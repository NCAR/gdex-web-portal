from lxml import etree

from .utils import (citations_tables,
                    format_publication_list_as_xml,
                    format_publications_as_bibliography,
                    get_authors,
                    get_publication_data)


def get_counts(doi, cursor, **kwargs):
    tbls = citations_tables()
    u = []
    params = []
    for tbl in tbls:
        u.append(f"select distinct doi_work, pub_year from citation.{tbl} as "
                 "d left join citation.works as w on w.doi = d.doi_work where "
                 "d.doi_data = %s and pub_year is not null")
        params.append(doi)

    u = " union ".join(u)
    query = f"select pub_year, count(distinct doi_work) from ({u}) as t"
    wc = []
    if 'min' in kwargs:
        wc.append("pub_year >= %s")
        params.append(kwargs['min'][-1])

    if 'max' in kwargs:
        wc.append("pub_year <= %s")
        params.append(kwargs['max'][-1])

    if len(wc) > 0:
        wc = " and ".join(wc)
        query += f" where {wc}"

    query += " group by pub_year order by pub_year"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    if kwargs['output_format'] == ".xml":
        counts = etree.Element('counts')
        for row in rows:
            e = etree.SubElement(counts, "year")
            e.text = str(row[0])
            e.set('citations', str(row[1]))

        return counts
    else:
        list = []
        for row in rows:
            list.append({'year': str(row[0]), 'citations': row[1]})

        return {'counts': list}


def get_publications(doi, cursor, **kwargs):
    tbls = citations_tables()
    query = []
    params = []
    for tbl in tbls:
        query.append(
                "select doi_work, title, pub_year, publisher, type from "
                f"citation.{tbl} as d left join citation.works as w on w.doi "
                "= d.doi_work where d.doi_data = %s and pub_year is not null")
        params.append(doi)

    query = " union ".join(query)
    if 'format' not in kwargs:
        query += " order by pub_year"

    cursor.execute(query, params)
    res = cursor.fetchall()
    publications = []
    auth_sep = " "
    if 'format' in kwargs:
        auth_sep = "::"

    for e in res:
        pubtype, pubdata = (
                get_publication_data(e['type'], e['doi_work'], cursor))
        publications.append(
                {'doi': {'ID': e['doi_work'],
                         'publication_type': pubtype,
                         'year': e['pub_year'],
                         'authors': get_authors(e['doi_work'], cursor,
                                                auth_sep),
                         'title': e['title'],
                         'publisher': e['publisher'],
                         'published_in': pubdata}})

    return (publications, len(res))


def updated_specific_doi_response(response, doi, cursor, **kwargs):
    if kwargs['show'] == "counts":
        if kwargs['output_format'] == ".xml":
            response.append(
                    get_counts(doi, cursor, **kwargs))
        else:
            response['doi'].update(
                    get_counts(doi, cursor, **kwargs))

        return True
    elif kwargs['show'] == "publications":
        publications, citedby_count = get_publications(
                doi, cursor, **kwargs)
        if 'format' in kwargs:
            if kwargs['format'][-1] == "bibliography":
                markup = None
                if 'markup' in kwargs:
                    markup = kwargs['markup'][-1]

                publications = format_publications_as_bibliography(
                        publications, markup=markup)

        if kwargs['output_format'] == ".xml":
            format_publication_list_as_xml(
                    publications, citedby_count, response, **kwargs)
        else:
            response['doi']['citedby-count'] = citedby_count
            response['doi']['publications'] = publications

        return True

    return False


def update_general_doi_response(response, doi, cursor, **kwargs):
    tbls = citations_tables()
    u = ""
    for x in range(len(tbls)):
        if x > 0:
            u += " union "

        u += ("select DOI_work, pub_year from citation." + tbls[x] + " as d "
              "left join citation.works as w on w.DOI = d.DOI_work where d."
              "doi_data = '" + doi + "' and pub_year is not null")

    query = ("select count(distinct DOI_work), min(pub_year), "
             "max(pub_year) from (" + u + ") as t")
    cursor.execute(query)
    row = cursor.fetchone()
    if kwargs['output_format'] == ".xml":
        etree.SubElement(response, 'totalCitations').text = str(row[0])
    else:
        response['doi'].update({'total_citations': row[0]})

    if row[0] > 0:
        if kwargs['output_format'] == ".xml":
            years = etree.SubElement(response, 'years')
            etree.SubElement(years, "min").text = str(row[1])
            etree.SubElement(years, "max").text = str(row[2])
        else:
            response['doi'].update({'years': {'min': row[1],
                                              'max': row[2]}})
