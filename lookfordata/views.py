import sys
import json

import psycopg2

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from . import defs
from . import utils


wdb_config = settings.RDADB['wagtail2_config_pg']
metadb_config = settings.RDADB['metadata_config_pg']


def start(request):
    wconn = psycopg2.connect(**wdb_config)
    wcursor = wconn.cursor()
    q = "select refine_filters from lookfordata_lookfordatapage"
    wcursor.execute(q)
    res = wcursor.fetchone()
    wcursor.close()
    arr = json.loads(res[0]);
    mconn = psycopg2.connect(**metadb_config)
    mcursor = mconn.cursor()
    wc = "(d.type = 'P' or d.type = 'H') and d.dsid < 'd999000'"
    q = "select count(distinct dsid) from search.datasets as d where " + wc
    s = "{\"numds\": "
    try:
        mcursor.execute(q)
    except:
        s += "\"??\""
    else:
        r = mcursor.fetchone()
        s += str(r[0])

    s += ", \"facets\": ["
    for e in arr:
        o = e['value']
        if o['query_table']:
            s += ("{\"id\": \"" + o['id'] + "\", \"title\": \"" + o['title'] +
                "\", \"description\": \"" + o['description'] + "\", \"cnt\": ")
            q = ("select count(distinct s.dsid) from " + o['query_table'] +
                     " as s left join search.datasets as d on d.dsid = s.dsid "
                     "where " + wc)
            try:
                mcursor.execute(q);
            except psycopg2.Error as e:
                sys.stderr.write("LOOKFORDATA error '" + str(e) + "' for query '" + q + "'\n")
                s += "\"??\""
            except:
                sys.stderr.write("LOOKFORDATA unknown error for query '" + q + "'\n")
                s += "\"??\""
            else:
                res = mcursor.fetchone()
                s += str(res[0])

            s += "}, "

    mcursor.close()
    s = s[:-2] + "]}"
    response = render(request, "lookfordata/start.html", json.loads(s))
    if not 'lkey' in request.COOKIES:
        response.set_cookie('lkey', utils.generate_lkey())

    return response


def refine(request):
    if not "HTTP_X_REQUESTED_WITH" in request.META:
        return render(request, "404.html")

    if not 'r' in request.GET:
        return HttpResponse("Error: undefined refine", status=400)

    if request.GET['r'] == "ftext":
        return HttpResponse("<div class=\"p-1\"><span class=\"nav-link small lh-sm p-0 pb-1\" style=\"color: #000\">Enter one or more keywords. Preceed a keyword with a minus sign (e.g. <nobr><i>-temperature</i></nobr>) to exclude datasets containing that keyword.</span><form class=\"d-flex mb-3 mb-md-0 px-2\" name=\"fts\" action=\"javascript:void(0)\" onsubmit=\"if (v.value.length == 0) { alert('Please enter one or more free text keywords to search on'); return false; } else { toggleRefine('ftext'); replace_lookfordata_content('/lookfordata/datasets/?b=' + document.fts.b.value + '&v=' + document.fts.v.value); return true; }\"><input class=\"form-control\" type=\"text\" name=\"v\" placeholder=\"keyword(s)\"><i class=\"fas fa-search btn btn-primary p-1\" onclick=\"document.fts.dispatchEvent(new Event('submit'))\"></i><input type=\"hidden\" name=\"b\" value=\"ftext\"></form></div>")

    if not request.GET['r'] in defs.refine_queries:
        return HttpResponse("Error: no function for '" + request.GET['r'] + "'", status=400)

    mconn = psycopg2.connect(**metadb_config)
    mcursor = mconn.cursor()
    nb = False
    if 'nb' in request.GET and request.GET['nb'] == "y":
        nb = True
        t = ([], {})
    else:
        t = utils.read_cache(request.COOKIES['lkey'])

    try:
        mcursor.execute(defs.refine_queries[request.GET['r']](request.COOKIES['lkey'], nb))
        res = mcursor.fetchall()
    except psycopg2.Error as e:
        sys.stderr.write("LOOKFORDATA query error: '" + e.pgerror + "'\n");
        return HttpResponse("Error: failed query", status=500)

    mcursor.close()
    list = []
    no_spec = {}
    for e in res:
        x = None
        if request.GET['r'] in t[1]:
            x = next((i for i in t[1][request.GET['r']] if i['name'] == e[0]), None)

        if x == None:
            if e[0] == None:
                no_spec = {'name': "Not specified", 'display': "Not specified", 'count': e[1]}
            else:
                list.append({'name': e[0], 'display': e[0], 'count': e[1]})

    if no_spec:
        list.append(no_spec)
    return render(request, "lookfordata/refine_slider.html", {'keywords': list, 'refine_by': request.GET['r']})


def show_datasets(request):
    if not 'lkey' in request.COOKIES:
        lkey = utils.generate_lkey()
    else:
        lkey = request.COOKIES['lkey']

    if not 'b' in request.GET or not 'v' in request.GET:
        return render(request, "404.html")

    nb = True if 'nb' in request.GET and request.GET['nb'] == "y" else False
    blist = request.GET.getlist('b')
    vlist = request.GET.getlist('v')
    for x in range(0, len(blist)):
        breadcrumbs = []
        t = None
        if not nb:
            t = utils.read_cache(lkey)
            for key in t[1]:
                for i in t[1][key]:
                    breadcrumbs.append({'refine_by': key, 'category': utils.category(key), 'browse_by': i['name'], 'count': i['count']})

        bdict = {'refine_by': blist[x], 'category': utils.category(blist[x]), 'browse_by': vlist[x]}
        mconn = psycopg2.connect(**metadb_config)
        mcursor = mconn.cursor()
        defs.browse_queries[blist[x]](vlist[x], mcursor)
        res = mcursor.fetchall()
        mcursor.close()
        datasets = []
        i = [0]
        for e in res:
            if t == None or e[0] in t[0]:
                d = {'dsid': e[0], 'title': e[1]}
                if e[3] == "H":
                    d.update({'historical': True})

                d.update({'summary': utils.convert_to_expandable_summary(e[2], 30, i)})
                datasets.append(d)

        cache = utils.open_cache_for_writing(lkey, nb)
        cache.write("@" + blist[x] + "<!>" + vlist[x] + "<!>" + str(len(datasets)) + "\n")
        for e in datasets:
            cache.write(e['dsid'] + "\n")

        cache.close()
        bdict.update({'count': len(datasets)})
        breadcrumbs.append(bdict)
        nb = False

    ctx = {'breadcrumbs': breadcrumbs, 'datasets': datasets}
    if "HTTP_X_REQUESTED_WITH" in request.META:
        response = render(request, "lookfordata/dataset_list.html", ctx)
    else:
        wconn = psycopg2.connect(**wdb_config)
        wcursor = wconn.cursor()
        wcursor.execute("select refine_filters from wagtail.lookfordata_lookfordatapage")
        row = wcursor.fetchone()
        wcursor.close()
        d = {}
        d.update({'refine_filters': json.loads(row[0])})
        d['url'] = ""
        ctx.update({'page': d})
        response = render(request, "lookfordata/look_for_data_page.html", ctx)

    response.set_cookie('lkey', lkey)
    return response


def compare(request):
    if not 'cmp1' in request.GET or not 'cmp2' in request.GET:
        return render(request, "404.html")

    cmp1 = utils.get_comparison_dataset(request.GET['cmp1'])
    if 'error' in cmp1:
        return render(request, "500.html")

    cmp2 = utils.get_comparison_dataset(request.GET['cmp2'])
    if 'error' in cmp2:
        return render(request, "500.html")

    cmp1.update({'dsid': request.GET['cmp1']})
    cmp2.update({'dsid': request.GET['cmp2']})
    return render(request, "lookfordata/dataset_compare.html", {'cmp1': cmp1, 'cmp2': cmp2})
