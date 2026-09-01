# FlowerSpring — Substance Painter Staging Kit (2026-08-31)

Everything needed to open a Substance Painter project and hand-paint the
FlowerSpring dress. Built by the detailed-Houdini redo lane (v2) after the
2026-08-31 owner QA rejection of v1 (crown = jagged ring, wings = waist slab).

## Contents

```
meshes/
  FS_Dress_Draped_cascade.fbx   shirt + redraped skirt (cascade silhouette)
  FS_Crown_v2.fbx               head-sized diadem: lathed band, 12 closed-shell
                                petals (curl+cup+twist), 7 faceted bezel gems
  FS_Wings_v2.fbx               4 back-mounted membranes: smooth cosine-scallop
                                outlines, tapered vein strips, rim cups
  FS_FullAssembly_cascade.fbx   all of the above in one file
textures/<Variant>/             2048 tiling sets, 8 maps each:
  T_<V>_BaseColor.png           authored colour (paint over this)
  T_<V>_Normal.png
  T_<V>_ORM.png                 R=AO  G=Roughness  B=Metallic (UE packing)
  T_<V>_Height.png
  T_<V>_Emissive.png
  T_<V>_Iridescence.png         soft-hex hue field (use as iridescence/thin-film input)
  T_<V>_Sheen.png               sheen strength mask
  T_<V>_Motif_N.png             Chladni motif normal (detail layer)
textures/FlowerSpring/v1_kit_legacy/   the 9 maps from the v1 fabric kit (kept)

Variants (colour families reused from Saved/Audit/copernicus_cymatic/):
  FlowerSpring        cream/butter/gold/peach/blush + spring accents
  GildedLoom          champagne -> deep gold (metallic thread 0.45)
  SilkWaterfall       pearl/ice/silver-blue satin
  CherryBlossomWood   petal blush/rose + warm wood
  StarlitAbyss        deep indigo, star-silver emissive field
```

## Opening in Substance Painter

1. **New project** -> select `meshes/FS_FullAssembly_cascade.fbx`
   (or per-piece FBX to paint them as separate texture sets).
   Normal map format: **OpenGL** (Blender/Houdini authored).
2. **Channel setup** is already conventional: BaseColor / Normal / Roughness /
   Metallic / Height / Emissive. Load each `T_<Variant>_*` map into its channel
   as a starting fill layer, then paint on top:
   - `ORM` -> split: R into AO, G into Roughness, B into Metallic
   - `Iridescence` -> paint-through layer or thin-film/level import
   - `Sheen` -> sheen weight mask
   - `Motif_N` -> detail normal layer (low strength, tile ~4x)
3. **Export** painted sets as PNG per channel (or ORM-packed) for re-import to UE.

## Status update 2026-09-01 — .spp files now exist

Substance **Painter 11.1.1 IS installed** and the five `.spp` projects were
generated automatically (startup-module Python builder). They live in `spp/`:
`FlowerSpring_<Variant>.spp` ×5, each with the four texture sets
(`M_FS_Crown / M_FS_Shirt / M_FS_Skirt / M_FS_Wings`) and starter fills already
wired — dress sets carry the baked `T_<V>` maps on BaseColor / Normal / Height /
Roughness / Metallic; crown/wings carry uniform gold/blush starter fills.
Open `spp/FlowerSpring_FlowerSpring.spp` and paint on top.

Full pipeline + Painter API gotchas:
`Docs/Production/FLOWERSPRING_SUBSTANCE_PIPELINE_2026-09-01.md`

(The note below predates the automation — channel setup guidance still applies,
but you no longer need to build the project or load maps by hand.)

## Honest note on .spp (historical, 2026-08-31)

Substance **Painter/Designer are not installed** on this workstation (only the
*Substance 3D for Maya* plugin, which cannot author .spp). A `.spp` is a
proprietary container that cannot be generated programmatically — this kit is
the complete, import-ready equivalent: meshes + baked starting maps + variants.
Opening Painter once creates the .spp in seconds from step 1 above.

## Provenance

- Geometry: `Tools/Houdini/sea_above_reef/flowerspring_crown_wings_v2.py`,
  `flowerspring_skirt_silhouette.py` (hython, seed 20260831, meters end-to-end)
- Maps: `Tools/Houdini/sea_above_reef/flowerspring_variant_maps.py` (seed 20260831)
- QA renders: `Saved/Audit/melusina_lookdev/flowers_outfit/qa_v3/`
  (front/back/three-quarter, crown + wings closeups, cascade/tulip/bloom
  silhouette contact sheet)
- Manifests: `Saved/Audit/melusina_lookdev/substance_staging/FlowerSpring/*.json`
  and `flowers_outfit/*manifest*.json`
