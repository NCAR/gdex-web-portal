import json
import os
import requests
import hmac
import hashlib
from django.shortcuts import render
from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from . import rdams
from . import common
from . import RDA_Response as rda_r

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.decorators import api_view, renderer_classes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

import logging
logger = logging.getLogger(__name__)

def verify_login(request):
    cookies = request.COOKIES
    return None

def param_summary(request, dsid):
    json = rdams.main("-get_param_summary",dsid)
    return JsonResponse(json)

def get_metadata(request, dsid):
    json = rdams.main("-get_metadata",dsid)
    return JsonResponse(json)

def get_staff(request):
    json = common.get_staff()
    response = rda_r.RDA_Response()
    response.add_data(json)
    return JsonResponse(response.get_json())

def get_staff_dsid(request, dsid):
    dsid = common.format_dataset_id(dsid)
    json = common.get_staff_dsid(dsid)
    response = rda_r.RDA_Response()
    response.add_data(json)
    return JsonResponse(response.get_json())

def _trigger_github(github_repo:str, github_token:str, payload=None):
    """
    Triggers the Github Actions workflow via github repository_dispatch

    ticket_id: is optional, but if provided will be included in the client_payload 
        sent to github and can be used to conditionally run steps in the workflow 
        or for debugging/logging purposes.
    Returns the status code and text response from the github API call
    """
    if not github_token:
        raise ValueError("PERSONAL_GITHUB_TOKEN did not load properly")
    print("Github token loaded successfully")
        
    headers = {
    "Authorization": f"token {github_token}",
    "Accept": "application/vnd.github.v3+json",
    }

    data = {
        "event_type": "jira-event",
        "client_payload": payload
        }

    try:
        response = requests.post(github_repo, json=data, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.status_code, response.text
    except requests.excepions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return None, str(http_err)
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occured: {conn_err}")
        return None, str(conn_err)
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
        return None, str(timeout_err)
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred: {req_err}")
        return None, str(req_err)

@method_decorator(csrf_exempt, name='dispatch')
class JiraEventReceiver(APIView):
    renderer_classes = [JSONRenderer] # disable UI rendering, return JSON only
    http_method_names = ['post'] # allow POST only

    def post(self,request, ticket_id=None):
        payload = request.body
        payload_ticket_id = ticket_id if ticket_id else None
            
        received_signature = request.headers.get("X-Hub-Signature")
        shared_secret = os.getenv("JIRA_WEBHOOK_SECRET")
        if not shared_secret:
            raise ValueError("Warning: JIRA_WEBHOOK_SECRET not set. Webhook signature will not be verified.")
        
        #Verify signature
        if not self._verify_signature(payload, received_signature, shared_secret):
            return Response({"status": "error", "message": "Invalid signature"}, status=403)
        print("Received Jira Webhook")

        github_repo=os.getenv("GITHUB_REPO")
        if not github_repo:
            raise ValueError("GITHUB_REPO did not load properly")
        
        github_token=os.getenv("PERSONAL_GITHUB_TOKEN")
        if not github_token:
            raise ValueError("PERSONAL_GITHUB_TOKEN did not load properly")
        
        status_code, text = _trigger_github(github_repo, github_token, payload = {"ticket_id": payload_ticket_id})

        return Response({
            "status": f"Worflow triggered due to incoming ticket: {payload_ticket_id}",
            "github_response_code": status_code,
            "github_response_text": text
        })   
    
    def _verify_signature(self, payload: bytes, received_signature: str, secret: str) -> bool:
        if not secret:
            raise ValueError("No shared secret found for webhook signature verification.")
        if not received_signature:
            raise ValueError("No signature found in headers. Webhook signature will not be verified.")   
        if received_signature.startswith("sha256="):
            received_signature = received_signature.split("=", 1)[1]
        # Jira uses HMAC SHA256
        computed_hmac = hmac.new(
            key=secret.encode("utf-8"),
            msg=payload,
            digestmod=hashlib.sha256
        ).hexdigest()
        is_match = hmac.compare_digest(computed_hmac, received_signature)
        return is_match


def _handle_dataset_response(dsid, data, error_message_template, wrap_key=None):
    """Helper function to handle common dataset response pattern
    Args:
        dsid: Dataset ID
        data: The data returned from common function
        error_message_template: Template for error message with {dsid} placeholder
        wrap_key: Optional key to wrap data in (e.g., 'temporal', 'data_types')
    """
    response = rda_r.RDA_Response()

    if data is None or not data:
        response.add_error_message(error_message_template.format(dsid=dsid))
        response.add_data('')
        return JsonResponse(response.get_json(), status=400)
    else:
        # wrap data in a key if specified, otherwise use data directly
        json_data = {wrap_key: data} if wrap_key else data
        response.add_data(json_data)
        return JsonResponse(response.get_json())

def get_root_groups(request, dsid):
    dsid = common.format_dataset_id(dsid)
    json = common.get_root_groups(dsid)
    response = rda_r.RDA_Response()
    response.add_data(json)
    return JsonResponse(response.get_json())

#@cache_page(4 * 24 * 60 * 60) # cache for 4 days
def get_assembled_groups(request, dsid, gindex=None):
    """ Creates table like representation of webfile data """
    dsid = common.format_dataset_id(dsid)
    response = rda_r.RDA_Response()

    page = request.GET.get('page')
    filter_wfile = request.GET.get('filter_wfile', '')
    fl_source = request.GET.get('fl', 'web')
    try:
        page = int(page)
        page = str(page)
    except:
        page = 0
    if not page:
        page = 0
    logger.debug("dsid: {}, page: {}, fl_source: {}, filter_wfile: {}".format(dsid, page, fl_source, filter_wfile))
    if gindex is None:
        json = common.assemble_root_group_filelist(dsid, page, fl_source)
    else:
        json = common.assemble_filelist(dsid, gindex, page, fl_source, filter_wfile)
    response.add_data(json)
    return JsonResponse(response.get_json())

def get_child_groups(request, dsid, gindex):
    dsid = common.format_dataset_id(dsid)
    json = common.get_child_groups(dsid, gindex)
    response = rda_r.RDA_Response()
    response.add_data(json)
    return JsonResponse(response.get_json())

def get_web_files(request,dsid, gindex, filter_wfile=None):
    dsid = common.format_dataset_id(dsid)
    json = common.get_web_files_from_gindex(dsid, gindex, filter_wfile=filter_wfile)
    response = rda_r.RDA_Response()
    response.add_data(json)
    response_json = response.get_json()
    #print(response_json)
    return JsonResponse(response_json)

#@cache_page(4 * 24 * 60 * 60) # cache for 4 days
def assemble_filelist(request, dsid):
    root_groups = common.get_root_groups()


def get_dataset_documentation(request, dsid):
    dsid = common.format_dataset_id(dsid)
    json = common.get_dataset_documentation(dsid)
    response = rda_r.RDA_Response()
    response.add_data(json)
    return JsonResponse(response.get_json())

def get_dataset_software(request, dsid):
    dsid = common.format_dataset_id(dsid)
    json = common.get_dataset_software(dsid)
    response = rda_r.RDA_Response()
    response.add_data(json)
    response_json = response.get_json()
    return JsonResponse(response_json)


@csrf_exempt
def generate_notebook(request):
    from . import NBBuilder as nbb

    if 'filelist' in request.POST:
        return HttpResponseBadRequest("use 'filelist[]' in request")
    if 'filelist[]' not in request.POST:
        return HttpResponseBadRequest("no 'filelist' in request")
    #if 'wpath' not in request.POST:
    #    return HttpResponseBadRequest("no 'wpath' in request")

    filelist = request.POST.getlist('filelist[]')
    #wpath = request.POST['wpath'][0]

    b = nbb.get_builder()


    b.add_markdown_block(" # Notebook for Downloading GDEX Data.")
    b.add_code_block(
        "import os",
        "import requests")

    # Add quotes to element so each file will have it's own line
    filelist = [ '"' + f.strip() + '",\n' for f in filelist]
    filelist.insert(0,"filelist = [")
    filelist.append("]")
    b.add_code_block(' '.join(filelist))

    b.add_markdown_block("Change the value of `save_dir` if you prefer your files saved somewhere other than the current directory.")
    b.add_code_block("save_dir = ''")
    b.add_markdown_block(" ## Now to download the files")

    b.add_code_block("for file in filelist:",
                     "    filename = (os.path.join(save_dir, os.path.basename(file))).strip()",
                     "    print('Downloading', file)",
                     "    req = requests.get(file, allow_redirects=True)",
                     "    open(filename, 'wb').write(req.content)")

    b.add_markdown_block("### Once you have downloaded the data, the next part can help you plot it.")
    b.add_markdown_block("In order to plot this data, you may need to install some libraries. The easiest way to do this is to use conda or pip, however any method of getting the following libraries will work.")
    b.add_code_block(
                     "import xarray # used for reading the data.",
                     "import matplotlib.pyplot as plt # used to plot the data.",
                     "import ipywidgets as widgets # For ease in selecting variables.",
                     "import cartopy.crs as ccrs # Used to georeference data.")


    b.add_code_block("filelist_arr = [save_dir + os.path.basename(file) for file in filelist]",
                     "selected_file = widgets.Dropdown(options=filelist_arr, description='data file')",
                     "display(selected_file)")

    b.add_code_block("# Now to load in the data to xarray",
                     "ds = xarray.open_dataset(selected_file.value)")

    b.add_code_block("# Helper methods"
                     "# Define function to get standard dimensions",
                     "def get_primary(dataset):",
                     "    primary_variables = {}",
                     "    coords = dataset.coords.keys()",
                     "    highest_dims = 0",
                     "    for cur_key,cur_var in dataset.variables.items():",
                     "        if cur_key not in coords:",
                     "            primary_variables[cur_key] = cur_var",
                     "    return primary_variables ")

    b.add_code_block("var = widgets.Dropdown(",
                     "    options=get_primary(ds).keys(),",
                     "    description='Variable')",
                     "display(var)")

    b.add_code_block("proj = ccrs.Mercator()",
                     "plt.gcf().set_size_inches(20,10)",
                     "ax = plt.axes(projection=proj)",
                     "data_slice = ds[var.value].isel(time=0)",
                     "data_slice.plot.contourf(ax=ax, transform=ccrs.PlateCarree())",
                     "ax.set_global()",
                     "ax.coastlines()")
    return HttpResponse(str(b))


def get_datasets(request):
    json = common.get_all_datasets()
    return JsonResponse({'data':json})

def get_summary(request, dsid):
    json = rdams.main("-get_summary",dsid)
    return JsonResponse(json)

@csrf_exempt
def submit(request):
    if request.method != 'POST':
        response = rda_r.RDA_Response()
        response.add_message('This action requires a POST request')
        print('method is '+request.method)
        return JsonResponse(response.get_json())
    request_body = request.body
    request_json = json.loads(request_body)
    email = get_email_from_token(request)
    if email is None:
        response = rda_r.RDA_Response()
        response.add_message('Incorrect Token. Visit "https://gdex.ucar.edu/accounts/profile/" to obtain token.')
        return JsonResponse(response.get_json())
    json_response = rdams.main("-submit", request_json, email)
    return JsonResponse(json_response)

@csrf_exempt
def submit_json(request):
    email = get_email_from_token(request)
    if email is None:
        response = rda_r.RDA_Response()
        response.add_message('Incorrect Token. Visit "https://gdex.ucar.edu/accounts/profile/" to obtain token.')
        return JsonResponse(response.get_json())
    json = rdams.main("-submit")
    return JsonResponse(json)

def print_help(request):
    json = rdams.main("-print_help")
    return JsonResponse(json)

def get_control_file_template(request, dsid):
    json = rdams.main("-get_control_file_template", dsid)
    return JsonResponse(json)

def get_control_file_template_old(request, dsid):
    json = rdams.main("-get_control_file_template_old", dsid)
    return JsonResponse(json)

def get_status(request, rindex=None):
    email = get_email_from_token(request)
    if email is None:
        email = request.COOKIES.get('ruser')
    json = rdams.main("-get_status", rindex, email)
    return JsonResponse(json)

def get_req_files(request, rindex):
    email = get_email_from_token(request)
    json = rdams.main("-get_req_files", rindex, email)
    return JsonResponse(json)

def get_req_files_old(request, rindex):
    json = rdams.main("-get_req_files_old", rindex)
    return JsonResponse(json)

@cache_page(4 * 24 * 60 * 60) # cache for 4 days
def volume_downloaded(request):
    volume = common.get_volume_downloaded_db()
    return JsonResponse({'volume':volume})

@cache_page(4 * 24 * 60 * 60) # cache for 4 days
def unique_users(request):
    ips = common.get_number_of_unique_users_db()
    return JsonResponse({'ips':ips})

def globus_download(request, rindex, endpoint):
    json = rdams.main("-globus_download", rindex, endpoint)
    return JsonResponse(json)

@csrf_exempt
def purge(request, rindex):
    if request.method != 'DELETE':
        response = rda_r.RDA_Response()
        response.add_message('This action requires a DELETE request')
        return JsonResponse(response.get_json())
    email = get_email_from_token(request)
    if email is None:
        response = rda_r.RDA_Response()
        response.add_message('Incorrect Token. Visit "https://gdex.ucar.edu/accounts/profile/" to obtain token.')
        return JsonResponse(response.get_json())
    json = rdams.main("-purge", rindex, email)
    return JsonResponse(json)

def get_email_from_token(request):
    token = request.GET.get('token','')
    email = common.get_email_from_token(token)
    print(email)
    return email

@extend_schema(
    operation_id='get_dataset_abstract',
    summary='Get dataset abstract',
    description='''
    Retrieves the abstract text for a specific dataset along with additional parsed notes.

    This endpoint performs comprehensive text processing including:
    - Unicode escape sequence decoding
    - URL extraction from the abstract text
    - Note/warning text identification and separation
    - HTML tag removal and text cleaning
    ''',
    parameters=[
        OpenApiParameter(
            name='dsid',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description='Dataset identifier in 6-digit format (e.g., d123456)',
            required=True,
            pattern=r'd\d{6}'
        )
    ],
    responses={
        200: {
            'type': 'object',
            'description': 'Successfully retrieved abstract with parsed metadata',
            'properties': {
                'status': {'type': 'string', 'example': 'ok'},
                'http_response': {'type': 'integer', 'example': 200},
                'error_messages': {'type': 'array', 'items': {'type': 'string'}, 'example': []},
                'data': {
                    'type': 'object',
                    'properties': {
                        'abstract': {
                            'type': 'string',
                            'description': 'Cleaned abstract text with HTML tags removed',
                            'example': "ECMWF has announced that the Copernicus Climate Change Service (C3S) has begun the release of the ERA5 back extension data covering the period 1950-1978 on the Climate Data Store (CDS). Although in many other respects the quality of this dataset is quite satisfactory, the current back extension appears to suffer from tropical cyclones that are sometimes unrealistically intense. This is in contrast with the ERA5 product from 1979 onwards (also available from the CDS and RDA ds633.0). For this reason the current release of the back extension is preliminary. It is therefore available from separate CDS catalogue entries (hourly, monthly, single level and pressure levels), and this RDA dataset. Around the end of 2021 an updated version of the back extension is to be made available which will be added to the ERA5 catalogue entries that currently reach back to 1979. After an overlap period (the duration of which is not yet decided), the preliminary back extension will be deprecated. The full back extension preliminary dataset is expected to be made available near the end of 2020/early 2021. After many years of research and technical preparation, the production of a new ECMWF climate reanalysis to replace ERA-Interim is in progress. ERA5 is the fifth generation of ECMWF atmospheric reanalyses of the global climate, which started with the FGGE reanalyses produced in the 1980s, followed by ERA-15, ERA-40 and most recently ERA-Interim. ERA5 will cover the period January 1950 to near real time. ERA5 is produced using high-resolution forecasts (HRES) at 31 kilometer resolution (one fourth the spatial resolution of the operational model) and a 62 kilometer resolution ten member 4D-Var ensemble of data assimilation (EDA) in CY41r2 of ECMWF's Integrated Forecast System (IFS) with 137 hybrid sigma-pressure (model) levels in the vertical, up to a top level of 0.01 hPa. Atmospheric data on these levels are interpolated to 37 pressure levels (the same levels as in ERA-Interim). Surface or single level data are also available, containing 2D parameters such as precipitation, 2 meter temperature, top of atmosphere radiation and vertical integrals over the entire atmosphere. The IFS is coupled to a soil model, the parameters of which are also designated as surface parameters, and an ocean wave model. Generally, the data is available at an hourly frequency and consists of analyses and short (12 hour) forecasts, initialized twice daily from analyses at 06 and 18 UTC. Most analyses parameters are also available from the forecasts. There are a number of forecast parameters, e.g. mean rates and accumulations, that are not available from the analyses. Improvements to ERA5, compared to ERA-Interim, include use of HadISST.2, reprocessed ECMWF climate data records (CDR), and implementation of RTTOV11 radiative transfer. Variational bias corrections have not only been applied to satellite radiances, but also ozone retrievals, aircraft observations, surface pressure, and radiosonde profiles. DECS produces a CF 1.6 compliant netCDF-4/HDF5 version of ERA5 for the CISL RDA at NCAR. The netCDF-4/HDF5 version is the de facto RDA ERA5 online data format. The GRIB1 data format is also available online. There is a one-to-one correspondence between the netCDF-4/HDF5 and GRIB1 files, with as much GRIB1 metadata as possible incorporated into the attributes of the netCDF-4/HDF5 counterpart."
                        },
                        'note': {
                            'type': 'string',
                            'description': 'Any warning or note text found in the abstract',
                            'example': "It is advised to use ds633.0, ERA5 Reanalysis (0.25 Degree Latitude-Longitude Grid)."
                        },
                        'urls': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'description': 'List of unique URLs found in the abstract text',
                            'example': ["https://rda.ucar.edu/datasets/ds633-0/"]
                        }
                    }
                },
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        },
        400: {
            'type': 'object',
            'description': 'Dataset not found',
            'properties': {
                'status': {'type': 'string', 'example': 'error'},
                'http_response': {'type': 'integer', 'example': 400},
                'error_messages': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'example': ['Abstract not found for dataset d123456']
                },
                'data': {'type': 'object', 'example': {}},
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        }
    },
    tags=['abstract']
)
@api_view(['GET'])
def get_abstract(request, dsid):
    """Get abstract text for a given dataset"""
    dsid = common.format_dataset_id(dsid)
    abstract_text = common.get_abstract(dsid)

    return _handle_dataset_response(
        dsid,
        abstract_text,
        "Abstract not found for dataset {dsid}"
    )

@extend_schema(
    operation_id='get_dataset_acknowledgement',
    summary='Get dataset acknowledgement text',
    description='''
    Retrieves the acknowledgement text for a specific dataset.
    HTML paragraph tags (`<p>`, `</p>`) are automatically stripped from the response
    ''',
    parameters=[
        OpenApiParameter(
            name='dsid',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description='Dataset identifier in 6-digit format (e.g., d123456)',
            required=True,
            pattern=r'd\d{6}'
        )
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'ok'},
                'http_response': {'type': 'integer', 'example': 200},
                'error_messages': {'type': 'array', 'items': {'type': 'string'}, 'example': []},
                'data': {
                    'type': 'object',
                    'properties': {
                        'acknowledgement': {
                            'type': 'string',
                            'example': "Papers using the NOAA-CIRES-DOE Twentieth Century Reanalysis Project version 3 dataset are requested to include the following text in their acknowledgements: \"Support for the Twentieth Century Reanalysis Project version 3 dataset is provided by the U.S. Department of Energy, Office of Science Biological and Environmental Research (BER), by the National Oceanic and Atmospheric Administration Climate Program Office, and by the NOAA Physical Sciences Laboratory.\""
                        }
                    }
                },
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        },
        400: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'error'},
                'http_response': {'type': 'integer', 'example': 400},
                'error_messages': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'example': ['Acknowledgement not found for dataset d633004']
                },
                'data': {'type': 'object', 'example': {}},
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        }
    },
    tags=['acknowledgment']
)
@api_view(['GET'])
def get_acknowledgement(request, dsid):
    """Get acknowledgement information for a given dataset"""
    dsid = common.format_dataset_id(dsid)
    acknowledgement_text = common.get_acknowledgement(dsid)

    data = {'acknowledgement': acknowledgement_text} if acknowledgement_text else None
    return _handle_dataset_response(
        dsid,
        data,
        "Acknowledgement not found for dataset {dsid}"
    )

@extend_schema(
    operation_id='get_dataset_temporal_coverage',
    summary='Get dataset temporal coverage',
    description='''
        Retrieves the temporal coverage information for a specific dataset.
        Returns start date, end date, and data groups with their respective time ranges.
    ''',
    parameters=[
        OpenApiParameter(
            name='dsid',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description='Dataset identifier in 6-digit format (e.g., d123456)',
            required=True,
            pattern=r'd\d{6}'
        )
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'ok'},
                'http_response': {'type': 'integer', 'example': 200},
                'error_messages': {'type': 'array', 'items': {'type': 'string'}, 'example': []},
                'data': {
                    'type': 'object',
                    'properties': {
                        'temporal': {
                            'type': 'object',
                            'properties': {
                                'start_date': {
                                    'type': 'string',
                                    'example': '1805-12-31 18:00 +0000'
                                },
                                'end_date': {
                                    'type': 'string',
                                    'example': '2016-01-01 00:00 +0000'
                                },
                                'data_groups': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'description': {
                                                'type': 'string',
                                                'example': 'Yearly Time Series 3-Hourly Analysis Fields'
                                            },
                                            'start_date': {
                                                'type': 'string',
                                                'example': '1805-12-31 18:00 +0000'
                                            },
                                            'end_date': {
                                                'type': 'string',
                                                'example': '2016-01-01 00:00 +0000'
                                            }
                                        }
                                    },
                                    'example': [
                                        {
                                            'description': 'Yearly Time Series 3-Hourly Analysis Fields',
                                            'start_date': '1805-12-31 18:00 +0000',
                                            'end_date': '2016-01-01 00:00 +0000'
                                        },
                                        {
                                            'description': 'Yearly Time Series 3-Hourly First Guess Forecast Fields',
                                            'start_date': '1806-12-31 18:00 +0000',
                                            'end_date': '2015-12-31 12:00 +0000'
                                        },
                                        {
                                            'description': 'Yearly Time Series 6-Hourly Analysis Fields',
                                            'start_date': '1806-12-31 21:00 +0000',
                                            'end_date': '2015-12-31 15:00 +0000'
                                        }
                                    ]
                                }
                            }
                        }
                    }
                },
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        },
        400: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'error'},
                'http_response': {'type': 'integer', 'example': 400},
                'error_messages': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'example': ['Temporal coverage not found for dataset d633004']
                },
                'data': {'type': 'object', 'example': {}},
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        }
    },
    tags=['temporal']
)
@api_view(['GET'])
def get_temporal(request, dsid):
    """Get temporal coverage information including start date, end date, and time range for a given dataset"""
    dsid = common.format_dataset_id(dsid)
    temporal_data = common.get_temporal_range(dsid)
    return _handle_dataset_response(
        dsid,
        temporal_data,
        "Temporal coverage not found for dataset {dsid}",
        wrap_key='temporal'
    )

@extend_schema(
    operation_id='get_dataset_variables',
    summary='Get dataset variables',
    description='''
        Retrieves the list of variables for a specific dataset.
        Returns a count of variables, a list of all variables, and variables organized by categories.
        Note: Variables represented in this API include but are not limited to those available in the dataset.
    ''',
    parameters=[
        OpenApiParameter(
            name='dsid',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description='Dataset identifier in 6-digit format (e.g., d123456)',
            required=True,
            pattern=r'd\d{6}'
        )
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'ok'},
                'http_response': {'type': 'integer', 'example': 200},
                'error_messages': {'type': 'array', 'items': {'type': 'string'}, 'example': []},
                'data': {
                    'type': 'object',
                    'properties': {
                        'count': {
                            'type': 'integer',
                            'example': 40,
                            'description': 'Total number of variables'
                        },
                        'variables': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'example': [
                                'Accumulative Convective Precipitation',
                                'Air Temperature',
                                'Atmospheric Ozone',
                                'Cloud Base Height',
                                'Cloud Fraction'
                            ],
                            'description': 'List of all variables in the dataset'
                        },
                        'categories': {
                            'type': 'object',
                            'additionalProperties': {
                                'type': 'array',
                                'items': {'type': 'string'}
                            },
                            'example': {
                                'Atmosphere': [
                                    'Accumulative Convective Precipitation'
                                ],
                                'Surface Temperature': [
                                    'Air Temperature',
                                    'Maximum/Minimum Temperature'
                                ],
                                'Oxygen Compounds': [
                                    'Atmospheric Ozone'
                                ],
                                'Cloud Properties': [
                                    'Cloud Base Height'
                                ],
                                'Cloud Indicators': [
                                    'Cloud Fraction'
                                ]
                            },
                            'description': 'Variables organized by category'
                        },
                        'message': {
                            'type': 'string',
                            'example': 'The variables represented in this API include but are not limited to those available in the dataset. Additional variables may be present in the actual data files.',
                            'description': 'Additional information about variable availability'
                        }
                    }
                },
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        },
        400: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'error'},
                'http_response': {'type': 'integer', 'example': 400},
                'error_messages': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'example': ['Variables not found for dataset d633004']
                },
                'data': {'type': 'object', 'example': {}},
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        }
    },
    tags=['variables']
)
@api_view(['GET'])
def get_variables(request, dsid):
    """Get list of variables in a given dataset"""
    dsid = common.format_dataset_id(dsid)
    variables_data = common.get_variables(dsid)
    return _handle_dataset_response(
        dsid,
        variables_data,
        "Variables not found for dataset {dsid}"
    )

@extend_schema(
    operation_id='get_dataset_publications',
    summary='Get dataset publications',
    description='''
        Retrieves the list of publications related to a specific dataset.
        Returns a count of publications and detailed information about each publication including authors, title, journal, and DOI.
    ''',
    parameters=[
        OpenApiParameter(
            name='dsid',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description='Dataset identifier in 6-digit format (e.g., d123456)',
            required=True,
            pattern=r'd\d{6}'
        )
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'ok'},
                'http_response': {'type': 'integer', 'example': 200},
                'error_messages': {'type': 'array', 'items': {'type': 'string'}, 'example': []},
                'data': {
                    'type': 'object',
                    'properties': {
                        'count': {
                            'type': 'integer',
                            'example': 2,
                            'description': 'Total number of publications'
                        },
                        'publications': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'authors': {
                                        'type': 'array',
                                        'items': {'type': 'string'},
                                        'example': ['Slivinski', 'Compo', 'Sardeshmukh', 'Whitaker', 'McColl'],
                                        'description': 'List of author surnames or full names'
                                    },
                                    'authors_text': {
                                        'type': 'string',
                                        'example': 'Slivinski, L. C., Compo, G. P., Sardeshmukh, P. D., Whitaker, J. S., McColl, C., Allan, R. J., Brohan, P., Yin, X., Smith, C. A., Spencer, L. J., Vose, R. S., Rohrer, M., Conroy, R. P., Schuster, D. C., Kennedy, J. J., Ashcroft, L., Brönnimann, S., Brunet, M., Camuffo, D., Cornes, R., Cram, T. A., Domínguez-Castro, F., Freeman, J. E., Gergis, J., Hawkins, E., Jones, P. D., Kubota, H., Lee, T. C., Lorrey, A. M., Luterbacher, J., Mock, C. J., Przybylak, R. K., Pudmenzky, C., Slonosky, V. C., Tinz, B., Trewin, B., Wang, X. L., Wilkinson, C., Wood, K., & Wyszyński, P.',
                                        'description': 'Formatted author names as citation text'
                                    },
                                    'year': {
                                        'type': 'string',
                                        'example': '2021',
                                        'description': 'Publication year'
                                    },
                                    'title': {
                                        'type': 'string',
                                        'example': 'An Evaluation of the Performance of the Twentieth Century Reanalysis Version 3',
                                        'description': 'Publication title'
                                    },
                                    'journal': {
                                        'type': 'string',
                                        'example': 'Journal of Climate',
                                        'description': 'Journal name'
                                    },
                                    'volume_pages': {
                                        'type': 'string',
                                        'example': '34(4)',
                                        'description': 'Volume and issue information'
                                    },
                                    'doi': {
                                        'type': 'string',
                                        'example': '10.1002/qj.3598',
                                        'description': 'Digital Object Identifier'
                                    },
                                    'url': {
                                        'type': 'string',
                                        'example': 'https://rmets.onlinelibrary.wiley.com/doi/10.1002/qj.3598',
                                        'description': 'Publication URL'
                                    }
                                }
                            },
                            'description': 'List of publications with detailed information'
                        }
                    }
                },
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        },
        400: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'error'},
                'http_response': {'type': 'integer', 'example': 400},
                'error_messages': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'example': ['Publications not found for dataset d633004']
                },
                'data': {'type': 'object', 'example': {}},
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        }
    },
    tags=['publications']
)
@api_view(['GET'])
def get_publications(request, dsid):
    """Get publications information for a given dataset"""
    dsid = common.format_dataset_id(dsid)
    publications_data = common.get_publications(dsid)
    return _handle_dataset_response(
        dsid,
        publications_data,
        "Publications not found for dataset {dsid}"
    )

@extend_schema(
    operation_id='get_dataset_license',
    summary='Get dataset license information',
    description='''
        Retrieves the licensing information for a specific dataset.
        Returns the license name and URL with legal details.
    ''',
    parameters=[
        OpenApiParameter(
            name='dsid',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description='Dataset identifier in 6-digit format (e.g., d123456)',
            required=True,
            pattern=r'd\d{6}'
        )
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'ok'},
                'http_response': {'type': 'integer', 'example': 200},
                'error_messages': {'type': 'array', 'items': {'type': 'string'}, 'example': []},
                'data': {
                    'type': 'object',
                    'properties': {
                        'name': {
                            'type': 'string',
                            'example': 'Creative Commons Attribution 4.0 International License',
                            'description': 'Full name of the data license'
                        },
                        'url': {
                            'type': 'string',
                            'example': 'https://creativecommons.org/licenses/by/4.0/legalcode',
                            'description': 'URL to the license legal text'
                        }
                    }
                },
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        },
        400: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'error'},
                'http_response': {'type': 'integer', 'example': 400},
                'error_messages': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'example': ['Data license not found for dataset d633004']
                },
                'data': {'type': 'object', 'example': {}},
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        }
    },
    tags=['data_license']
)
@api_view(['GET'])
def get_data_license(request, dsid):
    """Get licensing information for a given dataset"""
    dsid = common.format_dataset_id(dsid)
    data_license = common.get_data_license(dsid)
    return _handle_dataset_response(
        dsid,
        data_license,
        "Data license not found for dataset {dsid}"
    )

@extend_schema(
    operation_id='get_dataset_data_types',
    summary='Get dataset data types',
    description='''
        Retrieves the types of data contained in a specific dataset.
        Returns a list of data type categories (e.g., Grid, Point, Station).
    ''',
    parameters=[
        OpenApiParameter(
            name='dsid',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description='Dataset identifier in 6-digit format (e.g., d123456)',
            required=True,
            pattern=r'd\d{6}'
        )
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'ok'},
                'http_response': {'type': 'integer', 'example': 200},
                'error_messages': {'type': 'array', 'items': {'type': 'string'}, 'example': []},
                'data': {
                    'type': 'object',
                    'properties': {
                        'data_types': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'example': ['Grid'],
                            'description': 'List of data types contained in the dataset'
                        }
                    }
                },
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        },
        400: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'error'},
                'http_response': {'type': 'integer', 'example': 400},
                'error_messages': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'example': ['Data types not found for dataset d633004']
                },
                'data': {'type': 'object', 'example': {}},
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        }
    },
    tags=['data_types']
)
@api_view(['GET'])
def get_data_types(request, dsid):
    """Get types of data contained in a given dataset"""
    dsid = common.format_dataset_id(dsid)
    data_types = common.get_data_types(dsid)
    return _handle_dataset_response(
        dsid,
        data_types,
        "Data types not found for dataset {dsid}",
        wrap_key='data_types'
    )

@extend_schema(
    operation_id='get_dataset_data_formats',
    summary='Get dataset data formats',
    description='''
        Retrieves the available file formats and data structure information for a specific dataset.
        Returns a count of formats and detailed information about each format including description, URL, and documentation availability.
    ''',
    parameters=[
        OpenApiParameter(
            name='dsid',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description='Dataset identifier in 6-digit format (e.g., d123456)',
            required=True,
            pattern=r'd\d{6}'
        )
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'ok'},
                'http_response': {'type': 'integer', 'example': 200},
                'error_messages': {'type': 'array', 'items': {'type': 'string'}, 'example': []},
                'data': {
                    'type': 'object',
                    'properties': {
                        'count': {
                            'type': 'integer',
                            'example': 1,
                            'description': 'Total number of data formats'
                        },
                        'data_formats': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'description': {
                                        'type': 'string',
                                        'example': 'netCDF4',
                                        'description': 'Format name or description'
                                    },
                                    'url': {
                                        'type': 'string',
                                        'example': 'http://www.unidata.ucar.edu/software/netcdf/',
                                        'description': 'URL with information about the format'
                                    },
                                    'has_documentation': {
                                        'type': 'boolean',
                                        'example': 'true',
                                        'description': 'Whether documentation is available for this format'
                                    }
                                }
                            },
                            'description': 'List of available data formats with details'
                        }
                    }
                },
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        },
        400: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'error'},
                'http_response': {'type': 'integer', 'example': 400},
                'error_messages': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'example': ['Data formats not found for dataset d633004']
                },
                'data': {'type': 'object', 'example': {}},
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        }
    },
    tags=['data_formats']
)
@api_view(['GET'])
def get_data_formats(request, dsid):
    """Get available file formats and data structure information for a given dataset"""
    dsid = common.format_dataset_id(dsid)
    data_formats = common.get_data_formats(dsid)
    return _handle_dataset_response(
        dsid,
        data_formats,
        "Data formats not found for dataset {dsid}"
    )

@extend_schema(
    operation_id='get_dataset_spatial_coverage',
    summary='Get dataset spatial coverage',
    description='''
        Retrieves the spatial coverage information for a specific dataset.
        Returns geographic bounds, resolution, coordinate ranges, and grid dimensions.
    ''',
    parameters=[
        OpenApiParameter(
            name='dsid',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description='Dataset identifier in 6-digit format (e.g., d123456)',
            required=True,
            pattern=r'd\d{6}'
        )
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'ok'},
                'http_response': {'type': 'integer', 'example': 200},
                'error_messages': {'type': 'array', 'items': {'type': 'string'}, 'example': []},
                'data': {
                    'type': 'object',
                    'properties': {
                        'spatial_coverage': {
                            'type': 'object',
                            'properties': {
                                'bounds': {
                                    'type': 'object',
                                    'properties': {
                                        'north': {
                                            'type': 'number',
                                            'example': 89.463,
                                            'description': 'Northern boundary'
                                        },
                                        'south': {
                                            'type': 'number',
                                            'example': -89.463,
                                            'description': 'Southern boundary'
                                        },
                                        'east': {
                                            'type': 'number',
                                            'example': 180,
                                            'description': 'Eastern boundary'
                                        },
                                        'west': {
                                            'type': 'number',
                                            'example': -180,
                                            'description': 'Western boundary'
                                        },
                                        'lat_units': {
                                            'type': 'string',
                                            'example': 'degrees north',
                                            'description': 'Latitude units'
                                        },
                                        'lon_units': {
                                            'type': 'string',
                                            'example': 'degrees east',
                                            'description': 'Longitude units'
                                        }
                                    },
                                    'description': 'Geographic boundaries of the dataset'
                                },
                                'resolution': {
                                    'type': 'object',
                                    'properties': {
                                        'longitude': {
                                            'type': 'number',
                                            'example': 0.703,
                                            'description': 'Longitude resolution'
                                        },
                                        'latitude': {
                                            'type': 'number',
                                            'example': 0.702,
                                            'description': 'Latitude resolution'
                                        },
                                        'units': {
                                            'type': 'string',
                                            'example': 'degrees',
                                            'description': 'Resolution units'
                                        }
                                    },
                                    'description': 'Spatial resolution of the dataset'
                                },
                                'coordinate_range': {
                                    'type': 'object',
                                    'properties': {
                                        'longitude_start': {
                                            'type': 'string',
                                            'example': '0E',
                                            'description': 'Starting longitude coordinate'
                                        },
                                        'longitude_end': {
                                            'type': 'string',
                                            'example': '359.297E',
                                            'description': 'Ending longitude coordinate'
                                        },
                                        'latitude_start': {
                                            'type': 'string',
                                            'example': '89.463N',
                                            'description': 'Starting latitude coordinate'
                                        },
                                        'latitude_end': {
                                            'type': 'string',
                                            'example': '89.463S',
                                            'description': 'Ending latitude coordinate'
                                        }
                                    },
                                    'description': 'Coordinate range with directional indicators'
                                },
                                'grid_dimensions': {
                                    'type': 'object',
                                    'properties': {
                                        'longitude_points': {
                                            'type': 'integer',
                                            'example': 512,
                                            'description': 'Number of longitude grid points'
                                        },
                                        'latitude_points': {
                                            'type': 'integer',
                                            'example': 256,
                                            'description': 'Number of latitude grid points'
                                        }
                                    },
                                    'description': 'Grid dimensions in number of points'
                                }
                            },
                            'description': 'Complete spatial coverage information'
                        }
                    }
                },
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        },
        400: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'error'},
                'http_response': {'type': 'integer', 'example': 400},
                'error_messages': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'example': ['Spatial coverage not found for dataset d633004']
                },
                'data': {'type': 'object', 'example': {}},
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        }
    },
    tags=['spatial']
)
@api_view(['GET'])
def get_spatial_coverage(request, dsid):
    """Get spatial coverage for a given dataset"""
    dsid = common.format_dataset_id(dsid)
    spatial_data = common.get_spatial_coverage(dsid)
    return _handle_dataset_response(
        dsid,
        spatial_data,
        "Spatial coverage not found for dataset {dsid}",
        wrap_key='spatial_coverage'
    )

@extend_schema(
    operation_id='get_dataset_contributors',
    summary='Get dataset contributors',
    description='''
        Retrieves information about contributors for a specific dataset.
        Returns contributor details including names, IDs, and categories.
    ''',
    parameters=[
        OpenApiParameter(
            name='dsid',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description='Dataset identifier in 6-digit format (e.g., d123456)',
            required=True,
            pattern=r'd\d{6}'
        )
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'ok'},
                'http_response': {'type': 'integer', 'example': 200},
                'error_messages': {'type': 'array', 'items': {'type': 'string'}, 'example': []},
                'data': {
                    'type': 'object',
                    'properties': {
                        'count': {
                            'type': 'integer',
                            'example': 1,
                            'description': 'Number of contributors'
                        },
                        'contributors': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'id': {
                                        'type': 'string',
                                        'example': 'UCO/CIRES',
                                        'description': 'Contributor identifier'
                                    },
                                    'name': {
                                        'type': 'string',
                                        'example': 'Cooperative Institute for Research in Environmental Sciences, University of Colorado',
                                        'description': 'Full contributor name'
                                    },
                                    'category': {
                                        'type': 'string',
                                        'example': 'academic',
                                        'description': 'Contributor category (e.g., academic, government)'
                                    }
                                },
                                'description': 'Individual contributor information'
                            },
                            'description': 'List of dataset contributors'
                        }
                    }
                },
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        },
        400: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'error'},
                'http_response': {'type': 'integer', 'example': 400},
                'error_messages': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'example': ['Contributors not found for dataset d633004']
                },
                'data': {'type': 'object', 'example': {}},
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        }
    },
    tags=['contributors']
)
@api_view(['GET'])
def get_contributors(request, dsid):
    """Get information about dataset contributors"""
    dsid = common.format_dataset_id(dsid)
    contributors_data = common.get_contributors(dsid)
    return _handle_dataset_response(
        dsid,
        contributors_data,
        "Contributors not found for dataset {dsid}"
    )

@extend_schema(
    operation_id='get_dataset_total_volume',
    summary='Get dataset total volume',
    description='''
        Retrieves the total volume information for a specific dataset.
        Returns overall dataset size and breakdown by volume groups.
    ''',
    parameters=[
        OpenApiParameter(
            name='dsid',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description='Dataset identifier in 6-digit format (e.g., d123456)',
            required=True,
            pattern=r'd\d{6}'
        )
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'ok'},
                'http_response': {'type': 'integer', 'example': 200},
                'error_messages': {'type': 'array', 'items': {'type': 'string'}, 'example': []},
                'data': {
                    'type': 'object',
                    'properties': {
                        'total_volume': {
                            'type': 'string',
                            'example': '105.26 TB',
                            'description': 'Total dataset volume with units'
                        },
                        'volume_groups': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'group': {
                                        'type': 'string',
                                        'example': 'Yearly Time Series 3-Hourly Analysis Fields (Gaussian T-254)',
                                        'description': 'Volume group name or category'
                                    },
                                    'volume': {
                                        'type': 'string',
                                        'example': '68.52 TB',
                                        'description': 'Volume size for this group with units'
                                    }
                                },
                                'description': 'Individual volume group information'
                            },
                            'description': 'Breakdown of dataset volume by groups'
                        }
                    }
                },
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        },
        400: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'error'},
                'http_response': {'type': 'integer', 'example': 400},
                'error_messages': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'example': ['Total volume not found for dataset d633004']
                },
                'data': {'type': 'object', 'example': {}},
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        }
    },
    tags=['volume']
)
@api_view(['GET'])
def get_total_volume(request, dsid):
    """Get dataset size information including total volume"""
    dsid = common.format_dataset_id(dsid)
    volume = common.get_total_volume(dsid)
    return _handle_dataset_response(
        dsid,
        volume,
        "Total volume not found for dataset {dsid}"
    )

@extend_schema(
    operation_id='get_dataset_related_resources',
    summary='Get related resources',
    description='''
        Retrieves related resources for a specific dataset.
        Returns external tools, software, documentation, and other resources related to the dataset.
    ''',
    parameters=[
        OpenApiParameter(
            name='dsid',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description='Dataset identifier in 6-digit format (e.g., d123456)',
            required=True,
            pattern=r'd\d{6}'
        )
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'ok'},
                'http_response': {'type': 'integer', 'example': 200},
                'error_messages': {'type': 'array', 'items': {'type': 'string'}, 'example': []},
                'data': {
                    'type': 'object',
                    'properties': {
                        'count': {
                            'type': 'integer',
                            'example': 1,
                            'description': 'Number of related resources'
                        },
                        'resources_list': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'description': {
                                        'type': 'string',
                                        'example': 'Software that converts NetCDF files into WRF intermediate files',
                                        'description': 'Description of the related resource'
                                    },
                                    'url': {
                                        'type': 'string',
                                        'example': 'https://pywinter.readthedocs.io/en/latest/',
                                        'description': 'URL link to the related resource'
                                    }
                                },
                                'description': 'Individual related resource information'
                            },
                            'description': 'List of related resources'
                        }
                    }
                },
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        },
        400: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'error'},
                'http_response': {'type': 'integer', 'example': 400},
                'error_messages': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'example': ['Related resources not found for dataset d633004']
                },
                'data': {'type': 'object', 'example': {}},
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        }
    },
    tags=['resources']
)
@api_view(['GET'])
def get_related_resources(request, dsid):
    """Get related resources for a given dataset"""
    dsid = common.format_dataset_id(dsid)
    resources_list = common.get_related_resources(dsid)
    return _handle_dataset_response(
        dsid,
        resources_list,
        "Related resources not found for dataset {dsid}"
    )

@extend_schema(
    operation_id='get_dataset_related_datasets',
    summary='Get related datasets',
    description='''
        Retrieves datasets that are related to or derived from the specified dataset.
        Returns a list of related datasets with their identifiers and titles.
    ''',
    parameters=[
        OpenApiParameter(
            name='dsid',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description='Dataset identifier in 6-digit format (e.g., d123456)',
            required=True,
            pattern=r'd\d{6}'
        )
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'ok'},
                'http_response': {'type': 'integer', 'example': 200},
                'error_messages': {'type': 'array', 'items': {'type': 'string'}, 'example': []},
                'data': {
                    'type': 'object',
                    'properties': {
                        'count': {
                            'type': 'integer',
                            'example': 1,
                            'description': 'Number of related datasets'
                        },
                        'resources_list': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'dsid': {
                                        'type': 'string',
                                        'example': 'd093000',
                                        'description': 'Related dataset identifier'
                                    },
                                    'title': {
                                        'type': 'string',
                                        'example': 'NCEP Climate Forecast System Reanalysis (CFSR) 6-hourly Products, January 1979 to December 2010',
                                        'description': 'Related dataset title'
                                    }
                                },
                                'description': 'Individual related dataset information'
                            },
                            'description': 'List of related datasets'
                        }
                    }
                },
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        },
        400: {
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'error'},
                'http_response': {'type': 'integer', 'example': 400},
                'error_messages': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'example': ['Related datasets not found for dataset d633004']
                },
                'data': {'type': 'object', 'example': {}},
                'contact': {'type': 'string', 'example': 'rdahelp@ucar.edu'}
            }
        }
    },
    tags=['related_datasets']
)
@api_view(['GET'])
def get_related_datasets(request, dsid):
    """Get other datasets that are related to or derived from this dataset"""
    dsid = common.format_dataset_id(dsid)
    datasets_list = common.get_related_datasets(dsid)
    return _handle_dataset_response(
        dsid,
        datasets_list,
        "Related datasets not found for dataset {dsid}"
    )

@extend_schema(
    operation_id='get_all_datasets',
    summary='List all available datasets',
    description='''
    Retrieves a complete list of all available datasets in the system.

    Returns basic information for each dataset including:
    - Dataset ID (dsid)
    - Dataset title (dstitle)

    **Response Details:**
    - Results are ordered by dataset ID
    - Includes count of total datasets
    - Provides clean list for dataset discovery and browsing
    ''',
    parameters=[],
    responses={
        200: {
            'type': 'object',
            'description': 'Successfully retrieved list of all datasets',
            'properties': {
                'status': {'type': 'string', 'example': 'ok'},
                'http_response': {'type': 'integer', 'example': 200},
                'error_messages': {'type': 'array', 'items': {'type': 'string'}, 'example': []},
                'data': {
                    'type': 'object',
                    'properties': {
                        'count': {
                            'type': 'integer',
                            'description': 'Total number of datasets available'
                        },
                        'datasets': {
                            'type': 'array',
                            'description': 'List of all datasets with basic information',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'id': {
                                        'type': 'string',
                                        'description': 'Dataset identifier in 6-digit format'
                                    },
                                    'title': {
                                        'type': 'string',
                                        'description': 'Dataset title'
                                    }
                                }
                            }
                        }
                    }
                },
                'error_messages': {'type': 'array', 'items': {'type': 'string'}, 'example': []}
            }
        }
    },
    tags=['all_datasets']
)
@api_view(['GET'])
def get_all_datasets(request):
    """Get a complete list of all available datasets in the Research Data Archive"""
    all_datasets = common.get_all_datasets()
    json = all_datasets
    response = rda_r.RDA_Response()
    response.add_data(json)
    return JsonResponse(response.get_json())

