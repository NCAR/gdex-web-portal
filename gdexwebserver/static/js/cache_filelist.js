
var WPATH = 'https://gdex.ucar.edu';
var CGIBIN = WPATH+'/cgi-bin';
var GPATH = 'https://data.gdex.ucar.edu';
var SPATH = 'https://stratus.gdex.ucar.edu';
var RPATH = 'https://request.gdex.ucar.edu';

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
    $(document).on('click', '.parent_group, .table_group', toggleChildBoxes);
});
$('.file').on('click', toggleSingleBox);
$('.sort-column').on('click', sortColumn);
$('.clear-group-btn').on('click', clearFileSelections);
$('.btn-all-files').on('click', selectAllFiles);

// Per-file controls and the page filter: delegated so they work for ajax-loaded tables.
// Unbind first because this script is re-included each time the filelist is loaded.
$(document).off('.accessOptions')
   .on('click.accessOptions', '.file-toggle-btn', toggleFileDetail)
   .on('click.accessOptions', '.copy-path-btn', copyPathClicked)
   .on('click.accessOptions', '.preview-file-btn', previewFileClicked)
   .on('input.accessOptions', '.page-filter-input', pageFilterChanged)
   .on('click.accessOptions', '.page-filter-clear', pageFilterCleared);

// Client-side file name filter for groups that are not paginated (all files are in the table).
// Terms are whitespace separated, case-insensitive, all must match; * is a wildcard.
function pageFilterChanged() {
   var input = $(this);
   var table = $('#' + input.data('table'));
   var terms = $.trim(input.val()).toLowerCase().split(/\s+/).filter(Boolean).map(function(t) {
      return new RegExp(t.replace(/[.+?^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '.*'));
   });
   var rows = table.find('tbody > tr:not(.file-detail)');
   var shown = 0;
   rows.each(function() {
      var row = $(this);
      var name = row.children('td').eq(1).text().toLowerCase();
      var match = terms.every(function(re) { return re.test(name); });
      row.toggleClass('d-none', !match);
      var expanded = row.find('.file-toggle-btn').attr('aria-expanded') === 'true';
      row.next('.file-detail').toggleClass('d-none', !(match && expanded));
      if (match) { shown++; }
   });
   $('#' + input.data('table') + '_filter_count').text('Showing ' + shown + ' of ' + rows.length + ' files');
   setTableSummary(table);
}

function pageFilterCleared() {
   $('#' + $(this).data('table') + '_filter_input').val('').trigger('input');
}

function toggleFileDetail() {
   var btn = $(this);
   var detail = btn.closest('tr').next('.file-detail').toggleClass('d-none');
   var open = !detail.hasClass('d-none');
   var label = open ? 'Hide file details' : 'Show file details';
   btn.attr('aria-expanded', open).attr('data-tip', label).attr('aria-label', label);
   btn.find('i').toggleClass('fa-chevron-right', !open).toggleClass('fa-chevron-down', open);
}

function copyPathClicked() {
   var btn = $(this);
   navigator.clipboard.writeText(btn.data('path'));
   btn.find('i').removeClass('fa-copy').addClass('fa-check');
   setTimeout(function() { btn.find('i').removeClass('fa-check').addClass('fa-copy'); }, 2000);
}

function previewFileClicked() {
   var btn = $(this);
   var body = $('#filePreviewBody');
   $('#filePreviewTitle').text(btn.data('name'));
   body.html('<div class="spinner-border" role="status"></div><p class="mt-2 mb-0">Generating preview&hellip;</p>');
   bootstrap.Modal.getOrCreateInstance(document.getElementById('filePreviewModal')).show();
   // global:false keeps the page-wide ajaxSend/ajaxSuccess hooks above from replacing
   // #ds_content with the loading spinner (which would wipe the table and this modal)
   $.ajax({url: '/datasets/' + btn.data('dsid') + '/filelist-preview/', data: {path: btn.data('path')}, global: false})
      .done(function(d) {
         body.empty().append($('<img class="img-fluid">').attr('src', d.url).attr('alt', 'Preview of ' + btn.data('name')));
      })
      .fail(function(xhr) {
         var msg = (xhr.responseJSON && xhr.responseJSON.error) ||
                   'Unable to generate a preview for this file. (HTTP ' + xhr.status + ' from the portal)';
         body.empty().append($('<div class="alert alert-danger mb-0">').text(msg));
      });
}

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
    var rows = table.find('tr:gt(0):not(.file-detail)').toArray().sort(comparer($(this).parent().index()))
    this.asc = !this.asc
    if (!this.asc){rows = rows.reverse()}
    // keep each file's expandable detail row directly beneath it
    var details = rows.map(function(r) { return $(r).next('.file-detail'); });
    for (var i = 0; i < rows.length; i++){table.append(rows[i]); table.append(details[i])}
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
    var checked = $('.file:checked');
    if(checked.length == 0)
    {
        alert('No files are checked. Please select at least one file to continue.');
        throw 'No files selected';
    }
    return checked.map(function() {
        var row = $(this).closest('tr');
        var href = row.find('a').attr('href');
        var filename = (parse && href !== undefined) ? parseUrl(href).pathname : href;
        if(filename === undefined) {
            filename = row.find('a').text().trim();
        }
        return {'filename': filename, 'size': row.attr('data-size')};
    }).get();
}
function parseUrl(url)
{
   var a = document.createElement('a');
   a.href = url;
   return a;
}
/**
 * Replace the file list with a confirmation view of the selected files.
 * opts: {files, header, message, buttonText, onConfirm}
 */
function showSelectionConfirmation(opts)
{
    var files = opts.files;
    var totalSize = 0;
    $.each(getListFromKey(files, 'size'), function(){ totalSize += parseFloat(this) || 0; });

    var confirmation_div = $('<div></div>', {'id': 'confirmation-div', 'class': 'dataset p-3'});
    confirmation_div.append($("<h2></h2>", {'class':'mt-2'}).text(opts.header));
    confirmation_div.append($('<div></div>')
        .text('You have selected '+files.length+' files ('+Math.floor(totalSize/1000000)+' MB)'));
    confirmation_div.append($('<div></div>', {'style':'white-space:pre-line'}).text(opts.message));

    var confirm_button = $('<button />', {'class':'btn btn-primary mr-2'})
        .text(opts.buttonText)
        .on('click', opts.onConfirm);
    var cancel_button = $('<button />', {'class':'btn btn-outline-primary mr-2'})
        .text('Cancel')
        .on('click', function(){
           if($('#ds_content').length) {
              $('#ds_content').children().removeClass('d-none');
           }
           else {
              $('body').children().attr("style",'display:block');
           }
           $('#confirmation-div').remove();
        });
    confirmation_div.append($('<div />', {'class':'pt-2 pb-2'}).append(confirm_button).append(cancel_button));

    var file_table = $('<table />').append('<tr><th>Filename</th><th>Size</th></tr>');
    $.each(files, function(i, f) {
        file_table.append($('<tr></tr>')
            .append($('<td></td>').text(f['filename']))
            .append($('<td></td>').text(f['size'])));
    });
    confirmation_div.append(file_table);

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
function convertFiles()
{
    var dsid = $('#file_table').attr('data-dsid');
    showSelectionConfirmation({
        files: getCheckedFiles(),
        header: 'Web files selected for GDEX dataset '+dsid,
        message: 'Click the following button to send a request for converting format to NetCDF\n\n' +
                 'Contact datahelp@ucar.edu for further assistance',
        buttonText: 'Request format conversion to NetCDF for selected files',
        onConfirm: function(){ sendConvertApp(dsid); }
    });
}
function showGlobusConfirmation()
{
    var dsid = $('#file_table').attr('data-dsid');
    showSelectionConfirmation({
        files: getCheckedFiles(true),
        header: 'Files selected for GDEX dataset '+dsid,
        message: "To transfer these files using the Globus data transfer service, select the button labeled 'Globus transfer' below. " +
                 "You will be redirected to the Globus web app where you will be prompted to select a target endpoint to receive the " +
                 "data transfer. Once you have defined a target endpoint, you will be redirected back to the GDEX website and your data " +
                 "transfer will be submitted.\n\n" +
                 "A Globus login is required to use this service.  You may sign into Globus with your preferred identity " +
                 "(e.g. ORCID, GlobusID, Google, or other).\n\n" +
                 "Contact datahelp@ucar.edu for further assistance",
        buttonText: 'Globus transfer',
        onConfirm: function(){ globusTransfer(dsid); }
    });
}
function sendConvertApp(dsid)
{
    var files = getCheckedFiles();
    var filenames = getListFromKey(files, 'filename');
    var email = get_user_email(true);
    var url = '/php/dsrqst.php';
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
        script_name = 'gdex-download.py';
        break;
    case 'csh':
        script = getCshScript(files);
        script_name = 'gdex-download.csh';
        break;
    case 'jupyter':
        script = getJupyterScript(files);
        script_name = 'gdex-download.ipynb';
        break;
    case 'filelist':
        script = getFilelistScript(files);
        script_name = 'gdex-filelist.txt';
        break;
    default:
        script = getPythonScript(files);
        script_name = 'gdex-download.py';
    }
        var blob = new Blob([script], {type: "text/plain;charset=utf-8"});
        saveBlob(blob, script_name);

    return script;
}
function getPythonScript(filelist)
{
    script = `#!/usr/bin/env python
""" 
Python script to download selected files from gdex.ucar.edu.
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
# c-shell script to download selected files from gdex.ucar.edu using Wget
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

function saveBlob(blob, fileName) {
/**
 * Save a text or binary blob to a temporary object URL
 * and trigger a download of the file.
 * 
 * Example usage:
 * - Create a Blob from some text data

  const textBlob = new Blob(["This is some text content."], { type: "text/plain" });
  saveBlob(textBlob, "myTextFile.txt");

 * - Create a Blob from binary data (e.g., an image)
 * - Assuming 'imageData' is a Uint8Array or similar

  const imageBlob = new Blob([imageData], { type: "image/png" });
  saveBlob(imageBlob, "myImage.png");
 */

// Create a temporary anchor element
  const a = document.createElement("a");
  document.body.appendChild(a); // Append to body to ensure it's in the DOM
  // Hide the anchor element
  a.style.display = "none";
  // Create a URL for the Blob object
  const url = window.URL.createObjectURL(blob);
  // Set the href to the Blob URL and the download attribute to the desired file name
  a.href = url;
  a.download = fileName;
  // Programmatically click the anchor to trigger the download
  a.click();
  // Revoke the object URL to free up memory
  window.URL.revokeObjectURL(url);
  // Remove the temporary anchor element from the DOM
  document.body.removeChild(a);
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
	if (curCheckbox.is(":checked") && !row.hasClass('d-none')) {
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
        if (!row.hasClass('d-none')) {
            curChecked.prop('checked', true);
        }
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
         var size = self.attr('data-size') || self.find('td.Size').attr('data-size');
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

/**
 * Checkboxes in a table, excluding those in rows hidden by the page filter
 */
function visibleCheckboxes(table) {
    return table.find('input[type=checkbox]').not(table.find('tr.d-none input[type=checkbox]'));
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
    visibleCheckboxes(table).each(function(){
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
   
   visibleCheckboxes(table).each(function(){
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

/**
 * Copies full URL or path (link) to clipboard and updates button text.
 * Button text resets after 2 seconds.
 * @param {HTMLElement} btn 
 * @param {string} link 
 */
function copyFullLink(btn, link, text='Copy Full URL') {
    navigator.clipboard.writeText(link);
    $(btn).removeClass('btn-primary').addClass('btn-success').html('<i class="fa-solid fa-check pe-1"></i> Copied!');
    setTimeout(() => {
      $(btn).removeClass('btn-success').addClass('btn-primary').html('<i class="fa-solid fa-copy pe-1"></i> '+text);
    }, 5000);
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
