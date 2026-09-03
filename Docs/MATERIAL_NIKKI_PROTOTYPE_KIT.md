# Nikki Prototype Material Kit

This kit is for SurrealArch environment meshes, Review Queue architecture props, and portfolio stills. It is not a Melusina wardrobe/material workflow.

## Blender Operators

- `surreal_arch.nikki_mat_apply`: applies `MEL_Mat_NikkiSurface_{Subtle,Dream,Hero}` to selected prop meshes.
- `surreal_arch.komikaze_apply` palette key `NIKKI_HALFTONE`: delegates to `surreal_arch.nikki_mat_apply`.
- `surreal_arch.komikaze_auto_map`: routes stone, brick, wood, trim, and plaster roles to the Nikki prop wrapper.

Protected names containing `melusina`, `sk_melusina`, or `hair` are skipped.

## Wrapper Groups

| Group | Role |
| --- | --- |
| `MEL_NPR_LinearHalftone` | Melodia-owned wrapper around Komikaze `Linear Gradient (Halftone)` when available |
| `MEL_NPR_Tiler` | Melodia-owned wrapper around Komikaze `NTTiler [Komp]` when available |
| `MEL_Mat_NikkiSurface` | Shared wrapper identity for the prop material family |

Komikaze source blend: `G:\programs\BlenderPlugins\plugins\Komikaze v2 (UNZIP ME) vfxmed\Komikaze v2.blend`.

## Three-Layer Recipe

1. Texture layer: run or reuse `Tools/MaterialMaker/build_surreal_tile_master_v2.py` with `Tools/MaterialMaker/presets/nikki.json` for Nikki base color/roughness ideas.
2. Mesh detail layer: optionally load Higgsas grids through `surreal_arch.higgsas_bridge`, using `NTBricks Grid`, `NTHexagon Grid`, or `NTCairo Tile Grid` for prop-scale breakup.
3. NPR layer: apply `Nikki Mat (props)`, which creates the Melodia wrapper groups and assigns a pastel procedural material with halftone/tiler wrapper nodes available in the graph.

## Variants

- Subtle: soft pastel and mild halftone for portfolio stills.
- Dream: default balance for Review Queue architecture props.
- Hero: stronger sparkle/rim read for sendoff or close-up props.

## Render Notes

- EEVEE quick look: use material preview or EEVEE with soft shadows and bloom enabled. The native fallback material is procedural and does not need external textures.
- Cycles portfolio stills: use Dream or Hero, keep roughness below 0.55, and add a soft rim/key light so the pastel ramp remains visible on carved surfaces.
- Stage safety: agents should not save `Melodia_Portfolio_Stage_*.blend`; let the artist inspect and save.

## UE Boundary

UE `MI_NikkiProto_*` instances and `surreal_world/export.py` `ROLE_UE_HINTS` are owned by the UE phase. This Blender kit only records the intended recipe on objects via `melodia_material_recipe`.
