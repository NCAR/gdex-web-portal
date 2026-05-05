from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

_DSID = OpenApiParameter(
    name='dsid', type=OpenApiTypes.STR, location=OpenApiParameter.PATH,
    description='Dataset identifier in 6-digit format (e.g., d123456)',
    required=True, pattern=r'd\d{6}'
)

_STD_200 = {
    'status': {'type': 'string', 'example': 'ok'},
    'http_response': {'type': 'integer', 'example': 200},
    'error_messages': {'type': 'array', 'items': {'type': 'string'}, 'example': []},
    'contact': {'type': 'string', 'example': 'datahelp@ucar.edu'},
}

_STD_400 = {
    'status': {'type': 'string', 'example': 'error'},
    'http_response': {'type': 'integer', 'example': 400},
    'error_messages': {'type': 'array', 'items': {'type': 'string'}},
    'data': {'type': 'object', 'example': {}},
    'contact': {'type': 'string', 'example': 'datahelp@ucar.edu'},
}

# ---------------------------------------------------------------------------
# Parameters / metadata
# ---------------------------------------------------------------------------

param_summary_schema = extend_schema(
    operation_id='get_param_summary',
    summary='Get parameter summary for a dataset',
    description='Retrieves a summary of parameters available for subsetting a specific dataset.',
    parameters=[_DSID],
    responses={200: {'type': 'object', 'description': 'Parameter summary data'}},
    tags=['parameters']
)

get_metadata_schema = extend_schema(
    operation_id='get_dataset_metadata',
    summary='Get dataset metadata',
    description='Retrieves detailed metadata for a specific dataset including available parameters and data ranges.',
    parameters=[_DSID],
    responses={200: {'type': 'object', 'description': 'Dataset metadata'}},
    tags=['metadata']
)

get_summary_schema = extend_schema(
    operation_id='get_dataset_summary',
    summary='Get dataset parameter summary',
    description='Retrieves a summary of available parameters and data ranges for a specific dataset.',
    parameters=[_DSID],
    responses={200: {'type': 'object', 'description': 'Dataset summary'}},
    tags=['metadata']
)

# ---------------------------------------------------------------------------
# Staff
# ---------------------------------------------------------------------------

get_staff_schema = extend_schema(
    operation_id='get_staff',
    summary='Get all staff members',
    description='Retrieves a list of all GDEX staff members.',
    parameters=[],
    responses={
        200: {
            'type': 'object',
            'properties': {
                **_STD_200,
                'data': {'type': 'array', 'items': {'type': 'object'}},
            }
        }
    },
    tags=['staff']
)

get_staff_by_dataset_schema = extend_schema(
    operation_id='get_staff_by_dataset',
    summary='Get staff members for a dataset',
    description='Retrieves the GDEX staff members associated with a specific dataset.',
    parameters=[_DSID],
    responses={
        200: {
            'type': 'object',
            'properties': {
                **_STD_200,
                'data': {'type': 'array', 'items': {'type': 'object'}},
            }
        }
    },
    tags=['staff']
)

# ---------------------------------------------------------------------------
# Files / groups
# ---------------------------------------------------------------------------

get_root_groups_schema = extend_schema(
    operation_id='get_dataset_root_groups',
    summary='Get root file groups for a dataset',
    description='Retrieves the top-level file groups for a specific dataset.',
    parameters=[_DSID],
    responses={
        200: {
            'type': 'object',
            'properties': {
                **_STD_200,
                'data': {'type': 'array', 'items': {'type': 'object'}},
            }
        }
    },
    tags=['files']
)

get_assembled_groups_schema = extend_schema(
    operation_id='get_assembled_file_groups',
    summary='Get assembled file listing for a dataset',
    description='''
        Returns a paginated table-like representation of files within a dataset.
        Supports optional group index, page, file name filter, and file list source.
    ''',
    parameters=[
        _DSID,
        OpenApiParameter(name='gindex', type=OpenApiTypes.STR, location=OpenApiParameter.PATH,
                         description='Group index (optional)', required=False),
        OpenApiParameter(name='page', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
                         description='Page number for pagination', required=False),
        OpenApiParameter(name='filter_wfile', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                         description='Filter files by name pattern', required=False),
        OpenApiParameter(name='fl', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                         description='File list source (default: web)', required=False),
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {**_STD_200, 'data': {'type': 'object'}}
        }
    },
    tags=['files']
)

get_child_groups_schema = extend_schema(
    operation_id='get_dataset_child_groups',
    summary='Get child file groups',
    description='Retrieves child file groups nested under a specific parent group for a dataset.',
    parameters=[
        _DSID,
        OpenApiParameter(name='gindex', type=OpenApiTypes.STR, location=OpenApiParameter.PATH,
                         description='Parent group index', required=True),
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {**_STD_200, 'data': {'type': 'array', 'items': {'type': 'object'}}}
        }
    },
    tags=['files']
)

get_web_files_schema = extend_schema(
    operation_id='get_dataset_web_files',
    summary='Get web-accessible files for a group',
    description='Retrieves the list of web-accessible files for a specific file group within a dataset.',
    parameters=[
        _DSID,
        OpenApiParameter(name='gindex', type=OpenApiTypes.STR, location=OpenApiParameter.PATH,
                         description='Group index', required=True),
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {**_STD_200, 'data': {'type': 'array', 'items': {'type': 'object'}}}
        }
    },
    tags=['files']
)

# ---------------------------------------------------------------------------
# Documentation / software
# ---------------------------------------------------------------------------

get_dataset_documentation_schema = extend_schema(
    operation_id='get_dataset_documentation',
    summary='Get dataset documentation',
    description='Retrieves documentation files and links associated with a specific dataset.',
    parameters=[_DSID],
    responses={
        200: {
            'type': 'object',
            'properties': {**_STD_200, 'data': {'type': 'array', 'items': {'type': 'object'}}}
        }
    },
    tags=['documentation']
)

get_dataset_software_schema = extend_schema(
    operation_id='get_dataset_software',
    summary='Get software associated with a dataset',
    description='Retrieves software tools and utilities associated with a specific dataset.',
    parameters=[_DSID],
    responses={
        200: {
            'type': 'object',
            'properties': {**_STD_200, 'data': {'type': 'array', 'items': {'type': 'object'}}}
        }
    },
    tags=['documentation']
)

# ---------------------------------------------------------------------------
# ARCO
# ---------------------------------------------------------------------------

has_arco_schema = extend_schema(
    operation_id='has_arco_data',
    summary='Check if ARCO data is available',
    description='Returns whether Analysis-Ready Cloud-Optimized (ARCO) data is available for a specific dataset.',
    parameters=[_DSID],
    responses={
        200: {
            'type': 'object',
            'properties': {
                **_STD_200,
                'data': {
                    'type': 'object',
                    'properties': {
                        'has_arco': {'type': 'boolean', 'example': True,
                                     'description': 'Whether ARCO data is available for the dataset'}
                    }
                },
            }
        }
    },
    tags=['arco']
)

get_arco_variables_schema = extend_schema(
    operation_id='get_arco_variables',
    summary='Get ARCO variables for a dataset',
    description='Retrieves the list of variables available in the Analysis-Ready Cloud-Optimized (ARCO) version of a dataset.',
    parameters=[_DSID],
    responses={
        200: {
            'type': 'object',
            'properties': {
                **_STD_200,
                'data': {'type': 'object', 'description': 'ARCO variable list and metadata'},
            }
        }
    },
    tags=['arco']
)

search_arco_variables_schema = extend_schema(
    operation_id='search_arco_variables',
    summary='Search ARCO variables for a dataset',
    description='Searches the ARCO variables for a specific dataset using a case-insensitive text pattern match.',
    parameters=[
        _DSID,
        OpenApiParameter(name='search_text', type=OpenApiTypes.STR, location=OpenApiParameter.PATH,
                         description='Text to search for in variable names', required=True),
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                **_STD_200,
                'data': {'type': 'array', 'items': {'type': 'array'}, 'description': 'Matching ARCO variables'},
            }
        }
    },
    tags=['arco']
)

# ---------------------------------------------------------------------------
# Notebook
# ---------------------------------------------------------------------------

generate_notebook_schema = extend_schema(
    operation_id='generate_jupyter_notebook',
    summary='Generate a Jupyter notebook for downloading data',
    description='''
        Generates a Jupyter notebook (.ipynb) for downloading and visualizing a list of dataset files.
        Submit a POST request with one or more `filelist[]` form fields containing file URLs.
    ''',
    parameters=[],
    responses={
        200: {'description': 'Jupyter notebook content'},
        400: {'description': 'Invalid request — missing or incorrectly named filelist parameter'}
    },
    tags=['notebook']
)

# ---------------------------------------------------------------------------
# Datasets listing
# ---------------------------------------------------------------------------

list_datasets_simple_schema = extend_schema(
    operation_id='list_datasets_simple',
    summary='List all datasets (simple format)',
    description='Retrieves a simple list of all available datasets.',
    parameters=[],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'data': {'type': 'array', 'items': {'type': 'object'}, 'description': 'List of all datasets'}
            }
        }
    },
    tags=['datasets']
)

get_all_datasets_schema = extend_schema(
    operation_id='get_all_datasets',
    summary='List all available datasets',
    description='''
    Retrieves a complete list of all available datasets in the system.

    Returns basic information for each dataset including:
    - Dataset ID (dsid)
    - Dataset title (dstitle)

    **Response Details:**
    - Results are ordered by dataset ID
    - Includes count of total datasets
    - Provides clean list for dataset discovery and browsing
    ''',
    parameters=[],
    responses={
        200: {
            'type': 'object',
            'description': 'Successfully retrieved list of all datasets',
            'properties': {
                **_STD_200,
                'data': {
                    'type': 'object',
                    'properties': {
                        'count': {'type': 'integer', 'description': 'Total number of datasets available'},
                        'datasets': {
                            'type': 'array',
                            'description': 'List of all datasets with basic information',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'id': {'type': 'string', 'description': 'Dataset identifier in 6-digit format'},
                                    'title': {'type': 'string', 'description': 'Dataset title'}
                                }
                            }
                        }
                    }
                },
            }
        }
    },
    tags=['all_datasets']
)

# ---------------------------------------------------------------------------
# Requests / submission
# ---------------------------------------------------------------------------

submit_schema = extend_schema(
    operation_id='submit_data_request',
    summary='Submit a data request',
    description='''
        Submits a data subset request for a specific dataset. Requires a user authentication token
        provided as a query parameter. The request body must be a JSON control file specifying the
        subset parameters (dataset, parameters, temporal/spatial range, etc.).

        Visit `/accounts/profile/` to obtain your authentication token.
    ''',
    parameters=[
        OpenApiParameter(name='token', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                         description='User authentication token (from /accounts/profile/)', required=True),
    ],
    responses={
        200: {'type': 'object', 'description': 'Submission result including request index'},
        400: {'description': 'Invalid token or malformed request body'}
    },
    tags=['requests']
)

print_help_schema = extend_schema(
    operation_id='get_api_help',
    summary='Get API help information',
    description='Returns help information and documentation for the GDEX data request API.',
    parameters=[],
    responses={200: {'type': 'object', 'description': 'API help information'}},
    tags=['help']
)

get_control_file_template_schema = extend_schema(
    operation_id='get_control_file_template',
    summary='Get control file template',
    description='Retrieves the control file template for submitting data requests for a specific dataset.',
    parameters=[_DSID],
    responses={200: {'type': 'object', 'description': 'Control file template with available parameters'}},
    tags=['requests']
)

get_status_schema = extend_schema(
    operation_id='get_request_status',
    summary='Get data request status',
    description='''
        Retrieves the status of one or all data requests for the authenticated user.
        Omit `rindex` to retrieve status for all requests. Authentication is via token query
        parameter or session cookie.
    ''',
    parameters=[
        OpenApiParameter(name='rindex', type=OpenApiTypes.STR, location=OpenApiParameter.PATH,
                         description='Request index (omit to retrieve all requests)', required=False),
        OpenApiParameter(name='token', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                         description='User authentication token (from /accounts/profile/)', required=False),
    ],
    responses={200: {'type': 'object', 'description': 'Request status information'}},
    tags=['requests']
)

get_req_files_schema = extend_schema(
    operation_id='get_request_files',
    summary='Get files for a completed data request',
    description='Retrieves the list of output files available for a completed data request.',
    parameters=[
        OpenApiParameter(name='rindex', type=OpenApiTypes.STR, location=OpenApiParameter.PATH,
                         description='Request index', required=True),
        OpenApiParameter(name='token', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                         description='User authentication token (from /accounts/profile/)', required=False),
    ],
    responses={200: {'type': 'object', 'description': 'List of files for the request'}},
    tags=['requests']
)

purge_schema = extend_schema(
    operation_id='purge_data_request',
    summary='Purge a data request',
    description='''
        Deletes a data request and its associated output files. Requires a DELETE HTTP method
        and a valid user authentication token.

        Visit `/accounts/profile/` to obtain your authentication token.
    ''',
    parameters=[
        OpenApiParameter(name='rindex', type=OpenApiTypes.STR, location=OpenApiParameter.PATH,
                         description='Request index to purge', required=True),
        OpenApiParameter(name='token', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY,
                         description='User authentication token (from /accounts/profile/)', required=True),
    ],
    responses={
        200: {'type': 'object', 'description': 'Purge result'},
        400: {'description': 'Wrong HTTP method or invalid token'}
    },
    tags=['requests']
)

# ---------------------------------------------------------------------------
# Globus
# ---------------------------------------------------------------------------

globus_download_schema = extend_schema(
    operation_id='initiate_globus_download',
    summary='Initiate a Globus transfer for a request',
    description='Initiates a Globus transfer of completed request files to a specified Globus endpoint.',
    parameters=[
        OpenApiParameter(name='rindex', type=OpenApiTypes.STR, location=OpenApiParameter.PATH,
                         description='Request index', required=True),
        OpenApiParameter(name='endpoint', type=OpenApiTypes.STR, location=OpenApiParameter.PATH,
                         description='Destination Globus endpoint UUID', required=True),
    ],
    responses={200: {'type': 'object', 'description': 'Globus transfer initiation result'}},
    tags=['globus']
)

# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

volume_downloaded_schema = extend_schema(
    operation_id='metrics_volume_downloaded',
    summary='Get total volume downloaded',
    description='Returns the total data volume downloaded from GDEX across all datasets.',
    parameters=[],
    responses={
        200: {
            'type': 'object',
            'properties': {'volume': {'type': 'number', 'description': 'Total volume downloaded in bytes'}}
        }
    },
    tags=['metrics']
)

unique_users_schema = extend_schema(
    operation_id='metrics_unique_users',
    summary='Get number of unique users',
    description='Returns the count of unique users who have downloaded data from GDEX.',
    parameters=[],
    responses={
        200: {
            'type': 'object',
            'properties': {'ips': {'type': 'integer', 'description': 'Number of unique users'}}
        }
    },
    tags=['metrics']
)

total_datasets_schema = extend_schema(
    operation_id='metrics_total_datasets',
    summary='Get total number of datasets',
    description='Returns the total number of datasets available in GDEX.',
    parameters=[],
    responses={
        200: {
            'type': 'object',
            'properties': {'value': {'type': 'integer', 'description': 'Total number of datasets'}}
        }
    },
    tags=['metrics']
)

total_citations_schema = extend_schema(
    operation_id='metrics_total_citations',
    summary='Get total number of dataset citations',
    description='Returns the total number of citations for GDEX datasets.',
    parameters=[],
    responses={
        200: {
            'type': 'object',
            'properties': {'value': {'type': 'integer', 'description': 'Total number of citations'}}
        }
    },
    tags=['metrics']
)

gdex_volume_schema = extend_schema(
    operation_id='metrics_gdex_volume',
    summary='Get total GDEX data volume',
    description='Returns the total size of all data hosted in GDEX.',
    parameters=[],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'value': {'type': 'string', 'description': 'Total GDEX data volume with units', 'example': '3.2 PB'}
            }
        }
    },
    tags=['metrics']
)

total_requests_schema = extend_schema(
    operation_id='metrics_total_requests',
    summary='Get total number of data requests',
    description='Returns the total number of data subset requests submitted to GDEX.',
    parameters=[],
    responses={
        200: {
            'type': 'object',
            'properties': {'value': {'type': 'integer', 'description': 'Total number of data requests'}}
        }
    },
    tags=['metrics']
)

top_datasets_schema = extend_schema(
    operation_id='metrics_top_datasets',
    summary='Get most-downloaded datasets',
    description='Returns a list of the most frequently downloaded datasets in GDEX.',
    parameters=[],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'top_datasets': {
                    'type': 'array', 'items': {'type': 'object'},
                    'description': 'List of top datasets with download statistics'
                }
            }
        }
    },
    tags=['metrics']
)

ai_datasets_schema = extend_schema(
    operation_id='metrics_ai_datasets',
    summary='Get AI/ML-relevant datasets',
    description='Returns datasets that are suitable for or commonly used in AI and machine learning applications.',
    parameters=[],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'ai_datasets': {'type': 'array', 'items': {'type': 'array'}, 'description': 'List of AI/ML datasets'}
            }
        }
    },
    tags=['metrics']
)

dataset_users_month_schema = extend_schema(
    operation_id='metrics_dataset_users_month',
    summary='Get dataset unique users in the past 30 days',
    description='Returns the number of unique users who have downloaded data from a specific dataset in the past 30 days.',
    parameters=[_DSID],
    responses={
        200: {
            'type': 'object',
            'properties': {'value': {'type': 'integer', 'description': 'Number of unique users in the past 30 days'}}
        }
    },
    tags=['metrics']
)

dataset_users_year_schema = extend_schema(
    operation_id='metrics_dataset_users_year',
    summary='Get dataset unique users in the past year',
    description='Returns the number of unique users who have downloaded data from a specific dataset in the past 365 days.',
    parameters=[_DSID],
    responses={
        200: {
            'type': 'object',
            'properties': {'value': {'type': 'integer', 'description': 'Number of unique users in the past year'}}
        }
    },
    tags=['metrics']
)

dataset_volume_month_schema = extend_schema(
    operation_id='metrics_dataset_volume_month',
    summary='Get dataset download volume in the past 30 days',
    description='Returns the total data volume downloaded from a specific dataset in the past 30 days.',
    parameters=[_DSID],
    responses={200: {'type': 'object', 'description': 'Volume downloaded in the past 30 days'}},
    tags=['metrics']
)

dataset_volume_year_schema = extend_schema(
    operation_id='metrics_dataset_volume_year',
    summary='Get dataset download volume in the past year',
    description='Returns the total data volume downloaded from a specific dataset in the past 365 days.',
    parameters=[_DSID],
    responses={200: {'type': 'object', 'description': 'Volume downloaded in the past year'}},
    tags=['metrics']
)

# ---------------------------------------------------------------------------
# Dataset detail — abstract, acknowledgement, temporal, variables, publications
# ---------------------------------------------------------------------------

get_abstract_schema = extend_schema(
    operation_id='get_dataset_abstract',
    summary='Get dataset abstract',
    description='''
    Retrieves the abstract text for a specific dataset along with additional parsed notes.

    This endpoint performs comprehensive text processing including:
    - Unicode escape sequence decoding
    - URL extraction from the abstract text
    - Note/warning text identification and separation
    - HTML tag removal and text cleaning
    ''',
    parameters=[_DSID],
    responses={
        200: {
            'type': 'object',
            'description': 'Successfully retrieved abstract with parsed metadata',
            'properties': {
                **_STD_200,
                'data': {
                    'type': 'object',
                    'properties': {
                        'abstract': {
                            'type': 'string',
                            'description': 'Cleaned abstract text with HTML tags removed',
                        },
                        'note': {
                            'type': 'string',
                            'description': 'Any warning or note text found in the abstract',
                            'example': 'It is advised to use ds633.0, ERA5 Reanalysis (0.25 Degree Latitude-Longitude Grid).'
                        },
                        'urls': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'description': 'List of unique URLs found in the abstract text',
                            'example': ['https://gdex.ucar.edu/datasets/ds633-0/']
                        }
                    }
                },
            }
        },
        400: {
            'type': 'object',
            'description': 'Dataset not found',
            'properties': {
                **_STD_400,
                'error_messages': {
                    'type': 'array', 'items': {'type': 'string'},
                    'example': ['Abstract not found for dataset d123456']
                },
            }
        }
    },
    tags=['abstract']
)

get_acknowledgement_schema = extend_schema(
    operation_id='get_dataset_acknowledgement',
    summary='Get dataset acknowledgement text',
    description='''
    Retrieves the acknowledgement text for a specific dataset.
    HTML paragraph tags (`<p>`, `</p>`) are automatically stripped from the response
    ''',
    parameters=[_DSID],
    responses={
        200: {
            'type': 'object',
            'properties': {
                **_STD_200,
                'data': {
                    'type': 'object',
                    'properties': {
                        'acknowledgement': {'type': 'string'}
                    }
                },
            }
        },
        400: {
            'type': 'object',
            'properties': {
                **_STD_400,
                'error_messages': {
                    'type': 'array', 'items': {'type': 'string'},
                    'example': ['Acknowledgement not found for dataset d633004']
                },
            }
        }
    },
    tags=['acknowledgment']
)

get_temporal_schema = extend_schema(
    operation_id='get_dataset_temporal_coverage',
    summary='Get dataset temporal coverage',
    description='''
        Retrieves the temporal coverage information for a specific dataset.
        Returns start date, end date, and data groups with their respective time ranges.
    ''',
    parameters=[_DSID],
    responses={
        200: {
            'type': 'object',
            'properties': {
                **_STD_200,
                'data': {
                    'type': 'object',
                    'properties': {
                        'temporal': {
                            'type': 'object',
                            'properties': {
                                'start_date': {'type': 'string', 'example': '1805-12-31 18:00 +0000'},
                                'end_date': {'type': 'string', 'example': '2016-01-01 00:00 +0000'},
                                'data_groups': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'description': {'type': 'string'},
                                            'start_date': {'type': 'string'},
                                            'end_date': {'type': 'string'}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
            }
        },
        400: {
            'type': 'object',
            'properties': {
                **_STD_400,
                'error_messages': {
                    'type': 'array', 'items': {'type': 'string'},
                    'example': ['Temporal coverage not found for dataset d633004']
                },
            }
        }
    },
    tags=['temporal']
)

get_variables_schema = extend_schema(
    operation_id='get_dataset_variables',
    summary='Get dataset variables',
    description='''
        Retrieves the list of variables for a specific dataset.
        Returns a count of variables, a list of all variables, and variables organized by categories.
        Note: Variables represented in this API include but are not limited to those available in the dataset.
    ''',
    parameters=[_DSID],
    responses={
        200: {
            'type': 'object',
            'properties': {
                **_STD_200,
                'data': {
                    'type': 'object',
                    'properties': {
                        'count': {'type': 'integer', 'example': 40, 'description': 'Total number of variables'},
                        'variables': {
                            'type': 'array', 'items': {'type': 'string'},
                            'description': 'List of all variables in the dataset'
                        },
                        'categories': {
                            'type': 'object',
                            'additionalProperties': {'type': 'array', 'items': {'type': 'string'}},
                            'description': 'Variables organized by category'
                        },
                        'message': {'type': 'string', 'description': 'Additional information about variable availability'}
                    }
                },
            }
        },
        400: {
            'type': 'object',
            'properties': {
                **_STD_400,
                'error_messages': {
                    'type': 'array', 'items': {'type': 'string'},
                    'example': ['Variables not found for dataset d633004']
                },
            }
        }
    },
    tags=['variables']
)

get_publications_schema = extend_schema(
    operation_id='get_dataset_publications',
    summary='Get dataset publications',
    description='''
        Retrieves the list of publications related to a specific dataset.
        Returns a count of publications and detailed information about each publication including authors, title, journal, and DOI.
    ''',
    parameters=[_DSID],
    responses={
        200: {
            'type': 'object',
            'properties': {
                **_STD_200,
                'data': {
                    'type': 'object',
                    'properties': {
                        'count': {'type': 'integer', 'example': 2, 'description': 'Total number of publications'},
                        'publications': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'authors': {'type': 'array', 'items': {'type': 'string'}},
                                    'authors_text': {'type': 'string'},
                                    'year': {'type': 'string', 'example': '2021'},
                                    'title': {'type': 'string'},
                                    'journal': {'type': 'string'},
                                    'volume_pages': {'type': 'string'},
                                    'doi': {'type': 'string'},
                                    'url': {'type': 'string'}
                                }
                            }
                        }
                    }
                },
            }
        },
        400: {
            'type': 'object',
            'properties': {
                **_STD_400,
                'error_messages': {
                    'type': 'array', 'items': {'type': 'string'},
                    'example': ['Publications not found for dataset d633004']
                },
            }
        }
    },
    tags=['publications']
)

get_data_license_schema = extend_schema(
    operation_id='get_dataset_license',
    summary='Get dataset license information',
    description='''
        Retrieves the licensing information for a specific dataset.
        Returns the license name and URL with legal details.
    ''',
    parameters=[_DSID],
    responses={
        200: {
            'type': 'object',
            'properties': {
                **_STD_200,
                'data': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string', 'example': 'Creative Commons Attribution 4.0 International License',
                                 'description': 'Full name of the data license'},
                        'url': {'type': 'string', 'example': 'https://creativecommons.org/licenses/by/4.0/legalcode',
                                'description': 'URL to the license legal text'}
                    }
                },
            }
        },
        400: {
            'type': 'object',
            'properties': {
                **_STD_400,
                'error_messages': {
                    'type': 'array', 'items': {'type': 'string'},
                    'example': ['Data license not found for dataset d633004']
                },
            }
        }
    },
    tags=['data_license']
)

get_data_types_schema = extend_schema(
    operation_id='get_dataset_data_types',
    summary='Get dataset data types',
    description='''
        Retrieves the types of data contained in a specific dataset.
        Returns a list of data type categories (e.g., Grid, Point, Station).
    ''',
    parameters=[_DSID],
    responses={
        200: {
            'type': 'object',
            'properties': {
                **_STD_200,
                'data': {
                    'type': 'object',
                    'properties': {
                        'data_types': {
                            'type': 'array', 'items': {'type': 'string'}, 'example': ['Grid'],
                            'description': 'List of data types contained in the dataset'
                        }
                    }
                },
            }
        },
        400: {
            'type': 'object',
            'properties': {
                **_STD_400,
                'error_messages': {
                    'type': 'array', 'items': {'type': 'string'},
                    'example': ['Data types not found for dataset d633004']
                },
            }
        }
    },
    tags=['data_types']
)

get_data_formats_schema = extend_schema(
    operation_id='get_dataset_data_formats',
    summary='Get dataset data formats',
    description='''
        Retrieves the available file formats and data structure information for a specific dataset.
        Returns a count of formats and detailed information about each format including description, URL, and documentation availability.
    ''',
    parameters=[_DSID],
    responses={
        200: {
            'type': 'object',
            'properties': {
                **_STD_200,
                'data': {
                    'type': 'object',
                    'properties': {
                        'count': {'type': 'integer', 'example': 1, 'description': 'Total number of data formats'},
                        'data_formats': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'description': {'type': 'string', 'example': 'netCDF4'},
                                    'url': {'type': 'string', 'example': 'http://www.unidata.ucar.edu/software/netcdf/'},
                                    'has_documentation': {'type': 'boolean', 'example': True}
                                }
                            },
                            'description': 'List of available data formats with details'
                        }
                    }
                },
            }
        },
        400: {
            'type': 'object',
            'properties': {
                **_STD_400,
                'error_messages': {
                    'type': 'array', 'items': {'type': 'string'},
                    'example': ['Data formats not found for dataset d633004']
                },
            }
        }
    },
    tags=['data_formats']
)

get_spatial_coverage_schema = extend_schema(
    operation_id='get_dataset_spatial_coverage',
    summary='Get dataset spatial coverage',
    description='''
        Retrieves the spatial coverage information for a specific dataset.
        Returns geographic bounds, resolution, coordinate ranges, and grid dimensions.
    ''',
    parameters=[_DSID],
    responses={
        200: {
            'type': 'object',
            'properties': {
                **_STD_200,
                'data': {
                    'type': 'object',
                    'properties': {
                        'spatial_coverage': {
                            'type': 'object',
                            'properties': {
                                'bounds': {
                                    'type': 'object',
                                    'properties': {
                                        'north': {'type': 'number', 'example': 89.463},
                                        'south': {'type': 'number', 'example': -89.463},
                                        'east': {'type': 'number', 'example': 180},
                                        'west': {'type': 'number', 'example': -180},
                                        'lat_units': {'type': 'string', 'example': 'degrees north'},
                                        'lon_units': {'type': 'string', 'example': 'degrees east'}
                                    }
                                },
                                'resolution': {
                                    'type': 'object',
                                    'properties': {
                                        'longitude': {'type': 'number', 'example': 0.703},
                                        'latitude': {'type': 'number', 'example': 0.702},
                                        'units': {'type': 'string', 'example': 'degrees'}
                                    }
                                },
                                'coordinate_range': {
                                    'type': 'object',
                                    'properties': {
                                        'longitude_start': {'type': 'string', 'example': '0E'},
                                        'longitude_end': {'type': 'string', 'example': '359.297E'},
                                        'latitude_start': {'type': 'string', 'example': '89.463N'},
                                        'latitude_end': {'type': 'string', 'example': '89.463S'}
                                    }
                                },
                                'grid_dimensions': {
                                    'type': 'object',
                                    'properties': {
                                        'longitude_points': {'type': 'integer', 'example': 512},
                                        'latitude_points': {'type': 'integer', 'example': 256}
                                    }
                                }
                            }
                        }
                    }
                },
            }
        },
        400: {
            'type': 'object',
            'properties': {
                **_STD_400,
                'error_messages': {
                    'type': 'array', 'items': {'type': 'string'},
                    'example': ['Spatial coverage not found for dataset d633004']
                },
            }
        }
    },
    tags=['spatial']
)

get_contributors_schema = extend_schema(
    operation_id='get_dataset_contributors',
    summary='Get dataset contributors',
    description='''
        Retrieves information about contributors for a specific dataset.
        Returns contributor details including names, IDs, and categories.
    ''',
    parameters=[_DSID],
    responses={
        200: {
            'type': 'object',
            'properties': {
                **_STD_200,
                'data': {
                    'type': 'object',
                    'properties': {
                        'count': {'type': 'integer', 'example': 1, 'description': 'Number of contributors'},
                        'contributors': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'id': {'type': 'string', 'example': 'UCO/CIRES'},
                                    'name': {'type': 'string',
                                             'example': 'Cooperative Institute for Research in Environmental Sciences, University of Colorado'},
                                    'category': {'type': 'string', 'example': 'academic'}
                                }
                            }
                        }
                    }
                },
            }
        },
        400: {
            'type': 'object',
            'properties': {
                **_STD_400,
                'error_messages': {
                    'type': 'array', 'items': {'type': 'string'},
                    'example': ['Contributors not found for dataset d633004']
                },
            }
        }
    },
    tags=['contributors']
)

get_total_volume_schema = extend_schema(
    operation_id='get_dataset_total_volume',
    summary='Get dataset total volume',
    description='''
        Retrieves the total volume information for a specific dataset.
        Returns overall dataset size and breakdown by volume groups.
    ''',
    parameters=[_DSID],
    responses={
        200: {
            'type': 'object',
            'properties': {
                **_STD_200,
                'data': {
                    'type': 'object',
                    'properties': {
                        'total_volume': {'type': 'string', 'example': '105.26 TB',
                                         'description': 'Total dataset volume with units'},
                        'volume_groups': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'group': {'type': 'string'},
                                    'volume': {'type': 'string', 'example': '68.52 TB'}
                                }
                            }
                        }
                    }
                },
            }
        },
        400: {
            'type': 'object',
            'properties': {
                **_STD_400,
                'error_messages': {
                    'type': 'array', 'items': {'type': 'string'},
                    'example': ['Total volume not found for dataset d633004']
                },
            }
        }
    },
    tags=['volume']
)

get_related_resources_schema = extend_schema(
    operation_id='get_dataset_related_resources',
    summary='Get related resources',
    description='''
        Retrieves related resources for a specific dataset.
        Returns external tools, software, documentation, and other resources related to the dataset.
    ''',
    parameters=[_DSID],
    responses={
        200: {
            'type': 'object',
            'properties': {
                **_STD_200,
                'data': {
                    'type': 'object',
                    'properties': {
                        'count': {'type': 'integer', 'example': 1, 'description': 'Number of related resources'},
                        'resources_list': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'description': {'type': 'string'},
                                    'url': {'type': 'string', 'example': 'https://pywinter.readthedocs.io/en/latest/'}
                                }
                            }
                        }
                    }
                },
            }
        },
        400: {
            'type': 'object',
            'properties': {
                **_STD_400,
                'error_messages': {
                    'type': 'array', 'items': {'type': 'string'},
                    'example': ['Related resources not found for dataset d633004']
                },
            }
        }
    },
    tags=['resources']
)

get_related_datasets_schema = extend_schema(
    operation_id='get_dataset_related_datasets',
    summary='Get related datasets',
    description='''
        Retrieves datasets that are related to or derived from the specified dataset.
        Returns a list of related datasets with their identifiers and titles.
    ''',
    parameters=[_DSID],
    responses={
        200: {
            'type': 'object',
            'properties': {
                **_STD_200,
                'data': {
                    'type': 'object',
                    'properties': {
                        'count': {'type': 'integer', 'example': 1, 'description': 'Number of related datasets'},
                        'resources_list': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'dsid': {'type': 'string', 'example': 'd093000'},
                                    'title': {'type': 'string'}
                                }
                            }
                        }
                    }
                },
            }
        },
        400: {
            'type': 'object',
            'properties': {
                **_STD_400,
                'error_messages': {
                    'type': 'array', 'items': {'type': 'string'},
                    'example': ['Related datasets not found for dataset d633004']
                },
            }
        }
    },
    tags=['related_datasets']
)

# ---------------------------------------------------------------------------
# Excluded from schema (internal / deprecated)
# ---------------------------------------------------------------------------

exclude_schema = extend_schema(exclude=True)
