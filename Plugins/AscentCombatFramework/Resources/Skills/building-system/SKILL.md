---
name: building-system
description: Add base building / construction with recipes, placement preview, validity checks, modular snapping, inventory cost and dismantling using the ACF AscentBuildingSystem module.
globs: []
alwaysApply: false
---

# Building System — ACF Ultimate

The **AscentBuildingSystem** module provides survival-style base building: a player-owned `UACFBuildingManagerComponent` drives a build/dismantle mode, shows a ghost preview that follows the camera, validates placement (slope, overlap, snapping), consumes inventory items, and spawns the real structure on the server. Each placeable structure is described by a `UACFBuildRecipe` DataAsset (actor class + required/returned items + UI data) and built from any actor implementing `IACFBuildableInterface` — usually `AACFBaseBuildable`, which bundles a `UACFBuildableEntityComponent` (placement validity + dismantle) and a `UACFBuildingSnapComponent` (modular snapping). The whole flow is networked (server-authoritative spawn, replicated recipe list and build mode).

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Build recipe | `UACFBuildRecipe` | `/AscentCombatFramework/Building/Recipes/` | Defines a buildable: `ItemType`, `RequiredItems`, `ReturnedItems`, name/icon |
| Base buildable | `AACFBaseBuildable` | `/AscentCombatFramework/Building/` | Ready-made buildable actor (mesh + entity + snap + interactable) |
| Building manager | `UACFBuildingManagerComponent` | on player pawn/controller | Build/dismantle mode, preview, placement, recipe list |
| Buildable entity | `UACFBuildableEntityComponent` | on each buildable | Placement validity, dismantle, builder info |
| Snap component | `UACFBuildingSnapComponent` | on each buildable | Finds & snaps to nearby snap points |
| Snap point | `UACFBuildingSnapPointComponent` | child of buildable | Marks a modular snap location |
| Buildable interface | `IACFBuildableInterface` | implemented by buildables | `OnPlaced`, `OnDismantled`, `IsPlacementValid` |

> **Never edit sample assets.** Duplicate sample recipes and buildable BPs into `Content/YourGame/Building/` and customize **your copies**.

### Key members

| Class | Notable members |
|---|---|
| `UACFBuildingManagerComponent` | `StartBuild(Recipe)`, `Build()`, `EndBuildMode()`, `StartDismantling()`, `Dismantle(actor)`, `RotateBuildingBy/ByStep()`, `GetRecipes()`, `AddRecipe()`, `GetBuildingMode()`, `OnBuildingModeChanged` |
| `UACFBuildRecipe` | `BuildingName`, `BuildingIcon`, `Description`, `ItemType` (`MustImplement IACFBuildableInterface`), `RequiredItems[]`, `ReturnedItems[]` |
| `UACFBuildableEntityComponent` | `IsPlacementValid()`, `Build()`, `Dismantle()`, `CanBeDismantled()`, `MaxAllowedSlope`, `BlockingChannels`, `OnBuilt`, `OnDismantled` |
| `UACFBuildingSnapComponent` | `FindNearestSnapTarget()`, `TrySnap()`, `SnapToTarget()`, `GetWorldSnapPoints()`, `SnapDistance` |
| `AACFBaseBuildable` | `Dismantle(Pawn)`, interactable + savable interfaces, `BuildableComp`, `SnapComponent` |

`EBuildingMode`: `ENone` / `EBuilding` / `EDismantling`.

---

## 2 — Setup / Configuration

### A. Create a buildable actor

1. Duplicate the sample `AACFBaseBuildable` BP into `Content/YourGame/Building/` (or create a Blueprint implementing `IACFBuildableInterface`).
2. Set its `MeshComponent` to your structure mesh.
3. Configure the `UACFBuildableEntityComponent`:
   - `MaxAllowedSlope` — reject placement on steep ground.
   - `BlockingChannels` — collision channels that invalidate placement on overlap.
   - `ShapeCollisionMargin` — overlap box padding.
4. For modular pieces (walls/floors/foundations), add `UACFBuildingSnapPointComponent`s at the connection points and a `UACFBuildingSnapComponent` (already present on `AACFBaseBuildable`); tune `SnapDistance` / `bSnapVertically`.

### B. Create a build recipe

1. Right-click → **Data Asset** → `UACFBuildRecipe`, save under `Content/YourGame/Building/Recipes/`.
2. Set:
   - `ItemType` → your buildable actor class (must implement `IACFBuildableInterface`).
   - `RequiredItems` → `FBaseItem` array consumed from inventory on build.
   - `ReturnedItems` → items refunded on dismantle.
   - `BuildingName`, `Description`, `BuildingIcon` for the build menu UI.

### C. Add the building manager to the player

1. Add a `UACFBuildingManagerComponent` to the player pawn (or controller). It needs access to a `UACFInventoryComponent` (`GetInventoryComponent()`) and the owning `APlayerController`.
2. Populate its `Recipes` list, or call `AddRecipe()` at runtime (e.g. as the player unlocks blueprints). The recipe list is replicated/saved.
3. Assign `ValidMaterial` / `InvalidMaterial` (ghost preview feedback), `DefaultRotationStep`, and a `BuildInputMappingContext` (auto-activated while building) with priority.

---

## 3 — Core Workflow / Runtime API

### Build loop

```
UACFBuildingManagerComponent* Builder = Pawn->FindComponentByClass<UACFBuildingManagerComponent>();

// 1) Enter build mode with a recipe -> spawns the ghost preview that follows the camera:
Builder->StartBuild(MyRecipe);

// 2) (optional) rotate the preview:
Builder->RotateBuildingByStep();              // by DefaultRotationStep
Builder->RotateBuildingBy(FRotator(0,15,0));  // custom

// 3) Confirm -> validates, consumes RequiredItems, server-spawns the real actor:
Builder->Build();

// 4) Leave build mode:
Builder->EndBuildMode();
```

The manager ticks the preview, snaps it via the buildable's `UACFBuildingSnapComponent`, and recolors it with `ValidMaterial` / `InvalidMaterial` based on `IsBuildablePlaceable()`. `Build()` only succeeds when placement is valid and inventory can pay `RequiredItems`.

### Dismantle loop

```
Builder->StartDismantling();          // enter dismantle mode
Builder->Dismantle(TargetBuildable);  // server removes it, refunds ReturnedItems
// or, directly on the buildable:
BaseBuildable->Dismantle(Pawn);
```

### Validity & networking

- Placement validity lives in `UACFBuildableEntityComponent::IsPlacementValid()` (slope ≤ `MaxAllowedSlope`, no overlap on `BlockingChannels`). Override the `BlueprintNativeEvent` for custom rules.
- Spawning is server-authoritative: `Build()` → `ServerBuild(Id, Location, Rotation)` → async-loads the class → spawns. The recipe list (`RecipesIds`) and `BuildingMode` are replicated.

### Events

| Delegate | Where | Fires when |
|---|---|---|
| `OnBuildingModeChanged(EBuildingMode)` | manager | Build/dismantle mode toggles (drive UI/input) |
| `OnBuilt(APlayerState* Builder)` | entity | Structure finished building |
| `OnDismantled(Instigator, Builder)` | entity | Structure dismantled |

---

## 4 — Wire to Characters / Blueprints

1. Add `UACFBuildingManagerComponent` to the player and make sure the player has a `UACFInventoryComponent` (required items are paid from it).
2. Bind player input to the build loop: open the build menu → `StartBuild(SelectedRecipe)`; rotate keys → `RotateBuildingByStep()`; confirm → `Build()`; cancel → `EndBuildMode()`; dismantle toggle → `StartDismantling()`.
3. Drive the build menu UI from `GetRecipes()` (icon/name/description) and the cost from each recipe's `RequiredItems`.
4. Show/hide your build HUD by listening to `OnBuildingModeChanged`.
5. For modular sets, give matching `UACFBuildingSnapPointComponent`s on walls/floors/foundations so `TrySnap()` aligns them.

---

## 5 — Verify

**Checklist before testing:**

- [ ] Buildable actors duplicated into `Content/YourGame/Building/` and implement `IACFBuildableInterface`.
- [ ] Each `UACFBuildRecipe` has `ItemType`, `RequiredItems`, `ReturnedItems`, name/icon.
- [ ] Player has both `UACFBuildingManagerComponent` and `UACFInventoryComponent`.
- [ ] Manager `Recipes` populated (or added via `AddRecipe`).
- [ ] `ValidMaterial` / `InvalidMaterial` assigned for preview feedback.
- [ ] `BuildInputMappingContext` set and input bound to the build loop.
- [ ] Snap points placed on modular pieces (if using snapping).
- [ ] `MaxAllowedSlope` / `BlockingChannels` tuned on the buildable entity.

**Common failures:**

| Symptom | Fix |
|---|---|
| `StartBuild` shows no preview | Recipe `ItemType` unset, or class doesn't implement `IACFBuildableInterface` |
| Preview always red / `Build()` fails | Placement invalid: slope > `MaxAllowedSlope`, overlapping a `BlockingChannels` object, or no inventory items |
| Build consumes nothing / "not enough items" | `RequiredItems` mismatch with inventory item IDs, or no `UACFInventoryComponent` |
| Pieces don't snap together | Missing `UACFBuildingSnapPointComponent`s, or `SnapDistance` too small |
| Structure spawns on client then disappears | Don't spawn locally — use `Build()` which routes through server `ServerBuild` |
| Dismantle returns nothing | `ReturnedItems` empty, or `CanBeDismantled()` returns false |
| Recipes missing after rejoin/load | Recipe list is `SaveGame`/replicated — ensure the owner is saved and `AddRecipe` ran on the server |
| Build input still active after exiting | Listen to `OnBuildingModeChanged` and remove the mapping context on `ENone` |
