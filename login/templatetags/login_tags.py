import psycopg2

from django import template
from django.conf import settings
from home.utils import slug_list

register = template.Library()

@register.filter
def duser(value):
    if 'altID' in value and 'alttype' in value:
        return value['alttype'] + ":" + value['altID']
    if 'duser' in value:
        if ':' in value['duser']:
            idx = value['duser'].index(':')
            return value['duser'][0:idx]
        else:
            return value['duser']
    return ""

@register.filter
def ds_is_bookmarked(value, duser):
    conn = psycopg2.connect(**settings.RDADB['dssdb_config_pg'])
    cursor = conn.cursor()
    cursor.execute("select * from dsbookmarks where email = %s and dsid in %s", (duser, tuple(slug_list(value))))
    result = cursor.fetchone()
    conn.close()
    return not result == None
