ival_d = 0;

function doTheDrawBoxLoad() {
  if (typeof loadDrawBoxMapJS == "function") {
    clearInterval(ival_d);
    let map_clat = "0";
    let wlon = "0";
    let elon = "0";
    let map_clon = (wlon + elon) / 2;
    if (wlon > elon) {
      map_clon += 180;
      if (map_clon > 180) {
        map_clon -= 360;
      }
    }
    loadDrawBoxMapJS('drawboxmap', map_clat, map_clon, "1", '');
    var m = document.getElementById('mark');
    m.style.left = (parseInt(m.style.left) +
        (1 - 1) * 6) + "px";
  }
}

function doDrawBoxLoad() {
  ival_d = setInterval("doTheDrawBoxLoad()", 100);
}

registerAjaxCallback('doDrawBoxLoad');