# Melodia Roguelike Game Loop Completion Plan

> **Superseded for production scope (2026-07-26).** Retained as historical
> design and technical evidence. The active product is a small authored
> fixed-loop turn-based RPG; procedural expedition/roguelike requirements are
> not MVP gates. Do not execute this backlog without an explicit scope pivot.
> See `MELODIA_UE58_INTEGRATION_ARCHITECTURE_2026-07-26.md`.

**Audit date:** 2026-07-14  
**Target:** A repeatable, seeded stage loop that can support the first 20-minute vertical slice  
**Evidence standard:** A task is complete only after its acceptance path succeeds in PIE. Asset existence, compilation, or a successful editor script is not completion.

## 1. Current verified state

### Proven in PIE

- `BP_RoguelikeDungeonGenerator` can generate the current two-room layout.
- Both selected room levels instantiate and stream.
- The plugin-required generator overrides exist: first room, next room, continue, validation, and door choice.
- All 22 `RoomData` assets have level references, and the eight participating maps use `ARoomLevel`-derived Level Blueprints.

### Present, but not yet a roguelike loop

- `UMelodiaBattleSession` owns combat and broadcasts `OnEncounterEnded`.
- `AMelodiaGameMode` subscribes to that event, but victory currently only returns the HUD and loop phase to Exploration.
- `URoguelikeRoomCustomData` defines room type, floor eligibility, enemy pool, economy, lighting, and NPC metadata.
- Python modules define floor generation, run state, artifacts, blessings, shops, rewards, and enemy scaling.

### Not proven or not connected

- Runtime Unreal code does not consume the Python roguelike rules.
- `OnRoomAdded` does not configure encounter actors from `URoguelikeRoomCustomData`.
- Victory does not mark a room cleared, unlock an exit, present a run reward, or advance a stage.
- The generator is a fixed Grove V1 -> Grove V2 sequence, not a seeded selection algorithm.
- There is no authoritative run state, stage transition coordinator, defeat/reset path, run checkpoint, or completed multi-stage soak test.
- Shared level maps are referenced by multiple `RoomData` variants. They load, but produce the `RoomLevel Data does not match RoomData Level` diagnostic; metadata and debug drawing cannot be trusted until variants have unique maps or the ownership contract is revised.

## 2. Production architecture decision

Python remains an authoring and balancing reference. Shipping gameplay must not depend on editor Python.

Create one runtime source of truth:

`UMelodiaRoguelikeRunSubsystem : UGameInstanceSubsystem`

It owns:

- Run seed and `FRandomStream`.
- Run phase: Inactive, Generating, Exploring, Encounter, RewardChoice, Transitioning, Defeated, Complete.
- Stage/floor index, current room identity, and cleared-room identities.
- Persistent party resources for the run.
- Temporary boons, burdens, artifacts, currency, and dissonance.
- The generated stage recipe: room, enemy, modifier set, and reward candidates.
- Idempotency tokens so victory and rewards cannot be processed twice.

Add one world-facing coordinator:

`AMelodiaDungeonRunCoordinator`

It binds the run subsystem, dungeon generator, battle session, room exits, and UI. The GameMode remains responsible for mode bootstrap and presentation; it should not become the run-state database.

The runtime loop is:

`Start run -> build seeded stage recipe -> generate/load -> initialize room -> explore -> encounter -> confirm victory -> reward choice -> unlock exit -> transition -> unload/regenerate -> next stage`

Defeat branches to a run summary and explicit restart/return action. Flee must have an authored policy and cannot silently count as victory.

## 3. Updated task backlog

### P0 — Make one complete two-stage loop

#### RGL-001: Implement authoritative run subsystem

- Add C++ structs for run state, stage recipe, modifier, reward candidate, and result.
- Add `StartNewRun(seed)`, `BuildNextStage()`, `RecordEncounterResult()`, `SelectReward()`, `AdvanceStage()`, and `EndRun()`.
- Use `FRandomStream`; never use unrelated global random calls inside generation.
- Expose read-only Blueprint access and transition delegates.

**PIE gate:** Starting with the same seed twice logs the same first five stage recipes; another seed produces at least one different choice.

#### RGL-002: Add dungeon run coordinator

- Find or receive the placed generator.
- Bind generator lifecycle and `UMelodiaBattleSession::OnEncounterEnded` exactly once.
- Guard every transition against duplicate callbacks.
- Keep player input disabled during unload/load and restore it after post-generation initialization.

**PIE gate:** Re-entering PIE and regenerating does not duplicate delegate calls, rewards, rooms, or transitions.

#### RGL-003: Replace fixed room selection with a runtime stage recipe

- `ChooseFirstRoomData` and `ChooseNextRoomData` must read the active recipe/sequence.
- Filter by floor range, room type, valid level, compatible doors, and recent-room repetition.
- Use plugin `GenerationInit` to reset attempt-local counters.
- Use `IsValidDungeon` to validate the intended stage topology, not return unconditional true.
- Handle `GenerationFailed` with a safe fallback recipe and visible diagnostic.

**PIE gate:** Ten generations produce only valid, loadable rooms; fixed-seed runs reproduce their room order.

#### RGL-004: Initialize streamed room gameplay

- On `OnRoomAdded`, store virtual room metadata only; the plugin documents that the level is not spawned yet at this callback.
- After post-generation/room initialization, resolve `URoguelikeRoomCustomData` and configure encounter trigger, enemy, lighting profile, entrance, and exit.
- Fail closed when combat metadata is invalid: no invisible unwinnable encounter.

**PIE gate:** The room's selected enemy and displayed stage metadata match the seeded recipe, not an actor default.

#### RGL-005: Implement room-clear and exit contract

- Add `BP_MelodiaRoomExit`/C++ base with Locked, Available, Transitioning states.
- Lock on room initialization.
- On confirmed Victory, mark room clear once and open the exit after reward resolution.
- Standardize entrance/exit anchors and safe player teleport placement.

**PIE gate:** Exit is unusable before victory, usable once after reward selection, and cannot trigger two regenerations.

#### RGL-006: Implement minimal reward choice

- Present three deterministic candidates after `ConfirmVictoryReward`.
- MVP families: damage/song power, defense/recovery, and dissonance bargain (strong boon plus burden).
- Apply the selected modifier to the runtime system actually used by combat.
- Keep ordinary XP/currency rewards separate from run modifiers.

**PIE gate:** Only one candidate can be claimed; its gameplay effect is measurable in the next encounter.

#### RGL-007: Safe unload/regenerate transition

- Transition only after reward selection and exit activation.
- Fade/disable control, move player out of streamed-room ownership, request generation, wait for post-generation, teleport to entrance, restore control.
- Never call `Generate()` from battle callbacks while room actors are still executing teardown logic.

**PIE gate:** Clear stage 1, choose reward, cross exit, and fight stage 2 without stale actors, falling, duplicate rooms, or an editor crash.

### P1 — Make it a playable vertical-slice run

#### RGL-008: Author the first 20-minute run curve

- Stage 0: Bedroom/prologue and Sir Melodious introduction.
- Stage 1: Tutorial exploration and low-pressure encounter.
- Reward 1: obvious three-way choice.
- Stage 2: mechanic check with visible environmental dissonance.
- Stage 3: event/treasure recovery room.
- Stage 4: elite encounter requiring the chosen build.
- Stage 5: short boss/crescendo and run-summary beat.
- Target roughly 2–3 minutes per generated stage after the prologue.

**PIE gate:** A first-time tester reaches the summary in 15–25 minutes without developer intervention.

#### RGL-009: Port only required Python balance data into Unreal assets

- Create Primary Data Assets or Data Tables for room definitions, enemy pools, modifier definitions, reward weights, and difficulty curves.
- Treat the Python registry as migration input/tests, not a parallel runtime authority.
- Add stable IDs and validation for missing references.

**PIE gate:** Packaged Development build generates the same seeded recipes without Python/editor modules.

#### RGL-010: Connect dissonance to risk, mechanics, and presentation

- Run dissonance rises through burdens, damage, misses, or stage pressure and recovers through harmony/reward choices.
- Scale musical power through an explicit combat stat; do not infer it only from post-process intensity.
- Drive hallucination/material/post-process profiles from a bounded presentation interface.
- Reserve gore/surreal escalation for high thresholds and keep readability of doors, enemies, and rhythm prompts intact.

**PIE gate:** Changing dissonance changes a documented combat value and a documented visual/audio layer, while navigation remains readable.

#### RGL-011: Sir Melodious gameplay dependency

- Track companion availability in run/player state.
- Melusina's empowered music requires Sir Melodious; absence switches to a clearly defined weak/nonmagical command set.
- Vertical slice may keep bird possession/flying disabled, but must introduce him and prove the energy link in tutorial and UI.

**PIE gate:** Toggling companion availability changes the allowed music ability and feedback consistently.

#### RGL-012: Defeat, flee, restart, and checkpoint policy

- Defeat ends the active run and shows summary/restart.
- Define flee cost: return to exploration with encounter active, or end run; do not leave the room accidentally cleared.
- Save durable meta progression separately from an optional run checkpoint.
- Use asynchronous SaveGame writes at stage boundaries, not every combat beat.

**PIE gate:** Defeat and flee never unlock victory rewards; restart produces a clean run with no retained transient modifiers.

### P2 — Replayability and production hardening

#### RGL-013: Content weighting and anti-repetition

- Weighted room/enemy pools by stage tier.
- Pity/guarantee rules for recovery, shop, and variety.
- Mutually exclusive modifier tags and synergy tags.
- Seed and recipe displayed in development UI for bug reproduction.

#### RGL-014: Meta progression

- Separate run currency from permanent currency.
- Unlock option breadth rather than only permanent numerical power.
- Add run history, discoveries, Sir Melodious progression, and narrative memories.

#### RGL-015: Automated and manual test matrix

- Unit: deterministic recipe, eligibility filters, reward idempotency, modifier stacking.
- Functional: victory -> reward -> exit -> regeneration.
- Soak: 10 consecutive stages and 25 regeneration cycles.
- Failure injection: invalid room, no compatible door, missing enemy, generation failure, death during transition.
- Packaged build smoke test in addition to PIE.

## 4. Required supporting Blueprint actors

| Actor | Responsibility | MVP requirement |
|---|---|---|
| `BP_RoguelikeDungeonGenerator` | Spatial generation only; queries active recipe | Replace fixed two-room constants |
| `BP_MelodiaRoomEntrance` | Safe arrival transform and camera facing | Required |
| `BP_MelodiaRoomExit` | Lock, reward-complete gate, transition request | Required |
| `BP_MelodiaEncounterTrigger` | Starts configured encounter | Existing class must be recipe-driven |
| `BP_MelodiaRewardChoice` / widget | Shows and commits three choices | Required |
| `BP_MelodiaRunFailVolume` | Recovers player from invalid fall/stream placement | Required safety net |
| `BP_MelodiaRoomBounds` | Detects room presence and supports encounter scope | Recommended |
| `BP_MelodiaDissonanceVolume` | Local presentation contribution only | P1 |

## 5. Immediate implementation order

1. `RGL-001` run subsystem.
2. `RGL-002` coordinator and delegate/idempotency contract.
3. `RGL-005` locked exit and entrance anchors.
4. `RGL-006` one functional three-choice reward.
5. `RGL-007` stage transition and second-stage proof.
6. `RGL-003/004` replace fixed selection and configure rooms from data.
7. `RGL-012` defeat/flee/restart.
8. Run the two-stage acceptance path, then expand into `RGL-008`.

## 7. Verified transition milestone (2026-07-14)

The continuous PIE smoke `MELODIA_THREE_STAGE_PHYSICAL_FINAL` now proves the transition spine used by the current vertical-slice run:

- Three generated stages reached ProceduralDungeon `Ready To Play`.
- Stages 0 and 1 each completed encounter confirmation and reward commitment.
- The local player crossed the unlocked `AMelodiaRoomExit` through swept physical movement twice.
- Each crossing advanced exactly one stage and regenerated inside `ZenForestTest`; neither crossing invoked map travel.
- Stage 2 victory confirmation changed the run to `Complete`, enabled Sir Melodious, and spawned one reunion actor.
- No target RoomData, door-selection, generation-timeout, entrance-ambiguity, Blueprint runtime, or `Accessed None` diagnostic appeared during the active run.

This verifies the current fixed three-stage transition loop, not the entire replayable roguelike backlog. The RoomData library has subsequently been repaired and re-audited at `22/22` exact matches with zero repeated `_Vn_Vn` map suffixes. Seeded pool selection, defeat/restart, packaged-build coverage, and the full 15-25 minute authored content curve remain open production work.

## 6. Research basis

- ProceduralDungeon defines generation as unload, virtual dungeon creation, then level load/initialization; `OnRoomAdded` occurs before the room is spawned, while `PostGeneration` occurs after rooms are loaded and initialized.
- The plugin exposes fixed, random, and auto-increment seed policies, but Melodia still needs its own run recipe and deterministic gameplay RNG contract.
- Unreal `UGameInstanceSubsystem` shares the lifetime of the game instance and is suitable for transient state across generated level changes.
- Unreal Random Streams provide repeatable results from a seed.
- Unreal SaveGame supports purpose-specific save classes and asynchronous writes; durable meta progression and resumable run state should be separate records.
