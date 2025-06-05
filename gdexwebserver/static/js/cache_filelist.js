
var WPATH = 'https://rda.ucar.edu';
var CGIBIN = WPATH+'/cgi-bin';
var GPATH = 'https://data.rda.ucar.edu';
var SPATH = 'https://stratus.rda.ucar.edu';
var RPATH = 'https://request.rda.ucar.edu';

// show loading spinner during ajax content load
$(document).ajaxSend(function() {
  $("#ds_content").html('<div class="text-center mt-3" id="loading"><strong>Loading ... &nbsp;&nbsp;</strong><div class="spinner-border text-primary" role="status"><span class="sr-only">Loading...</span></div></div>');
});

// scroll to top on ajax success
$(document).ajaxSuccess(function() {
//  $('#datasetTab')[0].scrollIntoView();
  $(document).scrollTop(0);
});

$(function() {
    $(document).on('click', '.parent_group', toggleChildBoxes)
               });
$(function() {
    $(document).on('click', '.table_group', toggleChildBoxes)
               });
$('.file').on('click', toggleSingleBox);
$('.sort-column').on('click', sortColumn);
$('.clear-group-btn').on('click', clearFileSelections);
$('.btn-all-files').on('click', selectAllFiles);

$(document).ready(function() {
   $.ajaxSetup({
      headers: {
         'X-CSRF-TOKEN':get_csrf_token(),
         'X-CSRFTOKEN':get_csrf_token(),
      }
   });
});
 
// 'Scroll back to top' button for long file lists
$(window).on("scroll", function() {
   if ($(document).scrollTop() > 1000) {
      $("#topButton").show();
   } else {
      $("#topButton").hide();
   }
});
$("#topButton").on("click", function() {
   $(document).scrollTop(0);
});
    
function sortColumn()
{
    var table = $(this).parents('table').eq(0)
    var rows = table.find('tr:gt(0)').toArray().sort(comparer($(this).parent().index()))
    this.asc = !this.asc
    if (!this.asc){rows = rows.reverse()}
    for (var i = 0; i < rows.length; i++){table.append(rows[i])}
}
function comparer(index) {
    return function(a, b) {
        var valA = getCellValue(a, index);
        var valB = getCellValue(b, index);
        if($.isNumeric(valA))
            return parseInt(valA) - parseInt(valB);
        if(valA.trim().match(/....-..-../))
            return Date.parse(valA.trim()) - Date.parse(valB.trim());
        return valA.toLowerCase().localeCompare(valB.toLowerCase());
    
    }
}
function getCellValue(row, index) { 
  return $(row).children('td').eq(index).text(); 
}

/*
var type = getColumnType();
var column = $(this).parent().index();
var table = $(this).closest('table');
table.find('tr').each(
    function() {
        console.log($(this).attr('id'));
    }
);
function getColumnType(table, column)
{
  console.log('here')
}
*/

/**
 *
 * Given number of bytes, return string with best conversion.
 * example: formatBytes(10000) => '10 KB'
 */
function formatBytes(bytes)
{
    var bytes = parseInt(bytes);
    var digits = bytes.toString().length;
    digits += Math.floor(digits/4)
    var ratio = 1024;
    var exp = Math.floor(digits/4);
    if(exp == 0)
        return bytes + " B";

    var new_num = bytes / (ratio**exp);
    new_num = Math.ceil(new_num * 100) / 100; //round to hunderedth
    if(exp == 1)
        return new_num + 'K';
    if(exp == 2)
        return new_num + 'M';
    if(exp == 3)
        return new_num + 'G';
    if(exp == 4)
        return new_num + 'T';
    return '?';
}
function get_csrf_token()
{
    return $('input[name="csrfmiddlewaretoken"').attr('value');
}
function getCheckedFiles(parse=false)
{
    checked_boxes = [];
    $('.file:checked').each(function() {
            checked_boxes.push($(this));
            });

    if(checked_boxes.length == 0)
    {
        alert('No files are checked. Please select at least one file to continue.');
        throw 'No files selected';
    }
    files = [];
    for(var i=0; i < checked_boxes.length; i++)
    {
        var file_info = {
            'filename' : '',
            'size' : 0};
        var row = $(checked_boxes[i]).parent().parent();
        filename = row.find('a').attr('href');
        if (parse) {
          url = parseUrl(filename);
          file_info['filename'] = url.pathname;
        } else {
          file_info['filename'] = filename;
        }
        if(file_info['filename'] === undefined) {
            file_info['filename'] = row.find('a').text().trim();
        }
        file_info['size'] = row.find('.Size').attr('data-size');
        files.push(file_info);
    }
    return files;
}
function parseUrl(url)
{
   var a = document.createElement('a');
   a.href = url;
   return a;
}
function convertFiles()
{
    var contentDiv = 'ds_content';
    var files = getCheckedFiles();
    var sizes = getListFromKey(files, 'size');
    var totalSize = 0;
    $.each(sizes,function(){totalSize+=parseFloat(this) || 0;});
    var contact = "rdahelp@ucar.edu";
    var dsid = $('#file_table').attr('data-dsid');
    var message = `Click the following button to send a request for converting format to NetCDF

    Contact ${contact} for further assitance
    `;
    var confirmation_div = $('<div></div>', {'id': 'confirmation-div', 'class': 'dataset p-3'});

    var header = $("<h2></h2>", {'class':'mt-2'}).text('Web files selected for RDA dataset '+dsid);
    confirmation_div.append(header);

    var total_size_message = $('<div></div>')
        .text('You have selected '+files.length+' files ('+Math.floor(totalSize/1000000)+' MB)');
    confirmation_div.append(total_size_message);

    var message_div = $('<div></div>', {'style':'white-space:pre-line'}).text(message);
    confirmation_div.append(message_div);

    var button_div = $('<div />', {'class':'pt-2 pb-2'});
    var transfer_button = $('<button />', {'class':'btn btn-primary mr-2'})
        .text('Request format conversion to NetCDF for selected files')
        .on('click', function(){
           sendConvertApp(dsid);
        });
    var cancel_button = $('<button />', {'class':'btn btn-outline-primary mr-2'})
        .text('Cancel')
        .on('click',function(){
           if($('#ds_content').length) {
              $('#ds_content').children().removeClass('d-none');
           }
           else {
              $('body').children().attr("style",'display:block');
           }
              $('#confirmation-div').remove();
         });
    button_div
        .append(transfer_button)
        .append(cancel_button)
    confirmation_div.append(button_div);

    var file_table = $('<table />');
    var table_header = $('<tr><th>Filename</th><th>Size</th></tr>');
    file_table.append(table_header);
    for( var i=0; i < files.length; i++){
        var table_row = $('<tr><td>'+files[i]['filename']+'</td><td>'+files[i]['size']+'</td></tr>');
        file_table.append(table_row);
        }
    confirmation_div.append(file_table);

    //$('#ds_content').addClass('d-none');
    //confirmation_div.insertBefore($('#ds_content'));
    if($('#ds_content').length) {
       $('#ds_content').children().addClass('d-none');
       $('#ds_content').prepend(confirmation_div);
    }
    else {
       $('body').children().attr("style",'display:none');
       $('body').prepend(confirmation_div);
    }
}
function showGlobusConfirmation()
{
    var contentDiv = 'ds_content';
    var files = getCheckedFiles(true);
    var sizes = getListFromKey(files, 'size');
    var totalSize = 0;
    $.each(sizes,function(){totalSize+=parseFloat(this) || 0;});
    var contact = "rdahelp@ucar.edu";
    var dsid = $('#file_table').attr('data-dsid');
    var message = `To transfer these files using the Globus data transfer service, select the button labeled 'Globus transfer' below. 
                   You will be redirected to the Globus web app where you will be prompted to select a target endpoint to receive the 
		   data transfer. Once you have defined a target endpoint, you will be redirected back to the RDA website and your data 
		   transfer will be submitted.  
		   
		   A Globus login is required to use this service.  You may sign into Globus with your preferred identity 
		   (e.g. ORCID, GlobusID, Google, or other).
		   
		   Contact ${contact} for further assitance`;

    var confirmation_div = $('<div></div>', {'id': 'confirmation-div', 'class': 'dataset p-3'});

    var header = $("<h2></h2>", {'class':'mt-2'}).text('Files selected for RDA dataset '+dsid);
    confirmation_div.append(header);

    var total_size_message = $('<div></div>')
        .text('You have selected '+files.length+' files ('+Math.floor(totalSize/1000000)+' MB)');
    confirmation_div.append(total_size_message);

    var message_div = $('<div></div>', {'style':'white-space:pre-line'}).text(message);
    confirmation_div.append(message_div);

    var button_div = $('<div />', {'class':'pt-2 pb-2'});
    var transfer_button = $('<button />', {'class':'btn btn-primary mr-2'})
        .text('Globus transfer')
        .on('click', function(){
           globusTransfer(dsid);
        });
    var cancel_button = $('<button />', {'class':'btn btn-outline-primary mr-2'})
        .text('Cancel')
        .on('click',function(){
           if($('#ds_content').length) {
              $('#ds_content').children().removeClass('d-none');
           }
           else {
              $('body').children().attr("style",'display:block');
           }
              $('#confirmation-div').remove();
         });
    button_div
        .append(transfer_button)
        .append(cancel_button)
    confirmation_div.append(button_div);

    var file_table = $('<table />');
    var table_header = $('<tr><th>Filename</th><th>Size</th></tr>');
    file_table.append(table_header);
    for( var i=0; i < files.length; i++){
        var table_row = $('<tr><td>'+files[i]['filename']+'</td><td>'+files[i]['size']+'</td></tr>');
        file_table.append(table_row);
        }
    confirmation_div.append(file_table);

    //$('#ds_content').addClass('d-none');
    //confirmation_div.insertBefore($('#ds_content'));
    if($('#ds_content').length) {
       $('#ds_content').children().addClass('d-none');
       $('#ds_content').prepend(confirmation_div);
    }
    else {
       $('body').children().attr("style",'display:none');
       $('body').prepend(confirmation_div);
    }
    $(document).scrollTop(0);
}
function sendConvertApp(dsid)
{
    files = getCheckedFiles();
    var filenames = getListFromKey(files, 'filename');
    email = get_user_email(true);
    url = '/php/dsrqst.php'
    $.post(url, {'files':filenames, 'email':email,'rstat':'Q', 'rtype':'F', 'dsid':dsid }, function(data){
        window.location.href = data;
    });
    
}
function globusTransfer(dsid)
{
    var files = getCheckedFiles(true);
    var filenames = getListFromKey(files, 'filename');
    var url = '/globus/filelist/';
    $.post(url, {'files':filenames, 'dsid':dsid }, function(data){
        window.location.href = data;
    });
}
function getListFromKey(dict, key)
{
    return dict.map(o => o[key]);
}
function getScript(language)
{
    var script = null;
    var files = getListFromKey(getCheckedFiles(), 'filename');
    var email = get_user_email(true);
    var script_name = 'download.py';
    switch(language)
    {
    case 'python':
        script = getPythonScript(files);
        script_name = 'rda-download.py';
        break;
    case 'csh':
        script = getCshScript(files);
        script_name = 'rda-download.csh';
        break;
    case 'jupyter':
        script = getJupyterScript(files);
        script_name = 'rda-download.ipynb';
        break;
    case 'filelist':
        script = getFilelistScript(files);
        script_name = 'rda-filelist.txt';
        break;
    default:
        script = getPythonScript(files);
        script_name = 'rda-download.py';
    }
        var blob = new Blob([script], {type: "text/plain;charset=utf-8"});
        saveAs(blob, script_name);

    return script;
}
function getPythonScript(filelist)
{
    script = `#!/usr/bin/env python
""" 
Python script to download selected files from rda.ucar.edu.
After you save the file, don't forget to make it executable
i.e. - "chmod 755 <name_of_script>"
"""
import sys, os
from urllib.request import build_opener

opener = build_opener()

filelist = [\n`
    count = filelist.length;
    for(i = 0; i < count-1; i++) {
        script += "  '" + filelist[i].trim() + "',\n";
    }
    script += "  '" + filelist[count-1].trim() + "'\n]\n";
    script += `
for file in filelist:
    ofile = os.path.basename(file)
    sys.stdout.write("downloading " + ofile + " ... ")
    sys.stdout.flush()
    infile = opener.open(file)
    outfile = open(ofile, "wb")
    outfile.write(infile.read())
    outfile.close()
    sys.stdout.write("done\\n")
`
      return script
}
function getCshScript(filelist)
{
    script = `#!/usr/bin/env csh
#
# c-shell script to download selected files from rda.ucar.edu using Wget
# NOTE: if you want to run under a different shell, make sure you change
#       the 'set' commands according to your shell's syntax
# after you save the file, don't forget to make it executable
#   i.e. - "chmod 755 <name_of_script>"
#
# Experienced Wget Users: add additional command-line flags to 'opts' here
#   Use the -r (--recursive) option with care
#   Do NOT use the -b (--background) option - simultaneous file downloads
#       can cause your data access to be blocked
set opts = "-N"
#
# Check wget version.  Set the --no-check-certificate option 
# if wget version is 1.10 or higher
set v = \`wget -V |grep 'GNU Wget ' | cut -d ' ' -f 3\`
set a = \`echo $v | cut -d '.' -f 1\`
set b = \`echo $v | cut -d '.' -f 2\`
if(100 * $a + $b > 109) then
  set cert_opt = "--no-check-certificate"
else
  set cert_opt = ""
endif

set filelist= ( \\
`;
    for(i=0; i<filelist.length; i++)
    {
        script += "  " + filelist[i] + " \\\n";
     }
     script += ")"
     script += `
while($#filelist > 0)
  set syscmd = "wget $cert_opt $opts $filelist[1]"
  echo \"$syscmd ...\"
  $syscmd
  shift filelist
end
`
    return script;
}
function getFilelistScript(filelist)
{
files = "";
for(var i=0; i< filelist.length; i++)
{
    files +=  filelist[i] + " \\\n";
}
return files;
}

function getJupyterScript(filelist)
{
    url = '/api/generate_notebook';
    console.log(filelist);
    var return_data;

    $.ajax({
        type: "POST",
        url: url,
        data: {'filelist':filelist},
        async: false,
        global: false,
        success : function(data) {
            return_data = data;
        }
    });
    return return_data;
}

var lastChecked = {'checkbox':null, 'tableID':null};
function toggleSingleBox()
{
    var tableGroup = $(this).closest('table').attr('id').split('_table')[0];
    var groupButton = tableGroup+'_clear_button';
    var tableId = tableGroup + '_table';
    var start, end;
    var groupIndexBox, parentIndexBox;

    if (tableGroup != 'request') {
      groupIndexBox = tableGroup + '_group_index';
      parentIndexBox = tableGroup + '_parent';
      if ( $(this).is(":checked")==false ) {
         $("#"+parentIndexBox).prop("checked", false);
         $("#"+groupIndexBox).prop("checked", false);    
      }
   }

    tableID = "table#"+tableId;
    table = $(tableID);
    if(tableID == lastChecked['tableID']) {
        curIndex = parseInt($(this).parent().text().trim());
        prevIndex = parseInt(lastChecked['checkbox'].parent().text().trim());
	    
	if (curIndex > prevIndex) {
	    start = lastChecked['checkbox'];
	    end = $(this);
	} else {
	    start = $(this);
	    end = lastChecked['checkbox'];
	}
        if(Math.abs(curIndex-prevIndex) > 1 && countChecked(start, end) == 0) {
            if(confirm('Select all '+ Math.abs(curIndex-prevIndex) + ' files between selections?')) {
		checkRange(start, end);	
            }
        }
    }
    lastChecked['tableID'] = tableID;
    lastChecked['checkbox'] = $(this);

    setTableSummary(table);

    // disable clear button and reset lastChecked if no boxes are checked
    if ( table.find("input[type=checkbox]").is(":checked")) {
	    $("button#"+groupButton).attr("disabled", false);
        }
    else {
	    $("button#"+groupButton).attr("disabled", true);
	    lastChecked['tableID'] = null;
	    lastChecked['checkbox'] = null;
    }
}

// Count the number of boxes checked between two checkboxes.  
// Does not count the 'start' and 'end' checkboxes.
function countChecked(start, end)
{    
    count = 0;
    row = start.closest('tr');
    row = row.next();
    curCheckbox = row.find('input[type=checkbox]');
    while(!curCheckbox.is(end)) {
	if (curCheckbox.is(":checked")) {
	    count++;
	}
	row = row.next();
	curCheckbox = row.find('input[type=checkbox]');
    }
    return count;
}
function checkRange(start, end)
{    
    row = start.closest('tr');
    curChecked = row.find('input[type=checkbox]');
    while(!curChecked.is(end)) {
        curChecked = row.find('input[type=checkbox]');
        curChecked.prop('checked', true);
        row = row.next();
    }
}
/**
 * Set the summary information displayed above table groups
 */
function setTableSummary(table) {
    var tableGroup = table.attr('id').split('_table')[0];
    var num_files_ele = $('#num_selected_files_'+tableGroup);
    var total_size_ele = $('#total_size_'+tableGroup);

    var totalSize = 0;
    var numFiles = 0;

    table.find("tbody tr").each(
	    function () {
         var self = $(this);
         var size = self.find('td.Size').attr('data-size');
         if (!size) {
            size = self.find('td.size').attr('data-size');
         }
		   if ( self.find('input[type=checkbox]').is(':checked') ) {
            totalSize+=parseInt(size);
			   numFiles++;
		   }
      }
    );

    num_files_ele.text(numFiles);
    total_size_ele.text('('+formatBytes(totalSize)+')');
    total_size_ele.data('value', totalSize);
}

function toggleChildBoxes()
{
    var check;
    var table, tableGroup, button;
	
    var boxId = $(this).attr('id');
    if (boxId.includes("_group_index")) // if this checkbox is part of the group table
    {
        tableGroup = boxId.split("_group_index")[0];
    }
    else if (boxId.includes("_parent")) // checkbox is a parent referencing group table
    {
        tableGroup = boxId.split("_parent")[0];
    }
    else
    {
	alert("table not found");
    }

    table = $("#"+tableGroup+"_table");
    button = $("button#"+tableGroup+"_clear_button");

    if(this.checked) {
	    check = true;
	    button.attr("disabled", false);
    } else {
	    check = false;
	    button.attr("disabled", true);
    }

    if (boxId.includes("_group_index")) // toggle parent checkbox 
	{
	    $("#"+tableGroup+"_parent").filter(":input").prop('checked', check);
	}
    table.find('input[type=checkbox]')
         .each(function(){
            $(this).prop('checked',check);
             });
    setTableSummary(table);	
}

/**
  * Clear files selected in a group table for a given tableGroup
  */
function clearFileSelections() {
  var tableGroup = $(this).attr('id').split('_clear_button')[0];
  var table = $("table#"+tableGroup+"_table");
  
  table.find("input[type=checkbox]")
       .each(function(){
                 $(this).prop("checked",false);
             }
  );
	
  parentInput = $("#"+tableGroup+"_parent").filter(":input");
  if (parentInput.length) {
      parentInput.prop("checked", false);
  }
	
  setTableSummary(table);
  $(this).attr("disabled", true);

  // Reset last checkbox selected to null
  lastChecked['tableID'] = null;
  lastChecked['checkbox'] = null;
	
}

/**
  * Select all files in a table or table group
  */
function selectAllFiles() {
   var tableGroup = $(this).attr('id').split('_select_all')[0];
   var table = $("table#"+tableGroup+"_table");
   
   table.find("input[type=checkbox]")
        .each(function(){
                  $(this).prop("checked",true);
              }
   );
    
   parentInput = $("#"+tableGroup+"_parent").filter(":input");
   if (parentInput.length) {
       parentInput.prop("checked", true);
   }
    
   setTableSummary(table);
   $(this).attr("disabled", false);

   var clearButton = tableGroup+'_clear_button';
   $("button#"+clearButton).attr("disabled", false);
 
   // Reset last checkbox selected to null
   lastChecked['tableID'] = null;
   lastChecked['checkbox'] = null;    
 }
  
/**
  * get user email, remove trailing '<' and '>' for remove == true
  * return null if not logged in
  */
function get_user_email(remove) {

   var cookies, files, k, email;

   // get duser cookie for email
   if(document.cookie != "") {
      cookies = document.cookie.split("; ");
      for(i = 0; i < cookies.length; i++) {
         files = cookies[i].split("=");
         if(files[0] == 'duser') {
            email = files[1];
            k = email.indexOf(";");
            if(k > 0) {
               email = email.substring(0, k);
            }
            if(remove) {
               k = email.indexOf(":");
               if(k > 0) {
                  email = email.substring(0, k);
               }
            }
            return email;
         }
      }
   }
   return null;
}


/***********************************************************************************
 *
 *     Title : cache_filelist.js
 *    Author : Zaihua Ji (zji@ucar.edu)
 *      Date : 05/03/2006
 *   Purpose : javascript program to validate the form inputs for request of
 *             file list request from cache_filelist.inc.
 * Test File : $DSSWEB/js/cache_filelist_test.js
 * Work File : $DSSWEB/js/cache_filelist.js
 *  SVN File : $HeadURL: https://subversion.ucar.edu/svndss/zji/javascript/cache_filelist.js $
 *             $Id: cache_filelist.js 8286 2015-07-09 20:43:27Z zji $
 *  Modified : Thomas Cram (tcram@ucar.edu), 2012-09-06, for the new web format
 *
 **********************************************************************************/

/**
 * open a window to get an answer of yes, no or cancel
 */

//var DSSURL = "https://rda.ucar.edu";
//var CGIBIN = "https://rda.ucar.edu/cgi-bin/";
//var ynSaves;
//var ynInternal;
//var ynwin;
//var CHKCNT = 0;
//
function yn_window(gidx, idx1, idx2, gcnt, offset)
{
   var cnt = idx2 - idx1 - 1;
   var args = "width=500,height=110,left=325,top=300,scrollbars=0,resizable=0";
   var bttns = '<input type="button" name="yes" value="Yes" onClick="CloseForm(1)">&nbsp;&nbsp;' +
               '<input type="button" value="No" onClick="CloseForm(0)">&nbsp;&nbsp;' +
               '<input type="button" value="Unselect Last" onClick="CloseForm(2)">&nbsp;&nbsp;' +
               '<input type="button" value="Unselect Both" +" onClick="CloseForm(3)">';

   var scripts = "<script language=JavaScript>function CloseForm(val) { " +
                 "window.opener.ynSaves[0] = val; window.close(); }</script>";

   ynSaves = new Array(0, gidx, idx1, idx2, gcnt, offset);

   ynwin = window.open("", "Confirmation", args);
   ynwin.document.write("<html><head><title>Confirmation</title></head>" + scripts);
   ynwin.document.write("<body bgcolor=\"#e1eaff\" onblur=\"window.focus();\">");
   ynwin.document.write('<table border=0 width="95%" align=center cellspacing=0 cellpadding=2>');
   ynwin.document.write("<tr><td align=center>Include " + cnt + " Files between two selected ones?</td></tr>");
   ynwin.document.write('<tr><td><br></td></tr>');
   ynwin.document.write('<tr><td align=center>' + bttns + '</td></tr></body></html>');
   ynwin.document.close();
   ynwin.focus();
   ynInterval = window.setInterval("check_ynwin()", 100);
}

function check_ynwin()
{
   try {
      if(ynwin.closed) {
         window.clearInterval(ynInterval);
         yn_return();
      } else {
         ynwin.focus();
      }
   } catch(everything) {   }
}

function yn_return() {

   var i, gidx, idbox, checks;
   var act = ynSaves[0];
   var changed = true;
   var chkall, idx1, idx2;

   gidx = ynSaves[1];
   if(act > 0) {
      checks = document.form.elements["GRP" + gidx];
      if(act == 1) {
         if((ynSaves[3] - ynSaves[2] + 2) == checks.length) {
            idx1 = 0;
            idx2 = checks.length - 1;
            chkall = true;
         } else {
            idx1 = ynSaves[2] + 1;
            idx2 = ynSaves[3] - 1;
            all = false;
         }
         for(i = idx1; i <= idx2; i++) {
            if(!(checks.checked || checks[i].disabled)) checks[i].checked = true;
         }
         if(chkall) {
            eval("idbox = document.form.GID" + gidx);
            if(idbox && !idbox.checked) {
               idbox.checked = checked;
               resetGroupSelection(gidx, ynSaves[4], 0);
            }
         }
      } else if(act == 2) {
         checks[ynSaves[2 + ynSaves[5]]].checked = false;
         changed = false;
      } else if(act == 3) {
         checks[ynSaves[2]].checked = false;
         checks[ynSaves[3]].checked = false;
      }
   }
   if(changed) groupFileSelection(gidx);
}
var ajax = {};
ajax.x = function () {
    if (typeof XMLHttpRequest !== 'undefined') {
        return new XMLHttpRequest();
    }
    var versions = [
        "MSXML2.XmlHttp.6.0",
        "MSXML2.XmlHttp.5.0",
        "MSXML2.XmlHttp.4.0",
        "MSXML2.XmlHttp.3.0",
        "MSXML2.XmlHttp.2.0",
        "Microsoft.XmlHttp"
            ];

    var xhr;
    for (var i = 0; i < versions.length; i++) {
        try {
            xhr = new ActiveXObject(versions[i]);
            break;
        } catch (e) {
        }
    }
    return xhr;
};

ajax.send = function (url, callback, method, data, async) {
    if (async === undefined) {
        async = true;
    }
    var x = ajax.x();
    x.open(method, url, async);
    x.onreadystatechange = function () {
        if (x.readyState == 4) {
            callback(x.responseText)
        }
    };
    if (method == 'POST') {
        x.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    }
    x.send(data)
};

ajax.get = function (url, data, callback, async) {
    var query = [];
    for (var key in data) {
        query.push(encodeURIComponent(key) + '=' + encodeURIComponent(data[key]));
    }
    ajax.send(url + (query.length ? '?' + query.join('&') : ''), callback, 'GET', null, async)
};

ajax.post = function (url, data, callback, async) {
    var query = [];
    for (var key in data) {
        query.push(encodeURIComponent(key) + '=' + encodeURIComponent(data[key]));
    }
    ajax.send(url, callback, 'POST', query.join('&'), async)
};

/**
 * function to reset the checkbox selections of a group
 */
function resetFileSelection(chkbox, gidx, gcnt, initcall) {
   var idbox, sidx, cidx, i;
   var changed = true;
   var checked = chkbox ? chkbox.checked : false;
   var checks = document.form.elements["GRP" + gidx];

   if(checks == null) return;

   if(chkbox == null || chkbox.value == -1) {
      for(i = 0; i < checks.length; i++) {
         if(!(checks[i].disabled || checks[i].checked == checked)) checks[i].checked = checked;
      }
   } else {
      if(checked) {
         // checking multiple selections
         cidx = sidx = -1;
         for(i = 0; i < checks.length; i++) {
            if(checks[i].checked) {
               if(checks[i].value == chkbox.value) {
                  cidx = i;
                  if(sidx == checks.length) break;
               } else if(sidx == -1) {
                  sidx = i;
               } else {
                  sidx = checks.length;
                  if(cidx >= 0) break;
               }
            }
         }
         if(sidx >= 0 && sidx < checks.length) {
            if(sidx - cidx > 1) {
               yn_window(gidx, cidx, sidx, gcnt, 0);
               changed = false;
            } else if(cidx - sidx > 1) {
               yn_window(gidx, sidx, cidx, gcnt, 1);
               changed = false;
            }
         }
         if(changed) {  // checking if any unselected
            for(i = 0; i < checks.length; i++) {
               if(!(i == cidx || checks[i].disabled || checks[i].checked || checks[i].value == -1)) {
                  checked = false;
                  break;
               }
            }
         }
      }
      if(changed) {
         chkbox = document.getElementById("TGRP" + gidx);
        if(chkbox.checked != checked)  chkbox.checked = checked;
      }
   }

   if(changed) {
      groupFileSelection(gidx);
      if(initcall) {
         eval("idbox = document.form.GID" + gidx);
         if(idbox && idbox.checked != checked) {
            idbox.checked = checked;
            resetGroupSelection(gidx, gcnt, 0);
         }
      }
   }
}

/**
 * function to reset the checkbox selections of group ids
 */
function resetGroupSelection(gidx, gcnt, initcall) {
   var idbox, topbox;
   var checked;
   var i;

   eval("idbox = document.form.GID" + gidx);
   checked = idbox.checked;

   if(gidx == 0) { // GROUP ID check box clicked
      for(i = 1; i <= gcnt; i++) {
         eval("idbox = document.form.GID" + i);
         if(idbox && !(idbox.disabled || idbox.checked == checked)) {
            idbox.checked = checked;
            if(initcall) {
               topbox = document.getElementById("TGRP" + i);
               if(topbox && topbox.checked != checked) {
                  topbox.checked = checked;
                  resetFileSelection(topbox, i, gcnt, 0);
               }
            }
         }
      }
   } else {
      if(initcall) {
         topbox = document.getElementById("TGRP" + gidx);
         if(topbox && topbox.checked != checked) {
            topbox.checked = checked;
            resetFileSelection(topbox, gidx, gcnt, 0);
         }
      }
      if(checked) {
         for(i = 1; i <= gcnt; i++) {
            if(i != gidx) {
               eval("idbox = document.form.GID" + i);
               if(idbox && !(idbox.disabled || idbox.checked)) {
                  checked = false;
                  break;
               }
            }
         }
      }
      if(document.form.GID0.checked != checked) {
         document.form.GID0.checked = checked;
      }
   }
}

/**
 * function to redisplay full (act == 1) or short (act == 0) notes
 * do action on all notes if nidx is 0
 */
function displayNotes(nidx, ncnt, gidx, act) {
   var lnote, snote;
   var i, ldsp, sdsp;

   if(act == 1) {
      ldsp = "inline";
      sdsp = "none";
   } else {
      ldsp = "none";
      sdsp = "inline";
   }
   for(i = nidx; i <= ncnt; i++) {
      lnote = document.getElementById("LN" + gidx + "_" + i);
      if(nidx != ncnt && lnote == null) continue;
      snote = document.getElementById("SN" + gidx + "_" + i);
      lnote.style.display=ldsp;
      snote.style.display=sdsp;
   }
}

/**
 * function to show (act == 1) or hide (act == 0) sub groups
 */
function displayGroupNodes(hcnt, act) {
   var gopen, ghide;
   var i, hdsp;

   gopen = document.getElementById("GOPEN0");
   ghide = document.getElementById("GHIDE0");
   if(act == 1) {
      gopen.style.display="none";
      ghide.style.display="inline";
      hdsp = "table-row";
   } else {
      gopen.style.display="inline";
      ghide.style.display="none";
      hdsp = "none";
   }
   for(i = 1; i <= hcnt; i++) {
      ghide = document.getElementById("GHIDE" + i);
      ghide.style.display=hdsp;
   }
}

/**
 * function to valid form inputs
 *
 */
function checkFileSelection(grpcnt)
{
   var i, j, fidx;
   var checks;
   var sizes;
   var size = 0;
   var count = 0;
   var gidx, idx1, idx2;

   CHKCNT = 0;

   for(i = 1; i <= grpcnt; i++) {
      checks = document.form.elements['GRP' + i];
      sizes = document.form.elements['SIZ' + i];
      if(checks == null) continue;
      CHKCNT += checks.length - 1;
      for(j = 0; j < checks.length; j++) {
         if(checks[j].checked && checks[j].value >= 0) {
            count++;
            fidx = parseInt(checks[j].value);
            size = size + parseInt(sizes[fidx].value);
         }
      }
   }
   if(count == 0) {
      alert("Select at least one file to continue!");
   }
   document.form.total.value = size;
   return count;
}

function groupFileSelection(gidx)
{
   var i, j, fidx;
   var checks;
   var sizes;
   var size = 0;
   var count = 0;
   var disabled;

   checks = document.form.elements['GRP' + gidx];
   if(checks == null) return;
   sizes = document.form.elements['SIZ' + gidx];
   for(j = 0; j < checks.length; j++) {
      if(checks[j].checked && checks[j].value >= 0) {
         count++;
         fidx = parseInt(checks[j].value);
         size = size + parseInt(sizes[fidx].value);
      }
   }
   if(count > 0) {
      i = count > 1 ? "s" : "";
      j = count + " File" + i + " (" + totalSize(size) + ")";
      disabled = false;
   } else {
      j = "0 File";
      disabled = true;
   }
   document.getElementById("SUM" + gidx).innerHTML = j;
   document.getElementById("BTN" + gidx).disabled = disabled;
}

/**
 * set value for hidden input: action
 */

function setActionType(act)
{
   document.form.action.value = act;
}

/**
 * open a note window for long description
 */

function openNoteWindow(gindex, title)
{
   eval("note = document.form.GNOTE" + gindex + ".value");

   notewin = window.open("", "DescWin", "width=700,height=400,scrollbars=yes,resizable=yes");

   notewin.document.write("<html><head><title>" + title + "</title></head><body>\n" +
           "<p><h3>Data Description for '" + title + "':</h3>\n" + note + "</p>\n" +
           "<form><center><input type=\"button\" value=\"Close This Window\" " +
           "onClick=\"self.close()\"></center></form>\n</body></html>\n");
   notewin.document.close();
   notewin.focus();
}

/**
 * open a help window for given key
 */

function helpWindow(hkey, title)
{
   eval("note = document.form.HELP" + hkey + ".value");

   notewin = window.open("", "DescWin", "width=700,height=400,scrollbars=yes,resizable=yes");
   notewin.document.write("<html><head><title>" + title + "</title></head><body>\n" +
           "<p><h3>Help Information for " + title + ":</h3>\n" + note + "</p>\n" +
           "<form><center><input type=\"button\" value=\"Close This Window\" " +
           "onClick=\"self.close()\"></center></form>\n</body></html>\n");
   notewin.document.close();
   notewin.focus();
}

/**
 * open a help window
 */

function openHelpWindow(helpkey, grpcnt)
{
   var $dfmt;
   notewin = window.open("", "DescWin", "width=500,height=400,scrollbars=yes,resizable=yes");

   notewin.document.write("<html><head><title>Help Document</title></head><body>\n");
   if(helpkey == "ff") { // file archive format help
      notewin.document.write("<p><h3>Archive Format - post-proccessed file archive format:</h3>\n" +
              "<ul><li>BI - binary COS blocked *\n" +
              "<li>C1/CH - ASCII/character COS blocked *\n<li>TAR - multiple files archived into one file via 'tar'\n" +
              "<li>Z - compressed via UNIX 'compress'\n" +
              "<li>ZIP - compressed via 'zip'\n" +
              "<li>GZ - compressed via 'gzip'\n" +
              "<li>BZ2 - compressed via 'bzip2'</ul>\n" +
              "Example: <b>C1.TAR.GZ</b> means ASCII COS blocked,\n" +
              "then tarred, and then gzipped.<p>" +
              "* COS blocks can be checked and removed by the Unix " +
              "utility programs 'cosfile', 'cossplit', and 'cosconvert'. These " +
              "utilities are available on most CISL computers; otherwise click " +
              "<a href=\"javascript:window.open('/index.html#cosb');self.close()\">" +
              "HERE</a> to download them.</p>\n");
   } else if(helpkey == 'fc') { // index checkbox help
      var tmp = grpcnt > 1 ? "group" : "file list";
      notewin.document.write("<p><h3>Usage of the filelist checkboxes:</h3>" +
                "Click the checkbox at the top of this column to select/unselect " +
                "all data files in the " + tmp + ". If checkboxes of two individual files " +
                "are selected with unselected ones between, you will be given the option " +
                "to include them.</p>\n");
   } else if(helpkey == 'gc') { // group checkbox help
      notewin.document.write("<p><h3>Usage of the group checkbox:</h3>" +
                "Click the checkbox at the top of this column to select/unselect " +
                "all data files shown on this webpage in different groups. " +
                "Click a checkbox of an individual group to select/unselect " +
                "all data files in the group.</p>\n");
   } else if(helpkey == 'wb') { // web button help
      notewin.document.write("<p><h3>Usage of Buttons:</h3>" +
                "Click the button labeled 'View Selected Files/Get As a Tar File' " +
                "to view the list of selected file names and to download them " +
                "together as a single tar file if the total size of the " +
                "selected data files does not exceed the 2GB limit. Perl/Csh " +
                "scripts for downloading the selected files are available via " +
                "the buttons labeled 'Perl Download Script'/'Csh Download Script'. " +
                "To run any of the download scripts, the internet download " +
                "utility program 'wget' must exist on your system.</p>\n");
   } else if(helpkey == 'gb') { // Globus download help
      notewin.document.write("<p><h3>Globus file transfer:</h3>" +
                "Click the button labeled 'Globus download' " +
                "to transfer your data files using the Globus data transfer " +
                "service.  After clicking the button, you will receive an e-mail " +
                "notification from Globus with a download link.  If you do not " +
                "have a Globus user account, you may either sign up for a new Globus account " +
                "or sign in with your RDA user name and password by clicking the " +
                "'alternate identity' link on the Globus login page and selecting " +
                "the 'NCAR RDA' identity provider.</p>\n");
   } else if(helpkey == 'mb') { // hpss button help
      notewin.document.write("<p><h3>Usage of Buttons:</h3>" +
                "Click the button labeled 'View Selected Files' to view the list of selected " +
                "HPSS file names. Perl/Csh scripts for downloading the selected files " +
                "are available via the buttons labeled 'Perl Download Script'/" +
                "'Csh Download Script'. To run any of the download scripts, the HPSS utility " +
                "program 'hsi' must exist on your system.</p>\n");
   } else if(helpkey == 'nc') { // glade button help
      notewin.document.write("<p><h3>Usage of Buttons:</h3>" +
                "Click the button labeled 'View Selected Files' to view the list of selected " +
                "file names on GLADE. Perl/Csh scripts for downloading the selected files " +
                "are available via the buttons labeled 'Perl Download Script'/" +
                "'Csh Download Script'. The Unix command 'cp -f' is used in the download scripts.</p>\n");
   } else if(helpkey == 'rb') { // hpss online request button help
      notewin.document.write("<p><h3>Usage of Buttons:</h3>" +
                "Click the button labeled 'View Selected Files/Request Online Download' " +
                "to view the list of selected HPSS file names and to send a " +
                "request to make them available for online download.</p>\n");
   } else if(helpkey == 'rf') { // format conversion request button help
      if(document.form.dfmt) {
         $dfmt = document.form.dfmt.value;
      } else {
         $dfmt = "";
      }

      notewin.document.write("<p><h3>Usage of Buttons:</h3>" +
                "Click the button labeled 'View Selected Files/Convert Format to " + $dfmt +
                 "' to view the list of selected file names and to " +
                "send a request to convert the data format.</p>\n");
   }
   notewin.document.write("<form><center><input type=\"button\" value=\"Close This Window\" " +
           "onClick=\"self.close()\"></center></form>\n</body></html>\n");
   notewin.document.close();
   notewin.focus();
}

/**
 * open a window for filelist, perl script or csh script
 * action: 0 - 'Csh', 1 - 'Python', 2 - 'Jupyter'
 */

function openFileWindow(grpcnt, act)
{
    var filewin;
    var ftype;
    var dsid;
    var action;
    var fname;
    var count = checkFileSelection(grpcnt);

    if(count == 0) return;

    ftype = document.form.ftype.value;
    dsid = document.form.dsid.value;
    fname = dsid;
    if(act == 0) {
        action = 'Csh';
        fname += '.csh';
    }
    else if(act == 1) {
        action = 'Python';
        fname += '.py';
    }
    else if(action == 2) {
        action = 'Jupyter';
        fname += '.ipynb';
    }
    else if(action == 4)
    {
        action = 'Filelist';
        fname += '.list.txt';
    }
    if(act == 4)
    {
        console.log(dsid);
        console.log(grpcnt);
        console.log(count);
        console.log(ftype);
        showFilelist(dsid, grpcnt, count, ftype);
    }
    else
    {
    filewin = null;
    if(ftype == 'HPSS') {
        filewin = window.open("", action, "width=750,height=600,scrollbars=yes,resizable=yes");
        showHPSSScript(filewin, action, dsid, grpcnt, count);
    } else if(ftype == 'HTAR') {
        filewin = window.open("", action, "width=750,height=600,scrollbars=yes,resizable=yes");
        showHtarScript(filewin, action, dsid, grpcnt, count);
    } else if(ftype == 'NCAR') {
        filewin = window.open("", action, "width=750,height=600,scrollbars=yes,resizable=yes");
        showGLADEScript(filewin, action, dsid, grpcnt, count);
    } else {
        showWebScript(action, dsid, grpcnt, count);
    }
    }
    if(filewin)
    {
        filewin.document.close();
        filewin.focus();
    }
}

function showFilelist(dsid, grpcnt, count, ftype)
{
   var i, j, k, fidx;
   var srcids, files, checks;
   var limit, grpid;
   var size = document.form.total.value;
   var total = totalSize(size);
   var s = count > 1 ? "s" : "";
   var are = count > 1 ? " are" : " is";
   var sizes, locfiles, notes;
   var specialist, name;
   var htarfile
   var gname;
   var stat = 0;
   var ogidx = 1;
   var showgroup = false;
   var showlocal = false;
   var shownote = false;
   var adesc, wpath;
   var html, hidden_input;
   var gindex = document.form.gindex ? document.form.gindex.value : 0;
   var rtype = document.form.rtype ? document.form.rtype.value : null;
   var atype = document.form.atype ? document.form.atype.value : null;
   var rstat = document.form.rstat ? document.form.rstat.value : null;
   var dfmt = document.form.dfmt ? document.form.dfmt.value : null;

   if(ftype == "Web" && !rtype) {
      html = "<form name=\"form\" action=\"/cgi-bin/mget.tar\" method=\"post\">\n";
   } else {
      html = "<form name=\"form\" action=\"/php/dsrqst.php\" method=\"post\">\n";
   }
   if(ftype == 'HTAR') {
     htarfile = document.form.htarfile.value;
     html += "<p><h2>" + ftype + " member file" + s + " selected from '" + htarfile +
             "'</h2></p>\n<p>You have selected <strong>" + count + " member file" + s + " (" +
             total + ")</strong>.\n";
   } else {
     html += "<p><h2>" + ftype + " file" + s + " selected for '" + dsid +
            "'</h2></p>\n<p>You have selected <strong>" + count + " file" + s + " (" +
            total + ")</strong>.\n";
   }
   size /= 2000000000;
   if(ftype == "Web" && !rtype) {
      if(count > 1) {
         if(size >= 2) {
            html += "The total data size exceeds the limit of <strong>2.0GB</strong>. " +
                    "The selected files cannot be downloaded directly as a single tar " +
                    "file. Please select a smaller number of files to download.</p>\n" +
                    "<p><a href=\"javascript:void(0)\" onclick=\"displayDownloadForm(0)\">" +
                    "Back to file selection</a></p>\n";
         } else {
            if(document.form.mpath) {
               wpath = document.form.mpath.value;
            } else {
               wpath = document.form.wpath.value;
            }
            html += "<input type=\"hidden\" name=\"directory\" value=\"" + wpath + "/\">\n";
            html += "Click the button labeled <strong>'Download tar file'</strong> to " +
                    "download the selected files as a single tar file.</p>\n";
            html += "<p><button type=\"submit\" class=\"btn btn-primary\">" +
                    "Download tar file</button>&nbsp;" +
                    "<a class=\"btn btn-link\" href=\"javascript:void(0)\" onclick=\"displayDownloadForm(0)\">Return to file list</a></p>\n";
            stat = 2;
         }
      } else if(CHKCNT > 1) {
         html += "(Select multiple files to download as a single tar file)</p>\n";
      } else {
         html += "</p>\n";
      }
   } else if(rtype) { // dsrqst files
      limit = document.form.alimit ? document.form.alimit.value : 20;
      rstr = (dfmt ? ("converting format to " + dfmt) : "online download");
      if(size >= limit) {
         html += "The total data size exceeds the limit of " + limit + "GB. " +
                 "The selected files can not be requested for " + rstr +". " +
                 "Please select a smaller number of files to download.</p>\n" +
                 "<p><a href=\"javascript:void(0)\" onclick=\"displayDownloadForm(0)\">" +
                 "Back to file selection</a></p>\n</p>\n";
      } else {
         stat = check_access_type(atype);
         if(stat == 1) {
            html += "<input type=\"hidden\" name=\"dsid\" value=\"" + dsid + "\">\n";
            if(gindex) {
               html += "<input type=\"hidden\" name=\"gindex\" value=\"" + gindex + "\">\n";
            }
            if(ftype == 'HTAR') {
               html += "<input type=\"hidden\" name=\"htarfile\" value=\"" + htarfile + "\">\n";
            }
            if(rstat) {
               html += "<input type=\"hidden\" name=\"rstat\" value=\"" + rstat + "\">\n";
            }
            html += "<input type=\"hidden\" name=\"rtype\" value=\"" +  rtype + "\">\n";
            html += "Click the following button to send a request for " + rstr + ".</p>\n";
            html += "<p><input type=\"submit\" value=\"Request " + rstr + " for selected files\"></p>\n";
         } else {
            adesc = document.form.adesc.value;
             if(stat == 0) {
                html + "You need to login to our web server with permission to " +
                       "access " + adesc + " before you may submit a request for " +
                       + rstr + " of the selected data.</p>\n";
            } else {
                html += "You do not have the permission to access " + adesc +
                        " and therefore are not able to submit a request " +
                        "for " + rstr + " of the selected data.</p>\n";
            }
         }
      }
   }

   if(document.form.specialist) {
      specialist = document.form.specialist.value;
      name = document.form.fstname.value + " " + document.form.lstname.value;
   } else {
      specialist = "zji";
      name = "Zaihua Ji";
   }
   specialist = "rdahelp"
   name = "RDA help desk"
   html += "<p>Contact <strong>" + specialist + "@ucar.edu (" + name + ")</strong> for further assistance.</p>\n";
   // check if show local file names / group ids
   for(i = 1; i <= grpcnt; i++) {
      checks = document.form.elements["GRP" + i];
      if(checks == null) continue;
      if(ftype == 'HPSS') locfiles = document.form.elements["LOC" + i];
      gname = eval("document.form.GNAME" + i);
      notes = document.form.elements["NOTE" + i];
      if(locfiles || gname || notes) {
         for(j = 0; j < checks.length; j++) {
            if(checks[j].checked && checks[j].value >= 0) {
               fidx = parseInt(checks[j].value);
               if(locfiles && !showlocal && locfiles[fidx].value) showlocal = true;
               if(notes && !shownote && notes[fidx].value) shownote = true;
               if(gname && !showgroup && i != ogidx) showgroup = true;
               ogidx = i;
            }
         }
      }
      if(showgroup && (showlocal || shownote)) break;
   }
   if(showlocal) {
      shownote = false;
   }
   html += "<p>The file" + s + " you have selected" + are + " listed below:\n";
   html += "<p><table class=\"filelist\" style=\"width: 100%\">\n";
   html += "<tr class=\"blue-header\">\n";
   html += "<th class=\"blue-header\">INDEX</th>\n";
   html += "<th class=\"blue-header\">File Name</th>\n";
   if(showlocal) html += "<th class=\"blue-header\">Original File Name</th>\n";
   html += "<th class=\"blue-header\">Size</th>\n";
   if(showgroup) html += "<th class=\"blue-header\">GROUP ID</th>\n";
   if(shownote) html += "<th class=\"blue-header\">Description</th>\n";
   html += "</tr>\n";
   k = 1;
   hidden_input = "";
   for(i = 1; i <= grpcnt; i++) {
      checks = document.form.elements["GRP" + i];
      if(checks == null) continue; // should not happen
      files = document.form.elements["FIL" + i];
      sizes = document.form.elements["SIZ" + i];
      if(stat == 1) srcids = document.form.elements["SID" + i];
      gname = eval("document.form.GNAME" + i);
      sizes = document.form.elements["SIZ" + i];
      if(showlocal) {
         locfiles = document.form.elements["LOC" + i];
      } else if(shownote) {
         notes = document.form.elements["NOTE" + i];
      }
      for(j = 0; j < checks.length; j++) {
         if(!checks[j].checked || checks[j].value == -1) continue;
         fidx = parseInt(checks[j].value);
         html += "<tr class=\"zebra\">";
         html += "<td class=\"zebra\" align=\"right\">" + k++ + "</td>\n";
         html += "<td class=\"zebra\">" + files[fidx].value + "</td>\n";
         if(showlocal) {
            if(locfiles) {
               html += "<td class=\"zebra\">" + str_value(locfiles[fidx]) + "</td>\n";
            } else {
               html += "<td class=\"zebra\">&nbsp;</td>\n";
            }
         }
         html += "<td class=\"zebra\" align=\"right\">" + totalSize(sizes[fidx].value) + "</td>\n";
         if(showgroup) html += "<td class=\"zebra\">" + str_value(gname) + "</td>\n";
         if(shownote) html += "<td class=\"zebra\">" + str_value(notes[fidx]) + "</td>\n";
         html += "</tr>\n";
         if(stat == 2) {
            hidden_input += "<input type=\"hidden\" name=\"file\" value=\"" +
                               files[fidx].value + "\">\n";
         } else if(stat == 1) {
            hidden_input += "<input type=\"hidden\" name=\"srcids[]\" value=\"" +
                               srcids[fidx].value + "\">\n";
         }
      }
   }
   html += "</table></p>\n";
   html += hidden_input + "</form>\n";
   displayDownloadForm(1);
   document.getElementById("downloadForm").innerHTML = html;
}

function showHPSSScript(win, action, dsid, grpcnt, count)
{
   var i, j, k, l, fidx;
   var filelist = new Array();
   var loclist = new Array();
   var files, checks;
   var locfiles;
   var script;
   var lfile;

   // built up HPSS and local file lists
   for(k = 0, i = 1; i <= grpcnt; i++) {
      checks = document.form.elements["GRP" + i];
      if(checks == null) continue;
      files = document.form.elements["FIL" + i];
      locfiles = document.form.elements["LOC" + i];
      for(j = 0; j < checks.length; j++) {
         if(!checks[j].checked || checks[j].value == -1) continue;
         fidx = parseInt(checks[j].value);
         filelist[k] = files[fidx].value;
         if(locfiles == null) {
            loclist[k] = null;
         } else {
            lfile = locfiles[fidx].value;
            if(lfile.indexOf('/') == 0) {  // remove absolute path
               l = lfile.lastIndexOf('/');
               loclist[k] = lfile.substring(l + 1, lfile.length);
            } else {
               loclist[k] = lfile;
            }
         }
         k++;
      }
   }
   for(i = 0; i < count; i++) {
      if(loclist[i] != null) {
         for(j = 0; j < i; j++) {
            if(loclist[j] == loclist[i]) {
               loclist[i] = null;  // same local file names
               break;
            }
         }
      }
      if(loclist[i] == '' || loclist[i] == null) {  // use HPSS file name if missed
         lfile = filelist[i];
         l = lfile.lastIndexOf('/');
         loclist[i] = lfile.substring(l + 1, lfile.length);
      }
   }

   // write out script
   win.document.write("<pre>" + mssScriptHeader(action, dsid, count));
   if(action == 'Perl') {
      script = "use strict;\nuse File::Basename;\nmy $dir;\nmy $syscmd;\nmy @filelist = (\n";
      for(i = 0; i < count; i++) {
          script += "  [\"" + filelist[i] + "\", \"" + loclist[i] + "\"],\n";
      }
      script += ");\n"
             + "for(my $i = 0; $i < @filelist; $i++) {\n"
             + "  $dir = dirname($filelist[$i][1]);\n"
             + "  if($dir && ! -e $dir) {\n"
             + "    $syscmd = \"mkdir -p $dir\";\n"
             + "    print \"$syscmd...\\n\";\n"
             + "    system($syscmd);\n  }\n"
             + "  $syscmd = \"hsi get $filelist[$i][1] : $filelist[$i][0]\";\n"
             + "  print \"$syscmd...\\n\";\n"
             + "  system($syscmd);\n"
             + "}\nexit 0;\n";
      win.document.write(script);
   } else {
      for(j = 0; j < count; j += 300) {
         script = "set filelist = ( \\\n";
         k = (j + 300) < count ? (j + 300) : count;
         for(i = j; i < k; i++) {
            script += "  " + filelist[i] + " " + loclist[i] + " \\\n";
         }
         script += ")\n\n"
                +  "while($#filelist > 0)\n"
                + "  set dir = `dirname $filelist[2]`\n"
                + "  if ( x$dir != 'x' && ! -e $dir ) then\n"
                + "    echo \"mkdir -p $dir...\"\n"
                + "    mkdir -p $dir\n  endif\n"
                +  "  echo \"hsi get $filelist[2] : $filelist[1]...\"\n"
                +  "  hsi get $filelist[2] : $filelist[1]\n\n"
                +  "  shift filelist\n  shift filelist\n"
                +  "end\n\n";
         win.document.write(script);
      }
      win.document.write("exit 0\n</pre>");
   }
}

function showHtarScript(win, action, dsid, grpcnt, count)
{
   var i, j, k, l, fidx;
   var filelist = new Array();
   var files, checks;
   var script;
   var htarfile = document.form.htarfile.value;

   // built up HPSS and local file lists
   for(k = 0, i = 1; i <= grpcnt; i++) {
      checks = document.form.elements["GRP" + i];
      if(checks == null) continue;
      files = document.form.elements["FIL" + i];
      for(j = 0; j < checks.length; j++) {
         if(!checks[j].checked || checks[j].value == -1) continue;
         fidx = parseInt(checks[j].value);
         filelist[k] = files[fidx].value;
         k++;
      }
   }

   // write out script
   win.document.write("<pre>" + htarScriptHeader(action, htarfile, count));
   if(action == 'Perl') {
      script = "use strict;\nuse File::Basename;\nmy $dir;\nmy $syscmd;\nmy $htarfile = '" +
      		      htarfile + "';\nmy @filelist = (\n";
      for(i = 0; i < count; i++) {
          script += "  '" + filelist[i] + "',\n";
      }
      script += ");\n"
             + "for(my $i = 0; $i < @filelist; $i++) {\n"
             + "  $dir = dirname($filelist[$i]);\n"
             + "  if($dir && ! -e $dir) {\n"
             + "    $syscmd = \"mkdir -p $dir\";\n"
             + "    print \"$syscmd...\\n\";\n"
             + "    system($syscmd);\n  }\n"
             + "  $syscmd = \"htar -xf $htarfile $filelist[$i]\";\n"
             + "  print \"$syscmd...\\n\";\n"
             + "  system($syscmd);\n"
             + "}\nexit 0;\n";
      win.document.write(script);
   } else {
      win.document.write("set htarfile = " + htarfile + "\n");
      for(j = 0; j < count; j += 300) {
         script = "set filelist = ( \\\n";
         k = (j + 300) < count ? (j + 300) : count;
         for(i = j; i < k; i++) {
            script += "  " + filelist[i] + " \\\n";
         }
         script += ")\n\n"
                +  "while($#filelist > 0)\n"
                + "  set dir = `dirname $filelist[1]`\n"
                + "  if ( x$dir != 'x' && ! -e $dir ) then\n"
                + "    echo \"mkdir -p $dir...\"\n"
                + "    mkdir -p $dir\n  endif\n"
                +  "  echo \"htar -xf $htarfile $filelist[1]...\"\n"
                +  "  htar -xf $htarfile $filelist[1]\n"
                +  "  shift filelist\n"
                +  "end\n\n";
         win.document.write(script);
      }
      win.document.write("exit 0\n</pre>");
   }
}

function showGLADEScript(win, action, dsid, grpcnt, count)
{
   var i, j, k, l, fidx;
   var filelist = new Array();
   var files, checks;
   var locfiles;
   var script;
   var lfile;

   // built up NCAR file lists
   for(k = 0, i = 1; i <= grpcnt; i++) {
      checks = document.form.elements["GRP" + i];
      if(checks == null) continue;
      files = document.form.elements["FIL" + i];
      for(j = 0; j < checks.length; j++) {
         if(!checks[j].checked || checks[j].value == -1) continue;
         fidx = parseInt(checks[j].value);
         filelist[k++] = files[fidx].value;
      }
   }

   // write out script
   win.document.write("<pre>" + gladeScriptHeader(action, dsid, count));
   if(action == 'Perl') {
      script = "use strict;\nmy $syscmd;\nmy @filelist = (\n";
      for(i = 0; i < count; i++) {
          script += "  \"" + filelist[i] + "\,\n";
      }
      script += ");\n"
             + "for(my $i = 0; $i < @filelist; $i++) {\n"
             + "  $syscmd = \"cp -f $filelist[$i] ./\";\n"
             + "  print \"$syscmd...\\n\";\n"
             + "  system($syscmd);\n"
             + "}\nexit 0;\n";
      win.document.write(script);
   }
    else if(action == 'Python') {
      script = "import sys, os\nimport requests\n"
             + "if len(sys.argv) < 2 and not 'RDAPSWD' in os.environ:\n"
             + "    print('Usage: ' + sys.argv[0] + ' YourPassword')\n"
             + "    exit(1)\n"
             + "else:\n    try:\n        pswd = sys.argv[1]\n"
             + "    except:\n        pswd = os.environ['RDAPSWD']\n\n"
             + "url = '" + CGIBIN + "login'\n"
             //+"values = {'email' : '" + email + "', 'passwd' : pswd, 'action' : 'login'}\n"
             + "# Authenticate\n"
             + "ret = requests.post(url,data=values)\n"
             + "if ret.status_code != 200:\n    print('Bad Authentication')\n    exit(1)\n"
             //+ "dspath = '" + wpath +"'\n"
             + "filelist = [\n";
      for(i = 0; i< count-1; i++) {
          script += "'" + filelist[i] + "',\n";
      }
      script += "'" + filelist[count-1] + "']\n";
      script += "for file in filelist:\n    filename=dspath+file\n"
             + "    print('Downloading',file)\n"
             + "    req = requests.get(filename, cookies = ret.cookies, allow_redirects=True)\n"
             + "    open(os.path.basename(filename), 'wb').write(req.content)"
      win.document.write(script);
      console.log(script);
      var blob = new Blob([script], {type: "text/plain;charset=utf-8"});
      saveAs(blob, 'download.py');
    }
    else {
      for(j = 0; j < count; j += 300) {
         script = "set filelist = ( \\\n";
         k = (j + 300) < count ? (j + 300) : count;
         for(i = j; i < k; i++) {
            script += "  " + filelist[i] + " \\\n";
         }
         script += ")\n\n"
                +  "while($#filelist > 0)\n"
                +  "  echo \"cp -f $filelist[1]\"\n"
                +  "  cp -f $filelist[1] ./ \n\n"
                +  "  shift filelist\n"
                +  "end\n\n";
         win.document.write(script);
      }
      win.document.write("exit 0\n</pre>");
   }
}

function showWebScript(action, dsid, grpcnt, count)
{
   var i, j, k, fidx;
   var filelist = new Array();
   var filename;
   var files, checks;
   var script;
   var cookies;
   var wpath;
   var email = null;
   var dtype = document.form.dtype ? document.form.dtype.value : '';

   if(dtype == 'O') {
      wpath = DSSURL + "/datasets/" + dsid + "/docs/";
   } else if(dtype == 'S') {
      wpath = DSSURL + "/datasets/" + dsid + "/software/";
   } else {
      wpath = RPATH + document.form.wpath.value + "/";
   }

   // get duser cookie for email
   // email = get_user_email(true);
   // if(email == null) {
   //    alert('Please log in to download the script');
   //   return;
   // }

   // built up Web file list
   for(k = 0, i = 1; i <= grpcnt; i++) {
      checks = document.form.elements["GRP" + i];
	   if(checks == null) continue;
      files = document.form.elements["FIL" + i];
      for(j = 0; j < checks.length; j++) {
         if(checks[j].checked && checks[j].value >= 0) {
            fidx = parseInt(checks[j].value);
            filelist[k++] = files[fidx].value;
         }
      }
   }

   // write out script
   script = webScriptHeader(action, dsid, count);
   script += "\n"
   if(action == 'Python') {
      script += "import sys, os\n"
             + "from urllib.request import build_opener\n\n"
             + "opener = build_opener()\n"
             + "dspath = '" + wpath +"'\n"
             + "filelist = [\n";
      for(i = 0; i< count-1; i++) {
          script += "  '" + filelist[i] + "',\n";
      }
      script += "  '" + filelist[count-1] + "'\n]\n\n"
             + "for file in filelist:\n"
             + "   filename = dspath + file\n"
             + "   ofile = os.path.basename(filename)\n"
             + "   sys.stdout.write(\"downloading \" + ofile + \" ... \")\n"
             + "   sys.stdout.flush()\n"
             + "   infile = opener.open(filename)\n"
             + "   outfile = open(ofile, \"wb\")\n"
             + "   outfile.write(infile.read())\n"
             + "   outfile.close()\n"
             + "   sys.stdout.write(\"done\\n\")\n";
  
      var blob = new Blob([script], {type: "text/plain;charset=utf-8"});
      saveAs(blob, 'download_'+dsid+'.py');
    }
    else if(action == 'Csh') {
         filename = 'download_'+dsid+'.csh';
         script += "set opts = '-N'\n"
             + "# Check wget version.  Set the --no-check-certificate option\n"
             + "# if wget version is 1.10 or higher.\n" 
             + "set v = `wget -V |grep 'GNU Wget ' | cut -d ' ' -f 3`\n"
             + "set a = `echo $v | cut -d '.' -f 1`\n"
             + "set b = `echo $v | cut -d '.' -f 2`\n"
             + "if(100 * $a + $b > 109) then\n"
             + " set cert_opt = '--no-check-certificate'\nelse\n"
             + " set cert_opt = ''\nendif\n";

      for(j = 0; j < count; j += 600) {
         script += "set filelist = ( \\\n";
         k = (j + 600) < count ? (j + 600) : count;
         for(i = j; i < k; i++) {
            script += "  " + filelist[i] + " \\\n";
         }
         script += ")\nwhile($#filelist > 0)\n"
                +  "  set syscmd = \"wget $opts $cert_opt " + wpath + "$filelist[1]\"\n"
                +  "  echo \"$syscmd ...\"\n"
                +  "  $syscmd\n"
                +  "  shift filelist\nend\n";
      }
      var blob = new Blob([script], {type: "text/plain;charset=utf-8"});
      saveAs(blob, 'download_'+dsid+'.csh');
   }
   else {
	data = 'wpath='+wpath+';dsid='+dsid+';email='+email+';count='+count+';filelist='+filelist+';';
        ajax.send('/createNotebook',  function(result){
                script = result;
                var blob = new Blob([script], {type: "text/plain;charset=utf-8"});
                saveAs(blob, 'download_'+dsid+'.ipynb');
                }, 'POST', data);
    }
}

/**
 * get total size with unit
 */
function totalSize(size)
{
   var units = new Array("B", "K", "M", "G", "T", "P");
   var i = 0;

   while(i < 5 && size >= 1000) {
      size /= 1000;
      i++;
   }
   return (Math.round(size * 100) / 100) + units[i];
}

/**
 * get string of HPSS script header
 */
function mssScriptHeader(action, dsid, count)
{
   var header, specialist, name;
   var total = totalSize(document.form.total.value);

   if(action == 'Perl') {
      header = "<pre>#!/bin/perl -w\n";
   }
   else if(action == 'Python') {
      header = "<pre>#!/usr/bin/env python\n"
   }
    else {
      header = "<pre>#!/bin/csh\n";
   }

   if(document.form.specialist) {
      specialist = document.form.specialist.value;
      name = document.form.fstname.value + " " + document.form.lstname.value;
   } else {
      specialist = "zji";
      name = "Zaihua Ji";
   }
   specialist = "rdahelp"
   name = "RDA help desk"
   header += "#################################################################\n"
          +  "# Auto-generated " + action + " Script to retrieve " + count + " HPSS file(s) of\n"
          +  "# Dataset '" + dsid + "', total " + total + ", on any Unix machine\n"
          +  "# with HPSS connection. This script uses HPSS command 'hsi' to\n"
          +  "# download the data. Make sure you have enough disk space to hold\n"
          +  "# the data. A HPSS file name will be replaced by a local file name\n"
          +  "# if it is recorded in RDADB and also unique in the local file list.\n#\n"
          +  "# Highlight this script by Select All, Copy and Paste it into a file;\n"
          +  "# make the file executable and run it on command line.\n#\n"
          +  "# Contact " + specialist + "@ucar.edu (" + name + ") for further assistance.\n"
          +  "#################################################################\n\n";

   return header;
}

/**
 * get string of HTAR script header
 */
function htarScriptHeader(action, htarfile, count)
{
   var header, specialist, name;
   var total = totalSize(document.form.total.value);

   if(action == 'Perl') {
      header = "<pre>#!/bin/perl -w\n";
   } else {
      header = "<pre>#!/bin/csh\n";
   }

   if(document.form.specialist) {
      specialist = document.form.specialist.value;
      name = document.form.fstname.value + " " + document.form.lstname.value;
   } else {
      specialist = "zji";
      name = "Zaihua Ji";
   }
   specialist = "rdahelp"
   name = "RDA help desk"
   header += "#################################################################\n"
          +  "# Auto-generated " + action + " Script to retrieve " + count + " member file(s),\n"
          +  "# total " + total + ", From HTAR '" + htarfile + "', on any Unix machine\n"
          +  "# with HPSS connection. This script uses HPSS command 'htar' to\n"
          +  "# retrieve the HTAR member file(s). Make sure you have enough disk\n"
          +  "# space to hold the data. .\n#\n"
          +  "# Highlight this script by Select All, Copy and Paste it into a file;\n"
          +  "# make the file executable and run it on command line.\n#\n"
          +  "# Contact " + specialist + "@ucar.edu (" + name + ") for further assistance.\n"
          +  "#################################################################\n\n";

   return header;
}

/**
 * get string of GLADE script header
 */
function gladeScriptHeader(action, dsid, count)
{
   var header, specialist, name;
   var total = totalSize(document.form.total.value);
   var wpath = document.form.wpath.value;

   if(action == 'Perl') {
      header = "<pre>#!/bin/perl -w\n";
   } else {
      header = "<pre>#!/bin/csh\n";
   }

   if(document.form.specialist) {
      specialist = document.form.specialist.value;
      name = document.form.fstname.value + " " + document.form.lstname.value;
   } else {
      specialist = "zji";
      name = "Zaihua Ji";
   }
   specialist = "rdahelp"
   name = "RDA help desk"
   header += "#################################################################\n"
          +  "# Auto-generated " + action + " Script to retrieve " + count + " NCAR file(s) for\n"
          +  "# Dataset '" + dsid + "', total " + total + ", on any computer that can access\n"
          +  "# " + wpath + ". This script uses Unix command 'cp' to\n"
          +  "# retrieve the data. Make sure you have enough disk space to hold\n"
          +  "# the data. A file name will be replaced by a local file name\n"
          +  "# if it is recorded in RDADB and also unique in the local file list.\n#\n"
          +  "# Highlight this script by Select All, Copy and Paste it into a file;\n"
          +  "# make the file executable and run it on command line.\n#\n"
          +  "# Contact " + specialist + "@ucar.edu (" + name + ") for further assistance.\n"
          +  "#################################################################\n\n";

   return header;
}

/**
 * get string of Web script header
 */
function webScriptHeader(action, dsid, count)
{
   var header, specialist, name;
   var total = totalSize(document.form.total.value);
   var dtype = document.form.dtype.value;
   var rinfo;
   var s = count > 1 ? "s" : "";
   var required = "";
   if(dtype == 'O') {
      dtype = "document";
   } else if(dtype == 'S') {
      dtype = "software";
   } else { // default
      dtype = "data";
   }

   if(document.form.rqstid) {
      rinfo = " from Request '" + document.form.rqstid.value + "'";
   } else {
      rinfo = "";
   }
   if (document.form.ridx) {
      rindex = "Request index: " + document.form.ridx.value;
   } else {
      rindex = "";
   }

   specialist = "rdahelp";
   name = "RDA help desk";

   if(action == 'Python') {
      header = "#!/usr/bin/env python\n\n";
      hashes = "\"\"\"\n";
      hash = "";
      method = "Python ";
      required = "";
  }
   else if(action == 'Csh') {
      header = "#!/usr/bin/env csh\n\n";
      hashes = "################################################################################\n";
      hash = "# ";
      method = "C shell ";
      required = " using wget";
   }
   else {
       header = ""
   }

   header += hashes
          + hash + method + "script to download selected " + dtype + " files from rda.ucar.edu" + required + ".\n"
          + hash + "Number of files selected: " + count + "\n"
          + hash + "Data volume: " + total + "\n"
          + hash + "RDA dataset: " + dsid + "\n"
          + hash + rindex + "\n\n";
   if (action == 'Csh') {
      header += hash + "NOTE: if you want to run under a different shell, make sure you change\n"
          + hash + "      the 'set' commands according to your shell's syntax\n\n"
          + hash + "Experienced Wget Users: add additional command-line flags to 'opts' below.\n"
          + hash + "  Use the -r (--recursive) option with care.\n"
          + hash + "  Do NOT use the -b (--background) option - simultaneous file downloads\n"
          + hash + "  can cause your data access to be blocked.\n\n";
   }
   header += hash + "After you save the file, don't forget to make it executable\n"
          +  hash + "  i.e. - \"chmod 755 <name_of_script>\"\n\n"
          +  hash + "Contact " + specialist + "@ucar.edu (" + name + ") for further assistance.\n"
          +  hashes;
   return header;
}

/**
 Display (action = 1) or hide (action = 0) files selected by user for download or
 Globus transfer
**/
function displayDownloadForm(action) {
   if (action == 1) {
      document.getElementById("dsForm").style.display = "none";
      document.getElementById("downloadForm").style.display = "block";
   }
   if (action == 0) {
      document.getElementById("downloadForm").innerHTML = "";
      document.getElementById("dsForm").style.display = "block";
   }
   return;
}

// get a string value of an object
function str_value(obj) {

   var str = "&nbsp;";

   if(obj && obj.value) str= obj.value;

   return str;
}

/**
  * check access type for login users
  * return 1 - OK to select files; 0 - not logged in yet; -1 - logged in but no permission
  */
function check_access_type(atype) {

   var cookies, k, email;

   if(atype == 'g') return 1;

   email = get_user_email(false);
   if(email == null) return 0;

   k = email.indexOf("<" + atype + ">");
   if(k > 0) {
      return 1; // found match access type
   } else {
      return -1;
   }
}

/**
  * Copies text to clipboard.
  */
function copyText(text) {
   var temp_input = document.getElementById('clipboard');
   temp_input.type='none'; 
   temp_input.value=text;
   temp_input.select(); 
   document.execCommand('copy');
   temp_input.type='hidden';
   console.log(text+' copied')
   return true;
}

