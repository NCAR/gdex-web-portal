from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
import psycopg2
import json
from . import utils
from lxml import etree as ElementTree

metadb_config = settings.RDADB['metadata_config_pg']

def citations(request, output_format=None):
    response = {'response': "Bad request", 'status': 400}
    parts = request.META['HTTP_HOST'].split(".")
    if parts[0] != "api":
        return render(request, "404.html", {})

    parts = request.path.split("/")
    if parts[-1] == "":
        parts.pop()

    if parts[2] == "doi":
        if len(parts) == 5:
            response = doi(parts[3], parts[4], request.GET, output_format=output_format)
        elif len(parts) == 6:
            response = doi(parts[3], parts[4], request.GET, show=parts[5], output_format=output_format)

    elif parts[2] == "minter":
        if len(parts) == 4:
            response = minter(parts[3], request.GET)
        elif len(parts) == 5:
            response = minter(parts[3], request.GET, show=parts[4])

    elif parts[2] == "minters":
        if len(parts) == 3:
            response = minters()

    elif parts[2] == "publishers":
        if len(parts) == 3:
            response = publishers()

    indent = None
    if 'pretty-indent' in request.GET and len(request.GET['pretty-indent']) > 0:
        indent = int(request.GET['pretty-indent'])

    status = response['status']
    if output_format == ".xml":
        content_type = "application/xml"
        if not indent == None:
            space = " " * indent
            ElementTree.indent(response['response'], space=space, level=0)

        response = ElementTree.tostring(response['response'], encoding="unicode")
    else:
        content_type = "application/json"
        response = json.dumps(response['response'], indent=indent)

    return HttpResponse(response, content_type=content_type, status=status, headers={'Access-Control-Allow-Origin': "*", 'Access-Control-Allow-Headers': "X-Requested-With"})

def doi(doi_prefix, doi_suffix, query_dict, **kwargs):
    doi = doi_prefix + "/" + doi_suffix
    if kwargs['output_format'] == ".xml":
        response = ElementTree.Element('doi')
        response.set('ID', doi)
    else:
        response = {'doi': doi}

    conn = psycopg2.connect(**metadb_config)
    cursor = conn.cursor()
    if 'show' in kwargs:
        if kwargs['show'] == "counts":
            if kwargs['output_format'] == ".xml":
                response.append(utils.get_counts(query_dict, cursor, doi, kwargs['output_format']))
            else:
                response.update(utils.get_counts(query_dict, cursor, doi, kwargs['output_format']))
        elif kwargs['show'] == "publications":
            if kwargs['output_format'] == ".xml":
                response.append(utils.get_publications(query_dict, cursor, doi, kwargs['output_format']))
            else:
                response.update(utils.get_publications(query_dict, cursor, doi, kwargs['output_format']))

    else:
        tbls = utils.citations_tables()
        u = ""
        for x in range(len(tbls)):
            if x > 0:
                u += " union "

            u += "select DOI_work, pub_year from citation." + tbls[x] + " as d left join citation.works as w on w.DOI = d.DOI_work where d.DOI_data = '" + doi + "' and pub_year is not null"

        query = "select count(distinct DOI_work), min(pub_year), max(pub_year) from (" + u + ") as t"
        cursor.execute(query)
        row = cursor.fetchone()
        if row[0] == 0:
            response.update({'total_citations': 0})
        else:
            if kwargs['output_format'] == ".xml":
                tot_cit = ElementTree.SubElement(response, 'total_citations')
                tot_cit.text = str(row[0])
                years = ElementTree.SubElement(response, 'years')
                years.set('min', str(row[1]))
                years.set('max', str(row[2]))
            else:
                response.update({'total_citations': row[0], 'years': {'min': row[1], 'max': row[2]}})

    cursor.close()
    conn.close()
    return {'response': response, 'status': 200}

def minter(minter, query_dict, **kwargs):
    response = {'minter': minter.upper()}
    minter = minter.lower()
    valid_minters = utils.valid_minters()
    if not minter in valid_minters:
        return {'response': {'error_message': "The specified minter \"" + minter + "\" is not a valid minter."}, 'status': 400}

    if minter == "rda":
        minter = ""
    else:
        minter = "_" + minter

    conn = psycopg2.connect(**metadb_config)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'show' in kwargs:
        query = "select distinct c.DOI_data, d.DOI_data, d.publisher, d.asset_type from citation.data_citations" + minter + " as c left join citation.doi_data as d on d.DOI_data = c.DOI_data"
        if 'asset-type' in query_dict:
            query += " where d.asset_type = '" + query_dict.get('asset-type') + "'"
            response.update({'asset-type': query_dict.get('asset-type')})
        elif 'publisher' in query_dict:
            query += " where d.publisher = '" + query_dict.get('publisher').strip('"') + "'"
            response.update({'publisher': query_dict.get('publisher')})

        query += " order by c.DOI_data"
        cursor.execute(query)
        res = cursor.fetchall()
        list = []
        for e in res:
            d = {'doi': e['DOI_data']}
            if not 'asset-type' in query_dict:
                d.update({'asset-type': e['asset_type']})

            if not 'publisher' in query_dict:
                d.update({'publisher': e['publisher']})

            list.append(d)

        response.update({'list': list})
    else:
        query = "select distinct d.publisher, d.asset_type from citation.data_citations_ucar as c left join citation.doi_data as d on d.DOI_data = c.DOI_data"
        cursor.execute(query)
        res = cursor.fetchall()
        pubs = []
        assets = []
        for e in res:
            pubs.append(e['publisher'])
            if not e['asset_type'] in assets:
                assets.append(e['asset_type'])

        response.update({'asset-types': assets, 'publishers': pubs})

    return {'response': response, 'status': 200}

def minters():
    return {'response': {'minters': utils.valid_minters()}, 'status': 200}

def publishers():
    conn = psycopg2.connect(**metadb_config)
    cursor = conn.cursor()
    query = "select distinct publisher from citation.doi_data"
    cursor.execute(query)
    res = cursor.fetchall()
    l = []
    for e in res:
        l.append(e[0])

    return {'response': {'publishers': l}, 'status': 200}
