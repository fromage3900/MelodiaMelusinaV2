# Deterministic Weighted Random Selection for Chooser Actions

## Overview

This document explains the deterministic weighted random selection system for ACF's Chooser-based actions. This system enables **instant client-side prediction** with **zero network delay** while maintaining perfect synchronization between client and server.

## Table of Contents

- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [How It Works](#how-it-works)
- [Setup Guide](#setup-guide)
- [Implementation Details](#implementation-details)
- [Performance Benefits](#performance-benefits)
- [Troubleshooting](#troubleshooting)

---

## The Problem

### Combat Animation Jitter in Multiplayer

In networked games using Unreal's Gameplay Ability System (GAS), actions like dodges, attacks, and combos need to play animations. When these animations are selected dynamically (e.g., picking a random dodge from multiple options), we face a critical challenge:

**Scenario:**
1. Player presses dodge button
2. Client needs to know which dodge animation to play
3. Server also needs to know which dodge animation to play
4. **Client and server MUST play the SAME animation**

### Why It's Hard

**Problem 1: Non-Deterministic Selection**
- If client picks random dodge A (seed = system time)
- Server picks random dodge B (different system time)
- **Result:** Client sees dodge A, server sees dodge B → **desync/jitter**

**Problem 2: Chooser Table Complexity**
- Chooser tables support filters, nested choosers, and weighted randomization
- Evaluating filters requires context data (character state, targets, etc.)
- **Challenge:** How to get same filtered results on both client and server?

---

## The Solution

### Deterministic Weighted Random Using GAS Prediction Keys

**Core Concept:**

Use **GAS Prediction Keys** as synchronized random seeds:

```cpp
// GAS provides the same prediction key to both client and server
const int32 Seed = ActivationInfo.GetActivationPredictionKey().Current;

// Both client and server use the SAME seed
FRandomStream SyncedRNG(Seed);

// Both pick the SAME random value → SAME montage
float RandomValue = SyncedRNG.FRandRange(0.0f, TotalWeight);
```

### Key Insight: GAS Prediction Keys

**What are GAS Prediction Keys?**
- Unreal's GAS assigns a unique prediction key to each ability activation
- **Same prediction key is sent to both client and server**
- Increments with each activation (e.g., first dodge = seed 1, second = seed 2)
- Perfect for deterministic synchronization!

**Why This Works:**
```
Client: Dodge activated → Prediction Key = 42 → RNG seed = 42 → Picks montage A
Server: Dodge activated → Prediction Key = 42 → RNG seed = 42 → Picks montage A
Result: ✅ Perfect sync, ZERO network delay!
```

---

## How It Works

### Phase 1: Extract Weights from Chooser Table

Recursively traverse the entire chooser structure to build a complete weight map:

```cpp
TMap<UAnimMontage*, float> WeightMap;
UACFFunctionLibrary::BuildMontageWeightMapFromChooser(ChooserTable, WeightColumnIndex, WeightMap);

// Result:
// WeightMap = {
//   A_Dodge_Forward  → 2.0,  // 2x more likely
//   A_Dodge_Left     → 1.0,  // Normal chance
//   A_Dodge_Right    → 1.0,
//   A_Dodge_Back     → 0.5   // Half as likely
// }
```

The function:
1. Accesses internal chooser data (`ResultsStructs`)
2. Iterates through all rows
3. Handles nested choosers recursively
4. Extracts weights from Output Float column (`OutputFloatColumn.RowValues[RowIndex]`)

### Phase 2: Evaluate Chooser with Filters

Use `EvaluateChooserMulti` to get ALL montages that pass filter criteria:

```cpp
// Both client and server evaluate with same context
SetChooserParams(); // Set context data (movement direction, targets, etc.)

TArray<UObject*> Results = UChooserFunctionLibrary::EvaluateChooserMulti(
    this,           // Context object
    ChooserTable,   // Chooser to evaluate
    UAnimMontage::StaticClass()
);

// Results = [A_Dodge_Forward, A_Dodge_Left, A_Dodge_Right]
// (A_Dodge_Back filtered out because not moving backward)
```

**Important:** Override `SetChooserParams()` in Blueprint to set context data like movement direction, target distance, etc.

### Phase 3: Deterministic Weighted Selection

Apply weights to filtered montages and select using GAS prediction key:

```cpp
// Use GAS prediction key as random seed
const int32 Seed = ActivationInfo.GetActivationPredictionKey().Current;
FRandomStream SyncedRNG(Seed);

// Build cumulative weights (with anti-repeat penalty)
TArray<float> Weights = {2.0, 1.0, 1.0}; // From WeightMap
float TotalWeight = 4.0;

// Apply anti-repeat penalty to last selected montage
if (Montage == LastSelectedMontage) {
    Weight *= RepeatProbabilityMultiplier; // 0.5 by default
}

// Generate synchronized random value
float RandomValue = SyncedRNG.FRandRange(0.0f, TotalWeight);

// Select based on cumulative weights
// Random = 2.5 → Falls in range [2.0, 3.0] → Select A_Dodge_Left
```

**Both client and server:**
- Use same prediction key (seed)
- Evaluate same filters (same context)
- Have same weights
- Generate same random value
- Select same montage!

---

## Setup Guide

### 1. Create Chooser Table

1. Right-click in Content Browser → **Miscellaneous** → **Chooser Table**
2. Name it (e.g., `CT_DodgeAnimations`)
3. Set Result Type to `Animation Montage`

### 2. Configure Output Float Column

**Add weight column:**

1. Click **Add Column** → **Output Float**
2. **Bind to property:**
   - Select your action class (e.g., `ACFChooserAction`)
   - Choose `Randomize` property
3. **Position:** Column must be at index matching `WeightColumnIndex` (default: 0 = first column)

### 3. Add Montages and Weights

Add rows for each animation:

```
Row 0: A_Dodge_Forward   → Weight: 2.0  (2x more likely)
Row 1: A_Dodge_Left      → Weight: 1.0
Row 2: A_Dodge_Right     → Weight: 1.0
Row 3: A_Dodge_Back      → Weight: 0.5  (half as likely)
```

### 4. Optional: Add Filter Columns

**Example: Direction-based filtering:**

Add a **Float Difference** column:
- Bind to `CachedInputDirection` (if using `ACFDirectionalChooserAction`)
- Set target angles:
  - Forward: 0°
  - Right: 90°
  - Left: -90°
  - Back: 180°

**Example: Tag-based filtering:**

Add a **Gameplay Tag** column:
- Check for tags like `State.Grounded`, `State.InAir`
- Different animations for different states

### 5. Configure Action Properties

In your action ability:

```cpp
ChooserTable = CT_DodgeAnimations
WeightColumnIndex = 0  // First column
RepeatProbabilityMultiplier = 0.5  // 50% less likely to repeat same animation
```

That's it! The system handles everything automatically.

---

## Implementation Details

### Code Flow

**ACFChooserAction::ActivateAbility():**

```cpp
void UACFChooserAction::ActivateAbility(...)
{
    // 1. Set chooser params (context data)
    SetChooserParams();

    // 2. Build weight map from chooser (handles nested choosers)
    TMap<UAnimMontage*, float> WeightMap;
    BuildMontageWeightMapFromChooser(ChooserTable, WeightColumnIndex, WeightMap);

    // 3. Evaluate chooser with filters
    TArray<UObject*> Results = EvaluateChooserMulti(this, ChooserTable, UAnimMontage::StaticClass());

    // 4. Deterministic weighted random selection
    UAnimMontage* Selected = SelectMontageWithDeterministicWeightedRandom(
        FilteredMontages,
        WeightMap,
        ActivationInfo  // Contains GAS prediction key
    );

    // 5. Set montage and activate
    animMontage = Selected;
    Super::ActivateAbility(...);
}
```

### Anti-Repeat System

Prevents boring repetitive animations:

```cpp
// Apply penalty to previously selected montage
if (Montage == LastSelectedMontage) {
    Weight *= RepeatProbabilityMultiplier; // Default: 0.5
}

// Example:
// Normal weights:    [1.0, 1.0, 1.0, 1.0] → 25% each
// After selecting #2: [1.0, 1.0, 0.5, 1.0] → #2 now 14% instead of 25%
```

**Configure:** Set `RepeatProbabilityMultiplier`:
- `0.0` = Never repeat same animation twice
- `0.5` = 50% less likely to repeat (default)
- `1.0` = No penalty, can repeat freely

### Nested Choosers

The weight extraction handles nested choosers automatically:

```
CT_Dodge_Master
  → Row 0: CT_Dodge_Forward (nested chooser with 3 forward variations)
  → Row 1: CT_Dodge_Backward (nested chooser with 2 backward variations)
  → Row 2: A_Dodge_Left (direct montage)

BuildMontageWeightMapFromChooser recursively extracts all 6 montages with their weights.
```

---

## Performance Benefits

### Comparison

| Approach | Client Delay | Server Load | Sync Quality |
|----------|--------------|-------------|--------------|
| **Deterministic (Ours)** | **0ms** | Low (both evaluate) | Perfect |
| Server RPC | 50-150ms | Low (server only) | Perfect after delay |
| Client Prediction (broken) | 0ms | Low | Desyncs frequently |

### Metrics

**Deterministic Mode:**
- **Client response:** Instant (0ms)
- **Network traffic:** None (no RPC needed)
- **Synchronization:** Perfect (same seed → same result)
- **Overhead:** Minimal (one chooser evaluation per activation)

**Use Cases:**
- ✅ Fast-paced combat (dodges, attacks, combos)
- ✅ Responsive character movement
- ✅ Any action where instant feedback is critical
- ✅ Weighted random selection with filters

---

## Troubleshooting

### Animations Still Jitter

**Check:**
1. Verify `WeightColumnIndex` matches Output Float column position
2. Ensure Output Float column is bound to `Randomize` property
3. Confirm both client/server have same context data in `SetChooserParams()`

**Debug:**
- Add logs to see selected montages on client vs server
- Check GAS prediction keys match

### Always Selects Same Animation

**Possible Causes:**
1. Only one montage passes filters
2. All weights are 0.0
3. `RepeatProbabilityMultiplier = 1.0` with same seed

**Solutions:**
- Review filter logic (too restrictive?)
- Set weights > 0.0
- Lower `RepeatProbabilityMultiplier`

### "No montages found in chooser table"

**Causes:**
1. Chooser Table not assigned
2. Wrong `WeightColumnIndex`
3. Empty chooser table

**Solutions:**
- Assign `ChooserTable` property
- Verify column index matches Output Float column position
- Add montages to chooser table

### Properties Not Showing in Editor

**Fix:**
1. Close Unreal Editor
2. Delete `Intermediate` folder
3. Reopen editor (forces UHT regeneration)

---

## Advanced Topics

### Custom Context Properties

Override `SetChooserParams` to provide custom data:

**Blueprint:**
```
Event SetChooserParams
  → Calculate Custom Value
  → Set Float Context Param: "MyValue" = Value
```

**C++:**
```cpp
void UMyChooserAction::SetChooserParams_Implementation()
{
    Super::SetChooserParams_Implementation();

    float CustomValue = CalculateSomething();
    SetFloatContextParam(FName("MyValue"), CustomValue);
}
```

### Weight Calculation Algorithm

Cumulative probability distribution:

```
Weights: [5.0, 3.0, 2.0]
Total: 10.0
Cumulative: [5.0, 8.0, 10.0]

Random = 6.5 (from GAS seed)
  6.5 > 5.0? Yes → continue
  6.5 <= 8.0? Yes → Select index 1 (weight 3.0)
```

### Extending to Other Asset Types

The system works with any UObject:

```cpp
// For combo graphs
TMap<UACFComboGraph*, float> ComboWeightMap;
BuildAssetWeightMapFromChooser(ChooserTable, WeightColumnIndex, ComboWeightMap);

// For items, abilities, etc.
TMap<UMyAsset*, float> AssetWeightMap;
BuildAssetWeightMapFromChooser(ChooserTable, WeightColumnIndex, AssetWeightMap);
```

---

## References

- [Chooser Actions User Guide](chooser-actions-guide.md) - Step-by-step usage instructions
- [GAS Action Abilities Analysis](gas-action-abilities-analysis.md) - Full GAS integration details

---

**Document Version:** 2.0
**Last Updated:** 2025-10-05
**Author:** insodimension
