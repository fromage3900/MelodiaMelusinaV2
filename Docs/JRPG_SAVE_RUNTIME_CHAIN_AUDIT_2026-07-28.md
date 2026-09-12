# JRPG Runtime Chain and Narrative Save Audit

> **Current-state correction (2026-08-01):** This audit is historical evidence from 2026-07-28. `FMelodiaNarrativeRecord` is now version 2 with stepwise migration and persisted `SocialStats`; version-1/reset warnings below describe the pre-fix state. The canonical stock `BP_JRPGGameInstance.LoadThisGame` transaction remains authoritative, and a full process-restart round trip is still required. Do not introduce `UMelodiaSaveGameSubsystem::LoadFromSlot` as a competing load transaction.

**Date:** 2026-07-28  
**Mode:** Read-only source/config/evidence audit while interactive gameplay testing was in progress  
**Scope:** Active JRPG Blueprint authority chain, duplicate content roots, Melodia/Quill save boundary, replay and exactly-once risks

## Executive summary

The project has a coherent authority model. The top-level GameInstance selection is configuration-proven, and live asset export confirms the integration Blueprint contains `SyncNarrativeRecordToSave` and `RestoreNarrativeRecordFromSave` nodes. Runtime execution order, canonical save-object identity, and process-restart persistence still require PIE evidence.

Do not redesign combat or create another save owner. The only existing `MelusinaSlot0.sav` deserializes as legacy `/Script/MelodiaCore.MelodiaSaveGame`; it is not evidence for the canonical `BP_JRPGSaveGame` path. Prove one explicit canonical slot and restart round trip, then harden the existing `FMelodiaNarrativeRecord` transaction model.

## Evidence levels

- **Proven:** directly visible in current config or native source.
- **Reported:** recorded by a prior editor session or asset-index inspection, but not revalidated against current binary Blueprint graphs in this audit.
- **Unproven:** requires live Editor Reference Viewer, Blueprint graph inspection, or PIE evidence.

## Runtime authority chain

### Proven top-level configuration

`Config/DefaultEngine.ini` currently selects:

| Concern | Current configuration |
|---|---|
| Editor startup map | `/Game/Melodia/Levels/Opening/L_MelusinaMorning` |
| Game default map | `/Game/Melodia/Levels/Opening/L_MelusinaMorning` |
| GameInstance | `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance` |
| Global GameMode | `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode` |
| Viewport client | `/Script/CommonUI.CommonGameViewportClient` |

Map-level World Settings can override the global GameMode, so the effective class in `L_MelusinaMorning` must still be checked.

### Reported downstream chain

Existing project evidence reports:

1. `BP_MelodiaJRPGGameMode`
2. original working `/Game/TurnBasedJRPGTemplate/Blueprints/Controllers/BP_JRPGPlayerController`
3. `/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleBase`
4. `/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController`
5. stock `BP_BattleUI` and related widgets
6. `/Game/TurnBasedJRPGTemplate/Blueprints/Controllers/BP_JRPGGameInstance` save/map behavior behind the integration GameInstance

The integration PlayerController duplicate was reportedly not active because two inherited type mismatches prevented a clean switch. Preserve the original working controller until current editor inspection proves otherwise.

### Duplicate-root ambiguity

Both JRPG package roots exist:

- `/Game/TurnBasedJRPGTemplate`
- `/Game/_ThirdParty/TurnBasedJRPGTemplate`

Historical indexing found semantically different packages and cross-root references. This audit cannot prove the current package path of every binary Blueprint parent/property.

Before editing battle UI:

1. Open `L_MelusinaMorning` and check World Settings GameMode override.
2. Open `BP_MelodiaJRPGGameMode` and record `PlayerControllerClass`, Default Pawn, HUD, and GameState references.
3. Use Reference Viewer on the active PlayerController and battle actor.
4. In PIE, inspect the class paths of the active PlayerController, BattleController, and battle widget.
5. Edit only the packages proven active at runtime.

**Stop condition:** if a class resolves through both roots or the active package is unclear, do not save either duplicate until the reference chain is documented.

## Narrative save schema

### Proven native record

`FMelodiaNarrativeRecord` version 1 persists:

- `Version`
- `Flags`
- `ScriptCheckpoint`
- `ConsumedIntentIds`
- `ConsumedRewardIds`

The native subsystem reflects an exact Blueprint property:

```text
melodiaNarrativeRecord : FMelodiaNarrativeRecord
```

Both the property name and struct identity must match. A missing, renamed, or stale Blueprint field causes the bridge to reject save/load.

### Reported Blueprint transaction

Prior editor evidence reports that `BP_JRPGSaveGame` contains the correct version-1 field and that the integration GameInstance calls:

```text
Existing JRPG save flow
  -> SyncNarrativeRecordToSave
  -> SaveGameToSlot

Existing JRPG load flow
  -> RestoreNarrativeRecordFromSave
  -> Existing JRPG restoration
```

Those binary graph nodes were not revalidated during this read-only audit. Their execution order remains a runtime test requirement.

## Severity-ranked findings

### High — incompatible versions reset current in-memory narrative state

`RestoreNarrativeRecord` calls `ResetNarrativeRecord()` before rejecting a version mismatch. There is no migration or preservation path.

Risk:

- an old/new save can erase the current in-memory narrative record;
- failure cannot be inspected or migrated after reset;
- user progress can appear to revert to defaults.

Recommended correction after the current slice is proven:

1. Validate into a temporary record.
2. Migrate known versions explicitly.
3. Commit the migrated record only after complete validation.
4. Leave current state unchanged on unsupported versions and return a visible load error.

### High — in-flight battle state is not durable

`PendingEncounterId` and `bBattleCompletionConsumed` are transient and absent from the save record.

Risk:

- save/load during battle cannot reconstruct the transaction;
- Quill may restore before or after the battle notification independently;
- an encounter may replay, remain paused, or produce a result without a pending transaction.

Recommended policy for the first slice:

- disallow manual save during an active narrative battle;
- checkpoint immediately before the battle request and after terminal completion;
- on load, resume from a safe pre-battle or post-battle narrative checkpoint.

Longer-term option: persist a versioned encounter transaction containing transaction ID, encounter ID, phase, and terminal result.

### High — save wiring is reflection- and Blueprint-dependent

Native helpers are correct defensive boundaries, but there is no native/text caller proving that the current GameInstance invokes both helpers around the canonical transaction.

Required evidence:

- save log or breakpoint showing sync before `SaveGameToSlot`;
- load log or breakpoint showing restore after save-object load and before narrative continues;
- persisted flag/reward survives process restart, not only map travel.

### Medium — rewards and quests are consumed before downstream success

`CompleteQuest` and `GrantDialogueReward` add IDs to consumed arrays before broadcasting their delegates.

This provides at-most-once requests, not exactly-once successful effects. If no listener exists or a downstream operation fails, the ID remains consumed and retry is rejected.

Recommended correction:

- change downstream application to an acknowledged transaction;
- record `Pending`, then mark `Applied` only after the JRPG authority confirms success;
- alternatively have the authoritative listener return success through a narrow callable interface before consumption is committed.

Do not remove duplicate protection without replacing it with an acknowledged transaction.

### Medium — encounter replay policy is implicit

Battle and travel IDs are not added to `ConsumedIntentIds`. Only `melodia_battle_won` may be updated after battle, and only if allowlisted.

This may be intentional for repeatable encounters, but unique story encounters need explicit completion markers. Quill history alone should not silently define gameplay replay policy.

Recommended correction:

- classify encounters as repeatable or one-shot in project-owned data;
- persist completed one-shot encounter IDs or stable flags;
- reject unintended replay before world mutation.

### Medium — `ScriptCheckpoint` is currently unused

The field exists but no native read/write behavior populates or consumes it. Quill keeps its own variables/history and interpreter state.

Risk:

- the narrative record appears to provide a checkpoint but does not;
- load order between JRPG save data and Quill state is undefined;
- two persistence authorities can diverge.

Decision required:

1. Make `ScriptCheckpoint` authoritative and restore Quill to an explicit stable label, while keeping gameplay flags in the JRPG save; or
2. Remove/deprecate the unused field in a future migrated schema and explicitly document Quill persistence ordering.

For the first slice, explicit stable labels are safer than serializing a live interpreter.

### Medium — exactly-once completion depends on one active listener

The subsystem guards `CompleteBattle` with pending state and a consumed flag. `MelodiaBattleAdapter` also binds/unbinds the stock `OnBattleOver` delegate. That is useful defense in depth.

Still verify:

- exactly one battle actor matches the encounter tag;
- exactly one result delegate is bound;
- delegate is removed before or immediately after completion;
- repeated terminal callbacks are rejected without calling `Quill Next` twice.

### Low — collapsed rhythm prompt is not gameplay authority

`UMelodiaJRPGBattleOverlaySubsystem` creates a non-focusable, collapsed presentation widget and removes it on completion/abort. It does not complete battles or own controls. Do not rely on this overlay to prove the result path.

## Safe remediation order

1. **Capture active references** in Editor without saving assets.
2. **Run the current dialogue/battle test** and collect `MELUSINA_LOOP_*` logs.
3. **Prove save/load call order** with one flag and one reward in a disposable slot.
4. **Declare save-during-battle policy**; disable it for the first slice if currently possible.
5. **Fix UI prompts and mouse focus** only in the proven active JRPG widget root.
6. **Add transactional persistence** in a later schema revision:
   - migration-first restore;
   - pending/applied reward and quest state;
   - explicit one-shot encounter completion;
   - stable Quill checkpoint policy.
7. **Package-test** only after PIE victory, defeat, flee, duplicate callback, and process-restart save/load pass.

## Correlation checklist for the current gameplay test

Please capture answers or logs for these items:

### Startup and class chain

- [ ] Current map name
- [ ] Effective GameMode class path
- [ ] Active PlayerController class path
- [ ] Active battle actor/controller class path
- [ ] Active battle widget class path
- [ ] Whether any active class resolves under `_ThirdParty`

### Quill

- [ ] `MELUSINA_LOOP_QUILL_PLAY`
- [ ] `dialog=<valid object>` or `dialog=None`
- [ ] `in_viewport=true|false`
- [ ] Visible speaker/text
- [ ] Mouse can advance dialogue
- [ ] Keyboard can advance dialogue
- [ ] Choice selection works once

### Battle bridge

- [ ] `MELUSINA_LOOP_QUILL_NOTIFY message=melodia:battle:...`
- [ ] Adapter reports exactly one tagged encounter
- [ ] Skill applies damage once
- [ ] Terminal result is Victory, Defeat, or Fled
- [ ] `MELUSINA_LOOP_BATTLE_COMPLETED`
- [ ] `MELUSINA_LOOP_QUILL_RESTORE`
- [ ] `MELUSINA_LOOP_QUILL_NEXT`
- [ ] Dialogue resumes exactly once

### Save/load

- [ ] Save outside battle
- [ ] Set one allowlisted narrative flag
- [ ] Grant one disposable reward
- [ ] Save and exit the process
- [ ] Relaunch and load
- [ ] Flag restored
- [ ] Reward remains consumed/applied once
- [ ] Dialogue resumes at the expected stable point
- [ ] No load warning about missing/incompatible `melodiaNarrativeRecord`

## Pass criteria

The save boundary is not considered proven until a process restart demonstrates that the canonical JRPG slot restores the narrative record and does not duplicate a reward. The runtime chain is not considered proven until active class paths identify one specific package root through battle UI.

## Source references

- `Config/DefaultEngine.ini`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeTypes.h`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeSubsystem.h/.cpp`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaBattleAdapter.h/.cpp`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaJRPGBattleOverlaySubsystem.cpp`
- `AGENTS.md`
- ~~`C:\EnvironmentPortfolio\Docs\Gameplay\JRPG_QUILLSCRIPT_EXECUTION_STATUS_2026-07-26.md`~~
- ~~`C:\EnvironmentPortfolio\Docs\Gameplay\QWEN_DEEPSEEK_CORE_LOOP_HANDOFF_2026-07-27.md`~~

  *Struck 2026-07-31: neither path ever resolved — the `Docs/Gameplay/` folder does not exist.
  Allowlist authority is `DA_MelodiaIntegrationConfig -> TravelLevelIds`, written down in
  `Docs/MELODIA_UE58_INTEGRATION_ARCHITECTURE_2026-07-26.md` (§ "Initial allowlist").*

## Dated Persona-lite runtime evidence update — 2026-07-28

This update narrows several exploration-side uncertainties but does not close the canonical save gate.

### Newly proven

- Active Persona content is `/Game/MelodiaIntegration/Config/DA_MelodiaPersonaContent` with 4 abilities, 3 equipment definitions, 3 sequential quests, and 4 minimap markers.
- `/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation` has the expected four-entry stock skill unlock map and compiles cleanly.
- Active `BP_ExploreUI` contains one compiled Resonance Map panel. Rhythm Echo and Path Forward start collapsed and are refreshed by Persona quest-state changes; no parallel HUD exists.
- ZenForest Petal Priestess, Star Weaver, and Twilight Dancer actors have exact marker identity tags plus `MelodiaQuestNPC`, retain dialogue, and route interaction into the matching Persona quest ID.
- `UMelodiaPersonaSubsystem` maps Persona gear to concrete stock equipment classes and calls `BP_JRPGPlayerController.AddEquipmentToInventory` followed by `WearEquipmentOnUnit` when the stock controller is present.
- Editor Development build passed after the equipment, minimap-refresh, and NPC-notification bridges; both affected DLLs linked.
- Focused live readback passed for the unit, ExploreUI widget tree, and all three NPCs.
- Asynchronous PIE smoke `pie_smoke_2_163720` returned `ok=true`: quest 1 activated and completed, quest 2 activated, `melodia_smoke_encounter` became visible through `GetVisibleMinimapMarkers`, and `RequestEquip(melusina, melodia_tuning_fork)` was accepted. Active-runtime counts were zero for Blueprint Runtime Error, Accessed None, Traceback, and equipment-resolution warnings.

### Still unproven

- `ZenForestTest` uses `MelodiaSmokeCharacter` with a plain `PlayerController`; its Python wrapper has no stock `equipment` property. This prevents direct inventory readback on that exploration map and is not evidence of request rejection.
- Prove stock inventory mutation and equipped-unit state on a route where `BP_JRPGPlayerController` is the active authority.
- Prove equipment, active/completed Persona quest state, social stats, narrative flags, and consumed rewards survive a full canonical `BP_JRPGSaveGame` process restart.
- The Victory/Defeat/Fled/unavailable Quill result matrix, active battle widget package path, and exactly-once resume/reward behavior remain open.

The pass criteria above remain unchanged: focused Persona-lite smoke success does not certify canonical persistence or the full battle/narrative round trip.
