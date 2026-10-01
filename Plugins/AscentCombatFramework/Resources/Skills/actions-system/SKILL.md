---
name: actions-system
description: Create and trigger gameplay abilities, action sets, combos, sustained actions, and input bindings using the ACF Actions System (GAS-based) module.
globs: []
alwaysApply: false
---

# Actions System — ACF Ultimate

The **Actions System** is the GAS-based abilities and combat actions layer. `UACFAbilitySystemComponent` (on every `AACFCharacter`) manages which abilities are granted, handles action priority, buffers combos, and drives the state machine. `UACFGameplayAbility` is the base class for all abilities — it wraps a `UAnimMontage`, `FActionConfig` (cost, cooldown), and lifecycle events. Abilities are organized into `UACFAbilitySet` DataAssets; multiple sets can be loaded per moveset. Input is mapped via `UACFInputConfigDataAsset`.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Sample ability set | `UACFAbilitySet` | `/AscentCombatFramework/Actions/AbilitySets/` | Groups abilities granted to a character |
| Sample action ability | `UACFActionAbility` | `/AscentCombatFramework/Actions/` | One-shot combat action (attack, dodge, etc.) |
| Sample sustained action | `UACFSustainedAction` | `/AscentCombatFramework/Actions/` | Hold-to-sustain action (block, draw bow) |
| Sample input config | `UACFInputConfigDataAsset` | `/AscentCombatFramework/Input/` | Maps Enhanced Input actions → ability tags |

> **Never edit sample assets.** Duplicate into `Content/YourGame/Actions/` and customize your copy.

### Key classes

| Class | Role |
|---|---|
| `UACFAbilitySystemComponent` | Extends `UAbilitySystemComponent`; priority logic, buffering, moveset switching |
| `UACFGameplayAbility` | Base ability: montage, cost, cooldown, warp support |
| `UACFActionAbility` | Standard one-shot action (attack, roll, jump attack) |
| `UACFSustainedAction` | Hold-triggered ability released by `ReleaseSustainedAction()` |
| `UACFAbilitySet` | DataAsset listing `FAbilityConfig` entries keyed by GameplayTag |
| `UACFActionsSet` | Lightweight `UObject` holding `FActionState` array for a moveset |
| `UACFInputConfigDataAsset` | Maps `UInputAction` → ability `FGameplayTag` |
| `FActionConfig` | Per-ability config: cost (`TArray<FStatisticValue>`), cooldown, priority |

---

## 2 — Setup / Configuration

### A. Create an ability Blueprint

1. In the Content Browser, right-click → **Blueprint Class**.
2. Choose `UACFActionAbility` (one-shot) or `UACFSustainedAction` (hold) as parent.
3. Save under `Content/YourGame/Actions/`.
4. Open the Blueprint and configure in **Class Defaults**:
   - **`animMontage`** — the animation montage to play.
   - **`ActionConfig.ActionCost`** — array of `FStatisticValue` (e.g. Stamina cost).
   - **`ActionConfig.Cooldown`** — cooldown GameplayEffect class (or leave null).
   - **`TriggeringTag`** — the `FGameplayTag` that identifies this action (under `Actions.*`).
   - **`MontageInfo.MontageReproductionType`** — `Normal`, `Warp`, or `RootMotion`.
5. Override `OnNotablePointReached` (BlueprintNativeEvent) to handle mid-animation events (e.g. spawn projectile, activate hit trace).
6. Override `OnMontageFinished` to handle post-action cleanup.

### B. Create an AbilitySet DataAsset

1. Right-click → **Miscellaneous → Data Asset** → choose `UACFAbilitySet`.
2. Save under `Content/YourGame/Actions/`.
3. Add entries to the set:
   - **`AbilityTag`** — the `FGameplayTag` that triggers this ability.
   - **`AbilityClass`** — your ability Blueprint class.
   - **`bGrantOnStart`** — true to grant at initialization.
4. Assign this `UACFAbilitySet` as `DefaultAbilitySet` in your character's `UACFCharacterDataAsset`.
5. For moveset-dependent abilities (e.g. sword vs bow), populate `MovesetAbilities` map on the DataAsset:
   - Key: moveset tag (e.g. `Moveset.Sword`).
   - Value: a separate `UACFAbilitySet` for that moveset.

### C. Set up input bindings

1. Duplicate the sample `UACFInputConfigDataAsset`.
2. Save under `Content/YourGame/Input/`.
3. In the DataAsset, map each `UInputAction` asset to an ability `FGameplayTag`.
4. In your player character Blueprint's `SetupPlayerInputComponentBP`:
   - Bind each Enhanced Input action.
   - On Triggered/Started: call `GetActionsComponent()->TriggerAction(ActionTag, EActionPriority::ELow)`.
   - For sustained actions: on Started → `TriggerAction(...)`, on Completed/Canceled → `GetActionsComponent()->ReleaseSustainedAction(ActionTag)`.

---

## 3 — Core Workflow / Usage

### Triggering actions

```
// Standard trigger (respects priority + buffering):
ActionsComp->TriggerAction(FGameplayTag::RequestGameplayTag("Actions.Attack.Light"), EActionPriority::ELow, true);

// Force trigger (bypasses priority check):
Character->ForceAction(ActionTag);

// Trigger basic GAS ability (no priority):
ActionsComp->TriggerAbility(AbilityTag);
```

### Priority system

`EActionPriority` values (low to high):
- `ELow` — basic inputs (light attack, dodge).
- `EMedium` — contextual reactions.
- `EHigh` — overrides in progress actions.
- `EHighest` — forces interruption of anything.

A new action is only executed if its priority ≥ the current action's priority.

### Action buffering (combos)

```
// Enable buffering (call once at setup):
ActionsComp->StartStoringActions();

// Buffer the next combo step during the current action:
ActionsComp->StoreAbilityInBuffer(NextComboTag);

// The component auto-executes the buffered action when the current one ends.
```

### Moveset switching

```
// Switch ability set (e.g. when a weapon is equipped):
ActionsComp->SetMovesetActions(FGameplayTag::RequestGameplayTag("Moveset.Sword"));

// Remove a moveset's abilities:
ActionsComp->RemoveAbilitySetByTag(MovesetTag);
```

### Granting / revoking abilities at runtime

```
// Grant a full set:
ActionsComp->GrantAbilitySet(MyAbilitySet, MovesetTag);

// Grant a single ability:
FGameplayAbilitySpecHandle Handle = ActionsComp->GrantACFAbility(AbilityConfig, MovesetTag);

// Remove:
ActionsComp->RemoveAbilitySet(MyAbilitySet, MovesetTag);
```

### Querying state

```
bool bBusy = ActionsComp->IsPerformingAction();
FGameplayTag CurrentTag = ActionsComp->GetCurrentActionTag();
EActionPriority CurrentPrio = ActionsComp->GetCurrentActionPriority();
int32 ComboStep = ActionsComp->GetComboCount(ComboTag);
```

### Key delegates

| Delegate | Signature | When it fires |
|---|---|---|
| `OnAbilityStartedEvent` | `(FGameplayTag)` | Any ability begins |
| `OnAbilityFinishedEvent` | `(FGameplayTag)` | Any ability ends |

---

## 4 — Wire to Characters / Blueprints

### Wiring input (player pawn)

1. In your player character Blueprint, implement `SetupPlayerInputComponentBP`.
2. Use `UEnhancedInputComponent::BindAction` for each input action defined in your `UACFInputConfigDataAsset`.
3. On the **Triggered** event, call `TriggerAction` on `GetActionsComponent()`.
4. For hold actions: on **Started** trigger the action; on **Completed** call `ReleaseSustainedAction`.

Example Blueprint pseudo-logic:
```
// Light Attack (pressed)
EnhancedInput.BindAction(IA_LightAttack, ETriggerEvent::Started)
  → GetActionsComponent()->TriggerAction("Actions.Attack.Light", ELow, true)

// Block (hold)
EnhancedInput.BindAction(IA_Block, ETriggerEvent::Started)
  → GetActionsComponent()->TriggerAction("Actions.Block", EMedium, false)
EnhancedInput.BindAction(IA_Block, ETriggerEvent::Completed)
  → GetActionsComponent()->ReleaseSustainedAction("Actions.Block")
```

### Wiring for AI

AI characters trigger actions via the AI controller or behavior tree tasks:
```
// In a BTTask_TriggerAction node (or custom task):
Character->TriggerAction(AttackTag, EActionPriority::ELow, false);
```
No input binding is needed — ability tags drive everything.

### Ability Blueprint lifecycle overrides

| Override | When to use |
|---|---|
| `OnNotablePointReached` | Activate hit traces, spawn projectiles mid-montage |
| `OnMontageFinished(bInterrupted)` | Cleanup, reset state flags |
| `OnGameplayEventReceived(eventTag)` | React to mid-ability gameplay events |
| `GetWarpInfo / GetWarpTransform` | Drive Motion Warping for lunge/finisher attacks |
| `GetPlayRate` | Return stat-based play rate (e.g. attack speed) |

---

## 5 — Verify

**Checklist before testing:**

- [ ] Ability Blueprints are duplicated from sample and saved under `Content/YourGame/Actions/`.
- [ ] Each ability Blueprint has `animMontage`, `TriggeringTag`, and `ActionConfig` filled.
- [ ] `UACFAbilitySet` DataAsset has all abilities listed with correct tags.
- [ ] `DefaultAbilitySet` is assigned in the `UACFCharacterDataAsset`.
- [ ] Input actions are bound in `SetupPlayerInputComponentBP` (player only).
- [ ] `StartStoringActions()` called if combos are needed.
- [ ] For movesets: `MovesetAbilities` map on the DataAsset has entries for each moveset tag.
- [ ] Character has `UACFAbilitySystemComponent` (present automatically on `AACFCharacter`).

**Common failures:**

| Symptom | Fix |
|---|---|
| Action triggered but no animation plays | `animMontage` is null in the ability Blueprint |
| Action never fires | `TriggeringTag` doesn't match the tag passed to `TriggerAction`, or priority blocked |
| Combo doesn't chain | `StartStoringActions()` not called; or buffer window (`bCanBeStored` param) is false |
| Ability costs not deducted | `FStatisticValue` in `ActionConfig.ActionCost` references wrong attribute name |
| Sustained action never ends | `ReleaseSustainedAction` not called on input release |
| Moveset swap doesn't change animations | `SwitchMovesetActions` tag doesn't match a key in `MovesetAbilities` |
| AI triggers action but nothing happens | Missing `UACFAbilitySystemComponent` initialization — check `bAutoInit` on the component |
