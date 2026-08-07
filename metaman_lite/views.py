import psycopg2

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from metaman.datasets import add as add_dataset
from metaman.datasets import create as create_dataset
from metaman.datasets import edit as edit_dataset
from metaman.models import MetamanPage
from wagtail.models import Page


def start(request, token):
    qs = Page.objects.type(MetamanPage).live().specific()
    if token is None:
        return render(request, "metaman_lite/start_page.html",
                      {'title': qs[0].title})

    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute(
                "select token, dsid from metautil.metaman_lite where token = "
                "%s", (token, ))
        token, dsid = cursor.fetchone() or (None, None)
        if token is None:
            return render(request, "metaman_lite/start.html",
                          {'title': qs[0].title, 'error': "invalid_token"})

        if dsid is None:
            dsid = add_dataset(request)
            if isinstance(dsid, HttpResponse):
                return dsid

            cursor.execute(
                    "update metautil.metaman_lite set dsid = %s where token = "
                    "%s", (dsid, token))
            conn.commit()
            dsid = create_dataset(request, dsid)
            if isinstance(dsid, HttpResponse):
                return dsid

        return edit_dataset(request, dsid)

    except Exception as err:
        return HttpResponse(f"Error: {err}")
    finally:
        if 'conn' in locals():
            conn.close()
