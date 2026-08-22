# Resonant World Quantum Handoff — 2026-08-22

## Boundary

Quantum is a low-frequency world-preparation chooser, not a voxel generator, UI
clock, traversal loop, input grader, or reward authority.

The source implementation is:

`Content/Python/quantum/resonant_movement_ranker.py`

with the Q# operation:

`Content/Python/quantum/qsharp_world_movement_ranker.qs`

## Runtime contract

1. Build a bounded set of authored movement candidates.
2. Compute and retain the deterministic classical baseline.
3. Request `qsharp-simulator` only for exactly two candidates.
4. Fall back to `classical-baseline` when Q# is unavailable or times out.
5. Persist winner, baseline winner, backend, and trace ID before world apply.
6. Pass the resolved movement into the authored PCG binding.

The current environment reports `qsharp_available=false`, so the generated
passage artifacts request the Q# path but resolve honestly to the classical
baseline. No pseudo-quantum randomness is substituted.

## MCP verification calls

```json
{"name":"melodia_resonant_world_compile_passage","arguments":{"seed":3900,"movement_id":"petal_cantata"}}
{"name":"melodia_resonant_world_get_handoff","arguments":{"target":"quantum"}}
{"name":"melodia_resonant_world_validate","arguments":{}}
```

## Current status

The two-candidate contract, Q# source, classical fallback, replay fields, and
offline tests are present. Q# SDK promotion and live editor/runtime evidence are
environment gates, not reasons to fabricate a quantum result.
