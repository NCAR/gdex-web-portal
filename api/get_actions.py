#!/usr/bin/env python
import sys
import os
import pdb
import json
from .RDA_Response import RDA_Response
from . import common


def handle_connection_error(response, err):
    """Inits connection and handles errors.
    Modifies passed response object and returns it.
    """
    response.add_error_message(513)
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      response.add_message("Something is wrong with user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
      response.add_message("Database doesn't exist")
    else:
      response.add_message(str(err.msg))
    return response

def initial_checks(response, dsid=None):
    """Perform initial checks to see if connection to database
    is ok, and dsid is valid and exists.

    Returns response
    """
    try:
        common.init_connection()
    except Exception as err:
        response.add_error_message(512)
        response.add_message(str(err))
        return response
    if dsid is not None and common.check_ds(dsid) == False:
        response.add_error_message(460)
        response.add_message("dsid provided is: '"+dsid+"'")
        return response
    return response

def get_summary(dsid):
    """Returns a response that includes groups of given dsid that can
    be subset.
    """
    response = RDA_Response()
    response = initial_checks(response, dsid)
    if response.code != 200:
        return response

    dsid = common.format_dataset_id(dsid) # adds 'ds' to dsid if not there
    result = {}
    can_subset = common.can_subset(dsid)
    response.add_data({'subsetting_available':can_subset})
    if not can_subset:
        return response
    groups = common.get_request_type(dsid)
    for i,group in enumerate(groups):
        title = common.get_group_title(dsid, group['group_index'])
        if len(title) > 0:
            group['title'] = title[0]['title']
        else:
            pass

    result['data'] = groups

    response.add_data(result)

    return response

def get_param_summary(dsid):
    """Returns just the parameter info for a dataset"""
    return get_metadata(dsid, param_summary=True)

def get_variable_hash(var):
    """Returns a hash that represents a variable.
    """
    hash_str = str(var['format_code']) +\
            str(var['start_date']) +\
            str(var['end_date']) +\
            str(var['grid_definition_code']) +\
            str(var['parameter'])
    return hash_str

def get_metadata(dsid, param_summary=False, show_internal_values=False):
    """Gets metadata for dsid.
    `param_summary` of True only returns parameter information
    `show_internal_values` of True will return extra internal values
    such as level_code and parameter_code
    """
    response = RDA_Response()
    response = initial_checks(response, dsid)
    if response.code != 200:
        return response
    can_subset = common.can_subset(dsid)
    response.add_data({'subsetting_available': can_subset})
    if not can_subset:
        return response
    dsid = common.format_dataset_id(dsid, remove_ds=True)
    # All variables are returned here.
    variable_info = common.get_variable_info(dsid)

    variables = []
    # Changes default keys into something more descriptive.
    param_key_change = {
            'description' : 'param_description',
            'format' : 'native_format',
            'CF' : 'standard_name',
            'ISO' : 'ISO_TopicCategoryCode',
            'GCMD' : 'GCMD_uuid',
            'shortName' : 'param'
            }
    level_key_change = {
            'description' : 'level_description',
            'value' : 'level_value',
            'shortName' : 'level'
            }
    for variable in variable_info:


        # First get variable info
        try:
            param_info = common.get_param_info(variable['parameter'], param_key_change)
        except:
            param_info = {'variable':variable['parameter']}
        if param_summary:
            variables.append(param_info)
            continue
        else:
            cur_var = get_metadata_object_template() # Init dict
            cur_var.update(param_info)


        # First, fill cur_var with common parameters
        cur_var['start_date'] = variable['start_date']
        cur_var['end_date'] = variable['end_date']

        cur_var['product'] = variable['time_range']

        grid_def_code = variable['grid_definition_code']
        grid_def = common.get_grid_definition(grid_def_code)
        cur_var['griddef'] = grid_def['def_params']
        cur_var['gridproj'] = grid_def['definition']


        full_level_code = variable['level_type_codes']
        level_codes = common.parse_levelType_code(full_level_code)
        if show_internal_values:
            cur_var['level_codes'] = level_codes
            cur_var['parameter_code'] = variable['parameter']
            cur_var['product_code'] = variable['time_range_code']

        # Put level codes as a unique variable
        #for level_code in level_codes:
        #    level_def = common.get_level_definition(level_code, cur_var['native_format'],level_key_change)
        #    new_var = cur_var.copy()
        #    new_var.update(level_def)
        #    variables.append(new_var)
        #
        # Or
        #
        # Put level codes as an array
        cur_var['levels'] = []
        for level_code in level_codes:
            level_def = common.get_level_definition(level_code, cur_var['native_format'],level_key_change)
            cur_var['levels'].append(level_def)
        variables.append(cur_var)


#    print(json.dumps(variables, indent=4))
    result = {}
    result['dsid'] = dsid
    result['data'] = variables
    response.add_data(result)
    return response

def get_metadata_condensed(dsid, param_summary=False, show_internal_values=False):
    """Gets metadata for dsid.
    `param_summary` of True only returns parameter information
    `show_internal_values` of True will return extra internal values
    such as level_code and parameter_code
    """
    response = RDA_Response()
    response = initial_checks(response, dsid)
    if response.code != 200:
        return response
    can_subset = common.can_subset(dsid)
    response.add_data({'subsetting_available': can_subset})
    if not can_subset:
        return response
    dsid = common.format_dataset_id(dsid, remove_ds=True)
    # All variables are returned here.
    variable_info = common.get_variable_info(dsid)

    variables = []
    variables_dict = {}
    # Changes default keys into something more descriptive.
    param_key_change = {
            'description' : 'param_description',
            'format' : 'native_format',
            'CF' : 'standard_name',
            'ISO' : 'ISO_TopicCategoryCode',
            'GCMD' : 'GCMD_uuid',
            'shortName' : 'param'
            }
    level_key_change = {
            'description' : 'level_description',
            'value' : 'level_value',
            'shortName' : 'level'
            }
    for variable in variable_info:

        hsh = get_variable_hash(variable)
        if hsh in variables_dict:
            cur_var = variables_dict[hsh]
            cur_var['product'].append(variable['time_range'])
            continue

        # First get variable info
        try:
            param_info = common.get_param_info(variable['parameter'], param_key_change)
        except:
            param_info = {}
        if param_summary:
            variables.append(param_info)
            continue
        else:
            cur_var = get_metadata_object_template() # Init dict
            cur_var.update(param_info)


        # First, fill cur_var with common parameters
        cur_var['start_date'] = variable['start_date']
        cur_var['end_date'] = variable['end_date']

        grid_def_code = variable['grid_definition_code']
        grid_def = common.get_grid_definition(grid_def_code)
        cur_var['griddef'] = grid_def['def_params']
        cur_var['gridproj'] = grid_def['definition']

        cur_var['product'] = [variable['time_range']]


        full_level_code = variable['level_type_codes']
        level_codes = common.parse_levelType_code(full_level_code)
        if show_internal_values:
            cur_var['level_codes'] = level_codes
            cur_var['parameter_code'] = variable['parameter']
            cur_var['product_code'] = variable['time_range_code']

        # Put level codes as a unique variable
        #for level_code in level_codes:
        #    level_def = common.get_level_definition(level_code, cur_var['native_format'],level_key_change)
        #    new_var = cur_var.copy()
        #    new_var.update(level_def)
        #    variables.append(new_var)
        #
        # Or
        #
        # Put level codes as an array
        cur_var['levels'] = []
        for level_code in level_codes:
            level_def = common.get_level_definition(level_code, cur_var['native_format'],level_key_change)
            cur_var['levels'].append(level_def)
        variables_dict[hsh] = cur_var

    variables = variables_dict.values()
#    print(json.dumps(variables, indent=4))
    result = {}
    result['dsid'] = dsid
    result['data'] = variables
    response.add_data(result)
    return response

def get_type():
    pass

def get_metadata_object_template():
    """Returns a template of a metadata object.
    """
    meta_dict = {}
    meta_keys = [
            #'dataset',
            'param',
            'param_description',
            'start_date',
            'end_date',
            'native_format',
    #        'product',
            'gridproj',
            'griddef',
            'level']
            #'level_description']
            #'levelvalue']
    for key in meta_keys:
        meta_dict[key] = None
    return meta_dict

def globus_download(request_index=None, email=None):
    """Start a globus download.
    """
    response = RDA_Response()
    response = initial_checks(response)
    if response.code != 200:
        return response
    return response

def get_status(request_index=None,email=None):
    """Get request status"""
    response = RDA_Response()
    response = initial_checks(response)
    if response.code != 200:
        return response

    if email is None:
        email = common.get_local_emailname()
    if request_index is None or request_index == "None" or request_index == "ALL":
        return get_all_statuses(email)

    # Confirm email and request index match up
    rqst_idxs = common.get_rqst_indexes(email)
    #print(email)
    #print(rqst_idxs)
    if int(request_index) not in rqst_idxs:
        response.add_error_message(421)
        response.add_message('email: '+str(email)+', request index: '+str(request_index))
        return response

    rqst_info = common.get_request_info(request_index)
    response.add_data(rqst_info)

    return response

def get_all_statuses(email=None):
    """Get all statuses.
    If email is None, try to determine from email from ID.
    """
    if email is None:
        email = common.get_local_emailname()
    rqst_indexes = common.get_rqst_indexes(email)
    if len(rqst_indexes) == 0:
        response = RDA_Response()
        response.add_error_message(432)
        return response

    aggregated_response = RDA_Response()
    all_data = []
    for rindex in rqst_indexes:
        response = get_status(rindex, email)
        # Maybe should add som logic to handle if a response is bad,
        # however this is unlikely to happen.
        #if response.error_code != 200:
        #    aggregated_response.error_code
        data = response.data
        #print(data)
        all_data.append(data)
    aggregated_response.data = all_data
    return aggregated_response

def get_request_files_old(request_index, email=None):
    """Get files in a request. Returns json the old way"""
    if email is None:
        email = common.get_local_emailname()

    # Confirm email and request index match up
    rqst_idxs = common.get_rqst_indexes(email)
    if int(request_index) not in rqst_idxs:
        print("Request index does not exist or does not match email, "+email+".")
        exit(1)

    request_info = common.get_request_info(request_index)
    if request_info['status'] != 'Completed':
        print("Request is not completed.\nCurrent Status : "+request_info['status'])
        exit(1)

    download_url = 'https://request.rda.ucar.edu/dsrqst/' + request_info['request_id']

    web_files = common.get_web_files(request_index)
    # Get unique tindexes from web_files
    tindexes = set(map(lambda x: x['tindex'],web_files))

    if 0 not in tindexes: # If request is tarred
        out_dict = {}
        for _file in tindexes:
            file_info = common.get_tar_file(tindexes)
            tar_file = download_url + '/TarFiles/' + file_info['wfile']
            size = file_info['size']
            out_dict[tar_file] = size
        print(out_dict)
        exit(0)

    out_dict = {}
    for web_file in web_files:
        size = web_file['size']
        web_file = download_url+'/'+web_file['wfile']
        out_dict[web_file] = size
    print(out_dict)
    exit(0)


def get_request_files(request_index, email=None):
    """Get files in a request"""
    response = RDA_Response()
    response = initial_checks(response)
    if response.code != 200:
        return response

    if email is None:
        email = common.get_local_emailname()

    # Confirm email and request index match up
    rqst_idxs = common.get_rqst_indexes(email)
    if int(request_index) not in rqst_idxs:
        response.add_error_message(421)
        response.add_message('email: '+str(email)+', request index: '+str(request_index))
        return response

    request_info = common.get_request_info(request_index)
    download_url = 'https://request.rda.ucar.edu/dsrqst/' + request_info['request_id']

    web_files = common.get_web_files(request_index)

    total_size = 0
    tar_dict = {}
    for web_file in web_files:
        total_size += web_file['size']
        tindex = web_file.pop('tindex')
        if tindex == 0:
            web_file['web_path'] = download_url+'/'+web_file['wfile']
        else:
            if tindex in tar_dict:
                tar_info = tar_dict[tindex]
            else:
                tar_info = common.get_tar_file(tindex)[0]
                tar_dict[tindex] = tar_info
            web_file['web_path'] = download_url+'/TarFiles/'+tar_info['wfile']

    result = {
            'web_files' : web_files,
            'total_size' : total_size
            }
    response.add_data(result)

    return response


def get_control_file_template_old(dsid=None, json=False):
    """Prints a control file for a given dsid.

    This function simply prints the control file, while the none '_old'
    function will return a RDA_response json.
    """
    template_dir = "/glade/u/home/rdadata/share/rdams_control_files/"
    if dsid is not None:
        dsid = common.format_dataset_id(dsid)
        template_file = template_dir+str(dsid) + "_control_file"
        if not os.path.exists(template_file):
            template_file = template_dir + "dsnnn.n_control_file"
    else:
        template_file = template_dir + "dsnnn.n_control_file"
    with open(template_file, 'r') as fh:
        contents = fh.read()
        print(contents)
    return ""

def get_control_file_template(dsid=None, json=False):
    """Get's a control file for a given dsid"""
    response = RDA_Response()
    template_dir = "/glade/u/home/rdadata/share/rdams_control_files/"
    if dsid is not None:
        dsid = common.format_dataset_id(dsid)
        template_file = template_dir+str(dsid) + "_control_file"
        if not os.path.exists(template_file):
            template_file = template_dir + "dsnnn.n_control_file"
    else:
        template_file = template_dir + "dsnnn.n_control_file"
    with open(template_file, 'r') as fh:
        contents = fh.read()
        response.add_data({'template':contents})
    return response










