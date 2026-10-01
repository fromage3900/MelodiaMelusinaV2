---
name: cheat-manager
description: Enable and use the ACF debug/cheat console commands (UACFCheatManager) for fast iteration — grant XP, currency, items, advance quests, and reveal map locations.
globs: []
alwaysApply: false
---

# Cheat Manager — ACF Ultimate

The **Ascent Cheat Manager** module provides `UACFCheatManager`, a `UCheatManager` subclass exposing ACF-specific **exec console commands** for fast testing: grant experience and currency, hand the player a pre-set bundle of items, start/advance quests, and reveal all map locations. `UCheatManager` only runs in non-shipping builds with cheats enabled, so these commands are a development tool — they never ship to players. You enable it by assigning it as the `CheatManagerClass` on your `APlayerController`, then run the commands from the in-game console (`~`).

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Cheat manager | `UACFCheatManager` | Assigned on your `APlayerController` | ACF debug exec commands |
| Items-to-add list | `TArray<FBaseItem>` | `EditDefaultsOnly` on the cheat manager | Bundle granted by `AddItemsToInventory` |
| Quests-to-start list | `TArray<FGameplayTag>` | `EditDefaultsOnly` on the cheat manager | Quests started by `StartQuests` |

> **Never edit the framework class directly.** If you need custom cheat content, create a **Blueprint subclass** of `UACFCheatManager` (or your own `UCheatManager`-derived class) under `Content/YourGame/Debug/` and fill `ItemsToAdd` / `QuestsToStart` there.

### Key class

| Class | Role |
|---|---|
| `UACFCheatManager` | `UCheatManager` subclass; holds the exec commands plus `ItemsToAdd` and `QuestsToStart` defaults |

---

## 2 — Setup / Configuration

### A. Assign the cheat manager

1. Open your **PlayerController** Blueprint (or C++ class).
2. Set **`Cheat Manager Class`** (`CheatManagerClass`) to `UACFCheatManager` — or to your Blueprint subclass of it.
3. Cheats only activate in builds where cheats are allowed (non-shipping / `-game` with cheats, or PIE). The console must be enabled.

### B. Configure the bundles (use a subclass)

1. Create a Blueprint subclass of `UACFCheatManager`, e.g. `BP_ACFCheatManager`, under `Content/YourGame/Debug/`.
2. In **Class Defaults**:
   - **`ItemsToAdd`** — array of `FBaseItem` granted by the `AddItemsToInventory` cheat.
   - **`QuestsToStart`** — array of quest `FGameplayTag`s started by the `StartQuests` cheat.
3. Assign **this subclass** as the controller's `CheatManagerClass`.

### C. Enable the console (if needed)

Make sure the console is bound. In `DefaultInput.ini` (or Project Settings → Input) ensure a `ConsoleKey` (e.g. `` ` ``/`~`) is set. Use `EnableCheats` if your build requires it.

---

## 3 — Core Workflow / Runtime API

Open the console with `` ~ `` and type a command. All commands are `UFUNCTION(exec, Category = ACF)`:

| Console command | Effect |
|---|---|
| `DiscoverAllLocations` | Reveals all discoverable world locations (map/fast-travel) |
| `AddExp <Exps>` | Grants `<Exps>` experience points to the player |
| `AddCurrency <Coins>` | Adds `<Coins>` currency to the player's inventory |
| `ProceedInTrackedQuest` | Advances the currently tracked quest by one step |
| `StartQuests` | Starts every quest listed in `QuestsToStart` |
| `AddItemsToInventory` | Adds every item in `ItemsToAdd` to the local player's inventory |

### Examples

```
AddExp 5000          // grant 5000 XP
AddCurrency 1000     // grant 1000 coins
AddItemsToInventory  // grant the configured FBaseItem bundle
StartQuests          // start all configured quests
ProceedInTrackedQuest
DiscoverAllLocations
```

### Calling from code/Blueprint

```
// Get the cheat manager from the player controller (dev only):
if (UACFCheatManager* Cheats = Cast<UACFCheatManager>(PlayerController->CheatManager))
{
    Cheats->AddExp(5000.f);
    Cheats->AddItemsToInventory();
}
```

### Extending with your own cheats

```
// In your BP/C++ subclass of UACFCheatManager:
UFUNCTION(exec, Category = ACF)
void GodModeMyGame();      // your custom exec command, callable from the console
```

---

## 4 — Wire to Characters / Blueprints

- The cheat manager acts on the **local player** behind the controller it's attached to, so assign it on the **player** controller used in PIE/dev builds.
- `AddExp` / `AddCurrency` / `AddItemsToInventory` route to the player's RPG/inventory components — make sure your player pawn actually has those ACF components, or the commands have nothing to act on.
- `StartQuests` / `ProceedInTrackedQuest` require the quest system to be present and a quest currently tracked (for `ProceedInTrackedQuest`).
- Keep the cheat manager out of shipping flows: rely on `UCheatManager`'s built-in shipping guard rather than gameplay code paths.

---

## 5 — Verify

**Checklist before testing:**

- [ ] `CheatManagerClass` is set to `UACFCheatManager` (or your subclass) on the active PlayerController.
- [ ] Running a non-shipping build / PIE with cheats enabled.
- [ ] Console key is bound and the console opens with `` ~ ``.
- [ ] For `AddItemsToInventory` / `StartQuests`: `ItemsToAdd` / `QuestsToStart` are filled on a **subclass**, not the framework class.
- [ ] Player pawn has the inventory / RPG / quest components the commands target.

**Common failures:**

| Symptom | Fix |
|---|---|
| Command not recognized in console | `CheatManagerClass` not assigned, or shipping build (cheats disabled) |
| `AddItemsToInventory` adds nothing | `ItemsToAdd` empty (you edited the base class, not your subclass) or no inventory component |
| `StartQuests` does nothing | `QuestsToStart` empty, or quest system not initialized |
| `ProceedInTrackedQuest` no effect | No quest is currently tracked |
| `AddExp` / `AddCurrency` ignored | Player pawn lacks the RPG/inventory components that store XP/currency |
| Console won't open | No `ConsoleKey` bound in input settings |
