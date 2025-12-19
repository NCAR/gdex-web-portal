function initializeMarkerMap(o) {
  mdiv=document.getElementById(o.map_div_id);
  var x=mdiv;
  var xtop=x.offsetTop;
  var xleft=x.offsetLeft;
  while ( (x=x.offsetParent) != null && x.id != "content_container") {
    xtop+=x.offsetTop;
    xleft+=x.offsetLeft;
  }
  if (document.getElementById("loadwaitscreen")) {
    var lws=document.getElementById("loadwaitscreen");
    lws.style.top=(xtop)-5+"px";
    lws.style.left=(xleft-3)+"px";
    lws.style.visibility="hidden";
  }
  if (document.getElementById("loadwaittext")) {
    var lwt=document.getElementById("loadwaittext");
    lwt.style.top=(xtop+(parseInt(mdiv.style.height)-parseInt(lwt.style.height))/2)+"px";
    lwt.style.left=(xleft+(parseInt(mdiv.style.width)-parseInt(lwt.style.width))/2)+"px";
    lwt.style.visibility="hidden";
  }
}
