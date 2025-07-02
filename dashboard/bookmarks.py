import psycopg2

from datetime import datetime

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render

from .utils import get_duser


def get_bookmarks(request):
    if "HTTP_X_REQUESTED_WITH" not in request.META:
        return render(request, "404.html")

    duser = get_duser(request)
    if duser is None:
        return render(request, "dashboard/bookmarks.html",
                      {'error': "You are not signed in."})

    try:
        conn = psycopg2.connect(**settings.RDADB['dssdb_config_pg'])
        cursor = conn.cursor()
        cursor.execute((
                "select f.dsid, s.title from dssdb.dsbookmarks as f left join "
                "search.datasets as s on s.dsid = f.dsid where f.email in ("
                "select j.email from dssdb.ruser as r left join dssdb.ruser "
                "as j on j.id = r.id where r.email ilike %s) order by f.dsid"),
                (duser, ))
        res = cursor.fetchall()
        ctx = {'bookmarks': []}
        for e in res:
            ctx['bookmarks'].append({'dsid': e[0], 'dstitle': e[1]})

        ctx['update_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        return render(request, "dashboard/bookmarks.html", ctx)
    except psycopg2.Error:
        return render(request, "dashboard/bookmarks.html",
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
        conn = psycopg2.connect(**settings.RDADB['dssdb_config_pg'])
        cursor = conn.cursor()
        cursor.execute((
                "select count(dsid) from dssdb.dsbookmarks where email ilike "
                "%s"), (duser, ))
        res = cursor.fetchone()
        res = str(res[0]) if res[0] > 0 else "no"
        return HttpResponse(res)
    except psycopg2.Error:
        return HttpResponse("???")
    finally:
        conn.close()


def do_delete(request, dsid):
    if "HTTP_X_REQUESTED_WITH" not in request.META:
        return render(request, "404.html")

    duser = get_duser(request)
    if duser is None:
        return HttpResponse("missing duser")

    try:
        conn = psycopg2.connect(**settings.RDADB['dssdb_config_pg'])
        cursor = conn.cursor()
        cursor.execute((
                "delete from dssdb.dsbookmarks where email ilike %s and dsid "
                "= %s"), (duser, dsid))
        conn.commit()
    except psycopg2.Error as err:
        return HttpResponse(str(err))
    finally:
        conn.close()

    return HttpResponse("")
