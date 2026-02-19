import psycopg2

from django.conf import settings as django_settings
from django.shortcuts import render, redirect


def resolve(request, doi):
    try:
        conn = psycopg2.connect(**django_settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute((
                "select dsid, status from dsvrsn where doi ilike %s order by "
                "status"), (doi, ))
        res = cursor.fetchone()
        if res is None:
            return render(request, "doi/doi_page.html",
                          {'doi': doi, 'not_gdex': True})

        dsid, status = res
        if status == "A":
            return redirect("/datasets/{dsid}/".format(dsid=dsid))

        if status == "H":
            cursor.execute((
                    "select doi from dssdb.dsvrsn where dsid = %s and status "
                    "= 'A'"), (dsid, ))
            res = cursor.fetchall()
            if len(res) == 0:
                return render(request, "doi/doi_page.html",
                              {'doi': doi, 'terminated': True})

            if len(res) > 1:
                return render(request, "doi/doi_page.html", {'error': True})

        return render(request, "doi/doi_page.html",
                      {'doi': doi, 'dsid': dsid, 'superseded': True})
    except Exception:
        return render(request, "doi/doi_page.html", {'error': True})
    finally:
        if 'conn' in locals():
            conn.close()
