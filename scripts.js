/* ==========================================================================
   AMAKHOSI — gedeeld script voor alle pagina's (vanilla JS, geen libraries)
   --------------------------------------------------------------------------
    1. Basis (JS-vlag, helpers, reduced motion)
    2. Header: zwevende capsule, verbergen bij naar beneden scrollen,
       voortgangsbalk
    3. Navigatie: glijdende markering onder de links
    4. Mobiel menu (cirkel-onthulling vanaf de knop)
    5. Smooth scroll voor ankerlinks
    6. Woord-voor-woord titels
    7. Scroll-reveal (+ stagger) en "zon komt op"-secties
    8. Parallax
    9. 3D-tilt, spotlight en magnetische knoppen
   10. Sintels (hero/CTA) en cursorlicht in de hero
   11. Tellers
   12. Tabs (arrangementen)
   13. FAQ: vloeiend openen/sluiten, één tegelijk
   14. Galerij-lightbox
   15. Mobiele CTA-balk
   16. Terug naar boven + jaartal
   ========================================================================== */
(function () {
  'use strict';

  /* ------------------------------------------------------------------
     1. Basis
     ------------------------------------------------------------------ */
  var doc = document;
  var root = doc.documentElement;
  root.classList.add('amk-js');

  var mq = function (q) { return window.matchMedia ? window.matchMedia(q).matches : false; };
  var reduceMotion = mq('(prefers-reduced-motion: reduce)');
  var finePointer = mq('(hover: hover) and (pointer: fine)');

  function ready(fn) {
    if (doc.readyState !== 'loading') fn();
    else doc.addEventListener('DOMContentLoaded', fn);
  }

  function $$(sel, ctx) {
    return Array.prototype.slice.call((ctx || doc).querySelectorAll(sel));
  }

  function clamp(v, min, max) { return Math.min(max, Math.max(min, v)); }

  /* Eén gedeelde scroll-lus via requestAnimationFrame */
  var scrollFns = [];
  var ticking = false;
  function onScroll(fn) { scrollFns.push(fn); }
  function runScroll() {
    ticking = false;
    var y = window.scrollY || window.pageYOffset;
    for (var i = 0; i < scrollFns.length; i++) scrollFns[i](y);
  }
  function requestScroll() {
    if (!ticking) {
      ticking = true;
      window.requestAnimationFrame(runScroll);
    }
  }

  ready(function () {
    var header = doc.querySelector('[data-amk-header]');
    var menu = doc.getElementById('amk-menu');
    var menuBtn = doc.querySelector('[data-amk-menu-btn]');

    /* ------------------------------------------------------------------
       2. Header
       ------------------------------------------------------------------ */
    var lastY = 0;
    onScroll(function (y) {
      if (!header) return;
      var menuOpen = menu && menu.classList.contains('is-open');
      header.classList.toggle('is-scrolled', y > 40);

      // Verbergen bij naar beneden scrollen, tonen bij naar boven scrollen
      var delta = y - lastY;
      if (!menuOpen && !header.contains(doc.activeElement)) {
        if (y > 480 && delta > 6) header.classList.add('is-hidden');
        else if (delta < -6 || y < 200) header.classList.remove('is-hidden');
      }
      lastY = y;

      // Voortgangsbalk
      var max = root.scrollHeight - window.innerHeight;
      root.style.setProperty('--amk-progress', max > 0 ? (y / max).toFixed(4) : 0);
    });

    if (header) {
      header.addEventListener('focusin', function () { header.classList.remove('is-hidden'); });
    }

    /* ------------------------------------------------------------------
       3. Glijdende markering in de navigatie
       ------------------------------------------------------------------ */
    $$('[data-amk-navlinks]').forEach(function (list) {
      var glider = list.querySelector('.amk-nav__glider');
      var links = $$('a', list);
      var current = list.querySelector('[aria-current="page"]');
      if (!glider) return;

      function moveTo(el) {
        if (!el) {
          list.classList.remove('has-glider');
          return;
        }
        var lr = list.getBoundingClientRect();
        var r = el.getBoundingClientRect();
        list.style.setProperty('--amk-gx', (r.left - lr.left) + 'px');
        list.style.setProperty('--amk-gw', r.width + 'px');
        list.classList.add('has-glider');
      }

      links.forEach(function (a) {
        a.addEventListener('pointerenter', function () { moveTo(a); });
        a.addEventListener('focus', function () { moveTo(a); });
      });
      list.addEventListener('pointerleave', function () { moveTo(current); });
      list.addEventListener('focusout', function (e) {
        if (!list.contains(e.relatedTarget)) moveTo(current);
      });

      // Startpositie (na het laden van de lettertypes)
      var init = function () { moveTo(current); };
      if (doc.fonts && doc.fonts.ready) doc.fonts.ready.then(init);
      else window.setTimeout(init, 300);
      window.addEventListener('resize', init);
    });

    /* ------------------------------------------------------------------
       4. Mobiel menu
       ------------------------------------------------------------------ */
    function setMenu(open) {
      if (!menuBtn || !menu) return;
      if (open) {
        // De cirkel opent vanaf het midden van de menuknop
        var r = menuBtn.getBoundingClientRect();
        menu.style.setProperty('--amk-menu-x', (r.left + r.width / 2) + 'px');
        menu.style.setProperty('--amk-menu-y', (r.top + r.height / 2) + 'px');
      }
      menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
      menuBtn.setAttribute('aria-label', open ? 'Menu sluiten' : 'Menu openen');
      menu.classList.toggle('is-open', open);
      menu.setAttribute('aria-hidden', open ? 'false' : 'true');
      if (header) {
        header.classList.toggle('is-menu-open', open);
        header.classList.remove('is-hidden');
      }
      root.classList.toggle('amk-lock', open);
      if (open) {
        var first = menu.querySelector('a');
        if (first) window.setTimeout(function () { first.focus({ preventScroll: true }); }, 350);
      }
    }

    if (menuBtn && menu) {
      $$('.amk-menu__links a', menu).forEach(function (a, i) { a.style.setProperty('--i', i); });

      menuBtn.addEventListener('click', function () {
        setMenu(menuBtn.getAttribute('aria-expanded') !== 'true');
      });

      menu.addEventListener('click', function (e) {
        if (e.target.closest('a')) setMenu(false);
      });

      doc.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && menu.classList.contains('is-open')) {
          setMenu(false);
          menuBtn.focus();
        }
      });

      window.addEventListener('resize', function () {
        if (window.innerWidth >= 1000 && menu.classList.contains('is-open')) setMenu(false);
      });
    }

    /* ------------------------------------------------------------------
       5. Smooth scroll met compensatie voor de header
       ------------------------------------------------------------------ */
    doc.addEventListener('click', function (e) {
      var link = e.target.closest('a[href^="#"]');
      if (!link) return;
      var id = link.getAttribute('href');
      if (id.length < 2) return;
      var target = doc.getElementById(id.slice(1));
      if (!target) return;

      e.preventDefault();
      var top = target.getBoundingClientRect().top + window.scrollY - 90;
      window.scrollTo({ top: top, behavior: reduceMotion ? 'auto' : 'smooth' });
      if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
      target.focus({ preventScroll: true });
      if (history.pushState) history.pushState(null, '', id);
    });

    /* ------------------------------------------------------------------
       6. Woord-voor-woord titels
       Gebruik: data-amk-split op een titel. Opmaak zoals <em> blijft behouden.
       ------------------------------------------------------------------ */
    var splitTargets = $$('[data-amk-split]');
    splitTargets.forEach(function (el) {
      var count = 0;
      (function walk(node) {
        Array.prototype.slice.call(node.childNodes).forEach(function (child) {
          if (child.nodeType === 3) {
            var parts = child.textContent.split(/(\s+)/);
            var frag = doc.createDocumentFragment();
            parts.forEach(function (part) {
              if (!part) return;
              if (/^\s+$/.test(part)) {
                frag.appendChild(doc.createTextNode(' '));
                return;
              }
              var w = doc.createElement('span');
              w.className = 'amk-w';
              var inner = doc.createElement('span');
              inner.className = 'amk-w__i';
              inner.style.setProperty('--i', count++);
              inner.textContent = part;
              w.appendChild(inner);
              frag.appendChild(w);
            });
            node.replaceChild(frag, child);
          } else if (child.nodeType === 1 && child.tagName !== 'BR') {
            walk(child);
          }
        });
      })(el);
      el.classList.add('amk-split');
    });

    /* ------------------------------------------------------------------
       7. Scroll-reveal
       data-amk-reveal="" | "fade" | "left" | "right" | "zoom" | "clip"
       data-amk-stagger="0.08" geeft de kinderen een oplopende vertraging.
       data-amk-rise laat de zon in een CTA-sectie opkomen.
       ------------------------------------------------------------------ */
    $$('[data-amk-stagger]').forEach(function (group) {
      var step = parseFloat(group.getAttribute('data-amk-stagger')) || 0.08;
      var type = group.getAttribute('data-amk-stagger-type') || '';
      Array.prototype.forEach.call(group.children, function (child, i) {
        if (!child.hasAttribute('data-amk-reveal')) child.setAttribute('data-amk-reveal', type);
        child.style.setProperty('--amk-delay', (i * step).toFixed(2) + 's');
      });
    });

    var revealEls = $$('[data-amk-reveal], [data-amk-split], [data-amk-rise], .amk-steps');
    if ('IntersectionObserver' in window && !reduceMotion) {
      // Een volledig weggeknipt element (clip-reveal) telt voor de browser
      // nooit als zichtbaar; daarom observeren we dan de ouder.
      var watched = new Map();
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          (watched.get(entry.target) || []).forEach(function (el) {
            el.classList.add(el.hasAttribute('data-amk-rise') ? 'is-risen' : 'is-visible');
          });
          watched.delete(entry.target);
          io.unobserve(entry.target);
        });
      }, { rootMargin: '0px 0px -10% 0px', threshold: 0.12 });
      revealEls.forEach(function (el) {
        var target = el.getAttribute('data-amk-reveal') === 'clip' && el.parentElement ? el.parentElement : el;
        if (!watched.has(target)) {
          watched.set(target, []);
          io.observe(target);
        }
        watched.get(target).push(el);
      });
    } else {
      revealEls.forEach(function (el) {
        el.classList.add('is-visible');
        el.classList.add('is-risen');
      });
    }

    // Paginahero: zon in de eyebrow meteen laten opkomen
    $$('.amk-pagehero').forEach(function (h) {
      window.requestAnimationFrame(function () { h.classList.add('is-loaded'); });
    });

    /* ------------------------------------------------------------------
       8. Parallax
       data-amk-parallax="0.1" (positief = trager dan scrollen)
       Gebruikt de `translate`-eigenschap, zodat CSS-animaties op
       `transform` gewoon blijven werken.
       ------------------------------------------------------------------ */
    if (!reduceMotion) {
      var parallaxEls = $$('[data-amk-parallax]').map(function (el) {
        return {
          el: el,
          speed: parseFloat(el.getAttribute('data-amk-parallax')) || 0.1,
          // Foto's binnen een kader hebben maar een kleine reserve-rand:
          // daar blijft de verschuiving binnen 5% van de hoogte (geen lege randen)
          framed: el.tagName === 'IMG' || el.classList.contains('amk-tile__img'),
          shift: 0,
          active: true
        };
      });

      if (parallaxEls.length) {
        if ('IntersectionObserver' in window) {
          var pio = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
              parallaxEls.forEach(function (p) {
                if (p.el === entry.target) p.active = entry.isIntersecting;
              });
            });
            requestScroll();
          }, { rootMargin: '20% 0px 20% 0px' });
          parallaxEls.forEach(function (p) { pio.observe(p.el); });
        }

        onScroll(function () {
          var vh = window.innerHeight;
          parallaxEls.forEach(function (p) {
            if (!p.active) return;
            var r = p.el.getBoundingClientRect();
            // Positie zonder de huidige verschuiving, anders stapelt het effect op
            var center = r.top - p.shift + r.height / 2 - vh / 2;
            var max = p.framed ? r.height * 0.05 : 160;
            p.shift = clamp(-center * p.speed, -max, max);
            p.el.style.translate = '0 ' + p.shift.toFixed(1) + 'px';
          });
        });
      }
    }

    /* ------------------------------------------------------------------
       9. Tilt, spotlight en magnetische knoppen (enkel met muis)
       ------------------------------------------------------------------ */
    if (finePointer && !reduceMotion) {
      $$('[data-amk-tilt], .amk-spot, .amk-tile').forEach(function (card) {
        var max = parseFloat(card.getAttribute('data-amk-tilt')) || 0;
        var raf = null;

        card.addEventListener('pointermove', function (e) {
          if (raf) return;
          raf = window.requestAnimationFrame(function () {
            raf = null;
            var r = card.getBoundingClientRect();
            var px = (e.clientX - r.left) / r.width;
            var py = (e.clientY - r.top) / r.height;
            card.style.setProperty('--amk-mx', (px * 100).toFixed(1) + '%');
            card.style.setProperty('--amk-my', (py * 100).toFixed(1) + '%');
            if (max) {
              card.classList.add('is-tilting');
              card.style.setProperty('--amk-rx', ((0.5 - py) * max).toFixed(2) + 'deg');
              card.style.setProperty('--amk-ry', ((px - 0.5) * max).toFixed(2) + 'deg');
            }
          });
        });

        card.addEventListener('pointerleave', function () {
          card.classList.remove('is-tilting');
          card.style.setProperty('--amk-rx', '0deg');
          card.style.setProperty('--amk-ry', '0deg');
        });
      });

      $$('[data-amk-magnetic]').forEach(function (btn) {
        btn.addEventListener('pointermove', function (e) {
          var r = btn.getBoundingClientRect();
          var dx = (e.clientX - (r.left + r.width / 2)) / r.width;
          var dy = (e.clientY - (r.top + r.height / 2)) / r.height;
          btn.style.setProperty('--amk-bx', (dx * 10).toFixed(1) + 'px');
          btn.style.setProperty('--amk-by', (dy * 8).toFixed(1) + 'px');
        });
        btn.addEventListener('pointerleave', function () {
          btn.style.setProperty('--amk-bx', '0px');
          btn.style.setProperty('--amk-by', '0px');
        });
      });
    }

    /* ------------------------------------------------------------------
       10. Sintels + cursorlicht
       data-amk-embers="16" op een container met class .amk-embers
       ------------------------------------------------------------------ */
    if (!reduceMotion) {
      $$('[data-amk-embers]').forEach(function (box) {
        var n = parseInt(box.getAttribute('data-amk-embers'), 10) || 14;
        if (window.innerWidth < 700) n = Math.ceil(n / 2);
        for (var i = 0; i < n; i++) {
          var s = doc.createElement('span');
          s.className = 'amk-ember';
          s.style.setProperty('--x', (Math.random() * 100).toFixed(1) + '%');
          s.style.setProperty('--s', (2 + Math.random() * 4).toFixed(1) + 'px');
          s.style.setProperty('--d', (9 + Math.random() * 10).toFixed(1) + 's');
          s.style.setProperty('--delay', (-Math.random() * 18).toFixed(1) + 's');
          s.style.setProperty('--sway', ((Math.random() - 0.5) * 120).toFixed(0) + 'px');
          s.style.setProperty('--o', (0.35 + Math.random() * 0.55).toFixed(2));
          box.appendChild(s);
        }
      });
    }

    if (finePointer && !reduceMotion) {
      $$('[data-amk-light]').forEach(function (area) {
        var raf = null;
        area.addEventListener('pointermove', function (e) {
          if (raf) return;
          raf = window.requestAnimationFrame(function () {
            raf = null;
            var r = area.getBoundingClientRect();
            area.style.setProperty('--amk-px', (e.clientX - r.left) + 'px');
            area.style.setProperty('--amk-py', (e.clientY - r.top) + 'px');
          });
        });
      });
    }

    /* ------------------------------------------------------------------
       11. Tellers: data-amk-count op een element met een getal
       ------------------------------------------------------------------ */
    var counters = $$('[data-amk-count]');
    function runCount(el) {
      var target = parseInt(el.textContent.replace(/[^\d]/g, ''), 10);
      if (!target || reduceMotion) return;
      var start = null;
      var dur = 1400;
      el.textContent = '0';
      function step(t) {
        if (!start) start = t;
        var p = Math.min(1, (t - start) / dur);
        var eased = 1 - Math.pow(1 - p, 3);
        el.textContent = String(Math.round(target * eased));
        if (p < 1) window.requestAnimationFrame(step);
      }
      window.requestAnimationFrame(step);
    }
    if (counters.length && 'IntersectionObserver' in window) {
      var cio = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          runCount(entry.target);
          cio.unobserve(entry.target);
        });
      }, { threshold: 0.6 });
      counters.forEach(function (el) { cio.observe(el); });
    }

    /* ------------------------------------------------------------------
       12. Tabs (toegankelijk: pijltjestoetsen + aria)
       ------------------------------------------------------------------ */
    $$('[data-amk-tabs]').forEach(function (tablist) {
      var tabs = $$('[role="tab"]', tablist);

      function activate(index, focus) {
        tabs.forEach(function (tab, i) {
          var selected = i === index;
          var panel = doc.getElementById(tab.getAttribute('aria-controls'));
          tab.setAttribute('aria-selected', selected ? 'true' : 'false');
          tab.setAttribute('tabindex', selected ? '0' : '-1');
          if (!panel) return;
          panel.hidden = !selected;
          if (selected) {
            var kids = $$('[data-amk-reveal]', panel);
            kids.forEach(function (el) { el.classList.remove('is-visible'); });
            window.requestAnimationFrame(function () {
              window.requestAnimationFrame(function () {
                kids.forEach(function (el) { el.classList.add('is-visible'); });
              });
            });
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

    /* ------------------------------------------------------------------
       13. FAQ: vloeiend openen/sluiten, één vraag tegelijk open
       Structuur: <details class="amk-faq__item"><summary>…</summary>
                  <div class="amk-faq__answer"><div>…</div></div></details>
       ------------------------------------------------------------------ */
    $$('[data-amk-accordion]').forEach(function (list) {
      var items = $$('details', list);

      function animate(item, open) {
        var panel = item.querySelector('.amk-faq__answer');
        item._amkOpen = open;
        if (!panel || reduceMotion || !panel.animate) {
          item.open = open;
          return;
        }
        if (item._amkAnim) item._amkAnim.cancel();
        var startH = open ? 0 : panel.offsetHeight;
        if (open) item.open = true;
        var endH = open ? panel.scrollHeight : 0;
        var anim = panel.animate(
          [{ height: startH + 'px', opacity: open ? 0 : 1 }, { height: endH + 'px', opacity: open ? 1 : 0 }],
          { duration: 450, easing: 'cubic-bezier(0.2, 0.7, 0.2, 1)' }
        );
        item._amkAnim = anim;
        anim.onfinish = function () {
          item._amkAnim = null;
          if (!open) item.open = false;
        };
      }

      items.forEach(function (item) {
        var summary = item.querySelector('summary');
        if (!summary) return;
        summary.addEventListener('click', function (e) {
          e.preventDefault();
          // Gewenste toestand bijhouden, ook tijdens een lopende animatie
          var isOpen = typeof item._amkOpen === 'boolean' ? item._amkOpen : item.open;
          var willOpen = !isOpen;
          items.forEach(function (other) {
            if (other !== item && other.open && other._amkOpen !== false) animate(other, false);
          });
          animate(item, willOpen);
        });
      });
    });

    /* ------------------------------------------------------------------
       14. Galerij-lightbox
       <a href="groot.jpg" data-amk-gallery="naam" data-caption="…"><img></a>
       ------------------------------------------------------------------ */
    var galleryLinks = $$('[data-amk-gallery]');
    if (galleryLinks.length) {
      var box = doc.createElement('div');
      box.className = 'amk-lightbox';
      box.setAttribute('role', 'dialog');
      box.setAttribute('aria-modal', 'true');
      box.setAttribute('aria-label', 'Foto vergroot');
      box.innerHTML =
        '<button class="amk-lightbox__btn amk-lightbox__close" type="button" aria-label="Sluiten">' +
          '<svg class="amk-icon" aria-hidden="true"><use href="#amk-i-close"/></svg></button>' +
        '<img class="amk-lightbox__img" alt="">' +
        '<div class="amk-lightbox__bar">' +
          '<button class="amk-lightbox__btn" type="button" data-dir="-1" aria-label="Vorige foto">' +
            '<svg class="amk-icon" aria-hidden="true" style="rotate:180deg"><use href="#amk-i-arrow"/></svg></button>' +
          '<span class="amk-lightbox__count" aria-live="polite"></span>' +
          '<button class="amk-lightbox__btn" type="button" data-dir="1" aria-label="Volgende foto">' +
            '<svg class="amk-icon" aria-hidden="true"><use href="#amk-i-arrow"/></svg></button>' +
        '</div>';
      (doc.querySelector('.amk') || doc.body).appendChild(box);

      var img = box.querySelector('.amk-lightbox__img');
      var count = box.querySelector('.amk-lightbox__count');
      var closeBtn = box.querySelector('.amk-lightbox__close');
      var index = 0;
      var lastFocus = null;

      function show(i) {
        index = (i + galleryLinks.length) % galleryLinks.length;
        var link = galleryLinks[index];
        var thumb = link.querySelector('img');
        img.classList.add('is-switching');
        var next = new Image();
        next.onload = next.onerror = function () {
          img.src = link.getAttribute('href');
          img.alt = thumb ? thumb.alt : '';
          img.classList.remove('is-switching');
        };
        next.src = link.getAttribute('href');
        count.textContent = (index + 1) + ' / ' + galleryLinks.length +
          (link.getAttribute('data-caption') ? ' — ' + link.getAttribute('data-caption') : '');
      }

      function open(i) {
        lastFocus = doc.activeElement;
        show(i);
        box.classList.add('is-open');
        root.classList.add('amk-lock');
        window.setTimeout(function () { closeBtn.focus(); }, 50);
      }

      function close() {
        box.classList.remove('is-open');
        root.classList.remove('amk-lock');
        if (lastFocus) lastFocus.focus();
      }

      galleryLinks.forEach(function (link, i) {
        link.addEventListener('click', function (e) {
          e.preventDefault();
          open(i);
        });
      });

      box.addEventListener('click', function (e) {
        var dirBtn = e.target.closest('[data-dir]');
        if (dirBtn) show(index + parseInt(dirBtn.getAttribute('data-dir'), 10));
        else if (e.target.closest('.amk-lightbox__close') || e.target === box) close();
      });

      doc.addEventListener('keydown', function (e) {
        if (!box.classList.contains('is-open')) return;
        if (e.key === 'Escape') close();
        if (e.key === 'ArrowRight') show(index + 1);
        if (e.key === 'ArrowLeft') show(index - 1);
        if (e.key === 'Tab') {
          // Focus binnen de lightbox houden
          var f = $$('button', box);
          var first = f[0], last = f[f.length - 1];
          if (e.shiftKey && doc.activeElement === first) { e.preventDefault(); last.focus(); }
          else if (!e.shiftKey && doc.activeElement === last) { e.preventDefault(); first.focus(); }
        }
      });

      // Swipen op touchscreens
      var touchX = null;
      box.addEventListener('touchstart', function (e) { touchX = e.touches[0].clientX; }, { passive: true });
      box.addEventListener('touchend', function (e) {
        if (touchX === null) return;
        var dx = e.changedTouches[0].clientX - touchX;
        if (Math.abs(dx) > 50) show(index + (dx < 0 ? 1 : -1));
        touchX = null;
      });
    }

    /* ------------------------------------------------------------------
       15. Mobiele CTA-balk: verschijnt zodra de hero uit beeld is
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
      bar.setAttribute('aria-hidden', 'false');
    }

    /* ------------------------------------------------------------------
       16. Terug naar boven + jaartal
       ------------------------------------------------------------------ */
    $$('[data-amk-totop]').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
      });
    });

    $$('[data-amk-year]').forEach(function (el) {
      el.textContent = new Date().getFullYear();
    });

    // Start
    window.addEventListener('scroll', requestScroll, { passive: true });
    window.addEventListener('resize', requestScroll);
    runScroll();
  });
})();
