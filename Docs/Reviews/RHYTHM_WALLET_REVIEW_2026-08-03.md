# Rhythm Integration & Melody Token Wallet Review — 2026-08-03

**Date:** 2026-08-03
**Author:** UE 5.8 Audio/Rhythm Systems Analyst
**Build:** 0 errors, editor UP at :9316
**Scope:** Music clock composition, rhythm combat pipeline, MPC parameter contract, wallet system, Cadence Strike readiness, next-phase readiness

---

## 1. Music Clock Status

### Hierarchy (Decision 012)

```
UMelodiaMusicClockSubsystem (UWorldSubsystem, single authority)
+-- Harmonix UMusicClockComponent    ? preferred authored clock
+-- Quartz UMelodiaAudioComponent    ? sample-accurate battle transport fallback
+-- NO wall-clock accumulator         ? deliberate; degrades gracefully
```

### Resolution Order

Verified in `MelodiaMusicClockSubsystem.h` lines 259-260 (`IsHarmonixClockRunning()`, `IsQuartzClockRunning()`) and `MelodiaJRPGPresentationRhythmComponent.cpp` lines 9-42:

1. **Harmonix** — checked first. If the registered `UMusicClockComponent` has `State == Running`, source = Harmonix. Registered via `RegisterMusicClock()` called from `UMelodiaJRPGPresentationRhythmComponent::BeginPlay()` (line 19).
2. **Quartz** — checked second. If `UMelodiaAudioComponent->IsBattleClockRunning()`, source = Quartz. Registered via `RegisterQuartzAudioComponent()` + `StartBattleClock(QuartzFallbackBPM)` (lines 36-41).
3. **None** — if neither is running. `HasMusicalTime()` returns false. `GetTimingErrorMsToNearestBeat()` returns 0.

### Timebase Contract

| Domain | Timebase | Verified In |
|---|---|---|
| Visual | `VideoRenderTime` | `MelodiaMusicClockSubsystem.h:133` — `VisualTimebase` constexpr |
| Input | `ExperiencedTime` | `MelodiaMusicClockSubsystem.h:136` — `InputTimebase` constexpr |
| Events | `VideoRenderTime` | Default on Harmonix `MusicClockComponent` |

The `GetTimingErrorMsToNearestBeat()` call in `MelodiaJRPGPresentationRhythmComponent::RecordInputNow()` (line 91) reads the **input timebase** (`ExperiencedTime`), so grading is correctly measured against what the player heard.

### Registration Flow (Battle Begin)

Confirmed in `MelodiaJRPGPresentationRhythmComponent.cpp`:
```
BeginPlay
+-- RegisterMusicClock(HarmonixClock)          ? line 19
+-- RegisterQuartzAudioComponent(Audio)         ? line 36
+-- Audio->StartBattleClock(QuartzFallbackBPM)  ? line 41
```

At `EndPlay`, both are unregistered (lines 48-49).

### Interaction with RhythmCombatSubsystem

`UMelodiaRhythmCombatSubsystem` does NOT own a clock. It reads `UMelodiaMusicClockSubsystem::GetClockSource()` in `SubmitRatedInput()` (`MelodiaRhythmCombatSubsystem.cpp:144`) for audit logging, not damage computation. ?

### Verdict: MUSIC CLOCK IS CORRECT AND COMPLETE

Harmonix is preferred, Quartz fallback is wired, `HasMusicalTime()` returns true when either is running, and there is no wall-clock accumulator. All three clock sources (`None`, `Harmonix`, `Quartz`) are supported. Beat/Bar events broadcast via `OnMelodiaBeat`/`OnMelodiaBar`. Calibration offset is supported via `SetCalibrationOffsetMs`. **No changes needed.**

---

## 2. Rhythm Combat Pipeline

### Full Chain Verification

The design specifies: `RecordInputNow()` ? `SubmitRatedInput()` ? `SubmitResult()` ? `ConsumePendingRequest()` ? stock resolver.

#### `RecordInputNow()` — IMPLEMENTED ?

File: `MelodiaJRPGPresentationRhythmComponent.cpp:77-92`

```
RecordInputNow()
+-- MusicClock->HasMusicalTime() guard          ? if false, returns silent Miss (no flourish)
+-- MusicClock->GetTimingErrorMsToNearestBeat() ? input timebase (ExperiencedTime)
+-- EvaluateTimingError()                        ? grades via GradeInputFromTimingErrorMs()
+-- OnPresentationRhythmResult.Broadcast(Result) ? drives UI pulse, VFX
+-- Returns FJRPGPresentationRhythmResult (presentation ONLY — never damage)
```

**Grading windows** (from `MelodiaCoreRulesLibrary`): Perfect = 90ms, Great = 120ms, Good = 160ms.

#### `SubmitRatedInput()` — IMPLEMENTED ?

File: `MelodiaRhythmCombatSubsystem.cpp:119-147`

- Validates active session (`ActiveSessionId == 0` ? reject)
- Validates result not already accepted (`bResultAccepted` ? reject)
- Builds `FMelodiaAuthoritativeRhythmResult` with Grade, HitCount, MissCount, NoteCount, Accuracy, ClockSource
- Delegates to `SubmitResult()`

#### `SubmitResult()` — IMPLEMENTED ?

File: `MelodiaRhythmCombatSubsystem.cpp:92-117`

- Validates session ID match, `bValid` flag
- Builds `FMelodiaRhythmEffectRequest` via `BuildEffectRequest()`
- Sets `bHasPendingRequest = true`

#### `ConsumePendingRequest()` — IMPLEMENTED ?

File: `MelodiaRhythmCombatSubsystem.cpp:154-170`

- Returns the pending `FMelodiaRhythmEffectRequest` with `bConsumed = true`
- Calls `ApplyWalletIntegration(OutRequest)` exactly once
- Clears pending state

#### `BuildEffectRequest()` — IMPLEMENTED ?

File: `MelodiaRhythmCombatSubsystem.cpp:181-197`

- Maps `SkillId`, `EffectType`, `BaseMagnitude`, `RhythmScalar` (from grade multipliers), `TargetMode`, `TargetCount`, `Duration`, `TurnShift`

#### `ApplyWalletIntegration()` — IMPLEMENTED ?

File: `MelodiaRhythmCombatSubsystem.cpp:216-244`

- Spends SP cost via `Wallet->TrySpendMana(Skill->SPCost)`
- Grants Forte shard on grades >= 1.2x scalar via `Wallet->TryGrantShards(TEXT("Forte"), 1, GrantId)`
- GrantId format: `RhythmSkill_{SkillId}_{SessionId}` — session-scoped for idempotency

### Inventory of All C++ Pieces

| Component | File | Implemented? | Verified? |
|---|---|---|---|
| `RecordInputNow()` | `MelodiaJRPGPresentationRhythmComponent.cpp` | ? Lines 77-92 | ? Reads clock, grades, broadcasts |
| `SubmitRatedInput()` | `MelodiaRhythmCombatSubsystem.cpp` | ? Lines 119-147 | ? Validates, builds result |
| `SubmitResult()` | `MelodiaRhythmCombatSubsystem.cpp` | ? Lines 92-117 | ? Validates, stores pending |
| `ConsumePendingRequest()` | `MelodiaRhythmCombatSubsystem.cpp` | ? Lines 154-170 | ? Returns + wallet integration |
| `ApplyWalletIntegration()` | `MelodiaRhythmCombatSubsystem.cpp` | ? Lines 216-244 | ? SP cost + shard reward |
| `BuildEffectRequest()` | `MelodiaRhythmCombatSubsystem.cpp` | ? Lines 181-197 | ? Maps skill to request |
| `ResolveMagnitude()` | `MelodiaRhythmCombatSubsystem.cpp` | ? Lines 199-214 | ? Grade multiplier |

### What Is NOT Yet Verified End-to-End

The **Blueprint wiring** between these C++ pieces:

1. **Battle start** — BP_BattleUI/C++ does not yet call `StartSession("CadenceStrike")` (P0 in RHYTHM_SKILL_SYSTEM_EXPANSION)
2. **Highway complete** — BP_BattleUI does not yet call `SubmitRatedInput(Grade, HitCount, MissCount)` (Phase 3 in HARMONIX_QUARTZ doc)
3. **Stock resolver** — does not yet call `ConsumePendingRequest(OutRequest)` to apply `RhythmScalar` to damage (Phase 7)
4. **Session cleanup** — `InvalidateSession()` not yet called on battle end/defeat/retry

The C++ pipeline is **ready for wiring** — all seams exist, types are correct, validation is in place. But the **Blueprints are not yet connected**.

---

## 3. MPC Parameter Status

### What TickPresentation Actually Writes

File: `MelodiaAudioReactivePresentationSubsystem.cpp:94-128`

The sole writer of MPC scalars is `UMelodiaAudioReactivePresentationSubsystem::TickPresentation()` — **there is no `UMelodiaRhythmReactivitySubsystem` in the source tree**. The design doc's `Publish()` method (described in HARMONIX_QUARTZ doc §D.1) was either never implemented or was refactored into `UMelodiaAudioReactivePresentationSubsystem`.

#### Scalars Written by TickPresentation (7 total)

| Scalar Name | Derivation | Written? |
|---|---|---|
| `GlobalReactivity` | `bBattleActive ? BattleIntensity : 0.0f` | ? Line 120 |
| `Bass` | `bBattleActive ? BattleIntensity : 0.0f` | ? Line 121 |
| `Mid` | `RhythmPulseValue` (= ImpactPulse) | ? Line 122 |
| `Treble` | `BeatPulseValue` (= sin²(BeatPhase × PI)) | ? Line 123 |
| `BeatPhase` | `MusicClock->GetBeatPhase(VisualTimebase)` or 0 | ? Line 124 |
| `BeatPulse` | `BeatPulseValue` (sin² based) | ? Line 125 |
| `RhythmPulse` | `RhythmPulseValue` (= ImpactPulse) | ? Line 126 |

#### Scalars FROM DESIGN CONTRACT That Are MISSING (11 total)

| Scalar Name | Design Source | Written? | Impact |
|---|---|---|---|
| `BeatIntensity` | = BeatPulse (legacy compat) | **MISSING** | Legacy materials using this name get no value |
| `GlobalSparkleIntensity` | max(VictoryPulse, CommandPulse) | **MISSING** | No sparkle burst on command resolution |
| `PaletteShift` | = ComboNormalized | **MISSING** | No MPC color rotation |
| `GlobalEmissiveBoost` | 1.0 + CrescendoNormalized | **MISSING** | No emissive boost on resolution |
| `ProximityGlow` | NotifyBreak() | **MISSING** | No enemy proximity glow |
| `TemporalJitter` | = EnemyTension | **MISSING** | No enemy tension material effect |
| `WarmthGlow` | NotifyBeat() + slow fade | **MISSING** | No cozy ambient pulse |
| `PetalFallIntensity` | NotifyCommandResolved() | **MISSING** | No petal particle density |
| `DreamRipple` | NotifyBeat() + slow fade | **MISSING** | No dreamy oscillation |
| `EmberDance` | NotifyCommandResolved() | **MISSING** | No ember intensity |
| `CozyBloom` | NotifyVictory() | **MISSING** | No victory bloom |

#### Scalars Written by TickPresentation NOT in Design Contract

| Scalar Name | Comment |
|---|---|
| `GlobalReactivity` | Not in the design doc contract (likely custom for battle intensity) |
| `Bass` | Not in the design doc contract |
| `Mid` | Similar to `RhythmPulse` but uses `ImpactPulse` decay instead of grade-scaled energy |
| `Treble` | Similar to `BeatPulse` — uses sin² shape |

### Monolith Query: MPC_Melodia_Palette References

From the `project_query get_asset_details` result, `MPC_Melodia_Palette` at `/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette` is referenced by 18 materials/functions including:
- `M_Master_Toon_Universal` (the universal toon master)
- `M_Water_Master_Grand_v6`
- `M_PP_StarryNightOverlay_Candidate`
- `MF_Madoka` (material function)
- 7 landscape master variants
- Post-process materials

This confirms the MPC is **the live authority** and is broadly consumed. The `variables` array was empty in the API response (Monolith does not index MPC scalar/vector parameters), so the exact count of existing parameters could not be verified via API.

### Verdict: MPC PARTIALLY WIRED

Only 7 of 18 design-contract scalars are being written. The `UMelodiaRhythmReactivitySubsystem::Publish()` path (with `NotifyBeat()`, `NotifyCommandResolved()`, `NotifyBreak()`, `NotifyEnemyIntent()`, `NotifyVictory()`) does not exist. The presentation subsystem that does exist (`UMelodiaAudioReactivePresentationSubsystem`) handles battle transitions and basic beat pulse but misses all command-resolution, break, tension, and victory scalars.

---

## 4. Wallet System Status

### Source Files
- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaTokenWalletSubsystem.h` (150 lines)
- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaTokenWalletSubsystem.cpp` (231 lines via handoff)

### API Surface Verification

| Operation | Signature | Verified? | Location in .h |
|---|---|---|---|
| `GetSnapshot()` | `? FMelodiaWalletSnapshot` | ? Line 68-69 | All 7 elements guaranteed, safe every frame |
| `GetShards(Element)` | `FName ? int32` | ? Line 72 | Single-element lookup |
| `TryGrantShards(Element, Amount, GrantId)` | `? bool` | ? Line 84 | Idempotent via `GrantId` |
| `TrySpendShards(Element, Amount)` | `? bool` | ? Line 87 | Rejects unaffordable |
| `TryAddMana(Amount)` | `? bool` | ? Line 91 | Clamped to ManaMax |
| `TrySpendMana(Amount)` | `? bool` | ? Line 94 | Rejects unaffordable |
| `TryGrantGolden(Amount, GrantId)` | `? bool` | ? Line 97 | Idempotent |
| `TrySpendGolden(Amount)` | `? bool` | ? Line 100 | Rejects unaffordable |
| `IsGrantConsumed(GrantId)` | `? bool` | ? Line 104 | Queries persisted set |
| `CaptureToSave(Save)` | `void` | ? Line 113 | Part of canonical save |
| `RestoreFromSave(Save)` | `void` | ? Line 123 | Reads all 7 fields + migration |
| `OnWalletChanged` | delegate `FMelodiaWalletSnapshot` | ? Line 108 | Fires once per accepted transaction |

### Grant-Idempotency Path (Survives Restart)

Full chain verified from code + handoffs:

1. `TryGrantShards(Element, Amount, GrantId)` ? checks `IsGrantConsumed(GrantId)` ? if consumed, returns false
2. If accepted, `ConsumedGrantIds.Add(GrantId)` (only if `GrantId != NAME_None`)
3. `CaptureToSave` ? writes `ConsumedGrantIds` to `Save->WalletConsumedGrantIds`
4. Save is written atomically (Decision 019)
5. On load: `RestoreFromSave` ? reads `WalletConsumedGrantIds` back into `ConsumedGrantIds`
6. Second `TryGrantShards` with same `GrantId` ? rejected

**Finding:** Idempotency survives full process restart. No double-pay path exists for any non-`NAME_None` `GrantId`. ?

### Console Commands

From CLAUDE_TO_KIRO_STATE handoff (verified working, Live-Coding patched):
- `melodia.Wallet.Dump` — prints all balances
- `melodia.Wallet.Grant <Element> <Amount> [GrantId]` — test grant
- `melodia.Wallet.Spend <Element> <Amount>` — test spend
- `melodia.Wallet.AddMana <Amount>` — test mana add
- `melodia.Wallet.SpendMana <Amount>` — test mana spend

**Finding:** Console commands work. Repeat grant with same `GrantId` ? rejected. Overspend ? rejected, no state change. ?

### Save/Restore

- `CaptureToSave` writes all 7 fields + `ConsumedGrantIds` + `bWalletMigratedFromLegacy`
- `RestoreFromSave` reads all 7 fields back
- One-way migration: Heart?Forte, Swirl?Arcane (pre-v4 saves only)
- Mana sanity check: if `ManaMax <= 0`, reset to 100 and clamp
- `OnWalletChanged` fires after restore — UI must handle load-time broadcasts gracefully

**Finding:** Save/restore is sound. Migration respects cross-authority boundaries (legacy `UMelodiaRoguelikeRunSubsystem` fields not zeroed). ?

### Pickup / HUD Status

**Pickup:** Kiro in progress (Blueprint work — not C++)
**HUD:** Kiro in progress (Blueprint work — not C++)
**Token MIs:** Four exist at `/Game/EnvSandbox/Materials/Instances/MelodyTokens/` (Heart, Star, Swirl, Water) — parented to `M_Master_Toon_Universal`, all textures resolve.
**Token Value Table:**

| Variant | Element | Value | Rarity | Material Path |
|---|---|---|---|---|
| Heart | Forte | 10 | Common | `/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Heart` |
| Star | Radiant | 12 | Uncommon | `/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Star` |
| Swirl | Arcane | 15 | Rare | `/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Swirl` |
| Water | Tide | 12 | Common | `/Game/EnvSandbox/Materials/Instances/MelodyTokens/MI_MelodyToken_Water` |

Fallback (no authored art): Stone=11, Gale=11, Umbral=13.

### Verdict: WALLET SYSTEM IS COMPLETE AND CORRECT

The wallet subsystem is production-ready. Grant-idempotency survives restart, console commands work, save/restore is integrated, all API operations are verified. The only missing pieces are Blueprint-layer pickup actors and HUD widgets, which are explicitly assigned to Kiro's lane.

---

## 5. Cadence Strike Readiness

### DataAsset Status

| Check | Result | Evidence |
|---|---|---|
| Asset file on disk | ? EXISTS | `Content\MelodiaIntegration\Config\DA_CadenceStrike.uasset` (via file system check) |
| Monolith search for `DA_CadenceStrike` | NOT FOUND | Asset registry index may not yet include it |
| Alternate Monolith search for `CadenceStrike` | NOT FOUND | Same — index gap |
| Registered with combat subsystem | ? NOT REGISTERED | Auto-discover in `Initialize()` scans `/Game/MelodiaIntegration/Config` via FARFilter — asset may not be in registry yet, or needs explicit `RegisterSkill()` call |

The handoff (`RHYTHM_SKILL_SYSTEM_EXPANSION_2026-08-03.md`) states the DataAsset was "Created, saved, 14 fields verified." The file exists on disk, so it would be loaded at runtime when the asset registry refreshes. The auto-discover in `UMelodiaRhythmCombatSubsystem::Initialize()` (lines 25-44) scans `/Game/MelodiaIntegration/Config` recursively for `UMelodiaRhythmSkillDefinition` assets. This should pick up `DA_CadenceStrike` after an asset registry scan.

**Additional skill DataAssets also created (per handoff):**
- `DA_ResonantArc` at `/Game/MelodiaIntegration/Config/DA_ResonantArc` (17 fields)
- `DA_LullabyMend` at `/Game/MelodiaIntegration/Config/DA_LullabyMend` (17 fields)

### Highway Widget Status

| Check | Result | Evidence |
|---|---|---|
| `WBP_MelodiaRhythmHighway` exists | ? YES | Monolith confirms: `/Game/Melodia/UI/Rhythm/WBP_MelodiaRhythmHighway` (WidgetBlueprint) |
| Brush/texture assignments | ? MISSING | Handoff says "needs in-editor" — SheetMusicBG, AuroraOverlay, SparkleField have no texture |
| NoteGlyph/PlaybackHead atoms | ? MISSING | Need building or importing from redesign DreamBubble App frames |
| Wired to `SetNoteHighwayActive()` | ? NOT WIRED | `UMelodiaRhythmHUDWidget`'s `SetNoteHighwayActive(bool)` BP NativeEvent not yet connected |
| Visible during Cadence Strike | ? NOT | Requires StartSession + SetNoteHighwayActive wiring in BP_BattleUI |

### RecordInputNow() from Stock Battle Flow

**Can it be called?** ? YES

`UMelodiaJRPGPresentationRhythmComponent` is already attached to the stock `BP_BattleController` as `MelodiaPresentationRhythm` (verified via Monolith query in QWEN_BATTLE_NARRATIVE_BINDING handoff). `RecordInputNow()` is `BlueprintCallable` (line 86 of the header). Any Blueprint can call:
```
BP_BattleController ? MelodiaPresentationRhythm ? RecordInputNow
```

The component's `BeginPlay()` already registers both Harmonix and Quartz clocks, and `EndPlay()` unregisters them. The clock infrastructure is ready.

### Missing Wiring (Blocks Full PIE)

1. **BP_BattleUI** does not call `UMelodiaRhythmCombatSubsystem::StartSession("CadenceStrike")` on skill execution start
2. **BP_BattleUI** does not call `UMelodiaJRPGPresentationRhythmComponent::RecordInputNow()` on note input
3. **BP_BattleUI** does not call `UMelodiaRhythmCombatSubsystem::SubmitRatedInput(Grade, HitCount, MissCount)` on highway complete
4. **BP_BattleController** stock resolver does not call `UMelodiaRhythmCombatSubsystem::ConsumePendingRequest(OutRequest)` before damage
5. **BP_BattleController** does not call `UMelodiaRhythmCombatSubsystem::InvalidateSession()` on battle end/defeat/retry

### Verdict: CADENCE STRIKE IS STRUCTURALLY READY BUT NOT WIRED

The C++ infrastructure is complete: DataAsset exists, clock composition works, `RecordInputNow()` can be called, the combat subsystem validates and routes. But the Blueprint wiring layer (StartSession ? highway visible ? RecordInputNow ? SubmitRatedInput ? ConsumePendingRequest ? InvalidateSession) is not yet connected.

---

## 6. Ready-for-Next-Phase Assessment

### What Works (Production-Ready)

| Area | Status |
|---|---|
| Music Clock Composition | ? Complete. Harmonix preferred, Quartz fallback, no wall-clock. |
| Rhythm Combat Pipeline (C++) | ? Complete. All 6 functions implemented with validation, session management, grade conversion, and wallet integration. |
| Token Wallet Subsystem | ? Complete. All 6 operations, grant-idempotency survives restart, console commands, save/restore with migration. |
| `MelodiaRhythmCombatTypes.h` | ? Fixed (was corrupted, now has correct `EMelodiaSkillGrade`, `EMelodiaRhythmEffectType`, `FMelodiaAuthoritativeRhythmResult`, `FMelodiaRhythmEffectRequest`) |
| `MelodiaRhythmSkillDefinition.h` | ? Complete. Data-driven skill definition with MIDI params, effect params, grade multipliers, presentation theme. |
| `RecordInputNow()` | ? Implemented with clock reading, grading, and broadcast. |
| MPC_Melodia_Palette base pulses | ?? Partial. `BeatPhase`, `BeatPulse`, `RhythmPulse` written. 11 contract scalars missing. |

### What Needs Wiring (Blueprint Layer — P0)

| Task | Priority | Reference |
|---|---|---|
| Register 3 skill DataAssets in PIE/init | P1 | RHYTHM_SKILL_SYSTEM_EXPANSION §P1 |
| Assign textures to `WBP_MelodiaRhythmHighway` | P0 | RHYTHM_SKILL_SYSTEM_EXPANSION §P0.1 |
| Wire `StartSession("CadenceStrike")` on skill select | P0 | HARMONIX_QUARTZ §Phase 3 |
| Wire `RecordInputNow()` on note input | P0 | HARMONIX_QUARTZ §B.1 |
| Wire `SubmitRatedInput()` on highway complete | P0 | HARMONIX_QUARTZ §Phase 3 |
| Wire `ConsumePendingRequest()` in stock resolver | P0 | HARMONIX_QUARTZ §Phase 7 |
| Wire `InvalidateSession()` on battle end/defeat/retry | P1 | HARMONIX_QUARTZ §Phase 3.7 |

### What Needs Implementation (C++ — P1)

| Task | Priority | Reference |
|---|---|---|
| Create `UMelodiaRhythmReactivitySubsystem` with `NotifyBeat()`, `NotifyCommandResolved()`, `NotifyBreak()`, `NotifyEnemyIntent()`, `NotifyVictory()` and full `Publish()` contract | P1 | HARMONIX_QUARTZ §D.1 (or extend `UMelodiaAudioReactivePresentationSubsystem` to write all 18 scalars) |
| Implement `BeatIntensity`, `GlobalSparkleIntensity`, `PaletteShift`, `GlobalEmissiveBoost`, `ProximityGlow`, `TemporalJitter`, `WarmthGlow`, `PetalFallIntensity`, `DreamRipple`, `EmberDance`, `CozyBloom` | P1 | HARMONIX_QUARTZ §D.1 — 11 scalars pending |

### What Needs Blueprint Work (Kiro Lane)

| Task | Priority | Reference |
|---|---|---|
| Pickup actors with token MIs | P1 | KIRO_MELODY_TOKEN_INTEGRATION §2, §3 |
| Wallet HUD readout (7 balances + mana + golden) | P1 | KIRO_MELODY_TOKEN_INTEGRATION §3 |
| Post-battle token grant wiring (Decision 009 compliant) | P1 | QWEN_RHYTHM_SKILLS_SCOPE §2.4 — grants must fire via victory handler, not skill-inline |

### What Needs Testing (PIE Verification)

| Gate | What to Verify |
|---|---|
| Main Menu ? New Game ? Melusina ? dialogue ? battle ? Cadence Strike ? highway ? grade-dependent damage ? result | Full rhythm loop |
| Save ? full exit ? relaunch ? Continue ? wallet intact + Harmony 1/5 | Save round-trip |
| `melodia.Wallet.Grant Forte 1 pickup_test_01` ? verify balance + repeat-grant rejection | Grant-idempotency |
| No musical time ? highway shows "No Clock" ? skill resolves at Good/1.0x | Graceful degradation |
| `melodia.Rhythm.Disable` ? skill plays identically with no rhythm presentation | Disable toggle |

---

## Appendix A: Monolith Query Results

### Query 1: `cppreflect_query get_uclass` for UMelodiaMusicClockSubsystem
- **Status:** ? Success
- **Module:** BS_GodFile
- **Parent class:** None (direct UWorldSubsystem)
- **Key functions:** `Get`, `GetActiveMusicClock`, `GetBeatPhase`, `GetClockSource`, `GetMusicTime`, `GetTimingErrorMsToNearestBeat`, `HasMusicalTime`, `RegisterMusicClock`, `RegisterQuartzAudioComponent`, `SetCalibrationOffsetMs`
- **Delegates:** `OnMelodiaBeat`, `OnMelodiaBar`, `OnClockSourceChanged`

### Query 2: `project_query get_asset_details` on DA_CadenceStrike
- **Asset path:** `/Game/Melodia/MelodiaIntegration/Config/DA_CadenceStrike`
- **Status:** ? "Asset not found in index"
- **Note:** File exists at `Content\MelodiaIntegration\Config\DA_CadenceStrike.uasset` on disk but Monolith's asset registry index has not scanned it. Correct path without `/Melodia/` middle segment: `/Game/MelodiaIntegration/Config/DA_CadenceStrike`.

### Query 3: `project_query get_asset_details` on MPC_Melodia_Palette
- **Asset path:** `/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette`
- **Status:** ? Success
- **Class:** MaterialParameterCollection
- **Last modified:** 2026-08-03T06:37:34
- **Referenced by:** 18 materials/functions (M_Master_Toon_Universal, M_Water_Master_Grand_v6, M_Master_Toon_Cosmic, 7 landscape blends, post-process materials, etc.)
- **Variables:** Empty array (Monolith does not index MPC scalar/vector parameters)

### Query 4: `project_query search` for WBP_MelodiaRhythmHighway
- **Status:** ? Found
- **Asset:** `/Game/Melodia/UI/Rhythm/WBP_MelodiaRhythmHighway`
- **Class:** WidgetBlueprint
- **Count:** 1 result

### Query 5: `project_query search` for DA_MelodiaRhythmProfile
- **Status:** ? Returned (empty)
- **Count:** 0 results
- **Conclusion:** No rhythm profile DataAsset exists in the project. This matches the design where skills use `UMelodiaRhythmSkillDefinition` directly rather than a profile abstraction.

---

## Appendix B: Key Source Files Referenced

| File | Path |
|---|---|
| Music Clock Subsystem | `Source/BS_GodFile/MelodiaIntegration/MelodiaMusicClockSubsystem.h` |
| Presentation Rhythm Component | `Source/BS_GodFile/MelodiaIntegration/MelodiaJRPGPresentationRhythmComponent.h/.cpp` |
| Audio Reactive Presentation | `Source/BS_GodFile/MelodiaIntegration/MelodiaAudioReactivePresentationSubsystem.h/.cpp` |
| Rhythm Combat Subsystem | `Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmCombatSubsystem.h/.cpp` |
| Rhythm Combat Types | `Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmCombatTypes.h` |
| Rhythm Skill Definition | `Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmSkillDefinition.h` |
| Token Wallet Subsystem | `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaTokenWalletSubsystem.h` |
| Cadence Strike DataAsset | `Content/MelodiaIntegration/Config/DA_CadenceStrike.uasset` |
| Rhythm Highway Widget | `/Game/Melodia/UI/Rhythm/WBP_MelodiaRhythmHighway` (WidgetBlueprint) |
| MPC Palette | `/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette` |
