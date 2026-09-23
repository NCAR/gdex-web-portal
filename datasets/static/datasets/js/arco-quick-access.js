$(document).ready(function () {
    var dsid = $('#search_container').data('dsid');
    var PAGE_SIZE = 8;
    var _lastCode = null;

    function showLoadingCode() {
        if (_lastCode !== null) {
            const loading = _lastCode.replace(/filename = '.*?'/, "filename = 'loading...'");
            $('#quickstart').html(hljs.highlight(loading, { language: 'python' }).value);
        }
    }

    function update_quickstart_code(filename, engine, varname, extras, onHPC) {
        if (filename.endsWith('zarr')) {
            engine = 'zarr';
        }
        if (onHPC) {
            filename = filename.replace('https://data.gdex.ucar.edu/', '/glade/campaign/collections/gdex/data/');
        } else {
            filename = filename.replace('/glade/campaign/collections/gdex/data/', 'https://data.gdex.ucar.edu/');
        }
        _lastCode = `import xarray\nfilename = '${filename}'\nds = xarray.open_dataset(filename, engine='${engine}')\nds['${varname}'] # ${extras}`;
        $('#quickstart').html(hljs.highlight(_lastCode, { language: 'python' }).value);
    }

    function makeOptionDiv(value) {
        return $("<div>")
            .addClass("dropdown_option")
            .text(value)
            .on("click", function () {
                $("#searchBar").val(value);
                $("#dropdown").hide();
                $.getJSON('https://' + window.location.hostname + '/api/search_arco_vars/' + dsid + '/' + value, {}, function (data) {
                    update_quickstart_code(data.data[0][0], 'kerchunk', data.data[0][1], data.data[0][4], $('#onHPC').prop('checked'));
                });
            });
    }

    function renderOptions(filtered) {
        $("#dropdown").empty();
        if (filtered.data.length === 0) {
            $("#dropdown").hide();
            return;
        }
        $("#dropdown").show();
        const values = filtered.data.map(function (row) { return row[4]; });
        const visible = values.slice(0, PAGE_SIZE);
        const hidden = values.slice(PAGE_SIZE);
        $.each(visible, function (_, value) {
            makeOptionDiv(value).appendTo("#dropdown");
        });
        if (hidden.length > 0) {
            $("<div>")
                .addClass("dropdown_option text-muted")
                .css("font-style", "italic")
                .text(hidden.length + " more...")
                .appendTo("#dropdown")
                .on("click", function (e) {
                    e.stopPropagation();
                    $(this).remove();
                    $.each(hidden, function (_, value) {
                        makeOptionDiv(value).appendTo("#dropdown");
                    });
                });
        }
    }

    $.getJSON('https://' + window.location.hostname + '/api/search_arco_vars/' + dsid + '/' + dsid, {}, function (data) {
        if (data.data && data.data.length > 0) {
            update_quickstart_code(data.data[0][0], 'kerchunk', data.data[0][1], data.data[0][4], false);
        }
    });

    $('#onHPC').change(function () {
        var query = $('#searchBar').val();
        showLoadingCode();
        $.getJSON('https://' + window.location.hostname + '/api/search_arco_vars/' + dsid + '/' + query, {}, function (data) {
            update_quickstart_code(data.data[0][0], 'kerchunk', data.data[0][1], data.data[0][4], $('#onHPC').prop('checked'));
        });
    });

    $(".copy-btn").click(function () {
        var code = $('#quickstart').text();
        const btn = $(this);
        navigator.clipboard.writeText(code).then(() => {
            btn.addClass('copy-btn--copied').html('<i class="fa-solid fa-check pe-1"></i>Copied!');
            setTimeout(() => btn.removeClass('copy-btn--copied').html('<i class="fa-solid fa-copy pe-1"></i>Copy'), 1500);
        });
    });

    const searchInput = document.getElementById('searchBar');
    searchInput.addEventListener('input', (event) => {
        const query = event.target.value;

        $("#dropdown").html('<div class="dropdown_option text-muted">Loading...</div>').show();
        showLoadingCode();
        $.getJSON('https://' + window.location.hostname + '/api/search_arco_vars/' + dsid + '/' + query, {}, function (data) {
            update_quickstart_code(data.data[0][0], 'kerchunk', data.data[0][1], data.data[0][4], $('#onHPC').prop('checked'));
            renderOptions(data);
        })
            .fail(function () {
                console.error("Error fetching data");
                $("#dropdown").hide();
            });
    });

    $("#searchBar").on("focus", function () {
        if ($("#dropdown").children().length > 0) {
            $("#dropdown").show();
        }
    });

    $(document).on("click", function (e) {
        if (!$(e.target).closest("#search_container").length) {
            $("#dropdown").hide();
        }
    });
});
