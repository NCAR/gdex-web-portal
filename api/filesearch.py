import copy
import psycopg2
import pytz
import re

from datetime import datetime, timedelta
from dateutil import tz
from django.conf import settings
from django.http import HttpRequest, JsonResponse, QueryDict
from django.shortcuts import render
from facbrowse.grml_query import parse_grml_query
from facbrowse.utils import service_list
from libpkg.codemaps import decode_level, decode_parameter
from libpkg.dbutils import uncompress_bitmap_values
from libpkg.gridutils import convert_grid_definition
from libpkg.strutils import strand


datatypes_map = {
    'FixML': "cyclone_fix",
    'GrML': "grid",
    'ObML': "sensor",
}

grid_date_re = r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}"

PAGE_SIZE = 1000

files_response = {'dsid': "", 'datatype': "", 'restrictions': {},
                  'files': {
                      'https_base': settings.RDA_DATA_BASE_URL,
                      'ncar_hpc_base': settings.GDEX_CANONICAL_DATA_PATH},
                  'pagination': {}}


def swagger(request, output=None):
    return render(request, "dsfiles/swagger.html", {})


def valid_dsid(dsid, cursor):
    cursor.execute(
            "select dsid from search.datasets where dsid = %s and type in "
            "('P', 'H')", (dsid, ))
    dsid, = cursor.fetchone() or (None, )
    return dsid is not None


def datatypes(dsid):
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        if not valid_dsid(dsid, cursor):
            return JsonResponse(
                    {'error_message': f"'{dsid}' is not a valid dataset "
                                      "identifier."},
                    status=400)

        services = service_list(dsid)
        if len(services) == 0:
            return JsonResponse(
                    {'error_message': "API file discovery is not available "
                                      "for this dataset."},
                    status=400)

        response = {'dsid': dsid,
                    'datatypes': [datatypes_map[e] for e in services]}
        return JsonResponse(response)
    except Exception as err:
        # log the error in the Apache error log
        print(f"FILESEARCH API SERVER ERROR: datatypes(): '{err}'")
        return JsonResponse({'error_message': "Server error."}, status=500)
    finally:
        if 'conn' in locals():
            conn.close()


def parse_grid_filters_request(request, dsid, cursor):
    try:
        if 'parameters' in request.GET and len(request.GET['parameters']) > 0:
            request_parameters = (
                    [part for e in request.GET.getlist('parameters') for part
                     in e.split(",")])

        if 'products' in request.GET and len(request.GET['products']) > 0:
            request_products = (
                    [part for e in request.GET.getlist('products') for part in
                     e.split(",")])

        if 'grids' in request.GET and len(request.GET['grids']) > 0:
            request_grids = (
                    [part for e in request.GET.getlist('grids') for part in
                     e.split(",")])

        if 'levels' in request.GET and len(request.GET['levels']) > 0:
            request_levels = (
                    [part for e in request.GET.getlist('levels') for part in
                     e.split(",")])

        restrictions = {'valid_datetime_min': 999999999999,
                        'valid_datetime_max': 0,
                        'parameters': [],
                        'products': [],
                        'grids': [],
                        'levels': []}
        filters = copy.deepcopy(restrictions)
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
        if ('valid_datetime_min' in request.GET and
                len(request.GET['valid_datetime_min']) > 0):
            if not re.fullmatch(grid_date_re,
                                request.GET['valid_datetime_min']):
                return ({}, {}, "Invalid format for 'valid_datetime_min'", 400)

            restrictions['valid_datetime_min'] = (
                    request.GET['valid_datetime_min'])
            query += " and s.end_date >= %s"
            qparams.append(int(request.GET['valid_datetime_min']
                               .replace("-", "").replace(":", "")
                               .replace(" ", "")))
            del filters['valid_datetime_min']
        else:
            del restrictions['valid_datetime_min']

        if ('valid_datetime_max' in request.GET and
                len(request.GET['valid_datetime_max']) > 0):
            if not re.fullmatch(grid_date_re,
                                request.GET['valid_datetime_max']):
                return ({}, {}, "Invalid format for 'valid_datetime_max'", 400)

            restrictions['valid_datetime_max'] = (
                    request.GET['valid_datetime_max'])
            query += " and s.start_date <= %s"
            qparams.append(int(request.GET['valid_datetime_max']
                               .replace("-", "").replace(":", "")
                               .replace(" ", "")))
            del filters['valid_datetime_max']
        else:
            del restrictions['valid_datetime_max']

        if 'request_parameters' in locals():
            query += " and concat(s.format_code, '!', s.parameter) in %s"
            qparams.append(tuple(request_parameters))
            del filters['parameters']
        else:
            del restrictions['parameters']

        if 'request_products' in locals():
            query += " and s.time_range_code in %s"
            qparams.append(tuple([int(e) for e in request_products]))
            del filters['products']
        else:
            del restrictions['products']

        if 'request_grids' in locals():
            query += " and s.grid_definition_code in %s"
            qparams.append(tuple([int(e) for e in request_grids]))
            del filters['grids']
        else:
            del restrictions['grids']

        if 'request_levels' in locals():
            lvals = [int(e) for e in request_levels]
            query += (" and cast((string_to_array(level_type_codes, ':'))[1] "
                      "as integer) <= %s")
            qparams.append(max(lvals))
            del filters['levels']
        else:
            del restrictions['levels']

        cursor.execute(query, tuple(qparams))
        res = cursor.fetchall()
        if len(res) == 0:
            if len(request.GET) > 0:
                err = ("No filters were identified. Perhaps an invalid query "
                       "parameter was specified. See the "
                       f"'/api/datasets/{dsid}/filesearch/filters/grid' "
                       "endpoint for valid parameter values for this dataset.")
                return ({}, {}, err, 400)

            err = ("API file discovery is not available for data type "
                   "'grid'. See the "
                   f"'/api/datasets/{dsid}/filesearch/datatypes' endpoint "
                   "for the valid data types for this dataset.")
            return ({}, {}, err, 400)

        param_set = set()
        param_names = {}
        param_maps = {}
        tr_set = set()
        gd_set = set()
        lbmp_set = set()
        lev_fmts = {}
        for e in res:
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
                if 'request_products' in locals():
                    restrictions['products'].append(
                            {'name': e[2], 'code': str(e[1])})
                else:
                    filters['products'].append(
                            {'name': e[2], 'code': str(e[1])})

            if e[3] not in gd_set:
                gd_set.add(e[3])
                grid_name = convert_grid_definition(e[4].split("!"),
                                                    output="text")
                if 'request_grids' in locals():
                    restrictions['grids'].append(
                            {'name': grid_name, 'code': str(e[3])})
                else:
                    filters['grids'].append(
                            {'name': grid_name, 'code': str(e[3])})

            if e[5] not in lbmp_set:
                lbmp_set.add(e[5])
                vals = uncompress_bitmap_values(e[5])
                for val in vals:
                    if (val not in lev_fmts.keys() and
                            ('lvals' not in locals() or val in lvals)):
                        lev_fmts[val] = e[6]

            if 'valid_datetime_min' in filters:
                filters['valid_datetime_min'] = (
                        min(e[7], filters['valid_datetime_min']))

            if 'valid_datetime_max' in filters:
                filters['valid_datetime_max'] = (
                        max(e[8], filters['valid_datetime_max']))

        param_list = [{'name': name, 'code': code} for name, code in
                      param_names.items()]
        if 'request_parameters' in locals():
            restrictions['parameters'] = param_list
        else:
            filters['parameters'] = param_list

        lev_codes = [k for k in lev_fmts.keys()]
        if len(lev_codes) == 1:
            lev_codes.append(lev_codes[0])

        cursor.execute(
                'select distinct map, type, value, code from "WGrML".'
                "levels where code in %s", (tuple(lev_codes), ))
        res = cursor.fetchall()
        level_maps = {}
        for e in res:
            lev_name = decode_level(lev_fmts[e[3]], *e[0:3], level_maps)
            if 'request_levels' in locals():
                restrictions['levels'].append(
                        {'name': lev_name, 'code': str(e[3])})
            else:
                filters['levels'].append(
                        {'name': lev_name, 'code': str(e[3])})

        if 'valid_datetime_min' in filters:
            s = str(filters['valid_datetime_min'])
            filters['valid_datetime_min'] = (
                    f"{s[0:4]}-{s[4:6]}-{s[6:8]} {s[8:10]}:{s[10:12]}")

        if 'valid_datetime_max' in filters:
            s = str(filters['valid_datetime_max'])
            filters['valid_datetime_max'] = (
                    f"{s[0:4]}-{s[4:6]}-{s[6:8]} {s[8:10]}:{s[10:12]}")

        return (restrictions, filters, "", 200)
    except Exception as err:
        print("DSFILES API SERVER ERROR: parse_grid_filters_request(): "
              f"'{err}'")
        return ({}, {}, "Server error.", 500)


def filters(request, dsid, datatype):
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        if not valid_dsid(dsid, cursor):
            return JsonResponse(
                    {'error_message': f"'{dsid}' is not a valid dataset "
                                      "identifier."},
                    status=400)

        response = {'dsid': dsid}
        if datatype == "cyclone_fix":
            return JsonResponse({'error_message': "Not yet implemented."},
                                status=500)

        if datatype == "grid":
            restrictions, filters, err, status = (
                    parse_grid_filters_request(request, dsid, cursor))
            if len(err) > 0:
                return JsonResponse({'error_message': err}, status=status)

            if len(restrictions) > 0:
                response['restrictions'] = restrictions

            response['filters'] = filters
            return JsonResponse(response)

        if datatype == "sensor":
            return JsonResponse({'error_message': "Not yet implemented."},
                                status=500)

        msg = ("API file discovery is not available for data type "
               f"'{datatype}'. See the "
               f"'/api/datasets/{dsid}/filesearch/datatypes/' endpoint for "
               "the valid data types for this dataset.")
        return JsonResponse({'error_message': msg}, status=400)
    except Exception as err:
        # log the error in the Apache error log
        print(f"FILESEARCH API SERVER ERROR: filters(dsid={dsid}, "
              f"datatype={datatype}): '{err}'")
        return JsonResponse({'error_message': "Server error."}, status=500)
    finally:
        if 'conn' in locals():
            conn.close()


def files(request, dsid, datatype):
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        files_response['dsid'] = dsid
        files_response['datatype'] = datatype
        services = service_list(dsid)
        if datatype == "grid" and "GrML" in services:
            grml_req = HttpRequest()
            grml_req.method = "POST"
            grml_req.POST = QueryDict(mutable=True)
            grml_req.POST.setlist('parameter',
                                  request.GET.getlist('parameters'))
            if 'valid_datetime_min' in request.GET:
                if not re.fullmatch(grid_date_re,
                                    request.GET['valid_datetime_min']):
                    return JsonResponse(
                            {'error_message':
                             "Invalid format for 'valid_datetime_min'"},
                            status=400)

                files_response['restrictions']['valid_datetime_min'] = (
                        request.GET['valid_datetime_min'])
                parts = request.GET['valid_datetime_min'].split()
                grml_req.POST['startDate'] = parts[0]
                grml_req.POST['startTime'] = parts[1]
            else:
                grml_req.POST['startDate'] = "1000-01-01"
                grml_req.POST['startTime'] = "00:00"

            if 'valid_datetime_max' in request.GET:
                if not re.fullmatch(grid_date_re,
                                    request.GET['valid_datetime_max']):
                    return JsonResponse(
                            {'error_message':
                             "Invalid format for 'valid_datetime_max'"},
                            status=400)

                files_response['restrictions']['valid_datetime_max'] = (
                        request.GET['valid_datetime_max'])
                parts = request.GET['valid_datetime_max'].split()
                grml_req.POST['endDate'] = parts[0]
                grml_req.POST['endTime'] = parts[1]
            else:
                grml_req.POST['endDate'] = ""
                grml_req.POST['endTime'] = ""

            files_response['restrictions']['parameters'] = (
                    request.GET.getlist('parameters'))
            kwargs = {}
            if 'products' in request.GET:
                kwargs['pcodes'] = (
                        [part for e in request.GET.getlist('products') for part
                         in e.split(",")])
                files_response['restrictions']['products'] = (
                        request.GET.getlist('products'))

            if 'grids' in request.GET:
                kwargs['gcodes'] = (
                        [part for e in request.GET.getlist('grids') for part in
                         e.split(",")])
                files_response['restrictions']['grids'] = (
                        request.GET.getlist('grids'))

            if 'levels' in request.GET:
                kwargs['lcodes'] = (
                        [int(part) for e in request.GET.getlist('levels') for
                         part in e.split(",")])
                files_response['restrictions']['levels'] = (
                        request.GET.getlist('levels'))

            grml = parse_grml_query(cursor, dsid, "weblist", grml_req,
                                    **kwargs)
            file_codes = grml['fcodes']

        if 'file_codes' in locals():
            files_response['pagination']['total_count'] = len(file_codes)
            files_response['pagination']['num_pages'] = (
                    files_response['pagination']['total_count'] // PAGE_SIZE
                    + 1)
            files_response['pagination']['num_per_page'] = (
                    min(files_response['pagination']['total_count'],
                        PAGE_SIZE))
            if files_response['pagination']['total_count'] <= PAGE_SIZE:
                files_response['pagination']['current_page'] = 1
                files_response['pagination']['next_page'] = None
                files_response['pagination']['result_id'] = None
                cursor.execute(
                        f'select id from "WGrML".{dsid}_webfiles2 where code '
                        "in %s order by id", (tuple(grml['fcodes']), ))
            else:
                files_response['pagination']['result_id'] = strand(20)
                now = datetime.now(pytz.utc)
                expires = ((datetime.now(pytz.utc) + timedelta(hours=3))
                           .replace(tzinfo=tz.tzutc())
                           .strftime("%Y-%m-%d %H:%M:%S"))
                cursor.execute(
                        "insert into metautil.dsfiles_api_result_ids values "
                        "(%s, %s, %s, %s, %s)",
                        (files_response['pagination']['result_id'],
                         expires, len(file_codes), datatype, dsid))
                rows = (list(
                        zip([files_response['pagination']['result_id'] for x in
                             range(0, len(file_codes))], file_codes)))
                for x in range(0, len(rows), 10000):
                    rowins = ", ".join([str(t) for t in rows[x:x+10000]])
                    cursor.execute(
                            "insert into metautil.dsfiles_api_file_codes "
                            f"values {rowins}")

                conn.commit()
                files_response['pagination']['current_page'] = 1
                files_response['pagination']['next_page'] = 2
                cursor.execute(
                        "select w.id from metautil.dsfiles_api_file_codes as "
                        f'f left join "WGrML".{dsid}_webfiles2 as w on w.code '
                        "= f.file_code where f.result_id = %s order by w.id "
                        f"limit {PAGE_SIZE} offset 0",
                        (files_response['pagination']['result_id'], ))

            files_response['files']['paths'] = (
                    [e[0] for e in cursor.fetchall()])
            return JsonResponse(files_response, status=200)

        return JsonResponse(
                {'error_message': (
                        "API file discovery is not available for data type "
                        f"'{datatype}'. See the "
                        "'/api/datasets/{dsid}/filesearch/datatypes/' "
                        "endpoint for the valid data types for this "
                        "dataset.")},
                status=400)
    except Exception as err:
        # log the error in the Apache error log
        print(f"FILESEARCH API SERVER ERROR: files(dsid={dsid}, "
              f"datatype={datatype}): '{err}'")
        return JsonResponse({'error_message': "Server error."}, status=500)
    finally:
        if 'conn' in locals():
            conn.close()


def respond_to_request(request, dsid, operation, datatype=None):
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
            return filters(request, dsid, datatype, cursor)
        elif operation == "files":
            cursor.execute((
                    "select result_id from metautil.dsfiles_api_result_ids "
                    "where expiration < %s"), (datetime.now(), ))
            res = cursor.fetchall()
            for e in res:
                cursor.execute((
                        "delete from metautil.dsfiles_api_file_codes where "
                        "result_id = %s"), (e[0], ))
                cursor.execute((
                        "delete from metautil.dsfiles_api_result_ids where "
                        "result_id = %s"), (e[0], ))
                conn.commit()

            return files(request, dsid, datatype, conn)
        else:
            return JsonResponse(
                    {'error_message': f"'{operation}' is not a valid "
                                      "operation."},
                    status=400)

    except Exception as err:
        print(f"DSFILES API SERVER ERROR: respond_to_request(): '{err}'")
        return JsonResponse({'error_message': "Server error."}, status=500)
    finally:
        if 'conn' in locals():
            conn.close()


def serve_result_set(request, dsid, result_id, page_num):
    if len(result_id) != 20:
        return JsonResponse(
                    {'error_message': "Invalid 'result_id' - must be 20 "
                                      "characters."}, status=400)

    if page_num <= 0:
        return JsonResponse(
                    {'error_message': "Page numbers must be positive integers "
                                      "beginning at '1'."}, status=400)

    try:
        files_response['dsid'] = dsid
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute(
                "select total_count, datatype from metautil."
                "dsfiles_api_result_ids where dsid = %s", (dsid, ))
        total_count, datatype = cursor.fetchone() or (None, None)
        if total_count is None:
            return JsonResponse(
                        {'error_message': "Invalid or expired 'result_id'."},
                        status=400)

        files_response['datatype'] = datatype
        files_response['pagination']['result_id'] = result_id
        files_response['pagination']['total_count'] = total_count
        files_response['pagination']['num_pages'] = (
                files_response['pagination']['total_count'] // PAGE_SIZE + 1)
        service = (
                {value: key for key, value in datatypes_map.items()}[datatype])
        offset = (page_num - 1) * PAGE_SIZE
        cursor.execute(
                "select w.id from metautil.dsfiles_api_file_codes as f left "
                f'join "W{service}".{dsid}_webfiles2 as w on w.code = f.'
                "file_code where f.result_id = %s order by w.id limit "
                f"{PAGE_SIZE} offset {offset}", (result_id, ))
        res = cursor.fetchall()
        files_response['files']['paths'] = [e[0] for e in res]
        files_response['pagination']['num_per_page'] = min(len(res), PAGE_SIZE)
        files_response['pagination']['current_page'] = offset // PAGE_SIZE + 1
        if len(res) == PAGE_SIZE:
            files_response['pagination']['next_page'] = (
                    files_response['pagination']['current_page'] + 1)
        else:
            files_response['pagination']['next_page'] = None

        return JsonResponse(files_response, status=200)
    except Exception as err:
        print(f"DSFILES API SERVER ERROR: serve_result_set(): '{err}'")
        return JsonResponse({'error_message': "Server error."}, status=500)
    finally:
        if 'conn' in locals():
            conn.close()
