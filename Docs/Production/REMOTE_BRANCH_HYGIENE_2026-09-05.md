# Remote Branch Hygiene — 2026-09-05

## Why this exists

The repository had **101 remote branches** in the 2026-09-05 census. Most are agent, recovery, sync, docs, or superseded integration branches. Keeping all of them as live branch refs makes normal PC/laptop synchronization and agent discovery harder than it needs to be.

This cleanup is intentionally **reversible**.

## Active branch set to keep

The generated pruning script preserves these six branch refs:

- `main`
- `integration/astra-game-state-transplant-2026-09-05`
- `fix/mh6-shell-promotion-20260904`
- `codex/game-state-2026-09-04-checkpoint`
- `codex/weapon-gallery-20260902`
- `rnd/2026-08-30-blender52-music-gn-studio`

Everything else in the 2026-09-05 census is a fixed, explicit candidate list. The script does **not** discover and delete future branches.

## Safety model

`Tools/prune_remote_branches_2026_09_05.ps1` is dry-run by default.

With `-Execute`, for each candidate it:

1. fetches the exact remote branch tip;
2. creates a lightweight archive tag at
   `archive/branches/2026-09-05/<old-branch-name>`;
3. pushes the archive tag;
4. re-reads the remote tag and verifies it matches the branch SHA exactly;
5. only then deletes the remote branch;
6. verifies the remote branch ref is gone.

A branch can therefore be restored exactly from its archive tag.

## Current PR hygiene

The stale archaeology PRs were closed on 2026-09-05:

- #9 — Repo lock-in inventory
- #23 — Perforce prep / integration roadmap
- #37 — emerging toolchain consolidation
- #80 — grand master plan

The active recovery lanes remain:

- #94 — Astra game-state / PPV transplant
- #96 — MH6 shell promotion

## Run it

Preview only:

```powershell
powershell -ExecutionPolicy Bypass -File Tools/prune_remote_branches_2026_09_05.ps1
```

Execute:

```powershell
powershell -ExecutionPolicy Bypass -File Tools/prune_remote_branches_2026_09_05.ps1 -Execute
```

Expected target after execution: **6 live remote branch refs** from this snapshot, plus archive tags preserving the exact old tips.

## Restore an archived branch

```powershell
git push origin refs/tags/archive/branches/2026-09-05/<old-branch>:refs/heads/<old-branch>
```

## Important

Do not remove the three temporary recovery/source branches in the keep set until their associated recovery work is done:

- `integration/astra-game-state-transplant-2026-09-05`
- `fix/mh6-shell-promotion-20260904`
- `codex/game-state-2026-09-04-checkpoint`

The weapon-gallery and Blender music-GN research branches are also kept until their small unique deltas are transplanted or explicitly rejected.
