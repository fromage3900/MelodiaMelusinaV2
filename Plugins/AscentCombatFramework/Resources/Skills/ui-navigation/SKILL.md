---
name: ui-navigation
description: Manage Common UI layer stacks, a tag-based widget registry, gamepad-navigable pages, and "Spawn Widget By Tag" with the ACF UI Navigation System (ANS) module.
globs: []
alwaysApply: false
---

# UI Navigation — ACF Ultimate

The **UI Navigation System (ANS)** is the ACF layer on top of **Common UI**. `UANSUIPlayerSubsystem` (a `UGameInstanceSubsystem`) owns **layer stacks** (`UCommonActivatableWidgetStack`), spawns widgets **by GameplayTag** via the **Widget Registry** (`UANSUIWidgetRegistryDataAsset`), and centralizes pause/input-lock/HUD-hide behaviour. `UANSNavPageWidget` is the base full-screen page with gamepad focus management and page-to-page navigation. The rule: **gameplay code passes a `UI.Widget.*` tag, never a widget class**. See `Docs/ACFCommonUILayers_Wiki.md`.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Widget registry | `UANSUIWidgetRegistryDataAsset` | `/Game/FullSample/Integrations/Ultimate/UI/DA_ACFWidgetRegistry` | Maps `UI.Widget.*` tags → widget class + layer + pause/input flags |
| HUD with layers | `UCommonActivatableWidget` HUD | `/AscentCombatFramework/UITools/ANS_DefaultHUD_WBP` | Hosts the HUD/Default/Popup `CommonActivatableWidgetStack`s and registers them |
| Nav page | `UANSNavPageWidget` | Sample pages under `/AscentCombatFramework/UITools/` | Full-screen, gamepad-navigable menu page |
| Nav widget | `UANSNavWidget` | Children of pages | Focusable element for gamepad navigation |
| Popup | `UANSNavPopUpWidget` | Sample modals | Modal page (push to `UI.Layer.Popup`) |

> **Never edit sample assets.** Duplicate `DA_ACFWidgetRegistry` and `ANS_DefaultHUD_WBP` into `Content/YourGame/UI/` and customize your copies.

### Key classes

| Class | Role |
|---|---|
| `UANSUIPlayerSubsystem` | GameInstance subsystem: `SpawnWidgetByTag`, `RegisterLayer`, pause/input, layer visibility, navbar dispatch |
| `UANSUIWidgetRegistryDataAsset` | `WidgetsByTag` (`FANSWidgetConfig`) + `LayerConfigs` (`FANSUILayerConfig`) |
| `FANSWidgetConfig` | Per-widget: `WidgetClass`, `LayerTag`, `bPauseGame`, `bLockGameInput` |
| `UANSNavPageWidget` | Page base: focus, `GoToWidget`/`GoToPreviousWidget`, `SetupWithActor/Component`, `OnWidgetRemoved` |
| `UANSNavbarFunctionLibrary` | Static helpers for action/key icons |

---

## 2 — Setup / Configuration

1. **Duplicate the registry:** copy `/Game/FullSample/Integrations/Ultimate/UI/DA_ACFWidgetRegistry` → `Content/YourGame/UI/DA_ACFWidgetRegistry`.
2. **Assign it:** **Project Settings → Plugins → Ascent UI Settings → Navigation → Widget Registry Asset** → your copy. Set **Default Layer Tag** → `UI.Layer.Default`. (Without this, `SpawnWidgetByTag` logs *"Widget Registry not set"* and returns null.)
3. **HUD layers (already wired in the sample):** `ANS_DefaultHUD_WBP` holds three `UCommonActivatableWidgetStack`s and on Construct calls `Get Game Instance → Get Subsystem (ANS UI Player Subsystem) → RegisterLayer` for each:
   ```
   UI.Layer.HUD      → always-on overlays (compass, bars, prompts)
   UI.Layer.Default  → full-screen menus (inventory, pause, dialogue)
   UI.Layer.Popup    → modals on top
   ```
   The **first** layer registered becomes the default fallback. Duplicate the HUD only if you need a custom layout; keep the three stacks + `RegisterLayer` calls. Point your `AACFHUD` HUD Class to your copy.
4. **Configure registry rows** in your duplicated `DA_ACFWidgetRegistry`:
   - **Widgets** (`WidgetsByTag`): each `UI.Widget.*` tag → `WidgetClass` (menus parent `UANSNavPageWidget`), `LayerTag` (empty = default), `bPauseGame`, `bLockGameInput`. HUD/overlays: both flags **false**.
   - **Layers** (`LayerConfigs`): each `UI.Layer.*` → `HidesLayers` (e.g. `UI.Layer.Default` hides `[UI.Layer.HUD]`).
   - Custom menus: add a tag under `UI.Widget` in GameplayTags, then add a registry row.

---

## 3 — Core Workflow / Runtime API

Get the subsystem: `Get Game Instance → Get Subsystem (ANS UI Player Subsystem)`.

### Spawn by tag (primary path)

```
// Most common — registry decides layer, pause, and input lock:
UCommonActivatableWidget* W = Subsystem->SpawnWidgetByTag(
    FGameplayTag::RequestGameplayTag("UI.Widget.PauseMenu"));

// With context (chest, vendor, NPC) → calls SetupWithActor on the page:
Subsystem->SpawnWidgetByTagWithActor(
    FGameplayTag::RequestGameplayTag("UI.Widget.ChestWidget"), ChestActor);

// With a component → calls SetupWithComponent:
Subsystem->SpawnWidgetByTagWithComponent(
    FGameplayTag::RequestGameplayTag("UI.Widget.Vendor"), VendorComponent);
```

### Class-based spawns (one-off / debug)

`SpawnInGameWidget`, `SpawnWidgetByClassWithActor`, `SpawnWidgetByClassWithComponent`, `DisplayInGameWidget` — take a `LayerTag`, `bPauseGame`, `bLockGameInput` explicitly. Prefer the registry for anything reusable.

### Close / back

| Function | Purpose |
|---|---|
| `GoToPreviousWidget` | Pop the top page on the active stack (Back/Cancel) |
| `RemoveInGameWidget(widget, bUnlockUIInput, bRemovePause)` | Close a specific widget reference |
| `UANSNavPageWidget::RemoveSelf` | A page closes itself |

### Page navigation (on `UANSNavPageWidget`)

```
Page->GoToWidget(NextPageClass);   // push another page onto the same stack
Page->GoToPreviousWidget();        // pop back
Page->SetStartFocus(NavWidget);    // initial gamepad focus
Page->SetNavigationEnabled(true);  // enable/disable ANS focus handling
// Bind OnWidgetRemoved for cleanup (server RPCs, end interaction) — NOT NativeDestruct
```

### Layers, notifications, navbar, icons

```
Subsystem->SetLayerVisibility(UITag.Layer.HUD, false);  // hide HUD during cutscenes
Subsystem->HideAllLayers(true);                          // hide all UI; false to restore
Subsystem->BroadcastNotification(Text, 3.f);            // toast
Subsystem->RequestAddNavbarAction(ActionTag);           // modify active navbar (also Remove/Set)
UTexture2D* Icon = Subsystem->GetIconForUIAction(ActionTag, ECommonInputType::Gamepad);
Subsystem->TryGetKeysForAction(ActionTag, OutKeys);
```

Delegates: `OnFocusChanged`, `OnNotificationRequested`, `OnNavbarActionTriggered` (+ add/remove/set request delegates the navbar subscribes to).

---

## 4 — Wire to Characters / Blueprints

- **Input (pause/menus):** Enhanced Input action → `Get Subsystem (ANS UI Player Subsystem)` → `Spawn Widget By Tag (UI.Widget.PauseMenu)`. No layer/pause args at the call site.
- **Interactables (chest/vendor/NPC):** on interact → `Spawn Widget By Tag With Actor`/`With Component`, passing the interactable, so the page's `SetupWithActor`/`SetupWithComponent` fires.
- **Abilities / gameplay actions:** call `SpawnWidgetByTagWithActor` from `AGSAction`/abilities to open contextual pages without referencing a widget class.
- **HUD:** duplicate `ANS_DefaultHUD_WBP` only for custom layouts; keep the `RegisterLayer` calls. Assign it as the HUD Class.
- **Pages:** parent menus to `UANSNavPageWidget` (modals to `UANSNavPopUpWidget`), add `UANSNavWidget` children, override `Get Desired Focus Target`, and register the page in your registry.
- **Cutscenes:** `SetLayerVisibility(UI.Layer.HUD, false)` / `HideAllLayers(true)` to suppress UI, restore afterwards.

---

## 5 — Verify

**Checklist before testing:**

- [ ] Duplicated `DA_ACFWidgetRegistry` assigned in **Project Settings → Ascent UI Settings → Navigation**.
- [ ] Default Layer Tag set to `UI.Layer.Default`.
- [ ] HUD registers `UI.Layer.HUD/Default/Popup` via `RegisterLayer` on Construct.
- [ ] Every `UI.Widget.*` tag you spawn has a registry row with a valid `WidgetClass`.
- [ ] Menu pages parent `UANSNavPageWidget`; `Get Desired Focus Target` set for gamepad.
- [ ] Layer hide rules set (e.g. `UI.Layer.Default` hides `UI.Layer.HUD`).
- [ ] HUD/overlay rows have `bPauseGame = false` and `bLockGameInput = false`.

**Common failures:**

| Symptom | Fix |
|---|---|
| "Widget Registry not set" / null spawn | Registry not assigned in Project Settings, or pointing at a deleted asset |
| Spawn returns null + tag warning | Tag missing from **your** registry copy, or a typo in the Gameplay Tag |
| Widget doesn't appear | Registry row points to wrong class; or its layer was never registered by the HUD |
| No gamepad focus | Page not a `UANSNavPageWidget`, or `Get Desired Focus Target` not set |
| HUD visible over a menu | `UI.Layer.HUD` not listed in `HidesLayers` for `UI.Layer.Default` |
| Game doesn't pause | `bPauseGame = false` on that registry row |
| Wrong layer | Fix `LayerTag` on the row; empty uses Default Layer Tag |
| Cleanup runs at wrong time | Bind `OnWidgetRemoved` instead of `Event Destruct`/`NativeDestruct` |
| Input stuck in UI mode after travel | Let the subsystem manage pause/input lock; avoid manual `Add to Viewport` that bypasses it |
