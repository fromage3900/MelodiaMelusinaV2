# HDA_ENV_FabricMountain_Drape — Houdini 22 drape spec (breathtaking part)
Status: scaffold spec, not yet cooked — tonight's offline weave plan

## Goal
True fabric behaving as geology, not noise. SDF terrain as collision, pleat SDF as guide, Vellum cloth drape -> VAT export.

## SOP Network
```
IN_HeightField_tile (512x512, 1 tile of LM_FarawayMother_Terrain, scale 0.01 landscape)
  -> Labs HeightField to VDB (collision SDF)
IN_PleatCurves (sine fold network: |sin(x*f_fold)|^p_sharpness, f=0.02 km-scale, p=4, depth 40m)
  -> Labs Curve to SDF (fold field, thicken 8m)
Merge -> VDB Combine (SDF union, offset -2m for drape gap)
  -> Vellum Source (plane 200x200, res 4m, rest scale 8000m) + VDB collision
  -> Vellum Solver (tension anchors from Saved/Audit/houdini_faraway_mother/drape_manifest.json, stiffness 1e4, sag 0.6)
  -> Vellum Cache (1 frame, baked) -> Labs VAT ROP (vertex animation texture, 3 VAT textures)
  -> Height output + TensionMask (curvature * cymatics amplitude attribute)
  -> Labs AutoLOD (LOD0 Nanite, LOD1 50% remesh preserve sharpness attr, LOD2 25%+normal bake, LOD3 impostor)
  -> Output: SM_FabricRidge_Hero FBX + 4 LODs + collision Kdop18
```

## Outputs (per drape_manifest.json)
- Exports/Houdini/FarawayMother/SM_FabricRidge_Hero.fbx
- Saved/Audit/houdini_faraway_mother/tension_mask.png (8-bit, tension 0..1)
- Saved/Audit/houdini_faraway_mother/drape_attributes.json (WorldField.Resonance/Tension per-vertex)

## Bake command (tomorrow, Houdini 22.0.368)
```
hython Tools/Houdini/copernicus/copernicus_dress_bake.py --hip Tools/Houdini/copernicus/hda_variants/faraway_p2_corset_cop.hip --bake-set T_FarawayMother_Corset
# then for drape:
hython --hip Houdini/FarawayDrape.hip --cook HDA_ENV_FabricMountain_Drape --export FBX
```

## WPO link
Vellum VAT + MF_FabricMountainWPO stack: macro swell samples ModeN/ModeM as wavelength, not new sim.
Single MPC writer preserved.

## PCG link
HDA_ENV_ScatterMaskBuilder reads tension_mask + slope/curvature -> PCG_Faraway_FabricRidge candidate points.
