# Resonant World Quantum Provenance

Date: 2026-08-22
Repository: `C:\EnvironmentPortfolio\BS_GodFile`

## Design decision

Quantum computation is a low-frequency authoring selector, not the world
generator. The long-term world remains deterministic from its seed, chunk
coordinate, authored movement library, and persisted sparse edits. A quantum
result may select which of two already-authored movement ecologies is prepared
next; it never invents an asset path or chooses a voxel during play.

The current world boundary is:

```text
asset atlas -> classical feature extraction -> exactly two movement candidates
           -> optional Q# measurement -> persisted winner/baseline/trace
           -> authored PCG/materialization adapter -> runtime traversal authority
```

## Q# setup

`Content/Python/quantum/qsharp_world_movement_ranker.qs` allocates one qubit,
computes a bounded angle from two classical scores, applies `Ry`, measures in
the computational basis, and resets the qubit. For scores `a` and `b`, the
construction uses:

```text
theta = 2 atan2(sqrt(b), sqrt(a))
P(Zero) = a / (a + b)
P(One)  = b / (a + b)
```

The Python result records these probabilities beside the measurement. This is
an honest weighted two-candidate draw, not a claim that Q# solved the entire
procedural-generation problem. Q# measurement and reset semantics are
documented by Microsoft's [Q# overview](https://learn.microsoft.com/en-us/azure/quantum/qsharp-overview)
and [Measure reference](https://learn.microsoft.com/en-us/qsharp/api/qsharp-lang/std.intrinsic/measure).

## Provenance and replay

`resonant_movement_ranker.py` v2 embeds, per candidate:

- bounded objective features and the resulting classical score;
- atlas movement ID, asset-family counts, missing-family evidence, and the
  authored quantum objective;
- the requested backend and actual backend;
- the classical baseline winner; and
- a measurement log for every pairwise Q# draw.

The trace fingerprint includes candidate IDs, features, and provenance. A
changed atlas therefore changes the replay trace even when the seed and
movement IDs are unchanged. Persist the winner, baseline winner, backend,
trace, candidate provenance, and measurement log before any authored PCG apply.

## N>2 experiment

The world composer remains exactly two candidates because that is the smallest
auditable Q# kernel and keeps the runtime contract simple. For research and
atlas comparison, ranker v2 can compose the same kernel into a fixed-order
pairwise tournament for N>2 candidates. This is deliberately labeled
`qsharp-tournament`; it is not a claim of one N-state quantum optimization.
Any unavailable provider or failed measurement falls back to the complete
classical baseline rather than mixing partial quantum output into gameplay.

This follows the architecture of a classical application orchestrating a
quantum job, while keeping the handoff observable and replayable. Microsoft's
[quantum/classical integration guidance](https://learn.microsoft.com/en-us/azure/architecture/example-scenario/quantum/quantum-computing-integration-with-classical-apps)
and [resource-estimator documentation](https://learn.microsoft.com/en-us/azure/quantum/overview-resources-estimator)
make the same application/quantum/hardware boundary useful for future cost
studies. Quantum procedural-generation research is an inspiration for the
constraint framing, not runtime evidence: see [A quantum procedure for map
generation](https://arxiv.org/abs/2005.10327) and [Procedural Generation and
Games at the Dawn of Fault Tolerant Quantum Computing](https://arxiv.org/abs/2508.09683).

## Safety boundary

The selector is not allowed to:

- select individual voxels or PCG points;
- poll per frame or drive traversal;
- grade rhythm input or decide combat damage;
- grant wardrobe capability, currency, or rewards;
- create a second save authority; or
- mutate `L_WP_SakuraDream`, Headquarters BFG, gameplay maps, the webfront, or
  the isolated `/Game/_PROJECT/Levels/RenderTests/` lookdev namespace.

## Verification

```powershell
python -m unittest Content/Python/quantum/test_resonant_movement_ranker.py -v
python -B Content/Python/resonant_world_score.py --seed 3900 --movement petal_cantata --chunk-x 0 --chunk-y 0
python -B Tools/test_melodia_mcp.py
```

The current environment must report the actual backend. If Q# is unavailable,
the honest result is `classical-baseline` with `qsharp_available=false`; no
quantum-advantage claim should be made from the deterministic fallback.
