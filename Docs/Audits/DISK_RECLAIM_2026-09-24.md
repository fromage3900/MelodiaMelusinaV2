# Disk reclaim — 2026-09-24

Trigger: C: free **5.9 GB** (critical; UE builds/PIE choke under ~30).

## Volumes (start → end)

| Volume | Free start | Free end |
|---|---|---|
| C: | **5.9 GB** | **91.0 GB** (+85.1, final re-read after handle release) |
| D: | 358.3 GB | (present again; `_archive` junction resolves — probe-write before use) |
| G: | 92.2 GB | — |

## Taken without asking (measured)

| Item | Listed size | Freed (volume delta) |
|---|---|---|
| 8 registered worktrees, dirty=0 (`_wt_docs_mats_0923`, `_wt_final_conv`, `_wt_handpaint_docs_sparse`, `_wt_morning_closeout`, `_wt_paris_recut`, `_wt_studio_gn_convergence`, foundry-canon, melusina-canon-docs) | ~85 GB | ~65 GB (walk sizes exceed freed — hardlinked DDC-style content) |
| `_wt_morning_closeout` remnant after `git worktree remove` failed ("Invalid argument") | 28.35 GB | +12.33 GB (Python `shutil.rmtree`, 3 s, 0 failures) |
| `_wt_harp_recovery` (--force; only dirty file was scratch `replay_pid29120.log`) | 12.72 GB | ~12.7 GB |
| LFS prune (`--verify-remote --when-unverified=continue`) | 299 MB dry-run | 903 objects; post-check: 0/25 oids missing, tracked `.uasset` = real bytes |
| pip cache purge | — | 73 MB |
| CrashDumps | 0.04 GB | 0.04 GB |
| RecycleBin | — | empty |

Notes: `lfs.allowincompletepush=false` set first. All removals were `git worktree remove` — branches/commits stay in the main repo's refs.

## Deferred by instruction / owner calls (still on the table)

| Item | Size | Blocker |
|---|---|---|
| `BS_GodFile/.claude/worktrees/eyewear-editorial-0912` (LOCKED) | 12.4 GB | modified `Saved/Audit/eyewear/final_verify.json` + `run_out/` scratch dirs — Saved/Audit rule |
| `BS_GodFile_laptop` worktree | 12.5 GB | uncommitted authored code: `deploy/surreal_arch/melodia_gn/skirt_decor.py` + `__init__.py` edit |
| uv cache | 2.9 GB | locked by 3 live `uv.exe` processes; retry when lane ends |
| UnrealEngine DDC + Zen | 5.6 GB | UnrealEditor RUNNING — editor-closed only |
| NVIDIA DXCache | 0.77 GB | held open by live GPU process |
| JetBrains caches (Local+Roaming) | ~21 GB | Rider running; not closeable from this lane |
| Downloads → D:/G: | 1.9 GB | owner call; D: alive again, probe-write first |
| OneDrive `~\OneDrive\Documents` | ~58 GB | never delete inside synced tree; owner uses OneDrive's own Free-up-space |
| `_reconcile_backup_20260912`, `my-site-temp` | ~0.5 GB | ARCHIVE-TO-G candidates per root_hygiene_2026-09-17 |

## Dead ends this pass (re-measured, don't chase)

- Quick-win caches (Chrome/NVIDIA/Adobe/D3DS/Spotify/JB logs): **0.04 GB** — already swept in a prior pass.
- LFS cache is 45.9 GB but **only 299 MB prunable** — nearly all retained by current refs; dry-run first before promising.
- Old whales gone: `~\Backups\BS_GodFile-*` (was 39.5 GB), `.git_EnvironmentPortfolio_Archive_20260908` (was 20.3 GB), opencode.db (now 0.32 GB).
- `%TEMP%` 0.77 GB — fresh agent-session data.
