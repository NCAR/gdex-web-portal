/***********************************************************************************
 * 
 *     Title : imma1_subset.js
 *    Author : Zaihua Ji,  zji@ucar.edu
 *      Date : 07/05/2016
 *   Purpose : javascript program to validate the form inputs for request of 
 *             ICOADS sub-dataset in IMMA1 format.
 * Work File : $DSSWEB/js/imma1_subset.js
 *
 ***********************************************************************************/
 
var dates, flts, vars, comp, tarflag, rinfo, sflag, reanqcs, ivads;
var dcks, pts, sids;
var corevars, icoadsvars, immts, modqcs, metavos, nocns, ecrs;
var FP = 100;

/**
 * function to reset the checkbox selections for record elements
 *
 */
function resetSelection(attm) {
   var items = document.getElementsByName(attm);
   var i;
   
   for(i = 0; i < items.length; i++) {
      items[i].checked = false;
   }

   if(attm == 'core') {  // match initial setting of $CORE in imma1_subset.inc
      items[0].checked = true;
      items[1].checked = true;
      items[2].checked = true;
      items[3].checked = true;
      items[4].checked = true;
      items[5].checked = true;
   } else if(attm == 'icoads') { // match initial setting of $ICOADS in imma1_subset.inc
      items[2].checked = true;
      items[3].checked = true;
      items[4].checked = true;
   } else if(attm == 'addon') { // match initial setting of $ADDONS in imma1_subset.inc
      items[0].checked = true;
   }
}
      
/**
 * function to reset the temporal selections
 *
 */
function resetTemporal(sdate, edate) 
{
   document.getElementById('startDate').value = sdate;
   document.getElementById('endDate').value   = edate;
}

/**
 * functions to valid inputs
 *
 */
function checkSelection()
{
   if(!checkDates()) return false;
   if(!checkFilter()) return false;
   if(!checkLatLon()) return false;
   if(!checkVariables()) return false;
   if(!checkReanqc()) return false;
   if(!checkIvad()) return false;   
   return true;
}

/**
 * Validate start and end date form inputs
 *
 */
function checkDates() {
  
  var minDate, minYear, minMon, minDay;
  var maxDate, maxYear, maxMon, maxDay;
  var startDate, endDate;

  startDate = document.getElementById("startDate");
  endDate = document.getElementById("endDate");
  
  if (startDate.value.length != 10 || endDate.value.length != 10) {
    alert("Enter dates as \'YYYY-MM-DD\'");
    return false;
  }
  var isGoodDate=true;
  for (n=0; n < 10; n++) {
    if (n <= 3 || n == 5 || n == 6 || n == 8 || n == 9) {
      if (startDate.value.charAt(n) < '0' || startDate.value.charAt(n) > '9' || endDate.value.charAt(n) < '0' || endDate.value.charAt(n) > '9')
        isGoodDate=false;
    }
    else if (n == 4 || n == 7) {
      if (startDate.value.charAt(n) != '-' || endDate.value.charAt(n) != '-')
        isGoodDate=false;
    }
  }
  if (!isGoodDate) {
    alert("Enter dates as YYYY-MM-DD");
    return false;
  }
  if (startDate.value > endDate.value) {
    alert("The start date must precede the end date");
    return false;
  }

  var startYear = startDate.value.substr(0,4);
  var startMon  = startDate.value.substr(5,2);
  var startDay  = startDate.value.substr(8,2);
  var endYear = endDate.value.substr(0,4);
  var endMon  = endDate.value.substr(5,2);
  var endDay  = endDate.value.substr(8,2);
  
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

function checkLatLon()
{
   var i, j;
   var min, max;
   var tlat, blat, llon, rlon;

   // check latitude and longitude values
   i = 0;
   if(document.getElementById("mapdisplayed").value == 1) setSpaceValues();
   tlat = document.getElementById("tlat");
   blat = document.getElementById("blat");
   llon = document.getElementById("llon");
   rlon = document.getElementById("rlon");
   max = goodCoordinate(tlat.value, true);
   if(max == 999) {
      alert("Top latitude was entered improperly.\nRe-enter as a positive number, followed by a space and then 'N' or 'S'.");
      return false;
   }
   min = goodCoordinate(blat.value, true);
   if(min == 999) {
      alert("Bottom latitude was entered improperly.\nRe-enter as a positive number, followed by a space anth then 'N' or 'S'.");
      return false;
   }
   if(max < min) {
      alert("Bottom latitude cannot exceed Top latitude.\nRe-enter the latitudes.");
      return false;
   }
   if(max == 90) i++;
   if(min == -90) i++;
   tlat.value = Math.abs(max) + (max < 0.0 ? " S" : " N");
   blat.value = Math.abs(min) + (min < 0.0 ? " S" : " N");
   max = goodCoordinate(rlon.value, false);
   if(max == 999) {
      alert("Right longitude was entered improperly.\nRe-enter as a positive number, followed by a space and then 'E' or 'W'.");
      return false;
   }
   if((max - min) < 180) sflag |= 4; 

   min = goodCoordinate(llon.value, false);
   if(min == 999) {
      alert("Left longitude was entered improperly.\nRe-enter as a positive number, followed by a space and then 'E' or 'W'.");
      return false;
   }
   if(max < min && min - max < 180.0 && !document.map) { 
      if(!confirm("Left longitude (" + llon.value + 
                  ") exceeds Right Longitude (" +
                  rlon.value + ")!\n(Click OK to " +
                         "continue or Cancel to re-enter longitude values)")) {
         return false;
      }
   }
   if(max == 180) i++;
   if(min == -180) i++;
   rlon.value = Math.abs(max) + (max < 0.0 ? " W" : " E");
   llon.value = Math.abs(min) + (min < 0.0 ? " W" : " E");
   if(i == 4 && !confirm("Default Spacial Range (" + llon.value + ", " +
                         rlon.value + "; " + blat.value + ", " +
                         tlat.value + ") selected!\n(Click OK to " +
                         "continue or Cancel to re-enter the values)")) {
      return false;
   }
   
   if((max - min) < 360) sflag |= 4;
   return true;
}   

function setSpaceValues()
{
   var tmp;

   tmp = (Math.round(document.getElementById("gdrawboxmap_nlat").value*FP)/FP);
   document.getElementById("tlat").value = Math.abs(tmp) + (tmp < 0.0 ? " S" : " N");
   tmp = (Math.round(document.getElementById("gdrawboxmap_slat").value*FP)/FP);
   document.getElementById("blat").value = Math.abs(tmp) + (tmp < 0.0 ? " S" : " N");
   tmp = (Math.round(document.getElementById("gdrawboxmap_wlon").value*FP)/FP);
   document.getElementById("llon").value = Math.abs(tmp) + (tmp < 0.0 ? " W" : " E");
   tmp = (Math.round(document.getElementById("gdrawboxmap_elon").value*FP)/FP);
   document.getElementById("rlon").value = Math.abs(tmp) + (tmp < 0.0 ? " W" : " E");
}

/**
 * check if user input is a good latitude/longitude value
 */
function goodCoordinate(value, islat)
{
   var nvalue;
   var unit = value.charAt(value.length - 1);
   
   if(value.charAt(0) == '-') {
      return 999;
   }
   
   nvalue = (Math.round(parseFloat(value)*FP)/FP);
   
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

// check and record filter options
function checkFilter() {

   var chkary;
   var fltnames = new Array("opdn", "oppt", "opse", "opcq", "optf", "op11");
   var fltdescs = new Array("a \"day night\" option",
                            "a \"platform type\" option",
                            "a \"source exclusion\" flag",
                            "a composite QC flag",
                            "an \"outlier trimming\" level",
                            "what to do if trimming flag=11");
   flts = null;
   for(i = 0; i < fltnames.length; i++) {
      chkary = document.getElementsByName(fltnames[i]);
      for(j = 0; j < chkary.length; j++) {
         if(chkary[j].checked) {
            if(flts == null) {
               flts = chkary[j].value;
            } else {
               flts += " " + chkary[j].value;
            }
            break;
         }
      }
      if(j >= chkary.length) {
         alert("You must choose " + fltdescs[i]);
         return false;
      }
   }
   return true;
}

function checkVariables()
{   
   var i, j, k;
   var attm, vname, vcnt, dcnt;
   var attms = new Array("core", "icoads", "immt", "mqc", "metavos", "nocn", "ecr");
   var attmVars;

   dcnt = 0;
   vars = null;

   for(i = 0; i < attms.length; i++) {
      if(i > 0 && document.getElementById("a" + attms[i]).value == 0) {
         sflag |= 1;
         continue;
      }
      attmName = attms[i];
      attm = document.getElementsByName(attmName);
      attmVars = null;

      for(vcnt = j = 0; j < attm.length; j++) {
         if(attm[j].checked) {
            vcnt++;
            vname = attm[j].value;
            k = vname.indexOf('*');
            if(k > 0) {
               dcnt++;
               vname = vname.substring(0, k);
            }
            if(attmVars == null) {
               attmVars = vname;
            } else {
               attmVars += ", " + vname;
            }
            if(vars == null) {
               vars = vname;
            } else {
               vars += ", " + vname;
            }
         }
      }
      if(vcnt < attm.length) sflag |= 1;
      if(attmVars != null) {
         if(attmName == "core")      corevars = attmVars;
         if(attmName == "icoads")    icoadsvars = attmVars;
         if(attmName == "immt")      immts = attmVars;
         if(attmName == "mqc")       modqcs = attmVars;
         if(attmName == "metavos")   metavos = attmVars;
         if(attmName == "nocn")      nocns = attmVars;
         if(attmName == "ecr")       ecrs = attmVars;
      }
   }
   if(dcnt == 0) {
      alert("Please select at least one of the data elements (marked by an asterisk '*' in Core, Immt, Mod-qc, Meta-vos, Nocn, or Ecr) to continue.");
      return false;
   }
   
   disableParams();
   checkSubIcoads();

   return true;
}

/**
 * Validate selections for DCK, PT, and SID
 *
 */
 function checkSubIcoads()
{   
   var i, j;
   var param, pcnt;
   var ids;
   var params = new Array("dck", "pt", "sid");

   dcks = null;
   pts  = null;
   sids = null;
   ids  = null;
   pcnt = 0;

   var_split = vars.split(", ");

   for(i = 0; i < params.length; i++) {
      if(var_split.indexOf(params[i].toUpperCase()) >= 0) {
        param = document.getElementsByName(params[i]);      
        for(pcnt = j = 0; j < param.length; j++) {
           if(param[j].checked) {
              pcnt++;
              pname = param[j].value;
              if(ids == null) {
                 ids = pname;
              } else {
                 ids += ", " + pname;
              }
           }
        }
        if(params[i] == "dck") dcks = ids;
        if(params[i] == "pt") pts = ids;
        if(params[i] == "sid") sids = ids;
        if(pcnt < param.length) sflag |= 1;
      }
      ids = null;
      pcnt = 0;
   }
   return true;
}

/**
 * Check selections for Rean-qc
 */ 
function checkReanqc()
{   
   var j;
   var vacp, vname, vcnt;
   
   reanqcs = null;

   vacp = document.getElementsByName("reanqc");      
   for(vcnt = j = 0; j < vacp.length; j++) {
       if(vacp[j].checked) {
          vcnt++;
          vname = vacp[j].value;
          if(reanqcs == null) {
             reanqcs = vname;
           } else {
             reanqcs += ", " + vname;
           }
       }
    }
    
    if(vcnt < vacp.length) sflag |= 1;
    return true;

}

/**
 * Check selections for Ivad
 */ 
function checkIvad()
{   
   var j;
   var vacp, vname, vcnt;
   
   ivads = null;

   vacp = document.getElementsByName("ivad");      
   for(vcnt = j = 0; j < vacp.length; j++) {
       if(vacp[j].checked) {
          vcnt++;
          vname = vacp[j].value;
          if(ivads == null) {
             ivads = vname;
           } else {
             ivads += ", " + vname;
           }
       }
    }
    
    if(vcnt < vacp.length) sflag |= 1;
    return true;

}

/**
 * fill values for check boxes of filtering scheme
 */ 
function fillBoxes() {
   
  var selects = document.getElementsByName("select");
  var opdn = document.getElementsByName("opdn");
  var oppt = document.getElementsByName("oppt");
  var opse = document.getElementsByName("opse");
  var opcq = document.getElementsByName("opcq");
  var optf = document.getElementsByName("optf");
  var op11 = document.getElementsByName("op11");

  if(selects[0].checked) {
    opdn[0].checked=true;
    opdn[1].checked=false;
    opdn[2].checked=false;
    oppt[0].checked=true;
    oppt[1].checked=false;
    opse[0].checked=true;
    opse[1].checked=false;
    opcq[0].checked=true;
    opcq[1].checked=false;
    optf[0].checked=false;
    optf[1].checked=true;
    optf[2].checked=false;
    optf[3].checked=false;
    op11[0].checked=true;
    op11[1].checked=false;
    op11[2].checked=false;
  } else if(selects[1].checked) {
    opdn[0].checked=true;
    opdn[1].checked=false;
    opdn[2].checked=false;
    oppt[0].checked=false;
    oppt[1].checked=true;
    opse[0].checked=true;
    opse[1].checked=false;
    opcq[0].checked=true;
    opcq[1].checked=false;
    optf[0].checked=false;
    optf[1].checked=false;
    optf[2].checked=true;
    optf[3].checked=false;
    op11[0].checked=false;
    op11[1].checked=true;
    op11[2].checked=false;
  } else {
    opdn[0].checked=false;
    opdn[1].checked=false;
    opdn[2].checked=false;
    oppt[0].checked=false;
    oppt[1].checked=false;
    opse[0].checked=false;
    opse[1].checked=false;
    opcq[0].checked=false;
    opcq[1].checked=false;
    optf[0].checked=false;
    optf[1].checked=false;
    optf[2].checked=false;
    optf[3].checked=false;
    op11[0].checked=false;
    op11[1].checked=false;
    op11[2].checked=false;
  }
}

function protectFilterOptions(box)
{
   var n, len;
   var selects = document.getElementsByName("select");
   var optf = document.getElementsByName("optf");
   var op11 = document.getElementsByName("op11");
   var obox = document.getElementsByName(box.name);

   if(selects[0].checked || selects[1].checked) {
      fillBoxes();
   } else {
      if(box == null) {
         if(optf[3].checked) {
            op11[2].checked=true;
         } else {
            op11[2].checked=false;
         }
      } else {
         if(box.name != "op11" || (box.name == "op11" && !optf[3].checked)) {
            for(n = 0; n < obox.length; n++) {
               if(n == box.value) {
                  obox[n].checked = true;
               } else {
                  obox[n].checked = false;
               }
            }
            if(box.name == "optf" && box.value == 3) {
               op11[0].checked=false;
               op11[1].checked=false;
               op11[2].checked=true;
            } else {
               op11[2].checked=false;
            }
         } else {
            op11[0].checked=false;
            op11[1].checked=false;
            op11[2].checked=true;
         }
      }
   }
}

/**
 * open a help window
 */

function openHelpWindow(helpkey)
{
   notewin = window.open("", "DescWin", "width=500,height=400,scrollbars=yes,resizable=yes");

   notewin.document.write("<html><head><title>Help Document</title></head><body>\n");
   if(helpkey == "temp") { // temporal range help
      notewin.document.write("<h3>Usage of Temporal Range Selection:</h3>" +
                "<p>From the drop down menus choose the starting and ending months and years that define\n" +
                "the bounding dates for your request. The bounding dates and all dates in between will\n" +
                "be included in the output data set.  The ending date must be later than or equal to the\n" + 
                "starting date.</p>\n" +
                "<p>Click 'Reset Range' to re-select the full period of record.</p>\n");
   }
   notewin.document.write("<form><center><input type=\"button\" value=\"Close This Window\" " +
           "onClick=\"self.close()\"></center></form>\n</body></html>\n");
   notewin.document.close();
   notewin.focus();
}

/**
 * function to show/hide a given attm
 */
function displayAttachment(attm, act) {
   var sattm, hattm, aattm;

   sattm = document.getElementById("s" + attm);
   hattm = document.getElementById("h" + attm);
   aattm = document.getElementById("a" + attm);
   if(act == 1) {
      sattm.style.display="table";
      hattm.style.display="none";
      aattm.value = 1;
   } else {
//      resetSelection(attm);
      sattm.style.display="none";
      hattm.style.display="block";
      aattm.value = 0;
   }
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
      document.getElementById("mapdisplayed").value = 1;
   } else {
      setSpaceValues();
      mapdisp.style.display="none";
      mandisp.style.display="block";
      document.getElementById("mapdisplayed").value = 0;
   }
}

/**
 * Review subset selections and submit to dsrqst.php
 */
function reviewRequest()
{
   var gindex;
   var dsid, rindex, rtype;
   var rnote;

   sflag = 0;

   if(!checkSelection()) return;

   rtype = document.getElementById("rtype").value;
   gindex = document.getElementById("gindex").value;
   dsid = document.getElementById("dsid").value;

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
   if (tarflag != "N") {
      postData.tflag = tarflag;
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
      var dsid = $("#dsid").val();
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
   togglePage(1);
   $(document).scrollTop(0);
}

/**
 * gather the selected information into a string buffer
 */
function gather_request_info()
{   
   var lats, lons, rnote, comments;

   dates = document.getElementById("startDate").value + ' ' + document.getElementById("endDate").value
   lats = document.getElementById("blat").value + ", " + document.getElementById("tlat").value;
   lons = document.getElementById("llon").value + ", " + document.getElementById("rlon").value;
   comp = get_compress_info();
   tarflag = get_tarfile_info();

   rnote = "Date Limits      : " + dates +
         "\nLatitude Limits  : " + lats +
         "\nLongitude Limits : " + lons +
         "\nFilter options   : " + flts;

   rinfo = "dates=" + dates + "&lats=" + lats + "&lons=" + lons +
           "&flts=" + flts  + "&vars=" + vars;

   if(corevars) rnote += "\nCore variables   : " + corevars;
   if(icoadsvars) rnote += "\nIcoads variables : " + icoadsvars;
   if(dcks) {
     rnote += "\nDeck numbers     : " + dcks;
     rinfo += "&dcks=" + dcks;
   }
   if(pts) {
     rnote += "\nPlatform types   : " + pts;
     rinfo += "&pts=" + pts;
   }
   if(sids) {
     rnote += "\nSource IDs       : " + sids;
     rinfo += "&sids=" + sids;
   }
   if(immts) rnote +=   "\nImmt parameters : " + immts;
   if(modqcs) rnote +=  "\nMod-qc parameters : " + modqcs;
   if(metavos) rnote += "\nMeta-vos parameters : " + metavos;
   if(nocns) rnote +=   "\nNocn parameters : " + nocns;
   if(ecrs) rnote +=    "\nEcr parameters : " + ecrs;
   if(reanqcs) {
     rnote += "\nRean-qc parameters : " + reanqcs;
     rinfo += "&Rean-qc=" + reanqcs;
   }
   if(ivads) {
     rnote += "\nIvad parameters : " + ivads;
     rinfo += "&Ivad=" + ivads;
   }
     
   if(comp != "no")   rnote += "\nFile Compression : " + comp;
   if(tarflag != "N") rnote += "\nTar file         : " + tarflag;

   return rnote;
}

function get_compress_info()
{
   var i, idx;
   var comps = document.getElementsByName('comp');
   
   idx = 0;
   for(i = 0; i < comps.length; i++) {
      if(comps[i].checked) {
         return comps[i].value;
      }
   }
   return "no";
}

function get_tarfile_info()
{
   var i, idx;
   var tars = document.getElementsByName('tarflag');
   
   idx = 0;
   for(i = 0; i < tars.length; i++) {
      if(tars[i].checked) {
         return tars[i].value;
      }
   }
   return "N";
}

/**
 * Toggle between first and second pages of the request form
 */
function togglePage(page) 
{
   pOne = document.getElementById("pageOne");
   pTwo = document.getElementById("pageTwo");

   if(page == 1) {
      displayAttachment('dck', 0);
      displayAttachment('pt', 0);
      displayAttachment('sid', 0);
      pOne.style.display="block";
      pTwo.style.display="none";
   } 
   else if(page == 2) {
      if(!checkDates()) return false;
      if(!checkFilter()) return false;
      if(!checkLatLon()) return false;
      disableParams();
      pOne.style.display="none";
      pTwo.style.display="block";
      $(document).scrollTop(0);
   }
}

/**
 * Enable/disable the DCK, PT, and SID selections based on the user-selected date range.
 *
 */

function disableParams()
{
   var names = ["dck", "pt", "sid"];
   
   var i, j, k;
   var attm, vname;
   var icoads_vars = [];
   
   var paramStartId, paramEndId;
   var paramStart, paramEnd;
   var paramStartDate, paramEndDate;
   
   var startDate = document.getElementById("startDate").value;
   var endDate = document.getElementById("endDate").value;
   var startDateUTC = new Date(startDate + "T00:00:00");
   var endDateUTC   = new Date(endDate + "T00:00:00");

   // Check if DCK, PT, and/or SID are selected in Icoads table
   attm = document.getElementsByName("icoads");      
   for(j = 0; j < attm.length; j++) {
      if(attm[j].checked) {
         vname = attm[j].value;
         k = vname.indexOf('*');
         if(k > 0) vname = vname.substring(0, k);
         icoads_vars.push(vname);
      }
   }
   
   for(i=0; i < names.length; i++) {   
      // Uncheck and disable all selections if the associated Icoads parameter (Table C1) isn't selected
      if(icoads_vars.indexOf(names[i].toUpperCase()) == -1) {
         selectNone(names[i]);
         disableAll(names[i]);
         setParamFontColor(names[i]);
      } else {
         var checkboxes = document.getElementsByName(names[i]);      
         for (j = 0; j < checkboxes.length; j++) {
            paramStartId = names[i] + "S" + j;
            paramEndId   = names[i] + "E" + j;
            paramStart = document.getElementById(paramStartId)
            paramEnd   = document.getElementById(paramEndId)

            paramStartDate = new Date(paramStart.innerHTML + "T00:00:00");
            paramEndDate   = new Date(paramEnd.innerHTML + "T00:00:00");
         
            if(paramStartDate >= startDateUTC && paramStartDate <= endDateUTC) {
               checkboxes[j].disabled = false;
            }
            else if(paramEndDate >= startDateUTC && paramEndDate <= endDateUTC) {
               checkboxes[j].disabled = false;
            }
            else if(paramStartDate <= startDateUTC && paramEndDate >= startDateUTC) {
               checkboxes[j].disabled = false;
            }
            else if(paramStartDate <= endDateUTC && paramEndDate >= endDateUTC) {
               checkboxes[j].disabled = false;
            }
            else {
               checkboxes[j].disabled = true;
               checkboxes[j].checked = false;
            }
         }
         setParamFontColor(names[i]);
      }
   }
   return true;
}

/**
 * Set the font color for enabled/disabled DCK, PT, and SID selections
 */
 
function setParamFontColor(name)
{
   var i;
   var paramNameId, paramStartId, paramEndId, paramDescId;
   var paramName, paramStart, paramEnd, paramDesc;
   var black = "#000000";
   var gray = "#cccccc";
   
   var checkboxes = document.getElementsByName(name);

   for (i = 0; i < checkboxes.length; i++) {
      paramNameId  = name + "N" + i;
      paramStartId = name + "S" + i;
      paramEndId   = name + "E" + i;
      paramDescId  = name + "D" + i;
      paramName  = document.getElementById(paramNameId);
      paramStart = document.getElementById(paramStartId);
      paramEnd   = document.getElementById(paramEndId);
      paramDesc  = document.getElementById(paramDescId);

	  if(checkboxes[i].disabled) {
         paramName.style.color = gray;
         paramStart.style.color = gray;
         paramEnd.style.color = gray;
         paramDesc.style.color = gray;	 
	  } else {
         paramName.style.color = black;
         paramStart.style.color = black;
         paramEnd.style.color = black;
         paramDesc.style.color = black;	 	 
	  }
   }
}

/**
 * Select all checkboxes 
 */
function selectAll(name)
{
  var checkboxes = document.getElementsByName(name);
  for (var i in checkboxes) {
	if(!checkboxes[i].disabled) checkboxes[i].checked = true;
  }
}

/**
 * Clear all checkboxes
 */
function selectNone(name)
{
  var checkboxes = document.getElementsByName(name);
  for (var i in checkboxes) {
	if(!checkboxes[i].disabled) checkboxes[i].checked = false;
  }
}

/**
 * Disable all checkboxes 
 */
function disableAll(name)
{
  var checkboxes = document.getElementsByName(name);
  for (var i in checkboxes) {
	checkboxes[i].disabled = true;
  }
}
