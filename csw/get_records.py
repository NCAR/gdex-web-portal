import psycopg2

from django.conf import settings
from django.shortcuts import render
from libpkg.xmlutils import convert_html_to_text

from . import utils


def db_connect(request):
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
    except psycopg2.Error:
        return render(request, "csw/exception.xml",
                      context=utils.exception(
                              "TransactionFailed",
                              text="Database connection failure"),
                      content_type="application/xml", status=500)

    return conn


def hits(request, csw_request):
    conn = db_connect(request)
    try:
        cursor = conn.cursor()
        cursor.execute((
                "select count(dsid) from search.datasets where type in "
                "('P', 'H')"))
        res = cursor.fetchone()
        ctx = {'result_type': "hits",
               'num_matched': (int(res[0]) if res is not None else 0)}
        #cursor.execute((
        #        """select count(t."dc:identifier") from (select concat("""
        #        """'edu.ucar.gdex:', s.dsid) as "dc:identifier1", s.stitle """
        #        """as "dc.title", s.summary as "dct:abstract", concat("""
        #        """'doi:', v.doi) as "dc:identifier2", s.timestamp_utc as """
        #        """"dct:modified" from search.datasets as s left join """
        #        """dssdb.dsvrsn as v on v.dsid = s.dsid and v.status = """
        #        """'A' left join dssdb.dataset as d on d.dsid = s.dsid """
        #        """where s.type in ('P', 'H') having (""" +
        #        csw_request['constraint']['predicate'] + """) as x"""))
        #res = cursor.fetchall()
        return render(request, "csw/get_records.xml", context=ctx,
                      content_type="application/xml", status=200)
    except psycopg2.Error as err:
        print(f"CSW 'HITS' ERROR: '{err}', query: '{cursor.query}'")
        return render(request, "csw/exception.xml",
                      context=utils.exception("TransactionFailed",
                                              text="Database failure"),
                      content_type="application/xml", status=500)
    finally:
        conn.close()


def brief(request, csw_request):
    conn = db_connect(request)
    try:
        cursor = conn.cursor()
        cursor.execute((
                """select s.dsid, concat('edu.ucar.gdex:', s.dsid) as """
                """"dc:identifier1", s.title, concat('doi:', v.doi) as """
                """"dc:identifer2" from search.datasets as s left join """
                """dssdb.dsvrsn as v on v.dsid = s.dsid and v.status = 'A' """
                """where s.type in ('P', 'H') order by s.dsid"""))
        res = cursor.fetchall()
        ctx = {'result_type': "brief", 'num_matched': len(res),
               'num_returned': len(res), 'next_record': 0, 'records': []}
        for e in res:
            ctx['records'].append({'identifiers': [e[1]], 'title': e[2]})
            if len(e[3]) > 4:
                ctx['records'][-1]['identifiers'].append(e[3])

        return render(request, "csw/get_records.xml", context=ctx,
                      content_type="application/xml", status=200)
    except psycopg2.Error as err:
        print(f"CSW 'BRIEF' ERROR: '{err}', query: '{cursor.query}'")
        return render(request, "csw/exception.xml",
                      context=utils.exception("TransactionFailed",
                                              text="Database failure"),
                      content_type="application/xml", status=500)
    finally:
        conn.close()


def full(request, csw_request):
    ctx = {}
    return render(request, "csw/get_records.xml", context=ctx,
                  content_type="application/xml", status=200)


def summary(request, csw_request):
    conn = db_connect(request)
    try:
        cursor = conn.cursor()
        cursor.execute((
                """select s.dsid, concat('edu.ucar.gdex:', s.dsid) as """
                """"dc:identifier1", s.title as "dc.title", s.summary as """
                """"dct:abstract", concat('doi:', v.doi) as """
                """"dc.identifier2", s.timestamp_utc as "dct:modified" from """
                """search.datasets as s left join dssdb.dsvrsn as v on v."""
                """dsid = s.dsid and v.status = 'A' left join dssdb."""
                """dataset as d on d.dsid = s.dsid where s.type in """
                """('P', 'H') order by s.dsid"""))
        res = cursor.fetchall()
        ctx = {'result_type': "summary", 'num_matched': len(res),
               'num_returned': len(res), 'next_record': 0, 'records': []}
        for e in res:
            ctx['records'].append(
                    {'identifiers': [e[1]], 'title': e[2],
                     'abstract': convert_html_to_text("<summary>" + e[3] +
                                                      "</summary>"),
                     'modified': e[5].strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                     'subjects': [], 'formats': []})
            if len(e[4]) > 4:
                ctx['records'][-1]['identifiers'].append(e[4])

            cursor.execute((
                    "select g.path from search.variables as v left join "
                    "search.gcmd_sciencekeywords as g on g.uuid = v.keyword "
                    "where v.dsid = %s and v.vocabulary = 'GCMD' and g.path "
                    "is not null"), (e[0], ))
            subjects = cursor.fetchall()
            for s in subjects:
                ctx['records'][-1]['subjects'].append(s[0])

            cursor.execute((
                    "select distinct keyword from search.formats where dsid = "
                    "%s"), (e[0], ))
            formats = cursor.fetchall()
            for f in formats:
                ctx['records'][-1]['formats'].append(
                        f[0].replace("proprietary_", ""))

        return render(request, "csw/get_records.xml", context=ctx,
                      content_type="application/xml", status=200)
    except psycopg2.Error as err:
        print(f"CSW 'SUMMARY' ERROR: '{err}', query: '{cursor.query}'")
        return render(request, "csw/exception.xml",
                      context=utils.exception("TransactionFailed",
                                              text="Database failure"),
                      content_type="application/xml", status=500)
    finally:
        conn.close()


def respond(request, csw_request):
    if 'elementsetname' not in csw_request:
        csw_request['elementsetname'] = "summary"

    if csw_request['elementsetname'] not in ("brief", "full", "summary"):
        return render(request, "csw/exception.xml",
                      context=utils.exception("InvalidParameterValue",
                                              locator="ElementSetName"),
                      content_type="application/xml", status=400)

    if 'resulttype' not in csw_request:
        csw_request['resulttype'] = "hits"

    if csw_request['resulttype'] not in ("hits", "results"):
        return render(request, "csw/exception.xml",
                      context=utils.exception("InvalidParameterValue",
                                              locator="resultType"),
                      content_type="application/xml", status=400)

    code = None
    if 'typenames' not in csw_request:
        code = "MissingParameterValue"
    elif csw_request['typenames'] != "csw:Record":
        code = "InvalidParameterValue"

    if code is not None:
        return render(request, "csw/exception.xml",
                      context=utils.exception(code, locator="typeNames"),
                      content_type="application/xml", status=400)

    if csw_request['resulttype'] == "hits":
        return hits(request, csw_request)
    else:
        if csw_request['elementsetname'] == "brief":
            return brief(request, csw_request)
        elif csw_request['elementsetname'] == "full":
            return full(request, csw_request)
        elif csw_request['elementsetname'] == "summary":
            return summary(request, csw_request)

    return render(request, "csw/exception.xml",
                  context=utils.exception("TransactionFailed"),
                  content_type="application/xml", status=500)
