// Save profile, XP/levels, bounties and exploration.

import { BOUNTY_TEMPLATES, DAILY_RECITAL_TEMPLATES, ELEMENTS, STARTING_SKILLS, SKILLS, WEB_SKILLS, MOTIF_BY_ID, xpToNext, MAX_LEVEL, RULES } from './design.js';
import { pick, randInt } from './util.js';
import { WORLD_RADIUS } from './design.js';

export const SAVE_KEY = 'melodia_resonant_wilds_v2';
export const SAVE_KEY_LEGACY = 'melodia_resonant_wilds_v1';
const GRID = 72;

export function dayKey(ms = Date.now()) {
  return new Date(ms).toISOString().slice(0, 10);
}

export function defaultProfile() {
  return {
    v: 2, level: 1, xp: 0, gold: 0, shards: 0, notes: 0,
    inventory: [], equipment: {}, motifs: {},
    echoLineage: { phrase: null, pity: 0, active: null, history: 0 },
    oshiAria: null,
    loadout: STARTING_SKILLS.slice(), learned: STARTING_SKILLS.slice(),
    blessings: [], pylons: ['pylon_hub'], shrines: [], sheets: [], vistas: [], photos: [], gates: [], cleanses: [], destinations: [], dews: [],
    dewBonusTier: 0, destBuffs: {},
    phrasebook: {}, concertSkins: [], fashionGold: [],
    daily: null,
    riftTier: 0, bounties: null, bountySet: 0, movement: 0, maestros: [], maestroExams: [],
    settings: { music: 0.75, sfx: 0.9, offsetMs: 0, difficulty: 'standard', quality: 'auto', autoSalvage: false, shake: true, encoreVariant: 'cascade' },
    stats: { kills: 0, perfects: 0, bestCombo: 0, bosses: 0, rifts: 0, playSeconds: 0 },
    explored: '', tutorial: 0, lastSeen: 0, spawn: null,
  };
}

export function loadProfile() {
  const base = defaultProfile();
  try {
    let raw = localStorage.getItem(SAVE_KEY);
    if (!raw) raw = localStorage.getItem(SAVE_KEY_LEGACY);
    if (!raw) return base;
    const p = JSON.parse(raw);
    const merged = {
      ...base, ...p,
      settings: { ...base.settings, ...(p.settings || {}) },
      stats: { ...base.stats, ...(p.stats || {}) },
      motifs: { ...(p.motifs || {}) },
      echoLineage: { ...base.echoLineage, ...(p.echoLineage || {}) },
      oshiAria: p.oshiAria ?? null,
      phrasebook: { ...(p.phrasebook || {}) },
      concertSkins: Array.isArray(p.concertSkins) ? p.concertSkins : [],
      fashionGold: Array.isArray(p.fashionGold) ? p.fashionGold : [],
      maestroExams: Array.isArray(p.maestroExams) ? p.maestroExams : [],
      v: 2,
    };
    // One-time migrate: ensure icons on existing items
    for (const it of [...(merged.inventory || []), ...Object.values(merged.equipment || {})]) {
      if (it && !it.icon && it.slot && it.base) {
        it.icon = `${it.slot}_${String(it.base).toLowerCase().replace(/\s+/g, '_')}`;
      }
    }
    return merged;
  } catch {
    return base;
  }
}

export function saveProfile(p) {
  try {
    p.lastSeen = Date.now();
    localStorage.setItem(SAVE_KEY, JSON.stringify(p));
    return true;
  } catch {
    return false;
  }
}

export function wipeProfile() {
  try {
    localStorage.removeItem(SAVE_KEY);
    localStorage.removeItem(SAVE_KEY_LEGACY);
  } catch { /* storage unavailable */ }
}

export class Progress {
  constructor(game) {
    this.g = game;
    this.grid = new Uint8Array(GRID * GRID);
    this._decodeExplored(game.profile.explored);
    if (!game.profile.bounties) game.profile.bounties = [this.newBounty(), this.newBounty(), this.newBounty()];
    this.ensureDaily();
  }

  // ------------------------------------------------------------ Daily Recital
  ensureDaily() {
    const pr = this.g.profile;
    const today = dayKey();
    if (pr.daily && pr.daily.day === today && Array.isArray(pr.daily.tasks) && pr.daily.tasks.length) return pr.daily;
    pr.daily = this.rollDaily(today);
    return pr.daily;
  }

  rollDaily(day = dayKey()) {
    const used = new Set();
    const tasks = [];
    const pool = DAILY_RECITAL_TEMPLATES.slice();
    while (tasks.length < 3 && pool.length) {
      const i = Math.floor(Math.random() * pool.length);
      const t = pool.splice(i, 1)[0];
      if (used.has(t.id)) continue;
      used.add(t.id);
      const n = randInt(Math.random, t.n[0], t.n[1]);
      tasks.push({ tid: t.id, kind: t.kind, text: t.text.replace('{n}', n), n, prog: 0, done: false });
    }
    return { day, tasks, claimed: false };
  }

  dailyEvent(kind, amount = 1) {
    const daily = this.ensureDaily();
    let changed = false;
    for (const t of daily.tasks) {
      if (t.done || t.kind !== kind) continue;
      t.prog = Math.min(t.n, t.prog + amount);
      if (t.prog >= t.n) {
        t.done = true;
        this.g.ui.toast(`Daily Recital: ${t.text}`, 'gold');
        this.g.audio.chime?.(3);
      }
      changed = true;
    }
    if (changed) this.g.save();
  }

  claimDaily() {
    const g = this.g, pr = g.profile;
    const daily = this.ensureDaily();
    if (daily.claimed) { g.ui.toast('Daily Recital already claimed today', 'soft'); return false; }
    if (!daily.tasks.every((t) => t.done)) { g.ui.toast('Finish all three Daily Recital tasks first', 'lavender'); return false; }
    daily.claimed = true;
    pr.notes += 12;
    pr.gold += 80 + pr.level * 10;
    this.addXp(xpToNext(pr.level) * 0.22);
    // Fashion-only trail unlock for today's board.
    if (!pr.concertSkins.includes('overture')) {
      pr.concertSkins.push('overture');
      g.ui.banner('Daily Recital complete', '+12 Golden Notes · Daily Overture Trail unlocked');
    } else {
      g.ui.banner('Daily Recital complete', '+12 Golden Notes · gold & XP');
    }
    g.audio.levelUp();
    g.save();
    return true;
  }

  // ------------------------------------------------------------ XP
  addXp(n) {
    const pr = this.g.profile;
    if (pr.level >= MAX_LEVEL) return;
    pr.xp += Math.round(n);
    let leveled = false;
    while (pr.level < MAX_LEVEL && pr.xp >= xpToNext(pr.level)) {
      pr.xp -= xpToNext(pr.level);
      pr.level++;
      leveled = true;
    }
    if (leveled) this.g.onLevelUp();
  }

  isUnlocked(skill) {
    const pr = this.g.profile;
    return pr.level >= skill.unlockLevel || pr.learned.includes(skill.id);
  }

  lockedSkills() { return SKILLS.filter((s) => !this.isUnlocked(s)); }

  // ------------------------------------------------------------ bounties
  newBounty() {
    const pr = this.g.profile;
    const t = pick(Math.random, BOUNTY_TEMPLATES.filter((b) => b.id !== 'rift' || pr.level >= 3));
    const n = randInt(Math.random, t.n[0], t.n[1]);
    const biome = this.g.currentBiome?.();
    const e = biome ? pick(Math.random, biome.elements) : pick(Math.random, ELEMENTS);
    return { tid: t.id, text: t.text.replace('{n}', n).replace('{e}', e), n, e, prog: 0, done: false };
  }

  event(type, amount = 1, data = {}) {
    const pr = this.g.profile;
    const matches = (b) => {
      switch (b.tid) {
        case 'kill_element': return type === 'kill' && data.element === b.e;
        case 'kills': return type === 'kill';
        case 'elites': return type === 'kill' && !!data.elite;
        default: return b.tid === type;
      }
    };
    for (const b of pr.bounties) {
      if (b.done || !matches(b)) continue;
      b.prog = Math.min(b.n, b.prog + amount);
      if (b.prog >= b.n) {
        b.done = true;
        this.g.ui.toast(`Bounty complete: ${b.text}`, 'gold');
        this.g.audio.levelUp();
      }
    }
    // Mirror a few bounty kinds into Daily Recital progress.
    if (type === 'perfects') this.dailyEvent('perfects', amount);
    if (type === 'chests' || type === 'shrine') { /* board-adjacent; no auto mirror */ }
  }

  claim(i) {
    const g = this.g, pr = g.profile;
    const b = pr.bounties[i];
    if (!b || !b.done) return;
    const gold = 60 + pr.level * 25;
    pr.gold += gold;
    pr.notes += 6;
    this.addXp(xpToNext(pr.level) * 0.18);
    const it = g.loot.make(pr.level + 1, { min: 2, bonus: 0.3 });
    const put = g.loot.add(it);
    g.ui.toast(`+${gold} gold · +6 Golden Notes${put ? ' · ' + it.name : ''}`, 'gold');
    g.audio.loot(it.rarity);
    pr.bounties[i] = this.newBounty();
    pr.bountySet++;
    if (pr.bountySet >= 3) {
      pr.bountySet = 0;
      const cache = g.loot.make(pr.level + 2, { min: 3, bonus: 0.6 });
      g.loot.add(cache);
      pr.notes += 25;
      const packTier = ['tuned', 'tuned', 'resonant'];
      const pack = g.loot.grantMotifPack(pick(Math.random, packTier));
      const packLabel = Object.entries(pack.motifs)
        .map(([id, n]) => `${MOTIF_BY_ID[id]?.name || id}×${n}`)
        .join(', ');
      g.ui.toast(`Chorus Cache! ${cache.name} · +25♪ · Motif pack (${pack.n}): ${packLabel}`, 'gold');
      g.ui.ceremonyFlash?.('bank');
      g.audio.fanfare('bank');
      g.audio.loot(cache.rarity);
      if (g.ui.motifMorph) {
        g.ui.motifMorph({
          fromIcon: cache.icon || g.loot.iconKey(cache),
          motifIds: Object.keys(pack.motifs),
          rarity: cache.rarity,
          label: `Chorus Cache Motif pack · ${packLabel}`,
          kind: 'synth',
        });
      }
    }
    g.save();
  }

  // ------------------------------------------------------------ Movements (main path)
  // One Movement per biome, in level order: attune a pylon, answer a shrine,
  // defeat the Maestro. Returns the current step with a world target.
  objective() {
    const g = this.g, pr = g.profile;
    const BI = g.biomes;
    if (pr.movement >= BI.length) return null;
    const b = BI[pr.movement];
    const label = b.name.split('—')[0].trim();
    const P = g.player.pos;
    const nearest = (type, pred) => {
      let best = null, bd = Infinity;
      for (const p of g.activities.pois) {
        if (p.type !== type || p.biome !== pr.movement || !pred(p)) continue;
        const d = Math.hypot(p.x - P.x, p.z - P.z);
        if (d < bd) { bd = d; best = p; }
      }
      return best;
    };
    const roman = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII'][pr.movement];
    if (!pr.pylons.some((id) => id.startsWith('pylon_' + b.id))) return { title: `Movement ${roman} · ${label}`, text: `Travel to ${label} and attune a pylon`, target: nearest('pylon', () => true) };
    if (!pr.shrines.some((id) => id.startsWith('shrine_' + b.id))) return { title: `Movement ${roman} · ${label}`, text: 'Answer a music-key shrine', target: nearest('shrine', (p) => !pr.shrines.includes(p.id)) };
    if (!pr.maestros.includes(b.id)) return { title: `Movement ${roman} · ${label}`, text: `Defeat ${b.bossName} (Lv ${b.levels[1]})`, target: nearest('boss', () => true) };
    pr.movement++;
    pr.notes += 20;
    const it = g.loot.make(b.levels[1] + 2, { min: 3, bonus: 0.6 });
    g.loot.add(it);
    // Movement clearance teaches the next web chart (Sheet Music path).
    const webNext = WEB_SKILLS
      .filter((s) => !pr.learned.includes(s.id))
      .sort((a, b) => a.unlockLevel - b.unlockLevel)[0];
    let skillBit = '';
    if (webNext) {
      pr.learned.push(webNext.id);
      skillBit = ` · chart ${webNext.name}`;
      g.ui.toast(`Movement Sheet: learned ${webNext.name}`, 'gold');
    }
    g.ui.banner(`Movement ${roman} complete`, `${label} answers you · +20 Golden Notes · ${it.name}${skillBit}`);
    g.audio.fanfare('bank');
    g.ui.ceremonyFlash?.('bank');
    g.save();
    return this.objective();
  }

  // ------------------------------------------------------------ exploration
  _decodeExplored(s) {
    if (!s) return;
    try {
      const bin = atob(s);
      for (let i = 0; i < Math.min(bin.length, this.grid.length); i++) this.grid[i] = bin.charCodeAt(i);
    } catch { /* ignore corrupt data */ }
  }

  encodeExplored() {
    let s = '';
    for (let i = 0; i < this.grid.length; i++) s += String.fromCharCode(this.grid[i]);
    return btoa(s);
  }

  reveal(x, z, r = 48) {
    const ext = WORLD_RADIUS + 20, cell = (ext * 2) / GRID;
    const ci = Math.floor((x + ext) / cell), cj = Math.floor((z + ext) / cell), rr = Math.ceil(r / cell);
    let changed = false;
    for (let j = cj - rr; j <= cj + rr; j++) {
      for (let i = ci - rr; i <= ci + rr; i++) {
        if (i < 0 || j < 0 || i >= GRID || j >= GRID) continue;
        if ((i - ci) ** 2 + (j - cj) ** 2 > rr * rr) continue;
        const k = j * GRID + i;
        if (!this.grid[k]) { this.grid[k] = 1; changed = true; }
      }
    }
    return changed;
  }

  explored(i, j) { return this.grid[j * GRID + i] === 1; }
  get GRID() { return GRID; }

  percent() {
    let land = 0, seen = 0;
    const ext = WORLD_RADIUS + 20, cell = (ext * 2) / GRID;
    for (let j = 0; j < GRID; j++) for (let i = 0; i < GRID; i++) {
      const x = -ext + (i + 0.5) * cell, z = -ext + (j + 0.5) * cell;
      if (Math.hypot(x, z) > WORLD_RADIUS - 40) continue;
      land++;
      if (this.grid[j * GRID + i]) seen++;
    }
    return Math.round((seen / land) * 100);
  }
}

export const SP_START = RULES.turn_economy.shared_sp_start;
