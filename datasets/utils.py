import json
import socket
from django.http import HttpResponse
from django.conf import settings
import psycopg2
from api.common import format_dataset_id


def ng_gdex_id(dsid):
    if dsid.find("ds") == 0:
        dsid = dsid[2:]

    if dsid[3] == '.' or dsid[3] == '-':
        dsid = "d" + dsid[0:3] + "00" + dsid[4:5]

    return dsid


def bookmark(request, dsid):
    img_src = "hollow-black-star.png"
    if not 'duser' in request.COOKIES:
        return HttpResponse(img_src)

    conn = psycopg2.connect(**settings.RDADB['dssdb_config_pg'])
    cursor = conn.cursor()
    email = request.COOKIES['duser']
    if ':' in email:
        idx = email.index(':')
        email = email[0:idx]

    cursor.execute("select * from dsbookmarks where email = %s and dsid = %s", (email, ng_gdex_id(dsid)))
    result = cursor.fetchone()
    if result == None:
        """ Bookmark doesn't exist, so set it """
        cursor.execute("insert into dsbookmarks (email, dsid) values (%s, %s)", (email, ng_gdex_id(dsid)))
        img_src = "gold-star.png"

    else:
        """ Bookmark exists, so delete it """
        cursor.execute("delete from dsbookmarks where email = %s and dsid = %s", (email, ng_gdex_id(dsid)))

    conn.commit()
    conn.close()
    return HttpResponse(img_src)


def get_hostname():
    hostname = socket.gethostname()
    if 'prod' in hostname:
        return 'https://rda.ucar.edu'
    return 'https://'+hostname
