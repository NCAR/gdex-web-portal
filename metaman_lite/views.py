from django.shortcuts import render
from metaman.models import MetamanPage
from wagtail.models import Page


def start(request):
    qs = Page.objects.type(MetamanPage)
    return render(request, "metaman_lite/start.html",
                  {'title': qs[0].get_context(request)['page']['title']})
