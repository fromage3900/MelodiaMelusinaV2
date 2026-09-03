# Git worktree ownership inventory — 2026-08-24

## Status: RECOVERABLE / OWNERSHIP HOLDS ACTIVE

This is the current ownership manifest. It is not permission to stage all
listed work, delete a checkout, prune reachable objects, or merge a lane. The
repository is intentionally preserving valid concurrent work while each batch
is identified and proven.

## Current topology

| Checkout | State | Disposition |
| --- | --- | --- |
| Main `BS_GodFile` checkout | `main`; documented baseline `cfb2bef8`; dirty | Active integration checkout. Use path-limited commits only. Preserve all unrelated WIP and the foreign staged asset. |
| Detached `.claude/worktrees/magical-williamson-a3534a` checkout | Dirty; ownership not yet adjudicated | **HOLD.** Inventory its branch/reachability and owner before merge, archive, deletion, or metadata changes. |
| `Melodia_ClaireonTest` checkout | Dirty; ownership audit pending | **HOLD.** Keep the Claireon/plugin experiment isolated until provenance, build scope, and intended branch are confirmed. |
| Former `_pr_wt/pr5` registration | Stale metadata; checkout directory absent | Metadata was pruned after the absence was verified. No live worktree content was deleted. |

The two HOLD rows are not defects. A dirty worktree can be healthy when its
owner and recovery path remain known. Deleting it to improve a status summary
would be data loss, not maintenance.

## Main-checkout boundaries

- The main checkout contains mixed WIP from asset, plugin, Blender/worldgen,
  Gaea, gameplay-tooling, and documentation lanes.
- `A_MannFix_Walk.uasset` is already staged and belongs to a separate asset
  batch. Do not unstage, amend, or absorb it from a docs/Git-health lane.
- Hook/ignore plumbing landed at `70212962`; August 24 documentation remains a
  separate safe batch.
- No push has been performed. At the documented baseline, `main` was twelve
  commits ahead and zero behind fetched `origin/main`.

## Required ownership audit for each held worktree

Record all of the following before changing its lifecycle:

1. Exact path, current commit, branch or detached state, and configured remote.
2. Tracked modifications, staged paths, untracked files, and LFS-backed paths.
3. Human or lane owner, intended destination, and whether equivalent work is
   already reachable from a protected remote.
4. A recoverable backup or published ref that was independently verified.
5. The proposed action: preserve, commit in place, transplant to an isolated
   branch, archive, or delete.
6. Explicit owner approval for any delete, prune, history rewrite, or
   destructive cleanup.

If any item is unknown, keep the worktree on HOLD.

## Safe batch order

1. Current status docs: August 24 Git health, worktree inventory, overall
   status, index, and session routing.
2. Existing convergence/tool commits: review their exact outgoing range; do
   not amend them with current WIP.
3. Binary/asset batches: one owned concern at a time, with LFS validation and
   lock policy applied before publication.
4. Secondary worktrees: only after the ownership audit produces a reviewed
   disposition.

## Forbidden shortcuts

- No broad `git add`, `git checkout -- .`, `git restore .`, `git reset
  --hard`, `git clean`, blanket stash, or index rewrite.
- No worktree removal, branch deletion, object/LFS pruning, garbage collection,
  history rewrite, force push, or incomplete LFS push without the approvals and
  recovery evidence in [Git batch discipline](GIT_BATCH_DISCIPLINE.md).
- No claim that a clean object database proves gameplay, runtime, or package
  correctness.

The superseded August 23 manifest remains useful as a historical lane map, but
its paths and branch facts are not current authority.
