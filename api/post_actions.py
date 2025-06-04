#!/usr/bin/env python
import sys
import os
import subprocess
import pdb
import json
import re
from subprocess import check_output
from datetime import datetime
from . import common
from . import get_actions
from .RDA_Response import RDA_Response


def purge(request_index, email=None):
    response = RDA_Response()
    if email is None:
        email = common.get_local_emailname()
    rqst_indexes = common.get_rqst_indexes(email)
    if int(request_index) not in rqst_indexes:
        response.add_error_message(421)
        error_msg = 'Request index: "'+request_index+'" does not exist for email: "'+email
        response.add_message(error_msg)
        return response

    rqst_info = common.get_request_info(request_index)
    if rqst_info['status'] == 'Set for Purge':
        response.add_error_message(442)
        return response
    if rqst_info['status'] != 'Completed' and rqst_info['status'] != 'Error':
        response.add_error_message(rqst_info['status'])
        response.add_error_message(441)
        return response

    date_purge = get_purge_date()
    try:
        rdams_purge(request_index, date_purge, '00:00:00')
    except Exception as e:
        print(e)
        response.add_error_message(461)
        return response
    response.add_data({'purge_successful':'true'})

    return response

def rdams_purge(rindex, purge_date, purge_time):
    """
    Sets rindex to Purge state at given time. Note: this does not actually delete the request
    as purging is periodically done on a cron.

    Args:
        rindex (int): 6 digit request index.
        purge_date (str): Date at which to purge in format YYYY-MM-DD
        purge_time (str): Time at which to purge in format HH:MM
    """
    from rda_python_common import PgDBI
    
    donereq = PgDBI.pgget("dsrqst", "*", "rindex =" + str(rindex))
    donereq['date_purge'] = str(purge_date)
    donereq['time_purge'] = str(purge_time)
    donereq['status'] = "P"
    msg = PgDBI.pgupdt("dsrqst", donereq, "rindex="+str(rindex))

def get_purge_date():
    """Return string formatted purge date.
    """
    purge_date = datetime.now()
    return purge_date.strftime('%Y-%m-%d')

def subset_json_checks(in_json, response):
    """Checks for consistency in json keys.
    Multiple errors will be recorded in response."""
    # Check that certain keywords are present
    if 'dataset' not in in_json:
        response.add_error_message("'dataset' keyword not found in JSON.")
    if 'date' not in in_json:
        response.add_error_message("'date' keyword not found in JSON.")
    elif 'param' not in in_json:
        response.add_error_message("'param' keyword not found in JSON.")
    elif in_json['param'] == "" or in_json['param'] is None:
        msg = "keyword 'param' has no value. This may cause subsetting to fail for some datasets"
        response.add_message(msg)

    if 'datetype' in in_json:
        valid_datetypes = set(['valid', 'init'])
        if in_json['datetype'] not in valid_datetypes:
            error_msg = "'datetype': '"+in_json['datetype']+"' not found in JSON."
            response.add_error_message(error_msg)

    # Check for CSV errors
    if 'oformat' in in_json and in_json['oformat'].lower() == 'csv':
        if 'nlat' in in_json and 'slat' in in_json and 'elon' in in_json and 'wlon' in in_json:
            if in_json['nlat'] != in_json['slat'] or in_json['wlon'] != in_json['elon']:
                response.add_error_message('CSV files must only be a single point and single parameter.')
        else:
            response.add_error_message('Format is CSV, and missing elon, wlon, nlat, and/or slat')
   # elif 'level' not in in_json:
   #     response.add_error_message('\'level\' keyword not found in JSON.')
    # Check that lat/lon value are available and correct
    try:
        if 'nlat' in in_json:
            if 'slat' not in in_json:
                response.add_error_message("'nlat' keyword found in JSON, but not 'slat'.")
            elif abs(float(in_json['nlat'])) > 90:
                response.add_error_message("'nlat' value must fall between 90 and -90.")
            elif float(in_json['nlat']) <  float(in_json['slat']):
                response.add_error_message("'nlat' must be greater than 'slat'.")
        if 'slat' in in_json:
            if 'nlat' not in in_json:
                response.add_error_message("'slat' keyword found in JSON, but not 'nlat'")
            elif abs(float(in_json['slat'])) > 90:
                response.add_error_message("'slat' value must fall between 90 and -90")
        if 'wlon' in in_json:
            if 'elon' not in in_json:
                response.add_error_message("'wlat' keyword found in JSON, but not 'elat'")
            elif abs(float(in_json['elon'])) > 180:
                response.add_error_message("'elon' value must fall between 180 and -180")
        if 'elon' in in_json:
            if 'wlon' not in in_json:
                response.add_error_message("'elat' keyword found in JSON, but not 'wlat'")
            elif abs(float(in_json['wlon'])) > 180:
                response.add_error_message("'wlon' value must fall between 180 and -180")
    except ValueError:
        response.add_error_message('Spatial parameters malformed')
    #if 'wlon' in in_json and 'elon' in in_json:
    #    if in_json['wlon'] > in_json['elon']:
    #        response.add_error_message("'wlon' must be less than 'elon'")


    if 'griddef' in in_json and 'gridproj' not in in_json:
        response.add_error_message('Found \'griddef\' keyword without \'gridproj\' keyword')
    elif 'gridproj' in in_json and 'griddef' not in in_json:
        response.add_error_message('Found \'gridproj\' keyword without \'griddef\' keyword')
    
    # Special dataset checks
    if 'dataset' in in_json and in_json['dataset'] == 'ds633.0':
        if 'groupindex' not in in_json:
            response.add_error_message("This dataset requires that you specify a 'groupindex' key in your controlfile")
            response.add_error_message(f"groupindexes can be found at rda.ucar.edu/api/summary/{in_json['dataset']}")

    return response

def parse_subset_levels(level_str):
    """Parses a level string into a dict,
    where the key is the level and the value is
    a list of levels.
    Example:
    'ISBL:400/200;HGT:100' will become
    {'ISBL':[400,200], 'HGT':[100]}

    Returns dict.
    """
    levels = level_str.split(';')
    lev_dict = {}
    for lev in levels:
        level_name,level_values = lev.split(':')
        lev_dict[level_name] = level_values.split('/')
    return lev_dict


def parse_subset_json(in_json, response):
    """Parses JSON values.
    Records errors if values are improperly formatted.
    An example is converting 'param' values to an array
    """
    # Lat/Lon bounds
    if 'elon' not in in_json: # wlon will also not exist
        in_json['elon'] = 180
        in_json['wlon'] = -180
    if 'nlat' not in in_json: # slat will also not exist
        in_json['nlat'] = 90
        in_json['slat'] = -90
    in_json['elon'] = float(in_json['elon'])
    in_json['wlon'] = float(in_json['wlon'])
    in_json['nlat'] = float(in_json['nlat'])
    in_json['slat'] = float(in_json['slat'])

    in_json['start_date'] = in_json['date'].split('/')[0]
    in_json['end_date'] = in_json['date'].split('/')[-1]
    if in_json['start_date'] > in_json['end_date']:
        response.add_error_message('Start date must be earlier or equal to enddate')
    start_date_chars = len(in_json['start_date'])
    end_date_chars = len(in_json['end_date'])
    if start_date_chars != 12:
        response.add_error_message(f'Start date malformed. Need YYYYMMDDHHMMSS, given {start_date_chars} integers')
    if end_date_chars != 12:
        response.add_error_message(f'Start date malformed. Need YYYYMMDDHHMMSS, given {end_date_chars} integers')

    # Product
    if 'product' in in_json:
        in_json['product'] = in_json['product'].split('/')

    # Levels
    try:
        if 'level' in in_json:
            in_json['levels'] = parse_subset_levels(in_json['level'])
        else:
            in_json['levels'] = []
    except ValueError:
        response.add_error_message('Malformed "level" string')
        in_json['levels'] = []

    # Parameters
    in_json['parameters'] = in_json['param'].split('/')

    return (in_json, response)

def get_request_date(date):
    """Returns a date that is formatted as required by subsetting tools."""
    year = date[0:4]
    month = date[4:6]
    day = date[6:8]
    hour = date[8:10]
    minute = date[10:12]
    return year + '-' + month + '-' + day + ' ' + hour + ':' + minute

def get_request_str(in_json, metadata, response):
    """Returns the request string used in making a new request.
    """
    # Used for the request string
    param_list = []
    param_info_list = []
    level_list = []

    # Used for the info string
    level_info_list = {}
    product_list = []
    product_info_list = []
    for param in in_json['parameters']:
        # First filter the metadata by the current select parameter.
        filtered = filter(lambda x: param == x['param'], metadata)
        # Next, filter by the product
        if 'product' in in_json:
            filtered = filter(lambda x: x['product'] in in_json['product'], filtered)

        # Now we can loop through only the variables that match the correct params and products
        for var in filtered:
            if var['parameter_code'] not in param_list:
                param_list.append(var['parameter_code'])
                if var['param_description'] not in param_info_list:
                    param_info_list.append(var['param_description'])
            if str(var['product_code']) not in product_list:
                product_list.append(str(var['product_code']))
                if str(var['product']) not in product_info_list:
                    product_info_list.append(str(var['product']))

            # Loop through products vertical levels. If found add to request strings
            for i,level in enumerate(var['levels']):
                if level['level'] in in_json['levels'] and \
                        var['level_codes'][i] not in level_list and \
                        level['level_value'] in in_json['levels'][level['level']]:
                    level_list.append(var['level_codes'][i])
                    level_description = level['level_description']
                    if level_description in level_info_list:
                        level_info_list[level_description].append(level['level_value']);
                    else:
                        level_info_list[level_description] = [level['level_value']]



    # Get complete param e.g. '7-0.2-1:0.0.21' becomes '3!7-0.2-1:0.0.21'
    # This is done so the string will match the IGrML inventory table.
    for i,param in enumerate(param_list):
        param_list[i] = common.get_param_inventory(in_json['dataset'], param)

    dsid = common.format_dataset_id(in_json['dataset'], remove_ds=True)
    if ( dsid == '084.1' or dsid == '083.2') and len(param_list) == 0:
        response.add_error_message('Could not find parameters in dataset')

    # Make our lists into strings
    param_str = ','.join(param_list)
    product_str = ','.join(product_list)
    level_str = ','.join(level_list)

    # These keys should all be available
    req_str = 'dsnum='+common.format_dataset_id(in_json['dataset'], remove_ds=True) + ';' \
            + 'startdate=' + get_request_date(in_json['start_date']) + ';' \
            + 'enddate=' + get_request_date(in_json['end_date']) + ';' \
            + 'parameters=' +param_str + ';' \
            + 'product=' + product_str + ';' \
            + 'level=' + level_str

    #if (common.format_dataset_id(in_json['dataset'], remove_ds=True) == '093.0' 
    # or common.format_dataset_id(in_json['dataset'], remove_ds=True) == '094.0') 
    # and in_json['elon'] == 180 and in_json['wlon'] == -180 
    # and in_json['nlat'] == 90 and in_json['slat'] == -90:
    if in_json['elon'] == 180 and in_json['wlon'] == -180 and in_json['nlat'] == 90 and in_json['slat'] == -90:
            pass
    else:
        req_str += ';nlat=' + str(in_json['nlat']) + ';' \
            + 'slat=' + str(in_json['slat']) + ';' \
            + 'wlon=' + str(in_json['wlon']) + ';' \
            + 'elon=' + str(in_json['elon'])

    if 'groupindex' in in_json:
        req_str += ';tindex='+str(in_json['groupindex'])

    if 'griddef' in in_json:
        try:
            code = common.get_code_from_grid_definition(in_json['griddef'])
            req_str += ';grid_definition=' + str(code)
        except Exception as e:
            response.add_error_message('Could not find grid definition '+ in_json['griddef'])

    if in_json['request_type'] == 'T':
        req_str += ";ofmt="+in_json['oformat']

    datetype = None
    if 'datetype' in in_json:
        datetype = in_json['datetype'].lower()
        req_str += ";dates="+datetype

    if 'ststep' in in_json and in_json['ststep'] == 'yes':
        req_str += ";ststep=yes"


    req_info_str = get_request_info_str(output_format=in_json['oformat'],\
            levels=level_info_list,\
            products=product_info_list,\
            params=param_info_list,\
            start_date=get_request_date(in_json['start_date']),\
            end_date=get_request_date(in_json['end_date']),
            datetype=datetype
            )


    return (req_str, req_info_str)

def get_request_info_str(output_format=None, levels=None, \
            products=None, params=None, start_date=None, end_date=None , datetype=None):
    """Assembles a request info string.
    """
    req_info_str = "\n"
    if output_format is not None:
        req_info_str += "- Output format: "+output_format+"\n"
    if start_date is not None:
        req_info_str += "- Start date:  " + start_date +"\n"
    if end_date is not None:
        req_info_str += "- End date:    " + end_date +"\n"
    if datetype is not None and datetype == 'init':
        req_info_str += "- Initialization (reference) dates\n"
    if params is not None:
        req_info_str += "- Parameter(s):\n"
        for param in params:
            req_info_str += "   "+param+"\n"
    if levels is not None:
        req_info_str += "- Level(s):\n"
        for level_desc,values in levels.items():
            req_info_str += "   "+level_desc+":\n"
            for value in values:
                req_info_str += "     " + value +"\n"
    if products is not None:
        req_info_str += "- Product(s):\n"
        for product in products:
            req_info_str += "   "+product+"\n"



    return req_info_str


def submit_subset_request(in_json, user_email=None):
    """Submit subset request using JSON, `in_json`.
    in_json can be a file or string.
    """
    response = RDA_Response()
    if type(in_json) == str and os.path.isfile(in_json):
        with open(in_json) as fn:
            in_json = json.load(fn)
    elif type(in_json) == str:
        try:
            in_json = json.loads(in_json)
        except ValueError:
            response.add_error_message(463)
            return response
 
    if user_email is None:
        try:
            user_email = in_json['email']
            if user_email is None:
                user_email = common.get_local_emailname()
        except:
            user_email = common.get_local_emailname()
    # Check if User has too many requests
    request_limit = 10
    special_limits = {'drews@ucar.edu':100}
    if user_email in special_limits:
        request_limit = special_limits[user_email]
    num_requests = len(common.get_rqst_indexes(user_email))
    if num_requests > request_limit:
        response.add_error_message('User has more than '+str(request_limit)+' open requests. Purge requests before trying again.')
        return response


    # Check if anything from json is missing or invalid
    response = subset_json_checks(in_json, response)
    if response.code != 200:
        return response

    # Check Roles
    ds_role = common.get_access_type(in_json['dataset'])
    if ds_role is not None or ds_role == 'g':
        if ds_role not in in_json['role'].split(':'):
            response.add_error_message("You don't have permission to access this dataset.")
            return response

    # Parse JSON in more workable structures
    in_json, response = parse_subset_json(in_json, response)
    if response.code != 200:
        return response

    # Change request_type
    if 'oformat' in in_json and (in_json['oformat'].lower() == 'netcdf' or in_json['oformat'].lower() == 'csv'):
        in_json['request_type'] = 'T'
        if in_json['oformat'].lower() == 'netcdf':
            in_json['oformat'] = 'netCDF'
    else:
        in_json['request_type'] = 'S'
        in_json['oformat'] = None

    if not common.can_subset(in_json['dataset']):
        response.add_error_message('dataset '+ in_json['dataset']+ ' cannot be subset')
        return response
    metadata_response = get_actions.get_metadata(in_json['dataset'],
            param_summary=False,
            show_internal_values=True)
    # Metadata contains information about all variables.
    metadata = metadata_response.get_data()['data']

    request_str, request_info_str = get_request_str(in_json, metadata, response)
    if response.code != 200:
        return response

    try:
        request_id = rdams_submit(in_json['dataset'], request_str, in_json['request_type'], request_info_str, '128.117.10.120', user_email)
        response.add_data( {'request_id':request_id} )
    except Exception as e:
        response.add_error_message("There was a problem submitting the request. Please try again or contact rdahelp@ucar.edu")
        print("Error with dsrqst submission:" + str(e))
        print(str(user_email) + request_info_str)

    return response

def rdams_submit(dsid, rinfo, rtype, rnote, ip, email):
    """
    Submits a subset request.

    Args:
        dsid (str): 6 digit dataset id. e.g. 'd084001'
        rinfo (str): RDA request information string that gives subset options.
        rtype (str): Request type. (T, S, etc.)
        rnote (str): Human readable version of request info.
        ip (str): IP of requester. Generally not used.
        email (str): Email of requester. 

    Returns: 
        (str) 6 digit request index.
    """
    from rda_python_common import PgOPT
    from rda_python_dsrqst import PgRDARqst
    
    rqst = {}
    rqst['dsid'] = dsid
    rqst['rinfo'] = rinfo
    rqst['rtype'] = rtype
    rqst['rnote'] = rnote
    rqst['ip'] = ip
    rqst['email'] = email
    rqst['rnote'] = rnote
    rqst['location'] = "web"
    rqst['fromflag'] = "A"
    
    msg = PgRDARqst.rda_request(rqst);
    m = re.search(r'.*(\d\d\d\d\d\d).*', msg)
    return m.group(1)
