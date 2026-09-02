# WBP Systems Deep Dive & P0 Quick Wins

**Author:** Melusina (Hermes agent)
**Date:** 2026-08-28
**Status:** Comprehensive review complete — quick wins identified

---

## 1. Quill UI System

### Architecture

The Quill UI system consists of 4 native C++ adapter classes and their WBP children:

| C++ Class | WBP Child | Role |
|-----------|-----------|------|
| `UMelodiaQuillDialogWidget` | `WBP_MelodiaQuillDialog` | Dialogue presentation (speaker, body, advance) |
| `UMelodiaQuillSelectionWidget` | `WBP_MelodiaQuillSelection` | Selection presentation (options box) |
| `UMelodiaQuillChoiceEntryWidget` | `WBP_MelodiaQuillChoiceEntry` | Individual choice row |
| `UMelodiaQuillBackgroundWidget` | `WBP_MelodiaQuillBackground` | Background image transition |

### Native Adapters

All 4 adapters extend QuillScript's built-in widgets:
- `UMelodiaQuillDialogWidget` extends `UDialogBox`
- `UMelodiaQuillSelectionWidget` extends `USelectionBox`
- `UMelodiaQuillBackgroundWidget` extends `UBackgroundBox`
- `UMelodiaQuillChoiceEntryWidget` extends `UUserWidget`

### Key Features

- **Input Context**: Dialogue context pushed on interaction, popped on completion
- **BindWidgetOptional**: All child widgets are optional bindings (graceful degradation)
- **Focus Management**: Choice entries can be focused via keyboard/gamepad
- **Background Transition**: Bypasses QuillScript's viewport-condition bug

### Quick Wins

1. **Background Panel Rendering**: The `ShowBackgroundBox` double-call issue needs investigation
2. **Choice Entry Focus**: Verify keyboard/gamepad navigation works in PIE
3. **Speaker Text Binding**: Ensure `SpeakerText` is bound in the WBP
4. **Advance Button**: Verify `AdvanceButton` click handling

---

## 2. Battle UI System

### Architecture

The Battle UI system is a multi-layer overlay on top of the stock JRPG battle UI:

| Component | Role |
|-----------|------|
| `UMelodiaUIBridgeSubsystem` | Single owner of battle-time Melodia widgets |
| `UMelodiaBattleKeyboardLegendWidget` | Keyboard legend overlay |
| `UMelodiaJRPGPresentationRhythmComponent` | Rhythm grading (presentation-only) |
| `UMelodiaExternalJRPGBridgeSubsystem` | Battle start/end events |
| `UMelodiaJRPGBattleOverlaySubsystem` | Battle overlay observer |

### Widget Inventory

| WBP/C++ | Role |
|---------|------|
| `WBP_Battle_Rhythm` | Rhythm highway presentation |
| `WBP_Battle_Mobile` | Mobile battle UI |
| `WBP_Battle_Results` | Battle results screen |
| `WBP_GradePop` | Rhythm grade popup |
| `BP_MelodiaUnitBattleDetails` | Unit details panel |
| `BP_MelodiaBossUI` | Boss health bar |
| `BP_MelodiaVictoryDialogue` | Victory dialogue |
| `BP_MelodiaDefeatDialogue` | Defeat dialogue |
| `BP_MelodiaSkillUseDialogue` | Skill use dialogue |
| `BP_MelodiaItemUseDialogue` | Item use dialogue |
| `BP_MelodiaPlayerUnitListUI` | Player unit list |
| `BP_MelodiaQuestNotificationListUI` | Quest notification list |
| `BP_MelodiaQuestNotification` | Quest notification |
| `BP_MelodiaFadeTransitionUI` | Fade transition |
| `BP_MelodiaCraftBar` | Crafting bar |
| `BP_MelodiaExploreUI` | Exploration UI |
| `WBP_MelodiaCurrencyRow` | Currency display |
| `WBP_MelodiaWallet_Universal` | Universal wallet |
| `WBP_MelodiaTokenWallet` | Token wallet |
| `WBP_MelodiaSettings` | Settings panel |
| `WBP_MelodiaOpeningSlideshow` | Opening slideshow |
| `WBP_SaveLoadPanel` | Save/load panel |
| `WBP_UltCutIn` | Ultimate cut-in |
| `WBP_ComicOrrery` | Comic orrery |
| `WBP_BlessingBurden` | Blessing/burden display |
| `WBP_DialogueBubble` | Dialogue bubble |
| `WBP_MainMenu` | Main menu |
| `WBP_Settings` | Settings |
| `WBP_SaveLoad` | Save/load |
| `WBP_MenuButton` | Menu button |
| `DA_OrreryRegistry` | Orrery data asset |

### Key Features

- **Single Writer**: `UMelodiaUIBridgeSubsystem` owns all battle widgets
- **Reflective Write**: `EnsureStockBattleUIControllerReference()` writes `battleController` via reflection
- **Rhythm Grade**: `ShowRhythmGradeOnBattleUI()` forwards rhythm verdicts to BP
- **Live Results**: `LiveResultsWidget` persists outside battle
- **Keyboard Legend**: `UMelodiaBattleKeyboardLegendWidget` draws key labels

### Quick Wins

1. **Battle Controller Reference**: `EnsureStockBattleUIControllerReference()` is the root fix for "Accessed None" cascade
2. **Rhythm Grade Pop**: `WBP_GradePop` integration with `ShowRhythmGradeOnBattleUI()`
3. **Keyboard Legend Font**: Verify `LegendFont` is assigned in WBP defaults
4. **Battle Results**: `WBP_Battle_Results` integration with `HandleBattleCompleted()`
5. **Unit Details**: `BP_MelodiaUnitBattleDetails` for target selection

---

## 3. Chest/NPC UI System

### Architecture

The Chest/NPC UI system is built on the exploration interaction framework:

| Component | Role |
|-----------|------|
| `AMelodiaExplorationInteractionVolume` | Presentation-only overlap/interaction anchor |
| `AMelodiaPuzzleRelayVolume` | Spatial puzzle trigger |
| `WBP_DialogueBubble` | Dialogue bubble for NPC interactions |
| `UMelodiaInputContextSubsystem` | Input context routing |

### Interaction Volume Features

- **InteractionId**: Unique identifier for the interaction
- **PromptText**: Display text for the interaction prompt
- **bRequireMelusina**: Only Melusina can interact (default: true)
- **bOneShot**: One-time interaction (default: false)
- **Events**: `OnMelusinaEntered`, `OnMelusinaExited`, `OnInteractionRequested`

### Quick Wins

1. **Dialogue Bubble**: `WBP_DialogueBubble` for NPC chest/interaction prompts
2. **Interaction Prompt**: `PromptText` display for chests/NPCs
3. **Input Context**: Push `Dialogue` context on interaction
4. **Focus Management**: Ensure interaction widget gets focus

---

## 4. Input Context System

### Architecture

Stack-based input context system with 7 contexts:

| Context | Movement | Interaction | Saving | Input |
|---------|----------|-------------|--------|-------|
| None | Yes | Yes | Yes | Exploration |
| Exploration | Yes | Yes | Yes | Default |
| Dialogue | No | Yes | Yes | Advance/choice |
| Battle | No | No | No | JRPG commands |
| Menu | No | No | No | Menu navigation |
| Cinematic | No | No | No | All suppressed |
| Rhythm | No | No | No | Lane keys (Q/W/O/P) |

### Quick Wins

1. **Context Stack**: Verify contexts push/pop correctly
2. **Movement Lock**: Ensure movement is suppressed in Dialogue/Battle/Rhythm
3. **Save Gate**: Verify saving is refused in Battle/Rhythm
4. **Interaction Lock**: Ensure interaction is only allowed in Exploration

---

## 5. Widget Scaffold System

### Scaffolds

| Scaffold | Role |
|----------|------|
| `WBP_FiligreeBorder_scaffold` | Decorative border |
| `WBP_KeybindBadge_scaffold` | Keybind display badge |
| `WBP_SparkleFX_scaffold` | Sparkle particle effect |
| `WBP_ParchmentPanel_scaffold` | Parchment panel background |
| `WBP_MenuButton_scaffold` | Menu button template |

### Quick Wins

1. **Consistent Borders**: Apply `WBP_FiligreeBorder` to all UI panels
2. **Keybind Badges**: Use `WBP_KeybindBadge` for keyboard hints
3. **Parchment Backgrounds**: Use `WBP_ParchmentPanel` for dialogue/NPC panels
4. **Menu Buttons**: Use `WBP_MenuButton` for consistent menu styling

---

## 6. P0 Quick Wins — Prioritized

### Priority 1: Critical (Block P0 Closure)

| # | Win | Impact | Effort |
|---|-----|--------|--------|
| 1 | `EnsureStockBattleUIControllerReference()` | Fixes "Accessed None" cascade in battle | Low (already implemented) |
| 2 | `ShowRhythmGradeOnBattleUI()` integration | Rhythm grade popup in battle | Low (already implemented) |
| 3 | Quill background panel rendering | Background images display correctly | Medium (needs investigation) |
| 4 | Battle results `WBP_Battle_Results` | Victory/defeat screens work | Medium (needs wiring) |

### Priority 2: Important (Post-P0)

| # | Win | Impact | Effort |
|---|-----|--------|--------|
| 5 | `WBP_DialogueBubble` for NPC/chest prompts | Interaction prompts display | Medium |
| 6 | Widget scaffold system | Consistent UI styling | Low |
| 7 | Keyboard legend font assignment | Battle keyboard hints display | Low |
| 8 | Input context routing for UI | Correct input mode per UI state | Medium |
| 9 | `BP_MelodiaUnitBattleDetails` | Unit details in battle | Medium |
| 10 | `BP_MelodiaBossUI` | Boss health bar | Medium |

### Priority 3: Nice-to-Have

| # | Win | Impact | Effort |
|---|-----|--------|--------|
| 11 | `WBP_BlessingBurden` display | Roguelike room mod display | Medium |
| 12 | `WBP_QuestJournal` | Quest tracking UI | High |
| 13 | `WBP_SkillCodex` | Skill reference UI | High |
| 14 | `WBP_MelodiaSettings` | Settings panel | Medium |
| 15 | `WBP_SaveLoadPanel` | Save/load UI | Medium |

---

## 7. Integration Points

### Quill → Battle Flow

```
Quill Dialogue → melodia:battle:<EncounterId> → UMelodiaExternalJRPGBridgeSubsystem
  → StartTaggedJRPGBattle() → Stock JRPG Battle → Battle Result
  → HandleBattleOver() → ResumeQuillOnce() → Quill resumes
```

### Battle → UI Flow

```
Battle Requested → UMelodiaUIBridgeSubsystem::HandleBattleRequested()
  → CreateBattleUIInternal() → CreateMelodiaBattleUI()
  → Push Rhythm context → Rhythm session → ShowRhythmGradeOnBattleUI()
  → Battle completed → HandleBattleCompleted() → RemoveBattleUIInternal()
```

### NPC/Chest → UI Flow

```
Overlap → AMelodiaExplorationInteractionVolume::HandleBeginOverlap()
  → Push Dialogue context → Show WBP_DialogueBubble
  → Interaction requested → OnInteractionRequested broadcast
  → Pop Dialogue context → Resume Exploration
```

---

## 8. Known Defects

| Defect | Impact | Status |
|--------|--------|--------|
| Quill background panel not rendering | Background never shows | OPEN — needs investigation |
| Battle controller reference null | Target selection fails | FIXED — `EnsureStockBattleUIControllerReference()` implemented |
| Rhythm grade not displaying | No rhythm feedback | OPEN — needs `WBP_GradePop` wiring |
| Battle results not showing | No victory/defeat screen | OPEN — needs `WBP_Battle_Results` wiring |
| NPC dialogue bubble missing | No interaction prompts | OPEN — needs `WBP_DialogueBubble` wiring |

---

## 9. File Map

### C++ Headers

| File | Role |
|------|------|
| `MelodiaQuillPresentationWidgets.h` | 4 Quill adapter widgets |
| `MelodiaUIBridgeSubsystem.h` | Battle UI bridge subsystem |
| `MelodiaBattleKeyboardLegendWidget.h` | Keyboard legend widget |
| `MelodiaJRPGPresentationRhythmComponent.h` | Rhythm presentation component |
| `MelodiaExternalJRPGBridgeSubsystem.h` | JRPG battle bridge |
| `MelodiaJRPGBattleOverlaySubsystem.h` | Battle overlay observer |
| `MelodiaInputContextSubsystem.h` | Input context subsystem |
| `MelodiaExplorationActors.h` | Exploration interaction actors |

### WBP Files

| Path | Role |
|------|------|
| `Content/Melodia/UI/Quill/WBP_MelodiaQuillDialog.uasset` | Dialogue widget |
| `Content/Melodia/UI/Quill/WBP_MelodiaQuillSelection.uasset` | Selection widget |
| `Content/Melodia/UI/Quill/WBP_MelodiaQuillChoiceEntry.uasset` | Choice entry widget |
| `Content/Melodia/UI/Quill/WBP_MelodiaQuillBackground.uasset` | Background widget |
| `Content/Melodia/UI/WBP_Battle_Rhythm.uasset` | Rhythm highway |
| `Content/Melodia/UI/WBP_Battle_Mobile.uasset` | Mobile battle UI |
| `Content/Melodia/UI/WBP_Battle_Results.uasset` | Battle results |
| `Content/Melodia/UI/WBP_GradePop.uasset` | Grade popup |
| `Content/Melodia/UI/WBP_DialogueBubble.uasset` | Dialogue bubble |
| `Content/Melodia/UI/WBP_BlessingBurden.uasset` | Blessing/burden |
| `Content/Melodia/UI/WBP_QuestJournal.uasset` | Quest journal |
| `Content/Melodia/UI/WBP_SkillCodex.uasset` | Skill codex |
| `Content/Melodia/UI/WBP_MainMenu.uasset` | Main menu |
| `Content/Melodia/UI/WBP_Settings.uasset` | Settings |
| `Content/Melodia/UI/WBP_SaveLoad.uasset` | Save/load |
| `Content/Melodia/UI/WBP_MenuButton.uasset` | Menu button |
| `Content/Melodia/UI/WBP_MelodiaCurrencyRow.uasset` | Currency row |
| `Content/Melodia/UI/WBP_MelodiaWallet_Universal.uasset` | Universal wallet |
| `Content/Melodia/UI/WBP_MelodiaTokenWallet.uasset` | Token wallet |
| `Content/Melodia/UI/WBP_MelodiaSettings.uasset` | Melodia settings |
| `Content/Melodia/UI/WBP_MelodiaOpeningSlideshow.uasset` | Opening slideshow |
| `Content/Melodia/UI/WBP_SaveLoadPanel.uasset` | Save/load panel |
| `Content/Melodia/UI/WBP_UltCutIn.uasset` | Ultimate cut-in |
| `Content/Melodia/UI/WBP_ComicOrrery.uasset` | Comic orrery |
| `Content/Melodia/UI/DA_OrreryRegistry.uasset` | Orrery data asset |
| `Content/Melodia/UI/WidgetScaffolds/` | 6 widget scaffolds |

### Blueprint Actors

| Path | Role |
|------|------|
| `Content/Melodia/UI/BP_MelodiaUnitBattleDetails.uasset` | Unit battle details |
| `Content/Melodia/UI/BP_MelodiaBossUI.uasset` | Boss UI |
| `Content/Melodia/UI/BP_MelodiaVictoryDialogue.uasset` | Victory dialogue |
| `Content/Melodia/UI/BP_MelodiaDefeatDialogue.uasset` | Defeat dialogue |
| `Content/Melodia/UI/BP_MelodiaSkillUseDialogue.uasset` | Skill use dialogue |
| `Content/Melodia/UI/BP_MelodiaItemUseDialogue.uasset` | Item use dialogue |
| `Content/Melodia/UI/BP_MelodiaPlayerUnitListUI.uasset` | Player unit list |
| `Content/Melodia/UI/BP_MelodiaQuestNotificationListUI.uasset` | Quest notification list |
| `Content/Melodia/UI/BP_MelodiaQuestNotification.uasset` | Quest notification |
| `Content/Melodia/UI/BP_MelodiaFadeTransitionUI.uasset` | Fade transition |
| `Content/Melodia/UI/BP_MelodiaCraftBar.uasset` | Craft bar |
| `Content/Melodia/UI/BP_MelodiaExploreUI.uasset` | Explore UI |
