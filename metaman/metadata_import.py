import gspread
import psycopg2
import re

from django.conf import settings
from django.shortcuts import render
from google.oauth2.service_account import Credentials

from .datasets import get_data_format_options
from .get_items import get_data_type_options
from .local_settings import gdex_metadata_form_id
from .utils import get_author_from_orcid_id


def do_metadata_responses_import(request, spec):
    ctx = {'spec': spec}
    if 'row_number' not in request.POST:
        return render(request, "metaman/datasets/import.html", ctx)

    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        creds = Credentials.from_service_account_file(
                "/data/local/gdexweb/metaman/gspread_creds.json",
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ])
        client = gspread.authorize(creds)
        parent = client.open_by_key(gdex_metadata_form_id)
        sheet = parent.worksheets()[0]
        values = sheet.row_values(request.POST['row_number'])
        ctx['title'] = values[2]
        ctx['summary'] = values[3]
        authors = values[5].split("\n")
        auth_list = []
        for author in authors:
            parts = author.replace(";", "").split(",")
            for part in parts:
                part = part.strip()
                if re.search(r"^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$", part):
                    t = get_author_from_orcid_id(part)
                    if type(t[0]) is not dict:
                        auth_list.append("[!]".join(t[1:4] + (t[0], )))

                    break

        ctx['authors'] = "\n".join(auth_list)
        keywords = values[6].replace(";", "").split("\n")
        ctx['variables'] = {'imported': [], 'not_imported': []}
        for keyword in keywords:
            keyword = keyword.strip()
            parts = keyword.split(">")
            parts[-1] = parts[-1].strip()
            cursor.execute(
                    "select path, uuid from search.gcmd_sciencekeywords where "
                    "last_in_path ilike %s", (parts[-1], ))
            res = cursor.fetchall()
            if len(res) > 0:
                for e in res:
                    ctx['variables']['imported'].append("[!]".join(e))

            elif len(keyword) > 0:
                ctx['variables']['not_imported'].append(keyword)

        ctx['variables']['imported'] = "\n".join(ctx['variables']['imported'])
        keywords = ctx['variables']['not_imported']
        ctx['instruments'] = {'imported': [], 'not_imported': []}
        for keyword in keywords:
            keyword = keyword.strip()
            parts = keyword.split(">")
            parts[-1] = parts[-1].strip()
            cursor.execute(
                    "select path, uuid from search.gcmd_instruments where "
                    "last_in_path ilike %s", (parts[-1], ))
            res = cursor.fetchall()
            if len(res) > 0:
                for e in res:
                    ctx['instruments']['imported'].append("[!]".join(e))

            elif len(keyword) > 0:
                ctx['instruments']['not_imported'].append(keyword)

        ctx['instruments']['imported'] = (
                "\n".join(ctx['instruments']['imported']))
        keywords = ctx['instruments']['not_imported']
        ctx['keywords_not_imported'] = "<br>".join(keywords)
        platforms = values[7].replace(";", "").split("\n")
        ctx['platforms'] = {'imported': [], 'not_imported': []}
        for platform in platforms:
            parts = platform.split(">")
            parts[-1] = parts[-1].strip()
            cursor.execute(
                    "select path, uuid from search.gcmd_platforms where "
                    "last_in_path ilike %s", (parts[-1], ))
            res = cursor.fetchall()
            if len(res) > 0:
                for e in res:
                    ctx['platforms']['imported'].append("[!]".join(e))

            else:
                ctx['platforms']['not_imported'].append(platform.strip())

        ctx['platforms']['imported'] = "\n".join(ctx['platforms']['imported'])
        ctx['platforms']['not_imported'] = (
                "<br>".join(ctx['platforms']['not_imported']))

        data_formats = {e['value'] for e in get_data_format_options()}
        formats = values[8].split(",")
        ctx['formats'] = {'imported': [], 'not_imported': []}
        for fmt in formats:
            fmt = fmt.strip()
            if fmt in data_formats:
                ctx['formats']['imported'].append(fmt)
            else:
                ctx['formats']['not_imported'].append(fmt)

        ctx['formats']['not_imported'] = (
                "<br>".join(ctx['formats']['not_imported']))
        data_types = {e['value'] for e in get_data_type_options()}
        dtypes = values[11].split(",")
        ctx['data_types'] = {'imported': [], 'not_imported': []}
        for dtype in dtypes:
            dtype = dtype.strip().replace(" ", "_").lower()
            if dtype in data_types:
                if dtype == "grid":
                    dtype += "[!]n/a"

                ctx['data_types']['imported'].append(dtype)
            else:
                ctx['data_types']['not_imported'].append(dtype)

        if ctx['data_types']['imported'] in ("elevation", "model_simulation"):
            ctx['temporal_periods'] = {'imported':
                                       "9999[!]9999[!]Entire Dataset"}

        ctx['data_types']['imported'] = (
                "\n".join(ctx['data_types']['imported']))
        ctx['data_types']['not_imported'] = (
                "<br>".join(ctx['data_types']['not_imported']))
        if 'temporal_periods' not in ctx:
            ctx['temporal_periods'] = {'imported': [], 'not_imported': []}
            periods = values[9].split("\n")
            for period in periods:
                idx = period.find(";")
                if idx > 0:
                    period = period[0:idx]

                parts = period.split("to")
                if len(parts) == 2:
                    ctx['temporal_periods']['imported'].append(
                            "[!]".join([parts[0].strip(), parts[1].strip(),
                                        "Entire Dataset"]))
                else:
                    ctx['temporal_periods']['not_imported'].append(period)

            ctx['temporal_periods']['imported'] = (
                    "\n".join(ctx['temporal_periods']['imported']))
            ctx['temporal_periods']['not_imported'] = (
                    "<br>".join(ctx['temporal_periods']['not_imported']))

        return render(request, "metaman/datasets/import.html", ctx)
    except Exception as err:
        return render(request, "metaman/datasets/import.html",
                      {'error': str(err)})
    finally:
        if 'conn' in locals():
            conn.close()


def do_import(request, spec):
    if spec == "metadata_responses":
        return do_metadata_responses_import(request, spec)

    return render(request, "metaman/datasets/import.html")
