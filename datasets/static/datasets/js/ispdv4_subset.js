/***********************************************************************************
 * 
 *     Title : ispdv4_subset.js
 *    Author : Thomas Cram (tcram@ucar.edu)
 *      Date : 02/14/2020
 *   Purpose : javascript program to validate the form inputs for subset requests
 *             from ISPD version 4 (d132002)
 * Work File : $DSSWEB/js/ispdv4_subset.js
 * Test File : $DSSWEB/js/ispdv4_subset_test.js
 *
 ***********************************************************************************/

var dates, stations, locations, types, typecodes, fmt, comp, rinfo, sflag;
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
  
  var minDate, minYear, minMon, minDay;
  var maxDate, maxYear, maxMon, maxDay;
  var startDate, endDate;
  var n;
  var minDateInt, maxDateInt, startDateInt, endDateInt;

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
  if (document.form.startDate.value > document.form.endDate.value) {
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

  minDate = document.getElementById("minDate").value;
  minYear = minDate.substr(0,4);
  minMon  = minDate.substr(5,2);
  minDay  = minDate.substr(8,2);
  minDateInt = parseInt(minYear.concat(minMon,minDay));
  
  maxDate = document.getElementById("maxDate").value;
  maxYear = maxDate.substr(0,4);
  maxMon  = maxDate.substr(5,2);
  maxDay  = maxDate.substr(8,2);
  maxDateInt = parseInt(maxYear.concat(maxMon,maxDay));
  
  startDateInt = parseInt(startYear.concat(startMon,startDay));
  endDateInt = parseInt(endYear.concat(endMon,endDay));

  if(startDateInt < minDateInt || endDateInt > maxDateInt) {
    alert("The valid date range is " + minDate + " to " + maxDate + ".  Please revise your date selections.");
    return false;
  }

// Limit requests to 50 years or less    
//  if ( ((endYearFloat - startYearFloat) * 12 + (endMonthFloat - startMonthFloat)) > 600) {
//    alert("Please select a temporal range equal to or less than 50 years.  Submit multiple data requests if you wish to request data for more than 25 years.");
//    return false;
//  }
  
  // Set subsetting bit flag for partial temporal selection
  if(startDate > minDate) {
    sflag |= 2;
  } else {
    if(endDate < maxDate) {
      sflag |= 2;
    }
  }

 return true; 
} 

/** Validate and process spatial selection */
function checkSpatial()
{
   regionSelection = $('#gridSelectionMenu').val();

   if (regionSelection == "-1" || regionSelection == null) {
      alert("Please select a spatial range option from the dropdown menu.");
      return false;
   }
   if(regionSelection == "1") {
      return checkLatLon();
   }
   if(regionSelection == "2") {
      return checkStations();
   }
   if(regionSelection == "3") {
      return getLocations();
   }
   return true;
}

/**
 * Validate location selection
 *
 */
function checkStations()
{
   var i;
   var stationInput;
   var countEmpty, countValid;
   var stns, stn;
   var patt = new RegExp(/^\s*$/);
   
   stations = "";
   
   // check stations
   countValid = 0;   // Count the valid entries

   stationInput = document.getElementById("stationIDs").value;
   if (stationInput == "" || stationInput == null) {
      alert("Please enter at least one station ID or select a different spatial range option.");
      return false;
   }

// trim any leading and/or trailing commas, white space.
   if (stationInput != "") {
     stationInput = stationInput.replace(/(^\s*)|(,\s*$)/g, "");
     stationInput = stationInput.replace(/(^,)|(,$)/g, "");
     countValid++;
   }

// Validate input for 5 or 6 character length
   stns = stationInput.split(",");
   for(i=0; i<=stns.length-1; i++) {
     stn = stns[i].trim();

     // skip if blank string
     if (patt.test(stn)) {
       continue;
     }
     
     // return false if invalid value
     if (stn.length < 5 || stn.length > 6) {
       alert("Invalid value entered for station "+stn+" - must be 5 or 6 digits");
       return false;
     }
     
     if (!stations) {
       stations = stn;
     } else {
       stations += "," + stn;
     }
   }   
   
// Set subsetting bit flag for partial spatial selection
   if(countValid > 0) {
     sflag |= 4;
   }
   return true;
}

/**
 * Validate location selection
 *
 */
function getLocations()
{
   var locationInput;
   var countEmpty;
   var locs, loc;
   var patt = new RegExp(/^\s*$/);
   
   locations = "";
   
   // check locations
   countValid = 0;   // Count the valid entries

   locationInput = document.getElementById("location0").value;
   if (locationInput == "" || locationInput == null) {
      alert("Please enter at least one location name or select a different spatial range option.");
      return false;
   }

// trim any leading and/or trailing commas, white space
   if (locationInput != "") {
     locationInput = locationInput.replace(/(^\s*)|(,\s*$)/g, "");
     locationInput = locationInput.replace(/(^,)|(,$)/g, "");
     countValid++;
   }
   
// Validate input
   locs = locationInput.split(",");
   for(i=0; i<=locs.length-1; i++){
     loc = locs[i].trim();
     
     // skip if blank string
     if(patt.test(loc)){
       continue;
     }
     
     if(!locations){
       locations = loc;
     } else {
       locations += "," + loc;
     }
   }

// Set subsetting bit flag for partial spatial selection
   if(countValid > 0) {
     sflag |= 4;
   }
   return true;
}

/**
 * functions to validate latitude and longitude form inputs
 *
 */
function checkLatLon()
{
   var form = document.form;
   var i;
   var min, max;
   var value, unit;
   
   i = 0;
   setSpaceValues();
   
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

   if(i == 4 && !confirm("Default Spatial Range (" + form.llon.value + ", " +
                         form.rlon.value + "; " + form.blat.value + ", " +
                         form.tlat.value + ") selected!\n(Click OK to " +
                         "continue or Cancel to re-enter the values)")) {
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
 * Get NCEP observation type checkbox selections
 */

function getTypes()
{
   var i, thisType, typeCheck, typeCount;
   var tccodes;
   types = "";
   typecodes = "";
   typeCount = 0;

  for(i = 0; i < document.form.obstype.length; i++) {
    if(document.form.obstype[i].checked) {
      if (!types) {
        types = document.form.obstype[i].value;
      } else {
        types += ", " + document.form.obstype[i].value;
      }
      typeCount++;
    }
  }
  
  if(typeCount == document.form.obstype.length){
    return true;
  }
  
  for(i = 0; i < document.form.obstype.length; i++) {
    thisType = document.form.obstype[i].value;
    typeCheck = document.form.obstype[i].checked;
    if(thisType && typeCheck) {
      switch (thisType)
      {
      case "RADIOSONDE":
        if(!typecodes) {
          typecodes = "120";
        } else {
          typecodes += ", 120";
        }
        break;
      case "DROPSONDE":
        if(!typecodes) {
          typecodes = "132";
        } else {
          typecodes += ", 132";
        }
        break;
      case "MARINE":
        if(!typecodes) {
          typecodes = "180";
        } else {
          typecodes += ", 180";
        }
        break;
      case "SFC_STATION":
        if(!typecodes) {
          typecodes = "181, 183";
        } else {
          typecodes += ", 181, 183";
        }
        break;
      case "TC_BEST_TRACK":
        tccodes = "310, 320, 330, 340, 350, 360, 370, 380, 390, " +
                  "311, 321, 331, 341, 351, 361, 371, 381, 391, " + 
                  "312, 322, 332, 342, 352, 362, 372, 382, 392, " + 
                  "313, 323, 333, 343, 353, 363, 373, 383, 393, " + 
                  "314, 324, 334, 344, 354, 364, 374, 384, 394, " + 
                  "315, 325, 335, 345, 355, 365, 375, 385, 395, " + 
                  "410, 420, 430, 440, 450, 460, 470, 480, 490, " + 
                  "510, 520, 530, 540, 550, 560, 570, 580, 590, " + 
                  "511, 521, 531, 541, 551, 561, 571, 581, 591, " + 
                  "512, 522, 532, 542, 552, 562, 572, 582, 592, " + 
                  "513, 523, 533, 543, 553, 563, 573, 583, 593, " + 
                  "514, 524, 534, 544, 554, 564, 574, 584, 594, " + 
                  "515, 525, 535, 545, 555, 565, 575, 585, 595" ;
        if(!typecodes) {
          typecodes = tccodes;
        } else {
          typecodes += ", " + tccodes;
        }
        break;
      }  // end switch
    }  // end if(thisType)
  }  // end i loop
  return true;  
}

function displayGridSelection(value)
{
   if (value === "-1") {
      $('#mapselect').hide();
      $('#stationSelect').hide();
      $('#locationSelect').hide();
   } else if(value == "0") {
      $('#mapselect').show();
      $('#stationSelect').hide();
      $('#locationSelect').hide();
   } else if(value == "1") {
      $('#stationSelect').show();
      $('#mapselect').hide();
      $('#locationSelect').hide();
   } else if(value == "2") {
      $('#locationSelect').show();
      $('#mapselect').hide();
      $('#stationSelect').hide();
   }
}

/**
 * Review subset selections and submit request
 */
function reviewRequest()
{
   var dsid, rtype, gindex;
   var rnote;
   var form = document.form;

   sflag = 0;
   
// Validate form inputs
   if(!checkDates()) return;
   if(!checkSpatial()) return;

   rtype = form.rtype.value;
   gindex = form.gindex.value;
   dsid = form.dsid.value;

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
   var lats, lons;
   var form = document.form;

   dates = form.startDate.value + ' ' + form.endDate.value;
   lats = form.blat.value + ", " + form.tlat.value;
   lons = form.llon.value + ", " + form.rlon.value;
   getTypes();
   comp = get_compress_info();
   fmt = "ascii";

   rnote = "Date Limits           : " + dates;
   rinfo = "dates=" + dates;

   gridSelection = $('[name="gridSelection"]').val();
   if(gridSelection == "0") {
     rnote += "\nLatitude Limits       : " + lats +
              "\nLongitude Limits      : " + lons;
     rinfo += "&lats=" + lats + "&lons=" + lons;
   } else if (gridSelection == "1") {
     rnote += "\nStation ID            : " + stations;
     rinfo += "&stn=" + stations;
   } else if (gridSelection == "2") {
     rnote += "\nLocations              : " + locations;
     rinfo += "&loc=" + locations;
   }   

   if(types){
     rnote += "\nNCEP Observation Types: " + types;
   }
   if(typecodes){
     rinfo+= "&typ=" + typecodes;
   }
   
   rnote += "\nData format           : " + fmt;
   rinfo += "&fmt=" + fmt;
   
   if(comp != "no") {
     rnote += "\nFile Compression      : " + comp;
   }
   
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

function get_fmt_info()
{
   var i, idx;
   var fmts = document.form.elements['fmt'];
   
   idx = 0;
   for(i = 0; i < fmts.length; i++) {
      if(fmts[i].checked) {
         return fmts[i].value;
      }
   }
   return "ascii";
}

/**
 * Select all NCEP observation types
 */
function selectAllTypes()
{
   $('input[name="obstype"]').prop('disabled', false).each(function() {
       $(this).prop('checked', true);
   });
}

/**
 * Clear NCEP observation type selections
 */
function selectNoTypes()
{
   $('input[name="obstype"]').prop('disabled', false).each(function() {
       $(this).prop('checked', false);
   });
}
