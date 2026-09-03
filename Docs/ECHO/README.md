# Echo Topological Gate System

## What is this?

The Echo gate layer tracks **what is actually true** about the Melodia integration
through a ledger of dated pass/fail observations. Every stage — from proposal
through promotion — must produce a `Saved/gate_ledger.json` row before it is
believed. No document alone carries truth.

As of 2026-08-13, the Echo system operates in **two topological chapters**,
defined by a DAG in `specs/echo_topo.json`:

- **Chapter 1 — First Dream** is the linear gameplay chain: sanctuary dialogue →
  departure → dream traversal → JRPG encounter → typed result → save. It is
  complete; the four completion gates (runtime, save_load, repeat_consume,
  package_launch) plus a promote gate form the root layer.
- **Chapter 2 — Ecosystem expansion** fans out across independent lanes once
  Chapter 1 promotes: environment art, portfolio website, audiovisual (TouchDesigner),
  and Second Dream narrative expansion.

## Topological scheduling

The DAG is processed by `Tools/echo_topo.py` (Kahn's algorithm). Gates with
**in-degree 0** (no unmet predecessors) are *eligible*. Each gate is classified
into a model_router lane:

| Lane         | model_router task class | Agents that run here                  |
|--------------|------------------------|---------------------------------------|
| `gameplay`   | `code`                 | gameplay engineers, C++/Blueprint     |
| `code`       | `code`                 | pipeline, build, compile              |
| `author`     | `author`               | narrative, dialogue, Quill            |
| `vision`     | `vision`               | render captures, screenshots          |
| `audit`      | `audit`                | verification, sweep, lint             |
| `review`     | `review`               | benchmark, research                   |
| `orchestrator`| `orchestrator`        | lane_dispatcher, promote decisions    |

## Commands

```bash
# Full DAG readiness matrix (all gates, PASS/FAIL/OPEN, predecessors listed)
python Tools/echo_run.py topo eligible

# Topological sort order
python Tools/echo_run.py topo order

# Classify eligible gates into model lanes for agent dispatch
python Tools/echo_run.py topo schedule

# Verify a promote gate's predecessors before recording pass
python Tools/echo_run.py topo check-promote ch1_gameplay.promote
python Tools/echo_run.py topo check-promote ch2_website.site_deploy

# Record a gate with topo metadata (layer + lane)
python Tools/echo_run.py record ch2_website.site_build pass --layer ch2_website --lane code --note "Vite build 0 errors"

# Status with DAG matrix appended
python Tools/echo_run.py status --topo

# Or call the processor directly
python Tools/echo_topo.py summary
```

## Promote gates and the topological rule

A **promote** gate may only record `pass` when **all its predecessors** have a
ledger row with `status=pass`. The scheduler enforces this at record time:
`check-promote <gate-id>` will FAIL if any predecessor is OPEN or FAIL.

The **project-level promote** (`project_promote`) converges all Chapter 2 layer
promotes. It is optional — a release commit may happen per-layer, but the project
commit requires every layer's promote to be PASS.

## Campaign docs

Each gameplay/audiovisual gate links to a campaign doc under `Docs/ECHO/`:

| Campaign | Scope |
|----------|-------|
| `campaign_01_rhythm_damage_delta.md` | Chapter 1 — real-input combat through BP_BattleUI |
| `campaign_02_save_load.md` | Chapter 1 — save slot round-trip |
| `campaign_03_repeat_consume.md` | Chapter 1 — flag/reward/stat idempotency |
| `campaign_04_package_launch.md` | Chapter 1 — packaged build launch |
| `campaign_05_environment_art.md` | Chapter 2 — Blender GN → T3D → UE → render |
| `campaign_06_second_dream.md` | Chapter 2 — narrative expansion beyond First Dream |

## Integration with lane_dispatcher

`Tools/lane_dispatcher.py` reads the **queue** from `_VERTICAL_SLICE_SCOPE.md`
(flat list) and the **DAG** from `specs/echo_topo.json` (topological). The `plan`
command schedules flat queue items; the `topo` subcommand dispatches eligible DAG
nodes to model lanes. Both feed into the same `Saved/dispatch_report.md` output.
