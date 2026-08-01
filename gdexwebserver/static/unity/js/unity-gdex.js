  function enableNavDropdownHover() {
    var HOVER_CLOSE_DELAY = 300
    var navDropdowns = document.querySelectorAll('.navbar .nav-item.dropdown')

    function isDesktop() {
      return window.innerWidth >= 1024
    }

    function getDropdown(toggle) {
      return bootstrap.Dropdown.getOrCreateInstance(toggle)
    }

    navDropdowns.forEach(function (item) {
      var toggle = item.querySelector('.dropdown-toggle')
      if (!toggle) return

      var menu = item.querySelector('.dropdown-menu')
      var closeTimer

      function closeOtherDropdowns() {
        navDropdowns.forEach(function (other) {
          var otherToggle = other.querySelector('.dropdown-toggle')
          if (other !== item && otherToggle) getDropdown(otherToggle).hide()
        })
      }

      function openMenu() {
        clearTimeout(closeTimer)
        if (!isDesktop()) return
        closeOtherDropdowns()
        getDropdown(toggle).show()
        dropdown_items_click()
      }

      function closeMenu() {
        if (isDesktop()) getDropdown(toggle).hide()
      }

      function scheduleClose() {
        closeTimer = setTimeout(closeMenu, HOVER_CLOSE_DELAY)
      }

      item.addEventListener('mouseenter', openMenu)
      item.addEventListener('mouseleave', scheduleClose)

      if (menu) {
        menu.addEventListener('mouseenter', function () {
          clearTimeout(closeTimer)
        })
        menu.addEventListener('mouseleave', scheduleClose)
      }
    })
  }

  enableNavDropdownHover();
  