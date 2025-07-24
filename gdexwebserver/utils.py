import os
import pathlib
import shutil
import tempfile

from django.http import HttpResponse


def make_tempdir():
    try:
        tdir_name = tempfile.mkdtemp(dir="/data/ptmp")
        os.chmod(tdir_name, 0o777)
        return tdir_name
    except Exception:
        return ""


def remove_tempdir(tdir_name):
    try:
        shutil.rmtree(tdir_name)
    except Exception:
        pass


def upload(request):
    if 'file' in request.FILES and 'path' in request.POST:
        idx = request.POST['path'].rfind("/")
        if idx < 0:
            return HttpResponse("Invalid path.")

        try:
            pathlib.Path(request.POST['path'][0:idx]).mkdir(parents=True,
                                                     exist_ok=True)
            out_len = 0
            MAX_OUT = 30000000
            with open(request.POST['path'], "wb") as f:
                for chunk in request.FILES['file']:
                    out_len += len(chunk)
                    if (out_len <= MAX_OUT):
                        f.write(chunk)
                    else:
                        break

            if out_len > MAX_OUT:
                os.remove(request.POST['path'])
                return HttpResponse("File is too large.")

        except Exception as err:
            return HttpResponse("An error occurred: *{}*.".format(err))

        return HttpResponse("Success.")

    return HttpResponse("Bad request.")
