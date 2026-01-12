import os
import psycopg2

from django.conf import settings as django_settings
from django.http import StreamingHttpResponse
from libpkg.xmlutils import convert_html_to_text

import libpkg.metaformats.settings as metaformat_settings

from .utils import get_authors


def get_ds_data(dsid):
    try:
        conn = psycopg2.connect(**django_settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute((
                "select s.title, s.summary, s.pub_date, d.doi from search."
                "datasets as s left join dssdb.dsvrsn as d on d.dsid = s.dsid "
                "where s.dsid = %s"), (dsid, ))
        res = cursor.fetchone()
        return res
    except Exception as err:
        raise RuntimeError(err)
    finally:
        if 'conn' in locals():
            conn.close()


def get_publisher(ds_title):
    if ds_title[0:26] == "ICARUS Chamber Experiment:":
        return metaformat_settings.ARCHIVE['pub_name']['icarus']

    return metaformat_settings.ARCHIVE['pub_name']['default']


def create_bibtex(dsid):
    try:
        authors = get_authors(dsid)
        ds_data = get_ds_data(dsid)
        yield "@misc{{ncar_gdex_dataset_{},\n".format(dsid)
        yield '  author = "'
        for index, author in enumerate(authors):
            if index > 0:
                yield " and "

            if author[0] == "Person":
                yield author[1]

                if len(author[2]) > 0:
                    yield " {}".format(author[2])

                yield " {}".format(author[3])
            elif author[0] == "Organization":
                yield " {{{name}}}".format(name=author[1])
            else:
                parts = author[1].split(" > ")
                yield " {{{name}}}".format(name=parts[-1])

        yield '",\n'
        yield "  title = {{{{{title}}}}},\n".format(title=ds_data[0])
        yield '  publisher = "{}",\n'.format(get_publisher(ds_data[0]))
        yield '  address = "Boulder, CO",\n'
        yield "  year = {},\n".format(ds_data[2].year)
        if ds_data[3] is not None and len(ds_data[3]) > 0:
            yield '  doi = "{}"\n'.format(ds_data[3].replace("_", "\\{_}"))
            yield '  url = "{}"\n'.format(
                    os.path.join("https://",
                                 metaformat_settings.DOI_DOMAIN, ds_data[3]))
        else:
            yield '  url = "{}"\n'.format(
                    os.path.join("https://",
                                 metaformat_settings.ARCHIVE['domain'],
                                 metaformat_settings.ARCHIVE['datasets_path'],
                                 dsid, ""))

        yield "}\n"
    except Exception:
        yield "An error occurred and the file could not be created."
        return


def export_to_bibtex(dsid):
    headers = {'Content-type': "application/x-bibtex",
               'Content-disposition': (
                       "inline; filename=citation-ncar-" + dsid + ".bib")}
    return StreamingHttpResponse(create_bibtex(dsid), headers=headers)


def create_ris(dsid):
    try:
        authors = get_authors(dsid)
        ds_data = get_ds_data(dsid)
        abstract = convert_html_to_text(
                "<summary>" + ds_data[1] + "</summary>",
                wrapLength=80, indentLength=6).replace("\n", "\r\n").lstrip()
        yield "Provider: {}\r\n".format(
                metaformat_settings.ARCHIVE['pub_name']['default'])
        yield "Tagformat: ris\r\n"
        yield "\r\n"
        yield "TY  - DATA\r\n"
        for author in authors:
            if author[0] == "Person":
                yield "AU  - {}, {}".format(author[3], author[1])
                if len(author[2]) > 0:
                    yield " {}".format(author[2])

                yield "\r\n"
            elif author[0] == "Organization":
                yield "AU  - {}\r\n".format(author[1])
            else:
                parts = author[1].split(" > ")
                yield "AU  - {}\r\n".format(parts[-1])

        yield "T1  - {}\r\n".format(ds_data[0])
        yield "AB  - {}\r\n".format(abstract)
        yield "PY  - {}\r\n".format(ds_data[2].year)
        if ds_data[3] is not None and len(ds_data[3]) > 0:
            yield "DO  - {}\r\n".format(ds_data[3])
            yield "UR  - {}\r\n".format(
                    os.path.join("https://",
                                 metaformat_settings.DOI_DOMAIN, ds_data[3]))
        else:
            yield "UR  - {}\r\n".format(
                    os.path.join("https://",
                                 metaformat_settings.ARCHIVE['domain'],
                                 metaformat_settings.ARCHIVE['datasets_path'],
                                 dsid, ""))

        yield "PB  - {}\r\n".format(get_publisher(ds_data[0]))
        yield "CY  - Boulder, CO\r\n"
        yield "LA  - English\r\n"
        yield "ER  - \r\n"
    except Exception:
        yield "An error occurred and the file could not be created."
        return


def export_to_ris(dsid):
    headers = {'Content-type': "application/x-research-info-systems",
               'Content-disposition': (
                       "inline; filename=citation-ncar-" + dsid + ".ris")}
    return StreamingHttpResponse(create_ris(dsid), headers=headers)
