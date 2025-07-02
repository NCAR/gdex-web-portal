function bookmarksDisplay() {
  buttonDisplay("bookmarks");
}

function showBookmarks(e) {
  var b = document.getElementById('bookmarks_button');
  if (e == null) {

    // from update
    e = document.getElementById('bookmarks');
  } else {

    // from click
    b.innerHTML = "Hide Bookmarks";
  }
  if (e.classList.contains('d-none')) {
    e.classList.replace('d-none', 'd-block');
    getAjaxContent("GET", null, "bookmarks/", "bookmarks");
  }
}

function toggleBookmarks() {
  let e = document.getElementById('bookmarks');
  e.innerHTML = '<div class="text-center mt-3" id="loading"><strong>Loading ... &nbsp;&nbsp;</strong><div class="spinner-border text-primary" role="status"><span class="sr-only">Loading...</span></div></div>';
  if (e.classList.contains('d-none')) {
    showBookmarks(e);
  } else {
    hide(e, "bookmarks_button", "Bookmarks", "bookmarks");
  }
}

function refreshBookmarks() {
  if (document.getElementById("bookmarks_refresh").innerHTML.length > 0) {
    alert("An error occurred. Please try again later.");
    return;
  }
  getAjaxContent("GET", null, "bookmarks/count/", "bookmarks_count");
  getAjaxContent("GET", null, "bookmarks/", "bookmarks");
}

function removeBookmark(d, t) {
  getAjaxContent("DELETE", t, "bookmarks/" + d + "/", "bookmarks_refresh", null, refreshBookmarks);
  hideModalWindow();
}

function requestRemoveBookmark(d, t) {
  popConfirm("Are you sure you want to delete this bookmark?", "removeBookmark(&apos;" + d + "&apos;, &apos;" + t + "&apos;)", 350, 200);
}
