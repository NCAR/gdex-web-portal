import psycopg2

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render

from .utils import get_duser


def get_aggregations(request):
    if "HTTP_X_REQUESTED_WITH" not in request.META:
        return render(request, "404.html")

    duser = get_duser(request)
    if duser is None:
        return render(request, "dashboard/aggregations.html",
                      {'error': "You are not signed in."})

    try:
        conn = psycopg2.connect(**settings.RDADB['dssdb_config_pg'])
        cursor = conn.cursor()
        cursor.execute((
                "select d.id, d.rinfo, d.date, s.title from metautil."
                "custom_dap as d left join search.datasets as s on s.dsid = "
                "substr(d.rinfo, locate('dsnum=', d.rinfo)+6, 5) where duser "
                "= %s order by d.date"), (duser, ))
        res = cursor.fetchall()
        ctx = {'aggregations': []}
        for e in res:
            pass

        ctx['update_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        return render(request, "dashboard/aggregations.html", ctx)
    except psycopg2.Error:
        return render(request, "dashboard/aggregations.html",
                      {'error': (
                              "There was a database error. Please try again "
                              "later.")})
    finally:
        conn.close()


def get_count(request):
    if "HTTP_X_REQUESTED_WITH" not in request.META:
        return render(request, "404.html")

    duser = get_duser(request)
    if duser is None:
        return HttpResponse("no")

    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute(
                "select count(*) from metautil.custom_dap where duser = %s",
                (duser, ))
        res = cursor.fetchone()
        res = str(res[0]) if res[0] > 0 else "no"
        return HttpResponse(res)
    except psycopg2.Error:
        return HttpResponse("???")
    finally:
        conn.close()
