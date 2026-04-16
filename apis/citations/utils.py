import psycopg2

from django.conf import settings
from lxml import etree as ElementTree


metadb_config = settings.RDADB['metadata_config_pg']


def citations_tables():
    conn = psycopg2.connect(**metadb_config)
    cursor = conn.cursor()
    query = ("select table_name from information_schema.tables where "
             "table_schema = 'citation' and table_name like 'data_citations%'")
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


def get_publication_data(type):
    if type == "C":
        return ("book_chapter", {})

    if type == "J":
        return ("journal_article", {})

    if type == "P":
        return ("conference_paper", {})

    return (None, {})


def get_authors(id, cursor, separator):
    cursor.execute(
            f"select concat_ws('{separator}', first_name, case when "
            "middle_name = '' then NULL else middle_name end, last_name) from "
            "citation.works_authors where id = %s order by sequence", (id, ))
    return [e[0] for e in cursor.fetchall()]


def authors_from_list(list):
    authors = ""
    for i, author in enumerate(list, 1):
        if len(author) > 0:
            if len(authors) > 0:
                authors += "::"

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


def format_publication_list_as_xml(publications, citedby_count, root):
    e = ElementTree.SubElement(root, "citedbyCount").text = (
            str(citedby_count))
    e = ElementTree.SubElement(root, "publications")
    for publication in publications:
        pub_e = ElementTree.SubElement(e, "publication")
        doi_e = ElementTree.SubElement(
                pub_e, "doi", ID=publication['doi']['ID'])
        ElementTree.SubElement(doi_e, "publicationType").text = (
                publication['doi']['publication_type'])
        ElementTree.SubElement(doi_e, "year").text = (
                str(publication['doi']['year']))
        auth_e = ElementTree.SubElement(doi_e, "authors")
        for author in publication['doi']['authors']:
            ElementTree.SubElement(auth_e, "author").text = author

        ElementTree.SubElement(doi_e, "title").text = (
                publication['doi']['title'])
        ElementTree.SubElement(doi_e, "publisher").text = (
                publication['doi']['publisher'])


def format_as_bibliography(list, **kwargs):
    # default is APA style
    bib_list = []
    markup = None
    if 'markup' in kwargs:
        markup = kwargs['markup']

    for item in list:
        item = item['doi']
        authors = authors_from_list(item['authors'])
        if len(authors) > 0:
            bib_entry = (
                    authors + " (" + str(item['year']) + "). " +
                    item['title'] + ". ")
            if 'book_chapter' in item:
                bc = item['book_chapter']
                bib_entry += (
                        "In " + editors_from_list(bc['editors']) +
                        " (Eds.), " + do_title_markup(bc['title'],
                                                      markup=markup) +
                        " (pp. " + bc['pages'] + "). " + bc['publisher'] +
                        ". https://doi.org/" + item['ID'])
            elif 'journal' in item:
                j = item['journal']
                bib_entry += do_title_markup(j['title'], markup=markup)
                if len(j['volume']) > 0:
                    bib_entry += (
                            ", " + do_volume_markup(j['volume'],
                                                    markup=markup))

                if len(j['pages']) > 0:
                    bib_entry += ", " + j['pages']

                bib_entry += ". https://doi.org/" + item['ID']
            elif 'publication' in item:
                p = item['publication']
                bib_entry += do_title_markup(p['title'], markup=markup)
                if len(p['volume']) > 0:
                    bib_entry += (
                            ", " + do_volume_markup(p['volume'],
                                                    markup=markup))

                if len(p['pages']) > 0:
                    bib_entry += ", " + p['pages']

                bib_entry += ". https://doi.org/" + item['ID']

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
                entry = (entry[0:idx] + "&#x" + entry[idx+2:idx+6] + ";" +
                         entry[idx+6:])
                idx = entry.find("\\u")

        list.append(entry.replace("::", ", "))

    return {'bibliography': list}


def error(output_format, error_message):
    if output_format == ".xml":
        response = ElementTree.Element("Error")
        ElementTree.SubElement(response, "ErrorMessage").text = error_message
    else:
        response = {'error_message': error_message}

    return {'response': response, 'status': 400}
