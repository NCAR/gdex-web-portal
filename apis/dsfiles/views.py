import json
import psycopg2

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from facbrowse.utils import service_list
from libpkg.codemaps import decode_level, decode_parameter
from libpkg.dbutils import uncompress_bitmap_values
from libpkg.gridutils import convert_grid_definition


def swagger(request, output=None):
    return render(request, "dsfiles/swagger.html", {})


def get_grml_filters(dsid, **kwargs):
    filters = {'parameters': [],
               'products': [],
               'grids': [],
               'levels': []}
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        query = ("select concat(s.format_code, '!', s.parameter), s."
                 "time_range_code, t.time_range, s.grid_definition_code, "
                 "concat(g.definition, '!', g.def_params), s."
                 'level_type_codes, f.format from "WGrML".summary as s left '
                 'join "WGrML".time_ranges as t on t.code = s.time_range_code '
                 'left join "WGrML".grid_definitions as g on g.code = s.'
                 'grid_definition_code left join "WGrML".formats as f on f.'
                 "code = s.format_code where s.dsid = %s")
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
                    filters['parameters'].append({'name': param_name,
                                                  'code': e[0]})

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
        return HttpResponse("Server error.", status_code=500)
    finally:
        if 'conn' in locals():
            conn.close()

    return filters


def filters(request, dsid):
    response = {'DSID': dsid,
                'restrictions': {},
                'filters': {}}
    services = service_list(dsid)
    if "GrML" in services:
        if 'parameters' in request.GET:
            response['restrictions']['parameters'] = (
                    request.GET.getlist('parameters'))

        response['filters'] = get_grml_filters(dsid,
                                               **response['restrictions'])
        if len(response['restrictions']) == 0:
            del response['restrictions']

    return HttpResponse(json.dumps(response), content_type="application/json")


def files(request, dsid)
    return HttpResponse("files")
