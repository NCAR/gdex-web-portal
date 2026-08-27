import json
from drf_spectacular.utils import extend_schema
import os
import requests
from datetime import datetime, timedelta
import hmac
import hashlib
import re
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
from . import filesearch
from accounts.cookies import verified_cookie_email

from rest_framework.decorators import api_view, renderer_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.renderers import JSONRenderer

from .docs import (
    param_summary_schema,
    get_metadata_schema,
    get_staff_schema,
    get_staff_by_dataset_schema,
    get_root_groups_schema,
    get_assembled_groups_schema,
    has_arco_schema,
    get_arco_variables_schema,
    search_arco_variables_schema,
    get_child_groups_schema,
    get_web_files_schema,
    get_dataset_documentation_schema,
    get_dataset_software_schema,
    list_datasets_simple_schema,
    get_summary_schema,
    submit_schema,
    get_control_file_template_schema,
    get_status_schema,
    get_req_files_schema,
    purge_schema,
    globus_download_schema,
    volume_downloaded_schema,
    unique_users_schema,
    total_datasets_schema,
    total_citations_schema,
    gdex_volume_schema,
    total_requests_schema,
    top_datasets_schema,
    ai_datasets_schema,
    dataset_users_month_schema,
    dataset_users_year_schema,
    dataset_volume_month_schema,
    dataset_volume_year_schema,
    get_abstract_schema,
    get_acknowledgement_schema,
    get_temporal_schema,
    get_variables_schema,
    get_publications_schema,
    get_data_license_schema,
    get_data_types_schema,
    get_data_formats_schema,
    get_spatial_coverage_schema,
    get_contributors_schema,
    get_total_volume_schema,
    get_related_resources_schema,
    get_related_datasets_schema,
    get_all_datasets_schema,
    filesearch_datatypes_schema,
    filesearch_filters_cyclone_fix_schema,
    filesearch_filters_grid_schema,
    filesearch_filters_sensor_schema,
    filesearch_files_cyclone_fix_schema,
    filesearch_files_grid_schema,
    filesearch_files_sensor_schema,
    filesearch_result_set_schema,
    exclude_schema,
)

import logging
logger = logging.getLogger(__name__)

def dynamic_prefix_cache_page(timeout, prefix_func, *, cache=None, key_prefix=None):
    """This decorator is exactly like cache_page, but with the option to skip
    the caching entirely.

    The second argument is a callable, ``condition``. It's given the
    request and all further arguments, and if it evaluates to a true-ish
    value, the cache is used.
    """

    def decorator(func):
        def wrapper(request, *args, **kwargs):
            custom_prefix = prefix_func(request, *args, **kwargs)
            return cache_page(timeout=timeout, cache=cache, key_prefix=custom_prefix)(
                    func
                )(request, *args, **kwargs)

        return wrapper
    return decorator

def get_path(request, *args, **kwargs):
    return request.path

def verify_login(request):
    cookies = request.COOKIES
    return None

@param_summary_schema
@api_view(['GET'])
#@dynamic_prefix_cache_page(60*60*24*7, get_path)
def param_summary(request, dsid):
    json = rdams.main("-get_param_summary",dsid)
    return JsonResponse(json)

@get_metadata_schema
@api_view(['GET'])
#@dynamic_prefix_cache_page(60*60*24*7, get_path)
def get_metadata(request, dsid):
    json = rdams.main("-get_metadata",dsid)
    return JsonResponse(json)

@get_staff_schema
@api_view(['GET'])
#@dynamic_prefix_cache_page(60*60*24*7, get_path)
def get_staff(request):
    json = common.get_staff()
    response = rda_r.RDA_Response()
    response.add_data(json)
    return JsonResponse(response.get_json())

@get_staff_by_dataset_schema
@api_view(['GET'])
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

    @exclude_schema
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


def _handle_dataset_response(dsid, data, error_message_template, wrap_key=None, error_detail=None):
    """Helper function to handle common dataset response pattern
    Args:
        dsid: Dataset ID
        data: The data returned from common function
        error_message_template: Template for error message with {dsid} placeholder
        wrap_key: Optional key to wrap data in (e.g., 'temporal', 'data_types')
        error_detail: Optional extra detail explaining why data is missing/invalid,
            appended to the error message (e.g. the reason a parse failed)
    """
    response = rda_r.RDA_Response()

    if data is None or not data:
        message = error_message_template.format(dsid=dsid)
        if error_detail:
            message = "{}: {}".format(message, error_detail)
        response.add_error_message(message)
        response.add_data('')
        return JsonResponse(response.get_json(), status=400)
    else:
        # wrap data in a key if specified, otherwise use data directly
        json_data = {wrap_key: data} if wrap_key else data
        response.add_data(json_data)
        return JsonResponse(response.get_json())

@exclude_schema
def clear_cache(request, dsid):
    """Clear cache that matches dsid"""
    assert re.match('d\d\d\d\d\d\d', dsid)
    token = request.GET.get('token', 'default')
    if not common.is_superuser(token):
        return JsonResponse({"success": False, 'message': 'Not a super user'})
    import glob
    cache_dir = '/usr/local/gdexweb/cache/'
    matched_files = glob.glob(f'{cache_dir}*{dsid}*')
    if not matched_files:
        return JsonResponse({"success": False})
    for file in matched_files:
        os.remove(file)
    return JsonResponse({"success": True})

@get_root_groups_schema
@api_view(['GET'])
#@dynamic_prefix_cache_page(60*60*24*7, get_path)
def get_root_groups(request, dsid):
    dsid = common.format_dataset_id(dsid)
    json = common.get_root_groups(dsid)
    response = rda_r.RDA_Response()
    response.add_data(json)
    return JsonResponse(response.get_json())

@get_assembled_groups_schema
@api_view(['GET'])
#@dynamic_prefix_cache_page(60*60*24*7, get_path)
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

@has_arco_schema
@cache_page(4 * 24 * 60 * 60) # cache for 4 days
@api_view(['GET'])
def has_arco(request, dsid):
    """Return true if arco datasets available"""
    result = common.has_arco(dsid)
    response = rda_r.RDA_Response()
    response.add_data({'has_arco':result})
    return JsonResponse(response.get_json())

@get_arco_variables_schema
@cache_page(4 * 24 * 60 * 60) # cache for 4 days
@api_view(['GET'])
def get_arco_variables(request, dsid):
    result = common.get_arco_variables(dsid)
    response = rda_r.RDA_Response()
    response.add_data(result)
    return JsonResponse(response.get_json())

@search_arco_variables_schema
@api_view(['GET'])
def search_arco_variables(request, dsid, search_text):
    data = common.get_arco_variables(dsid)
    header = data[0]
    _vars = data[1:]
    matches = []
    for i in _vars:
        for j in i:
            if search_text.lower() in j.lower():
                matches.append(i)
                break
    response = rda_r.RDA_Response()
    response.add_data(matches)
    return JsonResponse(response.get_json())

@get_child_groups_schema
@api_view(['GET'])
def get_child_groups(request, dsid, gindex):
    dsid = common.format_dataset_id(dsid)
    json = common.get_child_groups(dsid, gindex)
    response = rda_r.RDA_Response()
    response.add_data(json)
    return JsonResponse(response.get_json())

def dynamic_key_prefix(request):
    return f"section:{request.resolver_match.url_name}"

@get_web_files_schema
@api_view(['GET'])
#@dynamic_prefix_cache_page(60*60*24*7, get_path)
def get_web_files(request, dsid, gindex, filter_wfile=None):
    dsid = common.format_dataset_id(dsid)
    json = common.get_web_files_from_gindex(dsid, gindex, filter_wfile=filter_wfile)
    response = rda_r.RDA_Response()
    response.add_data(json)
    response_json = response.get_json()
    #print(response_json)
    return JsonResponse(response_json)

#@dynamic_prefix_cache_page(60*60*24*7, get_path)
def assemble_filelist(request, dsid):
    root_groups = common.get_root_groups()

@get_dataset_documentation_schema
@api_view(['GET'])
#@dynamic_prefix_cache_page(60*60*24*7, get_path)
def get_dataset_documentation(request, dsid):
    dsid = common.format_dataset_id(dsid)
    json = common.get_dataset_documentation(dsid)
    response = rda_r.RDA_Response()
    response.add_data(json)
    return JsonResponse(response.get_json())

@get_dataset_software_schema
@api_view(['GET'])
#@dynamic_prefix_cache_page(60*60*24*7, get_path)
def get_dataset_software(request, dsid):
    dsid = common.format_dataset_id(dsid)
    json = common.get_dataset_software(dsid)
    response = rda_r.RDA_Response()
    response.add_data(json)
    response_json = response.get_json()
    return JsonResponse(response_json)

@extend_schema(exclude=True)
@csrf_exempt
@api_view(['POST'])
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

@list_datasets_simple_schema
@api_view(['GET'])
def get_datasets(request):
    json = common.get_all_datasets()
    return JsonResponse({'data':json})

@get_summary_schema
@api_view(['GET'])
#@dynamic_prefix_cache_page(60*60*24*7, get_path)
def get_summary(request, dsid):
    json = rdams.main("-get_summary",dsid)
    return JsonResponse(json)

@submit_schema
@csrf_exempt
@api_view(['POST'])
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

@exclude_schema
@csrf_exempt
def submit_json(request):
    email = get_email_from_token(request)
    if email is None:
        response = rda_r.RDA_Response()
        response.add_message('Incorrect Token. Visit "https://gdex.ucar.edu/accounts/profile/" to obtain token.')
        return JsonResponse(response.get_json())
    json = rdams.main("-submit")
    return JsonResponse(json)


@get_control_file_template_schema
@api_view(['GET'])
#@dynamic_prefix_cache_page(60*60*24*7, get_path)
def get_control_file_template(request, dsid):
    json = rdams.main("-get_control_file_template", dsid)
    return JsonResponse(json)

@exclude_schema
#@dynamic_prefix_cache_page(60*60*24*7, get_path)
def get_control_file_template_old(request, dsid):
    json = rdams.main("-get_control_file_template_old", dsid)
    return JsonResponse(json)

@get_status_schema
@api_view(['GET'])
def get_status(request, rindex=None):
    email = get_email_from_token(request)
    if email is None:
        email = verified_cookie_email(request, 'ruser')
    json = rdams.main("-get_status", rindex, email)
    return JsonResponse(json)

@get_req_files_schema
@api_view(['GET'])
def get_req_files(request, rindex):
    email = get_email_from_token(request)
    json = rdams.main("-get_req_files", rindex, email)
    return JsonResponse(json)

@exclude_schema
def get_req_files_old(request, rindex):
    json = rdams.main("-get_req_files_old", rindex)
    return JsonResponse(json)

@volume_downloaded_schema
@cache_page(4 * 24 * 60 * 60) # cache for 4 days
@api_view(['GET'])
def volume_downloaded(request):
    volume = common.get_volume_downloaded_db()
    return JsonResponse({'volume':volume})

@unique_users_schema
@cache_page(4 * 24 * 60 * 60) # cache for 4 days
@api_view(['GET'])
def unique_users(request):
    ips = common.get_number_of_unique_users_db()
    return JsonResponse({'ips':ips})

@total_datasets_schema
@cache_page(24 * 60 * 60)
@api_view(['GET'])
def total_datasets(request):
    return JsonResponse({'value': common.get_number_of_datasets()})

@total_citations_schema
@cache_page(24 * 60 * 60)
@api_view(['GET'])
def total_citations(request):
    return JsonResponse({'value': common.get_total_citations()})

@gdex_volume_schema
@cache_page(24 * 60 * 60)
@api_view(['GET'])
def gdex_volume(request):
    return JsonResponse({'value': common.get_gdex_volume()})

@total_requests_schema
@cache_page(24 * 60 * 60)
@api_view(['GET'])
def total_requests(request):
    return JsonResponse({'value': common.get_total_requests()})

@top_datasets_schema
@cache_page(24 * 60 * 60)
@api_view(['GET'])
def top_datasets(request):
    return JsonResponse({'top_datasets': common.get_top_datasets()})

@ai_datasets_schema
@cache_page(24 * 60 * 60)
@api_view(['GET'])
def ai_datasets(request):
    return JsonResponse({'ai_datasets': [list(row) for row in common.get_AI_datasets()]})

TWO_WEEKS = 14 * 24 * 60 * 60

@dataset_users_month_schema
@cache_page(TWO_WEEKS)
@api_view(['GET'])
def dataset_users_month(request, dsid):
    since = datetime.now() - timedelta(days=30)
    return JsonResponse({'value': common.get_dataset_users(dsid, since)})

@dataset_users_year_schema
@cache_page(TWO_WEEKS)
@api_view(['GET'])
def dataset_users_year(request, dsid):
    since = datetime.now() - timedelta(days=365)
    return JsonResponse({'value': common.get_dataset_users(dsid, since)})

@dataset_volume_month_schema
@cache_page(TWO_WEEKS)
@api_view(['GET'])
def dataset_volume_month(request, dsid):
    since = datetime.now() - timedelta(days=30)
    return JsonResponse(common.get_dataset_volume(dsid, since))

@dataset_volume_year_schema
@cache_page(TWO_WEEKS)
@api_view(['GET'])
def dataset_volume_year(request, dsid):
    since = datetime.now() - timedelta(days=365)
    return JsonResponse(common.get_dataset_volume(dsid, since))

@globus_download_schema
@api_view(['GET'])
def globus_download(request, rindex, endpoint):
    json = rdams.main("-globus_download", rindex, endpoint)
    return JsonResponse(json)

@purge_schema
@csrf_exempt
@api_view(['DELETE'])
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

@get_abstract_schema
@api_view(['GET'])
#@dynamic_prefix_cache_page(60*60*24*7, get_path)
def get_abstract(request, dsid):
    """Get abstract text for a given dataset"""
    dsid = common.format_dataset_id(dsid)
    abstract_text = common.get_abstract(dsid)

    return _handle_dataset_response(
        dsid,
        abstract_text,
        "Abstract not found for dataset {dsid}"
    )

@get_acknowledgement_schema
@api_view(['GET'])
#@dynamic_prefix_cache_page(60*60*24*7, get_path)
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

@get_temporal_schema
@api_view(['GET'])
#@dynamic_prefix_cache_page(60*60*24*7, get_path)
def get_temporal(request, dsid):
    """Get temporal coverage information including start date, end date, and time range for a given dataset"""
    dsid = common.format_dataset_id(dsid)
    error_detail = None
    try:
        temporal_data = common.get_temporal_range(dsid)
    except ValueError as e:
        logger.warning("get_temporal: failed to parse temporal data for dsid %s: %s", dsid, e)
        temporal_data = None
        error_detail = str(e)

    return _handle_dataset_response(
        dsid,
        temporal_data,
        "Temporal coverage not found for dataset {dsid}",
        wrap_key='temporal',
        error_detail=error_detail
    )

@get_variables_schema
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

@get_publications_schema
@api_view(['GET'])
#@dynamic_prefix_cache_page(60*60*24*7, get_path)
def get_publications(request, dsid):
    """Get publications information for a given dataset"""
    dsid = common.format_dataset_id(dsid)
    publications_data = common.get_publications(dsid)
    return _handle_dataset_response(
        dsid,
        publications_data,
        "Publications not found for dataset {dsid}"
    )

@get_data_license_schema
@api_view(['GET'])
#@dynamic_prefix_cache_page(60*60*24*7, get_path)
def get_data_license(request, dsid):
    """Get licensing information for a given dataset"""
    dsid = common.format_dataset_id(dsid)
    data_license = common.get_data_license(dsid)
    return _handle_dataset_response(
        dsid,
        data_license,
        "Data license not found for dataset {dsid}"
    )

@get_data_types_schema
@api_view(['GET'])
#@dynamic_prefix_cache_page(60*60*24*7, get_path)
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

@get_data_formats_schema
@api_view(['GET'])
#@dynamic_prefix_cache_page(60*60*24*7, get_path)
def get_data_formats(request, dsid):
    """Get available file formats and data structure information for a given dataset"""
    dsid = common.format_dataset_id(dsid)
    data_formats = common.get_data_formats(dsid)
    return _handle_dataset_response(
        dsid,
        data_formats,
        "Data formats not found for dataset {dsid}"
    )

@get_spatial_coverage_schema
@api_view(['GET'])
#@dynamic_prefix_cache_page(60*60*24*7, get_path)
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

@get_contributors_schema
@api_view(['GET'])
#@dynamic_prefix_cache_page(60*60*24*7, get_path)
def get_contributors(request, dsid):
    """Get information about dataset contributors"""
    dsid = common.format_dataset_id(dsid)
    contributors_data = common.get_contributors(dsid)
    return _handle_dataset_response(
        dsid,
        contributors_data,
        "Contributors not found for dataset {dsid}"
    )

@get_total_volume_schema
@api_view(['GET'])
#@dynamic_prefix_cache_page(60*60*24*7, get_path)
def get_total_volume(request, dsid):
    """Get dataset size information including total volume"""
    dsid = common.format_dataset_id(dsid)
    volume = common.get_total_volume(dsid)
    return _handle_dataset_response(
        dsid,
        volume,
        "Total volume not found for dataset {dsid}"
    )

@get_related_resources_schema
@api_view(['GET'])
#@dynamic_prefix_cache_page(60*60*24*7, get_path)
def get_related_resources(request, dsid):
    """Get related resources for a given dataset"""
    dsid = common.format_dataset_id(dsid)
    resources_list = common.get_related_resources(dsid)
    return _handle_dataset_response(
        dsid,
        resources_list,
        "Related resources not found for dataset {dsid}"
    )

@get_related_datasets_schema
@api_view(['GET'])
#@dynamic_prefix_cache_page(60*60*24*7, get_path)
def get_related_datasets(request, dsid):
    """Get other datasets that are related to or derived from this dataset"""
    dsid = common.format_dataset_id(dsid)
    datasets_list = common.get_related_datasets(dsid)
    return _handle_dataset_response(
        dsid,
        datasets_list,
        "Related datasets not found for dataset {dsid}"
    )

@get_all_datasets_schema
@api_view(['GET'])
def get_all_datasets(request):
    """Get a complete list of all available datasets in GDEX"""
    all_datasets = common.get_all_datasets()
    json = all_datasets
    response = rda_r.RDA_Response()
    response.add_data(json)
    return JsonResponse(response.get_json())

@filesearch_datatypes_schema
@api_view(['GET'])
def filesearch_datatypes(request, dsid):
    return filesearch.datatypes(dsid)

@filesearch_filters_cyclone_fix_schema
@api_view(['GET'])
def filesearch_filters_cyclone_fix(request, dsid):
    return filesearch.filters(request, dsid, datatype="cyclone_fix")

@filesearch_filters_grid_schema
@api_view(['GET'])
def filesearch_filters_grid(request, dsid):
    return filesearch.filters(request, dsid, datatype="grid")

@filesearch_filters_sensor_schema
@api_view(['GET'])
def filesearch_filters_sensor(request, dsid):
    return filesearch.filters(request, dsid, datatype="sensor")

@filesearch_files_cyclone_fix_schema
@api_view(['GET'])
def filesearch_files_cyclone_fix(request, dsid):
    return filesearch.files(request, dsid, datatype="cyclone_fix")

@filesearch_files_grid_schema
@api_view(['GET'])
def filesearch_files_grid(request, dsid):
    return filesearch.files(request, dsid, datatype="grid")

@filesearch_files_sensor_schema
@api_view(['GET'])
def filesearch_files_sensor(request, dsid):
    return filesearch.files(request, dsid, datatype="sensor")

@filesearch_result_set_schema
@api_view(['GET'])
def filesearch_result_set(request, dsid, result_id, page_num):
    return filesearch.serve_result_set(request, dsid, result_id, page_num)
