from lxml import etree as ElementTree

from .utils import citations_tables


def get_counts(query_dict, cursor, doi, output_format):
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
    if 'min' in query_dict:
        wc.append("pub_year >= %s")
        params.append(query_dict.get('min'))

    if 'max' in query_dict:
        wc.append("pub_year <= %s")
        params.append(query_dict.get('max'))

    if len(wc) > 0:
        wc = " and ".join(wc)
        query += f" where {wc}"

    query += " group by pub_year order by pub_year"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    if output_format == ".xml":
        counts = ElementTree.Element('counts')
        for row in rows:
            e = ElementTree.SubElement(counts, "year")
            e.text = str(row[0])
            e.set('citations', str(row[1]))

        return counts
    else:
        list = []
        for row in rows:
            list.append({'year': str(row[0]), 'citations': row[1]})

        return {'counts': list}
