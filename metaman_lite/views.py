from django.shortcuts import render
from metaman.models import MetamanPage
from wagtail.models import Page


def start(request, token):
    qs = Page.objects.type(MetamanPage).live().specific()
    return render(request, "metaman_lite/start.html", {'title': qs[0].title})
