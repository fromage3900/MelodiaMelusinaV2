(() => {
  "use strict";

  const TAU = Math.PI * 2;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const canvas = document.getElementById("stage");
  const ctx = canvas.getContext("2d", { alpha: false });

  const stateName = document.getElementById("state-name");
  const stateNote = document.getElementById("state-note");
  const mixHint = document.getElementById("mix-hint");
  const coherenceFill = document.getElementById("coherence-fill");
  const coherenceVal = document.getElementById("coherence-val");
  const btnC = document.getElementById("btn-c");
  const btnE = document.getElementById("btn-e");
  const btnG = document.getElementById("btn-g");
  const btnBloom = document.getElementById("btn-bloom");
  const btnRest = document.getElementById("btn-rest");
  const btnMute = document.getElementById("btn-mute");
  const glyphC = document.getElementById("glyph-c");
  const glyphE = document.getElementById("glyph-e");
  const glyphG = document.getElementById("glyph-g");

  const NOTES = {
    REST: "soft natural wool. the creature is already complete.",
    ROOT_C: "one pitch becomes visible. faint rings find the fleece.",
    INTERVAL_CE: "interference. the field is more complex, less settled.",
    RESOLUTION_CEG: "the shared field becomes more ordered, not louder.",
    WORLD_HIT: "structure leaves the body. the world answers the chord.",
    AFTERIMAGE: "the pattern decays. the sheep remains readable.",
  };

  const membrane = window.ChladniMembrane;
  const MODE = membrane.MODE;

  const target = { C: 0, E: 0, G: 0, world: 0 };
  const mix = { C: 0, E: 0, G: 0, world: 0 };
  let muted = true;
  let audio = null;
  let voices = null;
  let script = null;
  let last = performance.now();
  let coherence = 0;
  let coherenceShown = 0;
  let glyphFlash = { C: 0, E: 0, G: 0 };

  let W = 0;
  let H = 0;
  let cx = 0;
  let cy = 0;
  let scale = 1;
  let particles = [];
  let worldDust = [];
  let curls = [];
  let doodles = [];
  let grain = null;
  let grid = null;
  let gridN = 96;

  function hash(i) {
    let x = (i + 1) * 374761393;
    x = (x ^ (x >>> 13)) * 1274126177;
    return ((x ^ (x >>> 16)) >>> 0) / 4294967296;
  }

  function field(nx, ny) {
    return membrane.field(nx, ny, mix);
  }

  function inEllipse(x, y, ex, ey, rx, ry) {
    const dx = (x - ex) / rx;
    const dy = (y - ey) / ry;
    return dx * dx + dy * dy <= 1;
  }

  function inFleece(x, y) {
    return membrane.inFleece(x, y);
  }

  function inFaceQuiet(x, y) {
    return inEllipse(x, y, 80, -20, 34, 30);
  }

  function spawnInFleece() {
    for (let i = 0; i < 80; i++) {
      const x = (hash(i * 17 + particles.length * 3) * 2 - 1) * 130;
      const y = (hash(i * 31 + particles.length * 5) * 2 - 1) * 110;
      if (inFleece(x, y) && !inFaceQuiet(x, y)) {
        return { x, y };
      }
    }
    return { x: 0, y: 12 };
  }

  function rebuildParticles() {
    particles = [];
    const count = reduced ? 900 : 4200;
    for (let i = 0; i < count; i++) {
      const p = spawnInFleece();
      particles.push({
        x: p.x,
        y: p.y,
        vx: 0,
        vy: 0,
        seed: hash(i * 97),
        r: 0.55 + hash(i * 13) * 1.15,
      });
    }
    worldDust = [];
    const wcount = reduced ? 180 : 900;
    for (let i = 0; i < wcount; i++) {
      const a = hash(i * 19) * TAU;
      const rad = 130 + hash(i * 23) * 90;
      worldDust.push({
        a,
        rad,
        spin: 0.08 + hash(i * 29) * 0.12,
        r: 0.6 + hash(i * 11) * 1.4,
        seed: hash(i * 41),
      });
    }
    curls = [];
    for (let i = 0; i < 36; i++) {
      const p = spawnInFleece();
      curls.push({
        x: p.x,
        y: p.y,
        rad: 6 + hash(i * 7) * 14,
        rot: hash(i * 3) * TAU,
        turns: 1.2 + hash(i * 5) * 1.6,
      });
    }
  }

  function sampleCoherence() {
    return membrane.coherenceOf(mix);
  }

  function labelState() {
    return membrane.labelState(mix);
  }

  function syncUi() {
    const name = labelState();
    stateName.textContent = name.replaceAll("_", " ");
    stateNote.textContent = NOTES[name] || NOTES.REST;
    const parts = [];
    if (target.C) parts.push("C");
    if (target.E) parts.push("E");
    if (target.G) parts.push("G");
    mixHint.textContent = parts.length ? parts.join(" + ") : "no pitches";
    btnC.classList.toggle("on", target.C > 0.5);
    btnE.classList.toggle("on", target.E > 0.5);
    btnG.classList.toggle("on", target.G > 0.5);
    glyphC.classList.toggle("on", mix.C > 0.25);
    glyphE.classList.toggle("on", mix.E > 0.25);
    glyphG.classList.toggle("on", mix.G > 0.25);
    glyphC.classList.toggle("event", glyphFlash.C > 0.4);
    glyphE.classList.toggle("event", glyphFlash.E > 0.4);
    glyphG.classList.toggle("event", glyphFlash.G > 0.4);
    coherenceShown += (coherence - coherenceShown) * 0.12;
    coherenceFill.style.width = `${(coherenceShown * 100).toFixed(1)}%`;
    coherenceVal.textContent = coherenceShown < 0.03 ? "—" : coherenceShown.toFixed(2);
  }

  function ensureAudio() {
    if (audio) return;
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    audio = new AC();
    voices = {};
    for (const id of ["C", "E", "G"]) {
      const osc = audio.createOscillator();
      const gain = audio.createGain();
      osc.type = "sine";
      osc.frequency.value = MODE[id].freq;
      gain.gain.value = 0;
      osc.connect(gain);
      gain.connect(audio.destination);
      osc.start();
      voices[id] = { osc, gain };
    }
  }

  function setVoice(id, on) {
    if (!audio || !voices || muted) return;
    const v = voices[id];
    const now = audio.currentTime;
    const peak = id === "C" ? 0.045 : id === "E" ? 0.036 : 0.032;
    v.gain.gain.cancelScheduledValues(now);
    v.gain.gain.setTargetAtTime(on ? peak : 0, now, on ? 0.08 : 0.18);
  }

  function hushAll() {
    if (!voices) return;
    for (const id of ["C", "E", "G"]) setVoice(id, false);
  }

  function setPitch(id, on, flash) {
    target[id] = on ? 1 : 0;
    if (on && flash !== false) glyphFlash[id] = 1;
    if (!muted) {
      ensureAudio();
      audio?.resume?.();
      setVoice(id, on);
    }
  }

  function rest(all) {
    target.C = 0;
    target.E = 0;
    target.G = 0;
    if (all) target.world = 0;
    hushAll();
    stopScript();
  }

  function stopScript() {
    if (script) {
      script.cancelled = true;
      script = null;
    }
    btnBloom.disabled = false;
  }

  function wait(ms, token) {
    return new Promise((resolve) => {
      const t = setTimeout(resolve, reduced ? Math.min(ms, 80) : ms);
      const poll = setInterval(() => {
        if (token.cancelled) {
          clearTimeout(t);
          clearInterval(poll);
          resolve();
        }
      }, 40);
      setTimeout(() => clearInterval(poll), ms + 50);
    });
  }

  async function playBloom() {
    stopScript();
    const token = { cancelled: false };
    script = token;
    btnBloom.disabled = true;
    rest(true);
    if (!muted) {
      ensureAudio();
      audio?.resume?.();
    }
    await wait(700, token);
    if (token.cancelled) return;
    setPitch("C", true);
    await wait(2400, token);
    if (token.cancelled) return;
    setPitch("E", true);
    await wait(2000, token);
    if (token.cancelled) return;
    setPitch("G", true);
    await wait(2800, token);
    if (token.cancelled) return;
    target.world = 1;
    await wait(2200, token);
    if (token.cancelled) return;
    target.world = 0;
    rest(false);
    await wait(1600, token);
    if (token.cancelled) return;
    script = null;
    btnBloom.disabled = false;
  }

  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = Math.max(1, Math.floor(window.innerWidth * dpr));
    H = Math.max(1, Math.floor(window.innerHeight * dpr));
    canvas.width = W;
    canvas.height = H;
    canvas.style.width = `${window.innerWidth}px`;
    canvas.style.height = `${window.innerHeight}px`;
    cx = W * 0.5;
    cy = H * 0.54;
    scale = Math.min(W, H) / 520;
    rebuildParticles();
    buildGrain();
    buildDoodles();
    grid = {
      n: gridN,
      u: new Float32Array(gridN * gridN),
    };
  }

  function buildGrain() {
    grain = document.createElement("canvas");
    grain.width = 128;
    grain.height = 128;
    const g = grain.getContext("2d");
    const img = g.createImageData(128, 128);
    for (let i = 0; i < img.data.length; i += 4) {
      const n = 210 + (hash(i) * 45) | 0;
      img.data[i] = n;
      img.data[i + 1] = n - 6;
      img.data[i + 2] = n - 12;
      img.data[i + 3] = 40;
    }
    g.putImageData(img, 0, 0);
  }

  function buildDoodles() {
    doodles = [];
    const kinds = ["star", "heart", "swirl", "diamond"];
    for (let i = 0; i < 22; i++) {
      doodles.push({
        kind: kinds[i % kinds.length],
        x: hash(i * 11) * W,
        y: hash(i * 19) * H,
        r: 6 + hash(i * 3) * 11,
        rot: hash(i * 7) * TAU,
        a: 0.08 + hash(i * 13) * 0.12,
      });
    }
  }

  function wobbleEllipse(g, ex, ey, rx, ry, rot, seed) {
    g.beginPath();
    const n = 32;
    for (let i = 0; i <= n; i++) {
      const t = (i / n) * TAU;
      const j = 1 + (hash(seed + i) - 0.5) * 0.055;
      const x = ex + Math.cos(t) * rx * j;
      const y = ey + Math.sin(t) * ry * j;
      const xr = ex + (x - ex) * Math.cos(rot) - (y - ey) * Math.sin(rot);
      const yr = ey + (x - ex) * Math.sin(rot) + (y - ey) * Math.cos(rot);
      if (i === 0) g.moveTo(xr, yr);
      else g.lineTo(xr, yr);
    }
    g.closePath();
  }

  function diamond(g, x, y, r) {
    g.beginPath();
    g.moveTo(x, y - r);
    g.lineTo(x + r * 0.72, y);
    g.lineTo(x, y + r);
    g.lineTo(x - r * 0.72, y);
    g.closePath();
  }

  function lerpMix(dt) {
    const k = reduced ? 1 : 1 - Math.pow(0.001, dt);
    mix.C += (target.C - mix.C) * k;
    mix.E += (target.E - mix.E) * k;
    mix.G += (target.G - mix.G) * k;
    mix.world += (target.world - mix.world) * k;
    for (const id of ["C", "E", "G"]) {
      glyphFlash[id] = Math.max(0, glyphFlash[id] - dt * 1.6);
    }
  }

  function stepParticles(dt) {
    const active = mix.C + mix.E + mix.G;
    const settle = reduced ? 1 : Math.min(1, dt * 60);
    for (const p of particles) {
      const nx = p.x / 110;
      const ny = p.y / 110;
      const u = field(nx, ny);
      const eps = 1.6;
      const ux = field(nx + eps / 110, ny) - u;
      const uy = field(nx, ny + eps / 110) - u;
      const mag = Math.abs(u);
      // Nodes attract sand; antinodes push it away. REST is only wool-breath.
      const force = active > 0.05 ? mag : 0;
      p.vx += -ux * force * 48 * settle;
      p.vy += -uy * force * 48 * settle;
      p.vx += (hash((p.seed * 1e6 + p.x) | 0) - 0.5) * (0.35 + (1 - active) * 0.5);
      p.vy += (hash((p.seed * 1e6 + p.y) | 0) - 0.5) * (0.35 + (1 - active) * 0.5);
      p.vx *= 0.86;
      p.vy *= 0.86;
      p.x += p.vx * settle;
      p.y += p.vy * settle;
      if (!inFleece(p.x, p.y) || inFaceQuiet(p.x, p.y)) {
        const q = spawnInFleece();
        p.x = q.x;
        p.y = q.y;
        p.vx = 0;
        p.vy = 0;
      }
    }
  }

  function paper() {
    const g = ctx;
    g.fillStyle = "#f3efe4";
    g.fillRect(0, 0, W, H);

    const wash = g.createRadialGradient(cx - 80 * scale, cy - 40 * scale, 20 * scale, cx, cy, Math.max(W, H) * 0.62);
    wash.addColorStop(0, "rgba(244, 214, 228, 0.55)");
    wash.addColorStop(0.45, "rgba(226, 210, 240, 0.28)");
    wash.addColorStop(1, "rgba(243, 239, 228, 0)");
    g.fillStyle = wash;
    g.fillRect(0, 0, W, H);

    if (grain) {
      g.save();
      g.globalAlpha = 0.35;
      g.fillStyle = g.createPattern(grain, "repeat");
      g.fillRect(0, 0, W, H);
      g.restore();
    }

    g.save();
    g.strokeStyle = "rgba(58, 46, 36, 0.28)";
    g.lineWidth = 1.1 * scale;
    g.lineCap = "round";
    for (const d of doodles) {
      const dx = d.x - cx;
      const dy = d.y - cy;
      if (Math.hypot(dx, dy) < 160 * scale) continue;
      g.globalAlpha = d.a * (1 - mix.world * 0.55);
      g.save();
      g.translate(d.x, d.y);
      g.rotate(d.rot);
      if (d.kind === "star") {
        g.beginPath();
        for (let i = 0; i < 10; i++) {
          const a = (i / 10) * TAU - Math.PI / 2;
          const r = i % 2 ? d.r * 0.38 : d.r;
          const x = Math.cos(a) * r;
          const y = Math.sin(a) * r;
          if (i === 0) g.moveTo(x, y);
          else g.lineTo(x, y);
        }
        g.closePath();
        g.stroke();
      } else if (d.kind === "heart") {
        g.beginPath();
        g.moveTo(0, d.r * 0.35);
        g.bezierCurveTo(d.r, -d.r * 0.3, d.r * 0.3, -d.r, 0, -d.r * 0.35);
        g.bezierCurveTo(-d.r * 0.3, -d.r, -d.r, -d.r * 0.3, 0, d.r * 0.35);
        g.stroke();
      } else if (d.kind === "diamond") {
        diamond(g, 0, 0, d.r * 0.7);
        g.stroke();
      } else {
        g.beginPath();
        for (let t = 0; t < 1.4; t += 0.05) {
          const a = t * TAU;
          const r = d.r * (t / 1.4);
          const x = Math.cos(a) * r;
          const y = Math.sin(a) * r;
          if (t === 0) g.moveTo(x, y);
          else g.lineTo(x, y);
        }
        g.stroke();
      }
      g.restore();
    }
    g.restore();

    if (mix.world > 0.02) {
      g.save();
      g.globalAlpha = mix.world * 0.55;
      g.strokeStyle = "rgba(94, 200, 232, 0.7)";
      g.lineWidth = 1.4 * scale;
      for (let k = 0; k < 7; k++) {
        g.beginPath();
        for (let x = 0; x <= W; x += 8) {
          const y = cy + Math.sin(x * 0.012 + k * 0.9 + mix.world * 2) * (18 + k * 7) * scale
            + Math.sin(x * 0.03 + k) * 8 * scale;
          if (x === 0) g.moveTo(x, y);
          else g.lineTo(x, y);
        }
        g.stroke();
      }
      g.strokeStyle = "rgba(232, 123, 165, 0.28)";
      const cell = 28 * scale;
      for (let i = -8; i < 10; i++) {
        g.beginPath();
        g.moveTo(cx + i * cell - 180 * scale, cy - 160 * scale);
        g.lineTo(cx + i * cell + 180 * scale, cy + 160 * scale);
        g.stroke();
        g.beginPath();
        g.moveTo(cx + i * cell + 180 * scale, cy - 160 * scale);
        g.lineTo(cx + i * cell - 180 * scale, cy + 160 * scale);
        g.stroke();
      }
      g.restore();
    }
  }

  function drawSheepBody() {
    const g = ctx;
    const s = scale;
    g.save();
    g.translate(cx, cy);
    g.scale(s, s);

    if (mix.world > 0.2) {
      g.save();
      g.globalAlpha = mix.world * 0.45;
      g.strokeStyle = "#7ee7ff";
      g.lineWidth = 7;
      wobbleEllipse(g, 0, 10, 102, 88, -0.08, 3);
      g.stroke();
      g.restore();
    }

    const wool = g.createRadialGradient(-28, -36, 8, 10, 16, 140);
    wool.addColorStop(0, "#fbe8ef");
    wool.addColorStop(0.4, "#e8b4c4");
    wool.addColorStop(1, "#c07a96");
    g.fillStyle = wool;
    const blob = (ex, ey, rx, ry, rot, seed) => {
      wobbleEllipse(g, ex, ey, rx, ry, rot || 0, seed);
      g.fill();
    };
    blob(0, 10, 96, 82, -0.08, 11);
    blob(72, -22, 50, 46, 0.18, 17);
    blob(-46, -8, 42, 36, 0.2, 23);
    blob(18, -58, 38, 28, -0.3, 29);
    blob(-12, 28, 36, 24, 0.4, 31);

    g.fillStyle = "#d7a3b5";
    blob(58, -62, 18, 32, 0.55, 41);
    blob(98, -58, 16, 30, -0.7, 43);

    g.strokeStyle = "rgba(58, 46, 36, 0.72)";
    g.lineWidth = 1.8;
    wobbleEllipse(g, 0, 10, 96, 82, -0.08, 11);
    g.stroke();
    wobbleEllipse(g, 72, -22, 50, 46, 0.18, 17);
    g.stroke();
    wobbleEllipse(g, 58, -62, 18, 32, 0.55, 41);
    g.stroke();
    wobbleEllipse(g, 98, -58, 16, 30, -0.7, 43);
    g.stroke();

    g.fillStyle = "#b57a90";
    blob(-28, 86, 8, 20, 0.08, 51);
    blob(6, 90, 8, 20, -0.04, 53);
    blob(36, 88, 8, 19, 0.1, 55);
    blob(62, 82, 7.5, 18, 0.18, 57);
    g.fillStyle = "#2c241c";
    blob(-28, 104, 5.4, 3.4, 0, 61);
    blob(6, 108, 5.4, 3.4, 0, 63);
    blob(36, 105, 5.2, 3.3, 0, 65);
    blob(62, 98, 5, 3.2, 0.1, 67);

    g.restore();
  }

  function drawCurls() {
    if (mix.C + mix.E + mix.G > 0.85) return;
    const g = ctx;
    const s = scale;
    const fade = 1 - Math.min(1, (mix.C + mix.E + mix.G) * 1.1);
    g.save();
    g.translate(cx, cy);
    g.scale(s, s);
    g.strokeStyle = `rgba(58, 46, 36, ${0.22 * fade})`;
    g.lineWidth = 1.45;
    g.lineCap = "round";
    for (const c of curls) {
      g.beginPath();
      for (let t = 0; t < c.turns; t += 0.04) {
        const a = c.rot + t * TAU;
        const r = c.rad * (t / c.turns);
        const x = c.x + Math.cos(a) * r;
        const y = c.y + Math.sin(a) * r;
        if (t === 0) g.moveTo(x, y);
        else g.lineTo(x, y);
      }
      g.stroke();
    }
    g.restore();
  }

  function drawNodalField() {
    const active = mix.C + mix.E + mix.G;
    if (active < 0.05) return;
    const g = ctx;
    const n = grid.n;
    const u = grid.u;
    const span = 220;
    for (let j = 0; j < n; j++) {
      for (let i = 0; i < n; i++) {
        const x = ((i / (n - 1)) - 0.5) * span;
        const y = ((j / (n - 1)) - 0.5) * span * 0.9 + 6;
        u[j * n + i] = inFleece(x, y) ? field(x / 110, y / 110) : 99;
      }
    }
    g.save();
    g.translate(cx, cy);
    g.scale(scale, scale);
    g.lineWidth = 1.35;
    g.strokeStyle = `rgba(58, 46, 36, ${0.18 + active * 0.32})`;
    g.lineCap = "round";
    const cell = span / (n - 1);
    for (let j = 0; j < n - 1; j++) {
      for (let i = 0; i < n - 1; i++) {
        const a = u[j * n + i];
        const b = u[j * n + i + 1];
        const c = u[(j + 1) * n + i];
        if (a > 90 || b > 90 || c > 90) continue;
        const x = ((i / (n - 1)) - 0.5) * span;
        const y = ((j / (n - 1)) - 0.5) * span * 0.9 + 6;
        if ((a < 0) !== (b < 0)) {
          g.beginPath();
          g.moveTo(x, y);
          g.lineTo(x + cell, y);
          g.stroke();
        }
        if ((a < 0) !== (c < 0)) {
          g.beginPath();
          g.moveTo(x, y);
          g.lineTo(x, y + cell * 0.9);
          g.stroke();
        }
      }
    }
    g.restore();
  }

  function drawSand() {
    const g = ctx;
    const s = scale;
    const active = mix.C + mix.E + mix.G;
    g.save();
    g.translate(cx, cy);
    for (const p of particles) {
      const u = Math.abs(field(p.x / 110, p.y / 110));
      const onNode = u < 0.12;
      const a = 0.18 + active * (onNode ? 0.55 : 0.12);
      if (onNode && active > 0.2) {
        g.fillStyle = `rgba(44, 36, 28, ${a})`;
      } else {
        g.fillStyle = `rgba(255, 244, 248, ${0.2 + (1 - active) * 0.16})`;
      }
      const r = p.r * s * (onNode && active > 0.3 ? 1.25 : 0.9);
      g.beginPath();
      g.arc(p.x * s, p.y * s, r, 0, TAU);
      g.fill();
    }
    g.restore();
  }

  function drawWorldDust(t) {
    if (mix.world < 0.02) return;
    const g = ctx;
    const s = scale;
    g.save();
    g.translate(cx, cy);
    for (const d of worldDust) {
      const a = d.a + t * d.spin * 0.15;
      const x = Math.cos(a) * d.rad;
      const y = Math.sin(a) * d.rad * 0.86 + 8;
      const u = Math.abs(field(x / 160, y / 160));
      const onNode = u < 0.18 || mix.world > 0.5;
      g.fillStyle = onNode
        ? `rgba(126, 231, 255, ${0.22 + mix.world * 0.5})`
        : `rgba(232, 123, 165, ${0.08 + mix.world * 0.1})`;
      g.beginPath();
      g.arc(x * s, y * s, d.r * s, 0, TAU);
      g.fill();
    }
    g.restore();
  }

  function drawFace() {
    const g = ctx;
    const s = scale;
    g.save();
    g.translate(cx, cy);
    g.scale(s, s);

    g.fillStyle = "#f3c4d0";
    wobbleEllipse(g, 80, -18, 30, 26, 0.12, 71);
    g.fill();
    g.strokeStyle = "rgba(58, 46, 36, 0.7)";
    g.lineWidth = 1.6;
    g.stroke();

    g.fillStyle = "#e59bb0";
    wobbleEllipse(g, 70, -4, 8, 5, 0.2, 73);
    g.fill();
    wobbleEllipse(g, 92, -6, 8, 5, -0.1, 75);
    g.fill();

    const eye = (x, y) => {
      g.fillStyle = "#2c241c";
      g.beginPath();
      g.ellipse(x, y, 5.2, 6.6, 0.08, 0, TAU);
      g.fill();
      g.fillStyle = "#7ee7ff";
      diamond(g, x - 1.1, y - 1.6, 2.1);
      g.fill();
      g.fillStyle = "#fff";
      diamond(g, x + 1.6, y + 1.4, 1.15);
      g.fill();
    };
    eye(70, -22);
    eye(92, -24);

    g.fillStyle = "#4a3a46";
    wobbleEllipse(g, 82, -8, 4.6, 3.4, 0, 77);
    g.fill();

    const singing = mix.C + mix.E + mix.G > 0.4;
    g.strokeStyle = "#2c241c";
    g.lineWidth = 1.5;
    g.lineCap = "round";
    g.beginPath();
    if (singing) {
      g.ellipse(82, 0, 5.2, 3.6, 0, 0, TAU);
      g.stroke();
      g.strokeStyle = "rgba(58, 46, 36, 0.7)";
      g.beginPath();
      g.moveTo(78, -48);
      g.quadraticCurveTo(84, -58, 90, -50);
      g.quadraticCurveTo(84, -44, 78, -48);
      g.stroke();
    } else {
      g.moveTo(76, 1);
      g.quadraticCurveTo(80, 5, 84, 1);
      g.quadraticCurveTo(88, -1, 90, 2);
      g.stroke();
    }

    g.restore();
  }

  function corners() {
    const g = ctx;
    g.strokeStyle = "rgba(58, 46, 36, 0.4)";
    g.lineWidth = 1.3;
    g.lineCap = "round";
    const m = 22;
    const L = 26;
    const marks = [
      [m, m, 1, 1],
      [W - m, m, -1, 1],
      [m, H - m, 1, -1],
      [W - m, H - m, -1, -1],
    ];
    for (const [x, y, sx, sy] of marks) {
      g.beginPath();
      g.moveTo(x + (hash(x) - 0.5) * 3, y + sy * L);
      g.lineTo(x, y);
      g.lineTo(x + sx * L, y + (hash(y) - 0.5) * 3);
      g.stroke();
    }
  }

  function frame(now) {
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    lerpMix(dt);
    if (!reduced) stepParticles(dt);
    if ((now / 200 | 0) !== ((now - dt * 1000) / 200 | 0)) {
      coherence = sampleCoherence();
    }
    paper();
    drawWorldDust(now / 1000);
    drawSheepBody();
    drawCurls();
    drawNodalField();
    drawSand();
    drawFace();
    corners();
    syncUi();
    requestAnimationFrame(frame);
  }

  btnC.addEventListener("click", () => setPitch("C", target.C < 0.5));
  btnE.addEventListener("click", () => setPitch("E", target.E < 0.5));
  btnG.addEventListener("click", () => setPitch("G", target.G < 0.5));
  btnRest.addEventListener("click", () => rest(true));
  btnBloom.addEventListener("click", () => playBloom());
  btnMute.addEventListener("click", () => {
    muted = !muted;
    btnMute.textContent = muted ? "sound off" : "sound on";
    btnMute.setAttribute("aria-pressed", String(!muted));
    if (muted) hushAll();
    else {
      ensureAudio();
      audio?.resume?.();
      setVoice("C", target.C > 0.5);
      setVoice("E", target.E > 0.5);
      setVoice("G", target.G > 0.5);
    }
  });

  window.addEventListener("keydown", (e) => {
    if (e.repeat) return;
    const k = e.key.toLowerCase();
    if (k === "c") setPitch("C", target.C < 0.5);
    if (k === "e") setPitch("E", target.E < 0.5);
    if (k === "g") setPitch("G", target.G < 0.5);
    if (k === "r") rest(true);
    if (k === "m") btnMute.click();
    if (e.code === "Space") {
      e.preventDefault();
      playBloom();
    }
  });

  function snapMix() {
    mix.C = target.C;
    mix.E = target.E;
    mix.G = target.G;
    mix.world = target.world;
    for (let i = 0; i < (reduced ? 8 : 90); i++) stepParticles(1 / 60);
    coherence = sampleCoherence();
    coherenceShown = coherence;
  }

  function applyHash() {
    const h = (location.hash || "").replace("#", "").toUpperCase();
    if (h === "BLOOM") {
      playBloom();
      return;
    }
    rest(true);
    if (h === "C" || h === "ROOT_C" || h === "ROOT") {
      setPitch("C", true, false);
    } else if (h === "CE" || h === "INTERVAL_CE" || h === "INTERVAL") {
      setPitch("C", true, false);
      setPitch("E", true, false);
    } else if (h === "CEG" || h === "RESOLUTION" || h === "RESOLUTION_CEG") {
      setPitch("C", true, false);
      setPitch("E", true, false);
      setPitch("G", true, false);
    } else if (h === "WORLD" || h === "WORLD_HIT") {
      setPitch("C", true, false);
      setPitch("E", true, false);
      setPitch("G", true, false);
      target.world = 1;
    }
    snapMix();
  }

  window.addEventListener("resize", resize);
  window.addEventListener("hashchange", applyHash);
  resize();
  applyHash();
  requestAnimationFrame(frame);
})();
