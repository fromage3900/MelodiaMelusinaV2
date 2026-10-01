---
name: morality-system
description: Track karma and moral alignments per player using GameplayTag-based morality points with the ACF Morality System module.
globs: []
alwaysApply: false
---

# Morality System — ACF Ultimate

The **Morality System** tracks a player's karma across any number of moral **alignments** (e.g. `Morality.Good`, `Morality.Evil`, `Morality.Lawful`). Each alignment is a `FGameplayTag` with an associated float score. `UACFMoralityComponent` lives on the **Player Controller**, stores a replicated, save-game array of `FMoralityPoint` entries, and exposes a simple API to add points, query a score, and resolve the dominant alignment. Gameplay code (quests, dialogue choices, kills, thefts) calls `AddMoralityPoint` to shift the player's karma.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Morality component | `UACFMoralityComponent` | Added on your Player Controller Blueprint | Stores & replicates morality points per alignment |
| Alignment tags | `FGameplayTag` (`Morality.*`) | Project Settings → GameplayTags | Identify each moral stance |

> **Never edit sample assets.** Duplicate any sample Player Controller / tag config into `Content/YourGame/...` and customize your copy.

### Key types

| Type | Role |
|---|---|
| `UACFMoralityComponent` | `UActorComponent` on the Player Controller; replicated, save-game enabled |
| `FMoralityPoint` | Struct pairing an `Alignment` (`FGameplayTag`) with a `Points` (float) value |
| `FOnMoralityChanged` | Multicast delegate broadcast whenever points change (UI hook) |

---

## 2 — Setup / Configuration

1. Create your **Gameplay Tags** for alignments under a `Morality.*` root in **Project Settings → Project → GameplayTags** (e.g. `Morality.Good`, `Morality.Evil`, `Morality.Renegade`, `Morality.Paragon`).
2. Open your **Player Controller** Blueprint (duplicate the sample one into `Content/YourGame/` first if you are customizing it).
3. **Add Component → ACF Morality Component**. The component is `meta=(BlueprintSpawnableComponent)`, so it appears in the add-component list.
4. No further configuration is required on the component itself — points are created on demand the first time you add to an alignment.
5. Because the component is replicated and marked `SaveGame`, morality survives save/load and stays consistent on clients automatically.

> The component **must be attached to the Player Controller** (its API uses `Server, Reliable` RPCs and the controller is the natural per-player owner).

---

## 3 — Core Workflow / Runtime API

Get the component from the player controller, then call the API. All mutating calls are server functions — call them on the authority (or from a client; they route to the server via RPC).

| Function | Signature | Notes |
|---|---|---|
| `AddMoralityPoint` | `(FGameplayTag Alignment, float Points)` | Server RPC. Adds (or subtracts, if negative) points to an alignment; creates the entry if missing |
| `GetMoralityPoints` | `(FGameplayTag Alignment) → float` | Returns current score for one alignment (0 if none) |
| `GetMoralityAlignment` | `() → FGameplayTag` | BlueprintPure; returns the alignment with the **highest** points (dominant stance) |
| `ResetMorality` | `()` | Server RPC. Clears all morality points |

### Blueprint example — reward / punish a choice

```
// Player spares an enemy → +10 Good
PlayerController
  → Get Component By Class (ACF Morality Component)
  → Add Morality Point (Alignment = Morality.Good, Points = 10.0)

// Player steals from a vendor → +5 Evil
  → Add Morality Point (Alignment = Morality.Evil, Points = 5.0)

// Apply a penalty → negative points
  → Add Morality Point (Alignment = Morality.Good, Points = -3.0)
```

### Reading the dominant alignment (gating content)

```
FGameplayTag current = MoralityComp->GetMoralityAlignment();
if (current == FGameplayTag::RequestGameplayTag("Morality.Evil"))
{
    // unlock the "dark" dialogue branch / ending
}
```

### Reacting to changes

Bind to `OnMoralityChanged` (no params) to refresh karma UI, alignment meters, or reputation widgets whenever any score changes.

```
MoralityComp->OnMoralityChanged.AddDynamic(this, &AMyHUD::RefreshKarmaBar);
```

---

## 4 — Wire to Characters / Blueprints

- **Quests / Dialogue:** in a dialogue choice or quest-completion node, get the player's controller → `Get Component By Class (ACF Morality Component)` → `Add Morality Point`. Map each meaningful choice to an alignment tag and a points delta.
- **Combat events:** on a kill / non-lethal takedown, route through the killer's controller and call `AddMoralityPoint` with the appropriate tag.
- **Gating:** in dialogue conditions, vendor access, or ending selectors, call `GetMoralityAlignment` / `GetMoralityPoints` to branch.
- **UI:** create a karma widget that binds to `OnMoralityChanged` and reads `GetMoralityPoints` per alignment to drive meters.
- **Persistence:** the points array is `SaveGame`-tagged, so it is captured automatically by the ACF Save System component on the same controller — no extra wiring needed.

---

## 5 — Verify

**Checklist before testing:**

- [ ] Alignment Gameplay Tags created under `Morality.*` in Project Settings.
- [ ] `UACFMoralityComponent` added to the **Player Controller** (not the pawn).
- [ ] Gameplay code calls `AddMoralityPoint` with a **valid** tag (invalid tags are ignored).
- [ ] UI binds to `OnMoralityChanged` for live updates.
- [ ] If persistence is wanted, a Save System component is present on the controller.

**Common failures:**

| Symptom | Fix |
|---|---|
| Points never change | Tag passed to `AddMoralityPoint` is invalid/empty — `AddMoralityPoint` ignores invalid tags |
| Points reset on client / desync | Component not replicated or placed on pawn instead of controller; keep it on the Player Controller |
| `GetMoralityAlignment` returns empty | No points have ever been added; array is empty |
| Karma UI doesn't update | Not bound to `OnMoralityChanged`, or rebuilt widget lost its binding |
| Morality lost on save/load | Save System component missing on the controller, or save data not flushing the `SaveGame` array |
| Calling from client does nothing visible | Mutators are `Server, Reliable`; ensure the controller actually owns the connection |
