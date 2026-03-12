from django.shortcuts import render


def exception(code, **kwargs):
    d = {'exception': {}}
    e = d['exception']
    e['code'] = code
    if 'locator' in kwargs:
        e['locator'] = kwargs['locator']

    if 'text' in kwargs:
        e['text'] = kwargs['text']

    return d


def parse_query(request):
    if request.method == "GET" and len(request.GET) > 0:
        csw_request = {}
        for key, value in request.GET.items():
            csw_request[key.lower()] = value

    elif request.method == "POST" and len(request.POST) > 0:
        csw_request = {}
    else:
        csw_request = {'error': {'code': "MIssingParameterValue",
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


def get_capabilities(request, csw_request):
    if 'sections' in csw_request:
        sections = csw_request['sections'].split(",")
        ctx = {}
        if "ServiceIdentification" in sections:
            ctx['print_service_identification'] = True

        if "ServiceProvider" in sections:
            ctx['print_service_provider'] = True

        if "OperationsMetadata" in sections:
            ctx['print_operations_metadata'] = True

        if "Filter_Capabilities" in sections:
            ctx['print_filter_capabilities'] = True

    else:
        ctx = {'print_service_identification': True,
               'print_service_provider': True,
               'print_operations_metadata': True,
               'print_filter_capabilities': True}

    return render(request, "csw/capabilities.xml", context=ctx,
                  content_type="application/xml", status=200)


def respond_to_request(request):
    csw_request = parse_query(request)
    if 'error' in csw_request:
        ctx = exception(csw_request['error']['code'],
                        locator=csw_request['error']['locator'])
        return render(request, "csw/exception.xml",
                      context=ctx, content_type="application/xml", status=400)

    if csw_request['request'] == "GetCapabilities":
        return get_capabilities(request, csw_request)

    return render(request, "403.html")
