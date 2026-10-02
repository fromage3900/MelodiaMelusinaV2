---
name: loading-screen
description: Configure and display movie/widget loading screens during level transitions using the Ascent Loading Screen (ALS) module.
globs: []
alwaysApply: false
---

# Loading Screen — ACF Ultimate

The **Ascent Loading Screen (ALS)** module shows a loading screen (a movie and/or a UMG widget) automatically while a new level streams in. It is driven by `UALSLoadingScreensSubsystem` — a `UGameInstanceSubsystem` that hooks into the engine's `PreLoadMap`/`PostLoadMapWithWorld` delegates and feeds Unreal's `MoviePlayer` (`FLoadingScreenAttributes`). All behaviour is configured from one project-settings page (`UALSLoadingScreenSettings`); you normally don't write code — you set up a widget plus settings and the subsystem does the rest.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Loading screen settings | `UALSLoadingScreenSettings` | **Project Settings → Plugins → Ascent Loading Screens** | Master on/off switch, attributes, widget class |
| Loading widget | `UUserWidget` (your WBP) | `/AscentCombatFramework/UITools/.../` | UMG drawn on top of the loading movie |
| Loading subsystem | `UALSLoadingScreensSubsystem` | Runtime (auto-created) | Begins/ends the loading screen, exposes `OnMapLoaded` |
| Attributes struct | `FALSLoadingScreenAttributes` | Inside the settings | Timing, playback type, movie paths |

> **Never edit sample assets.** Duplicate the sample loading WBP into `Content/YourGame/UI/Loading/` and assign **your copy** in Project Settings.

### Key classes

| Class | Role |
|---|---|
| `UALSLoadingScreensSubsystem` | `GameInstanceSubsystem`; listens to map-load delegates, sets up the movie player, removes the screen |
| `UALSLoadingScreenSettings` | `UDeveloperSettings` (config = Plugins); holds `EnableLoadingScreen`, `LoadingScreenAttributes`, `LoadingWidget` |
| `FALSLoadingScreenAttributes` | Timing + movie config struct |

---

## 2 — Setup / Configuration

### A. Create your loading widget

1. Duplicate the sample loading screen WBP (or right-click → **Widget Blueprint** if none exists).
2. Save it under `Content/YourGame/UI/Loading/WBP_LoadingScreen`.
3. Design the widget (background, spinner, tip text, progress). It is drawn on top of any movie.

### B. Configure the settings page

Open **Project Settings → Plugins → Ascent Loading Screens** and set:

- **`EnableLoadingScreen`** — master toggle; must be `true` for the subsystem to act.
- **`LoadingWidget`** — your `WBP_LoadingScreen` class.
- **`LoadingScreenAttributes`** — expand and configure (see table below).

### C. `FALSLoadingScreenAttributes` fields

| Field | Default | Meaning |
|---|---|---|
| `MinimumLoadingScreenDisplayTime` | `5.0` | Minimum seconds the screen stays up (`-1` = no minimum) |
| `LoadingScreenRemovalDelay` | `2.0` | Extra delay after load completes (hides asset streaming pop-in) |
| `bAutoCompleteWhenLoadingCompletes` | `true` | Auto-dismiss as soon as the map finishes loading |
| `bWaitForManualStop` | `false` | If `true`, the screen stays until you call `RemoveLoadingScreen()` |
| `bAllowInEarlyStartup` | `false` | Allow the screen during very early engine startup |
| `bAllowEngineTick` | `false` | Tick the engine while loading (keeps animations moving) |
| `PlaybackType` | `MT_Normal` | `EMoviePlaybackType` for movie files |
| `MoviePaths` | `[]` | MP4 file names (no extension) in `Content/Movies/` |

> Movie files must be **MPEG-4 (.mp4)** placed in `Content/Movies/`. Enter the path/name **without** the `.mp4` extension.

---

## 3 — Core Workflow / Runtime API

The subsystem auto-shows the screen on level transitions — no code needed for the common case. For manual control (e.g. cutscenes, manual streaming), grab the subsystem:

```
// C++
UALSLoadingScreensSubsystem* LoadingSub =
    GetGameInstance()->GetSubsystem<UALSLoadingScreensSubsystem>();
```

```
// Blueprint: Get Game Instance → Get Subsystem (UALSLoadingScreensSubsystem)
```

### Subsystem API

| Function | Purpose |
|---|---|
| `SetLoadingScreensEnabled(bool)` | Enable/disable the subsystem at runtime |
| `IsEnabled()` | Returns whether the subsystem is currently active |
| `RemoveLoadingScreen()` | Dismiss the screen (respects removal delay) — required when `bWaitForManualStop = true` |
| `RemoveLoadingScreenImmediate()` | Dismiss instantly, no delay |
| `OnMapLoaded` (delegate) | `BlueprintAssignable`; fires when the new map has finished loading |

### Typical manual flow

```
// Force a long movie that you stop yourself:
//  1. Set bWaitForManualStop = true in settings
//  2. Open the level (UGameplayStatics::OpenLevel)
//  3. When your scene is ready:
LoadingSub->RemoveLoadingScreen();
```

### Reacting to load completion

```
// Bind in BeginPlay of your GameInstance / HUD:
LoadingSub->OnMapLoaded.AddDynamic(this, &UMyClass::HandleMapLoaded);
```

---

## 4 — Wire to Characters / Blueprints

The loading screen is **global**, not per-character, so wiring lives at the GameInstance / level-flow layer:

1. Make sure the project uses the default `GameInstance` (or your own subclass) — the subsystem is created automatically; no manual registration.
2. Trigger transitions with `Open Level` (or your map-travel logic). The subsystem intercepts `PreLoadMap` and shows the screen automatically when `EnableLoadingScreen` is `true`.
3. To gate gameplay until the world is ready, bind to `OnMapLoaded` (e.g. enable input, fade in HUD, start music).
4. For "press any key to continue" style screens, set `bWaitForManualStop = true` and call `RemoveLoadingScreen()` from your loading WBP on input.

---

## 5 — Verify

**Checklist before testing:**

- [ ] `EnableLoadingScreen` is `true` in Project Settings → Ascent Loading Screens.
- [ ] `LoadingWidget` points to **your duplicated** WBP under `Content/YourGame/`.
- [ ] Any movie file is an `.mp4` inside `Content/Movies/`, referenced in `MoviePaths` **without** extension.
- [ ] Level transitions use `Open Level` (so the subsystem can intercept them).
- [ ] If `bWaitForManualStop` is `true`, something calls `RemoveLoadingScreen()`.
- [ ] Project uses the standard GameInstance (subsystem auto-instantiates).

**Common failures:**

| Symptom | Fix |
|---|---|
| No loading screen appears | `EnableLoadingScreen` is `false`, or subsystem disabled via `SetLoadingScreensEnabled(false)` |
| Movie never plays | File not in `Content/Movies/`, wrong name, or `.mp4` extension included in `MoviePaths` |
| Screen never goes away | `bWaitForManualStop` is `true` but `RemoveLoadingScreen()` is never called |
| Screen flashes too quickly | Increase `MinimumLoadingScreenDisplayTime` / `LoadingScreenRemovalDelay` |
| Widget shows but animations frozen during load | Enable `bAllowEngineTick` |
| Pop-in visible after screen closes | Increase `LoadingScreenRemovalDelay` to mask asset streaming |
