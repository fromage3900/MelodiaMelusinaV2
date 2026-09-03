---
name: unreal-materials
description: Use when creating, editing, or inspecting Unreal Engine materials via Monolith MCP. Covers PBR setup, graph building, material instances, templates, HLSL nodes, validation, and previews. Triggers on material, shader, PBR, texture, material instance, material graph.
---

# Unreal Material Workflows

**63 material actions** via `material_query()`. Discover first: `monolith_discover({ namespace: "material" })`

## Key Parameters

- `asset_path` -- material asset path (NOT `asset`)

## Action Reference

### Read (21)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `get_all_expressions` | `asset_path` | List all expression nodes |
| `get_expression_details` | `asset_path`, `expression_name` | Node properties and pins |
| `get_expression_connections` | `asset_path`, `expression_name` | Input/output connections |
| `get_full_connection_graph` | `asset_path` | Complete topology |
| `get_material_parameters` | `asset_path` | All scalar/vector/texture params |
| `get_material_properties` | `asset_path` | Settings: blend_mode, shading_model, domain, two_sided, usage. Works on UMaterial + UMaterialInstance |
| `get_compilation_stats` | `asset_path` | VS/PS instruction counts, samplers, compile status |
| `get_layer_info` | `asset_path` | Layer/blend stack |
| `list_expression_classes` | `filter`?, `category`? | Available classes (cached) |
| `get_expression_pin_info` | `class_name` | Pin names/types without instance |
| `list_material_instances` | `parent_path`, `recursive`? | All instances (recursive walks chains) |
| `get_function_info` | `asset_path` | Function inputs, outputs, expressions |
| `export_material_graph` / `export_function_graph` | `asset_path`, `include_properties`?, `include_positions`? | Serialize to JSON. `include_properties: false` reduces ~70% |
| `get_function_instance_info` | `asset_path` | MFI parent chain, 11 override types |
| `get_thumbnail` | `asset_path`, `save_to_file`? | Use `save_to_file: true` (base64 wastes context) |
| `validate_material` | `asset_path`, `fix_issues`? | Broken connections, unused nodes |
| `render_preview` | `asset_path`, `uv_tiling`?, `preview_mesh`? | Compile + preview (tiling check at 3x/5x) |
| `get_texture_properties` | `asset_path` | sRGB, dims, compression, recommended_sampler_type |
| `check_tiling_quality` | `asset_path` | Detect tiling issues, missing anti-tiling/macro variation |
| `preview_texture` | `asset_path`, `resolution`?, `output_path`? | Texture preview + full metadata |

### Instance (5)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `get_instance_parameters` | `asset_path` | All overrides: scalar, vector, texture, static switch |
| `set_instance_parameters` | `asset_path`, `parameters` array of `{name, type, value}` | Batch-set, single recompile |
| `set_instance_parent` | `asset_path`, `new_parent` | Reparent (reports lost/kept params) |
| `clear_instance_parameter` | `asset_path`, `parameter_name`, `parameter_type`? | Remove override (`"all"` clears everything) |
| `save_material` | `asset_path`, `only_if_dirty`? | Save to disk |

### Function (9)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `create_material_function` | `asset_path`, `type`?, `description`?, `expose_to_library`? | Create function/layer/layer_blend |
| `build_function_graph` | `asset_path`, `graph_spec` | Build with typed I/O (same spec as build_material_graph) |
| `set_function_metadata` | `asset_path`, `description`?, `expose_to_library`?, `library_categories`? | Update metadata |
| `delete_function_expression` | `asset_path`, `expression_name` | Remove expression(s), comma-separated |
| `update_material_function` | `asset_path` | Recompile + cascade to referencing materials |
| `create_function_instance` | `asset_path`, `parent`, overrides? | Create MFI with param overrides |
| `set_function_instance_parameter` | `asset_path`, `parameter_name`, value | Set MFI override |
| `layout_function_expressions` | `asset_path` | Auto-arrange function graph |
| `rename_function_parameter_group` | `asset_path`, `old_group`, `new_group` | Rename param group |

### Write (23)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `auto_layout` | `asset_path` | Topological-sort layout (UMaterial + UMaterialFunction) |
| `create_material` | `asset_path`, `blend_mode`?, `shading_model`?, `two_sided`? | Create empty material |
| `build_material_graph` | `asset_path`, `graph_spec`, `clear_existing`? | Build from JSON spec (fastest) |
| `create_custom_hlsl_node` | `asset_path`, `code`, `inputs`?, `additional_outputs`? | Add Custom HLSL |
| `update_custom_hlsl_node` | `asset_path`, `expression_name`, `code`?, `inputs`?, `additional_outputs`? | Edit HLSL without rebuild |
| `replace_expression` | `asset_path`, `expression_name`, `new_class`, `preserve_connections`? | Swap node in-place |
| `rename_expression` | `asset_path`, `expression_name`, `new_desc` | Set label (Desc) |
| `duplicate_expression` | `asset_path`, `expression_name`, `offset_x`?, `offset_y`? | Duplicate (no connections) |
| `move_expression` | `asset_path`, `expression_name`/`expressions`, `pos_x`, `pos_y`, `relative`? | Reposition (batch OK) |
| `set_material_property` | `asset_path`, `blend_mode`?, `shading_model`?, `two_sided`? | Short or prefixed enums |
| `set_expression_property` | `asset_path`, `expression_name`, `property_name`, `value` | Property on expression |
| `connect_expressions` | `asset_path`, `from_expression`, `to_expression`/`to_property` | Wire nodes or to output |
| `disconnect_expression` | `asset_path`, `expression_name`, `input_name`?, `target_expression`?, `output_index`? | Remove connections |
| `delete_expression` | `asset_path`, `expression_name` | Delete node |
| `delete_expressions` | `asset_path`, `expression_names[]` | Batch delete nodes |
| `clear_graph` | `asset_path`, `preserve_parameters`? | Remove all expressions (optionally keep params) |
| `create_material_instance` | `asset_path`, `parent_material` | Create MIC |
| `set_instance_parameter` | `asset_path`, `parameter_name`, `scalar_value`/`vector_value`/`texture_value` | Set instance param |
| `duplicate_material` | `source_path`, `dest_path` | Duplicate |
| `recompile_material` | `asset_path` | Force recompile |
| `import_material_graph` | `asset_path`, `graph_json`, `mode`? | Import from JSON |
| `begin_transaction` / `end_transaction` | `transaction_name`? | Undo group |

### Batch (4)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `batch_set_material_property` | `asset_paths`, `properties` | Same props to multiple materials |
| `batch_recompile` | `asset_paths` | Recompile multiple, returns instruction counts |
| `import_texture` | `source_file`, `dest_path`, `compression`?, `srgb`?, `max_size`? | Import from disk |
| `preview_textures` | `asset_paths[]`, `per_texture_size`?, `output_path`? | Contact sheet of multiple textures |

### Compound (1)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `create_pbr_material_from_disk` | `material_path`, `texture_folder`, `maps`, `blend_mode`?, `shading_model`?, `material_domain`?, `two_sided`?, `max_texture_size`?, `opacity_from_alpha`? | Import PBR textures + create material + build graph + compile. Maps keys: basecolor, normal, roughness, metallic, ao, height, emissive, opacity |

## PBR Workflow

**CRITICAL:** `build_material_graph` requires a `graph_spec` wrapper. Spec goes INSIDE `graph_spec`.

```
// Create + build graph
material_query({ action: "create_material", params: {
  asset_path: "/Game/Materials/M_Rock", shading_model: "DefaultLit"
}})
material_query({ action: "build_material_graph", params: {
  asset_path: "/Game/Materials/M_Rock", clear_existing: true,
  graph_spec: {
    nodes: [
      { id: "TexBC", class: "TextureSample", props: { Texture: "/Game/Textures/T_Rock_D" }, pos: [-400, 0] },
      { id: "TexN", class: "TextureSample", props: { Texture: "/Game/Textures/T_Rock_N", SamplerType: "Normal" }, pos: [-400, 200] },
      { id: "TexORM", class: "TextureSample", props: { Texture: "/Game/Textures/T_Rock_ORM" }, pos: [-400, 400] }
    ],
    outputs: [
      { from: "TexBC", from_pin: "RGB", to_property: "BaseColor" },
      { from: "TexN", from_pin: "RGB", to_property: "Normal" },
      { from: "TexORM", from_pin: "G", to_property: "Roughness" },
      { from: "TexORM", from_pin: "B", to_property: "Metallic" }
    ]
  }
}})
```

**graph_spec fields:**
- `nodes[]` -- `{ id, class, props?, pos? }`
- `custom_hlsl_nodes[]` -- `{ id, code, description?, output_type?, inputs?, additional_outputs?, pos? }`
- `connections[]` -- `{ from, to, from_pin?, to_pin? }` (inter-node)
- `outputs[]` -- `{ from, from_pin?, to_property }` (to material output)

`clear_existing: true` clears expressions but preserves material properties. Blend mode warnings are informational (connection made but inactive until mode matches).

### One-Shot PBR from Disk
```
material_query({ action: "create_pbr_material_from_disk", params: {
  material_path: "/Game/Materials/SIGIL/M_BloodConcrete",
  texture_folder: "/Game/Textures/SIGIL/BloodConcrete",
  maps: { basecolor: "D:/output/basecolor.png", normal: "D:/output/normal.png", roughness: "D:/output/roughness.png" },
  max_texture_size: 2048
}})
```

For decals: add `blend_mode: "Translucent"`, `material_domain: "DeferredDecal"`, `opacity_from_alpha: true`.

## Editing Existing Materials

Inspect first: `get_all_expressions` + `get_full_connection_graph`. Wrap in `begin_transaction`/`end_transaction` for undo. Use `export_material_graph` to snapshot before destructive changes (`include_properties: false` reduces ~70%).

## Tiling Quality Checklist

Before finalizing any material that uses tiling textures, verify ALL of these:

1. **Macro variation applied?** Add world-space noise overlay on BaseColor (strength 0.1-0.3) and Roughness (multiply by 0.8-1.2 range). Use FluidNinja `T_LowResBlurredNoise_sRGB` at UV scale WorldPosition * 0.0003-0.001.
2. **UVs broken with noise offset or world-position blend?** Base UVs must not feed directly into TextureSample without transformation.
3. **Previewed at 3x tiling?** Use `render_preview` to check appearance at high repetition count. Tiling should not be obvious at 3x3.
4. **`MF_AntiTile_IqOffset` used for organic/terrain textures?** Apply Iq's 2-sample offset technique (cheapest proper anti-tiling, ~15 instructions). See `Docs/references/materials/anti-tiling.md` for HLSL and alternatives (hex tiling for large surfaces).
5. **FluidNinja noise textures used for macro variation?** Recommended: `/Game/FluidNinjaLive/Textures/T_LowResBlurredNoise_sRGB` (color), `/Game/FluidNinjaLive/Textures/T_MultilevelNoise1` (roughness).

## AI Introspection (editor:: actions)

For AI agents reasoning about materials without round-tripping through `render_preview`:

- `editor_query("inspect_material_pbr", { asset_path })` — pure reflection walk of `UMaterialInterface`. Classifies texture params by name (basecolor/normal/roughness/metallic) and detects ORM/ARM/MRA channel packing. Returns structured JSON, no render.
- `editor_query("capture_material_grid", { material_paths: [...] })` — N material instances (1-16) side-by-side under shared lighting; auto-grid `ceil(sqrt(N))` columns. Returns one PNG.
- `editor_query("capture_scene_preview", { asset_path, asset_type: "material" })` — single-material preview render.

See `monolith_guide(section="recipes")` entries "Visual introspection — going beyond thumbnails" and "Reading asset structure without rendering".

## Rules

- Graph editing only works on base Materials, not MICs
- Always `validate_material` after graph changes
- `build_material_graph` is fastest for complex graphs (single JSON)
- Use `render_preview` or `get_thumbnail` with `save_to_file: true` (no base64)
- `get_compilation_stats` catches runaway instruction counts after changes
