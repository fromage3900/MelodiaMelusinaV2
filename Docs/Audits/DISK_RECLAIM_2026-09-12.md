# C: disk reclaim — 2026-09-12

Measured with `_reconcile_backup_20260912/measure_disk.py` + `measure_disk2.py` (read-only walks).
Companion to `Docs/Audits/DISK_RECLAIM_2026-09-10.txt`.

## Volumes at time of survey

| Volume | Total | Free |
|---|---|---|
| C: | 1022.8 GB | **12.7 GB (1.2%)** — critical |
| D: | 2000.4 GB | 158.2 GB |
| G: | 1000.2 GB | 298.8 GB |
| E: / F: | unavailable (PermissionError / OSError) | — |

## Taken without owner consent (regenerable only)

| Action | Freed |
|---|---|
| `uv cache clean` — 31,211 files | 523.2 MB (measured) |
| `pip cache purge` — 289 files, 580 dirs | 72.4 MB (measured) |
| `npm cache clean --force` (`%LOCALAPPDATA%\npm-cache`, now 0.085 GB / 418 files) | amount unverified — the 1.94 GB under `AppData\Roaming\npm` is **installed global packages, not cache**; do not credit it to a cache clean |
| **C: free 12.7 GB → 13.2 GB (measured delta 0.5 GB = the two measured caches)** | |

Nothing was deleted from `BS_GodFile\Saved\` (owner veto), from `Content/`, or from any tracked file.

## Awaiting owner decision (measured, not touched)

| Candidate | Size | Why it needs a yes |
|---|---|---|
| `C:\hiberfil.sys` | ~25 GB est. (63.76 GB RAM, hibernation ENABLED) | `powercfg /h off` needs admin; reversible with `/h on`. Biggest single win, lowest risk. |
| `%TEMP%\opencode\eyewear-verify` + `eyewear-editorial-0912` | 13 GB + 13 GB | OpenCode session data for the eyewear lane — **active** (99 files touched in 30 min); PRs #194/#199 are open. |
| `%TEMP%\ds-work` | 12.65 GB | A full working copy of the repo inside Temp (Content 4.3 GB, **Exports 7.2 GB** — possibly unique art). Idle ~40 min. |
| `C:\Program Files\Epic Games\Twinmotion2026.1` | 9.05 GB | Uninstall via Epic Launcher (agent rmdir was blocked by owner in a prior session). |
| `C:\Program Files\Epic Games\DuetNightAbyss` | 4.45 GB | same |
| `C:\EnvironmentPortfolio\harp_bow_pipeline` | 36.0 GB | Move to D:/G: — path moves can break tooling. |
| `C:\EnvironmentPortfolio\Imports` | 19.0 GB | Move to D:/G: |
| `C:\EnvironmentPortfolio\BS_GodFile_studio` | 12.7 GB | Move to D:/G: |
| `AppData\Local\JetBrains` + `AppData\Roaming\JetBrains` | 13.5 + 8.8 GB | Regenerable caches/logs, but Rider is RUNNING; costs a reindex. |
| `C:\Users\froma\Downloads` | 5.2 GB | Move to D:, don't decide. |
| `MELUSINABACKUPBECAUSEAIAGENTSARERETARDED.blend` + `.blend1` | 4.1 GB | Owner's named rescue backup — move, never delete. |
| `C:\EnvironmentPortfolio\_archive` | 2.8 GB | Move to D:/G: |
| `.claude/worktrees/magical-williamson-a3534a` | 3.2 GB | 568 uncommitted files in it — do NOT remove without owner. |
| `AppData\Local\hermes` | 4.5 GB | Hermes platform data (sessions/audio cache); ask before pruning. |
| `.cache\codex-runtimes` | 1.4 GB | Re-downloadable runtimes. |
| `C:\ProgramData\Microsoft\VisualStudio\Packages` | 0 GB | Already empty — see note. |

## CORRECTIONS + BLOCKERS found while executing (2026-09-12 ~16:45)

- **Hibernation was a false alarm.** `powercfg /a` says *"Hibernation has not been enabled"* — my
  earlier ~25 GB `hiberfil.sys` estimate was a misread of the section heading. No win there, and
  `powercfg /h off` did nothing (it was already off).
- **D: is failing hardware — do NOT stage anything there.** D: is a *Seagate Portable* USB drive.
  Every write returns `The request failed due to a fatal device hardware error`
  (`echo`, `mkdir`, `del` all fail), even though `Get-Volume` reports NTFS/Healthy. The relocation
  script aborted on its first write and left no junction behind and nothing half-moved. Treat D: as
  read-only and copy anything valuable off it. Its 158 GB "free" is not usable space.
- **`bleachbit.exe` (PID 56860, started 14:21 today) is WIPING FREE SPACE on G:**, not freeing any.
  It has written a 196 GB zero-filled file at the G: root
  (`G:\tmptkxotclsYnl0qX...`), growing ~33 MB/s, and G: free fell 298.8 → 128.2 GB during this
  session. Its parent process has exited and it is not a scheduled task. The two older root files
  (`G:\tmp_t90wur...` 42.0 GB, 2026-09-04; `G:\tmpt1vsom...` 22.1 GB, 2026-09-10) are earlier
  interrupted wipe passes: **~260 GB of G: root is wipe scratch.** All three are zero-filled.
- **G: is therefore unusable as a move target until the wipe stops**, and it is the only writable
  volume besides C: (Disk 4 is read-only, Disk 2 = the failing D:).
- Done successfully: `C:\EnvironmentPortfolio\_archive` (2.78 GB, 576 files) moved to
  `G:\EnvironmentPortfolio\_archive` with a **junction** left at the original path (verified: the
  junction resolves and lists the moved contents).

## Still blocked on a running process (do not force)

- `%TEMP%\opencode` (26 GB) — two `opencode.exe` processes live; `eyewear-editorial-0912` was
  written to seconds ago. Biggest Temp win, but only once those sessions end.
- `AppData\Local\JetBrains` + `Roaming\JetBrains` (22.3 GB) — `rider64.exe` + `Rider.Backend.exe`
  running; clearing costs a reindex.
- Epic non-engine apps (14.1 GB) — **no registered uninstall strings** for Twinmotion 2026.1,
  DuetNightAbyss or RealityScan, so the Epic Launcher UI is the only clean path (agent rmdir on
  Program Files was vetoed by the owner previously).


- **The VS installer cache is already empty** and `_Instances` is missing, which is consistent
  with the orphaned VS 2022 install blocking the closed-editor build (see PR #201).
- A **VS Setup background downloader** ran at 14:42 today
  (`%TEMP%\dd_BackgroundDownload_20260912144255.log`) and logged
  `WmiValidatorResult: Failure` / `A Wmi provider at \\localhost\root\cimv2 is not registered`.
- Free space can move several GB mid-session while installers run — re-measure before believing
  any total.

## RESULT — what actually moved (2026-09-12 ~17:30)

C: free went **2.7 GB → 78.0 GB** (and rising with the Imports job). The relocation target had to
be G:, not D: — the D: write failure above killed that plan before a single byte was staged.

| Moved to G: | Size | Junction left at the C: path |
|---|---|---|
| `C:\EnvironmentPortfolio\harp_bow_pipeline` | 36.00 GB (413 files) | yes, verified |
| `C:\EnvironmentPortfolio\BS_GodFile_studio` | 12.68 GB (14,669 files) | yes, verified |
| `C:\Users\froma\Downloads` | 3.01 GB (2,655 files) | yes, verified |
| `C:\EnvironmentPortfolio\_archive` | 2.78 GB (576 files) | yes, verified |
| `%TEMP%\ds-work` | 12.65 GB | yes, verified |
| `%TEMP%\ms-sub` | 0.51 GB | yes |
| `%LOCALAPPDATA%\..\.cache\codex-runtimes` | 1.38 GB | yes |
| `MELUSINA…blend` + `.blend1` | 2.19 + 2.06 GB | moved (files, no junction needed) |
| `C:\EnvironmentPortfolio\Imports` | 18.0 GB | → `G:\_relocated\Imports` (the plain `G:\…\Imports` already held an unrelated 5.6 MB folder, so it was **not** merged) |

Caches/recycle-bin sweep (see table above): 4.35 GB + ~2.3 GB.

Verified after: every junction resolves and lists its moved contents; `%TEMP%\ds-work` is 0 bytes on C:.

Still on C:, deliberately untouched: `C:\Windows\Installer` (16 GB MSI repair cache — deleting it
breaks repair/uninstall), Blender addons under Roaming, Documents/Desktop, `Saved/`, `Content/`,
`AppData\Local\Programs` (17 GB of installed apps), `AppData\Local\Packages` (8.7 GB UWP data).

Blocked only by live processes: `%TEMP%\opencode` 26 GB (two OpenCode sessions running) and
`AppData\Local\JetBrains` 11.4 GB (Rider hosts the agent session, so it cannot be closed by me).

