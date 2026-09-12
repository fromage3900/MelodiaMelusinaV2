# Rebuild Status and Next Slice

**Date:** 2026-08-14  
**Goal:** keep extending the Melodia integration layer toward a reusable, data-driven
gameplay BP kit while preserving one authority per concern.

## Current state

- The latest read-only owner check finds **0 UnrealEditor**, **0 UnrealEditor-Cmd**,
  **8 monolith_proxy**, and no confirmed listener on `127.0.0.1:9316`. Recent
  `MODAL_OPEN`/save markers remain in the newest log. Claude owns the current build
  lane; do not launch a competing build or mutate the live editor.
- The same log later records a PIE start on `MelodiaIntegrationMap` using
  `BP_MelodiaJRPGGameMode_C`, plus a live `ABP_Melusina_WaterHair` attachment to the
  character hair component. Treat this as provisional observation only until one
  editor/proxy owner is isolated and the route is replayed in a clean session.
- The newest log tail records another IntegrationMap PIE at approximately 18:39:54,
  again with `BP_MelodiaJRPGGameMode_C` and `ABP_Melusina_WaterHair` bound. This is
  still not attributable proof of Kawaii, live capability registration, T3D, or the
  player-facing P0 route.
- The worktree is intentionally dirty with parallel art, gameplay, automation, and
  ledger edits. `_TASK_QUEUE.md` is being edited by another owner; do not rewrite it.
- `Tools/test_t3d_safe_wire.py` has a passing 42/42 pure-logic result, but live
  request-derived postcondition evidence is still required.
- The current closed-editor native build has now passed: UHT, `MelodiaTraversalComponent.cpp`,
  and the final `BS_GodFile.exe` link all succeeded. This is source/build evidence only;
  the editor re-entry is still stalled in Turnkey SDK detection and Monolith `9316` is
  unavailable.
- The latest read-only check is editor-free, so `safe_to_compile=true`; it also
  reports `safe_for_live_readonly=false` because Monolith `9316` is absent. This is
  an owner gate result, not build evidence. No process was terminated and no second
  editor was launched.
- The latest Wardrobe lane adds reflected Resonant Form/style data after the last
  verified closed-editor Wardrobe build. It needs one clean closed-editor compile
  before any live claim is made. A source-level module-neutral capability registry
  now connects Wardrobe's read-only provider to traversal requests and the jump-to-
  glide input path when opt-in is enabled. `UMelodiaTraversalComponent` remains the
  only movement mutator. A direct `BS_GodFile -> MelodiaWardrobe` dependency is
  forbidden because Wardrobe already depends on `BS_GodFile`.
- Offline validation is green for the current contract layer: the seven L1 fixture
  specs, the seven-template BP readiness inventory, and the T3D pure-logic suite
  (`42/42`). This is not a substitute for editor, map, PIE, or live T3D evidence.
- The versioned content lifecycle contract now exists at
  `specs/content/melodia_content_release_manifest.v1.json`, covering permanent,
  scheduled, recurring, rerun, retired, fallback, reset, preload, migration, and
  reference-safe cleanup states.
- The dependency-free contract runner now covers **17/17** offline suites with a
  fixed coverage floor and is wired into Echo Gates and BuildGraph; it does not
  rely on pytest collection.
- The registry/fixture parity suite confirms all seven BP families point to the
  intended parent templates, runtime authorities, and materialization order.
- The new read-only owner gate `Tools/melodia_rebuild_preflight.py` is executable
  on this Windows image. Its latest report found **1 UnrealEditor**, **0
  UnrealEditor-Cmd**, **8 monolith_proxy**, and no confirmed `127.0.0.1:9316`
  listener. It fails closed for both compile and live-readonly work and issues no
  mutations.
- The package now references one shared capability/context/progression gate for all
  seven BP families. Its offline contract is green and requires typed decisions,
  no mutation on blocked results, request fingerprints, and re-evaluation after
  load/context/travel/reset transitions. Every L1 fixture package references it;
  there is no live registry/build/PIE proof yet.
- WorldChallenge and StateAnchor now have explicit adapter contracts with atomic
  rollback and replay rules. The contract audit now also checks that BP-local
  attempt state is not misrepresented as a native persistence surface and that
  challenge/anchor IDs are allowlisted. This removes ambiguity from their future
  native work, but does not promote either family: UHT/build, live graph, save/load,
  and fixture evidence are still required.
- Their first fixture IDs are centralized in the merge-only seed
  `specs/progression/melodia_integration_allowlist_seed.v1.json`; the live owner
  must merge those values into `DA_MelodiaIntegrationConfig` before fixture runs.
- The roguelike content refresh confirms 26 authored blessing rows, zero burden rows,
  existing `WBP_BlessingBurden` presentation, and no typed native catalog consumer.
  This is now fail-closed in `specs/roguelike/melodia_blessing_burden_contract.v1.json`.

## Kawaii physics fixture

The reusable probe is safely present at
`/Game/MelodiaIntegration/Tests/BP_KawaiiPhysicsPlacementProbe` and has proven:

- compatible `SK_MelusinaHair` + `ABP_Melusina_WaterHair` presentation;
- `PreviewMesh`, `PreviewCamera`, and `ResetAnchor` components;
- `InitialTransform` and `bKawaiiDebug` variables;
- `ResetSimulation` and `ToggleKawaiiDebug` events;
- clean compile and exported EventGraph fingerprint
  `75193c2ad364e7629bc88c4995f563ef02062d42`.

It is not yet L4. A live spawn was observed, but the integration map save crashed
before persistence. The map's Windows read-only attribute has been cleared. The next
clean session must verify the hair physics asset's root body, save the probe in
`/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap`, re-query the actor list, and
run two deterministic PIE resets. A log warning about a missing root physics body
means the override may need to be removed if the Kawaii AnimBP's limits data asset is
the intended runtime authority.

The latest editor log also records an invalid read-only probe attempt using
`AnimNode_KawaiiPhysics.static_class` and `node_pos_x`. Use
`Content/Python/audit_kawaii_runtime_readonly.py` for the next clean session; it
uses only reflected editor-node/property reads and issues no mutation.

For the procedural dungeon lane, use `Content/Python/audit_roguelike_generator_readonly.py`
before any generation helper. It verifies the generator parent, recipe-consumer interface,
function graphs, and placed actors without calling generation, saving, map loading, or PIE.

## Next executable slice after rebuild

1. Obtain the current build-lane result, then resolve the Monolith handoff before
   treating any import or save as proof; keep one explicitly owned session and do
   not terminate it from this goal. Re-run `python Tools/melodia_rebuild_preflight.py`
   and require one editor, one confirmed Monolith listener, and no active
   import/modal boundary.
2. Finish one closed-editor compile for the latest reflected Wardrobe changes.
3. Re-enter once, reindex Monolith, and run the player-facing Core P0 golden route:
   `L_MelusinaMorning` → `L_KaleidoNave`; use `MelodiaIntegrationMap` only for
   deterministic persistence checkpoints.
4. Run the live T3D safe-wire probe after the golden route with expected nodes,
   links, semantic labels, and post-save re-export equality supplied independently
   of the server response.
5. Run the read-only Kawaii inspector, then complete Kawaii map/PIE evidence after the P0/T3D gates.
6. Close the Core P0 Dream golden route in the shared ledger without editing its row
   while another owner has the file open.
7. Verify the shared capability gate in the clean editor pass, then author exactly
   two first live fixtures from the shared package contract:
   `single_target_resonance_skill` and `hover_gate_with_dungeon_lock`.
8. Keep the new WorldChallenge and StateAnchor artifacts contract-only until their
   source-wired generic native adapters pass clean UHT/compile/reflection and
   replay-safe live fixtures; do not promote their JSON contracts to live Blueprint
   authority early.
9. Only after those first two pass L4 should the team add the first Enemy,
   Encounter, or Portal fixtures.

### Skill authority gate

The first Skill fixture is not promotable yet. `UMelodiaRhythmSkillDefinition` and
`FMelodiaSongSkillRecipe` are structurally different authorities: the former owns
pattern/effect/target/cost data for the rhythm subsystem, while the latter owns the
note/instrument/element/material/power recipe consumed by the stock battle execution
path. A guessed adapter would create unreviewed gameplay semantics and can also make
SP and skill-point spending diverge. The next Skill task is therefore a reviewed
one-way bridge contract with explicit field mapping and one resource authority.

The offline contract gate `python Tools/test_melodia_content_fixtures.py` currently
passes for all seven fixture specs. This proves only that the L1 package envelopes
are complete and authority-safe; it is not live Blueprint or PIE evidence.

## Infinity Nikki-derived design constraints

Public Version 2.8 material shows an ability package with multiple traversal modes,
context-specific locks, configurable input behavior, open-world scene preview,
effect toggles, styling-scheme import/fallback behavior, mount-to-gathering ability
interruption, Heart of Infinity progression, and region resource cleanup. Melodia
should model the same class of problem with stable IDs and local contracts, not product
economics:

`CapabilityId -> ModeSet -> ContextPolicy -> VariantSet -> PreviewPolicy -> Fixture`

The shared contract and BP kit are the correct integration seam for this. It keeps
new skills, enemies, portals, traversal states, and future wardrobe presentation
additive without adding another GameMode, save authority, or travel path.

## Definition of “ready”

- L0: path, owner, parent, identity, and purpose recorded.
- L1: authority, fields, restrictions, and dependency contract recorded.
- L2: live graph compiled and forbidden ownership absent.
- L3: disposable fixture exercises the real route and failure path.
- L4: compile, map reachability, runtime, reset/idempotency, and fresh evidence pass.
