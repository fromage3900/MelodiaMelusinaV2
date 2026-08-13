# Source-control status — 2026-08-13

This is the current source-control checkpoint for the multi-project
`C:\EnvironmentPortfolio` workspace. The workspace root is not itself a Git
repository.

## Unreal repository

- Checkout: `C:\EnvironmentPortfolio\BS_GodFile`
- Remote: `v2` → `https://github.com/fromage3900/MelodiaMelusinaV2.git`
- Branch: `main`
- Local and remote tip: `840b7650`
- State: the branch is synchronized; the working tree still contains
  uncommitted editor/agent artifacts and is not clean.
- PRs [#4](https://github.com/fromage3900/MelodiaMelusinaV2/pull/4) and
  [#6](https://github.com/fromage3900/MelodiaMelusinaV2/pull/6) are merged.

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
