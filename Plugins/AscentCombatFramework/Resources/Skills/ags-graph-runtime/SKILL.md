---
name: ags-graph-runtime
description: Foundation graph framework (AGS) that powers dialogue, quests, state machines, skill trees, and combo graphs — author custom graph nodes, edges, actions, and conditions.
globs: []
alwaysApply: false
---

# AGS Graph Runtime — ACF Ultimate

**AGS Graph Runtime** is the shared, generic graph foundation that every node-based ACF system is built on: **dialogue, quests, state machines, skill trees, and combo graphs** all subclass these base types. A graph (`UAGSGraph`) owns nodes (`UAGSGraphNode`) connected by edges (`UAGSGraphEdge`). Nodes activate/deactivate to drive traversal; each node can run pluggable **Actions** (`UAGSAction`) when reached and gate transitions with **Conditions** (`UAGSCondition`). Graph state (which nodes are active) serializes via `FAGSGraphRecord` for save/load and replication. This is a **framework skill** — read it before extending any graph system; the higher-level systems mostly add specialized node/action/condition subclasses on top of these classes.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Graph instance | `UAGSGraph` | Authored via system editors (dialogue/quest/etc.) | Container of nodes; traversal + save/replication |
| Graph node | `UAGSGraphNode` | Subclassed per system | A step/state; activate/deactivate, parents/children |
| Graph edge | `UAGSGraphEdge` | Subclassed per system | Directed connection `StartNode → EndNode` |
| Action | `UAGSAction` | Instanced on nodes | Logic run when a node is reached (`EditInlineNew`) |
| Condition | `UAGSCondition` | Instanced on nodes/edges | Boolean gate (`AND`/`OR` composites built in) |

> **Never edit sample graphs/assets.** Duplicate sample dialogue/quest/combo graphs into `Content/YourGame/...` and extend **your copies**. To add behaviour, create new **Blueprint subclasses** of the AGS base classes rather than modifying the framework.

### Key classes

| Class | Role |
|---|---|
| `UAGSGraph` | `Blueprintable UObject`; holds `AllNodes`, `RootNodes`, `ActivedNodes`; activate/deactivate, level queries, save records |
| `UAGSGraphNode` | `Blueprintable UObject`; `ParentNodes`, `ChildrenNodes`, `Edges`; `ActivateNode`/`DeactivateNode`, `GetDescription` |
| `UAGSGraphEdge` | `Blueprintable UObject`; `StartNode`, `EndNode`, `GetGraph` |
| `UAGSAction` | `EditInlineNew`; override `ExecuteAction`; `GetGraphOwnerActor` |
| `UAGSCondition` | `EditInlineNew`; override `VerifyCondition`; plus `UABGANDCondition` / `UABGORCondition` composites |
| `FAGSGraphRecord` / `FAGSGraphList` | Save/replication payload (`GraphID` + `ActiveNodeIds`), fast-array serialized |

---

## 2 — Setup / Configuration

You rarely instantiate AGS types directly — you author graphs through the higher-level editors (Dialogue, Quest, State Machine, Skill Tree, Combo). The setup that *is* common to all of them:

1. Each graph carries a `GraphTags` (`FGameplayTagContainer`) and a unique `GraphId` (regenerated on duplicate). Tag your graphs so systems can find them.
2. A graph is bound to a `APlayerController` at runtime (`GetPlayerController()`); actions/conditions receive this controller.
3. Nodes own their `Edges` map (`child node → edge`) and cache `ParentNodes` / `ChildrenNodes`. Authoring tools build these for you.
4. `bAllowCycles` defaults to `true` (state machines/combos can loop); editors enforce per-system connection rules via `CanCreateConnection`.

---

## 3 — Core Workflow / Runtime API

### Traversing a graph

```
// Activate a node (Blueprint or C++):
Graph->ActivateNode(SomeNode);          // virtual — systems override traversal
Graph->DeactivateNode(SomeNode);
Graph->DeactivateAllNodes();

bool bActive = Graph->IsNodeActive(SomeNode);
TArray<UAGSGraphNode*> Active = Graph->GetActiveNodes();
TArray<UAGSGraphNode*> All    = Graph->GetAllNodes();
UAGSGraphNode* Node = Graph->GetNodeById(NodeGuid);
```

### Node queries

```
bool bLeaf = Node->IsLeafNode();        // no children
bool bRoot = Node->IsRootNode();        // no parents
bool bOn   = Node->IsNodeActivated();
UAGSGraph* Owner = Node->GetGraph();
UAGSGraphEdge* Edge = Node->GetEdge(ChildNode);
AActor* OwnerActor = Graph->GetOwnerActor();   // walks outer chain to NPC/actor
```

### Authoring a custom node

1. Create a **Blueprint** (or C++) subclass of `UAGSGraphNode`.
2. Override `ActivateNode()` / `DeactivateNode()` (C++) for custom enter/exit behaviour.
3. Override `GetDescription()` (`BlueprintNativeEvent`) for editor/UI text.
4. (Editor) override `GetNodeTitle`, `GetBackgroundColor`, `CanCreateConnection` to control appearance and valid connections.

### Authoring a custom Action

```
// Subclass UAGSAction, override ExecuteAction:
void UMyAction::ExecuteAction_Implementation(APlayerController* PC, UAGSGraphNode* NodeOwner)
{
    AActor* Owner = GetGraphOwnerActor();   // the NPC/interactable running the graph
    // ...do work (give item, play sound, set flag)...
}
// Actions are added as Instanced (EditInlineNew) entries on a node and run via Execute().
```

### Authoring a custom Condition

```
// Subclass UAGSCondition, override VerifyCondition:
bool UMyCondition::VerifyCondition_Implementation(APlayerController* PC) const
{
    return /* gate logic */;
}
// Combine with built-ins: UABGANDCondition (all true) / UABGORCondition (any true).
// Evaluate via Verify(PC) or VerifyForNode(PC, NodeOwner).
```

### Save / load & replication

```
FAGSGraphRecord Record = Graph->CreateGraphRecord();   // GraphID + ActiveNodeIds
Graph->SynchWithGraphRecord(Record);                   // restore active node set
// FAGSGraphList holds many records (FastArraySerializer) for replicated/saved state.
```

---

## 4 — Wire to Characters / Blueprints

- AGS graphs are normally **owned by a component or actor** (e.g. a dialogue participant component, a quest manager). `GetOwnerActor()` walks `Graph → outer → component → actor` so actions/conditions can reach the NPC/interactable.
- When building a new graph-based system, the pattern is: a manager **component** instances a `UAGSGraph`, binds the `APlayerController`, then calls `ActivateNode` on root nodes and follows edges.
- Custom node/action/condition Blueprints appear automatically in the relevant system editor once they subclass the AGS base (and, where used, set `CompatibleGraphType`).
- For multiplayer, persist/replicate `FAGSGraphRecord`/`FAGSGraphList` and call `SynchWithGraphRecord` on clients to mirror active nodes.

---

## 5 — Verify

**Checklist before testing:**

- [ ] Custom logic is added as **subclasses** of `UAGSGraphNode` / `UAGSAction` / `UAGSCondition` — the framework itself is unmodified.
- [ ] Sample graphs were duplicated into `Content/YourGame/...` before editing.
- [ ] Graph is bound to a valid `APlayerController` at runtime (actions/conditions need it).
- [ ] Custom node sets editor connection rules (`CanCreateConnection`) if it has constraints.
- [ ] Save/replication uses `CreateGraphRecord` / `SynchWithGraphRecord`, not manual node copying.
- [ ] `GraphTags` set so the owning system can locate the graph.

**Common failures:**

| Symptom | Fix |
|---|---|
| Action does nothing | `ExecuteAction` not overridden, or action not added as Instanced entry on the node |
| `GetGraphOwnerActor` returns null | Graph not outered to a component/actor — check the owning component instances it |
| Condition always passes | Base `VerifyCondition_Implementation` returns `true`; override it in your subclass |
| Traversal stuck / never advances | Node never activated, or edges/children not built; verify in the system editor |
| Save restores wrong nodes | `GraphID` mismatch (regenerated on duplicate) — re-link record to the live graph |
| Custom node missing in editor | Wrong base class or `CompatibleGraphType` not set for that graph system |
| Infinite loop in traversal | `bAllowCycles` true with no exit condition — add a terminating condition/leaf |
