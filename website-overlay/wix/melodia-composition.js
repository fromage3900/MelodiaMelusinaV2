/**
 * Reversible composition variants for the Melodia portfolio.
 * Default remains current (A). Quiet (B) and Constellation (C) are opt-in.
 */
(function (global) {
  'use strict';

  var STORAGE_KEY = 'melodia.composition.v1';
  var ATTR = 'data-composition';
  var VALID = { current: 1, quiet: 1, constellation: 1 };
  var ALIAS = { museum: 'quiet', pearl: 'constellation', a: 'current', b: 'quiet', c: 'constellation' };
  var LABELS = [
    { id: 'current', label: 'Current' },
    { id: 'quiet', label: 'Quiet' },
    { id: 'constellation', label: 'Constellation' }
  ];

  function reduceMotion() {
    return !!(global.matchMedia && global.matchMedia('(prefers-reduced-motion: reduce)').matches);
  }

  function normalize(value) {
    if (!value) return 'current';
    var key = String(value).toLowerCase();
    if (ALIAS[key]) key = ALIAS[key];
    return VALID[key] ? key : 'current';
  }

  function readQuery() {
    try {
      var params = new URLSearchParams(global.location.search);
      if (params.has('composition')) return normalize(params.get('composition'));
    } catch (e) {}
    return null;
  }

  function readStored() {
    try {
      return normalize(global.localStorage.getItem(STORAGE_KEY));
    } catch (e) {
      return 'current';
    }
  }

  function store(value) {
    try {
      if (value === 'current') global.localStorage.removeItem(STORAGE_KEY);
      else global.localStorage.setItem(STORAGE_KEY, value);
    } catch (e) {}
  }

  var originalIntensity = null;

  function applyEffects(value) {
    var shell = document.querySelector('.melodia-shell');
    if (!shell) return;
    if (originalIntensity === null) {
      originalIntensity = shell.getAttribute('data-starfield-intensity') || 'standard';
    }
    var next = value === 'quiet' ? 'subtle' : originalIntensity;
    shell.setAttribute('data-starfield-intensity', next);
    if (global.MelodiaStarfield && typeof global.MelodiaStarfield.setIntensity === 'function') {
      global.MelodiaStarfield.setIntensity(next);
    }
    if (global.MelodiaEffects && typeof global.MelodiaEffects.setIntensity === 'function') {
      global.MelodiaEffects.setIntensity(next);
    }
  }

  function apply(value, persist) {
    var next = normalize(value);
    document.documentElement.setAttribute(ATTR, next);
    if (reduceMotion()) document.documentElement.setAttribute('data-reduced-motion', 'true');
    else document.documentElement.removeAttribute('data-reduced-motion');
    if (persist !== false) store(next);
    applyEffects(next);
    var radios = document.querySelectorAll('.composition-switcher input[name="melodia-composition"]');
    radios.forEach(function (input) {
      input.checked = input.value === next;
      if (input.checked) input.setAttribute('checked', 'checked');
      else input.removeAttribute('checked');
    });
    return next;
  }

  function currentValue() {
    return normalize(document.documentElement.getAttribute(ATTR) || readQuery() || readStored());
  }

  function closestArt(node) {
    if (!node || !node.closest) return null;
    return node.closest(
      '.hero, .home-art-plate, .art-piece, .env-card, .image-card, .feature-frame, .curated-hero-image, canvas, .photobooth, .zbrush-stage, .melodia-3d-viewport'
    );
  }

  function closestCopy(node) {
    if (!node || !node.closest) return null;
    return node.closest('p, .lede, .human-lede, .section-head, .table-list, article, .resume, .body-copy');
  }

  function bindQuietState() {
    if (reduceMotion()) return;
    document.addEventListener('pointerover', function (event) {
      var art = closestArt(event.target);
      var copy = closestCopy(event.target);
      document.documentElement.classList.toggle('is-art-focused', !!art);
      document.documentElement.classList.toggle('is-copy-focused', !art && !!copy);
    }, { passive: true });
    document.addEventListener('focusin', function (event) {
      var art = closestArt(event.target);
      document.documentElement.classList.toggle('is-art-focused', !!art);
    });
  }

  function ensureSwitcher() {
    if (document.querySelector('.composition-switcher')) return;
    var wrap = document.createElement('details');
    wrap.className = 'composition-switcher';
    var selected = currentValue();
    var fromQuery = readQuery();
    if (selected !== 'current' || fromQuery) wrap.open = true;
    var summary = document.createElement('summary');
    summary.textContent = 'Look';
    wrap.appendChild(summary);
    var field = document.createElement('fieldset');
    field.setAttribute('aria-label', 'Composition variant');
    var row = document.createElement('div');
    row.className = 'composition-switcher-options';
    LABELS.forEach(function (item) {
      var label = document.createElement('label');
      var input = document.createElement('input');
      input.type = 'radio';
      input.name = 'melodia-composition';
      input.value = item.id;
      if (item.id === selected) input.setAttribute('checked', 'checked');
      input.checked = item.id === selected;
      input.addEventListener('change', function () {
        if (input.checked) apply(item.id, true);
      });
      label.appendChild(input);
      label.appendChild(document.createTextNode(item.label));
      row.appendChild(label);
    });
    field.appendChild(row);
    wrap.appendChild(field);
    document.body.appendChild(wrap);
  }

  function boot() {
    var fromQuery = readQuery();
    apply(fromQuery || readStored(), !fromQuery);
    bindQuietState();
    ensureSwitcher();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  global.MelodiaComposition = {
    apply: apply,
    current: currentValue
  };
})(typeof window !== 'undefined' ? window : this);
