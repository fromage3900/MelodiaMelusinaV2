# 2026-08-31 — Emerging Toolchain Integration Spike Plan

**Project:** Melodia Melusina / UE5.8  
**Purpose:** test every newly researched tool against a real Melodia bottleneck without destabilizing production.  
**Companion research:** `Docs/Research/EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH_2026-08-30.md`

---

# Success definition

Tomorrow is **not** an installation marathon and not a renderer migration.

The objective is to leave the day with:

- reproducible evidence for what actually accelerates Melodia;
- a clean Adopt / Park / Reject decision for every tool we can reasonably test;
- isolated R&D maps/projects for experimental Unreal features;
- no irreversible production-map/plugin migration;
- timings and screenshots/captures from real Melodia-shaped tasks;
- a short list of 2–4 tools worth integrating further.

The benchmark question for every tool is:

> **Does this let us produce a visibly better Melodia result per hour than the current workflow?**

---

# Safety rules before starting

1. Pull the current project and confirm a clean worktree.
2. Do not perform R&D in the only copy of a hero map.
3. New runtime/editor plugins are enabled only on a dedicated local branch or test project unless already established.
4. Record exact version/build before each test.
5. Verify current license/trial/export restrictions before committing outputs.
6. Do not commit third-party binaries, proprietary example content or marketplace source assets unless repository policy explicitly permits it.
7. Commit only:
   - our test docs;
   - our generated source/config where legally permitted;
   - screenshots/captures if useful and lightweight;
   - Melodia-owned test assets;
   - reproducible notes/settings.
8. Prefer baked/native UE outputs over runtime dependencies.
9. Experimental UE5.8 systems remain isolated.
10. Stop a test when it has already failed its value proposition.

---

# Benchmark scenes/assets

Use the same small set of project-shaped benchmarks so tools are compared against useful work rather than vendor tutorials.

## Benchmark A — P2 Molt Material Family

Goal: one procedural molt fragment with matched states:

```text
Dormant
Hydrated
Reactive
Crystallized
Spent
```

Useful for:
- Copernicus;
- IlluGen;
- Toolbag;
- Substance comparison;
- Houdini SOP/COP interoperability.

## Benchmark B — P3 Filter-Flow Biome

Goal: a small grass/forest strip where ecology visibly reveals one impossible horizon-directed field.

Useful for:
- SpeedTree;
- Houdini semantic masks;
- UE PCG;
- Niagara;
- Dash final art pass;
- RTX future stress testing;
- Procedural Vegetation Editor experiment.

## Benchmark C — Mara Anchor Motion

Goal: 2–4 second grounded full-body brace/Anchor action using production-compatible proportions/skeleton assumptions.

Useful for:
- Cascadeur;
- UE Live Link/retarget iteration;
- Houdini deformation audit comparison.

## Benchmark D — Impossible Terrain Patch

Goal: a 20–40 m folded terrain/anatomy test with one overhang/cavity impossible for a normal heightfield.

Useful for:
- Houdini;
- UE5.8 Mesh Terrain + PCG;
- Gaea/World Creator as natural-base comparison.

## Benchmark E — Sea Above Hero Liquid/Atmosphere Shot

Goal: 5–10 second visual sketch containing one upward/liquid contradiction and one atmosphere response.

Useful for:
- LiquiGen;
- EmberGen;
- IlluGen;
- Niagara shipping-representation comparison.

---

# Priority order

## Tier A — test first

1. Copernicus
2. IlluGen
3. Cascadeur
4. Unreal MCP
5. UE5.8 Mesh Terrain + PCG

These have the highest chance of changing day-to-day production.

## Tier B — test if Tier A completes cleanly

6. Dash
7. LiquiGen
8. EmberGen
9. Marmoset Toolbag

## Tier C — controlled comparison / optional installs

10. Gaea
11. World Creator
12. UE5.8 Procedural Vegetation Editor

## Tier D — research spike only, no production adoption tomorrow

13. NVIDIA RTX Kit / NvRTX / neural shaders
14. Neural texture/material techniques
15. Procedura
16. Magpie / generative realtime renderer

SpeedTree is not an evaluation candidate; it is the **baseline botanical pillar** used inside several tests.

---

# Test 01 — Copernicus

**Timebox:** 60–90 min  
**Benchmark:** A — P2 Molt Material Family

### Build

From one Houdini geometry/anatomy source create:
- region ID / age mask;
- vein or seam distance field;
- wetness mask;
- edge/cavity mask;
- one pigment field.

Feed the same source into Copernicus and generate at minimum:
- base color;
- roughness;
- normal/detail contribution;
- wetness/reactivity mask;
- packed utility mask.

### Unreal test
- bake/export to ordinary UE texture assets;
- drive existing Unreal master-material logic rather than creating a new shader framework;
- verify deterministic recook.

### Measure
- setup time;
- recook time;
- how many maps remain synchronized automatically after geometry changes;
- cleanup required in Substance.

### Adopt if
One procedural rule can produce geometry + useful matching texture data without creating brittle export work.

### Park/reject if
It merely recreates Substance work with more setup and no geometry-data advantage.

---

# Test 02 — IlluGen

**Timebox:** 45–60 min  
**Benchmark:** A or E

### Build
Create one Melodia-specific animated texture family:
- upward/curved flow map;
- distortion;
- caustic/interference pattern;
- packed mask or flipbook.

### Unreal test
Apply it to either:
- Sea Above local reveal material/Niagara;
- P3 filter-flow particle/material prototype.

### Compare
Build the same visual idea using the fastest known Houdini/Copernicus/Substance path.

### Adopt if
IlluGen reaches usable VFX texture motion materially faster and exports cleanly.

### Boundary
IlluGen never owns gameplay fields. It beautifies fields authored elsewhere.

---

# Test 03 — Cascadeur

**Timebox:** 60–90 min  
**Benchmark:** C — Mara Anchor Motion

### Build
- import/retarget a production-compatible humanoid skeleton;
- create a short brace/Anchor animation;
- include weight shift, planted feet and recovery;
- test Unreal Live Link if available in the installed build.

### Verify in UE
- retarget fidelity;
- root motion;
- foot sliding;
- shoulder/coat clearance assumptions;
- iteration latency.

### Compare
Time equivalent blocking in the current animation route.

### Adopt if
Physics-assisted iteration clearly reduces blocking/cleanup time without forcing skeleton divergence.

---

# Test 04 — Unreal MCP

**Timebox:** 60 min  
**Benchmark:** isolated R&D map only

### Initial safe action surface
Attempt only:
1. inspect currently selected actor;
2. spawn one known test Blueprint/primitive;
3. create/configure one Material Instance or set one safe property;
4. run/read one automation or validation command if supported.

### Do NOT allow first day
- deletion/bulk rename;
- map migration;
- mass asset edits;
- plugin toggling;
- source-control operations;
- arbitrary Python/shell execution through a custom bridge.

### Document
- exact UE5.8 MCP setup;
- transport/client used;
- successful calls;
- failure modes;
- which Melodia-specific commands would be worth implementing later.

### Candidate phase-2 commands

```text
ValidateWaterAuthority
AuditDataLayers
ValidateMaraSkeleton
CreateRhythmReactiveMID
BuildMonolithPrototypeScaffold
AuditSpeedTreeBiome
RunP0SmokeTest
```

### Adopt if
Agent-to-editor operations are reliable enough to automate repetitive validation/scaffolding while staying constrained.

---

# Test 05 — UE5.8 Mesh Terrain + PCG

**Timebox:** 60–90 min  
**Benchmark:** D — Impossible Terrain Patch

### Build
- isolated test level/project;
- one folded/overhung Houdini-authored patch;
- one material setup;
- one PCG operation reading or decorating the terrain;
- simple collision/navigation test.

### Record
- import/edit friction;
- crash/editor instability;
- Nanite/material behavior;
- collision;
- PCG compatibility;
- packaging result;
- whether iteration is actually better than static meshes + landscape hybrid.

### Decision
**Never adopt globally tomorrow.** The only valid outcomes are:
- promising R&D candidate;
- not ready for Melodia.

---

# Test 06 — Dash

**Timebox:** 30–45 min  
**Benchmark:** B — P3 Filter-Flow Biome

### Procedure
1. make a small PCG/SpeedTree baseline scene;
2. duplicate it;
3. perform a strict 20-minute Dash art pass on one copy;
4. compare screenshots from the same cameras.

### Test tasks
- rocks/logs/debris;
- one cable/vine/road-like assembly;
- physics drop/placement if useful;
- fast prop composition around focal points.

### Adopt if
The scene becomes more authored faster than equivalent manual UE tools and the final result can remain normal UE content.

---

# Test 07 — LiquiGen

**Timebox:** 30–45 min  
**Benchmark:** E

### Build
One upward or impossible liquid motion study with foam/spray if supported.

### Export test
Check the fastest path into an Unreal-friendly representation:
- Alembic/cache;
- mesh sequence;
- image sequence/flipbook;
- reference-only handoff to Houdini.

### Adopt if
It dramatically shortens liquid ideation even when Houdini remains the final high-control sim tool.

---

# Test 08 — EmberGen

**Timebox:** 30–45 min  
**Benchmark:** E or P3 atmospheric inhale

### Build
A non-explosion atmospheric event:
- fog pulled toward an impossible direction;
- large-scale inhalation plume;
- cloud layer pushed around negative space.

### Export/representation question
Can the result become a cheap UE representation through VDB/flipbook/texture/cached data without runtime dependence?

### Adopt if
Atmospheric concept iteration is significantly faster than Houdini Pyro for the same class of shot.

---

# Test 09 — Marmoset Toolbag

**Timebox:** 45–60 min  
**Benchmark:** one existing hero character/prop high-to-low bake

### Evaluate
- bake setup speed;
- UDIM handling;
- cage/debug workflow;
- bevel/material-property bake utility;
- groom/material preview;
- how quickly problems are caught before UE import.

### Adopt if
It saves meaningful time on hero-asset bake/debug cycles.

---

# Test 10 — Gaea

**Timebox:** 30–45 min  
**Benchmark:** D natural base

### Task
Generate one believable ravine/highland/plateau base appropriate for P2 or P3.

### Compare against Houdini
Measure:
- time to convincing erosion;
- export cleanliness;
- scale fidelity;
- mask usefulness;
- how easy the result is to violate procedurally in Houdini.

### Adopt if
It is clearly the faster natural-geology front end.

---

# Test 11 — World Creator

**Timebox:** 30 min  
**Benchmark:** D natural base

### Task
Generate 3 radically different terrain compositions in one short session.

### Decision against Gaea
If both are available, choose the one that provides the larger **finished composition per minute** benefit for Melodia. Do not keep two paid terrain ideation tools without a concrete reason.

---

# Test 12 — UE5.8 Procedural Vegetation Editor

**Timebox:** 30–45 min  
**Benchmark:** B

### Important baseline
SpeedTree remains authoritative.

### Test
Attempt one secondary growth/mutation task that would normally require either:
- a special SpeedTree variant;
- a Houdini generated growth mesh.

Examples:
- branch growth around one Monolith fragment;
- grafted/localized mutation;
- secondary roots avoiding one collider.

### Keep only if
It creates useful **secondary anomalous growth** faster than SpeedTree/Houdini while integrating cleanly with the production biome.

---

# Test 13 — NVIDIA RTX Kit / NvRTX

**Timebox tomorrow:** research/setup feasibility only, 20–30 min

### Do not
- fork production;
- migrate shaders;
- promise shipping support.

### Record
- current UE compatibility;
- hardware requirement;
- branch/build burden;
- relevant features for foliage/character/path-traced cinematics;
- whether a later isolated benchmark is justified.

### Future benchmark
P3 SpeedTree density stress map:
- same cameras;
- same foliage counts;
- baseline UE vs candidate RTX path;
- GPU frame time;
- VRAM;
- visual gain;
- maintenance cost.

---

# Test 14 — Neural shaders / neural texture/material systems

**Timebox tomorrow:** 20 min literature/SDK feasibility note only

### Track specifically
- texture-memory reduction potential for wardrobe/material libraries;
- neural approximation of expensive pearlescent/fabric/water-glass shading;
- platform/hardware restrictions;
- training/build pipeline burden.

### No adoption until
A production-supported route exists that is less risky than conventional UE materials.

---

# Test 15 — Procedura

**Timebox tomorrow:** research-only 15 min

### Question
Is there an accessible implementation or reproducible code path that produces editable parametric assemblies rather than static generated meshes?

### Ideal future Melodia benchmark
Generate three Sounding Staff mechanical variations from fixed connection points and part constraints while preserving editable structure.

### Current default
**Watch. Do not integrate.**

---

# Test 16 — Magpie / generative realtime renderer

**Timebox tomorrow:** research-only 15 min

### Evaluate as architecture research
- engine remains simulation authority;
- generative system owns visual frame;
- latency;
- temporal consistency;
- deterministic art direction;
- collision/gameplay mismatch;
- debugging/QA impossibility;
- platform cost.

### Current default
**Research reference only.** It should not touch Melodia production.

---

# SpeedTree-specific integration work during these tests

Because SpeedTree is already a major Melodia pillar, use tomorrow to formalize rather than evaluate it.

## Minimal semantic bridge

Define/confirm the first Houdini/PCG fields that can influence SpeedTree distribution/presentation:

```text
melodia_moisture
melodia_slope
melodia_wind_exposure
melodia_soil_depth
melodia_monolith_proximity
melodia_molt_age
melodia_filter_flow
melodia_tension
melodia_ecological_density
```

Do not make SpeedTree ingest all of these directly. They are common **world-description data** from which Unreal/PCG/material systems decide how SpeedTree assets appear.

## P3 proof
Build one tiny sequence:

```text
normal wind
 -> grass/foliage begins biased response
 -> loose Niagara matter aligns
 -> larger SpeedTree silhouettes support direction
 -> filter-flow becomes unmistakable
```

This is a prototype of the larger principle:

> **The ecosystem can animate a Monolith without animating the Monolith itself.**

---

# Suggested day schedule

This is a priority sequence, not a promise to finish every install.

```text
09:00  clean repo / benchmark setup / versions
09:30  Copernicus
11:00  IlluGen
12:00  Cascadeur
13:00  break / capture notes
13:30  Unreal MCP
14:30  Mesh Terrain + PCG
16:00  Dash or Toolbag
16:45  LiquiGen / EmberGen rapid comparisons
17:30  Gaea / World Creator quick comparison if installed/trials permit
18:15  PVE short test
18:45  RTX / neural / Procedura / Magpie research notes
19:15  decisions + Git commits
```

If setup/download time makes this unrealistic, preserve the **priority order**, not the clock.

---

# Required result template for every tested tool

Add a short result block to this file or a follow-up audit:

```text
Tool:
Version:
Test asset/map:
Install/setup minutes:
Hands-on minutes:
Current workflow comparator:
What was faster:
What was worse:
Export/runtime dependency:
Stability problems:
Visual result:
Performance result:
License/provenance note:
Decision: ADOPT / PARK / REJECT / WATCH
Next action:
```

---

# End-of-day decisions we want

By tomorrow night, aim to know:

1. whether Copernicus becomes a real part of the Houdini material pipeline;
2. whether IlluGen earns a dedicated VFX-texture role;
3. whether Cascadeur belongs in hero-humanoid animation iteration;
4. whether Unreal MCP deserves a Melodia-specific safe automation layer;
5. whether Mesh Terrain is worth continued R&D for late Monoliths;
6. whether Dash materially improves the final environment art pass;
7. whether LiquiGen/EmberGen are useful rapid simulation sketchbooks;
8. whether Toolbag saves hero-asset finishing time;
9. whether Gaea or World Creator earns a terrain-ideation slot;
10. whether PVE adds anything beside heavy SpeedTree use;
11. whether RTX/neural rendering deserves a future dedicated hardware benchmark;
12. whether Procedura/Magpie remain watchlist research only.

The goal is **not more software**.

The goal is a smaller, faster, more deliberate Melodia production system.
