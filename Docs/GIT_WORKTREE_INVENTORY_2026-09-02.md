# Git worktree ownership inventory — 2026-09-02

## Status: CLOUD CHECKOUT CLEAN / WINDOWS HOLDS UNCHANGED

Supersedes the *routing* of [`GIT_WORKTREE_INVENTORY_2026-08-24.md`](GIT_WORKTREE_INVENTORY_2026-08-24.md)
for cloud agents. The August 24 HOLD rows for secondary Windows checkouts remain
in force until the owner audits them on the SoT machine — this environment cannot
see those paths.

## Current topology (this Cloud Agent)

| Checkout | State | Disposition |
| --- | --- | --- |
| `/workspace` on `cursor/git-health-checkpoint-c2b1` | Matches `origin/main` `8b3d2666` after rebase; path-limited docs/CI work | Active cloud docs/health lane |
| Secondary worktrees | None registered (`git worktree list` → single entry) | N/A |

`deploy/quick-deploy.ps1` may flicker dirty under CRLF/smudge on Linux; the
`cursor/fix-ci-workflows-529c` merge normalizes it. Do not broad-restore the tree.

## Windows SoT holds (still active until owner audit)

Carry forward from 2026-08-24 — **HOLD**, do not delete:

1. Detached `.claude/worktrees/...` checkout (dirty; ownership not adjudicated).
2. `Melodia_ClaireonTest` checkout (dirty; Claireon/plugin experiment).

Required audit fields before lifecycle change: path, commit, branch, dirty/LFS
paths, owner, recoverable ref, proposed action, explicit approval for delete/prune.

## Safe batch order (unchanged)

1. Docs / git-health / branch triage (this lane).
2. Text-only ahead-only merges (toolchain, CI, mara, cymatic specs).
3. Isolated binary/LFS commits only when the owner schedules them.
4. Never absorb foreign staged assets into a docs batch.

## Related

- [`GIT_HEALTH_2026-09-02.md`](GIT_HEALTH_2026-09-02.md)
- [`GIT_BRANCH_TRIAGE_2026-09-02.md`](GIT_BRANCH_TRIAGE_2026-09-02.md)
- [`GIT_BATCH_DISCIPLINE.md`](GIT_BATCH_DISCIPLINE.md)
