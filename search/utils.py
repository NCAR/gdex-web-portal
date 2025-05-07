import psycopg2
import re
import sys

from django.conf import settings

from .word_lists import word_lists


class IndexableDatasets:
    def __init__(self):
        self.map = {}
        try:
            conn = psycopg2.connect(**settings.RDADB['search_config_pg'])
            cursor = conn.cursor()
            cursor.execute((
                    "select dsid, type, title, summary from search.datasets "
                    "where type in ('P', 'H') and dsid not like 'd999%'"))
            res = cursor.fetchall()
            for row in res:
                self.map[row[0]] = {'type': row[1], 'title': row[2],
                                    'summary': row[3]}

        except BaseException as err:
            sys.stderr.write("INDEXABLEDATASETS EXCEPTION - '{}'\n"
                             .format(err))


class SearchWords:
    soundex_map = {
        'A': '', 'E': '', 'I': '', 'O': '', 'U': '', 'H': '', 'W': '', 'Y': '',
        'B': '1', 'F': '1', 'P': '1', 'V': '1',
        'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2',
        'Z': '2',
        'D': '3', 'T': '3',
        'L': '4',
        'M': '5', 'N': '5',
        'R': '6',
    }

    def root_of_word(word):
        if not word or not word.isalpha():
            return ""

        if word[len(word)-3:len(word)] == "ous":
            word = word[0:len(word)-3]

        if word[len(word)-2:len(word)] == "is":
            word = word[0:len(word)-2]

        if word[len(word)-2:len(word)] == "es":
            word = word[0:len(word)-2]

        if word[len(word)-1:len(word)] == "s":
            word = word[0:len(word)-1]

        if word[len(word)-3:len(word)] == "ing":
            word = word[0:len(word)-3]

        if word[len(word)-3:len(word)] == "ity":
            word = word[0:len(word)-3]

        if word[len(word)-3:len(word)] == "ian":
            word = word[0:len(word)-3]

        if word[len(word)-2:len(word)] == "ly":
            word = word[0:len(word)-2]

        if word[len(word)-2:len(word)] == "al":
            word = word[0:len(word)-2]

        if word[len(word)-2:len(word)] == "ic":
            word = word[0:len(word)-2]

        if word[len(word)-2:len(word)] == "ed":
            word = word[0:len(word)-2]

        chars = [c for c in word]
        for x in range(len(chars)-1, 0, -1):
            if chars[x] == chars[x-1]:
                chars.pop(x)

        return ''.join(chars)

    @classmethod
    def soundex(cls, word):
        if not word or not word.isalpha():
            return ""

        head = word[0:1].upper()
        tail = word[1:].upper()
        schars = [cls.soundex_map[c] for c in tail if cls.soundex_map[c]]
        for x in range(len(schars)-1, 0, -1):
            if schars[x] == schars[x-1]:
                schars.pop(x)

        while len(schars) < 3:
            schars.append('0')

        return (head + ''.join(schars))

    def compound_separator(word):
        if word.find("-") > 0:
            return "-"

        if word.find("/") > 0:
            return "/"

        if word.find(";") > 0:
            return ";"

        return ""


class SearchResults:
    def __init__(self, request):
        self.result_set = {}
        self.unmatched_terms = {}
        self.exclude_set = {}
        self.request = request
        words = self.request.GET['words'].split()
        self.include_words = []
        self.exclude_words = []
        for word in words:
            if word[0] == '-':
                self.exclude_words.append(word[1:])
            else:
                self.include_words.append(word)
                self.unmatched_terms[word] = True

        self.results = {'P': [], 'H': []}
        self.error = False
        self.show_adv = False
        self.startd = ""
        self.min_startd = ""
        self.endd = ""
        self.max_endd = ""
        self.tres = []
        self.fmts = []
        self.indexable_datasets = IndexableDatasets()
        self.fill_datasets()

    def fill_datasets(self):
        # check for word that is a dataset number
        if len(self.include_words) == 1 and len(self.exclude_words) == 0:
            # check for an old dataset number
            if re.compile(r"^ds[0-9]{3}\.[0-9]$").match(self.include_words[0]):
                self.include_words[0] = ("d" + self.include_words[0][2:5] +
                                         "00" + self.include_words[0][6:7])

            if re.compile("^d[0-9]{6}$").match(self.include_words[0]):
                if self.include_words[0] in self.indexable_datasets.map:
                    d = self.indexable_datasets.map[self.include_words[0]]
                    self.results[d['type']].append(
                            {'dsid': self.include_words[0], 'type': d['type'],
                             'title': d['title'], 'summary': d['summary']})
                    return

        try:
            conn = psycopg2.connect(**settings.RDADB['search_config_pg'])
            cursor = conn.cursor()
        except psycopg2.Error as err:
            sys.stderr.write("DSSEARCH EXCEPTION - Database error: '{}'\n"
                             .format(err))
            self.error = True
        except BaseException as err:
            sys.stderr.write("DSSEARCH EXCEPTION - '{}'\n".format(err))
            self.error = True

        for list in word_lists:
            self.use_wordlist_to_modify_results(
                    list['db'], list['table'], list['weight'], cursor)
            if len(self.exclude_words) > 0:
                self.use_wordlist_to_modify_results(
                        list['db'], list['table'], -1., cursor)

        n = len(self.include_words)
        del_list = []
        dlst = []
        for key in self.result_set:
            if (key in self.exclude_set or
                    len(self.result_set[key]['matched_words']) != n):
                del_list.append(key)
            else:
                dlst.append("'" + key + "'")

        for key in del_list:
            del self.result_set[key]

        if len(self.result_set) == 0:
            return

        dset = ", ".join(dlst)
        cursor.execute((
                "select distinct t.keyword, s.idx from search."
                "time_resolutions as t left join search.time_resolution_sort "
                "as s on s.keyword = t.keyword where t.dsid in (" + dset + ") "
                "order by s.idx"))
        res = cursor.fetchall()
        for row in res:
            self.tres.append(row[0])

        cursor.execute((
                "select distinct keyword from search.formats where dsid in (" +
                dset + ") order by keyword"))
        res = cursor.fetchall()
        for row in res:
            self.fmts.append(row[0])

        cursor.execute((
                "select min(date_start), max(date_end) from dssdb.dsperiod "
                "where dsid in (" + dset + ") and date_start >= '1000-01-01' "
                "and date_end <= '3000-12-31'"))
        res = cursor.fetchone()
        if res[0] is not None:
            self.min_startd = res[0].strftime("%Y-%m")
            self.max_endd = res[1].strftime("%Y-%m")

        self.filter_by_date_range(cursor)
        s = sorted(self.result_set.items(), key=lambda item: item[1]['rating'],
                   reverse=True)
        for t in s:
            d = self.indexable_datasets.map[t[0]]
            self.results[d['type']].append(
                    {'dsid': t[0], 'type': d['type'], 'title': d['title'],
                     'summary': d['summary']})

        if len(self.startd) == 0:
            self.startd = self.min_startd

        if len(self.endd) == 0:
            self.endd = self.max_endd

    def use_wordlist_to_modify_results(self, db, table, weight, cursor):
        rate_by_location = False
        if len(db) > 0:
            cursor.execute((
                    "select column_name from information_schema.columns where "
                    "table_schema = '" + db + "' and table_name = '" + table +
                    "' and column_name = 'location'"))
            res = cursor.fetchall()
            if len(res) > 0 and res[0][0] == "location":
                rate_by_location = True

        search_words = (self.include_words if weight > 0. else
                        self.exclude_words)
        for word in search_words:
            wc = "word ilike '" + word + "'"
            if weight > 0.:
                rword = SearchWords.root_of_word(word)
                if rword:
                    wc += (" or (word ilike '" + rword + "%' and sword = '" +
                           SearchWords.soundex(rword) + "')")

            if rate_by_location:
                q = ("select dsid, location, word from \"" + db + "\"." + table
                     + " where " + wc)
            else:
                if len(db) > 0:
                    q = ("select dsid, count(keyword), keyword from \"" + db +
                         "\". " + table + " where keyword ilike '%" + word +
                         "%' group by dsid, keyword")
                else:
                    q = ("select dsid, count(keyword), keyword from " + table +
                         " where keyword ilike '%" + word + "%' group by "
                         "dsid, keyword")

            cursor.execute(q)
            res = cursor.fetchall()
            if len(res) > 0 and word in self.unmatched_terms:
                del self.unmatched_terms[word]

            for row in res:
                if row[0] in self.indexable_datasets.map:
                    if weight > 0.:
                        if row[0] not in self.result_set:
                            self.result_set[row[0]] = (
                                    {'rating': 0., 'locations': [],
                                     'matched_words': []})

                        if rate_by_location:
                            if word == row[2]:
                                self.result_set[row[0]]['rating'] += weight
                            else:
                                self.result_set[row[0]]['rating'] += (
                                        weight * 0.5)

                            self.result_set[row[0]]['locations'].append(
                                    int(row[1]))
                        else:
                            if word == row[2]:
                                self.result_set[row[0]]['rating'] += (
                                        float(row[1]) * weight)
                            else:
                                self.result_set[row[0]]['rating'] += (
                                        float(row[1]) * weight * 0.5)

                        if (word not in
                                self.result_set[row[0]]['matched_words']):
                            self.result_set[row[0]]['matched_words'].append(
                                    word)
                    else:
                        self.exclude_set[row[0]] = True

        if weight > 0.:
            for key in self.result_set:
                if len(self.result_set[key]['locations']) > 0:
                    locs = self.result_set[key]['locations']
                    for x in range(0, len(locs)):
                        for y in range(x+1, len(locs)):
                            diff = locs[y] - locs[x]
                            if diff < 0 or diff > 100:
                                diff = 100
                            else:
                                diff -= 1

                            self.result_set[key]['rating'] += (
                                    1. / pow(2., diff) * weight)

                    locs.clear()

    def filter_by_date_range(self, cursor):
        dates = []
        if ('startd' in self.request.GET and len(self.request.GET['startd']) >
                0):
            self.startd = self.request.GET['startd']
            dates.append("date_end >= '" + self.request.GET['startd'] + "-01'")
            self.show_adv = True

        if 'endd' in self.request.GET and len(self.request.GET['endd']) > 0:
            self.endd = self.request.GET['endd']
            parts = self.request.GET['endd'].split("-")
            parts[0] = int(parts[0])
            parts[1] = int(parts[1]) + 1
            if parts[1] > 12:
                parts[0] += 1
                parts[1] = 1

            dates.append((
                    "date_start < '" + str(parts[0]) + "-" +
                    str(parts[1]).zfill(2) + "-01'"))
            self.show_adv = True

        if len(dates) > 0:
            try:
                q = ("select distinct dsid from dssdb.dsperiod where " +
                     " and ".join(dates) + " order by dsid")
                cursor.execute(q)
                res = cursor.fetchall()
                inc_list = []
                for e in res:
                    inc_list.append(e[0])

                del_list = []
                for key in self.result_set:
                    if key not in inc_list:
                        del_list.append(key)

                for key in del_list:
                    del self.result_set[key]

            except BaseException:
                pass

    def to_json(self):
        if self.error:
            return {'error': True}
        else:
            d = {'results': self.results['P'] + self.results['H'],
                 'historical_start': len(self.results['P']),
                 'historical_length': len(self.results['H']),
                 'show_adv': self.show_adv}
            if len(self.tres) > 0:
                d.update({'tres': self.tres})

            if len(self.fmts) > 0:
                d.update({'fmts': self.fmts})

            if len(self.startd) > 0:
                d.update({'date_start': self.startd})

            if len(self.min_startd) > 0:
                d.update({'min_date_start': self.min_startd})

            if len(self.endd) > 0:
                d.update({'date_end': self.endd})

            if len(self.max_endd) > 0:
                d.update({'max_date_end': self.max_endd})

            return d
