from string import Template

webhome_path = '/data'

content_metadata_dbs = [
    'WGrML',
    'WObML',
    'WFixML',
]

static_list_url_templates = {
    #'data_format_conversion': Template('/datasets/ds$dsnum/WEB-format-list.html'),
    'data_format_conversion': Template('/datasets/$dsid/filelist/'),
    #'glade': Template('/datasets/ds$dsnum/GLADE-file-list.html'),
    'glade': Template('/datasets/$dsid/filelist/'),
    'web': Template('/datasets/$dsid/filelist/'),
}

faceted_browse_url_templates = {
    'glade': Template("/datasets/$dsid/listopt/glade/"),
    'web': Template("/datasets/$dsid/listopt/web/"),
}
