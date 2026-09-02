/**
 * Melodia Dream Shaders — aurora wash, holo plates, fresnel vars (no starfield).
 */
(function (global) {
  'use strict';

  let dreamBooted = false;

  function mountDreamLayers() {
    document.querySelectorAll('.melodia-shell').forEach((shell) => {
      if (shell.querySelector(':scope > .dream-aurora-layer')) return;

      const aurora = document.createElement('div');
      aurora.className = 'dream-aurora-layer';
      aurora.setAttribute('aria-hidden', 'true');

      const sparkle = document.createElement('div');
      sparkle.className = 'dream-sparkle-layer';
      sparkle.setAttribute('aria-hidden', 'true');

      const planet = document.createElement('div');
      planet.className = 'dream-planet-layer';
      planet.setAttribute('aria-hidden', 'true');

      const bubbles = document.createElement('div');
      bubbles.className = 'figma-bubble-layer';
      bubbles.setAttribute('aria-hidden', 'true');

      shell.insertBefore(bubbles, shell.firstChild);
      shell.insertBefore(planet, shell.firstChild);
      shell.insertBefore(sparkle, shell.firstChild);
      shell.insertBefore(aurora, shell.firstChild);
    });
  }

  function detectPillar(card) {
    const blob = `${card.textContent || ''} ${card.querySelector('img')?.src || ''} ${card.querySelector('img')?.alt || ''}`.toLowerCase();
    if (/sakura|sakuradream|meadowbloom/.test(blob)) return 'sakura';
    if (/cathedral|celestial|spacecathedral|kaleidonave|kaleido|hoshi|nebula.*nasa/.test(blob)) return 'cathedral';
    if (/melusina|melusinamorning|melusinasmorning|atelier|stage|character/.test(blob)) return 'melusina';
    /* Orrery pillar is separate from L_FallenMoon (World 04) — do not collapse */
    if (/orrery|cosmicorrery|cosmic.?orrery/.test(blob) && !/fallenmoon|fallen.?moon|crater/.test(blob)) {
      return 'orrery';
    }
    if (/fallenmoon|fallen.?moon|crater|\bmoon\b/.test(blob)) return 'fallenmoon';
    return null;
  }

  function applyPillarTag(el, pillar) {
    if (!pillar || el.dataset.pillar) return;
    el.dataset.pillar = pillar;
  }

  const IRI_SHEEN_TARGETS = [
    '.card',
    '.premium-card',
    '.component-card',
    '.image-card',
    '.image-plate',
    '.world-card',
    '.portal-card',
    '.path-row',
    '.guide-card',
    '.breakdown-card',
    '.material-card',
    '.figma-swatch-card',
    '.figma-card-preview',
    '.figma-icon-item',
    '.viz-plate',
    '.viz-door',
    '.toolchain-card',
    '.passport-card',
    '.loop-stage-card',
    '.game-ui-frame',
    '.stage-plate-frame',
    '.stage-depth-tilt',
    '.stage-plate-grid > a',
    '.atelier-viewport-card',
    '.atelier-control-card',
    '.atelier-world-card',
    '.photobooth-container',
    '.photobooth-viewport',
    '.zbrush-studio-container',
    '.zbrush-viewport',
    '.hero-macro-plate',
    '.env-card',
    '.env-thumb',
    '.env-showcase a',
    '.hero-actions .button',
    '.table-row',
    '.alignment-card',
  ].join(',');

  function initIriSheenFrames() {
    document.querySelectorAll(`.melodia-shell ${IRI_SHEEN_TARGETS}`).forEach((frame) => {
      if (frame.querySelector(':scope > .melodia-iri-sheen')) return;

      frame.classList.add('melodia-iri-frame');
      const sheen = document.createElement('span');
      sheen.className = 'melodia-iri-sheen';
      sheen.setAttribute('aria-hidden', 'true');
      frame.appendChild(sheen);
    });
  }

  let gachaObserver = null;
  const gachaSeen = new WeakSet();

  function ensureGachaObserver() {
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (reduceMotion.matches || !('IntersectionObserver' in window)) return;
    if (gachaObserver) return;
    gachaObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting || entry.intersectionRatio < 0.35) return;
          const card = entry.target;
          if (gachaSeen.has(card)) return;
          gachaSeen.add(card);
          card.classList.add('is-gacha-in');
          window.setTimeout(() => card.classList.remove('is-gacha-in'), 1600);
          gachaObserver.unobserve(card);
        });
      },
      { threshold: [0, 0.35, 0.6], rootMargin: '0px 0px -8% 0px' }
    );
  }

  function initHoloPlates() {
    const shell = document.querySelector('.melodia-shell');
    if (!shell) return;

    ensureGachaObserver();

    shell.querySelectorAll('.image-card').forEach((card) => {
      if (!card.querySelector('img') || card.classList.contains('holo-plate')) return;
      card.classList.add('holo-plate');
      const pillar = detectPillar(card);
      applyPillarTag(card, pillar);
      if (gachaObserver) gachaObserver.observe(card);
    });

    // Stage character plates — thin-film sweep on tilt hero + strip
    shell.querySelectorAll('.stage-depth-tilt, .stage-plate-grid a').forEach((card) => {
      if (!card.classList.contains('holo-plate')) card.classList.add('holo-plate');
      if (gachaObserver && card.matches('.stage-plate-grid a')) gachaObserver.observe(card);
    });

    shell.querySelectorAll('.card.world-card-large').forEach((card) => {
      const pillar = detectPillar(card);
      applyPillarTag(card, pillar);
    });

    initIriSheenFrames();
  }

  function initWorldCardRims() {
    document.querySelectorAll('.melodia-shell .world-card').forEach((card) => {
      if (card.querySelector(':scope > .holo-rim')) return;
      const rim = document.createElement('span');
      rim.className = 'holo-rim';
      rim.setAttribute('aria-hidden', 'true');
      card.insertBefore(rim, card.firstChild);
      const pillarMap = {
        sakura: 'sakura',
        cathedral: 'cathedral',
        kaleidonave: 'cathedral',
        melusina: 'melusina',
        melusinamorning: 'melusina',
        castle: 'melusina',
        grotto: 'fallenmoon',
        fallenmoon: 'fallenmoon',
        orrery: 'orrery'
      };
      Object.keys(pillarMap).forEach((cls) => {
        if (card.classList.contains(cls)) applyPillarTag(card, pillarMap[cls]);
      });
      card.addEventListener(
        'pointerenter',
        () => {
          const shellEl = card.closest('.melodia-shell');
          if (shellEl && card.dataset.pillar) shellEl.dataset.pillar = card.dataset.pillar;
        },
        { passive: true }
      );
    });
  }

  function initScrollFresnel() {
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (reduceMotion.matches) return;
    const root = document.documentElement;
    let ticking = false;
    const onScroll = () => {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(() => {
        const max = Math.max(document.documentElement.scrollHeight - window.innerHeight, 1);
        const p = (window.scrollY || 0) / max;
        const fresnel = 0.22 + p * 0.28 + Math.abs(0.5 - (parseFloat(root.style.getPropertyValue('--dream-mouse-x')) || 0.5)) * 0.12;
        root.style.setProperty('--dream-fresnel', fresnel.toFixed(3));
        ticking = false;
      });
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  function bindHoloPointer(shell) {
    if (!shell || shell.dataset.holoBound) return;
    shell.dataset.holoBound = '1';
    shell.addEventListener(
      'pointermove',
      (event) => {
        const card = event.target.closest('.image-card.holo-plate, .world-card, .stage-depth-tilt.holo-plate, .stage-plate-grid a.holo-plate');
        if (!card) return;
        const rect = card.getBoundingClientRect();
        const x = (event.clientX - rect.left) / Math.max(rect.width, 1);
        const y = (event.clientY - rect.top) / Math.max(rect.height, 1);
        card.style.setProperty('--holo-x', x.toFixed(4));
        card.style.setProperty('--holo-y', y.toFixed(4));
      },
      { passive: true }
    );
  }

  function bindDreamMouse() {
    const root = document.documentElement;
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    let ticking = false;
    let mouseNX = 0.42;
    let mouseNY = 0.38;

    const setVars = (x, y) => {
      const nx = Math.max(0, Math.min(1, x));
      const ny = Math.max(0, Math.min(1, y));
      root.style.setProperty('--dream-mouse-x', String(nx));
      root.style.setProperty('--dream-mouse-y', String(ny));
      mouseNX = nx;
      mouseNY = ny;
      const fresnel = 0.22 + (1 - ny) * 0.28 + Math.abs(nx - 0.5) * 0.2;
      root.style.setProperty('--dream-fresnel', fresnel.toFixed(3));
    };

    const onMove = (event) => {
      if (reduceMotion.matches) return;
      if (!ticking) {
        window.requestAnimationFrame(() => {
          setVars(event.clientX / window.innerWidth, event.clientY / window.innerHeight);
          ticking = false;
        });
        ticking = true;
      }
    };

    setVars(0.42, 0.38);
    window.addEventListener('pointermove', onMove, { passive: true });
  }

  function initDreamShaders() {
    if (dreamBooted) return;
    dreamBooted = true;

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    mountDreamLayers();
    bindDreamMouse();

    const shellEl = document.querySelector('.melodia-shell');
    if (shellEl) {
      shellEl.dataset.dreamIntensity = reduceMotion.matches ? 'low' : 'standard';
      if (reduceMotion.matches) shellEl.classList.add('dream-reduced');
    }

    initHoloPlates();
    initIriSheenFrames();
    initWorldCardRims();
    initScrollFresnel();
    bindHoloPointer(shellEl);

    if (typeof MutationObserver !== 'undefined' && shellEl) {
      let holoTimer = null;
      const mo = new MutationObserver(() => {
        window.clearTimeout(holoTimer);
        holoTimer = window.setTimeout(() => {
          initHoloPlates();
          initIriSheenFrames();
        }, 150);
      });
      mo.observe(shellEl, { childList: true, subtree: true });
    }
  }

  global.MelodiaDreamShaders = {
    init: initDreamShaders,
    mountDreamLayers,
    initHoloPlates,
    initIriSheenFrames,
    initWorldCardRims,
    detectPillar,
  };
})(window);
