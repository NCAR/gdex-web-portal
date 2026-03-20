import psycopg2

from lxml import etree as ElementTree
from datetime import datetime, timezone
from django.conf import settings


def exception(code, **kwargs):
    d = {'exception': {}}
    e = d['exception']
    e['code'] = code
    if 'locator' in kwargs:
        e['locator'] = kwargs['locator']

    if 'text' in kwargs:
        e['text'] = kwargs['text']

    return d


def parse_request(request):
    if request.method == "GET" and len(request.GET) > 0:
        csw_request = {}
        for key, value in request.GET.items():
            csw_request[key.lower()] = value

    elif request.method == "POST" and len(request.POST) > 0:
        try:
            root = ElementTree.fromstring(request.body.decode("utf-8"))
            csw_request = {'request': root.tag}
            for key, value in root.attrib.items():
                csw_request[key.lower()] = value

        except Exception as err:
            return {'error': {'code': "InvalidRequest",
                              'locator': "Error",
                              'text': str(err)}}
    else:
        csw_request = {'error': {'code': "MissingParameterValue",
                                 'locator': "REQUEST"}}

    if 'service' not in csw_request:
        csw_request = {'error': {'code': "MissingParameterValue",
                                 'locator': "service"}}
    elif csw_request['service'] != "CSW":
        csw_request = {'error': {'code': "InvalidParameterValue",
                                 'locator': "service"}}

    if 'acceptversions' in csw_request:
        versions = [e.strip() for e in
                    csw_request['acceptversions'].split(",")]
        if "2.0.2" not in versions:
            csw_request = {'error': {'code': "VersionNegotiationFailed"}}

    return csw_request


def purge_result_sets():
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        now = datetime.now()
        now.replace(tzinfo=timezone.utc)
        cursor.execute((
                "select id from metautil.csw_result_set_ids where expiration "
                "< %s"), (now, ))
        res = cursor.fetchall()
        if len(res) > 0:
            ids = tuple(e[0] for e in res)
            cursor.execute((
                    "delete from metautil.csw_result_sets where id in %s"),
                    (str(ids), ))
            cursor.execute((
                    "delete from metautil.csw_result_set_ids where id in %s"),
                    (str(ids), ))
            conn.commit()
        else:
            ids = ()

        conn.close()
        return ids
    except Exception:
        return ()
