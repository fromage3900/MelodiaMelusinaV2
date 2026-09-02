# Git Health Repair Plan — 2026-09-01

## Objective

Restore trustworthy GitHub health signals without touching gameplay code, Unreal binaries, or authored art assets.

## Confirmed state

- `main` remains the protected source-of-truth branch.
- PR #48 now carries the CI repair (Actions checkout/artifact bumps, site-sync
  token-free path, `quick-deploy.ps1` CRLF normalize) plus the git health docs.
- **2026-09-02 fix:** never put `secrets.*` in step `if:` on this repo (both
  `== ''` and `!= ''` produced 0-job push failures). Detect `SITE_SYNC_TOKEN`
  via `env` + step output, then gate remote push steps on that output.
- Echo Static Gates and Unreal Build + Tests still require the self-hosted
  `[Windows, UE58]` runner; this plan does not pretend to solve runner availability.
- A fresh Linux checkout may still report `deploy/quick-deploy.ps1` dirty because
  the index stores CRLF while `.gitattributes` declares `eol=crlf`.
- LFS pointer validation passed for the repository snapshot; binary payload
  availability must still be checked on the Windows/UE machine before asset work.

## Repair sequence

1. Keep PR #32 as the single CI repair path; do not create a duplicate workflow-fix PR.
2. Normalize `deploy/quick-deploy.ps1` in the Git index while preserving CRLF on Windows checkout.
3. Keep the site sync workflow token-free by generating the status blob even when `SITE_SYNC_TOKEN` is absent, and skip only the remote checkout/push steps.
4. Validate the branch with GitHub's YAML/workflow checks, `git diff --check`, LFS pointer validation, and a fresh checkout.
5. After merge, rerun the scheduled site-status workflow and one manual BuildGraph canary.
6. Treat the self-hosted runner as a separate infrastructure task: bring `melodia-v2-win` online with the `Windows` and `UE58` labels, then rerun Echo and Unreal checks.

## Merge order

**Update 2026-09-02:** PR [#48](https://github.com/fromage3900/MelodiaMelusinaV2/pull/48) landed the CI/workflow repair (`cursor/fix-ci-workflows-529c`), toolchain consolidation docs, Mara instrument plan, and cymatic/RTX specs into one health PR on top of merge-train `main`. Prefer merging #48 over re-opening the separate ahead-only docs/CI PRs for those same tips.

Historical order (pre-#48):

- Review and merge PR #32 first.
- Review PR #37 after the CI signal is repaired.
- Rebase PR #41 after PR #37 because the two branches share the cymatic and NVIDIA plan files.
- Keep PR #43 isolated as the Mara instrument/cymatics documentation plan.
- Do not merge PR #28 without rebasing and resolving its overlap with PR #37.
- Close or archive obsolete PRs #9, #15, and #23 after confirming their contents are preserved.

## Acceptance criteria

- No invalid-workflow 0-job failures on the next main push.
- Scheduled site sync succeeds or exits with an explicit token-missing skip, never a checkout failure.
- `deploy/quick-deploy.ps1` is clean in a fresh clone.
- LFS pointer checks remain clean.
- Echo and Unreal jobs receive a real runner result rather than remaining indefinitely queued.

## Scope boundary

This repair is source-control and CI hygiene only. It does not merge a PR, alter runtime authority, recook Unreal assets, or resave `.uasset`/`.umap` files.