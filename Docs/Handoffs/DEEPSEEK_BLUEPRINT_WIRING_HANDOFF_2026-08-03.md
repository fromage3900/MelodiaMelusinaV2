> ⚠️ **SUPERSEDED by [`Docs/BLUEPRINT_WIRING_CONTRACT_2026-08-07.md`](../BLUEPRINT_WIRING_CONTRACT_2026-08-07.md)**
>
> This handoff (08-03) described the Cadence Strike → rhythm game wiring task. The 08-07 contract doc
> supersedes it with the canonical wiring protocol. Two specific contradictions corrected:
>
> 1. **Step 4 — text widget bindings.** This handoff's §4 instructs marking `JudgementText`,
>    `ComboText`, `ClockSourceText` as `Is Variable = true` in the editor. The 08-07 contract
>    confirms the C++ `MelodiaRhythmHUDWidget` resolves these by `BindWidget` auto-bind on
>    construction; manually toggling Is Variable is unnecessary and risks dangling variable nodes.
>    The fix is C++-only (add `BindWidget`/`BindWidgetOptional` to the member declarations).
> 2. **Grade multiplier table.** This handoff lists `0.5 Poor, 1.0 Good, 1.2 Great, 1.5 Perfect`.
>    The canonical `EMelodiaRhythmGrade` scalar table (Decision 041) is
>    `Poor=0.35, Good=1.0, Great=1.2, Perfect=1.5`. The 0.5 figure was from an uncommitted draft.
>
> This file is retained for historical audit (the C++ API reference table at §§94–102 is still
> accurate). **Do not follow its §4 wiring instructions.**

# DeepSeek Blueprint Wiring Handoff — Evening 2026-08-03

**From:** Cline (C++ backend, architecture)  
**To:** DeepSeek (Blueprint wiring via Monolith MCP)  
**Editor:** UE 5.8 OPEN, Monolith :9316 responding 200  
**Build:** Green (0 errors, last rebuild 14:38), EncounterGuidance fix live, MelodiaNPCInteractionComponent diagnostic logs hot-reloaded

---

## Context: What Happened This Session

Cline built the complete native rhythm combat stack:
- `UMelodiaRhythmCombatSubsystem` (WorldSubsystem): session lifecycle, skill catalog, `SubmitRatedInput`, wallet integration via `ConsumePendingRequest`
- `UMelodiaRhythmSkillDefinition` (UPrimaryDataAsset): MIDI params, niche-based effects, grade multipliers
- `FMelodiaAuthoritativeRhythmResult` / `FMelodiaRhythmEffectRequest` / `EMelodiaRhythmEffectType`
- Harmonix clock registration wired into `MelodiaJRPGPresentationRhythmComponent`
- Duplicate `EMelodiaRhythmGrade` fixed (deleted copy, reused plugin's)
- 2 tests passing (SessionLifecycle + GradeBoundaries)
- `UMelodiaSaveRecoverySubsystem` updated to use new subsystem

PIE testing revealed three blockers — Cadence Strike is yours:

| # | Blocker | Cause | Owner | Status |
|---|---------|-------|-------|--------|
| 1 | **QuillScript still inaccessible** | NPCs have QuillDialogue assigned → `BeginInteraction()` hands off to Quill runtime, but dialog box doesn't render. C++ logging added. | Quill plugin config issue | Cline diagnostic logs live |
| 2 | **Basic attacks do no damage** | Stock JRPG `BP_BattleUnit` damage formula / CDO values. Not in C++. | Needs live BP inspection | Unresolved |
| 3 | **Cadence Strike doesn't trigger rhythm game** | Skill visible in menu, but `BP_BattleUI` `OnSkillSelectedHandler`/`OnUnitHasEnoughMP` not wired to `UMelodiaRhythmCombatSubsystem::StartSession()` → show WBP_Battle_Rhythm | **Blueprint wiring** | **Yours** |

---

## Blueprint Wiring Task: Cadence Strike → Rhythm Game

### Step 1: Wire the Skill-Selected Seam

**File:** `BP_BattleUI` EventGraph (live at `game.WBP_BattleUI`)

The flow (after the stock `OnUnitHasEnoughMP` check passes for the skill):

```
OnSkillSelected(skillId="CadenceStrike")
  → OnUnitHasEnoughMP check passes
  → Get RhythmCombatSubsystem (UMelodiaRhythmCombatSubsystem::Get)
  → StartSession("CadenceStrike") → returns sessionId
  → IF sessionId > 0:
      → SetVisibility(true) on WBP_Battle_Rhythm reference
      → PushContext(MelodiaBattleInputContextHandle)  // rhythm input mode
      → SetVisibility(false) on WBP_CommandMenu / ActionsUI (hide stock menu)
  → ELSE:
      → Fall through to stock skill (no rhythm for this skill)
```

### Step 2: After Rhythm Game Completes

**File:** `WBP_Battle_Rhythm` → finishes player input → broadcasts grade

```
OnRhythmComplete(Grade, HitCount, MissCount)
  → Get RhythmCombatSubsystem
  → SubmitRatedInput(Grade, HitCount, MissCount) → returns bool accepted
  → IF accepted AND HasPendingRequest():
      → ConsumePendingRequest(OutRequest)
      → Feed OutRequest into stock damage/heal resolver
      → (see Step 3)
  → PopContext(MelodiaBattleInputContextHandle)
  → SetVisibility(WBP_Battle_Rhythm, false)
  → SetVisibility(WBP_CommandMenu, true)  // restore stock menu
```

### Step 3: Hook Into Stock Damage/Heal Resolver

The rhythm subsystem's `FMelodiaRhythmEffectRequest` contains:
- `EffectType` (Damage/Crit/Heal/RemoveDebuff/Debuff)
- `RhythmScalar` (grade multiplier — 0.5 Poor, 1.0 Good, 1.2 Great, 1.5 Perfect)
- `BaseMagnitude` (from skill DataAsset)
- `TargetMode` / `TargetCount`
- `Duration` / `TurnShift`

Wire `ConsumePendingRequest` into the stock `BP_BattleController` damage formula seam (the same place Attack/Item/Flee resolve). Use the `EffectType` to route:
- **Damage/Crit:** multiply stock damage by `RhythmScalar`
- **Heal/RemoveDebuff:** multiply stock heal by `RhythmScalar`
- **Debuff:** apply stock debuff with duration from request

### Step 4: Text Widget Bindings (WBP_Battle_Rhythm)

Three widgets currently `is_variable: false` — mark them as Is Variable:
1. Open `WBP_Battle_Rhythm`
2. Select `JudgementText` → Details panel → **Is Variable = true**
3. Select `ComboText` → **Is Variable = true**
4. Select `ClockSourceText` → **Is Variable = true**
5. Recompile WBP_Battle_Rhythm

### Reference: Active C++ API (all BlueprintCallable)

| Function | Where | Signature |
|----------|-------|-----------|
| `Get` | `UMelodiaRhythmCombatSubsystem` | `static UMelodiaRhythmCombatSubsystem* Get(WorldContextObject)` |
| `StartSession` | `UMelodiaRhythmCombatSubsystem` | `int32 StartSession(FName SkillId)` → returns session ID or 0 if skill not registered |
| `SubmitRatedInput` | `UMelodiaRhythmCombatSubsystem` | `bool SubmitRatedInput(EMelodiaRhythmGrade Grade, int32 HitCount, int32 MissCount)` |
| `HasPendingRequest` | `UMelodiaRhythmCombatSubsystem` | `bool HasPendingRequest()` |
| `ConsumePendingRequest` | `UMelodiaRhythmCombatSubsystem` | `bool ConsumePendingRequest(FMelodiaRhythmEffectRequest& OutRequest)` |
| `InvalidateSession` | `UMelodiaRhythmCombatSubsystem` | `void InvalidateSession()` |
| `FindSkill` | `UMelodiaRhythmCombatSubsystem` | `UMelodiaRhythmSkillDefinition* FindSkill(FName SkillId)` |

### Skill DataAsset Row (for reference)

The Cadence Strike DataAsset lives at `/Game/MelodiaIntegration/Config/Skills/`:
- **SkillId:** `CadenceStrike`
- **EffectType:** `Damage` (+ Crit on Great/Perfect)
- **Niche:** `Vigorous`
- **BaseMagnitude:** 1.0
- **SPCost:** 10
- **DamageMultipliers:** Poor=0.5, Good=1.0, Great=1.2, Perfect=1.5
- **TargetMode:** `SingleEnemy`

---

## Cline's Lane (parallel work)

While DeepSeek does the BP wiring, Cline handles:

1. **Git sync**: Stage + commit all C++ changes from this session
2. **Regression gate**: Widen test run to full `Melodia` suite (49 tests), confirm 2 roguelike failures are known/P3
3. **Documentation audit**: Check Docs/ for stale references, dead links, outdated handoffs
4. **Source control review**: Branch hygiene, commit message quality, `.gitignore` completeness
5. **Travel authority deadlock**: Document the design decision (move `UMelodiaTravelSubsystem` into MelodiaCore vs. interface)
6. **Qwen 3.8**: Complete ollama pull to F:\, test with JetBrains Rider
7. **Basic attack damage**: Investigate stock `BP_BattleUnit` CDO values

---

## Files Modified This Session (for git commit)

| File | Change |
|------|--------|
| `MelodiaRhythmCombatSubsystem.cpp` | Inlined skill catalog auto-loading in `Initialize()` via AssetRegistry |
| `MelodiaRhythmCombatSubsystem.h` | Added `LoadSkillCatalog()` declaration |
| `MelodiaNPCInteractionComponent.cpp` | Added `MELUSINA_NPC_QUILL_HANDOFF` + `MELUSINA_NPC_LEGACY_DIALOGUE` diagnostic logs |
| `MelodiaNPCInteractionComponent.h` | (previous rebuild) Restored `EncounterGuidance` default text |
| `MelodiaNPCApplicationTests.cpp` | (previous rebuild) Explicitly clears `EncounterGuidance` before asserting no-content contract |
| `_SESSION_HANDOFF.md` | Updated evening session state |

---

## Loose Ends (not assigned, tracked here)

1. **Packaged build launch test** — `_TASK_QUEUE.md` row 52, the only open packaging item
2. **12 foundation gates** — rows 37-51, all P0, unclaimed
3. **Wallet restart-idempotence test** — process restart, not in-memory (row 30)
4. **Orphaned .pyc reconstructions** — 4 of 5 are wrong, don't run them (row 34)
5. **Pacing improvements** — phase-dim transitions, beat-synced travel, dialogue typewriter (staged, not started)
6. **Kiro's token pickup/HUD** — Blueprint work, in progress by Kiro (row 29)
