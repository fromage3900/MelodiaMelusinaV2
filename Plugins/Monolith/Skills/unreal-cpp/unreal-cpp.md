---
name: unreal-cpp
description: Use when writing or debugging Unreal Engine C++ code via Monolith MCP — engine API lookup, signature verification, include paths, source reading, class hierarchies, config resolution. Triggers on C++, header, include, UCLASS, UFUNCTION, UPROPERTY, Build.cs, linker error.
---

# Unreal C++ Development Workflows

**~18+ source actions** via `source_query()`, **6 config actions** via `config_query()`.

```
monolith_discover({ namespace: "source" })
monolith_discover({ namespace: "config" })
```

## Source Actions

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `search_source` | `query` | Find symbols across engine source |
| `read_source` | `symbol` | Read engine source for a symbol |
| `get_class_hierarchy` | `symbol` | Inheritance tree |
| `find_callers` | `symbol` | Who calls this function |
| `find_callees` | `symbol` | What this function calls |
| `find_references` | `symbol` | All references to a symbol |
| `get_module_info` | `symbol` | Module dependencies, build type |
| `get_symbol_context` | `symbol` | Definition + surrounding context |
| `read_file` | `file_path` | Raw engine source file |
| `get_include_path` | `symbol` | Canonical `#include` for a symbol (Public/Classes/Internal includable; Private warns) |
| `get_signature` | `symbol` | Exact overload signature(s) — declaration-read, body-free |
| `check_deprecations` | `symbols` | Batch deprecation status (version/message/kind) from the deprecation index |
| `verify_symbols` | `symbols` | Batch pre-flight: existence + include + signature + deprecation per symbol in one call |
| `find_example_usage` | `symbol` | Ranked real call-site examples (±3 context lines), `prefer` engine/project, cursor-paged |
| `suggest_build_cs_deps` | `file_path` | Required Build.cs modules + missing deps for a file (works on uncommitted files) |
| `lint_header` | `file_path` | Regex UHT-gotcha lint of a header (works on UNINDEXED files); findings `{rule_id, line, message, severity}` |
| `generate_class_stub` | `parent`, `class_name`, `module` | UCLASS-derived `.h`/`.cpp` stub pair as TEXT (never writes; generated.h last, `<MODULE>_API`) |
| `trigger_reindex` | -- | Full engine source re-index |
| `trigger_project_reindex` | -- | Incremental project-only re-index |

## Common Workflows

```
// Find and read an API
source_query({ action: "search_source", params: { query: "ApplyDamage" } })
source_query({ action: "read_source", params: { symbol: "UGameplayStatics::ApplyDamage" } })

// Learn idiomatic usage from Epic's code
source_query({ action: "find_callers", params: { symbol: "UPrimitiveComponent::SetCollisionEnabled" } })

// Resolve config/CVar
config_query({ action: "resolve_setting", params: { file: "DefaultEngine", section: "/Script/Engine.RendererSettings", key: "r.Lumen.TraceMeshSDFs" } })
config_query({ action: "explain_setting", params: { setting: "r.DefaultFeature.AntiAliasing" } })
```

## Build.cs Gotchas

| Error | Fix |
|-------|-----|
| `LNK2019` for `UDeveloperSettings` | Add `"DeveloperSettings"` module (separate from `Engine`) |
| `LNK2019` for any UE type | Check module with `get_module_info`, add to Build.cs |
| Missing `#include` | Use `search_source` to find correct header -- never guess |
| Template instantiation | Check if type needs `_API` export macro |

## UE 5.7 Notes

- `FSkinWeightInfo`: `uint16` for `InfluenceWeights` (not uint8), `FBoneIndexType` for bones
- `CreatePackage` with same path returns existing in-memory package -- use unique names
- Live Coding: `.cpp` body changes only -- header changes require editor restart + UBT build

## Reflection Intelligence (structural view of your own C++)

`source_query` reads symbol-level engine + project SOURCE. The Reflection Intelligence (RI) namespaces add a higher-level STRUCTURAL view of the reflected surface, mined from UHT artefacts (`*.gen.cpp`) — use these when you want the as-declared UCLASS/UPROPERTY/UFUNCTION shape rather than the raw source text. Scope: project game module + project plugins (default); marketplace plugins gated (`bIndexMarketplacePluginReflection`, off); Epic engine built-ins excluded.

**`cppreflect_query` (6 actions)** — C++ reflection structure:

| Action | Purpose |
|--------|---------|
| `get_uclass` | Parent class, specifiers, source path for a UCLASS |
| `list_uproperties` | UPROPERTY surface of a UCLASS (paginated) |
| `list_ufunctions` | UFUNCTION surface of a UCLASS (paginated) |
| `find_interface_impls` | Every UCLASS that implements a UINTERFACE (C++ only — not BP) |
| `find_class_specifier` | Classes carrying a specifier; token-forgiving (alias map `Blueprintable`->`IsBlueprintBase`, case-insensitive) |
| `list_class_specifiers` | DISTINCT queryable token vocabulary + per-token counts (no params) |

Call `list_class_specifiers` first to learn what `find_class_specifier` can match — the `flags` column stores UHT metadata keys (`IsBlueprintBase`, `BlueprintType`, `Abstract`), NOT raw C++ specifiers.

**`network_query` (4 actions)** — replication/RPC structure of your C++ (covers project plugins): `list_replicated_classes`, `list_rpc_functions` (specifier-based — `FUNC_NetServer`/`Client`/`Multicast`), `list_onrep_handlers`, `audit_unbalanced_onreps` (catch `ReplicatedUsing=OnRep_X` with no `OnRep_X` handler).

**`reflect_query("rebuild_reflection_index")`** — project-only force-rebuild of the RI `reflect_*` tables. Call it after changing C++ reflection structure (new/renamed UCLASS/UPROPERTY/UFUNCTION) when lazy bootstrap + Live-Coding refresh haven't fired. It does NOT touch `source_query`'s engine source index.

## Rules

- **Never guess** `#include` paths or signatures -- always verify with `source_query`
- Search action is `search_source` (not `search`)
- Source index: engine Runtime/Editor/Developer + plugins + shaders (1M+ symbols)
- Use `find_callers` for idiomatic usage, `get_symbol_context` for quick definition lookup
- `cppreflect_query` for the structural reflected view; `source_query` for symbol-level source
- `cppreflect` `source_line` is `0` (UHT drops it) — round-trip through `source_query("search_source")` for real line numbers
- Use `config_query("explain_setting")` before changing unfamiliar CVars
- `check_deprecations` needs a full `source.trigger_reindex` once for engine deprecation rows; before that it returns `index_state: "empty"`
