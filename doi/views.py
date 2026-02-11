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

        if res[1] == "A":
            return redirect("/datasets/{dsid}/".format(dsid=res[0]))

    except Exception as err:
        return render(request, "doi/doi_page.html", {'error': str(err)})
    finally:
        if 'conn' in locals():
            conn.close()

    return render(request, "doi/doi_page.html")
