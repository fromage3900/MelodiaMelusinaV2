# NMS-Scale Procedural + Audio-Reactive Pipelines — Research Report
**Date:** 2026-09-02 | **For:** Melodia `Sea Above` large-scale experimental systems (Gaea + PCG + Kitbash → Houdini NMS-scale)
**Scope:** Reddit/niche repos, Houdini large-scale terrain, UE World Partition + PCG, procedural universe/planet gen, audio-reactive

> 7 bleeding-edge approaches with verified URLs and concrete Melodia integration paths. Each is selected to extend—not replace—the PRESENT toolchain (Houdini/Copernicus, PCG, World Partition, audio-reactive writer) per `EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md` §9.

---

## TL;DR Matrix

| # | Approach | Core Tech | Scale Claim | Audio-Reactive? | Maturity | Melodia Fit |
|---|----------|-----------|-------------|-----------------|----------|-------------|
| 1 | **NMS Hierarchical Deterministic Gen** (Superformula + fBm + domain warp) | Single 64-bit seed → galaxy→system→planet→biome hierarchy | 18 quintillion planets, 0 storage | No (seed-driven) | Shipped (2016→2026) | Universe/planet archetype generator |
| 2 | **Houdini COPs/Copernicus Tiled Terrain** | Heightfield as COP image layers, GPU-accelerated | Arbitrary tiled landscapes, 8K+ per tile, non-destructive | Yes via CHOPs→COPs | GA Houdini 21–22 | Replace Gaea single-shot with procedural graph |
| 3 | **Massive Worlds Toolkit** (Erwin Heyms) | Houdini HDAs ↔ UE World Partition Edit Layers + RVT + PCG | Multi-landscape, bi-directional, externalized data | Hookable | v1.1, Patreon, UE 5.3–5.5 | Immediate Sea Above pipeline upgrade |
| 4 | **Adrian Pan HoudiniEngineForUnreal (HE4UE Rebuild)** | Rewritten Houdini Engine, 2–15× faster I/O, `unreal_split_actors`, COPs/Mass translators | Native OFPA + packaging, no bake | Via custom translators | Active GH, UE 5.4+, Houdini 21+ | Performance fix for Houdini→UE at scale |
| 5 | **UE 5.6/5.7 PCG Hierarchical Generation + Partitioned Volumes** | PCG Graph with `HiGenGridSize`, partitioned volumes, bake vs runtime, HLOD | 64 km²+ with hierarchical biome→feature→dress passes | No (but attribute-driven) | Production-ready UE 5.7 | Biome/dress layer for Sea Above |
| 6 | **CDPR + Epic Fast Geometry Streaming / TurboEntities** | POCO `TurboEntity` + `RenderProxy`/`PhysicsProxy` on worker threads, FastGeo plugin | 95% geometry off main thread, 60fps infinite forest | No | Experimental UE 5.6, Witcher 4 demo | Scale ceiling breaker for NMS-scale |
| 7 | **Houdini CHOPs + TouchDesigner → UE Audio-Reactive Pipeline** | CHOPs spectrum/trigger/Analyze CHOPs → SOP params + OSC/Spout → Niagara | Realtime audio → geometry/material/camera | **YES – core** | Production (courses + SDKs) | Cymatic fabric / Sea Above audio-reactive terrain |

---

## 1) NMS Hierarchical Deterministic Generation — Superformula + Stacked Noise + Domain Warp

**What it is:** Hello Games' GDC-documented architecture: one master 64-bit seed deterministically branched into galaxy→system→planet→terrain→flora/fauna sub-seeds. Visual diversity from Johan Gielis' **Superformula** (generalized circle equation) + **L-systems** for flora + **fractal Brownian motion (fBm)** stacked Perlin/Simplex noise + **domain warping** + **image filtering** + **DEM blending**.

> `r(φ) = (|cos(mφ/4)/a|^n2 + |sin(mφ/4)/b|^n3|)^(-1/n1)` — Superformula param set `(a,b,m,n1,n2,n3)` spans diatoms→starfish→crystals with 6 numbers.

**Why bleeding-edge still:** Only shipped example of *coherent* infinite variation at this scale where every planet is bit-identical on any hardware from same seed. Reddit consensus: the pitfall is sameness-without-rules; NMS solved it with tag-driven cohesion (toothy fauna → predator behavior, steep terrain → rock biome).

**URLs:**
- Deep explainer (layered noise, warping, filtering, DEM, biome rules): https://dev.to/dubeykartikay/how-no-mans-sky-creates-18-quintillion-planets-with-just-math-3fgf
- Superformula biological basis (Rambus/Gielis/L-systems): https://www.rambus.com/blogs/the-algorithms-of-no-mans-sky-2/
- 10-year retrospective + 64-bit hierarchy: https://denvermobileappdeveloper.com/tech-news/no-mans-sky-celebrates-a-decade-of-galactic-wonder
- GDC talk notes filtered from reddit: https://www.reddit.com/r/NoMansSkyTheGame/comments/4xaisb/how_exactly_does_the_procedural_generation_work/ , https://www.reddit.com/r/NoMansSkyTheGame/comments/mq3egk/a_practical_look_at_procedural_generation_20_or/

**Melodia Integration – `NMS-Seed Universe HDA`:**
- Build `hda_nms_universe_seed` in Houdini: input `int64 world_seed` → VEX `rand(seed_derived)` per hierarchy level (mirror NMS branching via `pcg_hash`). Expose `planet_archetype` enum (barren/ocean/archipelago/void) = biome tag set.
- Reuse existing `melodia-copernicus-parallax` / `melodia-cymatic-fabric` seed contracts: terrain fBm → domain warp (CHOP-driven optionally) → biome rule filter = flora/fauna kitbash selector.
- Deterministic = **no storage**: Sea Above archipelago generates same islands on any machine; store only `seed + delta` for player edits (à la NMS base building = bidirectional proc-gen).
- Pair with World Partition (Approach 5) – far systems = impostor HLOD, near planets = streamed cells.

---

## 2) Houdini COPs / Copernicus Tiled Heightfield Terrain (Houdini 21–22)

**What it is:** SideFX moved Heightfield to **Copernicus (COPs)** as image layers. Terrain is now GPU-accelerated image ops: `HF Noise → HF Terrace → HF Erode → Strata → Mask→Material`. Tiling, stamps, and external heightmap I/O are native COP workflows. Houdini 22 talk: *Terrains in Copernicus* (Dmitrii Vlasenko).

**Why now:** Pre-COPs Heightfield was SOP-bound and memory-heavy. COPs unlock Gaea-style erosion at Gaea+ speeds *inside* Houdini with full PDG tiling and deterministic re-cooks. Existing Melodia Gaea→PCG path can be subsumed into a single Houdini graph.

**URLs:**
- SideFX What's New – Copernicus Terrain: https://www.sidefx.com/docs/houdini/news/22/copernicus.html#terrain
- Talk: H22 Terrains in Copernicus: https://www.sidefx.com/learn/talks/h22-terrains-in-copernicus/
- YouTube – Houdini 22 How to Create Terrains in COPs (Peter Arcara): https://www.youtube.com/watch?v=5v9lmJcIrIw
- Vlasenko "Call the COPs, my Terrain is Rocking Out!": https://www.youtube.com/watch?v=iFqZRY8lU4o
- Practical Gaea+Houdini solver pattern (erosion SOP + Heightfield Distort): https://lucastruchen.com/30-08-25-Terrain-Simulation-in-Houdini-and-Gaea-2

**Melodia Integration – `Copernicus Sea Above Graph`:**
- Replace one-shot Gaea heightmap import with `cop_terrain_sea_above.cop` → exports **tiled height + masks** (flow, slope, height) as 4K tiles (limit noted: Gaea node caps at 4096; COPs tiles bypass this).
- Solver SOP trick from lucastruchen: pipe heightfield through `Solver SOP` with `Heightfield Distort ($T*0.000001)` + `Gaea Erosion2` per frame → animated micro-erosion for "living sea above" without re-sim.
- Output masks directly feed Approach 5 PCG `Landscape Layer Sampler` + `Biome_Sample` attributes and `melodia-p0-sea-above-material` PBR.
- Keep Gaea as optional stamp source (`he_example_terrain_stamp.hda` texture input = COPs-compatible per Adrian Pan).

---

## 3) Massive Worlds Toolkit – Houdini-Centric World Partition Pipeline

**What it is:** Erwin Heyms' production framework (Patreon middleware) providing **bi-directional, lossless Houdini ↔ UE World Partition** with Edit Layer + Material Layer support, externalized data caches, RVT landscape material, road/bridge/tunnel toolkit, multi-landscape support, PDG task manager, and PCG spawner example.

**Why critical:** It's the only shipped bridge that makes Houdini the *authoritative* terrain source for World Partition without manual sublevels. Solves the "pulling hair out" World Partition stability issue cited on r/unrealengine (whole-map-must-be-loaded bug, 8K limit).

**URLs:**
- Official: https://ehoudiniacademy.com/massiveworlds/
- Licensing / Patreon (Invested Tier): http://patreon.com/ErwinHeyms

**Melodia Integration – `Sea Above World Partition Backbone`:**
- Adopt as Sea Above pipeline skeleton: Houdini HDAs own height + material layers → UE Edit Layers → PCG spawning → HLODs. Externalized caches keep memory manageable (matches `EMERGING_TOOLCHAIN_MASTER_INDEX` "external = say-so-don't-fake" rule).
- Use road/path HDAs for music-as-key puzzle networks (`Melodia.Water.Network.*` tags) and props spawner for biomes (replaces hand-placed kitbash).
- Validate on non-commercial tier first; budget commercial source-access if Sea Above becomes shipping pillar.

---

## 4) Adrian Pan HoudiniEngineForUnreal — 2–15× Faster Rebuild with Native WP + COPs

**What it is:** Complete rewrite of SideFX Houdini Engine for UE from zero. Headline deltas vs official: **2–15× faster I/O**, **native World Partition + packaging support** (no bake / no actor deletion, `i@unreal_split_actors=1` + `s@unreal_split_attr` → OFPA), **COPernicus texture I/O**, **Megaplants/InstancedSkinnedMeshComponent** (UE 5.6+), **custom C++ I/O translators** for PCG/Mass, lightweight Blueprint API, PDG support.

**URLs:**
- Repo + docs: https://github.com/AdrianPanGithub/HoudiniEngineForUnreal
- PCG translator example: https://github.com/AdrianPanGithub/HoudiniPCGTranslator
- Mass translator: https://github.com/AdrianPanGithub/HoudiniMassTranslator
- Demo reels – City: https://youtu.be/5Vp5nAFq1X8 , Terrain: https://youtu.be/19gIzQGnSaU

**Melodia Integration – `Performance Unlock`:**
- Drop-in replacement for official HE plugin (not compatible side-by-side). Benchmark on `L_KaleidoNave` / `LV_SeaAbove_Prototype`: measure cook I/O wall time before/after.
- Use `unreal_split_actors` to make every Houdini-generated island/props actor a standalone OFPA file → World Partition streaming *and* source-control friendly (no sublevel conflicts).
- Wire `HoudiniPCGTranslator` so Houdini point clouds → UE **PCG data** directly (feeds Approach 5 graphs without intermediate mesh).
- Leverage `HoudiniMassTranslator` for crowd/biome mass scattering if Sea Above needs fauna.

---

## 5) UE 5.6/5.7 PCG Hierarchical Generation + Partitioned Volumes (+ FastGeo)

**What it is:** PCG graduated from Experimental to Production-Ready in UE 5.7 (~2× faster, GPU acceleration, Editor Mode, deterministic ordering). Key pattern: **hierarchical generation** across `HiGenGridSize` levels:
- L0 coarse (51.2m): biome placement → outputs biome attribute/spline
- L1 medium (25.6m): landmarks/villages → feature output
- L2 fine (12.8m = WP cell): dressing (trees/rocks/grass) → HISM spawns
PCG Volumes set `Generation Grid Size = World Partition cell size`; cells stream → graph evaluates per-cell. **Bake vs Runtime** is the central tradeoff; default to **bake-time** unless runtime variation needed. New **FastGeo** backend (UE 5.6+) replaces mesh ops with pooled memory (2–4× faster).

**URLs:**
- Production patterns (hierarchical, streaming cost, bake vs runtime, WW+Data Partition): https://www.strayspark.studio/blog/procedural-content-generation-pcg-framework-production-ue5-7
- Migration guide (FastGeo, GPU, WP integration): https://www.strayspark.studio/blog/ue-57-pcg-framework-production-ready-migration-guide
- World Partition + Data Layers + Procedural Scatter (ownership problem): https://www.strayspark.studio/blog/world-partition-data-layers-procedural-scatter-ue57
- Large worlds guide (OFPA, HLOD, scatter): https://www.strayspark.studio/blog/ue5-landscape-world-partition-massive-open-worlds
- Epic issues – hierarchical runtime cost + partition grid fixups: https://forums.unrealengine.com/t/runtime-cost-in-pcg-hierarchical-generation/2708776 , https://forums.unrealengine.com/t/pcg-biomes-v2-partitioning-for-local-biome-graphs/2680350
- UE docs (PCG WP): https://dev.epicgames.com/documentation/unreal-engine/using-pcg-with-world-partition-in-unreal-engine

**Melodia Integration – `Sea Above PCG Dress Stack`:**
- Build 3-tier graph chain for Sea Above:
  ```
  Biome Graph (coarse, 4× WP cell) — samples COPs biome masks (Approach 2) → tags cells ocean/reef/floating-isle
    → Feature Graph (2× cell) — places temples/ruins/kitbash landmarks (distance-from-feature attribute)
      → Dress Graph (1× cell) — HISM foliage/rocks/shards, slope/altitude/distance branching + surface orient + jitter
  ```
- Set `bIsSpatiallyLoaded` partitioning on PCG Volumes, `pcg.cache.enabled` tuned, `MaxPercentageOfExecutingThreads=1.0` for async.
- **FastGeo interop** (`pcg.FastGeo`) for mesh sampling; pre-bake hot-path cells (near spawn / travel routes), leave distant cells runtime-generated.
- Rule: per-cell graph <50ms (profile via `stat pcg`), HISM not actors, Nanite where possible, HLOD for distant cells.

---

## 6) CD Projekt Red + Epic Fast Geometry Streaming / TurboEntities (Witcher 4 Tech Demo)

**What it is:** Co-developed for Witcher 4's "infinite forest" on UE 5.6: **95% of world geometry bypasses Actors/Components**. Lightweight `TurboEntity` (POCO struct) manages `RenderProxy` + `PhysicsProxy`; streaming runs on **worker threads** via Entity Jobs system. Companion plugin **`FastGeo Streaming`** (engine plugin, experimental) decouples streaming from game thread. Also: **Nanite Foliage** (voxelized HLOD blending) + vertical World Partition.

**Why bleeding-edge:** Solves UE's #1 open-world hitch – World Partition cell load spawning 100s of actors on game thread. Measured at 60fps on base PS5 with dense foliage covering 95% screen. This is the ceiling-breaker that makes NMS-scale *playable*.

**URLs:**
- Jarosław Rudzki (Epic/CDPR) breakdown + FastGeo plugin: https://www.linkedin.com/posts/jaroslaw-rudzki_streaming-improvements-for-dense-worlds-in-activity-7359633880082972672-IuZi
- Witcher 4 infinite forest / FastGeo + Nanite Foliage explainer: https://www.creativebloq.com/3d/video-game-design/how-the-witcher-4s-infinite-forest-is-being-built-one-branch-at-a-time-using-unreal-engine-5-6
- Fast Geo Streaming plugin news: https://en.gamegpu.com/news/igry/cd-projekt-red-i-epic-games-razrabotali-plagin-fast-geo-streaming-dlya-ustraneniya-statterov-v-unreal-engine-5-6
- UE forum – best practices procedural gen + WP (CDPR talk cited, staggered spawn, pre-gen vs runtime): https://forums.unrealengine.com/t/best-practices-for-procedural-world-generation-with-world-partition/2454743

**Melodia Integration – `NMS-Scale Streaming Experiment`:**
- Enable `FastGeo` plugin in a **branch** build of `BS_GodFile` on UE 5.6 preview (not main). Feed procedurally generated proxies (from Approach 4 HDAs) into TurboEntity pipeline instead of disk streaming – *generate* TurboEntities on demand from seed (forum suggests overriding interfaces to do this).
- Nanite Foliage for Sea Above kelp/forest canopy – modular instanced parts with voxel HLOD, no pop-in.
- Metrics to watch: `wp.Runtime.MaxStreamingCellsPerFrame`, `wp.Runtime.MaxActorsToSpawnPerFrame`, `wp.Runtime.MemoryBudgetMB`; validate no visible HLOD switch, no memory fragmentation.
- **Risk:** Experimental; keep behind `WorldPartition_Turbo` data layer toggle, do not block main.

---

## 7) Audio-Reactive Pipelines — Houdini CHOPs → TouchDesigner → UE Niagara/OSC

**What it is:** Two complementary stacks that together cover **offline Houdini** + **realtime performance**:
- **Houdini CHOPs** (Channel Operators): import audio → `Audio Spectrum CHOP` (FFT) → `Analyze`/`Filter`/`Math`/`Trigger` CHOPs → drive SOP params (displacement, particle emission, material, camera) via `chopnet` SOP + channel exports. Full 15-part masterclass exists (Houdini Harmonies).
- **TouchDesigner ↔ UE bridge**: TD's `Audio File In` + `Audio Spectrum` + `Analyze (Maximum)` + `Math (Average)` → texture/data → **Spout** → UE `Spout Receiver` + `Niagara Module Scripts` sampling pixel data → point cloud params (position/scale/color). OSC alternative for parameter driving (Blueprint `OSC Server` on `BeginPlay`, bind delegate, store ref to avoid GC).

**URLs:**
- Houdini CHOPs reference: https://www.sidefx.com/docs/houdini/nodes/chop/index.html
- Audio Driven Animation (CHOPs→SOPs, 18m beginner): https://www.sidefx.com/tutorials/audio-driven-animation-chops/
- Houdini Harmonies – Audio-Reactive 3D Art (15-part CHOPs/SOPs/Solaris course, 4.9★): https://www.graphicinmotion.com/houdini-course-audio-reactive-music-visualization/ + https://www.udemy.com/course/houdini-harmonies-creating-audio-reactive-3d-art/
- Takeru CHOPs deep-dive (why CHOPs click): https://tokeru.com/cgwiki/HoudiniChops.html
- TouchDesigner Audio Reactive Eye (Analog-look, Trim→Analyze→Math pipeline): https://interactiveimmersive.io/blog/touchdesigner-resources/audio-reactive-drawn-content-in-touchdesigner
- Audio-Reactive Point Clouds UE5 + TouchDesigner capstone (Spout → Niagara): https://pro.interactiveimmersive.io/courses/audio-reactive-point-clouds-with-ue5-touchdesigner/lessons/04-installing-soundviz
- TD ↔ UE5 Integration guide (OSC, NDI, Spout, embedding): https://medium.com/@Jamesroha/touchdesigner-and-unreal-engine-5-integration-ebb5b12d0609
- TD audio-reactive MCP `create_audio_reactive` (spectrum+level+beat → GLSL visual): https://glama.ai/mcp/servers/lucasmaher-hash/touch-designer-mcp/tools/create_audio_reactive

**Melodia Integration – `Cymatic Fabric Engine` (extends present `audio-reactive writer`):**
- **Offline** (HDA cooking): CHOP network in `hda_cymatic_terrain`: `File In CHOP → Spectrum (FFT 16K) → Trim (kick vs shimmer bands) → Analyze (Maximum) → Math (remap 1.2–1.6) → Filter (0.38)` → drives `Heightfield Distort` amplitude, `Copy-to-Points` scale, and Copernicus material emission. This already exists in prototype – formalize as reusable `onxx`-driven blueprint per `EMERGING_TOOLCHAIN_MASTER_INDEX` "audio-reactive writer" entry.
- **Runtime** (rhythm-JRPG loop): TD or in-engine `Audio Analyzer` (MetaSound) → OSC/Spout → UE `UMelodiaNarrativeSubsystem` / Niagara: beat triggers highway note spawning, cymatic fabric displacement, and `music_world_key` puzzle resonance. Reuse `melodia-cymatic-fabric` PBR maps but make them **spectrum textures** sampled in Niagara Module Scripts.
- Keep `music_world_key` gate logic: audio → `FGameplayTag` (`Melodia.Rhythm.*`) → piano-to-narrative allowlist check. Do not add second audio authority.

#### Bonus reference – GPGPU Planet Generators (prototyping sandboxes)

For rapid R&D before Houdini commit, these WebGL GPU-driven generators are useful reference impls for layered noise → skirts → LOD:

- **XenoverseUp procedural-planets** (Three.js, multilayered Simplex, GPGPU, .obj export, fork of Seb Lague): https://github.com/XenoverseUp/procedural-planets — Article: https://medium.com/fractions/gpgpu-on-the-web-procedural-planet-meshes-0601b044c818?sk=529caf4fffdb74a381b4f53dc7495d00 — Live: https://procedural-planets.vercel.app/
- **barrulus/proceduralterrains** (React+Vite+Three.js, deterministic mulberry32 seed, codegen'd layered noise, tile/infinite/planet modes, GLB/heightmap/splat export): https://github.com/barrulus/proceduralterrains — Live: https://terrains.zyfod.dev/

*Use as shader-codegen reference for `NoiseStack.js → noiseStackCodegen.js → terrainGLSL.js` pattern; port the deterministic `(worldXZ, seed, params) → height/normal/biome` pure function to HDA VEX.*

---

## Recommended Melodia Roadmap (3 Phases)

**Phase A – Immediate (no engine fork):** Approaches 2 + 4 + 5
- Convert Sea Above Gaea export to **COPs tiled graph** (Approach 2) → feed **HE4UE rebuild** (Approach 4, `unreal_split_actors`) → dress with **PCG hierarchical graphs** (Approach 5, bake-time). This trio is non-destructive, OFPA-clean, and reversible.

**Phase B – NMS Universe Prototype (HDA R&D):** Approaches 1 + 7
- Build `hda_nms_seed` (Approach 1) as parameter master for Phase A graphs. Add **CHOP audio warp** (Approach 7 offline) as optional domain warp input. Validate 4 archetype planets in isolation level `LV_SeaAbove_Prototype`.

**Phase C – Scale Ceiling Break (UE 5.6 branch):** Approach 6
- Fork UE 5.6 preview + **FastGeo** plugin, wire Houdini-generated TurboEntities. Target: stream 16 km² Sea Above with 95% off-thread geometry, profile vs Phase A baseline. Ship only if hitch reduction >50% and no HLOD regression.

---

## Reddit / Community Sentiment (selected)

- **NMS template vs random:** r/NoMansSkyTheGame consistently clarifies NMS is *not* random – it's **template-based proc-gen** ("reverse ML" – limited archetypes × many permutations). Risk is perceived sameness; solution is strong biome tags + hand-authored outliers. — https://www.reddit.com/r/NoMansSkyTheGame/comments/mq3egk/a_practical_look_at_procedural_generation_20_or/
- **World Partition pain:** r/unrealengine warns WP is ironically *unstable for large maps* if not used from day one; 8K cap, whole-map-must-be-loaded material bug. Mitigate by starting with WP enabled + OFPA from day zero (Approaches 3/4/5 address this). — https://www.reddit.com/r/unrealengine/comments/1afja4t/creating_actually_good_looking_terrains_in_ue5/
- **PCG runtime cost surprise:** UE forum reports `FPCGGraphExecutor::PrepareForExecute` + CRC dominate even with precomputed point clouds; fix is cache toggles + `Set Grid Size` node + `pcg.cache.*` – bake hot cells. — https://forums.unrealengine.com/t/runtime-cost-in-pcg-hierarchical-generation/2708776

---

*Sources verified 2026-09-02. All GH repos, SideFX docs, and forum threads fetched head+tail; full pages cached under `C:\Users\froma\AppData\Local\hermes\cache\web\`.*
