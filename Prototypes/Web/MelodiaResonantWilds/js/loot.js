// Items (Wardrobe slots), rarity rolls, affixes, arias, Motif salvage,
// Harmonic Synthesis, and forge tempering (hone).

import {
  RARITIES, SLOTS, SLOT_BY_ID, AFFIXES, AFFIX_BY_KEY, ARIAS, ARIA_BY_ID, ELEMENTS,
  HONE_MAX, honeChance, MOTIFS, MOTIF_BY_ID, SYNTH_LOOPS, SYNTH_SHARD_COST, SYNTH_GOLD_COST,
  synthQuality, synthTraitSlots, MOTIF_PACK,
} from './design.js';
import { pick, randRange, weightedPick, randInt } from './util.js';

const PREFIX = [[''], ['Tuned', 'Bright', 'Lilting'], ['Resonant', 'Chiming', 'Lucid'], ['Virtuoso', 'Celestial', 'Aria-bound'], ['']];
const SLOT_HP = { instrument: 0, head: 0.8, gown: 1.4, gloves: 0.7, shoes: 0.8, charm: 0.6 };
const SLOT_ARM = { instrument: 0, head: 0.9, gown: 1.2, gloves: 1.0, shoes: 0.9, charm: 0.5 };
const INV_MAX = 36;

let uidSeq = Date.now() % 1e6;

function slugBase(base) {
  return String(base).toLowerCase().replace(/\s+/g, '_');
}

export class Loot {
  constructor(game) {
    this.g = game;
    this.rng = Math.random;
  }

  get INV_MAX() { return INV_MAX; }

  iconKey(it) {
    if (!it) return null;
    return `${it.slot}_${slugBase(it.base)}`;
  }

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
    const it = {
      uid: ++uidSeq, slot: slot.id, base, rarity,
      ilvl: Math.max(1, Math.round(ilvl)), up: 0, pity: 0, affixes: [], isNew: true,
      quality: 0, synthCount: 0, icon: `${slot.id}_${slugBase(base)}`,
    };
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
    const qMul = 1 + (it.quality || 0) / 200;
    if (it.attack) out.push(`${Math.round(it.attack * up * qMul)} Attack` + (it.family ? ` · ${it.family === 'melee' ? 'Melee' : 'Ranged'} · ${it.element}` : ''));
    if (it.hp) out.push(`+${Math.round(it.hp * up * qMul)} Max HP · +${Math.round(it.armor * up * qMul)} Poise`);
    for (const a of it.affixes) out.push(this.affixText(a));
    if (it.quality) out.push(`Synthesis Quality ${it.quality}`);
    return out;
  }

  // Rough power number used for "better" arrows and Equip Best.
  score(it) {
    if (!it) return 0;
    const up = 1 + 0.06 * (it.up || 0);
    const qMul = 1 + (it.quality || 0) / 200;
    let s = (it.attack || 0) * up * qMul * 3 + (it.hp || 0) * up * qMul * 0.35 + (it.armor || 0) * up * qMul * 2.2 + it.ilvl * 2;
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
      if (it) sum += it.ilvl * 10 + it.rarity * 15 + (it.up || 0) * 8 + (it.quality || 0) * 0.3;
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
    // Nikki Ability Outfit beat — shoes/gown equip can open ethereal float spaces.
    if (it.slot === 'shoes' || it.slot === 'gown') {
      this.g.activities?.onAbilityOutfitEquipped?.(it.slot);
    }
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

  // ------------------------------------------------------------ Motifs
  ensureMotifs() {
    const pr = this.g.profile;
    if (!pr.motifs) pr.motifs = {};
    return pr.motifs;
  }

  addMotif(id, n = 1) {
    const bag = this.ensureMotifs();
    bag[id] = (bag[id] || 0) + n;
    return bag[id];
  }

  spendMotif(id, n = 1) {
    const bag = this.ensureMotifs();
    if ((bag[id] || 0) < n) return false;
    bag[id] -= n;
    if (bag[id] <= 0) delete bag[id];
    return true;
  }

  motifCount(id) { return this.ensureMotifs()[id] || 0; }

  motifInventory() {
    const bag = this.ensureMotifs();
    return Object.entries(bag)
      .filter(([, n]) => n > 0)
      .map(([id, n]) => ({ ...MOTIF_BY_ID[id], id, n }))
      .filter((m) => m.name);
  }

  /** Chorus Cache / Recital Motif pack — Atelier-style material bundle. */
  grantMotifPack(tier = 'tuned') {
    const rng = this.rng;
    const range = MOTIF_PACK[tier] || MOTIF_PACK.tuned;
    const n = randInt(rng, range[0], range[1]);
    const gain = {};
    const q2 = MOTIFS.filter((m) => m.quality >= 2);
    for (let i = 0; i < n; i++) {
      const rare = rng() < (tier === 'resonant' ? 0.45 : tier === 'tuned' ? 0.25 : 0.1);
      const id = pick(rng, rare && q2.length ? q2 : MOTIFS).id;
      this.addMotif(id, 1);
      gain[id] = (gain[id] || 0) + 1;
    }
    return { tier, n, motifs: gain };
  }

  /** Roll Motifs yielded by salvaging an item. Always at least one. */
  rollMotifsFromItem(it) {
    const rng = this.rng;
    const out = [];
    const n = 1 + Math.floor(it.rarity / 2) + (it.up >= 5 ? 1 : 0);
    const prefer = it.element
      ? MOTIFS.filter((m) => m.element === it.element)
      : MOTIFS.filter((m) => m.quality === 1);
    const pool = prefer.length ? prefer : MOTIFS;
    for (let i = 0; i < n; i++) {
      const rare = it.rarity >= 3 && rng() < 0.35;
      const src = rare ? MOTIFS.filter((m) => m.quality >= 2) : pool;
      out.push(pick(rng, src.length ? src : MOTIFS).id);
    }
    // Affix-linked Motif chance
    for (const a of it.affixes || []) {
      const hit = MOTIFS.find((m) => m.trait === a.key);
      if (hit && rng() < 0.4) out.push(hit.id);
    }
    return out;
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
    const motifIds = this.rollMotifsFromItem(it);
    const motifGain = {};
    for (const id of motifIds) {
      this.addMotif(id, 1);
      motifGain[id] = (motifGain[id] || 0) + 1;
    }
    v.motifs = motifGain;
    if (!silent) {
      const bits = Object.entries(motifGain).map(([id, n]) => `${MOTIF_BY_ID[id]?.name || id}×${n}`);
      if (this.g.ui.motifMorph) {
        this.g.ui.motifMorph({
          fromIcon: it.icon || this.iconKey(it),
          motifIds: Object.keys(motifGain),
          rarity: it.rarity,
          label: `Salvaged ${it.name}: +${v.gold}● +${v.shards}◆ · ${bits.join(', ')}`,
        });
      } else {
        this.g.ui.toast(`Salvaged ${it.name}: +${v.gold}● +${v.shards}◆ · ${bits.join(', ')}`);
      }
    }
    return v;
  }

  salvageWhere(pred) {
    const pr = this.g.profile;
    const list = pr.inventory.filter((it) => !it.locked && pred(it));
    let gold = 0, shards = 0;
    const motifs = {};
    for (const it of list) {
      const v = this.salvage(it, true);
      gold += v.gold; shards += v.shards;
      for (const [id, n] of Object.entries(v.motifs || {})) motifs[id] = (motifs[id] || 0) + n;
    }
    return { n: list.length, gold, shards, motifs };
  }

  // ------------------------------------------------------------ Harmonic Synthesis
  /**
   * Preview fill state for UI: motifSlots is [{motifId}] assigned to loops in order.
   * Loops fill when enough Motifs of matching element are assigned.
   */
  synthPreview(it, motifSlots = []) {
    const loops = SYNTH_LOOPS.filter((L) => !L.opusOnly || it.rarity >= 4);
    const fills = loops.map(() => 0);
    const used = [];
    let qi = 0;
    for (let i = 0; i < motifSlots.length; i++) {
      const mid = motifSlots[i];
      if (!mid) continue;
      const M = MOTIF_BY_ID[mid];
      if (!M) continue;
      // Assign to first loop that still needs fill and accepts this Motif.
      for (let li = 0; li < loops.length; li++) {
        const L = loops[li];
        if (fills[li] >= L.fillNeed) continue;
        if (L.elements === 'match') {
          const el = it.element || it.affixes.find((a) => a.e)?.e;
          if (el && M.element !== el) continue;
        }
        fills[li]++;
        used.push({ loop: L.id, motifId: mid });
        qi += M.quality;
        break;
      }
    }
    const filledLoops = fills.filter((f, i) => f >= loops[i].fillNeed).length;
    const quality = synthQuality(filledLoops, qi);
    const traitSlots = synthTraitSlots(filledLoops);
    return { loops, fills, filledLoops, quality, traitSlots, used, cost: { gold: SYNTH_GOLD_COST + (it.synthCount || 0) * 25, shards: SYNTH_SHARD_COST + (it.synthCount || 0) } };
  }

  /**
   * Apply Harmonic Synthesis: spend Motifs + gold/shards, raise quality,
   * transfer up to traitSlots Motifs as affixes (Atelier trait pick).
   * transferKeys: optional ordered trait keys to prefer from Motifs.
   */
  synthesize(it, motifSlots = [], transferKeys = null) {
    const pr = this.g.profile;
    if (!it) return { ok: false, reason: 'item' };
    if ((it.synthCount || 0) >= 5) return { ok: false, reason: 'rebuild_max' };
    const preview = this.synthPreview(it, motifSlots);
    if (preview.filledLoops < 1) return { ok: false, reason: 'loops' };
    if (pr.gold < preview.cost.gold || pr.shards < preview.cost.shards) return { ok: false, reason: 'cost' };

    // Validate Motif stock
    const need = {};
    for (const mid of motifSlots) if (mid) need[mid] = (need[mid] || 0) + 1;
    for (const [id, n] of Object.entries(need)) if (this.motifCount(id) < n) return { ok: false, reason: 'motifs' };

    for (const [id, n] of Object.entries(need)) this.spendMotif(id, n);
    pr.gold -= preview.cost.gold;
    pr.shards -= preview.cost.shards;

    it.quality = Math.max(it.quality || 0, preview.quality);
    it.synthCount = (it.synthCount || 0) + 1;

    // Trait transfer from Motifs
    const motifTraits = [];
    for (const mid of motifSlots) {
      const M = MOTIF_BY_ID[mid];
      if (M?.trait) motifTraits.push(M);
    }
    const slots = preview.traitSlots;
    const chosen = [];
    if (transferKeys?.length) {
      for (const key of transferKeys) {
        if (chosen.length >= slots) break;
        const M = motifTraits.find((m) => m.trait === key && !chosen.includes(m));
        if (M) chosen.push(M);
      }
    }
    for (const M of motifTraits) {
      if (chosen.length >= slots) break;
      if (!chosen.includes(M)) chosen.push(M);
    }

    for (const M of chosen) {
      const A = AFFIX_BY_KEY[M.trait];
      if (!A) continue;
      const existing = it.affixes.find((a) => a.key === M.trait);
      const q = 0.45 + preview.quality / 200;
      let v;
      if (A.flat) v = Math.max(1, Math.round(A.flat * it.ilvl * (0.6 + q * 0.7)));
      else v = Math.max(1, Math.round(A.min + (A.max - A.min) * Math.min(1, q)));
      if (existing) existing.v = Math.max(existing.v, v);
      else {
        const aff = { key: M.trait, v };
        if (A.element) aff.e = it.element || M.element;
        it.affixes.push(aff);
      }
    }

    // Opus Super Trait: ensure Aria if Aria ring filled
    if (it.rarity >= 4 && preview.filledLoops >= 3 && !it.aria) {
      it.aria = pick(this.rng, ARIAS).id;
      it.name = this.name(it);
    }

    this.g.player.recalc();
    this.g.onGearChanged();
    if (this.g.ui.motifMorph) {
      this.g.ui.motifMorph({
        fromIcon: it.icon || this.iconKey(it),
        motifIds: Object.keys(need),
        rarity: it.rarity,
        label: `Synthesized · Q${it.quality}` + (chosen.length ? ` · ${chosen.map((m) => m.trait).join(', ')}` : ''),
        kind: 'synth',
      });
    }
    return { ok: true, preview, transferred: chosen.map((m) => m.trait) };
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
