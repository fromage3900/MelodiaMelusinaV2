---
name: character-controller
description: Configure ACF's extended character movement — locomotion states, rotation/stances, climbing, ladders, and vaulting — using the CharacterController module.
globs: []
alwaysApply: false
---

# Character Controller — ACF Ultimate

The **CharacterController** module replaces the stock `UCharacterMovementComponent` with **`UACFCharacterMovementComponent`**, a replicated movement component built around **locomotion states** (Idle/Walk/Jog/Sprint), **rotation modes** (forward-facing vs strafing), **movement stances** (idle/aiming/block/custom), and per-state speed/attribute modifiers. Optional companion components add traversal: **`UACFClimbingComponent`** (free wall climbing + ledge climb-up), **`UACFLadderComponent`** (ability + motion-warp ladder climbing), and **`UACFVaultComponent`** (vault/mantle over obstacles). All of these drive `UACFAnimInstance` for animation.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Player/AI character BP | `AACFCharacter` (+ `UACFCharacterMovementComponent`) | `/AscentCombatFramework/.../Blueprint/` | Pawn with the extended movement component |
| Anim Instance | `UACFAnimInstance` | duplicate from sample ABP | Reads locomotion state/stance/moveset for the AnimGraph |
| Anim Set | `UACFAnimsetDataAsset` | `/AscentCombatFramework/Animations/` | Per-moveset/overlay animation layers |
| Ladder actor BP | (Blueprint with reach points) | `/AscentCombatFramework/.../Ladder/` | Climbable ladder with `ReachPoint-Top/Bottom` |

> **Never edit sample assets.** Duplicate character Blueprints, anim Blueprints and anim sets into `Content/YourGame/...` and wire your copies. Sample assets under `/AscentCombatFramework/` are overwritten on every plugin update.

### Key classes & types

| Symbol | Role |
|---|---|
| `UACFCharacterMovementComponent` | Extended CMC: locomotion states, rotation mode, stances, aim, climbing delegation |
| `UACFClimbingComponent` | Free-surface wall climbing, corner handling, ledge detection & climb-up |
| `UACFLadderComponent` | Ladder climbing via abilities + Motion Warping |
| `UACFVaultComponent` | `UBoxComponent` that detects vaultable actors and triggers vault/mantle actions |
| `ELocomotionState` | `EIdle`, `EWalk`, `EJog`, `ESprint` |
| `ERotationMode` | `EForwardFacing`, `EStrafing` |
| `EMovementStance` | `EIdle`, `EAiming`, `EBlock`, `ECustom` |
| `FACFLocomotionState` | Per-state config: `State`, `MaxStateSpeed`, `MaxStateSwimSpeed`, `StateModifier` (ARS) |
| `FAimOffset` / `FCharacterGroundInfo` | Aim yaw/pitch; ground hit/distance/slope info |

---

## 2 — Setup / Configuration

1. Base your player/AI pawn on **`AACFCharacter`**, or set the character's movement component class to **`UACFCharacterMovementComponent`** (ACF characters use it by default).
2. On the movement component, configure under **ACF|Movement**:
   - **`LocomotionStates`** — array of `FACFLocomotionState`. Add one entry per `ELocomotionState` you use and set **`MaxStateSpeed`** (and `MaxStateSwimSpeed`). Optionally set an ARS `StateModifier`.
   - **`DefaultState`** — starting locomotion state (default `EJog`).
   - **`SprintDirectionCone`** — max angle from forward that still allows sprint.
3. Under **ACF|Controller**, tune **`TurnRate`** / **`LookUpRate`**.
4. Add traversal components as needed:
   - **`UACFClimbingComponent`** for free climbing.
   - **`UACFLadderComponent`** for ladders (requires `UACFAbilitySystemComponent` + `UMotionWarpingComponent` on the same actor).
   - **`UACFVaultComponent`** (a box volume) for vault/mantle.

---

## 3 — Core Workflow / Runtime API

### Locomotion, rotation, stances

```
// Locomotion state (Server RPCs — call on owning client, executes on server)
MoveComp->SetLocomotionState(ELocomotionState::ESprint);
MoveComp->AccelerateToNextState();          // Walk → Jog → Sprint
MoveComp->BrakeToPreviousState();
MoveComp->ResetToDefaultLocomotionState();
MoveComp->SetLocomotionStateSpeed(State, Speed, SwimSpeed);   // override at runtime

// Rotation mode (local + server-authorised)
MoveComp->SetRotationMode(ERotationMode::EStrafing);
bool bStrafing = MoveComp->IsCharacterStrafing();

// Aiming
MoveComp->SetIsAiming(true);                // Server RPC; fires OnAimChanged
bool bAiming = MoveComp->GetIsAiming();

// Stances (Server RPCs)
MoveComp->ActivateLocomotionStance(BlockTag);
MoveComp->DeactivateCurrentLocomotionStance();

// Gating movement
MoveComp->SetCanMove(false);                // Server RPC
```

### Movement input helpers

`MoveForward(Value)`, `MoveRight(Value)`, `MoveUp(Value)`, `TurnAtRate(Rate)`, `LookUpAtRate(Rate)`, `TurnAtRateLocal(Value)`. Query input with `GetWorldMovementInputVector()`, `GetCameraMovementInputVector()`, `GetCurrentInputDirection()`.

### Queries

`GetCharacterMaxSpeed()`, `GetCurrentLocomotionState()`, `GetTargetLocomotionState()`, `GetRotationMode()`, `GetCurrentLocomotionStance()`, `GetAimOffset()`, `GetGroundInfo()`, `GetGroundDistance()`.

### Movement component delegates

| Delegate | Fires when |
|---|---|
| `OnLocomotionStateChanged(State)` | Current locomotion state changes |
| `OnTargetLocomotionStateChanged(State)` | Target state changes |
| `OnLocomotionStanceChanged(stance)` | Movement stance changes |
| `OnRotationModeChanged(rotMode)` | Rotation mode changes |
| `OnAimChanged(bIsAiming)` | Aim toggled |
| `OnMovementModeChangedEvent(mode)` | UE movement mode changes |

### Climbing (`UACFClimbingComponent`)

```
ClimbComp->TryClimbing();             // attempt to attach to a nearby wall
ClimbComp->RequestExitClimbing();     // request detach
ClimbComp->CancelClimbing();
bool bClimbing = ClimbComp->IsClimbing();
FVector N = ClimbComp->GetClimbSurfaceNormal();
```

Configure detection (**`ClimbDetectionDistance`**, **`ClimbableObjectTypes`** — set your meshes to a custom Object Type or it falls back to WorldStatic), movement (**`MaxClimbingSpeed`**, **`MaxClimbingAcceleration`**), auto-climb (**`bAutoClimb`**, **`bAutoClimbOnlyWhenFalling`**), and ledge offsets. For montage-driven enter/exit, bind `OnEnterClimbRequested`/`OnExitClimbRequested` and call `ConfirmEnterClimb()` / `BeginClimbingFromAbility()` / `ConfirmExitClimbing()`. Delegate: `OnClimbingStateChanged(bIsClimbing)`.

### Ladders (`UACFLadderComponent`)

```
LadderComp->SetLadder(LadderActor);   // on overlap/approach
LadderComp->InitiateLadderClimb();    // on interact input (runs all checks)
LadderComp->HandleClimbInput(Axis);   // +up / -down while climbing
LadderComp->ExitLadderClimb();
```

Set **`StartAbility`** / **`EndAbilityTag`** (ladder climb ability tags), **`ClimbUp/Down/LoopTag`** payload tags, **`InteractDistance`**, **`FacingTolerance`**. Ladder actor needs `ReachPoint-Bottom`, `ReachPoint-Top`, `DefaultSceneRoot` scene components and a `HasValidPlacement` bool. Delegates: `OnLadderClimbStarted/Ended`, `OnLadderSet`.

### Vaulting (`UACFVaultComponent`)

```
VaultComp->SetVaultingEnabled(true);
bool bCan = VaultComp->CanVault();
AActor* Target = VaultComp->GetActorToVault();
```

Set **`VaultActionTag`** / **`MantleActionTag`** (action ability tags), **`VaultablesChannel`** (collision channel of vaultable geometry), and **`bAutoEnable`**. When `CanVault()` is true, trigger the vault/mantle action via the Actions System. Delegate: `OnActivationChanged(isActive)`.

---

## 4 — Wire to Characters / Blueprints

1. **Input → movement:** in your player pawn's input setup, bind axes to `MoveForward`/`MoveRight`, look to `TurnAtRate`/`LookUpAtRate`, sprint to `AccelerateToNextState`/`SetLocomotionState`, and aim/block to `SetIsAiming`/`ActivateLocomotionStance`.
2. **Animation:** use a `UACFAnimInstance`-derived Anim Blueprint. It reads `GetCurrentLocomotionState`, `GetCurrentLocomotionStance`, `GetAimOffset`, current moveset/overlay tags (`SetCurrentMoveset`/`SetCurrentOverlay`) and the climbing/ladder flags to pick poses.
3. **Traversal:** add the climbing/ladder/vault components in the pawn Blueprint and assign their gameplay tags to abilities that exist in your moveset (Actions System). Ladder & vault rely on triggering ACF action abilities by tag.
4. **Networking:** state-changing calls (`SetLocomotionState`, `SetRotationMode`, `SetIsAiming`, `ActivateLocomotionStance`, climbing) are server RPCs / replicated — call them on the owning client; the component handles replication.

---

## 5 — Verify

**Checklist before testing:**

- [ ] Pawn uses `UACFCharacterMovementComponent` (default on `AACFCharacter`).
- [ ] `LocomotionStates` array has an entry per state with non-zero `MaxStateSpeed`.
- [ ] `DefaultState` set; sprint cone configured.
- [ ] Anim Blueprint derives from `UACFAnimInstance` and is assigned on the mesh.
- [ ] Climbing: `ClimbableObjectTypes` set (or geometry is WorldStatic); detection distance reasonable.
- [ ] Ladder: `StartAbility`/`EndAbilityTag` set; ladder actor has `ReachPoint-Top/Bottom`, `DefaultSceneRoot`, `HasValidPlacement`; pawn has `UACFAbilitySystemComponent` + `UMotionWarpingComponent`.
- [ ] Vault: `VaultActionTag`/`MantleActionTag` map to real abilities; `VaultablesChannel` matches obstacle collision.
- [ ] Movement-changing calls made on the owning client (they replicate via server).

**Common failures:**

| Symptom | Fix |
|---|---|
| Character never sprints | No `ESprint` entry in `LocomotionStates`, or moving outside `SprintDirectionCone` |
| Speed never changes between states | `MaxStateSpeed` is 0 for that `FACFLocomotionState` |
| Strafe/aim not reflected in animation | Anim Blueprint not derived from `UACFAnimInstance`, or not reading rotation mode/aim offset |
| Climbing never attaches | `ClimbableObjectTypes` doesn't match the wall's Object Type; detection distance too short |
| Climb desyncs in multiplayer | State changed on simulated proxy — call climbing functions on the owning client (server RPCs) |
| Ladder interact does nothing | Failed `LadderClimbChecks` — distance/facing out of tolerance, missing reach points, or abilities not granted |
| Vault never triggers | `VaultablesChannel` mismatch, component disabled (`SetVaultingEnabled`), or vault action tag not in moveset |
| Movement change reverts instantly | Called on a non-owning client; replicated value overwrote it — use the server RPC setters |
