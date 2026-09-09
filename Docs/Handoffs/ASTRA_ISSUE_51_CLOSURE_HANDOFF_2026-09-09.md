# Astra Handoff — Issue #51 Persistence Closure

**Date:** 2026-09-09  
**Read when Astra quota resets**  
**Repository:** `fromage3900/MelodiaMelusinaV2`  
**Issue:** #51  
**Active implementation:** PR #144  
**Branch:** `fix/issue-51-restore-idempotency-2026-09-09`

## Mission

Close Issue #51 with the **smallest decisive implementation + evidence pass**.

Do not reopen already-settled gameplay systems. Do not resurrect stale PR #54.

## Current truth

PR #144 was created fresh from current `main` and contains only the persistence fix + focused regression tests.

The code fix changes `UMelodiaNarrativeSubsystem::RestoreNarrativeRecord` so an incompatible candidate is refused **without resetting/mutating the valid current canonical record**.

New tests:

- `Melodia.Integration.NarrativeRecord.RestoreAtomicity`
- `Melodia.Integration.NarrativeRecord.RepeatRestoreIdempotent`

Existing tests that matter:

- `Melodia.Integration.NarrativeRecord.Migration`
- `Melodia.Integration.NarrativeRecord.SaveFlags`
- relevant Shorewake/Wardrobe contract tests

## Ownership decision — do not reopen

### Starskiff

Durable facts already exist:

- `flag.sea_above.starskiff_ready`
- Narrative `SpawnContext`

Transient/rebuilt state:

- `bBoarded`
- `BoardedPawn`
- player possession
- Starskiff transform
- velocity / `UFloatingPawnMovement` runtime state

**Do not create schema v6 for Starskiff. Do not persist raw physics.**

### Convergence

There is no need for a new Convergence save object.

Durable Convergence consequences remain existing Narrative facts:

- flags
- consumed intent IDs
- consumed reward IDs
- checkpoints / authored permanent consequences

Material/world/presentation response is derived and should rebuild from those facts.

**Do not add a second persistence owner.**

## Save-write race conclusion

Canonical save paths inspected use synchronous `UGameplayStatics::SaveGameToSlot`.

Async save writers found elsewhere belong to non-canonical lanes such as roguelike / alternate save subsystems / generated UI.

**Do not add a generation counter, queue, mutex, stale-write guard, or new serializer unless live Blueprint evidence proves the selected canonical GameInstance is actually writing asynchronously.**

## Required PC evidence pass

### 1. Closed-editor build

From repo root:

```powershell
git fetch origin
git checkout fix/issue-51-restore-idempotency-2026-09-09
git pull --ff-only

$ueRoot = if ($env:MELODIA_UNREAL_ROOT) {
    $env:MELODIA_UNREAL_ROOT
} else {
    "C:\Program Files\Epic Games\UE_5.8"
}

& "$ueRoot\Engine\Build\BatchFiles\Build.bat" `
  BS_GodFileEditor Win64 Development `
  -Project="$PWD\BS_GodFile.uproject" `
  -NoUBA -MaxParallelActions=1 -WaitMutex
```

Do not fix unrelated build warnings in this pass unless they block these tests.

### 2. Focused automation

```powershell
.\deploy\run_melodia_tests.ps1 -TestFilter "Melodia.Integration.NarrativeRecord"
```

At minimum confirm the four persistence tests above pass.

### 3. Full process restart proof

Use one known canonical slot / fixture.

Sequence:

1. Reach or inject the already-established durable state.
2. Save through the canonical JRPG save route.
3. Capture the durable-state vector.
4. Fully terminate **UnrealEditor.exe**.
5. Relaunch.
6. Load the same slot.
7. Capture the durable-state vector again.
8. Load the exact same slot twice more.
9. Capture the durable-state vector after each repeat load.
10. Verify zero duplicate reward/intent effects.

Compare at minimum:

- `Flags`
- `ConsumedIntentIds`
- `ConsumedRewardIds`
- `OwnedCosmeticIds`
- `EquippedCosmeticIds`
- `SocialStats`
- `ScriptCheckpoint`
- `SpawnContext`
- encounter receipt fields

Expected Starskiff result:

- readiness + spawn fact survive;
- runtime begins unboarded / rebuilt;
- no persisted velocity/possession.

Expected Convergence result:

- durable consequence facts survive unchanged;
- derived presentation rebuilds;
- no second commit/reward/intent consumption.

### 4. Packaged-build proof

Use the existing packaging script:

```powershell
.\deploy\package_game.ps1
```

Run the smallest equivalent persistence sequence in the packaged executable:

save → exit process → relaunch → load → repeat-load.

Capture logs/assertions proving equality and no duplication.

## Stop conditions

If all four focused tests + restart proof + packaged repeat-load proof pass:

- update PR #144 with evidence;
- update Issue #51;
- merge only after evidence is attached;
- close #51.

If something fails:

- fix only the concrete failing seam;
- do not expand scope.

## Hard no's

Do **not**:

- reopen Phoenix combat authority;
- rewrite rhythm semantics;
- rebuild the music → reward → wardrobe → Glide chain;
- create another SaveGame authority;
- persist live rhythm sessions;
- persist Starskiff physics/possession;
- create a Convergence save subsystem;
- bump schema version without a newly proven durable fact that cannot fit existing fields;
- revive/merge stale PR #54 wholesale;
- turn this into another architecture/research branch.

## Success definition

Issue #51 is closed when the existing canonical durable facts survive:

**save → process death → relaunch → load → same-slot repeat load → packaged process restart**

with **zero duplicate durable mutation** and without introducing another authority.
