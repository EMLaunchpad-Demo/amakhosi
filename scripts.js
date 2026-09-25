/* ==========================================================================
   AMAKHOSI — gedeeld script voor alle pagina's (vanilla JS, geen libraries)
   --------------------------------------------------------------------------
   1. JS-vlag (voor scroll-animaties)
   2. Sticky header bij scrollen
   3. Mobiel menu (hamburger)
   4. Smooth scroll voor ankerlinks (met header-offset)
   5. Scroll-reveal animaties (IntersectionObserver)
   6. Tabs (arrangementen: wellness / overnachting)
   7. FAQ-accordeon (één vraag tegelijk open)
   8. Mobiele CTA-balk tonen na de hero
   9. Huidig jaartal in de footer
   ========================================================================== */
(function () {
  'use strict';

  var doc = document;
  var root = doc.documentElement;

  /* 1. JS-vlag: animaties verbergen content pas als dit script draait */
  root.classList.add('amk-js');

  function ready(fn) {
    if (doc.readyState !== 'loading') fn();
    else doc.addEventListener('DOMContentLoaded', fn);
  }

  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  ready(function () {
    var header = doc.querySelector('[data-amk-header]');

    /* ------------------------------------------------------------------
       2. Sticky header: achtergrond + topbalk inklappen na 40px scrollen
       ------------------------------------------------------------------ */
    function onScroll() {
      if (!header) return;
      header.classList.toggle('is-scrolled', window.scrollY > 40);
    }
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });

    /* ------------------------------------------------------------------
       3. Mobiel menu
       ------------------------------------------------------------------ */
    var burger = doc.querySelector('[data-amk-burger]');
    var menu = doc.getElementById('amk-menu');

    function setMenu(open) {
      if (!burger || !menu) return;
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
      burger.setAttribute('aria-label', open ? 'Menu sluiten' : 'Menu openen');
      menu.classList.toggle('is-open', open);
      menu.classList.toggle('is-compact', header && header.classList.contains('is-scrolled'));
      menu.setAttribute('aria-hidden', open ? 'false' : 'true');
      if (header) header.classList.toggle('is-menu-open', open);
      root.classList.toggle('amk-lock', open);
      if (open) {
        var first = menu.querySelector('a');
        if (first) first.focus({ preventScroll: true });
      }
    }

    if (burger && menu) {
      burger.addEventListener('click', function () {
        setMenu(burger.getAttribute('aria-expanded') !== 'true');
      });

      menu.addEventListener('click', function (e) {
        if (e.target.closest('a')) setMenu(false);
      });

      doc.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && menu.classList.contains('is-open')) {
          setMenu(false);
          burger.focus();
        }
      });

      window.addEventListener('resize', function () {
        if (window.innerWidth >= 1000 && menu.classList.contains('is-open')) setMenu(false);
      });
    }

    /* ------------------------------------------------------------------
       4. Smooth scroll met compensatie voor de vaste header
       ------------------------------------------------------------------ */
    doc.addEventListener('click', function (e) {
      var link = e.target.closest('a[href^="#"]');
      if (!link) return;
      var id = link.getAttribute('href');
      if (id.length < 2) return;
      var target = doc.getElementById(id.slice(1));
      if (!target) return;

      e.preventDefault();
      var nav = doc.querySelector('.amk-nav');
      var offset = nav ? nav.offsetHeight + 12 : 0;
      var top = target.getBoundingClientRect().top + window.scrollY - offset;
      window.scrollTo({ top: top, behavior: reduceMotion ? 'auto' : 'smooth' });

      if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
      target.focus({ preventScroll: true });
      if (history.pushState) history.pushState(null, '', id);
    });

    /* ------------------------------------------------------------------
       5. Scroll-reveal
       Gebruik: data-amk-reveal op een element. Kinderen van een element
       met data-amk-stagger krijgen automatisch een oplopende vertraging.
       ------------------------------------------------------------------ */
    doc.querySelectorAll('[data-amk-stagger]').forEach(function (group) {
      var step = parseFloat(group.getAttribute('data-amk-stagger')) || 0.08;
      Array.prototype.forEach.call(group.children, function (child, i) {
        child.setAttribute('data-amk-reveal', '');
        child.style.setProperty('--amk-delay', (i * step).toFixed(2) + 's');
      });
    });

    var revealEls = doc.querySelectorAll('[data-amk-reveal]');
    if ('IntersectionObserver' in window && !reduceMotion) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            io.unobserve(entry.target);
          }
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.12 });
      revealEls.forEach(function (el) { io.observe(el); });
    } else {
      revealEls.forEach(function (el) { el.classList.add('is-visible'); });
    }

    /* ------------------------------------------------------------------
       6. Tabs (toegankelijk: pijltjestoetsen + aria)
       ------------------------------------------------------------------ */
    doc.querySelectorAll('[data-amk-tabs]').forEach(function (tablist) {
      var tabs = Array.prototype.slice.call(tablist.querySelectorAll('[role="tab"]'));

      function activate(index, focus) {
        tabs.forEach(function (tab, i) {
          var selected = i === index;
          var panel = doc.getElementById(tab.getAttribute('aria-controls'));
          tab.setAttribute('aria-selected', selected ? 'true' : 'false');
          tab.setAttribute('tabindex', selected ? '0' : '-1');
          if (panel) {
            panel.hidden = !selected;
            if (selected) {
              panel.querySelectorAll('[data-amk-reveal]').forEach(function (el) {
                el.classList.add('is-visible');
              });
            }
          }
        });
        tablist.setAttribute('data-active', String(index));
        if (focus) tabs[index].focus();
      }

      tabs.forEach(function (tab, i) {
        tab.addEventListener('click', function () { activate(i, false); });
        tab.addEventListener('keydown', function (e) {
          var next = null;
          if (e.key === 'ArrowRight') next = (i + 1) % tabs.length;
          if (e.key === 'ArrowLeft') next = (i - 1 + tabs.length) % tabs.length;
          if (e.key === 'Home') next = 0;
          if (e.key === 'End') next = tabs.length - 1;
          if (next !== null) {
            e.preventDefault();
            activate(next, true);
          }
        });
      });
    });

    /* Links met data-amk-open-tab="<index>" openen meteen het juiste tabblad */
    doc.querySelectorAll('[data-amk-open-tab]').forEach(function (link) {
      link.addEventListener('click', function () {
        var tab = doc.querySelectorAll('[data-amk-tabs] [role="tab"]')[+link.getAttribute('data-amk-open-tab')];
        if (tab) tab.click();
      });
    });

    /* ------------------------------------------------------------------
       7. FAQ: slechts één vraag tegelijk open binnen dezelfde lijst
       ------------------------------------------------------------------ */
    doc.querySelectorAll('[data-amk-accordion]').forEach(function (list) {
      var items = list.querySelectorAll('details');
      items.forEach(function (item) {
        item.addEventListener('toggle', function () {
          if (!item.open) return;
          items.forEach(function (other) {
            if (other !== item) other.open = false;
          });
        });
      });
    });

    /* ------------------------------------------------------------------
       8. Mobiele CTA-balk: verschijnt zodra de hero uit beeld is
       ------------------------------------------------------------------ */
    var bar = doc.querySelector('[data-amk-mobilebar]');
    var hero = doc.querySelector('[data-amk-hero]');
    if (bar && hero && 'IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        var visible = !entries[0].isIntersecting;
        bar.classList.toggle('is-visible', visible);
        bar.setAttribute('aria-hidden', visible ? 'false' : 'true');
      }, { threshold: 0 }).observe(hero);
    } else if (bar) {
      bar.classList.add('is-visible');
    }

    /* ------------------------------------------------------------------
       9. Jaartal
       ------------------------------------------------------------------ */
    doc.querySelectorAll('[data-amk-year]').forEach(function (el) {
      el.textContent = new Date().getFullYear();
    });
  });
})();
