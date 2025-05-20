import json
import requests
import psycopg2
import os
import re

from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
#from django.views.decorators.cache import cache_page
from os.path import exists
try:
    from urllib.parse import urlencode
except Exception:
    from urllib import urlencode
from wagtail.models import Page

from libpkg.metaformats import (datacite_4, dublin_core, fgdc, gcmd_dif,
                                iso_19139, json_ld)

from .utils import get_hostname, ng_gdex_id
from api.common import (format_dataset_id, get_request_info,
                        get_request_files, get_request_status,
                        get_request_index_from_rqstid,
                        request_type, get_dataset_info,
                        request_column_headers)
from .CodeExample import CodeExample

from dataaccess.matrix import Matrix
from .forms import ISPDSubsetForm
from dataset_description.models import DatasetDescriptionPage
from home.utils import slug_list
from globus.views import get_guest_collection_url

import logging
logger = logging.getLogger(__name__)

metadb_config = settings.RDADB['metadata_config_pg']


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
        template = "dataaccess/matrix_page.html"
        d = {
            'dsid': dsid.replace("-", "."),
            'title': "NCAR RDA Dataset {} Data Access".format(dsid),
            'url': ""}
        slist = slug_list(dsid)
        qs = Page.objects.type(DatasetDescriptionPage).filter(
                               slug__in=slist).live().specific()
        if len(qs) > 0:
            d.update({'dsdoi': qs[0].dsdoi, 'dstitle': qs[0].dstitle})

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

        d = {
            'dsid': dsid,
            'title': "NCAR RDA Dataset {} Data Access".format(dsid),
            'url': ""}
        slist = slug_list(dsid)
        qs = Page.objects.type(DatasetDescriptionPage).filter(
                               slug__in=slist).live().specific()
        if len(qs) > 0:
            d.update({'dsdoi': qs[0].dsdoi, 'dstitle': qs[0].dstitle})

        ctx.update({'page': d})
        if "HTTP_X_REQUESTED_WITH" in request.META:
            template = "dataaccess/listopt.html"
        else:
            template = "dataaccess/listopt_page.html"

        return render(request, template, ctx)

    return render(request, 'dataaccess/not_authorized.html')


def get_documentation_table(request, dsnum):
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
                'dstitle': qs[0].dstitle})

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
                'dstitle': qs[0].dstitle})

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
    return render(request,
                  'datasets/metrics.html',
                  {'dsid': dsid})


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


def custom_subset(request, dsid):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = get_custom_subset_form(dsid, request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required

            # redirect to a new URL:
            return render(request, 'datasets/custom_subset_confirm.html',
                          {'form': form})

    # if a GET (or any other method) we'll create a blank form
    else:
        form = get_custom_subset_form(dsid)

    return render(request, 'datasets/ispdv4_subset.html', {'form': form})


def get_custom_subset_form(dsid, post=None):
    if dsid == 'd132002':
        return ISPDSubsetForm(post)


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
                settings.RDADB['wagtail_config_pg'], fmt=parts[-1])
    elif request.GET['format'] == "dif":
        md = gcmd_dif.export(dsid, settings.RDADB['metadata_config_pg'],
                             settings.RDADB['wagtail_config_pg'])
    elif request.GET['format'] == "fgdc":
        md = fgdc.export(dsid, settings.RDADB['metadata_config_pg'],
                         settings.RDADB['wagtail_config_pg'])
    elif request.GET['format'] == "oai_dc":
        md = dublin_core.export(dsid, settings.RDADB['metadata_config_pg'],
                                settings.RDADB['wagtail_config_pg'])
    elif request.GET['format'] == "iso19139":
        md = iso_19139.export(dsid, settings.RDADB['metadata_config_pg'],
                              settings.RDADB['wagtail_config_pg'])
    elif request.GET['format'] == "json-ld":
        md = json_ld.export(dsid, settings.RDADB['metadata_config_pg'],
                            indent=2)

    if md is None:
        return HttpResponse((
                "Mapping for this metadata format is currently unavailable."))

    md = md.replace("<", "&lt;").replace(">", "&gt;")
    return HttpResponse("<pre>" + md + "</pre>")


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
