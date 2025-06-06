import random
import re
import string

from .utils import trim


def soundex(word):
    if len(word) == 0 or not word.isalpha():
        return ""

    head = word[0:1].upper()
    tail = (word[1:].upper()
            .replace("A", "")
            .replace("E", "")
            .replace("I", "")
            .replace("O", "")
            .replace("U", "")
            .replace("H", "")
            .replace("W", "")
            .replace("Y", "")
            .replace("B", "1")
            .replace("F", "1")
            .replace("P", "1")
            .replace("V", "1")
            .replace("C", "2")
            .replace("G", "2")
            .replace("J", "2")
            .replace("K", "2")
            .replace("Q", "2")
            .replace("S", "2")
            .replace("X", "2")
            .replace("Z", "2")
            .replace("D", "3")
            .replace("T", "3")
            .replace("L", "4")
            .replace("M", "5")
            .replace("N", "5")
            .replace("R", "6"))
    tail = list(tail)
    for x in reversed(range(1, len(tail))):
        if tail[x] == tail[x-1]:
            tail[x] = ''

    tail = "".join(tail).ljust(3, "0")
    return (head + tail)


def strand(n):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def cleaned_search_word(word):
    cleaned_word = trim(word).lower()

    # ignore dataset IDs
    if re.compile(r"^d\d{6}$").match(cleaned_word):
        return (True, "", "")

    # ignore full tags
    if cleaned_word[0] == '<' and cleaned_word[-1] == '>':
        return (True, "", "")

    # strip tags from word
    sidx = cleaned_word.find("<")
    eidx = cleaned_word.find(">", sidx+1)
    while len(cleaned_word) > 0 and sidx >= 0 and eidx > 0:
        tag = cleaned_word[sidx:eidx+1]
        cleaned_word = cleaned_word.replace(tag, "")
        sidx = cleaned_word.find("<")
        eidx = cleaned_word.find(">", sidx+1)

    # ignore partial tags
    if cleaned_word[0] == '<':
        return (True, "", "")

    idx = cleaned_word.find(">")
    if idx >= 0:
        cleaned_word = cleaned_word[idx+1:]

    # strip punctuation
    t = strip_punctuation(cleaned_word)
    while t[0]:
        cleaned_word = t[1]
        t = strip_punctuation(cleaned_word)

    if len(cleaned_word) > 1 and cleaned_word[-2:] == "'s":
        cleaned_word = cleaned_word[0:-2]

    # ignore URLs
    url_re = re.compile("^((ht)|(f))tp(s){0,1}://.{1,}$")
    if url_re.match(cleaned_word):
        return (True, "", "")

    return (False, cleaned_word, root_of_word(cleaned_word))


def root_of_word(word):
    while len(word) > 0 and word[-1] in string.digits:
        word = word[:-1]

    if len(word) > 0 and word.isalpha():
        return word

    if len(word) > 1 and word[-2:] in ("is", "es"):
        word = word[:-2]

    if len(word) > 0 and word[-1] == 's':
        word = word[:-1]

    if len(word) > 2 and word[-3:] in ("ing", "ity", "ian"):
        word = word[:-3]

    if len(word) > 1 and word[-2:] in ("ly", "al"):
        word = word[:-2]

    if len(word) > 1 and word[-2:] == ("ic", "ed"):
        word = word[:-2]

    if len(word) > 2 and word[-3:] == "ous":
        word = word[:-3]

    while (len(word) > 1 and (word[-1] == word[-2] or word[-1] in
                              string.digits)):
        word = word[:-1]

    return word


def strip_punctuation(word):
    stripped = False
    while len(word) > 0 and word[0] in (',', ':', '\'', '"', '\\'):
        word = word[1:]
        stripped = True

    while len(word) > 0 and word[-1] in (',', ':', '\'', '"', '\\', '.'):
        word = word[:-1]
        stripped = True

    if len(word) > 0 and word[0] == '(' and word[-1] == ')':
        word = word[1:-1]
        stripped = True

    return (stripped, word)


def to_title(s):
    if not hasattr(to_title, "uncapitalized_words"):
        to_title.uncapitalized_words = (
                "a", "an", "and", "as", "at", "but", "by", "for", "from", "in",
                "is", "nor", "of", "on", "or", "the", "to", "up")

    if len(s) > 0:
        words = s.split()
        for x in range(0, len(words)):
            words[x] = words[x].strip().lower()
            if words[x] not in to_title.uncapitalized_words:
                words[x] = words[x][0:1].upper() + words[x][1:]

    return " ".join(words)
