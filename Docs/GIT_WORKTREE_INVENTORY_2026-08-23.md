> **Superseded snapshot (2026-08-24):** Path and ownership state moved on; use [Git Worktree Inventory — 2026-08-24](GIT_WORKTREE_INVENTORY_2026-08-24.md).

# Git worktree ownership inventory — 2026-08-23

This is a recovery manifest for the mixed `main` worktree. It is an ownership
and commit-boundary record, not approval to stage every listed file. Do not use
`git clean`, `git reset --hard`, a broad `git add`, or a `checkout -- .` style
revert while any row is still pending.

## Commit order and ownership

| Lane | Paths | Disposition | Required proof before a commit |
| --- | --- | --- | --- |
| P0 runtime portability | `.gitignore`; `Docs/Evidence/2026-08-22_p0_enemy_territory_guard.md`; `Content/TurnBasedJRPGTemplate/Blueprints/EnemyExplorePawns/BP_EnemyExplorePawnBase.uasset`; `.../AggressiveEnemyExplorePawns/BP_AggressiveEnemyExplorePawnBase.uasset` | Commit first, after both remote LFS locks are acquired. | Existing scoped compile/PIE evidence in the companion document; `git lfs fsck`; LFS lock ownership; diff check. |
| P0 coordination ledger | `Docs/P0_TASK_LEDGER.json` | Preserve but defer to a separate audit-documentation commit. It records a point-in-time coordination state and is not direct implementation or the P0 portability evidence summary. | Audit timestamp and live-editor status must match the authoring handoff at commit time. |
| Save migration and economy | `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaPersistenceTests.cpp`; `MelodiaSaveGame.h`; `MelodiaTokenWalletSubsystem.cpp`; `MelodiaTokenWalletSubsystem.h`; untracked `MelodiaEconomyTestListener.h`; `Content/Python/author_melodia_universal_assets.py`; `specs/blueprints/fixtures/universal_melody_token.v1.json` | Preserve and split into a dedicated save/economy commit. Do not combine with HUD or Blender work. | Native build plus save migration and wallet contract tests. |
| MelodiaCore companion/fur/garden experiments | Untracked `MelodiaCompanionComponent.{cpp,h}`; `MelodiaCompanionData.{cpp,h}`; `MelodiaFurBackend.{cpp,h}`; `MelodiaResonanceGardenData.{cpp,h}`; `MelodiaCompanionRulesTests.cpp`; `Content/Melodia/Companions/ChoralSheep/{README.md,ChoralSheepDefinition.json}`; the companion-specific `.gitignore` exception | Preserve, then move to an isolated feature worktree before review. These are a separate gameplay-feature spike, not save migration or P0. | Feature-specific source review, native build, asset-provenance review, and a scoped runtime test. |
| HUD/rhythm integration | `Source/BS_GodFile/MelodiaIntegration/MelodiaJRPGBattleOverlaySubsystem.{h,cpp}`; `MelodiaUIBridgeSubsystem.{h,cpp}`; `Content/Melodia/UI/Rhythm/WBP_MelodiaRhythmHighway.uasset`; `Content/Melodia/DataStuctures/DT_MelodySlime_RoomMods.json`; `DT_MelodySlime_Skills.json`; `Plugins/MelodiaWardrobe/MelodiaWardrobe.uplugin`; `Plugins/UEBlueprintMCP/UEBlueprintMCP.uplugin`; `Tools/echo_run.py`; `specs/echo_pipeline.json` | Preserve and split into a HUD/rhythm commit only after source review. | Closed-editor native build, HUD ownership contract, and a viewport/runtime proof. |
| World-gen/capture provenance | `Content/Python/resonant_world_capture_manifest.py` | Preserve; commit as its own source-only change. | Manifest tests, Python syntax check, and diff check. |
| Lookdev material experiment | Eight `Content/EnvSandbox/Materials/Instances/**` assets; `Content/EnvSandbox/PCG/Musical/MI_Piano_{Ebony,Ivory}.uasset`; `Docs/V24_LOOKDEV_SESSION_PLAN_2026-08-23.md` | Preserve but defer. Do not stage into P0, gameplay, or website commits. | Explicit visual approval, matching runtime envelope, and LFS locks. |
| Melusina character and studio | `ABP_Melusina_Current.uasset`; `ABP_Melusina_WaterHair.uasset`; `BP_MelusinaJRPGCharacter.uasset`; `Content/Python/melodia_blender_offline_preview.py`; `Docs/MELODIA_STUDIO_PIE_ROOM_WINDOW_REVIEW_2026-08-23.md`; `Docs/MelodiaStudio/MUSIC_KIT_LEDGER_20260823.md`; `Exports/melodia_history.mid`; `Tools/BlenderAddons/melodia_{aura,stage,studio}/**`; `deploy/_sync_addon_to_blender_5_2.py`; `deploy/music_kit_loop.ps1`; `deploy/surreal_arch/chime_row.py`; `deploy/surreal_arch/melodia_gn/**`; `deploy/surreal_arch/melusina_portrait/__init__.py`; `deploy/surreal_arch/music_ui.py`; `deploy/surreal_greybox/__init__.py`; `deploy/surreal_os/_io.py`; tracked `deploy/surreal_arch/{bootstrap,integration,pie_menu,ui}.py`; `deploy/surreal_architecture_gen.py`; `deploy/surreal_greybox/shells.py`; `deploy/surreal_arch/melusina_portrait/expression_mixer.py` | Preserve and move to an isolated Blender/studio worktree before any merge. The current material explicitly records a prior destructive mirror/revert incident. | Restore the six missing verifier scripts, then run a full no-skip factory-startup Blender verification, source review, and a separate commit series; never a gameplay commit. |
| Claireon plugin import | `Plugins/Claireon/**` | Preserve but defer in an isolated plugin worktree. Do not recursively stage it. Exclude generated `Binaries/` and `Intermediate/` when deciding what source is intended. | Plugin provenance/license review, descriptor/source build, and its own `.gitignore` audit. |
| External adapter research | `Docs/Integrations/MELODIA_EXTERNAL_ADAPTER_LEDGER.md` | Preserve but defer with the experimental integration work. It is a research/provenance ledger, not an implementation approval. | License, engine-version, and source-provenance review before any adapter source is added. |

## Intentional non-actions

- `BP_AverageEnemyExplorePawn` and `BP_InteractionDetector` remain ignored because
  they were coverage subjects, not edited P0 assets.
- Passive stock enemy-pawn assets remain ignored; the P0 exception intentionally
  exposes only the Base and Aggressive Blueprint assets named above.
- The MIDI export is preserved but deferred; do not add it to source control
  until it is designated a playable source asset rather than a generated
  history artifact.
- No bulk EnvSandbox, marketplace, generated plugin binary, `Saved/`, or
  Blender cache path becomes tracked through this recovery.

## Git/LFS operating rules

1. Run remote Git/LFS commands in a normal user context. The Codex sandbox
   cannot read the user GitHub CLI configuration; native `git lfs status` and
   `git lfs locks` do pass.
2. Run `git update-index --refresh`, `git lfs fsck`, `git lfs status`, and
   `git lfs locks` serially, not in parallel with another Git/LFS operation.
3. Acquire locks before staging an edited `.uasset` or `.umap`; if GitHub is
   unreachable, preserve the local change and defer staging/pushing it.
4. Fetch before each push and never force-push this shared `main` checkout.
5. Treat the historical `Mud.uasset` LFS 404 as a separate, old merge artifact
   unless a current fetch or checkout reproduces it; current local LFS fsck is
   clean.
