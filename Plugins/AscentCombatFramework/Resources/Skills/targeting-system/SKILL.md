---
name: targeting-system
description: Set up lock-on / soft targeting in ACF — configure the targeting component, target points, filters and camera magnetism with the Ascent Targeting System (ATS).
globs: []
alwaysApply: false
---

# Ascent Targeting System (ATS) — ACF Ultimate

The **AscentTargetingSystem** module gives the player (and AI) soft-lock / hard-lock targeting. The player uses `UATSTargetingComponent`, which scans for nearby actors within a distance/angle cone, picks the best candidate (nearest, or closest to forward), and optionally locks the camera onto it with configurable magnetism. Targetable actors expose `IATSTargetableInterface` and one or more `UATSTargetPointComponent`s (the precise points the camera/reticle snaps to, e.g. head/torso). Targeting can be narrowed with `UATSTargetingFilter` objects. AI uses the sibling `UATSAITargetComponent`. This skill covers configuring and wiring lock-on targeting.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Player pawn with targeting | `ACharacter` + `UATSTargetingComponent` | `/Game/FullSample/` player pawn | Drives target search, lock and camera control |
| Targetable enemy | `AACFCharacter` implementing `IATSTargetableInterface` | `/Game/FullSample/` NPCs | Can be locked; reacts on acquire/lose |
| Target points | `UATSTargetPointComponent` | added to the enemy mesh sockets | Snap points (head/torso/etc.) with optional camera event |
| Targeting filter | `UATSTargetingFilter` (BP subclass) | sample targeting config | Custom rule to include/exclude potential targets |

> **Never edit sample assets.** Duplicate the sample player pawn / filter Blueprints into your own folder (e.g. `Content/YourGame/Targeting/`) and configure **your copies**. Editing the originals = lost on update.

### Key classes

| Class | Role |
|---|---|
| `UATSTargetingComponent` | Player lock-on: search, switch, camera magnetism, line-of-sight checks |
| `UATSBaseTargetComponent` | Shared base for targeting components (current target storage) |
| `UATSAITargetComponent` | AI variant used by `AACFAIController` |
| `UATSTargetPointComponent` | A lockable point on a target (extends look-at point); exposes a camera event name |
| `IATSTargetableInterface` | Interface targets implement: `OnTargetAcquired`, `OnTargetLosed` |
| `UATSTargetingFilter` | `IsActorTargetable(owner, target)` rule to filter candidates |
| `UATSTargetingFunctionLibrary` | Blueprint helpers for targeting queries |

### Important enums

- `ETargetingType`: `EDontLock` (no camera change), `EMagneticLock` (smooth lock), `EMagneticLockYawOnly` (yaw-only lock).
- `ETargetSelectionType`: `ENearestTarget` (lowest distance), `EForwardTarget` (closest to forward vector).
- `ETargetingDirection`: `ELeft`, `ERight`, `EUp`, `EDown` (for switching targets via input).

---

## 2 — Setup / Configuration

### A. Add the targeting component to the player

1. Open your **duplicated** player pawn Blueprint (`Content/YourGame/Targeting/`).
2. Add a `UATSTargetingComponent`.
3. Configure detection:
   - `MaxTargetingDistance` (default 1500) — how far targets can be acquired.
   - `MaxAngularDistanceDegree` (default 60) — half-angle of the search cone in front of the player.
   - `TargetSelectionType` — `ENearestTarget` or `EForwardTarget`.
   - `ObjectsToQuery` — the object types (e.g. Pawn) the sweep checks.
4. Configure the camera behaviour:
   - `TargetingType` — `EMagneticLock` / `EMagneticLockYawOnly` / `EDontLock`.
   - `LockMagnetism` (default 15) — interpolation strength for the magnetic lock.
   - `BottomPitchLimitDegree` / `UpperPitchLimitDegree` — pitch clamps to avoid gimbal lock.
   - `bStopTargetingIfOutOfSight` — drop the target if line of sight is blocked.
   - `InputTrasholdForSearch` (default 0.7) — stick deflection needed to switch targets via input.

### B. Make enemies targetable

1. On your enemy actor, **implement `IATSTargetableInterface`** (Blueprint: Class Settings → Implemented Interfaces).
2. Add one or more `UATSTargetPointComponent`s attached to mesh sockets (e.g. `spine_03` for torso, `head`). Each point can set a `CameraEvent` name to trigger a camera tweak when that point is locked.
3. Implement `OnTargetAcquired(point)` / `OnTargetLosed()` to show/hide a lock reticle or play feedback.

### C. (Optional) Create targeting filters

1. Create a Blueprint subclass of `UATSTargetingFilter`.
2. Override `IsActorTargetable(componentOwner, Target)` to return `false` for actors you never want to lock (dead, friendly team, stealthed, etc.).
3. Add it to the component's `TargetFilters` array (instanced), or add/remove at runtime (see below).

---

## 3 — Core Workflow / Runtime API

### Activating targeting (`UATSTargetingComponent`)

```
Targeting->TriggerTargeting(true);    // start lock-on
Targeting->TriggerTargeting(false);   // stop
Targeting->ToggleTargeting();         // flip current state
bool bOn = Targeting->IsTargetingEnabled();
```

### Switching targets with input

```
// Bind to right-stick axes; the component uses InputTrasholdForSearch as the deadzone:
Targeting->RightSearchTargetWithInput(AxisX);   // switch left/right
Targeting->UpSearchTargetWithInput(AxisY);      // switch up/down
```

### Reading / forcing the current target

```
AActor* current = Targeting->GetCurrentTarget();   // from UATSBaseTargetComponent
Targeting->SetCurrentTarget(SpecificEnemy);        // force a target
```

### Runtime tuning

```
Targeting->SetMaxTargetingDistance(2000.f);
Targeting->SetMaxAngularDistanceDegree(45.f);
Targeting->SetTargetingType(ETargetingType::EMagneticLockYawOnly);
Targeting->SetLockMagnetism(20.f);
Targeting->SetTargetSelectionType(ETargetSelectionType::EForwardTarget);
```

### Filters & object types at runtime

```
Targeting->AddFilter(UMyDeadEnemyFilter::StaticClass());
Targeting->RemoveFilter(UMyDeadEnemyFilter::StaticClass());
Targeting->AddObjectType(ObjectTypeQuery_Pawn);
Targeting->RemoveObjectType(ObjectTypeQuery_Pawn);
```

### Delegates

| Delegate | When it fires |
|---|---|
| `OnTargetingStateChanged(bIsTargeting)` | Lock-on turned on/off — toggle UI/movement mode |
| `OnTargetChanged(targetActor)` | The locked target switched — move the reticle |

---

## 4 — Wire to Characters / Blueprints

1. **Input → component**: bind your lock button to `ToggleTargeting()` (or hold = `TriggerTargeting(true/false)`), and the right-stick / look axes to `RightSearchTargetWithInput` / `UpSearchTargetWithInput`.
2. **Camera control**: with `EMagneticLock` the component interpolates the camera toward the locked target point using `LockMagnetism`. Use `EMagneticLockYawOnly` for action games that keep player pitch control. The `UATSTargetPointComponent.CameraEvent` lets specific points drive a custom camera modifier.
3. **Reticle UI**: listen to `OnTargetChanged` to reposition a lock-on widget over `GetCurrentTarget()`, and to `OnTargetingStateChanged` to show/hide it.
4. **Movement mode**: many games switch the character to strafe/orient-to-target movement while locked — toggle that on `OnTargetingStateChanged`.
5. **AI**: AI targeting uses `UATSAITargetComponent`, created/owned by `AACFAIController`; the controller's `GetTarget()` / `SetTarget()` read and write through it. You normally don't configure the player `UATSTargetingComponent` on NPCs.
6. **Combat integration**: ACF actions/abilities can read the current target from the targeting component to orient attacks toward the locked enemy.

---

## 5 — Verify

**Checklist before testing:**

- [ ] Player pawn is a **duplicate** with a `UATSTargetingComponent` added.
- [ ] `ObjectsToQuery` includes the object type your enemies use (e.g. Pawn).
- [ ] Enemies **implement `IATSTargetableInterface`** and have at least one `UATSTargetPointComponent`.
- [ ] `MaxTargetingDistance` and `MaxAngularDistanceDegree` are large enough for your encounters.
- [ ] Input is bound to `ToggleTargeting`/`TriggerTargeting` and the search-by-direction functions.
- [ ] A lock reticle is wired to `OnTargetChanged` / `OnTargetingStateChanged`.
- [ ] Any custom `UATSTargetingFilter`s are added to `TargetFilters` (or at runtime).

**Common failures:**

| Symptom | Fix |
|---|---|
| Nothing gets targeted | Enemy missing `IATSTargetableInterface` or `UATSTargetPointComponent`, or `ObjectsToQuery` doesn't include its object type |
| Target found but camera doesn't lock | `TargetingType = EDontLock`, or `LockMagnetism = 0` |
| Camera snaps too hard / jitters | Lower `LockMagnetism`, or use `EMagneticLockYawOnly` |
| Can't switch targets with the stick | `InputTrasholdForSearch` too high, or input not bound to `RightSearchTargetWithInput`/`UpSearchTargetWithInput` |
| Locks onto dead/friendly actors | Add a `UATSTargetingFilter` that rejects them via `IsActorTargetable` |
| Target stays locked behind walls | Enable `bStopTargetingIfOutOfSight` |
| Out-of-range enemies get locked | Lower `MaxTargetingDistance` / `MaxAngularDistanceDegree` |
