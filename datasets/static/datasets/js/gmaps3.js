var map=null;
var drawboxmap_init;
function loadDrawBoxMapJS(map_div_id,center_lat,center_lon,zoom_level,control_size) {
  drawboxmap_init={
    map_div_id: map_div_id,
    center_lat: center_lat,
    center_lon: center_lon,
    zoom_level: zoom_level,
    control_size: control_size
  };
  var head=document.getElementsByTagName('head').item(0);
  var scr=document.createElement('script');
  scr.setAttribute('type','text/javascript');
  scr.setAttribute('src','/static/js/gdrawboxmap3.js');
  scr.onload=initializeTheDrawBoxMap;
  scr.onreadystatechange=initializeTheDrawBoxMap;
  head.appendChild(scr);
}
var ival_drawbox;
function doTheDrawBoxMapInitialization() {
  if (map != null && map.handles.drawbox == null) {
    clearInterval(ival_drawbox);
    map.handles.drawbox=map.load(drawboxmap_init);
    if (typeof initializeDrawBoxMap != "undefined")
	initializeDrawBoxMap(drawboxmap_init);
  }
}
function initializeTheDrawBoxMap() {
  ival_drawbox=setInterval("doTheDrawBoxMapInitialization()",100);
}
var markermap_init;
function loadMarkerMapJS(map_div_id,center_lat,center_lon,zoom_level,control_size) {
  markermap_init={
    map_div_id: map_div_id,
    center_lat: center_lat,
    center_lon: center_lon,
    zoom_level: zoom_level,
    control_size: control_size
  };
  var head=document.getElementsByTagName('head').item(0);
  var scr=document.createElement('script');
  scr.setAttribute('type','text/javascript');
  scr.setAttribute('src','/static/js/gmarkermap3.js');
  scr.onload=initializeTheMarkerMap;
  scr.onreadystatechange=initializeTheMarkerMap;
  head.appendChild(scr);
}
var ival_marker;
function doTheMarkerMapInitialization() {
  if (map != null && map.handles.marker == null) {
    clearInterval(ival_marker);
    map.handles.marker=map.load(markermap_init);
    if (typeof initializeMarkerMap != "undefined")
	initializeMarkerMap(markermap_init);
  }
}
function initializeTheMarkerMap() {
  ival_marker=setInterval("doTheMarkerMapInitialization()",100);
}
var clustermap_init;
function loadClusterMapJS(map_div_id,center_lat,center_lon,zoom_level,control_size) {
  clustermap_init={
    map_div_id: map_div_id,
    center_lat: center_lat,
    center_lon: center_lon,
    zoom_level: zoom_level,
    control_size: control_size
  };
  var head=document.getElementsByTagName('head').item(0);
  var scr=document.createElement('script');
  scr.setAttribute('type','text/javascript');
  scr.setAttribute('src','/static/js/gclustermap3.js');
  scr.onload=initializeTheClusterMap;
  scr.onreadystatechange=initializeTheClusterMap;
  head.appendChild(scr);
}
var ival_cluster;
function doTheClusterMapInitialization() {
  if (map != null && map.handles.marker == null) {
    clearInterval(ival_cluster);
    map.handles.marker=map.load(clustermap_init);
    if (typeof initializeClusterMap != "undefined")
	initializeClusterMap(clustermap_init);
  }
}
function initializeTheClusterMap() {
  ival_cluster=setInterval("doTheClusterMapInitialization()",100);
}
function loadMixedMapJS() {
  var head=document.getElementsByTagName('head').item(0);
  var scr=document.createElement('script');
  scr.setAttribute('type','text/javascript');
  scr.setAttribute('src','/static/js/gmixedmap.js');
  scr.onload=loadTheMixedMap;
  scr.onreadystatechange=loadTheMixedMap;
  head.appendChild(scr);
}
function loadTheMixedMap() {
}
function zoomOut(map_handle,min_zoom,mark_id) {
  var zoom_level=map_handle.getZoom();
  if (zoom_level > min_zoom) {
    zoom_level--;
    var m=document.getElementById(mark_id);
    m.style.left=(parseInt(m.style.left)-6)+"px";
  }
  map_handle.setZoom(zoom_level);
}
function zoomIn(map_handle,max_zoom,mark_id) {
  var zoom_level=map_handle.getZoom();
  if (zoom_level < max_zoom) {
    zoom_level++;
    var m=document.getElementById(mark_id);
    m.style.left=(parseInt(m.style.left)+6)+"px";
  }
  map_handle.setZoom(zoom_level);
}
function refreshMap(h) {
  if (map != null) {
    eval("var handle=map.handles."+h.toLowerCase());
    if (handle != null) {
	var center=handle.getCenter();
	google.maps.event.trigger(handle,'resize');
	handle.setCenter(center);
    }
  }
}
