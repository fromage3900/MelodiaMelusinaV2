/**
 * Melodia shared site nav — one recruiter-path chrome for all pages.
 * Include after DOM header exists; safe to load before MelodiaEditorial.init.
 * Constellation accents activate when header has .constellation-nav or data-constellation.
 */
(function (global) {
  'use strict';

  var LINKS = [
    { href: 'index.html', label: 'Home', keys: ['index', ''] },
    { href: 'application-hub.html', label: 'Hub', keys: ['application-hub'] },
    { href: 'zbrush-breakdown.html', label: 'Breakdown', keys: ['zbrush-breakdown'] },
    { href: 'hero-renders.html', label: 'Renders', keys: ['hero-renders'] },
    { href: 'melodia-stage-character.html', label: 'Stage', keys: ['melodia-stage-character'] },
    { href: 'world-bible.html', label: 'Worlds', keys: ['world-bible'] },
    { href: 'resume.html', label: 'Resume', keys: ['resume'] },
  ];

  function pageKey() {
    var html = document.documentElement;
    if (html && html.getAttribute('data-page')) return html.getAttribute('data-page');
    var file = (location.pathname.split('/').pop() || 'index.html').replace(/\.html$/i, '');
    return file === '' || file === 'index' ? 'index' : file;
  }

  function ensureSkipLink() {
    if (document.querySelector('.skip-link')) return;
    var a = document.createElement('a');
    a.className = 'skip-link';
    a.href = '#main';
    a.textContent = 'Skip to main content';
    document.body.insertBefore(a, document.body.firstChild);
    var main = document.getElementById('main') || document.querySelector('main');
    if (main && !main.id) main.id = 'main';
  }

  function wantsConstellation(header) {
    return (
      header.classList.contains('constellation-nav') ||
      header.getAttribute('data-constellation') === 'true'
    );
  }

  function linkHtml(item, active, constellation) {
    var star = constellation
      ? '<span class="nav-star" aria-hidden="true"></span>'
      : '';
    return (
      '<a href="' +
      item.href +
      '"' +
      (active ? ' class="is-active" aria-current="page"' : '') +
      '>' +
      star +
      item.label +
      '</a>'
    );
  }

  function applyNav() {
    var header = document.querySelector('header.shell-nav');
    if (!header) return;

    var shell = document.querySelector('.melodia-shell');
    var ctaHref = (shell && shell.getAttribute('data-nav-cta')) || 'application-hub.html';
    var ctaLabel = (shell && shell.getAttribute('data-nav-cta-label')) || 'Application hub';
    var key = pageKey();
    var constellation = wantsConstellation(header);

    if (constellation) header.classList.add('constellation-nav');

    var brand = header.querySelector('.brand');
    if (brand && !brand.querySelector('.brand-mark')) {
      brand.insertAdjacentHTML('afterbegin', '<span class="brand-mark" aria-hidden="true"></span>');
    }

    var nav = header.querySelector('.nav-links');
    if (!nav) {
      nav = document.createElement('nav');
      nav.className = 'nav-links';
      nav.setAttribute('aria-label', 'Sections');
      header.appendChild(nav);
    }

    // Home keeps in-page section anchors when markup already provides them;
    // other pages get the shared recruiter link set.
    var keepLocal = key === 'index' && nav.querySelector('a[href^="#"]');
    if (!keepLocal) {
      nav.innerHTML = LINKS.map(function (item) {
        return linkHtml(item, item.keys.indexOf(key) !== -1, constellation);
      }).join('');
    } else if (constellation) {
      Array.prototype.forEach.call(nav.querySelectorAll('a'), function (a) {
        if (!a.querySelector('.nav-star')) {
          a.insertAdjacentHTML('afterbegin', '<span class="nav-star" aria-hidden="true"></span>');
        }
      });
    }

    var cta = header.querySelector('.nav-cta');
    if (!cta) {
      cta = document.createElement('a');
      header.appendChild(cta);
    }
    cta.className = 'nav-cta button-premium';
    cta.href = ctaHref;
    cta.textContent = ctaLabel;
  }

  function boot() {
    ensureSkipLink();
    applyNav();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  global.MelodiaSiteNav = { refresh: applyNav, links: LINKS };
})(typeof window !== 'undefined' ? window : this);
