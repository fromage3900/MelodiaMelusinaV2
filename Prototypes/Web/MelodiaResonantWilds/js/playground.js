// Playground toys — silly Three.js juice, not UE canon.
// 1) Chladni sand that settles on nodal lines and detonates on Perfect
// 5) Oversized fashion gown (~40 m) with soft wind + enemy shove
// Enable by default; `?toys=0` turns the whole playground off.

import * as THREE from 'three';
import { toon } from './entities.js';

export function toysEnabled() {
  return new URLSearchParams(window.location.search).get('toys') !== '0';
}

const _c = new THREE.Color();
const _v = new THREE.Vector3();

// ------------------------------------------------------------------ Chladni sand
const SAND_N = 320;

export class ChladniSand {
  constructor(game) {
    this.g = game;
    this.px = new Float32Array(SAND_N);
    this.py = new Float32Array(SAND_N);
    this.pz = new Float32Array(SAND_N);
    this.vx = new Float32Array(SAND_N);
    this.vz = new Float32Array(SAND_N);
    this.settle = new Float32Array(SAND_N); // 0 free, 1 locked to a node
    this.alive = new Uint8Array(SAND_N);
    this._spawnAcc = 0;
    this._boom = 0;

    const geo = new THREE.SphereGeometry(0.11, 6, 5);
    const mat = toon('#e8d7a8', { emissive: '#c9a86a', emissiveIntensity: 0.35 });
    this.mesh = new THREE.InstancedMesh(geo, mat, SAND_N);
    this.mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    this.mesh.frustumCulled = false;
    this.mesh.count = SAND_N;
    game.scene.add(this.mesh);
    this._m = new THREE.Matrix4();
    this._s = new THREE.Object3D();
    for (let i = 0; i < SAND_N; i++) this.alive[i] = 0;
    this._hideAll();
  }

  _hideAll() {
    this._s.scale.setScalar(0);
    for (let i = 0; i < SAND_N; i++) {
      this._s.updateMatrix();
      this.mesh.setMatrixAt(i, this._s.matrix);
    }
    this.mesh.instanceMatrix.needsUpdate = true;
  }

  _field(x, z, cx, cz) {
    const U = this.g.world.uniforms;
    const n = U.uModeN?.value || 3;
    const m = U.uModeM?.value || 5;
    const phase = U.uPhase?.value || 0;
    const scale = 0.18;
    const PI = Math.PI;
    const qx = (x - cx) * scale;
    const qz = (z - cz) * scale;
    const a = Math.cos(n * PI * qx + phase) * Math.cos(m * PI * qz);
    const b = Math.cos(m * PI * qx) * Math.cos(n * PI * qz + phase * 0.7);
    return a - b;
  }

  _spawnOne(cx, cz, cy) {
    let i = -1;
    for (let k = 0; k < SAND_N; k++) if (!this.alive[k]) { i = k; break; }
    if (i < 0) i = (Math.random() * SAND_N) | 0;
    const ang = Math.random() * Math.PI * 2;
    const r = 1.2 + Math.random() * 7.5;
    this.px[i] = cx + Math.cos(ang) * r;
    this.pz[i] = cz + Math.sin(ang) * r;
    this.py[i] = cy + 0.4 + Math.random() * 1.8;
    this.vx[i] = (Math.random() - 0.5) * 2;
    this.vz[i] = (Math.random() - 0.5) * 2;
    this.settle[i] = 0;
    this.alive[i] = 1;
  }

  update(dt) {
    const g = this.g, P = g.player;
    if (P.dead) return;
    const cx = P.pos.x, cz = P.pos.z, cy = P.pos.y;
    this._spawnAcc += dt;
    const rate = 0.035 + (g.rhythm?.crescendo || 0) * 0.0004;
    while (this._spawnAcc > rate) {
      this._spawnAcc -= rate;
      this._spawnOne(cx, cz, cy);
    }
    this._boom = Math.max(0, this._boom - dt);

    for (let i = 0; i < SAND_N; i++) {
      if (!this.alive[i]) {
        this._s.position.set(0, -99, 0);
        this._s.scale.setScalar(0);
        this._s.updateMatrix();
        this.mesh.setMatrixAt(i, this._s.matrix);
        continue;
      }
      if (this.settle[i] >= 1) {
        // Soft shimmer on settled grains.
        this.py[i] = g.world.height(this.px[i], this.pz[i]) + 0.08 + Math.sin(g.time * 6 + i) * 0.02;
        this._s.position.set(this.px[i], this.py[i], this.pz[i]);
        this._s.scale.setScalar(0.85 + this._boom * 0.5);
        this._s.updateMatrix();
        this.mesh.setMatrixAt(i, this._s.matrix);
        continue;
      }

      const f = this._field(this.px[i], this.pz[i], cx, cz);
      // Gradient nudge toward |f| ≈ 0 (nodal lines).
      const eps = 0.35;
      const fx = (this._field(this.px[i] + eps, this.pz[i], cx, cz) - f) / eps;
      const fz = (this._field(this.px[i], this.pz[i] + eps, cx, cz) - f) / eps;
      const pull = Math.sign(f) * 4.5;
      this.vx[i] += -fx * pull * dt;
      this.vz[i] += -fz * pull * dt;
      this.vx[i] *= 1 - dt * 1.6;
      this.vz[i] *= 1 - dt * 1.6;
      this.px[i] += this.vx[i] * dt;
      this.pz[i] += this.vz[i] * dt;
      const ground = g.world.height(this.px[i], this.pz[i]) + 0.08;
      this.py[i] += (ground - this.py[i]) * Math.min(1, dt * 6);

      if (Math.abs(f) < 0.07 && Math.hypot(this.vx[i], this.vz[i]) < 1.2) {
        this.settle[i] = Math.min(1, this.settle[i] + dt * 2.8);
        if (this.settle[i] >= 1) {
          this.vx[i] = 0; this.vz[i] = 0;
        }
      } else {
        this.settle[i] = Math.max(0, this.settle[i] - dt);
      }

      // Despawn far grains.
      if (Math.hypot(this.px[i] - cx, this.pz[i] - cz) > 22) this.alive[i] = 0;

      this._s.position.set(this.px[i], this.py[i], this.pz[i]);
      this._s.scale.setScalar(0.55 + this.settle[i] * 0.55);
      this._s.updateMatrix();
      this.mesh.setMatrixAt(i, this._s.matrix);
    }
    this.mesh.instanceMatrix.needsUpdate = true;
  }

  /** Perfect (or Chladni Burst) detonates settled sand into a nodal firework. */
  explode(mult = 1) {
    const g = this.g, P = g.player;
    let n = 0;
    const hits = [];
    for (let i = 0; i < SAND_N; i++) {
      if (!this.alive[i] || this.settle[i] < 0.55) continue;
      n++;
      const ang = Math.random() * Math.PI * 2;
      const sp = 8 + Math.random() * 10 * mult;
      g.particles.emit(this.px[i], this.py[i] + 0.2, this.pz[i], _c.set('#ffe7a8'), {
        dir: { x: Math.cos(ang), y: 0.6 + Math.random() * 0.8, z: Math.sin(ang) },
        speed: sp, life: 0.7, kind: 3, size: 0.9, gravity: 4,
      });
      hits.push({ x: this.px[i], z: this.pz[i] });
      this.alive[i] = 0;
      this.settle[i] = 0;
    }
    if (!n) {
      // Still spray a little sand fireworks so Perfect always feels juicy.
      g.particles.burst(P.pos.x, P.pos.y + 0.6, P.pos.z, _c.set('#e8d7a8'), 18, { speed: 7, life: 0.55, kind: 0, size: 0.5 });
      return 0;
    }
    this._boom = 0.55;
    g.world.pulse(P.pos.x, P.pos.z, 1.4 + mult, true);
    g.shake(0.2 + 0.08 * mult);
    g.audio.chime?.(6);
    // Damage enemies near detonated grains.
    let dmgHits = 0;
    for (const h of hits) {
      for (const e of g.combat.enemiesIn('circle', { x: h.x, z: h.z, r: 2.4 })) {
        g.combat.damage(e, 0.55 * mult, { element: 'Arcane', tough: 0.8, skill: true });
        dmgHits++;
      }
    }
    if (n > 12) g.ui.toast(`Sand figure ✦ ${n} grains`, 'gold');
    return dmgHits;
  }
}

// ------------------------------------------------------------------ Mega gown (~40 m)
export class MegaGown {
  constructor(game) {
    this.g = game;
    this.on = false;
    const skirt = new THREE.Group();
    skirt.name = 'MegaGown';
    const mat = toon('#c8b6ef', { transparent: true, opacity: 0.72, emissive: '#8a6bb8', emissiveIntensity: 0.2, side: THREE.DoubleSide });
    // Layered cones — a ridiculous couture cathedral.
    const layers = [
      { r: 18, h: 4.5, y: 1.2, op: 0.55 },
      { r: 14, h: 5.5, y: 2.0, op: 0.65 },
      { r: 9, h: 6.5, y: 2.8, op: 0.75 },
      { r: 5, h: 7.2, y: 3.4, op: 0.85 },
    ];
    this.layers = [];
    for (const L of layers) {
      const m = mat.clone();
      m.opacity = L.op;
      const mesh = new THREE.Mesh(new THREE.ConeGeometry(L.r, L.h, 28, 1, true), m);
      mesh.position.y = L.y;
      mesh.rotation.x = Math.PI; // flare downward from waist
      skirt.add(mesh);
      this.layers.push({ mesh, baseR: L.r, baseY: L.y });
    }
    // Outer soft ring for "40 m fashion" read.
    const rim = new THREE.Mesh(
      new THREE.TorusGeometry(20, 0.35, 6, 48),
      toon('#ffd978', { emissive: '#d9bc72', emissiveIntensity: 0.55, transparent: true, opacity: 0.8 }),
    );
    rim.rotation.x = Math.PI / 2;
    rim.position.y = 0.4;
    skirt.add(rim);
    this.rim = rim;
    skirt.visible = false;
    game.scene.add(skirt);
    this.root = skirt;
    this._shoveAcc = 0;
  }

  set(on) {
    this.on = !!on;
    this.root.visible = this.on;
    if (this.on) {
      this.g.ui.toast('MEGA GOWN — 40 m couture collision + wind ♡', 'lavender');
      this.g.audio.chime?.(5);
      this.g.shake(0.35);
    } else {
      this.g.ui.toast('Mega gown packed away', 'soft');
    }
  }

  toggle() { this.set(!this.on); }

  update(dt) {
    const g = this.g, P = g.player;
    if (!this.on || P.dead) {
      this.root.visible = false;
      return;
    }
    this.root.visible = true;
    const wind = Math.sin(g.time * 1.7) * 0.08 + Math.sin(g.time * 0.41) * 0.04;
    const beat = 1 - g.beatPhase;
    this.root.position.set(P.pos.x, P.pos.y, P.pos.z);
    this.root.rotation.y = P.facing + wind * 0.6;
    for (let i = 0; i < this.layers.length; i++) {
      const L = this.layers[i];
      const breathe = 1 + Math.sin(g.time * (1.3 + i * 0.2) + i) * 0.04 + beat * beat * 0.03;
      L.mesh.scale.set(breathe, 1 + wind * (0.5 + i * 0.1), breathe);
      L.mesh.rotation.z = wind * (0.15 + i * 0.05);
    }
    this.rim.scale.setScalar(1 + Math.sin(g.time * 2.2) * 0.03 + beat * 0.04);
    if (this.rim.material?.emissiveIntensity != null) {
      this.rim.material.emissiveIntensity = 0.4 + beat * beat * 0.55;
    }

    // Soft collision: shove enemies caught in the skirt (r≈20).
    this._shoveAcc += dt;
    if (this._shoveAcc < 0.08) return;
    this._shoveAcc = 0;
    for (const e of g.enemies) {
      if (e.dead) continue;
      const dx = e.pos.x - P.pos.x, dz = e.pos.z - P.pos.z;
      const d = Math.hypot(dx, dz);
      if (d < 2.5 || d > 20) continue;
      const push = (1 - d / 20) * 0.55;
      _v.set(dx / (d || 1), 0, dz / (d || 1)).multiplyScalar(push);
      e.pos.x += _v.x;
      e.pos.z += _v.z;
      if (Math.random() < 0.04) {
        g.combat.damage(e, 0.12, { element: 'Radiant', tough: 0.3 });
        g.particles.emit(e.pos.x, e.pos.y + 0.6, e.pos.z, _c.set('#c8b6ef'), { speed: 2, life: 0.4, kind: 1, size: 0.5 });
      }
    }
  }
}
