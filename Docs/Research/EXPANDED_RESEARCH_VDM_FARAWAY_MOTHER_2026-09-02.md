# Expanded Research — VDMs + Unexpanded Systems for P2 Faraway Mother Houdini

**Date:** 2026-09-02  
**Scope:** Vector Displacement Maps (VDMs) for fabric mountains + 6 unexpanded systems from `EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md`  
**Status:** Research report — no production mutations; baking required before shipping

---

## 1. VDMs — What They Are and Why Heightmaps Cannot Do Fabric Folds

**Heightmap (scalar displacement):** one channel (R), displaces along the base mesh **normal** only. Can raise/lower but never create overhangs, undercuts, arching pleats, or fabric that folds *over itself*. All Faraway Mother ridges built from heightmaps will read as eroded rock, not draped cloth.

**Vector Displacement Map (VDM):** RGB stores a full 3D offset vector (X,Y,Z) per texel — typically in tangent, object, or world space. The displaced surface can arch laterally, curl under, create true pleat overhangs and fabric gathers. For Faraway Mother this is the difference between "bumpy ground" and "kilometer-scale woven sheet under tension."

**Details:**
- VDM encoding: `[-1,1]` float vectors mapped to `[0,1]` RGB for storage. Requires 16-bit or 32-bit float textures (EXR / `PF_FloatRGBA` / `BC6H`) to avoid banding — 8-bit PNG is insufficient (see §3).
- Tangent-space VDM deforms correctly when the base mesh moves/deforms; world/object-space VDM "swims" — use tangent for characters/animated cloth, object-space is fine for static Nanite terrain.
- Project prior finding (confirmed still true): *"No VDM support in project. Use high-poly + WPO + POM instead"* — `Docs/Plans/P2_FABRIC_MOUNTAIN_PLAN_2026-08-31.md:23,170`, `Docs/Plans/P2_AUDIO_REACTIVE_FABRIC_MOUNTAINS_2026-08-31.md:186,291`, `Docs/Research/DEEP_RESEARCH_REPORT_2026-08-31.md:191-194`.

**Faraway Mother integration:** Use VDMs for hero fabric ridges (`SM_FabricRidge_Hero`) where pleats must overhang; use heightmap + WPO for broad landscape where lateral displacement is unnecessary. Hybrid is cheaper than VDM-everywhere.

---

## 2. Houdini SOP VDM Baker — Labs Maps Baker (Current Authoritative Path)

**What it does:** Bakes high-to-low mesh difference as vector displacement (and height, normal, curvature, AO, thickness) into textures. Replaces the old `GameDev Simple Baker` / `ROP Maps Baker`.

**Where it lives in Houdini 22.0.368:**
- **SOP network:** `Labs Maps Baker` (SideFX Labs, SOP context) — drop high-res + low-res inputs, choose output maps. Video + docs: Houdini 21 Maps Baker in COPs — https://www.youtube.com/watch?v=oZdJrI6dDhM (Houdini 21 COPs port), SideFX normal/displacement docs https://www.sidefx.com/docs/houdini/shade/normalmaps.html (vector vs. scalar displacement distinction).
- Forum confirmation of workflow: baking displacement/low-to-high plane tests, `Simple Baker` vs `Labs Maps Baker` discussion — https://www.sidefx.com/forum/post/445799/ ; Reddit summary "use Labs Maps Baker, not Simple Baker" — https://www.reddit.com/r/Houdini/comments/l8x9gq/bake_displacement_map/ ; Polycount VDM bake question — https://polycount.com/discussion/197078/where-do-i-bake-a-vector-displacement-map (Mudbox/ZBrush fallback if Houdini path stalls).
- **Editability requirement for HDA/Engine use:** Like Simple Baker, Maps Baker's internal ROPnet must be marked editable in the HDA Type Properties → Editable Nodes (ROP FBX + subnet + baker SOP) — https://www.sidefx.com/forum/topic/60265 (SideFX staff `dpernuit` note; same requirement applies to Labs Maps Baker).

**In-repo usage pattern today:** SOP attributes (`thickness`, `curvature`, AO via `dress_ao_vex.py` — 64 rays) are baked via `Tools/Houdini/sea_above_reef/bake_rasterize_ao.py` (numpy+PIL barycentric rasterizer). The Copernicus migration (`Tools/Houdini/copernicus/README.md`) replaces this with `SOP Import COP → Labs Maps Baker COP → Attribute Interpolate COP → Curvature directional COP → Denoise (OpenImageDenoise COP) → File Output COP`.

**Faraway Mother integration:**
- Build `HDA_ENV_FabricMountain_VDMBake`: Inputs = high-res Vellum-draped fabric (from `FARAWAY_MOTHER_DRAPE_SPEC_2026-09-01.md` Vellum SOP chain) + low-res proxy plane/mesh. Output = `T_FarawayMother_FabricRidge_VDM.exr` (32-bit, tangent-space) + companion height/normal/curvature.
- Mark Labs Maps Baker + internal `ropnet` + `rop_fbx` as Editable Nodes so the HDA cooks under Houdini Engine / Session Sync without manual export.
- Bake at 2K–4K for hero ridges (pleat frequency 0.02, sharpness p=4, depth 40m per drape spec); downsample to BC6H in UE via `verify_tex_contract.py` pattern.
- Keep `SEED=20260828` discipline from `Tools/Houdini/copernicus/README.md` — changing bake seed requires new manifest + QA renders.

---

## 3. Houdini COPs VDM — Copernicus (GPU Compositor, Houdini 20.5+/22.0)

**What it does:** Copernicus (Houdini 20.5's COP rewrite) is the GPU image-processing/compositing context that replaces old COPs. For VDMs it provides the *baking + compositing* side: geometry-aware procedural image generation from shared SOP fields — same procedural rule feeds both geometry and textures.

**Why it matters over PIL rasterizer:**
- COP tiles + viewport feedback, GPU-accelerated vs. O(n²) numpy loop.
- `OpenImageDenoise COP` (2s denoise) fixes 64-ray AO speckle without raising ray count.
- `Attribute Interpolate COP` with explicit `background_value=1.0` vs. PIL hard-coded 1.0.
- Height→Normal (`Gradient COP` Displacement→Normal) and curvature LUT in same graph, WYSIWYG.
- `COP Cache COP` — deterministic re-cook on Seed change only (per `Tools/Houdini/copernicus/README.md` comparison table).

**Files in repo (present, verified):**
- `Tools/Houdini/copernicus/copernicus_dress_bake.py` — generates `.hip` COP network (`hython ... --seed 20260828 --size 1024`).
- `Tools/Houdini/copernicus/copernicus_fabric_sheen.py` — velvet/silk sheen mask COP for `T_FarawayMother_Gown/Mantle`.
- `Tools/Houdini/copernicus/copernicus_cymatic_parallax.py` — surreal singing/twinkling/dancing 9-map PBR families (CymaticMarble, GildedLoom, SilkWaterfall, etc.) — pure numpy pipeline, 21 variants × 1665 PNGs already baked to `Saved/Audit/copernicus_cymatic/` (audit `Saved/Audit/cymatics_audit_2026-09-01.json`).
- `Tools/Houdini/copernicus/hda_variants/` — 6 Faraway Mother HDAs: `faraway_p2_corset/ cradle/ gown/ mantle/ ornament/ veil` (`.hip` + COP variants).
- Template: `Tools/Houdini/copernicus/melodia_dress_cop.hip.template.md` + `hda_melodia_lookdev_spec.json` (parms: Seed/Resolution/BakeSet/Denoise/ThicknessBias).

**Faraway Mother integration:**
- Extend existing COP network for VDM: `SOP Import COP (high + low)` → `Labs Maps Baker COP (vector displacement)` → `Attribute Interpolate COP` → `Height→Normal Gradient COP` → `Curvature COP` → `Denoise COP` → `File Output COP (BC6H EXR + BC5 Normal + BC4 Roughness)` with seed-locked manifest.
- Use `copernicus_fabric_sheen.py` sheen masks as VDM amplitude modulators — stretched zones (tension T>0.6) get sheen-suppressed VDM (taut fabric), slack zones get full pleat depth.
- Next step after COP proof: wrap as `hda_melodia_lookdev.hda` (async cook via Houdini Engine FREE, per COP README architecture diagram) so UE can re-cook on Seed change without leaving editor.

---

## 4. UE 5.8 VDM Displacement — WPO vs. Nanite Tessellation/Static Displacement (What Actually Ships)

**Current UE 5.8 reality (Epic docs + forums):**
- **Nanite has two displacement paths** — `dev.epicgames.com/documentation/unreal-engine/nanite-virtualized-geometry-in-unreal-engine`:
  - *Static Displacement Mapping* — Static Mesh Editor offline adaptive tessellator bakes displacement maps into an optimized Nanite mesh (texture-driven, non-destructive, scalar parameter control). No runtime cost.
  - *Nanite Tessellation* — dynamic programmable displacement at runtime via material `Displacement` input (height along normal) or procedural logic. Supports animated displacement; mesh is diced on GPU. **Explicitly experimental in 5.6–5.8.**
- **Vector displacement is NOT fully supported in Nanite tessellation yet.** Epic forum thread `Nanite Tessellation usage recommendation` (2025) — https://forums.unrealengine.com/t/nanite-tessellation-usage-recommendation/2663223 — Epic staff notes *"some of the issues we still need to fix (cracks on UV seams, vector displacement, etc.) could make that effort even more challenging."* Treat VDM-via-tessellation as **R&D WATCH**, not shipping dependency.
- **WPO (World Position Offset) works with Nanite but is limited** — same doc: *"Nanite meshes using WPO displacement are split into smaller clusters whereby each of those clusters have their own individual bounds and are culled individually on the GPU. You must clamp the amount of displacement ... to manage how many clusters are culled."* Forum reports: UV precision issues, shadow-cache invalidation, 3× WPO cost on Nanite, disappearing triangles if displacement is large — disable Nanite for heavy-WPO meshes or clamp aggressively.
- **DBuffer/decals cannot affect Nanite tessellated displacement** (depth-buffer projection limitation) — workaround is RVT displacement sampling — https://forums.unrealengine.com/t/nanite-displacement-tessellation-vs-dbuffer/2598139.
- **Landscape + VDM** remains heightmap-native; mesh terrain / Voxel Plugin 2 / UE Mesh Terrain are R&D alternatives for overhangs (see `EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH` §Mesh Terrain, recommendation: isolated R&D map only).

**Project policy (existing):** Heightmap + WPO + POM + high-poly meshes (from `DEEP_RESEARCH_REPORT` §6 and both P2 plans). VDM plan docs explicitly chose *"no VDM support — use high-poly + WPO"* — `P2_FABRIC_MOUNTAIN_PLAN` §Phase 5 and `P2_AUDIO_REACTIVE_FABRIC_MOUNTAINS` §2.5.

**Faraway Mother integration (hybrid — safe to ship):**
- **Broad landscape (`LM_FarawayMother_Terrain`, 8 km × 8 km):** Keep heightmap + `MF_FabricMountainWPO` 4-layer stack (Macro 1km/50m BassIntensity, Medium 100m/15m MidIntensity, Micro 1m/1m BeatPulse, Wind). No VDM needed — no overhangs.
- **Hero pleat meshes (`SM_FabricRidge_Hero`):** Bake VDM in Houdini (EXR, object-space for static Nanite) → import as **Static Displacement** Nanite mesh (offline tessellator) for shipping. This avoids experimental runtime VDM tessellation while still delivering true overhangs. Clamp WPO on these meshes or disable Nanite WPO and use static displacement instead.
- **Dynamic audio response on hero VDM meshes:** Do NOT animate VDM texture at runtime; instead modulate `MF_FabricMountainWPO` scalar params via `MPC_Melodia_Palette` (BeatPulse/BassIntensity/RhythmPulse) — proven path from `DEEP_RESEARCH_REPORT` §2 + `P2_AUDIO_REACTIVE_FABRIC_MOUNTAINS` §2.1 signal flow. VDM provides shape, WPO provides motion.
- **Guardrails:** `r.Nanite.DicingRate 3–4` for tessellated assets if tested; `Displacement Fade` in material to limit tessellation at distance; never use Nanite tessellated VDMs for gameplay collision — collision stays on low-res proxy.

---

## 5. Magpie — Simulation ↔ Visual Seam (Unexpanded WATCH, Scaffolded Read-Only)

**What it does:** Concept — *"conventional engine retains gameplay/simulation state while a generative renderer produces visual frames."* Separation of **simulation truth** (HP, quest flags, rhythm grade, positions) from **visual truth** (what frames show). Reference: `Docs/Research/EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH_2026-08-30.md` §Magpie + `Docs/Research/MAGPIE_SEAM_ARCHITECTURE_2026-08-31.md`.

**Status in repo:** WATCH/RESEARCH only — no renderer, no vendor, NOT a production dependency (determinism/latency/temporal stability/QA/platform). Promoted 2026-08-31 to **architecture scaffold** (read-only seam, not renderer) per `Docs/Research/DASH_MAGPIE_NATIVE_INTEGRATION_2026-08-31.md` + master index §3.

**File paths:**
- Spec: `Docs/Research/MAGPIE_SEAM_ARCHITECTURE_2026-08-31.md`
- Integration plan: `Docs/Research/DASH_MAGPIE_NATIVE_INTEGRATION_2026-08-31.md` (§2 Magpie → seam)
- Code (scaffold, needs closed-editor build): `Source/BS_GodFile/MelodiaIntegration/MelodiaVisualRepresentationSubsystem.h/.cpp` — read-only accessors `GetCurrentRhythmGradeKey()`, `GetBeatPhaseNormalized()`, `IsBattleActive()`, `GetActiveNarrativeVisualFlags()`, `IsReadOnlyByContract()==true`
- Probe: `Tools/test_visual_seam.py` → `Saved/Audit/visual_seam_probe_*.json`
- `Docs/Research/EMERGING_TOOLCHAIN_IMPLEMENTABLE_ROWS_2026-08-31.md` §2.3 (context)

**Faraway Mother integration:**
- Fabric mountains are the perfect Magpie test domain — simulation truth (mountain collision, Heart Gate challenge state `challenge.mother_heart_gate`, World Field Bus `Tension`/`Resonance`) stays authoritative; visual truth (Cymatic WPO amplitude, sheen shimmer, glitter pulse) is the presentational read layer.
- Wire `UMelodiaVisualRepresentationSubsystem` reads into a future **cymatic-driven lookdev overlay** — e.g., Faraway Mother silhouette color grades shift with `GetBeatPhaseNormalized()` without mutating simulation. This matches the audio-reactive presentation subsystem's MPC pattern.
- Do NOT build a Magpie frame generator; extend the seam accessor set with `GetWorldFieldTension(U,V)` / `GetCymaticAmplitude(U,V)` as additional read-only fields for PCG/Blueprint consumers.

---

## 6. Neural Shaders / Neural Materials — WATCH (Needs a Material ONNX, Present ONNX Is Embedding-Only)

**What it does:** Future where expensive material behavior (iridescent layered water-glass hair, complex pearl/fabric BRDFs, large wardrobe texture libraries) is approximated by compact neural networks — texture-memory reduction + shader-cost reduction. RTX Kit umbrella includes neural shaders/compression/materials/mega-geometry.

**Status in repo:** WATCH — tracked in `EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH` §Neural shaders (p.392), trench sweep §14, spike plan Test 14. `EMERGING_TOOLCHAIN_MASTER_INDEX` §3: *"needs a material onnx (present onnx is embedding-only)"*. `EMERGING_TOOLCHAIN_IMPLEMENTABLE_ROWS` §1 corrects earlier misclassification: `Plugins/Claireon/Resources/Models/bge-small-en-v1.5-int8/model.onnx` (34 MB, text-embedding for Claireon retrieval) **does exist**, but is NOT a material-shading network. NNERuntimeORT is PRESENT in `.uproject` (enables inference) per master index §1.

**File paths:**
- Present onnx: `Plugins/Claireon/Resources/Models/bge-small-en-v1.5-int8/model.onnx`
- Runtime: `NNERuntimeORT` in `BS_GodFile.uproject`
- Research: `EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH` §Neural shaders, `EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_03_2026-08-30.md` §14 (RTX Kit)
- Implementable rows: `EMERGING_TOOLCHAIN_IMPLEMENTABLE_ROWS_2026-08-31.md` §1, §3 (not attempted — needs trained model)

**Faraway Mother integration:**
- Near-term (no new ONNX): Use neural-material *interface* only — scaffold `MF_NeuralFabricApproximation` that can swap between analytic (`MelNikkiPearlSheen` dual-layer iridescence) and a neural texture sample, same inputs/outputs. This preserves the call site for later.
- Valuable spike if a material ONNX becomes available: train/compress Faraway Mother's 11 Copernicus PBR families (GildedLoom, SilkWaterfall, CherryBlossomWood, DancingCrystals, FinalDreamweaver, etc. in `Saved/Audit/copernicus_cymatic/`) via neural texture compression — measure VRAM reduction across 4 biomes × 8K textures.
- Do NOT plan shipping features around this; track Epic/RTX Kit 5.8 compatibility and platform lock-in per spike plan Test 13/14 notes.

---

## 7. Water / Oceanology — PRESENT Runtime Water Authority (Not an External Bake)

**What it does:** `Oceanology_Plugin` (`Plugins/Oceanology_Plugin/`) is the project's runtime water authority — FFT + Gerstner waves, C++ performance, QuadTree LOD, flow-based foam, crest splashes (Niagara), underwater volumetrics (scattering/caustics/god rays), RVT landscape shoreline blending, pontoon buoyancy, infinite ocean / lake / river volumes. NextGen docs: `galidar.com/oceanology-nextgen/setup` (DX12 + SM6, mesh distance fields, Lumen + VSM integration).

**Status in repo:** PRESENT — listed in `Plugins/` dir (verified `ls Plugins/` output). Integrated via `UMelodiaAudioReactivePresentationSubsystem` ocean beat drive: `Source/BS_GodFile/MelodiaIntegration/MelodiaAudioReactivePresentationSubsystem.cpp` — *"Oceanology surface drive"* section — does **not** include Oceanology headers; matches actor class by name token `TEXT("Oceanology")`, projects MPC BeatPulse/BassIntensity onto `M_Oceanology_Inst` scalar params (baselines preserved, deltas lift on beat). This respects that `M_Oceanology` is plugin-owned and must not be edited.

**File paths:**
- Plugin: `Plugins/Oceanology_Plugin/`
- Presentation bridge: `Source/BS_GodFile/MelodiaIntegration/MelodiaAudioReactivePresentationSubsystem.cpp` (Oceanology presentation drive + reflected parameter drive)
- Level usage: `L_SeaAbove_Prototype` (Sea Above is the "Water is Anatomy" vertical slice preceding Faraway Mother)
- Docs: `galidar.com/oceanology-nextgen` (NextGen setup, buoyancy, NextGen Ocean/Lake/Manager actors), `Docs/Research/TOOLCHAIN_INTEGRATION_SPIKE_PLAN` Benchmark E (Sea Above hero liquid/atmosphere shot)

**Faraway Mother integration:**
- Faraway Mother's *FrillValley* lowlands (T<0.40, Z<−1000, fog volumes + brocade flower understory) meet Oceanology at shoreline seams — use RVT landscape integration for seamless water→fabric transition (Oceanology docs: RVT height/gradient folding + shallow water advection via GPU compute shaders).
- Drive Oceanology surface params from the same MPC signal that drives `MF_FabricMountainWPO` — `BassIntensity` → wave amplitude, `BeatPulse` → foam/crest threshold — so sea and mountains breathe together. Already scaffolded in `MelodiaAudioReactivePresentationSubsystem`; extend with a Faraway Mother shoreline preset (`M_Water_Oceanology_Melodia` grafted params).
- Use Oceanology `Water Volume` + pontoon buoyancy for any Faraway Mother traversal that crosses water (e.g., valley causeways), not FluidNinja or custom buoyancy — Oceanology remains authoritative.

---

## 8. VegetationGrowth — SCAFFOLDED PCG Growth Supplement (Not a SpeedTree Replacement)

**What it does:** `UMelodiaVegetationGrowthSubsystem` (scaffold, needs closed-editor build) provides PCG-side secondary growth that *supplements* the PRESENT SpeedTree core plant authority — mutation, grafting, biome placement. SpeedTree owns hero trees/shrubs/branch architecture/wind; this system adds Monolith-corrupted or impossible secondary growth at PCG distribution time.

**Status in repo:** SCAFFOLDED 2026-08-31 additive — per master index §2 and `EMERGING_TOOLCHAIN_IMPLEMENTABLE_ROWS` §2.2. Source in `Source/BS_GodFile/MelodiaIntegration/MelodiaVegetationGrowthSubsystem.h/.cpp`. Probe: `Tools/test_*` pattern (vegetation growth probe to `Saved/Audit/`).

**File paths:**
- Subsystem: `Source/BS_GodFile/MelodiaIntegration/MelodiaVegetationGrowthSubsystem.h/.cpp` — APIs: `PlaceSpeedTreeBiomeTest(RegionAnchor, BiomeFamily)`, `MutateSecondaryGrowth(HostMesh, Seed, Density)`, `GraftBranch(HostBranch, VariantIndex, bDryRun)`
- Present botanical authority: `Content/EnvSandbox/Materials/Masters/M_SpeedTreeMaster.uasset` + `Content/Python/reset_speedtree_wind_instances.py` (master index §1)
- Semantic bridge fields (Houdini/PCG/material decisions, per `TOOLCHAIN_INTEGRATION_SPIKE_PLAN` §SpeedTree): `melodia_moisture`, `melodia_slope`, `melodia_wind_exposure`, `melodia_soil_depth`, `melodia_monolith_proximity`, `melodia_molt_age`, `melodia_filter_flow`, `melodia_tension`, `melodia_ecological_density`
- Faraway Mother ecosystem: `Docs/PCG/FARAWAY_MOTHER_PCG_SYSTEM_ARCHITECTURE.md` (4 biomes, VDM/WPO math, World Field Bus), `specs/pcg/faraway_mother_pcg_manifest.v1.json`, `Tools/PCG/build_faraway_mother_pcg_ecosystem.py --points-per-biome 30`, `Tools/mcp_tool_surface.py` (`PlaceSpeedTreeBiomeTest` surface)
- Orchestration doc: `Docs/Research/EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_02_2026-08-30.md` §9 Errant Biomes (comparison benchmark vs. UE PCG)

**Faraway Mother integration:**
- Map 4 biomes to `PlaceSpeedTreeBiomeTest` families: `WeaveRidge` (T>0.60) → wind-exposed prayer-strip vegetation; `LaceCanopy` (0.40–0.60) → translucent lace trees + pearl berry understory (`MEL_mother_lace_tree`, `MEL_mother_pearl_bush`); `FrillValley` (T<0.40) → brocade flowers + frill arches; `ResonantSeamWay` (|Chladni|<0.12) → sparse, corridor-aligned growth.
- Drive `MutateSecondaryGrowth` density directly from `WorldField.Tension` (see `FARAWAY_MOTHER_PCG_SYSTEM_ARCHITECTURE` §3.3) and Houdini `tension_mask.png` (from `FARAWAY_MOTHER_DRAPE_SPEC` — `Saved/Audit/houdini_faraway_mother/tension_mask.png` + `drape_attributes.json` per-vertex Tension/Resonance).
- Fabric ridge foliage placement: PCG graph `PCG_Faraway_FabricRidge` reads `HDA_ENV_ScatterMaskBuilder` outputs (tension + slope + curvature) → candidate points → `GraftBranch` for Monolith-corrupted variants only where `melodia_monolith_proximity` is high. Sandbox-only testing per master index anti-duplication rule — never migrate chapter maps until isolated R&D map passes.

---

## 9. Dressing — SCAFFOLDED Native Dressing / Art-Pass (Dash-Capability Fallback)

**What it does:** `UMelodiaDressingSubsystem` — the native "Dash-capability" editor art-pass: hero prop placement, physically-dropped debris, composition cleanup around camera-critical areas. Dash (Polygonflow, commercial marketplace plugin) is NOT vendored/installed — verified absent in `Plugins/` — so the native subsystem is the buildable fallback per `DASH_MAGPIE_NATIVE_INTEGRATION_2026-08-31.md` §1.

**Status in repo:** SCAFFOLDED 2026-08-31 additive, needs closed-editor build. Convergence-safe: reuses existing SM_/MI_ library + PCG `FGameplayTag` families, no parallel master/combat authority, no `Content/_PROJECT/` writes.

**File paths:**
- Subsystem: `Source/BS_GodFile/MelodiaIntegration/MelodiaDressingSubsystem.h/.cpp` — `DressHeroClutter(CameraFocus, FamilyTag, Count)`, `PhysicallyDrop(Actors, DropOffset, Restitution)`, `FindCompositionOccluders(CameraFocus, Radius, MaxReports)`, catalog path `/Game/MelodiaIntegration/Config/DA_MelodiaDressingCatalog`
- Decision doc: `Docs/Research/DASH_MAGPIE_NATIVE_INTEGRATION_2026-08-31.md` (§1 Dash → native subsystem, §4 delivery order)
- Spike plan: `TOOLCHAIN_INTEGRATION_SPIKE_PLAN` Test 06 (Dash — 30–45 min, 20-min art pass benchmark on duplicated PCG/SpeedTree baseline scene)
- Probe: `Tools/test_dressing.py` → `Saved/Audit/dressing_probe_*.json`
- Alternatives that ARE present: `PCGExtendedToolkit`, `ProceduralDungeon`, `ProceduralModelingToolkit`, `HoudiniEngine`, `GaeaUnrealTools` (same doc §0 ground truth table)

**Faraway Mother integration:**
- After PCG generates Faraway Mother scatter (120 points, 30/biome), run `DressHeroClutter` as the final human composition pass on hero viewpoints (Heart Gate `challenge.mother_heart_gate` camera, shoulder-fold overlook) — places tagged hero props (loom shuttles, prayer strips, brocade fragments) from `DA_MelodiaDressingCatalog` families.
- Use `PhysicallyDrop` for FrillValley debris (frill rocks, fallen lace) under gravity, then `FindCompositionOccluders` to flag props occluding Heart Gate framing — never auto-deletes, flags for owner.
- Pass condition (from SSOT): *"a 20-minute dressing pass makes a PCG-generated test scene visibly more authored with no fragile plugin-only runtime deps"* — validate on `L_KaleidoNave` or `LV_FarawayMother_Prototype` before promoting beyond sandbox.

---

## 10. CaptureRender — SCAFFOLDED Offscreen HDR Render Pipeline (4-View, PPV Gate)

**What it does:** `UMelodiaCaptureRenderSubsystem` — offscreen `SceneCapture` HDR pipeline (4-view, PPV gate) for deterministic lookdev verification, contact sheets, and audit renders. Validates that the PPV stack is canonical before capture; writes to render targets or files.

**Status in repo:** SCAFFOLDED 2026-08-31 additive, needs closed-editor build. Offscreen only — no gameplay authority.

**File paths:**
- Subsystem: `Source/BS_GodFile/MelodiaIntegration/MelodiaCaptureRenderSubsystem.h/.cpp` — `ConfigureSurface(Surface, Resolution)`, `CaptureToRenderTarget(Target)`, `CaptureToFile(LevelName, Surface)`, `IsPPVStackCanonical(OutReason)` (PPV gate)
- Probe: `Tools/test_dash_capture.py` → `Saved/Audit/dash_probe_*.json`
- Orchestration: `Tools/mcp_tool_surface.py` (`RunPerformanceCapture` + `AuditDataLayers` surfaces), `Tools/branch_health.py`
- Material audit lane: `Tools/Houdini/sea_above_reef/bake_rasterize_ao.py` manifest discipline (seed-locked), `Tools/verify_tex_contract.py` (BC7/BC5/BC4 compression contract)

**Faraway Mother integration:**
- Primary use: **VDM lookdev QA** — capture 4-view HDR contact sheets of `SM_FabricRidge_Hero` VDM baking (SOP vs. COP vs. UE static-displacement import) and of WPO animation states (BeatPulse / BassIntensity extremes) to verify no UV-seam cracks or tension-mask errors before chapter map migration.
- Gate every Faraway Mother material promotion through `IsPPVStackCanonical` — Faraway Mother's `MI_T_FarawayMother_*` variants (CelestialSilkJacquard, AquaticLullabyLace, GildedAcanthusBrocade, NightSkyVelvet) must prove they don't regress the `M_Master_Toon_Universal` / `M_Master_Nikki_Landscape` PPV stack.
- Run `Tools/mcp_tool_surface.py --dry` to preview `RunPerformanceCapture` on an isolated R&D map; promote to `--live` against Monolith `:9316` in sandbox only (master index rule 6: one editor, batch saves `unattended:true`, no `Content/_PROJECT/` writes; evidence = offline probe + live PIE + ledger row).

---

## Appendix — Quick Reference for Fabric Mountain Work

| System | Status | Next Concrete Step for Faraway Mother |
|---|---|---|
| **VDM SOP bake** | No VDM in project; path exists via Labs Maps Baker | Build `HDA_ENV_FabricMountain_VDMBake` (high Vellum + low proxy → EXR 4K VDM), mark editable nodes, seed-lock manifest |
| **VDM COPs** | Copernicus PRESENT (baked 11 families, 1665 PNGs) | Extend COP network with Labs Maps Baker Vector Displacement → Denoise → File Output (BC6H EXR) |
| **UE VDM / Nanite** | Experimental (vector disp. + UV cracks = known issue) | Ship hero pleats as **Static Displacement** Nanite meshes; animate via WPO/MPC, not runtime VDM |
| **WPO** | PRESENT (`MF_FabricMountainWPO` plan, `MF_ClothWindDrape`, cymatics) | Drive 4-layer WPO from `MPC_Melodia_Palette` + `UMelodiaCymaticsSubsystem` Chladni — single MPC writer preserved |
| **Magpie seam** | Scaffolded read-only | Add `GetWorldFieldTension`/`GetCymaticAmplitude` read accessors; use for lookdev overlay |
| **Neural shaders** | WATCH (embedding ONNX only) | Scaffold `MF_NeuralFabricApproximation` with analytic fallback; measure VRAM if material ONNX arrives |
| **Oceanology** | PRESENT (`Plugins/Oceanology_Plugin/`) | Extend audio-reactive drive for shoreline RVT blend; keep as water authority |
| **VegetationGrowth** | Scaffolded | Wire `WorldField.Tension` + `tension_mask.png` → `PlaceSpeedTreeBiomeTest`/`MutateSecondaryGrowth` per 4 biomes |
| **Dressing** | Scaffolded (native Dash fallback) | Post-PCG `DressHeroClutter` + `PhysicallyDrop` + `FindCompositionOccluders` on Heart Gate viewpoints |
| **CaptureRender** | Scaffolded | 4-view HDR contact sheets for VDM bake verification + PPV canonical gate per material promotion |

**Binding rules (from `EMERGING_TOOLCHAIN_MASTER_INDEX` §9):** extend PRESENT, finish SCAFFOLDED before parallel copy, WATCH needs owner task, external = say-so-don't-fake, reuse World Field Bus / SpeedTree bridge field names, one editor at `:9316`, evidence = offline probe + live PIE + ledger row.
