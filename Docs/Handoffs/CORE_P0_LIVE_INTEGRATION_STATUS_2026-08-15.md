# Core P0 Live Integration Status — 2026-08-15Z

## Scope

This handoff records the current gameplay-BP materialization, Melusina V2 bind
repair, Echo status, and the next Core P0 slice. The disposable gameplay proof
map is:

`/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap`

The player-facing Morning → KaleidoNave route remains owner-controlled and is
not replaced by this integration-map fixture pass.

## Completed in this work block

### Gameplay BP kit

The following assets were materialized through Monolith, compiled with zero
reported errors/warnings, saved, and read back before the editor went offline:

- `BP_MelodiaTraversalGate_Base` + `BP_MelodiaTraversalGate_HoverFixture`
- `BP_MelodiaEnemy_Base` + `BP_MelodiaEnemy_SingleStock`
- `BP_MelodiaEncounter_Base` + `BP_MelodiaEncounter_FirstDream`
- `BP_MelodiaPortal_Base` + `BP_MelodiaPortal_LockedTraversal`
- `BP_MelodiaWorldChallenge_Base` + `BP_MelodiaWorldChallenge_FirstResonance`
- `BP_MelodiaStateAnchor_Base` + `BP_MelodiaStateAnchor_FirstDreamProgress`

The Skill template remains intentionally unmaterialized because its definition,
cooldown, and point/mana authority bridge is not closed.

`BP_MelusinaJRPGCharacter` was updated only in its gameplay traversal component:
`bRequireCapabilityProviderForGlide=true` and
`TraversalCapabilityContextId=active_traversal_context`. The BP compiled and
saved cleanly. Melusina V2/ABP/Kawaii/material assets were not changed by this
lane.

The locked traversal fixture CDO was redirected to
`/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap`; it does not redirect the
production route.

### V2 bind repair and reimport

`Tools/bind_melusina_v2_pieces.py` now preserves the scale of an imported
canonical UE armature when `--canonical-armature-fbx` is supplied. Staged mesh
geometry still receives the metre → centimetre bake; the canonical rig does not
receive a second 100× bake.

Fresh export proof:

- `Saved/Audit/melusina_v2_piece_bind_report_canonical_scale_fix.json`
- five fresh `Exports/MelusinaClothes/V2/SK_Melusina_V2_*.json` sidecars
- `Saved/Audit/melusina_v2_actual_fbx_contract_report_canonical_scale_fix.json`

Observed values:

- `rig_bake_factor=1.0`
- `rig_scale_applied=false`
- `spine_02_x` sidecar probe extent `105.489456`
- 465 contract bones in the export graph
- all five actual FBX payloads pass; imported armature has 464 internal bones
  plus the expected root shim
- no dotted, missing, or unexpected contract bones
- Body imports with 120 shape keys (Basis plus the expected 119 morph targets)

The Melusina lane has reimported all five corrected FBXs under
`/Game/Melodia/Characters/Melusina/Outfits/V2` using the existing
`SK_Melusina_Skeleton` and approved materials. The pawn remains on original
`SK_Melusina`; V2 promotion and runtime visual approval are still pending UE
bind-pose readback and controlled preview/PIE evidence.

### Offline/Echo evidence

- `Tools/run_contract_tests.py`: **17/17 passed** after the preflight state-model
  repair.
- The BP preflight now distinguishes `materialized_requires_live_readback`
  from a true design block. Six materialized candidates require live proof; only
  Skill remains design-blocked. The preflight itself created no assets.
- The most recent Echo static chain reached 4/5 checks: graph reachability,
  BP live path, BP sweep, and UI lint passed. `verify_baseline` remains blocked
  by three pre-existing material-master drifts; do not rewrite the baseline
  without owner approval.

## Current live blocker

The single editor relaunch reached Monolith initialization, then entered a
blocking `MODAL_OPEN` at `2026.08.15-00:27:41Z`. The exact process is
`UnrealEditor` PID `42688`; it has no top-level window handle and port `9316`
is closed. The log stops immediately after the modal marker, with unrelated
AssetRegistry warnings about an unknown custom version in two legacy Brushify
`test_2123.uasset` packages.

No V2/ABP/Kawaii/material mutation was performed during the blocked session.
The source lane explicitly requested that this editor not be terminated. A
visible manual dismissal is preferred. If the modal cannot be dismissed, the
owner must explicitly authorize stopping exactly PID `42688` and relaunching
once with `-unattended`; do not kill broad process groups or start a second
editor.

## Next execution sequence

1. Restore one responsive editor and Monolith `127.0.0.1:9316`.
2. Load `MelodiaIntegrationMap` and read back the six BP parents, CDOs,
   components, compile status, and the traversal provider settings.
3. Read back the five reimported V2 mesh skeleton/bind-pose values while keeping
   the pawn on original V1 assets.
4. Run Echo `runtime_gates` only after reviewing the map and log state. Record
   observed PIE evidence; a HOLD is not a pass.
5. Use the IntegrationMap for deterministic battle, shop, save, forge/craft,
   boss/encounter, portal/traversal, and reset/idempotency fixtures. Keep the
   production Morning → KaleidoNave golden route for the owner’s later manual
   PIE pass.
6. Only after those observations, decide whether to promote corrected V2 to the
   pawn. Keep GC_MelusinaHairFlip_v22 staging-only until the preview proves the
   attachment and visual result.

## Ownership boundaries

- Melusina lane: V2 reimport/promotion, ABP, KawaiiPhysics, materials, sockets,
  and visual/PIE evidence.
- Gameplay lane: BP kit, traversal capability contract, IntegrationMap fixture
  validation, Echo evidence, and this handoff.
- Claude/build lane: C++/Python/docs outside the editor-owned gameplay BP scope.
- `_TASK_QUEUE.md` remains a shared coordination surface and is not edited here.
