---
name: unreal-debugging
description: Use when debugging Unreal Engine issues via Monolith MCP — build errors, editor log searching, crash context, Live Coding builds, and common UE error patterns. Triggers on build error, compile error, crash, log, debug, stack trace, assertion.
---

# Unreal Debugging Workflows

**13 editor diagnostic actions** via `editor_query()`. Discover with `monolith_discover({ namespace: "editor" })`.

## Action Reference

| Action | Purpose |
|--------|---------|
| `trigger_build` / `live_compile` | Live Coding compile. `live_compile` accepts `wait` (bool) |
| `get_build_errors` | Compile errors/warnings. Params: `since`, `category`, `compile_only` |
| `get_build_status` | Build in progress / succeeded / failed |
| `get_build_summary` | Stats across recent builds |
| `search_build_output` | Search build output by pattern |
| `get_recent_logs` | N most recent log entries |
| `search_logs` | Search by pattern, category, verbosity |
| `tail_log` | Latest log entries (like `tail -f`) |
| `get_log_categories` | All active log categories |
| `get_log_stats` | Error/warning counts by category |
| `get_compile_output` | Structured compile report: result, time, errors, patch status |
| `get_crash_context` | Crash dump, stack trace, system info |

## Workflows

### After modifying C++
```
editor_query({ action: "trigger_build", params: {} })
// Wait ~10s for Live Coding
editor_query({ action: "get_build_errors", params: {} })
```

### Investigate a crash
```
editor_query({ action: "get_crash_context", params: {} })
editor_query({ action: "search_logs", params: { pattern: "Fatal", limit: 20 } })
```

### Find specific log output
```
editor_query({ action: "search_logs", params: { pattern: "MyActor", category: "LogTemp", verbosity: "Warning" } })
```

## Common Error Patterns

- **LNK2019/LNK2001:** Missing module in `.Build.cs`. `DeveloperSettings` is separate from `Engine`.
- **Include path errors:** Use `source_query("search_source", ...)` to find correct header. Note: `get_include_path` does NOT exist as an action.
- **Live Coding limits:** Header changes (new members, class layout) require editor restart + UBT build. Only `.cpp` body changes work.
- **Package errors:** `CreatePackage` with same path returns existing in-memory package.

## Reflection Intelligence (context while root-causing)

When a bug is in unfamiliar territory, the Reflection Intelligence (RI) namespaces give deterministic, $0-LLM context before you start guessing. Scope: project game module + project plugins.

- **`cppreflect_query`** — inspect the reflected surface of the suspect class: `get_uclass`, `list_uproperties`, `list_ufunctions`, `find_interface_impls`, `find_class_specifier` / `list_class_specifiers`.
- **`network_query`** — when the bug is replication-shaped: `list_replicated_classes`, `list_rpc_functions`, `list_onrep_handlers`, and `audit_unbalanced_onreps` (a `ReplicatedUsing=OnRep_X` with no matching handler is a classic replication-bug source).
- **`decision_query`** — surface prior architectural decisions for the buggy area before "fixing" something that was a deliberate choice: `list_decisions` (filter by `path_filter`), `get_decision`, `find_supersession_chain`, `find_referent_decisions`, `list_stale`.
- **`risk_query`** — locate the danger zones: `get_hotspot_score` / `get_release_window_hotspots` (churn+complexity), `get_cochange_pairs` (files that historically change together — likely co-affected), `get_file_churn`, `list_conditional_gates` (find `#if WITH_*` regions that may be gating the bug out).

## Tips

- Log buffer: 10,000 entries, 5 build histories
- Use `search_logs` with category filters to reduce noise
- `get_build_summary` shows trends -- useful for spotting regressions
- Combine with `source_query` for engine internal errors
- `risk_query("get_cochange_pairs")` predicts which other files a fix may need to touch
- After changing C++ reflection structure, `reflect_query("rebuild_reflection_index")` refreshes the RI tables (project-only)
