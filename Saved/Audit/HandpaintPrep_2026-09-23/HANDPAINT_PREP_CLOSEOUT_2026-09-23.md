# Handpaint Prep — 2026-09-23

Six-asset staging for tonight's Substance handpaint + UE lookdev session.
Everything the agent produced lives in this folder; **no source files were modified**.

Pipeline used: headless Blender 5.2 (`blender -b <file> -P <script>`), scripts in this folder:
`extract_from_stage.py` (isolate assets from the 1.8 GB Melodia Portfolio Stage v18),
`prep_asset.py` (census → HI/LO pair → decimate → Smart UV → studio setup → report),
`fix_prep.py` (targeted fixes), `stage_census.py` (read-only stage audit).

## Status board

| # | Asset | State | Prep blend | Notes |
|---|-------|-------|-----------|-------|
| 1 | StylizedCrossProp | READY | `01_StylizedCrossProp/StylizedCrossProp_HandpaintPrep.blend` | 922 polys, UVMap OK, 2.0×4.1×5.7 m. Source FBX + 5 baked maps (BaseColor/Normal/Roughness/Displacement/Alpha) in `source/` |
| 2 | ZenLantern | READY (LO only) | `02_ZenLantern/ZenLantern_HandpaintPrep.blend` | 1,376-poly retopo w/ UVMap, 3.7×3.6×7.2 m. **Hi-poly (8.2 M tris) no longer exists** — retired with stage v14; only the retopo survives in v18/v24. Paint directly on the retopo |
| 3 | MelodySlime | READY | `03_MelodySlime/MelodySlime_HandpaintPrep.blend` | HI `slimebasicnormals` 282 k polys; LO `slimebasicnormals_LO` 54,993 polys w/ Smart UV. Plus 3 retopo variants (234–7,400 polys) |
| 4 | CosmicReaver | READY | `04_CosmicReaver/CosmicReaver_HandpaintPrep.blend` | `reaver_CAGE` (82 k, shape keys) + `reaver_LOW` (82 k) are the bake pair; `_LO` copies at 22,158 polys (shape keys stripped — decimate cannot apply with them). Ornament set included (clef, torus knot, circlet, pauldrons) |
| 5 | Baked Melody Tokens | READY | `05_MelodyTokens/SM_MelodyToken_HandpaintPrep.blend` | **All variants share this one mesh** (612 polys, UVMap) — Star/Swirl/Water/Heart maps bake onto it (owner confirmed: already painted on cylinders in Substance). Hi sculpts (`MelodyTokenStar/Swirl/Water`, 0.9–2.5 M polys) kept in `MelodyTokens_hi_source.blend` + per-token files as **reference only** — no UV work needed on them |
| 6 | TreasureChest | **MISSING** | — | Does not exist anywhere in the repo (exhaustive name search: no mesh, no `.blend`, no GN builder). Only unrelated KitBash vehicle chests. Needs authoring or a pointer to the real source |

## Pipelines reviewed (to minimize tonight's work)

- **melodia_gn** — `deploy/surreal_arch/melodia_gn/` (~150 Python GN builders; `reaver_wings.py` generated the Cosmic Reaver family; `misc_props_kit.py` has lamps/crates/banners — usable to bootstrap a TreasureChest base).
- **Higgsas bridge** — `deploy/surreal_arch/higgsas_bridge.py` + `RawArt/BlenderLibraries/Higgsas/Blender 5.0 Higgsas Geo Node Groups v13.blend` (33 node groups: Bend, Taper, Circular Array, Voxel Remesh, Ripples…).
- **Bake/UV/trim tooling** — `deploy/surreal_arch/trim_bake.py`, `trim_color_bake.py`, `uv_ops.py` (trim-sheet bake flow is the closest existing Substance-style lane).
- **Headless render/glam pattern** — `Tools/render_cross_zenlantern_mcp_resume.py` (the Cam_Beauty + 4-light rig pattern the prep studio copies).

## Tonight's workflow per asset

1. Open `<Asset>_HandpaintPrep.blend` — clay override is on the view layer; toggle it off to see original materials.
2. Substance Painter: import the `_LO` mesh (has UVs) + the HI mesh as a bake source where one exists (slime, reaver, tokens sculpts).
3. Tokens: import `SM_MelodyToken` only — your existing cylinder bakes apply as-is.
4. Export maps → UE lookdev against the existing instances: `MI_MelodyToken_Star/Swirl/Water/Heart`, `MI_Zen_LanternWarm`, `MI_Review_ZenLantern_Voronoi3T`, `MI_MelodySlime_Body`.

## Known gaps / decisions

- **TreasureChest**: not in the repo. Either point me at the real source or I can generate a handpaint-friendly base via melodia_gn + Higgsas (Rounded Cube body + lid + bands + lock) for you to art-direct.
- **ZenLantern hi-poly is unrecoverable** (stage v14 deleted); the retopo is clean and paint-ready, so impact is low.
- Token sculpt extracts (`MelodyToken*_source.blend`, `MelodyTokens_hi_source.blend`, ~1 GB) are reference-only — safe to delete once tonight is done.
- Each prep blend carries a `*_prep_report.json` with exact poly counts, UV state, and dimensions.


---

# PHASE 2 — Owner-supplied sources (2026-09-23 evening)

Plan of record: [UPDATED_PLAN](UPDATED_PLAN.md) — cymatic × Infinity Nikki lens.
All four sources were copied from Downloads into this workspace; originals untouched.

| Asset | Source | Topology fix | UV | Prep blend | Substance pair |
|---|---|---|---|---|---|
| TreasureChest | ZBrush OBJ, 2.403 M f, no UV | LO decimated to 224,975 f | Smart UV on LO | `06_TreasureChest/TreasureChest_HandpaintPrep.blend` | `substance/meshes/TreasureChest_high.fbx` + `_low.fbx` |
| FallenMoon | ZBrush OBJ, 3.069 M f, no normals/UV | LO decimated to 364,218 f | Smart UV on LO | `07_FallenMoon/FallenMoon_HandpaintPrep.blend` | `substance/meshes/FallenMoon_high.fbx` + `_low.fbx` |
| CosmicReaverBase | USDZ→usdc `male_zbrush` 81,995 f | already low; **identical to `reaver_LOW`** in the 04 prep | Smart UV added (had none) | `08_CosmicReaver_USDZ/CosmicReaverBase_HandpaintPrep.blend` | `substance/meshes/CosmicReaverBase_low.fbx` (male_zbrush) + `_high.fbx` (reaver_CAGE) |
| MelodiaMelusinaFlowers | USDZ→usdc, 3 meshes (23 k/534 k/626 k f) | LO at 23,538 / 103,560 / 110,696 f | Smart UV on LOs; Cylinder kept its UV | `09_MelodiaMelusinaFlowers/MelodiaMelusinaFlowers_HandpaintPrep.blend` | `substance/meshes/MelodiaMelusinaFlowers_high.fbx` (3) + `_low.fbx` (3) |

- Cymatic Copernicus map set staged: `Bakes_Cymatic/FrozenFracture/` (9 channels, from `Saved/Audit/copernicus_cymatic/`).
- Per-asset `substance/bake_recipe.json` (machine-readable cymatic layer recipes) + `substance/paint_guide.md` (Nikki palette, motif placement, bake steps).
- Note: flowers USDZ imports at centimeter-ish scale (dims 0.04–0.22 m) — verify intended scale against Melusina before UE import.
- Note: decimate under-reduces on dense ZBrush raws (collapse floor) — LO counts landed above target; still comfortably paintable in Substance.


## Phase-1 Substance scaffolding (same pass, applied to all five)

Each Phase-1 asset now mirrors the Phase-2 layout: `substance/meshes/` FBX, `substance/bake_recipe.json`, `substance/paint_guide.md`.

| Asset | Meshes staged | UV status |
|---|---|---|
| StylizedCrossProp | `StylizedCrossProp.fbx` (922 f, self-bake) | authored UVMap ✓ |
| ZenLantern | `ZenLantern.fbx` (1,376 f retopo, self-bake) | authored UVMap ✓ |
| MelodySlime | `MelodySlime_high.fbx` (282,873 f) + `MelodySlime_low.fbx` (4 meshes: 54,993 + 7,400 + 234 + 3,750 f) | Smart UV on LO; **Retopo_Cube UV fixed this pass** |
| CosmicReaver | `CosmicReaver_high.fbx` (CAGE + LOW) + `CosmicReaver_low.fbx` (both _LO at 22,158 f) | UVMap on all ✓ |
| MelodyTokens | `SM_MelodyToken.fbx` (612 f shared mesh) | authored UVMap ✓ |

All nine assets now share the `Bakes_Cymatic/FrozenFracture/` map root and the cymatic × Infinity Nikki lens via their recipes/guides.


---

# PHASE 3 — Geometry polish + final exports (2026-09-23 evening)

Polish script: `polish_meshes.py` (modes: hardsurface / organic / shapekey_safe). Every prep blend re-saved in place; every `substance/meshes/*.fbx` re-exported from the polished blends and name-verified (all 15 FBX contain their expected models — earlier ZenLantern/Slime-high FBX were empty due to hidden-collection skipping in the FBX exporter, now fixed in `export_fbx.py`).

| Asset | Mesh | Before → after f | Mode | UV after | Notes |
|---|---|---|---|---|---|
| StylizedCrossProp | Instance Star.001 | 922 → 2,344 | hardsurface | UVMap ✓ | bevel + weighted normal |
| ZenLantern | zenlantern_Retopo_lanternfinal.004 | 1,376 → 3,270 | hardsurface | UVMap ✓ | bevel + weighted normal |
| MelodySlime | slimebasicnormals_LO | 54,993 → 54,993 | organic | UVMap ✓ | merge doubles + Laplacian 0.4×2 + smooth-by-angle |
| MelodySlime | slimebasicnormals (HI) | untouched (bake source) | — | — | 282,873 f sculpt reference |
| CosmicReaver | reaver_CAGE / reaver_LOW | 81,995 → 81,995 | shapekey_safe | UVMap ✓ | smooth-by-angle ONLY; **shape keys preserved (keys=yes)** — audit gate |
| CosmicReaver | reaver_CAGE_LO / reaver_LOW_LO | 22,158 → 22,158 | organic | UVMap ✓ | merge doubles + Laplacian |
| MelodyTokens | SM_MelodyToken | 612 → 996 | hardsurface | UVMap ✓ | bevel + weighted normal |
| TreasureChest | treasurechest_LO | 224,975 → 224,975 | organic | UVMap ✓ | Laplacian 0.4×2 |
| FallenMoon | fallenmoon_LO | 364,218 → 364,218 | organic | UVMap ✓ | Laplacian 0.4×2 |
| CosmicReaverBase | male_zbrush | 81,995 → 81,995 | shapekey_safe | UVMap ✓ | smooth-by-angle only |
| Flowers | Cylinder_LO / Phonograph_Part2_LO / PM3D_Sphere3D1_LO | 23,538 / 103,560 / 110,696 → 23,534 / 103,560 / 110,696 | organic | st / UVMap / UVMap ✓ | merge doubles removed a handful of dupes |

**Audit gates (all pass):**
- UV layers non-empty on every exported mesh (report field `uv` in each `polish_report.json`).
- Reaver `reaver_CAGE`/`reaver_LOW` vertex/face counts byte-identical before/after and `keys=yes` in both runs — shape keys untouched.
- Organic passes: merge-doubles only ever *removed* duplicate verts (≤4 per mesh); Laplacian/smooth change shading only, never counts.
- Slime low FBX composition change: now **only** `slimebasicnormals_LO`. The three extra meshes swept in earlier (`Cube`, `Retopo_Cube`, `Retopo_Cube.001`) are rigged retopo-cube leftovers (ARMATURE modifiers, no authored UV on Retopo_Cube) — excluded from the paint set; still present in the blend, not deleted.

**Known leftovers (not blockers):**
- Flowers scale still unverified (cm-import dims) — check against Melusina before UE import.
- Token sculpt extracts (~1 GB) remain reference-only; safe to delete after tonight.
- Blender 5.2 gotchas encoded in scripts: LaplacianSmooth RNA renamed (`lambda_factor`/`iterations`); FBX exporter skips objects invisible at the view-layer level (`export_fbx.py` now force-unhides).


---

# PHASE 4 — Closeout: UE import manifest + contact-sheet verification (2026-09-23)

- UE import manifest committed to git: `Saved/Audit/HandpaintPrep_2026-09-23/UE_IMPORT_MANIFEST.md` + `ue_import_manifest.json` (commit 67f84611b, pre-commit validation passed). Maps all 9 assets to import FBX, bake source, proposed `Content/Melodia/{Props,Textures,Materials}/Handpaint/` paths and `MI_Handpaint_*` instances, with per-asset import flags.
- Contact sheets rendered from the exported FBX files in factory scenes (validates the actual deliverables, not just the blends): `contact_sheets/MASTER_contact_sheet.png` + 9 `strip_*.png` (3 views each).
- ZenLantern blend carries a compositing-stage setup (view-layer exclusion + `W_Melodia_FadeDayNight` world) that makes headless renders from the blend come out empty — renders are therefore FBX-sourced (`render_fbx.py`). FBX exports themselves are clean.
- Contact-sheet findings: reaver rest pose renders head-down (up-axis check at UE import; base #08 same mesh family renders upright). Flowers relative scale between the 3 meshes is off (cm-import family issue, ×100 flag in manifest).


---

# PHASE 5a — EXECUTED 2026-09-23 (Blender-only per owner): vcol_melodia on all 9

UE editor work explicitly vetoed by owner ("NO UE, ONLY BLENDER") — this phase is pure Blender.

**Convention delivered** (`vertex_paint.py`, one run per prep blend, blends saved in place):
- Attribute `vcol_melodia` (BYTE_COLOR, CORNER domain) on every paint-target mesh.
- **R wear** = inverted Cycles AO bake (8 samples, per-corner). `paint_dirty` op was removed in Blender 5.2 — AO bake replaces it. Bake needs full render-visibility reset (object + collection hide_render + LayerCollection exclude/holdout — the lantern stage-compositing setup had holdout, which fails Cycles bakes with "not enabled for rendering").
- **G decoration density** = per-asset bbox-fraction rules (lantern eaves 1.0; cross arm tips; token rims; chest lid; reaver edges; flowers petals).
- **B audio-reactivity weight** = normalized height falloff toward the crown.
- **A emissive zones** = lantern fire box 42–60% height; cross crystal >88%; token top; slime core; chest cavity; reaver torso; flowers centers.

**FBX re-export with vertex colors** (all 9 paint targets): vcol rides FBX automatically in 5.2. Stale color layers (`Attribute`, `Color`, `displayColor`) STRIPPED from 01/02/06/09 so `vcol_melodia` is the only color set — UE/Substance will unambiguously pick channel 0. Round-trip verified: re-imported lantern FBX carries exactly `vcol_melodia` with R/G/B/A means 0.49/0.30/0.50/0.45; cross 0.35/0.46/0.54/0.14.

**Per-asset stats** (corners / R / G mean / B mean / A coverage):
01 cross 9,490 · ao-ok · .46 · .54 · .14 | 02 lantern 13,168 · .30 · .50 · .45 | 03 slime 169,472 · .30 · .42 · .08
04 reaver LOW_LO 68,912 · .20 · .47 · .21 (CAGE_LO has vcol but flat R=0.5 — bake cage, not a paint surface) | 05 token 4,036 · .81 · .48 · .29
06 chest 688,589 · .32 · .46 · .13 | 07 moon 1,128,436 · .30 · .44 · .07 | 08 base 327,976 · .20 · .53 · .45
09 flowers 90,820+327,120+341,392 · ok · petals G=1 · centers A

**Handpaint starter state tonight:** polished meshes + UVs (Phases 1–3) + `vcol_melodia` masks (5a) + cymatic bake recipes/paint guides + contact sheets. In Substance: import the low FBX → vcol available as vertex data for masking (wear R, decoration G). Masks are STARTERS — hand-tune in Blender vertex-paint mode as you paint.
