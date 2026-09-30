// Melusina, the Choral Sheep companion and the Melody Slimes.
// Slimes hop on the beat and every attack is a telegraph that lands on a
// counted beat — the enemy "speaks" the same rhythm language as the player.

import * as THREE from 'three';
import { ELEMENT_STYLE, ENEMY_BY_ID, ELITE_AFFIXES, RULES } from './design.js';
import { clamp, lerp, angleDiff } from './util.js';

let _grad = null;
export function toonGradient() {
  if (_grad) return _grad;
  const data = new Uint8Array([90, 170, 255]);
  _grad = new THREE.DataTexture(data, 3, 1, THREE.RedFormat);
  _grad.minFilter = _grad.magFilter = THREE.NearestFilter;
  _grad.needsUpdate = true;
  return _grad;
}
export const toon = (color, o = {}) => new THREE.MeshToonMaterial({ color, gradientMap: toonGradient(), ...o });
const outlineMat = new THREE.MeshBasicMaterial({ color: '#2a1f3a', side: THREE.BackSide });

function withOutline(mesh, s = 1.07) {
  const o = new THREE.Mesh(mesh.geometry, outlineMat);
  o.scale.setScalar(s);
  mesh.add(o);
  return mesh;
}

const blobGeo = new THREE.CircleGeometry(1, 20).rotateX(-Math.PI / 2);
const blobMat = new THREE.MeshBasicMaterial({ color: '#1b1230', transparent: true, opacity: 0.28, depthWrite: false });
export function blob(r) {
  const m = new THREE.Mesh(blobGeo, blobMat);
  m.scale.setScalar(r);
  m.renderOrder = 1;
  return m;
}

// ------------------------------------------------------------------ Melusina
export function buildMelusina() {
  const g = new THREE.Group();
  const body = new THREE.Group();
  g.add(body);
  const gownMat = toon('#bda8df');
  const gown = withOutline(new THREE.Mesh(new THREE.ConeGeometry(0.62, 1.25, 14), gownMat));
  gown.position.y = 0.62;
  const bodice = new THREE.Mesh(new THREE.CylinderGeometry(0.19, 0.3, 0.5, 10), toon('#f6f0f8'));
  bodice.position.y = 1.38;
  const head = withOutline(new THREE.Mesh(new THREE.SphereGeometry(0.26, 16, 12), toon('#ffe3d6')));
  head.position.y = 1.86;
  const hairMat = toon('#82d2db');
  const hair = new THREE.Mesh(new THREE.SphereGeometry(0.3, 14, 10, 0, Math.PI * 2, 0, Math.PI * 0.62), hairMat);
  hair.position.set(0, 1.9, -0.03);
  const tail = new THREE.Mesh(new THREE.ConeGeometry(0.2, 1.0, 8), hairMat);
  tail.position.set(0, 1.5, -0.3);
  tail.rotation.x = 0.45;
  const eyeMat = new THREE.MeshBasicMaterial({ color: '#2a1f3a' });
  for (const s of [-1, 1]) {
    const e = new THREE.Mesh(new THREE.SphereGeometry(0.04, 6, 6), eyeMat);
    e.position.set(0.09 * s, 1.88, 0.23);
    body.add(e);
  }
  const crown = new THREE.Mesh(new THREE.TorusGeometry(0.2, 0.045, 6, 14), toon('#ffd978', { emissive: '#d9bc72', emissiveIntensity: 0.3 }));
  crown.position.y = 2.12; crown.rotation.x = Math.PI / 2; crown.visible = false;
  const shoes = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.1, 0.3), toon('#f3b6cf'));
  shoes.position.set(0, 0.05, 0.08);
  shoes.visible = false;
  body.add(gown, bodice, head, hair, tail, crown, shoes);
  // Floating instrument by her right hand.
  const inst = new THREE.Group();
  inst.position.set(0.62, 1.2, 0.15);
  const instMat = toon('#ffe7a8', { emissive: '#ffcf6a', emissiveIntensity: 0.35 });
  const lyre = new THREE.Mesh(new THREE.TorusGeometry(0.22, 0.04, 6, 14, Math.PI * 1.3), instMat);
  lyre.rotation.z = -Math.PI * 0.15;
  const baton = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.04, 0.8, 6), instMat);
  baton.rotation.x = Math.PI / 2.3;
  baton.visible = false;
  inst.add(lyre, baton);
  body.add(inst);
  g.scale.setScalar(1.25);
  const shadow = blob(0.85);
  return { group: g, body, gownMat, hairMat, crown, shoes, inst, instMat, lyre, baton, shadow };
}

// ------------------------------------------------------------------ Choral Sheep
export function buildSheep() {
  const g = new THREE.Group();
  const wool = toon('#f7f3ff');
  const fleece = new THREE.Group();
  const puffs = [[0, 0.62, 0, 0.5], [0.32, 0.6, 0.05, 0.36], [-0.32, 0.6, 0.05, 0.36], [0, 0.72, -0.32, 0.36], [0, 0.85, 0.08, 0.36], [0.2, 0.7, 0.3, 0.3], [-0.2, 0.7, 0.3, 0.3]];
  for (const [x, y, z, r] of puffs) {
    const p = withOutline(new THREE.Mesh(new THREE.IcosahedronGeometry(r, 1), wool), 1.08);
    p.position.set(x, y, z);
    fleece.add(p);
  }
  const face = toon('#3a2f45');
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.22, 10, 8), face);
  head.position.set(0, 0.78, 0.5);
  head.scale.set(1, 1.1, 1.25);
  for (const s of [-1, 1]) {
    const ear = new THREE.Mesh(new THREE.SphereGeometry(0.08, 6, 5), face);
    ear.position.set(0.2 * s, 0.86, 0.45); ear.scale.set(1.6, 0.6, 0.8);
    g.add(ear);
    for (const zz of [-0.22, 0.22]) {
      const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.4, 5), face);
      leg.position.set(0.2 * s, 0.2, zz);
      g.add(leg);
    }
  }
  g.add(fleece, head);
  g.scale.setScalar(0.9);
  return { group: g, fleece, wool, shadow: blob(0.55) };
}

// ------------------------------------------------------------------ Slimes
const slimeGeo = new THREE.SphereGeometry(1, 18, 12);
const eyeGeo = new THREE.SphereGeometry(0.13, 8, 6);
const eyeMat = new THREE.MeshBasicMaterial({ color: '#241a33' });
const shineMat = new THREE.MeshBasicMaterial({ color: '#ffffff' });
const shineGeo = new THREE.SphereGeometry(0.05, 6, 4);
const crownGeo = new THREE.CylinderGeometry(0.45, 0.55, 0.35, 6, 1, true);
const crownMat = toon('#ffd978', { emissive: '#d9a84a', emissiveIntensity: 0.4, side: THREE.DoubleSide });

function buildSlime(element, scale, elite, boss) {
  const g = new THREE.Group();
  const col = new THREE.Color(ELEMENT_STYLE[element]?.color || '#ffffff');
  const mat = toon(col, { emissive: col.clone().multiplyScalar(0.18), transparent: true, opacity: 0.93 });
  const body = new THREE.Mesh(slimeGeo, mat);
  body.position.y = 0.8;
  body.scale.set(1, 0.8, 1);
  const outline = new THREE.Mesh(slimeGeo, outlineMat);
  outline.scale.setScalar(1.06);
  body.add(outline);
  for (const s of [-1, 1]) {
    const e = new THREE.Mesh(eyeGeo, eyeMat);
    e.position.set(0.3 * s, 0.15, 0.86);
    e.scale.set(1, 1.3, 0.6);
    const sh = new THREE.Mesh(shineGeo, shineMat);
    sh.position.set(0.04, 0.05, 0.1);
    e.add(sh);
    body.add(e);
  }
  if (elite || boss) {
    const c = new THREE.Mesh(crownGeo, crownMat);
    c.position.y = 0.95;
    body.add(c);
  }
  g.add(body);
  g.scale.setScalar(scale);
  return { group: g, body, mat };
}

let _eid = 0;
export class Enemy {
  constructor(game, defId, level, opts = {}) {
    this.game = game;
    this.id = ++_eid;
    this.def = ENEMY_BY_ID[defId];
    this.level = level;
    this.elite = !!opts.elite;
    this.boss = !!opts.boss;
    this.bossName = opts.bossName || null;
    this.affixes = opts.affixes || [];
    this.camp = opts.camp || null;
    this.rift = !!opts.rift;
    const hpMul = opts.hpMul ?? 1;
    const lv = 1 + 0.3 * (level - 1);
    this.maxHp = Math.round(this.def.hp * 0.42 * lv * (this.elite ? 3.2 : 1) * (this.boss ? 18 : 1) * hpMul * (this.affixes.includes('fortissimo') ? 1.6 : 1));
    this.hp = this.maxHp;
    this.dmg = this.def.damage * 0.6 * (1 + 0.22 * (level - 1)) * (this.elite ? 1.6 : 1) * (this.boss ? 2.2 : 1) * (opts.dmgMul ?? 1);
    this.maxTough = this.elite || this.boss ? this.def.toughness * (this.boss ? 3 : 1) : 0;
    this.tough = this.maxTough;
    this.scale = this.boss ? 3.4 : this.elite ? 1.6 : 0.85 + Math.min(0.4, this.def.hp / 1500);
    this.radius = 0.95 * this.scale;
    this.pos = new THREE.Vector3(opts.x, 0, opts.z);
    this.pos.y = game.world.height(this.pos.x, this.pos.z);
    this.home = this.pos.clone();
    this.facing = Math.random() * Math.PI * 2;
    this.aggro = !!opts.aggro;
    this.hop = null;
    this.strikes = [];
    this.nextAttackBeat = 0;
    this.stunUntil = -1;
    this.weakUntil = -1;
    this.vulnUntil = -1;
    this.vuln = 0;
    this.silenceUntil = -1;
    this.slowUntil = 0;
    this.dead = false;
    this.flash = 0;
    this.squash = 0;
    this.phrase = 0;
    this.enraged = false;
    const bpm = this.def.bpm;
    this.attackEvery = this.affixes.includes('presto') ? 3 : bpm >= 140 ? 4 : bpm >= 128 ? 5 : 6;
    const el = this.def.element;
    this.attackKind = el === 'Gale' ? 'lunge' : el === 'Arcane' || el === 'Radiant' || el === 'Umbral' ? 'bolt' : el === 'Tide' && this.id % 2 ? 'bolt' : 'slam';
    this.range = this.attackKind === 'bolt' ? 11 : this.attackKind === 'lunge' ? 6.5 : 2.2 * this.scale + 0.6;
    const m = buildSlime(el, this.scale, this.elite, this.boss);
    this.mesh = m.group; this.bodyMesh = m.body; this.mat = m.mat;
    this.shadow = blob(this.radius * 0.95);
    this.mesh.position.copy(this.pos);
    game.scene.add(this.mesh, this.shadow);
    this.name = this.boss ? this.bossName || this.def.name : this.elite ? `${this.affixes.map((a) => ELITE_AFFIXES.find((x) => x.id === a)?.name).join(' ')} ${this.def.name}`.trim() : null;
  }

  get element() { return this.def.element; }
  get broken() { return this.stunUntil >= this.game.beatIndex; }

  remove() {
    this.game.scene.remove(this.mesh, this.shadow);
    this.mat.dispose();
    for (const s of this.strikes) this.game.decals.release(s.decal);
    this.strikes.length = 0;
  }

  windupBeats(extra = 0) {
    const spb = this.game.audio.spb;
    const minTime = this.boss ? 1.05 : this.elite ? 0.9 : 0.8;
    return Math.max(this.boss ? 2 : 1, Math.ceil(minTime / spb)) + extra;
  }

  // Queue a telegraphed strike that lands on beat `land`.
  strike(shape, params, land, extra = {}) {
    const spb = this.game.audio.spb;
    const beatsAway = land - this.game.beatIndex;
    const color = this.boss ? '#ff4d6d' : this.elite ? '#ff7a45' : '#ff5a6e';
    const decal = this.game.decals.spawn(shape, params.x, params.z, { ...params, dur: Math.max(0.2, beatsAway * spb), color });
    this.strikes.push({ shape, params, land, decal, ...extra });
  }

  onBeat(beat) {
    if (this.dead) return;
    const g = this.game, P = g.player;
    // Resolve strikes that land now.
    for (let i = this.strikes.length - 1; i >= 0; i--) {
      const s = this.strikes[i];
      if (s.land <= beat.index) {
        this.strikes.splice(i, 1);
        g.combat.resolveEnemyStrike(this, s);
      } else if ((this.boss || this.elite) && s.land - beat.index <= 3) {
        g.overlay.text(s.params.x, g.world.height(s.params.x, s.params.z) + 1, s.params.z, String(s.land - beat.index), '#ffb3c1', 22, { life: 0.5, rise: 0.4 });
        if (this.boss) g.audio.tick(s.land - beat.index === 1);
      }
    }
    if (this.broken) return;
    if (this.stunUntil === beat.index - 1 && this.maxTough) {
      this.tough = this.maxTough;
      this.weakUntil = beat.index + beat.meter * 4;
    }
    const dx = P.pos.x - this.pos.x, dz = P.pos.z - this.pos.z;
    const dist = Math.hypot(dx, dz);
    if (!this.aggro && !P.dead && dist < (this.elite || this.boss ? 17 : 13) && !g.safeZone) { this.aggro = true; this.nextAttackBeat = Math.max(this.nextAttackBeat, beat.index + 2); }
    if (this.aggro && (P.dead || g.safeZone || Math.hypot(P.pos.x - this.home.x, P.pos.z - this.home.z) > (this.rift ? 999 : 42))) {
      this.aggro = false;
      this.hp = Math.min(this.maxHp, this.hp + this.maxHp * 0.25);
    }
    if (this.boss && this.aggro) return this.bossBeat(beat, dist);
    // Attack tokens: only a few slimes wind up at once, so every telegraph stays readable.
    if (this.aggro && this.strikes.length === 0 && dist <= this.range && beat.index >= this.nextAttackBeat && this.silenceUntil < beat.index && g.attackTokens(this)) {
      this.startAttack(beat, dx / (dist || 1), dz / (dist || 1));
      return;
    }
    if (this.strikes.length) return;
    // Movement: one hop per beat towards the player, or a lazy wander.
    if (this.aggro) {
      if (dist > this.range * 0.8) {
        const step = Math.min(dist - this.range * 0.6, (0.9 + this.def.speed / 55) * (this.slowUntil > g.time ? 0.5 : 1));
        this.startHop(this.pos.x + (dx / dist) * step, this.pos.z + (dz / dist) * step, beat.spb);
      }
    } else if (beat.index % 4 === this.id % 4 && Math.random() < 0.5) {
      const a = Math.random() * Math.PI * 2, r = Math.random() * 4;
      this.startHop(this.home.x + Math.cos(a) * r, this.home.z + Math.sin(a) * r, beat.spb);
    }
  }

  startHop(x, z, spb) {
    const h = this.game.world.height(x, z);
    if (!this.game.world.inRift && h < -1.1) return;
    this.hop = { fx: this.pos.x, fz: this.pos.z, tx: x, tz: z, t: 0, dur: spb * 0.62 };
    this.facing = Math.atan2(x - this.pos.x, z - this.pos.z);
  }

  startAttack(beat, nx, nz) {
    const g = this.game;
    const w = this.windupBeats();
    const land = beat.index + w;
    this.facing = Math.atan2(nx, nz);
    this.nextAttackBeat = land + this.attackEvery;
    const x = this.pos.x, z = this.pos.z;
    if (this.attackKind === 'slam') this.strike('circle', { x, z, r: 2.2 * this.scale + 0.4 }, land, { kind: 'slam' });
    else if (this.attackKind === 'lunge') this.strike('rect', { x, z, len: 7, width: 1.5 * this.scale + 0.6, angle: this.facing }, land, { kind: 'lunge', nx, nz });
    else this.strike('rect', { x, z, len: 14, width: 0.9, angle: this.facing, alpha: 0.6 }, land, { kind: 'bolt', nx, nz });
    if (this.affixes.includes('canon')) {
      const s = this.strikes[this.strikes.length - 1];
      this.strike(s.shape, { ...s.params }, land + 1, { kind: s.kind, nx: s.nx, nz: s.nz, echo: true });
    }
    this.squash = 0.4;
  }

  // Bosses play phrases: one pattern per bar, windups counted aloud.
  bossBeat(beat, dist) {
    const g = this.game, P = g.player;
    this.enraged = this.hp < this.maxHp * 0.35;
    if (dist > 6 && this.strikes.length === 0 && beat.inBar !== 0) {
      const step = Math.min(dist - 5, 2.4);
      const dx = P.pos.x - this.pos.x, dz = P.pos.z - this.pos.z;
      this.startHop(this.pos.x + (dx / dist) * step, this.pos.z + (dz / dist) * step, beat.spb);
    }
    if (beat.inBar !== 0 || this.strikes.length > 2) return;
    const w = this.windupBeats(this.enraged ? 0 : 1);
    const x = this.pos.x, z = this.pos.z;
    const pattern = this.phrase++ % 5;
    if (pattern === 0) {
      this.strike('circle', { x, z, r: 8 }, beat.index + w, { kind: 'slam', mult: 1.2 });
    } else if (pattern === 1) {
      this.strike('ring', { x, z, r: 15, inner: 5 }, beat.index + w + 1, { kind: 'slam', mult: 1 });
    } else if (pattern === 2) {
      // Arpeggio: a falling note follows the player on each beat of the bar.
      for (let k = 0; k < beat.meter; k++) {
        const px = P.pos.x + P.vel.x * k * beat.spb * 0.6, pz = P.pos.z + P.vel.z * k * beat.spb * 0.6;
        this.strike('circle', { x: px, z: pz, r: 3.2 }, beat.index + w + k, { kind: 'slam', mult: 0.8 });
      }
    } else if (pattern === 3) {
      const base = Math.atan2(P.pos.x - x, P.pos.z - z);
      for (let k = 0; k < 4; k++) this.strike('rect', { x, z, len: 20, width: 3.4, angle: base + (k * Math.PI) / 2 }, beat.index + w, { kind: 'slam', mult: 0.9 });
      for (let k = 0; k < 4; k++) this.strike('rect', { x, z, len: 20, width: 3.4, angle: base + Math.PI / 4 + (k * Math.PI) / 2 }, beat.index + w + 2, { kind: 'slam', mult: 0.9 });
    } else {
      g.spawnAdds(this, this.enraged ? 4 : 3);
      this.strike('circle', { x, z, r: 6 }, beat.index + w, { kind: 'slam', mult: 0.8 });
    }
    this.squash = 0.5;
  }

  update(dt) {
    if (this.dead) return;
    const g = this.game;
    let yOff = 0;
    if (this.hop) {
      const hp = this.hop;
      hp.t += dt;
      const k = clamp(hp.t / hp.dur, 0, 1);
      this.pos.x = lerp(hp.fx, hp.tx, k);
      this.pos.z = lerp(hp.fz, hp.tz, k);
      yOff = Math.sin(k * Math.PI) * (0.55 + this.scale * 0.2);
      if (k >= 1) { this.hop = null; this.squash = 0.35; }
    }
    if (this.dash) {
      const d = this.dash;
      d.t += dt;
      const k = clamp(d.t / d.dur, 0, 1);
      this.pos.x = lerp(d.fx, d.tx, k); this.pos.z = lerp(d.fz, d.tz, k);
      if (k >= 1) this.dash = null;
    }
    const gy = g.world.height(this.pos.x, this.pos.z);
    this.pos.y = g.world.inRift ? 0 : Math.max(gy, -0.4);
    this.mesh.position.set(this.pos.x, this.pos.y + yOff, this.pos.z);
    this.shadow.position.set(this.pos.x, this.pos.y + 0.06, this.pos.z);
    this.shadow.scale.setScalar(this.radius * (1 - yOff * 0.15));
    const cur = this.mesh.rotation.y;
    this.mesh.rotation.y = cur + angleDiff(this.facing, cur) * Math.min(1, dt * 10);
    // Jelly: squash on landing + a breath on every beat.
    this.squash = Math.max(0, this.squash - dt * 2.5);
    const beatK = 1 - g.beatPhase;
    const s = 1 + Math.sin(this.squash * 12) * this.squash * 0.35 + beatK * beatK * 0.06;
    this.bodyMesh.scale.set(s, 0.8 / s, s);
    if (this.flash > 0) {
      this.flash -= dt;
      this.mat.emissiveIntensity = 1 + this.flash * 12;
    } else this.mat.emissiveIntensity = this.broken ? 2.5 + Math.sin(g.time * 20) : 1;
  }
}

// Enemy definitions for world bosses come from the biome table.
export function bossFor(biome) {
  return biome.boss;
}

export const TOUGH_REDUCTION = RULES.toughness.reduction;
