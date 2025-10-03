/***********************************************************************************
 * 
 *     Title : prepbufr_subset.js
 *    Author : Thomas Cram (tcram@ucar.edu)
 *      Date : 09/01/2011
 *   Purpose : javascript program to validate the form inputs for request of 
 *             NCEP ADP PREPBUFR sub-dataset.
 * Work File : $DSSWEB/js/prepbufr_subset.js
 * Test File : $DSSWEB/js/prepbufr_subset_test.js
 *
 ***********************************************************************************/
 
var dates, stations, parameters, types, pbtypes, inputtypes, flts, vars, rinfo, comp, sflag;
var stationCounter = 1;
var stationLimit = 20;
var stationNum, countValid;

/**
 * function to reset the temporal selections
 *
 */
function resetTemporal(sdate, edate) 
{
   document.form.startDate.value = sdate;
   document.form.endDate.value   = edate;
}

/**
 * Validate start and end date form inputs
 *
 */
function checkDates() { 

  if (document.form.startDate.value.length != 10 || document.form.endDate.value.length != 10) {
    alert("Enter dates as \'YYYY-MM-DD\'");
    return false;
  }

  var isGoodDate=true;

  for (n=0; n < 10; n++) {
    if (n <= 3 || n == 5 || n == 6 || n == 8 || n == 9) {
      if (document.form.startDate.value.charAt(n) < '0' || document.form.startDate.value.charAt(n) > '9' || document.form.endDate.value.charAt(n) < '0' || document.form.endDate.value.charAt(n) > '9')
        isGoodDate=false;
    }
    else if (n == 4 || n == 7) {
      if (document.form.startDate.value.charAt(n) != '-' || document.form.endDate.value.charAt(n) != '-')
        isGoodDate=false;
    }
  }

  if (!isGoodDate) {
    alert("Enter dates as YYYY-MM-DD");
    return false;
  }

  if ((document.form.startDate.value+' '+document.form.startTime.value) > (document.form.endDate.value+' '+document.form.endTime.value)) {
    alert("The start date and time must precede the end date");
    return false;
  }

  var startValue = document.form.startDate.value;
  var endValue   = document.form.endDate.value;

  var startYear = startValue.substr(0,4);
  var startMon  = startValue.substr(5,2);
  var startDay  = startValue.substr(8,2);
  var endYear = endValue.substr(0,4);
  var endMon  = endValue.substr(5,2);
  var endDay  = endValue.substr(8,2);
  
  var startYearFloat  = parseFloat(startYear);
  var endYearFloat    = parseFloat(endYear);
  var startMonthFloat = parseFloat(startMon);
  var endMonthFloat   = parseFloat(endMon);
  
 if ( ((endYearFloat - startYearFloat) * 12 + (endMonthFloat - startMonthFloat)) > 12) {
   alert("Please select a temporal range equal to or less than one year.  Submit multiple data requests if you wish to request data for more than one year.");
   return false;
 }

  var minDate = document.getElementById("minDate").value;
  var minYear = minDate.substr(0,4);
  var minMon  = minDate.substr(5,2);
  var minDay  = minDate.substr(8,2);
  var minDateInt = parseInt(minYear.concat(minMon,minDay));
  
  var maxDate = document.getElementById("maxDate").value;
  var maxYear = maxDate.substr(0,4);
  var maxMon  = maxDate.substr(5,2);
  var maxDay  = maxDate.substr(8,2);
  var maxDateInt = parseInt(maxYear.concat(maxMon,maxDay));
  
  var startDateInt = parseInt(startYear.concat(startMon,startDay));
  var endDateInt = parseInt(endYear.concat(endMon,endDay));
  
  if(startDateInt < minDateInt || endDateInt > maxDateInt) {
    alert("The valid date range is " + minDate + " to " + maxDate + ".  Please revise your date selections.");
    return false;
  }
  
// Set subsetting bit flag for partial temporal selection
  if(startDateInt > minDateInt) {
    sflag |= 2;
  } else {
    if(endDateInt < maxDateInt) {
      sflag |= 2;
    }
  }
  
 return true;
 
} 

/**
 * Validate output data format form input
 *
 */
function checkFormat()
{
 if (document.form.dataFormat.value == -1) {
   alert("Please select an output data format (NetCDF or ASCII)");
   return false;
 } else {
   return true;
 }
}

/**
 * Validate station ID form inputs
 *
 */
function checkStations()
{
   var i, j;
   var form = document.form;
   var stationSubmit;
   var countEmpty;
   
   // check station IDs
   countValid = 0;   // Count the valid entries
   countEmpty = 0;   // Count the empty entries
//   for($i=1; $i<=stationCounter; $i++) {
   for($i=1; $i<=stationLimit; $i++) {
     stationNum = "station"+String($i-1);
     stationSubmit = document.getElementById(stationNum).value;
     if (stationSubmit == "") {
         countEmpty++;
     } else if (stationSubmit.length < 4) {
         alert("Invalid value entered for station "+($i)+" - must be 4 or 5 characters");
         return false;
     } else {
         countValid++;
     }
   }

   // Fill stations field
   stations = "";
//   for($i=1; $i<=stationCounter; $i++) {
   for($i=1; $i<=stationLimit; $i++) {
       stationNum = "station"+String($i-1);
     if (countValid == 0) {
         stations = "ALL";
     } else if (document.getElementById(stationNum).value != "") {
         var stationstr = document.getElementById(stationNum).value;
         if(!stations) {
           stations = stationstr.toUpperCase();
         } else {
           stations += " " + stationstr.toUpperCase();
         }
     }
   }

// Set subsetting bit flag for partial spatial selection
   if(countValid > 0) {
     sflag |= 4;
   }

   return true;
}

/**
 * Validate spatial subset preference
 *
 */
function checkSpatialPref()
{
   if( (form.mapdisplayed.value == 0) && (form.latlondisplayed.value == 0) && (form.stationdisplayed.value == 0) && (form.polydisplayed.value == 0) && (form.griddisplayed.value == 0) ) {
     alert("Please select a spatial subset preference");
     return false;
 } else {
     return true;
 }
}

/**
 * Validate NCEP Storage Grid form input
 *
 */
function checkGrid()
{
 if ((document.form.griddisplayed.value == 1) && (document.form.mapProjection.value == "")) {
   alert("Please select a NCEP storage grid (Gnnn)");
   return false;
 } else {
   // Set subsetting bit flag for partial spatial selection
   sflag |= 4;
   return true;
 }
}

/**
 * functions to validate latitude and longitude form inputs
 *
 */
function checkLatLon()
{
   var form = document.form;
   var i, j;
   var min, max;
   var value, unit;

   i = 0;
   if(form.mapdisplayed.value == 1) setSpaceValues();
   
   max = goodCoordinate(form.tlat.value, true);
   if(max == 999) {
      alert("Top latitude was entered improperly.\nRe-enter as a positive number, followed by a space, followed by 'N' or 'S'.");
      return false;
   }
// Verify a space exists between the lat/lon coordinate number and direction
   value = form.tlat.value;
   unit = value.charAt(value.length - 1);
   form.tlat.value = parseFloat(value).toFixed(1) + " " + unit.toUpperCase();
   
   min = goodCoordinate(form.blat.value, true);
   if(min == 999) {
      alert("Bottom latitude was entered improperly.\nRe-enter as a positive number, followed by a space, followed by 'N' or 'S'.");
      return false;
   }
   if(max < min) {
      alert("Bottom latitude cannot exceed Top latitude.\nRe-enter the latitudes.");
      return false;
   }
// Verify a space exists between the lat/lon coordinate number and direction
   value = form.blat.value;
   unit = value.charAt(value.length - 1);
   form.blat.value = parseFloat(value).toFixed(1) + " " + unit.toUpperCase();
   
   if(max == 90) i++;
   if(min == -90) i++;

// Set subsetting bit flag for partial spatial selection
   if((max - min) < 180) sflag |= 4;

   max = goodCoordinate(form.rlon.value, false);
   if(max == 999) {
      alert("Right longitude was entered improperly.\nRe-enter as a positive number, followed by a space, followed by 'E' or 'W'.");
      return false;
   }
// Verify a space exists between the lat/lon coordinate number and direction
   value = form.rlon.value;
   unit = value.charAt(value.length - 1);
   form.rlon.value = parseFloat(value).toFixed(1) + " " + unit.toUpperCase();

   min = goodCoordinate(form.llon.value, false);
   if(min == 999) {
      alert("Left longitude was entered improperly.\nRe-enter as a positive number, followed by a space, followed by 'E' or 'W'.");
      return false;
   }
   if(max < min && min - max < 180.0 && !document.map) { 
      if(!confirm("Left longitude (" + form.llon.value + 
                  ") exceeds Right Longitude (" +
                  form.rlon.value + ")!\n(Click OK to " +
                         "continue or Cancel to re-enter longitude values)")) {
         return false;
      }
   }
// Verify a space exists between the lat/lon coordinate number and direction
   value = form.llon.value;
   unit = value.charAt(value.length - 1);
   form.llon.value = parseFloat(value).toFixed(1) + " " + unit.toUpperCase();

   if(max == 180) i++;
   if(min == -180) i++;

// Set subsetting bit flag for partial spatial selection
   if((max - min) < 360) sflag |= 4;

   if(i == 4) {
           alert("Requests for the entire globe cannot be fulfilled.  Please select a smaller latitude/longitude region.");
	   return false;
   }
   
   return true;
}

function setSpaceValues()
{
   var form = document.form;
   var tmp;
   
   tmp = document.getElementById("gdrawboxmap_nlat").value;
   if(tmp >= 0.) {
      form.tlat.value = tmp + ".0 N";
   } else {
      form.tlat.value = (-tmp) + ".0 S";
   }
   tmp = document.getElementById("gdrawboxmap_slat").value;
   if(tmp >= 0.) {
      form.blat.value = tmp + ".0 N";
   } else {
      form.blat.value = (-tmp) + ".0 S";
   }
   tmp = document.getElementById("gdrawboxmap_wlon").value;
   if(tmp >= 0.) {
      form.llon.value = tmp + ".0 E";
   } else {
      form.llon.value = (-tmp)+".0 W";
   }
   tmp = document.getElementById("gdrawboxmap_elon").value;
   if(tmp >= 0.) {
      document.form.rlon.value = tmp + ".0 E";
   } else {
      document.form.rlon.value = (-tmp) + ".0 W";
   }
}

/**
 * check if user input is a good latitude/longitude value
 */
function goodCoordinate(value, islat)
{
   var nvalue;
   var unit = value.charAt(value.length - 1).toUpperCase();
   
   if(value.charAt(0) == '-') {
      return 999;
   }
   
   nvalue=parseFloat(value);
   
   if(islat) {
      if(nvalue > 90.0 || nvalue < 0.0) {
         return 999;
      }
      if(unit == 'S') {
         nvalue = -nvalue;
      } else if(unit != 'N') {
	     return 999;
	  }
   } else  {
      if(nvalue > 360.0 || nvalue < 0.0) {
         return 999;
      }
      if(unit == 'W') {
	     nvalue=-nvalue;
	  } else if(unit != 'E') {
         return 999;
      }
   }
   return nvalue;
}

/**
 * Validate parameter checkbox selections
 */

function checkParameters()
{
  var num_checkboxes=0;
  var num_checked=0;
  parameters = "";

  num_checkboxes = document.form.parameter.length;
  
  for (i=0; i < num_checkboxes; i++) {
    if (document.form.parameter[i].checked) {
      num_checked++;
    }
  }

  if (num_checked == 0) {
    alert("Please select at least one parameter");
    return false;
  } else {
      if (document.getElementById("spfh").checked) {
        parameters = "SPFH";
      }
      if (document.getElementById("tmp").checked) {
        if (!parameters) {
          parameters = "TMP";
        } else {
          parameters += " TMP";
        }
      }
      if (document.getElementById("hgt").checked) {
        if (!parameters) {
          parameters = "HGT";
        } else {
          parameters += " HGT";
        }
      }
      if (document.getElementById("ugrd").checked) {
        if (!parameters) {
          parameters = "UGRD";
        } else {
          parameters += " UGRD";
        }
      }
      if (document.getElementById("vgrd").checked) {
        if (!parameters) {
          parameters = "VGRD";
        } else {
          parameters += " VGRD";
        }
      }
      if (document.getElementById("dpt").checked) {
        if (!parameters) {
          parameters = "DPT";
        } else {
          parameters += " DPT";
        }
      }
      if (document.getElementById("wdir").checked) {
        if (!parameters) {
          parameters = "WDIR";
        } else {
          parameters += " WDIR";
        }
      }
      if (document.getElementById("wind").checked) {
        if (!parameters) {
          parameters = "WIND";
        } else {
          parameters += " WIND";
        }
      }
      if (document.getElementById("rh").checked) {
        if (!parameters) {
          parameters = "RH";
        } else {
          parameters += " RH";
        }
      }
      if (document.getElementById("mixr").checked) {
        if (!parameters) {
          parameters = "MIXR";
        } else {
          parameters += " MIXR";
        }
      }
      if (document.getElementById("prmsl").checked) {
        if (!parameters) {
          parameters = "PRMSL";
        } else {
          parameters += " PRMSL";
        }
      }
  }
  
// Set subsetting bit flag for partial parameter selection
  if ((document.form.dataFormat.value == 0) && (num_checked < 10)) {
    sflag |= 1;
  }
  if ((document.form.dataFormat.value == 1) && (num_checked < 5)) {
    sflag |= 1;
  }
  
  return true;
}

/**
 * Get PREPBUFR message type checkbox selections
 */

function getTypes()
{
   var i;
   var num_checkboxes=0;
   var num_checked=0;
   types="";

   num_checkboxes = document.form.msgtype.length;

  for(i = 0; i < num_checkboxes; i++) {
    if(document.form.msgtype[i].checked) {
      if (!types) {
        types = document.form.msgtype[i].value;
      } else {
        types += " " + document.form.msgtype[i].value;
      }
      num_checked++;
    }
  }
  if (num_checked == num_checkboxes) {
    types = "ALL";  
  }
  return true;  
}

/**
 * Get PREPBUFR message type checkbox selections
 */

function getPBTypes()
{
   var i;
   var num_checkboxes=0;
   var num_checked=0;
   pbtypes="";

   num_checkboxes = document.form.pbtype.length;

  for(i = 0; i < num_checkboxes; i++) {
    if(document.form.pbtype[i].checked) {
      if (!pbtypes) {
        pbtypes = document.form.pbtype[i].value;
      } else {
        pbtypes += " " + document.form.pbtype[i].value;
      }
      num_checked++;
    }
  }
  if (num_checked == num_checkboxes) {
    pbtypes = "ALL";  
  }
  return true;  
}

/**
 * Get Input report type checkbox selections
 */

function getInputTypes()
{
   var i;
   var num_checkboxes=0;
   var num_checked=0;
   inputtypes="";
   num_checkboxes = document.form.inputtype.length;

  for(i = 0; i < num_checkboxes; i++) {
    if(document.form.inputtype[i].checked) {
      if (!inputtypes) {
        inputtypes = document.form.inputtype[i].value;
      } else {
        inputtypes += " " + document.form.inputtype[i].value;
      }
      num_checked++;
    }
  }  
  if (num_checked == num_checkboxes) {
    inputtypes = "ALL";  
  }
  return true;  
}

/**
 * open a help window
 */

function openHelpWindow(helpkey)
{
   notewin = window.open("", "DescWin", "width=600,height=400,scrollbars=yes,resizable=yes");

   notewin.document.write("<html><head><title>Help Document</title></head>\n" +
                          "<body style=\"font-size: 100%; font-family: helvetica,arial,verdana,sans-serif;\">\n");
   if(helpkey == "temp") { // temporal range help
      notewin.document.write("<table width=\"100%\">\n" +
                "<tr style=\"background-color: #336699\">\n" +
                "<th style=\"color: #ffffff; text-align:center; padding: 5px;\">\n" +
                "Temporal Range Selection</th></tr>\n" +
                "<tr><td style=\"font-size: medium; padding: 5px;\">\n" +
                "Choose the starting and ending dates that define the bounding dates for\n" +
                "your request, using the format YYYY-MM-DD. The bounding dates and all dates\n" +
                "in between will be included in the output data set.  The ending date must \n" + 
                "be later than or equal to the starting date.  Due to the large amount of data\n" +
                "produced for long temporal subset periods, please limit your request to one\n" +
                "year.  If you need more than one year of data, submit multiple data requests.\n" + 
                "</td></tr>\n" +
                "<tr><td style=\"font-size: medium; padding: 5px;\">\n" +
                "Click 'Reset Range' to re-select the full period of record.\n" +
                "</td></tr></table>\n");
   }
   if(helpkey == "spatial") { // Spatial subset preference help
      notewin.document.write("<table width=\"100%\">\n" +
                "<tr style=\"background-color: #336699\">\n" +
                "<th style=\"color: #ffffff; text-align:center; padding: 5px;\">\n" +
                "Spatial Subset Selection</th></tr>\n" +
                "<tr><td style=\"font-size: medium; padding: 5px;\">\n" +
                "The options for spatial subsetting are as follows:" +
                "</td></tr>\n" +
                "<tr><td style=\"font-size: medium; padding: 5px;\">\n" +
                "<ul>\n" + 
                "<li>Select region by latitude and longitude coordinates via Google map</li>\n" +
                "<li>Retain observations within a pre-defined NCEP verification region</li>\n" +
                "<li>Retain observations within a pre-defined NCEP storage grid</li>\n" +
                "<li>Select location(s) by station identifier</li>\n" +
                "</ul></td></tr></table>\n");

   }
   notewin.document.write("<form><center><input type=\"button\" value=\"Close This Window\" " +
           "onClick=\"self.close()\"></center></form>\n</body></html>\n");
   notewin.document.close();
   notewin.focus();
}


/**
 * function to show/hide google map
 */
function displayGoogleMap(act)
{
   var mapdisp = document.getElementById("mapselect");
   var mandisp = document.getElementById("manselect");

   if(act == 1) {
      mapdisp.style.display="block";
      mandisp.style.display="none";
      refreshMap('DrawBox');
      document.form.mapdisplayed.value = 1;
      document.form.latlondisplayed.value=1;
   } else {
      setSpaceValues();
      mapdisp.style.display="none";
      mandisp.style.display="block";
      document.form.mapdisplayed.value = 0;
      document.form.latlondisplayed.value=1;
   }
}

/**
 * function to show appropriate spatial subsetting selection
 */
function displayGridSelection(act)
{
   var mapdisp     = document.getElementById("mapselect");
   var mandisp     = document.getElementById("manselect");
   var polydisp    = document.getElementById("polySelect");
   var griddisp    = document.getElementById("gridSelect");
   var stationdisp = document.getElementById("stationSelect");
   var compdisp     = document.getElementById("compSelect");
   var submitdisp   = document.getElementById("review-button");

  // Null selection
  if (act == -1) {
    mapdisp.style.display="none";
    mandisp.style.display="none";
    stationdisp.style.display="none";
    polydisp.style.display="none";
    griddisp.style.display="none";
    compdisp.style.display="none";
    submitdisp.style.display="none";
    document.form.mapdisplayed.value=0;
    document.form.latlondisplayed.value=0;
    document.form.stationdisplayed.value=0;
    document.form.polydisplayed.value=0;
    document.form.griddisplayed.value=0;
  }
  
  // Google map lat/lon selection
  if (act == 0) {
    displayGoogleMap(1);
    stationdisp.style.display="none";
    polydisp.style.display="none";
    griddisp.style.display="none";
    if (document.form.dataFormat.value == 1) { 
      compdisp.style.display="block";
    } else {
      compdisp.style.display="none";
    }
    submitdisp.style.display="block";
    document.form.stationdisplayed.value=0;
    document.form.polydisplayed.value=0;
    document.form.griddisplayed.value=0;
//    loadDrawBoxMapJS('drawboxmap',20,0,1,'');
  }

  // NCEP verification region
  if (act == 1) {
    mapdisp.style.display="none";
    mandisp.style.display="none";
    stationdisp.style.display="none";
    polydisp.style.display="block";
    griddisp.style.display="none";
    compdisp.style.display="none";
    submitdisp.style.display="block";
    document.form.mapdisplayed.value=0;
    document.form.latlondisplayed.value=0;
    document.form.stationdisplayed.value=0;
    document.form.polydisplayed.value=1;
    document.form.griddisplayed.value=0;
  }

  // Interpolate to NCEP storage grid
  if (act == 2) {
    mapdisp.style.display="none";
    mandisp.style.display="none";
    stationdisp.style.display="none";
    polydisp.style.display="none";
    griddisp.style.display="block";
    compdisp.style.display="none";
    submitdisp.style.display="block";
    document.form.mapdisplayed.value=0;
    document.form.latlondisplayed.value=0;
    document.form.stationdisplayed.value=0;
    document.form.polydisplayed.value=0;
    document.form.griddisplayed.value=1;  
  }

  // Station ID
  if (act == 3) {
    mapdisp.style.display="none";
    mandisp.style.display="none";
    stationdisp.style.display="block";
    polydisp.style.display="none";
    griddisp.style.display="none";
    if (document.form.dataFormat.value == 1) { 
      compdisp.style.display="block";
    } else {
      compdisp.style.display="none";
    }
    submitdisp.style.display="block";
    document.form.mapdisplayed.value=0;
    document.form.latlondisplayed.value=0;
    document.form.stationdisplayed.value=1;
    document.form.polydisplayed.value=0;
    document.form.griddisplayed.value=0;    
  }
}

/**
 * function to display appropriate forms dependent on NetCDF or ASCII output
 */
function displayDataFormatSelection(format)
{
   var paramdisp     = document.getElementById("paramSelect");
   var typedisp      = document.getElementById("typeSelect");
   var pbtypedisp    = document.getElementById("pbTypeSelect");
   var inputtypedisp = document.getElementById("inputTypeSelect");
   var regiondisp    = document.getElementById("regionGridSelect");
   var compdisp      = document.getElementById("compSelect");
   var qualitydisp   = document.getElementById("qualityMarkFrame");
   var submitdisp    = document.getElementById("review-button");

// Null selection
   if(format == -1) {
     document.form.dataFormat.value=-1;
     paramdisp.style.display="none";
     typedisp.style.display="none";
     pbtypedisp.style.display="none";
     inputtypedisp.style.display="none";
     regiondisp.style.display="none";
     compdisp.style.display="none";
     qualitydisp.style.display="none";
     submitdisp.style.display="none";
     document.form.typedisplayed.value=0;
     document.form.pbtypedisplayed.value=0;
     document.form.compdisplayed.value=0;
     document.form.paramdisplayednc.value=0;
     document.form.paramdisplayedascii.value=0;
     document.form.qualitymarkdisplayed.value=0;
   }

// NetCDF output
   if(format == 0) {
     paramdisp.style.display="block";
     typedisp.style.display="block";
     pbtypedisp.style.display="block";
     inputtypedisp.style.display="block";
     regiondisp.style.display="block";
     compdisp.style.display="block";
     qualitydisp.style.display="block";
     submitdisp.style.display="block";
     document.form.typedisplayed.value=1;
     document.form.pbtypedisplayed.value=1;
     document.form.inputtypedisplayed.value=1;
     document.form.compdisplayed.value=1;
     document.form.paramdisplayednc.value=1;
     document.form.paramdisplayedascii.value=0;
     document.form.qualitymarkdisplayed.value=1;
     displayParameters(format);
     displayGridOptions(format);
     document.form.gridSelection.value=-1;
     displayGridSelection(document.form.gridSelection.value);
   }
   
// ASCII output
   if (format == 1) {
     paramdisp.style.display="block";
     typedisp.style.display="block";
     pbtypedisp.style.display="none";
     inputtypedisp.style.display="none";
     regiondisp.style.display="block";
     compdisp.style.display="block";
     qualitydisp.style.display="none";
     submitdisp.style.display="block";
     document.form.typedisplayed.value=1;
     document.form.pbtypedisplayed.value=0;
     document.form.inputtypedisplayed.value=0;
     document.form.compdisplayed.value=1;
     document.form.paramdisplayednc.value=0;
     document.form.paramdisplayedascii.value=1;
     document.form.qualitymarkdisplayed.value=0;
     displayParameters(format);
     displayGridOptions(format);
     document.form.gridSelection.value=-1;
     displayGridSelection(document.form.gridSelection.value);
   }
}

/**
 * Function to display the appropriate parameter list (dependent on output format)
 */
function displayParameters(format)
{
  var dptElem   = document.getElementById('dpt');
  var wdirElem  = document.getElementById('wdir');
  var windElem  = document.getElementById('wind');
  var rhElem    = document.getElementById('rh');
  var mixrElem  = document.getElementById('mixr');
  var prmslElem = document.getElementById('prmsl');
  var dptNode   = dptElem.nextSibling;
  var wdirNode  = wdirElem.nextSibling;
  var windNode  = windElem.nextSibling;
  var rhNode    = rhElem.nextSibling;
  var mixrNode  = mixrElem.nextSibling;
  var prmslNode = prmslElem.nextSibling;
  var dptCell   = document.getElementById('dptCell');
  var wdirCell  = document.getElementById('wdirCell');
  var windCell  = document.getElementById('windCell');
  var rhCell    = document.getElementById('rhCell');
  var mixrCell  = document.getElementById('mixrCell');
  var prmslCell = document.getElementById('prmslCell');

// NetCDF output  
  if (format == 0) {
    dptElem.disabled   = false;
    wdirElem.disabled  = false;
    windElem.disabled  = false;
    rhElem.disabled    = false;
    mixrElem.disabled  = false;
    prmslElem.disabled = false;
	dptNode.nodeValue = ' Dewpoint temperature (derived)';
	dptCell.style.color = '#000000';
	wdirNode.nodeValue = ' Wind direction (derived)';
	wdirCell.style.color = '#000000';
	windNode.nodeValue = ' Wind speed (derived)';
	windCell.style.color = '#000000';
	rhNode.nodeValue = ' Relative humidity (derived)';
	rhCell.style.color = '#000000';
	mixrNode.nodeValue = ' Humidity mixing ratio (derived)';
	mixrCell.style.color = '#000000';
	prmslNode.nodeValue = ' Pressure reduced to mean sea level (derived)';
	prmslCell.style.color = '#000000';
  }
  
// ASCII output
  if (format == 1) {
    dptElem.disabled   = true;
    wdirElem.disabled  = true;
    windElem.disabled  = true;
    rhElem.disabled    = true;
    mixrElem.disabled  = true;
    prmslElem.disabled = true;
	dptElem.checked    = false;
	windElem.checked   = false;
	rhElem.checked     = false;
	mixrElem.checked   = false;
	prmslElem.checked  = false;
	dptNode.nodeValue = ' Dewpoint Temperature (NetCDF only)';
	dptCell.style.color = '#A0A0A0';
	wdirNode.nodeValue = ' Wind direction (NetCDF only)';
	wdirCell.style.color = '#A0A0A0';
	windNode.nodeValue = ' Wind speed (NetCDF only)';
	windCell.style.color = '#A0A0A0';
	rhNode.nodeValue = ' Relative humidity (NetCDF only)';
	rhCell.style.color = '#A0A0A0';
	mixrNode.nodeValue = ' Humidity mixing ratio (NetCDF only)';
	mixrCell.style.color = '#A0A0A0';
	prmslNode.nodeValue = ' Pressure reduced to mean sea level (NetCDF only)';
	prmslCell.style.color = '#A0A0A0';
  }
}

/**
 * Function to display the grid subsetting options (dependent on output format)
 */
function displayGridOptions(format)
{
  var polyElem         = document.getElementById('polyOption');
  var ncepgridElem     = document.getElementById('ncepgridOption');
  
// NetCDF output  
  if (format == 0) {
    polyElem.innerHTML     = 'Retain observations within a pre-defined NCEP verification region';
    ncepgridElem.innerHTML = 'Retain observations within a pre-defined NCEP storage grid';
    polyElem.disabled      = false;
    ncepgridElem.disabled  = false;
  }
  
// ASCII output
  if (format == 1) {
    polyElem.innerHTML     = 'Retain observations within a pre-defined NCEP verification region (NetCDF only)';
    ncepgridElem.innerHTML = 'Retain observations within a pre-defined NCEP storage grid (NetCDF only)';
    if (document.form.gridSelection.value == 1 || document.form.gridSelection.value == 2) {
      displayGridSelection(-1);
    }
    polyElem.selected      = false;
    ncepgridElem.selected  = false;
    polyElem.disabled      = true;
    ncepgridElem.disabled  = true;
  }
}

/**
 * Review subset selections and submit to dsrqst.php
 */
function reviewRequest()
{
   var dsid, rtype;
   var rnote;
   var form = document.form;
   
   sflag = 0;

// Validate form inputs
   if(!checkDates()) return;
   if(!checkFormat()) return;
   if(!checkSpatialPref()) return;
   if(!checkStations()) return;
   if(!checkGrid()) return;
   if(form.latlondisplayed.value == 1 && !checkLatLon()) return;
   if(!checkParameters()) return;

   rtype = form.rtype.value;
   gindex = form.gindex.value;
   dsid = form.dsid.value;
   var postData;

   rnote = gather_request_info();
   $("#rnote-text").text(rnote);

   postData = {
      dsid: dsid,
      gindex: gindex,
      rtype: rtype,
      sflag: sflag,
      rinfo: rinfo,
      rnote: rnote
   };
   if (comp != "no") {
      postData.afmt = comp;
   }
   for (var key in postData) {
      $("#submit-form").append("<input type=\"hidden\" name=\"" + key + "\" value=\"" + postData[key] + "\">\n");
   }

   $("#subset-form-div").addClass("d-none");
   $("#subset-review-div").removeClass("d-none");
   $(document).scrollTop(0);
}

$(document).ready(function() {
   $("#submit-form").on("submit", function(event) {
      event.preventDefault();

      $("#subset-form-container").addClass("d-none");
      $("#loading-button").removeClass("d-none");

      var params = $(this).serialize();
      var dsid = document.form.dsid.value;
      $.post('/datasets/' + dsid + '/request/', params).done(function(data) {
         $("#ds_content").html(data);
         $(document).scrollTop(0);
      });
   });
});

function cancelRequest()
{
   // Cancel the request and return to subset form
   $("#subset-form-div").removeClass("d-none");
   $("#subset-review-div").addClass("d-none");
   $(document).scrollTop(0);
}

/**
 * gather the selected information into a string buffer
 */
function gather_request_info()
{   
   var rnote;
   var lats, lons, qualMark;
   var poly, ncepgrid;
   var form = document.form;

   dates = form.startDate.value + ' ' + 
           form.startTime.value + ' ' +
           form.endDate.value + ' ' + 
           form.endTime.value;
   lats = form.blat.value + " " + form.tlat.value;
   lons = form.llon.value + " " + form.rlon.value;
   qualMark = form.qualityMarkThreshold.value;
   poly = form.poly.value;
   ncepgrid = form.mapProjection.value;
   
   getTypes();
   getPBTypes();
   getInputTypes();
   comp = get_compress_info();

   rnote = "Date Limits               : " + dates
   rinfo = "dates=" + dates

   if(form.latlondisplayed.value == 1) {
     rnote += "\nLatitude Limits           : " + lats +
                 "\nLongitude Limits          : " + lons;
     rinfo += "&lats=" + lats + "&lons=" + lons;
   } else if (form.polydisplayed.value == 1) {
     rnote += "\nNCEP Verification Regions : " + poly;
     rinfo += "&poly=" + poly;
   } else if (form.griddisplayed.value == 1) {
     rnote += "\nNCEP Grid Number          : " + ncepgrid;
     rinfo += "&ncepgrid=" + ncepgrid;
   } else if (form.stationdisplayed.value == 1) {
     rnote += "\nStation ID                : " + stations;
     rinfo += "&station=" + stations;
   }   

   rnote += "\nParameters                : " + parameters;
   rinfo += "&params=" + parameters;
   
   if(form.typedisplayed.value == 1 && types) {
       rnote += "\nPREPBUFR Message Types    : " + types;
       if (types != "ALL") rinfo+= "&types=";
   }
   
   if(form.pbtypedisplayed.value == 1 && pbtypes) {
       rnote += "\nPREPBUFR Report Types     : " + pbtypes;
       if (pbtypes != "ALL") rinfo+= "&pbtypes=" + pbtypes;
   }

   if(form.inputtypedisplayed.value == 1 && inputtypes) {
       rnote += "\nInput Report Types        : " + inputtypes;
       if (inputtypes != "ALL") rinfo+= "&inputtypes=" + inputtypes;
   }

   if(form.qualitymarkdisplayed.value == 1) {
     rnote += "\nQuality Mark Threshold    : " + qualMark;
     rinfo += "&qualmark=" + qualMark;
   }
   
   if(form.compdisplayed.value == 1 && comp != "no") {
     rnote += "\nFile Compression          : " + comp;
   }

   if(form.dataFormat.value == 0) {
     rnote += "\nData Output Format        : " + "NETCDF";
     rinfo += "&format=" + 'NETCDF';   
   }
   if(form.dataFormat.value == 1) {
     rnote += "\nData Output Format        : " + "ASCII";
     rinfo += "&format=" + 'ASCII';
   }

   rinfo += "&gindex=" + form.gindex.value;
   
   return rnote;
}

function get_compress_info()
{
   var i, idx;
   var comps = document.form.elements['comp'];
   
   idx = 0;
   for(i = 0; i < comps.length; i++) {
      if(comps[i].checked) {
         return comps[i].value;
      }
   }
   return "no";
}

/**
 * Add additional fields to station ID form input
 */
function addStation()
{
  if (stationCounter == stationLimit) {
    alert("You have reached the limit of " + stationCounter + " station inputs");
  } else if (stationCounter < stationLimit/2) {
    var tbl = document.getElementById('stationTable');
    var lastRow = tbl.rows.length;
    var row = tbl.insertRow(lastRow);
    
    // Left cell
    var cellLeft = row.insertCell(0);
    cellLeft.className="body";
    cellLeft.style.textAlign="left";
    cellLeft.appendChild(document.createTextNode('Station '+(stationCounter+1)+' '));

    // Right cell
    var cellRight = row.insertCell(1);
    var elem = document.createElement('input');
    elem.type = 'text';
    elem.name = 'station' + stationCounter;
    elem.id = 'station' + stationCounter;
    elem.size = 5;
    elem.maxlength = 5;
    cellRight.appendChild(elem);

    // Add two more blank cells
    var cellThree = row.insertCell(2);
    cellThree.className="body";
    cellThree.style.textAlign="left";
    var cellFour  = row.insertCell(3);
  
    stationCounter++;
  } else {
    var tbl = document.getElementById('stationTable');
    var thisRow = stationCounter-(stationLimit/2);
    tbl.rows[thisRow].cells[2].appendChild(document.createTextNode('Station '+(stationCounter+1)+' '));
    var elem = document.createElement('input');
    elem.type = 'text';
    elem.name = 'station' + stationCounter;
    elem.id = 'station' + stationCounter;
    elem.size = 5;
    elem.maxlength = 5;
    tbl.rows[thisRow].cells[3].appendChild(elem);
    stationCounter++;
  }
}

/**
 * Select all parameters
 */
function selectAllParams()
{
  for (var i=0; i<document.form.parameter.length; i++) {
	if(!document.form.parameter[i].disabled)
	  document.form.parameter[i].checked = true;
  }
}

/**
 * Clear parameter selections
 */
function selectNoParams()
{
  for (var i=0; i<document.form.parameter.length; i++) {
	document.form.parameter[i].checked = false;
	}
}

/**
 * Select all PREPBUFR message types
 */
function selectAllTypes()
{
  for (var i=0; i<document.form.msgtype.length; i++) {
	if(!document.form.msgtype[i].disabled)
	  document.form.msgtype[i].checked = true;
  }
}

/**
 * Clear PREPBUFR message type selections
 */
function selectNoTypes()
{
  for (var i=0; i<document.form.msgtype.length; i++) {
	document.form.msgtype[i].checked = false;
	}
}

/**
 * Select all PREPBUFR report types
 */
function selectAllPBTypes()
{
  for (var i=0; i<document.form.pbtype.length; i++) {
	if(!document.form.pbtype[i].disabled)
	  document.form.pbtype[i].checked = true;
  }
}

/**
 * Clear PREPBUFR report type selections
 */
function selectNoPBTypes()
{
  for (var i=0; i<document.form.pbtype.length; i++) {
	document.form.pbtype[i].checked = false;
	}
}

/**
 * Select all input report types
 */
function selectAllInputTypes()
{
  for (var i=0; i<document.form.inputtype.length; i++) {
	if(!document.form.inputtype[i].disabled)
	  document.form.inputtype[i].checked = true;
  }
}

/**
 * Clear input report type selections
 */
function selectNoInputTypes()
{
  for (var i=0; i<document.form.inputtype.length; i++) {
	document.form.inputtype[i].checked = false;
	}
}
