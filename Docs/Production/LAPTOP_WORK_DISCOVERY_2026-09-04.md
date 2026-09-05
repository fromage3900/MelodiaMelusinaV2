# Laptop / Multi-Workstation Work Discovery — 2026-09-04

**Purpose:** Stop remote agents from losing committed work simply because it has not reached `main`.

## Two-workstation sync command

Before opening Blender/Rider/Unreal on either machine:

```powershell
.\deploy\sync_workstation.ps1
```

Safe fast-forward + lane-specific hydration:

```powershell
.\deploy\sync_workstation.ps1 -Mode Sync -LfsProfile House
```

Full contract: `Docs/Production/TWO_WORKSTATION_SYNC_CONTRACT_2026-09-04.md`.

A machine is not considered handed off while the report says `dirty`, `ahead`, `behind`, `diverged`, or `lfs-error`.

> **Front-door cleanup note:** the ahead/behind counts below are a captured discovery snapshot from before the 2026-09-04 documentation cleanup advanced `main`. Re-run the comparison before promotion. The branch contents and merge warning remain the important facts.

## Current important remote branches

### `recovery/laptop-main-20260904`

At the latest 2026-09-04 remote comparison:

- **ahead of `main`: 13 commits**
- **behind `main`: 24**
- status: **diverged**
- latest recovered commit: `bd870dd694403bb17c0f541289a8aba7a0794158`

This is the most important current laptop recovery source.

Notable work present there includes:

- `SESSION_NOTES_2026-09-04.md`
- `melusinahouse_v7_plan.md`
- `Tools/house_v7_base_build.py`
- `Tools/house_detailed.py`
- `Tools/house_facade.py`
- `Tools/house_greybox.py`
- `Tools/house_roof.py`
- `Tools/house_shingle_patch.py`
- current `deploy/surreal_arch/melodia_gn/` house / city / music convergence work
- multiple committed `Saved/MelusinasHouse/*.blend` versions including the V7 base

The session notes describe:

- 268 registered builders;
- converged house lineage;
- tower-wipe fix;
- universal music-influence fix;
- Set Position bend fix;
- restored unique builders;
- V7 house base build and remaining convergence boundaries.

### Important merge warning

**Do not merge `recovery/laptop-main-20260904` wholesale.**

The branch also contains broad removals under:

- `Exports/`
- old quarantine directories
- legacy source quarantine

Treat it as an extraction/recovery branch: promote named, reviewed work in isolated batches.

## Reconciliation PR status

- **PR #79** (`collab/laptop/integration-batch-2026-09-02`) is closed/superseded for active sync. Its branch remains historical documentation/archive only.
- **PR #81** (`collab/laptop/main-reconciliation-2026-09-04`) is closed/superseded. The three house reference boards are already viewable on `main`, and the V7 house runtime/source baseline was promoted via PR #82.
- Do not resurrect either PR as the active workstation baton.

## Older laptop branches

### `collab/laptop/integration-batch-2026-09-02`

At discovery time:
- ahead of `main`: 20
- behind `main`: 23
- status: diverged

Contains laptop onboarding/two-PC workflow docs and other historical integration work. Extract only named files after comparison.

### `collab/laptop/onboarding-closeout-2026-09-02`

At discovery time:
- ahead: 3
- behind: 23
- status: diverged

Contains onboarding closeout / two-PC workflow / quick-deploy changes.

### `collab/laptop/workstation-health`

At discovery time:
- ahead: 1
- behind: 23
- status: diverged

Contains workstation-health, Moho worker, and laptop-plan changes.

## Agent rule

Before saying any of the following:

- “the laptop did not commit anything”
- “that house work does not exist”
- “there are no new Blender/GN files”
- “main contains all current work”

you must compare `main` against the relevant laptop/recovery branch.

## Current synchronized house baseline

The recovered V7 Melusina House payload was promoted to `main` via **PR #82**.

Current canonical shared source:

`RawArt/MelusinasHouse/MelusinasHouse_V7_Base.blend`

Normal PC/laptop work should now return to `main`.

Old branches:
- `recovery/laptop-main-20260904`
- `integration/laptop-house-recovery-20260904`
- `integration/house-handoff-20260904`
- `integration/house-handoff-current-20260904`

are **recovery/history only**. Do not use them as the active workstation baton.

## Promotion policy

Use narrow promotion batches:

1. identify the exact file(s) / commit(s);
2. compare against current `main`;
3. reject destructive unrelated deletions;
4. promote only the intended files;
5. run the relevant test/build;
6. update this discovery doc when a branch is fully consumed or superseded.

The branch name is a discovery surface, not a source-of-truth replacement for `main`.
