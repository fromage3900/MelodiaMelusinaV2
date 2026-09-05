# Verify — Retopo recipe quad-dominant route (2026-09-04)

**Gate:** **PASS** — pre-intake route restored + headless verified on two dense MD triangulations, quad_ratio 1.0, slots intact.

**Recipe:** `Docs/Pipelines/MELODIA_RETOPO_RECIPE_2026-09-03.md` (seed **20260902**) + script `Tools/Houdini/sea_above_reef/garment_retopo_preintake.py` (schema `melodia.garment_retopo_preintake.v1`). Runs **before** `garment_intake_prep.py`; output FBX → `Imports/GarmentIntake/` for canonical intake.

**Files (re-read from disk):**

| file | bytes | sha12 | note |
|---|---|---|---|
| `Docs/Pipelines/MELODIA_RETOPO_RECIPE_2026-09-03.md` | 2500 | `63ed99f3cc20` | recipe doc, 52 lines |
| `Tools/Houdini/sea_above_reef/garment_retopo_preintake.py` | 8671 | `548432ab78fa` | 219 lines, quadriflow+voxel+smart UV |

Restored from `ba322abc` (branch `cleanup/integrate-batches-2026-09-03` had the recipe; `merge/unify-histories` had dropped it — same divergence that dropped the garment GN lane on 2026-09-03). Current branch now byte-identical to ba322abc for these two files.

**Route (fixed in script, re-read):**

| Stage | Op / params |
|---|---|
| Import | FBX `-Y/Z` or OBJ, join, `transform_apply` L/R/S |
| Clean | bmesh `remove_doubles dist=0.0001`, delete loose verts, `recalc_face_normals` outside |
| Primary | `quadriflow_remesh mode=FACES target_faces=N seed=20260902 preserve_sharp+boundary+attributes smooth_normals` |
| Fallback (auto, on Quadriflow no-op) | Voxel remesh, size iterated from `maxdim/60` until polys ∈ `[0.7N, 1.3N]` (≤5 tries); manifest `engine=voxel_fallback` |
| UV | `smart_project angle_limit=66 island_margin=0.02 correct_aspect` |
| Export | FBX `FACE` smoothing, `-Y/Z`, + `<out>.retopo_manifest.json` (seed+sha256) |

**Why fallback:** Quadriflow refuses non-manifold market `_thick` meshes headless (`QuadriFlow: needs manifold…` warning, 0.0 s no-op) — verified on AntiqueDoll with weld on/off + Solidify, ~5k multi-face edges/boundary rims. Closed manifold meshes take true Quadriflow; `_thick` class deterministically takes voxel fallback. Both converge to ~N quads (re-read below).

**Headless probes (Blender 5.2.1 LTS `9e2066aef7ef`, `--factory-startup --background`, scratch `C:/Users/froma/AppData/Local/Temp/retopo_verify_20260904`):**

*Probe A — AntiqueDoll (dense MD triangulated, 180,895v OBJ / 20 mtl slots):*
```
SRC  Cos_Dress_Melusina_AntiqueDoll.obj (180895 v, 744237 lines, 20 mtls)
CLEAN verts_in=143848 polys_in=296150 (bmesh weld 0.0001; close to prior 143913/296270)
QUADRIFLOW → no-op (0.0 s, polys unchanged) → Warning manifold → voxel_fallback
VOXEL_ATTEMPT 0 size=0.035795 polys=18220 → 1 size=0.050931 polys=9166 (target 9000, within 1.3N)
OUT verts_out=9168 polys_out=9166 quad_ratio=1.0 slots 21→21 kept (Material.001/Material counted)
MANIFEST engine=voxel_fallback voxel_size 0.050931 seconds 3.5 (voxel 0.8) sha256 cc4d65937508…
```

*Probe B — ButterflyWing (818,770v OBJ / 7 mtls, heavier):*
```
SRC  Cos_Accessory_Melusina_ButterflyWing.obj (818770 v)
CLEAN verts_in=777921 polys_in=1555948
QUADRIFLOW → no-op → voxel_fallback
VOXEL_ATTEMPT 0 size=0.052546 polys=9352 → 1 size=0.065602 polys=5932 (target 6000, within 1.3N)
OUT verts_out=5950 polys_out=5932 quad_ratio=1.0 slots 8→8 kept
MANIFEST engine=voxel_fallback voxel_size 0.065602 seconds 11.1 (voxel 3.3) sha256 087b0c11d5d7…
```

Both outputs are **100% quads** (`quad_ratio 1.0`), all material slots preserved by name (Substance ID reassignment intact), Smart UV applied (`smart_project 66°`), seed 20260902 in every manifest. Quadriflow path would be taken on closed-manifold inputs — the fallback is not a failure, it's the documented thick-mesh route (same `0.050931` voxel size as original recipe's scratch `TEST4`).

**Intake contract preserved:** Output FBX is drop-in for `garment_intake_prep.py --source <this output> --slot … --descriptor …` → Substance OBJ + UE FBX + intake manifest (10-garment-layer cadence). Hand-paint staging stays OPEN (never auto-wire onto mesh). UV overlap metric note: `intake uv_overlap_count` saturates post-pack (75→171 on AntiqueDoll); retopo's fresh Smart Project resets UVs, so intake will re-evaluate correctly.

**Limits (honest):**
- `_thick` double-walled market meshes are not manifold — Quadriflow will always refuse them headless; voxel fallback is the intended production path (calibrated iteration, ≤5 tries, lands within 30% of target).
- Voxel remesh is uniform — loses sewn edge sharpness; for hero tailoring, prefer a closed single-shell source if available, or split `_thick` into per-panel shells before retopo (future improvement, not blocking).
- Target N is a guide — voxel iteration stops at `[0.7N,1.3N]`; exact N requires second-pass decimation (not needed for intake).

**What was re-read (not trusted):** Both `.retopo_manifest.json` + output OBJ/FBX byte counts + sha256 are read back from disk after `blender.exe -b --factory-startup` exits. No `success:true` taken on faith.

**Rules upheld:** Seed 20260902, offline only, Blender headless only with `--factory-startup`, verified by re-reading, UE stays runtime writer, hand-paint staging stays OPEN, no Content/** touched.

Companion JSON: `verify_Retopo_2026-09-04.json`
