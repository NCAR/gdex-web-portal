word_lists = [
    {
        'db': "search",
        'table': "summary_wordlist",
        'weight': 1.,
    },
    {
        'db': "search",
        'table': "title_wordlist",
        'weight': 2.1,
    },
    {
        'db': "search",
        'table': "references_wordlist",
        'weight': 0.85,
    },
    {
        'db': "search",
        'table': "variables_wordlist",
        'weight': 2.,
    },
    {
        'db': "search",
        'table': "locations_wordlist",
        'weight': 2.,
    },
    {
        'db': "",
        'table': ("(select p.dsid as dsid, g.path as keyword from search."
                  "projects_new as p left join search.gcmd_projects as g on "
                  "g.uuid = p.keyword) as x"),
        'weight': 5.,
    },
    {
        'db': "search",
        'table': "supported_projects",
        'weight': 5.,
    },
    {
        'db': "search",
        'table': "formats",
        'weight': 0.5,
    },
]
