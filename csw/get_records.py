import psycopg2

from django.conf import settings
from django.shortcuts import render

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
                "('P', 'H') order by dsid"))
        res = cursor.fetchone()
        ctx = {'result_type': "hits",
               'num_matched': (int(res[0]) if res is not None else 0)}
        #cursor.execute((
        #        """select count(t."dc:identifier") from (select concat("""
        #        """'edu.ucar.gdex:', s.dsid) as "dc:identifier1", s.stitle """
        #        """as "dc.title", s.summary as "dct:abstract", concat("""
        #        """'doi:', v.doi) as "dc:identifier2", d.date_change as """
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
                """"dc:identifier", s.title from search.datasets as s where """
                """s.type in ('P', 'H') order by s.dsid"""))
        res = cursor.fetchall()
        ctx = {'result_type': "brief", 'records': []}
        for e in res:
            ctx['records'].append({'identifier': e[1], 'title': e[2]})

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
    ctx = {}
    return render(request, "csw/get_records.xml", context=ctx,
                  content_type="application/xml", status=200)


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
