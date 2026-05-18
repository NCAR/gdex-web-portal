import os
import shutil

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


def good_path(key_path, spec_path):
    if len(key_path) == 0 and spec_path[0] != '/':
        return False

    if len(key_path) > 0 and spec_path[0] == '/':
        return False

    return True


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

    is_good_path = good_path(
            (settings.LOCAL_API_KEYS['unlink']
             [request.headers['API-key']]), request.POST['path'])
    if not is_good_path:
        return HttpResponse("Invalid path.", status=400,
                            reason="Bad Request")

    path = os.path.join(
            settings.LOCAL_API_KEYS['unlink'][request.headers['API-key']],
            request.POST['path'])
    if not os.path.exists(path):
        return HttpResponse("Path does not exist.", status=400,
                            reason="Bad Request")

    if path[-1] == '/':
        try:
            shutil.rmtree(path)
        except Exception as err:
            return HttpResponse("Remove failed: {}".format(err), status=500,
                                reason="Internal Server Error")

    else:
        try:
            os.remove(path)
        except Exception as err:
            return HttpResponse("Remove failed: {}".format(err), status=500,
                                reason="Internal Server Error")

    return HttpResponse("Success.")
