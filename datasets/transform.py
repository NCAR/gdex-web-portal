import psycopg2

from django.conf import settings
from django.shortcuts import render
from libpkg.strutils import snake_to_capital

from . import views


def transform_grml(request, dsid, markup_type, file, ctx):
    grml = {}
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute(
                f'select f.format, w.code from "{markup_type}".{dsid}'
                f'_webfiles2 as w left join "{markup_type}".formats as f on f.'
                "code = w.format_code where w.id = %s", (file, ))
        data_format, file_code = cursor.fetchone() or (None, None)
        if file_code is not None:
            grml['data_format'] = snake_to_capital(data_format)
            cursor.execute(
                    f'select distinct time_range_code from "{markup_type}".'
                    f'{dsid}_grids2 where file_code = %s', (file_code, ))
            res = cursor.fetchall()
            grml['num_products'] = len(res)
        else:
            grml['error'] = "File does not exist"
    except Exception:
        grml['error'] = "Database error"
    finally:
        if 'conn' in locals():
            conn.close()

    ctx.update({'transform': grml})
    return render(request, "datasets/transform/grml.html", ctx)


def transform(request, dsid, markup_type, file):
    d = views.get_dataset_description_context(dsid)
    ctx = {'page': d}
    if markup_type[-4:] == "GrML":
        return transform_grml(request, dsid, markup_type, file, ctx)

    return render(request, "404.html")
