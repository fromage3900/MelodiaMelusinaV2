# DISK_RECLAIM_2026-10-11

Measured before: C: 9.1 GB free (critical). After: 42.8 GB free (+33.7 GB).

## Taken (no owner call needed — regenerable or empty worktrees)

| What | Freed | Notes |
|---|---|---|
| UE Zen cache `%LOCALAPPDATA%\UnrealEngine\Common\Zen` | 6.3 GB | Editor confirmed closed (no UnrealEditor.exe in tasklist); regenerable |
| `git worktree remove lane-opencode-pcg-audit --force` | 16.8 GB | 17.95 GB walk, 0 dirty files |
| 13 clean lane worktrees (docsrc, hermes-loop, audiofx, claude x3, gemini-video-qa, harmonic, holo4-overnight, main-rescue, muse-overworld-ui, owner-local, pr-423-seasonal-biomes) | ~11 GB | All dirty=0 |
| Clear-RecycleBin | 0.3 GB | — |

Worktree removals are non-destructive: branch and commits stay in the main repo refs.

## NOT taken — deferred by size/ownership (still on the table)

| Item | Size | Why deferred |
|---|---|---|
| `_worktrees/lane-melusina-boot-fit-luna` | 8.08 GB | 21,618 dirty files (mostly deletions of `.agents/` content) — per-item owner call |
| `_worktrees/lane-melusina-canon` | 3.10 GB | 15 dirty files — has a branch `feature/melusina-runtime-canon-20261005` |
| `BS_GodFile_recovery/` | 17.93 GB | recovery worktree — owner call |
| JetBrains caches | 16.46 GB | session runs inside Rider — logs locked, caches off-limits |
| OneDrive tree | 70.34 GB | synced tree — never delete inside; use OneDrive's own "Free up space" |
| Downloads | 18.85 GB | move candidate; D: (869 GB free) probe-passed today |

## Volumes (end of session)
C: 42.8 free · D: 869.6 free (probe-write passed) · G: 94.6 free
