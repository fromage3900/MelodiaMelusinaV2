// Echo Lineage — Uma-style inheritance from cleared Resonance Rifts.
// Banks a residual Phrase on clear; next Recital can inherit Motif buffs.

import {
  ECHO_BASE_PASS, ECHO_PITY_STEP, ECHO_SUPPORT_ARIA, ECHO_SUPPORT_BLESS,
  ECHO_TIER_BONUS, ECHO_OSHI_BONUS, ECHO_MOTIF_POOL, AFFIX_BY_KEY, ELEMENT_STYLE,
  ARIA_BY_ID, BLESSINGS,
} from './design.js';
import { pick } from './util.js';

const BLESSING_BY_ID = Object.fromEntries(BLESSINGS.map((b) => [b.blessing_id, b]));

export function defaultLineage() {
  return {
    phrase: null,
    pity: 0,
    active: null,
    history: 0,
  };
}

export class Echo {
  constructor(game) {
    this.g = game;
    const pr = game.profile;
    if (!pr.echoLineage) pr.echoLineage = defaultLineage();
  }

  get lineage() { return this.g.profile.echoLineage; }

  ownedArias() {
    const arias = new Set();
    for (const it of Object.values(this.g.profile.equipment)) if (it?.aria) arias.add(it.aria);
    return arias;
  }

  supportList() {
    const arias = [...this.ownedArias()].map((id) => ARIA_BY_ID[id]?.name || id);
    const blessings = (this.g.profile.blessings || []).map((id) => BLESSING_BY_ID[id]?.display_name || id);
    const oshi = this.g.profile.oshiAria;
    return { arias, blessings, oshi: oshi ? (ARIA_BY_ID[oshi]?.name || oshi) : null };
  }

  /** Score Supports: equipped Arias + Blessings + oshi pin bias pass chance. */
  supportBonus() {
    const pr = this.g.profile;
    const arias = this.ownedArias();
    let b = arias.size * ECHO_SUPPORT_ARIA + (pr.blessings?.length || 0) * ECHO_SUPPORT_BLESS;
    if (pr.oshiAria && arias.has(pr.oshiAria)) b += ECHO_OSHI_BONUS;
    else if (pr.oshiAria) b += ECHO_OSHI_BONUS * 0.35; // pinned but not equipped — soft devotion
    return b;
  }

  passChance(tier = 1) {
    const L = this.lineage;
    if (!L.phrase) return 0;
    const base = ECHO_BASE_PASS + (L.pity || 0) + this.supportBonus() + Math.max(0, (tier || L.phrase.tier || 1) - 1) * ECHO_TIER_BONUS;
    return Math.min(0.92, base);
  }

  /**
   * Bank a Phrase after rift clear.
   * goalsCleared: recital micro-goals completed (spice Motifs / quality / pity).
   */
  bankFromRift(rift, inTime, goalsCleared = []) {
    const rng = Math.random;
    let extraMotifs = 0;
    let qualityBonus = 0;
    let pityBonus = 0;
    for (const g of goalsCleared) {
      if (g.spice === 'motif') extraMotifs++;
      else if (g.spice === 'quality') qualityBonus += 12;
      else if (g.spice === 'pity') pityBonus += 0.08;
    }
    const n = 1 + (rift.tier >= 3 ? 1 : 0) + (inTime ? 1 : 0) + extraMotifs;
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
    const supports = this.supportList();
    const quality = Math.min(100, 40 + rift.tier * 12 + (inTime ? 15 : 0) + qualityBonus);
    const L = this.lineage;
    const chanceAtBank = this.passChance(rift.tier + (inTime ? 1 : 0));
    const phrase = {
      tier: rift.tier,
      motifs,
      quality,
      inTime: !!inTime,
      at: Date.now(),
      goalsCleared: goalsCleared.map((g) => g.id),
      pedigree: {
        motifs: motifs.map((m) => ({ ...m })),
        quality,
        tier: rift.tier,
        supportsUsed: supports,
        passChanceAtBank: chanceAtBank,
        parentHistory: L.history || 0,
        goals: goalsCleared.map((g) => g.text || g.id),
      },
    };
    L.phrase = phrase;
    L.history = (L.history || 0) + 1;
    L.active = null;
    if (pityBonus) L.pity = (L.pity || 0) + pityBonus;
    return phrase;
  }

  rollInheritance(tier, blessing = null) {
    const L = this.lineage;
    L.active = null;
    if (!L.phrase || !L.phrase.motifs?.length) {
      return { passed: false, chance: 0, motifs: [], reason: 'none' };
    }
    let chance = this.passChance(tier);
    if (blessing?.kind === 'echo_chance') chance = Math.min(0.95, chance + (blessing.mult || 0));
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

  activeBuffs() {
    const act = this.lineage.active;
    if (!act?.motifs?.length) return null;
    const out = { dmg: 0, crit: 0, speed: 0, perfectms: 0, encore: 0, magic: 0, break: 0, hp: 0 };
    for (const m of act.motifs) {
      if (m.key in out) out[m.key] += m.v;
    }
    return out;
  }

  /** Consume active Echo Motifs for Phrase Recall skill. Returns multiplier. */
  consumeActiveForSkill() {
    const act = this.lineage.active;
    if (!act?.motifs?.length) return 1;
    const n = act.motifs.length;
    this.lineage.active = null;
    this.g.player.recalc();
    return 1.35 + n * 0.2;
  }

  clearActive() {
    this.lineage.active = null;
  }

  pedigreeHtml() {
    const ph = this.lineage.phrase;
    if (!ph?.pedigree) return '';
    const p = ph.pedigree;
    const motifs = (p.motifs || []).map((m) => `${m.key}+${m.v}`).join(' · ') || '—';
    const sup = p.supportsUsed || {};
    const oshi = sup.oshi ? ` · oshi ${sup.oshi}` : '';
    return `T${p.tier} Q${p.quality} · ${motifs} · hist ${p.parentHistory}${oshi} · banked @ ${Math.round((p.passChanceAtBank || 0) * 100)}%`;
  }
}
