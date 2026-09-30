// World content: camps, chests, pylons, lost sheet music, music-key shrines,
// biome Maestros (world bosses), Elite Chorus events and Resonance Rifts.

import * as THREE from 'three';
import { BIOMES, HUB, WORLD_SEED, RIFT_POOL, BURDENS, ELITE_AFFIXES, RIFT_STYLE, ELEMENT_STYLE } from './design.js';
import { Enemy } from './entities.js';
import { mulberry32, pick, clamp } from './util.js';
import { makeBeam } from './fx.js';

const L = (hex, o = {}) => new THREE.MeshLambertMaterial({ color: hex, flatShading: true, ...o });

export class Activities {
  constructor(game) {
    this.g = game;
    this.pois = [];
    this.rift = null;
    this.shrine = null;
    this.eventAt = 110;
    this.event = null;
    this._acc = 0;
    this.generate();
  }

  // ------------------------------------------------------------ placement
  generate() {
    const g = this.g, W = g.world;
    const rng = mulberry32(WORLD_SEED + 99);
    const add = (p) => { this.pois.push(p); return p; };
    add({ type: 'pylon', id: 'pylon_hub', x: 0, z: -22, name: 'Shorewake Pylon', biome: -1 });
    add({ type: 'forge', x: 11, z: -9, name: 'Forge' });
    add({ type: 'board', x: -11, z: -9, name: 'Bounty Board' });
    add({ type: 'font', x: 0, z: 13, name: 'Blessing Font' });
    add({ type: 'rift', id: 'rift_hub', x: -20, z: 22, name: 'Rift Gate' });
    const spot = (angle, spread, rMin, rMax, spacing = 34) => {
      for (let t = 0; t < 60; t++) {
        const a = angle + (rng() * 2 - 1) * spread, r = rMin + rng() * (rMax - rMin);
        const x = Math.cos(a) * r, z = Math.sin(a) * r;
        const h = W.sample(x, z);
        if (h < 0.4 || W.hub > 0) continue;
        if (Math.abs(W.sample(x + 3, z) - h) > 2.2 || Math.abs(W.sample(x, z + 3) - h) > 2.2) continue;
        if (this.pois.some((p) => (p.x - x) ** 2 + (p.z - z) ** 2 < spacing * spacing)) continue;
        return { x, z };
      }
      return null;
    };
    BIOMES.forEach((b, bi) => {
      const ax = Math.cos(b.angle), az = Math.sin(b.angle);
      add({ type: 'boss', id: 'boss_' + b.id, biome: bi, x: b.cx - ax * 30, z: b.cz - az * 30, bx: b.cx - ax * 17, bz: b.cz - az * 17, name: b.bossName, cdUntil: 0 });
      [[240, -0.18], [520, 0.2]].forEach(([r, da], k) => {
        const s = spot(b.angle + da, 0.12, r - 30, r + 30, 30);
        if (s) add({ type: 'pylon', id: `pylon_${b.id}_${k}`, biome: bi, ...s, name: `${b.name.split('—')[0].trim()} Pylon ${k + 1}` });
      });
      const rs = spot(b.angle + 0.32, 0.1, 300, 380);
      if (rs) add({ type: 'rift', id: 'rift_' + b.id, biome: bi, ...rs, name: 'Rift Gate' });
      for (let i = 0; i < 16; i++) { const s = spot(b.angle, 0.55, 110, 640, 46); if (s) add({ type: 'camp', biome: bi, ...s, active: false, clearedAt: -999, enemies: [] }); }
      for (let i = 0; i < 7; i++) { const s = spot(b.angle, 0.55, 100, 650, 26); if (s) add({ type: 'chest', biome: bi, ...s, openedAt: -999 }); }
      for (let i = 0; i < 3; i++) { const s = spot(b.angle, 0.5, 140, 600, 40); if (s) add({ type: 'shrine', id: `shrine_${b.id}_${i}`, biome: bi, ...s, name: 'Music-Key Shrine', cdUntil: 0 }); }
      for (let i = 0; i < 5; i++) { const s = spot(b.angle, 0.55, 120, 650, 30); if (s) add({ type: 'sheet', id: `sheet_${b.id}_${i}`, biome: bi, ...s }); }
    });
    for (const p of this.pois) {
      p.y = W.sample(p.x, p.z);
      p.level = p.biome >= 0 ? W.zoneLevel(p.x, p.z) : 1;
      this.buildMesh(p);
    }
  }

  near(x, z, r) { return this.pois.filter((p) => Math.abs(p.x - x) < r && Math.abs(p.z - z) < r); }

  buildMesh(p) {
    const g = this.g;
    const grp = new THREE.Group();
    grp.position.set(p.x, p.y, p.z);
    if (p.type === 'pylon') {
      const base = new THREE.Mesh(new THREE.CylinderGeometry(1.4, 1.8, 0.8, 8), L('#e8e0f0'));
      base.position.y = 0.4;
      p.crystalMat = L('#ffffff', { emissive: '#8a8a9a', emissiveIntensity: 0.3 });
      const c = new THREE.Mesh(new THREE.OctahedronGeometry(0.9, 0), p.crystalMat);
      c.position.y = 3; c.scale.set(1, 2, 1);
      p.spin = c;
      grp.add(base, c);
    } else if (p.type === 'chest') {
      const body = new THREE.Mesh(new THREE.BoxGeometry(1.3, 0.8, 0.9), L('#b07a4a'));
      body.position.y = 0.4;
      const lid = new THREE.Mesh(new THREE.BoxGeometry(1.35, 0.3, 0.95), L('#ffd978', { emissive: '#d9a84a', emissiveIntensity: 0.3 }));
      lid.position.y = 0.95;
      p.lid = lid;
      grp.add(body, lid);
      grp.rotation.y = Math.random() * Math.PI;
    } else if (p.type === 'shrine') {
      for (let k = 0; k < 4; k++) {
        const a = (k / 4) * Math.PI * 2;
        const st = new THREE.Mesh(new THREE.BoxGeometry(0.7, 2.6 + (k % 2) * 0.6, 0.5), L('#d8d0e4'));
        st.position.set(Math.cos(a) * 2.6, 1.3, Math.sin(a) * 2.6);
        st.rotation.y = -a;
        grp.add(st);
      }
      p.clefMat = L('#ffffff', { emissive: '#62c8ff', emissiveIntensity: 0.5 });
      const clef = new THREE.Mesh(new THREE.TorusKnotGeometry(0.45, 0.12, 48, 6, 2, 3), p.clefMat);
      clef.position.y = 2.2;
      p.spin = clef;
      grp.add(clef);
    } else if (p.type === 'sheet') {
      const page = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 1.2), L('#fffaf0', { side: THREE.DoubleSide, emissive: '#fff2c8', emissiveIntensity: 0.6 }));
      page.position.y = 1.4;
      p.spin = page;
      grp.add(page);
    } else if (p.type === 'rift') {
      const ring = new THREE.Mesh(new THREE.TorusGeometry(2.2, 0.28, 8, 28), L('#2a2140', { emissive: '#8f6bff', emissiveIntensity: 0.6 }));
      ring.position.y = 2.6;
      const disc = new THREE.Mesh(new THREE.CircleGeometry(2.0, 28), new THREE.MeshBasicMaterial({ color: '#b89cff', transparent: true, opacity: 0.55, side: THREE.DoubleSide }));
      disc.position.y = 2.6;
      p.spin = disc; p.ring = ring;
      grp.add(ring, disc);
    } else if (p.type === 'boss') {
      const altar = new THREE.Mesh(new THREE.CylinderGeometry(1.6, 2, 1, 8), L('#e0d6ea'));
      altar.position.y = 0.5;
      p.orbMat = L('#ffffff', { emissive: '#ff5470', emissiveIntensity: 0.6 });
      const orb = new THREE.Mesh(new THREE.IcosahedronGeometry(0.6, 0), p.orbMat);
      orb.position.y = 1.8;
      p.spin = orb;
      grp.add(altar, orb);
    } else return;
    p.mesh = grp;
    g.world.root.add(grp);
  }

  // ------------------------------------------------------------ per frame
  update(dt) {
    const g = this.g, P = g.player;
    if (this.rift) return this.updateRift(dt);
    for (const p of this.pois) {
      if (p.spin) {
        p.spin.rotation.y += dt * 1.5;
        p.spin.position.y = (p.type === 'pylon' ? 3 : p.type === 'sheet' ? 1.4 : p.type === 'rift' ? 2.6 : 2) + Math.sin(g.time * 2 + p.x) * 0.15;
      }
    }
    this._acc += dt;
    if (this._acc < 0.25) return;
    this._acc = 0;
    for (const p of this.pois) {
      const d = Math.hypot(p.x - P.pos.x, p.z - P.pos.z);
      if (p.type === 'camp') {
        const ready = g.time - p.clearedAt > 150;
        if (!p.active && ready && d < 60 && !P.dead) this.spawnCamp(p);
        else if (p.active && d > 115) this.despawnCamp(p);
        else if (p.active && p.enemies.every((e) => e.dead)) this.clearCamp(p);
      } else if (p.type === 'chest') {
        const closed = g.time - p.openedAt > 600;
        if (p.lid) p.lid.rotation.x = closed ? 0 : -1.1;
        if (closed && d < 2.8 && !P.dead) this.openChest(p);
      } else if (p.type === 'sheet') {
        const have = g.profile.sheets.includes(p.id);
        if (p.mesh) p.mesh.visible = !have;
        if (!have && d < 2.4) this.collectSheet(p);
      } else if (p.type === 'pylon') {
        const known = g.profile.pylons.includes(p.id);
        p.crystalMat.emissive.set(known ? '#62c8ff' : '#8a8a9a');
        p.crystalMat.emissiveIntensity = known ? 0.8 : 0.3;
        if (!known && d < 8) {
          g.profile.pylons.push(p.id);
          g.ui.toast(`Pylon attuned: ${p.name} — fast travel from the map`, 'aqua');
          g.audio.levelUp();
          g.world.pulse(p.x, p.z, 1.5, true);
          g.save();
        }
      } else if (p.type === 'shrine') {
        const done = g.profile.shrines.includes(p.id);
        p.clefMat.emissive.set(done ? '#ffd978' : '#62c8ff');
      } else if (p.type === 'boss') {
        p.orbMat.emissiveIntensity = p.alive && !p.alive.dead ? 1.5 : g.time > p.cdUntil ? 0.7 : 0.1;
      }
    }
    this.updateEvent();
  }

  // ------------------------------------------------------------ camps
  enemyLevel(p) {
    return Math.max(p.level, this.g.profile.level - 2);
  }

  spawnCamp(p) {
    const g = this.g, b = BIOMES[p.biome];
    const rng = Math.random;
    p.active = true;
    p.enemies = [];
    const lvl = this.enemyLevel(p);
    const elite = rng() < 0.16 + p.biome * 0.02;
    const n = 3 + Math.floor(rng() * 3) + (p.biome >= 2 ? 1 : 0);
    for (let i = 0; i < n; i++) {
      const a = (i / n) * Math.PI * 2 + rng(), r = 2 + rng() * 4;
      const isElite = elite && i === 0;
      const def = isElite ? pick(rng, b.elites) : pick(rng, b.trash);
      const affixes = isElite ? [pick(rng, ELITE_AFFIXES).id] : [];
      if (isElite && lvl >= 15 && rng() < 0.5) affixes.push(pick(rng, ELITE_AFFIXES.filter((x) => !affixes.includes(x.id))).id);
      p.enemies.push(g.spawnEnemy(def.id, lvl, { x: p.x + Math.cos(a) * r, z: p.z + Math.sin(a) * r, elite: isElite, affixes, camp: p }));
    }
  }

  despawnCamp(p) {
    for (const e of p.enemies) if (!e.dead) this.g.removeEnemy(e);
    p.enemies = [];
    p.active = false;
  }

  clearCamp(p) {
    const g = this.g;
    p.active = false;
    p.enemies = [];
    p.clearedAt = g.time;
    g.dropGold(p.x, p.z, 8 + p.level * 4, 5);
    g.ui.toast('Camp cleared', 'soft');
  }

  // ------------------------------------------------------------ pickups
  openChest(p) {
    const g = this.g;
    p.openedAt = g.time;
    const n = 1 + Math.floor(Math.random() * 2);
    for (let i = 0; i < n; i++) g.dropItem(p.x, p.z, g.loot.make(this.enemyLevel(p) + 1, { min: 1, bonus: 0.2 }));
    g.dropGold(p.x, p.z, 10 + p.level * 6, 6);
    g.dropShards(p.x, p.z, 3, pick(Math.random, BIOMES[p.biome].elements));
    g.bountyEvent('chests', 1);
    g.audio.loot(2);
    g.particles.burst(p.x, p.y + 1, p.z, new THREE.Color('#ffd978'), 30, { speed: 8, life: 0.9, kind: 3 });
  }

  collectSheet(p) {
    const g = this.g;
    g.profile.sheets.push(p.id);
    const locked = g.progress.lockedSkills();
    if (locked.length) {
      const s = locked.sort((a, b) => a.unlockLevel - b.unlockLevel)[0];
      g.profile.learned.push(s.id);
      g.ui.toast(`Lost Sheet Music! Learned ${s.name} (${s.element})`, 'gold');
    } else {
      g.profile.notes += 10;
      g.ui.toast('Lost Sheet Music! +10 Golden Notes', 'gold');
    }
    g.audio.levelUp();
    g.particles.burst(p.x, p.y + 1.4, p.z, new THREE.Color('#fff2c8'), 30, { speed: 6, life: 1, kind: 1, size: 1 });
    g.save();
  }

  // ------------------------------------------------------------ bosses
  summonBoss(p) {
    const g = this.g, b = BIOMES[p.biome];
    if (p.alive && !p.alive.dead) return;
    if (g.time < p.cdUntil) { g.ui.toast(`${b.bossName} is resting (${Math.ceil(p.cdUntil - g.time)}s)`); return; }
    const lvl = Math.max(b.levels[1], g.profile.level - 1);
    const e = g.spawnEnemy(b.boss, lvl, { x: p.bx, z: p.bz, boss: true, bossName: b.bossName, aggro: true });
    e.poi = p;
    p.alive = e;
    g.ui.banner(b.bossName, `Maestro of ${b.name.split('—')[0].trim()} · Lv ${lvl}`);
    g.world.pulse(p.bx, p.bz, 2, true);
    g.shake(0.6);
  }

  bossDefeated(e) {
    const p = e.poi;
    if (p) { p.cdUntil = this.g.time + 180; p.alive = null; }
  }

  // ------------------------------------------------------------ Elite Chorus events
  updateEvent() {
    const g = this.g, P = g.player;
    if (this.event) {
      const ev = this.event;
      if (ev.enemies.every((e) => e.dead)) {
        g.ui.toast('Elite Chorus silenced! Bonus cache', 'gold');
        for (let i = 0; i < 2; i++) g.dropItem(ev.x, ev.z, g.loot.make(ev.level + 1, { min: 1, bonus: 0.35 }));
        g.dropGold(ev.x, ev.z, 20 + ev.level * 8, 8);
        g.profile.notes += 5;
        this.event = null;
        this.eventAt = g.time + 150 + Math.random() * 60;
      } else if (Math.hypot(ev.x - P.pos.x, ev.z - P.pos.z) > 220) {
        for (const e of ev.enemies) if (!e.dead) g.removeEnemy(e);
        this.event = null;
        this.eventAt = g.time + 60;
      }
      return;
    }
    if (g.time < this.eventAt || g.safeZone || P.dead) return;
    const d = g.world.dominantBiome(P.pos.x, P.pos.z);
    if (d.r < HUB.radius + 40) { this.eventAt = g.time + 20; return; }
    for (let t = 0; t < 20; t++) {
      const a = Math.random() * Math.PI * 2, r = 45 + Math.random() * 35;
      const x = P.pos.x + Math.cos(a) * r, z = P.pos.z + Math.sin(a) * r;
      const h = g.world.sample(x, z);
      if (h < 0.4 || Math.hypot(x, z) > 660 || g.world.hub > 0) continue;
      const b = d.biome, lvl = Math.max(g.world.zoneLevel(x, z), g.profile.level - 1);
      const ev = { x, z, level: lvl, enemies: [] };
      ev.enemies.push(g.spawnEnemy(pick(Math.random, b.elites).id, lvl, { x, z, elite: true, affixes: [pick(Math.random, ELITE_AFFIXES).id] }));
      for (let k = 0; k < 4; k++) ev.enemies.push(g.spawnEnemy(pick(Math.random, b.trash).id, lvl, { x: x + Math.cos(k * 1.6) * 4, z: z + Math.sin(k * 1.6) * 4 }));
      this.event = ev;
      g.ui.banner('Elite Chorus', 'A golden chorus sings nearby — follow the ★ on the map');
      return;
    }
    this.eventAt = g.time + 15;
  }

  // ------------------------------------------------------------ Music-key shrines
  startShrine(p) {
    const g = this.g, a = g.audio;
    if (g.player.dead) return;
    if (g.enemies.some((e) => !e.dead && e.aggro)) { g.ui.toast('The shrine cannot hear you over the battle'); return; }
    if (g.time < p.cdUntil) { g.ui.toast(`The shrine is still ringing (${Math.ceil(p.cdUntil - g.time)}s)`); return; }
    const now = a.audibleTime();
    const b = a.lastBeatAt(now) || a.nearestBeat(now);
    const meter = b.meter, spb = b.spb;
    const toBar = meter - b.inBar;
    const callStart = b.time + toBar * spb + meter * spb; // leave one count-in bar
    const slots = meter * 2;
    const pick8 = new Set([0]);
    const want = 3 + Math.min(3, Math.floor(p.biome / 2) + 1);
    while (pick8.size < want) pick8.add(1 + Math.floor(Math.random() * (slots - 1)));
    const order = [...pick8].sort((x, y) => x - y);
    const motif = BIOMES[p.biome].motif;
    const key = BIOMES[p.biome].key;
    const call = order.map((s, i) => ({ slot: s, t: callStart + (s * spb) / 2, midi: key + 12 + motif[i % motif.length] }));
    for (const c of call) a._voice('bell', c.t, c.midi, 0.6, 0.16, a.sfxBus, true);
    for (let k = 0; k < meter; k++) a.tick(k === 0, b.time + toBar * spb + k * spb);
    const respStart = callStart + meter * spb;
    this.shrine = {
      p, call, slots, meter, spb, callStart, respStart,
      resp: call.map((c) => ({ slot: c.slot, t: c.t + meter * spb, midi: c.midi, grade: null })),
      extra: 0, end: respStart + meter * spb + 0.25,
    };
    g.ui.openShrine(this.shrine);
  }

  shrineTap(perfMs) {
    const g = this.g, s = this.shrine;
    if (!s) return;
    const t = g.audio.audibleTime(perfMs) - g.profile.settings.offsetMs / 1000;
    const W = g.rhythm.windows();
    let best = null, bd = Infinity;
    for (const r of s.resp) { if (r.grade) continue; const d = Math.abs(t - r.t); if (d < bd) { bd = d; best = r; } }
    const ms = bd * 1000;
    if (!best || ms > W.good) {
      s.extra++;
      g.audio.fail();
      return;
    }
    best.grade = ms <= W.perfect ? 'Perfect' : ms <= W.great ? 'Great' : 'Good';
    g.audio._voice('bell', g.audio.now, best.midi, 0.6, 0.16, g.audio.sfxBus, true);
    g.ui.shrineGrade(best);
  }

  updateShrine() {
    const g = this.g, s = this.shrine;
    if (!s) return;
    const now = g.audio.audibleTime();
    g.ui.shrineFrame(s, now);
    if (now < s.end) return;
    this.shrine = null;
    const weights = { Perfect: 1, Great: 0.8, Good: 0.6 };
    const score = clamp(s.resp.reduce((acc, r) => acc + (r.grade ? weights[r.grade] : 0), 0) / s.resp.length - s.extra * 0.1, 0, 1);
    const p = s.p;
    g.ui.closeShrine();
    if (score < 0.4) {
      g.ui.toast('The phrase slips away… listen, then answer on the next bar.');
      g.audio.fail();
      return;
    }
    p.cdUntil = g.time + 45;
    const min = score >= 0.9 ? 3 : score >= 0.7 ? 2 : 1;
    g.dropItem(p.x, p.z, g.loot.make(this.enemyLevel(p) + 2, { min, bonus: 0.3 }));
    g.dropGold(p.x, p.z, 15 + p.level * 5, 6);
    const first = !g.profile.shrines.includes(p.id);
    if (first) {
      g.profile.shrines.push(p.id);
      g.profile.notes += 10;
      g.player.recalc();
      g.bountyEvent('shrine', 1);
    }
    g.ui.banner(`Phrase answered — ${Math.round(score * 100)}%`, first ? 'Attuned: +1% damage forever · +10 Golden Notes' : 'The shrine rewards you again');
    g.audio.levelUp();
    g.world.pulse(p.x, p.z, 2, true);
    g.save();
  }

  // ------------------------------------------------------------ Resonance Rifts
  riftDef(tier) {
    return { ...RIFT_STYLE, bpm: 124 + Math.min(24, tier * 2), motif: [0, 3, 7, 10, 8, 7] };
  }

  enterRift(tier, portal) {
    const g = this.g, P = g.player;
    g.clearWorldEnemies();
    g.combat.reset();
    g.decals.clear();
    const burden = tier >= 3 ? pick(Math.random, BURDENS) : null;
    this.rift = {
      tier, burden, progress: 0, time: 0, limit: 240, guardian: null, done: false, spawnT: 0, exit: null,
      level: g.profile.level + Math.max(0, tier - 1) * 2, hpMul: 1 + (tier - 1) * 0.15,
      returnPos: portal ? new THREE.Vector3(portal.x + 3, 0, portal.z + 3) : P.pos.clone(),
    };
    g.world.setRift(true);
    P.pos.set(0, 0, 0);
    g.sheep.pos.set(2, 0, 2);
    g.audio.setScore(this.riftDef(tier));
    g.rhythm.encore = Math.max(g.rhythm.encore, P.stats.encoreStart);
    g.ui.banner(`Resonance Rift · Tier ${tier}`, burden ? `Burden: ${burden.display_name} — ${burden.description} (+rarity)` : 'Silence the dissonance. Fill the bar.');
    g.shake(0.4);
  }

  burdenScale(kind) {
    const b = this.rift?.burden;
    if (!b) return 1;
    const m = b.magnitude / 100;
    if (kind === 'window' && b.rule_type === 'rhythm_timing_window') return 1 - m;
    if (kind === 'encore' && (b.rule_type === 'ultimate_gauge_recharge' || b.rule_type === 'ultimate_gauge')) return 1 - Math.min(0.5, m);
    if (kind === 'damage' && (b.rule_type === 'damage_taken' || b.rule_type === 'hp' || b.rule_type === 'toughness_damage_taken')) return 1 + Math.min(0.5, m);
    if (kind === 'speed' && b.rule_type === 'movement_speed') return 1 - Math.min(0.3, m / 2);
    if (kind === 'tough' && b.rule_type === 'toughness_damage') return 1 + m;
    return 1;
  }

  updateRift(dt) {
    const g = this.g, r = this.rift;
    if (r.done) return;
    r.time += dt;
    if (r.progress < 100) {
      r.spawnT -= dt;
      const alive = g.enemies.filter((e) => !e.dead).length;
      if (r.spawnT <= 0 && alive < 8 + Math.min(r.tier, 8)) {
        r.spawnT = 0.5;
        const a = Math.random() * Math.PI * 2, rr = 20 + Math.random() * 10;
        const elite = Math.random() < 0.1;
        const def = elite ? RIFT_POOL[RIFT_POOL.length - 1 - Math.floor(Math.random() * 12)] : RIFT_POOL[Math.floor(Math.random() * 30)];
        const e = g.spawnEnemy(def.id, r.level, { x: Math.cos(a) * rr, z: Math.sin(a) * rr, elite, rift: true, aggro: true, hpMul: r.hpMul, affixes: elite ? [pick(Math.random, ELITE_AFFIXES).id] : [] });
        g.particles.burst(e.pos.x, 0.5, e.pos.z, new THREE.Color(ELEMENT_STYLE[e.element].color), 12, { speed: 5, life: 0.5, kind: 2 });
      }
    } else if (!r.guardian) {
      for (const e of g.enemies) if (!e.dead) g.removeEnemy(e);
      const def = RIFT_POOL[RIFT_POOL.length - 1 - Math.floor(Math.random() * 6)];
      r.guardian = g.spawnEnemy(def.id, r.level + 1, { x: 0, z: -12, boss: true, bossName: `Rift Guardian · ${def.name}`, rift: true, aggro: true, hpMul: r.hpMul * 0.55 });
      g.ui.banner('Rift Guardian', `${def.name} · ${def.element}`);
      g.shake(0.6);
    } else if (r.guardian.dead) {
      this.completeRift();
    }
  }

  riftKill(e) {
    const r = this.rift;
    if (!r || r.progress >= 100) return;
    r.progress = Math.min(100, r.progress + (e.elite ? 11 : 3.4));
  }

  completeRift() {
    const g = this.g, r = this.rift;
    r.done = true;
    const inTime = r.time <= r.limit;
    const n = 3 + Math.floor(r.tier / 3);
    for (let i = 0; i < n; i++) g.dropItem(Math.cos(i) * 3, Math.sin(i) * 3, g.loot.make(r.level + 1, { min: 2, bonus: 0.4 + r.tier * 0.05 + (r.burden ? 0.25 : 0) }));
    g.dropGold(0, 0, 40 + r.level * 12, 12);
    g.dropShards(0, 0, 6 + r.tier, 'Arcane');
    const notes = 10 + r.tier * 2;
    g.profile.notes += notes;
    g.profile.stats.rifts++;
    if (inTime && r.tier > g.profile.riftTier) g.profile.riftTier = r.tier;
    g.bountyEvent('rift', 1);
    g.ui.banner(inTime ? `Rift Tier ${r.tier} cleared!` : 'Rift cleared (over time)', `+${notes} Golden Notes${inTime ? ` · Tier ${r.tier + 1} unlocked` : ''}`);
    g.audio.levelUp();
    const exit = new THREE.Group();
    const ring = new THREE.Mesh(new THREE.TorusGeometry(2.2, 0.28, 8, 28), L('#fff', { emissive: '#62c8ff', emissiveIntensity: 0.8 }));
    ring.position.y = 2.6;
    exit.add(ring);
    exit.position.set(0, 0, 6);
    g.scene.add(exit);
    r.exit = exit;
    g.save();
  }

  exitRift() {
    const g = this.g, r = this.rift;
    if (!r) return;
    if (r.exit) g.scene.remove(r.exit);
    for (const e of g.enemies) if (!e.dead) g.removeEnemy(e);
    g.enemies = [];
    g.combat.reset();
    g.decals.clear();
    g.collectAllDrops();
    this.rift = null;
    g.world.setRift(false);
    g.player.pos.copy(r.returnPos);
    g.player.pos.y = g.world.height(r.returnPos.x, r.returnPos.z);
    g.sheep.pos.copy(g.player.pos);
    g.world.warm(g.player.pos.x, g.player.pos.z);
    g.audio.setScore(g.scoreForPosition());
  }
}

export { makeBeam };
