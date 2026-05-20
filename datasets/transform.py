from django.shortcuts import render


def transform(request, dsid, markup_type, file):
    return render(request, "datasets/transform/grml.html")
