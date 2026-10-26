// Player attacks, skills, projectiles, zones and enemy strike resolution.
// Damage = attack × skill power × rules grade multiplier (with combo) ×
// element wheel × affixes; toughness breaks follow the rules' toughness block.

import * as THREE from 'three';
import { ELEMENT_STYLE, MODIFIERS, RULES, elementMultiplier } from './design.js';
import { clamp, angleDiff } from './util.js';

const projGeo = new THREE.IcosahedronGeometry(0.28, 0);
const tornadoGeo = new THREE.ConeGeometry(1.1, 2.8, 10, 1, true).translate(0, 1.4, 0).rotateX(Math.PI);
const matCache = new Map();
function projMat(color) {
  if (!matCache.has(color)) matCache.set(color, new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.95 }));
  return matCache.get(color);
}
const _col = new THREE.Color();

export class Combat {
  constructor(game) {
    this.g = game;
    this.projectiles = [];
    this.zones = [];
    this.orbs = [];
    this.summons = [];
    this.queue = [];
    this.whirl = null;
  }

  reset() {
    for (const p of this.projectiles) this.g.scene.remove(p.mesh);
    for (const o of this.orbs) this.g.scene.remove(o.mesh);
    for (const s of this.summons) this.g.scene.remove(s.mesh);
    for (const z of this.zones) this.g.decals.release(z.decal);
    this.projectiles = []; this.zones = []; this.orbs = []; this.summons = []; this.queue = []; this.whirl = null;
  }

  // ------------------------------------------------------------ geometry tests
  static inShape(px, pz, pr, shape, p) {
    const dx = px - p.x, dz = pz - p.z;
    const d = Math.hypot(dx, dz);
    if (shape === 'circle') return d <= p.r + pr;
    if (shape === 'ring') return d <= p.r + pr && d >= p.inner - pr;
    const ca = Math.cos(p.angle), sa = Math.sin(p.angle);
    if (shape === 'rect') {
      const lx = dx * ca - dz * sa, ly = dx * sa + dz * ca;
      return ly >= -pr && ly <= p.len + pr && Math.abs(lx) <= p.width / 2 + pr;
    }
    if (shape === 'cone') return d <= p.r + pr && Math.abs(angleDiff(Math.atan2(dx, dz), p.angle)) <= p.halfAngle + pr / Math.max(1, d);
    return false;
  }

  enemiesIn(shape, p) {
    const out = [];
    for (const e of this.g.enemies) if (!e.dead && Combat.inShape(e.pos.x, e.pos.z, e.radius, shape, p)) out.push(e);
    return out;
  }

  autoTarget(range = 10) {
    const P = this.g.player;
    let best = null, bd = range;
    for (const e of this.g.enemies) {
      if (e.dead) continue;
      const d = Math.hypot(e.pos.x - P.pos.x, e.pos.z - P.pos.z) - e.radius;
      // Prefer what is in front of Melusina a little.
      const facingPenalty = Math.abs(angleDiff(Math.atan2(e.pos.x - P.pos.x, e.pos.z - P.pos.z), P.facing)) * 0.8;
      if (d + facingPenalty < bd) { bd = d + facingPenalty; best = e; }
    }
    return best;
  }

  area(v) {
    const g = this.g;
    return g.player.stats.arias.has('CrescendoWave') && g.rhythm.dynIndex >= 3 ? v * 1.35 : v;
  }

  flash(shape, x, z, params, color) {
    this.g.decals.spawn(shape, x, z, { ...params, flash: true, dur: 0.35, color });
  }

  // ------------------------------------------------------------ damage
  damage(e, coef, o = {}) {
    if (!e || e.dead) return 0;
    const g = this.g, P = g.player, S = P.stats;
    let dmg = S.attack * coef * (o.mult ?? 1);
    const em = elementMultiplier(o.element, e.element);
    dmg *= em;
    dmg *= 1 + S.dmg + (S.elem[o.element] || 0);
    if (P.hasBuff('Crescendo_Minor')) dmg *= MODIFIERS.Crescendo_Minor.value;
    if (o.skill && S.arias.has('BurningChord')) dmg *= 1.5;
    if (e.vulnUntil >= g.beatIndex) dmg *= 1 + e.vuln;
    if (e.broken) dmg *= 1.3;
    const crit = Math.random() < S.crit + g.rhythm.dyn.crit + (P.nextCrit ? 1 : 0);
    if (crit) { dmg *= S.critDmg; P.nextCrit = false; }
    dmg = Math.max(1, Math.round(dmg * (0.92 + Math.random() * 0.16)));
    e.hp -= dmg;
    e.flash = 0.12;
    e.aggro = true;
    // Toughness (only elites and bosses carry it).
    if (e.maxTough && !e.broken) {
      let td = (o.tough ?? 1) * 6 * (o.mult ?? 1) * (1 + S.break);
      if (em > 1) td *= 1.5;
      if (o.downbeat && S.arias.has('DownbeatBreak')) td *= 3;
      e.tough -= td;
      if (e.tough <= 0) this.breakEnemy(e);
    }
    if (S.drain > 0) P.heal(dmg * S.drain, true);
    if (S.arias.has('DissonantSilence')) { e.vulnUntil = g.beatIndex + g.audio.meter; e.vuln = Math.max(e.vuln, 0.15); }
    if (o.knock && !e.boss) {
      const dx = e.pos.x - (o.fromX ?? P.pos.x), dz = e.pos.z - (o.fromZ ?? P.pos.z), d = Math.hypot(dx, dz) || 1;
      e.hop = null;
      e.dash = { fx: e.pos.x, fz: e.pos.z, tx: e.pos.x + (dx / d) * o.knock, tz: e.pos.z + (dz / d) * o.knock, t: 0, dur: 0.18 };
    }
    const col = crit ? '#ffd978' : em > 1 ? '#ffffff' : ELEMENT_STYLE[o.element]?.color || '#ffffff';
    g.overlay.text(e.pos.x, e.pos.y + 1.4 * e.scale + 0.4, e.pos.z, crit ? dmg + '!' : String(dmg), col, crit ? 26 : em > 1 ? 21 : 17);
    if (em > 1 && Math.random() < 0.3) g.overlay.text(e.pos.x, e.pos.y + 1.9 * e.scale + 0.8, e.pos.z, 'WEAK', '#ffffff', 12, { life: 0.6 });
    _col.set(ELEMENT_STYLE[o.element]?.color || '#ffffff');
    g.particles.burst(e.pos.x, e.pos.y + 0.8 * e.scale, e.pos.z, _col, crit ? 9 : 5, { speed: 6, life: 0.45, size: 0.5 });
    g.audio.hit(crit);
    if (o.perfect && S.arias.has('EchoingBeat') && !o.echo) {
      this.queue.push({ beat: g.beatIndex + 1, fn: () => this.damage(e, coef * 0.5, { ...o, echo: true, perfect: false }) });
    }
    if (e.hp <= 0) g.killEnemy(e);
    return dmg;
  }

  breakEnemy(e) {
    const g = this.g;
    e.tough = 0;
    e.stunUntil = g.beatIndex + g.audio.meter * 2;
    for (const s of e.strikes) g.decals.release(s.decal);
    e.strikes.length = 0;
    e.hop = null;
    g.overlay.text(e.pos.x, e.pos.y + 2.2 * e.scale, e.pos.z, 'BREAK!', '#ff5470', 30, { life: 1.2 });
    g.particles.burst(e.pos.x, e.pos.y + e.scale, e.pos.z, _col.set('#ffffff'), 24, { speed: 10, life: 0.7, kind: 3, size: 0.9 });
    g.world.pulse(e.pos.x, e.pos.z, 1.6, true);
    g.shake(0.5);
    g.audio.kill(true);
  }

  hitAll(list, coef, o) {
    let n = 0;
    for (const e of list) { this.damage(e, coef, o); n++; }
    return n;
  }

  // ------------------------------------------------------------ basic attack
  basic(gr) {
    const g = this.g, P = g.player, S = P.stats;
    const t = this.autoTarget(S.family === 'ranged' ? 16 : 9);
    if (t) P.faceTo(t.pos.x, t.pos.z);
    P.comboStep = (P.comboStep + 1) % 3;
    const step = P.comboStep;
    const o = { mult: gr.mult, element: S.basicElement, perfect: gr.grade === 'Perfect', downbeat: gr.downbeat, tough: step === 2 ? 2 : 1 };
    const color = ELEMENT_STYLE[S.basicElement].color;
    let hits = 0;
    P.swing(step);
    if (S.family === 'melee') {
      if (t) {
        const d = Math.hypot(t.pos.x - P.pos.x, t.pos.z - P.pos.z) - t.radius;
        if (d > 2.6) P.startDash(P.facing, Math.min(d - 2, 3), 0.12, false);
      }
      const fx = P.pos.x + Math.sin(P.facing) * (P.dash ? P.dash.dist : 0), fz = P.pos.z + Math.cos(P.facing) * (P.dash ? P.dash.dist : 0);
      if (step < 2) {
        const p = { x: fx, z: fz, r: this.area(3.6), halfAngle: 0.7, angle: P.facing };
        hits = this.hitAll(this.enemiesIn('cone', p), 1.0, o);
        this.flash('cone', fx, fz, p, color);
      } else {
        const p = { x: fx, z: fz, r: this.area(3.8) };
        hits = this.hitAll(this.enemiesIn('circle', p), 1.7, o);
        this.flash('circle', fx, fz, p, color);
        g.world.pulse(fx, fz, 0.8);
      }
    } else {
      const shots = step === 2 ? 3 : 1;
      for (let k = 0; k < shots; k++) {
        const a = P.facing + (k - (shots - 1) / 2) * 0.22;
        this.shoot({ angle: a, speed: 28, coef: step === 2 ? 0.75 : 1.0, o, color, homing: t, life: 0.7, radius: 0.6 });
      }
      hits = t ? 1 : 0;
    }
    if (S.arias.has('PetalCadence') && step === 2) {
      for (let k = 0; k < 8; k++) this.shoot({ angle: P.facing + (k / 8) * Math.PI * 2, speed: 16, coef: 0.45, o: { ...o, tough: 0.5 }, color: '#f7b8d2', life: 0.6, radius: 0.7, pierce: true });
    }
    return hits;
  }

  // ------------------------------------------------------------ skills
  cast(skill, gr) {
    const g = this.g, P = g.player;
    const t = this.autoTarget(skill.kind === 'projectile' || skill.kind === 'meteor' || skill.kind === 'bolts' ? 18 : 11);
    if (t && skill.kind !== 'heal' && skill.kind !== 'shield') P.faceTo(t.pos.x, t.pos.z);
    const o = { mult: gr.mult, element: skill.element, skill: true, perfect: gr.grade === 'Perfect', downbeat: gr.downbeat, tough: skill.tough ?? 1 };
    const c = skill.power;
    const color = ELEMENT_STYLE[skill.element].color;
    const fwdX = Math.sin(P.facing), fwdZ = Math.cos(P.facing);
    const aimX = t ? t.pos.x : P.pos.x + fwdX * 6, aimZ = t ? t.pos.z : P.pos.z + fwdZ * 6;
    g.audio.skill(skill);
    P.swing(3);
    P.castPose();
    let hits = 0;
    switch (skill.kind) {
      case 'strike': {
        const dist = t ? clamp(Math.hypot(t.pos.x - P.pos.x, t.pos.z - P.pos.z) + 1.5, 3, skill.range) : skill.range;
        const p = { x: P.pos.x, z: P.pos.z, len: dist, width: this.area(skill.width), angle: P.facing };
        hits = this.hitAll(this.enemiesIn('rect', p), c * skill.coef, o);
        this.flash('rect', p.x, p.z, p, color);
        P.startDash(P.facing, dist, 0.16, true);
        break;
      }
      case 'slam': {
        const d = Math.min(8, Math.hypot(aimX - P.pos.x, aimZ - P.pos.z));
        P.startDash(P.facing, d, 0.22, true, true);
        const x = P.pos.x + fwdX * d, z = P.pos.z + fwdZ * d;
        const p = { x, z, r: this.area(skill.radius) };
        setTimeout(() => {
          hits = this.hitAll(this.enemiesIn('circle', p), c * skill.coef, o);
          this.flash('circle', x, z, p, color);
          g.world.pulse(x, z, 1.4);
          g.shake(0.35);
          g.particles.burst(x, g.world.height(x, z) + 0.3, z, _col.set(color), 18, { speed: 9, life: 0.6 });
        }, 220);
        hits = 1;
        break;
      }
      case 'cone': {
        const p = { x: P.pos.x, z: P.pos.z, r: this.area(skill.range), halfAngle: (skill.angle * Math.PI) / 360, angle: P.facing };
        hits = this.hitAll(this.enemiesIn('cone', p), c * skill.coef, { ...o, knock: skill.knock });
        this.flash('cone', p.x, p.z, p, color);
        break;
      }
      case 'wave': {
        const p = { x: P.pos.x, z: P.pos.z, len: this.area(skill.range), width: this.area(skill.width), angle: P.facing };
        hits = this.hitAll(this.enemiesIn('rect', p), c * skill.coef, { ...o, knock: skill.knock });
        this.flash('rect', p.x, p.z, p, color);
        for (let k = 0; k < 14; k++) g.particles.emit(P.pos.x + fwdX * k * 0.8, P.pos.y + 0.4, P.pos.z + fwdZ * k * 0.8, _col.set(color), { speed: 3, life: 0.5, spread: skill.width, kind: 1, size: 0.8 });
        break;
      }
      case 'ringwave': {
        const r = this.area(skill.radius);
        const p = { x: P.pos.x, z: P.pos.z, r, inner: 0 };
        hits = this.hitAll(this.enemiesIn('circle', p), c * skill.coef, o);
        this.flash('ring', p.x, p.z, { r, inner: r - 1.4 }, color);
        g.world.pulse(p.x, p.z, 1.8, true);
        break;
      }
      case 'nova': {
        const p = { x: P.pos.x, z: P.pos.z, r: this.area(skill.radius) };
        hits = this.hitAll(this.enemiesIn('circle', p), c * skill.coef, o);
        this.flash('circle', p.x, p.z, p, color);
        g.particles.burst(P.pos.x, P.pos.y + 1, P.pos.z, _col.set(color), 22, { speed: 9, life: 0.6, kind: 3, size: 0.7 });
        break;
      }
      case 'echo':
      case 'pulses': {
        const n = skill.kind === 'echo' ? 1 + skill.echoes : skill.count;
        for (let k = 0; k < n; k++) {
          const fn = () => {
            const r = this.area(skill.radius * (skill.kind === 'pulses' ? 1 + k * 0.25 : 1));
            const p = { x: P.pos.x, z: P.pos.z, r };
            this.hitAll(this.enemiesIn('circle', p), c * skill.coef * (skill.kind === 'echo' && k > 0 ? 0.6 : 1), o);
            this.flash('circle', p.x, p.z, p, color);
            g.world.pulse(p.x, p.z, 1);
            g.audio.tick(k === n - 1);
          };
          if (k === 0) fn(); else this.queue.push({ beat: g.beatIndex + k, fn });
        }
        hits = 1;
        break;
      }
      case 'whirl':
        this.whirl = { until: g.time + skill.beats * g.audio.spb, next: 0, r: this.area(skill.radius), coef: c * skill.coef, o, color };
        hits = 1;
        break;
      case 'tornado':
        this.shoot({ angle: P.facing, speed: 9, coef: c * skill.coef, o, color, life: 2.4, radius: 2.2, pierce: true, tick: 0.25, mesh: 'tornado' });
        hits = 1;
        break;
      case 'bolts': {
        const targets = g.enemies.filter((e) => !e.dead && Math.hypot(e.pos.x - P.pos.x, e.pos.z - P.pos.z) < 20);
        for (let k = 0; k < skill.count; k++) {
          const tgt = targets.length ? targets[k % targets.length] : null;
          this.shoot({ angle: P.facing + (k - skill.count / 2) * 0.4, speed: 17, coef: c * skill.coef, o, color, homing: tgt, life: 1.6, radius: 0.8, turn: 7 });
        }
        hits = targets.length ? 1 : 0;
        break;
      }
      case 'projectile':
        this.shoot({ angle: P.facing, speed: skill.speed, coef: c * skill.coef, o, color, homing: t, life: 1.1, radius: 0.7, explode: this.area(skill.radius) });
        hits = t ? 1 : 0;
        break;
      case 'beam': {
        const p = { x: P.pos.x, z: P.pos.z, len: skill.range, width: this.area(skill.width), angle: P.facing };
        hits = this.hitAll(this.enemiesIn('rect', p), c * skill.coef, o);
        this.flash('rect', p.x, p.z, p, color);
        for (let k = 0; k < 18; k++) g.particles.emit(P.pos.x + fwdX * k * 0.75, P.pos.y + 1, P.pos.z + fwdZ * k * 0.75, _col.set(color), { speed: 1.5, life: 0.4, kind: 3, size: 0.6 });
        break;
      }
      case 'meteor': {
        const delay = skill.delay ?? 1;
        const pool = g.enemies.filter((e) => !e.dead && Math.hypot(e.pos.x - aimX, e.pos.z - aimZ) < 10);
        for (let k = 0; k < skill.count; k++) {
          const tgt = pool.length ? pool[k % pool.length] : null;
          const x = tgt ? tgt.pos.x : aimX + (Math.random() - 0.5) * 6 * (skill.count > 1 ? 1 : 0);
          const z = tgt ? tgt.pos.z : aimZ + (Math.random() - 0.5) * 6 * (skill.count > 1 ? 1 : 0);
          const r = this.area(skill.radius);
          const land = g.beatIndex + delay + (skill.count > 3 ? Math.floor(k / 2) : k);
          const decal = g.decals.spawn('circle', x, z, { r, dur: (land - g.beatIndex) * g.audio.spb, color });
          this.queue.push({
            beat: land, fn: () => {
              g.decals.release(decal);
              this.hitAll(this.enemiesIn('circle', { x, z, r }), c * skill.coef, o);
              this.flash('circle', x, z, { r }, color);
              g.world.pulse(x, z, 1.2);
              g.shake(0.25);
              g.particles.burst(x, g.world.height(x, z) + 0.5, z, _col.set(color), 16, { speed: 8, life: 0.7, kind: 1, size: 1 });
            },
          });
        }
        hits = 1;
        break;
      }
      case 'dash': {
        const p = { x: P.pos.x, z: P.pos.z, len: skill.dist, width: 2.4, angle: P.facing };
        hits = this.hitAll(this.enemiesIn('rect', p), c * skill.coef, o);
        P.startDash(P.facing, skill.dist, 0.2, true);
        if (skill.buff) P.addBuff(skill.buff, g.audio.meter * 2 * MODIFIERS[skill.buff].duration_turns);
        this.flash('rect', p.x, p.z, p, color);
        break;
      }
      case 'heal': {
        const amt = P.stats.maxHp * skill.heal * gr.mult;
        P.heal(amt);
        P.cleanse();
        g.particles.burst(P.pos.x, P.pos.y + 1, P.pos.z, _col.set('#9dffb8'), 26, { speed: 5, life: 1, kind: 1, size: 0.9, gravity: -2 });
        this.flash('circle', P.pos.x, P.pos.z, { r: 3 }, '#9dffb8');
        hits = 1;
        break;
      }
      case 'shield': {
        P.shield = Math.max(P.shield, P.stats.maxHp * skill.shield * gr.mult);
        P.addBuff('GuardHymn', g.audio.meter * skill.bars);
        g.particles.burst(P.pos.x, P.pos.y + 1, P.pos.z, _col.set(color), 20, { speed: 4, life: 0.8, kind: 3 });
        hits = 1;
        break;
      }
      case 'pool': {
        const r = this.area(skill.radius);
        const decal = g.decals.spawn('circle', aimX, aimZ, { r, dur: 0.01, color, alpha: 0.7 });
        decal.manual = true;
        decal.mesh.material.uniforms.uProgress.value = 1;
        this.zones.push({ x: aimX, z: aimZ, r, until: g.beatIndex + skill.bars * g.audio.meter, coef: c * skill.coef, o: { ...o, tough: 0.3 }, decal, slow: true });
        hits = 1;
        break;
      }
      case 'orbit': {
        for (let k = 0; k < skill.count; k++) {
          const mesh = new THREE.Mesh(projGeo, projMat(color));
          mesh.scale.setScalar(1.6);
          g.scene.add(mesh);
          this.orbs.push({ mesh, phase: (k / skill.count) * Math.PI * 2, until: g.time + skill.bars * g.audio.meter * g.audio.spb, coef: c * skill.coef, o, hitAt: new Map() });
        }
        hits = 1;
        break;
      }
      case 'summon': {
        const mesh = new THREE.Group();
        const base = new THREE.Mesh(new THREE.ConeGeometry(0.6, 1.6, 4), projMat('#e38bff'));
        base.position.y = 0.8;
        const arm = new THREE.Mesh(new THREE.BoxGeometry(0.08, 1.4, 0.08), projMat('#ffd978'));
        arm.position.y = 1.4;
        mesh.add(base, arm);
        mesh.position.set(P.pos.x + fwdX * 2, P.pos.y, P.pos.z + fwdZ * 2);
        g.scene.add(mesh);
        this.summons.push({ mesh, arm, until: g.beatIndex + skill.bars * g.audio.meter, coef: c * skill.coef, o, color });
        hits = 1;
        break;
      }
      case 'debuff': {
        const p = { x: P.pos.x, z: P.pos.z, r: this.area(skill.radius) };
        const list = this.enemiesIn('circle', p);
        for (const e of list) {
          e.vulnUntil = g.beatIndex + skill.bars * g.audio.meter;
          e.vuln = Math.max(e.vuln, skill.vuln);
          e.silenceUntil = g.beatIndex + g.audio.meter;
          for (const s of e.strikes) g.decals.release(s.decal);
          e.strikes.length = 0;
          g.overlay.text(e.pos.x, e.pos.y + 2 * e.scale, e.pos.z, 'SILENCED', '#9a7bf0', 13, { life: 0.8 });
        }
        hits = this.hitAll(list, c * skill.coef, o);
        this.flash('circle', p.x, p.z, p, color);
        break;
      }
    }
    return hits;
  }

  // ------------------------------------------------------------ projectiles
  shoot(opt) {
    const g = this.g, P = g.player;
    const mesh = opt.mesh === 'tornado' ? new THREE.Mesh(tornadoGeo, new THREE.MeshBasicMaterial({ color: opt.color, transparent: true, opacity: 0.45, side: THREE.DoubleSide, depthWrite: false })) : new THREE.Mesh(projGeo, projMat(opt.color));
    const x = P.pos.x + Math.sin(opt.angle) * 0.8, z = P.pos.z + Math.cos(opt.angle) * 0.8;
    mesh.position.set(x, P.pos.y + 1.1, z);
    g.scene.add(mesh);
    this.projectiles.push({
      mesh, owner: 'player', x, z, vx: Math.sin(opt.angle) * opt.speed, vz: Math.cos(opt.angle) * opt.speed, speed: opt.speed,
      life: opt.life, radius: opt.radius, coef: opt.coef, o: opt.o, color: opt.color, homing: opt.homing || null, turn: opt.turn ?? 4,
      pierce: !!opt.pierce, explode: opt.explode || 0, tick: opt.tick || 0, tickT: 0, hit: new Set(), tornado: opt.mesh === 'tornado',
    });
  }

  enemyShoot(e, nx, nz) {
    const g = this.g;
    const mesh = new THREE.Mesh(projGeo, projMat(ELEMENT_STYLE[e.element].color));
    mesh.scale.setScalar(1.5);
    const x = e.pos.x + nx * e.radius, z = e.pos.z + nz * e.radius;
    mesh.position.set(x, e.pos.y + 0.9, z);
    g.scene.add(mesh);
    this.projectiles.push({ mesh, owner: 'enemy', x, z, vx: nx * 17, vz: nz * 17, life: 1.0, radius: 0.55, dmg: e.dmg, src: e, color: ELEMENT_STYLE[e.element].color });
  }

  resolveEnemyStrike(e, s) {
    const g = this.g, P = g.player;
    const p = s.params;
    if (s.kind === 'bolt') { this.enemyShoot(e, s.nx, s.nz); return; }
    if (s.kind === 'lunge') {
      const tx = e.pos.x + s.nx * 6.5, tz = e.pos.z + s.nz * 6.5;
      e.hop = null;
      e.dash = { fx: e.pos.x, fz: e.pos.z, tx, tz, t: 0, dur: 0.16 };
    }
    g.particles.burst(p.x, g.world.height(p.x, p.z) + 0.3, p.z, _col.set('#ff8aa0'), s.shape === 'circle' ? 10 : 6, { speed: 6, life: 0.4 });
    if (e.boss || e.elite) g.shake(e.boss ? 0.35 : 0.15);
    const inside = Combat.inShape(P.pos.x, P.pos.z, 0.35, s.shape, p);
    const dodgedFrom = P.dodgeFrom && g.time - P.lastDodgeTime < 0.5 && Combat.inShape(P.dodgeFrom.x, P.dodgeFrom.z, 0.35, s.shape, p);
    if ((inside || dodgedFrom) && P.lastDodgeGrade && P.lastDodgeGrade !== 'Miss' && g.time - P.lastDodgeTime < 0.5) {
      g.perfectDodge(e);
      return;
    }
    if (inside) g.hurtPlayer(e.dmg * (s.mult || 1) * (e.weakUntil >= g.beatIndex ? RULES.toughness.broken_enemy_damage_mult : 1), e);
  }

  // ------------------------------------------------------------ per-beat / per-frame
  onBeat(beat) {
    const g = this.g;
    for (let i = this.queue.length - 1; i >= 0; i--) {
      if (this.queue[i].beat <= beat.index) { const q = this.queue[i]; this.queue.splice(i, 1); q.fn(); }
    }
    for (let i = this.zones.length - 1; i >= 0; i--) {
      const z = this.zones[i];
      if (beat.index > z.until) { g.decals.release(z.decal); this.zones.splice(i, 1); continue; }
      for (const e of this.enemiesIn('circle', z)) { this.damage(e, z.coef, z.o); if (z.slow) e.slowUntil = g.time + 1; }
      g.particles.burst(z.x, g.world.height(z.x, z.z) + 0.3, z.z, _col.set(z.o.element ? ELEMENT_STYLE[z.o.element].color : '#62c8ff'), 6, { speed: 2, life: 0.8, spread: z.r, kind: 1, gravity: -1 });
    }
    for (let i = this.summons.length - 1; i >= 0; i--) {
      const s = this.summons[i];
      if (beat.index > s.until) { g.scene.remove(s.mesh); this.summons.splice(i, 1); continue; }
      s.arm.rotation.z = beat.index % 2 ? 0.5 : -0.5;
      let best = null, bd = 15;
      for (const e of g.enemies) { if (e.dead) continue; const d = Math.hypot(e.pos.x - s.mesh.position.x, e.pos.z - s.mesh.position.z); if (d < bd) { bd = d; best = e; } }
      if (best) {
        const a = Math.atan2(best.pos.x - s.mesh.position.x, best.pos.z - s.mesh.position.z);
        const mesh = new THREE.Mesh(projGeo, projMat(s.color));
        const x = s.mesh.position.x, z = s.mesh.position.z;
        mesh.position.set(x, s.mesh.position.y + 1.6, z);
        g.scene.add(mesh);
        this.projectiles.push({ mesh, owner: 'player', x, z, vx: Math.sin(a) * 24, vz: Math.cos(a) * 24, speed: 24, life: 0.8, radius: 0.6, coef: s.coef, o: s.o, color: s.color, homing: best, turn: 8, pierce: false, explode: 0, tick: 0, hit: new Set() });
      }
    }
  }

  update(dt) {
    const g = this.g, P = g.player;
    if (this.whirl) {
      const w = this.whirl;
      P.spin = 1;
      if (g.time >= w.until) { this.whirl = null; P.spin = 0; }
      else if (g.time >= w.next) {
        w.next = g.time + g.audio.spb / 2;
        const p = { x: P.pos.x, z: P.pos.z, r: w.r };
        this.hitAll(this.enemiesIn('circle', p), w.coef, w.o);
        this.flash('ring', p.x, p.z, { r: w.r, inner: w.r - 1 }, w.color);
      }
    }
    for (let i = this.orbs.length - 1; i >= 0; i--) {
      const o = this.orbs[i];
      if (g.time > o.until) { g.scene.remove(o.mesh); this.orbs.splice(i, 1); continue; }
      o.phase += dt * (Math.PI * 2) / (g.audio.spb * g.audio.meter) * 1.5;
      const x = P.pos.x + Math.cos(o.phase) * 2.8, z = P.pos.z + Math.sin(o.phase) * 2.8;
      o.mesh.position.set(x, P.pos.y + 1.1, z);
      for (const e of g.enemies) {
        if (e.dead) continue;
        if (Math.hypot(e.pos.x - x, e.pos.z - z) < e.radius + 0.7 && (o.hitAt.get(e.id) || 0) < g.time) {
          o.hitAt.set(e.id, g.time + 0.4);
          this.damage(e, o.coef, o.o);
        }
      }
    }
    for (let i = this.projectiles.length - 1; i >= 0; i--) {
      const p = this.projectiles[i];
      p.life -= dt;
      if (p.homing && !p.homing.dead) {
        const want = Math.atan2(p.homing.pos.x - p.x, p.homing.pos.z - p.z);
        const cur = Math.atan2(p.vx, p.vz);
        const na = cur + clamp(angleDiff(want, cur), -p.turn * dt, p.turn * dt);
        p.vx = Math.sin(na) * p.speed; p.vz = Math.cos(na) * p.speed;
      }
      p.x += p.vx * dt; p.z += p.vz * dt;
      const gy = g.world.height(p.x, p.z);
      p.mesh.position.set(p.x, Math.max(gy, g.world.inRift ? 0 : -0.2) + (p.tornado ? 0 : 1.1), p.z);
      if (p.tornado) p.mesh.rotation.y += dt * 14;
      else p.mesh.rotation.y += dt * 6;
      if (Math.random() < 0.5) g.particles.emit(p.x, p.mesh.position.y, p.z, _col.set(p.color), { speed: 0.6, life: 0.3, size: 0.45 });
      let dead = p.life <= 0;
      if (p.owner === 'player') {
        if (p.tick) {
          p.tickT -= dt;
          if (p.tickT <= 0) {
            p.tickT = p.tick;
            for (const e of this.enemiesIn('circle', { x: p.x, z: p.z, r: p.radius })) this.damage(e, p.coef, p.o);
          }
        } else {
          for (const e of g.enemies) {
            if (e.dead || p.hit.has(e.id)) continue;
            if (Math.hypot(e.pos.x - p.x, e.pos.z - p.z) < e.radius + p.radius) {
              p.hit.add(e.id);
              if (p.explode) {
                const q = { x: p.x, z: p.z, r: p.explode };
                this.hitAll(this.enemiesIn('circle', q), p.coef, p.o);
                this.flash('circle', p.x, p.z, q, p.color);
              } else this.damage(e, p.coef, p.o);
              if (!p.pierce) { dead = true; break; }
            }
          }
        }
      } else if (!P.dead && Math.hypot(P.pos.x - p.x, P.pos.z - p.z) < 0.45 + p.radius) {
        dead = true;
        if (P.lastDodgeGrade && P.lastDodgeGrade !== 'Miss' && g.time - P.lastDodgeTime < 0.5) g.perfectDodge(p.src);
        else g.hurtPlayer(p.dmg * (p.src && p.src.weakUntil >= g.beatIndex ? RULES.toughness.broken_enemy_damage_mult : 1), p.src);
      }
      if (dead) { g.scene.remove(p.mesh); if (p.tornado) p.mesh.material.dispose(); this.projectiles.splice(i, 1); }
    }
  }
}
