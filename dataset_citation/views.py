from django.shortcuts import render
from wagtail.models import Page

from datasets.utils import ng_gdex_id
from dataset_description.models import DatasetDescriptionPage
from dataset_citation.models import DatasetCitationPage
from home.utils import slug_list

# Create your views here.


def citation(request, dsid):
    dsid = ng_gdex_id(dsid)
    slist = slug_list(dsid);
    for slug in slist:
        qs = Page.objects.type(DatasetCitationPage).filter(url_path__contains=slug).live().specific()
        if len(qs) > 0:
            break;

    if len(qs) == 0:
        return render(request, "404.html")

    d = {'dsid': dsid, 'num_citations': qs[0].num_citations, 'citations': qs[0].citations}
    if 'HTTP_X_REQUESTED_WITH' in request.META:
        template = "dataset_citation/dataset_citation.html"

    else:
        template = "dataset_citation/dataset_citation_page.html"
        qs2 = Page.objects.type(DatasetDescriptionPage).filter(slug__in=slist).live().specific()
        if len(qs2) > 0:
            d.update({'page': qs2[0]})
            d['page'].dsid = dsid

    return render(request, template, d)
