---
name: mount-system
description: Set up rideable mounts with the ACF Mount System module (rider + mountable components, mount points, mount/dismount abilities) including attach, camera blend, possession swap, and AI rider control.
globs: []
alwaysApply: false
---

# Mount System — ACF Ultimate

The **Mount System** module (`MountSystem`) lets ACF characters mount and ride other pawns (horses, vehicles, companions). The rider carries a `UACFRiderComponent`; the rideable pawn carries a `UACFMountableComponent` (or `UACFMountComponent` for companions) plus `UACFMountPointComponent`s marking attach/dismount sockets. Mounting and dismounting are driven by GAS abilities (`UACFMountActionAbility` / `UACFDismountActionAbility`) that motion-warp the rider into place, then perform attachment, a smooth camera blend, and a deferred possession swap — all server-authoritative and replicated. AI mounts are steered with `AACFRiderAIController` and animated via `UACFRiderAnimInstance`.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Sample mount pawn | Character/Pawn BP with `UACFMountableComponent` | `/AscentCombatFramework/.../Mounts/` | The rideable creature/vehicle |
| Sample mount action | `UACFMountActionAbility` | `/AscentCombatFramework/Actions/` | Ability that mounts the rider |
| Sample dismount action | `UACFDismountActionAbility` | `/AscentCombatFramework/Actions/` | Ability that dismounts the rider |
| Rider anim blueprint | `UACFRiderAnimInstance` (parent) | `/AscentCombatFramework/.../Mounts/` | Riding pose/locomotion for the rider |

> **Never edit sample assets.** Duplicate the sample mount pawn, abilities, and anim BP into `Content/YourGame/Mounts/` (and `Content/YourGame/Actions/`) and customize your copies — sample assets are overwritten on plugin/sample updates.

### Key classes

| Class | Role |
|---|---|
| `UACFRiderComponent` | On the rider character. `StartMount` / `StartDismount`, `IsRiding`, `GetMount`, `GetMountComp`, `GetMountTypeTag`; fires `OnRidingStateChanged` |
| `UACFMountableComponent` | On the rideable pawn. Mount config + `StartMount`/`StopMount`, mount-point lookup, `TriggerActionOnRider`; fires `OnMountedStateChanged` |
| `UACFMountComponent` | `UACFMountableComponent` subclass adding `bIsPlayerCompanion` / `IsCompanion()` |
| `UACFMountPointComponent` | Scene component marking a mount/dismount socket, identified by `PointTag` |
| `UACFMountActionAbility` | GAS action: warps rider to the mount socket, then calls `StartMount` (attach + camera blend + possession) |
| `UACFDismountActionAbility` | GAS action: plays dismount montage, then `StartDismount` (camera blend back + possession swap + detach) |
| `AACFRiderAIController` | AI controller for mounts; can override control rotation with the mount's rotation |
| `UACFRiderAnimInstance` | Anim instance driving the rider's riding pose |
| `UACFMountSystemFunctionLibrary` | Helpers e.g. `GetLocalRiderPlayerCharacter` (returns the player even when possessing the mount) |

---

## 2 — Setup / Configuration

### A. Set up the mountable pawn

1. Duplicate the sample mount pawn into `Content/YourGame/Mounts/` (or add components to your own pawn).
2. Add a `UACFMountableComponent` (or `UACFMountComponent` for a player companion). Configure:
   - **`MountTypeTag`** — identifies the mount type (e.g. `Mount.Horse`).
   - **`MountActionTag`** — the action tag used to trigger mounting (must match the mount ability's trigger tag).
   - **`MountPointSocket`** — skeletal mesh socket the rider attaches to.
   - **`DefaultDismountPoint`** — socket/tag used when no explicit dismount point is given.
   - **`bPossessMount`** — true to make the rider's controller possess the mount pawn while riding (default true).
   - For `UACFMountComponent`: **`bIsPlayerCompanion`** if it's a companion.
3. Add one or more `UACFMountPointComponent`s positioned where the rider should dismount; set each **`PointTag`**.
4. Assign the mount's anim blueprint (duplicate of the sample `UACFRiderAnimInstance`-based BP) on the rider mesh as appropriate.

### B. Set up the rider character

1. Add a `UACFRiderComponent` to your character (it is `BlueprintSpawnableComponent`).
2. Duplicate `UACFMountActionAbility` and `UACFDismountActionAbility` into `Content/YourGame/Actions/`.
3. On the **mount ability**, configure (see header guidance):
   - Assign it to the rider's ability set under the same tag as `UACFMountableComponent::MountActionTag`.
   - Set `ActionConfig.MontageReproductionType = EMotionWarped` and `ActionConfig.WarpInfo.SyncPoint` to the montage's MotionWarping notify name (default `MountPoint`).
4. On the **dismount ability**:
   - Optionally set `DismountPointName` (leave `NAME_None` to use the mount's `DefaultDismountPoint`).
   - For warped dismounts, set `bWarpToDismountPoint = true`, `MontageReproductionType = EMotionWarped`, and `WarpInfo.SyncPoint`.

---

## 3 — Core Workflow / Runtime API

### Mounting

The mount ability is triggered on the rider with a payload whose **TargetActor is the mount pawn**. The ability resolves the mountable component automatically, warps the rider to the mount socket, and on montage end calls `StartMount`:

```
// Trigger the mount action on the rider's ability system, payload.TargetActor = MountPawn.
// (e.g. from interaction: "Press E to ride")
RiderActionsComp->TriggerAction(MountActionTag, EActionPriority::EHigh /*, payload with TargetActor = mount*/);

// What StartMount does internally:
//  - attaches the rider to MountPointSocket (camera frozen)
//  - smooth camera blend rider view -> mount view
//  - deferred possession swap to the mount after the blend
RiderComp->StartMount(MountableComp);   // server RPC; also callable directly
```

### Dismounting

Because the controller possesses the **mount** while riding, the dismount action must be triggered on the **rider** through the mountable component:

```
// On the mount pawn:
MountableComp->TriggerActionOnRider(DismountActionTag, EActionPriority::EHigh);

// On montage end -> StartDismount: camera blend back, possession swap to rider, detach
RiderComp->StartDismount(DismountPointName);   // server RPC
```

### Queries & events

```
bool bRiding = RiderComp->IsRiding();
APawn* Mount = RiderComp->GetMount();
UACFMountableComponent* MComp = RiderComp->GetMountComp();
FGameplayTag Type = RiderComp->GetMountTypeTag();
RiderComp->OnRidingStateChanged.AddDynamic(...);     // (bool bIsRiding)

bool bMounted = MountableComp->IsMounted();
bool bFree    = MountableComp->CanBeMounted();
ACharacter* Rider = MountableComp->GetRider();
UMeshComponent* Mesh = MountableComp->GetMountMesh();
FName Near = MountableComp->GetNearestMountPointTag(WorldLoc);
MountableComp->OnMountedStateChanged.AddDynamic(...); // (bool inIsMounted)
```

### Triggering actions while mounted

```
// Run abilities on the rider while riding (e.g. mounted attacks):
MountableComp->TriggerActionOnRider(AttackTag, EActionPriority::ELow, false);
MountableComp->ReleaseSustainedActionOnRider(BlockTag);
```

### Local player helper

```
// Returns the local player character even when the controller is possessing the mount:
AACFCharacter* Player = UACFMountSystemFunctionLibrary::GetLocalRiderPlayerCharacter(WorldContext);
```

---

## 4 — Wire to Characters / Blueprints

1. **Rider character:** add `UACFRiderComponent`; register the duplicated mount/dismount abilities in the rider's `UACFAbilitySet` under the right tags.
2. **Mount pawn:** add `UACFMountableComponent`/`UACFMountComponent`, set `MountTypeTag`, `MountActionTag`, `MountPointSocket`, and add `UACFMountPointComponent`s for dismount spots.
3. **Interaction:** wire the mount's interactable so "interact" triggers the mount action on the rider with the mount as TargetActor (duplicate the sample interactable BP per the project rule; never edit the sample).
4. **Camera & possession** are handled by the abilities/`UACFRiderComponent` — ensure `bPossessMount` matches your desired control scheme.
5. **AI mounts:** use `AACFRiderAIController` on AI riders; set `bOverrideControlWithMountRotation` and the clamp/offset rotators so aim follows the mount.
6. **Animation:** assign the rider riding anim BP (duplicate of the sample using `UACFRiderAnimInstance`).

---

## 5 — Verify

**Checklist before testing:**

- [ ] Mount pawn, abilities, and anim BP are duplicated into your content (samples untouched).
- [ ] `UACFRiderComponent` is on the rider character.
- [ ] `UACFMountableComponent` on the mount has `MountTypeTag`, `MountActionTag`, and `MountPointSocket` set.
- [ ] At least one `UACFMountPointComponent` with a `PointTag` exists for dismounting.
- [ ] Mount/dismount abilities registered in the rider's ability set; mount ability tag == `MountActionTag`.
- [ ] Mount ability uses `EMotionWarped` with `WarpInfo.SyncPoint` matching the montage notify.
- [ ] Mount triggered with payload `TargetActor` = the mount pawn.
- [ ] Dismount triggered via `MountableComp->TriggerActionOnRider(DismountTag, ...)`.

**Common failures:**

| Symptom | Fix |
|---|---|
| Nothing happens on mount input | Mount ability tag doesn't match `MountActionTag`, or payload `TargetActor` not set to the mount |
| Rider warps to wrong spot | `MountPointSocket` missing on the mesh, or `WarpInfo.SyncPoint` doesn't match the montage notify |
| No camera blend / snap on mount | `MontageReproductionType` not `EMotionWarped`, or relying on direct attach instead of `StartMount` |
| Can't dismount | Dismount triggered on the rider directly — must use `TriggerActionOnRider` (controller possesses the mount) |
| Rider dismounts at wrong place | `DismountPointName`/`DefaultDismountPoint` not set, or no matching `UACFMountPointComponent` |
| Mounted attacks don't fire | Use `TriggerActionOnRider` (not the player's own input) while riding |
| AI mount aim is wrong | Tune `AACFRiderAIController` `OffsetRotCorrection` / `ClampMin` / `ClampMax`, enable `bOverrideControlWithMountRotation` |
| Mount can be ridden by two riders | Check `CanBeMounted()` before triggering; it returns false when a rider is assigned |
| Mount/dismount desyncs in MP | Use the server-authoritative `StartMount`/`StartDismount` paths (don't attach manually on clients) |
