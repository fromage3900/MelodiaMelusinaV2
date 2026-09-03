# Faraway Mother: PCG Graph Specification

**Document Version:** 1.0.0
**Date:** 2026-09-03
**Classification:** Implementation Specification — Artist / Agent Ready
**Target Engine:** Unreal Engine 5.8.0
**Target Level:** `/Game/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype`
**Owning Directory:** `Content/EnvSandbox/PCG/FarawayMother/`

---

## 1. Purpose & Scope

This specification defines the three missing PCG volume graphs required by `Content/Python/faraway_mother_pcg_assembly.py` (the verifier). All three graphs are consumed by the Faraway Mother PCG ecosystem, staged into `LV_FarawayMother_Prototype`, and wired to the Melodia World Field Bus.

These graphs are **volume-driven ISM/HISM scatter graphs** — they do not spawn unique `StaticMeshActor` instances. They generate point distributions inside a PCG spatial volume and batch-instantiate static meshes via the PCG static mesh spawner (HISM/ISM path), matching the proven architecture of `Content/EnvSandbox/PCG/Universal/PCG_RockScatter` and `Content/EnvSandbox/PCG/Universal/PCG_OrnamentalDetail`.

---

## 2. Authority & Single-Writer Constraints

| Subsystem | Role | Contract |
|-----------|------|----------|
| `UWorldFieldBus` | World truth provider | `SampleResonanceTension()`, `GetWaterDecision()`, `SampleCymaticRipple()` |
| `UMelodiaCymaticsSubsystem` | Cymatic publisher | Writes `WorldField.Resonance`, `WorldField.Tension` |
| These 3 PCG graphs | Consumers only | **Read** WorldField channels, never write them |
| `faraway_mother_pcg_assembly.py` | Verifier/stager | Validates manifest, applies graph bindings in-editor |
| `build_faraway_mother_pcg_ecosystem.py` | Manifest generator | Regenerates `specs/pcg/faraway_mother_pcg_manifest.v1.json` |

- These graphs **read** the World Field Bus; they do **not** publish to it.
- Graph construction must happen inside the Unreal Editor Python environment (no offline `.uasset` authoring).
- Each graph is a standalone PCG Graph asset (`is_standalone_graph = True`).

---

## 3. Graph 1: `PCG_Faraway_FabricRidge`

### 3.1 Purpose
Places macro-scale **fabric ridge geometry** along the high-tension seams of the WeaveRidge biome. These are the kilometer-scale woven terrain crests, shoulder folds, and silk vines that form the "anatomy" of the Faraway Mother — the primary silhouette masses the player navigates between.

### 3.2 Asset Path
```
/Game/EnvSandbox/PCG/FarawayMother/PCG_Faraway_FabricRidge
```

### 3.3 Inputs
| Input | Source | Type | Description |
|-------|--------|------|-------------|
| `Volume` | PCG Volume Actor | Bounding volume | Placement domain. Should cover the WeaveRidge biome zone (Z > +1500 uu). |
| `WorldField.Tension` | `UWorldFieldBus::SampleResonanceTension()` | Float (0–1) | Drives point density and scale. High tension → denser, more stretched instances. |
| `WorldField.Resonance` | `UWorldFieldBus::SampleResonanceTension()` | Int32 (N, M) | Harmonic mode (3, 5) selects mesh variant / material pulse frequency. |
| `WorldField.Moisture` | Synthetic — `0.0` at altitude | Float (0–1) | Ridge is arid; moisture is ~0 but available for LOD transitions. |

### 3.4 Point Generation
- **Sampler:** `PCGVolumeSamplerSettings` with `voxel_size` = 240.0 cm, `unbounded = False`.
- **Biome mask:** Only emit points where `altitude_uu > 1500.0 AND tension > 0.6` (matches `classify_biome` in `build_faraway_mother_pcg_ecosystem.py`).
- **Density filter:** `PCGDensityFilterSettings` — `lower_bound = 0.0`, `upper_bound = 0.85`, `b_invert_filter = False`.
- **Self-prune:** `PCGSelfPruningSettings` — `pruning_type = LARGEST_TO_SMALLEST`, `radius_similarity_factor = 0.25` to prevent overlap of macro masses.
- **Point count target:** ~30 points (matches manifest `WeaveRidge.point_count = 30`).

### 3.5 World Field Bus Read Pattern
```cpp
// Pseudocode — per-point sampling inside graph:
FWorldFieldSample Sample = UWorldFieldBus::SampleResonanceTension(PointWorldPos);
float DensityThreshold = Sample.Tension;          // WorldField.Tension
int32 ModeN = Sample.ResonanceN;                  // → material pulse
int32 ModeM = Sample.ResonanceM;
```

### 3.6 Mesh Spawner Configuration
- **Spawner type:** `PCGStaticMeshSpawnerSettings` (HISM path via `mesh_selector_parameters`).
- **HISM component name:** `PCG.HISM_Faraway_FabricRidge` (referenced by `sea_above_meshed_lane_height_aware_placements.v1.json`).
- **Mesh roles and sources:**

| Role | Primary Mesh | Fallback Mesh | Weight |
|------|-------------|---------------|--------|
| `fabric_ridge` | `/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchesA.SM_ATL_Palace_ArchesA` | `/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchA.SM_ATL_Palace_ArchA` | 3 |
| `shoulder_fold` | `/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_VaultBay.SM_Cathedral_VaultBay` | `/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Spire.SM_Cathedral_Spire` | 2 |
| `silk_vine` | `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Kelp_Tall.SM_Kelp_Tall` | `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Coral_Staghorn.SM_Coral_Staghorn` | 1 |

- **Material override:** `/Game/EnvSandbox/Materials/Instances/Environment/PBR_Auto/MI_T_FarawayMother_Gown_CelestialSilkJacquard` (canonical WeaveRidge MI).
- **Scale range:** `scale_min = (1.0, 1.0, 1.0)`, `scale_max = (4.0, 2.5, 1.5)` — macro masses, wider than tall (ridge form).
- **Rotation:** Yaw 0–359°, Pitch driven by `tension * 15°`, Roll from `sin(u * 10°) * 5°` (matches manifest rotation pattern).

### 3.7 Transform
- **PCGTransformPointsSettings:**
  - `scale_min = (1.0, 1.0, 1.0)`
  - `scale_max = (4.0, 2.5, 1.5)`
  - `uniform_scale = False` (anisotropic — ridges stretch along X)
  - `rotation_min = (0, -15, 0)`, `rotation_max = (0, 15, 359)`
  - `absolute_rotation = False`

### 3.8 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `Out` | HISM instances | Batched ISM/HISM instances of fabric ridge meshes |
| DataLayer | `DL_FarawayMother_Fabric` | Assigned via post-spawn actor tag or DataLayer subsystem |
| HLOD | `HLOD_FarawayMother_Instanced` | Layer assignment for World Partition HLOD |

### 3.9 World Field Bus Channels
| Channel | Direction | Usage |
|---------|-----------|-------|
| `WorldField.Tension` | **Read** | Density threshold, scale stretch, WPO amplitude |
| `WorldField.Resonance` | **Read** | Harmonic mode (N, M) → material pulse frequency |
| `WorldField.Moisture` | **Read** | Arid ridge detection (moisture ≈ 0 → ridge material dryness) |

---

## 4. Graph 2: `PCG_Faraway_DetailProps`

### 4.1 Purpose
Scatters **small-to-medium decorative props** across the LaceCanopy and FrillValley biomes: pearl bushes, lace trees, brocade flowers, frill rocks, and frill arches. These are the readable, mid-frequency details that give each biome its textile identity at player-walkable scale.

### 4.2 Asset Path
```
/Game/EnvSandbox/PCG/FarawayMother/PCG_Faraway_DetailProps
```

### 4.3 Inputs
| Input | Source | Type | Description |
|-------|--------|------|-------------|
| `Volume` | PCG Volume Actor | Bounding volume | Placement domain. Should cover LaceCanopy (mid-slope) and FrillValley (lowland). |
| `WorldField.Moisture` | Synthetic / `SampleResonanceTension` | Float (0–1) | Drives pearl bush density — wetter areas get denser understory. |
| `WorldField.FilterFlow` | Derived from cymatic field gradient | Vector2 (direction) | Orients lace tree canopies along valley airflow. |
| `WorldField.Resonance` | `UWorldFieldBus::SampleResonanceTension()` | Int32 (N, M) | Selects brocade flower variant by harmonic signature. |

### 4.4 Point Generation
- **Sampler:** `PCGVolumeSamplerSettings` with `voxel_size` = 180.0 cm, `unbounded = False`.
- **Biome mask:** Only emit where `tension < 0.6 AND altitude_uu < 1500.0` (complement of FabricRidge).
- **Density filter:** `PCGDensityFilterSettings` — `lower_bound = 0.0`, `upper_bound = 0.42`, `b_invert_filter = False`.
- **Self-prune:** `PCGSelfPruningSettings` — `pruning_type = LARGEST_TO_SMALLEST`, `radius_similarity_factor = 0.25`.
- **Exclusion:** `PCGExSampleNearestSplineSettings` + `PCGAttributeFilteringSettings` to carve points near ResonantSeamWay walkways (`TAG_SPLINE = "PCG_Spline"`), corridor = 700 uu. This keeps the walkable lanes clear (see `_wire_exclusion_filter` in `pcg_graph_builder.py`).
- **Point count target:** ~60 points (matches combined `LaceCanopy.point_count + FrillValley.point_count = 60`).

### 4.5 World Field Bus Read Pattern
```cpp
// Per-point sampling:
FWorldFieldSample Sample = UWorldFieldBus::SampleResonanceTension(PointWorldPos);
float Moisture = FMath::Clamp(0.5 - (Altitude / 8000.0) + (1.0 - Sample.Tension) * 0.3, 0.0, 1.0);
FVector2D FilterFlow = FVector2D(FMath::Cos(Sample.ResonanceN * PI * U), FMath::Sin(Sample.ResonanceM * PI * V));
```

### 4.6 Mesh Spawner Configuration
- **Spawner type:** `PCGStaticMeshSpawnerSettings` (HISM path).
- **Mesh roles and sources:**

| Role | Primary Mesh | Fallback Mesh | Weight |
|------|-------------|---------------|--------|
| `pearl_bush` | `/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchesA.SM_ATL_Palace_ArchesA` | `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Coral_ReefCluster.SM_Coral_ReefCluster` | 3 |
| `lace_tree` | `/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_VaultBay.SM_Cathedral_VaultBay` | `/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Spire.SM_Cathedral_Spire` | 2 |
| `brocade_flower` | `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Kelp_Cluster.SM_Kelp_Cluster` | `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Kelp_Tall.SM_Kelp_Tall` | 2 |
| `frill_rock` | `/Game/Greybox_Kit/SM_SM_Rock_1.SM_SM_Rock_1` | `/Game/Greybox_Kit/SM_SM_Rock_2.SM_SM_Rock_2` | 2 |
| `frill_arch` | `/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_EscherWaterfall.SM_Cathedral_EscherWaterfall` | `/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchA.SM_ATL_Palace_ArchA` | 1 |

- **Material overrides (per role):**
  - LaceCanopy props: `/Game/EnvSandbox/Materials/Instances/Environment/PBR_Auto/MI_T_FarawayMother_Veil_AquaticLullabyLace`
  - FrillValley props: `/Game/EnvSandbox/Materials/Instances/Environment/PBR_Auto/MI_T_FarawayMother_Corset_GildedAcanthusBrocade`
- **Scale range:** `scale_min = (0.35, 0.35, 0.35)`, `scale_max = (1.5, 1.5, 1.5)` — detail scale, not macro.
- **Rotation:** Yaw 0–359°, Pitch/Roll jitter from `transform_jitter = 18.0`.

### 4.7 Transform
- **PCGTransformPointsSettings:**
  - `scale_min = (0.35, 0.35, 0.35)`
  - `scale_max = (1.5, 1.5, 1.5)`
  - `uniform_scale = True`
  - `rotation_min = (0, 0, 0)`, `rotation_max = (0, 359, 0)`
  - `translation_min = (-18, -18, 0)`, `translation_max = (18, 18, 0)` (jitter)

### 4.8 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `Out` | HISM instances | Batched detail prop instances |
| DataLayer | `DL_FarawayMother_Fabric` | All detail props ride the Fabric DataLayer |
| HLOD | `HLOD_FarawayMother_Instanced` (foliage) / `HLOD_FarawayMother_Merged` (rocks/ruins) | Layer split by mesh role |

### 4.9 World Field Bus Channels
| Channel | Direction | Usage |
|---------|-----------|-------|
| `WorldField.Moisture` | **Read** | Pearl bush density, velvet sheen modulation |
| `WorldField.FilterFlow` | **Read** | Lace tree canopy orientation along valley airflow |
| `WorldField.Resonance` | **Read** | Brocade flower harmonic variant selection |
| `WorldField.Tension` | **Read** | Density threshold (low-tension areas get denser understory) |

---

## 5. Graph 3: `PCG_Faraway_WindZones`

### 5.1 Purpose
Creates **wind-responsive zones** along the ResonantSeamWay corridors and FrillValley airflow channels. These zones spawn Niagara ribbon emitters, wind-animated silk vine instances, and hair cascade ribbons that physically respond to the `WorldField.FilterFlow` vector field. This is the only graph that produces **animated / Niagara-driven** output — the other two are static ISM/HISM scatter.

### 5.2 Asset Path
```
/Game/EnvSandbox/PCG/FarawayMother/PCG_Faraway_WindZones
```

### 5.3 Inputs
| Input | Source | Type | Description |
|-------|--------|------|-------------|
| `Volume` | PCG Volume Actor | Bounding volume | Placement domain. Should cover ResonantSeamWay nodal corridors (\|Chladni\| < 0.12) and FrillValley airflow channels. |
| `WorldField.FilterFlow` | Derived from cymatic gradient | Vector2 (direction) | Primary wind direction vector for ribbon orientation and WPO phase. |
| `WorldField.Tension` | `UWorldFieldBus::SampleResonanceTension()` | Float (0–1) | Wind strength — high tension = more sag/less stiffness. |
| `WorldField.Resonance` | `UWorldFieldBus::SampleResonanceTension()` | Int32 (N, M) | Harmonic mode drives ribbon pulse frequency. |
| `WorldField.Moisture` | Synthetic | Float (0–1) | Valley fog density — high moisture areas get denser haze volumes. |

### 5.4 Point Generation
- **Sampler:** `PCGVolumeSamplerSettings` with `voxel_size` = 360.0 cm, `unbounded = False`.
- **Biome mask:** Only emit where `abs(chladni_val) < 0.12` (nodal lines = ResonantSeamWay) OR `altitude_uu < -1000.0` (valley airflow channels).
- **Density filter:** `PCGDensityFilterSettings` — `lower_bound = 0.0`, `upper_bound = 0.10` (sparse — wind zones are hero moments, not clutter).
- **Self-prune:** `PCGSelfPruningSettings` — `pruning_type = LARGEST_TO_SMALLEST`, `radius_similarity_factor = 0.25`.
- **Point count target:** ~30 points (matches manifest `ResonantSeamWay.point_count = 30`).

### 5.5 World Field Bus Read Pattern
```cpp
// Per-point sampling:
FWorldFieldSample Sample = UWorldFieldBus::SampleResonanceTension(PointWorldPos);
float FilterFlowStrength = Sample.Tension;  // tension doubles as wind strength
FVector2D FilterFlowDir = FVector2D(
    FMath::Cos(Sample.ResonanceN * PI * U),
    FMath::Sin(Sample.ResonanceM * PI * V)
);
float Sag = 1.0 - Sample.Tension;  // silk vine sag: low tension = more droop
```

### 5.6 Mesh Spawner Configuration
- **Spawner type:** `PCGStaticMeshSpawnerSettings` (HISM path for ribbon anchor meshes).
- **Mesh roles and sources:**

| Role | Primary Mesh | Fallback Mesh | Weight |
|------|-------------|---------------|--------|
| `silk_vine` | `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Kelp_Tall.SM_Kelp_Tall` | `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Coral_Staghorn.SM_Coral_Staghorn` | 3 |
| `hair_cascade_ribbon` | `/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_EscherWaterfall.SM_Cathedral_EscherWaterfall` | `/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchA.SM_ATL_Palace_ArchA` | 2 |
| `walkway_straight` | `/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchesA.SM_ATL_Palace_ArchesA` | `/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_VaultBay.SM_Cathedral_VaultBay` | 2 |
| `walkway_curved` | `/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_VaultBay.SM_Cathedral_VaultBay` | `/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchA.SM_ATL_Palace_ArchA` | 1 |
| `heart_gate` | `/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Spire.SM_Cathedral_Spire` | `/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchesA.SM_ATL_Palace_ArchesA` | 1 |
| `head_silhouette` | `/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Spire.SM_Cathedral_Spire` | `/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchA.SM_ATL_Palace_ArchA` | 1 |

- **Material override:** `/Game/EnvSandbox/Materials/Instances/Environment/PBR_Auto/MI_T_FarawayMother_Mantle_NightSkyVelvet` (canonical ResonantSeamWay MI).
- **Scale range:** `scale_min = (1.0, 1.0, 1.0)`, `scale_max = (6.5, 4.5, 1.5)` — hero-scale walkway and ribbon forms.
- **Rotation:** Yaw aligned to `FilterFlowDir` (wind-direction-oriented), Pitch driven by `tension * 7.5°`.

### 5.7 Niagara Ribbon Spawner (Unique to This Graph)
- After the static mesh spawner, attach a **PCGNiagaraSpawnerSettings** node to emit ribbons from each point.
- **Niagara system:** `NS_Faraway_WindRibbon` (to be authored; uses `WorldField.FilterFlow` vector for ribbon advection).
- **Ribbon orientation:** Aligned to `FilterFlowDir` per-point attribute.
- **Ribbon pulse:** Driven by `WorldField.Resonance` (N, M) → beat frequency.

### 5.8 Transform
- **PCGTransformPointsSettings:**
  - `scale_min = (1.0, 1.0, 1.0)`
  - `scale_max = (6.5, 4.5, 1.5)`
  - `uniform_scale = False` (ribbons stretch along Y)
  - `rotation_min = (0, -7.5, 0)`, `rotation_max = (0, 7.5, 359)`
  - `absolute_rotation = False`

### 5.9 Outputs
| Output | Type | Description |
|--------|------|-------------|
| `Out` | HISM instances | Walkway and ribbon anchor instances |
| Niagara | `NS_Faraway_WindRibbon` | Per-point ribbon emitters |
| DataLayer | `DL_FarawayMother_Fabric` | Walkways on Fabric |
| DataLayer | `DL_FarawayMother_Haze` | Haze volumes ride Haze layer |
| HLOD | `HLOD_FarawayMother_Instanced` | Instanced ribbon anchors |

### 5.10 World Field Bus Channels
| Channel | Direction | Usage |
|---------|-----------|-------|
| `WorldField.FilterFlow` | **Read** | Wind direction vector for ribbon orientation, WPO phase |
| `WorldField.Tension` | **Read** | Wind strength → silk vine sag, ribbon stiffness |
| `WorldField.Resonance` | **Read** | Harmonic mode (N, M) → ribbon pulse frequency |
| `WorldField.Moisture` | **Read** | Valley fog density for haze volume spawning |

---

## 6. Graph Construction Sequence (Artist / Agent Runbook)

### 6.1 Pre-conditions
- Unreal Editor 5.8 is running with `LV_FarawayMother_Prototype` loaded.
- `Plugins/Monolith` is disabled for the PCG build session (single-editor lock).
- The World Field Bus scaffold is compiled (`Source/BS_GodFile/MelodiaIntegration/MelodiaWorldFieldBus.h`).

### 6.2 Construction Order
1. **Create directory:** `/Game/EnvSandbox/PCG/FarawayMother/` (via `unreal.EditorAssetLibrary.make_directory`).
2. **Build `PCG_Faraway_FabricRidge`** — macro terrain masses first (defines silhouette).
3. **Build `PCG_Faraway_DetailProps`** — mid-frequency detail second (fills biome volume).
4. **Build `PCG_Faraway_WindZones`** — hero wind zones last (overlaps walkways).
5. **Assign graphs to PCG Volume actors** via `pcg_graph_builder.assign_pcg_graph(comp, graph)`.
6. **Run verifier:** `python Content/Python/faraway_mother_pcg_assembly.py --json`
7. **Confirm:** `ok: true`, all 3 graphs present in `pcg_graphs_staged`, all 4 WorldField channels connected.

### 6.3 Graph Wiring Template (Python — Editor)
```python
import unreal
import pcg_graph_builder as gb

# FabricRidge
graph, _ = gb.load_or_create_graph(
    "/Game/EnvSandbox/PCG/FarawayMother/PCG_Faraway_FabricRidge",
    "/Game/EnvSandbox/PCG/FarawayMother/"
)
inp = graph.get_input_node()
out = graph.get_output_node()
# ... Sampler → DensityFilter → SelfPrune → Transform → Spawner → Output
# (Follow the wire_scatter_chain pattern in pcg_graph_builder.py)
```

### 6.4 Acceptance Criteria
| Criterion | Test |
|-----------|------|
| All 3 graphs exist on disk | `python Content/Python/faraway_mother_pcg_assembly.py --json` → `ok: true` |
| Graph is standalone | `graph.is_standalone_graph == True` |
| HISM spawner configured | `mesh_selector_parameters.mesh_entries` non-empty |
| Material override valid | `unreal.EditorAssetLibrary.does_asset_exist(mi_path)` |
| Point count matches manifest | Sum of biome point counts = 120 |
| World Field channels read | All 4 channels listed in `world_field_channels` |
| No floating geometry | All instances raycast to `CanonicalLandscape` within 15 cm |
| DataLayer assigned | Actor tagged `DL_FarawayMother_Fabric` or `DL_FarawayMother_Haze` |

---

## 7. World Field Bus Channel Summary

| Channel | FabricRidge | DetailProps | WindZones | Published By |
|---------|:-----------:|:-----------:|:---------:|-------------|
| `WorldField.Tension` | Read (density, scale) | Read (inverse density) | Read (wind strength, sag) | `UMelodiaCymaticsSubsystem` |
| `WorldField.Resonance` | Read (material pulse) | Read (flower variant) | Read (ribbon pulse) | `UMelodiaCymaticsSubsystem` |
| `WorldField.Moisture` | Read (arid mask) | Read (bush density) | Read (fog density) | Synthetic / altitude-derived |
| `WorldField.FilterFlow` | — | Read (canopy orientation) | Read (wind direction, WPO phase) | Derived from cymatic gradient |

**No graph publishes to the World Field Bus.** All three are consumers only, preserving the single-writer guarantee (`UMelodiaCymaticsSubsystem` is the sole publisher).

---

## 8. File Manifest

| Asset | Path | Builder Script |
|-------|------|----------------|
| PCG Graph | `/Game/EnvSandbox/PCG/FarawayMother/PCG_Faraway_FabricRidge` | Editor Python (see §6.3) |
| PCG Graph | `/Game/EnvSandbox/PCG/FarawayMother/PCG_Faraway_DetailProps` | Editor Python |
| PCG Graph | `/Game/EnvSandbox/PCG/FarawayMother/PCG_Faraway_WindZones` | Editor Python |
| Niagara System | `/Game/EnvSandbox/Niagara/Faraway/NS_Faraway_WindRibbon` | Niagara Editor |
| Material (canonical) | `MI_T_FarawayMother_Gown_CelestialSilkJacquard` | Pre-existing |
| Material (canonical) | `MI_T_FarawayMother_Veil_AquaticLullabyLace` | Pre-existing |
| Material (canonical) | `MI_T_FarawayMother_Corset_GildedAcanthusBrocade` | Pre-existing |
| Material (canonical) | `MI_T_FarawayMother_Mantle_NightSkyVelvet` | Pre-existing |

---

## 9. References

- `Content/Python/faraway_mother_pcg_assembly.py` — verifier, REQUIRED_PCG_GRAPHS
- `Tools/PCG/build_faraway_mother_pcg_ecosystem.py` — manifest generator, biome classification
- `Content/Python/pcg_graph_builder.py` — graph construction utilities, wire_scatter_chain
- `Content/Python/pcg_portfolio_standards.py` — role/mesh table, PCG constants
- `Docs/PCG/FARAWAY_MOTHER_PCG_SYSTEM_ARCHITECTURE.md` — biome + WorldField architecture
- `Docs/Levels/LV_FarawayMother_Cymatic_State.md` — cymatic scaffolding state
- `specs/pcg/faraway_mother_pcg_manifest.v1.json` — canonical point distribution
- `specs/pcg/sea_above_meshed_lane_height_aware_placements.v1.json` — HISM_Faraway_FabricRidge reference
- `Source/BS_GodFile/MelodiaIntegration/MelodiaWorldFieldBus.h` — WorldField contract
