# Branch & Workstation Policy

**Status:** CANONICAL OPERATING POLICY  
**Date:** 2026-09-08  
**Updated:** 2026-09-21  
**Authority:** `main` remains the only canonical game/runtime/capstone branch.

This policy exists to make Git infrastructure boring and predictable.

For **current** priorities, blockers, and assigned work, read `CURRENT_STATE.md`. This file defines durable branch/workstation behavior only.

## 0. Production-spine rule

`main` is not a shared scratch branch and no longer functions as an experiment aggregator. It is the green production spine from which authored sessions start and to which proven slices return.

```text
green main
→ one bounded intent
→ one scoped branch
→ author / validate / capture evidence
→ PR + required gates
→ main
→ next bounded intent
```

During an interactive Unreal/Blender session, the checked-out branch must not move underneath live editor state. Do not merge, rebase, reset, or let background agents switch branches while the editor owns unsaved work. Close the editor before integration work.

A stale branch with useful source is never “updated” by wholesale merging current main into its history and then merging it back. Extract the named unique delta onto a fresh-main promotion branch.

## 1. Branch classes

Every non-main branch should be understood as one of these classes before merge or deletion.

### ACTIVE

A current scoped implementation branch.

Expected lifecycle:

```text
main
→ scoped work
→ validation
→ PR
→ required CI
→ merge
→ prune when safe
```
**Promotion subtype.** A stale source/workstation/recovery lane may remain useful, but it is not an active merge target. Promotion means: identify the exact unique files/intent, cut a fresh branch from current green `main`, transplant only those deltas, re-run current gates, then merge the fresh branch. The stale source branch remains provenance until deletion is separately proven safe.


### CANONIZED

Its meaningful work is already contained in `main`.

It may be pruned after verifying:
- zero unique intended work remains;
- no LFS/binary-only artifact would be lost;
- no workstation/recovery role applies.

### WORKSTATION

Intentional parallel production lane associated with a machine or DCC workflow.

Current preserved example:

`collab/laptop/longterm`

This branch is the ASUS laptop Blender / Geometry Nodes / procedural-authoring lane.

**Durable laptop/workstation contract:** [`LAPTOP_PROCEDURAL_LANE_2026-09-11.md`](LAPTOP_PROCEDURAL_LANE_2026-09-11.md). It defines Blender/GN/ArmorPaint boundaries, workstation sync/handoff rules, recovery provenance, and promotion behavior. `LAPTOP_WORK_DISCOVERY_2026-09-04.md` is historical only.

Rules:
- divergence from `main` is not, by itself, a defect;
- never auto-delete it as stale;
- never wholesale-merge it over `main`;
- periodically compare it to `main`;
- promote useful GN/DCC work in scoped branches/PRs with provenance;
- `main` remains runtime truth.

### RECOVERY

Historical or machine-recovery source.

Recovery branches are evidence/salvage stores, not current task queues.

Never wholesale-merge them. Extract a specific unique artifact/change against current `main`.

### OPERATIONAL

Infrastructure branch intentionally outside `main`.

Example:
- `render-queue`

Do not merge/delete merely to reduce branch count.

### UNKNOWN

A branch whose purpose or unique content has not been established.

UNKNOWN is never safe-to-delete by default.

## 2. No branch-count vanity work

A large branch count is not automatically unhealthy.

The health questions are:
- Is `main` canonical?
- Are open PRs understandable?
- Is CI green?
- Are preserved branches classified?
- Are unique assets safe?
- Can a fresh agent find current truth quickly?

Do not spend owner time reducing branch count when those answers are already good.

## 3. Merge discipline

Before merging:
1. understand branch purpose;
2. compare against current `main`;
3. inspect changed files;
4. identify authority touched;
5. check visual/reference impact;
6. check LFS/binary impact;
7. run required CI;
8. merge only the scoped intended work.

Never use a wholesale recovery/workstation merge as a shortcut to “sync everything.”

## 3.1 Production session lifecycle

For lookdev, level dressing, World Compiler work, animation presentation, VFX, or other editor-heavy production:

1. verify current `main` is green and run `python Tools/git_ok.py`;
2. cut one short-lived `feature/<intent>-<date>` branch from current `main`;
3. make LFS-managed assets writable before the first editor save;
4. keep one editor / one writer and freeze branch movement for the interactive session;
5. commit by reviewable visual/system slice, never the whole workstation dirty tree;
6. close the editor before UBT, AE, rebases, merges, or destructive sync;
7. run the lane-specific proof plus Echo/LFS gates;
8. merge the scoped PR, then begin the next session from refreshed green `main`.

Long-lived branches are reserved for explicit WORKSTATION, RECOVERY, or OPERATIONAL roles. A lookdev/worldbuilding feature branch should normally die after its slice lands.

## 4. Cleanup discipline

Repository cleanup is allowed when it:
- removes a concrete integrity risk;
- resolves a real merge/build blocker;
- fixes agent discoverability;
- prevents data loss;
- eliminates a verified duplicate authority.

Repository cleanup is **not** a default task.

Do not open cleanup work solely for:
- formatting;
- branch-count aesthetics;
- broad speculative refactors;
- rewriting old history;
- converting every old note into a new note.

## 5. Workstation roles

### Humber lab

Primary interactive semester workstation.

Use for:
- Unreal iteration;
- interactive review;
- semester production;
- approved authoring sessions.

### Home Windows PC

Render / bake / long-job worker and major Unreal build machine.

Use for:
- long renders;
- heavy bakes;
- closed-editor builds;
- large validation jobs.

### ASUS Nitro laptop

Auxiliary Blender / Geometry Nodes / procedural-authoring workstation.

Use for:
- GN builders;
- Blender source work;
- Blender 5.2 LTS audio/GN procedural experiments;
- Blender Python authoring automation;
- bounded ArmorPaint evaluation;
- DCC experiments;
- on-the-go procedural production.

Read [`LAPTOP_PROCEDURAL_LANE_2026-09-11.md`](LAPTOP_PROCEDURAL_LANE_2026-09-11.md) for durable lane rules before assigning laptop procedural work. Read `CURRENT_STATE.md` for what the laptop is actually doing now.

Its long-term branch is intentionally preserved until a future DCC-repository migration is deliberately chosen. Do not perform that migration during capstone production merely for repository aesthetics.

## 6. Promotion model for DCC work

```text
visual/design lock
→ laptop Blender/GN source
→ validate source/tool
→ identify promotable artifact
→ scoped promotion branch
→ UE import/validation
→ runtime/render evidence
→ main
```

Promote outputs/contracts deliberately. Do not merge stale game-state history alongside them.

## 7. Agent rule

Before any branch merge, deletion, salvage, or “cleanup,” agents must be able to state:

- branch class;
- unique work;
- intended destination;
- evidence that nothing important will be lost;
- why this action helps current production.

If they cannot, leave the branch alone.
