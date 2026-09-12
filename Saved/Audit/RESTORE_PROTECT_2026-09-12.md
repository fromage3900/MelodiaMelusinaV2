# Restore + Protect — 14 Material Files Deleted Externally — 2026-09-12

## Incident

Between the SeaAbove smoke (green) and the cymatics matrix run, **14 files
vanished from disk**: 8 rebuilt brass MIs + 6 reparented P2 MIs. No crash, no
log trace, no quarantine copy found anywhere on disk. All were untracked
(gitignored paths) — invisible to git, unrecoverable except by rebuild.
prime suspect: another lane's cleanup sweep (967-file staged index + active
Hermes/Claireon surfaces observed the same evening). Cause unproven — treated
as hostile-environment fact, not accusation.

## Recovery (all scripted, all green)

- Brass: reran original `_mi_brass_animated_create.py` → 8 created.
- P2: recreated via create-then-parent (originals were empty shells; zero loss).
- Matrix: brass 8/8 params green, fabric 9/9, sheep 2/2, copernicus 4/4 load.
- PIE SeaAbove: 48 samples, 0 errors.

## Protection (the point of this commit)

All 14 force-added to git (LFS). From here, any deletion is a visible `D`
with a recoverable blob — silent loss is no longer possible for this set.
Recommend extending the same treatment to the other session outputs
(gen-3 textures, Starskiff moves, sheep Chladni_C) before freeze.

**Evidence level:** live-proven (rebuild reports + matrix + smoke).
