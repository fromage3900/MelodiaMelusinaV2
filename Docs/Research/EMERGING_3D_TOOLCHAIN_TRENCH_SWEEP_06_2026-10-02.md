# Emerging 3D Toolchain — Trench Sweep 06

**Date:** 2026-10-02  
**Project:** Melodia Melusina / Unreal Engine 5.8  
**Status:** repo-aware procedural-worldbuilding / materials R&D delta; bounded canaries only  
**Git baseline checked:** `main` @ `46ac21dd6a9303cd36ca80905ac4d2357947e58c`  
**Companion:** `EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_05_2026-09-25.md`  
**Production authority:** `CURRENT_STATE.md` + `Docs/P1_TASK_LEDGER.json`

---

## Executive result

This sweep does **not** reopen generic procedural generation work.

Sweep 05 already established that the following are baseline Melodia capabilities rather than research discoveries:

- PCG Python semantic enrichment;
- Resonance / EcologyClass / MaterialVariant / ScaleBias metadata;
- native PCG spawners + per-instance custom data;
- material variation driven from procedural metadata;
- World Compiler ecology/presentation;
- Houdini/Hython deterministic source generation;
- Copernicus texture/mask generation;
- Gaea/DEM -> terrain handoff -> UE 5.8 Mesh Terrain source path.

The 2026-10-02 Git ledger is even more restrictive than the Sept. 25 snapshot:

`procedural_system_policy = BOUNDED_OWNER_APPROVED_SCHOOL_GATES`

Current owner-approved procedural work is limited to the named P0 Sea Above FieldAtlas tile, Faraway Mother resonance-field integration, and Gate 6 Glitter Pile. General PCG / World Compiler / Universe Foundry / FieldAtlas architecture expansion remains consume/maintain-only.

Therefore every item below is a **research canary**, not a new production authority or automatic task.

The useful additions/refinements from this sweep are:

1. **PROMOTE:** GPU PCG + Custom HLSL as a measured Resonance-field scale canary;
2. **REFINE:** Python-authored 2D structure -> Copernicus -> COP HDA -> Unreal as an interactive surface-authoring loop;
3. **CARRY FORWARD:** local-statistics anti-tiling for large hero surfaces;
4. **CARRY FORWARD:** iso-contour terrain as an artist-first macroform representation;
5. **NEW:** deformation-aware procedural texturing for highly stretched / advected surfaces.

---

# 1. UE 5.8 GPU PCG + Custom HLSL + Python orchestration — TEST NOW AS A BENCHMARK

Official Epic documentation:

- https://dev.epicgames.com/documentation/en-us/unreal-engine/using-pcg-with-gpu-processing-in-unreal-engine
- Unreal Python API index exposes `PCGCustomHLSLSettings`, `PCGCustomHLSLKernel`, `PCGComputeGraphSettings`, and related compute types.

Epic labels GPU PCG **Beta**.

The important implementation facts for Melodia are:

- compatible GPU-targeted PCG nodes are grouped into Compute Graphs;
- Custom HLSL provides arbitrary GPU-side data processing;
- Point Processor kernels execute once per point;
- Static Mesh Spawner supports GPU execution;
- CPU -> GPU uploads and GPU -> CPU downloads are explicitly visible and can erase the win;
- reusable `UComputeSource` assets can supply HLSL source;
- debugging includes cooked-HLSL dumps, data-description dumps, shader debug values, and scoped render capture.

## Why this survives the current Melodia filter

The project already has a correct CPU/editor semantic contract.

Do **not** move gameplay truth or the semantic vocabulary into HLSL.

The useful question is simply:

> At what density does evaluating one existing Resonance/ecology field on the GPU beat the current CPU/Python authoring path enough to matter?

Python's role remains **author/build/test orchestration**:

```text
existing canonical semantic rule
    -> Python configures / audits bounded PCG test graph
    -> GPU Custom HLSL evaluates dense field
    -> GPU-compatible filtering / point modification
    -> GPU Static Mesh Spawner
    -> existing material / per-instance semantic consumer
```

## Canary

`PCG_GPU_Resonance_Canary`

Use one existing Resonance-derived field operation. Do not invent a new world rule.

Benchmark the same visual result at approximately:

- 10k points;
- 100k points;
- 500k points.

Record:

- CPU generation time;
- GPU generation time;
- transfer boundaries;
- editor responsiveness;
- runtime frame cost where relevant;
- generated instance count;
- semantic range / equivalence;
- GPU memory impact.

Prefer one contiguous GPU region. Avoid bouncing the same data back to CPU merely for convenience.

## Pass condition

Promote GPU execution for that class of dense field only if:

1. the result remains semantically equivalent enough for the consumer;
2. the relevant density produces a meaningful measured gain;
3. transfer overhead does not consume the advantage;
4. graph debugging remains understandable;
5. the CPU semantic contract remains the readable source of truth.

## Park condition

If normal Melodia biome densities do not reach the crossover point, keep GPU PCG available as a scale tool and do not duplicate the CPU implementation across production graphs.

---

# 2. Python -> Copernicus -> COP HDA -> Unreal — TEST NOW

Official SideFX references:

- https://www.sidefx.com/docs/houdini/unreal/copernicus.html
- https://www.sidefx.com/docs/houdini/news/22/engine.html
- https://www.sidefx.com/contentlibrary/cops-scifi-panel/

Houdini 22's Unreal plugin supports UE 5.7 / 5.8 and supports Copernicus HDAs in both the asset editor and normal world.

Documented functionality includes:

- 2D COP HDA preview in the Unreal asset editor;
- generated texture selection / RGBA inspection;
- exposed HDA parameters and inputs;
- generated texture resolution, pixel scale and data-format controls;
- automatic Material Instance generation from a source Unreal material;
- bake / recook workflows;
- AO, displacement, Compact/RMA and normal material outputs.

The especially relevant July 2026 SideFX **COPs SciFi Panel** example demonstrates a production-shaped chain:

```text
Python Sub-COPhda
    -> procedural 2D structural lines
Main-COPhda
    -> detail / height / color development
SOP HDA wrapper + Houdini Engine
    -> Unreal
```

That is more relevant to Melodia than a generic texture-generator demo because the structural layer can be authored semantically.

## Melodia interpretation

Use Python for **meaningful graphic structure**, not pixel painting.

Candidate structural sources:

- cymatic / Chladni line families;
- shell-growth bands;
- art-nouveau floral engravings;
- musical seam diagrams;
- constellation / orrery channels;
- fabric stitch / tension paths;
- Monolith anatomical linework.

Then let Copernicus turn those sparse authored structures into richer surface evidence:

- height;
- bevel / relief;
- normal;
- roughness;
- RMA;
- base color;
- emissive;
- masks.

## Canary

`COPHDA_MelodiaSemanticSurface_Canary`

Start from one existing bounded Melodia surface family.

Python stage:
- create one deterministic 2D structural mask;
- record seed + source parameters.

COP stage:
- add height/detail;
- derive normal;
- derive roughness/RMA;
- develop color;
- expose only 4–6 meaningful controls.

Unreal stage:
- open the COP HDA;
- alter controls;
- recook;
- bake outputs;
- feed them into an **existing** Melodia material / MI authority;
- save / reload and verify persistence.

## Pass condition

This becomes an interactive texture-forge lane only if it is substantially faster than the current manual Hython/export/import iteration for lookdev **without**:

- replacing the existing material master;
- creating runtime Houdini dependence;
- bypassing deterministic batch/evidence tooling;
- creating a second source of world truth.

Hython remains the preferred deterministic batch lane.

---

# 3. Real-time by-example texture synthesis using local statistics exchange — KEEP TEST-SOON

**Paper:** Nicolas Lutz, Guillaume Gilet  
**Computer Graphics Forum, 2026**  
First published: 2026-05-13  
DOI: https://doi.org/10.1111/cgf.70355

Source:

https://onlinelibrary.wiley.com/doi/10.1111/cgf.70355

This remains one of the most directly useful material papers for Melodia.

The paper attacks the problem of synthesizing effectively unbounded surfaces from exemplars while reducing obvious repetition, especially for textures with spatial organization that simple random tiling/blending handles poorly.

## Practical takeaway

Melodia already has:

- triplanar / world-aligned mapping;
- macro variation;
- layered masters;
- procedural semantic variation;
- Nikki / pearl / SDF / stylized material controls.

The next useful problem is not “more random parameters.”

It is:

> preserve recognizable authored motifs while delaying the point where the eye detects repetition.

Candidate surfaces:

- velvet / cloth terrain;
- pearly shell geology;
- coral / reef structures;
- broad stylized stone;
- silk/fabric mountains;
- decorative architectural materials.

## Canary

`MF_LocalStatsBreakup_Prototype`

Do not port the full paper first.

Use one visibly repeating hero exemplar and approximate the core idea:

1. segment or classify a few local regions;
2. derive lightweight local statistics such as mean and variance/contrast;
3. use deterministic world-space tile IDs;
4. exchange/remap selected regional statistics across tiles;
5. preserve strong motif boundaries where possible.

A/B from the exact same camera against the current Melodia triplanar/macro-noise path.

## Pass metric

Use a practical art metric:

- how far can the camera move before the repeating pattern becomes obvious?
- does the method preserve the surface's authored identity?
- what is the material/shader cost?

Only implement more of the paper if the cheap approximation visibly wins.

---

# 4. Terrain Synthesis and Authoring based on Iso-Contours — KEEP TEST-SOON

**Authors:** Benoît Huftier, Hugo Schott, Eric Galin, Oscar Argudo, Adrien Peytavie, Eric Guérin  
**Computer Graphics Forum / Eurographics 2026**  
First published: 2026-04-30  
DOI: https://doi.org/10.1111/cgf.70389

Sources:

- https://onlinelibrary.wiley.com/doi/10.1111/cgf.70389
- https://h-schott.github.io/p/isos/

The method represents terrain as nested editable vector iso-contours, then reconstructs conventional terrain data. The representation supports direct operations such as warping, slope modulation and smoothing before downstream erosion/amplification.

## Practical takeaway

This is an **authoring representation**, not a reason to create a fourth Melodia terrain system.

Noise-first terrain is excellent for geological possibility.

Contours may be better when the owner already knows the intended composition:

- hero ridge;
- basin;
- shoreline;
- plateau;
- controlled traversal valley;
- Heart Gate approach;
- Sea Above shelf;
- strong silhouette from a named camera.

## Canary

Author one small terrain tile from roughly 6–10 elevation contours.

Houdini/Hython stage:

1. consume authored closed splines;
2. assign elevations;
3. reconstruct / rasterize height;
4. run existing detail / erosion after macroform is locked;
5. emit through the existing terrain handoff.

Compare against the same brief produced noise-first in the current Gaea/Houdini lane.

## Pass condition

Keep the technique only if the owner reaches the desired traversal composition and major silhouette faster.

If it works, contours become another **input representation to existing terrain ownership**, not another terrain authority.

---

# 5. Physics-inspired procedural texturing of extremely deformable surfaces — NEW TEST-SOON / PATTERN CANARY

**Authors:** Aleksei Kalinov, Mickaël Ly, Christian Hafner, Chris Wojtan  
**ACM Transactions on Graphics 45(4), Article 154 / SIGGRAPH 2026**  
DOI: https://doi.org/10.1145/3811353

Sources:

- https://visualcomputing.ist.ac.at/publications/2026/DeformableTextures/
- https://research-explorer.ista.ac.at/record/21923

The paper addresses extreme distortion of surface texture under deformation.

Instead of trying to preserve an ordinary texture map through arbitrarily stretched motion, it introduces two wave-based procedural texturing approaches inspired by physical behavior such as:

- advection;
- self-similarity;
- changing visible detail under deformation.

Important production properties:

- fully procedural;
- no full physical material simulation is required;
- no stored deformation history beyond the input UV map;
- highly parallelizable on GPU;
- designed for real-time use.

Demonstrated examples include highly deforming lava, putty and sludge.

## Why this matters to Melodia

This is **not** mainly a character-cloth paper.

The interesting Melodia surfaces are the ones whose identity should survive or evolve through dramatic deformation:

- cloth / fabric terrain;
- living membranes;
- World Eater tissue;
- fluid/sludge magical matter;
- highly stretched ribbons;
- deforming Monolith surfaces;
- magical fabric or shell surfaces whose microstructure should not simply smear.

## Canary

Do not port the complete method into the universal master.

Choose one disposable deformation test mesh.

Create three views:

A. ordinary UV texture under extreme stretch;  
B. current project deformation/macro breakup;  
C. simplified wave-based procedural response inspired by the paper.

The first implementation only needs to test the core visual principle:

> as the surface stretches/compresses, procedural detail should change scale/structure plausibly instead of visibly smearing.

Implement as a focused material function or Custom node prototype.

## Pass condition

Proceed only if the effect is visibly superior under deformation while remaining:

- local to a specialized material family;
- GPU-cheap enough for its intended usage;
- stateless / deterministic;
- independent of a new simulation authority.

## Likely role

Specialized material technique for extreme-deformation surfaces, not a general environment master feature.

---

# 6. Revised practical priority

For current Melodia R&D, the ordering is:

## Tier A — worth an isolated canary now

1. **GPU PCG Resonance benchmark**
2. **Python -> COP HDA semantic-surface canary**

These extend existing owners and have clear measurable pass/fail gates.

## Tier B — high-value visual R&D

3. **Local-statistics anti-tiling**
4. **Iso-contour terrain macro-authoring**
5. **Deformation-aware procedural surface detail**

## Do not reopen from Sweep 05 without a named need

- stochastic geomorphological transport;
- InfiniteDiffusion / Terrain Diffusion;
- neural-material runtime work;
- another PCG semantic system;
- another field bus;
- another terrain authority.

---

# 7. Suggested experiment packets

These packets are intentionally small enough to hand to a UE/Houdini agent without authorizing architecture work.

## Packet A — `PCG_GPU_Resonance_Canary`

**Input:** existing Resonance semantic field/rule.  
**Output:** measured CPU vs GPU table + one matching beauty/debug pair.  
**Mutation scope:** disposable PCG test graph or copy only.  
**Stop condition:** if CPU/GPU transfer dominates at practical densities, PARK.

## Packet B — `COPHDA_MelodiaSemanticSurface_Canary`

**Input:** deterministic Python structural mask.  
**Output:** baked BaseColor/Normal/RMA/Height family consumed by an existing MI.  
**Mutation scope:** isolated COP HDA + test material instance.  
**Stop condition:** if round-trip is not faster than existing Hython/COP workflow, PARK.

## Packet C — `MF_LocalStatsBreakup_Prototype`

**Input:** one visibly tiling existing exemplar.  
**Output:** same-camera A/B against current master.  
**Mutation scope:** isolated material function/prototype instance.  
**Stop condition:** if motif identity degrades or cost outweighs repetition improvement, PARK.

## Packet D — `IsoContour_TerrainAuthoring_Canary`

**Input:** 6–10 owner-authored contour splines.  
**Output:** terrain handoff entering the existing terrain lane.  
**Mutation scope:** source-data experiment only.  
**Stop condition:** if noise-first authoring is faster or equally controllable, PARK.

## Packet E — `MF_DeformationAwareSurface_Canary`

**Input:** one aggressively stretching test mesh.  
**Output:** ordinary UV vs existing breakup vs wave-inspired procedural-detail comparison.  
**Mutation scope:** disposable material function / Custom node.  
**Stop condition:** no visually meaningful benefit under target deformation.

---

# 8. Research doctrine update

Sweep 05's doctrine still stands:

> **Melodia does not need more procedural systems. It needs the existing procedural systems to become easier to art-direct, richer in visible result, and cheaper to iterate.**

Sweep 06 sharpens that into three questions for future papers:

1. **Scale:** can an existing semantic operation run much cheaper at production density?
2. **Authoring:** can a human establish the intended shape/surface faster?
3. **Representation:** can the same authored identity survive scale, tiling, or deformation better?

If a new technique does not improve one of those three dimensions while fitting current authority boundaries, it should not enter the active queue.
