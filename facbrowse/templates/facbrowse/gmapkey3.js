<script id="gmapkey_script_3" language="javascript">
var ival_gmapkey_callback = null;
var ival_count = 0;
function doGMapKeyCallback() {
  ival_count++;
  if (typeof google == "undefined") {
    if (ival_count > 20) {
      clearInterval(ival_gmapkey_callback);
      alert("Google Maps failed to load - the Google server is not responding. If reloading the page doesn't help, you will need to enter coordinates manually. In some cases, spatial subsetting may not be available at all.");
    }
    return;
  }
  map = {
    loaded: false,
    onchangefunc: showChangedSelections,
    options: {
      streetViewControl: false,
      scrollwheel: false,
      disableDoubleClickZoom: true,
      scaleControl: true,
      fullscreenControl: false,
      mapTypeId: google.maps.MapTypeId.ROADMAP
    },
    handles: {
      drawbox: null,
      marker: null
    },
    load: function(o) {
      var map_div=document.getElementById(o.map_div_id);
      var handle=new google.maps.Map(map_div,map.options);
      handle.setCenter(new google.maps.LatLng(o.center_lat,o.center_lon));
      handle.setZoom(o.zoom_level);
      if (o.control_size == null || o.control_size.length == 0) {
        handle.set('panControl',false);
        handle.set('zoomControl',false);
      } else {
        handle.set('panControl',true);
        handle.set('zoomControl',true);
        if (o.control_size == "small") {
          handle.set('zoomControlOptions',{style: google.maps.ZoomControlStyle.SMALL});
        } else if (o.control_size == "large") {
          handle.set('zoomControlOptions',{style: google.maps.ZoomControlStyle.LARGE});
        }
      }
      map.loaded=true;
      return handle;
    }
  };
  clearInterval(ival_gmapkey_callback);
}

var callback_called = false;

function gmap3_key_callback() {
  if (callback_called) {
    return;
  }
  clearInterval(ival_gmapkey_callback);
  ival_gmapkey_callback = setInterval("doGMapKeyCallback()", 100);
  callback_called = true;
}

if (typeof gmap3_loaded != "undefined" && !gmap3_loaded) {
  var scr = document.createElement("script");
  scr.setAttribute("type", "text/javascript");
  scr.setAttribute("src", "{{ gmap_api_url }}?key=" +
      "{{ gmap_api_key }}&loading=async&callback=gmap3_key_callback");
  document.body.appendChild(scr);
  gmap3_loaded = true;
}

registerAjaxCallback('gmap3_key_callback');
</script>
