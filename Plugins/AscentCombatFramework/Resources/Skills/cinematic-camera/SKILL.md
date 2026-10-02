---
name: cinematic-camera
description: Drive cinematic and dialogue cameras, camera events, target locks, level sequences, and camera points with the ACF Cinematic Camera Manager (CCM) module.
globs: []
alwaysApply: false
---

# Cinematic Camera — ACF Ultimate

The **Cinematic Camera Manager (CCM)** replaces the default `APlayerCameraManager` with `ACCMPlayerCameraManager`, adding data-driven **camera events** (offset/FOV/shake presets from a DataTable), **target locking**, **camera point blending** (`UACFCameraPointComponent`), automated **movement presets** (orbit, crane, pan), and **gameplay level sequences** with runtime actor bindings. It is what powers dialogue framing, lock-on, and battle/cinematic cameras. Most gameplay calls go through the Blueprint function library `UCCMCameraFunctionLibrary`.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Camera manager | `ACCMPlayerCameraManager` | Set as `PlayerCameraManagerClass` on your PlayerController | Runtime camera brain (events, locks, sequences) |
| Camera movements table | `UDataTable` (row `FCCMCameraMovementSettings`) | `/AscentCombatFramework/.../Camera/` | Named offset/FOV/shake presets for camera events |
| Camera point | `UACFCameraPointComponent` | Added on actors (NPCs, arenas, dialogue rigs) | Tagged `UCineCameraComponent` you can blend to |
| Sequence binding | `FCCMSequenceBinding` | Built at call time | Binds tag names in a Level Sequence to runtime actors |

> **Never edit sample assets.** Duplicate the camera movements DataTable and any camera-rig Blueprints into `Content/YourGame/Camera/` and customize your copies.

### Key classes

| Class | Role |
|---|---|
| `ACCMPlayerCameraManager` | Custom `APlayerCameraManager`; runs camera events, locks, follow, sequences |
| `UCCMCameraFunctionLibrary` | Static Blueprint API — the main entry point for gameplay |
| `UACFCameraPointComponent` | `UCineCameraComponent` resolved by `CameraTag`, with movement presets |
| `FCCMCameraMovementSettings` | DataTable row: `CameraOffset`, `FOV`, `Shake`, interp speeds |
| `FACFCameraMovementConfig` | Per-point movement preset (`EACFCameraMovementPreset`: orbit/crane/pan/custom) |
| `FCCMSequenceBinding` | `{ TagName, BoundActor }` used by `PlayGameplaySequenceWithBinding` |
| `ELockType` | `EYawOnly` / `EAllAxis` lock behaviour |

---

## 2 — Setup / Configuration

1. Set your PlayerController's **`PlayerCameraManagerClass`** to `ACCMPlayerCameraManager` (or a Blueprint subclass of it). Duplicate the sample camera-manager Blueprint into `Content/YourGame/Camera/` if you customize it.
2. Duplicate the sample **Camera Movements DataTable** (row struct `FCCMCameraMovementSettings`) into `Content/YourGame/Camera/`, then assign it to **`CameraMovements`** on your camera manager.
3. Add rows to the DataTable — each **row name** is the `CameraEventName` you trigger at runtime. Per row set:
   - `CameraOffset` — positional offset applied to the camera.
   - `FOV` — additive field-of-view change.
   - `Shake` (+ `ShakeIntensity`, `bShakeLooping`) — `UCameraShakeBase` class.
   - `InterpSpeed` / `FovInterpSpeed` — blend smoothing.
4. For framed shots (dialogue, finishers, arena cams), add `UACFCameraPointComponent` to the relevant actor and set its **`CameraTag`** (e.g. `Camera.Dialogue.NPC`, `Camera.Battle.Attack1`) and optional **`MovementConfig`** preset.

---

## 3 — Core Workflow / Runtime API

All functions below are static on `UCCMCameraFunctionLibrary` (category **CCM**) and need a World Context.

### Camera events (offset / FOV / shake presets)

```
// Apply a named preset until stopped:
UCCMCameraFunctionLibrary::TriggerCameraEvent(WorldContext, "CombatZoom");

// Apply for a fixed duration, then auto-revert:
UCCMCameraFunctionLibrary::TriggerTimedCameraEvent(WorldContext, "HitFocus", 0.5f);

// Stop a running event:
UCCMCameraFunctionLibrary::StopCameraEvent(WorldContext, "CombatZoom");

// Snap/blend back to the default camera:
UCCMCameraFunctionLibrary::ResetCameraPosition(WorldContext, /*bInstantReset*/ false);
```

### Target lock (lock-on)

```
// Lock onto an actor (yaw only or all axes):
UCCMCameraFunctionLibrary::LockCameraOnActor(WorldContext, TargetActor, ELockType::EYawOnly, /*strength*/ 5.f);

// Lock onto a component (e.g. a bone/socket scene component):
UCCMCameraFunctionLibrary::LockCameraOnComponent(WorldContext, SceneComp, ELockType::EAllAxis, 5.f);

// Release the lock:
UCCMCameraFunctionLibrary::StopLockingCameraOnActor(WorldContext);
```

### Blending to a tagged camera point

Use camera points for dialogue and scripted shots. On the manager, `BlendToPoint` / `PlayCameraBlend` resolve a `UACFCameraPointComponent` by tag on a target actor:

```
ACCMPlayerCameraManager* Cam = UCCMCameraFunctionLibrary::GetLocalCinematicCameraManager(WorldContext);

// Blend to the camera point tagged "Camera.Dialogue.NPC" on NpcActor:
Cam->PlayCameraBlend(NpcActor, FGameplayTag::RequestGameplayTag("Camera.Dialogue.NPC"),
                     /*BlendTime*/ 1.f, VTBlend_Cubic, /*BlendExp*/ 2.f, /*bLockOutgoing*/ false);
```

### Gameplay level sequences with bindings

```
TArray<FCCMSequenceBinding> Bindings;
Bindings.Add(FCCMSequenceBinding("Player", PlayerActor));
Bindings.Add(FCCMSequenceBinding("Enemy",  EnemyActor));

UCCMCameraFunctionLibrary::PlayGameplaySequenceWithBinding(
    WorldContext, MyLevelSequence, PlayerActor->GetActorTransform(), Bindings);

// Stop it (only one sequence plays at a time):
UCCMCameraFunctionLibrary::StopSequence(WorldContext);
```

### Movement presets on a camera point

`UACFCameraPointComponent` can auto-move while active:

```
PointComp->SetMovementPreset(EACFCameraMovementPreset::RotateAroundOwner);
PointComp->SetMovementSpeed(20.f);   // deg/sec for orbit
PointComp->StopMovement();           // pause / ResumeMovement() / ResetMovement()
```

### Key delegates (on `ACCMPlayerCameraManager`)

| Delegate | Fires when |
|---|---|
| `OnCameraSequenceStarted (FName)` | A camera sequence begins |
| `OnCameraSequenceEnded (FName)` | A camera sequence ends |

---

## 4 — Wire to Characters / Blueprints

- **Dialogue cameras (most common):** place a `UACFCameraPointComponent` on the NPC (or dialogue rig), tag it (e.g. `Camera.Dialogue.NPC`). When dialogue starts, call `PlayCameraBlend`/`BlendToPoint` to that tag; on dialogue end, `ResetCameraPosition`. (See the `configure-dialogue` skill for the dialogue side.)
- **Combat / lock-on:** when the targeting system selects a target, call `LockCameraOnActor`; clear it with `StopLockingCameraOnActor` when the target is lost.
- **Hit feedback:** fire `TriggerTimedCameraEvent` on big hits/finishers for a quick zoom + shake.
- **Animation-driven shots:** the module ships `CCMStartSequenceNotify` / `CCMSequenceNotifyState` anim notifies — add them to montages to trigger camera events/sequences from animation.
- **Cutscenes:** drive `PlayGameplaySequenceWithBinding` with a `ULevelSequence`, binding scene tags to live actors so the same sequence works for any participants.

---

## 5 — Verify

**Checklist before testing:**

- [ ] `PlayerCameraManagerClass` on the PlayerController is `ACCMPlayerCameraManager` (or a subclass).
- [ ] `CameraMovements` DataTable assigned, with row names matching every `CameraEventName` you trigger.
- [ ] Camera points have a valid, unique `CameraTag` and exist on the actor you pass to the blend call.
- [ ] Level Sequence binding tag names match the `FCCMSequenceBinding.TagName` values you pass.
- [ ] Lock calls are paired with a `StopLockingCameraOnActor`.

**Common failures:**

| Symptom | Fix |
|---|---|
| `TriggerCameraEvent` does nothing | Row name not found in `CameraMovements`, or DataTable not assigned |
| Camera never reverts | Missing `StopCameraEvent` / `ResetCameraPosition`; or used `TriggerCameraEvent` (untimed) and never stopped it |
| Blend-to-point fails | `CameraTag` mismatch, or the point component isn't on the actor passed to the blend |
| Lock-on jitters / wrong axis | Wrong `ELockType`; tune `lockStrength` |
| Sequence actors not animating | `FCCMSequenceBinding.TagName` doesn't match the sequence's binding tracks |
| Two sequences fight | Only one gameplay sequence plays at once — starting a new one stops the previous; call `StopSequence` first if needed |
| `GetLocalCinematicCameraManager` returns null | Local PlayerController's camera manager isn't a `ACCMPlayerCameraManager` |
