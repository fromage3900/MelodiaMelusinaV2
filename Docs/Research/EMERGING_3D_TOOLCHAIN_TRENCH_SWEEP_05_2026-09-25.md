# Emerging 3D Toolchain — Trench Sweep 05

**Date:** 2026-09-25  
**Project:** Melodia Melusina / Unreal Engine 5.8  
**Status:** repo-aware procedural-worldbuilding R&D delta; bounded canaries only  
**Companion authority:** `CURRENT_STATE.md`, `Docs/Production/PCG/README.md`, `Docs/Production/AGENT_PRODUCTION_PLAYBOOK.md`

---

## Executive result

This sweep intentionally starts from the current Melodia production baseline instead of rediscovering generic procedural-worldbuilding techniques.

The project already has a mature procedural spine:

- World Compiler is the canonical authored worldbuilding path.
- UE 5.8 PCG + PCGEx are already production infrastructure.
- PCG Python semantic enrichment is already proven and documented.
- Resonance is already packed into per-instance custom data and consumed by presentation/material lanes.
- Houdini/Hython is already canonical as a deterministic offline DCC forge.
- Copernicus is already present as a texture/mask/material-generation lane.
- Mesh Terrain already has an explicit Melodia P0 source/import contract and deterministic DEM source tooling.
- broad new procedural architecture is currently parked / consume-only unless a named blocker cannot be expressed through an existing owner.

Therefore the useful frontier is no longer “add procedural generation.” It is:

> **increase artist control, fidelity, scale, and iteration speed without introducing a second world authority.**

The strongest immediate candidates are:

1. UE 5.8 PCG Manual Editing / Data Overrides;
2. Houdini 22 COP HDA live texture iteration inside Unreal;
3. local-statistics anti-tiling for large authored surfaces;
4. iso-contour terrain authoring as an artist-first source representation.

Everything else below remains a bounded offline or disposable canary.

---

# 0. Repo-aware baseline — do not recommend these as new work

Verified against current `main` before this sweep.

## PCG Python semantic processing is solved

Canonical contract:

`Docs/Production/PCG/README.md`

Validated path:

```text
existing point source / authored biome graph
  -> PCGPythonDataProcessor
       Resonance
       EcologyClass
       MaterialVariant
       ScaleBias
  -> native PCG
  -> PCGStaticMeshSpawner
  -> PCGInstanceDataPackerByAttribute
  -> per-instance custom data
  -> material / presentation response
```

Canonical implementation:

- `Content/Python/pcg/resonance_ecology_processor.py`
- `Content/Python/pcg/apply_resonance_to_sea_above.py`
- `Content/Python/pcg/test_resonance_ecology.py`

Recorded production evidence includes a 140-instance Sea Above proof with Resonance custom data and a larger 6,835-instance generic proof.

**Research consequence:** do not propose “try PCG Python,” “semantic metadata,” “Python material variation,” or “per-instance material control” as novel experiments.

## World Compiler / Morning ecology presentation is already live-proven

`CURRENT_STATE.md` records the 2026-09-19 `L_MelusinaMorning` World Compiler closeout with Brushify/SpeedTree meadow dressing and the subsequent Niagara/user-parameter presentation pass.

**Research consequence:** generic procedural scattering, ecosystem dressing, and “PCG + Niagara” tutorials are below the current project baseline.

## Houdini/Hython is already canonical

`Docs/Production/AGENT_PRODUCTION_PLAYBOOK.md` defines Houdini/Hython as the deterministic DCC forge for geometry, masks, Copernicus textures, fields, caches, variants and offline processing.

**Research consequence:** do not propose Houdini as a second live world compiler or generic “Houdini -> Unreal” integration project.

## Mesh Terrain is already in the project research stack

Existing Melodia work:

- `Docs/WorldGen/MESH_TERRAIN_GAEA_DEM_P0.md`
- `Content/Python/melodia_mesh_terrain_source.py`
- `Docs/WorldGen/TERRAIN_HANDOFF_CONTRACT.md`

The project already has a deterministic real-world/Gaea -> metric mesh -> UE 5.8 Mesh Terrain source path and an explicit “no classic Landscape” guard for that P0.

**Research consequence:** Mesh Terrain itself is not a new discovery. Future Mesh Terrain work must test a capability not already represented, such as topology-aware PCG interaction or production viability.

---

# 1. UE 5.8 PCG Manual Editing / Data Overrides — TEST NOW

Epic added non-destructive manual editing of generated PCG data/artifacts in UE 5.8, including selection, exclusion, modification, restore behavior, manually editable nodes, and a Data Overrides panel.

This is Experimental, so it is not a production-policy change yet.

Official source:

- https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes
- https://dev.epicgames.com/documentation/unreal-engine/pcg-editor-mode-in-unreal-engine

## Why this matters to Melodia

The unsolved problem is not generation density. It is the last-mile environment-art question:

> Can authored PCG remain regenerable while Brennan manually protects hero negative space, sightlines, silhouettes and individual placements?

This is directly aligned with the current production-phase shift toward visible authored places rather than more architecture.

## Canary

`Morning_PCG_ArtDirectionOverride_Canary`

Target one existing flower/meadow output in `L_MelusinaMorning`.

1. mark only the final artist-facing placement/output node for manual editing;
2. manually exclude or move approximately 10–20 instances;
3. create one deliberate camera/traversal corridor or hero-frame negative-space adjustment;
4. regenerate upstream PCG;
5. change the upstream seed;
6. reload the map;
7. inspect the Data Overrides panel;
8. verify Restore returns cleanly to generated state.

## Pass condition

- authored exceptions survive the intended regeneration path;
- upstream procedural changes still work;
- overrides remain inspectable and reversible;
- no detached duplicate placement authority is created;
- source-control behavior is understandable.

## Fail / park condition

Park if overrides are brittle across graph edits, opaque in source control, or harder to reason about than an authored exclusion/source-data layer.

---

# 2. Houdini 22 Copernicus HDA inside Unreal — TEST NOW

Houdini 22's Unreal plugin supports Unreal 5.7/5.8 and now supports Copernicus HDAs in the asset editor and regular world.

SideFX documents:

- 2D COP HDA asset-editor preview;
- editable resolution, pixel scale and data format;
- HDA inputs and exposed parameters;
- generated texture outputs;
- generated Material Instances from a chosen source Unreal material;
- recook/rebuild and bake workflows;
- common output naming such as basecolor, normal, roughness, metal, emissive, height/displacement and RMA.

Official sources:

- https://www.sidefx.com/docs/houdini/unreal/copernicus.html
- https://www.sidefx.com/docs/houdini/news/22/engine.html

## Why this is genuinely new relative to the existing Melodia COP lane

Melodia already uses `Tools/Houdini/copernicus/` and Hython for deterministic batch output.

The new question is narrower:

> Can a small Copernicus family become an interactive Unreal-side texture forge without changing material authority?

This could reduce the edit -> export -> import iteration loop for lookdev while leaving Hython as the deterministic batch/evidence path.

## Canary

`COPHDA_MelodiaSurface_Canary`

Package one existing bounded Copernicus surface family as a COP HDA.

Expose only a small artistic control set, for example:

- pattern scale;
- resonance/cymatic strength;
- pearl/roughness breakup;
- edge or fiber response;
- seed.

Outputs:

- BaseColor;
- Normal;
- RMA or separate Roughness/Metal/AO;
- Height where useful.

In Unreal:

1. import/open the COP HDA;
2. connect outputs to an existing Melodia source Material / Material Instance workflow;
3. change parameters;
4. recook;
5. bake;
6. verify generated textures survive the expected save/reload workflow.

## Pass condition

Interactive parameter -> recook -> baked texture -> existing Melodia material iteration is materially faster than the current manual round trip.

## Boundary

COP HDA does not become a new material master, runtime shader authority, or world compiler.

---

# 3. Terrain Synthesis and Authoring based on Iso-Contours — TEST SOON

**Paper:** Benoît Huftier, Hugo Schott, Eric Galin, Oscar Argudo, Adrien Peytavie, Eric Guérin.  
**Computer Graphics Forum / Eurographics 2026.**  
First published 2026-04-30.  
DOI: https://doi.org/10.1111/cgf.70389

Project/source page:

https://h-schott.github.io/p/isos/

The paper represents terrain with nested vector iso-contours rather than making the artist begin with a dense elevation grid. The contour representation supports direct editing such as warping, slope modulation and smoothing, then reconstructs a standard terrain representation suitable for downstream processing such as erosion.

## Melodia takeaway

Do not add another terrain system.

Steal the **authoring representation**.

For hero traversal spaces, a handful of meaningful contour shapes may provide better composition control than beginning from noise/erosion parameters.

Potential authored structures:

- coastline;
- basin;
- ridge;
- plateau;
- Heart Gate approach;
- Sea Above shelf;
- controlled traversal valley.

## Canary

Build a tiny Hython/Houdini contour-authoring proof for one bounded Faraway Mother or Sea Above tile:

1. author roughly 5–8 closed contour splines;
2. assign elevations;
3. reconstruct/rasterize a height representation;
4. run existing erosion/detail processing afterward;
5. hand the result to the existing terrain handoff / Mesh Terrain lane.

## Question

Can the owner establish macro-composition faster and more intentionally than with a noise-first/Gaea-first terrain start?

If yes, this becomes a **source-authoring technique**, not a new terrain authority.

---

# 4. Real-time by-example texture synthesis using local statistics exchange — TEST SOON

**Paper:** Nicolas Lutz, Guillaume Gilet.  
**Computer Graphics Forum, 2026.**  
First published 2026-05-13.  
DOI: https://doi.org/10.1111/cgf.70355

The research targets real-time by-example synthesis/filtering for large surfaces while reducing visible repetition. The key useful idea for Melodia is exchanging local statistical characteristics between regions/tiles rather than relying only on ordinary UV offsets, macro-noise or simple random tinting.

## Why Melodia cares

Candidate surfaces:

- velvet/textile terrain;
- pearly cloth geology;
- coral/reef surfaces;
- broad stylized stone;
- silk mountains;
- large decorative surfaces with recognizable islands/motifs.

The project already has sophisticated triplanar, layered, Nikki, SDF and material-variation infrastructure. The problem worth attacking is **recognizable repetition at large scale**, not lack of variation controls.

## Canary

`MF_LocalStatsBreakup_Prototype`

Do not port the full paper first.

Use one troublesome exemplar and a lightweight region/ID segmentation.

Prototype an HLSL/material-function approximation that exchanges or remaps some combination of:

- local mean/color;
- contrast/variance;
- orientation/region transform;
- region selection.

Compare directly against the current Melodia world-aligned/triplanar/randomization path from the same camera.

## Pass condition

It meaningfully reduces tiling recognition while preserving authored motifs and remains cheap enough for the intended surface class.

---

# 5. Stochastic geomorphological transport for terrain erosion simulation — OFFLINE R&D

**Paper:** Nicholas McDonald, Guillaume Cordonnier.  
**ACM Transactions on Graphics 45(4), Article 78, 2026.**  
Published 2026-07-03.  
DOI: https://doi.org/10.1145/3811336

This work models terrain erosion through stochastic geomorphological transport.

## Melodia role

Do not replace Gaea.

The useful question is whether the method produces better **transport/deposition evidence** for downstream ecology/material logic:

- drainage hierarchy;
- braided channels;
- sediment accumulation;
- deposition masks;
- flow fields;
- delta structure.

## Canary

One 512 m offline terrain tile:

1. same starting heightfield for both paths;
2. current Gaea/Houdini erosion baseline;
3. stochastic-transport-inspired implementation/adaptation;
4. compare drainage, sediment/deposition fields and scale stability;
5. evaluate whether the masks are more useful to PCG/material consumers even if the final heightfield is not better.

## Promotion rule

Only promote a derived algorithm or field if it improves an existing Hython/Gaea source lane. Do not introduce a second terrain toolchain.

---

# 6. InfiniteDiffusion / Terrain Diffusion — RESEARCH ONLY

**Paper:** Alexander Goslin.  
**SIGGRAPH 2026.**  
DOI: https://doi.org/10.1145/3799902.3811080

Project/code:

- https://xandergos.github.io/terrain-diffusion/
- https://github.com/xandergos/terrain-diffusion

InfiniteDiffusion is interesting because it targets learned generation while retaining procedural-noise-like properties including unbounded generation, deterministic seed behavior and random spatial access.

## Why it is strategically interesting

Those properties resemble the reproducibility expectations behind Universe Foundry and deterministic world compilation.

## Why it is not a production candidate

Melodia already has explicit world-authoring and persistence authorities. A learned infinite terrain generator would create an unnecessary competing world source if introduced directly.

## Canary

Offline inspiration only:

1. fixed seed;
2. fixed coordinate addresses;
3. generate four neighboring tiles;
4. check seam/coherence behavior;
5. revisit the same coordinates and verify reproduction;
6. export only candidate height/mask/reference data if artistically useful.

The system may generate **possibilities**; it may not author canonical world state.

---

# 7. Toward Richer Material Generation via Procedural Data Enhancement — PATTERN QUARRY

**Paper:** Yunchen Yu, Jacob Munkberg, Jon Hasselgren, Chris Cummings, Steve Marschner, Andrea Weidlich.  
**SIGGRAPH 2026.**  
DOI: https://doi.org/10.1145/3799902.3811210

NVIDIA project:

https://research.nvidia.com/labs/rtr/publication/yu2026toward/

The paper procedurally enriches simple PBR materials with physically motivated multi-lobe effects such as dust, clearcoat and layered scattering, then compresses the richer response into a neural representation.

## Melodia takeaway

Do **not** implement the neural material runtime now.

The immediately useful idea is representation discipline:

> keep visually meaningful non-diffuse phenomena as distinct physical/semantic layers rather than hiding every effect inside one giant artistic parameter soup.

Potential existing Melodia consumers:

- pearl/ceramic response;
- clockwork clearcoat;
- fine dust/ecological accumulation;
- iridescent shell;
- textile/fiber sheen;
- wet film;
- thin/translucent layering.

Use the paper as a lookdev/material-model reference when simplifying or extending existing master materials.

---

# 8. GPU PCG / Custom HLSL — BENCHMARK GATE, NOT NEW ARCHITECTURE

The canonical PCG production contract already says Python Data Processor should remain bounded authoring-time enrichment and that very dense ecologies / Python-bound graphs should prefer native/GPU PCG or baked data.

Therefore GPU PCG is not a new system proposal.

## Trigger

Only benchmark when profiling shows a real point-count or Python-cost blocker.

Suggested thresholds remain practical rather than doctrinal:

- 10k;
- 100k;
- 500k points.

Use one existing cymatic/ecology field calculation and preserve the same semantic consumer contract.

## Pass condition

A measured editor/runtime improvement at relevant density without creating CPU/GPU transfer churn or a second semantic implementation.

---

# 9. Explicit skip list for future research sweeps

Unless current Git evidence changes, do not surface these as “new Melodia experiments”:

- PCG Python Data Processor basics;
- semantic PCG metadata;
- Resonance -> material variation;
- per-instance custom-data material control;
- generic procedural foliage scatter;
- basic Houdini -> Unreal bridges;
- generic Hython automation;
- procedural Niagara dressing;
- “use cymatics to vary materials”;
- Mesh Terrain merely existing;
- Gaea/DEM -> terrain source generation;
- another World Compiler;
- another persistent field/world authority.

A future paper/tool should clear at least one of these bars:

1. materially improves artist control;
2. improves visible fidelity;
3. removes a measurable production bottleneck;
4. improves deterministic evidence/rebuild quality;
5. enables a bounded geometry/material capability not represented by current owners.

---

# 10. Immediate experiment queue

Current production policy says broad procedural expansion is parked, so this is an **R&D queue**, not an instruction to execute all items.

## A — highest value

**PCG Manual Editing / Data Overrides in `L_MelusinaMorning`**

Goal: prove procedural regeneration and hand-composed hero placement can coexist.

## B

**COP HDA -> Unreal live texture canary**

Goal: shorten texture lookdev iteration while retaining existing material authority.

## C

**Local-statistics anti-tiling shader**

Goal: improve one large Melodia surface where repetition is visible.

## D

**Iso-contour terrain source sketch**

Goal: test whether artist-first terrain composition is faster than noise-first macroform authoring.

## Park until a named need

- stochastic erosion;
- InfiniteDiffusion;
- neural material representation;
- GPU PCG scale work without profiling evidence.

---

# Doctrine

> **Melodia does not need more procedural systems. It needs the existing procedural systems to become easier to art-direct, richer in visible result, and cheaper to iterate.**

The preferred research pattern is now:

```text
new paper / engine feature
    -> compare against current Git baseline
    -> isolate one missing capability
    -> build one bounded canary
    -> consume existing owners
    -> visual / performance / determinism evidence
    -> ADOPT / PARK / REJECT
```

Any proposal that begins by inventing a new world authority has failed the filter before implementation.
