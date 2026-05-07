import os
import shutil

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def unlink(request):
    parts = request.META['HTTP_HOST'].split(".")
    if parts[0] != "api":
        return render(request, "404.html", status=404)

    if 'API-key' not in request.headers:
        return HttpResponse("Missing API key.", status=400,
                            reason="Bad Request")

    if request.headers['API-key'] not in settings.LOCAL_API_KEYS['unlink']:
        return HttpResponse("Invalid API key.", status=403, reason="Forbidden")

    if 'path' not in request.POST:
        return HttpResponse("Missing path.", status=400, reason="Bad Request")

    if not os.path.exists(request.POST['path']):
        return HttpResponse("Path does not exist.", status=400,
                            reason="Bad Request")

    if request.POST['path'][-1] == '/':
        try:
            shutil.rmtree(request.POST['path'])
        except Exception as err:
            return HttpResponse("Remove failed: {}".format(err), status=500,
                                reason="Internal Server Error")

    else:
        try:
            os.remove(request.POST['path'])
        except Exception as err:
            return HttpResponse("Remove failed: {}".format(err), status=500,
                                reason="Internal Server Error")

    return HttpResponse("Success.")
