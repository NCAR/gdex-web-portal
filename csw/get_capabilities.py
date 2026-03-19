from django.shortcuts import render


def respond(request, csw_request):
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
