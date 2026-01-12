var drawboxmap_data;
function initializeDrawBoxMap(o) {
  drawboxmap_data={
    map_div: {ref: null, top: null, left: null, width: null, height: null},
    last_zoom: 0,
    center_lats: [0,36.2,73.,80.8,83.2,84.2,84.6,84.8,84.9,85.,85.,84,84,84,84,84,84,84],
    last_center_lat: 0,
    start: {x: 0, y: 0, ll: null},
    end: {x: 0, y: 0, ll: null},
    mouse_down: 0,
    mouse_moved: 0,
    overlay: null,
    p_options: null,
    box: null,
    box2: null,
    lines: null
  };
  var x=drawboxmap_data.map_div.ref=document.getElementById(o.map_div_id);
  drawboxmap_data.map_div.width=parseInt(drawboxmap_data.map_div.ref.style.width);
  drawboxmap_data.map_div.height=parseInt(drawboxmap_data.map_div.ref.style.height);
  drawboxmap_data.map_div.top=drawboxmap_data.map_div.ref.offsetTop;
  drawboxmap_data.map_div.left=drawboxmap_data.map_div.ref.offsetLeft;
  while ( (x=x.offsetParent) != null) {
    drawboxmap_data.map_div.top+=x.offsetTop;
    drawboxmap_data.map_div.left+=x.offsetLeft;
  }
  if (o.center_lat > drawboxmap_data.center_lats[1])
    o.center_lat=drawboxmap_data.center_lats[1];
  else if (o.center_lat < -drawboxmap_data.center_lats[1])
    o.center_lat=-drawboxmap_data.center_lats[1];
  drawboxmap_data.last_center_lat=o.center_lat;
  drawboxmap_data.p_options={
    strokeColor: '#ff7700',
    strokeOpacity: 0.0,
    fillColor: '#ff7700',
    fillOpacity: 0.2
  };
  drawboxmap_data.box=new google.maps.Polygon(drawboxmap_data.p_options);
  drawboxmap_data.box2=new google.maps.Polygon(drawboxmap_data.p_options);
  var l_options={
    strokeColor: '#ff7700',
    strokeWeight: 2,
    strokeOpacity: 0.4
  };
  drawboxmap_data.lines=new Array(
    new google.maps.Polyline(l_options),
    new google.maps.Polyline(l_options),
    new google.maps.Polyline(l_options),
    new google.maps.Polyline(l_options),
    new google.maps.Polyline(l_options),
    new google.maps.Polyline(l_options)
  );
  if (document.getElementById("pan")) {
    document.getElementById("pan").checked=true;
    defineDrag();
  }
  drawboxmap_data.overlay=new google.maps.OverlayView();
  drawboxmap_data.overlay.draw=function() {};
  drawboxmap_data.overlay.setMap(map.handles.drawbox);
  google.maps.event.addListener(map.handles.drawbox,"dragend",function() {
    checkBounds();
  });
  google.maps.event.addListener(map.handles.drawbox,"drag",function() {
    checkBounds();
  });
  google.maps.event.addListener(map.handles.drawbox,"idle",function() {
    if (map.handles.drawbox.getZoom() < drawboxmap_data.last_zoom) {
	drawboxmap_data.last_center_lat=0;
	checkBounds();
    }
    drawboxmap_data.last_zoom=map.handles.drawbox.getZoom();
  });
  google.maps.event.addListener(map.handles.drawbox,"mousedown",function(e) {
    resetBox(e);
  });
  google.maps.event.addListener(drawboxmap_data.box,"mousedown",function(e) {
    resetBox(e);
  });
  google.maps.event.addListener(drawboxmap_data.box2,"mousedown",function(e) {
    resetBox(e);
  });
  for (n=0; n < 6; n++) {
    google.maps.event.addListener(drawboxmap_data.lines[n],"mousedown",function(e) {
	resetBox(e);
    });
  }
  google.maps.event.addDomListener(document,"mouseup",function(e) {
    if (document.getElementById("draw") && document.getElementById("draw").checked && drawboxmap_data.mouse_down == 1) {
	drawboxmap_data.mouse_down=0;
//	drawBoxFromMouseMovement(e);
	drawboxmap_data.mouse_moved=0;
    }
  });
  google.maps.event.addDomListener(drawboxmap_data.map_div.ref,"mousemove",function(e) {
    if (document.getElementById("draw") && document.getElementById("draw").checked && drawboxmap_data.mouse_down == 1) {
	drawboxmap_data.mouse_moved=1;
	drawBoxFromMouseMovement(e);
    }
  });
}
function resetBox(e) {
  if (document.getElementById("draw") && document.getElementById("draw").checked) {
    clearBox();
    drawboxmap_data.mouse_down=1;
    document.getElementById("gdrawboxmap_nlat").value=parseInt(Math.ceil(e.latLng.lat()));
    document.getElementById("gdrawboxmap_wlon").value=parseInt(Math.floor(e.latLng.lng()));
    document.getElementById("gdrawboxmap_elon").value=parseInt(Math.ceil(e.latLng.lng()));
    document.getElementById("gdrawboxmap_slat").value=parseInt(Math.floor(e.latLng.lat()));
    drawboxmap_data.start.ll=e.latLng;
    var point=drawboxmap_data.overlay.getProjection().fromLatLngToContainerPixel(e.latLng);
    drawboxmap_data.start.x=drawboxmap_data.end.x=point.x;
    drawboxmap_data.start.y=drawboxmap_data.end.y=point.y;
    var point=drawboxmap_data.overlay.getProjection().fromLatLngToDivPixel(e.latLng);
    if (drawboxmap_data.end.x != point.x && drawboxmap_data.end.y != point.y) {
	var x=drawboxmap_data.map_div.ref;
	drawboxmap_data.map_div.top=x.offsetTop;
	drawboxmap_data.map_div.left=x.offsetLeft;
	while ( (x=x.offsetParent) != null) {
	  drawboxmap_data.map_div.top+=x.offsetTop;
	  drawboxmap_data.map_div.left+=x.offsetLeft;
	}
    }
  }
}
function clearBox() {
  drawboxmap_data.box.setMap(null);
  drawboxmap_data.box2.setMap(null);
  for (n=0; n < drawboxmap_data.lines.length; n++)
    drawboxmap_data.lines[n].setVisible(false);
}
function drawBoxFromMouseMovement(e) {
  if (drawboxmap_data.mouse_moved == 0) {
    clearBox();
    return;
  }
  if (e.pageX) {
    var e_pageX=e.pageX;
    var e_pageY=e.pageY;
  }
  else {
    var e_pageX=e.clientX+document.body.scrollLeft;
    var e_pageY=e.clientY+document.body.scrollTop;
  }
  if (e_pageX > (drawboxmap_data.map_div.left+drawboxmap_data.map_div.width))
    drawboxmap_data.end.x=drawboxmap_data.map_div.width;
  else if (e_pageX < drawboxmap_data.map_div.left)
    drawboxmap_data.end.x=0;
  else
    drawboxmap_data.end.x=e_pageX-drawboxmap_data.map_div.left;
  if (e_pageY > (drawboxmap_data.map_div.top+drawboxmap_data.map_div.height))
    drawboxmap_data.end.y=drawboxmap_data.map_div.height;
  else if (e_pageY < drawboxmap_data.map_div.top)
    drawboxmap_data.end.y=0;
  else
    drawboxmap_data.end.y=e_pageY-drawboxmap_data.map_div.top;
  drawboxmap_data.end.ll=drawboxmap_data.overlay.getProjection().fromContainerPixelToLatLng(new google.maps.Point(drawboxmap_data.end.x,drawboxmap_data.end.y));
  if (Math.abs(drawboxmap_data.end.ll.lng()-drawboxmap_data.start.ll.lng()) < 180.) {
    drawboxmap_data.box2.setMap(null);
    for (n=4; n < 6; n++)
	drawboxmap_data.lines[n].setMap(null);
    var coords=[
	new google.maps.LatLng(drawboxmap_data.start.ll.lat(),drawboxmap_data.start.ll.lng()),
	new google.maps.LatLng(drawboxmap_data.end.ll.lat(),drawboxmap_data.start.ll.lng()),
	new google.maps.LatLng(drawboxmap_data.end.ll.lat(),drawboxmap_data.end.ll.lng()),
	new google.maps.LatLng(drawboxmap_data.start.ll.lat(),drawboxmap_data.end.ll.lng()),
    ];
    drawboxmap_data.box.setPath(coords);
    drawboxmap_data.box.setMap(map.handles.drawbox);
    for (n=0; n < 4; n++) {
	var m=(n+1) % 4;
	drawboxmap_data.lines[n].setPath([coords[n],coords[m]]);
	drawboxmap_data.lines[n].setVisible(true);
	drawboxmap_data.lines[n].setMap(map.handles.drawbox);
    }
  }
  else {
    if ((drawboxmap_data.start.x < drawboxmap_data.end.x && drawboxmap_data.start.ll.lng() > 0 && drawboxmap_data.end.ll.lng() < 0) || (drawboxmap_data.start.x > drawboxmap_data.end.x && drawboxmap_data.start.ll.lng() < 0 && drawboxmap_data.end.ll.lng() > 0)) {
	var half_lng=180.+drawboxmap_data.start.ll.lng()/2.+drawboxmap_data.end.ll.lng()/2.;
	if (half_lng > 180.)
	  half_lng-=360.;
    }
    else
	var half_lng=(drawboxmap_data.start.ll.lng()+drawboxmap_data.end.ll.lng())/2.;
    var coords=[
	new google.maps.LatLng(drawboxmap_data.start.ll.lat(),half_lng),
	new google.maps.LatLng(drawboxmap_data.start.ll.lat(),drawboxmap_data.start.ll.lng()),
	new google.maps.LatLng(drawboxmap_data.end.ll.lat(),drawboxmap_data.start.ll.lng()),
	new google.maps.LatLng(drawboxmap_data.end.ll.lat(),half_lng)
    ];
    drawboxmap_data.box.setPath(coords);
    drawboxmap_data.box.setMap(map.handles.drawbox);
    for (n=0; n < 3; n++) {
	drawboxmap_data.lines[n].setPath([coords[n],coords[n+1]]);
	drawboxmap_data.lines[n].setVisible(true);
	drawboxmap_data.lines[n].setMap(map.handles.drawbox);
    }
    var coords=[
	new google.maps.LatLng(drawboxmap_data.start.ll.lat(),half_lng),
	new google.maps.LatLng(drawboxmap_data.start.ll.lat(),drawboxmap_data.end.ll.lng()),
	new google.maps.LatLng(drawboxmap_data.end.ll.lat(),drawboxmap_data.end.ll.lng()),
	new google.maps.LatLng(drawboxmap_data.end.ll.lat(),half_lng)
    ];
    drawboxmap_data.box2.setPath(coords);
    drawboxmap_data.box2.setMap(map.handles.drawbox);
    for (n=0; n < 3; n++) {
	drawboxmap_data.lines[n+3].setPath([coords[n],coords[n+1]]);
	drawboxmap_data.lines[n+3].setVisible(true);
	drawboxmap_data.lines[n+3].setMap(map.handles.drawbox);
    }
  }
  if (drawboxmap_data.end.y > drawboxmap_data.start.y)
    document.getElementById("gdrawboxmap_slat").value=parseInt(Math.floor(drawboxmap_data.end.ll.lat()));
  else
    document.getElementById("gdrawboxmap_nlat").value=parseInt(Math.ceil(drawboxmap_data.end.ll.lat()));
  if (drawboxmap_data.end.x > drawboxmap_data.start.x) {
    document.getElementById("gdrawboxmap_elon").value=parseInt(Math.ceil(drawboxmap_data.end.ll.lng()));
    if (document.getElementById("gdrawboxmap_elon").value == -180)
	document.getElementById("gdrawboxmap_elon").value=180;
  }
  else
    document.getElementById("gdrawboxmap_wlon").value=parseInt(Math.floor(drawboxmap_data.end.ll.lng()));
  if (map.onchangefunc != "undefined" && typeof map.onchangefunc == "function")
    map.onchangefunc();
}
var mcheck=0;
function checkInput(t)
{
  if (t.value.length == 0) {
    if (mcheck == 0) {
	if (t.id.indexOf("lat") > 0)
	  alert("You must enter a value between -90 and 90");
	else if (t.id.indexOf("lon") > 0)
	  alert("You must enter a value between -180 and 180");
	mcheck=1;
    }
    t.focus();
    return false;
  }
  else {
    if (t.value.indexOf(".") >= 0) {
//	if (mcheck == 0) {
	  alert("Decimal values are not allowed");
	  t.focus();
	  mcheck=1;
	  return false;
//	}
    }
//    if (mcheck == 0) {
	var non_numeric=false;
	for (n=0; n < t.value.length; n++) {
	  var x=t.value.charAt(n);
	  if (x < '0' || x > '9') {
	    if (x != '-' || n > 0)
		non_numeric=true;
	  }
	}
	if (non_numeric) {
	  alert("Values must be numeric");
	  t.focus();
	  mcheck=1;
	  return false;
	}
	if (t.id.indexOf("lat") > 0 && (t.value < -90 || t.value > 90)) {
	  alert("Latitude values must be between -90 and 90");
	  t.focus();
	  mcheck=1;
	  return false;
	}
	if (t.id.indexOf("lon") > 0 && (t.value < -180 || t.value > 180)) {
	  alert("Longitude values must be between -180 and 180");
	  t.focus();
	  mcheck=1;
	  return false;
	}
//    }
    mcheck=0;
    if (typeof google != "undefined") {
	drawBoxFromManualInput(true);
    }
    return true;
  }
}
function drawBoxFromManualInput(cfunc = false) {
  if (drawboxmap_data.box != null) {
    var nlat=document.getElementById("gdrawboxmap_nlat").value;
    var slat=document.getElementById("gdrawboxmap_slat").value;
    var wlon=document.getElementById("gdrawboxmap_wlon").value;
    var elon=document.getElementById("gdrawboxmap_elon").value;
    clearBox();
    if (nlat == 90 && slat == -90 && wlon == -180 && elon == 180)
	return;
    if (nlat > 89)
	nlat=89;
    if (slat < -89)
	slat=-89;
    if (wlon < -179)
	wlon=-179;
    if (elon > 179)
	elon=179;
    var ll1=new google.maps.LatLng(nlat,wlon);
    var ll2=new google.maps.LatLng(nlat,elon);
    var ll3=new google.maps.LatLng(slat,elon);
    var ll4=new google.maps.LatLng(slat,wlon);
    if (wlon < 0. && elon > 0.) {
	var ll0=new google.maps.LatLng(nlat,-0);
	var ll5=new google.maps.LatLng(slat,-0);
	drawboxmap_data.box.setPath([ll0,ll1,ll4,ll5]);
	drawboxmap_data.box.setMap(map.handles.drawbox);
	drawboxmap_data.lines[0].setPath([ll0,ll1]);
	drawboxmap_data.lines[0].setVisible(true);
	drawboxmap_data.lines[0].setMap(map.handles.drawbox);
	drawboxmap_data.lines[1].setPath([ll1,ll4]);
	drawboxmap_data.lines[1].setVisible(true);
	drawboxmap_data.lines[1].setMap(map.handles.drawbox);
	drawboxmap_data.lines[2].setPath([ll4,ll5]);
	drawboxmap_data.lines[2].setVisible(true);
	drawboxmap_data.lines[2].setMap(map.handles.drawbox);
	drawboxmap_data.box2.setPath([ll0,ll2,ll3,ll5]);
	drawboxmap_data.box2.setMap(map.handles.drawbox);
	var ll0=new google.maps.LatLng(nlat,0);
	var ll5=new google.maps.LatLng(slat,0);
	drawboxmap_data.lines[3].setPath([ll0,ll2]);
	drawboxmap_data.lines[3].setVisible(true);
	drawboxmap_data.lines[3].setMap(map.handles.drawbox);
	drawboxmap_data.lines[4].setPath([ll2,ll3]);
	drawboxmap_data.lines[4].setVisible(true);
	drawboxmap_data.lines[4].setMap(map.handles.drawbox);
	drawboxmap_data.lines[5].setPath([ll3,ll5]);
	drawboxmap_data.lines[5].setVisible(true);
	drawboxmap_data.lines[5].setMap(map.handles.drawbox);
    } else {
	drawboxmap_data.box.setPath([ll1,ll2,ll3,ll4]);
	drawboxmap_data.box.setMap(map.handles.drawbox);
	drawboxmap_data.lines[0].setPath([ll1,ll2]);
	drawboxmap_data.lines[0].setVisible(true);
	drawboxmap_data.lines[0].setMap(map.handles.drawbox);
	drawboxmap_data.lines[1].setPath([ll2,ll3]);
	drawboxmap_data.lines[1].setVisible(true);
	drawboxmap_data.lines[1].setMap(map.handles.drawbox);
	drawboxmap_data.lines[2].setPath([ll3,ll4]);
	drawboxmap_data.lines[2].setVisible(true);
	drawboxmap_data.lines[2].setMap(map.handles.drawbox);
	drawboxmap_data.lines[3].setPath([ll4,ll1]);
	drawboxmap_data.lines[3].setVisible(true);
	drawboxmap_data.lines[3].setMap(map.handles.drawbox);
    }
  }
  if (map.onchangefunc != "undefined" && typeof map.onchangefunc == "function" && cfunc) {
    map.onchangefunc();
  }
}
function checkBounds() {
  var bounds=map.handles.drawbox.getBounds();
  var center=map.handles.drawbox.getCenter();
  if (bounds.getNorthEast().lat() > 85. && center.lat() > drawboxmap_data.last_center_lat) {
    var zoom=map.handles.drawbox.getZoom();
    map.handles.drawbox.setCenter(new google.maps.LatLng(drawboxmap_data.center_lats[zoom],center.lng()),zoom);
  }
  else if (bounds.getSouthWest().lat() < -85. && center.lat() < drawboxmap_data.last_center_lat) {
    var zoom=map.handles.drawbox.getZoom();
    map.handles.drawbox.setCenter(new google.maps.LatLng(-drawboxmap_data.center_lats[zoom],center.lng()),zoom);
  }
  drawboxmap_data.last_center_lat=center.lat();
}
function defineDrag() {
  if (document.getElementById("pan").checked) {
//    mcheck=0;
//    if (checkInput(document.getElementById("gdrawboxmap_nlat")) && checkInput(document.getElementById("gdrawboxmap_slat")) && checkInput(document.getElementById("gdrawboxmap_wlon")) && checkInput(document.getElementById("gdrawboxmap_elon"))) {
	map.handles.drawbox.set('draggable',true);
	document.getElementById("gdrawboxmap_nlat").disabled=true;
	document.getElementById("gdrawboxmap_slat").disabled=true;
	document.getElementById("gdrawboxmap_wlon").disabled=true;
	document.getElementById("gdrawboxmap_elon").disabled=true;
//    }
//    else {
//	document.getElementById("pan").checked=false;
//	document.getElementById("draw").checked=true;
//    }
  }
  else {
    map.handles.drawbox.set('draggable',false);
    document.getElementById("gdrawboxmap_nlat").disabled=false;
    document.getElementById("gdrawboxmap_slat").disabled=false;
    document.getElementById("gdrawboxmap_wlon").disabled=false;
    document.getElementById("gdrawboxmap_elon").disabled=false;
  }
}
function resetToFullGlobalSelection()
{
  clearBox();
  document.getElementById("gdrawboxmap_nlat").value="90";
  document.getElementById("gdrawboxmap_slat").value="-90";
  document.getElementById("gdrawboxmap_wlon").value="-180";
  document.getElementById("gdrawboxmap_elon").value="180";
}
function checkMapInputs()
{
  if (parseFloat(document.getElementById("gdrawboxmap_nlat").value) <= parseFloat(document.getElementById("gdrawboxmap_slat").value)) {
    alert("The value for North latitude must be greater than the value for South latitude");
    return false;
  }
  var x=360.+parseFloat(document.getElementById("gdrawboxmap_elon").value)-parseFloat(document.getElementById("gdrawboxmap_wlon").value);
  if (parseFloat(document.getElementById("gdrawboxmap_elon").value) <= parseFloat(document.getElementById("gdrawboxmap_wlon").value) && (x == 0. || x > 180.)) {
    alert("The value for East longitude must be greater than the value for West longitude");
    return false;
  }
  return true;
}
