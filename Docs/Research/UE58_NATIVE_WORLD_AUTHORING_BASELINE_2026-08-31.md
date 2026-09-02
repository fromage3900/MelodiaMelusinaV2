# UE5.8 Native World Authoring Baseline — Melodia R&D Plan

**Date:** 2026-08-31  
**Project:** Melodia Melusina  
**Engine:** Unreal Engine 5.8  
**Status:** executable R&D baseline before adopting additional worldbuilding dependencies  
**Companions:**
- `EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_05_2026-08-31.md`
- `MELODIA_TOOLCHAIN_DATA_CONTRACT_2026-08-31.md`
- `DASH_ENVIRONMENT_DRESSING_SPIKE_2026-08-31.md`

> External worldbuilding software only passes if it beats the best native UE5.8 workflow Melodia can reasonably build.

---

# 1. Why this baseline exists

UE5.8 materially changes the comparison landscape for environment tooling.

The project can now combine:

```text
Houdini authored macro truth
        ↓
UE PCG systemic distribution
        ↓
PCG Manual Editing / Data Overrides
        ↓
PCG Editor Mode artist tools
        ↓
Biome Core / runtime local detail where useful
        ↓
Niagara / Data Channels / materials
        ↓
World Partition / HLOD
        ↓
shipping world
```

If Melodia does not benchmark this native stack first, it risks adopting plugins to solve problems the current engine already solves while fragmenting procedural ownership.

This document creates the native control group for Dash, FluidNinja, VectorayGen, terrain/biome plugins and future environment tools.

---

# 2. Benchmark doctrine

Every native test must use a **real Melodia-shaped problem** and produce evidence that an external tool can later be compared against.

Required metrics:

```text
setup_minutes
hands_on_minutes
iteration_minutes_after_change
visual_quality_score
runtime_gpu_ms where relevant
runtime_cpu_ms where relevant
streaming_memory where relevant
source_control_diff
runtime_dependency_count
reproducibility
package_result
artist_override_preservation
```

The goal is not “prove native Unreal wins.”

The goal is to create a fair baseline strong enough that any added dependency has to earn its place.

---

# 3. Test 01 — P3 native artist-override baseline

**Question:** Can UE5.8 PCG Manual Editing + Data Overrides solve the final-composition bottleneck well enough that Dash is optional?

**Map:** `LV_RND_P3_PCGManualEdit`

**Timebox:** 60 minutes total.

### Build

Start from one generated SpeedTree/PCG ecology strip containing:

- trees/shrubs;
- low vegetation;
- rocks/debris;
- one focal travel corridor;
- a deterministic P3 filter-flow field.

Canonical fields:

```text
melodia_filter_flow_strength
melodia_filter_flow_dir_ws
melodia_wind_exposure
melodia_ecological_density
melodia_monolith_proximity
```

### Pass A — untouched procedural scene

Capture fixed cameras.

### Pass B — 20-minute native artist pass

Use:

- Manual Editing;
- selection/exclusion/modify/restore;
- Data Overrides;
- normal transforms where necessary.

Do not rewrite the generating graph during the 20-minute pass.

### Measure

- how many ugly procedural placements are fixed;
- whether changes survive recook/reopen as intended;
- how legible the filter-flow direction becomes;
- source-control shape;
- whether the artist can see what is procedural vs manually overridden.

### Output

This becomes the native comparator for the Dash spike.

---

# 4. Test 02 — Melodia PCG Artist Tool prototype

**Question:** Can Melodia build a small project-owned world-authoring language in PCG Editor Mode instead of accumulating specialized placement plugins?

**Map:** `LV_RND_P3_PCGArtistTools`

**Timebox:** 90 minutes.

### Minimum tools

Build only two:

## A. `P3_FilterFlow_Brush`

Input gesture: paint/volume according to whichever PCG Editor Mode pattern is fastest to scaffold.

Writes or influences:

```text
melodia_filter_flow_strength
```

A direction source may be supplied globally or by the spline tool below.

## B. `P3_FilterFlow_Spline`

Writes/derives:

```text
melodia_filter_flow_dir_ws
melodia_filter_flow_strength
```

Consumers:

- PCG density/orientation;
- Niagara evidence;
- material distortion/grass response;
- later Biome Core filtering.

### Pass condition

Within 90 minutes, an artist can create or edit one visible impossible current without opening Houdini or changing C++.

### Park condition

PCG Editor Mode setup overhead is so high that a project tool requires substantial engineering before one field can be authored.

### Commit

- tool graph/preset definitions if source-control compatible;
- field mapping;
- screenshots;
- result metrics;
- no production-map migration.

---

# 5. Test 03 — PCG Biome Core as UE-side ecosystem compiler

**Question:** Does Biome Core make overlapping ecological rules and runtime detail significantly easier than existing project PCG graphs?

**Map:** `LV_RND_P3_BiomeCore`

**Timebox:** 120 minutes maximum.

### Use project-owned assets only

Do not make Epic sample assets part of the benchmark result.

Use a small selection of existing SpeedTree/static ecology assets.

### Required biome conditions

Create three regions:

```text
Normal Ecology
Filter-Flow Biased Ecology
Monolith Near-Field Ecology
```

Overlap at least two regions so priority/blending behavior is visible.

### Map canonical data

At minimum:

```text
melodia_ecological_density
melodia_monolith_proximity
melodia_filter_flow_strength
melodia_moisture
```

### Required checks

- local/global biome workflow;
- priority resolution;
- blending readability;
- project asset mapping;
- PCG interoperability;
- runtime generation if practical;
- GPU scatter if practical;
- deterministic regeneration;
- World Partition behavior;
- package result.

### Adopt architecture if

Biome Core substantially simplifies a real P3 ecology conflict while keeping SpeedTree asset ownership and semantic-field ownership understandable.

### Reject direct dependency if

The project can reproduce the useful architecture cleanly with ordinary PCG and fewer Experimental dependencies.

Even on rejection, document any reusable architecture ideas.

---

# 6. Test 04 — SpeedTree / Nanite Foliage three-lane canary

**Question:** Can UE5.8's Experimental Nanite Foliage representation reduce the cost of Melodia-quality botanical density without breaking the SpeedTree authoring loop?

**Map:** `LV_RND_SpeedTree_NaniteFoliage_Canary`

**Timebox:** 3 hours maximum for the entire investigation. Stop earlier if the conversion path becomes obviously non-production-ready.

### Use one approved project-owned SpeedTree

Prefer a tree that already exposes a real production cost or visual compromise.

### Lane A — current production representation

Current SpeedTree import, material and wind setup.

Record baseline:

```text
uasset_size
GPU_ms
VSM_ms
material/shader_cost
streaming_memory
close_quality
mid_distance_quality
far_canopy_quality
wind_quality
```

### Lane B — conventional Nanite-focused foliage variant

Where source geometry permits:

- geometry leaves rather than large masked cards;
- Nanite Preserve Area;
- bounded WPO;
- equivalent cameras and instance counts.

### Lane C — Experimental Nanite Foliage representation

Attempt:

- part decomposition / assembly;
- Nanite Assembly construction;
- skeletal representation if viable;
- optional Dynamic Wind only if setup is reasonable.

Do not assume `.st9` import performs this conversion automatically.

### Critical production metric: edit latency

Make one botanical source change after initial setup and measure the time required to propagate it through each lane.

A runtime win that destroys botanical iteration fails.

### Outcomes allowed

```text
PROMISING_RND
BLOCKED_CONVERSION
NO_MEANINGFUL_GAIN
TOO_FRAGILE
```

No chapter migration from this test.

---

# 7. Test 05 — World Streaming Insights evidence harness

**Question:** Can the project establish a repeatable streaming/memory benchmark route for all future worldbuilding tests?

**Map:** use an existing isolated world slice or the largest R&D world map that is safe to profile.

**Timebox:** 60 minutes.

### Fixed route

Define:

- player start;
- 2–5 minute traversal path;
- fixed camera/FPS policy;
- streaming-source configuration;
- same scalability settings;
- same warm-up policy.

### Capture

Use World Streaming trace support and record:

- loaded/activated cell count over route;
- estimated package memory where available;
- cell priority anomalies;
- shared/unique memory trends;
- streaming stalls or unexpected activation;
- HLOD transitions.

### Commit

Do not commit huge trace files by default.

Commit:

- exact capture command/config;
- benchmark route description;
- summary metrics;
- screenshots from Insights if lightweight;
- path to local trace evidence.

This harness becomes mandatory when evaluating:

- Mesh Terrain;
- Biome Core runtime generation;
- Nanite Foliage;
- FastGeo;
- chapter-scale PCG changes.

---

# 8. Test 06 — Fast Geometry Streaming canary only when justified

**Status:** conditional / WATCH.

Do not run simply because the plugin exists.

### Trigger

Run only if World Streaming Insights or actor/component profiling shows a real static-world representation bottleneck.

**Map:** duplicate of the affected R&D slice.

### Compare

```text
normal authored partitioned world
vs
FastGeo-converted representation
```

Measure:

- actor/component count;
- cell memory;
- load/activation time;
- runtime CPU;
- packaging stability;
- decal/light/physics behavior relevant to the slice;
- edit/rebuild friction.

### Promotion gate

A clear measurable runtime win with safe rebuild/rollback.

Experimental status prevents it from becoming default world authority without a second validation pass.

---

# 9. Test 07 — P3 vector-field authoring triangle

**Question:** Which tool is fastest for art-directing a P3 filter current while keeping world meaning portable?

**Map:** `LV_RND_P3_VectorFieldComparator`

### Three lanes

1. Houdini vector/volume field.
2. VectorayGen.
3. Native Unreal approximation using Niagara vector-field/data workflows.

### Timebox

20 minutes creative work per lane after setup.

### Common target

One current must:

- curve around a 5–10 m obstacle;
- converge slightly toward the horizon direction;
- include one quiet region and one compressed high-speed region;
- drive visible pollen/debris in UE.

### Metrics

```text
setup_minutes
creative_minutes
export_minutes
axis/scale corrections
field_data_size
UE_import_steps
visual_control_score
obstacle_response_score
reproducibility
runtime_cost
```

### Ownership rule

Whichever authoring tool wins, canonical world meaning remains:

```text
melodia_filter_flow_dir_ws
melodia_filter_flow_strength
```

Do not let a vendor-specific field file become the only copy of the design intent.

---

# 10. Test 08 — Native Niagara vs FluidNinja environmental field

**Question:** Does FluidNinja create a meaningfully better coherent local interaction field than a native Niagara implementation at acceptable runtime cost?

**Map:** `LV_RND_P3_LocalField_NativeVsFluidNinja`

### Shared target

30–50 m player-local current with:

- pollen;
- mist;
- one surface/material response;
- one player disturbance;
- one fixed directional source.

### Lane A — native Niagara

Use the simplest viable combination of:

- Grid2D/Grid3D or applicable fluid template;
- Simulation Stages;
- Niagara Data Channels if useful;
- native vector-field/data interfaces.

### Lane B — FluidNinja

Build the same visible behavior without expanding scope.

### Metrics

- setup/iteration time;
- GPU cost;
- memory;
- cross-system field coherence;
- collision/interaction quality;
- scalability controls;
- package result;
- runtime/plugin dependency;
- how easily canonical semantic strength/direction can drive or constrain the simulation.

### Adopt FluidNinja only if

The runtime result is visibly more coherent or materially faster to author than native Niagara **and** the plugin does not become a second gameplay/world-state authority.

---

# 11. Recommended execution order

```text
1. Native PCG Manual Editing baseline          60 min
2. P3 PCG Artist Tool prototype                90 min
3. Dash comparative pass                       60–90 min
4. Biome Core ecology spike                    120 min
5. World Streaming Insights harness            60 min
6. Vector-field triangle                       ~90 min + setup
7. SpeedTree/Nanite Foliage canary             up to 180 min
8. FluidNinja vs Niagara                       only after native field baseline
9. FastGeo                                     only when evidence triggers it
```

The first four tests should occur before installing more general world-dressing software.

---

# 12. Expected repository artifacts

After these tests, the useful Git state should look roughly like:

```text
Docs/Research/
  UE58_NATIVE_WORLD_AUTHORING_BASELINE_2026-08-31.md
  Evidence/Toolchain/2026-08-31/
    pcg_manual_edit/
      result.md
      metrics.json
    pcg_artist_tools/
      result.md
      metrics.json
    biome_core/
      result.md
      metrics.json
    nanite_foliage/
      result.md
      metrics.json
    vector_field_comparison/
      result.md
      metrics.json

Content/ or project PCG location, only if policy permits:
  R&D-only PCG tool graphs/presets
```

Do not commit vendor binaries, sample packs or large profiling traces.

---

# 13. Decision rubric

## ADOPT NATIVE PATTERN

A native UE workflow solves the bottleneck with acceptable complexity. External tools must now beat it.

## ADOPT EXTERNAL ACCELERATOR

External tool provides a repeatable 25%+ time reduction or a substantial quality capability unavailable natively, and leaves a maintainable shipping representation.

## PARK

Potentially useful but current bottleneck is too small or engine/plugin maturity too low.

## REJECT

No meaningful gain, poor reproducibility, weak package behavior, competing authority or excessive source-control/runtime dependency.

## WATCH

Experimental technology with real strategic value but no current production reason to integrate.

---

# 14. Highest-value hypothesis

The most valuable “new tool” may be a thin layer of **Melodia-specific PCG Editor Mode tools** rather than another commercial package.

If `P3_FilterFlow_Brush`, `P2_MoltSuccession_Brush`, `P1_TensionFiber_Spline` and related tools can manipulate the same canonical fields Houdini already authors, the project gains something more durable than a scatter plugin:

> an artist-facing procedural language whose semantics belong to Melodia.

That is the native baseline every future environment tool should have to beat.