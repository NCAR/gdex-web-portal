from django.conf import settings
import psycopg2
from lxml import etree as ElementTree

metadb_config = settings.RDADB['metadata_config_pg']

def citations_tables():
    conn = psycopg2.connect(**metadb_config)
    cursor = conn.cursor()
    query = "select table_name from information_schema.tables where table_schema = 'citation' and table_name like 'data_citations%'"
    cursor.execute(query)
    rows = cursor.fetchall()
    list = []
    for row in rows:
        list.append(row[0])

    return list

def valid_minters():
    tbls = citations_tables()
    list = []
    for tbl in tbls:
        center = tbl.replace("data_citations", "")
        if len(center) == 0:
            list.append('rda')
        else:
            list.append(center[1:])

    return list

def get_counts(query_dict, cursor, doi, output_format):
    tbls = citations_tables()
    u = ""
    for x in range(len(tbls)):
        if x > 0:
            u += " union "

        u += "select distinct doi_work, pub_year from citation." + tbls[x] + " as d left join citation.works as w on w.doi = d.doi_work where d.doi_data = '" + doi + "' and pub_year is not null"

    query = "select pub_year, count(distinct doi_work) from (" + u + ") as t"
    wc = ""
    if 'min' in query_dict:
        if len(wc) > 0:
            wc += " and "

        wc += "pub_year >= " + query_dict.get('min')

    if 'max' in query_dict:
        if len(wc) > 0:
            wc += " and "

        wc += "pub_year <= " + query_dict.get('max')

    if len(wc) > 0:
        query += " where " + wc

    query += " group by pub_year order by pub_year"
    cursor.execute(query)
    rows = cursor.fetchall()
    if output_format == ".xml":
        counts = ElementTree.Element('counts')
        for row in rows:
            e = ElementTree.SubElement(counts, "y" + str(row[0]))
            e.text = str(row[1])

        return counts
    else:
        list = []
        for row in rows:
            list.append({str(row[0]): row[1]})

        return {'counts': list}

def get_publications(query_dict, cursor, doi, output_format):
    tbls = citations_tables()
    query = ""
    for x in range(len(tbls)):
        if x > 0:
            query += " union "

        query += "select DOI_work, title, pub_year, publisher, type from citation." + tbls[x] + " as d left join citation.works as w on w.DOI = d.DOI_work where d.DOI_data = '" + doi + "' and pub_year is not null"

    if not 'format' in query_dict:
        query += " order by pub_year"

    cursor.execute(query)
    rows = cursor.fetchall()
    a_ws = " "
    if 'format' in query_dict:
        a_ws = "::"

    if output_format == ".xml":
        list = ElementTree.Element('publications')
    else:
        list = []
    for row in rows:
        if output_format == ".xml":
            d = ElementTree.SubElement(list, 'doi')
            d.set('ID', row[0])
            y = ElementTree.SubElement(d, 'year')
            y.text = str(row[2])
            a_list = ElementTree.SubElement(d, 'authors')
        else:
            d = {'doi': row[0], 'year': row[2]}
            a_list = []
        cursor.execute("select concat_ws('" + a_ws + "', first_name, case when middle_name = '' then NULL else middle_name end, last_name) from citation.works_authors where id = '" + row[0] + "' order by sequence")
        a_rows = cursor.fetchall()
        for a_row in a_rows:
            if output_format == ".xml":
                a = ElementTree.SubElement(a_list, 'author')
                a.text = a_row[0]
            else:
                a_list.append(a_row[0])

        if output_format == ".xml":
            t = ElementTree.SubElement(d, 'title')
            t.text = row[1]
            p = ElementTree.SubElement(d, 'publisher')
            p.text = row[3]
        else:
            d.update({'authors': a_list})
            d.update({'title': row[1], 'publisher': row[3]})
        if row[4] == "C":
            cursor.execute("select pages, ISBN from citation.book_chapter_works where DOI = '" + row[0] + "'")
            c_row = cursor.fetchone()
            if c_row != None:
                cursor.execute("select title, publisher from citation.book_works where ISBN = '" + c_row[1] + "'")
                b_row = cursor.fetchone()
                if b_row != None:
                    cursor.execute("select concat_ws(' ', first_name, case when middle_name = '' then NULL else middle_name end, last_name) from citation.works_authors where id = '" + c_row[1] + "'")
                    ed_res = cursor.fetchall()
                    if output_format == ".xml":
                        bc = ElementTree.SubElement(d, 'book_chapter')
                        i = ElementTree.SubElement(bc, 'ISBN')
                        i.text = c_row[1]
                        ed_list = ElementTree.SubElement(bc, 'editors')
                        t = ElementTree.SubElement(bc, 'title')
                        t.text = b_row[0]
                        p = ElementTree.SubElement(bc, 'publisher')
                        p.text = b_row[1]
                        pg = ElementTree.SubElement(bc, 'pages')
                        pg.text = c_row[0]
                    else:
                        ed_list = []

                    for editor in ed_res:
                        if output_format == ".xml":
                            e = ElementTree.SubElement(ed_list, 'editor')
                            e.text = editor[0]
                        else:
                            ed_list.append(editor[0])

                    if output_format == None or output_format == ".json":
                        d.update({'book_chapter': {'ISBN': c_row[1], 'editors': ed_list, 'title': b_row[0], 'publisher': b_row[1], 'pages': c_row[0]}})

        elif row[4] == "J":
            cursor.execute("select pub_name, volume, pages from citation.journal_works where DOI = '" + row[0] + "'")
            j_row = cursor.fetchone()
            if j_row != None:
                if output_format == ".xml":
                    j = ElementTree.SubElement(d, 'journal')
                    t = ElementTree.SubElement(j, 'title')
                    t.text = j_row[0]
                    v = ElementTree.SubElement(j, 'volume')
                    v.text = j_row[1]
                    pg = ElementTree.SubElement(j, 'pages')
                    pg.text = j_row[2]
                else:
                    d.update({'journal': {'title': j_row[0], 'volume': j_row[1], 'pages': j_row[2]}})

        elif row[4] == "P":
            cursor.execute("select pub_name, volume, pages from citation.proceedings_works where DOI = '" + row[0] + "'")
            p_row = cursor.fetchone()
            if p_row != None:
                if output_format == ".xml":
                    p = ElementTree.SubElement(d, 'publication')
                    t = ElementTree.SubElement(p, 'title')
                    t.text = p_row[0]
                    v = ElementTree.SubElement(p, 'volume')
                    v.text = p_row[1]
                    pg = ElementTree.SubElement(p, 'pages')
                    pg.text = p_row[2]
                else:
                    d.update({'publication': {'title': p_row[0], 'volume': p_row[1], 'pages': p_row[2]}})

        if output_format == None or output_format == ".json":
            list.append(d)

    if 'format' in query_dict:
        if query_dict['format'] == "bibliography":
            markup = None
            if 'markup' in query_dict:
                markup = query_dict['markup']

            return format_as_bibliography(list, markup=markup)

    if output_format == ".xml":
        return list
    else:
        return {'publications': list}

def authors_from_list(list):
    authors = ""
    llen = len(list)
    for i, author in enumerate(list, 1):
        if len(author) > 0:
            if len(authors) > 0:
            #    authors += ", "
                authors += "::"
            #if llen > 1 and i == llen:
            #    authors += "& "

            aparts = author.split("::")
            authors += aparts[-1] + ", " + aparts[0][:1] + "."
            if len(aparts) == 3:
                authors += " "
                if len(aparts[1]) >= 2 and aparts[1][1] == '.':
                    authors += aparts[1]
                else:
                    authors += aparts[1][:1] + "."

            if i == 19:
                aparts = list[-1].split("::")
                authors += ", ... " + aparts[-1] + ", " + aparts[0][:1] + "."
                if len(aparts) == 3:
                    authors += " "
                    if len(aparts[1]) >= 2 and aparts[1][1] == '.':
                        authors += aparts[1]
                    else:
                        authors += aparts[1][:1] + "."

                break

    return authors

def editors_from_list(list):
    editors = ""
    llen = len(list)
    for i, editor in enumerate(list, 1):
        if len(editor) > 0:
            if len(editors) > 0:
                editors += ", "
            if llen > 1 and i == llen:
                editors += "& "

            aparts = editor.split()
            editors += aparts[0][:1] + ". "
            if len(aparts) == 3:
                if len(aparts[1]) >= 2 and aparts[1][1] == '.':
                    editors += aparts[1]
                else:
                    editors += aparts[1][:1] + "."

                editors += " "

            editors += aparts[-1]

    return editors

def do_title_markup(t, **kwargs):
    if 'markup' in kwargs and kwargs['markup'] == "html":
        t = "<i>" + t + "</i>"

    return t

def do_volume_markup(v, **kwargs):
    if 'markup' in kwargs and kwargs['markup'] == "html":
        idx = v.find("(")
        if (idx > 0):
            v = "<i>" + v[0:idx] + "</i>" + v[idx:]
        else:
            v = "<i>" + v + "</i>"

    return v

def format_as_bibliography(list, **kwargs):
    # default is APA style
    bib_list = []
    markup = None
    if 'markup' in kwargs:
        markup = kwargs['markup']

    for item in list:
        authors = authors_from_list(item['authors'])
        if len(authors) > 0:
            bib_entry = authors + " (" + str(item['year']) + "). " + item['title'] + ". "
            if 'book_chapter' in item:
                bc = item['book_chapter']
                bib_entry += "In " + editors_from_list(bc['editors']) + " (Eds.), " + do_title_markup(bc['title'], markup=markup) + " (pp. " + bc['pages'] + "). " + bc['publisher'] + ". https://doi.org/" + item['doi']
            elif 'journal' in item:
                j = item['journal']
                bib_entry += do_title_markup(j['title'], markup=markup)
                if len(j['volume']) > 0:
                    bib_entry += ", " + do_volume_markup(j['volume'], markup=markup)

                if len(j['pages']) > 0:
                    bib_entry += ", " + j['pages']

                bib_entry += ". https://doi.org/" + item['doi']
            elif 'publication' in item:
                p = item['publication']
                bib_entry += do_title_markup(p['title'], markup=markup)
                if len(p['volume']) > 0:
                    bib_entry += ", " + do_volume_markup(p['volume'], markup=markup)

                if len(p['pages']) > 0:
                    bib_entry += ", " + p['pages']

                bib_entry += ". https://doi.org/" + item['doi']

            bib_list.append(bib_entry)

    bib_list.sort(key=str.casefold)
    list = []
    for entry in bib_list:
        idx = entry.rfind("::")
        if idx > 0:
            entry = entry[0:idx] + ", & " + entry[idx+2:]

        if markup == "html":
            idx = entry.find("\\u")
            while idx >= 0:
                entry = entry[0:idx] + "&#x" + entry[idx+2:idx+6] + ";" + entry[idx+6:]
                idx = entry.find("\\u")

        list.append(entry.replace("::", ", "))

    return {'bibliography': list}
