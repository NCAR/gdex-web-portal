from lxml import etree as ElementTree


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
