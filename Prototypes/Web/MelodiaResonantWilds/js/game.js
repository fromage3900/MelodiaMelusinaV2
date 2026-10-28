// Core loop. The audio beat clock drives enemies, the companion, delayed
// skills and the world pulse; the player's taps are judged against it.

import * as THREE from 'three';
import { painterlyEnabled, PainterlyFilter } from './painterly.js';
import { AudioEngine } from './audio.js';
import { World, WATER } from './world.js';
import { Particles, Decals, Overlay, makeBeam } from './fx.js';
import { Player, Sheep } from './player.js';
import { Enemy } from './entities.js';
import { Combat } from './combat.js';
import { Loot } from './loot.js';
import { Rhythm } from './rhythm.js';
import { Progress, saveProfile, loadProfile, wipeProfile } from './progress.js';
import { Activities } from './activities.js';
import { UI } from './ui.js';
import { BIOMES, HUB, DIFFICULTY, RARITIES, SKILL_BY_ID, SHARD_BY_ELEMENT, ELEMENT_STYLE, MODIFIERS, RULES, xpToNext } from './design.js';
import { clamp, lerp } from './util.js';

const _c = new THREE.Color();
const isTouch = matchMedia('(pointer: coarse)').matches;

export class Game {
  constructor() {
    this.profile = loadProfile();
    this.canvas = document.getElementById('game');
    this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas, antialias: !isTouch, powerPreference: 'high-performance' });
    // Opt-in painterly postprocess. Quality adaptation still controls render resolution.
    this.painterly = painterlyEnabled ? new PainterlyFilter() : null;
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color('#f3e6dc');
    this.scene.fog = new THREE.Fog('#f3e6dc', 75, 175);
    this.camera = new THREE.PerspectiveCamera(42, 1, 0.5, 400);
    this.hemi = new THREE.HemisphereLight('#ffffff', '#8f7fa3', 1.5);
    this.sun = new THREE.DirectionalLight('#fff1e6', 1.7);
    this.sun.position.set(40, 80, 30);
    this.scene.add(this.hemi, this.sun);
    this.pal = { fog: new THREE.Color(), water: new THREE.Color(), light: new THREE.Color() };

    this.time = 0;
    this.beatIndex = 0;
    this.beatPhase = 0;
    this.paused = false;
    this.started = false;
    this.enemies = [];
    this.drops = [];
    this.hazards = [];
    this.cooldowns = [0, 0, 0, 0];
    this.cdTotal = [1, 1, 1, 1];
    this.dodgeReadyAt = 0;
    this.dodgeCd = 1.1;
    this.lastAttackAt = -9;
    this.autoAttackBeat = -1;
    this.shakeAmt = 0;
    this.inCombat = false;
    this.safeZone = true;
    this.zoneId = null;
    this.calibrating = null;
    this._save = 0;
    this._explore = 0;
    this._fps = { t: 0, n: 0, scale: 1 };

    this.audio = new AudioEngine();
    this.audio.volumes = { music: this.profile.settings.music, sfx: this.profile.settings.sfx };
    this.world = new World(this);
    this.particles = new Particles(this.scene);
    this.decals = new Decals(this.scene, this.world);
    this.overlay = new Overlay(document.getElementById('overlay'), this.camera);
    this.loot = new Loot(this);
    this.player = new Player(this);
    this.player.recalc();
    this.biomes = BIOMES;
    this.progress = new Progress(this);
    this.rhythm = new Rhythm(this);
    this.combat = new Combat(this);
    this.sheep = new Sheep(this);
    this.activities = new Activities(this);
    this.ui = new UI(this);

    this.firstRunGear();
    const sp = this.profile.spawn;
    if (sp && Math.hypot(sp.x, sp.z) < 660) this.player.pos.set(sp.x, 0, sp.z);
    this.player.pos.y = this.world.height(this.player.pos.x, this.player.pos.z);
    this.sheep.pos.copy(this.player.pos).add(new THREE.Vector3(2, 0, 2));
    this.camTarget = this.player.pos.clone();
    this.applyQuality();
    this.resize();
    window.addEventListener('resize', () => this.resize());
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) { this.save(); this.audio.suspend(); } else if (this.started) this.audio.resume();
    });
    window.addEventListener('pagehide', () => this.save());
  }

  // ------------------------------------------------------------ boot
  async warm(progress) {
    progress('Raising the five biomes…');
    await new Promise((r) => setTimeout(r, 20));
    this.world.warm(this.player.pos.x, this.player.pos.z);
    progress('Drawing the map…');
    await new Promise((r) => setTimeout(r, 20));
    this.overview = this.world.overview(180);
    this.renderer.compile(this.scene, this.camera);
    progress('Ready.');
  }

  start() {
    this.started = true;
    this.audio.start(this.scoreForPosition());
    this.audio.setVolumes(this.profile.settings.music, this.profile.settings.sfx);
    this.ui.show();
    this.idleReward();
    this.zoneId = null;
    this.clock = performance.now();
    this.ui.banner('Resonant Wilds', `${this.zoneName()} · every action lands on the beat`);
    requestAnimationFrame(() => this.frame());
  }

  firstRunGear() {
    const pr = this.profile;
    if (Object.keys(pr.equipment).length) return;
    const inst = this.loot.make(1, { slot: 'instrument', rarity: 1, element: 'Forte' });
    inst.base = 'Baton'; inst.family = 'melee'; inst.name = 'Tuned Baton of Forte'; inst.isNew = false;
    const gown = this.loot.make(1, { slot: 'gown', rarity: 0 });
    gown.name = 'Shorewake Dress'; gown.isNew = false;
    pr.equipment.instrument = inst;
    pr.equipment.gown = gown;
    this.player.recalc();
    this.player.hp = this.player.stats.maxHp;
  }

  idleReward() {
    const pr = this.profile;
    if (!pr.lastSeen) return;
    const mins = (Date.now() - pr.lastSeen) / 60000;
    if (mins < 5) return;
    const hours = Math.min(8, mins / 60);
    const gold = Math.round(20 + hours * pr.level * 60);
    const shards = Math.round(2 + hours * 6);
    pr.gold += gold; pr.shards += shards;
    setTimeout(() => this.ui.toast(`While you were away, your Choral Sheep gathered ${gold} gold and ${shards} shards ♪`, 'aqua'), 1500);
  }

  // ------------------------------------------------------------ helpers
  get difficultyDef() { return DIFFICULTY[this.profile.settings.difficulty] || DIFFICULTY.standard; }
  windowScale() { return this.difficultyDef.windowScale * this.activities.burdenScale('window'); }
  encoreGainScale() { return this.activities.burdenScale('encore'); }
  poiNear(x, z, r) { return this.activities ? this.activities.near(x, z, r) : []; }

  currentBiome() {
    const d = this.world.dominantBiome(this.player.pos.x, this.player.pos.z);
    return d.biome;
  }

  zoneName() {
    if (this.activities.rift) return `Resonance Rift · Tier ${this.activities.rift.tier}`;
    const d = this.world.dominantBiome(this.player.pos.x, this.player.pos.z);
    if (d.r < HUB.radius + 15) return HUB.name;
    return `${d.biome.name.split('—')[0].trim()} · Lv ${this.world.zoneLevel(this.player.pos.x, this.player.pos.z)}`;
  }

  scoreForPosition() {
    const d = this.world.dominantBiome(this.player.pos.x, this.player.pos.z);
    if (d.r < HUB.radius + 20) return { ...HUB, motif: [0, 4, 7, 9, 7, 4] };
    const b = d.biome;
    return { id: b.id, bpm: b.bpm, meter: b.meter, key: b.key, mode: b.mode, prog: b.prog, style: b.style, motif: b.motif };
  }

  musicIntensity() {
    if (this.rhythm.encoreActive) return 2;
    if (this.inCombat || this.activities.rift) return 1;
    return this.rhythm.dynIndex >= 3 ? 1 : 0;
  }

  skillCost(sk) {
    return sk.sp + (this.player.stats.arias.has('BurningChord') ? 1 : 0);
  }

  setPaused(p) {
    this.paused = p;
    if (p) {
      for (const e of this.enemies) { for (const s of e.strikes) this.decals.release(s.decal); e.strikes.length = 0; }
      this.ui.attackHeld = false;
    }
  }

  shake(a) { if (this.profile.settings.shake) this.shakeAmt = Math.max(this.shakeAmt, a); }

  aimAt(cx, cy) {
    const v = new THREE.Vector3((cx / innerWidth) * 2 - 1, -(cy / innerHeight) * 2 + 1, 0.5).unproject(this.camera);
    const dir = v.sub(this.camera.position).normalize();
    const t = (this.player.pos.y + 1 - this.camera.position.y) / dir.y;
    if (t > 0) {
      const x = this.camera.position.x + dir.x * t, z = this.camera.position.z + dir.z * t;
      this.player.faceTo(x, z);
      this.player.lastActionTime = this.time;
    }
  }

  // ------------------------------------------------------------ actions
  attack(perfMs) {
    if (!this.started || this.paused || this.player.dead) return;
    if (this.activities.shrine) { this.activities.shrineTap(perfMs); return; }
    if (this.calibrating) { this.calibrateTap(perfMs); return; }
    const spb = this.audio.spb;
    if (this.time - this.lastAttackAt < spb * 0.42) return;
    this.lastAttackAt = this.time;
    this.player.lastActionTime = this.time;
    const gr = this.rhythm.judge(perfMs);
    const hits = this.combat.basic(gr);
    if (gr.grade === 'Perfect') {
      this.player.sp = Math.min(this.player.stats.spMax, this.player.sp + 1);
      this.player.addBuff('Crescendo_Minor', this.audio.meter * MODIFIERS.Crescendo_Minor.duration_turns);
    } else if (gr.grade === 'Great' && Math.random() < this.player.stats.harmony) {
      this.player.sp = Math.min(this.player.stats.spMax, this.player.sp + 1);
    }
    this.autoAttackBeat = gr.beat ? gr.beat.index : this.beatIndex;
    this.rhythm.register(gr, hits);
  }

  // Holding attack auto-fires on each beat at a flat ×1.0 — tapping on the
  // beat yourself is what earns Perfect, combo, Crescendo and Harmony.
  autoAttack(beat) {
    if (this.time - this.lastAttackAt < this.audio.spb * 0.6) return;
    this.lastAttackAt = this.time;
    const hits = this.combat.basic({ grade: 'Good', mult: 1, downbeat: beat.inBar === 0, beat, err: 0 });
    if (hits && !this.rhythm.encoreActive) this.rhythm.encore = Math.min(this.rhythm.encoreMax, this.rhythm.encore + RULES.ultimate.gain_per_hit * 0.4);
  }

  skill(i, perfMs) {
    if (!this.started || this.paused || this.player.dead || this.activities.shrine || this.calibrating) return;
    const sk = SKILL_BY_ID[this.profile.loadout[i]];
    if (!sk) return;
    const P = this.player;
    if (this.cooldowns[i] > this.time) { this.ui.toast(`${sk.name} returns in ${(this.cooldowns[i] - this.time).toFixed(1)}s`, 'soft'); return; }
    const cost = this.skillCost(sk);
    if (P.sp < cost) { this.ui.toast('Not enough Harmony ◆ — land Perfect hits', 'soft'); this.audio.fail(); return; }
    P.sp -= cost;
    P.lastActionTime = this.time;
    const gr = this.rhythm.judge(perfMs);
    const total = sk.cd * this.audio.spb * (1 - P.stats.cdr);
    this.cdTotal[i] = total;
    this.cooldowns[i] = this.time + total;
    const hits = this.combat.cast(sk, gr);
    this.rhythm.register(gr, hits);
  }

  dodge(perfMs) {
    if (!this.started || this.paused || this.player.dead || this.activities.shrine || this.calibrating) return;
    if (this.time < this.dodgeReadyAt) return;
    const P = this.player;
    const gr = this.rhythm.judge(perfMs);
    const mv = this.ui.move();
    const ang = mv.x || mv.z ? Math.atan2(mv.x, mv.z) : P.facing;
    P.dodgeFrom = { x: P.pos.x, z: P.pos.z };
    P.startDash(ang, 5.5, 0.22, gr.grade !== 'Miss');
    P.lastDodgeTime = this.time;
    P.lastDodgeGrade = gr.grade;
    this.dodgeReadyAt = this.time + (gr.grade === 'Perfect' && P.stats.arias.has('SwiftTempo') ? 0.25 : this.dodgeCd);
    this.audio.dodge();
    this.ui.gradeFlash(gr.grade, gr.err);
    for (let k = 0; k < 8; k++) this.particles.emit(P.pos.x, P.pos.y + 0.8, P.pos.z, _c.set('#ffffff'), { speed: 2, life: 0.4, size: 0.7 });
  }

  perfectDodge(src) {
    const P = this.player, R = this.rhythm;
    const g = P.lastDodgeGrade;
    P.lastDodgeGrade = null;
    const great = g === 'Perfect' || g === 'Great';
    this.overlay.text(P.pos.x, P.pos.y + 3, P.pos.z, great ? 'PERFECT DODGE' : 'DODGE', great ? '#ffd978' : '#c9b6ef', great ? 22 : 16, { life: 0.9 });
    P.invulnUntil = Math.max(P.invulnUntil, this.time + 0.3);
    if (!great) return;
    P.nextCrit = true;
    R.encore = Math.min(R.encoreMax, R.encore + RULES.ultimate.gain_perfect);
    R.crescendo = Math.min(RULES.crescendo.max, R.crescendo + RULES.crescendo.gain.perfect);
    if (src && !src.dead) src.slowUntil = this.time + this.audio.spb * 2;
    if (P.stats.arias.has('TempoShift')) for (let i = 0; i < 4; i++) this.cooldowns[i] -= 4 * this.audio.spb;
    this.world.pulse(P.pos.x, P.pos.z, 1.5, true);
    this.audio.grade('Perfect');
  }

  encore() {
    if (!this.started || this.paused || this.player.dead) return;
    const R = this.rhythm, P = this.player;
    if (R.encore < R.encoreMax || R.encoreActive) return;
    R.encore = 0;
    R.encoreUntil = this.beatIndex + this.audio.meter * 2;
    P.invulnUntil = this.time + 0.6;
    const p = { x: P.pos.x, z: P.pos.z, r: 9 };
    this.combat.hitAll(this.combat.enemiesIn('circle', p), RULES.ultimate.damage_mult * 1.2, { mult: RULES.rhythm.max_combat_multiplier, element: P.stats.basicElement, tough: 3 });
    this.combat.flash('circle', p.x, p.z, p, '#ffd978');
    this.world.pulse(P.pos.x, P.pos.z, 2.5, true);
    this.particles.burst(P.pos.x, P.pos.y + 1, P.pos.z, _c.set('#ffd978'), 60, { speed: 14, life: 1, kind: 2, size: 1.2 });
    this.shake(0.7);
    this.audio.encore();
    this.audio.setIntensity(2);
    this.ui.banner('ENCORE!', 'Every action is Perfect for two bars');
  }

  skyboundStrike() {
    const t = this.combat.autoTarget(14);
    if (!t) return;
    const p = { x: t.pos.x, z: t.pos.z, r: 3 };
    this.combat.hitAll(this.combat.enemiesIn('circle', p), 3.0, { element: 'Radiant', tough: 2 });
    this.combat.flash('circle', p.x, p.z, p, '#ffe07a');
    this.particles.burst(t.pos.x, t.pos.y + 6, t.pos.z, _c.set('#ffe07a'), 26, { dir: { x: 0, y: -1, z: 0 }, speed: 14, life: 0.5, kind: 1, size: 1.2, spread: 2 });
    this.overlay.text(t.pos.x, t.pos.y + 3.5, t.pos.z, 'Skybound Refrain!', '#ffe07a', 16);
  }

  // ------------------------------------------------------------ interact
  nearestInteract() {
    if (this.paused) return null;
    const P = this.player;
    const r = this.activities.rift;
    if (r) return r.exit && Math.hypot(P.pos.x, P.pos.z - 6) < 3.5 ? { label: 'Leave the Rift ◎', fn: () => this.activities.exitRift() } : null;
    let best = null, bd = 4;
    for (const p of this.activities.pois) {
      if (!['forge', 'board', 'font', 'rift', 'boss', 'shrine', 'pylon'].includes(p.type)) continue;
      const d = Math.hypot(p.x - P.pos.x, p.z - P.pos.z);
      if (d < bd) { bd = d; best = p; }
    }
    if (!best) return null;
    const p = best;
    switch (p.type) {
      case 'forge': return { label: 'Forge ⚒', fn: () => this.ui.open('forge') };
      case 'board': return { label: 'Bounties 📜', fn: () => this.ui.open('bounties') };
      case 'font': return { label: 'Blessing Font ✧', fn: () => this.ui.open('blessings') };
      case 'rift': return { label: 'Enter Rift ◎', fn: () => { this.ui.riftPortal = p; this.ui.open('rift'); } };
      case 'boss': return p.alive && !p.alive.dead ? null : { label: `Summon ${p.name} ♛`, fn: () => this.activities.summonBoss(p) };
      case 'shrine': return this.activities.shrine ? null : { label: 'Play the shrine 𝄞', fn: () => this.activities.startShrine(p) };
      case 'pylon': return this.profile.pylons.includes(p.id) ? { label: 'Fast travel ◆', fn: () => this.ui.open('map') } : null;
    }
    return null;
  }

  interact() {
    const it = this.nearestInteract();
    if (it) { this.audio.ui(); it.fn(); }
  }

  travelTo(p) {
    this.clearWorldEnemies();
    this.player.pos.set(p.x + 3, 0, p.z + 3);
    this.player.pos.y = this.world.height(this.player.pos.x, this.player.pos.z);
    this.sheep.pos.copy(this.player.pos);
    this.camTarget.copy(this.player.pos);
    this.world.warm(this.player.pos.x, this.player.pos.z);
    this.audio.setScore(this.scoreForPosition());
    this.world.pulse(this.player.pos.x, this.player.pos.z, 2, true);
    this.ui.banner(p.name, this.zoneName());
    this.save();
  }

  // ------------------------------------------------------------ enemies
  spawnEnemy(defId, level, opts) {
    const e = new Enemy(this, defId, level, opts);
    this.enemies.push(e);
    return e;
  }

  removeEnemy(e) {
    if (!e.removed) { e.remove(); e.removed = true; }
    e.dead = true;
    const i = this.enemies.indexOf(e);
    if (i >= 0) this.enemies.splice(i, 1);
  }

  attackTokens(e) {
    if (e.elite || e.boss) return true;
    let n = 0;
    for (const o of this.enemies) if (!o.dead && !o.elite && !o.boss && o.strikes.length) n++;
    return n < (this.activities.rift ? 4 : 3);
  }

  spawnAdds(boss, n) {
    const b = this.currentBiome();
    const pool = this.activities.rift ? null : b.trash;
    for (let k = 0; k < n; k++) {
      const a = (k / n) * Math.PI * 2;
      const def = pool ? pool[Math.floor(Math.random() * pool.length)].id : boss.def.id;
      this.spawnEnemy(def, boss.level, { x: boss.pos.x + Math.cos(a) * 6, z: boss.pos.z + Math.sin(a) * 6, aggro: true, rift: boss.rift, hpMul: 0.6 });
    }
  }

  clearWorldEnemies() {
    for (const p of this.activities.pois) {
      if (p.type === 'camp' && p.active) this.activities.despawnCamp(p);
      if (p.type === 'boss' && p.alive) p.alive = null;
    }
    if (this.activities.event) this.activities.event = null;
    for (const e of this.enemies.slice()) this.removeEnemy(e);
    this.enemies = [];
    for (const h of this.hazards) this.decals.release(h.decal);
    this.hazards = [];
  }

  killEnemy(e) {
    if (e.dead) return;
    e.dead = true;
    e.dying = 0.35;
    for (const s of e.strikes) this.decals.release(s.decal);
    e.strikes.length = 0;
    const pr = this.profile, lvl = e.level;
    pr.stats.kills++;
    const xp = (8 + 4 * lvl) * (e.elite ? 5 : 1) * (e.boss ? 40 : 1) * (e.rift ? 1.3 : 1);
    this.progress.addXp(xp);
    const x = e.pos.x, z = e.pos.z;
    const goldAmt = (3 + lvl * 2) * (e.elite ? 4 : 1) * (e.boss ? 20 : 1);
    if (Math.random() < (e.elite || e.boss ? 1 : 0.7)) this.dropGold(x, z, goldAmt, e.boss ? 12 : e.elite ? 5 : 1);
    if (e.boss) {
      const n = 3 + Math.floor(Math.random() * 2);
      for (let i = 0; i < n; i++) this.dropItem(x, z, this.loot.make(lvl + 1, { min: 2, bonus: 0.6 }));
      if (pr.stats.bosses === 0 || Math.random() < 0.25) this.dropItem(x, z, this.loot.make(lvl + 1, { rarity: Math.random() < 0.5 ? 4 : 3 }));
      this.dropShards(x, z, 8, e.element);
      pr.notes += 15;
      pr.stats.bosses++;
      if (e.poi && !pr.maestros.includes(BIOMES[e.poi.biome].id)) pr.maestros.push(BIOMES[e.poi.biome].id);
      this.activities.bossDefeated(e);
      this.ui.banner(`${e.name} defeated!`, '+15 Golden Notes · the Maestro returns in 3 minutes');
      this.shake(0.8);
    } else if (e.elite) {
      const n = 1 + (Math.random() < 0.5 ? 1 : 0);
      for (let i = 0; i < n; i++) this.dropItem(x, z, this.loot.make(lvl, { min: 1, bonus: 0.3 }));
      this.dropShards(x, z, 2 + Math.floor(Math.random() * 2), e.element);
      this.dropOrb(x, z);
      pr.notes += 1;
      if (e.affixes.includes('dissonant')) this.addHazard(x, z, 3.2, e.dmg * 0.8);
    } else {
      if (Math.random() < 0.16) this.dropItem(x, z, this.loot.make(lvl));
      if (Math.random() < 0.12) this.dropShards(x, z, 1, e.element);
      if (Math.random() < 0.14) this.dropOrb(x, z);
    }
    this.bountyEvent('kill', 1, { element: e.element, elite: e.elite || e.boss });
    if (this.activities.rift) this.activities.riftKill(e);
    this.particles.burst(x, e.pos.y + e.scale, z, _c.set(ELEMENT_STYLE[e.element].color), e.boss ? 60 : 14, { speed: e.boss ? 14 : 7, life: 0.9, kind: 1 + (Math.random() < 0.5 ? 1 : 0), size: e.boss ? 1.4 : 0.9, gravity: -1 });
    this.audio.kill(e.boss);
    if (!this.rhythm.encoreActive) this.rhythm.encore = Math.min(this.rhythm.encoreMax, this.rhythm.encore + 2);
  }

  addHazard(x, z, r, dmg) {
    const land = this.beatIndex + 2;
    const decal = this.decals.spawn('circle', x, z, { r, dur: 2 * this.audio.spb, color: '#9a7bf0' });
    this.hazards.push({ x, z, r, dmg, land, decal });
  }

  hurtPlayer(dmg, src) {
    const P = this.player;
    if (P.dead || P.invulnUntil > this.time || this.paused) return;
    const S = P.stats;
    let d = dmg * S.dmgTaken * this.activities.burdenScale('damage');
    if (P.hasBuff('GuardHymn')) d *= MODIFIERS.GuardHymn.value;
    d *= 1 - S.armor / (S.armor + 50 + 10 * (src ? src.level : P.stats.armor / 2));
    d = Math.max(1, Math.round(d * (0.9 + Math.random() * 0.2)));
    if (P.shield > 0) {
      const a = Math.min(P.shield, d);
      P.shield -= a; d -= a;
    }
    P.hp -= d;
    P.hurtT = 1;
    this.overlay.text(P.pos.x, P.pos.y + 2.2, P.pos.z, '-' + d, '#ff6b81', 18);
    this.audio.hurt();
    this.shake(0.25);
    if (P.hp <= 0) this.die();
  }

  die() {
    const P = this.player;
    P.hp = 0;
    P.dead = true;
    this.rhythm.combo = 0;
    this.particles.burst(P.pos.x, P.pos.y + 1, P.pos.z, _c.set('#bda8df'), 40, { speed: 8, life: 1.2, kind: 1 });
    this.audio.fail();
    setTimeout(() => document.getElementById('death').classList.remove('hidden'), 900);
  }

  respawn() {
    document.getElementById('death').classList.add('hidden');
    const P = this.player;
    if (this.activities.rift) this.activities.exitRift();
    let best = null, bd = Infinity;
    for (const p of this.activities.pois) {
      if (p.type !== 'pylon' || !this.profile.pylons.includes(p.id)) continue;
      const d = Math.hypot(p.x - P.pos.x, p.z - P.pos.z);
      if (d < bd) { bd = d; best = p; }
    }
    P.dead = false;
    P.hp = P.stats.maxHp;
    P.shield = 0;
    P.sp = RULES.turn_economy.shared_sp_start;
    this.rhythm.encore = Math.max(this.rhythm.encore, P.stats.encoreStart);
    P.invulnUntil = this.time + 2;
    this.travelTo(best || { x: 0, z: -22, name: HUB.name });
  }

  // ------------------------------------------------------------ drops
  _dropMesh(kind, color) {
    let m;
    if (kind === 'gold') m = new THREE.Mesh(new THREE.OctahedronGeometry(0.22, 0), new THREE.MeshBasicMaterial({ color: '#ffd978' }));
    else if (kind === 'shard') m = new THREE.Mesh(new THREE.TetrahedronGeometry(0.3, 0), new THREE.MeshBasicMaterial({ color }));
    else if (kind === 'orb') m = new THREE.Mesh(new THREE.SphereGeometry(0.3, 10, 8), new THREE.MeshBasicMaterial({ color: '#62c8ff' }));
    else {
      m = new THREE.Group();
      const gem = new THREE.Mesh(new THREE.OctahedronGeometry(0.4, 0), new THREE.MeshBasicMaterial({ color }));
      gem.scale.set(0.8, 1.2, 0.8);
      m.add(gem);
    }
    this.scene.add(m);
    return m;
  }

  _drop(kind, x, z, extra) {
    const a = Math.random() * Math.PI * 2, s = 2 + Math.random() * 3;
    const color = extra.color || '#fff';
    const d = { kind, x, z, y: this.world.height(x, z) + 1, vx: Math.cos(a) * s, vz: Math.sin(a) * s, vy: 6 + Math.random() * 3, t: 0, mesh: this._dropMesh(kind, color), ...extra };
    if (kind === 'item' && extra.item.rarity >= 2) {
      d.beam = makeBeam(RARITIES[extra.item.rarity].color);
      this.scene.add(d.beam);
    }
    this.drops.push(d);
    return d;
  }

  dropItem(x, z, item) {
    this._drop('item', x, z, { item, color: RARITIES[item.rarity].color });
    if (item.rarity >= 3) {
      this.audio.loot(item.rarity);
      if (item.rarity === 4) { this.ui.banner('✦ OPUS ✦', item.name); this.shake(0.4); }
    }
  }

  dropGold(x, z, amount, count = 1) {
    const each = Math.max(1, Math.round(amount / count));
    for (let i = 0; i < count; i++) this._drop('gold', x, z, { amount: each });
  }

  dropShards(x, z, n, element) {
    const sh = SHARD_BY_ELEMENT[element] || SHARD_BY_ELEMENT.Forte;
    for (let i = 0; i < n; i++) this._drop('shard', x, z, { amount: Math.max(1, Math.round(sh.value / 5)), shard: sh, color: ELEMENT_STYLE[element]?.color || '#82d2db' });
  }

  dropOrb(x, z) { this._drop('orb', x, z, {}); }

  pickup(d) {
    const pr = this.profile, P = this.player;
    if (d.kind === 'gold') {
      const v = Math.round(d.amount * (1 + P.stats.gold));
      pr.gold += v;
      this.overlay.text(P.pos.x, P.pos.y + 2, P.pos.z, '+' + v + '●', '#ffd978', 12, { life: 0.6, bold: false });
      this.audio.pickup();
    } else if (d.kind === 'shard') {
      pr.shards += d.amount;
      this.overlay.text(P.pos.x, P.pos.y + 2.2, P.pos.z, `+${d.amount} ${d.shard.name}`, ELEMENT_STYLE[d.shard.element]?.color || '#82d2db', 12, { life: 0.8, bold: false });
      this.audio.pickup();
    } else if (d.kind === 'orb') {
      P.heal(P.stats.maxHp * 0.12);
      P.sp = Math.min(P.stats.spMax, P.sp + 1);
      this.audio.chime(6);
    } else if (d.kind === 'item') {
      if (!this.loot.add(d.item)) {
        if (this.time - (this._fullT || -9) > 5) { this._fullT = this.time; this.ui.toast('Bag full — salvage in the Wardrobe 👗'); }
        return false;
      }
      const R = RARITIES[d.item.rarity];
      this.ui.toast(`${d.item.name}`, 'item', R.color);
      if (d.item.rarity < 3) this.audio.loot(d.item.rarity);
    }
    return true;
  }

  removeDrop(i) {
    const d = this.drops[i];
    this.scene.remove(d.mesh);
    if (d.beam) this.scene.remove(d.beam);
    d.mesh.traverse((o) => { if (o.geometry) o.geometry.dispose(); if (o.material) o.material.dispose(); });
    this.drops.splice(i, 1);
  }

  collectAllDrops() {
    for (let i = this.drops.length - 1; i >= 0; i--) { this.pickup(this.drops[i]); this.removeDrop(i); }
  }

  updateDrops(dt) {
    const P = this.player;
    const labels = [];
    for (let i = this.drops.length - 1; i >= 0; i--) {
      const d = this.drops[i];
      d.t += dt;
      const gy = this.world.inRift ? 0 : Math.max(this.world.height(d.x, d.z), WATER);
      const dist = Math.hypot(P.pos.x - d.x, P.pos.z - d.z);
      const magnet = !P.dead && d.t > 0.5 && ((d.kind !== 'item' && dist < 6.5) || (d.kind === 'item' && dist < 2.4));
      if (magnet) {
        const sp = 16 * dt;
        d.x += ((P.pos.x - d.x) / (dist || 1)) * Math.min(dist, sp);
        d.z += ((P.pos.z - d.z) / (dist || 1)) * Math.min(dist, sp);
        d.y = lerp(d.y, P.pos.y + 1, 0.2);
        if (dist < 0.9 && this.pickup(d)) { this.removeDrop(i); continue; }
      } else if (d.vy !== 0 || d.y > gy + 0.45) {
        d.vy -= 20 * dt;
        d.x += d.vx * dt; d.z += d.vz * dt;
        d.vx *= 1 - dt * 2; d.vz *= 1 - dt * 2;
        d.y += d.vy * dt;
        if (d.y <= gy + 0.45) { d.y = gy + 0.45; d.vy = 0; d.vx = d.vz = 0; }
      }
      d.mesh.position.set(d.x, d.y + Math.sin(this.time * 3 + i) * 0.08, d.z);
      d.mesh.rotation.y += dt * 3;
      if (d.beam) d.beam.position.set(d.x, gy, d.z);
      if (d.kind === 'item' && d.item.rarity >= 2 && dist < 40) labels.push({ x: d.x, y: d.y + 0.8, z: d.z, text: d.item.name, color: RARITIES[d.item.rarity].color });
      if (d.t > 180) this.removeDrop(i);
    }
    return labels;
  }

  // ------------------------------------------------------------ progression
  onLevelUp() {
    const P = this.player, pr = this.profile;
    P.recalc();
    P.hp = P.stats.maxHp;
    P.sp = P.stats.spMax;
    this.audio.levelUp();
    this.ui.banner(`Level ${pr.level}`, 'Your melody grows');
    this.particles.burst(P.pos.x, P.pos.y + 1, P.pos.z, _c.set('#ffd978'), 50, { speed: 9, life: 1.2, kind: 3, size: 1, gravity: -3 });
    this.world.pulse(P.pos.x, P.pos.z, 2, true);
    const fresh = Object.values(SKILL_BY_ID).filter((s) => s.unlockLevel === pr.level && !pr.learned.includes(s.id));
    for (const s of fresh) setTimeout(() => this.ui.toast(`New skill: ${s.name} (${s.element}) — equip it in ♫ Skills`, 'gold'), 700);
    this.save();
  }

  onGearChanged() { this.save(); }

  bountyEvent(type, n = 1, data = {}) { this.progress.event(type, n, data); }

  save() {
    if (!this.started) return;
    const pr = this.profile;
    pr.explored = this.progress.encodeExplored();
    if (!this.activities.rift && !this.player.dead) pr.spawn = { x: this.player.pos.x, z: this.player.pos.z };
    saveProfile(pr);
  }

  wipe() {
    wipeProfile();
    this.started = false;
    location.reload();
  }

  startCalibration() {
    this.calibrating = [];
    this.ui.hint('Calibration: tap ⚔ exactly on 8 beats of the music');
  }

  calibrateTap(perfMs) {
    const a = this.audio;
    const t = a.audibleTime(perfMs);
    const b = a.nearestBeat(t);
    if (!b) return;
    this.calibrating.push((t - b.time) * 1000);
    this.ui.hint(`Calibration: ${this.calibrating.length}/8`);
    this.audio.tick(true);
    if (this.calibrating.length >= 8) {
      const s = this.calibrating.slice().sort((x, y) => x - y);
      const median = (s[3] + s[4]) / 2;
      this.profile.settings.offsetMs = Math.round(median);
      this.calibrating = null;
      this.ui.hint(null);
      this.ui.toast(`Latency offset set to ${this.profile.settings.offsetMs} ms`, 'gold');
      this.save();
    }
  }

  // ------------------------------------------------------------ display
  applyQuality() {
    const q = this.profile.settings.quality;
    const dpr = window.devicePixelRatio || 1;
    this.baseRatio = q === 'low' ? 1 : q === 'high' ? Math.min(dpr, 2) : Math.min(dpr, isTouch ? 1.5 : 2);
    this._fps.scale = 1;
    this.renderer.setPixelRatio(this.baseRatio);
  }

  resize() {
    const w = innerWidth, h = innerHeight;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.fov = w < h ? 62 : 40;
    this.camera.updateProjectionMatrix();
    this.overlay.resize();
    this.particles.mat.uniforms.uScale.value = (h * this.renderer.getPixelRatio()) / (2 * Math.tan((this.camera.fov * Math.PI) / 360));
  }

  adaptQuality(dt) {
    if (this.profile.settings.quality !== 'auto') return;
    const f = this._fps;
    f.t += dt; f.n++;
    if (f.t < 3) return;
    const fps = f.n / f.t;
    f.t = 0; f.n = 0;
    if (fps < 42 && f.scale > 0.55) f.scale -= 0.15;
    else if (fps > 57 && f.scale < 1) f.scale = Math.min(1, f.scale + 0.1);
    else return;
    this.renderer.setPixelRatio(Math.max(0.75, this.baseRatio * f.scale));
    this.resize();
  }

  // ------------------------------------------------------------ loop
  onBeat(beat) {
    this.beatIndex = beat.index;
    const P = this.player;
    this.ui.beat(beat);
    this.world.swingPendulum();
    if (!P.dead) this.world.pulse(P.pos.x, P.pos.z, beat.inBar === 0 ? 1 : 0.55);
    if (this.paused || !this.started) return;
    for (const e of this.enemies) e.onBeat(beat);
    this.combat.onBeat(beat);
    this.sheep.onBeat(beat);
    for (let i = this.hazards.length - 1; i >= 0; i--) {
      const h = this.hazards[i];
      if (h.land > beat.index) continue;
      this.decals.release(h.decal);
      if (!P.dead && Math.hypot(P.pos.x - h.x, P.pos.z - h.z) < h.r) this.hurtPlayer(h.dmg, null);
      this.hazards.splice(i, 1);
    }
    if (beat.inBar === 0) {
      this.rhythm.onBar(beat);
      if (beat.bar % 2 === 0 && !P.dead) P.sp = Math.min(P.stats.spMax, P.sp + 1);
      if (this.rhythm.encoreActive && !P.dead) {
        const p = { x: P.pos.x, z: P.pos.z, r: 7 };
        this.combat.hitAll(this.combat.enemiesIn('circle', p), 1.2, { mult: RULES.rhythm.max_combat_multiplier, element: P.stats.basicElement, tough: 2 });
        this.combat.flash('ring', p.x, p.z, { r: 7, inner: 5.8 }, '#ffd978');
      }
    }
    if (this.ui.attackHeld && !P.dead && !this.activities.shrine && !this.calibrating && beat.index > this.autoAttackBeat) this.autoAttack(beat);
    this.audio.setIntensity(this.musicIntensity());
  }

  frame() {
    requestAnimationFrame(() => this.frame());
    const now = performance.now();
    let dt = (now - this.clock) / 1000;
    this.clock = now;
    if (dt > 0.1) dt = 0.1;
    if (!this.started) return;
    const audible = this.audio.audibleTime(now);
    for (const b of this.audio.pollBeats(audible)) this.onBeat(b);
    const lb = this.audio.lastBeatAt(audible);
    this.beatPhase = lb ? clamp((audible - lb.time) / lb.spb, 0, 1) : 0;
    this.adaptQuality(dt);

    if (!this.paused) this.simulate(dt);
    this.world.frame(dt, this.time, this.player.pos, this.beatPhase, this.rhythm.crescendo / 100);
    this.updateCamera(dt);
    this.decals.update(dt);
    this.particles.update(dt);
    const labels = this.paused ? [] : this.updateDrops(dt);
    const bars = [];
    for (const e of this.enemies) {
      if (e.dead || e.boss) continue;
      if (e.hp < e.maxHp || e.elite) {
        bars.push({ x: e.pos.x, y: e.pos.y + 1.9 * e.scale + 0.3, z: e.pos.z, w: e.elite ? 64 : 38, h: e.elite ? 6 : 4, frac: e.hp / e.maxHp, color: e.elite ? '#ff9a4a' : '#ff6b81', tough: e.maxTough ? e.tough / e.maxTough : undefined, broken: e.broken, name: e.elite ? e.name : null, nameColor: '#ffb27a' });
      }
    }
    this.overlay.draw(dt, bars, labels);
    this.ui.update(dt);
    if (this.painterly) this.painterly.render(this.renderer, this.scene, this.camera);
    else this.renderer.render(this.scene, this.camera);
  }

  simulate(dt) {
    this.time += dt;
    const P = this.player;
    const mv = this.activities.shrine || this.calibrating ? { x: 0, z: 0 } : this.ui.move();
    const speedBurden = this.activities.burdenScale('speed');
    P.update(dt, mv.x * speedBurden, mv.z * speedBurden);
    this.sheep.update(dt);
    // Enemies + separation.
    const E = this.enemies;
    for (let i = E.length - 1; i >= 0; i--) {
      const e = E[i];
      if (e.dying !== undefined) {
        e.dying -= dt;
        const s = Math.max(0.01, e.dying / 0.35);
        e.mesh.scale.setScalar(e.scale * (1 + (1 - s) * 0.6));
        e.mat.opacity = s;
        if (e.dying <= 0) { e.remove(); e.removed = true; E.splice(i, 1); }
        continue;
      }
      e.update(dt);
    }
    for (let i = 0; i < E.length; i++) {
      const a = E[i];
      if (a.dead) continue;
      for (let j = i + 1; j < E.length; j++) {
        const b = E[j];
        if (b.dead) continue;
        const dx = b.pos.x - a.pos.x, dz = b.pos.z - a.pos.z, d = Math.hypot(dx, dz), min = (a.radius + b.radius) * 0.85;
        if (d > 0.001 && d < min) {
          const push = (min - d) * 0.5, nx = dx / d, nz = dz / d;
          if (!a.boss) { a.pos.x -= nx * push; a.pos.z -= nz * push; }
          if (!b.boss) { b.pos.x += nx * push; b.pos.z += nz * push; }
        }
      }
      if (!P.dead && !P.dash) {
        const dx = P.pos.x - a.pos.x, dz = P.pos.z - a.pos.z, d = Math.hypot(dx, dz), min = a.radius + 0.4;
        if (d > 0.001 && d < min) { P.pos.x += (dx / d) * (min - d); P.pos.z += (dz / d) * (min - d); }
      }
    }
    this.combat.update(dt);
    this.activities.update(dt);
    this.activities.updateShrine();
    // World streaming, zones, exploration.
    if (!this.world.inRift) {
      this.world.update(P.pos.x, P.pos.z, 1);
      for (const c of this.world.chimes) {
        if (Math.abs(c.x - P.pos.x) < 1.6 && Math.abs(c.z - P.pos.z) < 1.6 && this.time - c.last > 2) {
          c.last = this.time;
          this.audio.chime(c.i);
          this.particles.burst(c.x, c.y, c.z, _c.set('#9fe6ff'), 6, { speed: 2, life: 0.8, kind: 1, gravity: -2 });
        }
      }
      this._explore += dt;
      if (this._explore > 0.5) {
        this._explore = 0;
        this.progress.reveal(P.pos.x, P.pos.z);
        const d = this.world.dominantBiome(P.pos.x, P.pos.z);
        const zone = d.r < HUB.radius + 20 ? 'hub' : d.weight > 0.6 ? d.biome.id : this.zoneId;
        if (zone !== this.zoneId) {
          const first = this.zoneId === null;
          this.zoneId = zone;
          this.audio.setScore(this.scoreForPosition());
          if (!first) {
            if (zone === 'hub') this.ui.banner(HUB.name, 'Safe harbour · Forge · Bounties · Blessings · Rift Gate');
            else this.ui.banner(d.biome.name.split('—')[0].trim(), `${d.biome.name.split('—')[1]?.trim() || ''} · ${d.biome.bpm} BPM in ${d.biome.meter}/4 · Lv ${d.biome.levels[0]}–${d.biome.levels[1]}`);
          }
        }
      }
    }
    this.safeZone = !this.world.inRift && Math.hypot(P.pos.x, P.pos.z) < HUB.radius;
    this.inCombat = this.enemies.some((e) => !e.dead && e.aggro && Math.hypot(e.pos.x - P.pos.x, e.pos.z - P.pos.z) < 28);
    if (!this.inCombat && !P.dead && P.hp < P.stats.maxHp) P.hp = Math.min(P.stats.maxHp, P.hp + P.stats.maxHp * (this.safeZone ? 0.12 : 0.03) * dt);
    // Palette follows the biome you stand in.
    this.world.palette(P.pos.x, P.pos.z, this.pal);
    const k = Math.min(1, dt * 1.5);
    this.scene.fog.color.lerp(this.pal.fog, k);
    this.scene.background.lerp(this.pal.fog, k);
    this.world.water.material.color.lerp(this.pal.water, k);
    this.sun.color.lerp(this.pal.light, k);
    if (this.world.inRift) { this.scene.fog.near = 45; this.scene.fog.far = 110; } else { this.scene.fog.near = 75; this.scene.fog.far = 175; }
    this.ui.tutorialTick(dt);
    this.profile.stats.playSeconds += dt;
    this._save += dt;
    if (this._save > 15) { this._save = 0; this.save(); }
  }

  updateCamera(dt) {
    const P = this.player;
    const portrait = innerWidth < innerHeight;
    const lead = 0.35;
    this.camTarget.x = lerp(this.camTarget.x, P.pos.x + P.vel.x * lead, Math.min(1, dt * 6));
    this.camTarget.z = lerp(this.camTarget.z, P.pos.z + P.vel.z * lead, Math.min(1, dt * 6));
    this.camTarget.y = lerp(this.camTarget.y, P.pos.y, Math.min(1, dt * 4));
    const dist = portrait ? 34 : 31;
    const encoreZoom = this.rhythm.encoreActive ? 0.88 : 1;
    this.shakeAmt = Math.max(0, this.shakeAmt - dt * 2.2);
    const s = this.shakeAmt * this.shakeAmt;
    this.camera.position.set(
      this.camTarget.x + (Math.random() - 0.5) * s,
      this.camTarget.y + dist * 0.8 * encoreZoom + (Math.random() - 0.5) * s,
      this.camTarget.z + dist * 0.62 * encoreZoom,
    );
    this.camera.lookAt(this.camTarget.x, this.camTarget.y + 1, this.camTarget.z);
    this.sun.position.set(this.camTarget.x + 40, this.camTarget.y + 80, this.camTarget.z + 30);
    this.sun.target.position.copy(this.camTarget);
    this.sun.target.updateMatrixWorld();
  }
}

export { xpToNext };
