# Git leftovers triage — 2026-08-11

## Authority (use these)

| Checkout | Remote | Role |
|----------|--------|------|
| `C:\EnvironmentPortfolio\BS_GodFile` | `v2` → MelodiaMelusinaV2 | Primary Unreal working tree |
| `C:\EnvironmentPortfolio\MelodiaMelusinaV2` | `origin` → MelodiaMelusinaV2 | Published V2 mirror / push target |
| `C:\EnvironmentPortfolio\my-site-clean` | `origin` → my-site | Website (separate) |

## Keep offline / do not treat as trunk

| Path | Finding | Recommendation |
|------|---------|----------------|
| `.git.backup.mirror` | Bare backup of old portfolio history; incomplete objects | Keep as cold backup; never set as `GIT_DIR` for daily work |
| `.repo_recovery_20260727` | Branch `recovery/core-game-state-20260727` ahead 7 of old `environment-portfolio`; **~7254 deleted** worktree paths | Archive zip then delete when MelodiaMelusinaV2 confirmed complete; do not restore as active root |
| `.clean_repo` / `.temp_repo` | Empty / no useful commits | Safe to delete when disk needed |
| Root `.github/workflows/{pages,quantum-experiments}.yml` | Orphan copies — **no root `.git`** | Either move under `my-site-clean` / a restored portfolio remote, or delete; they do not run from root today |
| Root `.gitattributes` / `.gitignore` | Working-tree leftovers aligned with Melodia LFS policy | Harmless reference copies; authority is inside Unreal repos |

## LFS hygiene (done this pass)

- `MelodiaMelusinaV2`: `NotoMusic-Regular.ttf` + `assimp-vc141-mt.dll` renormalized from full blobs → LFS pointers (lockable attributes were already set).

## Not touched

- Untracked Melusina/SirMelodious FBX drops under V2 `Content/Melodia/Characters/` (separate content intake).
- Diverged `my-site-clean` ahead/behind remote.
- Force-push to legacy `MelodiaMelusina` `origin/main` (non-ff; left alone).
