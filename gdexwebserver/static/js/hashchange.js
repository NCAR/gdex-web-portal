var hashchange = {
  supported: false,
  loc: document.location,
  hash: '',
  qs: '',
  scroll_to: '',
  poll_interval: null,
  cancel: false,
  action: null,
};

if ("onhashchange" in window) {
  hashchange.supported = true;
  if (window.addEventListener) {
    window.addEventListener("hashchange", respondToHashChange, false);
  } else if (window.attachEvent) {
    window.attachEvent("onhashchange", respondToHashChange);
  }
} else {
  hashchange.supported = false;
  hashchange.poll_interval = setInterval("pollForHashChange()", 100);
}

window.onload = respondToHashChange;

function findAnchor(s) {
  idx = s.indexOf("#");
  if (idx > 0) {
    hashchange.scroll_to = s.substr(idx + 1);
    s = s.substr(0, idx);
  }
}

function decodeHash() {
  hashchange.hash = hashchange.loc.hash.substr(1);

  // '!' is for Google SEO
  if (hashchange.hash.charAt(0) == '!') hashchange.hash =
      hashchange.hash.substr(1);
  idx = hashchange.hash.indexOf("?")
  if (idx > 0) {

    // found a search string
    hashchange.qs = hashchange.hash.substr(idx);
    hashchange.hash = hashchange.hash.substr(0, idx);
    findAnchor(hashchange.qs);
  } else {
    findAnchor(hashchange.hash);
  }
}

function decodeSearch() {
  idx = hashchange.loc.search.indexOf("?hash=");
  if (idx == 0) {
    hashchange.hash = hashchange.loc.search.substr(idx + 6);
    if (hashchange.hash.charAt(0) == '!') hashchange.hash =
        hashchange.hash.substr(1);
    idx = hashchange.hash.indexOf("&");
    if (idx > 0) {
      hashchange.qs = "?" + hashchange.hash.substr(idx + 1);
      hashchange.hash = hashchange.hash.substr(0, idx);
    }
  } else {
    hashchange.qs = hashchange.loc.search;
  }
}

function respondToHashChange() {
  if (hashchange.cancel) {
    hashchange.cancel = false;
    return;
  }
  if (!hashchange.supported) {
    clearInterval(hashchange.poll_interval);
  }

  // any variable initializations that should happen on hashchange go here
  //

  if (hashchange.loc.hash.length > 0) {
    decodeHash();
  } else if (hashchange.loc.search.length > 0) {
    decodeSearch();
  } else {
    if (hashchange.loc.pathname.indexOf("/doi/") == 0) {
      hashchange.hash = "cgi-bin/doi";
      hashchange.qs = "?doi=" + loc.pathname.substr(5, 32768);
    }
  }

  // look for an anchor in the search string
  if (hashchange.scroll_to.length == 0) {
    arr = hashchange.qs.substr(1).split("&");
    for (n = 0; n < arr.length; ++n) {
      if (arr[n].indexOf("scrollTo=") == 0) hashchange.scroll_to =
          arr[n].substr(9);
    }
  }
  if (hashchange.hash.length > 0) {
    if (hashchange.hash == "lfd") {
      document.location = '/lookfordata/';
      return;
    }

    if (hashchange.hash.indexOf("cgi-bin") == 0) {
      getContent(ajax_container, '/' + hashchange.hash + hashchange.qs);
    } else if (hashchange.hash.indexOf("view.") == 0) {
      getContent(ajax_container, hashchange.hash.substr(5));
    } else if (hashchange.hash.indexOf("sfol-") == 0) {
      var type = hashchange.hash.substr(5, 2);
      var url;
      if (type == "wl") {
        url = hashchange.hash.substr(8) + '/index.html';
      } else {
        url = '/datasets/' + hashchange.loc.pathname.substring(10, 17) + '/';
        if (type == "fh") {
          url += 'MSS-format-list.html';
        } else if (type == "fw") {
          url += 'WEB-format-list.html';
        } else if (type == "gl") {
          url += 'GLADE-file-list.html';
        } else if (type == "hl") {
          url += 'MSS-file-list.html';
        } else if (type == "hr") {
          url += 'MSS-rqst-list.html';
        }
      }
      getContent(ajax_container, url + hashchange.qs);
    } else if (hashchange.hash.indexOf("dsrqst") == 0 ||
        hashchange.hash.indexOf("rdadocs") == 0) {
      getContent(ajax_container, '/' + hashchange.hash);
    } else {
      getContent(ajax_container, '/php/ajax/' + hashchange.hash + '.php' +
          hashchange.qs);
    }
    if (hashchange.action != null) hashchange.action();
  }
}
