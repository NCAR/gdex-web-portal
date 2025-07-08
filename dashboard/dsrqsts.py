import math
import psycopg2

from datetime import datetime, timedelta

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render

from .utils import get_duser


vunits = ["B", "KB", "MB", "GB", "TB"]


def set_process_status(rindex, pid, fcount, cursor):
    if pid == "0":
        return "Queued for Processing"

    status = "Processing..."
    if fcount == 0:
        return status

    try:
        cursor.execute((
                "select count(rindex) from dssdb.wfrqst where rindex = %s and "
                "type = 'D'"), (rindex, ))
        count = cursor.fetchone()
        if count[0] > 0:
            status += " (" + str(math.floor(count[0] / fcount * 100.)) + "%)"

    except Exception:
        pass

    return status


def set_status(s):
    if s == "E":
        return "Error"
    elif s == "H":
        return "On Hold"
    elif s == "I":
        return "Interrupted"
    elif s == "O":
        return "Completed"
    elif s == "P":
        return "Purged"
    elif s == "W":
        return "Approval Pending"

    return ""


def get_dsrqsts(request):
    if "HTTP_X_REQUESTED_WITH" not in request.META:
        return render(request, "404.html")

    duser = get_duser(request)
    if duser is None:
        return render(request, "dashboard/dsrqsts.html",
                      {'error': "You are not signed in."})

    try:
        conn = psycopg2.connect(**settings.RDADB['dssdb_config_pg'])
        cursor = conn.cursor()
        cursor.execute((
                "select r.rindex, r.rqstid, r.dsid, r.status, r.pid, r."
                "size_request, r.fcount, r.date_purge, r.location, r."
                "specialist, r.date_purge + interval '1 day' date_min, "
                "current_date + interval '14 day' date_max from dssdb.dsrqst "
                "as r where r.email in (select distinct j.email from (select "
                "id from dssdb.ruser where email = %s) as r left join dssdb."
                "ruser as j on j.id = r.id) order by r.rindex"), (duser, ))
        res = cursor.fetchall()
        ctx = {'dsrqsts': []}
        for e in res:
            if e[3] == "Q":
                status = set_process_status(e[0], e[4], e[6], cursor)
            else:
                status = set_status(e[3])

            volume = e[5]
            vidx = 0
            while vidx < 4 and (volume / 1000.) >= 1.:
                volume /= 1000.
                vidx += 1

            volume = round(volume, 2)
            date_purge = e[7]
            if date_purge is not None:
                date_purge = date_purge.strftime("%Y-%m-%d")

            date_min = e[10]
            if date_min is not None:
                date_min = date_min.strftime("%Y-%m-%d")

            date_max = e[11]
            if date_max is not None:
                date_max = date_max.strftime("%Y-%m-%d")

            ctx['dsrqsts'].append({'id': e[0], 'dsid': e[2], 'status': status,
                                   'volume': " ".join([str(volume),
                                                       vunits[vidx]]),
                                   'nfiles': 0, 'date_purge': date_purge,
                                   'specialist': e[9], 'date_min': date_min,
                                   'date_max': date_max})
            if ctx['dsrqsts'][-1]['status'] == "Completed":
                ctx['dsrqsts'][-1].update({'rqstid': e[1]})

            cursor.execute((
                    "select count(rindex) from dssdb.wfrqst where rindex = %s "
                    "and type = 'D'"), (e[0], ))
            count = cursor.fetchone()
            ctx['dsrqsts'][-1]['nfiles'] = count[0]

        ctx['update_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        return render(request, "dashboard/dsrqsts.html", ctx)
    except psycopg2.Error:
        return render(request, "dashboard/dsrqsts.html",
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
                "select count(rindex) from dssdb.dsrqst where email in ("
                "select distinct j.email from (select id from dssdb.ruser "
                "where email ilike %s) as r left join dssdb.ruser as j on j."
                "id = r.id) and status != 'P'"), (duser, ))
        res = cursor.fetchone()
        res = str(res[0]) if res[0] > 0 else "no"
        return HttpResponse(res)
    except psycopg2.Error:
        return HttpResponse("???")
    finally:
        conn.close()


def extend(request):
    if "HTTP_X_REQUESTED_WITH" not in request.META:
        return render(request, "404.html")

    duser = get_duser(request)
    if duser is None:
        return HttpResponse("You are not signed in.")

    if ('id' not in request.POST or 'date' not in request.POST or 'min_date'
            not in request.POST):
        return HttpResponse("Bad request.")

    max_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    if request.POST['date'] > max_date:
        return HttpResponse((
                "You can't request a date farther out than two weeks from "
                "today"))

    if request.POST['date'] < request.POST['min_date']:
        return HttpResponse((
                "You can't set a date earlier than " +
                request.POST['min_date']))

    try:
        conn = psycopg2.connect(**settings.RDADB['dssdb_config_pg'])
        cursor = conn.cursor()
        cursor.execute(
                "update dssdb.dsrqst set date_purge = %s where rindex = %s",
                (request.POST['date'], request.POST['id']))
        conn.commit()
    except Exception:
        return HttpResponse(
                "There was a database error. Please try again later.")
    finally:
        conn.close()

    return HttpResponse((
            "<p>Your extension was successfully processed.</p><img src=\""
            "/images/transpace.gif\" class=\"w-auto h-auto\" onload=\""
            "getAjaxContent('GET', null, 'requests/', 'requests')\">"))
