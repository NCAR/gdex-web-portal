import subprocess

from django.http import HttpResponse


def respond(o):
    o = (
            o.stdout.decode("utf-8").replace("\n", "<br>") + "<br>" +
            o.stderr.decode("utf-8").replace("\n", "<br>"))
    subprocess.run("touch /data/local/gdexweb/gdexwebserver/wsgi.py",
                   shell=True)
    return HttpResponse(o)


def redeploy_dsgen():
    o = subprocess.run((
            "pip install git+https://github.com/rda-dattore/testpkg#"
            "subdirectory=dsgen"), shell=True, capture_output=True)
    return respond(o)


def redeploy_libpkg():
    o = subprocess.run((
            "pip install git+https://github.com/rda-dattore/testpkg#"
            "subdirectory=libpkg"), shell=True, capture_output=True)
    return respond(o)


def redeploy_spellchecker():
    o = subprocess.run((
            "pip install git+https://github.com/NCAR/rda-dsspellchecker; "
            "/usr/local/gdexweb/bin/dsspellchecker_manage build_db"),
            shell=True, capture_output=True)
    return respond(o)


def redeploy(request, pkg):
    if pkg == "dsgen":
        return redeploy_dsgen()
    elif pkg == "libpkg":
        return redeploy_libpkg()
    elif pkg == "spellchecker":
        return redeploy_spellchecker()

    return HttpResponse("bad request")
