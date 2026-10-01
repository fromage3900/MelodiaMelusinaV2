---
name: vehicle-system
description: Set up drivable ACF vehicles (wheeled Chaos cars, physics boats, and kinematic flying ships) with mount/dismount, combat-team integration and damage using the VehicleSystem module.
globs: []
alwaysApply: false
---

# Vehicle System — ACF Ultimate

The **VehicleSystem** module adds drivable vehicles that plug into ACF's combat, team, interaction and mounting systems. It provides three flavours: a **wheeled** vehicle built on Unreal's Chaos `AWheeledVehiclePawn`, a **boat** driven by a physics-thrust `UACFWaterVehicleComponent`, and a **flying ship** driven by a kinematic `UACFFlyComponent`. Wheeled and boat pawns already carry ACF combat plumbing — `UARSStatisticsComponent`, `UACFDamageHandlerComponent`, `UACFEffectsManagerComponent`, a `UACFTeamComponent`, AI perception stimuli — and implement `IACFEntityInterface` and `IACFInteractableInterface`, so players enter them through the standard interaction prompt and they can take damage / be destroyed.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Wheeled vehicle | `AACFWheeledVehiclePawn` | `/AscentCombatFramework/Vehicles/` | Chaos car; mountable, damageable, team-aware |
| Boat | `AACFBoatVehiclePawn` | `/AscentCombatFramework/Vehicles/` | Physics boat using `UACFWaterVehicleComponent` |
| Flying ship | `AACFFlyingVehicle` | `/AscentCombatFramework/Vehicles/` | Kinematic 6DOF ship using `UACFFlyComponent` |
| Water movement | `UACFWaterVehicleComponent` | on the boat pawn | Thrust + steering torque on a simulating mesh |
| Flight movement | `UACFFlyComponent` | on the flying pawn | Input smoothing + takeoff/land state machine |

> **Never edit sample assets.** Duplicate the sample vehicle pawns into `Content/YourGame/Vehicles/` and customize **your copies** (mesh, physics asset, stats, input).

### Key members

| Class | Notable members |
|---|---|
| `AACFWheeledVehiclePawn` | `GetMountComponent()` (`UACFMountableComponent`), `GetDismountPoint()`, `GetStatisticsComponent()`, `GetDamageHandlerComponent()`, `OnVehicleDestroyed()`, `VehicleName` |
| `AACFBoatVehiclePawn` | `GetWaterVehicleComponent()`, `GetMountComponent()`, `GetMesh()`, same combat/team interfaces |
| `AACFFlyingVehicle` | `GetFlyComponent()`, `GetMesh()` (root skeletal mesh = movement collision), `InputMappingContext`, `InputMappingPriority` |
| `UACFWaterVehicleComponent` | `AddThrust(-1..1)`, `AddSteering(-1..1)`, `ThrustForce`, `SteeringTorque`, `bAlignVelocityToForward`, `PhysicsMeshTag` |
| `UACFFlyComponent` | `AddForward/Strafe/Vertical/Yaw/Pitch/RollInput`, `EnableFly`, `TakeOff`, `Land`, `GetFlyPhase()` (`EACFFlyPhase`), delegates |

---

## 2 — Setup / Configuration

### A. Wheeled vehicle (Chaos)

1. Duplicate the sample `AACFWheeledVehiclePawn` BP into `Content/YourGame/Vehicles/`.
2. Assign your skeletal mesh, **Chaos Vehicle Movement** wheel setup, and physics asset (standard Chaos Vehicle workflow).
3. Configure the ACF combat components in the BP defaults: `StatisticsComp` attribute set, `DamageHandlerComp`, effects, and the `TeamComponent` combat team.
4. Set `VehicleName` (shown in the interaction prompt).
5. The pawn already has a `UACFMountableComponent` and a `UACFMountPointComponent` dismount point — position the dismount point where the driver should appear on exit.

### B. Boat (physics)

1. Duplicate the sample `AACFBoatVehiclePawn` into `Content/YourGame/Vehicles/`.
2. Assign a **simulating** skeletal/primitive mesh (the hull). `UACFWaterVehicleComponent` auto-resolves the mesh at BeginPlay: tagged-by-`PhysicsMeshTag` first, then the first simulating mesh.
3. Tune `ThrustForce`, `SteeringTorque`, and `bAlignVelocityToForward` / `VelocityAlignmentSpeed` to reduce lateral drift.

### C. Flying ship (kinematic)

1. Duplicate the sample `AACFFlyingVehicle` into `Content/YourGame/Vehicles/`.
2. The **root skeletal mesh** is the movement collision surface — set its collision profile and **Physics Asset** to the real hull so wings/hull don't clip terrain.
3. Add a `UFloatingPawnMovement` to the pawn — `UACFFlyComponent` forwards linear input to it (it is auto-discovered).
4. Set `bUseControllerRotationPitch/Yaw/Roll = true` so the mesh follows control rotation.
5. Assign an `InputMappingContext` (and `InputMappingPriority`) — it is added automatically when the pawn is possessed and removed on unpossess.
6. Tune `LinearInputSmoothing`, `AngularInputSmoothing`, `AngularSensitivity`, and takeoff/landing params (`TakeOffAltitude`, `LandingGroundOffset`, etc.).

---

## 3 — Core Workflow / Runtime API

### Boat driving

```
// Each frame from input (-1..1):
BoatPawn->GetWaterVehicleComponent()->AddThrust(ForwardAxis);
BoatPawn->GetWaterVehicleComponent()->AddSteering(SteerAxis);
```

### Flying ship

```
UACFFlyComponent* Fly = Ship->GetFlyComponent();

// Begin/end flight + phase transitions (Server RPCs, server-authoritative):
Fly->EnableFly(true);
Fly->TakeOff();          // Grounded -> TakingOff -> Flying
Fly->Land();             // Flying  -> Landing  -> Grounded
Fly->CancelPhaseTransition();

// Per-frame input (smoothed internally):
Fly->AddForwardInput(Throttle);
Fly->AddStrafeInput(Strafe);
Fly->AddVerticalInput(Up);
Fly->AddYawInput(Yaw);
Fly->AddPitchInput(Pitch);
Fly->AddRollInput(Roll);

// Queries:
EACFFlyPhase Phase = Fly->GetFlyPhase();   // Grounded / TakingOff / Flying / Landing
bool bLocked = Fly->IsInputLocked();        // true during takeoff/landing if configured
```

React to phase changes via delegates: `OnFlyPhaseChanged`, `OnTakeOffCompleted`, `OnLandingCompleted`, `OnFlyStateChanged`.

> Phase control RPCs (`EnableFly`, `TakeOff`, `Land`) are **server-authoritative** — clients request, the server switches and replicates `CurrentPhase`.

### Wheeled vehicle combat

`AACFWheeledVehiclePawn` and `AACFBoatVehiclePawn` route `TakeDamage` through `UACFDamageHandlerComponent`; when health hits zero `OnVehicleDestroyed()` fires (a `BlueprintNativeEvent` — override for explosion FX / cleanup). Team relationships come from `UACFTeamComponent` via `IACFEntityInterface`.

---

## 4 — Wire to Characters / Blueprints

### Enter / exit (mount-based, wheeled & boat)

1. These pawns implement `IACFInteractableInterface` — the player's interaction component shows the prompt from `GetInteractableName()`.
2. On interact, mount the player using the vehicle's `GetMountComponent()` (`UACFMountableComponent`) — the same mount flow as the Mount System.
3. On exit, the player is placed at `GetDismountPoint()`.
4. Drive by forwarding player input to the relevant movement API (Chaos throttle/steer for wheeled, `AddThrust/AddSteering` for boats).

### Flying ship possession

1. The flying ship is a `AACFActor` pawn — possess it with the player controller (e.g. swap possession on enter).
2. On possession, its `InputMappingContext` is auto-added; bind the mapping's actions to the `UACFFlyComponent` `Add*Input` calls.
3. Call `EnableFly(true)` + `TakeOff()` to leave the ground.

---

## 5 — Verify

**Checklist before testing:**

- [ ] Vehicle pawns duplicated into `Content/YourGame/Vehicles/`.
- [ ] **Wheeled:** Chaos vehicle movement + wheels + physics asset configured; `VehicleName` set.
- [ ] **Boat:** hull mesh is **simulating physics**; `PhysicsMeshTag` set or auto-resolve works.
- [ ] **Flying:** root skeletal mesh has correct collision + Physics Asset; `UFloatingPawnMovement` present; `bUseControllerRotation*` enabled; `InputMappingContext` assigned.
- [ ] Mount component + dismount point positioned (wheeled/boat).
- [ ] `TeamComponent`, `StatisticsComp`, `DamageHandlerComp` configured for combat vehicles.
- [ ] Input bound to the correct movement API for each vehicle type.

**Common failures:**

| Symptom | Fix |
|---|---|
| Boat doesn't move | Hull mesh isn't simulating physics, or `UACFWaterVehicleComponent` resolved the wrong mesh (set `PhysicsMeshTag`) |
| Boat slides sideways on turns | Enable `bAlignVelocityToForward` / raise `VelocityAlignmentSpeed` |
| Flying ship clips through terrain | Root mesh has no Physics Asset / wrong collision profile — sweeps use the mesh bodies |
| Ship rotates but doesn't translate | Missing `UFloatingPawnMovement` (FlyComponent forwards linear input to it) |
| Ship input does nothing after possession | `InputMappingContext` not assigned, or actions not bound to `Add*Input` |
| Takeoff/landing never completes | `TakeOffAltitude` / `LandingTraceDistance` / `LandingGroundOffset` misconfigured |
| No interaction prompt on vehicle | Player lacks an interaction component, or `CanBeInteracted` returns false |
| Vehicle invincible | `DamageHandlerComp` / `StatisticsComp` not initialized; check the attribute set has Health |
| Phase desync in multiplayer | Don't call phase RPCs on clients expecting instant change — they're server-authoritative |
