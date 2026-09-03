# BP_WidgetComponent Base Class — Design Document

**Version:** 1.0.0  
**Created:** 2026-08-13  
**Author:** Agent System  
**Based On:** `WidgetStyleSheet.json` (created same date)

## Overview

`BP_WidgetComponent` is the base class for all Melodia UI widgets. It provides:
- Theme color lookup from `WidgetStyleSheet.json`
- Safe area detection (UE5)
- Standard focus navigation
- State animation player
- Brush resolution for button variants

All other Melodia WBPs should extend this class rather than `UserWidget` directly.

---

## 1. Class Variables (Defaults)

### EWidgetState (Enum)
| Name | Description |
|---|---|
| `Normal` | Default state (no hover/press) |
| `Hovered` | Mouse cursor over widget |
| `Pressed` | Mouse button held down |
| `Disabled` | Widget is disabled (grayed out) |
| `DisabledHovered` | Disabled + mouse over |

### FThemeData (Struct)
| Field | Type | Description |
|---|---|---|
| `colorPrimary` | `LinearColor` | From `WidgetStyleSheet.json` `colorPalette.primary` |
| `colorSecondary` | `LinearColor` | From `WidgetStyleSheet.json` `colorPalette.secondary` |
| `colorBackground` | `LinearColor` | From `WidgetStyleSheet.json` `colorPalette.background` |
| `fontFamily` | `String` | From `WidgetStyleSheet.json` `typography.fontFamily` |
| `fontSizeBody` | `Float` | From `WidgetStyleSheet.json` `typography.fontSize.body` |
| `spacingUnit` | `Float` | From `WidgetStyleSheet.json` `spacing.unit` |

### FBrushCache (Struct)
| Field | Type | Description |
|---|---|---|
| `brushNormal` | `Brush` | Cached normal state brush |
| `brushHovered` | `Brush` | Cached hovered state brush |
| `brushPressed` | `Brush` | Cached pressed state brush |
| `brushDisabled` | `Brush` | Cached disabled state brush |

---

## 2. Construction Script

**Runs once at edit time.** Perform:

1. **Read `WidgetStyleSheet.json`** from `/Game/Content/UI/WidgetStyleSheet.json`
   - Use `Asset Player` or `Dynamic Load Asset` node
   - Parse JSON via **`String >> Split`** macro or **`Blueprint JSON Library`**
   - Store parsed `ThemeData` struct

2. **Initialize Brush Cache** using `Generate Button Brushes` function (see §3)

3. **Call `RefreshTheme()`** to apply sheet colors to widget materials

---

## 3. Functions (Graph-Usable)

### `GetEffectiveBrush(State: EWidgetState) → Brush`

**Returns the correct brush for the given state.**

**Logic:**
```pseudo
switch State:
  case Normal:       return BrushNormal
  case Hovered:    return BrushHovered
  case Pressed:    return BrushPressed
  case Disabled:   return BrushDisabled
  case DisabledHovered: return BrushHovered (overlay on Disabled)
```

**Also applies:** `ThemeData.colorPrimary` as tint, `spacingUnit` as padding.

**Cache:** Results stored in `FBrushCache` so recompute only when state changes.

---

### `GetThemeColor(ThemeKey: String) → LinearColor`

**Reads a color from the loaded `WidgetStyleSheet.json`.**

**Supported Keys (from `colorPalette`):**
- `primary`, `secondary`, `accent`, `background`, `surface`, `error`, `success`, `warning`

**Supported Keys (from `shadow`):**
- `sm`, `md`, `lg`

**Example Call:** `GetThemeColor("primary")` → returns `#FF6B35` as `LinearColor`

**Fallback:** If key not found, returns `WidgetStyleSheet.json` default (red `primary`).

---

### `IsInSafeArea() → Boolean`

**UE5 Verdict / Safe Area check.**

**Logic:**
- If running in **Shipped** build → return `True` (already in safe area)
- If running in **Play In Editor** → use `UVerdict` component or `USafeAreaBox`:
  - Get `GameSafeArea` from `owner->GetPlayerOwner(0)->GetPlayerCameraManager()->GetCameraSafeArea()`
  - Return `True` if widget root is inside those bounds
- **Editor mode:** Always return `True` (safe to design)

**Use Case:** Prevent text/buttons from being cut off on mobile/notch displays.

---

### `NavigateFocus(Direction: ENavDirection) → Widget`

**Circular/grid focus movement for gamepad/keyboard traversal.**

**Direction Enum:**
| Value | Meaning |
|---|---|
| `Up` | Move focus widget above current |
| `Down` | Move focus widget below current |
| `Left` | Move focus widget to the left |
| `Right` | Move focus widget to the right |

**Logic:**
1. Get all focusable widgets in hierarchy (child WBPs with `bIsFocusable = True`)
2. Compute position based on `Direction`
3. If valid target exists → `SetKeyboardFocus()` on it
4. If no valid target → wrap around (circular) or stay put

**Typical Use:** MainMenu → PauseMenu → HUD focus traversal.

---

### `PlayStateAnimation(State: EWidgetState) → Animator`

**Plays the correct animation for the given state.**

**Animation Names (AnimMontage or UMG AnimSequence):**
| State | Animation Asset | Duration |
|---|---|---|
| `Normal` | `AnimIdle` | 0ms (hold frame) |
| `Hovered` | `AnimHover` | 150ms ease-out |
| `Pressed` | `AnimPress` | 100ms ease-in then hold |
| `Disabled` | `AnimDisabled` | Loop 400ms fade |
| `DisabledHovered` | `AnimDisabledHover` | 150ms ease-out on top of Disabled |

**Logic:**
- Stop any running animation
- Play new montage/sequence named `Anim_{State}`
- Set `PlayRate` based on `ThemeData` (faster for Pressed, slower for Disabled)

---

### `RefreshTheme() → Void`

**Re-reads `WidgetStyleSheet.json` and updates all colors/brushes.**

**Call this:**
- Construction Script (once)
- Any time the user changes the style sheet asset
- On **PostInitialize** for each widget that extends this base

**Also:** Re-caches `FBrushCache` via `GenerateButtonBrushes()`.

---

## 4. Brush Generation (Construction Script)

### `GenerateButtonBrushes() → FBrushCache`

**Creates 4 brushes from a single `Texture2D` + `LinearColor` tint.**

**Input:** 
- `Texture2D` — base icon/button asset (e.g., `BP_Button` sprite)
- `LinearColor` tints from `ThemeData` (primary for normal, disabled for disabled)

**Output:** `FBrushCache` with 4 entries:
- `brushNormal` = `MakeBrush(baseTex, Theme.colorPrimary)`
- `brushHovered` = `MakeBrush(baseTex, Theme.colorSecondary)`
- `brushPressed` = `MakeBrush(baseTex, Theme.colorPrimary + 0.1 brightness delta)`
- `brushDisabled` = `MakeBrush(baseTex, Theme.colorSecondary * 0.5)`

**Formula:** `MakeBrush(Texture, Tint)` modulates the texture with the color.

**Cache:** Stored in `FBrushCache` struct member so `GetEffectiveBrush()` doesn't regenerate every tick.

---

## 5. Typical Construction Hierarchy

```
Class: BP_WidgetComponent (extends UserWidget)
├─ Components:
│   └─ UMG Root Content (Canvas Panel)
│
├─ Functions (from base):
│   • GetEffectiveBrush(State)
│   • GetThemeColor(Key)
│   • IsInSafeArea()
│   • NavigateFocus(Dir)
│   • PlayStateAnimation(State)
│   • RefreshTheme()
│
├─ Animations (assign in editor):
│   • AnimIdle (Normal)
│   • AnimHover (Hovered)
│   • AnimPress (Pressed)
│   • AnimDisabled (Disabled)
│   • AnimDisabledHover (DisabledHovered)
│
├─ Defaults (apply from WidgetStyleSheet.json):
│   • DefaultState = Normal
│   • bIsFocusable = True (for navigable widgets)
│   • DefaultThemeKey = "primary"
│
└─ Child WBPs (example):
    ├─ BP_Button (extends BP_WidgetComponent)
    ├─ BP_Notification (extends BP_WidgetComponent)
    ├─ BP_ProgressBar (extends BP_WidgetComponent)
    └─ BP_TextBlock (extends BP_WidgetComponent, no animations)
```

---

## 6. Migration Path (Existing WBPs → Base Class)

| Existing BP | New Base | Changes Required |
|---|---|---|
| `WBP_Battle_Rhythm` | `BP_WidgetComponent` | Add `RefreshTheme()` call in Event BeginPlay; extract HitWindow/JudgementText/ComboText brushes via `GetThemeColor` |
| `BP_BattleUI` | `BP_WidgetComponent` | Add `NavigateFocus` for circular menu traversal; add `PlayStateAnimation` for button states |
| `BP_MelodiaRhythmPrompt` | `BP_WidgetComponent` | Use `GetEffectiveBrush` for prompt background; `GetThemeColor` for text colors |
| `WBP_SkillCodex` | `BP_WidgetComponent` | Use `GenerateButtonBrushes` for skill icon frames |
| `BP_InfoDialogue` (stock) | Keep as-is | Do NOT migrate — keep as narrative primitive per inventory doc |
| `BP_YesNoDialogue` (stock) | Keep as-is | Do NOT migrate — keep as narrative primitive per inventory doc |

---

## 7. Version & Breaking Change Policy

**Version:** Embed in every BP comment section:
```unreal
--- Begin Widget Version Info ---
Version: 1.0.0
Updated: 2026-08-13
Author: Agent System
DependsOn: BP_WidgetComponent_1.0.0
BreakingChanges: None
--- End Widget Version Info ---
```

**When incrementing version (e.g., 1.1.0):**
- **Non-breaking:** Add new enum value, new theme key, new function with default params
- **Breaking:** Rename existing function, change enum values, remove struct fields
- **Grace period:** 2 releases before removing deprecated features

**Deprecation Pipeline (5-step, documented in `UI_ASSET_INVENTORY_2026-08-03.md`):**
1. Add `!deprecated` tag to User Comments + Inventory doc
2. 1-release grace period: no new usage, mark as legacy
3. 2-release grace period: update all references → `BP_Legacy*` (read-only)
4. Delete the BP, keep `BP_Legacy*` as reference only
5. Remove from `UI_ASSET_INVENTORY_2026-08-03.md` `Available` table

---

## 8. Quick-Start Checklist (Run After Creating BP)

- [ ] **Create BP_WidgetComponent** class (extends UserWidget)
- [ ] **Paste Construction Script** from §2
- [ ] **Create EWidgetState enum** and FThemeData/FBrushCache structs
- [ ] **Add 5 functions** from §3 to the class
- [ ] **Assign animations** (AnimIdle/Hover/Press/Disabled/DisabledHover) in editor
- [ ] **Set Defaults** (DefaultState=Normal, bIsFocusable=True, DefaultThemeKey="primary")
- [ ] **Child WBPs**: Right-click → "Add Child Class" → select `BP_WidgetComponent`
- [ ] **Update Inventory doc:** `UI_ASSET_INVENTORY_2026-08-03.md` — add version tag to each BP
- [ ] **Run:** `BP_WidgetComponent RefreshTheme()` → verify colors match `WidgetStyleSheet.json`

---

## 8. Integration With Existing Melodia WBPs

| WBP | Integration Step | Priority |
|---|---|---|
| `WBP_Battle_Rhythm` | Call `RefreshTheme()` in Event BeginPlay; use `GetThemeColor` for JudgementText/ComboText colors | P0 (already compiled, just theme-ify) |
| `BP_BattleUI` | Add `NavigateFocus` for main menu → pause menu traversal | P1 |
| `BP_MelodiaRhythmPrompt` | Use `GetEffectiveBrush` for prompt bg; `GetThemeColor` for text | P1 |
| `WBP_SkillCodex` | Use `GenerateButtonBrushes` for icon frames | P2 |
| `BP_InfoDialogue` | Keep as-is (stock primitive) | — |
| `BP_YesNoDialogue` | Keep as-is (stock primitive) | — |

---

**End of Document.**
