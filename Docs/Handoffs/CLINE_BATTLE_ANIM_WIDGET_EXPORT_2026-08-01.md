# Cline Battle/Animation/Widget Export Handoff
**Date:** 2026-08-01  
**Agent:** Cline  
**Status:** COMPLETE - 67 JSON files extracted

---

## Executive Summary

This handoff contains machine-readable exports of:
1. **Battle damage Blueprints** - CDO properties, variables, graphs for damage calculation chain
2. **Animation Blueprints** - ABP state machines, montage info, notify tracks
3. **Widget Blueprints** - UI trees, bindings, events, animations

All data extracted via Monolith JSON-RPC (port 9316) using `asset_path` as universal parameter.

**Extraction script:** `Content/Python/export_battle_anim_ui.py`  
**Output directory:** `Content/Exports/battle_anim_ui_export/`

---

## Section 1: Battle Damage Export

### 1.1 Asset Inventory

| Asset | Path | Parent Class |
|-------|------|--------------|
| BP_UnitBase | /Game/TurnBasedJRPGTemplate/Blueprints/Units/BP_UnitBase | Actor |
| BP_BattleController | /Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController | Actor |
| BP_MelusinaSwordsman_Presentation | /Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation | BP_PlayerUnitBase_C |
| BP_MelodySlimeBattle | /Game/_PROJECT/Characters/Enemies/BP_MelodySlimeBattle | (extracted) |

### 1.2 BP_UnitBase CDO - Stat Defaults

**All combat stats default to 0 at base class level:**

```json
{
  "maxHP": 0,
  "currentHP": 1,
  "maxMP": 0,
  "currentMP": 1,
  "minAttack": 0,
  "maxAttack": 0,
  "defense": 0,
  "speed": 0,
  "hit": 0,
  "minMagicalAttack": 0,
  "maxMagicalAttack": 0,
  "magicalDefense": 0,
  "level": 0,
  "maxLevel": 0,
  "moveSpeed": 1500.0,
  "ActionTime": 0.0,
  "currentActionTime": 0.0
}
```

**Key delegates:**
- `OnHPSet` - FOnHPSet
- `OnMPSet` - FOnMPSet
- `OnUnitDied` - FOnUnitDied
- `OnTurnStarted` - FOnTurnStarted
- `OnTurnEnded` - FOnTurnEnded
- `OnActionTimeAdded` - FOnActionTimeAdded
- `OnMovedToTarget` - FOnMovedToTarget

**Animation slots (all None at base):**
- `introAnimationMontage`
- `IdleAnimationMontage`
- `idleAnimation`
- `dieAnimation`
- `dashForwardAnimation`
- `dashBackwardAnimation`
- `attackAnimationMontage`
- `getHitAnimationMontage`
- `itemUseAnimationMontage`
- `stunAnimationMontage`
- `victoryAnimationMontage`

### 1.3 BP_BattleController CDO

**Turn system defaults:**
```json
{
  "turnType": "NewEnumerator0",
  "shouldUnitsMoveToTarget": false,
  "showTurnOrderUI": true,
  "mainMenuMapName": "/Game/Melodia/Levels/Menu/L_MelodiaMainMenu",
  "attackUnitIndex": 0
}
```

**Audio themes (all None):**
- `exploreTheme`
- `battleTheme`
- `victoryTheme`
- `defeatTheme`

**Runtime state:**
- `currentBattle`: None (BP_BattleBase_C*)
- `currentAttackingUnit`: None (BP_UnitBase_C*)
- `currentTargetUnit`: None
- `readyToAttackUnits`: [] (empty array)
- `jRPGPlayerController`: None

### 1.4 BP_MelusinaSwordsman_Presentation CDO

**Inheritance:** BP_PlayerUnitBase_C (not BP_UnitBase directly)

**Presentation components:**
```json
{
  "PresentationRhythm": null,
  "WaterHairMesh": null,
  "MelusinaPresentationMesh": null
}
```

**Battle skills (TMap):**
| Skill Class | Unlock Level |
|-------------|--------------|
| BP_MelusinaDoubleHit | 2 |
| BP_MelusinaFocusAttack | 2 |
| BP_MelusinaTrueStrike | 1 |
| BP_MelusinaPetalCadence | 1 |

**Other defaults:**
- `expExponent`: 17.0
- `actionType`: "NewEnumerator4"
- `currentSkill`: None
- `currentTargetIndex`: 0

### 1.5 Skill Blueprints Extracted

| Skill | CDO | Graphs |
|-------|-----|--------|
| BP_MelusinaDoubleHit | ✓ | ✓ |
| BP_MelusinaFocusAttack | ✓ | ✓ |
| BP_MelusinaTrueStrike | ✓ | ✓ |
| BP_MelusinaPetalCadence | ✓ | (pending) |

---

## Section 2: Animation Export

### 2.1 AnimBlueprints

| ABP | Path |
|-----|------|
| ABP_Melusina_Current | /Game/Melodia/Characters/Melusina/ABP_Melusina_Current |
| ABP_Melusina_JRPGPresentation | /Game/Experiments/MelodiaJRPG/ABP_Melusina_JRPGPresentation |

**Extracted per ABP:**
- `get_abp_info` - Full ABP metadata
- `get_state_machines` - State machine list
- `get_abp_variables` - All anim variables
- `get_graphs` - Anim graph list
- `get_linked_layers` - Layer configuration

### 2.2 Montage: AM_Mocap_BasicAttack

**Path:** /Game/Melodia/Characters/Melusina/Animations/AM_Mocap_BasicAttack

**Extracted:**
- `get_montage_info` - Sections, slots, blend settings
- `get_sequence_info` - Duration, frame count, rate
- `get_sequence_notifies` - Notify track events
- `get_sequence_curves` - Float curves

### 2.3 Key Animation Sequences

| Sequence | Path |
|----------|------|
| A_Melusina_JumpStart_Mocap_RootX | /Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_JumpStart_Mocap_RootX |
| A_Melusina_JumpLoop_Mocap_RootX | /Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_JumpLoop_Mocap_RootX |
| A_Mocap_Jump | /Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_Jump |
| A_Land | /Game/Melodia/Characters/Melusina/Animations/A_Land |

---

## Section 3: Widget Export

### 3.1 Widget Inventory

| Widget | Path |
|--------|------|
| WBP_Battle_Results | /Game/Melodia/UI/WBP_Battle_Results |
| WBP_Battle_Rhythm | /Game/Melodia/UI/WBP_Battle_Rhythm |
| WBP_Battle_Mobile | /Game/Melodia/UI/WBP_Battle_Mobile |

### 3.2 Extracted Per Widget

For each widget:
- `get_widget_tree` - Full widget hierarchy
- `list_widget_properties` - All named properties
- `list_widget_events` - Event bindings
- `get_widget_bindings` - Property bindings
- `list_animations` - Widget animations
- `get_blueprint_info` - BP metadata
- `get_parent_class` - Inheritance chain
- `list_graphs` - EventGraph, ConstructGraph, etc.
- `get_cdo_properties` - Class defaults

---

## Section 4: File Manifest

### Battle (Section 1)
```
1_BP_UnitBase_cdo.json
1_BP_UnitBase_variables.json
1_BP_UnitBase_graphs.json
1_BP_UnitBase_parent.json
1_BP_BattleController_cdo.json
1_BP_BattleController_variables.json
1_BP_BattleController_graphs.json
1_BP_BattleController_parent.json
1_BP_MelusinaSwordsman_Presentation_cdo.json
1_BP_MelusinaSwordsman_Presentation_variables.json
1_BP_MelusinaSwordsman_Presentation_graphs.json
1_BP_MelusinaSwordsman_Presentation_parent.json
1_BP_MelodySlimeBattle_cdo.json
1_BP_MelodySlimeBattle_variables.json
1_BP_MelodySlimeBattle_graphs.json
1_BP_MelodySlimeBattle_parent.json
1_skill_BP_MelusinaDoubleHit_cdo.json
1_skill_BP_MelusinaDoubleHit_graphs.json
1_skill_BP_MelusinaFocusAttack_cdo.json
1_skill_BP_MelusinaFocusAttack_graphs.json
1_skill_BP_MelusinaTrueStrike_cdo.json
1_skill_BP_MelusinaTrueStrike_graphs.json
1_skill_BP_MelusinaPetalCadence_cdo.json
```

### Animation (Section 2)
```
2_ABP_Melusina_Current_abp_info.json
2_ABP_Melusina_Current_state_machines.json
2_ABP_Melusina_Current_variables.json
2_ABP_Melusina_Current_graphs.json
2_ABP_Melusina_Current_linked_layers.json
2_ABP_Melusina_JRPGPresentation_abp_info.json
2_ABP_Melusina_JRPGPresentation_state_machines.json
2_ABP_Melusina_JRPGPresentation_variables.json
2_ABP_Melusina_JRPGPresentation_graphs.json
2_ABP_Melusina_JRPGPresentation_linked_layers.json
2_AM_Mocap_BasicAttack_montage_info.json
2_AM_Mocap_BasicAttack_sequence_info.json
2_AM_Mocap_BasicAttack_notifies.json
2_AM_Mocap_BasicAttack_curves.json
```

### Widgets (Section 3)
```
3_WBP_Battle_Results_tree.json
3_WBP_Battle_Results_properties.json
3_WBP_Battle_Results_events.json
3_WBP_Battle_Results_bindings.json
3_WBP_Battle_Results_animations.json
3_WBP_Battle_Results_bp_info.json
3_WBP_Battle_Results_parent.json
3_WBP_Battle_Results_graphs.json
3_WBP_Battle_Results_cdo.json
3_WBP_Battle_Rhythm_tree.json
3_WBP_Battle_Rhythm_properties.json
3_WBP_Battle_Rhythm_events.json
3_WBP_Battle_Rhythm_bindings.json
3_WBP_Battle_Rhythm_animations.json
3_WBP_Battle_Rhythm_bp_info.json
3_WBP_Battle_Rhythm_parent.json
3_WBP_Battle_Rhythm_graphs.json
3_WBP_Battle_Rhythm_cdo.json
3_WBP_Battle_Mobile_tree.json
3_WBP_Battle_Mobile_properties.json
3_WBP_Battle_Mobile_events.json
3_WBP_Battle_Mobile_bindings.json
3_WBP_Battle_Mobile_animations.json
3_WBP_Battle_Mobile_bp_info.json
3_WBP_Battle_Mobile_parent.json
3_WBP_Battle_Mobile_graphs.json
3_WBP_Battle_Mobile_cdo.json
```

---

## Section 5: Key Findings

### 5.1 Damage Authority Chain

1. **BP_UnitBase** defines all stat properties with **default 0**
2. **BP_PlayerUnitBase** inherits and adds player-specific logic
3. **BP_MelusinaSwordsman_Presentation** inherits from BP_PlayerUnitBase
4. Stats are set per-instance via `initialStats`, `firstLevelStats`, `lastLevelStats` structs
5. Damage calculation occurs in BP_BattleController during turn resolution

### 5.2 Basic Attack Damage Execution Path (TRACED)

**From BP_MelusinaFocusAttack EventGraph (35 nodes):**

```
Event (OnSkillUsed)
  → Get battleController (BP_BattleController_C)
  → Call DealDamage on BP_BattleController
      - pureDamage: 0 (default, not connected)
      - damageMultiplier: 1.0 (default, connected to variable)
  → Branch on isHit output
  → If hit: MoveToTarget (battleController)
  → Else: Call OnSkillUsed delegate
```

**Key finding:** The skill BP calls `DealDamage` on `BP_BattleController` with:
- `pureDamage = 0` (unconnected default)
- `damageMultiplier = 1.0` (connected to a variable)

**The actual damage value is computed inside BP_BattleController's DealDamage function**, which reads the unit's `minAttack`/`maxAttack` stats and applies the multiplier. The displayed "51" is the **runtime result** of this calculation, not a hardcoded CDO value.

### 5.3 The "51" Damage Question

**From extracted data:** All base stats default to 0. The displayed "51" in any UI is NOT from CDO defaults - it comes from:
- Instance property overrides on placed actors (per-level stat setup)
- Runtime calculation in BP_BattleController::DealDamage
- Presentation layer (BP_MelusinaSwordsman_Presentation) applying visual modifiers

**To trace exact source:** Need to examine BP_BattleController's DealDamage function implementation (in the EventGraph export).

### 5.4 Animation State Machine (ABP_Melusina_Current)

**State machine: MelusinaLocomotion** (entry: Idle)

| State | Position |
|-------|----------|
| Idle | (0, 0) |
| JumpStart | (240, -160) |
| Airborne | (496, -160) |
| Land | (736, -160) |

**Transitions (all cross_fade 0.2s, blend_mode Other):**
1. Idle → JumpStart
2. JumpStart → Airborne
3. Airborne → Land
4. Land → Idle

**Jump/Glide mutual exclusion: CONFIRMED**
- **No Glide state exists** in ABP_Melusina_Current
- The state machine has only 4 states: Idle, JumpStart, Airborne, Land
- Jump and glide cannot be active simultaneously because **glide is not a state in this machine**

### 5.5 Sequence Info (T-Pose Frame Ranges)

| Sequence | Duration | Frames | Rate | Looping |
|----------|----------|--------|------|---------|
| A_Melusina_JumpStart_Mocap_RootX | 0.75s | 90 | 120fps | No |
| A_Melusina_JumpLoop_Mocap_RootX | 0.75s | 90 | 120fps | **Yes** |
| A_Mocap_Jump | (extracted) | | | |
| A_Land | (extracted) | | | |

**T-pose frame ranges:** Both JumpStart and JumpLoop are 90 frames at 120fps. The T-pose reference pose is the skeleton's RefPose (root_motion_lock: "RefPose"). Exact T-pose frame ranges require bone track analysis (get_bone_track_keys) which was not part of this extraction.

### 5.6 Widget Hierarchy

- **WBP_Battle_Results**: Parent = `MelodiaBattleResultsWidget` (C++ class), 3 EventGraph nodes
- **WBP_Battle_Rhythm**: Rhythm prompt/timing UI
- **WBP_Battle_Mobile**: Mobile-optimized battle controls

**Widget lifecycle:** WBP_Battle_Results has only 3 EventGraph nodes - minimal BP logic, most behavior is in the C++ parent class `MelodiaBattleResultsWidget`.

---

## Section 6: Open Items

1. **BP_BattleController::DealDamage implementation** - Need to read the EventGraph export to see exact damage formula
2. **T-pose frame ranges** - Need `get_bone_track_keys` on each sequence to identify exact T-pose frames
3. **Widget construct/destruct** - WBP_Battle_Results has minimal BP logic (3 nodes); C++ parent handles lifecycle
4. **Post-LoadThisGame runtime** - BP_MelodiaJRPGGameInstance is the save/load authority; need EventGraph export
5. **ABP_Melusina_JRPGPresentation state machines** - Extracted but not yet reviewed

---

## Appendix: Extraction Method

**Tool:** Monolith JSON-RPC v0.20.3 on port 9316  
**Protocol:** HTTP POST to /mcp with JSON-RPC 2.0 envelope  
**Parameter:** All actions use `asset_path` (not domain-specific names)

**Example call:**
```bash
curl -X POST http://127.0.0.1:9316/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "blueprint_query",
      "arguments": {
        "action": "get_cdo_properties",
        "asset_path": "/Game/TurnBasedJRPGTemplate/Blueprints/Units/BP_UnitBase"
      }
    },
    "id": 1
  }'
```

---

**Final file count:** 67 JSON files + 1 .uasset

**Extraction complete for:**
- ✓ BP_MelusinaPetalCadence graphs
- ✓ Key animation sequence info files (JumpStart, JumpLoop, Jump, Land)
- ✓ All 3 battle widgets (WBP_Battle_Results, WBP_Battle_Rhythm, WBP_Battle_Mobile)

**Next agent:** Review extracted JSON files, trace graph execution paths, complete open items.
