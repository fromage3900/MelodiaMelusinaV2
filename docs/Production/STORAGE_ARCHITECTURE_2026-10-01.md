# Storage Architecture — what "versioned" actually means here

**Date:** 2026-10-01 · **Status:** current · **Supersedes:** nothing; complements
[`2026-10-01_git_p4_closure.md`](../.hermes/plans/2026-10-01_git_p4_closure.md) (the ownership
rule) and [`SESSION_CLOSEOUT_2026-10-01.md`](../Docs/Handoffs/SESSION_CLOSEOUT_2026-10-01.md)
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
