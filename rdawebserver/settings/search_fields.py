import os
from urllib.parse import urlsplit, urlunsplit, urlencode
import datetime
from datetime import datetime
from typing import List, Mapping, Any

from .globus_settings import GLOBUS_DATA_ENDPOINT_ID, GLOBUS_FILE_MANAGER_URL

def search_highlights(result: List[Mapping[str, Any]]) -> List[Mapping[str, dict]]:
    """Prepare the most useful pieces of information for users on the search results page."""

    search_highlights_fields = [
        {
            "field_name": "description",
            "title": "Description"
        },
        {
            "field_name": "dataset_id",
            "title": "Dataset ID"
        },
        {
            "field_name": "format",
            "title": "Data Format"
        }
    ]

    search_highlights = list()

    date_fmt = "%Y-%m-%d %H:%M:%S"
    
    for field in search_highlights_fields:
        name = field['field_name']
        value = result[0].get(name)
        value_type = "str"

        # Parse a date if it's a date. All dates expected isoformat
        if name == "temporal_range_start":
            value = datetime.datetime.strptime(value, date_fmt)
            value_type = "date"
        elif name == "tags":
            value = ", ".join(value)

        # Add the value to the list
        search_highlights.append(
            {
                "name": name,
                "title": field['title'],
                "value": value,
                "type": value_type,
            }
        )
    return search_highlights

def title(result):
    """The title for this Globus Search subject"""
    return result[0]["title"]

def globus_app_link(result):
    """A Globus Webapp link for the transfer/sync button on the detail page"""
    url = result[0]["url"]
    parsed = urlsplit(url)
    query_params = {
        "origin_id": GLOBUS_DATA_ENDPOINT_ID,
        "origin_path": "/{}/".format(os.path.basename(parsed.path)),
    }
    gfm_parsed = urlsplit(GLOBUS_FILE_MANAGER_URL)

    return urlunsplit(
        (gfm_parsed.scheme, gfm_parsed.netloc, gfm_parsed.path, urlencode(query_params), "")
    )

def dataset_url(result):
    """ URL for the main dataset page """
    return result[0]["url"]

def https_url(result):
    """Add a direct download link to files over HTTPS"""
    parsed = urlsplit(result[0]["url"])
    path = os.path.join(parsed.path, "dataaccess")
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))

