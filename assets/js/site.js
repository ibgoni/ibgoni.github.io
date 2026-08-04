/* Site behaviour: theme toggle, mobile menu, publication filters, BibTeX copy,
   notebook table of contents, scroll reveal.

   Everything here is progressive enhancement — the pages are readable and
   navigable with JavaScript disabled. */

(function () {
  'use strict';

  var root = document.documentElement;
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ------------------------------------------------------------- theme */

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    var button = document.querySelector('.theme-toggle');
    if (button) {
      var next = theme === 'dark' ? 'light' : 'dark';
      button.setAttribute('aria-label', 'Switch to ' + next + ' theme');
    }
  }

  // The inline script in <head> already set the attribute; make sure the
  // button label matches it.
  applyTheme(root.getAttribute('data-theme') || 'light');

  var themeToggle = document.querySelector('.theme-toggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      try { localStorage.setItem('theme', next); } catch (e) {}
    });
  }

  // Follow the system if the visitor never expressed a preference.
  try {
    if (!localStorage.getItem('theme') && window.matchMedia) {
      var scheme = window.matchMedia('(prefers-color-scheme: dark)');
      var onSchemeChange = function (event) {
        applyTheme(event.matches ? 'dark' : 'light');
      };
      if (scheme.addEventListener) scheme.addEventListener('change', onSchemeChange);
      else if (scheme.addListener) scheme.addListener(onSchemeChange);
    }
  } catch (e) {}

  /* -------------------------------------------------------- mobile menu */

  var navToggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('site-nav');

  if (navToggle && nav) {
    navToggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      navToggle.setAttribute('aria-expanded', String(open));
      navToggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    });

    nav.addEventListener('click', function (event) {
      if (event.target.tagName === 'A') {
        nav.classList.remove('open');
        navToggle.setAttribute('aria-expanded', 'false');
      }
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && nav.classList.contains('open')) {
        nav.classList.remove('open');
        navToggle.setAttribute('aria-expanded', 'false');
        navToggle.focus();
      }
    });
  }

  /* --------------------------------------------------- publication filters */

  var filterBar = document.querySelector('.filters');
  if (filterBar) {
    var papers = Array.prototype.slice.call(document.querySelectorAll('.paper[data-status]'));
    var buttons = Array.prototype.slice.call(filterBar.querySelectorAll('.filter'));

    // Label each button with how many papers it matches.
    buttons.forEach(function (button) {
      var want = button.getAttribute('data-filter');
      var n = want === 'all'
        ? papers.length
        : papers.filter(function (p) { return p.getAttribute('data-status') === want; }).length;
      var slot = button.querySelector('.count');
      if (slot) slot.textContent = String(n);
      if (n === 0) button.hidden = true;
    });

    filterBar.addEventListener('click', function (event) {
      var button = event.target.closest('.filter');
      if (!button) return;
      var want = button.getAttribute('data-filter');

      buttons.forEach(function (other) {
        other.setAttribute('aria-pressed', String(other === button));
      });

      papers.forEach(function (paper) {
        paper.hidden = want !== 'all' && paper.getAttribute('data-status') !== want;
      });

      // Hide a section heading whose papers are all filtered out.
      document.querySelectorAll('section[data-group]').forEach(function (section) {
        var visible = section.querySelectorAll('.paper:not([hidden])').length;
        section.hidden = visible === 0;
      });
    });
  }

  /* ------------------------------------------------------------ BibTeX */

  document.querySelectorAll('.cite-toggle').forEach(function (toggle) {
    var box = document.getElementById(toggle.getAttribute('aria-controls'));
    if (!box) return;
    toggle.addEventListener('click', function () {
      var open = box.hidden;
      box.hidden = !open;
      toggle.setAttribute('aria-expanded', String(open));
      toggle.textContent = open ? 'Hide BibTeX' : 'Cite';
    });
  });

  document.querySelectorAll('.copy-btn').forEach(function (button) {
    button.addEventListener('click', function () {
      var pre = document.getElementById(button.getAttribute('data-target'));
      if (!pre) return;
      var text = pre.textContent;
      var done = function () {
        var original = button.textContent;
        button.textContent = 'Copied';
        setTimeout(function () { button.textContent = original; }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () {});
      } else {
        var area = document.createElement('textarea');
        area.value = text;
        area.setAttribute('readonly', '');
        area.style.position = 'absolute';
        area.style.left = '-9999px';
        document.body.appendChild(area);
        area.select();
        try { document.execCommand('copy'); done(); } catch (e) {}
        document.body.removeChild(area);
      }
    });
  });

  /* ------------------------------------------------- notebook table of contents */

  var tocLinks = Array.prototype.slice.call(document.querySelectorAll('.nb-toc a'));
  if (tocLinks.length && 'IntersectionObserver' in window) {
    var targets = tocLinks
      .map(function (link) { return document.getElementById(decodeURIComponent(link.hash.slice(1))); })
      .filter(Boolean);

    if (targets.length) {
      var setActive = function (id) {
        tocLinks.forEach(function (link) {
          link.classList.toggle('active', decodeURIComponent(link.hash.slice(1)) === id);
        });
      };

      var spy = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) setActive(entry.target.id);
        });
      }, { rootMargin: '-80px 0px -70% 0px', threshold: 0 });

      targets.forEach(function (target) { spy.observe(target); });
    }
  }

  /* ------------------------------------------------------- scroll reveal */

  if (!reduceMotion && 'IntersectionObserver' in window) {
    var reveal = document.querySelectorAll('.paper, .course, .nb-card, .facet');
    if (reveal.length) {
      reveal.forEach(function (element) { element.classList.add('will-reveal'); });

      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('revealed');
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.05, rootMargin: '0px 0px -4% 0px' });

      reveal.forEach(function (element) { observer.observe(element); });

      // Content must never stay invisible because of a decoration. If anything
      // is still hidden shortly after load — a browser quirk, a print dialog, a
      // page opened in a background tab — show it.
      var unhideAll = function () {
        reveal.forEach(function (element) { element.classList.add('revealed'); });
        observer.disconnect();
      };
      setTimeout(unhideAll, 4000);
      window.addEventListener('beforeprint', unhideAll);
    }
  }
})();
