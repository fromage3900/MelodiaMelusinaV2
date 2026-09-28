# 08 — Gate 8 (P1): Volumetric Ecology + Sea Above fluid intelligence

| | |
|---|---|
| **Purpose** | (A) A reusable offline **volume** vocabulary for environmental state. (B) Expensive ocean/FLIP simulation reduced to reusable fields. Both are baked data products. |
| **Authority** | **No new runtime world-state authority.** No environmental singleton, no second bus. `UWorldFieldBus` is still a scaffold (`CURRENT_STATE.md`), and this gate does not close it. Ocean runtime stays Oceanology + `MelodiaOceanologyWaterBridgeSubsystem`. Houdini FLIP is **not** shipped runtime. |
| **Inputs** | FieldAtlas tile channels, FlowVolume, hero points, ocean surface/shoreline, recipe seed. |
| **Outputs** | Channel VDBs (low-res) + 2D slices/atlases for UE; ocean-intelligence rasters; manifests. |
| **Evidence** | `Saved/Audit/houdini_foundry/<recipe_id>/` |
| **Status** | STAGED. Prior art: `Tools/Houdini/sea_above_reef/singing_water_veil_flip.py` (FLIP), `Saved/Audit/melusina_bake_staging_20260922/` (FLIP smoke + 480/480-frame full-bake evidence), and the tracked `Reef/Volumes/VOL_{GhostFog,GodRays,NebulaVeil}.vdb` (static art VDBs, plain git). |

## A — volume channels (all `proposed` in `field_atlas_channels.v1.json`)

`humidity` (reuses `WorldField.Moisture` meaning) · `mist` · `pollen` · `bioluminescence` · `reef_pigment` · `resonance` (reuses the Resonance Ecology meaning) · `temperature` · `sparkle_habitat`.

Derivation is rule-based from existing fields, not simulated. For example: `mist = f(humidity, shore_influence, low exposure)`, `pollen = f(biome_id, wind_strength, height band)`, `bioluminescence = f(depth below water, reef_pigment, cavity)`. Record each rule and constant in the manifest so the volume is re-derivable.

**UE use:** heterogeneous volume / local fog density texture, or Niagara spawn weighting through the existing systems. Materials read the textures. Nothing writes MPCs.

## B — ocean / FLIP / whitewater intelligence (heavy lane)

Simulate once per shoreline tile (FLIP or ocean spectrum + whitewater), then **reduce** to 2D rasters over the tile:

| Channel | Reduction |
|---|---|
| `wave_direction` | mean surface velocity direction (vec2) |
| `wave_amplitude` | RMS surface height deviation |
| `surface_velocity` | mean surface velocity (vec3, cm/s) |
| `foam_probability` | fraction of frames with whitewater density > threshold |
| `shore_hit` | impact frequency at shoreline cells |
| `wetness_reach` | max wet line over the sequence |
| `wake_corridor` | authored route spline ∩ calm water (low amplitude) |
| `mist_spawn` | foam × exposure (feeds the existing `NS_Uni_WaterMist` via anchors/textures) |
| `whitewater_spawn` | foam at shore_hit peaks |

Caches stay on the college scratch disk and are **never committed**. Only reduced rasters + manifest travel.

## Done when

(A) one tile's channel volumes verify and one existing fog/Niagara consumer reads one channel in UE. (B) one shoreline tile's reduced rasters verify, and Brennan confirms foam/wetness lines match the art direction.
