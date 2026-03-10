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
        pass
    elif request.method == "POST" and len(request.POST) > 0:
        pass
    else:
        return {'error': {'code': "MIssingParameterValue",
                          'locator': "REQUEST"}}


def respond_to_request(request):
    csw_request = parse_query(request)
    if 'error' in csw_request:
        ctx = exception(csw_request['error']['code'],
                        locator=csw_request['error']['locator'])
        return render(request, "csw/exception.xml",
                      context=ctx, content_type="application/xml", status=400)

    return render(request, "403.html")
