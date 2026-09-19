# Disk Reclaim — 2026-09-18 (C: extreme dive)

**Purpose.** Record of what was measured and what was taken from `C:` in one session, so the next
batch can be decided from numbers instead of prose. Audit snapshot, not a status document —
[CURRENT_STATE.md](../../CURRENT_STATE.md) remains the only status authority.

**Volumes at start:** C: 953 GB — **6.4 GB free (100 % used)** · G: (ROG ESD-S1C) 931 GB — 173 GB
free · E: removable, no media · **D: not attached** (see finding 1).
**Volumes at end:** C: — **66 GB free (94 % used)** = **+59.6 GB measured**.

## 1. What was taken (no owner decision required)

| Item | Freed | Evidence |
|---|---|---|
| Git worktree `C:/EnvironmentPortfolio/_worktrees/canonical-agent-context-repair-0914` | 12.42 GB | `dirty=0`, branch `codex/canonical-agent-context-repair-20260914` pushed; `git worktree remove` rc=0 |
| Git worktree `C:/Users/froma/Worktrees/melodia-evidence-audits-0917` | 12.53 GB | only diff was a deleted `.bak`; branch pushed; removed with `--force` |
| LFS local prune (`.git/lfs`) | **35.0 GB** | `git lfs prune --verify-remote --when-unverified=continue` → `14,078 files deleted`; `.git` 54 GB → 21 GB |
| Chrome Cache + Code Cache + GPU Cache | 0.35 GB | contents cleared, 0 locked |
| NVIDIA DXCache/GLCache, D3DSCache, CrashDumps, `%TEMP%` | 0.48 GB | contents cleared |
| Stale worktree registrations (`bg_main_check`, `BS_GodFile_studio`) | 0 | `git worktree prune` |

Safety work done around the LFS prune, in order:

1. `git config lfs.allowincompletepush false` — a quota-blocked upload now fails loudly instead of
   landing pointer-only commits.
2. Dry-run first: `prune --verify-remote` **halted** (GitHub's LFS batch check is unreliable on this
   repo — it reports present objects as missing; the same artefact made `git lfs push --all --dry-run`
   claim 16,449 objects are absent when two sampled committed objects re-hydrate fine).
   `--when-unverified=continue` deletes what verifies and keeps the rest.
3. Receipts: `%LOCALAPPDATA%\Temp\disk-dive-20260918\lfs_prune_receipt_20260918.txt` (copy on `G:`).
4. Post-checks: working tree intact (spot-checked real bytes in `MelodiaIntegration/Config` and
   `WorldCompiler/DT_*`); 4,000 sampled `origin/main` LFS objects **0 missing locally**; a fresh-storage
   `git lfs fetch` re-downloads from the remote (899,628 B verified).

**Cost of the prune:** older revisions now re-download on demand, which consumes the metered LFS
bandwidth (~$0.0875/GiB). Only superseded versions were dropped; everything reachable from current
refs was retained.

## 2. Findings

### F1 — `C:\EnvironmentPortfolio` symlinks are DANGLING; D: is not attached

`_archive`, `BS_GodFile_studio`, `harp_bow_pipeline`, `Imports` are symlinks to `/d/_relocated/*`.
No D: volume exists today (only C:, E:(no media), G:). Recent disk events: **13× ID 154 + 7× ID 153**
(IO failures), including a "Disk 1" failure at 08:00 today; that disk is no longer enumerated
(`Get-Disk`: 0 = internal NVMe, 2 = ROG ESD-S1C, 1 = card reader, no media).
The moved material exists on G: inside `G:\EnvironmentPortfolio_Snapshot_20260918` (98 GB, made today)
and `G:\EnvironmentPortfolio\BS_GodFile_STALE_G_do_not_launch\Imports`.
**Decision needed:** re-point the four symlinks at the G: paths, or delete them.

### F2 — `C:\EnvironmentPortfolio` remaining footprint (measured)

| Entry | GB | Class |
|---|---|---|
| `BS_GodFile` | 259.0 | repo — Content 90.7 · `.git` 21 (post-prune) · Plugins 36.4 · Saved 29 · `.claude/worktrees` 16 · Imports 8.1 · Exports 7.9 · Intermediate 5.5 |
| `.git_EnvironmentPortfolio_Archive_20260908` | 19.9 | archived umbrella `.git` — move to G: |
| `_worktrees` | 0 | removed this session |
| `wix` 0.79 · `generated` 0.69 · `apps` 0.53 · `_reconcile_backup_20260912` 0.49 · `git_bundles_archive` 0.16 · `studio` 0.15 · `teamwork_projects` 0.14 · `browser-test` 0.12 | ~3.1 | move to G: |
| root scratch files (`.env*`, `req*.json`, `BS_G`, `VERSION`, `wix.lock`, ME_WaveHarp_* …) | <0.01 | P6 file `_Reports/root_hygiene_2026-09-17.json` already classifies them |

### F3 — Other measured C: whales (owner decisions)

| Item | GB | Note |
|---|---|---|
| `C:\Users\froma\Backups\BS_GodFile-20260904-205650` | 39.5 | whole-repo snapshot — move to G: or delete |
| `%LOCALAPPDATA%\UnrealEngine` (DDC + Zen) | 25.3 | purge only with the editor closed (it is live now) |
| `AppData\Local\JetBrains` + `Roaming\JetBrains` | 21.1 | Rider is the shell this session runs in — purge when closed |
| `.local/share/opencode/opencode.db` | 18.0 | single agent-session DB — prune sessions or archive to G: |
| `OneDrive\Documents` (Adobe 25 · Xfer 3.2 · Unreal 2.3 · GitHub 1.7) | 58.5 local | NEVER delete inside a synced tree — use OneDrive "Free up space" |
| `C:\Users\froma\Worktrees\melodia-issue51-f1f2-0915` | 23.55 | worktree with 4 uncommitted `MelodiaIntegration` source edits — preserve diff, then remove |
| `.claude/worktrees`: `eyewear-editorial-0912` 13 (locked) · `magical-williamson-a3534a` 3.2 (detached, 568 doc/template diffs) · `p0-morning-dungeon-hop` 0.23 | 16.4 | remove the two unlocked ones |
| `Windows\Installer` | 13.3 | NEVER delete (MSI repair cache) |
| `Windows\WinSxS` | 16.3 | DISM only |
| `Program Files`: Adobe 39.8 · Visual Studio 21.2 (+7.0 x86) · SideFX 11.1 · JetBrains 8.9 · Derivative 8.6 · dotnet 7.2 | — | uninstall decisions |
| Epic: `UE_5.8` 38.0 (keep) · `RealityScan_2.2` 0.59 | 38.6 | only RealityScan is removable |

## 3. Not touched (standing rules)

`BS_GodFile/Content` (90.7 GB authored art), `Saved` (29 GB), `Plugins` (36.4 GB — the project needs
them), `CompatibilityLabs`, `.git` beyond the LFS prune, `Windows\Installer`, `WinSxS`, anything inside
`OneDrive`, and no uninstalls. `%TEMP%` is now only 0.30 GB (it was 39.5 GB in an earlier audit).

## 4. Suggested next batch (by GB per risk)

1. ~~Move `Backups\BS_GodFile-20260904-205650` (39.5) and `.git_EnvironmentPortfolio_Archive_20260908`
   (19.9) to `G:`~~ — **DONE 2026-09-18, see §5**: 59.3 GB moved, C: 66 GB → **124 GB** free.
2. Purge DDC+Zen (25.3) and JetBrains caches (21.1) in the next **closed-editor, closed-Rider** window
   — ~46 GB.
3. Decide F1 (symlink repair) — dangling links are a data-availability flag, not a space item.
4. Remove the two unlocked `.claude` worktrees and the issue51 worktree after saving its diff — ~27 GB.
5. OneDrive "Free up space" on Documents (Adobe/Xfer/Unreal Projects) — ~30 GB local.

## 5. Batch 1 executed — 2026-09-18 evening

Moved off C: with `robocopy /MOVE` (one job at a time, destination probed by two writers first and
churn-checked: G: free stable across 20 s), then verified byte-for-byte with a native walk:

| Tree | Files / Dirs / Bytes | Destination | Result |
|---|---|---|---|
| `C:\Users\froma\Backups\BS_GodFile-20260904-205650` | 37,028 / 31,342 / 42,406,197,350 | `G:\_relocated\Backups\BS_GodFile-20260904-205650` | identical, 0 failed |
| `C:\EnvironmentPortfolio\.git_EnvironmentPortfolio_Archive_20260908` | 12,782 / 11,427 / 21,315,380,317 | `G:\_relocated\.git_EnvironmentPortfolio_Archive_20260908` | identical, 0 failed |

- Robocopy log: `%LOCALAPPDATA%\Temp\disk-dive-20260918\move_log_20260918.txt` (RC=1 both trees = success).
- Sources removed by `/MOVE`; pointer files left at the old locations
  (`C:\Users\froma\Backups\_MOVED_TO_G_20260918.txt`, `C:\EnvironmentPortfolio\_ARCHIVE_GIT_MOVED_TO_G_20260918.txt`).
- **C: free 66 GB → 124 GB.** Session total so far: 6.4 GB → 124 GB (≈ +118 GB).

## 6. Batch 2 executed — 2026-09-18 late evening (non-UE items only)

| Item | Action | Freed |
|---|---|---|
| JetBrains old-version caches + logs (`Rider2026.1`, `IntelliJIdea2026.1`, `WebStorm2026.1`, every product `log`/`logs`) | deleted — live `Rider2026.2` (12.9 GB local + 3.3 GB roaming) deliberately untouched | 2.86 GB |
| `Worktrees/melodia-issue51-f1f2-0915` | diff saved to `G:\_relocated\patches\issue51-worktree-20260918.patch` (6.5 MB), then removed | 23.55 GB |
| `.claude/worktrees/magical-williamson-a3534a` (detached HEAD) | diff saved (363 KB), then removed | 3.17 GB |
| `.claude/worktrees/p0-morning-dungeon-hop` | diff saved (1.5 KB), then removed | 0.19 GB |
| `~/.local/share/opencode/opencode.db` (+ `-wal`, `-shm`) | archived to `G:\_relocated\opencode-sessions-20260918\` (byte sizes verified at destination), local copies removed | 18.80 GB |

**C: free 124 GB → 165 GB.** Worktrees left: main + `.claude/worktrees/eyewear-editorial-0912` (locked, active).

**Deferred by owner instruction ("no UE"):** UE DDC + Zen (~25 GB) — still needs a window with the editor closed.

**Junctions repaired.** `C:\EnvironmentPortfolio\{harp_bow_pipeline, BS_GodFile_studio, Imports}` were
junctions pointing at the dead `D:\_relocated\*`. Re-pointed to their verified counterparts under
`G:\EnvironmentPortfolio_Snapshot_20260918\` (resolution probe: 78 / 85 / 7 entries visible).
`_archive` is left dangling on `D:\_relocated\_archive` on purpose — its snapshot counterpart is empty,
so nothing is there to point at. Owner call: say where that content lives, or delete the link.

Receipts: per-item freed sizes from the driver's own before/after walk
(`%LOCALAPPDATA%\Temp\disk-dive-20260918\batch2_nonue.py`, `batch2b_worktrees.py`), opencode move log
`opencode_archive_log.txt`, junction script `repoint_junctions.ps1`.

Session totals: **C: 6.4 GB → 165 GB free** (LFS prune 35.0 · worktrees 52.3 · batch-1 move 58.0 · caches 3.7 · opencode archive 18.8).
