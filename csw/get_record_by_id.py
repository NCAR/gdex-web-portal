from django.shortcuts import render

from . import get_records, utils


def respond(request, csw_request):
    if 'id' not in csw_request:
        return render(request, "csw/exception.xml",
                      context=utils.exception("MissingParameterValue",
                                              locator="Id"),
                      content_type="application/xml", status=400)

    return get_records.respond(request, csw_request)
