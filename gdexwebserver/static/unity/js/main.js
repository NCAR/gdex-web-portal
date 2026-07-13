// Example starter JavaScript for disabling form submissions if there are invalid fields
(function () {
  'use strict'

  // Fetch all the forms we want to apply custom Bootstrap validation styles to
  function webformValidation() {
    var forms = document.querySelectorAll('.needs-validation')

    // Loop over them and prevent submission
    Array.prototype.slice.call(forms)
      .forEach(function (form) {
        form.addEventListener('submit', function (event) {
          if (!form.checkValidity()) {
            event.preventDefault()
            event.stopPropagation()
          }

          form.classList.add('was-validated')
        }, false)
      })
  }

  function siteNameSplit() {
    var site_name_link = document.querySelector('.site-name a')
    var words = site_name_link.innerHTML.split(' ')

    words.forEach(function (item, i, word) {
      if (i === Math.floor(words.length / 2 - 1))
        word[i] += "<br/>";
      else
        word[i] += ' ';
    })

    site_name_link.innerHTML = words.join('')
  }

  function addOpenNavClass() {
    var container = document.querySelector('#menuIcon')
    var mobile_menu_open = false

    container.addEventListener('click', function () {
      if (mobile_menu_open === false) {
        document.body.classList.add('nav-open')
        mobile_menu_open = true
      } else {
        document.body.classList.remove('nav-open')
        mobile_menu_open = false
      }
    })
  }

  function offscreen(selector) {
    let elem = document.querySelectorAll(selector);
    if (elem !== 'undefined' && elem.length > 0) {
      let rect = elem[0].getBoundingClientRect();
      return (
        (rect.right > window.innerWidth)
      );
    }
  }

  function dropdown_menu_spacing() {
    if (document.querySelectorAll('li:not(.mega-menu) .dropdown-menu.show')[0]) {
      let menu_item = document.querySelectorAll('.dropdown-menu.show')[0].parentElement;
      let menu_item_height = menu_item.offsetHeight
      let menu_lines = Math.floor(menu_item_height / 24);
      let spacing = Math.floor(menu_lines * .75)

      if (menu_lines > 1) {
        spacing = Math.floor(menu_lines * .75) - .5;
      }

      let top_height = spacing + 1.9;
      let site_name = document.querySelectorAll('.navbar-collapse .site-name a');

      if (site_name.length > 0) {
        let site_name_height = site_name[0].offsetHeight
        let site_name_lines = Math.floor(site_name_height / 24);
        top_height = (site_name_lines * .75) + spacing + 2.25;
      }

      document.querySelectorAll('.dropdown-menu.show')[0].style.top=top_height + "rem";
    }
  }

  function add_dropdown_menu_end() {
    if (offscreen('.dropdown-menu.show')) {
      let dropdown_menu = document.querySelectorAll('.dropdown-menu.show');
      dropdown_menu[0].classList.add('dropdown-menu-end');
    }
  }

  function dropdown_menu_offscreen() {
    let dropdown_menu = document.querySelector('.navbar .dropdown-menu-end');

    if (dropdown_menu) {
      dropdown_menu.classList.remove('dropdown-menu-end');
    }

    add_dropdown_menu_end();
  }

  function dropdown_items_click() {
    dropdown_menu_spacing();
    dropdown_menu_offscreen();
  }

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

  webformValidation();
  siteNameSplit();
  addOpenNavClass();
  enableNavDropdownHover();

  let buttons = document.querySelectorAll('.btn.dropdown-toggle');
  for (let i of buttons) {
    i.addEventListener('click', dropdown_items_click);
  }

  window.addEventListener('DOMContentLoaded', function () {
    if (window.innerWidth >= 1024) {
      document.getElementById('ncarCollapseButton').classList.add('disabled')
      document.getElementById('ncarCollapseButton').classList.remove('collapsed')
      document.getElementById('ncarCollapseButton').removeAttribute('data-bs-toggle')
      document.getElementById('ncarCollapseMenu').removeAttribute('class')
      document.getElementById('ucarCollapseButton').classList.add('disabled')
      document.getElementById('ucarCollapseButton').classList.remove('collapsed')
      document.getElementById('ucarCollapseButton').removeAttribute('data-bs-toggle')
      document.getElementById('ucarCollapseMenu').removeAttribute('class')

      if (document.getElementById('sidebarCollapseButton') && document.getElementById('sidebarMenu')) {
        document.getElementById('sidebarCollapseButton').classList.add('disabled')
        document.getElementById('sidebarCollapseButton').classList.remove('collapsed')
        document.getElementById('sidebarCollapseButton').removeAttribute('data-bs-toggle')
        document.getElementById('sidebarMenu').classList.remove('collapse')
      }
    }
  })

  window.addEventListener('resize', function () {
    if (window.innerWidth >= 1024) {
      document.getElementsByTagName('body')[0].classList.remove('nav-open')
      document.getElementById('ncarCollapseButton').classList.add('disabled')
      document.getElementById('ncarCollapseButton').classList.remove('collapsed')
      document.getElementById('ncarCollapseButton').removeAttribute('data-bs-toggle')
      document.getElementById('ncarCollapseMenu').removeAttribute('class')
      document.getElementById('ucarCollapseButton').classList.add('disabled')
      document.getElementById('ucarCollapseButton').classList.remove('collapsed')
      document.getElementById('ucarCollapseButton').removeAttribute('data-bs-toggle')
      document.getElementById('ucarCollapseMenu').removeAttribute('class')

      if (document.getElementById('sidebarCollapseButton') && document.getElementById('sidebarMenu')) {
        document.getElementById('sidebarCollapseButton').classList.add('disabled')
        document.getElementById('sidebarCollapseButton').classList.remove('collapsed')
        document.getElementById('sidebarCollapseButton').removeAttribute('data-bs-toggle')
        document.getElementById('sidebarMenu').classList.remove('collapse')
      }
    } else if (window.innerWidth < 1024) {
      document.getElementById('ncarCollapseButton').classList.remove('disabled')
      document.getElementById('ncarCollapseButton').classList.add('collapsed')
      document.getElementById('ncarCollapseButton').setAttribute('data-bs-toggle', 'collapse')
      document.getElementById('ncarCollapseMenu').setAttribute('class', 'collapse')
      document.getElementById('ucarCollapseButton').classList.remove('disabled')
      document.getElementById('ucarCollapseButton').classList.add('collapsed')
      document.getElementById('ucarCollapseButton').setAttribute('data-bs-toggle', 'collapse')
      document.getElementById('ucarCollapseMenu').setAttribute('class', 'collapse')

      if (document.getElementById('sidebarCollapseButton') || document.getElementById('sidebarMenu')) {
        document.getElementById('sidebarCollapseButton').classList.remove('disabled')
        document.getElementById('sidebarCollapseButton').classList.add('collapsed')
        document.getElementById('sidebarCollapseButton').setAttribute('data-bs-toggle', 'collapse')
        document.getElementById('sidebarMenu').classList.add('collapse')
      }
    }
  })
})()
