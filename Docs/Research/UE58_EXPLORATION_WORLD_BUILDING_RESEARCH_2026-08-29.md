# UE 5.8 Exploration + Large-World Systems Research

**Date:** 2026-08-29  
**Status:** production-oriented research handoff; verify all project-local plugin APIs before implementation  
**Scope:** systems useful for Melodia Melusina P0–P3 exploration, authored Monolith encounters, party investigation, and eventual large-world production.

---

## Executive decision

Melodia does **not** need a giant third-party exploration framework right now.

The strongest stack for the next production phase is mostly native Unreal Engine 5.8:

- World Partition + Data Layers + HLOD for large authored regions and alternate world states;
- Level Instances / Packed Level Actors for repeated static assemblies and points of interest;
- PCG for editor-authored ecological distribution, with hierarchical/runtime generation investigated later rather than made mandatory now;
- Gameplay Tags as the common vocabulary for exploration observations and interaction capabilities;
- StateTree for local encounter/companion state orchestration where ordinary Blueprint state logic starts becoming unwieldy;
- Niagara + project Effect Types for environmental response at scale;
- MetaSounds / Audio Modulation for resonance, pressure, distant anatomy, and rhythm-reactive ambience;
- local MIDs / existing rhythm subsystem for chapter-specific material responses;
- simple interaction interfaces/components before GAS, Smart Objects, or generalized chemistry/spatial frameworks.

The recurring architecture rule is:

> **Author the impossible interaction first. Generalize only after the same interaction pattern appears in at least two or three chapters.**

This is especially important for P1 Faraway Mother, P2 God That Molts, and P3 Horizon Eater.

---

# 1. Native UE 5.8 systems worth adopting

## World Partition

**Recommendation:** use for genuinely large contiguous production maps, not automatically for every small prototype map.

UE 5.8 documents World Partition as automatic distance-based streaming of a single persistent world split into grid cells. It works directly with Data Layers, HLODs, and streaming sources.

Use for:
- broad P3 highland / horizon compositions;
- distant Monolith-scale landmarks that must remain visible through HLOD;
- eventual regional traversal between authored points of interest;
- keeping editor collaboration manageable with One File Per Actor.

Do not convert a stable small P0/P1 prototype merely to satisfy architecture purity.

Official docs:  
https://dev.epicgames.com/documentation/unreal-engine/world-partition-in-unreal-engine

---

## Runtime Data Layers

**Recommendation:** very high value for Melodia.

UE 5.8 allows runtime Data Layers to be loaded/activated from Blueprint or C++ and explicitly cites gameplay progression and elaborate world transitions as intended uses.

Best Melodia uses:
- `DL_P2_DormantMolt` / `DL_P2_CatalyzedMolt` for authored geological-to-biological reveals;
- `DL_P3_NormalHorizon` / `DL_P3_FilterGape` / `DL_P3_WayfoldState` for large spatial reveals;
- optional-before / optional-after ecological states;
- replacing whole expensive static configurations without keeping every version live.

Use Data Layers for **large authored state changes**, not individual small interactions.

Official docs:  
https://dev.epicgames.com/documentation/unreal-engine/world-partition---data-layers-in-unreal-engine

Blueprint runtime state API:  
https://dev.epicgames.com/documentation/unreal-engine/BlueprintAPI/DataLayers/SetDataLayerRuntimeState

---

## HLOD

**Recommendation:** essential once P3 or any landscape-scale Monolith composition becomes real production content.

World Partition HLOD replaces unloaded distant actors with proxy meshes/materials. This is directly useful for Melodia because Monoliths should often be perceived as enormous silhouettes and synchronized landscape behavior rather than fully simulated actors.

Use separate HLOD policy for:
- ordinary ecology;
- distant architecture;
- Monolith-scale static anatomy / shell / horizon silhouettes.

The P3 filter-feeder should be mostly static/HLOD-compatible geometry until the final authored gape event.

Official docs:  
https://dev.epicgames.com/documentation/unreal-engine/world-partition---hierarchical-level-of-detail-in-unreal-engine

---

## Level Instances + Packed Level Actors

**Recommendation:** use now for reusable static encounter assemblies.

Level Instances are production-ready and work with World Partition/Data Layers. Packed Level Blueprints are optimized for dense static mesh assemblies, but are not appropriate when the assembly needs arbitrary non-static components or behavior.

Good uses:
- P2 repeated shed-layer cliff formations;
- P3 survey towers / wind instruments / ruin clusters;
- recurring field camps;
- reusable environmental clue assemblies.

Keep active gameplay logic outside a Packed Level Actor in a normal Blueprint director/interaction actor.

Official docs:  
https://dev.epicgames.com/documentation/unreal-engine/level-instancing-in-unreal-engine

---

## PCG Framework

**Recommendation:** editor-time PCG is a strong near-term win; runtime hierarchical generation is a later optimization/tooling lane.

UE 5.8 PCG supports non-partitioned, partitioned, hierarchical, and runtime generation. Runtime generation can use player or World Partition streaming sources, and hierarchical generation allows large features on coarse grids and detail on small grids.

Immediate uses:
- P2 fungal colonization, moss, roots, insect habitat markers, shed-flake scatter;
- P3 grassland ecology, migration traces, distant wind flora, pollen zones;
- authored spline/volume exclusion around hero reveals.

Preferred rule:
- build the hero encounter by hand;
- let PCG fill **supporting ecology**, not determine the critical reveal composition.

Official docs:  
https://dev.epicgames.com/documentation/en-us/unreal-engine/pcg-development-guides  
https://dev.epicgames.com/documentation/en-us/unreal-engine/using-pcg-generation-modes-in-unreal-engine

### PCG Biome Core

UE 5.8 documents PCG Biome Core as **Experimental**. Treat it as a reference/sample architecture rather than a production dependency until it proves stable in the project's local 5.8 build.

Do not rebuild the world pipeline around it for P0–P3.

Official docs:  
https://dev.epicgames.com/documentation/unreal-engine/procedural-content-generation-pcg-biome-core-and-sample-plugins-overview-guide-in-unreal-engine

---

## Gameplay Tags

**Recommendation:** adopt as the vocabulary layer for exploration, even without GAS.

Gameplay Tags are hierarchical labels and work well for capability/observation matching without hard-coding character classes into every interaction.

Suggested taxonomy:

```text
Explore.Channel.Relationship
Explore.Channel.Measurement
Explore.Channel.Material
Explore.Channel.Resonance
Explore.Channel.Tactile

Explore.Capability.Stitch
Explore.Capability.Survey
Explore.Capability.Anchor
Explore.Capability.Catalyze
Explore.Capability.Wayfold
Explore.Capability.ResonanceCall
Explore.Capability.TactileTest

Explore.Clue.Tension
Explore.Clue.LayerAge
Explore.Clue.Residue
Explore.Clue.Distance
Explore.Clue.FilterFlow
Explore.Clue.BiologicalResponse
```

An interaction target can expose required/optional tags without knowing whether Mara, Iris, Melusina, Sir Melodious, or Ebenezer is executing the observation.

Official docs:  
https://dev.epicgames.com/documentation/unreal-engine/using-gameplay-tags-in-unreal-engine

---

## StateTree

**Recommendation:** use selectively for encounter directors and companions once a state graph exceeds a simple Blueprint enum.

UE 5.8 describes StateTree as a performant hierarchical state machine combining selectors with explicit states/transitions.

Strong uses:
- `ST_GodThatMolts_Encounter`;
- `ST_HorizonEater_Encounter`;
- Ebenezer behavior (`Perched -> Investigate -> Test -> React -> Return`);
- Sir Melodious response states;
- lightweight Iris/Mara contextual investigation behavior.

Do **not** make every clickable exploration object own a StateTree.

Official docs:  
https://dev.epicgames.com/documentation/unreal-engine/statetree-quick-start-guide

---

## Smart Objects

**Recommendation:** investigate after P1/P2, not required for the first authored interactions.

Smart Objects provide queryable/reservable interaction slots and can be filtered using Gameplay Tags. They are strongest when multiple AI/player agents need to discover and reserve the same world interactions.

Potential later uses:
- bird perches;
- NPC observation stations;
- camp work surfaces;
- reusable sampling points;
- contextual sitting/leaning/instrument positions.

For one bespoke P2 sample or P3 Wayfold, a simple interface + authored transform is cheaper.

Official docs:  
https://dev.epicgames.com/documentation/en-us/unreal-engine/smart-objects-in-unreal-engine---overview

---

## Geometry Script / Dynamic Mesh

**Recommendation:** excellent editor tooling candidate; avoid making it the runtime foundation of Monolith deformation.

Geometry Script in UE 5.8 is marked **Beta**. It can generate/edit `UDynamicMesh` through Blueprint and Python and is useful for custom editor utilities and procedural mesh analysis.

Good uses:
- author shed-layer variants from one hero source mesh;
- generate fracture/cut/profile variants offline in-editor;
- analyze surface directions / seams;
- create one-click art tools for repeated biological geology.

Avoid:
- runtime continent-scale remeshing;
- real-time skin peeling as core gameplay.

Official docs:  
https://dev.epicgames.com/documentation/unreal-engine/geometry-scripting-users-guide-in-unreal-engine

---

## Runtime / Streaming Virtual Texturing

**Recommendation:** useful for broad terrain/material blending; profile before making it mandatory.

Virtual Texturing lowers and stabilizes memory use for large texture data. RVT is especially suited to runtime-composited layered material data.

Potential P2 uses:
- moss / residue / age blending where shed layers intersect terrain;
- environmental staining around molt fragments;
- large-scale material masks sampled by foliage/PCG.

Do not depend on the newer **mesh-terrain RVT workflow** without verification; UE 5.8 marks that specific mesh-terrain feature Experimental.

Official docs:  
https://dev.epicgames.com/documentation/unreal-engine/virtual-texturing-in-unreal-engine

---

## Niagara + Effect Types

**Recommendation:** formalize environmental Niagara scalability before P2/P3 become VFX-heavy.

UE recommends Niagara Effect Types to share scalability/culling policies. Large-scale environmental effects should prefer a small number of reusable systems or “system as a service” patterns over hundreds of independent instances.

Create project effect families such as:

```text
NET_Melodia_EnvironmentalAmbient
NET_Melodia_MonolithHero
NET_Melodia_InteractionFeedback
NET_Melodia_DistantAtmosphere
```

P2:
- spores;
- molt dust;
- reaction vapor;
- residue motes.

P3:
- pollen/particulate flow revealing filter currents;
- distant cloud deformation;
- horizon-scale ingestion flow cues.

Official docs:  
https://dev.epicgames.com/documentation/unreal-engine/scalability-and-best-practices-for-niagara

---

## MetaSounds + Audio Modulation

**Recommendation:** very strong thematic fit, but integrate through the existing rhythm system rather than create a second musical authority.

MetaSounds provide procedural, sample-accurate DSP and accept gameplay parameters. Audio Modulation provides Blueprint/C++ control buses for volume, pitch, filtering, etc.

P2 uses:
- damped membrane creak emerging from “stone”;
- hydration/catalysis changing spectral content;
- distant fresh-molt pulse.

P3 uses:
- echo distance contradiction;
- horizon mouth sub-bass that is initially mistaken for weather;
- filtering/low-pass tied to Monolith gape;
- calls returning from geometrically impossible directions.

Preferred architecture:

```text
UMelodiaRhythmReactivitySubsystem
        |
        +--> existing gameplay/presentation signals
        |
        +--> thin audio adapter
               |
               +--> MetaSound parameters / Audio Modulation buses
```

Do not let audio assets call gameplay rhythm events directly.

Official docs:  
https://dev.epicgames.com/documentation/unreal-engine/metasounds-the-next-generation-sound-sources-in-unreal-engine  
https://dev.epicgames.com/documentation/unreal-engine/audio-modulation-overview-in-unreal-engine

---

# 2. Large-world caution: LWC

UE 5.8 documents Large World Coordinates and its Niagara integration, but still marks the LWC feature documentation as Beta/caution for shipping.

For Melodia:
- use UE's normal world coordinate support;
- do not deliberately build hundreds-of-kilometers physical maps merely because doubles exist;
- sell impossible scale through composition, HLOD, atmosphere, streaming, false adjacency, and authored transitions.

P3 in particular should **fake impossible distance**, not require impossible physical map dimensions.

Official docs:  
https://dev.epicgames.com/documentation/unreal-engine/large-world-coordinates-in-unreal-engine-5

---

# 3. Exploration interaction architecture

## Do not start with GAS

Gameplay Ability System is powerful but unnecessary merely to support Survey, Anchor, Catalyze, Wayfold, Resonance Call, and Tactile Test in authored P0–P3 prototypes.

Revisit GAS if the project later needs:
- complex combat status effects;
- replicated ability prediction;
- large attribute/effect stacks;
- many cross-character ability combinations.

For current exploration, use a thin capability/observation model.

### Proposed minimal contract

```text
BPC_ExplorationInteractor
IExplorationTarget
FExplorationObservation
FExplorationActionRequest
FExplorationActionResult
```

`IExplorationTarget` should answer questions such as:

```text
GetObservationChannels()
GetAvailableActions(InteractorTags)
PreviewAction(ActionTag)
ExecuteAction(ActionTag, Context)
```

Keep visual execution local to the target/encounter director.

Example:

```text
Molt fragment
  exposes:
    Explore.Clue.Material
    Explore.Clue.LayerAge

Iris has:
    Explore.Capability.Catalyze

Result:
    target performs its authored Catalyze state
    existing rhythm signal modifies clarity/duration
```

This keeps each impossible phenomenon bespoke without hard-wiring it into a giant global chemistry system.

---

# 4. Ranking

## Use / prototype now

1. Gameplay Tags for exploration vocabulary.
2. StateTree for P2/P3 encounter directors if Blueprint enum logic starts sprawling.
3. PCG editor-time supporting ecology.
4. Niagara Effect Types/scalability policy.
5. MetaSound parameters driven by existing rhythm/presentation signals.
6. Level Instances / Packed Level Actors for static repeated assemblies.
7. World Partition + Data Layers + HLOD when the first genuinely large P3 production map begins.

## Investigate after P0/P1

- Smart Objects for reusable AI/player stations and perches.
- Runtime/hierarchical PCG for large streaming ecology.
- RVT-based ecological/material mask sharing.
- custom editor tools using Geometry Script.
- Data Layer preloading/transition workflow for P3 Wayfolds.

## Defer / avoid as core dependency

- PCG Biome Core as a shipping dependency while Experimental;
- Geometry Script runtime deformation as Monolith foundation while Beta;
- Havok Navigation unless built-in nav/invokers fail a demonstrated requirement;
- Havok Cloth unless Chaos cannot meet a demonstrated hero-garment requirement;
- giant third-party interaction frameworks;
- GAS solely for exploration verbs;
- runtime continent-scale skeletal Monoliths;
- constructing P3 at literal planetary distances.

---

# 5. Existing-project authority boundaries

Preserve the systems already proven in Melodia:

- `UMelodiaRhythmReactivitySubsystem` remains rhythm authority;
- `UMelodiaWaterInteractionSubsystem` remains gameplay-water authority;
- `MPC_Melodia_Palette` remains the existing shared palette/rhythm bus where appropriate;
- `BP_MelodiaNiagaraDriver` remains the standard shared Niagara writer;
- Oceanology remains the current production water/environment authority where already used;
- VRM4U remains an established character/NPC pipeline dependency;
- Monolith chapters get local encounter directors/adapters rather than replacing global subsystems.

No researched plugin should silently become a second global rhythm, water, interaction, or world-state authority.

---

# 6. Immediate implementation experiment

Before adding a marketplace plugin, build one tiny vertical test actor:

```text
BP_ExplorationTestTarget

Tags:
  Explore.Clue.Material
  Explore.Clue.Distance

Supported actions:
  Survey
  Catalyze
  ResonanceCall

State:
  Dormant
  Observed
  Reacted

Presentation:
  one MID scalar
  one Niagara user parameter
  one MetaSound float
```

If the same contract cleanly supports a P2 molt fragment and a P3 Wayfold marker without special-case global code, keep it. If it does not, modify the contract based on concrete chapter needs rather than abstract framework design.
