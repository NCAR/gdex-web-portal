from django.conf import settings
from api.common import get_search_config, init_connection_new, close_connection

import logging
logger = logging.getLogger(__name__)

def get_time_resolution_sort_indices():
    """
    Get the time resolution sort indices from the search configuration.
    """
    search_config = get_search_config()
    con, cur = init_connection_new(config=search_config)
    q = "select * from search.time_resolution_sort"
    try:
        cur.execute(q)
        time_resolution_sort_indices = cur.fetchall()
    except Exception as e:
        logger.error(f"Error fetching time resolution sort indices: {e}")
        close_connection(con, cur)
        return {}
    finally:
        close_connection(con, cur)
    time_resolution_sort_indices = {row[0]: row[1] for row in time_resolution_sort_indices}
    return time_resolution_sort_indices

def get_spatial_resolution_sort_indices():
    """
    Get the spatial resolution sort indices from the search configuration.
    """
    search_config = get_search_config()
    con, cur = init_connection_new(config=search_config)
    q = "select * from search.grid_resolution_sort"
    try:
        cur.execute(q)
        grid_resolution_sort_indices = cur.fetchall()
    except Exception as e:
        logger.error(f"Error fetching grid resolution sort indices: {e}")
        close_connection(con, cur)
        return {}
    finally:
        close_connection(con, cur)
    grid_resolution_sort_indices = {row[0]: row[1] for row in grid_resolution_sort_indices}
    return grid_resolution_sort_indices
