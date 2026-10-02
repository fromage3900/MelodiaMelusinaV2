---
name: executions-system
description: Set up finisher/execution moves with the ACF Executions System module (executor component, combined animations, and execution conditions that gate finishers on target state like low health or stun).
globs: []
alwaysApply: false
---

# Executions System — ACF Ultimate

The **Executions System** module (`ExecutionsSystem`) implements synchronized finisher / execution moves between an attacker and a victim. The attacker carries a `UACFExecutorComponent` (a subclass of `UCASAnimMasterComponent`, the combined-animation master) that, given a valid target, picks the best execution based on the **relative direction** to the target and the attacker's current **moveset action**, then plays a paired ("combined") animation on both characters. Whether an execution is even allowed is decided by `UACFExecutionCondition` (e.g. target health below a threshold, plus a random chance), and the active condition set can be data-driven per character via `UACFExecutionConditionsFragment`. Executions are server-authoritative and replicated.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Sample combined-anim set | `FCombinedAnimConfig` data (on `CASAnimMaster`) | `/AscentCombatFramework/.../Executions/` | The paired attacker/victim animations |
| Sample execution condition | `UACFExecutionCondition` (subclass of `UCASAnimCondition`) | Authored inline | Gates when a finisher is allowed |
| Sample conditions fragment | `UACFExecutionConditionsFragment` | On `UACFCharacterDataAsset.Fragments` | Data-driven condition set per character |

> **Never edit sample assets.** Duplicate sample execution animations, conditions, and data assets into `Content/YourGame/Executions/` and customize your copies — sample assets are overwritten on plugin/sample updates.

### Key classes & structs

| Class / Struct | Role |
|---|---|
| `UACFExecutorComponent` | Attacker component (extends `UCASAnimMasterComponent`). `TryExecuteCharacter`, `TryExecuteCurrentTarget`; holds the executions table by direction + moveset action |
| `FExecution` | One execution entry: `AnimationTag`, `CameraEvent`, `bIsFatal`, `bCanBeHitDuringAnim`, `Weight` |
| `FExecutionArray` | Array of `FExecution` (the candidates for one moveset action) |
| `FExecutions` | `TMap<FGameplayTag /*moveset action*/, FExecutionArray>` |
| `ERelativeDirection` | Direction of the target relative to the attacker (front/back/side) used to pick the right finisher |
| `UACFExecutionCondition` | Condition (extends `UCASAnimCondition`): `RemainingHealthPercentage`, `ExecutionChance` |
| `UACFExecutionConditionsFragment` | Character fragment that replaces the slave component's `AnimStartingConditions` at init |

---

## 2 — Setup / Configuration

### A. Add the executor to the attacker

1. Add a `UACFExecutorComponent` to your attacker character (it is a `BlueprintSpawnableComponent`). It inherits the combined-animation master behavior from `UCASAnimMasterComponent`.
2. Populate **`ExecutionsByDirectionAndMovesetAction`** — a `TMap<ERelativeDirection, FExecutions>`:
   - Key: the relative direction to the target (e.g. front vs. back finishers).
   - Value: an `FExecutions` mapping each **moveset action tag** → an `FExecutionArray` of candidate `FExecution`s.
3. For each `FExecution` entry set:
   - **`AnimationTag`** — the combined-animation tag (resolves the paired attacker/victim montage on the anim-master).
   - **`CameraEvent`** — optional camera shake/sequence event name fired during the execution.
   - **`bIsFatal`** — whether the execution kills the target.
   - **`bCanBeHitDuringAnim`** — whether the attacker can be interrupted/damaged mid-execution.
   - **`Weight`** — relative chance of being chosen among candidates.

### B. Author the gating conditions

1. The "can I execute this target" gate comes from `UCASAnimCondition`s on the target's combined-anim slave component (`AnimStartingConditions`).
2. Create a `UACFExecutionCondition` and set:
   - **`RemainingHealthPercentage`** — the execution is only allowed when the target's health is at/below this percentage (default 15%). Use this for "finish low-health enemies", and pair with stun/CC tags via additional conditions.
   - **`ExecutionChance`** — percent chance the execution actually triggers (default 75%).
3. To drive conditions from data per character, add a `UACFExecutionConditionsFragment` to the character's `UACFCharacterDataAsset.Fragments` and author its `Conditions` array there. At initialization the fragment **replaces** whatever conditions were on the slave component (safe to re-apply at runtime to hot-swap on phase change).

---

## 3 — Core Workflow / Runtime API

### Triggering an execution

```
// Try to execute a specific target (server-authoritative).
// Returns false if no valid execution (conditions failed, no entry for direction/moveset, etc.)
bool bOk = ExecutorComp->TryExecuteCharacter(TargetCharacter);

// Try to execute whatever the attacker is currently targeting:
bool bOk2 = ExecutorComp->TryExecuteCurrentTarget();
```

### Selection logic (what happens internally)

1. The component computes the `ERelativeDirection` of the target relative to the attacker.
2. It looks up `ExecutionsByDirectionAndMovesetAction[direction]`, then the `FExecutionArray` for the attacker's current **moveset action tag**.
3. It evaluates the target's `UACFExecutionCondition`(s): the target's `RemainingHealthPercentage` gate must pass and the `ExecutionChance` roll must succeed.
4. Among valid candidates it picks one by **`Weight`** (higher = more likely) and stores it as `currentBestExec` (replicated).
5. The combined animation (`AnimationTag`) plays on both attacker and victim; `CameraEvent` fires; both characters' actions are locked for the duration (the victim's `bCanBeHitDuringAnim` controls vulnerability).
6. `OnCombinedAnimStarted` / `OnCombinedAnimEnded` fire for hookable logic (apply fatal damage on end if `bIsFatal`, cleanup, etc.).

### Hooking start/end

`UACFExecutorComponent` overrides `OnCombinedAnimStarted(animTag)` and `OnCombinedAnimEnded(animTag)` from the anim-master base — use a Blueprint/C++ subclass to react (VFX, scoring, applying the fatal blow).

---

## 4 — Wire to Characters / Blueprints

1. Add `UACFExecutorComponent` to attacker characters (players and/or executing AI).
2. Fill `ExecutionsByDirectionAndMovesetAction` with directional, moveset-keyed `FExecution` entries that reference your duplicated combined animations.
3. Ensure potential **victims** have the combined-anim slave setup (via `UCASAnimMasterComponent`/slave) and the gating `UACFExecutionCondition`s — ideally applied through `UACFExecutionConditionsFragment` on their `UACFCharacterDataAsset`.
4. Trigger executions from gameplay:
   - **Player:** bind a "finisher" input that calls `ExecutorComp->TryExecuteCurrentTarget()` (typically when the target is stunned/low health and in range).
   - **AI:** call `TryExecuteCharacter(target)` from a behavior-tree task or AI controller when conditions are met.
5. Connect the `CameraEvent` to your camera shake/sequence system, and apply the killing blow on `OnCombinedAnimEnded` when `bIsFatal`.
6. For phase-based bosses, re-apply a different `UACFExecutionConditionsFragment` at runtime to swap which executions are allowed.

---

## 5 — Verify

**Checklist before testing:**

- [ ] Execution animations, conditions, and data assets are duplicated into your content (samples untouched).
- [ ] `UACFExecutorComponent` is on the attacker.
- [ ] `ExecutionsByDirectionAndMovesetAction` has entries for the directions and moveset action tags you use.
- [ ] Each `FExecution` has a valid `AnimationTag` and sensible `Weight`, `bIsFatal`, `bCanBeHitDuringAnim`.
- [ ] Victims have combined-anim slave support and gating `UACFExecutionCondition`s.
- [ ] `RemainingHealthPercentage` / `ExecutionChance` are tuned for your "executable" window.
- [ ] Conditions applied via `UACFExecutionConditionsFragment` on the victim's `UACFCharacterDataAsset` (recommended).
- [ ] A trigger path exists: player input → `TryExecuteCurrentTarget`, or AI → `TryExecuteCharacter`.

**Common failures:**

| Symptom | Fix |
|---|---|
| `TryExecute...` always returns false | No entry for the current direction/moveset, or the target's conditions fail |
| Execution never allowed | Target health above `RemainingHealthPercentage`, or `ExecutionChance` roll keeps failing |
| Always the same finisher | Vary `Weight` across candidates; check only one entry exists for that direction/moveset |
| Wrong-direction finisher plays | Relative direction key mismatch — verify the `ERelativeDirection` buckets in the map |
| Animations not synced on victim | Victim missing the combined-anim slave (`UCASAnimMasterComponent`) setup |
| Attacker interrupted mid-execution | Set `bCanBeHitDuringAnim = false` on the relevant `FExecution` |
| Target survives a finisher | Set `bIsFatal = true` and apply the killing blow on `OnCombinedAnimEnded` |
| No camera effect | `CameraEvent` empty or not wired to the camera system |
| Conditions don't update on phase change | Re-apply the `UACFExecutionConditionsFragment` to hot-swap the condition set |
| Execution desyncs in multiplayer | Trigger through the server-authoritative `TryExecute...` path; `currentBestExec` is replicated |
