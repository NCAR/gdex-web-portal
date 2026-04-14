from . import utils


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
    publications = []
    for e in res:
        pubtype = utils.get_publication_type(e['type'])
        publications.append({'doi': {'ID': e['doi_work'],
                                     'publication_type': pubtype,
                                     'year': e['pub_year'],
                                     'title': e['title'],
                                     'publisher': e['publisher']}})

    return (publications, len(res))
