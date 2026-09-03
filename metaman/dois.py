import json
import os
import psycopg2
import requests
import smtplib
import subprocess

from datetime import datetime
from doi_manager import local_settings as doi_manager_settings
from dsspellchecker import SpellChecker
from email.message import EmailMessage
from libpkg.metautils import open_dataset_overview

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from lxml import etree

from .config import (bin_utils,
                     doi_manager,
                     linkcheck_headers,
                     metadata_managers,
                     root_dirs)
from .utils import check_html, get_iuser, log_error, set_wfile_version
from gdexwebserver.utils import make_tempdir, remove_tempdir


def dataset_has_data_files(dsid, cursor):
    cursor.execute(
            "select dwebcnt from dssdb.dataset where dsid = %s", (dsid, ))
    res = cursor.fetchall()
    if len(res) == 0 or len(res[0]) == 0 or res[0][0] == 0:
        return False

    return True


def adopt(request, dsid):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    iuser = get_iuser(request)
    if len(iuser) == 0:
        return render(request, "500.html")

    d = {'dsid': dsid,
         'resolution_domain': doi_manager_settings.resolution_domain}
    try:
        conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
        if not dataset_has_data_files(dsid, cursor):
            d.update({'error': ("The dataset does not have any data files, "
                                "so a DOI cannot be adopted.")})
            return render(request, "metaman/dois/adopt.html", {'data': d})

        if 'vdoi' not in request.POST:
            return render(request, "metaman/dois/adopt.html", {'data': d})

        if 'res_url' in request.POST:
            if (request.POST['res_url'][0:26] != "https://icarus.ucdavis.edu"):
                d.update({'error':
                          ("The resolution URL provided is not an approved "
                           "URL")})
                return render(request, "metaman/dois/adopt.html", {'data': d})

            try:
                response = requests.get(request.POST['res_url'],
                                        headers=linkcheck_headers)
                if response.status_code != 403:
                    response.raise_for_status()

            except Exception:
                d.update({'error':
                          ("The resolution URL provided is invalid or cannot "
                           "be reached")})
                return render(request, "metaman/dois/adopt.html", {'data': d})

        r = requests.get((
                "https://api.datacite.org/dois/" + request.POST['vdoi']))
        o = json.loads(r.text)
        if 'data' not in o or 'id' not in o['data']:
            d.update({'verified': False})
            return render(request, "metaman/dois/adopt.html", {'data': d})

        d.update({'verified': True})
        cursor.execute((
                "select * from dssdb.dsvrsn where doi ilike '" +
                request.POST['vdoi'] + "'"))
        res = cursor.fetchall()
        if len(res) > 0:
            d.update({'usable': False})
            return render(request, "metaman/dois/adopt.html", {'data': d})

        d.update({'usable': True})
        pub_year = None
        if 'attributes' in o['data']:
            if 'url' in o['data']['attributes']:
                url = o['data']['attributes']['url']
                if url.find("gdex.ucar.edu") > 0:
                    url = url.replace(".html", ".xml?type=iso19139")
                elif url.find("icarus.ucdavis.edu") > 0:
                    idx = url.rfind("/")
                    url = ("https://gdex.ucar.edu/dataset/icarus.experiment." +
                           url[idx+1:] + ".xml?type=iso19139")
                else:
                    url = None

            if 'publicationYear' in o['data']['attributes']:
                pub_year = o['data']['attributes']['publicationYear']

        pub_date = None
        if url is not None:
            try:
                response = requests.get(url)
                root = etree.fromstring(response.content)
                dates = root.xpath((
                        "//gmd:identificationInfo/gmd:MD_DataIdentification/"
                        "gmd:citation/gmd:CI_Citation/gmd:date"),
                        namespaces=root.nsmap)
                for date in dates:
                    date_type = date.xpath(
                            "gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode",
                            namespaces=root.nsmap)[0].text
                    if date_type == "publication":
                        pub_date = date.xpath("gmd:CI_Date/gmd:date/gco:Date",
                                              namespaces=root.nsmap)[0].text

            except Exception:
                url = None

        if pub_date is None:
            if pub_year is None:
                d.update({'error':
                          ("The original publication date for the DOI could "
                           "not be determined")})
                return render(request, "metaman/dois/adopt.html", {'data': d})
            else:
                pub_date = str(pub_year) + "-01-01"

        try:
            tdir_name = make_tempdir()
            env = {'TMPDIR': "/data/ptmp"}
            subprocess.run((
                    bin_utils['cvs'] + " -Q -d " + root_dirs['cvs'] +
                    " checkout -d " + tdir_name + " datasets/" + dsid +
                    ".xml"), shell=True, env=env)
            root = etree.parse(os.path.join(tdir_name, dsid + ".xml"))
            root.find("./publicationDate").text = pub_date
            with open(os.path.join(tdir_name, dsid + ".xml"), "w") as f:
                f.write("<?xml version=\"1.0\" ?>\n")
                f.write(etree.tostring(root).decode("utf-8"))

            o = subprocess.run((
                bin_utils['cvs'] + " -d " + root_dirs['cvs'] + " commit -m \""
                + iuser + ": update pub_date to original\" " +
                os.path.join(tdir_name, dsid + ".xml")),
                shell=True, env=env, stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE)
            if o.stderr:
                d.update({
                    'error': ("The publication date could not be saved by "
                              "cvs: '{}'").format(
                              o.stderr.decode("utf-8"))})
                return render(request, "metaman/dois/adopt.html", {'data': d})

            cursor.execute((
                    "update search.datasets set pub_date = %s where dsid = "
                    "%s"), (pub_date, dsid))
            conn.commit()
        except Exception as err:
            err = "An error occurred: {}".format(err)
            log_error(err, source="adopt")
            d.update({'error': err})
            return render(request, "metaman/dois/adopt.html", {'data': d})
        finally:
            remove_tempdir(tdir_name)

        try:
            set_wfile_version(dsid, request.POST['vdoi'], conn)
        except psycopg2.Error as err:
            err = "Database error: '{}'".format(err)
            log_error(err, source="adopt")
            d.update({'error': err})
            return render(request, "metaman/dois/adopt.html", {'data': d})

        try:
            if 'res_url' in request.POST:
                cursor.execute((
                        "insert into metautil.doi_registration values "
                        "(%s, %s)"),
                        (request.POST['vdoi'], request.POST['res_url']))
                conn.commit()

            doi_command = (
                    doi_manager['invoke_command'] + " " +
                    doi_manager['auth_key'] + " update " +
                    request.POST['vdoi'] + "==" + dsid)
            o = subprocess.run(doi_command, capture_output=True, shell=True)
            if o.stderr:
                d.update({'error': (
                        "An error occured and the DataCite metadata was not "
                        "updated: {}").format(o.stderr.decode("utf-8"))})
                return render(request, "metaman/dois/adopt.html", {'data': d})
            else:
                d.update({'vdoi': request.POST['vdoi']})

        except Exception as err:
            err = ("An error occured and the DataCite metadata was not "
                   "updated: {}").format(err)
            log_error(err, source="adopt")
            d.update({'error': err})
            return render(request, "metaman/dois/adopt.html", {'data': d})

        o = subprocess.run((
                "dsgen --mdb='" +
                json.dumps(settings.RDADB['metadata_config_pg']) + "' " +
                "--wdb='" +
                json.dumps(settings.RDADB['wagtail2_config_pg']) + "' " +
                dsid),
                shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if o.stderr:
            err = "dsgen failure: {}".format(o.stderr.decode("utf-8"))
            log_error(err, source="adopt")
            d.update({'error': err})
            return render(request, "metaman/dois/adopt.html", {'data': d})

        with open("/data/logs/doi_log", "a") as f:
            f.write((
                    "DOI adopted: {} - dsid: {}, specialist: {}\n")
                    .format(request.POST['vdoi'], dsid, iuser))

        smtp = smtplib.SMTP('localhost')
        msg = EmailMessage()
        msg['From'] = "rdadata@ucar.edu"
        msg['To'] = "decs-info@ucar.edu"
        msg['Subject'] = "DOI for " + dsid
        msg.set_content((
                "A DOI ({doi}) has been adopted and assigned to dataset "
                "{dsid} by {iuser}.\n\nYou can view the DOI registration at "
                "our DOI registration and management service: "
                "https://commons.datacite.org/doi.org/{doi}").format(
                        doi=request.POST['vdoi'],
                        dsid=dsid,
                        iuser=iuser))
        smtp.send_message(msg)
        smtp.quit()

    except psycopg2.Error as err:
        d.update({'error': "Database error: {}".format(err)})
    except Exception as err:
        d.update({'error': "An error occurred: {}".format(err)})
    finally:
        conn.close()

    return render(request, "metaman/dois/adopt.html", {'data': d})


def validate_dataset(dsid):
    errors = []
    try:
        mconn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        mcursor = mconn.cursor()
        wconn = psycopg2.connect(**settings.RDADB['wagtail2_config_pg'])
        wcursor = wconn.cursor()
        if not dataset_has_data_files(dsid, mcursor):
            errors.append((
                    "The dataset does not have any data files, so a DOI "
                    "cannot be assigned."))

        # make sure named specialists are active
        mcursor.execute((
                "select specialist from dssdb.dsowner where dsid = %s order "
                "by priority"), (dsid, ))
        res = mcursor.fetchall()
        for spec in res:
            mcursor.execute((
                    "select logname from dssdb.dssgrp where logname = %s and "
                    "stat_flag = 'C'"), (spec[0], ))
            sres = mcursor.fetchall()
            if len(sres) != 1:
                errors.append("<b>Dataset Specialist</b>: '{}' is inactive or "
                              "unknown".format(spec[0]))

        mcursor.execute((
                "select title, summary, curation_level, has_redundancy from "
                "search.datasets where dsid = %s"), (dsid, ))
        ttl, summ, cur_lev, redun = mcursor.fetchone()
        # make sure curation level has been set
        if len(cur_lev) == 0:
            errors.append("<b>Curation Level</b>: missing, must be specified")
        elif cur_lev not in ("basic", "enhanced", "data-level"):
            errors.append(("<b>Curation Level</b>: '{}' is not a valid "
                           "selection").format(cur_lev))

        # make sure a dataset redundancy option has been chosen
        if redun == "U":
            errors.append(("<b>Dataset Redundancies</b>: This dataset has not "
                           "been marked 'yes' or 'no' as having one or more "
                           "redundant copies"))
        elif redun == "Y":
            mcursor.execute((
                    "select count(*) from search.dataset_redundancy where "
                    "dsid = %s"), (dsid, ))
            res = mcursor.fetchone()
            if res[0] == "0":
                errors.append((
                        "<b>Dataset Redundancies</b>: This dataset is marked "
                        "as having one or more redundant copies, but no "
                        "redundancies are specified"))

        xml_root = open_dataset_overview(dsid)
        references = xml_root.findall("./reference")
        sc = SpellChecker()
        if not sc.ready:
            errors.append(("<b>System</b>: The spellchecker is not ready for "
                           "use."))
        else:
            # check the title and summary for misspelled words
            sc.check(ttl)
            if len(sc.misspelled_words) > 0:
                errors.append(("<b>Title</b>: Misspelled words must be "
                               "corrected: " + ", ".join(sc.misspelled_words)))

            summ_errs = check_html("<summary>" + summ + "</summary>", sc)
            if len(summ_errs) > 0:
                errors.extend([("<b>Summary/Abstract</b>: " + e)
                               for e in summ_errs])

            this_year = datetime.now().year
            for reference in references:
                author_list = reference.find("./authorList").text
                # check for misspellings in publication titles
                ttl = reference.find("./title").text
                sc.check(ttl)
                if len(sc.misspelled_words) > 0:
                    errors.append((
                            "<b>Publication References</b>: Misspelled words "
                            " in the title of (" + author_list + ") must be "
                            "corrected: " + ", ".join(sc.misspelled_words)))

                # check for incomplete references (e.g., submitted, in review)
                incomplete = False
                e = reference.find("./periodical")
                if e is not None:
                    if e.get("number") == "0" or e.get("pages") == "0-0":
                        incomplete = True
                else:
                    e = reference.find("./book")
                    if e is not None:
                        if e.get("pages") == "0-0":
                            incomplete = True

                if (incomplete and (this_year -
                                    int(reference.find("./year").text)) > 1):
                    errors.append((
                            "<b>Publication References</b>: Incomplete "
                            "reference (" + author_list + ") marked as "
                            "'submitted', 'accepted', etc. must be updated"))

        # check for broken links in related resources
        wcursor.execute((
                "select related_rsrc_list from wagtail2."
                "dataset_description_datasetdescriptionpage where dsid = %s"),
                (dsid, ))
        rsrcs = wcursor.fetchone()
        if rsrcs is not None:
            for rsrc in rsrcs[0]:
                try:
                    response = requests.get(
                            rsrc['url'], headers=linkcheck_headers)
                    if response.status_code != 403:
                        response.raise_for_status()

                except Exception:
                    errors.append((
                            "<b>Related Websites</b>: Unresolvable URL <i>" +
                            rsrc['url'] + "</i> (" + str(response.status_code)
                            + ") must be fixed or removed"))

    except psycopg2.Error as err:
        errors.append(str(err))
    finally:
        mconn.close()
        wconn.close()

    return errors


def assign(request, dsid):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    iuser = get_iuser(request)
    if len(iuser) == 0:
        return render(request, "500.html")

    ctx = {'dsid': dsid, 'action': "assign"}
    if 'passedTest' in request.POST and request.POST['passedTest'] == "true":
        if len(request.POST['adoi']) == 0:
            # 'adoi' could already be 'X' if the assignment process failed
            #   partway through on a previous attempt
            try:
                conn = psycopg2.connect(**settings.RDADB['dssdb_config_pg'])
                set_wfile_version(dsid, "X", conn)
            except psycopg2.Error as err:
                ctx.update({'error': "Database error '{}'".format(err)})
                return render(request, "metaman/dois/doi_msg.html", ctx)
            finally:
                conn.close()

        ctx = create_a_real_doi(request, dsid, iuser, ctx)
        return render(request, "metaman/dois/doi_msg.html", ctx)

    ctx.update(create_a_test_doi(dsid, "assign"))
    return render(request, "metaman/dois/doi_test.html", ctx)


def supersede(request, dsid):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    iuser = get_iuser(request)
    if len(iuser) == 0:
        return render(request, "500.html")

    ctx = {'dsid': dsid, 'action': "supersede"}
    if 'saveMessage' in request.POST and request.POST['saveMessage'] == "true":
        errs = check_html("<msg>" + request.POST['message'] + "</msg>",
                          SpellChecker())
        words = request.POST['message'].split()
        if len(words) < 10:
            errs.append(("The reason for superseding the DOI <b>MUST</b> "
                         "contain at least ten words."))

        if len(errs) == 0:
            try:
                conn = psycopg2.connect(**settings.RDADB['dssdb_config_pg'])
                cursor = conn.cursor()
                cursor.execute((
                        "update dssdb.dsvrsn set note = %s where dsid = %s "
                        "and doi = %s"),
                        (request.POST['message'], dsid, request.POST['adoi']))
                if cursor.rowcount != 1:
                    raise psycopg2.Error((
                            "Incorrect row count for update: '{}'")
                            .format(cursor.rowcount))

                conn.commit()
            except psycopg2.Error as err:
                errs.append("database error: '{}'".format(err))

        if len(errs) > 0:
            return HttpResponse((
                    '<img src="/images/x.gif" width="16" height="16">&nbsp;'
                    'The following errors were identified:<ul>{}</ul>')
                    .format("<br> - ".join(errs)))

        return HttpResponse("Success")
    elif 'abort' in request.POST and request.POST['abort'] == "true":
        ctx.update({'abort': True})
        try:
            conn = psycopg2.connect(**settings.RDADB['dssdb_config_pg'])
            cursor = conn.cursor()
            cursor.execute(
                    "update dssdb.dsvrsn set note = '' where dsid = %s and "
                    "doi = %s", (dsid, request.POST['adoi']))
            if cursor.rowcount != 1:
                raise psycopg2.Error(("Incorrect row count for update: '{}'")
                                     .format(cursor.rowcount))

            conn.commit()
            conn.close()
        except psycopg2.Error as err:
            errs.append("database error: '{}'".format(err))

        return render(request, "metaman/dois/doi_msg.html", ctx)
    elif 'passedTest' in request.POST and request.POST['passedTest'] == "true":
        # make a temporary DOI entry in dssdb.dsvrsn for the dataset, making
        #  sure there isn't already one from a previous failed test run
        try:
            conn = psycopg2.connect(**settings.RDADB['dssdb_config_pg'])
            cursor = conn.cursor()
            cursor.execute(
                    "select vindex from dssdb.dsvrsn where dsid = %s and doi "
                    "= 'X'", (dsid, ))
            vindex, = cursor.fetchone() or (None, )
            conn.close()
        except psycopg2.Error as err:
            ctx.update({'error': "Error while checking for temporary "
                                 f"entry: '{err}'"})
            return render(request, "metaman/dois/doi_msg.html", ctx)

        if vindex is None:
            dsarch_command = (
                    bin_utils['rdadatarun'] + " /usr/local/decs/bin/dsarch "
                    "-sv -ds " + dsid + " -nv -dn X -md")
            o = subprocess.run(dsarch_command, capture_output=True, shell=True)
            if o.stderr:
                ctx.update({'error': str(o.stderr, encoding="utf-8")})
                return render(request, "metaman/dois/doi_msg.html", ctx)

        ctx.update({'adoi': request.POST['adoi']})
        ctx = create_a_real_doi(request, dsid, iuser, ctx)
        return render(request, "metaman/dois/doi_msg.html", ctx)

    ctx.update(create_a_test_doi(dsid, "supersede"))
    return render(request, "metaman/dois/doi_test.html", ctx)


def create_a_test_doi(dsid, action):
    adoi, err = get_active_doi(dsid)
    if action == "assign":
        if len(adoi) > 0 and adoi not in ("X", "Y"):
            return {'already_active': True, 'adoi': adoi}

    elif action == "supersede":
        if len(adoi) == 0 or adoi in ("X", "Y"):
            return {'noactive': True}

    else:
        return {'error': "'{}' is not a valid action".format(action)}

    errs = validate_dataset(dsid)
    if len(errs) > 0:
        return {'validator_errors': errs}

    o = subprocess.run((
            doi_manager['invoke_command'] + " " + doi_manager['auth_key'] +
            " -t create " + dsid),
            shell=True, env={'USER': "apache", 'QUERY_STRING': "X"},
            capture_output=True)
    err = o.stderr.decode("utf-8")
    if len(err) > 0:
        return {'error': f"test DOI creation failed: '{err}'"}

    out = o.stdout.decode("utf-8")
    if out.find("Success:") == 0:
        return {'adoi': adoi}

    if o.returncode != 1:
        out = (
            out.replace("Content-type: text/plain", "")
               .replace("Error: ", "")
               .strip()
               .replace("\n", "<br>"))

    return {'error': out}


def get_active_doi(dsid):
    try:
        conn = psycopg2.connect(**settings.RDADB['dssdb_config_pg'])
        cursor = conn.cursor()
        cursor.execute((
                "select doi from dssdb.dsvrsn where dsid = %s and status = "
                "'A'"), (dsid, ))
        res = cursor.fetchall()
        if len(res) > 0:
            return (res[0][0], "")

    except psycopg2.Error as err:
        return ("", str(err))

    return ("", "")


def create_a_real_doi(request, dsid, iuser, ctx):
    try:
        conn = psycopg2.connect(**settings.RDADB['dssdb_config_pg'])
        cursor = conn.cursor()
    except psycopg2.Error as err:
        ctx['error'] = f"A database error occurred: '{err}'"
        return ctx

    with open("/data/logs/doi_log", "a") as doi_log:
        doi_log.write(
                f"Starting DOI creation at {str(datetime.now())} - dsid: "
                f"{dsid}, specialist: {iuser} ...\n")

    cursor.execute(
            "select vindex from dssdb.dsvrsn where dsid = %s and doi = 'X' "
            "and status = 'A'", (dsid, ))
    vindex, = cursor.fetchone() or (None, )
    if vindex is None:
        ctx['error'] = (
                "The database is out-of-sync and DOI creation cannot "
                "continue")
        return ctx

    cursor.execute(
            "update dssdb.dsvrsn set doi = 'Y' where dsid = %s and vindex = "
            "%s and doi = 'X' and status = 'A' returning doi", (dsid, vindex))
    temp_doi, = cursor.fetchone() or (None, )
    if temp_doi is None or temp_doi != "Y":
        conn.rollback()
        ctx['error'] = (
                "The temporary database DOI record for this dataset "
                "cannot be accessed, so DOI creation cannot continue")
        return ctx

    conn.commit()
    proc = subprocess.run((
            doi_manager['invoke_command'] + " " + doi_manager['auth_key'] +
            " create " + dsid),
            shell=True, env={'USER': "apache", 'QUERY_STRING': "X"},
            capture_output=True)
    out = proc.stdout.decode("utf-8")
    with open("/data/logs/doi_log", "a") as doi_log:
        doi_log.write(
                f"  dsid: {dsid}, specialist: {iuser}, DataCite response: "
                f"{out}, timestamp: {str(datetime.now())}\n")

    if out.find("Success:") == 0:
        lines = out.split("\n")
        parts = lines[0].split()
        ctx.update({'doi': parts[1]})
        with open("/data/logs/doi_log", "a") as doi_log:
            doi_log.write(
                    f"DOI created: {ctx['doi']} - dsid: {dsid}, specialist: "
                    f"{iuser}, timestamp: {str(datetime.now())}\n")

        smtp = smtplib.SMTP('localhost')
        msg = EmailMessage()
        msg['From'] = "rdadata@ucar.edu"
        try:
            cursor.execute(
                    "update dssdb.dsvrsn set doi = %s where dsid = %s and doi "
                    "= 'Y'", (ctx['doi'], dsid))
            if cursor.rowcount != 1:
                raise psycopg2.Error(
                        f"Incorrect row count for update: '{cursor.rowcount}'")

            conn.commit()
            parts = lines[1].split()
            ctx.update({'datacite_url': parts[4]})
            msg['To'] = "decs-info@ucar.edu"
            msg['Subject'] = "DOI for " + dsid
            msg.set_content((
                    "A {}DOI has been assigned to dataset {}{} by {}.\n\nYou "
                    "can view the DOI registration at our DOI registration "
                    "and management service: {}").format(
                            "new " if ctx['action'] == "supersede" else "",
                            dsid,
                            (", which supersedes the old DOI: " + ctx['adoi']
                             + "," if ctx['action'] == "supersede" else ""),
                            iuser,
                            ctx['datacite_url'],))
            subprocess.run((
                    "dsgen --mdb='" +
                    json.dumps(settings.RDADB['metadata_config_pg']) + "' " +
                    "--wdb='" +
                    json.dumps(settings.RDADB['wagtail2_config_pg']) + "' " +
                    ctx['dsid']), shell=True)
        except psycopg2.Error as err:
            ctx['error'] = f"A database error occurred: '{err}'"
            msg['To'] = ", ".join(m + "@ucar.edu" for m in metadata_managers)
            msg['Subject'] = "FAILED DOI for " + dsid
            msg.set_content(
                    f"A DOI ({ctx['doi']}) was minted but a database failure "
                    f"- '{err}' caused it to not be saved in dssdb.dsvrsn.")

        smtp.send_message(msg)
        smtp.quit()

    else:
        err = proc.stderr.decode("utf-8")
        if len(err) == 0:
            err = out

        with open("/data/logs/doi_log", "a") as doi_log:
            doi_log.write(
                    f"***DOI creation error: {err} - dsid: {dsid}, "
                    f"specialist: {iuser}, timestamp: {str(datetime.now())}"
                    "\n")

        ctx['error'] = (
                f"DOI creation failed: '{err}'<br><br>A DOI was <b>NOT</b> "
                "assigned to this dataset")

    conn.close()
    return ctx
