import psycopg2
import re
import string

from django.conf import settings

from .config import spellchecker_settings as sc_settings
from . import utils


class SpellChecker:
    def __init__(self):
        self._word_valids = ()
        self._acronym_valids = ()
        self._exact_match_valids = ()
        self._units_valids = ()
        self._file_ext_valids = ()
        self._misspelled_words = []
        self._error = ""
        try:
            conn = psycopg2.connect(**sc_settings['db_config'])
            cursor = conn.cursor()
            self._word_valids += self.fill_valids(cursor, "word_valids", "word")
            self._word_valids += self.fill_valids(cursor, "non_english_valids", "word")
            self._acronym_valids += self.fill_valids(cursor, "acronym_valids", "word")
            self._exact_match_valids += self.fill_valids(cursor, "acronym_valids", "description")
            self._exact_match_valids += self.fill_valids(cursor, "place_valids", "word")
            self._exact_match_valids += self.fill_valids(cursor, "name_valids", "word")
            self._exact_match_valids += self.fill_valids(cursor, "other_exactmatch_valids", "word")
            self._units_valids += self.fill_valids(cursor, "unit_valids", "word")
            self._file_ext_valids += self.fill_valids(cursor, "file_ext_valids", "word")
            self._initialized = True
        except Exception as err:
            self._initialized = False
            self._error = err


    def __del__(self):
        del self._word_valids
        del self._acronym_valids
        del self._exact_match_valids
        del self._units_valids
        del self._file_ext_valids


    @property
    def initialized(self):
        return self._initialized


    @property
    def error(self):
        return self._error


    @property
    def misspelled_words(self):
        return self._misspelled_words


    def fill_valids(self, cursor, table, column):
        try:
            cursor.execute("select " + column + " from " + sc_settings['valids_schema'] + "." + table)
            res = cursor.fetchall()
            return tuple(e[0] for e in res)
        except Exception as err:
            raise Exception("error filling valids table '{}': '{}'".format(table, err))


    def check(self, text):
        check_text = text
        check_text = check_text.replace("\n", " ").replace("\u2010", "-")
        check_text = utils.trim(check_text)

        # check the words case-insensitive against the regular words
        self._misspelled_words = unknown(check_text, self._word_valids, icase=True, file_ext_valids=self._file_ext_valids)
        if len(self._misspelled_words) > 0:
            check_text = self.new_text(check_text)

            # check the words directly against the acronyms, trimming plurals
            self._misspelled_words = unknown(check_text, self._acronym_valids, trimPlural=True)

        if len(self._misspelled_words) > 0:
            check_text = self.new_text(check_text)

            # check the words directly against the exact match valids
            self._misspelled_words = unknown(check_text, self._exact_match_valids)

        if len(self._misspelled_words) > 0:
            check_text = self.new_text(check_text)
            if text.find("-") >= 0:
                # check compound (hyphen) words case-insensitive against the regular words
                self._misspelled_words = unknown(check_text, self._word_valids, separator="-", icase=True)

        if len(self._misspelled_words) > 0:
            check_text = self.new_text(check_text)
            if text.find("\u2013") >= 0:
                # check compound (unicode En-dash) words case-insensitive against the regular words
                self._misspelled_words = unknown(check_text, self._word_valids, separator="\u2013", icase=True)

        if len(self._misspelled_words) > 0:
            check_text = self.new_text(check_text)
            if text.find("/") >= 0:
                # check compound (slash) words case-insensitive against the regular words
                self._misspelled_words = unknown(check_text, self._word_valids, separator="/", icase=True)

        if len(self._misspelled_words) > 0:
            check_text = self.new_text(check_text)
            if text.find("/") >= 0:
                # check compound (slash) words directly against the acronyms
                self._misspelled_words = unknown(check_text, self._acronym_valids, separator="/")

        if len(self._misspelled_words) > 0:
            check_text = text
            check_text = check_text.replace("\n", " ")
            check_text = utils.trim(check_text)
            check_text = self.new_text(check_text, includePrevious=True)
            # check words directly against the units valids
            self._misspelled_words = unknown(check_text, self._units_valids, units=True)

        if len(self._misspelled_words) > 0:
            check_text = self.new_text(check_text)
            if text.find("_") >= 0:
                # check snake_case words case-insensitive against the regular words
                self._misspelled_words = unknown(check_text, self._word_valids, separator="_", icase=True)



    def new_text(self, text, **kwargs):
        if 'includePrevious' in kwargs and kwargs['includePrevious']:
            words = text.split()
            text = ""
            if words[0] == self._misspelled_words[0]:
                text = "XX " + self._misspelled_words[0]
                midx = 1
            else:
                midx = 0

            for n in range(1, len(words)):
                if midx == len(self._misspelled_words):
                    break

                if self._misspelled_words[midx] in (words[n], clean_word(words[n]), trim_punctuation(words[n]), utils.trim(words[n])):
                    text += " " + words[n-1] + " " + self._misspelled_words[midx]
                    midx += 1

            return text

        return " ".join(self._misspelled_words)


def trim_plural(text):
    text = text.replace(u"\u2019", "'")
    if text[-2:] == "'s":
        return text[:-2]

    if text[-1:] == "s":
        return text[:-1]

    return text


def trim_punctuation(text):
    c = text[-1]
    while len(text) > 0 and c in (".", ",", ":", ";", "?", "!"):
        text = text[:-1]
        if len(text) > 0:
            c = text[-1]

    return text


def unknown(text, valids, **kwargs):
    misspelled_words = []
    words = text.split()
    icase = kwargs['icase'] if 'icase' in kwargs else False
    checking_units = kwargs['units'] if 'units' in kwargs else False
    separator = kwargs['separator'] if 'separator' in kwargs else ""
    file_ext_valids = kwargs['file_ext_valids'] if 'file_ext_valids' in kwargs else None
    n = 0 if not checking_units else 1
    while n < len(words):
        words[n] = clean_word(words[n])
        if words[n] not in misspelled_words:
            cword = words[n]
            if 'trimPlural' in kwargs and kwargs['trimPlural']:
                cword = trim_plural(cword)

            if check_word(cword, file_ext_valids):
                if cword[0:4] == "non-":
                    cword = cword[4:]

                if icase:
                    cword = cword.lower()

                if len(separator) == 0:
                    if checking_units:
                        if cword in valids:
                            pword = utils.trim_front(words[n-1]) if n > 0 else "XX"
                            if pword == "et" and cword == "al":
                                pass
                            elif not pword.replace(".", "").isnumeric():
                                misspelled_words.append(words[n])
                        else:
                            if n > 0:
                                if len(cword) == 1 and cword.isalpha() and cword == cword.upper() and words[n-1].lower() == "station":
                                    # allow for e.g. 'Station P'
                                    pass

                                else:
                                    misspelled_words.append(words[n])

                            else:
                                misspelled_words.append(words[n])

                        n += 1
                    else:
                        if cword[-2:] == "'s":
                            cword = cword[:-2]

                        if cword not in valids:
                            misspelled_words.append(words[n])

                else:
                    parts = cword.split(separator)
                    m = 0
                    failed = False
                    while m < len(parts):
                        if check_word(parts[m], file_ext_valids) and parts[m] not in valids:
                            if parts[m][-2:] == "'s":
                                if parts[m][:-2] not in valids:
                                    failed = True
                                    break

                            else:
                                failed = True

                        m += 1

                    if failed:
                        misspelled_words.append(words[n])

        n += 1

    return misspelled_words


def check_word(word, file_ext_valids):
    if len(word) == 0:
        return False

    if word[0] == '#':
        word = word[1:]

    # ignore numbers, including floating point and currency numbers
    if word.replace(".", "").replace(",", "").isnumeric():
        return False

    # ignore acronyms containing all capital letters and numbers
    if word.isalpha() and word == word.upper():
        return False

    # ignore ratios (e.g. 9:3)
    if word.replace(":", "").isnumeric():
        return False

    # ignore e.g. 1900s
    if word[-1] == "s" and word[:-1].isnumeric():
        return False

    if word[-2:] == "st" and word[:-2].isnumeric() and word[-3] == "1":
        return False

    if word[-2:] == "nd" and word[:-2].isnumeric() and word[-3] == "2":
        return False

    if word[-2:] == "rd" and word[:-2].isnumeric() and word[-3] == "3":
        return False

    if word[-2:] == "th" and word[:-2].isnumeric() and word[-3] in ("0", "4", "5", "6", "7", "8", "9"):
        return False

    # ignore NG-GDEX dataset IDs
    if len(word) == 7 and word[0] == "d" and word[1:].isnumeric():
        return False

    # ignore e.g. pre-1950
    if word[0:4] == "pre-" and word[4:].isnumeric():
        return False

    # ignore version numbers e.g. v2.0, 0.x, 1a
    if word[0] == "v" and word[1:].replace(".", "").isnumeric():
        return False

    if word[-2:] == ".x" and word[:-2].isnumeric():
        return False

    rexp = re.compile("^[0-9]{1,}[a-z]{1,}$")
    if rexp.match(word):
        return False

    # ignore NCAR Technical notes
    rexp = re.compile("^NCAR/TN-([0-9]){1,}\+STR$")
    if rexp.match(word):
        return False

    # ignore itemizations
    rexp = re.compile("^[a-zA-Z][\.)]$")
    if rexp.match(word):
        return False

    # ignore references
    rexp = re.compile("^\([a-zA-Z0-9]\)$")
    if rexp.match(word):
        return False

    rexp = re.compile("^\([ivx]{1,}\)$")
    if rexp.match(word):
        return False

    # ignore email addresses
    rexp = re.compile("^(.){1,}@(.){1,}\.(.){1,}$")
    if rexp.match(word):
        return False

    # ignore file extensions
    rexp = re.compile("^\.([a-zA-Z0-9]){1,10}$")
    if rexp.match(word):
        return False

    # ignore file names
    idx = word.rfind(".")
    if idx > 0 and file_ext_valids != None and word[idx+1:] in file_ext_valids:
        return False

    # ignore acronyms like TS1.3B.4C
    rexp = re.compile("^[A-Z0-9]{1,}(\.[A-Z0-9]{1,}){0,}$")
    if rexp.match(word):
        return False

    # ignore URLs
    rexp = re.compile("^\[{0,1}https{0,1}://")
    if rexp.match(word):
        return False

    rexp = re.compile("^\[{0,1}ftp://")
    if rexp.match(word):
        return False

    rexp = re.compile("^\[{0,1}mailto:")
    if rexp.match(word):
        return False

    # ignore DOIs
    rexp = re.compile("^10\.\d{4,}/.{1,}$")
    if rexp.match(word):
        return False

    return True


def clean_word(word):
    if len(word) == 0:
        return ""

    # strip html entities
    entity = re.compile("&\S{1,};")
    m = entity.findall(word)
    for e in m:
        word = word.replace(e, "")

    if len(word) == 0:
        return ""

    word = trim_punctuation(word)
    if len(word) == 0:
        return ""

    cleaned_word = False
    if word[0] in ('"', '\''):
        word = word[1:]
        cleaned_word = True

    if word[0] == '(' and (word[-1] == ')' or word.find(")") < 0):
        word = word[1:]
        cleaned_word = True

    if word[-1] in (',', '"', '\''):
        word = word[:-1]
        if len(word) == 0:
            return

        cleaned_word = True

    rexp = re.compile("\(s\)$")
    if word[-1] == ")" and not rexp.search(word):
        word = word[:-1]
        if len(word) == 0:
            return

        cleaned_word = True

    if len(word) >= 2 and word[-2:] == ").":
        word = word[:-2]
        if len(word) == 0:
            return

        cleaned_word = True

    if len(word) >= 2 and word[-2] == "-" and word[-1] in string.ascii_uppercase:
        word = word[:-2]
        if len(word) == 0:
            return

        cleaned_word = True

    if cleaned_word:
        word = clean_word(word)

    return word
