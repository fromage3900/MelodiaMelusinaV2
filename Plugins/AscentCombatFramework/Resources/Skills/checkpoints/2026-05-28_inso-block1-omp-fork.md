# Checkpoint: Inso Block 1 — OMP Fork + MCP Schema Fix

**Date:** 2026-05-28
**Branch (plugin):** `pi/harness`
**Branch (inso):** `main` (initial commit)
**Summary:** Set up the Inso agent platform with a full OMP engine fork, wired global `inso` CLI, and fixed MCP tool schema validation errors that broke OpenAI models.

## What Happened

### Block 1: OMP Engine Fork (Tools/inso/)

Copied the full OMP (Oh My Pi) engine v15.5.4 into `Tools/inso/omp/` as a fork (not submodule). Wired it as a Bun workspace so all `@oh-my-pi/*` packages resolve locally.

Key setup steps:
- Fetched prebuilt `pi-natives` win32-x64 `.node` binary from npm (no Rust toolchain needed)
- Generated `docs-index.generated.ts` for `--help` to work
- Created `src/cli.ts` entry point with manual `.env` loading (env vars survive global `bun link`)
- Set default model to `anthropic/claude-sonnet-4-6` in `~/.omp/agent/settings.json`
- Upgraded Bun from 1.3.5 to 1.3.14 (required by OMP)

**Verified:** `inso --version` → `omp/15.5.4`, `inso -p "prompt"` streams response from Claude, ~467 models available across 4 providers, MCP servers auto-discovered from `~/.codex/config.toml`.

### MCP Tool Schema Fix (AgenticUEBridge)

OMP auto-discovered the `agentic-ue` MCP server from `~/.codex/config.toml` and connected automatically. OpenAI models failed with 400 errors because the Python MCP server (`D:\Gamedev\Dy\Plugins\AgenticUEBridge\Tools\agentic_mcp\server.py`) used bare `list` type hints in ~47 tool functions.

FastMCP/Pydantic converts bare `list` → `{"type": "array", "items": true}`. OpenAI's strict JSON Schema validation rejects `"items": true` (must be an object).

**Fix:** Changed all 47 bare `list` params to properly typed:
- 30 → `list[dict]` (array-of-objects params)
- 14 → `list[str]` (names/paths/IDs)
- 1 → `list[int]` (indices)
- 1 → `list[dict | str]` (bp_remove_components mixed type)
- 1 → `list[str]` (source_textures)

**Not committed** in AgenticUEBridge — changes are local only. The user chose to commit/push only the Inso repo.

## Files Changed

### Inso repo (Tools/inso/) — initial commit
- `src/cli.ts` — global CLI entry point
- `package.json` — workspace config with full OMP catalog
- `bunfig.toml` — Bun config
- `.gitignore` — excludes node_modules, .env, dist
- `CLAUDE.md` — platform instructions
- `omp/` — full OMP engine fork (2787 files, 762k lines)

### AgenticUEBridge (D:\Gamedev\Dy\Plugins\AgenticUEBridge) — uncommitted
- `Tools/agentic_mcp/server.py` — 47 bare `list` → typed list params

## What's Working

- `inso` CLI runs globally from any directory
- OMP engine fully operational (agent loop, streaming, tools, sessions)
- Multi-provider: Anthropic, OpenAI, OpenRouter, ZAI
- MCP server auto-discovery from `~/.codex/config.toml` and `.mcp.json`
- `agentic-ue` MCP server connects and tools register
- OpenAI models no longer 400 on MCP tool schemas (after server restart)

## What's Not Working / Known Issues

- AgenticUEBridge server.py type fixes not committed (different repo, user deferred)
- Model selector action menu UX: Enter always shows action menu instead of direct select (deferred)
- No Inso-specific extensions wired yet (ue, acf, saas)

## Next Steps

1. **Block 2: Plug ueExtension** — write ExtensionFactory connecting to UE TCP bridge on port 56570
2. **Block 3: Plug acfExtension** — ACF-specific tools and prompts
3. **Block 4: Plug saasExtension** — credits and billing
4. Model selector UX improvement (deferred from this session)
5. Commit AgenticUEBridge server.py fixes when working in that repo
