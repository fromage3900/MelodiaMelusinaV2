# Melodia Retopo Recipe (pre-intake) — 2026-09-03

**Recommended route: Quadriflow-first + Smart Project, calibrated Voxel fallback.**
One script: `Tools/Houdini/sea_above_reef/garment_retopo_preintake.py`
(schema `melodia.garment_retopo_preintake.v1`, seed `20260902`).
It runs BEFORE `garment_intake_prep.py`; output FBX drops into
`Imports/GarmentIntake/` for canonical intake.

## Exact command

```bat
"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup ^
  -noaudio --python Tools/Houdini/sea_above_reef/garment_retopo_preintake.py ^
  -- --source Imports/GarmentIntake/AntiqueDoll_Dress_fbx_thick.fbx ^
     --out AntiqueDoll_Dress_retopo.fbx --target_faces 9000
```

`--outdir <dir>` redirects output to scratch for testing (never overwrite
canonical intake FBX in place). `--target_faces` default `9000`.

## Settings (fixed in script)

| Stage | Op / params |
|---|---|
| Import | FBX `-Y/Z`, join, `transform_apply` L/R/S |
| Clean | bmesh `remove_doubles dist=0.0001`, delete loose verts, recalc normals outside |
| Primary | `quadriflow_remesh mode=FACES target_faces=<N> seed=20260902 preserve_sharp+boundary+attributes smooth_normals` |
| Fallback (auto, on Quadriflow no-op) | Voxel remesh, size iterated from `maxdim/60` to land polys in `[0.7N, 1.3N]` (≤5 tries); manifest `engine=voxel_fallback` |
| UV | `smart_project angle_limit=66 island_margin=0.02 correct_aspect` |
| Export | FBX `FACE` smoothing, `-Y/Z`, + `<out>.retopo_manifest.json` (seed+sha256) |

## Why the fallback exists

Quadriflow takes only manifold input. Market `_thick` meshes are refused
headless (`QuadriFlow: needs manifold…` warning, 0.0 s no-op) — verified on
AntiqueDoll with weld on/off and +Solidify (diag: 5118 multi-face edges,
boundary rims). Closed manifold meshes take the true Quadriflow path; `_thick`
class takes the voxel fallback. Both converge to ~N quads.

## Test evidence (scratch copy, 2026-09-03, Blender 5.2.1 `--factory-startup`)

AntiqueDoll dress, `target_faces=9000`:

- Raw import 180,895 v / 316,912 polys → cleaned 143,913 v / 296,270 polys
- **Out: 9,168 v / 9,166 polys / quad_ratio 1.0**, all 20 material slots kept
- Engine `voxel_fallback` (size 0.050931), total **2.6 s** (voxel 0.7 s)
- Output FBX sha256 `18e982fb…3f766a` (scratch `…/AntiqueDoll_Dress_retopo_TEST4.fbx`)

## Next

Feed the retopo FBX to `garment_intake_prep.py --source … --slot … --descriptor …`
(Substance OBJ + UE FBX + intake manifest as usual).
