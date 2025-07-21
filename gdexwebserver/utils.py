import os
import shutil
import tempfile


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


def utils(request):
    pass
