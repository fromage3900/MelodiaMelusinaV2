# Extract BP_Battle_Rhythm Reusable Components — Design Doc

**Based On:** `WBP_Battle_Rhythm` (compiled at `/Game/Melodia/UI/`, verified 2026-08-03)  
**Design Date:** 2026-08-13  
**Integrates With:** `BP_WidgetComponent`, `WidgetStyleSheet.json`, `BP_CommandPhaseWBP`

## 1. Current WBP_Battle_Rhythm Hierarchy (Verified)

```
WBP_Battle_Rhythm (UserWidget root)
├─ HitWindow (ProgressBar or Border)
│   • Brush/Color: Hardcoded (needs theme migration)
│   • Purpose: Shows timing window/early/late zone
├─ JudgementText (Text Block)
│   • Text: "PERFECT" / "GREAT" / "GOOD" / "MISS"
│   • Color: Hardcoded (needs theme migration)
│   • Font: Hardcoded (needs theme migration)
├─ ComboText (Text Block)
│   • Text: "COMBO: x5" / "COMBO: x0"
│   • Color: Hardcoded (needs theme migration)
├─ ClockSourceText (Text Block)
│   • Text: "00:00:00" (game clock)
│   • Color: Hardcoded (needs theme migration)
└─ (Root Canvas Panel) — hosts all above
```

**161 nodes, 153 connections, 0 errors** — verified compiled/saved.

## 2. Reusable Component Extraction

### A. `BP_TimingWindow` (ProgressBar/Border)

**Purpose:** Shows the timing window (early/great/good/late/miss zone).  
**Extends:** `BP_WidgetComponent`  
**Theme Integration:**
- `Background Color` → `WidgetStyleSheet.json` `colorPalette.background`
- `Fill Color` → `GetThemeColor("primary")` for active window, `GetThemeColor("error")` for miss zone
- `Border Color` → `GetThemeColor("secondary")`

**Functions:**
- `SetWindowState(State: EWindowState)` where:
  - `EWindowState.Normal` — full visibility (default)
  - `EWindowState.Early` — highlight early segment
  - `EWindowState.Late` — highlight late segment
  - `EWindowState.Miss` — reduce to 0% width, show error color
- `UpdateTimingDisplay(Timing: Float)` — receives timing value from Quartz/VRTC, sets progress bar %

**UMG Layout:**
```
ProgressBar (or Border withCachedBrush)
├─ Fill (progress direction left→right or right→left)
│   • Brush: GetEffectiveBrush based on WindowState
│   • Percentage: 1.0 (full) → 0.0 (miss)
└─ Border (optional)
    • Thickness: GetThemeSpacing("sm")
    • Color: GetThemeColor("secondary")
```

### B. `BP_JudgementText` (Text Block)

**Purpose:** Shows the judgement result (PERFECT / GREAT / GOOD / MISS).  
**Extends:** `BP_WidgetComponent`  
**Theme Integration:**
- `Text Color` → `GetThemeColor()` based on judgement level
- `Font` → `WidgetStyleSheet.json` typography `body`
- `Justification` → Center

**Judgement-to-Color Mapping:**
| Judgement | Color | `GetThemeKey()` |
|---|---|---|
| `PERFECT` | Success green | `"success"` → `#4ECDC4` |
| `GREAT` | Success green | `"success"` → `#4ECDC4`` |
| `GOOD` | Primary orange | `"primary"` → `#FF6B35` |
| `MISS` | Error red | `"error"` → `#FF4757` |

**Functions:**
- `SetJudgement(Judgement: EJudgement)` — sets text + color + animation
- `ClearJudgement()` — reset to empty/neutral

**Animations:**
- `AnimJudgementPop` — pop-in when judgement changes (150ms ease-out)
- `AnimJudgementFade` — fade out after 2s

### C. `BP_ComboCounter` (Text Block)

**Purpose:** Displays current combo count.  
**Extends:** `BP_WidgetComponent`  
**Theme Integration:**
- `Text Color` → `GetThemeColor("primary")` normally, `GetThemeColor("success")` on combo break/reset threshold
- `Font` → `WidgetStyleSheet.json` typography `body` or `h3` for large numbers

**Functions:**
- `AddCombo()` — increment combo, play `AnimComboPop`, update display
- `ResetCombo()` — reset to 0, play `AnimComboReset`
- `SetCombo(Count: Int)` — set to specific value

**Animations:**
- `AnimComboPop` — number pops up slightly then settles
- `AnimComboReset` — number drops/fades to 0

### D. `BP_ClockSource` (Text Block)

**Purpose:** Shows game-internal clock (HH:MM:SS format).  
**Extends:** `BP_WidgetComponent`  
**Theme Integration:**
- `Text Color` → `GetThemeColor("secondary")`
- `Font` → `WidgetStyleSheet.json` typography `caption`

**Functions:**
- `StartClock()` — bind to GameMode's game time event
- `StopClock()` — stop ticking
- `SetTime(hours, minutes, seconds)` — manual override

## 3. Integration With New Phase WBPs

### A. `BP_CommandPhaseWBP` — Uses Extracted Components

```text
WBP_CommandPhaseWBP hierarchy:
├─ TimingWindow: BP_TimingWindow (floating window near bottom-center)
├─ Judgement: BP_JudgementText (center, shows PERFECT/GOOD/MISS)
├─ ComboCounter: BP_ComboCounter (top-left)
└─ ClockSource: BP_ClockSource (top-right, optional)
```

**Event Graph additions:**
- `OnButtonSelected` → `SetJudgement("PERFECT")` (or GREAT/GOOD/MISS based on timing)
- `OnTimingWindowUpdate` → `TimingWindow.SetWindowState()` + `TimingWindow.UpdateTimingDisplay()`
- `OnComboIncrement` → `ComboCounter.AddCombo()`
- `OnClockTick` → `ClockSource.SetTime()`

### B. `BP_EnemyPhaseWBP` — Uses Extracted Components (Same Structure, Different Prompts)

Same hierarchy as Command phase, but:
- Judgement text: "EVASIVE" / "COUNTER" / "BLOCK" instead of "PERFECT"/"GOOD"/"MISS"
- Timing window: enemy attack indicators vs player commands
- Combo counter: still tracks player successful deflections

### C. `BP_ResultsPhaseWBP` — Uses Partial Components

Uses:
- `BP_ComboCounter` (shows final max combo)
- Does NOT use: `BP_TimingWindow` (no real-time timing in results)
- Does NOT use: `BP_JudgementText` (results show static rank, not live judgement)
- Uses `BP_ClockSource` optionally (show total play time)

## 4. Migration Path (WBP_Battle_Rhythm → New Components)

| Existing WBP_Battle_Rhythm Element | New Reusable Component | Migration Steps |
|---|---|---|
| `HitWindow` (ProgressBar) | `BP_TimingWindow` | 1. Create BP_TimingWindow extends BP_WidgetComponent<br>2. Copy progress bar logic + theme bindings<br>3. Replace HitWindow component reference → BP_TimingWindow<br>4. Call RefreshTheme() in Event BeginPlay |
| `JudgementText` (Text Block) | `BP_JudgementText` | 1. Create BP_JudgementText extends BP_WidgetComponent<br>2. Copy text + colour logic + judgement mapping<br>3. Replace JudgementText component reference → BP_JudgementText<br>4. Call SetJudgement() on relevant events |
| `ComboText` (Text Block) | `BP_ComboCounter` | 1. Create BP_ComboCounter extends BP_WidgetComponent<br>2. Copy combo logic + animation<br>3. Replace ComboText component reference → BP_ComboCounter<br>4. Bind AddCombo/ResetCombo to game events |
| `ClockSourceText` (Text Block) | `BP_ClockSource` | 1. Create BP_ClockSource extends BP_WidgetComponent<br>2. Copy clock ticking logic<br>3. Replace ClockSourceText component reference → BP_ClockSource<br>4. StartClock() in Event BeginPlay |

## 5. Updated WBP_Battle_Rhythm Post-Migration

**New Hierarchy:**
```
WBP_Battle_Rhythm (UserWidget, but now delegates to components)
├─ TimingWindow: BP_TimingWindow (handles window display + theme)
├─ Judgement: BP_JudgementText (handles PERFECT/GOOD/MISS + theme)
├─ ComboCounter: BP_ComboCounter (handles combo count + theme + anim)
├─ ClockSource: BP_ClockSource (handles live clock + theme)
└─ (Root) — minimal logic; delegates to children
```

**Event Graph Simplification:**
- All theme handling moved to components via `RefreshTheme()`, `GetThemeColor()`, `GetEffectiveBrush()`
- Event graph now just routes: `OnTimingHit` → `TimingWindow.SetWindowState(Normal)` etc.
- **Result:** 40-50% fewer nodes in WBP_Battle_Rhythm (logic moved to reusable components)

## 5. Versioning & Deprecation

All new components embed version info:
```
--- Begin Widget Version Info ---
Version: 1.0.0
Updated: 2026-08-13
Author: Agent System
DependsOn: BP_WidgetComponent_1.0.0
BreakingChanges: None
--- End Widget Version Info ---
```

## 6. Quick-Start Checklist

- [ ] Create `BP_TimingWindow` (extends BP_WidgetComponent)
- [ ] Create `BP_JudgementText` (extends BP_WidgetComponent)
- [ ] Create `BP_ComboCounter` (extends BP_WidgetComponent)
- [ ] Create `BP_ClockSource` (extends BP_WidgetComponent)
- [ ] Update `WBP_Battle_Rhythm`: replace 4 child components with new BP*s
- [ ] Call `RefreshTheme()` in each new BP's Event BeginPlay
- [ ] Verify: WBP_Battle_Rhythm still compiles (0 errors)
- [ ] Run: `GetThemeColor("primary")` matches `WidgetStyleSheet.json` `#FF6B35`
- [ ] Update `UI_ASSET_INVENTORY_2026-08-03.md` — mark components as "Available"

## 7. Related Docs

- `BP_WidgetComponent_Base_Design.md` — base class for all above
- `WidgetStyleSheet.json` — theme data for all above
- `BP_CommandPhaseWBP` — uses these components in phase layout
- `BP_EnemyPhaseWBP` — uses same components, different prompts
- `BP_ResultsPhaseWBP` — uses ComboCounter from this extraction
