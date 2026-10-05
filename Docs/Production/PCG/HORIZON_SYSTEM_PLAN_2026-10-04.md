# Horizon System — Updated PCG Plan (2026-10-04)

**Status:** PLANNED — no code written yet  
**Supersedes:** `specs/horizon_eater/HORIZON_EATER_DESIGN.md` (2026-09-02) as the active horizon spec  
**Levels:** `LV_SeaAbove_Prototype` (primary), `LV_FarawayMother_Prototype` (horizon sink), `L_MelusinaMorning` (gameplay)  
**Engine:** UE 5.8, Oceanology SLW, World Partition + Data Layers + HLOD, PCGEx, Copernicus, UDS, single MPC writer

---

## 0. Executive Summary

The project already has **most of the horizon machinery** — the Horizon Eater spec, Faraway Mother fabric mountain, Sea Above Oceanology integration, UDS sky, PPV stack, optical LOD manifest, and Houdini Foundry field atlas vocabulary. What's missing is:

1. **A golden hour PPV** — no dedicated sunset/golden hour post-process exists
2. **World Compiler horizon fields** — no `horizon_distance`, `sky_exposure`, or `atmospheric_depth` point attributes
3. **A true horizon PCG graph** — `PCG_HorizonEater_FilterFlow` is referenced in spec but doesn't exist as a `.uasset`
4. **Distant terrain impostor baking** — LOD3 is defined but no impostor baking pipeline exists
5. **Cloud card / skybox pipeline** — UDS handles physical sky but no artistic cloud cards for stylized horizons
6. **Houdini Foundry live proof** — all gates are STAGED, none are `live_proven`
7. **Horizon Eater live proof** — spec + scripts exist but no PIE evidence

This plan sequences the work to close these gaps using existing systems, not new ones.

---

## 1. Existing Systems Inventory (Verified 2026-10-04)

### 1.1 Horizon Eater (spec + offline PCG + editor scripts, not live-proven)

| Component | Path | Status |
|-----------|------|--------|
| Spec | `specs/horizon_eater/HORIZON_EATER_DESIGN.md` | Written 2026-09-02 |
| Spec JSON | `specs/horizon_eater/horizon_eater_spec.v1.json` | On disk |
| Manifest | `specs/horizon_eater/horizon_eater_manifest.v1.json` | Generated |
| Placements | `specs/horizon_eater/horizon_eater_placements.v1.json` | Generated |
| HDA manifest | `specs/horizon_eater/horizon_mouth_hda_manifest.v1.json` | Generated |
| Offline PCG | `Tools/PCG/build_horizon_eater_ecosystem.py` | Written, deterministic, seed 20260829 |
| MPC params | `Content/Python/add_horizon_eater_mpc_params.py` | Written, headless-safe |
| Prototype build | `Content/Python/horizon_eater_prototype_build.py` | Written, editor-only |
| LOD destruction | `Content/Python/faraway_lod_destruction_build.py` | Written, editor-only |
| MPC scalars | `HorizonEatAmount`, `DestructionAmount`, `HorizonTension`, `WorldHorizonEat` | On `MPC_Melodia_Palette` |
| HDA template | `Tools/Houdini/horizon_eater/hda_horizon_mouth_composer.py` | Template script, not cooked |
| PCG graph | `PCG_HorizonEater_FilterFlow` | Spec only, no `.uasset` |

**Offline PCG zones (from `build_horizon_eater_ecosystem.py`):**
- `FilterCorridor` — Chladni mode (3,7), MI_Horizon_FilterFlow
- `HorizonRim` — Chladni mode (6,9), MI_Horizon_MouthCard, Z = SEA_Z + 8000..22000
- `WayfoldPair` — Chladni mode (4,4), MI_Horizon_Wayfold, tension capped at 0.35
- `DistanceEvidence` — Chladni mode (5,6), MI_Horizon_Evidence

**Three kills defined in spec:**
- **Kill A** — Oceanology SLW absorption (false ocean band at -50m)
- **Kill B** — Volumetric haze companion (height fog + cloud + haze volume)
- **Kill C** — LOD3 impostor crumble + PCG filter-flow cull

### 1.2 Faraway Mother (LV_FarawayMother_Prototype)

| Component | Path | Status |
|-----------|------|--------|
| Terrain | `SM_FarawayMother_FabricRidge` (4km OBJ → Nanite) | On disk |
| Prototype build | `Content/Python/faraway_mother_prototype_build.py` | Written |
| Capture rig | `Content/Python/build_faraway_mother_capture_rig.py` | Written |
| Offline PCG | `Tools/PCG/build_faraway_mother_pcg_ecosystem.py` | Written, 4 biomes |
| Offline LOD destruction | `Tools/PCG/build_faraway_lod_destruction_ecosystem.py` | Written, deterministic |
| Moon-haze fog | `FM_MoonHaze_Fog`, `FM_MoonHaze_PPV`, `FM_MoonHaze_VolumeBox` | In level |
| Copernicus MIs | `MI_Copernicus_GildedLoom`, `SilkWaterfall`, `FinalDreamweaver`, `FrostBloom` | On disk |
| Faraway MIs | `MI_Mother_Gown`, `Mantle`, `Veil`, `Corset`, `Cradle` | On disk |
| Optical LOD | `specs/lookdev/optical_lod_manifest.v1.json` | 11 assets, 563 textures |
| Season data | `Content/Melodia/PCG/Seasons/DA_Season_FarawayFabric.uasset` | On disk |

**Faraway Mother biomes (from `build_faraway_mother_pcg_ecosystem.py`):**
- `WeaveRidge` — fabric ridges, shoulder folds, silk vines (kill_thresh 0.35)
- `LaceCanopy` — lace trees, pearl bushes (kill_thresh 0.50)
- `FrillValley` — valley depressions, frill rocks, brocade flowers (kill_thresh 0.85)
- `ResonantSeamWay` — walkways, heart gate, head silhouette (kill_thresh 0.95, never fully crumbles)

### 1.3 Sea Above (LV_SeaAbove_Prototype)

| Component | Path | Status |
|-----------|------|--------|
| Oceanology | `AOceanologyInfiniteOcean`, `AOceanologyWaterVolume`, `AOceanologyManager` | In level |
| False ocean | `SeaAbove_FalseOceanPlane_Prototype` (Z -5000 cm) | In level |
| Bell/Crown | `SeaAbove_BellProxy_Prototype`, `SeaAbove_CentralCore_Proxy` | In level |
| PCG integration | `Content/Python/build_sea_above_pcg_integration.py` | Written |
| Island ring | `Tools/PCG/build_sea_above_island_ring.py` | Written, golden-angle spiral |
| Arpeggio Bridge | 24-node PCG graph | In level |
| DataLayers | `DL_Islands`, `DL_Creature`, `DL_Lighting`, `DL_Water` | On disk |
| HLOD | `LV_SeaAbove_Prototype_WP_HLODLayer_Instanced` + Merged | On disk |
| Season data | `Content/Melodia/PCG/Seasons/DA_Season_SeaAboveReef.uasset` | On disk |
| Reef volumes | `VOL_GhostFog.vdb`, `VOL_GodRays.vdb`, `VOL_NebulaVeil.vdb` | On disk |
| Reef meshes | JELLY_Bell, JELLY_Cathedral (48+ meshes) | On disk |

**Sea Above PCG graphs (9 graphs):**
- `PCG_SeaAbove_BellTreeGarden`, `Colonnade`, `East_AtlantisGrove`, `East_PhyllotaxisBiome`, `East_PhyllotaxisCourtyard`, `East_Scree`, `East_TerraceGarden`, `ResonanceCathedral`, `XylophoneTrail`

**Island ring (from `build_sea_above_island_ring.py`):**
- Golden radii: 5000, 8090, 13090, 21180, 34270 uu + 2 far spires at 55420
- Golden angle 137.50776° spiral pacing
- Uses real `SM_Island_A/B/C` meshes scaled 2.5-4.5x, flattened z-scale 0.5
- Material: `MI_ForestRockFormation_01` (Megascans AAA island tier)
- Z = 13455 (sea surface waterline)

### 1.4 PCG_Dreamstate_DistantRuin

| Component | Path | Status |
|-----------|------|--------|
| Graph | `Content/Melodia/PCG/PCG_Dreamstate_DistantRuin.uasset` | On disk |
| Setup script | `Content/Python/setup_melodia_opening_pcg.py` | Written |
| Structure | PCGVolumeSampler → PCGTransformPoints → PCGStaticMeshSpawner | Basic rock spawner |
| Volume | `PCG_MelodiaOpening_Dream_Atmosphere` (10×2.2×2.0 at 0,720,220) | In level |

**Assessment:** This is a basic off-route rock spawner, not a true horizon system. It's a proof-of-concept for PCG volume sampling, not a horizon dressing tool.

### 1.5 PCGDemo_FogCards

| Component | Path | Status |
|-----------|------|--------|
| Graph | `Content/PCG/Graphs/Forest/PCGDemo_FogCards.uasset` | On disk |

**Assessment:** Fog card system exists but is not wired into any horizon pipeline. Reusable for atmospheric perspective.

### 1.6 UltraDynamicSky (UDS)

| Component | Path | Status |
|-----------|------|--------|
| BP | `/Game/UltraDynamicSky/Blueprints/Ultra_Dynamic_Sky` | On disk |
| Weather BP | `/Game/UltraDynamicSky/Blueprints/Ultra_Dynamic_Weather` | On disk |
| MPC | `/Game/UltraDynamicSky/Materials/Weather/UltraDynamicWeather_Parameters` | On disk |
| MF | `Day_to_Night_Float`, `Day_to_Night_Color` | On disk |
| ToD sync | `Content/Python/setup_time_of_day_mpc.py` | Written, `--apply` flag |
| Time bridge | `Content/Python/melodia_uds_time_bridge.py` | Written, semantic day model |
| Landscape loops | `Content/Python/setup_landscape_uds_loops.py` | Written, 4 WP pillars |
| Sky tune | `Content/Python/_gg_sky_tune.py` | Written (Glassgarden only) |
| SunsetBlush preset | `MI_Universal_SunsetBlush` | On disk (universal_instance_presets.py) |

**Assessment:** UDS is the live sky authority. `UseUDSTimeOfDay` static switch on `M_Master_Toon_Universal` is wired. `melodia_uds_time_bridge.py` derives semantic day parts (dawn/noon/dusk/night) from UDS clock. `MI_Universal_SunsetBlush` exists as a material preset but no golden hour PPV exists.

### 1.7 World Compiler

| Component | Path | Status |
|-----------|------|--------|
| Contract | `Docs/WorldGen/WORLD_COMPILER_CONTRACT.md` | Canonical |
| Point row schema | `specs/schemas/world_compiler_point_row.v1.json` | 25 columns |
| UE driver | `Content/Python/world_compiler_ue.py` | Written |
| Recipe example | `recipes/morning_rainbow_bloom.v1.json` | Live-proven |

**Point fields relevant to horizon:**
- `height_class` (0=low, 1=mid, 2=tall) — can drive horizon silhouette
- `density_class` (0=sparse, 1=normal, 2=dense) — can drive atmospheric density
- `hero_weight` (0..1) — 1 near authored moments
- `Resonance` (0..1) — Resonance Ecology field
- `band` (0..6) — ROYGBIV band index

**Missing for horizon work:**
- No `horizon_distance` field (distance to horizon line)
- No `sky_exposure` field (how much sky is visible from this point)
- No `atmospheric_depth` field (baked atmospheric perspective value)
- No `silhouette_weight` field (how much this point contributes to the horizon silhouette)

### 1.8 Houdini Foundry

| Component | Path | Status |
|-----------|------|--------|
| README | `specs/houdini_foundry/README.md` | Canonical |
| Recipe schema | `specs/houdini_foundry/houdini_foundry_recipe.v1.schema.json` | Canonical |
| Field channels | `specs/houdini_foundry/field_atlas_channels.v1.json` | 38 channels |
| Foundry tool | `Tools/Houdini/foundry/houdini_foundry.py` | Written |

**All gates are STAGED.** None are `live_proven`. Key horizon-relevant channels:

| Channel | Status | Horizon Use |
|---------|--------|-------------|
| `height` | existing | Terrain height for silhouette |
| `slope` | proposed | Cliff/ridge detection |
| `curvature` | proposed | Ridge/hollow detection |
| `concavity` | existing | Valley detection |
| `convexity` | existing | Ridge detection |
| `exposure` | proposed | Sky openness |
| `flow` | proposed | Erosion/water flow |
| `flowdir` | proposed | Flow direction |
| `mist` | proposed | Volumetric ecology |
| `pollen` | proposed | Volumetric ecology |
| `bioluminescence` | proposed | Volumetric ecology |
| `shore_influence` | proposed | Distance to shoreline |
| `cliff` | proposed | Cliff mask |
| `wave_direction` | proposed | Ocean intelligence |
| `wave_amplitude` | proposed | Ocean intelligence |
| `foam_probability` | proposed | Ocean intelligence |
| `shore_hit` | proposed | Ocean intelligence |
| `wetness_reach` | proposed | Ocean intelligence |
| `wake_corridor` | proposed | Traversal wake |
| `mist_spawn` | proposed | Niagara mist spawn weight |
| `whitewater_spawn` | proposed | Niagara whitewater spawn |
| `velocity` | proposed | Vector field for Niagara |

### 1.9 PPV System

| Component | Path | Status |
|-----------|------|--------|
| Contract | `Content/Python/ppv_contract.py` | Canonical |
| Nikki render PP | `Content/Python/setup_nikki_render_post_process.py` | Written |
| Nikki dream PPV | `Content/Python/build_ppv_nikkidream.py` | Written |
| Portfolio MPC | `Content/Python/setup_portfolio_mpc.py` | Written |
| Gameplay levels | `L_MelusinaMorning`, `L_KaleidoNave`, `ZenForestTest`, `LV_SeaAbove_Prototype` | Certified |

**PPV stack per level:** dreamprint_ink + melusina_grade + starry_night

**Missing:** No golden hour / sunset PPV preset. No horizon-specific grade.

### 1.10 Quality Tier System

| Master | Tiers | Status |
|--------|-------|--------|
| M_Master_Gemstone | Fast/Standard/Hero/Cinematic | ✅ Created |
| M_Master_Toon_Universal | Fast/Standard/Hero/Cinematic | Script written, not executed |
| M_Master_Nikki | Fast/Standard/Hero/Cinematic | Script written, not executed |

### 1.11 Optical LOD Manifest

| LOD | Distance | POM | Toksvig | Rim | WPO | Res |
|-----|----------|-----|---------|-----|-----|-----|
| LOD0 | 0-15m | 32 | 0.0 | 1.0 | 1.0 | 1024 |
| LOD1 | 15-50m | 16 | 0.35 | 1.15 | 0.75 | 512 |
| LOD2 | 50-200m | 0 | 0.75 | 1.4 | 0.3 | 256 |
| LOD3 | 200-5000m | 0 | 1.0 | 1.8 | 0.0 | 128 |

**Shared utilities:** `T_LOD_BayerDither_8x8`, `T_LOD_BlueNoise_64x64`, `T_LOD_Iridescence_ThinFilm_LUT`

---

## 2. Gap Analysis

### 2.1 Golden Hour PPV (HIGH priority)

**What exists:** UDS drives time of day. PPV stack is ink + grade + starry_night. `TimeOfDayWarmth` scalar on MPC_Melodia_Palette. `MI_Universal_SunsetBlush` material preset. `melodia_uds_time_bridge.py` derives semantic day parts. `execute_phase_b_wp_lighting.py` has "golden-hour sunset" lighting intent.

**What's missing:** A dedicated golden hour PPV preset that:
- Warms the color grade (amber/rose/gold)
- Increases bloom for atmospheric glow
- Adjusts exposure for sunset contrast
- Adds a subtle horizon gradient blend
- Ties to UDS `Time of Day` (golden hour = ~1700-1900)

**How to build it:** New `Content/Python/setup_golden_hour_ppv.py` that:
1. Reads UDS `Time of Day` from the current level
2. Computes golden hour weight (0 at noon, 1 at sunset)
3. Applies PPV overrides: bloom, exposure, color grade, vignette
4. Writes to `PPV_GoldenHour` actor (additive, not replacement)
5. Ties to `MPC_Melodia_Palette.TimeOfDayWarmth` for material-side warmth

### 2.2 World Compiler Horizon Fields (MEDIUM priority)

**What exists:** `height_class`, `density_class`, `hero_weight`, `Resonance`, `band`. No horizon-specific fields.

**What's missing:** Horizon-specific point attributes that would let PCG drive horizon dressing:
- `horizon_distance` — distance from point to horizon line (for LOD blending)
- `sky_exposure` — 0..1 how much sky is visible (for atmospheric density)
- `silhouette_weight` — 0..1 how much this point contributes to the horizon silhouette
- `atmospheric_depth` — baked atmospheric perspective value (for color grading)

**How to build it:** Additive schema version `world_compiler_point_row.v2` (never edit v1). New fields computed in `Tools/world_compiler.py` ecology stage from terrain height + band position. PCG reads them via `PCGInstanceDataPackerByAttribute`.

### 2.3 PCG_HorizonEater_FilterFlow Graph (HIGH priority)

**What exists:** Spec references it. `build_horizon_eater_ecosystem.py` generates offline placements JSON. No `.uasset` on disk.

**What's missing:** The actual PCG graph that:
- Takes World Compiler points as input
- Applies `density *= (1 - HorizonEat * HorizonMask)` where `HorizonMask = distance>1500m & dot(view, horizon)`
- Advects survivors toward `HorizonMouthCorridor` spline
- Outputs filter-flow debris points

**How to build it:** New `Content/Python/build_horizon_eater_filter_flow.py` that:
1. Creates `PCG_HorizonEater_FilterFlow` graph
2. Input: World Compiler DataTable (points.csv)
3. Filter: `PCGFilterPointsByAttribute` on `horizon_distance > 1500`
4. Cull: `PCGMultiplyDensityByAttribute` with `HorizonEatAmount` scalar
5. Advect: `PCGTransformPoints` toward mouth corridor spline
6. Output: `PCGStaticMeshSpawner` with filter-flow debris meshes

### 2.4 Distant Terrain Impostor Baking (MEDIUM priority)

**What exists:** LOD3 defined in optical LOD manifest. `T_BayerDither_8x8`, `T_BlueNoise_64x64` shared textures. `hda_horizon_mouth_composer.py` template has impostor baking stubs.

**What's missing:** A baking pipeline that:
- Takes Faraway Mother terrain (or any distant terrain)
- Bakes 128px impostor textures (BaseColor, Normal, ORM, Height)
- Applies Toksvig filtering + rim boost
- Outputs to `Saved/Audit/lookdev/optical_lods/<asset>/LOD3/`
- Registers in `optical_lod_manifest.v1.json`

**How to build it:** New `Tools/Houdini/copernicus/copernicus_impostor_bake.py` that:
1. Imports terrain mesh
2. Bakes impostor from horizon-view direction
3. Applies Toksvig + rim per LOD3 spec
4. Outputs 4 maps + manifest entry
5. Deterministic: two cooks, same hashes

### 2.5 Cloud Card / Skybox Pipeline (LOW priority)

**What exists:** UDS volumetric clouds. `MI_StarryNight_Hero` for night sky overlay. `PCGDemo_FogCards` graph. `brooch_sky.py` Blender-side sky shader with horizon glow layer.

**What's missing:** Artistic cloud cards for stylized horizons — the "painterly cloud" look that Infinity Nikki uses. These are billboarded cloud sprites placed at horizon distance, not volumetric clouds.

**How to build it:** New `Content/Python/build_horizon_cloud_cards.py` that:
1. Creates a PCG graph `PCG_HorizonCloudCards`
2. Places cloud card billboards at 2000-5000m distance
3. Uses existing cloud textures (or bakes new ones from UDS)
4. Ties opacity to `HorizonEatAmount` (clouds dissipate as horizon is eaten)
5. Reuses `PCGDemo_FogCards` pattern

### 2.6 Houdini Foundry Live Proof (MEDIUM priority)

**What exists:** All gates STAGED. Field atlas vocabulary defined. Recipe schema written. `hda_horizon_mouth_composer.py` template exists (not cooked).

**What's missing:** First live-proven recipe. Recommended starting point: `volumetric_ecology` for Sea Above (Gate 8A — volume channels only, no FLIP).

**How to build it:** 
1. Write `recipes/houdini_foundry/volumetric_ecology_sea_above.v1.json`
2. Cook `HDA_Foundry_VolumetricEcology` via Hython
3. Verify determinism (two cooks, same hashes)
4. Import one channel (e.g. `mist`) into UE as a texture
5. Wire to existing `NS_Uni_WaterMist` via anchors/textures
6. Promote to `live_proven` in `CURRENT_STATE.md`

### 2.7 Horizon Eater Live Proof (HIGH priority)

**What exists:** Spec, offline PCG (`build_horizon_eater_ecosystem.py`), editor scripts, MPC scalars, expected actors, HDA template.

**What's missing:** PIE evidence. The spec's evidence section requires:
- 4 HDR captures via `UMelodiaCaptureRenderSubsystem` (Shot A pristine, B half-eaten, C eaten+membrane, D filter corridor top-down)
- `Saved/gate_ledger.json` row `horizon_eater_prototype`

**How to build it:**
1. Run `add_horizon_eater_mpc_params.py` headless
2. Run `horizon_eater_prototype_build.py` in editor
3. Run `faraway_lod_destruction_build.py` in editor
4. PIE from hero CineCameraActor at HorizonEat 0.0 / 0.6 / 1.0
5. Capture 4 shots via `UMelodiaCaptureRenderSubsystem`
6. Write `Saved/gate_ledger.json` row

---

## 3. Creative Runtime Usage of the World Compiler

### 3.1 Current State

The World Compiler outputs `points.csv` with 25 columns. PCG consumes it via `Load Data Table` → `PCGMeshSelectorByAttribute` → `PCGInstanceDataPackerByAttribute`. The compiler is deterministic (same recipe + seed = byte-identical output).

### 3.2 Horizon-Specific Runtime Usage

**New v2 fields for horizon work:**

| Field | Type | Computation | PCG Consumer |
|-------|------|-------------|--------------|
| `horizon_distance` | float cm | `dist(point, horizon_line)` | LOD blending, culling |
| `sky_exposure` | float 0..1 | `f(height, slope, curvature)` | Atmospheric density |
| `silhouette_weight` | float 0..1 | `f(height_class, convexity)` | Impostor dither mask |
| `atmospheric_depth` | float 0..1 | `f(horizon_distance, mist)` | Color grade blend |

**Runtime PCG graph structure (v2):**

```
Load Data Table (DT_<recipe>_Points)
  -> PCGFilterPointsByAttribute (horizon_distance > 1500)
  -> PCGMultiplyDensityByAttribute (1 - HorizonEat * HorizonMask)
  -> PCGTransformPoints (advect toward mouth corridor)
  -> PCGStaticMeshSpawner (filter-flow debris)
  -> PCGInstanceDataPackerByAttribute (silhouette_weight, atmospheric_depth)
  -> Output
```

### 3.3 Musical-Biome Horizon Derivative

Per the musical-biome derivative rule (2026-10-03), a new musical biome's horizon is a chapter-specific derivative of the shared Musical/Hero graph, never a rewrite. The horizon fields compose with the existing `Resonance` / `EcologyClass` / `MaterialVariant` / `ScaleBias` contract.

**New biome horizon recipe:**
```json
{
  "schema": "melodia.houdini_foundry_recipe.v1",
  "recipe_id": "horizon_<place>",
  "product": "field_atlas",
  "seed": 20261004,
  "status": "staged",
  "params": {
    "channels": ["height", "slope", "curvature", "exposure", "mist", "shore_influence"]
  }
}
```

---

## 4. Houdini Engine Integration

### 4.1 Current State

Houdini Foundry has 9 products, all STAGED. The field atlas has 38 channels. The recipe schema is written. The validation tool exists.

### 4.2 Horizon-Relevant Houdini Bakes

| Product | Gate | Horizon Use | Priority |
|---------|------|-------------|----------|
| `field_atlas` | 4 | Height/slope/curvature for silhouette | P0 |
| `volumetric_ecology` | 8A | Mist/pollen/bioluminescence volumes | P1 |
| `flow_volume` | 7 | Air/water flow for cloud cards | P1 |
| `deposition` | 6 | Glitter/snow accumulation on ridges | P2 |
| `ocean_intelligence` | 8B | Wave/foam for Sea Above horizon | P2 |
| `copernicus_field` | 9 | Field-driven material variants | P2 |

### 4.3 Recommended First Bake: field_atlas for Sea Above

**Why:** Sea Above is the primary horizon level. It has real terrain (MeshTerrain), real ocean (Oceanology), and real horizon. The field atlas channels (height, slope, curvature, exposure) directly drive the horizon silhouette and atmospheric density.

**Recipe:**
```json
{
  "schema": "melodia.houdini_foundry_recipe.v1",
  "recipe_id": "field_atlas_sea_above",
  "product": "field_atlas",
  "seed": 20261004,
  "status": "staged",
  "source": {
    "kind": "hda",
    "path": "Tools/Houdini/foundry/hda_foundry_field_atlas.py",
    "extends": "HDA_Foundry_FieldAtlas"
  },
  "params": {
    "channels": ["height", "slope", "curvature", "concavity", "convexity", "exposure"]
  },
  "region": {
    "level": "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype",
    "bounds_cm": [-6000, -6000, 6000, 6000],
    "tile_size_cm": 1000
  },
  "outputs": [
    {"name": "height", "format": "png16"},
    {"name": "slope", "format": "png8"},
    {"name": "curvature", "format": "png8"},
    {"name": "concavity", "format": "png8"},
    {"name": "convexity", "format": "png8"},
    {"name": "exposure", "format": "png8"}
  ],
  "ue_target": {
    "consumer": "pcg_graph",
    "asset_path_prefix": "/Game/EnvSandbox/Textures/FieldAtlas/SeaAbove",
    "integration_gate": "PCG samples field atlas textures for horizon dressing"
  },
  "authority": {
    "runtime_owner": "UMelodiaAudioReactivePresentationSubsystem",
    "writes_mpc": false
  }
}
```

### 4.4 HDA_P3_HorizonMouthComposer

**Spec:** Houdini owns upper/lower horizon proxies, filter plates, mouth depth cards, silhouette mask, HLOD variants. Exports curves/points/CSV for PCGEx.

**Status:** Spec only. Not authored.

**How to build it:** New `Tools/Houdini/horizon_eater/hda_horizon_mouth_composer.py` that:
1. Takes terrain heightfield as input
2. Computes upper/lower horizon proxies (silhouette curves)
3. Generates filter plates (pleated throat geometry)
4. Bakes mouth depth cards (distance-based opacity)
5. Exports silhouette mask texture
6. Outputs HLOD variants (LOD0-LOD3)
7. Exports curves/points/CSV for PCGEx consumption

---

## 5. Niche Pipeline Research

### 5.1 Infinity Nikki Horizon Rendering

**Key techniques (from project's own research doc `Docs/Research/UE58_TOON_MATERIAL_INTAKE_INFINITY_NIKKI_2026-08-08.md` + web research):**

1. **Atmospheric perspective** — color shift toward sky color with distance, not just fog. Horizons blend into soft, hazy skies with a "painterly" quality
2. **Silhouette layering** — multiple depth layers with different color grades. Each layer has its own color temperature and saturation curve
3. **Cloud cards** — billboarded cloud sprites at horizon distance, not volumetric. Hand-painted cloud textures on camera-facing billboards
4. **Distant impostors** — low-res baked impostors for far terrain. 128px textures with Toksvig filtering
5. **Gradient skybox** — hand-painted gradient sky, not physical sky model. UDS handles physical sky but artistic gradient overlays it
6. **Rim lighting** — strong rim on distant objects to separate from sky. Grazing-angle rim boost at distance

**Infinity Nikki's rendering approach:**
- Built on Unreal Engine with custom modifications
- Cel-shaded/toon-shaded hybrid + physically-based lighting
- Advanced cloth physics and material rendering
- Dynamic weather and time-of-day affecting atmospheric conditions
- Large-scale open world with seamless streaming
- Often compared to Genshin Impact and BotW for visual artistry

**Production rubric (8 points):**
1. Silhouette readability at distance
2. Color harmony with sky
3. Atmospheric depth cueing
4. Material consistency across LODs
5. Lighting coherence
6. Performance budget adherence
7. Art direction alignment
8. Technical constraint compliance

### 5.2 UE5 Volumetric Fog + Horizon

**Techniques:**
- `ExponentialHeightFog` with `FogHeightFalloff` for above-water horizon
- `VolumetricFog` with `ScatteringDistribution` for atmospheric perspective
- `VolumetricCloud` with `bPerSampleEmissive` for sunset-lit clouds
- `SkyAtmosphere` with `MieScatteringScale` for Rayleigh/Mie balance
- `PostProcessVolume` with `ColorGrading` for horizon-specific grade

**Post Process Material node setup for horizon effects:**
```
SceneTexture: SceneDepth
SceneTexture: WorldPosition
CameraVector → DotProduct with WorldNormal
Distance-based color interpolation (Lerp)
Power nodes for falloff curves
Clamp nodes to prevent over-saturation
```

**Key blendable locations:**
- `Before Tonemapping` — for physical fog integration
- `After Tonemapping` — for stylized color grading

**Volumetric Fog settings for horizon:**
- `Fog Inscattering Color` — controls scattered light color
- `Fog Height Falloff` — altitude-based density change
- `Fog Max Opacity` — density ceiling

**Performance:** Volumetric Fog can be expensive; use Temporal Upsampling. For stylized games, fake fog planes or sprite-based fog can be more efficient.

**Project already uses:** UDS (which wraps SkyAtmosphere + VolumetricCloud), ExponentialHeightFog, PPV with color grading.

### 5.3 Houdini → UE Horizon Pipelines

**Industry patterns:**
1. **Heightfield → Impostor baking** — bake distant terrain to 128px impostors with Toksvig filtering
2. **Volume → Texture atlas** — bake volumetric data to 2D texture atlases for UE sampling
3. **Curve → PCG spline** — export Houdini curves as PCG splines for scatter paths
4. **Point cloud → PCG points** — export Houdini point clouds as PCG point data
5. **VDB → Volume Texture** — convert VDBs to UE Volume Textures for Niagara/fog

**Houdini impostor baking workflow:**
1. Generate terrain in Houdini (heightfield tools)
2. Chunk terrain into tiles
3. Bake impostor textures (albedo, normal, roughness) — 8-16 views for 360° coverage
4. Export as FBX + textures
5. Import into UE via Houdini Engine
6. Configure LOD transitions and culling distances

**Tools:** Houdini Engine for Unreal (SideFX), UE Impostor Baker (community), Simplygon/InstaLOD (mesh optimization)

**Project already uses:** Field atlas channels, VDBs for static art, Copernicus for material maps.

### 5.4 PCG Horizon Dressing

**Industry patterns (Horizon Zero Dawn, Ghost of Tsushima, Infinity Nikki):**
1. **Biome-specific horizon palettes** — each biome has a horizon color grade
2. **Procedural cloud placement** — PCG places cloud cards based on wind + exposure
3. **Distant landmark scattering** — PCG places distant landmarks (towers, mountains) at horizon
4. **Atmospheric depth layers** — PCG places multiple depth layers with different fog densities
5. **Silhouette breakup** — PCG places foreground elements to break up the horizon line

**Project already uses:** PCG volume sampling, PCG mesh spawner, PCG instance data packer.

### 5.5 Oceanology + Horizon

**Key principle:** The horizon line where water meets sky is the most important visual in Sea Above. Oceanology's SLW (Subsurface Scattering) handles the water side. The sky side is UDS. The transition zone is where the Horizon Eater operates.

**Techniques:**
1. **Extinction-based false ocean** — tune absorption to extinguish faster than physical distance justifies
2. **Fresnel band** — mid-ground Fresnel reflection band that reads as "km of water"
3. **Horizon fog** — height fog that blends water color to sky color at horizon
4. **Wave direction alignment** — align wave direction to horizon line for visual coherence

**Project already uses:** Oceanology SLW, false ocean plane, Fresnel band, height fog.

### 5.6 Distant Impostor / HLOD Techniques

**UE5 best practices:**
1. **HLOD layers** — already exist for L_MelusinaMorning and 9 other levels
2. **Impostor baking** — bake 128px textures from horizon-view direction
3. **Dithered destruction** — use Bayer/blue noise dither for LOD transitions
4. **Toksvig filtering** — pre-filter normal maps for distant viewing
5. **Rim boost** — increase rim lighting at distance to separate from sky

**Project already uses:** HLOD layers, optical LOD manifest, Bayer/blue noise dither, Toksvig filtering, rim boost.

### 5.7 "Horizon Eater" / Filter-Feeder Creature Design

**Concept:** The Horizon Eater is a filter feeder whose feeding field compresses adjacency; mouth spans what the player reads as horizon. Mountains/ridges become jaw margins, filter plates, pleated throat.

**Design principles:**
1. **Horizon IS the mouth** — the creature doesn't have a horizon, it *is* the horizon
2. **Three kills imply one anatomy** — Oceanology SLW (water), volumetric haze (sky), LOD3 impostor crumble (geometry)
3. **Single scalar rules all** — `HorizonEatAmount 0..1` on MPC_Melodia_Palette
4. **Tension-gated destruction** — crumble only where `Tension > 0.6` or `dist > 1500m`
5. **Wayfold corridor** — SeamWay (`|Chladni| < 0.12`) never fully crumbles; becomes path to mouth

**Wardrobe integration:**
- Clothing classification (omen/predator/pilgrim/lineage/guide) alters HorizonEat response curve
- Hostile bias: +0.2 for predator/omen
- Wayfold (Glasswing Courier outfit) aligns local adjacency
- Mara Anchor: inside radius, 1m stays 1m — stops collapse mid-crossing

**Rhythm integration:**
- Better rhythm → longer stability, clearer destination, side route, glimpse of feeding current
- Iris proves matter crosses fold (alpine+lowland species side-by-side)

**Similar creatures in game design:**
- **Filter feeders** (whale sharks, manta rays) — passive, large, majestic
- **Reality benders** (Lovecraftian entities) — warp space around them
- **Living landscapes** (Zelda: BotW's Hyrule, Horizon Zero Dawn's Tallnecks) — environment as creature

**Project already uses:** Full spec, offline PCG, MPC scalars, HDA template, editor scripts.

### 5.8 Copernicus Field Pipeline

**What it is:** FieldAtlas channels drive material maps through the existing Copernicus/cymatic map contracts. No second material pipeline — output is a new variant in the existing family.

**Channel → map mapping:**
| FieldAtlas Channel | Map Effect |
|---|---|
| `sediment` | BaseColor pigment blend toward variant's sediment tint |
| `wetness` | Roughness down, BaseColor value down (darken) |
| `concavity` | accumulation mask → Height fill + BaseColor accumulation tint |
| `exposure` | bleaching: BaseColor saturation down, value up |
| `resonance` | cymatic pattern visibility (lerp of Chladni layer into Height/Emissive) |
| crystal mask | Iridescence strength + Emissive sparkle |

**Output:** 9-map family (BaseColor, Normal, Roughness, Metallic, Height, ORM, Emissive, Iridescence, Opacity) at 2K test / 4K hero.

**Determinism hazard:** The existing `copernicus_cymatic_parallax.py` uses numpy `hash()` seeding which is non-deterministic across processes. New work must use `stable_int`.

**Project already uses:** Copernicus MIs (40+ variants), 9-map contract, `verify_tex_contract.py` validator.

### 5.9 Blender-Side Sky Shader (brooch_sky.py)

**What it is:** Melusina Sky v3 — editorial gradient + glow + stars + clouds + aurora + grain. Has horizon glow layer (L1).

**Horizon color science:**
- `TINT_HORIZON` — warm/cool tint at horizon line
- `TINT_ZENITH` — deep sky color at zenith
- Multiple presets (editorial_dark, forte, etc.)

**Relevance:** While Blender-only, the horizon color science informs the UE-side golden hour PPV. The gradient + glow + stars approach is what the UE PPV should replicate.

**Project already uses:** `Tools/brooch_sky.py` for Blender-side sky rendering.

---

## 6. Implementation Sequence

### Phase 1: Golden Hour PPV (1-2 days)

**Goal:** A golden hour PPV preset that works in any level with UDS.

**Steps:**
1. Write `Content/Python/setup_golden_hour_ppv.py`
2. Read UDS `Time of Day` from current level
3. Compute golden hour weight (0 at noon, 1 at sunset ~1800)
4. Apply PPV overrides: bloom +0.3, exposure -0.2, color grade warm
5. Write to `PPV_GoldenHour` actor (additive)
6. Tie to `MPC_Melodia_Palette.TimeOfDayWarmth`
7. Test in LV_SeaAbove_Prototype at Time of Day 1750

**Evidence:** `Saved/Audit/golden_hour_ppv.json` + PIE capture at sunset.

### Phase 2: PCG_HorizonEater_FilterFlow Graph (2-3 days)

**Goal:** The actual PCG graph that culls and advects points based on HorizonEat.

**Steps:**
1. Write `Content/Python/build_horizon_eater_filter_flow.py`
2. Create `PCG_HorizonEater_FilterFlow` graph
3. Input: World Compiler DataTable
4. Filter: `horizon_distance > 1500` (or `band >= 5` for ROYGBIV)
5. Cull: `density *= (1 - HorizonEat * HorizonMask)`
6. Advect: transform toward mouth corridor spline
7. Output: filter-flow debris spawner
8. Test in LV_SeaAbove_Prototype

**Evidence:** `Saved/Audit/horizon_eater_filter_flow.json` + PIE capture.

### Phase 3: World Compiler v2 Horizon Fields (3-4 days)

**Goal:** Additive schema version with horizon-specific point attributes.

**Steps:**
1. Write `specs/schemas/world_compiler_point_row.v2.schema.json`
2. Add `horizon_distance`, `sky_exposure`, `silhouette_weight`, `atmospheric_depth`
3. Compute in `Tools/world_compiler.py` ecology stage
4. Update `Content/Python/world_compiler_ue.py` to read v2
5. Test with `recipes/morning_rainbow_bloom.v1.json`
6. Verify determinism (two compiles, same hashes)

**Evidence:** `Saved/WorldCompiler/morning_rainbow_bloom_3900_v2/` + determinism report.

### Phase 4: Houdini Foundry field_atlas Live Proof (1-2 weeks)

**Goal:** First live-proven Houdini Foundry recipe.

**Steps:**
1. Write `recipes/houdini_foundry/field_atlas_sea_above.v1.json`
2. Cook `HDA_Foundry_FieldAtlas` via Hython
3. Verify determinism (two cooks, same hashes)
4. Import `height` + `slope` + `exposure` into UE as textures
5. Wire to PCG graph for horizon dressing
6. Promote to `live_proven` in `CURRENT_STATE.md`

**Evidence:** `Saved/Audit/houdini_foundry/field_atlas_sea_above/` + determinism report.

### Phase 5: Distant Terrain Impostor Baking (1-2 weeks)

**Goal:** Baked impostors for Faraway Mother terrain.

**Steps:**
1. Write `Tools/Houdini/copernicus/copernicus_impostor_bake.py`
2. Import `SM_FarawayMother_FabricRidge`
3. Bake impostor from horizon-view direction
4. Apply Toksvig + rim per LOD3 spec
5. Output 4 maps + manifest entry
6. Register in `optical_lod_manifest.v1.json`

**Evidence:** `Saved/Audit/lookdev/optical_lods/FarawayMother_CelestialSilk/LOD3/` + manifest update.

### Phase 6: Horizon Eater Live Proof (1 week)

**Goal:** PIE evidence for the Horizon Eater system.

**Steps:**
1. Run `add_horizon_eater_mpc_params.py` headless
2. Run `horizon_eater_prototype_build.py` in editor
3. Run `faraway_lod_destruction_build.py` in editor
4. PIE from hero CineCameraActor at HorizonEat 0.0 / 0.6 / 1.0
5. Capture 4 shots via `UMelodiaCaptureRenderSubsystem`
6. Write `Saved/gate_ledger.json` row

**Evidence:** 4 HDR captures + `Saved/gate_ledger.json` row `horizon_eater_prototype`.

### Phase 7: Cloud Card Pipeline (2-3 days)

**Goal:** Artistic cloud cards for stylized horizons.

**Steps:**
1. Write `Content/Python/build_horizon_cloud_cards.py`
2. Create `PCG_HorizonCloudCards` graph
3. Place cloud card billboards at 2000-5000m distance
4. Use existing cloud textures (or bake from UDS)
5. Tie opacity to `HorizonEatAmount`
6. Test in LV_SeaAbove_Prototype

**Evidence:** `Saved/Audit/horizon_cloud_cards.json` + PIE capture.

---

## 7. Ownership and Authority

| System | Owner | Writes MPC? |
|--------|-------|-------------|
| UDS (sky) | UDS BP | No (own MPC) |
| Oceanology (water) | Oceanology BP | No |
| MPC_Melodia_Palette | UMelodiaAudioReactivePresentationSubsystem | Yes (sole writer) |
| MPC_Cymatics_Driver | UMelodiaCymaticsWriterSubsystem | Yes (sole writer) |
| PPV stack | Per-level PPV actor | No |
| PCG graphs | PCG graph asset | No |
| World Compiler | Tools/world_compiler.py | No |
| Houdini Foundry | Tools/Houdini/foundry/houdini_foundry.py | No |
| Horizon Eater | UMelodiaAudioReactivePresentationSubsystem | Yes (HorizonEatAmount) |

**Hard no's (from World Compiler contract):**
- No `import unreal` in `Tools/world_compiler.py`
- No PCG edge/node edits from Python (use graph builder)
- No writes to `MPC_Melodia_Palette` or `MPC_Cymatics_Driver` from Houdini
- No new material master per effect
- No uniform density
- No skipping `scene_context_cycle.begin/end`

---

## 8. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Golden hour PPV conflicts with existing PPV stack | Medium | Additive PPV actor, not replacement |
| PCG_HorizonEater_FilterFlow graph too complex for PCGEx | High | Start with simple filter, add advection later |
| World Compiler v2 breaks existing recipes | Medium | Additive schema, v1 recipes still valid |
| Houdini Foundry field_atlas bake too slow | Medium | Start with 1 tile, tile_size_cm=1000 |
| Impostor baking loses too much detail | Low | LOD3 is 128px, detail loss is expected |
| Horizon Eater PIE evidence hard to capture | Medium | Use existing `UMelodiaCaptureRenderSubsystem` |
| Cloud cards look fake | Low | Use existing cloud textures, tie to HorizonEat |

---

## 9. References

- `specs/horizon_eater/HORIZON_EATER_DESIGN.md` — Horizon Eater spec
- `specs/houdini_foundry/README.md` — Houdini Foundry contract
- `specs/houdini_foundry/field_atlas_channels.v1.json` — Field atlas vocabulary
- `specs/houdini_foundry/houdini_foundry_recipe.v1.schema.json` — Recipe schema
- `specs/lookdev/optical_lod_manifest.v1.json` — Optical LOD manifest
- `Docs/WorldGen/WORLD_COMPILER_CONTRACT.md` — World Compiler contract
- `Docs/Production/UNIVERSE_FOUNDRY_CONTRACT.md` — Universe Foundry contract
- `Docs/Production/PCG/README.md` — PCG production contract
- `Docs/Research/UE58_TOON_MATERIAL_INTAKE_INFINITY_NIKKI_2026-08-08.md` — Nikki research
- `Content/Python/ppv_contract.py` — PPV contract
- `Content/Python/setup_time_of_day_mpc.py` — UDS ToD sync
- `Content/Python/horizon_eater_prototype_build.py` — Horizon Eater build
- `Content/Python/faraway_lod_destruction_build.py` — LOD destruction build
- `Content/Python/add_horizon_eater_mpc_params.py` — MPC params
- `Content/Python/build_sea_above_pcg_integration.py` — Sea Above PCG
- `Content/Python/faraway_mother_prototype_build.py` — Faraway Mother build
- `Content/Python/build_faraway_mother_capture_rig.py` — Faraway Mother capture
- `Content/Python/setup_melodia_opening_pcg.py` — DistantRuin setup
