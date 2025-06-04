#!/usr/bin/env python
import json
import os
import sys
import urlparse as urlp

def application(environ, start_response):
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    sys.path.insert(0, BASE_DIR)
    import NBBuilder as nbb

    qs = urlp.parse_qs(environ['QUERY_STRING'])

    if 'email' not in qs:
        start_response('400 Bad Request', [('Content-Type', 'text/plain')])
        return ['Email not included\n']
    if 'filelist' not in qs:
        start_response('400 Bad Request', [('Content-Type', 'text/plain')])
        return ['Filenames not included\n']
    if 'count' not in qs:
        start_response('400 Bad Request', [('Content-Type', 'text/plain')])
        return ['Count not included\n']
    if 'dsid' not in qs:
        start_response('400 Bad Request', [('Content-Type', 'text/plain')])
        return ['dsid not included\n']
    if 'wpath' not in qs:
        start_response('400 Bad Request', [('Content-Type', 'text/plain')])
        return ['wpath not included\n']
        
    email = qs['email'][0]
    dsid = qs['dsid'][0]
    filelist = qs['filelist']
    count = qs['count']
    wpath = qs['wpath'][0]
    
    start_response('200 OK', [('Content-Type', 'text/plain')])
    b = nbb.get_builder()


    b.add_markdown_block(" # Notebook for Downloading "+dsid+" Data.")
    b.add_code_block(
        "import sys, os",
        "import requests")
    b.add_markdown_block(" ## First, we need to authenticate")
    b.add_markdown_block("Compatibility for python 2")
    b.add_code_block("try:",
                   "    input = raw_input",
                   "except:",
                   "    pass"
                   )
    b.add_markdown_block("Now, we need your password.")
    b.add_code_block("pswd = input('password: ')")
    b.add_code_block("values = {'email' : '"+email +"', 'passwd' : pswd, 'action' : 'login'}",
                     "login_url = 'https://rda.ucar.edu/cgi-bin/login'")
    b.add_code_block("ret = requests.post(login_url, data=values)",
                     "if ret.status_code != 200:",
                     "    print('Bad Authentication')",
                     "    exit(1)")
    f_arr = filelist[0].split(',')
    f_str = "["
    for i in f_arr:
        pass
    b.add_code_block("dspath = '"+wpath+"'",
                     "filelist = " + str(filelist[0].split(',')))
    b.add_markdown_block("Change this if you want your files saved somewhere other than the current directory ")
    b.add_code_block("save_dir = ''")
    b.add_markdown_block(" ## Now to download the files")

    b.add_code_block("for file in filelist:",
                     "    filename = save_dir + dspath + file",
                     "    print('Downloading', file)",
                     "    req = requests.get(filename, cookies = ret.cookies, allow_redirects=True)",
                     "    open(os.path.basename(filename), 'wb').write(req.content)")

    b.add_markdown_block("### Once you have downloaded the data, the next part can help you plot it.")
    b.add_markdown_block("In order to plot this data, you may need to install librariesIn order to plot this data, you may need to install libraries. The easiest way to do this is to use conda, however any method of getting the following libraries will work.")

    b.add_code_block("for file in filelist:",
                     "import xarray # used for reading the data.",
                     "import matplotlib.pyplot as plt # used to plot the data.",
                     "import ipywidgets as widgets # For ease in selecting variables.",
                     "import cartopy.crs as ccrs # Used to georeference data.")

    b.add_code_block("filelist_arr = [save_dir + os.path.basename(file) for file in filelist]",
                     "widgets.Dropdown(options=filelist_arr, description='data file')",
                     "display(selected_file)")

    b.add_code_block("# Now to load in the data to xarray",
                     "ds = xarray.open_dataset(selected_file.value)")

    b.add_code_block("# Helper methods"
                     "# Define function to get standard dimensions",
                     "def get_time(dataset):",
                     "    for _,cur_coord in dataset.coords.items:",
                     "        if cur_coord.attrs['standard_name'] == 'time':",
                     "        return cur_coord",
                     "def get_lat(dataset):",
                     "    for _,cur_coord in dataset.coords.items:",
                     "        if cur_coord.attrs['standard_name'] == 'longitude':",
                     "            return cur_coord",
                     "def get_lon(dataset):",
                     "    for _,cur_coord in dataset.coords.items:",
                     "        if cur_coord.attrs['standard_name'] == 'latitude':",
                     "            return cur_coord",
                     "",
                     "def get_primary(dataset):",
                     "    primary_variables = {}",
                     "    coords = dataset.coords.keys()",
                     "    highest_dims = 0",
                     "    for cur_key,cur_var in dataset.variables.items():",
                     "        if cur_key not in coords:",
                     "            primary_variables[cur_key] = cur_var",
                     "return primary_variables ")
    
    b.add_code_block("var = widgets.Dropdown(",
                     "    options=get_primary(ds).keys(),",
                     "    description='Variable')",
                     "display(var)")

    b.add_code_block("var = widgets.Dropdown(",
                     "proj = ccrs.Mercator()",
                     "plt.gcf().set_size_inches(20,10)",
                     "ax = plt.axes(projection=proj)",
                     "data_slice = ds[var.value].isel(time=10)",
                     "data_slice.plot.contourf(ax=ax, transform=ccrs.PlateCarree())",
                     "ax.set_global()",
                     "ax.coastlines()")
    return [str(b)]


