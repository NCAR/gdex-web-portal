import psycopg2

from django.conf import settings as django_settings
from django.shortcuts import render


def resolve(request, doi):
    try:
        conn = psycopg2.connect(**django_settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
    except Exception as err:
        return render(request, "doi/doi_page.html", {'error': str(err)})
    finally:
        if 'conn' in locals():
            conn.close()

    return render(request, "doi/doi_page.html")
