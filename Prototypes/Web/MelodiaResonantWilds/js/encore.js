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
    biome: 'sakura_terrace',
    blurb: 'Radial hits every beat for a bar; Perfects extend the cascade.',
  },
  {
    id: 'subject',
    short: 'FUGUE',
    name: 'Subject & Answer',
    color: '#9a7bf0',
    tag: 'Combat',
    biome: 'fugue_grotto',
    blurb: 'Mark three foes, then mirror your phrase onto all of them.',
  },
  {
    id: 'cadenza',
    short: 'BREAK',
    name: 'Break Cadenza',
    color: '#ff5470',
    tag: 'Combat',
    biome: 'cadence_crystal_ridge',
    blurb: 'Shatter toughness; Perfects guarantee BREAK for a short window.',
  },
  {
    id: 'reprise',
    short: 'REPRISE',
    name: 'Encore Reprise',
    color: '#ffd978',
    tag: 'Combat',
    biome: null,
    blurb: 'Replay your last four Perfect hits as ghost notes.',
  },
  {
    id: 'duet',
    short: 'DUET',
    name: 'Choral Duet',
    color: '#62c8ff',
    tag: 'Companion',
    biome: 'liquid_cathedral',
    blurb: 'You and Sheep Harmonize as one — heal, cleanse, Tide pulse.',
  },
  {
    id: 'veil',
    short: 'VEIL',
    name: 'Aria Veil Step',
    color: '#e8dff8',
    tag: 'Wardrobe',
    biome: null,
    blurb: 'Float on the beat, then land as a shockwave.',
  },
  {
    id: 'overture',
    short: 'OVERTURE',
    name: 'Wardrobe Overture',
    color: '#f3b6cf',
    tag: 'Wardrobe',
    biome: null,
    blurb: 'Concert set: all Opus Aria passives live for eight beats.',
  },
  {
    id: 'modulation',
    short: 'KEY',
    name: 'Key Modulation',
    color: '#8ff0b4',
    tag: 'World',
    biome: null,
    blurb: 'Local key flips to yours — bridges soften, blots shrink.',
  },
  {
    id: 'dew',
    short: 'DEW',
    name: 'Resonance Dew Bloom',
    color: '#9fe6ff',
    tag: 'World',
    biome: 'aurora_glacier',
    blurb: 'Spent Dew detonates as a cymatic damage field.',
  },
  {
    id: 'recital',
    short: 'RECITAL',
    name: 'Rift Recital',
    color: '#c690ff',
    tag: 'Rift',
    biome: null,
    blurb: 'Inside a Rift: bank a mid-run Echo Phrase buff.',
  },
]);

export const ENCORE_BY_ID = Object.fromEntries(ENCORE_VARIANTS.map((v) => [v.id, v]));

/** Fashion-only Encore presentation skins (zero power). */
export const ENCORE_FASHION = Object.freeze({
  petal: { id: 'petal', name: 'Petal Trail', match: /dress|kimono|robe|petal/i, color: '#f7b8d2', particle: 1 },
  ice: { id: 'ice', name: 'Ice Veil', match: /coat|glacier|ice|veil/i, color: '#dff3ff', particle: 3 },
  gold: { id: 'gold', name: 'Concert Gold', match: /gown|tiara|opus|virtuoso/i, color: '#ffd978', particle: 2 },
  tide: { id: 'tide', name: 'Tide Ribbon', match: /slippers|heels|boots|shell/i, color: '#62c8ff', particle: 0 },
});

export class EncoreSystem {
  constructor(game) {
    this.g = game;
    const id = game.profile.settings.encoreVariant;
    this.selected = ENCORE_BY_ID[id] ? id : 'cascade';
    this.active = null;
    this.lastPerfects = [];
    this.lastCast = null;
    this._savedArias = null;
    this._modScore = null;
    this._bloomBoost = 0;
    this._veilY = 0;
    this._previewUntil = 0;
    this._afterimages = [];
    this._stats = { breaks: 0, hits: 0, heals: 0 };
  }

  get variant() { return ENCORE_BY_ID[this.selected] || ENCORE_VARIANTS[0]; }

  /** Presentation color: fashion skin overrides variant accent when dressed. */
  accentColor(v = this.variant) {
    const skin = this.fashionSkin();
    return skin?.color || v.color;
  }

  fashionSkin() {
    const eq = this.g.profile.equipment || {};
    const gown = eq.gown?.base || eq.gown?.name || '';
    const shoes = eq.shoes?.base || eq.shoes?.name || '';
    const head = eq.head?.base || eq.head?.name || '';
    const blob = `${gown} ${shoes} ${head} ${eq.gown?.rarity || ''}`.toLowerCase();
    for (const skin of Object.values(ENCORE_FASHION)) {
      if (skin.match.test(blob)) return skin;
    }
    // Opus gown always reads concert gold.
    if (eq.gown?.rarity >= 4) return ENCORE_FASHION.gold;
    return null;
  }

  biomeFavored(v = this.variant) {
    if (!v.biome || this.g.world?.inRift) return false;
    const d = this.g.world.dominantBiome(this.g.player.pos.x, this.g.player.pos.z);
    return d?.biome?.id === v.biome && d.weight > 0.45;
  }

  cycle(dir = 1) {
    const i = ENCORE_VARIANTS.findIndex((v) => v.id === this.selected);
    const n = (i + dir + ENCORE_VARIANTS.length) % ENCORE_VARIANTS.length;
    this.selected = ENCORE_VARIANTS[n].id;
    this.g.profile.settings.encoreVariant = this.selected;
    const v = this.variant;
    const fav = this.biomeFavored(v);
    const skin = this.fashionSkin();
    const bits = [v.name];
    if (fav) bits.push('biome favor');
    if (skin) bits.push(skin.name);
    this.g.ui.toast(`${bits.join(' · ')} — ${v.blurb}`, 'gold');
    this.g.audio.ui();
    this.g.audio.encoreSelect(v.id);
    this.preview(v);
    this.g.sheep?.reactEncore?.(v, this.accentColor(v));
    return v;
  }

  /** One-beat ghost of the selected Encore — toy feel while cycling. */
  preview(v = this.variant) {
    const g = this.g, P = g.player;
    const col = this.accentColor(v);
    this._previewUntil = g.time + (g.audio.spb || 0.45);
    g.decals.spawn('ring', P.pos.x, P.pos.z, { r: 3.2, inner: 2.4, flash: true, dur: 0.35, color: col });
    const kind = this.fashionSkin()?.particle ?? 3;
    g.particles.burst(P.pos.x, P.pos.y + 1.1, P.pos.z, _c.set(col), 18, { speed: 6, life: 0.4, kind, size: 0.7 });
    if (v.id === 'veil' || v.id === 'cascade') {
      for (let i = 0; i < 6; i++) {
        const a = (i / 6) * Math.PI * 2;
        g.particles.emit(P.pos.x, P.pos.y + 1.4, P.pos.z, _c.set(col), {
          dir: { x: Math.cos(a), y: 0.2, z: Math.sin(a) }, speed: 4, life: 0.45, kind, size: 0.6, gravity: 0,
        });
      }
    }
    if (g.postfx?.bloom) {
      g.postfx.bloom.strength = 0.75;
      this._bloomBoost = 0.45;
    }
    g.overlay.text(P.pos.x, P.pos.y + 2.6, P.pos.z, v.short, col, 14, { life: 0.55 });
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

    const favored = this.biomeFavored(v);
    const skin = this.fashionSkin();
    this._stats = { breaks: 0, hits: 0, heals: 0, favored, skin: skin?.id || null };
    this.dmgMul = favored ? 1.12 : 1;
    this.color = this.accentColor(v);

    R.encore = 0;
    let bars = v.id === 'overture' || v.id === 'modulation' ? 2 : v.id === 'veil' ? 1 : 2;
    if (favored) bars += 0; // favor is damage/feel, not duration creep
    // Dew set bonus 10: free extra beat of Perfect window.
    if ((g.profile.dewBonusTier || 0) >= 3) bars = Math.max(bars, bars);
    const extraBeats = (g.profile.dewBonusTier || 0) >= 3 ? 1 : 0;
    R.encoreUntil = g.beatIndex + g.audio.meter * bars + extraBeats;
    g.player.invulnUntil = Math.max(g.player.invulnUntil, g.time + 0.55);
    this._bloomBoost = 1;
    if (g.postfx?.bloom) {
      g.postfx.bloom.strength = 0.95;
      g.postfx.bloom.threshold = 0.72;
    }
    g.audio.setIntensity(2);
    g.shake(0.55);
    g.audio.encoreVariant(v.id);
    g.sheep?.reactEncore?.(v, this.color);
    if (favored) g.ui.toast(`${v.short} resonates with this biome (+12% power)`, 'gold');
    if (skin) g.ui.toast(`Fashion Encore — ${skin.name}`, 'lavender');

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
      // Gown afterimage ribbon — fashion-only trail along the float path.
      this._afterimageTimer = (this._afterimageTimer || 0) - dt;
      if (this._afterimageTimer <= 0) {
        this._afterimageTimer = 0.08;
        const col = this.color || this.active.color;
        this.g.particles.emit(P.pos.x, P.pos.y + 1.2 + this._veilY, P.pos.z, _c.set(col), {
          dir: { x: -Math.sin(P.facing), y: 0.15, z: -Math.cos(P.facing) },
          speed: 1.2, life: 0.55, kind: this.fashionSkin()?.particle ?? 1, size: 0.85, gravity: 0,
        });
      }
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
    const col = this.color || v.color;
    this.g.ui.banner(v.name.toUpperCase(), sub || v.blurb);
    this.g.overlay.text(this.g.player.pos.x, this.g.player.pos.y + 3.2, this.g.player.pos.z, v.short, col, 22, { life: 1.1 });
  }

  _burst(color, n = 48, speed = 12) {
    const P = this.g.player;
    const col = color || this.color || '#ffd978';
    const kind = this.fashionSkin()?.particle ?? 2;
    this.g.particles.burst(P.pos.x, P.pos.y + 1.1, P.pos.z, _c.set(col), n, { speed, life: 0.9, kind, size: 1.15 });
    this.g.world.pulse(P.pos.x, P.pos.z, 2.2, true);
  }

  _pulseRing(color, r = 8, alpha = 0.5) {
    const P = this.g.player;
    this.g.decals.spawn('ring', P.pos.x, P.pos.z, { r, inner: r * 0.72, flash: true, dur: 0.45, color: color || this.color, alpha });
  }

  _spark(color, n = 16, size = 0.7) {
    const P = this.g.player;
    const kind = this.fashionSkin()?.particle ?? 3;
    this.g.particles.burst(P.pos.x, P.pos.y + 1.4, P.pos.z, _c.set(color || this.color), n, { speed: 7, life: 0.5, kind, size });
  }

  _coef(base) {
    return base * (this.dmgMul || 1);
  }

  _startCascade(v) {
    const g = this.g;
    const col = this.color || v.color;
    const until = g.beatIndex + g.audio.meter;
    this.active = { id: 'cascade', until, color: col, hits: 0 };
    g.rhythm.encoreUntil = until;
    this._banner(v, 'Every beat is a Perfect wave — extend with Perfects');
    this._burst(col, 56, 14);
    this._pulseRing(col, 9);
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
    const col = this.color || v.color;
    const list = g.combat.enemiesIn('circle', { x: P.pos.x, z: P.pos.z, r: 11 });
    const n = g.combat.hitAll(list, this._coef(RULES.ultimate.damage_mult * 0.85), {
      mult: RULES.rhythm.max_combat_multiplier, element: P.stats.basicElement, tough: 14, perfect: true,
    });
    this._stats.hits += n;
    for (const e of list) {
      if (e.maxTough && !e.broken) {
        e.tough = 0;
        g.combat.breakEnemy(e);
        this._stats.breaks++;
      } else if (e.broken) this._stats.breaks++;
    }
    this.active = {
      id: 'cadenza',
      until: g.beatIndex + g.audio.meter * 2,
      color: col,
      perfectBreak: true,
    };
    this._banner(v, 'Perfects guarantee BREAK');
    this._burst(col, 64, 16);
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
    const col = this.color || v.color;
    this.active = { id: 'duet', until: g.beatIndex + g.audio.meter, color: col };
    const before = P.hp;
    P.heal(P.stats.maxHp * 0.12);
    this._stats.heals += Math.max(0, P.hp - before);
    P.sp = Math.min(P.stats.spMax, P.sp + 2);
    P.cleanse();
    g.sheep.harmonize(true);
    const p = { x: P.pos.x, z: P.pos.z, r: 8 };
    this._stats.hits += g.combat.hitAll(g.combat.enemiesIn('circle', p), this._coef(2.4), {
      mult: RULES.rhythm.max_combat_multiplier, element: 'Tide', tough: 3, perfect: true,
    });
    g.combat.flash('circle', p.x, p.z, p, col);
    g.activities.cleanseNear(P.pos.x, P.pos.z, 10);
    this._banner(v, 'Harmonize duet');
    this._burst(col, 52, 12);
    g.decals.spawn('ring', g.sheep.pos.x, g.sheep.pos.z, { r: 4.5, inner: 3.6, flash: true, dur: 0.7, color: col });
    this._pulseRing(col, 8);
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
    const col = this.color || '#ffae45';
    const p = { x: P.pos.x, z: P.pos.z, r: 8.5 };
    const n = g.combat.hitAll(g.combat.enemiesIn('circle', p), this._coef(coef), {
      mult: RULES.rhythm.max_combat_multiplier, element: P.stats.basicElement, tough: 2, perfect: true,
    });
    g.combat.flash('ring', p.x, p.z, { r: p.r, inner: p.r * 0.78 }, col);
    this._spark(col, 14, 0.75);
    if (this.active) this.active.hits++;
    this._stats.hits += n;
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
      this._stats.hits += g.combat.hitAll(g.combat.enemiesIn('circle', p), this._coef(3.2), {
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
    const v = ENCORE_BY_ID[a.id];
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
    // Last-cast replay — makes the ultimate feel memorable.
    const s = this._stats || {};
    const parts = [];
    if (s.breaks) parts.push(`${s.breaks} BREAK${s.breaks > 1 ? 's' : ''}`);
    if (s.hits) parts.push(`${s.hits} hit${s.hits > 1 ? 's' : ''}`);
    if (s.heals) parts.push(`+${Math.round(s.heals)} HP`);
    if (a.hits) parts.push(`${a.hits} waves`);
    if (a.spent) parts.push(`${a.spent} Dew`);
    if (s.favored) parts.push('biome favor');
    if (s.skin) parts.push(ENCORE_FASHION[s.skin]?.name || s.skin);
    const line = parts.length ? parts.join(' · ') : 'phrase complete';
    this.lastCast = { id: a.id, name: v?.name || a.id, line, at: g.time };
    g.ui.toast(`${v?.short || 'ENCORE'} · ${line}`, 'gold');
    this.active = null;
    this._veilY = 0;
    this.dmgMul = 1;
  }

  noteBreak() {
    if (this.active) this._stats.breaks = (this._stats.breaks || 0) + 1;
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
