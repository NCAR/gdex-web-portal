import sys

from . import utils


INDEXABLE_DATASET_CONDITIONS = "d.type in ('P', 'H') and d.dsid < 'd999000'"


def add_previous_datasets(lkey):
    t = utils.read_cache(lkey)
    return " and d.dsid in ('" + "', '".join(t[0]) + "')"


def set_variable_refine_query(lkey, nb=True):
    q = "select s.keyword, count(distinct s.dsid) from (select distinct split_part(g.path, ' > ', -1) as keyword, v.dsid from search.variables as v left join search.gcmd_sciencekeywords as g on g.uuid = v.keyword left join search.datasets as d on d.dsid = v.dsid where " + INDEXABLE_DATASET_CONDITIONS
    if not nb:
        q += add_previous_datasets(lkey)

    q += " and v.vocabulary = 'GCMD') as s group by s.keyword"
    return q


def run_variable_browse_query(v, cursor):
    q = "select distinct d.dsid, d.title, d.summary, d.type, max(t.rank) as trank from search.variables as v left join search.gcmd_sciencekeywords as g on g.uuid = v.keyword left join search.datasets as d on d.dsid = v.dsid left join search.gcmd_topics as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS + " and g.path like concat('%% > ', %s) group by d.dsid order by d.type, trank"
    cursor.execute(q, (v, ))


def set_time_resolution_refine_query(lkey, nb=True):
    q = "select replace(substring(t.keyword, 5), ' - ', ' to '), count(distinct d.dsid), s.idx as idx from search.datasets as d left join search.time_resolutions as t on t.dsid = d.dsid left join search.time_resolution_sort as s on s.keyword = t.keyword where " + INDEXABLE_DATASET_CONDITIONS
    if not nb:
        q += add_previous_datasets(lkey)
        
    q += " and idx is not null group by t.keyword, s.idx order by idx"
    return q


def run_time_resolution_browse_query(v, cursor):
    if v == "Not specified":
        q = "select distinct d.dsid, d.title, d.summary, d.type, max(t.rank) as trank from search.datasets as d left join search.time_resolutions as r on r.dsid = d.dsid left join search.gcmd_topics as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS + " and r.keyword is null group by d.dsid order by d.type, trank"
        cursor.execute(q, ())
    else:
        q = "select distinct d.dsid, d.title, d.summary, d.type, max(t.rank) as trank from search.time_resolutions as r left join search.datasets as d on d.dsid = r.dsid left join search.gcmd_topics as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS + " and r.keyword = concat('T : ', %s) group by d.dsid order by d.type, trank"
        cursor.execute(q, (v.replace(" to ", " - "), ))


def set_platform_refine_query(lkey, nb=True):
    q = "select distinct g.last_in_path, count(distinct d.dsid) from search.datasets as d left join search.platforms_new as p on p.dsid = d.dsid left join search.gcmd_platforms as g on g.uuid = p.keyword where " + INDEXABLE_DATASET_CONDITIONS
    if not nb:
        q += add_previous_datasets(lkey)
        
    q += " group by g.last_in_path order by g.last_in_path"
    return q


def run_platform_browse_query(v, cursor):
    if v == "Not specified":
        q = "select distinct d.dsid, d.title, d.summary, d.type, max(t.rank) as trank from search.datasets as d left join search.platforms_new as p on p.dsid = d.dsid left join search.gcmd_topics as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS + " and p.keyword is null group by d.dsid order by d.type, trank"
        cursor.execute(q, ())
    else:
        q = "select distinct d.dsid, d.title, d.summary, d.type, max(t.rank) as trank from search.platforms_new as p left join search.gcmd_platforms as g on g.uuid = p.keyword left join search.datasets as d on d.dsid = p.dsid left join search.gcmd_topics as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS + " and (g.last_in_path = %s or g.path like concat('%% > ', %s)) group by d.dsid order by d.type, trank"
        cursor.execute(q, (v, v))


def set_spatial_resolution_refine_query(lkey, nb=True):
    q = "select replace(substring(r.keyword, 5), ' - ', ' to '), count(distinct d.dsid), s.idx as idx from search.datasets as d left join search.grid_resolutions as r on r.dsid = d.dsid left join search.grid_resolution_sort as s on s.keyword = r.keyword where " + INDEXABLE_DATASET_CONDITIONS
    if not nb:
        q += add_previous_datasets(lkey)
        
    q += " and idx is not null group by r.keyword, s.idx order by idx"
    return q


def run_spatial_resolution_browse_query(v, cursor):
    if v == "Not specified":
        q = "select distinct d.dsid, d.title, d.summary, d.type, max(t.rank) as trank from search.datasets as d left join search.grid_resolutions as g on g.dsid = d.dsid left join search.gcmd_topics as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS + " and g.keyword is null group by d.dsid order by d.type, trank"
        cursor.execute(q, ())
    else:
        q = "select distinct d.dsid, d.title, d.summary, d.type, max(t.rank) as trank from search.grid_resolutions as g left join search.datasets as d on d.dsid = g.dsid left join search.gcmd_topics as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS + " " + " and g.keyword = concat('H : ', %s) group by d.dsid order by d.type, trank"
        cursor.execute(q, (v.replace(" to ", " - "), ))


def set_topic_refine_query(lkey, nb=True):
    q = "select s.keyword, count(distinct s.dsid) from (select distinct concat(split_part(g.path, ' > ', -3), ' > ', split_part(g.path, ' > ', -2)) as keyword, v.dsid from search.variables as v left join search.gcmd_sciencekeywords as g on g.uuid = v.keyword left join search.datasets as d on d.dsid = v.dsid where " + INDEXABLE_DATASET_CONDITIONS
    if not nb:
        q += add_previous_datasets(lkey)
        
    q += " and v.vocabulary = 'GCMD') as s group by s.keyword"
    return q


def run_topic_browse_query(v, cursor):
    parts = v.split(" > ")
    addl_cond = "v.topic ilike %s"
    if len(parts) > 1:
        addl_cond += " and v.term ilike %s"

    q = "select distinct d.dsid, d.title, d.summary, d.type, max(t.rank) as trank from search.gcmd_variables as v left join search.datasets as d on d.dsid = v.dsid left join search.gcmd_topics as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS + " and " + addl_cond + " group by d.dsid order by d.type, trank"
    if len(parts) > 1:
        cursor.execute(q, (parts[0], parts[1]))
    else:
        cursor.execute(q, (v, ))


def set_project_refine_query(lkey, nb=True):
    q = "select distinct g.last_in_path, count(distinct d.dsid) from search.datasets as d left join search.projects_new as p on p.dsid = d.dsid left join search.gcmd_projects as g on g.uuid = p.keyword where " + INDEXABLE_DATASET_CONDITIONS
    if not nb:
        q += add_previous_datasets(lkey)
        
    q += " group by g.last_in_path order by g.last_in_path"
    return q


def run_project_browse_query(v, cursor):
    if v == "Not specified":
        q = "select distinct d.dsid, d.title, d.summary, d.type, max(t.rank) as trank from search.datasets as d left join search.projects_new as p on p.dsid = d.dsid left join search.gcmd_topics as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS + " and p.keyword is null group by d.dsid order by d.type, trank"
        cursor.execute(q, ())
    else:
        q = "select distinct d.dsid, d.title, d.summary, d.type, max(t.rank) as trank from search.projects_new as p left join search.gcmd_projects as g on g.uuid = p.keyword left join search.datasets as d on d.dsid = p.dsid left join search.gcmd_topics as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS + " and (g.last_in_path = %s or g.path like concat('%% > ', %s)) group by d.dsid order by d.type, trank"
        cursor.execute(q, (v, v))


def set_type_refine_query(lkey, nb=True):
    q = "select distinct t.keyword, count(distinct d.dsid) from search.datasets as d left join search.data_types as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS
    if not nb:
        q += add_previous_datasets(lkey)
        
    q += " group by t.keyword"
    return q


def run_type_browse_query(v, cursor):
    q = "select distinct d.dsid, d.title, d.summary, d.type, max(t.rank) as trank from search.datasets as d left join search.data_types as y on y.dsid = d.dsid left join search.gcmd_topics as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS + " and "
    if v == "Not specified":
        q += "y.keyword is null"
    else:
        q += "y.keyword = %s"

    q += " group by d.dsid order by d.type, trank"
    cursor.execute(q, (v, ))


def set_supported_project_refine_query(lkey, nb=True):
    q = "select g.last_in_path, count(distinct d.dsid) from search.datasets as d left join search.supported_projects as p on p.dsid = d.dsid left join search.gcmd_projects as g on g.uuid = p.keyword where " + INDEXABLE_DATASET_CONDITIONS
    if not nb:
        q += add_previous_datasets(lkey)
        
    q += " group by g.last_in_path order by g.last_in_path"
    return q


def run_supported_project_browse_query(v, cursor):
    if v == "Not specified":
        q = "select distinct d.dsid, d.title, d.summary, d.type, max(t.rank) as trank from search.datasets as d left join search.supported_projects as s on s.dsid = d.dsid left join search.gcmd_topics as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS + " and s.keyword is null group by d.dsid order by d.type, trank"
    else:
        q = "select distinct d.dsid, d.title, d.summary, d.type, max(t.rank) as trank from search.supported_projects as p left join search.gcmd_projects as g on g.uuid = p.keyword left join search.datasets as d on d.dsid = p.dsid left join search.gcmd_topics as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS + " and (g.last_in_path = %s or g.path like concat('%% > ', %s)) group by d.dsid order by d.type, trank"

    cursor.execute(q, (v, v))


def set_data_format_refine_query(lkey, nb=True):
    q = "select distinct f.keyword, count(distinct d.dsid) from search.datasets as d left join search.formats as f on f.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS
    if not nb:
        q += add_previous_datasets(lkey)
        
    q += " group by f.keyword"
    return q


def run_data_format_browse_query(v, cursor):
    if v == "Not specified":
        q = "select distinct d.dsid, d.title, d.summary, d.type, max(t.rank) as trank from search.datasets as d left join search.formats as f on f.dsid = d.dsid left join search.gcmd_topics as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS + " and f.keyword is null group by d.dsid order by d.type, trank"
    else:
        q = "select distinct d.dsid, d.title, d.summary, d.type, max(t.rank) as trank from search.formats as f left join search.datasets as d on d.dsid = f.dsid left join search.gcmd_topics as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS + " and f.keyword = %s group by d.dsid order by d.type, trank"

    cursor.execute(q, (v, ))


def set_instrument_refine_query(lkey, nb=True):
    q = "select distinct g.last_in_path, count(distinct d.dsid) from search.datasets as d left join search.instruments as i on i.dsid = d.dsid left join search.gcmd_instruments as g on g.uuid = i.keyword where " + INDEXABLE_DATASET_CONDITIONS
    if not nb:
        q += add_previous_datasets(lkey)
        
    q += " group by g.last_in_path order by g.last_in_path"
    return q


def run_instrument_browse_query(v, cursor):
    if v == "Not specified":
        q = "select distinct d.dsid, d.title, d.summary, d.type, max(t.rank) as trank from search.datasets as d left join search.instruments as i on i.dsid = d.dsid left join search.gcmd_topics as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS + " and i.keyword is null group by d.dsid order by d.type, trank"
    else:
        q = "select distinct d.dsid, d.title, d.summary, d.type, max(t.rank) as trank from search.instruments as i left join search.gcmd_instruments as g on g.uuid = i.keyword left join search.datasets as d on d.dsid = i.dsid left join search.gcmd_topics as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS + " and g.last_in_path = %s group by d.dsid order by d.type, trank"

    cursor.execute(q, (v, ))


def set_location_refine_query(lkey, nb=True):
    q = "select initcap (case when position('UNITED STATES' in upper(l.keyword)) != 0 then concat(split_part(l.keyword, ' > ', -2), ' > ', split_part(l.keyword, ' > ', -1)) else split_part(l.keyword, ' > ', -1) end) as kw, count(d.dsid) from search.datasets as d left join search.locations as l on l.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS
    if not nb:
        q += add_previous_datasets(lkey)
        
    q += " and (l.include is null or l.include != 'N') group by kw order by kw"
    return q


def run_location_browse_query(v, cursor):
    k = ""
    if v == "Not specified":
        q = "select distinct d.dsid, d.title, d.summary, d.type, max(t.rank) as trank from search.datasets as d left join search.locations as l on l.dsid = d.dsid left join search.gcmd_topics as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS + " and l.keyword is null group by d.dsid order by d.type, trank"
    else:
        q = "select distinct d.dsid, d.title, d.summary, d.type, max(t.rank) as trank from search.locations as l left join search.datasets as d on d.dsid = l.dsid left join search.gcmd_topics as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS + " and l.keyword like concat('%% > ', %s) group by d.dsid order by d.type, trank"
        k = v.replace("USA", "United States Of America")
        k = k.replace("'", "\\'")

    cursor.execute(q, (k, ))


def set_progress_refine_query(lkey, nb=True):
    q = "select case when continuing_update='Y' then 'Continually Updated' else 'Complete' end, count(distinct dsid) from search.datasets as d where " + INDEXABLE_DATASET_CONDITIONS
    if not nb:
        q += add_previous_datasets(lkey)
        
    q += " group by continuing_update"
    return q


def run_progress_browse_query(v, cursor):
    v = "N" if v == "Complete" else "Y"
    q = "select distinct d.dsid, d.title, d.summary, d.type, max(t.rank) as trank from search.datasets as d left join search.gcmd_topics as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS + " and d.continuing_update = %s group by d.dsid order by d.type, trank"
    cursor.execute(q, (v, ))


def run_ftext_browse_query(v, cursor):
    parts = v.split()
    inc = ""
    exc = ""
    ilst = []
    elst = []
    for part in parts:
        if part[0] == '-':
            if len(exc) > 0:
                exc += " or "

            exc += "word = %s"
            elst.append(part[1:])
        else:
            if len(inc) > 0:
                inc += " or "

            inc += "word = %s or (word like %s and sword = %s)"
            ilst.extend([part, "%" + part + "%", utils.soundex(part)])

    if ilst and elst:
        q = "select distinct d.dsid, d.title, d.summary, d.type, max(t.rank) as trank from (select dsid from search.title_wordlist where " + inc + " union all select dsid from search.summary_wordlist where " + inc + ") as a left join (select dsid from search.title_wordlist where " + exc + " union all select dsid from search.summary_wordlist where " + exc + ") as b on b.dsid = a.dsid left join search.datasets as d on d.dsid = a.dsid left join search.gcmd_topics as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS + " and b.dsid is null group by d.dsid order by d.type, trank"
        cursor.execute(q, tuple(ilst) + tuple(ilst) + tuple(elst) + tuple(elst))
    elif ilst:
        q = "select distinct d.dsid, d.title, d.summary, d.type, max(t.rank) as trank from (select dsid from search.title_wordlist where " + inc + " union all select dsid from search.summary_wordlist where " + inc + ") as u left join search.datasets as d on d.dsid = u.dsid left join search.gcmd_topics as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS + " group by d.dsid order by d.type, trank"
        cursor.execute(q, tuple(ilst) + tuple(ilst))
    elif elst:
        q = "select distinct d.dsid, d.title, d.summary, d.type, max(t.rank) as trank from search.datasets as d left join (select dsid from search.title_wordlist where " + exc + " union all select dsid from search.summary_wordlist where " + exc + " ) as u on u.dsid = d.dsid left join search.gcmd_topics as t on t.dsid = d.dsid where " + INDEXABLE_DATASET_CONDITIONS + " and u.dsid is null group by d.dsid order by d.type, trank"
        cursor.execute(q, tuple(elst) + tuple(elst))

refine_queries = {
    'var': set_variable_refine_query,
    'tres': set_time_resolution_refine_query,
    'plat': set_platform_refine_query,
    'sres': set_spatial_resolution_refine_query,
    'topic': set_topic_refine_query,
    'proj': set_project_refine_query,
    'type': set_type_refine_query,
    'supp': set_supported_project_refine_query,
    'fmt': set_data_format_refine_query,
    'instr': set_instrument_refine_query,
    'loc': set_location_refine_query,
    'prog': set_progress_refine_query,
}

browse_queries = {
    'var': run_variable_browse_query,
    'tres': run_time_resolution_browse_query,
    'plat': run_platform_browse_query,
    'sres': run_spatial_resolution_browse_query,
    'topic': run_topic_browse_query,
    'proj': run_project_browse_query,
    'type': run_type_browse_query,
    'supp': run_supported_project_browse_query,
    'fmt': run_data_format_browse_query,
    'instr': run_instrument_browse_query,
    'loc': run_location_browse_query,
    'prog': run_progress_browse_query,
    'ftext': run_ftext_browse_query,
}
