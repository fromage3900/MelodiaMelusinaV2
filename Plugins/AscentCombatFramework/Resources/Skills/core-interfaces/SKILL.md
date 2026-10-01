---
name: core-interfaces
description: Reference for the shared ACF core interfaces (entity/team and interactable) — when and how to implement IACFEntityInterface and IACFInteractableInterface on your actors.
globs: []
alwaysApply: false
---

# Core Interfaces — ACF Ultimate

**Ascent Core Interfaces** is the low-level contract layer shared across the whole framework. It defines the small set of `UINTERFACE`s that other ACF systems (combat, AI, interaction, targeting, warp) query so they don't need to know your concrete classes. Implement these interfaces on your actors to opt them into ACF behaviour. The two runtime interfaces are **`IACFEntityInterface`** (anything that has a combat team / can be alive — characters, destructibles, turrets) and **`IACFInteractableInterface`** (anything a pawn can interact with — NPCs, doors, pickups, levers). The module also defines shared core types (`EACFDirection`, `FACFStruct`).

---

## 1 — Understand the assets

This is a **C++ interface reference**, not a content-asset system — there are no DataAssets to duplicate. You implement these interfaces on **your own** Blueprints/C++ classes.

| Interface | Class | Header | Implement on |
|---|---|---|---|
| Entity / team | `IACFEntityInterface` (`UACFEntityInterface`) | `Interfaces/ACFEntityInterface.h` | Any actor with a combat team / aliveness (characters, enemies, destructibles) |
| Interactable | `IACFInteractableInterface` (`UACFInteractableInterface`) | `Interfaces/ACFInteractableInterface.h` | Any actor a pawn can interact with (NPCs, doors, pickups) |
| Core types | `UACFCoreTypes`, `EACFDirection`, `FACFStruct` | `ACFCoreTypes.h` | Shared enums/structs (hit directions, tag wrapper) |

> **Never edit the framework interface headers.** Implement the interfaces on **your** classes (`Content/YourGame/...` Blueprints, or your C++ actors) and override the `_Implementation` functions.

> `AACFCharacter` and the standard ACF actors already implement these interfaces. You only implement them yourself on **custom** actors that aren't ACF base classes.

---

## 2 — Setup / Configuration

### `IACFEntityInterface` — methods

All are `BlueprintNativeEvent` + `BlueprintCallable` (implement in Blueprint or C++):

| Method | Returns | Purpose |
|---|---|---|
| `GetEntityCombatTeam()` | `FGameplayTag` | The combat team this entity belongs to (drives friend/foe) |
| `GetEntityExtentRadius()` | `float` | Bounding radius covering the mesh — used for warp + distance checks |
| `IsEntityAlive()` | `bool` | Whether the entity is currently alive/valid as a target |
| `AssignTeamToEntity(FGameplayTag)` | `void` | Sets/reassigns the entity's combat team |

### `IACFInteractableInterface` — methods

| Method | Returns | Purpose |
|---|---|---|
| `OnInteractedByPawn(APawn*, FString interactionType)` | `void` | Replicated interaction performed by a pawn |
| `OnLocalInteractedByPawn(APawn*, FString interactionType)` | `void` | Local (non-replicated) interaction |
| `OnInteractableRegisteredByPawn(APawn*)` | `void` | Entered a pawn's detection area (show prompt) |
| `OnInteractableUnregisteredByPawn(APawn*)` | `void` | Left the detection area (hide prompt) |
| `GetInteractableName()` | `FText` | Display name for interaction prompts/UI |
| `CanBeInteracted(APawn*)` | `bool` | Gate availability (defaults to `true`) |

---

## 3 — Core Workflow / Runtime API

### Implementing in C++

```
// MyTurret.h
class AMyTurret : public AActor, public IACFEntityInterface
{
    GENERATED_BODY()
public:
    virtual FGameplayTag GetEntityCombatTeam_Implementation() const override;
    virtual float        GetEntityExtentRadius_Implementation() const override;
    virtual bool         IsEntityAlive_Implementation() const override;
    virtual void         AssignTeamToEntity_Implementation(FGameplayTag InTeam) override;
};
```

### Implementing in Blueprint

1. Open your Actor Blueprint → **Class Settings → Interfaces → Add** → choose `ACF Entity Interface` and/or `ACF Interactable Interface`.
2. Implement each event in the Event Graph (e.g. `Get Entity Combat Team`, `Can Be Interacted`, `On Interacted By Pawn`).

### Calling interfaces safely

```
// Always check before calling (the actor may not implement it):
if (Actor->Implements<UACFEntityInterface>())
{
    FGameplayTag Team = IACFEntityInterface::Execute_GetEntityCombatTeam(Actor);
    bool bAlive       = IACFEntityInterface::Execute_IsEntityAlive(Actor);
}

if (Target->Implements<UACFInteractableInterface>())
{
    if (IACFInteractableInterface::Execute_CanBeInteracted(Target, MyPawn))
    {
        IACFInteractableInterface::Execute_OnInteractedByPawn(Target, MyPawn, TEXT("Talk"));
    }
}
```
In Blueprint, use the **message** call nodes (e.g. `Get Entity Combat Team (Message)`) — they safely no-op if the interface isn't implemented.

### Shared core types

```
EACFDirection Dir = EACFDirection::FrontLeft;   // hit/reaction direction (8-way)
// FACFStruct wraps a FGameplayTag with == / != operators for tag-keyed containers.
```

---

## 4 — Wire to Characters / Blueprints

- **When to implement `IACFEntityInterface`:** any actor that combat/AI/targeting must treat as a combatant — custom enemies not derived from `AACFCharacter`, destructible objects, shootable props, turrets. Targeting and warp use `GetEntityExtentRadius`; team systems use `GetEntityCombatTeam` / `AssignTeamToEntity`; damage/aliveness checks use `IsEntityAlive`.
- **When to implement `IACFInteractableInterface`:** any actor the player/NPC can interact with that isn't already an ACF interactable — custom doors, levers, readables, quest objects. The interaction component on pawns calls `OnInteractableRegisteredByPawn` / `Unregistered` to drive prompts and `CanBeInteracted` to filter what's selectable.
- Prefer composition: implement only the interface(s) the actor needs. A pickup might implement only `IACFInteractableInterface`; a destructible barrel might implement only `IACFEntityInterface`; an interactable NPC implements both.

---

## 5 — Verify

**Checklist before testing:**

- [ ] Interface added under **Class Settings → Interfaces** (Blueprint) or in the class declaration (C++).
- [ ] Every method has an implementation (BlueprintNativeEvent events / `_Implementation` overrides).
- [ ] `GetEntityCombatTeam` returns a valid team `FGameplayTag` (not empty).
- [ ] `GetEntityExtentRadius` returns a sensible radius covering the mesh (warp/targeting depend on it).
- [ ] Callers use `Implements<>()` / message nodes rather than hard casts.
- [ ] Interactables return a meaningful `GetInteractableName` and correct `CanBeInteracted`.

**Common failures:**

| Symptom | Fix |
|---|---|
| Actor ignored by targeting/AI | Doesn't implement `IACFEntityInterface`, or `IsEntityAlive` returns false |
| Friend/foe logic wrong | `GetEntityCombatTeam` returns empty/wrong tag; call `AssignTeamToEntity` on spawn |
| Warp/attacks miss the target | `GetEntityExtentRadius` returns 0 or too small |
| Interaction prompt never shows | `IACFInteractableInterface` not implemented, or `CanBeInteracted` returns false |
| Interaction does nothing on multiplayer | Logic placed in `OnLocalInteractedByPawn` instead of replicated `OnInteractedByPawn` |
| Interface call crashes / no-ops | Calling concrete function instead of `Execute_*` / message node without `Implements<>()` check |
