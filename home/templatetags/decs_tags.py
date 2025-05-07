from django import template
import psycopg2
from django.conf import settings
from pathlib import Path

register = template.Library()

def ds_slug(value):
    return value.replace('.', '-')

register.filter('ds_slug', ds_slug)

def is_active(value, page_url):
    if isinstance(value, dict):
        if value['url'] in page_url:
            return True
    elif isinstance(value, list):
        for x in value:
            if x['url'] in page_url:
                return True
    return False

register.filter('is_active', is_active)

def is_remote_url(value):
    s = value[7:19]
    if s == 'rda.ucar.edu':
        return False
    s = value[8:20]
    if s == 'rda.ucar.edu':
        return False
    return True

register.filter('is_remote_url', is_remote_url)

@register.simple_tag
def countries():
    dssdb_config = settings.RDADB['dssdb_config_db']
    conn = psycopg2.connect(**dssdb_config)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    q = "select token, description from countries order by description"
    cursor.execute(q)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

@register.simple_tag
def include_strip(value):
    lst = value.split("/")
    if len(lst) != 2:
        return ""

    file = "/usr/local/rdaweb/" + lst[0] + "/templates/" + lst[0] + "/" + lst[1]
    path = Path(file)
    if not path.is_file():
        return ""

    with open(file) as f:
        lines = f.readlines()
        f.close()

    value = ""
    for line in lines:
        value += line.strip(' \n')

    return value

@register.simple_tag
def dictKeyLookup(the_dict, key, subkey=None):
    # Try to fetch from the dict, and if it's not found return an empty string.
    if subkey is None:
        return the_dict.get(key, '') 
    else:
        return the_dict.get(key).get(subkey)

@register.simple_tag
def getORCID(extra_data_dict):
    try:
        if 'orcid' in extra_data_dict:
            #orcid.0.extra_data
            return extra_data_dict['orcid'][0].extra_data.get('orcid-identifier').get('uri')
        else:
            identities = extra_data_dict['globus'][0].extra_data['identity_set']
            for identity in identities:
                if 'identity_provider' in identity and identity['identity_provider'] == '0519206d-f21c-4771-990a-282a12bb666b':
                    return identity['username']
    except:
        return "No ORCID Found"

