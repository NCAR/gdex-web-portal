import subprocess

from django.http import HttpResponse


def redeploy_spellchecker():
    o = subprocess.run((
            "source /usr/local/rdaweb/bin/activate; "
            "pip install git+https://github.com/NCAR/rda-dsspellchecker; "
            "dsspellchecker_manage build_db"), shell=True,
            capture_output=True, env={'PYTHONPATH': "/usr/local/rdaweb"})
    o = (
            o.stdout.decode("utf-8").replace("\n", "<br>") + "<br>" +
            o.stderr.decode("utf-8").replace("\n", "<br>"))

    return HttpResponse(o)


def redeploy(request, pkg):
    if pkg == "spellchecker":
        return redeploy_spellchecker()

    return HttpResponse("bad request")
