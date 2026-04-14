def get_dois(minter, cursor, **kwargs):
    query = ("select distinct c.doi_data, d.publisher, d.asset_type from "
             f"citation.data_citations{minter} as c left join citation."
             "doi_data as d on d.doi_data = c.doi_data")
    wc = []
    if 'asset-type' in kwargs:
        wc.append("d.asset_type = '" + kwargs.get('asset-type') + "'")

    if 'publisher' in kwargs:
        wc.append(("d.publisher = '" +
                   kwargs.get('publisher').strip('"') + "'"))

    if len(wc) > 0:
        query += " where " + " and ".join(wc)

    query += " order by c.doi_data"
    cursor.execute(query)
    res = cursor.fetchall()
    dois = []
    for e in res:
        dois.append({'doi': {'ID': e['doi_data'],
                             'asset-type': e['asset_type'],
                             'publisher': e['publisher']}})

    return dois


def get_publications(minter, cursor, **kwargs):
    publications = []
    return publications
