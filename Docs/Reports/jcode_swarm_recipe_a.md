# jcode Recipe A — SQA verify overview

**Outcome:** done  
**Role:** SQA (light-swarm stand-in on Windows UE box)  
**Date:** 2026-08-11  
**Validation:** filesystem inventory of `deploy/run_verify.ps1` + `deploy/_mcp_verify_*.py`; PhoneOps INDEX link check  
**Blockers:** none for docs recipe. Live interactive jcode worker spawn not required for A (docs-only).

## WEB hygiene (coordinator reconcile)

- `Docs/PhoneOps/INDEX.md` already links `JCODE_SWARM_PIPELINE.md` as **Implemented**.
- Harness pointers present: `.jcode/README.md`, `.\deploy\start_jcode_swarm.ps1`.
- No `wix/` redesign performed.

## What `deploy/run_verify.ps1` covers

Headless Blender verify runner (`--factory-startup` always). Modes: `all` | `world` | `overhaul` | `os`.

Invokes `deploy/_mcp_verify_all.py`, which dispatches:

| Mode | Script | Role |
|------|--------|------|
| `overhaul` | `_mcp_verify_overhaul.py` (~19KB) | Surreal overhaul checks |
| `world` | `_mcp_verify_world.py` (~42KB) | World / surreal_world checks |
| `os` | `_mcp_verify_os.py` (~31KB) | Surreal OS checks |
| `blender` (via all) | `_mcp_verify_blender_5_2.py` (~3KB) | Blender 5.2 MCP sanity |
| (related) | `_verify_escher_hero_builders.py` | Escher hero builders (sibling, not in Mode enum) |

Requires Blender at `C:\Program Files\Blender Foundation\Blender 5.1\` (or 4.2 fallback).

## Paths touched

- `Docs/Reports/jcode_swarm_recipe_a.md` (this file)
- No `Content/` or `Plugins/` binary edits
