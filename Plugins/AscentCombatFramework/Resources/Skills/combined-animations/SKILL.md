---
name: combined-animations
description: Set up synchronized multi-actor (master/slave) contextual animations such as paired takedowns, finishers and ambushes using the ACF CombinedAnimationsSystem module.
globs: []
alwaysApply: false
---

# Combined Animations — ACF Ultimate

The **CombinedAnimationsSystem** plays synchronized two-actor animations (takedowns, finishers, paired interactions, ambushes) on top of Unreal's **Contextual Animation** plugin. One actor is the **master** (initiator) and one is the **slave** (target). The master holds a `UACFCombinedAnimMasterComponent` that picks the best matching `FCombinedAnimConfig` for a target; the slave holds a `UACFCombinedAnimSlaveComponent` that decides whether it is eligible via gameplay tags and `UCASAnimCondition` objects. Both components derive from `UACFCombinedAnimComponent`, which wraps a `UContextualAnimSceneActorComponent` and adds ACF rules (lock abilities, invulnerability, finisher kill).

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Combined animations config | `UACFCombinedAnimationsDataAsset` | `/AscentCombatFramework/CombinedAnimations/` | Holds a `TArray<FCombinedAnimConfig>` of all synced anims a master can play |
| Contextual Anim Scene | `UContextualAnimSceneAsset` | `/AscentCombatFramework/CombinedAnimations/Scenes/` | The actual synced montage/warp scene (referenced by a config) |
| Master component | `UACFCombinedAnimMasterComponent` | On initiator character BP | Selects & validates combined anims for a target |
| Slave component | `UACFCombinedAnimSlaveComponent` | On target character BP | Declares eligibility via `AnimTags` + conditions |
| Anim condition | `UCASAnimCondition` (+ `UCASORCondition`, `UCASANDCondition`) | Instanced on slave | Extra eligibility checks per anim |

> **Never edit sample assets.** Duplicate the sample `UACFCombinedAnimationsDataAsset` and scene assets into `Content/YourGame/CombinedAnimations/` and wire **your copies**.

### `FCombinedAnimConfig` (the heart of the system)

| Field | Meaning |
|---|---|
| `AnimTag` | Gameplay tag identifying this combined anim (used to filter/select) |
| `CombinedAnimation` | `TArray<UContextualAnimSceneAsset*>` — the synced scene(s) to play |
| `MaxDistanceToStart` | Max master↔slave distance to begin (default 450) |
| `MasterRequiredActionsSet` | Required moveset action tag on the master (empty = any) |
| `SlaveRequiredTags` | Tags the slave must have (checked against `AnimTags`) |
| `KillSlaveAfterAnim` | If true, slave is killed at the end (finisher) |
| `AmbushExecution` + `AmbushRequiredDegrees` | Restrict to ambush angle (e.g. behind the slave) |

---

## 2 — Setup / Configuration

### A. Author the contextual animation scene

1. Create / duplicate a `UContextualAnimSceneAsset` under `Content/YourGame/CombinedAnimations/Scenes/`.
2. Define the **master** and **slave** roles and assign each role's synced montage and warp targets (standard Contextual Animation workflow).

### B. Build the combined animations DataAsset (master side)

1. Duplicate the sample `UACFCombinedAnimationsDataAsset` into `Content/YourGame/CombinedAnimations/`.
2. Add a `FCombinedAnimConfig` entry per synced anim:
   - `AnimTag` (e.g. `CombinedAnim.Takedown.Front`).
   - `CombinedAnimation` → your scene asset(s).
   - `MaxDistanceToStart`, `MasterRequiredActionsSet` as needed.
   - `SlaveRequiredTags` → tags the target must expose.
   - For finishers set `KillSlaveAfterAnim = true`; for ambushes set `AmbushExecution = true` and `AmbushRequiredDegrees`.

### C. Add the master component

1. On the initiator character Blueprint, add `UACFCombinedAnimMasterComponent`.
2. Set its `CombinedAnimations` property to **your** duplicated DataAsset.

### D. Add the slave component

1. On the target character Blueprint, add `UACFCombinedAnimSlaveComponent`.
2. Set `AnimTags` to the tags this character supports (must satisfy `SlaveRequiredTags`).
3. (Optional) Add `AnimStartingConditions` — instanced `UCASAnimCondition` objects for extra checks. Use `UCASANDCondition` / `UCASORCondition` to combine. Conditions can also be injected at runtime via `SetAnimStartingConditions()` (e.g. by an execution-conditions character fragment).
4. Configure `bCanBeHitDuringCombinedAnims` and `bLockAbilityTriggersDuringCombinedAnims` (inherited from `UACFCombinedAnimComponent`) per character.

---

## 3 — Core Workflow / Runtime API

### Selecting and starting (master)

```
// Find the best synced anim for a target:
FCombinedAnimConfig outConfig;
if (MasterComp->TryGetBestCombinedAnimForActor(TargetActor, outConfig))
{
    // outConfig is valid -> the Contextual Anim scene is started for both actors
}

// Or validate a specific config directly:
bool bOk = MasterComp->CanPlayCombinedAnimWithActor(SomeConfig, TargetActor);

// Filter configs by tag (e.g. only finishers):
TArray<FCombinedAnimConfig> finishers;
MasterComp->GetContextualAnimsByTag(FGameplayTag::RequestGameplayTag("CombinedAnim.Finisher"), finishers);
```

### Eligibility check (slave)

```
// Called internally during selection; runs tag + condition checks:
bool bEligible = SlaveComp->CanStartCombinedAnimation(Config, MasterCharacter);

// Ambush helper:
bool bAmbush = SlaveComp->CanBeAmbushed(MasterPawn);
```

`CanStartCombinedAnimation` succeeds only when the slave's `AnimTags` contain `SlaveRequiredTags`, the relative direction/ambush angle matches, and every `UCASAnimCondition` in `AnimStartingConditions` returns true.

### Component state & events

| Member | Use |
|---|---|
| `GetIsPlayingContextualAnim()` | True while a scene is playing |
| `GetContextualAnimComponent()` | Access the underlying `UContextualAnimSceneActorComponent` |
| `OnJoinedScene` / `OnLeftScene` | `BlueprintNativeEvent`s — override for FX, movement lock, cleanup |
| `FOnCombinedAnimationStarted` / `FOnCombinedAnimationEnded` | Delegates carrying the `AnimTag` |
| `SetCanBeHitDuringCombinedAnims(bool)` | Toggle invulnerability mid-scene |

---

## 4 — Wire to Characters / Blueprints

1. **Initiator:** `UACFCombinedAnimMasterComponent` + DataAsset assigned. Trigger `TryGetBestCombinedAnimForActor` from an execution ability, finisher action, or input.
2. **Target:** `UACFCombinedAnimSlaveComponent` with `AnimTags` matching the configs' `SlaveRequiredTags`.
3. Hook the master's selection into your combat flow — e.g. when the target is low health / staggered, call `TryGetBestCombinedAnimForActor` and start the finisher.
4. Override `OnJoinedScene` / `OnLeftScene` on both components to disable movement, swap collision, or play FX, and to restore state afterwards.
5. For finishers, rely on `KillSlaveAfterAnim` in the config rather than manually killing the slave.

---

## 5 — Verify

**Checklist before testing:**

- [ ] Contextual Anim scene assets created/duplicated under `Content/YourGame/CombinedAnimations/`.
- [ ] `UACFCombinedAnimationsDataAsset` duplicated and assigned on the master component's `CombinedAnimations`.
- [ ] Each `FCombinedAnimConfig` has `AnimTag`, `CombinedAnimation`, and correct `SlaveRequiredTags`.
- [ ] Master character BP has `UACFCombinedAnimMasterComponent`.
- [ ] Target character BP has `UACFCombinedAnimSlaveComponent` with `AnimTags` covering `SlaveRequiredTags`.
- [ ] Distance/direction/ambush settings realistic (`MaxDistanceToStart`, `AmbushRequiredDegrees`).
- [ ] `bLockAbilityTriggersDuringCombinedAnims` / `bCanBeHitDuringCombinedAnims` set per character.

**Common failures:**

| Symptom | Fix |
|---|---|
| `TryGetBestCombinedAnimForActor` returns false | Slave's `AnimTags` don't contain the config's `SlaveRequiredTags`, or master too far (`MaxDistanceToStart`) |
| Anim never starts on the slave | Slave missing `UACFCombinedAnimSlaveComponent`, or a `UCASAnimCondition` rejects it |
| Actors don't line up / clip | Warp targets misconfigured in the `UContextualAnimSceneAsset` |
| Finisher doesn't kill target | `KillSlaveAfterAnim` not enabled on the config |
| Ambush triggers from the front | `AmbushExecution` off, or `AmbushRequiredDegrees` too wide |
| Character still takes/deals input mid-scene | Toggle `bLockAbilityTriggersDuringCombinedAnims` / `bCanBeHitDuringCombinedAnims` |
| Bindings break on World Partition streaming | Ensure components aren't destroyed mid-scene; cleanup happens in `EndPlay` |
