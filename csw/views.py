from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from . import get_capabilities, get_record_by_id, get_records, utils


@csrf_exempt
def respond_to_request(request):
    csw_request = utils.parse_request(request)
    if 'error' in csw_request:
        code = csw_request['error']['code']
        locator = (csw_request['error']['locator'] if 'locator' in
                   csw_request['error'] else None)
        text = (csw_request['error']['text'] if 'text' in csw_request['error']
                else None)
        ctx = utils.exception(code, locator=locator, text=text)
        return render(request, "csw/exception.xml",
                      context=ctx, content_type="application/xml", status=400)

    purged_ids = utils.purge_result_sets()
    if 'requestid' in csw_request and csw_request['requestid'] in purged_ids:
        del csw_request['requestid']

    if csw_request['request'] == "GetCapabilities":
        return get_capabilities.respond(request, csw_request)
    elif csw_request['request'] == "GetRecords":
        return get_records.respond(request, csw_request)
    elif csw_request['request'] == "GetRecordById":
        return get_record_by_id.respond(request, csw_request)

    ctx = utils.exception("InvalidParameterValue", locator="REQUEST")
    return render(request, "csw/exception.xml", context=ctx,
                  content_type="application/xml", status=400)
