import json
import psycopg2

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from facbrowse.grml_query import parse_grml_query
from facbrowse.utils import service_list


def swagger(request, output=None):
    return render(request, "dsfiles/swagger.html", {})


def get_grml_filters(dsid):
    filters = {'parameters': [],
               'products': [],
               'grids': [],
               'levels': []}
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute(
                "select concat(s.format_code, '!', s.parameter), s."
                "time_range_code, t.time_range, s.grid_definition_code, "
                "concat(g.definition, '!', g.def_params), s.level_type_codes "
                'from "WGrML".summary as s left join "WGrML".time_ranges as t '
                'on t.code = s.time_range_code left join "WGrML".'
                "grid_definitions as g on g.code = s.grid_definition_code "
                "where s.dsid = %s", (dsid, ))
        res = cursor.fetchall()
        param_set = set()
        tr_set = set()
        gd_set = set()
        for e in res:
            if e[0] not in param_set:
                param_set.add(e[0])
                filters['parameters'].append({'name': "", 'code': e[0]})

            if e[1] not in tr_set:
                tr_set.add(e[1])
                filters['products'].append({'name': e[2], 'code': e[1]})

            if e[3] not in gd_set:
                gd_set.add(e[3])
                filters['grids'].append({'name': e[4], 'code': e[3]})

            if e[5] not in lbmp_set:
                lbmp_set.add(e[5])
                vals = uncompress_bitmap_values(e[5])
                for val in vals:
                    if val not in lev_set:
                        lev_set.add(val)
                        filters['levels'].append({'name': "", 'code': val})

    except Exception:
        return HttpResponse("Server error.", status_code=500)
    finally:
        if 'conn' in locals():
            conn.close()

    return filters


def filters(request, dsid):
    response = {'DSID': dsid,
                'filters': {}}
    services = service_list(dsid)
    if "GrML" in services:
        response['filters'] = get_grml_filters(dsid)

    return HttpResponse(json.dumps(response), content_type="application/json")
