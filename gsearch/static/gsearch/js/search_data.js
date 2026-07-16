/* ============================================================
   GDEX — Search Data Page JavaScript
   Loaded at the bottom of search.html via {% block extra_js %}
   Depends on: flatpickr (loaded via CDN before this file)
   ============================================================ */

(function () {
    var chips          = document.getElementById('gdex-active-filters');
    var resetBtn       = document.getElementById('gdex-reset-btn');
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

    /* ---------- collapsible groups ---------- */

    document.querySelectorAll('[data-gdex-toggle]').forEach(function (h) {
        h.addEventListener('click', function () {
            var group = this.closest('.gdex-filter-group');
            group.classList.toggle('gdex-filter-group--collapsed');
            if (group.classList.contains('gdex-filter-group--collapsed') && group._gdexResetSeeMore) {
                group._gdexResetSeeMore();
            }
        });
    });

    /* ---------- location cascade dropdowns ---------- */

    (function () {
        var dataEl = document.getElementById('gdex-location-data');
        if (!dataEl) return;
        var buckets;
        try { buckets = JSON.parse(dataEl.textContent); } catch (e) { return; }

        /* ── Geographic lookup tables ───────────────────────────────── */

        var US_STATES = {};
        ['ALABAMA','ALASKA','ARIZONA','ARKANSAS','CALIFORNIA','COLORADO','CONNECTICUT',
         'DELAWARE','FLORIDA','GEORGIA','HAWAII','IDAHO','ILLINOIS','INDIANA','IOWA',
         'KANSAS','KENTUCKY','LOUISIANA','MAINE','MARYLAND','MASSACHUSETTS','MICHIGAN',
         'MINNESOTA','MISSISSIPPI','MISSOURI','MONTANA','NEBRASKA','NEVADA',
         'NEW HAMPSHIRE','NEW JERSEY','NEW MEXICO','NEW YORK','NORTH CAROLINA',
         'NORTH DAKOTA','OHIO','OKLAHOMA','OREGON','PENNSYLVANIA','RHODE ISLAND',
         'SOUTH CAROLINA','SOUTH DAKOTA','TENNESSEE','TEXAS','UTAH','VERMONT',
         'VIRGINIA','WASHINGTON','WEST VIRGINIA','WISCONSIN','WYOMING',
         'DISTRICT OF COLUMBIA'].forEach(function (s) { US_STATES[s] = true; });

        var CA_PROVS = {};
        ['ALBERTA','BRITISH COLUMBIA','MANITOBA','NEW BRUNSWICK',
         'NEWFOUNDLAND AND LABRADOR','NORTHWEST TERRITORIES','NOVA SCOTIA','NUNAVUT',
         'ONTARIO','PRINCE EDWARD ISLAND','QUEBEC','SASKATCHEWAN','YUKON']
            .forEach(function (p) { CA_PROVS[p] = true; });

        var COUNTRY_CONT = {
            'CANADA':'North America','MEXICO':'North America','GREENLAND':'North America',
            'CUBA':'North America','PUERTO RICO':'North America','BERMUDA':'North America',
            'BELIZE':'North America','COSTA RICA':'North America','EL SALVADOR':'North America',
            'GUATEMALA':'North America','HONDURAS':'North America','NICARAGUA':'North America',
            'PANAMA':'North America','HAITI':'North America','DOMINICAN REPUBLIC':'North America',
            'JAMAICA':'North America','TRINIDAD AND TOBAGO':'North America',
            'BRAZIL':'South America','ARGENTINA':'South America','CHILE':'South America',
            'COLOMBIA':'South America','PERU':'South America','VENEZUELA':'South America',
            'ECUADOR':'South America','BOLIVIA':'South America','PARAGUAY':'South America',
            'URUGUAY':'South America','GUYANA':'South America','SURINAME':'South America',
            'UNITED KINGDOM':'Europe','FRANCE':'Europe','GERMANY':'Europe','ITALY':'Europe',
            'SPAIN':'Europe','PORTUGAL':'Europe','NETHERLANDS':'Europe','BELGIUM':'Europe',
            'SWITZERLAND':'Europe','AUSTRIA':'Europe','SWEDEN':'Europe','NORWAY':'Europe',
            'DENMARK':'Europe','FINLAND':'Europe','IRELAND':'Europe','GREECE':'Europe',
            'POLAND':'Europe','CZECH REPUBLIC':'Europe','SLOVAKIA':'Europe',
            'HUNGARY':'Europe','ROMANIA':'Europe','BULGARIA':'Europe','CROATIA':'Europe',
            'UKRAINE':'Europe','RUSSIA':'Europe',
            'CHINA':'Asia','JAPAN':'Asia','INDIA':'Asia','SOUTH KOREA':'Asia',
            'NORTH KOREA':'Asia','TAIWAN':'Asia','INDONESIA':'Asia','MALAYSIA':'Asia',
            'PHILIPPINES':'Asia','THAILAND':'Asia','VIETNAM':'Asia','CAMBODIA':'Asia',
            'MYANMAR':'Asia','LAOS':'Asia','SINGAPORE':'Asia','BANGLADESH':'Asia',
            'SRI LANKA':'Asia','NEPAL':'Asia','PAKISTAN':'Asia','AFGHANISTAN':'Asia',
            'IRAN':'Asia','IRAQ':'Asia','SAUDI ARABIA':'Asia','TURKEY':'Asia',
            'SYRIA':'Asia','JORDAN':'Asia','ISRAEL':'Asia','LEBANON':'Asia',
            'OMAN':'Asia','YEMEN':'Asia','KUWAIT':'Asia',
            'UNITED ARAB EMIRATES':'Asia','UAE':'Asia','MONGOLIA':'Asia',
            'KAZAKHSTAN':'Asia','UZBEKISTAN':'Asia','TAJIKISTAN':'Asia',
            'KYRGYZSTAN':'Asia','TURKMENISTAN':'Asia',
            'NIGERIA':'Africa','ETHIOPIA':'Africa','EGYPT':'Africa',
            'SOUTH AFRICA':'Africa','KENYA':'Africa','GHANA':'Africa',
            'TANZANIA':'Africa','ALGERIA':'Africa','ANGOLA':'Africa',
            'MOZAMBIQUE':'Africa','CAMEROON':'Africa','NIGER':'Africa',
            'MALI':'Africa','SENEGAL':'Africa','CHAD':'Africa','SOMALIA':'Africa',
            'RWANDA':'Africa','ZAMBIA':'Africa','ZIMBABWE':'Africa',
            'MOROCCO':'Africa','TUNISIA':'Africa','LIBYA':'Africa','SUDAN':'Africa',
            'SOUTH SUDAN':'Africa',
            'AUSTRALIA':'Oceania','NEW ZEALAND':'Oceania',
            'PAPUA NEW GUINEA':'Oceania','FIJI':'Oceania'
        };

        var GCMD_TOP = { 'CONTINENT':true, 'OCEAN':true, 'GEOGRAPHIC REGION':true,
                         'VERTICAL LOCATION':true, 'WATERSHED':true };

        var CONT_ORDER = ['North America','South America','Europe','Asia',
                          'Africa','Oceania','Polar Regions','Ocean Basins'];

        /* ── Classify a bucket value into {continent, country, state} ── */

        function toTitle(str) {
            if (!str) return str;
            return str.toLowerCase()
                .replace(/(?:^|[\s\-\/])\S/g, function (c) { return c.toUpperCase(); });
        }

        function classifyBucket(value) {
            var up = value.toUpperCase().trim();

            // Full GCMD hierarchical path (contains ">")
            if (up.indexOf('>') !== -1) {
                var parts = up.split('>').map(function (p) { return p.trim(); });
                var si = GCMD_TOP[parts[0]] ? 1 : 0;
                var cont = parts[si] || 'Other';
                if (cont === 'OCEAN' || /\bOCEAN\b/.test(cont)) cont = 'Ocean Basins';
                else if (cont === 'GEOGRAPHIC REGION') {
                    cont = (parts[si + 1] && /POLAR|ARCTIC|ANTARCT/.test(parts[si + 1]))
                        ? 'Polar Regions' : (parts[si + 1] ? toTitle(parts[si + 1]) : 'Other');
                    si++;
                }
                else cont = toTitle(cont);
                return {
                    continent: cont,
                    country:   parts.length > si + 1 ? toTitle(parts[si + 1]) : null,
                    state:     parts.length > si + 2 ? toTitle(parts[si + 2]) : null,
                };
            }

            // Flat value — classify by lookup tables
            if (US_STATES[up]) return { continent: 'North America', country: 'United States', state: toTitle(value) };
            if (CA_PROVS[up])  return { continent: 'North America', country: 'Canada',        state: toTitle(value) };

            if (/\bARCTIC\b|\bANTARCT/.test(up))
                return { continent: 'Polar Regions', country: toTitle(value), state: null };

            if (/\bOCEAN\b|\bSEA\b|\bGULF OF\b|\bBAY OF\b/.test(up))
                return { continent: 'Ocean Basins', country: toTitle(value), state: null };

            var knownCont = COUNTRY_CONT[up];
            if (knownCont) return { continent: knownCont, country: toTitle(value), state: null };

            // Default — show as a standalone entry in the continent dropdown
            return { continent: toTitle(value), country: null, state: null };
        }

        /* ── Build hierarchy from Globus buckets ─────────────────────── */

        var continentMap = {};
        var continentOrder = [];

        buckets.forEach(function (b) {
            var cls  = classifyBucket(b.value);
            var cont = cls.continent;

            if (!continentMap[cont]) {
                continentMap[cont] = { countryMap: {}, countryOrder: [], buckets: [] };
                continentOrder.push(cont);
            }

            if (cls.country) {
                var ctry = cls.country;
                if (!continentMap[cont].countryMap[ctry]) {
                    continentMap[cont].countryMap[ctry] = { stateMap: {}, stateOrder: [], buckets: [] };
                    continentMap[cont].countryOrder.push(ctry);
                }
                if (cls.state) {
                    var st = cls.state;
                    if (!continentMap[cont].countryMap[ctry].stateMap[st]) {
                        continentMap[cont].countryMap[ctry].stateMap[st] = [];
                        continentMap[cont].countryMap[ctry].stateOrder.push(st);
                    }
                    continentMap[cont].countryMap[ctry].stateMap[st].push(b);
                } else {
                    continentMap[cont].countryMap[ctry].buckets.push(b);
                }
            } else {
                continentMap[cont].buckets.push(b);
            }
        });

        // Sort continents in preferred order; unknowns alphabetically after
        continentOrder.sort(function (a, b) {
            var ai = CONT_ORDER.indexOf(a), bi = CONT_ORDER.indexOf(b);
            if (ai === -1 && bi === -1) return a.localeCompare(b);
            return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
        });

        /* ── DOM refs ─────────────────────────────────────────────────── */

        var contSel    = document.getElementById('loc-continent');
        var countrySel = document.getElementById('loc-country');
        var stateSel   = document.getElementById('loc-state');
        var stateRow   = document.getElementById('loc-state-row');
        var hiddenDiv  = document.getElementById('gdex-location-hidden');
        if (!contSel || !countrySel || !stateSel || !hiddenDiv) return;

        function makeOpt(label) {
            var o = document.createElement('option');
            o.value = o.textContent = label;
            return o;
        }

        // Collect only the Globus buckets that directly match the selected level
        function getBuckets(cont, ctry, st) {
            var node = continentMap[cont];
            if (!node) return [];
            if (!ctry) return node.buckets;
            var cNode = node.countryMap[ctry];
            if (!cNode) return [];
            if (!st) return cNode.buckets; // only the direct country-level bucket(s)
            return cNode.stateMap[st] || [];
        }

        function setHiddenInputs(bs) {
            hiddenDiv.innerHTML = '';
            (bs || []).forEach(function (b) {
                var inp = document.createElement('input');
                inp.type = 'checkbox'; inp.checked = true;
                inp.name = b.name; inp.value = b.value;
                inp.autocomplete = 'off'; inp.style.display = 'none';
                hiddenDiv.appendChild(inp);
            });
        }

        function resetState() {
            stateSel.innerHTML = '<option value="">Select state…</option>';
            stateSel.disabled = true; stateRow.style.display = 'none';
        }
        function resetCountry() {
            countrySel.innerHTML = '<option value="">Select country…</option>';
            countrySel.disabled = true; resetState();
        }

        /* ── Populate continent dropdown ─────────────────────────────── */

        continentOrder.forEach(function (label) { contSel.appendChild(makeOpt(label)); });

        /* ── Event listeners ─────────────────────────────────────────── */

        contSel.addEventListener('change', function () {
            var cv = this.value;
            resetCountry(); hiddenDiv.innerHTML = '';
            if (!cv) { customSearch(1); return; }

            var node = continentMap[cv];
            if (!node) return;

            if (node.countryOrder.length > 0) {
                node.countryOrder.forEach(function (l) { countrySel.appendChild(makeOpt(l)); });
                countrySel.disabled = false;
            } else {
                setHiddenInputs(node.buckets);
                customSearch(1);
            }
        });

        countrySel.addEventListener('change', function () {
            var cv = contSel.value, ctv = this.value;
            resetState(); hiddenDiv.innerHTML = '';
            if (!ctv) { customSearch(1); return; }

            var cNode = continentMap[cv] && continentMap[cv].countryMap[ctv];
            if (!cNode) return;

            if (cNode.stateOrder.length > 0) {
                // Has states — show the dropdown and wait; don't search yet
                cNode.stateOrder.forEach(function (l) { stateSel.appendChild(makeOpt(l)); });
                stateSel.disabled = false; stateRow.style.display = '';
            } else {
                // Leaf country — filter immediately
                setHiddenInputs(getBuckets(cv, ctv, null));
                customSearch(1);
            }
        });

        stateSel.addEventListener('change', function () {
            var cv = contSel.value, ctv = countrySel.value, sv = this.value;
            setHiddenInputs(getBuckets(cv, ctv, sv || null));
            customSearch(1);
        });

        /* ── Restore cascade state on page load ──────────────────────── */
        // Read from URL params first (reliable after F5 refresh), then
        // fall back to the Globus bucket checked flag.

        var urlParams = new URLSearchParams(window.location.search);
        var activeValues = urlParams.getAll('filter-match-any.location');

        if (!activeValues.length) {
            for (var i = 0; i < buckets.length; i++) {
                if (buckets[i].checked) { activeValues = [buckets[i].value]; break; }
            }
        }

        if (activeValues.length) {
            var activeValue = activeValues[0];
            var cls = classifyBucket(activeValue);

            // Find the matching Globus bucket so we can wire the hidden input
            var activeBucket = null;
            for (var j = 0; j < buckets.length; j++) {
                if (buckets[j].value === activeValue) { activeBucket = buckets[j]; break; }
            }

            // Pre-select continent
            contSel.value = cls.continent;

            // Force the location group open (it might still be collapsed)
            var locGroup = contSel.closest('.gdex-filter-group');
            if (locGroup) locGroup.classList.remove('gdex-filter-group--collapsed');

            if (cls.country && continentMap[cls.continent]) {
                continentMap[cls.continent].countryOrder.forEach(function (l) {
                    countrySel.appendChild(makeOpt(l));
                });
                countrySel.disabled = false;
                countrySel.value = cls.country;

                if (cls.state && continentMap[cls.continent].countryMap[cls.country]) {
                    continentMap[cls.continent].countryMap[cls.country].stateOrder.forEach(function (l) {
                        stateSel.appendChild(makeOpt(l));
                    });
                    stateSel.disabled = false;
                    stateRow.style.display = '';
                    stateSel.value = cls.state;
                }
            }

            if (activeBucket) setHiddenInputs([activeBucket]);
        }

        window._resetLocationSelects = function () {
            contSel.value = ''; resetCountry(); hiddenDiv.innerHTML = '';
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

                    var topSeeMoreBtn = document.createElement('button');
                    topSeeMoreBtn.type = 'button';
                    topSeeMoreBtn.className = 'gdex-filter-see-more gdex-filter-see-more--top';
                    topSeeMoreBtn.textContent = 'see less';
                    topSeeMoreBtn.style.display = 'none';
                    optionsEl.parentNode.insertBefore(topSeeMoreBtn, optionsEl);

                    function toggleSeeMore() {
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
                        topSeeMoreBtn.style.display = expanded ? '' : 'none';
                    }

                    seeMoreBtn.addEventListener('click', toggleSeeMore);
                    topSeeMoreBtn.addEventListener('click', toggleSeeMore);

                    group._gdexResetSeeMore = function () {
                        if (!expanded) return;
                        expanded = false;
                        labels.forEach(function (lbl, i) {
                            if (i >= LIMIT) lbl.classList.add('gdex-filter-option--overflow');
                        });
                        seeMoreBtn.textContent = 'see ' + overflow + ' more…';
                        topSeeMoreBtn.style.display = 'none';
                    };
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
                if (seeMoreBtn && overflow > 0) {
                    seeMoreBtn.style.display = q ? 'none' : '';
                    topSeeMoreBtn.style.display = (q || !expanded) ? 'none' : '';
                }
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
            pop.appendChild(lbl);
            pop.appendChild(p);

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
