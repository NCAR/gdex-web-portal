from django import template
from django.conf import settings
import math
import re
import os

register = template.Library()

@register.filter
def format_dsid(dsid, remove_ds=None):
    if remove_ds is None:
        ds = 'ds'
    else:
        ds = ''
    
    # check for format 'dnnnnnn'
    ms = re.match(r'^([a-z]{1})(\d{3})(\d{3})$', dsid)
    if ms:
        if settings.NEW_DATASET_ID:
            return dsid
        else:
            return '{}{:03d}.{}'.format(ds, int(ms.group(2)), int(ms.group(3)))
    
    # check for legacy format 'dsnnn.n', 'dsnnn-n', 'nnn.n', and
    # 'nnn-n'.  Change dash '-' to dot '.' if necessary.
    ms = re.match(r'^(ds)?(\d{3})(-|\.)(\d{1})$', dsid)
    if ms:
        if settings.NEW_DATASET_ID:
            return 'd{:03d}{:03d}'.format(int(ms.group(2)), int(ms.group(4)))
        else:
            return '{}{}.{}'.format(ds, ms.group(2), ms.group(4))

@register.filter
def remove_datadsid(path):
    match = re.match(r'(.*/ds\d{3}\.\d{1})(.*)', path)
    if match:
        return match.group(2)
    match = re.match(r'(.*/d\d{6})(.*)', path)
    if match:
        return match.group(2)
    return None

@register.filter
def split_path(request):
    paths = request.path.split('/')[1:-1]
    full_paths = []
    cur_full_path = ''
    for path in paths:
        cur_full_path += '/'+path
        full_paths.append(cur_full_path)
    merged_list = [(paths[i], full_paths[i]) for i in range(0, len(paths))]
    return merged_list

@register.filter
def dsid_dash_to_dot(dsid):
    if dsid.lower().startswith('ds'):
       return dsid.replace('-','.')
    return dsid

@register.filter
def basename(value):
    return os.path.basename(value)

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_dsid_from_url(url):
    # check for 'dnnnnnn'
    match = re.search('([a-z]\d{6})', url)
    if match is not None:
        return match.group(0)
    # check for 'dsnnn.n'
    match = re.search('(ds\d{3}.\d{1})', url)
    if match is not None:
        return match.group(0)
    return None

@register.filter
def make_glade_URL(uri):
    if (uri.find('/',0,1) != -1):
        uri = uri.replace('/','',1)
    url = os.path.join(settings.RDA_CANONICAL_DATA_PATH, uri)
    if '/OS/' in url:
        return re.sub('.*/OS/', settings.NCAR_STRATUS_URL, url)
    return url

@register.filter
def convert_bytes(bytes):
    size_bytes = int(bytes)
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])
        
@register.simple_tag
def has_alt_index(data):
    for i in data:
        if i['hfile'] == 'alt_index.html':
            return True
    return False

@register.filter
def template_exists(value):
    try:
        template.loader.get_template(value)
        return True
    except template.TemplateDoesNotExist:
        return False

@register.simple_tag
def truncate_facet(value, separator='>', num=1):
    """ Split a facet string value by the given separator,
        and return the last num element(s) joined by the separator.

        Example usage in template:
        {% truncate_facet 'a > b > c > d' %}                       # returns 'd'
        {% truncate_facet 'a > b > c > d' separator='>', num=2 %}  # returns 'c > d'
        {% truncate_facet 'a > b > c > d' separator='>', num=1 %}  # returns 'd'
        {% truncate_facet 'a > b > c > d' separator='>', num=0 %}  # returns 'a > b > c > d'
    """
    if not value:
        return ''
    if isinstance(value, list):
        return value[-num:]
    if isinstance(value, str):
        value_list = value.split(separator)
        if len(value_list) > num:
            return separator.join(value_list[-num:]).strip()
        else:
            return value
    return value
