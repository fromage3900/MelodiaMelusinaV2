# Doc Health Report - 2026-09-01

**Mode:** Read-only

## Summary

| Metric | Value |
|---|---:|
| .md files scanned | 911 |
| Technical claims extracted | 2689 |
| Source headers indexed | 167 |
| C++ classes indexed | 79 |
| C++ functions indexed | 359 |
| Source mismatches (MISSING/STALE) | 1029 |
| Monolith mismatches | 0 |
| Cross-doc contradictions | 52 |
| Stale drive paths | 179 |
| Stale docs (>14d without update) | 439 |

## Source Cross-Reference Findings

Claims from docs that reference C++ names not found in scanned source trees.
Scanned: `Source/` + MelodiaCore, QuillScript, Monolith, UEBlueprintMCP plugin dirs.

### * MISSING - `cpp_file` (312 occurrences)

- `_ROADBLOCKS_2026-07-31.md:84` - `MelodiaMinimalHUD.cpp`
  - File `MelodiaMinimalHUD.cpp` not found under scanned Source/ or Plugins/ trees
  - _- `FSlateFontInfo` deprecations in `MelodiaMinimalHUD.cpp` become errors in a future engine version _
- `_ROADBLOCKS_2026-07-31.md:133` - `MelodiaRulesGenerated.h`
  - File `MelodiaRulesGenerated.h` not found under scanned Source/ or Plugins/ trees
  - _- **Generated files have been hand-edited.** `MelodiaRulesGenerated.h` carried seven `Opening*`_
- `AGENTS.md:361` - `PyWrapperTypeRegistry.cpp`
  - File `PyWrapperTypeRegistry.cpp` not found under scanned Source/ or Plugins/ trees
  - _Fatal error: PyWrapperTypeRegistry.cpp:2641_
- `AGENTS.md:473` - `UserDefinedStruct.h`
  - File `UserDefinedStruct.h` not found under scanned Source/ or Plugins/ trees
  - _`UserDefinedStruct.h` from `Engine/` to CoreUObject's `StructUtils/`._
- `CURRENT_STATE.md:105` - `MelodiaDungeonRunCoordinator.cpp`
  - File `MelodiaDungeonRunCoordinator.cpp` not found under scanned Source/ or Plugins/ trees
  - _- `NotifySirRescued()` fixed by another agent at `MelodiaDungeonRunCoordinator.cpp:474`, tests exten_
- `CURRENT_STATE.md:106` - `MelodiaCoreRulesTests.cpp`
  - File `MelodiaCoreRulesTests.cpp` not found under scanned Source/ or Plugins/ trees
  - _in `MelodiaCoreRulesTests.cpp`. Previously Sir Melodious could never join the party._
- `CURRENT_STATE.md:237` - `MonolithEditorActions.cpp`
  - File `MonolithEditorActions.cpp` not found under scanned Source/ or Plugins/ trees
  - _The `r.PSOPrecaching` capture fix (committed in `Plugins/Monolith/Source/MonolithEditor/Private/Mono_
- `SYSTEM_MAP.md:81` - `BPConnector.cpp`
  - File `BPConnector.cpp` not found under scanned Source/ or Plugins/ trees
  - _*   Commands: Programmatic graph manipulation and variable editing (`BPConnector.cpp`, `BPVariables._
- `SYSTEM_MAP.md:81` - `BPVariables.cpp`
  - File `BPVariables.cpp` not found under scanned Source/ or Plugins/ trees
  - _*   Commands: Programmatic graph manipulation and variable editing (`BPConnector.cpp`, `BPVariables._
- `Docs\_Reference\BP_INTEGRATION_REVIEW_2026-07-18.md:15` - `MelodiaBattleSession.cpp`
  - File `MelodiaBattleSession.cpp` not found under scanned Source/ or Plugins/ trees
  - _`MelodiaBattleSession.cpp` calls into two interfaces at real gameplay moments:_
- `Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md:15` - `MelodiaCombatStateComponent.cpp`
  - File `MelodiaCombatStateComponent.cpp` not found under scanned Source/ or Plugins/ trees
  - _- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCombatStateComponent.cpp`_
- `Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md:17` - `MelodiaRulesGenerated.h`
  - File `MelodiaRulesGenerated.h` not found under scanned Source/ or Plugins/ trees
  - _- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRulesGenerated.h`_
- `Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md:50` - `MelodiaBattleSession.cpp`
  - File `MelodiaBattleSession.cpp` not found under scanned Source/ or Plugins/ trees
  - _- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleSession.cpp`_
- `Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md:53` - `MelodiaCoreRulesLibrary.cpp`
  - File `MelodiaCoreRulesLibrary.cpp` not found under scanned Source/ or Plugins/ trees
  - _- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCoreRulesLibrary.cpp`_
- `Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md:115` - `MelodiaRoguelikeRunSubsystem.cpp`
  - File `MelodiaRoguelikeRunSubsystem.cpp` not found under scanned Source/ or Plugins/ trees
  - _- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRoguelikeRunSubsystem.cpp`_
- `Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md:132` - `MelodiaDungeonRunCoordinator.cpp`
  - File `MelodiaDungeonRunCoordinator.cpp` not found under scanned Source/ or Plugins/ trees
  - _- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaDungeonRunCoordinator.cpp`_
- `Docs\_Superseded\ROADMAP.md:22` - `BPVariables.cpp`
  - File `BPVariables.cpp` not found under scanned Source/ or Plugins/ trees
  - _*   [x] Fix C2665 compilation errors in `UnrealMCP` plugin (`BPVariables.cpp` / `BPConnector.cpp`) c_
- `Docs\_Superseded\ROADMAP.md:22` - `BPConnector.cpp`
  - File `BPConnector.cpp` not found under scanned Source/ or Plugins/ trees
  - _*   [x] Fix C2665 compilation errors in `UnrealMCP` plugin (`BPVariables.cpp` / `BPConnector.cpp`) c_
- `Docs\ASSET_PIPELINE_HARDENING_AND_AGENT_PROMPT_2026-07-14.md:39` - `MelodiaRulesGenerated.h`
  - File `MelodiaRulesGenerated.h` not found under scanned Source/ or Plugins/ trees
  - _- `MelodiaRulesGenerated.h` or `rules_generated.py` edited directly._
- `Docs\Backend\MELODIA_BACKEND_INTEGRATION_PLAN_2026-08-28.md:403` - `MelodiaEditorValidatorSubsystem.h`
  - File `MelodiaEditorValidatorSubsystem.h` not found under scanned Source/ or Plugins/ trees
  - _// Source/BS_GodFile/MelodiaIntegration/MelodiaEditorValidatorSubsystem.h_
- *... and 292 more*

### * MISSING - `system_ref` (717 occurrences)

- `_AGENT_WORKING_AGREEMENT.md:58` - `UMelodiaHairComponent`
  - Class `UMelodiaHairComponent` not indexed in any scanned Source/ or Plugins/ header
  - _Each of these appeared in `UMelodiaHairComponent` and cost roughly three days:_
- `_AUDIT_2026-08-05.md:47` - `UMelodiaExternalBridgeSubsystem`
  - Class `UMelodiaExternalBridgeSubsystem` not indexed in any scanned Source/ or Plugins/ header
  - _CRITICAL structural finding: the battle-start request `OnBattleRequested` is bound by BOTH `UMelodia_
- `_AUDIT_2026-08-05.md:47` - `UMelodiaBattleAdapterSubsystem`
  - Class `UMelodiaBattleAdapterSubsystem` not indexed in any scanned Source/ or Plugins/ header
  - _CRITICAL structural finding: the battle-start request `OnBattleRequested` is bound by BOTH `UMelodia_
- `_VERTICAL_SLICE_SCOPE.md:163` - `UMelodiaHairComponent`
  - Class `UMelodiaHairComponent` not indexed in any scanned Source/ or Plugins/ header
  - _- [x] Native C++ fallback staged in `UMelodiaHairComponent`: attach hair to `head_x`, retain Kawaii _
- `AGENTS.md:224` - `UMelodiaRhythmHUDWidget`
  - Class `UMelodiaRhythmHUDWidget` not indexed in any scanned Source/ or Plugins/ header
  - _5. **The HUD is shared, and the owning lane clears.** `UMelodiaRhythmHUDWidget` is driven by_
- `AGENTS.md:226` - `UMelodiaRhythmCombatSubsystem`
  - Class `UMelodiaRhythmCombatSubsystem` not indexed in any scanned Source/ or Plugins/ header
  - _`UMelodiaRhythmCombatSubsystem::PushHighwayToHUD`. The ambient lane must only clear a_
- `AGENTS.md:329` - `FMelodiaNarrativeRecord`
  - Class `FMelodiaNarrativeRecord` not indexed in any scanned Source/ or Plugins/ header
  - _`FMelodiaNarrativeRecord::ConsumedIntentIds` (SaveGame), so replaying the same authored beat after a_
- `AUTOMATION_SCRIPTS_README.md:119` - `FMelodiaRhythmEffectRequest`
  - Class `FMelodiaRhythmEffectRequest` not indexed in any scanned Source/ or Plugins/ header
  - _- Rhythm functions = presentation + one validated `FMelodiaRhythmEffectRequest` → stock resolver_
- `AUTOMATION_SCRIPTS_README.md:125` - `FMelodiaSongChart`
  - Class `FMelodiaSongChart` not indexed in any scanned Source/ or Plugins/ header
  - _3. MIDI parser (`MelodiaMidiParser`) outputs `FMelodiaSongChart` with `BasicChartNotes` array_
- `CURRENT_STATE.md:82` - `UMelodiaRhythmReactivitySubsystem`
  - Class `UMelodiaRhythmReactivitySubsystem` not indexed in any scanned Source/ or Plugins/ header
  - _- **UE→TD OSC (port 9000) now emits** — previously dead because every `UMelodiaRhythmReactivitySubsy_
- `CURRENT_STATE.md:98` - `AMelodiaGameMode`
  - Class `AMelodiaGameMode` not indexed in any scanned Source/ or Plugins/ header
  - _component is only created by `AMelodiaGameMode`, and the live game mode is `BP_MelodiaJRPGGameMode`._
- `CURRENT_STATE.md:114` - `UMelodiaOrreryRegistry`
  - Class `UMelodiaOrreryRegistry` not indexed in any scanned Source/ or Plugins/ header
  - _- `UMelodiaOrreryRegistry::IsSphereUnlocked` has zero callers; spheres gated at `RequiredPhase >= Si_
- `Docs\2026-07-29_PROJECT_HANDOFF.md:15` - `UMelodiaJRPGBattleOverlaySubsystem`
  - Class `UMelodiaJRPGBattleOverlaySubsystem` not indexed in any scanned Source/ or Plugins/ header
  - _- The keyboard legend is now a native, non-focusable presentation overlay owned by `UMelodiaJRPGBatt_
- `Docs\_Reference\BP_INTEGRATION_REVIEW_2026-07-18.md:26` - `IMelodiaEnemyPresentationInterface`
  - Class `IMelodiaEnemyPresentationInterface` not indexed in any scanned Source/ or Plugins/ header
  - _Checked `get_interfaces` on `BP_Melusina` (the player pawn target) and `BP_MelodiaEnemyBase` (the en_
- `Docs\_Reference\BP_INTEGRATION_REVIEW_2026-07-18.md:26` - `IMelodiaCombatPresentationInterface`
  - Class `IMelodiaCombatPresentationInterface` not indexed in any scanned Source/ or Plugins/ header
  - _Checked `get_interfaces` on `BP_Melusina` (the player pawn target) and `BP_MelodiaEnemyBase` (the en_
- `Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md:16` - `UMelodiaCombatStateComponent`
  - Class `UMelodiaCombatStateComponent` not indexed in any scanned Source/ or Plugins/ header
  - _- `UMelodiaCombatStateComponent::EvaluateModifier`_
- `Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md:128` - `AMelodiaDungeonRunCoordinator`
  - Class `AMelodiaDungeonRunCoordinator` not indexed in any scanned Source/ or Plugins/ header
  - _**Impact:** `AMelodiaDungeonRunCoordinator::CommitRewardAndAdvance` selects a reward and unlocks the_
- `Docs\_Superseded\MELODIA_ROGUELIKE_GAMELOOP_COMPLETION_PLAN_2026-07-14.md:25` - `AMelodiaGameMode`
  - Class `AMelodiaGameMode` not indexed in any scanned Source/ or Plugins/ header
  - _- `AMelodiaGameMode` subscribes to that event, but victory currently only returns the HUD and loop p_
- `Docs\_Superseded\MELODIA_ROGUELIKE_GAMELOOP_COMPLETION_PLAN_2026-07-14.md:44` - `UMelodiaRoguelikeRunSubsystem`
  - Class `UMelodiaRoguelikeRunSubsystem` not indexed in any scanned Source/ or Plugins/ header
  - _`UMelodiaRoguelikeRunSubsystem : UGameInstanceSubsystem`_
- `Docs\_Superseded\MELODIA_ROGUELIKE_GAMELOOP_COMPLETION_PLAN_2026-07-14.md:58` - `AMelodiaDungeonRunCoordinator`
  - Class `AMelodiaDungeonRunCoordinator` not indexed in any scanned Source/ or Plugins/ header
  - _`AMelodiaDungeonRunCoordinator`_
- *... and 697 more*

## Cross-Doc Contradictions

### `UMelodiaNarrativeSubsystem`

- Claimed present in 46 doc(s) and absent/broken in 5 doc(s)
- **Present-claiming docs:** 48H_CHANGE_REVIEW_2026-08-05.md, AGENTS.md, Docs\ECHO\campaign_02_battle_integration_map.md, Docs\ENVIRONMENT_SOURCE_OF_TRUTH_2026-08-11.md, Docs\GAME_FOUNDATION_PLAN_2026-08-11.md, Docs\Handoffs\CORE_LOOP_STATUS_AND_AGENT_PROMPTS_2026-08-07.md, Docs\Handoffs\EDITOR_UP_EXECUTION_CHECKLIST_2026-08-28.md, Docs\Handoffs\ENEMY_BATTLE_REPEAT_TEST_PLAN_2026-08-28.md, Docs\Handoffs\HOUDINI_WORLDGEN_DEEP_INTAKE_2026-08-28.md, Docs\Handoffs\MASTER_P0_CLOSEOUT_AND_LOOSE_ENDS_2026-08-28.md, Docs\Handoffs\MELODIA_GRIEF_HOOK_PRESENTATION_STATE_2026-08-01.md, Docs\Handoffs\MUSICAL_DREAM_BIOME_HANDOFF_2026-08-26.md, Docs\Handoffs\P0_CLOSEOUT_ACTION_PLAN_2026-08-28.md, Docs\Handoffs\P0_PHASE1_CLOSEOUT_AND_QUILL_TRIGGER_2026-08-28.md, Docs\Handoffs\QWEN_BATTLE_NARRATIVE_BINDING_2026-08-03.md, Docs\Handoffs\RESONANT_WORLD_GAMEPLAY_HANDOFF_2026-08-22.md, Docs\Handoffs\RESONANT_WORLD_MCP_TOOL_CALLS_2026-08-22.md, Docs\Handoffs\SESSION_CLOSEOUT_2026-08-20.md, Docs\Handoffs\SESSION_CLOSEOUT_2026-08-28_EVENING.md, Docs\Handoffs\UI_BRIDGE_SUBSYSTEM_AUTHORITY_2026-08-18.md, Docs\MELODIA_STORY_SEQUENCE_AND_QUILL_CONTRACT.md, Docs\MELODIA_STUDIO_QOL_CLOSURE_AND_LONGTERM_PLAN_2026-08-24.md, Docs\MELODIA_SYSTEMS_COMPOSITION_CONTRACT_2026-07-30.md, Docs\MELODIA_WARDROBE_ARCHITECTURE_2026-08-14.md, Docs\MELODIA_WARDROBE_PLUGIN_PLAN_2026-08-07.md, Docs\MELUSINA_AGENT_TEST_HARNESS.md, Docs\MELUSINA_CLAIREON_INTEGRATION_PLAN.md, Docs\OLLAMA_UE5_INTEGRATION_REPORT.md, Docs\ORCHESTRA_CONTRACT_2026-08-20.md, Docs\ORCHESTRA_CONVERGENCE_2026-08-20.md, Docs\P0_CLOSEOUT_PLAN_2026-08-28.md, Docs\P0_CLOSEOUT_TEST_PLAYBOOK_2026-08-24.md, Docs\P0_CONTENT_AND_QUESTS_PLAYTHROUGH_2026-08-27.md, Docs\Plans\DREAMANCHOR_EVENT_WIRING_SPEC_2026-08-31.md, Docs\Plans\LONG_TERM_GAMEPLAY_BP_T3D_PLAN_2026-08-14.md, Docs\Plans\MELODIA_INTEGRATION_MAP_OVERHAUL_2026-08-16.md, Docs\Plans\P2_P3_SYSTEM_PREPARATION_AND_ROADMAP_2026-08-31.md, Docs\Plans\REUSABLE_CHAPTER_VALIDATION_SYSTEM_2026-08-31.md, Docs\Portfolio\GAMEPLAY_SYSTEMS_CASE_STUDY_SOURCE_2026-08-24.md, Docs\Portfolio\PITCH_OPENCODE.md, Docs\RESONANT_WORLD_SYSTEM.md, Docs\Reports\Overnight\GAMEPLAY_AUTHORITY_ATLAS_2026-08-24.md, Docs\Research\AI_WORKFLOW_OPTIMIZATION_2026-08-03.md, Docs\Reviews\CORE_4_EDITABLE_BP_SYSTEMS_2026-08-09.md, Docs\UNFINISHED_AND_PLANNED_WORK_PREP_2026-08-24.md, Docs\WorldGen\WARDROBE_ORBITAL_GATE_SPEC_2026-08-27.md
- **Absent-claiming docs:** Docs\Backend\MELODIA_BACKEND_INTEGRATION_PLAN_2026-08-28.md, Docs\Handoffs\REMAINING_TASKS_EXECUTE_2026-08-13.md, Docs\JRPG_UI_QUILL_NEXT_IMPLEMENTATION_2026-07-28.md, Docs\MCP_MELODIA_SYSTEM.md, Docs\Research\DASH_MAGPIE_NATIVE_INTEGRATION_2026-08-31.md

### `UMelodiaHairComponent`

- Claimed present in 13 doc(s) and absent/broken in 4 doc(s)
- **Present-claiming docs:** Docs\BLUEPRINT_WIRING_CHECKLIST_2026-07-30.md, Docs\Handoffs\CORE_LOOP_STATUS_AND_AGENT_PROMPTS_2026-08-07.md, Docs\Handoffs\GEMINI_UI_POLISH_2026-07-31.md, Docs\Handoffs\KAWAII_HAIR_SKIRT_INTEGRATION_FIX_2026-08-29.md, Docs\Handoffs\TONIGHT_PORTFOLIO_STUDIO_PREP_2026-08-12.md, Docs\MELUSINA_ANIMATION_PIPELINE_REVIEW_2026-08-20.md, Docs\MELUSINA_HAIR_REEXPORT_CHECKLIST_2026-07-30.md, Docs\MELUSINA_IDLE_GEO_FIX_2026-08-20.md, Docs\MELUSINA_SIR_SKILL_UI_AUTHORING_2026-07-29.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-08-03.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-09-01.md, _AGENT_WORKING_AGREEMENT.md, _VERTICAL_SLICE_SCOPE.md
- **Absent-claiming docs:** Docs\Handoffs\CLINE_BLUEPRINT_WIRING_2026-07-31.md, Docs\Handoffs\CLINE_MONOLITH_COMMANDS_2026-07-31.md, Docs\Handoffs\QWEN_DEEPSEEK_PERSONA_LITE_2026-07-31.md, Docs\MELUSINA_NEXT_SESSION_PREP_2026-08-24.md

### `UMelodiaBattleAdapterSubsystem`

- Claimed present in 6 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Handoffs\CLINE_WIRING_EXECUTION_2026-08-06.md, Docs\MELODIA_AUTHORITATIVE_RHYTHM_COMBAT_WIRING_2026-08-03.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-08-03.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-09-01.md, Docs\Reviews\SESSION_REVIEW_2026-08-06.md, _AUDIT_2026-08-05.md
- **Absent-claiming docs:** Docs\Handoffs\QWEN_RHYTHM_SKILLS_SCOPE_2026-08-03.md

### `UMelodiaRhythmHUDWidget`

- Claimed present in 18 doc(s) and absent/broken in 2 doc(s)
- **Present-claiming docs:** AGENTS.md, Docs\Backend\UI_LONG_TERM_CLEANUP_INVENTORY_2026-08-28.md, Docs\ECHO\campaign_02_battle_integration_map.md, Docs\HANDOFF_P0_LOOKDEV_PHASE_2026-08-24.md, Docs\Handoffs\CLINE_WIRING_EXECUTION_2026-08-06.md, Docs\Handoffs\CLOSEOUT_SOURCE_VERDICTS_2026-08-11.md, Docs\Handoffs\CORE_SYSTEMS_HANDOFF_2026-08-09.md, Docs\Handoffs\GAMEMODE_029A_RETIREMENT_INVENTORY_2026-08-14.md, Docs\Handoffs\QWEN_HARMONIX_QUARTZ_BATTLE_INTEGRATION_2026-08-03.md, Docs\Handoffs\RHYTHM_SKILL_SYSTEM_EXPANSION_2026-08-03.md, Docs\Handoffs\RUNTIME_CONSOLIDATION_V3_2026-08-18.md, Docs\MELODIA_BATTLE_UI_INTEGRATION_2026-07-11.md, Docs\MELODIA_CUTE_UI_ELEMENTS_SPEC_2026-07-31.md, Docs\MELODIA_FIGMA_UI_WIRING_PLAN_2026-07-16.md, Docs\MELODIA_WIDGET_GAMEPLAY_INTEGRATION_2026-07-31.md, Docs\Production\MODEL_LANES_2026-08-12.md, Docs\Reports\Overnight\GAMEPLAY_AUTHORITY_ATLAS_2026-08-24.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-09-01.md
- **Absent-claiming docs:** Docs\Handoffs\MELODIA_HUB_SESSION_HANDOFF_2026-08-26.md, Docs\Handoffs\NEXT_AGENTS_PARALLEL_2026-08-13.md

### `UMelodiaBattleSession`

- Claimed present in 13 doc(s) and absent/broken in 2 doc(s)
- **Present-claiming docs:** AGENTS.md, Docs\AUDIO_IMMERSION_PLAN_2026-08-09.md, Docs\Backend\UI_LONG_TERM_CLEANUP_INVENTORY_2026-08-28.md, Docs\Handoffs\BP_NATIVE_SURFACE_AUDIT_2026-08-14.md, Docs\Handoffs\GAMEMODE_029A_RETIREMENT_INVENTORY_2026-08-14.md, Docs\Handoffs\MUSICAL_DREAM_BIOME_HANDOFF_2026-08-26.md, Docs\Handoffs\PARALLEL_LANES_2026-08-08.md, Docs\Handoffs\QWEN_BATTLE_NARRATIVE_BINDING_2026-08-03.md, Docs\Handoffs\TENSION_AUDIO_REACTIVITY_2026-08-15.md, Docs\Reports\Overnight\GAMEPLAY_AUTHORITY_ATLAS_2026-08-24.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-08-03.md, Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md, Docs\_Superseded\MELODIA_ROGUELIKE_GAMELOOP_COMPLETION_PLAN_2026-07-14.md
- **Absent-claiming docs:** Docs\Handoffs\BLACKBOX_AUDIT_COMPLETE_2026-08-01.md, Docs\SCAFFOLDING_DEEP_REVIEW_LIVE_INTEGRATION_2026-07-24.md

### `UMelodiaRhythmCombatSubsystem`

- Claimed present in 29 doc(s) and absent/broken in 3 doc(s)
- **Present-claiming docs:** AGENTS.md, Docs\BLUEPRINT_WIRING_CONTRACT_2026-08-07.md, Docs\BLUEPRINT_WIRING_SKILL_2026-08-07.md, Docs\Backend\UI_LONG_TERM_CLEANUP_INVENTORY_2026-08-28.md, Docs\ECHO\campaign_01_rhythm_damage_delta.md, Docs\ENVIRONMENT_SOURCE_OF_TRUTH_2026-08-11.md, Docs\HANDOFF_P0_LOOKDEV_PHASE_2026-08-24.md, Docs\Handoffs\BP_NATIVE_SURFACE_AUDIT_2026-08-14.md, Docs\Handoffs\CLINE_WIRING_EXECUTION_2026-08-06.md, Docs\Handoffs\CORE_LOOP_STATUS_AND_AGENT_PROMPTS_2026-08-07.md, Docs\Handoffs\CURRENT_P0_STATUS_2026-08-25.md, Docs\Handoffs\DEEPSEEK_BLUEPRINT_WIRING_HANDOFF_2026-08-03.md, Docs\Handoffs\ENEMY_BATTLE_REPEAT_TEST_PLAN_2026-08-28.md, Docs\Handoffs\INTEGRATION_POLISH_HANDOFFS_2026-08-06.md, Docs\Handoffs\KIMI_UI_WIRING_NOTES_2026-08-03.md, Docs\Handoffs\MUSICAL_DREAM_BIOME_HANDOFF_2026-08-26.md, Docs\Handoffs\PARALLEL_LANES_2026-08-08.md, Docs\Handoffs\RHYTHM_SKILL_SYSTEM_EXPANSION_2026-08-03.md, Docs\Handoffs\RUNTIME_CONSOLIDATION_V3_2026-08-18.md, Docs\Handoffs\UI_BRIDGE_SUBSYSTEM_AUTHORITY_2026-08-18.md, Docs\MULTI_AGENT_DELEGATION_PROMPTS_2026-08-03.md, Docs\OLLAMA_UE5_INTEGRATION_REPORT.md, Docs\ORCHESTRA_CONTRACT_2026-08-20.md, Docs\Portfolio\GAMEPLAY_SYSTEMS_CASE_STUDY_SOURCE_2026-08-24.md, Docs\Portfolio\PITCH_OPENCODE.md, Docs\Reports\Overnight\GAMEPLAY_AUTHORITY_ATLAS_2026-08-24.md, Docs\Reviews\CORE_4_EDITABLE_BP_SYSTEMS_2026-08-09.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-08-03.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-09-01.md
- **Absent-claiming docs:** Docs\Handoffs\QWEN_HARMONIX_QUARTZ_BATTLE_INTEGRATION_2026-08-03.md, Docs\Research\DASH_MAGPIE_NATIVE_INTEGRATION_2026-08-31.md, Docs\Reviews\RHYTHM_WALLET_REVIEW_2026-08-03.md

### `FMelodiaNarrativeRecord`

- Claimed present in 21 doc(s) and absent/broken in 5 doc(s)
- **Present-claiming docs:** AGENTS.md, Docs\AGENT_MCP_CHEAT_SHEET.md, Docs\Backend\MELODIA_BACKEND_INTEGRATION_PLAN_2026-08-28.md, Docs\FIRST_DREAM_VERTICAL_SLICE_CHECKLIST_2026-07-28.md, Docs\Handoffs\BEDROCK_LEDGER_LANES_2026-08-14.md, Docs\Handoffs\GPT_HANDOFF_2026-08-14_EVENING.md, Docs\Handoffs\KIRO_CLAUDE_CLINE_EVENING_CORE_LOOP_2026-08-01.md, Docs\Handoffs\MELODIA_CONVERGENCE_CLOSEOUT_AND_P0_PLAN_2026-08-24.md, Docs\Handoffs\PROCEDURAL_DUNGEON_REACTIVATION_2026-08-14.md, Docs\Handoffs\QWEN_DEEPSEEK_PERSONA_LITE_2026-07-31.md, Docs\MELODIA_SYSTEMS_COMPOSITION_CONTRACT_2026-07-30.md, Docs\MELODIA_WARDROBE_ARCHITECTURE_2026-08-14.md, Docs\MELODIA_WARDROBE_HANDOFF_2026-08-07.md, Docs\MELODIA_WARDROBE_PLUGIN_PLAN_2026-08-07.md, Docs\P0_CLOSEOUT_PLAN_2026-08-28.md, Docs\Plans\P2_P3_SYSTEM_PREPARATION_AND_ROADMAP_2026-08-31.md, Docs\Research\MELODIA_PSYCH_MUSIC_INDIE_REFERENCE_2026-07-31.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-09-01.md, Docs\Reviews\TRAVERSAL_SAVE_REVIEW_2026-08-03.md, Docs\WEBSITE_OVERHAUL_LEVEL_MAPPING_2026-07-31.md, Docs\WorldGen\WARDROBE_ORBITAL_GATE_SPEC_2026-08-27.md
- **Absent-claiming docs:** Docs\Handoffs\CODEX_WARDROBE_CORE_CPP_INTEGRATION_REVIEW_2026-08-15.md, Docs\JRPG_SAVE_RUNTIME_CHAIN_AUDIT_2026-07-28.md, Docs\MCP_MELODIA_SYSTEM.md, Docs\Plans\MELODIA_PROGRESSION_GATING_DESIGN_2026-08-14.md, Docs\Reviews\JRPG_BLUEPRINT_CHAIN_REVIEW_2026-08-03.md

### `UMelodiaRhythmReactivitySubsystem`

- Claimed present in 24 doc(s) and absent/broken in 2 doc(s)
- **Present-claiming docs:** Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md, Docs\HANDOFF_P0_LOOKDEV_PHASE_2026-08-24.md, Docs\Handoffs\CLAUDE_KIRO_TANDEM_PREP_2026-08-01.md, Docs\Handoffs\CLAUDE_REBUILD_VALIDATION_HANDOFF_2026-08-01.md, Docs\Handoffs\DREAMPRINT_AUDIO_REACTIVITY_PREP_2026-08-18.md, Docs\Handoffs\FX_PPV_UI_INTEGRATION_HANDOFF_2026-08-01.md, Docs\Handoffs\HOUDINI_WORLDGEN_DEEP_INTAKE_2026-08-28.md, Docs\Handoffs\PPV_FINALIZE_PLAN_2026-08-26.md, Docs\Handoffs\QWEN_HARMONIX_QUARTZ_BATTLE_INTEGRATION_2026-08-03.md, Docs\Handoffs\TENSION_AUDIO_REACTIVITY_2026-08-15.md, Docs\Monoliths\P1_FARAWAY_MOTHER_PLAN_2026-08-29.md, Docs\Monoliths\P2_GOD_THAT_MOLTS_MECHANICS_RESEARCH_2026-08-29.md, Docs\NIAGARA_ECOSYSTEM_2026-08-09.md, Docs\OCEANOLOGY_STYLIZATION_AND_TRAVERSAL_INTEGRATION_RESEARCH_2026-08-29.md, Docs\ORCHESTRA_CONTRACT_2026-08-20.md, Docs\Production\PCG\SCALE_FIRST_MUSICAL_PCG_PLAN_2026-08-10.md, Docs\Production\PCG\SCALE_FIRST_MUSICAL_PCG_PLAN_REVIEW_2026-08-10.md, Docs\Research\UE58_EXPLORATION_WORLD_BUILDING_RESEARCH_2026-08-29.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-09-01.md, Docs\Reviews\MUSIC_RHYTHM_REVIEW_2026-08-03.md, Docs\Reviews\RHYTHM_WALLET_REVIEW_2026-08-03.md, Docs\SCAFFOLDING_DEEP_REVIEW_LIVE_INTEGRATION_2026-07-24.md, Docs\UNIVERSAL_MUSICAL_INFLUENCE_SCAFFOLD_2026-07-18.md, Docs\phase_14_wiring_spec.md
- **Absent-claiming docs:** CURRENT_STATE.md, Docs\QUEUE.md

### `AMelodiaGameMode`

- Claimed present in 10 doc(s) and absent/broken in 3 doc(s)
- **Present-claiming docs:** CURRENT_STATE.md, Docs\BLUEPRINT_WIRING_CONTRACT_2026-08-07.md, Docs\Handoffs\BP_AUTHORITY_READINESS_AUDIT_2026-08-14.md, Docs\Handoffs\RUNTIME_CONSOLIDATION_V3_2026-08-18.md, Docs\MELODIA_FIGMA_UI_WIRING_PLAN_2026-07-16.md, Docs\Plans\MELODIA_INFINITY_NIKKI_PIPELINE_UPDATE_2026-08-14.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-08-03.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-09-01.md, Docs\WEBSITE_OVERHAUL_LEVEL_MAPPING_2026-07-31.md, Docs\_Superseded\MELODIA_ROGUELIKE_GAMELOOP_COMPLETION_PLAN_2026-07-14.md
- **Absent-claiming docs:** Docs\Handoffs\GAMEMODE_029A_RETIREMENT_INVENTORY_2026-08-14.md, Docs\Handoffs\P0_INTEGRATION_HANDOFF_2026-08-20.md, Docs\ORCHESTRA_CONTRACT_2026-08-20.md

### `UMelodiaJRPGBattleOverlaySubsystem`

- Claimed present in 9 doc(s) and absent/broken in 2 doc(s)
- **Present-claiming docs:** Docs\Backend\UI_LONG_TERM_CLEANUP_INVENTORY_2026-08-28.md, Docs\Evidence\2026-08-23_hud_single_writer.md, Docs\Handoffs\INTEGRATION_POLISH_HANDOFFS_2026-08-06.md, Docs\Handoffs\UI_BRIDGE_SUBSYSTEM_AUTHORITY_2026-08-18.md, Docs\MELODIA_AUTHORITATIVE_RHYTHM_COMBAT_WIRING_2026-08-03.md, Docs\Portfolio\GAMEPLAY_SYSTEMS_CASE_STUDY_SOURCE_2026-08-24.md, Docs\Reports\Overnight\GAMEPLAY_AUTHORITY_ATLAS_2026-08-24.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-08-03.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-09-01.md
- **Absent-claiming docs:** Docs\2026-07-29_PROJECT_HANDOFF.md, Docs\JRPG_SAVE_RUNTIME_CHAIN_AUDIT_2026-07-28.md

### `IMelodiaEnemyPresentationInterface`

- Claimed present in 3 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\PRESENTATION_INTERFACE_INTEGRATION_PROPOSAL_2026-07-18.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-08-03.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-09-01.md
- **Absent-claiming docs:** Docs\_Reference\BP_INTEGRATION_REVIEW_2026-07-18.md

### `IMelodiaCombatPresentationInterface`

- Claimed present in 4 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md, Docs\PRESENTATION_INTERFACE_INTEGRATION_PROPOSAL_2026-07-18.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-08-03.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-09-01.md
- **Absent-claiming docs:** Docs\_Reference\BP_INTEGRATION_REVIEW_2026-07-18.md

### `UMelodiaCombatStateComponent`

- Claimed present in 3 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Reviews\DOC_HEALTH_REPORT_2026-08-03.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-09-01.md, Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md
- **Absent-claiming docs:** Docs\_Superseded\NEXT_HIGHEST_LEVERAGE_TASK.md

### `AMelodiaDungeonRunCoordinator`

- Claimed present in 7 doc(s) and absent/broken in 2 doc(s)
- **Present-claiming docs:** Docs\Handoffs\CORE_LOOP_STATUS_AND_AGENT_PROMPTS_2026-08-07.md, Docs\Handoffs\CORE_SYSTEMS_HANDOFF_2026-08-09.md, Docs\Handoffs\PARALLEL_LANES_2026-08-08.md, Docs\Handoffs\PROCEDURAL_DUNGEON_REACTIVATION_2026-08-14.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-08-03.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-09-01.md, Docs\_Superseded\MELODIA_ROGUELIKE_GAMELOOP_COMPLETION_PLAN_2026-07-14.md
- **Absent-claiming docs:** Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md, Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md

### `UMelodiaTokenWalletSubsystem`

- Claimed present in 22 doc(s) and absent/broken in 4 doc(s)
- **Present-claiming docs:** Docs\Backend\UI_LONG_TERM_CLEANUP_INVENTORY_2026-08-28.md, Docs\ENVIRONMENT_SOURCE_OF_TRUTH_2026-08-11.md, Docs\HANDOFF_P0_LOOKDEV_PHASE_2026-08-24.md, Docs\Handoffs\CLAUDE_TO_KIRO_STATE_2026-08-01.md, Docs\Handoffs\CLINE_TOKEN_BRANCH_VERIFICATION_2026-08-01.md, Docs\Handoffs\GPT_HANDOFF_2026-08-14_EVENING.md, Docs\Handoffs\KIRO_MELODY_TOKEN_INTEGRATION_2026-08-01.md, Docs\Handoffs\MELODIA_HUB_SESSION_HANDOFF_2026-08-26.md, Docs\Handoffs\QWEN_RHYTHM_SKILLS_SCOPE_2026-08-03.md, Docs\Handoffs\SESSION_CLOSEOUT_2026-08-14_CLAUDE.md, Docs\MELODIA_WARDROBE_ARCHITECTURE_2026-08-14.md, Docs\MELODIA_WARDROBE_PLUGIN_PLAN_2026-08-07.md, Docs\MULTI_AGENT_DELEGATION_PROMPTS_2026-08-03.md, Docs\Plans\MELODIA_PROGRESSION_GATING_DESIGN_2026-08-14.md, Docs\Plans\MELUSINA_V2_REBUILD_AND_INFINITY_NIKKI_WARDROBE_PLAN_2026-08-14.md, Docs\Reports\DUPLICATE_TREE_AUDIT_2026-08-14.md, Docs\Reports\Overnight\GAMEPLAY_AUTHORITY_ATLAS_2026-08-24.md, Docs\Reports\WARDROBE_CONTENT_CONTRACT_GAPS_2026-08-14.md, Docs\Research\MELODIA_WARDROBE_RESEARCH_SUMMARY_2026-08-14.md, Docs\Research\QWEN_WARDROBE_COMPARISON_AND_ROADMAP_2026-08-14.md, Docs\Reviews\TRAVERSAL_SAVE_REVIEW_2026-08-03.md, Docs\_Superseded\_AGENT_GOALS_2026-08-02.md
- **Absent-claiming docs:** Docs\Handoffs\BLACKBOX_AUDIT_COMPLETE_2026-08-01.md, Docs\Handoffs\CODEX_TOKEN_WALLET_BP_2026-08-14.md, Docs\MELODIA_WARDROBE_HANDOFF_2026-08-07.md, Docs\Reports\CLAUDE_SESSION_REPORT_2026-08-15.md

### `UMelodiaRoguelikeRunSubsystem`

- Claimed present in 11 doc(s) and absent/broken in 3 doc(s)
- **Present-claiming docs:** Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md, Docs\Handoffs\BLACKBOX_AUDIT_COMPLETE_2026-08-01.md, Docs\Handoffs\BLACKBOX_HANDOFF_2026-08-01.md, Docs\Handoffs\CLAUDE_TO_KIRO_STATE_2026-08-01.md, Docs\Handoffs\CLINE_TOKEN_BRANCH_VERIFICATION_2026-08-01.md, Docs\Handoffs\KIRO_MELODY_TOKEN_INTEGRATION_2026-08-01.md, Docs\Handoffs\PARALLEL_LANES_2026-08-08.md, Docs\Reports\WBP_BINDING_MATRIX_2026-08-14.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-08-03.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-09-01.md, Docs\_Superseded\MELODIA_ROGUELIKE_GAMELOOP_COMPLETION_PLAN_2026-07-14.md
- **Absent-claiming docs:** Docs\Handoffs\QWEN_RHYTHM_SKILLS_SCOPE_2026-08-03.md, Docs\MELODIA_TRANSITION_SYSTEM_CONTRACT.md, Docs\Reviews\RHYTHM_WALLET_REVIEW_2026-08-03.md

### `UMelodiaSaveGameSubsystem`

- Claimed present in 5 doc(s) and absent/broken in 2 doc(s)
- **Present-claiming docs:** Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md, Docs\Handoffs\CONTINUATION_2026-08-14_NIGHT.md, Docs\Reports\Overnight\GAMEPLAY_AUTHORITY_ATLAS_2026-08-24.md, Docs\Reports\WBP_BINDING_MATRIX_2026-08-14.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-08-03.md
- **Absent-claiming docs:** Docs\Handoffs\BLACKBOX_AUDIT_COMPLETE_2026-08-01.md, Docs\MELODIA_FIGMA_UI_WIRING_PLAN_2026-07-16.md

### `IMelodiaDungeonRecipeConsumer`

- Claimed present in 3 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\COORDINATOR_DEEP_REVIEW_2026-07-17.md, Docs\Handoffs\GPT_HANDOFF_2026-08-14_EVENING.md, Docs\VERTICAL_SLICE_20MIN_REVIEW_2026-07-17.md
- **Absent-claiming docs:** Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md

### `EMelodiaWardrobeSlot`

- Claimed present in 2 doc(s) and absent/broken in 4 doc(s)
- **Present-claiming docs:** Docs\Architecture\MELUSINA_V2_RUNTIME_CONTRACT.md, Docs\MELODIA_WARDROBE_HANDOFF_2026-08-07.md
- **Absent-claiming docs:** Docs\Handoffs\GPT_HANDOFF_2026-08-14_EVENING.md, Docs\Handoffs\REMAINING_TASKS_EXECUTE_2026-08-13.md, Docs\MELODIA_WARDROBE_PLUGIN_PLAN_2026-08-07.md, Docs\Reports\WARDROBE_CONTENT_CONTRACT_GAPS_2026-08-14.md

### `UMelodiaWardrobeComponent`

- Claimed present in 8 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Architecture\MELUSINA_V2_RUNTIME_CONTRACT.md, Docs\Evidence\P0_EXPLORATION_WARDROBE_GLIDE_PORTAL_PROBE_2026-08-31.md, Docs\Handoffs\CODEX_WARDROBE_CORE_CPP_INTEGRATION_REVIEW_2026-08-15.md, Docs\Handoffs\WARDROBE_REBUILD_AND_WIRING_2026-08-15.md, Docs\MELODIA_WARDROBE_PLUGIN_PLAN_2026-08-07.md, Docs\ORCHESTRA_CONVERGENCE_2026-08-20.md, Docs\Plans\MELUSINA_ANIM_NEXT_LEVEL_AND_OUTFIT_CORE_2026-08-16.md, Docs\Reports\Overnight\GAMEPLAY_AUTHORITY_ATLAS_2026-08-24.md
- **Absent-claiming docs:** Docs\Plans\MELUSINA_V2_REBUILD_AND_INFINITY_NIKKI_WARDROBE_PLAN_2026-08-14.md

### `FMelodiaEnemyDef`

- Claimed present in 2 doc(s) and absent/broken in 3 doc(s)
- **Present-claiming docs:** Docs\COORDINATOR_DEEP_REVIEW_2026-07-17.md, Docs\TOMORROW_2026-07-18_ARTIST_DAY_PLAN.md
- **Absent-claiming docs:** Docs\ASSET_PIPELINE_HARDENING_AND_AGENT_PROMPT_2026-07-14.md, Docs\Handoffs\VRM4U_NPC_PLACEHOLDERS_2026-08-14.md, Docs\MELODIA_NPC_VRM4U_READINESS_2026-07-11.md

### `UMelodiaPCGNarrativeChallengeBridgeComponent`

- Claimed present in 13 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Backend\MELODIA_BACKEND_INTEGRATION_PLAN_2026-08-28.md, Docs\Handoffs\HOUDINI_WORLDGEN_DEEP_INTAKE_2026-08-28.md, Docs\Handoffs\P0_INTEGRATION_HANDOFF_2026-08-20.md, Docs\Handoffs\P0_SHIP_NIGHT_CLOSEOUT_2026-08-28.md, Docs\Handoffs\RESONANT_WORLD_GAMEPLAY_HANDOFF_2026-08-22.md, Docs\ORCHESTRA_CONTRACT_2026-08-20.md, Docs\P0_CLOSEOUT_PLAN_2026-08-28.md, Docs\Portfolio\GAMEPLAY_SYSTEMS_CASE_STUDY_SOURCE_2026-08-24.md, Docs\Reports\Overnight\GAMEPLAY_AUTHORITY_ATLAS_2026-08-24.md, Docs\Research\RIDER_SEA_ABOVE_P0_WORKFLOWS_2026-08-28.md, Docs\UE_IMPORT_VERIFICATION_2026-08-24.md, Docs\UE_LIVE_GAMEPLAY_ASSEMBLY_2026-08-24.md, Docs\WorldGen\WARDROBE_ORBITAL_GATE_SPEC_2026-08-27.md
- **Absent-claiming docs:** Docs\ORCHESTRA_CONVERGENCE_2026-08-20.md

### `UMelodiaUIBridgeSubsystem`

- Claimed present in 12 doc(s) and absent/broken in 2 doc(s)
- **Present-claiming docs:** Docs\Backend\UI_LONG_TERM_CLEANUP_INVENTORY_2026-08-28.md, Docs\Evidence\2026-08-23_hud_single_writer.md, Docs\Handoffs\CORE_LOOP_STATUS_AND_AGENT_PROMPTS_2026-08-07.md, Docs\Handoffs\INTEGRATION_POLISH_HANDOFFS_2026-08-06.md, Docs\Handoffs\MELODIA_CONVERGENCE_CLOSEOUT_AND_P0_PLAN_2026-08-24.md, Docs\Handoffs\RUNTIME_CONSOLIDATION_V3_2026-08-18.md, Docs\Handoffs\UI_WBP_LOOKDEV_FINALIZATION_PLAN_2026-08-28.md, Docs\Handoffs\WBP_SYSTEMS_DEEP_DIVE_AND_P0_QUICK_WINS_2026-08-28.md, Docs\ORCHESTRA_CONTRACT_2026-08-20.md, Docs\ORCHESTRA_CONVERGENCE_2026-08-20.md, Docs\Portfolio\GAMEPLAY_SYSTEMS_CASE_STUDY_SOURCE_2026-08-24.md, Docs\Reports\Overnight\GAMEPLAY_AUTHORITY_ATLAS_2026-08-24.md
- **Absent-claiming docs:** Docs\Handoffs\EXTREME_INVENTORY_DUPLICATE_ASSET_CRISIS_2026-08-18.md, Docs\Handoffs\UI_BRIDGE_SUBSYSTEM_AUTHORITY_2026-08-18.md

### `UMelodiaBattleInputComponent`

- Claimed present in 5 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\BLUEPRINT_WIRING_CONTRACT_2026-08-07.md, Docs\Handoffs\BP_AUTHORITY_READINESS_AUDIT_2026-08-14.md, Docs\Handoffs\GAMEMODE_029A_RETIREMENT_INVENTORY_2026-08-14.md, Docs\Handoffs\P0_INTEGRATION_HANDOFF_2026-08-20.md, Docs\Reports\Overnight\GAMEPLAY_AUTHORITY_ATLAS_2026-08-24.md
- **Absent-claiming docs:** Docs\ORCHESTRA_CONTRACT_2026-08-20.md

### `AMelodiaChoralSheepActor`

- Claimed present in 3 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\CHORAL_SHEEP_INTEGRATION_RUNBOOK.md, Docs\HANDOFF_P0_LOOKDEV_PHASE_2026-08-24.md, Docs\MELUSINA_NEXT_SESSION_PREP_2026-08-24.md
- **Absent-claiming docs:** Docs\Handoffs\CHORAL_SHEEP_GROOM_VARIANTS_2026-08-28.md

### `UMelodiaGameUserSettings`

- Claimed present in 4 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\CORE_QOL_AUDIT_2026-07-29.md, Docs\FOUNDATION_LOCKIN_PLAN_2026-07-30.md, Docs\Handoffs\PROCEDURAL_DUNGEON_REACTIVATION_2026-08-14.md, Docs\MELODIA_WIDGET_GAMEPLAY_INTEGRATION_2026-07-31.md
- **Absent-claiming docs:** Docs\MELODIA_SYSTEMS_COMPOSITION_CONTRACT_2026-07-30.md

### `UMelodiaPersonaSubsystem`

- Claimed present in 10 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\CORE_QOL_AUDIT_2026-07-29.md, Docs\Handoffs\CORE_LOOP_STATUS_AND_AGENT_PROMPTS_2026-08-07.md, Docs\Handoffs\DEEPSEEK_B6_QUEST_CHAIN_2026-08-08.md, Docs\Handoffs\QWEN_DEEPSEEK_PERSONA_LITE_2026-07-31.md, Docs\JRPG_SAVE_RUNTIME_CHAIN_AUDIT_2026-07-28.md, Docs\JRPG_UI_QUILL_NEXT_IMPLEMENTATION_2026-07-28.md, Docs\LOWER_TIER_FOUNDATION_LOCK_2026-07-29.md, Docs\MELODIA_SYSTEMS_COMPOSITION_CONTRACT_2026-07-30.md, Docs\PERSONA_LITE_LOW_AGENCY_HANDOFF_2026-07-28.md, Docs\Reports\Overnight\GAMEPLAY_AUTHORITY_ATLAS_2026-08-24.md
- **Absent-claiming docs:** Docs\MCP_MELODIA_SYSTEM.md

### `UMelodiaMusicClockSubsystem`

- Claimed present in 26 doc(s) and absent/broken in 3 doc(s)
- **Present-claiming docs:** Docs\ECHO\campaign_01_rhythm_damage_delta.md, Docs\FOUNDATION_LOCKIN_PLAN_2026-07-30.md, Docs\GAMEPLAY_REVIEW_2026-07-30.md, Docs\Handoffs\CODEX_PETAL_CANDIDATE_HANDOFF_2026-08-01.md, Docs\Handoffs\DREAMPRINT_AUDIO_REACTIVITY_PREP_2026-08-18.md, Docs\Handoffs\HOUDINI_WORLDGEN_DEEP_INTAKE_2026-08-28.md, Docs\Handoffs\P0_SEA_ABOVE_CYMATICS_CLOSEOUT_2026-09-01.md, Docs\Handoffs\PARALLEL_LANES_2026-08-08.md, Docs\Handoffs\PPV_FINALIZE_PLAN_2026-08-26.md, Docs\Handoffs\QWEN_HARMONIX_QUARTZ_BATTLE_INTEGRATION_2026-08-03.md, Docs\Handoffs\RESONANT_WORLD_UI_HANDOFF_2026-08-22.md, Docs\Handoffs\SESSION_CLOSEOUT_2026-08-09.md, Docs\MELODIA_AUDIO_VISUAL_SYNESTHESIA_LAYER_2026-08-28.md, Docs\MELODIA_AUTHORITATIVE_RHYTHM_COMBAT_WIRING_2026-08-03.md, Docs\MULTI_AGENT_DELEGATION_PROMPTS_2026-08-03.md, Docs\ORCHESTRA_CONTRACT_2026-08-20.md, Docs\Plans\SHOREWAKE_TRAVERSAL_PLAN_AND_P0_CLOSEOUT_2026-08-29.md, Docs\Portfolio\GAMEPLAY_SYSTEMS_CASE_STUDY_SOURCE_2026-08-24.md, Docs\Portfolio\PITCH_OPENCODE.md, Docs\Production\LOOKDEV_HOUR_EXECUTION_2026-08-29.md, Docs\Production\PCG\SCALE_FIRST_MUSICAL_PCG_PLAN_2026-08-10.md, Docs\Research\DEEP_RESEARCH_REPORT_2026-08-31.md, Docs\Research\MELODIA_PSYCH_MUSIC_INDIE_REFERENCE_2026-07-31.md, Docs\Reviews\RHYTHM_WALLET_REVIEW_2026-08-03.md, Docs\WEBSITE_OVERHAUL_LEVEL_MAPPING_2026-07-31.md, Docs\WorldGen\HOUDINI_ENGINE_SMOKE_SPEC_2026-08-27.md
- **Absent-claiming docs:** Docs\Handoffs\FX_PPV_UI_INTEGRATION_HANDOFF_2026-08-01.md, Docs\Handoffs\MUSICAL_DREAM_BIOME_HANDOFF_2026-08-26.md, Docs\Handoffs\RESONANT_WORLD_GAMEPLAY_HANDOFF_2026-08-22.md

### `UMelodiaNarrativeSubsystem` validates`

- Claimed present in 1 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\ENVIRONMENT_SOURCE_OF_TRUTH_2026-08-11.md
- **Absent-claiming docs:** Docs\JRPG_UI_QUILL_NEXT_IMPLEMENTATION_2026-07-28.md

### `UMelodiaTravelSubsystem`

- Claimed present in 14 doc(s) and absent/broken in 2 doc(s)
- **Present-claiming docs:** Docs\ENVIRONMENT_SOURCE_OF_TRUTH_2026-08-11.md, Docs\Handoffs\CLAUDE_COORDINATION_NOTE_2026-07-31.md, Docs\Handoffs\CLAUDE_REBUILD_VALIDATION_HANDOFF_2026-08-01.md, Docs\Handoffs\CLINE_BLUEPRINT_WIRING_2026-07-31.md, Docs\Handoffs\CLINE_MONOLITH_COMMANDS_2026-07-31.md, Docs\Handoffs\DEEPSEEK_BLUEPRINT_WIRING_HANDOFF_2026-08-03.md, Docs\Handoffs\KIRO_CLAUDE_CLINE_EVENING_CORE_LOOP_2026-08-01.md, Docs\Handoffs\PIE_2026-08-11.md, Docs\Plans\LONG_TERM_GAMEPLAY_BP_T3D_PLAN_2026-08-14.md, Docs\Portfolio\PITCH_OPENCODE.md, Docs\Reviews\CORE_4_EDITABLE_BP_SYSTEMS_2026-08-09.md, Docs\Reviews\DOC_HEALTH_REPORT_2026-08-03.md, Docs\Reviews\TRAVERSAL_SAVE_REVIEW_2026-08-03.md, Docs\WEBSITE_OVERHAUL_LEVEL_MAPPING_2026-07-31.md
- **Absent-claiming docs:** Docs\Handoffs\BLACKBOX_AUDIT_COMPLETE_2026-08-01.md, Docs\Reviews\JRPG_BLUEPRINT_CHAIN_REVIEW_2026-08-03.md

### `UMelodiaInputContextSubsystem`

- Claimed present in 10 doc(s) and absent/broken in 2 doc(s)
- **Present-claiming docs:** Docs\ENVIRONMENT_SOURCE_OF_TRUTH_2026-08-11.md, Docs\Handoffs\CLINE_BLUEPRINT_WIRING_2026-07-31.md, Docs\Handoffs\DEEPSEEK_HANDOFF_2026-08-12.md, Docs\Handoffs\KIRO_GAMEPLAY_SYSTEMS_ACCOUNTING_2026-08-01.md, Docs\MELODIA_CUTE_UI_ELEMENTS_SPEC_2026-07-31.md, Docs\MELODIA_WARDROBE_PLUGIN_PLAN_2026-08-07.md, Docs\MELODIA_WIDGET_GAMEPLAY_INTEGRATION_2026-07-31.md, Docs\RIDER_UE58_INTEGRATION_ROADMAP_2026-08-28.md, Docs\Reviews\CORE_4_EDITABLE_BP_SYSTEMS_2026-08-09.md, Docs\Reviews\JRPG_TRAVERSAL_REVIEW_2026-08-03.md
- **Absent-claiming docs:** Docs\Reviews\JRPG_BLUEPRINT_CHAIN_REVIEW_2026-08-03.md, Docs\UI_CLOSEOUT_SESSION_2026-08-03.md

### `UMelodiaWardrobeSubsystem`

- Claimed present in 19 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Evidence\P0_EXPLORATION_WARDROBE_GLIDE_PORTAL_PROBE_2026-08-31.md, Docs\Handoffs\CODEX_TOKEN_WALLET_BP_2026-08-14.md, Docs\Handoffs\CURRENT_P0_STATUS_2026-08-25.md, Docs\Handoffs\EDITOR_UP_EXECUTION_CHECKLIST_2026-08-28.md, Docs\Handoffs\MASTER_P0_CLOSEOUT_AND_LOOSE_ENDS_2026-08-28.md, Docs\Handoffs\MELODIA_CONVERGENCE_CLOSEOUT_AND_P0_PLAN_2026-08-24.md, Docs\Handoffs\P0_CLOSEOUT_ACTION_PLAN_2026-08-28.md, Docs\Handoffs\PROCEDURAL_DUNGEON_REACTIVATION_2026-08-14.md, Docs\Handoffs\RESONANT_WORLD_GAMEPLAY_HANDOFF_2026-08-22.md, Docs\Handoffs\UI_WBP_LOOKDEV_FINALIZATION_PLAN_2026-08-28.md, Docs\MELODIA_WARDROBE_PLUGIN_PLAN_2026-08-07.md, Docs\ORCHESTRA_CONTRACT_2026-08-20.md, Docs\ORCHESTRA_CONVERGENCE_2026-08-20.md, Docs\Plans\LONG_TERM_GAMEPLAY_BP_T3D_PLAN_2026-08-14.md, Docs\Plans\P2_P3_SYSTEM_PREPARATION_AND_ROADMAP_2026-08-31.md, Docs\Portfolio\GAMEPLAY_SYSTEMS_CASE_STUDY_SOURCE_2026-08-24.md, Docs\Reports\Overnight\GAMEPLAY_AUTHORITY_ATLAS_2026-08-24.md, Docs\UI\MELUSINA_WARDROBE_LOOKBOOK_ROLLOUT_2026-08-14.md, Docs\WorldGen\WARDROBE_ORBITAL_GATE_SPEC_2026-08-27.md
- **Absent-claiming docs:** Docs\MELUSINA_ANIMATION_PIPELINE_REVIEW_2026-08-20.md

### `UMelodiaTraversalComponent`

- Claimed present in 27 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\FIRST_20_MINUTES_LIVE_EDITOR_CUTOVER_2026-07-29.md, Docs\Handoffs\BP_NATIVE_SURFACE_AUDIT_2026-08-14.md, Docs\Handoffs\CURRENT_P0_STATUS_2026-08-25.md, Docs\Handoffs\GPT_HANDOFF_2026-08-14_EVENING.md, Docs\Handoffs\JUMP_WINDUP_FIX_2026-08-05.md, Docs\Handoffs\KIRO_GAMEPLAY_SYSTEMS_ACCOUNTING_2026-08-01.md, Docs\Handoffs\MASTER_P0_CLOSEOUT_AND_LOOSE_ENDS_2026-08-28.md, Docs\Handoffs\MCP_Melodia_Integration_Architecture_Handoff_2026-08-18.md, Docs\Handoffs\OCEANOLOGY_WATER_COEXISTENCE_2026-08-15.md, Docs\Handoffs\REBUILD_STATUS_AND_NEXT_SLICE_2026-08-14.md, Docs\Handoffs\RESONANT_WORLD_ECHO_PIE_HANDOFF_2026-08-22.md, Docs\Handoffs\RESONANT_WORLD_GAMEPLAY_HANDOFF_2026-08-22.md, Docs\Handoffs\SIR_MELODIOUS_PERCH_FLIGHT_DESIGN_2026-08-28.md, Docs\Handoffs\TRAVERSAL_API_BUILD_EVIDENCE_2026-08-14.md, Docs\Handoffs\UNIFIED_PPV_OCEANOLOGY_LOOKDEV_PLAN_2026-08-28.md, Docs\Handoffs\WARDROBE_REBUILD_AND_WIRING_2026-08-15.md, Docs\LOWER_TIER_FOUNDATION_LOCK_2026-07-29.md, Docs\MELODIA_WARDROBE_ARCHITECTURE_2026-08-14.md, Docs\OCEANOLOGY_STYLIZATION_AND_TRAVERSAL_INTEGRATION_RESEARCH_2026-08-29.md, Docs\ORCHESTRA_CONTRACT_2026-08-20.md, Docs\Plans\LONG_TERM_GAMEPLAY_BP_T3D_PLAN_2026-08-14.md, Docs\Plans\MELODIA_INFINITY_NIKKI_PIPELINE_UPDATE_2026-08-14.md, Docs\Plans\MELODIA_PROGRESSION_GATING_DESIGN_2026-08-14.md, Docs\Portfolio\GAMEPLAY_SYSTEMS_CASE_STUDY_SOURCE_2026-08-24.md, Docs\Reports\Overnight\GAMEPLAY_AUTHORITY_ATLAS_2026-08-24.md, Docs\Reviews\CORE_4_EDITABLE_BP_SYSTEMS_2026-08-09.md, Docs\WATER_SYSTEM_EXPANSION_RESEARCH_2026-08-08.md
- **Absent-claiming docs:** Docs\Research\INFINITY_NIKKI_PIPELINES_AND_PROJECT_UPDATES_2026-08-14.md

### `UMelodiaPartySubsystem`

- Claimed present in 5 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\FULL_GAME_LOOSE_SCOPE_2026-07-31.md, Docs\LOWER_TIER_FOUNDATION_LOCK_2026-07-29.md, Docs\MELODIA_FIGMA_UI_WIRING_PLAN_2026-07-16.md, Docs\Reviews\CORE_4_EDITABLE_BP_SYSTEMS_2026-08-09.md, Docs\SCAFFOLDING_DEEP_REVIEW_LIVE_INTEGRATION_2026-07-24.md
- **Absent-claiming docs:** Docs\Handoffs\KIRO_MELODY_TOKEN_INTEGRATION_2026-08-01.md

### `FMelodiaWalletSnapshot`

- Claimed present in 5 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\HANDOFF_P0_LOOKDEV_PHASE_2026-08-24.md, Docs\Handoffs\CLAUDE_TO_KIRO_STATE_2026-08-01.md, Docs\Handoffs\CODEX_TOKEN_WALLET_BP_2026-08-14.md, Docs\Handoffs\KIRO_MELODY_TOKEN_INTEGRATION_2026-08-01.md, Docs\Handoffs\MELODIA_HUB_SESSION_HANDOFF_2026-08-26.md
- **Absent-claiming docs:** Docs\Reports\DUPLICATE_TREE_AUDIT_2026-08-14.md

### `UMelodiaOpeningFlowSubsystem`

- Claimed present in 5 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Handoffs\CLINE_TOKEN_BRANCH_VERIFICATION_2026-08-01.md, Docs\Handoffs\DEEPSEEK_SIR_RESCUE_2026-08-08.md, Docs\Handoffs\MELODIA_CONVERGENCE_CLOSEOUT_AND_P0_PLAN_2026-08-24.md, Docs\MELODIA_FIGMA_UI_WIRING_PLAN_2026-07-16.md, Docs\Reports\Overnight\GAMEPLAY_AUTHORITY_ATLAS_2026-08-24.md
- **Absent-claiming docs:** Docs\Handoffs\BLACKBOX_AUDIT_COMPLETE_2026-08-01.md

### `UMelodiaRhythmSkillDefinition`

- Claimed present in 8 doc(s) and absent/broken in 4 doc(s)
- **Present-claiming docs:** Docs\Handoffs\BP_NATIVE_SURFACE_AUDIT_2026-08-14.md, Docs\Handoffs\DEEPSEEK_BLUEPRINT_WIRING_HANDOFF_2026-08-03.md, Docs\Handoffs\IMPORT_EXECUTION_HANDOFF_2026-08-13.md, Docs\Handoffs\KIMI_UI_WIRING_NOTES_2026-08-03.md, Docs\Handoffs\QWEN_HARMONIX_QUARTZ_BATTLE_INTEGRATION_2026-08-03.md, Docs\Plans\LONG_TERM_GAMEPLAY_BP_T3D_PLAN_2026-08-14.md, Docs\Reviews\CORE_4_EDITABLE_BP_SYSTEMS_2026-08-09.md, Docs\Reviews\RHYTHM_WALLET_REVIEW_2026-08-03.md
- **Absent-claiming docs:** Docs\Handoffs\BP_MATERIALIZATION_CONTRACT_2026-08-14.md, Docs\Handoffs\CLINE_WIRING_EXECUTION_2026-08-06.md, Docs\Handoffs\REBUILD_STATUS_AND_NEXT_SLICE_2026-08-14.md, Docs\Plans\MELODIA_INFINITY_NIKKI_PIPELINE_UPDATE_2026-08-14.md

### `IMelodiaTravelProvider`

- Claimed present in 1 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Handoffs\DEEPSEEK_PARALLEL_LANE_2026-07-31_EVENING.md
- **Absent-claiming docs:** Docs\Handoffs\CLAUDE_COORDINATION_NOTE_2026-07-31.md

### `UMelodiaPacingSubsystem`

- Claimed present in 4 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Handoffs\CLAUDE_COORDINATION_NOTE_2026-07-31.md, Docs\Handoffs\DEEPSEEK_PARALLEL_LANE_2026-07-31_EVENING.md, Docs\Handoffs\TENSION_AUDIO_REACTIVITY_2026-08-15.md, Docs\Research\MELODIA_PSYCH_MUSIC_INDIE_REFERENCE_2026-07-31.md
- **Absent-claiming docs:** Docs\Handoffs\KIRO_MELODY_TOKEN_INTEGRATION_2026-08-01.md

### `UMelodiaExternalJRPGBridgeSubsystem`

- Claimed present in 11 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Handoffs\CLINE_WIRING_EXECUTION_2026-08-06.md, Docs\Handoffs\CLOSEOUT_SOURCE_VERDICTS_2026-08-11.md, Docs\Handoffs\CORE_LOOP_STATUS_AND_AGENT_PROMPTS_2026-08-07.md, Docs\Handoffs\MELODIA_CONVERGENCE_CLOSEOUT_AND_P0_PLAN_2026-08-24.md, Docs\Handoffs\UI_BRIDGE_SUBSYSTEM_AUTHORITY_2026-08-18.md, Docs\Handoffs\WBP_SYSTEMS_DEEP_DIVE_AND_P0_QUICK_WINS_2026-08-28.md, Docs\Handoffs\WIRING_FINALIZATION_STATUS_2026-08-07.md, Docs\LOWER_TIER_FOUNDATION_LOCK_2026-07-29.md, Docs\ORCHESTRA_CONTRACT_2026-08-20.md, Docs\Reviews\JRPG_TRAVERSAL_REVIEW_2026-08-03.md, Docs\Reviews\SESSION_REVIEW_2026-08-06.md
- **Absent-claiming docs:** Docs\Reviews\JRPG_BLUEPRINT_CHAIN_REVIEW_2026-08-03.md

### `UMelodiaTokenCatalog`

- Claimed present in 4 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Handoffs\CODEX_TOKEN_WALLET_BP_2026-08-14.md, Docs\Handoffs\CODEX_WARDROBE_CORE_CPP_INTEGRATION_REVIEW_2026-08-15.md, Docs\Handoffs\CONTINUATION_2026-08-14_NIGHT.md, Docs\Handoffs\SESSION_CLOSEOUT_2026-08-14_CLAUDE.md
- **Absent-claiming docs:** Docs\Handoffs\WARDROBE_REBUILD_AND_WIRING_2026-08-15.md

### `EMelodiaSpellElement`

- Claimed present in 3 doc(s) and absent/broken in 2 doc(s)
- **Present-claiming docs:** Docs\Handoffs\CODEX_TOKEN_WALLET_BP_2026-08-14.md, Docs\Handoffs\CONTINUATION_2026-08-14_NIGHT.md, Docs\Plans\MELODIA_PROGRESSION_GATING_DESIGN_2026-08-14.md
- **Absent-claiming docs:** Docs\Handoffs\GPT_HANDOFF_2026-08-14_EVENING.md, Docs\Reports\WARDROBE_CONTENT_CONTRACT_GAPS_2026-08-14.md

### `UMelodiaIntegrationConfig`

- Claimed present in 3 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Handoffs\CORE_LOOP_STATUS_AND_AGENT_PROMPTS_2026-08-07.md, Docs\Handoffs\INTEGRATION_POLISH_HANDOFFS_2026-08-06.md, Docs\Plans\LONG_TERM_GAMEPLAY_BP_T3D_PLAN_2026-08-14.md
- **Absent-claiming docs:** Docs\MELODIA_OVERALL_STATUS_2026-08-23.md

### `AMelodiaSmokeCharacter`

- Claimed present in 3 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Handoffs\GAMEMODE_029A_RETIREMENT_INVENTORY_2026-08-14.md, Docs\Handoffs\GPT_HANDOFF_2026-08-14_EVENING.md, Docs\SCAFFOLDING_DEEP_REVIEW_2026-07-24.md
- **Absent-claiming docs:** Docs\MELODIA_JRPG_CHARACTER_SKILL_SLICE_2026-07-26.md

### `EMelodiaCosmeticRarity`

- Claimed present in 3 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Handoffs\GPT_HANDOFF_2026-08-14_EVENING.md, Docs\MELODIA_WARDROBE_HANDOFF_2026-08-07.md, Docs\Reports\WARDROBE_CONTENT_CONTRACT_GAPS_2026-08-14.md
- **Absent-claiming docs:** Docs\Handoffs\WARDROBE_REBUILD_AND_WIRING_2026-08-15.md

### `UMelodiaCymaticsSubsystem`

- Claimed present in 6 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Handoffs\P0_SEA_ABOVE_CYMATICS_CLOSEOUT_2026-09-01.md, Docs\Plans\NEXT_SESSION_PLAN_2026-08-31.md, Docs\Plans\P2_AUDIO_REACTIVE_FABRIC_MOUNTAINS_2026-08-31.md, Docs\Plans\P2_P3_SYSTEM_PREPARATION_AND_ROADMAP_2026-08-31.md, Docs\Research\DEEP_RESEARCH_REPORT_2026-08-31.md, Docs\Research\EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md
- **Absent-claiming docs:** Docs\Handoffs\SESSION_HANDOFF_2026-09-01_P0_SHOREWAKE_REBIND.md

### `AMelodiaMovingPlatform`

- Claimed present in 1 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Handoffs\PCG_SESSION_WINS_2026-08-02.md
- **Absent-claiming docs:** Docs\Handoffs\PCG_TEAGARDEN_HERO_2026-08-02.md

### `UMelodiaRhythmCombatSubsystem::InvalidateS`

- Claimed present in 1 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Handoffs\QWEN_HARMONIX_QUARTZ_BATTLE_INTEGRATION_2026-08-03.md
- **Absent-claiming docs:** Docs\Reviews\RHYTHM_WALLET_REVIEW_2026-08-03.md

### `FMelodiaSongSkillRecipe`

- Claimed present in 1 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Handoffs\REBUILD_STATUS_AND_NEXT_SLICE_2026-08-14.md
- **Absent-claiming docs:** Docs\Plans\MELODIA_INFINITY_NIKKI_PIPELINE_UPDATE_2026-08-14.md

### `UMelodiaJRPGPartyBootstrapSubsystem`

- Claimed present in 2 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Handoffs\UI_BRIDGE_SUBSYSTEM_AUTHORITY_2026-08-18.md, Docs\LOWER_TIER_FOUNDATION_LOCK_2026-07-29.md
- **Absent-claiming docs:** Docs\Reviews\TRAVERSAL_SAVE_REVIEW_2026-08-03.md

### `UMelodiaDissonanceSubsystem`

- Claimed present in 1 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\MELODIA_FIGMA_UI_WIRING_PLAN_2026-07-16.md
- **Absent-claiming docs:** Docs\Reports\WBP_BINDING_MATRIX_2026-08-14.md

### `UMelodiaDressingSubsystem`

- Claimed present in 3 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Plans\NEXT_SESSION_PLAN_2026-08-31.md, Docs\Research\DASH_MAGPIE_NATIVE_INTEGRATION_2026-08-31.md, Docs\Research\DEEP_RESEARCH_REPORT_2026-08-31.md
- **Absent-claiming docs:** Docs\Research\EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md

## Stale Drive Paths

- `Docs\_Reference\MELODIA_ACFU_QUILLSCRIPT_COMPATIBILITY_MATRIX_2026-07-25.md:30` - Stale drive path: `G:\ueprojects\TurnBasedjRPGTemplate`
- `Docs\Architecture\MELUSINA_V2_RESkin_IMPORT_CONTRACT_AND_FAILURE_ANALYSIS_2026-08-14.md:7` - Stale drive path: `G:\EnvironmentPortfolio\BS_GodFile\Melodia_Portfolio_Stage_v22_ZenRebuild_WIP`
- `Docs\AUDIO_IMMERSION_PLAN_2026-08-09.md:57` - Stale drive path: `F:\Backups\Melodia\`
- `Docs\BLENDER_MELODIA_COCKPIT.md:10` - Stale drive path: `G:\EnvironmentPortfolio\BS_GodFile\Melodia_Portfolio_Stage_v22_ZenRebuild_WIP`
- `Docs\BLENDER_MELODIA_COCKPIT.md:15` - Stale drive path: `G:\EnvironmentPortfolio\BS_GodFile\Melodia_Portfolio_Stage_v22_ZenRebuild_WIP`
- `Docs\CREDITS.md:67` - Stale drive path: `F:\Library\Assets\Downloads_Zips`
- `Docs\CREDITS.md:68` - Stale drive path: `F:\Library\Assets\Downloads_Zips`
- `Docs\CREDITS.md:69` - Stale drive path: `F:\Library\Assets\Downloads_Zips`
- `Docs\CREDITS.md:72` - Stale drive path: `F:\Library\Assets\Downloads_Zips`
- `Docs\CREDITS.md:110` - Stale drive path: `F:\Library\Assets\Downloads_Zips`
- `Docs\CREDITS.md:110` - Stale drive path: `F:\Inbox\Downloads_Sweep_2026`
- `Docs\CREDITS.md:118` - Stale drive path: `F:\harddrivebackup\unreal`
- `Docs\CREDITS.md:119` - Stale drive path: `F:\Library\Assets\Downloads_Zips`
- `Docs\CREDITS.md:120` - Stale drive path: `F:\Library\Assets\Packs`
- `Docs\CREDITS.md:121` - Stale drive path: `F:\Inbox\Downloads_Sweep_2026`
- `Docs\CREDITS.md:122` - Stale drive path: `G:\Zundamons`
- `Docs\CREDITS.md:123` - Stale drive path: `F:\_Organized\POC_Archive\My`
- `Docs\ENVIRONMENT_SOURCE_OF_TRUTH_2026-08-11.md:130` - Stale drive path: `G:\EnvironmentPortfolio`
- `Docs\Handoffs\ATLANTIS_MATERIALS_AND_MASTER_PIPELINE_2026-08-17.md:41` - Stale drive path: `G:\UE_DDC`
- `Docs\Handoffs\BLENDER_MELODIA_STUDIO_HANDOFFS_2026-08-12.md:31` - Stale drive path: `G:\EnvironmentPortfolio\BS_GodFile\Melodia_Portfolio_Stage_v22_ZenRebuild_WIP`
- `Docs\Handoffs\BLENDER_VERSION_GRAPH_AND_V25_ROKOKO_PLAN_2026-08-28.md:414` - Stale drive path: `G:\MelodiaMelusina\MelusinaFinalRig\`
- `Docs\Handoffs\BLENDER_VERSION_GRAPH_AND_V25_ROKOKO_PLAN_2026-08-28.md:415` - Stale drive path: `G:\MelodiaMelusina\`
- `Docs\Handoffs\BLENDER_VERSION_GRAPH_AND_V25_ROKOKO_PLAN_2026-08-28.md:416` - Stale drive path: `G:\MelusinaRigFinalSeparate\`
- `Docs\Handoffs\BLENDER_VERSION_GRAPH_AND_V25_ROKOKO_PLAN_2026-08-28.md:417` - Stale drive path: `G:\MelusinasPuzzle\`
- `Docs\Handoffs\BLENDER_VERSION_GRAPH_AND_V25_ROKOKO_PLAN_2026-08-28.md:418` - Stale drive path: `G:\Blender`
- `Docs\Handoffs\BLENDER_VERSION_GRAPH_AND_V25_ROKOKO_PLAN_2026-08-28.md:419` - Stale drive path: `G:\BlenderAssets\`
- `Docs\Handoffs\BLENDER_VERSION_GRAPH_AND_V25_ROKOKO_PLAN_2026-08-28.md:420` - Stale drive path: `G:\Gaea\`
- `Docs\Handoffs\BLENDER_VERSION_GRAPH_AND_V25_ROKOKO_PLAN_2026-08-28.md:421` - Stale drive path: `G:\portfoliowebsite\`
- `Docs\Handoffs\BLENDER_VERSION_GRAPH_AND_V25_ROKOKO_PLAN_2026-08-28.md:422` - Stale drive path: `G:\Stylized`
- `Docs\Handoffs\BLENDER_VERSION_GRAPH_AND_V25_ROKOKO_PLAN_2026-08-28.md:423` - Stale drive path: `G:\stylizedcrossprop\`
- *... and 149 more*

## Stale Docs (>14 Days)

- `48H_CHANGE_REVIEW_2026-08-05.md` - Doc date `2026-08-05` is 27d old (threshold: 14d)
- `_AGENT_ECOSYSTEM.md` - Doc date `2026-08-07` is 25d old (threshold: 14d)
- `_AGENT_WORKING_AGREEMENT.md` - Doc date `2026-08-17` is 15d old (threshold: 14d)
- `_AUDIT_2026-08-05.md` - Doc date `2026-08-05` is 27d old (threshold: 14d)
- `_INTAKE_REPORT_2026-07-26.md` - Doc date `2026-07-26` is 37d old (threshold: 14d)
- `_PORTFOLIO_SHIP_CHECKLIST.md` - Doc date `2026-07-29` is 34d old (threshold: 14d)
- `_ROADBLOCKS_2026-07-31.md` - Doc date `2026-08-07` is 25d old (threshold: 14d)
- `_SESSION_HANDOFF_TEMPLATE.md` - Doc date `2026-08-07` is 25d old (threshold: 14d)
- `ART_DIRECTOR_REVIEW.md` - Doc date `2026-06-25` is 68d old (threshold: 14d)
- `asset_recommendations.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `CONTRIBUTING.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `CURRENT_STATE.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `CURRENT_SYSTEM_MAP.md` - Doc date `2026-06-25` is 68d old (threshold: 14d)
- `INTEGRATION_WORKFLOW.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `MATERIAL_SYSTEM_REVIEW.md` - Doc date `2026-06-25` is 68d old (threshold: 14d)
- `MELIDIA_LONGTERM_HEALTH_SAFETY_PLAN.md` - Doc date `2026-07-16` is 47d old (threshold: 14d)
- `MONETIZATION_ROADMAP.md` - Doc date `2026-07-16` is 47d old (threshold: 14d)
- `niagara_audit_report.md` - Doc date `2026-08-04` is 28d old (threshold: 14d)
- `PCG_REFINEMENT_REPORT.md` - Doc date `2026-06-25` is 68d old (threshold: 14d)
- `PORTFOLIO_PIPELINE_AUDIT.md` - Doc date `2026-06-25` is 68d old (threshold: 14d)
- `QUICKSTART.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `TODO.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `VFX_material_fixlist.md` - Doc date `2026-08-16` is 16d old (threshold: 14d)
- `Docs\2026-07-29_PROJECT_HANDOFF.md` - Doc date `2026-07-29` is 34d old (threshold: 14d)
- `Docs\_Reference\BP_INTEGRATION_REVIEW_2026-07-18.md` - Doc date `2026-07-18` is 45d old (threshold: 14d)
- `Docs\_Reference\MELODIA_ACFU_QUILLSCRIPT_COMPATIBILITY_MATRIX_2026-07-25.md` - Doc date `2026-07-25` is 38d old (threshold: 14d)
- `Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md` - Doc date `2026-07-14` is 49d old (threshold: 14d)
- `Docs\_Superseded\_AGENT_GOALS_2026-08-02.md` - Doc date `2026-08-02` is 30d old (threshold: 14d)
- `Docs\_Superseded\CHANGELOG_24H.md` - Doc date `2026-07-09` is 54d old (threshold: 14d)
- `Docs\_Superseded\MELODIA_ROGUELIKE_GAMELOOP_COMPLETION_PLAN_2026-07-14.md` - Doc date `2026-07-26` is 37d old (threshold: 14d)
- `Docs\_Superseded\NEXT_ACTIONS.md` - Doc date `2026-07-20` is 43d old (threshold: 14d)
- `Docs\_Superseded\NEXT_HIGHEST_LEVERAGE_TASK.md` - Doc date `2026-07-14` is 49d old (threshold: 14d)
- `Docs\_Superseded\README.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\AFTERNOON_WORK_SESSION_PLAN_2026-07-12.md` - Doc date `2026-07-12` is 51d old (threshold: 14d)
- `Docs\AGENT_BRIDGE_IMPLEMENTATION.md` - Doc date `2026-07-20` is 43d old (threshold: 14d)
- `Docs\AGENT_LANES.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\AGENT_MCP_SURFACES.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\AGENT_TOOLS.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\AgentMemory\Decisions.md` - Doc date `2026-07-02` is 61d old (threshold: 14d)
- `Docs\AI_AGENTS_MODELS_WORKFLOW_GUIDE_2026-07-26.md` - Doc date `2026-07-26` is 37d old (threshold: 14d)
- `Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md` - Doc date `2026-07-26` is 37d old (threshold: 14d)
- `Docs\ART_SPINE_CLEANUP_2026-08-13.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\ASSET_PIPELINE_HARDENING_AND_AGENT_PROMPT_2026-07-14.md` - Doc date `2026-07-26` is 37d old (threshold: 14d)
- `Docs\Atlantis_Ingest_Completion.md` - Doc date `2026-08-17` is 15d old (threshold: 14d)
- `Docs\AUDIO_IMMERSION_PLAN_2026-08-09.md` - Doc date `2026-08-09` is 23d old (threshold: 14d)
- `Docs\AWS_AGENT_TOOLKIT_SETUP_2026-07-26.md` - Doc date `2026-07-26` is 37d old (threshold: 14d)
- `Docs\BLENDER_MELODIA_COCKPIT.md` - Doc date `2026-08-17` is 15d old (threshold: 14d)
- `Docs\BLUEPRINT_WIRING_CHECKLIST_2026-07-30.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\BLUEPRINT_WIRING_CONTRACT_2026-08-07.md` - Doc date `2026-08-08` is 24d old (threshold: 14d)
- `Docs\BLUEPRINT_WIRING_SKILL_2026-08-07.md` - Doc date `2026-08-07` is 25d old (threshold: 14d)
- `Docs\Career\STUDIO_COMPULSION_GAMES_DRAFT.md` - Doc date `2026-07-26` is 37d old (threshold: 14d)
- `Docs\Career\STUDIO_DIGITAL_EXTREMES_DRAFT.md` - Doc date `2026-07-26` is 37d old (threshold: 14d)
- `Docs\Career\STUDIO_INFOLD_GAMES_DRAFT.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\Career\STUDIO_PROMETHEAN_AI_DRAFT.md` - Doc date `2026-07-26` is 37d old (threshold: 14d)
- `Docs\CASCADEUR_MELUSINA_PIPELINE_2026-08-07.md` - Doc date `2026-08-07` is 25d old (threshold: 14d)
- `Docs\COLLABORATION_WORKFLOW.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\COMMIT_PLAN_UNTRACKED_2026-07.md` - Doc date `2026-07-17` is 46d old (threshold: 14d)
- `Docs\CONSISTENCY_REPORT.md` - Doc date `2025-06-25` is 433d old (threshold: 14d)
- `Docs\COORDINATOR_DEEP_REVIEW_2026-07-17.md` - Doc date `2026-07-17` is 46d old (threshold: 14d)
- `Docs\CORE_QOL_AUDIT_2026-07-29.md` - Doc date `2026-07-29` is 34d old (threshold: 14d)
- `Docs\CREDITS.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\CURRENT_VERTICAL_SLICE_SCOPE_2026-08-01.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\DESIGN_SYSTEM_GAPS.md` - Doc date `2026-06-25` is 68d old (threshold: 14d)
- `Docs\DUPE_ROOT_QUARANTINE_2026-07.md` - Doc date `2026-07-25` is 38d old (threshold: 14d)
- `Docs\ECHO\campaign_01_rhythm_damage_delta.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\ECHO\campaign_02_save_round_trip.md` - Doc date `2026-08-07` is 25d old (threshold: 14d)
- `Docs\ECHO\campaign_03_package_launch.md` - Doc date `2026-08-10` is 22d old (threshold: 14d)
- `Docs\ECHO\README.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\ECHO\reconciliation_duplicate_trees.md` - Doc date `2026-07-26` is 37d old (threshold: 14d)
- `Docs\ECHO_PIPELINE_2026-08-09.md` - Doc date `2026-08-09` is 23d old (threshold: 14d)
- `Docs\ENVIRONMENT_MATERIAL_LAYOUT.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\ENVIRONMENT_PASS_PLAN_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\ENVIRONMENT_RUNBOOK_2026-08-11.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\ENVIRONMENT_SOURCE_OF_TRUTH_2026-08-11.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\EXPORT_STANDARDIZATION_NOTES.md` - Doc date `2025-06-25` is 433d old (threshold: 14d)
- `Docs\FIGMA_IMPLEMENTATION_GUIDE.md` - Doc date `2026-06-25` is 68d old (threshold: 14d)
- `Docs\FIGMA_MAPPING_GUIDE.md` - Doc date `2026-06-25` is 68d old (threshold: 14d)
- `Docs\FIRST_20_MINUTES_LIVE_EDITOR_CUTOVER_2026-07-29.md` - Doc date `2026-07-29` is 34d old (threshold: 14d)
- `Docs\FIRST_DREAM_20_MINUTE_PLAYTEST_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\FIRST_DREAM_VERTICAL_SLICE_CHECKLIST_2026-07-28.md` - Doc date `2026-07-29` is 34d old (threshold: 14d)
- `Docs\FOUNDATION_CLOSEOUT_DECISIONS_2026-07-30.md` - Doc date `2026-07-30` is 33d old (threshold: 14d)
- `Docs\FOUNDATION_LOCKIN_PLAN_2026-07-30.md` - Doc date `2026-07-30` is 33d old (threshold: 14d)
- `Docs\FULL_GAME_LOOSE_SCOPE_2026-07-31.md` - Doc date `2026-07-31` is 32d old (threshold: 14d)
- `Docs\GAME_FOUNDATION_PLAN_2026-08-11.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\GAMEPLAY_REVIEW_2026-07-30.md` - Doc date `2026-07-31` is 32d old (threshold: 14d)
- `Docs\GIT_BATCH_DISCIPLINE.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\GRANDMASTER_MASTER_PLAN_V2.md` - Doc date `2026-07-15` is 48d old (threshold: 14d)
- `Docs\Gumroad\FAB_SDF_PACK_MANIFEST.md` - Doc date `2026-07-18` is 45d old (threshold: 14d)
- `Docs\Gumroad\SKU1_SCREENSHOT_CHECKLIST.md` - Doc date `2026-07-18` is 45d old (threshold: 14d)
- `Docs\HANDOFF_CASCADEUR_MCP_BRIDGE_2026-08-08.md` - Doc date `2026-08-08` is 24d old (threshold: 14d)
- `Docs\HANDOFF_SURREAL_TO_MELODIA_SYSTEM_2026-07-12.md` - Doc date `2026-07-12` is 51d old (threshold: 14d)
- `Docs\Handoffs\A1_BATTLE_PATH_PIE_CHECKLIST_2026-08-12.md` - Doc date `2026-08-12` is 20d old (threshold: 14d)
- `Docs\Handoffs\AGENT_COORDINATION_QUANTUM_2026-08-06.md` - Doc date `2026-08-06` is 26d old (threshold: 14d)
- `Docs\Handoffs\ATLANTIS_MATERIALS_AND_MASTER_PIPELINE_2026-08-17.md` - Doc date `2026-08-17` is 15d old (threshold: 14d)
- `Docs\Handoffs\BEDROCK_LEDGER_LANES_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\BLACKBOX_AUDIT_COMPLETE_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\BLACKBOX_EXPORT_GAP_AUDIT_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\BLACKBOX_HANDOFF_2026-07-31.md` - Doc date `2026-07-31` is 32d old (threshold: 14d)
- `Docs\Handoffs\BLACKBOX_HANDOFF_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\BLENDER_MELODIA_STUDIO_HANDOFFS_2026-08-12.md` - Doc date `2026-08-12` is 20d old (threshold: 14d)
- `Docs\Handoffs\BP_AUTHORITY_READINESS_AUDIT_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\BP_MATERIALIZATION_CONTRACT_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\BP_NATIVE_SURFACE_AUDIT_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\CI_REALITY_AUDIT_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\CLAUDE_COORDINATION_NOTE_2026-07-31.md` - Doc date `2026-07-31` is 32d old (threshold: 14d)
- `Docs\Handoffs\CLAUDE_HANDOFF_2026-07-31.md` - Doc date `2026-07-31` is 32d old (threshold: 14d)
- `Docs\Handoffs\CLAUDE_KIRO_TANDEM_PREP_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\CLAUDE_REBUILD_VALIDATION_HANDOFF_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\CLAUDE_REVIEW_OLLAMA_VALIDATION_2026-07-31.md` - Doc date `2026-07-31` is 32d old (threshold: 14d)
- `Docs\Handoffs\CLAUDE_TO_KIRO_STATE_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\CLINE_BATTLE_ANIM_WIDGET_EXPORT_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\CLINE_BLUEPRINT_WIRING_2026-07-31.md` - Doc date `2026-07-31` is 32d old (threshold: 14d)
- `Docs\Handoffs\CLINE_MONOLITH_COMMANDS_2026-07-31.md` - Doc date `2026-08-05` is 27d old (threshold: 14d)
- `Docs\Handoffs\CLINE_TOKEN_BRANCH_VERIFICATION_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\CLINE_WIRING_EXECUTION_2026-08-06.md` - Doc date `2026-08-06` is 26d old (threshold: 14d)
- `Docs\Handoffs\CLOSEOUT_SOURCE_VERDICTS_2026-08-11.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\Handoffs\CLOUD_AGENT_GIT_HEALTH_2026-08-12.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\Handoffs\CLOUD_RESEARCH_FOLD_IN_2026-08-11.md` - Doc date `2026-08-12` is 20d old (threshold: 14d)
- `Docs\Handoffs\CODEX_FX_NIAGARA_PPV_HANDOFF_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\CODEX_GAMEPLAY_RESEARCH_HANDOFF_2026-08-15.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\Handoffs\CODEX_LIVING_SAKURA_CANDIDATE_STATUS_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\CODEX_LOOKDEV_CANDIDATE_HANDOFF_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\CODEX_NIAGARA_EXECUTION_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\CODEX_NIAGARA_LIBRARY_AUDIT_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\CODEX_NIAGARA_RENDERER_AUDIT_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\CODEX_NIAGARA_UPGRADE_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\CODEX_PETAL_CANDIDATE_HANDOFF_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\CODEX_SDF_NIAGARA_FINALIZATION_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\CODEX_TOKEN_WALLET_BP_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\CODEX_WARDROBE_CORE_CPP_INTEGRATION_REVIEW_2026-08-15.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\Handoffs\CONTINUATION_2026-08-14_NIGHT.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\COOP_SKILL_RESONANCE_SPEC_2026-08-08.md` - Doc date `2026-08-08` is 24d old (threshold: 14d)
- `Docs\Handoffs\CORE_GAMEPLAY_CLOSEOUT_PLAN_2026-08-11.md` - Doc date `2026-08-12` is 20d old (threshold: 14d)
- `Docs\Handoffs\CORE_LOOP_STATUS_AND_AGENT_PROMPTS_2026-08-07.md` - Doc date `2026-08-07` is 25d old (threshold: 14d)
- `Docs\Handoffs\CORE_P0_DREAM_SLICE_HANDOFF_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\CORE_P0_LIVE_INTEGRATION_STATUS_2026-08-15.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\Handoffs\CORE_SYSTEMS_HANDOFF_2026-08-09.md` - Doc date `2026-08-09` is 23d old (threshold: 14d)
- `Docs\Handoffs\CORE_SYSTEMS_HANDOFF_2026-08-10.md` - Doc date `2026-08-10` is 22d old (threshold: 14d)
- `Docs\Handoffs\DEEPSEEK_B6_QUEST_CHAIN_2026-08-08.md` - Doc date `2026-08-08` is 24d old (threshold: 14d)
- `Docs\Handoffs\DEEPSEEK_BLUEPRINT_WIRING_HANDOFF_2026-08-03.md` - Doc date `2026-08-07` is 25d old (threshold: 14d)
- `Docs\Handoffs\DEEPSEEK_HANDOFF_2026-08-12.md` - Doc date `2026-08-12` is 20d old (threshold: 14d)
- `Docs\Handoffs\DEEPSEEK_SIR_RESCUE_2026-08-08.md` - Doc date `2026-08-08` is 24d old (threshold: 14d)
- `Docs\Handoffs\ED_CLOSEOUT_RESTART_HANDOFF_2026-08-13.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\Handoffs\EDITOR_CRASH_DIAGNOSIS_2026-08-08.md` - Doc date `2026-08-08` is 24d old (threshold: 14d)
- `Docs\Handoffs\ENVIRONMENT_BUILD_VALIDATION_2026-08-11.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\Handoffs\FX_PPV_UI_INTEGRATION_HANDOFF_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\G_ROOT_AUDIT_2026-08-06.md` - Doc date `2026-08-06` is 26d old (threshold: 14d)
- `Docs\Handoffs\GAMEMODE_029A_RETIREMENT_INVENTORY_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\GEMINI_PROJECT_HEALTH_2026-08-06.md` - Doc date `2026-08-06` is 26d old (threshold: 14d)
- `Docs\Handoffs\GEMINI_UI_POLISH_2026-07-31.md` - Doc date `2026-07-31` is 32d old (threshold: 14d)
- `Docs\Handoffs\GPT_HANDOFF_2026-08-14_EVENING.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\HANDOFF_KIRI_2026_08_03_UI_GRANDMASTER.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\Handoffs\HANDOFF_PCG_HERO_AUDIO_2026-08-09.md` - Doc date `2026-08-09` is 23d old (threshold: 14d)
- `Docs\Handoffs\HERO_GRAPH_REVIEW_QUEUE_2026-08-07.md` - Doc date `2026-08-07` is 25d old (threshold: 14d)
- `Docs\Handoffs\IMPORT_EXECUTION_HANDOFF_2026-08-13.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\Handoffs\INTEGRATION_LAYER_EXPANSION_PLAN_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\INTEGRATION_POLISH_HANDOFFS_2026-08-06.md` - Doc date `2026-08-12` is 20d old (threshold: 14d)
- `Docs\Handoffs\JCODE_OLLAMA_INTEGRATION_AUDIT_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\KAWAII_PHYSICS_PLACEMENT_AUDIT_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\KAWAII_PHYSICS_PLACEMENT_EVIDENCE_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\KIMI_UI_WIRING_NOTES_2026-08-03.md` - Doc date `2026-08-07` is 25d old (threshold: 14d)
- `Docs\Handoffs\KIRO_CLAUDE_CLINE_EVENING_CORE_LOOP_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\KIRO_GAMEPLAY_SYSTEMS_ACCOUNTING_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\KIRO_MELODY_TOKEN_INTEGRATION_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\MATERIAL_AAA_TAKEOVER_LANES_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\MATERIAL_CORE_STANDARD_SWEEP_2026-08-15.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\Handoffs\MATERIAL_PIPELINE_AAA_EXECUTION_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\MATERIAL_SURFACE_PROTECTION_AUDIT_2026-08-15.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\Handoffs\MATERIAL_SYSTEM_ORGANIZATION_HANDOFF_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\MATERIAL_TEXTURE_ROUTING_HANDOFF_2026-08-13.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\MELODIA_GOAL_STATUS_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\MELODIA_GRIEF_HOOK_PRESENTATION_STATE_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\MELODIA_VOICE_QUILLSCRIPT_HANDOFF_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\MELUSINA_IDLE_RESTORE_MOCAP_2026-08-13.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\Handoffs\MELUSINA_LOOKDEV_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\Handoffs\MESH_MATERIAL_COMPLETION_PINKBLUE_KENNEY_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\MESH_SCALE_REPAIR_2026-08-02.md` - Doc date `2026-08-02` is 30d old (threshold: 14d)
- `Docs\Handoffs\MODEL_FLEET_2026-08-13.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\MUSE_HANDOFF_2026-08-12.md` - Doc date `2026-08-12` is 20d old (threshold: 14d)
- `Docs\Handoffs\NEXT_AGENTS_PARALLEL_2026-08-13.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\NIAGARA_STUB_REPLACEMENT_MAP_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\NIKKI_GENSHIN_BLENDER_2026-08-13.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\Handoffs\OCEANOLOGY_WATER_COEXISTENCE_2026-08-15.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\Handoffs\OVERALL_STATUS_2026-08-17.md` - Doc date `2026-08-17` is 15d old (threshold: 14d)
- `Docs\Handoffs\PARALLEL_LANES_2026-08-08.md` - Doc date `2026-08-12` is 20d old (threshold: 14d)
- `Docs\Handoffs\PARALLEL_LANES_2026-08-12.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\Handoffs\PARALLEL_SESSIONS_2026-08-12.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\Handoffs\PCG_LIBRARY_REVIEW_2026-08-02.md` - Doc date `2026-08-02` is 30d old (threshold: 14d)
- `Docs\Handoffs\PCG_RENDER_POLISH_AND_UNIVERSAL_2026-08-02.md` - Doc date `2026-08-02` is 30d old (threshold: 14d)
- `Docs\Handoffs\PCG_SESSION_WINS_2026-08-02.md` - Doc date `2026-08-02` is 30d old (threshold: 14d)
- `Docs\Handoffs\PCG_SPLINE_CARVE_FIXED_2026-08-02.md` - Doc date `2026-08-02` is 30d old (threshold: 14d)
- `Docs\Handoffs\PCG_TEAGARDEN_HERO_2026-08-02.md` - Doc date `2026-08-02` is 30d old (threshold: 14d)
- `Docs\Handoffs\PCG_WALKABILITY_PASS_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\PCG_WORKING_STATE_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\PHONE_ARTIST_BRIDGE_HANDOFF_2026-08-11.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\Handoffs\PIE_2026-08-11.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\Handoffs\PIE_RUNTIME_NOTES_2026-08-12.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\Handoffs\PPV_DEEP_STUDY_V4_2026-08-02.md` - Doc date `2026-08-02` is 30d old (threshold: 14d)
- `Docs\Handoffs\PPV_STORYBOOK_OUTLINE_INTEGRATION_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\PRE_REBUILD_HEALTH_PASS_2026-08-02.md` - Doc date `2026-08-02` is 30d old (threshold: 14d)
- `Docs\Handoffs\PREMIUM_OUTLINE_STACK_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\PROCEDURAL_DUNGEON_REACTIVATION_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\PROJECT_HANDOFF_2026-08-09.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\Handoffs\QUANTUM_GAMEPLAY_EXPERIMENT_2026-08-06.md` - Doc date `2026-08-06` is 26d old (threshold: 14d)
- `Docs\Handoffs\QUANTUM_GAMEPLAY_EXPERIMENT_PROTO_2026-08-06.md` - Doc date `2026-08-09` is 23d old (threshold: 14d)
- `Docs\Handoffs\QUILLSCRIPT_LOCKED_2026-08-12.md` - Doc date `2026-08-12` is 20d old (threshold: 14d)
- `Docs\Handoffs\QWEN_BATTLE_NARRATIVE_BINDING_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\Handoffs\QWEN_DEEPSEEK_PERSONA_LITE_2026-07-31.md` - Doc date `2026-07-31` is 32d old (threshold: 14d)
- `Docs\Handoffs\QWEN_HARMONIX_QUARTZ_BATTLE_INTEGRATION_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\Handoffs\QWEN_RHYTHM_SKILLS_SCOPE_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\Handoffs\REBUILD_STATUS_AND_NEXT_SLICE_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\REMAINING_TASKS_EXECUTE_2026-08-13.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\Handoffs\RHYTHM_GAME_LOCKED_2026-08-12.md` - Doc date `2026-08-12` is 20d old (threshold: 14d)
- `Docs\Handoffs\RHYTHM_SKILL_SYSTEM_EXPANSION_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\Handoffs\RIDER_HANDOFF_2026-07-31.md` - Doc date `2026-07-31` is 32d old (threshold: 14d)
- `Docs\Handoffs\SESSION_CLOSEOUT_2026-08-08.md` - Doc date `2026-08-08` is 24d old (threshold: 14d)
- `Docs\Handoffs\SESSION_CLOSEOUT_2026-08-09.md` - Doc date `2026-08-09` is 23d old (threshold: 14d)
- `Docs\Handoffs\SESSION_CLOSEOUT_2026-08-10.md` - Doc date `2026-08-10` is 22d old (threshold: 14d)
- `Docs\Handoffs\SESSION_CLOSEOUT_2026-08-14_CLAUDE.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\SESSION_CLOSEOUT_GAMEPLAY_LOOP_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\Handoffs\SESSION_CLOSEOUT_LOOKDEV_NIAGARA_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\Handoffs\SESSION_CLOSEOUT_UI_MIGRATION_2026-08-04.md` - Doc date `2026-08-04` is 28d old (threshold: 14d)
- `Docs\Handoffs\SESSION_HANDOFF_2026-08-07_PHYSICS_LOOKDEV.md` - Doc date `2026-08-07` is 25d old (threshold: 14d)
- `Docs\Handoffs\SESSION_HANDOFF_2026-08-11_CATHEDRAL_RIG.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\Handoffs\SESSION_REVIEW_NEXT_PROMPTS_2026-08-13.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\Handoffs\SOURCE_CONTROL_STATUS_2026-08-13.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\Handoffs\STOCK_UI_REPLACEMENT_AUDIT_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\Handoffs\TENSION_AUDIO_REACTIVITY_2026-08-15.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\Handoffs\TONIGHT_CONTINUATION_HANDOFF_2026-08-12.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\Handoffs\TONIGHT_FIRST_DREAM_OPENCODE_2026-08-11.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\Handoffs\TONIGHT_PORTFOLIO_STUDIO_PREP_2026-08-12.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\Handoffs\TRAVERSAL_API_BUILD_EVIDENCE_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\TWINMOTION_REALITYSCAN_SIDE_LANE_2026-08-13.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\Handoffs\UI_FIGMA_SKIN_TASK_2026-08-06.md` - Doc date `2026-08-06` is 26d old (threshold: 14d)
- `Docs\Handoffs\VFX_NIAGARA_FINALIZATION_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\VISUAL_POLISH_PLAN_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\Handoffs\VRM4U_NPC_PLACEHOLDERS_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Handoffs\WARDROBE_REBUILD_AND_WIRING_2026-08-15.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\Handoffs\WEBSITE_SENDOFF_2026-08-13.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\Handoffs\WIRING_FINALIZATION_STATUS_2026-08-07.md` - Doc date `2026-08-07` is 25d old (threshold: 14d)
- `Docs\Handoffs\WORKFLOW_UNIFY_2026-08-12.md` - Doc date `2026-08-12` is 20d old (threshold: 14d)
- `Docs\Handoffs\ZERO_OVERRIDE_MI_TRIAGE_2026-08-15.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\HARMONIX_MIDI_RHYTHM_CONTRACT_2026-07-29.md` - Doc date `2026-07-29` is 34d old (threshold: 14d)
- `Docs\IMPRESSIONIST_SYSTEM.md` - Doc date `2026-06-19` is 74d old (threshold: 14d)
- `Docs\JRPG_MECHANICS_CONTRACT_SHEET_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\JRPG_QUILLSCRIPT_FOUNDATION_2026-07-25.md` - Doc date `2026-07-26` is 37d old (threshold: 14d)
- `Docs\JRPG_SAVE_RUNTIME_CHAIN_AUDIT_2026-07-28.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\JRPG_UI_QUILL_NEXT_IMPLEMENTATION_2026-07-28.md` - Doc date `2026-07-28` is 35d old (threshold: 14d)
- `Docs\LEVEL_DESIGNER_ONBOARDING.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\LFS_COLD_ARCHIVE.md` - Doc date `2026-08-02` is 30d old (threshold: 14d)
- `Docs\LIVEOPS_GIT_SOP_2026-08-11.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\LOWER_TIER_FOUNDATION_LOCK_2026-07-29.md` - Doc date `2026-07-29` is 34d old (threshold: 14d)
- `Docs\MAIN_MENU_CONTINUE_LOAD_WIRING_PLAN_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\MATERIAL_INTEGRATION.md` - Doc date `2026-07-01` is 62d old (threshold: 14d)
- `Docs\MATERIAL_LIBRARY_AUDIT.md` - Doc date `2026-06-19` is 74d old (threshold: 14d)
- `Docs\MATERIAL_LIBRARY_NAPO_LOOP_PLAN.md` - Doc date `2026-06-20` is 73d old (threshold: 14d)
- `Docs\MATERIAL_MIGRATION.md` - Doc date `2026-06-19` is 74d old (threshold: 14d)
- `Docs\MATERIAL_NODE_TREE_REVIEW.md` - Doc date `2026-06-24` is 69d old (threshold: 14d)
- `Docs\MATERIAL_STUDIO_NIKKI_DOCTRINE.md` - Doc date `2026-07-14` is 49d old (threshold: 14d)
- `Docs\material_system_completion_report.md` - Doc date `2026-06-25` is 68d old (threshold: 14d)
- `Docs\MATERIAL_WORK_PLAN.md` - Doc date `2026-06-19` is 74d old (threshold: 14d)
- `Docs\MELODIA_AUTHORITATIVE_RHYTHM_COMBAT_WIRING_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\MELODIA_BATTLE_UI_INTEGRATION_2026-07-11.md` - Doc date `2026-07-11` is 52d old (threshold: 14d)
- `Docs\MELODIA_CORE_LOOP.md` - Doc date `2026-07-26` is 37d old (threshold: 14d)
- `Docs\MELODIA_CUTE_UI_ELEMENTS_SPEC_2026-07-31.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\MELODIA_FIGMA_UI_WIRING_PLAN_2026-07-16.md` - Doc date `2026-07-28` is 35d old (threshold: 14d)
- `Docs\MELODIA_FIRST_20_MINUTES_VERTICAL_SLICE.md` - Doc date `2026-07-26` is 37d old (threshold: 14d)
- `Docs\MELODIA_GMM_FAMILY_ARCHITECTURE_PLAN.md` - Doc date `2026-08-12` is 20d old (threshold: 14d)
- `Docs\MELODIA_IDENTITY_AND_LOOP_2026-07-30.md` - Doc date `2026-07-31` is 32d old (threshold: 14d)
- `Docs\MELODIA_INTEGRATION_EVIDENCE_REGISTER_2026-07-26.md` - Doc date `2026-07-26` is 37d old (threshold: 14d)
- `Docs\MELODIA_LUXURY_UI_FILIGREE_NIKKI_MOTION_PLAN_2026-07-12.md` - Doc date `2026-07-17` is 46d old (threshold: 14d)
- `Docs\MELODIA_NEXT_PLAYABLE_SLICE_SWIRL_2026-07-14.md` - Doc date `2026-07-14` is 49d old (threshold: 14d)
- `Docs\MELODIA_NPC_VRM4U_READINESS_2026-07-11.md` - Doc date `2026-07-11` is 52d old (threshold: 14d)
- `Docs\MELODIA_SOLO_GAMEPLAY_CONSTITUTION_2026-07-27.md` - Doc date `2026-07-27` is 36d old (threshold: 14d)
- `Docs\MELODIA_STAGE_SAVE_POLICY.md` - Doc date `2026-07-16` is 47d old (threshold: 14d)
- `Docs\MELODIA_STUDIO_GATE3_UI_UNLOCK.md` - Doc date `2026-07-16` is 47d old (threshold: 14d)
- `Docs\MELODIA_STUDIO_SHIP_CHECKLIST.md` - Doc date `2026-08-17` is 15d old (threshold: 14d)
- `Docs\MELODIA_SYSTEMS_COMPOSITION_CONTRACT_2026-07-30.md` - Doc date `2026-07-31` is 32d old (threshold: 14d)
- `Docs\MELODIA_TODAY_PLAYTEST_HANDOFF_2026-07-11.md` - Doc date `2026-07-11` is 52d old (threshold: 14d)
- `Docs\MELODIA_TRANSITION_SYSTEM_CONTRACT.md` - Doc date `2026-07-26` is 37d old (threshold: 14d)
- `Docs\MELODIA_UE58_INTEGRATION_ARCHITECTURE_2026-07-26.md` - Doc date `2026-07-28` is 35d old (threshold: 14d)
- `Docs\MELODIA_WARDROBE_HANDOFF_2026-08-07.md` - Doc date `2026-08-07` is 25d old (threshold: 14d)
- `Docs\MELODIA_WARDROBE_PLUGIN_PLAN_2026-08-07.md` - Doc date `2026-08-07` is 25d old (threshold: 14d)
- `Docs\MELODIA_WIDGET_GAMEPLAY_INTEGRATION_2026-07-31.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\MELODY_TOKEN_GAMEPLAY_CONTRACT.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\MELUSINA_BLENDER_AAA_PIPELINE_2026-07-30.md` - Doc date `2026-07-30` is 33d old (threshold: 14d)
- `Docs\MELUSINA_BLENDER_WARDROBE_SSOT.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\MELUSINA_HAIR_REEXPORT_CHECKLIST_2026-07-30.md` - Doc date `2026-07-30` is 33d old (threshold: 14d)
- `Docs\MELUSINA_IRIS_POSTMORTEM_2026-07-13.md` - Doc date `2026-07-13` is 50d old (threshold: 14d)
- `Docs\MELUSINA_MARKETING_INTRO_PREP_2026-08-02.md` - Doc date `2026-08-02` is 30d old (threshold: 14d)
- `Docs\MELUSINA_RENDER_SESSION_2026-07-13.md` - Doc date `2026-07-13` is 50d old (threshold: 14d)
- `Docs\MELUSINA_SESSION_LOG_2026-07-13.md` - Doc date `2026-07-14` is 49d old (threshold: 14d)
- `Docs\missing_connections_report.md` - Doc date `2026-06-25` is 68d old (threshold: 14d)
- `Docs\MOBILE_SCAN_ZBRUSH_ROKOKO_PIPELINE_2026-08-11.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\MONETIZATION_GEOMETRY_FIX_EXPORT_2026-07-12.md` - Doc date `2026-07-16` is 47d old (threshold: 14d)
- `Docs\MULTI_AGENT_DELEGATION_PROMPTS_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\MULTI_AGENT_ORCHESTRATION_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\NIAGARA_ECOSYSTEM_2026-08-09.md` - Doc date `2026-08-09` is 23d old (threshold: 14d)
- `Docs\NIAGARA_INFINITY_NIKKI_UPGRADE_PLAN_2026-08-01.md` - Doc date `2026-08-01` is 31d old (threshold: 14d)
- `Docs\NIKKI_VERTICAL_SLICE_PLAN.md` - Doc date `2026-07-15` is 48d old (threshold: 14d)
- `Docs\PCG_CATALOG.md` - Doc date `2026-08-05` is 27d old (threshold: 14d)
- `Docs\PCG_PORTFOLIO_HANDOFF_DEEPSEEK_2026-07-26.md` - Doc date `2026-07-26` is 37d old (threshold: 14d)
- `Docs\PERSONA_LITE_LOW_AGENCY_HANDOFF_2026-07-28.md` - Doc date `2026-07-28` is 35d old (threshold: 14d)
- `Docs\PhoneOps\ENV_PACK_RESEARCH_POINTER.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\PhoneOps\HIGHEST_LEVERAGE_NOW.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\PhoneOps\JCODE_SWARM_PIPELINE.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\PhoneOps\RECENT_STUDY.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\PhoneOps\SCRATCHPAD.md` - Doc date `2026-08-12` is 20d old (threshold: 14d)
- `Docs\PIE_VERIFICATION_CHECKLIST_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\Plans\DREAMPRINT_DIRECTOR_WIRING_2026-08-15.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\Plans\DREAMPRINT_DIRECTOR_WIRING_STEPS_2026-08-15.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\Plans\LONG_TERM_GAMEPLAY_BP_T3D_PLAN_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Plans\MELODIA_INFINITY_NIKKI_PIPELINE_UPDATE_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Plans\MELODIA_INTEGRATION_MAP_OVERHAUL_2026-08-16.md` - Doc date `2026-08-16` is 16d old (threshold: 14d)
- `Docs\Plans\MELODIA_PROGRESSION_GATING_DESIGN_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Plans\MELUSINA_ANIMATION_BLENDSPACE_INTEGRATION_2026-08-15.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\Plans\MELUSINA_RIG_FINALIZATION_PLAN_2026-08-15.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\Plans\MELUSINA_V2_REBUILD_AND_INFINITY_NIKKI_WARDROBE_PLAN_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\PORTFOLIO_IMPROVEMENT_LOG.md` - Doc date `2026-06-25` is 68d old (threshold: 14d)
- `Docs\PORTFOLIO_MAPPING_RULES.md` - Doc date `2026-06-25` is 68d old (threshold: 14d)
- `Docs\PRESENTATION_INTERFACE_INTEGRATION_PROPOSAL_2026-07-18.md` - Doc date `2026-07-18` is 45d old (threshold: 14d)
- `Docs\Production\AGENT_INFRASTRUCTURE_2026-08-11.md` - Doc date `2026-08-12` is 20d old (threshold: 14d)
- `Docs\Production\DREAM_SYSTEM.md` - Doc date `2026-07-04` is 59d old (threshold: 14d)
- `Docs\Production\MATERIAL_MASTER_RECONCILIATION.md` - Doc date `2026-08-16` is 16d old (threshold: 14d)
- `Docs\Production\Materials\UNIVERSAL_WATER_FAMILY.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Production\MELUSINA_AAA_POLISH_RECIPE_2026-08-13.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\Production\MODEL_LANES_2026-08-12.md` - Doc date `2026-08-12` is 20d old (threshold: 14d)
- `Docs\Production\MUSE_CODE_LANE_2026-08-11.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\Production\PCG\PCG_PIANO_README.md` - Doc date `2026-08-08` is 24d old (threshold: 14d)
- `Docs\Production\PCG\SCALE_FIRST_MUSICAL_PCG_PLAN_2026-08-10.md` - Doc date `2026-08-10` is 22d old (threshold: 14d)
- `Docs\Production\PCG\SCALE_FIRST_MUSICAL_PCG_PLAN_REVIEW_2026-08-10.md` - Doc date `2026-08-10` is 22d old (threshold: 14d)
- `Docs\Production\T3D_MONOLITH_REFERENCE.md` - Doc date `2026-08-12` is 20d old (threshold: 14d)
- `Docs\Production\UNIVERSAL_MASTER_NODE_REVIEW.md` - Doc date `2026-07-04` is 59d old (threshold: 14d)
- `Docs\Production\UNIVERSAL_MASTER_OVERHAUL_PLAN.md` - Doc date `2026-07-04` is 59d old (threshold: 14d)
- `Docs\PROJECT_HEALTH_24H.md` - Doc date `2026-07-16` is 47d old (threshold: 14d)
- `Docs\PROJECT_SCOPE_AND_WORKFLOW_PLAN_2026-08-06.md` - Doc date `2026-08-06` is 26d old (threshold: 14d)
- `Docs\PROJECT_STATUS_2026-07-25.md` - Doc date `2026-07-27` is 36d old (threshold: 14d)
- `Docs\QUEUE.md` - Doc date `2026-08-07` is 25d old (threshold: 14d)
- `Docs\Reconstruction\MATERIAL_SYSTEM_REBUILD_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\RELEASE_VALIDATION_REPORT.md` - Doc date `2026-07-17` is 46d old (threshold: 14d)
- `Docs\Reports\BACKUP_SYNC_AUDIT_2026-08-12.md` - Doc date `2026-08-12` is 20d old (threshold: 14d)
- `Docs\Reports\CLAUDE_SESSION_REPORT_2026-08-15.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\Reports\DEEP_REVIEW_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Reports\DUPLICATE_TREE_AUDIT_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Reports\DUPLICATE_TREE_INVENTORY_2026-08-11.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\Reports\GATE_TEST_COVERAGE_GAP_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Reports\GIT_LEFTOVERS_TRIAGE_2026-08-11.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\Reports\GROK_RESEARCH_FOLDIN_2026-08-11.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\Reports\jcode_muse_opencode_setup_acceptance.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\Reports\jcode_swarm_acceptance.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\Reports\jcode_swarm_recipe_a.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\Reports\jcode_swarm_recipe_b_mpa.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\Reports\jcode_swarm_recipe_b_ppa.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\Reports\JRPG_BP_REPLACEMENT_PRIORITY_2026-08-11.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\Reports\LFS_HEALTH_2026-08-13.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\Reports\LOST_TOOL_SOURCES_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Reports\MELUSINA_FINGER_DEFECT_POSTMORTEM_2026-08-15.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\Reports\RECENT_CHANGES_AND_JCODE_STUDY_2026-08-11.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\Reports\RECORD_GATE_ENVELOPE_BLAST_RADIUS_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Reports\REPEAT_CONSUME_VERDICT_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Reports\WARDROBE_CONTENT_CONTRACT_GAPS_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Reports\WBP_BINDING_MATRIX_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Reports\WORKDAY_REVIEW_2026-08-12.md` - Doc date `2026-08-12` is 20d old (threshold: 14d)
- `Docs\Research\AAA_ANIME_UE_CHARACTER_PIPELINE_2026-08-15.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\Research\AI_WORKFLOW_OPTIMIZATION_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\Research\BLENDER_ADDON_INTAKE_2026-08-15.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\Research\ENVIRONMENT_PACK_RESEARCH_2026-08-13.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\Research\FromProfile_2026-08-13\MELODIA_OVERHAUL_COMPLETION_REPORT.md` - Doc date `2026-06-05` is 88d old (threshold: 14d)
- `Docs\Research\FromProfile_2026-08-13\MelodiaMelusina_Overhaul_Implementation.md` - Doc date `2026-06-05` is 88d old (threshold: 14d)
- `Docs\Research\INFINITY_NIKKI_PIPELINES_AND_PROJECT_UPDATES_2026-08-14.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\Research\Infinity_Nikki_VFX_Cohesion_Report.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\Research\MELODIA_BARD_GRIEF_HOOK_2026-07-31.md` - Doc date `2026-07-31` is 32d old (threshold: 14d)
- `Docs\Research\MELODIA_PSYCH_MUSIC_INDIE_REFERENCE_2026-07-31.md` - Doc date `2026-07-31` is 32d old (threshold: 14d)
- `Docs\Research\MELODIA_UE_JRPG_WORKFLOW_RESEARCH_2026-08-15.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\Research\MELUSINA_BILINGUAL_VOICE_INTAKE_2026-08-11.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\Research\MELUSINA_SINGS_DIFFSVC_PLAN_2026-08-11.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\Research\MODEL_ACCESS_GUIDE_2026-08-15.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\Research\STYLIZED_ENV_PACK_SHORTLIST_2026-08-11.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\Research\UE58_MaterialNotes.md` - Doc date `2026-06-20` is 73d old (threshold: 14d)
- `Docs\Research\UE58_TOON_MATERIAL_INTAKE_INFINITY_NIKKI_2026-08-08.md` - Doc date `2026-08-08` is 24d old (threshold: 14d)
- `Docs\Research\UE58_TOON_SHADER_EXTERNAL_PRACTICES_2026-08-14.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\Research\UE58_WORKFLOW_RESEARCH_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\Research\UE_RETARGET_PIPELINES_LONG_TERM_2026-08-15.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\Reviews\BP_WIRING_GAP_SCAN_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\Reviews\CORE_4_EDITABLE_BP_SYSTEMS_2026-08-09.md` - Doc date `2026-08-09` is 23d old (threshold: 14d)
- `Docs\Reviews\CORE_GAMEPLAY_LOOSE_ENDS_2026-08-09.md` - Doc date `2026-08-09` is 23d old (threshold: 14d)
- `Docs\Reviews\DOC_HEALTH_REPORT_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\Reviews\GRIEF_HOOK_NARRATIVE_SWEEP_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\Reviews\JRPG_BLUEPRINT_CHAIN_REVIEW_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\Reviews\JRPG_TRAVERSAL_REVIEW_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\Reviews\MCP_SURFACE_SCAN_2026-08-03.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\Reviews\MUSIC_RHYTHM_REVIEW_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\Reviews\PERSONA_LITE_LOOP_DEEP_REVIEW_2026-08-08.md` - Doc date `2026-08-08` is 24d old (threshold: 14d)
- `Docs\Reviews\QUILLSCRIPT_GRIEF_HOOK_REVIEW_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\Reviews\RHYTHM_WALLET_REVIEW_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\Reviews\SESSION_REVIEW_2026-08-06.md` - Doc date `2026-08-06` is 26d old (threshold: 14d)
- `Docs\Reviews\TRAVERSAL_SAVE_REVIEW_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\Reviews\UI_LOOSE_ENDS_SWEEP_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\RHYTHM_COMBAT_SYSTEM_HANDOFF_2026-07-30.md` - Doc date `2026-07-30` is 33d old (threshold: 14d)
- `Docs\ROKOKO_MELUSINA_MOCAP.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\ROUGELIKE_GAMEPLAY_COLLECTION_REVIEW.md` - Doc date `2026-07-14` is 49d old (threshold: 14d)
- `Docs\SCAFFOLDING_DEEP_REVIEW_LIVE_INTEGRATION_2026-07-24.md` - Doc date `2026-07-24` is 39d old (threshold: 14d)
- `Docs\SCHEMA_ALIGNMENT_MAP.md` - Doc date `2025-06-25` is 433d old (threshold: 14d)
- `Docs\SCULPT_ASSET_INTAKE_2026-08-11.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\SDF_UTILITY_RETRO_GRAPHICS_CHEATS_PLAN_2026-08-09.md` - Doc date `2026-08-09` is 23d old (threshold: 14d)
- `Docs\SESSION_FLUFFY_AUDVIS_SPLASH_2026-07-13.md` - Doc date `2026-07-13` is 50d old (threshold: 14d)
- `Docs\SETUP_COLLAB.md` - Doc date `2026-08-11` is 21d old (threshold: 14d)
- `Docs\SIR_MELODIOUS_IMPORT_FORENSICS_2026-07-13.md` - Doc date `2026-07-13` is 50d old (threshold: 14d)
- `Docs\STAGE22_FINALIZATION_REPORT.md` - Doc date `2026-06-27` is 66d old (threshold: 14d)
- `Docs\standardization_fixes.md` - Doc date `2026-06-25` is 68d old (threshold: 14d)
- `Docs\SUBSTANCE_LACE_BLING_MATERIAL_IMPORT_PLAN.md` - Doc date `2026-07-13` is 50d old (threshold: 14d)
- `Docs\SYSTEM_ORGANIZATION_PLAN.md` - Doc date `2026-06-25` is 68d old (threshold: 14d)
- `Docs\T3D_Baseline\README.md` - Doc date `2026-08-07` is 25d old (threshold: 14d)
- `Docs\T3D_Patterns\patterns\README.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\T3D_Patterns\payloads\README.md` - Doc date `2026-08-09` is 23d old (threshold: 14d)
- `Docs\T3D_Patterns\wiring\README.md` - Doc date `2026-08-08` is 24d old (threshold: 14d)
- `Docs\TD_GRANDMASTER_MELODIA_PLAN.md` - Doc date `2026-07-15` is 48d old (threshold: 14d)
- `Docs\TD_PAGE_COPY_2026-07-18.md` - Doc date `2026-07-18` is 45d old (threshold: 14d)
- `Docs\TD_PAGE_DESIGN_SPEC_2026-07-18.md` - Doc date `2026-07-18` is 45d old (threshold: 14d)
- `Docs\TEXTURE_DUPLICATE_AUDIT_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\TOMORROW_2026-07-18_ARTIST_DAY_PLAN.md` - Doc date `2026-07-18` is 45d old (threshold: 14d)
- `Docs\TOON_MIGRATION_RUNBOOK.md` - Doc date `2026-06-19` is 74d old (threshold: 14d)
- `Docs\TOUCHDESIGNER_MCP_INTEGRATION_PLAN.md` - Doc date `2026-07-15` is 48d old (threshold: 14d)
- `Docs\UI_CLOSEOUT_SESSION_2026-08-03.md` - Doc date `2026-08-03` is 29d old (threshold: 14d)
- `Docs\UI_WIDGET_INHERITANCE_PLAN_2026-08-04.md` - Doc date `2026-08-04` is 28d old (threshold: 14d)
- `Docs\UNIVERSAL_MUSICAL_INFLUENCE_SCAFFOLD_2026-07-18.md` - Doc date `2026-07-18` is 45d old (threshold: 14d)
- `Docs\VERTICAL_SLICE_20MIN_REVIEW_2026-07-17.md` - Doc date `2026-07-17` is 46d old (threshold: 14d)
- `Docs\VFX_ASSET_MANIFEST.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\WATER_AUDIO_NIAGARA_V10_2026-08-09.md` - Doc date `2026-08-09` is 23d old (threshold: 14d)
- `Docs\WATER_SYSTEM_EXPANSION_RESEARCH_2026-08-08.md` - Doc date `2026-08-15` is 17d old (threshold: 14d)
- `Docs\WATER_SYSTEM_TEST_MATRIX_2026-08-09.md` - Doc date `2026-08-09` is 23d old (threshold: 14d)
- `Docs\WATER_V10_FINALIZATION_STATUS_2026-08-09.md` - Doc date `2026-08-14` is 18d old (threshold: 14d)
- `Docs\WEBSITE_OVERHAUL_LEVEL_MAPPING_2026-07-31.md` - Doc date `2026-07-31` is 32d old (threshold: 14d)
- `Docs\WEBSITE_OVERHAUL_PLAN_2026-07-31.md` - Doc date `2026-07-31` is 32d old (threshold: 14d)
- `Docs\WEBSITE_RENDER_CHECKLIST_2026-07-17.md` - Doc date `2026-07-17` is 46d old (threshold: 14d)
- `Docs\WebsiteRenderArchive\README.md` - Doc date `2026-07-31` is 32d old (threshold: 14d)
- `Docs\Widgets\BP_WidgetComponent_Base_Design.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\Widgets\Extract_BattleRhythm_Components.md` - Doc date `2026-08-13` is 19d old (threshold: 14d)
- `Docs\WORK_LOG_2026-07-16.md` - Doc date `2026-07-16` is 47d old (threshold: 14d)

## Docs Modified Without Date Bump

- `48H_CHANGE_REVIEW_2026-08-05.md` - mtime (2026-08-20) newer than newest date `2026-08-05` - doc modified without date bump
- `_AGENT_ECOSYSTEM.md` - mtime (2026-08-30) newer than newest date `2026-08-07` - doc modified without date bump
- `_AGENT_WORKING_AGREEMENT.md` - mtime (2026-08-20) newer than newest date `2026-08-17` - doc modified without date bump
- `_AUDIT_2026-08-05.md` - mtime (2026-08-20) newer than newest date `2026-08-05` - doc modified without date bump
- `_DECISION_LOG.md` - mtime (2026-08-23) newer than newest date `2026-08-18` - doc modified without date bump
- `_INTAKE_REPORT_2026-07-26.md` - mtime (2026-08-20) newer than newest date `2026-07-26` - doc modified without date bump
- `_PORTFOLIO_SHIP_CHECKLIST.md` - mtime (2026-08-20) newer than newest date `2026-07-29` - doc modified without date bump
- `_ROADBLOCKS_2026-07-31.md` - mtime (2026-08-20) newer than newest date `2026-08-07` - doc modified without date bump
- `_SESSION_HANDOFF_TEMPLATE.md` - mtime (2026-08-20) newer than newest date `2026-08-07` - doc modified without date bump
- `_VERTICAL_SLICE_SCOPE.md` - mtime (2026-08-30) newer than newest date `2026-08-29` - doc modified without date bump
- `ART_DIRECTOR_REVIEW.md` - mtime (2026-08-15) newer than newest date `2026-06-25` - doc modified without date bump
- `asset_recommendations.md` - mtime (2026-08-20) newer than newest date `2026-08-13` - doc modified without date bump
- `CLAUDE.md` - mtime (2026-08-30) newer than newest date `2026-08-29` - doc modified without date bump
- `CONTRIBUTING.md` - mtime (2026-08-27) newer than newest date `2026-08-13` - doc modified without date bump
- `CURRENT_STATE.md` - mtime (2026-08-20) newer than newest date `2026-08-11` - doc modified without date bump
- `CURRENT_SYSTEM_MAP.md` - mtime (2026-08-20) newer than newest date `2026-06-25` - doc modified without date bump
- `DOC_INDEX.md` - mtime (2026-08-26) newer than newest date `2026-08-25` - doc modified without date bump
- `INTEGRATION_WORKFLOW.md` - mtime (2026-08-20) newer than newest date `2026-08-13` - doc modified without date bump
- `MATERIAL_SYSTEM_REVIEW.md` - mtime (2026-08-15) newer than newest date `2026-06-25` - doc modified without date bump
- `MELIDIA_LONGTERM_HEALTH_SAFETY_PLAN.md` - mtime (2026-08-20) newer than newest date `2026-07-16` - doc modified without date bump
- *... and 529 more*

## Unresolved TODO/FIXME/HACK Markers

- `_DECISION_LOG.md` - 2 unresolved: hack, workaround
- `_ROADBLOCKS_2026-07-31.md` - 1 unresolved: workaround
- `Docs\_Superseded\CHANGELOG_24H.md` - 1 unresolved: Workaround
- `Docs\_Superseded\README.md` - 1 unresolved: TODO
- `Docs\Career\OPENCODE_TECHNICAL_OBSERVATIONS.md` - 3 unresolved: Workaround, workaround
- `Docs\Career\STUDIO_NVIDIA_DRAFT.md` - 1 unresolved: Hack
- `Docs\Handoffs\AGENT_COORDINATION_QUANTUM_2026-08-06.md` - 1 unresolved: todo
- `Docs\Handoffs\EDITOR_CRASH_DIAGNOSIS_2026-08-08.md` - 1 unresolved: workaround
- `Docs\Handoffs\KIRO_MELODY_TOKEN_INTEGRATION_2026-08-01.md` - 1 unresolved: hack
- `Docs\Handoffs\MELODIA_HUB_SESSION_HANDOFF_2026-08-26.md` - 1 unresolved: workaround
- `Docs\Handoffs\NEMOTRON_OPENCODE_UE_RESEARCH_2026-08-19.md` - 1 unresolved: Workaround
- `Docs\Handoffs\NEMOTRON_PHASE0_2_RESULTS_2026-08-20.md` - 1 unresolved: todo
- `Docs\Handoffs\NIAGARA_HOUDINI_FX_REVIEW_2026-08-30.md` - 2 unresolved: hack
- `Docs\Handoffs\PHONE_ARTIST_BRIDGE_HANDOFF_2026-08-11.md` - 1 unresolved: todo
- `Docs\Handoffs\SESSION_HANDOFF_ORG_FX_QOL_2026-08-31.md` - 1 unresolved: workaround
- `Docs\Handoffs\SESSION_REVIEW_ALL_FINDINGS_2026-08-28.md` - 1 unresolved: Workaround
- `Docs\MELODIA_STUDIO_PIE_ROOM_WINDOW_REVIEW_2026-08-23.md` - 1 unresolved: hack
- `Docs\NIKKI_VERTICAL_SLICE_PLAN.md` - 3 unresolved: TODO
- `Docs\NVIDIA_SHOWCASE_READINESS_2026-08-20.md` - 1 unresolved: workaround
- `Docs\PhoneOps\BACKLOG.md` - 1 unresolved: TODO
- `Docs\Plans\MELODIA_INFINITY_NIKKI_PIPELINE_UPDATE_2026-08-14.md` - 1 unresolved: hack
- `Docs\Plans\MELUSINA_ANIMATION_BLENDSPACE_INTEGRATION_2026-08-15.md` - 1 unresolved: workaround
- `Docs\Portfolio\PITCH_OPENCODE.md` - 1 unresolved: workaround
- `Docs\PORTFOLIO_MAPPING_RULES.md` - 2 unresolved: XXX
- `Docs\Production\AGENT_INFRASTRUCTURE_2026-08-11.md` - 1 unresolved: xxx
- `Docs\Production\FLOWERSPRING_SUBSTANCE_PIPELINE_2026-09-01.md` - 4 unresolved: TODO, hack
- `Docs\Research\AAA_ANIME_UE_CHARACTER_PIPELINE_2026-08-15.md` - 2 unresolved: workaround
- `Docs\Research\AGENT_TOOLCHAIN_DISCOVERY_INDEX_2026-08-30.md` - 1 unresolved: TODO
- `Docs\Research\AI_WORKFLOW_OPTIMIZATION_2026-08-03.md` - 1 unresolved: XXX
- `Docs\Research\CLAIREON_ARCHITECTURE_AND_COMPARISON_2026-08-19.md` - 2 unresolved: workaround
- `Docs\Research\ENVIRONMENT_PACK_RESEARCH_2026-08-13.md` - 1 unresolved: todo
- `Docs\Research\JAPANESE_ASSET_REPO_GRAND_LIST_2026-08-28.md` - 1 unresolved: TODO
- `Docs\Research\MELODIA_PSYCH_MUSIC_INDIE_REFERENCE_2026-07-31.md` - 1 unresolved: hack
- `Docs\Research\UE58_TOON_MATERIAL_INTAKE_INFINITY_NIKKI_2026-08-08.md` - 1 unresolved: hack
- `Docs\Research\UE58_TOON_SHADER_EXTERNAL_PRACTICES_2026-08-14.md` - 1 unresolved: hack
- `Docs\Reviews\DOC_HEALTH_REPORT_2026-08-03.md` - 18 unresolved: FIXME, HACK, TODO, Workaround, XXX, hack, workaround
- `Docs\Reviews\DOC_HEALTH_REPORT_2026-09-01.md` - 52 unresolved: FIXME, HACK, Hack, TODO, Workaround, XXX, hack, todo, workaround, xxx
- `Docs\SCAFFOLDING_DEEP_REVIEW_2026-07-24.md` - 1 unresolved: hack
- `Docs\TD_GRANDMASTER_MELODIA_PLAN.md` - 1 unresolved: TODO
- `Docs\WorldGen\WARDROBE_ORBITAL_GATE_SPEC_2026-08-27.md` - 1 unresolved: workaround

## File Inventory

Scanned 911 markdown files.

