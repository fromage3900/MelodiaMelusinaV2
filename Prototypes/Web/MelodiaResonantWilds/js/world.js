// Open world: chunk-streamed terrain around the player (the OpenWorldJS idea
// of player-centred tiles, rebuilt for phones as small CPU chunks), five
// biomes from the Gaea setups arranged around Shorewake Village, props,
// landmarks, water and the rift arena.

import * as THREE from 'three';
import { Simplex2, mulberry32, clamp, lerp, smoothstep, angleDiff } from './util.js';
import { BIOMES, HUB, WORLD_RADIUS, WORLD_SEED, RIFT_STYLE } from './design.js';
import { environmentMaterial, legacyRender } from './cel.js';

export const CHUNK = 64;
const SEG = 28;
const VIEW = 2;
export const WATER = 0;
const BIOME_R = 390;
const SIGMA = 0.28;
export const RIFT_RADIUS = 34;

const _c1 = new THREE.Color(), _c2 = new THREE.Color(), _c3 = new THREE.Color();

function col(hex) { return new THREE.Color(hex); }

export class World {
  constructor(game) {
    this.game = game;
    this.scene = game.scene;
    this.N = new Simplex2(WORLD_SEED);
    this.N2 = new Simplex2(WORLD_SEED + 17);
    this.W = new Float32Array(BIOMES.length);
    this.hub = 0;
    this.r = 0;
    this.inRift = false;
    for (const b of BIOMES) {
      b.cx = Math.cos(b.angle) * BIOME_R;
      b.cz = Math.sin(b.angle) * BIOME_R;
      b.pal = Object.fromEntries(Object.entries(b.colors).map(([k, v]) => [k, col(v)]));
    }
    this.hubPal = Object.fromEntries(Object.entries(HUB.colors).map(([k, v]) => [k, col(v)]));
    this.riftPal = Object.fromEntries(Object.entries(RIFT_STYLE.colors).map(([k, v]) => [k, col(v)]));

    this.root = new THREE.Group();
    this.scene.add(this.root);
    this.chunks = new Map();
    this.queue = [];
    this.chimes = [];

    this.uniforms = {
      uTime: { value: 0 },
      uRipple: { value: new THREE.Vector4(0, 0, -99, 0) },
      uRipple2: { value: new THREE.Vector4(0, 0, -99, 0) },
      uPlayer: { value: new THREE.Vector3() },
      uCres: { value: 0 },
      uRingColor: { value: new THREE.Color('#ffe8b0') },
      uChladni: { value: 0.65 },
      uCaustics: { value: 0.55 },
      uIsRift: { value: 0 },
    };
    // Compare new effects with ?chladni=0 and/or ?caustics=0.
    const shaderFlags = new URLSearchParams(window.location.search);
    if (shaderFlags.get('chladni') === '0') this.uniforms.uChladni.value = 0;
    if (shaderFlags.get('caustics') === '0') this.uniforms.uCaustics.value = 0;
    if (legacyRender) { this.uniforms.uChladni.value = 0; this.uniforms.uCaustics.value = 0; }
    this.terrainMat = environmentMaterial('#ffffff', { vertexColors: true });
    this._resonate(this.terrainMat);
    this._buildIndex();
    this._buildPropLibrary();
    this._buildWater();
    this._buildHub();
    this._buildLandmarks();
    this._buildRift();
  }

  // ------------------------------------------------------------------ sampling
  sample(x, z) {
    const r = Math.hypot(x, z);
    this.r = r;
    const warp = this.N2.noise(x * 0.0025, z * 0.0025) * 0.35;
    const a = Math.atan2(z, x) + warp;
    let sum = 0;
    for (let i = 0; i < BIOMES.length; i++) {
      const d = angleDiff(a, BIOMES[i].angle);
      const w = Math.exp(-(d * d) / (2 * SIGMA * SIGMA));
      this.W[i] = w; sum += w;
    }
    for (let i = 0; i < BIOMES.length; i++) this.W[i] /= sum;
    this.hub = 1 - smoothstep(HUB.radius, HUB.radius + 45, r);
    let h = 0, used = 0;
    for (let i = 0; i < BIOMES.length; i++) {
      const w = this.W[i];
      if (w < 0.012) continue;
      h += w * this._biomeHeight(BIOMES[i], x, z);
      used += w;
    }
    h /= used;
    if (this.hub > 0) h = lerp(h, 2.2 + this.N.noise(x * 0.05, z * 0.05) * 0.15, this.hub);
    h = lerp(h, -14, smoothstep(WORLD_RADIUS - 80, WORLD_RADIUS + 10, r));
    return h;
  }

  height(x, z) {
    if (this.inRift) return 0;
    return this.sample(x, z);
  }

  dominantBiome(x, z) {
    this.sample(x, z);
    let bi = 0;
    for (let i = 1; i < BIOMES.length; i++) if (this.W[i] > this.W[bi]) bi = i;
    return { biome: BIOMES[bi], index: bi, weight: this.W[bi], hub: this.hub, r: this.r };
  }

  // Level of the zone at a point: rises through each biome with distance.
  zoneLevel(x, z) {
    const d = this.dominantBiome(x, z);
    const t = clamp((d.r - 90) / 520, 0, 1);
    return Math.round(lerp(d.biome.levels[0], d.biome.levels[1], t));
  }

  _rivers(h, x, z, width, depth = -0.7) {
    const rv = Math.abs(this.N.noise(x * 0.0021 + 31.7, z * 0.0021 - 12.3));
    if (rv < width) h = lerp(h, depth, smoothstep(0, 0.75, 1 - rv / width));
    return h;
  }

  _biomeHeight(b, x, z) {
    const N = this.N;
    const dc = Math.hypot(x - b.cx, z - b.cz);
    switch (b.id) {
      case 'sakura_terrace': {
        let h = 2.4 + (N.fbm(x * 0.0042, z * 0.0042, 4) * 0.5 + 0.5) * b.amp;
        const step = 2.6, t = h / step, f = t - Math.floor(t);
        h = lerp(h, step * (Math.floor(t) + f * f * f * f), clamp(b.terrace * 4, 0, 0.85));
        return this._rivers(h, x, z, 0.03 + 0.04 * b.flow);
      }
      case 'liquid_cathedral': {
        let h = 1.8 + (N.fbm(x * 0.0035, z * 0.0035, 4) * 0.5 + 0.5) * b.amp * 0.7;
        h -= 3 * (1 - smoothstep(0, 180, dc));
        h = this._rivers(h, x, z, 0.03 + 0.06 * b.flow);
        return lerp(h, -0.6, 1 - smoothstep(26, 44, dc));
      }
      case 'fugue_grotto': {
        const g = Math.abs(N.noise(x * 0.0075 + 100, z * 0.0075));
        return 1.2 + smoothstep(0.05, 0.3, g) * b.amp * 0.75 + N.fbm(x * 0.02, z * 0.02, 2) * 1.1;
      }
      case 'cadence_crystal_ridge': {
        const rg = 1 - Math.abs(N.fbm(x * 0.0055 - 50, z * 0.0055 + 20, 3));
        let h = 2.6 + rg * rg * b.amp * 0.8;
        if (b.radial) h += b.amp * 0.5 * (1 - smoothstep(0, 200, dc));
        return lerp(h, 3 + b.amp * 0.5, 1 - smoothstep(16, 30, dc));
      }
      case 'aurora_glacier': {
        let h = 2.6 + (N.fbm(x * 0.003 + 7, z * 0.003 - 3, 5) * 0.5 + 0.5) * b.amp * 0.55;
        const step = 5, t = h / step, f = t - Math.floor(t);
        h = lerp(h, step * (Math.floor(t) + f * f), 0.55);
        if (b.hasLakes) {
          const lk = N.noise(x * 0.004 - 40, z * 0.004 + 90);
          if (lk < -0.42) h = lerp(h, -0.5, smoothstep(-0.42, -0.58, lk));
        }
        return h;
      }
      default:
        return 2 + N.fbm(x * 0.004, z * 0.004, 3) * 6;
    }
  }

  // Vertex colour for a sampled point (call right after sample()).
  _color(x, z, h, slope, out) {
    out.setRGB(0, 0, 0);
    const n = this.N2.noise(x * 0.03, z * 0.03) * 0.5 + 0.5;
    const n2 = this.N2.noise(x * 0.11 + 9, z * 0.11) * 0.5 + 0.5;
    const rock = smoothstep(0.32, 0.6, slope);
    for (let i = 0; i < BIOMES.length; i++) {
      const w = this.W[i];
      if (w < 0.012) continue;
      const b = BIOMES[i], p = b.pal;
      _c1.copy(p.grass).lerp(p.grass2, smoothstep(0.55, 0.85, n) * 0.7);
      if (b.id === 'aurora_glacier') _c1.lerp(p.snow, 0.5 + 0.4 * n2);
      if (b.id === 'cadence_crystal_ridge' && h > 18) _c1.lerp(p.snow, smoothstep(18, 26, h));
      _c1.lerp(p.rock, rock);
      if (h < 0.7) _c1.lerp(p.sand, smoothstep(0.7, 0.1, h));
      out.r += _c1.r * w; out.g += _c1.g * w; out.b += _c1.b * w;
    }
    if (this.hub > 0) {
      const p = this.hubPal;
      _c2.copy(p.grass).lerp(p.grass2, n * 0.4);
      const r = this.r;
      if (r < 30) {
        // Plaza: a stave of five rings, like a score laid in the stone.
        const ring = Math.abs(((r % 5) + 5) % 5 - 2.5) < 0.25 && r > 8 && r < 28 ? 0.25 : 0;
        _c3.copy(p.sand).multiplyScalar(1 - ring);
        _c2.lerp(_c3, 1 - smoothstep(27, 30, r));
      }
      out.lerp(_c2, this.hub);
    }
    const v = 0.93 + n2 * 0.1;
    out.multiplyScalar(v);
    return out;
  }

  // ------------------------------------------------------------------ chunks
  _buildIndex() {
    const idx = [];
    const n = SEG + 1;
    for (let j = 0; j < SEG; j++) {
      for (let i = 0; i < SEG; i++) {
        const a = j * n + i, b = a + 1, c = a + n, d = c + 1;
        idx.push(a, c, b, b, c, d);
      }
    }
    this.index = new THREE.BufferAttribute(new Uint16Array(idx), 1);
  }

  _buildChunk(cx, cz) {
    const P = SEG + 3, n = SEG + 1, step = CHUNK / SEG;
    const x0 = cx * CHUNK, z0 = cz * CHUNK;
    const hp = new Float32Array(P * P);
    for (let j = 0; j < P; j++) for (let i = 0; i < P; i++) hp[j * P + i] = this.sample(x0 + (i - 1) * step, z0 + (j - 1) * step);
    const pos = new Float32Array(n * n * 3), nor = new Float32Array(n * n * 3), colr = new Float32Array(n * n * 3);
    const c = new THREE.Color();
    for (let j = 0; j < n; j++) {
      for (let i = 0; i < n; i++) {
        const k = j * n + i;
        const x = x0 + i * step, z = z0 + j * step;
        const h = hp[(j + 1) * P + (i + 1)];
        const hl = hp[(j + 1) * P + i], hr = hp[(j + 1) * P + i + 2];
        const hd = hp[j * P + i + 1], hu = hp[(j + 2) * P + i + 1];
        let nx = hl - hr, ny = 2 * step, nz = hd - hu;
        const inv = 1 / Math.hypot(nx, ny, nz);
        nx *= inv; ny *= inv; nz *= inv;
        pos[k * 3] = x; pos[k * 3 + 1] = h; pos[k * 3 + 2] = z;
        nor[k * 3] = nx; nor[k * 3 + 1] = ny; nor[k * 3 + 2] = nz;
        this.sample(x, z);
        this._color(x, z, h, 1 - ny, c);
        colr[k * 3] = c.r; colr[k * 3 + 1] = c.g; colr[k * 3 + 2] = c.b;
      }
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    geo.setAttribute('normal', new THREE.BufferAttribute(nor, 3));
    geo.setAttribute('color', new THREE.BufferAttribute(colr, 3));
    geo.setIndex(this.index);
    geo.computeBoundingSphere();
    const mesh = new THREE.Mesh(geo, this.terrainMat);
    mesh.matrixAutoUpdate = false;
    const group = new THREE.Group();
    group.add(mesh);
    const chimes = [];
    this._buildProps(cx, cz, group, chimes);
    this.root.add(group);
    return { cx, cz, group, geo, chimes };
  }

  _disposeChunk(ch) {
    this.root.remove(ch.group);
    ch.geo.dispose();
    ch.group.traverse((o) => { if (o.isInstancedMesh) o.dispose(); });
  }

  update(px, pz, budget = 1) {
    if (this.inRift) return;
    const ccx = Math.floor(px / CHUNK), ccz = Math.floor(pz / CHUNK);
    for (const [key, ch] of this.chunks) {
      if (Math.abs(ch.cx - ccx) > VIEW + 1 || Math.abs(ch.cz - ccz) > VIEW + 1) {
        this._disposeChunk(ch);
        this.chunks.delete(key);
      }
    }
    const want = [];
    for (let dz = -VIEW; dz <= VIEW; dz++) {
      for (let dx = -VIEW; dx <= VIEW; dx++) {
        const cx = ccx + dx, cz = ccz + dz;
        const key = cx + ',' + cz;
        if (this.chunks.has(key)) continue;
        if (Math.hypot(cx * CHUNK + CHUNK / 2, cz * CHUNK + CHUNK / 2) > WORLD_RADIUS + CHUNK * 1.5) continue;
        want.push({ cx, cz, key, d: dx * dx + dz * dz });
      }
    }
    want.sort((a, b) => a.d - b.d);
    for (let i = 0; i < Math.min(budget, want.length); i++) {
      const w = want[i];
      this.chunks.set(w.key, this._buildChunk(w.cx, w.cz));
    }
    this.chimes.length = 0;
    for (const ch of this.chunks.values()) for (const c of ch.chimes) this.chimes.push(c);
  }

  // ------------------------------------------------------------------ props
  _buildPropLibrary() {
    const L = (hex, o = {}) => environmentMaterial(hex, { flatShading: true, ...o });
    const M = (geo, mat, y = 0, sx = 1, sy = 1, sz = 1) => ({ geo, mat, m: new THREE.Matrix4().compose(new THREE.Vector3(0, y, 0), new THREE.Quaternion(), new THREE.Vector3(sx, sy, sz)) });
    const white = L('#ffffff');
    const glow = (hex) => L('#ffffff', { emissive: hex, emissiveIntensity: 0.55 });
    this.props = {
      sakura: { parts: [M(new THREE.CylinderGeometry(0.22, 0.4, 3.4, 6), L('#8a5a4a'), 1.7), M(new THREE.IcosahedronGeometry(2.2, 0), white, 4.4)], tint: 1, palette: ['#f7b8d2', '#f9c9dc', '#f3a6c6', '#fde0ea'] },
      flower: { parts: [M(new THREE.ConeGeometry(0.2, 0.55, 5), white, 0.27)], tint: 0, palette: ['#ffd1e3', '#ffffff', '#d8c3ff', '#fff1a8', '#ffb3c7'] },
      rock: { parts: [M(new THREE.DodecahedronGeometry(1, 0), white, 0.3, 1.3, 0.75, 1.1)], tint: 0, palette: ['#b7a9a6', '#a39a9f', '#c2b5ad'], rockTint: true },
      lantern: { parts: [M(new THREE.CylinderGeometry(0.07, 0.07, 1.8, 5), L('#6b4a3a'), 0.9), M(new THREE.BoxGeometry(0.42, 0.52, 0.42), glow('#ffcf7a'), 1.95)] },
      bell: { parts: [M(new THREE.CylinderGeometry(0.05, 0.05, 1.3, 4), L('#5f8f5a'), 0.65), M(new THREE.ConeGeometry(0.38, 0.55, 8, 1, true), glow('#9fe6ff'), 1.25)], chime: true },
      note: { parts: [M(new THREE.SphereGeometry(0.7, 10, 8), glow('#ffd66e'), 2.4, 1.2, 0.85, 1), M(new THREE.CylinderGeometry(0.12, 0.12, 3.2, 6), glow('#ffd66e'), 4.0), M(new THREE.BoxGeometry(0.9, 0.35, 0.12), glow('#ffd66e'), 5.4)], offsetX: [0, 0.62, 1.05] },
      pillar: { parts: [M(new THREE.CylinderGeometry(0.7, 0.85, 9, 10), L('#eef2f6'), 4.5), M(new THREE.BoxGeometry(2, 0.5, 2), L('#dfe7ee'), 9.2)] },
      reed: { parts: [M(new THREE.ConeGeometry(0.09, 1.9, 4), L('#6fae7c'), 0.95)], water: 'shore' },
      lily: { parts: [M(new THREE.CylinderGeometry(0.65, 0.65, 0.05, 9), L('#5fb37a'), 0.02), M(new THREE.ConeGeometry(0.18, 0.3, 6), L('#fbd3e6'), 0.2)], water: 'on' },
      stalagmite: { parts: [M(new THREE.ConeGeometry(0.85, 4.2, 6), white, 2.1)], tint: 0, palette: ['#8f7f95', '#7d6f8a', '#a08c86'] },
      mushroom: { parts: [M(new THREE.CylinderGeometry(0.15, 0.22, 1.3, 6), L('#e8dccb'), 0.65), M(new THREE.SphereGeometry(0.75, 10, 6, 0, Math.PI * 2, 0, Math.PI / 2), glow('#63e6d0'), 1.3)] },
      crystal: { parts: [M(new THREE.OctahedronGeometry(1, 0), L('#ffffff', { emissive: '#6d5bd0', emissiveIntensity: 0.35 }), 1.9, 0.55, 2.4, 0.55)], tint: 0, palette: ['#d7c4ff', '#9fe0ff', '#ffc4f0', '#c4fff0'] },
      spire: { parts: [M(new THREE.OctahedronGeometry(1, 0), L('#ffffff', { emissive: '#8a6cff', emissiveIntensity: 0.4 }), 7, 1.4, 8, 1.4)] },
      pine: { parts: [M(new THREE.CylinderGeometry(0.15, 0.2, 1.2, 5), L('#6b5044'), 0.6), M(new THREE.ConeGeometry(1.5, 4.2, 7), L('#4f7f78'), 3.0), M(new THREE.ConeGeometry(0.7, 1.4, 7), L('#ffffff'), 4.6)] },
      icespike: { parts: [M(new THREE.ConeGeometry(0.6, 3.6, 5), L('#bfe9ff', { emissive: '#4aa8d8', emissiveIntensity: 0.25 }), 1.8)] },
    };
    // Note sculpture pieces are offset sideways (head / stem / flag).
    const np = this.props.note;
    np.parts.forEach((p, i) => p.m.setPosition(np.offsetX[i], p.m.elements[13], 0));
  }

  _buildProps(cx, cz, group, chimes) {
    const rng = mulberry32((cx * 73856093) ^ (cz * 19349663) ^ WORLD_SEED);
    const x0 = cx * CHUNK, z0 = cz * CHUNK;
    const center = this.dominantBiome(x0 + CHUNK / 2, z0 + CHUNK / 2);
    if (center.r < HUB.radius + 10 || center.r > WORLD_RADIUS - 30) return;
    const buckets = new Map();
    const tmpQ = new THREE.Quaternion(), tmpE = new THREE.Euler(), tmpS = new THREE.Vector3(), tmpP = new THREE.Vector3(), tmpM = new THREE.Matrix4();
    const pois = this.game.poiNear ? this.game.poiNear(x0 + CHUNK / 2, z0 + CHUNK / 2, CHUNK) : [];
    for (let bi = 0; bi < BIOMES.length; bi++) {
      this.sample(x0 + CHUNK / 2, z0 + CHUNK / 2);
      const bw = this.W[bi];
      if (bw < 0.1) continue;
      const b = BIOMES[bi];
      for (const [type, count] of b.props) {
        const def = this.props[type];
        const tries = Math.floor(count * bw + rng());
        for (let t = 0; t < tries; t++) {
          const x = x0 + rng() * CHUNK, z = z0 + rng() * CHUNK;
          const h = this.sample(x, z);
          if (this.hub > 0.01 || this.r > WORLD_RADIUS - 40) continue;
          if (rng() > this.W[bi] * 1.4) continue;
          if (def.water === 'on') { if (h > -0.15) continue; }
          else if (def.water === 'shore') { if (h < -0.3 || h > 1.0) continue; }
          else if (h < 0.35) continue;
          const hx = this.sample(x + 1.5, z), hz = this.sample(x, z + 1.5);
          if (!def.water && (Math.abs(hx - h) > 1.6 || Math.abs(hz - h) > 1.6) && type !== 'rock' && type !== 'crystal') continue;
          let blocked = false;
          for (const p of pois) if ((p.x - x) ** 2 + (p.z - z) ** 2 < 49) { blocked = true; break; }
          if (blocked) continue;
          const s = type === 'flower' ? 0.7 + rng() * 0.8 : 0.75 + rng() * 0.6;
          const y = def.water === 'on' ? WATER : h - 0.05;
          tmpE.set(type === 'rock' ? rng() * 0.5 : 0, rng() * Math.PI * 2, type === 'rock' ? rng() * 0.4 : 0);
          tmpQ.setFromEuler(tmpE);
          tmpP.set(x, y, z);
          tmpS.set(s, s * (type === 'crystal' ? 0.7 + rng() * 0.9 : 1), s);
          tmpM.compose(tmpP, tmpQ, tmpS);
          let colorHex = null;
          if (def.palette) colorHex = def.palette[Math.floor(rng() * def.palette.length)];
          if (def.rockTint) colorHex = '#' + b.pal.rock.clone().multiplyScalar(0.9 + rng() * 0.25).getHexString();
          if (!buckets.has(type)) buckets.set(type, []);
          buckets.get(type).push({ m: tmpM.clone(), c: colorHex });
          if (def.chime) chimes.push({ x, z, y: y + 1.25, i: Math.floor(rng() * 8), last: 0 });
        }
      }
    }
    const pm = new THREE.Matrix4(), cc = new THREE.Color();
    for (const [type, list] of buckets) {
      const def = this.props[type];
      def.parts.forEach((part, pi) => {
        const im = new THREE.InstancedMesh(part.geo, part.mat, list.length);
        list.forEach((it, k) => {
          pm.multiplyMatrices(it.m, part.m);
          im.setMatrixAt(k, pm);
          if (it.c && (def.tint === undefined || def.tint === pi)) im.setColorAt(k, cc.set(it.c));
          else if (def.palette || def.rockTint) im.setColorAt(k, cc.set('#ffffff'));
        });
        im.instanceMatrix.needsUpdate = true;
        if (im.instanceColor) im.instanceColor.needsUpdate = true;
        im.computeBoundingSphere();
        group.add(im);
      });
    }
  }

  // ------------------------------------------------------------------ resonance shader
  // Beat ripples and a Crescendo glow painted into any Lambert/Phong material.
  _resonate(mat) {
    const U = this.uniforms;
    mat.onBeforeCompile = (sh) => {
      Object.assign(sh.uniforms, U);
      sh.vertexShader = sh.vertexShader
        .replace('#include <common>', '#include <common>\nvarying vec3 vWP;')
        .replace('#include <begin_vertex>', '#include <begin_vertex>\nvWP = (modelMatrix * vec4(transformed, 1.0)).xyz;');
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', `#include <common>
          varying vec3 vWP; uniform float uTime; uniform vec4 uRipple; uniform vec4 uRipple2; uniform vec3 uPlayer; uniform float uCres; uniform vec3 uRingColor; uniform float uChladni; uniform float uCaustics; uniform float uIsRift;
          float ripple(vec4 r){ float age = uTime - r.z; if(age < 0.0 || age > 1.2) return 0.0; float d = distance(vWP.xz, r.xy); float rad = age * 30.0; return exp(-pow((d - rad) / 1.4, 2.0)) * r.w * (1.0 - age / 1.2); }
          float rwChladni(vec2 p) {
            vec2 q = (p - uPlayer.xz) * 0.24;
            float a = sin(q.x * 2.0) * sin(q.y * 3.0);
            float b = sin(q.x * 3.0) * sin(q.y * 2.0);
            return 1.0 - smoothstep(0.018, 0.09, abs(a - b));
          }
          float rwCaustic(vec2 p, float t) {
            vec2 q = p * 0.73;
            float waves = sin(q.x + t * 0.87) * sin(q.y - t * 0.63);
            float cross = sin((q.x + q.y) * 0.85 - t * 0.47);
            return pow(max(0.0, 0.55 + 0.28 * waves + 0.22 * cross), 5.0);
          }`)
        .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
          float pd = distance(vWP.xz, uPlayer.xz);
          float glow = exp(-pow(pd / (3.0 + uCres * 5.0), 2.0)) * (0.06 + uCres * 0.22);
          float musicalZone = 1.0 - smoothstep(7.0, 18.0, pd);
          float scoreLines = rwChladni(vWP.xz) * musicalZone * (0.15 + uCres * 0.85) * uChladni;
          // Caustics affect shallow terrain, not the rift floor.
          float shore = 1.0 - smoothstep(0.0, 2.2, abs(vWP.y));
          float causticLight = rwCaustic(vWP.xz, uTime) * shore * uCaustics * (1.0 - uIsRift);
          totalEmissiveRadiance += uRingColor * (ripple(uRipple) * 0.45 + ripple(uRipple2) * 0.7 + glow + scoreLines * 0.38);
          totalEmissiveRadiance += vec3(0.28, 0.70, 0.90) * causticLight * 0.3;`);
    };
    mat.customProgramCacheKey = () => 'resonate-cel-v1';
  }

  pulse(x, z, strength = 1, big = false) {
    const u = big ? this.uniforms.uRipple2 : this.uniforms.uRipple;
    u.value.set(x, z, this.uniforms.uTime.value, strength);
  }

  // ------------------------------------------------------------------ water
  _buildWater() {
    const geo = new THREE.PlaneGeometry(300, 300, 60, 60);
    geo.rotateX(-Math.PI / 2);
    const mat = new THREE.MeshPhongMaterial({ color: '#7fd0e4', transparent: true, opacity: 0.78, shininess: 90, specular: new THREE.Color('#ffffff'), depthWrite: false });
    const U = this.uniforms;
    mat.onBeforeCompile = (sh) => {
      Object.assign(sh.uniforms, U);
      sh.vertexShader = sh.vertexShader
        .replace('#include <common>', '#include <common>\nuniform float uTime; varying vec3 vWP;')
        .replace('#include <begin_vertex>', `#include <begin_vertex>
          vec3 wp0 = (modelMatrix * vec4(transformed, 1.0)).xyz;
          float w1 = sin(wp0.x * 0.18 + uTime * 1.3) * 0.12 + sin(wp0.z * 0.23 + uTime * 1.7) * 0.1 + sin((wp0.x + wp0.z) * 0.41 + uTime * 2.3) * 0.05;
          transformed.y += w1;
          vWP = wp0;`)
        .replace('#include <beginnormal_vertex>', `#include <beginnormal_vertex>
          { vec3 wpn = (modelMatrix * vec4(position, 1.0)).xyz;
            float dx = cos(wpn.x * 0.18 + uTime * 1.3) * 0.12 * 0.18 + cos((wpn.x + wpn.z) * 0.41 + uTime * 2.3) * 0.05 * 0.41;
            float dz = cos(wpn.z * 0.23 + uTime * 1.7) * 0.1 * 0.23 + cos((wpn.x + wpn.z) * 0.41 + uTime * 2.3) * 0.05 * 0.41;
            objectNormal = normalize(vec3(-dx, 1.0, -dz)); }`);
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', `#include <common>
          varying vec3 vWP; uniform float uTime; uniform vec4 uRipple; uniform vec4 uRipple2; uniform vec3 uRingColor; uniform float uCaustics;
          float ripple(vec4 r){ float age = uTime - r.z; if(age < 0.0 || age > 1.2) return 0.0; float d = distance(vWP.xz, r.xy); float rad = age * 30.0; return exp(-pow((d - rad) / 1.4, 2.0)) * r.w * (1.0 - age / 1.2); }`)
        .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
          float sparkle = pow(max(0.0, sin(vWP.x * 1.7 + uTime * 2.0) * sin(vWP.z * 1.3 - uTime * 1.6)), 12.0) * 0.35;
          float waterCaustic = pow(max(0.0, 0.5 + 0.5 * sin(vWP.x * 0.78 + uTime * 0.9) * sin(vWP.z * 0.93 - uTime * 0.64)), 6.0);
          totalEmissiveRadiance += uRingColor * (ripple(uRipple) * 0.5 + ripple(uRipple2) * 0.7) + vec3(sparkle);
          totalEmissiveRadiance += vec3(0.3, 0.65, 0.95) * waterCaustic * uCaustics * 0.38;`);
    };
    mat.customProgramCacheKey = () => 'water-caustics-v1';
    this.water = new THREE.Mesh(geo, mat);
    this.water.position.y = WATER;
    this.water.renderOrder = 2;
    this.scene.add(this.water);
  }

  // ------------------------------------------------------------------ hub + landmarks
  _buildHub() {
    const g = new THREE.Group();
    const L = (hex, o = {}) => environmentMaterial(hex, { flatShading: true, ...o });
    const add = (geo, mat, x, y, z, ry = 0) => { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.rotation.y = ry; g.add(m); return m; };
    const h = 2.2;
    // Metronome obelisk: its pendulum swings on the beat (see update()).
    add(new THREE.CylinderGeometry(1.2, 1.8, 1.2, 8), L('#e8dccb'), 0, h + 0.6, 0);
    add(new THREE.ConeGeometry(1.1, 7, 4), L('#f4ecff'), 0, h + 4.6, 0, Math.PI / 4);
    this.pendulum = new THREE.Group();
    this.pendulum.position.set(0, h + 7.6, 0.9);
    const rod = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 5.2, 5), L('#d9bc72', { emissive: '#d9bc72', emissiveIntensity: 0.3 }));
    rod.position.y = -2.6;
    const bob = new THREE.Mesh(new THREE.OctahedronGeometry(0.45, 0), L('#ffe7a8', { emissive: '#ffcf6a', emissiveIntensity: 0.7 }));
    bob.position.y = -4.4;
    this.pendulum.add(rod, bob);
    g.add(this.pendulum);
    // Pavilions (shell-roofed huts) around the plaza.
    const hutPos = [[-20, -14, '#f3b6cf'], [20, -14, '#9fd4e6'], [-22, 14, '#c8b6ef'], [22, 14, '#ffd98a']];
    for (const [x, z, roof] of hutPos) {
      add(new THREE.CylinderGeometry(3, 3.2, 3.2, 8), L('#fbf5ee'), x, h + 1.6, z);
      add(new THREE.ConeGeometry(4.2, 3, 8), L(roof), x, h + 4.6, z);
      add(new THREE.BoxGeometry(1.4, 2.2, 0.3), L('#8a6a5a'), x, h + 1.1, z + (z < 0 ? 3.1 : -3.1));
    }
    // Forge anvil (north-east) and bounty board (north-west) + blessing font (south).
    this.forgePos = new THREE.Vector3(11, h, -9);
    add(new THREE.BoxGeometry(1.8, 0.7, 0.9), L('#6d6d78'), 11, h + 1.05, -9);
    add(new THREE.CylinderGeometry(0.35, 0.5, 0.7, 6), L('#4e4e58'), 11, h + 0.35, -9);
    const fire = add(new THREE.IcosahedronGeometry(0.6, 0), L('#ff9a4a', { emissive: '#ff7a2a', emissiveIntensity: 1 }), 12.8, h + 0.6, -8.4);
    this.forgeFire = fire;
    this.boardPos = new THREE.Vector3(-11, h, -9);
    add(new THREE.BoxGeometry(3, 2, 0.2), L('#a07a5a'), -11, h + 2.1, -9);
    add(new THREE.BoxGeometry(0.2, 3, 0.2), L('#6b4a3a'), -12.4, h + 1.5, -9);
    add(new THREE.BoxGeometry(0.2, 3, 0.2), L('#6b4a3a'), -9.6, h + 1.5, -9);
    for (let i = 0; i < 4; i++) add(new THREE.PlaneGeometry(0.6, 0.7), L('#fff6e0', { side: THREE.DoubleSide }), -12 + i * 0.66, h + 2.2 + (i % 2) * 0.2, -8.88);
    this.fontPos = new THREE.Vector3(0, h, 13);
    add(new THREE.CylinderGeometry(1.6, 1.2, 1, 10), L('#e0e8f0'), 0, h + 0.5, 13);
    add(new THREE.CylinderGeometry(1.35, 1.35, 0.1, 16), L('#8fe0ff', { emissive: '#5fc6ff', emissiveIntensity: 0.6 }), 0, h + 1.02, 13);
    // Lanterns around the plaza edge.
    for (let i = 0; i < 12; i++) {
      const a = (i / 12) * Math.PI * 2;
      add(new THREE.CylinderGeometry(0.08, 0.08, 2.4, 5), L('#6b4a3a'), Math.cos(a) * 31, h + 1.2, Math.sin(a) * 31);
      add(new THREE.BoxGeometry(0.5, 0.6, 0.5), L('#fff', { emissive: '#ffcf7a', emissiveIntensity: 0.7 }), Math.cos(a) * 31, h + 2.6, Math.sin(a) * 31);
    }
    this.hubGroup = g;
    this.root.add(g);
  }

  _buildLandmarks() {
    const L = (hex, o = {}) => environmentMaterial(hex, { flatShading: true, ...o });
    this.landmarks = [];
    for (const b of BIOMES) {
      const g = new THREE.Group();
      const y = this.sample(b.cx, b.cz);
      g.position.set(b.cx, 0, b.cz);
      const add = (geo, mat, x, yy, z, s = [1, 1, 1], r = [0, 0, 0]) => {
        const m = new THREE.Mesh(geo, mat); m.position.set(x, yy, z); m.scale.set(...s); m.rotation.set(...r); g.add(m); return m;
      };
      const gy = (x, z) => this.sample(b.cx + x, b.cz + z);
      if (b.id === 'sakura_terrace') {
        add(new THREE.CylinderGeometry(1.2, 2.2, 16, 8), L('#7a4e40'), 0, y + 8, 0);
        for (let i = 0; i < 6; i++) {
          const a = (i / 6) * Math.PI * 2;
          add(new THREE.IcosahedronGeometry(4 + (i % 2), 0), L('#f7b8d2'), Math.cos(a) * 4, y + 16 + (i % 3), Math.sin(a) * 4);
        }
        add(new THREE.IcosahedronGeometry(5.5, 0), L('#fbd0e1'), 0, y + 19, 0);
      } else if (b.id === 'liquid_cathedral') {
        for (let i = 0; i < 10; i++) {
          const a = (i / 10) * Math.PI * 2, px = Math.cos(a) * 30, pz = Math.sin(a) * 30;
          add(new THREE.CylinderGeometry(1.1, 1.3, 14, 10), L('#eef3f8'), px, gy(px, pz) + 7, pz);
          add(new THREE.TorusGeometry(9.4, 0.6, 6, 16, Math.PI), L('#e3ebf3'), px * 0.84, gy(px, pz) + 14, pz * 0.84, [1, 1, 1], [0, -a + Math.PI / 2, 0]);
        }
        add(new THREE.OctahedronGeometry(3, 0), L('#ffffff', { emissive: '#5fc6ff', emissiveIntensity: 0.6 }), 0, 7, 0, [1, 2, 1]);
      } else if (b.id === 'fugue_grotto') {
        for (let i = 0; i < 14; i++) {
          const a = (i / 14) * Math.PI * 2, rr = 22 + (i % 3) * 4, px = Math.cos(a) * rr, pz = Math.sin(a) * rr;
          add(new THREE.ConeGeometry(2.4, 12 + (i % 4) * 3, 6), L('#6f6474'), px, gy(px, pz) + 6, pz, [1, 1, 1], [0, 0, (i % 2 ? 0.25 : -0.25)]);
        }
        for (let i = 0; i < 6; i++) {
          const a = (i / 6) * Math.PI * 2, px = Math.cos(a) * 10, pz = Math.sin(a) * 10;
          add(new THREE.OctahedronGeometry(1.6, 0), L('#ffffff', { emissive: '#9a7bf0', emissiveIntensity: 0.7 }), px, gy(px, pz) + 2.5, pz, [0.7, 2, 0.7]);
        }
      } else if (b.id === 'cadence_crystal_ridge') {
        add(new THREE.OctahedronGeometry(3.2, 0), L('#ffffff', { emissive: '#8a6cff', emissiveIntensity: 0.55 }), 0, y + 14, 0, [1, 5, 1]);
        for (let i = 0; i < 8; i++) {
          const a = (i / 8) * Math.PI * 2, px = Math.cos(a) * 9, pz = Math.sin(a) * 9;
          add(new THREE.OctahedronGeometry(1.4, 0), L('#ffffff', { emissive: i % 2 ? '#62c8ff' : '#e38bff', emissiveIntensity: 0.5 }), px, gy(px, pz) + 4, pz, [1, 3, 1], [0.2, a, 0.2]);
        }
      } else if (b.id === 'aurora_glacier') {
        for (let i = 0; i < 11; i++) {
          const hgt = 6 + Math.sin(i * 0.7) * 3 + (5 - Math.abs(i - 5)) * 1.6;
          add(new THREE.CylinderGeometry(0.9, 0.9, hgt, 10), L('#dff3ff', { emissive: '#7fc8ff', emissiveIntensity: 0.25 }), (i - 5) * 2.1, y + hgt / 2, -12);
        }
        const aur = new THREE.Mesh(new THREE.PlaneGeometry(70, 16, 1, 1), new THREE.MeshBasicMaterial({ color: '#8fffd8', transparent: true, opacity: 0.18, side: THREE.DoubleSide, blending: THREE.AdditiveBlending, depthWrite: false }));
        aur.position.set(0, y + 30, -30);
        g.add(aur);
      }
      g.userData.mats = [];
      g.traverse((o) => { if (o.material && !g.userData.mats.includes(o.material)) g.userData.mats.push(o.material); });
      this.landmarks.push(g);
      this.root.add(g);
    }
  }

  // ------------------------------------------------------------------ rift arena
  _buildRift() {
    const g = new THREE.Group();
    const floorMat = environmentMaterial('#3b2a55');
    this._resonate(floorMat);
    const floor = new THREE.Mesh(new THREE.CircleGeometry(RIFT_RADIUS + 4, 64), floorMat);
    floor.rotation.x = -Math.PI / 2;
    g.add(floor);
    // A stave of rings on the floor so beat ripples read against it.
    for (let i = 1; i <= 5; i++) {
      const ring = new THREE.Mesh(new THREE.RingGeometry(i * 6.4 - 0.12, i * 6.4 + 0.12, 64), new THREE.MeshBasicMaterial({ color: '#8f6bff', transparent: true, opacity: 0.35 }));
      ring.rotation.x = -Math.PI / 2; ring.position.y = 0.02;
      g.add(ring);
    }
    const pm = environmentMaterial('#2a2140', { flatShading: true });
    const cm = environmentMaterial('#ffffff', { emissive: '#8f6bff', emissiveIntensity: 0.6, flatShading: true });
    for (let i = 0; i < 12; i++) {
      const a = (i / 12) * Math.PI * 2;
      const p = new THREE.Mesh(new THREE.CylinderGeometry(1, 1.3, 10, 6), pm);
      p.position.set(Math.cos(a) * (RIFT_RADIUS + 3), 5, Math.sin(a) * (RIFT_RADIUS + 3));
      g.add(p);
      const c = new THREE.Mesh(new THREE.OctahedronGeometry(0.9, 0), cm);
      c.position.set(Math.cos(a) * (RIFT_RADIUS + 3), 11.5, Math.sin(a) * (RIFT_RADIUS + 3));
      g.add(c);
    }
    g.visible = false;
    this.riftGroup = g;
    this.scene.add(g);
  }

  setRift(on) {
    this.inRift = on;
    this.uniforms.uIsRift.value = on ? 1 : 0;
    this.root.visible = !on;
    this.water.visible = !on;
    this.riftGroup.visible = on;
  }

  // Build every chunk around a point immediately (spawn / teleport).
  warm(px, pz) {
    this.update(px, pz, 25);
  }

  // Colour for fog/sky/water given the player's position.
  palette(px, pz, out) {
    if (this.inRift) { out.fog.copy(this.riftPal.fog); out.water.copy(this.riftPal.water); out.light.copy(this.riftPal.light); return; }
    this.sample(px, pz);
    out.fog.setRGB(0, 0, 0); out.water.setRGB(0, 0, 0); out.light.setRGB(0, 0, 0);
    for (let i = 0; i < BIOMES.length; i++) {
      const w = this.W[i], p = BIOMES[i].pal;
      out.fog.r += p.fog.r * w; out.fog.g += p.fog.g * w; out.fog.b += p.fog.b * w;
      out.water.r += p.water.r * w; out.water.g += p.water.g * w; out.water.b += p.water.b * w;
      out.light.r += p.light.r * w; out.light.g += p.light.g * w; out.light.b += p.light.b * w;
    }
    if (this.hub > 0) { out.fog.lerp(this.hubPal.fog, this.hub); out.water.lerp(this.hubPal.water, this.hub); out.light.lerp(this.hubPal.light, this.hub); }
  }

  frame(dt, t, player, beatPhase, crescendo) {
    const U = this.uniforms;
    U.uTime.value = t;
    U.uPlayer.value.copy(player);
    U.uCres.value = crescendo;
    if (!this.inRift) {
      const s = 300 / 60;
      this.water.position.x = Math.round(player.x / s) * s;
      this.water.position.z = Math.round(player.z / s) * s;
    }
    if (this.pendulum) this.pendulum.rotation.z = Math.sin(beatPhase * Math.PI) * 0.45 * (this._pendDir || 1);
    if (this.forgeFire) this.forgeFire.scale.setScalar(0.85 + Math.sin(t * 9) * 0.12);
    // Landmarks go translucent when Melusina is under them so the camera never loses her.
    for (const lm of this.landmarks) {
      const near = Math.hypot(lm.position.x - player.x, lm.position.z - player.z) < 48;
      if (lm.userData.faded === near) continue;
      lm.userData.faded = near;
      for (const m of lm.userData.mats) {
        if (!m.userData.base) m.userData.base = { t: m.transparent, o: m.opacity, d: m.depthWrite };
        const base = m.userData.base;
        m.transparent = near ? true : base.t;
        m.opacity = near ? Math.min(base.o, 0.28) : base.o;
        m.depthWrite = near ? false : base.d;
        m.needsUpdate = true;
      }
    }
  }

  swingPendulum() { this._pendDir = -(this._pendDir || 1); }

  // Low-res overview for the map (biome colour + height shading + water).
  overview(size = 180) {
    const cv = document.createElement('canvas');
    cv.width = cv.height = size;
    const cx = cv.getContext('2d');
    const img = cx.createImageData(size, size);
    const c = new THREE.Color();
    const ext = WORLD_RADIUS + 20;
    for (let j = 0; j < size; j++) {
      for (let i = 0; i < size; i++) {
        const x = -ext + (i / size) * ext * 2, z = -ext + (j / size) * ext * 2;
        const h = this.sample(x, z);
        const hx = this.sample(x + 4, z);
        if (h < WATER) {
          c.set('#6ec3dc').lerp(new THREE.Color('#2f6f9a'), clamp(-h / 10, 0, 1));
        } else {
          this.sample(x, z);
          this._color(x, z, h, 0, c);
          c.multiplyScalar(clamp(0.95 + (hx - h) * 0.12, 0.7, 1.15));
        }
        const k = (j * size + i) * 4;
        img.data[k] = c.r * 255; img.data[k + 1] = c.g * 255; img.data[k + 2] = c.b * 255; img.data[k + 3] = 255;
      }
    }
    cx.putImageData(img, 0, 0);
    return { canvas: cv, extent: ext };
  }
}
