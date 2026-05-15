document.addEventListener('DOMContentLoaded', function () {
    const btn = document.getElementById('exchange-filelist-btn');
    const selectAll = document.getElementById('exchange-select-all');

    if (!btn) return;

    function getChecked() {
        return Array.from(document.querySelectorAll('.exchange-file-cb:checked'));
    }

    function updateButton() {
        btn.disabled = getChecked().length === 0;
    }

    document.querySelectorAll('.exchange-file-cb').forEach(function (cb) {
        cb.addEventListener('change', function () {
            updateButton();
            if (selectAll && !this.checked) {
                selectAll.checked = false;
            }
        });
    });

    if (selectAll) {
        selectAll.addEventListener('change', function () {
            document.querySelectorAll('.exchange-file-cb').forEach(function (cb) {
                cb.checked = selectAll.checked;
            });
            updateButton();
        });
    }

    btn.addEventListener('click', function () {
        const urls = getChecked().map(function (cb) { return cb.dataset.url; });
        const escaped = urls.join('\n').replace(/&/g, '&amp;').replace(/</g, '&lt;');
        const html = '<div style="padding:8px">'
            + '<p class="mb-1"><strong>' + urls.length + ' file' + (urls.length !== 1 ? 's' : '') + ' selected:</strong></p>'
            + '<textarea id="exchange-filelist-output" style="width:100%;height:190px;font-family:monospace;font-size:0.82em;" readonly>'
            + escaped
            + '</textarea>'
            + '<button class="btn btn-sm btn-secondary mt-2" '
            + 'onclick="navigator.clipboard.writeText(document.getElementById(\'exchange-filelist-output\').value)">'
            + '<i class=\"fas fa-copy me-1\"></i>Copy to clipboard</button>'
            + '</div>';
        popModalWindowWithHTML(true, true, html);
    });
});
