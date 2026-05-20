from django.http import HttpResponse


def transform(dsid, markup_type, file):
    return HttpResponse(f"Hello! {dsid} {markup_type} {file}") 
