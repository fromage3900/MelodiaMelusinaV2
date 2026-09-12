# Spline carve — FIXED, 2026-08-02

Scatter now pulls away from spline paths. Verified positionally, not just by count.

## Result

`PCG_Nikki_PhyllotaxisGarden_Walkable`, carved against a 4-point spline crossing the garden:

| Corridor half-width | Survivors of 160 | Closest survivor to path | Inside corridor |
|---:|---:|---:|---:|
| 1200 | 53 | 1203 uu | **0** |
| 700 | 97 | 707 uu | **0** |

The threshold is a real dial — survivors track it exactly, and nothing leaks. `L_FallenMoon` saved
with a live demo: `PCG_Demo_PathSpline` (a `BP_InstanceOnSpline` tagged `PCG_Spline`) and
`PCG_Demo_WalkableGarden`. 702 PCG instances total in the level.

## What was actually wrong

`PCGDifference` was abandoned, not repaired. It depends on the spatial-data semantics of whatever
`PCGDataFromActor` emits, and that proved opaque — it culled nothing across two actor classes
(`StaticMeshActor`, `BlockingVolume`) and three source modes, with verified genuine overlap.

One real bug was found and fixed along the way: **`actor_filter` defaults to `Self`**, so a
by-tag search never scans the world at all. `PCGGetSpline` has the same default and the same trap.
That alone was not sufficient to make Difference work.

## The replacement — numeric, not spatial

```
CreateShapes ──> PCGExSampleNearestSpline ──> PCGAttributeFiltering ──> TransformPoints ──> Spawner
                          ▲                      (InsideFilter)
   PCGGetSpline ──────────┘
   ALL_WORLD_ACTORS + ByTag "PCG_Spline"      GREATER than corridor width
```

`PCGExSampleNearestSpline` writes a per-point distance (`PathDist`); a plain attribute filter keeps
points beyond the corridor. This carves to the spline's **actual ribbon**, not an actor's bounding
box, and corridor width is one tunable number instead of a volume someone places by hand. The
distance attribute is also exactly what a feathered falloff needs later.

## Four API traps, each of which silently produced zero

1. **`actor_filter` defaults to `Self`.** Set `ALL_WORLD_ACTORS` or the tag search finds nothing.
2. **`PCGAttributePropertyInputSelector` must be built from text.**
   `sel.set_attribute_name("PathDist")` **returns `True` and does nothing** — the selection stays
   `PROPERTY($Density)`. Only `sel.import_text("PCGBegin(PathDist)PCGEnd")` flips it to `ATTRIBUTE`.
   Bare `"PathDist"` yields `@Last`, which is also wrong.
3. **PCGEx shape fitting is uniform by default.** `scale_to_fit_mode: Uniform` + `scale_to_fit: Min`
   means a flattened `cell_size.Z` shrinks the *whole* shape uniformly — a 4000 uu garden collapsed
   to a 20 uu ball. Needs `INDIVIDUAL` + per-axis `FILL`. The base graph had this; the walkable fork
   did not, and that mismatch cost real time.
4. **`max_range` is a struct**, set `.constant`. A very large value makes every point sample
   successfully so the *filter* decides culling, not the sampler.

## Diagnostic that settled it

Bisect, in this order — each step is one generate plus one separate-call count:

1. **Does spline data reach PCG at all?** `PCGGetSpline` → `PCGSplineSampler` → `StaticMeshSpawner`
   in a probe graph. 28 instances appeared along the spline: **the actor query works.** This is the
   step that was never run on the Difference chain, and it would have redirected the whole effort.
2. **Bypass the filter** — sampler straight to `TransformPoints`. 160 through, so the sampler is fine
   and the filter is the problem.
3. **Threshold −1 with `GREATER`** — all 160 pass, so `PathDist` resolves. Therefore the earlier zero
   meant every value sat below the threshold.
4. **Inspect positions, not counts.** That is what exposed the collapsed 20 uu ball. A count alone
   said "160 instances, healthy"; the positions said the garden was gone.

**Rule: when a filter yields zero, check whether the upstream data still has the shape you think it
has.** Three separate wrong conclusions this session came from trusting a count over a position.

## Reusable helper — rewritten

`pcg_graph_builder._wire_exclusion_filter(graph, prev, prev_pin, corridor_cm=700.0)` now builds this
chain and returns `{"node": filter, "pin": "InsideFilter"}`. Verified end-to-end on a fresh graph:
169 → 102 instances, closest survivor 701 uu, zero inside.

The old implementation could never have worked, and every caller believed it had:

- set `actor_selector = unreal.PCGActorSelector.ByTag` — but `actor_selector` is a *struct*
  (`actor_filter` / `actor_selection` / `actor_selection_tag`);
- set a property `actor_tag` that does not exist;
- wired Difference's subtract input to `"Subtract"`; the real pin is `"Differences"`;
- preferred `PCGFilterByTag`, which filters **data by tag** and has nothing to do with proximity;
- swallowed every failure in `except: return False`, so `wire_scatter_chain` recorded
  `pcgex_exclusion: True` while nothing was culled.

Callers (`setup_pcg_greybox.py`, `setup_pcg_universal.py`, `build_pcg_cosmic_orrery.py`) need no
change — they already use the returned pin name. **Any graph previously built with
`apply_exclusion=True` has a non-functional filter and should be rebuilt.**

## Still open

- `PCG_FallenMoon_Mandala` generates at **Z 5755**, ~57 m above the level.
- `VolumeSampler`-sourced graphs still emit zero project-wide.
- Feathered falloff (use `PathDist` to drive density rather than a hard cut) — the attribute is
  already there, this is a small follow-up.
- The hero "Infinite Nave" graph is planned but not built; it routes around exclusion via geometric
  clearance, so it never depended on this fix.

Two probe graphs are parked in `/Game/EnvSandbox/PCG/_Dev/`: `PCG_Probe_SplineReach` and
`PCG_Probe_ExclusionHelper`. Left in place deliberately — deleting freshly-created assets mid-session
trips an editor Ensure (`ObjectTools.cpp:4043`).
