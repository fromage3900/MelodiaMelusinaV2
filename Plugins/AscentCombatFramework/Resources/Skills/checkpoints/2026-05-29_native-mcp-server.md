# Checkpoint: Native C++ MCP Server + Realm SDK

**Date:** 2026-05-29
**Branch:** `pi/harness` (plugin) / `main` (inso)
**Summary:** Defined the **Realm** primitive (`@inso/realm-sdk`), turned the ACF editor into a **native C++ MCP server** (`FACFMCPServer` on `:56571`) serving a 110-tool catalog generated from the realm's Zod schemas, verified the full Inso→MCP→editor loop live, fixed OpenAI-strict schema validity, and decoupled the hand-wired tools so MCP is the sole tool source. Architecture validated against Epic's UE 5.8 first-party `ModelContextProtocol` plugin.

## Files Changed

### Plugin repo — commit `03db7ec0`
- `Source/AscentAIAgent/Private/ACFMCPServer.{h,cpp}` — **new** MCP Streamable-HTTP server (initialize / tools/list / tools/call → `ExecuteCommand`)
- `Source/AscentAIAgent/Private/AscentAIAgentSubsystem.{h,cpp}` — MCP server member + `StartMCPServer`/`StopMCPServer` + Initialize/Deinitialize wiring (`:56571`)
- `Source/AscentAIAgent/AscentAIAgent.Build.cs` — added `HTTPServer` dependency
- `Config/mcp-tools.json` — **new** generated 110-tool catalog (Zod→JSON-Schema)
- `.claude/launch.json` — preview/launch config
- `docs/design/00-mental-model.html` — vision doc: Realm standard, three-layer model, the five edges, Edge C = MCP

### Inso repo — commit `153cdef`
- `packages/realm-sdk/` — **new** SDK: `defineRealm()`, `connectRealm()`, primitive types
- `extensions/ue/realm.ts` — UE realm: declares the `ue-editor` MCP server; **no longer registers tools**
- `extensions/ue/index.ts` — `connectRealm(ueRealm)` (4 lines, was 258)
- `extensions/ue/bridge.ts` — TCP client (ping/sendCommand) — UE-only, for status + slash commands
- `extensions/ue/tools/*.ts` — 110 Zod tool defs (now the **catalog source**, not realm tools)
- `extensions/ue/scripts/gen-mcp-catalog.ts` — Zod → `Config/mcp-tools.json`
- `extensions/ue/{prompts,commands}/*` — UE system prompt, `/ue-status` `/ue-ping`
- `test/{realm-check,mcp-connect-test,mcp-load-test,mcp-discover-test}.ts`
- `CLAUDE.md`, `package.json`, `bun.lock`

## What's Working
- **Realm SDK** compiles a domain Realm to OMP's `ExtensionFactory`. UE realm registers 0 tools (decoupled), declares the MCP server.
- **Native C++ MCP server** on `http://127.0.0.1:56571/mcp` — `initialize` / `tools/list` (110) / `tools/call` → existing `ExecuteCommand` dispatch. Compiles into the shipping plugin (UE 5.7.4).
- **Catalog generation** — `gen-mcp-catalog.ts` emits 110 clean draft-2020-12 schemas from the Zod defs; C++ serves them.
- **End-to-end verified, live editor:** raw MCP client ✅; OMP's MCP client (110 tools, ping) ✅; OMP startup loader via `~/.omp/agent/mcp.json` ✅; the **Inso agent** answered "which map/project + what's in it" → project `ACFSample` (UE 5.7.4, ACF 4.1.1), map `L_UltOpenWorld`, actor census (121 PCGPartitionActor, 16 BP_DemoDisplay, …) ✅.
- **OpenAI-strict schemas** — `z.unknown()`/`z.record(z.unknown())` replaced with typed unions; the `bp_add_variables` 400 is fixed.
- **Forward-compatible:** identical architecture to Epic's UE 5.8 `ModelContextProtocol` plugin (HTTPServer + IHttpRouter + JSON-RPC). On 5.7 we ship our own (Epic's is `NoRedist`); at 5.8 we can adopt Epic's engine plugin — Inso side unchanged (MCP is the contract).

## What's Not Working / Known Issues
- **CRITICAL — game-thread blocking:** the HTTP handler runs `ExecuteCommand` synchronously on the game thread (FHttpServerModule ticks there); heavy tools (`CompileBlueprint`, `SavePackage`, large graphs) freeze the editor 50ms–1s+, and MCP requests serialize. **No timeout** on this path (the TCP path has one).
- **CRITICAL — security:** unauthenticated localhost MCP port exposing ~110 editor-mutating tools (incl. a **Python-exec** surface), auto-started by default, with no auth, no `Origin`/`Host` validation, and no dedicated enable flag. Any local process / browser tab (DNS-rebinding) can drive it. **Ship blocker** for a marketplace plugin.
- **WARNING:** MCP start gated on `bAutoStartTCPBridge` (no separate flag); `MCPPort` hardcoded (no settings/CLI override); `Stop()` doesn't release the listener (guard `IsModuleLoaded("HTTPServer")` for editor-shutdown order); `GetHttpRouter(Port, /*fail*/true)` should be `false` so the null-check governs; raw-`this` handler lambda safe only by single-threading (document invariant); UTF-8 body double-copied.
- **NOTE:** triple JSON pass per `tools/call` (serialize result → reparse for `success` → re-stringify); `const`/`constexpr`/naming nits.
- **Duplication resolved:** running inso loaded both hand-wired `ue_*` and `mcp__ue_editor_*` (~220); Phase 3 removed the hand-wired set.

## Review Findings

### Code Review (ue-performance-reviewer)
Wiring correct end-to-end (catalog names match the command dispatch). Scores: Architecture 7, Code Quality 8, **Correctness 6** (the game-thread hang), Maintainability 8. Positives: RAII destructor, `TWeakObjectPtr`/`TUniquePtr` ownership, Deinitialize order, deliberate no-`StopAllListeners`. Top fix: the game-thread synchronous dispatch.

### Performance / Threading / Security (performance-engineer-cpp)
Confirmed the game-thread CRITICAL (named the offending handlers: `CompileBlueprint`, `SavePackage`). Raised the **security CRITICAL** (unauth port; relay has `RelayAuthToken`, this port has nothing; MCP spec mandates Origin validation + localhost + auth). Honest note: editor mutations must run on the game thread, so heavy tools hitch by design — mitigation is to defer `OnComplete` so the socket loop isn't held + add a duration timer/WARNING.

### Documentation (doc-updater)
Updated `Tools/inso/CLAUDE.md` (Realm + MCP reality: 110 tools via MCP, realm declares the server, `:56571`, build order, Realm SDK section) and the plugin `CLAUDE.md` (connection architecture diagram, port `:56570`→`:56571`, `Config/mcp-tools.json`). Vision doc `00-mental-model.html` already current from earlier this session. `docs/handoff.md` updated separately (this checkpoint).

## Next Steps
1. **Security hardening (ship blocker):** off-by-default `bEnableMCPServer` setting distinct from the TCP bridge; bearer token (`Authorization` check before dispatch, 401 otherwise); `Origin`/`Host` validation (reject non-localhost Host / non-empty Origin) to block browser DNS-rebinding.
2. **Game-thread safety:** defer the MCP `OnComplete` callback (don't hold the socket read loop); wrap `ExecuteCommand` in `FScopedDurationTimer` + log a WARNING past a threshold; document that heavy tools hitch by design.
3. **Quick fixes:** `GetHttpRouter(..., false)`; `IsModuleLoaded("HTTPServer")` guard in `Stop()`; `MCPPort` settings/CLI override; `FUTF8ToTCHAR` no-copy body decode; `const`/`constexpr`/naming cleanup.
4. **Block 3 — ACF sub-realm:** ACF-specific tools/prompts compose into the UE realm; extend the catalog + MCP server with the 17 ACF commands.
5. **Future (UE 5.8):** adopt Epic's `ModelContextProtocol` engine plugin (and `JsonSchemaGenerator` UStruct→schema) when the project moves to 5.8.

## Verification Snapshot
- `bun run test/realm-check.ts` → realm 0 tools, 2 commands, 1 prompt (decoupled) ✅
- `bun run extensions/ue/scripts/gen-mcp-catalog.ts` → 110 tools, clean schemas ✅
- `Build.bat ACFSampleEditor` → Succeeded (ACFMCPServer compiled, DLL linked) ✅
- OMP MCP client + Inso agent drove the live editor ✅
