# Melodia Traveling Folio — Three.js Prototype

Browser-side interaction lab for Melodia's proposed 3D Folio UI and future evergreen-content surfaces.

This is deliberately a **prototype boundary**, not a new gameplay/UI authority.

## What it demonstrates

- a tactile 3D Folio made from book/page/thread/parcel objects;
- raycast interaction that emits UI intents rather than mutating gameplay state;
- a local offline mailbox fixture matching the future Gift/Reverie presentation model;
- a manifest-driven repository model turntable;
- OBJ, FBX, and future GLTF/GLB loader paths;
- automatic centering and scale normalization for unrelated source assets;
- graceful visible failure when an LFS-backed binary is not hydrated/servable.

## Run it

From the repository root:

```powershell
python -m http.server 8080
```

Then open:

```text
http://127.0.0.1:8080/Prototypes/Web/MelodiaFolio3D/
```

Do **not** open `index.html` directly through `file://`; the browser must be able to fetch `models.json`, `mailbox.json`, and repository assets through HTTP.

## Current verified model seeds

The viewer manifest currently contains:

- `Content/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Island_A.obj`
- `Content/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Island_B.obj`
- `Content/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Island_C.obj`
- `UpdatedShirt.fbx`

The first three are tracked OBJ exports from the Sea Above prototype reef set. `UpdatedShirt.fbx` is the initial FBX/Wardrobe compatibility test and may require `git lfs pull` before the local HTTP server can provide its binary payload.

## Model manifest contract

`models.json` is intentionally tiny and engine-neutral:

```json
{
  "id": "sea_above.island_a",
  "label": "Sea Above — Reef Island A",
  "format": "obj",
  "path": "../../../Content/.../SM_Island_A.obj",
  "source_path": "Content/.../SM_Island_A.obj",
  "category": "environment"
}
```

Future web exports should prefer GLB for compactness and predictable browser loading. Do not convert the whole repository just to serve this prototype; add intentional showcase exports as they become useful.

## UI authority rule

The prototype follows:

```text
canonical state
    -> UI view model
    -> 3D presentation object
    -> pointer/raycast interaction
    -> UI intent
    -> canonical subsystem performs/denies action
```

A parcel can emit `ui.post.open_requested`. It cannot grant inventory.
An outfit model can emit `ui.wardrobe.inspect_requested`. It cannot equip itself.
A chapter page can emit `ui.chapter.selected`. It cannot author progression.

In Unreal, the same principle should route player-facing surfaces through `UMelodiaUIBridgeSubsystem` and the existing narrative/wardrobe/reward authorities.

## Files

- `index.html` — self-contained Three.js scene + UI shell
- `models.json` — repository model manifest
- `mailbox.json` — dev-only offline Post/Gift/Reverie fixture

## Next useful experiments

1. Export one intentional Starskiff GLB and add it to the manifest.
2. Export one canonical outfit mannequin/garment GLB.
3. Add a chapter-card projection onto a 3D folio page.
4. Add deterministic `FMelodiaUIIntent`-shaped JSON fixtures shared with UE tests.
5. Make the Starskiff parcel shelf and Folio mailbox consume the same Post view-model contract.
6. Add screenshot/reference capture once the visual language is locked.
