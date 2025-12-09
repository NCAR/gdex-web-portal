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

       var from = $( "#startDate" )
        .datepicker({
          changeMonth: true,
          changeYear: true,
          numberOfMonths: 1,
          dateFormat: dateFormat,
          showButtonPanel: true,
          minDate: new Date(startDateString),
          maxDate: new Date(endDateString),
        })
        .on( "change", function() {
          to.datepicker( "option", "minDate", getDate( this ) );
        });

      var to = $( "#endDate" ).datepicker({
        changeMonth: true,
        changeYear: true,
        numberOfMonths: 1,
        dateFormat: dateFormat,
        showButtonPanel: true,
        minDate: new Date(startDateString),
        maxDate: new Date(endDateString),
      })
      .on( "change", function() {
        from.datepicker( "option", "maxDate", getDate( this ) );
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

  // Reset the datepickers' min and max dates
  $('#startDate').datepicker('option', 'minDate', new Date($('#minDate').val()));
  $('#startDate').datepicker('option', 'maxDate', new Date($('#maxDate').val()));
  $('#endDate').datepicker('option', 'minDate', new Date($('#minDate').val()));
  $('#endDate').datepicker('option', 'maxDate', new Date($('#maxDate').val()));
}

changed_selection = false;
function showChangedSelections() {
  if (!changed_selection) {
    changed_selection = true;
  }
}
