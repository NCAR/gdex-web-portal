from . import local_settings


metadata_managers = local_settings.metadata_managers

root_dirs = {
    'cvs': "/data/cvs",
    'rdadata_home': local_settings.rdadata_home,
    'tmp': "/data/ptmp",
    'web': "/data/web",
}

bin_utils = {
    'cvs': "/usr/bin/cvs",
    'imagemagick': {
        'identify': "/usr/bin/identify",
    },
    'rdadatarun': local_settings.rdadatarun,
}

spellchecker_settings = {
    'db_config': local_settings.spellcheck_db_config,
    'valids_schema': "metautil",
}

ISO_topics = [
    "biota",
    "boundaries",
    "climatologyMeteorologyAtmosphere",
    "economy",
    "elevation",
    "environment",
    "farming",
    "geoscientificInformation",
    "health",
    "imageryBaseMapsEarthCover",
    "intelligenceMilitary",
    "inlandWaters",
    "location",
    "oceans",
    "planningCadastre",
    "society",
    "structure",
    "transportation",
    "utilitiesCommunications",
]

linkcheck_headers = {
    'Accept': ("text/html,application/xhtml+xml,application/xml;q=0.9,image/"
               "avif,image/webp,image/apng,*/*;q=0.8,application/"
               "signed-exchange;v=b3;q=0.7"),
    'Accept-Encoding': "gzip, deflate, br, zstd",
    'Accept-Language': "en-US,en;q=0.9",
    'Priority': "u=0, i",
    'Sec-Fetch-Dest': "document",
    'Sec-Fetch-Mode': "navigate",
    'Sec-Fetch-Site': "none",
    'Sec-Fetch-User': "?1",
    'Upgrade-Insecure-Requests': "1",
    'User-Agent': ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 "
                   "Safari/537.36"),
}

markup_schemas = [
    "GrML",
    "ObML",
]

default_data_license = "CC-BY-4.0"

doi_manager = {
    'auth_key': local_settings.doi_manager_auth_key,
    'invoke_command': "source /usr/local/rdaweb/bin/activate; doi_manage",
}
