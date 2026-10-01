---
name: combo-graph
description: Build data-driven combo attack chains using the ACF Combo Graph module (graph nodes, transitions, input buffering, and Chooser integration) and wire them to ActionsSystem abilities.
globs: []
alwaysApply: false
---

# Combo Graph — ACF Ultimate

The **Combo Graph** module (`AscentComboGraph`) provides data-driven combo attack chains built on top of `AGSGraphRuntime`. A `UACFComboGraph` asset is a node graph where each `UACFComboNode` holds an animation montage plus a damage/modifier configuration, and `UACFTransition` edges define which input tag (and conditions) advance the chain to the next node. At runtime a `UACFComboComponent` on the character starts a per-character duplicate of the graph, opens/closes an input buffer driven by anim notifies, and routes input tags to the active node. Combos are launched and animated through the Actions System via `UACFComboAttackAction` (player) and `UACFComboAIAttackAction` (AI), and montages/combos can be selected dynamically through Unreal's Chooser system.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Sample combo graph | `UACFComboGraph` | `/AscentCombatFramework/.../Combos/` | The node graph defining a combo chain |
| Sample combo attack action | `UACFComboAttackAction` | `/AscentCombatFramework/Actions/` | Ability that starts/drives a combo for players |
| Sample AI combo action | `UACFComboAIAttackAction` | `/AscentCombatFramework/Actions/` | Combo action with AI input probabilities |
| Chooser table (combos) | `Chooser Table` (result `ACFComboGraph`) | `/Game/.../Choosers/` | Dynamically pick a combo graph |

> **Never edit sample assets.** Duplicate the sample combo graph and actions into `Content/YourGame/Combos/` (and `Content/YourGame/Actions/`) and customize your copy. Sample assets are overwritten on every plugin/sample update.

### Key classes

| Class | Role |
|---|---|
| `UACFComboGraph` | The graph asset (extends `UAGSGraph`). Owns nodes/transitions, tracks the current node, performs transitions |
| `UACFComboComponent` | Actor component that starts/stops combos, holds the runtime graph instance, manages the input buffer, routes input tags (server-authoritative) |
| `UACFBaseComboNode` | Abstract base for all combo nodes (extends `UAGSGraphNode`) |
| `UACFComboNode` | A combo step: holds `ComboMontage`, `ComboModifier`, `DamageToActivate`, `TraceChannels` |
| `UACFStartComboNode` | Entry node; exposes `triggeringAction` (the tag that starts the combo) |
| `UACFRerouteNode` | Routing helper node for graph organization |
| `UACFTransition` | Graph edge: `TransitionInputTag`, `Conditions`, `Priority`, optional weighted (`bUseWeightedPriorities`, `Weight`) |
| `UACFComboAttackAction` | Action ability (extends `UACFAttackAction`) that runs a `Combo` graph; supports `bAutoOpenBuffer` |
| `UACFComboAIAttackAction` | AI variant with `AIInputProbabilities` (TMap of input tag → probability) |
| `UACFInputBufferNotifyState` | Anim notify state that opens the input buffer for its duration on the montage |

---

## 2 — Setup / Configuration

### A. Create your combo graph

1. Duplicate the sample `UACFComboGraph` into `Content/YourGame/Combos/` (or, if none exists, right-click → **Blueprint Class / Misc** to create one from `UACFComboGraph`).
2. Open the graph editor.
3. Add a `UACFStartComboNode` as the entry point:
   - Set **`triggeringAction`** to the GameplayTag that launches this combo (e.g. `Actions.Attack.Light`).
   - Set **`ComboMontage`** to the first attack montage.
4. Add one `UACFComboNode` per follow-up step. For each node set:
   - **`ComboMontage`** — the montage for this step.
   - **`ComboModifier`** (`FAttributesSetModifier`) — optional stat modifier applied during the step.
   - **`DamageToActivate`** (`EDamageActivationType`) — how/when damage traces activate.
   - **`TraceChannels`** — the trace channel names used for hit detection.
5. Connect nodes with `UACFTransition` edges. On each transition set:
   - **`TransitionInputTag`** — the input tag that advances to the next node (e.g. `Actions.Attack.Heavy`).
   - **`Conditions`** — optional `UACFActionCondition` instances that must pass.
   - **`Priority`** — higher priority transitions are evaluated first when multiple match.
   - For probabilistic branching, enable **`bUseWeightedPriorities`** and set **`Weight`**.

### B. Open the input buffer in your montages

Transitions are only accepted while the input buffer is open. Choose one approach per step:

- **Per-montage window (recommended):** In each combo montage, add a `UACFInputBufferNotifyState` notify-state spanning the window where the next input is allowed.
- **Whole-animation:** On the `UACFComboAttackAction`, set **`bAutoOpenBuffer = true`** to keep the buffer open for the entire montage.

### C. Create the combo attack action

1. Duplicate the sample `UACFComboAttackAction` (player) into `Content/YourGame/Actions/`.
2. In Class Defaults set **`Combo`** to your duplicated `UACFComboGraph`.
3. Set **`bAutoOpenBuffer`** if you are not using buffer notify-states.
4. Add this action to your character's `UACFAbilitySet` under the same triggering tag (see the actions-system skill).
5. For AI, duplicate `UACFComboAIAttackAction` instead and fill **`AIInputProbabilities`** (input tag → chance of being chosen) so AI advances the combo automatically.

---

## 3 — Core Workflow / Runtime API

### How a combo runs

1. The triggering action fires (e.g. light attack), activating `UACFComboAttackAction`.
2. The action calls `UACFComboComponent::StartCombo(Combo, triggeringAbility)`. The component **duplicates** the graph per character (so `GetCurrentCombo()` returns the runtime instance, not the source asset).
3. The start node's montage plays; its input buffer notify opens the window.
4. Each new input tag is sent to the server (`SendInputReceived`) and routed into the graph; `PerformTransition` evaluates matching transitions (by `TransitionInputTag`, conditions, and priority/weight) and advances to the next node.
5. If no valid input is buffered when the montage ends, the combo stops.

### `UACFComboComponent` API

```
// Start / stop
ComboComp->StartCombo(MyComboGraph, FGameplayTag::RequestGameplayTag("Actions.Attack.Light"));
ComboComp->StopCombo(MyComboGraph);

// Buffer control (usually driven by notify-states)
ComboComp->SetInputBufferOpened(true);

// Queries
bool bAny   = ComboComp->IsExecutingAnyCombo();
bool bThis  = ComboComp->IsExecutingCombo(MyComboGraph);
UACFComboGraph* Current = ComboComp->GetCurrentCombo();   // runtime instance
bool bPending = ComboComp->HasPendingInput();
FGameplayTag Last = ComboComp->GetLastTagInput();
ComboComp->ClearInputTag();
```

### `UACFComboGraph` API

```
graph->StartCombo(StartActionTag);
graph->PerformTransition(currentInputTag, Character);   // returns true if it advanced
UAnimMontage* M = graph->GetCurrentComboMontage();
UACFComboNode* N = graph->GetCurrentComboNode();
FAttributesSetModifier Mod; graph->GetCurrentComboModifier(Mod);
TArray<FGameplayTag> Valid = graph->GetValidInputsForCurrentNode();
graph->StopCombo();
```

### Input routing (player)

`UACFComboComponent::SetupPlayerInputComponent(EnhancedInputComponent)` binds the actions in the component's **`ComboInputs`** map (`UInputAction* → FGameplayTag`). Populate `ComboInputs` on the component so each input action maps to the transition tag it should send. Call `SetupPlayerInputComponent` during input setup / on every possess.

### Chooser integration (dynamic combo selection)

To pick the combo graph at runtime instead of hard-coding `Combo`, use `ACFChooserComboAttackAction` with a Chooser Table whose result type is `ACFComboGraph`. For deterministic multiplayer selection enable `bUseDeterministicRandomization`, add an Output Float column bound to the action's `Randomize` property at `WeightColumnIndex`, and set per-row weights. See `docs/chooser-actions-guide.md` and `docs/sustained-chooser-actions.md` for full setup, filters (gameplay tag / float range / bool / enum), nested choosers, and anti-repeat (`RepeatProbabilityMultiplier`).

---

## 4 — Wire to Characters / Blueprints

1. Add a **`UACFComboComponent`** to your character Blueprint (it is a `BlueprintSpawnableComponent`). `AACFCharacter` already provides a `UACFAbilitySystemComponent` which the combo component uses.
2. On the player character, populate the component's **`ComboInputs`** map and call `SetupPlayerInputComponent(GetEnhancedInputComponent())` in `SetupPlayerInputComponentBP` (and re-bind on possess).
3. Register your `UACFComboAttackAction` in the character's `UACFAbilitySet` (or moveset ability set) under the combo's start tag, so triggering that action starts the combo.
4. For AI: register the `UACFComboAIAttackAction` instead and ensure `AIInputProbabilities` covers the transition tags so the AI advances the chain — no input binding is required.
5. Multiplayer: input handling is server-authoritative (`SendInputReceived` is a server RPC; `bIsPerformingCombo` and `LastTagInput` are replicated). For instant client-side combo selection through Chooser, use deterministic mode.

---

## 5 — Verify

**Checklist before testing:**

- [ ] Combo graph is duplicated into `Content/YourGame/Combos/` (sample untouched).
- [ ] The graph has a `UACFStartComboNode` with a valid `triggeringAction` tag and `ComboMontage`.
- [ ] Each `UACFComboNode` has a `ComboMontage` set.
- [ ] Transitions have correct `TransitionInputTag` values and priorities/weights.
- [ ] Each combo montage has a `UACFInputBufferNotifyState` window, **or** the action has `bAutoOpenBuffer = true`.
- [ ] `UACFComboAttackAction.Combo` points to your duplicated graph.
- [ ] The action is registered in the character's `UACFAbilitySet` under the start tag.
- [ ] `UACFComboComponent` is on the character; `ComboInputs` is populated and `SetupPlayerInputComponent` is called (player).
- [ ] AI uses `UACFComboAIAttackAction` with `AIInputProbabilities` filled.

**Common failures:**

| Symptom | Fix |
|---|---|
| Combo starts but never chains | Input buffer never opens — add `UACFInputBufferNotifyState` or set `bAutoOpenBuffer = true` |
| Input pressed but no transition | `TransitionInputTag` doesn't match the tag sent; check `ComboInputs` mapping |
| First attack doesn't trigger combo | `UACFStartComboNode.triggeringAction` doesn't match the action's trigger tag |
| Two transitions both fire / wrong branch | Set distinct `Priority` values, or use `bUseWeightedPriorities` + `Weight` |
| Transition blocked unexpectedly | A `UACFActionCondition` on the transition is failing (`AreConditionsMet` returns false) |
| Editing the graph affects no character | You edited the source asset, but `GetCurrentCombo()` is a per-character duplicate — restart play / re-trigger |
| AI never continues the combo | `AIInputProbabilities` empty or tags don't match the graph's transition tags |
| Combo desyncs in multiplayer | Use deterministic Chooser mode, or rely on the server-authoritative `SendInputReceived` path |
| No damage during a step | `DamageToActivate` / `TraceChannels` on the node not configured |
