# Melodia Goal Status and Next Steps

**Date:** 2026-08-14  
**Goal:** make the Melodia integration layer safe to extend with reusable,
data-driven gameplay BPs while protecting the Core P0 Dream slice and preserving
one authority per concern.

## Current status

The recorded pre-reentry native source lane is build-green from closed-editor
UBT/UHT/compile/link evidence; the later capability-provider and Blueprint-shell
edits still need one clean post-change compile. The latest read-only owner check
now finds **0 `UnrealEditor`**, **0 commandlets**, eight `monolith_proxy` processes,
and no listener on `127.0.0.1:9316`. Claude owns the current build lane, so this
goal does not launch a competing build or infer a build result from process absence.

The newer log has since reached PIE on `MelodiaIntegrationMap`: it reports
`BP_MelodiaJRPGGameMode_C`, a successful PIE start, and
`ABP_Melusina_WaterHair` bound to the character hair component. This is useful
provisional signal for the GameMode/map/hair route, but it is not accepted as fresh
goal evidence until one editor/proxy owner is isolated and Monolith returns.
The newest log tail also records another IntegrationMap PIE at approximately
18:39:54 with the same `BP_MelodiaJRPGGameMode_C` and a live
`ABP_Melusina_WaterHair` binding. This remains provisional and does not prove
Kawaii reset/physics behavior, live capability registration, T3D mutation, or the
player-facing Morning-to-KaleidoNave P0 route.
Two additional IntegrationMap PIE runs at approximately 18:24 included the
`MELUSINA_V2_PROMOTION_SMOKE` marker and clean world teardown; they still do not
prove Kawaii reset/physics behavior or the player-facing Morning → KaleidoNave P0
route.

The latest `python Tools/melodia_rebuild_preflight.py` run found **0 UnrealEditor**,
**0 UnrealEditor-Cmd**, **8 monolith_proxy**, no confirmed
`127.0.0.1:9316` listener, and recent `MODAL_OPEN`/save markers in the newest log.
It reports `safe_to_compile=true` and `safe_for_live_readonly=false`. This is the
authoritative current handoff state; it does not prove Claude's build passed.

Completed or materially advanced:

- T3D safety contract repaired and regression-tested at **42/42**. Committed
  requests now require a unique request ID, matching live pre-edit fingerprint,
  explicit expected node/link delta, compile-zero, and saved re-export proof.
- The gameplay BP registry, materialization models, native-surface audit, and seven
  L1 fixture contracts are documented. WorldChallenge and StateAnchor now bind to
  the existing narrative flag/quest/reward seam through explicit native adapter
  source, without inventing a second save authority.
- A new offline materialization preflight and BuildGraph validation gate are in place.
  It now reports **6/7** templates ready to enter live authoring (TraversalGate,
  Enemy, Encounter, Portal, WorldChallenge, StateAnchor) and **1/7** design-blocked
  (Skill).
- The CI coverage gap is now closed in source: `Tools/run_contract_tests.py` runs
  **17/17** offline suites with a fixed coverage floor and is wired into Echo Gates
  and BuildGraph. It does not require pytest or contact the editor.
- The Skill design gate is now explicit: `UMelodiaSongSkillDefinition` is the
  planned MelodiaCore authority, the current game-module rhythm definition is a
  migration source, chart lanes are authored rather than pitch-derived, and skill
  points/mana/cooldown semantics cannot be silently merged.
- WorldChallenge and StateAnchor now have contract-only first fixtures with stable
  canonical keys, idempotency rules, context restrictions, reload behavior, and
  fail-closed adapter requirements. Their native adapter source is now wired, but
  clean UHT/compile/reflection, save/load, and live fixture evidence remain pending.
- The Kawaii placement probe exists and has an offline/live-history trail, but it is
  not yet a production-ready physics placement BP: clean map save, root physics body
  compatibility, AnimBP playback, PIE reset, and fresh evidence remain open.
- The Infinity Nikki refresh confirms the transferable architecture: abilities are
  bounded mode packages with context restrictions, fallback presentation, evolution
  state, authored compatibility/clipping data, and fixtureable world interactions.
- The delegated JCode/Ollama audit is offline-green but live-unverified. It found a
  Hermes model-contract mismatch, endpoint-name drift, and no generation smoke test;
  these are rebuild follow-ups, not reasons to launch the fleet during the editor
  owner block.
- The delegated Infinity Nikki refresh adds explicit requirements for traversal
  state transitions, bounded temporary-object cleanup, preview/locked/fallback/
  evolution separation, authored Kawaii physics profiles, and a versioned content
  release manifest. The manifest contract is now present offline.
- A shared capability gate contract now covers all seven BP families. It requires
  typed gate requests, deterministic fingerprints, fail-closed missing-provider and
  blocked-context results, and re-evaluation after context, progression, load, travel,
  and reset transitions. Every L1 fixture package explicitly references it. It is
  offline-green and intentionally not live-promoted.
- The two previously design-blocked families now have explicit native adapter
  contracts: WorldChallenge requires one atomic completion/intent/reward transaction,
  and StateAnchor requires a generic stable-key apply transaction distinct from the
  opening-specific anchor. Attempt state is explicitly BP-transient; canonical IDs
  are now checked against dedicated native allowlists. Both remain native-compile
  and live-fixture pending.
- The native-adapter contract audit now keeps gate responsibility explicit: BPs
  carry the shared-gate request/fingerprint and transient attempt state, while the
  narrative subsystem validates canonical IDs and performs atomic state changes.
- The player-facing P0 route now has a machine-readable owner-run contract at
  `specs/p0/core_p0_dream_golden_run.v1.json`; it separates Morning → KaleidoNave
  from the integration proof map and requires fresh-slot, restart, Continue, and
  idempotency observations.
- The first progression fixtures now have a merge-only allowlist seed at
  `specs/progression/melodia_integration_allowlist_seed.v1.json`; it supplies the
  exact challenge, anchor, flag, reward, and quest IDs needed to populate the
  canonical integration config during the live handoff.
- A registry/fixture parity gate now verifies all seven templates, their explicit
  materialization order, fixture parent mapping, and authority boundaries before
  any live BP transaction.
- The roguelike content audit now verifies **26** authored blessing rows and **0**
  burden rows. `WBP_BlessingBurden` and its presentation assets exist, but the typed
  catalog, currency authority, atomic purchase/apply path, and burden content remain
  deliberately unselected and fail closed.
- `Content/Python/audit_kawaii_runtime_readonly.py` is now the supported clean-session
  inspector; it avoids the invalid `static_class` and `node_pos_x` assumptions found in
  the latest editor log and issues no save, compile, map, or PIE operation.
- A fresh offline inventory still finds all seven canonical gameplay BP assets
  absent, seven contract-only fixtures, zero planned asset collisions, and the
  preflight result at 6/7 live-authoring-ready and 1/7 design-blocked.

## Rebuild owner gate (fresh read-only check)

`python Tools/melodia_rebuild_preflight.py` is now the executable handoff check. It
does not terminate processes, launch Unreal, contact Monolith, or mutate project
files. The latest run found **1 UnrealEditor**, **0 UnrealEditor-Cmd**, **8
monolith_proxy**, and no confirmed listener on `127.0.0.1:9316`; therefore both
compile and live-readonly work fail closed. Re-run this gate after Claude's build
handoff and do not infer build success from process absence.

## Why the work is stuck

This is now a live-tool availability/ownership handoff, not a missing design plan.
The editor has exited, but Monolith has several proxy processes and no confirmed
`9316` listener. That prevents independent live graph reads, Blueprint
materialization, save/readback, Kawaii PIE validation, and the disposable T3D
postcondition probe from having an attributable tool owner or trustworthy evidence.
The worktree is also intentionally dirty and `_TASK_QUEUE.md` is owned by another
writer, so it must not be rewritten or used as a coordination surface by this goal.

## Next execution sequence

1. **Resolve the handoff:** obtain Claude's build result, then verify one clean
   UnrealEditor plus one Monolith endpoint before any live transaction. Do not
   terminate processes or launch a competing build from this goal.
2. **Close/rebuild handoff:** verify the surviving editor reaches a clean boundary,
   then run one clean Development compile. Capture the exit code and build log.
3. **Single editor re-entry:** confirm Monolith, query the
   effective GameMode/WorldSettings and integration map, then capture fresh evidence.
4. **Core P0 Dream:** run the owner-controlled Morning → KaleidoNave golden route
   using the integration map only for deterministic persistence checkpoints. Record
   the fresh slot, encounter result, restart boundary, and return path.
5. **T3D proof:** after the golden run, run the disposable probe with a fresh request ID and live
   fingerprint; independently verify the expected graph delta, compile result, and
   saved re-export. Only then permit production authoring.
6. **Kawaii proof:** verify or remove the invalid root-body physics override, save the
   probe in its intended test map, compile/export, run two deterministic PIE resets,
   and record the result.
7. **First BP lanes:** verify the shared capability gate in the clean editor pass,
   close the Skill definition/cooldown/request-id bridge, then materialize the Skill
   DataAsset + thin presentation child and the TraversalGate
   fixture. Promote neither beyond L1 until compile, graph, fixture, reset, and
   evidence-envelope checks pass.
8. **Scale in order:** Enemy + Encounter, then Portal, then WorldChallenge and
   StateAnchor after their adapters/fixtures exist. Add variants from data, never
   from new authority BPs.

## Files added or updated in this work block

- `Tools/melodia_bp_materialization_preflight.py`
- `Tools/test_melodia_bp_materialization_preflight.py`
- `Tools/run_contract_tests.py`
- `Tools/test_melodia_native_adapter_contract.py`
- `Tools/test_melodia_bp_registry_contract.py`
- `specs/roguelike/melodia_blessing_burden_contract.v1.json`
- `Tools/test_melodia_blessing_burden_contract.py`
- `Content/Python/audit_kawaii_runtime_readonly.py`
- `Content/Python/audit_roguelike_generator_readonly.py`
- `Docs/Handoffs/PROCEDURAL_DUNGEON_REACTIVATION_2026-08-14.md`
- `Tools/test_mcp_registration.py`
- `Docs/Handoffs/JCODE_OLLAMA_INTEGRATION_AUDIT_2026-08-14.md`
- `.github/workflows/echo_gates.yml`
- `.gitignore`
- `specs/blueprints/melodia_gameplay_bp_kit.v1.json`
- `specs/blueprints/fixtures/first_resonance_world_challenge.v1.json`
- `specs/blueprints/fixtures/first_dream_progress_anchor.v1.json`
- `specs/blueprints/fixtures/single_stock_enemy.v1.json`
- `specs/blueprints/fixtures/repeatable_first_dream_encounter.v1.json`
- `specs/blueprints/fixtures/locked_traversal_portal.v1.json`
- `Tools/test_melodia_content_fixtures.py`
- `specs/content/melodia_content_release_manifest.v1.json`
- `specs/capability/melodia_capability_gate.v1.json`
- `specs/progression/melodia_world_challenge_adapter.v1.json`
- `specs/progression/melodia_state_anchor_adapter.v1.json`
- `specs/progression/melodia_integration_allowlist_seed.v1.json`
- `specs/p0/core_p0_dream_golden_run.v1.json`
- `Tools/test_evidence_envelope.py`
- `BuildGraph/MelodiaBuildGraph.xml`
- `Docs/Plans/MELODIA_INFINITY_NIKKI_PIPELINE_UPDATE_2026-08-14.md`
- `Docs/Plans/LONG_TERM_GAMEPLAY_BP_T3D_PLAN_2026-08-14.md`
- `Docs/Research/INFINITY_NIKKI_PIPELINES_AND_PROJECT_UPDATES_2026-08-14.md`
- `Docs/Handoffs/BP_MATERIALIZATION_CONTRACT_2026-08-14.md`
- `Tools/melodia_rebuild_preflight.py`

The current goal remains active. The next meaningful transition is from “editor
owner unresolved” to “one clean editor + Monolith read-only evidence,” not bulk BP
creation.
