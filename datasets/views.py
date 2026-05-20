import json
import requests
import psycopg2
import os
import re
import subprocess

from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.forms import ValidationError
#from django.views.decorators.cache import cache_page
from os.path import exists
try:
    from urllib.parse import urlencode
except Exception:
    from urllib import urlencode
from wagtail.models import Page

from libpkg.metaformats import (datacite_4, dublin_core, fgdc, gcmd_dif,
                                iso_19139, json_ld)

from .transform import transform
from .utils import get_custom_subset_context, get_hostname, ng_gdex_id
from .CodeExample import CodeExample
from api.common import (format_dataset_id, get_request_info,
                        get_request_files, get_request_status,
                        get_request_index_from_rqstid,
                        request_type, get_dataset_info,
                        request_column_headers)
import api.common

from dataaccess.matrix import Matrix
from dataset_description.models import DatasetDescriptionPage
from home.utils import slug_list
from globus.views import get_guest_collection_url
from gdexwebserver.utils import make_tempdir, remove_tempdir
from dashboard.utils import get_user_email, is_internal_user

from .forms import DatasetRequestForm
from rda_python_dsrqst.PgRDARqst import rda_request

import logging
logger = logging.getLogger(__name__)

metadb_config = settings.RDADB['metadata_config_pg']

def get_dataset_description_context(dsid):
    """ Return basic dataset description context (dsid, dsdoi, dstitle) """
    slist = slug_list(dsid)
    qs = Page.objects.type(DatasetDescriptionPage).filter(
                           slug__in=slist).live().specific()
    if len(qs) > 0:
        d = {
            'url': "",
            'dsid': qs[0].dsid,
            'dsdoi': qs[0].dsdoi,
            'dstitle': qs[0].dstitle,
            'dslogo': qs[0].dslogo,
            }
        return d
    else:
        return None

def get_result_list(config, query):
    conn = psycopg2.connect(**config)
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    res_list = []
    for res in results:
        res_list.append(res[0])

    return res_list


def description(request, dsid):
    qs = Page.objects.type(DatasetDescriptionPage).filter(
                           slug__in=slug_list(dsid)).live().specific()
    if len(qs) == 0:
        return render(request, "404.html")

    if "HTTP_X_REQUESTED_WITH" in request.META:
        template = "datasets/description.html"
    else:
        template = "dataset_description/dataset_description_page.html"

    ctx = qs[0].get_context(request)
    ctx['page'].dsid = ng_gdex_id(dsid)
    ctx['page'].acknowledgement = (
            ctx['page'].acknowledgement.encode("latin-1")
                                       .decode("unicode-escape"))
    ctx['has_arco'] = api.common.has_arco(ctx['page'].dsid)
    if ctx['has_arco']:
        tmp_vars = api.common.get_arco_variables(ctx['page'].dsid)
        ctx['arco_assets'] = tmp_vars[1:]
        ctx['arco_headers'] = tmp_vars[0]
    software_data = api.common.get_dataset_software(ctx['page'].dsid)
    ctx['has_software'] = bool(software_data.get('files'))
    documentation_data = api.common.get_dataset_documentation(ctx['page'].dsid)
    ctx['has_documentation'] = bool(documentation_data.get('files'))
    return render(request, template, ctx)


def build_matrix(request, dsid):
    if dsid[0] != 'd' or len(dsid) != 7:
        return render(request, "404.html")

    if 'duser' in request.COOKIES:
        duser = request.COOKIES['duser']
        duser = duser if ":" not in duser else duser[:duser.find(":")]
    else:
        duser = None

    ctx = Matrix(dsid, duser).to_json()
    ctx.update({'dsid': dsid})
    if "HTTP_X_REQUESTED_WITH" in request.META:
        template = "dataaccess/matrix.html"
    else:
        d = get_dataset_description_context(dsid)
        if d is None:
            return render(request, "404.html")

        template = "dataaccess/matrix_page.html"
        d.update ({
            'title': "NSF NCAR GDEX | Dataset {} Data Access".format(dsid),
        })
        ctx.update({'page': d})

    return render(request, template, ctx)


def listopt(request, dsid, listtyp):
    dsid = ng_gdex_id(dsid)
    if 'g' in request.GET:
        return listopt_gindex(request, dsid, listtyp, request.GET['g'])

    return listopt_gindex(request, dsid, listtyp, None)


def listopt_gindex(request, dsid, listtyp, gindex):
    if listtyp in ["web", "glade"] or 'duser' in request.COOKIES:
        ctx = {'dsid': dsid}
        if gindex is not None:
            ctx.update({'group': gindex})

        if listtyp == 'web':
            ctx.update({'listtyp': 'Internet', 'listapp': 'weblist'})
        elif listtyp == 'glade':
            ctx.update({'listtyp': 'Glade', 'listapp': 'gladelist'})
        else:
            ctx.update({'error': 'no such list type'})

        d = get_dataset_description_context(dsid)
        if d is None:
            return render(request, "404.html")

        d.update({
            'title': "NSF NCAR GDEX | Dataset {} Data Access".format(dsid),
        })
        ctx.update({'page': d})
        if "HTTP_X_REQUESTED_WITH" in request.META:
            template = "dataaccess/listopt.html"
        else:
            template = "dataaccess/listopt_page.html"

        return render(request, template, ctx)

    return render(request, 'dataaccess/not_authorized.html')

def get_alt_index(json, _type='docs'):
    """Get HTML from alt_index if it exists as a helpfile.

    Args:
        json (obj): JSON formatted object from API call
                    for documentation
        _type (str): 'docs' or 'software'

    Returns (str): HTML content from alt_index.html helpfile
    """
    dsid = json['data']['dsid']
    try:
        for file in json['data']['files']:
            if file['hfile'] == 'alt_index.html':
                alt_url = os.path.join(
                        settings.GLOBUS_STRATUS_BASE_URL,
                        'web/datasets',
                        dsid,
                        f'{_type}/alt_index.html')
                return requests.get(alt_url).text.replace('\n','')
    except KeyError as e:
        print(e)
        return None
    return None

def get_documentation_table(request, dsnum):
    hostname = get_hostname()
    dsid = format_dataset_id(dsnum)
    dsnum = format_dataset_id(dsnum, remove_ds=True)
    api_uri = '/api/datasets/{}/documentation/'.format(dsid)
    url = hostname + api_uri
    documentation = requests.get(url)
    documentation = documentation.content
    documentation_json = json.loads(documentation)

    alt_index = get_alt_index(documentation_json)
    if alt_index:
        documentation_json['data'].update({'alt_index':alt_index})


    if "HTTP_X_REQUESTED_WITH" in request.META:
        template = "datasets/documentation_table.html"
    else:
        d = get_dataset_description_context(dsid)
        if d is None:
            return render(request, "404.html")

        template = "datasets/documentation_table_page.html"
        documentation_json.update({'page': d})

    return render(request, template, documentation_json)


def examples_page(request, dsnum):
    hostname = get_hostname()
    dsid = format_dataset_id(dsnum)
    dsnum = format_dataset_id(dsnum, remove_ds=True)
    api_uri = '/api/datasets/{}/documentation/'.format(dsid)
    url = hostname + api_uri
    documentation = requests.get(url)
    documentation = documentation.content
    documentation_json = json.loads(documentation)
    if "HTTP_X_REQUESTED_WITH" in request.META:
        template = "datasets/documentation_table.html"
    else:
        template = "datasets/documentation_table_page.html"
        d = {'url': ""}
        slist = slug_list(dsnum)
        qs = Page.objects.type(DatasetDescriptionPage).filter(
                               slug__in=slist).live().specific()
        if len(qs) > 0:
            d.update({
                'dsid': qs[0].dsid,
                'dsdoi': qs[0].dsdoi,
                'dstitle': qs[0].dstitle,
                'dslogo': qs[0].dslogo})

        documentation_json.update({'page': d})

    return render(request, template, documentation_json)


#@cache_page(4 * 24 * 60 * 60) # cache for 4 days
def get_software_table(request, dsnum):
    hostname = get_hostname()
    dsid = format_dataset_id(dsnum)
    api_uri = '/api/datasets/{}/software'.format(dsid)
    url = hostname + api_uri
    software = requests.get(url)
    software = software.content
    software_json = json.loads(software)
    return render(request,
                  'datasets/software_table.html',
                  software_json)


def get_filelist_table(request, dsnum, groupid=None):
    hostname = get_hostname()
    dsid = format_dataset_id(dsnum)
    if groupid:
        api_uri = '/api/datasets/{}/filelist/{}'.format(dsid, groupid)
    else:
        api_uri = '/api/datasets/{}/filelist/'.format(dsid)
    page = request.GET.get('page', '')
    filter_wfile = request.GET.get('filter_wfile', '')
    filelist_source = request.GET.get('fl', 'web')
    url = hostname + api_uri
    params = {}
    if page:
        params['page'] = page
    if filelist_source == 'glade':
        params['fl'] = 'glade'
    if filter_wfile:
        params['filter_wfile'] = filter_wfile
    if params:
        url = "{}?{}".format(url, urlencode(params))
    logger.debug("url: {}".format(url))
    filelist = requests.get(url)
    filelist_str = filelist.content
    filelist_json = json.loads(filelist_str)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if 'data' in filelist_json:
            filelist_json['data']['is_ajax'] = True
        else:
            filelist_json['data']['is_ajax'] = False
    if filelist_source == 'glade':
        filelist_json['data']['is_glade'] = True
    else:
        filelist_json['data']['is_glade'] = False

    return render(request,
                  'datasets/filelist.html',
                  filelist_json)


def get_request(request, rqstid):
    """ Get request info and files and render dsrqst
        download page or request status page """

    rindex = get_request_index_from_rqstid(rqstid)
    if rindex is None:
        request_data = {"info": "Request not found", "rqstid": rqstid}
        return render(request,
                      'datasets/request_notfound.html',
                      request_data)

    try:
        rinfo = get_request_info(rindex)
        note = rinfo['subset_info']['note']
        # set note to single space if empty to avoid KeyError in template
        if note:
            note = re.sub(r'^(\r\n|\n\r|\r|\n)', '', note)
        else:
            note = ' '
        rinfo['subset_info']['note'] = note
    except ValueError:
        request_data = {"info": "Request not found", "rqstid": rqstid}
        return render(request,
                      'datasets/request_notfound.html',
                      request_data)

    rinfo.update({'status_code': get_request_status(rindex)})
    ds_info = get_dataset_info(rinfo['dsid'])
    rinfo.update({'dstitle': ds_info['title']})
    dsurl = os.path.join('/datasets', ds_info['dsid'])
    rinfo.update({'dsurl': dsurl})
    globus_url = get_guest_collection_url(rindex=rindex)
    rinfo.update({'globus_url': globus_url})

    has_notes = False

    if (rinfo['status_code'] == 'O') or (rinfo['status_code'] == 'P'):
        rfiles = get_request_files(rindex, with_urls=True)

        if len(rfiles) > 0:
            headers = request_column_headers()
            # Update file type to long name. Check if request file has notes.
            for i in range(len(rfiles)):
                type = rfiles[i]['type']
                rfiles[i].update({'type': request_type(type)})
                if rfiles[i]['note']:
                    has_notes = True

            # Remove 'note' column from headers and file records if no notes
            if not has_notes:
                headers.pop('note', None)
                for i in range(len(rfiles)):
                    rfiles[i].pop('note', None)

            request_data = {
                "info": rinfo,
                "files": rfiles,
                "column_headers": headers}
            request_template = 'datasets/request_filelist.html'
        else:
            request_data = {"info": rinfo}
            request_template = 'datasets/request_nooutput.html'
    else:
        request_data = {"info": rinfo}
        request_template = 'datasets/request_status.html'

    return render(request, request_template, request_data)


def get_metrics(request, dsnum):
    dsid = format_dataset_id(dsnum)
    return redirect(f'/datasets/{dsid}/?content=metrics')


def get_detailed_metadata(request, dsid):
    d = {'url': ""}
    slist = slug_list(dsid)
    qs = Page.objects.type(DatasetDescriptionPage).filter(
                           slug__in=slist).live().specific()
    if len(qs) > 0:
        d.update({
            'dsid': ng_gdex_id(dsid),
            'dsdoi': qs[0].dsdoi,
            'dstitle': qs[0].dstitle,
            'dslogo': qs[0].dslogo,
            'data_types': qs[0].data_types,
            'data_formats': qs[0].data_formats,
            'contributors': qs[0].contributors,
            'volume': qs[0].volume})

    if exists(("/data/web/datasets/" + dsid +
               "/metadata/parameter-detail.html")):
        d['grid_view'] = True
        grid_buttons = {
            'parameter': "Parameter View",
            'level': "Vertical Level View",
            'product': "Product View"}
        if 'view' in request.GET and request.GET['view'] in grid_buttons:
            d['view'] = request.GET['view']
            d['view_button'] = grid_buttons[request.GET['view']]
    else:
        d['obs_view'] = True

    p = get_result_list(metadb_config,
                        ("select g.path from search.projects_new as p left "
                         "join search.gcmd_projects as g on g.uuid = p."
                         "keyword  where dsid in " + str(tuple(slist))))
    if p is not None:
        lst = []
        for x in p:
            lst.append(x)

        d['projects'] = lst

    p = get_result_list(metadb_config,
                        ("select g.path from search.supported_projects as p "
                         "left join search.gcmd_projects as g on g.uuid = p."
                         "keyword where dsid in " + str(tuple(slist))))
    if p is not None:
        lst = []
        for x in p:
            lst.append(x)

        d['supported_projects'] = lst

    if "HTTP_X_REQUESTED_WITH" in request.META:
        template = "datasets/detailed_metadata.html"
    else:
        template = "datasets/detailed_metadata_page.html"

    return render(request,
                  template,
                  {'page': d})

def metadata_view(request, dsid):
    if "HTTP_X_REQUESTED_WITH" not in request.META:
        return render(request, "404.html")

    if 'format' not in request.GET:
        ctx = {'dsid': dsid}
        try:
            conn = psycopg2.connect(**settings.RDADB['dssdb_config_pg'])
            cursor = conn.cursor()
            cursor.execute(("select doi from dssdb.dsvrsn where dsid = %s and "
                            "status = 'A'"), (dsid, ))
            res = cursor.fetchall()
            if len(res) > 0:
                ctx.update({'datacite': True})

        except Exception:
            return HttpResponse("A database error occurred.")
        finally:
            conn.close()
            return render(request, "datasets/metadata_formats_menu.html", ctx)

    md = None
    if request.GET['format'].find("datacite4") == 0:
        parts = request.GET['format'].split("-")
        md, warn = datacite_4.export(
                dsid, settings.RDADB['metadata_config_pg'],
                settings.RDADB['wagtail2_config_pg'], fmt=parts[-1])
    elif request.GET['format'] == "dif":
        md = gcmd_dif.export(dsid, settings.RDADB['metadata_config_pg'],
                             settings.RDADB['wagtail2_config_pg'])
    elif request.GET['format'] == "fgdc":
        md = fgdc.export(dsid, settings.RDADB['metadata_config_pg'],
                         settings.RDADB['wagtail2_config_pg'])
    elif request.GET['format'] == "oai_dc":
        md = dublin_core.export(dsid, settings.RDADB['metadata_config_pg'],
                                settings.RDADB['wagtail2_config_pg'])
    elif request.GET['format'] == "iso19139":
        md = iso_19139.export(dsid, settings.RDADB['metadata_config_pg'],
                              settings.RDADB['wagtail2_config_pg'])
    elif request.GET['format'] == "json-ld":
        md = json_ld.export(dsid, settings.RDADB['metadata_config_pg'],
                            settings.RDADB['wagtail2_config_pg'], indent=2)

    if md is None:
        return HttpResponse((
                "Mapping for this metadata format is currently unavailable."))

    md = md.replace("<", "&lt;").replace(">", "&gt;")
    return HttpResponse("<pre>" + md + "</pre>")

@csrf_exempt
def submit_web_data_request(request, dsid):
    """ View to handle subset data request submitted from the web interface """

    d = None
    if "HTTP_X_REQUESTED_WITH" in request.META:
        confirm_template = 'datasets/request-submit-confirm.html'
        error_template = 'datasets/request-submit-error.html'
        logger.info("Rendering AJAX request submission for dataset {}".format(dsid))
    else:
        d = get_dataset_description_context(dsid)
        if d is None:
            return render(request, "404.html")
        confirm_template = 'datasets/request-submit-confirm-base.html'
        error_template = 'datasets/request-submit-error-base.html'
        logger.info("Rendering full request submission page for dataset {}".format(dsid))

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a mutable copy of POST data
        mutable_post = request.POST.copy()
        mutable_post['fromflag'] = 'W'  # enforce fromflag = 'W' for web requests
        mutable_post['location'] = 'web'  # enforce location = 'web' for web requests
        mutable_post['gindex'] = mutable_post.get('gindex', 0)  # default gindex to 0 if not provided

        # get user email if not provided
        if not mutable_post.get('email', None):
            mutable_post['email'] = get_user_email(request)

        # instantiate a form instance and populate it with data from the request:
        form = DatasetRequestForm(mutable_post, initial={'dsid': dsid})

        # validate the form
        if form.is_valid():
            # check if email is still missing after validation
            if not form.cleaned_data.get('email'):
                form.add_error('email', "Please log in at <a href='/dashboard/'>Dashboard</a> to submit a data request.")
                response = {'error': {'code': 'missing_email'}}
                context = {'form': form, 'response': response}
                if d:
                    context.update({'page': d})
                template = error_template
                logger.info("Missing email error after validation: {}".format(response))
                return render(request, template, context)

            # process the data in form.cleaned_data as required
            try:
                response = rda_request(form.cleaned_data)
            except Exception as e:
                logger.info("Error processing data request: {}".format(e))
                form.add_error(None, str(e))
                response = {'error': {'code': 'processing_error', 'message': str(e)}}
                context = {'form': form, 'response': response}
                if d:
                    context.update({'page': d})
                template = error_template
                return render(request, template, context)

            if 'error' in response:
                logger.info("Request submission error: {}".format(response))
                form.add_error(None, response['error']['message'])
                context = {'form': form, 'response': response}
                if d:
                    context.update({'page': d})
                template = error_template
                return render(request, template, context)

            # successful request submission, redirect to the confirmation page
            logger.info("Request submission successful: {}".format(response))
            template = confirm_template
            context = {'response': response}
            if d:
                context.update({'page': d})
                logger.info("Added dataset description context to confirmation page for dataset {}".format(dsid))
            return render(request, template, context)
        else:
            for field_name, errors in form.errors.items():
                for error in errors:
                    logger.error("Form error in field '{}': {}".format(field_name, error))
            # redirect to the form error page
            response = {'error': {'code': 'invalid_form'}}
            context = {'form': form, 'response': response}
            if d:
                context.update({'page': d})
            template = error_template
            return render(request, template, context)

    # If a GET (or any other method) redirect user to the data access page.
    # DECS staff get a blank request form
    else:
        if is_internal_user(request):
            return blank_request_form(request, dsid)
        else:
            return redirect(f'/datasets/{dsid}/dataaccess/')

def blank_request_form(request, dsid):
    """
    View to display a blank subset request form and manually
    submit a subset data request. This view is only accessible
    to internal DECS staff. External users are redirected to the
    data access page.
    """
    if not is_internal_user(request):
        return render(request, "403.html")

    d = None

    if "HTTP_X_REQUESTED_WITH" in request.META:
        form_template = 'datasets/request-submit-form.html'
        logger.info("Rendering AJAX request form for dataset {}".format(dsid))
    else:
        d = get_dataset_description_context(dsid)
        if d is None:
            return render(request, "404.html")
        form_template = 'datasets/request-submit-form-base.html'
        logger.info("Rendering full request form page for dataset {}".format(dsid))

    form = DatasetRequestForm(initial={'dsid': dsid})
    context = {'form': form}
    if d:
        context.update({'page': d})
        logger.info("Added dataset description context to form page for dataset {}".format(dsid))
    template = form_template
    return render(request, template, context)

def get_native(request, dsid):
    tdir_name = make_tempdir()
    try:
        o = subprocess.run((
                "/usr/bin/cvs -d /data/cvs checkout -d " + tdir_name + " " +
                "datasets/" + dsid + ".xml"), shell=True,
                env={'TMPDIR': "/data/ptmp"}, capture_output=True)
        if o.stderr:
            return HttpResponse("Error: " + o.stderr.decode("utf-8"))

        with open(os.path.join(tdir_name, dsid + ".xml"), "r") as f:
            xml = f.read()

        return HttpResponse(xml, content_type="application/xml")
    finally:
        remove_tempdir(tdir_name)

def custom_subset(request, dsid):
    """
    View to render a custom subset form page

    Templates:
       Depending on the dataset ID, a specific custom subset page template
       may be used. If no specific template exists for the dataset, a generic
       custom subset page template is used.

       default template: datasets/custom-subset-page.html
       specific template: datasets/custom-subset-page-<dsid>.html

    Context:
       This view generates the following context:
         - dsid: dataset ID (d132002, etc.)
         - gindex: group index (if provided in request GET parameters)
         - dataset description page context (dsid, dsdoi, dstitle, etc.)
         - dataset period context (date_start, time_start, date_end, time_end)

    """
    d = None
    if "HTTP_X_REQUESTED_WITH" in request.META:
        if dsid in ['d132002']:
            template = f"datasets/custom-subset-page-{dsid}.html"
        else:
            template = "datasets/custom-subset-page-base.html"
        logger.info("Rendering AJAX custom subset page for dataset {}".format(dsid))
    else:
        d = get_dataset_description_context(dsid)
        if d is None:
            return render(request, "404.html")
        template = "datasets/custom-subset-page-base.html"
        logger.info("Rendering full custom subset page for dataset {}".format(dsid))

    subset_context = {
        'dsid': dsid,
        'title': "NSF NCAR GDEX | Dataset {} Custom Subset".format(dsid),
        'dstitle': d['dstitle'] if d else get_dataset_description_context(dsid)['dstitle'],
    }
    if 'gindex' in request.GET:
        subset_context.update({'gindex': request.GET['gindex']})

    subset_context.update(get_custom_subset_context(dsid, subset_context.get('gindex', None)))

    ctx = {
        'subset': subset_context,
        'gmap_api_key': settings.GMAP_API_KEY,
        'gmap_api_url': settings.GMAP_API_URL
        }

    if d:
        ctx.update({'page': d})

    return render(request, template, ctx)

def example_view(request, dsid):
    """Displays page to get code examples."""
    if request.GET:
        param = request.GET.get('param', None)
        example_type = request.GET.get('type', None)
        start = request.GET.get('start', None)
        end = request.GET.get('end', None)
        is_remote = request.GET.get('is_remote', None)
        if is_remote:
            is_remote = is_remote.lower() == 'true'
        else:
            is_remote = False
        example_type = request.GET.get('exampletype', 'image')
        nlat = request.GET.get('nlat', 90)
        slat = request.GET.get('slat', -90)
        wlon = request.GET.get('wlon', -180)
        elon = request.GET.get('elon', 180)
        example_obj = CodeExample(dsid, start=start, end=end, is_remote=is_remote, selected_var=param,
                elon=elon,wlon=wlon,slat=slat,nlat=nlat, selected_type=example_type)
        return HttpResponse(example_obj.get_code())
    example_obj = CodeExample(dsid)
    return render(request, "datasets/code_example.html", {'ctx':example_obj})


def markup_view(request, dsid, markup_type, file):
    #if "HTTP_X_REQUESTED_WITH" not in request.META:
    #    return render(request, "404.html")

    return transform(dsid, markup_type, file)
