import os
import json
import psycopg2
import re
import sys

from enum import Enum

from django.conf import settings
from globus.views import get_guest_collection_url

from . import config
from .config import static_list_url_templates as sl
from .config import faceted_browse_url_templates as fb
from home.utils import slug_list

import logging
logger = logging.getLogger(__name__)

DataFormatConversionType = Enum('DataFormatConversionType',
    [
        ('GLOBAL', 'global'),
        ('GROUP', 'group'),
    ]
)
ResultType = Enum('ResultType', 'ONE MANY')

class Matrix:
    def __init__(self, dsid, duser):
        self.dsid = dsid.replace("-", ".")

        self.duser = duser
        self.error = self.Error()
        self.columns = {}
        self.union_urls = {}
        self.conn = psycopg2.connect(**settings.RDADB['metadata_config_pg'])
        self.cursor = self.conn.cursor()
        self.web_data = self.get_download_file_data()
        if not self.error:
            self.set_custom_request_data()

        if not self.error:
            self.group_data = self.get_group_data()

    def __del__(self):
        self.cursor.close()
        self.conn.close()

    def fill_download_file_data(self, result):
        web_data = {}
        if result[0] != '0':
            web_data['home'] = config.webhome_path + "/" + self.dsid

        web_data['locflag'] = result[2] 
        self.columns['web_files'] = True
        self.columns['globus'] = True
        logger.debug("dsid: {}, locflag: {}".format(self.dsid, web_data['locflag']))
        g_dsid = self.dsid;
        if g_dsid[0] != 'd':
            g_dsid = "ds" + g_dsid

        try:
            self.union_urls['globus'] = get_guest_collection_url(dsid=g_dsid, locflag=web_data['locflag'])
        except:
            pass

        self.columns['glade'] = True
        for db in config.content_metadata_dbs:
            if os.path.isfile("/data/web/datasets/" + self.dsid + "/metadata/customize." + db):
                self.union_urls['web_files'] = fb['web'].substitute(dsid=self.dsid)
                self.union_urls['glade'] = fb['glade'].substitute(dsid=self.dsid)

        if not 'web_files' in self.union_urls:
            self.union_urls['web_files'] = sl['web'].substitute(dsid=self.dsid)
            self.union_urls['glade'] = sl['glade'].substitute(dsid=self.dsid)

        return web_data

    def get_download_file_data(self):
        q = "select dwebcnt, inet_access, locflag from dssdb.dataset as d left join search.datasets as s on s.dsid = d.dsid where s.dsid = %s"
        res_tup = my_execute(self.cursor, q, (self.dsid, ), ResultType.ONE)
        if not res_tup[1] is None or res_tup[0] is None:
            self.error.set("Server Error", "Database error", "get_download_file_data")
            return {}

        if res_tup[0][0] == 0 or res_tup[0][1] == "N":
            self.error.set("No Public Access", "This dataset contains data files that are not currently publicly accessible. For assistance, please <a href=\"/contact-us/\">submit a request</a> for access to the data in this dataset. Be sure to include the dataset title in your request.", None)
            return {}
        
        return self.fill_download_file_data(res_tup[0])

    def set_custom_request_data(self):
        q = "select url, rqsttype from dssdb.rcrqst where dsid in %s and gindex = 0"
        res_tup = my_execute(self.cursor, q, (tuple(slug_list(self.dsid)), ), ResultType.MANY)
        if not res_tup[1] is None:
            logger.debug("res_tup: {0}, {1}".format(res_tup[0], res_tup[1]))
            sys.stderr.write("ERROR set_custom_request_data(): '" + res_tup[1] + "' for '" + self.dsid + "'\n")
            self.error.set("Server Error", "Database error", "set_custom_request_data")
            return

        if not res_tup[0] is None:
            for result in res_tup[0]:
                if result[0]:
                    if result[1] in {"S", "T"}:
                        self.union_urls['subset'] = result[0]
                        if self.union_urls['subset'].find("/cgi-bin/datasets/getSubset") >= 0:
                            self.union_urls['subset'] = "/datasets/" + self.dsid + "/facbrowse/subset/customize/"
                        elif re.search("^/datasets/ds.*\.(php|html).*$", self.union_urls['subset']):
                            self.union_urls['subset'] = "/php" + self.union_urls['subset']

                        self.columns['subset'] = True
                    elif result[1] == "N":
                        self.union_urls['dap'] = result[0]
                        self.columns['other'] = True
                    elif result[1] == "F":
                        """
                        This means global format conversion with specified URL.
                        """
                        self.columns['data_format_conversion'] = DataFormatConversionType.GLOBAL.value
                        self.union_urls['data_format_conversion'] = result[0]

                elif result[1] == "F":
                    """
                    This means global format conversion with default URL.
                    """
                    self.columns['data_format_conversion'] = DataFormatConversionType.GLOBAL.value
                    self.union_urls['data_format_conversion'] = sl['data_format_conversion'].substitute(dsid=self.dsid)

    def set_group_data(self, results, group_dict):
        for result in results:
            gindex = result[0]
            if gindex in group_dict:
                if not 'urls' in group_dict[gindex]:
                    group_dict[gindex]['urls'] = {}

                rtyp = result[1]
                if rtyp in {"S", "T"}:
                    group_dict[gindex]['urls']['subset'] = result[2]
                    if group_dict[gindex]['urls']['subset'].find("/cgi-bin/datasets/getSubset") >= 0:
                        group_dict[gindex]['urls']['subset'] = "/datasets/" + self.dsid + "/facbrowse/subset/customize/"
                    elif re.search("^/datasets/ds.*\.(php|html).*$", group_dict[gindex]['urls']['subset']):
                        group_dict[gindex]['urls']['subset'] = "/php" + group_dict[gindex]['urls']['subset']

                    if group_dict[gindex]['urls']['subset'].find("?") >= 0:
                        group_dict[gindex]['urls']['subset'] += '&gindex=' + str(gindex)
                    else:
                        group_dict[gindex]['urls']['subset'] += '?gindex=' + str(gindex)

                    self.columns['subset'] = True
                elif rtyp == "N":
                    group_dict[gindex]['urls']['dap'] = result[2]
                    self.columns['other'] = True
                elif rtyp == "F" and result[2] is None:
                    """
                    This means only group-specific format conversion. 'url'
                    should be null. Use the url from config.
                    """
                    group_dict[gindex]['urls']['data_format_conversion'] = sl['data_format_conversion'].substitute(dsid=self.dsid) + '/' + str(gindex) + '?converted=True'
                    self.columns['data_format_conversion'] = DataFormatConversionType.GROUP.value

    def fill_group_data(self, results):
        group_dict = {}
        for result in results:
            group_dict[result[0]] = {'index': result[0], 'title': result[1], 'dwebcnt': result[2], 'nwebcnt': result[3]}

        q = "select gindex, rqsttype, url from dssdb.rcrqst where dsid in %s and gindex != 0"
        res_tup = my_execute(self.cursor, q, (tuple(slug_list(self.dsid)), ), ResultType.MANY)
        if not res_tup[1] is None or res_tup[0] is None:
            self.error.set("Server Error", "Database error", "fill_group_data")
            return {}

        if len(res_tup[0]) > 0:
            self.set_group_data(res_tup[0], group_dict)

        group_data = []
        for key in group_dict:
            group_data.append(group_dict[key])
        # Put ARCO data at end
        group_data = sorted(group_data, key=lambda group:group['index'] if group['index'] >=0 else group['index'] * -1000000)
        return group_data

    def get_group_data(self):
        q = "select gindex, title, dwebcnt, nwebcnt from dssdb.dsgroup where dsid in %s and pindex = 0 and ((dwebcnt > 0 or nwebcnt > 0) or gindex < 0) order by gindex"
        res_tup = my_execute(self.cursor, q, (tuple(slug_list(self.dsid)), ), ResultType.MANY)
        if not res_tup[1] is None:
            self.error.set("Server Error", "Database error", "get_group_data")
            return {}

        if not res_tup[0] is None and len(res_tup[0]) > 1:
            """The dataset needs to have more than one group for the matrix to
            have a row for each group.
            """
            return self.fill_group_data(res_tup[0])

        return {}

    def get_grid_template_columns(self):
        template = ''
        width = 100
        if self.group_data:
            width -= 25
            template += '2% 23% '

        if 'glade' in self.columns:
            width -= 2

        num_cols = len(self.columns)
        col_width = width / num_cols
        end = num_cols - 1 if 'glade' in self.columns else num_cols
        for x in range(end):
            template += str(col_width) + '% '

        if 'glade' in self.columns:
            template += '2% ' + str(col_width) + '% '

        return template[:-1]

    def get_header(self):
        """Returns a JSON representation of the data access matrix header row.
        """
        header = {}
        next_col = 3 if self.group_data else 1
        n_dfil = 0
        if 'web_files' in self.columns:
            n_dfil += 1

        if 'globus' in self.columns:
            n_dfil += 1

        if 'data_format_conversion' in self.columns:
            n_dfil += 1

        if n_dfil > 0:
            header['dfil_span'] = str(next_col) + ' / '
            next_col += n_dfil
            header['dfil_span'] += str(next_col)

        if 'subset' in self.columns:
            header['creq_col'] = next_col
            next_col += 1

        if 'other' in self.columns:
            header['othr_col'] = next_col
            next_col += 1

        if 'glade' in self.columns:
            header['spc_col'] = next_col
            next_col += 1
            header['ncar_col'] = next_col
            next_col += 1

        return header

    def to_json(self):
        """Returns a JSON representaton of the data access matrix."""
        if self.error:
            return {'matrix': self.error.to_json()}
        else:
            matrix = {}
            matrix['dsid'] = self.dsid
            matrix['duser'] = self.duser
            matrix['columns'] = self.columns
            matrix['union_urls'] = self.union_urls
            matrix['row_end'] = 4 + len(self.group_data)
            if len(self.group_data) > 0:
                matrix['group_data'] = self.group_data

            matrix['grid_template_columns'] = self.get_grid_template_columns()
            matrix['header'] = self.get_header()
            return {'matrix': matrix}

    class Error:
        header = ""
        message = ""
        module = ""

        def __bool__(self):
            return len(self.message) > 0

        def set(self, header, message, module):
            self.header = header
            self.message = message
            self.module = module

        def to_json(self):
            return {'error': {'header': self.header, 'message': self.message, 'module': self.module}}


def get_globus_share(duser, dsnum, cursor):
    """Returns the globus share for the dataset, if the user has already set
    one up.
    """
    share_data = {}
    q = "select globus_url from dssdb.goshare where email = %s and dsid = concat('ds', %s) and status = 'ACTIVE'"
    res_tup = my_execute(cursor, q, (duser, dsnum), ResultType.ONE)
    if not res_tup[1] is None:
        share_data['error_header'] = "Server Error"
        share_data['error_message'] = "Database error (get_globus_share)"
        return share_data

    if not res_tup[0] is None:
        result = res_tup[0]
        if result[0]:
            share_data['share'] = result[0]

    return share_data

def my_execute(cursor, query, params_tuple, result_type):
    """Tries to execute a query with given parameters and ResultType. Returns a
    tuple as (Result(s), Error). "Error=None" means query was successful.
    """
    try:
        cursor.execute(query, params_tuple)
        if result_type is ResultType.ONE:
            return (cursor.fetchone(), None)
        elif result_type is ResultType.MANY:
            return (cursor.fetchall(), None)
        else:
            return (None, 'Undefined ResultType')

    except psycopg2.Error as err:
        return (None, str(err))
