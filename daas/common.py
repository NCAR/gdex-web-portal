#!/usr/bin/env python
import sys
import os
import pdb
import pwd
from django.conf import settings
import psycopg2
import xml.etree.ElementTree as ET
import glob
from datetime import datetime

import logging
logger = logging.getLogger(__name__)

"""
This module contains database interaction and common data
management functions.
"""

conn = None
cursor = None

# cache is designed where each key is a tablename.
cache = {}

def get_IGrML_config():
    return settings.RDADB['IGrML_config_pg']

def get_search_config():
    return settings.RDADB['search_config_pg']

def get_WGrML_config():
    return settings.RDADB['WGrML_config_pg']

def get_dssdb_config():
    return settings.RDADB['dssdb_config_pg']

def init_connection(config=None, schema_name=None):
    """initializes connection.
    prefereable to call this function first since you can catch
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
    
    return cursor

def set_schema(schema_name=None):
    """ Set the DB schema search path.  Default is 'dssdb'. """

    if schema_name is None:
        schema_name = 'dssdb'
    
    try:
        cursor.execute(sql.SQL("SET search_path TO '{}'").format(sql.Identifier(schema_name)))
        logger.info("Search path set to schema '{schema_name}'.")

    except Exception as e:
        logger.error("{}".format(e))

def close_connection():
    """Close connection and set cursor/conn obj to None."""
    global conn
    global cursor
    if cursor is None:
        cursor.close()
    if conn is not None:
        conn.close()
    conn = None
    cursor = None

def change_keys(in_dict, key_map):
    """Change keys of a dict.
    If key map has value of None, remove key"""
    for key in in_dict.keys():
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
        elements.extend(filter(lambda var: var.tag == tag_name, root.getchildren() ))
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
        for child in level.getchildren():
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
        for child in param.getchildren():
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

    xml_location = '/gpfs/u/home/rdadata/share/metadata/ParameterTables/'
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
    level_dict = check_cache('level_codes', map_name)
    if level_dict is not None:
        return level_dict[code]

    xml_location = '/gpfs/u/home/rdadata/share/metadata/LevelTables/'
    glob_str = xml_location + '*'+map_name+'.xml'
    filenames = glob.glob(glob_str)
    if len(filenames) > 1:
        raise ValueError('Glob should only return 1 filename')
    if len(filenames) == 0:
        raise ValueError('Glob couldn\'t find file. glob string is: '+glob_str )
    levels = get_levels_from_xml(filenames[0])
    add_to_cache('level_codes', map_name, levels)
    return levels[code]

def get_param_inventory(dsid, param_code):
    """Returns param_code with appropriate inventory number.
    """
    dsid = add_ds(dsid)
    dsid = "".join(dsid.split('.'))
    like_str = dsid + "%" + param_code
    init_connection(config=get_IGrML_config(), schema_name=settings.RDADB['pg_schemas']['IGrML'])
    query = "show tables like %s"
    cursor.execute(query, (like_str,))
    response = cursor.fetchone()
    if response is None:
        return response
    # e.g. "ds0833_inventory_3!7-0.2-1:0.0.21"
    inventory_str = response[0]
    new_param_code = inventory_str.split('_')[-1]
    return new_param_code

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
    dsid = remove_ds(dsid)
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
    dsid = remove_ds(dsid)
    init_connection(config=get_WGrML_config(), schema_name=settings.RDADB['pg_schemas']['WGrML'])
    column_names = ('format_code', 'time_range_code', 'grid_definition_code', \
            'parameter', 'level_type_codes', 'start_date','end_date', 'time_range')
    column_names_str = ','.join(column_names)
    query = "select "+ column_names_str +" from summary left join time_ranges on summary.time_range_code=time_ranges.code where dsid=%s"
    cursor.execute(query, (dsid,))
    return to_dict(column_names, cursor.fetchall())

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
    dsid = add_ds(dsid)
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

def make_list_from_index(list_of_iterable, index=0):
    """Makes a single list from a list of iterables, optionally giving index.
    """
    return [i[index] for i in list_of_iterable]

def get_request_info(rindex):
    """Returns a dict of request indexes.
    Return keys are:
    'status'
    'NCAR_contact'
    'date_ready'
    'date_rqst'
    'date_purge'
    'subset_info'
    'request_id'
    'rinfo'
    """
    info = check_cache('rqst_info', rindex)
    if info is not None:
        return info
    column_names = ('date_rqst', 'date_ready', 'date_purge',\
            'status','rqstid', 'specialist', 'note', 'rqstid', 'rinfo')
    init_connection()
    query = 'select ' + ','.join(column_names) + ' from dsrqst where rindex=%s'
    cursor.execute(query, (rindex,))
    request = cursor.fetchall()
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

    add_to_cache('rqst_info', rindex, request)

    return request

def get_request_indexes(email):
    """Returns rindexes of requests associated with email"""
    column_names = ('rindex')
    init_connection()
    query = 'select rindex from dsrqst where email=%s'
    cursor.execute(query, (email,))
    request = cursor.fetchall()
    return request

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

def get_tindex_from_webfile(wfile, dsid):
    """Get the tindex of a webfile"""
    dsid = add_ds(dsid)
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
    query = "SELECT webID from "+table+" where code=%s"
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
    init_connection()
    query = 'select wfile,size,tindex from wfrqst where rindex=%s'
    cursor.execute(query, (request_index,))
    files = cursor.fetchall()
    return to_dict(('wfile','size','tindex'), files)

def get_tar_file(tindex):
    """Get's information about tar file given an index
    """
    tar_info = check_cache('tindex', tindex)
    if tar_info is not None:
        return tar_info
    init_connection()
    column_names = ('fcount', 'size', 'data_format', 'wfile')
    query = 'select '+ (','.join(column_names)) +' from tfrqst where tindex=%s'
    cursor.execute(query, (tindex,))
    tar_info = to_dict(column_names, cursor.fetchall())
    return tar_info

def get_status_map():
    """Returns a dict of Status key to long name.
    """
    status_map = {
    'O' : 'Completed',
    'E' : 'Error',
    'Q' : 'Queued for Processing',
    'P' : 'Set for Purge'
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

def get_rqst_indexes(email):
    """Given Email, return list of request indexes."""
    indexes = check_cache('request_indexes', email)
    if indexes is not None:
        return indexes
    init_connection()
    cursor.execute('select rindex from dsrqst where email=%s', (email,))
    data = cursor.fetchall()
    indexes = make_list_from_index(data)

    add_to_cache('request_indexes', email, indexes)
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
    """Returns true if proper dataset id,
    otherwise returns false.

    A proper dataset id is either in format
    dsxxx.x or xxx.x and it exists in database
    """
    if not (type(ds) is str or type(ds) is unicode):
        return False
    if len(ds) > 7 or len(ds) < 5:
        return False
    init_connection()
    cursor.execute('select distinct dsid from dataset')
    data = cursor.fetchall()
    data_list = make_list_from_index(data)
    return add_ds(ds) in data_list

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
