/**
 * Leaflet/OpenStreetMap-based replacement for the legacy Google Maps
 * bounding-box selector. Preserves the element IDs and global function
 * names (defineDrag, checkInput, resetToFullGlobalSelection, refreshMap,
 * map.handles.drawbox) relied on by the dataset-specific subset scripts
 * (BUFR_subset.js, prepbufr_subset.js, ispdv4_subset.js, etc.) and by the
 * markup in google-map.html. Zoom in/out is handled by Leaflet's own
 * on-map zoom control rather than a custom widget.
 */
var map = {
  handles: { drawbox: null },
  get onchangefunc() {
    return (typeof showChangedSelections == "function") ? showChangedSelections : null;
  }
};

var drawboxBoxLayer = null;
var drawboxDragStart = null;

function qsById(id) {
  return document.getElementById(id);
}

function normalizeLng(lng) {
  return L.Util.wrapNum(lng, [-180, 180], true);
}

function clampBounds(nlat, slat, wlon, elon) {
  return {
    nlat: Math.min(89, nlat),
    slat: Math.max(-89, slat),
    wlon: Math.max(-179, wlon),
    elon: Math.min(179, elon)
  };
}

function refreshMap(h) {
  var handle = map.handles[h.toLowerCase()];
  if (handle) {
    handle.invalidateSize();
  }
}

function defineDrag() {
  var drawbox = map.handles.drawbox;
  if (!drawbox) return;
  var panMode = qsById("pan").checked;
  if (panMode) {
    drawbox.dragging.enable();
  } else {
    drawbox.dragging.disable();
  }
  ["gdrawboxmap_nlat", "gdrawboxmap_slat", "gdrawboxmap_wlon", "gdrawboxmap_elon"].forEach(function(id) {
    qsById(id).disabled = panMode;
  });
}

function clearBox() {
  if (drawboxBoxLayer) {
    drawboxBoxLayer.clearLayers();
  }
}

var boxStyle = {
  color: "#ff7700",
  weight: 2,
  opacity: 0.6,
  fillColor: "#ff7700",
  fillOpacity: 0.2
};

function renderBox(nlat, slat, wlon, elon) {
  clearBox();
  if (!drawboxBoxLayer) return;
  if (wlon <= elon) {
    L.rectangle([[slat, wlon], [nlat, elon]], boxStyle).addTo(drawboxBoxLayer);
  } else {
    L.rectangle([[slat, wlon], [nlat, 180]], boxStyle).addTo(drawboxBoxLayer);
    L.rectangle([[slat, -180], [nlat, elon]], boxStyle).addTo(drawboxBoxLayer);
  }
}

function resetToFullGlobalSelection() {
  clearBox();
  drawboxSetInputsFromBounds("90", "-90", "-180", "180");
}

function drawBoxFromManualInput(cfunc) {
  var nlat = parseFloat(qsById("gdrawboxmap_nlat").value);
  var slat = parseFloat(qsById("gdrawboxmap_slat").value);
  var wlon = parseFloat(qsById("gdrawboxmap_wlon").value);
  var elon = parseFloat(qsById("gdrawboxmap_elon").value);
  clearBox();
  if (nlat == 90 && slat == -90 && wlon == -180 && elon == 180) {
    return;
  }
  var b = clampBounds(nlat, slat, wlon, elon);
  renderBox(b.nlat, b.slat, b.wlon, b.elon);
  if (cfunc && typeof map.onchangefunc == "function") {
    map.onchangefunc();
  }
}

var mcheck = 0;
function checkInput(t) {
  if (t.value.length == 0) {
    if (mcheck == 0) {
      if (t.id.indexOf("lat") > 0)
        alert("You must enter a value between -90 and 90");
      else if (t.id.indexOf("lon") > 0)
        alert("You must enter a value between -180 and 180");
      mcheck = 1;
    }
    t.focus();
    return false;
  }
  if (t.value.indexOf(".") >= 0) {
    alert("Decimal values are not allowed");
    t.focus();
    mcheck = 1;
    return false;
  }
  var non_numeric = false;
  for (var n = 0; n < t.value.length; n++) {
    var x = t.value.charAt(n);
    if (x < "0" || x > "9") {
      if (x != "-" || n > 0) non_numeric = true;
    }
  }
  if (non_numeric) {
    alert("Values must be numeric");
    t.focus();
    mcheck = 1;
    return false;
  }
  if (t.id.indexOf("lat") > 0 && (t.value < -90 || t.value > 90)) {
    alert("Latitude values must be between -90 and 90");
    t.focus();
    mcheck = 1;
    return false;
  }
  if (t.id.indexOf("lon") > 0 && (t.value < -180 || t.value > 180)) {
    alert("Longitude values must be between -180 and 180");
    t.focus();
    mcheck = 1;
    return false;
  }
  mcheck = 0;
  drawBoxFromManualInput(true);
  return true;
}

function drawboxSetInputsFromBounds(nlat, slat, wlon, elon) {
  qsById("gdrawboxmap_nlat").value = nlat;
  qsById("gdrawboxmap_slat").value = slat;
  qsById("gdrawboxmap_wlon").value = wlon;
  qsById("gdrawboxmap_elon").value = elon;
}

function drawboxBoundsFromLatLngs(startLatLng, endLatLng) {
  var lat1 = startLatLng.lat, lat2 = endLatLng.lat;
  var lng1 = normalizeLng(startLatLng.lng), lng2 = normalizeLng(endLatLng.lng);
  var nlat = Math.ceil(Math.max(lat1, lat2));
  var slat = Math.floor(Math.min(lat1, lat2));
  var w = Math.min(lng1, lng2), e = Math.max(lng1, lng2);
  var directWidth = e - w;
  var wrapWidth = 360 - directWidth;
  var wlon, elon;
  if (wrapWidth < directWidth) {
    wlon = e;
    elon = w;
  } else {
    wlon = w;
    elon = e;
  }
  return clampBounds(nlat, slat, Math.floor(wlon), Math.ceil(elon));
}

function drawboxUpdateFromDrag(startLatLng, endLatLng) {
  var b = drawboxBoundsFromLatLngs(startLatLng, endLatLng);
  drawboxSetInputsFromBounds(b.nlat, b.slat, b.wlon, b.elon);
  renderBox(b.nlat, b.slat, b.wlon, b.elon);
  if (typeof map.onchangefunc == "function") {
    map.onchangefunc();
  }
}

function drawboxOnMapMouseDown(e) {
  if (!qsById("draw") || !qsById("draw").checked) return;
  drawboxDragStart = e.latlng;
  drawboxUpdateFromDrag(e.latlng, e.latlng);
}

function drawboxOnDocMouseMove(e) {
  if (!drawboxDragStart || !map.handles.drawbox) return;
  var latlng = map.handles.drawbox.mouseEventToLatLng(e);
  drawboxUpdateFromDrag(drawboxDragStart, latlng);
}

function drawboxOnDocMouseUp() {
  drawboxDragStart = null;
}

function initDrawBoxMap() {
  if (map.handles.drawbox) return;
  var mapDiv = qsById("drawboxmap");
  if (!mapDiv || typeof L == "undefined") return;

  if (window.__osmDrawboxMapInstance) {
    window.__osmDrawboxMapInstance.remove();
    window.__osmDrawboxMapInstance = null;
  }

  var drawbox = L.map(mapDiv, {
    center: [0, 0],
    zoom: 1,
    minZoom: 1,
    maxZoom: 10,
    zoomControl: true,
    scrollWheelZoom: false,
    doubleClickZoom: false,
    boxZoom: false,
    keyboard: false,
    worldCopyJump: true
  });

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; <a href=\"https://www.openstreetmap.org/copyright\">OpenStreetMap</a> contributors",
    maxZoom: 19
  }).addTo(drawbox);

  L.control.scale().addTo(drawbox);

  map.handles.drawbox = drawbox;
  window.__osmDrawboxMapInstance = drawbox;
  drawboxBoxLayer = L.layerGroup().addTo(drawbox);

  drawbox.on("mousedown", drawboxOnMapMouseDown);
  if (!window.__osmDrawboxDocListenersAttached) {
    document.addEventListener("mousemove", function(e) { drawboxOnDocMouseMove(e); });
    document.addEventListener("mouseup", function(e) { drawboxOnDocMouseUp(e); });
    window.__osmDrawboxDocListenersAttached = true;
  }

  if (qsById("pan")) {
    qsById("pan").checked = true;
  }
  defineDrag();
}

(function() {
  function setup() {
    var mapSelectDiv = document.getElementById("mapselect");
    if (!mapSelectDiv) return;

    var initAttempts = 0;
    var retryInterval = null;

    function tryInit() {
      if (mapSelectDiv.style.display === "none") return;
      if (map.handles.drawbox) {
        map.handles.drawbox.invalidateSize();
        return;
      }
      if (typeof L == "undefined") {
        initAttempts++;
        if (initAttempts == 20) {
          clearInterval(retryInterval);
          alert("The interactive map failed to load. You can still enter the bounding coordinates manually in the boxes below.");
        }
        return;
      }
      initDrawBoxMap();
      clearInterval(retryInterval);
    }

    var observer = new MutationObserver(tryInit);
    observer.observe(mapSelectDiv, { attributes: true, attributeFilter: ["style"] });
    tryInit();
    retryInterval = setInterval(tryInit, 100);
  }

  // On a full page load, this script's own <script src> tag is parsed (and
  // executed synchronously) before the parser reaches #mapselect further
  // down the same document, so it must wait for DOMContentLoaded. When this
  // file is instead re-run because an AJAX tab-swap injected a fresh copy of
  // this markup via jQuery's .html() (which executes embedded scripts only
  // after inserting their DOM), the document has long since finished
  // loading and setup() must run immediately.
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setup);
  } else {
    setup();
  }
})();
