from django.shortcuts import render
from wagtail.models import Page

from datasets.views import description
from dataset_citation.models import DatasetCitationPage
from home.utils import slug_list

from . import styles

# Create your views here.


def citation(request, dsid):
    if 'style' in request.GET:
        if ('HTTP_X_REQUESTED_WITH' not in request.META and
                request.GET['style'] not in ("ris", "bibtex")):
            return render(request, "404.html")

        return styles.export_citation(request, dsid)

    slist = slug_list(dsid)
    for slug in slist:
        qs = Page.objects.type(DatasetCitationPage).filter(
                url_path__contains=slug).live().specific()
        if len(qs) > 0:
            break

    if len(qs) == 0:
        return render(request, "404.html")

    d = {'dsid': dsid, 'num_citations': qs[0].num_citations,
         'citations': qs[0].citations}
    if 'HTTP_X_REQUESTED_WITH' in request.META:
        return render(request, "dataset_citation/dataset_citation.html", d)

    return description(request, dsid,
                       template="dataset_citation/dataset_citation_page.html",
                       page_context=d)
