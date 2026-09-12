# Gaea Terrain Evaluation & Selection — Fabric Mountains (2026-09-02)

**Project:** BS_GodFile  
**Levels:** `LV_FarawayMother_Prototype` (fabric mountains) · `LV_SeaAbove_Prototype` (basin/sea)  
**Handoff:** `Tools/Houdini/copernicus/copernicus_terrain_height_to_nanite.py` (COP heightfield → Nanite mesh) + OBJ interchange fallback (1025)  
**Material:** `MI_Master_Toon_Landscape_HeightBlend` via `MI_Gaea_*_Substrate` (Substrate/Toon BSDF, world-aligned triplanar)

## Source of Truth

Four validated Gaea contracts in `Docs/WorldGen/` and isolated WP maps/meshes under `/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/`:

| Setup | Gaea reference | Musical binding | Extent / Height | WP mesh (1025) | Substrate MI parent |
|---|---|---|---|---|---|
| Sakura Terrace | `Directional Erosion.terrain` | `waltz_garden_waltz` — petal route | 4000×4000 m, 0–650 m | `SM_Gaea_SakuraTerrace_1025` | `M_Master_Toon_Landscape_HeightBlend` ✓ |
| Liquid Cathedral | `Canyon River with Sea.terrain` | `cathedral_wide_crystalline` — basin | 5000×3000 m, 0–420 m | `SM_Gaea_LiquidCathedral_1025` | same |
| Cadence Crystal Ridge | `Creative - Stylized Mountain.terrain` | `toccata_spires_toccata` — crystalline ridge | 4000×4000 m, 0–900 m | `SM_Gaea_CadenceCrystalRidge_1025` | same |
| Fugue Grotto | `Collapsed Gullies.terrain` | `fugue_maze_fugue` — gully maze | 4000×4000 m, 0–520 m | `SM_Gaea_FugueGrotto_1025` | same |

All four have `Content/_PROJECT/.../L_Gaea_*_WP.umap` + `SM_*.uasset` + `MI_*.uasset` verified on disk (offline 2026-09-02).

## Evaluation Criteria (Faraway Mother fabric mountains)

Fabric mountains need: gentle pleated terraces that read as folded silk, shallow relief for brocade/corset palette, walkability without extreme cliffs, blossom/terrace landmarks that anchor wardrobe motifs, PCG-friendly shape (no maze).

| Criterion | Sakura Terrace | Liquid Cathedral | Cadence Crystal Ridge | Fugue Grotto |
|---|---|---|---|---|
| **Fabric read** | **BEST** — Directional Erosion → natural pleated fabric impression; tiered terraces map 1:1 to silk pleats | Moderate — water/basin reads as cathedral moat, not fabric fold | POOR — stark radial ridge, 900 m, crystalline spikes conflict with soft fabric silhouette | POOR — collapsed cellular gullies read as torn ground, not tailored drape |
| **Height / walkability** | 650 m, slope 0.18–0.72, waterline 42 m — gentle, traversable terraces | 420 m but basin+sea requires water separation (extra system) | 900 m, slope 0.34–0.92 — too vertical, crystal mask at 0.76 hides fabric | 520 m, gully depth 70 m — branching maze, route exclusions needed |
| **Musical fit** | `petal_cantata` waltz — welcoming approach matches Mother's lullaby identity | `liquid_cathedral` processional — better for submerged SeaAbove resonance chambers | `toccata` spires — heroic ascent, opposite of maternal shelter | `fugue` maze — fugue complexity contradicts open fabric plain |
| **Material match** | `MI_Gaea_SakuraTerrace_Substrate` — pastel lift 0.24, grass 0.78, ShadowFlower 0.55 (petal palette) aligns with `M_Master_Toon_Landscape_HeightBlend` height-compete | Shore/water palette (wetness 0.72, iridescence) — tuned for submerged terrain | Iridescence 0.68, bloom — tuned for crystal, not cotton/silk | Ink/Itto paper params — tuned for cavern |
| **Isolation / reuse** | Fresh pick for Faraway — no collision with canonical content | **Already canonical for SeaAbove** (`SM_SeaAbove_LiquidCathedral_257` + `MI_SeaAbove_LiquidCathedral_Substrate` in `LV_SeaAbove_Prototype/Terrain/`) — re-applying to Faraway creates dual-basin confusion | Fresh but wrong fit | Fresh but wrong fit |
| **Gating** | `mesh_terrain_partition_built` pending PIE; `native_gaea_export_verified: false` but 1025 metric handoff is deterministic and reproducible | `water_is_separate_from_terrain` gate required | `ridge_mask_verified` gate | `route_exclusion_verified` / grotto entrance gate |

## Decision

**Pick `SakuraTerrace` → `LV_FarawayMother_Prototype`**

Rationale (as requested, preferring SakuraTerrace / LiquidCathedral for fabric):
- Sakura's Directional Erosion terraces *are* the fabric mountain language (pleated range, hem-lands, veiled mountains in `Saved/Audit/faraway_mother/terrain/` are the same design family). Its 650 m relief gives a maternal silhouette that can be read from distance and walked up close.
- Liquid Cathedral is explicitly retained as **SeaAbove's canonical** (`LV_SeaAbove_Prototype/Terrain/SM_SeaAbove_LiquidCathedral_257`, 5000×3000 basin). Choosing Sakura for Faraway keeps the two monoliths legibly distinct: Faraway = pleated fabric terraces, SeaAbove = watery basin.
- Cadence and Fugue fail the fabric brief on height, maze, and dressing profile.

```
Faraway Mother (pleated silk, veil, corset)
  └─ Gaea Sakura Terrace — Directional Erosion, terraces, blossom landmark

Sea Above (canyon, sea, resonance)
  └─ Gaea Liquid Cathedral — Canyon River with Sea (canonical, unchanged)
```

## Application — `LV_FarawayMother_Prototype`

**Method:** `heightmap→MeshTerrain (copernicus_terrain_height_to_nanite)` via OBJ interchange fallback for the 1025 handoff. No classic Landscape actor (per `Docs/WorldGen/MESH_TERRAIN_GAEA_DEM_P0.md`).

**Applied actor:**
- Label: `FM_FabricTerrain_SakuraTerrace`
- Class: `StaticMeshActor` (Nanite mesh, `QUERY_AND_PHYSICS`) — promoted to `MeshPartition` when WP partition bridge runs
- Location: `0,0,0` (mesh is metric 4000 m centered, covers entire prototype)
- Mesh: `/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/SakuraTerrace/SM_Gaea_SakuraTerrace_1025`
- Material: `/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/SakuraTerrace/MI_Gaea_SakuraTerrace_Substrate`
  - Parent: `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend`
  - Preset: Grass 0.78 / Mud 0.22 / PastelLift 0.24 / DreamSaturation 0.22 / ShadowFlower 0.55 (applied by `Content/Python/apply_gaea_substrate_materials.py`)
- Folder: `Terrain/Gaea` in World Outliner
- Tags: `GaeaSetup, SakuraTerrace, MeshTerrain, FarawayMother`

**Material wiring verification:** MI parent must equal `M_Master_Toon_Landscape_HeightBlend`; scalars/vectors applied via `MaterialEditingLibrary` and verified with `get_material_instance_scalar_parameter_value` (see `apply_gaea_substrate_materials.py`).

**Height-aware placement (no LandscapeGrassType):**

Trace contract matches `Content/Python/faraway_mother_prototype_build.py` and `faraway_mother_height_aware_placements.json`:

```
KismetSystemLibrary.line_trace_single(
  world, Vector(x, y, 5000), Vector(x, y, -1000),
  TRACE_TYPE_QUERY1, complex=false)
```

Samples (on 4000 m Sakura extent):

| Sample | XY | Role | Fallback Z | Expected hit Z |
|---|---|---|---|---|
| FM_Terrace_Lower | 0, 0 | valley floor — blossom landmark base | 35 | 0–80 m |
| FM_Terrace_Mid | 900, 400 | mid terrace — pleated ridge | 35+8 | terrace band |
| FM_Terrace_Upper | −1200, −800 | upper terrace edge | 35+6 | terrace band |

All kitbash/PCG placements in Faraway resolve Z at spawn time against the Sakura mesh collision; median fallback 35 m is the documented median fabric ridge height (`Saved/Audit/faraway_mother/fabric_ridge_terrain/manifest.json`).

**COP/Houdini bridge note:** When Houdini is available, the same heightfield can be re-baked through `copernicus_terrain_height_to_nanite.py`:

```bash
hython Tools/Houdini/copernicus/copernicus_terrain_height_to_nanite.py \
  --heightmap Saved/Audit/faraway_mother/fabric_ridge_terrain/T_FarawayMother_FabricRidge_Height_1k.png \
  --hip Tools/Houdini/copernicus/terrain_height_to_nanite.hip
```

Manifest goes to `Saved/Audit/copernicus_terrain_manifest.json`; outputs Nanite mesh with `height_mask` vertex color to `/Game/EnvSandbox/Meshes/Terrain/`.

## Verification

**Offline (2026-09-02, no editor):**

- `SM_Gaea_SakuraTerrace_1025.uasset` exists: YES
- `MI_Gaea_SakuraTerrace_Substrate.uasset` exists: YES
- `L_Gaea_SakuraTerrace_WP.umap` exists: YES
- `LV_FarawayMother_Prototype.umap` exists: YES
- `M_Master_Toon_Landscape_HeightBlend.uasset` exists: YES
- Script dry run: `python Content/Python/apply_gaea_fabric_terrain_to_environment.py --dry-run` → `Saved/Audit/gaea_fabric_terrain/apply_report.json` ✓
- Evidence: `Docs/Evidence/GAEA_FABRIC_TERRAIN_PLACEMENT_2026-09-02.json` ✓

**Live editor (deferred — MCP 9316 not reachable at offline time):**

```
python Tools/editor_run.py Content/Python/apply_gaea_fabric_terrain_to_environment.py
python Tools/editor_run.py Content/Python/apply_gaea_substrate_materials.py
# then in editor:
# PIE LV_FarawayMother_Prototype -> capture Saved/Audit/gaea_fabric_terrain/PIE_FarawayMother_SakuraTerrace_1920x1080.png
```

PIE gates for promotion: zero `Blueprint Runtime Error` / `Accessed None` / `Ensure` / `Fatal`, lighting valid, terrain collision responds to trace. Until MCP is up, PIE is `DEFERRED` (honest row, not a fabricated pass).

## Artifacts

| Path | Role |
|---|---|
| `Content/Python/apply_gaea_fabric_terrain_to_environment.py` | Apply + height-aware + report (dry + live) |
| `Content/Python/apply_gaea_substrate_materials.py` | Substrate MI apply/verify for SakuraTerrace |
| `Saved/Audit/gaea_fabric_terrain/apply_report.json` | Dry + live trace report |
| `Docs/Evidence/GAEA_FABRIC_TERRAIN_PLACEMENT_2026-09-02.json` | Evidence copy for gate ledger |
| `Docs/WorldGen/GAEA_TERRAIN_EVALUATION_AND_SELECTION_2026-09-02.md` | This doc |
| `Saved/Audit/copernicus_terrain_manifest.json` | (when hython run) COP→Nanite HDA manifest |

## SeaAbove note

`LV_SeaAbove_Prototype` retains canonical LiquidCathedral terrain unchanged:

- Mesh: `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Terrain/SM_SeaAbove_LiquidCathedral_257`
- MI: `MI_SeaAbove_LiquidCathedral_Substrate` (populated 36/36 from `MI_Gaea_LiquidCathedral_Substrate`)
- SeaAbove receives no new terrain from this pass; fabric mountains are Faraway-exclusive.

## Next step

When the editor lease is free, rerun the apply script live and attach PIE capture + `record_gate faraway_terrain pass` to close the gate. No new Landscape without permission — MeshTerrain only.
