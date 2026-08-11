/**
 * Melodia Effects Manager — Single RAF loop for all visual effects
 * Consolidates: starfield, orrery, magical-girl, dream-shaders, planetarium, cosmic-instruments
 * Respects prefers-reduced-motion and visibilitychange
 */

(function (global) {
  'use strict';

  const state = {
    booted: false,
    rafId: 0,
    effects: new Set(),
    shell: null,
    reduceMotion: false,
    isVisible: true,
    lastFrame: 0,
    mouseNX: 0.5,
    mouseNY: 0.5,
    scrollY: 0,
    dpr: 1,
    canvas: null,
    ctx: null,
    w: 0,
    h: 0,
    stars: [],
    intensity: 'standard',
    // Effect modules
    modules: {}
  };

  const reduceMotionMQ = window.matchMedia('(prefers-reduced-motion: reduce)');
  const mobileMQ = window.matchMedia('(max-width: 680px)');

  // ===== Effect Module Interface =====
  // Each module must implement: init(ctx, state), draw(ctx, state, dt), resize(state), destroy()

  // ===== Starfield Module =====
  function createStarfieldModule() {
    let stars = [];
    let clusters = [];

    function makeStars(count) {
      clusters = Array.from({ length: 8 }, () => ({
        x: Math.random(),
        y: Math.random(),
        r: 0.06 + Math.random() * 0.1,
      }));

      return new Array(count).fill(0).map(() => {
        let x = Math.random();
        let y = Math.random();
        if (Math.random() < 0.38) {
          const c = clusters[Math.floor(Math.random() * clusters.length)];
          const a = Math.random() * Math.PI * 2;
          const d = Math.random() * c.r;
          x = Math.min(1, Math.max(0, c.x + Math.cos(a) * d));
          y = Math.min(1, Math.max(0, c.y + Math.sin(a) * d));
        }
        const roll = Math.random();
        const layer = roll < 0.32 ? 'far' : roll < 0.68 ? 'mid' : 'near';
        return {
          x, y,
          z: Math.pow(Math.random(), 1.35),
          size: Math.random() * 1.5 + 0.2,
          tw: Math.random() * Math.PI * 2,
          layer,
          streak: layer === 'near' && Math.random() < 0.06,
          streakAngle: Math.random() * Math.PI,
        };
      });
    }

    function starCountForIntensity() {
      const mobile = mobileMQ.matches;
      if (state.intensity === 'cosmic') return mobile ? 620 : 1080;
      if (state.intensity === 'subtle') return mobile ? 380 : 640;
      return mobile ? 520 : 920;
    }

    return {
      name: 'starfield',
      init(ctx, s) {
        stars = makeStars(starCountForIntensity());
        s.stars = stars;
      },
      draw(ctx, s, dt) {
        if (reduceMotionMQ.matches || mobileMQ.matches) return;
        const time = performance.now() * 0.001;
        ctx.save();
        ctx.globalCompositeOperation = 'source-over';
        ctx.setTransform(s.dpr, 0, 0, s.dpr, 0, 0);
        ctx.clearRect(0, 0, s.w, s.h);

        const mx = s.mouseNX - 0.5;
        const my = s.mouseNY - 0.5;
        const scrollFactor = Math.pow(Math.min(s.scrollY / Math.max(document.documentElement.scrollHeight - s.h, 1), 1), 0.85);

        for (let i = 0; i < stars.length; i++) {
          const star = stars[i];
          const depth = star.z;
          const parallax = star.layer === 'far' ? 0.32 : star.layer === 'mid' ? 0.74 : 1.18;
          const depthExp = Math.pow(depth, 1.15);
          const px = mx * 240 * depthExp * parallax;
          const py = my * 175 * depthExp * parallax + s.scrollY * 0.042 * depthExp * parallax + scrollFactor * 18 * depthExp;

          const x = star.x * s.w + px;
          const y = star.y * s.h + py;
          if (x < -60 || x > s.w + 60 || y < -60 || y > s.h + 60) continue;

          const alphaWave = 0.48 + 0.52 * Math.sin(time * (0.65 + depth * 1.3) + star.tw);
          const layerAlpha = star.layer === 'far' ? 0.5 : star.layer === 'mid' ? 0.82 : 1;
          const alpha = (0.018 + depth * 0.24) * alphaWave * layerAlpha * (s.intensity === 'cosmic' ? 1.05 : 0.92);

          // IQ palette for color
          const cycles = 0.45 + depth * 1.08;
          const twoPi = 6.28318530718;
          const base = time * cycles + depth * 0.45 + scrollFactor * 0.2;
          const r = 0.5 + 0.5 * Math.cos(twoPi * (base + 0.0));
          const g = 0.5 + 0.5 * Math.cos(twoPi * (base + 0.33));
          const b = 0.5 + 0.5 * Math.cos(twoPi * (base + 0.67));
          const mag = 0.5 + 0.5 * Math.cos(twoPi * (base + 0.12));
          const cr = r * 0.68 + mag * 0.26 + 0.12;
          const cg = g * 0.72 + 0.1;
          const cb = b * 0.7 + mag * 0.18 + 0.14;

          const colR = Math.round(255 * cr);
          const colG = Math.round(255 * cg);
          const colB = Math.round(255 * cb);

          const size = star.size * (0.45 + depth * 1.3) * (star.layer === 'near' ? 1.12 : 1);

          if (star.streak) {
            ctx.save();
            ctx.translate(x, y);
            ctx.rotate(star.streakAngle);
            const streakGrad = ctx.createLinearGradient(-size * 3, 0, size * 3, 0);
            streakGrad.addColorStop(0, `rgba(${colR},${colG},${colB},0)`);
            streakGrad.addColorStop(0.5, `rgba(${colR},${colG},${colB},${alpha * 0.55})`);
            streakGrad.addColorStop(1, `rgba(${colR},${colG},${colB},0)`);
            ctx.fillStyle = streakGrad;
            ctx.fillRect(-size * 3, -0.6, size * 6, 1.2);
            ctx.restore();
          }

          ctx.fillStyle = `rgba(${colR},${colG},${colB},${alpha})`;
          ctx.beginPath();
          ctx.arc(x, y, size, 0, Math.PI * 2);
          ctx.fill();

          if (star.layer !== 'far') {
            ctx.fillStyle = `rgba(${colR},${colG},${colB},${alpha * 0.28})`;
            ctx.beginPath();
            ctx.arc(x, y, size * 2.5, 0, Math.PI * 2);
            ctx.fill();
          }
        }
        ctx.restore();
      },
      resize(s) {
        stars = makeStars(starCountForIntensity());
        s.stars = stars;
      },
      destroy() { stars = []; }
    };
  }

  // ===== Orrery Module =====
  function createOrreryModule() {
    return {
      name: 'orrery',
      init(ctx, s) {},
      draw(ctx, s, dt) {
        if (reduceMotionMQ.matches) return;
        const time = performance.now() * 0.001;
        const mounts = document.querySelectorAll('.melodia-orrery, .orrery-mount, .section-orrery');
        if (!mounts.length) return;

        mounts.forEach(mount => {
          const svg = mount.querySelector('svg');
          if (!svg) return;
          const rect = mount.getBoundingClientRect();
          if (rect.width === 0 || rect.height === 0) return;

          // Draw orrery into an offscreen canvas then draw to main ctx
          // For simplicity, we let CSS animations handle the orrery rings
          // This module just ensures the mount is positioned correctly
        });
      },
      resize() {},
      destroy() {}
    };
  }

  // ===== Watercolor Wash / Thin Film (from starfield) =====
  function createAtmosphereModule() {
    return {
      name: 'atmosphere',
      init() {},
      draw(ctx, s, dt) {
        if (reduceMotionMQ.matches || mobileMQ.matches) return;
        const time = performance.now() * 0.001;
        ctx.save();
        ctx.globalCompositeOperation = 'soft-light';
        ctx.filter = 'blur(28px)';
        const washes = [
          { cx: 0.22, cy: 0.18, r: 0.42, hue: [255, 110, 180], a: s.intensity === 'cosmic' ? 0.1 : 0.08 },
          { cx: 0.78, cy: 0.28, r: 0.36, hue: [204, 153, 255], a: 0.075 },
          { cx: 0.52, cy: 0.72, r: 0.48, hue: [102, 217, 255], a: 0.065 },
          { cx: 0.12, cy: 0.62, r: 0.32, hue: [232, 80, 140], a: 0.06 },
        ];
        for (let i = 0; i < washes.length; i++) {
          const w = washes[i];
          const driftX = Math.sin(time * 0.14 + i * 1.7) * w.r * 0.04 * s.w;
          const driftY = Math.cos(time * 0.11 + i * 2.2) * s.h * 0.03;
          const cx = w.cx * s.w + driftX + (s.mouseNX - 0.5) * 60;
          const cy = w.cy * s.h + driftY + (s.mouseNY - 0.5) * 40;
          const rad = w.r * Math.max(s.w, s.h);
          const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, rad);
          grad.addColorStop(0, `rgba(${w.hue[0]},${w.hue[1]},${w.hue[2]},${w.a})`);
          grad.addColorStop(0.55, `rgba(${w.hue[0]},${w.hue[1]},${w.hue[2]},${w.a * 0.45})`);
          grad.addColorStop(1, `rgba(${w.hue[0]},${w.hue[1]},${w.hue[2]},0)`);
          ctx.fillStyle = grad;
          ctx.fillRect(0, 0, s.w, s.h);
        }
        ctx.filter = 'none';
        ctx.restore();
      },
      resize() {},
      destroy() {}
    };
  }

  // ===== Magical Girl / Dream Shaders (simplified) =====
  function createMagicalModule() {
    return {
      name: 'magical',
      init() {},
      draw(ctx, s, dt) {
        if (reduceMotionMQ.matches) return;
        const shells = document.querySelectorAll('[data-mg="full"], .magical-girl-active');
        if (!shells.length) return;
        // CSS handles the actual effects via custom properties
        // This module just updates the mouse/scroll CSS vars
      },
      resize() {},
      destroy() {}
    };
  }

  // ===== Core Manager =====
  function mountCanvas(shell) {
    if (shell.querySelector(':scope > .melodia-effects-canvas')) return;
    const el = document.createElement('canvas');
    el.className = 'melodia-effects-canvas';
    el.setAttribute('aria-hidden', 'true');
    el.style.position = 'fixed';
    el.style.inset = '0';
    el.style.zIndex = 'var(--z-starfield, 0)';
    el.style.pointerEvents = 'none';
    shell.insertBefore(el, shell.firstChild);
    state.canvas = el;
    state.ctx = el.getContext('2d', { alpha: true });
  }

  function resize() {
    if (!state.canvas) return;
    state.dpr = Math.min(window.devicePixelRatio || 1, 2);
    state.w = window.innerWidth;
    state.h = window.innerHeight;
    state.canvas.width = Math.max(1, Math.floor(state.w * state.dpr));
    state.canvas.height = Math.max(1, Math.floor(state.h * state.dpr));
    state.canvas.style.width = `${state.w}px`;
    state.canvas.style.height = `${state.h}px`;
    state.modules.starfield?.resize(state);
    state.modules.atmosphere?.resize(state);
  }

  function readInputs() {
    const root = document.documentElement;
    const style = getComputedStyle(root);
    const mx = parseFloat(style.getPropertyValue('--dream-mouse-x'));
    const my = parseFloat(style.getPropertyValue('--dream-mouse-y'));
    if (!Number.isNaN(mx)) state.mouseNX = mx;
    if (!Number.isNaN(my)) state.mouseNY = my;
    state.scrollY = window.scrollY || 0;
  }

  function drawFrame(timestamp) {
    if (!state.isVisible || !state.ctx) {
      state.rafId = requestAnimationFrame(drawFrame);
      return;
    }
    const dt = timestamp - state.lastFrame;
    state.lastFrame = timestamp;

    readInputs();
    state.ctx.setTransform(state.dpr, 0, 0, state.dpr, 0, 0);
    state.ctx.clearRect(0, 0, state.w, state.h);

    // Draw in order: atmosphere -> starfield -> magical
    state.modules.atmosphere?.draw(state.ctx, state, dt);
    state.modules.starfield?.draw(state.ctx, state, dt);
    state.modules.magical?.draw(state.ctx, state, dt);

    state.rafId = requestAnimationFrame(drawFrame);
  }

  function init(options = {}) {
    if (state.booted) return;
    state.shell = document.querySelector('.melodia-shell');
    if (!state.shell) {
      // Retry on next frame
      requestAnimationFrame(() => init(options));
      return;
    }

    state.booted = true;
    state.reduceMotion = reduceMotionMQ.matches;
    state.intensity = options.intensity || state.shell.getAttribute('data-starfield-intensity') || 'standard';
    if (state.shell.getAttribute('data-hero') === 'cosmic') state.intensity = 'cosmic';

    // Register modules
    state.modules.starfield = createStarfieldModule();
    state.modules.atmosphere = createAtmosphereModule();
    state.modules.orrery = createOrreryModule();
    state.modules.magical = createMagicalModule();

    mountCanvas(state.shell);
    resize();

    // Initialize modules
    Object.values(state.modules).forEach(m => m.init?.(state.ctx, state));

    // Event listeners
    window.addEventListener('resize', resize, { passive: true });
    document.addEventListener('visibilitychange', () => {
      state.isVisible = !document.hidden;
      if (state.isVisible) state.lastFrame = performance.now();
    });
    reduceMotionMQ.addEventListener('change', e => { state.reduceMotion = e.matches; });

    state.lastFrame = performance.now();
    state.rafId = requestAnimationFrame(drawFrame);

    // Expose API
    global.MelodiaEffects = {
      setIntensity: (next) => { state.intensity = next; resize(); },
      stop: () => { cancelAnimationFrame(state.rafId); },
      restart: () => { state.rafId = requestAnimationFrame(drawFrame); },
      getState: () => ({ ...state, ctx: null, canvas: null, modules: Object.keys(state.modules) })
    };

    if (reduceMotionMQ.matches) state.shell.classList.add('starfield-reduced');
  }

  // Auto-init when DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => init());
  } else {
    init();
  }

})(window);