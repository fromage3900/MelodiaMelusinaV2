# Duplicate tree inventory — 2026-08-11

**Status:** inventory only. Owner sign-off required before quarantine/delete.  
**Echo:** not a completion gate. Related plan: [`Docs/ECHO/reconciliation_duplicate_trees.md`](../ECHO/reconciliation_duplicate_trees.md).

## Correction vs older docs

The 33-asset MelodiaIntegration mirror is **tracked in MelodiaMelusinaV2** (`git ls-files` count = 33). Older prose saying it is untracked is stale.

## Canonical vs mirror

| Role | Path |
|------|------|
| LIVE Melodia battle UI | `Content/MelodiaIntegration/UI/BP_MelodiaBattleUI.uasset` |
| MIRROR (shadow-risk copy) | `Content/MelodiaIntegration/Content_MelodiaIntegration/UI/BP_MelodiaBattleUI.uasset` |
| Stock JRPG battle UI | `Content/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI.uasset` |

## Mirror contents (33)

All under `Content/MelodiaIntegration/Content_MelodiaIntegration/`:

- Blueprints: BattleBridge, JRPG GI/GM/PC configs, MelusinaJRPGCharacter, Sir morning intro
- Config: DA_* cadence/harmony + `DA_MelodiaIntegrationConfig` copy
- MIDI / Narrative Quill assets / Party Sir unit + skills
- UI: MelodiaAction*, MelodiaBattleUI, RhythmPrompt, TurnOrderList

## Recommended next action (not executed)

1. `bp_live_path` on each mirror asset when editor is up (rule: ORPHAN ≠ delete).
2. Owner chooses quarantine to `_QuarantineAssets_YYYYMMDD/` (relocate, never `Remove-Item`).
3. Record a ledger note only after sweep clean — do not invent a completion-gate pass.

## EnvSandbox note (placement50)

This checkout has **0** tracked `Content/EnvSandbox/**` files. Universal PCG/material binaries must be pulled on the Windows tree before `placement50` can certify its required paths.
