import random
import string

import psycopg2

from . import defs


def category(short_name):
    if short_name == "var":
        return "Variable / Parameter"
    elif short_name == "tres":
        return "Time Resolution"
    elif short_name == "plat":
        return "Platform"
    elif short_name == "sres":
        return "Spatial Resolution"
    elif short_name == "topic":
        return "Topic / Subtopic"
    elif short_name == "proj":
        return "Project / Experiment"
    elif short_name == "type":
        return "Type of Data"
    elif short_name == "supp":
        return "Supports Project"
    elif short_name == "fmt":
        return "Data Format"
    elif short_name == "instr":
        return "Instrument"
    elif short_name == "loc":
        return "Location"
    elif short_name == "prog":
        return "Progress"
    elif short_name == "ftext":
        return "Free Text"
    elif short_name == "recent":
        return "Recently Added / Updated"
    elif short_name == "doi":
        return "Datasets with DOIs"
    elif short_name == "all":
        return "All RDA Datasets"
    else:
        return short_name


def convert_to_expandable_summary(summary, visible_length, iterator):
    parts = summary.split()
    if len(parts) < visible_length:
        s = summary.strip()
        s = s.replace("<p>", "<span>")
        s = s.replace("</p>", "</span><br><br>")
        return s[:-8]
    else:
        s = ""
        in_tag = 0
        for n in range(visible_length):
            if "</p>" in parts[n] or ( (n + 1) < len(parts) and "</p>" in parts[n + 1]):
                break

            if len(s) > 0:
                s += " "

            s += parts[n]
            in_tag += parts[n].count("<") - parts[n].count("</") * 2 + parts[n].count("</p>") - parts[n].count("<p>")

        n += 1
        if in_tag > 0:
            while n < len(parts) and in_tag > 0:
                s += " " + parts[n]
                if "</" in parts[n]:
                    in_tag -= 1

                n += 1

        s = s.replace("<p>", "<span>")
        s = s.replace("</p>", "</span><br><br>")
        s_end = "<span>"
        while n < len(parts):
            s_end += " " + parts[n]
            n += 1

        s_end = s_end.replace("<p>", "<span>")
        s_end = s_end.replace("</p>", "</span><br><br>")
        s_end = s_end.strip()
        if s[-9:] == "<br><br>\n":
            s = s[:-9]
            s_end = "<br><br>" + s_end

        if len(s_end) > 8:
            one = str(iterator[0])
            two = str(iterator[0] + 1)
            s += "<span id=\"D" + one + "\">&nbsp;...&nbsp;<a href=\"javascript:swapDivs(" + str(one) + ", " + two + ")\" title=\"Expand\"><img src=\"/images/expand.gif\" width=\"11\" height=\"11\" border=\"0\"></a></span></span><span style=\"visibility: hidden; position: absolute; left: 0px\" id=\"D" + two + "\">" + s_end[:-8] + " <a href=\"javascript:swapDivs(" + two + ", " + one + ")\" title=\"Collapse\"><img src=\"/images/contract.gif\" width=\"11\" height=\"11\" border=\"0\"></a></span>"

        if s[-1] == "\n":
            s = s[:-1]

        iterator[0] += 2
        return s


def set_date_time(dt, flag, tz):
    s = dt
    if flag == "1":
        s = s[0:4]
    elif flag == "2":
        s = s[0:7]
    elif flag == "3":
        s = s[0:10]
    elif flag == "4":
        s = s[0:13] + " " + tz
    elif flag == "5":
        s = s[0:16] + " " + tz
    elif flag == "6":
        s += " " + tz

    return s


def get_comparison_dataset(dsid):
    d = {}
    mconn = psycopg2.connect(**defs.metadb_config_pg)
    mcursor = mconn.cursor()
    mcursor.execute("select title, type from search.datasets where dsid = %s", (dsid, ))
    res = mcursor.fetchone()
    if res == None:
        d.update({'error': True})
        return d

    d.update({'title': res[0]})
    mcursor.execute("select min(concat(date_start, ' ', time_start)), min(start_flag), max(concat(date_end, ' ', time_end)), min(end_flag), any_value(time_zone) from dssdb.dsperiod where dsid = %s group by dsid", (dsid, ))
    res = mcursor.fetchone()
    if res != None:
        d.update({'temporal_start': set_date_time(res[0], res[1], res[4]), 'temporal_end': set_date_time(res[2], res[3], res[4])})

    mcursor.execute("select distinct keyword from search.data_types where dsid = %s order by keyword", (dsid, ))
    res = mcursor.fetchall()
    if res == None:
        d.update({'error': True})
        return d

    list = []
    for r in res:
        list.append(r[0].title())

    d.update({'data_types': list})
    mcursor.execute("select distinct keyword from search.formats where dsid = %s order by keyword", (dsid, ))
    res = mcursor.fetchall()
    if res == None:
        d.update({'error': True})
        return d

    list = []
    for r in res:
        if r[0].startswith("proprietary_"):
            list.append(r[0][12:] + " (see dataset documentation)")
        else:
            list.append(r[0])

    d.update({'data_formats': list})
    mcursor.execute("select distinct g.last_in_path from search.platforms_new as p left join search.gcmd_platforms as g on g.uuid = p.keyword where p.dsid = %s order by g.last_in_path", (dsid, ))
    res = mcursor.fetchall()
    if res == None:
        d.update({'error': True})
        return d

    list = []
    for r in res:
        if r[0] != None:
            list.append(r[0])

    d.update({'platforms': list})
    try:
        mcursor.execute("select distinct t.time_range from (select distinct time_range_code from WGrML." + dsid + "_grids2) as g left join WGrML.time_ranges as t on t.code = g.time_range_code")
    except:
        pass
    else:
        res = mcursor.fetchall()
        if res != None:
            list = []
            for r in res:
                if r != None:
                    list.append(r[0])

            d.update({'gridded_products': list})

    try:
        mcursor.execute("select distinct d.definition, d.def_params from WGrML.summary as s left join WGrML.grid_definitions as d on d.code = s.grid_definition_code where s.dsid = %s", (dsid, ))
    except:
        pass
    else:
        res = mcursor.fetchall()
        if res != None:
            list = []
            for r in res:
                if r != None:
                    list.append(r[0])

            d.update({'grid_definitions': list})

    mcursor.execute("select replace(g.path, 'EARTH SCIENCE > ', '') as var from search.variables as v left join search.gcmd_sciencekeywords as g on g.uuid = v.keyword where v.dsid = %s and v.vocabulary = 'GCMD' order by var", (dsid, ))
    res = mcursor.fetchall()
    if res == None:
        d.update({'error': True})
        return d

    list = []
    for r in res:
        if r[0] != None:
            list.append(r[0])

    d.update({'parameters': list})
    return d


def open_cache_for_writing(lkey, nb=True):
    if nb:
        return open("/usr/local/www/server_root/tmp/browse." + lkey, "w")
    else:
        return open("/usr/local/www/server_root/tmp/browse." + lkey, "a")


def read_cache(lkey):
    refines = {}
    dsids = []
    with open("/usr/local/www/server_root/tmp/browse." + lkey, "r") as f:
        line = f.readline()
        while line:
            if line[0] == '@':
                parts = line.split("<!>")
                key = parts[0][1:]
                d = {'name': parts[1], 'count': int(parts[2])}
                if key in refines:
                    refines[key].append(d)
                else:
                    refines.update({key: [d]})

                dsids = []
            else:
                dsids.append(line.strip())

            line = f.readline()

    return (dsids, refines)


def generate_lkey():
    s = string.ascii_letters + string.digits
    return ''.join(random.choice(s) for i in range(30))


def soundex(word):
    word = word.upper()
    soundex = word[0]
    d = {"AEIOUHWY": "0", "BFPV": "1", "CGJKQSXZ": "2", "DT": "3", "L": "4", "MN": "5", "R": "6"}
    for char in word[1:]:
        for key in d:
            if char in key:
                code = d[key]
                if code != "0" and code != soundex[-1]:
                    soundex += code

    return soundex[:4].ljust(4, "0")
