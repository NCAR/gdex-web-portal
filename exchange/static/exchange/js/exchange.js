document.addEventListener('DOMContentLoaded', function () {

    // --- Get Filelist button ---

    const btn = document.getElementById('exchange-filelist-btn');
    const selectAll = document.getElementById('exchange-select-all');

    if (btn) {
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
    }

    // --- Filter / search ---

    const searchInput = document.getElementById('exchange-search');
    if (!searchInput) return;

    const tbody = document.querySelector('.exchange-table tbody');
    if (!tbody) return;

    // Record original row order so we can restore it on clear
    const originalOrder = Array.from(tbody.querySelectorAll('tr'));

    function dirsFirst(rows) {
        return rows.slice().sort(function (a, b) {
            const aDir = a.dataset.isDir === 'true';
            const bDir = b.dataset.isDir === 'true';
            if (aDir !== bDir) return aDir ? -1 : 1;
            return (a.dataset.name || '').localeCompare(b.dataset.name || '');
        });
    }

    searchInput.addEventListener('input', function () {
        const query = this.value.toLowerCase().trim();
        const rows = Array.from(tbody.querySelectorAll('tr'));

        if (!query) {
            // Restore server-rendered order (already dirs-first) and remove dimming
            originalOrder.forEach(function (row) {
                row.classList.remove('exchange-row-dim');
                tbody.appendChild(row);
            });
            return;
        }

        const matches = [];
        const nonMatches = [];

        rows.forEach(function (row) {
            // Match against the name data attribute set on each row
            const text = row.dataset.name || '';
            if (text.includes(query)) {
                row.classList.remove('exchange-row-dim');
                matches.push(row);
            } else {
                row.classList.add('exchange-row-dim');
                nonMatches.push(row);
            }
        });

        // Within each group keep dirs first, then append non-matches after matches
        dirsFirst(matches).concat(dirsFirst(nonMatches)).forEach(function (row) {
            tbody.appendChild(row);
        });
    });
});
