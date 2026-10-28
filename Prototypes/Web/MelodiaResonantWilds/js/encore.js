// Encore variants — one gauge, ten ultimate identities.
// Selected via the Encore button (cycle when not ready / Alt+T / hold).
// Cast keeps the free-Perfect window + camera juice; each id owns its verb.

import * as THREE from 'three';
import { ARIAS, RULES, SKILL_BY_ID } from './design.js';
import { clamp } from './util.js';

const _c = new THREE.Color();

/** Ordered as pitched: combat → companion/wardrobe → world. */
export const ENCORE_VARIANTS = Object.freeze([
  {
    id: 'cascade',
    short: 'CASCADE',
    name: 'Crescendo Cascade',
    color: '#ffae45',
    tag: 'Combat',
    blurb: 'Radial hits every beat for a bar; Perfects extend the cascade.',
  },
  {
    id: 'subject',
    short: 'FUGUE',
    name: 'Subject & Answer',
    color: '#9a7bf0',
    tag: 'Combat',
    blurb: 'Mark three foes, then mirror your phrase onto all of them.',
  },
  {
    id: 'cadenza',
    short: 'BREAK',
    name: 'Break Cadenza',
    color: '#ff5470',
    tag: 'Combat',
    blurb: 'Shatter toughness; Perfects guarantee BREAK for a short window.',
  },
  {
    id: 'reprise',
    short: 'REPRISE',
    name: 'Encore Reprise',
    color: '#ffd978',
    tag: 'Combat',
    blurb: 'Replay your last four Perfect hits as ghost notes.',
  },
  {
    id: 'duet',
    short: 'DUET',
    name: 'Choral Duet',
    color: '#62c8ff',
    tag: 'Companion',
    blurb: 'You and Sheep Harmonize as one — heal, cleanse, Tide pulse.',
  },
  {
    id: 'veil',
    short: 'VEIL',
    name: 'Aria Veil Step',
    color: '#e8dff8',
    tag: 'Wardrobe',
    blurb: 'Float on the beat, then land as a shockwave.',
  },
  {
    id: 'overture',
    short: 'OVERTURE',
    name: 'Wardrobe Overture',
    color: '#f3b6cf',
    tag: 'Wardrobe',
    blurb: 'Concert set: all Opus Aria passives live for eight beats.',
  },
  {
    id: 'modulation',
    short: 'KEY',
    name: 'Key Modulation',
    color: '#8ff0b4',
    tag: 'World',
    blurb: 'Local key flips to yours — bridges soften, blots shrink.',
  },
  {
    id: 'dew',
    short: 'DEW',
    name: 'Resonance Dew Bloom',
    color: '#9fe6ff',
    tag: 'World',
    blurb: 'Spent Dew detonates as a cymatic damage field.',
  },
  {
    id: 'recital',
    short: 'RECITAL',
    name: 'Rift Recital',
    color: '#c690ff',
    tag: 'Rift',
    blurb: 'Inside a Rift: bank a mid-run Echo Phrase buff.',
  },
]);

export const ENCORE_BY_ID = Object.fromEntries(ENCORE_VARIANTS.map((v) => [v.id, v]));

export class EncoreSystem {
  constructor(game) {
    this.g = game;
    const id = game.profile.settings.encoreVariant;
    this.selected = ENCORE_BY_ID[id] ? id : 'cascade';
    this.active = null;
    this.lastPerfects = [];
    this._savedArias = null;
    this._modScore = null;
    this._bloomBoost = 0;
    this._veilY = 0;
  }

  get variant() { return ENCORE_BY_ID[this.selected] || ENCORE_VARIANTS[0]; }

  cycle(dir = 1) {
    const i = ENCORE_VARIANTS.findIndex((v) => v.id === this.selected);
    const n = (i + dir + ENCORE_VARIANTS.length) % ENCORE_VARIANTS.length;
    this.selected = ENCORE_VARIANTS[n].id;
    this.g.profile.settings.encoreVariant = this.selected;
    const v = this.variant;
    this.g.ui.toast(`${v.name} · ${v.blurb}`, 'gold');
    this.g.audio.ui();
    this.g.audio.encoreSelect(v.id);
    return v;
  }

  /** Record Perfect hits for Encore Reprise. */
  notePerfect(hits, coef = 1, element = null) {
    if (!hits) return;
    const g = this.g, P = g.player;
    const el = element || P.stats.basicElement;
    const list = g.combat.enemiesIn('circle', { x: P.pos.x, z: P.pos.z, r: 14 });
    for (const e of list.slice(0, 3)) {
      this.lastPerfects.push({
        x: e.pos.x, z: e.pos.z, y: e.pos.y,
        coef, element: el, id: e.id || e.name,
      });
    }
    if (!list.length) {
      this.lastPerfects.push({
        x: P.pos.x + Math.sin(P.facing) * 3,
        z: P.pos.z + Math.cos(P.facing) * 3,
        y: P.pos.y, coef, element: el,
      });
    }
    while (this.lastPerfects.length > 4) this.lastPerfects.shift();
  }

  cast() {
    const g = this.g;
    if (!g.started || g.paused || g.player.dead) return false;
    const R = g.rhythm;
    if (R.encore < R.encoreMax || this.active) return false;
    const v = this.variant;
    if (v.id === 'recital' && !g.activities.rift) {
      g.ui.toast('Rift Recital needs an active Resonance Rift', 'soft');
      g.audio.fail();
      return false;
    }
    if (v.id === 'dew' && !(g.profile.dews || []).length) {
      g.ui.toast('Collect Resonance Dew at destinations first', 'soft');
      g.audio.fail();
      return false;
    }
    if (v.id === 'cascade' && R.crescendo < 80) {
      // Soft gate: still castable, but toast hints at ff fantasy.
      g.ui.toast('Cascade sings louder at ff…', 'soft');
    }

    R.encore = 0;
    const bars = v.id === 'overture' || v.id === 'modulation' ? 2 : v.id === 'veil' ? 1 : 2;
    R.encoreUntil = g.beatIndex + g.audio.meter * bars;
    g.player.invulnUntil = Math.max(g.player.invulnUntil, g.time + 0.55);
    this._bloomBoost = 1;
    if (g.postfx?.bloom) {
      g.postfx.bloom.strength = 0.95;
      g.postfx.bloom.threshold = 0.72;
    }
    g.audio.setIntensity(2);
    g.shake(0.55);
    g.audio.encoreVariant(v.id);

    switch (v.id) {
      case 'cascade': this._startCascade(v); break;
      case 'subject': this._startSubject(v); break;
      case 'cadenza': this._startCadenza(v); break;
      case 'reprise': this._startReprise(v); break;
      case 'duet': this._startDuet(v); break;
      case 'veil': this._startVeil(v); break;
      case 'overture': this._startOverture(v); break;
      case 'modulation': this._startModulation(v); break;
      case 'dew': this._startDew(v); break;
      case 'recital': this._startRecital(v); break;
      default: this._startCascade(v); break;
    }
    return true;
  }

  onBeat(beat) {
    const a = this.active;
    if (!a) return;
    const g = this.g;
    if (g.beatIndex > a.until) {
      this._end();
      return;
    }
    switch (a.id) {
      case 'cascade': this._beatCascade(beat, a); break;
      case 'subject': this._beatSubject(beat, a); break;
      case 'cadenza': this._beatCadenza(beat, a); break;
      case 'reprise': this._beatReprise(beat, a); break;
      case 'veil': this._beatVeil(beat, a); break;
      case 'duet':
      case 'overture':
      case 'modulation':
      case 'dew':
      case 'recital':
        if (beat.inBar === 0) this._pulseRing(a.color, 6.5, 0.35);
        break;
      default: break;
    }
  }

  onPerfect() {
    const a = this.active;
    if (!a) return;
    if (a.id === 'cascade') {
      a.until = Math.min(a.until + 1, this.g.beatIndex + this.g.audio.meter * 3);
      this.g.rhythm.encoreUntil = Math.max(this.g.rhythm.encoreUntil, a.until);
      this._spark(a.color, 10, 0.4);
      this.g.overlay.text(this.g.player.pos.x, this.g.player.pos.y + 2.8, this.g.player.pos.z, '+1 beat', a.color, 13, { life: 0.55 });
    }
    if (a.id === 'cadenza') {
      a.perfectBreak = true;
    }
  }

  /** Cadenza: Perfect hits force BREAK toughness. */
  perfectBreakActive() {
    return this.active?.id === 'cadenza' && this.active.perfectBreak;
  }

  update(dt) {
    if (this._bloomBoost > 0 && this.g.postfx?.bloom) {
      this._bloomBoost = Math.max(0, this._bloomBoost - dt * 0.55);
      const t = this._bloomBoost;
      this.g.postfx.bloom.strength = 0.55 + t * 0.45;
      this.g.postfx.bloom.threshold = 0.82 - t * 0.12;
    }
    if (this.active?.id === 'veil') {
      const P = this.g.player;
      const k = clamp((this.active.landBeat - this.g.beatIndex) / Math.max(1, this.active.floatBeats), 0, 1);
      this._veilY = Math.sin((1 - k) * Math.PI) * 2.4;
      P.pos.y += this._veilY * 0.02; // soft lift bias; height snap still owns ground
      if (P.m?.group) P.m.group.position.y += this._veilY;
    }
    if (this.active?.id === 'modulation') {
      // Shrink nearby dissonant blot meshes for the key window.
      for (const p of this.g.activities.pois) {
        if (p.type !== 'cleanse' || p.cleansed || !p.mesh) continue;
        const d = Math.hypot(p.x - this.g.player.pos.x, p.z - this.g.player.pos.z);
        if (d < 48) p.mesh.scale.setScalar(0.55 + Math.sin(this.g.time * 4) * 0.05);
      }
    }
  }

  // ------------------------------------------------------------------ starts
  _banner(v, sub) {
    this.g.ui.banner(v.name.toUpperCase(), sub || v.blurb);
    this.g.overlay.text(this.g.player.pos.x, this.g.player.pos.y + 3.2, this.g.player.pos.z, v.short, v.color, 22, { life: 1.1 });
  }

  _burst(color, n = 48, speed = 12) {
    const P = this.g.player;
    this.g.particles.burst(P.pos.x, P.pos.y + 1.1, P.pos.z, _c.set(color), n, { speed, life: 0.9, kind: 2, size: 1.15 });
    this.g.world.pulse(P.pos.x, P.pos.z, 2.2, true);
  }

  _pulseRing(color, r = 8, alpha = 0.5) {
    const P = this.g.player;
    this.g.decals.spawn('ring', P.pos.x, P.pos.z, { r, inner: r * 0.72, flash: true, dur: 0.45, color, alpha });
  }

  _spark(color, n = 16, size = 0.7) {
    const P = this.g.player;
    this.g.particles.burst(P.pos.x, P.pos.y + 1.4, P.pos.z, _c.set(color), n, { speed: 7, life: 0.5, kind: 3, size });
  }

  _startCascade(v) {
    const g = this.g;
    const until = g.beatIndex + g.audio.meter;
    this.active = { id: 'cascade', until, color: v.color, hits: 0 };
    g.rhythm.encoreUntil = until;
    this._banner(v, 'Every beat is a Perfect wave — extend with Perfects');
    this._burst(v.color, 56, 14);
    this._pulseRing(v.color, 9);
    // Opening hit.
    this._cascadeHit(1.35);
  }

  _startSubject(v) {
    const g = this.g, P = g.player;
    const marks = g.combat.enemiesIn('circle', { x: P.pos.x, z: P.pos.z, r: 16 })
      .filter((e) => !e.dead)
      .sort((a, b) => Math.hypot(a.pos.x - P.pos.x, a.pos.z - P.pos.z) - Math.hypot(b.pos.x - P.pos.x, b.pos.z - P.pos.z))
      .slice(0, 3);
    for (const e of marks) {
      e._fugueMark = true;
      g.decals.spawn('ring', e.pos.x, e.pos.z, { r: 1.8 * e.scale, inner: 1.3 * e.scale, flash: true, dur: g.audio.spb * g.audio.meter, color: v.color });
      g.overlay.text(e.pos.x, e.pos.y + 2.2 * e.scale, e.pos.z, '♪', v.color, 18, { life: 1.2 });
    }
    this.active = {
      id: 'subject',
      until: g.beatIndex + g.audio.meter * 2,
      color: v.color,
      marks,
      phase: 'subject',
      answerAt: g.beatIndex + g.audio.meter,
    };
    this._banner(v, marks.length ? `Subject locked · ${marks.length} voices` : 'No voices nearby — hold the phrase');
    this._burst(v.color, 40, 10);
    this._pulseRing(v.color, 7);
  }

  _startCadenza(v) {
    const g = this.g, P = g.player;
    const list = g.combat.enemiesIn('circle', { x: P.pos.x, z: P.pos.z, r: 11 });
    g.combat.hitAll(list, RULES.ultimate.damage_mult * 0.85, {
      mult: RULES.rhythm.max_combat_multiplier, element: P.stats.basicElement, tough: 14, perfect: true,
    });
    for (const e of list) {
      if (e.maxTough && !e.broken) {
        e.tough = 0;
        g.combat.breakEnemy(e);
      }
    }
    this.active = {
      id: 'cadenza',
      until: g.beatIndex + g.audio.meter * 2,
      color: v.color,
      perfectBreak: true,
    };
    this._banner(v, 'Perfects guarantee BREAK');
    this._burst(v.color, 64, 16);
    this._pulseRing('#ffffff', 10);
    g.shake(0.85);
  }

  _startReprise(v) {
    const g = this.g;
    const ghosts = this.lastPerfects.slice(-4);
    this.active = {
      id: 'reprise',
      until: g.beatIndex + Math.max(4, ghosts.length + 1),
      color: v.color,
      ghosts: ghosts.map((h) => ({ ...h })),
      i: 0,
    };
    this._banner(v, ghosts.length ? `Replaying ${ghosts.length} Perfects` : 'No Perfects banked — opening flourish');
    this._burst(v.color, 36, 11);
    this._pulseRing(v.color, 6);
    if (!ghosts.length) {
      g.combat.hitAll(g.combat.enemiesIn('circle', { x: g.player.pos.x, z: g.player.pos.z, r: 8 }), 2.2, {
        mult: RULES.rhythm.max_combat_multiplier, element: g.player.stats.basicElement, tough: 2, perfect: true,
      });
    }
  }

  _startDuet(v) {
    const g = this.g, P = g.player;
    this.active = { id: 'duet', until: g.beatIndex + g.audio.meter, color: v.color };
    P.heal(P.stats.maxHp * 0.12);
    P.sp = Math.min(P.stats.spMax, P.sp + 2);
    P.cleanse();
    g.sheep.harmonize(true);
    // Extra Tide pulse tinted by first equipped Aria element fantasy.
    const p = { x: P.pos.x, z: P.pos.z, r: 8 };
    g.combat.hitAll(g.combat.enemiesIn('circle', p), 2.4, {
      mult: RULES.rhythm.max_combat_multiplier, element: 'Tide', tough: 3, perfect: true,
    });
    g.combat.flash('circle', p.x, p.z, p, v.color);
    g.activities.cleanseNear(P.pos.x, P.pos.z, 10);
    this._banner(v, 'Harmonize duet');
    this._burst(v.color, 52, 12);
    // Sheep + Melusina twin rings.
    g.decals.spawn('ring', g.sheep.pos.x, g.sheep.pos.z, { r: 4.5, inner: 3.6, flash: true, dur: 0.7, color: '#8fd8ff' });
    this._pulseRing(v.color, 8);
  }

  _startVeil(v) {
    const g = this.g, P = g.player;
    const floatBeats = Math.max(2, Math.floor(g.audio.meter / 2));
    this.active = {
      id: 'veil',
      until: g.beatIndex + floatBeats + 1,
      color: v.color,
      floatBeats,
      landBeat: g.beatIndex + floatBeats,
      landed: false,
    };
    P.invulnUntil = Math.max(P.invulnUntil, g.time + g.audio.spb * (floatBeats + 0.5));
    this._banner(v, 'Float… then land');
    this._burst(v.color, 28, 8);
    this._pulseRing(v.color, 4);
    // Soft lift.
    if (typeof P.startDash === 'function') P.startDash(P.facing, 0.2, 0.05, false);
  }

  _startOverture(v) {
    const g = this.g, P = g.player;
    this._savedArias = new Set(P.stats.arias);
    for (const a of ARIAS) P.stats.arias.add(a.id);
    this.active = { id: 'overture', until: g.beatIndex + 8, color: v.color };
    g.rhythm.encoreUntil = this.active.until;
    this._banner(v, 'All Arias singing');
    this._burst(v.color, 44, 10);
    // Orbit of rarity sparks.
    for (let i = 0; i < 12; i++) {
      const a = (i / 12) * Math.PI * 2;
      g.particles.emit(P.pos.x + Math.cos(a) * 2, P.pos.y + 1.2, P.pos.z + Math.sin(a) * 2, _c.set(v.color), {
        dir: { x: Math.cos(a), y: 0.4, z: Math.sin(a) }, speed: 5, life: 0.8, kind: 3, size: 0.85, gravity: 0,
      });
    }
    this._pulseRing('#ffd978', 7);
  }

  _startModulation(v) {
    const g = this.g;
    this._modScore = g.scoreForPosition();
    // Flip to a bright related score feel: raise intensity + pad shimmer via encore mix.
    g.audio.setIntensity(2);
    // Soften Phrase Bridges: temporary flag read by activities.
    this.active = {
      id: 'modulation',
      until: g.beatIndex + g.audio.meter * 2,
      color: v.color,
    };
    g.rhythm.encoreUntil = this.active.until;
    g._keyModulation = true;
    this._banner(v, 'The world answers in your key');
    this._burst(v.color, 40, 9);
    this._pulseRing(v.color, 12);
    // Auto-nudge nearby music gates toward open fantasy (visual only if not open).
    for (const p of g.activities.pois) {
      if ((p.type === 'musicgate' || p.type === 'ariagate') && !p.open) {
        const d = Math.hypot(p.x - g.player.pos.x, p.z - g.player.pos.z);
        if (d < 40 && p.mesh) {
          g.particles.burst(p.x, p.y + 2, p.z, _c.set(v.color), 12, { speed: 4, life: 0.6, kind: 3, size: 0.7 });
        }
      }
    }
  }

  _startDew(v) {
    const g = this.g, P = g.player;
    const dews = (g.profile.dews || []).slice();
    const n = Math.max(1, dews.length);
    // Spend up to 3 dew ids (keep progress flags that end with _open).
    const spend = dews.filter((id) => !String(id).endsWith('_open')).slice(0, 3);
    g.profile.dews = dews.filter((id) => !spend.includes(id));
    const r = 6 + spend.length * 2.5;
    const coef = 1.8 + spend.length * 0.7;
    g.combat.hitAll(g.combat.enemiesIn('circle', { x: P.pos.x, z: P.pos.z, r }), coef, {
      mult: RULES.rhythm.max_combat_multiplier, element: 'Arcane', tough: 2 + spend.length, perfect: true,
    });
    // Map ping: remaining dew destinations.
    for (const p of g.activities.pois) {
      if (p.type !== 'destination' || p.dewTaken) continue;
      if ((g.profile.dews || []).includes(p.id)) continue;
      g.overlay.text(p.x, p.y + 3, p.z, '◇', v.color, 16, { life: 1.4, rise: 0.15 });
      g.particles.burst(p.x, p.y + 1.5, p.z, _c.set(v.color), 8, { speed: 3, life: 0.7, kind: 3, size: 0.6 });
    }
    this.active = { id: 'dew', until: g.beatIndex + g.audio.meter, color: v.color, spent: spend.length };
    this._banner(v, spend.length ? `Bloomed ${spend.length} Dew` : 'Cymatic bloom');
    this._burst(v.color, 70, 15);
    this._pulseRing(v.color, r);
    for (let i = 0; i < 3; i++) {
      g.decals.spawn('ring', P.pos.x, P.pos.z, {
        r: r * (0.4 + i * 0.3), inner: r * (0.3 + i * 0.3), flash: true, dur: 0.5 + i * 0.15, color: v.color,
      });
    }
    g.save();
  }

  _startRecital(v) {
    const g = this.g;
    const rift = g.activities.rift;
    // Mid-run bank: softer phrase than full clear, applied immediately as active Echo.
    const phrase = g.echo.bankFromRift(
      { tier: Math.max(1, (rift.tier || 1) - 0), level: rift.level },
      false,
    );
    // Force-activate inheritance for the rest of this rift.
    g.echo.lineage.active = {
      motifs: phrase.motifs.map((m) => ({ ...m })),
      fromTier: phrase.tier,
      chance: 1,
      recital: true,
    };
    g.player.recalc();
    this.active = { id: 'recital', until: g.beatIndex + g.audio.meter * 2, color: v.color, phrase };
    g.rhythm.encoreUntil = this.active.until;
    this._banner(v, `Echo Phrase banked · Q${phrase.quality}`);
    this._burst(v.color, 48, 12);
    this._pulseRing(v.color, 9);
    // Rift floor stave flash.
    g.world.pulse(Psafe(g).x, Psafe(g).z, 2.8, true);
    g.combat.hitAll(g.combat.enemiesIn('circle', { x: g.player.pos.x, z: g.player.pos.z, r: 10 }), 2.0, {
      mult: RULES.rhythm.max_combat_multiplier, element: 'Arcane', tough: 4, perfect: true,
    });
  }

  // ------------------------------------------------------------------ beats
  _cascadeHit(coef) {
    const g = this.g, P = g.player;
    const p = { x: P.pos.x, z: P.pos.z, r: 8.5 };
    g.combat.hitAll(g.combat.enemiesIn('circle', p), coef, {
      mult: RULES.rhythm.max_combat_multiplier, element: P.stats.basicElement, tough: 2, perfect: true,
    });
    g.combat.flash('ring', p.x, p.z, { r: p.r, inner: p.r * 0.78 }, '#ffae45');
    this._spark('#ffae45', 14, 0.75);
    if (this.active) this.active.hits++;
  }

  _beatCascade(beat, a) {
    this._cascadeHit(1.15 + (beat.inBar === 0 ? 0.35 : 0));
    this.g.audio.encoreTick('cascade', beat.inBar);
  }

  _beatSubject(beat, a) {
    if (this.g.beatIndex < a.answerAt) {
      if (beat.inBar === 0) this._pulseRing(a.color, 5, 0.4);
      return;
    }
    if (a.phase === 'subject') {
      a.phase = 'answer';
      this.g.ui.toast('Answer!', 'gold');
      this.g.audio.encoreTick('subject', 0);
    }
    // Mirror: each marked foe takes a skill-like strike per beat of the answer bar.
    const sk = SKILL_BY_ID[this.g.profile.loadout[0]];
    const coef = (sk?.coef || 1.4) * 0.85;
    const el = sk?.element || this.g.player.stats.basicElement;
    for (const e of a.marks) {
      if (!e || e.dead) continue;
      this.g.combat.damage(e, coef, {
        mult: RULES.rhythm.max_combat_multiplier, element: el, tough: 2, perfect: true, skill: true,
      });
      this.g.particles.burst(e.pos.x, e.pos.y + e.scale, e.pos.z, _c.set(a.color), 10, { speed: 6, life: 0.4, kind: 3, size: 0.7 });
      makeGhostBeam(this.g, this.g.player.pos, e.pos, a.color);
    }
    this.g.audio.encoreTick('subject', beat.inBar);
  }

  _beatCadenza(beat, a) {
    if (beat.inBar === 0) {
      this._pulseRing(a.color, 7);
      this.g.audio.encoreTick('cadenza', 0);
    }
  }

  _beatReprise(beat, a) {
    if (a.i >= a.ghosts.length) return;
    const h = a.ghosts[a.i++];
    const list = this.g.combat.enemiesIn('circle', { x: h.x, z: h.z, r: 3.2 });
    if (list.length) {
      this.g.combat.hitAll(list, h.coef * 1.1, {
        mult: RULES.rhythm.max_combat_multiplier, element: h.element, tough: 2, perfect: true,
      });
    } else {
      this.g.combat.hitAll(this.g.combat.enemiesIn('circle', { x: h.x, z: h.z, r: 5 }), h.coef * 0.9, {
        mult: RULES.rhythm.max_combat_multiplier, element: h.element, tough: 1, perfect: true,
      });
    }
    this.g.decals.spawn('ring', h.x, h.z, { r: 2.2, inner: 1.6, flash: true, dur: 0.35, color: a.color });
    this.g.particles.burst(h.x, (h.y || 1) + 1, h.z, _c.set(a.color), 16, { speed: 8, life: 0.5, kind: 3, size: 0.85 });
    this.g.overlay.text(h.x, (h.y || 1) + 2.4, h.z, 'echo', a.color, 12, { life: 0.5 });
    this.g.audio.encoreTick('reprise', a.i);
  }

  _beatVeil(beat, a) {
    if (!a.landed && this.g.beatIndex >= a.landBeat) {
      a.landed = true;
      const g = this.g, P = g.player;
      const p = { x: P.pos.x, z: P.pos.z, r: 9 };
      g.combat.hitAll(g.combat.enemiesIn('circle', p), 3.2, {
        mult: RULES.rhythm.max_combat_multiplier, element: P.stats.basicElement, tough: 4, perfect: true, knock: 4,
      });
      g.combat.flash('circle', p.x, p.z, p, a.color);
      this._burst(a.color, 60, 16);
      this._pulseRing('#ffffff', 10);
      g.shake(0.75);
      g.audio.encoreTick('veil', 1);
      g.overlay.text(P.pos.x, P.pos.y + 2.6, P.pos.z, 'LAND', a.color, 20, { life: 0.8 });
    } else if (!a.landed && beat.inBar % 2 === 0) {
      this._spark(a.color, 8, 0.5);
      this.g.audio.encoreTick('veil', 0);
    }
  }

  _end() {
    const g = this.g;
    const a = this.active;
    if (!a) return;
    if (a.id === 'overture' && this._savedArias) {
      g.player.stats.arias = this._savedArias;
      this._savedArias = null;
      g.player.recalc();
    }
    if (a.id === 'modulation') {
      g._keyModulation = false;
      for (const p of g.activities.pois) {
        if (p.type === 'cleanse' && p.mesh && !p.cleansed) p.mesh.scale.setScalar(1);
      }
    }
    if (a.id === 'subject') {
      for (const e of a.marks || []) if (e) e._fugueMark = false;
    }
    this.active = null;
    this._veilY = 0;
  }
}

function Psafe(g) { return g.player.pos; }

function makeGhostBeam(g, from, to, color) {
  try {
    const dx = to.x - from.x, dz = to.z - from.z;
    const d = Math.hypot(dx, dz) || 1;
    for (let k = 0; k < 8; k++) {
      const t = k / 8;
      g.particles.emit(from.x + dx * t, from.y + 1.2, from.z + dz * t, _c.set(color), {
        speed: 1.2, life: 0.28, kind: 3, size: 0.55, gravity: 0,
      });
    }
  } catch { /* presentation only */ }
}
