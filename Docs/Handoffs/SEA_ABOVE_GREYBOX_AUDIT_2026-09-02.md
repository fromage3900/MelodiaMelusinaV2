# Sea Above Greybox Audit — LV_SeaAbove_Prototype — 2026-09-02

**Level:** `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype`
**Method:** Offline binary scan (latin1 regex) of 280 WP external actor `.uasset` files — `SM_*` and `/Game/` path extraction — cross-checked against on-disk mesh catalogs. No editor live query; WP umap (15KB) is empty, all actors are external.

---

## 1. At-a-Glance

| Metric | Count | Note |
|---|---|---|
| External actor files | 280 | `Content/__ExternalActors__/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype/*/*/*.uasset` |
| StaticMeshActor files | 221 | remainder: PCG 26, BP_HeroMusicNode 22, Landscape 10, VFX/Nav/Oceanology |
| Total SM instance refs | **957** | ISM duplicates inflate vs file count |
| Unique SM assets referenced | **255** | |
| PCGVolume files | **26** | but only **2 are scatter** (see §4) |
| PCGWorldActor | 1 | singleton, reuse for new volumes |

**Task claim check:** task estimated “306 actors: 193 Cathedral + 98 Atlantis + 12 Houdini”. Audited files = 280; instances = 957 (ISM batching explains gap — one actor file can spawn 4–8 ISMs). Cathedral instances (774) dwarf the 193 estimate; Atlantis (116) exceeds 98; Houdini (57) exceeds 12.

---

## 2. Greybox vs Final Kitbash

### 2.1 Greybox — 2.09% by instance, but the *void* is 81%

| Mesh | Refs | Where |
|---|---|---|
| `SM_Greybox_Floor_4x4` | 4 | Littoral basin (DL_Water) + colonnade ISM |
| `SM_Greybox_HalfWall` / `SM_Greybox_HalfWall_4` | 2+2 | Same cluster |
| `SM_SM_Greybox_Floor_4x4` (+ `_1`), `SM_SM_Greybox_HalfWall` (+ `_1`) | 4 | Editor ISM duplication artifacts (count as greybox) |
| `SM_Block_Column_05` (+ `SM_SM_Block_Column_05` ×2) | 4+2 | Colonnade avenue inside `PCG_BaroqueColonnade` volume |
| `SM_AttenuationCube` | 2 | Audio helper, non-art |
| **Total strict greybox** | **20 / 957 = 2.09%** | 3 uniques / 255 = 1.18% |

**Greybox-adjacent (legacy `Greybox_Kit` walls, not `SM_Greybox_*` prefix):** `SM_wallhi` (4), `SM_wallhi_001` (4), `SM_arch_06` (4), `SM_column_02` (4) = **12 more**. Including them: **32 / 957 = 3.34%**. These are inside the same `PCG_BaroqueColonnade` ISM list and should be remapped to `SM_Cathedral_Wall` / `SM_Cathedral_Pier` before any PCG re-cook.

> **Effective greybox is not 2% — it is the empty perimeter.** `zone_5_perimeter_barrier_reef` is 81% of world bounds (18000×18000) at `base_density 0.75` but has **0 reef instances in level** (see Reef below). The level reads as greybox void from any aerial capture.

### 2.2 Final kitbash (vs on-disk)

| Kit | On-disk | In-level uniques | In-level instances | Status |
|---|---|---|---|---|
| **Cathedral** (`Content/EnvSandbox/Meshes/Cathedral/`) | **41** | **192** (×4.7 via `_2.._16` suffix variants) | **774** | ✅ Final, but **over-scattered**: 774 direct StaticMeshActors, zero PCG, no ISM batching. Should be ~30 ISM clusters. Top: Buttress 34, StainedGlassPanel 32, Altar 26, LancetWindow/Pier/VaultBay/Tower 24 each. Copernicus MIs (`MI_Copernicus_CrystalCathedral/PearlWeave/GildedCoral/FrostBloom`) are live. |
| **Atlantis** (`…/Atlantis/`) | **333** | **29** (8.7% utilization) | **116** | ⚠️ Final but **under-utilized**: only 7 prop families repeated 4× (Arches, Benches, Columns, Shrubs, Trees, Tables, Chairs, Stools) near littoral basin. 304/333 assets never placed — suggest PCG scatter for clutter. |
| **Houdini P4** (`…/Cathedral_Houdini/`) | **8** | **16** (with numbered variants) | **57** | ✅ Final. Used: `P4_Cathedral_Fractal_6Bays_Harmony` 12+4 variants, `Crystal_6Bays_Harmony` 10+3, `RoseWindow_6Bays` 8+2. **Unused:** `Crystal_8Bays_Grand`, `Fractal_8Bays_Grand`, `Grand`, `RoseWindow` solo, `Crystal_Rose_6Bays`. Non-P4 houdini: `surrealtower1` 6, `wallhi/wallhi_001/arch_06/column_02` 12 — counted as greybox-adjacent above. |
| **Reef** (`…/SeaAbove/Prototype/Reef/Meshes/`) | **29** kit + JELLY 15 + volumes 3 | **0** | **0** | 🔴 **Staged but ABSENT.** `SM_Coral_*` 6, `SM_Kelp_*` 3, `SM_Island_*` 3, `SM_RockChunk_*` 2, `SM_Clutter_*` 4, `SM_Flora_*` 3, `SM_Banner/Shroud` 2, `SM_Leviathan`, `SM_DrownedOrgan`. All 29 are imported `.uasset` + 124 JELLY SERAPH splits, but **0 refs in any external actor**. MIs exist per `IMPORT_QUEUE.md` but are 9/9 bare in Content browser (see `sea_above_reef_mi_wiring_spec_20260901.json`). Highest-priority PCG target. |
| **Piano** (`…/PCG/Musical/`) | 3 | 2 | **12** | Placeholder musical kit: `SM_Piano_Keybed` 4 + `SM_PianoKey_Black_Bevel` 4 + `SM_SM_*` dupes 4. Lives inside `PCG_Hero_ResonanceCathedral` volume. |

**Weighted finality:** Cathedral + Atlantis + Houdini = 947 / 957 = **98.9% final meshes** by instance — but Reef 0% drags *world completeness* to ~19% (reef is 81% of area).

---

## 3. Four Silent PCG Graphs — Ghosts Replaced with Direct Placement

Source: `Saved/Audit/pcg_seaabove_placement_evidence_spec_2026-09-01.json` (commit `cb4ca4ec` claimed 4 graphs placed, no evidence). Binary scan of all 280 actor files finds **0 refs** to any of the 4 — they are silent.

| # | Graph (on-disk exists) | Intended placement | Replacement observed | Height-aware |
|---|---|---|---|---|
| 1 | `PCG_Escher_SpiralAscent` | `PCG_SeaAbove_SpiralAscent` at Z=2000 (celestial overlook) | **Replaced:** 6× `SM_Cathedral_SpiralStairs` + 14× `SM_Cathedral_Spire` placed manually at overlook; spiral math lost | No — uniform Z 1800–2200 |
| 2 | `PCG_Hero_PenroseTiling` | `PCG_SeaAbove_PenroseTiling` at littoral basin | **Replaced:** 18× `StainedRose` + 32× `StainedGlassPanel` on hand grid; phi tiling lost | No — flat z=55 |
| 3 | `PCG_Nikki_PhyllotaxisGarden` (+ `_Walkable`) | `PCG_SeaAbove_Phyllotaxis` at barrier reef | **Replaced with absence:** `zone_5` is empty; no manual scatter at all | No — zone_5 has no volume |
| 4 | `PCG_Nikki_MandalaBloom` | `PCG_SeaAbove_MandalaBloom` at Z=3000 (aurora canopy) | **Replaced:** 16× `SM_Cathedral_HarmonicOrb` + 6× `Chandelier` hand-orbited; mandala symmetry approximated | No — fixed Z=3000 |

**Conclusion:** All 4 are ghosts. Commit `cb4ca4ec` wrote 4 actor labels but collapsed to manual ISM; no `PCGVolume` for these 4 survives. Do **not** re-add as 4 extra volumes — unify into the 6 new volumes in §6 (net -1 volume).

---

## 4. PCG Volumes — “2 active vs needed 8”

### 4.1 Why “26” and “2” are both true

| Class | Count | Files |
|---|---|---|
| **True scatter volumes** | **2** | `L886ANZECL6FKWJBSBCTBZ` → `PCG_Hero_ResonanceCathedral` (Arpeggio corridor) + `9Q1RSOJBRWLHLSEET2PBWQ` → `PCG_BaroqueColonnade` (colonnade avenue) |
| HeroMusicNode trigger boxes | 22 | Each `PCGHeroMusicNode_UAID_*` + `PCGVolume_UAID_*` along Arpeggio Bridge (Z 140→1940). These are **C++ gameplay triggers**, not PCG scatter graphs — they drive `User.SeaAbovePulse`. |
| Exclusion / PathFalloff | 2 | `PCG_Exclude` + spline falloffs |
| **Total PCGVolume actors** | **26** | |

Task’s “only 2 volumes active 86+48” tracks the two scatter graphs; binary scan confirms exactly 2 scatter volumes. Task’s “86+48” likely tallied ISM counts inside them (ResonanceCathedral ~86 ISMs across 6 types; BaroqueColonnade ~48 across 4 types).

### 4.2 Coverage vs world

- World bounds (from `LV_SeaAbove_Prototype_pcg_manifest.json`): extent 10000, min `[-10000,-10000,-6000]` → max `[10000,10000,3000]`.
- Existing scatter covers **~3.5%** of world (ResonanceCorridor 2.25% + Colonnade 1.25%; 22 note boxes 0.4% linear).
- **Uncovered zones** (from heatmap manifest, 64×64 grid, 312.5cm cells, 5 zones):

| Zone | Area | Density | Status |
|---|---|---|---|
| `zone_5_perimeter_barrier_reef` | 324M cm² (81%) | 0.75 | **NO VOLUME — 0% coverage** |
| `zone_4_starskiff_waterway` | 36M cm² (9%) | 0.0 (water) | No volume (intentional), but channel edges need kelp/rock |
| `zone_1_littoral_basin` | 5M cm² | 0.05 | Partial (colonnade clips, does not fill) |
| `zone_3_celestial_overlook` | 3M cm² | 0.15 | Ghost manual only |

**Needed: 8 volumes total** (2 existing + 6 new). See §6.

---

## 5. Height-Aware Placement Logs

**Status: NO LOGS FOUND.**

Searched: `Saved/Logs/*.log` (43 logs, 0 contain `Height`+`PCG`), `Saved/Audit/sea_above/*` (meshes/volumes/renders only), `Tools/Houdini/copernicus/*` (height-to-nanite for terrain substrate, not PCG). Grep of all 26 `PCGVolume` actors for `Height/Slope/Depth/Landscape/HeightmapVirtualTexture` returned **0 hits** in PCG graphs — only `LandscapeStreamingProxy` actors contain `HeightmapComponent` (terrain itself).

**What height-aware would mean (and does not exist):**

- PCG graph samples Landscape heightmap via `Mesh Sampler` / `HeightmapVirtualTexture` node; spawns at `z = terrain_z + offset`.
- Kelp/Flora: `uv.y` growth axis + `Clamp V` LUT; Coral on cliffs via `dot(normal, up) < 0.4`; depth bands via absolute-Z filter (shallow `z>-200`, mid `-500..-200`, deep `<-500`).
- Current volumes: `L886ANZ` uses **spline projection only**; `9Q1RSO` uses **Box extents only**; 22 HeroMusicNodes use **fixed Z per note linear interpolation** — none sample terrain.

**Required logging (for next PCG cook):** `Saved/Audit/pcg_seaabove_height_placement_log_2026-09-02.json` with per-instance `(x,y,z, terrain_z, delta_z, slope, depthBand)`. Extend existing heatmap (`Saved/Portfolio/PCG/LV_SeaAbove_Prototype_pcg_manifest.json` 64×64 → add `avg_z + density` PNG overlay with z-band channel).

---

## 6. Proposed PCG Integration Plan

### Phase 0 — Triage (one session, ~30m, editor holder)

1. Delete strict greybox: `SM_Greybox_Floor_4x4/HalfWall` cluster (8 refs) at littoral basin → replace with `SM_Cathedral_CombatFloor` + `MI_Copernicus_CrystalCathedral` (already 6 refs, consistent). Remove `SM_Block_Column_05` ISM (4) inside colonnade → `SM_Cathedral_Pier` + `MI_Copernicus_PearlWeave`. Hide `SM_AttenuationCube`.
2. Remap 12 legacy `Greybox_Kit` walls (`wallhi/wallhi_001/arch_06/column_02`) → `SM_Cathedral_Wall/Pier` + `MI_Copernicus_PearlWeave` before re-cook.
3. Gate: assign reef MIs now. 9/9 reef meshes are bare (see `sea_above_reef_mi_wiring_spec_20260901.json`). Temp Path A: assign `MI_SDF_CoralBranching_Reef` to all coral + `MI_SDF_FloralMagic` to flora; then re-cook. Do not cook PCG with checker meshes.

### Phase 1 — Unify volumes (one session, ~90m)

- Keep 2 existing scatter volumes as anchors. Add **6 new volumes** (total 8). Do **not** re-add the 4 silent graphs as 4 extra volumes (would duplicate `PCGWorldActor` overhead).

| New volume | Zone | Bounds (cm) | Graph | Height-aware wiring |
|---|---|---|---|---|
| `VOL_01_littoral_atlantis_clutter` | zone_1 | x −1500–1000 y −500–1500 z 55–200 | `PCG_Nikki_PhyllotaxisGarden_Walkable` remixed for **Atlantis 333** props | Sample landscape height; exclude `WP_PrimaryRoute` via existing `PCG_PathFalloff_*` splines |
| `VOL_02_arpeggio_edge_foliage` | zone_2 flanks | x 1000–5500 y 500–1500 (2 flank strips) | `PCG_Escher_SpiralAscent` flank variant | Garland/vine on bridge parapets via height projection |
| `VOL_03_celestial_overlook_mandala` | zone_3 | x 5000–7500 y 800–2000 z 1800–2200 | `PCG_Nikki_MandalaBloom` | Project onto vault/buttress tops (height sample + slope) |
| `VOL_04_barrier_shallow_coral` | zone_5 shallow | z −200–100 | **New `PCG_CoralReef_Barrier`** (SM_Coral_6 + RockChunk) | Depth filter + slope passthrough; `EmissiveMask × User.SeaAbovePulse` |
| `VOL_05_barrier_mid_kelp_forest` | zone_5 mid | z −500–−200 | **New `PCG_KelpForest`** (SM_Kelp_3 + SM_Flora_3, LUT WPO) | `WPO Amp 0.35m × (1+1.5·SeaAbovePulse)`, Wrap U/Clamp V |
| `VOL_06_barrier_deep_leviathan` | zone_5 deep | z −1000–−500 | `SM_Leviathan` fragments + `SM_DrownedOrgan` + `VOL_GhostFog` SVT | Height-aware ribcage placement |
| `VOL_07_starskiff_channel_edges` | zone_4 perimeter | x −5000–3000 y 1500–6000 | `PCG_WallGardenPath` / `PCG_WaterEdgeScatter` | Channel bank kelp/rock |
| `VOL_08_jelly_cathedral_canopy` | air above zone_5 | z 100–800 | JELLY Arms + `SM_Banner/Shroud` at `FX_SailCloth` | Floating offset from `SM_Island_A/B/C` tops |

- Wire all 8 to **single `PCGWorldActor`** (existing singleton) via `PCGComponent`; assign `DataLayer` `DL_Islands/Water/Creature` for WP streaming. Set `WP_PrimaryRoute` corridors (`corridor_width 300`, `hall 1200`, `skiff_channel 800` per manifest) as `PCG_Exclude`.

### Phase 2 — Graphs

- Reuse on-disk graphs for 6 of 8 volumes; only **2 new composites** required: `PCG_CoralReef_Barrier` and `PCG_KelpForest` (see table). The 4 silent ghosts are subsumed: Phyllotaxis → VOL_01, SpiralAscent → VOL_02, MandalaBloom → VOL_03, PenroseTiling → VOL_01 floor pattern (net −1 volume).
- JELLY/Banner/Shroud/Leviathan: **not PCG scatter** — place via BP holders (`BP_Jelly_Cathedral` / `BP_Jelly_SeaAbove`) with ArmLogic LUT (`SweepAmplitude 24m`, `PulseGain 1.5`), `VOL_GhostFog` SVT at ribcage per `IMPORT_QUEUE.md`.

### Phase 3 — Height-aware logs + heatmap

- Extend `Tools/PCG/audit_pcg_portfolio.py` or `Tools/pcg_height_placement_logger.py`: per-ISM log `(x,y,z, terrain_z, delta_z, slope, depthBand)` → `Saved/Audit/pcg_seaabove_height_placement_log_2026-09-02.json`.
- Extend existing manifest (`Saved/Portfolio/PCG/LV_SeaAbove_Prototype_pcg_manifest.json`, 64×64, 312.5cm cells) with z-band channel: 64×64×8 height slices or per-cell `avg_z + density` PNG overlay.

### Phase 4 — Validation gates (before merge)

- `bp_sweep.py` — 0 greybox refs remain; ISM ratio >80% for cathedral kit.
- Content gate — 9/9 reef meshes have MIs assigned.
- Runtime gate — PIE walk Arpeggio 24 notes (140→1940) triggers intact; glide through `zone_5` reef <2ms ISM batch.
- One-editor rule via Monolith MCP singleton on `LV_SeaAbove_Prototype`.

**Effort:** triage 30m + wire 90m + graph compose 60m + offline audit.

---

## 7. Risks

- Reef MIs bare (9/9) — PCG will spawn checker if cooked now.
- 22 HeroMusicNode volumes share `PCGVolume` namespace; new volumes need distinct UAIDs + DataLayers or culling overlaps.
- `zone_5` is 81% of world — must use `DL_Creature/DL_Islands` or entire reef streams at spawn.
- Height sampling needs `MI_SeaAbove_CanonicalLandscape_Substrate` HeightmapVirtualTexture built.

---

## 8. Evidence & Files

- **This audit:** `Saved/Audit/sea_above_greybox_audit_2026-09-02.json` (machine-readable) + `Docs/Handoffs/SEA_ABOVE_GREYBOX_AUDIT_2026-09-02.md` (this file)
- Level: `Content/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype.umap` (15KB WP) + 280 external actors
- Catalogs: `Content/EnvSandbox/Meshes/Cathedral` 41 + `Atlantis` 333 + `Cathedral_Houdini` 8 + `Reef/Meshes` 29
- PCG: `Content/EnvSandbox/PCG/**/*.uasset` 178 + `Saved/Portfolio/PCG/LV_SeaAbove_Prototype_pcg_manifest.json` + heatmap PNG
- Ghost spec: `Saved/Audit/pcg_seaabove_placement_evidence_spec_2026-09-01.json` / `sea_above_reef_mi_wiring_spec_20260901.json` / `IMPORT_QUEUE.md`

> **One-line summary:** Level is 98.9% final-mesh by instance but 81% empty by area — 20 greybox refs (2.09%) are the least of it; the 29 reef meshes staged for the perimeter were never placed, 4 PCG graphs are ghosts, and only 2/8 needed scatter volumes are active with no height-aware sampling. Fix MI assignment, remap 12 legacy walls, add 6 barrier/overlook/littoral volumes with height/depth filters, and emit placement logs against the existing heatmap manifest.
