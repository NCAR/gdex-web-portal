from django.shortcuts import render
from wagtail.models import Page

from datasets.utils import ng_gdex_id
from datasets.views import description
from dataset_provenance.models import DatasetProvenancePage
from home.utils import slug_list


# Create your views here.

def provenance(request, dsid):
    dsid = ng_gdex_id(dsid)
    slist = slug_list(dsid)
    for slug in slist:
        qs = Page.objects.type(DatasetProvenancePage).filter(
                url_path__contains=slug).live().specific()
        if len(qs) > 0:
            break

    if len(qs) == 0:
        return render(request, "404.html")

    events = []
    for event in qs[0].events:
        d = {}
        sd = event.value.get('start_date')
        d.update({'start_date': sd.isoformat()})
        ed = event.value.get('end_date')
        d.update({'end_date': ed.isoformat()})
        d.update({'source_institution': event.value.get('source_institution')})
        d.update({'description': event.value.get('description')})
        if sd == ed:
            d['start_date'] = "{0:%B} {0:%Y}".format(sd)
            del d['end_date']

        events.append(d)

    d = {'events': events}
    if 'HTTP_X_REQUESTED_WITH' in request.META:
        return render(request, "dataset_provenance/dataset_provenance.html",
                      {'page': d})

    d['dsid'] = dsid
    return description(request, dsid,
                       template=(
                               "dataset_provenance/dataset_provenance_page."
                               "html"),
                       page_context=d)
