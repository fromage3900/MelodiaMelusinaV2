# Git Archaeology Closeout — 2026-09-08

**Status:** CLOSED / DO NOT REOPEN WITHOUT A CONCRETE MISSING-WORK SYMPTOM

## Final authority map

- Game / Unreal / capstone: `fromage3900/MelodiaMelusinaV2`
- TouchDesigner / live visuals / AE: `fromage3900/MelodiaTouchDesigner`
- Portfolio website: `fromage3900/my-site`
- Historical umbrella remote: `fromage3900/EnvironmentPortfolio` — archived/read-only

Local workspace distinction:

`C:/EnvironmentPortfolio/` remains a valid parent workspace folder.

The deprecated object was the root umbrella Git repository that used to make the container folder itself appear authoritative. The game checkout remains nested at `C:/EnvironmentPortfolio/BS_GodFile/`.

## Verified closeout state

- all three active repos use `main` as their default branch;
- no open cleanup PRs remain in the game, TD, or site repos at this closeout point;
- `EnvironmentPortfolio` is archived;
- the game repo has `REPOSITORY_AUTHORITY.md` and a CI guard against reintroducing the deprecated umbrella Git remote as active authority;
- the site repo has an explicit website-only authority contract;
- the TD repo has the current 2026-09-08 visual-performance contracts and Chladni ROOT_C source lane;
- the old EnvironmentPortfolio TD copy is historical/reference only.

## Branch archaeology policy

Do not treat ahead/behind counts alone as evidence of unique work.

Several old branches were squash-merged. GitHub can report them as `diverged` even when their final file tree matches `main`.

Verified examples at closeout:
- `MelodiaTouchDesigner:fix/chladni-fleece-contract-closeout-2026-09-08` has the same final Git tree as TD `main` after squash merge.
- `MelodiaMelusinaV2:fix/repo-authority-workspace-vs-repo-2026-09-08` has the same final Git tree as game `main`.
- `my-site:fix/repo-authority-workspace-vs-repo-2026-09-08` has the same final Git tree as site `main`.

Those branches may be deleted as routine branch hygiene, but branch deletion is **not required for project correctness**.

Older long-lived/staging branches should only be deleted after one of:
1. tree/content equivalence to `main` is verified;
2. their unique work is explicitly migrated;
3. the branch is intentionally declared obsolete.

Do not start another broad branch-merging campaign merely because many branches exist.

## Reopen archaeology only if

Reopen this topic only when there is a concrete symptom such as:
- a known committed asset is missing from a canonical repo;
- a workstation cannot reproduce current `main`;
- Git LFS reports missing objects/pointers;
- a named branch contains known required work not present on `main`;
- a canonical repo remote points somewhere unexpected;
- an agent cites `EnvironmentPortfolio` as active project authority again.

Do **not** reopen archaeology for:
- old path strings in dated historical docs;
- squash-merged branches showing ahead/behind noise;
- archived provenance copies;
- harmless local workspace folder nesting;
- speculative fear that something might be missing without a named artifact.

## Operational rule going forward

> **One domain, one repo, one authority. Build forward unless a specific missing artifact proves otherwise.**

Git work from this point should serve production: small commits, explicit evidence, reproducible assets, and clean handoffs—not repository archaeology as a standing task.
