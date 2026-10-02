---
name: quest-system
description: Create quest graph assets, objectives, quest target actors, and wire the AQSQuestManagerComponent to track and complete quests.
globs: []
alwaysApply: false
---

# Quest System — ACF Ultimate (AscentQuestSystem)

The **AscentQuestSystem (AQS)** module provides a graph-based quest framework. Each quest is a `UAQSQuest` asset (a directed graph) containing start, objective, and end nodes. `UAQSQuestManagerComponent` on the PlayerController tracks active, completed, and failed quests, drives objective state, and replicates everything to clients. World actors that are quest targets carry `UAQSQuestTargetComponent`. Quests are stored in a `UDataTable` (the Quest Database) and referenced by `FGameplayTag`.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Sample quest graph | `UAQSQuest` | `/Game/FullSample/Integrations/Ultimate/Quests/` | Graph asset defining quest flow and objectives |
| Quest DataTable | `UDataTable` (row: `FAQSQuestData`) | `/Game/FullSample/Integrations/Ultimate/Quests/` | Database of all quest assets keyed by tag |
| Sample objective | `UAQSQuestObjective` | Graph node inner object | Objective data: name, description, tag, targets |
| Sample quest target actor | any actor + `UAQSQuestTargetComponent` | Sample level | World actor that is an objective target |

> **Never edit sample assets.** Duplicate the quest graph and DataTable into `Content/YourGame/Quests/` and customize your copies.

### Key classes

| Class | Role |
|---|---|
| `UAQSQuest` | Graph DataAsset: `QuestTag`, `QuestName`, objectives as nodes, `LayerToLoad` (World Partition) |
| `UAQSQuestManagerComponent` | On PlayerController; owns in-progress, completed, failed quest lists |
| `UAQSQuestObjective` | UObject inner class on an objective graph node; carries tag, description, targets, repetitions |
| `UAQSQuestTargetComponent` | ActorComponent added to any world actor that is a quest objective target |
| `UAQSQuestTrigger` | Volume/actor that auto-starts a quest on player overlap |
| `FAQSQuestRecord` | Lightweight replicated struct: quest tag + active objective IDs |

### Graph node types

| Node | Purpose |
|---|---|
| `UAQSStartQuestNode` | Entry point — first node activated when the quest starts |
| `UAQSObjectiveNode` | Represents one objective; holds a `UAQSQuestObjective` instance |
| `UAQSFinishQuestNode` | Routes to success or failure outcome |
| `UAQSQuestSuccededNode` | Terminal node — quest succeeded |
| `UAQSQuestFailedNode` | Terminal node — quest failed |
| `UAQSEdge` | Directed connection between nodes; can carry a transition filter `FName` for branching |

---

## 2 — Setup / Configuration

### A. Create a Quest graph asset

1. In the Content Browser, right-click → **AscentQuestSystem → Quest**.
2. Save under `Content/YourGame/Quests/`.
3. Open the quest editor (double-click). You will see a graph canvas.
4. Set in **Class Defaults** (details panel):
   - **`QuestTag`** — unique GameplayTag under `Quest.*` (e.g. `Quest.MainStory.Chapter1`).
   - **`QuestName`** and **`QuestDescription`** — displayed in UI.
   - **`QuestIcon`** — UI texture.
   - **`LayerToLoad`** *(optional)* — a World Partition Data Layer to load when this quest starts.

5. Build the graph:
   - Add a **StartQuestNode** → wire to the first **ObjectiveNode**.
   - Each **ObjectiveNode** holds a `UAQSQuestObjective`:
     - Set **`ObjectiveTag`** (child tag of the quest tag, e.g. `Quest.MainStory.Chapter1.TalkToNPC`).
     - Set **`ObjectiveName`** and **`ObjectiveDescription`**.
     - Set **`TargetRefType`**: `ETag` (by GameplayTag on target components) or `ESoftRef` (direct actor soft references).
     - Add **`ReferencedTargets`** (tags) or **`ReferencedActors`** (soft refs).
     - Set **`Repetitions`** if the player must repeat the action multiple times (e.g. kill 5 enemies).
   - Wire objectives in sequence (or parallel — multiple active nodes at once).
   - For branching, add multiple outgoing edges from an objective node; give each edge a unique `TransitionFilter` name. Call `CompleteBranchedObjective(ID, FilterNames)` at runtime to unlock only specific paths.
   - Add a **FinishQuestNode**, then wire to **QuestSucceededNode** or **QuestFailedNode**.

### B. Register quests in the DataTable

1. Duplicate (or open your copy of) the Quest DataTable asset.
2. Add a new row for each quest:
   - **Row Name** — any unique name.
   - **`QuestTag`** — the same tag set on the quest graph.
   - **`QuestAsset`** — soft reference to your quest graph asset.
3. Assign this DataTable to `UAQSQuestManagerComponent.QuestsDB` on your player controller Blueprint.

### C. Add UAQSQuestManagerComponent to your PlayerController

1. Open your PlayerController Blueprint.
2. Add component → `UAQSQuestManagerComponent`.
3. In **Details**:
   - **`QuestsDB`** — assign your quest DataTable.
   - **`bAutoTrackQuest`** — true to auto-track the newest started quest.
   - **`DefaultQuestTag`** *(optional)* — quest to auto-start on BeginPlay.

### D. Add UAQSQuestTargetComponent to world actors

1. Open any actor that will be a quest target (NPC, chest, location trigger, etc.).
2. Add component → `UAQSQuestTargetComponent`.
3. Set the component's **`TargetTag`** to match the `FGameplayTag` used in the objective's `ReferencedTargets` array.
4. Register it: the component auto-registers with the `UAQSQuestManagerComponent` when the quest is active.

---

## 3 — Core Workflow / Usage

### Starting a quest

```
// On the server (or with authority):
QuestManager->StartQuest(FGameplayTag::RequestGameplayTag("Quest.MainStory.Chapter1"));

// Via Server RPC (from client):
QuestManager->ServerStartQuest(QuestTag);
```

### Completing an objective

```
// By tag (simplest):
QuestManager->CompleteObjective(FGameplayTag::RequestGameplayTag("Quest.MainStory.Chapter1.TalkToNPC"));

// By node GUID (for branched quests):
QuestManager->CompleteObjectiveByNodeID(ObjectiveGUID);

// Branched objective (unlocks only specific transition paths):
QuestManager->CompleteBranchedObjective(ObjectiveGUID, { "PathA" });

// Via Server RPC:
QuestManager->ServerCompleteObjectiveByTag(ObjectiveTag);
```

### Querying quest state

```
bool bInProgress = QuestManager->IsQuestInProgressByTag(QuestTag);
bool bDone = QuestManager->IsQuestCompletedByTag(QuestTag);
bool bFailed = QuestManager->IsQuestFailedByTag(QuestTag);
bool bObjInProgress = QuestManager->IsObjectiveInProgressByTag(ObjectiveTag);

TArray<FAQSQuestRecord> Records = QuestManager->GetInProgressQuestsRecords();
UAQSQuest* TrackedQuest = QuestManager->GetCurrentlyTrackedQuest();
TArray<UAQSQuestObjective*> Objectives = QuestManager->GetCurrentlyTrackedQuestObjectives();
```

### Tracking

```
QuestManager->TrackInProgressQuestByTag(QuestTag);
QuestManager->UntrackCurrentQuest();
```

### Key delegates on UAQSQuestManagerComponent

| Delegate | Signature | When it fires |
|---|---|---|
| `OnQuestStarted` | `(FGameplayTag)` | A quest begins |
| `OnQuestEnded` | `(FGameplayTag, bool bSuccessful)` | A quest ends (success or failure) |
| `OnObjectiveStarted` | `(FGuid, FGameplayTag)` | An objective becomes active |
| `OnObjectiveCompleted` | `(FGuid, FGameplayTag)` | An objective is completed |
| `OnObjectiveUpdated` | `(FGuid, FGameplayTag)` | Objective progress changes (repetitions) |
| `OnInProgressQuestsUpdate` | `()` | Active quest list changes |
| `OnCompletedQuestsUpdate` | `()` | Completed quest list changes |
| `OnTrackedQuestChanged` | `()` | Tracked quest changes |

---

## 4 — Wire to Characters / Blueprints

### Auto-starting a quest via trigger volume

1. Duplicate a `UAQSQuestTrigger` actor from the sample.
2. Set its `QuestTag` to the quest you want to start on overlap.
3. Place it in the level. When the player enters, it calls `StartQuest` automatically.

### Completing objectives from game events

Objectives should be completed wherever the relevant game event occurs. Common patterns:

- **Kill objective**: In the enemy character's `OnDeath` delegate, get the player's `UAQSQuestManagerComponent` and call `CompleteObjective(KillObjectiveTag)`.
- **Collect objective**: In the item pickup logic, call `CompleteObjective` after the item is added to inventory.
- **Interact / talk objective**: In the NPC interaction Blueprint, call `CompleteObjective` after the dialogue ends.
- **Reach location**: Use a trigger box with `OnActorBeginOverlap` → `CompleteObjective`.

### Updating repetition-based objectives

If an objective requires multiple completions (e.g. "Kill 5 wolves"):
1. Set `Repetitions = 5` on the `UAQSQuestObjective` in the graph node.
2. Each time the event fires, call `CompleteObjective` once. The system increments the counter and fires `OnObjectiveUpdated`. When the counter reaches `Repetitions`, the objective auto-completes.

### World Partition integration

Set `LayerToLoad` on the quest graph to a `UDataLayerAsset`. When the quest starts, the system loads that layer (making its actors visible / streamable). When the quest ends, the layer is unloaded. This enables per-quest level sections.

### Building a Quest Journal UI

Bind to `OnInProgressQuestsUpdate` and `OnTrackedQuestChanged` on the `UAQSQuestManagerComponent`.
- For the tracked quest: call `GetCurrentlyTrackedQuest()` → display `QuestName`, `QuestDescription`.
- For objectives: call `GetCurrentlyTrackedQuestObjectives()` → iterate and display `GetObjectiveName()`, `GetCurrentRepetitions()`, `GetRepetitions()`, `IsObjectiveCompleted()`.

---

## 5 — Verify

**Checklist before testing:**

- [ ] Quest graph is duplicated from sample, saved under `Content/YourGame/Quests/`, and has a unique `QuestTag`.
- [ ] Quest DataTable contains a row for the quest, with `QuestAsset` pointing to your graph.
- [ ] `UAQSQuestManagerComponent.QuestsDB` is assigned on the PlayerController Blueprint.
- [ ] All objective nodes have unique `ObjectiveTag` values (child tags of the quest tag).
- [ ] Quest target actors have `UAQSQuestTargetComponent` with matching `TargetTag`.
- [ ] `StartQuest` is called with authority (server or server-side code).
- [ ] `CompleteObjective` is called where the relevant game event fires.
- [ ] Graph has exactly one `UAQSQuestSuccededNode` and one `UAQSQuestFailedNode`.

**Common failures:**

| Symptom | Fix |
|---|---|
| `StartQuest` returns false | Quest tag not found in `QuestsDB`, or `QuestAsset` is null in the DataTable row |
| Objective never completes | `CompleteObjective` tag doesn't match the `ObjectiveTag` set on the objective node |
| Quest not replicated to client | `StartQuest` called on client instead of server; use `ServerStartQuest` RPC |
| Branched objective unlocks wrong path | `TransitionFilter` name on edge doesn't match the filter name passed to `CompleteBranchedObjective` |
| Tracked quest journal is empty | No quest is tracked; check `bAutoTrackQuest` or call `TrackInProgressQuestByTag` manually |
| World Partition layer never loads | `LayerToLoad` is null in the quest graph, or the Data Layer is not set to Runtime Loaded |
| `OnObjectiveUpdated` never fires for kill counts | `CompleteObjective` is not being called per-kill; wire it to the enemy death delegate |
