# Disk reclaim — plan for 2026-10-02 (READ-ONLY scan done 2026-10-02 ~02:00-02:30)

Status: PLAN — nothing deleted or moved yet. Owner said "do that tmrw".
Scan method: bounded native walks (no full-tree du), packaged probes + targeted
walks. All sizes below are measured tonight unless marked "(report)" (from
_Reports/root_hygiene_2026-09-17).

## Volumes (measured, first and last)
- C: ~2.6-2.8 GB free of 952 GB — CRITICAL-thin.
- D: (Seagate Portable Drive) ~1000 GB free of 1.86 TB — attached.
- G: NOT attached tonight. Imports + BS_GodFile_studio symlink into
  G:/EnvironmentPortfolio_Snapshot_20260918/ and are DANGLING until G: is
  plugged in. Plug G: in tomorrow before the archive/move work.

## Tier 1 — repo-side, biggest and safest (~59 GB)
1. **Git worktrees — 6 registered, ALL dirty=0 (pure checkouts; branches/commits
   stay in the main repo refs; `git worktree remove` is non-destructive):**
   - airi-bridge-p0 (Documents/Codex/worktrees/melusina-airi-bridge-p0) — 19.84 GB
   - archery_wt (BS_GodFile_archery_wt) — 17.35 GB
   - eyewear-editorial (.claude/worktrees/, currently LOCKED — `git worktree
     unlock` first) — 13.31 GB
   - hybrid-combat-bridge (_worktrees/) — 0.12 GB
   - humber-source-handoff (_worktrees/) — 0.01 GB
   - Worktrees/ph — ~0.00 GB (9 files)
   Total ≈ **50.6 GB**. After removal re-check `git worktree list`; a failed
   mid-delete leaves a remnant — finish with Python shutil.rmtree.
2. **LFS local prune — 6.4 GB verified reclaimable** (dry-run: 5405 files).
   Safe order: `git config lfs.allowincompletepush false` → dry-run (done) →
   `git lfs prune --verify-remote --when-unverified=continue` → post-checks
   (spot-read a working-tree .uasset; sample ls-files vs objects; one fresh-
   storage fetch). .git/lfs objects currently 56.72 GB.
3. **uv cache clean** (~1.9 GB in AppData/Local/uv; safe, self-reporting) and
   `python -m pip cache purge`. JetBrains caches are OFF-LIMITS (Rider open,
   agent runs inside it); DDC/Zen off-limits while UE is open.

## Tier 2 — cache clears, mostly runnable while apps live (~8-10 GB)
- NVIDIA DXCache/GLCache (~0.75), Adobe media cache (~0.66), Chrome Cache +
  Code Cache (~0.5), CrashDumps, D3DSCache, JetBrains LOGS (not caches).
- Spotify `Packages\SpotifyAB…\LocalCache` ~4.6 GB — targeted clear (keep
  LocalState/Settings), verify Spotify not writing.
- `Clear-RecycleBin -Force` — needs one UAC; size unknown (sizing needs
  elevation). Skill notes ~2.3 GB when non-empty.

## Tier 3 — moves to external (owner yes; probe-write destination FIRST)
- **harp_bow_pipeline — 62.72 GB, REAL on C:** (61 files, big ones). Move to
  D:/G: per owner choice. Removable volume → robocopy /MOVE + pointer file, NOT
  a junction (skill rule). It is a working pipeline dir — confirm nothing
  references it while unplugged, or prefer D: if D: stays attached.
- **Downloads — 18.15 GB (1835 files)** → move to D:/G:.
- Destination checks: probe-write with TWO writers; never robocopy /MOVE into
  an existing path; one robocopy at a time (check for stray robocopy first).

## Tier 4 — inspect / owner calls (not sized to zero yet)
- AppData/Local total 93.76 GB: Programs 21.86, JetBrains 14.64, **hermes
  10.45** (inspect: hook_outputs/browser-use/audio caches), Packages 9.34,
  Microsoft 5.80, wsl 4.29 (vhdx — compactable), Google 3.80, Roblox 1.89
  (uninstall?), Zed 1.73, Ollama 1.62 (KEEP per rules).
- AppData/Roaming 38.58 GB: JetBrains 6.07, Cursor 5.79, Blender Foundation
  3.50, Adobe 2.82, npm 2.50 (INSTALLED packages — do not delete), Code 2.45,
  kimi-desktop 1.58, SketchUp 1.57, .minecraft 1.03.
- opencode.db — 1.58 GB, LIVE (two opencode.exe). Per-item call when closed.
- OneDrive — NEVER delete inside; report only; use OneDrive "Free up space".
- Epic Games 40.5 GB — UE_5.8 KEEP; re-list for non-engine extras.
- %TEMP% 0.14 GB — nothing old enough to sweep (all fresh).
- Backups\BS_GodFile-<date> (39.5 GB in the old skill table): already GONE
  (dir now 1 file, ~0 GB). .git_EnvironmentPortfolio_Archive_20260908 (20.3 GB
  report): already gone from C:.
- MELUSINA*.blend rescue backups: not found at old locations — verify before
  repeating the old 4.1 GB claim.

## Realistic totals
- Tier 1+2 only: ~**65-70 GB** freed, no external media needed.
- Plus Tier 3 moves: ~**145+ GB** total.
- G: must be plugged in for anything targeting G:/the dangling symlinks.

## Nothing was deleted tonight. Tomorrow: owner approves list → execute in tier
order, re-measuring C: before/after, updating this file with measured gains.