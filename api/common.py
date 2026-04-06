#!/usr/bin/env python
from django.conf import settings
import os
import pwd
import math
import xml.etree.ElementTree as ET
import glob
import psycopg2
from psycopg2 import sql
from datetime import datetime, timedelta
import re
import requests
import json

try:
    from urllib.parse import urlparse, urlencode
except:
    from urllib import urlparse, urlencode

import logging
logger = logging.getLogger(__name__)

"""This module contains database interaction and common data
management functions.
"""

conn = None
cursor = None

# cache is designed where each key is a tablename.
cache = {}

XML_DIR = '/data/web/metadata/'

def get_IGrML_config():
    return settings.RDADB['IGrML_config_pg']

def get_search_config():
    return settings.RDADB['search_config_pg']

def get_WGrML_config():
    return settings.RDADB['WGrML_config_pg']

def get_dssdb_config():
    return settings.RDADB['dssdb_config_pg']

def get_wagtail_config():
    return settings.RDADB['wagtail2_config_pg']

def init_connection_new(config=None, schema_name=None):
    """
    Initialize connection and set DB schema.
    Prefereable to call this function first since you can catch
    connection errors. Otherwise, functions that need a connection
    will initialize it.
    """
    if config is None:
        db_config = get_dssdb_config()
    else:
        db_config = config

    con = psycopg2.connect(**db_config)
    cur = con.cursor()

    if schema_name is not None:
        set_schema_new(cur, schema_name)

    return (con,cur)

def init_connection(config=None, schema_name=None):
    """
    Initialize connection and set DB schema.
    Prefereable to call this function first since you can catch
    connection errors. Otherwise, functions that need a connection
    will initialize it.
    """
    global cursor
    global conn
    if config is None:
        db_config = get_dssdb_config()
    else:
        db_config = config

    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    if schema_name is not None:
        set_schema(schema_name)

    return (conn,cursor)

def set_schema_new(cur, schema_name=None):
    """ Set the DB schema search path.  Default is 'dssdb'. """

    if schema_name is None:
        schema_name = 'dssdb'

    try:
        #cursor.execute(sql.SQL("SET search_path TO '{}'").format(sql.Identifier(schema_name)))
        query = "SET search_path TO '{}'".format(schema_name)
        cur.execute(query)
        logger.debug("Search path set to schema '{schema_name}'.")

    except Exception as e:
        logger.error("{}".format(e))

def set_schema(schema_name=None):
    """ Set the DB schema search path.  Default is 'dssdb'. """

    if schema_name is None:
        schema_name = 'dssdb'

    try:
        #cursor.execute(sql.SQL("SET search_path TO '{}'").format(sql.Identifier(schema_name)))
        query = "SET search_path TO '{}'".format(schema_name)
        cursor.execute(query)
        logger.debug("Search path set to schema '{schema_name}'.")

    except Exception as e:
        logger.error("{}".format(e))

def close_connection(connection, cur):
    """Close connection and set cursor/conn obj to None."""
    cur.close()
    connection.close()

def change_keys(in_dict, key_map):
    """Change keys of a dict.
    If key map has value of None, remove key"""
    for key in list(in_dict):
        if key in key_map:
            if key_map[key] is None:
                in_dict.pop(key)
            else:
                new_key = key_map[key]
                in_dict[new_key] = in_dict[key]
                in_dict.pop(key)
    return in_dict

def get_format_from_filename(filename):
    """XML file contains format before first '.'
    """
    filename = os.path.basename(filename)
    return filename.split('.')[0]

def get_xml_elements(xml_file, *tag_names):
    """Given an xml file, return xml elements of a given tagname
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # filter tag_name
    elements = []
    for tag_name in tag_names:
        elements.extend(filter(lambda var: var.tag == tag_name, root ))
    return elements

def get_levels_from_xml(xml_file):
    """Convert XML to parameter information.
    Also stuffs format info in there.
    """
    levels = get_xml_elements(xml_file, 'level', 'layer')
    level_data = {}
    for level in levels:
        code = level.attrib['code']
        level_obj = {}
        for child in list(level):
            key = child.tag
            value = child.text
            level_obj[key] = value

        level_data[code] = level_obj
    return level_data

def get_params_from_xml(xml_file):
    """Convert XML to parameter information.
    Also stuffs format info in there.
    """
    file_format = get_format_from_filename(xml_file)
    parameters = get_xml_elements(xml_file, 'parameter')
    param_data = {}
    for param in parameters:
        code = param.attrib['code']
        param_obj = {}
        param_obj['format'] = file_format
        for child in param:
            key = child.tag
            value = child.text
            param_obj[key] = value

        param_data[code] = param_obj
    return param_data

def parse_param_code(param_code):
    """Given a parameter code, return table name and code.
    Example:
    7-0.2:11 returns,
    ('7-0.2', 11)
    """
    return param_code.split(':')

def get_param_info(full_code, key_change=None):
    """Return param information given code.
    """
    tablename, code = parse_param_code(full_code)
    param_dict = check_cache('param_codes', tablename)
    if param_dict is not None:
        return param_dict[code]

    xml_location = os.path.join(XML_DIR,'ParameterTables/')
    filenames = glob.glob(xml_location + '*'+tablename+'.xml')
    if len(filenames) > 1:
        raise ValueError('Glob should only return 1 filename')
    params = get_params_from_xml(filenames[0])
    if key_change is not None:
        for param in params.values():
            param = change_keys(param, key_change)
    add_to_cache('param_codes', tablename, params)
    return params[code]

def get_level_info(map_name, code):
    """Return level information given code.
    """
    #level_dict = check_cache('level_codes', map_name)
    #if level_dict is not None:
    #    return level_dict[code]

    xml_location = os.path.join(XML_DIR,'LevelTables/')
    glob_str = xml_location + '*'+map_name+'.xml'
    filenames = glob.glob(glob_str)
    if len(filenames) > 1:
        #raise ValueError('Glob should only return 1 filename')
        levels = {}
        for _file in filenames:
            levels.update(get_levels_from_xml(_file))
    elif len(filenames) == 0:
        raise ValueError('Glob couldn\'t find file. glob string is: '+glob_str )
    else:
        levels = get_levels_from_xml(filenames[0])
    #add_to_cache('level_codes', map_name, levels)
    if code not in levels:
        print(f'code: "{code}" not found in {levels}')
        print(f'{filenames}')
        return {}
    return levels[code]

def get_param_inventory(dsid, param_code):
    """Returns param_code with appropriate inventory number. """
    #dsid = format_dataset_id(dsid)
    #dsid = "".join(dsid.split('.'))

    #new_param_code = get_inventory_name_from_parameter(param_code)
    #like_str = dsid + "%" + str(param_code)
    #init_connection(config=get_IGrML_config(), schema_name=settings.RDADB['pg_schemas']['IGrML'])
    #query = "show tables like %s"
    #cursor.execute(query, (like_str,))

    init_connection(config=get_IGrML_config(), schema_name=settings.RDADB['pg_schemas']['IGrML'])
    query = "select parameter from parameters where parameter like %s"
    cursor.execute(query, ('%'+param_code,))

    response = cursor.fetchone()
    #if response is None:
    #    return response
    ## e.g. "ds0833_inventory_3!7-0.2-1:0.0.21"
    #inventory_str = response[0]
    #new_param_code = inventory_str.split('_')[-1]
    #new_param_code = str(inventory_str) + '!' + str(param_code)
    return response[0]

def to_dict(keys, data):
    """Converts list of tuples into a list of dicts using the key

    # Example
    >> to_dict(('key1', 'key2'), [('value1a','value2a'), ('value1b','value2b')])
    [{'key1':'value1a', 'key2':'value2a'},{'key1':'value1b', 'key2':'value2b'}]

    """
    if type(data) is str:
        data = (data,)
    if len(data) == 0:
        return []
    if len(keys) != len(data[0]):
        raise Exception("number of keys doesn't equal data length")
    out = []
    for i in data:
        tmp_obj = {}
        for k,v in zip(keys, i):
            tmp_obj[k] = v
        out.append(tmp_obj)
    return out

def reset_cache():
    """Resets cache. Useful for testing"""
    global cache
    cache = {}

def check_cache(table, key):
    """Checks cache to see if 'table' has been defined in cache, then check if key exists.
    If both cases are true, returns value. Otherwise, returns None.
    """
    if table in cache:
        cached_table = cache[table]
        if key in cached_table:
            return cached_table[key]
    return None

def add_to_cache(table, key, value):
    """Adds a key-value pair to given table.
    """
    if table not in cache:
        cache[table] = {}
    cache[table][key] = value

def get_access_type(dsid):
    """Get's dataset's access type.
    For example,
    084.1 would return 'g' as it's globally accessible.
    whereas JRA would return 'j' since it has restriced access.
    """
    dsid = format_dataset_id(dsid)
    init_connection(get_dssdb_config())
    query = "select access_type from dataset where dsid=%s"
    cursor.execute(query, (dsid,))
    response = cursor.fetchone()
    if response is None:
        return response
    return response[0]

def get_variable_info(dsid):
    """Get variable information for a given dsid.
    returns a list of dicts that have keys:
    format_code,
    time_range_code,
    grid_definition_code,
    parameter,
    level_type_codes,
    start_date,
    end_date

    """
    dsid = format_dataset_id(dsid, remove_ds=True)
    con,cur = init_connection_new(config=get_WGrML_config(), schema_name=settings.RDADB['pg_schemas']['WGrML'])
    column_names = ('format_code', 'time_range_code', 'grid_definition_code', \
            'parameter', 'level_type_codes', 'start_date','end_date', 'time_range')
    column_names_str = ','.join(column_names)
    query = "select "+ column_names_str +" from summary left join time_ranges on summary.time_range_code=time_ranges.code where dsid=%s"
    cur.execute(query, (dsid,))
    close_connection(con,cur)
    return to_dict(column_names, cur.fetchall())

def flipbit(bit):
    """flips a bit that is a string."""
    if bit == '1':
        return '0'
    return '1'

def expand_bitmap(compressed_map):
    """Given a bitmap levelcode, expand to full bitmap.
    The code is separated into two parts that can be separated
    by a '-'. The first part is the bitmap--except for the
    last bit, which should be inverted an multiplied by the second
    part of the code after the '-'. Some examples might show this a
    bit more clearly (no pun intended).
    Examples:
    10110-4 yields 10111111
    1-10    yields 0000000000
    -4      yields 1111
    101     yields 101
    """
    if '-' not in compressed_map:
        return compressed_map
    bitmap, stride = compressed_map.split('-')
    if bitmap == "":
        last_bit = '0'
    else:
        last_bit = bitmap[-1]
    stride = str(int(stride) -1)
    remaining_bitmap = flipbit(last_bit) * int(stride)
    bitmap = bitmap + remaining_bitmap
    return bitmap

def parse_levelType_code(code):
    """Takes level code and returns array of codes.
    Examples:
    ```
    >>> parse_levelType_code('2721:1')
    [2727]
    >>> parse_levelType_code('2721:-43/1000-10/1-14/0-10/1')
    [2727,2728]
    ```
    """
    # code starts with the begining index
    first_index,remainder = code.split(':')
    return_codes = []
    if remainder == '1':
        return [first_index]
    cur_index = int(first_index)
    levelmaps = remainder.split('/')
    for levelmap in levelmaps:
        bitmap = expand_bitmap(levelmap)
        for bit in bitmap:
            if bit == '0':
                pass
            elif bit == '1':
                return_codes.append(str(cur_index))
            else:
                raise ValueError("non-binary character in bitmap")
            cur_index += 1

    return return_codes

def get_format(dsid):
    """Returns format given dsid"""
    pass

def get_code_from_grid_definition(grid_def):
    """Return the code associated with the grid definition.
    """
    grid_def = str(grid_def)
    table = 'grid_definitions'
    init_connection(config=get_WGrML_config(), schema_name=settings.RDADB['pg_schemas']['WGrML'])
    cursor.execute("select code from "+table+" where def_params = %s", (grid_def,))
    data = cursor.fetchall()[0] # should only return 1 entry, so take first

    return data[0]

    #get_grid_definition(code)

def get_grid_definition(code):
    """Return grid definition and definition parameters

    Example of 'definition' is 'latLon'
    Example of 'def_params' is '360:180:90N:0E:90S:360E:1:1'
    """
    code = str(code)
    table = 'grid_definitions'
    value = check_cache(table, code)
    if value is not None:
        return value
    init_connection(config=get_WGrML_config(), schema_name=settings.RDADB['pg_schemas']['WGrML'])
    code = str(code)
    cursor.execute("select * from "+table+" where code = %s", (code,))
    data = cursor.fetchall()[0] # should only return 1 entry, so take first
    return_obj =  {
            'definition':data[0],
            'def_params':data[1]
            }
    add_to_cache(table, code, return_obj)
    return return_obj

def get_level_definition(code, file_format="", key_change=None):
    """Return level definition and definition parameters.
    """
    table = 'levels'
    value = check_cache(table, code)
    if value is not None:
        return value

    init_connection(config=get_WGrML_config(), schema_name=settings.RDADB['pg_schemas']['WGrML'])
    code = str(code)
    query = "select map,type,value from "+table+" where code = %s"
    cursor.execute("select map,type,value from "+table+" where code = %s", (code,))
    try:
        data = cursor.fetchall()[0] # should only return 1 entry, so take first
    except IndexError as e:
        raise IndexError('code: '+code+' not found in levels table')

    return_obj =  {
            'map':data[0],
            'type':data[1],
            'value':data[2]
            }
    # Get remainder of info from XML
    if file_format is None:
        file_format = '' #'WMO_GRIB2'
    map_name = file_format+'.'+return_obj['map']
    type_code = return_obj['type']
    if '-' in type_code:
        type_code = type_code.split('-')[0]
    level_info = get_level_info(map_name, type_code)
    return_obj.pop('map')
    return_obj.pop('type')
    return_obj.update(level_info)
    if key_change is not None:
        change_keys(return_obj, key_change)
    if 'level' not in return_obj:
        return_obj['level'] = code

    add_to_cache(table, code, return_obj)
    return return_obj

def merge_dicts(default_dict, added_dict):
    """Merges two dicts.
    default_dict will be overwritten if key is same as
    added_dict
    """
    new_dict = {}
    new_dict.update(default_dict)
    new_dict.update(added_dict)
    return new_dict

def can_subset(dsid):
    """Returns true if dataset has subsetting available."""
    dsid = format_dataset_id(dsid)
    groups = get_request_type(dsid)
    for group in groups:
        request_type = group['request_type']
        # Where S is subset and T is format conversion
        if request_type == 'S' or request_type == 'T':
            return True
    return False

def get_request_type(dsid):
    """Returns the request type and index.
    Example:
    ```
    >>> get_request_type('083.2')
    [{'request_type': u'T', 'group_index': 0}, {'request_type': u'T', 'group_index': 1}, {'request_type': u'T', 'group_index': 2}]
    ```
    """
    init_connection()
    cursor.execute('select rqsttype,gindex from rcrqst where dsid=%s and command is not NULL', (dsid,))
    data = cursor.fetchall()
    return to_dict(('request_type','group_index'), data)

def get_group_title(dsid, group):
    init_connection()
    cursor.execute('select title from dsgroup where dsid=%s and gindex=%s', (dsid,group))
    data = cursor.fetchall()
    return to_dict(('title',), data)

def get_group_info(dsid, group):
    con,cur = init_connection_new()
    cur.execute('select title,wnote,grpid,pindex,webpath from dsgroup where dsid=%s and gindex=%s', (dsid,group))
    data = cur.fetchall()
    close_connection(con,cur)
    if len(data) == 0:
        raise ValueError('No Data')
    return (data[0][0],data[0][1],data[0][2],data[0][3],data[0][4])

def make_list_from_index(list_of_iterable, index=0):
    """Makes a single list from a list of iterables, optionally giving index.
    """
    return [i[index] for i in list_of_iterable]

def get_request_info(rindex):
    """ Returns a dict of request indexes.
    Return keys are:
    'status'
    'NCAR_contact'
    'date_ready'
    'date_rqst'
    'date_purge'
    'subset_info'
    'request_id'
    'rinfo'
    'location'
    'dsid'
    """
    #info = check_cache('rqst_info', rindex)
    #if info is not None:
    #    return info
    column_names = ('date_rqst', 'date_ready', 'date_purge','status','rqstid',\
                    'dsid','specialist', 'note', 'rqstid', 'rinfo', 'location')
    con, cur = init_connection_new()
    query = 'select ' + ','.join(column_names) + ' from dsrqst where rindex=%s'
    cur.execute(query, (rindex,))
    request = cur.fetchall()
    close_connection(con, cur)

    if len(request) > 1:
        raise ValueError("There should not be multiple requests per rindex")
    if len(request) == 0:
        raise ValueError("No request found for rindex '"+str(rindex)+"'")
    request = to_dict(column_names, request)
    request = request[0]

    # Handle status
    request['status'] = parse_status(request['status'])
    request['request_id'] = request['rqstid']

    # Handle specialist
    specialist = request['specialist']
    request.pop('specialist')
    request['NCAR_contact'] = specialist+'@ucar.edu'

    request['request_id'] = request['rqstid']
    request.pop('rqstid')

    # Handle dates
    date_rqst = request['date_rqst']
    date_ready = request['date_ready']
    date_purge = request['date_purge']
    if date_rqst is not None:
        request['date_rqst'] = date_rqst.isoformat()
    if date_ready is not None:
        request['date_ready'] = date_ready.isoformat()
    if date_purge is not None:
        request['date_purge'] = date_purge.isoformat()

    # Handle note
    note = parse_note(request['note'])
    request.pop('note')
    request['subset_info'] = note

    request['request_index'] = rindex

    #add_to_cache('rqst_info', rindex, request)

    return request

def get_request_indexes(email):
    """Returns rindexes of requests associated with email"""
    init_connection()
    query = 'select rindex from dsrqst where email=%s'
    cursor.execute(query, (email,))
    request = cursor.fetchall()
    return request

def get_request_status(request_index):
    """ Returns the status code for a given request index """
    init_connection()
    query = 'select status from dsrqst where rindex=%s'
    cursor.execute(query, (request_index,))
    status = cursor.fetchall()
    return status[0][0]

def get_request_index_from_rqstid(rqstid):
    """ Returns request index for a given request ID """
    con,cur = init_connection_new()
    query = 'select rindex from dsrqst where rqstid=%s'
    cur.execute(query, (rqstid,))
    request = cur.fetchall()
    if len(request) > 0:
        rindex = request[0][0]
    else:
        rindex = None

    close_connection(con,cur)

    return rindex

def get_request_files(request_index, with_urls=False):
    """
    Returns a list of dictionaries of request output
    files for a given request index.

    If with_urls = True, the returned list will also include
    download URLs and base file names of the request files.
    """
    con,cur = init_connection_new()
    query = 'select tarcount from dsrqst where rindex=%s'
    cur.execute(query, (request_index,))
    request = cur.fetchall()
    if len(request) > 0:
        request = to_dict(('tarcount',), request)
        request = request[0]

    if request['tarcount'] > 0:
        tcnd = ' AND tindex=0'
    else:
        tcnd = ''

    rcnd = ' ORDER BY disp_order, wfile'

    column_names = request_column_names()
    query = 'select ' + ','.join(column_names) + ' from wfrqst where rindex=%s' + tcnd + rcnd
    cur.execute(query, (request_index,))
    files = cur.fetchall()
    if len(files) > 0:
        files = to_dict(column_names, files)
    else:
        files = []

    if request['tarcount'] > 0:
        tarpath = "TarFiles/"
        fields = ','.join(column_names)
        field_wfile = "concat('{}', wfile) wfile".format(tarpath)
        field_type = "'D' type"
        fields = re.sub(r'wfile', field_wfile, fields)
        fields = re.sub(r'type', field_type, fields)
        query = 'select {} from tfrqst where rindex=%s {}'.format(fields, rcnd)
        cur.execute(query, (request_index,))
        tarfiles = cur.fetchall()
        if len(tarfiles) > 0:
            tarfiles = to_dict(column_names, tarfiles)
            files = files + tarfiles
    else:
        tarpath = ''

    if with_urls:
        base_rpath = get_request_path(request_index)
        for i in range(len(files)):
            wfile = files[i]['wfile']
            if re.search(r'^{}'.format(tarpath), wfile):
                wfile = re.sub(r'^{}'.format(tarpath), '', wfile, 1)
                rpath = "{}/{}".format(base_rpath, tarpath)
            else:
                rpath = base_rpath
            url = get_request_file_url(wfile, rpath=rpath)
            base_file_name = os.path.basename(wfile)
            files[i].update({'url': url, 'base_file_name': base_file_name})

    close_connection(con,cur)
    return files

def request_column_names():
    """
    Returns a tuple of column names to query for request files (table wfrqst or tfrqst)
    """
    column_names = ('wfile', 'size', 'data_format', 'date', 'type', 'note')
    return column_names

def request_column_headers():
    """
    Returns long names associated with data
    request files.  Input keys are based on database
    column names in rdadb.wfrqst and/or rdadb.tfrqst.
    """
    column_map = {
        'wfile' : 'File Name',
        'note': 'Notes',
        'size' : 'Size',
        'type': 'Type',
        'data_format' : 'Data Format',
        'file_format' : 'Archive Format',
        'checksum': 'Checksum (MD5)',
        'date' : 'Date Online'
    }
    headers = {}
    for item in request_column_names():
        headers.update({item: column_map[item]})

    return headers

def request_type(type):
    """
    Returns a long name associated with a given data type
    (data, document, or software).
    """
    type_map = {
        'D': 'Data',
        'O': 'Document',
        'S': 'Software',
        'H': 'Help Document'
    }
    return type_map[type]

def get_grouplevel(dsid):
    """Returns group level of dataset"""
    dsid = format_dataset_id(dsid)
    init_connection()
    query = 'select grouplevel from dataset where dsid=%s'
    cursor.execute(query, (dsid,))
    grouplevel = cursor.fetchone()[0]
    return grouplevel

def get_local_emailname():
    disallowed_users = set('apache',)
    uid = get_user_id()
    if uid in disallowed_users:
        raise ValueError("Dissallowed user request")
    user = uid + "@ucar.edu"
    return user

def get_unique_tindex(request_index):
    """Returns unique tindexes (tar indexes) given request index."""
    init_connection()
    query = 'select distinct tindex from wfrqst where rindex=%s'
    cursor.execute(query, (request_index,))
    tindexes = cursor.fetchall()
    return tindexes

def get_random_webfile(dsid, parameter_code=None, start_date=None, end_date=None):
    """Gets a random webfile from dataset. optionally limit by parameter and date."""
    init_connection(config=get_WGrML_config(), schema_name=settings.RDADB['pg_schemas']['WGrML'])
    conditions = []
    conditions_vars = []
    grids_table = f'{dsid}_grids2'
    webfiles_table = f'{dsid}_webfiles2'

    if not parameter_code and not start_date and not end_date:
        query = f'select id from {grids_table} left join {webfiles_table} on code=file_code order by RANDOM() limit 1;'
        cursor.execute(query, ())
        return cursor.fetchall()[0][0] # should only return 1 entry, so take first

    if parameter_code:
        conditions.append('parameter=%s')
        conditions_vars.append(parameter_code)
    if start_date:
        conditions.append(f'{webfiles_table}.start_date>%s ')
        conditions_vars.append(start_date)
    if end_date:
        conditions.append(f'{webfiles_table}.end_date<%s')
        conditions_vars.append(end_date)

    conditions_str = " AND ".join(conditions)

    query = f'select id from {grids_table} left join {webfiles_table} on code=file_code WHERE {conditions_str} order by RANDOM() limit 1;'
    print(query)
    print(conditions_vars)
    cursor.execute(query, tuple(conditions_vars))
    result = cursor.fetchall()
    print(result)
    if len(result) > 0:
        return result[0] # should only return 1 entry, so take first
    return None

def get_arco_variables(dsid):
    """Get Arco Variables"""
    import csv
    from io import StringIO
    csv_info = check_cache('arco_vars', dsid )
    if csv_info is not None:
        return csv_info
    con,cur = init_connection_new()
    wfile_table=f'wfile_{dsid}'
    assert len(wfile_table) == 13
    match_str = 'catalog%.csv'
    query = f'select wfile,locflag from {wfile_table} where gindex<0 and wfile like %s'
    cur.execute(query, (match_str,))
    result = cur.fetchall()
    close_connection(con,cur)
    csv_files = [(i[0],i[1]) for i in result]
    res = [['unknown','error']]
    print(csv_files)
    for _file in csv_files:
        if 'http' in _file[0]:
            if _file[1] != 'O':
                url = get_webfile_url(dsid, _file[0], settings.GLOBUS_DATA_BASE_URL, locflag=_file[1])
            else:
                url = get_webfile_url(dsid, _file[0], settings.GLOBUS_STRATUS_BASE_URL, locflag=_file[1])
            print(url)
            content = requests.get(url).content
            reader = csv.reader(StringIO(content.decode()))
            res = []
            for row in reader:
                if dsid in ['d316010']:
                    shifted = [row[-1]] + row[1:-1]
                    row = shifted
                res.append(row)
    add_to_cache('arco_vars', dsid, res)
    return res

def get_time_range(dsid):
    """Get the temporal range for a given dataset

    Args:
        dsid (str): six digit id for dataset (dxxxxxx)

    Returns (tuple):
        [0]: start date in datetime format
        [1]: end date in datetime format
    """
    con,cur = init_connection_new(get_wagtail_config())
    query = 'select temporal from dataset_description_datasetdescriptionpage where dsid=%s'
    cur.execute(query, (dsid,))
    data = cur.fetchone()[0]
    close_connection(con,cur)
    start_date = data['full'].split(' to ')[0]
    start_date = datetime.strptime(start_date.split('+')[0], '%Y-%m-%d %H:%M ')
    end_date = data['full'].split(' to ')[1]
    end_date = datetime.strptime(end_date.split('+')[0], '%Y-%m-%d %H:%M ')
    return (start_date, end_date)

def get_tindex_from_webfile(wfile, dsid):
    """Get the tindex of a webfile"""
    dsid = format_dataset_id(dsid)
    tindex_info = check_cache('web_file_tindex', dsid + wfile)
    if tindex_info is not None:
        return tindex_info
    init_connection()
    if settings.SPLIT_WFILE:
        query = "SELECT wfile,file_format from wfile_{} where tindex=%s".format(dsid)
        cursor.execute(query, (wfile,))
    else:
        query = "SELECT wfile,file_format from wfile where dsid='%s' and tindex=%s"
        cursor.execute(query, (dsid,wfile))

    files = cursor.fetchall()

def get_webid_from_code(table, code):
    webid =  check_cache('webid', code)
    if webid is not None:
        return webid
    init_connection(config=get_WGrML_config(), schema_name=settings.RDADB['pg_schemas']['WGrML'])
    query = "SELECT id from "+table+" where code=%s"
    cursor.execute(query, (code,))
    webid = cursor.fetchone()[0]
    add_to_cache('webid', code, webid)
    return webid

def get_webfiles_by_param_and_date(grid_table, param, start_date, end_date):
    init_connection(config=get_WGrML_config(), schema_name=settings.RDADB['pg_schemas']['WGrML'])
    columns = ['file_code', 'grid_definition_code', 'level_type_codes', 'start_date' ,'end_date','min_nsteps','max_nsteps']
    query = "SELECT "+ ','.join(columns) + " from "+ grid_table +" where parameter=%s and ((start_date<%s and end_date>=%s) OR (start_date>=%s and end_date<=%s) OR (start_date<=%s and end_date>%s))"
    cursor.execute(query, (param, start_date, start_date, start_date, end_date, end_date, end_date))
    return cursor.fetchall() # likely many files, so allow client to iterate.

def get_web_files(request_index):
    """Given a request index, get web file path"""
    con,cur = init_connection_new()
    query = 'select wfile,size,tindex from wfrqst where rindex=%s'
    cur.execute(query, (request_index,))
    files = cur.fetchall()
    close_connection(con,cur)
    return to_dict(('wfile','size','tindex'), files)

def get_tar_file(tindex):
    """Get's information about tar file given an index
    """
    #tar_info = check_cache('tindex', tindex)
    #if tar_info is not None:
    #    return tar_info
    con,cur = init_connection_new()
    column_names = ('fcount', 'size', 'data_format', 'wfile')
    query = 'select '+ (','.join(column_names)) +' from tfrqst where tindex=%s'
    cur.execute(query, (tindex,))
    tar_info = to_dict(column_names, cur.fetchall())
    close_connection(con,cur)
    return tar_info

def get_status_map():
    """Returns a dict of Status key to long name.
    """
    status_map = {
    'O' : 'Completed',
    'E' : 'Error',
    'Q' : 'Queued for Processing',
    'P' : 'Set for Purge',
    'W' : 'Wait',
    'H' : 'Suspended',
    'I' : 'Interrupted'
    }
    return status_map

def parse_status(status):
    """Given a status, return a description of code.
    """
    status_map = get_status_map()
    if status in status_map:
        return status_map[status]
    return "Unknown status"

def parse_rinfo(rinfo):
    """Parse dsrqst rinfo into dict.
    rinfo looks like the following:
    ```
      dsnum=084.1;startdate=2016-09-20 00:00;enddate=2016-09-20 00:00;dates=init;parameters=3!7-0.2-1:0.0.0,3!7-0.2-1:0.1.1,3!7-0.2-1:0.2.10;level=81,84,88;nlat=5;slat=-5;wlon=-150;elon=-125;product=23,1,3,41
    ```
    """
    assert isinstance(rinfo, str)
    entries = rinfo.split(';')

    rinfo_dict = {}
    for kv in entries:
        key, value = kv.split('=')
        rinfo_dict[key] = value

    # Parse Parameters
    if 'parameters' in rinfo_dict:
        parameters_str = rinfo_dict['parameters']
        param_list = parameters_str.split(',')
        for i,param in enumerate(param_list):
            param_list[i] = param.split('!')[1] # index 0 is format code
        rinfo_dict['parameters'] = param_list
    # Parse Product
    if 'product' in rinfo_dict:
        product_str = rinfo_dict['product']
        rinfo_dict['product'] = product_str.split(',')
    # Parse level
    if 'level' in rinfo_dict:
        level_str = rinfo_dict['level']
        rinfo_dict['level'] = level_str.split(',')
    # Parse tindex
    if 'tindex' in rinfo_dict:
        tindex_str = rinfo_dict['tindex']
        rinfo_dict['tindex'] = tindex_str.split(',')
    # Parse start and end time into datetimes then to properly str
    start_datetime = datetime.strptime(rinfo_dict['startdate'],'%Y-%m-%d %H:%M')
    end_datetime = datetime.strptime(rinfo_dict['enddate'],'%Y-%m-%d %H:%M')
    rinfo_dict['startdate'] = start_datetime.strftime('%Y%m%d%H%M')
    rinfo_dict['enddate'] = end_datetime.strftime('%Y%m%d%H%M')

    return rinfo_dict

def parse_note(note):
    """Parse dsrqst 'note' into dict.
    WARNING: the 'note' is not consistent across methods.
    'note' generally looks like the following:
    ```
    2016-09-20 00:00 to 2016-09-20 00:00
    Date Type            :  init
    Parameter            :  TMP/R H/ABS V
    Level Type           :  ISBL:850/700/500
    Latitude Limits      :  5 N to -5 S
    Longitude Limits     :  -150 W to -125 E
    Product              :  Analysis/12-hour Forecast/6-hour Forecast/18-hour Forecast
     | dsnum=084.1;startdate=2016-09-20 00:00;enddate=2016-09-20 00:00;dates=init;parameters=3!7-0.2-1:0.0.0,3!7-0.2-1:0.1.1,3!7-0.2-1:0.2.10;level=81,84,88;nlat=5;slat=-5;wlon=-150;elon=-125;product=23,1,3,41
    ```
    """
    return {'note':note} #tmp
    note = note.split('\n')
    note = note[:-1] # Empty last line
    out_dict = {}
    for part in note:
        key,value = part.split(':', 1)
        out_dict[key.strip()] = value.strip()

    return out_dict

def long_name(key):
    """Returns a more descriptive name given the 'key'.
    Typically converts database keys to a longer name.
    """
    name_change = {
        'wfile': 'File Name',
        'data_size': 'Size',
        'data_format': 'Data Format',
        'date_modified': 'Date Archived',
        'groupid': 'Group ID',
        'grpid': 'Group Name',
        'webcnt': 'File Count',
        'title': 'Description'
    }
    return name_change[key]

def create_filelist_table(dsid, gindex, page=0, filter_wfile=None):
    from globus.views import get_guest_collection_origin_path

    files = get_web_files_from_gindex(dsid, gindex, page, filter_wfile)
    total_files = int(get_total_webfiles_gindex(dsid, gindex, filter_wfile))
    webpath = ""
    try:
        title,note,group_id,parent_id,webpath = get_group_info(dsid, gindex)
    except ValueError:
        title = dsid + ' files'
        note = None
        group_id = None
    group = Group(title, note, group_id)
    if total_files > 2000:
        total_pages = math.floor(total_files/2000)
        group.set_paginator_pages(total_pages, page)
    group.set_gindex(gindex)
    group.set_webpath(webpath)
    group.set_total_file_count(total_files)
    group.is_group_summary = False
    if len(files) == 0:
        return group

    locflag = get_dataset_location(dsid)
    origin_path = get_guest_collection_origin_path(dsid)

    if int(gindex) < 0:  # Use Globus HTTPS domains for ARCO datasets (gindex < 0)
        if locflag == 'G':
            base_url = settings.GLOBUS_DATA_BASE_URL
        else:
            base_url = settings.GLOBUS_STRATUS_BASE_URL
    else:
        base_url = get_webfile_base_url(dsid, files[0]['wfile'], locflag=locflag)

    for _file in files:
        file_url = get_webfile_url(dsid, _file['wfile'], base_url, origin_path=origin_path, locflag=locflag)
        data_path = os.path.join('/',dsid,_file['wfile'])
        #if _file['locflag'] == 'O':
        #    data_path = os.path.join('/OS',dsid,_file['wfile'])
        filename = {
            'is_file' : True,
            'name' : long_name('wfile'),
            'value' : os.path.basename(_file['wfile']),
            'url' : file_url,
            'data_path': data_path,
            'note' : _file['note'],
        }
        if _file['meta_link'] is None:
            filename['meta_link'] = None
        else:
            filename['meta_link'] = _file['meta_link'].strip()
        size = {'name':long_name('data_size'), 'value': _file['data_size']}
        data_format = {'name':long_name('data_format'), 'value': _file['data_format']}
        date_archived = {'name':long_name('date_modified'), 'value': _file['date_modified']}
        group.add_row([filename,size,data_format,date_archived])
    return group

def assemble_no_group_filelist(dsid, page=0):
    gindex = 0
    title = dsid + " Files"
    filelist = Filelist(title)
    #num_files = 2000
    #while num_files == 2000:
    #    fl_table = create_filelist_table(dsid, gindex, page)
    #    filelist.add_group(fl_table)
    #    num_files = len(fl_table)
    #    page += 1
    fl_table = create_filelist_table(dsid, gindex, page)
    filelist.add_group(fl_table)
    return filelist.get_data(dsid)

def assemble_filelist(dsid, group=None, page=0, fl_source=None, filter_wfile=None):
    """ Create a data structure to represent groups and files """
    if group is None:
        return assemble_root_group_filelist(dsid, fl_source=fl_source)
    dsid = format_dataset_id(dsid)
    title,note,group_id,parent_id,webpath = get_group_info(dsid, group)
    locflag = get_dataset_location(dsid)
    filelist = Filelist(title, note)

    if (parent_id == 0):
        parent_url = "/datasets/{0}/filelist".format(dsid)
    else:
        parent_url = "/datasets/{0}/filelist/{1}".format(dsid, parent_id)
    parent_group = {
            "gindex": parent_id,
            "url": parent_url
        }
    filelist.add_parent(parent_group)
    sub_group = Group('Subgroup Summary')

    child_groups = get_child_groups(dsid, group)
    logger.debug("fl_source: {}, len child_groups: {}".format(fl_source, len(child_groups)))
    if len(child_groups) == 0:
        fl_table = create_filelist_table(dsid, group, page, filter_wfile)
        if fl_table is not None:
            filelist.add_group(fl_table)
        return filelist.get_data(dsid, locflag, filter_wfile)
    child_groups_total_files = sum([i['webcnt'] for i in child_groups])
    if child_groups_total_files == 0:
        fl_table = create_filelist_table(dsid, group, page, filter_wfile)
        if fl_table is not None:
            filelist.add_group(fl_table)
        return filelist.get_data(dsid, locflag, filter_wfile)

    for child_group in child_groups:
        logger.debug("fl_source: {}, webcnt: {}, dwebcnt: {}".format(fl_source, child_group['webcnt'], child_group['dwebcnt']))
        logger.debug("grpid: {}, title: {}".format(child_group['grpid'], child_group['title']))
        if fl_source and fl_source == 'glade' and child_group['webcnt'] == 0:
            continue
        elif fl_source and fl_source != 'glade' and child_group['dwebcnt'] == 0:
            continue
        else:
            gindex = child_group['gindex']
            if not has_child_groups(dsid, gindex) and child_groups_total_files < 2000:
                fl_table = create_filelist_table(dsid, gindex, filter_wfile=filter_wfile)
                if fl_table is not None:
                    filelist.add_group(fl_table)
            else:
                group_url = os.path.join('/datasets',dsid,'filelist',str(child_group['gindex']))
                group_name = {'is_file':False,
                              'name':long_name('grpid'),
                              'value':child_group['grpid'],
                              'webpath':child_group['webpath'],
                              'url': group_url}
                group_description = {'name':long_name('title'),
                                     'value': child_group['title']}
                file_count = {'name':long_name('webcnt'),
                              'value': child_group['webcnt']}
                logger.debug("file count: {}".format(file_count['value']))
                if file_count['value'] > 0:
                    logger.debug("file count: {}".format(file_count['value']))
                    sub_group.add_row([group_name, group_description, file_count])
    if sub_group.has_data():
        logger.debug("adding subgroup to filelist")
        filelist.add_group(sub_group)

    return filelist.get_data(dsid, locflag, filter_wfile)

def assemble_root_group_filelist(dsid, page=0, fl_source=None):
    dsid = format_dataset_id(dsid)
    root_groups = get_root_groups(dsid)
    if len(root_groups) == 0:
        return assemble_no_group_filelist(dsid, page)
    if len(root_groups) == 1:
        return assemble_filelist(dsid, root_groups[0]['gindex'])
    title = "Group/Subgroup summary"

    # Assemble table view
    filelist = Filelist(title)
    if filelist.has_data():
        return filelist.get_data(dsid)
    group = Group()
    for parent_group in root_groups:
        if fl_source and fl_source == 'glade' and parent_group['webcnt'] == 0:
            continue
        elif fl_source and fl_source != 'glade' and parent_group['dwebcnt'] == 0:
            continue
        else:
            group_name = {'is_file':False,'name':long_name('grpid'), 'value':parent_group['grpid'], 'url': os.path.join('/datasets',dsid,'filelist',str(parent_group['gindex']))}
            group_description = {'name':long_name('title'), 'value': parent_group['title']}
            file_count = {'name':long_name('webcnt'), 'value': parent_group['webcnt']}
            group.add_row([group_name, group_description, file_count])

    filelist.add_group(group)
    return filelist.get_data(dsid)

def get_dataset_helpfile(dsid, _type='A'):
    """Get helpfiles for dataset.
    _type can be:
    D (documentation),
    S (software),
    A (both software and documentation),"""
    dsid = format_dataset_id(dsid)
    assert _type=='D' or _type=='S' or _type=='A'
    init_connection()
    columns = ('hfile','data_size','date_modified','note','url')
    columns_str = ','.join(columns)
    if _type=='A':
        query = 'select '+columns_str+" from hfile where status='P' and dsid=%s order by disp_order asc"
        cursor.execute(query,(dsid,))
    else:
        query = 'select '+columns_str+" from hfile where status='P' and type=%s and dsid=%s order by disp_order asc"
        cursor.execute(query,(_type,dsid,) )
    data = cursor.fetchall()
    data = to_dict(columns, data)

    _dict = get_helpfile_common_metadata(dsid)
    _dict['files'] = data
    return _dict

def get_helpfile_common_metadata(dsid):
    return {'dsid':dsid}

def get_dataset_documentation(dsid):
    """Get documentation associated with dsid"""
    return get_dataset_helpfile(dsid, _type='D')

def get_dataset_software(dsid):
    """Get software associated with dsid"""
    return get_dataset_helpfile(dsid, _type='S')

def get_dataset_info(dsid):
    """ Returns a dict of selected dataset info """
    dsid = format_dataset_id(dsid)
    con,cur = init_connection_new()
    columns = ('dsid', 'title')
    query = 'select {} from dataset where dsid=%s'.format(','.join(columns))
    cur.execute(query, (dsid,))
    ds_info = cur.fetchall()
    if len(ds_info) > 0:
        ds_info = to_dict(columns, ds_info)
    close_connection(con,cur)
    return ds_info[0]

def get_root_groups(dsid):
    dsid = format_dataset_id(dsid)
    init_connection()
    columns = ('grpid','title','gindex','inote','mnote','dwebcnt','webcnt')
    columns_str = ','.join(columns)
    query = 'select '+columns_str+' from dsgroup where dsid=%s and pindex=0 order by gindex asc'
    cursor.execute(query,(dsid,))
    data = cursor.fetchall()
    data = to_dict(columns, data)
    return data

def has_child_groups(dsid, gindex):
    """Returns true if if group has child groups."""
    dsid = format_dataset_id(dsid)
    con,cur = init_connection_new()
    columns = ('grpid','gindex')
    columns_str = ','.join(columns)
    query = 'select '+columns_str+' from dsgroup where dsid=%s and pindex=%s limit 1'
    cur.execute(query,(dsid,gindex))
    data = cur.fetchall()
    close_connection(con,cur)
    return len(data) > 0

def has_webfiles(dsid, gindex):
    dsid = format_dataset_id(dsid)
    init_connection()
    columns = ('grpid','gindex')
    columns_str = ','.join(columns)
    if settings.SPLIT_WFILE:
        query = 'select '+columns_str+' from wfile_{} where gindex=%s limit 1'.format(dsid)
        cursor.execute(query,(gindex,))
    else:
        query = 'select '+columns_str+' from wfile where dsid=%s and gindex=%s limit 1'
        cursor.execute(query,(dsid,gindex))

    data = cursor.fetchall()
    return len(data) > 0

def get_child_groups(dsid, gindex):
    dsid = format_dataset_id(dsid)
    con,cur = init_connection_new()
    columns = ('grpid','gindex','inote','mnote','dwebcnt','webcnt','title','webpath')
    columns_str = ','.join(columns)
    query = 'select '+columns_str+' from dsgroup where dsid=%s and pindex=%s order by gindex asc'
    cur.execute(query,(dsid,gindex))
    data = cur.fetchall()
    close_connection(con,cur)
    data = to_dict(columns, data)
    return data

def get_total_webfiles_gindex(dsid, gindex, filter_wfile=None):
    dsid = format_dataset_id(dsid)
    con,cur = init_connection_new()
    if filter_wfile:
        if settings.SPLIT_WFILE:
            query = 'SELECT count(wfile) FROM wfile_{} WHERE gindex=%s AND wfile LIKE %s'.format(dsid)
            cur.execute(query, (gindex,f'%{filter_wfile}%'))
        else:
            query = 'SELECT count(wfile) FROM wfile WHERE dsid=%s AND gindex=%s AND wfile LIKE %s'
            cur.execute(query, (dsid,gindex,f'%{filter_wfile}%'))
    else:
        if settings.SPLIT_WFILE:
            query = 'SELECT count(wfile) FROM wfile_{} WHERE gindex=%s'.format(dsid)
            cur.execute(query,(gindex,))
        else:
            query = 'SELECT count(wfile) FROM wfile WHERE dsid=%s AND gindex=%s'
            cur.execute(query,(dsid,gindex))

    data = cur.fetchall()
    close_connection(con,cur)
    return data[0][0]

def get_web_files_from_gindex(dsid, gindex, page=0, filter_wfile=None):
    dsid = format_dataset_id(dsid)
    con,cur = init_connection_new()
    columns = ('wfile','note', 'status', 'date_modified', 'data_size', 'data_format', 'meta_link', 'locflag')
    columns_str = ','.join(columns)
    file_limit = 2000
    offset = int(page) * file_limit

    if filter_wfile:
        if settings.SPLIT_WFILE:
            query = 'SELECT '+columns_str+' FROM wfile_{} WHERE gindex=%s AND wfile LIKE %s ORDER BY disp_order ASC LIMIT {} OFFSET {}'.format(dsid, file_limit, offset)
            cur.execute(query,(gindex, f'%{filter_wfile}%'))
        else:
            query = 'SELECT '+columns_str+' FROM wfile WHERE dsid=%s AND gindex=%s AND wfile LIKE %s ORDER BY disp_order ASC LIMIT {} OFFSET {}'.format(file_limit, offset)
            cur.execute(query,(dsid, gindex, f'%{filter_wfile}%'))
    else:
        if settings.SPLIT_WFILE:
            query = 'SELECT '+columns_str+' FROM wfile_{} WHERE gindex=%s ORDER BY disp_order ASC LIMIT {} OFFSET {}'.format(dsid, file_limit, offset)
            cur.execute(query,(gindex,))
        else:
            query = 'SELECT '+columns_str+' FROM wfile WHERE dsid=%s AND gindex=%s ORDER BY disp_order ASC LIMIT {} OFFSET {}'.format(file_limit, offset)
            cur.execute(query,(dsid, gindex))

    data = cur.fetchall()
    close_connection(con,cur)
    data = to_dict(columns, data)
    for i,j in enumerate(data):
        if not isinstance(data[i]['wfile'],str):
            data[i]['wfile'] = data[i]['wfile'].decode()
    return data

def get_webfile_base_url(dsid, test_wfile, locflag=None):
    """
    Returns the base URL for dataset web files.
    """
    dsid = format_dataset_id(dsid)
    if not locflag:
        locflag = get_dataset_location(dsid)

    if locflag == 'C':
        base_url = settings.CGD_DATA_BASE_URL
        return base_url
    elif locflag == 'O':
        base_url = settings.RDA_STRATUS_BASE_URL
        osdf_origin = settings.OSDF_NCAR_S3_ORIGIN
        osdf_path = settings.OSDF_STRATUS_PATH
        globus_base_url = settings.GLOBUS_STRATUS_BASE_URL
    else:
        base_url = settings.RDA_DATA_BASE_URL
        osdf_origin = settings.OSDF_NCAR_ORIGIN
        osdf_path = settings.OSDF_DATA_PATH
        globus_base_url = settings.GLOBUS_DATA_BASE_URL

    # Check if OSDF director and origin are reachable
    if re.search(settings.OSDF_DOMAIN, base_url):
        osdf_director_url = os.path.join(settings.OSDF_DIRECTOR_URL, osdf_path)
        osdf_origin_url = os.path.join(osdf_origin, osdf_path)

        osdf_test_url_origin = get_webfile_url(dsid, test_wfile, osdf_origin_url, locflag=locflag)
        osdf_test_url_director = get_webfile_url(dsid, test_wfile, osdf_director_url, locflag=locflag)

        if is_url_reachable(osdf_test_url_origin) and is_url_reachable(osdf_test_url_director):
            return base_url
        else:
            # if OSDF is not reachable, use Globus domain
            return globus_base_url

    return base_url

def get_webfile_url(dsid, wfile, base_url, origin_path=None, locflag=None):
    """
    Returns the URL for a dataset web file.
        Optional argument 'locflag' = dataset location flag
          ('G' = glade, 'O' = stratus, 'B' = both,
           'C' = CGD data under /glade/campaign/cgd/cesm)
    """
    from globus.views import get_guest_collection_file_path

    dsid = format_dataset_id(dsid)

    # check wfile for leading '/' and remove if found
    wfile = wfile.lstrip('/')

    if not locflag:
        locflag = get_webfile_location(dsid, wfile)

    if locflag == 'C':
        wfile_path = get_guest_collection_file_path(origin_path, wfile)
        url = os.path.join(base_url, wfile_path)
    else:
        url = os.path.join(base_url, dsid, wfile)

    return url

def get_request_file_url(rfile, rpath=None):
    """ Returns the URL for a request file
       Input arguments:
          rfile = request file
	      rpath = path to request file, relative to RDA data request
                  base path (e.g. 'dsrqst/<rqstid>/')
    """
    base_url = settings.RDA_REQUEST_BASE_URL

    if not rpath:
        con,cur = init_connection_new()

        # get rindex from table 'wfrqst' or 'tfrqst'
        query = 'select rindex from wfrqst where wfile=%s'
        cur.execute(query, (rfile,))
        rindex = cur.fetchall()

        if len(rindex) == 0:
            # query table 'tfrqst' if not found in 'wfrqst'
            query = 'select rindex from tfrqst where wfile=%s'
            cur.execute(query, (rfile,))
            rindex = cur.fetchall()

        close_connection(con,cur)

        if len(rindex) > 0:
            rindex = to_dict(('rindex',), rindex)
            rindex = rindex[0]['rindex']
        else:
            raise TypeError("Request file {} not found in table 'wfrqst' or 'tfrqst'".format(rfile))

        rpath = get_request_path(rindex)

    if (rpath.find('/',0,1) != -1):
        rpath = rpath.replace('/','',1)

    url = os.path.join(base_url, rpath, rfile)

    return url

def get_request_path(rindex):
    """ Returns relative path to request file
        Example: '/dsrqst/<rqstid>/'
    """
    rqst_base_path = settings.RDA_REQUEST_PATH
    rqst_home = settings.RDA_REQUEST_HOME

    con,cur = init_connection_new()
    fields = ('rqstid',)
    query = 'select {} from dsrqst where rindex=%s'.format(','.join(fields))
    cur.execute(query, (rindex,))
    rqst_info = cur.fetchall()
    close_connection(con,cur)

    if len(rqst_info) > 0:
        rqst_info = to_dict(fields, rqst_info)
        rqstid = rqst_info[0]['rqstid']
    else:
        msg = "[get_request_path] Request index {} not found in table dsrqst".format(rindex)
        logger.error(msg)
        raise TypeError("Request index {} not found in RDADB".format(rindex))

    rqst_path = os.path.join(rqst_home, rqstid)
    rqst_path = re.sub(r'^{}'.format(rqst_base_path), '', rqst_path, 1)

    return rqst_path

def get_dataset_location(dsid):
    """ Get the location flag for a dataset
        locflag = 'G' = glade
        locflag = 'O' = stratus
        locflag = 'B' = both glade and stratus
        locflag = 'C' = CDG data under /glade/campaign/cgd/cesm
    """
    dsid = format_dataset_id(dsid)
    con,cur = init_connection_new()
    query = "select locflag from dataset where dsid=%s"
    cur.execute(query, (dsid,))
    response = cur.fetchone()
    close_connection(con,cur)
    return response[0]

def get_webfile_location(dsid, wfile):
    """ Get the location flag for a web file
        locflag = 'G' = glade
        locflag = 'O' = stratus
        locflag = 'B' = both glade and stratus
        locflag = 'C' = CDG data under /glade/campaign/cgd/cesm
    """
    dsid = format_dataset_id(dsid)
    con,cur = init_connection_new()
    if settings.SPLIT_WFILE:
        query = "select locflag from wfile_{} where wfile=%s".format(dsid)
        cur.execute(query, (wfile,))
    else:
        query = "select locflag from wfile where dsid=%s and wfile=%s"
        cur.execute(query, (dsid,wfile))

    response = cur.fetchone()
    close_connection(con,cur)

    if response[0] is None or response[0] == '':
        return get_dataset_location(dsid)
    else:
        return response[0]

def get_dataset_webhome(dsid):
    """ Get the base web directory of a dataset """
    dsid = format_dataset_id(dsid)
    con,cur = init_connection_new()
    query = "select webhome from dataset where dsid=%s"
    cur.execute(query, (dsid,))
    response = cur.fetchone()
    close_connection(con,cur)

    return response[0]

def has_arco(dsid):
    con,cur = init_connection_new()
    dsid = format_dataset_id(dsid)
    query = "select * from dsgroup where dsid=%s and gindex < 0"
    cur.execute(query, (dsid,))
    data = cur.fetchall()
    close_connection(con,cur)
    return len(data) != 0

def get_staff():
    """Get DECS employee information."""
    init_connection()
    cursor.execute("select fstname,lstname,officeno,phoneno,logname from dssgrp where role='S' or role='M'")
    data = cursor.fetchall()
    data_dict = to_dict(('first_name','last_name','officeno','phoneno','email'),data)
    for i in data_dict:
        i['email'] = i['email']+'@ucar.edu'
    return data_dict

def get_staff_dsid(dsid):
    """Get DECS employee information for a specific dataset."""
    con,cur = init_connection_new()
    cur.execute("select fstname,lstname,officeno,phoneno,logname from dssgrp inner join dsowner on dssgrp.logname=dsowner.specialist where dsowner.dsid=%s",(dsid,))
    data = cur.fetchall()
    close_connection(con,cur)

    data_dict = to_dict(('first_name','last_name','officeno','phoneno','email'),data)
    for i in data_dict:
        i['email'] = i['email']+'@ucar.edu'
    return data_dict

def check_user_exists(email):
    email.strip()
    init_connection()
    cursor.execute('select email from ruser where email=%s', (email,))
    result = cursor.fetchall()
    if len(result) > 0:
        return True
    return False

def add_new_user(email, first_name, last_name):
    """Adds a new user to the dssdb if it doesn't already exist.
    Returns True if added.
    Returns False if nothing was added.
    """
    email.strip()
    init_connection()
    if check_user_exists(email):
        return False
    cursor.execute('INSERT INTO ruser (org, country, valid_flag, valid_email, throttle, org_type, password, email, fname, lname) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
            ('','','1',email,'0','orcid', '', email, first_name, last_name))
    conn.commit()
    return True

def is_superuser(token):
    """Returns whether a given token is associated with a superuser."""
    con,cur = init_connection_new(get_wagtail_config())
    query = 'select is_superuser from auth_user left join login_usertoken on auth_user.id = login_usertoken.user_id where value=%s'
    cur.execute(query, (token,))
    data = cur.fetchall()
    close_connection(con,cur)
    if len(data) == 0:
        return False
    return data[0][0]

def get_email_from_token(token):
    """Returns email given token."""
    con,cur = init_connection_new(get_wagtail_config())
    query = 'select email from auth_user left join login_usertoken on auth_user.id = login_usertoken.user_id where value=%s'
    cur.execute(query, (token,))
    data = cur.fetchall()
    close_connection(con,cur)
    if len(data) == 0:
        return None
    return data[0][0]

def get_rqst_indexes(email):
    """Given Email, return list of request indexes."""
    con,cur = init_connection_new()
    cur.execute('select rindex from dsrqst where email=%s', (email,))
    data = cur.fetchall()
    indexes = make_list_from_index(data)
    close_connection(con, cur)

    return indexes

def update_sflag(sflag, rqstidx):
    """Upadates the sflag for a given request index."""
    assert sflag < 10
    init_connection()
    cursor.execute('update dsrqst set sublflag=%d where rindex=%s',(sflag, rqstidx))
    data = cursor.fetchall()

def get_user_id():
    """Get user id"""
    return pwd.getpwuid( os.getuid()).pw_name

def check_ds(ds):
    """Returns True if proper dataset id,
    otherwise returns False.

    A proper dataset id is either in format
    dxxxxxx, dsxxx.x, or xxx.x, and it exists
    in the database
    """
    if not (type(ds) is str or type(ds) is unicode):
        return False
    if len(ds) > 7 or len(ds) < 5:
        return False
    init_connection()
    cursor.execute('select distinct dsid from dataset')
    data = cursor.fetchall()
    data_list = make_list_from_index(data)
    return format_dataset_id(ds) in data_list

def get_all_datasets():
    """Returns all dataset information"""

    init_connection()
    cursor.execute('select dsid,title from dataset')
    data = cursor.fetchall()
    return data

def get_number_of_datasets():
    """Get the total number of datasets in the GDEX
    """
    con,cur =  init_connection_new(config=get_search_config())
    cond = "(d.type = 'P' or d.type = 'H') and d.dsid < 'd999000'"
    query = "select count(distinct dsid) from search.datasets as d where " + cond
    cur.execute(query)
    response = cur.fetchone()
    close_connection(con,cur)
    return response[0]

def get_gdex_volume():
    """Get the total volume of data in the GDEX
    Returns value in PB
    """
    con,cur =  init_connection_new()
    cond = "(s.type = 'P' or s.type = 'H') and s.dsid < 'd999000'"
    query = "select sum(d.dweb_size)/1.e15 from dataset as d left join search.datasets as s on d.dsid = s.dsid where " + cond
    cur.execute(query)
    response = cur.fetchone()
    close_connection(con,cur)
    return float(round(response[0], 2))

def get_total_requests(since=None):
    if since is None:
        since = datetime.now() - timedelta(days=365) # One year ago
    con,cur =  init_connection_new()
    query = f"select count(*) from dspurge where date_rqst > '{since.year}-{since.month}-{since.day}'"
    cur.execute(query)
    response = cur.fetchone()
    close_connection(con,cur)
    return response[0]


def get_top_datasets(top=15):
    rankings_file = '/data/local/gdexweb/media/metrics/rankings/rankingsYear.json'
    try:
        rankings = json.load(open(rankings_file))
        return rankings[:top]

    except FileNotFoundError as e:
        print(e)
        return 'Unknown'

def get_AI_datasets(limit=50):
    con,cur = init_connection_new(config=get_WGrML_config())
    query = f"select dsid,title from search.datasets where ai_ready = 'Y' limit {limit};"
    cur.execute(query)
    res = cur.fetchall()
    close_connection(con,cur)
    return res


def get_total_citations():
    """Get total number of citations"""
    con,cur = init_connection_new(config=get_WGrML_config())
    query = "select distinct v.dsid,c.DOI_work,e.title,d.pub_year from citation.data_citations as c left join dssdb.dsvrsn as v on v.doi = c.DOI_data left join citation.works as d on c.DOI_work = d.DOI left join dssdb.dataset as e on e.dsid = v.dsid ;"
    cur.execute(query)
    response = cur.fetchall()
    close_connection(con,cur)
    return len(response)

def get_number_of_unique_users(since=None):
    if since is None:
        since = datetime.now() - timedelta(days=365) # One year ago

    cur_year = datetime.now().year
    current_metrics_file = f'/data/local/gdexweb/media/metrics/json/{cur_year}_all.json'
    last_metrics_file = f'/data/local/gdexweb/media/metrics/json/{cur_year - 1}_all.json'
    try:
        metrics = json.load(open(current_metrics_file)) + json.load(open(last_metrics_file))
    except FileNotFoundError as e:
        print(e)
        return 'Unknown'

    total_unique_users = 0
    for year_month in metrics:
        year,month = year_month['Date'].split('-')
        obj_date = datetime(year=int(year), month=int(month), day=1)
        if obj_date > since:
            total_unique_users += year_month['Total Number of Unique Users']

    return total_unique_users

def get_number_of_unique_users_db(since=None):
    """Get total number of unique IPs from the database"""
    if since is None:
        since = datetime.now() - timedelta(days=366) # One year ago
    assert isinstance(since, datetime)

    cur_year = datetime.now().year
    last_year = since.year
    last_month = since.month
    last_day = since.day
    last_ymd = f'{last_year}-{last_month}-{last_day}'

    con,cur =  init_connection_new()

    query = f"select count(distinct(ip)) from allusage_{last_year} where date > '{last_ymd}'" + \
    f" union all select count(distinct(ip)) from allusage_{cur_year}"
    cur.execute(query)
    res = cur.fetchall()
    close_connection(con,cur)
    total_IPs = 0
    for i in res:
        total_IPs += int(i[0])
    return total_IPs


def get_volume_downloaded_db(since=None):
    """Get total volume downloaded from a datetime. Does not work on `since` > 2 years"""
    if since is None:
        since = datetime.now() - timedelta(days=365) # One year ago
    assert isinstance(since, datetime)

    cur_year = datetime.now().year
    last_year = since.year
    last_month = since.month
    last_day = since.day
    last_ymd = f'{last_year}-{last_month}-{last_day}'

    con,cur =  init_connection_new()

    query = f"select sum(size) from allusage_{last_year} where date > '{last_ymd}'" + \
    f" union all select sum(size) from allusage_{cur_year}"
    cur.execute(query)
    res = cur.fetchall()
    close_connection(con,cur)
    total_volume_downloaded = 0
    for i in res:
        total_volume_downloaded += i[0]
    return math.floor(total_volume_downloaded/1000/1000/1000/1000/1000)

def get_volume_downloaded(since=None):
    if since is None:
        since = datetime.now() - timedelta(days=365) # One year ago

    cur_year = datetime.now().year
    current_metrics_file = f'/data/local/gdexweb/media/metrics/json/{cur_year}_all.json'
    last_metrics_file = f'/data/local/gdexweb/media/metrics/json/{cur_year - 1}_all.json'
    try:
        metrics = json.load(open(current_metrics_file)) + json.load(open(last_metrics_file))
    except FileNotFoundError as e:
        print(e)
        return 'Unknown'

    total_volume_downloaded = 0
    for year_month in metrics:
        year,month = year_month['Date'].split('-')
        obj_date = datetime(year=int(year), month=int(month), day=1)
        if obj_date > since:
            total_volume_downloaded += year_month['Total Volume Downloaded (TB)']

    return total_volume_downloaded

def add_ds(ds):
    """Adds 'ds' to input string if not already there.
    Assumes ds str is properly formatted, see check_ds.
    """
    if ds[0:2] == 'ds':
        return ds
    return 'ds'+ds

def remove_ds(ds):
    """Removes 'ds' input string if not already there.
    Assumes ds str is properly formatted, see check_ds.
    """
    if ds[0:2] != 'ds':
        return ds
    return ds[2:]

def dash_to_dot(ds):
    ds = str(ds)
    ds = ds.replace('-','.')
    return ds

def format_dataset_id(dsid, remove_ds=False):
    """ Returns the dataset ID formatted either as
        'dsnnn.n' or 'dnnnnnn'.  The format
        returned by this function is determined by
        the parameter flag settings.NEW_DATASET_ID
        (if True, return 'dnnnnnn', if False, return
        'dsnnn.n').  The input argument 'dsid' can
        also include a dash, e.g. 'dsnnn-n', and the
        code will convert it to the correct format.
    """

    # If remove_ds = True, return legacy dsid without
    # leading 'ds', e.g. 'nnn.n'
    if remove_ds:
        ds = ''
    else:
        ds = 'ds'

    # check for format 'dnnnnnn'
    ms = re.match(r'^([a-z]{1})(\d{3})(\d{3})$', dsid)
    if ms:
        if settings.NEW_DATASET_ID:
            return dsid
        else:
            return '{}{:03d}.{}'.format(ds, int(ms.group(2)), int(ms.group(3)))

    # check for legacy format 'dsnnn.n', 'dsnnn-n', 'nnn.n', and
    # 'nnn-n'.  Change dash '-' to dot '.' if necessary.
    ms = re.match(r'^(ds)?(\d{3})(-|\.)(\d{1})$', dsid)
    if ms:
        if settings.NEW_DATASET_ID:
            return 'd{:03d}{:03d}'.format(int(ms.group(2)), int(ms.group(4)))
        else:
            return '{}{}.{}'.format(ds, ms.group(2), ms.group(4))

def is_url_reachable(url):
    """
    Checks if a URL is reachable.  Returns True if reachable, False otherwise.
    """
    try:
        response = requests.head(url)
        response.raise_for_status()
        return True
    except requests.exceptions.HTTPError:
        return False
    except requests.exceptions.RequestException:
        return False
    except requests.exceptions.ConnectionError:
        return False
    except requests.exceptions.Timeout:
        return False

class Filelist(object):

    def __init__(self, title=None, note=None):
        self.title = title
        self.note = note
        self.parent = {}
        self.groups = []

    def add_group(self, group):
        self.groups.append(group)

    def add_parent(self, parent_group):
        self.parent.update(parent_group)

    def get_data(self, dsid=None, locflag=None, filter_wfile=None):
        filelist = {
            'title':self.title,
            'note':self.note,
            'parent':self.parent}
        filelist['groups'] = self.groups
        if dsid:
            filelist['dsid'] = dsid
        if locflag:
            filelist['locflag'] = locflag
        else:
            filelist['locflag'] = 'G'
        if filter_wfile:
            filelist['filter_wfile'] = filter_wfile
        for i,j in enumerate(filelist['groups']):
            if isinstance(j,Group):
                filelist['groups'][i] = j.get_data()
        return filelist

    def has_data(self):
        return len(self.groups) > 0

class Group(object):

    def __init__(self, title=None, note=None, group_id=None):
        self.title = title
        self.note = note
        self.group_id = group_id
        self.is_group_summary = True
        self.gindex = 0
        self.webpath = None
        self.paginator = {'needs_pagination':False,'max_pages':0, 'cur_page':0}
        self.column_headers = {}
        self.rows = []
        self.total_file_count = 0

    def has_data(self):
        return len(self.rows) > 0

    def add_row(self,row):
        for r in row:
            self.column_headers.update({r['name']:None})
        self.rows.append(row)

    def set_gindex(self, gindex):
        self.gindex = gindex

    def set_webpath(self, webpath):
        self.webpath = webpath

    def set_total_file_count(self, total_files):
        self.total_file_count = total_files

    def set_paginator_pages(self, pages, cur_page=0):
        self.paginator['needs_pagination'] = True
        self.paginator['max_pages'] = int(pages)
        self.paginator['cur_page'] = int(cur_page)

    def get_data(self, dsid=None):
        headers = list(self.column_headers.keys())
        # All groups/tables will have these keys
        group = {
                 'title':self.title,
                 'note': self.note,
                 'is_group_summary' : self.is_group_summary,
                 'column_headers' : headers,
                 'group_id' : self.group_id,
                 'paginator' : self.paginator,
                 'gindex' : self.gindex,
                 'webpath' : self.webpath,
                 'total_file_count': self.total_file_count,
                }
        if dsid:
            group['dsid'] = dsid
        group['rows'] = self.rows
        return group

    def __len__(self):
        return len(rows)


def get_abstract(dsid):
    """Get the abstract for a given dataset with additional parsing
    Args:
        dsid (str): six digit id for dataset (dxxxxxx)
    Returns:
        dict: Dictionary containing:
            - abstract (str): Cleaned abstract text
            - note (str): Any note/warning text found
            - urls (list): List of URLs found in the abstract
    """
    con, cur = init_connection_new(get_wagtail_config())
    query = 'select abstract from dataset_description_datasetdescriptionpage where dsid=%s'
    cur.execute(query, (dsid,))
    raw_data = cur.fetchone()[0]
    close_connection(con, cur)

    result = {
        'abstract': '',
        'note': '',
        'urls': []
    }

    unicode_escapes = {
        '\\u003C': '<',
        '\\u003E': '>',
        '\\u0026': '&',
        '\\u0022': '"',
        '\\u0027': "'",
        '\\u002F': '/',
        '\\u003D': '='
    }

    decoded_text = raw_data
    for escape, char in unicode_escapes.items():
        decoded_text = decoded_text.replace(escape, char)

    url_pattern = r'https?://[^\s<>"{}|\\^\[\]]+[^\s<>"{}|\\^\[\].,;:!?]'
    remaining_urls = re.findall(url_pattern, decoded_text)
    result['urls'].extend(remaining_urls)
    result['urls'] = list(set(result['urls']))

    # look for font tags with color="red" or similar note patterns
    note_section_pattern = r'(<font[^>]*color\s*=\s*["\']red["\'][^>]*>.*?</font>)'
    note_match = re.search(note_section_pattern, decoded_text, re.IGNORECASE | re.DOTALL)

    if note_match:
        full_note_html = note_match.group(1)

        clean_note = full_note_html
        clean_note = re.sub(r'<[^>]+>', '', clean_note)
        clean_note = re.sub(r'\s+', ' ', clean_note).strip()
        clean_note = re.sub(r'^PLEASE NOTE[.:\s]*', '', clean_note, flags=re.IGNORECASE)
        result['note'] = clean_note

        clean_abstract = decoded_text.replace(note_match.group(0), '')
    else:
        # look for other note patterns if font tag not found
        note_patterns = [
            r'(PLEASE NOTE[^.]*\.)',  # PLEASE NOTE with everything until first period
            r'(NOTE[.:][^.]*\.)'      # NOTE: with everything until first period
        ]

        clean_abstract = decoded_text
        for pattern in note_patterns:
            matches = re.findall(pattern, decoded_text, re.IGNORECASE | re.DOTALL)
            if matches:
                full_note_section = matches[0].strip()
                clean_note = re.sub(r'<[^>]+>', '', full_note_section)
                clean_note = re.sub(r'^PLEASE NOTE[.:\s]*', '', clean_note, flags=re.IGNORECASE)
                clean_note = re.sub(r'^NOTE[.:\s]*', '', clean_note, flags=re.IGNORECASE)
                clean_note = re.sub(r'\s+', ' ', clean_note).strip()
                result['note'] = clean_note
                clean_abstract = decoded_text.replace(full_note_section, '')
                break

    clean_abstract = re.sub(r'<[^>]+>', '', clean_abstract)
    clean_abstract = re.sub(r'\s+', ' ', clean_abstract)
    clean_abstract = clean_abstract.strip()

    clean_abstract = re.sub(r'\s+[,;:]\s*$', '', clean_abstract)
    clean_abstract = re.sub(r'^\s*[,;:]\s+', '', clean_abstract)

    result['abstract'] = clean_abstract

    return result


def get_acknowledgement(dsid):
    """Get the acknowledgement for a given dataset
    Args:
        dsid (str): six digit id for dataset (dxxxxxx)
    Returns:
        str: The acknowledgement text for the dataset, or None if not found
    """
    con, cur = init_connection_new(get_wagtail_config())
    query = 'select acknowledgement from dataset_description_datasetdescriptionpage where dsid=%s'
    cur.execute(query, (dsid,))
    result = cur.fetchone()
    close_connection(con, cur)

    if result is None or result[0] is None:
        return None

    data = result[0]
    clean_text = re.sub(r'</?p>', '', data)
    clean_text = clean_text.strip()

    if not clean_text:
        return None

    return clean_text

def get_temporal_range(dsid):
    """Get the temporal range for a given dataset
    Args:
        dsid (str): six digit id for dataset (dxxxxxx)
    Returns:
        dict: Dictionary containing temporal range information
    """
    con, cur = init_connection_new(get_wagtail_config())
    query = 'select temporal from dataset_description_datasetdescriptionpage where dsid=%s'
    cur.execute(query, (dsid,))
    data = cur.fetchone()[0]
    close_connection(con, cur)

    full_range = data['full']
    start_date_str, end_date_str = full_range.split(' to ')
    start_date_clean = start_date_str.strip()
    end_date_clean = end_date_str.strip()

    result = {
        'start_date': start_date_clean,
        'end_date': end_date_clean,
        'data_groups': []
    }

    for group in data['groups']:
        if '(' in group and ')' in group:
            date_part = group.split(' (')[0]
            description_part = group.split(' (')[1].rstrip(')')

            if ' to ' in date_part:
                group_start, group_end = date_part.split(' to ')
                group_start_clean = group_start.strip()
                group_end_clean = group_end.strip()
            else:
                group_start_clean = date_part.strip()
                group_end_clean = date_part.strip()

            result['data_groups'].append({
                'description': description_part,
                'start_date': group_start_clean,
                'end_date': group_end_clean
            })

    return result

def categorize_variables_manual(variables):
    categories = {
        'temperature': [],
        'precipitation': [],
        'wind': [],
        'pressure': [],
        'humidity': [],
        'cloud': [],
        'radiation': [],
        'other': []
    }

    for var in variables:
        var_lower = var.lower()
        if 'temperature' in var_lower or 'heat' in var_lower:
            categories['temperature'].append(var)
        elif 'precipitation' in var_lower or 'rain' in var_lower or 'snow' in var_lower:
            categories['precipitation'].append(var)
        elif 'wind' in var_lower:
            categories['wind'].append(var)
        elif 'pressure' in var_lower:
            categories['pressure'].append(var)
        elif 'humidity' in var_lower:
            categories['humidity'].append(var)
        elif 'cloud' in var_lower:
            categories['cloud'].append(var)
        elif 'radiative' in var_lower or 'flux' in var_lower:
            categories['radiation'].append(var)
        else:
            categories['other'].append(var)

    return {k: v for k, v in categories.items() if v}

#@lru_cache(maxsize=128)
def fetch_gcmd_concepts():
    """Fetch GCMD science keywords concepts and cache the result"""
    try:
        url = "https://gcmd.earthdata.nasa.gov/kms/concepts/concept_scheme/sciencekeywords/?format=json&page_num=1&page_size=2000"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        concepts = data.get('concepts', [])
        return concepts
    except requests.RequestException as e:
        return []

#@lru_cache(maxsize=256)
def get_concept_category(uuid):
    """Get the broader category for a given concept UUID"""
    try:
        url = f"https://gcmd.earthdata.nasa.gov/kms/concept/{uuid}?format=json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        broader = data.get('broader', [])

        if broader and len(broader) > 0 and 'prefLabel' in broader[0]:
            category = broader[0]['prefLabel'].lower()
            return category
        else:
            return 'other'
    except requests.RequestException as e:
        return 'other'

def categorize_variables(variables):
    """Categorize variables using GCMD API"""
    concepts = fetch_gcmd_concepts()
    if not concepts:
        return categorize_variables_manual(variables)

    variable_to_uuid = {}

    for var in variables:
        var_lower = var.lower()

        found_exact = False
        for concept in concepts:
            pref_label = concept.get('prefLabel', '').lower()
            if pref_label and var_lower == pref_label:
                variable_to_uuid[var] = concept.get('uuid')
                found_exact = True
                break

        if not found_exact:
            for concept in concepts:
                pref_label = concept.get('prefLabel', '').lower()
                if pref_label and (var_lower in pref_label or pref_label in var_lower):
                    variable_to_uuid[var] = concept.get('uuid')
                    break

    categories = {}

    for var in variables:
        if var in variable_to_uuid:
            uuid = variable_to_uuid[var]
            category = get_concept_category(uuid).title()
        if category not in categories:
            categories[category] = []
        categories[category].append(var)

    return {k: v for k, v in categories.items() if v}

def get_variables(dsid):
    """Get the variables for a given dataset
    Args:
        dsid (str): six digit id for dataset (dxxxxxx)
    Returns:
        dict: Dictionary containing variables information
    """
    con, cur = init_connection_new(get_wagtail_config())
    query = 'select variables from dataset_description_datasetdescriptionpage where dsid=%s'
    cur.execute(query, (dsid,))
    data = cur.fetchone()[0]
    close_connection(con, cur)

    variables_list = data.get('gcmd', [])
    variables_sorted = sorted(variables_list)

    result = {
        'count': len(variables_sorted),
        'variables': variables_sorted,
        'categories': categorize_variables(variables_sorted),
        'message': "The variables represented in this API include but are not limited to those available in the dataset. Additional variables may be present in the actual data files."
    }

    return result

def parse_authors(authors_string):
    """
    Parse authors string into a clean array of author names

    Args:
        authors_string (str): Raw authors string from publication data

    Returns:
        list: List of cleaned author names
    """
    if not authors_string:
        return []

    authors_string = re.sub(r'<[^>]+>', '', authors_string)

    authors = []
    raw_authors = authors_string.split(',')

    for author in raw_authors:
        author = author.strip()

        if not author:
            continue

        author = re.sub(r'[.;]+$', '', author)
        author = re.sub(r'^(and|&)\s+', '', author, flags=re.IGNORECASE)
        if author.strip():
            authors.append(author.strip())

    return authors

def clean_publication(pub_text):
    """Clean publications data with author parsing"""
    if not pub_text:
        return None

    pub_text = pub_text.replace('&amp;amp;', '&')
    pub_text = pub_text.replace('&amp;', '&')

    url_match = re.search(r'<a href="([^"]+)"[^>]*>([^<]+)</a>', pub_text)
    url = url_match.group(1) if url_match else None
    link_text = url_match.group(2) if url_match else None

    clean_text = re.sub(r'<[^>]+>', '', pub_text)

    year_match = re.search(r'(\d{4}):', clean_text)
    year = year_match.group(1) if year_match else None

    # journal name
    journal_match = re.search(r'<i>([^<]+)</i>', pub_text)
    journal = journal_match.group(1) if journal_match else None

    # DOI
    doi_match = re.search(r'DOI:\s*([^)]+)', clean_text)
    doi = doi_match.group(1).strip() if doi_match else None

    # volume and pages
    volume_match = re.search(r'<b>([^<]+)</b>', pub_text)
    volume_pages = volume_match.group(1) if volume_match else None

    # authors
    authors_string = None
    if year:
        authors_match = re.search(r'^([^:]+)' + year, clean_text)
        authors_string = authors_match.group(1).strip().rstrip(',') if authors_match else None

    authors_array = parse_authors(authors_string)
    authors_array = [author for author in authors_array if any(len(word.strip('.,')) >= 3 for word in author.split())]

    # title
    title = link_text if link_text else None
    if not title and year:
        title_match = re.search(year + r':\s*([^.]+)', clean_text)
        title = title_match.group(1).strip() if title_match else None

    return {
        'authors': authors_array,
        'authors_text': authors_string,
        'year': year,
        'title': title,
        'journal': journal,
        'volume_pages': volume_pages,
        'doi': doi,
        'url': url
    }

def get_publications(dsid):
    """Get the publications for a given dataset
    Args:
        dsid (str): six digit id for dataset (dxxxxxx)
    Returns:
        dict: Dictionary containing publications information
    """
    con, cur = init_connection_new(get_wagtail_config())
    query = 'select publications from dataset_description_datasetdescriptionpage where dsid=%s'
    cur.execute(query, (dsid,))
    data = cur.fetchone()[0]
    close_connection(con, cur)

    publications_list = data if isinstance(data, list) else []
    cleaned_publications = []

    for pub in publications_list:
        cleaned_pub = clean_publication(pub)
        if cleaned_pub:
            cleaned_publications.append(cleaned_pub)

    result = {
        'count': len(cleaned_publications),
        'publications': cleaned_publications
    }

    return result

def get_data_license(dsid):
    """Get the data license for a given dataset
    Args:
        dsid (str): six digit id for dataset (dxxxxxx)
    Returns:
        dict: Dictionary containing information regarding the data license (name and url)
    """
    con, cur = init_connection_new(get_wagtail_config())
    query = 'select data_license from dataset_description_datasetdescriptionpage where dsid=%s'
    cur.execute(query, (dsid,))
    data = cur.fetchone()[0]
    close_connection(con, cur)

    result = {
        'name': data['name'],
        'url': data['url']
    }

    return result

def get_data_types(dsid):
    """Get the data types for a given dataset
    Args:
        dsid (str): six digit id for dataset (dxxxxxx)
    Returns:
        str: The data types text for the dataset
    """
    con, cur = init_connection_new(get_wagtail_config())
    query = 'select data_types from dataset_description_datasetdescriptionpage where dsid=%s'
    cur.execute(query, (dsid,))
    data = cur.fetchone()[0]
    close_connection(con, cur)

    return data

def get_data_formats(dsid):
    """Get the data formats for a given dataset
    Args:
        dsid (str): six digit id for dataset (dxxxxxx)
    Returns:
        str: Dictionary containing information regarding the data formats (description and url)
    """
    con, cur = init_connection_new(get_wagtail_config())
    query = 'select data_formats from dataset_description_datasetdescriptionpage where dsid=%s'
    cur.execute(query, (dsid,))
    data = cur.fetchone()[0]
    close_connection(con, cur)

    formats_list = data if isinstance(data, list) else []
    processed_formats = []

    for format_item in formats_list:
        processed_format = {
            'description': format_item.get('description', 'Unknown format'),
            'url': format_item.get('url', None),
            'has_documentation': format_item.get('url') is not None
        }
        processed_formats.append(processed_format)

    result = {
        'count': len(processed_formats),
        'data_formats': processed_formats
    }

    return result

def clean_spatial_details(details_list):
    cleaned_details = []
    for detail in details_list:
        if detail:
            clean_detail = detail.replace('&deg;', '°')
            clean_detail = clean_detail.replace('&times;', '×')
            clean_detail = re.sub(r'<small>([^<]+)</small>', r'(\1)', clean_detail)
            clean_detail = re.sub(r'<[^>]+>', '', clean_detail)
            cleaned_details.append(clean_detail.strip())

    return cleaned_details

def parse_spatial_details(details):
    """Parse spatial details to extract resolution and grid information"""
    parsed_info = {}

    for detail in details:
        # Extract resolution ("0.703° x ~0.702°")
        resolution_match = re.search(r'([\d.]+)°?\s*x\s*~?([\d.]+)°?', detail)
        if resolution_match:
            parsed_info['resolution'] = {
                'longitude': float(resolution_match.group(1)),
                'latitude': float(resolution_match.group(2)),
                'units': 'degrees'
            }

        # Extract coordinate ranges
        coord_match = re.search(r'from\s+([\d.]+[EW])\s+to\s+([\d.]+[EW])\s+and\s+([\d.]+[NS])\s+to\s+([\d.]+[NS])', detail)
        if coord_match:
            parsed_info['coordinate_range'] = {
                'longitude_start': coord_match.group(1),
                'longitude_end': coord_match.group(2),
                'latitude_start': coord_match.group(3),
                'latitude_end': coord_match.group(4)
            }

        # Extract grid dimensions ("512 x 256")
        grid_match = re.search(r'\((\d+)\s*x\s*(\d+)', detail)
        if grid_match:
            parsed_info['grid_dimensions'] = {
                'longitude_points': int(grid_match.group(1)),
                'latitude_points': int(grid_match.group(2))
            }

        # Extract grid type
        if 'Gaussian' in detail:
            parsed_info['grid_type'] = 'Gaussian'
        elif 'Regular' in detail:
            parsed_info['grid_type'] = 'Regular'

    return parsed_info

def get_spatial_coverage(dsid):
    """Get the spatial coverage for a given dataset
    Args:
        dsid (str): six digit id for dataset (dxxxxxx)
    Returns:
        dict: Dictionary containing spatial coverage information
    """
    con, cur = init_connection_new(get_wagtail_config())
    query = 'select spatial_coverage from dataset_description_datasetdescriptionpage where dsid=%s'
    cur.execute(query, (dsid,))
    data = cur.fetchone()[0]
    close_connection(con, cur)

    details = clean_spatial_details(data.get('details', []))

    def process_bound(value):
        """Process a bound value according to directional rules"""
        if value is None:
            return None

        value_str = str(value).strip()

        if value_str.endswith('N'):
            # north - positive value, remove N
            return float(value_str[:-1])
        elif value_str.endswith('S'):
            # south - make negative, remove S
            return -float(value_str[:-1])
        elif value_str.endswith('W'):
            # west - make negative, remove W
            return -float(value_str[:-1])
        elif value_str.endswith('E'):
            # east - make sure positive, remove E
            return abs(float(value_str[:-1]))

    result = {
        'bounds': {
            'north': process_bound(data.get('north')),
            'south': process_bound(data.get('south')),
            'east': process_bound(data.get('east')),
            'west': process_bound(data.get('west')),
            'lat_units': 'degrees north',
            'lon_units': 'degrees east'
        }
    }

    # Add parsed details if available
    if details:
        parsed_details = parse_spatial_details(details)
        result.update(parsed_details)

    return result

def categorize_contributors(contributors):
    """Add category field to each contributor based on organization type"""
    categorized_contributors = []

    for contributor in contributors:
        # Create a copy of the contributor to avoid modifying the original
        contributor_with_category = contributor.copy()

        org_id = contributor.get('id', '').upper()
        org_name = contributor.get('name', '').upper()

        # Categorize based on ID patterns and keywords
        if any(keyword in org_id for keyword in ['DOC', 'NOAA', 'DOE', 'NASA', 'USGS', 'EPA']) or 'U.S.' in org_name:
            contributor_with_category['category'] = 'government'
        elif 'UCAR' in org_id:
            contributor_with_category['category'] = 'ucar'
        elif 'UNIVERSITY' in org_name or 'INSTITUTE' in org_name:
            contributor_with_category['category'] = 'academic'
        else:
            contributor_with_category['category'] = 'other'

        categorized_contributors.append(contributor_with_category)

    return categorized_contributors

def get_contributors(dsid):
    """Get the data contributors for a given dataset

    Args:
        dsid (str): six digit id for dataset (dxxxxxx)

    Returns:
        dict: Dictionary containing data contributors information
    """
    con, cur = init_connection_new(get_wagtail_config())
    query = 'select contributors from dataset_description_datasetdescriptionpage where dsid=%s'
    cur.execute(query, (dsid,))
    data = cur.fetchone()[0]
    close_connection(con, cur)

    contributors_list = data if isinstance(data, list) else []

    categorized_contributors = categorize_contributors(contributors_list)

    result = {
        'count': len(categorized_contributors),
        'contributors': categorized_contributors
    }

    return result

def get_total_volume(dsid):
    """Get the total volume for a given dataset
    Args:
        dsid (str): six digit id for dataset (dxxxxxx)
    Returns:
        dict: Dictionary containing information regarding the total volume and volume groups
    """
    con, cur = init_connection_new(get_wagtail_config())
    query = 'select volume from dataset_description_datasetdescriptionpage where dsid=%s'
    cur.execute(query, (dsid,))
    data = cur.fetchone()[0]
    close_connection(con, cur)

    result = {
        'total_volume': data['full'],
        'volume_groups': data['groups']
    }

    return result

def get_related_resources(dsid):
    """Get the related resources list for a given dataset
    Args:
        dsid (str): six digit id for dataset (dxxxxxx)
    Returns:
        str: Dictionary containing information regarding the related resources list
    """
    con, cur = init_connection_new(get_wagtail_config())
    query = 'select related_rsrc_list from dataset_description_datasetdescriptionpage where dsid=%s'
    cur.execute(query, (dsid,))
    data = cur.fetchone()[0]
    close_connection(con, cur)

    rsrc_list = data if isinstance(data, list) else []
    processed_resources = []

    for resource in rsrc_list:
        rsrc = {
            'description': resource.get('description'),
            'url': resource.get('url', None)
        }
        processed_resources.append(rsrc)

    result = {
        'count': len(processed_resources),
        'resources_list': processed_resources
    }

    return result

def get_related_datasets(dsid):
    """Get the related datasets list for a given dataset
    Args:
        dsid (str): six digit id for dataset (dxxxxxx)
    Returns:
        str: Dictionary containing information regarding the related datasets list
    """
    con, cur = init_connection_new(get_wagtail_config())
    query = 'select related_dslist from dataset_description_datasetdescriptionpage where dsid=%s'
    cur.execute(query, (dsid,))
    data = cur.fetchone()[0]
    close_connection(con, cur)

    datasets_list = data if isinstance(data, list) else []
    processed_ds = []

    for ds in datasets_list:
        dataset = {
            'dsid': ds.get('dsid'),
            'title': ds.get('title')
        }
        processed_ds.append(dataset)

    result = {
        'count': len(processed_ds),
        'resources_list': processed_ds
    }

    return result

def get_all_datasets():
    con, cur = init_connection_new(get_wagtail_config())
    query = 'SELECT DISTINCT dsid, dstitle FROM dataset_description_datasetdescriptionpage ORDER BY dsid'
    cur.execute(query)
    results = cur.fetchall()
    close_connection(con, cur)

    datasets_list = []
    for row in results:
        datasets_list.append({
            'id': row[0],
            'title': row[1]
        })

    response = {
        'count': len(datasets_list),
        'datasets': datasets_list
    }

    return response
