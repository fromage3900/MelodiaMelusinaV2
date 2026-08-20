# Source-control status — 2026-08-13 (updated ~23:20 ET)

This is the current source-control checkpoint for the multi-project
`C:\EnvironmentPortfolio` workspace. The workspace root is not itself a Git
repository.

## Unreal repository

- Checkout: `C:\EnvironmentPortfolio\BS_GodFile`
- Remote: `origin` → `https://github.com/fromage3900/MelodiaMelusinaV2.git`
  (`legacy-melodia` = old `MelodiaMelusina.git`, never push; `pushDefault=origin`,
  `autoSetupRemote=true` set)
- Active branch: `feature/repo-lockin-20260813`, local tip `b10898d0`
- **Pushed 2026-08-13 ~23:00 ET:** `d349d0f1..b10898d0` (22 commits: B7 wiring
  `bfae236c`, router diagnosis + prompt caching `82fdfc21`/`f41bdde5`, full-project
  bp_sweep `974d1d2d`, gate-mechanics evidence `b10898d0`, fleet/queue/handoff docs).
  Push was blocked once by an unknown LFS object (`11aba2b7…` =
  `BP_MelodiaBattleUI.uasset`, the B7 asset — uploaded via
  `git lfs push --object-id`, then the ref push succeeded), then by the intermittent
  `github.com:443` timeout, which cleared on retry.
- `main` local is 1 behind `origin/main` (`343d091c` — a remote PIE-notes doc). No
  conflict risk for PR #9; the PR base will want a rebase/merge of main before merge.
- PRs [#9](https://github.com/fromage3900/MelodiaMelusinaV2/pull/9) (repo-lockin,
  OPEN/MERGEABLE/BLOCKED, 5,367+/492−, now 39 commits incl. the 22 above),
  [#10](https://github.com/fromage3900/MelodiaMelusinaV2/pull/10) (credits, OPEN,
  607+/102−) and #1/#5/#7/#8 open; #4 and #6 merged.
- **Self-hosted runner revived 2026-08-13 ~23:05 ET:** `melodia-v2-win` at
  `C:\actions-runner` was **offline since 08-12 20:08 UTC** (network abort, never
  restarted) — which is why CI has been queuing forever. Restarted via
  `run.cmd` (hidden window); Listener 13308 + Worker active. The runner drained the
  whole queued backlog (8 jobs: old static_gates + old build runs on stale heads).
  **Fresh PR CI (after the push):** `static_gates` ran and reported fail (4m10s) — the
  LFS-pull/Python steps were transient on the first drained jobs; a manual `git lfs pull`
  of the same paths exits 0. `build` fails deterministically with
  `Unable to build while Live Coding is active. Exit the editor and game...`
  (reproduced locally, 2.36s): **the runner is this machine, and the editor is open**
  (PID 43584). The build gate can only pass in a closed-editor window; with Live Coding
  active it fails instantly and that is expected, not a regression. Do not chase this
  failure while the editor runs. The UE build also requires the
  `[self-hosted, Windows, UE58]` label and the runner machine having the editor closed.
- Working tree still contains uncommitted editor/agent artifacts and is not clean.

## Website repository

- Checkout: `C:\EnvironmentPortfolio\my-site-clean`
- Remote: `origin` → `https://github.com/fromage3900/my-site.git`
- Local tip: `3cfa5f0`
- Cached remote tip: `90c6e77`
- State: not synchronized. The local and remote histories are unrelated; do
  not use an unrelated-history merge or force-push without an owner decision.
- The local site facts and asset checks pass. `npm run verify:all` remains
  blocked by the token linter (`99` hard errors and `1113` warnings).

## Working rule

Treat the Unreal branch tip as published, but do not describe either checkout
as fully clean. Keep the website remote mismatch visible until the correct
remote history or a reviewed publication branch is chosen.

## Remaining before a collaborator can self-serve

1. `BS_GodFile.uproject` dirty/uncommitted (MelodiaWardrobe plugin + UTF-8 BOM) —
   owner sign-off, `SKIP_PROTECTION=1` per pre-commit.
2. Enable `GitSourceControl` in UE (2,224 lockable files, 0 locks ever held) —
   `.uproject` + Config touch, owner sign-off.
3. Art delivery decision — Glacier backup exists (13.02 GiB, `s3://melodia-archive-…`);
   no self-service pull yet.
4. Untracked-but-valuable content: Melusina V2Test rig, UpdatedShirt set,
   SirMelodious textures, `l_melodia_dreamstate..umap` (owner call: rename or delete),
   `Plugins/MelodiaWardrobe/`.
5. Corrupt LFS object: `Melodia_Portfolio_Stage_v18_SIR_VISIBLE.blend` (1.79 GB,
   live-referenced, in `.git/lfs/bad`) — re-fetch from origin.
6. `static_gates` ledger row (Echo) — pending the CI run that is now actually running.
7. **`build` CI gate vs open editor** — the runner is this machine; the build step
   hard-fails while the editor runs (Live Coding active). Either run the build check
   in a closed-editor window (before/after an editor session) or accept the red check
   as expected-while-editing. Candidate improvement (owner call): make the workflow
   skip/soft-fail the build step when an editor is running, or run the gate on a
   separate build-only machine.
