
$(document).ready(function() {
    // make all dataset page tabs inactive if in the subset request form view

    requestPathPattern = new RegExp('/datasets/d[0-9]{6}/request/');
    if (requestPathPattern.test(window.location.pathname)) {
        const listItems = $('#datasetTab li');
        $.each(listItems, function() {
        // for each li, get the a element and remove active class
        $(this).find('a').removeClass('active');
        $(this).find('a').attr('aria-selected', 'false');
        });

    }
});
