// Save profile, XP/levels, bounties and exploration.

import { BOUNTY_TEMPLATES, ELEMENTS, STARTING_SKILLS, SKILLS, xpToNext, MAX_LEVEL, RULES } from './design.js';
import { pick, randInt } from './util.js';
import { WORLD_RADIUS } from './design.js';

export const SAVE_KEY = 'melodia_resonant_wilds_v1';
const GRID = 72;

export function defaultProfile() {
  return {
    v: 1, level: 1, xp: 0, gold: 0, shards: 0, notes: 0,
    inventory: [], equipment: {},
    loadout: STARTING_SKILLS.slice(), learned: STARTING_SKILLS.slice(),
    blessings: [], pylons: ['pylon_hub'], shrines: [], sheets: [],
    riftTier: 0, bounties: null, bountySet: 0, movement: 0, maestros: [],
    settings: { music: 0.75, sfx: 0.9, offsetMs: 0, difficulty: 'standard', quality: 'auto', autoSalvage: false, shake: true },
    stats: { kills: 0, perfects: 0, bestCombo: 0, bosses: 0, rifts: 0, playSeconds: 0 },
    explored: '', tutorial: 0, lastSeen: 0, spawn: null,
  };
}

export function loadProfile() {
  const base = defaultProfile();
  try {
    const raw = localStorage.getItem(SAVE_KEY);
    if (!raw) return base;
    const p = JSON.parse(raw);
    return { ...base, ...p, settings: { ...base.settings, ...(p.settings || {}) }, stats: { ...base.stats, ...(p.stats || {}) } };
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
  try { localStorage.removeItem(SAVE_KEY); } catch { /* storage unavailable */ }
}

export class Progress {
  constructor(game) {
    this.g = game;
    this.grid = new Uint8Array(GRID * GRID);
    this._decodeExplored(game.profile.explored);
    if (!game.profile.bounties) game.profile.bounties = [this.newBounty(), this.newBounty(), this.newBounty()];
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
      g.ui.toast(`Chorus Cache! ${cache.name} · +25 Golden Notes`, 'gold');
      g.audio.loot(cache.rarity);
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
    const roman = ['I', 'II', 'III', 'IV', 'V'][pr.movement];
    if (!pr.pylons.some((id) => id.startsWith('pylon_' + b.id))) return { title: `Movement ${roman} · ${label}`, text: `Travel to ${label} and attune a pylon`, target: nearest('pylon', () => true) };
    if (!pr.shrines.some((id) => id.startsWith('shrine_' + b.id))) return { title: `Movement ${roman} · ${label}`, text: 'Answer a music-key shrine', target: nearest('shrine', (p) => !pr.shrines.includes(p.id)) };
    if (!pr.maestros.includes(b.id)) return { title: `Movement ${roman} · ${label}`, text: `Defeat ${b.bossName} (Lv ${b.levels[1]})`, target: nearest('boss', () => true) };
    pr.movement++;
    pr.notes += 20;
    const it = g.loot.make(b.levels[1] + 2, { min: 3, bonus: 0.6 });
    g.loot.add(it);
    g.ui.banner(`Movement ${roman} complete`, `${label} answers you · +20 Golden Notes · ${it.name}`);
    g.audio.levelUp();
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
