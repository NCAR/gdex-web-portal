import json
import psycopg2

from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from lxml import etree as ElementTree

from . import utils
from .doi import (update_general_doi_response,
                  updated_specific_doi_response)
from .minter import (update_general_minter_response,
                     updated_specific_minter_response)


metadb_config = settings.RDADB['metadata_config_pg']


def swagger(request, output_format=None):
    return render(request, "citations/swagger.html", {})


def citations(request, output_format=None):
    parts = request.META['HTTP_HOST'].split(".")
    if parts[0] != "api":
        return render(request, "404.html", {})

    response = {'response': "Bad request", 'status': 400}
    from_swagger = (
        True if 'referer' in request.headers and
        request.headers['referer'].find(request.get_host()) > 0 else False)
    parts = request.path.replace("%2F", "/").split("/")
    if parts[-1] == "":
        parts.pop()

    if parts[2] == "doi":
        if len(parts) == 5:
            response = doi(parts[3], parts[4], request.GET,
                           output_format=output_format)
        elif len(parts) == 6:
            response = doi(parts[3], parts[4], request.GET, show=parts[5],
                           output_format=output_format)

    elif parts[2] == "minter":
        if len(parts) == 4:
            response = minter(parts[3], request.GET,
                              output_format=output_format)
        elif len(parts) == 5:
            response = minter(parts[3], request.GET, show=parts[4],
                              output_format=output_format,
                              from_swagger=from_swagger)

    elif parts[2] == "minters":
        if len(parts) == 3:
            response = minters(output_format)

    elif parts[2] == "publishers":
        if len(parts) == 3:
            response = publishers(output_format)

    indent = None
    if ('pretty-indent' in request.GET and len(request.GET['pretty-indent']) >
            0):
        indent = int(request.GET['pretty-indent'])

    status = response['status']
    if output_format == ".xml":
        content_type = "application/xml"
        if indent is not None:
            space = " " * indent
            ElementTree.indent(response['response'], space=space, level=0)

        response = ElementTree.tostring(
                response['response'], xml_declaration=True, encoding="utf-8")
    else:
        content_type = "application/json"
        response = json.dumps(response['response'], indent=indent)

    return HttpResponse(
            response, content_type=content_type, status=status,
            headers={'Access-Control-Allow-Origin': "*",
                     'Access-Control-Allow-Headers': "X-Requested-With"})


def doi(doi_prefix, doi_suffix, query_dict, **kwargs):
    doi = doi_prefix + "/" + doi_suffix
    if kwargs['output_format'] == ".xml":
        response = ElementTree.Element('doi')
        response.set('ID', doi)
    else:
        response = {'doi': {'ID': doi}}

    try:
        conn = psycopg2.connect(**metadb_config)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if 'show' in kwargs:
            updated_specific_doi_response(response, doi, cursor, **query_dict,
                                          **kwargs)
            return {'response': response, 'status': 200}

        update_general_doi_response(response, doi, cursor, **kwargs)
        return {'response': response, 'status': 200}
    finally:
        conn.close()


def minter(minter, query_dict, **kwargs):
    if kwargs['output_format'] == ".xml":
        response = ElementTree.Element('minter')
        response.set('ID', minter.upper())
    else:
        response = {'minter': {'ID': minter.upper()}}

    minter = minter.lower()
    valid_minters = utils.valid_minters()
    if minter not in valid_minters:
        return utils.error(
                kwargs['output_format'],
                f"The specified minter '{minter}' is not a valid minter.")

    if minter == "gdex":
        minter = ""
    else:
        minter = "_" + minter

    try:
        conn = psycopg2.connect(**metadb_config)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if 'show' in kwargs:
            # return specific information for the minter
            if updated_specific_minter_response(
                    response, minter, cursor, **query_dict, **kwargs):
                return {'response': response, 'status': 200}

        # return general minter information
        update_general_minter_response(response, minter, cursor, **kwargs)
        return {'response': response, 'status': 200}
    finally:
        conn.close()


def minters(output_format):
    minters = utils.valid_minters()
    if output_format == ".xml":
        response = ElementTree.Element('minters')
        for minter in minters:
            ElementTree.SubElement(response, 'minter').text = minter
    else:
        response = {'minters': minters}

    return {'response': response, 'status': 200}


def publishers(output_format):
    if output_format == ".xml":
        response = ElementTree.Element('publishers')
    else:
        response = {'publishers': []}

    conn = psycopg2.connect(**metadb_config)
    cursor = conn.cursor()
    query = "select distinct publisher from citation.doi_data"
    cursor.execute(query)
    res = cursor.fetchall()
    for e in res:
        if output_format == ".xml":
            ElementTree.SubElement(response, 'publisher').text = e[0]
        else:
            response['publishers'].append(e[0])

    conn.close()
    return {'response': response, 'status': 200}
