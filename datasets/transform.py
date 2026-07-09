import os
import psycopg2

from functools import cmp_to_key
from lxml import etree

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from libpkg.dbutils import uncompress_bitmap_values
from libpkg.gridutils import convert_grid_definition
from libpkg.metacompares import compare_levels, compare_time_ranges
from libpkg.strutils import snake_to_capital

from . import views


def transform_grml(request, dsid, ctx):
    markup_type = ctx['transform']['markup_type']
    file = ctx['transform']['file']
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        data_format, file_code = file_data(file, dsid, markup_type, cursor)
        if file_code is not None:
            ctx['transform']['data_format'] = snake_to_capital(data_format)
            cursor.execute(
                    "select distinct t.time_range, concat(d.definition, '+', "
                    "d.def_params), g.level_type_codes, string_agg(parameter, "
                    "','), g.time_range_code, g.grid_definition_code from "
                    f'"{markup_type}".{dsid}_grids2 as g left join '
                    f'"{markup_type}".time_ranges as t on t.code = g.'
                    f'time_range_code left join "{markup_type}".'
                    "grid_definitions as d on d.code = g.grid_definition_code "
                    "where g.file_code = %s group by t.time_range, concat(d."
                    "definition, '+', d.def_params), g.level_type_codes, "
                    "g.time_range_code, g.grid_definition_code", (file_code, ))
            res = cursor.fetchall()
            tranges = [e[0] for e in res]
            s_tranges = sorted(tranges, key=cmp_to_key(compare_time_ranges))
            gdefs = {}
            prods = {}
            for t in s_tranges:
                prods[t] = {}
                for e in res:
                    if e[0] == t:
                        if e[1] not in gdefs:
                            gdefs[e[1]] = (
                                    convert_grid_definition(e[1].split("+")))

                        g = gdefs[e[1]]
                        if g not in prods[t]:
                            prods[t][g] = {'level_codes': [], 'parameters': [],
                                           'tr_code': e[4], 'gd_code': e[5]}

                        prods[t][g]['level_codes'].extend(
                                [code for code in
                                 uncompress_bitmap_values(e[2]) if code not in
                                 prods[t][g]['level_codes']])
                        prods[t][g]['parameters'].extend(
                                [param for param in e[3].split(",") if param
                                 not in prods[t][g]['parameters']])

            ctx['transform']['products'] = prods
        else:
            ctx['transform']['error'] = "File does not exist"

    except Exception:
        ctx['transform']['error'] = "Database error"
    finally:
        if 'conn' in locals():
            conn.close()

    return render(request, "datasets/transform/grml.html", ctx)


def transform_obml(request, dsid, ctx):
    markup_type = ctx['transform']['markup_type']
    file = ctx['transform']['file']
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        data_format, file_code = file_data(file, dsid, markup_type, cursor)
        if file_code is not None:
            ctx['transform']['data_format'] = snake_to_capital(data_format)
            cursor.execute(
                    "select o.obs_type, p.platform_type, l.data_type from "
                    f'"{markup_type}".{dsid}_data_types_list as l left join '
                    f'"{markup_type}".{dsid}_data_types as t on t.'
                    f'data_type_code = l.code left join "{markup_type}".'
                    "obs_types as o on o.code = l.observation_type_code left "
                    f'join "{markup_type}".platform_types as p on p.code = l.'
                    "platform_type_code where file_code = %s", (file_code, ))
            res = cursor.fetchall()
            ctx['obs_types'] = {}
            for e in res:
                obs_type = snake_to_capital(e[0])
                if obs_type not in ctx['obs_types']:
                    ctx['obs_types'][obs_type] = {'platforms': {}}

                platform_type = snake_to_capital(e[1])
                if platform_type not in ctx['obs_types'][obs_type]:
                    ctx['obs_types'][obs_type]['platforms'][platform_type] = (
                            {'data_types': [], 'num_obs': None,
                             'start_date': None, 'end_date': None, 'IDs': []})

                (ctx['obs_types'][obs_type]['platforms'][platform_type]
                    ['data_types']).append(e[2])

        else:
            ctx['transform']['error'] = "File does not exist"

    except Exception:
        ctx['transform']['error'] = "Database error"
    finally:
        if 'conn' in locals():
            conn.close()

    return render(request, "datasets/transform/obml.html", ctx)


def transform(request, dsid, markup_type, file):
    d = views.get_dataset_description_context(dsid)
    ctx = {'page': d, 'transform': {'markup_type': markup_type, 'file': file}}
    if markup_type[-4:] == "GrML":
        return transform_grml(request, dsid, ctx)
    elif markup_type[-4:] == "ObML":
        return transform_obml(request, dsid, ctx)

    return render(request, "404.html")


def grml_product_detail(request, dsid, markup_type, time_range_code,
                        grid_definition_code, file):
    ctx = {'detail': {}}
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute(
                f'select g.level_type_codes, g.parameter, cast(g.start_date '
                "as text), cast(g.end_date as text), g.nsteps, f.format from "
                f'"{markup_type}".{dsid}_grids2 as g left join '
                f'"{markup_type}".{dsid}_webfiles2 as w on w.code = g.'
                f'file_code left join "{markup_type}".formats as f on f.code '
                "= w.format_code where w.id = %s and g.time_range_code = %s "
                "and g.grid_definition_code = %s",
                (file, time_range_code, grid_definition_code))
        res = cursor.fetchall()
        parameter_maps = {}
        levels = {}
        for e in res:
            data_format = e[5]
            level_codes = uncompress_bitmap_values(e[0])
            for code in level_codes:
                if code not in levels:
                    levels[code] = []

                start = [e[2][0:4], "-", e[2][4:6], "-", e[2][6:8], " ",
                         e[2][8:10], ":", e[2][10:12], " +0000"]
                start = "".join(start)
                end = [e[3][0:4], "-", e[3][4:6], "-", e[3][6:8], " ",
                       e[3][8:10], ":", e[3][10:12], " +0000"]
                end = "".join(end)
                pmap, pcode = e[1].split(":")
                pmap_key = ".".join([e[5], pmap, "xml"])
                if pmap_key not in parameter_maps:
                    parameter_maps[pmap_key] = etree.parse(os.path.join(
                            "/data/web/metadata/ParameterTables", pmap_key)
                            ).getroot()

                pdesc = parameter_maps[pmap_key].find(
                        f"./parameter[@code='{pcode}']/description")
                pdesc = pdesc.text if pdesc is not None else e[1]
                levels[code].append({'name': pdesc,
                                     'datetime_range': " to ".join(
                                             [start, end]),
                                     'num_grids': e[4]})

        level_codes = [key for key, value in levels.items()]
        # make sure tuple has at least two entries by duplicating the first if
        #  necessary
        if len(level_codes) == 1:
            level_codes.append(level_codes[0])

        cursor.execute(
                f'select code, map, type, value from "{markup_type}".levels '
                f"where code in {tuple(level_codes)}")
        res = cursor.fetchall()
        level_maps = {}
        decoded_levels = {}
        for e in res:
            lmap_key = ".".join([data_format, e[1], "xml"])
            if lmap_key not in level_maps:
                level_maps[lmap_key] = etree.parse(os.path.join(
                        "/data/web/metadata/LevelTables", lmap_key)).getroot()

            types = e[2].split("-")
            if len(types) == 1:
                tree = level_maps[lmap_key].find(f"./level[@code='{e[2]}']")
                if tree is None:
                    tree = level_maps[lmap_key].find(
                            f"./layer[@code='{e[2]}']")

                if tree is None:
                    decoded_levels[e[0]] = e[0]
                else:
                    ldesc = tree.find("./description")
                    if ldesc is None:
                        decoded_levels[e[0]] = e[0]
                    else:
                        lunits = tree.find("./units")
                        if lunits is None or lunits.text is None:
                            if e[3] == "0":
                                ldesc = ldesc.text
                            else:
                                ldesc = "".join([ldesc.text, ": ", e[3]])

                        else:
                            ldesc = "".join([ldesc.text, ": ", e[3], " ",
                                             lunits.text])

                        decoded_levels[ldesc] = e[0]

            else:
                tree1 = level_maps[lmap_key].find(
                        f"./level[@code='{types[0]}']")
                tree2 = level_maps[lmap_key].find(
                        f"./level[@code='{types[1]}']")
                if tree1 is None or tree2 is None:
                    decoded_levels[e[0]] = e[0]
                else:
                    ldesc1 = tree1.find("./description")
                    ldesc2 = tree2.find("./description")
                    if ldesc1 is None or ldesc2 is None:
                        decoded_levels[e[0]] = e[0]
                    else:
                        values = e[3].split(",")
                        lunits1 = tree1.find("./units")
                        if lunits1 is not None:
                            values[0] = "".join([values[0], " ", lunits1.text])

                        lunits2 = tree2.find("./units")
                        if lunits2 is not None:
                            values[1] = "".join([values[1], " ", lunits2.text])

                        if ldesc1.text == ldesc2.text:
                            ldesc = "".join(["Layer between two '",
                                             ldesc1.text,
                                             "': ", values[0], ", ",
                                             values[1]])
                        else:
                            ldesc = "".join(["Layer between '", ldesc1.text,
                                             "': ", values[0], " and '",
                                             ldesc2.text, "': ", values[1]])

                        decoded_levels[ldesc] = e[0]

        l = [k for k, v in decoded_levels.items()]
        s_l = sorted(l, key=cmp_to_key(compare_levels))
        for lev in s_l:
            code = decoded_levels[lev]
            ctx['detail'].update({lev: levels[code]})

    except Exception:
        ctx['detail']['error'] = "Database error"
    finally:
        if 'conn' in locals():
            conn.close()

    return render(request, "datasets/transform/grml_product_detail.html", ctx)


def product_detail(request, dsid, markup_type, time_range_code,
                   grid_definition_code, file):
    if markup_type[-4:] == "GrML":
        return grml_product_detail(request, dsid, markup_type, time_range_code,
                                   grid_definition_code, file)

    return HttpResponse("Bad request.")


def file_data(file, dsid, markup_type, cursor):
    cursor.execute(
            f'select f.format, w.code from "{markup_type}".{dsid}_webfiles2 '
            f'as w left join "{markup_type}".formats as f on f.code = w.'
            "format_code where w.id = %s", (file, ))
    data_format, file_code = cursor.fetchone() or (None, None)
    return (data_format, file_code)
