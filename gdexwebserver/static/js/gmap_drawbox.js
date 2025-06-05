ival_d = 0;

function doTheDrawBoxLoad() {
  if (typeof loadDrawBoxMapJS == "function") {
    clearInterval(ival_d);
    if (typeof(gmap_clat) != "undefined" && typeof(gmap_clon) != "undefined" && typeof(gmap_zoom) != "undefined") {
       loadDrawBoxMapJS('drawboxmap', gmap_clat, gmap_clon, gmap_zoom, '');
    } else {
       loadDrawBoxMapJS('drawboxmap', 0, 0, 1, '');
    }
    m = document.getElementById('mark');
    zoom = typeof(gmap_zoom) != "undefined" ? gmap_zoom : 1;
    m.style.left = (parseInt(m.style.left) + (zoom - 1) * 6) + "px";
  }
}

function doDrawBoxLoad() {
  ival_d = setInterval("doTheDrawBoxLoad()", 100);
}

registerAjaxCallback('doDrawBoxLoad');
