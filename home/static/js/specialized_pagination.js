/*
   Client-side pagination for the AI-ready / Popular datasets pages.
   All cards are already rendered server-side; this just shows/hides
   them in pages and builds a pagination control matching the same
   look as the main search results pagination (.gdex-pagination).
*/
function gdexInitClientPagination(options) {
    var perPage = options.perPage || 7;
    var items = Array.prototype.slice.call(document.querySelectorAll(options.itemSelector));
    var nav = document.querySelector(options.paginationSelector);
    if (!nav || items.length <= perPage) return;

    var totalPages = Math.ceil(items.length / perPage);
    var currentPage = 1;

    function showPage(page, scrollToNav) {
        currentPage = Math.min(Math.max(1, page), totalPages);
        items.forEach(function (item, index) {
            var itemPage = Math.floor(index / perPage) + 1;
            item.style.display = (itemPage === currentPage) ? '' : 'none';
        });
        renderControls();
        if (scrollToNav) nav.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    function arrowButton(iconClass, label, targetPage, disabled) {
        var li = document.createElement('li');
        var btn = document.createElement('button');
        btn.className = 'gdex-pagination__arrow' + (disabled ? ' gdex-pagination__arrow--disabled' : '');
        btn.setAttribute('aria-label', label);
        if (disabled) btn.disabled = true;
        btn.innerHTML = '<i class="' + iconClass + '"></i>';
        if (!disabled) btn.addEventListener('click', function () { showPage(targetPage, true); });
        li.appendChild(btn);
        return li;
    }

    function pageButton(pageNum) {
        var li = document.createElement('li');
        var btn = document.createElement('button');
        var isActive = pageNum === currentPage;
        btn.className = 'gdex-pagination__page' + (isActive ? ' gdex-pagination__page--active' : '');
        btn.textContent = pageNum;
        if (isActive) btn.setAttribute('aria-current', 'page');
        else btn.addEventListener('click', function () { showPage(pageNum, true); });
        li.appendChild(btn);
        return li;
    }

    function ellipsis() {
        var li = document.createElement('li');
        li.innerHTML = '<span class="gdex-pagination__ellipsis">&hellip;</span>';
        return li;
    }

    function shouldShowPageNumber(pageNum) {
        return pageNum === 1 || pageNum === totalPages || Math.abs(pageNum - currentPage) <= 1;
    }

    function renderControls() {
        var list = document.createElement('ul');
        list.className = 'gdex-pagination__list';

        list.appendChild(arrowButton('fas fa-chevron-left', 'Previous', currentPage - 1, currentPage === 1));

        var lastShown = 0;
        for (var pageNum = 1; pageNum <= totalPages; pageNum++) {
            if (!shouldShowPageNumber(pageNum)) continue;
            if (pageNum - lastShown > 1) list.appendChild(ellipsis());
            list.appendChild(pageButton(pageNum));
            lastShown = pageNum;
        }

        list.appendChild(arrowButton('fas fa-chevron-right', 'Next', currentPage + 1, currentPage === totalPages));

        nav.innerHTML = '';
        nav.appendChild(list);
    }

    showPage(1);
}
