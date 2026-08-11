# Muse Code Lane — Setup (2026-08-11)

Meta's terminal coding agent (beta, 2026-08-05) powered by Muse Spark 1.2.
Installed in WSL2 Ubuntu. Model runs on Meta's cloud (no local GPU needed).

## Status

- [x] Installed: WSL2 Ubuntu, `~/.local/bin/muse` (launcher + `muse-bin-0.1.0-R708.1`)
- [x] Verified: `muse --version` → Muse Code 0.1.0
- [x] Workspace: `/mnt/c/EnvironmentPortfolio/BS_GodFile` (reads this repo's `AGENTS.md`;
      `muse init` correctly refuses to overwrite it)
- [x] MCP: binary reads `.mcp.json` (Monolith, ueblueprintmcp, ollama, model endpoints auto-wire)
- [x] Auth script staged: `~/.local/bin/muse-login.sh` (device flow, polls, saves token)
- [ ] Auth: Meta account approval — OWNER STEP, not yet completed
- [ ] Smoke test: headless `muse exec` run pending auth

## Auth (owner step — pick one)

1. **Device flow (no Meta developer account needed):**
   In a WSL terminal run `muse-login.sh` — it prints a URL + code, polls, and
   saves the token to `~/.config/muse/auth.json` automatically.
2. **Meta Model API key (for API-key auth):**
   Create a key at developer.meta.com, then either run `/login` in the Muse Code
   TUI or set `META_API_KEY=<key>` (the binary reads this env var).

## Usage

- Interactive TUI: `muse` (needs a real TTY; does not work through piped shells)
- Headless lane run: `muse exec --help` (use for queue tasks; same pattern as other lanes)
- Built-in skills: `plan` (approval-gated plan), `grill` (plan stress-test),
  `git` (never commit unless asked), `import` (resume Claude/Codex/Grok sessions)

## Lane rules (inherited from AGENTS.md)

Same as every lane: queue + scaffolding docs (`_SESSION_HANDOFF.md`, `_TASK_QUEUE.md`),
ledger-gated completion (`Tools/echo_run.py`), one editor instance, never
`git clean` / `checkout -- .`, Monolith `blueprint_query` for Blueprint reads
(never Python glue on skill Blueprints).
