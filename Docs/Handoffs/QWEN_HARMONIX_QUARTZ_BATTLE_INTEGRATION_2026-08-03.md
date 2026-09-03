# Harmonix+Quartz Battle Rhythm Integration — Cadence Strike Vertical Slice

**Date:** 2026-08-03
**Author:** UE 5.8 Audio/Rhythm Systems Engineer
**Status:** Design locked; ready for implementation
**Scope:** Harmonix/Quartz clock composition, Cadence Strike wiring, MIDI import requirements, MPC parameter contract, implementation order

---

## A. Clock Composition Architecture

### Hierarchy (Decision 012)

```
UMelodiaMusicClockSubsystem  (UWorldSubsystem, single authority)
├── Harmonix UMusicClockComponent    ← preferred authored clock
├── Quartz UMelodiaAudioComponent    ← sample-accurate battle transport fallback
└── NO wall-clock accumulator         ← deliberate; degrades gracefully
```

**Resolution order** (MelodiaMusicClockSubsystem.cpp:202-217):

1. If the registered `UMusicClockComponent` has `State == Running`, source = `Harmonix`. Its authored tempo map provides bar numbers, total beat count, time signature, and section markers. The clock is registered via `RegisterMusicClock()` (MelodiaMusicClockSubsystem.h:143), typically from `UMelodiaJRPGPresentationRhythmComponent::BeginPlay()`.

2. Else if the registered `UMelodiaAudioComponent->IsBattleClockRunning()`, source = `Quartz`. It provides beat phase (0..1), beat-in-bar (fractional), and BPM. No authored tempo map — `Bar`, `TotalBeats`, and `SecondsPerBeat` are derived from the single start-BPM. Quartz beat-edge detection runs in the ticker callback (MelodiaMusicClockSubsystem.cpp:386-398).

3. Else source = `None`. `HasMusicalTime()` is false. `GetTimingErrorMsToNearestBeat()` returns 0. `ConsumePendingRequest` on the combat subsystem must still serve a valid request at the fallback grade (e.g. Good/1.0x) — the grade must not silently become Perfect.

### Timebase Contract

| Domain | Timebase | Used For |
|---|---|---|
| Visual | `VideoRenderTime` | Note highway scroll, UI pulses, MPC animations, material beat reactivity |
| Input | `ExperiencedTime` | Timing error measurement (`GetTimingErrorMsToNearestBeat`), grading |
| Events | `VideoRenderTime` | Harmonix `BeatEvent`/`BarEvent` (default on the component) |

The two timebases are the **same** at zero latency and diverge under audio buffer load. Using `ExperiencedTime` for grading is what makes the feel tight — the player's input is measured against what they actually heard, not where the video renderer happens to be.

### Registration Flow (Battle Begin)

```
BP_BattleUI BeginPlay
└── UMelodiaJRPGPresentationRhythmComponent::BeginPlay()
    ├── RegisterMusicClock(HarmonixClock)    → UMelodiaMusicClockSubsystem
    ├── RegisterQuartzAudioComponent(Audio)   → UMelodiaMusicClockSubsystem
    └── Audio->StartBattleClock(QuartzFallbackBPM)
```

At EndPlay, both are unregistered (MelodiaJRPGPresentationRhythmComponent.cpp:44-55).

### Interaction with RhythCombatSubsystem

`UMelodiaRhythmCombatSubsystem` does NOT own a clock. It reads `UMelodiaMusicClockSubsystem::GetClockSource()` when building the authoritative result from `SubmitRatedInput()` (MelodiaRhythmCombatSubsystem.cpp:144). This is the only place the clock source touches the combat authority — the clock source is recorded in the result for audit/logging, not for damage computation.

---

## B. Cadence Strike Skill Wiring

### B.1 Session Lifecycle

```
Stock UI: Player selects Cadence Strike
  │
  ▼
UMelodiaRhythmCombatSubsystem::StartSession("CadenceStrike")
  ├── Clears previous session + pending request (InvalidateSession)
  ├── Looks up skill definition from SkillCatalog
  ├── Sets ActiveSkillId = "CadenceStrike"
  ├── ActiveSessionId = NextSessionId++
  └── Returns ActiveSessionId
  │
  ▼
Note highway becomes visible (reuses WBP_Battle_Rhythm host in BP_BattleUI)
  ├── Notes scheduled from skill's MIDI pattern (IntroBeats + ActiveBeats)
  └── Scroll driven by Harmonix/Quartz beat position
  │
  ▼
Player hits notes → RecordInputNow()
  │
  ├── UMelodiaJRPGPresentationRhythmComponent::RecordInputNow()
  │   ├── Calls GetTimingErrorMsToNearestBeat() on input timebase
  │   ├── Evaluates timing error against RhythmWindows (P=90/Gt=120/Gd=160ms)
  │   ├── Grades → EMelodiaRhythmGrade
  │   ├── Broadcasts OnPresentationRhythmResult (UI pulse, VFX)
  │   └── Returns FJRPGPresentationRhythmResult
  │
  └── This path is PRESENTATION ONLY (Decision 011/016)
  │
  ▼
On skill execution complete:
  │
  ├── UI calls UMelodiaRhythmCombatSubsystem::SubmitRatedInput(Grade, Hits, Misses)
  │   ├── Validates session active + result not already accepted
  │   ├── Builds FMelodiaAuthoritativeRhythmResult
  │   ├── Converts via BuildEffectRequest() → FMelodiaRhythmEffectRequest
  │   └── Stores in PendingRequest; sets bHasPendingRequest = true
  │   └── This is the ONLY seam where presentation feeds combat authority
  │
  ▼
Stock resolver calls UMelodiaRhythmCombatSubsystem::ConsumePendingRequest(OutRequest)
  ├── Returns FMelodiaRhythmEffectRequest to stock resolver
  ├── ApplyWalletIntegration (SP cost + shard reward)
  └── Clears pending state
```

### B.2 MPC Parameter Flow on Beat Hit

When a note is hit and graded:

```
RecordInputNow()
  │
  ├── MusicClock->GetTimingErrorMsToNearestBeat()     ← input timebase
  ├── GradeInputFromTimingErrorMs()                     ← EMelodiaRhythmGrade
  │
  ▼
UMelodiaRhythmReactivitySubsystem::NotifyBeat(BPM, BeatPhase)
  ├── Signal.BeatPulse = 1.0f  (decays each tick)
  ├── Signal.BeatPhase = 0..1
  ├── Signal.WarmthGlow += 0.3
  ├── Signal.DreamRipple += 0.2
  │
  ▼
Publish() → MPC_Melodia_Palette writes:
  ├── BeatPulse         → Material beat reactivity, UI pulse amplitude
  ├── BeatPhase         → Lane scroll position, sine-driven glow oscillation
  ├── BeatIntensity     = BeatPulse (redundant, kept for legacy materials)
  ├── RhythmPulse       = CommandEnergy (set below)
  ├── WarmthGlow        → Ambient world glow, cozy materials
  └── DreamRipple       → Subtle scene oscillation
```

On command resolution (after `SubmitRatedInput` is accepted):

```
UMelodiaRhythmReactivitySubsystem::NotifyCommandResolved(Grade, Energy, Combo, Crescendo, Element)
  ├── Signal.CommandEnergy    = energy (1.0 for Perfect, 0.5 for Good, etc.)
  ├── Signal.ComboNormalized  = 0..1
  ├── Signal.CommandPulse     = 1.0f (decays)
  ├── Signal.LastRhythmGrade  = grade enum
  ├── Signal.RhythmElement    = element byte
  ├── Signal.PetalFallIntensity += ComboNormalized * 0.5
  ├── Signal.EmberDance      += CrescendoNormalized * 0.4
  │
  ▼
Publish() → MPC_Melodia_Palette additional writes:
  ├── RhythmPulse         = CommandEnergy
  ├── GlobalSparkleIntensity = max(VictoryPulse, CommandPulse)
  ├── PaletteShift        = ComboNormalized    (drives MPC color rotation)
  ├── GlobalEmissiveBoost = 1.0 + CrescendoNormalized
  └── PetalFallIntensity / EmberDance
```

On grade judgment displayed in the HUD:

```
UMelodiaRhythmHUDWidget::SetJudgment("Perfect" / "Great" / "Good" / "Miss")
  ├── LastJudgmentText = grade text
  ├── LastPulseTime = GetHUDTimeSeconds()
  ├── DoPulse() → BeatCountForBassProxy every 2nd beat → LastBassPulseTime
  │
  ▼
NativePaint renders grade texture (GradePerfect/Great/Good/Miss) at center
  └── Fades out over 1.5s with scale-up animation
```

### B.3 RecordInputNow() → Grade → ConsumePendingRequest

The full wiring chain:

1. **Input capture**: `UMelodiaJRPGPresentationRhythmComponent::RecordInputNow()` (line 77-92) reads the music clock's timing error on the **input timebase** and grades it. Returns `FJRPGPresentationRhythmResult` (grade + presentation scalar — NEVER damage).

2. **Presentation feedback**: The same component broadcasts `OnPresentationRhythmResult`, which drives:
   - `UMelodiaRhythmHUDWidget::SetJudgment` (text + texture)
   - `UMelodiaRhythmHUDWidget::DoPulse` (bass pulse proxy)
   - `UMelodiaRhythmHUDWidget::NotifyPerfectHit` (NoteTrailIri cue on F-b motion channel)

3. **Authoritative request**: After the highway completes, the battle UI calls:
   ```cpp
   UMelodiaRhythmCombatSubsystem::SubmitRatedInput(Grade, HitCount, MissCount)
   ```
   This converts the presentation grade (`EMelodiaRhythmGrade`) to the skill grade (`EMelodiaSkillGrade` — same enum values, declared in MelodiaRhythmCombatTypes.h) and builds the authoritative effect request.

4. **Stock consumption**: The stock skill resolver calls:
   ```cpp
   Subsystem->ConsumePendingRequest(OutRequest)
   ```
   This returns the `FMelodiaRhythmEffectRequest` with:
   - `SkillId`, `EffectType`, `BaseMagnitude`
   - `RhythmScalar` = grade multiplier (Perfect=1.45, Great=1.20, Good=1.00, Miss=0.70)
   - `TargetMode`, `TargetCount`, `Duration`, `TurnShift`

5. **Wallet integration** fires exactly once on consume:
   - SP cost deducted via `Wallet->TrySpendMana(Skill.SPCost)`
   - Shard reward on grades >= 1.2x scalar via `Wallet->TryGrantShards("Forte", 1, GrantId)`

### B.4 Grade Table (from melodia_rules.json + initial balance)

| Grade | Timing Error | Damage Mult | Heal Mult | SP/Resource | Turn Shift |
|---|---|---|---|---|---|
| Perfect | ≤ 90ms | 1.45 | 1.35 | 1.25 | Yes (MaxTurnShift) |
| Great | ≤ 120ms | 1.20 | 1.15 | 1.10 | Yes (MaxTurnShift) |
| Good | ≤ 160ms | 1.00 | 1.00 | 1.00 | No |
| Miss | > 160ms | 0.70 | 0.70 | 0.75 | No |

---

## C. MIDI Import Requirements

### C.1 What MIDI asset is needed

Each rhythm skill requires a Harmonix `UMidiFile` asset (imported from Standard MIDI File `.mid`).

For **Cadence Strike** (first skill to prove the pipeline):

| Property | Value |
|---|---|
| **Asset path** | `/Game/MelodiaIntegration/MIDI/CadenceStrike_Pattern.CadenceStrike_Pattern` |
| **Tempo** | 128 BPM (matching QuartzFallbackBPM default, adjustable per skill) |
| **Time signature** | 4/4 |
| **Key** | C minor (default, matches `UMelodiaRhythmSkillDefinition::MusicalKey`) |
| **Length** | 2 bars intro (empty) + 4 bars active = 6 bars total |
| **Tracks** | 1 track, 1 channel |
| **Notes** | Quarter-note density (2 notes per beat = 8th notes), F4 key |
| **Lane mapping** | MIDI note 53 (F3) = Lane 0 (left/F), 60 (C4) = Lane 1 (center/J), 67 (G4) = Lane 2 (right/K) |

### C.2 MIDI Import Procedure

1. Author the `.mid` file externally (Reaper, MuseScore, FL Studio) or generate programmatically:
   - Tempo event at tick 0: 128 BPM
   - 4/4 time signature at tick 0
   - No pitch bends, no CC, no program changes
   - Notes on a single track
2. Import into UE5.8: Content Browser → Import → select `.mid` file
   - UE5.8 with Harmonix installed imports `.mid` as `UMidiFile`
   - Place at `/Game/MelodiaIntegration/MIDI/`
3. Assign the asset to the skill definition's `PatternAsset` (TSoftObjectPtr<UObject>)
4. The note scheduler reads `UMidiFile->GetSongMaps()->GetBeatMap()` for beat positions and `GetNoteTrack(0)->GetNoteEvents()` for note list

### C.3 Quartz Fallback for MIDI-less Skills

Skills without an authored `PatternAsset` fall back to procedural pattern generation using `NoteDensity`, `ActiveBeats`, and `IntroBeats` from the skill definition. The scheduler generates equidistant notes on Lane 0. This allows proving the pipeline without MIDI authoring.

### C.4 Harmonix vs Quartz Note Scheduling

| Aspect | Harmonix | Quartz |
|---|---|---|
| Note positions | Beatmap from MIDI file | Procedural from BPM + density |
| Beat events | `UMusicClockComponent::BeatEvent` | `UMelodiaAudioComponent::GetSongBeatPosition()` |
| TotalBeats | Known from authored tempo map | Not available (beat-in-bar only) |
| Bar numbers | Known from MIDI | None |
| Scheduling | `GetMusicalTimebase(beats)` maps beats to seconds | `60/BPM * beats` derived |

The note scheduler in `UMelodiaRhythmExecutionComponent` (MelodiaCore plugin) reads `GetCurrentBeatPosition()` which already supports both paths via `bUseQuartzClock` (line 116). During battle, the execution component's beat position should come from `UMelodiaMusicClockSubsystem` rather than from its own accumulator.

---

## D. MPC Parameter Contract

### D.1 MPC_Melodia_Palette Published Scalars

Source: `UMelodiaRhythmReactivitySubsystem::Publish()` (MelodiaRhythmReactivitySubsystem.cpp:256-271)

| Scalar Name | Written By | Read By | Range | Description |
|---|---|---|---|---|
| `BeatPulse` | `NotifyBeat()` + decay | Battle UI lane glow, highway background pulse, material DreamPulseAmp, Iridescence, ParallaxStrength | 0..1 | Peaks 1.0 on beat, decays per tick |
| `BeatPhase` | `NotifyBeat()` | Lane scroll position, sine-driven glow, meter oscillation | 0..1 | 0..1 within current beat |
| `BeatIntensity` | = BeatPulse | Legacy materials (pre-MPC rename compat) | 0..1 | Same as BeatPulse |
| `RhythmPulse` | `NotifyCommandResolved()` | Skill resolution VFX, combo glow, arena feel | 0..1 | = CommandEnergy (grade-scaled) |
| `GlobalSparkleIntensity` | max(VictoryPulse, CommandPulse) | Sparkle particles, grade halo, note hit VFX | 0..1 | Burst on command resolution |
| `PaletteShift` | `NotifyCommandResolved()` | Material color rotation, UI palette cycling | 0..1 | = ComboNormalized |
| `GlobalEmissiveBoost` | `NotifyCommandResolved()` | Emissive materials, skill glow | 1.0..2.0 | 1.0 + CrescendoNormalized |
| `ProximityGlow` | `NotifyBreak()` | Enemy proximity glow, break state | 0..1 | Peaks on break |
| `TemporalJitter` | `NotifyEnemyIntent()` | Enemy tension material, temporal instability | 0..1 | = EnemyTension |
| `WarmthGlow` | `NotifyBeat()` + slow fade | Cozy world materials, ambient warmth | 0..1 | Gentle pulse on each beat |
| `PetalFallIntensity` | `NotifyCommandResolved()` | Petal particle system density | 0..1 | Responds to combo |
| `DreamRipple` | `NotifyBeat()` + slow fade | Dreamy world oscillation, water ripple | 0..1 | Subtle atmospheric shift |
| `EmberDance` | `NotifyCommandResolved()` | Ember particle intensity | 0..1 | Responds to crescendo |
| `CozyBloom` | `NotifyVictory()` | Victory bloom, warm ambient light | 0..1 | Flares on victory |

### D.2 Consumers

| Consumer | Scalars Read | Effect |
|---|---|---|
| **Battle UI** (BP_MelodiaBattleUI) | BeatPulse, BeatPhase, RhythmPulse | Highway lane glow pulse, hit line shimmer, combo meter rotation |
| **Note highway** (WBP_Battle_Rhythm via MelodiaRhythmHUDWidget) | (reads beat from MusicClock directly) | Note scroll position, resolved note color (already in C++) |
| **Grade halo** (GradePerfect/Great/Good/Miss textures) | GlobalSparkleIntensity | Halo opacity on judgment display |
| **Enemy material** (M_Master_Toon_Universal) | BeatPulse → DreamPulseAmp, Iridescence | Enemy pulses on beat when registered via `RegisterReactiveMeshComponent` |
| **Arena environment materials** | WarmthGlow, PetalFallIntensity, DreamRipple, EmberDance, CozyBloom | World reactivity |
| **Sparkle particles** | GlobalSparkleIntensity | Burst on Perfect hit |
| **Camera post-process** | BeatPulse, TemporalJitter | Subtle beat-synced camera bob, tension shake |
| **OSC endpoints** (TouchDesigner) | BeatPulse, BeatPhase, ComboNormalized, CrescendoNormalized, CommandEnergy, VictoryPulse | External visualizer / stream reactivity |

### D.3 OSC Contract

UDP to `localhost:9000` (MelodiaRhythmReactivitySubsystem.cpp:37-38):

| OSC Address | Value | Rate |
|---|---|---|
| `/rhythm/beat_pulse` | Signal.BeatPulse | Every Publish() |
| `/rhythm/beat_phase` | Signal.BeatPhase | Every Publish() |
| `/rhythm/combo_normalized` | Signal.ComboNormalized | On command resolve + decay |
| `/rhythm/crescendo_normalized` | Signal.CrescendoNormalized | On command resolve + decay |
| `/rhythm/command_energy` | Signal.CommandEnergy | On command resolve + decay |
| `/rhythm/victory_pulse` | Signal.VictoryPulse | On victory |

---

## E. Implementation Order — Cadence Strike Vertical Slice

### Phase 1: Fix MelodiaRhythmCombatTypes.h (Day 1)

The file at `Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmCombatTypes.h` currently contains the wrong content (copy of `MelodiaJRPGPresentationRhythmComponent.cpp`). It must be rewritten with the canonical type declarations:

1. `enum class EMelodiaSkillGrade : uint8` (same values as `EMelodiaRhythmGrade` — Miss, Good, Great, Perfect)
2. `enum class EMelodiaRhythmEffectType : uint8` (Damage, Crit, Heal, RemoveDebuff, Debuff, Shield, Speed, Resource)
3. `struct FMelodiaAuthoritativeRhythmResult` with: `bValid`, `SessionId`, `Grade`, `HitCount`, `MissCount`, `NoteCount`, `Accuracy`, `ClockSource`
4. `struct FMelodiaRhythmEffectRequest` with: `SkillId`, `SessionId`, `EffectType`, `BaseMagnitude`, `RhythmScalar`, `TargetMode`, `TargetCount`, `Duration`, `TurnShift`, `bConsumed`

**Note:** The test file `MelodiaRhythmCombatTests.cpp` already uses `EMelodiaRhythmGrade` instead of `EMelodiaSkillGrade` on line 53 where it passes `EMelodiaRhythmGrade::Perfect` to `SubmitRatedInput`. If these must remain distinct enums, fix the test to use `EMelodiaSkillGrade`. Ideally collapse them into one type by moving `EMelodiaSkillGrade` to MelodiaCoreRulesLibrary.h next to `EMelodiaRhythmGrade`.

### Phase 2: Author Cadence Strike DataAsset (Day 1)

Create `UMelodiaRhythmSkillDefinition` DataAsset:

```
Asset: /Game/MelodiaIntegration/Config/Skills/Def_CadenceStrike
├── SkillId = "CadenceStrike"
├── Niche = Vigorous (Damage + Crit)
├── EffectType = Damage
├── TempoBPM = 128.0
├── MusicalKey = "C minor"
├── TimeSignature = 4/4
├── PatternAsset = /Game/MelodiaIntegration/MIDI/CadenceStrike_Pattern (or null for procedural)
├── NoteDensity = 2 (8th notes)
├── IntroBeats = 2
├── ActiveBeats = 4
├── OutroBeats = 1
├── BaseMagnitude = 1.0 (skill base, multiplied by grade scalar)
├── TargetMode = "SingleEnemy"
├── TargetCount = 1
├── SPCost = 2
├── MaxTurnShift = 1
├── DamageMultipliers = { Miss: 0.70, Good: 1.00, Great: 1.20, Perfect: 1.45 }
├── HealMultipliers = (unused for this skill)
├── ResourceMultipliers = (unused)
├── SpeedMultipliers = (unused)
└── LaneColor = FLinearColor(0.42, 1.0, 0.72)  (cyan-green, Vigorous)
```

Place it at a path the auto-discover filter can find: `/Game/MelodiaIntegration/Config/Skills/Def_CadenceStrike` (the filter scans `/Game/MelodiaIntegration/Config` recursively — MelodiaRhythmCombatSubsystem.cpp:30).

### Phase 3: Wire SubmitRatedInput in Battle UI (Day 2)

In `BP_MelodiaBattleUI` (or `BP_BattleUI`):

1. On skill execution start → call `UMelodiaRhythmCombatSubsystem::StartSession("CadenceStrike")`
2. Store returned session ID
3. Show note highway child overlay (already wired per KIMI notes: `MelodiaNoteHighway` visibility driven by `ShowBattleUI`/`HideBattleUI`)
4. On each note input → call `UMelodiaJRPGPresentationRhythmComponent::RecordInputNow()` on the player character component
5. On highway complete → call `UMelodiaRhythmCombatSubsystem::SubmitRatedInput(Grade, HitCount, MissCount)`
6. On stock skill resolver → call `UMelodiaRhythmCombatSubsystem::ConsumePendingRequest(OutRequest)` and apply `OutRequest.RhythmScalar * OutRequest.BaseMagnitude` to the stock damage formula
7. On battle end/defeat/retry → call `UMelodiaRhythmCombatSubsystem::InvalidateSession()`

### Phase 4: Wire Note Highway Beat Position to MusicClock (Day 2)

In `UMelodiaRhythmExecutionComponent::GetCurrentBeatPosition()`:

Currently uses its own `AccumulatedBeatPosition` or Quartz from `UMelodiaAudioComponent`. Change to query `UMelodiaMusicClockSubsystem::GetMusicTime().TotalBeats` (when Harmonix) or `GetMusicTime().BeatInBar` (when Quartz). This ensures the highway scrolls to the same beat phase that `RecordInputNow()` judges against.

Fallback: When `HasMusicalTime()` is false, the execution component should either use its own accumulator (for pre-battle preview) or disable highway with a "No Clock" indicator.

### Phase 5: Wire MPC Reactivity on Hit (Day 2)

In the Blueprint or C++ that receives `UMelodiaJRPGPresentationRhythmComponent::OnPresentationRhythmResult`:

1. Call `UMelodiaRhythmReactivitySubsystem::NotifyBeat(BPM, BeatPhase)` on each beat boundary (already done by the clock)
2. Call `UMelodiaRhythmReactivitySubsystem::NotifyCommandResolved(Grade, Energy, ComboNormalized, CrescendoNormalized, Element)` on skill resolution

The MPC scalars `BeatPulse`, `BeatPhase`, `RhythmPulse`, `GlobalSparkleIntensity`, and `PaletteShift` will then drive the UI and VFX.

### Phase 6: Wire Grade Judgment to HUD (Day 2-3)

In `BP_MelodiaBattleUI`:

1. On `OnPresentationRhythmResult` broadcast:
   - Call `UMelodiaRhythmHUDWidget::SetJudgment(grade text)` — displays grade texture with fade animation
   - Call `UMelodiaRhythmHUDWidget::DoPulse()` — triggers bass proxy pulse for StaffShimmer/SPMeterShimmer
   - On Perfect: Call `UMelodiaRhythmHUDWidget::NotifyPerfectHit()` — triggers NoteTrailIri cyan→gold trail
2. The `SetNoteHighwayActive(Active, Notes, BeatPosition, ScrollBeatsAhead)` is already called from the widget's NativeTick (MelodiaRhythmHUDWidget.cpp:134)

### Phase 7: Verify ConsumePendingRequest at Stock Boundary (Day 3)

In the stock `BP_BattleController` skill resolution graph:

1. Before applying the stock damage formula, call `UMelodiaRhythmCombatSubsystem::ConsumePendingRequest`
2. If `bConsumed == true`, multiply stock damage by `Request.RhythmScalar`
3. If `bConsumed == false` (no rhythm session or already consumed), use stock damage unchanged

This is the exact seam described in KIMI_UI_WIRING_NOTES (line 36-38): wire `ConsumePendingRequest` at `OnSkillSelectedHandler` / `OnUnitHasEnoughMP`.

### Phase 8: MIDI Authoring + Fallback Pattern (Day 3)

1. Author `CadenceStrike_Pattern.mid`:
   - 6 bars at 128 BPM, 4/4
   - Bars 1-2: empty (intro)
   - Bar 3: F3 quarter notes (Lane 0)
   - Bar 4: C4 eighth notes (Lane 1)
   - Bar 5: G4 alternating quarter (Lane 2)
   - Bar 6: F3→C4→G4→C4 (all lanes)
2. Import as UMidiFile
3. Assign to `Def_CadenceStrike` DataAsset
4. Verify `PatternAsset` is loaded correctly by the note scheduler

For fallback (no MIDI): `UMelodiaRhythmExecutionComponent::BuildBasicNotes()` generates equidistant notes on Lane 0 based on `NoteDensity` and `ActiveBeats`. This is sufficient to prove the end-to-end pipeline without MIDI.

### Phase 9: Test + Accept (Day 3-4)

1. Run `Melodia.RhythmCombat.SessionLifecycle` test
2. Run `Melodia.RhythmCombat.GradeBoundaries` test
3. PIE: Main menu → New Game → exploration → battle → Cadence Strike → note highway → grade-dependent damage
4. Verify:
   - Harmonix clock drives the highway when a MetaSound is playing
   - Quartz fallback drives the highway when no Harmonix clock is registered
   - No musical time → `HasMusicalTime()` is false → highway shows "No Clock" → skill resolves at Good/1.0x
   - `SubmitRatedInput` → `ConsumePendingRequest` → stock damage is multiplied by grade scalar
   - MPC scalars update on beat + command resolve
   - HUD shows grade judgment with correct texture and lifetime
   - `RecordInputNow()` → `RecordTimingError` with `ExperiencedTime` timebase
5. Set `melodia.Rhythm.Disable` to 1 → skill plays identically with no rhythm presentation

### Phase 10: Lullaby Mend + Resonance Draw (Day 5-6)

Follow the same pattern for healing and SP restoration skills using the already-wired effect system. Each new skill is a DataAsset row + MIDI pattern, not new code.

---

## Blockers and Risks

1. **MelodiaRhythmCombatTypes.h corrupted** — The file has been overwritten with `MelodiaJRPGPresentationRhythmComponent.cpp` content. It must be restored before compilation succeeds. If no backup exists, reconstruct from the types used by `MelodiaRhythmCombatSubsystem.h` and `MelodiaRhythmSkillDefinition.h` plus the test file.

2. **EMelodiaSkillGrade vs EMelodiaRhythmGrade** — Test file uses `EMelodiaRhythmGrade::Perfect` in a call to `SubmitRatedInput(EMelodiaSkillGrade, ...)`. If these are separate enums, this fails to compile. Either make them the same type or fix the test. Recommendation: rename `EMelodiaSkillGrade` → `EMelodiaRhythmGrade` project-wide and consolidate in `MelodiaCoreRulesLibrary.h`.

3. **GetCurrentBeatPosition() still uses local accumulator** — `UMelodiaRhythmExecutionComponent` has its own `AccumulatedBeatPosition` (MelodiaRhythmExecutionComponent.h:192). It must be redirected to `UMelodiaMusicClockSubsystem` for sync with the grading input. The existing `bUseQuartzClock` flag is a good migration point but needs to also cover Harmonix.

4. **Note highway text bindings not wired** — Per KIMI notes, `JudgementText`, `ComboText`, and `ClockSourceText` are not marked `IsVariable = true` in `WBP_Battle_Rhythm`. The C++ `BindWidget` won't find them. Non-blocking for Phase 1 since `UMelodiaRhythmHUDWidget::SetJudgment` uses NativePaint rendering instead.
