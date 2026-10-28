// World content: camps, chests, pylons, lost sheet music, music-key shrines,
// biome Maestros (world bosses), Elite Chorus events and Resonance Rifts.

import * as THREE from 'three';
import { BIOMES, HUB, WORLD_SEED, RIFT_POOL, BURDENS, ELITE_AFFIXES, RIFT_STYLE, ELEMENT_STYLE } from './design.js';
import { Enemy } from './entities.js';
import { mulberry32, pick, clamp } from './util.js';
import { makeBeam } from './fx.js';
import { planExploration, biomeWorkflow, OW_RULES } from './openworld.js';

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
      const wf = biomeWorkflow(b);
      add({ type: 'boss', id: 'boss_' + b.id, biome: bi, x: b.cx - ax * 30, z: b.cz - az * 30, bx: b.cx - ax * 17, bz: b.cz - az * 17, name: b.bossName, cdUntil: 0 });
      // Gate camps (Nikki/Genshin first-pressure ring just past the safe hub).
      [[72, 0], [88, 0.07], [105, -0.08]].forEach(([r, da], k) => {
        const a = b.angle + da;
        add({
          type: 'camp', biome: bi, x: Math.cos(a) * r, z: Math.sin(a) * r,
          active: false, clearedAt: -999, enemies: [], starter: true, id: `camp_gate_${b.id}_${k}`,
        });
      });
      // Reveal overlook anchored on the workflow vista point (Genshin Stone-Gate reveal).
      add({
        type: 'overlook', id: `vista_${b.id}`, biome: bi,
        x: wf.reveal.x, z: wf.reveal.z,
        name: `${b.name.split('—')[0].trim()} Reveal`,
        vistaLine: wf.vistaLine, gateFeeling: wf.gateFeeling, workflow: 'vista',
      });
      [[240, -0.18], [520, 0.2]].forEach(([r, da], k) => {
        const s = spot(b.angle + da, 0.12, r - 30, r + 30, 30);
        if (s) add({ type: 'pylon', id: `pylon_${b.id}_${k}`, biome: bi, ...s, name: `${b.name.split('—')[0].trim()} Pylon ${k + 1}` });
      });
      const rs = spot(b.angle + 0.32, 0.1, 300, 380);
      if (rs) add({ type: 'rift', id: 'rift_' + b.id, biome: bi, ...rs, name: 'Rift Gate' });
      // Density-budgeted exploration from the anime OW workflow (camps/chests/shrines/sheets + chimes/photos).
      const planned = planExploration(b, bi, rng, this.pois.slice());
      for (const p of planned.pois) add(p);
    });
    this.workflowRules = OW_RULES;
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
    } else if (p.type === 'overlook') {
      // Vista platform — Genshin-style reveal perch with a framed view toward the landmark.
      const deck = new THREE.Mesh(new THREE.CylinderGeometry(3.2, 3.6, 0.45, 10), L('#efe6d8'));
      deck.position.y = 0.25;
      const rail = new THREE.Mesh(new THREE.TorusGeometry(3.1, 0.08, 6, 24), L('#d9bc72', { emissive: '#d9a84a', emissiveIntensity: 0.25 }));
      rail.rotation.x = Math.PI / 2; rail.position.y = 1.1;
      p.clefMat = L('#ffffff', { emissive: '#ffd978', emissiveIntensity: 0.7 });
      const lens = new THREE.Mesh(new THREE.TorusGeometry(0.7, 0.12, 8, 20), p.clefMat);
      lens.position.y = 2.2;
      p.spin = lens;
      grp.add(deck, rail, lens);
    } else if (p.type === 'photo') {
      // Nikki-style "whim frame" — a floating picture frame that pulses on the beat.
      const frame = new THREE.Mesh(new THREE.BoxGeometry(2.4, 1.7, 0.12), L('#f7f0ff', { emissive: '#c8b6ef', emissiveIntensity: 0.35 }));
      frame.position.y = 2.1;
      const pane = new THREE.Mesh(new THREE.PlaneGeometry(1.9, 1.2), new THREE.MeshBasicMaterial({ color: '#9fe6ff', transparent: true, opacity: 0.35, side: THREE.DoubleSide }));
      pane.position.y = 2.1; pane.position.z = 0.08;
      p.spin = frame;
      grp.add(frame, pane);
    } else if (p.type === 'chime') {
      for (let k = 0; k < 3; k++) {
        const a = (k / 3) * Math.PI * 2;
        const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 2.2 + k * 0.3, 5), L('#5f8f5a'));
        pole.position.set(Math.cos(a) * 1.1, 1.1 + k * 0.1, Math.sin(a) * 1.1);
        const bell = new THREE.Mesh(new THREE.ConeGeometry(0.32, 0.5, 8, 1, true), L('#9fe6ff', { emissive: '#62c8ff', emissiveIntensity: 0.55, side: THREE.DoubleSide }));
        bell.position.set(Math.cos(a) * 1.1, 2.3 + k * 0.15, Math.sin(a) * 1.1);
        grp.add(pole, bell);
      }
      p.spin = grp.children[grp.children.length - 1];
    } else if (p.type === 'musicgate') {
      // Phrase Bridge — two posts + a sealed ribbon until answered on the beat.
      const plank = new THREE.Mesh(new THREE.BoxGeometry(7.2, 0.28, 2.4), L('#c9b48a'));
      plank.position.y = 0.2;
      p.plank = plank;
      for (const s of [-1, 1]) {
        const post = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.35, 3.2, 8), L('#d8d0e4'));
        post.position.set(s * 3.4, 1.6, 0);
        grp.add(post);
      }
      p.clefMat = L('#ffffff', { emissive: '#62c8ff', emissiveIntensity: 0.7, transparent: true, opacity: 0.95 });
      const ribbon = new THREE.Mesh(new THREE.BoxGeometry(6.4, 1.6, 0.12), p.clefMat);
      ribbon.position.y = 1.6;
      p.barrier = ribbon;
      p.spin = ribbon;
      grp.add(plank, ribbon);
      grp.rotation.y = Math.atan2(-p.x, -p.z) + Math.PI / 2;
    } else if (p.type === 'cleanse') {
      // Dissonant blot — sheep Harmonize clears it.
      p.blotMat = new THREE.MeshBasicMaterial({ color: '#6b3a78', transparent: true, opacity: 0.55, depthWrite: false });
      const blot = new THREE.Mesh(new THREE.CircleGeometry(2.8, 24), p.blotMat);
      blot.rotation.x = -Math.PI / 2;
      blot.position.y = 0.08;
      const thorn = new THREE.Mesh(new THREE.IcosahedronGeometry(0.7, 0), L('#8a4a9a', { emissive: '#ff5470', emissiveIntensity: 0.45 }));
      thorn.position.y = 0.9;
      p.spin = thorn;
      p.blot = blot;
      grp.add(blot, thorn);
    } else if (p.type === 'ariagate') {
      // Wardrobe / Aria veil — needs an equipped Opus aria (or shoes slot gear).
      const arch = new THREE.Mesh(new THREE.TorusGeometry(2.4, 0.22, 8, 28, Math.PI), L('#e8dff8', { emissive: '#c8b6ef', emissiveIntensity: 0.4 }));
      arch.rotation.z = Math.PI; arch.position.y = 0.2;
      p.veilMat = new THREE.MeshBasicMaterial({ color: '#b89cff', transparent: true, opacity: 0.45, side: THREE.DoubleSide });
      const veil = new THREE.Mesh(new THREE.PlaneGeometry(4.2, 3.4), p.veilMat);
      veil.position.y = 1.8;
      p.barrier = veil;
      p.spin = arch;
      grp.add(arch, veil);
      grp.rotation.y = Math.atan2(-p.x, -p.z);
    } else return;
    p.mesh = grp;
    g.world.root.add(grp);
  }

  // ------------------------------------------------------------ per frame
  update(dt) {
    const g = this.g, P = g.player;
    if (this.rift) return this.updateRift(dt);
    for (const p of this.pois) {
      if (p.spin && p.type !== 'chime' && p.type !== 'musicgate' && p.type !== 'ariagate') {
        p.spin.rotation.y += dt * 1.5;
        const baseY = p.type === 'pylon' ? 3 : p.type === 'sheet' ? 1.4 : p.type === 'rift' ? 2.6 : p.type === 'overlook' ? 2.2 : p.type === 'photo' ? 2.1 : p.type === 'cleanse' ? 0.9 : 2;
        p.spin.position.y = baseY + Math.sin(g.time * 2 + p.x) * 0.15;
      } else if (p.spin && (p.type === 'musicgate' || p.type === 'ariagate') && !p.open) {
        p.spin.rotation.y += dt * 0.8;
      }
      if (p.type === 'cleanse' && !p.cleared && p.blotMat) {
        p.blotMat.opacity = 0.4 + Math.sin(g.time * 3 + p.x) * 0.15;
      }
    }
    this._acc += dt;
    if (this._acc < 0.25) return;
    this._acc = 0;
    for (const p of this.pois) {
      const d = Math.hypot(p.x - P.pos.x, p.z - P.pos.z);
      if (p.type === 'camp') {
        const ready = g.time - p.clearedAt > (p.starter ? 70 : 150);
        const spawnR = p.starter ? 78 : 60;
        const despawnR = p.starter ? 140 : 115;
        if (!p.active && ready && d < spawnR && !P.dead) this.spawnCamp(p);
        else if (p.active && d > despawnR) this.despawnCamp(p);
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
      } else if (p.type === 'overlook' && !p.revealed && d < 10 && !P.dead) {
        // Auto-reveal on approach — Genshin "veil falls away" moment.
        this.viewOverlook(p, true);
      } else if (p.type === 'photo' && d < 3.2 && !P.dead && !p.autoDone && !p.challenge) {
        this.snapPhoto(p, true);
      } else if (p.type === 'chime' && d < 3.2 && !P.dead && !p.autoDone) {
        this.ringChimes(p, true);
      } else if (p.type === 'musicgate' && !p.open && d < 5.5) {
        // Soft block: push Melusina back while the ribbon is sealed.
        this._pushFromGate(p, P);
      } else if (p.type === 'ariagate' && !p.open && d < 3.2) {
        this._pushFromGate(p, P);
      }
    }
    this.updateEvent();
  }

  _pushFromGate(p, P) {
    const dx = P.pos.x - p.x, dz = P.pos.z - p.z, d = Math.hypot(dx, dz) || 1;
    const min = p.type === 'musicgate' ? 4.2 : 2.6;
    if (d < min) {
      P.pos.x = p.x + (dx / d) * min;
      P.pos.z = p.z + (dz / d) * min;
    }
  }

  nearCleanse(x, z, r) {
    return this.pois.some((p) => p.type === 'cleanse' && !p.cleared && Math.hypot(p.x - x, p.z - z) < r);
  }

  cleanseNear(x, z, r) {
    for (const p of this.pois) {
      if (p.type === 'cleanse' && !p.cleared && Math.hypot(p.x - x, p.z - z) < r) this.finishCleanse(p);
    }
  }

  viewOverlook(p, soft = false) {
    if (p.revealed && soft) return;
    const g = this.g;
    p.revealed = true;
    g.profile.vistas = g.profile.vistas || [];
    if (p.id && !g.profile.vistas.includes(p.id)) {
      g.profile.vistas.push(p.id);
      g.profile.notes += 2;
      g.progress.addXp(40);
    }
    const title = p.name || 'Overlook';
    const sub = p.vistaLine || p.gateFeeling || 'A new motif opens across the wilds.';
    g.ui.banner(title, sub);
    if (!soft) g.audio.levelUp();
    g.world.pulse(p.x, p.z, 1.8, true);
    g.particles.burst(p.x, p.y + 2, p.z, new THREE.Color('#ffd978'), 18, { speed: 5, life: 1.1, kind: 1, gravity: -1 });
    g.save();
  }

  snapPhoto(p, soft = false) {
    if (p.autoDone && soft) return;
    const g = this.g, P = g.player;
    // Challenge frames need Melusina facing the prompt angle (Nikki whim pose).
    if (p.challenge && !soft && typeof p.aimAngle === 'number') {
      const err = Math.abs(((P.facing - p.aimAngle + Math.PI * 3) % (Math.PI * 2)) - Math.PI);
      if (err > 0.55) {
        g.ui.toast(`${p.aimLabel || 'Face the prompt'} — turn toward the ◇`, 'lavender');
        g.overlay.text(p.x, p.y + 2.6, p.z, '◇', '#c8b6ef', 28, { life: 0.9, rise: 0.2 });
        return;
      }
    }
    p.autoDone = true;
    g.profile.photos = g.profile.photos || [];
    const id = p.id || `photo_${p.biome}_${Math.round(p.x)}_${Math.round(p.z)}`;
    if (!g.profile.photos.includes(id)) {
      g.profile.photos.push(id);
      const bonus = p.challenge ? 2 : 1;
      g.profile.notes += bonus;
      g.ui.toast(p.challenge ? `Whim challenge framed — Golden Notes +${bonus}` : 'Whim Frame captured — Golden Note +1', 'aqua');
      g.progress.addXp(p.challenge ? 40 : 25);
    } else if (!soft) g.ui.toast('Already framed this whim', 'lavender');
    g.world.pulse(p.x, p.z, 1.1, true);
    g.particles.burst(p.x, p.y + 2, p.z, new THREE.Color('#c8b6ef'), 16, { speed: 4, life: 0.8, kind: 1 });
    g.audio.ui();
    g.save();
  }

  openMusicGate(p) {
    const g = this.g;
    if (p.open) return;
    if (g.enemies.some((e) => !e.dead && e.aggro)) { g.ui.toast('Clear the dissonance before the bridge will listen'); return; }
    const gr = g.rhythm.judge(performance.now());
    if (gr.grade === 'Miss' || gr.grade === 'Good') {
      g.ui.toast('Answer on the beat — Great or Perfect opens the Phrase Bridge', 'soft');
      g.audio.fail();
      g.ui.gradeFlash(gr.grade, gr.err);
      return;
    }
    p.open = true;
    if (p.barrier) {
      p.barrier.visible = false;
    }
    g.profile.gates = g.profile.gates || [];
    if (p.id && !g.profile.gates.includes(p.id)) {
      g.profile.gates.push(p.id);
      g.profile.notes += 2;
      g.progress.addXp(35);
    }
    g.ui.banner('Phrase Bridge opens', 'The ribbon dissolves on your answer');
    g.world.pulse(p.x, p.z, 1.6, true);
    g.particles.burst(p.x, p.y + 1.6, p.z, new THREE.Color('#62c8ff'), 22, { speed: 6, life: 0.9, kind: 1 });
    g.audio.levelUp();
    g.save();
  }

  cleanseSpot(p) {
    if (p.cleared) return;
    const g = this.g;
    // Pull sheep in and force a Harmonize pulse.
    g.sheep.pos.set(p.x + 1.2, p.y, p.z + 1.2);
    g.sheep.harmonize(true);
  }

  finishCleanse(p) {
    if (p.cleared) return;
    const g = this.g;
    p.cleared = true;
    if (p.blot) p.blot.visible = false;
    if (p.spin) p.spin.visible = false;
    g.profile.cleanses = g.profile.cleanses || [];
    if (p.id && !g.profile.cleanses.includes(p.id)) {
      g.profile.cleanses.push(p.id);
      g.profile.notes += 1;
      g.progress.addXp(30);
      g.player.sp = Math.min(g.player.stats.spMax, g.player.sp + 2);
    }
    g.ui.toast('Dissonance cleansed — Sheep Harmonize ♪', 'aqua');
    g.world.pulse(p.x, p.z, 1.4, true);
    g.save();
  }

  tryAriaGate(p) {
    const g = this.g, P = g.player, pr = g.profile;
    if (p.open) return;
    const hasAria = P.stats.arias && P.stats.arias.size > 0;
    const outfit = ['shoes', 'gown', 'gloves', 'head'].find((s) => pr.equipment?.[s]);
    if (!hasAria && !outfit) {
      g.ui.toast('Wardrobe gate — equip an outfit piece or Opus Aria to part the veil', 'lavender');
      return;
    }
    p.open = true;
    if (p.barrier) p.barrier.visible = false;
    if (p.veilMat) p.veilMat.opacity = 0.08;
    g.profile.gates = g.profile.gates || [];
    if (p.id && !g.profile.gates.includes(p.id)) {
      g.profile.gates.push(p.id);
      g.profile.notes += 3;
      g.progress.addXp(45);
    }
    const why = hasAria ? 'Your Aria parts the veil' : `Your ${outfit} carries the cadence through`;
    g.ui.banner('Aria Veil opens', why);
    g.world.pulse(p.x, p.z, 1.5, true);
    g.particles.burst(p.x, p.y + 1.8, p.z, new THREE.Color('#ffd978'), 20, { speed: 5, life: 1, kind: 3 });
    g.audio.levelUp();
    g.save();
  }

  ringChimes(p, soft = false) {
    if (p.autoDone && soft) return;
    const g = this.g;
    p.autoDone = true;
    g.audio.chime(Math.floor(Math.random() * 8));
    g.particles.burst(p.x, p.y + 2.2, p.z, new THREE.Color('#9fe6ff'), 12, { speed: 3, life: 0.9, kind: 1, gravity: -2 });
    if (!soft) {
      g.player.sp = Math.min(g.player.stats.spMax, g.player.sp + 1);
      g.ui.toast('Chimes restore 1 Harmony ◆', 'aqua');
    }
    g.world.pulse(p.x, p.z, 0.9);
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
    const lvl = p.starter ? Math.max(1, Math.min(this.enemyLevel(p), 3 + p.biome)) : this.enemyLevel(p);
    const elite = !p.starter && rng() < 0.18 + p.biome * 0.02;
    const n = p.starter ? 3 + Math.floor(rng() * 2) : 3 + Math.floor(rng() * 3) + (p.biome >= 2 ? 1 : 0);
    for (let i = 0; i < n; i++) {
      const a = (i / n) * Math.PI * 2 + rng(), r = 2 + rng() * 4;
      const isElite = elite && i === 0;
      const def = isElite ? pick(rng, b.elites) : pick(rng, b.trash);
      const affixes = isElite ? [pick(rng, ELITE_AFFIXES).id] : [];
      if (isElite && lvl >= 15 && rng() < 0.5) affixes.push(pick(rng, ELITE_AFFIXES.filter((x) => !affixes.includes(x.id))).id);
      // Starter packs wake hungry: aggro as soon as the player leaves the gate.
      p.enemies.push(g.spawnEnemy(def.id, lvl, {
        x: p.x + Math.cos(a) * r, z: p.z + Math.sin(a) * r,
        elite: isElite, affixes, camp: p, aggro: !!p.starter && i === 0,
      }));
    }
    if (p.starter && !this._starterToast) {
      this._starterToast = true;
      g.ui.toast('Melody slimes ahead — dodge the red rings on the beat', 'rose');
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
