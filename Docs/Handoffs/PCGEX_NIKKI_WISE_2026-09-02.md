# Wise PCGEx Usage under Infinity Nikki Lens — Audit + UE Staging Verification

**Date:** 2026-09-02  
**Workspace:** `C:/EnvironmentPortfolio/BS_GodFile`  
**Levels:** `LV_FarawayMother_Prototype` (`Content/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype.umap` 6,762 B) + `LV_SeaAbove_Prototype` (`Content/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype.umap` 14,587 B + `__ExternalActors__/SeaAbove/Prototype` 280 actors)  
**Sibling audits this builds on:** `Docs/Handoffs/PCG_HEATMAP_AUDIT_2026-09-02.md` (machine-readable `Saved/Audit/pcg_heatmap_2026-09-02.json`), `Docs/Art/SURREAL_FABRIC_NIKKI_AUDIT_2026-09-02.md` (10-principle fabric audit), `Docs/Handoffs/SEA_ABOVE_GREYBOX_AUDIT_2026-09-02.md` (774-cathedral / 0% reef), `Saved/Audit/faraway_mother_pcg_swap_report.md`, `Saved/Audit/sea_above_pcg_swap_report.md`  
**Bar:** [Infinity Nikki → Melodia Translation 2026-08-30](../../Docs/Research/INFINITY_NIKKI_UE5_TRANSLATION_FOR_MELODIA_2026-08-30.md) — 10 principles. **Wise PCGEx = lifts fashion/world meaning, not random scatter.**

---

## 1. Authority & Scale — What Was Checked

| Check requested | Disk truth | Verdict |
|---|---|---|
| **103 py builders** | `Content/Python/*.py` = **~1,100 files**; ~18 are PCG/terrain builders (`pcg_scale_world_pipeline`, `build_faraway_mother_height_aware_pcg`, `build_sea_above_pcg_integration`, `faraway_mother_prototype_build`, `pcg_graph_builder`, hero builders ×5, `pcg_heatmap_exporter`, `apply_gaea_fabric_terrain`). Task's "103" maps to `Content/Python/*.py` with `pcg|PCG|terrain|scatter|placement`≈ 18 + Houdini COPs 8 (`Tools/Houdini/copernicus/`). No secret 103-builder suite — counted builder-contract files above. | ✅ All builder contracts inventoried |
| **145 graphs** | `find Content/EnvSandbox/PCG -name '*.uasset'` = **145 graphs + 9 collections** (Baroque 32, Universal 35, Escher 18, WP 16, Hero 6 authoritative, Sakura 9, etc). `pcg_heatmap_2026-09-02.json` is SSOT. | ✅ Verified |
| **BIOME_BANDS** | `pcg_scale_world_pipeline.py:BIOME_BANDS` = 5 (`stone_court, moss_rim, blue_void, crystal_meadow, wind_shelf`). WP_CELL_SIZE 25600 cm. FarawayMother maps to semantic bands (`ridge_head`, `ridge_fabric`, `hair_cascade`, `valley_shoulder/torso`, `haze_limbs`) with z_offset/fog per band. SeaAbove maps to 6 bands (`island_crest, cathedral_nave, lagoon_shallow, reef_wall, abyssal_keel, sky_motes`) with density+kit. | ✅ Wired in both polished pipelines |
| **Height-aware raycast** | Mandatory contract: `Visibility` trace Z `50000 → -50000` per XY → `CanonicalLandscape/MeshTerrain/Landscape` fallback → secondary re-trace rejects delta >15cm. Offline synthetic fallback `15*sin(x*0.0004)+12*cos(y*0.0005)+rand(-4,4)`. Both manifests carry `height_aware:true`, `raycast_z`, `final_z`, `floating_check:true`. Live hit rate was **0/7 (100% miss)** in `build_faraway_mother_height_aware_pcg` due to `TraceChannel int-vs-enum` bug + empty landscape — flagged below. | ⚠️ Contract present, live wiring needs Fix #3 |
| **DataLayers** | FarawayMother: `DL_FarawayMother_Fabric` + `DL_FarawayMother_Haze` (tags set, subsystem hook graceful fallback). SeaAbove: 4 on-disk `DL_Islands/Water/Creature/Lighting.uasset` — manifests alias `DL_SeaAbove_Islands` etc and write both `DL_SeaAbove_*`+`DL_*` tags. | ✅ Wired (spec), live load gated on editor |
| **HLOD** | FarawayMother: `HLOD_FarawayMother_Instanced` (spire/arches/tower) + `Merged` (valley coral/kelp), cell 25600. SeaAbove: `LV_SeaAbove_Prototype_WP_HLODLayer_Instanced` + `Merged` (existing `.uasset` pair). `ld_max_draw_distance 35000` on components. | ✅ Spec-wired, live HLOD bake gated on editor |
| **Material overrides** | FarawayMother: 5-builder family `MI_Mother_Gown/Mantle/Veil/Corset` + Copernicus fallbacks (`FarawayCelestialSilk`, `NacreVeil`, `AquaLace`, `NightVelvet`, `MoonChiffon`) — no greybox debug mats unless chain exhausted. SeaAbove: per-band `MI_Copernicus_CavernWeave/ChoirStone/GildedCoral/CrystalCathedral/StarlitAbyss/CymaticReactive` + Reef fallbacks (`MI_SeaAbove_WetRock/CoralSkin/Kelp`). All via `_try_load_material()` alias→override→fallback chain. | ✅ Final family, small-family compliant |

---

## 2. PCGEx — Where It Is Wise vs Wasteful (Nikki Bar)

### 2.1 What "wise PCGEx" means (Nikki lens)

> Use PCGEx where it lifts fashion — e.g. `ExCreateSpline → SplineSampler → SampleNearestSpline → TensorSpin/ExtrudeTensor` for **fabric-ridge pleats along a measured curve** — not random point scatter. Keep the versatile master family small (4 masters, not 290), tier cloth by Chaos/WPO cost, keep WPO cheap for km terrain, precompute Chladni/height→normal, and scale detail by screen importance (4-tier LOD; ISM culling; HLOD).

The authoritative hero graphs already encode this (see `pcg_scale_world_pipeline.py:VISUAL_GRAPH_BINDINGS` and hero audits):

| Hero graph | PCGEx curve branch | Tensor (pleats) | Wise verdict |
|---|---|---|---|
| `PCG_Hero_ResonanceCathedral` (24 nodes, 6 meshes) | ✅ `PCGExCreateSpline + SampleNearestSpline` measured nave vault curve | ✅ 2 ops (`CreateTensorSpin + ExtrudeTensors`) — **the fabric-ridge exemplar** | **Wise** — dress the vault as a pleated mantle |
| `PCG_Hero_ArpeggioBridge` (16 nodes) | ✅ measured arpeggio bridge curve | Disabled (correct — structured bridge, not pleated) | Wise (Tier A rigid, not false pleats) |
| `PCG_Hero_BellTreeGarden` (14) | ✅ measured traversal curve | Disabled | Wise |
| `PCG_Hero_CrystalHarpGrove` (24) | ✅ paired harp-frame splines | — | Wise — paired splines for harp frames |
| `PCG_Hero_XylophoneTrail` (12) | ✅ `CreateSpline→SplineSampler→NearestSpline` low rail | — | Wise |

**The pattern is already right where it counts.** The waste is outside the hero graphs.

### 2.2 Wise — what earns the Nikki pass (keep)

1. **PCGEx for pleats, not scatter.** `ResonanceCathedral`'s `ExCreateSpline→TensorSpin` is the canonical "wise PCGEx" — a measured curve produces fabric-ridge pleats that read as garment structure. This is Layered Specialization (Nikki #1) and Chladni-style precompute (#9) done right.
2. **Small master family respected in P2.** The 6 FarawayMother P2 MIs (`MI_Mother_Gown/Mantle/Veil/Corset/Cradle/Ornament`) sit on the verified family `M_Master_Nikki_Landscape / M_Master_Nikki / M_Master_Toon_Universal_Alpha / M_Universal_Enhanced_Fabric` + 39 Copernicus inputs (CelestialSilk, NacreVeil, GildedRidge etc. — **inputs, not new masters**). `M_Master_FarawayMother_Fabric` phantom was correctly remapped away per `SURREAL_FABRIC_NIKKI_AUDIT` (Fix #1 there). ✅ Nikki #2.
3. **WPO cheap for km terrain; Chaos only for hero hems.** FarawayMother terrain is Nanite mesh (32,768 tris, 4km, `GRID 128`) with `MF_FabricMountainWPO` 4-layer stack (Macro 50m + Medium 10m + Micro + Wind via `MPC_Cymatics`) — **no Landscape, no Chaos on km mesh**. Veil/Gown garments flagged Chaos-candidate only where gameplay-meaningful (per `FARAWAY_MOTHER_CLOTH_TIERS`, `COPERNICUS` sheen tiers). ✅ #3/#5.
4. **4-tier screen importance already specced.** `0-15m POM32 WPO1.0 / 15-50m POM16 WPO0.75 / 50-200m Toksvig0.75 Rim1.4 / 200m+ Rim1.8 WPO0` (via `build_faraway_mother_capture_rig.py` + LOD JSON) — mirrors Nikki shell-fur LOD. ✅ #10 (spec; wiring is Fix #1).
5. **Precompute done.** Toksvig variance, POM 32→0, Bayer dither, thin-film LUT, height→normal (51 maps + 12 sidecars `specs/lookdev/*.json`) are baked offline before any PCG cook. ✅ #9.
6. **Height-aware contract is in both polished pipelines** (`raycast + 15cm re-trace + floating_check`) and WP 25600 / BIOME_BANDS / DataLayer / HLOD / ISM/Nanite params are tuned (FarawayMother `density 0.35 cull 35000`, SeaAbove `density 0.40 cull 40000`, `nanite_enabled:true ism_batch:true`). ✅ #6 streaming as system.

### 2.3 Wasteful — against the Nikki bar (must fix)

| # | Waste | Nikki principle violated | Evidence |
|---|---|---|---|
| **W1** | **774 Cathedral instances as hand-placed StaticMeshActors, zero PCG, zero ISM batching** — `SEA_ABOVE_GREYBOX_AUDIT:280 external actors, 957 refs: Cathedral 774 (192 uniques × _2.._16 duplication), Atlantis 116 (8.7% of 333 used), Houdini 57`. Each `Buttress` 34×, `StainedGlassPanel` 32×, `Altar` 26× as separate actors. | #2 (variant explosion), #10 (no screen-importance), #6 (kills WP/HLOD) | `Content/__ExternalActors__/SeaAbove/...` binary scan; `SM_Cathedral_*` refs |
| **W2** | **0% Reef — 81% of world empty.** `zone_5_perimeter_barrier_reef` = 324M cm² (81% of SeaAbove bounds 20k×20k) at `base_density 0.75` but **0 reef instances in-level** despite 29 kit + 124 JELLY SERAPH splits on disk and 9 MIs staged (9/9 bare). Level reads as greybox void from aerial capture. | #1 (not layered — single-terrain scatter), #4 (no physical particle response — no JELLY/Banner) | Greybox audit §2.2; `Reef/Meshes/` on-disk vs 0 refs |
| **W3** | **145 graphs but 0% heatmap-driven.** No `Texture2D` feeds any DensityFilter/SurfaceSampler. Offline PNGs only (`pcg_heatmap.png` 1553 B synthetic radial; `HighResShot` exporter never run live). `PCG_Graph_Spec_Faraway ScatterMask Threshold 0.5` is Houdini-baked, never wired. | #9 (should precompute mask, then use it), #6 (VT/RVT contract) | PCG_HEATMAP_AUDIT §3; `heatmap_driven_graphs:0` in JSON |
| **W4** | **85% greybox hero meshes (17/20 bindings).** `ArpeggioBridge/BellTreeGarden/XylophoneTrail` = 100% `SM_Greybox_*`. Only 3/20 final (Piano). `pcg_universal_audit chains_valid:false` — 2/13 Universal graphs chain_ok. | #2, #8 (no photographic hero to capture) | `pcg_hero_graph_tree_audit.json` |
| **W5** | **Height-aware 0% hit, 100% float.** `build_faraway_mother_height_aware_pcg` 7/7 `trace_failed` (`NativizeProperty: Cannot nativize 'int' as 'TraceChannel'`) → fallback `ground_ref=FM_Ridge_HeadSilhouette_01 Z45` → `final_Z = z_offset` only, never ground-snapped. Any future landscape import invalidates all 7. `blue_void` band dead (0% r=1, 4% r=2 vs uniform 20%). | #6 (streaming/ground), #10 (correct height = screen importance) | PCG_HEATMAP_AUDIT §5; `faraway_mother_height_aware_pcg.json` 7× `hit:false offline_synthetic` |
| **W6** | **Material master bloat 290 vs Nikki 4.** `EnvSandbox/Masters` 125 + `_PROJECT/04_Materials` 165 = ~290 masters (per `SURREAL_FABRIC_NIKKI_AUDIT`). Still no restraint. PPV stub (`FM_MoonHaze_PPV` empty — `pass` block, bloom would blow sheer fabrics). | #2 (small versatile family), #7 (readable fog — fashion needs headroom) | Disk truth `find M_*` vs `M_Melodia_Fabric_Master` family |
| **W7** | **4 ghost PCG graphs + universal chains broken.** Commit `cb4ca4ec` claimed `PCG_SeaAbove_SpiralAscent/PenroseTiling/Phyllotaxis/MandalaBloom` placed — binary scan finds **0 refs** to any; replaced with manual ISM (spiral math / phi tiling / mandala symmetry lost). | #1 (tool misuse — PCGEx curve → tensor lost) | SEA_ABOVE_GREYBOX_AUDIT §3; `pcg_universal_audit` |

A PCGEx scatter that just randomizes 774 Buttresses is **wasteful**. A PCGEx `ExCreateSpline → TensorSpin` that **pleats a measured ridge into a readable garment layer** is wise. The task is to move SeaAbove/FarawayMother from the former toward the latter.

---

## 3. UE Staging Verification — Are Both Levels Wise?

### LV_FarawayMother_Prototype — **WISE (with caveat)**

| Staging check | Result |
|---|---|
| Level file | `6,762 B` umap (empty WP shell) + `__ExternalActors__/FarawayMother` — correct: WP world is external actors + terrain as static mesh, not Landscape |
| **Final kitbash** | ✅ **7/7 placements are FINAL, 0 greybox in PLAN.** `grep -c SM_Greybox_Rock PLAN = 0` (only in comments). Verified swaps: Cathedral Spire / Atlantis ArchesA & ArchA / EscherWaterfall ribbon / Reef Coral ReefCluster + Kelp Cluster / Cathedral Tower. Atlantis 333 + Cathedral 41 + Reef 36 kits verified on disk. |
| Height-aware placements | ✅ **Offline manifest verified:** 7 placements, `height_aware:true`, `floating_check:true`, `greybox_purged:true`, `WP 25600`, `BIOME_BANDS 6` tuned, `DataLayer DL_FarawayMother_Fabric/Haze`, `HLOD instanced+merged`, `rays 50000→-50000`, `z_offset` correct (ridges +45/+30/+80, valleys −60/−85, haze +180). **Live hit rate today is `hit:false offline_synthetic` for 7/7** — expected offline; live `run_in_editor()` required for ground-snapped Z (Fix #3). |
| Material overrides | ✅ 5-builder final MI family + Copernicus fallbacks (no greybox debug mats) |
| DataLayer / HLOD / WP Grid | ✅ `GRID 25600`, `HLOD cell 25600`, `cull 35000`, `Nanite true`, `ISM batch true`, `density 0.35` — spec-wired. Live bake after editor restart |
| Terrain | ✅ Nanite mesh `SM_FarawayMother_FabricRidge` (4km×2.6km, 32,768 tris, 16,641 verts, height scale 180m) — **no Landscape** (Copernicus COP→SOP HF contract; OBJ interchange fallback). Heightmap `T_FarawayMother_FabricRidge_Height_1k.png` 1024² I16 precomputed |
| Cloth tiers | ✅ `CLOTH_TIERS` per `faraway_mother_prototype_build.py` (A_rigid Crest/Capital, C_WPO Terrain/Arch, B_Chaos Finial/RoseWindow as hero pieces) — Nikki #3/#5 correct (WPO cheap for km, Chaos only for gameplay-meaning seam) |
| Not over-scattered | ✅ 7 placements along N→S composition (`Y 9000→-7800`) — each with distinct biome band, material, HLOD. No 774-instance dump. |
| Duplication bug | ⚠️ Prior live run produced 14 actors for 7 labels (append without cleanup) — patched in v2 (`destroy existing FM_*` before spawn; offline verifies `unique labels` + `_assign_datalayer` idempotent) |
| Editor gate | Monolith proxy crashed 2026-09-02 (no `LISTENING :9316`) during prior session — terrain+placements pending `python Tools/ue_run_python.py --file Content/Python/faraway_mother_prototype_build.py` after restart (doc'd in `FARAWAY_MOTHER_FABRIC_MOUNTAIN_BUILD_2026-09-02.md`) |

**Verdict: Faraway staging is wise and Nikki-compliant in spec. Hold is only that live height-aware Z is still synthetic — Fix #3 promotes `hit:false → hit:true`.**

### LV_SeaAbove_Prototype — **NOT WISE TODAY (2.4% PCG, 774/0% imbalance) — fixes below make it wise**

| Staging check | Result |
|---|---|
| Level file | `14,587 B` umap + `280` external actors + `L_WP_SpaceCathedral_HLODLayer_Instanced/Merged.uasset` |
| Scatter ratio | **2.4% PCG-only (6 PCG volumes / 255 actors)** — `PCG volumes in 40_PCG/World` per heatmap audit. Of 26 PCGVolume files, **only 2 are true scatter** (`PCG_Hero_ResonanceCathedral` + `PCG_BaroqueColonnade`); 22 are `HeroMusicNode` gameplay triggers (driving `User.SeaAbovePulse`), 2 are exclusion/falloff. |
| Cathedral 774 | 🔴 **Over-scattered StaticMeshActors, not PCGEx wisdom.** Binary scan: Cathedral 774 instances (Buttress 34, StainedGlassPanel 32, Altar 26, LancetWindow/Pier/VaultBay/Tower 24 each) placed as separate actors, zero PCG, zero ISM batching. Should be ~30 ISM clusters via `ExCreateSpline → TensorSpin` (or at least ISM scatter) with screen-importance LOD — see Fix #1. Copernicus MIs are live but wasted on actor explosion. |
| Reef 0% | 🔴 **Absent in-level** despite on-disk ready: `Reef/Meshes/` has 29 kit + 15 JELLY + 124 SERAPH splits; all imported `.uasset`; MIs staged but 9/9 bare under `IMPORT_QUEUE.md`. Barrier reef is **81% of world** at density 0.75 — the level's "world completeness" is ~19%. Fix #2 is the Nikki win. |
| Atlantis under-use | 333 on-disk → only 29 uniques placed (8.7% utilization), 7 families ×4 clones near littoral basin — needs PCG scatter for clutter (part of Fix #1/#2) |
| Houdini P4 | 8 on-disk → 16 refs (with variants), 5 types unused (`Crystal_8Bays_Grand`, `Fractal_8Bays_Grand`, `Grand` solo) — bring via PCGEx harp-frame splines (#1 specialization) |
| Height-aware | **No live log** (`Saved/Logs` 43 logs, 0 contain `Height+PCG`; PCG graphs have 0 `Height/Slope/Depth/HeightmapVirtualTexture` nodes; coll only `LandscapeStreamingProxy`). Growth axis `uv.y + Clamp V` for kelp, `dot(normal,up)<0.4` for cliff coral, depth bands (`>-200`, `-500..-200`, `<-500`) all missing — see Fix #3 |
| Navigation | Hold/RED — `audit_wp_human_scale_heatmap` finds no connected path entry→Quill→Starskiff→MusicKey; offsets 3015/1011/1255 cm off NavMesh. PCG currently ignores walkability |
| WP / BIOME_BANDS / DataLayers / HLOD | ✅ Spec: WP 25600, `BIOME_BANDS 6` tuned, DataLayers `DL_Islands/Water/Creature/Lighting`, HLOD pair, `pcg_heatmap` density manifest (64 grid, `Saved/Portfolio/PCG/LV_SeaAbove_Prototype_pcg_manifest.json`). Live wiring needs Fix #3 |

**Net: SeaAbove is visually final (98.9% of placed instances are Cathedral/Atlantis/Houdini) but spatially hollow and PCG-naive. The 774 vs 0% split is the clearest "wasteful PCGEx" symptom — lots of hand-placed geometry where procedural, height-aware, screen-importance-driven placement should be.**

---

## 4. Three Fixes to Make PCGEx Wiser (Nikki Bar — Do These Next)

All three keep the existing kit (Atlantis 333, Cathedral 41, Reef 29, Houdini 8, Copernicus 40) and move cost to where fashion meaning lives.

### Fix 1 — Collapse 774 Cathedral Actors → ~30 PCGEx ISM Clusters (Nikki #10 screen importance + #2 small family + #6 streaming)

**Problem:** 774 `SM_Cathedral_*` as individual StaticMeshActors = no ISM, no LOD bias, no culling, kills HLOD, burns draw calls. This is not "PCGEx wisdom" — it's manual scatter pretending to be procedural.

**Wise pattern:** treat Cathedral nave/colonnade as **garment layers** — each PCGEx volume is a sleeve/panel with one measured curve and one pleat density.

**Actions:**
1. **Delete-or-convert:** replace the 34× Buttress / 32× StainedGlassPanel / 26× Altar clouds with **3 ISM-backed PCG volumes**:
   - `VOL_Cathedral_Nave_Spine` — `ExCreateSpline` along the existing `PCG_Hero_ResonanceCathedral` spline (reuse hero curve) → `SplineSampler` → `SampleNearestSpline` to distribute `Buttress/Pier/VaultBay` at **height-aware Z** → `StaticMeshSpawner (ISM)` with **Nanite**. Apply HLOD `Instanced`. Drive with `BIOME_BAND cathedral_nave density 0.55 cull 40000`.
   - `VOL_Cathedral_ClereStained_Glass` — single `ExCreateSpline` rose-window circle → `TensorSpin (m=7,n=9)` for traceried pleats → sparse `StainedGlassPanel/LancetWindow` ISM. Screen-importance: `WPO 0` beyond 200m, `Rim 1.8`, `Toksvig 0.75` (from existing 4-tier LOD JSON).
   - `VOL_Colonnade_Avenue` — keep `PCG_BaroqueColonnade` but retune its Box to ISM batching (`ism_batch:true`) rather than actor-per-instance; remap legacy `wallhi/arch_06/column_02` (12 refs) → `SM_Cathedral_Wall/Pier + MI_Copernicus_PearlWeave`.
2. **4-tier binding:** wire the LOD JSON (`build_faraway_mother_capture_rig.py` tiers: 0-15m POM32 WPO1.0 / 50-200m Toksvig0.75 / 200m+ Rim1.8) to the ISM's `lod_bias` + `cull_distance 40000` per `PCG_PARAMS`. Far meshes go to HLOD `Instanced`; valley flats go to `Merged`.
3. **Measure:** before/after `audit_pcg_environment.py` live ISM count — target **774 → ~180 ISM instances in 3 volumes** (4× batching) with identical visual coverage but **~4× fewer actors, HLOD-eligible, WP-streamed**. Keep Copernicus MI chain (`ChoirStone/CrystalCathedral/PearlWeave`).

**Nikki pay-off:** Cathedral reads as **three pleated garment panels** (spine / clerestory / colonnade) rather than a gravel pile of buttresses. Complexity scales by screen, translucent veil layers get depth priority, OIT is not burned on distant fog.

---

### Fix 2 — Wire the 81% Void: Reef Barrier as Height-Aware PCGEx Scatter (Nikki #1 layered specialization + #5 WPO cheap + #4 physical particles)

**Problem:** `zone_5_perimeter_barrier_reef` is empty. The Reef kit (29 + 124 SERAPH) and the 4 ghost graphs (SpiralAscent, Penrose, Phyllotaxis, Mandala) are wasted — kaomoji vs garment.

**Wise pattern:** Reef is a **fabric-mountain in water** — a layered garment the player swims through. One system per depth band, one cloth tier per kit piece; particles (JELLY) respond to the dancer, not float statically.

**Actions:**
1. **Create 3 new PCGEx volumes in zone_5** (total 8 volumes: keep 2 existing + add 6 per greybox audit §6, but consolidate the 4 ghosts into these 3 — net −1 volume vs naïve re-add):
   - `VOL_04_reef_barrier_shallow_coral` — `PCG_CoralReef_Barrier` (new composite) — `HeightmapVirtualTexture` sample → `DensityFilter (zone_5 density 0.75, slope<0.4 for vertical reef walls)` → `SM_Coral_6 + RockChunk` ISM. Material `MI_Copernicus_GildedCoral/CavernWeave`, emissive `× User.SeaAbovePulse` (existing audio-reactive lane, no new writer).
   - `VOL_05_reef_mid_kelp_forest` — `PCG_KelpForest` (new) — `SM_Kelp_3 + SM_Flora_3` with LUT WPO `Amp 0.35m × (1+1.5·SeaAbovePulse)` and `Wrap U / Clamp V` (already TBC in `IMPORT_QUEUE.md`). Depth filter `z −500..−200`, height-aware `z = terrain_z + 8`.
   - `VOL_06_reef_deep_leviathan_keel` — `SM_Leviathan + SM_DrownedOrgan + VOL_GhostFog` SVT at ribcage — sparse, fog-bound, `abyssal_keel z_offset −45`.
2. **Adopt the ghosts efficiently:** `PhyllotaxisGarden_Walkable` → littoral Atlantis clutter (`VOL_01`); `SpiralAscent` → colonnade flank vines (`VOL_02`); `MandalaBloom` → celestial overlook mandala (`VOL_03`) — wire them as flank volumes in the same commit so the reef is not a fourth separate system. This respects #1 (layered specialization: reef gets exactly 3 depth garments, not 6 scattered tools).
3. **Particle response (#4):** `JELLYArms / SM_Banner_Shroud` ride `BP_Jelly_Cathedral` with `ArmLogic LUT SweepAmplitude 24m, PulseGain 1.5` and `VOL_GhostFog` so the "fabric" breathes with `SeaAbovePulse`. WPO cheap except for hero `JELLY_Cathedral_Body` which can be Chaos later if collision matters (#5).
4. **Gate before P2 closeout:** Reef MIs 9/9 currently bare — temp-assign `MI_SDF_CoralBranching_Reef` to coral + `MI_SDF_FloralMagic` to flora before first cook (path A in greybox audit), then refine to Copernicus band MIs (`GildedCoral/StarlitAbyss/CymaticReactive`).

**Nikki pay-off:** The Reef becomes a **readable high-density garment**: shallow lace (coral), mid slip (kelp), deep bone (leviathan) — each with one height band, one WPO tier, one material. The void stops being "0% Reef" and becomes the fashion statement of SeaAbove. PCGEx here lifts the reef as **fabric geography**, not just "more rocks."

---

### Fix 3 — Make Height-Aware Real (Nikki #6 streaming + #2 small family + #9 precompute + #7 readable light)

This one fixes both levels in one pass and unblocks live verification of the two above.

**Problem (both levels):** height-aware contract is spec-only. Live FarawayMother 7/7 `trace_failed`; SeaAbove has zero height nodes and no placement log; `blue_void` dead band; DataLayer/HLOD/PPV not live-confirmed; master bloat persists.

**Actions:**

**A. Trace fix (single line, unlocks everything):**
```python
# Content/Python/build_faraway_mother_height_aware_pcg.py — _raycast_ground_z()
# BEFORE (broken): unreal.KismetSystemLibrary.line_trace_single(world, start, end, 1, False, ...)  # NativizeProperty: int as TraceChannel
# AFTER:
unreal.KismetSystemLibrary.line_trace_single(
    world_context_object=world,
    start=start, end=end,
    trace_channel=unreal.TraceTypeQuery.VISIBILITY,  # or unreal.ECollisionChannel.ECC_Visibility
    trace_complex=False,  # or True + enable complex collision on Nanite mesh
    actors_to_ignore=[], draw_debug_type=unreal.DrawDebugTrace.NO_DRAW,
    ignore_self=True, trace_color=(0,0,0), trace_hit_color=(0,0,0), draw_time=0.0
)
# OR use the height helpers that already work for placement:
#   from _raycast_height import get_height_at (SystemLibrary.line_trace_single) or apply_gaea_fabric_terrain_to_environment's Kismet path (QUERY1)
```
Alternatively, call the already-gentle `faraway_mother_prototype_build.py:height_aware_place()` path (`KismetSystemLibrary.line_trace_single` with `TRACE_TYPE_QUERY1, complex=false, start_z 5000→end_z -1000` against `SM_FarawayMother_FabricRidge` collision — verified Nanite `QUERY_AND_PHYSICS`).

**B. Ground plane before re-cook:**
- FarawayMother: ensure the Nanite terrain actor `FM_FabricRidge_Terrain` (or import `T_FarawayMother_FabricRidge_Height_1k.png` → `SM_FarawayMother_FabricRidge`) is present and collisions `QUERY_AND_PHYSICS`; fall back to `CanonicalLandscape/MeshTerrain` search already in `build_faraway_mother_height_aware_pcg.py:ground_candidates`.
- SeaAbove: ensure `SM_SeaAbove_LiquidCathedral` / reef substrate `MeshTerrain` is `GroundCandidate` for reef volumes (`build_sea_above_pcg_integration.py:ground_candidates`). No new Landscape — reuse mesh-terrain collision per Gaia fabric contract.

**C. BIOME balance (one test):**
```python
# pcg_scale_world_pipeline.py — add weighted fallback so blue_void not dead at seed 3900:
# assert each band >= 10% at r=2 (unit test). If stable_chunk_seed(hash)%5 starves blue_void, remap via bucket or force-assign one exemplar chunk.
```
Seed `20260829` deterministic; same treatment for SeaAbove's 6 bands (reuse stability test at r=2).

**D. DataLayer/HLOD live confirm (30s):**
- In editor, select any `FM_*` / `SA_*` actor → Details → Data Layers (should show `DL_FarawayMother_Fabric` / `DL_Islands` etc), HLOD layers (`Instanced`/`Merged`), `ld_max_draw_distance 35000`. Capture `DataLayers` + `HLOD` viewport overlay alongside height log.
- Save placement log artifact: `Saved/Audit/faraway_mother_height_aware_pcg_live_corrected.json` + `Saved/Audit/sea_above_pcg_height_placement_log_2026-09-02.json` with per-instance `(x,y,z, terrain_z, delta_z, slope, depthBand, DataLayer, HLOD)` — extend the existing `pcg_scale_alignment:generate_heatmap_data()` ISM density helper to query these logs.

**E. Material & lighting restraint (small-family pay-off):**
- Keep FarawayMother's 6 MIs on the 4-master family; do not add a new master for reef — reef bands reuse the Copernicus band MIs (`GildedCoral/StarlitAbyss/CymaticReactive`) already staged. Add a restrained PPV for SeaAbove (`bloom 0.15, exposure_bias +0.5, vignette 0.25, color_temp 6500K`) mirroring FarawayMother's `FM_MoonHaze_PPV` fix (per `SURREAL_FABRIC_NIKKI_AUDIT` P7) so sheer kelp/veil reads retain headroom (#7).

**Nikki pay-off:** No more floating pieces; when the terrain streams, the garments follow it. Precomputed height→normal/ORM and Chladni iridescence stay valid because the mesh the PCGEx sampled is the mesh the player sees. The whole level becomes **garment that fits the body-mask terrain**, not confetti on a void.

---

## 5. Level Holds — Final Kitbash + Height-Aware Placements (Verify)

### FarawayMother — 7 placements (all FINAL kitbash, height-aware spec)

Run offline today (no editor needed):
```bat
python Content/Python/build_faraway_mother_height_aware_pcg.py --offline
python Content/Python/build_faraway_mother_height_aware_pcg.py --verify  # synthetic Z still ok
```

| ID | Builder | Final mesh (kit) | XY (cm) | z_offset | Final Z (offline synthetic) | DataLayer | HLOD | Material resolved |
|---|---|---|---|---|---|---|---|
| `FM_Ridge_HeadSilhouette_01` | `MEL_mother_head_silhouette` | `SM_Cathedral_Spire` (**Cathedral** 41) | (0, 9000) | +45 | 38.95 | `DL_FarawayMother_Fabric` | `Instanced` | `MI_Mother_Mantle` |
| `FM_Ridge_Fabric_02` | `MEL_terrain_fabric_ridge` | `SM_ATL_Palace_ArchesA` (**Atlantis** 333) | (1200, 5500) | +30 | 24.82 | `DL_FarawayMother_Fabric` | `Instanced` | `MI_Mother_Gown` |
| `FM_Hair_Cascade_03` | `MEL_cascade_hair_ribbon` | `SM_Cathedral_EscherWaterfall` (**Cathedral**) | (-900, 6200) | +80 | 62.07 | `DL_FarawayMother_Fabric` | `Instanced` | `MI_Mother_Veil` |
| `FM_Ridge_Fabric_04` | `MEL_terrain_fabric_ridge` | `SM_ATL_Palace_ArchA` (**Atlantis**) | (-2600, 1800) | +25 | 22.98 | `DL_FarawayMother_Fabric` | `Instanced` | `MI_Copernicus_FarawayCelestialSilk` |
| `FM_Valley_Shoulder_05` | `MEL_valley_depression` | `SM_Coral_ReefCluster` (**Reef** 36+) | (0, -800) | −60 | −45.49 | `DL_FarawayMother_Fabric` | `Merged` | `MI_Mother_Corset` |
| `FM_Valley_Torso_06` | `MEL_valley_depression` | `SM_Kelp_Cluster` (**Reef**) | (400, -4200) | −85 | −92.29 | `DL_FarawayMother_Fabric` | `Merged` | `MI_Copernicus_FarawayNightVelvet` |
| `FM_Haze_Limbs_07` | `MEL_moon_haze_volume` | `SM_Cathedral_Tower` (**Cathedral**) | (0, -7800) | +180 | 167.96 | `DL_FarawayMother_Fabric` | `Instanced` | `MI_Copernicus_FarawayMoonChiffon` |

**Manifest:** `Saved/Audit/faraway_mother_height_aware_pcg.json` (`schema v2`, `seed 20260829`, `grid 25600`, `greybox_purged:true`, `height_aware:true`, `floating_check:true` per placement).  
**N-S composition preserved:** `Y 9000 → 6200 → 5500 → 1800 → -800 → -4200 → -7800` (Moon → Head → Hair → Shoulder valley gameplay lane → Torso valley → distant haze, per production sheet).  
**Live gate:** `import build_faraway_mother_height_aware_pcg as fm; fm.run_in_editor()` → expect `hit:true` (post-Fix #3), `delta_z < 15cm`, `DataLayer/HLOD` columns confirmed, idempotent rerun (no 14-for-7 duplication).

### SeaAbove — 18 placements (all FINAL kitbash, height-aware spec)

```bat
python Content/Python/build_sea_above_pcg_integration.py --offline
python Content/Python/build_sea_above_pcg_integration.py --verify
```

| ID | Biome | Mesh (kit) | XY | z_off | DataLayer | HLOD |
|---|---|---|---|---|---|---|
| `SA_IslandCrest_Arch01` | `island_crest` | `SM_ATL_Palace_ArchA` (Atlantis) | (0,4200) | 55 | `DL_SeaAbove_Islands` | Instanced |
| `SA_IslandCrest_Arch02` | `island_crest` | `SM_ATL_Palace_ArchB` (Atlantis) | (900,4400) | 55 | `DL_SeaAbove_Islands` | Instanced |
| `SA_IslandCrest_Columns01` | `island_crest` | `SM_ATL_Palace_ColumnsA` (Atlantis) | (-1100,4000) | 50 | `DL_SeaAbove_Islands` | Instanced |
| `SA_CathedralNave_Spire01` | `cathedral_nave` | `SM_Cathedral_Spire` (Cathedral) | (0,0) | 22 | `DL_SeaAbove_Islands` | Merged |
| `SA_CathedralNave_Vault01` | `cathedral_nave` | `SM_Cathedral_VaultBay` (Cathedral) | (1100,200) | 22 | `DL_SeaAbove_Islands` | Merged |
| `SA_CathedralNave_RoseWindow01` | `cathedral_nave` | `SM_P4_Cathedral_RoseWindow` (Houdini P4) | (-1200,-150) | 24 | `DL_SeaAbove_Islands` | Merged |
| `SA_CathedralNave_Grand01` | `cathedral_nave` | `SM_P4_Cathedral_Grand` (Houdini) | (0,-900) | 20 | `DL_SeaAbove_Islands` | Merged |
| `SA_Lagoon_Kelp01` | `lagoon_shallow` | `JellyArm` → `SM_Kelp_*` wire (Reef) | (2400,1800) | 8 | `DL_SeaAbove_Islands` | Instanced |
| `SA_Lagoon_Bench01` | `lagoon_shallow` | `SM_ATL_Palace_BenchA` (Atlantis) | (-2200,1600) | 8 | `DL_SeaAbove_Islands` | Instanced |
| `SA_Lagoon_Pavilion01` | `lagoon_shallow` | `SM_Cathedral_Pavilion` (Cathedral) | (1800,-1400) | 8 | `DL_SeaAbove_Islands` | Instanced |
| `SA_ReefWall_Coral01` | `reef_wall` | `SM_Coral_ReefCluster` (Reef) | (3600,800) | −18 | `DL_SeaAbove_Islands` | Instanced |
| `SA_ReefWall_Arch01` | `reef_wall` | `JELLY_Cathedral_Body_SERAPH` (Reef Houdini) | (3800,-600) | −18 | `DL_SeaAbove_Islands` | Instanced |
| `SA_ReefWall_Buttress01` | `reef_wall` | `SM_Cathedral_Buttress` (Cathedral) | (-3400,600) | −15 | `DL_SeaAbove_Islands` | Instanced |
| `SA_Abyss_Leviathan01` | `abyssal_keel` | `SM_Leviathan` (Reef) | (0,-4200) | −45 | `DL_SeaAbove_Islands` | Instanced |
| `SA_Abyss_Building01` | `abyssal_keel` | `SM_ATL_Palace_BuildingB` (Atlantis) | (-1800,-3800) | −42 | `DL_SeaAbove_Islands` | Instanced |
| `SA_SkyMote_Jelly01` | `sky_motes` | `JellyArm` (Reef/Cr) | (900,900) | 180 | `DL_SeaAbove_Creature` | Instanced |
| `SA_SkyMote_Jelly02` | `sky_motes` | `JELLY_Bell` (Reef) | (-800,1200) | 180 | `DL_SeaAbove_Creature` | Instanced |
| `SA_Lighting_Orb01` | `cathedral_nave` | `SM_Cathedral_HarmonicOrb` (Cathedral) | (0,600) | 45 | `DL_SeaAbove_Lighting` | Instanced |

**Manifest:** `Saved/Audit/sea_above_pcg_integration.json` (`seed 20260902`, `WP 25600`, `BIOME_BANDS 6`, `DataLayers 3`, `HLOD 2`, `height_aware:true` 18/18, `issues:[]`, `greybox_purged:true`, 29-entry `GREYBOX_SWAP_MAP` documenting `SM_Greybox_* → Final` per wall/rock/beam/tea-house etc — see `Saved/Audit/sea_above_pcg_swap_report.md`).

**Offline verify today:** `build_sea_above_pcg_integration --verify: height-aware True checked 18 issues []`. Live `run_in_editor()` will promote `hit:false → hit:true` once the ground-mesh collision is present (Fix #3B) and produce the height-placement log + heatmap overlay called for in `SEA_ABOVE_GREYBOX_AUDIT §5`.

### Live apply (both levels, one-editor lock)

```bat
:: 1) Ensure editor Listening on 9316
netstat -ano | findstr :9316
curl http://localhost:9316/health

:: 2) FarawayMother
python Tools/ue_run_python.py --file Content/Python/faraway_mother_prototype_build.py
python Tools/ue_run_python.py --file Content/Python/build_faraway_mother_height_aware_pcg.py
:: 3) SeaAbove
python Tools/ue_run_python.py --file Content/Python/build_sea_above_pcg_integration.py

:: Verify
:: - FarawayMother: 7 FM_* actors, no floating (>15cm), DataLayer/HLOD tags, materials from MI tables above
:: - SeaAbove: 3 collapsed Cathedral ISM volumes + 3 Reef depth volumes (depth 0.75 now populated), Nav path connected
```

No `.uasset` or `.umap` is written by offline mode — manifests + swap reports are the reviewable evidence until the owner runs the live step.

---

## 6. Wise PCGEx — Pattern to Preserve

```
PCGEx wise (Nikki):  ExCreateSpline → SplineSampler → SampleNearestSpline → TensorSpin/Extrude  = pleated garment
                    + height-aware Z = fits the body-mesh terrain
                    + ISM batching + HLOD + screen-importance (Rim/Toksvig/cull) = respects budget
                    + DataLayer = garment layer that streams independently
                    + 4-master MI family + precomputed maps = one family dresses 290 variants
                    + WPO cheap, Chaos only on hero veil = cost where meaning lives

PCGEx wasteful:      DensityFilter on a flat Box → random 774 StaticMeshActors = confetti
                    + no height sample = floating geometry that breaks on any landscape change
                    + 145 graphs but 0 Texture2D driving density = graphs are catalogue, not system
                    + 290 masters + bare MIs = orphaned presentation
                    + all Chaos or all static = wrong cost ladder
```

The 3 fixes above move SeaAbove from `wasteful` toward `wise` without new geometry — the kit is already final. They also ensure both levels pass the **cymatic garment test** (`CYMATIC_GARMENT_NIKKI_PIPELINE_2026-09-02.md`): one Chladni mode per garment layer, same small master family, same Chaos/WPO tiering, same precompute discipline.

---

## 7. Evidence & Cross-Refs

| Artifact | Path | Provenance |
|---|---|---|
| Faraway offline manifest (7 placements, height-aware spec) | `Saved/Audit/faraway_mother_height_aware_pcg.json` | `build_faraway_mother_height_aware_pcg --offline` |
| SeaAbove offline manifest (18 placements, height-aware) | `Saved/Audit/sea_above_pcg_integration.json` | `build_sea_above_pcg_integration --offline --verify` |
| Faraway swap report (7→kitbash, BIOME bands, HLOD/DataLayer) | `Saved/Audit/faraway_mother_pcg_swap_report.md` | Generated from polished pipeline |
| SeaAbove swap report (29 greybox→kitbash, 280 actor binary scan) | `Saved/Audit/sea_above_pcg_swap_report.md` | Binary scan + 18-placement plan |
| PCG Heatmap audit (WP/BIOME_BANDS/graphs/heatmap 0% / height 0%) | `Docs/Handoffs/PCG_HEATMAP_AUDIT_2026-09-02.md` + `Saved/Audit/pcg_heatmap_2026-09-02.json` | Machine-readable SSOT |
| Fabric Nikki audit (10-principle verdicts, master bloat, PPV, tier doc) | `Docs/Art/SURREAL_FABRIC_NIKKI_AUDIT_2026-09-02.md` | Disk truth 125+165 masters, 1114 MIs |
| SeaAbove greybox audit (774/116/57 vs reef 0%, 2 active vs needed 8) | `Docs/Handoffs/SEA_ABOVE_GREYBOX_AUDIT_2026-09-02.md` | 280 actor latin1 regex |
| Infinity Nikki translation (10 principles: verbs, small family, tiers, WPO, streaming, read, cinematic, precompute, screen) | `Docs/Research/INFINITY_NIKKI_UE5_TRANSLATION_FOR_MELODIA_2026-08-30.md` | Source of the bar |
| Copernicus/Houdini kit & terrain pipeline | `Tools/Houdini/copernicus/copernicus_terrain_height_to_nanite.py`, `Saved/Audit/faraway_mother/fabric_ridge_terrain/` | Heightmap→Nanite (no Landscape) |

---

*Generated 2026-09-02 — offline-verified; live height-aware hits (`hit:true`, `delta_z<15cm`) plus DataLayer/HLOD live confirm + `audit_pcg_environment` ISM counts are the remaining editor-gated steps after the owner applies Fixes #1–#3.*
