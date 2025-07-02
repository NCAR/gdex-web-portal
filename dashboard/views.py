import psycopg2

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from wagtail.models import Page

from .models import DashboardPage
from .utils import get_duser

# Create your views here.


def dashboard(request):
    duser = get_duser(request)
    if duser is None:
        return render(request, "403.html")

    qs = Page.objects.type(DashboardPage).live().specific()
    if len(qs) == 0:
        return render(request, "404.html")

    ctx = qs[0].get_context(request)
    logname = duser[:duser.find("@")]
    try:
        conn = psycopg2.connect(**settings.RDADB['dssdb_config_pg'])
        cursor = conn.cursor()
        cursor.execute("select stat_flag from dssdb.dssgrp where logname = %s",
                       (logname, ))
        res = cursor.fetchone()
        if res is not None and res[0] == "C":
            ctx.update({'has_internal_access': True})

    except Exception:
        pass
    finally:
        conn.close()
    return render(request, "dashboard/dashboard_page.html", ctx)


def get_version(request):
    qs = Page.objects.type(DashboardPage).live().specific()
    if len(qs) == 0:
        return render(request, "404.html")

    return HttpResponse(qs[0].get_context(request)['page'].version)
