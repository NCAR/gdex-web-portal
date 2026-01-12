import os
import psycopg2

from string import Template
from django.conf import settings as django_settings
from django.http import HttpResponse

import libpkg.metaformats.settings as metaformat_settings

from .export import export_to_bibtex, export_to_ris
from .utils import list_authors


MAP = {
    'agu': {
        'max_authors': 9,
        'other_authors': "et al.",
        'lfm': "all",
        'update_frequency': Template(" (Updated $frequency) "),
        'template': Template((
                "$authors. ($pub_year). $title $update_frequency[Dataset]. "
                "$publisher. $url. Accessed$dagger dd mmm yyyy.")),
    },
    'ams': {
        'max_authors': 8,
        'other_authors': "and Coauthors",
        'lfm': "first",
        'template': Template((
                "$authors, $pub_year: $title. $publisher, accessed$dagger "
                "dd mm yyyy, $url.")),
    },
    'copernicus': {
        'max_authors': 0,
        'other_authors': None,
        'lfm': "all",
        'template': Template((
                "$authors: $title, $publisher, $url, $pub_year. Accessed"
                "$dagger dd mmm yyyy.")),
    },
    'datacite': {
        'max_authors': 0,
        'other_authors': None,
        'lfm': "all",
        'template': Template((
                "$authors ($pub_year): $title. $publisher. Dataset. $url. "
                "Accessed$dagger dd mmm yyyy.")),
    },
    'esip': {
        'max_authors': 10,
        'other_authors': "et al.",
        'lfm': "first",
        'update_frequency': Template(", updated $frequency"),
        'template': Template((
                "$authors. $pub_year$update_frequency. $title. "
                "$publisher. $url. Accessed$dagger dd mmm yyyy.")),
    },
    'gdj': {
        'max_authors': 0,
        'other_authors': None,
        'lfm': "all",
        'template': Template((
                "$authors ($pub_year): $title. $publisher. $url. Accessed"
                "$dagger dd mmm yyyy.")),
    },
}


def export_citation(request, dsid, **kwargs):
    if request.GET['style'] in MAP:
        try:
            conn = psycopg2.connect(
                    **django_settings.RDADB['metadata_config_pg'])
            cursor = conn.cursor()
            cursor.execute((
                    "select title, pub_date, continuing_update from "
                    "search.datasets where dsid = %s"), (dsid, ))
            ds_data = cursor.fetchone()
            e = MAP[request.GET['style']]
            authors = list_authors(dsid, e['other_authors'],
                                   maxAuthors=e['max_authors'],
                                   lastFirstMiddle=e['lfm'])
            if request.GET['style'] in ("agu", "esip") and authors[-1] == '.':
                authors = authors[0:-1]

            update_frequency = ""
            if ds_data[2] == "Y" and 'update_frequency' in e:
                try:
                    wconn = psycopg2.connect(
                            **django_settings.RDADB['wagtail2_config_pg'])
                    wcursor = wconn.cursor()
                    wcursor.execute((
                            "select update_freq from wagtail2."
                            "dataset_description_datasetdescriptionpage where "
                            "dsid = %s"), (dsid, ))
                    res = wcursor.fetchone()
                    if res is not None:
                        update_frequency = res[0].lower()

                except Exception:
                    pass
                finally:
                    if 'wconn' in locals():
                        wconn.close()

            if len(update_frequency) > 0:
                update_frequency = e['update_frequency'].substitute(
                                frequency=update_frequency)

            cursor.execute((
                    "select doi, min(start_date) as sd, max(end_date) as ed, "
                    "status from dssdb.dsvrsn where dsid = %s and status in "
                    "('A', 'H') group by doi, status order by sd desc, "
                    "ed desc"), (dsid, ))
            dois = cursor.fetchall()
            if len(dois) > 0:
                url = os.path.join("https://", metaformat_settings.DOI_DOMAIN,
                                   dois[0][0])
            else:
                url = os.path.join(
                        "https://", metaformat_settings.ARCHIVE['domain'],
                        metaformat_settings.ARCHIVE['datasets_path'], dsid,
                        "")

            dagger = '<font color="red">&dagger;</font>'
            return HttpResponse(
                    e['template'].substitute(
                            authors=authors,
                            pub_year=ds_data[1].year,
                            update_frequency=update_frequency,
                            title=ds_data[0],
                            publisher=metaformat_settings.ARCHIVE[
                                    'pub_name']['default'],
                            url=url, dagger=dagger))
        except Exception as err:
            print("CITATION EXPORT ERROR: '" + str(err) + "'")
            return HttpResponse((
                    "An internal error occurred and the citation cannot be "
                    "loaded."))
        finally:
            if 'conn' in locals():
                conn.close()

    if request.GET['style'] == "bibtex":
        return export_to_bibtex(dsid)
    elif request.GET['style'] == "ris":
        return export_to_ris(dsid)

    return HttpResponse('<font color="red">Citation unavailable</font>')
