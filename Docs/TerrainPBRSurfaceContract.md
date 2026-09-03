# Terrain PBR Surface Contract

New terrain maps belong under:

`/Game/Melodia/Art/Materials/Landscape/<Surface>/Textures/`

Use the following surface IDs for the Zen Forest launch set:

| Material role | Surface ID | Required assets |
| --- | --- | --- |
| Rock | `ZenForest_Stone` | `T_Land_ZenForest_Stone_BC`, `_N`, `_ORM`, `_H` |
| Moss ground | `ZenForest_MossGround` | `T_Land_ZenForest_MossGround_BC`, `_N`, `_ORM`, `_H` |
| Soil / leaf litter | `ZenForest_Soil` | `T_Land_ZenForest_Soil_BC`, `_N`, `_ORM`, `_H` |
| Compacted path | `ZenForest_CompactedPath` | `T_Land_ZenForest_CompactedPath_BC`, `_N`, `_ORM`, `_H` |

## Export rules

- All maps must tile seamlessly in X and Y at the intended world scale. Test a 3x3 repeat before import.
- `BC`: albedo only; no baked directional light, AO, contact shadows, bloom, vignette, or color grading. Import sRGB on.
- `N`: tangent-space normal, OpenGL/Y+ convention. Import as `TC_Normalmap`, sRGB off.
- `ORM`: `R=ambient occlusion`, `G=roughness`, `B=metallic`. Terrain is dielectric, so B should normally be black. Import as `TC_Masks`, sRGB off.
- `H`: linear 0–1 height; black is recess, white is raised surface. It must describe material relief, not the landscape’s world height. Import as `TC_Masks`, sRGB off.
- Use 2K as the Standard tier source. Reserve 4K only for Hero-only, close-camera material instances; do not use it as the general landscape default.

## Art direction

- **Stone:** cool mineral value structure, broad planar breakup, moss-friendly recesses, no dense photographic pebble noise.
- **Moss ground:** soft olive/blue-green pigment pools over earthen substrate; small fallen-leaf and root hints, but no repeated leaf stamps.
- **Soil:** warm umber with damp darkening and compressed organic fibres; do not use brick, paving, or cracked plaster as soil.
- **Path:** compacted earth with fine grit and occasional embedded stone; it must remain lower-contrast than the destination/focal landmarks.

The material system treats these as physically distinct layers. Keep their median values separated: rock is coolest and highest roughness, moss is softer and moderately rough, soil is warm/dark, path is the most compact and slightly smoother. Magical color, sparkle, and Wonder Mask stay in the master and are not baked into these maps.

## Gameplay surface contract

After importing the texture library, run `setup_landscape_surface_physics.py` and then
`setup_landscape_layers.py`. Rock, Moss ground, Soil, and Path then carry distinct
physical surfaces for footsteps, landings, decals, particles, and acoustic traces.
