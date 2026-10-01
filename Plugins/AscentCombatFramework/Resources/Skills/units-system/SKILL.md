---
name: units-system
description: Manage a roster of AI units, deploy them into group-AI squads, and run territory conquest (assault points) using the ACF UnitsSystem module.
globs: []
alwaysApply: false
---

# Units System — ACF Ultimate

The **UnitsSystem** module manages a persistent roster of AI **units** and lets you push/pull them into live `UACFGroupAIComponent` squads, plus a **conquest** layer for capturing territory via assault points. A `UACFUnitsComponent` stores an array of `FBaseUnit` (a soft AI class + `UACFCharacterDataAsset` config + level) and can move units in and out of group AI at runtime. The conquest side uses `AACFAssaultPoint` actors (state machine: not conquered → in progress → conquered), a per-player `UACFConqueringComponent` that tracks capture state by tag, and `UACFConqueringElementComponent` for world elements that react to capture state.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Units roster component | `UACFUnitsComponent` | on commander pawn/PlayerState/GameState | Holds `TArray<FBaseUnit>`; add/remove/move units |
| Unit entry | `FBaseUnit` (struct) | data | `AIClassBP` (soft `AACFCharacter`), `AIConfig` (`UACFCharacterDataAsset`), `AILevel` |
| Assault point | `AACFAssaultPoint` | placed in level | Capturable point with `AssaultPointTag` + conquer state machine |
| Conquering component | `UACFConqueringComponent` | on player controller | Per-player capture state keyed by point tag |
| Conquest element | `UACFConqueringElementComponent` | on world actors | Show/hide or react based on a point's `EConqueredState` |
| Conquest helpers | `UACFConquestFunctionLibrary` | static BP library | `GetLocalConqueringComponent`, `GetAssaultPoint` |

> **Never edit sample assets.** Duplicate the sample unit `UACFCharacterDataAsset`s / character BPs into `Content/YourGame/Units/` and reference **your copies** in `FBaseUnit` entries.

### `FBaseUnit` fields

| Field | Type | Meaning |
|---|---|---|
| `AIClassBP` | `TSoftClassPtr<AACFCharacter>` | The character class to spawn for this unit |
| `AIConfig` | `TSoftObjectPtr<UACFCharacterDataAsset>` | Stats/equipment config for the unit |
| `AILevel` | `int32` | Spawn level (drives scaling) |

`FBaseUnit` is `SaveGame`-tagged and `Units` is replicated, so the roster persists and syncs.

### Conquer state (`EConqueredState`)

`ENotConquered` → `EConquerInProgress` → `EConquered`.

---

## 2 — Setup / Configuration

### A. Units roster

1. Add a `UACFUnitsComponent` to the actor that owns the army — typically a commander pawn, PlayerState, or GameState.
2. Populate the `Units` array (in defaults or at runtime) with `FBaseUnit` entries pointing at **your** duplicated character classes / `UACFCharacterDataAsset`s and the desired `AILevel`.

### B. Conquest (assault points)

1. Place `AACFAssaultPoint` actors in the level where territory can be captured.
2. Give each a unique `AssaultPointTag` (e.g. `Conquest.Point.North`).
3. Ensure each player controller that can capture has a `UACFConqueringComponent` (it tracks capture state for that player).
4. On world props that should react to capture (banners, gates, spawners), add `UACFConqueringElementComponent`, set its `AssaultPointTag`, and optionally `bShowOnlyInDisplayState` + `DisplayInState` to show only in a specific `EConqueredState`.

---

## 3 — Core Workflow / Runtime API

### Managing the roster

```
// Add / remove a unit:
UnitsComp->AddUnit(FBaseUnit(MyCharacterClass));
UnitsComp->RemoveUnit(SomeUnit);

// Read the roster:
TArray<FBaseUnit> roster = UnitsComp->GetUnits();

// Deploy a unit into a live squad (UACFGroupAIComponent), or pull it back:
UnitsComp->MoveUnitToGroup(SomeUnit, GroupAIComp);
UnitsComp->MoveUnitFromGroup(SomeUnit, GroupAIComp);
```

Bind to roster events for UI:

| Delegate | Fires when |
|---|---|
| `OnUnitsChanged(const TArray<FBaseUnit>&)` | Whole roster changes (replication) |
| `OnUnitAdded(const FBaseUnit&)` | A unit is added |
| `OnUnitRemoved(const FBaseUnit&)` | A unit is removed |

> Commanding *behavior* (move/attack orders, formations) is handled by the **AI Framework**'s `UACFGroupAIComponent`. The Units System feeds units into those groups — use the AI Framework skill for squad orders.

### Running conquest

```
// Start / complete / interrupt capture of a point (server-authoritative):
AssaultPoint->StartConquering(PlayerController);
AssaultPoint->CompleteConquering(PlayerController);
AssaultPoint->InterruptConquering(PlayerController);

// Query state:
EConqueredState state = AssaultPoint->GetConqueringState();
bool canStart = AssaultPoint->CanStartConquering();   // true only when ENotConquered

// Per-player tracking:
UACFConqueringComponent* conq = UACFConquestFunctionLibrary::GetLocalConqueringComponent(WorldContext);
EConqueredState s = conq->GetConqueringStateForPoint(PointTag);
bool busy = conq->IsAnyConquerInProgress();

// Resolve a point by tag:
AACFAssaultPoint* pt = UACFConquestFunctionLibrary::GetAssaultPoint(WorldContext, PointTag);
```

React to capture changes:

| Hook | Where |
|---|---|
| `OnConquestStarted` / `OnConquestCompleted` / `OnConquestInterrupted` | `BlueprintNativeEvent` on `AACFAssaultPoint` — override for FX, spawns |
| `OnConquerStateChanged(EConqueredState)` | Delegate on `AACFAssaultPoint` and `UACFConqueringElementComponent` |
| `OnConquerStateChanged(tag, state)` | Delegate on `UACFConqueringComponent` |

`AACFAssaultPoint` and the unit roster are `SaveGame`/replicated, so conquest progress persists and syncs in multiplayer. The assault point also extends the wave master (`ACFAIWaveMaster`), so a point can drive defender waves.

---

## 4 — Wire to Characters / Blueprints

1. Put the `UACFUnitsComponent` on the actor that represents the player's army (commander pawn / PlayerState / GameState) and fill the roster from your saved data or a config.
2. To field the army, spawn / feed units into one or more `UACFGroupAIComponent` squads with `MoveUnitToGroup`, then issue orders through the AI Framework.
3. For conquest: place `AACFAssaultPoint`s, tag them, and trigger `StartConquering` when a capturing pawn enters the point's volume (e.g. from an overlap on the point's collision).
4. Drive capture UI/FX from the assault point and `UACFConqueringElementComponent` delegates rather than polling.

---

## 5 — Verify

**Checklist before testing:**

- [ ] `UACFUnitsComponent` added to the commander/army owner.
- [ ] `FBaseUnit` entries reference **your** duplicated character classes + `UACFCharacterDataAsset` and valid `AILevel`.
- [ ] Target squads have a `UACFGroupAIComponent` (AI Framework) before calling `MoveUnitToGroup`.
- [ ] `AACFAssaultPoint`s placed with unique `AssaultPointTag`s.
- [ ] Capturing player controllers have a `UACFConqueringComponent`.
- [ ] World reaction props have `UACFConqueringElementComponent` with matching tags.
- [ ] Conquest calls run on the **server** (StartConquering/CompleteConquering are server RPCs).

**Common failures:**

| Symptom | Fix |
|---|---|
| `MoveUnitToGroup` does nothing | Target group has no `UACFGroupAIComponent`, or the unit isn't in the roster |
| Units don't persist across save/load | Owner isn't actually saved; `Units` is `SaveGame` but the component must be on a saved actor |
| Roster doesn't update on clients | Read it via `OnUnitsChanged`/`OnRepUnits`; don't cache the array locally |
| Capture never starts | `CanStartConquering()` false — point isn't `ENotConquered`, or call made on a client instead of server |
| Element doesn't show/hide on capture | `AssaultPointTag` mismatch, or `DisplayInState` doesn't match current `EConqueredState` |
| `GetAssaultPoint` returns null | No assault point in the level with that tag |
| Spawned units have wrong stats | `AIConfig` points at a sample asset or wrong `UACFCharacterDataAsset` |
