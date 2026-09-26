# World Atlas Branch-Retirement Census — 2026-09-25

Generated from the live GitHub branch list and pull-request history while implementing Issue #327.

## Snapshot

- **98 branches** were visible after creating the Atlas convergence branch.
- Classification counts: `HOLD_BACKUP` 5, `CANONIZED_CANDIDATE` 45, `ACTIVE` 5, `UNKNOWN` 4, `SALVAGE_HOLD` 26, `WORKSTATION_HOLD` 5, `P4_CONTENT_RECOVERY` 8.
- **No branch deletion was performed.**
- Full machine-readable rows, head SHAs and PR provenance: [`specs/branch_retirement_census_2026-09-25.json`](../../specs/branch_retirement_census_2026-09-25.json).

## Retirement policy

`CANONIZED_CANDIDATE` means a merged PR exists from that branch. It is **not yet a deletion instruction**: verify that the branch head has no later unique commits, satisfy the repository destructive-operation gate, and preserve any required LFS/P4 provenance first.

`P4_CONTENT_RECOVERY`, `WORKSTATION_HOLD`, `HOLD_BACKUP`, `SALVAGE_HOLD`, and `UNKNOWN` are explicit holds. They are not cleanup targets until their unique semantic source and/or creative binaries have been reconciled.

## PCG / worldbuilding priority holds

Do not delete or wholesale merge these until their specific provenance is resolved:

- `feature/frequency-ecology-20260921` and `recovery/lookdev-frequency-ecology-20260921`: compare unique source separately from UE binaries; current reusable Resonance Ecology PCG is already on main.
- `feature/universe-foundry-ue-staging-20260922`: the Foundry source is canonized, but the Faraway Mother UE staging binaries are not current-main authority; verify them against live UE/Perforce.
- `cursor/realtime-world-compiler-b196`: old parallel World Compiler lane; salvage only semantics missing from current canonical compiler.
- `recovery/pre-restart-working-tree-2026-09-19` and other world/map recovery lanes: treat binary state as P4/content recovery, never as a Git merge target.
- `prep/houdini-foundry-college-2026-09-24` / PR #321: active prep lane; preserve and review separately.

## Safe first cleanup class

The census currently identifies **45 merged-PR source branches** as the first retirement class. Each still needs the final exact-head containment/reachability check required by `Docs/GIT_BATCH_DISCIPLINE.md`.

The connected GitHub tool used for this audit cannot delete refs, so the final remote branch deletion pass remains a separate explicitly-approved mechanical action after these checks.
