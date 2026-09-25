// Particles, ground decals (telegraphs + skill flashes), loot beams and the
// 2D overlay for combat text / health bars.

import * as THREE from 'three';
import { clamp } from './util.js';

// ---------------------------------------------------------------- particles
const MAXP = 900;
function makeAtlas() {
  const s = 128, cv = document.createElement('canvas');
  cv.width = cv.height = s;
  const c = cv.getContext('2d');
  const h = s / 2;
  // 0: soft dot
  let g = c.createRadialGradient(h / 2, h / 2, 0, h / 2, h / 2, h / 2);
  g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.4, 'rgba(255,255,255,0.6)'); g.addColorStop(1, 'rgba(255,255,255,0)');
  c.fillStyle = g; c.fillRect(0, 0, h, h);
  c.fillStyle = '#fff'; c.textAlign = 'center'; c.textBaseline = 'middle';
  c.font = `bold ${h * 0.8}px serif`;
  c.fillText('♪', h * 1.5, h * 0.55); // 1: note
  c.fillText('♫', h * 0.5, h * 1.55); // 2: beamed notes
  // 3: star
  c.save(); c.translate(h * 1.5, h * 1.5); c.beginPath();
  for (let i = 0; i < 10; i++) { const r = i % 2 ? h * 0.16 : h * 0.44, a = (i / 10) * Math.PI * 2 - Math.PI / 2; c.lineTo(Math.cos(a) * r, Math.sin(a) * r); }
  c.closePath(); c.fill(); c.restore();
  const t = new THREE.CanvasTexture(cv);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

export class Particles {
  constructor(scene) {
    this.pos = new Float32Array(MAXP * 3);
    this.vel = new Float32Array(MAXP * 3);
    this.col = new Float32Array(MAXP * 3);
    this.size = new Float32Array(MAXP);
    this.alpha = new Float32Array(MAXP);
    this.kind = new Float32Array(MAXP);
    this.life = new Float32Array(MAXP);
    this.max = new Float32Array(MAXP);
    this.grav = new Float32Array(MAXP);
    this.size0 = new Float32Array(MAXP);
    this.cursor = 0;
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(this.pos, 3).setUsage(THREE.DynamicDrawUsage));
    geo.setAttribute('aColor', new THREE.BufferAttribute(this.col, 3).setUsage(THREE.DynamicDrawUsage));
    geo.setAttribute('aSize', new THREE.BufferAttribute(this.size, 1).setUsage(THREE.DynamicDrawUsage));
    geo.setAttribute('aAlpha', new THREE.BufferAttribute(this.alpha, 1).setUsage(THREE.DynamicDrawUsage));
    geo.setAttribute('aKind', new THREE.BufferAttribute(this.kind, 1).setUsage(THREE.DynamicDrawUsage));
    geo.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 1e6);
    this.mat = new THREE.ShaderMaterial({
      uniforms: { uMap: { value: makeAtlas() }, uScale: { value: 300 } },
      vertexShader: `attribute vec3 aColor; attribute float aSize; attribute float aAlpha; attribute float aKind;
        varying vec3 vC; varying float vA; varying float vK; uniform float uScale;
        void main(){ vC = aColor; vA = aAlpha; vK = aKind; vec4 mv = modelViewMatrix * vec4(position,1.0);
          gl_PointSize = aSize * uScale / -mv.z; gl_Position = projectionMatrix * mv; }`,
      fragmentShader: `uniform sampler2D uMap; varying vec3 vC; varying float vA; varying float vK;
        void main(){ vec2 cell = vec2(mod(vK, 2.0), 1.0 - floor(vK / 2.0)); vec2 uv = (gl_PointCoord * vec2(1.0,-1.0) + vec2(0.0,1.0)) * 0.5 + cell * 0.5;
          vec4 t = texture2D(uMap, vec2(uv.x, uv.y)); if (t.a * vA < 0.01) discard; gl_FragColor = vec4(vC, t.a * vA); }`,
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    });
    this.points = new THREE.Points(geo, this.mat);
    this.points.frustumCulled = false;
    this.points.renderOrder = 5;
    scene.add(this.points);
    this.geo = geo;
  }

  emit(x, y, z, color, opts = {}) {
    const i = this.cursor; this.cursor = (this.cursor + 1) % MAXP;
    const sp = opts.speed ?? 4;
    const a = Math.random() * Math.PI * 2, u = opts.up ?? (Math.random() * 0.8 + 0.2);
    this.pos[i * 3] = x + (opts.spread ? (Math.random() - 0.5) * opts.spread : 0);
    this.pos[i * 3 + 1] = y;
    this.pos[i * 3 + 2] = z + (opts.spread ? (Math.random() - 0.5) * opts.spread : 0);
    const dir = opts.dir;
    if (dir) { this.vel[i * 3] = dir.x * sp; this.vel[i * 3 + 1] = dir.y * sp; this.vel[i * 3 + 2] = dir.z * sp; }
    else { this.vel[i * 3] = Math.cos(a) * sp * (1 - u * 0.5); this.vel[i * 3 + 1] = u * sp; this.vel[i * 3 + 2] = Math.sin(a) * sp * (1 - u * 0.5); }
    this.col[i * 3] = color.r; this.col[i * 3 + 1] = color.g; this.col[i * 3 + 2] = color.b;
    this.size0[i] = opts.size ?? 0.6;
    this.kind[i] = opts.kind ?? 0;
    this.life[i] = this.max[i] = opts.life ?? 0.7;
    this.grav[i] = opts.gravity ?? 6;
  }

  burst(x, y, z, color, n = 12, opts = {}) { for (let k = 0; k < n; k++) this.emit(x, y, z, color, opts); }

  update(dt) {
    for (let i = 0; i < MAXP; i++) {
      if (this.life[i] <= 0) { this.alpha[i] = 0; this.size[i] = 0; continue; }
      this.life[i] -= dt;
      const t = clamp(this.life[i] / this.max[i], 0, 1);
      this.vel[i * 3 + 1] -= this.grav[i] * dt;
      const drag = 1 - dt * 1.8;
      this.vel[i * 3] *= drag; this.vel[i * 3 + 2] *= drag;
      this.pos[i * 3] += this.vel[i * 3] * dt;
      this.pos[i * 3 + 1] += this.vel[i * 3 + 1] * dt;
      this.pos[i * 3 + 2] += this.vel[i * 3 + 2] * dt;
      this.alpha[i] = t < 0.5 ? t * 2 : 1;
      this.size[i] = this.size0[i] * (0.4 + 0.6 * t);
    }
    for (const k of ['position', 'aColor', 'aSize', 'aAlpha', 'aKind']) this.geo.attributes[k].needsUpdate = true;
  }
}

// ---------------------------------------------------------------- decals
// One conforming grid decal type draws circle / ring / rect / cone shapes via
// an SDF in the shader, so telegraphs hug the terrain on slopes.
const DSEG = 14;
const decalVert = `attribute vec2 aLocal; varying vec2 vL; void main(){ vL = aLocal; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`;
const decalFrag = `uniform int uShape; uniform vec4 uDim; uniform float uProgress; uniform vec3 uColor; uniform float uAlpha; uniform float uTime; varying vec2 vL;
  void main(){
    float inside; float fill; float edge;
    if (uShape == 0) { float r = length(vL); inside = step(r, uDim.x); fill = step(r, uDim.x * uProgress); edge = smoothstep(uDim.x - 0.35, uDim.x, r) * inside; }
    else if (uShape == 1) { float r = length(vL); inside = step(uDim.y, r) * step(r, uDim.x); fill = inside * step(r, uDim.y + (uDim.x - uDim.y) * uProgress); edge = (smoothstep(uDim.x - 0.35, uDim.x, r) + 1.0 - smoothstep(uDim.y, uDim.y + 0.35, r)) * inside; }
    else if (uShape == 2) { inside = step(abs(vL.x), uDim.y * 0.5) * step(0.0, vL.y) * step(vL.y, uDim.x); fill = inside * step(vL.y, uDim.x * uProgress); edge = inside * max(smoothstep(uDim.y * 0.5 - 0.3, uDim.y * 0.5, abs(vL.x)), smoothstep(uDim.x - 0.3, uDim.x, vL.y)); }
    else { float r = length(vL); float a = abs(atan(vL.x, vL.y)); inside = step(r, uDim.x) * step(a, uDim.y); fill = inside * step(r, uDim.x * uProgress); edge = inside * max(smoothstep(uDim.x - 0.35, uDim.x, r), smoothstep(uDim.y - 0.06, uDim.y, a)); }
    if (inside < 0.5) discard;
    float a = (0.16 + fill * 0.34 + edge * 0.6) * uAlpha;
    gl_FragColor = vec4(uColor * (1.0 + edge * 0.6), a);
  }`;

export class Decals {
  constructor(scene, world, size = 32) {
    this.world = world;
    this.pool = [];
    for (let i = 0; i < size; i++) {
      const geo = new THREE.PlaneGeometry(1, 1, DSEG, DSEG);
      geo.rotateX(-Math.PI / 2);
      geo.setAttribute('aLocal', new THREE.BufferAttribute(new Float32Array((DSEG + 1) * (DSEG + 1) * 2), 2));
      const mat = new THREE.ShaderMaterial({
        uniforms: { uShape: { value: 0 }, uDim: { value: new THREE.Vector4(1, 0, 0, 0) }, uProgress: { value: 0 }, uColor: { value: new THREE.Color() }, uAlpha: { value: 1 }, uTime: { value: 0 } },
        vertexShader: decalVert, fragmentShader: decalFrag, transparent: true, depthWrite: false, side: THREE.DoubleSide,
        polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4,
      });
      const m = new THREE.Mesh(geo, mat);
      m.visible = false; m.frustumCulled = false; m.renderOrder = 3;
      scene.add(m);
      this.pool.push({ mesh: m, active: false });
    }
  }

  // shape: 'circle' {r}, 'ring' {r, inner}, 'rect' {len, width, angle}, 'cone' {r, halfAngle, angle}
  spawn(shape, x, z, opts) {
    let d = this.pool.find((p) => !p.active);
    if (!d) d = this.pool[0];
    d.active = true;
    d.t = 0;
    d.dur = opts.dur ?? 1;
    d.fade = opts.fade ?? 0.25;
    d.flash = !!opts.flash;
    d.follow = opts.follow || null;
    const m = d.mesh, u = m.material.uniforms;
    const code = { circle: 0, ring: 1, rect: 2, cone: 3 }[shape];
    u.uShape.value = code;
    const ang = opts.angle ?? 0;
    let ext;
    if (code === 0) { u.uDim.value.set(opts.r, 0, 0, 0); ext = opts.r; }
    else if (code === 1) { u.uDim.value.set(opts.r, opts.inner, 0, 0); ext = opts.r; }
    else if (code === 2) { u.uDim.value.set(opts.len, opts.width, 0, 0); ext = Math.max(opts.len, opts.width); }
    else { u.uDim.value.set(opts.r, opts.halfAngle, 0, 0); ext = opts.r; }
    u.uColor.value.set(opts.color || '#ff5a6e');
    u.uAlpha.value = opts.alpha ?? 1;
    u.uProgress.value = d.flash ? 1 : 0;
    d.shape = { code, x, z, ang, ext };
    this._conform(d);
    m.visible = true;
    return d;
  }

  _conform(d) {
    const { code, x, z, ang, ext } = d.shape;
    const geo = d.mesh.geometry;
    const pos = geo.attributes.position.array, loc = geo.attributes.aLocal.array;
    const n = DSEG + 1;
    const ca = Math.cos(ang), sa = Math.sin(ang);
    // rect grows forward from origin along +local y; others centred.
    const oy = code === 2 ? ext / 2 : 0, half = ext + 0.2;
    const baseY = this.world.height(x, z);
    for (let j = 0; j < n; j++) {
      for (let i = 0; i < n; i++) {
        const k = j * n + i;
        const lx = (i / DSEG - 0.5) * 2 * half, ly = (j / DSEG - 0.5) * 2 * half + oy;
        // local forward (ly) points along the facing angle.
        const wx = x + lx * ca + ly * sa, wz = z - lx * sa + ly * ca;
        pos[k * 3] = wx - x; pos[k * 3 + 1] = Math.max(this.world.height(wx, wz), this.world.inRift ? 0 : -0.1) - baseY + 0.12; pos[k * 3 + 2] = wz - z;
        loc[k * 2] = lx; loc[k * 2 + 1] = ly;
      }
    }
    geo.attributes.position.needsUpdate = true;
    geo.attributes.aLocal.needsUpdate = true;
    geo.computeBoundingSphere();
    d.mesh.position.set(x, baseY, z);
  }

  move(d, x, z) { d.shape.x = x; d.shape.z = z; this._conform(d); }

  release(d) { if (d) { d.active = false; d.mesh.visible = false; } }

  update(dt) {
    for (const d of this.pool) {
      if (!d.active) continue;
      d.t += dt;
      const u = d.mesh.material.uniforms;
      if (d.flash) {
        u.uAlpha.value = clamp(1 - d.t / d.dur, 0, 1);
        if (d.t >= d.dur) this.release(d);
      } else if (d.manual) {
        // progress set by owner
      } else {
        u.uProgress.value = clamp(d.t / d.dur, 0, 1);
        if (d.t >= d.dur + d.fade) this.release(d);
        else if (d.t > d.dur) u.uAlpha.value = 1 - (d.t - d.dur) / d.fade;
      }
      if (d.follow) { const p = d.follow(); if (p) { d.mesh.position.x = p.x; d.mesh.position.z = p.z; } }
    }
  }

  clear() { for (const d of this.pool) this.release(d); }
}

// ---------------------------------------------------------------- overlay
export class Overlay {
  constructor(canvas, camera) {
    this.cv = canvas;
    this.cx = canvas.getContext('2d');
    this.camera = camera;
    this.texts = [];
    this.v = new THREE.Vector3();
    this.resize();
  }

  resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.dpr = dpr;
    this.cv.width = Math.floor(window.innerWidth * dpr);
    this.cv.height = Math.floor(window.innerHeight * dpr);
    this.w = window.innerWidth; this.h = window.innerHeight;
  }

  project(x, y, z) {
    this.v.set(x, y, z).project(this.camera);
    if (this.v.z > 1) return null;
    return { x: (this.v.x * 0.5 + 0.5) * this.w, y: (-this.v.y * 0.5 + 0.5) * this.h };
  }

  text(x, y, z, str, color = '#fff', size = 18, opts = {}) {
    if (this.texts.length > 70) this.texts.shift();
    this.texts.push({ x, y, z, str, color, size, t: 0, life: opts.life ?? 0.9, rise: opts.rise ?? 1.6, jitter: (Math.random() - 0.5) * 18, bold: opts.bold ?? true, stroke: opts.stroke ?? true });
  }

  draw(dt, bars, labels) {
    const c = this.cx;
    c.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    c.clearRect(0, 0, this.w, this.h);
    // Ground labels (loot names) first.
    c.textAlign = 'center'; c.textBaseline = 'middle';
    for (const l of labels) {
      const p = this.project(l.x, l.y, l.z);
      if (!p) continue;
      c.font = '600 12px system-ui, sans-serif';
      const w = c.measureText(l.text).width + 10;
      c.fillStyle = 'rgba(20,14,34,0.72)';
      c.fillRect(p.x - w / 2, p.y - 9, w, 18);
      c.fillStyle = l.color;
      c.fillText(l.text, p.x, p.y);
    }
    // Health bars.
    for (const b of bars) {
      const p = this.project(b.x, b.y, b.z);
      if (!p) continue;
      const w = b.w, h = b.h;
      c.fillStyle = 'rgba(15,10,25,0.75)';
      c.fillRect(p.x - w / 2 - 1, p.y - 1, w + 2, h + 2);
      c.fillStyle = b.color;
      c.fillRect(p.x - w / 2, p.y, w * clamp(b.frac, 0, 1), h);
      if (b.tough !== undefined) {
        c.fillStyle = 'rgba(15,10,25,0.75)';
        c.fillRect(p.x - w / 2 - 1, p.y + h + 1, w + 2, 4);
        c.fillStyle = b.broken ? '#ff5470' : '#f5f0ff';
        c.fillRect(p.x - w / 2, p.y + h + 2, w * clamp(b.tough, 0, 1), 2);
      }
      if (b.name) {
        c.font = '700 11px system-ui, sans-serif';
        c.lineWidth = 3; c.strokeStyle = 'rgba(15,10,25,0.9)';
        c.strokeText(b.name, p.x, p.y - 8);
        c.fillStyle = b.nameColor || '#ffd978';
        c.fillText(b.name, p.x, p.y - 8);
      }
    }
    // Floating text.
    for (let i = this.texts.length - 1; i >= 0; i--) {
      const t = this.texts[i];
      t.t += dt;
      if (t.t > t.life) { this.texts.splice(i, 1); continue; }
      const p = this.project(t.x, t.y + t.t * t.rise, t.z);
      if (!p) continue;
      const k = t.t / t.life;
      const pop = k < 0.12 ? 1 + (0.12 - k) * 4 : 1;
      c.globalAlpha = k > 0.7 ? 1 - (k - 0.7) / 0.3 : 1;
      c.font = `${t.bold ? 800 : 600} ${Math.round(t.size * pop)}px system-ui, sans-serif`;
      if (t.stroke) { c.lineWidth = 4; c.strokeStyle = 'rgba(20,12,34,0.85)'; c.strokeText(t.str, p.x + t.jitter, p.y); }
      c.fillStyle = t.color;
      c.fillText(t.str, p.x + t.jitter, p.y);
      c.globalAlpha = 1;
    }
  }
}

// ---------------------------------------------------------------- beams
export function makeBeam(color) {
  const geo = new THREE.CylinderGeometry(0.18, 0.35, 14, 8, 1, true);
  geo.translate(0, 7, 0);
  const mat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.35, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
  const m = new THREE.Mesh(geo, mat);
  m.renderOrder = 4;
  return m;
}
