import json
import psycopg2
import requests
import smtplib
import subprocess

from datetime import datetime
from dsspellchecker import SpellChecker
from email.message import EmailMessage
from libpkg.metautils import open_dataset_overview

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render

from .config import (bin_utils,
                     doi_manager,
                     linkcheck_headers,
                     metadata_managers)
from .utils import check_html, get_iuser, log_error


def adopt(request, dsid):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

    d = {'dsid': dsid}
    if 'vdoi' in request.POST:
        r = requests.get((
                "https://api.datacite.org/dois/" + request.POST['vdoi']))
        o = json.loads(r.text)
        if 'data' in o and 'id' in o['data']:
            d.update({'verified': True})
            conn = psycopg2.connect(**settings.RDADB['dssdb_config_pg'])
            cursor = conn.cursor()
            cursor.execute((
                    "select * from dssdb.dsvrsn where doi ilike '" +
                    request.POST['vdoi'] + "'"))
            res = cursor.fetchall()
            cursor.close()
            if len(res) > 0:
                d.update({'usable': False})
            else:
                d.update({'usable': True})
                try:
                    dsarch_command = (
                            bin_utils['rdadatarun'] + " /usr/local/decs/bin/"
                            "dsarch -sv -ds " + dsid + " -nv -dn " +
                            request.POST['vdoi'] + " -md")
                    res = subprocess.run(dsarch_command, capture_output=True,
                                         shell=True)
                    if res.stderr:
                        d.update({'error': str(res.stderr, encoding='utf-8')})

                    try:
                        doi_command = (
                                doi_manager['invoke_command'] + " " +
                                doi_manager['auth_key'] + " update " +
                                request.POST['vdoi'])
                        res = subprocess.run(doi_command, capture_output=True,
                                             shell=True)
                        if res.stderr:
                            d.update({'error': str(res.stderr,
                                                   encoding='utf-8')})
                        else:
                            d.update({'vdoi': request.POST['vdoi']})

                    except Exception as err:
                        d.update({'error': ("An error occurred and 'doi' was "
                                            "not able to update the metadata "
                                            "at DataCite.")})
                        log_error(err, source="adopt")

                except Exception as err:
                    d.update({'error': ("An error occurred and 'dsarch' was "
                                        "not able to insert the DOI into the "
                                        "database.")})
                    log_error(err, source="adopt")

        else:
            d.update({'verified': False})

    return render(request, "metaman/dois/adopt.html", {'data': d})


def validate_dataset(dsid):
    errors = []
    try:
        mconn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        mcursor = mconn.cursor()
        wconn = psycopg2.connect(**settings.RDADB['wagtail2_config_pg'])
        wcursor = wconn.cursor()
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
                "select related_rsrc_list from wagtail."
                "dataset_description_datasetdescriptionpage where dsid = %s"),
                (dsid, ))
        rsrcs = wcursor.fetchone()
        if rsrcs is not None:
            for rsrc in rsrcs[0]:
                try:
                    response = requests.get(
                            rsrc['url'], headers=linkcheck_headers)
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

    ctx = {'dsid': dsid, 'action': "assign"}
    if 'passedTest' in request.POST and request.POST['passedTest'] == "true":
        if len(request.POST['adoi']) == 0:
            dsarch_command = (
                    bin_utils['rdadatarun'] + " /usr/local/decs/bin/dsarch "
                    "-sv -ds " + dsid + " -nv -dn X -md")
            o = subprocess.run(dsarch_command, capture_output=True, shell=True)
            if o.stderr:
                ctx.update({'error': str(o.stderr, encoding="utf-8")})
                return render(request, "metaman/dois/doi_msg.html", ctx)

        ctx = create_a_real_doi(request, dsid, get_iuser(request), ctx)
        return render(request, "metaman/dois/doi_msg.html", ctx)

    ctx.update(create_a_test_doi(dsid, "assign"))
    return render(request, "metaman/dois/doi_test.html", ctx)


def supersede(request, dsid):
    if 'HTTP_X_REQUESTED_WITH' not in request.META:
        return render(request, "404.html")

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
            cursor.execute((
                    "update dssdb.dsvrsn set note = '' where dsid = %s and "
                    "doi = %s"), (dsid, request.POST['adoi']))
            if cursor.rowcount != 1:
                raise psycopg2.Error(("Incorrect row count for update: '{}'")
                                     .format(cursor.rowcount))

            conn.commit()
        except psycopg2.Error as err:
            errs.append("database error: '{}'".format(err))

        return render(request, "metaman/dois/doi_msg.html", ctx)
    elif 'passedTest' in request.POST and request.POST['passedTest'] == "true":
        dsarch_command = (
                bin_utils['rdadatarun'] + " /usr/local/decs/bin/dsarch -sv "
                "-ds " + dsid + " -nv -dn X -md")
        o = subprocess.run(dsarch_command, capture_output=True, shell=True)
        if o.stderr:
            ctx.update({'error': str(o.stderr, encoding="utf-8")})
            return render(request, "metaman/dois/doi_msg.html", ctx)

        ctx.update({'adoi': request.POST['adoi']})
        ctx = create_a_real_doi(request, dsid, get_iuser(request), ctx)
        return render(request, "metaman/dois/doi_msg.html", ctx)

    ctx.update(create_a_test_doi(dsid, "supersede"))
    return render(request, "metaman/dois/doi_test.html", ctx)


def create_a_test_doi(dsid, action):
    adoi, err = get_active_doi(dsid)
    if action == "assign":
        if len(adoi) > 0 and adoi != "X":
            return {'already_active': True, 'adoi': adoi}

    elif action == "supersede":
        if len(adoi) == 0 or adoi == "X":
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
        return {'error': "test DOI creation failed: '{}'".format(err)}

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
        ctx.update({'error': "A database error occurred: '{}'".format(err)})
        return render(request, "metaman/dois/doi_msg.html", ctx)

    proc = subprocess.run((
            doi_manager['invoke_command'] + " " + doi_manager['auth_key'] +
            " create " + dsid),
            shell=True, env={'USER': "apache", 'QUERY_STRING': "X"},
            capture_output=True)
    out = proc.stdout.decode("utf-8")
    if out.find("Success:") == 0:
        lines = out.split("\n")
        parts = lines[0].split()
        ctx.update({'doi': parts[1]})
        smtp = smtplib.SMTP('localhost')
        msg = EmailMessage()
        msg['From'] = "rdadata@ucar.edu"
        try:
            cursor.execute((
                    "update dssdb.dsvrsn set doi = %s where dsid = %s and doi "
                    "= 'X'"), (ctx['doi'], dsid))
            if cursor.rowcount != 1:
                raise psycopg2.Error(("Incorrect row count for update: '{}'")
                                     .format(cursor.rowcount))

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
                    bin_utils['rdadatarun'] + " /usr/local/decs/bin/dsgen " +
                    dsid),
                    shell=True, env={'USER': "apache"})
        except psycopg2.Error as err:
            ctx.update({'error': ("A database error occurred: '{}'")
                       .format(err)})
            msg['To'] = ", ".join(m + "@ucar.edu" for m in metadata_managers)
            msg['Subject'] = "FAILED DOI for " + dsid
            msg.set_content(("A DOI (" + ctx['doi'] + ") was minted but a "
                             "database failure - '{}' caused it to not be "
                             "saved in dssdb.dsvrsn.").format(err))

        smtp.send_message(msg)
        smtp.quit()

    else:
        err = proc.stderr.decode("utf-8")
        ctx.update({'error': ("DOI creation failed: '{}'<br><br>A DOI was <b>"
                              "NOT</b> assigned to this dataset").format(err)})

    conn.close()
    return ctx
