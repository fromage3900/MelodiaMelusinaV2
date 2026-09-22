# Git health audit — 2026-09-21

Read-only sweep + two backup-gap pushes. Repo: `fromage3900/MelodiaMelusinaV2` (private),
checkout `C:/EnvironmentPortfolio/BS_GodFile`, branch `lookdev/frequency-ecology-20260921`
(upstream `origin/feature/frequency-ecology-20260921`).

## Verdict

Healthy and improving. Object store clean (fsck 0 missing/corrupt, 277 dangling — normal), CI green
on all recent runs, LFS `allowincompletepush=false`, hooks wired (`core.hooksPath=.githooks`).
The two real risks — unpushed local commits — were closed during this audit. Convergence backlog
exists (80 remote branches, 5 fully merged) but is triage-able, not alarming.

## Actions taken this audit

| Action | Proof |
|---|---|
| Pushed 6 showcase-lane commits `74d9f936f..de51bf582` to `origin/feature/frequency-ecology-20260921` | 55 LFS objects / 148 MB, budget gate OK; post-push `rev-list HEAD...upstream` = `0 0`; ls-remote tip `de51bf582` |
| Pushed 4 eyewear commits `a119b7a39..5432b2509` to `origin/feature/eyewear-editorial-20260912` | 0 LFS bytes; post-push `rev-list` = `0 0`; ls-remote tip `5432b2509` |

## Test gate (the real one)

`python -m unittest discover -s Content/Python/Tests -p "test_*.py"` — **116 tests, 2 failures**
(baseline 2026-08-31 was 7 failures).

1. `test_on_disk_authored_textures_toon_monotonicity` (test_adversarial_empirical_challenge) — known
   contract-drift family from the 08-31 baseline.
2. `test_on_disk_fabric_textures_exist_and_conform` (test_fabric_instances) — asserts
   `Content/Textures/Fabrics/` exists on disk; directory absent. Fixture/fixture-path issue, not
   logic rot. 11 files sit untracked under `Content/Textures/` — likely the same family.

## Dirty tree (parked, per CURRENT_STATE 2026-09-20 isolated-landing rule)

149 modified · 39 deleted · 161 untracked. Classified:

- **39 deletions**: 26 `Content/EnvSandbox/VFX/Materials/MI_Niagara_*` + 13 `__ExternalActors__` —
  parked, unstaged; matches the intent of branch `fix/archive-cosmo-pre-expansion-snapshot-20260921`.
- **161 untracked, dominated by**: UltraDynamicSky 52, Content/Melodia 43, EnvSandbox 19,
  Content/Python 13, Content/Textures 11, Cinematics 5, surreal_arch 4.
- **Junk**: `CURRENT_STATE.md~` editor backup at repo root — safe to delete.
- **Policy conflict**: 2 untracked `Docs/Handoffs/*_2026-09-21.md` files. AGENTS.md: no handoff
  files; CURRENT_STATE: no new session-note docs. Owner decision: land content into
  CURRENT_STATE/Saved/Audit or delete.
- 3 stashes, all named pre-destructive-op backups — leave in place.

## Branch census (80 remote refs, 5 fully merged)

- **Tier 0 — landable now**: PR #281 `fix/runtime-gameplay-closure-recut-20260921` is
  `CLEAN`/`MERGEABLE`, CI green, 0 unique files (supersession-proof), 0 required reviews.
  Owner merge.
- **Tier 1 — active lanes, backed up as of this audit**:
  `feature/frequency-ecology-20260921` (this lane; content-identical to
  `recovery/pre-restart-working-tree-2026-09-19` plus the 6 pushed commits; 145 behind main —
  converge via PR when showcase prep settles, not before), `feature/studio-final-convergence-20260921`
  (landed as PR #280), `feature/house-gn-paris-recut-20260921`.
- **Tier 2 — zero-unique-file branches (ahead via squash-era shas, content on main)** — prune
  candidates after receipt: `docs/production-spine-paradigm-20260921`, `fix/runtime-gameplay-closure-20260921`,
  `fix/archive-cosmo-pre-expansion-snapshot-20260921`, `fix/retire-front-door-suite-20260921`,
  `recovery/harp-receipt-current-main-20260921`, `feature/harp-recovery-2026-09-20`,
  `feature/house-gn-paris-20260920`, `docs/canonize-converged-project-state-20260920`.
- **Tier 3 — pre-docs-collapse branches with inflated "unique" counts** (A-files are mostly Docs
  main deleted 2026-09-10; e.g. `backup/pr166` 954 A-files = 829 Docs/.hermes): verify-then-prune,
  one receipt each, never bulk. Includes the `backup/*`, `collab/laptop/*`, `cursor/*` families.
- **Local-only stragglers**: `codex/snapshot-prep-20260914` has 1 unpushed commit (`e71027a59`,
  09-14, mirror-path chore) whose upstream is `origin/main` — needs a `docs/`-prefix refspec, owner
  call. `collab/desktop/integrate-laptop-2026-09-06` (121 ahead, tip 09-09) is likely superseded by
  PR #280 but NOT proven (3797-file diff, rename detection skipped) — content-check before prune.
  Local `main` is 41 behind `origin/main` (stale, no exposure — update from `_wt_morning_closeout`
  when idle).
- All `wip/*` and mis-prefixed locals verified content-identical (diff 0) to their remote
  `recovery/*`/`feature/*` twins — fully backed up.

## Governance (honest note)

GitHub-side `main` protection is **cosmetic**: `required_approving_review_count=0`,
`enforce_admins=false`, 0 rulesets. The real gate is client-side (`.githooks` pre-commit/pre-push +
LFS budget 512 MB feature / 50 MB docs-classes). Protection is hooks + discipline, not
machine-enforced — tightening it is an owner decision (single-collaborator repo; required reviews
would be unsatisfiable as configured).

14 open issues. #51 is the long-chain persistence gate (owner queue), #252/#221 active semester
lanes. Issues #29–#42 (R&D spikes, early-Sept) look stale — close-or-scope candidates.

## Convergence order (recommended)

1. Merge PR #281 (owner; CLEAN, green).
2. Keep CURRENT_STATE updated in-commit; delete `CURRENT_STATE.md~`; resolve the 2 handoff files.
3. When showcase prep settles: PR the `feature/frequency-ecology` lane into main (it is the only
   Tier-1 lane ahead of main).
4. Prune pass with receipts: 8 Tier-2 branches, then Tier-3 verify-then-prune; write receipts to
   `Docs/Audits/` before deleting any ref.

## Second pass — execution (same day, owner go-ahead)

| Action | Verified outcome |
|---|---|
| Merge PR #281 | Was **DRAFT** (first `gh pr merge` correctly refused); `gh pr ready` then `--merge --delete-branch` → `state=MERGED`, origin/main tip `dea0522ac` "Merge pull request #281" |
| Local `main` | Fast-forwarded in clean `_wt_morning_closeout` to `40238a89c`→`dea0522ac` line (ff-only) |
| codex backup gaps | `codex/game-state-2026-09-04-checkpoint` (4 unpushed commits, remote ref had been deleted — stale tracking ref caught it) and `codex/snapshot-prep-20260914` (`e71027a59`) re-pushed; tips verified via ls-remote |
| Remote ref prunes | 6 deleted per `Docs/Audits/BRANCH_PRUNE_RECEIPT_2026-09-21.md` (5 manual + recut via gh); ls-remote confirms gone |
| Local branch prunes | 7 parity-proven locals deleted (`wip/*` ×3, `reconcile/studio-typed-*`, `llm/fromage/p0-*`, `feat/choral-sheep-*`, `cleanup/melusina-gen3-*`); tip SHAs in receipt; remote twins diff=0 |
| Remote-tracking hygiene | `git remote prune origin` cleared stale refs; 75 live remote heads reconcile: ~74 live pre-pass − 6 deleted + 2 new backup refs |
| Junk | `CURRENT_STATE.md~` deleted; 2 untracked `Docs/Handoffs/*` parked into allowlisted `Saved/Audit/` (owner may delete) |

## Not checked (boundaries)

LFS remote hydration sampling (bandwidth cost — last run 2026-09-18 audit branch), `my-site` and
`MelodiaTouchDesigner` repos, per-worktree dirty state (7 other worktrees), CI workflow vs local
gate strictness diff, .github workflows content.
