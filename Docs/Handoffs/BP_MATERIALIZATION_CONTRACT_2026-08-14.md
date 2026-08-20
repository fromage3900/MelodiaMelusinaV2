# Melodia BP Materialization Contract

**Date:** 2026-08-14  
**Status:** Offline contract ready; editor-closed compile and live graph proof pending  
**Scope:** MelodiaIntegrationMap gameplay expansion after the Core P0 Dream slice

## What changed

The gameplay kit now records an explicit materialization model for each planned
surface in `specs/blueprints/melodia_gameplay_bp_kit.v1.json`:

| Surface | Correct artifact model | Native authority | Current gate |
| --- | --- | --- | --- |
| Skill | `UMelodiaRhythmSkillDefinition` DataAsset + thin stock presentation child | `UMelodiaBattleSession` / `UMelodiaRhythmCombatSubsystem` | Definition bridge, cooldown, request-id, and stock-parent reflection |
| Enemy | DataAsset + BP child | `AMelodiaEnemyBase` | Parent/CDO/component reflection and stock encounter fixture |
| Encounter | BP child of stock trigger | `AMelodiaEncounterTrigger` | Battle handoff and reset/idempotency evidence |
| Portal | BP child of travel shell | `AMelodiaTravelInteractionPortal` | Allowlisted destination, save-before-travel, input restoration |
| Traversal gate | Actor BP with presentation only | `UMelodiaTraversalComponent` | Capability-provider compile/live evidence and context matrix |
| World challenge | Actor BP + definition data | `UMelodiaNarrativeSubsystem` | Source-wired atomic adapter; clean compile and idempotent reward/state fixture |
| State anchor | Actor BP + canonical narrative state | Narrative subsystem/save contract | Source-wired generic stable-key adapter; clean compile and replay-safe load fixture |

`UMelodiaRhythmSkillDefinition` is a final `UPrimaryDataAsset`; it must not be
treated as a Blueprint parent. The skill contract therefore remains blocked until
the definition bridge closes the split between stock recipes and rhythm definitions.

The battle-interaction and travel-portal shells are now source-level Blueprint
extensible. Children may add presentation and authored policy, but may not own
battle execution, travel routing, save mutation, or a second traversal state machine.

Progression adapters follow the same boundary: the BP owns transient attempt state
and must forward an allowed shared-gate result with its `GateRequestId` and
`EvaluationFingerprint`; the narrative subsystem owns canonical ID allowlists and
atomic completion/apply mutation. The current native adapter signatures do not claim
to re-evaluate the gate registry until that registry is compiled and reflected.

The T3D transaction gate now requires a non-placeholder request ID, a matching
live pre-edit fingerprint in both the CLI and request envelope, and an explicit
`expected_delta` proving that newly requested nodes or links were absent before
the mutation and present afterward. This gate must be live-proven on the disposable
probe before it is used for production BP authoring.

## Verified in this closed-editor window

- `python Tools/test_melodia_bp_readiness.py` passed.
- `python Tools/test_melodia_content_fixtures.py` passed.
- `python Tools/test_melodia_bp_materialization_preflight.py` passed: 7 templates,
  no assets created, 6 specified for live authoring, 1 held at a design gate.
- `python Tools/test_melodia_native_adapter_contract.py` passed: the progression
  specs agree with the reflected native method names, BP-local attempt ownership,
  and dedicated challenge/anchor allowlists.
- `specs/progression/melodia_integration_allowlist_seed.v1.json` is the exact
  merge-only source for the first challenge/anchor config entries; it does not
  modify the existing `.uasset` while the editor owner is unresolved.
- `python Tools/run_contract_tests.py` passes **17/17** offline suites; the
  additional registry/fixture parity gate prevents parent/order/authority drift.
- `python Tools/test_t3d_safe_wire.py` passed: **42/42**.
- JSON contracts parse and the changed files pass targeted `git diff --check`.
- No canonical gameplay template `.uasset` has been fabricated.

Current offline inventory remains:

- 7 canonical template assets missing on disk.
- 7 contract-only fixtures at L1.
- Kawaii placement probe present at L0; live compile/PIE/reset evidence pending.
- The explicit live materialization order is `Skill -> TraversalGate -> Enemy ->
  Encounter -> Portal -> WorldChallenge -> StateAnchor`.
- Live evidence unavailable until the current build handoff is complete and
  Monolith returns on `127.0.0.1:9316`; the latest owner check finds no editor but
  also no usable Monolith endpoint.

## Next live sequence

1. Resolve the current editor/UAT owner. Do not kill the responding editor or launch
   a second editor. Once Claude's build lane reaches a clean boundary, run one
   Development compile with no competing process holding the project.
2. Relaunch one clean editor, verify Monolith, then compile/export the native
   traversal capability registry and the two extensible shell headers.
3. Query the effective GameMode and MelodiaIntegrationMap route; capture parent/CDO,
   components, graph, compile, and map-reachability evidence.
4. Materialize only the first two fixture lanes: the skill DataAsset/stock
   presentation path after its bridge gate, and the Hover Gate actor BP.
5. Run failure/reset/idempotency checks and emit fresh evidence envelopes before
   creating Enemy, Encounter, Portal, WorldChallenge, or StateAnchor children.
6. Reconcile the Core P0 Dream ledger after one clean golden pass; then promote the
   reusable templates and add content variants from data.

Infinity Nikki remains a structural reference only: ability-driven exploration,
context restrictions, preview/fallback presentation, evolution/fusion, and authored
scene interactions. Melodia keeps its own musical progression, no gacha/economy,
and one-authority-per-domain rule. See
`Docs/Research/INFINITY_NIKKI_PIPELINES_AND_PROJECT_UPDATES_2026-08-14.md` and
`Docs/Plans/MELODIA_INFINITY_NIKKI_PIPELINE_UPDATE_2026-08-14.md`.
