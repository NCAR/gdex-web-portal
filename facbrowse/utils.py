import os
import psycopg2

from lxml import etree as ElementTree
from pathlib import Path

from django.conf import settings
from django.shortcuts import render
from home.utils import slug_list
from libpkg.dbutils import uncompress_bitmap_values

rdadb_config = settings.RDADB['dssdb_config_pg']
metadata_db_config = settings.RDADB['metadata_config_pg']


def toomany_requests(request, dsid):
    conn = psycopg2.connect(**rdadb_config)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    duser = request.COOKIES['duser']
    duser = duser if ':' not in duser else duser[:duser.find(':')]
    cursor.execute((
            "select rindex, status, logname from dsrqst as r left join dssgrp "
            "as g on concat(g.logname, '@ucar.edu') = r.email where email = "
            "%s and dsid = %s and status != 'P' and coalesce(logname) is not "
            "null"), (duser, dsid))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result.__len__() >= 6


def service_list(dsid):
    services = []
    conn = psycopg2.connect(**metadata_db_config)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    ds_list = slug_list(dsid)
    for ds in ds_list:
        ds.replace(".", "")
        ds.replace("-", "")
        cursor.execute((
                "select table_schema, table_name from information_schema."
                "tables where table_name like '%{}_webfiles2'").format(ds))
        result = cursor.fetchall()
        if result is not None:
            for res in result:
                service = res[0]
                if service[0] == 'W':
                    service = service[1:]

                services.append(service)

    cursor.close()
    conn.close()
    return services


def get_presets(db, dsid):
    presets = []
    conn = psycopg2.connect(**metadata_db_config)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute((
            "select description, json_agg(parameter) as codes from \"{}\"."
            "parameter_presets where dsid in %s group by description order by "
            "description asc").format(db), (tuple(slug_list(dsid)), ))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    gen = (row for row in result if result is not None)
    for row in gen:
        presets.append({'description': row['description'],
                        'codes': row['codes']})

    return presets


def get_group_title(dsid, gindex):
    conn = psycopg2.connect(**rdadb_config)
    cursor = conn.cursor()
    cursor.execute((
            "select title from dssdb.dsgroup where dsid in %s and gindex = "
            "%s"), (tuple(slug_list(dsid)), gindex))
    res = cursor.fetchone()
    cursor.close()
    conn.close()
    if res is None:
        return ""

    return res[0]


def validate_request(request, listtyp):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, '404.html')

    if (listtyp not in ["weblist", "gladelist"] and 'duser' not in
            request.COOKIES):
        return render(request, '403.html')

    return None


def has_continuing_updates(dsid):
    try:
        tree = (ElementTree.parse("/data/web/datasets/" + dsid +
                "/metadata/dsOverview.xml"))
    except Exception:
        return (False, None)

    root = tree.getroot()
    e = root.find("./continuingUpdate")
    if e is None:
        return (False, None)

    update = e.get("value")
    if update == "yes":
        return (True, e.get("frequency"))

    return (False, None)


def get_groups(dsid):
    conn = psycopg2.connect(**rdadb_config)
    cursor = conn.cursor()
    cursor.execute((
            "select gindex, grpid, title from dsgroup where dsid = %s and "
            "pindex = 0 and dwebcnt > 0"), (dsid, ))
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    if res is None:
        return []

    groups = []
    for e in res:
        if e[2]:
            title = e[2]
        else:
            title = e[1]

        groups.append({'gindex': e[0], 'title': title})

    return groups


def list_type_from_request(request):
    idx = request.path.find("/facbrowse/")
    listtyp = request.path[idx + 11:]
    idx = listtyp.find("/")
    if idx > 0:
        listtyp = listtyp[0:idx]

    return listtyp


def cache_file(dsid, gindex, mu_type, listtyp):
    ds_list = slug_list(dsid)
    if listtyp == "subset":
        for ds in ds_list:
            path = ("/usr/local/www/server_root/web/datasets/" + ds +
                    "/metadata/customize.I" + mu_type)
            if gindex:
                path += "." + gindex

            if Path(path).is_file():
                return path

    elif listtyp == "weblist" or listtyp == "gladelist":
        for ds in ds_list:
            path = ("/usr/local/www/server_root/web/datasets/" + ds +
                    "/metadata/customize.W" + mu_type)
            if gindex:
                path += "." + gindex

            if Path(path).is_file():
                return path

    return ""


def update_parameter_aliases(dsid, parameters):
    with open(os.path.join(
            "/data/web/datasets", dsid, "metadata", "customize.WGrML"),
            "r") as f:
        lines = f.read().splitlines()

    if lines[0].find("curl_subset") == 0:
        del lines[0]

    del lines[0]
    for line in lines:
        parts = line.split("<!>")[0].split(",")
        if parts.__len__() > 1:
            for x in range(0, parts.__len__()):
                if parts[x] in parameters:
                    for part in parts:
                        if part not in parameters:
                            parameters.append(part)

    return parameters


def from_bitmaps(bitmap_list, delimiter, values):
    bmaps = bitmap_list.split(delimiter)
    for bmap in bmaps:
        for val in uncompress_bitmap_values(bmap):
            if val not in values:
                values.append(val)

    return values


def sort_products(t):
    if t[1][0:6] == "Analys":
        return "0"

    idx = t[1].find("-hour Forecast")
    if idx > 0:
        if t[1][0].isnumeric():
            return t[1][0:idx].rjust(4, "0") + "0"

    if t[1].find("(initial+") > 0 and t[1][-1] == ')':
        idx = t[1].rfind("+")
        key = t[1][idx+1:-1].rjust(4, "0")
        parts = t[1].split("-hour ")
        key += parts[1].split()[0] + parts[0].rjust(4, "0")
        return key

    return t[1]


def sort_levels(t):
    if t[1][-4:] == "mbar" or t[1][-3:] == "hPa":
        parts = t[1].split(": ")
        v = parts[1].split()
        if v[0].isnumeric():
            return parts[0] + ": " + str(2000 - int(v[0])) + " ".join(v[1:])

    if t[1].find("Potential vorticity") == 0:
        parts = t[1].split(": ")
        v = parts[1].split()
        return (parts[0] + ": " + str(int(v[0]) + 10000).rjust(5, "0") +
                " ".join(v[1:]))

    return t[1]


def sort_grids(t):
    idx = t[1].find("&deg;")
    if idx > 0:
        return float(t[1][0:idx])

    return 1000.
