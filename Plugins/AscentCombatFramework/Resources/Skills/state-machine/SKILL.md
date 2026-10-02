---
name: state-machine
description: Build visual finite state machines with the ACF State Machine module (ASM graph, state nodes, tag-driven transitions) and drive them from an actor component with full multiplayer replication.
globs: []
alwaysApply: false
---

# State Machine (ASM) — ACF Ultimate

The **Ascent State Machine** module (`AscentStateMachine`) provides visual finite state machines built on `AGSGraphRuntime`. A `UASMStateMachine` asset is a graph of `UASMStateNode` nodes, each owning an instanced `UASMBaseFSMState` object with `OnEnter` / `OnExit` / `OnUpdate` / `OnTransition` Blueprint events. States are connected by `UASMTransition` edges keyed by a `FGameplayTag`. A `UASMFSMComponent` placed on any actor hosts a state machine instance, starts/stops it, and triggers tag-based transitions — with replicated (server-authoritative) variants for multiplayer. Use it for AI behavior phases, boss fights, door/interaction states, game flow, or any logic best expressed as discrete states.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Sample state machine | `UASMStateMachine` | `/AscentCombatFramework/.../FSM/` | The graph defining states + transitions |
| Sample FSM state logic | `UASMBaseFSMState` (Blueprint subclass) | Authored inline on each node | Per-state enter/exit/update logic |

> **Never edit sample assets.** Duplicate any sample state machine graph into `Content/YourGame/FSM/` and customize your copy — sample assets are overwritten on plugin/sample updates.

### Key classes

| Class | Role |
|---|---|
| `UASMStateMachine` | The FSM graph asset (extends `UAGSGraph`). Starts/stops, tracks current state, triggers transitions, dispatches tick |
| `UASMStateNode` | A node wrapping a `StateName` (FName) and an instanced `UASMBaseFSMState` |
| `UASMStartFSMNode` | The entry node where the FSM begins (`OnEnter` is called here on start) |
| `UASMBaseFSMState` | Blueprintable state logic object: `OnEnter`, `OnExit`, `OnUpdate`, `OnTransition`; can call `TriggerTransition` |
| `UASMNestedFSMState` | A state that itself hosts a nested/sub state machine |
| `UASMTransition` | Graph edge keyed by `TransitionTag`, gated by `ActivationConditions` (`UAGSCondition` array) |
| `UASMFSMComponent` | Actor component that hosts and drives a state machine (replicated control) |
| `UASMFSMFunctionLibrary` | Static helpers to trigger transitions on an actor's FSM from anywhere |

---

## 2 — Setup / Configuration

### A. Create the state machine graph

1. Duplicate a sample `UASMStateMachine` into `Content/YourGame/FSM/` (or create a new `UASMStateMachine` asset if none exists).
2. Open the graph editor. It already has a `UASMStartFSMNode`.
3. Add a `UASMStateNode` for each state. For each node:
   - Set **`StateName`** (FName) — used by `GetCurrentStateName()` and shown in the node title.
   - Set **`State`** — create/assign an instanced `UASMBaseFSMState` Blueprint subclass.
4. Author each state's logic by subclassing `UASMBaseFSMState` (Blueprintable, `EditInlineNew`) and overriding:
   - **`OnEnter`** — runs when the state becomes active.
   - **`OnExit`** — runs when leaving the state.
   - **`OnUpdate(deltaTime)`** — runs each tick (only if the component ticks; see below).
   - **`OnTransition(previousState)`** — runs when entering via a transition.
5. Connect states with `UASMTransition` edges. On each transition set:
   - **`TransitionTag`** — the GameplayTag that triggers this transition.
   - **`ActivationConditions`** — optional `UAGSCondition` instances that must pass (`VerifyTransitionConditions`).

### B. Configure the component

1. Add a `UASMFSMComponent` to your actor (it is a `BlueprintSpawnableComponent`).
2. Set **`StateMachine`** to your duplicated `UASMStateMachine` asset.
3. Set **`bCanFsmTick`** to true if your states use `OnUpdate` (off by default for performance).
4. Set **`bShouldDisplayDebugInfo`** to true to print the current state on screen while debugging.

---

## 3 — Core Workflow / Runtime API

### Lifecycle (single-player / authority)

```
// Start the FSM (calls OnEnter on the start node's state)
FSMComp->StartFSM();

// Fire a transition by tag (advances if a matching, condition-passing edge exists)
FSMComp->TriggerTransition(FGameplayTag::RequestGameplayTag("FSM.ToCombat"));

// Stop the FSM (calls OnExit on the current state; further triggers ignored until restart)
FSMComp->StopFSM();
```

### Multiplayer (replicated control)

Use the synched / client variants so all peers stay in sync:

```
FSMComp->SynchedStartFSM();                 // Server RPC → multicast start
FSMComp->SynchedTriggerTransition(Tag);     // Server RPC → multicast transition
FSMComp->SynchedStopFSM();                  // Server RPC → multicast stop
FSMComp->ClientTriggerTransition(Tag);      // Run a transition on the owning client
```

### Querying state

```
FName Name = FSMComp->GetCurrentStateName();
UASMBaseFSMState* State = FSMComp->GetCurrentState();
bool bActive = FSMComp->IsFSMActive();
bool bTicks  = FSMComp->IsFsmTicking();
FSMComp->SetFsmTickEnabled(true);   // toggle OnUpdate ticking at runtime
```

### Triggering transitions from within a state

Inside a `UASMBaseFSMState` subclass you can transition directly:

```
// From state logic (Blueprint or C++):
TriggerTransition(FGameplayTag::RequestGameplayTag("FSM.ToIdle"));
AActor* Owner = GetActorOwner();
UASMStateMachine* MyFSM = GetFSM();
APlayerController* PC = GetLocalPlayerController();
```

### Triggering from anywhere (function library)

```
// Trigger a transition on any actor that has a UASMFSMComponent:
UASMFSMFunctionLibrary::TriggerTransition(TargetActor, Tag);
UASMFSMFunctionLibrary::ClientTriggerTransition(TargetActor, Tag);
```

### Nested state machines

Use `UASMNestedFSMState` as a node's state to embed a sub-FSM, letting a single high-level state contain its own internal states (e.g. a "Combat" state with nested "Approach / Attack / Retreat").

---

## 4 — Wire to Characters / Blueprints

1. Add a `UASMFSMComponent` to the actor that should own the behavior (character, AI pawn, boss, interactable, or game-mode helper actor).
2. Assign your duplicated `UASMStateMachine` to the component's `StateMachine` property.
3. Call `StartFSM()` (or `SynchedStartFSM()` in multiplayer) when appropriate — e.g. in `BeginPlay`, on possession, or when combat begins.
4. Drive transitions from gameplay events:
   - From AI/behavior trees: call `TriggerTransition(Tag)` or `UASMFSMFunctionLibrary::TriggerTransition(Owner, Tag)`.
   - From within states: call `TriggerTransition` in `OnUpdate`/`OnEnter` based on conditions.
5. Enable `bCanFsmTick` only on actors whose states need per-frame `OnUpdate` logic.
6. In states, use `GetActorOwner()` to reach the owning actor and read/write gameplay data (health, target, etc.).

---

## 5 — Verify

**Checklist before testing:**

- [ ] State machine graph is duplicated into `Content/YourGame/FSM/` (sample untouched).
- [ ] Every `UASMStateNode` has a unique `StateName` and an assigned `State` instance.
- [ ] The graph has a reachable `UASMStartFSMNode`.
- [ ] Each `UASMTransition` has the correct `TransitionTag` and any needed `ActivationConditions`.
- [ ] `UASMFSMComponent.StateMachine` points to your duplicated asset.
- [ ] `bCanFsmTick` is enabled if any state uses `OnUpdate`.
- [ ] `StartFSM()` / `SynchedStartFSM()` is actually called at runtime.
- [ ] Multiplayer uses the `Synched*` / `Client*` variants, not the local-only ones.

**Common failures:**

| Symptom | Fix |
|---|---|
| FSM does nothing | `StartFSM()` was never called, or `StateMachine` is null on the component |
| `OnUpdate` never runs | `bCanFsmTick` is false — enable it or call `SetFsmTickEnabled(true)` |
| Transition ignored | `TransitionTag` doesn't match the tag passed to `TriggerTransition`, or an `ActivationCondition` fails |
| Transitions ignored after stop | FSM was stopped; triggers are ignored until `StartFSM()` is called again |
| State desyncs across clients | Used `TriggerTransition`/`StartFSM` (local) instead of `SynchedTriggerTransition`/`SynchedStartFSM` |
| `GetCurrentStateName` returns None | The FSM isn't started, or the current node has an empty `StateName` |
| Can't reach a state | No transition path from the start node, or the edge tag/conditions never satisfied |
| Editing graph doesn't affect actor | You edited the sample asset, not your duplicated copy assigned on the component |
