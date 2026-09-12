# Melodia Melusina — Houdini + Unreal Engine 5.8 Technical Production Research

**Date:** 2026-08-30  
**Status:** production research / implementation guidance  
**Applies to:** Mara hero-character pipeline, P0–P3 Monolith production, and later large-scale worldbuilding  
**Companion docs:**
- `Docs/Houdini/MARA_P0_P3_HOUDINI_EXECUTION_PLAN_2026-08-29.md`
- `Docs/Houdini/LATE_MONOLITH_VISUAL_ESCALATION_BIBLE_2026-08-29.md`
- `Docs/Research/UE58_EXPLORATION_WORLD_BUILDING_RESEARCH_2026-08-29.md`
- `Docs/Monoliths/P2_GOD_THAT_MOLTS_MECHANICS_RESEARCH_2026-08-29.md`
- `Docs/Monoliths/P3_HORIZON_EATER_PLAN_2026-08-29.md`

---

# Executive decision

Houdini should become **Melodia's procedural authoring layer**, not its runtime simulation engine.

Use Houdini to manufacture:

```text
terrain families
hero and modular meshes
state variants
anatomical repetition
curve networks
scatter candidates
masks
UVs
LODs
collision
fracture hierarchies
texture families
offline simulation caches
world-scale reveal geometry
```

Use Unreal to own:

```text
World Partition
Runtime Data Layers
HLOD runtime behavior
PCG runtime/streamed scatter
gameplay state
rhythm reactivity
Oceanology
StateTree
Gameplay Tags
Niagara
MetaSounds
Sequencer
save/persistence
interaction logic
```

The production rule is:

> **Houdini authors the impossible evidence; Unreal decides when the player experiences it.**

Do not build a runtime Houdini dependency into shipping gameplay unless a future feature proves that baking cannot satisfy it.

---

# 1. Current SideFX / UE compatibility posture

## Core Houdini Engine

SideFX's current Unreal documentation states that the Houdini Engine plugin source is compatible with UE5.x generally, while packaged plugin builds must match the Houdini build they were compiled against. Installation Info in Unreal should be used to verify that the running Houdini version matches the plugin's `built with` version.

Official reference:
https://www.sidefx.com/docs/houdini/unreal/install_houdiniengine.html

**Melodia policy:**
- pin the exact Houdini production build in project docs;
- pin the matching Houdini Engine plugin build;
- install the plugin at project level for launcher Unreal builds;
- record the known-good pair before committing generated `.uasset` work;
- never let one workstation silently cook with a different Houdini build.

Suggested project note once verified locally:

```text
Houdini Production Build: <fill after local verification>
Houdini Engine Plugin Build: <same>
UE: 5.8
Session type: Named Pipe or local socket
```

## Houdini-PCG

SideFX documents a separate Houdini-PCG plugin in Houdini 21+ requiring Unreal 5.5+. It allows HDAs to run directly inside Unreal PCG graphs.

Official references:
https://www.sidefx.com/docs/houdini/unreal/pcg.html
https://www.sidefx.com/docs/houdini/unreal/pcg/overview.html

**Melodia policy:** useful, but not required for P0/P1. Adopt only after a normal HDA proves the operation is valuable.

Best candidates later:
- biome-specific mask generation;
- geological scatter preprocessing;
- authored path-aware point generation;
- Monolith residue distribution;
- procedural micro-ecology around a handcrafted hero reveal.

Do not use Houdini-PCG merely because both systems are procedural. UE PCG should retain ownership of runtime/stream-aware scatter when it is already sufficient.

## Houdini-Niagara

Houdini-Niagara exists as a separate plugin. Public plugin documentation should not be treated as proof that the exact binary is healthy on the local UE5.8 project.

Official reference:
https://www.sidefx.com/docs/houdini/unreal/niagara.html

**Melodia policy:** optional experimental tool only until compiled and tested locally. Niagara itself remains authoritative at runtime. Houdini may generate point/curve/attribute data that Niagara consumes through simpler import paths if that is safer.

## KineFX Live Link

SideFX documents Houdini KineFX Live Link, but the public compatibility section is historically narrower than the current core Houdini Engine integration.

Official reference:
https://www.sidefx.com/docs/houdini/unreal/livelink.html

**Melodia policy:** do not make Live Link a dependency for Mara. Use KineFX + NodeSync / SkeletalMesh import first. Treat Live Link as a convenience experiment only after the base hero pipeline is stable.

---

# 2. SessionSync and NodeSync should be daily tools

## SessionSync

SessionSync connects Unreal to an interactive Houdini session and reflects parameter/network changes without repeatedly packaging an HDA.

Official reference:
https://www.sidefx.com/docs/houdini/unreal/sessionsync.html

This is ideal for **building the HDAs themselves**:

```text
Unreal camera / landscape / spline
        ↓
SessionSync
        ↓
Houdini authoring + debugging
        ↓
recook visible in Unreal
```

Recommended uses:
- tuning P1 cloth-landscape folds from a gameplay camera;
- tuning P3 mouth silhouette against the reveal camera;
- checking P2 molt strata at actual player scale;
- validating collision / materials / pivot placement while constructing an HDA;
- debugging attribute translation.

Do not leave SessionSync as the final production interface. Once a tool stabilizes, save/version the HDA and test a clean cold cook.

## NodeSync

NodeSync is especially useful for one-off hero asset iteration and character work.

Official reference:
https://www.sidefx.com/docs/houdini/unreal/nodesync.html

Recommended Mara loop:

```text
UE Melusina skeletal mesh
→ Send to Houdini
→ UnrealToKineFX
→ build Mara proportions / topology / test processing
→ KineFXToUnreal
→ Fetch into UE
→ compare side-by-side
```

For landscapes, use **selected components only** whenever practical rather than sending an entire large world during every iteration.

---

# 3. Mara: production-safe KineFX pipeline

SideFX currently supports Skeletal Mesh input/output through HDAs and NodeSync.

Official reference:
https://www.sidefx.com/docs/houdini/unreal/skeletalmesh.html

The key nodes are:

```text
UnrealToKineFX
KineFXToUnreal
```

A Skeletal Mesh in Houdini is represented by:
- Rest Geometry;
- Capture Pose;
- KineFX skeleton hierarchy.

KineFX skeletons are SOP point hierarchies with transform/name attributes, which makes procedural modifications and rig analysis far more scriptable than classic object-level rigs.

Reference:
https://www.sidefx.com/docs/houdini/character/kinefx/skeletons.html

## Recommended Mara pipeline

```text
Melusina existing production skeleton
        ↓
UnrealToKineFX
        ↓
freeze skeleton hierarchy contract
        ↓
Mara blockout body at compatible joint centers
        ↓
ZBrush hero sculpt
        ↓
Houdini retopo / cleanup / naming / UV / material groups
        ↓
weight transfer from Melusina proxy
        ↓
corrective paint / pose-space testing
        ↓
KineFXToUnreal
        ↓
reuse existing Unreal Skeleton where valid
        ↓
IK Retarget / Control Rig polish
```

The plugin supports `unreal_skeleton` to target an existing Unreal Skeleton Asset. Use this only if Mara's exported bind skeleton remains structurally compatible.

## Physics assets

The plugin can:
- generate a default Physics Asset;
- target an existing Unreal Physics Asset with `unreal_physics_asset`;
- receive custom collision geometry into the third input of KineFXToUnreal.

Useful collision group prefixes include:

```text
collision_geo_simple_box
collision_geo_simple_sphere
collision_geo_simple_capsule
collision_geo_simple_kdop18
collision_geo_simple_kdop26
```

For hero characters, do **not** rely on automatically generated physics as final. It is useful for a first import only.

## What to proceduralize for Mara

Good Houdini targets:
- curl cluster generation from guide curves;
- hair LOD simplification;
- coat accessory placement;
- button / clasp / strap distribution;
- UV packing / validation;
- topology checks;
- naming / material slot enforcement;
- socket marker generation;
- initial skin-weight transfer;
- automated deformation test poses;
- collision proxy generation.

Keep authored:
- face topology and likeness decisions;
- primary curl silhouette;
- coat silhouette;
- asymmetrical hero details;
- final skin weights around face/shoulders/hips;
- hero facial rig decisions.

## Automated deformation QA HDA

Build:

```text
HDA_CH_DeformationAudit
```

Inputs:
- rest mesh;
- capture pose;
- skeleton;
- optional test animation clip.

Outputs:
- shoulder-up pose;
- extreme elbow bend;
- deep crouch;
- high-knee step;
- wrist flexion;
- neck turn;
- coat-clearance masks;
- max-stretch heatmap;
- likely clipping point group.

This is a strong Houdini advantage because the same pose suite can evaluate every party member.

---

# 4. Animation and motion clips

Houdini Engine can import Unreal Animation Sequences and output packed Houdini Motion Clips as Unreal Animation Sequences.

Official reference:
https://www.sidefx.com/docs/houdini/unreal/animations.html

Potential Melodia uses:
- batch animation cleanup analysis;
- procedural secondary-motion preprocessing;
- motion variation generation for NPC field work;
- animation-driven garment collision tests;
- analyzing stride/contact for procedural footprints or cloth response.

Do not replace the established Unreal animation pipeline. Use Houdini where batch analysis or procedural manipulation creates clear value.

---

# 5. World Partition landscape workflow

SideFX supports Unreal Landscapes as input/output, including Edit Layers, Paint Layers, and World Partition.

References:
https://www.sidefx.com/docs/houdini/unreal/landscape/basics.html
https://www.sidefx.com/docs/houdini/unreal/worldpartition/worldpartition.html

## Important source-control rule

In World Partition levels, certain landscape operations can dirty many loaded Landscape Streaming Proxies. Creating or clearing landscape Edit Layers can cause broad dirtying.

Therefore:

> **Only load the region being worked on before cooking a landscape HDA.**

Recommended large-world loop:

```text
load target World Partition cells only
        ↓
select relevant landscape components
        ↓
NodeSync / HDA world input
        ↓
modify local tiles
        ↓
review seams
        ↓
bake
        ↓
submit only intended external actors / proxies
```

Avoid full-landscape recooks for a localized Monolith change.

SideFX recommends tile-based edits for World Partition landscapes and notes that neighboring streaming proxies may be touched to maintain seams.

## Landscape conversion consistency

The plugin exposes landscape conversion options including default Unreal scaling, full-resolution conversion, and forced min/max values.

Reference:
https://www.sidefx.com/docs/houdini/unreal/settings.html

For Melodia, pick one project-wide vertical conversion strategy before generating multiple regions. Otherwise separately authored HDAs may produce subtly inconsistent height scaling.

## Landscape role by chapter

P1 Faraway Mother:
- landscape is the base terrain only;
- giant fabric folds should primarily be meshes, not destructive terrain sculpting;
- use heightfield masks to blend roads/grass/erosion into fold contact zones.

P2 God That Molts:
- landscape carries basin/ravine massing;
- molt strata should be modular meshes intersecting/sitting within terrain;
- use masks to coordinate ecology across actual terrain and shed-material surfaces.

P3 Horizon Eater:
- distant mountains remain landscape/HLOD where useful;
- mouth silhouette is authored presentation geometry, not a physically enormous terrain deformation.

---

# 6. Data Layers and HLOD output from Houdini

Houdini Engine supports importing/exporting Data Layer membership in World Partition maps.

Reference:
https://www.sidefx.com/docs/houdini/unreal/worldpartition/datalayers.html

Groups prefixed with:

```text
unreal_data_layer_<LayerName>
```

can assign Houdini-created actors to a Data Layer when baking. `unreal_create_data_layers = 1` can create missing layers, but production tools should prefer existing known Data Layer assets rather than proliferating typo-driven layers.

## Melodia use

Example P3 groups:

```text
unreal_data_layer_P3_BaseLandscape
unreal_data_layer_P3_PreReveal
unreal_data_layer_P3_GapeReveal
unreal_data_layer_P3_FilterInterior
```

Do not rely on Houdini-created Data Layers for runtime semantics. Unreal remains the authority that activates/deactivates them.

HLOD layer assignment is also supported with:

```text
unreal_hlod_layer
```

Reference:
https://www.sidefx.com/docs/houdini/unreal/worldpartition/hlodlayers.html

This is useful for procedurally generated distant Monolith components that need predictable HLOD treatment.

Potential P3 usage:
- mouth ridge proxies;
- filter plate forests;
- distant false mountain geometry;
- vast ecological scatter that should collapse into HLOD proxies.

---

# 7. Instancing, foliage, Level Instances, Packed Level Actors

Houdini Engine supports instance translation and Level Instancing in Unreal 5.1+.

Reference:
https://www.sidefx.com/docs/houdini/unreal/instancing.html

Use instancing aggressively for:
- repeated molt flakes;
- prayer strips;
- cloth anchor hardware;
- filter plates;
- coral/ecological props;
- shell plates;
- seed pods;
- distant anatomical repetition.

## Author one family, instance many

Do not create 2,000 unique meshes because Houdini can.

Preferred hierarchy:

```text
3–12 authored/generated source variants
        ↓
packed primitives / attribute instancing
        ↓
UE instancing / PCG / foliage
        ↓
per-instance custom data for controlled variation
```

Level Instances / Packed Level Actors are strong for repeating authored environmental motifs such as:
- survey camps;
- shrine clusters;
- ruin fragments;
- field stations;
- large coral colonies;
- cloth shrine assemblies.

Always run Unreal Map Check when building an HDA that outputs Level Instances; SideFX specifically cautions that source and target level settings such as External Actors must be compatible.

---

# 8. PCG vs Houdini vs PDG: exact ownership

## Use Unreal PCG when

- output must react to streaming/runtime generation;
- scatter depends on World Partition runtime cells;
- data already exists cleanly as UE points/surfaces;
- iteration is simple enough to stay in-engine;
- designers need lightweight graph-level control.

## Use a normal HDA when

- geometry itself is being procedurally constructed;
- you need robust curve/surface processing;
- anatomical patterns must stay mathematically coherent across scales;
- custom UVs/masks/groups are required;
- offline simulation or heavy geometry analysis is needed.

## Use Houdini-PCG when

- a specific PCG graph needs one operation Unreal PCG is poor at;
- the HDA can behave like a deterministic PCG node;
- the cost of starting a Houdini cook is acceptable.

## Use PDG when

- the same operation must process many tiles/variants independently;
- work needs caching / resuming;
- outputs can be partitioned into work items;
- parallel batch generation materially improves iteration.

PDG Asset Link can cook embedded TOP networks and import work-item outputs into Unreal.

Reference:
https://www.sidefx.com/docs/houdini/unreal/pdg.html

Potential Melodia PDG uses later:

```text
HE_P2_MoltTile_<x>_<y>
HE_P3_FilterPlateChunk_<n>
HE_BiomeScatter_<cell>
HE_HLODSource_<region>
HE_CollisionLOD_<asset>
HE_TextureBake_<material_family>
```

Do **not** introduce PDG for P0/P1 just to appear scalable. A single artist gains more from clear HDAs than from premature farm-style orchestration.

---

# 9. Mesh output contract

Houdini Engine supports normals, up to multiple UV sets, vertex colors, material references, LODs, sockets/colliders, and Static Mesh build settings.

References:
https://www.sidefx.com/docs/houdini/unreal/meshes.html
https://www.sidefx.com/docs/houdini/unreal/outputs.html

## Standard Melodia mesh attributes

Every production HDA that emits hero environment geometry should standardize:

```text
N
uv
uv2            // optional lightmap / utility
Cd             // masks / material control if needed
unreal_material
unreal_generated_mesh_name
unreal_bake_folder
unreal_bake_outliner_folder
```

Where relevant also emit:

```text
unreal_hlod_layer
unreal_data_layer_*
unreal_output_curve
```

Avoid scattering ad-hoc attribute names without a documented prefix.

## Suggested custom namespaces

Use custom Houdini attributes with clear ownership:

```text
melodia_role
melodia_chapter
melodia_state
melodia_variant
melodia_reveal_stage
melodia_gameplay_tag
melodia_material_family
melodia_lod_class
melodia_collision_class
```

Before Unreal bake, convert only the necessary fields to `unreal_*` attributes.

---

# 10. Materials: generate instances, not giant one-off graphs

Houdini Engine supports assigning existing Unreal materials with `unreal_material`, generating Material Instances with `unreal_material_instance`, and setting parameters using `unreal_material_parameter_*` attributes.

Reference:
https://www.sidefx.com/docs/houdini/unreal/materials.html

This is very useful for Melodia because Houdini can output geometry plus the correct instance configuration without becoming material authority.

Example P2 output:

```text
s@unreal_material_instance = "/Game/Monoliths/GodThatMolts/Materials/MI_Molt_Master";
f@unreal_material_parameter_Hydration = f@melodia_hydration;
f@unreal_material_parameter_LayerAge = f@melodia_age;
f@unreal_material_parameter_PearlSheen = f@melodia_pearl;
```

Exact parameter names must match actual Unreal master materials.

**Rule:** Unreal master materials remain authored and reviewed in Unreal. Houdini chooses parameters and texture assets; it does not auto-invent opaque generated shader graphs for production.

---

# 11. Copernicus: high-value future material tool

Current Houdini Engine documentation supports Copernicus HDAs for texture outputs into Unreal, including texture baking and automatic material/texture handoff.

Reference:
https://www.sidefx.com/docs/houdini/unreal/copernicus.html

This is potentially very valuable for Melodia.

## High-value uses

### God That Molts
Generate matched texture families from one procedural anatomical field:

```text
ancient crust
weathered laminate
wet inner membrane
pigment migration
fresh secretion
Catalyzed state
```

All can share coherent seam/pore structure.

### Faraway Mother
Generate:
- woven direction fields;
- seam/fiber masks;
- tension-aware wear;
- embroidered guide masks;
- world-space cloth breakup.

### Horizon Eater
Generate:
- filter-fiber density maps;
- parallax breakup;
- feeding-flow residue masks;
- distance-field-derived reveal masks.

### General painterly materials
Generate masks and RMA/normal/height support maps while preserving Unreal's authored painterly master shader.

## Adoption rule

Investigate after the first geometry HDAs are stable. It is valuable, but it should not delay P1 geometry proof.

---

# 12. Offline simulation: the real path to “insane” Monolith visuals

Houdini's greatest value for late Monoliths is not running simulations live. It is **baking physically rich motion into cheap runtime representations**.

## Vellum

Use offline Vellum for:
- continent-scale cloth fold inspiration;
- Faraway Mother hero contractions;
- membrane peeling;
- tensile banners / ribbons;
- shell/skin flapping;
- biological sheets folding around terrain.

Production outputs:
- selected mesh states;
- VAT animation;
- bone/skeleton reduction;
- texture flow fields;
- spline envelopes;
- baked deformation curves.

Do not ship kilometer-wide Vellum simulation.

## FLIP

Use offline FLIP for:
- impossible water sheets;
- vertical folded seas;
- liquid flowing upward around anatomy;
- sea displacement references;
- splash/wake texture and velocity fields.

For P0 Sea Above, Oceanology remains runtime water authority. Houdini FLIP is a source of hero animation/reference/data, not a replacement ocean system.

## Pyro / sparse volumes

Use offline Pyro for:
- cloud flow around negative-space bodies;
- Moon Grazer light-obscuring atmosphere;
- breathing fog fields;
- impossible weather vortices;
- particulate filter feeding.

Convert results into:
- flipbooks;
- sparse VDB assets if the runtime path is proven;
- vector fields;
- Niagara point/velocity datasets;
- static cloud masks;
- Sequencer-only cinematic caches.

## RBD / Chaos handoff

Houdini Engine supports Geometry Collection output for Unreal Chaos using `unreal_gc_piece` and clustering attributes.

Reference:
https://www.sidefx.com/docs/houdini/unreal/chaosintegration.html

Strong Melodia uses:
- a “stone” shell that fractures and reveals membrane;
- ancient molt plates cracking under a Catalyze event;
- giant mineralized deposits breaking along biologically meaningful seams;
- shrine/ruin destruction tied to Monolith movement.

Do not make every Monolith event destruction-heavy. Chaos should be a punctuation mark.

---

# 13. Vertex Animation Textures (VAT): extremely relevant to Monoliths

SideFX Labs VAT can bake complex soft-body, rigid-body, dynamic-remeshing, particle, and skeletal motion into textures for GPU playback.

Reference:
https://www.sidefx.com/docs/houdini/nodes/out/labs--vertex_animation_textures-3.1.html

VAT is one of the most relevant techniques for later Melodia visuals because it allows enormous or unusual animated geometry without a giant skeletal rig or CPU-heavy simulation.

## Best Melodia VAT candidates

### Faraway Mother
- one distant valley fold slowly contracting;
- huge membrane breathing once;
- cloth cliff responding to Ebenezer tug.

### God That Molts
- drying/curling shed membrane;
- fresh layer peeling away;
- thousands of small fragments performing a synchronized biological twitch.

### Horizon Eater
- filter plates flexing during gape;
- skyline lip deformation;
- huge soft-tissue silhouettes that only need limited authored motion.

### Late Monoliths
- Starfish Continent arm contraction;
- Reef That Looks Back chromatophore/soft-body wave;
- River Serpent watershed muscle wave;
- Unfinished Whale rain-deflection/body-boundary deformation.

## VAT limitations that matter

VAT trades CPU animation cost for texture memory and shader complexity. Animated collision is limited, and runtime interactivity is lower than a fully rigged mesh.

Therefore use VAT for **presentation surfaces**, not player-critical collision geometry.

Keep collision on a simpler static / skeletal / gameplay proxy.

---

# 14. Curves should be the common language of impossible anatomy

Houdini Engine accepts Unreal Spline Components and can output Unreal Spline Components using `unreal_output_curve`.

Reference:
https://www.sidefx.com/docs/houdini/unreal/curves.html

This is one of the most strategically useful integration points for Melodia.

Curves can represent:
- Faraway Mother seams;
- tension lines;
- Mara survey baselines;
- Starskiff/current rails;
- P2 molt seams;
- residue trails;
- P3 Wayfold correspondence;
- filter-flow fields;
- river-serpent body axis;
- antler/mountain branching;
- giant nerve / vein systems;
- migration routes.

## Standardize curve attributes

```text
melodia_curve_role
melodia_strength
melodia_radius
melodia_phase
melodia_reveal_stage
melodia_gameplay_tag
```

Then author chapter-specific HDAs that consume the same curve vocabulary.

This is a better long-term abstraction than a monolithic “Monolith framework.”

---

# 15. Chapter-specific HDA expansion

## P1 — Faraway Mother

Existing planned tools:

```text
HDA_P1_TensionValley
HDA_P1_SeamGraph
HDA_P1_BannerPrayerStripField
```

Add:

```text
HDA_P1_FoldStateFamily
HDA_P1_ClothContactMask
HDA_P1_DistantContractionBake
```

### FoldStateFamily
Input:
- hero fold mesh;
- anchor curves;
- tension values;
- seed.

Output matched states:

```text
Rest
WindLoaded
ImpossibleTension
Contracted
Reveal
```

Maintain topology when possible to support clean material morphs or VAT.

### ClothContactMask
Generates ground masks beneath giant draped surfaces:
- dead grass;
- compressed vegetation;
- mud/water collection;
- fiber debris;
- shadowing / dampness.

This helps the fabric read as old landscape before the reveal.

## P2 — God That Molts

Existing tools:

```text
HDA_P2_MoltLayerFamily
HDA_P2_MoltRavine
HDA_P2_EcologyOnMolt
```

Add:

```text
HDA_P2_MicroMacroAnatomy
HDA_P2_CatalyzeStateBake
HDA_P2_RecentMoltTrail
```

### MicroMacroAnatomy
One procedural seam/pore network produces:
- hand-sized specimen pattern;
- boulder pattern;
- cliff-scale pattern.

This mechanically guarantees the “same anatomy at impossible scale” clue.

### CatalyzeStateBake
Produces matched topology/material states for one object:

```text
Dormant
Hydrated
Reactive
Crystallized
Spent
```

Unreal chooses state. Houdini only authors the valid forms.

## P3 — Horizon Eater

Existing tools:

```text
HDA_P3_HorizonMouthComposer
HDA_P3_WayfoldAuthoring
HDA_P3_FilterFlowField
```

Add:

```text
HDA_P3_ParallaxContradiction
HDA_P3_GapeStateFamily
HDA_P3_FilterPlateForest
HDA_P3_DistanceContinuityAudit
```

### ParallaxContradiction
Takes the intended camera path and creates placements/scale offsets where known landmarks violate expected parallax without immediately reading as teleportation.

### GapeStateFamily
Create states:

```text
Closed_Landscape
PreFeed_Tension
Gape_10
Gape_35
Gape_70
FullReveal
AfterFeed
```

Each state must preserve horizon composition from designated cameras.

### DistanceContinuityAudit
For each Wayfold pair:
- confirm destination streaming bounds;
- visualize camera cut risk;
- validate companion landing transforms;
- export occlusion/fog suggestion volumes;
- calculate entry/exit tangent mismatch.

---

# 16. Late-Monolith shared HDA library

Build reusable tools only where multiple concepts share the same underlying operation.

Recommended library:

```text
HDA_MONOLITH_NegativeSpaceBody
HDA_MONOLITH_CameraRevealComposer
HDA_MONOLITH_AnatomyFromCurves
HDA_MONOLITH_FieldResponse
HDA_MONOLITH_StateFamily
HDA_MONOLITH_ParallaxContradiction
HDA_MONOLITH_MicroMacroPattern
HDA_MONOLITH_OfflineMotionBake
HDA_MONOLITH_WorldMaskProjector
HDA_MONOLITH_RevealAudit
```

## NegativeSpaceBody
Defines a body through what it removes/deflects:
- clouds;
- rain;
- stars;
- moonlight;
- birds;
- fog;
- vegetation orientation.

Ideal for Unfinished Whale and Moon Grazer.

## CameraRevealComposer
Given hero cameras, preserve the ordinary landscape silhouette until a reveal parameter changes.

This is essential because Monoliths are **composition problems before they are modeling problems**.

## FieldResponse
Inputs a vector/scalar field and generates secondary evidence:
- grass lean;
- particles;
- cloth orientation;
- debris trails;
- tree growth direction;
- erosion biases;
- filter flow.

Export the field itself where Unreal/Niagara/PCG can use it.

---

# 17. Baking and shipping policy

SideFX explicitly supports baking Houdini-generated outputs into native Unreal assets/actors. Once baked, those outputs no longer depend on the HDA.

References:
https://www.sidefx.com/docs/houdini/unreal/intro.html
https://www.sidefx.com/docs/houdini/unreal/packaging.html

## Melodia policy

During development:
- HDAs may stay live in authoring maps;
- prototype maps can use Houdini Asset Actors;
- keep source `.hda/.otl/.hiplc/.hip` outside or within source-controlled tool folders as appropriate.

Before content lock:
- bake hero outputs;
- replace procedural actors where stability matters;
- keep the HDA and seed/parameters documented for regeneration;
- validate baked Data Layer/HLOD assignments;
- remove runtime Houdini requirement unless intentionally justified.

Suggested bake folder convention:

```text
/Game/Melodia/Generated/P1/FarawayMother/...
/Game/Melodia/Generated/P2/GodThatMolts/...
/Game/Melodia/Generated/P3/HorizonEater/...
```

Author source HDAs separately:

```text
/Tools/Houdini/HDAs/Shared/
/Tools/Houdini/HDAs/Characters/
/Tools/Houdini/HDAs/P1/
/Tools/Houdini/HDAs/P2/
/Tools/Houdini/HDAs/P3/
/Tools/Houdini/HDAs/Monoliths/
```

Use `unreal_bake_folder` and `unreal_bake_outliner_folder` rather than manual cleanup after every cook.

---

# 18. Versioning / determinism rules

Each important HDA should expose:

```text
ToolVersion
Seed
QualityMode
Preview / Production switch
OutputNamingPrefix
BakeFolderOverride
DebugVisualization
```

Record a deterministic seed for any hero reveal.

A Monolith should not silently change shape because somebody recooked it three months later with a default random seed.

## Production HDA versioning

Prefer versioned asset definitions:

```text
HDA_P2_MoltLayerFamily::1.0
HDA_P2_MoltLayerFamily::1.1
HDA_P2_MoltLayerFamily::2.0
```

Do not break a shipped/proven definition merely to improve the tool for another chapter.

---

# 19. Performance budgets and representation ladder

For each enormous visual, choose the cheapest representation that sells the idea.

```text
1. material parameter / shader distortion
2. Niagara / MetaSound evidence
3. spline / instanced secondary geometry
4. Data Layer state swap
5. static mesh transform
6. VAT deformation
7. simple skeletal mesh
8. Chaos event
9. Sequencer-only cached cinematic
10. fully simulated runtime system
```

Start at the top and move downward only when the effect cannot be sold otherwise.

Example: Horizon Eater gape does **not** begin with a giant rig. It begins with:
- skyline states;
- fog;
- filter plate visibility;
- distant transforms;
- flow vectors;
- audio;
- a small number of VAT/skeletal hero surfaces.

---

# 20. Build order — next 10 Houdini deliverables

## Tier A — prove the pipeline now

### 1. `HDA_CH_CurlCluster`
Mara curl guides → grouped curl cards/tubes/mesh clusters + LOD variants.

### 2. `HDA_CH_DeformationAudit`
Reusable hero-character skinning QA.

### 3. `HDA_ENV_ScatterMaskBuilder`
Landscape/mesh → slope/height/curvature/distance masks for PCG and procedural ecology.

### 4. `HDA_P1_SeamGraph`
Anchors + fold surfaces → coherent seam/tension network.

### 5. `HDA_P1_FoldStateFamily`
One hero cloth-landscape fold → matched reveal states.

## Tier B — build after first P1 proof

### 6. `HDA_P2_MicroMacroAnatomy`
Shared specimen-to-cliff pattern generator.

### 7. `HDA_P2_CatalyzeStateBake`
Matched material/geometry states for Iris interactions.

### 8. `HDA_P3_HorizonMouthComposer`
Camera-driven skyline/mouth composition tool.

### 9. `HDA_P3_FilterFlowField`
Feeding vector field → splines/points/masks for Niagara, ecology, and audio zones.

### 10. `HDA_MONOLITH_NegativeSpaceBody`
General later-Monolith tool for visible environmental displacement around an unseen body.

---

# 21. Things to explicitly defer

Do **not** spend current production time on:
- global procedural world generation;
- a generalized biological chemistry simulator;
- runtime Houdini cooking for gameplay;
- live continent-scale Vellum/FLIP/Pyro;
- procedural full character generation;
- automatic hero-face retopology as a required pipeline;
- non-Euclidean world-coordinate rewrite;
- Houdini-generated gameplay Blueprints as the primary logic source;
- full procedural cities;
- PDG farm orchestration before local iteration is slow enough to justify it.

---

# 22. Highest-leverage research findings for Melodia specifically

1. **KineFX SkeletalMesh I/O makes the Melusina rig reusable as a genuine technical foundation for Mara**, rather than merely a visual reference.

2. **World Partition/Data Layer/HLOD metadata can travel through Houdini**, which means giant Monolith reveal geometry can be generated with streaming organization already attached instead of manually re-sorting every bake.

3. **Curves are the best shared procedural primitive for Melodia.** Tension, seams, currents, anatomy, migration, Wayfolds, rivers, antlers, nerves, and filter flow can all use a common authored curve vocabulary.

4. **VAT is likely the secret weapon for impossible world-scale motion.** Use it to turn expensive Houdini simulations into GPU presentation layers while keeping simple gameplay collision.

5. **Copernicus can eventually unify procedural mesh logic and procedural texture logic**, especially for God That Molts where the same anatomical field should appear in geometry, pigment, pores, roughness, and Catalyze states.

6. **PDG is a later scaling tool, not a first-step architecture.** The project is currently better served by a dozen clear, inspectable HDAs than one enormous procedural world graph.

7. **Bake aggressively at content lock.** Houdini should give Melodia extraordinary authoring power without forcing the shipping game to depend on procedural cooks.

---

# 23. External documentation references

Core plugin / install:
- https://www.sidefx.com/docs/houdini/unreal/install_houdiniengine.html
- https://www.sidefx.com/docs/houdini/unreal/intro.html
- https://www.sidefx.com/docs/houdini/unreal/outputs.html
- https://www.sidefx.com/docs/houdini/unreal/packaging.html

Iteration:
- https://www.sidefx.com/docs/houdini/unreal/sessionsync.html
- https://www.sidefx.com/docs/houdini/unreal/nodesync.html

Characters:
- https://www.sidefx.com/docs/houdini/unreal/skeletalmesh.html
- https://www.sidefx.com/docs/houdini/character/kinefx/skeletons.html
- https://www.sidefx.com/docs/houdini/unreal/animations.html

World building:
- https://www.sidefx.com/docs/houdini/unreal/landscape/basics.html
- https://www.sidefx.com/docs/houdini/unreal/worldpartition/worldpartition.html
- https://www.sidefx.com/docs/houdini/unreal/worldpartition/datalayers.html
- https://www.sidefx.com/docs/houdini/unreal/worldpartition/hlodlayers.html
- https://www.sidefx.com/docs/houdini/unreal/instancing.html
- https://www.sidefx.com/docs/houdini/unreal/curves.html

Procedural scaling:
- https://www.sidefx.com/docs/houdini/unreal/pcg.html
- https://www.sidefx.com/docs/houdini/unreal/pcg/overview.html
- https://www.sidefx.com/docs/houdini/unreal/pdg.html

Materials / VFX:
- https://www.sidefx.com/docs/houdini/unreal/materials.html
- https://www.sidefx.com/docs/houdini/unreal/copernicus.html
- https://www.sidefx.com/docs/houdini/nodes/out/labs--vertex_animation_textures-3.1.html
- https://www.sidefx.com/docs/houdini/unreal/chaosintegration.html
- https://www.sidefx.com/docs/houdini/unreal/niagara.html

---

# Acceptance criterion for this research

This document succeeds if another technical artist or implementation agent can open the project and understand:

- what Houdini owns;
- what Unreal owns;
- which integrations are production-ready vs optional;
- how Mara can reuse the existing hero rig infrastructure;
- how P1/P2/P3 should be procedurally authored;
- how the late Monoliths can look impossibly expensive without actually shipping impossible simulations;
- what ten tools to build first;
- what not to build yet.

Final rule:

> **Use Houdini to make the world obey one impossible rule with obsessive internal consistency. Use Unreal to reveal that rule at the exact moment the player is ready to misunderstand it.**
