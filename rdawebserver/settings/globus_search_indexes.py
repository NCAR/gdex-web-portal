""" Globus Search Index Configuration """

from . import globus_search_fields as search_fields

SEARCH_INDEXES = {
    'dataset-search': {
        'name': 'NSF NCAR RDA Dataset Search',
        'uuid': 'fc7218fe-742c-4112-ab05-fc40472ced92',
        'facets': [
          {
            'name': 'Variables',
            'field_name': 'variables'
          },
          {
            'name': 'Data Type',
            'field_name': 'data_type'
          },
          {
            'name': 'Time Resolution',
            'field_name': 'time_resolution'
          },
          {
            'name': 'Platform',
            'field_name': 'platform'
          },
          {
            'name': 'Spatial Resolution',
            'field_name': 'spatial_resolution'
          },
          {
            'name': 'Topic/Subtopic',
            'field_name': 'gcmd_keywords'
          },
          {
            'name': 'Project',
            'field_name': 'project'
          },
          {
            'name': 'Supports Project',
            'field_name': 'supports_project'
          },
          {
            'name': 'Data Format',
            'field_name': 'format'
          },
          {
            'name': 'Instrument',
            'field_name': 'instrument'
          },
          {
            'name': 'Location',
            'field_name': 'location'
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