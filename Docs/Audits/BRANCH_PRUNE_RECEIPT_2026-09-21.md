# Branch prune receipt — 2026-09-21

Matched pair with the 2026-09-21 deletions. Deleted refs stay recoverable by their recorded tip
SHA until a gc runs. **No `git gc` was run and none should be run until this receipt ages out.**
Proof method for every entry: `git diff --name-status origin/main <ref>` → zero `A` rows
(no file exists on the branch that is absent from main), re-run immediately before deletion.
Branches are squash/PR-merged by convention here, so sha-ancestry is not the test; content is.

## Deleted remote refs

| Ref | Tip SHA (recoverable) | Last commit | Proof |
|---|---|---|---|
| `fix/runtime-gameplay-closure-recut-20260921` | via PR #281 merge | 2026-09-21 | PR #281 merged CLEAN/green; `gh pr merge --delete-branch` |
| `docs/production-spine-paradigm-20260921` | `c40891b97c63bd09b96b07a89cf9bd051e7b1e6c` | 2026-09-21 | A-files=0; lane landed via PR #277 |
| `fix/runtime-gameplay-closure-20260921` | `1ca49d08d1568570eeebe0b928a6b46347f30b1e` | 2026-09-21 | A-files=0; superseded by its own recut (#281) |
| `fix/retire-front-door-suite-20260921` | `2a1aeb1ca1a9a00305e79ca0f7abbd665dc6cb7e` | 2026-09-21 | A-files=0 |
| `docs/canonize-converged-project-state-20260920` | `8ee74be46a69830cdec11030fdda3fd204a6fc0a` | 2026-09-20 | A-files=0 |
| `feature/house-gn-paris-20260920` | `594041d99b62c51714f3728deadb7479488bb13f` | 2026-09-20 | A-files=0; not the merge-base of the live recut lane (verified `merge-base --is-ancestor` = NOT_BASE) |

## Deleted local branches (content-identical to pushed remote twins, diff=0, none worktree-checked-out)

`wip/pre-restart-working-tree-2026-09-19`, `wip/morning-niagara-rewire-2026-09-19`,
`wip/bowstage-2026-09-19`, `reconcile/studio-typed-source-live-gates-20260920`,
`llm/fromage/BS_GodFile/p0-morning-dungeon-hop`,
`feat/choral-sheep-root-c-material-proof-2026-09-08`,
`cleanup/melusina-gen3-accessories-hair-2026-09-10` — each verified
`git diff --name-status <local> <remote-twin>` = 0 lines before deletion; twins:
`origin/recovery/*` ×3, `origin/recovery/studio-typed-source-live-gates-20260920`,
`origin/recovery/p0-morning-dungeon-hop-2026-09-10`, `origin/feature/choral-sheep-root-c-material-proof-2026-09-08`,
`origin/cleanup/melusina-gen3-accessories-hair-2026-09-10`.

## Deliberately KEPT (with reasons)

- `backup/*` (6) — intentional pre-clean snapshots; owner-created safety refs.
- `recovery/*` (6 remaining) — owner's parked-work pattern (CURRENT_STATE 2026-09-20).
- `feature/harp-recovery-2026-09-20` — checked out in live worktree `_wt_harp_recovery` (dirty=1).
- `collab/laptop/*` — workstation lane; `Docs/Production/BRANCH_WORKSTATION_POLICY.md` forbids
  wholesale deletion.
- `cursor/*`, `codex/*` old lanes, `backup/pr166`-class pre-collapse branches (~25) — Tier 3:
  "unique" counts are inflated by the 2026-09-10 docs collapse; each needs its own content
  check. Next pass, one receipt each.
- `feature/frequency-ecology-20260921`, `feature/house-gn-paris-recut-20260921` — live lanes.

## Backed up this pass (were unpushed)

`codex/game-state-2026-09-04-checkpoint` (4 commits, remote ref had been deleted → re-pushed),
`codex/snapshot-prep-20260914` (1 commit `e71027a59`), plus the 10 commits from
`Saved/Audit/git_health_2026-09-21.md`.
