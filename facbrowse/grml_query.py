import math
import os
import psycopg2
import threading

from lxml import etree as ElementTree

from django.conf import settings
from django.shortcuts import render
from libpkg.strutils import snake_to_capital

from . import utils
from .log import add_to_log


def process_preset(dsid, preset, cursor):
    """
    Returns the time range, grid definition, and level codes for the
    given parameter preset.
    """
    cursor.execute((
            "select time_range_code from \"WGrML\".time_range_presets where "
            "dsid = %s and description = %s"), (dsid, preset))
    trngs = [e[0] for e in cursor.fetchall()]
    cursor.execute((
            "select grid_definition_code from \"WGrML\"."
            "grid_definition_presets where dsid = %s and description = %s"),
           (dsid, preset))
    gdefs = [e[0] for e in cursor.fetchall()]
    cursor.execute((
            "select map, type, value from \"WGrML\".level_presets where dsid "
            "= %s and description = %s"), (dsid, preset))
    res = cursor.fetchall()
    levs = []
    for e in res:
        if e[2] == "*":
            cursor.execute((
                    "select code from \"WGrML\".levels where map = %s and "
                    "type = %s"), (e[0], e[1]))
        else:
            cursor.execute((
                    "select code from \"WGrML\".levels where map = %s and "
                    "type = %s and value = %s"), (e[0], e[1], e[2]))

        levs.extend([e[0] for e in cursor.fetchall()])

    return trngs, gdefs, levs


def get_db_subset_options(cursor, dsid, **kwargs):
    opts = {
        'can_spatially_subset': False,
        'can_combine': False,
    }
    query = (
            "select command, to_format, tarflag from dssdb.rcrqst where dsid "
            "= %s")
    if 'gindex' in kwargs:
        query += " and (gindex = %s or gindex = 0)"

    query += (
            " and (command like '%%subconv%%' or command like "
            "'%%dssubset_partition.pl' or command like "
            "'%%dssubset_partition_nospa.pl' or command like "
            "'%%dsrqst_netcdf_commandlist.%%') order by gindex")
    if 'gindex' in kwargs:
        query += " desc"
        vars = (dsid, kwargs['gindex'])
    else:
        query += " asc"
        vars = (dsid, )

    cursor.execute(query, vars)
    res = cursor.fetchall()
    if res[0][0].find("subconv") >= 0:
        opts['is_subconv'] = True
        if res[0][2] == "N":
            opts['can_combine'] = True

    if not res[0][1]:
        opts['can_spatially_subset'] = True
    else:
        fmt = kwargs['ofmt'] if 'ofmt' in kwargs else "native"
        parts = res[0][1].split(":")
        for part in parts:
            if (part and (part == fmt or (fmt == "native" and
                          snake_to_capital(part) == kwargs['ifmt']))):
                opts['can_spatially_subset'] = True

    if 'is_subconv' in opts or res[0][0].find("dssubset_partition.pl") >= 0:
        opts['is_multi_spatial'] = True

    return opts


def translate_grid_definition(type, params):
    parts = params.split(":")
    if type == "gaussLatLon":
        lat1 = float(parts[2][0:-1])
        lat2 = float(parts[4][0:-1])
        if parts[2][-1] != parts[4][-1]:
            yres = (lat1 + lat2)
        else:
            yres = math.fabs(lat1 - lat2)

        yres /= (float(parts[1]) - 1)
        d = (parts[6] + "&deg; x ~" + str(round(yres, 3)) + "&deg; from " +
             parts[3] + " to " + parts[5] + " and " + parts[2] + " to " +
             parts[4] + " <small>(")
        if parts[0] == "-1":
            d += "reduced n" + str(int(float(parts[1]) / 2))
        else:
            d += parts[0] + " x " + parts[1]

        d += " Longitude/Gaussian Latitude)</small>"
        return d

    if type == "lambertConformal":
        return type + "#" + params

    if type == "polarStereographic":
        return type + "#" + params

    if type == "sphericalHarmonics":
        return type + "#" + params

    if type == "latLon" or type == "mercator":
        d = parts[6] + "&deg; x "
        if type == "mercator":
            d += "~"

        d += (parts[7] + "&deg; from " + parts[3] + " to " + parts[5] +
              " and " + parts[2] + " to " + parts[4] + " <small>(")
        if parts[0] == "-1":
            d += "reduced"
        else:
            d += parts[0] + " x " + parts[1]

        d += " Longitude/Latitude)</small>"
        return d

    return ""


def process_grids(cursor, grid_codes):
    cursor.execute((
            "select code, definition, def_params from \"WGrML\"."
            "grid_definitions where code in %s order by definition, "
            "def_params"), (tuple(grid_codes), ))
    res = cursor.fetchall()
    if len(res) > 1:
        # check for nearly identical grid definitions
        found_dupe = True
        while found_dupe:
            found_dupe = False
            for x in range(1, len(res)):
                if len(res[x][2]) == len(res[x-1][2]):
                    nmatch = 0
                    nlen = len(res[x][2])
                    for n in range(0, nlen):
                        if res[x][2][n] == res[x-1][2][n]:
                            nmatch += 1

                    if (nmatch / nlen) > 0.95:
                        tmp_lst = list(res[x])
                        tmp_lst[0] = ",".join([str(tmp_lst[0]),
                                               str(res[x-1][0])])
                        res[x] = tuple(tmp_lst)
                        del res[x-1]
                        found_dupe = True
                        break

    grids = []
    for e in res:
        grids.append((str(e[0]), translate_grid_definition(e[1], e[2])))

    grids.sort(key=utils.sort_grids)
    return grids


def process_levels(cursor, dsid, level_codes):
    cursor.execute((
            "select l.code, l.map, l.type, l.value, f.format from \"WGrML\"."
            "levels as l left join \"WGrML\"." + dsid + "_levels as d on d."
            "level_type_code = l.code left join \"WGrML\".formats as f on f."
            "code = d.format_code where l.code in %s"), (tuple(level_codes), ))
    res = cursor.fetchall()
    d = {}
    lmaps = {}
    for e in res:
        key = e[4] + "." + e[1] + ".xml"
        if key not in lmaps:
            lmaps[key] = ElementTree.parse(os.path.join(
                    "/glade/u/home/rdadata/share/metadata/LevelTables",
                    key)).getroot()

        parts = e[2].split("-")
        tmp_lst = []
        for part in parts:
            lroot = lmaps[key].find("./level[@code='{}']".format(part))
            if lroot is not None:
                description = lroot.find("./description").text
                if description is None:
                    description = part

                tmp_lst.append({'level': description})
            else:
                lroot = lmaps[key].find("./layer[@code='{}']".format(part))
                if lroot is not None:
                    description = lroot.find("./description").text
                    if description is None:
                        description = part

                    tmp_lst.append({'layer': description})

            if lroot is not None:
                unit = lroot.find("./units")
                if unit is not None and unit.text is not None:
                    tmp_lst[-1]['unit'] = " " + unit.text
                else:
                    tmp_lst[-1]['unit'] = ""

        if tmp_lst:
            if len(tmp_lst) == 1:
                key = 'level' if 'level' in tmp_lst[0] else 'layer'
                if (e[3] != "0" or (key == 'level' and len(tmp_lst[0]['unit'])
                                    > 0)):
                    key = tmp_lst[0][key] + ": " + e[3] + tmp_lst[0]['unit']
                else:
                    key = tmp_lst[0][key]

            else:
                if tmp_lst[0] == tmp_lst[1]:
                    key = "level" if 'level' in tmp_lst[0] else "layer"
                    key = "Layer between two '{}': {}{}".format(
                            tmp_lst[0][key], e[3], tmp_lst[0]['unit'])
                else:
                    key0 = "level" if 'level' in tmp_lst[0] else "layer"
                    key1 = "level" if 'level' in tmp_lst[1] else "layer"
                    if tmp_lst[0]['unit'] == tmp_lst[1]['unit']:
                        key = "Layer between '{}' and '{}': {}{}".format(
                                tmp_lst[0][key0], tmp_lst[1][key1], e[3],
                                tmp_lst[0]['unit'])
                    else:
                        parts = e[3].split(",")
                        key = "Layer between '{}' and '{}': {}{},{}{}".format(
                                tmp_lst[0][key0], tmp_lst[1][key1], parts[0],
                                tmp_lst[0]['unit'], parts[1],
                                tmp_lst[1]['unit'])

            if key in d:
                d[key].append(str(e[0]))
            else:
                d[key] = [str(e[0])]

        else:
            add_to_log("process_levels: MISSING LEVEL FOR '{}'".format(e[2]))

    levels = []
    for key in d:
        levels.append((",".join(d[key]), key, False))

    levels.sort(key=utils.sort_levels)
    return levels


def query_inventory(dsid, param, start, end, data, **kwargs):
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute((
                "select code from \"IGrML\".parameters where parameter = %s"),
                (param, ))
        res = cursor.fetchone()
        if len(res) == 0:
            raise Exception()

        vars = [param, start, end]
        q = ("select i.file_code, string_agg(distinct cast(time_range_code as "
             "text), '[!]'), string_agg(distinct cast(grid_definition_code as "
             "text), '[!]'), %s, string_agg(distinct cast(level_code as "
             "text), '[!]'), min(valid_date), max(valid_date), sum(i."
             "byte_length), (s.byte_length = sum(i.byte_length)) from "
             "\"IGrML\"." + dsid + "_inventory_" + str(res[0]) + " as i left "
             "join \"IGrML\"." + dsid + "_inventory_summary as s on s."
             "file_code = i.file_code where ")
        if 'init' in kwargs:
            q += "init_date"
        else:
            q += "valid_date"

        q += " between %s and %s"
        if 'pcodes' in kwargs:
            q += " and time_range_code in %s"
            vars.append(tuple(kwargs['pcodes']))

        if 'gcodes' in kwargs:
            q += " and grid_definition_code in %s"
            vars.append(tuple(kwargs['gcodes']))

        if 'lcodes' in kwargs:
            q += " and level_code in %s"
            vars.append(tuple(kwargs['lcodes']))

        q += " group by i.file_code, s.byte_length"
        cursor.execute("set statement_timeout = 30000")
        cursor.execute(q, vars)
        add_to_log("query_inventory: " + cursor.query.decode("utf-8"))
        res = cursor.fetchall()
        data.extend(res)
    except Exception:
        data.extend([None])
    finally:
        conn.close()


def check_grid_inventory(dsid, params, start, end, **kwargs):
    add_to_log("check_grid_inventory: start")
    tlist = []
    tdata = []
    for param in params:
        tdata.append([])
        tlist.append(threading.Thread(
                target=query_inventory, args=(
                        dsid, param, start, end, tdata[-1]
                ), kwargs=kwargs))
        tlist[-1].start()

    for t in tlist:
        t.join()

    res = []
    fparams = []
    for x in range(0, len(tdata)):
        if len(tdata[x]) > 0:
            if tdata[x][0] is None:
                fparams.append(params[x])
            else:
                res.extend(tdata[x])

    add_to_log("check_grid_inventory: done")
    return (res, fparams)


def parse_grml_query(cursor, dsid, listtyp, request, **kwargs):
    q = ("select w.code, w.format_code from \"WGrML\"." + dsid +
         "_webfiles2 as w")
    wc = []
    vars = None
    if 'gindex' in request.POST:
        q += " left join dssdb.wfile_" + dsid + " as d on d.wfile = w.id"
        wc.append("d.tindex = %s")
        if vars is None:
            vars = [request.POST['gindex']]
        else:
            vars.extend([request.POST['gindex']])

    if 'ptfile' in request.POST:
        wc.append("id ilike %s")
        if vars is None:
            vars = ["%" + request.POST['ptfile'] + "%"]
        else:
            vars.extend(["%" + request.POST['ptfile'] + "%"])

    if len(wc) > 0:
        q += " where " + " and ".join(wc)

    if vars is not None:
        vars = tuple(vars)

    cursor.execute(q, vars)
    res = cursor.fetchall()
    mfiles = [str(e[0]) for e in res]
    formats = set([e[1] for e in res])
    qparams = [y for list in [x.split("[!]")[0].split(",") for x in
               request.POST.getlist('parameter')] for y in list]
    if 'nfmt' in request.POST and request.POST['nfmt'] == "yes":
        qparams = utils.update_parameter_aliases(dsid, qparams)

    start = int((request.POST['startDate'].replace("-", "") +
                 request.POST['startTime'].replace(":", "")))
    if len(request.POST['endDate']) > 0 and len(request.POST['endTime']) > 0:
        end = int((request.POST['endDate'].replace("-", "") +
                   request.POST['endTime'].replace(":", "")))
    else:
        end = 300012312359

    opts = {
        'min_start': 999999999999,
        'max_end': 000000000000,
        'products': [],
        'grids': [],
        'levels': [],
    }
    fcodes = set()
    mparams = []
    s = set(mfiles)
    if 'init' in request.POST and request.POST['init'] == "yes":
        kwargs.update({'init': True})

    if listtyp == "subset" or 'init' in kwargs:
        add_to_log("parse_grml_query: start check_grid_inventory")
        res, sparams = check_grid_inventory(dsid, qparams, start, end,
                                            **kwargs)
        if len(sparams) > 0:
            opts['large_request'] = True

        opts['num_not_whole'] = 0
        opts['volume'] = 0
        for e in res:
            x = str(e[0])
            if x in s:
                fcodes.add(x)
                opts['min_start'] = min(e[5], opts['min_start'])
                opts['max_end'] = max(e[6], opts['max_end'])
                opts['products'].extend([x for x in e[1].split("[!]") if x not
                                         in opts['products']])
                opts['grids'].extend([x for x in e[2].split("[!]") if x not in
                                      opts['grids']])
                if e[3] not in mparams:
                    mparams.append(e[3])

                opts['levels'].extend([x for x in e[4].split("[!]") if x not in
                                       opts['levels']])
                opts['volume'] += e[7]
                if not e[8] or 'map_zoom' in request.POST:
                    opts['num_not_whole'] += 1

        add_to_log("parse_grml_query: done check_grid_inventory")
        #if len(res) == 0:
        #    return {**opts, 'fcodes': []}

    else:
        sparams = qparams

    if len(sparams) > 0:
        add_to_log("parse_grml_query: start grids check")
        sparams = [x.split("!")[-1] for x in sparams]
        if any(key.endswith("codes") for key in kwargs):
            bitmap_agg = False
            q = ("select string_agg(distinct cast(file_code as text), '[!]'), "
                 "string_agg(distinct cast(time_range_code as text), '[!]'), "
                 "string_agg(distinct cast(grid_definition_code as text), "
                 "'[!]'), parameter, level_type_codes, min(start_date), max("
                 "end_date) from \"WGrML\"." + dsid + "_grids2 where "
                 "parameter in %s and start_date <= %s and end_date >= %s")
            vars = [tuple(sparams), end, start]
            if 'pcodes' in kwargs:
                q += " and time_range_code in %s"
                vars.append(tuple(kwargs['pcodes']))

            if 'gcodes' in kwargs:
                q += " and grid_definition_code in %s"
                vars.append(tuple(kwargs['gcodes']))

            q += " group by parameter, level_type_codes"
            cursor.execute(q, tuple(vars))
        else:
            bitmap_agg = True
            q = ("select string_agg(distinct cast(file_code as text), '[!]'), "
                 "string_agg(distinct time_range_codes, '[!]'), string_agg("
                 "distinct grid_definition_codes, '[!]'), parameter, "
                 "string_agg(distinct level_type_codes, '[!]'), min("
                 "start_date), max(end_date) from \"WGrML\"." + dsid +
                 "_agrids2 where parameter in %s and start_date <= %s and "
                 "end_date >= %s group by parameter")
            if 'gindex' in request.POST:
                q += (", level_type_codes, time_range_codes, "
                      "grid_definition_codes")
            vars = [tuple(sparams), end, start]
            cursor.execute(q, tuple(vars))

        add_to_log("parse_grml_query: bitmap_agg: " + str(bitmap_agg) + " " +
                   cursor.query.decode("utf-8"))
        res = cursor.fetchall()
        for e in res:
            codes = e[0].split("[!]")
            codes = [x for x in codes if x in s]
            if codes:
                lcodes = utils.from_bitmaps(e[4], "[!]", [])
                if 'lcodes' in kwargs:
                    lcodes = [x for x in lcodes if x in kwargs['lcodes']]

                if lcodes:
                    fcodes.update(set([x for x in codes if x not in fcodes]))
                    opts['min_start'] = min(e[5], opts['min_start'])
                    opts['max_end'] = max(e[6], opts['max_end'])
                    if bitmap_agg:
                        opts['products'] = utils.from_bitmaps(
                                e[1], "[!]", opts['products'])
                        opts['grids'] = utils.from_bitmaps(
                                e[2], "[!]", opts['grids'])
                    else:
                        opts['products'].extend([
                                x for x in e[1].split("[!]") if x not in
                                opts['products']])
                        opts['grids'].extend([
                                x for x in e[2].split("[!]") if x not in
                                opts['grids']])

                    mparams.append(e[3])
                    opts['levels'].extend([
                            x for x in lcodes if x not in opts['levels']])
        add_to_log("parse_grml_query: done grids check")

    if len(qparams) != len(mparams):
        opts['mparams'] = mparams

    s = str(opts['min_start'])
    opts['min_start'] = " ".join([
            "-".join([s[0:4], s[4:6], s[6:8]]),
            ":".join([s[8:10], s[10:12]])
    ])
    s = str(opts['max_end'])
    opts['max_end'] = " ".join([
            "-".join([s[0:4], s[4:6], s[6:8]]),
            ":".join([s[8:10], s[10:12]])
    ])
    if len(opts['products']) > 0:
        cursor.execute((
                "select code, time_range from \"WGrML\".time_ranges where "
                "code in %s"), (tuple(opts['products']), ))
        res = cursor.fetchall()
        opts['products'] = []
        for e in res:
            opts['products'].append((str(e[0]), e[1]))

        opts['products'].sort(key=utils.sort_products)

    if len(opts['grids']) > 0:
        opts['grids'] = process_grids(cursor, opts['grids'])

    if len(opts['levels']) > 0:
        opts['levels'] = process_levels(cursor, dsid, opts['levels'])

    if len(formats) > 0:
        cursor.execute((
                "select distinct w.format_code, f.format from \"WGrML\"." +
                dsid + "_webfiles2 as w left join \"WGrML\".formats as f on f."
                "code = w.format_code where w.format_code in %s"),
                (tuple(formats), ))
        res = cursor.fetchall()
        opts['input_formats'] = [
                {'code': e[0],
                 'description': snake_to_capital(e[1])} for e in res]

    return {**opts, 'fcodes': fcodes}


def do_grml_query(request, dsid, listtyp):
    ctx = {'dsid': dsid, 'listtyp': listtyp, 'db': "WGrML"}
    add_to_log("do_grml_query: " + str(request.POST) + " " + str(ctx))
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute((
                "select tablename from pg_tables where schemaname = %s and "
                "tablename = %s"), ("WGrML", dsid + "_grids2"))
        res = cursor.fetchone()
        if res is None:
            return render(request, "facbrowse/grml_query.html",
                          {'error': "This service does not exist."})

    except psycopg2.Error:
        return render(request, "facbrowse/grml_query.html",
                      {'error': "A database error occurred."})

    code_args = {}
    ctx['selected'] = {'prods': [], 'gdef': None, 'levs': []}
    ctx.update({'ststep': {'selected': False, 'disabled': False}})
    if 'preset' in request.POST:
        pcodes, gcodes, lcodes = process_preset(dsid, request.POST['preset'],
                                                cursor)
        code_args.update({'pcodes': pcodes, 'gcodes': gcodes,
                          'lcodes': lcodes})
        ctx['selected']['prods'].extend([str(x) for x in pcodes])
        ctx['selected']['gdef'] = ",".join([str(e) for e in gcodes])
        ctx['selected']['levs'].extend(lcodes)
        if (request.POST['preset'].find("WRF") == 0 or request.POST['preset']
                .find("FLEXPART") == 0):
            ctx['ststep']['selected'] = True
            ctx['ststep']['disabled'] = True
    else:
        if 'product' in request.POST:
            ctx['selected']['prods'].extend(
                    [e for e in request.POST.getlist('product')])
            code_args.update({'pcodes': ctx['selected']['prods']})

        if ('grid_definition' in request.POST and len(request.POST[
                'grid_definition']) > 0):
            ctx['selected']['gdef'] = request.POST['grid_definition']
            code_args.update({'gcodes': ctx['selected']['gdef'].split(",")})

        if 'level' in request.POST:
            ctx['selected']['levs'].extend(([
                    int(x) for e in request.POST.getlist('level') for x in
                    e.split(",")]))
            code_args.update({'lcodes': ctx['selected']['levs']})

        if 'ststep' in request.POST:
            ctx['ststep']['selected'] = True

    ctx.update(parse_grml_query(cursor, dsid, listtyp, request, **code_args))
    if len(ctx['fcodes']) == 0:
        add_to_log("do_grml_query: NO MATCH - context = " + str(ctx))
        return render(request, "facbrowse/grml_query.html", ctx)

    # levels to show as selected in the Vertical Level menu need to be set here
    # because the level codes are comma-delimited strings that can have
    # multiple values and this can't be checked in the template
    for x in range(0, len(ctx['levels'])):
        tmp_lst = list(ctx['levels'][x])
        codes = tmp_lst[0].split(",")
        for code in codes:
            if int(code) in ctx['selected']['levs']:
                tmp_lst[2] = True

        ctx['levels'][x] = tuple(tmp_lst)

    if 'mparams' in ctx:
        ctx['parameters'] = []
        for p in ctx['mparams']:
            for x in request.POST.getlist('parameter'):
                if x.find(p) >= 0 and x not in ctx['parameters']:
                    ctx['parameters'].append(x)
                    break

        n = len(request.POST.getlist('parameter')) - len(ctx['parameters'])
        if n > 0:
            ctx['num_params_removed'] = n

        ctx['parameters'] = [tuple(x.split("[!]")) for x in ctx['parameters']]
    else:
        ctx['parameters'] = [tuple(x.split("[!]")) for x in
                             request.POST.getlist('parameter')]

    ctx['parameters'].sort(key=lambda t: t[1])
    if 'gindex' in request.POST and len(request.POST['gindex']) > 0:
        ctx['gindex'] = request.POST['gindex']

    s = " ".join([request.POST['startDate'], request.POST['startTime']])
    if ctx['min_start'] < s:
        ctx['min_start'] = s

    if len(request.POST['endDate']) > 0 and len(request.POST['endTime']) > 0:
        s = " ".join([request.POST['endDate'], request.POST['endTime']])
        if ctx['max_end'] > s:
            ctx['max_end'] = s

    times = []
    for x in range(0, 24):
        times.append(str(x).rjust(2, "0") + ":00")

    ctx['times'] = times
    if listtyp == "subset":
        kwargs = {}
        if 'gindex' in ctx:
            kwargs['gindex'] = ctx['gindex']

        kwargs['ifmt'] = (request.POST['ifmt'].split("[!]")[1] if 'ifmt' in
                          request.POST else
                          ctx['input_formats'][0]['description'])
        if 'ofmt' in request.POST:
            kwargs['ofmt'] = request.POST['ofmt']
            if request.POST['ofmt'] == "netCDF":
                ctx['can_compress'] = True

        ctx.update(get_db_subset_options(cursor, dsid, **kwargs))
        if kwargs['ifmt'] == "WMO GRIB2":
            ctx['can_convert_to_netcdf'] = True
            if ctx.get('is_subconv') is not None:
                ctx['can_convert_to_csv'] = True

        if ('ofmt' not in request.POST or request.POST['ofmt'] not in
                ("netCDF", "csv")):
            ctx['show_topt'] = True
        elif request.POST['ofmt'] == "csv":
            if (len(ctx['parameters']) != 1 or len(ctx['levels']) != 1 or
                    len(ctx['grids']) != 1 or 'nlat' not in request.POST or
                    'slat' in request.POST):
                ctx['alert_csv'] = True

        if ctx['can_spatially_subset']:
            ctx.update({'gmap_api_url': settings.GMAP_API_URL,
                        'gmap_api_key': settings.GMAP_API_KEY})

        if 'is_multi_spatial' not in ctx or 'nlat' in request.POST:
            if 'map_zoom' in request.POST and request.POST['map_zoom'] == "-1":
                ctx['show_manual_display'] = True

        if 'nlat' in request.POST and 'wlon' in request.POST:
            if 'slat' in request.POST:
                ctx['bounds'] = {'nlat': request.POST['nlat'],
                                 'slat': request.POST['slat'],
                                 'wlon': request.POST['wlon'],
                                 'elon': request.POST['elon']}
            else:
                ctx['point'] = {'nlat': request.POST['nlat'],
                                'wlon': request.POST['wlon']}

        if 'map_zoom' in request.POST:
            ctx['tick_position'] = (int(request.POST['map_zoom']) - 2) * 6

        ctx.update({'rnote': {
                'ofmt': "",
                'dates': ("- Start date: " + ctx['min_start'] + "\\n"
                          "- End date: " + ctx['max_end'] + "\\n"),
                'parameters': "- Parameter(s):\\n" + "\\n".join([
                        ("    " + e[1]) for e in ctx['parameters']]) + "\\n",
            }
        })
        if 'ofmt' in request.POST and request.POST['ofmt'] != "native":
            ctx['rnote']['ofmt'] = (
                    "- Output format: " + request.POST['ofmt'] + "\\n")
            if request.POST['ofmt'] not in ("netCDF", "csv"):
                ctx['rnote']['ofmt'] = snake_to_capital(ctx['rnote']['ofmt'])

        if ctx['ststep']['selected']:
            ctx['rnote']['dates'] += "- *Each timestep in its own file\\n"

        if len(ctx['levels']) > 0:
            ctx['rnote']['levels'] = "- Vertical Level(s):\\n" + "\\n".join([
                    "    " + e[1] for e in ctx['levels']]) + "\\n"

        if len(ctx['products']) > 0:
            ctx['rnote']['products'] = "- Product(s):\\n" + "\\n".join([
                    ("    " + e[1]) for e in ctx['products']]) + "\\n"

        if len(ctx['grids']) > 0:
            ctx['rnote'].update({'grids': "- Grid(s):\\n"})
            for grid in ctx['grids']:
                grid = (grid[1].replace("<small>", "")
                        .replace("</small>", "")
                        .replace("&deg;", "-deg"))
                ctx['rnote']['grids'] += "    " + grid + "\\n"

    if listtyp == "gladelist":
        ctx['rda_data_path'] = settings.RDA_DATA_PATH
    else:
        cursor.execute((
                "select s.inet_access, d.locflag from search.datasets as s "
                "left join dssdb.dataset as d on d.dsid = s.dsid where s.dsid "
                "= %s"), (dsid, ))
        res = cursor.fetchone()
        if res is not None and res[0] == "Y":
            if res[1] == "O":
                ctx['data_domain'] = settings.GLOBUS_STRATUS_DOMAIN
            else:
                ctx['data_domain'] = settings.GLOBUS_DATA_DOMAIN

    conn.close()
    log_ctx = ctx.copy()
    log_ctx['fcodes'] = str(len(ctx['fcodes']))
    add_to_log("do_grml_query: context = " + str(log_ctx))
    return render(request, "facbrowse/grml_query.html", ctx)
