---
name: chooser-actions
description: How to configure and use ACF Chooser Actions to dynamically select animation montages and combo graphs via Unreal's Chooser system. Covers deterministic vs server-authority selection for multiplayer, weighted/filtered chooser tables, sustained (hold/release) chooser actions, and hit-reaction chooser actions. Use when setting up dynamic animation/combo selection, fixing multiplayer animation desync, configuring chooser tables, or working with ACFChooserAction / ACFChooserComboAttackAction.
globs: []
alwaysApply: false
---

# Chooser Actions Guide

## Overview

Chooser Actions allow you to dynamically select animations (montages) or combo graphs using Unreal Engine's Chooser system. This provides data-driven, context-aware selection with support for filters, weights, and nested choosers.

**Available Chooser Actions:**
- **ACFChooserAction** - Selects animation montages for dodges, attacks, idles, etc.
- **ACFChooserComboAttackAction** - Selects combo graphs for attack sequences

## Table of Contents

- [Basic Setup](#basic-setup)
- [Deterministic Mode (Recommended for Multiplayer)](#deterministic-mode-recommended-for-multiplayer)
- [Non-Deterministic Mode (Server Authority)](#non-deterministic-mode-server-authority)
- [Chooser Table Configuration](#chooser-table-configuration)
- [Common Use Cases](#common-use-cases)
- [Troubleshooting](#troubleshooting)

---

## Basic Setup

### 1. Create a Chooser Table

1. **Right-click in Content Browser** → **Miscellaneous** → **Chooser Table**
2. **Name it** (e.g., `CT_DodgeAnimations` or `CT_AttackCombos`)
3. **Open the Chooser Table**

### 2. Configure Result Type

In the Chooser Table editor:

1. **Set Result Type**:
   - For montages: `Animation Montage`
   - For combo graphs: `ACFComboGraph`

2. **Add rows** for each asset you want to select from

### 3. Add the Chooser Action

In your Action ability:

1. **Create or open an Action ability** (Blueprint or C++)
2. **Set the action class**:
   - For montages: `ACFChooserAction`
   - For combos: `ACFChooserComboAttackAction`

3. **Assign the Chooser Table** to the `ChooserTable` property

---

## Deterministic Mode (Recommended for Multiplayer)

**Use this mode for:**
- Zero network delay
- Instant client-side prediction
- Perfectly synchronized client/server selection
- Custom seed-based chooser evaluators

### Setup Steps

#### 1. Configure the Chooser Action

In your Action ability settings:

1. **Enable deterministic mode:**
   ```
   bUseDeterministicRandomization = true
   ```

2. **Set weight column index** (default 0):
   ```
   WeightColumnIndex = 0
   ```

3. **Configure anti-repeat** (optional, default 0.5):
   ```
   RepeatProbabilityMultiplier = 0.5
   ```
   - `0.0` = never repeat same animation twice in a row
   - `1.0` = no penalty for repeating
   - `0.5` = 50% less likely to repeat

#### 2. Configure the Chooser Table

**Add an Output Float Column:**

1. In the Chooser Table, click **Add Column** → **Output Float**
2. **Position it at the correct index** (must match `WeightColumnIndex`)
   - If `WeightColumnIndex = 0`, make it the **first column**
   - If `WeightColumnIndex = 1`, make it the **second column**

3. **Bind the column to the Randomize property:**
   - Click the column header
   - Set **Binding** → Select your action class
   - Choose the `Randomize` property

4. **Set weight values for each row:**
   ```
   Row 0: Dodge_Forward     → Weight: 1.0
   Row 1: Dodge_Backward    → Weight: 1.0
   Row 2: Dodge_Left        → Weight: 1.0
   Row 3: Dodge_Right       → Weight: 1.0
   Row 4: Dodge_Fancy_Flip  → Weight: 0.3  (rare/flashy animation)
   ```
   - Higher weight = more likely to be selected
   - Weights are relative (1.0, 1.0, 2.0 is same as 10, 10, 20)

#### 3. Add Filter Columns (Optional)

You can add filter columns to context-aware selection:

**Example: Distance-based selection**
```
Column 1: Output Float (Randomize weights)
Column 2: Float Range (Target Distance)
  - Dodge_Short: 0-300 units
  - Dodge_Long: 300+ units
```

**Example: Tag-based selection**
```
Column 1: Output Float (Randomize weights)
Column 2: Gameplay Tag (Character State)
  - Dodge_Grounded: Has tag "State.Grounded"
  - Dodge_Aerial: Has tag "State.InAir"
```

### How It Works

When deterministic mode is enabled:

1. **Both client and server** receive the same GAS prediction key
2. **Both** extract weights from the chooser table
3. **Both** evaluate filters using the same context data
4. **Both** use the prediction key as random seed
5. **Both** select the same montage/combo instantly
6. **Zero network delay** - animations play immediately

---

## Non-Deterministic Mode (Server Authority)

**Use this mode when:**
- Chooser uses server-only context data
- Using non-deterministic custom evaluators
- Single-player game (no multiplayer)

### Setup Steps

#### 1. Configure the Chooser Action

```
bUseDeterministicRandomization = false  (default)
```

#### 2. Configure the Chooser Table

- No special setup required
- Use any columns, filters, or evaluators you want
- Can use Unreal's built-in Randomize column

### How It Works

When deterministic mode is disabled:

1. **Server** evaluates the chooser and picks the montage/combo
2. **Server** sends the choice to the client via RPC
3. **Client** waits 50-150ms for the RPC to arrive
4. **Client** plays the animation/combo

**Trade-off:** 50-150ms network delay, but guaranteed correctness even with server-only data.

---

## Chooser Table Configuration

### Column Types

#### Output Float (for Weights)
- **Purpose:** Assign selection weights to each row
- **Binding:** Must bind to the action's `Randomize` property
- **Values:** Relative weights (higher = more likely)
- **Required for:** Deterministic mode

#### Asset Chooser
- **Purpose:** Direct asset reference (montage, combo graph)
- **Most common result type**

#### Nested Chooser
- **Purpose:** Reference another chooser table
- **Use case:** Organize complex selection logic into sub-choosers
- **Example:**
  ```
  CT_Dodge_Master
    → Row 0: CT_Dodge_Forward (nested chooser)
    → Row 1: CT_Dodge_Backward (nested chooser)
    → Row 2: CT_Dodge_Side (nested chooser)
  ```

#### Filter Columns

**Gameplay Tag**
- Filter by actor's gameplay tags
- Example: Only select aerial dodges if character has "State.InAir" tag

**Float Range**
- Filter by numeric context values
- Example: Select different attacks based on distance to target

**Bool**
- Simple true/false conditions
- Example: Only select combo if character has enough stamina

**Enum**
- Filter by enum values
- Example: Select animations based on weapon type

---

## Common Use Cases

### 1. Basic Random Dodge Selection

**Chooser Table: `CT_DodgeAnimations`**
```
Output Float (Randomize)  |  Asset
--------------------------|------------------
1.0                       |  AM_Dodge_Forward
1.0                       |  AM_Dodge_Backward
1.0                       |  AM_Dodge_Left
1.0                       |  AM_Dodge_Right
```

**Action Setup:**
```
ChooserTable = CT_DodgeAnimations
bUseDeterministicRandomization = true
WeightColumnIndex = 0
RepeatProbabilityMultiplier = 0.5
```

### 2. Weighted Combo Selection (Rare Finishers)

**Chooser Table: `CT_SwordCombos`**
```
Output Float (Randomize)  |  Asset
--------------------------|------------------
5.0                       |  CG_Combo_Basic_1
5.0                       |  CG_Combo_Basic_2
5.0                       |  CG_Combo_Basic_3
1.0                       |  CG_Combo_Flashy_Finisher (rare)
0.2                       |  CG_Combo_Ultimate (very rare)
```

**Action Setup:**
```
ChooserTable = CT_SwordCombos
bUseDeterministicRandomization = true
WeightColumnIndex = 0
RepeatProbabilityMultiplier = 0.0  (never repeat same combo)
```

### 3. Context-Aware Selection (Distance-Based)

**Chooser Table: `CT_AttacksByDistance`**
```
Output Float  |  Float Range (Target Distance)  |  Asset
--------------|----------------------------------|------------------
1.0           |  0-200                           |  AM_Attack_Close_1
1.0           |  0-200                           |  AM_Attack_Close_2
1.0           |  200-500                         |  AM_Attack_Medium_1
1.0           |  200-500                         |  AM_Attack_Medium_2
1.0           |  500-1000                        |  AM_Attack_Lunge
```

**Action Setup:**
```
ChooserTable = CT_AttacksByDistance
bUseDeterministicRandomization = true
WeightColumnIndex = 0
```

**Blueprint: Override `SetChooserParams`**
```cpp
// Provide context data for chooser evaluation
SetFloatContextParam("TargetDistance", DistanceToTarget);
```

### 4. Nested Choosers (Complex Logic)

**Master Chooser: `CT_Combat_Master`**
```
Gameplay Tag (Weapon Type)  |  Nested Chooser
----------------------------|------------------
Weapon.Sword                |  CT_SwordAttacks
Weapon.Axe                  |  CT_AxeAttacks
Weapon.Spear                |  CT_SpearAttacks
```

**Sub-Chooser: `CT_SwordAttacks`**
```
Output Float  |  Float Range (Stamina)  |  Asset
--------------|-------------------------|------------------
1.0           |  50-100                 |  AM_SwordHeavy
1.0           |  20-100                 |  AM_SwordLight
1.0           |  0-100                  |  AM_SwordQuick
```

---

## Troubleshooting

### Animation Jitters/Desyncs in Multiplayer

**Symptom:** Client and server play different animations

**Solutions:**
1. ✅ Enable `bUseDeterministicRandomization = true`
2. ✅ Verify `WeightColumnIndex` matches the Output Float column position
3. ✅ Ensure Output Float column is bound to `Randomize` property
4. ✅ Check that both client/server have same context data (for filters)

### Always Selects Same Animation

**Symptom:** Same animation plays every time, no variety

**Possible Causes:**
1. **Total weight is zero** → Check that weight values are > 0
2. **Only one row passes filters** → Review filter column conditions
3. **RepeatProbabilityMultiplier = 1.0** → Animation can repeat freely
4. **All weights equal 0.0** → Falls back to first montage

**Solutions:**
1. ✅ Set weights > 0.0 for all rows
2. ✅ Review filter logic (too restrictive?)
3. ✅ Lower `RepeatProbabilityMultiplier` to reduce repeats
4. ✅ Check logs for "Total weight is zero" warnings

### Properties Not Showing in Editor

**Symptom:** `bUseDeterministicRandomization` or `Randomize` not visible

**Solutions:**
1. ✅ Close Unreal Editor
2. ✅ Delete `Intermediate` folder
3. ✅ Reopen editor (forces UHT regeneration)
4. ✅ Verify code compiled successfully

### "No montages found in chooser table" Warning

**Symptom:** Warning in logs, no animation plays

**Possible Causes:**
1. **Chooser Table is null** → Assign a chooser table
2. **Wrong WeightColumnIndex** → Column doesn't exist at that index
3. **Empty chooser table** → Add rows with assets
4. **Wrong result type** → Chooser returns wrong asset type

**Solutions:**
1. ✅ Assign `ChooserTable` property
2. ✅ Verify `WeightColumnIndex` matches column position
3. ✅ Add rows to chooser table
4. ✅ Set correct result type (AnimMontage or ACFComboGraph)

### "No valid montages passed filters" Warning

**Symptom:** Chooser has montages, but none selected

**Cause:** All rows failed filter evaluation

**Solutions:**
1. ✅ Review filter column conditions
2. ✅ Check context data values (via SetChooserParams)
3. ✅ Add debug logging to see which filters are failing
4. ✅ Temporarily remove filters to verify weights work

### Client Waits 50-150ms Before Animation

**Symptom:** Noticeable delay before character reacts

**Cause:** Using non-deterministic mode (server RPC)

**Solution:**
✅ Enable `bUseDeterministicRandomization = true` for instant client response

---

## Advanced Topics

### Custom Context Properties

Override `SetChooserParams` to provide custom data to chooser filters:

**Blueprint:**
```
Event SetChooserParams
  → Get Target Actor
  → Calculate Distance
  → Set Float Context Param: "TargetDistance" = Distance
  → Set Bool Context Param: "HasLineOfSight" = Trace Result
```

**C++:**
```cpp
void UMyChooserAction::SetChooserParams_Implementation()
{
    Super::SetChooserParams_Implementation();

    // Provide custom context data
    float Distance = CalculateDistanceToTarget();
    SetFloatContextParam(FName("TargetDistance"), Distance);

    bool bHasLOS = CheckLineOfSight();
    SetBoolContextParam(FName("HasLineOfSight"), bHasLOS);
}
```

### Weight Calculation

Weights use cumulative probability distribution:

**Example:** Weights [5.0, 3.0, 2.0]
- Total weight: 10.0
- Cumulative: [5.0, 8.0, 10.0]
- Random value: 6.5 (from GAS prediction seed)
- Selection logic:
  - 6.5 > 5.0? Yes → continue
  - 6.5 <= 8.0? Yes → **Select index 1** (weight 3.0)

### Anti-Repeat System

Reduces probability of repeating the same animation:

**Example:** RepeatProbabilityMultiplier = 0.5
- Last selected: Dodge_Forward (weight 1.0)
- Next evaluation:
  - Dodge_Forward: 1.0 * 0.5 = **0.5** (penalized)
  - Dodge_Backward: 1.0 (normal)
  - Dodge_Left: 1.0 (normal)
  - Dodge_Right: 1.0 (normal)
- Dodge_Forward now 50% less likely to be selected

---

## References

For technical details on the deterministic system implementation:
- [Deterministic Chooser Selection](deterministic-chooser-selection.md)
- [GAS Action Abilities Analysis](gas-action-abilities-analysis.md)

---

**Document Version:** 1.0
**Last Updated:** 2025-10-05
**Author:** insodimension

---

## Supporting Reference Files (this skill folder)

- `deterministic-chooser-selection.md` — deep dive on the deterministic weighted
  random selection system (GAS prediction key, zero network delay, sync details).
- `sustained-chooser-actions.md` — hold/release (charged) chooser actions, e.g.
  archery; combines chooser selection with sustained action mechanics.
- `hit-reaction-chooser-action.md` — `UACFHitReactionChooserAction`: hit-zone /
  damage-type / direction / death-state based reaction animation selection.
