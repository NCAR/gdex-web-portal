import os
import psycopg2
import pytz
import random
import requests
import smtplib
import subprocess

from datetime import date, datetime, timedelta
from dateutil import tz
from dateutil.relativedelta import relativedelta
from dsspellchecker import SpellChecker
from email.message import EmailMessage
from lxml import etree as ElementTree
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from . import config
from . import strutils
from . import utils
from .config import bin_utils, root_dirs
from .utils import check_html, log_error
from .xmlutils import convert_plain_ampersands


def add(request):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    iuser = utils.get_iuser(request)
    if len(iuser) == 0:
        return render(request, "500.html")

    # return any expired IDs to the pool
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute((
                "delete from search.datasets where type = 'R' and "
                "timestamp_utc < current_timestamp at time zone 'UTC'"))
        conn.commit()
    except psycopg2.Error as err:
        log_error(err, source="add")
        return render(request, "metaman/datasets/add.html",
                      {'database_error': "{}".format(err)})

    # check to see if an ID has already been reserved
    try:
        cursor.execute((
                "select dsid, timestamp_utc from search.datasets where type = "
                "'R' and title = '" + iuser + "'"))
        res = cursor.fetchone()
        if res is not None:
            next_id = res[0]
            expires = (res[1].replace(tzinfo=tz.tzutc())
                       .astimezone(tz.gettz("US/Mountain")))
            return render(request, "metaman/datasets/add.html",
                          {'next_id': next_id,
                           'expires': str(expires)[0:19],
                           'already_reserved': True})

    except psycopg2.Error as err:
        log_error(err, source="add")
        return render(request, "metaman/datasets/add.html",
                      {'database_error': "{}".format(err)})

    if 'id' not in request.POST:
        return render(request, "metaman/datasets/add.html")

    id = request.POST['id']
    if id == "pool":
        # pull the next available ID from the 'pool'
        try:
            random.seed()
            off = random.randrange(0, 100)
            cursor.execute((
                    "select next_id from generate_series((select min(cast("
                    "substring(dsid, 2) as integer)) from search.datasets), "
                    "(select max(cast(substring(dsid, 2) as integer)) from "
                    "search.datasets)) as next_id left join search.datasets "
                    "as d on cast(substring(dsid, 2) as integer) = next_id "
                    "where d.dsid is null limit 1 offset " + str(off)))
            res = cursor.fetchone()
            next_id = str(res[0])
            if len(next_id) < 6:
                next_id = ("0" * (6-len(next_id))) + next_id

            next_id = "d" + next_id
            expires = ((datetime.now(pytz.utc) + timedelta(hours=48))
                       .replace(tzinfo=tz.tzutc()))
            cursor.execute((
                    "insert into search.datasets (dsid, timestamp_utc, type, "
                    "curation_level, title, summary, continuing_update, "
                    "inet_access, pub_date, has_redundancy) values ('" +
                    next_id + "', '" + str(expires)[0:19] + "', 'R', '', '" +
                    iuser + "', '', 'N', 'N', '9999-01-01', 'N')"))
            conn.commit()
            conn.close()
            return render(request, "metaman/datasets/add.html",
                          {'next_id': next_id,
                           'expires': (str(expires.astimezone(tz
                                       .gettz("US/Mountain")))[0:19])})
        except psycopg2.Error as err:
            log_error(err, source="add")
            return render(request, "metaman/datasets/add.html",
                          {'database_error': "{}".format(err)})

    else:
        # a specific ID was submitted, so check if it is good and available
        if len(id) != 7 or id[0] != 'd' or id < 'd010000' or id > 'd998999':
            return render(request, "metaman/datasets/add.html", {'bad_id': id})

        try:
            ctx = {}
            expires = ((datetime.now(pytz.utc) + timedelta(hours=48))
                       .replace(tzinfo=tz.tzutc())
                       .astimezone(tz.gettz("US/Mountain")))
            cursor.execute("select dsid from search.datasets where dsid = %s",
                           (id, ))
            res = cursor.fetchone()
            if res is None:
                ctx.update({'got_requested': True})
            else:
                try:
                    ctx.update({'requested_id': id})
                    cursor.execute((
                            "select next_id from generate_series(" + id[1:] +
                            ", 998999) as next_id left join search.datasets "
                            "as d on cast(substring(dsid, 2) as integer) = "
                            "next_id where d.dsid is null limit 1 offset 0"))
                    res = cursor.fetchone()
                    id = str(res[0])
                    if len(id) < 6:
                        id = ("0" * (6-len(id))) + id

                    id = "d" + id

                except psycopg2.Error as err:
                    log_error(err, source="add")
                    return render(request, "metaman/datasets/add.html",
                                  {'database_error': "{}".format(err)})

            try:
                cursor.execute((
                        "insert into search.datasets (dsid, timestamp_utc, "
                        "type, curation_level, title, summary, "
                        "continuing_update, inet_access, pub_date, "
                        "has_redundancy) values (%s, %s, %s, %s, %s, %s, "
                        "%s, %s, %s, %s)"),
                        (id, str(expires)[0:19], "R", "", iuser, "", "N",
                         "N", "9999-01-01", "N"))
                conn.commit()
                ctx.update({'next_id': id, 'expires': str(expires)[0:19]})

            except psycopg2.Error as err:
                log_error(err, source="add")
                return render(request, "metaman/datasets/add.html",
                              {'database_error': "{}".format(err)})

            cursor.close()
            conn.close()
            return render(request, "metaman/datasets/add.html", ctx)

        except psycopg2.Error as err:
            log_error(err, source="add")
            return render(request, "metaman/datasets/add.html",
                          {'database_error': "{}".format(err)})


def cancel(request, dsid):
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute((
                "delete from search.datasets where type = 'R' and dsid = "
                "%s"), (dsid, ))
        conn.commit()
        cursor.close()
        conn.close()
        return render(request, "metaman/datasets/cancel.html", {'dsid': dsid})
    except psycopg2.Error as err:
        log_error(err, source="cancel")
        return render(request, "metaman/datasets/cancel.html",
                      {'database_error': "{}".format(err)})


def commit_changes(request, dsid):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    ctx = {'dsid': dsid}
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute((
                "select lockname, ds_type, ds_curation, update_frequency, "
                "logo, title, summary, contributors, authors, "
                "access_restrictions, usage_restrictions, variables, "
                "contacts, platforms, instruments, projects, "
                "supports_projects, iso_topic, _references, reflists, "
                "acknowledgement, related_resources, related_dois, "
                "related_datasets, publication_date, redundancys, license, "
                "content_metadata, updated_datacite_field from metautil."
                "metaman where dsid = %s"), (dsid, ))
        res = cursor.fetchone()
        if res is None:
            ctx.update({'error': "Missing entry for this dataset"})
            return render(request, "metaman/datasets/commit_msg.html", ctx)

        iuser = utils.get_iuser(request)
        if res[0] != iuser:
            ctx.update({'error': ("This dataset is locked by '{}'")
                       .format(res[0])})
            return render(request, "metaman/datasets/commit_msg.html", ctx)

    except psycopg2.Error as err:
        ctx.update({'error': "A database error occurred: '{}'".format(err)})
        return render(request, "metaman/datasets/commit_msg.html", ctx)

    updated_datacite_field = res[28]
    ctx.update({'ds_type': res[1], 'curation_level': res[2]})
    now = (str(datetime.now().replace(tzinfo=tz.tzutc())
           .astimezone(tz.gettz("US/Mountain"))))
    now = now[0:19] + " " + now[-6:].replace(":", "")
    ctx.update({'timestamp': now})
    parts = res[3].split("<!>")
    ctx.update({'continuing_update': {'value': parts[0]}})
    if ctx['continuing_update']['value'] == "yes":
        ctx['continuing_update'].update({'frequency': parts[1]})

    if len(res[4]) > 0:
        ctx.update({'logo': res[4]})

    cursor.execute("select dsid from search.datasets where title = %s",
                   (res[5], ))
    dres = cursor.fetchall()
    for x in dres:
        if x[0] != dsid:
            ctx.update({'error': ("The title is already in use by '{}'")
                       .format(x[0])})
            return render(request, "metaman/datasets/commit_msg.html", ctx)

    ctx.update({'title': res[5], 'summary': convert_plain_ampersands(res[6]),
                'contributors': utils.extract_contributors(res[7]),
                'authors': utils.extract_authors(res[8])})
    if len(res[9]) > 0:
        ctx.update({'access_restrictions': convert_plain_ampersands(res[9])})

    if len(res[10]) > 0:
        ctx.update({'usage_restrictions': convert_plain_ampersands(res[10])})

    vars = []
    parts = res[11].split("\n")
    for p in parts:
        vparts = p.split("[!]")
        vars.append({'path': vparts[0], 'uuid': vparts[1]})

    ctx.update({
        'variables': vars,
        'contacts': [x for x in res[12].split("\n") if len(x) > 0],
        'platforms': ([x.split("[!]")[1] for x in res[13].split("\n") if
                      len(res[13]) > 0]),
        'instruments': ([x.split("[!]")[1] for x in res[14].split("\n") if
                        len(res[14]) > 0]),
        'projects': ([x.split("[!]")[1] for x in res[15].split("\n") if
                     len(res[15]) > 0]),
        'supports_projects': ([x.split("[!]")[1] for x in
                              res[16].split("\n") if len(res[16]) > 0]),
        'iso_topic': res[17],
    })
    refs = utils.extract_references(res[18])
    ctx.update({'references': refs[0]})
    if len(res[19]) > 0:
        parts = res[19].split("\n")
        ref_urls = []
        for p in parts:
            rparts = p.split("[!]")
            ref_urls.append({'url': rparts[0], 'description': rparts[1]})

        ctx.update({'reference_urls': ref_urls})

    if len(res[20]) > 0:
        ctx.update({'acknowledgement': convert_plain_ampersands(res[20])})

    if len(res[21]) > 0:
        parts = res[21].split("\n")
        rel_resources = []
        for p in parts:
            rparts = p.split("[!]")
            rel_resources.append({'url': rparts[0].replace("&", "&amp;"),
                                  'description': rparts[1]})

        ctx.update({'related_resources': rel_resources})

    if len(res[22]) > 0:
        parts = res[22].split("\n")
        rel_dois = []
        for p in parts:
            dparts = p.split("[!]")
            rel_dois.append({'doi': dparts[0], 'type': dparts[1]})

        ctx.update({'related_dois': rel_dois})

    if len(res[23]) > 0:
        ctx.update({'related_datasets': [x for x in res[23].split("\n")]})

    pub_date = str(res[24])
    if ((pub_date.find("9999") == 0 or pub_date.find("0001") == 0) and
            ctx['ds_type'] in ("primary", "historical")):
        pub_date = now[0:10]

    ctx.update({'pub_date': pub_date, 'redundancies': []})
    parts = res[25].split("\n")
    if parts[0] == "yes":
        parts.pop(0)
        for p in parts:
            rparts = p.split("[!]")
            d = {}
            if len(rparts[0]) > 0:
                d.update({'url': rparts[0]})

            if len(rparts[1]) > 0:
                d.update({'name': rparts[1]})

            if len(rparts[2]) > 0:
                d.update({'address': rparts[2]})

            ctx['redundancies'].append(d)

    ctx.update({'data_license': res[26]})
    if res[27] == "Y":
        ctx.update({'content_metadata': {}})
        try:
            cursor.execute((
                    "select periods, temporal_frequencys, data_types, "
                    "formats, ascii_url, binary_url, varlist, levels, "
                    "coverages from metautil.cmd where dsid = %s"),
                    (dsid, ))
            res = cursor.fetchone()
            if res is None:
                ctx.update({'error': ("Missing content metadata entry for "
                                      "this dataset")})
                return render(request, "metaman/datasets/commit_msg.html",
                              ctx)

        except psycopg2.Error as err:
            ctx.update({'error': ("Database error while getting content "
                                  "metadata: '{}'").format(err)})
            return render(request, "metaman/datasets/commit_msg.html", ctx)

        time_ranges = utils.extract_time_ranges(dsid, res[0])
        if type(time_ranges) is str:
            ctx.update({'error': time_ranges})
            return render(request, "metaman/datasets/commit_msg.html", ctx)

        tf = utils.extract_temporal_frequencies(res[1])
        coverages = utils.extract_coverages(res[8])
        ctx['content_metadata'].update({
            'time_ranges': time_ranges,
            'temporal_frequencies': tf[0],
            'data_types': utils.extract_data_types(res[2]),
            'data_formats': utils.extract_data_formats(res[3], res[4], res[5]),
            'detailed_variables': utils.extract_detailed_variables(res[6]),
            'levels': utils.extract_levels(res[7]),
            'coverages': coverages,
        })

    xml = render_to_string("metaman/datasets/dataset.xml", ctx)
    xml = "\n".join([line for line in xml.splitlines() if line])
    with open(root_dirs['tmp'] + "/" + dsid + ".xml", "w") as f:
        try:
            f.write(xml)
        except UnicodeEncodeError:
            chars = [c for c in xml]
            min_x = len(xml)
            max_x = -1
            for x in range(0, len(chars)):
                o = ord(chars[x])
                if o < 10 or o > 127:
                    if o == 160:
                        chars[x] = " "
                    else:
                        chars[x] = "&diams;"
                        min_x = min(min_x, x)
                        max_x = max(max_x, x)

            if max_x >= 0:
                min_x -= 20
                if min_x < 0:
                    min_x = 0

                max_x += 20
                if max_x > len(chars):
                    max_x = len(chars)

                ctx.update({'error': ("Unable to write XML file: non-ASCII "
                                      "characters (denoted by diamonds) in "
                                      "<i>{}</i>")
                           .format("".join(chars[min_x:max_x]))})
                return render(request, "metaman/datasets/commit_msg.html",
                              ctx)
            else:
                f.write("".join(chars))

        except Exception as err:
            ctx.update({'error': ("Unable to write XML file: '{}'\n")
                       .format(err)})
            return render(request, "metaman/datasets/commit_msg.html", ctx)

    f.close()
    try:
        schema_doc = ElementTree.parse(
                root_dirs['web'] + "/metadata/schemas/dsOverview3.xsd")
        xml_schema = ElementTree.XMLSchema(schema_doc)
        xml_schema.assertValid(
                ElementTree.parse(root_dirs['tmp'] + "/" + dsid + ".xml"))
        ctx.update({'overview_validated': True})
    except Exception as err:
        ctx.update({'error': ("Your changes did not pass the XML validator: "
                              "'{}'\n").format(err)})
        return render(request, "metaman/datasets/commit_msg.html", ctx)

    # create a temporary directory
    tdir_name = utils.make_tempdir()
    if len(tdir_name) == 0:
        ctx.update({'error': ("Unable to make a temporary directory for the "
                              "CVS commit")})
        return render(request, "metaman/datasets/commit_msg.html", ctx)

    err = commit_dsoverview(
            tdir_name, dsid, iuser, request.POST['cvscomment'])
    if len(err) > 0:
        ctx.update({'error': err})
        utils.remove_tempdir(tdir_name)
        return render(request, "metaman/datasets/commit_msg.html", ctx)

    ctx.update({'overview_committed': True})
    cursor.execute(("delete from metautil.metaman where dsid = %s"),
                   (ctx['dsid'], ))
    cursor.execute(("delete from metautil.cmd where dsid = %s"),
                   (ctx['dsid'], ))
    conn.commit()
    if ctx['ds_type'] in ("primary", "historical"):
        if (not os.path.exists(os.path.join(
                root_dirs['web'], "datasets", dsid))):
            subprocess.run((
                    "mkdir -p " + os.path.join(
                            tdir_name, "datasets", dsid, "metadata")),
                           shell=True)
            err = utils.rdadata_rsync(
                    tdir_name, os.path.join("datasets", dsid, "metadata"),
                    root_dirs['web'])
            if len(err) > 0:
                ctx.update({'error': ("Unable to create web directory: '{}'")
                           .format(err)})
                utils.remove_tempdir(tdir_name)
                return render(request, "metaman/datasets/commit_msg.html",
                              ctx)

        os.chmod(os.path.join(tdir_name, dsid + ".xml"), 0o644)
        err = utils.rdadata_rsync(
                tdir_name, dsid + ".xml", os.path.join(
                        root_dirs['web'], "datasets", dsid, "metadata",
                        "dsOverview.xml"))
        if len(err) > 0:
            ctx.update({'error': "XML copy failed: '{}'".format(err)})
            utils.remove_tempdir(tdir_name)
            return render(request, "metaman/datasets/commit_msg.html", ctx)

    utils.remove_tempdir(tdir_name)
    if 'content_metadata' in ctx:
        err = update_metadata_database(ctx, conn, ref_words=refs[1],
                                       tres_keywords=tf[1])
    else:
        err = update_metadata_database(ctx, conn, ref_words=refs[1])

    if len(err) > 0:
        ctx.update({'error': ("Error while updating the search/discovery "
                              "metadata: '{}'").format(err)})
        return render(request, "metaman/datasets/commit_msg.html", ctx)

    ctx.update({'metadata_updated': True})
    env = os.environ.copy()
    env['USER'] = "apache"
    env['QUERY_STRING'] = "X"
    if ctx['ds_type'] in ("primary", "historical"):
        o = subprocess.run((
                bin_utils['rdadatarun'] + " /usr/local/decs/bin/dsgen " +
                ctx['dsid']),
                shell=True, env=env, stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE)
        o = o.stderr.decode("utf-8")
        if len(o) > 0:
            ctx.update({'error': ("Unable to refresh the dataset "
                                  "description page: '{}'").format(o)})
            return render(request, "metaman/datasets/commit_msg.html", ctx)

    ctx.update({'dsgen_success': True})
    if updated_datacite_field == "Y":
        try:
            cursor.execute((
                    "select doi from dssdb.dsvrsn where dsid = %s and "
                    "status = 'A'"), (ctx['dsid'], ))
            res = cursor.fetchone()
            if res is not None:
                o = subprocess.run((
                        bin_utils['rdadatarun'] + " /usr/local/decs/bin/doi "
                        "q46IE9AqHo update " + res[0]),
                        shell=True, env=env, stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE)
                o = o.stderr.decode("utf-8")
                if len(o) > 0:
                    ctx.update({'error': ("Unable to update the DataCite "
                                          "metadata: '{}'").format(o)})
                    return render(request,
                                  "metaman/datasets/commit_msg.html", ctx)

                ctx.update({'datacite_updated': True})

        except Exception as e:
            ctx.update({'error': ("Unable to check for datacite updates: "
                                  "'{}'").format(e)})
            return render(request, "metaman/datasets/commit_msg.html", ctx)

    cursor.close()
    conn.close()
    return render(request, "metaman/datasets/commit_msg.html", ctx)


def commit_dsoverview(tdir_name, dsid, iuser, cvscomment):
    xml_file = dsid + ".xml"
    env = {'TMPDIR': "/data/ptmp"}
    subprocess.run((
            bin_utils['cvs'] + " -Q -d " + root_dirs['cvs'] + " checkout "
            "-d " + tdir_name + " " + os.path.join("datasets", xml_file)),
            shell=True, env=env)
    subprocess.run((
            "/bin/mv " + os.path.join(root_dirs['tmp'], xml_file) + " " +
            os.path.join(tdir_name, xml_file)),
            shell=True)
    web_path = os.path.join(root_dirs['web'], "datasets", dsid, "metadata")
    if not os.path.exists(web_path):
        subprocess.run("/bin/mkdir -p " + web_path, shell=True)

    subprocess.run((
            bin_utils['cvs'] + " -d " + root_dirs['cvs'] + " edit " +
            os.path.join(tdir_name, xml_file)),
            shell=True, env=env)
    o = subprocess.run((
            bin_utils['cvs'] + " -d " + root_dirs['cvs'] + " commit -m \"" +
            iuser + ": " + cvscomment.replace("\"", "'") + "\" " +
            os.path.join(tdir_name, xml_file)),
            shell=True, env=env, stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE)
    o = o.stderr.decode("utf-8")
    if len(o) > 0:
        return "Your changes could not be saved by cvs: '{}'".format(o)

    return ""


def update_metadata_database(ctx, conn, **kwargs):
    err = ""
    uflg = strutils.strand(3)

    # index the dataset title
    if len(err) == 0:
        words = ctx['title'].split()
        loc = 0
        for word in words:
            t = strutils.cleaned_search_word(word)
            if not t[0]:
                err = utils.inserted_word_into_search_wordlist(
                        conn, "search.title_wordlist", ctx['dsid'], t[1:],
                        loc, uflg)
                if len(err) > 0:
                    break

                loc += 1

    # index the dataset summary
    if len(err) == 0:
        words = ctx['summary'].split()
        loc = 0
        for word in words:
            t = strutils.cleaned_search_word(word)
            if not t[0]:
                err = utils.inserted_word_into_search_wordlist(
                        conn, "search.summary_wordlist", ctx['dsid'], t[1:],
                        loc, uflg)
                if len(err) > 0:
                    break

                loc += 1

    type = ctx['ds_type'][0:1].upper()
    timestamp = (datetime.now(pytz.utc).replace(tzinfo=tz.tzutc())
                 .strftime("%Y-%m-%d %H:%M:%S"))
    update_flag = ctx['continuing_update']['value'][0:1].upper()
    has_redundancy = "Y" if len(ctx['redundancies']) > 0 else "N"
    try:
        cursor = conn.cursor()
        cursor.execute((
                "insert into search.datasets (dsid, timestamp_utc, type, "
                "curation_level, title, summary, continuing_update, "
                "pub_date, has_redundancy) values (%s, %s, %s, %s, %s, %s, "
                "%s, %s, %s) on conflict on constraint datasets_pkey do "
                "update set timestamp_utc = excluded.timestamp_utc, type = "
                "excluded.type, curation_level = excluded.curation_level, "
                "title = excluded.title, summary = excluded.summary, "
                "continuing_update = excluded.continuing_update, pub_date = "
                "excluded.pub_date, has_redundancy = excluded."
                "has_redundancy"),
                (ctx['dsid'], timestamp, type, ctx['curation_level'],
                 ctx['title'], ctx['summary'], update_flag, ctx['pub_date'],
                 has_redundancy))
        conn.commit()
        backflag = "B" if has_redundancy == "N" else "N"
        cursor.execute((
                "update dssdb.dataset set title = %s, backflag = %s, "
                "version = version+1 where dsid = %s"),
                (ctx['title'], backflag, ctx['dsid']))
        conn.commit()
        cursor.execute("delete from search.dataset_authors where dsid = %s",
                       (ctx['dsid'], ))
        conn.commit()
        for x in range(0, len(ctx['authors'])):
            author = ctx['authors'][x]
            if 'corporation' in author:
                cursor.execute((
                        "insert into search.dataset_authors (dsid, type, "
                        "given_name, sequence) values (%s, %s, %s, %s)"),
                        (ctx['dsid'], "Organization", author['corporation'],
                         x))
            else:
                orcid_id = author['orcid_id'] if 'orcid_id' in author else None
                cursor.execute((
                        "insert into search.dataset_authors (dsid, type, "
                        "given_name, middle_name, family_name, orcid_id, "
                        "sequence) values (%s, %s, %s, %s, %s, %s, %s) on "
                        "conflict on constraint dataset_authors_pkey do "
                        "nothing"),
                        (ctx['dsid'], "Person", author['fname'],
                         author['mname'], author['lname'], orcid_id, x))

        conn.commit()
    except Exception as e:
        err = str(e)

    if len(err) == 0 and type != "I":
        try:
            cursor.execute((
                    "delete from search.variables where dsid = %s and "
                    "vocabulary = 'GCMD'"), (ctx['dsid'], ))
            conn.commit()
        except Exception as e:
            err = str(e)

        if len(err) == 0:
            try:
                cursor.execute((
                        "delete from search.gcmd_variables where dsid = %s"),
                        (ctx['dsid'], ))
                conn.commit()
            except Exception as e:
                err = str(e)

        if len(err) == 0:
            topic_map = {}
            for var in ctx['variables']:
                try:
                    cursor.execute((
                            "insert into search.variables (keyword, "
                            "vocabulary, dsid) values (%s, 'GCMD', %s)"),
                            (var['uuid'], ctx['dsid']))
                    conn.commit()
                    parts = var['path'].split(" > ")
                    if len(parts) < 4 or parts[0][0:13] != "EARTH SCIENCE":
                        err = ("malformed GCMD science keyword error for '" +
                               var['path'] + "'")
                        break

                    topic = strutils.to_title(parts[1])
                    term = strutils.to_title(parts[2])
                    variable = strutils.to_title(parts[-1])
                    cursor.execute((
                            "insert into search.gcmd_variables (keyword, "
                            "dsid, topic, term) values (%s, %s, %s, %s)"),
                            (variable, ctx['dsid'], topic, term))
                    conn.commit()
                    if topic not in topic_map:
                        topic_map.update({topic: 1})
                    else:
                        topic_map[topic] += 1

                except Exception as e:
                    err = str(e)
                    break

        if len(err) == 0:
            try:
                cursor.execute((
                        "select date_create from dssdb.dataset where dsid = "
                        "%s"), (ctx['dsid'], ))
                res = cursor.fetchone()
                age = (date(2030, 12, 31) - res[0]).days
                num_vars = len(ctx['variables'])
                cursor.execute((
                        "delete from search.gcmd_topics where dsid = %s"),
                        (ctx['dsid'], ))
                conn.commit()
                for topic in topic_map:
                    rank = (((num_vars * 1000) / topic_map[topic]) * 100000 +
                            age)
                    cursor.execute((
                            "insert into search.gcmd_topics (keyword, dsid, "
                            "rank) values (%s, %s, %s)"),
                            (topic, ctx['dsid'], int(rank)))
                    conn.commit()

            except Exception as e:
                err = str(e)

    if len(err) == 0:
        try:
            cursor.execute(("delete from dssdb.dsowner where dsid = %s"),
                           (ctx['dsid'], ))
            conn.commit()
            for x in range(0, len(ctx['contacts'])):
                cparts = ctx['contacts'][x].split()
                cursor.execute((
                        "select logname from dssdb.dssgrp where fstname = "
                        "%s and lstname = %s"), (cparts[0], cparts[1]))
                res = cursor.fetchone()
                cursor.execute((
                        "insert into dssdb.dsowner (dsid, specialist, "
                        "priority) values (%s, %s, %s)"),
                        (ctx['dsid'], res[0], x+1))
                conn.commit()

        except Exception as e:
            err = str(e)

    if len(err) == 0:
        try:
            cursor.execute((
                    "delete from search.contributors_new where dsid = %s "
                    "and vocabulary = 'GCMD'"), (ctx['dsid'], ))
            conn.commit()
            for x in range(0, len(ctx['contributors'])):
                c = ctx['contributors'][x]
                fn = c['former_name'] if 'former_name' in c else ""
                cx = c['contact'] if 'contact' in c else ""
                cursor.execute((
                        "insert into search.contributors_new (keyword, "
                        "vocabulary, dsid, citable, disp_order, "
                        "former_name, contact) values (%s, 'GCMD', %s, %s, "
                        "%s, %s, %s)"),
                        (c['uuid'], ctx['dsid'], c['citable'][0:1].upper(),
                         x, fn, cx))
                conn.commit()

        except Exception as e:
            err = str(e)

    if len(err) == 0:
        try:
            cursor.execute((
                    "delete from search.platforms_new where dsid = %s and "
                    "vocabulary = 'GCMD'"), (ctx['dsid'], ))
            conn.commit()
            for pf in ctx['platforms']:
                cursor.execute((
                        "insert into search.platforms_new (keyword, "
                        "vocabulary, dsid) values (%s, 'GCMD', %s)"),
                        (pf, ctx['dsid']))
                conn.commit()

        except Exception as e:
            err = str(e)

    if len(err) == 0:
        try:
            cursor.execute((
                   "delete from search.instruments where dsid = %s and "
                   "vocabulary = 'GCMD'"), (ctx['dsid'], ))
            conn.commit()
            for i in ctx['instruments']:
                cursor.execute((
                        "insert into search.instruments (keyword, "
                        "vocabulary, dsid) values (%s, 'GCMD', %s)"),
                        (i, ctx['dsid']))
                conn.commit()

        except Exception as e:
            err = str(e)

    if len(err) == 0:
        try:
            cursor.execute((
                    "delete from search.projects_new where dsid = %s and "
                    "vocabulary = 'GCMD'"), (ctx['dsid'], ))
            conn.commit()
            for p in ctx['projects']:
                cursor.execute((
                        "insert into search.projects_new (keyword, "
                        "vocabulary, dsid) values (%s, 'GCMD', %s)"),
                        (p, ctx['dsid']))
                conn.commit()

        except Exception as e:
            err = str(e)

    if len(err) == 0:
        try:
            cursor.execute((
                    "delete from search.supported_projects where dsid = %s "
                    "and vocabulary = 'GCMD'"), (ctx['dsid'], ))
            conn.commit()
            for p in ctx['supports_projects']:
                cursor.execute((
                        "insert into search.supported_projects (keyword, "
                        "vocabulary, dsid, origin) values (%s, 'GCMD', %s, "
                        "'dssmm')"), (p, ctx['dsid']))
                conn.commit()

        except Exception as e:
            err = str(e)

    if len(err) == 0:
        try:
            cursor.execute((
                    "delete from search.topics where dsid = %s and "
                    "vocabulary = 'ISO'"), (ctx['dsid'], ))
            conn.commit()
            cursor.execute((
                    "insert into search.topics (keyword, vocabulary, dsid) "
                    "values (%s, 'ISO', %s)"),
                    (ctx['iso_topic'], ctx['dsid']))
            conn.commit()
        except Exception as e:
            err = str(e)

    if (len(err) == 0 and 'ref_words' in kwargs and len(kwargs['ref_words'])
            > 0):
        try:
            loc = 0
            for e in kwargs['ref_words']:
                words = e.split()
                for word in words:
                    t = strutils.cleaned_search_word(word)
                    if not t[0]:
                        err = utils.inserted_word_into_search_wordlist(
                                conn, "search.references_wordlist",
                                ctx['dsid'], t[1:], loc, uflg)
                        if len(err) > 0:
                            break

                        loc += 1

        except Exception as e:
            err = str(e)

    if len(err) == 0:
        for r in ctx['redundancies']:
            name = r['name'] if 'name' in r else ""
            address = r['address'] if 'address' in r else ""
            url = r['url'] if 'url' in r else ""
            try:
                cursor.execute((
                        "insert into search.dataset_redundancy (dsid, name, "
                        "physical_address, web_address, uflag) values (%s, "
                        "%s, %s, %s, %s) on conflict on constraint "
                        "dataset_redundancy_pkey do update set uflag = "
                        "excluded.uflag"),
                        (ctx['dsid'], name, address, url, uflg))
                conn.commit()
            except Exception as e:
                err = str(e)
                break

        try:
            cursor.execute((
                    "delete from search.dataset_redundancy where dsid = %s "
                    "and uflag != %s"), (ctx['dsid'], uflg))
            conn.commit()
        except Exception as e:
            err = str(e)

    if len(err) == 0 and 'content_metadata' in ctx:
        try:
            cursor.execute("delete from dssdb.dsperiod where dsid = %s",
                           (ctx['dsid'], ))
            conn.commit()
            cursor.execute((
                    "select grpid, gindex from dssdb.dsgroup where dsid = "
                    "%s"), (ctx['dsid'], ))
            res = cursor.fetchall()
            grps = {e[0]: e[1] for e in res}
            for x in range(0, len(ctx['content_metadata']['time_ranges'])):
                tr = ctx['content_metadata']['time_ranges'][x]
                tzone = "+0000"
                sparts = tr['start'].split()
                sflg = sparts[0].count("-") + 1
                sdate = sparts[0]
                while sdate.count("-") < 2:
                    sdate += "-01"

                if len(sparts) > 1 and len(sparts[1]) > 0:
                    sflg += sparts[1].count(":") + 1
                    stime = sparts[1]
                    while stime.count(":") < 2:
                        stime += ":00"

                else:
                    stime = "00:00:00"

                if len(sparts) > 2:
                    tzone = sparts[2]

                eparts = tr['end'].split()
                eflg = eparts[0].count("-") + 1
                edate = eparts[0]
                while edate.count("-") < 2:
                    edate += "-01"

                if len(eparts) > 1 and len(eparts[1]) > 0:
                    eflg += eparts[1].count(":") + 1
                    etime = eparts[1]
                    while etime.count(":") < 2:
                        etime += ":00"

                else:
                    etime = "00:00:00"

                if tr['group_id'] != "Entire Dataset":
                    gindex = grps[tr['group_id']]
                else:
                    gindex = 0

                if 'type' in tr:
                    tzone = tr['type']

                cursor.execute((
                        "insert into dssdb.dsperiod (dsid, gindex, dorder, "
                        "date_start, time_start, start_flag, date_end, "
                        "time_end, end_flag, time_zone) values (%s, %s, %s, "
                        "%s, %s, %s, %s, %s, %s, %s)"),
                        (ctx['dsid'], gindex, x+1, sdate, stime, sflg,
                         edate, etime, eflg, tzone))
                conn.commit()

            cursor.execute((
                    "delete from search.time_resolutions where dsid = %s "
                    "and vocabulary = 'GCMD'"), (ctx['dsid'], ))
            conn.commit()
            if 'tres_keywords' in kwargs:
                for k in kwargs['tres_keywords']:
                    cursor.execute((
                            "insert into search.time_resolutions (keyword, "
                            "vocabulary, dsid, origin) values (%s, 'GCMD', "
                            "%s, 'dssmm')"), (k, ctx['dsid']))
                    conn.commit()

            cursor.execute((
                    "delete from search.data_types where dsid = %s and "
                    "vocabulary = 'dssmm'"), (ctx['dsid'], ))
            conn.commit()
            for dt in ctx['content_metadata']['data_types']:
                process = dt['process'] if 'process' in dt else ""
                cursor.execute((
                        "insert into search.data_types (keyword, process, "
                        "vocabulary, dsid) values (%s, %s, 'dssmm', %s)"),
                        (dt['description'], process, ctx['dsid']))
                conn.commit()

            cursor.execute((
                    "delete from search.formats where dsid = %s and "
                    "vocabulary = 'dssmm'"), (ctx['dsid'], ))
            conn.commit()
            for df in ctx['content_metadata']['data_formats']:
                cursor.execute((
                        "insert into search.formats (keyword, vocabulary, "
                        "dsid) values (%s, 'dssmm', %s)"),
                        (df['description'], ctx['dsid']))
                conn.commit()

            cursor.execute((
                    "delete from search.variables where dsid = %s and "
                    "vocabulary = 'CMDMM'"), (ctx['dsid'], ))
            conn.commit()
            for var in ctx['content_metadata']['detailed_variables']:
                cursor.execute((
                        "insert into search.variables (keyword, vocabulary, "
                        "dsid) values (%s, 'CMDMM', %s)"),
                        (var['description'], ctx['dsid']))
                conn.commit()

            cursor.execute((
                    "delete from search.grid_resolutions where dsid = %s "
                    "and vocabulary = 'GCMD'"), (ctx['dsid'], ))
            conn.commit()
            for grid in ctx['content_metadata']['coverages']['grids']:
                if 'hres_keyword' in grid:
                    cursor.execute((
                            "insert into search.grid_resolutions (keyword, "
                            "vocabulary, dsid, origin) values (%s, 'GCMD', "
                            "%s, 'dssmm')"),
                            (grid['hres_keyword'], ctx['dsid']))
                    conn.commit()

            cursor.execute((
                    "delete from search.locations_new where dsid = %s and "
                    "vocabulary = 'GCMD'"), (ctx['dsid'], ))
            conn.commit()
            for location in ctx['content_metadata']['coverages']['locations']:
                cursor.execute((
                        "insert into search.locations_new (keyword, "
                        "vocabulary, dsid) values (%s, 'GCMD', %s)"),
                        (location, ctx['dsid']))
                conn.commit()

        except Exception as e:
            err = str(e)

    return err


def commit_field(request, fieldname):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    ctx = {'fieldname': fieldname}
    if fieldname not in commit_fields:
        ctx.update({
                'error_type': "commit",
                'error': ("Unknown field '" + fieldname + "' - unable to "
                          "save this field's changes")})
        return render(request, "metaman/datasets/commit_msg.html", ctx)

    if 'fv' not in request.POST:
        ctx.update({'error_type': "commit", 'error': "Missing field value"})
        return render(request, "metaman/datasets/commit_msg.html", ctx)

    if (commit_fields[fieldname]['is_required'] and len(request.POST['fv'])
            == 0):
        ctx.update({'error_type': "commit",
                    'error': "This is a required field and cannot be empty"})
        return render(request, "metaman/datasets/commit_msg.html", ctx)

    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
    except psycopg2.Error as err:
        ctx.update({'error_type': "database",
                    'error': "database error '{}'".format(err)})
        return render(request, "metaman/datasets/commit_msg.html", ctx)

    if ('checker' in commit_fields[fieldname] and
            callable(commit_fields[fieldname]['checker'])):
        checker = commit_fields[fieldname]['checker']
        if checker.__name__ == "check_html" and len(request.POST['fv']) > 0:
            errs = check_html((
                    "<" + fieldname + ">" + request.POST['fv'] + "</" +
                    fieldname + ">"), SpellChecker())
            if len(errs) > 0:
                ctx.update({'error_type': "commit",
                            'error': "<br>".join(errs)})

        elif (checker.__name__ == "check_related_datasets" and
              len(request.POST['fv']) > 0):
            errs = check_related_datasets(
                    request.POST['fv'].split("\n"), cursor)
            if len(errs) > 0:
                ctx.update({
                        'error_type': "commit",
                        'error': ("References to non-primary and non-"
                                  "historical datasets must be removed:<br>"
                                  + "<br>").join(errs)})

        elif (checker.__name__ in {
                "check_references", "check_related_dois",
                "check_related_sites", "check_varlist"} and
              len(request.POST['fv']) > 0):
            errs = checker(request.POST['fv'].split("\n"))
            if len(errs) > 0:
                ctx.update({'error_type': "commit",
                            'error': "<br>".join(errs)})

        elif checker.__name__ == "check_title" and len(request.POST['fv']) > 0:
            errs = checker(request.POST['fv'], SpellChecker())
            if len(errs) > 0:
                ctx.update({'error_type': "commit", 'error': errs})

        elif checker.__name__ == "check_contributors":
            check_contributors(request.POST['dsid'], cursor)

    try:
        cursor.execute((
                "update metautil." + commit_fields[fieldname]['db_table'] +
                " set " + commit_fields[fieldname]['db_column'] + " = %s "
                "where dsid = %s"), (request.POST['fv'],
                                     request.POST['dsid']))
        conn.commit()
        cursor.execute((
                "update metautil.metaman set updated_any_field = 'Y', "
                "updated_datacite_field = %s where dsid = %s"),
                ("Y" if commit_fields[fieldname]['is_datacite'] else "N",
                 request.POST['dsid']))
        conn.commit()
        if fieldname == "formats":
            if 'ascii_url' in request.POST:
                cursor.execute((
                        "update metautil." +
                        commit_fields[fieldname]['db_table'] + " set "
                        "ascii_url = %s where dsid = %s"),
                        (request.POST['ascii_url'], request.POST['dsid']))
                conn.commit()
            elif 'binary_url' in request.POST:
                cursor.execute((
                        "update metautil." +
                        commit_fields[fieldname]['db_table'] + " set "
                        "binary_url = %s where dsid = %s"),
                        (request.POST['binary_url'], request.POST['dsid']))
                conn.commit()

    except psycopg2.Error as err:
        ctx.update({'error_type': "database",
                    'error': "database error '{}'".format(err)})
        return render(request, "metaman/datasets/commit_msg.html", ctx)

    cursor.close()
    conn.close()
    return render(request, "metaman/datasets/commit_msg.html", ctx)


def create(request, dsid):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    iuser = utils.get_iuser(request)
    if len(iuser) == 0:
        return render(request, "500.html")

    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute("select title from dssdb.dataset where dsid = %s",
                       (dsid, ))
        res = cursor.fetchone()
        if res is not None:
            if os.path.exists((root_dirs['cvs'] + "/datasets/" + dsid +
                               ".xml,v")):
                return render(request, "metaman/datasets/create.html",
                              {'already_in_use': True})

        start = datetime.now()
        while os.path.exists(root_dirs['cvs'] + "/datasets/.lock"):
            now = datetime.now()
            tdelta = now - start
            if tdelta.total_seconds() > 10:
                s = smtplib.SMTP('localhost')
                msg = EmailMessage()
                msg['From'] = iuser + "@ucar.edu"
                msg['Subject'] = "CVS lock error"
                msg['To'] = "dattore@ucar.edu"
                msg.set_content(("CVS lock error while '" + iuser + "' was "
                                 "creating dataset '" + dsid + "'."))
                s.send_message(msg)
                s.quit()
                return render(request, "metaman/datasets/create.html",
                              {'lock_timeout': True})

    except psycopg2.Error as err:
        log_error(err, source="create")
        return render(request, "metaman/datasets/create.html",
                      {'database_error': "{}".format(err)})

    # create a temporary directory
    tdir_name = utils.make_tempdir()
    if len(tdir_name) == 0:
        return render(request, "metaman/datasets/create.html",
                      {'temp_dir_failed': True})

    # add the dataset to the search schema
    try:
        cursor.execute(("update search.datasets set type = 'W', title = '' "
                        "where dsid = %s and type = 'R'"), (dsid, ))
        conn.commit()
    except psycopg2.Error as err:
        utils.remove_tempdir(tdir_name)
        log_error(err, source="create")
        return render(request, "metaman/datasets/create.html",
                      {'database_error': "{}".format(err)})

    # create the cvs document
    try:
        Path(root_dirs['cvs'] + "/datasets/.lock").touch()
        subprocess.run((
                bin_utils['cvs'] + " -Q -d " + root_dirs['cvs'] +
                " checkout -d " + tdir_name + " -l datasets"), shell=True)
        with open(tdir_name + "/" + dsid + ".xml", "w") as f:
            f.write("<?xml version=\"1.0\" ?>\n")
            f.write(("<dsOverview xmlns:xsi=\"http://www.w3.org/2001/"
                     "XMLSchema-instance\"\n"))
            f.write(("            xsi:schemaLocation=\"https://rda.ucar.edu/"
                     "schemas\n"))
            f.write(("                                https://rda.ucar.edu/"
                     "schemas/dsOverview3.xsd\"\n"))

            f.write(("            ID=\"" + dsid + "\" type=\""
                     "work-in-progress\">\n"))
            f.write("  <continuingUpdate value=\"no\" />\n")
            cursor.execute(("select fstname, lstname from dssdb.dssgrp "
                            "where logname = %s"), (iuser, ))
            res = cursor.fetchone()
            if res is None:
                return render(request, "metaman/datasets/create.html",
                              {'missing_specialist': iuser})
            else:
                f.write(("  <contact>" + res[0] + " " + res[1] +
                         "</contact>\n"))

            f.write("</dsOverview>\n")

        f.close()
        subprocess.run((
                bin_utils['cvs'] + " -Q -d " + root_dirs['cvs'] + " add " +
                tdir_name + "/" + dsid + ".xml"), shell=True)
        o = subprocess.run((
                bin_utils['cvs'] + " -Q -d " + root_dirs['cvs'] + " commit -m "
                "\"initial version\" " + tdir_name + "/" + dsid + ".xml"),
                shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        Path(root_dirs['cvs'] + "/datasets/.lock").unlink()
        o = o.stderr.decode("utf-8")
        if len(o) > 0:
            return render(request, "metaman/datasets/create.html",
                          {'cvs_commit_error': o})

    except Exception as err:
        utils.remove_tempdir(tdir_name)
        log_error(err, source="create")
        return render(request, "metaman/datasets/create.html",
                      {'cvs_open_failed': True})

    # add the dataset to the dssdb schema
    try:
        cursor.execute(("insert into dssdb.dsowner (dsid, specialist, "
                        "priority) values (%s, %s, %s)"), (dsid, iuser, 1))
        conn.commit()
        cursor.execute((
                "insert into dssdb.dataset (dsid, date_create, use_rdadb, "
                "webhome) values (%s, %s, %s, %s)"),
                (dsid, datetime.now().strftime("%Y-%m-%d"), "Y",
                 settings.RDA_DATA_PATH + dsid))
        conn.commit()
    except psycopg2.Error as err:
        utils.remove_tempdir(tdir_name)
        log_error(err, source="create")
        return render(request, "metaman/datasets/create.html",
                      {'database_error': "{}".format(err)})

    # add the dataset to wagtail
    subprocess.run(("/usr/local/rdaweb/bin/apacherun /usr/local/rdaweb/bin/"
                    "add_dataset " + dsid), shell=True)

    # create the web directories
    subprocess.run("mkdir -p " + tdir_name + "/datasets/" + dsid + "/metadata",
                   shell=True)
    utils.rdadata_rsync(tdir_name, "datasets/" + dsid + "/metadata/",
                        root_dirs['web'])
    subprocess.run("mkdir -p " + tdir_name + "/internal/datasets/" + dsid,
                   shell=True)
    utils.rdadata_rsync(tdir_name, "internal/datasets/" + dsid + "/",
                        root_dirs['web'])

    # clean up
    cursor.close()
    conn.close()
    utils.remove_tempdir(tdir_name)
    return render(request, "metaman/datasets/create.html", {'dsid': dsid})


def change_history(request, dsid):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    d = {}
    with open(root_dirs['cvs'] + "/datasets/" + dsid + ".xml,v") as f:
        key = None
        for line in f:
            if line[0:4] == "date":
                dt = datetime(int(line[5:9]), int(line[10:12]),
                              int(line[13:15]), int(line[16:18]),
                              int(line[19:21]),
                              int(line[22:24])) - relativedelta(hours=7)
                d.update({key: {'timestamp': dt.strftime("%Y-%m-%d %H:%M")}})
            elif line[0:3] == "log":
                line = f.readline()
                idx = line.find(":")
                if idx > 0:
                    d[key]['specialist'] = line[1:idx]
                    d[key]['commit_msg'] = line[idx+1:].strip()

            key = line.strip()

    l = []
    for key in d:
        l.append({'key': key, 'data': d[key]})

    return render(request, "metaman/datasets/show_history.html",
                  {'versions': l, 'dsid': dsid})


def delete(request, dsid):
    # verify that this dataset has never been published
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute(("select type, pub_date from search.datasets where "
                        "dsid = %s"), (dsid, ))
        res = cursor.fetchone()
    except psycopg2.Error as err:
        log_error(err, source="delete")
        return render(request, "metaman/datasets/delete.html",
                      {'database_error': "{}".format(err)})

    if res[0] != "W" or (res[1].year > 1900 and res[1].year < 2100):
        return render(request, "metaman/datasets/delete.html",
                      {'published': True})

    messages = []
    hosts = ["rda-web-prod01", "rda-web-test01"]
    for host in hosts:
        # remove the public and internal web directories
        o = subprocess.check_output((
                bin_utils['rdadatarun'] + " ssh -i " +
                root_dirs['rdadata_home'] + "/.ssh/" + host +
                "-sync_rdadata_rsa -l rdadata rdadata@" + host + ".ucar.edu "
                "\"rm -rf " + root_dirs['web'] + "/datasets/" + dsid + "\""),
                shell=True, stderr=subprocess.STDOUT).decode("utf-8")
        if o[0:7] == "Success" or o.find("No such file or directory") >= 0:
            messages.append({'success': True,
                             'value': "Public web directory was deleted"})
        else:
            messages.append({
                    'success': False,
                    'value': ("Deletion of public web directory failed with "
                              "error '{}'").format(o)})
            return render(request, "metaman/datasets/delete.html",
                          {'message_list': messages})

        o = subprocess.check_output((
                bin_utils['rdadatarun'] + " ssh -i " +
                root_dirs['rdadata_home'] + "/.ssh/" + host +
                "-sync_rdadata_rsa -l rdadata rdadata@" + host + ".ucar.edu "
                "\"rm -rf " + root_dirs['web'] + "/internal/datasets/" + dsid +
                "\""),
                shell=True, stderr=subprocess.STDOUT).decode("utf-8")
        if o[0:7] == "Success" or o.find("No such file or directory") >= 0:
            messages.append({'success': True,
                             'value': "Internal web directory was deleted"})
        else:
            messages.append({
                    'success': False,
                    'value': ("Deletion of internal web directory failed "
                              "with error '{}'").format(o)})
            return render(request, "metaman/datasets/delete.html",
                          {'message_list': messages})

    # unpublish the dataset pages
    unpub_cmd = ("cd /usr/local/rdaweb; source bin/activate; python manage.py "
                 "unpublish_dataset " + dsid)
    o = subprocess.check_output(unpub_cmd, shell=True,
                                stderr=subprocess.STDOUT).decode("utf-8")
    if o.find("Success: unpublished") >= 0:
        messages.append({'success': True,
                         'value': "Dataset pages were unpublished"})
    else:
        messages.append({
                'success': False,
                'value': "Unpublish failed with error '{}'".format(o)})
        return render(request, "metaman/datasets/delete.html",
                      {'message_list': messages})

    # delete the dataset entries in 'rdadb'
    try:
        cursor.execute("delete from dssdb.dataset where dsid = %s", (dsid, ))
        conn.commit()
        messages.append({
                'success': True,
                'value': ("'" + dsid + "' was removed from table 'dssdb."
                          "dataset'")})
    except psycopg2.Error as err:
        messages.append({
                'success': False,
                'value': ("Database error: '{}' while removing dataset from "
                          "table 'dssdb.dataset'").format(err)})
        log_error(err, source="delete")
        return render(request, "metaman/datasets/delete.html",
                      {'message_list': messages})

    try:
        cursor.execute("delete from dssdb.dsowner where dsid = %s", (dsid, ))
        conn.commit()
        messages.append({
                'success': True,
                'value': ("'" + dsid + "' was removed from table 'dssdb."
                          "dsowner'")})
    except psycopg2.Error as err:
        messages.append({
                'success': False,
                'value': ("Database error: '{}' while removing dataset from "
                          "table 'dssdb.dsowner'").format(err)})
        log_error(err, source="delete")
        return render(request, "metaman/datasets/delete.html",
                      {'message_list': messages})

    # remove the cvs document
    cvs_cmd = (bin_utils['rdadatarun'] + " rm -f " + root_dirs['cvs'] +
               "/datasets/" + dsid + ".xml,v")
    o = subprocess.check_output(cvs_cmd, shell=True,
                                stderr=subprocess.STDOUT).decode("utf-8")
    if o.find("Success") >= 0:
        messages.append({'success': True,
                         'value': "The CVS document was removed."})
    else:
        messages.append({
                'success': False,
                'value': ("Removal of the CVS document failed with error "
                          "'{}'").format(o[o.find("Error:"):])})
        return render(request, "metaman/datasets/delete.html",
                      {'message_list': messages})

    # delete the dataset entry in 'search.datasets'
    try:
        cursor.execute("delete from search.datasets where dsid = %s", (dsid, ))
        conn.commit()
        messages.append({
                'success': True,
                'value': ("'" + dsid + "' was removed from table 'search."
                          "datasets'")})
    except psycopg2.Error as err:
        messages.append({
                'success': False,
                'value': ("Database error: '{}' while removing dataset from "
                          "table 'search.datasets'").format(err)})
        log_error(err, source="delete")
        return render(request, "metaman/datasets/delete.html",
                      {'message_list': messages})

    cursor.close()
    conn.close()
    return render(request, "metaman/datasets/delete.html",
                  {'message_list': messages})


def discard_changes(request, dsid):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    ctx = {'dsid': dsid}
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute("delete from metautil.metaman where dsid = %s",
                       (dsid, ))
        cursor.execute("delete from metautil.cmd where dsid = %s", (dsid, ))
        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as err:
        ctx.update({'error': "A database error occurred: '{}'".format(err)})

    return render(request, "metaman/datasets/discard.html", ctx)


def edit(request, dsid):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    spellchecker = SpellChecker()
    if not spellchecker.ready:
        return render(
                request, "metaman/datasets/edit.html",
                {'error': ("the spell checker is not ready: '" +
                           spellchecker.error + "'")})

    ctx = {'dsid': dsid}
    iuser = utils.get_iuser(request)
    ctx.update({'is_manager': (iuser in config.metadata_managers)})
    if 'clear_changes' in request.POST:
        clear_changes = request.POST['clear_changes']
    else:
        clear_changes = ""

    # check for uncommitted changes
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute(("select lockname, updated_any_field from metautil."
                        "metaman where dsid = %s"), (dsid, ))
        res = cursor.fetchall()
        if len(res) > 0:
            if res[0][0] != iuser:
                ctx.update({'lock_user': res[0][0]})
                return render(request, "metaman/datasets/uncommitted.html",
                              ctx)

            if res[0][1] == "N" or clear_changes == "yes":
                cursor.execute((
                        "delete from metautil.metaman where dsid = %s"),
                        (dsid, ))
                cursor.execute(("delete from metautil.cmd where dsid = %s"),
                               (dsid, ))
                conn.commit()
                clear_changes = ""
            elif clear_changes == "":
                return render(request, "metaman/datasets/uncommitted.html",
                              ctx)

    except psycopg2.Error as err:
        ctx.update({'database_error': "{}".format(err)})
        log_error(err, source="edit")
        return render(request, "metaman/datasets/uncommitted.html", ctx)

    # check for automatic content metadata
    try:
        cursor.execute(("select distinct schemaname from pg_catalog.pg_tables "
                        "where schemaname like '%ML'"))
        res = cursor.fetchall()
        cmd_database_names = []
        ignore_db_prefixes = ['I', 'V']
        for r in res:
            if r[0][0] not in ignore_db_prefixes:
                cmd_database_names.append(r[0])

    except psycopg2.Error as err:
        log_error(err, source="edit")

    show_manual_cmd = True
    for db in cmd_database_names:
        try:
            cursor.execute(("select count(*) from \"" + db + "\"." + dsid +
                            "_webfiles2"))
            res = cursor.fetchall()
            if len(res) > 0 and res[0][0] != "0":
                show_manual_cmd = False

        except psycopg2.Error:
            conn.rollback()

    has_doi = utils.has_doi(dsid)
    if type(has_doi) is str:
        log_error(has_doi, source="edit")
        return render(
                request,
                "metaman/datasets/edit.html",
                {'error': ("database error while checking for DOI lock: '{}'")
                 .format(has_doi)})

    ctx.update({'has_doi': has_doi})
    version = "latest_version"
    if len(clear_changes) == 0:
        # fill edit fields from most recent commit (CVS file)
        tdir_name = utils.make_tempdir()
        if len(tdir_name) == 0:
            return render(
                    request,
                    "metaman/datasets/edit.html",
                    {'error': "unable to create a temporary directory"})

        checkout_cmd = (bin_utils['cvs'] + " -Q -d " + root_dirs['cvs'] +
                        " checkout -d " + tdir_name)
        if 'version' in request.POST and len(request.POST['version']) > 0:
            version = request.POST['version']
            checkout_cmd += " -r " + version

        checkout_cmd += " datasets/" + dsid + ".xml"
        o = subprocess.run(checkout_cmd, shell=True, stdout=subprocess.DEVNULL,
                           stderr=subprocess.PIPE)
        o = o.stderr.decode("utf-8")
        if len(o) > 0:
            utils.remove_tempdir(tdir_name)
            return render(
                    request,
                    "metaman/datasets/edit.html",
                    {'error': ("unable to check out the CVS file: <font "
                               "color=\"red\">" + o + "</font>")})

        res = fill_from_most_recent_commit(
                conn, iuser, tdir_name, dsid, show_manual_cmd, spellchecker)
        if 'error' in res[0]:
            utils.remove_tempdir(tdir_name)
            return render(
                    request,
                    "metaman/datasets/edit.html", {'error': res[0]['error']})

        ctx.update(res[0])
        ctx.update({'errors': res[1]})
        utils.remove_tempdir(tdir_name)
    else:
        # fill edit fields from uncommitted changes (DB)
        res = fill_from_uncommitted_changes(cursor, dsid, spellchecker)
        if 'error' in res[0]:
            return render(
                    request,
                    "metaman/datasets/edit.html", {'error': res[0]['error']})

        ctx.update(res[0])
        ctx.update({'errors': res[1]})

    cursor.close()
    conn.close()
    ctx.update({'clear_changes': clear_changes, 'version': version,
                'show_manual_cmd': show_manual_cmd})
    try:
        tree = ElementTree.parse((root_dirs['web'] +
                                 "/metadata/schemas/dsOverview3.xsd"))
        root = tree.getroot()
        ns = {
            'xsd': "http://www.w3.org/2001/XMLSchema",
        }
        ctx.update({'curation_level_options': get_curation_options(root, ns)})
        ctx.update({
                'update_frequency_options': get_update_frequency_options(
                        root, ns)})
        ctx.update({
                'dataset_type_options': get_dataset_type_options(
                        root, ns, has_doi)})
        if show_manual_cmd:
            ctx.update({'data_format_options': get_data_format_options()})

    except Exception as err:
        log_error(err, source="edit")

    ctx.update({'license_options': get_license_options()})
    if 'license' not in ctx:
        ctx.update({'license': ctx['license_options'][0]['value']})

    ctx.update({'iso_topics': config.ISO_topics})
    return render(request, "metaman/datasets/edit.html", ctx)


def show_web_access(request, dsid):
    path = os.path.join(settings.RDA_CANONICAL_DATA_PATH, dsid)
    if not os.path.exists(path):
        return HttpResponse(
                "Data directory does not exist on the RDA web server",
                status=500)

    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        cursor.execute("select dwebcnt from dssdb.dataset where dsid = %s",
                       (dsid, ))
        res = cursor.fetchone()

    except psycopg2.Error as err:
        log_error(err, source="show_web_access")
        return HttpResponse("Database error: '{}'".format(err),
                            status=500)

    if res[0] == "0":
        return HttpResponse((
                "According to RDADB, there are no web data files "
                "associated with this dataset"),
                status=500)

    try:
        cursor.execute(("select inet_access from search.datasets where dsid = "
                        "%s"), (dsid, ))
        res = cursor.fetchone()

    except psycopg2.Error as err:
        log_error(err, source="show_web_access")
        return HttpResponse("Database error: '{}'".format(err),
                            status=500)

    cursor.close()
    conn.close()
    if res[0] == "Y":
        curr_set = "on"
        new_set = "off"
    else:
        curr_set = "off"
        new_set = "on"

    return render(request, "metaman/datasets/web_access.html", {
                 'dsid': dsid,
                 'current_setting': curr_set,
                 'new_setting': new_set})


def do_web_access_toggle(request, dsid):
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        inet_access = "Y" if request.POST['inetOption'] == "on" else "N"
        cursor.execute(("update search.datasets set inet_access = %s where "
                        "dsid = %s"), (inet_access, dsid))
        conn.commit()
        cursor.close()
        conn.close()

    except psycopg2.Error as err:
        log_error(err, source="do_web_access_toggle")
        return render(
                request, "500.html",
                {'custom_message': "Database error: '{}'".format(err)})

    return render(request, "metaman/datasets/web_access.html", {
                  'toggle_access': True,
                  'dsid': dsid,
                  'inet_option': request.POST['inetOption']})


def web_access(request, dsid):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    if 'inetOption' in request.POST:
        return do_web_access_toggle(request, dsid)

    return show_web_access(request, dsid)


def fill_from_most_recent_commit(conn, iuser, tdir_name, dsid, show_manual_cmd,
                                 spellchecker):
    page_vars = {
        'curation_level': "",
        'dataset_type': "",
        'contacts': "",
        'redundancies_exist': "",
        'redundancies': "",
        'title': "",
        'authors': "",
        'contributors': "",
        'update_frequency': "",
        'logo': "",
        'summary': "",
        'variables': "",
        'platforms': "",
        'instruments': "",
        'projects': "",
        'supports_projects': "",
        'iso_topic': "",
        'access_restrictions': "",
        'usage_restrictions': "",
        'references': "",
        'reflists': "",
        'acknowledgement': "",
        'related_resources': "",
        'related_datasets': "",
        'related_dois': "",
        'license': "",
    }
    cursor = conn.cursor()
    try:
        tree = ElementTree.parse(tdir_name + "/" + dsid + ".xml")
    except Exception as err:
        log_error(err, source="fill_from_most_recent_commit")
        return ({'error': ("unable to open XML overview document '" +
                           tdir_name + "/" + dsid + ".xml': '{}'")
                .format(err)}, )

    errors = {}
    root = tree.getroot()
    v = root.get("curationLevel")
    if v is not None:
        page_vars['curation_level'] = v
    else:
        errors.update({
                'curation_level': ("The dataset curation level must be "
                                   "specified")})

    page_vars['dataset_type'] = root.get("type")
    elist = root.findall("./contact")
    contacts = []
    errs = []
    for e in elist:
        contacts.append(e.text)
        cursor.execute((
                "select logname from dssdb.dssgrp where concat(fstname, ' ', "
                "lstname) = %s and stat_flag = 'C'"), (e.text, ))
        res = cursor.fetchall()
        if len(res) == 0:
            errs.append(e.text)

    if len(errs) > 0:
        errors.update({'contacts': ("Invalid specialist(s) must be removed:"
                                    "<br>" + "<br>").join(errs)})

    page_vars['contacts'] = "\n".join(contacts)
    e = root.find("./redundancies")
    if e is not None:
        r = e.get("exist")
        redundancies = [r]
        page_vars['redundancies_exist'] = r
        elist = e.findall("redundancy")
        if len(elist) == 0:
            if r == "yes":
                errors.update({
                        'redundancies': ("Because you answered <b>yes</b>, "
                                         "you must enter information for at "
                                         "least one alternate repository that "
                                         "hosts this dataset.")})

        else:
            errs = []
            for e in elist:
                url = e.get("url") or ""
                if len(url) > 0:
                    try:
                        response = requests.get(
                                url, headers=config.linkcheck_headers)
                        response.raise_for_status()
                    except Exception:
                        log_error(("Link check failure for '" + url + "': " +
                                   str(response.status_code)),
                                  source="fill_from_most_recent_commit")
                        errs.append(("- Unresolvable URL <i>" + url + "</i> "
                                     "must be fixed or removed"))

                redundancies.append(
                        "[!]".join([url.replace("%", "%25"),
                                    (e.get("name") or ""),
                                    (e.get("address") or "")]))

            if len(errs) > 0:
                errors.update({'redundancies': "<br>".join(errs)})

        page_vars['redundancies'] = "\n".join(redundancies)

    else:
        errors.update(
                {'redundancies': ("You must state, yes or no, whether or not "
                                  "other copies of this dataset are known to "
                                  "exist.")})

    e = root.find("./title")
    if e is not None:
        page_vars['title'] = e.text
        errs = check_title(page_vars['title'], spellchecker)
        if len(errs) > 0:
            errors.update({'title': errs})

    elist = root.findall("./author")
    authors = []
    for e in elist:
        lname = e.get("lname")
        if lname is not None:
            authors.append("[!]".join([e.get("fname"), e.get("mname"), lname,
                                       (e.get("orcid_id") or "")]))
        else:
            name = e.get("name")
            if name is not None:
                authors.append(name)
            else:
                return ({'error': "bad author: '" + str(e) + "'"}, )

    page_vars['authors'] = "\n".join(authors)
    try:
        cursor.execute((
                "select g.path, p.keyword, p.former_name, p.contact, p."
                "citable from search.contributors_new as p left join search."
                "gcmd_providers as g on g.uuid = p.keyword where p.dsid = %s "
                "and p.vocabulary = 'GCMD' order by p.disp_order, g.path"),
               (dsid, ))
        res = cursor.fetchall()
    except psycopg2.Error as err:
        log_error(err, source="fill_from_most_recent_commit")
        return ({'error': ("unable to retrieve contributor keywords from the "
                           "metadata database: '{}'").format(err)}, )

    contributors = []
    for e in res:
        contributors.append("[!]".join(["" if x is None else x for x in e]))

    page_vars['contributors'] = "\n".join(contributors)
    e = root.find("./continuingUpdate")
    if e is not None:
        ufreq = e.get("frequency")
        ufreq = "yes<!>" + ufreq if ufreq is not None else "no"
        page_vars['update_frequency'] = ufreq

    e = root.find("./logo")
    src = "default_200_200.png"
    width = 70
    if e is not None:
        src = e.text
        sparts = src.split(".")
        iparts = sparts[len(sparts)-2].split("_")
        plen = len(iparts)
        if iparts[plen-2] != iparts[plen-1]:
            w = int(iparts[plen-2])
            h = int(iparts[plen-1])
            width = w * width / h

    page_vars['logo'] = {'src': src, 'width': width}
    e = root.find("./summary")
    s = ""
    errs = []
    if e is not None:
        s = ElementTree.tostring(e).decode().replace("&amp;", "&")
        errs.extend(check_html(s, spellchecker))
        page_vars['summary'] = utils.trim(s[s.find(">")+1:s.rfind("</")])

    sparts = s.split()
    if len(sparts) < 50:
        errs.insert(0, ("The Summary/Abstract MUST contain at least fifty "
                        "words. (This is a JSON-LD requirement)"))

    if len(errs) > 0:
        errors.update({'summary': "<br>".join(errs)})

    try:
        cursor.execute((
                "select g.path, v.keyword from search.variables as v left "
                "join search.gcmd_sciencekeywords as g on g.uuid = v.keyword "
                "where v.dsid = %s and v.vocabulary = 'GCMD' order by g.path"),
               (dsid, ))
        res = cursor.fetchall()
    except psycopg2.Error as err:
        log_error(err, source="fill_from_most_recent_commit")
        return ({'error': ("unable to retrieve variable keywords from the "
                           "metadata database: '{}'").format(err)}, )

    variables = []
    for e in res:
        variables.append("[!]".join([e[0], e[1]]))

    page_vars['variables'] = "\n".join(variables)
    try:
        cursor.execute((
                "select g.path, p.keyword from search.platforms_new as p left "
                "join search.gcmd_platforms as g on g.uuid = p.keyword where "
                "p.dsid = %s and p.vocabulary = 'GCMD' order by g.path"),
               (dsid, ))
        res = cursor.fetchall()
    except psycopg2.Error as err:
        log_error(err, source="fill_from_most_recent_commit")
        return ({'error': ("unable to retrieve platform keywords from the "
                           "metadata database: '{}'").format(err)}, )

    platforms = []
    for e in res:
        platforms.append("[!]".join([e[0], e[1]]))

    page_vars['platforms'] = "\n".join(platforms)
    try:
        cursor.execute((
                "select g.path, i.keyword from search.instruments as i left "
                "join search.gcmd_instruments as g on g.uuid = i.keyword "
                "where i.dsid = %s and i.vocabulary = 'GCMD' order by g.path"),
               (dsid, ))
        res = cursor.fetchall()
    except psycopg2.Error as err:
        log_error(err, source="fill_from_most_recent_commit")
        return ({'error': ("unable to retrieve instrument keywords from the "
                           "metadata database: '{}'").format(err)}, )

    instruments = []
    for e in res:
        instruments.append("[!]".join([e[0], e[1]]))

    page_vars['instruments'] = "\n".join(instruments)
    try:
        cursor.execute((
                "select g.path, p.keyword from search.projects_new as p left "
                "join search.gcmd_projects as g on g.uuid = p.keyword where p."
                "dsid = %s and p.vocabulary = 'GCMD' order by g.path"),
               (dsid, ))
        res = cursor.fetchall()
    except psycopg2.Error as err:
        log_error(err, source="fill_from_most_recent_commit")
        return ({'error': ("unable to retrieve project keywords from the "
                           "metadata database: '{}'").format(err)}, )

    projects = []
    for e in res:
        projects.append("[!]".join([e[0], e[1]]))

    page_vars['projects'] = "\n".join(projects)
    try:
        cursor.execute((
                "select g.path, p.keyword from search.supported_projects as p "
                "left join search.gcmd_projects as g on g.uuid = p.keyword "
                "where p.dsid = %s and p.vocabulary = 'GCMD' order by g.path"),
               (dsid, ))
        res = cursor.fetchall()
    except psycopg2.Error as err:
        log_error(err, source="fill_from_most_recent_commit")
        return ({'error': ("unable to retrieve 'supports' project keywords "
                           "from the metadata database: '{}'").format(err)}, )

    supp_projects = []
    for e in res:
        supp_projects.append("[!]".join([e[0], e[1]]))

    page_vars['supports_projects'] = "\n".join(supp_projects)
    e = root.find("./topic[@vocabulary='ISO']")
    if e is not None:
        page_vars['iso_topic'] = e.text

    e = root.find("./restrictions/access")
    if e is not None:
        s = ElementTree.tostring(e).decode().replace("&amp;", "&")
        errs = check_html(s, spellchecker)
        if len(errs) > 0:
            errors.update({'access_restrictions': "<br>".join(errs)})

        page_vars['access_restrictions'] = (
                utils.trim(s[s.find(">")+1:s.rfind("</")]))

    e = root.find("./restrictions/usage")
    if e is not None:
        if e.text is None:
            s = ElementTree.tostring(e).decode().replace("&amp;", "&")
            errs = check_html(s, spellchecker)
            if len(errs) > 0:
                errors.update({'usage_restrictions': "<br>".join(errs)})
            page_vars['usage_restrictions'] = s[s.find(">")+1:s.rfind("</")]

    elist = root.findall("./reference")
    references = []
    for e in elist:
        ref = []
        ref.append(e.get("type"))
        for child in e:
            a = []
            for attr in child.attrib:
                a.append(child.attrib[attr])

            text = child.text
            if child.tag in ("annotation", "doi", "url"):
                text = ":".join([child.tag, text])

            a.append(text)
            ref.append("[+]".join(a))

        rel = e.get("ds_relation")
        if rel is not None:
            ref.append("ds_rel:" + rel)

        references.append("[!]".join(ref))

    page_vars['references'] = "\n".join(references)
    errs = check_references(references)
    if len(errs) > 0:
        errors.update({'references': "<br>".join(errs)})

    elist = root.findall("./referenceURL")
    reflists = []
    for e in elist:
        reflists.append("[!]".join([e.get("url"), e.text]))

    page_vars['reflists'] = "\n".join(reflists)
    e = root.find("./acknowledgement")
    if e is not None:
        if e.text is None:
            s = ElementTree.tostring(e).decode().replace("&amp;", "&")
            errs = check_html(s, spellchecker)
            if len(errs) > 0:
                errors.update({'acknowledgement': "<br>".join(errs)})
            page_vars['acknowledgement'] = s[s.find(">")+1:s.rfind("</")]

    elist = root.findall("./relatedResource")
    rel_resources = []
    for e in elist:
        url = e.get("url")
        rel_resources.append("[!]".join([url, e.text]))

    page_vars['related_resources'] = "\n".join(rel_resources)
    errs = check_related_sites(rel_resources)
    if len(errs) > 0:
        errors.update({'related_resources': "<br>".join(errs)})

    elist = root.findall("./relatedDataset")
    rel_datasets = []
    for e in elist:
        rel_dsid = e.get("ID")
        if len(rel_dsid) == 5 and rel_dsid[3] == '.':
            rel_dsid = "d" + rel_dsid[0:3] + "00" + rel_dsid[4:]

        rel_datasets.append(rel_dsid)

    page_vars['related_datasets'] = "\n".join(rel_datasets)
    errs = check_related_datasets(rel_datasets, cursor)
    if len(errs) > 0:
        errors.update({
                'related_datasets': ("References to non-primary and non-"
                                     "historical datasets must be removed:"
                                     "<br>" + "<br>").join(errs)})

    elist = root.findall("./relatedDOI")
    rel_dois = []
    for e in elist:
        rel_dois.append("[!]".join([e.text, e.get("relationType")]))

    page_vars['related_dois'] = "\n".join(rel_dois)
    errs = check_related_dois(rel_dois)
    if len(errs) > 0:
        errors.update({'related_dois': "<br>".join(errs)})

    e = root.find("./dataLicense")
    if e is not None and e.text != "None":
        page_vars['license'] = e.text
    else:
        page_vars['license'] = config.default_data_license

    e = root.find("./publicationDate")
    pub_date = e.text if e is not None else ""
    if len(pub_date) == 0:
        try:
            cursor.execute(("select pub_date from search.datasets where dsid "
                            "= %s"), (dsid, ))
            res = cursor.fetchone()
            if res is not None:
                pub_date = res[0]
            else:
                err = "No publication date in the database"
                log_error(err, source="fill_from_most_recent_commit")
                return ({'error': ("unable to get dataset publication date: "
                                   "'{}'").format(err)}, )

        except psycopg2.Error as err:
            log_error(err, source="fill_from_most_recent_commit")
            return ({'error': ("unable to get dataset publication date: '{}'")
                    .format(err)}, )

    if show_manual_cmd:
        page_vars.update({'manual_cmd': get_manual_cmd_values(root)})

    try:
        cursor.execute((
                "insert into metautil.metaman (dsid, lockname, ds_type, "
                "ds_curation, update_frequency, logo, title, summary, "
                "contributors, authors, access_restrictions, "
                "usage_restrictions, access_code, variables, contacts, "
                "platforms, instruments, projects, supports_projects, "
                "iso_topic, keywords, _references, reflists, acknowledgement, "
                "related_resources, related_dois, related_datasets, "
                "publication_date, redundancys, license, content_metadata) "
                "values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
                "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
                "%s, %s, %s) on conflict on constraint metaman_pkey do "
                "nothing"), (
                dsid,
                iuser,
                page_vars['dataset_type'],
                page_vars['curation_level'],
                page_vars['update_frequency'],
                page_vars['logo']['src'],
                page_vars['title'],
                page_vars['summary'],
                page_vars['contributors'],
                page_vars['authors'],
                page_vars['access_restrictions'],
                page_vars['usage_restrictions'],
                "",
                page_vars['variables'],
                page_vars['contacts'],
                page_vars['platforms'],
                page_vars['instruments'],
                page_vars['projects'],
                page_vars['supports_projects'],
                page_vars['iso_topic'],
                "",
                page_vars['references'],
                page_vars['reflists'],
                page_vars['acknowledgement'],
                page_vars['related_resources'],
                page_vars['related_dois'],
                page_vars['related_datasets'],
                pub_date,
                page_vars['redundancies'],
                page_vars['license'],
                ("Y" if show_manual_cmd else "N")))
        conn.commit()
    except psycopg2.Error as err:
        log_error(err, source="fill_from_most_recent_commit")
        return ({'error': ("unable to insert core values for uncommitted "
                           "changes: '{}'").format(err)}, )

    if show_manual_cmd:
        try:
            ascii_url = (page_vars['manual_cmd']['ascii_url'] if 'ascii_url'
                         in page_vars['manual_cmd'] else "")
            binary_url = (page_vars['manual_cmd']['binary_url'] if
                          'binary_url' in page_vars['manual_cmd'] else "")
            cursor.execute((
                    "insert into metautil.cmd (dsid, periods, "
                    "temporal_frequencys, data_types, formats, ascii_url, "
                    "binary_url, varlist, levels, coverages) values (%s, %s, "
                    "%s, %s, %s, %s, %s, %s, %s, %s) on conflict on "
                    "constraint cmd_pkey do nothing"), (
                    dsid,
                    page_vars['manual_cmd']['temporal_periods'],
                    page_vars['manual_cmd']['temporal_frequencies'],
                    page_vars['manual_cmd']['data_types'],
                    page_vars['manual_cmd']['data_formats'],
                    ascii_url,
                    binary_url,
                    page_vars['manual_cmd']['variables'],
                    page_vars['manual_cmd']['levels'],
                    page_vars['manual_cmd']['coverages']))
            conn.commit()
        except psycopg2.Error as err:
            log_error(err, source="fill_from_most_recent_commit")
            return ({'error': ("unable to insert cmd for uncommitted changes: "
                               "'{}'").format(err)}, )
    return (page_vars, errors)


def fill_from_uncommitted_changes(cursor, dsid, spellchecker):
    page_vars = {}
    errors = {}
    try:
        cursor.execute((
                "select ds_type, ds_curation, update_frequency, logo, title, "
                "summary, contributors, authors, access_restrictions, "
                "usage_restrictions, access_code, variables, contacts, "
                "platforms, instruments, projects, supports_projects, "
                "iso_topic, keywords, _references, reflists, acknowledgement, "
                "related_resources, related_dois, related_datasets, "
                "publication_date, redundancys, license, content_metadata "
                "from metautil.metaman where dsid = %s"), (dsid, ))
        res = cursor.fetchone()
    except Exception as err:
        log_error(err, source="fill_from_uncommitted_changes")
        return ({'error': ("database error while getting uncommitted changes: "
                           "'{}'").format(err)}, )

    page_vars.update({
            'dataset_type': res[0], 'curation_level': res[1],
            'update_frequency': res[2]})
    src = "default_200_200.png"
    width = 70
    if res[3] is not None:
        src = res[3]
        sparts = src.split(".")
        iparts = sparts[len(sparts)-2].split("_")
        plen = len(iparts)
        if iparts[plen-2] != iparts[plen-1]:
            w = int(iparts[plen-2])
            h = int(iparts[plen-1])
            width = w * width / h

    page_vars.update({
            'logo': {'src': src, 'width': width},
            'title': res[4], 'summary': res[5], 'contributors': res[6],
            'authors': res[7], 'access_restrictions': res[8],
            'usage_restrictions': res[9], 'variables': res[11],
            'contacts': res[12], 'platforms': res[13], 'instruments': res[14],
            'projects': res[15], 'supports_projects': res[16],
            'iso_topic': res[17], 'references': res[19], 'reflists': res[20],
            'acknowledgement': res[21], 'related_resources': res[22],
            'related_dois': res[23], 'related_datasets': res[24]})
    parts = res[26].strip().split("\n")
    page_vars.update({
            'redundancies_exist': parts[0],
            'redundancies': "\n".join(parts),
            'license': res[27]})
    errs = []
    for n in range(1, len(parts)):
        x = parts[n].split("[!]")
        if len(x[0]) > 0:
            try:
                response = requests.get(x[0], headers=config.linkcheck_headers)
                response.raise_for_status()
            except Exception:
                log_error(("Link check failure for '" + x[0] + "': " +
                           str(response.status_code)),
                          source="fill_from_uncommitted_changes (A)")
                errs.append(("- broken link <i>" + x[0] + "</i> must be fixed "
                             "or removed"))

    if len(errs) > 0:
        errors.update({'redundancies': "<br>".join(errs)})

    spellchecker.check(res[4])
    if len(spellchecker.misspelled_words) > 0:
        errors.update({
                'title': ("- Misspelled/unrecognized word(s) must be "
                          "corrected:<br><i>" + ", ")
                .join(spellchecker.misspelled_words) + "</i>"})

    errs = check_html("<summary>" + res[5] + "</summary>", spellchecker)
    if len(errs) > 0:
        errors.update({'summary': "<br>".join(errs)})

    if len(res[8]) > 0:
        errs = check_html("<access>" + res[8] + "</access>", spellchecker)
        if len(errs) > 0:
            errors.update({'access_restrictions': "<br>".join(errs)})

    if len(res[9]) > 0:
        errs = check_html("<usage>" + res[9] + "</usage>", spellchecker)
        if len(errs) > 0:
            errors.update({'usage_restrictions': "<br>".join(errs)})

    if len(res[19]) > 0:
        ref_list = res[19].strip().split("\n")
        errs = check_references(ref_list)
        if len(errs) > 0:
            errors.update({'references': "<br>".join(errs)})

    if len(res[21]) > 0:
        errs = check_html("<acknowledgement>" + res[21] + "</acknowledgement>",
                          spellchecker)
        if len(errs) > 0:
            errors.update({'acknowledgement': "<br>".join(errs)})

    if len(res[22]) > 0:
        rsrcs = res[22].strip().split("\n")
        errs = []
        for rsrc in rsrcs:
            parts = rsrc.split("[!]")
            try:
                response = requests.get(
                        parts[0], headers=config.linkcheck_headers)
                response.raise_for_status()
            except Exception:
                log_error(("Link check failure for '" + parts[0] + "': " +
                           str(response.status_code)),
                          source="fill_from_uncommitted_changes (B)")
                errs.append(("- broken link <i>" + parts[0] + "</i> must be "
                             "fixed or removed"))

        if len(errs) > 0:
            errors.update({'related_resources': "<br>".join(errs)})

    if len(res[23]) > 0:
        rel_dois = res[23].strip().split("\n")
        errs = []
        for rel_doi in rel_dois:
            parts = rel_doi.split("[!]")
            test = "https://doi.org/" + parts[0] + "?noredirect"
            try:
                response = requests.get(test, headers=config.linkcheck_headers)
                response.raise_for_status()
            except Exception:
                log_error(("Link check failure for '" + test + "': " +
                           str(response.status_code)),
                          source="fill_from_uncommitted_changes (C)")
                errs.append(("- unresolvable DOI <b>" + parts[0] + "</b> must "
                             "be fixed or removed"))

            if len(errs) > 0:
                errors.update({'related_dois': "<br>".join(errs)})

    if len(res[24]) > 0:
        rel_dsids = res[24].strip().split("\n")
        errs = []
        for rel_dsid in rel_dsids:
            try:
                cursor.execute(("select type from search.datasets where dsid "
                                "= %s"), (rel_dsid, ))
                lres = cursor.fetchone()
                if lres is None or lres[0] not in ('P', 'H'):
                    errs.append(rel_dsid)

            except psycopg2.Error as err:
                log_error(err, source="fill_from_uncommitted_changes")
                return ({
                        'error': ("unable to verify related datasets: '{}'")
                        .format(err)}, )

            if len(errs) > 0:
                errors.update({
                        'related_datasets': (
                                "References to non-primary and non-historical "
                                "datasets must be removed:<br>" + "<br>")
                        .join(errs)})

    if res[28] == "Y":
        try:
            cursor.execute((
                    "select periods, temporal_frequencys, data_types, "
                    "formats, ascii_url, binary_url, varlist, levels, "
                    "coverages from metautil.cmd where dsid = %s"), (dsid, ))
            res = cursor.fetchone()
        except Exception as err:
            log_error(err, source="fill_from_uncommitted_changes")
            return ({'error': ("database error while getting uncommitted "
                               "content metadata changes: '{}'")
                     .format(err)}, )

        d = {}
        d.update({
            'temporal_periods': res[0],
            'temporal_frequencies': res[1],
            'data_types': res[2],
            'data_formats': res[3]})
        if res[4] is not None and len(res[4]) > 0:
            d.update({'ascii_url': res[4]})

        if res[5] is not None and len(res[5]) > 0:
            d.update({'binary_url': res[5]})

        if len(res[6]) > 0:
            errs = check_varlist(res[6].strip().split("\n"))
            if len(errs) > 0:
                errors.update({'varlist': "<br>".join(errs)})

        d.update({'variables': res[6], 'levels': res[7], 'coverages': res[8]})
        page_vars.update({'manual_cmd': d})

    return (page_vars, errors)


def get_curation_options(root, ns):
    elist = root.findall(("./xsd:simpleType[@name='datasetCurationLevel']/xsd:"
                          "restriction/xsd:enumeration"), ns)
    clevels = []
    for e in elist:
        clevels.append({
            'value': e.get("value"),
            'description': e.find("xsd:annotation/xsd:documentation",
                                  ns).text})

    return clevels


def get_license_options():
    licenses = []
    try:
        conn = psycopg2.connect(**settings.RDADB['wagtail2_config_pg'])
        cursor = conn.cursor()
        cursor.execute("select id, name from wagtail.home_datalicense")
        res = cursor.fetchall()
        for e in res:
            licenses.append({'value': e[0], 'title': e[1]})
        cursor.close()
        conn.close()
    except Exception as err:
        log_error(err, source="get_license_options")

    return licenses


def get_update_frequency_options(root, ns):
    elist = root.findall((
            "./xsd:element[@name='continuingUpdate']/xsd:complexType/xsd:"
            "attribute[@name='frequency']/xsd:simpleType/xsd:restriction/xsd:"
            "enumeration"), ns)
    ufrequencies = []
    for e in elist:
        ufrequencies.append({
            'value': "yes<!>" + e.get("value"),
            'description': "yes: " + e.get("value")})

    return ufrequencies


def get_dataset_type_options(root, ns, has_doi):
    elist = root.findall(("./xsd:simpleType[@name='datasetType']/xsd:"
                          "restriction/xsd:enumeration"), ns)
    types = []
    for e in elist:
        v = e.get("value")
        if v != "internal" or not has_doi:
            types.append({
                'value': v,
                'description': e.find(
                        "xsd:annotation/xsd:documentation", ns).text})

    return types


def get_data_format_options():
    formats = []
    try:
        tree = ElementTree.parse((root_dirs['web'] +
                                  "/metadata/schemas/common.xsd"))
        root = tree.getroot()
        ns = {
            'xsd': "http://www.w3.org/2001/XMLSchema",
        }
        elist = root.findall(("./xsd:simpleType[@name='formatList']/xsd:"
                              "restriction/xsd:enumeration"), ns)
        for e in elist:
            formats.append({'value': e.get("value")})

    except Exception as err:
        log_error(err, source="get_data_format_options")

    return formats


def get_manual_cmd_values(root):
    d = {
        'temporal_periods': "",
        'temporal_frequencies': "",
        'data_types': "",
        'ascii_url': "",
        'binary_url': "",
        'data_formats': "",
        'variables': "",
        'levels': "",
        'coverages': "",
    }
    root = root.find("contentMetadata")
    if root is None:
        return d

    elist = root.findall("temporal")
    periods = []
    for e in elist:
        group_id = e.get("groupID")
        if group_id is None:
            group_id = "Entire Dataset"

        parts = [e.get("start"), e.get("end"), group_id]
        if e.get("type") is not None:
            parts.append(e.get("type"))

        periods.append("[!]".join(parts))

    d['temporal_periods'] = "\n".join(periods)
    elist = root.findall("temporalFrequency")
    frequencies = []
    for e in elist:
        freq_type = [e.get("type")]
        if freq_type[0] == "irregular" or freq_type[0] == "climatology":
            freq_type.append(e.get("unit"))
        elif freq_type[0] == "regular":
            freq_type.extend([e.get("number"), e.get("unit")])
            stats = e.get("statistics")
            if stats is not None:
                freq_type.append(stats)

        frequencies.append("[!]".join(freq_type))

    d['temporal_frequencies'] = "\n".join(frequencies)
    elist = root.findall("dataType")
    data_types = []
    for e in elist:
        data_type = e.text
        if data_type == "grids" or data_type == "platform_observations":
            data_type = data_type[:-1]

        process = e.get("process")
        if process is not None:
            data_type += "[!]" + process

        data_types.append(data_type)

    d['data_types'] = "\n".join(data_types)
    elist = root.findall("format")
    formats = []
    for e in elist:
        fmt = e.text
        if fmt == "proprietary_ASCII":
            d['ascii_url'] = e.get("href")
        elif fmt == "proprietary_Binary":
            d['binary_url'] = e.get("href")

        formats.append(fmt)

    d['data_formats'] = "\n".join(formats)
    elist = root.findall("detailedVariables/detailedVariable")
    variables = []
    for e in elist:
        var = e.text
        units = e.get("units")
        if units is not None:
            var += "::" + units

        variables.append(var)

    d['variables'] = "\n".join(variables)
    levels = []
    elist = root.findall("levels/level")
    for e in elist:
        levels.append("[!]".join([e.get("type"), e.get("value"),
                                  (e.get("units") or "")]))

    elist = root.findall("levels/layer")
    for e in elist:
        levels.append("[!]".join([e.get("type"), e.get("top"), e.get("bottom"),
                                  e.get("units")]))

    d['levels'] = "\n".join(levels)
    elist = root.findall("geospatialCoverage/grid")
    coverages = []
    for e in elist:
        c = []
        c.extend([e.get("definition"), e.get("numX"), e.get("numY"),
                  e.get("startLon"), e.get("startLat")])
        if c[0] == "gaussLatLon":
            c.extend([e.get("endLon"), e.get("endLat"), e.get("xRes")])
            circles = e.get("circles")
            if circles is None:
                c.append(str(int(e.get("numY")) / 2))
            else:
                c.append(circles)

        elif c[0] == "lambertConformal":
            c.extend([e.get("projLon"), e.get("resLat"), e.get("xRes"),
                      e.get("yRes"), e.get("pole"), e.get("stdParallel1"),
                      e.get("stdParallel2")])
        elif c[0] == "latLon":
            c.extend([e.get("endLon"), e.get("endLat"), e.get("xRes"),
                      e.get("yRes")])
            cell = e.get("isCell")
            if cell is not None and cell == "true":
                c.append("cell")

        elif c[0] == "mercator":
            c.extend([e.get("endLon"), e.get("endLat"), e.get("xRes"),
                      e.get("yRes"), e.get("resLat")])
        elif c[0] == "polarStereographic":
            c.extend([e.get("projLon"), e.get("xRes"), e.get("yRes"),
                      e.get("pole")])
            extent = e.get("extent")
            if extent is not None:
                c.append(extent)

        coverages.append("[!]".join(c))

    d['coverages'] = "\n".join(coverages)
    return d


def help(request, help_type):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    return render(request, "metaman/datasets/help/" + help_type + ".html", {})


def check_related_datasets(ds_list, cursor):
    errs = []
    for ds in ds_list:
        try:
            cursor.execute("select type from search.datasets where dsid = %s",
                           (ds, ))
            res = cursor.fetchone()
            if res is None or res[0] not in ('P', 'H'):
                errs.append(ds)

        except psycopg2.Error as err:
            log_error(err, source="check_related_datasets")
            return ({'error': ("unable to verify related datasets: '{}'")
                     .format(err)}, )

    return errs


def check_related_dois(doi_list):
    errs = []
    for doi in doi_list:
        parts = doi.split("[!]")
        test = "https://doi.org/" + parts[0] + "?noredirect"
        try:
            response = requests.get(test, headers=config.linkcheck_headers)
            response.raise_for_status()
        except Exception:
            log_error(("Link check failure for '" + test + "': " +
                       str(response.status_code)),
                      source="check_related_dois")
            errs.append(("- Unresolvable DOI <b>" + parts[0] + "</b> must be "
                         "fixed or removed"))

    return errs


def check_related_sites(site_list):
    errs = []
    for site in site_list:
        parts = site.split("[!]")
        url = parts[0]
        if url.find("doi.org"):
            url += "?noredirect"

        try:
            response = requests.get(
                    url, headers=config.linkcheck_headers, timeout=10)
            response.raise_for_status()
        except Exception as err:
            log_error("Link check failure for '" + parts[0] + "': " + str(err),
                      source="check_related_sites")
            errs.append(("- Unresolvable URL <i>" + parts[0] + "</i> must be "
                         "fixed or removed"))

    return errs


def check_references(ref_list):
    errs = []
    ref_num = 1
    auth_err = False
    for ref in ref_list:
        parts = ref.split("[!]")
        del parts[0]
        # check author list for non-ASCII characters
        err = utils.check_for_bad_characters(parts[0])
        if len(err) > 0:
            errs.append((
                    "- reference #" + str(ref_num) + " author list: " + err))
            auth_err = True

        del parts[0]
        found_ds_rel = False
        for part in parts:
            if part[0:4] == "url:":
                url = part[4:]
                if url.find("doi.org") > 0:
                    url += "?noredirect"

                try:
                    response = requests.get(
                            url, headers=config.linkcheck_headers, timeout=10)
                    response.raise_for_status()
                except Exception as err:
                    log_error(("Link check failure for '" + part[4:] + "': "
                               + str(err)), source="check_references")
                    errs.append(("- Unresolvable URL <i>" + part[4:] + "</i> "
                                 "must be fixed or removed"))

            elif part[0:7] == "ds_rel:":
                found_ds_rel = True

        if not found_ds_rel:
            errs.append(("- reference #" + str(ref_num) + " must have a "
                         "specified relationship to the dataset"))

        ref_num += 1

    if auth_err:
        errs.append((
                "<br>NOTE: non-text characters in an author list can be the "
                "result of cut-and-paste, and are usually hyphens and quotes, "
                "which you will need to delete and then reinsert with the "
                "keyboard."))

    return errs


def check_title(title, spellchecker):
    errs = ""
    spellchecker.check(title)
    if len(spellchecker.misspelled_words) > 0:
        errs = ("- Misspelled/unrecognized word(s) must be corrected:<br><i>"
                + ", ".join(spellchecker.misspelled_words) + "</i>")

    return errs


def check_contributors(dsid, cursor):
    cursor.execute("select authors from metautil.metaman where dsid = %s",
                   (dsid, ))
    res = cursor.fetchall()
    if len(res[0][0]) == 0:
        commit_fields['contributors']['is_datacite'] = True


def check_varlist(varlist):
    for var in varlist:
        if len(var) == 0:
            return ["Blank line(s) must be removed"]

    return []


commit_fields = {
    'access_code': {
        'db_table': "metaman",
        'db_column': "access_code",
        'is_datacite': False,
        'is_required': False,
    },
    'access_restrictions': {
        'checker': check_html,
        'db_table': "metaman",
        'db_column': "access_restrictions",
        'is_datacite': False,
        'is_required': False,
    },
    'acknowledgement': {
        'checker': check_html,
        'db_table': "metaman",
        'db_column': "acknowledgement",
        'is_datacite': False,
        'is_required': False,
    },
    'authors': {
        'db_table': "metaman",
        'db_column': "authors",
        'is_datacite': True,
        'is_required': False,
    },
    'contacts': {
        'db_table': "metaman",
        'db_column': "contacts",
        'is_datacite': False,
        'is_required': True,
    },
    'contributors': {
        'checker': check_contributors,
        'db_table': "metaman",
        'db_column': "contributors",
        'is_datacite': False,
        'is_required': True,
    },
    'coverages': {
        'db_table': "cmd",
        'db_column': "coverages",
        'is_datacite': False,
        'is_required': False,
    },
    'data_types': {
        'db_table': "cmd",
        'db_column': "data_types",
        'is_datacite': False,
        'is_required': True,
    },
    'ds_curation': {
        'db_table': "metaman",
        'db_column': "ds_curation",
        'is_datacite': False,
        'is_required': True,
    },
    'ds_type': {
        'db_table': "metaman",
        'db_column': "ds_type",
        'is_datacite': False,
        'is_required': True,
    },
    'formats': {
        'db_table': "cmd",
        'db_column': "formats",
        'is_datacite': True,
        'is_required': True,
    },
    'instruments': {
        'db_table': "metaman",
        'db_column': "instruments",
        'is_datacite': False,
        'is_required': False,
    },
    'iso_topic': {
        'db_table': "metaman",
        'db_column': "iso_topic",
        'is_datacite': False,
        'is_required': True,
    },
    'levels': {
        'db_table': "cmd",
        'db_column': "levels",
        'is_datacite': False,
        'is_required': False,
    },
    'license': {
        'db_table': "metaman",
        'db_column': "license",
        'is_datacite': False,
        'is_required': True,
    },
    'logo': {
        'db_table': "metaman",
        'db_column': "logo",
        'is_datacite': False,
        'is_required': False,
    },
    'periods': {
        'db_table': "cmd",
        'db_column': "periods",
        'is_datacite': False,
        'is_required': True,
    },
    'platforms': {
        'db_table': "metaman",
        'db_column': "platforms",
        'is_datacite': False,
        'is_required': True,
    },
    'projects': {
        'db_table': "metaman",
        'db_column': "projects",
        'is_datacite': False,
        'is_required': False,
    },
    'redundancys': {
        'db_table': "metaman",
        'db_column': "redundancys",
        'is_datacite': False,
        'is_required': True,
    },
    'references': {
        'checker': check_references,
        'db_table': "metaman",
        'db_column': "_references",
        'is_datacite': False,
        'is_required': False,
    },
    'reflists': {
        'db_table': "metaman",
        'db_column': "reflists",
        'is_datacite': False,
        'is_required': False,
    },
    'related_datasets': {
        'checker': check_related_datasets,
        'db_table': "metaman",
        'db_column': "related_datasets",
        'is_datacite': False,
        'is_required': False,
    },
    'related_dois': {
        'checker': check_related_dois,
        'db_table': "metaman",
        'db_column': "related_dois",
        'is_datacite': True,
        'is_required': False,
    },
    'related_sites': {
        'checker': check_related_sites,
        'db_table': "metaman",
        'db_column': "related_resources",
        'is_datacite': False,
        'is_required': False,
    },
    'sciencekeywords': {
        'db_table': "metaman",
        'db_column': "variables",
        'is_datacite': True,
        'is_required': True,
    },
    'supports_projects': {
        'db_table': "metaman",
        'db_column': "supports_projects",
        'is_datacite': False,
        'is_required': False,
    },
    'summary': {
        'checker': check_html,
        'db_table': "metaman",
        'db_column': "summary",
        'is_datacite': True,
        'is_required': True,
    },
    'temporal_frequencys': {
        'db_table': "cmd",
        'db_column': "temporal_frequencys",
        'is_datacite': False,
        'is_required': False,
    },
    'title': {
        'checker': check_title,
        'db_table': "metaman",
        'db_column': "title",
        'is_datacite': True,
        'is_required': True,
    },
    'update_frequency': {
        'db_table': "metaman",
        'db_column': "update_frequency",
        'is_datacite': False,
        'is_required': False,
    },
    'usage_restrictions': {
        'checker': check_html,
        'db_table': "metaman",
        'db_column': "usage_restrictions",
        'is_datacite': False,
        'is_required': False,
    },
    'varlist': {
        'checker': check_varlist,
        'db_table': "cmd",
        'db_column': "varlist",
        'is_datacite': False,
        'is_required': False,
    },
}
