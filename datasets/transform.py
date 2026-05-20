from django.shortcuts import render

from . import views


def transform(request, dsid, markup_type, file):
    d = views.get_dataset_description_context(dsid)
    ctx = {'page': d}
    return render(request, "datasets/transform/grml.html", ctx)
