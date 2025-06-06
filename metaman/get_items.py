import psycopg2
import re

from lxml import etree as ElementTree

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from . import config
from . import utils


def add_ancillary_info(pub_parts):
    d = {}
    for x in range(5, len(pub_parts)):
        if pub_parts[x].find("ds_rel:") == 0:
            d.update({'ds_rel': pub_parts[x][7:]})
        elif pub_parts[x].find("doi:") == 0:
            d.update({'doi': pub_parts[x][4:]})
        elif pub_parts[x].find("url:") == 0:
            d.update({'url': pub_parts[x][4:]})
        elif pub_parts[x].find("annotation:") == 0:
            d.update({'annotation': pub_parts[x][11:]})

    return d


def get_book_ref(request):
    d = {}
    d.update({'relation_options': utils.ds_relationship_options()})
    if 'editItem' in request.POST:
        parts = request.POST['editItem'].split("[!]")
        d.update({
            'replace_item': request.POST['editItem'].replace("'", "\\'"),
            'authors': parts[1],
            'pub_year': parts[2],
            'pub_title': parts[3],
        })
        extra = parts[4].split("[+]")
        d.update({
            'pub_city': extra[0],
            'publisher': extra[1],
        })
        d.update(add_ancillary_info(parts))

    return render(request, "metaman/datasets/get_book_ref.html", {'data': d})


def get_bookchapter_ref(request):
    d = {}
    d.update({'relation_options': utils.ds_relationship_options()})
    if 'editItem' in request.POST:
        parts = request.POST['editItem'].split("[!]")
        d.update({
            'replace_item': request.POST['editItem'].replace("'", "\\'"),
            'authors': parts[1],
            'pub_year': parts[2],
            'pub_title': parts[3],
        })
        extra = parts[4].split("[+]")
        d.update({
            'editor': extra[0],
            'publisher': extra[1],
            'pages': extra[2],
            'book_title': extra[3],
        })
        d.update(add_ancillary_info(parts))

    return render(request, "metaman/datasets/get_bookchapter_ref.html",
                  {'data': d})


def get_contact(request):
    conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
    cursor = conn.cursor()
    cursor.execute((
            "select concat(fstname, ' ', lstname) from dssdb.dssgrp where "
            "role in ('S', 'M', 'T') and stat_flag = 'C' order by fstname"))
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    contacts = []
    for e in res:
        contacts.append(e[0])

    return render(request, "metaman/datasets/get_contact.html",
                  {'contacts': contacts})


def get_contributor(request):
    if 'org' in request.POST:
        org = request.POST['org']

    is_citable = True
    if 'editItem' in request.POST:
        parts = request.POST['editItem'].split("[!]")
        org = parts[0] + "[!]" + parts[1]
        former_name = parts[2]
        if parts[3]:
            if re.compile("^(http(s){0,1}|ftp)://").match(parts[3]):
                idx = parts[3].find(";")
                if idx > 0:
                    url = parts[3][0:idx]
                    contacts = parts[3][idx+1:].split(";")
                else:
                    url = parts[3]
            else:
                contacts = parts[3].split(";")

        if parts[4] == "N":
            is_citable = False

    d = {}
    if 'centerSearchFor' in request.POST:
        q = "select distinct path, uuid from search.gcmd_providers where"
        if request.POST['centerSearchFor'] != "SHOW_ALL":
            terms = request.POST['centerSearchFor'].split()
            for term in terms:
                q += " path ilike '%" + term + "%' and"

        q += " cflag != 9 order by path"
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute(q)
        res = cursor.fetchall()
        cursor.close()
        conn.close()
        mkeys = []
        for e in res:
            mkeys.append({'path': e[0], 'uuid': e[1]})

        d.update({'matched_keywords': mkeys})
    elif 'org' in locals():
        d.update({'org_name': org, 'is_citable': is_citable})
        if 'former_name' in locals():
            d.update({'former_name': former_name})

        if 'url' in locals():
            d.update({'url': url})

        if 'contacts' in locals():
            if len(contacts) > 0:
                d.update({'contact0': contacts[0]})

            if len(contacts) > 1:
                d.update({'contact1': contacts[1]})

            if len(contacts) > 2:
                d.update({'contact2': contacts[2]})

            if len(contacts) > 3:
                d.update({'contact3': contacts[3]})

            if len(contacts) > 4:
                d.update({'contact4': contacts[4]})

        if 'editItem' in request.POST:
            d.update({'replace_item': (request.POST['editItem']
                                       .replace("'", "\\'"))})

    return render(request, "metaman/datasets/get_contributor.html",
                  {'data': d})


def get_datasets(request):
    if 'edit_dsid' not in request.POST or 'type' not in request.POST:
        return render(request, "400.html")

    ctx = {'edit_dsid': request.POST['edit_dsid'],
           'type': request.POST['type']}
    return render(request, "metaman/datasets/get_datasets.html", ctx)


def get_doi(request):
    ctx = {}
    if 'editItem' in request.POST:
        ctx.update({'edit_item': request.POST['editItem']})

    rel_values = []
    try:
        tree = ElementTree.parse("/data/web/metadata/schemas/dsOverview3.xsd")
        root = tree.getroot()
        ns = {
            'xsd': "http://www.w3.org/2001/XMLSchema",
        }
        e = root.find((
                "./xsd:element[@name='relatedDOI']/xsd:complexType/xsd:"
                "simpleContent/xsd:extension/xsd:attribute[@name="
                "'relationType']/xsd:simpleType/xsd:restriction"), ns)
        for enumeration in e.findall("xsd:enumeration", ns):
            rel_values.append(enumeration.get("value"))

    except Exception:
        pass

    ctx.update({'relation_values': rel_values})
    return render(request, "metaman/dois/get_doi.html", ctx)


def get_journal_ref(request):
    d = {}
    d.update({'relation_options': utils.ds_relationship_options()})
    if 'ris_file' in request.FILES:
        s = ""
        for chunk in request.FILES['ris_file']:
            s += chunk.decode("utf-8")

        lines = s.split("\n")
        while len(lines) > 0 and (len(lines[0]) < 7 or lines[0][0:3] != "TY "):
            lines.pop(0)

        if len(lines) == 0:
            return HttpResponse(("This file does not appear to be in RIS "
                                 "format."))

        if lines[0][0:3] == "TY ":
            lines.pop(0)
            found_end = False
            for line in lines:
                if len(line) < 7:
                    continue

                if line[0:5] == "AU  -" or line[0:5] == "A1  -":
                    parts = line[5:].strip().split(",")
                    initials = parts[1].split()
                    initials = [x if x[1] == '.' else (x[0:1] + ".") for x in
                                initials]
                    if 'authors' in locals():
                        authors = authors.replace(", and", ", ")
                        authors += (", and " + " ".join(initials) + " " +
                                    parts[0].strip())
                    else:
                        authors = parts[0].strip() + ", " + " ".join(initials)

                elif line[0:5] == "CY  -":
                    d.update({'pub_city': line[5:].strip()})
                elif line[0:5] == "DO  -":
                    d.update({'doi': line[5:].strip()})
                elif line[0:5] == "EP  -":
                    if 'pages' in locals():
                        pages += "-" + line[5:].strip()
                    else:
                        pages = line[5:].strip()

                elif line[0:5] == "ER  -":
                    found_end = True
                elif line[0:5] == "JA  -":
                    ja = line[5:].strip()
                elif line[0:5] == "JO  -":
                    jo = line[5:].strip()
                elif line[0:5] == "PY  -":
                    parts = line[5:].split("/")
                    d.update({'pub_year': parts[0].strip()})
                elif line[0:5] == "SP  -":
                    if 'pages' in locals():
                        pages = line[5:].strip() + "-" + pages
                    else:
                        pages = line[5:].strip()

                elif line[0:5] == "TI  -" or line[0:5] == "T1  -":
                    d.update({'pub_title': line[5:].strip()})
                elif line[0:5] == "UR  -":
                    d.update({'url': line[5:].strip()})
                elif line[0:5] == "VL  -":
                    d.update({'volume': line[5:].strip()})

                if found_end:
                    break

            if 'authors' in locals():
                d.update({'authors': authors})

            if 'jo' in locals() and 'ja' not in locals():
                parts = jo.split()
                abbrevs = [x for x in parts if x[-1] == "."]
                if len(abbrevs) > 0:
                    ja = jo

            if 'ja' in locals():
                d.update({'journal': ja})

        else:
            return HttpResponse(("The RIS file does not contain journal "
                                 "article information."))

    elif 'editItem' in request.POST:
        parts = request.POST['editItem'].split("///")
        d.update({'item_num': parts[-1]})
        parts = parts[0].split("[!]")
        d.update({
            'replace_item': request.POST['editItem'].replace("'", "\\'"),
            'authors': parts[1],
            'pub_year': parts[2],
            'pub_title': parts[3],
        })
        extra = parts[4].split("[+]")
        d.update({
            'volume': extra[0],
            'journal': extra[2],
        })
        if extra[1].find("AGU:") == 0:
            d.update({'agu_cite': extra[1][4:]})
        else:
            d.update({'pages': extra[1]})

        d.update(add_ancillary_info(parts))

    return render(request, "metaman/datasets/get_journal_ref.html",
                  {'data': d})


def get_preprint_ref(request):
    d = {}
    d.update({'relation_options': utils.ds_relationship_options()})
    if 'editItem' in request.POST:
        parts = request.POST['editItem'].split("[!]")
        d.update({
            'replace_item': request.POST['editItem'].replace("'", "\\'"),
            'authors': parts[1],
            'pub_year': parts[2],
            'pub_title': parts[3],
        })
        extra = parts[4].split("[+]")
        d.update({
            'host': extra[0],
            'location': extra[1],
            'pages': extra[2],
            'conference': extra[3],
        })
        d.update(add_ancillary_info(parts))

    return render(request, "metaman/datasets/get_preprint_ref.html",
                  {'data': d})


def get_site(request):
    d = {}
    if 'editItem' in request.POST:
        parts = request.POST['editItem'].split("[!]")
        d.update({'replace_item': request.POST['editItem'].replace("'", "\\'"),
                  'url': parts[0], 'description': parts[1]})

    return render(request, "metaman/datasets/get_site.html", {'data': d})


def get_ref_list(request):
    ctx = {}
    if 'editItem' in request.POST:
        parts = request.POST['editItem'].split("[!]")
        ctx.update({'edit_item': request.POST['editItem'],
                    'url': parts[0], 'description': parts[1]})

    return render(request, "metaman/datasets/get_ref_list.html", ctx)


def get_technote_ref(request):
    d = {}
    d.update({'relation_options': utils.ds_relationship_options()})
    if 'editItem' in request.POST:
        parts = request.POST['editItem'].split("///")
        d.update({'item_num': parts[-1]})
        parts = parts[0].split("[!]")
        d.update({
            'replace_item': request.POST['editItem'].replace("'", "\\'"),
            'authors': parts[1],
            'pub_year': parts[2],
            'pub_title': parts[3],
        })
        extra = parts[4].split("[+]")
        d.update({
            'id': extra[0],
            'pages': extra[1],
            'organization': extra[2],
        })
        d.update(add_ancillary_info(parts))

    return render(request, "metaman/datasets/get_technote_ref.html",
                  {'data': d})


def get_reference(request):
    return render(request, "metaman/datasets/get_reference.html")


def get_redundancy(request):
    d = {}
    if 'editItem' in request.POST:
        parts = request.POST['editItem'].split("[!]")
        d.update({
            'replace_item': request.POST['editItem'].replace("'", "\\'"),
            'url': parts[0],
            'name': parts[1],
            'address': parts[2].replace("\\n", "\n"),
        })

    return render(request, "metaman/datasets/get_redundancy.html", {'data': d})


def get_period(request):
    if 'edit_dsid' not in request.POST:
        return render(request, "404.html")

    conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
    cursor = conn.cursor()
    cursor.execute("select iso_topic from metautil.metaman where dsid = %s",
                   (request.POST['edit_dsid'], ))
    res = cursor.fetchone()
    if res is None:
        cursor.close()
        return render(request, "404.html")

    d = {'is_elevation': (res[0] == "elevation"), 'period_type': "modern"}
    cursor.execute("select grpid from dssdb.dsgroup where dsid = %s",
                   (request.POST['edit_dsid'], ))
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    grp_opts = []
    for e in res:
        grp_opts.append({'value': e[0]})

    d.update({'group_options': grp_opts})
    if 'editItem' in request.POST:
        d.update({'replace_item': request.POST['editItem']})
        parts = request.POST['editItem'].split("[!]")
        keystart = ''
        if len(parts) == 4 and parts[3] == "BCE":
            d['period_type'] = "paleo"
            keystart = 'p'

        sparts = parts[0].split()
        dparts = sparts[0].split("-")
        d.update({keystart + 'syr': dparts[0]})
        if len(dparts) > 1:
            d.update({keystart + 'smo': dparts[1]})
            if len(dparts) > 2:
                d.update({'sdy': dparts[2]})
                if len(sparts) > 1:
                    tparts = sparts[1].split(":")
                    d.update({'shr': tparts[0]})
                    if len(tparts) > 1:
                        d.update({'smin': tparts[1]})
                        if len(tparts) > 2:
                            d.update({'ssec': tparts[2]})

                    if len(sparts) > 2:
                        d.update({'tz': sparts[2]})

        eparts = parts[1].split()
        dparts = eparts[0].split("-")
        d.update({keystart + 'eyr': dparts[0]})
        if len(dparts) > 1:
            d.update({keystart + 'emo': dparts[1]})
            if len(dparts) > 2:
                d.update({'edy': dparts[2]})
                if len(eparts) > 1:
                    tparts = eparts[1].split(":")
                    d.update({'ehr': tparts[0]})
                    if len(tparts) > 1:
                        d.update({'emin': tparts[1]})
                        if len(tparts) > 2:
                            d.update({'esec': tparts[2]})

        grpid = parts[2]
        d.update({'grpid': grpid})

    return render(request, "metaman/datasets/get_period.html", {'data': d})


def get_temporal_frequency(request):
    d = {'type': "", 'unit': "", 'ival': "", 'stats': ""}
    if 'editItem' in request.POST:
        d.update({'replace_item': request.POST['editItem']})
        parts = request.POST['editItem'].split("[!]")
        d['type'] = parts[0]
        if d['type'] == "irregular" or d['type'] == "climatology":
            d['unit'] = parts[1]
        elif d['type'] == "regular":
            d['ival'] = parts[1]
            d['unit'] = parts[2]
            if len(parts) > 3:
                d['stats'] = parts[3]

    try:
        tree = ElementTree.parse("/data/web/metadata/schemas/dsOverview3.xsd")
        root = tree.getroot()
        ns = {
            'xsd': "http://www.w3.org/2001/XMLSchema",
        }
        elist = root.findall((
                "./xsd:element[@name='contentMetadata']/xsd:complexType/xsd:"
                "choice/xsd:sequence/xsd:element[@name='temporalFrequency']/"
                "xsd:complexType/xsd:attribute[@name='unit']/xsd:simpleType/"
                "xsd:restriction/xsd:enumeration"), ns)
        freq_opts = []
        for e in elist:
            freq_opts.append({'value': e.get("value")})

        d.update({'frequency_options': freq_opts})
        elist = root.findall((
                "./xsd:element[@name='contentMetadata']/xsd:complexType/xsd:"
                "choice/xsd:sequence/xsd:element[@name='temporalFrequency']/"
                "xsd:complexType/xsd:attribute[@name='statistics']/xsd:"
                "simpleType/xsd:restriction/xsd:enumeration"), ns)
        stats_opts = []
        for e in elist:
            stats_opts.append({'value': e.get("value")})

        d.update({'stats_options': stats_opts})
    except Exception:
        pass

    return render(request, "metaman/datasets/get_temporal_frequency.html",
                  {'data': d})


def get_data_type(request):
    d = {'type': "", 'proc': "", 'nhour': ""}
    if 'editItem' in request.POST:
        d.update({'replace_item': request.POST['editItem']})
        parts = request.POST['editItem'].split("[!]")
        d['type'] = parts[0]
        if len(parts) > 1:
            d['proc'] = parts[-1]
            idx = d['proc'].find("-hour")
            if idx >= 0:
                d['nhour'] = d['proc'][0:idx]
                d['proc'] = d['proc'][idx+6:]

    try:
        tree = ElementTree.parse("/data/web/metadata/schemas/dsOverview3.xsd")
        root = tree.getroot()
        ns = {
            'xsd': "http://www.w3.org/2001/XMLSchema",
        }
        elist = root.findall((
                "./xsd:element[@name='contentMetadata']/xsd:complexType/xsd:"
                "choice/xsd:sequence/xsd:element[@name='dataType']/xsd:"
                "complexType/xsd:simpleContent/xsd:restriction/xsd:"
                "enumeration"), ns)
        dt_opts = []
        for e in elist:
            dt_opts.append({'value': e.get("value")})

        d.update({'data_type_options': dt_opts})
    except Exception:
        pass

    return render(request, "metaman/datasets/get_data_type.html", {'data': d})


def get_layer(request):
    return get_level_layer(request, "layer")


def get_level(request):
    return get_level_layer(request, "level")


def get_level_layer(request, type):
    d = {'type': type}
    try:
        tree = ElementTree.parse("/data/web/metadata/schemas/dsOverview3.xsd")
        root = tree.getroot()
        ns = {
            'xsd': "http://www.w3.org/2001/XMLSchema",
        }
        elist = root.findall((
                "./xsd:element[@name='contentMetadata']/xsd:complexType/xsd:"
                "choice/xsd:sequence/xsd:element[@name='levels']/xsd:"
                "complexType/xsd:sequence/xsd:element[@name='" + type + "']/"
                "xsd:complexType/xsd:attribute[@name='type']/xsd:simpleType/"
                "xsd:restriction/xsd:enumeration"), ns)
        lev_opts = []
        for e in elist:
            lev_opts.append({'value': e.get("value")})

        d.update({'level_options': lev_opts})
    except Exception:
        pass

    return render(request, "metaman/datasets/get_level.html", {'data': d})


def get_coverage(request):
    d = {}
    if 'editItem' in request.POST:
        d.update({'replace_item': request.POST['editItem']})
        parts = request.POST['editItem'].split("[!]")
        d.update({'coverage_type': parts[0], 'grid_nx': parts[1],
                  'grid_ny': parts[2]})
        if parts[0] == "latLon" or parts[0] == "mercator":
            d.update({'grid_slon': parts[3][0:-1], 'grid_slon_h': parts[3][-1],
                      'grid_slat': parts[4][0:-1], 'grid_slat_h': parts[4][-1],
                      'grid_elon': parts[5][0:-1], 'grid_elon_h': parts[5][-1],
                      'grid_elat': parts[6][0:-1], 'grid_elat_h': parts[6][-1],
                      'grid_xres': parts[7], 'grid_yres': parts[8]})
            if len(parts) > 9 and parts[9] == "cell":
                d.update({'grid_cell': True})

        elif parts[0] == "gaussLatLon":
            d.update({'grid_slon': parts[3][0:-1], 'grid_slon_h': parts[3][-1],
                      'grid_slat': parts[4][0:-1], 'grid_slat_h': parts[4][-1],
                      'grid_elon': parts[5][0:-1], 'grid_elon_h': parts[5][-1],
                      'grid_elat': parts[6][0:-1], 'grid_elat_h': parts[6][-1],
                      'grid_xres': parts[7], 'gauss_circles': parts[8]})
        elif parts[0] == "lambertConformal":
            d.update({'grid_slon': parts[3][0:-1], 'grid_slon_h': parts[3][-1],
                      'grid_slat': parts[4][0:-1], 'grid_slat_h': parts[4][-1],
                      'grid_projlon': parts[5][0:-1],
                      'grid_projlon_h': parts[5][-1],
                      'grid_reslat': parts[6][0:-1],
                      'grid_reslat_h': parts[6][-1],
                      'grid_xres': parts[7], 'grid_yres': parts[8],
                      'grid_pole': parts[9],
                      'grid_parallel1': parts[10][0:-1],
                      'grid_parallel1_h': parts[10][-1],
                      'grid_parallel2': parts[11][0:-1],
                      'grid_parallel2_h': parts[11][-1]})
        elif parts[0] == "polarStereographic":
            d.update({'grid_swlon': parts[3][0:-1],
                      'grid_swlon_h': parts[3][-1],
                      'grid_swlat': parts[4][0:-1],
                      'grid_swlat_h': parts[4][-1],
                      'grid_projlon': parts[5][0:-1],
                      'grid_projlon_h': parts[5][-1],
                      'grid_xres': parts[6], 'grid_yres': parts[7],
                      'grid_pole': parts[8]})
            if len(parts) > 9 and parts[9] == "truncated":
                d.update({'grid_truncated': True})

    elif 'coverage_type' not in request.POST:
        data_types = request.POST['data_types'].split("\n")
        already = []
        opts = []
        for data_type in data_types:
            parts = data_type.split("[!]")
            if parts[0] not in already and parts[0] == "grid":
                try:
                    tree = ElementTree.parse(
                            "/data/web/metadata/schemas/common.xsd")
                    root = tree.getroot()
                    ns = {
                        'xsd': "http://www.w3.org/2001/XMLSchema",
                    }
                    elist = root.findall((
                            "./xsd:simpleType[@name='gridDefinition']/xsd:"
                            "restriction/xsd:enumeration"), ns)
                    for e in elist:
                        opts.append({'value': e.get("value"),
                                     'description': e.get("value") + " grid"})

                    already.append(parts[0])
                except Exception:
                    pass

        d.update({'coverage_options': opts})
    else:
        d.update({'coverage_type': request.POST['coverage_type']})

    return render(request, "metaman/datasets/get_coverage.html", {'data': d})


def get_author(request):
    if 'edit_dsid' not in request.POST:
        return render(request, "404.html")

    has_doi = utils.has_doi(request.POST['edit_dsid'])
    if type(has_doi) is str:
        return render(request, "metaman/datasets/get_author.html",
                      {'error': ("unable to check if dataset has a DOI: '" +
                                 has_doi + "'")})

    d = {'has_doi': utils.has_doi(request.POST['edit_dsid']),
         'fname': "", 'mname': "", 'lname': "", 'orcid_id': "",
         'corp_name': "", 'from_ris': False}
    iuser = utils.get_iuser(request)
    d.update({'is_manager': (iuser in config.metadata_managers)})
    if 'editItem' in request.POST:
        d.update({'replace_item': request.POST['editItem']})
        parts = request.POST['editItem'].split("[!]")
        if len(parts) in (3, 4):
            d['fname'] = parts[0]
            d['mname'] = parts[1]
            d['lname'] = parts[2]
            if len(parts) == 4:
                d['orcid_id'] = parts[3]

        elif len(parts) == 1:
            d['corp_name'] = parts[0]

    elif 'ris_file' in request.FILES:
        s = ""
        for chunk in request.FILES['ris_file']:
            s += chunk.decode("utf-8")

        lines = s.split("\n")
        tag = re.compile("^A[U2]  - ")
        authors = []
        for line in lines:
            if tag.match(line):
                parts = line[6:].split(",")
                if len(parts) != 2 or len(parts[-1]) == 0:
                    return render(request,
                                  "metaman/datasets/get_author.html",
                                  {'error': ("Author line is not in proper "
                                             "RIS format")})

                if len(authors) > 0:
                    authors.append((utils.trim(parts[-1]) + " " +
                                    utils.trim(parts[0])))
                else:
                    authors.append((utils.trim(parts[0]) + ", " +
                                    utils.trim(parts[-1])))

        d.update({'authors': ", ".join(authors)})
        d['from_ris'] = True

    return render(request, "metaman/datasets/get_author.html", {'data': d})


def get_gcmd_keywords(keyword_list, search_words):
    words = search_words.split()
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        query = ("select distinct path, uuid from search.gcmd_" +
                 keyword_list + " where cflag != 9")
        if words[0] != "SHOW_ALL":
            query += " and " + " and ".join([
                    "path ilike '%" + word + "%'" for word in words])

        cursor.execute(query + " order by path")
        res = cursor.fetchall()
        cursor.close()
        conn.close()
        return res
    except psycopg2.Error as err:
        return "{}".format(err)


def get_platform(request):
    ctx = {'keyword_type': "platform", 'keyword_title': "Platform"}
    if 'search' in request.POST:
        res = get_gcmd_keywords("platforms", request.POST['search'])
        if type(res) is str:
            return render(request,
                          "metaman/datasets/get_descriptive_keyword.html",
                          {'error': "database error '{}'".format(res)})

        ctx.update({'results': res})

    return render(request, "metaman/datasets/get_descriptive_keyword.html",
                  ctx)


def get_instrument(request):
    ctx = {'keyword_type': "instrument", 'keyword_title': "Instrument"}
    if 'search' in request.POST:
        res = get_gcmd_keywords("instruments", request.POST['search'])
        if type(res) is str:
            return render(request,
                          "metaman/datasets/get_descriptive_keyword.html",
                          {'error': "database error '{}'".format(res)})

        ctx.update({'results': res})

    return render(request, "metaman/datasets/get_descriptive_keyword.html",
                  ctx)


def get_project(request):
    ctx = {'keyword_type': "project", 'keyword_title': "Project"}
    if 'search' in request.POST:
        res = get_gcmd_keywords("projects", request.POST['search'])
        if type(res) is str:
            return render(request,
                          "metaman/datasets/get_descriptive_keyword.html",
                          {'error': "database error '{}'".format(res)})

        ctx.update({'results': res})

    return render(request, "metaman/datasets/get_descriptive_keyword.html",
                  ctx)


def get_supports_project(request):
    ctx = {'keyword_type': "supports_project",
           'keyword_title': "Supports Project"}
    if 'search' in request.POST:
        res = get_gcmd_keywords("projects", request.POST['search'])
        if type(res) is str:
            return render(request,
                          "metaman/datasets/get_descriptive_keyword.html",
                          {'error': "database error '{}'".format(res)})

        ctx.update({'results': res})

    return render(request, "metaman/datasets/get_descriptive_keyword.html",
                  ctx)


def get_sciencekeyword(request):
    ctx = {'keyword_type': "sciencekeyword", 'keyword_title': "Variable"}
    if 'search' in request.POST:
        res = get_gcmd_keywords("sciencekeywords", request.POST['search'])
        if type(res) is str:
            return render(request,
                          "metaman/datasets/get_descriptive_keyword.html",
                          {'error': "database error '{}'".format(res)})

        ctx.update({'results': res})

    return render(request, "metaman/datasets/get_descriptive_keyword.html",
                  ctx)


render_map = {
    'author': {
        'getter': get_author,
        'edit-title': "Edit an Author",
        'remove-title': "Remove an Author",
    },
    'book_ref': {
        'getter': get_book_ref,
        'edit-title': "Edit a Book Reference",
    },
    'bookchapter_ref': {
        'getter': get_bookchapter_ref,
        'edit-title': "Edit a Book Chapter Reference",
    },
    'contact': {
        'getter': get_contact,
        'remove-title': "Remove a Dataset Contact",
    },
    'contributor': {
        'getter': get_contributor,
        'edit-title': "Edit a Contributor",
        'remove-title': "Remove a Contributor",
    },
    'coverage': {
        'getter': get_coverage,
        'edit-title': "Edit Coverage Information",
        'remove-title': "Remove Coverage Information",
    },
    'data_type': {
        'getter': get_data_type,
        'edit-title': "Edit a Data Type",
        'remove-title': "Remove a Data Type",
    },
    'datasets': {
        'getter': get_datasets,
    },
    'doi': {
        'getter': get_doi,
    },
    'instrument': {
        'getter': get_instrument,
        'remove-title': "Remove an Instrument Keyword",
    },
    'journal_ref': {
        'getter': get_journal_ref,
        'edit-title': "Edit a Journal Reference",
    },
    'layer': {
        'getter': get_layer,
    },
    'level': {
        'getter': get_level,
        'remove-title': "Remove a Vertical Level",
    },
    'period': {
        'getter': get_period,
        'edit-title': "Edit a Data Period",
        'remove-title': "Remove a Data Period",
    },
    'platform': {
        'getter': get_platform,
        'remove-title': "Remove a Platform Keyword",
    },
    'preprint_ref': {
        'getter': get_preprint_ref,
        'edit-title': "Edit a Conference Proceeding Reference",
    },
    'project': {
        'getter': get_project,
        'remove-title': "Remove a Project Keyword",
    },
    'redundancy': {
        'getter': get_redundancy,
        'edit-title': "Edit a Dataset Redundancy",
        'item-start': 1,
        'remove-title': "Remove a Dataset Redundancy",
    },
    'ref_list': {
        'getter': get_ref_list,
    },
    'reflist': {
        'getter': get_ref_list,
        'edit-title': "Edit a List of References",
        'remove-title': "Remove a List of References",
    },
    'reference': {
        'getter': get_reference,
        'edit-title': "Edit a Publication Reference",
        'remove-title': "Remove a Publication Reference",
    },
    'related_dataset': {
        'remove-title': "Remove a Related Dataset",
    },
    'related_doi': {
        'remove-title': "Remove a Related DOI",
    },
    'related_site': {
        'getter': get_site,
        'edit-title': "Edit a Related Website",
        'remove-title': "Remove a Related Website",
    },
    'sciencekeyword': {
        'getter': get_sciencekeyword,
        'remove-title': "Remove a Variable Keyword",
    },
    'site': {
        'getter': get_site,
    },
    'supports_project': {
        'getter': get_supports_project,
        'remove-title': "Remove a Supports Project Keyword",
    },
    'technote_ref': {
        'getter': get_technote_ref,
        'edit-title': "Edit a Technical Report Reference",
    },
    'temporal_frequency': {
        'getter': get_temporal_frequency,
        'edit-title': "Edit a Temporal Frequency",
        'remove-title': "Remove a Temporal Frequency",
    },
}
