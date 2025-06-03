from .utils import get_time_resolution_sort_indices, get_spatial_resolution_sort_indices

import logging
logger = logging.getLogger(__name__)

def sort_time_and_spatial_resolution_facets(facets):
    """
    For time and spatial resolution facets, sort the terms based on their predefined order.
    """
    for facet in facets:
        if facet.get('buckets'):
            if facet['field_name'] == 'time_resolution':
                sort_indices = get_time_resolution_sort_indices()
            elif facet['field_name'] == 'spatial_resolution':
                sort_indices = get_spatial_resolution_sort_indices()
            else:
                continue
            
            if not sort_indices:
                logger.error(f"{facet['field_name']} sort indices are not available.")
                continue

            bucket_sort_indices = []
            bucket_list = facet['buckets']

            for bucket in bucket_list:
                bucket_sort_indices.append(sort_indices.get(bucket['value']))

            facet['buckets'] = [x for _, x in sorted(zip(bucket_sort_indices, bucket_list), key=lambda pair: pair[0])]

    return facets
