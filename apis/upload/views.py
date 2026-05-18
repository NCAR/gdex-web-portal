import os
import pathlib
import subprocess
import urllib.parse

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
def upload(request):
    parts = request.META['HTTP_HOST'].split(".")
    if parts[0] != "api":
        return render(request, "404.html", status=404)

    if 'API-key' not in request.headers:
        return HttpResponse("Missing API key.", status=400,
                            reason="Bad Request")

    if request.headers['API-key'] not in settings.LOCAL_API_KEYS['upload']:
        return HttpResponse("Invalid API key.", status=403, reason="Forbidden")

    if 'file' in request.FILES and 'path' in request.POST:
        is_good_path = good_path(
                (settings.LOCAL_API_KEYS['upload']
                 [request.headers['API-key']]), request.POST['path'])
        if not is_good_path:
            return HttpResponse("Invalid path.", status=400,
                                reason="Bad Request")

        path = os.path.join(
                settings.LOCAL_API_KEYS['upload'][request.headers['API-key']],
                request.POST['path'])
        idx = path.rfind("/")
        if idx < 0:
            return HttpResponse("Invalid path.", status=400,
                                reason="Bad Request")

        try:
            pathlib.Path(path[0:idx]).mkdir(parents=True, exist_ok=True)
            out_len = 0
            MAX_OUT = 60000000
            with open(path, "wb") as f:
                for chunk in request.FILES['file']:
                    out_len += len(chunk)
                    if (out_len <= MAX_OUT):
                        f.write(chunk)
                    else:
                        break

            if out_len > MAX_OUT:
                os.remove(path)
                return HttpResponse("File is too large.", status=413,
                                    reason="Content Too Large")

        except Exception as err:
            return HttpResponse("An error occurred: *{}*.".format(err),
                                status=500, reason="Internal Server Error")

        return HttpResponse("Success.")

    if len(request.META['QUERY_STRING']) > 0:
        if request.META['QUERY_STRING'][0:4] == "list":
            parts = request.META['QUERY_STRING'].split("=")
            lpath = urllib.parse.unquote(parts[-1])
            is_good_path = good_path(
                    (settings.LOCAL_API_KEYS['upload']
                     [request.headers['API-key']]),
                    lpath)
            if is_good_path:
                path = os.path.join(
                        (settings.LOCAL_API_KEYS['upload']
                         [request.headers['API-key']]),
                        lpath)
                o = subprocess.run("ls -FGAhlp " + path, shell=True,
                                   capture_output=True)
                err = o.stderr.decode("utf-8")
                if len(err) > 0:
                    return HttpResponse("Not found.", status=404,
                                        reason="Not Found")

                lines = o.stdout.decode("utf-8").splitlines()
                out_lines = []
                for line in lines:
                    parts = line.split()
                    if len(parts) > 7:
                        out_lines.append(" ".join(parts[3:8]))

                return HttpResponse("\n".join(out_lines))

    return HttpResponse("Upload file missing.",
                        status=400, reason="Bad Request")
