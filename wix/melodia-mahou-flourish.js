/**
 * Melodia Mahou Flourish — Sailor Moon & Madoka Magica Transformation Lookbook System
 * Standalone module providing sacred geometry sigil overlays, unfurling ribbons,
 * interactive pointer stardust trails, and radiant henshin transformation bursts.
 *
 * Interface contract:
 * window.MelodiaMahouFlourish = { init, trigger, burst, mount, mountHeroFlourish, triggerHenshin }
 */
(function (global) {
  'use strict';

  var activeParticles = 0;
  var MAX_TRAIL_PARTICLES = 16;
  var lastTrailTime = 0;
  var TRAIL_THROTTLE_MS = 55;

  function prefersReducedMotion() {
    return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function createSigilSvg() {
    // 24 radial rune tick marks around the outer perimeter
    var ticks = Array.from({ length: 24 }, function (_, i) {
      var a = (i / 24) * Math.PI * 2;
      var x1 = (250 + Math.cos(a) * 208).toFixed(1);
      var y1 = (250 + Math.sin(a) * 208).toFixed(1);
      var x2 = (250 + Math.cos(a) * 224).toFixed(1);
      var y2 = (250 + Math.sin(a) * 224).toFixed(1);
      return '<line class="mahou-tick" x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 + '" />';
    }).join('');

    // 8 radial starburst coordinates for 8-pointed star
    var outerStarPoints = [];
    var innerStarPoints = [];
    for (var i = 0; i < 16; i++) {
      var angle = (i / 16) * Math.PI * 2 - Math.PI / 2;
      var rOuter = i % 2 === 0 ? 190 : 85;
      var rInner = i % 2 === 0 ? 135 : 60;
      outerStarPoints.push((250 + Math.cos(angle) * rOuter).toFixed(1) + ',' + (250 + Math.sin(angle) * rOuter).toFixed(1));
      innerStarPoints.push((250 + Math.cos(angle) * rInner).toFixed(1) + ',' + (250 + Math.sin(angle) * rInner).toFixed(1));
    }

    return (
      '<svg class="mahou-sigil-svg" viewBox="0 0 500 500" aria-hidden="true">' +
      '<circle class="mahou-ring outer" cx="250" cy="250" r="236" />' +
      '<circle class="mahou-ring mid" cx="250" cy="250" r="195" />' +
      '<circle class="mahou-ring inner" cx="250" cy="250" r="140" />' +
      '<circle class="mahou-ring core" cx="250" cy="250" r="48" />' +
      '<polygon class="mahou-starburst" points="' + outerStarPoints.join(' ') + '" />' +
      '<polygon class="mahou-starburst-inner" points="' + innerStarPoints.join(' ') + '" />' +
      '<path class="mahou-crescent" d="M250,210 A40,40 0 0,0 250,290 A30,30 0 0,1 250,210 Z" />' +
      ticks +
      '</svg>'
    );
  }

  function mountHeroFlourish(container) {
    var target = container || document.querySelector('[data-mahou-stage]') || document.querySelector('.hero');
    if (!target || target.querySelector(':scope > .mahou-flourish-stage')) return null;

    var computedStyle = window.getComputedStyle(target);
    if (computedStyle.position === 'static') {
      target.style.position = 'relative';
    }

    var stage = document.createElement('div');
    stage.className = 'mahou-flourish-stage';
    stage.setAttribute('aria-hidden', 'true');
    stage.innerHTML =
      '<div class="mahou-lens-flare"></div>' +
      '<div class="mahou-sigil-ring">' + createSigilSvg() + '</div>' +
      '<div class="mahou-ribbon-spiral r1"></div>' +
      '<div class="mahou-ribbon-spiral r2"></div>' +
      '<div class="mahou-sparks">' +
        '<span class="mahou-spark s1">✦</span>' +
        '<span class="mahou-spark s2">✧</span>' +
        '<span class="mahou-spark s3">✦</span>' +
        '<span class="mahou-spark s4">✧</span>' +
      '</div>';

    target.appendChild(stage);

    window.requestAnimationFrame(function () {
      stage.classList.add('is-active', 'is-mounted');
    });

    return stage;
  }

  function triggerHenshin(target) {
    if (prefersReducedMotion()) return;

    var host = target || document.querySelector('[data-mahou-stage]') || document.querySelector('.hero') || document.body;
    var burstEl = document.createElement('div');
    burstEl.className = 'mahou-henshin-burst';
    burstEl.setAttribute('aria-hidden', 'true');

    var shardElements = '';
    var glyphs = ['✦', '✧', '⋆', '♪', '✧', '✦', '⋆', '✧'];
    for (var i = 0; i < 8; i++) {
      var a = (i / 8) * Math.PI * 2;
      var dist = 90 + Math.random() * 50;
      var tx = (Math.cos(a) * dist).toFixed(1) + 'px';
      var ty = (Math.sin(a) * dist).toFixed(1) + 'px';
      shardElements += '<span class="mahou-burst-shard" style="--tx:' + tx + '; --ty:' + ty + ';">' + glyphs[i] + '</span>';
    }

    burstEl.innerHTML =
      '<div class="mahou-burst-core"></div>' +
      '<div class="mahou-burst-ring"></div>' +
      '<div class="mahou-burst-shards">' + shardElements + '</div>';

    host.appendChild(burstEl);

    setTimeout(function () {
      if (burstEl.parentNode) {
        burstEl.parentNode.removeChild(burstEl);
      }
    }, 1500);
  }

  function burst(x, y) {
    if (prefersReducedMotion()) return;

    var posX = typeof x === 'number' ? x : window.innerWidth / 2;
    var posY = typeof y === 'number' ? y : window.innerHeight / 2;

    var b = document.createElement('div');
    b.className = 'mahou-henshin-burst';
    b.setAttribute('aria-hidden', 'true');
    b.style.position = 'fixed';
    b.style.left = posX + 'px';
    b.style.top = posY + 'px';

    b.innerHTML = '<div class="mahou-burst-core"></div><div class="mahou-burst-ring"></div>';
    document.body.appendChild(b);

    setTimeout(function () {
      if (b.parentNode) {
        b.parentNode.removeChild(b);
      }
    }, 1300);
  }

  function spawnTrailSpark(x, y) {
    if (activeParticles >= MAX_TRAIL_PARTICLES || prefersReducedMotion()) return;

    activeParticles++;
    var particle = document.createElement('span');
    particle.className = 'mahou-trail-particle';
    particle.setAttribute('aria-hidden', 'true');
    particle.textContent = Math.random() > 0.5 ? '✦' : '✧';
    particle.style.left = x + 'px';
    particle.style.top = y + 'px';

    document.body.appendChild(particle);

    var cleanedUp = false;
    function cleanup() {
      if (cleanedUp) return;
      cleanedUp = true;
      if (particle.parentNode) {
        particle.parentNode.removeChild(particle);
      }
      activeParticles = Math.max(0, activeParticles - 1);
    }

    particle.addEventListener('animationend', cleanup, { once: true });
    setTimeout(cleanup, 850);
  }

  function initPointerTrails() {
    if (prefersReducedMotion()) return;

    var handleMove = function (e) {
      var now = performance.now();
      if (now - lastTrailTime < TRAIL_THROTTLE_MS) return;
      lastTrailTime = now;
      spawnTrailSpark(e.clientX, e.clientY);
    };

    window.addEventListener('pointermove', handleMove, { passive: true });
  }

  function bindInteractiveTriggers() {
    var triggers = document.querySelectorAll(
      '[data-mahou-trigger], .magazine-kicker, .hero-actions .button.primary, .brand'
    );

    triggers.forEach(function (el) {
      if (el.getAttribute('data-mahou-bound')) return;
      el.setAttribute('data-mahou-bound', 'true');

      if (el.tagName !== 'BUTTON' && el.tagName !== 'A') {
        if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '0');
        if (!el.hasAttribute('role')) el.setAttribute('role', 'button');
        if (!el.hasAttribute('aria-label')) el.setAttribute('aria-label', 'Trigger henshin flourish burst');

        el.addEventListener('keydown', function (e) {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            el.click();
          }
        });
      }

      el.addEventListener('click', function (event) {
        var stageTarget = el.closest('[data-mahou-stage]') || el.closest('.hero');
        if (stageTarget) {
          triggerHenshin(stageTarget);
        } else {
          burst(event.clientX, event.clientY);
        }
      });
    });
  }

  function init() {
    mountHeroFlourish();
    initPointerTrails();
    bindInteractiveTriggers();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  global.MelodiaMahouFlourish = {
    init: init,
    mount: mountHeroFlourish,
    mountHeroFlourish: mountHeroFlourish,
    trigger: triggerHenshin,
    triggerHenshin: triggerHenshin,
    burst: burst
  };
})(window);
