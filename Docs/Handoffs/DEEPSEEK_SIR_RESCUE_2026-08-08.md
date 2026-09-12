# DeepSeek handoff — `NotifySirRescued()` has zero callers (executed 2026-08-08)

**Status:** fix applied, tests extended. Requires closed-editor rebuild.

---

## Changes made

### C1 — Fix site: `MelodiaDungeonRunCoordinator.cpp`

**File:** `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaDungeonRunCoordinator.cpp`

- Added `#include "MelodiaOpeningFlowSubsystem.h"` (line 12)
- Added `NotifySirRescued()` call after the `SpawnActor<AMelodiaSirMelodiousIntroActor>` at line 474:

```cpp
if (UMelodiaOpeningFlowSubsystem* Flow = UMelodiaOpeningFlowSubsystem::Get(this))
{
    if (Flow->NotifySirRescued())
    {
        UE_LOG(LogTemp, Log, TEXT("Melodia run: SirRescued phase set on dungeon completion."));
    }
    else
    {
        UE_LOG(LogTemp, Warning, TEXT("Melodia run: NotifySirRescued rejected (phase=%d)."),
            static_cast<int32>(Flow->Phase));
    }
}
```

This mirrors the spawn-then-notify convention used by `MelodiaSirMelodiousIntroActor` for `BeginMorning`/`NotifySirDeparted`.

### C2 — Tests: `MelodiaCoreRulesTests.cpp`

**File:** `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCoreRulesTests.cpp`

Extended `FMelodiaOpeningFlowRulesTest` (test `Melodia.CoreRules.OpeningFlow`) with 8 new assertions
after the existing `FirstDungeonUnlocked` walk (after `:413`):

| Assertion | Expected |
|-----------|----------|
| Phase == FirstDungeonUnlocked before SirRescued | `EMelodiaOpeningPhase::FirstDungeonUnlocked` |
| `NotifySirRescued()` returns true | `true` |
| Phase == SirRescued after notify | `EMelodiaOpeningPhase::SirRescued` |
| `NotifySirRescued()` idempotent guard | `false` |
| `NotifyReturnedHome()` advances from SirRescued | `true` |
| Phase == ReturnedHome after notify | `EMelodiaOpeningPhase::ReturnedHome` |
| `NotifyReturnedHome()` idempotent guard | `false` |
| `NotifySirRescued()` fails from ReturnedHome | `false` |

### C3 — Handoff document

This file.

---

## Save compatibility

`EMelodiaOpeningPhase` is a `uint8` UENUM persisted by value.
- Adding the call does **not** invalidate existing saves — `RestoreFromSave` sets Phase directly.
- Saves at `FirstDungeonUnlocked` from a previously completed run will **not** backfill.
  The player must complete a dungeon run again.
- `RestoreFromSave` broadcasts `OnPhaseChanged` → `HandleOpeningPhaseChanged` fires
  `TryRecruitSirMelodious()` → guarded by `HasPlayerUnit()` — idempotent.

---

## Report only — not fixed

`UMelodiaOrreryRegistry::IsSphereUnlocked` has **zero callers** project-wide. Any orrery
sphere authored with `RequiredPhase >= SirRescued` stays locked regardless of this fix.

---

## Build

This is a C++ change in `MelodiaCore` — Live Coding will not pick up a new cross-module call
reliably. Close the editor and run:

```
Build.bat BS_GodFileEditor Win64 Development -Project=C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject
```

**Verify every claim here against the live editor and on-disk source before acting.**
