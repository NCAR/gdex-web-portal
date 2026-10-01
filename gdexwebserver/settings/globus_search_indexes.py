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
            'name': 'Location Category',
            'field_name': 'gcmd_location_category',
            'size': 1000
          },
          {
            'name': 'Location Type',
            'field_name': 'gcmd_location_type',
            'size': 1000
          },
          {
            'name': 'Location Subregion 1',
            'field_name': 'gcmd_location_subregion1',
            'size': 1000
          },
          {
            'name': 'Location Subregion 2',
            'field_name': 'gcmd_location_subregion2',
            'size': 1000
          },
          {
            'name': 'Location Subregion 3',
            'field_name': 'gcmd_location_subregion3',
            'size': 1000
          },
          {
            'name': 'Detailed Location',
            'field_name': 'gcmd_location_detailed',
            'size': 1000
          },
          {
            # Not filtered on directly — used only to drive correct
            # client-side narrowing of the tier dropdowns above, since
            # Globus Search does not scope facets to currently-applied
            # filters. See search-sidebar.html / search_data.js.
            'name': 'Location Path',
            'field_name': 'gcmd_location_path',
            'size': 1000
          },
        ],
        'filter_match': 'match-any',
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
          ("title",                   search_fields.title),
          ("globus_app_link",         search_fields.globus_app_link),
          ("dataset_url",             search_fields.dataset_url),
          ("https_url",               search_fields.https_url),
          ("dataset_type",            search_fields.dataset_type),
          ("gcmd_location_path",      search_fields.gcmd_location_path),
          ("search_highlights",       search_fields.search_highlights),
          # New fields for redesigned result cards
          ("summary",                 search_fields.summary),
          ("doi",                     search_fields.doi),
          ("dataset_id",              search_fields.dataset_id),
          ("size",                    search_fields.size),
          ("data_type_display",       search_fields.data_type_display),
          ("temporal_range",          search_fields.temporal_range),
          ("data_source",             search_fields.data_source),
          ("data_format_display",     search_fields.data_format_display),
          ("time_resolution_display", search_fields.time_resolution_display),
          ("dataset_logo",            search_fields.dataset_logo),
          ("dataset_tags",            search_fields.dataset_tags),
        ],
        'facet_modifiers': [
            'gsearch.modifiers.custom_sort_facets',
        ],
    }
}