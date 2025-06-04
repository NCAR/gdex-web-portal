import json
from django.shortcuts import render
from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from . import rdams
from . import common
from . import RDA_Response as rda_r

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


    b.add_markdown_block(" # Notebook for Downloading RDA Data.")
    b.add_code_block(
        "import sys, os",
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
                     "    filename = (save_dir + file).strip()",
                     "    print('Downloading', file)",
                     "    req = requests.get(filename, allow_redirects=True)",
                     "    open(os.path.basename(filename), 'wb').write(req.content)")

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
        return JsonResponse(response.get_json())
    request_body = request.body
    request_json = json.loads(request_body)
    email = get_email_from_token(request)
    if email is None:
        response = rda_r.RDA_Response()
        response.add_message('Incorrect Token. Visit "https://rda.ucar.edu/accounts/profile/" to obtain token.')
        return JsonResponse(response.get_json())
    json_response = rdams.main("-submit", request_json, email)
    return JsonResponse(json_response)

@csrf_exempt
def submit_json(request):
    email = get_email_from_token(request)
    if email is None:
        response = rda_r.RDA_Response()
        response.add_message('Incorrect Token. Visit "https://rda.ucar.edu/accounts/profile/" to obtain token.')
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
        response.add_message('Incorrect Token. Visit "https://rda.ucar.edu/accounts/profile/" to obtain token.')
        return JsonResponse(response.get_json())
    json = rdams.main("-purge", rindex, email)
    return JsonResponse(json)

def get_email_from_token(request):
    token = request.GET.get('token','')
    email = common.get_email_from_token(token)
    print(email)
    return email
