# Doc Health Report — 2026-08-03

**Mode:** Read-only

## Summary

| Metric | Value |
|---|---:|
| .md files scanned | 324 |
| Technical claims extracted | 947 |
| Source headers indexed | 76 |
| C++ classes indexed | 37 |
| C++ functions indexed | 170 |
| Source mismatches (MISSING/STALE) | 337 |
| Monolith mismatches | 0 |
| Cross-doc contradictions | 28 |
| Stale drive paths | 181 |
| Stale docs (>14d without update) | 80 |

## Source Cross-Reference Findings

Claims from docs that reference C++ names not found in scanned source trees.
Scanned: `Source/` + MelodiaCore, QuillScript, Monolith, UEBlueprintMCP plugin dirs.

### ❌ MISSING — `cpp_file` (101 occurrences)

- `_ROADBLOCKS_2026-07-31.md:79` — `MelodiaMinimalHUD.cpp`
  - File `MelodiaMinimalHUD.cpp` not found under scanned Source/ or Plugins/ trees
  - _- `FSlateFontInfo` deprecations in `MelodiaMinimalHUD.cpp` become errors in a future engine version _
- `_ROADBLOCKS_2026-07-31.md:128` — `MelodiaRulesGenerated.h`
  - File `MelodiaRulesGenerated.h` not found under scanned Source/ or Plugins/ trees
  - _- **Generated files have been hand-edited.** `MelodiaRulesGenerated.h` carried seven `Opening*`_
- `CURRENT_STATE.md:35` — `MonolithEditorActions.cpp`
  - File `MonolithEditorActions.cpp` not found under scanned Source/ or Plugins/ trees
  - _The `r.PSOPrecaching` capture fix (committed in `Plugins/Monolith/Source/MonolithEditor/Private/Mono_
- `ROADMAP.md:22` — `BPVariables.cpp`
  - File `BPVariables.cpp` not found under scanned Source/ or Plugins/ trees
  - _*   [x] Fix C2665 compilation errors in `UnrealMCP` plugin (`BPVariables.cpp` / `BPConnector.cpp`) c_
- `ROADMAP.md:22` — `BPConnector.cpp`
  - File `BPConnector.cpp` not found under scanned Source/ or Plugins/ trees
  - _*   [x] Fix C2665 compilation errors in `UnrealMCP` plugin (`BPVariables.cpp` / `BPConnector.cpp`) c_
- `SYSTEM_MAP.md:81` — `BPConnector.cpp`
  - File `BPConnector.cpp` not found under scanned Source/ or Plugins/ trees
  - _*   Commands: Programmatic graph manipulation and variable editing (`BPConnector.cpp`, `BPVariables._
- `SYSTEM_MAP.md:81` — `BPVariables.cpp`
  - File `BPVariables.cpp` not found under scanned Source/ or Plugins/ trees
  - _*   Commands: Programmatic graph manipulation and variable editing (`BPConnector.cpp`, `BPVariables._
- `Docs\_Reference\BP_INTEGRATION_REVIEW_2026-07-18.md:15` — `MelodiaBattleSession.cpp`
  - File `MelodiaBattleSession.cpp` not found under scanned Source/ or Plugins/ trees
  - _`MelodiaBattleSession.cpp` calls into two interfaces at real gameplay moments:_
- `Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md:15` — `MelodiaCombatStateComponent.cpp`
  - File `MelodiaCombatStateComponent.cpp` not found under scanned Source/ or Plugins/ trees
  - _- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCombatStateComponent.cpp`_
- `Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md:17` — `MelodiaRulesGenerated.h`
  - File `MelodiaRulesGenerated.h` not found under scanned Source/ or Plugins/ trees
  - _- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRulesGenerated.h`_
- `Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md:50` — `MelodiaBattleSession.cpp`
  - File `MelodiaBattleSession.cpp` not found under scanned Source/ or Plugins/ trees
  - _- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleSession.cpp`_
- `Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md:53` — `MelodiaCoreRulesLibrary.cpp`
  - File `MelodiaCoreRulesLibrary.cpp` not found under scanned Source/ or Plugins/ trees
  - _- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCoreRulesLibrary.cpp`_
- `Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md:115` — `MelodiaRoguelikeRunSubsystem.cpp`
  - File `MelodiaRoguelikeRunSubsystem.cpp` not found under scanned Source/ or Plugins/ trees
  - _- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRoguelikeRunSubsystem.cpp`_
- `Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md:132` — `MelodiaDungeonRunCoordinator.cpp`
  - File `MelodiaDungeonRunCoordinator.cpp` not found under scanned Source/ or Plugins/ trees
  - _- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaDungeonRunCoordinator.cpp`_
- `Docs\ASSET_PIPELINE_HARDENING_AND_AGENT_PROMPT_2026-07-14.md:39` — `MelodiaRulesGenerated.h`
  - File `MelodiaRulesGenerated.h` not found under scanned Source/ or Plugins/ trees
  - _- `MelodiaRulesGenerated.h` or `rules_generated.py` edited directly._
- `Docs\COORDINATOR_DEEP_REVIEW_2026-07-17.md:64` — `MelodiaBattleArena.cpp`
  - File `MelodiaBattleArena.cpp` not found under scanned Source/ or Plugins/ trees
  - _8. Hitstop 1-line fix (`MelodiaBattleArena.cpp:143`)._
- `Docs\FIRST_DREAM_VERTICAL_SLICE_CHECKLIST_2026-07-28.md:183` — `UnrealNames.cpp`
  - File `UnrealNames.cpp` not found under scanned Source/ or Plugins/ trees
  - _- Win64 Development BuildCookRun built both Editor and game targets, then cook crashed with `LogUnre_
- `Docs\FOUNDATION_CLOSEOUT_DECISIONS_2026-07-30.md:18` — `MelodiaMinimalHUD.cpp`
  - File `MelodiaMinimalHUD.cpp` not found under scanned Source/ or Plugins/ trees
  - _Only warnings are pre-existing `FSlateFontInfo` deprecations in `MelodiaMinimalHUD.cpp`, unrelated_
- `Docs\FOUNDATION_LOCKIN_PLAN_2026-07-30.md:150` — `MusicClockComponent.h`
  - File `MusicClockComponent.h` not found under scanned Source/ or Plugins/ trees
  - _(`Engine/Plugins/Runtime/Harmonix/Source/HarmonixMetasound/Public/HarmonixMetasound/Components/Music_
- `Docs\FOUNDATION_LOCKIN_PLAN_2026-07-30.md:383` — `MelodiaAudioComponent.h`
  - File `MelodiaAudioComponent.h` not found under scanned Source/ or Plugins/ trees
  - _Plugins/MelodiaCore/Source/MelodiaCore/MelodiaAudioComponent.h/.cpp      (+GetBattleClockBPM)_
- *... and 81 more*

### ❌ MISSING — `system_ref` (236 occurrences)

- `_AGENT_WORKING_AGREEMENT.md:58` — `UMelodiaHairComponent`
  - Class `UMelodiaHairComponent` not indexed in any scanned Source/ or Plugins/ header
  - _Each of these appeared in `UMelodiaHairComponent` and cost roughly three days:_
- `_SESSION_HANDOFF.md:34` — `UMelodiaRhythmCombatSubsystem`
  - Class `UMelodiaRhythmCombatSubsystem` not indexed in any scanned Source/ or Plugins/ header
  - _- Wire UMelodiaRhythmCombatSubsystem::ConsumePendingRequest into BP_BattleUI OnSkillSelectedHandler _
- `_SESSION_HANDOFF.md:53` — `UMelodiaTravelSubsystem`
  - Class `UMelodiaTravelSubsystem` not indexed in any scanned Source/ or Plugins/ header
  - _- **Travel authority deadlock:** UMelodiaTravelSubsystem in game module, MelodiaCore plugin has 7 Op_
- `_SESSION_HANDOFF.md:61` — `UMelodiaPacingProfile`
  - Class `UMelodiaPacingProfile` not indexed in any scanned Source/ or Plugins/ header
  - _- Pacing profiles per register (UMelodiaPacingProfile DataAsset)_
- `_SESSION_HANDOFF.md:76` — `UMelodiaBattleAdapterSubsystem`
  - Class `UMelodiaBattleAdapterSubsystem` not indexed in any scanned Source/ or Plugins/ header
  - _- `Content/Python/tag_kaleido_encounter.py` — Monolith-driven **audit** of the KaleidoNave encounter_
- `_VERTICAL_SLICE_SCOPE.md:76` — `UMelodiaHairComponent`
  - Class `UMelodiaHairComponent` not indexed in any scanned Source/ or Plugins/ header
  - _- [x] Native C++ fallback staged in `UMelodiaHairComponent`: attach hair to `head_x`, retain Kawaii _
- `NEXT_HIGHEST_LEVERAGE_TASK.md:12` — `UMelodiaCombatStateComponent`
  - Class `UMelodiaCombatStateComponent` not indexed in any scanned Source/ or Plugins/ header
  - _1. **GS-001 - Fix multiplicative modifier stacking.** `UMelodiaCombatStateComponent::EvaluateModifie_
- `Docs\2026-07-29_PROJECT_HANDOFF.md:15` — `UMelodiaJRPGBattleOverlaySubsystem`
  - Class `UMelodiaJRPGBattleOverlaySubsystem` not indexed in any scanned Source/ or Plugins/ header
  - _- The keyboard legend is now a native, non-focusable presentation overlay owned by `UMelodiaJRPGBatt_
- `Docs\_Reference\BP_INTEGRATION_REVIEW_2026-07-18.md:26` — `IMelodiaEnemyPresentationInterface`
  - Class `IMelodiaEnemyPresentationInterface` not indexed in any scanned Source/ or Plugins/ header
  - _Checked `get_interfaces` on `BP_Melusina` (the player pawn target) and `BP_MelodiaEnemyBase` (the en_
- `Docs\_Reference\BP_INTEGRATION_REVIEW_2026-07-18.md:26` — `IMelodiaCombatPresentationInterface`
  - Class `IMelodiaCombatPresentationInterface` not indexed in any scanned Source/ or Plugins/ header
  - _Checked `get_interfaces` on `BP_Melusina` (the player pawn target) and `BP_MelodiaEnemyBase` (the en_
- `Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md:5` — `UMelodiaBattleSession`
  - Class `UMelodiaBattleSession` not indexed in any scanned Source/ or Plugins/ header
  - _**Current state:** Songcraft effects and generated modifier tables are now present in C++ and partia_
- `Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md:16` — `UMelodiaCombatStateComponent`
  - Class `UMelodiaCombatStateComponent` not indexed in any scanned Source/ or Plugins/ header
  - _- `UMelodiaCombatStateComponent::EvaluateModifier`_
- `Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md:128` — `AMelodiaDungeonRunCoordinator`
  - Class `AMelodiaDungeonRunCoordinator` not indexed in any scanned Source/ or Plugins/ header
  - _**Impact:** `AMelodiaDungeonRunCoordinator::CommitRewardAndAdvance` selects a reward and unlocks the_
- `Docs\_Superseded\MELODIA_ROGUELIKE_GAMELOOP_COMPLETION_PLAN_2026-07-14.md:24` — `UMelodiaBattleSession`
  - Class `UMelodiaBattleSession` not indexed in any scanned Source/ or Plugins/ header
  - _- `UMelodiaBattleSession` owns combat and broadcasts `OnEncounterEnded`._
- `Docs\_Superseded\MELODIA_ROGUELIKE_GAMELOOP_COMPLETION_PLAN_2026-07-14.md:25` — `AMelodiaGameMode`
  - Class `AMelodiaGameMode` not indexed in any scanned Source/ or Plugins/ header
  - _- `AMelodiaGameMode` subscribes to that event, but victory currently only returns the HUD and loop p_
- `Docs\_Superseded\MELODIA_ROGUELIKE_GAMELOOP_COMPLETION_PLAN_2026-07-14.md:44` — `UMelodiaRoguelikeRunSubsystem`
  - Class `UMelodiaRoguelikeRunSubsystem` not indexed in any scanned Source/ or Plugins/ header
  - _`UMelodiaRoguelikeRunSubsystem : UGameInstanceSubsystem`_
- `Docs\_Superseded\MELODIA_ROGUELIKE_GAMELOOP_COMPLETION_PLAN_2026-07-14.md:58` — `AMelodiaDungeonRunCoordinator`
  - Class `AMelodiaDungeonRunCoordinator` not indexed in any scanned Source/ or Plugins/ header
  - _`AMelodiaDungeonRunCoordinator`_
- `Docs\_Superseded\MELODIA_ROGUELIKE_GAMELOOP_COMPLETION_PLAN_2026-07-14.md:236` — `AMelodiaRoomExit`
  - Class `AMelodiaRoomExit` not indexed in any scanned Source/ or Plugins/ header
  - _- The local player crossed the unlocked `AMelodiaRoomExit` through swept physical movement twice._
- `Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md:9` — `UMelodiaRoguelikeRunSubsystem`
  - Class `UMelodiaRoguelikeRunSubsystem` not indexed in any scanned Source/ or Plugins/ header
  - _- **6 new WBP menu panels authored**, all under `/Game/Melodia/UI/`: `WBP_MenuButton` (reusable atom_
- `Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md:9` — `UMelodiaSaveGameSubsystem`
  - Class `UMelodiaSaveGameSubsystem` not indexed in any scanned Source/ or Plugins/ header
  - _- **6 new WBP menu panels authored**, all under `/Game/Melodia/UI/`: `WBP_MenuButton` (reusable atom_
- *... and 216 more*

## Cross-Doc Contradictions

### `UMelodiaTokenWalletSubsystem`

- Claimed present in 6 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Handoffs\CLAUDE_TO_KIRO_STATE_2026-08-01.md, Docs\Handoffs\CLINE_TOKEN_BRANCH_VERIFICATION_2026-08-01.md, Docs\Handoffs\KIRO_MELODY_TOKEN_INTEGRATION_2026-08-01.md, Docs\Handoffs\QWEN_RHYTHM_SKILLS_SCOPE_2026-08-03.md, Docs\MULTI_AGENT_DELEGATION_PROMPTS_2026-08-03.md, _AGENT_GOALS_2026-08-02.md
- **Absent-claiming docs:** Docs\Handoffs\BLACKBOX_AUDIT_COMPLETE_2026-08-01.md

### `UMelodiaHairComponent`

- Claimed present in 6 doc(s) and absent/broken in 3 doc(s)
- **Present-claiming docs:** Docs\BLUEPRINT_WIRING_CHECKLIST_2026-07-30.md, Docs\Handoffs\GEMINI_UI_POLISH_2026-07-31.md, Docs\MELUSINA_HAIR_REEXPORT_CHECKLIST_2026-07-30.md, Docs\MELUSINA_SIR_SKILL_UI_AUTHORING_2026-07-29.md, _AGENT_WORKING_AGREEMENT.md, _VERTICAL_SLICE_SCOPE.md
- **Absent-claiming docs:** Docs\Handoffs\CLINE_BLUEPRINT_WIRING_2026-07-31.md, Docs\Handoffs\CLINE_MONOLITH_COMMANDS_2026-07-31.md, Docs\Handoffs\QWEN_DEEPSEEK_PERSONA_LITE_2026-07-31.md

### `UMelodiaRhythmCombatSubsystem`

- Claimed present in 5 doc(s) and absent/broken in 2 doc(s)
- **Present-claiming docs:** Docs\Handoffs\DEEPSEEK_BLUEPRINT_WIRING_HANDOFF_2026-08-03.md, Docs\Handoffs\KIMI_UI_WIRING_NOTES_2026-08-03.md, Docs\Handoffs\RHYTHM_SKILL_SYSTEM_EXPANSION_2026-08-03.md, Docs\MULTI_AGENT_DELEGATION_PROMPTS_2026-08-03.md, _SESSION_HANDOFF.md
- **Absent-claiming docs:** Docs\Handoffs\QWEN_HARMONIX_QUARTZ_BATTLE_INTEGRATION_2026-08-03.md, Docs\Reviews\RHYTHM_WALLET_REVIEW_2026-08-03.md

### `UMelodiaTravelSubsystem`

- Claimed present in 8 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Handoffs\CLAUDE_COORDINATION_NOTE_2026-07-31.md, Docs\Handoffs\CLAUDE_REBUILD_VALIDATION_HANDOFF_2026-08-01.md, Docs\Handoffs\CLINE_BLUEPRINT_WIRING_2026-07-31.md, Docs\Handoffs\CLINE_MONOLITH_COMMANDS_2026-07-31.md, Docs\Handoffs\DEEPSEEK_BLUEPRINT_WIRING_HANDOFF_2026-08-03.md, Docs\Handoffs\KIRO_CLAUDE_CLINE_EVENING_CORE_LOOP_2026-08-01.md, Docs\WEBSITE_OVERHAUL_LEVEL_MAPPING_2026-07-31.md, _SESSION_HANDOFF.md
- **Absent-claiming docs:** Docs\Handoffs\BLACKBOX_AUDIT_COMPLETE_2026-08-01.md

### `UMelodiaBattleAdapterSubsystem`

- Claimed present in 2 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\MELODIA_AUTHORITATIVE_RHYTHM_COMBAT_WIRING_2026-08-03.md, _SESSION_HANDOFF.md
- **Absent-claiming docs:** Docs\Handoffs\QWEN_RHYTHM_SKILLS_SCOPE_2026-08-03.md

### `UMelodiaNarrativeSubsystem`

- Claimed present in 5 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** AGENTS.md, Docs\Handoffs\MELODIA_GRIEF_HOOK_PRESENTATION_STATE_2026-08-01.md, Docs\Handoffs\QWEN_BATTLE_NARRATIVE_BINDING_2026-08-03.md, Docs\MELODIA_STORY_SEQUENCE_AND_QUILL_CONTRACT.md, Docs\MELODIA_SYSTEMS_COMPOSITION_CONTRACT_2026-07-30.md
- **Absent-claiming docs:** Docs\JRPG_UI_QUILL_NEXT_IMPLEMENTATION_2026-07-28.md

### `UMelodiaCombatStateComponent`

- Claimed present in 1 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md
- **Absent-claiming docs:** NEXT_HIGHEST_LEVERAGE_TASK.md

### `UMelodiaJRPGBattleOverlaySubsystem`

- Claimed present in 1 doc(s) and absent/broken in 2 doc(s)
- **Present-claiming docs:** Docs\MELODIA_AUTHORITATIVE_RHYTHM_COMBAT_WIRING_2026-08-03.md
- **Absent-claiming docs:** Docs\2026-07-29_PROJECT_HANDOFF.md, Docs\JRPG_SAVE_RUNTIME_CHAIN_AUDIT_2026-07-28.md

### `IMelodiaEnemyPresentationInterface`

- Claimed present in 1 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\PRESENTATION_INTERFACE_INTEGRATION_PROPOSAL_2026-07-18.md
- **Absent-claiming docs:** Docs\_Reference\BP_INTEGRATION_REVIEW_2026-07-18.md

### `IMelodiaCombatPresentationInterface`

- Claimed present in 2 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md, Docs\PRESENTATION_INTERFACE_INTEGRATION_PROPOSAL_2026-07-18.md
- **Absent-claiming docs:** Docs\_Reference\BP_INTEGRATION_REVIEW_2026-07-18.md

### `UMelodiaBattleSession`

- Claimed present in 3 doc(s) and absent/broken in 2 doc(s)
- **Present-claiming docs:** Docs\Handoffs\QWEN_BATTLE_NARRATIVE_BINDING_2026-08-03.md, Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md, Docs\_Superseded\MELODIA_ROGUELIKE_GAMELOOP_COMPLETION_PLAN_2026-07-14.md
- **Absent-claiming docs:** Docs\Handoffs\BLACKBOX_AUDIT_COMPLETE_2026-08-01.md, Docs\SCAFFOLDING_DEEP_REVIEW_LIVE_INTEGRATION_2026-07-24.md

### `AMelodiaDungeonRunCoordinator`

- Claimed present in 1 doc(s) and absent/broken in 2 doc(s)
- **Present-claiming docs:** Docs\_Superseded\MELODIA_ROGUELIKE_GAMELOOP_COMPLETION_PLAN_2026-07-14.md
- **Absent-claiming docs:** Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md, Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md

### `UMelodiaRoguelikeRunSubsystem`

- Claimed present in 7 doc(s) and absent/broken in 3 doc(s)
- **Present-claiming docs:** Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md, Docs\Handoffs\BLACKBOX_AUDIT_COMPLETE_2026-08-01.md, Docs\Handoffs\BLACKBOX_HANDOFF_2026-08-01.md, Docs\Handoffs\CLAUDE_TO_KIRO_STATE_2026-08-01.md, Docs\Handoffs\CLINE_TOKEN_BRANCH_VERIFICATION_2026-08-01.md, Docs\Handoffs\KIRO_MELODY_TOKEN_INTEGRATION_2026-08-01.md, Docs\_Superseded\MELODIA_ROGUELIKE_GAMELOOP_COMPLETION_PLAN_2026-07-14.md
- **Absent-claiming docs:** Docs\Handoffs\QWEN_RHYTHM_SKILLS_SCOPE_2026-08-03.md, Docs\MELODIA_TRANSITION_SYSTEM_CONTRACT.md, Docs\Reviews\RHYTHM_WALLET_REVIEW_2026-08-03.md

### `UMelodiaSaveGameSubsystem`

- Claimed present in 1 doc(s) and absent/broken in 2 doc(s)
- **Present-claiming docs:** Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md
- **Absent-claiming docs:** Docs\Handoffs\BLACKBOX_AUDIT_COMPLETE_2026-08-01.md, Docs\MELODIA_FIGMA_UI_WIRING_PLAN_2026-07-16.md

### `UMelodiaRhythmReactivitySubsystem`

- Claimed present in 9 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md, Docs\Handoffs\CLAUDE_KIRO_TANDEM_PREP_2026-08-01.md, Docs\Handoffs\CLAUDE_REBUILD_VALIDATION_HANDOFF_2026-08-01.md, Docs\Handoffs\FX_PPV_UI_INTEGRATION_HANDOFF_2026-08-01.md, Docs\Handoffs\QWEN_HARMONIX_QUARTZ_BATTLE_INTEGRATION_2026-08-03.md, Docs\Reviews\RHYTHM_WALLET_REVIEW_2026-08-03.md, Docs\SCAFFOLDING_DEEP_REVIEW_LIVE_INTEGRATION_2026-07-24.md, Docs\UNIVERSAL_MUSICAL_INFLUENCE_SCAFFOLD_2026-07-18.md, Docs\phase_14_wiring_spec.md
- **Absent-claiming docs:** Docs\QUEUE.md

### `IMelodiaDungeonRecipeConsumer`

- Claimed present in 2 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\COORDINATOR_DEEP_REVIEW_2026-07-17.md, Docs\VERTICAL_SLICE_20MIN_REVIEW_2026-07-17.md
- **Absent-claiming docs:** Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md

### `FMelodiaEnemyDef`

- Claimed present in 2 doc(s) and absent/broken in 2 doc(s)
- **Present-claiming docs:** Docs\COORDINATOR_DEEP_REVIEW_2026-07-17.md, Docs\TOMORROW_2026-07-18_ARTIST_DAY_PLAN.md
- **Absent-claiming docs:** Docs\ASSET_PIPELINE_HARDENING_AND_AGENT_PROMPT_2026-07-14.md, Docs\MELODIA_NPC_VRM4U_READINESS_2026-07-11.md

### `UMelodiaGameUserSettings`

- Claimed present in 3 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\CORE_QOL_AUDIT_2026-07-29.md, Docs\FOUNDATION_LOCKIN_PLAN_2026-07-30.md, Docs\MELODIA_WIDGET_GAMEPLAY_INTEGRATION_2026-07-31.md
- **Absent-claiming docs:** Docs\MELODIA_SYSTEMS_COMPOSITION_CONTRACT_2026-07-30.md

### `FMelodiaNarrativeRecord`

- Claimed present in 6 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\FIRST_DREAM_VERTICAL_SLICE_CHECKLIST_2026-07-28.md, Docs\Handoffs\KIRO_CLAUDE_CLINE_EVENING_CORE_LOOP_2026-08-01.md, Docs\Handoffs\QWEN_DEEPSEEK_PERSONA_LITE_2026-07-31.md, Docs\MELODIA_SYSTEMS_COMPOSITION_CONTRACT_2026-07-30.md, Docs\Research\MELODIA_PSYCH_MUSIC_INDIE_REFERENCE_2026-07-31.md, Docs\WEBSITE_OVERHAUL_LEVEL_MAPPING_2026-07-31.md
- **Absent-claiming docs:** Docs\JRPG_SAVE_RUNTIME_CHAIN_AUDIT_2026-07-28.md

### `UMelodiaMusicClockSubsystem`

- Claimed present in 9 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\FOUNDATION_LOCKIN_PLAN_2026-07-30.md, Docs\GAMEPLAY_REVIEW_2026-07-30.md, Docs\Handoffs\CODEX_PETAL_CANDIDATE_HANDOFF_2026-08-01.md, Docs\Handoffs\QWEN_HARMONIX_QUARTZ_BATTLE_INTEGRATION_2026-08-03.md, Docs\MELODIA_AUTHORITATIVE_RHYTHM_COMBAT_WIRING_2026-08-03.md, Docs\MULTI_AGENT_DELEGATION_PROMPTS_2026-08-03.md, Docs\Research\MELODIA_PSYCH_MUSIC_INDIE_REFERENCE_2026-07-31.md, Docs\Reviews\RHYTHM_WALLET_REVIEW_2026-08-03.md, Docs\WEBSITE_OVERHAUL_LEVEL_MAPPING_2026-07-31.md
- **Absent-claiming docs:** Docs\Handoffs\FX_PPV_UI_INTEGRATION_HANDOFF_2026-08-01.md

### `UMelodiaPartySubsystem`

- Claimed present in 4 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\FULL_GAME_LOOSE_SCOPE_2026-07-31.md, Docs\LOWER_TIER_FOUNDATION_LOCK_2026-07-29.md, Docs\MELODIA_FIGMA_UI_WIRING_PLAN_2026-07-16.md, Docs\SCAFFOLDING_DEEP_REVIEW_LIVE_INTEGRATION_2026-07-24.md
- **Absent-claiming docs:** Docs\Handoffs\KIRO_MELODY_TOKEN_INTEGRATION_2026-08-01.md

### `UMelodiaOpeningFlowSubsystem`

- Claimed present in 2 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Handoffs\CLINE_TOKEN_BRANCH_VERIFICATION_2026-08-01.md, Docs\MELODIA_FIGMA_UI_WIRING_PLAN_2026-07-16.md
- **Absent-claiming docs:** Docs\Handoffs\BLACKBOX_AUDIT_COMPLETE_2026-08-01.md

### `IMelodiaTravelProvider`

- Claimed present in 1 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Handoffs\DEEPSEEK_PARALLEL_LANE_2026-07-31_EVENING.md
- **Absent-claiming docs:** Docs\Handoffs\CLAUDE_COORDINATION_NOTE_2026-07-31.md

### `UMelodiaPacingSubsystem`

- Claimed present in 3 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Handoffs\CLAUDE_COORDINATION_NOTE_2026-07-31.md, Docs\Handoffs\DEEPSEEK_PARALLEL_LANE_2026-07-31_EVENING.md, Docs\Research\MELODIA_PSYCH_MUSIC_INDIE_REFERENCE_2026-07-31.md
- **Absent-claiming docs:** Docs\Handoffs\KIRO_MELODY_TOKEN_INTEGRATION_2026-08-01.md

### `UMelodiaInputContextSubsystem`

- Claimed present in 5 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Handoffs\CLINE_BLUEPRINT_WIRING_2026-07-31.md, Docs\Handoffs\KIRO_GAMEPLAY_SYSTEMS_ACCOUNTING_2026-08-01.md, Docs\MELODIA_CUTE_UI_ELEMENTS_SPEC_2026-07-31.md, Docs\MELODIA_WIDGET_GAMEPLAY_INTEGRATION_2026-07-31.md, Docs\Reviews\JRPG_TRAVERSAL_REVIEW_2026-08-03.md
- **Absent-claiming docs:** Docs\UI_CLOSEOUT_SESSION_2026-08-03.md

### `AMelodiaMovingPlatform`

- Claimed present in 1 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Handoffs\PCG_SESSION_WINS_2026-08-02.md
- **Absent-claiming docs:** Docs\Handoffs\PCG_TEAGARDEN_HERO_2026-08-02.md

### `UMelodiaRhythmCombatSubsystem::InvalidateS`

- Claimed present in 1 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\Handoffs\QWEN_HARMONIX_QUARTZ_BATTLE_INTEGRATION_2026-08-03.md
- **Absent-claiming docs:** Docs\Reviews\RHYTHM_WALLET_REVIEW_2026-08-03.md

### `AMelodiaSmokeCharacter`

- Claimed present in 1 doc(s) and absent/broken in 1 doc(s)
- **Present-claiming docs:** Docs\SCAFFOLDING_DEEP_REVIEW_2026-07-24.md
- **Absent-claiming docs:** Docs\MELODIA_JRPG_CHARACTER_SKILL_SLICE_2026-07-26.md

## Stale Drive Paths

- `_ROADBLOCKS_2026-07-31.md:108` — Stale drive path: `C:\EnvironmentPortfolio\`
- `_SESSION_HANDOFF.md:5` — Stale drive path: `F:\ollama_models`
- `_SESSION_HANDOFF.md:70` — Stale drive path: `F:\ollama_models`
- `CURRENT_STATE.md:122` — Stale drive path: `C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile`
- `INTEGRATION_WORKFLOW.md:439` — Stale drive path: `C:\EnvironmentPortfolio\BS_GodFile`
- `README.md:166` — Stale drive path: `C:\EnvironmentPortfolio\BS_GodFile\Tools`
- `WEBSITE_MAINTENANCE.md:146` — Stale drive path: `C:\EnvironmentPortfolio\_github_deploy`
- `WEBSITE_MAINTENANCE.md:176` — Stale drive path: `C:\EnvironmentPortfolio\_github_deploy\`
- `WORKING_SOLUTION.md:49` — Stale drive path: `C:\EnvironmentPortfolio\BS_GodFile\`
- `Docs\_Reference\MELODIA_ACFU_QUILLSCRIPT_COMPATIBILITY_MATRIX_2026-07-25.md:30` — Stale drive path: `G:\ueprojects\TurnBasedjRPGTemplate`
- `Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md:41` — Stale drive path: `C:\EnvironmentPortfolio\_TouchDesigner\grandmaster_melodia\`
- `Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md:41` — Stale drive path: `C:\EnvironmentPortfolio\BS_GodFile\Plugins\MelodiaCore\Source\MelodiaCore\`
- `Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md:41` — Stale drive path: `C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile`
- `Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md:140` — Stale drive path: `C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile`
- `Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md:150` — Stale drive path: `C:\EnvironmentPortfolio\BS_GodFile`
- `Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md:165` — Stale drive path: `C:\EnvironmentPortfolio\BS_GodFile\Imports\UI\`
- `Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md:178` — Stale drive path: `C:\EnvironmentPortfolio\BS_GodFile`
- `Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md:179` — Stale drive path: `C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile`
- `Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md:195` — Stale drive path: `C:\EnvironmentPortfolio\BS_GodFile`
- `Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md:204` — Stale drive path: `C:\EnvironmentPortfolio\BS_GodFile\Imports\Data\`
- `Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md:213` — Stale drive path: `C:\EnvironmentPortfolio\BS_GodFile`
- `Docs\AI_ORCHESTRATION_HANDOFFS_2026-07-17.md:227` — Stale drive path: `C:\EnvironmentPortfolio\BS_GodFile`
- `Docs\ASSET_PIPELINE_HARDENING_AND_AGENT_PROMPT_2026-07-14.md:331` — Stale drive path: `C:\EnvironmentPortfolio\BS_GodFile`
- `Docs\BLENDER_LIVELINK.md:80` — Stale drive path: `C:\EnvironmentPortfolio\BS_GodFile\Tools\BlenderLiveLink\`
- `Docs\HANDOFF_SURREAL_TO_MELODIA_SYSTEM_2026-07-12.md:5` — Stale drive path: `C:\EnvironmentPortfolio`
- `Docs\HANDOFF_SURREAL_TO_MELODIA_SYSTEM_2026-07-12.md:47` — Stale drive path: `C:\EnvironmentPortfolio\BS_GodFile\deploy\`
- `Docs\HANDOFF_SURREAL_TO_MELODIA_SYSTEM_2026-07-12.md:54` — Stale drive path: `C:\EnvironmentPortfolio\BS_GodFile\deploy\sync_surreal_to_live`
- `Docs\HANDOFF_SURREAL_TO_MELODIA_SYSTEM_2026-07-12.md:71` — Stale drive path: `C:\EnvironmentPortfolio\BS_GodFile\Tools\ensure_blender_mcp`
- `Docs\HANDOFF_SURREAL_TO_MELODIA_SYSTEM_2026-07-12.md:269` — Stale drive path: `C:\EnvironmentPortfolio\BS_GodFile`
- `Docs\HANDOFF_SURREAL_TO_MELODIA_SYSTEM_2026-07-12.md:453` — Stale drive path: `C:\EnvironmentPortfolio\BS_GodFile\deploy\sync_surreal_to_live`
- *... and 151 more*

## Stale Docs (>14 Days)

- `ART_DIRECTOR_REVIEW.md` — Doc date `2026-06-25` is 39d old (threshold: 14d)
- `CHANGELOG_24H.md` — Doc date `2026-07-09` is 25d old (threshold: 14d)
- `CURRENT_STATE.md` — Doc date `2026-07-02` is 32d old (threshold: 14d)
- `CURRENT_SYSTEM_MAP.md` — Doc date `2026-06-25` is 39d old (threshold: 14d)
- `INTEGRATION_WORKFLOW.md` — Doc date `2026-06-27` is 37d old (threshold: 14d)
- `MATERIAL_SYSTEM_REVIEW.md` — Doc date `2026-06-25` is 39d old (threshold: 14d)
- `MELIDIA_LONGTERM_HEALTH_SAFETY_PLAN.md` — Doc date `2026-07-16` is 18d old (threshold: 14d)
- `MONETIZATION_ROADMAP.md` — Doc date `2026-07-16` is 18d old (threshold: 14d)
- `NEXT_HIGHEST_LEVERAGE_TASK.md` — Doc date `2026-07-14` is 20d old (threshold: 14d)
- `PCG_REFINEMENT_REPORT.md` — Doc date `2026-06-25` is 39d old (threshold: 14d)
- `PORTFOLIO_PIPELINE_AUDIT.md` — Doc date `2026-06-25` is 39d old (threshold: 14d)
- `README.md` — Doc date `2026-07-13` is 21d old (threshold: 14d)
- `Docs\_Reference\BP_INTEGRATION_REVIEW_2026-07-18.md` — Doc date `2026-07-18` is 16d old (threshold: 14d)
- `Docs\_Reference\MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md` — Doc date `2026-07-14` is 20d old (threshold: 14d)
- `Docs\AFTERNOON_WORK_SESSION_PLAN_2026-07-12.md` — Doc date `2026-07-12` is 22d old (threshold: 14d)
- `Docs\AgentMemory\Decisions.md` — Doc date `2026-07-02` is 32d old (threshold: 14d)
- `Docs\BLENDER_MELODIA_COCKPIT.md` — Doc date `2026-07-16` is 18d old (threshold: 14d)
- `Docs\COMMIT_PLAN_UNTRACKED_2026-07.md` — Doc date `2026-07-17` is 17d old (threshold: 14d)
- `Docs\CONSISTENCY_REPORT.md` — Doc date `2025-06-25` is 404d old (threshold: 14d)
- `Docs\COORDINATOR_DEEP_REVIEW_2026-07-17.md` — Doc date `2026-07-17` is 17d old (threshold: 14d)
- `Docs\DESIGN_SYSTEM_GAPS.md` — Doc date `2026-06-25` is 39d old (threshold: 14d)
- `Docs\EXPORT_STANDARDIZATION_NOTES.md` — Doc date `2025-06-25` is 404d old (threshold: 14d)
- `Docs\FIGMA_IMPLEMENTATION_GUIDE.md` — Doc date `2026-06-25` is 39d old (threshold: 14d)
- `Docs\FIGMA_MAPPING_GUIDE.md` — Doc date `2026-06-25` is 39d old (threshold: 14d)
- `Docs\GRANDMASTER_MASTER_PLAN_V2.md` — Doc date `2026-07-15` is 19d old (threshold: 14d)
- `Docs\Gumroad\FAB_SDF_PACK_MANIFEST.md` — Doc date `2026-07-18` is 16d old (threshold: 14d)
- `Docs\Gumroad\SKU1_SCREENSHOT_CHECKLIST.md` — Doc date `2026-07-18` is 16d old (threshold: 14d)
- `Docs\HANDOFF_SURREAL_TO_MELODIA_SYSTEM_2026-07-12.md` — Doc date `2026-07-12` is 22d old (threshold: 14d)
- `Docs\IMPRESSIONIST_SYSTEM.md` — Doc date `2026-06-19` is 45d old (threshold: 14d)
- `Docs\MATERIAL_INTEGRATION.md` — Doc date `2026-07-01` is 33d old (threshold: 14d)
- `Docs\MATERIAL_LIBRARY_AUDIT.md` — Doc date `2026-06-19` is 45d old (threshold: 14d)
- `Docs\MATERIAL_LIBRARY_NAPO_LOOP_PLAN.md` — Doc date `2026-06-20` is 44d old (threshold: 14d)
- `Docs\MATERIAL_MIGRATION.md` — Doc date `2026-06-19` is 45d old (threshold: 14d)
- `Docs\MATERIAL_NODE_TREE_REVIEW.md` — Doc date `2026-06-24` is 40d old (threshold: 14d)
- `Docs\MATERIAL_STUDIO_NIKKI_DOCTRINE.md` — Doc date `2026-07-14` is 20d old (threshold: 14d)
- `Docs\material_system_completion_report.md` — Doc date `2026-06-25` is 39d old (threshold: 14d)
- `Docs\MATERIAL_WORK_PLAN.md` — Doc date `2026-06-19` is 45d old (threshold: 14d)
- `Docs\MELODIA_BATTLE_UI_INTEGRATION_2026-07-11.md` — Doc date `2026-07-11` is 23d old (threshold: 14d)
- `Docs\MELODIA_GMM_FAMILY_ARCHITECTURE_PLAN.md` — Doc date `2026-07-12` is 22d old (threshold: 14d)
- `Docs\MELODIA_LUXURY_UI_FILIGREE_NIKKI_MOTION_PLAN_2026-07-12.md` — Doc date `2026-07-17` is 17d old (threshold: 14d)
- `Docs\MELODIA_NEXT_PLAYABLE_SLICE_SWIRL_2026-07-14.md` — Doc date `2026-07-14` is 20d old (threshold: 14d)
- `Docs\MELODIA_NPC_VRM4U_READINESS_2026-07-11.md` — Doc date `2026-07-11` is 23d old (threshold: 14d)
- `Docs\MELODIA_STAGE_SAVE_POLICY.md` — Doc date `2026-07-16` is 18d old (threshold: 14d)
- `Docs\MELODIA_STUDIO_GATE3_UI_UNLOCK.md` — Doc date `2026-07-16` is 18d old (threshold: 14d)
- `Docs\MELODIA_TODAY_PLAYTEST_HANDOFF_2026-07-11.md` — Doc date `2026-07-11` is 23d old (threshold: 14d)
- `Docs\MELUSINA_BLENDER_WARDROBE_SSOT.md` — Doc date `2026-07-13` is 21d old (threshold: 14d)
- `Docs\MELUSINA_IRIS_POSTMORTEM_2026-07-13.md` — Doc date `2026-07-13` is 21d old (threshold: 14d)
- `Docs\MELUSINA_RENDER_SESSION_2026-07-13.md` — Doc date `2026-07-13` is 21d old (threshold: 14d)
- `Docs\MELUSINA_SESSION_LOG_2026-07-13.md` — Doc date `2026-07-14` is 20d old (threshold: 14d)
- `Docs\missing_connections_report.md` — Doc date `2026-06-25` is 39d old (threshold: 14d)
- `Docs\MONETIZATION_GEOMETRY_FIX_EXPORT_2026-07-12.md` — Doc date `2026-07-16` is 18d old (threshold: 14d)
- `Docs\NIKKI_VERTICAL_SLICE_PLAN.md` — Doc date `2026-07-15` is 19d old (threshold: 14d)
- `Docs\PORTFOLIO_IMPROVEMENT_LOG.md` — Doc date `2026-06-25` is 39d old (threshold: 14d)
- `Docs\PORTFOLIO_MAPPING_RULES.md` — Doc date `2026-06-25` is 39d old (threshold: 14d)
- `Docs\PRESENTATION_INTERFACE_INTEGRATION_PROPOSAL_2026-07-18.md` — Doc date `2026-07-18` is 16d old (threshold: 14d)
- `Docs\Production\DREAM_SYSTEM.md` — Doc date `2026-07-04` is 30d old (threshold: 14d)
- `Docs\Production\UNIVERSAL_MASTER_NODE_REVIEW.md` — Doc date `2026-07-04` is 30d old (threshold: 14d)
- `Docs\Production\UNIVERSAL_MASTER_OVERHAUL_PLAN.md` — Doc date `2026-07-04` is 30d old (threshold: 14d)
- `Docs\PROJECT_HEALTH_24H.md` — Doc date `2026-07-16` is 18d old (threshold: 14d)
- `Docs\RELEASE_VALIDATION_REPORT.md` — Doc date `2026-07-17` is 17d old (threshold: 14d)
- `Docs\Research\UE58_MaterialNotes.md` — Doc date `2026-06-20` is 44d old (threshold: 14d)
- `Docs\ROKOKO_MELUSINA_MOCAP.md` — Doc date `2026-07-12` is 22d old (threshold: 14d)
- `Docs\ROUGELIKE_GAMEPLAY_COLLECTION_REVIEW.md` — Doc date `2026-07-14` is 20d old (threshold: 14d)
- `Docs\SCHEMA_ALIGNMENT_MAP.md` — Doc date `2025-06-25` is 404d old (threshold: 14d)
- `Docs\SESSION_FLUFFY_AUDVIS_SPLASH_2026-07-13.md` — Doc date `2026-07-13` is 21d old (threshold: 14d)
- `Docs\SIR_MELODIOUS_IMPORT_FORENSICS_2026-07-13.md` — Doc date `2026-07-13` is 21d old (threshold: 14d)
- `Docs\STAGE22_FINALIZATION_REPORT.md` — Doc date `2026-06-27` is 37d old (threshold: 14d)
- `Docs\standardization_fixes.md` — Doc date `2026-06-25` is 39d old (threshold: 14d)
- `Docs\SUBSTANCE_LACE_BLING_MATERIAL_IMPORT_PLAN.md` — Doc date `2026-07-13` is 21d old (threshold: 14d)
- `Docs\SYSTEM_ORGANIZATION_PLAN.md` — Doc date `2026-06-25` is 39d old (threshold: 14d)
- `Docs\TD_GRANDMASTER_MELODIA_PLAN.md` — Doc date `2026-07-15` is 19d old (threshold: 14d)
- `Docs\TD_PAGE_COPY_2026-07-18.md` — Doc date `2026-07-18` is 16d old (threshold: 14d)
- `Docs\TD_PAGE_DESIGN_SPEC_2026-07-18.md` — Doc date `2026-07-18` is 16d old (threshold: 14d)
- `Docs\TOMORROW_2026-07-18_ARTIST_DAY_PLAN.md` — Doc date `2026-07-18` is 16d old (threshold: 14d)
- `Docs\TOON_MIGRATION_RUNBOOK.md` — Doc date `2026-06-19` is 45d old (threshold: 14d)
- `Docs\TOUCHDESIGNER_MCP_INTEGRATION_PLAN.md` — Doc date `2026-07-15` is 19d old (threshold: 14d)
- `Docs\UNIVERSAL_MUSICAL_INFLUENCE_SCAFFOLD_2026-07-18.md` — Doc date `2026-07-18` is 16d old (threshold: 14d)
- `Docs\VERTICAL_SLICE_20MIN_REVIEW_2026-07-17.md` — Doc date `2026-07-17` is 17d old (threshold: 14d)
- `Docs\WEBSITE_RENDER_CHECKLIST_2026-07-17.md` — Doc date `2026-07-17` is 17d old (threshold: 14d)
- `Docs\WORK_LOG_2026-07-16.md` — Doc date `2026-07-16` is 18d old (threshold: 14d)

## Docs Modified Without Date Bump

- `AGENTS.md` — mtime (2026-07-31) newer than newest date `2026-07-29` — doc modified without date bump
- `ART_DIRECTOR_REVIEW.md` — mtime (2026-07-15) newer than newest date `2026-06-25` — doc modified without date bump
- `CHANGELOG_24H.md` — mtime (2026-07-15) newer than newest date `2026-07-09` — doc modified without date bump
- `CURRENT_STATE.md` — mtime (2026-07-15) newer than newest date `2026-07-02` — doc modified without date bump
- `CURRENT_SYSTEM_MAP.md` — mtime (2026-07-15) newer than newest date `2026-06-25` — doc modified without date bump
- `INTEGRATION_WORKFLOW.md` — mtime (2026-07-24) newer than newest date `2026-06-27` — doc modified without date bump
- `NEXT_HIGHEST_LEVERAGE_TASK.md` — mtime (2026-07-22) newer than newest date `2026-07-14` — doc modified without date bump
- `PCG_REFINEMENT_REPORT.md` — mtime (2026-07-22) newer than newest date `2026-06-25` — doc modified without date bump
- `PORTFOLIO_PIPELINE_AUDIT.md` — mtime (2026-07-15) newer than newest date `2026-06-25` — doc modified without date bump
- `README.md` — mtime (2026-07-31) newer than newest date `2026-07-13` — doc modified without date bump
- `Docs\CONSISTENCY_REPORT.md` — mtime (2026-06-25) newer than newest date `2025-06-25` — doc modified without date bump
- `Docs\DESIGN_SYSTEM_GAPS.md` — mtime (2026-07-24) newer than newest date `2026-06-25` — doc modified without date bump
- `Docs\EXPORT_STANDARDIZATION_NOTES.md` — mtime (2026-06-25) newer than newest date `2025-06-25` — doc modified without date bump
- `Docs\FIGMA_IMPLEMENTATION_GUIDE.md` — mtime (2026-07-24) newer than newest date `2026-06-25` — doc modified without date bump
- `Docs\FIGMA_MAPPING_GUIDE.md` — mtime (2026-07-24) newer than newest date `2026-06-25` — doc modified without date bump
- `Docs\GRANDMASTER_MASTER_PLAN_V2.md` — mtime (2026-07-24) newer than newest date `2026-07-15` — doc modified without date bump
- `Docs\IMPRESSIONIST_SYSTEM.md` — mtime (2026-06-24) newer than newest date `2026-06-19` — doc modified without date bump
- `Docs\MATERIAL_INTEGRATION.md` — mtime (2026-07-22) newer than newest date `2026-07-01` — doc modified without date bump
- `Docs\MATERIAL_LIBRARY_AUDIT.md` — mtime (2026-07-16) newer than newest date `2026-06-19` — doc modified without date bump
- `Docs\MATERIAL_MIGRATION.md` — mtime (2026-07-01) newer than newest date `2026-06-19` — doc modified without date bump
- *... and 16 more*

## Unresolved TODO/FIXME/HACK Markers

- `_ROADBLOCKS_2026-07-31.md` — 1 unresolved: workaround
- `_TASK_QUEUE.md` — 1 unresolved: hack
- `CHANGELOG_24H.md` — 1 unresolved: Workaround
- `Docs\Handoffs\KIRO_MELODY_TOKEN_INTEGRATION_2026-08-01.md` — 1 unresolved: hack
- `Docs\NIKKI_VERTICAL_SLICE_PLAN.md` — 3 unresolved: TODO
- `Docs\PORTFOLIO_MAPPING_RULES.md` — 2 unresolved: XXX
- `Docs\Research\MELODIA_PSYCH_MUSIC_INDIE_REFERENCE_2026-07-31.md` — 1 unresolved: hack
- `Docs\Reviews\DOC_HEALTH_REPORT_2026-08-03.md` — 11 unresolved: FIXME, TODO, Workaround, XXX, hack, workaround
- `Docs\SCAFFOLDING_DEEP_REVIEW_2026-07-24.md` — 1 unresolved: hack
- `Docs\TD_GRANDMASTER_MELODIA_PLAN.md` — 1 unresolved: TODO

## File Inventory

Scanned 324 markdown files.

