/***********************************************************************************
 * 
 *     Title : ADP_subset.js
 *    Author : Thomas Cram (tcram@ucar.edu),
 *      Date : 12/15/2010
 *   Purpose : javascript program to validate the form inputs for subset requests from 
 *             the NCEP ADP BUFR datasets (d351000 and d461000).
 * Work File : $DSSWEB/js/ADP_subset.js
 * Test File : $DSSWEB/js/ADP_subset_test.js
 ***********************************************************************************/
 

// var dates, stations, rectypes, allbasic, parms, xparms, compr, vars, flts, rinfo;
var dates, stations, rectypes, parms, compr, rinfo, allbasic;
var stationNum, countValid;
var ivals, evals;

/* 
   Function is a constructor for an object {struct} that holds current state of 
   subsetting values whn called. Current implementation is to call at load and submit
   to compare initial and ending values and set bit flag accordingly.

   Returns: Object whose attributes are current values

   Related:

       variables: ivals, evals
       functions: countchecked, initvals, sflagtest, alert_vals
*/
function getsubsetvals() {
    ss = new Object();
    ss.start_date = document.form.startDate.value;
    ss.end_date = document.form.endDate.value;
    ss.tlat = document.form.tlat.value;
    ss.blat = document.form.blat.value;
    ss.llon = document.form.llon.value;
    ss.rlon = document.form.rlon.value;

    // Get all stations by class name (Note: does not work for IE <= 8)
    // loop trough stns and concat values; store to object
    var s = document.getElementsByClassName("stns");
    stn = '';
    for (var k = 0; k < s.length; k++) { stn += s[k].value; }
    ss.stations = stn; 

    ss.rectypes = countchecked('rectypes');
    ss.params = countchecked('parms');
    return ss
}

/* 
   Function takes input type name='_name' & counts all checked
   Returns: # of boxes checked for _name
*/
function countchecked(_name) {
    cnt = 0;
    rts = document.getElementsByName(_name);
    for (i = 0; i < rts.length; ++i) {    
        if (rts[i].checked) { cnt++; }
    }
    return cnt
}

/* Function to grab initial values. Called "onload" of page body */
function initvals() {
    ivals = getsubsetvals();
    //alert_vals(ivals);
}

/* Debugging function to spit out current values of 'i'. Assumes 'i' is getsubsetvals */
function alert_vals(i) {

    str = '';
    for (var key in i) {
        str += '[' +key + ']: ' + i[key] + "\n";
    }
    alert(str);
}

/*
    Function to compare two getsubsetvals objects, usually at inital and submit states.
    Assumes identical attribute keys. Based on subset type (spatial, temporal, variable)
    sets bit flag.  Final bit flag is sum of bit flags per Hua's email on 18 July 2013:

    "The field sflag is a bit flag, it needs set to 1 - for partial variable selection, 
     2 - for partial temporal selection, 4 - for partial spatial selection , 
     or combination of them."

     Returns: bit flag total of subsetting options
*/
function sflagtest(b,e) {
    sflag = 0;
    tmpflag = 0;
    varflag = 0;
    spaflag = 0;

    // Loop thru keys, compare corresponding vals of b,e
    for (var key in b) {

      // variable
      if (key === 'rectypes' || key === 'parms') {
        if (b[key] !== e[key]) { varflag = 1 }
      }

      // temporal
      if (key === 'start_date' || key === 'end_date') {
        if (b[key] !== e[key]) { tmpflag = 2 }
      }

      // spatial
      if (key === 'tlat' || key === 'blat' || key === 'llon' || key === 'rlon' 
                                                         || key === 'stations') {
        if (b[key] !== e[key]) { spaflag = 4 }
      }

    }

    sflag = varflag + tmpflag + spaflag;
    return sflag;
}

/**
 * function to reset the temporal selections
 * somehow this uses metadata from the dataset (ds461.0) 
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
function checkDates()
{
  if (document.form.startDate.value.length != 10 || document.form.endDate.value.length != 10) 
  {
    alert("Enter dates as \'YYYY-MM-DD\'");
    return false;
  }

  var isGoodDate=true;

  for (n=0; n < 10; n++) 
  {
    if (n <= 3 || n == 5 || n == 6 || n == 8 || n == 9) 
    {
      if (document.form.startDate.value.charAt(n) < '0' || document.form.startDate.value.charAt(n) > '9' || document.form.endDate.value.charAt(n) < '0' || document.form.endDate.value.charAt(n) > '9')
        isGoodDate=false;
    }
    else if (n == 4 || n == 7) 
    {
      if (document.form.startDate.value.charAt(n) != '-' || document.form.endDate.value.charAt(n) != '-')
        isGoodDate=false;
    }
  }

  if (!isGoodDate) 
  {
    alert("Enter dates as YYYY-MM-DD");
    return false;
  }

//if ((document.form.startDate.value+' '+document.form.startTime.value) > (document.form.endDate.value+' '+document.form.endTime.value)) 
  if (document.form.startDate.value > document.form.endDate.value)
  {
//  alert("The start date and time must precede the end date");
    alert("The start date must precede the end date");
    return false;
  }

  var startValue = document.form.startDate.value;
  var endValue   = document.form.endDate.value;
  var startYearFloat  = parseFloat(startValue.substr(0,4));
  var endYearFloat    = parseFloat(endValue.substr(0,4));
  var startMonthFloat = parseFloat(startValue.substr(5,1));
  var endMonthFloat   = parseFloat(endValue.substr(5,1));
  
  if ( ((endYearFloat - startYearFloat) * 12 + (endMonthFloat - startMonthFloat)) > 12) 
  {
    alert("Please select a temporal range equal to or less than one year.  Submit multiple data requests if you wish to request data for more than one year.");
    return false;
  }
  
 return true;
 
} 

/**
 * Validate station ID form inputs
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

   stationInput = document.getElementById("station0").value;
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
   
   return true;
}

/**
 * Validate record type checkbox selections
 */

function checkRectypes()
{
  var num_checkboxes=0;
  var num_checked=0;
  rectypes = "";
  var checkedArray = new Array();

  num_checkboxes = document.form.rectypes.length;
  
  for (i=0; i < document.form.rectypes.length; i++) 
  {
    if (document.form.rectypes[i].type == "checkbox" && document.form.rectypes[i].checked) 
    {
      num_checked++;
      checkedArray.push(document.form.rectypes[i].value)
    }
  }

  if (num_checked == 0) 
  {
    alert("Please select at least one record type");
    return false;
  } 
  else 
  { 
    rectypes = checkedArray.join(" ");
  }
  return true;
}

/**
 * Validate spatial subset preference
 *
 */
function checkSpatial()
{
  gridSelection = $('[name="gridSelection"]').val();

  if(gridSelection == -1)
  {
    alert("Please select a spatial subset preference");
    return false;
  } 
  else if(gridSelection == 0)
  {
    return checkLatLon();
  }
  else if(gridSelection == 1)
  {
    return checkStations();
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
   var i, j;
   var min, max;
   var value, unit;

   i = 0;

   gridSelection = $('[name="gridSelection"]').val();
   if(gridSelection == 1) setSpaceValues();
   
   max = goodCoordinate(form.tlat.value, true);
   if(max == 999) 
   {
      alert("Top latitude was entered improperly.\nRe-enter as a positive number, followed by a space, followed by 'N' or 'S'.");
      return false;
   }
   
// Verify a space exists between the lat/lon coordinate number and direction
   value = form.tlat.value;
   unit = value.charAt(value.length - 1);
   form.tlat.value = parseFloat(value).toFixed(1) + " " + unit.toUpperCase();
   
   min = goodCoordinate(form.blat.value, true);
   if(min == 999) 
   {
     alert("Bottom latitude was entered improperly.\nRe-enter as a positive number, followed by a space, followed by 'N' or 'S'.");
     return false;
   }
   if(max < min) 
   {
     alert("Bottom latitude cannot exceed Top latitude.\nRe-enter the latitudes.");
     return false;
   }
// Verify a space exists between the lat/lon coordinate number and direction
   value = form.blat.value;
   unit = value.charAt(value.length - 1);
   form.blat.value = parseFloat(value).toFixed(1) + " " + unit.toUpperCase();
   
   if(max == 90) i++;
   if(min == -90) i++;
   max = goodCoordinate(form.rlon.value, false);
   if(max == 999) 
   {
     alert("Right longitude was entered improperly.\nRe-enter as a positive number, followed by a space, followed by 'E' or 'W'.");
     return false;
   }
// Verify a space exists between the lat/lon coordinate number and direction
   value = form.rlon.value;
   unit = value.charAt(value.length - 1);
   form.rlon.value = parseFloat(value).toFixed(1) + " " + unit.toUpperCase();

   min = goodCoordinate(form.llon.value, false);
   if(min == 999) 
   {
     alert("Left longitude was entered improperly.\nRe-enter as a positive number, followed by a space, followed by 'E' or 'W'.");
     return false;
   }
   if(max < min && min - max < 180.0 && !document.map) 
   {
     if(!confirm("Left longitude (" + form.llon.value + 
                 ") exceeds Right Longitude (" +
                 form.rlon.value + ")!\n(Click OK to " +
                        "continue or Cancel to re-enter longitude values)")) 
     {
        return false;
     }
   }
// Verify a space exists between the lat/lon coordinate number and direction
   value = form.llon.value;
   unit = value.charAt(value.length - 1);
   form.llon.value = parseFloat(value).toFixed(1) + " " + unit.toUpperCase();

   if(max == 180) i++;
   if(min == -180) i++;
   if(i == 4 && !confirm("Default Spatial Range (" + form.llon.value + ", " +
                         form.rlon.value + "; " + form.blat.value + ", " +
                         form.tlat.value + ") selected!\n(Click OK to " +
                         "continue or Cancel to re-enter the values)")) 
   {
      return false;
   }
   return true;
}

function setSpaceValues()
{
   var form = document.form;
   var tmp;
   
   tmp = $("#gdrawboxmap_nlat").val();
   if(tmp >= 0.) 
   {
      form.tlat.value = tmp + ".0 N";
   } 
   else 
   {
      form.tlat.value = (-tmp) + ".0 S";
   }
   tmp = $("#gdrawboxmap_slat").val();
   if(tmp >= 0.) 
   {
      form.blat.value = tmp + ".0 N";
   } 
   else 
   {
      form.blat.value = (-tmp) + ".0 S";
   }
   tmp = $("#gdrawboxmap_wlon").val();
   if(tmp >= 0.) 
   {
      form.llon.value = tmp + ".0 E";
   } 
   else 
   {
      form.llon.value = (-tmp)+".0 W";
   }
   tmp = $("#gdrawboxmap_elon").val();
   if(tmp >= 0.) 
   {
      document.form.rlon.value = tmp + ".0 E";
   } 
   else 
   {
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
   
   if(value.charAt(0) == '-') 
   {
      return 999;
   }
   nvalue=parseFloat(value);
   if(islat) 
   {
     if(nvalue > 90.0 || nvalue < 0.0) 
     {
       return 999;
     }
     if(unit == 'S') 
     {
       nvalue = -nvalue;
     } 
     else if(unit != 'N') 
     {
       return 999;
     }
   } 
   else  
   {
     if(nvalue > 360.0 || nvalue < 0.0) 
     {
       return 999;
     }
     if(unit == 'W') 
     {
       nvalue=-nvalue;
     } 
     else if(unit != 'E') 
     {
       return 999;
     }
   }
   return nvalue;
}

/**
 * Validate parms checkbox selections
 */

function checkParameters()
{
/**
 * may need to setup a popup menu for extra parameters
 * <input type="button" onclick="popup()" value="popup">
 */

  var num_checkboxes=0;
  var num_checked=0;
  var count=0;
  var checkedArray = new Array();

  allbasic = "y";
  parms = "";

  num_checkboxes = document.form.parms.length;
  
  for (i=0; i < document.form.parms.length; i++) 
  {
    if (document.form.parms[i].type == "checkbox" && document.form.parms[i].checked) 
    {
      num_checked++;
      checkedArray.push(document.form.parms[i].value)
    }
    if (document.form.parms[i].type == "checkbox" && !document.form.parms[i].checked)  {
        allbasic = "n";
     }
  }

  if (num_checked == 0) 
  {
    alert("Please select at least one parameter");
    return false;
  } 
  else 
  {
    parms = checkedArray.join(" ");
  }
  return true;
}

/**
 * function to show/hide google map
 */
function displayGoogleMap(act)
{
   if(act == 1) 
   {
      $("#mapselect").show();
      refreshMap('DrawBox');
      document.form.mapdisplayed.value = 1;
      document.form.latlondisplayed.value=1;
   } 
   else 
   {
      setSpaceValues();
      $("#mapselect").hide();
      document.form.mapdisplayed.value = 0;
      document.form.latlondisplayed.value=1;
   }
}

/**
 * function to show appropriate spatial subsetting selection
 */
function displayGridSelection(value)
{
  // Null selection
  if (value == -1) 
  {
    $("#mapselect").hide();
    $("#stationSelect").hide();
    document.form.mapdisplayed.value=0;
    document.form.latlondisplayed.value=0;
    document.form.stationdisplayed.value=0;
  }
  
  // Google map lat/lon selection
  if (value == 0) 
  {
    displayGoogleMap(1);
    $("#stationSelect").hide();
    document.form.stationdisplayed.value=0;
  }

  // Station ID
  if (value == 1) {
    $("#mapselect").hide();
    $("#stationSelect").show();
    document.form.mapdisplayed.value=0;
    document.form.latlondisplayed.value=0;
    document.form.stationdisplayed.value=1;
  }
}

/**
 * gather the selected information into a string buffer
 */
function gather_request_info()
{
   var rqstinfo;
   var lats, lons;
   var form = document.form;

   dates = document.form.startDate.value + ' ' + 
           document.form.endDate.value;
//         document.form.startTime.value + ' ' +
//         document.form.endDate.value + ' ' + 
//         document.form.endTime.value;
   lats = form.blat.value + " " + form.tlat.value;
   lons = form.llon.value + " " + form.rlon.value;

   compr = get_compress_info();

// note the ampersands (&) leading each field in the rinfo string
//   these are delimiters for the info string sent to dsrqst 

   rqstinfo    = "\nDate Limits               : " + dates;
   rinfo  = "&dates=" + dates;

   if(form.latlondisplayed.value == 1) 
   {
     rqstinfo += "\nLatitude Limits           : " + lats +
                 "\nLongitude Limits          : " + lons;
     rinfo += "&lats=" + lats + "&lons=" + lons;
   }  else if (form.stationdisplayed.value == 1) {
     rqstinfo += "\nStation ID                : " + stations;
     rinfo += "&station=" + stations;
   }

   rqstinfo   += "\nRecord Types              : " + rectypes; 
   rinfo += "&rectypes=" + rectypes;

   // rqstinfo   += "\nAll Basic Parameters      : " + allbasic;
   rinfo += "&allbasic=" + allbasic;

   rqstinfo   += "\nParameters                : " + parms; 
   rinfo += "&parms=" + parms;

   rqstinfo   += "\nCompression               : " + compr; 
   rinfo += "&compr=" + compr;

/**
 * rqstinfo is not a global variable, but we can return it as if it
 *   were in a Fortran argument list
 */
   return rqstinfo + "\n";
}

/**
 * check if user selection of compression
 */
function get_compress_info()
{
   var i, idx;
   var comprs = document.form.elements['compression'];
   
   idx = 0;
   for(i = 0; i < comprs.length; i++) {
      if(comprs[i].checked) {
         return comprs[i].value;
      }
   }
   return "None";
}

/**
 * Review subset selections and submit request
 */
function reviewRequest()
{
   var dsid, rindex, rtype;
   var rnote;
   var form = document.form;

// Validate form inputs
   if(!checkSpatial()) return;
   if(!checkDates()) return;
   if(!checkStations()) return;
   if(form.latlondisplayed.value == 1 && !checkLatLon()) return;
   if(!checkParameters()) return;
   if(!checkRectypes()) return;

   rtype = form.rtype.value;
   gindex = form.gindex.value;    
   dsid = form.dsid.value;
   var title = dsid;
   var postData, formContent;

   rnote = gather_request_info();
   $("#rnote-text").text(rnote);

// Get current values for subsetting; compare to initial vals, and calc sflag
// MUST BE CALLED AFTER 'gather_request_info()'
   evals = getsubsetvals();
   sflag = sflagtest(ivals,evals);

   postData = {
      dsid: dsid,
      gindex: gindex,
      rtype: rtype,
      sflag: sflag,
      rinfo: rinfo,
      rnote: rnote
   };
   if (compr != "None") {
      postData.afmt = compr;
   }
   for (var key in postData) {
      $("#submit-form").append("<input type=\"hidden\" name=\"" + key + "\" value=\"" + postData[key] + "\">\n");
   }

   $("#subset-form-div").addClass("d-none");
   $("#subset-review-div").removeClass("d-none");
   $(document).scrollTop(0);
}

$(document).ready(function() {
   initvals();
   selectAllRectypes();
   selectAllParms();

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
 * Select all parms
 */
function selectAllParms()
{
  for (var i=0; i<document.form.parms.length; i++) 
  {
    if(!document.form.parms[i].disabled)
    {
      document.form.parms[i].checked = true;
    }
  }
  //allbasic = "y";
}

/**
 * Clear parms selections
 */
function selectNoParms()
{
  for (var i=0; i<document.form.parms.length; i++) 
  {
    document.form.parms[i].checked = false;
  }
  //allbasic = "n";
}


/**
 * Select all rectypes
 */
function selectAllRectypes()
{
  for (var i=0; i<document.form.rectypes.length; i++)
  {
    if(!document.form.rectypes[i].disabled)
    {
      document.form.rectypes[i].checked = true;
    }
  }
}

/**
 * Clear rectype selections
 */
function selectNoRectypes()
{
  for (var i=0; i<document.form.rectypes.length; i++) 
  {
    document.form.rectypes[i].checked = false;
  }
}


