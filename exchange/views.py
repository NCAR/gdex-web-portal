import os
import re
from datetime import datetime

from django.conf import settings
from django.shortcuts import render


def _format_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def _parse_readme(content):
    """Return (title, description) from a markdown README.

    title       — text of the first # heading
    description — text of the ## Description section (everything until the
                  next heading, stripped)
    """
    title = None
    description = None
    desc_lines = []
    in_description = False

    for line in content.splitlines():
        if title is None and line.startswith('# '):
            title = line[2:].strip()
        elif re.match(r'^##\s+description\s*$', line, re.IGNORECASE):
            in_description = True
            desc_lines = []
        elif in_description:
            if line.startswith('#'):
                break
            desc_lines.append(line)

    if desc_lines:
        description = '\n'.join(desc_lines).strip()

    return title, description


def filelist(request, subpath=''):
    base_path = getattr(settings, 'PELICAN_EXCHANGE_BASE_PATH', None)
    osdf_data_path = getattr(settings, 'OSDF_DATA_PATH', '').rstrip('/')
    subpath = subpath.strip('/')
    entries = []
    error = None
    readme_title = None
    readme_description = None

    # A top-level dataset page has exactly one path component
    is_dataset_page = bool(subpath) and '/' not in subpath

    if not base_path:
        error = 'Exchange area is not configured (PELICAN_EXCHANGE_BASE_PATH is not set).'
    else:
        try:
            import pelicanfs

            list_path = base_path.rstrip('/') + ('/' + subpath if subpath else '') + '/'

            pelfs = pelicanfs.PelicanFileSystem("pelican://osg-htc.org")
            listing = pelfs.ls(list_path, detail=True)

            has_readme = False
            for entry in listing:
                name = os.path.basename(entry['name'].rstrip('/'))
                if not name:
                    continue
                if not subpath and name == 'README.md':
                    continue
                if name == 'README.md':
                    has_readme = True

                is_dir = entry.get('type') == 'directory'
                size = entry.get('size', 0)
                modtime = entry.get('last_modified') or entry.get('modified')
                if isinstance(modtime, (int, float)):
                    modtime = datetime.fromtimestamp(modtime)

                entry_subpath = (subpath + '/' + name).strip('/') if subpath else name
                full_path = base_path.rstrip('/') + '/' + entry_subpath
                entries.append({
                    'name': name,
                    'is_dir': is_dir,
                    'size': _format_size(size) if not is_dir else None,
                    'modtime': modtime,
                    'subpath': entry_subpath,
                    'download_url': (osdf_data_path + full_path) if (not is_dir and osdf_data_path) else None,
                })
            entries.sort(key=lambda e: (not e['is_dir'], e['name'].lower()))

            if is_dataset_page and has_readme:
                readme_path = base_path.rstrip('/') + '/' + subpath + '/README.md'
                try:
                    content = pelfs.cat(readme_path).decode('utf-8')
                    readme_title, readme_description = _parse_readme(content)
                except Exception:
                    pass

        except ImportError:
            error = 'pelicanfs is not installed.'
        except Exception as exc:
            error = str(exc)

    parent_subpath = ''
    if subpath:
        parts = subpath.split('/')
        parent_subpath = '/'.join(parts[:-1])

    return render(request, 'exchange/filelist.html', {
        'entries': entries,
        'current_subpath': subpath,
        'parent_subpath': parent_subpath,
        'readme_title': readme_title,
        'readme_description': readme_description,
        'error': error,
    })
