# Sea Above gameplay paths and level organization — 2026-09-01

`LV_SeaAbove_Prototype` is organized and saved without changing the curated landscape, cathedral,
or any actor transform. The 254 existing actors now sit under explicit canonical, gameplay, world,
presentation, and PCG folders. The twelve Resonance Cathedral music nodes have their own
`02_GAMEPLAY/MusicKey` folder, and the new navigation coverage is isolated under
`05_GAMEPLAY/Navigation_Heatmap`.

The navigation build completed, but the first heatmap is correctly red/HOLD: entry → Quill,
Quill → Starskiff, and Starskiff → music-key have no connected nav path. The nearest navigable
surface is 3015 cm below PlayerStart, 1011 cm above the Quill trigger, and 1256 cm below the
Starskiff. The music-key ring near Z 28 has no navigable surface within a 7000 cm vertical search,
while the cathedral gameplay cluster is near Z 10535–13175.

That makes the next level-authoring pass precise: snap or deliberately stage the gameplay actors
against the canonical landscape/cathedral surfaces, rebuild navigation, and require all three route
queries to return connected paths before placing polish dressing. Do not move the canonical
landscape or cathedral to meet the actors.

Lookdev/material-instance polish remains intentionally untouched. Five Copernicus material
instances were already dirty and were preserved unsaved. After route connectivity is green, tune
those instances in a separate lookdev transaction so traversal evidence and art changes do not
share a rollback surface.

Git/source-control update:

- Added the machine-readable folder/nav baseline at
  `Docs/Evidence/SEA_ABOVE_LEVEL_ORGANIZATION_2026-09-01.json`.
- Added this handoff and linked it from the root README.
- Updated the local, gitignored Sea Above map/external actors through Unreal Editor; no destructive
  Git command, commit, or push was performed.
- Zero errored Blueprints after the save. The five unrelated dirty material packages remain
  unsaved and unchanged by this pass.

Visual planning canvas:
`C:/Users/froma/.cursor/projects/c-EnvironmentPortfolio/canvases/sea-above-gameplay-paths.canvas.tsx`.

## Updated-landscape integration pass

The updated canonical landscape was integrated without moving the landscape or cathedral. PlayerStart
and Quill were surface-aligned, and all twelve music-key nodes were moved as one preserved formation
onto collision-sampled cathedral surfaces. Entry → Quill and Quill → music-key now return connected
shortest, curious, and cautious nav paths.

All fifteen gameplay anchors carry `PCG_Exclude` and `WP_NoScatter`. Existing PCG authorities were
retained and grouped by cathedral resonance, cathedral structure, perimeter scatter, and water-edge
scatter. No replacement PCG graph was created. The falloff contract is 0–300 cm hard exclusion,
300–900 cm transition, and full density beyond 900 cm, with the real/false-ocean vertical gap always
empty.

Two editor-authored falloff splines now trace the proven nav corridors:
`PCG_PathFalloff_EntryToQuill` (982.7 cm) and
`PCG_PathFalloff_QuillToMusicKey` (1671.1 cm). Both carry the existing
`PCG_Spline` contract consumed by `PCG_ExclusionFalloff`, plus `WP_NoScatter`; they live under
`40_PCG/Falloff_Controls`.

World Partition varied the loaded census from 302 to 240 actors during the pass. Fifty-two newly
loaded root actors and the subsequently streamed Gaea canonical terrain were organized, leaving
zero actors at the Outliner root at verification. The map saved with zero dirty packages and zero errored
Blueprints. Twelve focused offline tests passed.

Starskiff remains intentionally unsnapped: it is a water actor and needs a deliberate walkable
shoreline/dock boarding anchor rather than a nav endpoint placed on the boat. Machine-readable
evidence is in
`Docs/Evidence/SEA_ABOVE_LANDSCAPE_GAMEPLAY_PCG_INTEGRATION_2026-09-01.json`.

## Canonical landscape deduplication

The map previously contained three `Landscape` actors. Only `CanonicalLandscape` remains. Its
64 loaded streaming proxies all use
`MI_SeaAbove_CanonicalLandscape_Substrate`; no loaded proxy uses either legacy landscape material.
The legacy CliffGrass landscape, the elevated CoastalCliff landscape, and the separate
`Gaea_LiquidCathedral_Terrain` level actor were removed. Their source assets were not deleted.

The level is saved. Unreal retains one dirty World Partition tombstone for a removed external actor
whose package no longer exists on disk; it cannot be saved as a package and clears when the editor
unloads the deleted object.

## Starskiff dock and traversal placement

The remaining dock placement is now live. `SM_Starskiff_Dock_Blockout_P0` is a 600 × 400 × 50 cm
collision platform at `(-800, 900, 10510)`; its surface is Z 10535. The boarding anchor is 50 cm
above that surface and measured 313.25 cm from Starskiff in PIE, inside the pawn's native 400 cm
boarding radius. The boat and canonical landscape were not moved.

`PCG_PathFalloff_MusicKeyToStarskiffDock` records the 4468.32 cm Glide transition and carries the
existing `PCG_Spline` / `WP_NoScatter` contract. This segment is intentionally traversal rather
than navmesh: the upper cathedral route reaches the music-key formation, then Glide owns the
vertical descent to the water-level dock.

PIE placement/runtime results:

- Boarding failed while the canonical readiness condition was absent.
- Setting `flag.sea_above.starskiff_ready` enabled boarding.
- Boarding succeeded at the placed anchor and transferred possession to Starskiff.
- Movement input advanced Starskiff 200 cm.
- Disembark restored Melusina control and cleared the boarded state.

This is a runtime seam probe because player placement and the readiness flag were invoked directly.
Final certification still requires one uninterrupted focused-player-input traversal with assertion
JSON and visible cymatics frames.
