from lxml import etree as ElementTree

from .utils import (citations_tables, format_as_bibliography,
                    get_authors, get_publication_type)


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


def get_publications(doi, cursor, **kwargs):
    tbls = citations_tables()
    query = []
    params = []
    for tbl in tbls:
        query.append("select doi_work, title, pub_year, publisher, type from "
                     f"citation.{tbl} as d left join citation.works as w on w."
                     "doi = d.doi_work where d.doi_data = %s and pub_year is "
                     "not null")
        params.append(doi)

    query = " union ".join(query)
    if 'format' not in kwargs:
        query += " order by pub_year"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    auth_sep = " "
    if 'format' in kwargs:
        auth_sep = "::"

    if kwargs['output_format'] == ".xml":
        list = ElementTree.Element('publications')
    else:
        list = []

    for row in rows:
        pubtype = get_publication_type(row[4])
        if kwargs['output_format'] == ".xml":
            d = ElementTree.SubElement(list, "doi")
            d.set('ID', row[0])
            ElementTree.SubElement(d, "publicationType").text = pubtype
            y = ElementTree.SubElement(d, "year")
            y.text = str(row[2])
            a_list = ElementTree.SubElement(d, "authors")
        else:
            d = {'doi': {'ID': row[0], 'publication_type': pubtype,
                         'year': row[2]}}
            a_list = []

        authors = get_authors(row[0], auth_sep, cursor)
        for author in authors:
            if kwargs['output_format'] == ".xml":
                ElementTree.SubElement(a_list, "author").text = author
            else:
                a_list.append(author)

        if kwargs['output_format'] == ".xml":
            t = ElementTree.SubElement(d, "title")
            t.text = row[1]
            p = ElementTree.SubElement(d, "publisher")
            p.text = row[3]
        else:
            d['doi'].update({'authors': a_list, 'title': row[1],
                             'publisher': row[3]})

        if row[4] == "C":
            cursor.execute(
                    "select pages, ISBN from citation.book_chapter_works "
                    "where doi = %s", (row[0], ))
            c_row = cursor.fetchone()
            if c_row is not None:
                cursor.execute(
                        "select title, publisher from citation.book_works "
                        "where ISBN = %s", (c_row[1], ))
                b_row = cursor.fetchone()
                if b_row is not None:
                    cursor.execute(
                            "select concat_ws(' ', first_name, case when "
                            "middle_name = '' then NULL else middle_name end, "
                            "last_name) from citation.works_authors where id "
                            "= %s", (c_row[1], ))
                    ed_res = cursor.fetchall()
                    if kwargs['output_format'] == ".xml":
                        bc = ElementTree.SubElement(d, "publishedIn")
                        i = ElementTree.SubElement(bc, "ISBN")
                        i.text = c_row[1]
                        ed_list = ElementTree.SubElement(bc, "editors")
                        t = ElementTree.SubElement(bc, "title")
                        t.text = b_row[0]
                        p = ElementTree.SubElement(bc, "publisher")
                        p.text = b_row[1]
                        pg = ElementTree.SubElement(bc, "pages")
                        pg.text = c_row[0]
                    else:
                        ed_list = []

                    for editor in ed_res:
                        if kwargs['output_format'] == ".xml":
                            e = ElementTree.SubElement(ed_list, 'editor')
                            e.text = editor[0]
                        else:
                            ed_list.append(editor[0])

                    if (kwargs['output_format'] is None or
                            kwargs['output_format'] == ".json"):
                        d['doi'].update(
                                {'published_in':
                                 {'ISBN': c_row[1], "editors": ed_list,
                                  'title': b_row[0], "publisher": b_row[1],
                                  'pages': c_row[0]}})

        elif row[4] == "J":
            cursor.execute(
                    "select pub_name, volume, pages from citation."
                    "journal_works where doi = %s", (row[0], ))
            j_row = cursor.fetchone()
            if j_row is not None:
                if kwargs['output_format'] == ".xml":
                    j = ElementTree.SubElement(d, "publishedIn")
                    t = ElementTree.SubElement(j, "title")
                    t.text = j_row[0]
                    v = ElementTree.SubElement(j, "volume")
                    v.text = j_row[1]
                    pg = ElementTree.SubElement(j, "pages")
                    pg.text = j_row[2]
                else:
                    d['doi'].update(
                            {'published_in':
                             {'title': j_row[0], 'volume': j_row[1],
                              'pages': j_row[2]}})

        elif row[4] == "P":
            cursor.execute(
                    "select pub_name, volume, pages from citation."
                    "proceedings_works where doi = %s", (row[0], ))
            p_row = cursor.fetchone()
            if p_row is not None:
                if kwargs['output_format'] == ".xml":
                    p = ElementTree.SubElement(d, "publishedIn")
                    t = ElementTree.SubElement(p, "title")
                    t.text = p_row[0]
                    v = ElementTree.SubElement(p, "volume")
                    v.text = p_row[1]
                    pg = ElementTree.SubElement(p, "pages")
                    pg.text = p_row[2]
                else:
                    d['doi'].update(
                            {'published_in':
                             {'title': p_row[0], 'volume': p_row[1],
                              'pages': p_row[2]}})

        if (kwargs['output_format'] is None or kwargs['output_format'] ==
                ".json"):
            list.append(d)

    if 'format' in kwargs:
        if kwargs['format'][-1] == "bibliography":
            markup = None
            if 'markup' in kwargs:
                markup = kwargs['markup'][-1]

            return format_as_bibliography(list, markup=markup)

    if kwargs['output_format'] == ".xml":
        return list

    return {'publications': list}
