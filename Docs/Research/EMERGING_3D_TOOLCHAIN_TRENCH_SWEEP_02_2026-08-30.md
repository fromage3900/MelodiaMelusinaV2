# Emerging 3D Toolchain — Trench Sweep II

**Date:** 2026-08-30  
**Project:** Melodia Melusina / Unreal Engine 5.8  
**Status:** deep R&D annex; no listed external dependency is approved for production merely by inclusion here  
**Companion:** `Docs/Research/EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH_2026-08-30.md`

---

# Why this second sweep exists

The first survey found obvious high-value accelerators such as Copernicus, IlluGen, Cascadeur, Dash, Mesh Terrain and Unreal MCP.

This second sweep deliberately went below the obvious layer: Unreal plugin forums, Fab listings, small developer communities, emerging GPU frameworks, Gaussian-splat tooling, fashion/cloth technology, OpenUSD/Hydra infrastructure and research-oriented renderer projects.

The result is more useful than another list of DCC applications because several candidates map almost directly onto Melodia's unsolved problems:

- **fashion-game wardrobe scaling**;
- **environmental interaction fields**;
- **Monolith effects that are physical rather than decorative**;
- **non-heightfield terrain / cave / anatomical geography**;
- **rapid real-world capture for environment reference and material sourcing**;
- **cheap mocap -> physical cleanup -> UE iteration**;
- **future neural rendering / programmable rendering research**.

Core rule remains:

> **Production UE stays boring. R&D is allowed to be insane.**

---

# Tier S discoveries — add to active integration research

## 1. FluidNinja LIVE-2 — runtime environmental field laboratory

**Status:** LIVE-2 open beta in 2026; test only in isolated project/map until exact UE5.8 compatibility is verified.

FluidNinja LIVE is much more relevant to Melodia than a generic liquid plugin. LIVE-2 is being rebuilt around Niagara Simulation Stages and Data Interfaces and is designed to drive water, fog, smoke, fire, sand, snow, foliage, volumetrics and particles from common simulation fields.

Publicly described inputs include:
- mesh distance fields;
- landscape height/slope;
- spline direction;
- particles;
- destructible chunks;
- skeletal bones / object pivots.

Outputs can drive:
- mesh surfaces / arrays;
- volumetrics;
- Niagara particles;
- exposed simulation buffers such as density / velocity / pressure.

The architecture also uses a **player-local interactive simulation region with cheaper non-interactive patterns outside it**, which is conceptually extremely relevant to large Monolith events.

### Melodia use cases

P1 Faraway Mother:
- local wind/tension field affects prayer strips, loose fibers, dust and foliage;
- use field coherence as biological evidence rather than generic wind FX.

P2 God That Molts:
- reaction vapor / spores / secretion mist driven by local membrane state;
- player and companion motion disturb visible biological atmosphere.

P3 Horizon Eater:
- build a local filter-flow field around the player while distant fields use authored/passive approximations;
- one velocity field can drive pollen, loose grass fragments, mist, particles and surface cues.

### Integration doctrine

```text
FluidNinja = optional runtime local field solver
Niagara    = presentation / particles
SpeedTree  = authored botanical assets
Materials  = field response
Houdini    = offline macro-field / vector-field authoring
```

Do **not** let FluidNinja become water authority; Oceanology/project water systems remain authoritative.

### First benchmark
Create `L_RND_FilterField_FluidNinja`:
- 30–50 m local field around player;
- one directional/spline feeding current;
- Niagara pollen + mist use the field;
- one foliage/material response reads a simplified exported signal;
- profile GPU and memory against a non-simulated Niagara-vector-field version.

Decision gate: adopt only if the field coherence produces a noticeably better Monolith read at sane cost.

---

## 2. Advanced Environment Interaction — persistent GPU world-contact data

**Released:** 2026.  
**Architecture:** GPU-driven render targets + Niagara; designed to avoid scene captures and per-frame decal/mesh modification approaches.

It can produce persistent blended interaction data such as:
- footprints;
- tire/object trails;
- surface deformation;
- water ripples.

Public material says it supports Nanite, Virtual Heightfield Mesh and flat-surface workflows, with scalability controls. Version 1.1 adds persistent traces that can survive when the player travels far away and returns.

### Why Melodia cares

This is not merely a snow-footprint system. It is a candidate **generic contact-evidence layer**.

Potential uses:
- Shorelistener hem leaving temporary impossible wetness / tide marks;
- Ebenezer claw/beak contact marking suspicious material;
- P2 membrane indentation / residue response;
- outfit-specific footprints / surface reactions;
- Monolith areas retaining evidence of player traversal;
- Mara Anchor leaving a stable reference imprint while nearby reality shifts.

### Test against building our own
Benchmark exactly one target: player + Ebenezer contact into a reactive P2 surface.

Compare:
1. Advanced Environment Interaction;
2. simple project-owned RVT/render-target implementation;
3. Niagara-only approximation.

Adopt only if it saves enough engineering time while keeping data ownership understandable.

---

## 3. MetaTailor — wardrobe auto-fit / auto-skin acceleration

MetaTailor currently advertises:
- arbitrary rigged FBX character import;
- self-adaptive garments;
- auto-fitting;
- automatic rigging / skin-weight generation;
- garment layering and fit correction;
- real-time cloth preview;
- Unreal bridge / round-trip workflow.

This could attack one of the largest long-term costs in a fashion-heavy game: **making every garment fit a hero body and skeleton cleanly before final bespoke polish**.

### Correct role for Melodia

Not a costume generator and not final character authority.

Potential role:

```text
CLO / donor garment / authored mesh
        -> MetaTailor quick conform + provisional skin
        -> Houdini deformation/intersection audit
        -> manual hero corrections
        -> UE Chaos / skeletal production setup
```

### First benchmark
Use an existing non-final garment donor and canonical Melusina body/skeleton.

Measure:
- body conform time;
- weight quality at shoulders / hips / elbows;
- deformation through 10 existing gameplay poses;
- whether material slots / UVs / mesh organization survive;
- how much manual cleanup remains.

**Pass condition:** a believable first-pass fitted/skinned garment in a fraction of the current manual transfer/cleanup time.

This could be more important to a wardrobe game than another renderer.

---

## 4. UE5.8 Chaos Outfit Assets / parametric clothing — native wardrobe R&D

UE5.8 includes a **Beta Chaos Outfit Asset** system. Epic's documented parametric clothing workflow is MetaHuman-oriented, but the underlying Outfit Asset is a Chaos Cloth asset type capable of assembling multiple Cloth Assets and includes mesh-resizing infrastructure.

Important distinction:
- official resizable/parametric workflow is documented for MetaHumans / Fab;
- Melusina is a custom stylized hero, so generic applicability must be proven rather than assumed.

### Why it matters anyway

Infinity Nikki-scale fashion becomes painful when every outfit is an isolated pile of meshes and bespoke logic.

A future Melodia outfit container needs concepts similar to:
- garment-piece assembly;
- simulation/render mesh separation;
- cloth asset references;
- resize/fitting metadata;
- body-hide information;
- per-outfit material/runtime metadata.

The UE Outfit Asset/Dataflow design is therefore worth studying even if we do not directly adopt MetaHuman resizing.

### First R&D question
Can a custom non-MetaHuman skeletal mesh use a Chaos Outfit Asset cleanly as an **assembly container**, even if parametric body resizing remains disabled?

If yes, it may inform `U/DA_MelodiaOutfitDefinition` architecture.

If no, steal the data-organization ideas, not the implementation.

---

## 5. Rokoko Vision 3.0 -> Cascadeur -> Unreal

Rokoko Vision 3.0 launched in July 2026 with a rebuilt monocular video-to-motion pipeline focused on faster iteration.

This creates a very cheap animation ideation chain:

```text
phone/video performance
 -> Rokoko Vision
 -> cleanup / physical exaggeration in Cascadeur
 -> IK Retarget / Control Rig polish in UE
```

### Melodia benchmark
Record one 10–15 second Mara sequence:
- inspect instrument;
- notice impossible pull;
- brace into Anchor;
- recover.

Compare total time against keyframe blockout from zero.

Do not judge the system on final finger/face quality; judge it on whether it supplies useful body mechanics faster.

---

# Tier A discoveries — serious isolated tests

## 6. JangaFX GeoGen

GeoGen is JangaFX's new real-time terrain / planet generator and remains Beta in 2026.

It competes with Gaea / World Creator on fast terrain generation but belongs to the same JangaFX ecosystem as IlluGen / EmberGen / LiquiGen.

### Melodia value proposition
If GeoGen can create geological macroforms and useful masks extremely quickly, it could become the **terrain thumbnailer** before Houdini makes the geography impossible.

Test against Gaea and World Creator using the same brief:
> highland steppe / chalk plateau for Horizon Eater, believable first, anatomically violatable second.

Keep only one fast-terrain ideation tool unless a second one has a clearly unique job.

---

## 7. JangaFX VectorayGen

VectorayGen is a specialized real-time vector-field authoring tool for game VFX. It can import objects, generate flows around geometry and build artistic turbulence/noise fields.

This is almost suspiciously aligned with Monolith presentation.

Potential uses:
- P3 filter flow;
- Sea Above upward droplet field;
- Faraway Mother tension wind;
- River Serpent current anatomy;
- Moon Grazer atmospheric flow;
- White Current invisible transport.

### Test
Create the same P3 filter field in:
1. VectorayGen;
2. Houdini volume/VDB workflow;
3. hand-authored Niagara vector field approximation.

Compare time-to-art-direct, export quality and runtime usability.

If VectorayGen wins, it becomes an **FX-field sketchbook**, while Houdini remains authoritative for data derived from actual world geometry.

---

## 8. Voxel Plugin 2 — volumetric/anatomical terrain alternative

Voxel Plugin 2's current documentation describes:
- Nanite-focused terrain rendering;
- materials / displacement;
- strong UE PCG integration;
- metadata queries;
- volume/height spline graphs;
- sculpting and material/metadata painting;
- experimental runtime editing;
- deterministic procedural world generation.

However current docs target UE5.6/5.7 and explicitly warn that 2.0 is actively developed and may be buggy.

### Why it is interesting

It may solve a class of geometry that Landscape cannot:
- caves;
- negative spaces;
- tunnels;
- fleshy folds;
- terrain with meaningful 3D volume;
- P3/P2 geography that must be queried by PCG as data.

### Why it is dangerous

- current documented UE target does not include 5.8;
- plugin is still active-development software;
- current world generation is runtime/on-the-fly rather than a simple static-bake workflow;
- introducing it beside Houdini + World Partition + PCG could create competing world authorities.

### Decision
**WATCH / isolated comparison only.**

Do not put it in production P1/P2/P3 until UE5.8 support and persistence/baking needs are proven.

Compare to UE5.8 Mesh Terrain rather than adopting both.

---

## 9. Errant Worlds / Errant Biomes

Errant Worlds is a mature Unreal-native set of large-world tools for:
- landscape authoring;
- procedural biomes;
- paths/spline networks.

Its current product material emphasizes:
- large-scale generation;
- GPU/multithreaded processing;
- manual artistic control;
- World Partition / PCG / Nanite integration;
- biome debugging and mask visualization.

### Potential project value
The interesting part is not replacing SpeedTree or Houdini. It is whether **biome iteration/debugging is substantially faster than our PCG-only workflow**.

Potential architecture:

```text
SpeedTree assets
 + Houdini semantic masks
 -> Errant Biomes OR UE PCG
 -> final UE instances
```

### Benchmark
Use one SpeedTree micro-biome with three semantic masks:
- moisture;
- wind exposure;
- Monolith proximity.

Recreate it in Errant Biomes and current UE PCG.

Keep Errant only if the iteration/debugging benefit is large enough to justify another worldbuilding dependency.

---

## 10. RealityScan 2.2 + RealityScan Mobile

RealityScan desktop 2.2 shipped in June 2026 and the mobile app continues to update. It is particularly attractive as a **source-data acquisition tool**, not as a final-style generator.

Potential Melodia uses:
- scan bark / stone / cloth / damaged architecture / shore material;
- capture real erosion and surface irregularity;
- produce geometry to analyze procedurally in Houdini;
- extract physically plausible source maps and then stylize them;
- rapid scale/reference captures for environment art.

Suggested flow:

```text
real object / location
 -> RealityScan
 -> Houdini cleanup / decomposition / masks
 -> Copernicus / Substance stylization
 -> Nanite or derived authored asset
```

Do not let photogrammetry dictate Melodia's painterly style. Use reality as **data**, not final appearance.

---

## 11. SuperSplat + PlayCanvas 2026 Gaussian stack

SuperSplat's 2026 releases added significant production-oriented Gaussian-splat tooling:
- WebGPU rendering;
- streamed LOD;
- walk mode / voxel collision;
- collision generation;
- huge-scene streaming;
- SPZ export;
- proxy-assisted relighting examples;
- downloadable web-app starter projects.

PlayCanvas demonstrates a 250M-splat city streamed with LOD in Engine 2.20 examples.

### Melodia role
Not shipping gameplay geometry.

Use splats for:
- location/reference capture;
- remote art review;
- rapid spatial ideation from scans;
- preserving a real reference environment before heavily stylizing/remodeling it;
- browser-shareable reference scenes.

A useful research chain is:

```text
RealityScan / video
 -> Postshot or compatible reconstruction
 -> SuperSplat cleanup / streaming
 -> reference / remote review
 -> Houdini / UE authored production asset
```

---

# Tier B — specialized workflow candidates

## 12. InstaMAT

InstaMAT is a material/texturing system with procedural graphs, 3D painting, GPU processing and DCC integrations. Its January 2026 integration update explicitly lists Unreal 5.7.1 support; UE5.8 support must therefore be checked rather than assumed.

Potential value:
- another geometry/material automation layer;
- graph synchronization / instances;
- scalable asset texturing;
- C++ SDK / pipeline automation.

Problem: Melodia already has Substance + Copernicus. InstaMAT must beat one of them at a specific task, not merely be another material editor.

Suggested benchmark: one reusable wardrobe trim/material family with ten parameterized variants and UE round-trip.

---

## 13. Material Maker

Material Maker launched on Steam in July 2026 and remains an open-source procedural material / model-texturing tool with Unreal export.

Useful as:
- low-cost/open fallback;
- portable procedural texture graph editor;
- shader/material prototyping outside Adobe licensing.

Likely not worth adding if Substance + Copernicus already cover the job faster.

---

## 14. ArmorPaint

ArmorPaint remains an unusually capable lightweight/open-source painting stack:
- GPU painting;
- ray-traced baking;
- path-traced viewport;
- node materials/brushes;
- Unreal live-link plugin;
- local neural image/material tools.

Potential role is not replacing Substance blindly. Benchmark whether its **instant GPU bake + paint loop** could replace part of the Toolbag/Painter round-trip for small assets.

---

## 15. Style3D Atelier + Style3D Simulator

Style3D's current marketing describes a GPU fashion pipeline with Atelier garment authoring and a proprietary realtime Unreal cloth simulator capable of multilayer garments and cache recording.

This is conceptually extremely relevant to an outfit-heavy game.

However there is a compatibility red flag:
- current Fab listing states Simulator support through UE5.4;
- other Style3D material describes broader UE5 support.

For Melodia UE5.8, **do not buy/build around this until the vendor confirms a compatible build or source path**.

If 5.8 becomes supported, benchmark a layered skirt/coat against Chaos Cloth rather than swapping the full pipeline.

CLO/Marvelous remain established garment-authoring options; Style3D must demonstrate a simulation advantage, not just similar pattern tools.

---

## 16. Autodesk Flow Studio

Flow Studio's 2026 releases include:
- AI mocap improvements;
- 3D Editor for characters/cameras/scenes;
- FBX/USD-oriented motion exports;
- AI rigging for generated characters;
- scene/camera editing and cinematic workflows.

Potential Melodia use:
- rough cinematic blocking from live-action footage;
- camera/motion extraction;
- non-final NPC/shot ideation.

Not a hero-animation authority. Compare to Rokoko Vision for raw motion acquisition; keep the simpler/faster path.

---

# Tier C — low-level frameworks and future renderer infrastructure

## 17. NVIDIA Warp

Warp is an open-source Python framework that JIT-compiles numerical kernels for CPU/GPU and includes geometry-processing / physics primitives. Kernels can be differentiable and integrate with ML frameworks.

### Why a Houdini/UE developer should care
It provides a lightweight way to prototype custom field/simulation ideas without writing a full Unreal plugin or building a Houdini DOP network first.

Possible R&D uses:
- million-particle Monolith field experiments;
- custom attraction / flow / pressure models;
- optimization of authored Wayfold/filter fields;
- signed-distance / geometry analysis;
- offline data generation baked into UE textures/point caches.

Do not ship Warp as gameplay runtime. Treat it as a Python **simulation notebook accelerator**.

---

## 18. Taichi Lang + AMD Simulation / GSplat

AMD's Simulation toolkit began shipping Taichi Lang and GSplat components, exposing GPU numerical simulation / Gaussian workflows on ROCm.

Taichi is another Python-embedded GPU-compute language for high-performance simulation.

For Melodia it occupies almost the same research slot as Warp.

Decision: do not adopt both. If custom GPU simulation research becomes necessary, benchmark Warp vs Taichi on one field-generation problem and keep the tool that matches local hardware / Python ergonomics.

---

## 19. Slang shading language

Slang is now Khronos-hosted and is designed as a cross-platform shading language/compiler targeting modern realtime graphics and neural graphics. Current tooling can target APIs such as Direct3D and Vulkan, and Slang's differentiable-programming capabilities are relevant to research renderers.

### Why it matters
If Melodia ever leaves UE's material graph for **renderer R&D**, Slang is more strategically interesting than committing directly to hand-written HLSL tied to one experimental backend.

Do not alter production UE materials for this.

---

## 20. NVIDIA RTX Neural Shading SDK (RTXNS)

RTXNS is now public and demonstrates training/inference for neural shader/texture representations using Slang and GPU cooperative-vector capabilities.

This turns "neural shaders" from a vague roadmap idea into code that can actually be studied.

Potential long-term experiments:
- approximate expensive pearlescent/fabric responses;
- compress complex texture functions;
- explore learned material representations.

Current status: **standalone renderer lab only**. No shipping dependency.

---

## 21. OpenUSD 26.x + Hydra 2 + MaterialX

OpenUSD continues moving toward a more explicit Hydra 2 scene-index architecture, while MaterialX can be translated through USD/Hydra into renderer material networks.

For Melodia the practical value is **pipeline interchange**, not replacing Unreal:
- layered Houdini scene exchange;
- sim/cache interchange;
- material-description experiments;
- predictable interchange between future tools.

Potential policy:
- use USD where layered scene/animation/simulation semantics are valuable;
- continue using simpler FBX/Alembic/texture exports where USD adds no value.

Do not introduce USD complexity merely for prestige.

---

## 22. Hydra Merlin — the actual trench

`hydra-merlin` is an emerging open-source Hydra renderer built around Vulkan/Metal. Its roadmap/work includes:
- Hydra 2;
- MaterialX -> Slang material compilation;
- Gaussian rendering;
- GPU-driven resource systems;
- streamed/LOD Gaussian work.

This is not a Melodia production renderer.

It is valuable as **living reference code** for understanding where USD/Hydra, MaterialX, Slang and Gaussian rendering are converging outside large proprietary engines.

Keep bookmarked for renderer education / experiments only.

---

## 23. Omniverse Kit SDK

NVIDIA's Kit SDK remains a framework for building custom OpenUSD applications with Python/C++, rendering, physics and extension systems.

Melodia does not need another engine, but Kit becomes interesting if the project eventually needs a custom **asset-review / batch-processing / USD inspection application** shared across DCCs.

No action until a real tool cannot be solved more cheaply with Python/Houdini/UE editor utilities.

---

## 24. Abstract RSX Engine / Polyverse / InstaLOD ecosystem

Abstract is moving several tools toward broader 2026 release:
- **RSX Engine** — WebGPU/browser-native collaborative 3D editor/engine with automatic cloud versioning;
- **Polyverse** — cloud asset management / processing workflows;
- **InstaLOD** — automated optimization and conversion;
- **InstaMAT** — material/texturing.

### Melodia read
RSX is interesting as evidence that browser-native multi-user 3D editing is maturing, but Unreal remains the runtime/editor authority.

Polyverse is only interesting if current Git/Perforce/asset workflows develop a concrete processing/review bottleneck.

InstaLOD becomes interesting for:
- batch collision/proxy/LOD generation outside Nanite cases;
- scan cleanup/optimization;
- skeletal/mobile/platform fallback assets.

Do not buy an ecosystem to solve a problem we do not yet have.

---

# Reddit / community trench leads that require verification

## Fluid Forge

A small Unreal developer has been publicly showing an upcoming `Fluid Forge` plugin in 2026, including shallow-water simulation, foam/whitewater and GPU-particle visualization. Community posts indicate a planned Fab release.

This is **not production-vetted yet**.

Watch because:
- its shallow-water solver may be simpler/more specialized than FluidNinja;
- it could become useful for streams/coasts if documentation/performance are strong.

No project integration until a stable public build exists.

---

## Prismatiscape Interaction Plugin

Existing UE5 interaction system based on Niagara Grid2D + Runtime Virtual Textures with foliage/water/wind/surface simulations and pivot-paint tooling.

It is older than this sweep's "new release" focus but remains relevant as a comparator for:
- Advanced Environment Interaction;
- FluidNinja;
- project-owned interaction fields.

Do not adopt three interaction frameworks. Use Prismatiscape as a benchmark/reference.

---

# Newly discovered architecture opportunities

## A. The Melodia World Field Bus

Multiple independent tools keep converging on the same primitive:

> a spatial field that stores direction / density / pressure / contact / state, then many presentation systems read it.

Rather than allowing every plugin to invent its own world truth, Melodia should formalize a small common contract.

Candidate conceptual fields:

```text
WorldField.FilterFlow
WorldField.Tension
WorldField.Moisture
WorldField.Contact
WorldField.Residue
WorldField.Reaction
WorldField.AnchorStability
WorldField.Resonance
```

Possible representations depend on scale:
- scalar/vector parameters for local targets;
- Material Parameter Collections for global low-bandwidth values;
- render targets / RVTs for local spatial history;
- Niagara grids / simulation stages for transient local fields;
- Houdini-authored textures/vector fields for static macro behavior;
- PCG metadata for persistent ecological interpretation.

**Do not build a giant generalized field framework tomorrow.**

Use the R&D tools to discover the minimum contract shared by P1/P2/P3.

---

## B. Wardrobe pipeline should be a ladder, not one solver

The deeper fashion research suggests a scalable wardrobe stack:

```text
CLO / Marvelous / donor mesh
        |
        +-> MetaTailor quick conform/skin candidate
        |
        +-> Houdini deformation + intersection audit
        |
        +-> authored correction / sculpt
        |
        +-> UE outfit-definition container
                |
                +-> skeletal secondary motion
                +-> Chaos Cloth hero regions
                +-> WPO cheap regions
                +-> Houdini/Vellum/VAT cinematic or giant cloth
```

Style3D Simulator becomes an optional future runtime-cloth competitor only if UE5.8 support exists and it clearly beats Chaos for one garment class.

This mirrors the Infinity Nikki lesson: different garment categories deserve different simulation solutions.

---

## C. Capture should feed stylization, not fight it

RealityScan + splats are valuable even for a painterly fantasy game because they give us **truthful source data quickly**.

Example:

```text
scan real eroded bark
 -> derive macro cracks / fiber statistics
 -> Houdini exaggerates pattern
 -> Copernicus produces stylized masks
 -> Substance paints final art direction
 -> SpeedTree/Houdini use pattern structurally
```

The point is not photorealism. The point is avoiding having to invent every natural irregularity from zero.

---

# Revised priority board

## Test immediately / as soon as compatible
1. Copernicus
2. Unreal MCP
3. IlluGen
4. **MetaTailor**
5. **FluidNinja LIVE-2**
6. Cascadeur + **Rokoko Vision 3.0** pair
7. UE5.8 Mesh Terrain
8. **Advanced Environment Interaction**
9. Dash
10. RealityScan 2.2

## Compare before adding
- GeoGen vs Gaea vs World Creator;
- VectorayGen vs Houdini vector fields;
- Errant Biomes vs UE PCG;
- MetaTailor vs Houdini/manual fitting;
- Advanced Environment Interaction vs project-owned RT/RVT interaction;
- ArmorPaint vs Toolbag/Painter for small-asset bake/paint;
- InstaMAT vs Substance/Copernicus;
- Flow Studio vs Rokoko Vision for motion extraction.

## Watch for UE5.8 / maturity
- Style3D Simulator;
- Voxel Plugin 2;
- Fluid Forge;
- UE Chaos Outfit custom-character usage;
- Procedural Vegetation Editor.

## Research lab only
- NVIDIA Warp / Taichi;
- Slang;
- RTXNS;
- RTX Kit / Mega Geometry;
- OpenUSD/Hydra 2/MaterialX infrastructure;
- Hydra Merlin;
- Omniverse Kit;
- RSX Engine;
- Procedura;
- Magpie.

---

# Tomorrow: revised first-hour plan

Do **not** start by installing everything.

### 0:00–0:15 — compatibility matrix
Record whether each candidate supports the project's exact UE5.8 build and whether it is editor-only, source-available, binary-only or external-authoring-only.

### 0:15–0:45 — wardrobe accelerator test
If available:
- MetaTailor trial;
- existing Melusina body/skeleton;
- one donor garment;
- export provisional fitted/skinned mesh;
- compare to current manual/Houdini path.

### 0:45–1:30 — world-field test
Try FluidNinja LIVE-2 beta **or**, if exact compatibility is uncertain, Advanced Environment Interaction in a disposable project.

Goal is not pretty water. Goal is one spatial field driving two independent presentation systems.

### Next
Resume original priority schedule:
- Copernicus;
- IlluGen;
- Unreal MCP;
- Cascadeur/Rokoko;
- Mesh Terrain;
- remaining comparator tools.

---

# Final trench rule

The most important pattern in this survey is not any individual app.

The industry is converging on:

```text
procedural authoring
+ shared spatial fields
+ GPU local simulation
+ data-oriented garment assembly
+ cheap capture / neural reconstruction
+ increasingly programmable/neural renderers
```

Melodia can exploit that direction without becoming dependent on it.

> **Use exotic tools to manufacture evidence. Bake the evidence into boring, inspectable Unreal assets whenever possible.**
