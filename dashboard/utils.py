from api.common import init_connection
from accounts.cookies import verified_cookie_email

def get_duser(request):
    return verified_cookie_email(request, 'duser')

def get_user_email(request):
    return verified_cookie_email(request, 'duser')

def is_internal_user(request):
    duser = get_duser(request)
    if not duser:
        return False

    logname = duser[:duser.find("@")]
    try:
        conn, cursor = init_connection()
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
