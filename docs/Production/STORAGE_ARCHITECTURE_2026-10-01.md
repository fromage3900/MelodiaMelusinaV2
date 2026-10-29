# Storage Architecture — what "versioned" actually means here

**Date:** 2026-10-01 · **Status:** current · **Supersedes:** nothing; complements
[`2026-10-01_git_p4_closure.md`](../../.hermes/plans/2026-10-01_git_p4_closure.md) (the ownership
rule) and [`SESSION_CLOSEOUT_2026-10-01.md`](../Handoffs/SESSION_CLOSEOUT_2026-10-01.md)
(the 2026-10-01 sweep receipt).

## Read this before calling anything "backed up"

**Both version-control systems live on this machine.**

| System | Location | Off-machine copy? |
|---|---|---|
| Git working tree | `C:\EnvironmentPortfolio\BS_GodFile` | no |
| Perforce server root | `D:\perforce\root` (`fromage:1666`) | **no** |
| GitHub remote | `github.com/fromage3900/MelodiaMelusinaV2` | **yes — the only one** |

So a Perforce submit and a git commit protect you from **accidental edit and from losing
uncommitted work**. Neither one protects you from losing the disk. Only what is pushed to GitHub
is off-machine.

This is not a defect and there is no second server planned. It is a fact that changes what
"it's in Perforce" is worth, and it should shape decisions rather than be rediscovered after a
loss.

## The ownership rule (unchanged)

| Git | Perforce |
|---|---|
| `Source/**`, C++, shaders | `Content/**` `.uasset`/`.umap` |
| `Tools/`, `deploy/`, `Content/Python/` | dropped plugins (`Plugins/<Vendor>/**`) |
| `Docs/`, `.hermes/plans/`, specs, schemas | bulk art, texture libraries, reference meshes |
| `Config/*.ini` (the tracked ones) | anything multi-MB |

Reasoned in `2026-10-01_git_p4_closure.md`. The short version: the git LFS budget is
**branch-name dependent** (50 MB on `docs/`, 512 MB elsewhere), so a large binary import on a
`docs/` branch fails CI no matter how it is chunked.

## The one deliberate duplication: AscentCombatFramework

| | in git | in p4 | off-machine | re-downloadable |
|---|---|---|---|---|
| Source (1,153 files) | **yes** | yes (1,154) | **yes** | no |
| Binary `Content/` (1,446 files, ~1.4 GB) | no | yes | **no** | yes (Fab listing) |

Both halves were submitted to Perforce (changes 271–276). Source is **deliberately kept in git**
even though Perforce holds it, because source is the half you cannot re-fetch and the half that
needs PR review. The binary is Perforce-only because it is large, it is third-party, and the Fab
listing in `AscentCombatFramework.uplugin` can restore it.

Do not "clean up" the source duplication without reading this. It is the only off-machine copy of
code you actually compile.

## What is single-copy today

The 2026-10-01 sweep closed every *unversioned* file: nothing on disk is now in neither system.
But **298 paths are Perforce-only**, which under the fact above means single-disk:

- `Content/Melodia/**` — the bulk of game content, including the Choral Sheep audio bank and the
  animation archive (changes 273, 276)
- `Reference/` — 247 files, in the depot since change 41 (2026-09-25)
- AscentCombatFramework `Content/` — as above, re-downloadable

None of it has an off-machine copy. That is an accepted steady state for re-derivable and
locally-authored art, not an oversight.

## If redundancy for authored content ever matters

Ranked by cost, roughly:

1. **Push the depot to a real server** — the only change that makes p4 a backup. Largest effort.
2. **Git LFS the content deliberately** — needs a non-`docs/` branch and a raised budget; the
   LFS gate is per-branch, so this is a policy change, not a technical block.
3. **A file-level backup of `Content/` off-machine** — cheapest, no VCS semantics, no diffs.

Any of these is an owner decision. This document records the trade-off; it does not recommend
spending the money.

## Traps that produced wrong numbers on 2026-10-01

Each of these produced a confidently incorrect file count before being caught:

- **`p4 files` word-splits paths containing spaces.** `SC4 Ashlotte Maedel/... (1P Weapon)/...`
  made 247 depot-resident files read as missing. Use `-ztag` or diff set membership, never count
  lines.
- **`p4 files` reports absence on stderr and drops entries.** A gap scan built on it reported 163
  missing files; the real figure was 123.
- **`p4 add -c <CL>` on a batch does not reliably target that changelist.** It prints "opened
  for add" and parks the files in `default`. Use `p4 add` then `p4 reopen -c <CL>`.
- **A `binary+F` typemap makes `p4 add` refuse a file that is already in the depot**, reporting
  "can't add existing file" on a writable file.
- **The LFS gate reads `HEAD_BRANCH`.** Nine sub-50 MB commits all pushed green and the PR still
  failed at 461 MB, because CI measures the whole base..head range.

## Verify, do not infer

A submit or push reporting success is not evidence. Read the destination:

```bash
git ls-tree -r origin/main --name-only | grep -c '<path>'      # git
p4 files //Melodia/main/<path>/...                            # perforce
```

Both zero means the file exists on exactly one disk, in one place, on this machine.

### 2026-10-28 Jev direction - worktree policy

Jev (free beam model, receipt `Saved/Audit/SourceControl_20261028/jev_ask_receipt_sourcecontrol_20261028.json`) ranked the next structural fix **C: retire stale worktrees and enforce one worktree per lane** (0.86) - the shared checkout is the collision surface behind the repeated clobbering; one-off backlog cleanup does not prevent recurrence.

- One worktree per active lane; the main checkout is not a shared workspace.
- Worktree audit (`Saved/Audit/SourceControl_20261028/worktree_audit_20261028.json`): 16 worktrees; dead metadata pruned; five clean stale candidates identified for removal (lane-docs-archive, lane-house-dressing-ecv, lane-magicians-audit, lane-morning-live-vista, _wt_final1015) with HEAD SHAs recorded; eight dirty worktrees left untouched.
- **Removal is unsafe without a Content check**: the five candidates held 0.04-8.89 GB of ignored Content each (git status does not show ignored files). Archive by copy only (D:\MelodiaArchive\worktrees_20261029), verify the copy, and never delete a worktree whose Content is not reconciled against p4/main. The 2026-10-29 attempt was interrupted mid-move; the moved files were restored from the archive copy and the worktrees were left in place.
- Pending Perforce CL inventory: 307 = 745 files (458 HoudiniEngine temp cooks, 217 EnvSandbox, 35 Melodia, 25 Staging, 6 Textures, 2 HDA, 1 Tools, 1 _PROJECT), 303 = 543 (interiors lane), 298 = 1, 235 = 1. Per-file triage only; never bulk-revert another lane's opens.
- Offsite push: succeeded - origin `feature/vfx-universal-material-convergence` = `8d05d92e4` (16 commits, LFS 90 objects / 19 MB) as of 2026-10-28 23:4x.
## 2026-10-28 source-control incident addendum

Context: one shared checkout, 16 worktrees, multiple agents merging/committing concurrently. The working tree was clobbered twice (uncommitted CURRENT_STATE edits lost, recovered), a foreign staged case-rename (`docs/` -> `Docs/`) was swept into a materials commit (amended back out), and the default Perforce changelist held ~745 foreign opens one `p4 submit` away from landing under a materials message. The same staged-index hazard recurred at 23:3x: a plain `git commit` swept 103 foreign staged files into a docs commit; it was reverted with `git reset --soft HEAD~1` and re-committed with an explicit pathspec, leaving the foreign staged entries untouched (0 deletions).

Rules adopted (binding):
1. **Commit exact paths with a pathspec.** Never `git add .` and never plain `git commit` in the shared checkout - the corridor can stage a hundred foreign files between your check and your commit. Use `git commit -m "..." -- <exact paths>`; verify `git show --name-status HEAD` afterward.
2. **Never commit with `MERGE_HEAD` or unmerged rows.** Wait for the corridor to finish.
3. **Case discipline:** never case-move `docs/` vs `Docs/`; the tracked path here is lowercase `docs/`, and a case-only rename in the index is a real change.
4. **Perforce: never submit the default changelist.** Recipe: `p4 add/edit` exact files -> create an empty CL (`p4 change -i` with `Change: new`) -> `p4 reopen -c <cl>` -> verify `p4 opened -c <cl>` lists exactly the lane's files -> `p4 submit -c <cl>`.
5. **p4d persistence:** `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\MelodiaP4d.cmd` starts p4d at logon (no admin); `schtasks` needs elevation.
6. **Checkpoints:** `p4 admin checkpoint -Z` writes `D:\perforce\root\checkpoint.<n>.gz` (+md5); `D:\perforce\checkpoints` is unused. `checkpoint.48` exists (2026-10-28 23:19:55, 15.1 MB). No automated schedule yet - owner action.
7. **Offsite:** GitHub is the only offsite copy; push cadence must be verified, not assumed.
8. **Pending CLs are state, not trash:** 307 (745 files, PARK), 303 (543), 298 (1), 235 (1). Per-file triage only; never bulk-revert another lane's opens.
9. **Receipts:** every source-control action writes a receipt under `Saved/Audit/SourceControl_YYYYMMDD/` (JSON only - the pre-commit hook rejects other extensions there).
### 2026-10-28 loss-verification baseline (the anti-regression rule)

The project had no way to detect loss: Content is 41,505 files / 86.44 GB outside git, lanes leave ~1,294 files pending in Perforce, and `git stash` commits are unreachable until pinned. Baseline created 2026-10-28 23:50:

- **Content manifest**: `D:\MelodiaArchive\manifests\content_manifest_20261028_235043.csv` (path, size, mtime for every file) + summary `Saved/Audit/SourceControl_20261028/content_manifest_summary_20261028.json`. Compare tomorrow: a missing or resized file is detectable instead of assumed.
- **Git recovery inventory**: 93 unreachable commits (all stash/WIP/index commits from 2026-09-13..10-28) pinned under `refs/recovery/20261028/` - `git fsck --unreachable` can no longer let gc delete them. Receipt: `Saved/Audit/SourceControl_20261028/git_recovery_inventory_20261028.json`.
- **p4 pending snapshot**: 1,294 opens recorded at `Saved/Audit/SourceControl_20261028/p4_opened_snapshot_20261028.txt`.

**No-WIP-overnight policy (binding):**
1. Content WIP must be `p4 shelve`d (server-side, survives client loss) or submitted before ending a session. A pending CL is not protection.
2. Code/docs WIP must be committed and pushed the same day; the lane branch is the offsite copy.
3. `git stash` is not durable: stash commits are unreachable until pinned. Prefer `refs/recovery/<date>/` pins (this baseline) or a commit.
4. Run the daily manifest before the first edit of the day and diff against the previous day's CSV.
### 2026-10-29 owner ruling - C: is the source of truth

**`C:\EnvironmentPortfolio\BS_GodFile` is authoritative.** Git and Perforce are backup/transport, not truth. Operational consequences:

- No agent may run `p4 sync`, `p4 revert`, `p4 sync -f`, `git checkout`, `git reset`, `git stash`, or `git clean` over this checkout without explicit owner approval. Agents work in lane worktrees and copy in only reviewed artifacts.
- **Loss vault** (`Tools/loss_vault.ps1`, Startup `MelodiaLossVault.cmd`): every 5 minutes it copies Content files modified in the last 20 minutes to `D:\MelodiaVault\YYYYMMDD\HHMMSS\`, with a manifest and git/p4 state. Retention 7 days. Worst case is now the snapshot interval, not months.
- **Pending-CL archive**: the full set of p4-opened files on this client (1,328 existing files / 0.89 GB) is archived at `D:\MelodiaVault\p4_opened_20261029\` - pending changelists are local-only and are the largest remaining exposure.
- **Recovery pins**: 93 unreachable commits + 16 stash commits + 5 worktree HEADs are pinned under `refs/recovery/` (114 refs). Stash commits are local-only; pinning prevents gc from deleting them.
- **Daily guard** (`Tools/lane_guard.ps1`, Startup `MelodiaLaneGuard.cmd`): Content manifest diff (missing/added/resized), git unpushed/staged/stash, p4 opened/checkpoint age, and the fabric canon check (10 MIs -> `M_Master_Nikki`; wrong master must stay deleted).