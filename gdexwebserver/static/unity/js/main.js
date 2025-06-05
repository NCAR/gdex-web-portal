'use strict';

// Example starter JavaScript for disabling form submissions if there are invalid fields
(function () {

  // Fetch all the forms we want to apply custom Bootstrap validation styles to
  function webformValidation() {
    var forms = document.querySelectorAll('.needs-validation');

    // Loop over them and prevent submission
    Array.prototype.slice.call(forms)
      .forEach(function (form) {
        form.addEventListener('submit', function (event) {
          if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
          }

          form.classList.add('was-validated');
        }, false);
      });
  }

  function siteNameSplit() {
    var site_name_link = document.querySelector('.site-name a');
    var words = site_name_link.innerHTML.split(' ');

    words.forEach(function (item, i, word) {
      if (i === Math.floor(words.length / 2 - 1))
        word[i] += "<br/>";
      else
        word[i] += ' ';
    });

    site_name_link.innerHTML = words.join('');

    if (site_name_link.innerHTML.includes('<br>')) {
      site_name_link.classList.add('small-site-name');
      var menu = document.querySelector('.navbar-nav .dropdown-menu');
      menu.classList.add('small-site-name');
    }
  }

  function addOpenNavClass() {
    var container = document.querySelector('#menuIcon');
    var mobile_menu_open = false;

    container.addEventListener('click', function () {
      if (mobile_menu_open === false) {
        document.body.classList.add('nav-open');
        mobile_menu_open = true;
      } else {
        document.body.classList.remove('nav-open');
        mobile_menu_open = false;
      }
    });
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

  function get_dropdown_items() {
    if (offscreen('.dropdown-menu.show')) {
      let dropdown_menu = document.querySelectorAll('.dropdown-menu.show');
      dropdown_menu[0].classList.add('dropdown-menu-end');
    }
  }

  function dropdown_items_click() {
    let dropdown_menu = document.querySelector('.navbar .dropdown-menu-end');

    if (dropdown_menu) {
      dropdown_menu.classList.remove('dropdown-menu-end');
    }

    get_dropdown_items();
  }

  webformValidation();
  siteNameSplit();
  addOpenNavClass();

  window.addEventListener('click', dropdown_items_click);

  window.addEventListener('DOMContentLoaded', function () {
    if (window.innerWidth >= 1024) {
      document.getElementById('ncarCollapseButton').classList.add('disabled');
      document.getElementById('ncarCollapseButton').classList.remove('collapsed');
      document.getElementById('ncarCollapseButton').removeAttribute('data-bs-toggle');
      document.getElementById('ncarCollapseMenu').removeAttribute('class');
      document.getElementById('ucarCollapseButton').classList.add('disabled');
      document.getElementById('ucarCollapseButton').classList.remove('collapsed');
      document.getElementById('ucarCollapseButton').removeAttribute('data-bs-toggle');
      document.getElementById('ucarCollapseMenu').removeAttribute('class');

      if (document.getElementById('sidebarCollapseButton') && document.getElementById('sidebarMenu')) {
        document.getElementById('sidebarCollapseButton').classList.add('disabled');
        document.getElementById('sidebarCollapseButton').classList.remove('collapsed');
        document.getElementById('sidebarCollapseButton').removeAttribute('data-bs-toggle');
        document.getElementById('sidebarMenu').classList.remove('collapse');
      }
    }
  });

  window.addEventListener('resize', function (event) {
    if (window.innerWidth >= 1024) {
      document.getElementsByTagName('body')[0].classList.remove('nav-open');
      document.getElementById('ncarCollapseButton').classList.add('disabled');
      document.getElementById('ncarCollapseButton').classList.remove('collapsed');
      document.getElementById('ncarCollapseButton').removeAttribute('data-bs-toggle');
      document.getElementById('ncarCollapseMenu').removeAttribute('class');
      document.getElementById('ucarCollapseButton').classList.add('disabled');
      document.getElementById('ucarCollapseButton').classList.remove('collapsed');
      document.getElementById('ucarCollapseButton').removeAttribute('data-bs-toggle');
      document.getElementById('ucarCollapseMenu').removeAttribute('class');

      if (document.getElementById('sidebarCollapseButton') && document.getElementById('sidebarMenu')) {
        document.getElementById('sidebarCollapseButton').classList.add('disabled');
        document.getElementById('sidebarCollapseButton').classList.remove('collapsed');
        document.getElementById('sidebarCollapseButton').removeAttribute('data-bs-toggle');
        document.getElementById('sidebarMenu').classList.remove('collapse');
      }
    } else if (window.innerWidth < 1024) {
      document.getElementById('ncarCollapseButton').classList.remove('disabled');
      document.getElementById('ncarCollapseButton').classList.add('collapsed');
      document.getElementById('ncarCollapseButton').setAttribute('data-bs-toggle', 'collapse');
      document.getElementById('ncarCollapseMenu').setAttribute('class', 'collapse');
      document.getElementById('ucarCollapseButton').classList.remove('disabled');
      document.getElementById('ucarCollapseButton').classList.add('collapsed');
      document.getElementById('ucarCollapseButton').setAttribute('data-bs-toggle', 'collapse');
      document.getElementById('ucarCollapseMenu').setAttribute('class', 'collapse');

      if (document.getElementById('sidebarCollapseButton') || document.getElementById('sidebarMenu')) {
        document.getElementById('sidebarCollapseButton').classList.remove('disabled');
        document.getElementById('sidebarCollapseButton').classList.add('collapsed');
        document.getElementById('sidebarCollapseButton').setAttribute('data-bs-toggle', 'collapse');
        document.getElementById('sidebarMenu').classList.add('collapse');
      }
    }

    get_dropdown_items();
  });
})();
