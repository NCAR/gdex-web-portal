import os
from urllib.parse import urlsplit, urlunsplit, urlencode
from datetime import datetime
from typing import List, Mapping, Any

from .globus_settings import GLOBUS_DATA_ENDPOINT_ID, GLOBUS_FILE_MANAGER_URL


# ---------------------------------------------------------------------------
# Display name maps (shared by multiple extractors)
# ---------------------------------------------------------------------------

_FORMAT_DISPLAY = {
    'netcdf4':            'NetCDF4',
    'netcdf':             'NetCDF',
    'proprietary_ascii':  'ASCII',
    'proprietary_binary': 'Binary',
    'wmo_grib1':          'GRIB1',
    'noaa_imma':          'NOAA IMMA',
    'dss_wmssc':          'DSS WMSSC',
}

_DATA_TYPE_DISPLAY = {
    'grid':                 'Grid',
    'platform_observation': 'Platform Observation',
    'satellite':            'Satellite',
    'model_output':         'Model Output',
    'reanalysis':           'Reanalysis',
    'derived_product':      'Derived Product',
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_time_res(raw):
    """'T : Monthly - < Annual'  →  'Monthly'"""
    return raw.split(' : ')[1].split(' - ')[0].strip() if ' : ' in raw else raw

def _fmt_date(raw):
    """'2023-01-15' or '2023-01-15T...' → '01-2023', or None on failure."""
    try:
        return datetime.strptime(str(raw)[:10], '%Y-%m-%d').strftime('%m-%Y')
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Existing field extractors — unchanged
# ---------------------------------------------------------------------------

def search_highlights(result: List[Mapping[str, Any]]) -> List[Mapping[str, dict]]:
    """Prepare the most useful pieces of information for users on the search results page."""

    search_highlights_fields = [
        {"field_name": "description", "title": "Description"},
        {"field_name": "dataset_id",  "title": "Dataset ID"},
        {"field_name": "format",      "title": "Data Format"},
        {"field_name": "tags",        "title": "Tags"},
    ]

    highlights = []
    for field in search_highlights_fields:
        name  = field['field_name']
        value = result[0].get(name)
        highlights.append({
            "name":                    name,
            "title":                   field['title'],
            "value":                   value,
            "type":                    "str",
            "search_filter_query_key": f"filter-match-all.{name}",
        })
    return highlights


def title(result):
    """The title for this Globus Search subject."""
    return result[0]["title"]


def globus_app_link(result):
    """A Globus Webapp link for the transfer/sync button on the detail page."""
    url    = result[0]["url"]
    parsed = urlsplit(url)
    query_params = {
        "origin_id":   GLOBUS_DATA_ENDPOINT_ID,
        "origin_path": "/{}/".format(os.path.basename(parsed.path)),
    }
    gfm_parsed = urlsplit(GLOBUS_FILE_MANAGER_URL)
    return urlunsplit(
        (gfm_parsed.scheme, gfm_parsed.netloc, gfm_parsed.path, urlencode(query_params), "")
    )


def dataset_url(result):
    """URL path for the main dataset page."""
    return urlsplit(result[0]["url"]).path


def https_url(result):
    """Direct download link to files over HTTPS."""
    parsed = urlsplit(result[0]["url"])
    path   = os.path.join(parsed.path, "dataaccess")
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def dataset_type(result):
    """Dataset type flag: 'P' (primary) or 'H' (historical)."""
    if not result or "dataset_type" not in result[0]:
        return None
    return result[0]["dataset_type"]


# ---------------------------------------------------------------------------
# New field extractors for the redesigned result cards
# ---------------------------------------------------------------------------

def summary(result):
    """Full description text — shown in the hover popover on result cards."""
    return (result[0].get('description') or '').strip()


def doi(result):
    """Dataset DOI string."""
    return result[0].get('doi') or 'N/A'


def dataset_id(result):
    """Short dataset identifier, e.g. 'd123456'."""
    return result[0].get('dataset_id') or 'N/A'


def size(result):
    """Total data volume as a human-readable string."""
    return result[0].get('total_volume') or 'N/A'


def data_type_display(result):
    """Comma-separated display labels for the data_type list field."""
    raw   = result[0].get('data_type') or []
    parts = [_DATA_TYPE_DISPLAY.get(str(t), str(t).replace('_', ' ').title()) for t in raw]
    return ', '.join(parts) or 'N/A'


def temporal_range(result):
    """Formatted date range string: 'MM-YYYY – MM-YYYY'."""
    start = _fmt_date(result[0].get('temporal_range_start'))
    end   = _fmt_date(result[0].get('temporal_range_end'))
    if start and end:
        return f'{start} – {end}'
    if start:
        return f'{start} – present'
    if end:
        return f'– {end}'
    return 'N/A'


def data_source(result):
    """First organisation from data_contributors, trimmed before the first ' > '."""
    contributors = result[0].get('data_contributors') or []
    if not contributors:
        return 'N/A'
    return contributors[0].split(' > ')[0].strip() or 'N/A'


def data_format_display(result):
    """Comma-separated display labels for the format list field."""
    raw   = result[0].get('format') or []
    parts = [_FORMAT_DISPLAY.get(str(f).lower(), str(f)) for f in raw]
    return ', '.join(parts) or 'N/A'


def time_resolution_display(result):
    """Comma-separated parsed time resolution labels (deduplicated)."""
    raw   = result[0].get('time_resolution') or []
    parts = [_parse_time_res(r).title() for r in raw]
    seen  = set()
    unique = [p for p in parts if not (p in seen or seen.add(p))]
    return ', '.join(unique) or 'N/A'
