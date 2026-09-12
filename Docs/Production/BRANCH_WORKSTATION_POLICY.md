# Branch & Workstation Policy

**Status:** CANONICAL OPERATING POLICY  
**Date:** 2026-09-08  
**Updated:** 2026-09-11  
**Authority:** `main` remains the only canonical game/runtime/capstone branch.

This policy exists to make Git infrastructure boring and predictable.

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

**Current lane contract:** [`LAPTOP_PROCEDURAL_LANE_2026-09-11.md`](LAPTOP_PROCEDURAL_LANE_2026-09-11.md) — Blender 5.2 LTS GN baseline, audio-reactive GN proof, Blender Python automation, ArmorPaint evaluation, and promotion rules back into UE/main.

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

Read [`LAPTOP_PROCEDURAL_LANE_2026-09-11.md`](LAPTOP_PROCEDURAL_LANE_2026-09-11.md) before assigning new laptop procedural work.

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
