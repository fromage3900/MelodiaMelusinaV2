# Integrated PCG Water Gameplay T3D Manifest

This is the Blueprint-wiring lane for the isolated Crystal Harp water proof.
Native C++ owns water state, platform motion, buoyancy, save data, and the
single clock/reactivity/audio authorities. T3D only connects live Blueprint
controllers/components to those reflected APIs.

| ID | Live-path target | Reflected operation | Required verification |
|---|---|---|---|
| `hero_host_begin_play` | Crystal Harp graph host controller | `UMelodiaPCGWaterGameplayBridgeComponent::RebindToHost` and `UMelodiaWaterGameplayControllerComponent::RegisterConfiguredNode` | host owns bridge; `OnNoteJudged` is bound once |
| `hero_host_end_play` | same host EndPlay path | `UMelodiaPCGWaterGameplayBridgeComponent::UnregisterWaterBindings` | logical state retained; world bindings removed |
| `note_judged_resonance` | host `OnNoteJudged` dispatcher | bridge `HandleNoteJudged` -> typed `FMelodiaWaterOperationRequest` | no direct MPC write; subsystem state revision increments |
| `pattern_completed_puzzle` | host `OnPatternCompleted` dispatcher | bridge `HandlePatternCompleted` | `OnPuzzleSolved` fires once; optional route opens |
| `controller_state_fanout` | water controller event graph | `HandleWaterStateChanged` | bounded fluid telemetry reaches existing interaction bus |
| `device_interaction` | valve/pump/drain/gate anchors | controller `InteractWithDevice` / `SetRouteOpen` | invalid IDs reject; route state is deterministic |
| `platform_route_activation` | moving platform controller | `AMelodiaWaterPlatform` + motion component state | gate requirement and pressure/flow response are visible |
| `platform_state_update` | platform tick/controller | `UMelodiaWaterGameplaySubsystem::UpdatePlatformState` | progress/dock/activation only; no raw physics save |
| `buoyancy_debug_telemetry` | proof-map debug controller | buoyancy `HasAuthoritativeWaterSample` and bounded impact events | no force without a native Water Body sample |
| `save_load_rebind` | canonical narrative save adapter | water snapshot capture/restore | logical route/puzzle state restores; physics velocity resets |
| `runtime_diagnostic` | one-shot proof-map diagnostic | `GetNodeState`, `GetPressureForNode`, `GetResolvedWaterFlow`, `GetPlatformMotionState` | one recorded PIE sequence, no duplicate cluster |

## Injection protocol

For each target, the injector must:

1. Resolve the Blueprint on the live editor path and export the current graph.
2. Record the before fingerprint and reject an existing generated cluster.
3. Validate the parameterized T3D payload with `validate_nodes_t3d`.
4. Inject one cluster atomically with `inject_nodes_t3d`.
5. Compile immediately and stop on any compile error.
6. Assert expected nodes and links, then record the after fingerprint.
7. Save only after the structural assertion succeeds.
8. Write target, payload hash, expected nodes, before/after fingerprints, and
   rollback export to the injection report.

The checked-in `Tools/melodia_water_gameplay_t3d.py` implements this protocol
around Monolith. It intentionally requires an explicit live Blueprint path;
it does not guess production assets or mutate a graph while the editor is
unavailable.

