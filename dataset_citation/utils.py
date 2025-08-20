import psycopg2

from django.conf import settings as django_settings


def get_authors(dsid):
    try:
        conn = psycopg2.connect(**django_settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute((
                "select type, given_name, middle_name, family_name from "
                "search.dataset_authors where dsid = %s order by sequence"),
                (dsid, ))
        res = cursor.fetchall()
        if len(res) > 0:
            return res

        cursor.execute((
                "select 'Contributor', g.path, c.contact from search."
                "contributors_new as c left join search.gcmd_providers as g "
                "on g.uuid = c.keyword where c.dsid = %s and c.vocabulary = "
                "'GCMD' and c.citable = 'Y' order by c.disp_order"), (dsid, ))
        return cursor.fetchall()
    except Exception:
        return ()
    finally:
        if 'conn' in locals():
            conn.close()


def get_lfm(t):
    lfm = t[2] + ", " + t[0][0:1] + "."
    if len(t[1]) > 0:
        if t[1].find(".") > 0:
            lfm += " " + t[1]
        else:
            lfm += " " + t[1][0:1] + "."

    return lfm


def get_fml(t):
    fml = t[0][0:1] + "."
    if len(t[1]) > 0:
        if t[1].find(".") > 0:
            fml += " " + t[1]
        else:
            fml += " " + t[1][0:1] + "."

    fml += " " + t[2]
    return fml


def get_contributor(t):
    if t[0] == "UNAFFILIATED INDIVIDUAL":
        contacts = t[1].split(",")
        if len(contacts) > 0:
            return "Unaffiliated Individual:" + contacts[0]

    else:
        parts = t[0].split (" > ")
        return parts[-1].replace(", ", ":")

    return ""


def list_authors(dsid, et_al, **kwargs):
    max_authors = kwargs['maxAuthors'] if 'maxAuthors' in kwargs else 0
    if max_authors == 0 and et_al != None and len(et_al) == 0:
        return ""

    lfm = kwargs['lastFirstMiddle'] if 'lastFirstMiddle' in kwargs else "first"
    auth_list = get_authors(dsid)
    if len(auth_list) > 0:
        if auth_list[0][0] == "Person":
            authors = [get_lfm(auth_list[0][1:])]
        else:
            authors = [auth_list[0][1]]

        if max_authors > 0 and len(auth_list) > max_authors:
            authors.append(et_al)
            return ", ".join(authors)

        del auth_list[0]
        for author in auth_list:
            if author[0] == "Person":
                if lfm == "first":
                    authors.append(get_fml(author[1:]))
                else:
                    authors.append(get_lfm(author[1:]))

            elif author[0] == "Organization":
                authors.append(author[1])
            else:
                authors.append(get_contributor(author[1:]))

        if len(authors) > 1:
            return ", ".join(authors[0:-1]) + ", and " + authors[-1]
        else:
            return authors[0]

    return ""
