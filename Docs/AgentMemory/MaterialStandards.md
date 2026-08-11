# Material Standards

## Current Pillars

- Mesh/prop/trimsheet surfaces use `M_Master_Toon_Universal`.
- Terrain look-dev uses `M_Master_Toon_Landscape_HeightBlend`.
- Water look-dev uses `M_Water_Master_Grand_v6`.
- New environment looks should prefer material instances over new master materials.

## Manifest Fields

Every portfolio-facing material should expose:

- `material_name`
- `parent_master`
- `shader_family`
- `material_type`
- `parameter_groups`
- `output_maps`
- `preview_path`
- `status`
- `purpose`
- `source_module`

## Allowed Theme Work

- Japanese/Sakura-themed materials and material instances are allowed as reusable look-dev assets.
- Do not place or compose those materials in L_SakuraPath without explicit human direction.
