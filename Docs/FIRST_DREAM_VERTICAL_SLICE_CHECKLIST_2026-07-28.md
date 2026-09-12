# First Dream Vertical Slice — Editor Wiring and Playtest Checklist

**Date:** 2026-07-28  
**Scope:** one opening interaction, visible Quill dialogue and choice, one stock JRPG encounter, typed terminal result, one Quill resume, persistent completion/reward, and safe return.  
**Authority:** stock JRPG owns combat/results/inventory/save; Quill owns dialogue/choice sequencing; MelodiaIntegration validates stable-ID intents.

## Playable-game milestone — verified in PIE

**Runtime pass reported by the player on 2026-07-28:** Melusina approached Sir in `L_MelusinaMorning`, visible Quill dialogue played and advanced to completion, Sir performed the native departure/travel sequence, Dreamstate loaded under the integration GameMode, the player traversed Dreamstate, and the existing route reached the ZenForest test. This is the first verified playable opening traversal of the Persona-lite game loop.

This proves the opening interaction, managed Quill presentation, dialogue completion gate, single native departure authority, Morning-to-Dreamstate travel, Dreamstate traversal, and onward ZenForest route in one continuous PIE session. It does **not** by itself close the separate Victory/Defeat/Fled/unavailable result matrix, save persistence, battle-command accessibility, cook, or packaged-build checks below.

## Implemented Morning dialogue gate

`L_MelusinaMorning` now contains exactly one `BP_MelodiaSirMelodiousMorningIntro` instance at the original Sir transform. The Blueprint subclasses `AMelodiaSirMelodiousIntroActor`, preserves native departure/travel authority, and uses this verified chain:

1. `bDepartAfterReunion=false` prevents the native overlap timer from bypassing dialogue.
2. Actor overlap passes through `DoOnce`, spawns/casts one `AQuillscriptInterpreter`, and starts `/Game/MelodiaIntegration/Narrative/MelodiaMorningIntro`.
3. `MelodiaMorningIntro` contains five visible dialogue beats and finishes with `%melodia_morning_sir.BeginWindowDeparture` followed by `$ End`.
4. The Sir instance carries tag `melodia_morning_sir`; the Quill command therefore calls inherited `BeginWindowDeparture()` on the same actor after dialogue.
5. Native `BeginWindowDeparture()` remains the sole owner of departure animation, opening-flow notifications, and `OpenLevel`. No Blueprint travel authority was added.

Verified structural evidence: Blueprint compile status `UpToDate` with zero errors/warnings; exactly one Sir instance; original location `(-100, 810, 30)` and yaw `90`; auto-depart false; Morning Quill compiled to eight statements; zero dirty packages after save.

Verified runtime evidence: approaching Sir produced visible dialogue before movement; completing dialogue triggered departure; Dreamstate opened; the player traversed it and reached the ZenForest test.

## Same-day Editor run card

Use this order while testing. Do not advance to a later mutation until the preceding runtime identity/evidence is captured.

1. **Record effective startup classes (no edits)**
   - Open `/Game/Melodia/Levels/Opening/L_MelusinaMorning` and record its World Settings GameMode override.
   - Confirm the effective integration classes resolve through `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode` and `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance`.
   - Do not use `BP_MelodiaJRPGGameInstance_Config`; live inspection proved it is an empty stock child that bypasses the narrative sync/restore hooks.
   - Record the resolved PlayerController, Pawn, HUD, GameState, and package paths. A package path is required before touching either JRPG root.
2. **Prove the opening starts Quill (one interaction)**
   - Inspect `Morning_SirMelodious_STATIC_INTRO` and identify the exact interaction event/node that starts `/Game/MelodiaIntegration/Narrative/MelodiaQuillSmoke`.
   - PIE, interact once, and capture `MELUSINA_LOOP_QUILL_PLAY` including interpreter and dialog object names.
   - Stop if the log never appears: repair only the opening interaction/start call before investigating UI.
3. **Prove or repair visible dialogue and choices**
   - If the log reports `dialog=None`, inspect the Quill asset/project settings and assign the intended dialogue-box class.
   - If a valid dialog exists but is invisible, locate its actual `/Game` Widget Blueprint path at runtime and repair only that widget's `Play(Speaker, Text, Tags)` lifecycle.
   - Require visible speaker/text, one advance per click/key, clickable/focusable choices, and exactly one `OptionSelected` per choice. Stop on duplicate widgets or duplicate callbacks.
4. **Prove the encounter and active battle root**
   - During PIE run `Content/Python/persona_lite_runtime_probe.py` as an observer/driver.
   - Require exactly one actor tagged `melodia_smoke_encounter`; record actor label, class, containing map, and package path.
   - Start battle once, then use Widget Reflector/runtime inspection to record the instantiated battle HUD/widget package. This runtime path—not folder similarity—selects the active JRPG root.
   - Stop if encounter count is zero/multiple, the actor lacks the stock reflection surface, or more than one battle/HUD appears.
5. **Repair controls only in the proven active widget**
   - Expose focusable/clickable Attack, Skill, Item, and Flee controls with keyboard labels.
   - Route every `OnClicked` to the same stock event/function already used by controller/keyboard input. Do not calculate damage, select targets, or advance turns in UMG.
   - Test one mouse command and its keyboard equivalent; each must execute once. Verify initial focus, Back/Confirm, cursor, click/hover, and no exploration-input leakage.
6. **Prove each terminal round trip**
   - Run Victory, Defeat, Fled, and unavailable separately from clean state.
   - For each terminal battle require exactly one `MELUSINA_LOOP_BATTLE_COMPLETED`, one `MELUSINA_LOOP_QUILL_RESTORE`, and one `MELUSINA_LOOP_QUILL_NEXT`; unavailable must use the abort path.
   - Verify branch dialogue, reward/completion rules, one restored exploration state, and no stale battle/dialogue HUD.
7. **Prove canonical persistence last**
   - Open the runtime-selected stock save class and confirm exact property `melodiaNarrativeRecord : FMelodiaNarrativeRecord`.
   - In `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance`, prove `SyncNarrativeRecordToSave` executes before `SaveGameToSlot` and `RestoreNarrativeRecordFromSave` executes after load.
   - Use an explicit non-empty canonical slot name; the GameInstance CDO slot defaults are empty and the slot is supplied by the caller.
   - Save, fully stop PIE, start again, load, and verify completion persists and `melodia_smoke_reward` is not granted twice.
   - Load once with Quill unavailable and prove JRPG-owned map/party/inventory state remains readable.
   - Test a missing/unknown script or checkpoint and require an authored safe fallback without erasing valid current narrative state.

**Minimum evidence to retain:** effective class/package paths; opening start node screenshot; Quill play log; dialog and choice widget paths; encounter actor class/map/tag count; active battle widget path; one complete log per result; save/load graph screenshots; post-restart persistence result.

## Implemented text/code/config contract

- `MelodiaQuillSmoke.qsc` requests exactly one `melodia_smoke_encounter` battle.
- Native `EMelodiaBattleResult` is mirrored to the presentation-only Quill variable `melodia_battle_result` as `victory`, `defeat`, `fled`, or fail-closed `unavailable` before one resume.
- Victory grants `melodia_smoke_reward`; Victory, Defeat, and Fled set `melodia_smoke_complete=true`; unavailable/aborted startup grants and completes nothing.
- The compiler script reads the checked-in `.qsc` verbatim, verifies exact notifications/result branches/dialogue markers, compiles the asset, compares compiled source with disk source, verifies statements, and saves the asset.
- Packaging explicitly includes Morning, Dreamstate, the runtime-proven `/Game/ZenForestTest` destination, and the integration map, and always cooks `/Game/MelodiaIntegration/Narrative`. No unproven stock JRPG battle map was added.

## Editor-only wiring (active assets only)

Do not edit either duplicate JRPG root until PIE/Reference Viewer proves which one is instantiated.

1. **Compile Quill source**
   - In Unreal Editor, run `Content/Python/compile_melodia_quill_battle.py` through **Execute Python Script**.
   - Require `MELUSINA_QUILL_COMPILED` in Output Log and save `MelodiaQuillSmoke.uasset`.
   - If Quill rejects nested conditions, stop and record the parser error; do not hand-edit the generated asset.
2. **Opening interaction**
   - Open `L_MelusinaMorning` and inspect the intended NPC/interactable.
   - Confirm it starts `/Game/MelodiaIntegration/Narrative/MelodiaQuillSmoke` once.
   - Confirm the map/GameMode uses the configured integration GameMode and no level override points to a duplicate authority chain.
3. **Visible Quill UI**
   - PIE and require `MELUSINA_LOOP_QUILL_PLAY`.
   - If `dialog=None`, fix the Quill asset/settings dialogue class.
   - If the dialog exists but is not visible, modify only its active Widget Blueprint `Play(Speaker, Text, Tags)` override: populate content, add to viewport if unattached, set Visible, and focus a real advance button.
   - Confirm choice widgets create clickable/focusable buttons and call Quill `OptionSelected` exactly once.
4. **Encounter actor**
   - In the actual battle host map, identify the stock `BP_OffLevelBattleController`-compatible actor used by the working path.
   - Ensure exactly one actor is discoverable for stable ID/tag `melodia_smoke_encounter`.
   - Do not create a second battle controller or edit both JRPG roots.
5. **Battle command UI**
   - Identify the instantiated battle widget with Widget Reflector/runtime inspection.
   - On that widget only, expose focusable UButtons for `Attack [J]`, `Skill [K]`, `Item [I]`, and `Flee [F]` plus `Confirm [Enter/Space]` and `Back [Esc]` where relevant.
   - Route each `OnClicked` to the same stock function/event used by keyboard/controller input; UMG must not calculate damage or advance turns itself.
   - During command selection use Game-and-UI input, cursor/click/hover enabled, deterministic focus, and no exploration movement leakage.
6. **Canonical persistence**
   - Verify the active JRPG save class has the exact reflected `melodiaNarrativeRecord` property of type `FMelodiaNarrativeRecord`.
   - Verify save calls `SyncNarrativeRecordToSave` before serialization and load calls `RestoreNarrativeRecordFromSave` after deserialization.
   - Verify the reward delegate acknowledges `melodia_smoke_reward` through stock JRPG inventory/reward authority.

## PIE acceptance runs

### Exact first-test route after reopening

1. Open the project and confirm `L_MelodiaMainMenu` is the startup map.
2. PIE: require one `WBP_MainMenu`, visible cursor, and initial focus on `Btn_NewGame`.
3. Confirm Continue reads `CONTINUE - NO SAVE` and Load Game reads `LOAD GAME - LOCKED`; both must remain disabled.
4. Activate New Game and require travel to `L_MelusinaMorning` through `BP_MelodiaJRPGGameInstance::OnNewGameStarted`.
5. Interact with Sir once, advance visible Quill dialogue, and require the native departure path to load `L_Melodia_Dreamstate` exactly once.
6. Trigger the single `melodia_smoke_encounter` and confirm only one stock battle HUD appears.
7. Visually verify the themed Attack/Skill/Item/Flee presentation, turn order, unit details, boss panel, HP, MP, and action-time bars. Exercise one known working stock command and require one action/turn release.
8. Complete the available battle path and continue to `/Game/ZenForestTest`.
9. At every transition, reject duplicate HUDs, duplicate dialogue, duplicate input, duplicate rewards, or stale widgets.

This run is a runtime gate, not yet proven by headless validation. Capture the menu startup/New Game result and battle terminal result separately.

Run from a clean session for each result. Capture Output Log around the complete run.

### Shared sequence

1. Start in `L_MelusinaMorning`.
2. Interact once; visible speaker/text appears.
3. Select each opening option at least once across runs using both mouse and keyboard.
4. Require one `MELUSINA_LOOP_QUILL_NOTIFY message=melodia:battle:melodia_smoke_encounter`.
5. Require exactly one stock battle and one battle HUD.
6. Exercise one clickable command and its equivalent keyboard command without duplicate execution.

### Victory

- Require typed `result=victory`, then exactly one `QUILL_RESTORE` and one `QUILL_NEXT`.
- Require Victory dialogue, one reward notification, and one completion-flag notification.
- Save, reload, and verify `melodia_battle_won=true`, `melodia_smoke_complete=true`, and `melodia_smoke_reward` is not granted again.

### Defeat

- Require typed `result=defeat`, one resume/next, Defeat dialogue, completion flag, and no reward notification.
- Save/reload and verify the completion state persists.

### Fled

- Require typed `result=fled`, one resume/next, Fled dialogue, completion flag, and no reward notification.
- Verify cursor/input returns to the destination state and no stale battle HUD remains.

### Missing/duplicate encounter fail-closed check

- In a disposable test state only, make encounter discovery fail.
- Require `MELUSINA_LOOP_BATTLE_ABORTED`, `melodia_battle_result=unavailable` behavior, one narrative resume, unavailable dialogue, no reward, and no completion flag.
- Restore the valid encounter immediately after the check.

## Validation after the editor closes

1. Build `BS_GodFileEditor Win64 Development` with `-WaitMutex -NoHotReloadFromIDE -NoUBA`; confirm the final UBT `Result: Succeeded` line.
2. Run `verify_melodia_opening_levels.py` and inspect `Saved/Melodia/opening_level_verification.json`.
3. Re-run the Quill compiler in a commandlet/editor context and require its full source/statement checks.
4. Run the five `Melodia.CoreRules.Rhythm*` regression tests.
5. Cook/package Development with the explicit maps, then launch the packaged build and repeat the shared Victory path.

## Validation evidence — 2026-07-28

- **Dedicated front-end is statically validated:** `EditorStartupMap` and `GameDefaultMap` are `/Game/Melodia/Levels/Menu/L_MelodiaMainMenu`; its World Settings override resolves to `/Script/MelodiaCore.OrreryMainMenuGameMode`; the host defaults to `/Game/Melodia/UI/WBP_MainMenu`, creates no pawn/HUD, sets UI-only input, shows the cursor, and focuses `Btn_NewGame`.
- **Targeted UI commandlet passed its script assertions:** UE 5.8 loaded and compiled `WBP_MainMenu`, `BP_ActionButton`, `BP_TurnOrderList`, `BP_UnitBattleDetails`, `BP_BossUI`, `BP_HPBar`, `BP_MPBar`, and `BP_ActionTimeBar`, then loaded the menu map and checked its GameMode. `Python script executed successfully` is recorded in `Saved/Logs/VerticalSliceTargetedValidation.log`.
- **Configuration route is complete:** canonical GameInstance is `BP_MelodiaJRPGGameInstance`; cooked maps include Menu → Morning → Dreamstate → ZenForestTest plus the integration map.
- The targeted commandlet process still exits nonzero because Unreal reports the existing GameFeatureData Asset Manager startup error. `DefaultEngine.ini` visibly already contains the rule, so this is tracked without adding a duplicate.
- A broad `CompileAllBlueprints` diagnostic returned code 28 with 83 errors and 137 warnings in unrelated legacy assets (for example `BP_Ladder_PEN` and `BP_QuestManager`). It is diagnostic baseline only, not the acceptance gate for these touched assets.
- **No additional behavior fix was applied after review:** remaining gaps require PIE evidence or larger persistence/bridge work; changing them headlessly would increase risk before the environment lock.

- **First continuous playable traversal passed in PIE:** Morning Sir interaction → visible `MelodiaMorningIntro` dialogue → dialogue-completion-gated native departure → Dreamstate load/traversal → ZenForest test arrival.
- `MelodiaMorningIntro.uasset` is saved with eight compiled statements.
- `BP_MelodiaSirMelodiousMorningIntro` compiles `UpToDate` with zero errors/warnings. Morning contains exactly one instance at the preserved Sir transform, with `bDepartAfterReunion=false` and tag `melodia_morning_sir`.
- Dreamstate's effective override is `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode.BP_MelodiaJRPGGameMode_C`.
- Dreamstate contains exactly one `/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_InteractionBattle` tagged `melodia_smoke_encounter`, with one enemy-spawn and three player-spawn references. The active stock root is therefore `/Game/TurnBasedJRPGTemplate`.
- Final live authoring check reported zero dirty packages.
- `BS_GodFileEditor Win64 Development` completed with authoritative UBT `Result: Succeeded`.
- Current Quill compilation executed through `PythonScriptCommandlet`; `MelodiaQuillSmoke.uasset` was saved and the log records `MELUSINA_QUILL_COMPILED` with 42 statements, three notifications, and three post-battle markers. Evidence: `Saved/Logs/MelusinaFirstDreamQuillCompile.log`.
- The compiler verifier was corrected to stop searching dialogue text in compiled statements' `source_line`; exact compiled-source equality still proves all authored dialogue, while all three notifications retain compiled-statement checks.
- All five `Melodia.CoreRules.Rhythm*` tests passed with automation exit code 0. Evidence: `Saved/Logs/MelusinaRhythmAutomation.log`.
- Both opening maps load and report zero Map Check errors/warnings, but `verify_melodia_opening_levels.py` fails because `L_MelusinaMorning` lacks actor label `Morning_RoomShell`; no report JSON is produced until that contract is repaired.
- Win64 Development BuildCookRun built both Editor and game targets, then cook crashed with `LogUnrealNames: String is too long` and `Assertion failed: Header.Len != 0` (`UnrealNames.cpp:2428`). UAT returned 25 (`Error_UnknownCookFailure`), so no launchable archive is validated.

## Runtime update â€” 2026-07-29

- **New Game is runtime-proven:** the dedicated menu's New Game button creates
  the canonical stock `BP_JRPGSaveGame` in `MelusinaSlot0`, assigns it to the
  active integration GameInstance, and opens `L_MelusinaMorning`. The player
  verified this route in PIE. A VN-style intro segment may be inserted between
  this handoff and the room later; it must remain presentation/narrative only
  and must not become a second save or travel authority.
- **Keyboard prompt contract:** desktop UI should present readable keyboard
  labels rather than PS2 glyph-only overlays: Attack `J`, Skill `K`, Item `I`,
  Flee `F`, Interact `E`, Menu `~`, Confirm `Enter`/`Space`, Back `Esc`.
  Gamepad remains supported as an alternate input method.

## Current blockers / stop conditions

- Add or correctly label the intended room-shell actor as `Morning_RoomShell` in `L_MelusinaMorning`, save the map, and rerun the opening validator. This validator contract does not invalidate the successful PIE traversal.
- Diagnose the overlong/invalid serialized name that crashes UE 5.8 cook; packaging cannot be considered ready until BuildCookRun and packaged launch succeed.
- The encounter actor, tag count, spawn-reference cluster, integration GameMode, and active `/Game/TurnBasedJRPGTemplate` root are proven. The instantiated battle widget package path and full command-accessibility behavior still require runtime capture.
- Quill dialogue visibility and completion-gated Morning departure are proven in PIE. Choice accessibility and current canonical save Blueprint call sites remain unproven.
- PIE Victory, Defeat, Fled, and unavailable terminal-result/resume flows remain untested.
- Unreal startup reports that `GameFeatureData` lacks an Asset Manager rule even though `DefaultEngine.ini` contains one; verify the effective UE 5.8 config/class path while diagnosing cook.
- No additional stock JRPG battle map should be added to `MapsToCook` without runtime proof that off-level travel requires it; the current Dreamstate encounter uses the proven active root.
- GitHub LFS budget still blocks publishing the recovery branch.
