import subprocess

from django.http import HttpResponse


def redeploy_spellchecker():
    o = subprocess.run((
            "pip install git+https://github.com/NCAR/rda-dsspellchecker; "
            "/usr/local/gdexweb/bin/dsspellchecker_manage build_db"),
            shell=True, capture_output=True)
    o = (
            o.stdout.decode("utf-8").replace("\n", "<br>") + "<br>" +
            o.stderr.decode("utf-8").replace("\n", "<br>"))
    return HttpResponse(o)


def redeploy(request, pkg):
    if pkg == "spellchecker":
        return redeploy_spellchecker()

    return HttpResponse("bad request")
