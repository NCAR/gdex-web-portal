import os
import psycopg2
import pytz
import re

from datetime import datetime, timedelta
from dateutil import tz
from django.conf import settings as django_settings
from django.shortcuts import render

from libpkg.metaformats import (dublin_core, datacite_4, fgdc, gcmd_dif,
                                iso_19115_3, iso_19139, native)
from libpkg.metaformats import settings as metaformat_settings
from libpkg.strutils import strand
from wagtail.core.models import Page

from .models import MetadataFormatsPage


def error(request, errors, **kwargs):
    ctx = {'errors': errors}
    if 'verb' in kwargs:
        ctx.update({'verb': kwargs['verb']})

    return render(request, "oai/error.xml",
                  context=ctx, content_type="text/xml")


def check_args(oai_args, repo_identifier):
    errors = []
    for arg, vals in oai_args:
        if len(vals) > 1:
            errors.append({'code': "badArgument",
                           'message': "'" + arg + "' must not be repeated"})

        if arg == "identifier":
            if (re.compile("^oai:" + repo_identifier + r":d\d{6}$")
                    .match(vals[0]) is None):
                errors.append({'code': "badArgument",
                               'message': ("'" + arg + "' is not a valid "
                                           "identifier")})

        if arg == "metadataPrefix":
            qs = Page.objects.type(MetadataFormatsPage)
            prefixes = {f.value['prefix'] for f in
                        qs[0].specific.metadata_formats}
            if vals[0] not in prefixes:
                errors.append({'code': "cannotDisseminateFormat",
                               'message': ("'" + vals[0] + "' is not a "
                                           "supported metadata format")})

    return errors


def bad_args(request, args, **kwargs):
    errors = []
    for arg in args:
        errors.append({'code': "badArgument",
                       'message': "'" + arg[0] + "' is not allowed here"})
    if 'verb' in kwargs:
        return error(request, errors, verb=kwargs['verb'])

    return error(request, errors)


def build_list(oai_args):
    errors = []
    from_ = None
    until = None
    for arg, vals in oai_args:
        if arg == "from":
            from_ = vals[0]
        elif arg == "until":
            until = vals[0]
        elif arg == "metadataPrefix":
            pass
        elif arg == "set":
            errors.append(
                    {'code': "noSetHierarchy",
                     'message': "This repository does not support sets"})
        elif arg == "resumptionToken":
            errors.append(
                    {'code': "badResumptionToken",
                     'message': ("This repository does not support "
                                 "resumption tokens")})
        else:
            errors.append(
                    {'code': "badArgument",
                     'message': "'" + arg + "' is an illegal argument"})

    if len(errors) > 0:
        return ([], errors)

    try:
        tstamp = None
        conn = psycopg2.connect(**django_settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        q = ("select dsid, timestamp_utc from search.datasets where type in "
             "('P', 'H') and dsid < 'd999000'")
        params = []
        if from_ is not None:
            if tstamp is None:
                tstamp = re.compile((r"^\d{4}-\d{2}-\d{2}"
                                     r"(T\d{2}:\d{2}:\d{2}Z){0,1}$"))

            if tstamp.match(from_) is None:
                errors.append({'code': "badArgument",
                               'message': "Invalid granularity for 'from'"})

            q += " and timestamp_utc >= %s"
            if len(from_) == 20:
                from_ = from_.replace("T", " ")[0:-1]

            params.append(from_)

        if until is not None:
            if tstamp is None:
                tstamp = re.compile((r"^\d{4}-\d{2}-\d{2}"
                                     r"(T\d{2}:\d{2}:\d{2}Z){0,1}$"))

            if tstamp.match(until) is None:
                errors.append({'code': "badArgument",
                               'message': "Invalid granularity for 'until'"})

            q += " and timestamp_utc <= %s"
            if len(until) == 20:
                until = until.replace("T", " ")[0:-1]

            params.append(until)

        if len(errors) > 0:
            return ([], errors)

        cursor.execute(q, tuple(params))
        identifiers = cursor.fetchall()
    except psycopg2.Error:
        errors.append({'code': "internalServerError"})
        return ([], errors)

    return (identifiers, [])


def get_metadata_record(dsid, metadata_prefix, mconfig, wconfig):
    if metadata_prefix == "oai_dc":
        mrec = dublin_core.export(dsid, mconfig, wconfig)
    elif metadata_prefix == "dif":
        mrec = gcmd_dif.export(dsid, mconfig, wconfig)
    elif metadata_prefix == "datacite":
        mrec = datacite_4.export(dsid, mconfig, wconfig)
    elif metadata_prefix == "fgdc":
        mrec = fgdc.export(dsid, mconfig, wconfig)
    elif metadata_prefix == "iso19115-3":
        mrec = iso_19115_3.export(dsid, mconfig, wconfig)
    elif metadata_prefix == "iso19139":
        mrec = iso_19139.export(dsid, mconfig, wconfig)
    elif metadata_prefix == "native":
        mrec = native.export(dsid, mconfig)

    return mrec.replace("\n", "\n        ").strip()


def get_record(request, oai_args, ctx):
    if 'identifier' not in request.GET:
        return error(request, [{'code': "badArgument",
                                'message': "'identifier' is missing"}],
                     verb="GetRecord")

    if 'metadataPrefix' not in request.GET:
        return error(request, [{'code': "badArgument",
                                'message': "'metadataPrefix' is missing"}],
                     verb="GetRecord")

    errors = []
    for arg, vals in oai_args:
        if arg in ("identifier", "metadataPrefix"):
            pass
        else:
            errors.append(
                    {'code': "badArgument",
                     'message': "'" + arg + "' is an illegal argument"})

    if len(errors) > 0:
        return error(request, errors, verb="GetRecord")

    iparts = request.GET['identifier'].split(":")
    ctx.update({
            'metadata_record':
            get_metadata_record(
                    iparts[-1],
                    request.GET['metadataPrefix'],
                    django_settings.RDADB['metadata_config_pg'],
                    django_settings.RDADB['wagtail_config_pg'])})
    return render(request, "oai/get_record.xml", context=ctx,
                  content_type="text/xml")


def list_identifiers(request, oai_args, ctx):
    if 'metadataPrefix' not in request.GET:
        return error(request, [{'code': "badArgument",
                                'message': "'metadataPrefix' is missing"}],
                     verb="ListIdentifiers")

    identifiers, errors = build_list(oai_args)
    if len(errors) > 0:
        if errors[0]['code'] == "internalServerError":
            return render(request, "500.html")

        return error(request, errors, verb="ListIdentifiers")

    ctx.update({'identifiers': identifiers})
    return render(request, "oai/identifiers.xml", context=ctx,
                  content_type="text/xml")


def list_metadata_formats(request, oai_args, ctx):
    if len(oai_args) > 0:
        return bad_args(request, oai_args, verb="Identify")

    qs = Page.objects.type(MetadataFormatsPage).specific()
    ctx.update({'page': qs[0].specific})
    return render(request, "oai/metadata_formats.xml", context=ctx,
                  content_type="text/xml")


def list_records(request, oai_args, ctx):
    if 'metadataPrefix' not in request.GET:
        return error(request, [{'code': "badArgument",
                                'message': "'metadataPrefix' is missing"}],
                     verb="ListRecords")

    try:
        conn = psycopg2.connect(
                **django_settings.RDADB['metadata_config_pg'])
        cursor = conn.cursor()
    except psycopg2.Error:
        return error(request,
                     [{'code': "internalServerError",
                       'message': ("Database connection error. Please try "
                                   "again later.")}],
                     verb="ListRecords")

    if 'resumptionToken' not in request.GET:
        identifiers, errors = build_list(oai_args)
        if len(errors) > 0:
            if errors[0]['code'] == "internalServerError":
                return render(request, "500.html")

            return error(request, errors, verb="ListRecords")

        token = strand(20)
        now = datetime.now(pytz.utc)
        expires = now + timedelta(hours=3)
        list_size = len(identifiers)
        lcursor = 0
        try:
            cursor.execute((
                    "select token from metautil.oai_resumption where "
                    "expiration < %s"), (now, ))
            res = cursor.fetchall()
            for e in res:
                cursor.execute((
                        "delete from metautil.oai_resumption_list where token "
                        "= %s"), (e[0], ))
                cursor.execute((
                        "delete from metautil.oai_resumption where token = "
                        "%s"), (e[0], ))
                conn.commit()

            cursor.execute((
                    "insert into metautil.oai_resumption values (%s, %s, %s)"),
                    (token, expires.astimezone(tz.gettz("US/Mountain")),
                     list_size))
            for x in range(0, list_size):
                cursor.execute((
                        "insert into metautil.oai_resumption_list values (%s, "
                        "%s, %s, %s)"), (token, identifiers[x][0],
                                         identifiers[x][1], x))

            conn.commit()
        except psycopg2.Error as err:
            print("OAI DATABASE (ListRecords) ERROR: " + str(err))
            return error(request,
                         [{'code': "internalServerError",
                           'message': ("Database error. Please try again "
                                       "later.")}],
                         verb="ListRecords")
    else:
        try:
            cursor.execute((
                    "select r.token, r.expiration, r.list_size, min(l."
                    "sort_order) from metautil.oai_resumption as r left "
                    "join metautil.oai_resumption_list as l on l.token = r."
                    "token where r.token = %s group by r.token"),
                    (request.GET['resumptionToken'], ))
            token, expires, list_size, lcursor = cursor.fetchone()
        except TypeError:
            return error(request,
                         [{'code': "badResumptionToken",
                           'message': ("The token provided is invalid or "
                                       "expired.")}],
                         verb="ListRecords")

    try:
        cursor.execute((
                "select dsid, timestamp_utc from metautil.oai_resumption_list "
                "where token = %s and sort_order < %s order by sort_order"),
                (token, lcursor+25))
        dsids = cursor.fetchall()
        mrecs = []
        for dsid, timestamp_utc in dsids:
            mrecs.append((
                    ":".join(["oai", ctx['repo_identifier'], dsid]),
                    timestamp_utc,
                    get_metadata_record(
                            dsid,
                            request.GET['metadataPrefix'],
                            django_settings.RDADB['metadata_config_pg'],
                            django_settings.RDADB['wagtail_config_pg'])))

        ctx.update({'metadata_records': mrecs})
        cursor.execute((
                "delete from metautil.oai_resumption_list where token = %s "
                "and sort_order < %s"), (token, lcursor+25))
        conn.commit()
        cursor.execute((
                "select count(*) from metautil.oai_resumption_list where "
                "token = %s"), (token, ))
        remaining_size, = cursor.fetchone()
        if remaining_size == 0:
            cursor.execute((
                    "delete from metautil.oai_resumption where token = %s"),
                    (token, ))
            conn.commit()
            token = ""
            expires = None

        ctx.update({'resumption_token': token,
                    'list_size': list_size,
                    'cursor': lcursor})
        if expires is not None:
            ctx.update({'token_expiration':
                        expires.strftime("%Y-%m-%dT%H:%M:%SZ")})

        return render(request, "oai/list_records.xml", context=ctx,
                      content_type="text/xml")
    except Exception as err:
        print("OAI ListRecords ERROR: " + str(err))
        return error(request,
                     [{'code': "internalServerError",
                       'message': ("An error occurred. Please try again "
                                   "later.")}],
                     verb="ListRecords")


def respond_to_request(request):
    if 'verb' not in request.GET:
        return error(request,
                     [{'code': "badVerb",
                      'message': "'verb' argument is missing"}])

    legal_verbs = {
        "GetRecord",
        "Identify",
        "ListIdentifiers",
        "ListMetadataFormats",
        "ListRecords",
        "ListSets",
    }
    if request.GET['verb'] not in legal_verbs:
        return error(request,
                     [{'code': "badVerb",
                      'message': ("'verb' argument is not a legal OAI-PMH "
                                  "verb")}])

    if len(request.GET.getlist('verb')) > 1:
        return error(request,
                     [{'code': "badArgument",
                      'message': "'verb' argument must not be repeated"}])

    ctx = {'base_url': os.path.join(metaformat_settings.ARCHIVE['url'],
                                    "oai")}
    uparts = metaformat_settings.ARCHIVE['url'].split("//")
    ctx.update({'repo_identifier': ".".join(reversed(uparts[1].split(".")))})
    oai_args = [t for t in request.GET.lists() if t[0] != 'verb']
    errors = check_args(oai_args, ctx['repo_identifier'])
    if len(errors) > 0:
        return error(request, errors, verb=request.GET['verb'])

    if request.GET['verb'] == "GetRecord":
        return get_record(request, oai_args, ctx)

    if request.GET['verb'] == "Identify":
        if len(oai_args) > 0:
            return bad_args(request, oai_args, verb="Identify")

        ctx.update({
            'repo_name': metaformat_settings.ARCHIVE['name'],
            'admin_email': metaformat_settings.ARCHIVE['email'],
        })
        return render(request, "oai/identify.xml", context=ctx,
                      content_type="text/xml")

    if request.GET['verb'] == "ListIdentifiers":
        return list_identifiers(request, oai_args, ctx)

    if request.GET['verb'] == "ListMetadataFormats":
        return list_metadata_formats(request, oai_args, ctx)

    if request.GET['verb'] == "ListRecords":
        return list_records(request, oai_args, ctx)

    if request.GET['verb'] == "ListSets":
        if len(oai_args) > 0:
            return bad_args(request, oai_args, verb="ListSets")

        return error(request,
                     [{'code': "noSetHierarchy",
                       'message': "This repository does not support sets"}],
                     verb="ListSets")
