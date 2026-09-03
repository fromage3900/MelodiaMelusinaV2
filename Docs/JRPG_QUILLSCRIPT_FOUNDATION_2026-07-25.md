# TurnBased JRPG + QuillScript Foundation Intake

**Date:** 2026-07-25  
**Mode:** read-only production intake; isolated QuillScript compatibility work  
**Product premise:** preserve the runtime-proven JRPG template and replace only
its presentation/authorship seams as needed.

## Decision

Use the complete standalone TurnBased JRPG template as the provisional gameplay
baseline. Do not rewrite battle, party, quest, turn, inventory, save, or UI
behavior while that template remains the only end-to-end runtime-proven route.

The current `BS_GodFile` imports are incomplete reference subsets, not yet the
runtime-proven baseline.

Evaluate QuillScript as an optional narrative authoring/runtime layer in a
separate UE5.8 lab. It may enter production only through a small project-owned
adapter after compile, editor-load, runtime, save-boundary, and packaging gates
pass.

MelodiaCore remains quarantined as a production authority. Its rhythm concepts
may be salvaged later, but its runtime instability disqualifies it from owning
the base loop.

## Evidence hierarchy

1. User runtime verification: battles, party systems, quests, turn management,
   UI, and the complete template loop behave as expected.
2. Live Monolith inspection: the template has a coherent Blueprint authority
   spine and usable extension events/functions.
3. Static package/source inspection: QuillScript has the required narrative
   language and callbacks, but also owns independent story/global/save state.
4. Compilation is necessary but is not equivalent to runtime suitability.

## Current JRPG authority map

| Concern | Current authority | Useful seam | Integration rule |
|---|---|---|---|
| Game/player state | `BP_JRPGPlayerController` | `OnGameStateChanged`; `isInputBlocked`; `gameState` | Adapter requests state changes; QuillScript never owns input or gameplay mode |
| Party/progression | `BP_JRPGPlayerController` | `partyMembers`; `UpdatePlayerUnitsData` | Preserve template data and reward flow |
| Inventory/equipment | `BP_JRPGPlayerController` | existing add/remove/equip functions | Only allowlisted reward IDs may enter through adapter |
| Quests | `BP_JRPGPlayerController` + `BP_QuestBase` | `GetQuestStatus`; `IsQuestAvailable`; `UpdateQuest` | QuillScript may request; controller remains authority |
| Battle encounter | `BP_BattleBase` | editable encounter/spawn/reward data; `OnBattleOver`; `OnBattleRemoved` | Narrative starts battle by ID and waits for result event |
| Turn execution | `BP_BattleController` | `OnTurnChanged`; `OnActionTimeAdded` | Do not replace or shadow turn scheduling |
| Battle UI | `BP_BattleUI` and related widgets | existing controller/widget references | Reskin after behavior is frozen and regression-tested |
| Save/load | `BP_JRPGGameInstance` + `BP_JRPGSaveGame` | existing slot/save flow | One gameplay save schema; Quill story state must be embedded or translated |
| Narrative | candidate `QuillScript` | script target, interpreter delegates, allowlisted callbacks | Narrative-local sequencing only |

## Blueprint intake findings

`BP_JRPGPlayerController` is the broad gameplay state hub. It currently owns or
coordinates:

- party members and unit progression;
- inventory, equipment, and gold;
- active/completed quests and quest updates;
- the current battle controller;
- exploration character/UI;
- game state and input blocking;
- an existing `dialogues` widget array.

This makes it the correct destination behind a narrow adapter, but the wrong
object to expose directly to QuillScript.

`BP_BattleBase` is the encounter/result boundary. It exposes editable battle
configuration and broadcasts `OnBattleOver(BattleResult)` and
`OnBattleRemoved`. That is a clean asynchronous narrative seam:

`dialogue -> request encounter -> template battle -> result event -> resume dialogue`

`BP_BattleController` owns turn selection, damage, current units/targets,
battle UI, and results. It already broadcasts `OnTurnChanged` and
`OnActionTimeAdded`. Existing rhythm functions and variables are present in
both template roots; they are legacy/customized surface area, not proof that
MelodiaCore should be reactivated.

`BP_QuestBase` is primarily data-driven, while quest mutation lives on the
player controller. QuillScript should therefore pass a stable project quest ID
to the adapter rather than storing Blueprint class paths in authored dialogue.

## Duplicate-root correction

The project currently contains **330 files in each** of:

- `/Game/TurnBasedJRPGTemplate`
- `/Game/_ThirdParty/TurnBasedJRPGTemplate`

All 330 relative paths overlap and all 330 package hashes differ. The path
difference embedded in Unreal packages explains some byte-level difference,
but live inspection also found a semantic type difference: the root
`BP_BattleController` resolves `RhythmHUDRef` as `WBP_RhythmHUD_C`, while the
`_ThirdParty` copy reports it as a generic object.

Therefore these roots are not a harmless "small overrides + full library"
arrangement. They are parallel full trees with independent internal references.
Do not delete, move, redirect, or customize either root during the portfolio
push.

The complete standalone source was subsequently located at
`G:\ueprojects\TurnBasedjRPGTemplate`. It contains 409 assets and three maps,
for 412 content packages total. Comparing relative paths shows that each
`BS_GodFile` import is missing 82 source packages, including:

- `BP_JRPGGameMode` and `BP_MainMenuController`;
- `Gameplay`, `BattleMap`, and `MainMenu`;
- off-level/permanent battle variants and transitions;
- concrete NPC, shop, chest, forge, shrine, and save-point actors;
- concrete quests, equipment, enemies, and supporting UI.

The complete source has been staged without caches or saves at
`CompatibilityLabs/TurnBasedJRPGUE58` for an isolated UE5.8 proof.

## Sample versus template

`F:\TurnBasedjRPGSample\TurnBasedjRPGSample` is a separate demo/content layer:

- 142 sample assets;
- `SampleGameplay` and `SampleMainMenu`;
- custom characters, skills, battles, transitions, interactables, and UI;
- explicit dependencies on `/Game/TurnBasedJRPGTemplate`.

Its current copy does not contain `Content\TurnBasedJRPGTemplate`. Its final
February 27, 2026 log records failed Blueprint parents and missing template
packages before brief PIE sessions. It is useful extension-pattern evidence,
but it is not currently a self-contained working baseline.

## QuillScript integration risks

1. **Second save authority:** QuillScript provides
   `SaveGameAndStoryToSlot`, `LoadGameAndStoryFromSlot`, and
   `ResumeGameAndStoryFromSlot`.
2. **Second progression store:** global variables and script history can silently
   become durable gameplay flags.
3. **Hidden world mutation:** script travel/commands could bypass project
   transition policy.
4. **UI/input competition:** its dialogue widgets and interpreter input can
   conflict with the controller's `isInputBlocked`, game state, and existing UI.
5. **Asset coupling:** authored scripts must not depend directly on template
   Blueprint class paths, especially while duplicate roots exist.

## Safe adapter contract

The first adapter should be deliberately small:

- `StartBattle(EncounterId)`
- `CompleteQuest(QuestId)`
- `SetNarrativeFlag(FlagId, Value)`
- `RequestTravel(LevelId)`
- `GrantDialogueReward(RewardId)`

Each intent uses a project-owned stable identifier. The adapter validates the
identifier, calls the existing template authority, logs rejection, and reports
completion back to the interpreter. No raw controller, save object, inventory
map, or subsystem reference crosses the boundary.

## Acceptance sequence

1. Refresh the stale enum switch in QuillScript's editor-only `StatementBP`.
   The UE5.8 editor target and both plugin modules now build and load.
2. Load the QuillScript lab editor and create/reload one script asset.
3. Run dialogue, choice, condition, variable mutation, label jump, and callback.
4. Verify unknown callbacks are rejected.
5. Build and launch a QuillScript Development package.
6. Interactively verify the complete JRPG template's battle, UI, quest, and
   save/load flows in `CompatibilityLabs/TurnBasedJRPGUE58`. Its UE5.8
   Blueprint compile and all three map initialization gates already pass.
7. Build a disposable bridge slice against those independently proven sources.
8. Prove `dialogue -> battle -> result -> dialogue` without modifying battle
   scheduling, party state, quest authority, or save ownership.

## Scope guard

While portfolio renders are active:

- production work remains read-only;
- no MelodiaCore, ACFU, JRPG Blueprint, map, or save changes;
- no editor shutdown or Live Coding interruption for the compatibility lab;
- documentation and isolated lab work may continue.

ACFU remains a researched alternative only if the product explicitly pivots to
real-time action RPG. It is not part of this foundation.

The parallel character-presentation experiment is specified in
`Docs/MELODIA_JRPG_CHARACTER_SKILL_SLICE_2026-07-26.md`. It keeps JRPG combat
authority and evaluates Melusina only as a mesh/animation/impact presentation
layer.
