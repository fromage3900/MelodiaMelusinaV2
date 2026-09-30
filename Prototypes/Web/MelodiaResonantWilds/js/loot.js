// Items (Wardrobe slots), rarity rolls, affixes, arias, salvage and forge honing.

import { RARITIES, SLOTS, SLOT_BY_ID, AFFIXES, AFFIX_BY_KEY, ARIAS, ARIA_BY_ID, ELEMENTS, HONE_MAX, honeChance } from './design.js';
import { pick, randRange, weightedPick } from './util.js';

const PREFIX = [[''], ['Tuned', 'Bright', 'Lilting'], ['Resonant', 'Chiming', 'Lucid'], ['Virtuoso', 'Celestial', 'Aria-bound'], ['']];
const SLOT_HP = { instrument: 0, head: 0.8, gown: 1.4, gloves: 0.7, shoes: 0.8, charm: 0.6 };
const SLOT_ARM = { instrument: 0, head: 0.9, gown: 1.2, gloves: 1.0, shoes: 0.9, charm: 0.5 };
const INV_MAX = 36;

let uidSeq = Date.now() % 1e6;

export class Loot {
  constructor(game) {
    this.g = game;
    this.rng = Math.random;
  }

  get INV_MAX() { return INV_MAX; }

  rollRarity(bonus = 0, min = 0) {
    const magic = this.g.player?.stats?.magic || 0;
    const b = bonus + magic + this.g.difficultyDef.rarityBonus;
    const list = RARITIES.map((r, i) => ({ i, w: r.weight * Math.exp(b * i * 1.1) })).filter((x) => x.i >= min);
    return weightedPick(this.rng, list, (x) => x.w).i;
  }

  make(ilvl, opts = {}) {
    const rng = this.rng;
    const slot = opts.slot ? SLOT_BY_ID[opts.slot] : pick(rng, SLOTS);
    const rarity = opts.rarity ?? this.rollRarity(opts.bonus || 0, opts.min || 0);
    const R = RARITIES[rarity];
    const [base, family] = pick(rng, slot.bases);
    const it = { uid: ++uidSeq, slot: slot.id, base, rarity, ilvl: Math.max(1, Math.round(ilvl)), up: 0, pity: 0, affixes: [], isNew: true };
    if (slot.id === 'instrument') {
      it.family = family;
      it.element = opts.element || pick(rng, ELEMENTS);
      it.attack = Math.round((6 + it.ilvl * 4.2) * R.mult * randRange(rng, 0.95, 1.08));
    } else {
      it.hp = Math.round((10 + it.ilvl * 7.5) * R.mult * SLOT_HP[slot.id] * randRange(rng, 0.9, 1.1));
      it.armor = Math.round((2 + it.ilvl * 1.3) * R.mult * SLOT_ARM[slot.id] * randRange(rng, 0.9, 1.1));
    }
    const keys = AFFIXES.map((a) => a.key).filter((k) => !(slot.id !== 'instrument' && k === 'dmg' && rng() < 0.3));
    const chosen = new Set();
    while (chosen.size < R.affixes && chosen.size < keys.length) chosen.add(pick(rng, keys));
    for (const key of chosen) {
      const A = AFFIX_BY_KEY[key];
      const q = rng() * 0.6 + 0.4 * (rarity / 4) + 0.1;
      let v;
      if (A.flat) v = Math.max(1, Math.round(A.flat * it.ilvl * (0.7 + q * 0.6)));
      else v = Math.max(1, Math.round(A.min + (A.max - A.min) * Math.min(1, q)));
      const aff = { key, v };
      if (A.element) aff.e = it.element || pick(rng, ELEMENTS);
      it.affixes.push(aff);
    }
    if (R.id === 'opus') it.aria = opts.aria || pick(rng, ARIAS).id;
    it.name = this.name(it);
    return it;
  }

  name(it) {
    if (it.aria) return `${ARIA_BY_ID[it.aria].name} ${it.base}`;
    const pre = pick(this.rng, PREFIX[it.rarity]);
    const el = it.element || it.affixes.find((a) => a.e)?.e;
    return `${pre ? pre + ' ' : ''}${it.base}${el ? ' of ' + el : ''}`;
  }

  affixText(a) {
    return AFFIX_BY_KEY[a.key].text.replace('{v}', a.v).replace('{e}', a.e || '');
  }

  lines(it) {
    const out = [];
    const up = 1 + 0.06 * (it.up || 0);
    if (it.attack) out.push(`${Math.round(it.attack * up)} Attack` + (it.family ? ` · ${it.family === 'melee' ? 'Melee' : 'Ranged'} · ${it.element}` : ''));
    if (it.hp) out.push(`+${Math.round(it.hp * up)} Max HP · +${Math.round(it.armor * up)} Poise`);
    for (const a of it.affixes) out.push(this.affixText(a));
    return out;
  }

  // Rough power number used for "better" arrows and Equip Best.
  score(it) {
    if (!it) return 0;
    const up = 1 + 0.06 * (it.up || 0);
    let s = (it.attack || 0) * up * 3 + (it.hp || 0) * up * 0.35 + (it.armor || 0) * up * 2.2 + it.ilvl * 2;
    const W = { dmg: 14, elem: 5, crit: 11, critdmg: 3, perfectms: 5, hp: 0.35, armor: 2.2, speed: 6, encore: 3, harmony: 2, cdr: 9, gold: 1, break: 2, drain: 16, magic: 2 };
    for (const a of it.affixes) s += a.v * (W[a.key] || 1);
    if (it.aria) s += 80;
    return Math.round(s);
  }

  gearScore() {
    const eq = this.g.profile.equipment;
    let sum = 0;
    for (const s of SLOTS) {
      const it = eq[s.id];
      if (it) sum += it.ilvl * 10 + it.rarity * 15 + (it.up || 0) * 8;
    }
    return Math.round(sum / SLOTS.length);
  }

  add(it) {
    const inv = this.g.profile.inventory;
    if (inv.length >= INV_MAX) return false;
    if (this.g.profile.settings.autoSalvage && it.rarity <= 1 && this.score(it) <= this.score(this.g.profile.equipment[it.slot])) {
      this.salvage(it, true);
      return true;
    }
    inv.push(it);
    return true;
  }

  equip(it) {
    const pr = this.g.profile;
    const i = pr.inventory.indexOf(it);
    if (i >= 0) pr.inventory.splice(i, 1);
    const old = pr.equipment[it.slot];
    pr.equipment[it.slot] = it;
    it.isNew = false;
    if (old) pr.inventory.push(old);
    this.g.player.recalc();
    this.g.onGearChanged();
  }

  equipBest() {
    const pr = this.g.profile;
    let n = 0;
    for (const s of SLOTS) {
      let best = pr.equipment[s.id], bs = this.score(best);
      for (const it of pr.inventory) if (it.slot === s.id && this.score(it) > bs) { best = it; bs = this.score(it); }
      if (best && best !== pr.equipment[s.id]) { this.equip(best); n++; }
    }
    return n;
  }

  salvageValue(it) {
    return { gold: Math.round(it.ilvl * 3 * (it.rarity + 1) * (1 + (it.up || 0) * 0.3)), shards: 1 + it.rarity * 2 + Math.floor((it.up || 0) / 2) };
  }

  salvage(it, silent = false) {
    const pr = this.g.profile;
    if (it.locked) return null;
    const i = pr.inventory.indexOf(it);
    if (i >= 0) pr.inventory.splice(i, 1);
    const v = this.salvageValue(it);
    pr.gold += v.gold;
    pr.shards += v.shards;
    if (!silent) this.g.ui.toast(`Salvaged ${it.name}: +${v.gold} gold, +${v.shards} shards`);
    return v;
  }

  salvageWhere(pred) {
    const pr = this.g.profile;
    const list = pr.inventory.filter((it) => !it.locked && pred(it));
    let gold = 0, shards = 0;
    for (const it of list) { const v = this.salvage(it, true); gold += v.gold; shards += v.shards; }
    return { n: list.length, gold, shards };
  }

  honeCost(it) {
    const u = it.up || 0;
    return { gold: Math.round(60 * Math.pow(u + 1, 1.6) * (1 + it.ilvl / 10)), shards: 4 + u * 3 };
  }

  // Lost Ark style: chance falls with level; each failure banks +10% pity.
  hone(it) {
    const pr = this.g.profile;
    if ((it.up || 0) >= HONE_MAX) return { ok: false, reason: 'max' };
    const c = this.honeCost(it);
    if (pr.gold < c.gold || pr.shards < c.shards) return { ok: false, reason: 'cost' };
    pr.gold -= c.gold; pr.shards -= c.shards;
    const chance = Math.min(1, honeChance(it.up || 0) + (it.pity || 0));
    if (Math.random() < chance) {
      it.up = (it.up || 0) + 1;
      it.pity = 0;
      this.g.player.recalc();
      this.g.onGearChanged();
      return { ok: true, success: true, chance };
    }
    it.pity = (it.pity || 0) + 0.1;
    return { ok: true, success: false, chance };
  }
}
