import psycopg2

from django.conf import settings
from django.shortcuts import render
from libpkg.strutils import snake_to_capital

from .log import add_to_log
from .utils import cache_file


def parse_obml_query(cursor, dsid, listtyp, request):
    add_to_log("parse_obml_query: start obs check")
    opts = {
        'min_start': 99999999,
        'max_end': 00000000,
        'platforms': [],
        'data_types': [],
        'formats': [],
    }
    q = ("select distinct t.file_code, d.platform_type_code, w.start_date, "
         "w.end_date, d.data_type, w.format_code from \"WObML\"." + dsid +
         "_data_types as t left join \"WObML\"." + dsid + "_data_types_list "
         "as d on d.code = t.data_type_code left join \"WObML\"." + dsid +
         "_webfiles2 as w on w.code = t.file_code")
    wc = ["w.start_date <= %s", "w.end_date >= %s"]
    vars = [int(request.POST['endDate'].replace("-", "")),
            int(request.POST['startDate'].replace("-", ""))]
    if 'gindex' in request.POST:
        q += " left join dssdb.wfile_" + dsid + " as wf on wf.wfile = w.id"
        wc.append("wf.tindex = %s")
        vars.append(request.POST['gindex'])

    if 'platform_type' in request.POST:
        wc.append("d.platform_type_code = %s")
        vars.append(int(request.POST['platform_type']))

    if 'data_type' in request.POST:
        dtypes = []
        for item in request.POST.getlist('data_type'):
            dtypes.extend(item.split(","))

        wc.append("d.data_type in %s")
        vars.append(tuple(dtypes))

    if 'id' in request.POST or 'nlat' in request.POST:
        q += (" left join \"WObML\"." + dsid + "_id_list as l on l.file_code "
              "= w.code and l.platform_type_code = d.platform_type_code left "
              "join \"WObML\"." + dsid + "_ids as i on i.code = l.id_code")
        if 'id_match' in request.POST:
            if request.POST['id_match'] == "exact":
                wc.append("i.id = %s")
            elif request.POST['id_match'] == "partial":
                wc.append("i.id ilike %%%s%%")

            vars.append(request.POST['id'])
        else:
            wc.append(("i.sw_lat <= %s and i.ne_lat >= %s and i.sw_lon <= %s "
                       "and i.ne_lon >= %s"))
            vars.extend([int(request.POST['nlat']) * 10000,
                         int(request.POST['slat']) * 10000,
                         int(request.POST['elon']) * 10000,
                         int(request.POST['wlon']) * 10000])

    q += " where " + " and ".join(wc)
    cursor.execute(q, tuple(vars))
    add_to_log("parse_obml_query: " + cursor.query.decode("utf-8"))
    res = cursor.fetchall()
    fcodes = set([e[0] for e in res])
    opts['platforms'] = set([e[1] for e in res])
    opts['data_types'] = set([e[4] for e in res])
    opts['formats'] = list(set([e[5] for e in res]))
    for e in res:
        opts['min_start'] = min(e[2], opts['min_start'])
        opts['max_end'] = max(e[3], opts['max_end'])

    s = str(opts['min_start'])
    opts['min_start'] = "-".join([s[0:4], s[4:6], s[6:8]])
    s = str(opts['max_end'])
    opts['max_end'] = "-".join([s[0:4], s[4:6], s[6:8]])
    cursor.execute(("select code, platform_type from \"WObML\".platform_types "
                    "where code in %s"), (tuple(opts['platforms']), ))
    res = cursor.fetchall()
    opts['platforms'] = [(str(e[0]), snake_to_capital(e[1])) for e in res]
    cfile = cache_file(dsid, request.POST.get('gindex'), "ObML", listtyp)
    with open(cfile) as f:
        line = f.readline()
        line = f.readline()
        nlines = int(line)
        for n in range(nlines):
            line = f.readline()

        line = f.readline()
        if "<!>" not in line:
            nlines = int(line)
            dtypes = []
            for n in range(nlines):
                line = f.readline().strip()
                lst = line.split("<!>")
                parts = lst[0].split(",")
                for part in parts:
                    if part in opts['data_types']:
                        dtypes.append(line)

            dtypes = list(set(dtypes))
            opts['data_types'] = [tuple(e.split("<!>")) for e in dtypes]
            opts['data_types'].sort(key=lambda t: t[1])

    return {**opts, 'fcodes': fcodes}


def do_obml_query(request, dsid, listtyp):
    ctx = {'dsid': dsid, 'listtyp': listtyp, 'db': "WObML"}
    add_to_log("do_obml_query: " + str(request.POST) + " " + str(ctx))
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute((
                "select tablename from pg_tables where schemaname = %s and "
                "tablename = %s"), ("WObML", dsid + "_locations"))
        res = cursor.fetchone()
        if res is None:
            return render(request, "facbrowse/obml_query.html",
                          {'error': "This service does not exist."})

    except psycopg2.Error:
        return render(request, "facbrowse/obml_query.html",
                      {'error': "A database error occurred."})

    ctx['selected'] = {'platform_type': None, 'data_types': []}
    if 'platform_type' in request.POST:
        ctx['selected']['platform_type'] = request.POST['platform_type']

    if 'data_type' in request.POST:
        ctx['selected']['data_types'] = [x for x in request.POST.getlist(
                'data_type')]

    ctx.update(parse_obml_query(cursor, dsid, listtyp, request))
    conn.close()
    ctx.update({'gmap_api_url': settings.GMAP_API_URL,
                'gmap_api_key': settings.GMAP_API_KEY})
    log_ctx = ctx.copy()
    log_ctx['fcodes'] = str(len(ctx['fcodes']))
    add_to_log("do_obml_query: context = " + str(log_ctx))
    return render(request, "facbrowse/obml_query.html", ctx)
