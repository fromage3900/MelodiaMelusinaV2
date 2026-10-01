# Hit Reaction Chooser Action

## Overview

`UACFHitReactionChooserAction` is a specialized chooser action that selects hit reaction animations based on:
- **Hit zone** (Head, Chest, Torso, Arms, Legs, Pelvis)
- **Damage type tags** (Melee.Slash, Ranged.Pierce, etc.)
- **Hit direction** (8-way: Front, Back, Left, Right, and diagonals)
- **Death state** (alive vs dead for death animations)

The action automatically maps hit bones to logical body zones using hierarchy traversal and provides out-of-the-box support for UE5 Mannequin/MetaHuman skeletons.

---

## Table of Contents

- [Key Features](#key-features)
- [Default Zone Mappings](#default-zone-mappings)
- [Setup Guide](#setup-guide)
- [Chooser Parameters](#chooser-parameters)
- [Motion Warping](#motion-warping)
- [Blueprint Customization](#blueprint-customization)
- [Example Configurations](#example-configurations)
- [Troubleshooting](#troubleshooting)

---

## Key Features

### Automatic Bone-to-Zone Mapping
- Maps individual bones to logical hit zones (e.g., `spine_03` → `Hit.Zone.Chest`)
- **Hierarchy traversal**: Mapping a parent bone automatically includes all children
  - Example: Mapping `hand_l` includes all finger bones
- **O(1) lookup** via cached TMap for performance
- **First zone wins**: If bone appears in multiple zones, first mapping takes precedence

### 8-Way Hit Direction Detection
- Calculates direction **from victim's perspective toward attacker**
- Uses dot product with victim's forward/right vectors
- Directions: Front, FrontRight, Right, BackRight, Back, BackLeft, Left, FrontLeft

### Default Skeleton Support
- Provides 8 default zone mappings for UE5 Mannequin/MetaHuman skeletons
- Works out-of-box without manual configuration
- Fully Blueprint-overridable per character

### Motion Warping Integration
- Automatically warps character away from attacker based on damage force
- Configurable warp distance (base + force multiplier)
- Optional rotation to face attacker
- Disables movement on death

---

## Default Zone Mappings

The action provides these default mappings in the constructor:

| Zone Tag | Root Bones | Coverage |
|----------|-----------|----------|
| `Hit.Zone.Head` | `head`, `neck_01`, `neck_02` | Entire head, neck, face |
| `Hit.Zone.Chest` | `spine_03`, `spine_04`, `spine_05`, `clavicle_l`, `clavicle_r` | Upper torso, shoulders |
| `Hit.Zone.Torso` | `spine_01`, `spine_02` | Mid/lower torso |
| `Hit.Zone.LeftArm` | `upperarm_l`, `lowerarm_l`, `hand_l` | Left arm, shoulder to fingertips |
| `Hit.Zone.RightArm` | `upperarm_r`, `lowerarm_r`, `hand_r` | Right arm, shoulder to fingertips |
| `Hit.Zone.LeftLeg` | `thigh_l`, `calf_l`, `foot_l` | Left leg, hip to toes |
| `Hit.Zone.RightLeg` | `thigh_r`, `calf_r`, `foot_r` | Right leg, hip to toes |
| `Hit.Zone.Pelvis` | `pelvis` | Lower torso, hips |

**Note:** Only root bones need to be specified - child bones are automatically included via hierarchy traversal.

---

## Setup Guide

### 1. Create Hit Reaction Chooser Table

1. **Right-click in Content Browser** → **Miscellaneous** → **Chooser Table**
2. **Name it**: `CHT_HitReactions`
3. **Set Result Type**: `Animation Montage`

### 2. Add Chooser Columns

Add these columns for comprehensive filtering:

#### Column 0: Output Float (Weights)
- **Type**: Output Float
- **Binding**: `Randomize` property from `ACFHitReactionChooserAction`
- **Purpose**: Weighted random selection with deterministic sync

#### Column 1: Gameplay Tag (Hit Zone)
- **Type**: Gameplay Tag
- **Binding**: `HitZone` property
- **Match Type**: `Has Tag`
- **Purpose**: Filter by body part hit

#### Column 2: Gameplay Tag (Damage Type)
- **Type**: Gameplay Tag
- **Binding**: `DamageTypeTags` property
- **Match Type**: `Has Tag`
- **Purpose**: Filter by damage type (melee, ranged, elemental)

#### Column 3: Enum (Direction)
- **Type**: Enum
- **Binding**: `DamageDirection` property
- **Enum**: `EACFDirection`
- **Purpose**: Filter by hit direction

#### Column 4: Bool (Is Dead)
- **Type**: Bool
- **Binding**: `bIsDead` property
- **Purpose**: Select death animations when character dies

### 3. Add Animation Rows

Example configuration:

| Weight | Hit Zone | Damage Type | Direction | Is Dead | Montage |
|--------|----------|-------------|-----------|---------|---------|
| 1.0 | Hit.Zone.Head | Damage.Type.Melee.Slash | Front | false | AM_HitReact_Head_Front |
| 1.0 | Hit.Zone.Head | Damage.Type.Melee.Slash | Back | false | AM_HitReact_Head_Back |
| 1.0 | Hit.Zone.Torso | Damage.Type.Melee.Slash | Front | false | AM_HitReact_Torso_Front |
| 1.0 | Hit.Zone.Torso | Damage.Type.Ranged.Pierce | Front | false | AM_HitReact_Arrow_Front |
| 1.0 | Hit.Zone.Head | ANY | ANY | true | AM_Death_Headshot |
| 1.0 | Hit.Zone.Torso | ANY | Front | true | AM_Death_Torso_Front |

### 4. Create Action Blueprint

1. **Create Blueprint** inheriting from `ACFHitReactionChooserAction`
2. **Assign chooser table**: Set `ChooserTable` = `CHT_HitReactions`
3. **Configure deterministic mode**:
   - `bUseDeterministicRandomization` = `true`
   - `WeightColumnIndex` = `0`
   - `RepeatProbabilityMultiplier` = `0.5` (avoid repeating same reaction)

### 5. Configure Gameplay Tags

Add these tags to your `DefaultGameplayTags.ini`:

```ini
+GameplayTagList=(Tag="Hit.Zone.Head",DevComment="Head zone")
+GameplayTagList=(Tag="Hit.Zone.Chest",DevComment="Chest zone")
+GameplayTagList=(Tag="Hit.Zone.Torso",DevComment="Torso zone")
+GameplayTagList=(Tag="Hit.Zone.LeftArm",DevComment="Left arm zone")
+GameplayTagList=(Tag="Hit.Zone.RightArm",DevComment="Right arm zone")
+GameplayTagList=(Tag="Hit.Zone.LeftLeg",DevComment="Left leg zone")
+GameplayTagList=(Tag="Hit.Zone.RightLeg",DevComment="Right leg zone")
+GameplayTagList=(Tag="Hit.Zone.Pelvis",DevComment="Pelvis zone")

+GameplayTagList=(Tag="Damage.Type.Melee.Slash",DevComment="Melee slash damage")
+GameplayTagList=(Tag="Damage.Type.Melee.Pierce",DevComment="Melee pierce damage")
+GameplayTagList=(Tag="Damage.Type.Ranged.Pierce",DevComment="Ranged pierce damage")
```

### 6. Configure Damage Types

In your damage type Blueprints (inheriting from `UACFDamageType`):

1. **Melee Sword**: Set `DamageTags` = `Damage.Type.Melee.Slash`
2. **Melee Spear**: Set `DamageTags` = `Damage.Type.Melee.Pierce`
3. **Arrow**: Set `DamageTags` = `Damage.Type.Ranged.Pierce`

---

## Chooser Parameters

The action automatically sets these parameters for chooser evaluation:

### HitZone (FGameplayTagContainer)
- **Source**: Mapped from `FACFDamageEvent.hitResult.BoneName`
- **Mapping**: Uses bone-to-zone cache built from `BoneToZoneMappings`
- **Example**: Hit on `spine_03` → `Hit.Zone.Chest`

### DamageTypeTags (FGameplayTagContainer)
- **Source**: `FACFDamageEvent.DamageTags`
- **Configured in**: Damage type Blueprint's `DamageTags` property
- **Example**: `Damage.Type.Melee.Slash`

### DamageDirection (EACFDirection)
- **Calculation**: 8-way direction from victim toward attacker
- **Algorithm**:
  ```cpp
  // Get direction TO attacker (negated relative vector)
  FVector ToAttacker = -(Receiver.Location - Dealer.Location).Normalized();

  // Dot product with victim's forward/right
  float ForwardDot = DotProduct(Victim.Forward, ToAttacker);
  float RightDot = DotProduct(Victim.Right, ToAttacker);

  // 8-way detection (22.5° thresholds)
  if (ForwardDot >= 0.924) return Front;
  else if (ForwardDot >= 0.383 && RightDot >= 0.383) return FrontRight;
  // ... etc
  ```
- **Values**: Front, FrontRight, Right, BackRight, Back, BackLeft, Left, FrontLeft

### bIsDead (bool)
- **Source**: `AACFCharacter::GetIsDead()`
- **Purpose**: Select death animations when character dies
- **Usage**: Filter death animations with `bIsDead = true`

---

## Motion Warping

The action provides automatic motion warping to move characters away from attackers:

### Configuration

```cpp
// Base distance to warp (units)
BaseWarpDistance = 100.0f

// Maximum warp distance (clamped)
MaxWarpDistance = 500.0f

// Multiplier for damage-based distance
ForceDistanceMultiplier = 0.1f

// Use damage impulse instead of damage amount
bUseDamageImpulse = false

// Rotate to face attacker during reaction
bShouldFaceAttacker = true
```

### Warp Calculation

```cpp
// Start with base distance
float WarpDist = BaseWarpDistance;

// Add force-based distance
if (bUseDamageImpulse)
    WarpDist += DamageType.DamageImpulse * ForceDistanceMultiplier;
else
    WarpDist += DamageEvent.FinalDamage * ForceDistanceMultiplier;

// Clamp to max
WarpDist = min(WarpDist, MaxWarpDistance);

// Move away from attacker
FVector Direction = (Receiver - Dealer).Normalized();
FVector WarpLocation = Character.Location + Direction * WarpDist;
```

### Rotation

If `bShouldFaceAttacker = true`:
- Character rotates to look at attacker during reaction
- Pitch and roll zeroed out (only yaw rotation)

### Death Handling

When `IsDeathHit()` returns true:
- Motion warp executes normally
- **After warp completes**: `OnActionEnded` disables character movement
- Character remains in death pose at warped location

---

## Blueprint Customization

### Override IsDeathHit

Customize death detection logic:

**Blueprint:**
```
Event IsDeathHit (Return: Bool)
  → Get Character Health
  → Return (Health <= 0)
```

**C++:**
```cpp
bool UMyHitReactionAction::IsDeathHit_Implementation() const
{
    AACFCharacter* Character = Cast<AACFCharacter>(GetCharacterOwner());
    return Character && Character->GetCurrentHealth() <= 0.0f;
}
```

### Override SetChooserParams

Add custom chooser parameters:

**Blueprint:**
```
Event SetChooserParams
  → Parent: SetChooserParams
  → Calculate Custom Value
  → Set Float Context Param: "MyValue" = Value
```

**C++:**
```cpp
void UMyHitReactionAction::SetChooserParams_Implementation()
{
    Super::SetChooserParams_Implementation();

    // Add custom chooser parameters
    float CustomValue = CalculateSomething();
    SetFloatContextParam(FName("MyCustomValue"), CustomValue);
}
```

### Custom Bone-to-Zone Mappings

Override default mappings for custom skeletons:

**Blueprint:**
```
Event Construct
  → Clear BoneToZoneMappings
  → Add Custom Mapping (Zone: "Hit.Zone.CustomZone", Bones: ["custom_bone_1", "custom_bone_2"])
```

**C++:**
```cpp
UMyHitReactionAction::UMyHitReactionAction()
{
    // Clear defaults
    BoneToZoneMappings.Empty();

    // Add custom mappings
    FHitZoneBoneMapping CustomZone;
    CustomZone.ZoneTag = FGameplayTag::RequestGameplayTag(FName("Hit.Zone.CustomZone"), false);
    CustomZone.BoneNames = { TEXT("custom_bone_1"), TEXT("custom_bone_2") };
    BoneToZoneMappings.Add(CustomZone);
}
```

---

## Example Configurations

### Example 1: Basic Hit Reactions

Simple setup with directional reactions per zone:

**Chooser Table:**
```
Weight | Zone          | Direction | Montage
-------|---------------|-----------|------------------
1.0    | Hit.Zone.Head | Front     | AM_HitHead_Front
1.0    | Hit.Zone.Head | Back      | AM_HitHead_Back
1.0    | Hit.Zone.Torso| Front     | AM_HitTorso_Front
1.0    | Hit.Zone.Torso| Back      | AM_HitTorso_Back
1.0    | Hit.Zone.Arms | Any       | AM_HitArms
1.0    | Hit.Zone.Legs | Any       | AM_HitLegs
```

### Example 2: Damage Type Specific

Different reactions for melee vs ranged:

**Chooser Table:**
```
Weight | Zone          | Damage Type              | Direction | Montage
-------|---------------|--------------------------|-----------|------------------
1.0    | Hit.Zone.Torso| Damage.Type.Melee.Slash  | Front     | AM_Slash_Front
1.0    | Hit.Zone.Torso| Damage.Type.Melee.Pierce | Front     | AM_Pierce_Front
1.0    | Hit.Zone.Torso| Damage.Type.Ranged.Pierce| Front     | AM_Arrow_Front
1.0    | Hit.Zone.Head | Damage.Type.Ranged.Pierce| Any       | AM_Arrow_Head
```

### Example 3: With Death Animations

Include death animations when `bIsDead = true`:

**Chooser Table:**
```
Weight | Zone          | Direction | IsDead | Montage
-------|---------------|-----------|--------|------------------
1.0    | Hit.Zone.Head | Any       | false  | AM_HitHead
1.0    | Hit.Zone.Torso| Front     | false  | AM_HitTorso_Front
1.0    | Hit.Zone.Torso| Back      | false  | AM_HitTorso_Back
1.0    | Hit.Zone.Head | Any       | true   | AM_Death_Headshot
1.0    | Hit.Zone.Torso| Front     | true   | AM_Death_Front
1.0    | Hit.Zone.Torso| Back      | true   | AM_Death_Back
0.2    | Any           | Any       | true   | AM_Death_Dramatic (rare)
```

### Example 4: Weighted Variety

Multiple animations per zone with varying weights:

**Chooser Table:**
```
Weight | Zone          | Direction | Montage
-------|---------------|-----------|------------------
3.0    | Hit.Zone.Torso| Front     | AM_HitTorso_Front_1 (common)
3.0    | Hit.Zone.Torso| Front     | AM_HitTorso_Front_2 (common)
1.0    | Hit.Zone.Torso| Front     | AM_HitTorso_Front_Stagger (rare)
0.2    | Hit.Zone.Torso| Front     | AM_HitTorso_Front_Epic (very rare)
```

---

## Troubleshooting

### Hit Direction Shows Backwards

**Symptom:** Hit from front, but chooser shows "Back" direction

**Cause:** Direction calculation was inverted (fixed in recent commits)

**Solution:** Update to latest code - direction now correctly calculates as `-(Receiver - Dealer)`

### DamageTags is Empty

**Symptom:** Debug log shows `DamageTags is EMPTY`

**Possible Causes:**
1. Damage type doesn't inherit from `UACFDamageType`
2. `DamageTags` property not set in damage type Blueprint

**Solutions:**
1. ✅ Use `UACFDamageType` as damage type base class
2. ✅ Set `DamageTags` property in damage type Blueprint
3. ✅ Check logs: `"ACFHitReactionChooserAction: DamageTags is EMPTY"`

### Wrong Zone Detected

**Symptom:** Hit on chest, but shows as Torso (or vice versa)

**Cause:** Bone appears in multiple zone mappings - first one wins

**Solutions:**
1. ✅ Check `BoneToZoneMappings` order - reorder zones if needed
2. ✅ Review bone names - verify hit bone matches expected zone
3. ✅ Check logs: `"ACFHitReactionChooserAction: HitBoneName = spine_03"`

### No Animation Plays

**Symptom:** Character gets hit, no reaction animation

**Possible Causes:**
1. No rows match all filter conditions
2. Chooser table not assigned
3. Wrong column bindings

**Solutions:**
1. ✅ Add fallback row with minimal filters (e.g., weight + zone only)
2. ✅ Verify `ChooserTable` property is set
3. ✅ Check column bindings match action properties (`HitZone`, `DamageDirection`, etc.)
4. ✅ Review logs: `"[ChooserAction] No valid montages passed filters!"`

### Custom Skeleton Not Working

**Symptom:** Default bone names don't match your skeleton

**Solution:** Override bone mappings in Blueprint:
1. Clear `BoneToZoneMappings` in constructor
2. Add custom mappings with your skeleton's bone names
3. Use hierarchy - only specify root bones, children auto-included

### Chooser References Old Property Name

**Symptom:** `Property/Function: HitBone not Found`

**Cause:** Chooser table uses old `HitBone` property (renamed to `HitZone`)

**Solution:**
1. ✅ Open chooser table
2. ✅ Find column referencing `HitBone`
3. ✅ Change binding to `HitZone`

---

## Advanced Topics

### Hierarchy Traversal Algorithm

The bone-to-zone cache builds recursively:

```cpp
void BuildBoneToZoneCache()
{
    for (FHitZoneBoneMapping& Mapping : BoneToZoneMappings)
    {
        for (FName& RootBone : Mapping.BoneNames)
        {
            // Breadth-first traversal
            TArray<int32> Queue = { GetBoneIndex(RootBone) };

            while (!Queue.IsEmpty())
            {
                int32 BoneIndex = Queue[0];
                Queue.RemoveAt(0);

                // Cache this bone
                BoneToZoneCache.Add(GetBoneName(BoneIndex), Mapping.ZoneTag);

                // Add children to queue
                for (int32 i = 0; i < NumBones; ++i)
                {
                    if (GetParentIndex(i) == BoneIndex)
                        Queue.Add(i);
                }
            }
        }
    }
}
```

**Key Points:**
- Breadth-first traversal ensures all descendants are cached
- First zone wins if bone appears in multiple mappings
- O(N) build time where N = total bones in skeleton
- O(1) lookup time via TMap

### Direction Calculation Details

Hit direction uses dot product thresholds:

```cpp
// Thresholds based on angle ranges
const float COS_22_5 = 0.924f;  // cos(22.5°)
const float COS_67_5 = 0.383f;  // cos(67.5°)

// Direction vector points TO attacker (negated relative)
FVector ToAttacker = -(Receiver - Dealer).Normalized();

float ForwardDot = DotProduct(Victim.Forward, ToAttacker);
float RightDot = DotProduct(Victim.Right, ToAttacker);

// 8-way detection
if (ForwardDot >= COS_22_5)
    return Front;  // 337.5° - 22.5°
else if (ForwardDot >= COS_67_5 && RightDot >= COS_67_5)
    return FrontRight;  // 22.5° - 67.5°
// ... etc for all 8 directions
```

**Angle Ranges:**
- Front: 337.5° - 22.5° (45° total)
- FrontRight: 22.5° - 67.5° (45°)
- Right: 67.5° - 112.5° (45°)
- BackRight: 112.5° - 157.5° (45°)
- Back: 157.5° - 202.5° (45°)
- BackLeft: 202.5° - 247.5° (45°)
- Left: 247.5° - 292.5° (45°)
- FrontLeft: 292.5° - 337.5° (45°)

---

## References

- [Chooser Actions Guide](chooser-actions-guide.md) - General chooser action usage
- [Deterministic Chooser Selection](deterministic-chooser-selection.md) - Multiplayer synchronization details
- [GAS Action Abilities Analysis](../gas-action-abilities-analysis.md) - GAS integration overview

---

**Document Version:** 1.0
**Last Updated:** 2025-10-09
**Author:** insodimension
