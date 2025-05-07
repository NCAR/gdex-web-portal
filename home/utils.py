def slug_list(dsid):
    if dsid[0] != 'd':
        dsid = "ds" + dsid

    l = [dsid]
    if dsid.find(".") == 5:
        l.extend([dsid.replace(".", "-"), "d" + dsid[2:5] + "00" + dsid[6:7]])

    if dsid.find("-") == 5:
        l.extend([dsid.replace("-", "."), "d" + dsid[2:5] + "00" + dsid[6:7]])

    if dsid[0] == 'd' and len(dsid) == 7 and dsid[1] != 's':
        l.extend(["ds" + dsid[1:4] + "." + dsid[6:7], "ds" + dsid[1:4] + "-" + dsid[6:7]])

    return l
