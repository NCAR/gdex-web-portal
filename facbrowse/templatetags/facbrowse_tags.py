import math
import os
import psycopg2

from django import template
from django.conf import settings


register = template.Library()


@register.filter
def convert_file_bytes(bytes):
    units = ("bytes", "Kbytes", "Mbytes", "Gbytes", "Tbytes", "Pbytes")
    if bytes == 0:
        return "%s %s" % (bytes, units[0])

    idx = math.floor(math.log(bytes, 1000))
    div = int(math.pow(1000, idx))
    sval = round(bytes / div, 2)
    return "%s %s" % (sval, units[idx])


@register.filter
def file_data(codes, args):
    dsid, db = args.split(",")
    if db == "WGrML":
        type = "grids"
    elif db == "WObML":
        type = "observations"

    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute((
                "select w.id, f.format, w.num_" + type + " as units, w."
                "start_date, w.end_date, x.file_format, round((x.data_size / "
                "1000000.), 2) as data_size from \"" + db + "\"." + dsid +
                "_webfiles2 as w left join \"" + db + "\".formats as f on f."
                "code = w.format_code left join dssdb.wfile_" + dsid + " as x "
                "on x.wfile = w.id where w.code in %s order by w.start_date, "
                "w.end_date, w.id"), (tuple(codes), ))
        res = cursor.fetchall()
        conn.close()
        show_archive_format = False
        for e in res:
            if e['file_format'] is not None and len(e['file_format']) > 0:
                show_archive_format = True
                break

        return (res, show_archive_format)
    except Exception:
        return ([], None)


@register.filter
def date_time(value):
    value = str(value)
    if len(value) > 4:
        value = "-".join([value[0:4], value[4:]])
        if len(value) > 7:
            value = "-".join([value[0:7], value[7:]])
            if len(value) > 10:
                value = " ".join([value[0:10], value[10:]])
                if len(value) > 13:
                    value = ":".join([value[0:13], value[13:]])
                    if len(value) > 16:
                        value = ":".join([value[0:16], value[16:]])

    return value


@register.filter
def data_link(file_id, dsid):
    return os.path.join(settings.RDA_DATA_BASE_URL, dsid, file_id)


@register.filter
def basename(value):
    return os.path.basename(value)


@register.filter
def snake_to_capital(value):
    parts = value.split("_")
    if len(parts) == 1:
        parts = value.split()

    return " ".join([e[0:1].upper() + e[1:] for e in parts])


@register.filter
def pages(list_length, page_size):
    return [(x+1) for x in range(0,
                                 int((list_length + page_size) / page_size))]
