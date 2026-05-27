import json

from django.http import HttpResponse
from django.shortcuts import render


def swagger(request, output=None):
    return render(request, "dsfiles/swagger.html", {})


def filters(request, dsid):
    response = {'DSID': dsid,
                'filters': {
                        'valid-dates': {
                                'min': "", 'max': ""}}}
    return HttpResponse(json.dumps(response))
