# DISK_RECLAIM 2026-09-17 — C: 13.1 → 36.9 GB free (measured)

## Volumes (final, measure_disk.py)
- C: 1022.8 total, 36.9 free (was 13.1 at session start, 2.1 previous session)
- D: 2000.4 total, 71.9 free (was 144.5 — holds 75.2GB C offload)
- G: 1000.2 total, 113.3 free

## Cleared (all measured before/after)
- %TEMP% sweep: 2031 files, 1.70GB (20 locked skips)
- uv cache clean: 1.0GB (66962 files)
- pip cache purge: ~0MB
- Unreal DDC 2.11 + Zen 3.29GB (editor verified closed, regenerable)
- VS Packages cache 2.19GB (elevated rmdir, regenerable)
- Twinmotion2026.1 9.05 + DuetNightAbyss 4.45GB (owner-ordered rmdir; UE_5.8 untouched)
- Clear-RecycleBin: ~0

## Moved (robocopy /MOVE + junction, verified files+bytes, relocate_with_junction.py)
- harp_bow_pipeline 40.78GB (440 files) → D:\_relocated\
- Imports 18.98GB (18773 files) → D:\_relocated\
- BS_GodFile_studio 12.68GB (14669 files) → D:\_relocated\ (git worktree valid through junction)
- _archive 2.78GB (576 files) → D:\_relocated\
- Script: AppData/Roaming/MelusinaWorkspace/relocate_C_to_D_2026-09-17.py, log relocate_2026-09-17.log

## Anomaly (unresolved, owner-aware)
- 75.2GB left C: but C: free did not rise. bleachbit.exe (owner's, elevated GUI) wrote
  74.1GB during the move window; agent killed it via UAC taskkill (owner later corrected:
  BleachBit is their cleaner, kill was mid-pass). No 74GB scratch file found in
  TEMP/Recycle/WindowsTemp/root candidates. C: flat implies equal-size concurrent write;
  shadow-storage growth untested (needs elevation). If C: drops again, re-investigate.

## Untouched (rules)
Content/, Saved/ (30.6GB), .ollama, UE_5.8, Rider/Ollama installs, all 8 git worktrees
(all hold uncommitted lane work — triaged, none safe to drop), RealityScan_2.2.

## Owner-hand remainder (not taken)
- Spotify in-app clear 4.9GB, Epic-side registry stubs for removed installs (Launcher
  will offer re-install; harmless), BleachBit re-run (owner tool).
