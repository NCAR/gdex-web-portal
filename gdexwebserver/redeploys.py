import json
import subprocess

from metaman import local_settings as metaman_settings

from django.conf import settings
from django.http import HttpResponse


def respond(o, touch=False):
    o = (
            o.stdout.decode("utf-8").replace("\n", "<br>") + "<br>" +
            o.stderr.decode("utf-8").replace("\n", "<br>"))
    if touch:
        subprocess.run("touch /usr/local/gdexweb/gdexwebserver/wsgi.py",
                       shell=True)
    return HttpResponse(o)


def redeploy_dsgen(ident):
    if len(ident) == 5:
        o = subprocess.run((
                "pip install git+https://github.com/rda-dattore/testpkg#"
                "subdirectory=dsgen"), shell=True, capture_output=True)
    else:
        o = subprocess.run((
                "/usr/local/gdexweb/bin/dsgen --mdb='" +
                json.dumps(settings.RDADB['metadata_config_pg']) + "' --wdb='"
                + json.dumps(settings.RDADB['wagtail2_config_pg']) + "' " +
                ident[5:]),
                shell=True, capture_output=True)

    return respond(o)


def redeploy_libpkg():
    o = subprocess.run((
            "pip install git+https://github.com/rda-dattore/testpkg#"
            "subdirectory=libpkg"), shell=True, capture_output=True)
    return respond(o, touch=True)


def redeploy_spellchecker():
    o = subprocess.run((
            "pip install git+https://github.com/NCAR/rda-dsspellchecker; "
            "/usr/local/gdexweb/bin/dsspellchecker_manage build_db"),
            shell=True, capture_output=True)
    return respond(o, touch=True)


def redeploy_doi_manager():
    o = subprocess.run((
            "pip install git+https://github.com/NCAR/rda-doi_manager; "
            "/usr/local/gdexweb/bin/doi_manage " +
            metaman_settings.doi_manager_auth_key + " configure "
            "/data/local/doi_manager/settings.txt"),
            shell=True, capture_output=True)
    return respond(o)


def redeploy(request, pkg):
    if pkg[0:5] == "dsgen":
        return redeploy_dsgen(pkg)
    elif pkg == "libpkg":
        return redeploy_libpkg()
    elif pkg == "spellchecker":
        return redeploy_spellchecker()
    elif pkg == "doi_manager":
        return redeploy_doi_manager()

    return HttpResponse("bad request")
