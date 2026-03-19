import psycopg2

from django.conf import settings
from django.shortcuts import render
from libpkg.metaformats.settings import ARCHIVE
from libpkg.geospatial import fill_geographic_extent_data
from libpkg.metautils import get_temporal_range, metadata_date
from libpkg.xmlutils import convert_html_to_text

from . import utils


def hits(request, csw_request, conn):
    try:
        cursor = conn.cursor()
        cursor.execute((
                "select count(dsid) from search.datasets where type in "
                "('P', 'H') and dsid < 'd999000'"))
        res = cursor.fetchone()
        ctx = {'result_type': "hits",
               'num_matched': (int(res[0]) if res is not None else 0)}
        #cursor.execute((
        #        """select count(t."dc:identifier") from (select concat("""
        #        """'edu.ucar.gdex:', s.dsid) as "dc:identifier1", s.stitle """
        #        """as "dc.title", s.summary as "dct:abstract", concat("""
        #        """'doi:', v.doi) as "dc:identifier2" from search.datasets """
        #        """as s left join dssdb.dsvrsn as v on v.dsid = s.dsid and """
        #        """v.status = 'A' left join dssdb.dataset as d on d.dsid = """
        #        """s.dsid where s.type in ('P', 'H') and s.dsid < """
        #        """'d999009' having (""" +
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


def brief(request, csw_request, conn):
    try:
        cursor = conn.cursor()
        cursor.execute((
                """select s.dsid, concat('edu.ucar.gdex:', s.dsid) as """
                """"dc:identifier1", s.title, concat('doi:', v.doi) as """
                """"dc:identifer2" from search.datasets as s left join """
                """dssdb.dsvrsn as v on v.dsid = s.dsid and v.status = 'A' """
                """where s.type in ('P', 'H') and s.dsid < 'd999000' order """
                """by s.dsid"""))
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


def full(request, csw_request, conn):
    ctx = summary(request, csw_request, conn)
    ctx['publisher'] = ARCHIVE['pub_name']['default']['name']
    try:
        cursor = conn.cursor()
        cursor.execute((
                "select count(*) from search.datasets where type in "
                "('P', 'H') and dsid < 'd999000'"))
        ctx['num_matched'] = cursor.fetchone()[0]
        if ctx['next_record'] > ctx['num_matched']:
            ctx['next_record'] = 0

        for record in ctx['records']:
            cursor.execute((
                    "select type, given_name, middle_name, family_name from "
                    "search.dataset_authors where dsid = %s order by "
                    "sequence"), (record['identifiers'][0][14:], ))
            authors = cursor.fetchall()
            if len(authors) == 0:
                cursor.execute((
                        "select 'Organization', p.path from search."
                        "contributors_new as c left join search."
                        "gcmd_providers as p on p.uuid = c.keyword where dsid "
                        "= %s and c.citable = 'Y' order by c.disp_order"),
                        (record['identifiers'][0][14:], ))
                authors = cursor.fetchall()

            if len(authors) > 0:
                record['creators'] = []
                for author in authors:
                    if author[0] == "Person":
                        record['creators'].append(
                                " ".join([a for a in author[1:4] if len(a) >
                                         0]))
                    elif author[0] == "Organization":
                        record['creators'].append(author[1])

            cursor.execute((
                    "select p.path from search.contributors_new as c left "
                    "join search.gcmd_providers as p on p.uuid = c.keyword "
                    "where dsid = %s and c.citable = 'N' order by c."
                    "disp_order"), (record['identifiers'][0][14:], ))
            contributors = cursor.fetchall()
            if len(contributors) > 0:
                record['contributors'] = [c[0] for c in contributors]

            trange = get_temporal_range(record['identifiers'][0][14:],
                                        cursor)
            if all(trange):
                record['temporal_range'] = {'start': trange[0],
                                            'end': trange[1]}

            geoext = fill_geographic_extent_data(record['identifiers'][0][14:],
                                                 cursor)
            if None not in geoext.values():
                record['bounding_box'] = {
                        'lower_corner': {'west_lon': geoext['wlon'],
                                         'south_lat': geoext['slat']},
                        'upper_corner': {'east_lon': geoext['elon'],
                                         'north_lat': geoext['nlat']}}

        return render(request, "csw/get_records.xml", context=ctx,
                      content_type="application/xml", status=200)
    except psycopg2.Error as err:
        print(f"CSW 'FULL' ERROR: '{err}', query: '{cursor.query}'")
        return render(request, "csw/exception.xml",
                      context=utils.exception("TransactionFailed",
                                              text="Database failure"),
                      content_type="application/xml", status=500)


def summary(request, csw_request, conn):
    try:
        cursor = conn.cursor()
        limit = None
        offset = 0
        next_record = 0
        if csw_request['elementsetname'] == "full":
            if 'startposition' in csw_request:
                offset = int(csw_request['startposition']) - 1

            limit = 100
            if 'maxrecords' in csw_request:
                limit = min(limit, int(csw_request['maxrecords']))

            next_record = offset + limit + 1

        cursor.execute((
                """select s.dsid, concat('edu.ucar.gdex:', s.dsid) as """
                """"dc:identifier1", s.title as "dc.title", s.summary as """
                """"dct:abstract", concat('doi:', v.doi) as """
                """"dc.identifier2" from search.datasets as s left join """
                """dssdb.dsvrsn as v on v.dsid = s.dsid and v.status = 'A' """
                """left join dssdb.dataset as d on d.dsid = s.dsid where s."""
                """type in ('P', 'H') and s.dsid < 'd999000' order by s."""
                """dsid limit %s offset %s"""), (limit, offset))
        res = cursor.fetchall()
        ctx = {'result_type': csw_request['elementsetname'],
               'num_matched': len(res), 'num_returned': len(res),
               'next_record': next_record, 'records': []}
        for e in res:
            mdate = metadata_date(e[0], cursor)
            ctx['records'].append(
                    {'identifiers': [e[1]], 'title': e[2],
                     'abstract': convert_html_to_text("<summary>" + e[3] +
                                                      "</summary>"),
                     'modified': mdate.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
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

        if csw_request['elementsetname'] == "full":
            return ctx

        return render(request, "csw/get_records.xml", context=ctx,
                      content_type="application/xml", status=200)
    except psycopg2.Error as err:
        print((
                f"CSW '{csw_request['elementsetname']}' ERROR: '{err}', "
                "query: '{cursor.query}'"))
        return render(request, "csw/exception.xml",
                      context=utils.exception("TransactionFailed",
                                              text="Database failure"),
                      content_type="application/xml", status=500)


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

    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        if csw_request['resulttype'] == "hits":
            return hits(request, csw_request, conn)
        else:
            if csw_request['elementsetname'] == "brief":
                return brief(request, csw_request, conn)
            elif csw_request['elementsetname'] == "full":
                return full(request, csw_request, conn)
            elif csw_request['elementsetname'] == "summary":
                return summary(request, csw_request, conn)

        return render(request, "csw/exception.xml",
                      context=utils.exception("TransactionFailed"),
                      content_type="application/xml", status=500)
    except psycopg2.Error:
        return render(request, "csw/exception.xml",
                      context=utils.exception(
                              "TransactionFailed",
                              text="Database connection failure"),
                      content_type="application/xml", status=500)
    finally:
        if 'conn' in locals():
            conn.close()
