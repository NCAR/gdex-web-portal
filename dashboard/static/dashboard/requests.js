function requestsDisplay() {
  buttonDisplay("requests");
}

function showRequests(e) {
  var b = document.getElementById('requests_button');
  if (e == null) {

    // from update
    e = document.getElementById('requests');
  } else {

    // from click
    b.innerHTML = "Hide Requests";
  }
  if (e.classList.contains('d-none')) {
    e.classList.replace('d-none', 'd-block');
    getAjaxContent("GET", null, "requests/", "requests");
  }
}

function toggleRequests() {
  let e = document.getElementById('requests');
  e.innerHTML = '<div class="text-center mt-3" id="loading"><strong>Loading ... &nbsp;&nbsp;</strong><div class="spinner-border text-primary" role="status"><span class="sr-only">Loading...</span></div></div>';
  if (e.classList.contains('d-none')) {
    showRequests(e);
  } else {
    hide(e, "requests_button", "Requests", "requests");
  }
}

function extendRequest(r, n, x, t) {
  if (x < n) {
    popModalWindowWithHTML(500, 200, '<center><p>The current purge date is already at least two weeks away, and you can\'t request a date farther out than that.</p></center>');
  } else {
    cal_min_date = n;
    cal_max_date = x;
    popModalWindowWithHTML(500, 250, '<center><p>Use the date picker to choose a different date.</p><form name="extend" action="javascript:void(0)" onsubmit="document.extend.submit.disabled=true;getAjaxContent(\'POST\',\'id='+r+'&date=\'+document.extend.date.value+\'&min_date='+n+'&csrfmiddlewaretoken='+t+'\',\'requests/extend/\',\'modal-window-content\')"><input name="date" type="text" class="font-monospace" value="'+n+'" size="10" readonly onclick="showCalendar(\'calendar_div\',\'extend.date\')">&nbsp;<a href="javascript:void(0)" onclick="showCalendar(\'calendar_div\',\'extend.date\')"><i class="fas fa-calendar fa-lg"></i></a><br><br><button class="btn btn-primary px-2 py-1 border-1" onclick="document.extend.submit()">Update this Request</button></form></center><div id="calendar_div" class="calendar"></div>');
  }
}

function doPurge(r) {
  var r=getContentFromSynchronousRequest(null,'/php/pgrqst.php?ridx='+r);
  if (r.search("Thank you") > 0 && r.search("data will be purged") > 0) {
    document.getElementById('modal-window-content').innerHTML='<h1>Success</h1><p>Your data request has been marked for purging. The data will be removed from our system within one hour. If you did not mean to purge this request, please contact us immediately.</p>';
    getAjaxContent('GET', null, 'requests/','requests');
  } else {
    document.getElementById('modal-window-content').innerHTML='<h1>Error</h1><p>An error occurred and your request could not be marked for purging. Please try your request again later, and if the trouble persists, please let us know.</p>';
  }
}

function purgeRequest(r) {
  popConfirm('Once your data are purged, they will no longer be available for download. Are you sure you want to continue?', 'doPurge('+r+')', 500, 200);
}
