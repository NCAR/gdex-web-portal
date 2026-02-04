from django import template
from django.conf import settings
import math
import re
import os
from pathlib import Path

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

@register.filter
def get_extension(value):
    """Return the file extension of the given filename"""
    if not value:
        return ''
    return Path(value).suffix.lstrip('.').lower()

@register.filter
def get_data_format_from_row(row):
    """
    Given a static filelist row entry, return the data format.
    The row is a list of dictionaries with 'name' and 'value' keys.
    """
    if not row or not isinstance(row, list):
        return ''
    for item in row:
        name = item.get('name', '').lower()
        if name == 'data format':
            return item.get('value', '').lower()
    return ''

@register.inclusion_tag('datasets/filelist-zarr-catalogs.html', takes_context=True)
def show_arco_catalogs(context):
    """
    Takes the context from filelist.html and returns a list of dicts with ARCO file information
    (data format, size, date archived, file path, file name, file url, file note).
    """
    groups = []
    for i, group in enumerate(context['data']['groups']):
        file_rows = []
        for row in context['data']['groups'][i]['rows']:
            file_info = { 'data_format': '', 'size': None, 'date_archived': '', 'file_path': '', 'file_name': '', 'file_url': '', 'file_note': None }
            for item in row:
                name = item.get('name', '').lower()
                if name == 'data format':
                    file_info['data_format'] = item.get('value', '').lower()
                elif name == 'size':
                    file_info['size'] = item.get('value', '')
                elif name == 'date archived':
                    file_info['date_archived'] = item.get('value', '')
                elif 'data_path' in item:
                    file_info['file_path'] = item.get('data_path', '')
                    file_info['file_name'] = item.get('value', '')
                    url = item.get('url', '')
                    if '-posix' in url:
                        url = os.path.join(settings.GDEX_SHORT_PATH, 'data', file_info['file_path'].strip('/'))
                    elif '-http' in url:
                        url = 'https://' + settings.GLOBUS_DATA_DOMAIN.strip('/') + file_info['file_path']
                    elif '-osdf' not in url: # Some assets don't have posix
                        url = os.path.join(settings.GDEX_SHORT_PATH, 'data', file_info['file_path'].strip('/'))
                    file_info['file_url'] = url
                    file_info['file_note'] = item.get('note', None)

            file_rows.append(file_info)
        groups.append({'files':file_rows, 'group_name': group['group_id']})

    return { 'groups': groups }
