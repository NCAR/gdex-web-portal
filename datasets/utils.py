from django.http import HttpResponse
from django.conf import settings
import psycopg2
from datetime import datetime
from wagtail.models import Page
from datasets.models import CustomSubsetPage

from logging import getLogger
logger = getLogger(__name__)

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
    return 'http://127.0.0.1:8080'

def get_custom_subset_context(dsid, gindex=None):
    # Get dataset context needed for custom subset page
    context = {}
    query_params = {'dsid': dsid}
    if gindex is not None:
        query_params['gindex'] = gindex
    qs = Page.objects.type(CustomSubsetPage).filter(**query_params).live().specific()
    if len(qs) > 0:
        context = {
            'header': qs[0].header,
            'description': qs[0].description,
        }
    
    dsperiod = get_dataset_period(dsid, gindex)
    if dsperiod:
        context.update(dsperiod)

    return context

def get_dataset_period(dsid, gindex=None):
    # Get the dataset period from the database
    query = "SELECT MIN(CONCAT(date_start, ' ', time_start)) as datetime_start, MAX(CONCAT(date_end, ' ', time_end)) as datetime_end FROM dsperiod WHERE dsid = %s"
    if gindex is not None:
        query += " AND gindex::text LIKE %s"
        cond = (dsid, f"{gindex}%")
    else:
        cond = (dsid,)

    conn = psycopg2.connect(**settings.RDADB['dssdb_config_pg'])
    cursor = conn.cursor()
    cursor.execute(query, cond)
    result = cursor.fetchone()
    conn.close()

    format_str = "%Y-%m-%d %H:%M:%S"  # The format

    # if dsid = 'd351000' enforce datetime_start = 1999-10-01 and datetime_end to be the current datetime
    if dsid == 'd351000':
        datetime_start = datetime.strptime('1999-10-01 00:00:00', format_str)
        datetime_end = datetime.now()
    else:
        datetime_start = datetime.strptime(result[0], format_str) if result[0] else None
        datetime_end = datetime.strptime(result[1], format_str) if result[1] else None


    date_start = datetime_start.date().strftime("%Y-%m-%d") if datetime_start else None
    date_end = datetime_end.date().strftime("%Y-%m-%d") if datetime_end else None
    time_start = datetime_start.time().strftime("%H:%M:%S") if datetime_start else None
    time_end = datetime_end.time().strftime("%H:%M:%S") if datetime_end else None

    if result:
        return {
            'date_start': date_start,
            'date_end': date_end,
            'time_start': time_start,
            'time_end': time_end
        }
    return None
