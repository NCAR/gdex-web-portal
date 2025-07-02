def get_duser(request):
    if 'duser' not in request.COOKIES:
        return None

    duser = request.COOKIES['duser']
    duser = duser if ":" not in duser else duser[:duser.find(":")]
    return duser
