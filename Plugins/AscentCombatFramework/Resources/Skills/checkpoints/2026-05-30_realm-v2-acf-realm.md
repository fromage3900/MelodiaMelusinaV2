# Checkpoint: Realm v2 + ACF Realm

**Date:** 2026-05-30
**Branch (plugin):** `pi/harness`
**Branch (inso):** `feat/flip-shimmer`
**Summary:** Realm v2 redesign — auto-injected status tool, TCP bridge deleted (pure MCP), ACF realm scaffolded as Block 3, `mcpTool()` moved to SDK, realm types extend OMP types, dependencies replace subRealms, MCP realm tags for tool claiming.

## Files Changed

### Realm SDK (`packages/realm-sdk/src/`)
- `types.ts` — v2 RealmDefinition: dependencies, skills/agents paths, agentTeams stub, RealmMCPServer extends MCPServerConfig, isUrlServer() type guard
- `define.ts` — mcpTool() with realm tag, removed subRealm validation
- `connect.ts` — flat realm loading, no tree walking, auto-injects status tool
- `status-tool.ts` — mandatory auto-built: pings MCP servers via tools/list, counts tools with realm tag filtering, discovers skills/agents
- `mcp-ping.ts` — pingMCP() uses tools/list (domain-agnostic, not ue_sys_ping)
- `mcp-provider.ts` — uses isUrlServer(), only registers servers with URLs
- `index.ts` — exports pingMCP, mcpTool, isUrlServer, MCPToolInfo, RealmAgentTeam

### UE Realm (`extensions/ue/`)
- `realm.ts` — removed subRealms, removed custom status(), added skills/agents paths
- `bridge.ts` — DELETED (was TCP client, replaced by pingMCP in SDK)
- `commands/ue-status.ts` — uses pingMCP from SDK
- `prompts/ue-system.ts` — "MCP server on port 56571" (was TCP)
- `scripts/gen-mcp-catalog.ts` — outputs realm tags per tool

### ACF Realm (`extensions/acf/`) — NEW (Block 3)
- `realm.ts` — dependencies: ["ue"], mcp claim via realm: "acf"
- `index.ts` — connectRealm(acfRealm)
- `commands/acf-status.ts` — /acf-status
- `prompts/acf-system.ts` — combat domain context
- `tools/{actions,combos,assets}.ts` — 18 MCP tool schemas tagged realm: "acf"
- `skills/` — /create-combat-character, /setup-combat-system
- `agents/` — @combat-designer

### Plugin C++
- `UEBlueprintCommands.{h,cpp}` — added FAgenticMCPGraphAnalysis command surface
- `Config/mcp-tools.json` — 128 tools (110 UE + 18 ACF tagged with realm field)

### Skills + Docs
- `.claude/skills/realm-manager/SKILL.md` — realm scaffolding skill for Claude Code
- `Tools/inso/skills/realm-manager/SKILL.md` — same skill for Inso TUI
- `Tools/inso/CLAUDE.md` — "Extend, never duplicate" rule added
- `docs/design/00-mental-model.html` — updated for Realm v2

## What's Working
- Realm v2 types and connectRealm() pipeline
- Auto-injected {name}_status tool per realm (mandatory, SDK-built)
- pingMCP() — domain-agnostic MCP health check via tools/list
- mcpTool() with realm tags — catalog generator outputs tags
- UE realm: 110 tools, ● CONNECTED, auto-status with skills/agents
- ACF realm: depends on ue, claims 18 tools via realm:"acf", auto-status
- 128 MCP tools in catalog (110 UE + 18 ACF)
- realm-manager skill works in both Claude Code and Inso TUI
- Mental model doc updated for v2

## Known Issues
- W2 (review): auth token + MCP URL duplicated between ue/realm.ts and ue/commands/ue-status.ts — should extract to shared config
- W3 (review): mcp-provider asRealmList iterable detection is fragile
- W4 (review): type→transport field rename in toMCPServer not documented
- N4 (review): mcp-provider toMCPServer drops auth/oauth fields
- C++ W1: static TSet not used in IsBpAuthorCommand/IsStructEnumCommand/IsGraphAnalysisCommand (perf)
- C++ W2: bp_add_switch_pin in routing set has no handler (pre-existing)
- C++ W3: FAgenticMCPGraphAnalysis missing AGENTICMCP_API macro

## Review Findings

### TypeScript Code Review
- **C1 FIXED:** Shared isUrlServer() type guard replaces duplicated getMCPUrl unsafe casts
- **C2 FIXED:** pingMCP uses tools/list instead of hardcoded ue_sys_ping
- **W1 FIXED:** Dead claimServers loop removed
- **W5 FIXED:** Server object carried through Promise.all, no find+! assertion
- W2, W3, W4, N1-N4: Deferred (low risk)

### C++ Review
- No CRITICAL issues
- W1 (static TSet), W2 (dead entry), W3 (missing macro): Deferred (low risk, pre-existing patterns)
- Dispatch pattern matches established codebase conventions

## Next Steps
- Fix remaining warnings (W2 shared config, W3 iterable detection, C++ W1 static sets)
- Block 3 content: populate ACF skills and agents with real recipes
- Block 4: Infrastructure Gate (saasExtension)
- Consider: realm.json manifest for distribution (Edge E)
