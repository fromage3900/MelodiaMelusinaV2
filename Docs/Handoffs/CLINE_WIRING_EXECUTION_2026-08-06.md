# Cline Wiring Execution Handoff — 2026-08-06

**From:** Cline (wiring blueprint expert)
**To:** Subagent(s) with Monolith MCP access (`:9316`)
**Editor:** UE 5.8, Monolith live. **Run `monolith` + `it-is-unreal` together per QUEUE.md #9.**
**Ground truth:** All API names below were verified against live source this session — do not trust the older
handoffs (DeepSeek/Kimi) where they conflict; the corrections are flagged inline.

---

## ⚠️ Two corrections to prior handoffs (read first)

1. **Grade enum is `EMelodiaSkillGrade`** (Miss / Good / Great / Perfect) — there is **no "Poor" grade**.
   The DeepSeek handoff's "Poor=0.5" multiplier is wrong. Grade multipliers live in the skill DataAsset
   (`UMelodiaRhythmSkillDefinition`), not in the subsystem.
2. **`UMelodiaRhythmHUDWidget` is a NativePaint HUD with NO `BindWidget` UPROPERTYs.**
   The Kimi/DeepSeek task "mark `JudgementText`/`ComboText`/`ClockSourceText` as Is Variable so C++ can bind
   them" is based on a **false premise** — this C++ class renders the highway/vitals/combat text via Slate
   `NativePaint`, not UMG TextBlocks. The real API is `SetJudgment(FText)`, `SetHUDMode(EMelodiaHUDMode)`,
   `SetNoteHighwayActive(...)`, `SetEnemyVitals`, `SetPartyVitals`, `SetSkillPoints`, `SetUltimateGauge`,
   `SetEnemyBreakGauge`, `ShowActionPrompt`, `SetBattlePhaseBanner`, `PushFloatingCombatText`,
   `TriggerDamageFlash`, `ShowBattleStatus`, `DoPulse`, `TriggerSparkleBurst` — all `BlueprintNativeEvent`
   (a BP subclass can override them). **Do not spend time marking UMG widgets as variables; there is nothing
   to bind.**

---

## Item 1 — Bake the Monolith enum-pin fix + run one persona terminal path

### 1a. Bake the enum-pin fix into the running editor (Live Coding)

The fix is an **uncommitted working-tree change** in 3 Monolith source files:

| File | Change |
|---|---|
| `Plugins/Monolith/Source/MonolithBlueprint/Private/MonolithBlueprintInternal.h` | `PC_Enum` → `PC_Byte` + `PinSubCategoryObject=UEnum` for `enum:` base types; reader now emits `enum:<Name>` for byte-backed enum pins |
| `Plugins/Monolith/Source/MonolithCore/Public/MonolithPropertyAccessReader.h` | same reader-side `enum:` emission |
| `Plugins/Monolith/Source/MonolithUI/Private/MonolithUIRegistryActions.cpp` | `PC_Enum` → `PC_Byte` for `TEnumAsByte<EFoo>` member variables |

**Why it matters:** `PC_Enum` is reserved for C++-only `enum class`; `CreatePrimitiveProperty` has no `PC_Enum`
branch and would lower the pin to a plain `FIntProperty`, breaking delegate signature checks. `PC_Byte` +
enum subcategory compiles to the same `FEnumProperty` the native signature declares.

**Steps (per CURRENT_STATE.md's documented Live-Coding pattern):**
1. Confirm the editor is running and Monolith `:9316` responds.
2. Call `editor:trigger_build` (Live Coding). Wait for `patch_applied=true`.
3. **Verify the patch took** — this is the same trap as the PSO fix: Live Coding patches the running process
   only; it is NOT baked into the on-disk DLL. If the editor restarts before a real rebuild, re-run
   `editor:trigger_build` after every fresh launch.
4. Sanity-check: create a delegate with an enum param via Monolith and confirm the pin type reads back as
   `enum:<Name>` (not `byte`/`int`).

### 1b. Run one persona terminal path (PIE)

After the bake, drive one full terminal path to prove the battle-and-return half (currently **zero PIE proof**):

```
dialogue → allowlisted encounter request → JRPG battle (Melusina) → typed result → Quill resumes exactly once → exploration
```

- The battle-start request `OnBattleRequested` is now bound by **only** `UMelodiaExternalJRPGBridgeSubsystem`
  (the duplicate `UMelodiaBattleAdapterSubsystem` was deleted 2026-08-06 — verified). Confirm exactly **one**
  battle starts.
- `ClassifyJRPGBattleResult` (cpp:20-45) loads `/Game/TurnBasedJRPGTemplate/Blueprints/Battle/E_BattleResult`;
  name-matches playerwon/victory/win→Victory, enemywon/defeat/lose/loss→Defeat, flee/fled/escape→Fled, else
  Unavailable.
- On start failure, `AbortPendingBattle("no tagged JRPG encounter could start")` replaces
  `CompleteBattle(Unavailable)` (cpp:136-149); `AbortPendingBattle` at `MelodiaNarrativeSubsystem.cpp:271`.
- Watch for: exactly-one `OnJRPGBattleStarted`, a typed `CompleteBattle`, and `resumeQuill` firing **once**.

---

## Item 2 — PIE walk: prove the battle-and-return loop end-to-end

Single PIE walk driving `melodia:battle`. Assertions:

1. **Exactly one** battle-start (no duplicate `OnBattleRequested`).
2. **Typed** `CompleteBattle` (Victory/Defeat/Fled/Unavailable) — no fabricated result on start failure.
3. **`resumeQuill` fires exactly once** per terminal result.
4. World null-guard holds (no crash if the world is torn down mid-broadcast).

Use the 8-section checklist at `Docs/PIE_VERIFICATION_CHECKLIST_2026-08-03.md` as the walk skeleton
(dialogue → traversal → battle → save/load → menu → rhythm → route). Report per-section PASS/FAIL.

---

## Item 3 — Rhythm wiring seams (corrected)

The C++ rhythm stack is build-green and registered. Three seams remain editor-side:

### 3a. Cadence Strike → rhythm game (`BP_BattleUI` EventGraph)

Flow (after stock `OnUnitHasEnoughMP` passes for the skill):
```
OnSkillSelected(skillId="CadenceStrike")
  → Get UMelodiaRhythmCombatSubsystem (static Get(WorldContextObject))
  → StartSession("CadenceStrike") → returns sessionId (0 if skill not registered)
  → IF sessionId > 0:
      → show WBP_Battle_Rhythm (SetHUDMode / SetNoteHighwayActive)
      → push rhythm input context
      → hide stock command menu
  → ELSE: fall through to stock skill
```

### 3b. Rhythm → stock resolver hookup

On rhythm complete:
```
OnRhythmComplete(Grade, HitCount, MissCount)
  → SubmitRatedInput(EMelodiaSkillGrade Grade, int32 HitCount, int32 MissCount) → bool accepted
  → IF accepted AND HasPendingRequest():
      → ConsumePendingRequest(FMelodiaRhythmEffectRequest& OutRequest)
      → feed OutRequest into stock damage/heal resolver (route by EffectType)
  → restore stock menu
```
`FMelodiaRhythmEffectRequest` fields (verified): `bConsumed`, `SkillId`, `SessionId`, `EffectType`
(Damage/Crit/Heal/RemoveDebuff/Debuff/None), `BaseMagnitude`, `RhythmScalar`, `TargetMode`, `TargetCount`,
`Duration`, `TurnShift`, `Scalar`, `Magnitude`, `TargetId`.

Route by `EffectType`:
- **Damage/Crit:** multiply stock damage by `RhythmScalar`
- **Heal/RemoveDebuff:** multiply stock heal by `RhythmScalar`
- **Debuff:** apply stock debuff with `Duration` from request

### 3c. Text widget bindings — **DO NOT DO** (see correction #2)

The `JudgementText`/`ComboText`/`ClockSourceText` "Is Variable" task is based on a false premise. The HUD is
NativePaint. If the highway text is static, the fix is in the C++ `SetJudgment`/`SetNoteHighwayActive` path or
the BP subclass override — not UMG widget flags.

---

## Reference: verified C++ API (all BlueprintCallable/Pure)

| Function | Class | Signature |
|---|---|---|
| `Get` | `UMelodiaRhythmCombatSubsystem` | `static UMelodiaRhythmCombatSubsystem* Get(const UObject* WorldContextObject)` |
| `RegisterSkill` | `UMelodiaRhythmCombatSubsystem` | `void RegisterSkill(UMelodiaRhythmSkillDefinition* InSkill)` |
| `FindSkill` | `UMelodiaRhythmCombatSubsystem` | `UMelodiaRhythmSkillDefinition* FindSkill(FName SkillId) const` |
| `StartSession` | `UMelodiaRhythmCombatSubsystem` | `int32 StartSession(FName SkillId)` → 0 if not registered |
| `SubmitResult` | `UMelodiaRhythmCombatSubsystem` | `bool SubmitResult(const FMelodiaAuthoritativeRhythmResult& InResult)` |
| `SubmitRatedInput` | `UMelodiaRhythmCombatSubsystem` | `bool SubmitRatedInput(EMelodiaSkillGrade Grade, int32 HitCount, int32 MissCount)` |
| `HasPendingRequest` | `UMelodiaRhythmCombatSubsystem` | `bool HasPendingRequest() const` |
| `ConsumePendingRequest` | `UMelodiaRhythmCombatSubsystem` | `bool ConsumePendingRequest(FMelodiaRhythmEffectRequest& OutRequest)` |
| `InvalidateSession` | `UMelodiaRhythmCombatSubsystem` | `void InvalidateSession()` |
| `GetActiveSessionId` | `UMelodiaRhythmCombatSubsystem` | `int32 GetActiveSessionId() const` |
| `SetJudgment` | `UMelodiaRhythmHUDWidget` | `void SetJudgment(const FText& NewText)` (BlueprintNativeEvent) |
| `SetHUDMode` | `UMelodiaRhythmHUDWidget` | `void SetHUDMode(EMelodiaHUDMode NewMode)` (BlueprintNativeEvent) |
| `SetNoteHighwayActive` | `UMelodiaRhythmHUDWidget` | `void SetNoteHighwayActive(bool bActive, const TArray<FMelodiaHighwayNote>& Notes, float BeatPosition, float ScrollBeatsAhead)` |

**Enums:** `EMelodiaSkillGrade` = Miss/Good/Great/Perfect. `EMelodiaRhythmEffectType` = Damage/Crit/Heal/
RemoveDebuff/Debuff/None.

---

## Loose ends (not assigned here, tracked in `_TASK_QUEUE.md`)
- Packaged build launch test (only open packaging item).
- 12 P0 foundation gates (all runtime-unproven).
- Wallet restart-idempotence test (process restart, not in-memory).
- 4 of 5 orphaned `.pyc` reconstructions are wrong — do not run.
- Travel authority deadlock (MelodiaCore 7 `OpenLevel` calls) — **design decision, not a wiring task**.
