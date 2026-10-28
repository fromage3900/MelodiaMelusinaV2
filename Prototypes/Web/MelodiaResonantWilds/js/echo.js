// Echo Lineage — Uma-style inheritance from cleared Resonance Rifts.
// Banks a residual Phrase on clear; next Recital can inherit Motif buffs.

import {
  ECHO_BASE_PASS, ECHO_PITY_STEP, ECHO_SUPPORT_ARIA, ECHO_SUPPORT_BLESS,
  ECHO_TIER_BONUS, ECHO_MOTIF_POOL, AFFIX_BY_KEY, ELEMENT_STYLE,
} from './design.js';
import { pick } from './util.js';

export function defaultLineage() {
  return {
    phrase: null,      // last banked phrase { tier, motifs: [{key,v,e?}], quality, at }
    pity: 0,           // banked pass chance
    active: null,      // currently applied inheritance for this rift
    history: 0,        // total phrases banked
  };
}

export class Echo {
  constructor(game) {
    this.g = game;
    const pr = game.profile;
    if (!pr.echoLineage) pr.echoLineage = defaultLineage();
  }

  get lineage() { return this.g.profile.echoLineage; }

  /** Score Supports: equipped Arias + owned Blessings bias pass chance. */
  supportBonus() {
    const pr = this.g.profile;
    const arias = new Set();
    for (const it of Object.values(pr.equipment)) if (it?.aria) arias.add(it.aria);
    return arias.size * ECHO_SUPPORT_ARIA + (pr.blessings?.length || 0) * ECHO_SUPPORT_BLESS;
  }

  passChance(tier = 1) {
    const L = this.lineage;
    if (!L.phrase) return 0;
    const base = ECHO_BASE_PASS + (L.pity || 0) + this.supportBonus() + Math.max(0, (tier || L.phrase.tier || 1) - 1) * ECHO_TIER_BONUS;
    return Math.min(0.92, base);
  }

  /** Bank a Phrase after rift clear. Motifs scale with tier / in-time clear. */
  bankFromRift(rift, inTime) {
    const rng = Math.random;
    const n = 1 + (rift.tier >= 3 ? 1 : 0) + (inTime ? 1 : 0);
    const motifs = [];
    const keys = ECHO_MOTIF_POOL.slice();
    for (let i = 0; i < n && keys.length; i++) {
      const key = keys.splice(Math.floor(rng() * keys.length), 1)[0];
      const A = AFFIX_BY_KEY[key];
      let v;
      if (A.flat) v = Math.max(1, Math.round(A.flat * (4 + rift.tier * 2) * (0.7 + rng() * 0.5)));
      else v = Math.max(1, Math.round(A.min + (A.max - A.min) * (0.35 + rng() * 0.55) * (0.85 + rift.tier * 0.05)));
      const m = { key, v };
      if (A.element) m.e = pick(rng, Object.keys(ELEMENT_STYLE));
      motifs.push(m);
    }
    const phrase = {
      tier: rift.tier,
      motifs,
      quality: Math.min(100, 40 + rift.tier * 12 + (inTime ? 15 : 0)),
      inTime: !!inTime,
      at: Date.now(),
    };
    const L = this.lineage;
    L.phrase = phrase;
    L.history = (L.history || 0) + 1;
    L.active = null;
    return phrase;
  }

  /**
   * Roll inheritance when entering a rift.
   * Returns { passed, chance, motifs } — failures bank pity.
   */
  rollInheritance(tier) {
    const L = this.lineage;
    L.active = null;
    if (!L.phrase || !L.phrase.motifs?.length) {
      return { passed: false, chance: 0, motifs: [], reason: 'none' };
    }
    const chance = this.passChance(tier);
    if (Math.random() < chance) {
      L.active = {
        motifs: L.phrase.motifs.map((m) => ({ ...m })),
        fromTier: L.phrase.tier,
        chance,
      };
      L.pity = 0;
      return { passed: true, chance, motifs: L.active.motifs };
    }
    L.pity = (L.pity || 0) + ECHO_PITY_STEP;
    return { passed: false, chance, motifs: [], pity: L.pity };
  }

  /** Flat buffs applied while a lineage Motif set is active in a rift. */
  activeBuffs() {
    const act = this.lineage.active;
    if (!act?.motifs?.length) return null;
    const out = { dmg: 0, crit: 0, speed: 0, perfectms: 0, encore: 0, magic: 0, break: 0, hp: 0 };
    for (const m of act.motifs) {
      if (m.key in out) out[m.key] += m.v;
    }
    return out;
  }

  clearActive() {
    this.lineage.active = null;
  }
}
