from .customize import customize
from .query import query


def do_customize(request, dsid, listtyp):
    return customize(request, dsid, listtyp)


def do_query(request, dsid, listtyp, querytyp):
    return query(request, dsid, listtyp, querytyp)
