/***********************************************************************************
 * 
 *     Title : msg3.0_subset.js
 *    Author : Zaihua Ji,  zji@ucar.edu
 *      Date : 31/08/2016
 *   Purpose : javascript program to validate the form inputs for request of 
 *             ICOADS 3.0 MSG sub-dataset.
 * Work File : $DSSWEB/js/msg3.0_subset.js
 *
 ***********************************************************************************/
 
var styr, dates, vars, comp, rinfo, sflag;
var FP = 10;

/**
 * function to reset the checkbox selections for record elements
 *
 */
function resetSelection()
{
   var items = document.getElementsByName("param");
   var i;
   
   for(i = 0; i < items.length; i++) {
      items[i].checked = false;
   }
}
      

/**
 * function to reset the temporal selections
 *
 */
function resetTemporal(smoidx, syridx, emoidx, eyridx) {
   var select;
   
   select = document.getElementById("startmo");
   select.options[smoidx].selected = true;

   select = document.getElementById("startyr");
   select.options[syridx].selected = true;

   select = document.getElementById("endmo");
   select.options[emoidx].selected = true;

   select = document.getElementById("endyr");
   select.options[eyridx].selected = true;
}

/**
 * functions to valid form inputs
 *
 */
function checkSelection()
{
   var i, min, max;
   var yr, mo;
   var startyr, endyr, startmo, endmo;
   var tlat, blat, llon, rlon;
   
   // check date range
   yr = document.getElementById("startyr");
   startyr = parseInt(yr.options[yr.selectedIndex].value);
   yr = document.getElementById("endyr");
   endyr = parseInt(yr.options[yr.selectedIndex].value);
   mo = document.getElementById("startmo");
   startmo = parseInt(mo.options[mo.selectedIndex].value);
   mo = document.getElementById("endmo");
   endmo = parseInt(mo.options[mo.selectedIndex].value);

   if(startyr > endyr || (startyr == endyr) && startmo > endmo) {
      alert("Invalid Date Range - Starting Date cannot be later than Ending Date");
      return false;
   }
   dates = startyr + (startmo < 10 ? "0" : "") + startmo + " " +
           endyr + (endmo < 10 ? "0" : "") + endmo;
   styr = startyr;

   yr = parseInt(document.getElementById("minyr").value);
   mo = parseInt(document.getElementById("minmo").value);
   if(startyr > yr || (startyr == yr) && startmo > mo) {
      sflag |= 2;
   } else {
      yr = parseInt(document.getElementById("maxyr").value);
      mo = parseInt(document.getElementById("maxmo").value);
      if(endyr > yr || (endyr == yr) && endmo > mo) {
         sflag |= 2;
      }
   }
   
   // check latitude and longitude values
   i = 0;
   setSpaceValues();
   tlat = document.getElementById("tlat");
   blat = document.getElementById("blat");
   llon = document.getElementById("llon");
   rlon = document.getElementById("rlon");
   max = goodCoordinate(tlat.value, true);
   if(max == 999) {
      alert("Top latitude was entered improperly.\nRe-enter as a positive number, followed by a space, followed by 'N' or 'S'.");
      return false;
   }
   min = goodCoordinate(blat.value, true);
   if(min == 999) {
      alert("Bottom latitude was entered improperly.\nRe-enter as a positive number, followed by a space, followed by 'N' or 'S'.");
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
   if((max - min) < 180)  sflag |= 4;

   max = goodCoordinate(rlon.value, false);
   if(max == 999) {
      alert("Right longitude was entered improperly.\nRe-enter as a positive number, followed by a space, followed by 'E' or 'W'.");
      return false;
   }
   min = goodCoordinate(llon.value, false);
   if(min == 999) {
      alert("Left longitude was entered improperly.\nRe-enter as a positive number, followed by a space, followed by 'E' or 'W'.");
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
   
   // check if any data element selected
   if(!checkVariables()) return false;

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

   nvalue= (Math.round(parseFloat(value)*FP)/FP);
   
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

function checkVariables()
{   
   var j, k;
   var attm, vname, vcnt;

   vars = null;
   attm = document.getElementsByName("param");
   for(vcnt = j = 0; j < attm.length; j++) {
      if(attm[j].checked) {
         vname = attm[j].value;
         vcnt++;
         if(vars == null) {
            vars = vname;
         } else {
            vars += ", " + vname;
         }
      }
   }
   if(vcnt == 0) {
      alert("Select at least one of the variables to continue!");
      return false;
   }

   if(vcnt < attm.length) sflag |= 1;

   return true;
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
 * open a window for selection and submit to dsrqst.php if validated
 */
function submitSubsetRequest()
{
   var win, doc;
   var dsid, rtype, gindex;
   var rnote;

   sflag = 0;

   if(!checkSelection()) return;

   rtype = document.getElementById("rtype").value;
   dsid = document.getElementById("dsid").value;
   gindex = document.getElementById("gindex").value;

   win = window.open("", "MSG3.0", "width=800,height=600,scrollbars=yes,resizable=yes");
   doc = win.document;
   doc.write("<html><head><title>ICOADS 3.0 MSG Subset</title></head><body>\n");
   doc.write("<form name=\"form\" action=\"/php/dsrqst.php\" method=\"post\">\n");
   doc.write("<P>An ICOADS 3.0 MSG data request has been completed. A summary of the request is given below.\n");
   doc.write("Click the Button 'Submit Request' at the bottom if the information is <b>correct</b>;\n");
   doc.write("otherwise click the Button 'Cancel Request' to reselect the condtions.\n");
   doc.write("Email <a href=\"mailto:Zaihua Ji <zji@ucar.edu>?subject=Help for DS548.1 Request Result!\">\n");
   doc.write("Zaihua Ji</i></a> for questions and comments.</p>\n");

   rnote = gather_request_info();
   doc.write("<pre>\n" + rnote + "\n</pre>\n");

   /* hidden inputs for submit form */
   doc.write("<input type=\"hidden\" name=\"dsid\" value=\"" + dsid + "\">\n");
   doc.write("<input type=\"hidden\" name=\"gindex\" value=\"" + gindex + "\">\n");
   doc.write("<input type=\"hidden\" name=\"rtype\" value=\"" + rtype + "\">\n");
   if(comp != "no") doc.write("<input type=\"hidden\" name=\"afmt\" value=\"" + comp + "\">\n");
   doc.write("<input type=\"hidden\" name=\"sflag\" value=\"" + sflag + "\">\n");
   doc.write("<input type=\"hidden\" name=\"rinfo\" value=\"" + rinfo + "\">\n");
   doc.write("<input type=\"hidden\" name=\"rnote\" value=\"" + rnote + "\">\n");
   doc.write("<p><input type=\"submit\" value=\"Submit Request\">");
   doc.write("&nbsp<input type=\"button\" onClick=\"self.close()\" value=\"Cancel Request\"></p>\n");
   doc.write("</form></body></html>\n");
   doc.close();
   win.focus();   
}

/**
 * gather the selected information into a string buffer
 */
function gather_request_info()
{   
   var lats, lons, ptype, resol, rnote, comments;

   lats = document.getElementById("blat").value + ", " + document.getElementById("tlat").value;
   lons = document.getElementById("llon").value + ", " + document.getElementById("rlon").value;
   comp = get_radio_select("comp", "no");
   ptype = get_radio_select("ptype", "ENH");
   resol = get_radio_select("resol", "2DEG");
   comments = document.getElementById("comments");
   if(resol == "1DEG" && styr < 1960) {
      resol = "2DEG";
   }

   rnote = "Date Limits      : " + dates +
         "\nLatitude Limits  : " + lats +
         "\nLongitude Limits : " + lons +
         "\nVariable Names   : " + vars +
         "\nStatistic Type   : " + ptype +
         "\nResolution       : " + resol;
   if(comp != "no") rnote += "\nFile Compression : " + comp;

   rinfo = "dates=" + dates + "&lats=" + lats + "&lons=" + lons +
           "&vars=" + vars + "&ptype=" + ptype + "&resol=" + resol;
   if(comments.value) {
      rnote += "\n\nComments:\n" + comments.value;
   }
   return rnote;
}

function get_radio_select(rname, def)
{
   var i;
   var rvals = document.getElementsByName(rname);
   
   for(i = 0; i < rvals.length; i++) {
      if(rvals[i].checked) {
         return rvals[i].value;
      }
   }
   return def;
}
