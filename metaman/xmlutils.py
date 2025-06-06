import re

from . import utils


def convert_html_to_text(html, **kwargs):
    indent_len = kwargs['indentLength'] if 'indentLength' in kwargs else 0
    wrap_length = kwargs['wrapLength'] if 'wrapLength' in kwargs else -1
    html = html.replace("\n", " ")
    html = html.replace("&nbsp;", " ")
    html = html.replace("&deg;", "degree")
    html = html.replace("&lt;", "less than")
    html = html.replace("&gt;", "greater than")
    html = re.sub("<br( ){0,}(/){0,1}>", " ", html)
    while html.find("  ") >= 0:
        html = html.replace("  ", " ")

    nodes = fill_nodes(html)
    text = ""
    for node in nodes:
        node = process_node(node, wrap_length)
        while node['value'][-2:] == "\n\n":
            node['value'] = node['value'][:-1]

        node['value'] = wrap_node_value(node['value'], wrap_length, indent_len)
        text += (" " * indent_len) + node['value'] + "\n"

    text = utils.trim_back(text)
    return text


def fill_nodes(html):
    html = utils.trim(html)
    if html[0] != "<":
        return []

    idx = html.find(" ")
    idx2 = html.find(">")
    if idx > 0 and idx < idx2:
        end_tag = html[0:idx] + ">"
    else:
        end_tag = html[0:idx2+1]

    end_tag = end_tag.replace("<", "</")
    if end_tag != html[-len(end_tag):]:
        return []

    html = html[1:]
    html = html[html.find("<"):]
    html = html[0: len(html)-len(end_tag)]
    if len(html) == 0:
        return []

    nodes = []
    x = xml_split(html)
    n = 0
    while n < len(x):
        if x[n][0] == '<' and x[n][1] != '/' and x[n][-2:] != "/>":
            node = {'copy': x[n], 'value': "", 'nodes': []}
            begin_tag = x[n]
            idx = begin_tag.find(" ")
            if idx > 0:
                begin_tag = begin_tag[0:idx]
            else:
                begin_tag = begin_tag[:-1]

            end_tag = "</" + begin_tag[1:] + ">"
            m = 0
            while n < len(x)-1 and (x[n+1] != end_tag or m > 0):
                n += 1
                idx = x[n].find(" ")
                if ((idx > 0 and x[n][0:idx] == begin_tag) or x[n] ==
                        (begin_tag+">")):
                    m += 1

                if x[n] == end_tag:
                    m -= 1

                node['copy'] += x[n]

            n += 1
            node['copy'] += x[n]
            y = xml_split(node['copy'])
            if len(y) > 3:
                node['nodes'] = fill_nodes(node['copy'])

            nodes.append(node)

        n += 1

    return nodes


def xml_split(xml):
    pos = 0
    bidx = xml.find("<", pos)
    if bidx != 0:
        return []

    tlen = len(xml)
    parts = []
    while pos < tlen and bidx >= 0:
        if bidx == pos:
            eidx = xml.find(">", pos)
            if eidx < 0:
                pos = tlen
            else:
                pos = eidx + 1

            parts.append(xml[bidx:pos])
            bidx = xml.find("<", pos)
        else:
            parts.append(xml[pos:bidx])
            pos = bidx

    return parts


def process_node(node, wrap_length, **kwargs):
    indent = kwargs['indent'] if 'indent' in kwargs else ""
    node['copy'] = node['copy'].replace("> <", "><")
    node['copy'] = node['copy'].replace(". </", ".</")
    node['value'] = node['copy']
    for n in node['nodes']:
        ul = n['copy'].find("<ul>")
        if ul == 0:
            indent += "   "

        n = process_node(n, wrap_length, indent=indent)
        if len(node['value']) > 0:
            node['value'] = node['value'].replace(n['copy'], n['value'])

        if ul == 0:
            indent = indent[:-3]

    if node['copy'].find("<a href=") == 0:
        idx = node['value'][9:].find("\"") + 9
        idx = node['value'][idx:].find(">") + idx
        node['value'] = node['value'][idx+1:]
        node['value'] = node['value'].replace("</a>", "")
        temp = node['copy'][node['copy'].find("href=")+6:]
        idx = temp.find("\"")
        if idx < 0:
            idx = temp.find("'")

        temp = temp[0:idx]
        if temp.find("mailto:") == 0:
            node['value'] = "[" + temp + "]"
        else:
            node['value'] += " [" + temp + "]"

    elif node['copy'].find("<font") == 0:
        node['value'] = node['value'][node['value'].find(">")+1:]
        node['value'] = node['value'].replace("</font>", "")
    elif node['copy'].find("<li>") == 0:
        node['value'] = node['value'].replace("<li>", "")
        node['value'] = node['value'].replace("</li>", "")
        node['value'] = "\n" + indent + "    * " + node['value']
        node['value'] = wrap_node_value(node['value'], wrap_length,
                                        len(indent)+6)
    elif node['copy'].find("<p>") == 0:
        node['value'] = node['value'].replace("<p>", "")
        if node['value'][0] == '\n':
            node['value'] = node['value'][1:]

        node['value'] = node['value'].replace("</p>", "\n")
    elif node['copy'].find("<P>") == 0:
        node['value'] = node['value'].replace("<P>", "")
        node['value'] = node['value'].replace("</P>", "")
        if node['value'][-1] != '\n':
            node['value'] += "\n"

    elif node['copy'].find("<ul>") == 0:
        node['value'] = node['value'].replace("<ul>", "")
        node['value'] = node['value'].replace("</ul>", "\n")
    elif node['copy'][0] == '<':
        idx = node['copy'].find(" ")
        idx2 = node['copy'].find(">")
        if idx < 0 or idx2 < idx:
            temp = node['copy'][1:idx2]
        else:
            temp = node['copy'][1:idx]

        node['value'] = node['value'][idx2+1:]
        node['value'] = node['value'].replace("</" + temp + ">", "")

    return node


def wrap_node_value(node_value, wrap_len, indent_len):
    if wrap_len < 0:
        return node_value

    indent = " " * indent_len
    line_len = wrap_len - indent_len
    n = 0
    while len(node_value[n:]) > line_len:
        idx = node_value[n:].find("\n")
        if idx >= 0 and idx <= line_len:
            n += (idx + 1)
        else:
            m = n
            n += line_len
            while n > m and node_value[n] not in (' ', '\n'):
                n -= 1

            if n == m:
                return node_value

            node_value = indent + node_value[0:n] + "\n" + node_value[n+1:]
            n += 1

    return node_value


def convert_plain_ampersands(text):
    text = text.replace("&", "&Amp;")
    idx = text.find("&Amp;")
    while idx >= 0:
        if text[idx+5:idx+9] == "amp;" or text[idx+5:idx+8] == "gt;":
            text = text[0:idx] + "&" + text[idx+5:]
        else:
            text = text[0:idx+1] + "a" + text[idx+2:]

        idx = text.find("&Amp;")

    return text
