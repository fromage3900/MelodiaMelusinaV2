// Melusina (player) and her Choral Sheep companion.

import * as THREE from 'three';
import { buildMelusina, buildSheep } from './entities.js';
import { RULES, MODIFIERS, RARITIES, BLESSINGS } from './design.js';
import { clamp, lerp, angleDiff } from './util.js';
import { WORLD_RADIUS } from './design.js';
import { RIFT_RADIUS } from './world.js';

const BLESSING_BY_ID = Object.fromEntries(BLESSINGS.map((b) => [b.blessing_id, b]));
const _c = new THREE.Color();

export class Player {
  constructor(game) {
    this.g = game;
    this.m = buildMelusina();
    game.scene.add(this.m.group, this.m.shadow);
    this.pos = new THREE.Vector3(0, 2.2, 8);
    this.vel = new THREE.Vector3();
    this.facing = Math.PI;
    this.shield = 0;
    this.sp = RULES.turn_economy.shared_sp_start;
    this.dead = false;
    this.buffs = new Map();
    this.comboStep = -1;
    this.dash = null;
    this.invulnUntil = 0;
    this.lastDodgeTime = -9;
    this.lastDodgeGrade = null;
    this.dodgeFrom = null;
    this.nextCrit = false;
    this.spin = 0;
    this.swingT = 0;
    this.hurtT = 0;
    this.stats = null;
    this.hp = 1;
  }

  // ---------------------------------------------------------------- stats
  recalc() {
    const pr = this.g.profile;
    const L = pr.level;
    const S = {
      attack: 22 + 6 * (L - 1), maxHp: 300 + 42 * (L - 1), armor: 4 + 2 * (L - 1),
      crit: 0.05, critDmg: 1.5, moveSpeed: 7.2, speed: 0, dmg: 0, elem: {}, perfectms: 0, encore: 0, harmony: 0,
      cdr: 0, gold: 0, break: 0, drain: 0, magic: 0, arias: new Set(), family: 'melee', basicElement: 'Forte',
      spMax: RULES.turn_economy.shared_sp_max, dmgTaken: 1, encoreStart: 50, comboKeeper: false,
    };
    for (const slot in pr.equipment) {
      const it = pr.equipment[slot];
      if (!it) continue;
      const up = 1 + 0.06 * (it.up || 0);
      if (it.attack) S.attack += Math.round(it.attack * up);
      if (it.hp) S.maxHp += Math.round(it.hp * up);
      if (it.armor) S.armor += Math.round(it.armor * up);
      if (slot === 'instrument') { S.family = it.family || 'melee'; S.basicElement = it.element || 'Forte'; }
      for (const a of it.affixes) {
        if (a.key === 'elem') S.elem[a.e] = (S.elem[a.e] || 0) + a.v / 100;
        else if (a.key === 'hp' || a.key === 'armor') S[a.key === 'hp' ? 'maxHp' : 'armor'] += a.v;
        else if (a.key === 'crit' || a.key === 'critdmg') S[a.key === 'crit' ? 'crit' : 'critDmg'] += a.v / 100;
        else if (a.key === 'perfectms') S.perfectms += a.v;
        else S[a.key] += a.v / 100;
      }
      if (it.aria) S.arias.add(it.aria);
    }
    S.dmg += 0.01 * (pr.shrines?.length || 0);
    for (const id of pr.blessings) {
      const b = BLESSING_BY_ID[id];
      if (!b) continue;
      if (b.effect_type === 'max_sp') S.spMax = b.effect_value;
      if (b.effect_type === 'perfect_window_bonus') S.perfectms += b.effect_value;
      if (b.effect_type === 'element_unlock') S.elem[b.effect_str] = (S.elem[b.effect_str] || 0) + 0.15;
      if (b.effect_type === 'starting_mana') S.encoreStart = b.effect_value;
      if (b.effect_type === 'combo_persistence') S.comboKeeper = true;
    }
    if (S.arias.has('StoneCarapace')) S.dmgTaken *= 0.8;
    if (S.arias.has('SwiftTempo')) S.speed += 0.2;
    S.cdr = Math.min(0.4, S.cdr);
    const ratio = this.stats ? this.hp / this.stats.maxHp : 1;
    this.stats = S;
    this.hp = clamp(ratio, 0.05, 1) * S.maxHp;
    this.sp = Math.min(this.sp, S.spMax);
    this.dress();
  }

  // Wardrobe: equipped gear recolours Melusina.
  dress() {
    const eq = this.g.profile.equipment;
    const gown = eq.gown;
    this.m.gownMat.color.set(gown ? RARITIES[gown.rarity].color : '#bda8df').lerp(_c.set('#bda8df'), 0.35);
    this.m.crown.visible = !!eq.head;
    if (eq.head) this.m.crown.material.color.set(RARITIES[eq.head.rarity].color);
    this.m.shoes.visible = !!eq.shoes;
    const inst = eq.instrument;
    this.m.lyre.visible = !inst || inst.family === 'ranged';
    this.m.baton.visible = !!inst && inst.family === 'melee';
    this.m.instMat.emissive.set(inst ? RARITIES[inst.rarity].color : '#ffcf6a');
  }

  hasBuff(id) { return (this.buffs.get(id) ?? -1) >= this.g.beatIndex; }
  addBuff(id, beats) { this.buffs.set(id, this.g.beatIndex + beats); }

  heal(amt, silent = false) {
    if (this.dead) return;
    const before = this.hp;
    this.hp = Math.min(this.stats.maxHp, this.hp + amt);
    if (!silent && this.hp - before > 1) this.g.overlay.text(this.pos.x, this.pos.y + 2.4, this.pos.z, '+' + Math.round(this.hp - before), '#9dffb8', 17);
  }

  cleanse() { this.buffs.delete('TempoBreak'); }

  faceTo(x, z) { this.facing = Math.atan2(x - this.pos.x, z - this.pos.z); }

  startDash(angle, dist, dur, invuln, arc = false) {
    this.dash = { fx: this.pos.x, fz: this.pos.z, tx: this.pos.x + Math.sin(angle) * dist, tz: this.pos.z + Math.cos(angle) * dist, t: 0, dur, arc, dist };
    if (invuln) this.invulnUntil = Math.max(this.invulnUntil, this.g.time + dur + 0.08);
    this.facing = angle;
  }

  swing(step) { this.swingT = 1; this.swingStep = step; }

  walkable(x, z) {
    const w = this.g.world;
    if (w.inRift) return Math.hypot(x, z) < RIFT_RADIUS;
    if (Math.hypot(x, z) > WORLD_RADIUS - 25) return false;
    return w.height(x, z) > -1.15;
  }

  // ---------------------------------------------------------------- update
  update(dt, ix, iz) {
    const g = this.g, S = this.stats, m = this.m;
    if (this.dead) { m.group.visible = false; m.shadow.visible = false; return; }
    m.group.visible = true; m.shadow.visible = true;
    const haste = this.hasBuff('HasteDance') ? MODIFIERS.HasteDance.value - 1 : 0;
    const slow = this.hasBuff('TempoBreak') ? MODIFIERS.TempoBreak.value - 1 : 0;
    const spd = S.moveSpeed * (1 + S.speed + g.rhythm.dyn.speed + haste + slow);
    let nx = this.pos.x, nz = this.pos.z;
    if (this.dash) {
      const d = this.dash;
      d.t += dt;
      const k = clamp(d.t / d.dur, 0, 1);
      const e = 1 - (1 - k) * (1 - k);
      nx = lerp(d.fx, d.tx, e); nz = lerp(d.fz, d.tz, e);
      if (k >= 1) this.dash = null;
      this.vel.set(0, 0, 0);
    } else {
      const acc = Math.min(1, dt * 14);
      this.vel.x += (ix * spd - this.vel.x) * acc;
      this.vel.z += (iz * spd - this.vel.z) * acc;
      nx += this.vel.x * dt; nz += this.vel.z * dt;
      if ((ix || iz) && g.time - (this.lastActionTime || -9) > 0.35) {
        const want = Math.atan2(ix, iz);
        this.facing += angleDiff(want, this.facing) * Math.min(1, dt * 12);
      }
    }
    if (this.walkable(nx, nz)) { this.pos.x = nx; this.pos.z = nz; }
    else if (this.walkable(nx, this.pos.z)) this.pos.x = nx;
    else if (this.walkable(this.pos.x, nz)) this.pos.z = nz;
    else if (this.dash) this.dash = null;
    const gy = g.world.height(this.pos.x, this.pos.z);
    this.pos.y = g.world.inRift ? 0 : Math.max(gy, -0.75);

    // ---- presentation
    const beatK = 1 - g.beatPhase;
    const moving = Math.hypot(this.vel.x, this.vel.z) > 0.5;
    const bob = moving ? Math.abs(Math.sin(g.beatPhase * Math.PI)) * 0.12 : beatK * beatK * 0.05;
    const arcY = this.dash && this.dash.arc ? Math.sin(clamp(this.dash.t / this.dash.dur, 0, 1) * Math.PI) * 2.2 : 0;
    m.group.position.set(this.pos.x, this.pos.y + bob + arcY, this.pos.z);
    m.shadow.position.set(this.pos.x, this.pos.y + 0.05, this.pos.z);
    m.group.rotation.y = this.facing + (this.spin ? g.time * 18 : 0);
    const lean = moving ? 0.12 : 0;
    m.body.rotation.x = lerp(m.body.rotation.x, lean, Math.min(1, dt * 8));
    const stretch = this.dash ? 1.15 : 1;
    m.body.scale.set(1 / Math.sqrt(stretch), stretch * (1 + beatK * beatK * 0.03), 1 / Math.sqrt(stretch));
    this.swingT = Math.max(0, this.swingT - dt * 4);
    m.inst.rotation.y = this.swingT * Math.PI * 2 * (this.swingStep % 2 ? -1 : 1);
    m.inst.position.y = 1.2 + Math.sin(g.time * 2.4) * 0.06;
    this.hurtT = Math.max(0, this.hurtT - dt * 3);
    m.gownMat.emissive.setRGB(this.hurtT * 0.9, this.hurtT * 0.1, this.hurtT * 0.2);
    if (this.invulnUntil > g.time && Math.random() < 0.6) g.particles.emit(this.pos.x, this.pos.y + 1, this.pos.z, _c.set('#ffffff'), { speed: 1, life: 0.35, size: 0.5, kind: 3 });
  }
}

export class Sheep {
  constructor(game) {
    this.g = game;
    this.m = buildSheep();
    game.scene.add(this.m.group, this.m.shadow);
    this.pos = new THREE.Vector3(2, 2.2, 10);
    this.facing = 0;
    this.hopT = 0;
    this.glow = 0;
  }

  get every() { return this.g.player.stats.arias.has('ChoralFleece') ? 1 : 2; }

  onBeat(beat) {
    const g = this.g, P = g.player;
    this.hopT = 1;
    if (P.dead || g.paused) return;
    if (beat.inBar === 0 && beat.bar % this.every === 0 && g.inCombat) this.harmonize();
  }

  // Harmonize: the proven UE companion verb — heal, Harmony, and a cymatic pulse.
  harmonize() {
    const g = this.g, P = g.player;
    P.heal(P.stats.maxHp * 0.05);
    P.sp = Math.min(P.stats.spMax, P.sp + 1);
    this.glow = 1;
    g.decals.spawn('ring', this.pos.x, this.pos.z, { r: 5, inner: 4.2, flash: true, dur: 0.6, color: '#62c8ff' });
    for (let k = 0; k < 24; k++) {
      const a = (k / 24) * Math.PI * 2;
      g.particles.emit(this.pos.x + Math.cos(a) * 1.2, this.pos.y + 0.8, this.pos.z + Math.sin(a) * 1.2, _c.set('#8fd8ff'), { dir: { x: Math.cos(a), y: 0.2, z: Math.sin(a) }, speed: 7, life: 0.6, kind: k % 2 ? 1 : 0, size: 0.7, gravity: 0 });
    }
    for (const e of g.combat.enemiesIn('circle', { x: this.pos.x, z: this.pos.z, r: 5 })) g.combat.damage(e, 0.45, { element: 'Tide', tough: 0.6 });
    g.overlay.text(this.pos.x, this.pos.y + 1.8, this.pos.z, 'Harmonize ♪', '#8fd8ff', 14, { life: 1 });
    g.audio.chime(4);
  }

  update(dt) {
    const g = this.g, P = g.player;
    const back = P.facing + Math.PI * 0.8;
    const tx = P.pos.x + Math.sin(back) * 2.4, tz = P.pos.z + Math.cos(back) * 2.4;
    const dx = tx - this.pos.x, dz = tz - this.pos.z, d = Math.hypot(dx, dz);
    if (d > 25) { this.pos.x = tx; this.pos.z = tz; }
    else if (d > 0.4) {
      const sp = Math.min(d * 4, 14);
      this.pos.x += (dx / d) * sp * dt; this.pos.z += (dz / d) * sp * dt;
      this.facing += angleDiff(Math.atan2(dx, dz), this.facing) * Math.min(1, dt * 8);
    }
    const gy = g.world.height(this.pos.x, this.pos.z);
    this.pos.y = g.world.inRift ? 0 : Math.max(gy, -0.4);
    this.hopT = Math.max(0, this.hopT - dt * 3.5);
    const hop = Math.sin(this.hopT * Math.PI) * 0.35;
    const mm = this.m;
    mm.group.position.set(this.pos.x, this.pos.y + hop, this.pos.z);
    mm.group.rotation.y = this.facing;
    mm.shadow.position.set(this.pos.x, this.pos.y + 0.05, this.pos.z);
    mm.group.visible = mm.shadow.visible = !P.dead;
    this.glow = Math.max(0, this.glow - dt * 1.5);
    mm.wool.emissive.setRGB(this.glow * 0.3, this.glow * 0.6, this.glow * 0.9);
  }
}
