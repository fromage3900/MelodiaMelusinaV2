---
name: maps-system
description: Build world maps, minimaps, compass, discoverable locations, fast travel, fog of war, and tracked markers with the ACF Maps System (AMS) module.
globs: []
alwaysApply: false
---

# Maps System — ACF Ultimate

The **Maps System (AMS)** provides a full world-map / minimap / compass stack. `UAMSMapSubsystem` (a `UGameInstanceSubsystem`) is the central registry for **map areas**, **locations**, and **markers**. `AAMSMapArea` actors define the bounds and capture/texture of each map region (with optional **fog of war**); `AAMSMapLocation` actors are discoverable points with optional **fast travel**; `UAMSMapMarkerComponent` (a `UWidgetComponent`) puts any actor on the map/compass; and `UAMSMapWidget` renders a pannable, zoomable map with marker tracking. See `Docs/` for related notes.

---

## 1 — Understand the assets

| Asset | Class | Location (sample) | Purpose |
|---|---|---|---|
| Map area | `AAMSMapArea` | Placed per region in the level | Bounds + texture/render target + fog for one map region |
| Discoverable location | `AAMSMapLocation` | Placed in the world | Discover-on-overlap point with optional fast travel |
| Marker component | `UAMSMapMarkerComponent` | Added to actors (NPCs, quests, POIs) | Shows the owner on map & compass; trackable |
| Standalone marker | `AAMSActorMarker` | Spawned at runtime | Pin a world point (player ping) |
| Map widget | `UAMSMapWidget` | `Content/.../UI/Map/` | Full pannable/zoomable map UI |
| Marker widget | `UAMSMarkerWidget` | `Content/.../UI/Map/` | Icon widget for a single marker |
| Marker icon config | `UAMSMarkersConfigDataAsset` | Project Settings → Ascent Navigation Settings | Marker icon set |

> **Never edit sample assets.** Duplicate the map/marker widgets and the markers config DataAsset into `Content/YourGame/UI/Map/` and customize your copies.

### Key classes

| Class | Role |
|---|---|
| `UAMSMapSubsystem` | GameInstance subsystem: registers areas, locations, markers; tracking; ping spawning |
| `AAMSMapArea` | World→normalized conversion, capture/texture, fog of war (`UpdateFogOfWar`, save/load) |
| `AAMSMapLocation` | Discovery (`DiscoverLocation`), fast travel (`FastTraverlToLocation`, `CanFastTravel`) |
| `UAMSMapMarkerComponent` | Per-actor marker: texture, `MarkerCategory` tags, name/ID, compass visibility, tracking |
| `UAMSMapWidget` | Zoom/pan/cursor, marker hover/highlight/track, fog rendering |
| `UAMSDeveloperSettings` | "Ascent Navigation Settings" — holds the marker icon config path |

---

## 2 — Setup / Configuration

1. **Marker icon config:** duplicate the sample `UAMSMarkersConfigDataAsset` into `Content/YourGame/UI/Map/`, then assign it in **Project Settings → Plugins → Ascent Navigation Settings** (`UAMSDeveloperSettings`).
2. **Define a map area:** place an `AAMSMapArea` covering a region. Set `AreaName`, `AreaSize`, and `TextureType`:
   - `ECustomTexture` → assign a hand-made `Texture`.
   - `ERenderTarget` → assign a `RenderTarget`, then call `GenerateMap` / `GenerateMapTexture` (uses the area's `USceneCaptureComponent2D`) to bake a top-down image.
   - Enable **`EnableFog`** for fog of war (tune `FogWidthPixelsCount`, `FogOfWarBrushMultiplier`).
3. **Add locations:** place `AAMSMapLocation` actors. Set `LocationID`, UI name, `bDiscoverOnPlayerOverlap`, and for fast travel `bCanFastTravel` + `FastTravelLocation`. Each has a built-in `UAMSMapMarkerComponent`.
4. **Map UI:** duplicate the sample `UAMSMapWidget` Blueprint into `Content/YourGame/UI/Map/`. Bind the required `BindWidget` panels (`MapBrush`, `MapMask`, `MapCanvas`, `MapCursor`) and set `MarkersClass`, zoom limits, and input keys. Spawn it through the UI Navigation system (see the `ui-navigation` skill, e.g. `UI.Widget.Map`).

---

## 3 — Core Workflow / Runtime API

### Markers (per actor)

Add `UAMSMapMarkerComponent` to any actor and configure `MarkerTexture`, `MarkerCategory` (Gameplay tags for filtering), `MarkerName`, `MarkerID`, `bShouldRotate`, `bActivateWorldWidget`. It registers itself; you can also drive it:

```
Marker->AddMarker();              // register with the subsystem
Marker->RemoveMarker();           // unregister
Marker->SetTracked(true);         // mark as the tracked quest objective
bool bCompass = Marker->ShowOnCompass();
```

### Subsystem (`UAMSMapSubsystem`)

Get it via `Get Game Instance → Get Subsystem (AMS Map Subsystem)`.

| Function | Purpose |
|---|---|
| `SetCurrentMapArea` / `GetCurrentMapArea` | Choose the active region |
| `GetRegisteredMapArea(FName)` | Look up an area by name |
| `GetLocationByID(FName)` | Find a placed location |
| `GetAllDiscoveredLocation` / `GetAllDiscoveredFastTravelLocation` / `GetAllLocations` | Query locations |
| `GetAllMarkers` / `GetAllMarkersByCategory(tag)` | Query markers |
| `RegisterMarker` / `RemoveMarker` / `RemoveAllMarkersByCategory` | Manage markers |
| `TrackMarker` / `UntrackMarker` / `GetCurrentlytTrackedMarker` / `HasAnyTrackedMarker` | Quest tracking |
| `SpawnMarkerActor(class, worldPos, bProjectToNavmesh)` | Player ping / waypoint |
| `RemoveAllMarkerActors` / `HasAtLeastOneMarkerActor` | Manage pings |
| `DiscoverAllLocation` | Cheat: reveal everything |
| `UpdateDiscovererPosition(worldPos)` | Feed player position (fog/compass) |

Delegates: `OnMapMarkerAdded`, `OnMapMarkerRemoved`, `OnMapAreaChanged`, `OnLocationDiscovered`, `OnTrackedMarkerChanged`.

### Discovery & fast travel (`AAMSMapLocation`)

```
Location->DiscoverLocation(Pawn);     // marks discovered (auto on overlap if bDiscoverOnPlayerOverlap)
if (Location->CanFastTravel())        // BlueprintNativeEvent — override to gate by combat, etc.
    Location->FastTraverlToLocation(); // teleport player to FastTravelLocation
// Bind: OnDiscoveredEvent, OnFastTravelEvent
```

### Map widget (`UAMSMapWidget`)

```
MapWidget->SetMapAreaByTag("Region_Forest");  // or SetMapArea(AreaActor)
MapWidget->CenterOnLocalPlayer();
MapWidget->ZoomIn(0.2f);                       // MoveUp/MoveRight/MoveMap for pan
MapWidget->TrackHoveredMarker();               // track marker under cursor
MapWidget->RefreshMaterials();                 // call from "On Activated"
```

### Fog of war (`AAMSMapArea`)

```
Area->UpdateFogOfWar(PlayerWorldPos);  // reveal around the player (tick/timer)
Area->OnSave();  Area->OnLoad();       // persist the fog mask (SaveGame)
```

---

## 4 — Wire to Characters / Blueprints

- **Player:** call `UpdateDiscovererPosition` (and/or `AAMSMapArea::UpdateFogOfWar`) from the player pawn/controller on a timer to drive compass + fog. The `UAMSDiscoverComponent` can be added to the player to handle discovery proximity.
- **POIs / NPCs / quests:** add a `UAMSMapMarkerComponent`, set its `MarkerCategory` tags and texture. Quest tracking calls `TrackMarker` so the compass and minimap point at the active objective.
- **Map screen:** open `UAMSMapWidget` through the UI Navigation registry (`Spawn Widget By Tag`, e.g. `UI.Widget.Map`). On the widget's "On Activated", call `RefreshMaterials` and `CenterOnLocalPlayer`.
- **Fast travel UI:** build a list from `GetAllDiscoveredFastTravelLocation`, and on selection call `FastTraverlToLocation` (after checking `CanFastTravel`).
- **Pings/waypoints:** on map click, `UAMSMapWidget::SpawnMarkerActorAtScreenPosition` or subsystem `SpawnMarkerActor` to drop an `AAMSActorMarker`.

---

## 5 — Verify

**Checklist before testing:**

- [ ] Marker icon config DataAsset assigned in **Project Settings → Ascent Navigation Settings**.
- [ ] At least one `AAMSMapArea` placed, with bounds covering play space and a valid `Texture` or baked `RenderTarget`.
- [ ] `SetCurrentMapArea` (or `SetMapAreaByTag`) called so the widget knows the active region.
- [ ] `UAMSMapWidget` Blueprint binds `MapBrush`, `MapMask`, `MapCanvas`, `MapCursor` and sets `MarkersClass`.
- [ ] Actors that should appear have a `UAMSMapMarkerComponent` with a texture + category.
- [ ] If using fast travel, locations have `bCanFastTravel` + a valid `FastTravelLocation`.

**Common failures:**

| Symptom | Fix |
|---|---|
| Map widget blank | No current map area set, or area `Texture`/`RenderTarget` missing/unbaked (`GenerateMap`) |
| Markers don't appear | Marker component not registered, wrong area active, or `MarkerTexture` null |
| Player not centered | `CenterOnLocalPlayer`/`RefreshMaterials` not called on activate |
| Compass marker missing | `ShowOnCompass` false for that category, or no `UpdateDiscovererPosition` feed |
| Fog never reveals | `EnableFog` off on the area, or `UpdateFogOfWar` not driven from the player |
| Fast travel does nothing | `bCanFastTravel` false, `CanFastTravel` override returns false, or `FastTravelLocation` unset |
| Markers misplaced | Map area bounds wrong; normalized↔world conversion depends on correct `AreaSize`/bounds |
| Widget binding errors | Required `BindWidget` panels not present in the Blueprint widget tree |
