/**
 * Melodia Magical Girl Layer — tiered chrome (full / soft / chrome / off).
 * Wish overlays are opt-in via the bow toggle (full + soft only).
 */
(function (global) {
  'use strict';

  var TIERS = { full: 1, soft: 1, chrome: 1, off: 1 };

  function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function resolveTier(shell) {
    var explicit = (shell.getAttribute('data-mg') || '').toLowerCase();
    if (TIERS[explicit]) return explicit;

    if (shell.classList.contains('game-mode')) return 'off';
    if (shell.getAttribute('data-hero') === 'cosmic') return 'full';
    if (shell.classList.contains('fashion-mode')) return 'soft';
    return 'chrome';
  }

  function contractRingSvg() {
    var ticks = Array.from({ length: 24 }, function (_, i) {
      var a = (i / 24) * Math.PI * 2;
      var x1 = 210 + Math.cos(a) * 168;
      var y1 = 210 + Math.sin(a) * 168;
      var x2 = 210 + Math.cos(a) * 182;
      var y2 = 210 + Math.sin(a) * 182;
      return '<line class="tick" x1="' + x1.toFixed(1) + '" y1="' + y1.toFixed(1) +
        '" x2="' + x2.toFixed(1) + '" y2="' + y2.toFixed(1) + '" />';
    }).join('');
    return (
      '<svg viewBox="0 0 420 420" aria-hidden="true">' +
      '<circle cx="210" cy="210" r="178" />' +
      '<circle class="inner" cx="210" cy="210" r="132" />' +
      '<circle class="inner" cx="210" cy="210" r="88" />' +
      ticks +
      '</svg>'
    );
  }

  function mount(shell) {
    if (!shell || shell.querySelector(':scope > .mg-layer')) return;

    var tier = resolveTier(shell);
    shell.setAttribute('data-mg', tier);
    if (tier === 'off') return;

    shell.classList.add('mg-ui-chrome', 'mg-tier-' + tier);

    var nav = shell.querySelector('.shell-nav');
    if (nav) nav.classList.add('mg-nav-chrome');

    var layer = document.createElement('div');
    layer.className = 'mg-layer is-hidden';
    layer.setAttribute('aria-hidden', 'true');
    layer.innerHTML =
      '<div class="mg-halftone" aria-hidden="true"></div>' +
      '<div class="mg-wish-stage" aria-hidden="true">' +
      '<div class="mg-contract-ring" aria-hidden="true">' + contractRingSvg() + '</div>' +
      '<div class="mg-shards" aria-hidden="true">' +
      '<div class="mg-shard s1"></div><div class="mg-shard s2"></div><div class="mg-shard s3"></div>' +
      '</div></div>';
    shell.appendChild(layer);

    if (tier === 'full' || tier === 'soft') {
      shell.classList.add('mg-ambient');
      layer.classList.remove('is-hidden');

      // Corner crystals + band ribbon trails (Magical Girl details)
      ['c1', 'c2', 'c3', 'c4'].forEach(function (cls) {
        var crystal = document.createElement('span');
        crystal.className = 'mg-crystal ' + cls;
        crystal.setAttribute('aria-hidden', 'true');
        layer.appendChild(crystal);
      });

      shell.querySelectorAll('.band.astral, .band.stage-character-band, .hero, #portals').forEach(function (band, i) {
        if (band.querySelector(':scope > .mg-ribbon-trail')) return;
        band.style.position = band.style.position || 'relative';
        var t1 = document.createElement('span');
        t1.className = 'mg-ribbon-trail t1';
        t1.setAttribute('aria-hidden', 'true');
        var t2 = document.createElement('span');
        t2.className = 'mg-ribbon-trail t2';
        t2.setAttribute('aria-hidden', 'true');
        if (i % 2 === 1) t2.style.animationDelay = '2.4s';
        band.appendChild(t1);
        band.appendChild(t2);
      });
    }

    var allowWish = tier === 'full' || tier === 'soft';
    var toggle = null;

    if (allowWish) {
      toggle = document.createElement('button');
      toggle.className = 'mg-bow-toggle';
      toggle.type = 'button';
      toggle.setAttribute('aria-label', 'Toggle wish-mode UI accents');
      toggle.setAttribute('aria-pressed', 'false');
      toggle.innerHTML =
        '<svg viewBox="0 0 44 44" aria-hidden="true">' +
        '<path class="bow-fill" d="M8 22 C 8 14, 16 10, 22 14 C 28 10, 36 14, 36 22 C 36 30, 28 34, 22 30 C 16 34, 8 30, 8 22 Z" />' +
        '<path class="bow-fill" d="M14 22 C 10 20, 10 24, 14 22" opacity="0.5" />' +
        '<path class="bow-fill" d="M30 22 C 34 20, 34 24, 30 22" opacity="0.5" />' +
        '<circle class="bow-knot" cx="22" cy="22" r="2.8" />' +
        '<path class="bow-fill" d="M22 19 L22 25" opacity="0.6" stroke-width="0.8" />' +
        '</svg>';
      document.body.appendChild(toggle);

      var on = false;
      var root = document.documentElement;
      var apply = function () {
        toggle.setAttribute('aria-pressed', on ? 'true' : 'false');
        if (on) {
          layer.classList.remove('is-hidden');
          layer.classList.add('is-wish');
          shell.classList.add('mg-wish-mode');
          toggle.classList.add('is-wish');
          root.style.setProperty('--dream-sparkle-density', '1.18');
          root.style.setProperty('--dream-hue-shift', '6deg');
          if (global.MelodiaStarfield) global.MelodiaStarfield.setIntensity('cosmic');
        } else {
          if (tier !== 'full' && tier !== 'soft') layer.classList.add('is-hidden');
          else layer.classList.remove('is-hidden');
          layer.classList.remove('is-wish');
          shell.classList.remove('mg-wish-mode');
          toggle.classList.remove('is-wish');
          root.style.setProperty('--dream-sparkle-density', '0.88');
          root.style.setProperty('--dream-hue-shift', '0deg');
          if (global.MelodiaStarfield) {
            var heroType = shell.getAttribute('data-hero');
            global.MelodiaStarfield.setIntensity(heroType === 'cosmic' ? 'cosmic' : 'standard');
          }
        }
      };

      toggle.addEventListener('click', function () {
        on = !on;
        apply();
      });
      apply();
    }

    // Interactive cards + stage plate strip
    document.querySelectorAll('.portal-card, .path-row, .guide-card, .stage-plate-grid a').forEach(function (el) {
      el.classList.add('mg-ribbon-card');
    });

    if (!prefersReducedMotion() && (tier === 'full' || tier === 'soft')) {
      var onMove = function (e) {
        var mx = (e.clientX / window.innerWidth - 0.5) * 14;
        var my = (e.clientY / window.innerHeight - 0.5) * 10;
        document.documentElement.style.setProperty('--mouse-x', mx + 'px');
        document.documentElement.style.setProperty('--mouse-y', my + 'px');
      };
      window.addEventListener('pointermove', onMove, { passive: true });
    }
  }

  function boot() {
    var shell = document.querySelector('.melodia-shell');
    if (!shell) return;
    mount(shell);
  }

  global.MelodiaMagicalGirl = { boot: boot, mount: mount, resolveTier: resolveTier };
})(window);
