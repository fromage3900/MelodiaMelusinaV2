(() => {
  "use strict";

  const TAU = Math.PI * 2;

  const MODE = {
    C: { k: 5.5201, m: 0, n: 0, amp: 1.00, freq: 261.63 },
    E: { k: 5.1356, m: 2, n: 2, amp: 0.88, freq: 329.63 },
    G: { k: 6.3802, m: 3, n: 3, amp: 0.72, freq: 392.00 },
  };

  function factorial(n) {
    let v = 1;
    for (let i = 2; i <= n; i++) v *= i;
    return v;
  }

  function besselJ(n, x) {
    if (x === 0) return n === 0 ? 1 : 0;
    const ax = Math.abs(x);
    let term = (ax / 2) ** n / factorial(n);
    let sum = term;
    for (let k = 1; k < 14; k++) {
      term *= -(ax * ax / 4) / (k * (k + n));
      sum += term;
    }
    return (x < 0 && n % 2) ? -sum : sum;
  }

  function makeLut(n, xMax) {
    const samples = 512;
    const data = new Float32Array(samples + 1);
    for (let i = 0; i <= samples; i++) data[i] = besselJ(n, (i / samples) * xMax);
    return (x) => {
      const t = Math.max(0, Math.min(1, x / xMax)) * samples;
      const i = t | 0;
      const f = t - i;
      return data[i] * (1 - f) + data[Math.min(samples, i + 1)] * f;
    };
  }

  const J = {
    0: makeLut(0, 9.2),
    2: makeLut(2, 9.2),
    3: makeLut(3, 9.2),
  };

  function field(nx, ny, mix) {
    const r = Math.hypot(nx, ny);
    if (r > 1.02) return 0;
    const th = Math.atan2(ny, nx);
    let u = 0;
    const c = mix.C || 0;
    const e = mix.E || 0;
    const g = mix.G || 0;
    if (c > 0.001) u += c * MODE.C.amp * J[0](MODE.C.k * r);
    if (e > 0.001) u += e * MODE.E.amp * J[2](MODE.E.k * r) * Math.cos(2 * th);
    if (g > 0.001) u += g * MODE.G.amp * J[3](MODE.G.k * r) * Math.cos(3 * th);
    return u;
  }

  function inEllipse(x, y, ex, ey, rx, ry) {
    const dx = (x - ex) / rx;
    const dy = (y - ey) / ry;
    return dx * dx + dy * dy <= 1;
  }

  function inFleece(x, y) {
    return (
      inEllipse(x, y, 0, 10, 96, 82) ||
      inEllipse(x, y, 72, -22, 50, 46) ||
      inEllipse(x, y, -46, -8, 42, 36) ||
      inEllipse(x, y, 18, -58, 38, 28)
    );
  }

  function coherenceOf(mix) {
    const active = (mix.C || 0) + (mix.E || 0) + (mix.G || 0);
    if (active < 0.04) return 0;
    const bins = 96;
    let circularity = 0;
    let rings = 0;
    const folds = { 2: 0, 3: 0, 6: 0 };
    for (let j = 4; j < 14; j++) {
      const rad = j / 16;
      const samples = [];
      for (let i = 0; i < bins; i++) {
        const th = (i / bins) * TAU;
        samples.push(Math.abs(field(Math.cos(th) * rad, Math.sin(th) * rad, mix)));
      }
      const mean = samples.reduce((a, b) => a + b, 0) / bins;
      let varc = 0;
      for (const v of samples) varc += (v - mean) ** 2;
      const std = Math.sqrt(varc / bins);
      circularity += 1 - std / (mean + 1e-6);
      rings += 1;
      for (const n of [2, 3, 6]) {
        let re = 0;
        let im = 0;
        for (let i = 0; i < bins; i++) {
          const th = (i / bins) * TAU;
          re += samples[i] * Math.cos(n * th);
          im += samples[i] * Math.sin(n * th);
        }
        folds[n] += Math.hypot(re, im) / bins / (mean + 1e-6);
      }
    }
    circularity /= rings;
    folds[2] /= rings;
    folds[3] /= rings;
    folds[6] /= rings;
    // C is calm (circular). C+E adds 2-fold unrest. C+E+G adds 3-fold and a 6-fold lock.
    const calm = circularity * 0.65;
    const blossom = folds[6] * 4.2 + folds[3] * 0.45;
    const unrest = Math.max(0, folds[2] - folds[3]) * 0.4;
    const ordered = Math.max(0, Math.min(1, calm + blossom - unrest));
    const world = mix.world || 0;
    return Math.min(1, ordered * 0.92 + world * 0.18);
  }

  function labelState(mix) {
    const c = (mix.C || 0) > 0.35;
    const e = (mix.E || 0) > 0.35;
    const g = (mix.G || 0) > 0.35;
    const w = (mix.world || 0) > 0.45;
    const any = (mix.C || 0) + (mix.E || 0) + (mix.G || 0);
    if (w && c && e && g) return "WORLD_HIT";
    if (c && e && g) return "RESOLUTION_CEG";
    if (c && e) return "INTERVAL_CE";
    if (c && g) return "INTERVAL_CE";
    if (e && g && !c) return "INTERVAL_CE";
    if (c) return "ROOT_C";
    if (any > 0.04 && any < 0.35) return "AFTERIMAGE";
    if (e || g) return "ROOT_C";
    return "REST";
  }

  const api = { MODE, field, coherenceOf, inFleece, labelState, besselJ };
  if (typeof window !== "undefined") window.ChladniMembrane = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})();
