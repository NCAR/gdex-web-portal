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


def _parse_xrootd_url(url):
    """Split root://server//path into (server_url, base_path)."""
    m = re.match(r'(root://[^/]+)(.*)', url)
    if not m:
        raise ValueError(f"Invalid XROOTD_EXCHANGE_URL: {url!r}")
    return m.group(1), m.group(2) or '/'


def filelist(request, subpath=''):
    xrootd_url = getattr(settings, 'XROOTD_EXCHANGE_URL', None)
    entries = []
    error = None

    if not xrootd_url:
        error = 'Exchange area is not configured (XROOTD_EXCHANGE_URL is not set).'
    else:
        try:
            from XRootD import client
            from XRootD.client.flags import DirListFlags, StatInfoFlags

            server, base_path = _parse_xrootd_url(xrootd_url)
            subpath = subpath.strip('/')
            list_path = base_path.rstrip('/') + ('/' + subpath if subpath else '')

            fs = client.FileSystem(server)
            status, listing = fs.dirlist(list_path, DirListFlags.STAT)

            if not status.ok:
                error = f"Could not list directory: {status.message}"
            else:
                for entry in listing.dirlist:
                    is_dir = bool(entry.statinfo.flags & StatInfoFlags.IS_DIR)
                    entry_subpath = (subpath + '/' + entry.name).strip('/') if subpath else entry.name
                    entries.append({
                        'name': entry.name,
                        'is_dir': is_dir,
                        'size': _format_size(entry.statinfo.size) if not is_dir else None,
                        'modtime': datetime.fromtimestamp(entry.statinfo.modtime),
                        'subpath': entry_subpath,
                    })
                entries.sort(key=lambda e: (not e['is_dir'], e['name'].lower()))

        except ImportError:
            error = 'XRootD Python bindings are not installed.'
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
