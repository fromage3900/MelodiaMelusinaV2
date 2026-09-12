# PCG Heatmap Usage Audit — 2026-09-02

**Scope:** BIOME_BANDS usage, heatmap textures, PCG volumes (SeaAbove / FarawayMother / ScaleWorldProof), height-aware raycast logs, instance counts per zone.

**Artifacts:**
- JSON: `Saved/Audit/pcg_heatmap_2026-09-02.json` (machine-readable, 10 gaps + 10 recs)
- Sources: `pcg_scale_world_pipeline.py`, `build_faraway_mother_height_aware_pcg.py`, `Saved/Audit/faraway_mother_height_aware_pcg.json`, `pcg_hero_graph_tree_audit.json`, `pcg_visual_world_plan.json`, `pcg_scale_world_chunk_grid.json`, `pcg_universal_audit.json`, `Saved/Portfolio/PCG/LV_SeaAbove_Prototype_pcg_manifest.json`, `Docs/Evidence/SEA_ABOVE_LEVEL_ORGANIZATION_2026-09-01.json`

---

## 1. World Partition & BIOME_BANDS

| Param | Value |
|-------|-------|
| WP_CELL_SIZE_CM | **25,600** (256 m) — `pcg_scale_world_pipeline.py:18` |
| Generator | `musical_pcg_scale_v1` seed 3900 |
| BIOME_BANDS (5) | `stone_court`, `moss_rim`, `blue_void`, `crystal_meadow`, `wind_shelf` |
| Selection | `(0,0)=stone_court` forced; else `BIOME_BANDS[stable_chunk_seed(seed,x,y) % 5]` |

### Distribution

**Radius 1 — 9 chunks (`pcg_scale_world_chunk_grid.json`)**

| Band | Count | % |
|------|-------|---|
| wind_shelf | 4 | **44.4%** |
| stone_court | 3 | 33.3% |
| moss_rim | 1 | 11.1% |
| crystal_meadow | 1 | 11.1% |
| **blue_void** | **0** | **0.0%** ⛔ |

**Radius 2 — 25 chunks (`pcg_visual_world_plan.json`)**

| Band | Count | % | vs uniform 20% |
|------|-------|---|----------------|
| stone_court | 8 | 32.0% | +12pp |
| wind_shelf | 7 | 28.0% | +8pp |
| crystal_meadow | 6 | 24.0% | +4pp |
| moss_rim | 3 | 12.0% | −8pp |
| **blue_void** | **1** | **4.0%** | **−16pp (5× under)** |

**Hero slots:** r=1 `5/9 = 55.6%` chunks carry a hero; r=2 `7/25 = 28.0%` (majority biome-only). All five hero types appear in both radii; ResonanceCathedral + ArpeggioBridge double-up at r=2.

**Finding:** `blue_void` is effectively dead content at this seed — deterministic hash starvation, no design intent doc, no override.

---

## 2. PCG Graph Inventory

| Location | Graphs |
|----------|--------|
| **Total** | **145** PCG graphs + 9 collections |
| Baroque | 32 (largest) |
| Universal | 35 |
| Escher | 18 |
| WP | 16 |
| Musical/Hero (authoritative) | **6** |
| Sakura | 9, Alpine 2, Cosmic 2, Cyberpunk 2, Desert 2, Grotto 1 |

**Authoritative hero graphs (all `ok=true`, `pcg_hero_graph_tree_audit.json`):**

| Graph | Nodes | Meshes | Greybox | Final | Tensor |
|-------|-------|--------|---------|-------|--------|
| ResonanceCathedral | 24 | 6 | 4 | 2 (Piano) | required (2 ops) |
| ArpeggioBridge | 16 | 3 | **3 (100%)** | 0 | disabled |
| BellTreeGarden | 14 | 4 | **4 (100%)** | 0 | disabled |
| XylophoneTrail | 12 | 2 | **2 (100%)** | 0 | disabled |
| CrystalHarpGrove | 24 | 5 | 4 | 1 (Piano Keybed) | — |
| WaterGameplayInteractive | — | — | — | — | — |
| **Total** | — | **20** | **17 (85.0%)** | **3 (15.0%)** | — |

> **85% greybox** — only Piano meshes are final. Three hero graphs are 100% greybox.

**PCG build health:**

| Check | Result |
|-------|--------|
| `L_PCG_Hero_ScaleWorldProof` dry-run | ✅ PASS (4 stages) |
| `L_PCG_Hero_ScaleWorldProof` live | ❌ **FAIL return_code 1** (`pcg_scale_world_build.json`) |
| `pcg_universal_audit` chains | ❌ `chains_valid=false` — only 2/13 graphs chain_ok (ExclusionFalloff, WallDetail); `node_count=0` for FoliageDensity, RockScatter, MeadowBloom, BlossomPath, LanternGrove, etc. |
| `pcg_hero_graph_tree_audit` | ✅ 5/5 ok |

---

## 3. Heatmap Textures — 0% Drive Placement

| Category | Count | % driving PCG | Note |
|----------|-------|---------------|------|
| **Engine Texture2D sampling PCG density** | **0** | **0.0%** | No graph has a Texture parameter feeding DensityFilter/SurfaceSampler |
| Figma UI slots | 3 | 0% | `T_Melodia_Figma_*Heatmap` — presentation placeholders |
| ScatterMask (spec) | 1 ref | 0% live | `pcg_graph_spec_faraway_2026-09-03.json` `MaskThreshold 0.5` — Houdini mask, never wired to live Texture asset |

**Offline PNG generators (all synthetic, not live-captured):**

| Generator | Output | Mode |
|-----------|--------|------|
| `audit_pcg_heatmap.py` | `Saved/Portfolio/Renders/pcg_heatmap.png` (1553 B, 512², 32 grid) | Radial gradient + exclusion zones (path/pond/torii) when audit lacks `point_count`; not instance positions |
| `pcg_heatmap_exporter.py` | `Saved/Portfolio/PCG/LV_SeaAbove_Prototype_pcg_heatmap.png` (5039 B) | `HighResShot 3840×2160` top-down via viewport — requires live editor, never run in CI |
| `pcg_scale_alignment.py:generate_heatmap_data()` | in-memory ISM density query | Helper never invoked against either prototype level |
| `stage_seaabove_level_loop.py` | `LV_SeaAbove_Prototype_pcg_manifest.json` (64 grid, 312.5 cm cell, extent 10000 cm) | Spec density projection from zone `base_density`, not volume capture |

> **Verdict:** Heatmap pipeline is entirely offline/spec — 0% of PCG placement is heatmap-driven at runtime.

---

## 4. PCG Volumes by Level

| Level | UMap | Total Actors | PCG Volumes | Vol % | Method |
|-------|------|-------------|-------------|-------|--------|
| **LV_SeaAbove_Prototype** | 14,587 B | 255 | **6** | **2.4%** | PCG volumes in `40_PCG/World` |
| **LV_FarawayMother_Prototype** | 6,762 B | 14* | **0** | **0.0%** | StaticMeshActor via MEL builders (no PCGVolume) |
| **L_PCG_Hero_ScaleWorldProof** | 14,058 B | — | 5 hero bindings (WP) | — | WP builder `DA_PCGHeroBuilderSettings` |

\* FarawayMother reports 14 actors for 7 placements — each `FM_*` label appears twice (live run appended without cleanup). True unique placements: **7**.

**SeaAbove — 4-graph placement (cb4ca4ec):** `SPEC_ONLY_PENDING_OWNER_EXEC` — actors `PCG_SeaAbove_SpiralAscent` (z 2000), `PenroseTiling` (unspec), `Phyllotaxis` (unspec), `MandalaBloom` (z 3000). No before/after count delta, no Z verification, no PIECapture (`pcg_seaabove_placement_evidence_spec_2026-09-01.json`).

**SeaAbove — Zone spec (`stage_seaabove_level_loop`):**

| Zone | Density | Tags | Scatter? |
|------|---------|------|----------|
| zone_1 Littoral Basin | 0.05 | WP_PrimaryRoute, WP_NoScatter, PCG_Exclude | ❌ excluded |
| zone_2 Arpeggio Bridge | 0.00 | WP_PrimaryRoute, WP_NoScatter, PCG_Exclude | ❌ excluded + zero |
| zone_3 Celestial Overlook | 0.15 | WP_LandmarkClear, PCG_Exclude, BattleArena | ❌ excluded |
| zone_4 Starskiff Waterway | 0.00 | WP_PrimaryRoute, WP_NoScatter | ❌ zero |
| **zone_5 Barrier Reef** | **0.75** | **PCG_Ground, PCG_Scatter** | **✅ only scatter zone** |

> **Only 1/5 zones (20%) enables scatter** — 60% are `PCG_Exclude`, 40% have `density 0.0`. No live ISM counts verify zone_5 actually spawns.

**SeaAbove — Navigation heatmap (Evidence 2026-09-01):**

| Route | Status |
|-------|--------|
| entry → Quill | `no connected path` |
| Quill → Starskiff | `no connected path` |
| Starskiff → MusicKey | `no connected path` |

Nearest-nav offsets: PlayerStart 3015 cm, QuillTrigger 1011 cm, Starskiff 1255 cm. Gate **HOLD/RED** — heatmap built but no single walkable surface.

---

## 5. Height-Aware Raycast — 0% Hit Rate

**Source:** `build_faraway_mother_height_aware_pcg.py` — Visibility trace `Z 50000 → -50000` per XY, fallback to `CanonicalLandscape / MeshTerrain / Landscape`.

| Metric | Value |
|--------|-------|
| Placements | 7 |
| Hits | **0** |
| Misses | **7** |
| **Hit rate** | **0.0%** |
| **Miss rate** | **100.0%** |

**Error breakdown:**

| Run | Error | Count | Detail |
|-----|-------|-------|--------|
| Live editor | `trace_failed` | 7/7 | `NativizeProperty: Cannot nativize 'int' as 'TraceChannel' (ByteProperty)` — wrong param type to `KismetSystemLibrary.LineTraceSingle`; all fall back to `ground_ref=FM_Ridge_HeadSilhouette_01 Z 45.0` |
| Offline fallback | `miss_fallback_no_landscape` | 7/7 | Empty 6762-byte level has no Landscape/MeshTerrain; synthetic `15*sin(x*0.0004)+12*cos(y*0.0005)+uniform(-4,4)` |

| Builder | Count | % | Hits |
|---------|-------|---|------|
| MEL_terrain_fabric_ridge | 2 | 28.6% | 0 |
| MEL_valley_depression | 2 | 28.6% | 0 |
| MEL_mother_head_silhouette | 1 | 14.3% | 0 |
| MEL_cascade_hair_ribbon | 1 | 14.3% | 0 |
| MEL_moon_haze_volume | 1 | 14.3% | 0 |

| Placement | XY | z_offset | Final Z | Grounded? |
|-----------|----|----------|---------|-----------|
| FM_Ridge_HeadSilhouette_01 | (0, 9000) | +45 | 45.0 | ❌ |
| FM_Ridge_Fabric_02 | (1200, 5500) | +30 | 30.0 | ❌ |
| FM_Hair_Cascade_03 | (-900, 6200) | +80 | 80.0 | ❌ |
| FM_Ridge_Fabric_04 | (-2600, 1800) | +25 | 25.0 | ❌ |
| FM_Valley_Shoulder_05 | (0, -800) | −60 | −60.0 | ❌ |
| FM_Valley_Torso_06 | (400, -4200) | −85 | −85.0 | ❌ |
| FM_Haze_Limbs_07 | (0, -7800) | +180 | 180.0 | ❌ |

> **All placements float** — Final Z = `z_offset` only, never ground-snapped. Any future landscape import invalidates all 7 positions.

---

## 6. Instance Counts per Zone

No live ISM instance counts have ever been captured for either prototype level (`check_walkability_from_instances()` never executed live).

| Level | Declared | Verified |
|-------|----------|----------|
| SeaAbove zones | densities 0.05/0.0/0.15/0.0/**0.75** (spec) | **None — zero verified counts** |
| FarawayMother | **7** StaticMeshActors (not ISM) | 7 (but 14 with duplication bug) |
| ScaleWorldProof | 450 `static_spec_count` across 25 chunks (spec) | **None — live builder never succeeded** |

**Coverage percentages:**

| Metric | % |
|--------|---|
| Heatmap drives placement | **0.0%** |
| Biome band coverage of chunks | 100.0% (all chunks assigned) |
| Scatter-enabled SeaAbove zones | **20.0%** (1/5) |
| Zero-density SeaAbove zones | 40.0% (2/5) |
| Greybox among hero meshes | **85.0%** |
| Final asset among hero meshes | **15.0%** |
| PCG volume ratio (SeaAbove) | 2.4% |
| PCG volume ratio (FarawayMother) | **0.0%** |
| Height-aware hit rate | **0.0%** |

---

## 7. Gaps (10) & Recommendations (10)

| ID | Sev | Gap | Recommendation |
|----|-----|-----|----------------|
| **GAP-01** | **P1** | **0% heatmap-driven** — no Texture2D feeds any of 145 graphs | Wire one heatmap `Texture2D` (e.g. `T_ScatterMask_SeaAbove`) into `PCG_Melodia_Universal_Scatter` DensityFilter; verify `chain_ok=true`. Source mask from Houdini `ScatterMaskBuilder`; expose `MaskThreshold` param |
| **GAP-02** | **P1** | **Raycast 0/7 hits** — TraceChannel type mismatch + empty level | Fix `LineTraceSingle` to use `ETraceTypeQuery`/`ECC_Visibility` enum (not int); import `CanonicalLandscape`/MeshTerrain ground plane before re-running `build_faraway_mother_height_aware_pcg.run_in_editor()`. Mark current JSON `OFFLINE_ONLY` |
| **GAP-03** | **P1** | **blue_void 0-4%** vs uniform 20% (dead band) | Rebalance `stable_chunk_seed` at seed 3900 (weighted bucket or hash remap) or force-assign one exemplar chunk; add unit test `each band ≥10% at r=2` |
| **GAP-04** | **P1** | **85% greybox** hero meshes (3 graphs 100% greybox) | Replace `SM_Greybox_*` with final meshes per `mesh_catalog`+`pbr_full_scan`; prioritize ArpeggioBridge/BellTreeGarden/XylophoneTrail; gate `<30%` greybox before P2 closeout |
| **GAP-05** | **P2** | **Scatter 20%** — 80% zones exclude/zero | Justify `PCG_Exclude` on corridor zones or collapse to 2 zones (playable + reef); capture per-zone ISM counts via `audit_pcg_environment` live |
| **GAP-06** | **P2** | **Universal graphs 15% ok** — 2/13 `chain_ok` | Implement nodes for FoliageDensity/RockScatter/MeadowBloom per `pcg_visual_world_plan` tier_3, or quarantine broken graphs from scatter sets; gate `chains_valid=true` |
| **GAP-07** | **P2** | **Faraway duplication** — 14 actors for 7 placements | Add cleanup: `destroy_actor` existing `FM_*` before spawn; assert `total_actors==7` post-rebuild |
| **GAP-08** | **P2** | **Live WP builder FAIL** (ret 1) vs dry-run PASS | Triage `pcg_scale_world_pcg.log`; fix `DA_PCGHeroBuilderSettings`/graph ref; re-run `WorldPartitionBuilderCommandlet` live and publish instance counts |
| **GAP-09** | **P3** | **Nav heatmap HOLD/RED** — scatter ignores walkability | Feed NavMesh projection into heatmap density (exclude unscannable); re-run `audit_wp_human_scale_heatmap` live (240 cm clearance) |
| **GAP-10** | **P3** | **Heatmap PNGs stale/synthetic** — no live capture provenance | Execute `pcg_heatmap_exporter.export_pcg_heatmap()` in-editor on both levels; store timestamped PNG+manifest under `Saved/Portfolio/PCG/`; deprecate fallback gradient |

---

## 8. Verification Commands (owner)

```bash
# BIOME_BANDS distribution
python -c "import json,collections,pathlib; d=json.loads(pathlib.Path('Saved/Audit/pcg_visual_world_plan.json').read_text()); print(collections.Counter(c['biome_band'] for c in d['chunks']))"

# Height-aware re-run (requires editor + landscape)
# in Unreal Python console:
import build_faraway_mother_height_aware_pcg as fm; fm.run_in_editor()

# PCG environment live instance counts (requires editor, level loaded)
# py Content/Python/audit_pcg_environment.py  # writes ISM counts per actor

# Heatmap live capture (requires editor)
# py Content/Python/pcg_heatmap_exporter.py
```

---

*Generated 2026-09-02 — `Saved/Audit/pcg_heatmap_2026-09-02.json` is the authoritative machine-readable companion.*
