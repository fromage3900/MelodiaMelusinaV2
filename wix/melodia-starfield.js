/**
 * MelodiaStarfield — single full-viewport depth-parallax canvas sky.
 */
(function (global) {
  'use strict';

  let booted = false;
  let rafId = 0;
  let canvas = null;
  let ctx = null;
  let stars = [];
  let w = 0;
  let h = 0;
  let dpr = 1;
  let intensity = 'standard';
  let mouseNX = 0.42;
  let mouseNY = 0.38;
  let scrollY = 0;

  const reduceMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)');
  const isMobile = () => window.matchMedia('(max-width: 680px)').matches;

  function iqPalette(t, cycles) {
    const twoPi = 6.28318530718;
    const base = t * cycles;
    const r = 0.5 + 0.5 * Math.cos(twoPi * (base + 0.0));
    const g = 0.5 + 0.5 * Math.cos(twoPi * (base + 0.33));
    const b = 0.5 + 0.5 * Math.cos(twoPi * (base + 0.67));
    const mag = 0.5 + 0.5 * Math.cos(twoPi * (base + 0.12));
    return [r * 0.68 + mag * 0.26 + 0.12, g * 0.72 + 0.1, b * 0.7 + mag * 0.18 + 0.14];
  }

  function devinIridescence(fres) {
    const f2 = fres * fres;
    const mix = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
    const c1 = [0, 0.8, 1];
    const c2 = [1, 0.9, 0.3];
    const c3 = [0.8, 0.4, 1];
    return mix(mix(c1, c2, fres), c3, f2);
  }

  function wavelengthToRgb(lambda) {
    let r = 0;
    let g = 0;
    let b = 0;
    if (lambda >= 380 && lambda < 440) {
      r = -(lambda - 440) / (440 - 380);
      b = 1;
    } else if (lambda < 490) {
      g = (lambda - 440) / (490 - 440);
      b = 1;
    } else if (lambda < 510) {
      g = 1;
      b = -(lambda - 510) / (510 - 490);
    } else if (lambda < 580) {
      r = (lambda - 510) / (580 - 510);
      g = 1;
    } else if (lambda < 645) {
      r = 1;
      g = -(lambda - 645) / (645 - 580);
    } else if (lambda <= 780) {
      r = -(lambda - 780) / (780 - 645);
    }
    const fade =
      lambda < 420 ? 0.35 + (0.65 * (lambda - 380)) / 40 : lambda > 700 ? 0.35 + (0.65 * (780 - lambda)) / 80 : 1;
    return [r * fade, g * fade, b * fade];
  }

  function thinFilmSample(thicknessNm, cosTheta) {
    const nFilm = 1.33;
    let r = 0;
    let g = 0;
    let b = 0;
    const steps = 14;
    for (let i = 0; i < steps; i++) {
      const lambda = 390 + (i / (steps - 1)) * 370;
      const phase = (4 * Math.PI * nFilm * thicknessNm * cosTheta) / lambda;
      const intensityVal = 0.5 + 0.5 * Math.cos(phase);
      const [lr, lg, lb] = wavelengthToRgb(lambda);
      r += lr * intensityVal;
      g += lg * intensityVal;
      b += lb * intensityVal;
    }
    const inv = 1 / steps;
    const fres = Math.max(0, Math.min(1, 0.28 + cosTheta * 0.55));
    const [dr, dg, db] = devinIridescence(fres);
    const bias = 0.42;
    return [(r * inv) * (1 - bias) + dr * bias, (g * inv) * (1 - bias) + dg * bias, (b * inv) * (1 - bias) + db * bias];
  }

  function starCountForIntensity() {
    const mobile = isMobile();
    if (intensity === 'cosmic') return mobile ? 620 : 1080;
    if (intensity === 'subtle') return mobile ? 380 : 640;
    return mobile ? 520 : 920;
  }

  function makeStars() {
    const count = starCountForIntensity();
    const clusters = Array.from({ length: 8 }, () => ({
      x: Math.random(),
      y: Math.random(),
      r: 0.06 + Math.random() * 0.1,
    }));

    stars = new Array(count).fill(0).map(() => {
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
        x,
        y,
        z: Math.pow(Math.random(), 1.35),
        size: Math.random() * 1.5 + 0.2,
        tw: Math.random() * Math.PI * 2,
        layer,
        streak: layer === 'near' && Math.random() < 0.06,
        streakAngle: Math.random() * Math.PI,
      };
    });
  }

  function mountCanvas(shell) {
    if (shell.querySelector(':scope > .melodia-starfield-canvas')) return;
    const el = document.createElement('canvas');
    el.className = 'melodia-starfield-canvas';
    el.setAttribute('aria-hidden', 'true');
    shell.insertBefore(el, shell.firstChild);
    if (!canvas) canvas = el;
  }

  function resize() {
    if (!canvas) return;
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    w = window.innerWidth;
    h = window.innerHeight;
    canvas.width = Math.max(1, Math.floor(w * dpr));
    canvas.height = Math.max(1, Math.floor(h * dpr));
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;
    ctx = canvas.getContext('2d', { alpha: true });
    makeStars();
  }

  function readInputs() {
    const root = document.documentElement;
    const style = getComputedStyle(root);
    const mx = parseFloat(style.getPropertyValue('--dream-mouse-x'));
    const my = parseFloat(style.getPropertyValue('--dream-mouse-y'));
    if (!Number.isNaN(mx)) mouseNX = mx;
    if (!Number.isNaN(my)) mouseNY = my;
    scrollY = window.scrollY || 0;
  }

  function drawWatercolorWash(t) {
    if (!ctx || reduceMotion().matches || isMobile()) return;
    const time = t * 0.001;
    ctx.save();
    ctx.globalCompositeOperation = 'soft-light';
    ctx.filter = 'blur(28px)';
    const washes = [
      { cx: 0.22, cy: 0.18, r: 0.42, hue: [255, 110, 180], a: intensity === 'cosmic' ? 0.1 : 0.08 },
      { cx: 0.78, cy: 0.28, r: 0.36, hue: [204, 153, 255], a: 0.075 },
      { cx: 0.52, cy: 0.72, r: 0.48, hue: [102, 217, 255], a: 0.065 },
      { cx: 0.12, cy: 0.62, r: 0.32, hue: [232, 80, 140], a: 0.06 },
    ];
    for (let i = 0; i < washes.length; i++) {
      const wash = washes[i];
      const driftX = Math.sin(time * 0.14 + i * 1.7) * wash.r * 0.04 * w;
      const driftY = Math.cos(time * 0.11 + i * 2.2) * h * 0.03;
      const cx = wash.cx * w + driftX + (mouseNX - 0.5) * 60;
      const cy = wash.cy * h + driftY + (mouseNY - 0.5) * 40;
      const rad = wash.r * Math.max(w, h);
      const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, rad);
      const [hr, hg, hb] = wash.hue;
      grad.addColorStop(0, `rgba(${hr},${hg},${hb},${wash.a})`);
      grad.addColorStop(0.55, `rgba(${hr},${hg},${hb},${wash.a * 0.45})`);
      grad.addColorStop(1, `rgba(${hr},${hg},${hb},0)`);
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, w, h);
    }
    ctx.filter = 'none';
    ctx.restore();
  }

  function drawThinFilmBands(t) {
    if (!ctx) return;
    const time = t * 0.001;
    const cosTheta = 0.58 + mouseNY * 0.28 + Math.abs(mouseNX - 0.5) * 0.08;
    const bandCount = reduceMotion().matches ? 2 : intensity === 'cosmic' ? 5 : 4;
    ctx.save();
    ctx.globalCompositeOperation = 'screen';
    for (let band = 0; band < bandCount; band++) {
      const thickness = 380 + band * 95 + Math.sin(time * 0.35 + band * 1.4) * 45;
      const [tr, tg, tb] = thinFilmSample(thickness, cosTheta);
      const alpha = (0.04 + band * 0.01) * 0.5;
      const yCenter =
        h * (0.12 + band * 0.18) +
        Math.sin(time * 0.22 + band * 2.1) * (reduceMotion().matches ? 8 : 24) +
        (mouseNY - 0.5) * 36;
      const grad = ctx.createLinearGradient(0, yCenter - 120, w, yCenter + 120);
      grad.addColorStop(0, `rgba(${Math.round(tr * 255)},${Math.round(tg * 255)},${Math.round(tb * 255)},0)`);
      grad.addColorStop(0.45, `rgba(${Math.round(tr * 255)},${Math.round(tg * 255)},${Math.round(tb * 255)},${alpha})`);
      grad.addColorStop(0.55, `rgba(${Math.round(tr * 255)},${Math.round(tg * 255)},${Math.round(tb * 255)},${alpha * 1.05})`);
      grad.addColorStop(1, `rgba(${Math.round(tr * 255)},${Math.round(tg * 255)},${Math.round(tb * 255)},0)`);
      ctx.fillStyle = grad;
      ctx.fillRect(0, yCenter - 130, w, 260);
    }
    ctx.restore();
  }

  function drawFrame(t) {
    if (!ctx || !canvas) return;
    readInputs();
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);

    drawWatercolorWash(t);
    drawThinFilmBands(t);

    ctx.globalCompositeOperation = 'screen';
    const mx = mouseNX - 0.5;
    const my = mouseNY - 0.5;
    const time = t * 0.001;
    const scrollFactor = Math.pow(Math.min(scrollY / Math.max(document.documentElement.scrollHeight - h, 1), 1), 0.85);

    for (let i = 0; i < stars.length; i++) {
      const s = stars[i];
      const depth = s.z;
      const parallax = s.layer === 'far' ? 0.32 : s.layer === 'mid' ? 0.74 : 1.18;
      const depthExp = Math.pow(depth, 1.15);
      const px = mx * 240 * depthExp * parallax;
      const py = my * 175 * depthExp * parallax + scrollY * 0.042 * depthExp * parallax + scrollFactor * 18 * depthExp;

      const x = s.x * w + px;
      const y = s.y * h + py;
      if (x < -60 || x > w + 60 || y < -60 || y > h + 60) continue;

      const alphaWave = 0.48 + 0.52 * Math.sin(time * (0.65 + depth * 1.3) + s.tw);
      const layerAlpha = s.layer === 'far' ? 0.5 : s.layer === 'mid' ? 0.82 : 1;
      const alpha = (0.018 + depth * 0.24) * alphaWave * layerAlpha * (intensity === 'cosmic' ? 1.05 : 0.92);

      const cycles = 0.45 + depth * 1.08;
      const [pr, pg, pb] = iqPalette(time + depth * 0.45 + scrollFactor * 0.2, cycles);
      const r = Math.round(255 * pr);
      const g = Math.round(255 * pg);
      const b = Math.round(255 * pb);

      const size = s.size * (0.45 + depth * 1.3) * (s.layer === 'near' ? 1.12 : 1);

      if (s.streak) {
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(s.streakAngle);
        const streakGrad = ctx.createLinearGradient(-size * 3, 0, size * 3, 0);
        streakGrad.addColorStop(0, `rgba(${r},${g},${b},0)`);
        streakGrad.addColorStop(0.5, `rgba(${r},${g},${b},${alpha * 0.55})`);
        streakGrad.addColorStop(1, `rgba(${r},${g},${b},0)`);
        ctx.fillStyle = streakGrad;
        ctx.fillRect(-size * 3, -0.6, size * 6, 1.2);
        ctx.restore();
      }

      ctx.fillStyle = `rgba(${r},${g},${b},${alpha})`;
      ctx.beginPath();
      ctx.arc(x, y, size, 0, Math.PI * 2);
      ctx.fill();

      if (s.layer !== 'far') {
        ctx.fillStyle = `rgba(${r},${g},${b},${alpha * 0.28})`;
        ctx.beginPath();
        ctx.arc(x, y, size * 2.5, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    ctx.globalCompositeOperation = 'source-over';
  }

  function startLoop() {
    if (reduceMotion().matches) {
      drawFrame(performance.now());
      return;
    }
    const tick = (t) => {
      drawFrame(t);
      rafId = window.requestAnimationFrame(tick);
    };
    rafId = window.requestAnimationFrame(tick);
  }

  function stopLoop() {
    if (rafId) window.cancelAnimationFrame(rafId);
    rafId = 0;
  }

  function init(options) {
    if (booted) return;
    const shell = document.querySelector('.melodia-shell');
    if (!shell) return;

    booted = true;
    intensity = (options && options.intensity) || shell.getAttribute('data-starfield-intensity') || 'standard';
    if (shell.getAttribute('data-hero') === 'cosmic') intensity = 'cosmic';

    mountCanvas(shell);
    resize();
    shell.dataset.starfieldIntensity = intensity;
    if (reduceMotion().matches) shell.classList.add('starfield-reduced');

    startLoop();
    window.addEventListener('resize', resize, { passive: true });
  }

  function setIntensity(next) {
    intensity = next || 'standard';
    makeStars();
  }

  global.MelodiaStarfield = { init, setIntensity, stopLoop };
})(window);
