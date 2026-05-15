import os
from datetime import datetime

from django.conf import settings
from django.shortcuts import render


def _format_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def filelist(request, subpath=''):
    base_path = getattr(settings, 'PELICAN_EXCHANGE_BASE_PATH', None)
    subpath = subpath.strip('/')
    entries = []
    error = None

    if not base_path:
        error = 'Exchange area is not configured (PELICAN_EXCHANGE_BASE_PATH is not set).'
    else:
        try:
            import pelicanfs

            list_path = base_path.rstrip('/') + ('/' + subpath if subpath else '') + '/'

            pelfs = pelicanfs.PelicanFileSystem("pelican://osg-htc.org")
            listing = pelfs.ls(list_path, detail=True)

            for entry in listing:
                name = os.path.basename(entry['name'].rstrip('/'))
                if not name:
                    continue
                is_dir = entry.get('type') == 'directory'
                size = entry.get('size', 0)
                modtime = entry.get('last_modified') or entry.get('modified')
                if isinstance(modtime, (int, float)):
                    modtime = datetime.fromtimestamp(modtime)

                entry_subpath = (subpath + '/' + name).strip('/') if subpath else name
                entries.append({
                    'name': name,
                    'is_dir': is_dir,
                    'size': _format_size(size) if not is_dir else None,
                    'modtime': modtime,
                    'subpath': entry_subpath,
                })
            entries.sort(key=lambda e: (not e['is_dir'], e['name'].lower()))

        except ImportError:
            error = 'pelicanfs is not installed.'
        except Exception as exc:
            error = str(exc)

    # Build breadcrumb trail
    breadcrumbs = [{'name': 'Exchange', 'subpath': ''}]
    parent_subpath = ''
    if subpath:
        parts = subpath.split('/')
        for i, part in enumerate(parts):
            breadcrumbs.append({'name': part, 'subpath': '/'.join(parts[: i + 1])})
        parent_subpath = '/'.join(parts[:-1])

    return render(request, 'exchange/filelist.html', {
        'entries': entries,
        'breadcrumbs': breadcrumbs,
        'current_subpath': subpath,
        'parent_subpath': parent_subpath,
        'error': error,
    })
