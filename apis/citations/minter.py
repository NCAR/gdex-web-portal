from lxml import etree

from .utils import (format_publication_list_as_xml,
                    get_authors,
                    get_publication_data)


def get_dois(minter, cursor, **kwargs):
    query = ("select distinct c.doi_data, d.publisher, d.asset_type from "
             f"citation.data_citations{minter} as c left join citation."
             "doi_data as d on d.doi_data = c.doi_data")
    wc = []
    params = []
    if 'asset-type' in kwargs:
        wc.append("d.asset_type = %s")
        params.append(kwargs['asset-type'][-1])

    if 'publisher' in kwargs:
        wc.append("d.publisher = %s")
        params.append(kwargs['publisher'][-1].strip('"'))

    if len(wc) > 0:
        query += " where " + " and ".join(wc)

    query += " order by c.doi_data"
    cursor.execute(query, params)
    res = cursor.fetchall()
    dois = []
    for e in res:
        dois.append({'doi': {'ID': e['doi_data'],
                             'asset-type': e['asset_type'],
                             'publisher': e['publisher']}})

    return dois


def get_publications(minter, cursor, **kwargs):
    query = ("select distinct c.doi_work, w.type, w.pub_year, w.title, w."
             f"publisher from citation.data_citations{minter} as c left join "
             "citation.works as w on w.doi = c.doi_work where w.pub_year is "
             "not null order by w.pub_year")
    cursor.execute(query)
    res = cursor.fetchall()
    if kwargs['from_swagger']:
        # if from swagger, limit the results to 10, otherwise a large number of
        #  results overloads the swagger UI
        del res[10:]

    publications = []
    for e in res:
        pubtype, pubdata = (
                get_publication_data(e['type'], e['doi_work'], cursor))
        publications.append(
                {'doi': {'ID': e['doi_work'],
                         'publication_type': pubtype,
                         'year': e['pub_year'],
                         'authors': get_authors(e['doi_work'], cursor, " "),
                         'title': e['title'],
                         'publisher': e['publisher'],
                         'published_in': pubdata}})

    return (publications, len(res))


def updated_specific_minter_response(response, minter, cursor, **kwargs):
    if kwargs['show'] == "dois":
        dois = get_dois(minter, cursor, **kwargs)
        if kwargs['output_format'] == ".xml":
            e = etree.SubElement(response, "dois")
            for doi in dois:
                d = etree.SubElement(e, "doi")
                d.set('ID', doi['doi']['ID'])
                etree.SubElement(d, "assetType").text = (
                        doi['doi']['asset-type'])

                etree.SubElement(d, "publisher").text = (
                        doi['doi']['publisher'])

        else:
            response['minter'].update({'dois': dois})

        return True
    elif kwargs['show'] == "publications":
        publications, citedby_count = get_publications(
                minter, cursor, **kwargs)
        if kwargs['output_format'] == ".xml":
            format_publication_list_as_xml(
                    publications, citedby_count, response, **kwargs)
        else:
            response['minter']['citedby-count'] = citedby_count
            if kwargs['from_swagger']:
                response['minter']['comment'] = (
                       "Example results from this UI are limited to 10 "
                       "results. A (e.g.) 'curl' command will return all "
                       "available results.")

            response['minter']['publications'] = publications

        return True

    return False


def update_general_minter_response(response, minter, cursor, **kwargs):
    query = ("select distinct d.publisher, d.asset_type from citation."
             f"data_citations{minter} as c left join citation.doi_data as d "
             "on d.DOI_data = c.DOI_data")
    cursor.execute(query)
    res = cursor.fetchall()
    pubs = []
    assets = []
    for e in res:
        pubs.append(e['publisher'])
        if e['asset_type'] not in assets:
            assets.append(e['asset_type'])

    if kwargs['output_format'] == ".xml":
        e = etree.SubElement(response, "assetTypes")
        for asset in assets:
            etree.SubElement(e, "assetType").text = asset

        e = etree.SubElement(response, "publishers")
        for pub in pubs:
            etree.SubElement(e, "publisher").text = pub

    else:
        response['minter'].update({'asset-types': assets, 'publishers': pubs})
