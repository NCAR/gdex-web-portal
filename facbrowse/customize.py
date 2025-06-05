from datetime import date
from dateutil.relativedelta import relativedelta
from itertools import zip_longest
from pathlib import Path

from django.conf import settings
from django.shortcuts import render
from libpkg.strutils import snake_to_capital

from . import utils
from datasets.utils import ng_gdex_id


def customize_exists(service, dsid, listtyp):
    customize_exists = False
    ds_list = utils.slug_list(dsid)
    if listtyp == "weblist" or listtyp == "gladelist":
        for ds in ds_list:
            if Path(("/usr/local/www/server_root/web/datasets/" + ds +
                     "/metadata/customize.W" + service)).is_file():
                customize_exists = True

    elif listtyp == "subset" or listtyp == "opendap":
        for ds in ds_list:
            if Path(("/usr/local/www/server_root/web/datasets/" + ds +
                     "/metadata/customize.I" + service)).is_file():
                customize_exists = True

    return customize_exists


def customize_grml(request, dsid, gindex, listtyp, path):
    if not path:
        return render(request, "facbrowse/error.html",
                      {'error': 'service_unavailable'})

    ctx = {'dsid': dsid, 'gindex': gindex, 'listtyp': listtyp}
    if listtyp == "weblist" or listtyp == "gladelist":
        ctx.update({'part_file': {'value': ""}})

    if gindex:
        ctx.update({'gtitle': utils.get_group_title(dsid, gindex)})

    else:
        groups = utils.get_groups(dsid)
        if groups:
            ctx.update({'groups': groups})

    plist0 = []
    plist1 = []
    with open(path) as f:
        line = f.readline()
        if line[:11] == "curl_subset":
            line = f.readline()
            ctx.update({'curl_subset': "yes"})

        nlines = int(line)
        nl2 = nlines // 2
        if nlines % 2 == 1:
            nl2 += 1
        for n in range(nl2):
            line = f.readline()
            lst = line.split("<!>")
            plist0.append({'codes': lst[0], 'long_name': lst[1], 'index': n})
        nlines += 1
        for n in range(nl2 + 1, nlines):
            line = f.readline()
            lst = line.split("<!>")
            plist1.append({'codes': lst[0], 'long_name': lst[1], 'index': n})
        plist = list(zip_longest(plist0, plist1))
        line = f.readline()
        lst = line.split()
        sdate = lst[0][0:4] + '-' + lst[0][4:6] + '-' + lst[0][6:8]
        stime = lst[0][8:10] + ':' + lst[0][10:12]
        set_start = sdate
        edate = lst[1][0:4] + '-' + lst[1][4:6] + '-' + lst[1][6:8]
        etime = lst[1][8:10] + ':' + lst[1][10:12]
        if listtyp == "weblist":
            t = utils.has_continuing_updates(dsid)
            if t[0]:
                d = date(int(lst[1][0:4]), int(lst[1][4:6]), int(lst[1][6:8]))
                if t[1] == "monthly" or t[1] == "weekly":
                    d -= relativedelta(days=180)

                elif t[1] == "daily":
                    d -= relativedelta(days=30)

                else:
                    d -= relativedelta(years=2)

                ctx.update({'recent_start_date': str(d)})

        f.close()

    times = []
    for n in range(24):
        time = str(n).zfill(2) + ':00'
        times.append(time)

    presets = utils.get_presets("WGrML", dsid)
    ctx.update({
        'parameters': plist,
        'start_date': sdate,
        'start_time': stime,
        'set_start': set_start,
        'end_date': edate,
        'end_time': etime,
        'presets': presets,
        'times': times,
    })
    return render(request, "facbrowse/customize_grml.html", ctx)


def customize_obml(request, dsid, gindex, listtyp, path):
    if not path:
        return render(request, "facbrowse/error.html",
                      {'error': 'service_unavailable'})

    ctx = {'dsid': dsid, 'gindex': gindex, 'listtyp': listtyp}
    if listtyp == "weblist" or listtyp == "gladelist":
        ctx.update({'part_file': {'value': ""}})

    if gindex:
        ctx.update({'gtitle': utils.get_group_title(dsid, gindex)})

    else:
        groups = utils.get_groups(dsid)
        if groups:
            ctx.update({'groups': groups})

    with open(path) as f:
        line = f.readline()
        lst = line.split()
        sdate = lst[0][0:4] + '-' + lst[0][4:6] + '-' + lst[0][6:8]
        edate = lst[1][0:4] + '-' + lst[1][4:6] + '-' + lst[1][6:8]
        ctx.update({
            'start_date': sdate,
            'end_date': edate,
        })
        line = f.readline()
        nlines = int(line)
        pfms = []
        for n in range(nlines):
            line = f.readline()
            lst = line.split("<!>")
            pfms.append({'code': lst[0], 'name': snake_to_capital(lst[1])})

        ctx.update({'platforms': pfms})
        line = f.readline()
        if "<!>" not in line:
            nlines = int(line)
            dtypes = []
            for n in range(nlines):
                line = f.readline()
                lst = line.split("<!>")
                dtypes.append({'code': lst[0], 'name': lst[1]})

            ctx.update({'data_types': dtypes})

    ctx.update({'gmap_api_url': settings.GMAP_API_URL,
                'gmap_api_key': settings.GMAP_API_KEY})
    return render(request, "facbrowse/customize_obml.html", ctx)


def customize(request, dsid, listtyp):
    dsid = ng_gdex_id(dsid)
    err_resp = utils.validate_request(request, listtyp)
    if err_resp is not None:
        return err_resp

    if "facbrowse/subset" in request.path:
        if utils.toomany_requests(request, dsid):
            return render(request, "facbrowse/error.html",
                          {'error': 'toomany'})

    list = utils.service_list(dsid)
    if not list:
        return render(request, "facbrowse/error.html",
                      {'error': 'no_customization'})

    list = [service for service in list if customize_exists(
            service, dsid, listtyp)]
    if not list:
        return render(request, "facbrowse/error.html",
                      {'error': 'file_check_error'})
    elif list.__len__() > 1:
        return render(request, "facbrowse/error.html",
                      {'error': 'multiple_services', 'type': 'subset',
                       'list': list})

    gindex = request.GET['gindex'] if 'gindex' in request.GET else ""
    if list[0] == "GrML":
        return customize_grml(request, dsid, gindex, listtyp,
                              utils.cache_file(dsid, gindex, "GrML", listtyp))

    elif list[0] == "ObML":
        return customize_obml(request, dsid, gindex, listtyp, utils.cache_file(
                              dsid, gindex, "ObML", listtyp))

    else:
        return render(request, "facbrowse/error.html",
                      {'error': 'service_undefined'})
