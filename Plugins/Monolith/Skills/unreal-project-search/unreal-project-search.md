---
name: unreal-project-search
description: Use when searching for assets, references, or dependencies across an Unreal project via Monolith MCP — FTS5 full-text search, asset discovery, reference tracing, type filtering. Triggers on find asset, search project, asset references, where is, dependencies.
---

# Unreal Project Search Workflows

You have access to **Monolith** with a deep project index via `project_query()`.

## Discovery

```
monolith_discover({ namespace: "project" })
```

## Asset Path Conventions

All asset paths follow UE content browser format (no .uasset extension):

| Location | Path Format | Example |
|----------|------------|--------|
| Project Content/ | `/Game/Path/To/Asset` | `/Game/Materials/M_Rock` |
| Project Plugins/ | `/PluginName/Path/To/Asset` | `/MassProjectile/Materials/M_Example` |
| Engine Plugins | `/PluginName/Path/To/Asset` | `/Niagara/DefaultAssets/SystemAssets/NS_Default` |

**Note:** For project plugins, the path starts with the plugin name as configured in the .uplugin file's "MountPoint" — which defaults to `/<PluginName>/`. Most plugins mount their Content/ folder there directly.

## Action Reference

| Action | Params | Purpose |
|--------|--------|---------|
| `search` | `query` (string) | Full-text search across all indexed assets, nodes, variables, parameters |
| `find_references` | `asset_path` (string) | Find all assets that reference a given asset |
| `find_by_type` | `asset_type` (string), `module`? (string) | List all assets of a specific type, optionally filtered by plugin/module |
| `get_asset_details` | `asset_path` (string) | Detailed metadata for a specific asset |
| `get_stats` | _(none)_ | Index statistics — asset counts by type, module_breakdown by plugin, index freshness |

## FTS5 Search Syntax

The `search` action uses SQLite FTS5 under the hood. Key syntax:

| Pattern | Meaning |
|---------|---------|
| `BP_Enemy` | Match exact token |
| `BP_*` | Prefix match |
| `"BP_Enemy Health"` | Exact phrase |
| `BP_Enemy OR BP_Ally` | Either term |
| `BP_Enemy NOT Health` | Exclude term |
| `BP_Enemy NEAR/3 Health` | Terms within 3 tokens |

## Common Workflows

### Find any asset by name
```
project_query({ action: "search", params: { query: "BP_Player*" } })
```

### Find all Blueprints in the project
```
project_query({ action: "find_by_type", params: { asset_type: "Blueprint" } })
```

### Find all assets referencing a material
```
project_query({ action: "find_references", params: { asset_path: "/Game/Materials/M_Skin" } })
```

### Find references to a plugin asset
```
project_query({ action: "find_references", params: { asset_path: "/MassProjectile/Materials/M_Example" } })
```

### Get detailed metadata for an asset
```
project_query({ action: "get_asset_details", params: { asset_path: "/Game/Blueprints/BP_Player" } })
```

### Check index health
```
project_query({ action: "get_stats", params: {} })
```

### Find all Niagara systems
```
project_query({ action: "find_by_type", params: { asset_type: "NiagaraSystem" } })
```

### Find assets by variable or parameter name
```
project_query({ action: "search", params: { query: "Health" } })
```

## Supported Asset Types

The index covers these types for `find_by_type`:
- `Blueprint`, `WidgetBlueprint`, `AnimBlueprint`
- `Material`, `MaterialInstance`, `MaterialFunction`
- `NiagaraSystem`, `NiagaraEmitter`
- `AnimSequence`, `AnimMontage`, `BlendSpace`
- `Texture2D`, `StaticMesh`, `SkeletalMesh`
- `DataTable`, `CurveTable`, `SoundWave`

## Project-Intelligence Search Complements

`project_query` and `source_query` search assets and source symbols. The Reflection Intelligence (RI) namespaces are deterministic, $0-LLM search complements that answer higher-level structural and historical questions about the project's own artefacts. Scope: project game module + project plugins (marketplace gated, Epic engine built-ins excluded).

- **`cppreflect_query`** — search the C++ reflection graph: `find_class_specifier` (every UCLASS carrying a specifier — token-forgiving, alias-maps `Blueprintable`->`IsBlueprintBase`, case-insensitive; pair with `list_class_specifiers` to discover the queryable token vocabulary), `find_interface_impls` (every C++ UCLASS implementing a UINTERFACE), plus `get_uclass` / `list_uproperties` / `list_ufunctions` for a specific class.
- **`decision_query`** — find architectural decision records mined from the markdown corpus: `list_decisions` (filter by `path_filter` / `status` / `min_confidence`), `get_decision`, `find_supersession_chain`, `find_referent_decisions`, `list_stale`.
- **`risk_query`** — find git-derived hotspots and co-change relationships: `get_release_window_hotspots`, `get_hotspot_score`, `get_cochange_pairs`, `get_file_churn`, `list_conditional_gates`.

## Tips

- The index is built on first launch and auto-updates — use `monolith_reindex()` to force rebuild
- FTS5 search covers asset names, node names, variable names, parameter names, and comments
- Use `find_references` to understand dependency chains before deleting or renaming assets
- Combine with domain-specific tools: search first, then inspect with `blueprint_query`, `material_query`, etc.
- `get_stats` shows last index time — if stale, trigger `monolith_reindex()`
- RI reflection tables refresh on Live Coding / lazy first-call; force a project-only rebuild with `reflect_query("rebuild_reflection_index")`
- Call `monolith_discover('namespace')` to list action names + one-line descriptions (terse by default). For an action's full param schema, call `describe_query action_schema` (or pass `detail=true` to inline all schemas)
