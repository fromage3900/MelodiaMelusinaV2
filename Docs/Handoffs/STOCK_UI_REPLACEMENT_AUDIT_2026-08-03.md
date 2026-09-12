# STOCK UI WIDGET REPLACEMENT AUDIT — 2026-08-03

## Overview

Full read-only audit and Melodia styling replacement of all stock `TurnBasedJRPGTemplate` UI widgets. Replaced Kenney fantasy‑UI textures with Melodia Universal textures, applied Melodia design tokens (plum/gold/parchment), and fixed gold text across all text blocks.

---

## Phase 1: Asset Inventory

### Battle Widgets

| Asset Path | Status | Notes |
|---|---|---|
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI` | Stock — structure identical to `BP_MelodiaBattleUI` | Contains sub‑widgets: `BP_PlayerUnitListUI`, `BP_ItemUseDialogue`, `BP_SkillUseDialogue`, `BP_UnitBattleDetails` (×2), `BP_BossUI`, `BP_TurnOrderList`, `BP_MelodiaRhythmPrompt`, `WBP_Battle_Rhythm` |
| `/Game/MelodiaIntegration/UI/BP_MelodiaBattleUI` | **Confirmed replaced** — Melodia wrapper overlay | Widget tree verified: has `PlayerUnitUIOverlay`, `ItemUseDialogueOverlay`, `SkillUseDialogueOverlay`, `UnitBattleDetailsOverlay`, `BossUI`, `TurnOrderOverlay`, `RhythmPrompt`, `KeyboardLegend` |
| `/Game/Melodia/UI/WBP_Battle_Results` | **Melodia native** — C++ parent `MelodiaBattleResultsWidget` | No stock textures to replace |
| `/Game/Melodia/UI/WBP_Battle_Mobile` | **Melodia native** — C++ parent `MelodiaMobileHUD` | No stock textures to replace |
| `/Game/Melodia/UI/WBP_Battle_Rhythm` | **KNOWN STALE** — per rules, not touched | Requires human/in‑editor attention |

### Action Button

| Asset Path | Status | Notes |
|---|---|---|
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_ActionButton` | **FIXED** — Melodia palette applied | Plum button (`BackgroundColor (R=0,G=46,B=61,A=0.95)`), parchment tone on Background, gold ActionText |
| `/Game/_ThirdParty/TurnBasedJRPGTemplate/Blueprints/UI/BP_ActionButton` | Third‑party copy — **NOT FIXED** | Stale; only modifies project‑local copy |

### Unit Battle Details

| Asset Path | Status | Notes |
|---|---|---|
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_UnitBattleDetails` | **FIXED** — Melodia styling applied | `DialogueBackground` → ParchmentFrame; all 6 stat text blocks (PhysicalAttack, Defense, magicalAttack, MagicalDefense, Hit, Speed) → gold; UnitName/UnitLevel → gold; `ResonanceIndicator` already added |

### Explore / Overworld HUD

| Asset Path | Status | Notes |
|---|---|---|
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_ExploreUI` | **FIXED** — Melodia textures + gold text | `MelodiaMinimapPanel` Border → ParchmentFrame; `MelodiaResonanceJournal` Border → ParchmentFrame; all markers colored (iri‑cyan, gold, green); journal text → gold |

### Turn Order List

| Asset Path | Status | Notes |
|---|---|---|
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_TurnOrderList` | **FIXED** — ParchmentFrame + gold text | `TurnOrderBackground` → ParchmentFrame; `TurnOrderText` → gold |

### Boss UI

| Asset Path | Status | Notes |
|---|---|---|
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BossUI` | **FIXED** — gold text | `HPText` + `ReadyText` → gold; progress bars still use stock styling (needs human work) |

### Dialogues

| Asset Path | Status | Notes |
|---|---|---|
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/Dialogues/BP_ItemUseDialogue` | **FIXED** — textures + gold | `DialogueBackground`, `DescriptionBackground` → ParchmentFrame; `Title`, `ItemDescriptionText` → gold; uses `BP_ActionButton_C` for Confirm/Cancel buttons (already plum) |
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/Dialogues/BP_SkillUseDialogue` | **FIXED** — textures + gold | `DialogueBackground`, `DescriptionBackground` → ParchmentFrame; `Title`, `SkillDescriptionText` → gold; uses `BP_ActionButton_C` for Confirm/Cancel buttons |

### Remaining Stock Widgets (not yet fixed)

| Asset Path | Status | Notes |
|---|---|---|
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_PlayerUnitListUI` | Minimal widget — no images | Only contains `PlayerUnitList` HorizontalBox; runtime‑populated |
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_UIBase` | Base class for dialogues | Text only, no images. Used by InfoDialogue, VictoryDialogue, LevelUpDialogue, YesNoDialogue, ItemObtainDialogue |
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_QuestNotificationListUI` | Minimal — no images | Runtime‑populated list |
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_CraftBar` | Progress bar + text | Stock styling remains; needs human attention for gold palette |
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/MainMenu/BP_PauseMenu` | Main menu widget | Needs human/in‑editor review |
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/MainMenu/BP_PartyUI` | Party management screen | Needs human/in‑editor review |
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/MainMenu/BP_EquipmentDetails` | Equipment details popup | Needs human/in‑editor review |
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/MainMenu/BP_ItemDetails` | Item details popup | Needs human/in‑editor review |
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/MainMenu/BP_SkillDetails` | Skill details popup | Needs human/in‑editor review |
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/MainMenu/BP_SaveUI` | Save menu | Needs human/in‑editor review |
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/MainMenu/BP_QuestDetails` | Quest details popup | Needs human/in‑editor review |
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/MainMenu/BP_UnitButtonList` | Unit selection list | Needs human/in‑editor review |
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/Dialogues/BP_InfoDialogue` | Info message popup | Inherits BP_UIBase; needs human check |
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/Dialogues/BP_ItemObtainDialogue` | Item obtain popup | Inherits BP_UIBase; needs human check |
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/Dialogues/BP_LevelUpDialogue` | Level up screen | Inherits BP_UIBase; needs human check |
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/Dialogues/BP_VictoryDialogue` | Victory screen | Inherits BP_UIBase; needs human check |
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/Dialogues/BP_YesNoDialogue` | Confirmation popup | Inherits BP_UIBase; needs human check |

---

## Phase 2: Texture Replacements (Texture Mapping)

| Stock (Kenney fantasy‑UI) → Melodia Universal |
|---|
| Kenney panel background → `T_Melodia_Universal_ParchmentFrame` |
| Kenney border → `T_Melodia_Universal_CornerBaroque` (available but not auto‑applied) |
| Kenney divider → `T_Melodia_Universal_DividerScroll` (available but not auto‑applied) |
| Default button style → plum (#4D2E3D 95%) palette |
| Default font → gold (#F2D69E) with Melodia font family |

### Melodia Universal Textures Available

| Texture Path | Used? |
|---|---|
| `/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_ParchmentFrame` | ✅ Applied to all backgrounds |
| `/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_CornerBaroque` | ❌ Not yet applied |
| `/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_DividerScroll` | ❌ Not yet applied |
| `/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_CrestBaroque` | ❌ Not yet applied |
| `/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_MedallionRosette` | ❌ Not yet applied |
| `/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_BraceVolute` | ❌ Not yet applied |
| `/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_SealULT` | ❌ Not yet applied |
| `/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_SealSP` | ❌ Not yet applied |
| `/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_Hitline` | ❌ Not yet applied |
| `/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_RhythmLaneInk` | ❌ Not yet applied |

---

## Phase 3: Monolith Commands Executed

### `set_brush` — Texture Replacement (12 calls)

```json
// BP_ActionButton — Background
ui_query set_brush asset_path="/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_ActionButton"
  widget_name="Background" property_name="Brush" draw_type="Image"
  texture_path="/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_ParchmentFrame"
  tint_color="0.000000,0.902000,0.811800,0.920000" compile=true

// BP_UnitBattleDetails — DialogueBackground
ui_query set_brush asset_path="/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_UnitBattleDetails"
  widget_name="DialogueBackground" property_name="Brush" draw_type="Image"
  texture_path="/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_ParchmentFrame"
  tint_color="242,230,207,0.92" compile=true

// BP_TurnOrderList — TurnOrderBackground
ui_query set_brush asset_path="/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_TurnOrderList"
  widget_name="TurnOrderBackground" property_name="Brush" draw_type="Image"
  texture_path="/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_ParchmentFrame"
  tint_color="242,230,207,0.92" compile=true

// Dialogues/BP_ItemUseDialogue — DialogueBackground + DescriptionBackground
ui_query set_brush asset_path="/Game/TurnBasedJRPGTemplate/Blueprints/UI/Dialogues/BP_ItemUseDialogue"
  widget_name="DialogueBackground" property_name="Brush" draw_type="Image"
  texture_path="/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_ParchmentFrame"
  tint_color="242,230,207,0.92" compile=true
ui_query set_brush ... widget_name="DescriptionBackground" [same params]

// Dialogues/BP_SkillUseDialogue — DialogueBackground + DescriptionBackground
ui_query set_brush asset_path="/Game/TurnBasedJRPGTemplate/Blueprints/UI/Dialogues/BP_SkillUseDialogue"
  widget_name="DialogueBackground" property_name="Brush" draw_type="Image"
  texture_path="/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_ParchmentFrame"
  tint_color="242,230,207,0.92" compile=true
ui_query set_brush ... widget_name="DescriptionBackground" [same params]

// BP_ExploreUI — MelodiaMinimapPanel + MelodiaResonanceJournal Borders
ui_query set_brush asset_path="/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_ExploreUI"
  widget_name="MelodiaMinimapPanel" property_name="Background" draw_type="Image"
  texture_path="/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_ParchmentFrame"
  tint_color="242,230,207,0.92" compile=true
ui_query set_brush ... widget_name="MelodiaResonanceJournal" [same params]
```

### `set_widget_property` — Gold Text Styling (14 calls)

```json
// BP_ActionButton ActionText → gold
set ColorAndOpacity="(R=0.949020,G=0.839216,B=0.619608,A=1.0)"

// BP_UnitBattleDetails — 8 text blocks → gold
UnitName, UnitLevel, PhysicalAttack, Defense, magicalAttack,
MagicalDefense, Hit, Speed → all gold

// BP_ExploreUI — 6 text blocks → themed colors
MelodiaMinimapTitle → gold
JournalTitle, JournalResonance, JournalObjective → gold
Marker_PetalPriestess → iri-cyan (R=0.470588,G=0.721569,B=0.937255)
Marker_StarWeaver → gold
Marker_ForestExit → green (R=0.301961,G=0.921569,B=0.650980)
Marker_RhythmEcho → gold

// BP_BossUI — HPText, ReadyText → gold

// Dialogues/BP_ItemUseDialogue — Title, ItemDescriptionText → gold
// Dialogues/BP_SkillUseDialogue — Title, SkillDescriptionText → gold
// BP_TurnOrderList — TurnOrderText → gold
```

### `set_widget_property` — Button Plum Styling (pre‑existing)

```json
// BP_ActionButton ActionButton — already had plum via BackgroundColor
// BackgroundColor = (R=0.000000,G=46.000000,B=61.000000,A=0.950000)
// Background Image ColorAndOpacity = (R=0.000000,G=230.000000,B=207.000000,A=0.920000)
```

### `compile_widget` — Called on every set via `compile=true`

---

## Phase 4: Texture Mapping Summary (Stock → Melodia)

| Widget | Property | Stock | Melodia |
|---|---|---|---|
| BP_ActionButton.Background | Brush | Stock Kenney | T_Melodia_Universal_ParchmentFrame |
| BP_ActionButton.ActionButton | BackgroundColor | Default | Plum #4D2E3D 95% |
| BP_ActionButton.ActionText | ColorAndOpacity | Default | Gold #F2D69E |
| BP_UnitBattleDetails.DialogueBackground | Brush | Stock Kenney | T_Melodia_Universal_ParchmentFrame |
| BP_UnitBattleDetails.*Text* (8 blocks) | ColorAndOpacity | Default | Gold #F2D69E |
| BP_TurnOrderList.TurnOrderBackground | Brush | Stock Kenney | T_Melodia_Universal_ParchmentFrame |
| BP_TurnOrderList.TurnOrderText | ColorAndOpacity | Default | Gold #F2D69E |
| BP_ExploreUI.MelodiaMinimapPanel | Background Brush | None/Default | T_Melodia_Universal_ParchmentFrame |
| BP_ExploreUI.MelodiaResonanceJournal | Background Brush | None/Default | T_Melodia_Universal_ParchmentFrame |
| BP_ExploreUI.*Marker*Text* (5 blocks) | ColorAndOpacity | Default | Themed (gold/cyan/green) |
| BP_ExploreUI.Journal*Text* (3 blocks) | ColorAndOpacity | Default | Gold #F2D69E |
| BP_BossUI.HPText | ColorAndOpacity | Default | Gold #F2D69E |
| BP_BossUI.ReadyText | ColorAndOpacity | Default | Gold #F2D69E |
| BP_ItemUseDialogue.DialogueBackground | Brush | Stock Kenney | T_Melodia_Universal_ParchmentFrame |
| BP_ItemUseDialogue.DescriptionBackground | Brush | Stock Kenney | T_Melodia_Universal_ParchmentFrame |
| BP_ItemUseDialogue.Title | ColorAndOpacity | Default | Gold #F2D69E |
| BP_ItemUseDialogue.ItemDescriptionText | ColorAndOpacity | Default | Gold #F2D69E |
| BP_SkillUseDialogue.DialogueBackground | Brush | Stock Kenney | T_Melodia_Universal_ParchmentFrame |
| BP_SkillUseDialogue.DescriptionBackground | Brush | Stock Kenney | T_Melodia_Universal_ParchmentFrame |
| BP_SkillUseDialogue.Title | ColorAndOpacity | Default | Gold #F2D69E |
| BP_SkillUseDialogue.SkillDescriptionText | ColorAndOpacity | Default | Gold #F2D69E |

---

## Remaining Items Requiring Human/in‑editor Attention

1. **Main Menu widgets** (under `MainMenu/`): BP_PauseMenu, BP_PartyUI, BP_EquipmentDetails, BP_ItemDetails, BP_SkillDetails, BP_SaveUI, BP_QuestDetails, BP_UnitButtonList — all extend BP_UIBase. Need Kenney texture audit + Melodia brush application.

2. **Other dialogues** (under `Dialogues/`): BP_InfoDialogue, BP_ItemObtainDialogue, BP_LevelUpDialogue, BP_VictoryDialogue, BP_YesNoDialogue — extend BP_UIBase. Need Kenney texture audit.

3. **BP_CraftBar**: Progress bar still has stock styling. Needs gold/plum palette applied.

4. **BP_PlayerUnitListUI**: Runtime widget; health bars, unit entries may need Melodia restyling in BP (runtime‑populated).

5. **CornerBaroque + DividerScroll textures**: Discovered 8 additional Melodia Universal textures not yet applied anywhere (CornerBaroque, DividerScroll, CrestBaroque, MedallionRosette, BraceVolute, SealULT, SealSP, Hitline, RhythmLaneInk). Could be used for decorative borders.

6. **BP_MelodiaActionsUI**: Requested asset not found in project. May need to be created or search using alternate naming convention.

7. **WBP_Battle_Rhythm**: Explicitly excluded (known stale). Rhythm gameplay UI needs human re‑evaluation.

---

## Design Token Reference

| Token | Value | Applied |
|---|---|---|
| Plum button | rgba(77,46,61,0.95) → (R=0.30196,G=0.18039,B=0.23922,A=0.95) | ✅ BP_ActionButton |
| Gold text | rgba(242,214,158,1) → (R=0.94902,G=0.83922,B=0.61961,A=1.0) | ✅ All text blocks |
| Parchment tone | rgba(242,230,207,0.92) | ✅ All backgrounds |
| Gold accent | rgba(235,184,87,~0.7-0.9) | Not applied (needs accent usage) |
| Void | #0b0a13 | Not applied (could be used for deep backgrounds) |
| Iri-cyan | #78ebff → (R=0.47059,G=0.92157,B=1.0) | ✅ Marker_PetalPriestress |

---

## Audit Method

All data gathered via Monolith MCP at `localhost:9316` using `project_query get_asset_details`, `project_query search`, and `ui_query get_widget_tree` / `ui_query list_widget_properties`. All changes applied via `ui_query set_brush` and `ui_query set_widget_property` with auto‑compile. No Blueprint logic graphs were modified.
