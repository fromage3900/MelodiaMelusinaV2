# PCG walkability pass — 2026-08-01

## The headline finding: `coordinate_space` defaults to WORLD

`PCGCreatePointsGrid.coordinate_space` defaults to **`WORLD`**, not local. A graph using it
generates around the **world origin and ignores the volume that owns it entirely.** Moving the
volume does nothing.

This was masked in `L_FallenMoon` because the first volume placed happened to sit at (0,0,0). It
looked correct. The other five were stacked invisibly on top of it.

### Correction to the earlier claim

`PCG_WORKING_STATE_2026-08-01.md` reported "6 PCG volumes, 605 instances, spaced 12000 uu apart."
The count was right; **the spacing was not.** Measured scatter centroid vs. owning volume location:

| Volume | Volume at | Scatter centre was | Offset |
|---|---|---|---:|
| DreamWalls | (0, 0) | (0, 0) | 0 |
| SpiralAscent | (12000, 0) | (0, 0) | **12000** |
| Phyllotaxis | (0, 12000) | (0, 0) | **12000** |
| Mandala | (12000, 12000) | (0, 0) | **16970** |
| PenroseRing | (−12000, 0) | (0, 0) | **12000** |
| SteppedColonnade | (0, −12000) | (0, 0) | **12000** |

Five of six were piled at the origin. Any render framed on a volume other than DreamWalls would
have been empty, and the origin was six graphs deep in overlapping geometry.

### Fix applied

`coordinate_space = LOCAL_COMPONENT` on the source node of all six graphs, all saved:

`PCG_DreamWalls` · `PCG_Escher_SpiralAscent` (two nodes) · `PCG_Nikki_PhyllotaxisGarden` ·
`PCG_Nikki_MandalaBloom` · `PCG_Escher_PenroseRing` · `PCG_Escher_SteppedColonnade`

Re-verified after regenerate — **605 instances, 0 detached, max offset 1 uu.** `L_FallenMoon` saved.

**Rule: every new graph must set `coordinate_space = LOCAL_COMPONENT` explicitly.** The default is
wrong for anything volume-placed, and it fails silently.

## Walkability: exclusion is built but NOT yet proven

`PCG_Nikki_PhyllotaxisGarden_Walkable` (Sakura) is built and saved:

```
CreatePointsGrid (LOCAL_COMPONENT) --Seeds--> PCGExCreateShapes --> PCGDifference --> TransformPoints --> StaticMeshSpawner
CreateShapeFiblat --Shape Builder-->  ^                               ^
PCGDataFromActor (ALL_WORLD_ACTORS, BY_TAG "PCG_Exclude") ------------+ Differences
```

All 7 nodes wired, verified edge-by-edge. It emits 160 instances.

**The carve does not work yet.** With a `BlockingVolume` tagged `PCG_Exclude` overlapping the
garden, 8 instances still sit inside the corridor footprint. Configurations ruled out:

| Tried | Result |
|---|---|
| `actor_filter = SELF` (the default) | never scans the world — **a real bug, fixed to `ALL_WORLD_ACTORS`** |
| `mode = PARSE_ACTOR_COMPONENTS` | no carve |
| `mode = GET_SINGLE_POINT` | no carve |
| `difference mode = INFERRED` / `DISCRETE` | no carve |
| StaticMeshActor vs BlockingVolume as the exclusion actor | no carve either way |

Note the first three tests were run **before** the coordinate-space fix, i.e. while the garden was
at the origin and the corridor at Y=24000 — **there was no overlap, so those results are void.**
Only the last configuration was tested with genuine overlap. Re-test `PARSE_ACTOR_COMPONENTS` and
`INFERRED` now that the geometry actually intersects before concluding anything about them.

Regeneration itself was proven live (changing Fiblat resolution 160 → 60 changed the count to
exactly 60), so this is not a stale-cache artifact.

## Second issue: Fiblat is spherical

`CreateShapeFiblat` is a Fibonacci lattice **on a sphere** — the garden's Z spans ±1980 uu. Setting
`default_extents.Z = 0` did not flatten it. For a *walkable* phyllotaxis garden this needs either a
flat golden-angle disc instead of Fiblat, or a Z-flattening step after the shape. Unresolved.

## Open question for the owner

The exclusion is currently driven by **actor tag `PCG_Exclude`**. You mentioned
`BP_InstanceOnSpline` / `BP_InstanceOnSpline_02` and `BP_PathSplineProvider` for paths. Which should
drive the carve? That choice determines the wiring:

- **Tag a spline actor `PCG_Exclude`** — simplest, works with what is built, but carves to the
  spline's *bounds*, not its ribbon.
- **`BP_PathSplineProvider` → spline data → `PCGSplineSampler` → Difference** — carves an actual
  path corridor of controllable width. More nodes, correct result.

The second is almost certainly what "a genuine pass on walkability" means, but it is a different
graph shape, so I stopped rather than guess.

## Test hygiene

Probe actors `PCG_T_Walkable`, `PCG_T_WalkCorridor`, `PCG_T_WalkCorridorVol` were destroyed.
`L_FallenMoon` contains only the six intended `PCG_FallenMoon_*` volumes.
