# JRPG Mechanics Contract Sheet — 2026-08-03

**Purpose:** Catalog every core JRPG mechanic from the TurnBasedJRPG template, what's integrated into Melodia, and what's missing/blocked. This is the "what did we inherit from the JRPG systems" reference.
**Authority:** `Docs/MELODIA_UE58_INTEGRATION_ARCHITECTURE_2026-07-26.md` (authority map), `_VERTICAL_SLICE_SCOPE.md`, `_TASK_QUEUE.md`.
**Legend:** ✅ = integrated & working · 🟡 = partial / needs PIE · ⏳ = missing / blocked · 🔒 = out of scope (deferred)

---

## 1. Party & Progression

| Mechanic | Template Provides | Melodia Integration | Status |
|----------|-------------------|---------------------|--------|
| Party roster | ✅ `BP_JRPGSaveGame` party units | ✅ `UMelodiaJRPGPartyBootstrapSubsystem` | ✅ |
| Leveling / XP | ✅ | ✅ `FMelodiaQuestDef.RewardXP` | 🟡 PIE |
| Turn order / AV | ✅ stock controller | 🔒 MelodiaCore AV (GS-003) quarantined | 🔒 |
| Party member swap | ✅ | ⏳ not exposed | 🟡 |

## 2. Battle & Combat

| Mechanic | Template Provides | Melodia Integration | Status |
|----------|-------------------|---------------------|--------|
| Battle scheduling | ✅ stock battle controller | ✅ `UMelodiaBattleAdapterSubsystem` | ✅ |
| Turn / target / damage resolution | ✅ stock | ✅ via adapter seams | ✅ |
| Skill execution | ✅ stock skills | ✅ `BP_MelusinaPetalCadence`, `BP_SirSkyboundRefrain` | ✅ |
| Rhythm-modified combat | 🔒 (new) | ✅ `UMelodiaRhythmCombatSubsystem` (new) | 🟡 new |
| Battle UI | ✅ stock `BP_BattleUI` | ✅ hosts `MelodiaNoteHighway` | 🟡 |
| Victory/Defeat/Fled result matrix | ✅ | ⏳ PIE gate §3 | ⏳ |

## 3. Damage & Effects

| Mechanic | Template Provides | Melodia Integration | Status |
|----------|-------------------|---------------------|--------|
| Damage formula | ✅ stock | ✅ reduces via stock | ✅ |
| Status effects (buff/debuff) | ✅ stock | ✅ `BP_Resonance` (buff) | ✅ |
| Conditional bonus (Resonance) | ✅ stock rules | ⏳ Skybound Refrain bonus | ⏳ |
| Rhythm scalar → damage | 🔒 (new) | ✅ `FMelodiaRhythmEffectRequest` | 🟡 new |

## 4. Inventory & Equipment

| Mechanic | Template Provides | Melodia Integration | Status |
|----------|-------------------|---------------------|--------|
| Inventory | ✅ stock | ✅ via adapter | ✅ |
| Equipment | ✅ stock | ✅ Persona equipment maps to stock API | ✅ |
| Outfit identity | 🔒 (new) | 🔒 post-slice | 🔒 |

## 5. Quests

| Mechanic | Template Provides | Melodia Integration | Status |
|----------|-------------------|---------------------|--------|
| Quest flow | ✅ stock | ✅ `UMelodiaQuestManagerBase` | ✅ |
| Quest-gated markers | ✅ | ✅ Persona gate predicate | ✅ |
| NPC → quest runtime | ✅ | 🟡 NPC binding pending PIE | 🟡 |

## 6. Save / Load

| Mechanic | Template Provides | Melodia Integration | Status |
|----------|-------------------|---------------------|--------|
| Canonical save slot | ✅ `BP_JRPGSaveGame` | ✅ save schema v2 | ✅ |
| Narrative record in save | 🔒 (new) | ✅ `FMelodiaNarrativeRecord` v2 | ✅ |
| Process-restart load | ✅ | ⏳ PIE gate §4 | ⏳ |
| Wallet persistence | 🔒 (new) | ✅ `UMelodiaTokenWalletSubsystem` | ✅ |
| Wallet restart-idempotence | 🔒 (new) | ⏳ PIE gate §4.7 | ⏳ |

## 7. Dialogue & Narrative

| Mechanic | Template Provides | Melodia Integration | Status |
|----------|-------------------|---------------------|--------|
| Dialogue UI | 🟡 template modals only | ✅ QuillScript + native adapters | ✅ |
| Branches / labels / conditions | 🔒 (Quill) | ✅ QuillScript | ✅ |
| Narrative intent allowlist | 🔒 (new) | ✅ `UMelodiaNarrativeSubsystem` | ✅ |

## 8. Input & Movement

| Mechanic | Template Provides | Melodia Integration | Status |
|----------|-------------------|---------------------|--------|
| Exploration movement | ✅ | ✅ `UMelodiaTraversalComponent` | ✅ |
| Jump / glide | ✅ | ✅ (input-gated) | ✅ |
| Input context stack | 🔒 (new) | ✅ `UMelodiaInputContextSubsystem` | ✅ |
| Battle input parity | ✅ | ⏳ PIE gate §3.2 | ⏳ |

---

## Integration Gaps (what's likely "missing" from the initial JRPG systems)

1. **Battle result matrix** — Victory/Defeat/Fled/unavailable each resume/abort Quill exactly once. **Not PIE-proven.** (gate §3)
2. **Process-restart save/load** — the biggest integration gap. Continue/Load disabled until proven. (gate §4)
3. **Skybound Refrain conditional bonus** — the last co-op mechanic; Resonance-triggered bonus not wired.
4. **NPC → dialogue runtime binding** — NPCs authored/read back, but the runtime NPC→Quill binding is open.
5. **Stock skill resolver entry points** — the 08-03 doc flagged "exact stock skill damage/heal/SP/turn resolver entry points require live Blueprint graph audit." The rhythm subsystem produces a request but nothing feeds it into the stock resolver yet.
6. **MelodiaCore AV/turn-override (GS-003)** — quarantined; the stock JRPG is the turn authority. This is a deliberate deferral, not a bug.

## What's genuinely missing vs. deliberately deferred

- **Genuinely missing (needs work):** result matrix PIE, process-restart save/load, Skybound bonus, NPC binding, stock resolver hookup.
- **Deliberately deferred (do not build):** MelodiaCore AV/turn authority, wardrobe platform, roguelike, second combat framework, ACFU.

---

**End of Contract Sheet**
