# Checkpoint: Inso Block 2 — ueExtension + RPC Harness

**Date:** 2026-05-28
**Branch:** pi/harness
**Summary:** Completed Block 2 of the Inso platform: ueExtension with 16 tools across 6 domains wired to UE TCP bridge, RPC test harness with token usage reporting, and disabled the broken agentic_ue MCP server that was flooding OMP with schema errors.

## Files Changed

### Inso repo (Tools/inso/)
- `CLAUDE.md` — added ueExtension docs, RPC harness section, build order
- `test/rpc-test.ts` — RPC test harness (token usage aggregation from message_end events)

### Plugin repo (root)
- `CLAUDE.md` — updated repo structure docs
- `.claude/agents/code-simplifier-cpp.md` — agent config
- `.claude/skills/checkpoint/SKILL.md` — checkpoint skill
- `.gitignore` — updated exclusions
- `.codex/config.toml` — commented out broken agentic-ue MCP server
- `Source/AscentAIAgent/Private/AgenticMCP/Commands/AgenticMCPDataCommands.cpp` — data commands
- `Source/AscentAIAgent/Private/AscentAIAgentSubsystem.cpp` — subsystem changes
- `Source/AscentAIAgent/Private/Commands/UEACFAssetCommands.cpp` — asset commands
- `Content/Configuration/ACF_SampleAttributesInit_DT.uasset` — attribute init data

### External config
- `~/.codex/config.toml` — commented out agentic-ue MCP server (user-global)
- `~/.omp/agent/config.yml` — added tools.discoveryMode: mcp-only

## What's Working

- ueExtension: 16 tools across 6 domains (system, asset, selection, level, blueprint, data)
- RPC test harness: spawn OMP → send prompt → capture tool calls/results → aggregate token usage
- Bridge TCP client with 15s timeout, JSON command/response protocol
- Bridge status monitor in TUI status bar
- OMP tool discovery mode set to mcp-only
- agentic_ue MCP server disabled (broken anyOf schema on animcomp tool)

## What's Not Working / Known Issues

- OMP's `disabledServers` in mcp.json does NOT prevent codex-discovered MCP servers from loading — had to comment out at source
- `tools.discoveryMode: mcp-only` unclear if it actually affects codex-discovered servers (bypassed by codex provider)
- Copy-paste in OMP TUI not supported (Ink framework limitation)
- agentic_ue MCP server at `D:\Gamedev\Dy\Plugins\AgenticUEBridge\Tools\agentic_mcp\` has broken JSON Schema on `agentic_animcomp_get_info` tool (anyOf items not objects) — needs fixing at source

## Review Findings

### Code Review

**Priority issues in C++ bridge code (Source/AscentAIAgent/):**

- **P1-P2 (Duplication):** `FallbackGameplayTagTables` array and `IsConfiguredGameplayTag`/`ResolveGameplayTagForBridge` functions duplicated between `AgenticMCPDataCommands.cpp` and `UEACFAssetCommands.cpp`. Should extract to shared utility.
- **M1 (Memory safety):** Raw `new`/`delete` for `BridgeRunnable` and `ServerThread` in `AscentAIAgentSubsystem.cpp` violates R.11. Should use TUniquePtr or RAII wrapper.
- **P3 (Performance):** `CollectGameplayTags()` called per-request with no caching — loads all DataTables each time.
- **C1 (Correctness):** `MarkEditableObjectChanged` called before property set succeeds in `HandleDaSetProperty`.
- **M2:** Manual `FMemory::Malloc`/`Free` for DataTable rows needs RAII wrapper.
- **S3:** Dead `ServerAddress` member never read.
- **C4:** Near-identical `SetRowFieldsFromJson` and `SetStructFieldsFromJson` functions.

### Documentation

- `docs/handoff.md` — updated with Block 2 completion, 16 tools listed, build order table, RPC harness section
- `Tools/inso/CLAUDE.md` — added ueExtension API docs, RPC test harness usage, updated build order

### Performance / Architecture Review

Confirmed code review findings. Additional notes:

- **W4:** `TObjectIterator` brute-force in `ResolveRowStruct`/`ResolveDataAssetClass` — should use FindObject or cache results.
- **W7:** Static `bInitialized` cache in `GetConfiguredGameplayTagSet()` never refreshes — stale after hot-reload or DataTable changes.
- **Overall scores:** Architecture 7/10, Code Quality 7/10, Performance 7/10, Memory Safety 8/10, Threading 8/10.

## Next Steps

1. **Fix P1-P2 duplication** — extract shared gameplay tag utilities to a common header
2. **Fix M1** — replace raw new/delete with TUniquePtr for BridgeRunnable/ServerThread
3. **Fix P3** — cache CollectGameplayTags result, invalidate on DataTable change
4. **Block 3: acfExtension** — ACF-specific tools (character, abilities, combat, inventory, AI routines)
5. **Fix agentic_ue schema** — fix anyOf in animcomp tool at AgenticUEBridge source
6. **RPC test suite** — build per-tool test cases using the harness
