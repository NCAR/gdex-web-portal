#!/usr/bin/env python

import sys
import os
from . import get_actions
from . import post_actions
from .RDA_Response import RDA_Response
import pdb
print_json = True

def usage(code=111):
    """Create repsonse object with usage message."""
    response = RDA_Response(code)
    return response

def print_response(response):
    """Prints response object."""
    if print_json:
        print(response)

def do_nothing():
    pass

def get_options_dict():
    """Returns a dict containing rdams options and associated functions."""
    options_dict = {
        "-get_summary" : {
                "function" : get_actions.get_summary,
                 "min_args" : 1
                },
        "-get_metadata" : {
                "function" : get_actions.get_metadata,
                "min_args" : 1
                },
        "-get_metadata_live" : {
                "function" : do_nothing,
                "min_args" : 1
                },
        "-get_param_summary" : {
                "function" : get_actions.get_param_summary,
                "min_args" : 1
                },
        "-get_param_summary_live" : {
                "function" : do_nothing,
                "min_args" : 1
                },
        "-submit" : {
                "function" : post_actions.submit_subset_request,
                "min_args" : 1
                },
        "-submit_json" : {
                "function" : post_actions.submit_subset_request,
                "min_args" : 1
                },
        "-print_help" : {
                "function" : print_help,
                "min_args" : 0
                },
        "-help" : {
                "function" : rdams_help,
                "min_args" : 0
                },
        "-get_control_file_template" : {
                "function" : get_actions.get_control_file_template,
                "min_args" : 1
                },
        "-get_control_file_template_old" : {
                "function" : get_actions.get_control_file_template_old,
                "min_args" : 1
                },
        "-get_remote_control_file_template" : {
                "function" : get_actions.get_control_file_template,
                "min_args" : 0
                },
        "-get_status" : {
                "function" : get_actions.get_status,
                "min_args" : 0
                },
        "-get_req_files" : {
                "function" : get_actions.get_request_files,
                "min_args" : 1
                },
        "-get_req_files_old" : {
                "function" : get_actions.get_request_files_old,
                "min_args" : 1
                },
        "-globus_download" : {
                "function" : get_actions.globus_download,
                "min_args" : 2
                },
        "-purge" : {
                "function" : post_actions.purge,
                "min_args" : 1
                },
        }
    return options_dict

def main(*args):
    args = list(args)

    if len(args) == 0:
        response = usage()
        print_response(response)
        return response.get_json()
    options = get_options_dict() # Defines which functions perform which actions
    option = args.pop(0)
    if option not in options:
        response = usage(112)
        response.add_message("option, '"+option+"' not one of "+str(options.keys()))
        print_response(response)
        return response.get_json()

    func = options[option]['function']
    min_args = options[option]['min_args']
    if len(args) < min_args:
        response = usage(113)
        print_response(response)
        return response.get_json()

    response = func(*args)

    #print_response(response)
    return response.get_json()

def rdams_help():
    response = RDA_Response()
    response.add_message(get_rdams_usage_string)
    return response

def print_help():
    print(get_rdams_usage_string())
    exit(0)

def get_rdams_usage_string():
    return "Usage:"

if __name__ == "__main__":
    sys.argv.pop(0)
    main(*sys.argv)


__version__ = "0.1.0"






