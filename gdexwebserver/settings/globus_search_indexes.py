""" Globus Search Index Configuration """

from . import globus_search_fields as search_fields

SEARCH_MAX_PAGES=1000
SEARCH_RESULTS_PER_PAGE=10

SEARCH_INDEXES = {
    'dataset-search': {
        'name': 'NSF NCAR GDEX Dataset Search',
        'uuid': 'fc7218fe-742c-4112-ab05-fc40472ced92',
        'facets': [
          {
            'name': 'Keyword',
            'field_name': 'gcmd_topics_and_terms',
            'size': 1000
          },
          {
            'name': 'Variables',
            'field_name': 'gcmd_variables',
            'size': 1000,
          },
          {
            'name': 'Platform',
            'field_name': 'platform',
            'size': 1000
          },
          {
            'name': 'Spatial Resolution',
            'field_name': 'spatial_resolution',
            'size': 1000
          },
          {
            'name': 'Time Resolution',
            'field_name': 'time_resolution',
            'size': 1000
          },
          {
            'name': 'Data Format',
            'field_name': 'format',
            'size': 1000
          },
          {
            'name': 'Data Type',
            'field_name': 'data_type',
            'size': 1000
          },
          {
            'name': 'Project',
            'field_name': 'project',
            'size': 1000
          },
          {
            'name': 'Supports Project',
            'field_name': 'supports_project',
            'size': 1000
          },
          {
            'name': 'Instrument',
            'field_name': 'instrument',
            'size': 1000
          },
          {
            'name': 'Location',
            'field_name': 'location',
            'size': 1000
          },
        ],
        'filter_match': 'match-any',
        'sort': [
            {
                'field_name': 'dataset_id',
                'order': 'asc',
            },
        ],
        'boosts': [
            {
                'field_name': 'title',
                'factor': 2.0,
            },
            {
                'field_name': 'description',
                'factor': 1.0,
            },
            {
                'field_name': 'gcmd_variables',
                'factor': 2.0,
            },
            {
                'field_name': 'location',
                'factor': 2.0,
            },
            {
                'field_name': 'project',
                'factor': 5.0,
            },
            {
                'field_name': 'supports_project',
                'factor': 5.0,
            },
            {
                'field_name': 'format',
                'factor': 0.5,
            },
        ],
        'fields': [
          ("title", search_fields.title),
          ("globus_app_link", search_fields.globus_app_link),
          ("dataset_url", search_fields.dataset_url),
          ("https_url", search_fields.https_url),
          ("dataset_type", search_fields.dataset_type),
          ("search_highlights", search_fields.search_highlights),
        ],
        'facet_modifiers': [
            'globus_portal_framework.modifiers.facets.sort_terms',
            'globus_portal_framework.modifiers.facets.sort_terms_numerically',
            'gsearch.modifiers.sort_time_and_spatial_resolution_facets',
        ],
    }
}