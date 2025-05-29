from django.shortcuts import render
from django.conf import settings
from urllib.parse import urlparse
from django.contrib import messages

from globus_portal_framework.gsearch import (
    post_search, get_search_query, 
    get_search_filters, get_template,
    get_template_path
)
from globus_portal_framework.gclients import load_search_client

import psycopg2
import json
import sys

import logging
logger = logging.getLogger(__name__)

wdb_config = settings.RDADB['wagtail2_config_pg']
metadb_config = settings.RDADB['metadata_config_pg']

def dataset_search(request, index):
    context = {}
    query = get_search_query(request)
    if query:
        filters = get_search_filters(request)
        context['search'] = post_search(
            index, query, filters, request.user, request.GET.get('page', 1)
        )
        request.session['search'] = {
            'full_query': urlparse(request.get_full_path()).query,
            'query': query,
            'filters': filters,
            'index': index,
        }
        error = context['search'].get('error')
        if error:
            messages.error(request, error)
        
        # Reorder search results to put historical datasets last
        search_results = context['search'].get('search_results', [])
        if search_results:
            historical_datasets = get_historical_datasets(search_results)
            context['search']['search_results'] = [
                result for result in search_results if result['dataset_type'] != 'H'
            ] + historical_datasets
    
    context['datasets'] = get_dataset_counts()
    tvers = get_template_path('search.html', index=index)
    return render(request, get_template(index, tvers), context)

def get_dataset_counts():
    """
    Get the number of RDA datasets and facet titles, dataset counts, and descriptions
    """
    wconn = psycopg2.connect(**wdb_config)
    wcursor = wconn.cursor()
    q = "select refine_filters from lookfordata_lookfordatapage"
    wcursor.execute(q)
    res = wcursor.fetchone()
    wcursor.close()
    wconn.close()
    if not res:
        logger.error("No refine_filters found in lookfordata_lookfordatapage")
        return None

    filters = json.loads(res[0])

    mconn = psycopg2.connect(**metadb_config)
    mcursor = mconn.cursor()
    cond = "(d.type = 'P' or d.type = 'H') and d.dsid < 'd999000'"
    q = "select count(distinct dsid) from search.datasets as d where " + cond

    s = {
        "numds": None,
        "facets": []
    }

    try:
        mcursor.execute(q)
    except:
        s["numds"] = "??"
    else:
        res = mcursor.fetchone()
        s["numds"] = res[0]

    for filter in filters:
        value = filter['value']
        facet = {}
        if value['query_table']:
            facet['id'] = value['id']
            facet['title'] = value['title']
            facet['description'] = value['description']
            facet['cnt'] = 0
            q = (
                "select count(distinct s.dsid) from " + value['query_table'] +
                 " as s left join search.datasets as d on d.dsid = s.dsid "
                 "where " + cond
            )
            try:
                mcursor.execute(q)
            except psycopg2.Error as e:
                logger.error(f'Dataset search error: {e} for query: {q}')
                facet['cnt'] = "??"
            except:
                logger.error(f'Dataset search unknown error for query: {q}')
                facet['cnt'] = "??"
            else:
                res = mcursor.fetchone()
                facet['cnt'] = res[0]
            s['facets'].append(facet)

    mcursor.close()
    mconn.close()
    return s

def get_historical_datasets(search_results):
    """
    Get historical datasets from the 'search_results' list and return
    as a new list.
    """
    if not search_results or not isinstance(search_results, list):
        return search_results

    filtered_results = [
        result for result in search_results if result['dataset_type'] == 'H'
    ]
    
    return filtered_results