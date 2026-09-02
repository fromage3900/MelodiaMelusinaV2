# Melodia Transition System Contract

> **Partially superseded (2026-07-26).** Preserve the authored-story travel
> distinction and stable level-ID policy. Roguelike room traversal, run-stage
> advancement, and MelodiaCore run authority are not active MVP requirements.
> Future travel must pass through the project adapter and JRPG-owned game-state
> policy. See `MELODIA_UE58_INTEGRATION_ARCHITECTURE_2026-07-26.md`.

Status: historical transition contract; authored-travel guidance retained  
Owner: Melodia gameplay/world integration  
Last updated: 2026-07-14

## Non-negotiable separation

Melodia has two transition mechanics. They solve different problems and must never call each other's state machinery.

| Domain | Canonical actor | Changes map? | Advances run stage? | Invokes Procedural Dungeon? |
|---|---|---:|---:|---:|
| Authored story travel | `AMelodiaOpeningPortal` | Yes | No | No |
| Roguelike room traversal | `AMelodiaRoomExit` through `AMelodiaDungeonRunCoordinator` | No | Yes | Yes |

`BP_MelodiaTeleporterVolume` is a legacy generic `OpenLevel` overlap. Do not place new instances. Existing instances must be replaced by a Blueprint child of `AMelodiaOpeningPortal` or by the native actor before production review.

## Story-travel contract

Story travel connects authored campaign maps such as Dreamstate, Melusina's bedroom, and the forest threshold.

Canonical flow:

```text
Player enters AMelodiaOpeningPortal
→ validate local player pawn
→ one-shot activation
→ authored transition presentation
→ OpenLevel(DestinationLevelName)
→ destination map resolves its authored PlayerStart/arrival anchor
```

Rules:

- Destination is an authored level, never a generated room.
- Story travel never reads or writes `UMelodiaRoguelikeRunSubsystem::CurrentStageIndex`.
- Story travel never calls `ADungeonGeneratorBase::Generate`.
- Only the local player pawn can activate it.
- Every portal must define an explicit destination and a destination arrival policy.
- Opening-state persistence belongs to opening/story state components, not the roguelike subsystem.

## Roguelike-traversal contract

Room exits advance a persistent run while replacing streamed procedural rooms inside the same gameplay world.

Canonical flow:

```text
Encounter victory
→ reward choice
→ CommitRewardAndAdvance unlocks active room exit
→ local player overlaps AMelodiaRoomExit
→ Coordinator.RequestNextStage
→ RunSubsystem.AdvanceStage
→ DungeonGenerator.Generate
→ generator completion delegate
→ RunSubsystem.NotifyGenerationComplete(true)
→ new room encounter configuration
```

Rules:

- A room exit never calls `OpenLevel`.
- A room exit never chooses a story destination.
- Only the local player pawn can activate it.
- New room exits must have an explicit coordinator reference. Auto-resolution exists only for migration and is valid only when exactly one coordinator exists.
- Exit collision remains disabled while locked and is enabled only after reward commitment.
- A transition is one-shot until the next lock cycle.
- Generation must complete or fail within the configured timeout; a run must not remain permanently in `Generating`.
- Room generation must preserve persistent HP, SP, rewards, dissonance, and companion/run state through the Game Instance subsystems.

## Asset ownership

| Asset/class | Allowed responsibility | Forbidden responsibility |
|---|---|---|
| `AMelodiaOpeningPortal` | Authored-level travel | Stage advancement, dungeon generation |
| `BP_MelodiaTeleporterVolume` | Legacy migration only | New production placement |
| `AMelodiaRoomExit` / `BP_MelodiaRoomExit` | Player request to advance an unlocked run | `OpenLevel`, story flags |
| `AMelodiaDungeonRunCoordinator` | Bridge run state, battle, rewards, generator and active exit | Campaign map routing |
| `UMelodiaRoguelikeRunSubsystem` | Persistent recursive-run state | World loading and portal presentation |

## Current authored instances

- `Dreamstate_WakePortal`: valid story travel using `AMelodiaOpeningPortal`.
- `StoryTravel_ToDreamstate` in `ZenForestTest`: canonical `AMelodiaOpeningPortal`, targeting `/Game/Melodia/Levels/Opening/L_Melodia_Dreamstate`.
- `BP_MelodiaRoomExit` in `ZenForestTest`: canonical roguelike traversal with an explicit coordinator reference and compatibility auto-resolution disabled.

## Acceptance tests

### Story travel

- AI and non-player overlaps do nothing.
- One player overlap opens exactly one authored destination.
- The run stage and procedural generator remain unchanged.
- Invalid destination data fails visibly during validation.
- Arrival cannot immediately retrigger the return portal.

### Roguelike traversal

- Locked exit has no collision and cannot transition.
- Reward commitment unlocks exactly the active exit.
- AI and non-player overlaps do nothing.
- Player overlap advances exactly one stage without changing maps.
- Generator success changes `Generating → Exploring`.
- Generator failure or timeout leaves a diagnosable non-stuck state.
- Two consecutive physical exits preserve HP and SP and reach the final encounter.

## Implementation status (2026-07-14)

- Story travel and roguelike traversal have separate native actors and separate runtime call paths.
- `ZenForestTest` uses `AMelodiaOpeningPortal` for Dreamstate travel. Its roguelike exit is explicitly bound to the run coordinator.
- The coordinator owns one active room exit; it no longer unlocks every exit in the world.
- The live-editor aggregate RoomData audit now reports `22/22` exact `RoomData <-> ARoomLevel.Data` matches. Each variant owns its canonical `_Vn` world package, and the room directory contains zero repeated `_Vn_Vn` suffixes.
- Generation has a timeout and returns from failure instead of remaining stuck in `Generating`.
- `AMelodiaRoomEntrance` defines the roguelike-only post-generation arrival contract. A multi-room stage must expose exactly one primary entrance.
- Native compilation passes with the entrance-anchor implementation.
- The continuous PIE smoke `MELODIA_THREE_STAGE_PHYSICAL_FINAL` passed on 2026-07-14: three `Ready To Play` generations, two swept physical room-exit crossings, stages `0 -> 1 -> 2`, final phase `Complete`, Sir availability `true`, and one spawned Sir Melodious reunion actor.
- That run recorded zero occurrences of `ChooseDoor not implemented`, invalid RoomData levels, RoomLevel/RoomData mismatch, generation timeout, ambiguous primary entrance, Blueprint runtime error, or `Accessed None`.

## Remaining verification and migration work

1. Expand the physical-route test into a checked-in automation test instead of relying only on the Monolith smoke harness.
2. Add packaged-build coverage for the same three-stage route.

## Verification artifacts

- `Saved/Audit/melodia_transition_contract.json`: passing source and authored-instance domain audit.
- `Saved/Audit/melodia_room_level_contract.json`: current library audit, `22/22` matching and zero mismatches.
- PIE marker `MELODIA_THREE_STAGE_PHYSICAL_FINAL`: passing physical route recorded in `Saved/Logs/BS_GodFile.log`.

## Runtime authority boundary

`UMelodiaRoguelikeRunSubsystem` in MelodiaCore is the only shipping authority for run phase, stage advancement, rewards, persistent run resources, and idempotency.

GMM is an offline authoring and verification lane. It may produce versioned contracts, fixtures, generated constants, deterministic simulations, and golden event traces consumed by tests. It must not emit or register another Unreal roguelike subsystem. The legacy `UMelodiaRoguelikeSession` generator is intentionally removed from the GMM daemon registry.
