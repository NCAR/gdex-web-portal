from .utils import get_time_and_spatial_resolution_sort_indices, sort_by_separator

import logging
logger = logging.getLogger(__name__)

def custom_sort_facets(facets):
    """
    Custom sort facet buckets.
    """
    time_resolution_sort_indices, grid_resolution_sort_indices = get_time_and_spatial_resolution_sort_indices()

    for facet in facets:
        if facet.get('buckets'):
            if facet['field_name'] == 'time_resolution':
                # Sort time resolution buckets
                facet['buckets'] = sort_time_and_spatial_resolution_buckets(facet['buckets'], time_resolution_sort_indices)
            elif facet['field_name'] == 'spatial_resolution':
                # Sort spatial resolution buckets
                facet['buckets'] = sort_time_and_spatial_resolution_buckets(facet['buckets'], grid_resolution_sort_indices)
            elif facet['type'] == 'terms':
                try:
                    # Sort other term buckets numerically if applicable
                    facet['buckets'].sort(key=lambda x: float(x['value']))
                except ValueError:
                    # If sorting by float fails, sort lexicographically by string
                    facet['buckets'].sort(key=lambda x: x['value'])
            else:
                continue

    return facets

def sort_time_and_spatial_resolution_buckets(buckets, sort_indices):
    """
    Sort time and spatial resolution buckets
    """
    if not sort_indices:
        logger.error("Sort indices are not available for this facet.")
        return

    bucket_sort_indices = []

    for bucket in buckets:
        bucket_sort_indices.append(sort_indices.get(bucket['value']))

    return [x for _, x in sorted(zip(bucket_sort_indices, buckets), key=lambda pair: pair[0])]

def sort_location_buckets(buckets):
    """
    Sort location facets (full gcmd location path) based on the last element of the location string.
    """
    location_names = [bucket['field_name'] for bucket in buckets]
    sorted_locations = sort_by_separator(location_names, ">", 1)

    return [bucket for name in sorted_locations for bucket in buckets if bucket['field_name'] == name]
