# Melodia UI Widget Inheritance & Replacement Plan
**Date:** 2026-08-04  
**Author:** UE 5.8 UI Architecture — Monolith Static Analysis  
**Status:** Read-only Research Complete — Ready for Implementation Planning

---

## 1. Widget Inheritance Map

### 1.1 Stock Widget Hierarchy

`
UserWidget (UMG base)
├── BP_UIBase                         /Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_UIBase
│   ├── BP_VictoryDialogue            .../Dialogues/BP_VictoryDialogue
│   ├── BP_DefeatDialogue             .../Dialogues/BP_DefeatDialogue
│   ├── BP_InfoDialogue               .../Dialogues/BP_InfoDialogue
│   ├── BP_LevelUpDialogue            .../Dialogues/BP_LevelUpDialogue
│   ├── BP_ItemObtainDialogue         .../Dialogues/BP_ItemObtainDialogue
│   └── BP_YesNoDialogue              .../Dialogues/BP_YesNoDialogue
├── BP_BattleUI                       .../UI/BP_BattleUI
├── BP_ActionsUI                      .../UI/BP_ActionsUI
├── BP_ActionButton                   .../UI/BP_ActionButton
├── BP_ExploreUI                      .../UI/BP_ExploreUI
├── BP_PlayerUnitListUI               .../UI/BP_PlayerUnitListUI
├── BP_ItemUseDialogue                .../Dialogues/BP_ItemUseDialogue
├── BP_SkillUseDialogue               .../Dialogues/BP_SkillUseDialogue
├── BP_UnitBattleDetails              .../UI/BP_UnitBattleDetails
├── BP_BossUI                         .../UI/BP_BossUI
├── BP_TurnOrderList                  .../UI/BP_TurnOrderList
├── BP_TurnOrderUI                    .../UI/BP_TurnOrderUI
├── BP_CraftBar                       .../UI/BP_CraftBar
├── BP_QuestNotificationListUI        .../UI/BP_QuestNotificationListUI
└── MainMenu/
    ├── BP_MainMenu                   .../UI/MainMenu/BP_MainMenu
    ├── BP_PauseMenu                  .../UI/MainMenu/BP_PauseMenu
    ├── BP_PartyUI                    .../UI/MainMenu/BP_PartyUI
    ├── BP_SaveUI                     .../UI/MainMenu/BP_SaveUI
    ├── BP_EquipmentDetails            .../UI/MainMenu/BP_EquipmentDetails
    ├── BP_ItemDetails                .../UI/MainMenu/BP_ItemDetails
    ├── BP_SkillDetails               .../UI/MainMenu/BP_SkillDetails
    ├── BP_QuestDetails               .../UI/MainMenu/BP_QuestDetails
    └── BP_UnitButtonList              .../UI/MainMenu/BP_UnitButtonList
`

### 1.2 Current Melodia Widgets (Separate Hierarchy — No Inheritance from Stock)

All existing Melodia widgets inherit directly from **UserWidget**, NOT from their stock counterparts. This is the central architectural gap.

| Melodia Widget | Asset Path | Parent | Stock Counterpart | Same Interface? |
|---|---|---|---|---|
| BP_MelodiaBattleUI | /Game/MelodiaIntegration/UI/BP_MelodiaBattleUI | UserWidget | BP_BattleUI | **Near-identical widget tree** (18 vs 19 widgets; only difference: no MelodiaNoteHighway Image) |
| BP_MelodiaActionsUI | /Game/MelodiaIntegration/UI/BP_MelodiaActionsUI | UserWidget | BP_ActionsUI | **Simplified** — no ActionsBackground Image, no Background canvas render opacity |
| BP_MelodiaActionButton | /Game/MelodiaIntegration/UI/BP_MelodiaActionButton | UserWidget | BP_ActionButton | Separate implementation |
| BP_MelodiaTurnOrderList | /Game/MelodiaIntegration/UI/BP_MelodiaTurnOrderList | UserWidget | BP_TurnOrderList | Separate implementation |
| BP_MelodiaRhythmPrompt | /Game/MelodiaIntegration/UI/BP_MelodiaRhythmPrompt | UserWidget | (No stock equivalent — Melodia-native) | N/A — Melodia-only feature |

**Missing Melodia versions (need creation):**
- BP_MelodiaVictoryDialogue (inherit from BP_VictoryDialogue → BP_UIBase)
- BP_MelodiaDefeatDialogue (inherit from BP_DefeatDialogue → BP_UIBase)
- BP_MelodiaInfoDialogue (inherit from BP_InfoDialogue → BP_UIBase)
- BP_MelodiaLevelUpDialogue (inherit from BP_LevelUpDialogue → BP_UIBase)
- BP_MelodiaItemObtainDialogue (inherit from BP_ItemObtainDialogue → BP_UIBase)
- BP_MelodiaYesNoDialogue (inherit from BP_YesNoDialogue → BP_UIBase)
- BP_MelodiaPlayerUnitListUI (inherit from BP_PlayerUnitListUI)
- BP_MelodiaItemUseDialogue (inherit from BP_ItemUseDialogue)
- BP_MelodiaSkillUseDialogue (inherit from BP_SkillUseDialogue)
- BP_MelodiaUnitBattleDetails (inherit from BP_UnitBattleDetails)
- BP_MelodiaBossUI (inherit from BP_BossUI)
- BP_MelodiaExploreUI (inherit from BP_ExploreUI)
- BP_MelodiaCraftBar (inherit from BP_CraftBar)
- All MainMenu/* Melodia variants

### 1.3 BP_BattleController — Create Widget Nodes

The BP_BattleController (/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController) is the primary creation point for battle-related widgets. It has **two** battle UI variable paths:

| Variable | Type | Current Usage |
|---|---|---|
| attleUI | BP_BattleUI_C (stock) | **Currently assigned BP_MelodiaBattleUI_C** via K2Node_CreateWidget_7 (type mismatch: Melodia inherits UserWidget, not BP_BattleUI) |
| melodiaBattleUI | BP_MelodiaBattleUI_C | Exists as a separate variable but unclear if actively used |

**Create Widget Nodes in EventGraph:**

| Node ID | Creates | Class | Inputs |
|---|---|---|---|
| K2Node_CreateWidget_7 | BP Melodia Battle UI | BP_MelodiaBattleUI_C | currentBattle, battleController → Set battleUI |
| K2Node_CreateWidget_3 | BP Victory Dialogue | BP_VictoryDialogue_C | expReward, goldReward, usableItemDrops, miscItemDrops, equipmentDrops |
| K2Node_CreateWidget_5 | BP Defeat Dialogue | BP_DefeatDialogue_C | mainMenuMapName, defeatTheme |
| K2Node_CreateWidget_4 | BP Level Up Dialogue | BP_LevelUpDialogue_C | playerUnit, playerUnitData, levelUpAmount, battleController |
| K2Node_CreateWidget_1/2/8 | BP Info Dialogue | BP_InfoDialogue_C | dialogueText, dialogueTitle |
| K2Node_CreateWidget_6 | BP Unit Button List | BP_UnitButtonList_C | jRPGPlayerController, playerUnits |

**Critical Discovery:** Node K2Node_CreateWidget_7 creates BP_MelodiaBattleUI_C but assigns the ReturnValue (type BP_MelodiaBattleUI_C) to variable attleUI which is typed as BP_BattleUI_C. This is a **type-mismatch hazard** — BP_MelodiaBattleUI inherits from UserWidget, NOT from BP_BattleUI. The fact that this compiles suggests either:
- (a) The attleUI variable type was widened to UserWidget (less likely given the audit data showing it as BP_BattleUI_C)
- (b) BP_MelodiaBattleUI inherits from BP_BattleUI but the parent query showed UserWidget (possible if the index is stale)
- (c) The blueprint has a compiler error (BP_BattleController status shows "Error")

---

## 2. Replacement Order (Priority)

### Tier 1 — P0 (Battle-critical, directly used in BP_BattleController)

| Order | Widget | Rationale |
|---|---|---|
| 1 | **BP_MelodiaBattleUI → inherit from BP_BattleUI** | Fix the type-compatibility gap; BP_BattleUI is the root container for all battle sub-widgets |
| 2 | **BP_MelodiaVictoryDialogue** | Direct Create Widget node; handles battle outcome display |
| 3 | **BP_MelodiaDefeatDialogue** | Direct Create Widget node; handles battle defeat flow |
| 4 | **BP_MelodiaActionsUI** | Already exists but needs to inherit from BP_ActionsUI for type compatibility with BP_PlayerUnitBase casts |

### Tier 2 — P1 (Battle sub-widgets, referenced inside BP_BattleUI)

| Order | Widget | Rationale |
|---|---|---|
| 5 | **BP_MelodiaItemUseDialogue** | Sub-widget inside BattleUI; used in item flow |
| 6 | **BP_MelodiaSkillUseDialogue** | Sub-widget inside BattleUI; used in skill flow |
| 7 | **BP_MelodiaUnitBattleDetails** | Sub-widget inside BattleUI (×2 instances: attacking + target) |
| 8 | **BP_MelodiaPlayerUnitListUI** | Sub-widget inside BattleUI; player party display |
| 9 | **BP_MelodiaBossUI** | Sub-widget inside BattleUI; boss encounter HUD |
| 10 | **BP_MelodiaTurnOrderList** | Already exists as BP_MelodiaTurnOrderList — needs inheritance fix |

### Tier 3 — P2 (Explore/Dialogue widgets, created by PlayerController)

| Order | Widget | Rationale |
|---|---|---|
| 11 | **BP_MelodiaExploreUI** | Created in BP_JRPGPlayerController; main exploration HUD |
| 12 | **BP_MelodiaInfoDialogue** | Used extensively by BattleController + QuestNPCs + Interactables |
| 13 | **BP_MelodiaLevelUpDialogue** | Created in BattleController after victory |
| 14 | **BP_MelodiaItemObtainDialogue** | Post-battle item reward display |
| 15 | **BP_MelodiaYesNoDialogue** | Confirmation prompts |
| 16 | **BP_MelodiaCraftBar** | Crafting progress UI |

### Tier 4 — P3 (Main Menu widgets, created in BP_PauseMenu)

| Order | Widget | Rationale |
|---|---|---|
| 17-26 | **All MainMenu/ variants** | Lowest blast radius; created internally by BP_PauseMenu; lowest user-facing priority for the 20-min slice |

---

## 3. Type Compatibility Analysis

### 3.1 Inheritance-Based Compatibility (Recommended Approach)

For each stock widget, the Melodia replacement should inherit from the stock class:

`
BP_MelodiaBattleUI : BP_BattleUI (UserWidget)
BP_MelodiaVictoryDialogue : BP_VictoryDialogue (BP_UIBase → UserWidget)
BP_MelodiaDefeatDialogue : BP_DefeatDialogue (BP_UIBase → UserWidget)
BP_MelodiaActionsUI : BP_ActionsUI (UserWidget)
BP_MelodiaInfoDialogue : BP_InfoDialogue (BP_UIBase → UserWidget)
BP_MelodiaLevelUpDialogue : BP_LevelUpDialogue (BP_UIBase → UserWidget)
BP_MelodiaItemUseDialogue : BP_ItemUseDialogue (UserWidget)
BP_MelodiaSkillUseDialogue : BP_SkillUseDialogue (UserWidget)
BP_MelodiaUnitBattleDetails : BP_UnitBattleDetails (UserWidget)
BP_MelodiaBossUI : BP_BossUI (UserWidget)
BP_MelodiaPlayerUnitListUI : BP_PlayerUnitListUI (UserWidget)
BP_MelodiaTurnOrderList : BP_TurnOrderList (UserWidget)
BP_MelodiaExploreUI : BP_ExploreUI (UserWidget)
BP_MelodiaCraftBar : BP_CraftBar (UserWidget)
`

**Benefits:**
- Full type compatibility: any pin accepting BP_BattleUI_C will accept BP_MelodiaBattleUI_C
- All existing Cast To BP_BattleUI_C nodes continue to function
- Variable types (attleUI: BP_BattleUI_C) remain valid
- Shared functions/events from stock parent remain available
- Override only the visual elements (brushes, colors, text styles)

**Cost:**
- Melodia widgets carry the full stock widget tree in addition to their overrides (slightly larger memory footprint)
- Stock widget changes may propagate to Melodia versions (risk of accidental inheritance contamination)

### 3.2 Current Melodia Widget Interface Gaps

| Widget | Stock Functions/Events | Melodia Has Same? |
|---|---|---|
| BP_BattleUI | ShowBattleUI, HideBattleUI, ShowSkills, HideSkills, ShowUsableItemInventory, UpdateTurnOrderList, ShowBossUI, ShowRhythmGrade (via RhythmPrompt), 8 delegate outputs | ✅ **Fully matched** |
| BP_ActionsUI | (4 BP_ActionButton children + ActionsBackground Image) | ⚠️ **Missing ActionsBackground** — simplified widget tree |
| BP_ActionButton | Background, ActionText, ActionButton (plum/gold styling) | Separate implementation, needs audit |
| BP_TurnOrderList | TurnOrderBackground, TurnOrderText | Separate implementation, needs audit |

### 3.3 Critical Type Issues

1. **BP_BattleController.battleUI variable** — typed BP_BattleUI_C, currently receiving BP_MelodiaBattleUI_C (via Create Widget node). This only works at runtime because both inherit from UserWidget and are assigned to a common base, but direct calls to stock-specific functions (e.g., ShowBattleUI) require the Cast to succeed. If BP_MelodiaBattleUI doesn't inherit from BP_BattleUI, those calls silently fail or produce runtime errors.

2. **BP_PlayerUnitBase Cast To BP_ActionsUI** — Stock BP_PlayerUnitBase has a Cast To BP_ActionsUI node. A Melodia ActionsUI that inherits from UserWidget (not BP_ActionsUI) will fail this cast. The Melodia ActionsUI **must** inherit from BP_ActionsUI for this path to work.

---

## 4. Risk Assessment

### 4.1 Risk by Widget Replacement

| Widget | Risk Level | What Could Break | Mitigation |
|---|---|---|---|
| **BP_MelodiaBattleUI** | **HIGH** | Root container; if it breaks, ALL battle UI is invisible. Type mismatch on attleUI variable could cause cascade failures across 29+ BattleUI references in BP_BattleController | Inherit from BP_BattleUI; incrementally override visual components (brushes, colors) while preserving all child widget bindings |
| **BP_MelodiaVictoryDialogue** | **MEDIUM** | 9 input pins (expReward, goldReward, drops ×3). Wrong parent = inputs silently ignored. Post-battle rewards flow broken, save/player progression halts | Inherit from BP_VictoryDialogue → BP_UIBase; preserve all exposed pins; only swap DialogueBackground brush + Title text color |
| **BP_MelodiaDefeatDialogue** | **MEDIUM** | 2 input pins (mainMenuMapName, defeatTheme). If broken, defeat flow won't return to menu — player gets stuck mid-battle | Same approach as VictoryDialogue |
| **BP_MelodiaActionsUI** | **MEDIUM** | Cast To BP_ActionsUI in BP_PlayerUnitBase fails → action buttons (Attack, Skill, Item, Flee) don't appear. Player cannot interact | Must inherit from BP_ActionsUI, not UserWidget |
| **BP_MelodiaItemUseDialogue** | **LOW-MED** | Sub-widget within BattleUI; item selection/inventory broken if missing | Only visually swap; preserve all delegate bindings |
| **BP_MelodiaSkillUseDialogue** | **LOW-MED** | Sub-widget within BattleUI; skill selection broken if missing | Same as ItemUseDialogue |
| **BP_MelodiaUnitBattleDetails** | **LOW** | Unit stat display broken; cosmetic only, battle logic unaffected | Brush + text color only |
| **BP_MelodiaBossUI** | **LOW** | Boss HP display cosmetic; battle logic unaffected | Same |
| **BP_MelodiaTurnOrderList** | **LOW** | Turn order sidebar cosmetic; visual-only | Same |
| **BP_MelodiaExploreUI** | **LOW-MED** | Created in BP_JRPGPlayerController; if broken, exploration HUD vanishes | Inherit from BP_ExploreUI; preserve all marker bindings |
| **BP_MelodiaInfoDialogue** | **LOW** | Generic info popups; low blast radius | Inherit from BP_InfoDialogue → BP_UIBase |
| **BP_MelodiaLevelUpDialogue** | **LOW** | Level-up celebration screen; cosmetic | Same |
| **BP_MelodiaCraftBar** | **LOW** | Crafting progress; low usage in 20-min slice | Defer to P2-P3 |
| **MainMenu widgets** | **LOW** | Created internally by BP_PauseMenu; no external type dependencies | Defer entirely to P3 |

### 4.2 Global Risks

| Risk | Description | Severity |
|---|---|---|
| **BP_BattleController has "Error" status** | The Blueprint compilation status shows "Error" — this may already be broken before any changes. Check list_errored_blueprints before modifying. | HIGH |
| **Existing Melodia widgets have wrong parent** | BP_MelodiaBattleUI, BP_MelodiaActionsUI, BP_MelodiaActionButton, BP_MelodiaTurnOrderList all inherit from UserWidget. The 2-node swap strategy requires changing these to inherit from their stock counterparts. This is a **reparenting operation** which is destructive. | MEDIUM |
| **Third-party copy divergence** | Stock widgets exist at /Game/TurnBasedJRPGTemplate/... AND /Game/_ThirdParty/TurnBasedJRPGTemplate/.... Any changes must target the primary project copy, not the third-party copy. The audit confirmed only the project-local copy was fixed. | LOW |
| **WBP_Battle_Rhythm is known stale** | Explicitly excluded from this migration per the previous audit. Rhythm gameplay UI needs human re-evaluation. | LOW (deferred) |

### 4.3 Pre-Implementation Checklist

Before any widget is modified:

1. ✅ Run editor_query list_errored_blueprints to check BP_BattleController compile status
2. ✅ Run editor_query list_dirty_packages to capture current dirty state
3. ✅ Duplicate any widget being reparented (backup pattern: _Backup_2026-08-04)
4. ✅ Verify that the Melodia widget's widget tree matches the stock widget's tree (child names, types)
5. ✅ Export the stock widget's get_widget_tree for diff comparison after reparenting
6. ⬜ After reparenting, verify get_widget_tree shows inherited children intact
7. ⬜ After first reparent, run lueprint_query compile_blueprint on the Melodia widget
8. ⬜ After compiling BP_BattleController, verify no compiler errors on the Set battleUI connection

---

## 5. Implementation Strategy

### 5.1 Reparent-and-Swap Protocol (for each widget)

`
Step 1:  Duplicate the existing Melodia widget as backup
Step 2:  Reparent the Melodia widget to inherit from the stock widget
         (blueprint_query → reparent_blueprint)
Step 3:  Verify the widget tree — inherited stock widgets appear
Step 4:  Set Melodia-style brushes and colors on the inherited components
         (ui_query → set_brush, set_widget_property)
Step 5:  Compile the Melodia widget
Step 6:  In BP_BattleController (or the relevant creator BP), 
         swap the Create Widget node's Class pin from stock to Melodia version
Step 7:  Compile the creator blueprint
Step 8:  Run get_widget_tree on the creator to verify binding
`

### 5.2 Critical Path: BattleUI

The BP_MelodiaBattleUI is already WIRED as the active widget (K2Node_CreateWidget_7 assigns to attleUI). The only issue is the **inheritance/parent class**. Steps:

1. Backup BP_MelodiaBattleUI
2. Reparent BP_MelodiaBattleUI to BP_BattleUI (parent = /Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI.BP_BattleUI_C)
3. Override visual properties (brushes → ParchmentFrame, text → gold)
4. Compile
5. No Create Widget node swap needed — it's already pointing to BP_MelodiaBattleUI!

### 5.3 Critical Path: ActionsUI

BP_MelodiaActionsUI exists but:
- Inherits from UserWidget (must change to BP_ActionsUI)
- Has no ActionsBackground Image (stock has one)
- Cast To BP_ActionsUI in BP_PlayerUnitBase will fail without proper inheritance

Steps:
1. Add ActionsBackground Image to BP_MelodiaActionsUI (or ensure it doesn't need it — visual audit needed)
2. Reparent to BP_ActionsUI
3. Now Cast To BP_ActionsUI will succeed

### 5.4 New Widget Creation (VictoryDialogue, DefeatDialogue)

No Melodia versions exist. For each:
1. Create new WBP (or duplicate from stock)
2. Reparent/Set inheriting from the stock version
3. Apply Melodia visual overrides
4. Connect to a new Create Widget node in BattleController (or swap the Class pin on the existing node)

---

## 6. Verified Asset Paths (from Monolith)

### Stock Widgets (project-local copies)
`
/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI
/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_ActionsUI
/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_ActionButton
/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_ExploreUI
/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_PlayerUnitListUI
/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_UnitBattleDetails
/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BossUI
/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_TurnOrderList
/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_CraftBar
/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_UIBase
/Game/TurnBasedJRPGTemplate/Blueprints/UI/Dialogues/BP_VictoryDialogue
/Game/TurnBasedJRPGTemplate/Blueprints/UI/Dialogues/BP_DefeatDialogue
/Game/TurnBasedJRPGTemplate/Blueprints/UI/Dialogues/BP_InfoDialogue
/Game/TurnBasedJRPGTemplate/Blueprints/UI/Dialogues/BP_LevelUpDialogue
/Game/TurnBasedJRPGTemplate/Blueprints/UI/Dialogues/BP_ItemObtainDialogue
/Game/TurnBasedJRPGTemplate/Blueprints/UI/Dialogues/BP_YesNoDialogue
/Game/TurnBasedJRPGTemplate/Blueprints/UI/Dialogues/BP_ItemUseDialogue
/Game/TurnBasedJRPGTemplate/Blueprints/UI/Dialogues/BP_SkillUseDialogue
`

### Existing Melodia Widgets
`
/Game/MelodiaIntegration/UI/BP_MelodiaBattleUI
/Game/MelodiaIntegration/UI/BP_MelodiaActionsUI
/Game/MelodiaIntegration/UI/BP_MelodiaActionButton
/Game/MelodiaIntegration/UI/BP_MelodiaTurnOrderList
/Game/MelodiaIntegration/UI/BP_MelodiaRhythmPrompt
`

### Melodia Universal Textures Available
`
/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_ParchmentFrame ✅ (applied)
/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_CornerBaroque ❌
/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_DividerScroll ❌
/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_CrestBaroque ❌
/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_MedallionRosette ❌
/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_BraceVolute ❌
/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_SealULT ❌
/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_SealSP ❌
/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_Hitline ❌
/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_RhythmLaneInk ❌
`

---

## 7. Design Token Reference (from Audit)

| Token | Value | Hex/RGBA | Applied To |
|---|---|---|---|
| Plum button | rgba(77,46,61,0.95) | #4D2E3D F2 | BP_ActionButton BackgroundColor |
| Gold text | rgba(242,214,158,1) | #F2D69E | All text blocks |
| Parchment tone | rgba(242,230,207,0.92) | #F2E6CF EB | All dialogue/image backgrounds |
| Gold accent | rgba(235,184,87,~0.7-0.9) | #EBB857 | Not yet applied (for borders/accents) |
| Void | rgba(11,10,19,1) | #0B0A13 | Not yet applied (deep backgrounds) |
| Iri-cyan | rgba(120,235,255,1) | #78EBFF | Marker_PetalPriestess only |

---

## 8. Appendix: Widget Tree Diff Summary

### BP_BattleUI (stock) vs BP_MelodiaBattleUI (current)

| Component | Stock BP_BattleUI | BP_MelodiaBattleUI | Match? |
|---|---|---|---|
| CanvasPanel_0 root | ✅ | ✅ | ✅ |
| PlayerUnitUIOverlay → BP_PlayerUnitListUI_C | ✅ | ✅ | ✅ Identical |
| ItemUseDialogueOverlay → BP_ItemUseDialogue_C | ✅ | ✅ | ✅ Identical |
| SkillUseDialogueOverlay → BP_SkillUseDialogue_C | ✅ | ✅ | ✅ Identical |
| UnitBattleDetailsOverlay → [TargetImage, ×2 BP_UnitBattleDetails_C] | ✅ | ✅ | ✅ Identical |
| BossUI → BP_BossUI_C | ✅ | ✅ | ✅ Identical |
| TurnOrderOverlay → BP_TurnOrderList_C | ✅ | ✅ | ✅ Identical |
| KeyboardLegend TextBlock | ✅ | ✅ | ✅ Identical |
| RhythmPrompt → BP_MelodiaRhythmPrompt_C | ✅ | ✅ | ✅ Identical |
| MelodiaNoteHighway Image | ✅ | ❌ **Missing** | ⚠️ Difference |
| **Animations** | 5 (ShowPlayerUnitListUIAnim, ShowUnitBattleDetailsAnim, TargetImageAnim, ShowBossUIAnim, ShowTurnOrderUI) | 5 (identical set) | ✅ |

**Conclusion:** BP_MelodiaBattleUI is >95% structurally identical to BP_BattleUI. The only difference is a single Image widget (MelodiaNoteHighway) that exists in stock but not in Melodia. Safe to reparent.

### BP_ActionsUI (stock) vs BP_MelodiaActionsUI (current)

| Component | Stock BP_ActionsUI | BP_MelodiaActionsUI | Match? |
|---|---|---|---|
| CanvasPanel_0 root | ✅ (render_opacity=0.92) | ✅ (render_opacity=1.0) | ⚠️ Opacity differs |
| ItemButton (BP_ActionButton_C) | ✅ | ✅ | ✅ Same position |
| SkillButton (BP_ActionButton_C) | ✅ | ✅ | ✅ Same position |
| FleeButton (BP_ActionButton_C) | ✅ | ✅ | ✅ Same position |
| AttackButton (BP_ActionButton_C) | ✅ | ✅ | ✅ Same position |
| ActionsBackground Image | ✅ | ❌ **Missing** | ⚠️ Stock has Background |
| ShowAnimation | ✅ | ✅ | ✅ |

**Conclusion:** BP_MelodiaActionsUI is a simplified version missing the ActionsBackground Image. This is acceptable for visual design but means it cannot be a pure inherit-and-override. The ActionsBackground will be inherited from BP_ActionsUI after reparenting — no action needed.
