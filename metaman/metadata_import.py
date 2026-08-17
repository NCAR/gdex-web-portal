import gspread
import psycopg2
import re
import requests

from django.conf import settings
from django.shortcuts import render
from google.oauth2.service_account import Credentials
from lxml import etree

from .local_settings import gdex_metadata_form_id
from .utils import get_author_from_orcid_id


def do_gdex_import(request):
    ctx = {'spec': "gdex"}
    if 'gdex_path_base' not in request.POST:
        return render(request, "metaman/datasets/import.html", ctx)

    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        response = requests.get((
               "https://gdex.ucar.edu/dataset/" +
               request.POST['gdex_path_base'] + ".xml?type=iso19139"))
        root = etree.fromstring(response.content)
        title = root.xpath((
                "//gmd:identificationInfo/gmd:MD_DataIdentification/"
                "gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString"),
                namespaces=root.nsmap)[0].text
        if len(title) > 0:
            ctx['title'] = title

        summary = root.xpath((
                "//gmd:identificationInfo/gmd:MD_DataIdentification/"
                "gmd:abstract/gco:CharacterString"),
                namespaces=root.nsmap)[0].text
        if len(summary) > 0:
            ctx['summary'] = (
                    "<p>" + summary.replace("\n\n", "</p><nl><p>")
                    .replace("\n", "<br/>\n").replace("<nl>", "\n")
                    .replace("&amp;", "&") + "</p>")

        authors = root.xpath((
                "//gmd:identificationInfo/gmd:MD_DataIdentification/"
                "gmd:citation/gmd:CI_Citation/gmd:citedResponsibleParty/"
                "gmd:CI_ResponsibleParty/gmd:individualName"),
                namespaces=root.nsmap)
        auth_list = []
        orcid_id = None
        for author in authors:
            names = []
            a = author.xpath("gmx:Anchor", namespaces=root.nsmap)
            if len(a) > 0:
                names = a[0].text.split()
                orcid_id = a[0].get("{" + root.nsmap['xlink'] + "}href")
                idx = orcid_id.rfind("/")
                if idx > 0:
                    orcid_id = orcid_id[idx+1:]

            else:
                a = author.xpath("gco:CharacterString", namespaces=root.nsmap)
                if len(a) > 0:
                    names = a[0].text.split()

            if len(names) > 0:
                lidx = -1
                for x in range(0, len(names)):
                    if names[x][-1] == ',':
                        lidx = x
                        break

                if lidx >= 0:
                    for x in range(0, lidx+1):
                        names.append(names[0])
                        if names[-1][-1] == ',':
                            names[-1] = names[-1][0:-1]

                        del names[0]

                author = names[0] + "[!]"
                if names[1][-1] == '.':
                    author += names[1] + "[!]" + " ".join(names[2:])
                else:
                    author += "[!]" + " ".join(names[1:])

                author += "[!]"
                if orcid_id is not None:
                    author += orcid_id

                auth_list.append(author)

        if len(auth_list) > 0:
            ctx['authors'] = "\n".join(auth_list)

        keywords = root.xpath((
                "//gmd:identificationInfo/gmd:MD_DataIdentification/"
                "gmd:descriptiveKeywords/gmd:MD_Keywords/gmd:keyword/"
                "gco:CharacterString"), namespaces=root.nsmap)
        var_list = []
        for keyword in keywords:
            if keyword.text.find("EARTH SCIENCE >") == 0:
                cursor.execute((
                        "select uuid from search.gcmd_sciencekeywords where "
                        "path = %s"), (keyword.text, ))
                res = cursor.fetchone()
                if res is not None:
                    var_list.append(keyword.text + "[!]" + res[0])

        if len(var_list) > 0:
            ctx['variables'] = "\n".join(var_list)

        if request.POST['gdex_path_base'].lower()[0:17] == "icarus.experiment":
            ctx['ds_curation'] = "basic"
            ctx['ds_type'] = "primary"
            icarus_doi = root.xpath((
                    "//gmd:identificationInfo/gmd:MD_DataIdentification/"
                    "gmd:citation/gmd:CI_Citation/gmd:identifier/"
                    "gmd:MD_Identifier/gmd:code/"
                    "gmx:Anchor[@xlink:title='DOI']"),
                    namespaces=root.nsmap)
            if len(icarus_doi) > 0:
                ctx['icarus_doi'] = (icarus_doi[0].text.strip()
                                     .replace("https://doi.org/", ""))

            cursor.execute((
                    "select path, uuid from search.gcmd_platforms where path "
                    "like 'LABORATORY > %'"))
            res = cursor.fetchall()
            if len(res) > 0:
                ctx['platforms'] = "[!]".join(res[0][0:2])

            cursor.execute((
                    "select path, uuid from search.gcmd_projects where path "
                    "like 'ICARUS > %'"))
            res = cursor.fetchall()
            if len(res) > 0:
                ctx['projects'] = "[!]".join(res[0][0:2])

            ctx['iso_topic'] = "environment"
            ctx['data_type'] = "platform_observation"
            ctx['format'] = "proprietary_ASCII"

        temporal_starts = root.xpath((
                "//gmd:identificationInfo/gmd:MD_DataIdentification/"
                "gmd:extent/gmd:EX_Extent/gmd:temporalElement/"
                "gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/"
                "gml:beginPosition"), namespaces=root.nsmap)
        temporal_ends = root.xpath((
                "//gmd:identificationInfo/gmd:MD_DataIdentification/"
                "gmd:extent/gmd:EX_Extent/gmd:temporalElement/"
                "gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/"
                "gml:endPosition"), namespaces=root.nsmap)
        if len(temporal_starts) == len(temporal_ends):
            min_tstart = "9999-99-99T99:99:99"
            min_sflag = 6
            max_tend = "0000-00-00T00:00:00"
            min_eflag = 6
            for x in range(0, len(temporal_starts)):
                tstart = temporal_starts[x].text
                parts = tstart.split("T")
                dparts = parts[0].split("-")
                sflag = len(dparts)
                if len(parts) > 1:
                    tparts = parts[1].split(":")
                    sflag += len(tparts)
                    tstart += (":00" * (6-sflag))
                else:
                    tstart += ("-01" * (3-sflag)) + "T00:00:00"

                min_tstart = min(tstart, min_tstart)
                min_sflag = min(sflag, min_sflag)
                tend = temporal_ends[x].text
                parts = tend.split("T")
                dparts = parts[0].split("-")
                eflag = len(dparts)
                if len(parts) > 1:
                    tparts = parts[1].split(":")
                    eflag += len(tparts)
                    tend += (":99" * (6-sflag))
                else:
                    tend += ("-99" * (3-sflag)) + "T99:99:99"

                max_tend = max(tend, max_tend)
                min_eflag = min(eflag, min_eflag)

        flag = min(min_sflag, min_eflag) - 1
        tlen = 4
        for x in range(0, flag):
            tlen += 3

        ctx['tstart'] = min_tstart[0:tlen]
        ctx['tend'] = max_tend[0:tlen]
        return render(request, "metaman/datasets/import.html", ctx)
    except psycopg2.Error as err:
        return render(request, "metaman/datasets/import.html",
                      {'error': str(err)})
    finally:
        conn.close()


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
        keywords = values[6].replace(";", "\n").split("\n")
        ctx['variables'] = {'imported': [], 'not_imported': []}
        for keyword in keywords:
            parts = keyword.split(">")
            parts[-1] = parts[-1].strip()
            cursor.execute(
                    "select path, uuid from search.gcmd_sciencekeywords where "
                    "last_in_path ilike %s", (parts[-1], ))
            res = cursor.fetchall()
            if len(res) > 0:
                for e in res:
                    ctx['variables']['imported'].append("[!]".join(e))

            else:
                ctx['variables']['not_imported'].append(keyword.strip())

        ctx['variables']['imported'] = "\n".join(ctx['variables']['imported'])
        keywords = ctx['variables']['not_imported']
        ctx['instruments'] = {'imported': [], 'not_imported': []}
        for keyword in keywords:
            parts = keyword.split(">")
            parts[-1] = parts[-1].strip()
            cursor.execute(
                    "select path, uuid from search.gcmd_instruments where "
                    "last_in_path ilike %s", (parts[-1], ))
            res = cursor.fetchall()
            if len(res) > 0:
                for e in res:
                    ctx['instruments']['imported'].append("[!]".join(e))

            else:
                ctx['instruments']['not_imported'].append(keyword.strip())

        ctx['instruments']['imported'] = (
                "\n".join(ctx['instruments']['imported']))
        keywords = ctx['instruments']['not_imported']
        ctx['keywords_not_imported'] = "<br>".join(keywords)
        platforms = values[7].replace(";", "\n").split("\n")
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

        return render(request, "metaman/datasets/import.html", ctx)
    except Exception as err:
        return render(request, "metaman/datasets/import.html",
                      {'error': str(err)})
    finally:
        if 'conn' in locals():
            conn.close()


def do_import(request, spec):
    if spec == "gdex":
        return do_gdex_import(request)
    elif spec == "metadata_responses":
        return do_metadata_responses_import(request, spec)

    return render(request, "metaman/datasets/import.html")
