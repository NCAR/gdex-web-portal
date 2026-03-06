import os
import sys
from api import common
import re
from textwrap import dedent
from datetime import datetime

class CodeExample:

    def __init__(self, dsid,
            selected_var=None, start=None, end=None, is_remote=False, selected_type=None,
            nlat=90, slat=-90, elon=180, wlon=-180):
        self.dsid = dsid
        self.snippets = []
        self.extra_imports = []
        if selected_var:
            self.selected_var = common.get_param_info(selected_var)
            self.selected_var['code'] = selected_var
        else:
            self.variables = self.get_available_variables(dsid)
            self.selected_var = self.variables[0]
        if not start and not end:
            self.start_date, self.end_date = common.get_time_range(dsid)
        else:
            self.start_date = datetime.strptime(start,'%Y-%m-%d')
            self.end_date = datetime.strptime(end,'%Y-%m-%d')
        self.set_example_type(selected_type)
        self.nlat = nlat
        self.slat = slat
        self.elon = elon
        self.wlon = wlon
        self.resource_identifier = 'filename'
        self.is_remote = self.set_remote(is_remote)
        self.requirements = ['xarray']
        self.init_code_snippets()

    def init_code_snippets(self):

        # Header
        self.snippets.append(self.get_header_snippet())

        # Open file
        random_file = self.get_random_file()[0]
        open_snip = self.get_open_data_snippet(random_file)
        self.snippets.append(open_snip)

        # Select variable
        self.snippets.append(self.get_variable_snippet())

        # Select in space
        if self.nlat != 90 and self.slat != -90 and self.elon != 180 and self.wlon != -180:
            self.snippets.append(self.get_spatial_snippet())

        # Select in time
        self.snippets.append(self.get_temporal_snippet())

        # Get examples code
        self.snippets.append(self.get_example_snippet())

    def set_example_type(self, example_type):
        if example_type in self.example_types():
            self.example_type = example_type
        else:
            example_type = None
        if example_type is None:
            self.example_type = self.example_types()[0]
        if example_type == 'image':
            self.extra_imports.extend(['import cartopy.crs as ccrs',
                'import matplotlib as mpl',
                'import matplotlib.pyplot as plt'])

    def set_remote(self, remote):
        if remote:
            self.resource_identifier = 'url'
        else:
            self.resource_identifier = 'filename'
        return remote

    def example_types(self):
        return ['image', 'time_series', 'aggregation', 'regrid']

    def get_example_snippet(self):
        if  self.example_type == 'image':
            return self.get_image_gen_snippet()
        return CodeSnippet()

    def get_available_variables(self, dsid):
        """Collect available variables for a given dataset."""
        _vars = common.get_variable_info(dsid)
        _vars = [x['parameter'] for x in _vars]
        out_vars = []
        check_dupes = set()
        for v in _vars:
            v_info = common.get_param_info(v)
            v_info['code'] = v
            dupe_key = v_info['description']
            if 'units' in v_info:
                dupe_key = v_info['description']+v_info['units']
            if dupe_key not in check_dupes:
                check_dupes.add(dupe_key)
                out_vars.append(v_info)

        def in_preferred(var):
            preferred_vars = ['temperature','wind']
            for i in preferred_vars:
                if re.match(f'^.*{i}.*$', var['description'].lower()):
                    if '2' in var['description']:
                        return -3
                    return -1
            return 1
        out_vars = sorted(out_vars, key=in_preferred)

        return out_vars

    def get_variables(self):
        return self.variables

    def get_start_date(self):
        return self.start_date.strftime('%Y-%m-%d')

    def get_end_date(self):
        return self.end_date.strftime('%Y-%m-%d')

    def get_random_file(self):
        return common.get_random_webfile(self.dsid, parameter_code=self.selected_var['code'],
                start_date=self.start_date.strftime('%Y%m%d0000'),end_date=self.end_date.strftime('%Y%m%d0000'))

    def get_open_data_snippet(self, _file):
        if self.is_remote:
            _file = f'https://data.rda.ucar.edu/datasets/{self.dsid}/{_file}'
        else:
            _file = f'/glade/campaign/collections/rda/data/{self.dsid}/{_file}'


        code = f"""
               # Open dataset using xarray
               {self.resource_identifier} = '{_file}'
               """
        if _file[-3:] == 'grb' or _file[-5:-1] == 'grib':
            code = code + f"ds = xarray.open_dataset({self.resource_identifier}, engine='cfgrib')"
            self.requirements.append('cfgrib')
        else:
            code = code + f"ds = xarray.open_dataset({self.resource_identifier})"

        code = dedent(code)
        return CodeSnippet(code=code, priority=1)

    def get_header_snippet(self):
        code = """
               # Example script
               import xarray
               import datetime"""
        code = dedent(code)
        for line in self.extra_imports:
            code = code + f"\n{line}"
        return CodeSnippet(code=code, priority=1)

    def get_variable_snippet(self):
        shortname = self.selected_var['shortName']
        code = f"""
               # Select Variable
               var = ds['{shortname}']"""
        code = dedent(code)
        return CodeSnippet(code=code, priority=2)

    def get_spatial_snippet(self):
        code = f"""
               # subset in space
               lat_mask = (ds[lat] <= float({self.nlat})) & (ds[lat] >= float({self.slat}))
               if elon > 360 and wlon < 360:
                   lon_mask = (ds[lon] <= float({self.elon})%360) | (ds[lon] >= float({self.wlon})%360)
               else:
                   lon_mask = (ds[lon] <= float({self.elon})%360) & (ds[lon] >= float({self.wlon})%360)

               new_dataset = ds.isel({{lat:lat_mask, lon:lon_mask}})"""
        code = dedent(code)
        return CodeSnippet(code=code, priority=2)

    def get_temporal_snippet(self):
        code = f"""
                # subset in time
                start_date = datetime.datetime.strptime({self.start_date}, '%Y-%m-%d')
                end_date = datetime.datetime.strptime({self.end_date}, '%Y-%m-%d')

                time_mask = (ds[time] >= numpy.datetime64(start_date)) & (ds[time] <= numpy.datetime64(end_date))

                # subset each datavar
                new_vars = {{}}
                for k,v in ds.data_vars.items():
                    if 'coordinates' in v.attrs:
                        del v.attrs['coordinates'] # for serializing
                    if time in v.dims:
                        new_vars[k] = ds[k].isel({{time:time_mask}})
                    else:
                        new_vars[k] = v

                new_dataset = xarray.Dataset(new_vars)
                """
        code = dedent(code)
        return CodeSnippet(code=code, priority=2)

    def get_image_gen_snippet(self):
        self.requirements.append('cartopy')
        self.requirements.append('matplotlib')
        code = f"""
                # Generate Image
                new_ds.plot(
                    ax=axis,
                    transform=ccrs.PlateCarree(),
                    cbar_kwargs={{"orientation": "horizontal", "shrink": 0.7}},
                    robust=True,
                )
                axis.coastlines()
                """
        code = dedent(code)
        return CodeSnippet(code=code, priority=10)

    def get_code(self):
        return self.__str__()

    def get_requirements(self):
        return self.requirements

    def __str__(self):

        output = ""
        for s in self.snippets:
            output += s.__str__() + '\n'
        return output


class CodeSnippet:

    def __init__(self, code="", priority=5):
        self.code = code
        self.priority = priority

    def __str__(self):
        return self.code






