# Melodia Agent Start Here

**Status authority date:** 2026-09-04  
**Purpose:** One current discovery contract for every AI / IDE / remote agent.

> **Do not derive current project state from an old handoff, old roadblock file, old session note, or the absence of a file on `main`.**

## 1. Current reading order

Read only this front door before expanding outward:

1. `README.md`
2. `MELODIA_TECHNICAL_VERTICAL_SLICE.md`
3. `CURRENT_STATE.md`
4. `_VERTICAL_SLICE_SCOPE.md`
5. `TODO.md`
6. `Docs/Art/VISUAL_REFERENCE_INDEX.md` when art / design / modeling / environment references matter
7. `Docs/Production/LAPTOP_WORK_DISCOVERY_2026-09-04.md` when work may have come from the laptop or another workstation
8. `SYSTEM_MAP.md` + `DATA_FLOW.md` only when architecture detail is required

Everything under dated Handoffs, Reviews, Research, Archives, old queues, and old roadblock files is **context/evidence**, not automatic current authority.

## 2. Freshness rule

Use this precedence:

```text
current source / assets / current branch state
    >
2026-09-04 front-door docs
    >
explicit current evidence packets
    >
dated plans / handoffs
    >
research / historical audits
```

A dated document saying a system is missing, broken, blocked, or unproven is **not** permission to repeat that claim without checking current source/evidence.

Before saying “the project does not work” or “system X is missing”:

- inspect the current implementation;
- inspect `MELODIA_TECHNICAL_VERTICAL_SLICE.md`;
- inspect `Docs/Evidence/P0_EXPLORATION_WARDROBE_GLIDE_PORTAL_PROBE_2026-08-31.md`;
- inspect recent commits and relevant non-main branches;
- state the evidence level: source-built, live-proven, restart-proven, or packaged-proven.

## 3. Current runtime reality

The project is not a blank or nonfunctional prototype.

Current evidence records a working chain across music/challenge → reward → wardrobe equip → Glide capability → world/traversal unlock, plus canonical save → full process restart → load → wardrobe state restoration.

Focused evidence also records passing Wardrobe, P0, Shorewake, and traversal capability-contract tests.

Do **not** regress the project back to an August “nothing is live” interpretation.

The still-open boundary is deeper persistence/idempotency/package closure, not whether the core runtime exists.

## 4. Laptop / multi-workstation discovery rule

**Both workstations should use `main` as the shared baseline unless the owner explicitly assigns a feature branch.** The recovered V7 house baseline was promoted to `main` via PR #82.

Before opening Blender/Rider/Unreal on either workstation, run `.\deploy\sync_workstation.ps1`. A handoff is not complete until its report says `sync_state = synced`.

**Never equate “not on main” with “not committed.”**

As of 2026-09-04:

- `recovery/laptop-main-20260904` is **13 commits ahead of main and 0 behind** at discovery time.
- It contains current Melusina House Geometry Nodes/addon work, V7 build scripts, house Blender files, and `SESSION_NOTES_2026-09-04.md`.
- It also contains broad export/quarantine deletions, so **do not merge it wholesale**.
- Older `collab/laptop/*` branches are diverged and remain discovery/extraction sources.

Before declaring laptop work absent, check the branch discovery document and compare relevant branches with `main`.

## 5. Visual reference rule

For character, environment, Monolith, wardrobe, lookdev, concept, or modeling work, start at:

`Docs/Art/VISUAL_REFERENCE_INDEX.md`

Do not search random dated docs first and do not fabricate a missing reference path.

The visual index distinguishes:

- committed canonical images;
- committed diagrams / technical visual targets;
- branch-only or uncommitted references;
- planned boards that were never actually committed.

## 6. Research / handoff rule

Research is allowed to be broad. It is **not** a task queue.

Dated handoffs are historical memory. They may contain contradictions that were correct at the time.

Do not:
- revive an August task solely because an August handoff says it is open;
- rebuild a system because an old audit says it is absent;
- use `_ROADBLOCKS_2026-07-31.md` as current project status;
- use deleted `_SESSION_HANDOFF.md` / `_TASK_QUEUE.md` as current authority;
- read the entire repo before doing a scoped task.

## 7. Current production bias

Until the professor-facing vertical slice is safe:

**protect / polish**
- First Dream / Sea Above
- environment presentation
- rhythm interaction
- Wardrobe → Glide → traversal
- Starskiff only where stable
- canonical persistence
- character presentation

**stabilize, do not expand**
- repeat-load / idempotency
- package proof
- UI single-writer proof
- Starskiff state

**freeze unless explicitly requested**
- new gameplay frameworks
- second save/progression/traversal authorities
- speculative AI/toolchain expansion
- new broad systems that do not improve the review slice

## 8. When the repo disagrees with itself

Do not average contradictory prose.

Resolve contradictions by:
1. current source / branch comparison;
2. newest explicit evidence;
3. current front-door docs;
4. ask only if an owner decision is genuinely required.

**Current front door = truth routing. Historical docs = memory. Runtime/source = authority.**


---

## ♬ Melusina House / Blender Geometry Nodes

If the task mentions **Melusina's House**, **Geometry Nodes**, **round Baroque architecture**, **house foundation**, or any `MEL_mh_*` builder, stop broad repo discovery and open:

`MELUSINA_HOUSE_GN_START_HERE.md`

Then run:

```powershell
python Tools/verify_melusina_house_gn_catalog.py
```

Important naming rule:

```text
MEL_mh_* = live registered Melodia Studio builder
GN_MH_*  = optional scene-local wrapper / historical plan alias
```

Do not infer missing implementation from a missing `GN_MH_*` name.
