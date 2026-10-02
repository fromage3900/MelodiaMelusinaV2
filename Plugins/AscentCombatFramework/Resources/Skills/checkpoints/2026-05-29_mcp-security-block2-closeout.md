# Checkpoint: MCP Security Hardening + Block-2 Close-Out

**Date:** 2026-05-29
**Branch:** plugin `pi/harness` · inso `main`
**Summary:** Hardened the native MCP server (C++) — off-by-default `bEnableMCPServer`, per-request bearer + Host/Origin (DNS-rebinding) auth, game-thread duration timer, no-copy UTF-8 decode — and closed **Block 2**: the UE Realm now loads as an OMP **plugin** (`--extension` + `--plugin-dir`) with a skill + agent, all live-verified. A checkpoint review then found a **CRITICAL header-split auth bypass** (documented below, not yet fixed).

## Files Changed

### Plugin (C++) — security hardening, commit `c2b0b03c`
- `Source/AscentAIAgent/Private/ACFMCPServer.{h,cpp}` — `Authorize()` (bearer + Host/Origin), game-thread timer, `IsModuleLoaded` guard, no-copy UTF-8 decode, const handlers
- `Source/AscentAIAgent/Public/AscentAIAgentSettings.h` — `bEnableMCPServer` (off), `MCPServerPort`, `MCPAuthToken`
- `Source/AscentAIAgent/Private/AscentAIAgentSubsystem.{h,cpp}` — gate on `bEnableMCPServer`; port/token from settings

### Inso (TS) — Block-2 close-out (pushed to `insodimension/inso`)
- `src/cli.ts` — load realm as plugin: `--extension` + `--plugin-dir`; `registerRealmMCPProvider`; `inso update`; removed the `customDirectories` shim
- `packages/realm-sdk/src/mcp-provider.ts` (+ index) — `registerRealmMCPProvider()` (realm-declared MCP as OMP provider `inso-realms`)
- `extensions/ue/skills/create-blueprint-class/SKILL.md` — first UE skill
- `extensions/ue/agents/blueprint-architect.md` — first UE agent persona
- `test/{skills,agents}-check.ts` — discovery via the real `--plugin-dir` path
- `docs/design/00-mental-model.html` — "Realm extends Plugin"; B2 → done; MCP :56571 (Edge C done)

## What's Working
- **Native MCP server** `:56571` — off by default; when enabled, per-request bearer + Host/Origin auth; 110-tool catalog; game-thread timer/WARNING.
- **UE Realm = OMP plugin** — `--extension` (connectRealm: commands/prompts/setup) + `--plugin-dir` (skills/, agents/); `registerRealmMCPProvider` owns the `ue-editor` MCP source (no `mcp.json` mutation).
- **Live end-to-end verified** — one inso session: 110 `mcp__ue_editor_*` tools; agent called `ue_sys_project_info` → ACFSample / 5.7.4 / ACF 4.1.1; skill `ue:create-blueprint-class` + agent `blueprint-architect` discovered.

## What's Not Working / Known Issues
> **CRITICAL found by this checkpoint's review — FIXED + verified the same session** (header-split bypass; see handoff Known Issues + the follow-up security commit). Re-entrancy guard + constant-time compare also shipped. Recorded here as the historical finding.
- **CRITICAL · security — header-split auth bypass.** UE's HTTP server splits header values on commas (`HttpConnectionRequestReadContext.cpp:323`); `GetHeader()` returns only `Values[0]`. So `Host: 127.0.0.1,evil.com` and `Origin: http://127.0.0.1,http://evil.com` pass the loopback checks → DNS-rebinding defense bypassed. Also duplicate header lines. **Fix:** validate ALL header values and reject multi-valued `Host`/`Origin` (`ACFMCPServer.cpp` `GetHeader`/`Authorize`). The curl battery only tested single-value headers, so it missed this.
- **WARNING · threading — re-entrancy crash.** `ExecuteCommand` runs inside the HTTP tick; a tool that pumps the game thread (`CompileBlueprint`/`SavePackage`) under a concurrent 2nd request can re-enter the listener → engine `check(AwaitingProcessing)` (`HttpConnection.cpp:183/219`). Fix: re-entrancy guard returning a JSON-RPC error.
- **WARNING · security — non-constant-time token compare** (`ACFMCPServer.cpp:239`) — `FString::Equals` leaks a per-byte timing oracle (loopback-local). Add a constant-time compare.
- **WARNING · perf — success flag re-parses the whole tool result** (`:392`). Return structured success from `ExecuteCommand` instead of re-parsing the JSON.
- **WARNING · perf — `tools/list` re-copies/re-serializes the 110-tool catalog every call** (`:344-350`). Cache the serialized body in `LoadToolCatalog`.
- **NOTE** — bracket-less `Host: ::1` (no port) fails closed (interop, not a hole); `MakeHttpError` Printf-builds JSON un-escaped (safe today, fixed literals); `MCPAuthToken` plaintext at rest (consistent with `RelayAuthToken`); `bEnableMCPServer` is init-only (restart to toggle, like the TCP bridge); no CORS/OPTIONS (by design).
- **Doc discrepancy** — `00-mental-model.html` says "124 tools"; catalog file + live server both serve **110** (independently confirmed). Reconcile.

## Review Findings

### Code Review (ue-performance-reviewer)
Strong: Architecture 9, Code quality 9, Security 8, Maintainability 9. No CRITICAL from this pass. WARNING: non-constant-time token compare. NOTES: no-CORS-by-design, plaintext token at rest, init-only enable flag. Many positive confirmations (RAII dtor, `TWeakObjectPtr` subsystem, `GetHttpRouter(...,true)` correct, no-copy decode correct, off-by-default wired right).

### Documentation (doc-updater)
`docs/handoff.md` + plugin `CLAUDE.md` verified **accurate** for the implemented state — no edits needed. Re-confirmed 110 tools, security settings, Block-2 done. (Ran before the security review surfaced the CRITICAL.)

### Performance / Threading / Security (ue-performance-reviewer)
Found **CRITICAL #1 (header-split auth bypass)** by tracing the engine source — the must-fix. Plus WARNINGs: re-entrancy crash, constant-time compare, success re-parse, `tools/list` caching. Verified clean: raw-`this` lifetime (subsystem-owned, `Stop()` unbinds in dtor on the game thread), the timer, game-thread single-threading, off-by-default decoupled from `bAutoStartTCPBridge`, missing-Host rejection, IPv6 bracket/port-strip.

## Next Steps
1. **Fix CRITICAL #1** (header-split bypass) — all-values check + reject multi-valued Host/Origin; extend the curl battery with comma-joined/duplicate-header cases; rebuild + re-verify.
2. **Fix WARNING — re-entrancy guard** (latent crash on heavy tools).
3. Constant-time token compare; structured `ExecuteCommand` return (kills the success re-parse); cache `tools/list` body.
4. Reconcile the "124" vs **110** tool-count doc discrepancy.
5. **Block 3** — compose `acfRealm` into the UE realm; port the 7 ACF skills (`ueBp*`→`ue_bp_*`).
