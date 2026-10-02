---
name: ui-tools
description: Build themed, styled UI using the Ascent UI Tools (AUT) module — theme DataAssets, styled base widgets, game user settings, and helper functions.
globs: []
alwaysApply: false
---

# UI Tools — ACF Ultimate

The **Ascent UI Tools (AUT)** module is the styling and base-widget layer that all ACF UMG widgets build on. A single `UAUTThemeDataAsset` holds arrays of styles (buttons, sliders, combo boxes, checkboxes, titles, backgrounds). Custom base widgets (`UAUTTextBlock`, `UAUTRichTextBlock`, `UAUTBorder`, …) each carry a **`StyleIndex`** that looks up the matching style from the active theme, so the whole UI restyles by swapping one DataAsset. `UAUTDeveloperSettings` selects the active theme + default maps + icon tables; `UAUTGameUserSettings` persists player options (audio levels, sensitivity, difficulty).

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| UI theme | `UAUTThemeDataAsset` | `/AscentCombatFramework/UITools/Themes/` | Arrays of styles indexed by `StyleIndex` |
| UI settings | `UAUTDeveloperSettings` | **Project Settings → Plugins → Ascent UI Settings** | Active theme, default menu/new-game maps, icon tables, widget registry |
| User settings | `UAUTGameUserSettings` | Runtime (saved config) | Player audio/sensitivity/difficulty preferences |
| Function library | `UAUTUIFunctionLibrary` | C++/Blueprint static | Style lookups, level/audio helpers |

> **Never edit sample assets.** Duplicate the sample theme DataAsset into `Content/YourGame/UI/Themes/` and point **Ascent UI Settings** at your copy.

### Key classes

| Class | Role |
|---|---|
| `UAUTThemeDataAsset` | `UPrimaryDataAsset`; arrays: `TitlesStyle`, `ButtonsStyle`, `ComboBoxesStyle`, `SpinnersStyle`, `SlidersStyle`, `CheckBoxesStyle`, `Background`, `SpacerStyle` |
| `UAUTDeveloperSettings` | `UDeveloperSettings`; `GetTheme()`, default maps, `GetWidgetRegistryPath()`, `GetDefaultLayerTag()`, icon tables |
| `UAUTGameUserSettings` | `UGameUserSettings`; difficulty, sensitivity, audio volumes, toggle-sprint, invert-Y |
| `UAUTUIFunctionLibrary` | Static helpers: `TryGet*Style`, `GetGameUserSettings`, `GetDefaultMenuLevel`, `SetSoundClassVolume`, `IsValidAndOnScreen` |
| `UAUTTextBlock` / `UAUTRichTextBlock` | `TextBlock`/`RichTextBlock` with `SetStyleIndex` / `UpdateStyle` |
| `UAUTTypeWriteTextBlock` | `UAUTTextBlock` with a typewriter effect (`SetTextWithTypeWriterEffect`) |
| `UAUTBorder` | `UBorder` driven by `StyleIndex` |
| `UAUTRadialMenu` | Pie/radial menu widget (`SetItems`, `AddItem`, `OnItemSelected`) |

---

## 2 — Setup / Configuration

### A. Create your theme

1. Duplicate the sample `UAUTThemeDataAsset` into `Content/YourGame/UI/Themes/DA_MyTheme`.
2. Set the **`ThemeTag`** (a `FGameplayTag`, e.g. `UI.Theme.Default`).
3. Fill the style arrays. **Array order matters** — the index in each array is the `StyleIndex` widgets reference:
   - `TitlesStyle` → `FAUTBaseTextStyle` (font + `NormalColor`).
   - `ButtonsStyle` → `FAUTButtonStyle` (`ButtonStyle` + `FontStyle`).
   - `SlidersStyle`, `ComboBoxesStyle`, `SpinnersStyle`, `CheckBoxesStyle` → hoverable styles (each can carry `PressedSound` / `HoveredSound`).
   - `Background`, `SpacerStyle` → `FSlateBrush` arrays.

### B. Assign the theme

1. Open **Project Settings → Plugins → Ascent UI Settings**.
2. Set **`ThemesAsset`** to your `DA_MyTheme`.
3. Optionally set `DefaultMenuMap`, `DefaultNewGameMap`, `DefaultSoundClasses`, `WidgetRegistryAsset`, `DefaultLayerTag`, `IconsByTag`, and per-platform `KeysConfigByPlatform`.

### C. Use the styled widgets

1. In any WBP, add `UAUTTextBlock` / `UAUTRichTextBlock` / `UAUTBorder` instead of the stock UMG versions.
2. Set each widget's **`StyleIndex`** to the index of the desired style in the theme arrays.
3. Set `bUseStyle = true` to apply the theme (set `false` to keep manual styling).

---

## 3 — Core Workflow / Runtime API

### Restyling at runtime

```
// Re-apply styles after changing StyleIndex (C++ or Blueprint):
MyTextBlock->SetStyleIndex(2);   // calls UpdateStyle internally
MyBorder->SetStyle(1);
```

### Typewriter text

```
TypeWriter->SetTextWithTypeWriterEffect(FText::FromString("Hello..."), 0.03f);
TypeWriter->SkipTypewriterEffect();              // jump to full text
// bind OnTypewriterComplete to know when typing finishes
```

### Function library lookups

```
FAUTButtonStyle Style;
if (UAUTUIFunctionLibrary::TryGetButtonStyle(0, Style)) { /* use Style */ }

UAUTGameUserSettings* Settings = UAUTUIFunctionLibrary::GetGameUserSettings();
TSoftObjectPtr<UWorld> Menu = UAUTUIFunctionLibrary::GetDefaultMenuLevel();
UAUTUIFunctionLibrary::SetSoundClassVolume(MasterSoundClass, 0.8f);
bool bVisible = UAUTUIFunctionLibrary::IsValidAndOnScreen(MyWidget);
```
Available style getters: `TryGetButtonStyle`, `TryGetSliderStyle`, `TryGetSpinnerStyle`, `TryGetComboBoxStyle`, `TryGetCheckBoxStyle`, `TryGetTitleStyle`, `TryGetBackgroundStyle`, `TryGetSpacerStyle`.

### Player settings (`UAUTGameUserSettings`)

| Function | Purpose |
|---|---|
| `GetPreferredDifficultyLevel` / `SetPreferredDifficultyLevel` | Difficulty as `FGameplayTag` (broadcasts `OnDifficultyPreferenceChanged`) |
| `GetAxisSensitivity` / `SetAxisSensitivity` | Mouse + gamepad sensitivity (`FVector2D`) |
| `GetIsYAxisInverted` / `SetYAxisInverted` | Invert look Y |
| `GetAudioVolumeLevels` / `SetAudioVolumeLevels` | Per-channel volume array |
| `GetToggleSprint` / `SetToggleSprint` | Toggle vs hold sprint |
| `OnGameSettingsApplied` (delegate) | Fires after `ApplySettings` |

### Radial menu

```
RadialMenu->SetItems(MyItems);                 // TArray<FAUTRadialMenuItem>
RadialMenu->AddItem(NewItem);
RadialMenu->OnItemSelected.AddDynamic(this, &UMyHUD::HandleRadialSelection);
// Bind the menu's MenuCanvas (meta=BindWidget) in the WBP.
```

---

## 4 — Wire to Characters / Blueprints

1. **Theme** is global: set it once in Ascent UI Settings; every AUT widget reads it automatically.
2. **Settings menu WBP:** drive options through `UAUTUIFunctionLibrary::GetGameUserSettings()` and the `Set*` functions, then call `ApplySettings`. Bind `OnGameSettingsApplied` / `OnDifficultyPreferenceChanged` to refresh UI.
3. **Per-widget styling:** designers only set `StyleIndex` — no per-widget color/font edits — so a theme swap restyles the whole UI consistently.
4. The widget registry / layer tags (`WidgetRegistryAsset`, `DefaultLayerTag`) are consumed by the UI Navigation system; set them here so spawned in-game widgets land on the right HUD layer.

---

## 5 — Verify

**Checklist before testing:**

- [ ] Theme DataAsset is duplicated into `Content/YourGame/UI/Themes/` and assigned in Ascent UI Settings (`ThemesAsset`).
- [ ] Each style array has entries at the indices your widgets reference via `StyleIndex`.
- [ ] Widgets use the `UAUT*` base classes (not stock UMG) where theming is wanted, with `bUseStyle = true`.
- [ ] `ThemeTag` is a valid GameplayTag.
- [ ] Settings menus call `GetGameUserSettings()` + `ApplySettings`.
- [ ] `RadialMenu`'s `MenuCanvas` BindWidget is satisfied in the WBP.

**Common failures:**

| Symptom | Fix |
|---|---|
| Widget ignores the theme | `bUseStyle` is `false`, or it's a stock UMG widget instead of `UAUT*` |
| Wrong style applied | `StyleIndex` points to a missing/wrong entry in the theme array |
| Style change not visible at runtime | Call `SetStyleIndex` / `UpdateStyle` (or `SetStyle` on border) after editing |
| Theme not loading | `ThemesAsset` in Ascent UI Settings is empty or points to the sample |
| Settings don't persist | `ApplySettings` / `SaveSettings` not called after `Set*` |
| Radial menu compile/bind error | `MenuCanvas` (`meta = BindWidget`) missing in the WBP |
| Typewriter shows full text instantly | Char delay too small, or `SkipTypewriterEffect` called immediately |
