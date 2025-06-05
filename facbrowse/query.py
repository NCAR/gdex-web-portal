from django.shortcuts import render

from .grml_query import do_grml_query
from .obml_query import do_obml_query


def query(request, dsid, listtyp, querytyp):
    if querytyp == "grml":
        return do_grml_query(request, dsid, listtyp)

    if querytyp == "obml":
        return do_obml_query(request, dsid, listtyp)

    return render(request, "facbrowse/grml_query.html",
                  {'error': "bad query type"})
