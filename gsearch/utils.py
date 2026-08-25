from django.conf import settings
from api.common import get_search_config, init_connection, close_connection

import logging
logger = logging.getLogger(__name__)

def get_time_and_spatial_resolution_sort_indices():
    """
    Get the time and spatial resolution sort indices from the search configuration.
    """
    search_config = get_search_config()
    con, cur = init_connection(config=search_config)
    q = "select * from search.time_resolution_sort"
    try:
        cur.execute(q)
        time_resolution_sort_indices = cur.fetchall()
    except Exception as e:
        logger.error(f"Error fetching time resolution sort indices: {e}")
        time_resolution_sort_indices = {}

    if time_resolution_sort_indices:
        time_resolution_sort_indices = {row[0]: row[1] for row in time_resolution_sort_indices}

    q = "select * from search.grid_resolution_sort"
    try:
        cur.execute(q)
        grid_resolution_sort_indices = cur.fetchall()
    except Exception as e:
        logger.error(f"Error fetching grid resolution sort indices: {e}")
        grid_resolution_sort_indices = {}

    close_connection(con, cur)

    if grid_resolution_sort_indices:
        grid_resolution_sort_indices = {row[0]: row[1] for row in grid_resolution_sort_indices}

    return time_resolution_sort_indices, grid_resolution_sort_indices

def sort_by_separator(strings, sep, num=1):
    """
    Given a list of strings with a specified separator 'sep', 
    splits each string by the specified separator,
    and sorts the list based on the -num substring.
    If the separator is not found, the whole string is used for sorting.

    Examples:
        # sort list of strings by the last element after splitting the string
        sort_by_separator(["a > 3", "b > 2", "c > 1"], ">", 1)
        # returns ["c > 1", "b > 2", "a > 3"]

        # sort list of strings by the second element after splitting the string
        sort_by_separator(["cat > 2 > a", "dog > 1 > c", "elephant > 3 > b"], ">", 2)
        # returns ["dog > 1 > c", "cat > 2 > a", "elephant > 3 > b"]
    """
    return sorted(strings, key=lambda s: s.split(sep)[-num] if sep in s else s)
