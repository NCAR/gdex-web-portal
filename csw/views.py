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


def respond_to_request(request):
    if len(request.GET) == 0 and len(request.POST) == 0:
        return render(request, "csw/exception.html",
                      context=exception("InvalidParameterValue",
                                        locator="REQUEST"),
                      content_type="application/xml", status=400)

    return render(request, "403.html")
