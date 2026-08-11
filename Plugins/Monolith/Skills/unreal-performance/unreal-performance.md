---
name: unreal-performance
description: Use when analyzing or optimizing Unreal Engine performance via Monolith MCP — config auditing, material shader stats, draw call analysis, INI tuning. Triggers on performance, optimization, FPS, frame time, GPU, draw calls, shader complexity.
---

# Unreal Performance Analysis Workflows

You have access to **Monolith** with cross-domain performance tools.

## Asset Path Conventions

All asset paths follow UE content browser format (no .uasset extension):

| Location | Path Format | Example |
|----------|------------|--------|
| Project Content/ | `/Game/Path/To/Asset` | `/Game/Materials/M_Rock` |
| Project Plugins/ | `/PluginName/Path/To/Asset` | `/MassProjectile/Materials/M_Example` |
| Engine Plugins | `/PluginName/Path/To/Asset` | `/Niagara/DefaultAssets/SystemAssets/NS_Default` |

**Note:** For project plugins, the path starts with the plugin name as configured in the .uplugin file's "MountPoint" — which defaults to `/<PluginName>/`. Most plugins mount their Content/ folder there directly.

## Key Tools by Domain

### Config Auditing (`config_query`)
```
monolith_discover({ namespace: "config" })
```

| Action | Purpose |
|--------|---------|
| `resolve_setting` | Get the effective value of any CVar/config setting |
| `explain_setting` | Understand what a setting does before changing it |
| `diff_from_default` | See all project customizations vs engine defaults |
| `search_config` | Find settings by keyword |

### Material Performance (`material_query`)
| Action | Purpose |
|--------|---------|
| `validate_material` | Check for errors, unused nodes, broken connections |
| `get_all_expressions` | Count instruction/texture samples per material |
| `render_preview` | Trigger compilation to get shader stats |

### Niagara Inspection (`niagara_query`)

Use `monolith_discover({ namespace: "niagara" })` to see all 41 available actions. Key ones for performance:

| Action | Purpose |
|--------|---------|
| `list_emitters` | List all emitters in a system — check emitter count |
| `list_renderers` | List all renderers on an emitter — check renderer count |
| `get_ordered_modules` | Get modules in a script stage — audit module complexity |
| `get_all_parameters` | Get all parameters — review parameter overhead |
| `get_compiled_gpu_hlsl` | Get compiled GPU HLSL — inspect shader complexity |

**Note:** Niagara actions use `asset_path` as the parameter name (not `system`).

## Common Workflows

### Audit INI performance settings
```
config_query({ action: "diff_from_default", params: { file: "DefaultEngine" } })
config_query({ action: "resolve_setting", params: { file: "DefaultEngine", section: "/Script/Engine.RendererSettings", key: "r.Lumen.TraceMeshSDFs" } })
config_query({ action: "explain_setting", params: { setting: "r.Lumen.TraceMeshSDFs" } })
```

### Check material shader complexity
```
material_query({ action: "get_all_expressions", params: { asset_path: "/Game/Materials/M_Character" } })
material_query({ action: "validate_material", params: { asset_path: "/Game/Materials/M_Character" } })
```

### Audit Niagara effect complexity
```
niagara_query({ action: "list_emitters", params: { asset_path: "/Game/VFX/NS_Blood" } })
niagara_query({ action: "list_renderers", params: { asset_path: "/Game/VFX/NS_Blood", emitter_name: "Emitter0" } })
niagara_query({ action: "get_compiled_gpu_hlsl", params: { asset_path: "/Game/VFX/NS_Blood", emitter_name: "Emitter0" } })
```

### Find expensive config settings
```
config_query({ action: "search_config", params: { query: "Lumen", file: "DefaultEngine" } })
config_query({ action: "search_config", params: { query: "Shadow", file: "DefaultEngine" } })
config_query({ action: "search_config", params: { query: "TSR", file: "DefaultEngine" } })
```

## High-Impact INI Settings

These are the most impactful performance CVars to audit:

| Setting | Impact | Notes |
|---------|--------|-------|
| `r.Lumen.TraceMeshSDFs` | ~1-2ms GPU | Set to 0 if not using mesh SDF tracing |
| `r.Shadow.Virtual.SMRT.RayCountDirectional` | ~0.5ms GPU | 8 is default, 4 is often sufficient |
| `gc.IncrementalBeginDestroyEnabled` | Frame spikes | Enable to eliminate GC hitches |
| `r.StochasticInterpolation` | ~0.5ms GPU | Set to 2 for better perf |
| `r.AntiAliasingMethod` | Varies | TSR handles aliasing — MSAA often redundant |
| `r.Lumen.Reflections.AsyncCompute` | White flash | UE-354891 bug, keep at 0 until 5.7.2 |

## Tips

- Use `explain_setting` before changing any unfamiliar CVar
- `diff_from_default` is the fastest way to see all project customizations
- Material instruction counts from `get_all_expressions` correlate with pixel shader cost
- Use `list_emitters` + `list_renderers` to audit Niagara system complexity
