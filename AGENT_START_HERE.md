# Melodia Agent Start Here

**Status authority date:** 2026-09-09  
**Purpose:** One current discovery contract for every AI / IDE / remote agent.

> **Do not derive current project state from an old handoff, old roadblock file, old session note, or the absence of a file on `main`.**

## 0. Repository identity — mandatory

Read `REPOSITORY_AUTHORITY.md` before any cross-repo or old-workspace discovery.

Hard rule:

> `fromage3900/EnvironmentPortfolio` is a deprecated **root umbrella Git repo**. The local folder `C:/EnvironmentPortfolio/` itself remains a valid workspace container. Never infer repo authority from the container path.

Active domains are split deliberately:
- game/runtime/capstone → this repository;
- website → `fromage3900/my-site`;
- TD/AE → separate `MelodiaTouchDesigner` Git.

`C:/EnvironmentPortfolio/...` paths may be valid live checkout locations. The rule is about Git boundaries: `BS_GodFile/.git`, `my-site/.git`, and the separate TD repo own their domains; the workspace root must not become a competing authority.

## 0.5 Git — do not spend a day

```text
python Tools/git_ok.py
```

If it prints `git_ok: OK`, Git is not the task. Stop. Do not reconstruct merge history, do not run `Tools/git_health_audit.py` (fsck), and do not write another Git report.

If it FAILs, fix the printed lines only. Protected material masters and both-parent merge drops are CI-gated.

Branch/workstation classification authority: `Docs/Production/BRANCH_WORKSTATION_POLICY.md`. Do not merge/delete a divergent branch merely to make branch count smaller. `collab/laptop/longterm` is the intentional laptop Blender / Geometry Nodes lane.

## 1. Current reading order

Read only this front door before expanding outward:

1. `README.md`
2. `CAPSTONE_NOW.md` for the immediate production queue
3. `Docs/Production/CANONICAL_PROJECT_PIPELINE_2026-09-08.md` for repository/lane/Git authority
4. `Docs/Production/BRANCH_WORKSTATION_POLICY.md` when branches, machines, salvage, or cleanup matter
5. `Docs/Production/SEMESTER_SCOPE_LEDGER_2026.md` for Fall 2026 production priority
6. `Docs/Semester/FALL_2026_ACADEMIC_MATRIX.md` when academic requirements are involved
7. `MELODIA_TECHNICAL_VERTICAL_SLICE.md`
8. `CURRENT_STATE.md`
9. `_VERTICAL_SLICE_SCOPE.md`
10. `TODO.md`
11. `Docs/Art/VISUAL_REFERENCE_INDEX.md` when art / design / modeling / environment references matter
12. `Docs/WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md` when world-building, chapter authoring, cymatics, or TouchDesigner visual work
13. `Docs/Production/HUMBER_LAB_PRIMARY_WORKSTATION_2026.md` for semester workstation/render decisions
14. `SYSTEM_MAP.md` + `DATA_FLOW.md` only when architecture detail is required

Everything under dated Handoffs, Reviews, Research, Archives, old queues, and old roadblock files is **context/evidence**, not automatic current authority.

Root files stamped `HISTORICAL` or replaced with archive stubs are memory, not status. Current score is `TODO.md`. Current slice scope is `_VERTICAL_SLICE_SCOPE.md`. Capstone/TD contracts stay live and are not historical.

Before trusting or rewriting status, run:

```text
python Tools/front_door_health.py --brief
```

`--ci` is the PR gate (contradictions). `--age` is the Monday reminder: production source moved and `CURRENT_STATE.md` was not refreshed. The tool does not rewrite docs and does not merge branches.

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

## 4. Fall 2026 workstation rule

**Humber labs are the primary interactive semester workstation. The home Windows PC is the render/bake/long-job worker. The ASUS Nitro laptop is auxiliary.** All machines use `main` as the shared baseline unless the owner explicitly assigns a feature branch.

At Humber, start with `.\deploy\humber_lab_bootstrap.ps1 -Mode Check`; authorized preparation uses `-Mode Prepare -IConfirmAuthorizedUse`, which delegates to the existing safe sync contract and the `HumberSemester` LFS profile.

The home PC should consume explicit render/bake jobs through `.\deploy\render_worker.ps1`; render-worker mode must not invent project edits.

A handoff is not complete until the relevant commit is pushed and the receiving machine's sync state is safe.

**Never equate “not on main” with “not committed,” but never equate a branch with current truth either.**

As of 2026-09-08, `main` is the only canonical production baseline. Superseded September 8 docs/fix branches have been reconciled into current main state. Recovery-only branches may remain for deliberate extraction; they are not task queues and must never be merged wholesale.

The authoritative branch classes/workstation rules are in `Docs/Production/BRANCH_WORKSTATION_POLICY.md`; the September reconciliation receipt remains in `Docs/Reports/BRANCH_CANONIZATION_2026-09-08.md`.

`collab/laptop/longterm` is intentionally preserved for laptop Blender / Geometry Nodes production. It is neither current runtime truth nor disposable stale history. Promote useful work selectively; never wholesale-merge or auto-delete it.

Before declaring laptop/recovery work absent, compare the relevant branch to current `main` and extract only the specific unique artifact with provenance.

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

`CAPSTONE_NOW.md` owns the immediate owner queue. The rules below are scope constraints, not an invitation to create a second task list.

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

---

## ♬ Choral Sheep / Chladni Fleece / Nikki Cymatics

If the task mentions **Choral Sheep**, **Chladni Fleece**, **Nikki Cymatics**, **Sheep lookdev**, or Sheep **TouchDesigner / Geometry Nodes** presentation, stop broad repo discovery and open:

`Docs/References/ChoralSheepCapstone/AGENT_CONTEXT.md`

Preserve these locks:

- Board 06 + the two committed Sheep WebPs are the owner-approved visual lock;
- final Sheep lookdev / P0 proof uses the approved Nikki-derived Cymatics material (`MI_ChoralSheep_Body` → `M_Master_Toon_Character`, Chladni as a child, not a replacement shader);
- C++ owns gameplay truth; Blueprint / material / Niagara / TD present it;
- `collab/laptop/longterm` is the intentional laptop Blender / Geometry Nodes lane — inspect and promote in scoped batches; never wholesale-merge or delete it as stale.

Do not reparent Sheep off `M_Master_Toon_Character`. The Nikki **character** master `M_Master_Nikki.uasset` is restored on `main` as a protected EnvSandbox showcase/glitter asset; it is not the Sheep body parent.
