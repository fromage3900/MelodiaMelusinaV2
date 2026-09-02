# Emerging 3D Toolchain — Trench Sweep V

**Date:** 2026-08-31  
**Project:** Melodia Melusina / UE5.8  
**Focus:** native UE5.8 systems that materially change whether external worldbuilding tools are worth adopting  
**Status:** deep R&D annex; experimental systems remain isolated  
**Related:** `EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_04_2026-08-31.md`, `MELODIA_TOOLCHAIN_DATA_CONTRACT_2026-08-31.md`, Issue #36, PR #37

> A third-party tool does not compete against Unreal 5.5 in this project. It competes against the actual UE5.8 editor and PCG stack Melodia is running now.

---

# Executive findings

This pass found a second major correction to the super-pipeline:

1. **Dash has a much harder native baseline than the original plan assumed.** UE5.8 PCG now supports non-destructive Manual Editing, Data Overrides, PCG Editor Mode painting/splines/surfaces/volumes, level graphs, editor-selection/camera queries, actor transforms, Python data processing and custom tool presets. Dash must beat that, not basic hand placement.
2. **PCG Biome Core is strategically more relevant than PVE for Melodia's existing SpeedTree world.** It already expresses local/global biomes, priorities, blending, runtime hierarchical generation and GPU scattering around the camera. This maps directly onto the semantic-field/world-compiler architecture.
3. **Nanite Foliage / Nanite Assemblies is the most important new SpeedTree-adjacent R&D lane found so far.** It is experimental, but its architecture attacks exactly the foliage disk/streaming/WPO limits that matter for a high-density world.
4. **The correct Nanite-Foliage question is not “replace SpeedTree.”** SpeedTree remains botanical authoring. The question is whether a SpeedTree-derived hero plant can be transformed into an Unreal Nanite Assembly / skeletal-wind representation without destroying iteration speed or art direction.
5. **World Streaming Insights should become part of the R&D measurement harness.** UE5.8 can now visualize World Partition cell state, priority and estimated memory over time inside Unreal Insights.
6. **Fast Geometry Streaming is a new WATCH candidate for heavy procedural/static world slices.** It converts partitioned-world geometry to optimize streaming, but remains Experimental and has enough historical stability fixes that it should only be tested after a world slice exists.
7. **FluidNinja, VectorayGen, LiquiGen and EmberGen now need stronger native comparators.** UE5.8 already has Niagara Fluids, Grid 2D/3D simulation, Vector Field data interfaces, Niagara Data Channels and improved fluid solvers. External tools must demonstrate either authoring-speed or cross-system-coherence wins.
8. **VectorayGen deserves a cheap micro-spike because it is free again.** Its scope is narrow enough to test without creating another paid-tool commitment.

---

# 1. UE5.8 PCG Manual Editing changes the Dash decision

Primary Epic sources:

- UE5.8 release notes: https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes
- PCG Editor Mode: https://dev.epicgames.com/documentation/unreal-engine/pcg-editor-mode-in-unreal-engine
- PCG overview: https://dev.epicgames.com/documentation/unreal-engine/procedural-content-generation-overview

UE5.8 adds non-destructive Manual Editing of generated PCG data/artifacts through:

- selection;
- exclusion;
- modification;
- restore;
- node-level Manual Edit marking;
- temporary overrides;
- Data Overrides inspection.

PCG Editor Mode can create custom artist-facing tools around:

```text
SplineTool
SplineSurfaceTool
PaintTool
VolumeTool
```

Each tool can expose graph parameters and can write into separate data instances/layers.

## Why this matters for Melodia

The original pipeline had a clean conceptual division:

```text
Houdini = systemic generation
PCG     = scalable distribution
Dash    = final human composition
```

UE5.8 now blurs the second and third line.

A better native architecture may be:

```text
Houdini semantic fields
    -> UE PCG systemic distribution
    -> PCG Manual Editing / Editor Mode artist overrides
    -> optional Dash only for operations native PCG still makes painful
```

### Revised Dash adoption gate

Dash no longer passes merely by beating ordinary drag-and-drop placement.

It must beat a 20-minute native UE5.8 pass using:

- PCG Manual Editing;
- Data Overrides;
- PCG Editor Mode tools/presets;
- normal editor transform tools.

If native PCG overrides preserve procedural provenance and reach similar visual quality, Dash becomes a narrower optional convenience layer.

---

# 2. Invent a Melodia PCG Artist Tool shelf before buying more dressing software

The PCG Editor Mode is extensible enough to justify a Melodia-specific authoring layer.

Candidate tool presets:

```text
P3_FilterFlow_Brush
P3_EcologyBias_Spline
P2_MoltSuccession_Brush
P2_ExclusionScar_Paint
P1_TensionFiber_Spline
Monolith_Proximity_Volume
HeroDebris_Composition_Paint
SpeedTree_Override_Paint
```

Each tool should write canonical fields from `melodia.semantic-fields.v1`, rather than inventing local attributes.

Example:

```text
P3_FilterFlow_Brush
    writes:
      melodia_filter_flow_strength
      melodia_filter_flow_dir_ws

P3_EcologyBias_Spline
    consumes:
      melodia_filter_flow_strength
      melodia_wind_exposure
    writes:
      melodia_ecological_density
```

## Why this is strategically strong

It lets Melodia keep the **world meaning** in its own schema while giving the environment artist a direct paint/spline workflow inside Unreal.

This is closer to inventing a project-specific world-authoring language than collecting another scattering plugin.

---

# 3. PCG Biome Core may be the missing UE-side ecosystem compiler

Primary Epic sources:

- Overview: https://dev.epicgames.com/documentation/unreal-engine/procedural-content-generation-pcg-biome-core-and-sample-plugins-overview-guide-in-unreal-engine
- Reference: https://dev.epicgames.com/documentation/unreal-engine/procedural-content-generation-pcg-biome-core-and-sample-plugins-reference-guide-in-unreal-engine
- Quick Start: https://dev.epicgames.com/documentation/unreal-engine/procedural-content-generation-pcg-biome-core-and-sample-plugins-quick-start-guide-in-unreal-engine

PCG Biome Core is Experimental, but its architecture is unusually aligned with Melodia:

- local biome generation;
- global biome merge/difference;
- biome and generator priorities;
- biome blending;
- asset mapping via data assets;
- output serialized for other PCG graphs;
- runtime hierarchical generation;
- GPU runtime ground scattering;
- point influences that attract/repulse density;
- mesh scattering over pre-generated world forms.

## Melodia mapping

```text
Houdini
  authors macro fields / masks / terrain anatomy

Biome Core local actors
  encode chapter/ecology regions

Biome Core global
  resolves overlapping ecological truths by priority

Biome Core Runtime
  generates dense local detail around player on GPU

SpeedTree
  remains source of botanical assets
```

### Potential mapping to canonical fields

```text
Biome priority      <- authored chapter/ecology rule
Influence points    <- melodia_monolith_proximity / filter-flow sources
Density weighting   <- melodia_ecological_density
Filter graph        <- moisture / molt-age / wind-exposure tests
Runtime asset layer <- grass / petals / small stems / loose ecological evidence
```

### Important boundary

Do not fork the project onto Epic's sample graphs wholesale.

The spike should mine Biome Core for architecture and nodes, then decide whether:

1. Melodia should directly use the plugin;
2. Melodia should adapt a minimal subset into project PCG graphs;
3. the existing world compiler already solves the problem better.

---

# 4. Nanite Foliage / Assemblies — the major SpeedTree-adjacent discovery

Primary Epic sources:

- Nanite Foliage: https://dev.epicgames.com/documentation/unreal-engine/nanite-foliage
- Nanite Assemblies: https://dev.epicgames.com/documentation/unreal-engine/nanite-assemblies
- Nanite-enabled content: https://dev.epicgames.com/documentation/unreal-engine/working-with-naniteenabled-content
- SpeedTree UE support: https://dev.epicgames.com/documentation/unreal-engine/using-speedtree-in-unreal-engine

Nanite Foliage is Experimental in UE5.8 and is composed of:

- Nanite Assemblies;
- Nanite Voxels;
- Nanite Skinning;
- optional Experimental Dynamic Wind.

The key idea is to stop treating a dense tree as one giant duplicated mesh or traditional masked-card/WPO object.

Nanite Assemblies micro-instance repeated branch/frond parts inside one asset. Epic's demonstration shows extremely large disk/streaming reductions on its own test tree, but those numbers are **not assumed to transfer to Melodia**.

Nanite Skinning replaces much WPO-style foliage motion with skeletal motion so bounds and rasterization can be handled more efficiently.

## Critical SpeedTree boundary

Unreal's normal SpeedTree `.st9` importer remains a separate, established path.

No primary documentation found in this sweep says that importing a SpeedTree asset automatically converts it into a UE5.8 Nanite Foliage skeletal assembly.

Therefore the proposed lane is explicitly experimental:

```text
SpeedTree botanical source
    -> geometry/skeleton/part decomposition experiment
    -> Houdini/USD or Unreal assembly builder
    -> Nanite Assembly / optional skeletal wind
    -> UE benchmark
```

SpeedTree remains the authoring truth even if the **shipping representation** later changes.

## Why this could matter enormously

Melodia's desired forests are not generic card forests. They want:

- large, readable silhouettes;
- hero leaves and flowers;
- close inspection;
- high density;
- huge vistas;
- rhythm/Monolith response;
- less obvious billboard/LOD collapse.

That is exactly the problem Nanite Foliage is being designed to attack.

## But current limitations matter

Dynamic Wind is Experimental and currently documents:

- global wind direction only;
- no player/object collision;
- required skeletal data import;
- additional setup burden.

Nanite Assemblies also currently support only one layer of assembly instancing and have skeletal-part animation limitations.

So this is **R&D WATCH / HIGH-VALUE CANARY**, not a chapter migration.

---

# 5. Concrete Nanite Foliage benchmark

**Map:** `LV_RND_SpeedTree_NaniteFoliage_Canary`

Use one existing project-owned SpeedTree whose silhouette and wind are already approved.

Create three lanes:

### Lane A — production baseline

Current SpeedTree import/material/wind path.

### Lane B — standard Nanite geometry foliage

A geometry-rich variant using normal Nanite guidance where feasible:

- geometry leaves instead of broad masked cards where available;
- Preserve Area;
- bounded WPO;
- same cameras and density.

### Lane C — experimental Nanite Foliage representation

Attempt a part-based Nanite Assembly and skeletal wind representation using only project-owned source data.

If the conversion path becomes a research project by itself, stop after documenting the blockage.

### Metrics

```text
source asset authoring minutes
conversion/setup minutes
uasset disk size
streaming memory
GPU frame time
VSM cost
shader/material cost
wind cost
visual canopy retention at distance
close-leaf quality
package result
fallback behavior
iteration pain after one botanical edit
```

### Promotion gate

Do not promote Lane C unless it wins on **both**:

1. runtime/storage quality;
2. re-authoring/iteration practicality.

A representation that is 5x cheaper but takes half a day to rebuild every tree after a SpeedTree edit is not production-ready for Melodia.

---

# 6. World Streaming Insights should become evidence infrastructure

Primary Epic sources:

- UE5.8 release notes: https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes
- World Partition overview: https://dev.epicgames.com/documentation/unreal-engine/world-partition-in-unreal-engine
- HLOD: https://dev.epicgames.com/documentation/unreal-engine/world-partition---hierarchical-level-of-detail-in-unreal-engine

UE5.8 introduces Experimental World Streaming Insights inside Unreal Insights.

It can analyze World Partition cells over time and display:

- cell state;
- priority;
- estimated total/unique/shared package memory;
- streaming source timelines;
- spatial position over a minimap;
- links into Memory Profiler.

There is also a command to export the current World Partition minimap and world-bounds sidecar for the spatial profiler.

## Melodia use

This should not be another “tool to evaluate.”

It should become a **measurement harness** for any test that changes:

- foliage density;
- HLODs;
- world partition layout;
- Mesh Terrain;
- FastGeo;
- PCG runtime generation;
- chapter streaming footprint.

### Required capture for chapter-shaped R&D

```text
trace = WorldStreaming
+ optional priority/dependency traces
fixed player route
fixed camera/FPS settings
minimap background
streaming state capture
memory capture
```

Store a small JSON/Markdown summary in Git; do not commit massive trace files by default.

---

# 7. Fast Geometry Streaming — WATCH as a runtime representation optimizer

Primary Epic sources:

- UE5.8 release notes: https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes
- Plugin API index: https://dev.epicgames.com/documentation/unreal-engine/API/PluginIndex/FastGeoStreaming

Fast Geometry Streaming is Experimental and described as extracting/converting partitioned-world geometry to optimize world streaming performance.

UE5.8 added/fixed support around:

- decals;
- multiple light component types;
- mesh paint textures;
- physics ownership/resolution;
- instance transforms;
- threading/deadlock/crash cases.

## Why Melodia might care

Procedural tools can create worlds that are visually beautiful but structurally expensive because they leave thousands of actor/component objects behind.

FastGeo may eventually be useful as a **post-authoring runtime representation**:

```text
Houdini / PCG / Dash / artist-authored actors
    -> normal editable world
    -> FastGeo conversion for runtime cells
```

This is conceptually attractive because authoring and shipping representation can differ.

## Current status

WATCH only.

The volume of stability fixes is itself evidence that this is not a foundation to design around yet.

Run a canary only after a real world slice exhibits measurable actor/streaming overhead.

---

# 8. Native Niagara baselines make the environmental-field tests harder

Primary Epic sources:

- Niagara Fluids: https://dev.epicgames.com/documentation/unreal-engine/niagara-fluids-in-unreal-engine
- Fluid simulation overview: https://dev.epicgames.com/documentation/unreal-engine/fluid-simulation-in-unreal-engine---overview
- Niagara Data Channels: https://dev.epicgames.com/documentation/unreal-engine/data-channels-in-niagara-for-unreal-engine

UE5.8's native Niagara stack already includes:

- Grid2D/Grid3D simulation data;
- Simulation Stages;
- 2D FLIP;
- Shallow Water;
- 3D FLIP;
- vector-field data interfaces;
- Niagara Data Channels for shared communication;
- a newer particle-neighbor query interface;
- pressure-solver updates.

### Revised external-tool doctrine

**FluidNinja LIVE-2** must beat native Niagara at coherent player-local multi-surface field interaction.

**LiquiGen** must beat native Niagara primarily as a liquid **ideation/export accelerator**, not by merely being capable of liquid simulation.

**EmberGen** must beat native Niagara on volumetric iteration/bake quality per minute.

**VectorayGen** must beat both Houdini and a simple Unreal vector-field workflow on vector-field authoring speed.

---

# 9. VectorayGen — promote from buried candidate to cheap immediate micro-spike

Primary source:

- https://jangafx.com/software/vectoraygen

JangaFX currently offers VectorayGen as a free download. It is narrowly focused on real-time vector-field generation and can create object-driven flows, mathematical fields, noise and turbulence.

Because it is free and narrow, the switching cost is low enough to justify a short test.

### Benchmark

**Asset:** `P3_FilterFlow_VectorField_A`

Build the same field three ways:

1. VectorayGen;
2. Houdini volume/vector field;
3. native UE approximation.

### Timebox

20 minutes per lane after installation/setup.

### Score

- time to intended motion;
- obstacle/object-flow quality;
- artistic control;
- export/import friction;
- coordinate-system correctness;
- reproducibility;
- runtime data size;
- whether semantic field direction can remain authoritative outside the tool.

### Decision

Even if VectorayGen wins, it is a **field sketchbook**, not the canonical owner of `melodia_filter_flow_dir_ws`.

---

# 10. Revised worldbuilding stack hypothesis

The new most coherent architecture is now:

```text
SpeedTree
  authored botany
       |
Houdini 22
  world geometry + macro semantic fields
       |
       +--> Copernicus: textures/masks
       |
       v
UE5.8 PCG / Biome Core
  biome resolution + distribution + runtime detail
       |
       +--> PCG Editor Mode / Manual Editing
       |      project-specific artist override language
       |
       +--> Niagara / Data Channels
       |      transient ecological/field evidence
       |
       +--> optional Dash
       |      only for operations that still beat native tools
       |
       v
World Partition / HLOD
       |
       +--> World Streaming Insights evidence
       |
       +--> future FastGeo post-authoring optimization
       |
       v
shipping world
```

Nanite Foliage sits beside this as a possible future **shipping representation** for selected SpeedTree-derived ecology, not as botanical authoring authority.

---

# 11. Priority changes caused by this sweep

| System | Previous stance | New stance |
| --- | --- | --- |
| Dash | Tier B test | Tier B, but must beat PCG Manual Editing / Editor Mode baseline |
| PCG Editor Mode | under-emphasized | HIGH-PRIORITY native authoring spike |
| PCG Manual Editing | under-emphasized | HIGH-PRIORITY native authoring spike |
| PCG Biome Core | background/native | HIGH-PRIORITY architecture evaluation |
| Nanite Foliage | mostly absent | HIGH-VALUE R&D canary, SpeedTree-adjacent |
| World Streaming Insights | absent | adopt as R&D measurement harness |
| FastGeo | absent | WATCH; runtime representation experiment only |
| VectorayGen | buried Tier A | cheap 60-minute micro-spike |
| FluidNinja | Tier S candidate | still high-interest, but must beat stronger native Niagara baseline |

---

# 12. Concrete next actions

- [ ] Build `LV_RND_P3_PCGArtistTools` with one PaintTool and one SplineTool using canonical semantic fields.
- [ ] Run PCG Manual Edit baseline before Dash comparison.
- [ ] Inspect PCG Biome Core in a disposable map and map its priority/blending model to `melodia.semantic-fields.v1`.
- [ ] Build a tiny Biome Core runtime test using project-owned SpeedTree/static assets; do not import sample assets into production.
- [ ] Create `LV_RND_SpeedTree_NaniteFoliage_Canary` and record baseline storage/perf before attempting assembly conversion.
- [ ] Enable World Streaming Insights only in an isolated performance/debug configuration and define the fixed benchmark route.
- [ ] Add VectorayGen micro-spike to the P3 field benchmark.
- [ ] Compare FluidNinja against Niagara Grid/Simulation Stage/Data Channel baseline before any runtime adoption.
- [ ] Leave FastGeo off until a real world slice demonstrates streaming/actor overhead worth optimizing.

---

# Final doctrine

The deeper we go, the less the best answer looks like “install another program.”

UE5.8 itself has crossed a threshold where Melodia can build a **project-specific procedural art language inside the editor**: Houdini supplies deep authored truth, PCG supplies scalable world logic, Manual Editing supplies intentional human exceptions, and semantic fields keep all of them speaking the same language.

The external tools now have to beat that architecture rather than merely look impressive in isolation.