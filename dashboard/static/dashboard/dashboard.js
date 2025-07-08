function hide(e, b, l, c) {
  let e2 = document.getElementById(b);
  if (e2 != null) {
    e2.innerHTML = "Manage " + l;
    if (e == null) {
      e2.style.display = "none";
      e2.classList.replace('d-block', 'd-none');
    }
  }
  if (e == null) {
    e = document.getElementById(c);
  }
  e.style.display = "none";
  e.classList.replace('d-block', 'd-none');
  e.innerHTML = '<center><img src="/images/browse_wait.gif" class="w-auto h-auto"></center>';
}

function buttonDisplay(sid) {
  let count = document.getElementById(sid + '_count').innerHTML;
  let button = document.getElementById(sid + '_button');
  if (count == "no") {
    button.classList.add('d-none');
    document.getElementById(sid).classList.add('d-none');
  } else {
    button.classList.remove('d-none');
  }
}

function toggleCitation() {
  let e = document.getElementById('mycitation');
  e.innerHTML = '<div class="text-center mt-3" id="loading"><strong>Loading ... &nbsp;&nbsp;</strong><div class="spinner-border text-primary" role="status"><span class="sr-only">Loading...</span></div></div>';
  if (e.classList.contains('d-none')) {
    e.classList.replace('d-none', 'd-block');
    document.getElementById('cite_button').innerHTML = "Hide Citation Tool";
    getContent("mycitation", "/php/ajax/mydatacitation.php");
  } else {
    e.classList.replace('d-block', 'd-none');
    document.getElementById('cite_button').innerHTML = "Show Citation Tool";
  }
}

var spec_reqs_already_open=false;
months = new Array("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec");
timezones = new Array("", "", "", "", "", "", "MDT", "MST");

function toggleControlledRequests() {
  if (spec_req_button == null) {
    spec_req_button = document.getElementById('spec_req_button');
  }
  document.getElementById('specreqs').innerHTML = '<div class="text-center mt-3" id="loading"><strong>Loading ... &nbsp;&nbsp;</strong><div class="spinner-border text-primary" role="status"><span class="sr-only">Loading...</span></div></div>';
  let e = document.getElementById('myspecreqs');
  if (e.classList.contains('d-none')) {
    if (spec_reqs_already_open) {
      return;
    }
    spec_reqs_already_open = true;
    spec_req_button.innerHTML = "Hide Requests";
    e.classList.replace('d-none', 'd-block');
    getContent("specreqs", "/php/ajax/ckrqst.php", null, function() {
    document.getElementById('specreqs-refresh').classList.replace('d-none', 'd-block');
    date = new Date();
    document.getElementById('specreqs-refresh-date').innerHTML = "Information valid as of " + ("0" + date.getDate()).slice(-2) + " " + months[date.getMonth()] + " " + date.getFullYear() + " " + ("0" + date.getHours()).slice(-2) + ":" + ("0" + date.getMinutes()).slice(-2) + ":" + ("0" + date.getSeconds()).slice(-2) + " " + timezones[date.getTimezoneOffset() / 60];
    });
  } else {
    spec_req_button.innerHTML = "Show Requests";
    e.classList.replace('d-block', 'd-none');
    document.getElementById('specreqs-refresh').classList.replace('d-block', 'd-none');
    spec_reqs_already_open = false;
  }
}

function refreshControlledRequests() {
  let e = document.getElementById('myspecreqs');
  if (e.classList.contains('d-block')) {
    getContent("specreqs", "/php/ajax/ckrqst.php", null, function () {
      date = new Date();
      document.getElementById('specreqs-refresh-date').innerHTML = "Information valid as of " + ("0" + date.getDate()).slice(-2) + " " + months[date.getMonth()] + " " + date.getFullYear() + " " + ("0" + date.getHours()).slice(-2) + ":" + ("0" + date.getMinutes()).slice(-2) + ":" + ("0" + date.getSeconds()).slice(-2) + " " + timezones[date.getTimezoneOffset() / 60];
    });
  }
}

function refreshForVersion() {
  if (document.getElementById('poll_version').innerHTML == dashboard_version) {
    getAjaxContent('GET', null, 'bookmarks/count/', 'bookmarks_count', null, bookmarksDisplay)
    getAjaxContent('GET', null, 'requests/count/', 'requests_count', null, requestsDisplay)
    getAjaxContent('GET', null, 'aggregations/count/', 'aggregations_count', null, aggregationsDisplay)
  } else {
    location.reload(true);
  }
}

function updateInfo() {
  getAjaxContent("GET", null, "version/", "poll_version", null, refreshForVersion);
}

setInterval("updateInfo()", 300000);
