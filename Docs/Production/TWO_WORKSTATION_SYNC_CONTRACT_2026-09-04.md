# Two-Workstation Sync Contract — 2026-09-04

**Machines:** main Windows workstation + ASUS Nitro laptop  
**Authority:** Git/Git LFS for the current project checkout; Perforce remains a local pilot and is not the cross-machine transport yet.

## The rule

A workstation handoff is complete only when all three states agree:

```text
Git commit/ref state
+
required Git LFS objects hydrated
+
local-only/vendor art expectations understood
```

A successful `git pull` proves only the first line. It does not prove that an LFS object is hydrated, and it cannot restore art that was never committed.

## Live Blender addon is a fourth state

For Melusina House / Geometry Nodes work, a workstation is only truly synchronized when the live Blender 5.2 addon also matches the checkout.

Older installer behavior could silently source `C:\EnvironmentPortfolio\BS_GodFile\deploy` even when you ran the installer from another clone. That is forbidden now.

After Git/LFS synchronization, **close Blender completely** and run:

```powershell
.\deploy\install_melodia_studio.ps1
```

The installer now:

- sources the checkout containing the installer, not a guessed C: path;
- prints source branch + exact Git HEAD;
- stamps the AppData live install with provenance;
- verifies copied addon bytes against the checkout;
- refuses to replace the addon while Blender is running.

Read-only verification:

```powershell
.\deploy\install_melodia_studio.ps1 -CheckOnly
```

If this fails, Git may be synchronized while Blender is still executing stale addon code.

## One command first

By default the sync tool targets `origin/main`, not the current feature branch. A machine on any branch other than `main` reports `wrong-branch` for the normal cross-workstation check.

Use `-Target Current` only when you intentionally want to verify a named feature branch.

### Safe automatic return to main

`-Mode Sync` may move a clean non-main checkout back to `main` when **either** recovery proof is true:

1. `git rev-list --count origin/main..HEAD == 0` — there are no commits unique to the current branch; **or**
2. the current branch has a same-name remote branch and local `HEAD` exactly equals `origin/<current-branch>` — any unique commits are already preserved on GitHub.

This matters for old laptop/recovery branches whose useful changes were squash-promoted to `main`: their commit graph can remain unique even though the important work has landed.

If the branch has unique commits **and** local HEAD is not fully published to its same-name remote branch, the script refuses to switch and tells you to push/preserve the branch first.

No branch is deleted by this normalization. The remote recovery branch remains available for archaeology.

Run this before opening Rider, Blender, or Unreal:

```powershell
.\deploy\sync_workstation.ps1
```

The check fetches `origin`, verifies the repository/remote, reports dirty/ahead/behind/diverged state, compares the current branch with `origin/main`, inventories LFS hydration, and writes:

`Saved/Workstation/<machine>-sync-report.json`

To apply only safe changes:

```powershell
.\deploy\sync_workstation.ps1 -Mode Sync
```

The script may **fast-forward only**. It never resets, cleans, rebases, stashes, force-pushes, or auto-merges divergent branches.

## LFS is a separate step

Hydrate only the lane being used:

```powershell
# route maps / small core
.\deploy\sync_workstation.ps1 -Mode Sync -LfsProfile Core

# Melusina House references / canonical RawArt house source on the current branch
.\deploy\sync_workstation.ps1 -Mode Sync -LfsProfile House

# current gameplay / characters / route / integration
.\deploy\sync_workstation.ps1 -Mode Sync -LfsProfile Gameplay

# expensive: every LFS object reachable from the current checkout
.\deploy\sync_workstation.ps1 -Mode Sync -LfsProfile Full
```

Do not run `Full` on the laptop by reflex.

## Handoff: PC → laptop

On the PC:

1. Close the editor/DCC that owns any lockable binary being handed off.
2. Run `.\deploy\sync_workstation.ps1`.
3. If dirty, commit only the intended lane.
4. Push the lane branch.
5. Confirm the remote branch exists.
6. Unlock any LFS assets whose pushed edit is complete.
7. Do not continue editing the same binary after declaring the handoff.

On the laptop:

1. Run `.\deploy\sync_workstation.ps1 -Mode Sync -LfsProfile <lane>`.
2. Require `sync_state = synced` before starting edits.
3. If the report says `ahead`, the laptop already has unpublished commits: push them before switching context.
4. If it says `diverged`, stop. Do not `git pull --rebase`, reset, or force anything.
5. Take an LFS lock before editing a tracked `.blend`, `.uasset`, `.umap`, FBX, image, or other lockable binary.

Laptop → PC is the same sequence in reverse.

## Branch policy

Use one remote lane as the handoff baton.

Normal work:

- `feature/*`
- `fix/*`
- `collab/*`

Cross-workstation integration / extraction:

- `integration/*`

Preserving machine-local commits before reconciliation:

- `recovery/*`

Never use “I committed it locally” as a handoff. The other machine cannot see a commit until the branch is pushed.

## What the sync states mean

| State | Meaning | Next action |
|---|---|---|
| `synced` | HEAD equals selected remote branch | work may begin |
| `ahead` | this machine has unpublished commits | push before switching machines |
| `behind` | remote moved; clean worktree can fast-forward | run `-Mode Sync` |
| `dirty` | uncommitted work exists | commit the intended work before handoff |
| `diverged` | both local and remote moved | explicit review/reconciliation; no automatic pull |
| `lfs-error` | Git refs may match but binary hydration failed | fix LFS before opening the affected asset |
| `lfs-unavailable` | Git LFS is missing | install/fix LFS first |

## Current Melusina House baseline

The recovered V7 house work is now on `main` via PR #82.

Current canonical Blender source:

`RawArt/MelusinasHouse/MelusinasHouse_V7_Base.blend`

Therefore the default workstation contract is deliberately simple:

```text
PC main == origin/main == laptop main
```

Do not switch to the old recovery/integration house branches for ordinary work. They are historical recovery surfaces only.

Before editing the V7 source:

```powershell
git lfs lock RawArt/MelusinasHouse/MelusinasHouse_V7_Base.blend
```

## Local-only art is not a Git failure

The repository deliberately does not contain every environment/vendor asset. If Git is synchronized and LFS is hydrated but Unreal still reports a missing reference:

1. check whether Git tracks the path;
2. if not tracked, use the documented authored-art/vendor source;
3. do not keep running `git lfs pull` against a path that never existed in Git.

## Acceptance test

Either machine can run:

```powershell
.\deploy\test_laptop_workstation.ps1 -Suite Sync
```

This is the fast source-control acceptance lane. Run the heavier Smoke/Build/UE suites separately.
