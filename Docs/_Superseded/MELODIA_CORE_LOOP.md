# Melodia Core Loop — BS_GodFile Bridge

> **Superseded (2026-07-26).** `G:\Melodia` and MelodiaCore are no longer the
> gameplay authority. The complete TurnBased JRPG template is the provisional
> mechanical baseline, with QuillScript evaluated separately behind a
> project-owned adapter. See
> `MELODIA_UE58_INTEGRATION_ARCHITECTURE_2026-07-26.md`.

This document is retained for historical reference only. The current active
integration record is `Docs/MELODIA_UE58_INTEGRATION_ARCHITECTURE_2026-07-26.md`.

## What lives where

| Capability | G:\Melodia | BS_GodFile |
|------------|------------|------------|
| Battle session kernel | `UMelodiaBattleSession` | — |
| Dissonance / sound | `UMelodiaDissonanceSubsystem` | — |
| Phoenix UI bridge | `MelodiaPhoenixBattleBridgeLibrary` | JRPG template only |
| Quest on win | `AMelodiaQuestManagerBase` | `BP_QuestManager` (wire on victory) |
| Notation UI art | `Content/Melodia/UI/Notation/` | Copy textures/fonts for mock |

## BS_GodFile setup

Run `Content/Python/setup_melodia_core_loop_demo.py` in editor, then place
`BP_InteractionBattle` + `BP_BattleController` on a demo map under
`Content/Melodia/Levels/`. On `E_BattleResult::Victory`, call
`BP_QuestManager` notify hook.

## Migrating full loop later

Copy `MelodiaMelusina_PROD` module + `Content/Melodia/` gameplay assets, or
link Melodia as sibling project for environment + game split.

See `G:\Melodia\Docs\CORE_LOOP_STATUS.md` for acceptance criteria.
