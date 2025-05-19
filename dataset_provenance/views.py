import json

from django.shortcuts import render
from wagtail.models import Page

from datasets.utils import ng_gdex_id
from dataset_description.models import DatasetDescriptionPage
from dataset_provenance.models import DatasetProvenancePage
from home.utils import slug_list


# Create your views here.

months = ["", "January", "February", "March", "April", "May", "June", "July", "Agust", "September", "October", "November", "December"]


def provenance(request, dsid):
    dsid = ng_gdex_id(dsid)
    slist = slug_list(dsid)
    for slug in slist:
        qs = Page.objects.type(DatasetProvenancePage).filter(url_path__contains=slug).live().specific()
        if len(qs) > 0:
            break;

    if len(qs) == 0:
        return render(request, "404.html")

    l = []
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
            del(d['end_date'])

        l.append(d)

    d = {'events': l}
    if 'HTTP_X_REQUESTED_WITH' in request.META:
        template = "dataset_provenance/dataset_provenance.html"
    else:
        template = "dataset_provenance/dataset_provenance_page.html"
        d['dsid'] = dsid
        d['title'] = "NCAR Dataset " + dsid + " Provenance"
        d['url'] = ""
        qs2 = Page.objects.type(DatasetDescriptionPage).filter(slug__in=slist).live().specific()
        if len(qs2) > 0:
            d['dsdoi'] = qs2[0].dsdoi
            d['dstitle'] = qs2[0].dstitle

    return render(request, template, {'page': d})
