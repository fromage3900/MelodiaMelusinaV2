# Melodia × jcode Swarm Pipeline

**Status:** Implemented (harness in-repo). Run Recipes A/B on the Windows UE box to validate.

Target pattern: [jcode swarm](https://jcode.sh/swarm) — many coding agents in **one repo**, optimistic concurrency, code-shift notifications, coordinator → workers (not N git worktrees by default).

Reference: https://x.com/1jehuang/status/2086858114893279524

## Architecture

```text
Human (phone or desktop)
        │
        ▼
  Coordinator session          ← .jcode/coordinator-bootstrap.md
        │ spawns scoped workers (light-swarm, ≤6)
        ├─► PGA / MPA / PPA / WIA / SQA / WEB / MUSE
        ▼
  Shared MelodiaMelusinaV2 checkout
  (jcode tracks reads/writes → code-shift pings)
        │
        ▼
  Optional: Monolith stdio proxy → UE :9316
```

jcode does **not** replace Unreal/Blender. It is the parallel **repo** coding lane (Python, C++, docs, deploy, `wix/`).

## Companion IDE lanes (not jcode)

| Lane | Tool | Job |
|---|---|---|
| Parallel repo swarm | jcode (this doc) | Coordinator → PGA/MPA/PPA/WIA/SQA/WEB/**MUSE** workers on shared checkout |
| C++ / PIE gameplay | OpenCode inside JetBrains Rider | MelodiaCore edits, build, PIE debug; Rider shortcut **Ctrl+\\** opens OpenCode terminal |
| Meta terminal agent | Muse Code (WSL2 `muse`) | Cloud Muse Spark agent; docs: `Docs/Production/MUSE_CODE_LANE_2026-08-11.md` |

Launch helpers:

- Swarm: `.\deploy\start_jcode_swarm.ps1`
- OpenCode/Muse validate (no UE): `.\deploy\start_opencode_muse_lane.ps1`
- Project OpenCode config: `.opencode/opencode.jsonc` (Monolith/Blender MCP off until editors are live)

Do not run jcode workers and OpenCode/Muse on the same write paths without coordinator ownership.

## Install (Windows UE workstation)

```powershell
irm https://jcode.sh/install.ps1 | iex
jcode login --provider <claude|openai|copilot|gemini|...>

cd <MelodiaMelusinaV2>
# creates ~/.jcode/config.toml from example if missing; installs skills; launches jcode
.\deploy\start_jcode_swarm.ps1
```

Paste [`.jcode/coordinator-bootstrap.md`](../../.jcode/coordinator-bootstrap.md) into the root session.

Manual pieces (if not using the start script):

| Step | Action |
|---|---|
| User config | Copy/merge [`.jcode/config.example.toml`](../../.jcode/config.example.toml) → `%USERPROFILE%\.jcode\config.toml` (`swarm = true`, `concurrency_cap = 6`) |
| Skills | `.\deploy\install_jcode_melodia_skills.ps1` |
| Policy | [`.jcode/swarm-prompt.md`](../../.jcode/swarm-prompt.md) (auto-loaded for swarm) |
| MCP | [`.jcode/mcp.json`](../../.jcode/mcp.json) → `Plugins/Monolith/Scripts/monolith_proxy.bat` (UE must be open) |

More: [`.jcode/README.md`](../../.jcode/README.md)

## Project files

| Path | Purpose |
|---|---|
| `.jcode/swarm-prompt.md` | Role spawn templates + red lines |
| `.jcode/mcp.json` | Monolith stdio MCP proxy |
| `.jcode/config.example.toml` | Swarm/memory/concurrency defaults |
| `.jcode/coordinator-bootstrap.md` | Recipe A/B paste prompt |
| `deploy/start_jcode_swarm.ps1` | One-command launch |
| `deploy/install_jcode_melodia_skills.ps1` | Monolith → `~/.jcode/skills/*/SKILL.md` |
| `deploy/start_opencode_muse_lane.ps1` | Validate OpenCode (+ optional Muse); print Rider shortcuts; no UE |
| `.opencode/opencode.jsonc` | OpenCode project config for Rider lane |
| `Docs/Production/MUSE_CODE_LANE_2026-08-11.md` | Muse Code install/auth status |
| `Docs/Handoffs/TONIGHT_FIRST_DREAM_OPENCODE_2026-08-11.md` | 2026-08-11 prep record (historical — current prep lives in `_SESSION_HANDOFF.md`) |
| `AGENTS.md` §5 | Constitution pointer |

## Loops policy

| Keep | Deprecated for parallel coding wakes |
|---|---|
| `start_surreal_*.ps1`, `start_world_loop.ps1`, `run_verify.ps1` | `deploy/cursor_*_loop.ps1`, `start_cursor_agent_loop.ps1` |

After Recipes A/B pass, do **not** start Cursor wake loops for new parallel work — use jcode swarm.

## Acceptance recipes

### Recipe A — docs (Green) — required

Coordinator spawns WEB + SQA per `.jcode/coordinator-bootstrap.md`.

**Pass when:**

- [ ] Two workers, no overlapping writes
- [ ] `Docs/Reports/jcode_swarm_recipe_a.md` exists (SQA verify overview)
- [ ] Coordinator `/commit` succeeds if there were changes (or clean no-op)
- [ ] No Content/Plugin binary edits

### Recipe B — audits (Yellow) — required

MPA + PPA read-only reports.

**Pass when:**

- [ ] `Docs/Reports/jcode_swarm_recipe_b_mpa.md` and `..._ppa.md` exist
- [ ] No `setup_master_universal.py` regenerate / no `.uasset` writes
- [ ] Completion reports include outcome, paths, validation, blockers

### Recipe C — optional

Single MelodiaCore worker for GS-001/GS-002 after LFS push — do not split one `.cpp` across agents.

## Hard rules

1. Ownership scopes from `AGENT_OWNERSHIP.md` / `.jcode/swarm-prompt.md`
2. No Sakura composition / no `Content/_PROJECT/`
3. One material master editor at a time
4. Swarm v1 avoids bulk LFS asset churn
5. SQA verify before merging production mutations
6. OpenCode/Muse are companion lanes — coordinate write paths with jcode MUSE role; never start UE from `start_opencode_muse_lane.ps1`

## Phone / Cursor cloud

Cursor iOS cloud agents remain the PR/mobile lane (`Docs/PhoneOps/`). jcode gateway + Tailscale phone clients are **v2** (not wired in this pass).

## Non-goals (v1)

- Replacing surreal/world production PowerShell loops
- HTTP MCP in jcode (stdio proxy only)
- Auto-publish / Gumroad
- Duplicate surreal Art Deco PR spam
