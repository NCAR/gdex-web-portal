import psycopg2

from functools import cmp_to_key

from django.conf import settings
from django.shortcuts import render
from libpkg.metacompares import compare_time_ranges
from libpkg.strutils import snake_to_capital

from . import views


def transform_grml(request, dsid, markup_type, file, ctx):
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute(
                f'select f.format, w.code from "{markup_type}".{dsid}'
                f'_webfiles2 as w left join "{markup_type}".formats as f on f.'
                "code = w.format_code where w.id = %s", (file, ))
        data_format, file_code = cursor.fetchone() or (None, None)
        if file_code is not None:
            ctx['transform']['data_format'] = snake_to_capital(data_format)
            cursor.execute(
                    f'select distinct t.time_range from "{markup_type}".'
                    f'{dsid}_grids2 as g left join "{markup_type}".'
                    'time_ranges as t on t.code = g.time_range_code where '
                    'file_code = %s', (file_code, ))
            res = cursor.fetchall()
            products = [e[0] for e in res]
            ctx['transform']['products'] = (
                    sorted(products, key=cmp_to_key(compare_time_ranges)))
        else:
            ctx['transform']['error'] = "File does not exist"

    except Exception:
        ctx['transform']['error'] = "Database error"
    finally:
        if 'conn' in locals():
            conn.close()

    return render(request, "datasets/transform/grml.html", ctx)


def transform(request, dsid, markup_type, file):
    d = views.get_dataset_description_context(dsid)
    ctx = {'page': d, 'transform': {'file': file}}
    if markup_type[-4:] == "GrML":
        return transform_grml(request, dsid, markup_type, file, ctx)

    return render(request, "404.html")
