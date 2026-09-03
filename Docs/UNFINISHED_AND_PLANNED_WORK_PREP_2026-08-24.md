# Unfinished + Planned Work — Prep Package

**Date:** 2026-08-24
**Companion to:** `MIDI_WORLDGEN_REVIEW_AND_AAA_PLAN_2026-08-24.md`
**Purpose:** every open item stated so a fresh session (or another lane) can
resume without re-deriving context. Nothing here is claimed as done.

---

## 0. Session preconditions

```
repo            C:\EnvironmentPortfolio\BS_GodFile
blender         C:\Program Files\Blender Foundation\Blender 5.2\blender.exe
gaea 1 CLI      C:\Program Files\QuadSpinner\Gaea\Gaea.Build.exe
gaea 2 CLI      C:\Program Files\QuadSpinner\Gaea 2\Gaea.BuildManager.exe
renders         G:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\midi_*
```

Baseline moved **5x** during the previous session
(`0de0e3c6 → df404e84 → c66c531f → 529967d4 → …`). Other lanes commit live.
**Re-run `git log --oneline -3` and `git status` before any write.**

Regression suite (offline, no Blender, no UE):
```
python -B -m unittest discover -s Tools/BlenderAddons/melodia_studio/tests
-> Ran 52 tests, OK (expected failures=1), exit 0
```
Run this first. If it is not green, fix that before new work.

---

## 1. Serpentine edits — DONE this session

Requested explicitly. Completed and verified.

### 1.1 Strengthened the weak oracle
The original adjacency test asserted `<= 2` Manhattan step, which would pass a
broken fold that jumped diagonally. Measured worst step is **1**. Test now
asserts `== 1` across widths 2,3,4,8,15,16.

### 1.2 Added fold abstraction
`walkable_world.py` now exposes:
```
serpentine_xy(index, grid_w)   boustrophedon (default, unchanged behaviour)
spiral_xy(index, grid_w)       NEW inward spiral
FOLD_MODES / fold_xy(...)      dispatch, unknown mode falls back to serpentine
```
`build_heightfield(..., fold="serpentine")` and `generate_walkable()` thread the
mode through via `preset["fold"]`.

### 1.3 New preset
`walkable_spiral_arena` — song coils inward, finale lands at a central arena.
Useful when a level should build toward a boss/arena rather than a far edge.

### 1.4 Measured
```
                       footprint  aspect  height  walkable  region
walkable_valley          15 x 16   1.07      4     100%     100%
walkable_highlands       15 x 16   1.07      8     100%     100%
walkable_plaza           20 x 20   1.00      4     100%     100%
walkable_canyon          13 x 14   1.08      8    91.2%     100%
walkable_spiral_arena    15 x 15   1.00      5     100%     100%

spiral fold: w=4/8/15 -> worst step 1, bijective (16/16, 64/64, 225/225)
```
Spiral gives a perfect 1.00 aspect — the squarest footprint available.

### 1.5 Not done
Spiral has **no renders yet**. It is proven numerically, not visually.

---

## 2. Open defects

### D7 — preset height divisors ignored  (BLOCKS: preset variety)
`Tools/midi_to_voxel/midi_voxel_v3.py` `generate()` hardcodes:
```
line 119:   h = max(1, vel // 32)   # surface
line 126:   h = max(1, vel // 40)   # cave
```
So `surface_height_divisor` / `cave_height_divisor` in `midi_presets.json` are
read and discarded. Consequence: **`abyss_caves` is byte-identical to
`resonant_default`** (346 voxels, 2768 verts, same SHA).

Guarded by `@unittest.expectedFailure` in
`tests/test_midi_bridge.py::test_height_divisors_are_honoured`.

Fix: add optional `surface_div`/`cave_div` kwargs to `generate()` defaulting to
32/40 so existing callers are unaffected. **Owner decision required** — this
edits a shared tool other lanes may import.

### D14 — v5 renders not visually validated
20 frames exist in `Saved/Audit/midi_v5/`. Placement is proven numerically by
`verify_v5_placement.py`. Nobody has confirmed they look good.

**Vision is unreliable here.** Two reads of the same file
(`full_bloom__eye_level.png`) gave contradictory answers — one described a
scythe and silver hair, the other said no character present. Owner eyes needed.

### D15 — `aaa_scene_builder.py` never successfully ran
Written, syntax-clean, `os._exit` bug fixed, but its one run failed before
`save_mainfile`. It has **never modified a scene**. Superseded in practice by
`render_v5_matrix.py`. Decide: fix, or delete as dead code.

### D16 — 37 GeneratedScenes still broken
All 37 share defects D3/D4/D5 (no material, unrotated camera, undersized
lights). Only the 3 `scene_128BPMarpeggiomelody*` scenes were investigated, and
those were left **unmodified** (SHA-verified against `scene_PRE_AAA.blend`).
The 37 exported FBX in `Content/GeneratedScenes/` are geometry with no
materials and no UVs.

### D17 — only 1 MIDI has usable substance
```
128BPMarpeggiomelody.mid            192 notes -> 346 voxels
128BPMarpeggiomelody_beatgrid.mid    64 notes -> 192 voxels
all_jingles.mid                      12 notes ->  27 voxels
(17 more GBA jingles: 1-8 notes each, 3-24 voxels)
```
"Different landscapes" currently means different presets, not different songs.
More substantial MIDI is needed for real level variety.

---

## 3. Phase 1 — Material and lighting  (NEXT, highest payoff)

Not started. This is where the visual jump happens; everything renders as
untextured cubes with flat EEVEE shading today.

| # | Task | Notes |
|---|---|---|
| 1.1 | PBR per block tier | stone/wood/crystal/gold; triplanar so voxels need no UV unwrap |
| 1.2 | Compositor bloom/glare | **root cause of "matte"** — shader emits, nothing blooms it |
| 1.3 | Volumetric fog + light shafts | `aurora_veil` exists but is thin (density 0.035) |
| 1.4 | Contact shadows + AO | seat props visually into the ground |
| 1.5 | Re-render matrix, owner review | side-by-side vs a reference frame |

Existing project PBR to reuse before authoring new:
`Content/EnvSandbox/Materials/` (`M_Master_Toon_*`, PBR instances).

Blender 5.2 API notes already learned:
- `scene.node_tree` does **not** exist — use `getattr(sc, "node_tree", None)`.
- `Material.use_nodes` / `World.use_nodes` deprecated (removal in 6.0).
- `mesh.use_auto_smooth` gone; use the `SMOOTH_BY_ANGLE` modifier.
- Wrap `os._exit()` in try/except or tracebacks are swallowed silently.

---

## 4. Phase 2 — Gaea integration

Not started. Unblocked by the fold: a 64x11 ribbon could not be meaningfully
eroded; a 15x16 field can.

| # | Task |
|---|---|
| 2.1 | Export heightfield as 16-bit PNG/TIFF heightmap |
| 2.2 | Verify Gaea CLI contract (`Gaea.Build.exe` args, headless flags) |
| 2.3 | Author Gaea graph: erosion, sediment, flow, curvature, splat |
| 2.4 | Re-import as displaced landscape; keep voxels as hero silhouette or drop |
| 2.5 | Gate: erosion visibly follows the melody's ridgelines |

**Owner decision:** Gaea 1 (`Gaea.Build.exe`, known CLI) or Gaea 2
(`Gaea.BuildManager.exe`, CLI contract unverified)?

Field data is already available for export — `walkability()` returns footprint
and height span, and `classify_cells()` gives peak/ridge/valley/path/slope tags
usable directly as Gaea masks.

---

## 5. Phase 3 — Scattering at density

Current cap is **57 props** via per-object instancing. Not viable for AAA.

| # | Task |
|---|---|
| 3.1 | Geometry-Nodes scatter driven by the existing tag map |
| 3.2 | Density masks from Gaea flow/curvature output |
| 3.3 | LOD + instancing budget for UE |
| 3.4 | Gate: 10k+ instances at interactive frame rate |

`plan_dressing()` already returns a deterministic, budgeted plan — feed it to GN
instead of `instance_dressing()`.

---

## 6. Phase 4 — UE5 level pipeline  (FROZEN)

**Blocked by the convergence plan** — `.umap`/`.uasset` writes are forbidden and
"Never run Unreal, Monolith, PIE."

| # | Task |
|---|---|
| 4.1 | Heightmap -> UE Landscape; splat -> Landscape layers |
| 4.2 | Props -> PCG (project already uses `PCG_*`), not baked FBX |
| 4.3 | Collision proven with a pawn |
| 4.4 | Gate: **walk it in PIE with real input** |

Note the project's own evidence standard: a probe is **not** play evidence, and
a gate is certified only when `record_gate.py <id> pass` writes a ledger row.
`walkable_fraction: 1.0` is a geometry metric, **not** proof anything is
playable in-engine.

---

## 7. Phase 5 — Musical gameplay

| # | Task |
|---|---|
| 5.1 | Beat-synced level events (`harmonic_rings` pulsing on beat) |
| 5.2 | Music-as-key traversal — the world puzzle is **not yet built** per AGENTS.md |
| 5.3 | Wire via existing typed bridge; **no new authority** |

Must respect: QuillScript owns narrative, stock JRPG owns combat/save,
`UMelodiaNarrativeSubsystem` is the only Melodia story-state boundary.

---

## 8. Convergence-plan lanes — none started

All four overnight lane paths are still **absent** from disk:
```
absent  Tools/authority_atlas/
absent  Tools/experience_contract_audit/
absent  Tools/non_ue_gate_audit/
absent  Tools/portfolio_claims_packet/
absent  Docs/Reports/Overnight/
```
Prompts are in the plan the owner pasted. Independent of world-gen work.

---

## 9. Owner decisions blocking progress

1. **D7** — patch `midi_voxel_v3.generate()` for divisors? (shared tool)
2. **Freeze** — plan says "Never run Blender"; it was run on explicit owner
   instruction. Does that authorization extend to Phase 1?
3. **Scope** — polish 3 scenes, or batch-fix all 37 (D16)?
4. **Gaea version** — 1 or 2?
5. **`abyss_caves`** — keep duplicate preset until D7, or remove now?
6. **D15** — fix or delete `aaa_scene_builder.py`?
7. **Spiral renders** — render `walkable_spiral_arena` for visual sign-off?

---

## 10. Resume checklist

```
1  git log --oneline -3 && git status --porcelain | wc -l
2  python -B -m unittest discover -s Tools/BlenderAddons/melodia_studio/tests
      expect: 52 tests, OK (expected failures=1)
3  python -B Tools/BlenderAddons/melodia_studio/walkable_world.py
      expect: 5 presets, all aspect < 1.1, walk >= 0.91, region 1.0
4  blender --background --factory-startup --python \
      Tools/MelodiaProceduralStudio/verify_v5_placement.py
      expect: STANDING / ABOVE_SURFACE / ON_SURFACE / IN_FRAME
5  confirm scenes untouched:
      sha256sum GeneratedScenes/scene_128BPMarpeggiomelody/scene.blend
      vs        .../scene_PRE_AAA.blend
```

Do not trust vision output as proof of geometry. Use
`verify_v5_placement.py` numbers.
