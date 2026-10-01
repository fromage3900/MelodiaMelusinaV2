---
name: save-system
description: Add save/load persistence in ACF — the Ascent Load & Save subsystem, the savable component, the savable interface and project settings for save slots and serialization.
globs: []
alwaysApply: false
---

# Ascent Save System (ALS) — ACF Ultimate

The **AscentSaveSystem** module persists your game world. The entry point is `UALSLoadAndSaveSubsystem` (a `UGameInstanceSubsystem`) that serializes the whole world — actors, the local player, and metadata/screenshots — into named slots. Actors opt into persistence by adding a `UALSLoadAndSaveComponent` and/or implementing `IALSSavableInterface`, and any `UPROPERTY(SaveGame)` on those actors/components is serialized automatically. Project-wide behaviour (save-game class, slot count, default names, missing-actor policy) is configured in `UALSSaveGameSettings` (Project Settings → **Ascent Load & Save**). This skill covers making actors savable, saving/loading slots and wiring the flow.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Save game object | `UALSSaveGame` (or your BP subclass) | set in Project Settings | The serialized container written to a slot |
| Save settings | `UALSSaveGameSettings` | Project Settings → Ascent Load & Save | Global save config (class, slots, names, policies) |
| Savable actor | actor + `UALSLoadAndSaveComponent` | `/Game/FullSample/` actors | Marks an actor for save/load; auto-reload on start |
| Save metadata | `FALSSaveMetadata` | runtime | Slot info (name, description, timestamp, screenshot) |

> **Never edit sample assets.** If you need a custom save container, **duplicate**/subclass `UALSSaveGame` into `Content/YourGame/Save/` and assign your subclass in the settings — don't modify the sample/plugin default. Editing originals = lost on update.

### Key classes

| Class | Role |
|---|---|
| `UALSLoadAndSaveSubsystem` | The API: save/load world, player, single actors; slot & metadata management |
| `UALSLoadAndSaveComponent` | Per-actor opt-in; `bAutoReload`, `bDestroyIfMissingInSave`; `OnActorSaved`/`OnActorLoaded` |
| `IALSSavableInterface` | Actor hooks: `OnSaved`, `OnLoaded`, `ShouldBeIgnored`, `GetComponentsToSave` |
| `UALSSaveGame` | The save container object (subclass to add custom global data) |
| `UALSSaveGameSettings` | Developer settings (config = Plugins, DefaultConfig) |
| `UALSFunctionLibrary` | Serialize/deserialize helpers used by the subsystem |

### Important enums

- `ELoadingState`: `EIdle`, `ESaving`, `ELoading` (query current system state).
- `ELoadType`: `EDontReload` (and variants) — how player/actors are reloaded on load.
- Component callbacks resolved by name from settings: `OnComponentSaved` / `OnComponentLoaded`.

---

## 2 — Setup / Configuration

### A. Configure project settings (`Ascent Load & Save`)

In **Project Settings → Plugins → Ascent Load & Save** (`UALSSaveGameSettings`):
- `SaveGameClass` — your `UALSSaveGame` subclass (kept as a soft class ref so BP subclasses survive startup).
- `DefaultSaveName` (default `ACFSave`), `SavesMetadata` (default `SaveMetadata`), `TravelSlotName` (default `TempSave`).
- `MaxSlotsNum` (default 8) — number of allowed save slots.
- `bDestroyActorsMissingInSaveByDefault` — default policy for savable actors **without** a component that are missing from a loaded save (default `false` = forward-compatible; new level actors survive old saves).
- Screenshot: `SaveScreenWidth` / `SaveScreenHeight`.
- `OnComponentSavedFunctionName` / `OnComponentLoadedFunctionName` — function names invoked on savable actors during the save/load phases.

### B. Make an actor savable

1. Add a `UALSLoadAndSaveComponent` to the actor (sample persistent actors already have one).
2. Set per-actor options:
   - `bAutoReload` (default true) — restore this actor's saved state automatically when the game starts.
   - `bDestroyIfMissingInSave` (default false) — destroy this actor on load if the save has no record of it.
3. Mark the data you want persisted with `UPROPERTY(SaveGame)` on the actor/its components. (ACF stat/inventory/leveling fields are already `SaveGame`.)

### C. (Optional) Implement the savable interface

Implement `IALSSavableInterface` on the actor for fine control:
- `GetComponentsToSave()` — return the specific components to serialize.
- `ShouldBeIgnored()` — skip this actor entirely.
- `OnSaved()` / `OnLoaded()` — custom pre/post hooks (e.g. rebuild transient references).

---

## 3 — Core Workflow / Runtime API

Get the subsystem from the Game Instance, then call its functions.

### Saving

```
// Save the whole world to a named slot (with player + screenshot):
Subsystem->SaveGameWorld("Slot1", OnSaveFinished, /*bSaveLocalPlayer*/ true,
                         /*bSaveScreenshot*/ true, "Chapter 1 - Forest");

// Save into the currently active slot:
Subsystem->SaveGameWorldInCurrentSlot(OnSaveFinished, true, true, "Autosave");

// Save just one actor or just the local player:
Subsystem->SaveActor(SomeActor);
Subsystem->SaveLocalPlayer("Slot1");
```

### Loading

```
// Load a slot and open its saved map:
Subsystem->LoadGameWorld("Slot1", OnLoadFinished, /*reloadPlayer*/ true);

// Reload the current level from a slot:
Subsystem->LoadCurrentLevel("Slot1", OnLoadFinished, /*bReloadLocalPlayer*/ true);

// Load one actor / the local player:
Subsystem->LoadActor(SomeActor);
Subsystem->LoadLocalPlayer("Slot1", /*bReloadTransform*/ true);

// Global completion event:
Subsystem->OnLoadFinished.AddDynamic(this, &MyClass::HandleLoadFinished);
```

### Map travel (preserve the player across level changes)

```
Subsystem->TravelLocalPlayer();    // before opening the new map (writes TempSave)
// ... open level ...
Subsystem->LoadTraveledPlayer();   // after the new map is ready
```

### Slots & metadata (for a save/load menu)

```
TArray<FALSSaveMetadata> saves = Subsystem->GetAllSaveGames();
bool bAny      = Subsystem->HasAnySaveGame();
bool bCanAdd   = Subsystem->CanAddNewSlot();
bool bUnique   = Subsystem->IsSlotNameUnique("Slot2");
UTexture2D* shot = Subsystem->GetScreenshotForSave("Slot1");
FALSSaveMetadata meta;
Subsystem->TryGetSaveMetadata("Slot1", meta);
Subsystem->RemoveSlotInfo("Slot1");

ELoadingState state = Subsystem->GetSystemState();   // Idle / Saving / Loading
Subsystem->SetNewGame(true);                          // mark a fresh playthrough
```

### Per-actor events (`UALSLoadAndSaveComponent`)

```
Comp->SaveActor();   // save just this actor
Comp->LoadActor();   // load just this actor
Comp->OnActorSaved.AddDynamic(this, &MyClass::HandleSaved);
Comp->OnActorLoaded.AddDynamic(this, &MyClass::HandleLoaded);
```

---

## 4 — Wire to Characters / Blueprints

1. **Persistent actors**: add `UALSLoadAndSaveComponent` to anything whose state must survive (player, important NPCs, containers, doors, pickups). Mark mutable fields `UPROPERTY(SaveGame)`.
2. **Save/Load menu**: build the slot list from `GetAllSaveGames()`, show `FALSSaveMetadata` (name/description/timestamp) and the screenshot from `GetScreenshotForSave`. Use `CanAddNewSlot` / `IsSlotNameUnique` to gate new saves.
3. **Save trigger**: call `SaveGameWorld` (or `SaveGameWorldInCurrentSlot` for autosave) from a menu button, checkpoint volume, or on quit. Pass a callback to update UI on completion.
4. **Load trigger**: from the main menu call `LoadGameWorld(slot, cb)`. Bind `OnLoadFinished` to dismiss the loading screen.
5. **New game**: call `SetNewGame(true)` to start playtime tracking and skip auto-reload of stale state.
6. **Level streaming / travel**: wrap level transitions with `TravelLocalPlayer()` → open map → `LoadTraveledPlayer()` so the player keeps inventory/stats.
7. **ACF integration**: ARS stats/level/XP, inventory items, AI agent info and crafting runtime recipes are already `SaveGame`-tagged, so they persist automatically once their owning actor is savable. Use `OnComponentLoaded` hooks (e.g. `UACFAIPatrolComponent::OnComponentLoaded`) for components that must restore runtime state after deserialization.

---

## 5 — Verify

**Checklist before testing:**

- [ ] `SaveGameClass` is set in **Ascent Load & Save** settings (default `UALSSaveGame` or your duplicated subclass).
- [ ] `MaxSlotsNum` and default/travel slot names are configured.
- [ ] Every persistent actor has a `UALSLoadAndSaveComponent` (or implements `IALSSavableInterface`).
- [ ] Data to persist is marked `UPROPERTY(SaveGame)`.
- [ ] `bAutoReload` / `bDestroyIfMissingInSave` set appropriately per actor.
- [ ] Save/Load called through the `UALSLoadAndSaveSubsystem` (from the Game Instance), not ad-hoc.
- [ ] UI bound to `OnLoadFinished` and reads `GetSystemState()` to avoid overlapping save/load.

**Common failures:**

| Symptom | Fix |
|---|---|
| Actor state not restored | Missing `UALSLoadAndSaveComponent`, or fields not marked `UPROPERTY(SaveGame)` |
| Actor disappears after load | `bDestroyIfMissingInSave = true` (or the global default) and the actor isn't in that save |
| Saves don't appear in the menu | Reading the wrong API — use `GetAllSaveGames()` / `TryGetSaveMetadata`; check `SavesMetadata` name |
| Player resets on level change | Missing `TravelLocalPlayer()` before travel or `LoadTraveledPlayer()` after |
| No screenshot in slot | `bSaveScreenshot = false`, or screenshot width/height set to 0 in settings |
| Custom global data not saved | Subclass `UALSSaveGame`, add your fields, and assign the subclass as `SaveGameClass` |
| Save/load seems to do nothing | Another op in progress — check `GetSystemState()` is `EIdle` before starting |
| BP `UALSSaveGame` subclass resets to default | Use the soft-class `SaveGameClass` setting (it's designed to survive startup) — don't hardcode the native class |
