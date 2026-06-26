/* ============================================================
   GDEX — Search Data Page JavaScript
   Loaded at the bottom of search.html via {% block extra_js %}
   Depends on: flatpickr (loaded via CDN before this file)
   ============================================================ */

(function () {
    var chips          = document.getElementById('gdex-active-filters');
    var resetBtn       = document.getElementById('gdex-reset-btn');
    var sidebarBody    = document.getElementById('gdex-sidebar-body');
    var sidebar        = document.querySelector('.gdex-filters-sidebar');
    var dateFromPicker, dateToPicker;

    /* ---------- group-based chip state ---------- */

    var groupSelections = {};
    var groupChipEls    = {};

    var GROUP_META = {
        'time_range':  { label: 'Time Range' },
        'date_range':  { label: 'Date Range' },
        'keyword':     { label: 'Keyword' },
        'variable':    { label: 'Variable' },
        'data_format': { label: 'Data Format' },
        'loc':         { label: 'Location' },
        'platform':    { label: 'Platform' },
        'spatial_res': { label: 'Spatial Resolution' },
        'time_res':    { label: 'Time Resolution' },
        'data_type':   { label: 'Data Type' },
    };

    function renderGroupChip(groupKey) {
        var values = groupSelections[groupKey];
        var meta   = GROUP_META[groupKey] || { label: groupKey };

        if (groupChipEls[groupKey]) {
            groupChipEls[groupKey].remove();
            delete groupChipEls[groupKey];
        }
        if (!values || values.length === 0) return;

        var chip = document.createElement('span');
        chip.className     = 'gdex-active-filter-chip';
        chip.dataset.group = groupKey;

        var grpSpan = document.createElement('span');
        grpSpan.className   = 'gdex-active-filter-chip__group';
        grpSpan.textContent = meta.label;

        var valSpan = document.createElement('span');
        valSpan.className   = 'gdex-active-filter-chip__value';
        valSpan.textContent = values.join(', ');

        var rb = document.createElement('button');
        rb.className = 'gdex-active-filter-chip__remove';
        rb.setAttribute('aria-label', 'Clear ' + meta.label);
        rb.textContent = '×';
        rb.addEventListener('click', function () { clearGroupChip(groupKey); });

        chip.appendChild(grpSpan);
        chip.appendChild(valSpan);
        chip.appendChild(rb);
        chips.appendChild(chip);
        groupChipEls[groupKey] = chip;
    }

    function clearGroupChip(groupKey) {
        groupSelections[groupKey] = [];

        document.querySelectorAll('input[name="' + groupKey + '"][type="checkbox"]').forEach(function (inp) {
            inp.checked = false;
        });
        document.querySelectorAll('input[data-filter-group="' + groupKey + '"]').forEach(function (inp) {
            if (inp.hasAttribute('data-filter-default')) inp.checked = true;
            else if (inp.type === 'checkbox') inp.checked = false;
        });

        if (groupKey === 'loc' && window._resetLocationSelects) window._resetLocationSelects();
        if (groupKey === 'date_range') {
            if (dateFromPicker) dateFromPicker.clear();
            if (dateToPicker)   dateToPicker.clear();
        }

        renderGroupChip(groupKey);
        scheduleNavigation();
    }

    /* ---------- debounced navigation ---------- */

    var navTimer = null;

    function scheduleNavigation() {
        clearTimeout(navTimer);
        navTimer = setTimeout(navigateWithFilters, 350);
    }

    function navigateWithFilters() {
        var params = new URLSearchParams();

        // Preserve the current search query from the hero input
        var heroInput = document.querySelector('.gdex-find-data-hero__input');
        var q = heroInput ? heroInput.value.trim() : '';
        if (q) params.set('q', q);

        // Collect all checked filter checkboxes
        var filterNames = ['time_range', 'keyword', 'variable', 'data_format',
                           'platform', 'spatial_res', 'time_res', 'data_type'];
        filterNames.forEach(function (name) {
            document.querySelectorAll('input[name="' + name + '"]:checked').forEach(function (cb) {
                params.append(name, cb.dataset.filterLabel || cb.value);
            });
        });

        // Custom date range
        if (dateFromPicker && dateFromPicker.input.value)
            params.set('date_from', dateFromPicker.input.value);
        if (dateToPicker && dateToPicker.input.value)
            params.set('date_to', dateToPicker.input.value);

        // Location (from chip state)
        if (groupSelections['loc'] && groupSelections['loc'].length)
            params.set('loc', groupSelections['loc'][0]);

        window.location.href = window.location.pathname +
            (params.toString() ? '?' + params.toString() : '');
    }

    /* ---------- restore state from URL on page load ---------- */

    function initFromURL() {
        var params = new URLSearchParams(window.location.search);

        var filterNames = ['time_range', 'keyword', 'variable', 'data_format',
                           'platform', 'spatial_res', 'time_res', 'data_type'];

        filterNames.forEach(function (name) {
            var values = params.getAll(name);
            if (!values.length) return;

            if (!groupSelections[name]) groupSelections[name] = [];

            values.forEach(function (val) {
                var cb = document.querySelector(
                    'input[name="' + name + '"][data-filter-label="' + val + '"]'
                );
                if (cb) {
                    cb.checked = true;
                    if (groupSelections[name].indexOf(val) === -1)
                        groupSelections[name].push(val);

                    // Expand the filter group that has an active selection
                    var group = cb.closest('.gdex-filter-group');
                    if (group) group.classList.remove('gdex-filter-group--collapsed');
                }
            });

            renderGroupChip(name);
        });

        // Restore custom date range
        var dateFrom = params.get('date_from');
        var dateTo   = params.get('date_to');
        if (dateFrom && dateFromPicker) dateFromPicker.setDate(dateFrom, true);
        if (dateTo   && dateToPicker)   dateToPicker.setDate(dateTo, true);
        if (dateFrom || dateTo) {
            groupSelections['date_range'] = [
                (dateFrom || '') + (dateFrom && dateTo ? ' → ' : '') + (dateTo || '')
            ];
            renderGroupChip('date_range');
            // Open the Time Range group
            var trGroup = document.querySelector('input[name="time_range"]');
            if (trGroup) {
                var g = trGroup.closest('.gdex-filter-group');
                if (g) g.classList.remove('gdex-filter-group--collapsed');
            }
        }

        // Restore location chip (select restore is complex; just show chip)
        var loc = params.get('loc');
        if (loc) {
            groupSelections['loc'] = [loc];
            renderGroupChip('loc');
        }
    }

    /* ---------- filter change ---------- */

    function onFilterChange(input) {
        var label     = input.dataset.filterLabel;
        var groupKey  = input.dataset.filterGroup || input.name || '';
        var isDefault = input.hasAttribute('data-filter-default');
        if (!label || !groupKey) return;

        if (!groupSelections[groupKey]) groupSelections[groupKey] = [];

        if (input.type === 'checkbox') {
            if (input.checked) {
                if (groupKey === 'time_range') {
                    document.querySelectorAll('input[name="time_range"][type="checkbox"]').forEach(function (cb) {
                        if (cb !== input) cb.checked = false;
                    });
                    if (dateFromPicker) dateFromPicker.clear();
                    if (dateToPicker)   dateToPicker.clear();
                    groupSelections['date_range'] = [];
                    renderGroupChip('date_range');
                    groupSelections[groupKey] = [label];
                } else {
                    if (groupSelections[groupKey].indexOf(label) === -1)
                        groupSelections[groupKey].push(label);
                }
            } else {
                groupSelections[groupKey] = groupSelections[groupKey].filter(function (v) {
                    return v !== label;
                });
            }
        } else if (input.type === 'radio') {
            groupSelections[groupKey] = isDefault ? [] : [label];
        }

        renderGroupChip(groupKey);
        scheduleNavigation();
    }

    document.querySelectorAll('input[data-filter-label]').forEach(function (inp) {
        inp.addEventListener('change', function () { onFilterChange(this); });
    });

    /* ---------- date range chip ---------- */

    function refreshDateChip() {
        var f = dateFromPicker ? dateFromPicker.input.value : '';
        var t = dateToPicker   ? dateToPicker.input.value   : '';
        groupSelections['date_range'] = (f && t) ? [f + ' → ' + t] : [];
        renderGroupChip('date_range');

        if (f || t) {
            document.querySelectorAll('input[name="time_range"][type="checkbox"]').forEach(function (cb) {
                cb.checked = false;
            });
            groupSelections['time_range'] = [];
            renderGroupChip('time_range');
        }

        scheduleNavigation();
    }

    /* ---------- flatpickr (only init if the library is loaded) ---------- */

    if (typeof flatpickr !== 'undefined') {
        dateFromPicker = flatpickr('#date-from', {
            dateFormat: 'Y-m-d',
            allowInput: true,
            onChange: function (sel, str) {
                if (dateToPicker) dateToPicker.set('minDate', str || null);
                refreshDateChip();
            }
        });
        dateToPicker = flatpickr('#date-to', {
            dateFormat: 'Y-m-d',
            allowInput: true,
            onChange: function (sel, str) {
                if (dateFromPicker) dateFromPicker.set('maxDate', str || null);
                refreshDateChip();
            }
        });
    }

    /* ---------- restore URL state (after flatpickr is ready) ---------- */

    initFromURL();

    /* ---------- reset — navigate to clean URL ---------- */

    if (resetBtn) {
        resetBtn.addEventListener('click', function () {
            window.location.href = window.location.pathname;
        });
    }

    /* ---------- hero search: soft refresh on clear (preserves filters) ---------- */

    var heroInput = document.querySelector('.gdex-find-data-hero__input');
    if (heroInput) {
        heroInput.addEventListener('input', function () {
            if (this.value === '') {
                var params = new URLSearchParams(window.location.search);
                params.delete('q');
                var newUrl = window.location.pathname +
                    (params.toString() ? '?' + params.toString() : '');
                fetch(newUrl)
                    .then(function (r) { return r.text(); })
                    .then(function (html) {
                        var doc      = new DOMParser().parseFromString(html, 'text/html');
                        var newList  = doc.getElementById('gdex-results-list');
                        var newCount = doc.querySelector('.gdex-results-count');
                        var curList  = document.getElementById('gdex-results-list');
                        var curCount = document.querySelector('.gdex-results-count');
                        if (newList  && curList)  curList.innerHTML  = newList.innerHTML;
                        if (newCount && curCount) curCount.innerHTML = newCount.innerHTML;
                        history.pushState({}, '', newUrl);
                    });
            }
        });
    }

    /* ---------- sidebar scroll fade ---------- */

    function checkScroll() {
        if (!sidebarBody || !sidebar) return;
        var atEnd = sidebarBody.scrollTop + sidebarBody.clientHeight >= sidebarBody.scrollHeight - 8;
        sidebar.classList.toggle('gdex-filters-sidebar--at-bottom', atEnd);
    }
    if (sidebarBody) {
        sidebarBody.addEventListener('scroll', checkScroll);
        checkScroll();
    }

    /* ---------- collapsible groups ---------- */

    document.querySelectorAll('[data-gdex-toggle]').forEach(function (h) {
        h.addEventListener('click', function () {
            this.closest('.gdex-filter-group').classList.toggle('gdex-filter-group--collapsed');
            checkScroll();
        });
    });

    /* ---------- location cascade dropdowns ---------- */

    (function () {
        var dataEl = document.getElementById('gdex-location-data');
        if (!dataEl) return;

        var buckets;
        try { buckets = JSON.parse(dataEl.textContent); } catch (e) { return; }

        // Build tree from GCMD strings: "CATEGORY > CONTINENT > COUNTRY > STATE"
        // parts[0]=GCMD category, parts[1]=continent/region, parts[2]=country, parts[3]=state
        var tree = {};
        var continentOrder = [];

        buckets.forEach(function (b) {
            var parts = b.value.split('>').map(function (p) { return p.trim(); });
            var continent = parts.length > 1 ? parts[1] : parts[0];
            var country   = parts.length > 2 ? parts[2] : null;
            var state     = parts.length > 3 ? parts[3] : null;

            if (!tree[continent]) {
                tree[continent] = { bucket: null, countries: {}, countryOrder: [] };
                continentOrder.push(continent);
            }
            if (country) {
                if (!tree[continent].countries[country]) {
                    tree[continent].countries[country] = { bucket: null, states: {}, stateOrder: [] };
                    tree[continent].countryOrder.push(country);
                }
                if (state) {
                    tree[continent].countries[country].states[state] = b;
                    tree[continent].countries[country].stateOrder.push(state);
                } else {
                    tree[continent].countries[country].bucket = b;
                }
            } else {
                tree[continent].bucket = b;
            }
        });

        var contSel    = document.getElementById('loc-continent');
        var countrySel = document.getElementById('loc-country');
        var stateSel   = document.getElementById('loc-state');
        var stateRow   = document.getElementById('loc-state-row');
        var hiddenDiv  = document.getElementById('gdex-location-hidden');
        if (!contSel || !countrySel || !stateSel || !hiddenDiv) return;

        function toTitleCase(str) {
            return str.toLowerCase().replace(/(?:^|\s|-)\S/g, function (c) { return c.toUpperCase(); });
        }

        function makeOption(label) {
            var opt = document.createElement('option');
            opt.value = label;
            opt.textContent = toTitleCase(label);
            return opt;
        }

        function setHiddenInput(bucket) {
            hiddenDiv.innerHTML = '';
            if (!bucket) return;
            var inp = document.createElement('input');
            inp.type = 'checkbox';
            inp.name = bucket.name;
            inp.value = bucket.value;
            inp.checked = true;
            inp.autocomplete = 'off';
            inp.style.display = 'none';
            hiddenDiv.appendChild(inp);
        }

        function resetState() {
            stateSel.innerHTML = '<option value="">Select state…</option>';
            stateSel.disabled = true;
            stateRow.style.display = 'none';
        }

        function resetCountry() {
            countrySel.innerHTML = '<option value="">Select country…</option>';
            countrySel.disabled = true;
            resetState();
        }

        // Populate continent/region select from bucket data
        continentOrder.forEach(function (label) {
            contSel.appendChild(makeOption(label));
        });

        contSel.addEventListener('change', function () {
            var cv = this.value;
            resetCountry();
            hiddenDiv.innerHTML = '';
            if (!cv) { customSearch(1); return; }

            var node = tree[cv];
            if (!node) return;

            if (node.countryOrder.length > 0) {
                node.countryOrder.forEach(function (label) {
                    countrySel.appendChild(makeOption(label));
                });
                countrySel.disabled = false;
                // Wait for country selection before firing search
            } else {
                // No children (e.g. "ARCTIC") — filter immediately on this bucket
                setHiddenInput(node.bucket);
                customSearch(1);
            }
        });

        countrySel.addEventListener('change', function () {
            var cv = contSel.value;
            var ctv = this.value;
            resetState();
            hiddenDiv.innerHTML = '';
            if (!ctv) { customSearch(1); return; }

            var countryNode = tree[cv] && tree[cv].countries[ctv];
            if (!countryNode) return;

            if (countryNode.stateOrder.length > 0) {
                countryNode.stateOrder.forEach(function (label) {
                    stateSel.appendChild(makeOption(label));
                });
                stateSel.disabled = false;
                stateRow.style.display = '';
            }
            // Filter on the country bucket (or continent bucket as fallback)
            setHiddenInput(countryNode.bucket || (tree[cv] && tree[cv].bucket));
            customSearch(1);
        });

        stateSel.addEventListener('change', function () {
            var cv  = contSel.value;
            var ctv = countrySel.value;
            var sv  = this.value;
            hiddenDiv.innerHTML = '';

            if (!sv) {
                // Reverted to country level
                var countryNode = tree[cv] && tree[cv].countries[ctv];
                setHiddenInput(countryNode && countryNode.bucket);
            } else {
                var stateBucket = tree[cv] && tree[cv].countries[ctv] &&
                                  tree[cv].countries[ctv].states[sv];
                setHiddenInput(stateBucket);
            }
            customSearch(1);
        });

        // Pre-select dropdowns if a location filter is already active on load
        var checkedBucket = null;
        for (var i = 0; i < buckets.length; i++) {
            if (buckets[i].checked) { checkedBucket = buckets[i]; break; }
        }
        if (checkedBucket) {
            var pp = checkedBucket.value.split('>').map(function (p) { return p.trim(); });
            var preContinent = pp.length > 1 ? pp[1] : pp[0];
            var preCountry   = pp.length > 2 ? pp[2] : null;
            var preState     = pp.length > 3 ? pp[3] : null;

            contSel.value = preContinent;

            if (preCountry && tree[preContinent]) {
                tree[preContinent].countryOrder.forEach(function (label) {
                    countrySel.appendChild(makeOption(label));
                });
                countrySel.disabled = false;
                countrySel.value = preCountry;

                if (preState && tree[preContinent].countries[preCountry]) {
                    tree[preContinent].countries[preCountry].stateOrder.forEach(function (label) {
                        stateSel.appendChild(makeOption(label));
                    });
                    stateSel.disabled = false;
                    stateRow.style.display = '';
                    stateSel.value = preState;
                }
            }
            setHiddenInput(checkedBucket);
        }

        // Allow external code (clear-all chip) to reset the selects
        window._resetLocationSelects = function () {
            contSel.value = '';
            resetCountry();
            hiddenDiv.innerHTML = '';
        };
    }());

    /* ---------- filter search + see more ---------- */

    (function () {
        var LIMIT = 5;

        document.querySelectorAll('.gdex-filter-group').forEach(function (group) {
            var optionsEl  = group.querySelector('.gdex-filter-options');
            var seeMoreBtn = group.querySelector('.gdex-filter-see-more');
            var rawInput   = group.querySelector('.gdex-filter-search-input');
            if (!optionsEl) return;

            var labels   = Array.from(optionsEl.querySelectorAll('label'));
            var expanded = false;
            var overflow = labels.length - LIMIT;

            var searchInput = null;
            var clearBtn    = null;
            if (rawInput) {
                var wrapper = document.createElement('div');
                wrapper.className = 'gdex-filter-search-wrapper';
                rawInput.parentNode.insertBefore(wrapper, rawInput);
                wrapper.appendChild(rawInput);
                clearBtn = document.createElement('button');
                clearBtn.type = 'button';
                clearBtn.className = 'gdex-filter-search-clear';
                clearBtn.innerHTML = '&times;';
                clearBtn.setAttribute('aria-label', 'Clear search');
                wrapper.appendChild(clearBtn);
                searchInput = rawInput;
            }

            if (seeMoreBtn) {
                if (overflow <= 0) {
                    seeMoreBtn.style.display = 'none';
                } else {
                    labels.slice(LIMIT).forEach(function (lbl) {
                        lbl.classList.add('gdex-filter-option--overflow');
                    });
                    seeMoreBtn.textContent = 'see ' + overflow + ' more…';

                    seeMoreBtn.addEventListener('click', function () {
                        expanded = !expanded;
                        labels.forEach(function (lbl, i) {
                            if (i >= LIMIT) {
                                if (expanded) {
                                    lbl.classList.remove('gdex-filter-option--overflow');
                                } else if (!lbl.classList.contains('gdex-filter-option--search-hidden')) {
                                    lbl.classList.add('gdex-filter-option--overflow');
                                }
                            }
                        });
                        seeMoreBtn.textContent = expanded ? 'see less' : 'see ' + overflow + ' more…';
                        checkScroll();
                    });
                }
            }

            if (!searchInput) return;

            var noResult = document.createElement('p');
            noResult.className = 'gdex-filter-no-results';
            noResult.textContent = 'No matches found';
            noResult.hidden = true;
            optionsEl.after(noResult);

            function applySearch(q) {
                var anyVisible = false;

                labels.forEach(function (lbl, i) {
                    var firstSpan = lbl.querySelector('span');
                    var text = (firstSpan ? firstSpan.textContent : lbl.textContent).trim().toLowerCase();
                    var matches = !q || text.indexOf(q) !== -1;

                    lbl.classList.toggle('gdex-filter-option--search-hidden', !matches);

                    if (q) {
                        if (matches) lbl.classList.remove('gdex-filter-option--overflow');
                    } else {
                        if (!expanded && seeMoreBtn && overflow > 0 && i >= LIMIT)
                            lbl.classList.add('gdex-filter-option--overflow');
                    }

                    if (matches) anyVisible = true;
                });

                noResult.hidden = !q || anyVisible;
                if (seeMoreBtn && overflow > 0) seeMoreBtn.style.display = q ? 'none' : '';
                checkScroll();
            }

            searchInput.addEventListener('input', function () {
                var q = this.value.trim().toLowerCase();
                var w = this.closest('.gdex-filter-search-wrapper');
                if (w) w.classList.toggle('gdex-filter-search-wrapper--active', q.length > 0);
                applySearch(q);
            });

            searchInput.addEventListener('keydown', function (e) {
                if (e.key === 'Enter') e.preventDefault();
            });

            clearBtn.addEventListener('click', function () {
                searchInput.value = '';
                searchInput.dispatchEvent(new Event('input'));
                searchInput.focus();
            });
        });
    }());

    /* ---------- copy DOI ---------- */

    document.querySelectorAll('.gdex-doi-copy').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var self = this;
            var icon = self.querySelector('i');
            if (!navigator.clipboard) return;
            navigator.clipboard.writeText(self.dataset.doi).then(function () {
                icon.className = 'fas fa-check';
                self.classList.add('gdex-doi-copy--copied');
                self.title = 'Copied!';
                setTimeout(function () {
                    icon.className = 'fas fa-copy';
                    self.classList.remove('gdex-doi-copy--copied');
                    self.title = 'Copy DOI';
                }, 2000);
            });
        });
    });

    /* ---------- dataset summary popover ---------- */

    (function () {
        var pop = document.createElement('div');
        pop.className = 'gdex-summary-popover';
        pop.setAttribute('role', 'tooltip');
        document.body.appendChild(pop);

        function show(anchor) {
            pop.innerHTML = '';
            var lbl = document.createElement('p');
            lbl.className   = 'gdex-summary-popover__label';
            lbl.textContent = 'Dataset Summary';
            var p = document.createElement('p');
            p.className   = 'gdex-summary-popover__text';
            p.textContent = anchor.dataset.summary || '';
            var hint = document.createElement('span');
            hint.className = 'gdex-summary-popover__hint';
            hint.innerHTML = 'Click <strong>Description</strong> for the full dataset page';
            pop.appendChild(lbl);
            pop.appendChild(p);
            pop.appendChild(hint);

            var rect   = anchor.getBoundingClientRect();
            var maxW   = Math.min(420, window.innerWidth - 32);
            var left   = Math.max(16, Math.min(rect.left, window.innerWidth - maxW - 16));
            pop.style.maxWidth = maxW + 'px';
            pop.style.left     = left + 'px';
            pop.style.top      = '-9999px';

            var popH       = pop.offsetHeight;
            var spaceBelow = window.innerHeight - rect.bottom - 12;
            pop.style.top  = (spaceBelow >= popH || spaceBelow >= rect.top - 12)
                ? (rect.bottom + 8) + 'px'
                : (rect.top - popH - 8) + 'px';

            pop.classList.add('gdex-summary-popover--visible');
        }

        function hide() { pop.classList.remove('gdex-summary-popover--visible'); }

        document.querySelectorAll('[data-summary]').forEach(function (el) {
            el.addEventListener('mouseenter', function () { show(this); });
            el.addEventListener('mouseleave', hide);
            el.addEventListener('focus',      function () { show(this); });
            el.addEventListener('blur',       hide);
        });

        pop.addEventListener('mouseleave', hide);
    }());


}());
