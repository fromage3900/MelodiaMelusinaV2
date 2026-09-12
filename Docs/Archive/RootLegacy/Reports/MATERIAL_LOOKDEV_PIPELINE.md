# Material Look-Dev Pipeline

This document defines the reusable material/look-dev workflow for the universal environment platform.

## Source Of Truth

- [MATERIAL_PIPELINE.md](MATERIAL_PIPELINE.md) - shader architecture.
- [MATERIAL_SYSTEM_REVIEW.md](MATERIAL_SYSTEM_REVIEW.md) - cleanup priorities.
- [Docs/MATERIAL_NODE_TREE_REVIEW.md](Docs/MATERIAL_NODE_TREE_REVIEW.md) - current node-stack review.
- [Docs/MATERIAL_INTEGRATION.md](Docs/MATERIAL_INTEGRATION.md) - run order and loop notes.

## Master Families

| Master | Role | Status |
|---|---|---|
| `M_Master_Toon_Universal` | Mesh, props, architecture, trimsheets, style families. | Implemented |
| `M_Master_Toon_Landscape_HeightBlend` | Reusable terrain and painted layer look-dev. | Implemented |
| `M_Water_Master_Grand_v6` | Reusable translucent water, shoreline, caustics, stylized ponds/rivers/ocean. | Implemented |
| `M_Master_Impressionist_Toon` | Painterly overlay lane. | Partial |
| `M_SDF_*` family | Experimental/procedural facade and relief studies. | Research/Partial |

## Look-Dev Contract

Each material family should produce:

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

The disk-only producer is:

```text
python Content/Python/material_family_manifest_full.py
```

Outputs:

```text
Saved/Portfolio/Materials/material_family_manifest.json
Saved/Portfolio/MaterialPreviews/previews_manifest.json
```

The second file intentionally matches the current `portfolio_aggregator.py` material input shape.

## Generic Capture Targets

| Family | Expected Preview |
|---|---|
| `MI_Show_*` | Sphere or slab grid in `L_Template`. |
| `MI_Landscape_*` | Ground slab or landscape patch. |
| `MI_GrandWater_*` | Plane with controlled lighting and shoreline context where possible. |
| `MI_Trimsheet_*` / `MI_ZenTrim_*` | Flat trim panel plus angled usage sample. |
| Baroque/Zen theme instances | Neutral prop or wall panel, not Sakura scene dependent. |

## Recommended Run Order

```text
python Content/Python/material_family_manifest_full.py
python Content/Python/portfolio_output_layout.py
python Content/Python/compile_render_plates.py
python Content/Python/portfolio_aggregator.py
```

For UE-backed rebuilds/audits, follow `Docs/MATERIAL_INTEGRATION.md` and close the editor before headless runs when file locks are likely.

## Review Checklist

- Universal master still compiles.
- Parameter groups remain organized.
- Latest master update is reflected in docs or reports.
- Material manifest includes all canonical starter/theme families available from source tables.
- Missing preview images are explicit `status` fields, not silent omissions.
- No Sakura level edits are required for generic material proof.
