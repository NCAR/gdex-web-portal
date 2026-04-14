import json
import psycopg2

from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from lxml import etree as ElementTree

from . import utils
from .minter import get_dois as get_minter_dois
from .minter import get_publications as get_minter_publications


metadb_config = settings.RDADB['metadata_config_pg']


def swagger(request, output_format=None):
    return render(request, "citations/swagger.html", {})


def citations(request, output_format=None):
    parts = request.META['HTTP_HOST'].split(".")
    if parts[0] != "api":
        return render(request, "404.html", {})

    response = {'response': "Bad request", 'status': 400}
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
                              output_format=output_format)

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

    conn = psycopg2.connect(**metadb_config)
    cursor = conn.cursor()
    if 'show' in kwargs:
        if kwargs['show'] == "counts":
            if kwargs['output_format'] == ".xml":
                response.append(
                        utils.get_counts(query_dict, cursor, doi,
                                         kwargs['output_format']))
            else:
                response['doi'].update(
                        utils.get_counts(query_dict, cursor, doi,
                                         kwargs['output_format']))
        elif kwargs['show'] == "publications":
            if kwargs['output_format'] == ".xml":
                response.append(
                        utils.get_publications(query_dict, cursor, doi,
                                               kwargs['output_format']))
            else:
                response['doi'].update(
                        utils.get_publications(query_dict, cursor, doi,
                                               kwargs['output_format']))

    else:
        tbls = utils.citations_tables()
        u = ""
        for x in range(len(tbls)):
            if x > 0:
                u += " union "

            u += ("select DOI_work, pub_year from citation." + tbls[x] + " as "
                  "d left join citation.works as w on w.DOI = d.DOI_work "
                  "where d.DOI_data = '" + doi + "' and pub_year is not null")

        query = ("select count(distinct DOI_work), min(pub_year), "
                 "max(pub_year) from (" + u + ") as t")
        cursor.execute(query)
        row = cursor.fetchone()
        if kwargs['output_format'] == ".xml":
            ElementTree.SubElement(response, 'totalCitations').text = (
                    str(row[0]))
        else:
            response['doi'].update({'total_citations': row[0]})

        if row[0] > 0:
            if kwargs['output_format'] == ".xml":
                years = ElementTree.SubElement(response, 'years')
                ElementTree.SubElement(years, "min").text = str(row[1])
                ElementTree.SubElement(years, "max").text = str(row[2])
            else:
                response['doi'].update({'years': {'min': row[1],
                                                  'max': row[2]}})

    cursor.close()
    conn.close()
    return {'response': response, 'status': 200}


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
                ("The specified minter \"" + minter + "\" is not a valid "
                 "minter."))

    if minter == "rda":
        minter = ""
    else:
        minter = "_" + minter

    conn = psycopg2.connect(**metadb_config)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'show' in kwargs:
        if kwargs['show'] == "dois":
            dois = get_minter_dois(minter, cursor, **query_dict, **kwargs)
            if kwargs['output_format'] == ".xml":
                e = ElementTree.SubElement(response, "dois")
                for doi in dois:
                    d = ElementTree.SubElement(e, "doi")
                    d.set('ID', doi['doi']['ID'])
                    ElementTree.SubElement(d, "assetType").text = (
                            doi['doi']['asset-type'])

                    ElementTree.SubElement(d, "publisher").text = (
                            doi['doi']['publisher'])

            else:
                response['minter'].update({'dois': dois})

            return {'response': response, 'status': 200}
        elif kwargs['show'] == "publications":
            publications, citedby_count = get_minter_publications(
                    minter, cursor, **query_dict, **kwargs)
            if kwargs['output_format'] == ".xml":
                e = ElementTree.SubElement(response, "citedbyCount").text = (
                        str(citedby_count))
                e = ElementTree.SubElement(response, "publications")
                for publication in publications:
                    p = ElementTree.SubElement(e, "publication")
                    d = ElementTree.SubElement(p, "doi", ID=p['doi']['ID'])
            else:
                response['minter'].update({'citedby-count': citedby_count,
                                           'publications': publications})

            return {'response': response, 'status': 200}

    query = ("select distinct d.publisher, d.asset_type from citation."
             f"data_citations{minter} as c left join citation.doi_data as d "
             "on d.DOI_data = c.DOI_data")
    cursor.execute(query)
    res = cursor.fetchall()
    pubs = []
    assets = []
    for e in res:
        pubs.append(e['publisher'])
        if e['asset_type'] not in assets:
            assets.append(e['asset_type'])

    if kwargs['output_format'] == ".xml":
        e = ElementTree.SubElement(response, "assetTypes")
        for asset in assets:
            ElementTree.SubElement(e, "assetType").text = asset

        e = ElementTree.SubElement(response, "publishers")
        for pub in pubs:
            ElementTree.SubElement(e, "publisher").text = pub

    else:
        response['minter'].update({'asset-types': assets, 'publishers': pubs})

    return {'response': response, 'status': 200}


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

    return {'response': response, 'status': 200}
