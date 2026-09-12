# Mesh-scale repair — Part A progress, 2026-08-02

18 of 29 broken-scale meshes repaired via `BuildScale3D = 100`. **No level was modified or saved.**

## The finding that changed the risk assessment

The plan assumed the 29 meshes were hand-placed across ~100 World Partition external-actor packages,
requiring a world-size-preserving migration of every placement.

**They are not hand-placed.** Inspecting `L_Template` — the level with the most references — found:

| | |
|---|---:|
| PCG-spawned entries (`InstancedStaticMeshComponent`) | 11 (82 instances) |
| Hand-placed actors (plain `StaticMeshComponent`) | **0** |

The asset-registry references come from **PCG volumes that spawned those meshes**, not from artists
placing them. PCG regenerates from the graph, so corrected meshes simply come back at the right size.
The migration step is unnecessary wherever this holds — and it held everywhere checked so far.

**Still verify per level before fixing a mesh.** The check is cheap: count plain `StaticMeshComponent`
users versus `InstancedStaticMeshComponent` users. Only plain ones need migrating.

## Repaired (18)

Each landed on its intended real-world size, which is the strongest confirmation the factor is right:

| Mesh | Before (uu) | After (uu) |
|---|---|---|
| `SM_Block_Cube_1` | 1 × 1 × 1 | **100 × 100 × 100** — a 1 m cube, exactly as named |
| `SM_Block_Wall_4x3` | 4 × 0.3 × 3 | **400 × 30 × 300** — a 4 m × 3 m wall, exactly as named |
| `SM_Block_Pillar_03` / `SM_Greybox_Pillar_03` | 0.3 × 0.3 × 3 | 30 × 30 × 300 |
| `SM_corridor` | 24 × 24 × 3.5 | 2485 × 2538 × 399 |
| `SM_venetianbridge` | 11 × 1.2 × 3.3 | 1108 × 160 × 349 |
| `SM_PENROSE1` | 3.7 × 3.7 × 6 | 387 × 385 × 608 |
| `SM_ceilingsquare` | 5 × 5 × 0.14 | 500 × 500 × 14 |
| `Stairs_001` | 2.5 × 3.6 × 0.8 | 252 × 363 × 84 |
| `SM_Cube_001/002/004/005/006/007`, `SM_wallshort_001`, `SM_wallhi_018`, `SM_Door_Swing_Annotation` | — | all ×100 |

`SM_Block_Cube_1` → exactly 100³ and `SM_Block_Wall_4x3` → exactly 400×30×300 is the proof: the
names encode metres, and after the fix the geometry matches the names.

Full before/after table: `Content/Python/../scratchpad/mesh_fix_all.json` (also inlined above).

## Two false positives — deliberately NOT changed

The original audit flagged these by size threshold alone. They are real props at plausible sizes:

- `SM_GlassBottle_Object1715` — 6 × 4 × **12 uu**. That is a 12 cm bottle. Correct.
- `SM_LanternGlass` — 28 × 25 × 25 uu. A 28 cm lantern. Correct.

Scaling either by 100 would have produced a 12-metre bottle. **The "max dimension < 30 uu" heuristic
is not sufficient on its own** — small props are legitimately small. Judge by intended real-world
size, not by a threshold.

## Remaining (3 meshes) — blocked on owner approval

| Mesh | Levels | Why blocked |
|---|---|---|
| `SM_Greybox_Column_05` | `L_MelusinaMorning`, `L_Melodia_Dreamstate`, `DistanceFieldBlendLab` | `L_MelusinaMorning` is Red — ask first |
| `SM_Sakura_PetalProxy_Sphere` | `L_SakuraPath` | human-owned art direction |
| `SM_LanternGlass` | `L_CelestialPond` | not broken — see above |

Likely these are PCG-spawned too, in which case the fix is as free as the rest. **Run the
hand-placement check on those three levels before deciding** — it is read-only and settles it.

## Also still pending

`SM_Greybox_Cube_1m` (10 graphs), `SM_Greybox_Wall_4x3` (6), `SM_wallshort` (4), `SM_wallhi_015`,
`SM_wallhi_016`, `SM_SurrealRoof_HIP_002` — all in `L_WP_BaroqueGrotto` / `DistanceFieldBlendLab`.
Safe by the same reasoning, just not yet done. `SM_Greybox_Cube_1m` measures 1 × 1 × 1 while its name
says one metre, so it is the clearest remaining case.

## Method (repeat for the rest)

```python
bs = unreal.EditorStaticMeshLibrary.get_lod_build_settings(mesh, 0)
cur = bs.get_editor_property('build_scale3d')
bs.set_editor_property('build_scale3d', unreal.Vector(cur.x*100, cur.y*100, cur.z*100))
unreal.EditorStaticMeshLibrary.set_lod_build_settings(mesh, 0, bs)
unreal.EditorAssetLibrary.save_asset(path)
```

Multiply the **existing** build scale rather than assigning 100 outright, so a mesh that already
carries a non-default scale is not silently reset. Re-load and re-measure bounds to verify; the
functions are deprecated in 5.8 but still work (Static Mesh Editor Subsystem is the modern route).
