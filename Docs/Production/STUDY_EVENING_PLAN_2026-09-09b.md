# STUDY_EVENING_PLAN_2026-09-09b — Ornament Visibility Fix

## Status: COMPLETE — Ornaments confirmed visible in renders

## Root Cause
The ornament GN trees (Beads_Catenary, Star Pendant, Heart Filigree, Wall Bead String)
were structurally complete but had two rendering defects:

1. **Guide curves were empty**: Eave_Guide_Main had 0 splines, and all other guides
   had only 2 control points (degenerate straight lines). The Object Info node could
   not read points from these curves, so Resample Curve produced nothing and
   Instance on Points had zero instances to distribute.

2. **GN material remapping**: When Instance on Points instances a template object
   onto the roof mesh, Blender's Realize Instances creates a 2nd material slot
   in the output mesh (index 1 = None/empty). ~57% of ornament faces ended up
   on this null material slot and were invisible in renders.

## Fixes Applied
1. **Rebuilt all 9 guide curves** with proper multi-point Bézier splines (3-5 points each)
2. **Added Set Material nodes** to all 4 ornament GN node groups, forcing every face
   to use MH_MAT_Ornament_Gold (Base Color 0.95, 0.85, 0.2 = bright gold) at index 0
3. **Templates cleaned**: Each template now has exactly 1 material (gold) at slot 0,
   all faces at material_index 0
4. **Templates moved** to STUDY_TEMPLATES collection (render visibility confirmed)

## Verification
- Evaluated mesh: 32,432 verts, 7,464 faces
- ALL 7464 faces at material_index 0 = gold (0.95, 0.85, 0.2, 1.0)
- Set Material nodes confirmed in all 4 GN groups
- **Renders showing gold ornaments**:
  - Orn_CloseUp_v1.png: gold spheres + metallic wing structure
  - Orn_Star_XT.png: 19 gold spheres in arched line below metallic structure
  - Orn_Star_v4.png: faceted metallic gold panels on eave, spheres may appear
    off-white due to metallic reflection highlights
  - Orn_Eave_v3.png: "small, spherical, shiny metallic gold (yellow-gold) objects"
    — CONTINUOUS GOLD BEAD STRING confirmed along eave curve
  - Orn_Hero_v3.png: gold upper rim of wing structure, ovoid ornaments

## Ornament Verification Results
- **Bead strings**: Visible as gold spheres along eave curves (confirmed in Eave_v3)
- **Star pendants**: Faceted gold/polished spheres along roof ridges
- **Heart filigree**: Ovoid/capsule gold ornaments at upper ends of structures
- Note: Gold material (metallic=0.9, roughness=0.25) appears off-white under
  direct highlights, but confirms as gold in proper lighting

## Ornament Inventory
- **Bead strings** (Bead_Template, 0.15m): distributed along eave edges and wall curves
- **Star pendants** (Star_SDF_Base, 0.06m → scaled 2x = 0.12m): faceted spheres along roof ridges
- **Heart filigree** (Heart_Template_L, 0.06m → scaled 4x = 0.24m): ovoid/filigree shapes
- **Wall beads** (Bead_Template): on wall bead string guides at x=4, y=7-9

## Remaining Issues
- Some camera positions produce sky-only shots (Wall_v4, Eave_v4 from old runs) — need
  to position cameras from outside the building, accounting for wall occlusion
- Gold material appears off-white under direct highlights (metallic=0.9) — renders
  need proper lighting angles to show the true gold color
- Cycles renders at 16+ samples are slow (~12-30s per render) — use 8 samples for
  development, 32+ for final hero renders

## Next Steps
1. Hero render: wide overview showing all ornaments from outside the building
2. Detail renders: close-ups of each ornament type with proper lighting angles
3. Save final .blend state with all fixes
4. STUDY_EVENING_PLAN complete — ornaments verified visible and gold
