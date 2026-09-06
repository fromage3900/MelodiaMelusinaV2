# Remote Branch Hygiene — 2026-09-06 second pass

The first cleanup reduced the live remote branch count from 101 into the twenties. The remaining count is mostly historical/recovery sediment plus temporary extraction branches.

## Recovery completed before pruning

- stale Grand Master Plan PR #97 closed;
- stale canon/toolchain PR #28 reduced to its one genuinely missing research file and superseded by merged PR #103;
- stale Astra PR #94 audited; newer main source kept and provenance docs preserved by merged PR #104;
- Perforce setup guide + UE5.8 runner helper preserved by merged PR #105;
- parallel recovery work has also been landing small web/Blender/research leftovers onto current main.

## Intentionally kept live

- `main`
- `docs/stale-session-start-fix-2026-09-06` — recent unique session-start/project-state work still needs review.
- `recovery/harvest-small-branches-2026-09-06` — current concurrent recovery lane.

All other branches explicitly listed in the second-pass script are archive/delete candidates.

## Safety

`Tools/prune_remote_branches_2026_09_06.ps1` is dry-run by default. With `-Execute`, every candidate is first tagged at `archive/branches/2026-09-06/<old-branch>`, the remote tag SHA is verified against the branch tip, and only then is the branch deleted.

The script uses PowerShell 5.1-safe refspec interpolation around `:`.

## Run

```powershell
git switch main
git pull
powershell -ExecutionPolicy Bypass -File Tools/prune_remote_branches_2026_09_06.ps1
```

After reviewing the dry-run table:

```powershell
powershell -ExecutionPolicy Bypass -File Tools/prune_remote_branches_2026_09_06.ps1 -Execute
git fetch --prune --tags
```

The script is snapshot-specific and will not delete future branches that are not explicitly listed.
