from api.common import init_connection_new

def get_duser(request):
    if 'duser' not in request.COOKIES:
        return None

    duser = request.COOKIES['duser']
    duser = duser if ":" not in duser else duser[:duser.find(":")]
    return duser

def get_user_email(request):
    email = None
    if 'duser' in request.COOKIES:
        email = request.COOKIES.get('duser')
        if ':' in email:
            idx = email.index(':')
            email = email[0:idx]
    return email

def is_internal_user(request):
    duser = get_duser(request)
    if not duser:
        return False

    logname = duser[:duser.find("@")]
    try:
        conn, cursor = init_connection_new()
        cursor.execute("select stat_flag from dssdb.dssgrp where logname = %s",
                       (logname, ))
        res = cursor.fetchone()
        if res is not None and res[0] == "C":
            return True
    except Exception:
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return False
