# 04 — Gate 3 (P0): `HDA_Foundry_FieldAtlas`

| | |
|---|---|
| **Purpose** | One reusable semantic-field generator: terrain/geometry in → named, normalised channel rasters/attributes out, tile-aware and deterministic. |
| **Authority** | Offline data product. It **extends** World Compiler; it does not change it. `world_recipe.v1`, `world_compiler_point_row.v1` and `world_compiler_v1.0` are untouched. Channels reach World Compiler only through a future additive version (`field.kind: chunk_grid`, `world_compiler_point_row.v2`), already anticipated by `WORLD_COMPILER_CONTRACT.md` §9. |
| **Inputs** | terrain or arbitrary geometry (OBJ/FBX import or UE export of the tile), region bounds, optional water surface, authored splines, hero locations, seed. |
| **Outputs** | Per channel: one linear 32f EXR per tile (`field_atlas_<tile>_<channel>.exr`) + optional point attributes; `bake_manifest.json` with bounds, tile id, channel list, hashes; ≤ 1 MB preview PNG. |
| **Vocabulary** | [`specs/houdini_foundry/field_atlas_channels.v1.json`](../../../specs/houdini_foundry/field_atlas_channels.v1.json) — validated by `houdini_foundry.py`. |
| **Evidence** | `Saved/Audit/houdini_foundry/<recipe_id>/` |
| **Status** | STAGED. HDA does not exist. The pattern to copy is `Tools/Houdini/vdm_fabric_mountains/faraway_static_field.py` (RGBA + manifest + hash, cross-checks existing math before writing). |

## Channel rules (why the vocabulary looks the way it does)

Before adding a name, the existing contracts were checked:

- `points.csv` already defines `hero_weight`, `sparkle_response`, `Resonance` (exact case), `EcologyClass`. FieldAtlas reuses those meanings. When a channel is emitted as a **point attribute for World Compiler**, it must use the exact existing column name.
- The Faraway static field already names `WorldField.Tension`, `WorldField.ResonanceBase`, `WorldField.Moisture`. `tension`, `resonance` and `humidity` map to these.
- `Cymatic_WindDirX/Y`, `Cymatic_WindStrength` are **runtime MPC lanes with sole writers**. FieldAtlas `wind_x/wind_y/wind_strength` are baked data with aligned names and are **never written to an MPC**.
- Everything else is `status: proposed` in the vocabulary file. Proposed means that name is reserved for this meaning; it does not mean a UE consumer exists.

## HDA interface

| Parm | Type | Notes |
|---|---|---|
| `Seed` | int | tile seed from `houdini_foundry.py plan` (never invent one) |
| `BoundsMin/Max` | vec2 cm | tile **bake** bounds (core + gutter) from `plan` |
| `CoreMin/Max` | vec2 cm | crop region for export |
| `Resolution` | int | px per tile edge (test tile 512) |
| `Channels` | string list | subset of vocabulary |
| `WaterLevel` | float cm | optional; drives `shore_influence`, `wetness` |
| `HeroPoints` | point input | drives `hero_weight` (falloff default 600 cm, the World Compiler `hero_falloff_cm` default) |
| `Splines` | curve input | optional flow/wake guides |
| `ErosionIterations` | int | heavy; 0 for the interactive test tile |

Inputs: 0 = terrain/geometry, 1 = hero points, 2 = splines, 3 = water surface.

## Network outline (SOP/COP, H22)

`input terrain → heightfield from geometry (bounds from parms) → masks (slope, curvature split into concavity/convexity, occlusion→cavity, exposure) → optional heightfield erode (flow, sediment, debris) → distance-to-water (shore_influence, wetness) → hero falloff → resonance (reuse the Chladni basis from resonance_ecology_processor where possible) → normalise per channel to vocabulary range → crop to core → File COP/heightfield output, one EXR per channel`.

Normalisation constants (for example, the max slope used for 1.0) are **recorded in the manifest**. Otherwise tiles stop being comparable.

## Determinism and seams

- All noise uses `Seed`. Tiles compute on **bake bounds** (with gutter) and export **core bounds**, so neighbouring tiles agree at the seam within the gutter.
- Seam check (Gate 5): for adjacent tiles, compare the shared edge column. Pass when the mean absolute difference is ≤ 0.02 in normalised units. Record the value.

## Done when (Gate 3)

`field_atlas_sea_above_test_tile` produces every listed channel for `tx-001_ty+000`. A second cook has identical hashes. `verify` passes. Brennan has looked at the preview and says the channels read sensibly (e.g. flow follows valleys).
