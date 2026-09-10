# Branch prune receipt — 2026-09-10

Nine `materials-2026-09-09` branches pruned after proof of redundancy against `origin/main`.
Nothing is destroyed: every commit below stays in the object store until gc and is reachable by SHA.

Proof method (both run against `origin/main`):
1. `git diff --name-status origin/main <branch>` filtered for `A` — zero branch-only files (except
   one scratch asset, itself junk).
2. `git cherry origin/main <branch>` — commits already upstream by patch-id, or zero commits ahead.

Residual deltas on the two `docs/` branches are 2-line **LFS pointer** differences on `.uasset`
revisions that `origin/main` already carries in a later form (their PRs #158 / #162 landed as
`14a9272d` and `df300947`; main then did `c08c49d0 chore(sheep): salvage #149 proof and remove scratch`).

| branch | tip SHA | verdict |
|---|---|---|
| content/materials-session-closeout-2026-09-09 | 7e66c7938279b7407be227bca39d0fe524d22b76 | redundant (cherry `-`) |
| content/materials-tw-stub-persist-2026-09-09 | 02460b06355ffd919095e1e2191a98f473e6dd63 | redundant (cherry `-`) |
| docs/materials-clean-env-2026-09-09 | 89223d89bb1146ce10415712c39edc9ceea2d0d9 | redundant (0 branch-only files; PR #162 landed) |
| docs/materials-nikki-leftover-2026-09-09 | e63567604c98809b5711b658100eacddb0912d54 | redundant (0 branch-only files; PR #158 landed) |
| docs/materials-texture-triage-2026-09-09 | 31a0b493ccc311f4cdf39d8a0877ac7769aa9a02 | redundant (0 commits ahead) |
| docs/materials-batch4-wiring-receipt-2026-09-09 | f5343f45cec7fd7c29e28de1bcd155ad7b23bae6 | redundant (0 commits ahead) |
| docs/materials-offline-flipbook-audit-2026-09-09 | df1c350dcf69427ca9425e850c86e76e0a7646e2 | redundant (0 commits ahead) |
| docs/materials-wiring-flipbook-cleanup-2026-09-09 | c9c10a71d3a5b373234d5b647685cbad20ac5c24 | redundant (0 commits ahead) |
| docs/materials-all-merged-2026-09-09 | febfe309d1cfd0f48328189fced9a9a2057aec4c | redundant (0 commits ahead) |
