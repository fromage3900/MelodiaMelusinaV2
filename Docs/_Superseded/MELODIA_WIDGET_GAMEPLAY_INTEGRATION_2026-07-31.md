# Melodia Widget Gameplay Integration Guide

> **Authority correction (2026-08-01):** Sections 1–8 are an early widget concept guide, not current wiring authority. The stock JRPG GameInstance/controller/UI own canonical save/load, battle commands, damage, turns, results, quests, and inventory. Do not bind menu widgets directly to `UMelodiaSaveGameSubsystem::LoadGame`, route stock commands through `UMelodiaBattleSession`, or restore stale `WBP_Battle_Rhythm` as authority. Current presentation extends the active stock widgets, consumes typed snapshots/events, and follows the runtime ownership update in §9. `UMelodiaInputContextSubsystem` is in the `BS_GodFile` game module, not `MelodiaCore`.

**Date:** 2026-07-31
**Purpose:** Document gameplay integration points for all UI widgets
**Scope:** All 5 widget blueprints with subsystem bindings and event hooks

---

## 1. WBP_MenuButton

### Purpose
Reusable button for all menu panels (MainMenu, SaveLoad, Settings, etc.)

### Gameplay Integration

**Events:**
- `OnClicked` - Delegate fired when button is clicked

**Subsystem Bindings:**

| Context | Subsystem | Method | Action |
|---------|-----------|--------|--------|
| MainMenu | `UMelodiaOpeningFlowSubsystem` | `ResetOpening()` | New Game button |
| MainMenu | `UMelodiaSaveGameSubsystem` | `LoadGame()` | Continue button |
| MainMenu | `WBP_SaveLoad` | `AddToViewport()` | Load Game button |
| MainMenu | `WBP_Settings` | `AddToViewport()` | Settings button |
| SaveLoad | `UMelodiaSaveGameSubsystem` | `SaveGame()` | Save button |
| SaveLoad | `UMelodiaSaveGameSubsystem` | `LoadGame()` | Load button |
| Settings | `UMelodiaGameUserSettings` | `ApplySettings()` | Apply settings button |

**Sparkle Integration:**
- Trigger: Call `WBP_SparkleFX::PlaySparkle()` on `OnClicked`
- Density tier: Read from `UMelodiaGameUserSettings` motion tier (full/soft/chrome/off)

**Implementation Notes:**
- Bind `OnClicked` delegate in parent widget graph
- Call sparkle widget's `PlaySparkle()` before executing action
- Disable button during async operations (save/load)

---

## 2. WBP_SparkleFX

### Purpose
Shared sparkle effects for UI feedback (success, hover, burst)

### Gameplay Integration

**C++ Hook:**
- `UMelodiaRhythmHUDWidget::TriggerSparkleBurst()` - Battle HUD sparkle trigger
- `UMelodiaRhythmHUDWidget::DoPulse()` - Pulse animation trigger

**Events:**
- `PlaySparkle()` - Blueprint-callable function to trigger sparkle animation
- `SetDensityTier()` - Update density based on settings

**Subsystem Bindings:**

| Context | Subsystem | Trigger | Sparkle Type |
|---------|-----------|---------|--------------|
| Battle | `UMelodiaRhythmHUDWidget` | `TriggerSparkleBurst()` on Perfect/Break/ULT | Burst |
| Battle | `UMelodiaRhythmHUDWidget` | `DoPulse()` on beat hit | Drift |
| Menu | Parent widget | Button hover/click | Burst/Drift |
| ComicOrrery | Parent widget | Select flourish | Orbit |
| Settings | `UMelodiaGameUserSettings` | Motion tier change | Update density |

**Density Mapping:**

| Tier | Density | Motion | Usage |
|------|---------|--------|-------|
| Full | 1.0 | Enabled | Default, full effects |
| Soft | 0.5 | Enabled | Reduced motion |
| Chrome | 0.25 | Enabled | Minimal motion |
| Off | 0.0 | Disabled | No sparkles |

**Implementation Notes:**
- Read motion tier from `UMelodiaGameUserSettings::GetMotionTier()`
- Update Niagara system density parameter when tier changes
- Call `TriggerSparkleBurst()` from C++ or Blueprint via BlueprintNativeEvent

---

## 3. WBP_KeybindBadge

### Purpose
JRPG keybind visualizer (F=Interact, J=Attack, K=Skill, L=Ultimate, E=Menu, ESC=Back)

### Gameplay Integration

**Input Context:**
- `UMelodiaInputContextSubsystem` - Keybind mappings and input handling

**Keybind Mapping:**

| Key | Action | Subsystem | Method |
|-----|--------|-----------|--------|
| F | Interact | `UMelodiaNPCInteractionComponent` | `BeginInteraction()` |
| J | Attack | `UMelodiaBattleSession` | `SubmitBasicCommand()` |
| K | Skill | `UMelodiaBattleSession` | `SubmitSkillCommand()` |
| L | Ultimate | `UMelodiaBattleSession` | `SubmitUltimateCommand()` |
| E | Menu | Parent widget | Open menu overlay |
| ESC | Back | Parent widget | Close panel / cancel |

**Color Mapping:**

| Action | Color | Design Token |
|--------|-------|--------------|
| Interact | Rose (#E8A9A1) | `KeybindColors.Interact` |
| Attack | Amber (#D9A566) | `KeybindColors.Attack` |
| Skill | Lavender (#B6A6D9) | `KeybindColors.Skill` |
| Ultimate | Seafoam (#8FC9BD) | `KeybindColors.Ultimate` |
| Menu | Parchment (#F2E6CF) | `KeybindColors.Menu` |
| Back | Ink (#3B2A22) | `KeybindColors.Back` |

**Events:**
- `OnKeyPressed` - Set `IsActive=true`, show glow
- `OnKeyReleased` - Set `IsActive=false`, hide glow
- `OnCooldown` - Desaturate color during cooldown

**Implementation Notes:**
- Bind to `UMelodiaInputContextSubsystem::OnKeyPressed` / `OnKeyReleased`
- Read keybind colors from `DA_MelodiaDesignTokens`
- Show glow overlay when key is pressed
- Desaturate during ability cooldowns (K, L)

---

## 4. WBP_ParchmentPanel

### Purpose
Base panel for all meta UI (SaveLoad, Settings, QuestJournal, NPCInfo, etc.)

### Gameplay Integration

**Usage:**
Helper atom - compose into larger panels, no direct gameplay bindings

**Subsystem Usage:**

| Panel | Subsystem | Content |
|-------|-----------|---------|
| SaveLoad | `UMelodiaSaveGameSubsystem` | Slot cards, save/load buttons |
| Settings | `UMelodiaGameUserSettings` | Tabbed controls, accessibility |
| QuestJournal | `AMelodiaQuestManagerBase` | Quest list, objectives |
| NPCInfo | `UMelodiaNPCDataAsset` | NPC details, interaction CTAs |

**Theming:**
- Parchment tint: Read from `DA_MelodiaDesignTokens.GameColors.ParchmentField`
- Clef watermark: Musical theme element, no gameplay function

**Implementation Notes:**
- Use as background container for all meta panels
- Child widgets added to `ContentSlot` canvas panel
- No direct gameplay events, purely visual

---

## 5. WBP_FiligreeBorder

### Purpose
Decorative Baroque borders for panel polish

### Gameplay Integration

**Usage:**
Helper atom - compose into panels for visual polish, no direct gameplay bindings

**Theming:**
- Color: Read from `DA_MelodiaDesignTokens.GameColors.GoldBorder`
- Crest: Optional header accent for important panels

**Usage Context:**

| Panel | ShowCorners | ShowCrest |
|-------|-------------|-----------|
| MainMenu | true | true |
| SaveLoad | true | false |
| Settings | true | false |
| QuestJournal | true | false |

**Implementation Notes:**
- Use for visual polish on important panels
- No direct gameplay events, purely decorative
- Toggle corners/crest via properties

---

## 6. Subsystem Reference

### UMelodiaSaveGameSubsystem
- **Path:** `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaSaveGameSubsystem.h`
- **Methods:** `SaveGame()`, `LoadGame()`, `HasSaveGame()`, `OnSaveCompleted`, `OnLoadCompleted`
- **Usage:** Save/Load buttons, continue game

### UMelodiaOpeningFlowSubsystem
- **Path:** `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaOpeningFlowSubsystem.h`
- **Methods:** `ResetOpening()`, `IsFirstDungeonUnlocked()`
- **Usage:** New Game button

### UMelodiaGameUserSettings
- **Path:** `Source/BS_GodFile/MelodiaIntegration/MelodiaGameUserSettings.h`
- **Methods:** `GetMotionTier()`, `ApplySettings()`
- **Usage:** Settings panel, sparkle density tier

### UMelodiaInputContextSubsystem
- **Path:** `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaInputContextSubsystem.h`
- **Methods:** `OnKeyPressed`, `OnKeyReleased`
- **Usage:** Keybind badge input handling

### UMelodiaBattleSession
- **Path:** `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaBattleSession.h`
- **Methods:** `SubmitBasicCommand()`, `SubmitSkillCommand()`, `SubmitUltimateCommand()`
- **Usage:** Battle keybinds (J, K, L)

### UMelodiaNPCInteractionComponent
- **Path:** `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaNPCInteractionComponent.h`
- **Methods:** `BeginInteraction()`, `AdvanceInteraction()`
- **Usage:** Interact keybind (F)

### UMelodiaRhythmHUDWidget
- **Path:** `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRhythmHUDWidget.h`
- **Methods:** `TriggerSparkleBurst()`, `DoPulse()`
- **Usage:** Battle sparkle effects

### AMelodiaQuestManagerBase
- **Path:** `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaQuestManagerBase.h`
- **Methods:** `GetActiveQuests()`, `GetCompletedQuestIds()`, `OnQuestAccepted`, `OnQuestCompleted`
- **Usage:** Quest journal panel

### UMelodiaNPCDataAsset
- **Path:** `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaNPCDefinition.h`
- **Methods:** `FindNPCById()`, `GetNPCByIndex()`
- **Usage:** NPC info panel

---

## 7. Implementation Checklist

### WBP_MenuButton
- [ ] Create widget blueprint
- [ ] Add corner star images
- [ ] Implement hover/pressed states
- [ ] Bind OnClicked delegate
- [ ] Integrate sparkle on click
- [ ] Bind to subsystem methods (SaveGame, LoadGame, etc.)

### WBP_SparkleFX
- [ ] Create widget blueprint
- [ ] Set up Niagara system
- [ ] Implement PlaySparkle() function
- [ ] Implement SetDensityTier() function
- [ ] Bind to UMelodiaRhythmHUDWidget::TriggerSparkleBurst()
- [ ] Read motion tier from UMelodiaGameUserSettings

### WBP_KeybindBadge
- [ ] Create widget blueprint
- [ ] Add action icons (hand, sword, sparkle, star, book, arrow)
- [ ] Bind to UMelodiaInputContextSubsystem
- [ ] Implement OnKeyPressed / OnKeyReleased
- [ ] Map colors to actions
- [ ] Implement cooldown desaturation

### WBP_ParchmentPanel
- [ ] Create widget blueprint
- [ ] Add parchment texture
- [ ] Add clef watermark
- [ ] Add scroll edges
- [ ] Set up content slot
- [ ] Use in SaveLoad, Settings, QuestJournal, NPCInfo

### WBP_FiligreeBorder
- [ ] Create widget blueprint
- [ ] Add filigree textures (corners, edges, crest)
- [ ] Implement corner/crest toggles
- [ ] Use in MainMenu, SaveLoad, Settings

---

## 8. Testing Checklist

### Gameplay Integration
- [ ] Test WBP_MenuButton OnClicked in PIE
- [ ] Test sparkle trigger on button click
- [ ] Test keybind badge input response (F, J, K, L, E, ESC)
- [ ] Test sparkle density tier changes in settings
- [ ] Test save/load button subsystem bindings
- [ ] Test new game button subsystem bindings

### Visual Polish
- [ ] Test corner star animations (hover, pressed)
- [ ] Test parchment panel tinting
- [ ] Test filigree border visibility
- [ ] Test keybind badge glow on key press
- [ ] Test sparkle burst animation timing

---

This guide ensures all widgets have documented gameplay integration points with the existing Melodia subsystems.

## 9. 2026-08-01 Runtime Ownership Update

### CommonUI/input contract
- Screen widgets request/release `UMelodiaInputContextSubsystem` contexts; they do not independently call `SetInputMode` or mutate cursor state.
- Each activatable screen defines a deterministic initial focus target and restores focus after modal close.
- CommonInput action rows supply keyboard/gamepad glyphs; labels must not hard-code `E`, `Enter`, or controller face-button names.
- Existing legacy mappings remain compatibility inputs until dedicated Enhanced Input/CommonInput assets are live.

### Semantic feedback contract
Presentation emits semantic feedback IDs such as `UI.Feedback.Hover`, `Focus`, `Confirm`, `Back`, `Denied`, `QuestAccepted`, `HarmonyGain`, `DialogueAdvance`, and `ChoiceSelected`. A shared router resolves those IDs to sound, animation, sparkle type, density, and optional haptics.

Feedback is presentation-only:
- It never advances Quill.
- It never grants rewards or changes Persona/JRPG state.
- It never performs save/load/travel.
- For Quill selection, sparkle/audio plays around the click while Quill receives exactly one original `FStatement` through its existing selection delegate.

### Native Cosmic Orrery menu contract
- `AOrreryMainMenuGameMode` remains the action authority.
- `DA_OrreryRegistry` remains destination/unlock authority.
- CommonUI selection broadcasts a presentation event to a 3D Orrery actor; that actor may rotate rings, move a menu camera, adjust material glow, and trigger Niagara, but cannot travel or mutate saves.
- Confirm returns to the existing GameMode/widget action path; 3D presentation does not duplicate execution.
- Reduced-motion mode freezes or scales orbital camera/material/Niagara motion while preserving focus and legibility.

### Quill presentation contract
Project-owned widgets must subclass Quill's `UDialogBox`, `USelectionBox`, and `UBackgroundBox` and be selected through `FScriptSettings`. Quill remains dialogue/choice/story-flow authority. The project widgets own layout, focus, input affordances, animation, audio, and `AddToViewportAtLayer`; they do not independently increment the interpreter.
