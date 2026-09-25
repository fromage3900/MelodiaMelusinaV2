// Judging taps against the audible beat, combo, Crescendo dynamics and Encore.
// Windows, grade multipliers, combo bonus, Crescendo gains and Encore gains
// are the rules JSON values (generated/ue_data.js).

import { RULES, GRADE, DYNAMICS, MODIFIERS } from './design.js';
import { clamp } from './util.js';

export class Rhythm {
  constructor(game) {
    this.g = game;
    this.combo = 0;
    this.best = 0;
    this.crescendo = 0;
    this.encore = 0;
    this.encoreUntil = -1;
    this.lastHitBeat = -99;
    this.perfectRun = 0;
    this.dynIndex = 0;
    this.dyn = DYNAMICS[0];
    this.ffReached = false;
    this.lastErr = 0;
  }

  get encoreMax() { return RULES.ultimate.max; }
  get encoreActive() { return this.encoreUntil >= this.g.beatIndex; }

  windows() {
    const w = RULES.rhythm.windows_ms;
    const sc = this.g.windowScale();
    const bonus = this.g.player.stats.perfectms;
    const perfect = w.perfect * sc + bonus;
    const great = Math.max(perfect + 8, w.great * sc + bonus * 0.5);
    const good = Math.max(great + 8, w.good * sc);
    return { perfect, great, good };
  }

  // Map a tap (performance.now ms) to the beat the player heard.
  judge(perfMs) {
    const a = this.g.audio;
    const t = a.audibleTime(perfMs) - this.g.profile.settings.offsetMs / 1000;
    const b = a.nearestBeat(t);
    if (!b) return { grade: 'Good', err: 0, beat: null, downbeat: false, mult: 1 };
    const err = (t - b.time) * 1000;
    let grade;
    if (this.encoreActive) grade = 'Perfect';
    else {
      const W = this.windows(), ae = Math.abs(err);
      grade = ae <= W.perfect ? 'Perfect' : ae <= W.great ? 'Great' : ae <= W.good ? 'Good' : 'Miss';
    }
    this.lastErr = err;
    return { grade, err, beat: b, downbeat: b.inBar === 0, mult: this.multiplier(grade) };
  }

  // UMelodiaCoreRulesLibrary::GetRhythmCombatMultiplier, same numbers.
  multiplier(grade) {
    const r = RULES.rhythm;
    const raw = GRADE[grade].mult;
    const bonus = grade === 'Miss' ? 0 : this.combo * r.combo_bonus_per_hit;
    return clamp(raw + bonus, r.grade_multipliers.miss, r.max_combat_multiplier);
  }

  register(res, hits = 0, showLabel = true) {
    const g = this.g, P = g.player, grade = res.grade;
    if (grade === 'Miss') {
      if (this.combo >= 8) g.overlay.text(P.pos.x, P.pos.y + 3.2, P.pos.z, 'combo lost', '#8d8698', 13, { life: 0.8 });
      this.combo = 0;
      this.perfectRun = 0;
      this.crescendo = Math.max(0, this.crescendo - 12);
    } else {
      this.combo++;
      if (this.combo > this.best) this.best = this.combo;
      if (this.combo > g.profile.stats.bestCombo) g.profile.stats.bestCombo = this.combo;
      this.crescendo = Math.min(RULES.crescendo.max, this.crescendo + GRADE[grade].crescendo);
      this.lastHitBeat = res.beat ? res.beat.index : g.beatIndex;
    }
    if (!this.encoreActive && hits > 0 && grade !== 'Miss') {
      let gain = grade === 'Perfect' ? RULES.ultimate.gain_perfect : RULES.ultimate.gain_per_hit;
      gain *= 1 + P.stats.encore;
      if (P.hasBuff('ResonantFocus')) gain *= MODIFIERS.ResonantFocus.value;
      gain *= g.encoreGainScale();
      const was = this.encore;
      this.encore = Math.min(this.encoreMax, this.encore + gain);
      if (was < this.encoreMax && this.encore >= this.encoreMax) g.ui.toast('ENCORE ready!', 'gold');
    }
    if (grade === 'Perfect') {
      g.profile.stats.perfects++;
      g.bountyEvent('perfects', 1);
      this.perfectRun++;
      if (P.stats.arias.has('HarmonyShield')) P.shield = Math.min(P.stats.maxHp * 0.3, P.shield + P.stats.maxHp * 0.03);
      if (P.stats.arias.has('SkyboundRefrain') && this.perfectRun % 4 === 0) g.skyboundStrike();
    }
    this.updateDyn();
    if (showLabel) {
      g.ui.gradeFlash(grade, res.err);
    }
    g.audio.grade(grade);
  }

  updateDyn() {
    let idx = 0;
    for (let i = 0; i < DYNAMICS.length; i++) if (this.crescendo >= DYNAMICS[i].at) idx = i;
    if (idx !== this.dynIndex) {
      if (idx > this.dynIndex) this.g.ui.dynamicsUp(DYNAMICS[idx]);
      this.dynIndex = idx;
      this.dyn = DYNAMICS[idx];
      this.g.audio.setIntensity(this.g.musicIntensity());
    }
    if (idx === DYNAMICS.length - 1 && !this.ffReached) { this.ffReached = true; this.g.bountyEvent('crescendo', 1); }
    if (idx < DYNAMICS.length - 2) this.ffReached = false;
  }

  onBar(beat) {
    const g = this.g;
    const idle = g.beatIndex - this.lastHitBeat;
    if (idle > beat.meter && !this.encoreActive) {
      this.crescendo = Math.max(0, this.crescendo - 8);
      if (idle > beat.meter * 2 && !g.player.stats.comboKeeper) this.combo = 0;
    }
    this.updateDyn();
  }
}
