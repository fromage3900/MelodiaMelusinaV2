# Melodia — Subagent Findings Atlas + Updated Workplan
## LOD Vision Manipulation for Faraway Mother
**Date:** 2026-09-02 | **Status:** Living SSOT — fusing 6 delegations (15 subagents)  
**Principles:** Height-aware PCG mandatory, instances only, single MPC writer, vision manipulation via Perceptual LOD

---

## 1. SUBAGENT FINDINGS — COMPLETE ATLAS

### 1.1 Intake Triad (deleg_3c8d1755 — 3 scouts, 208s)

**Infinity Nikki Lens — Wardrobe**
- Authority: `Plugins/MelodiaWardrobe` (GameInstanceSubsystem, Decision 043), `MelodiaWardrobeComponent` (Decision 044), 15 plugins total
- Catalog: `DA_MelodiaCosmeticCatalog` + 39 drafts `Cos_*.json` (dress/hat/gloves/shawl/trail), 5 slots × 5 Commons = `MelusinaV2` shipped, `MelusinaV2_ResonantWeave` (Uncommon, Glide) is P0 gate `wardrobe_equip_roundtrip` HOLD
- Material: 5 Universal masters + 40+ MooaToon masters, `M_Character_Clothing`, Ink PP, hybrid lanes (SHAWL.001, Water Advance hair), Nikki bar via `Content/Melodia/Nikki/MI_Nikki_Iridescent`
- UI: 26 WBPs, `WBP_Lookbook_OutfitBrowser.cs` (grid, rarity colors Common #64b5f6→Grandmaster #ffd54f), `melodia-design-system/tokens.json` (Ivory/ Astral #141A30), 200 figma exports gitignored, `WBP_MelodiaQuillDialog` tracked
- Gaps: `materialization_status: source_ready_editor_materialization_pending` (SK_Melusina_V2_ meshes unproven), `bEnableBattleWardrobe=false`, Komikaze tools lost (`.pyc` only), shard vs Golden pricing split, `Refined`/`Couture` drift, Lookbook stub `.cs` not `UWidget`

**Houdini Savant Lens — Procedural Spine**
- Houdini 22.0.368 + Engine 3.0 + PCGEx toolkit — Bridge PASS (WP25600, hython present), FREE Engine license needed via `hserver -l`
- COPs/Copernicus: **~100K lines** — `copernicus_cymatic_parallax.py` (65KB, 11 families + 5 glitter + fractal/golden spiral/voronoi), `surreal_cobble` (3 variants, 8 maps), `dress_bake` (4K BC/N/ORM), `terrain_height_to_nanite` (Heightfield→Nanite)
- HDA: `hda/` empty, `Content/HDA/` missing, 16 hip/hipnc (only 3 surreal cobble >100KB real), `create_hda_arpeggio_stair.py` headless builder exists but never cooked, 6 example HDAs shipped in plugin
- PCG: 103 py builders, `pcg_scale_world_pipeline.py` (WP_CELL_SIZE 25600, BIOME_BANDS stone_court/moss_rim/blue_void/crystal_meadow/wind_shelf, 5 hero graphs ResonanceCathedral/ArpeggioBridge/BellTreeGarden/XylophoneTrail/CrystalHarpGrove), 29 demo graphs stock, 42 legacy `_landscape_*.py` at odds with MeshTerrain-only rule
- Gaps: No production HDA ever baked (90% authoring code, 10% cooked evidence), PIL rasterizer still shipped path (not COP), Apprentice 1080p cap blocks 4K + groom `.abc`, terrain spine spec-only (no heightmap ingested), PCG is Python-graph not Houdini-PCG, no SessionSync evidence

**Environment Designer Lens — World + Sea Above**
- Levels: `ZenForestTest` 63 MB (only mature), `L_KaleidoNave` 344 KB (14 external actors, 16 hex cells), `LV_SeaAbove_Prototype` 15 KB (100+ externals), `L_FallenMoon` 14 KB skeleton, 5 PCG Hero musical biomes, 4 Gaea WP terrains (CadenceCrystalRidge etc)
- Sea Above: Gaea LiquidCathedral, 306 actors (193 Cathedral Kitbash + 98 Atlantis + 12 Houdini), 2 active PCG (86+48), 30 Copernicus MIs, zones canyon/valley/plaza/spiral/highlands, but `SM_SeaAbove_LiquidCathedral_257` only placed mesh, plane 500m (needs 6km), Bell crown -180m (needs -60m), banding veto violated if colonnade crosses surfaces
- Landscapes: ZenForest painted vs Gaea imports (VolcanicCrater, AuroraGlacier), 13 landscape MIs, `M_HybridLandscape_MooaToonSDF`, World Partition CellSize 25600 default (FallenMoon 12800), DataLayers: only SeaAbove has 4 (Creature/Islands/Lighting/Water), KaleidoNave/FallenMoon have none (spec demands Day/Night/PCG_Foliage)
- Kitbash: Atlantis 333 meshes + 424 textures + 83 MIs (BldgLgPalace_A), EnchantedVehicles 100+ FBX raw, Reef kit 36 meshes + 9 MIs + 3 VDBs (`GhostFog/GodRays/NebulaVeil`) — **zero placed except 1 cliff**
- Gaps: DataLayers absent, landscapes unpainted except ZenForest, lighting incomplete (no PPV bound, UDS unused), kitbash unplaced, SeaAbove illusion broken (altitudes/plane size), composition tiny umaps vs 63 MB, HLOD exists but unvalidated

### 1.2 Fringe Research Triad (deleg_2cb1a7fd — 3 scouts, 238s)

**Cymatic Breathtaking (7 findings)**
1. **Houdini 20.5 COP Chladni native** — `sidefx.com/docs/houdini/nodes/cop/chladni.html` — non-integer a/b, GPU tileable, feeds LABS Baker. Replace VEX cos loop, drive a/b from audio bands, 10× iteration
2. **Marcus Kulik Chladni Plate Engine** — `marcuskulik.com/tech/chladniengine` — VEX → gradient field → DOP advect → Vellum Grains pin. Any image can replace Chladni, noise on direction/speed. Bake vector field to vertex color for WPO
3. **joshuarrr/cymatics** — `github.com/joshuarrr/cymatics` — JS 512 FFT smart mapping: Bass 20-250Hz → m,n (1-16), Mid → vibration 0.01-0.1, Treble → a,b -2..2. Lift into `MelodiaCymaticsSubsystem::Tick()` + `MPC_Cymatics_Driver` (M/N/Vibration/AB)
4. **Lahe/AudioVisual + Niagara Audio Spectrum** — `github.com/Lahe/AudioVisual` — Niagara Data Interface 64 bands, no BP tick. `NS_Cymatics_Resonance` sampling `RT_CymaticsPattern` height map, gradient texture advect, BeatPulse burst
5. **coreyepstein/cymatic auto-director** — `github.com/coreyepstein/cymatic` — tracks song arc intro→drop, macros intensity/motion/bloom, MoodVector, WebGPU HDR bloom. Port to `UCymeticsDirectorComponent`
6. **Audio-Shader-Studio uniforms** — `github.com/sandner-art/Audio-Shader-Studio` — exhaustive uniforms bass/treble/centroid/energy/beat/onset + 256×1 freq + 512×1 time textures. Mirror as MPC + 1D textures, Custom HLSL `tex2D(FrequencyTexture)`
7. **3DChladni volumetric** — `github.com/CDInstitute/3DChladni` + Shadertoy `lfsfzN` — 128³ SDF volume for fabric mountain interiors, Heterogeneous Volume material, marching cubes. Bake or raymarch boss arena

**NMS Scale (7 findings)**
1. **NMS Hierarchical Deterministic** — 64-bit seed → galaxy→planet hierarchy, Superformula `r(φ)`, fBm + domain warp, tag-driven cohesion. `hda_nms_universe_seed` for Sea Above archipelago, zero storage, store seed+delta only
2. **Houdini COPs Tiled Terrain** — Heightfield as COP image layers, GPU, tiling + erosion. `cop_terrain_sea_above.cop` tiled 4K, Solver SOP animated micro-erosion
3. **Massive Worlds Toolkit** — `ehoudiniacademy.com/massiveworlds` — bi-directional Houdini↔WP Edit Layers + RVT + PCG, externalized caches, road toolkit. Immediate Sea Above upgrade
4. **Adrian Pan HE4UE Rebuild** — `github.com/AdrianPanGithub/HoudiniEngineForUnreal` — 2-15× faster, `unreal_split_actors`, COPs translators, OFPA packaging
5. **UE 5.6/5.7 PCG Hierarchical + Partitioned Volumes** — `HiGenGridSize`, partitioned volumes, bake vs runtime, HLOD. 64 km²+ biome→feature→dress passes
6. **CDPR Fast Geometry Streaming / TurboEntities** — POCO TurboEntity + Render/PhysicsProxy worker threads, FastGeo plugin. 95% off main thread, 60fps infinite forest — NMS ceiling breaker
7. **CHOPs + TouchDesigner → UE Audio-Reactive** — CHOPs spectrum/trigger → SOP params + OSC/Spout → Niagara. Core audio→terrain pipeline, `How to Create Terrains in COPs` talk

**Blender Audio GN (8 findings)**
1. **5.2 Sample Sound Frequencies native PRIMARY** — `docs.blender.org` — Sound+Time+Low/High+FFT→Amplitude, VSE strip, scrub-safe, FFmpeg. 3 bands bass 20-250Hz→fabric amplitude, mids→fold freq, highs→emissive. Bake via Named Attribute→Alembic or 1px image sequence→Curve Atlas→UE
2. **Sound Nodes (negdo)** — `github.com/negdo/Sound_Nodes` — Loudness/AvgFreq/Beats + Spectrogram/Chromagram 32-64 bands radial, chromagram 12-TET → wardrobe hue. Keyframes→CSV/JSON→DataTable
3. **Sound Reaktor** — `blenderartists.org/t/.../1633918` — SciPy 6 methods FFT/Onset/RMS/Centroid/Flatness/Rolloff, 9 presets, Drivers+Keyframes, 50-200× faster than native. Custom mode drives any GN input. Drivers→bake→Alembic/texture/JSON → `UMelodiaAudioReactiveSubsystem`
4. **AudVis** — `github.com/example-sk/audvis` — Sequence+Realtime + MIDI File/Realtime (only MIDI), scripting API. Bridges Melodia MIDI puzzle, live playtest via LiveLink
5. **Animation Nodes Sound Spectrum** — legacy reference, cleanest API (Full/Single/Custom, Attack/Release, Max/Mean). Spec for builder
6. **Simple Audio Visualizer (polyfjord)** — `github.com/polyfjord/Simple-Audio-Visualizer` — bake-sound-to-fcurve minimal
7. **Wavelet / GSoC Wavelab** — devtalk `draft-gsoc-2026-geometry-nodes-wavelab` — upcoming procedural sound in GN
8. **Curve Atlas / VAT bake** — shared 2-track: procedural authoring with native Sample Sound in `GN_MEL_AudioReactive_Fabric_v01`, then bake for UE via Alembic/Curve Atlas/DataTable → Niagara/PCG/Material

### 1.3 Current Night Sprint (deleg_73cbbf1e + deleg_40d39855 + deleg_578c0132 + deleg_55c9e6c1 + deleg_166ed9f8 — 12 hands running)

- **Flowers:** OSC gate (validate_osc_loop.py, 14 routes on 9000, battle_osc.py raw sockets, osc_server.py raw UDP, MPC_Melodia_Palette single writer) + GN flower (`Sample Sound Frequencies` 6-petal, bass→scale etc, .blend/.abc) + TD CHOP (File In→Spectrum→3 bands→OSC Out 9000 /melodia/audio/*) — all running
- **Copernicus Expanded:** 30 MIs → +5-8 Faraway Mother fabric variants (celestial silk/mountain velvet, Chladni modes, PBR 9 maps) via `copernicus_fabric_sheen.py` + `cymatic_parallax.py` — running
- **Lookdev Toon 5.8:** Masters `M_Master_Toon_Universal/Character/Landscape_HeightBlend/Cosmic/Unified` + MooaToon + SDF + Glitter/Cathedral functional, PostProcess `MI_PP_StorybookOutline` etc, Ink lanes, Perceptual LOD 4-tier (POM32→0, Toksvig, Bayer 8x8/BlueNoise 64x64, rim 1.4→1.8×), Claireon + NNERuntimeORT onnx present — research running
- **3D AI Spatial:** `MelodiaVisualRepresentationSubsystem` (Magpie seam), `MelodiaCaptureRenderSubsystem` (4-view HDR), Claireon qwen3-coder 7/8, onnx bge-small-en — research running
- **Scaffold:** `build_optical_lod_matrix.py` + `FarawayMother_CelestialSilk` (Chladni 3,5) 4-tier + `melodia_optical_lod_pipeline.py` 12 MIs + `optical_lod_manifest.v1.json` — scaffolding
- **Faraway PCG:** `MEL_terrain_fabric_ridge` (Width/Height/Fold Depth/Count) + valley/haze/cascade + height-aware raycast to CanonicalLandscape/MeshTerrain, `LV_FarawayMother_Prototype` prototype — building
- **Brass:** 14 modifiers (tube/bell/valve/slide/tone_hole/bracing/lead_pipe/rib/spiral/chevron/mouthpiece cup/shank/partial holes/wrap) + `MI_Starskiff_Brass` + filigree/patina textures, expanding to 17 + 6-8 animated MIs (panning, BeatPulse emissive, patina blend, flipbook) — expanding

---

## 2. THE LOD ILLUSION PLAN — MAKING FARAWAY MOTHER BREATHTAKING

### 2.1 Core Thesis — Vision Manipulation via Perceptual Continuity

The documented `MELODIA_PERCEPTUAL_LOD_LOOKDEV_ARCHITECTURE.md` is not an optimization — it's a **perceptual weapon**. The Faraway Mother is a mountain that is a body that is fabric. The player must never resolve which is true. LOD is how we lie truthfully.

**4-Tier Continuum as Narrative Device:**

| LOD | Distance | Shader | What Player Sees | What It Is |
|-----|----------|--------|------------------|------------|
| **LOD0** 0-15m | 32-step POM + thin-film iridescence + 4-harmonic | Fabric weave, stitch, jacquard Chladni (3,5) micro-weave, thread-level gloss | Torso valley floor — fabric terrain, walkable |
| **LOD1** 15-50m | 16-step POM + moderate Toksvig + 75% WPO | Fold depth, drape tension, shoulder ridge gathers | Valley walls — fabric mountains, implied anatomy |
| **LOD2** 50-200m | Macro normals + Toksvig + rim 1.4× | Silhouette reads as reclining figure, hair cascade ribbon, moon haze edge | Whole mother — mountain range as body |
| **LOD3** 200m+ | Vista impostor + max Toksvig + rim-bloom 1.8× | Moonlit haze, single brushstroke, memory of mother | Horizon — implied limbs, no mesh, pure fog |

**The trick:** Each LOD is *true* at its distance. No popping — dithered Bayer 8×8 / BlueNoise 64×64 crossfade over 5m window, smoothed by TSR/TAA, so the fabric *becomes* flesh as you retreat. The eye is reassigned without consent.

### 2.2 Five Vision Manipulation Techniques (from LOD doc)

**1. Toksvig Anti-Aliasing — Preserve the Glint That Should Be Lost**
- Math: `R_adjusted = sqrt(R_base² + w_toksvig * σ²)` where `σ² = (1-|N̄|)/|N̄|`
- Faraway Mother: At LOD2/3, high-frequency normal variance (weave) would collapse to shiny shimmer. Toksvig folds variance into roughness, so distant mountains keep a soft, pearl-like highlight — like moon on distant silk, not aliased sparkle. Capable of making 200m+ vista read as *material* not noise.

**2. Adaptive POM — Depth That Isn't There**
- Math: `P_offset = V_xy/V_z * H * h_scale`, steps 32→16→0 by `N_steps(d,θ) = round(lerp(Nmin,Nmax,1-N·V)) * clamp(1-(d-d0)/(d1-d0))`
- Faraway Mother: LOD0 valley floor has *real* parallax crevices between folds (32-step ray march, view-angle dependent). By LOD1, POM decays gracefully — folds flatten but normals keep shape. Player feels fabric depth underfoot that vanishes at horizon, selling impossibility: you walked on cloth, but the mountain was never cloth.

**3. Dithered Screen-Door Crossfade — The Seamless Lie**
- Math: `α(d)=clamp((d-d_start)/(d_end-d_start))`, discard if `α < M8(px mod 8)`
- Faraway Mother: 5m overlap between each LOD. As player walks from valley (LOD0) toward shoulder ridge (LOD1), the weave texture stipples into macro-form without pop. At 50m, the same mountain that was fabric *is* flesh — the stipple was the transmutation. TSR hides the dither; eye never catches the swap.

**4. Grazing Rim Sheen — Hide the Polygon, Sell the Scale**
- Faraway Mother: LOD2/3 meshes are low-poly by necessity (Nanite fallback). Silhouette faceting is hidden by Fresnel rim: 1.4× at LOD2, 1.8× + bloom at LOD3. The moon rim catches the mother silhouette — a mother-shaped glow, not a low-poly edge. She never looks low-poly; she looks backlit.

**5. Chladni Jacquard Weave (FarawayMother_CelestialSilk) — Audio Drives Vision**
- From matrix: `Chladni Mode (3,5) Jacquard Weave` for FabricMountain
- Map `MelodiaCymaticsSubsystem` audio bands → Chladni n,m + vibration → iridescence tint + emissive pulse (via `MPC_Melodia_Palette` BeatPulse or new `MPC_Cymatics_Driver`). The weave *breathes* with music — calm littoral still, membrane phase shimmering. Player hears the mountain as vision.

### 2.3 Body Map — Model vs. Implied via LOD

From `FAR_AWAY_MOTHER_PRODUCTION_SHEET_2026-08-29.md`:

| Body Part | LOD0-1 (close) Model | LOD2-3 (far) Implied | Manipulation |
|-----------|----------------------|----------------------|--------------|
| Head silhouette | Sculpted ridge `BP_MotherHead_Silhouette` (hero mesh, Toon Unified, profile reads left) | Same mesh, rim-bloom only | High-poly hero only needed close — LOD3 replaces with haze imposter |
| Hair cascade | Niagara ribbon `BP_HairCascade` (translucent, `M_Oceanology_NikkiHero`, flow) | Single ribbon + volumetric haze tint | LOD2 merges strands → one silver thread |
| Shoulder/chest folds | Terrain + fabric normal `MI_Master_Nikki_Landscape` (POM depth) | Macro normal only, Toksvig bloom | POM gives close depth, macro normal gives far read |
| Torso valley | Depression + fog `MEL_valley_depression` (player walks here) | Depression only, denser fog, floor dark cool grey wet specular | Valley is gameplay lane at all LODs — fog density is rhythm-driven |
| Distant limbs | Not modeled | Moon haze volume `MEL_moon_haze_volume` (silver-blue 0.70,0.75,0.90 density 0.04) — no mesh | Pure volume, cost-free, reads as anatomy at horizon |
| Hands/feet | Rock scatters | Rock scatters merged to silhouette | 3 Atlantis arches → one limb shape via HLOD |

### 2.4 Rhythm + Fashion + LOD Integration

| System | LOD-Aware Behavior |
|--------|---------------------|
| **Moon phase** | Beat-synchronized intensity — breathing via `MPC_Melodia_Palette` BeatPulse → emissive + rim intensity (LOD2/3 bloom pulses) |
| **Fog density** | Rhythm accuracy → fog clarity: Perfect = thin (see mother), Poor = thick (lose her). Volumetric fog box density 0.04 → 0.08 driven by accuracy grade |
| **Highway** | Notes travel along hair cascade ribbon — LOD0: many ribbons, LOD2: one ribbon, same path |
| **Fashion** | Celestial/marine silhouettes (wardrobe) open membrane paths — `EquippedCosmeticIds` check, `IMelodiaTraversalCapabilityProvider` grants traversal, membrane WPO opens |
| **Checkpoint** | Rhythm gate at "heart" — stabilize moon phase (single writer) to proceed, fog clears, silhouette sharpens (LOD2→LOD1 via dither as reward) |

---

## 3. UPDATED WORKPLAN — METHODICAL EXECUTION

### Phase 0 — Prove the Spine (Tonight, 4h) — KEEP WORKING

| Task | Owner | Output | Health Gate |
|------|-------|--------|-------------|
| OSC 9000 → MPC health | Env | `Saved/Audit/osc_health_2026-09-02.json` PASS (14 routes + 3 audio bands) | `validate_osc_loop.py` |
| GN Flower `Sample Sound Frequencies` | Blender | `Exports/FlowerAudio/SK_Flower_Audio.*` + spectral 1px texture | PIE flower breathes |
| TD CHOP → OSC live | TD | `/melodia/audio/bass/mid/treble` + BeatPulse on 9000 | OSC monitor |
| Height-aware placement | UE | Flowers in `LV_SeaAbove_Prototype` / `L_PetalCantata` raycast Z, captures | `*_audit.json` + `.mp4` |

### Phase 1 — Faraway Mother LOD Illusion (Next, 1 week)

**1A. Scaffold Perceptual LOD Matrix (2h) — IN PROGRESS**
- Run `Tools/LookDev/build_optical_lod_matrix.py` → `FarawayMother_CelestialSilk` 4-tier (51 maps: BaseColor/Normal/ORM/Height ×4 + Bayer/BlueNoise/Iridescence LUT)
- Via `Content/Python/melodia_optical_lod_pipeline.py` → 12 MIs `MI_FarawayMother_CelestialSilk_LOD0..3` (+ shared utilities) with Toksvig w_toksvig 0.0→1.0, POM steps 32→0, rim 1.0→1.8×
- Manifest: `specs/lookdev/optical_lod_manifest.v1.json`

**1B. Height-Aware Fabric Ridge PCG (1 day) — IN PROGRESS**
- Build `Content/Python/build_faraway_mother_height_aware_pcg.py` — raycast to `CanonicalLandscape` / MeshTerrain, no floating, no new landscape
- Use `MEL_terrain_fabric_ridge` (Width/Height/Fold Depth/Count), `MEL_valley_depression`, `MEL_moon_haze_volume`, `MEL_cascade_hair_ribbon` GN builders
- Place in `LV_FarawayMother_Prototype`: head silhouette → hair cascade → shoulder valley → torso depression → haze limbs → checkpoint gate (top-down per production sheet)
- PCG graph: `PCG_FarawayMother_FabricRidge` with `WP_CELL_SIZE 25600`, height-aware attribute `height_mask` vertex color, DataLayer `DL_FarawayMother_Fabric`
- 5-8 instances height-aware, moon-haze volume silver-blue, hair ribbon Niagara

**1C. Vision Manipulation Pass (2 days)**
- Bind each LOD tier to material: `M_Master_FarawayMother_Fabric` with distance-driven switches (LOD0 POM, LOD1 Toksvig 0.3, LOD2 Toksvig 0.7 + rim 1.4×, LOD3 impostor + rim bloom 1.8×)
- Dithered crossfade: assign `T_LOD_BayerDither_8x8` / `BlueNoise_64x64` to material `DitherTemporalAA` node, 5m window, TSR smoothing proof
- Audio→Chladni: `MelodiaCymaticsSubsystem` n=3,m=5 base, audio Bass 20-250Hz → m,n 1-16, Mid → vibration, Treble → a,b per joshuarrr mapping, write to `MPC_Cymatics_Driver` → MI IridescenceTint/EmissiveScale/UV distortion
- Brass accent: `MI_Starskiff_Brass` filigree on head silhouette rim, patina animated via BeatPulse

**1D. PPV + Lighting Lock (1 day)**
- Bind `MI_PP_StorybookOutline` + `M_PP_StarryNightOverlay` to `LV_FarawayMother_Prototype` on `DL_Lighting` (only real DLCs + new `DL_FarawayMother_Fabric`)
- Moon horizon: low silver-blue directional + SkyAtmosphere + VolumetricCloud, height fog tuned for sub-surface, Oceanology SLW absorption removed (not water level)
- Camera hero frames: 3 locked CineCameras (valley floor LOD0, shoulder LOD1, horizon LOD3) for portfolio, `MelodiaCaptureRenderSubsystem` 4-view HDR

### Phase 2 — Cymatic Breadth (Week 2)

- Marcus Kulik vector-field HDA → grains flowing to Chladni nodes across nave (GildedLoom/CavernWeave 12 MIs regenerated with mixed-mode)
- COP Chladni native bake → 4K PBR sets for `MF_CymaticParallax`
- Niagara `NS_Cymatics_Resonance` 20k GPU particles advected by gradient texture, BeatPulse burst, along nodal lines

### Phase 3 — NMS Experimental Scale (Week 3)

- NMS seed `hda_nms_universe_seed` (64-bit) → deterministic Sea Above archipelago (store seed+delta)
- Massive Worlds Toolkit → World Partition tiled landscape 5000×3000 → 25600 cells, HLOD, RVT
- COPs tiled terrain `cop_terrain_sea_above.cop` + PCG hierarchical biome→feature→dress (5 hero graphs), FastGeo TurboEntity for 95% off main thread

### Evidence Per Phase

1. PIE with labeled overlay (matches production sheet top-down)
2. Assertion JSON next to captures `Saved/Audit/faraway_mother_*.json`
3. `Saved/gate_ledger.json` row `faraway_mother_prototype` + `p2_faraway_mother_height_aware`
4. SHA-256 of new MIs/textures, `optical_lod_manifest.v1.json` hash

---

## 4. CREATIVE LOD MANIPULATIONS — MAKE HER BREATHTAKING

**The core idea:** Faraway Mother is never fully seen. LOD is not optimization — it's dramaturgy.

**Manipulation 1 — The Fabric That Remembers Skin**
Close: fabric weave with stitch POM; mid: folds that happen to be a shoulder; far: a sleeping woman. The crossfade *is* the reveal. No cutscene.

**Manipulation 2 — The Haze That Has Shape**
No mesh for limbs. At 200m+, volumetric fog + rim bloom *implies* limbs where there are none. Player swears they saw hands. HLOD merges 3 Atlantis arches into one limb silhouette — cheaper than meshing, more haunting.

**Manipulation 3 — The Breathing Moon**
Rhythm accuracy drives fog density + emissive. Perfect play → fog thins, mother sharpens (LOD2→LOD1 dither as reward). Miss → haze thickens, she recedes. She lives when you play well.

**Manipulation 4 — The Ribbon Highway**
Hair cascade ribbon is also rhythm highway. LOD0: many strands, LOD2: one. Notes travel the same path regardless of strand count — gameplay persists across LOD collapse.

**Manipulation 5 — The Impossible Scale**
Material `FarawayMother_CelestialSilk` uses Chladni (3,5) at LOD0 (weave) but same Chladni scaled at LOD3 (vista geology). Same math, different perceived scale — impossible textile-landscape.

---

**Tonight's first concrete step (queued):** Height-aware PCG ridge + LOD0 material in valley → PIE proof that fabric reads as terrain at 5m and flesh at 50m with no pop. Then iterate outward.

*— Atlas compiled 2026-09-02 ~01:05 from 15 live subagents; full transcripts at `C:\Users\froma\AppData\Local\hermes\cache/delegation/live/*` and summaries under `subagent-summary-*.txt`. Next update when scaffold + PCG land.*
