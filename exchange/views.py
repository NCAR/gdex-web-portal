import os
import re
from datetime import datetime
from urllib.parse import quote, urlparse

import pelicanfs
from django.conf import settings
from django.shortcuts import render


def _format_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def _parse_readme(content):
    """Return (title, description) parsed from a markdown README.

    title       — text of the first heading (any level)
    description — body of the first heading named 'description' (any level),
                  collected until the next heading
    """
    title = None
    desc_lines = []
    in_description = False

    for line in content.splitlines():
        if title is None and re.match(r'^#+\s', line):
            title = re.sub(r'^#+\s+', '', line).strip()
        elif re.match(r'^#+\s+description\s*$', line, re.IGNORECASE):
            in_description = True
            desc_lines = []
        elif in_description:
            if re.match(r'^#+\s', line):
                break
            desc_lines.append(line)

    description = '\n'.join(desc_lines).strip() or None
    return title, description


def _get_pelican_fs():
    return pelicanfs.PelicanFileSystem("pelican://osg-htc.org")


def _list_directory(pelfs, list_path, subpath, base_path, osdf_data_path, hide_readme_at_root):
    """List a directory and return a sorted list of entry dicts.

    Directories come first, then files, both sorted alphabetically.
    README.md is excluded when listing the exchange root.
    """
    entries = []
    has_readme = False

    for entry in pelfs.ls(list_path, detail=True):
        name = os.path.basename(entry['name'].rstrip('/'))
        if not name or name.startswith('.'):
            continue
        if hide_readme_at_root and name == 'README.md':
            continue
        if name == 'README.md':
            has_readme = True

        is_dir = entry.get('type') == 'directory'
        is_zarr = is_dir and name.endswith('.zarr')
        size = entry.get('size', 0)
        modtime = entry.get('last_modified') or entry.get('modified')
        if isinstance(modtime, (int, float)):
            modtime = datetime.fromtimestamp(modtime)

        entry_subpath = (subpath + '/' + name).strip('/') if subpath else name
        full_path = base_path.rstrip('/') + '/' + entry_subpath
        download_url = (osdf_data_path + full_path) if ((not is_dir or is_zarr) and osdf_data_path) else None
        file_path = urlparse(download_url).path.removeprefix('/ncar') if download_url else None
        entries.append({
            'name': name,
            'is_dir': is_dir,
            'is_zarr': is_zarr,
            'size': _format_size(size) if not is_dir else None,
            'modtime': modtime,
            'subpath': entry_subpath,
            'file_path': file_path,
            'download_url': download_url,
        })

    entries.sort(key=lambda e: (not e['is_dir'], e['name'].lower()))
    return entries, has_readme


def _read_dataset_readme(pelfs, base_path, subpath):
    """Fetch and parse README.md from a dataset directory.

    Returns (title, description) or (None, None) if the file cannot be read.
    """
    readme_path = base_path.rstrip('/') + '/' + subpath + '/README.md'
    try:
        content = pelfs.cat(readme_path).decode('utf-8')
        return _parse_readme(content)
    except Exception:
        return None, None


def filelist(request, subpath=''):
    base_path = getattr(settings, 'PELICAN_EXCHANGE_BASE_PATH', None)
    osdf_data_path = getattr(settings, 'OSDF_DIRECTOR_URL', '').rstrip('/')
    subpath = subpath.strip('/')

    entries = []
    error = None
    readme_title = None
    readme_description = None

    if subpath and any(part in ('.', '..') for part in subpath.split('/')):
        error = 'Invalid path.'
    else:
        # A top-level dataset page has exactly one path component (e.g. "my-dataset")
        is_dataset_page = bool(subpath) and '/' not in subpath

        try:
            pelfs = _get_pelican_fs()
            list_path = base_path.rstrip('/') + ('/' + subpath if subpath else '') + '/'

            entries, has_readme = _list_directory(
                pelfs, list_path, subpath, base_path, osdf_data_path,
                hide_readme_at_root=not subpath,
            )

            # Read README metadata only on top-level dataset pages
            if is_dataset_page and has_readme:
                readme_title, readme_description = _read_dataset_readme(pelfs, base_path, subpath)

        except Exception as exc:
            error = str(exc)

    globus_endpoint_id = getattr(settings, 'GLOBUS_DATA_ENDPOINT_ID', '')
    exchange_path = '/exchange/' + (subpath.strip('/') + '/' if subpath else '')
    globus_url = (
        'https://app.globus.org/file-manager'
        '?origin_id=' + globus_endpoint_id +
        '&origin_path=' + quote(exchange_path, safe='')
    )

    return render(request, 'exchange/filelist.html', {
        'entries': entries,
        'current_subpath': subpath,
        'readme_title': readme_title,
        'readme_description': readme_description,
        'error': error,
        'globus_url': globus_url,
    })
