geocodeIcon = null;
geocode_marker = null;

function doGeocode() {
  g = new google.maps.Geocoder();
  g.geocode({"address": document.getElementById("geoloc").value}, function(results,status) {
    if (status == google.maps.GeocoderStatus.OK) {
      if (geocode_marker != null) {
        geocode_marker.setMap(null);
        geocode_marker = null;
      }
      geocode_marker = new google.maps.Marker({position: results[0].geometry.location, icon: getGeocodeIcon()});
      geocode_marker.setMap(map.handles.marker);
      max_zoom = 13;
      if (document.selections.spatial.selectedIndex == 3) {
        map.handles.marker.setZoom(max_zoom);
        showFourPoints(getGridCode(), results[0].geometry.location, true);
      } else {
        map.handles.marker.setCenter(results[0].geometry.location);
        map.handles.marker.setZoom(MIN_ZOOM_START);
      }
      z = map.handles.marker.getZoom();
        document.getElementById('mark2').style.left = ( (z - 2) * 6) + "px";
    }
  });
}

ival_m = 0, ival_m2 = 0;
markerIcon = null, annulusIcon = null;
last_bounds = null;
markerArray = null, annulus = null, annuli = null;
this_grid = 0, last_grid = 0, last_x = 0, last_y = 0;
click4_added = false;
MIN_ZOOM_START = 6;
min_zoom = MIN_ZOOM_START, last_zoom = 0;

function addMarkerMapEvent() {
  if (map && map.handles && map.handles.marker && map.handles.marker != null) {
    clearInterval(ival_m2);
    google.maps.event.addListener(map.handles.marker, "resize", function() {
      if (document.selections.spatial.selectedIndex == 2) {
        if (geocode_marker != null) {
          geocode_marker.setMap(null);
        }
        if (annulus != null) {
          annulus.setMap(map.handles.marker);
        }
        if (annuli != null) {
          for (n = 0; n < 4; ++n) {
            annuli[n].setMap(null);
          }
        }
      } else if (document.selections.spatial.selectedIndex == 3) {
        if (annulus != null) {
          annulus.setMap(null);
        }
        if (annuli != null) {
          for (n = 0; n < 4; ++n) {
            annuli[n].setMap(map.handles.marker);
          }
        }
        if (geocode_marker != null) {
          geocode_marker.setMap(map.handles.marker);
        }
      }
      google.maps.event.trigger(map.handles.marker, 'idle');
    });
    google.maps.event.addListener(map.handles.marker, "dragend", function() {
      last_zoom = 0;
    });
    google.maps.event.addListener(map.handles.marker, "idle", function() {
      this_zoom = map.handles.marker.getZoom();
      if (this_zoom >= min_zoom) {
        if (last_zoom == 0 || this_zoom < last_zoom) {
          bounds = map.handles.marker.getBounds();
          this_grid = getGridCode();
          submitRequest('https://' + location.host + '/cgi-bin/datasets/getGridpoints?db=WGrML&code=' + this_grid + '&nlat=' + bounds.getNorthEast().lat() + '&slat=' + bounds.getSouthWest().lat() + '&wlon=' + bounds.getSouthWest().lng() + '&elon=' + bounds.getNorthEast().lng(),function() {
            if (xhr.readyState == 4) {
              array = eval('(' + xhr.responseText + ')');
              if (this_grid != last_grid) {
                for (n = 0; n < last_y; ++n) {
                  for (m = 0; m < last_x; ++m) {
                    if (markerArray[n][m] != 0) {
                      markerArray[n][m].setVisible(false);
                    }
                  }
                  markerArray[n] = null;
                }
                markerArray = null;
              }
              last_grid = this_grid;
              last_x = array.x;
              last_y = array.y;
              if (markerArray == null) {
                markerArray = new Array(array.y);
                for (n = 0; n < array.y; ++n) {
                  markerArray[n] = new Array(array.x);
                  for (m = 0; m < array.x; markerArray[n][m++] = 0);
                }
              }
              if (array.locdata.length > 0) {
                last_zoom=map.handles.marker.getZoom();
                if (document.selections.spatial.selectedIndex != 3 && min_zoom == MIN_ZOOM_START) {
                  min_zoom = last_zoom;
                }
                for (n = 0; n < array.locdata.length; ++n) {
                  if (markerArray[array.locdata[n][0]][array.locdata[n][1]] == 0) {
                    markerArray[array.locdata[n][0]][array.locdata[n][1]] = new google.maps.Marker({position: new google.maps.LatLng(array.locdata[n][2], array.locdata[n][3]),  icon: getMarkerIcon()});
                    markerArray[array.locdata[n][0]][array.locdata[n][1]].setMap(map.handles.marker);
                  } else {
                    markerArray[array.locdata[n][0]][array.locdata[n][1]].setVisible(true);
                    if (document.selections.spatial.selectedIndex == 3) {
                      google.maps.event.clearListeners(markerArray[array.locdata[n][0]][array.locdata[n][1]], "click");
                    }
                  }
                  if (document.selections.spatial.selectedIndex == 2) {
                    google.maps.event.addListener(markerArray[array.locdata[n][0]][array.locdata[n][1]], "click", function() {
                      document.selections.ts_lat.value = this.getPosition().lat();
                      document.selections.ts_lon.value = this.getPosition().lng();
                      if (annulus != null) {
                        annulus.setMap(null);
                        annulus = null;
                      }
                      annulus = new google.maps.Marker({position: this.getPosition(), icon: getAnnulusIcon()});
                      annulus.setMap(map.handles.marker);
                    });
                  }
                }
              }
              if (document.selections.spatial.selectedIndex == 2) {
                google.maps.event.clearListeners(map.handles.marker, "click");
                click4_added = false;
              } else if (document.selections.spatial.selectedIndex == 3) {
                if (annulus != null) {
                  annulus.setMap(null);
                }
                if (!click4_added) {
                  google.maps.event.addListener(map.handles.marker, "click", function(e) {
                    if (geocode_marker != null) {
                      geocode_marker.setMap(null);
                      geocode_marker = null;
                    }
                    geocode_marker = new google.maps.Marker({position: e.latLng, icon: getGeocodeIcon()});
                    geocode_marker.setMap(this);
                    showFourPoints(this_grid, e.latLng, false);
                  });
                  click4_added = true;
                }
              }
              last_bounds = bounds;
            }
          });
        }
      } else {
        if (markerArray != null) {
          for (n = 0; n < markerArray.length; ++n) {
            for (m = 0; m < markerArray[n].length; ++m) {
              if (markerArray[n][m] != 0) {
                markerArray[n][m].setVisible(false);
              }
            }
          }
          last_zoom = 0;
        }
      }
    });
  }
}

function showFourPoints(grid, latLng, recenter) {
  submitRequest('https://' + location.host + '/cgi-bin/datasets/getGridpoints?db=WGrML&code=' + grid + '&lat=' + latLng.lat() + '&lon=' + latLng.lng(),function() {
    if (xhr.readyState == 4) {
      min_zoom = MIN_ZOOM_START;
      last_zoom = 0;
      array = eval('(' + xhr.responseText + ')');
      if (annuli == null) {
        annuli = new Array(4);
      } else {
        for (n = 0; n < 4; ++n) {
          annuli[n].setMap(null);
        }
      }
      min_lat = array.locdata[0][2];
      min_lon = array.locdata[0][3];
      max_lat = min_lat;
      max_lon = min_lon;
      for (n = 1; n < 4; ++n) {
        if (array.locdata[n][2] < min_lat) {
          min_lat = array.locdata[n][2];
        }
        if (array.locdata[n][2] > max_lat) {
          max_lat = array.locdata[n][2];
        }
        if (array.locdata[n][3] < min_lon) {
          min_lon = array.locdata[n][3];
        }
        if (array.locdata[n][3] > max_lon) {
          max_lon = array.locdata[n][3];
        }
      }
      document.selections.nlat_four.value = max_lat;
      document.selections.wlon_four.value = min_lon;
      document.selections.slat_four.value = min_lat;
      document.selections.elon_four.value = max_lon;
      if (recenter) {
        map.handles.marker.setCenter(new google.maps.LatLng((max_lat + min_lat) / 2., (max_lon + min_lon) / 2.));
      }
      for (n = 0; n < array.locdata.length; ++n) {
        annuli[n] = new google.maps.Marker({position: new google.maps.LatLng(array.locdata[n][2], array.locdata[n][3]), icon: getAnnulusIcon()});
        annuli[n].setMap(map.handles.marker);
        while (map.handles.marker.getZoom() > 2 && !map.handles.marker.getBounds().contains(annuli[n].getPosition())) {
          if (recenter) {
            zoomOut(map.handles.marker, 2, 'mark2');
          } else {
            map.handles.marker.setCenter(new google.maps.LatLng((max_lat + min_lat) /2., (max_lon + min_lon) / 2.));
            recenter=true;
          }
        }
      }
    }
  });
}

function getGridCode() {
  if (document.selections.grid_definition) {
    return document.selections.grid_definition[document.selections.grid_definition.selectedIndex].value;
  } else {
    return selected_grid_value;
  }
}

function getMarkerIcon() {
  if (markerIcon == null) {
    markerIcon={
      anchor: new google.maps.Point(8, 8),
      origin: new google.maps.Point(0, 0),
      size: new google.maps.Size(16, 16),
      url: 'https://' + location.host + '/images/gmaps/circle_cross_red_16x16.png'
    };
  }
  return markerIcon;
}

function getAnnulusIcon() {
  if (annulusIcon == null) {
    annulusIcon={
      anchor: new google.maps.Point(12, 12),
      size: new google.maps.Size(24, 24),
      url: 'https://' + location.host + '/images/gmaps/annulus.png'
    };
  }
  return annulusIcon;
}

function getGeocodeIcon() {
  if (geocodeIcon == null) {
    geocodeIcon={
      anchor: new google.maps.Point(16, 32),
      origin: new google.maps.Point(0, 0),
      size: new google.maps.Size(32, 32),
      url: 'https://' + location.host + '/images/gmaps/blue-dot.png'
    };
  }
  return geocodeIcon;
}

function doTheMarkerLoad() {
  if (typeof loadMarkerMapJS == "function") {
    clearInterval(ival_m);
    loadMarkerMapJS('markermap', 0, 0, 2, '');
    ival_m2=setInterval("addMarkerMapEvent()", 100);
  }
}

function doMarkerLoad() {
  ival_m = setInterval("doTheMarkerLoad()", 100);
}

registerAjaxCallback('doMarkerLoad');
