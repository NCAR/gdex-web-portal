  /*
  This helper function ensures queries are inserted as the first query-param
  so that the search url is copy-pastable by the user
  */
  function customSearch(page=1) {
    //copy as a hidden field so we don't change the look of the page
    var page = $('<input>').attr({type: 'hidden', id: 'foo',
                                 name: 'page', value: page});

                                 //copy the current text query
    var input = $('#search-input').clone().attr('type','hidden');

    //check temporal range inputs and prepend them to the facet form
    //if they are not empty
    var start = $('#temporal_start_input').val();
    if (start.length > 0) {
      var start_input = $('#temporal_start_input').clone().attr('type','hidden');
      start_input.val(decodeURIComponent(start)+'--*');
      $('#facet-form').append(start_input);
    }
    var end = $('#temporal_end_input').val();
    if (end.length > 0) {
      var end_input = $('#temporal_end_input').clone().attr('type','hidden');
      end_input.val('*--'+decodeURIComponent(end));
      $('#facet-form').append(end_input);
    }

    // get all query parameters from the url
    var queryParams = new URLSearchParams(window.location.search);

    // iterate through each url query parameter and add it as a hidden input if not
    // included already or if it's not in #facet-form
    queryParams.forEach(function(value, key) {
      if ($('#facet-form').find('input[name="' + key + '"]').length === 0 &&
          key !== 'page' && key !== 'search_input' &&
          key !== 'temporal_start_input' && key !== 'temporal_end_input') {
        var hiddenInput = $('<input>').attr({
          type: 'hidden',
          name: key,
          value: value
        });
        $('#facet-form').append(hiddenInput);
      }
    });

    //prepend the page and text query to the facet form, then submit it
    $('#facet-form').prepend(page).prepend(input).submit();
  }

    $(function() {
       var dateFormat = "yy-mm-dd";
       var from = $( "#temporal_start_input" )
        .datepicker({
          changeMonth: true,
          changeYear: true,
          numberOfMonths: 1,
          dateFormat: dateFormat,
          showButtonPanel: true,
          yearRange: "c-100:c+10",
        })
        .on( "change", function() {
          to.datepicker( "option", "minDate", getDate( this ) );
        });

      var to = $( "#temporal_end_input" ).datepicker({
        changeMonth: true,
        changeYear: true,
        numberOfMonths: 1,
        dateFormat: dateFormat,
        showButtonPanel: true,
        yearRange: "c-100:c+10",
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

  $( function() {
    // Save text input values in session storage
    $('#temporal_start_input').on('input', function() {
      sessionStorage.setItem('temporal_start_input', $(this).val());
    });
    $('#temporal_end_input').on('input', function() {
      sessionStorage.setItem('temporal_end_input', $(this).val());
    });

    $('#facet-form').on('submit', function() {
      // Save the current values of the temporal inputs to session storage
      sessionStorage.setItem('temporal_start_input', $('#temporal_start_input').val());
      sessionStorage.setItem('temporal_end_input', $('#temporal_end_input').val());
    });

    // Retrieve from session storage on page load
    var start = sessionStorage.getItem('temporal_start_input');
    var end = sessionStorage.getItem('temporal_end_input');
    if (start) {
      $('#temporal_start_input').val(start);
    }
    if (end) {
      $('#temporal_end_input').val(end);
    }
  });

function clearFilters() 
{
  // Clear session storage
  sessionStorage.removeItem('temporal_start_input');
  sessionStorage.removeItem('temporal_end_input');

  // Clear the input fields
  $('#temporal_start_input').val('');
  $('#temporal_end_input').val('');

  // Uncheck all checkboxes in the facet form
  $('#facet-form input[type="checkbox"]').prop('checked', false);

  // Reset the search input
  $('#search-input').val('');

  // Reset the search query in the session
  sessionStorage.removeItem('search_input');

  // Submit the form to clear filters
  $('#facet-form').submit();
}

function clearTemporalRange() {
  // Clear the temporal range inputs
  $('#temporal_start_input').val('');
  $('#temporal_end_input').val('');

  // Remove the temporal range from the session storage
  sessionStorage.removeItem('temporal_start_input');
  sessionStorage.removeItem('temporal_end_input');

  // Submit the form to apply changes
  $('#facet-form').submit();
}

function clearBuckets(facetName) {
  // Clear all checkboxes in the facet container
  $('#facet-' + facetName + ' input[type="checkbox"]').prop('checked', false);
  $('#facet-form').submit();
}