# Melodia Authoritative Rhythm Combat Wiring

**Date:** 2026-08-03  
**Status:** Design locked; implementation begins with a Cadence Strike vertical slice  
**Scope:** Authoritative rhythm-modified combat, note highway UI, Harmonix/Quartz timing, rhythm skills, save/load, and acceptance

## Authority decision

Rhythm results now affect gameplay. The rhythm layer supplies one validated modifier/effect request to the stock skill-resolution boundary. It does not create a second battle session and does not independently apply damage, healing, SP, statuses, speed, turn order, victory, defeat, or save mutations.

```text
Stock skill validation -> rhythm session -> note highway -> graded result
-> one authoritative effect request -> stock resolver -> UI/audio/VFX feedback
```

The stock battle controller remains authoritative for command validation, target validation, turn advancement, combat mutation, victory/defeat, and save boundaries.

## Existing foundations

- `UMelodiaMusicClockSubsystem`: single musical-time authority.
- Harmonix `UMusicClockComponent`: preferred authored clock.
- `UMelodiaAudioComponent`: Quartz fallback transport.
- `URhythmBeatTracker`: beat/bar forwarding without DeltaTime scheduling.
- `UMelodiaJRPGPresentationRhythmComponent`: timing-window evaluator and calibration surface; its existing presentation path remains intact.
- `UMelodiaBattleAdapterSubsystem`: battle lifecycle bridge.
- `UMelodiaJRPGBattleOverlaySubsystem`: battle overlay creation/removal.
- `/Game/MelodiaIntegration/UI/BP_MelodiaRhythmPrompt`: existing rhythm prompt host.
- `/Game/Melodia/UI/WBP_Battle_Rhythm`: nearest authored highway host.
- `/Game/Melodia/UI/WBP_SkillCodex`: skill presentation surface.
- `/Game/MelodiaIntegration/Blueprints/DT_MelodySlime_Skills`: existing skill data reference.
- `UMelodiaSaveSlotLibrary`: canonical save/load boundary.

No existing authoritative rhythm modifier, note scheduler, or typed rhythm skill-effect resolver was found. Those are new project-owned contracts.

## New authoritative contracts

### Rhythm result

`FMelodiaAuthoritativeRhythmResult` must contain:

- validity/completion flags;
- unique session ID;
- grade: Miss, Good, Great, Perfect;
- note/hit/miss counts;
- accuracy and timing score;
- damage/heal/resource/speed scalars;
- bounded turn shift;
- clock source.

Results are immutable after completion and reject duplicate session IDs.

### Effect request

`FMelodiaRhythmEffectRequest` must contain:

- skill ID;
- effect type;
- base magnitude;
- rhythm scalar;
- target mode/count;
- duration;
- bounded turn shift;
- result/session ID;
- consumed flag.

The stock resolver combines the rhythm scalar with ordinary damage, defense, resistance, critical, status, and targeting rules.

### Proposed authority owner

Add a project-owned battle-scoped rhythm adapter, preferably `UMelodiaRhythmCombatAdapter`, owned by the battle controller or battle adapter subsystem. It starts sessions, accepts exactly one result, converts it to a typed request, and hands it to the stock resolver. It never bypasses the stock resolver.

## Initial grade balance

These are starting values for playtesting:

| Grade | Damage | Healing | SP/resource | Speed/turn |
|---|---:|---:|---:|---|
| Miss | 0.70 | 0.70 | 0.75 | none |
| Good | 1.00 | 1.00 | 1.00 | baseline |
| Great | 1.20 | 1.15 | 1.10 | minor |
| Perfect | 1.45 | 1.35 | 1.25 | strongest bounded |

No-clock behavior must be explicit: resolve as a defined fallback grade or disable rhythm skills with a visible reason. Never silently grant Perfect.

## Note highway

Host the reusable highway as a child overlay of `BP_BattleUI`, using `WBP_Battle_Rhythm` or a compatible contract-preserving wrapper. Required elements:

- lane background;
- incoming note container;
- fixed hit line/window;
- note template;
- judgement/combo/accuracy text;
- active skill label;
- clock-source indicator;
- cancel prompt.

Visual note position uses `VideoRenderTime`. Input grading uses `ExperiencedTime`. Notes are scheduled from musical beat positions, never a wall-clock DeltaTime accumulator.

Initial keys: F/J/K. Initial note types: tap notes only. Hold notes, chords, and directional patterns are later expansions.

Harmonix is registered by the actor owning the authored music clock. Quartz is registered by the battle audio owner and started only as fallback. Harmonix wins whenever it is running.

## Initial skill catalog

### Damage

- `Cadence Strike`: single-target damage; first end-to-end vertical slice.
- `Resonant Arc`: multi-target damage with controlled falloff.
- `Downbeat Break`: damage plus stock defense-down status on strong grades.

### Healing

- `Lullaby Mend`: single-ally heal modified by grade.
- `Chorus of Renewal`: party heal with explicit falloff.

### SP/resource

- `Resonance Draw`: caster SP restoration.
- `Ensemble Gift`: multi-ally SP restoration.

### Speed/turn order

- `Accelerando`: bounded temporary speed increase.
- `Quickstep Prelude`: maximum one-position forward shift through stock turn authority.
- `Ritardando Veil`: temporary enemy slow through stock status authority.

### Defense/status

- `Syncopated Ward`: shield/damage reduction through stock status/effect authority.
- `Dissonant Silence`: short status effect with stock validation.

## Data-driven skill schema

Each rhythm skill should be data-driven and include:

`SkillId`, display name, description, effect type, base magnitude, targeting mode, target count, rhythm-enabled flag, pattern asset, SP cost, duration, grade multipliers, status effect, max turn shift, and presentation theme.

Each pattern includes beat positions, lanes, expected keys, early/late windows, difficulty tier, intro beats, active beats, and outro beats.

## Wiring order

1. Add authoritative result/effect structs and adapter.
2. Integrate `Cadence Strike` at the stock skill-resolution boundary.
3. Add the note highway child overlay and session lifecycle.
4. Route Harmonix/Quartz timing to note scheduling and input grading.
5. Apply damage scalar exactly once through stock combat resolution.
6. Add `Lullaby Mend` and `Resonance Draw` using the same effect adapter.
7. Add speed and turn-order effects with hard bounds.
8. Convert remaining skills to data-driven rows.
9. Persist unlocked skills, patterns, calibration, and accessibility settings.
10. Invalidate sessions on battle end, defeat, retry, map travel, and load.
11. Run the complete PIE acceptance loop.

## Save/load rules

Persist skill/pattern unlocks, calibration offset, input/accessibility settings, and optional best accuracy. Do not persist active notes, active session IDs, pending results, beat phase, or widget references. On load, reset the rhythm session and re-register the active clock.

## Failure and recovery

- Cancelled session: explicit Miss/cancel result.
- No clock: configured fallback or disabled skill.
- Battle ended: invalidate without applying result.
- Duplicate result: reject by session ID.
- Defeat/retry: clear highway and pending state before recovery.
- Save/load: never serialize transient highway state.

## Acceptance loop

`Main menu -> New Game -> exploration -> battle -> Cadence Strike -> note highway -> grade-dependent damage -> Lullaby Mend -> grade-dependent heal -> Resonance Draw -> SP change -> Accelerando -> speed/status -> Quickstep Prelude -> bounded turn shift -> victory -> save -> reload -> defeat/retry cleanup.`

## Required validation

- UHT/build clean after native changes.
- Focused unit tests for grade boundaries, duplicate results, caps, target falloff, turn bounds, serialization, and invalidation.
- Blueprint compile/readback for each changed asset.
- PIE verifies each stock command executes once and all effects are applied through stock authority.
- Development logs include skill ID, session ID, clock source, BPM, note count, accuracy, grade, requested effect, resolved magnitude, and rejection reason.

## Current blockers

- Exact stock skill damage/heal/SP/turn resolver entry points require live Blueprint graph audit.
- No authored note highway implementation currently exists beyond `WBP_Battle_Rhythm`/`BP_MelodiaRhythmPrompt` hosts.
- Harmonix production owner/registration caller is not yet confirmed.
- Native implementation must be added before Blueprint effect wiring can be safely completed.
- Protected `MelodiaHairComponent.cpp` and `ZenForestTest.umap` remain out of scope and must not be opened or modified.

## Live editor wiring transaction — 2026-08-03

### `WBP_Battle_Rhythm`

Compiled and saved with this hierarchy:

```text
HUDRoot
└── HighwayOverlay (Overlay)
    └── HighwaySurface (Border)
        └── HighwayCanvas (CanvasPanel)
            ├── HitWindow (Image)
            ├── JudgementText (TextBlock, READY)
            ├── ComboText (TextBlock, COMBO 0)
            └── ClockSourceText (TextBlock, CLOCK: WAITING)
```

The asset remains a presentation host. It has no note scheduling, input grading, or combat mutation graph yet.

### `BP_BattleUI`

Added `MelodiaNoteHighway` as a child of `CanvasPanel_0` using:

`/Game/Melodia/UI/WBP_Battle_Rhythm.WBP_Battle_Rhythm_C`

Slot configuration:

- Center anchor
- Z-order 100
- Size 640 x 260

Existing stock battle graph topology remained unchanged at 157 nodes / 151 connections. Existing collapsed `RhythmPrompt` remains intact. Both assets compiled cleanly and both packages are saved; dirty-package readback returned zero.

### Remaining wiring

- `MelodiaNoteHighway` visibility must be driven by the authoritative rhythm-session lifecycle.
- Note pattern scheduling must consume Harmonix `VideoRenderTime` and Quartz fallback phase.
- Input grading must consume `ExperiencedTime`.
- `JudgementText`, `ComboText`, and `ClockSourceText` need runtime bindings to the adapter/music-clock delegates.
- The stock skill resolver still needs exact graph-level entry points before effect requests can mutate damage/heal/SP/speed/turn order.
- The readback serializer reports text color as transparent despite successful explicit color writes; this requires a focused property readback/editor inspection before treating palette persistence as verified.

### Battle highway lifecycle visibility transaction — 2026-08-03

`/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI` now drives the hosted `MelodiaNoteHighway` child through the existing stock lifecycle events without changing command or combat authority:

```text
ShowBattleUI -> Get MelodiaNoteHighway -> SetVisibility(Visible)
HideBattleUI -> Get MelodiaNoteHighway -> SetVisibility(Collapsed)
```

Validation evidence: the pre-change EventGraph fingerprint was `370f5b2611afdab36d87b3ab06280fdf0169a37f` with 157 nodes/151 connections; the post-change topology fingerprint is `1dfe843184cfede3f8d921b8eb8e188fe4f4a68d` with 161 nodes/153 connections. Blueprint compile returned `UpToDate` with zero errors and warnings. A subset graph assertion matched both `SetVisibility` nodes; exported readback confirmed the two lifecycle exec edges and two `MelodiaNoteHighway` target edges. Save returned `saved:true` and `was_dirty:false` after persistence.
