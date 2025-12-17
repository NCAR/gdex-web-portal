/**
 * jQuery datepicker setup
 */
    $(function() {
       var dateFormat = "yy-mm-dd";
       const startDateInput = $('#startDate');
       const endDateInput = $('#endDate');

       // Initialize datepickers with existing values if present
       startDateInput.datepicker("setDate", startDateInput.val() ? startDateInput.val() : null);
       endDateInput.datepicker("setDate", endDateInput.val() ? endDateInput.val() : null);

       const startDateString = $('#minDate').val();
       const endDateString = $('#maxDate').val();
       minDate = new Date(startDateString);
       maxDate = new Date(endDateString);
       startYear = minDate.getFullYear();
       endYear = maxDate.getFullYear(); 

       var from = $( "#startDate" )
        .datepicker({
          changeMonth: true,
          changeYear: true,
          numberOfMonths: 1,
          dateFormat: dateFormat,
          showButtonPanel: true,
          minDate: minDate,
          maxDate: maxDate,
          yearRange: startYear + ":" + endYear,
        })
        .on( "change", function() {
          to.datepicker( "option", "minDate", getDate( this ) );
          endYear = to.datepicker("option", "maxDate").getFullYear();
          to.datepicker("option", "yearRange", getDate( this ).getFullYear() + ":" + endYear);
        });

      var to = $( "#endDate" ).datepicker({
        changeMonth: true,
        changeYear: true,
        numberOfMonths: 1,
        dateFormat: dateFormat,
        showButtonPanel: true,
        minDate: minDate,
        maxDate: maxDate,
        yearRange: startYear + ":" + endYear,
      })
      .on( "change", function() {
        from.datepicker( "option", "maxDate", getDate( this ) );
        startYear = from.datepicker("option", "minDate").getFullYear();
        from.datepicker("option", "yearRange", startYear + ":" + getDate( this ).getFullYear());
      });

    function getDate( element ) {
      var date;
      try {
        date = $.datepicker.parseDate( dateFormat, element.value );
      } catch( error ) {
        date = null;
      }
      return date;
    }

  });

function clearTemporalRange() {
  // Clear the temporal range inputs
  $('#startDate').val('');
  $('#endDate').val('');

  // Reset the datepickers' min and max dates and year ranges
  $('#startDate').datepicker('option', 'minDate', new Date($('#minDate').val()));
  $('#startDate').datepicker('option', 'maxDate', new Date($('#maxDate').val()));
  $('#endDate').datepicker('option', 'minDate', new Date($('#minDate').val()));
  $('#endDate').datepicker('option', 'maxDate', new Date($('#maxDate').val()));
  const minDate = new Date($('#minDate').val());
  const maxDate = new Date($('#maxDate').val());
  const startYear = minDate.getFullYear();
  const endYear = maxDate.getFullYear();
  $('#startDate').datepicker('option', 'yearRange', startYear + ':' + endYear);
  $('#endDate').datepicker('option', 'yearRange', startYear + ':' + endYear);
}

changed_selection = false;
function showChangedSelections() {
  if (!changed_selection) {
    changed_selection = true;
  }
}

var head=document.getElementsByTagName('head').item(0);
var scr=document.createElement('script');
scr.setAttribute('type','text/javascript');
scr.setAttribute('src','/static/js/gdrawboxmap3.js');
scr.onload=initializeTheDrawBoxMap;
scr.onreadystatechange=initializeTheDrawBoxMap;
head.appendChild(scr);
