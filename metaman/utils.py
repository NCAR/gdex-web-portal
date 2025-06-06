import glob
import os
import psycopg2
import re
import requests
import shutil
import smtplib
import subprocess
import sys
import tempfile

from email.message import EmailMessage
from lxml import etree as ElementTree

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render

from .config import bin_utils, linkcheck_headers, markup_schemas, root_dirs
from . import strutils
from .xmlutils import convert_html_to_text, xml_split


def get_iuser(request):
    if (settings.ICOOKIE['id'] not in request.COOKIES or
            request.COOKIES[settings.ICOOKIE['id']].find("@") < 0):
        return ""

    return request.COOKIES[settings.ICOOKIE['id']][
            0:request.COOKIES[settings.ICOOKIE['id']].find("@")]


def ds_relationship_options():
    rel_opts = []
    try:
        tree = ElementTree.parse(
                root_dirs['web'] + "/metadata/schemas/dsOverview3.xsd")
        root = tree.getroot()
        ns = {
            'xsd': "http://www.w3.org/2001/XMLSchema",
        }
        e = root.find((
                "./xsd:element[@name='reference']/xsd:complexType/xsd:"
                "attribute[@name='ds_relation']/xsd:simpleType/xsd:"
                "restriction"), ns)
        for enumeration in e.findall("xsd:enumeration", ns):
            rel_opts.append({
                    'value': enumeration.get("value"),
                    'description': enumeration.find((
                            "xsd:annotation/xsd:documentation"), ns).text})
    except Exception:
        pass

    return rel_opts


def make_tempdir():
    try:
        tdir_name = tempfile.mkdtemp(dir="/data/ptmp")
        os.chmod(tdir_name, 0o777)
        return tdir_name
    except Exception:
        return ""


def remove_tempdir(tdir_name):
    try:
        shutil.rmtree(tdir_name)
    except Exception:
        pass


def choose_existing_dataset(request):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    d = {}
    if 'slug' in request.POST:
        d.update({'slug': request.POST['slug']})
    else:
        return render(request, "metaman/bad_request.html",
                      {'missing_key': "slug"})

    if 'parent' not in request.POST:
        return render(request, "metaman/bad_request.html",
                      {'missing_key': "parent"})
    else:
        if request.POST['parent'] == "manage-datasets":
            if request.POST['slug'] == "delete":
                d.update({'dsids': dsids_never_published()})
            else:
                d.update({'dsids': dsids_from_cvs()})

        elif request.POST['parent'] == "manage-dataset-dois":
            if request.POST['slug'] in {"adopt", "create"}:
                d.update({'dsids': dsids_without_doi()})
            else:
                d.update({'dsids': dsids_with_doi()})

        else:
            return render(request, "metaman/bad_request.html",
                          {'bad_value': {'key': "parent"}})

    if 'description' in request.POST:
        d.update({'description': request.POST['description']})

    return render(request, "metaman/choose_existing_dataset.html", d)


def show_logos(request):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    logos = []
    files = glob.glob(root_dirs['web'] + "/images/ds_logos/*")
    for file in files:
        file = file.replace(root_dirs['web'], "")
        d = {'src': file}
        logo_parts = file.split(".")
        geom_parts = logo_parts[-2].split("_")
        width = 70
        if geom_parts[-2] != geom_parts[-1]:
            w = int(geom_parts[-2])
            h = int(geom_parts[-1])
            width = round(w * 70. / h)

        d.update({'width': width})
        logo_parts = file.split("/")
        d.update({'name': logo_parts[-1]})
        logos.append(d)

    return render(request, "metaman/datasets/logo_library.html",
                  {'logos': logos})


def show_words(request):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    ctx = {'no_results': True}
    if 'pattern' in request.POST:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute((
                "select word from metautil.word_valids where word ilike %s "
                "order by word"), (request.POST['pattern'], ))
        res = cursor.fetchall()
        words = []
        if len(res) > 0:
            ctx['no_results'] = False
            for e in res:
                words.append(e[0])

        ctx.update({'regular_words': words})
        cursor.execute((
                "select word, description from metautil.acronym_valids where "
                "word ilike %s order by word"), (request.POST['pattern'], ))
        res = cursor.fetchall()
        acronyms = []
        if len(res) > 0:
            ctx['no_results'] = False
            for e in res:
                acronyms.append({'word': e[0], 'description': e[1]})

        ctx.update({'acronyms': acronyms})
        cursor.execute((
                "select word from metautil.place_valids where word ilike %s "
                "order by word"), (request.POST['pattern'], ))
        res = cursor.fetchall()
        places = []
        if len(res) > 0:
            ctx['no_results'] = False
            for e in res:
                places.append(e[0])

        ctx.update({'places': places})
        cursor.execute((
                "select word from metautil.name_valids where word ilike %s "
                "order by word"), (request.POST['pattern'], ))
        res = cursor.fetchall()
        names = []
        if len(res) > 0:
            ctx['no_results'] = False
            for e in res:
                names.append(e[0])

        ctx.update({'names': names})
        cursor.execute((
                "select word from metautil.other_exactmatch_valids where word "
                "ilike %s order by word"), (request.POST['pattern'], ))
        res = cursor.fetchall()
        others = []
        if len(res) > 0:
            ctx['no_results'] = False
            for e in res:
                others.append(e[0])

        ctx.update({'others': others})

    return render(request, "metaman/show_spellcheck.html", ctx)


def upload_logo(request):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    if 'logo_file' in request.FILES:
        try:
            filename = (root_dirs['web'] + "/" + request.POST['directory'] +
                        "/" + request.FILES['logo_file'].name)
            with open(filename, "wb") as f:
                for chunk in request.FILES['logo_file']:
                    f.write(chunk)

            f.close()
            o = subprocess.run((
                    bin_utils['imagemagick']['identify'] + " " + filename),
                    shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            err = o.stderr.decode("utf-8")
            if len(err) > 0:
                return render(request, "metaman/datasets/logo_upload.html",
                              {'error': ("unable to identify image: '" + err +
                                         "'")})

            parts = o.stdout.decode("utf-8").split()
            geom_parts = parts[2].split("x")
            if int(geom_parts[0]) < 70 or int(geom_parts[1]) < 70:
                subprocess.run("/bin/rm " + filename, shell=True)
                return render(request, "metaman/datasets/logo_upload.html",
                              {'error': ("The image that you uploaded did not "
                                         "meet the minimum dimensions "
                                         "requirement of 70x70 pixels.")})

            idx = filename.rfind(".")
            o = subprocess.run((
                    "/bin/mv " + filename + " " + filename[0:idx] + "_" +
                    geom_parts[0] + "_" + geom_parts[1] + filename[idx:]),
                    shell=True, stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE)
            err = o.stderr.decode("utf-8")
            if len(err) > 0:
                return render(request, "metaman/datasets/logo_upload.html",
                              {'error': ("unable to rename logo: '" + str(err)
                                         + "'")})

        except Exception as err:
            return render(request, "metaman/datasets/logo_upload.html",
                          {'error': str(err)})

    return render(request, "metaman/datasets/logo_upload.html")


def rdadata_rsync(local_dir, relative_local_path, remote_path):
    hosts = ["rda-web-prod01", "rda-web-test01"]
    errs = []
    for host in hosts:
        o = subprocess.run((
                "cd " + local_dir + "; " + bin_utils['rdadatarun'] + " rsync "
                "-rptgD --relative " + relative_local_path + " " + host +
                ".ucar.edu:" + remote_path),
                shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        o = o.stderr.decode("utf-8")
        if len(o) > 0:
            errs.append(o)

    return "\n".join(errs)


def reorder_authors(request):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    if 'authorList' not in request.POST:
        return render(request, "400.html")

    authors = request.POST['authorList'].splitlines()
    author_list = []
    for author in authors:
        author_list.append(author)

    return render(request, "metaman/datasets/reorder_authors.html",
                  {'authors': author_list})


def dsids_from_cvs():
    dsids = []
    files = glob.glob((
            "/data/cvs/datasets/d[0-9][0-9][0-9][0-9][0-9][0-9].xml,v"))
    for file in files:
        idx = file.find("datasets/")
        if idx >= 0:
            s = file[idx+9:]
            idx = s.find(".xml,v")
            dsids.append(s[0:idx])

    dsids.sort()
    return dsids


def dsids_never_published():
    dsids = []
    conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
    cursor = conn.cursor()
    cursor.execute("select dsid from search.datasets where type = 'W'")
    res = cursor.fetchall()
    cursor.close()
    for e in res:
        dsids.append(e[0])

    dsids.sort()
    return dsids


def dsids_without_doi():
    dsids = []
    conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
    cursor = conn.cursor()
    cursor.execute((
            "select distinct s.dsid from search.datasets as s left join dssdb."
            "dsvrsn as v on v.dsid = s.dsid where s.dsid < 'd999000' and s."
            "type in ('P', 'H') and (v.doi is null or v.doi = 'X') order by s."
            "dsid"))
    res = cursor.fetchall()
    cursor.close()
    for e in res:
        dsids.append(e[0])

    dsids.sort()
    return dsids


def dsids_with_doi():
    dsids = []
    conn = psycopg2.connect(**settings.RDADB['dssdb_config_pg'])
    cursor = conn.cursor()
    cursor.execute((
            "select dsid from dssdb.dsvrsn where status = 'A' and dsid < "
            "'d999000' order by dsid"))
    res = cursor.fetchall()
    cursor.close()
    for e in res:
        dsids.append(e[0])

    dsids.sort()
    return dsids


def spellcheck_request(request):
    if 'words' in request.GET:
        user = get_iuser(request)
        if len(user) == 0:
            return HttpResponse("Error: unknown user", status=400)

        user += "@ucar.edu"
        try:
            smtp = smtplib.SMTP('localhost')
            msg = EmailMessage()
            msg['From'] = user
            subject = "Spellcheck words to add"
            if 'dsid' in request.GET:
                subject += " (" + request.GET['dsid'] + ")"

            msg['Subject'] = subject
            msg['To'] = "dattore@ucar.edu"
            msg['CC'] = user
            msg.set_content(request.GET['words'])
            smtp.send_message(msg)
            smtp.quit()
            return HttpResponse((
                    "Success: your request has been received"), status=200)

        except BaseException as err:
            return HttpResponse((
                    "Error: unable to send email: '" + str(err) + "'"),
                    status=500)

    return HttpResponse("Error: no words specified", status=400)


def log_error(error, **kwargs):
    if 'source' in kwargs:
        error = "source: '" + kwargs['source'] + "()' " + str(error)

    sys.stderr.write("METAMAN ERROR: '{}'\n".format(error))


def trim(text):
    if len(text) == 0:
        return ""

    text = trim_front(text)
    text = trim_back(text)
    return text


def trim_front(text):
    n = 0
    while n < len(text) and text[n] in (' ', '\t', '\n', '\r'):
        n += 1

    return text[n:]


def trim_back(text):
    n = len(text) - 1
    while n >= 0 and text[n] in (' ', '\t', '\n', '\r'):
        n -= 1

    return text[0:n+1]


def check_html(html, spellchecker):
    if len(html) == 0:
        return []

    errs = []
    html = trim(html)
    err = check_for_bad_characters(html)
    if len(err) > 0:
        errs.append(err)

    try:
        root = ElementTree.fromstring(html.replace("&", "&amp;"))
    except Exception as err:
        errs.append("XML parse error: <i>{}</i>".format(err))
        return errs

    if len(root.getchildren()) == 0:
        errs.append((
                "This field must be composed of one or more paragraphs - "
                "there is content somewhere that is not within a paragraph "
                "(&amp;lt;p&amp;gt;&amp;lt;/p&amp;gt;)."))

    for child in root:
        if child.tag not in ("p", "P"):
            errs.append((
                    "This field must be composed of one or more paragraphs - "
                    "there is content somewhere that is not within a "
                    "paragraph (&amp;lt;p&amp;gt;&amp;lt;/p&amp;gt;)."))

    check_text = "".join(
            [ElementTree.tostring(e).decode("ascii") for e in root])
    spellchecker.check(convert_html_to_text(html))
    if len(spellchecker.misspelled_words) > 0:
        errs.append((
                "- Misspelled/unrecognized word(s) must be corrected:<br><i>"
                + ", ".join(spellchecker.misspelled_words) + "</i>"))

    xparts = xml_split(html)
    checked_urls = set()
    for part in xparts:
        if part.find("<a href") == 0:
            anchor = ElementTree.fromstring(part + "</a>")
            if anchor.get("href") not in checked_urls:
                try:
                    response = requests.get(
                            anchor.get("href"), headers=linkcheck_headers)
                    response.raise_for_status()
                except Exception:
                    errs.append((
                            "- Unresolvable URL <i>" + anchor.get("href") +
                            "</i> (" + str(response.status_code) + ") must be "
                            "fixed or removed"))

                checked_urls.add(anchor.get("href"))

    return errs


def check_for_bad_characters(text):
    start = 0
    if text[0] == '<':
        start = text.find(">") + 1

    bad_chars = []
    for n in range(start, len(text)):
        i = ord(text[n])
        if i < 9 or (i > 10 and i < 32) or i == 96 or i > 126:
            bad_chars.append(n-start+1)

    if len(bad_chars) == 0:
        return ""

    return ("Non-text characters are not allowed here (position(s) " +
            ", ".join(str(x) for x in bad_chars) + ").")


def has_doi(dsid):
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute((
                "select doi from dssdb.dsvrsn where dsid = %s and status = "
                "'A'"), (dsid, ))
        res = cursor.fetchone()
        cursor.close()
        conn.close()
        return res is not None
    except psycopg2.Error as err:
        return str(err)


def cite_contributors(request):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    if 'action' not in request.POST or 'contributorList' not in request.POST:
        return render(request, "404.html")

    ctx = {}
    if 'citable' in request.POST:
        ctx.update({'citable': (request.POST['citable'] == "true")})

    contributors = request.POST['contributorList'].split("\n")
    if len(contributors[-1]) == 0:
        contributors.pop()

    if request.POST['action'] == "cite" and ctx['citable']:
        c = []
        for item in contributors:
            parts = item.split("[!]")
            c.append({'description': parts[0], 'cited': parts[4],
                      'item': item})

        ctx.update({'contributors': c})
    else:
        y = []
        n = []
        for item in contributors:
            parts = item.split("[!]")
            if parts[4] == "Y":
                y.append({'description': parts[0], 'item': item})
            else:
                n.append({'description': parts[0], 'item': item})

        ctx.update({'contributors': {'cited': y, 'uncited': n}})

    return render(request, "metaman/datasets/cite_contributors.html", ctx)


def metadata_summary(request, dsid):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    if 'editItem' in request.POST and request.POST['editItem'] == "inv":
        return show_missing_inv(request, dsid)

    ctx = {'dsid': dsid}
    cache_list = read_cache(dsid, cmd=True)
    if type(cache_list) is str:
        ctx.update({'error': cache_list})
        return render(request, "metaman/datasets/metadata_summary.html", ctx)

    ctx.update({'web_files': cache_list[0],
                'data_types': ", ".join(cache_list[1]),
                'data_formats': ", ".join([e.replace("_", " ") for e in
                                           cache_list[2]]),
                'num_cmd': 0, 'has_cmd_date_range': False})
    if len(cache_list[3]) > 0:
        ctx.update({'start_date': cache_list[3][0:cache_list[4]],
                    'end_date': cache_list[5][0:cache_list[6]]})
        ctx['has_cmd_date_range'] = True

    for file in ctx['web_files']:
        if file['has_cmd']:
            ctx['num_cmd'] += 1

    cache_list = read_cache(dsid, cmd=False)
    if type(cache_list) is str:
        ctx.update({'error': cache_list})
        return render(request, "metaman/datasets/metadata_summary.html", ctx)

    ctx['web_files'].extend(cache_list[0])
    if 'editItem' in request.POST and request.POST['editItem'] == "web":
        return render(request, "metaman/datasets/metadata_summary.html", ctx)

    ctx.update({'cmd_no_files': []})
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute((
                "select schemaname from pg_catalog.pg_tables where tablename "
                "like '" + dsid + "_webfiles2'"))
        res = cursor.fetchall()
        u = " union ".join([
                "select id from \"" + e[0] + "\"." + dsid + "_webfiles2" for e
                in res])
        if len(u) > 0:
            cursor.execute((
                    "select w.id, x.wfile from (" + u + ") as w left join "
                    "dssdb.wfile_" + dsid + " as x on (x.wfile = w.id and x."
                    "type = 'D' and x.status = 'P') where x.wfile is null"))
            res = cursor.fetchall()
            for e in res:
                ctx['cmd_no_files'].append(e[0])

    except psycopg2.Error as err:
        ctx.update({'error': ("database error while getting filenames with "
                              "content metadata but not archived for the "
                              "dataset: '{}'").format(err)})
        return render(request, "metaman/datasets/metadata_summary.html", ctx)

    if ctx['num_cmd'] == 0 and len(ctx['cmd_no_files']) == 0:
        ctx.update({'no_cmd': True})
        return render(request, "metaman/datasets/metadata_summary.html", ctx)

    ctx.update({'has_inventories': False, 'inv_cnt': 0, 'num_no_inv': 0})
    try:
        cursor.execute((" union ")
                       .join([("select substring(schemaname, 2) from "
                               "pg_catalog.pg_tables where schemaname = 'I" +
                               e + "' and tablename like '" + dsid +
                               "_inventory_summary'")
                              for e in markup_schemas]))
        res = cursor.fetchall()
        if len(res) > 0:
            cursor.execute((
                    "select 'inv_cnt', count(w.id) from \"W" + res[0][0] +
                    "\"." + dsid + "_webfiles2 as w left join \"I" +
                    res[0][0] + "\"." + dsid + "_inventory_summary as s on s."
                    "file_code = w.code where s.file_code is not null union "
                    "select 'num_no_inv', count(w.id) from \"W" + res[0][0] +
                    "\"." + dsid + "_webfiles2 as w left join \"I" +
                    res[0][0] + "\"." + dsid + "_inventory_summary as s on s."
                    "file_code = w.code where s.file_code is null"))
            res = cursor.fetchall()
            for e in res:
                if e[0] == "inv_cnt":
                    ctx['inv_cnt'] = int(e[1])
                elif e[0] == "num_no_inv":
                    ctx['num_no_inv'] = int(e[1])

            ctx['has_inventories'] = True

    except psycopg2.Error as err:
        ctx.update({'error': ("database error while getting inventory counts "
                              "for the dataset: '{}'").format(err)})
        return render(request, "metaman/datasets/metadata_summary.html", ctx)

    if 'Grid' in ctx['data_types']:
        try:
            cursor.execute((
                    "select distinct t.time_range from \"WGrML\".summary as s "
                    "left join \"WGrML\".time_ranges as t on t.code = s."
                    "time_range_code where s.dsid = %s order by t.time_range"),
                    (dsid, ))
            res = cursor.fetchall()
            prods = []
            for e in res:
                prods.append(e[0])

            ctx.update({'grid_products': prods})
        except psycopg2.Error as err:
            ctx.update({'error': ("database error while getting grid products "
                                  "for the dataset: '{}'").format(err)})
            return render(request, "metaman/datasets/metadata_summary.html",
                          ctx)

    return render(request, "metaman/datasets/metadata_summary.html", ctx)


def show_missing_inv(request, dsid):
    ctx = {'dsid': dsid}
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        for schema in markup_schemas:
            cursor.execute((
                    "select tablename from pg_catalog.pg_tables where "
                    "schemaname = 'I" + schema + "' and tablename like '" +
                    dsid + "_inventory_summary'"))
            res = cursor.fetchone()
            if res is not None:
                cursor.execute((
                        "select w.id, s.file_code from \"W" + schema + "\"." +
                        dsid + "_webfiles2 as w left join \"I" + schema +
                        "\"." + dsid + "_inventory_summary as s on s."
                        "file_code = w.code where s.file_code is null"))
                res = cursor.fetchall()
                inv_list = []
                for e in res:
                    inv_list.append(e[0])

                ctx.update({'missing_inv_list': inv_list})
                return render(request,
                              "metaman/datasets/metadata_summary.html", ctx)

        ctx.update({'error': "no inventory database exists for this dataset"})
        return render(request, "metaman/datasets/metadata_summary.html", ctx)
    except psycopg2.Error as err:
        ctx.update({'error': "database error: '{}'".format(err)})
        return render(request, "metaman/datasets/metadata_summary.html", ctx)

    return render(request, "metaman/datasets/metadata_summary.html", ctx)


def read_cache(dsid, **kwargs):
    ret_list = [[], [], [], "9999-99-99 99:99:99", 0, "0000-00-00 00:00:00", 0]
    if 'cmd' in kwargs:
        s = ""
        if not kwargs['cmd']:
            s = "_nonCMD"

        try:
            with open((root_dirs['web'] + "/datasets/" + dsid +
                       "/metadata/getWebList" + s + ".cache"), "r") as f:
                f.readline()
                if not kwargs['cmd']:
                    f.readline()

                for line in f:
                    parts = line.split("<!>")
                    ret_list[0].append({'name': parts[0],
                                        'data_format': parts[1],
                                        'has_cmd': kwargs['cmd']})
                    if kwargs['cmd']:
                        parts[8] = parts[8].strip()
                        dt = ""
                        if parts[8][-4:] == "GrML":
                            dt = "Grid"
                        elif parts[8][-4:] == "ObML":
                            dt = "Platform Observation"
                        elif parts[8][-5:] == "SatML":
                            if parts[2].find("Image") > 0:
                                dt = "Image"
                            elif parts[2].find("Scan") > 0:
                                dt = "Swath"
                        elif parts[8][-5:] == "FixML":
                            dt = "Cyclone Fix"

                        if len(dt) > 0 and dt not in ret_list[1]:
                            ret_list[1].append(dt)

                        if parts[1] not in ret_list[2]:
                            ret_list[2].append(parts[1])

                        sdt = parts[3].strip()
                        dt_parts = sdt.split()
                        dparts = dt_parts[0].split("-")
                        if len(dparts) == 3:
                            sdt_prec = 10
                        elif len(dparts) == 2:
                            sdt_prec = 7
                            sdt += "-01"
                        else:
                            sdt_prec = 4
                            sdt += "-01-01"

                        if len(dt_parts) > 1:
                            tparts = dt_parts[1].split(":")
                            if len(tparts) == 3:
                                sdt_prec = 19
                            elif len(tparts) == 2:
                                sdt_prec = 16
                                sdt += ":00"
                            else:
                                sdt_prec = 13
                                sdt += ":00:00"

                        ret_list[3] = min(sdt, ret_list[3])
                        ret_list[4] = max(sdt_prec, ret_list[4])
                        edt = parts[4].strip()
                        dt_parts = edt.split()
                        dparts = dt_parts[0].split("-")
                        if len(dparts) == 3:
                            edt_prec = 10
                        elif len(dparts) == 2:
                            edt_prec = 7
                            edt += "-12"
                        else:
                            edt_prec = 4
                            edt += "-12-31"

                        if len(dt_parts) > 1:
                            tparts = dt_parts[1].split(":")
                            if len(tparts) == 3:
                                edt_prec = 19
                            elif len(tparts) == 2:
                                edt_prec = 16
                                edt += ":59"
                            else:
                                edt_prec = 13
                                edt += ":59:59"

                        ret_list[5] = max(edt, ret_list[5])
                        ret_list[6] = max(edt_prec, ret_list[6])

        except Exception:
            pass

    return ret_list


def extract_contributors(list):
    contributors = []
    if len(list) == 0:
        return contributors

    clst = list.split("\n")
    for e in clst:
        parts = e.split("[!]")
        if len(parts) == 5:
            d = {'uuid': parts[1]}
            if len(parts[2]) > 0:
                d.update({'former_name': parts[2]})

            if len(parts[3]) > 0:
                if (parts[3].find("http://") == 0 or parts[3].find("https://")
                        == 0 or parts[3].find("ftp://") == 0):
                    idx = parts[3].find(";")
                    if idx < 0:
                        d.update({'url': parts[3]})
                    else:
                        d.update({'url': parts[3][0:idx],
                                  'contact': parts[3][idx+1:]})
                else:
                    d.update({'contact': parts[3]})

            if parts[4] == "Y":
                d.update({'citable': "yes"})
            else:
                d.update({'citable': "no"})

            contributors.append(d)

    return contributors


def extract_authors(list):
    authors = []
    if len(list) == 0:
        return authors

    alst = list.split("\n")
    for e in alst:
        parts = e.split("[!]")
        d = {}
        if len(parts) == 1:
            d.update({'corporation': parts[0]})
        elif len(parts) == 3 or len(parts) == 4:
            d.update({'fname': parts[0], 'mname': parts[1], 'lname': parts[2]})
            if len(parts) == 4 and len(parts[3]) > 0:
                d.update({'orcid_id': parts[3]})

        authors.append(d)

    return authors


def extract_references(list):
    ref_list = []
    ref_words = []
    if len(list) == 0:
        return (ref_list, ref_words)

    rlst = list.replace("&", "&amp;").split("\n")
    for e in rlst:
        parts = e.split("[!]")
        d = {'type': parts[0], 'author_list': parts[1], 'pub_year': parts[2],
             'title': parts[3]}
        ref_words.extend([parts[1], parts[2], parts[3]])
        sub_parts = parts[4].split("[+]")
        if parts[0] == "book":
            d.update({'pub_place': sub_parts[0], 'publisher': sub_parts[1]})
            ref_words.extend([sub_parts[0], sub_parts[1]])
        elif parts[0] == "book_chapter":
            d.update({'editor': sub_parts[0], 'publisher': sub_parts[1],
                      'pages': sub_parts[2], 'book': sub_parts[3]})
            ref_words.extend([sub_parts[0], sub_parts[1], sub_parts[2],
                              sub_parts[3]])
        elif parts[0] == "journal":
            d.update({'number': sub_parts[0], 'pages': sub_parts[1],
                      'journal': sub_parts[2]})
            ref_words.append(sub_parts[2])
        elif parts[0] == "preprint":
            d.update({'host': sub_parts[0], 'location': sub_parts[1],
                      'pages': sub_parts[2], 'conference': sub_parts[3]})
            ref_words.extend([sub_parts[0], sub_parts[1], sub_parts[3]])
        elif parts[0] == "technical_report":
            d.update({'report_id': sub_parts[0], 'pages': sub_parts[1],
                      'organization': sub_parts[2]})
            ref_words.extend([sub_parts[0], sub_parts[2]])

        next = 5
        while next < len(parts):
            if parts[next].find("ds_rel:") == 0:
                d.update({'ds_relation': parts[next][7:]})
            elif parts[next].find("doi:") == 0:
                d.update({'doi': (parts[next][4:].replace("<", "&lt;")
                         .replace(">", "&gt;"))})
            elif parts[next].find("url:") == 0:
                d.update({'url': (parts[next][4:].replace("<", "&lt;")
                         .replace(">", "&gt;"))})
            elif parts[next].find("annotation:") == 0:
                d.update({'annotation': parts[next][11:]})

            next += 1

        ref_list.append(d)

    return (ref_list, ref_words)


def extract_time_ranges(dsid, list):
    if len(list) == 0:
        return []

    tlst = list.split("\n")
    rlst = []
    used_grp_ids = []
    num_grps = 0
    for e in tlst:
        rlst.append(e)
        parts = e.split("[!]")
        if parts[2] != "Entire Dataset":
            if parts[2] not in used_grp_ids:
                used_grp_ids.append(parts[2])

            num_grps += 1

    if num_grps > 0:
        if num_grps != len(rlst):
            return ("If one period is associated with a group ID, then all "
                    "periods must be associated with a group ID")
        elif num_grps != len(used_grp_ids):
            return "Each group can be assigned to only one data period"

    rlst.sort(key=compare_periods)
    tranges = []
    for e in rlst:
        parts = e.split("[!]")
        d = {'start': parts[0], 'end': parts[1], 'group_id': parts[2]}
        if len(parts) == 4:
            d.update({'type': parts[3]})

        tranges.append(d)

    return tranges


def compare_periods(e):
    yr_type = "ACE"
    parts = e.split("[!]")
    if len(parts) == 4:
        yr_type = parts[3]

    key = parts[1]
    idx = parts[1].find("-")
    if idx == 4:
        if yr_type == "ACE":
            key = "0" + key
        else:
            key = "x" + key

    if yr_type == "BCE":
        key = "-" + key

    return key


def extract_temporal_frequencies(list):
    frequencies = []
    klst = []
    if len(list) == 0:
        return (frequencies, klst)

    tlst = list.split("\n")
    for e in tlst:
        parts = e.split("[!]")
        d = {'type': parts[0]}
        if parts[0] == "irregular" or parts[0] == "climatology":
            d.update({'unit': parts[1]})
        elif parts[0] == "regular":
            d.update({'number': parts[1], 'unit': parts[2]})
            if len(parts) > 3 and len(parts[3]) > 0:
                d.update({'stats': parts[3]})

        frequencies.append(d)
        k = time_resolution_keyword(d)
        if len(k) > 0 and k not in klst:
            klst.append(k)

    return (frequencies, klst)


def extract_data_types(list):
    types = []
    if len(list) == 0:
        return types

    dlst = list.split("\n")
    for e in dlst:
        parts = e.split("[!]")
        d = {'description': parts[0]}
        if len(parts) > 1:
            d.update({'process': parts[1]})

        types.append(d)

    return types


def extract_data_formats(list, ascii_url, binary_url):
    formats = []
    if len(list) == 0:
        return formats

    dlst = list.split("\n")
    for e in dlst:
        d = {'description': e}
        if e == "proprietary_ASCII":
            if ascii_url is not None and len(ascii_url) > 0:
                d.update({'href': ascii_url})
        elif e == "proprietary_Binary":
            if binary_url is not None and len(binary_url) > 0:
                d.update({'href': binary_url})

        formats.append(d)

    return formats


def extract_detailed_variables(list):
    vars = []
    if len(list) == 0:
        return vars

    vlst = list.split("\n")
    for e in vlst:
        parts = e.split("::")
        d = {'description': parts[0]}
        if len(parts) > 1:
            parts[1] = parts[1].strip()
            if len(parts[1]) > 0:
                d.update({'units': parts[1]})

        vars.append(d)

    return vars


def extract_levels(list):
    levels = []
    if len(list) == 0:
        return levels

    llst = list.split("\n")
    for e in llst:
        parts = e.split("[!]")
        d = {'type': parts[0]}
        if len(parts) == 3:
            d.update({'value': parts[1]})
            if len(parts[2]) > 0:
                d.update({'units': parts[2]})

        else:
            d.update({'top': parts[1], 'bottom': parts[2]})
            if len(parts[3]) > 0:
                d.update({'units': parts[3]})

        levels.append(d)

    return levels


def extract_coverages(list):
    grids = []
    locations = []
    if len(list) == 0:
        return {'grids': grids, 'locations': locations}

    clst = list.split("\n")
    uuid = re.compile(r"^\w{8}-\w{4}-\w{4}-\w{4}-\w{12}$")
    for e in clst:
        parts = e.split("[!]")
        if uuid.match(parts[-1]):
            locations.append(parts[-1])
        else:
            d = {'definition': parts[0], 'numx': parts[1], 'numy': parts[2],
                 'start_lon': parts[3], 'start_lat': parts[4]}
            if d['definition'] == "gaussLatLon":
                d.update({'end_lon': parts[5], 'end_lat': parts[6],
                          'xres': parts[7], 'circles': parts[8]})
                res_type = 0
                max_res = float(parts[7])
            elif d['definition'] == "lambertConformal":
                d.update({'proj_lon': parts[5], 'res_lat': parts[6],
                          'xres': parts[7], 'yres': parts[8], 'pole': parts[9],
                          'sp1': parts[10], 'sp2': parts[11]})
                res_type = 1
                max_res = max(float(parts[7]), float(parts[8]))
            elif d['definition'] in ("latLon", "mercator"):
                d.update({'ll': True, 'end_lon': parts[5], 'end_lat': parts[6],
                          'xres': parts[7], 'yres': parts[8]})
                if len(parts) > 9 and parts[9] == "cell":
                    d.update({'is_cell': True})
                res_type = 0
                max_res = max(float(parts[7]), float(parts[8]))
            elif d['definition'] == "polarStereographic":
                d.update({'polar': True, 'proj_lon': parts[5],
                          'xres': parts[6], 'yres': parts[7],
                          'pole': parts[8]})
                if len(parts) > 9:
                    d.update({'extent': parts[9]})

                res_type = 1
                max_res = max(float(parts[6]), float(parts[7]))

            k = horizontal_resolution_keyword(res_type, max_res)
            if len(k) > 0:
                d.update({'hres_keyword': k})

            grids.append(d)

    return {'grids': grids, 'locations': locations}


def inserted_word_into_search_wordlist(conn, db_absolute_table, dsid, words,
                                       loc, uflg):
    try:
        cursor = conn.cursor()
        cursor.execute((
                "insert into " + db_absolute_table + " (word, sword, "
                "location, dsid, uflg) values (%s, %s, %s, %s, %s) on "
                "conflict (word, location, dsid) do update set sword = "
                "excluded.sword, uflg = excluded.uflg"),
                (words[0], strutils.soundex(words[1]), loc, dsid, uflg))
        conn.commit()
        cursor.execute((
                "select a, b from search.cross_reference where a = %(word)s "
                "union select b, a from search.cross_reference where b = "
                "%(word)s"), {'word': words[0]})
        res = cursor.fetchall()
        for e in res:
            t = strutils.cleaned_search_word(e[1])
            if not t[0]:
                cursor.execute((
                        "insert into " + db_absolute_table + " (word, sword, "
                        "location, dsid, uflg) values (%s, %s, %s, %s, %s) on "
                        "conflict (word, location, dsid) do update set sword "
                        "= excluded.sword, uflg = excluded.uflg"),
                        (t[1], strutils.soundex(t[2]), loc, dsid, uflg))
                conn.commit()

        parts = words[0].split("-")
        if len(parts) == 1:
            parts = words[0].split("/")

        if len(parts) == 1:
            parts = []
        else:
            for part in parts:
                if len(part) == 0:
                    parts = []
                    break

            cword = []
            for p in parts:
                if len(p) > 0:
                    cword.append(p)
                    t = strutils.cleaned_search_word(p)
                    if not t[0]:
                        cursor.execute((
                                "insert into " + db_absolute_table + " (word, "
                                "sword, location, dsid, uflg) values (%s, %s, "
                                "%s, %s, %s) on conflict (word, location, "
                                "dsid) do update set sword = excluded.sword, "
                                "uflg = excluded.uflg"),
                                (t[1], strutils.soundex(t[2]), loc, dsid,
                                 uflg))
                        conn.commit()
                        cursor.execute((
                                "select a, b from search.cross_reference "
                                "where a = %(word)s union select b, a from "
                                "search.cross_reference where b = %(word)s"),
                                {'word': t[1]})
                        res = cursor.fetchall()
                        for e in res:
                            t = strutils.cleaned_search_word(e[1])
                            if not t[0]:
                                cursor.execute((
                                        "insert into " + db_absolute_table +
                                        " (word, sword, location, dsid, uflg) "
                                        "values (%s, %s, %s, %s, %s) on "
                                        "conflict (word, location, dsid) do "
                                        "update set sword = excluded.sword, "
                                        "uflg = excluded.uflg"),
                                        (t[1], strutils.soundex(t[2]), loc,
                                         dsid, uflg))
                                conn.commit()

            if len(cword) > 1:
                cword = "".join(cword)
                t = strutils.cleaned_search_word(cword)
                if not t[0]:
                    cursor.execute((
                            "insert into " + db_absolute_table + " (word, "
                            "sword, location, dsid, uflg) values (%s, %s, %s, "
                            "%s, %s) on conflict (word, location, dsid) do "
                            "update set sword = excluded.sword, uflg = "
                            "excluded.uflg"),
                            (t[1], strutils.soundex(t[2]), loc, dsid, uflg))
                    conn.commit()

        cursor.execute((
                "delete from " + db_absolute_table + " where dsid = %s and "
                "uflg != %s"), (dsid, uflg))
        conn.commit()
    except Exception as err:
        return "{}; word: '{}'; table: {}".format(
                err, words[0], db_absolute_table)

    return ""


def time_resolution_keyword(d):
    if d['type'] == "climatology":
        if d['unit'] == "hour":
            return "T : Hourly Climatology"

        if d['unit'] == "day":
            if 'number' in d:
                if d['number'] == 5:
                    return "T : Pentad Climatology"

                if d['number'] == 7:
                    return "T : Weekly Climatology"

            return "T : Daily Climatology"

        if d['unit'] == "week":
            return "T : Weekly Climatology"

        if d['unit'] == "month":
            return "T : Monthly Climatology"

        if d['unit'] in ("season", "winter", "spring", "summer", "autumn"):
            return "T : Seasonal Climatology"

        if d['unit'] == "year":
            return "T : Annual Climatology"

        if d['unit'] == "30-year":
            return "T : Climate Normal (30-year climatology)"

    elif d['type'] == "regular":
        if d['unit'] == "second":
            return "T : 1 second - < 1 minute"

        if d['unit'] == "minute":
            return "T : 1 minute - < 1 hour"

        if d['unit'] == "hour":
            return "T : Hourly - < Daily"

        if d['unit'] == "day":
            return "T : Daily - < Weekly"

        if d['unit'] == "week":
            return "T : Weekly - < Monthly"

        if (d['unit'] in
                ("month", "season", "winter", "spring", "summer", "autumn")):
            return "T : Monthly - < Annual"

        if d['unit'] == "year":
            return "T : Annual"

        if d['unit'] == "decade":
            return "T : Decadal"

    elif d['type'] == "irregular":
        if d['unit'] == "second":
            return "T : < 1 second"

        if d['unit'] == "minute":
            return "T : 1 second - < 1 minute"

        if d['unit'] == "hour":
            return "T : 1 minute - < 1 hour"

        if d['unit'] == "day":
            return "T : Hourly - < Daily"

        if d['unit'] == "week":
            return "T : Daily - < Weekly"

        if d['unit'] == "month":
            return "T : Weekly - < Monthly"

        if d['unit'] in ("season", "winter", "spring", "summer", "autumn"):
            return "T : Monthly - < Annual"

        if d['unit'] == "year":
            return "T : Monthly - < Annual"

        if d['unit'] == "decade":
            return "T : Annual"

    return ""


def horizontal_resolution_keyword(res_type, max_res):
    if res_type == 0:
        if max_res < 0.00001:
            return "H : < 1 meter"

        if max_res < 0.0003:
            return "H : 1 meter - < 30 meters"

        if max_res < 0.001:
            return "H : 30 meters - < 100 meters"

        if max_res < 0.0025:
            return "H : 100 meters - < 250 meters"

        if max_res < 0.005:
            return "H : 250 meters - < 500 meters"

        if max_res < 0.01:
            return "H : 500 meters - < 1 km"

        if max_res < 0.09:
            return ("H : 1 km - < 10 km or approximately .01 degree - < .09 "
                    "degree")

        if max_res < 0.5:
            return ("H : 10 km - < 50 km or approximately .09 degree - < .5 "
                    "degree")

        if max_res < 1.:
            return ("H : 50 km - < 100 km or approximately .5 degree - < 1 "
                    "degree")

        if max_res < 2.5:
            return ("H : 100 km - < 250 km or approximately 1 degree - < 2.5 "
                    "degrees")

        if max_res < 5.:
            return ("H : 250 km - < 500 km or approximately 2.5 degrees - < "
                    "5.0 degrees")

        if max_res < 10.:
            return ("H : 500 km - < 1000 km or approximately 5 degrees - < 10 "
                    "degrees")

        return "H : >= 1000 km or >= 10 degrees"
    elif res_type == 1:
        if max_res < 0.001:
            return "H : < 1 meter"

        if max_res < 0.03:
            return "H : 1 meter - < 30 meters"

        if max_res < 0.1:
            return "H : 30 meters - < 100 meters"

        if max_res < 0.25:
            return "H : 100 meters - < 250 meters"

        if max_res < 0.5:
            return "H : 250 meters - < 500 meters"

        if max_res < 1.:
            return "H : 500 meters - < 1 km"

        if max_res < 10.:
            return ("H : 1 km - < 10 km or approximately .01 degree - < .09 "
                    "degree")

        if max_res < 50.:
            return ("H : 10 km - < 50 km or approximately .09 degree - < .5 "
                    "degree")

        if max_res < 100.:
            return ("H : 50 km - < 100 km or approximately .5 degree - < 1 "
                    "degree")

        if max_res < 250.:
            return ("H : 100 km - < 250 km or approximately 1 degree - < 2.5 "
                    "degrees")

        if max_res < 500.:
            return ("H : 250 km - < 500 km or approximately 2.5 degrees - < "
                    "5.0 degrees")

        if max_res < 1000.:
            return ("H : 500 km - < 1000 km or approximately 5 degrees - < 10 "
                    "degrees")

        return "H : >= 1000 km or >= 10 degrees"

    return ""
