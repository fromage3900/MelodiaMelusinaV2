# Codex Gameplay Research and Restart Handoff

**Checkpoint:** 2026-08-15 UTC
**Map for core integration proof:** `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap`
**Player-facing golden route:** remains separate; see `specs/p0/core_p0_dream_golden_run.v1.json`.

## What is recorded

- Research synthesis: `Docs/Research/MELODIA_UE_JRPG_WORKFLOW_RESEARCH_2026-08-15.md`.
- Additive Infinity Nikki gameplay ledger: `Saved/Audit/melodia_gameplay_task_ledger_infinity_nikki_2026-08-15.json`.
- Existing evidence remains authoritative for the current BP shell and live-gate state:
  - `Saved/Audit/melodia_bp_task_ledger_snapshot_2026-08-15.json`
  - `Saved/Audit/melodia_definition_asset_creation_manifest_2026-08-15.json`
  - `Saved/Audit/skill_definition_path_alignment_audit_2026-08-15.json`
  - `Saved/Audit/integration_map_fixture_static_probe_2026-08-15.json`
  - `Saved/Audit/core_p0_offline_gate_snapshot_2026-08-15.json`

## Current truth

- T3D safe-wire: 42/42.
- Contract suite: 17/17.
- Six of seven BP families have offline materialized shells; none are promoted to L2+ on fresh live evidence.
- The Skill family remains blocked by a definition-path/cooldown/SP authority mismatch.
- The First Dream encounter CDO fix is prepared but must wait for live actor/tag/roster readback and a responsive Monolith endpoint.
- The IntegrationMap is a proof fixture, not the player route.
- The editor/Monolith gate is still closed/stale (`MainWindowHandle=0`, port `9316` not listening); no live Blueprint/DataAsset mutation was attempted here.
- Melusina V2, ABP/BlendSpace, KawaiiPhysics, materials, and optional hair VFX remain owned by the Melusina lane. Their handoff is evidence-only until visual/runtime promotion is accepted.
- `_TASK_QUEUE.md` was deliberately not edited.

## Handoff to the next agents

### Agent A — editor/integration owner

Own one clean editor process only. After restart:

1. Confirm no duplicate UnrealEditor/Monolith owner and record PID, window handle, port, and log path.
2. Load the Integration Map without mutating Melusina assets.
3. Read back actor tags, `Encounter_enemy.single_stock_fixture`, `offLevelBattleData`, and a nonempty stock `enemyList`.
4. Only if those preconditions pass, apply the prepared First Dream `EnemyId` fix, compile/save/read back, and run success, abort/failure, reset.
5. Leave fresh JSON evidence under `Saved/Audit` and do not overwrite the shared ledger or `_TASK_QUEUE.md`.

### Agent B — C++/bridge owner

Own the skill-definition bridge and source/build lane:

1. Reconcile `/Game/MelodiaIntegration/Definitions` with the native discovery path under `/Game/MelodiaIntegration/Config`.
2. Select one authoritative cooldown and one SP/mana contract.
3. Add stable request identity and a result journal before authoring a runtime-ready skill asset.
4. Run the closed-editor reflected build; report exact binary/DLL timestamp and test output.
5. Do not change editor-owned `.uasset` fixtures or Melusina V2 files in the same commit.

### Agent C — content/gathering owner

After P0 is proven, build one disposable gathering slice only:

1. Define one gatherable node, one required capability, one material, and one recipe.
2. Route the grant through the canonical inventory transaction and save boundary.
3. Add blocked/allowed/reset/repeat evidence and a typed visual event for Niagara/UI observers.
4. Keep the BP thin; do not create a local inventory or save authority.

## Collaboration rules

- One writer per asset and one lane per commit.
- Check `git log -1` before staging; re-stage after any parallel commit.
- Never use `git reset` or `git checkout` to recover from parallel work.
- Do not stage `_TASK_QUEUE.md`, unrelated material/V2 assets, or another lane's C++/Python/docs.
- The next shared-ledger reconciliation should merge this snapshot additively rather than replacing earlier rows.

## Restart boundary

The restart is intentionally the final action after the checkpoint commit and handoff
message are recorded. On the next session, reopen the editor only through the supported
project path and revalidate Monolith before any live mutation. No work in this handoff
claims successful PIE or visual V2 runtime proof.
