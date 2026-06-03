import psycopg2

from django.conf import settings
from django.http import HttpRequest, JsonResponse, QueryDict
from django.shortcuts import render
from facbrowse.grml_query import parse_grml_query
from facbrowse.utils import service_list
from libpkg.codemaps import decode_level, decode_parameter
from libpkg.dbutils import uncompress_bitmap_values
from libpkg.gridutils import convert_grid_definition


datatypes_map = {
    'FixML': "cyclone_fix",
    'GrML': "gridded",
    'ObML': "observation",
    'SatML': "satellite",
}


def swagger(request, output=None):
    return render(request, "dsfiles/swagger.html", {})


def valid_dsid(dsid, cursor):
    cursor.execute(
            "select dsid from search.datasets where dsid = %s and type in "
            "('P', 'H')", (dsid, ))
    dsid, = cursor.fetchone() or (None, )
    return dsid is not None


def datatypes(dsid, cursor):
    services = service_list(dsid)
    if len(services) == 0:
        return JsonResponse(
                {'error_message': "API file discovery is not available for "
                                  "this dataset"},
                status=400)

    response = {'DSID': dsid,
                'datatypes': [datatypes_map[e] for e in services]}
    return JsonResponse(response)


def get_grml_filters(dsid, cursor, **kwargs):
    filters = {'valid_datetime_min': 999999999999,
               'valid_datetime_max': 0,
               'parameters': [],
               'products': [],
               'grids': [],
               'levels': []}
    try:
        query = ("select concat(s.format_code, '!', s.parameter), s."
                 "time_range_code, t.time_range, s.grid_definition_code, "
                 "concat(g.definition, '!', g.def_params), s."
                 "level_type_codes, f.format, s.start_date, s.end_date from "
                 '"WGrML".summary as s left join "WGrML".time_ranges as t on '
                 't.code = s.time_range_code left join "WGrML".'
                 "grid_definitions as g on g.code = s.grid_definition_code "
                 'left join "WGrML".formats as f on f.code = s.format_code '
                 "where s.dsid = %s")
        qparams = [dsid]
        if 'parameters' in kwargs:
            query += " and concat(s.format_code, '!', s.parameter) in %s"
            qparams.append(tuple(kwargs['parameters']))
            del filters['parameters']

        cursor.execute(query, tuple(qparams))
        res = cursor.fetchall()
        if len(res) == 0:
            return filters

        param_set = set()
        param_names = {}
        param_maps = {}
        tr_set = set()
        gd_set = set()
        lbmp_set = set()
        lev_fmts = {}
        for e in res:
            if 'parameters' not in kwargs:
                if e[0] not in param_set:
                    param_set.add(e[0])
                    fmt, param = e[0].split("!")
                    param_name = decode_parameter(e[6], param, param_maps)
                    if param_name not in param_names:
                        param_names[param_name] = e[0]
                    else:
                        param_names[param_name] += "," + e[0]

            if e[1] not in tr_set:
                tr_set.add(e[1])
                filters['products'].append({'name': e[2], 'code': e[1]})

            if e[3] not in gd_set:
                gd_set.add(e[3])
                grid_name = convert_grid_definition(e[4].split("!"),
                                                    output="text")
                filters['grids'].append({'name': grid_name, 'code': e[3]})

            if e[5] not in lbmp_set:
                lbmp_set.add(e[5])
                vals = uncompress_bitmap_values(e[5])
                for val in vals:
                    if val not in lev_fmts.keys():
                        lev_fmts[val] = e[6]

            filters['valid_datetime_min'] = (
                    min(e[7], filters['valid_datetime_min']))
            filters['valid_datetime_max'] = (
                    max(e[8], filters['valid_datetime_max']))

        filters['parameters'] = (
                [{'name': name, 'code': code} for name, code in
                 param_names.items()])
        lev_codes = [k for k in lev_fmts.keys()]
        if len(lev_codes) == 1:
            lev_codes.append(lev_codes[0])

        cursor.execute(
                'select distinct map, type, value, code from "WGrML".levels '
                "where code in %s", (tuple(lev_codes), ))
        res = cursor.fetchall()
        level_maps = {}
        for e in res:
            lev_name = decode_level(lev_fmts[e[3]], *e[0:3], level_maps)
            filters['levels'].append({'name': lev_name, 'code': e[3]})

    except Exception:
        return JsonResponse({'error_message': "Server error."}, status=500)

    s = str(filters['valid_datetime_min'])
    filters['valid_datetime_min'] = (
            f"{s[0:4]}-{s[4:6]}-{s[6:8]} {s[8:10]}:{s[10:12]}")
    s = str(filters['valid_datetime_max'])
    filters['valid_datetime_max'] = (
            f"{s[0:4]}-{s[4:6]}-{s[6:8]} {s[8:10]}:{s[10:12]}")
    return filters


def filters(request, dsid, cursor):
    response = {'DSID': dsid,
                'restrictions': {},
                'filters': {}}
    services = service_list(dsid)
    if "GrML" in services:
        if 'parameters' in request.GET:
            response['restrictions']['parameters'] = (
                    request.GET.getlist('parameters'))

        response['filters'] = (
                get_grml_filters(dsid, cursor, **response['restrictions']))

    if len(response['filters']) == 0:
        return JsonResponse(
                {'error_message': "API file discovery is not available for "
                                  "this dataset"},
                status=400)

    if len(response['restrictions']) == 0:
        del response['restrictions']

    return JsonResponse(response)


def files(request, dsid, datatype, cursor):
    services = service_list(dsid)
    if datatype == "gridded" and "GrML" in services:
        grml_req = HttpRequest()
        grml_req.method = "POST"
        grml_req.POST = QueryDict(mutable=True)
        grml_req.POST.setlist('parameter', request.GET.getlist('parameters'))
        if 'valid_datetime_min' in request.GET:
            parts = request.GET['valid_datetime_min'].split()
            grml_req.POST['startDate'] = parts[0]
            grml_req.POST['startTime'] = parts[1]
        else:
            grml_req.POST['startDate'] = "1000-01-01"
            grml_req.POST['startTime'] = "00:00"

        if 'valid_datetime_max' in request.GET:
            parts = request.GET['valid_datetime_max'].split()
            grml_req.POST['endDate'] = parts[0]
            grml_req.POST['endTime'] = parts[1]
        else:
            grml_req.POST['endDate'] = ""
            grml_req.POST['endTime'] = ""

        grml = parse_grml_query(cursor, dsid, "weblist", grml_req)
        return JsonResponse({'files': grml['fcodes']})

    return JsonResponse(
            {'error_message': "API file discovery is not available for "
                              f"data-type '{datatype}'"},
            status=400)


def respond_to_request(request, dsid, operation, datatype):
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        if not valid_dsid(dsid, cursor):
            return JsonResponse(
                    {'error_message': f"'{dsid}' is not a valid dataset "
                                      "identifier."},
                    status=400)

        if operation == "datatypes":
            return datatypes(dsid, cursor)
        elif operation == "filters":
            return filters(request, dsid, cursor)
        elif operation == "files":
            return files(request, dsid, datatype, cursor)
        else:
            return JsonResponse(
                    {'error_message': f"'{operation}' is not a valid "
                                      "operation."},
                    status=400)

    except Exception:
        return JsonResponse({'error_message': "Server error."}, status=500)
    finally:
        if 'conn' in locals():
            conn.close()
