# Perforce Migration Handoff — 2026-08-26

## Status

**Preparation package only. Perforce is not live yet.**

This branch makes the current migration decision and safety rules available from GitHub on the Windows/Unreal PC. It does not provision Helix Core, move or delete assets, alter BS_GodFile.uproject, rewrite Git history, prune LFS, or change the game's current authority.

The existing phase plan remains the design reference:

- [Perforce migration plan](PERFORCE_MIGRATION_PLAN_2026-08-13.md)

This handoff is the current execution record for the remote state audited on 2026-08-26.

## Intended split

| System | Owns after acceptance | Current state |
| --- | --- | --- |
| GitHub: fromage3900/MelodiaMelusinaV2 | Source/, Tools/, Docs/, deploy/, Plugins/, Config/, specs/, project text/config, evidence and lightweight CI | Current code/docs reference; main is 23acba7 |
| Perforce: planned //melodia | Unreal content, maps, environment art, exports, raw art, and other large lockable binaries | Not provisioned or seeded by this commit |
| Git LFS | Transitional protection for files still tracked in Git | Keep intact until the Perforce acceptance gate passes |

**One path must have one owner.** Do not submit or edit the same path through Git/LFS and Perforce during the transition.

## Remote baseline

- Repository: fromage3900/MelodiaMelusinaV2
- GitHub main: 23acba70c32883b947272ed41295f288ea63b47e
- Prior comparison baseline: 70f85d56c01943f1444eeac36278a4163e94c8e2
- The 64 previously suspicious animation objects are present on the remote, hash/size verified, and recognized as Unreal packages. Their small payload sizes remain a content-level review item; they were not automatically restored from the older baseline.
- PR #15's eight V22 texture/locomotion LFS payloads are present and hash/size verified. PR #15 remains an isolated draft and is not promoted by this package.
- The restored UE mannequin retarget lane remains the conservative P0 reference. Do not treat the newer Quaternius lane as proven merely because its files are present.
- The P0 gameplay authority remains the existing wardrobe/equip flow into Glide capability, traversal, and save/restart proof. This migration package does not create a second gameplay authority.

## What to do on the Windows PC

If the checkout has uncommitted or untracked work, preserve it first. Do not run git clean, git reset, git gc, git lfs prune, or a history rewrite.

From a clean or separately preserved checkout:

~~~text
git fetch origin codex/perforce-migration-handoff-2026-08-26
git switch --track origin/codex/perforce-migration-handoff-2026-08-26
git config core.hooksPath .githooks
python Tools/perforce_migration_preflight.py
~~~

For a machine-readable report:

~~~text
python Tools/perforce_migration_preflight.py --json
~~~

The preflight is read-only. It reports Git provenance, dirty state, LFS pointer/hydration information, and whether the p4 client is available. It does not create a Perforce workspace, add files, reconcile files, submit a changelist, or delete anything.

If the PC is not yet connected to this branch, the setup itself is still accessible without merging it:

~~~text
git clone https://github.com/fromage3900/MelodiaMelusinaV2.git MelodiaMelusinaV2
cd MelodiaMelusinaV2
git fetch origin codex/perforce-migration-handoff-2026-08-26
git switch --track origin/codex/perforce-migration-handoff-2026-08-26
~~~

Git LFS only hydrates files that are tracked by Git. It cannot supply bulk environment art that was deliberately never committed; use the approved art/archive source for those files.

## Safe migration sequence

1. **Preserve the source checkouts.** Record git rev-parse HEAD, git branch --show-current, git status --short, git diff --name-status, git lfs status, and git lfs fsck --pointers on the friend-PC checkout before changing it.
2. **Provision Helix Core separately.** Create the //melodia depot, named users/workspaces, and a verified backup. Do not point Unreal at an unverified depot.
3. **Install the typemap before the first submit.** Review Perforce/typemap.melodia.txt; binary+l is intended to enforce exclusive checkout for Unreal and art binaries.
4. **Configure the ignore rules and depot view.** Review Perforce/p4ignore.txt. Map only the intended Perforce roots; do not use a broad workspace view that overlaps Git-owned source/docs.
5. **Seed into a staging workspace.** Copy from the preserved source/art checkout, verify counts and SHA-256 manifests, and keep the Git copies untouched.
6. **Prove editor locking.** From two UE/P4-capable sessions, Check Out / Check In / Revert a representative uasset, umap, and source-art file. Confirm the second writer is refused.
7. **Repair tooling seams before cutover.** Any gate that uses git ls-files Content must be changed to a Perforce query or an explicitly scoped workspace walk, then re-proven with a planted failure.
8. **Acceptance gate.** A clean PC must open L_KaleidoNave with no missing references, and the P0 wardrobe → Glide → traversal → save/restart proof must remain reproducible.
9. **Only after acceptance:** remove the approved binary paths from Git tracking and update onboarding. Until then, do not delete the Git copy.

## Current CI note

The red site_status_sync check is a portfolio convenience job. The game checkout and status generation passed; the job failed when checking out fromage3900/my-site because SITE_SYNC_TOKEN is not configured. It is not a Perforce or Unreal asset failure. It can remain non-blocking or be retired during the GitHub-to-Perforce handoff.

## Explicit holds

- No Git branch deletion, LFS pruning, garbage collection, force push, or history rewrite.
- No automatic restoration of the 64 small animation packages.
- No merge of PR #15 solely because its LFS payloads are available.
- No wholesale merge of PR #9.
- No removal of Git copies before a verified Perforce backup and clean-machine acceptance.
- No credentials, PATs, Perforce passwords, or AWS keys belong in this repository.

When this branch is merged, it gives the PC a versioned runbook and safe preflight. It does not by itself make Perforce live; server provisioning and the acceptance evidence still occur on the owner-controlled machine.