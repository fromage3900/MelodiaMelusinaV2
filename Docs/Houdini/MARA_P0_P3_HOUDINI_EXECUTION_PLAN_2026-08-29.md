# Mara + P0–P3 Houdini Execution Plan

**Date:** 2026-08-29  
**Status:** executable production handoff / docs-only  
**Target:** Houdini 21/22 + Houdini Engine for Unreal + Unreal Engine 5.8  
**Primary rule:** use Houdini to manufacture reusable geometry, masks, layouts, LODs, scatter data, and authored state variants; keep gameplay authority, Data Layer state changes, encounter logic, rhythm authority, and final hand-authored composition in Unreal.

---

# 0. Current source-of-truth decisions

Opening sequence:

```text
P0 — Sea Above
water may be anatomy

P1 — Faraway Mother
fabric may be landscape / draped anatomy
introduce Mara Vell + Ebenezer

P2 — God That Molts
geology may be discarded biology
introduce Iris Fen / Catalyze material-state play

P3 — Horizon Eater
distance/adjacency may be anatomy
a horizon-scale filter feeder uses Wayfold-like spatial compression to feed
```

Character direction:
- Melusina remains the hero rig/animation standard.
- Mara is a distinct authored hero mesh, not a generic VRM NPC body.
- Reuse Melusina skeleton hierarchy / rig conventions where practical so locomotion, IK, sockets, retargeting, and interaction work are shared.
- VRM4U remains useful for rapid proxy iteration because the project already uses VRM NPCs.
- The final Mara/Ebenezer raster concept sheet is **not currently in Git**; the production-safe written stylization spec is.

Production doctrine:

> **Build the authored impossible interaction first. Turn it into an HDA only when procedural control saves repeated work.**

Do not proceduralize a one-off hero reveal just because Houdini can.

---

# 1. Toolchain gate — do this before any asset work

## Required

- Houdini production build installed.
- Houdini Engine for Unreal installed **inside the project Plugins directory** and confirmed working with UE5.8.
- Unreal PCG enabled.
- Session Sync or Node Sync working for quick round-trip tests.

SideFX currently documents Houdini Engine binaries for UE5.8 and UE5.7. Treat this as the preferred bridge rather than custom exporters.

Official references:
- Houdini Engine Unreal introduction / compatibility: https://www.sidefx.com/docs/houdini/unreal/intro.html
- PCG integration: https://www.sidefx.com/docs/houdini/unreal/pcg/overview.html
- Inputs: https://www.sidefx.com/docs/houdini/unreal/inputs.html
- Outputs: https://www.sidefx.com/docs/houdini/unreal/outputs.html
- World Partition: https://www.sidefx.com/docs/houdini/unreal/worldpartition/index.html
- PDG Asset Link: https://www.sidefx.com/docs/houdini/unreal/pdg.html

## Optional / verification-only

### Houdini Niagara
Useful for offline point-cache-driven effects such as:
- horizon-filter flow bands;
- molt fragments traveling through air;
- authored particulate streams;
- debris paths.

But SideFX public Houdini-Niagara documentation currently names UE5.4 as the latest supported build. **Do not make it a dependency until a UE5.8 local compile/test passes.** Standard Niagara + exported curves/point data remains the safe fallback.

### KineFX Live Link
Investigate only if it meaningfully accelerates Mara animation/rig iteration. It is not required for the first Mara mesh pass.

---

# 2. Project folder contract

## Houdini source

```text
$HIP/Melodia/
  Characters/
    Mara/
      00_Input/
      10_Proxy/
      20_HeroMesh/
      30_Retopology/
      40_UV/
      50_RigTransfer/
      60_HairAccessories/
      70_LOD/
      90_Export/
  World/
    Shared/
    P0_SeaAbove/
    P1_FarawayMother/
    P2_GodThatMolts/
    P3_HorizonEater/
  HDA/
    Character/
    Terrain/
    Scatter/
    Monolith/
  PDG/
```

## Unreal output

```text
/Game/Melodia/Characters/Mara/
/Game/Melodia/Environment/Shared/Houdini/
/Game/Melodia/Environment/P0_SeaAbove/Houdini/
/Game/Melodia/Environment/P1_FarawayMother/Houdini/
/Game/Melodia/Environment/P2_GodThatMolts/Houdini/
/Game/Melodia/Environment/P3_HorizonEater/Houdini/
```

Houdini-generated content is a **manufacturing result**, not the design authority. Bake anything production-critical and do not leave final playable scenes dependent on live HDA cooking.

---

# 3. Mara hero mesh — fastest safe pipeline

## Goal

Create a Mara hero character that:
- clearly belongs beside Melusina;
- can reuse/retarget Melusina animation infrastructure;
- can temporarily run through the existing VRM pipeline while the hero mesh is unfinished;
- preserves the successful stylized face, graphic dark curls, surveyor silhouette, layered field clothing, and adult proportions.

## Phase M0 — make the in-engine proxy first

**Timebox: 1–2 hours**

1. Duplicate/derive a compatible humanoid proxy from the existing working character pipeline.
2. Match only:
   - total height;
   - shoulder width;
   - head size;
   - leg length;
   - arm reach;
   - eye line;
   - curl silhouette proxy;
   - coat/skirt volume proxy.
3. Put proxy Mara beside Melusina in UE.
4. Test:
   - idle;
   - walk/run;
   - close dialogue camera;
   - shoulder-to-shoulder composition;
   - Sounding Staff hand socket;
   - Ebenezer shoulder/perch socket;
   - concertina hand spacing.

**Gate M0:** proportions must read as Mara at gameplay and dialogue distance before sculpt detail begins.

---

## Phase M1 — export Melusina reference scaffold into Houdini

Preferred input:
- Melusina body mesh;
- skeleton;
- skin weights if accessible;
- neutral pose;
- sockets/marker transforms exported separately if needed.

Use Houdini Engine geometry/skeletal input or FBX where appropriate. SideFX supports Skeletal Mesh input and output through the Unreal plugin.

Create network:

```text
/obj/CH_Mara_Build
  IN_Melusina_Body
  IN_Melusina_Skeleton
  IN_Mara_Sculpt
  IN_Mara_Clothes
```

Create stable groups:

```text
body_head
body_neck
body_torso
body_arm_L
body_arm_R
body_leg_L
body_leg_R
hands
feet
face_mask
```

Do not destructively alter the reference skeleton.

---

## Phase M2 — hero sculpt division of labor

### ZBrush / authored sculpt owns

- Mara face likeness/stylization;
- cheek/jaw/nose/eye design;
- curl hero shapes;
- hand silhouettes;
- coat hero folds;
- silhouette asymmetry;
- intentional painterly irregularity.

### Houdini owns

- scale/proportion validation;
- reusable cleanup;
- retopo assistance / topology validation;
- symmetry checks where desired;
- UV creation/layout;
- material/group assignment;
- skin-weight transfer experiments;
- collision proxies;
- LOD generation;
- accessory procedural helpers;
- export packaging.

Do **not** procedurally smooth away the stylized face or coat asymmetry.

---

## Phase M3 — Mara retopo target

Recommended topology priorities:

1. Match Melusina deformation topology around:
   - shoulders;
   - elbows;
   - wrists;
   - hips;
   - knees;
   - ankles;
   - mouth/eyes if facial rig reuse is planned.
2. Keep Mara face loops authored rather than relying on fully automatic remesh.
3. Allow outfit layers to remain separate meshes during iteration.
4. Keep rigid survey hardware separate from deforming cloth.

Houdini network concept:

```text
IN_HighSculpt
 -> cleanup
 -> split body / garment / rigid accessories
 -> retopo or imported authored low mesh
 -> attribute transfer (groups/material IDs)
 -> normal/tangent prep
 -> OUT_Mara_LOD0
```

**Gate M3:** run an extreme-pose deformation test before UV finalization.

Required poses:
- arm overhead;
- deep crouch;
- wide Starskiff-like riding lean even if P1 no longer requires Starskiff;
- staff strike windup;
- concertina hands together;
- bird-on-shoulder head turn.

---

## Phase M4 — skeleton + weights reuse

### Preferred

Keep Mara on a skeleton that is compatible with the Melusina hierarchy.

Two acceptable outcomes:

**A. Same skeleton asset / closely compatible bind proportions**  
Best for maximum animation reuse.

**B. Mara-specific skeleton with identical/near-identical hierarchy**  
Use UE IK Retargeter from Melusina for more freedom in limb/body proportion.

In Houdini/KineFX:
- bring in reference skeleton;
- align Mara joint centers to her final mesh;
- transfer initial capture/weights from Melusina where usable;
- repaint/refine shoulders, hips, neck, hands, and face;
- preserve bone names expected by Unreal systems.

Do not lock yourself into bad Mara proportions just to avoid retargeting.

**Gate M4:** existing Melusina locomotion must play on Mara without catastrophic shoulder/hip deformation.

---

## Phase M5 — curls, coat, scarf, equipment

### Curls

Build 3 levels:

```text
A — hero curl masses: authored mesh
B — secondary curl clusters: reusable curve-to-ribbon / curve-to-tube HDA
C — tiny breakup: shader / cards / minimal geometry
```

Useful HDA:

```text
HDA_CH_CurlCluster
inputs:
  guide curves
  scalp mesh
params:
  width
  taper
  twist
  clump
  random seed
  silhouette bias
outputs:
  curl mesh/cards
  scalp attachment group
  LOD variants
```

Do not make the hair simulation-heavy. The graphic silhouette matters more than strand count.

### Survey gear

Proceduralize only repeated functional elements:
- brass clips;
- contour-map engraving paths;
- straps;
- stitching;
- tiny measurement ticks;
- specimen/survey tag variants.

Hero Sounding Staff should be authored, with Houdini used for:
- repeating measurement marks;
- cable/brace geometry;
- clean LODs;
- collision.

### Ebenezer sockets

Export named guide transforms/locators for:

```text
Socket_Ebenezer_Shoulder_L
Socket_Ebenezer_Shoulder_R
Socket_Ebenezer_Staff
Socket_Ebenezer_Satchel
```

UE remains authority for sockets/attachment behavior.

---

# 4. Shared worldbuilding HDA stack

Build these **before** chapter-specific procedural tools.

## HDA_ENV_TerrainStamp

Purpose:
- authored large-scale terrain shape stamp;
- ridge/valley/basin/terrace generation;
- outputs masks for materials, foliage, paths, and reveal composition.

Inputs:
- Unreal Landscape or HeightField;
- boundary curve;
- optional hero-viewpoint points.

Outputs:
- heightfield;
- slope mask;
- curvature mask;
- flow mask;
- erosion mask;
- biome masks;
- `MonolithRevealMask`.

## HDA_ENV_PathCorridor

Purpose:
- turn hand-authored curves into paths/trails/roads/boardwalks without surrendering composition.

Inputs:
- Unreal spline / Houdini curve;
- landscape.

Outputs:
- terrain flatten/carve mask;
- edge scatter masks;
- optional path mesh;
- avoidance zone.

Important: SideFX landscape spline support is currently marked experimental. For production-critical authored routes, prefer normal Unreal Spline Components as Houdini curve inputs, or generate meshes/masks and keep final Landscape Spline editing in Unreal.

## HDA_ENV_ScatterMaskBuilder

Purpose:
- convert terrain analysis + art direction curves/volumes into PCG-ready masks/point attributes.

Outputs point attributes such as:

```text
species_group
scale_min
scale_max
orientation_bias
wetness
slope
chapter_state
avoid_hero_view
monolith_influence
```

Final large scatter should usually be done by Unreal PCG so streaming/runtime ownership stays inside UE.

## HDA_ENV_HeroRockFamily

Purpose:
- generate controlled variants from 3–8 authored rock/shell/bark source meshes.

Allowed variation:
- proportion;
- cut planes;
- erosion;
- fracture;
- limited bend;
- UV-preserving or tri-planar-ready output.

Not allowed:
- random noise blobs with no art direction.

## HDA_ENV_LOD_Collision_Batch

Input:
- selected environment meshes.

Output:
- LOD1/LOD2/LOD3;
- simplified collision;
- naming validation;
- texel-density report attributes.

This is one of the highest-return Houdini tools for a solo production.

---

# 5. World Partition / PDG strategy

Do **not** start P0/P1 by procedural-generating an entire continent.

Use World Partition when region size makes it necessary; until then, use contained authored test maps.

For genuinely large regions:

```text
TOP network
  HE_TerrainTiles
  HE_OUT_Terrain
  HE_ScatterAnalysis
  HE_OUT_ScatterData
  HE_HLODPrep
  HE_OUT_HLODPrep
```

Use PDG to process terrain/scatter tiles independently and bake stable outputs. SideFX PDG Asset Link can import work-item outputs directly into Unreal and supports asynchronous importing for large batches.

Houdini landscape output can create LandscapeStreamingProxies + SharedLandscapeActor through the documented Unreal attributes when appropriate.

**Rule:** PDG is a build farm for content, not gameplay.

---

# 6. P0 — Sea Above Houdini work

P0 is already a focused beauty/runtime slice. Do not rebuild water logic in Houdini.

## Build only

### HDA_P0_CoastlineComposer

Inputs:
- coastline curve;
- hero reveal viewpoint;
- Oceanology/waterline reference height;
- keep-out volumes.

Outputs:
- cliff/shore terrain stamp;
- beach/rock masks;
- hero framing rock placements;
- fog-card anchor points;
- distant false-horizon geometry guide.

### HDA_P0_BellProxyBuilder

Purpose:
- build static/low-deformation Monolith proxy shells from 2–4 profile curves.

Outputs:
- Bell membrane hero proxy;
- coarse far proxy;
- UVs / vertex masks for material pulse;
- optional radial parameter coordinate.

Never turn Bell into gameplay water or a giant rig.

### P0 acceptance

Houdini work is done when:
- coast composition supports the reveal;
- proxies are cheap;
- shader masks are clean;
- nothing duplicates Oceanology or the water subsystem.

---

# 7. P1 — Faraway Mother Houdini work

P1 should be the strongest early Houdini showcase because cloth-like geography benefits from curve/surface proceduralism.

## HDA_P1_TensionValley

Inputs:
- valley boundary;
- 3–8 tension anchor points;
- route curve;
- hero-viewpoint points;
- exclusion volumes.

Procedure:

```text
anchors
 -> generate tension graph
 -> build catenary / draped guide curves
 -> surface loft / cloth-like broad sheets
 -> selectively relax/sag
 -> project/embed some sheets into terrain
 -> create seam curves
 -> create tear/opening zones
 -> output proxy terrain + hero cloth meshes + masks
```

Parameters:

```text
Tension
Sag
AnchorBreakProbability
SeamFrequency
FoldScale
DistantDelayGroup
HeroFoldBias
```

This is **geography that can pass as cloth**, not literal flags everywhere.

## HDA_P1_BannerPrayerStripField

Use for local scale clues:
- cloth strips;
- survey ribbons;
- prayer tags;
- abandoned textile structures.

Outputs PCG points rather than thousands of baked unique meshes.

Point attributes:

```text
wind_axis
false_tension_axis
reaction_delay
cloth_family
```

UE material/Blueprint owns actual runtime response.

## HDA_P1_SeamGraph

Outputs curves representing:
- ordinary seam;
- impossible seam;
- hidden Monolith continuity;
- rhythm reveal route.

Bake curves or convert them into lightweight spline/data assets used by the P1 encounter director.

### Hero reveal

Do **not** procedurally reveal a humanoid giant.

Houdini should generate several independently plausible formations that, from one authored camera/viewpoint, align into the suggestion of one impossible draped organism.

Use a camera-frustum validation subnet:

```text
VIEW_HeroReveal
 -> project silhouette
 -> compare landmark alignment
 -> flag pieces outside intended composition
```

### P1 acceptance

Player can read:
1. landscape;
2. impossible tension;
3. shared seams/folds;
4. distant response to local cloth interaction;
5. finally one connected organism.

---

# 8. P2 — God That Molts Houdini work

P2 should exploit Houdini's strongest procedural modeling advantage: **families of related material layers**.

## HDA_P2_MoltLayerFamily

Inputs:
- 3–6 authored base shell/bark/membrane meshes or curves;
- age profile;
- split/opening curve;
- weathering controls.

Generate states:

```text
State_A_AncientCrust
State_B_WeatheredLaminate
State_C_FlexibleMembrane
State_D_FreshPearlInner
State_E_ReactiveCatalyzed
```

All states must preserve enough correspondence for clean mesh swapping / material blending in UE.

Outputs:
- LOD0–LOD2;
- shared pivot;
- UVs;
- material groups;
- vertex masks:
  - `mask_freshness`
  - `mask_pores`
  - `mask_seams`
  - `mask_catalyze`
  - `mask_fungal_attach`.

## HDA_P2_MoltRavine

Inputs:
- ravine curve;
- terrain;
- molt-direction vector;
- nested age layers.

Outputs:
- terrain stamp;
- nested discarded-shell formations;
- micro-to-kilometer repeating seam pattern;
- fresh-molt direction mask;
- ecology scatter masks.

Core trick:

A hand-sized specimen and the distant cliff must share the **same procedural seam language** so the player can visually infer scale.

Implement by driving both with the same normalized 2D/3D pattern function or stored seam curve family, not by eyeballing unrelated textures.

## HDA_P2_EcologyOnMolt

Outputs Unreal-PCG-ready points for:
- fungi on old outer crust;
- roots in seam gaps;
- insects/nests;
- moss in moisture pockets;
- sparse growth avoidance around fresh material.

Do not bake the whole ecosystem from Houdini if UE PCG can own the streamed scatter.

## Catalyze asset contract

Every hero Catalyze mesh exports:

```text
pivot-consistent state variants
material slot consistency
collision-state recommendation
CatalyzeMask vertex color or texture
InteractionAnchor transform
TraversalAnchor transforms[]
```

UE owns:
- state machine;
- rhythm result;
- collision toggle;
- Niagara;
- audio;
- save persistence.

### P2 acceptance

One asset must successfully demonstrate:

```text
ordinary geology
 -> sampled material
 -> Catalyze
 -> alternate material state
 -> traversal opportunity
 -> visual match to kilometer-scale molt layer
```

before generating a whole biome.

---

# 9. P3 — Horizon Eater Houdini work

P3 needs huge perceived scale without huge simulation.

## Core fiction

The Horizon Eater is a filter feeder whose feeding behavior compresses adjacency. Distant ecological material is drawn into temporary shared flow corridors. The mouth spans what the player initially reads as the horizon.

Houdini's job is to manufacture the **illusion of one anatomical geometry distributed across landscape scale**.

## HDA_P3_HorizonMouthComposer

Inputs:
- reveal camera(s);
- upper mountain/ridge curve;
- lower mountain/ridge curve;
- mouth-depth volume;
- filter-plate guide curves;
- atmospheric occlusion volumes.

Outputs:

```text
UpperHorizonProxy
LowerHorizonProxy
FilterPlateFarMeshes
MouthDepthCardsOrMeshes
SilhouetteMask
RevealAlignmentData
HLOD/FarLOD variants
```

The reveal must work first as ordinary skyline.

### Composition test

Build a Houdini camera projection diagnostic:
- render/preview skyline silhouette from reveal camera;
- measure gape width in screen space;
- visualize filter plate readability;
- validate that mouth interpretation is ambiguous before reveal and obvious after state change.

Do not require the entire mouth mesh to move.

Prefer:
- Runtime Data Layer swaps;
- material state changes;
- small transform changes on a handful of skyline proxies;
- fog/cloud changes;
- filter plate visibility;
- synchronized far-field animation.

## HDA_P3_WayfoldAuthoring

Inputs:
- Entry point;
- Exit point;
- local orientation frames;
- optional route curve;
- obstruction volumes;
- destination bounds.

Outputs data/locators:

```text
EntryTransform
ExitTransform
EntryPreviewPlane
ExitPreviewPlane
CameraOcclusionSuggestion
CompanionLandingTransforms
StreamingPrewarmBounds
```

Do not build non-Euclidean runtime geometry in Houdini.

UE `BP_WayfoldPair` owns crossing and streaming.

## HDA_P3_FilterFlowField

Generate offline curves/points representing:
- pollen paths;
- cloud-dust flow;
- bird migration bend;
- grass orientation bias;
- debris/filter approach.

Export as:
- curves/splines;
- point clouds;
- PCG point data;
- CSV/DataTable-friendly attributes if useful.

If Houdini-Niagara proves stable on UE5.8 locally, point caches can drive some hero VFX; otherwise use the exported curve/point data to construct standard Niagara systems.

## HDA_P3_DistanceEvidenceScatter

Create intentionally impossible adjacency evidence:
- alpine species beside lowland species;
- pollen/debris from distant biome;
- rock/mineral fragments sourced from another region;
- navigation markers whose measured distance contradicts visible distance.

This HDA outputs **placement hypotheses**, not final storytelling placement. Hero contradictions remain hand-authored.

### P3 acceptance

Prototype succeeds when one 5–10 minute region proves:

1. visible landmark distance contradiction;
2. one Wayfold crossing;
3. Mara Anchor stabilizes one local metric relationship;
4. environmental matter physically supports the spatial anomaly;
5. filter-flow direction becomes legible;
6. skyline resolves into a horizon-scale mouth;
7. the mouth never needs a giant full-body rig.

---

# 10. Unreal/Houdini ownership boundary

## Houdini owns

- terrain manufacture;
- mesh variants;
- masks;
- UVs;
- LODs;
- collision generation;
- procedural accessory/detail families;
- offline scatter candidate points;
- path/seam/filter curves;
- reveal-alignment geometry;
- PDG batch generation;
- KineFX character processing where useful.

## Unreal owns

- World Partition runtime streaming;
- Runtime Data Layer activation;
- PCG runtime/streamed scatter;
- Oceanology/water authority;
- rhythm subsystem;
- Gameplay Tags / interaction contract;
- StateTree/encounter logic;
- Wayfold teleport/transform logic;
- Catalyze state logic;
- SaveGame persistence;
- Niagara playback;
- MetaSounds/audio;
- Sequencer/camera;
- final hand-authored lighting/composition.

---

# 11. Minimal HDA backlog — build in this order

Do not start all HDAs simultaneously.

## Tier 0 — immediate production return

```text
[ ] HDA_ENV_LOD_Collision_Batch
[ ] HDA_CH_CurlCluster
[ ] HDA_ENV_TerrainStamp
[ ] HDA_ENV_ScatterMaskBuilder
```

These help the whole project immediately.

## Tier 1 — P1 proof

```text
[ ] HDA_P1_TensionValley
[ ] HDA_P1_SeamGraph
[ ] HDA_P1_BannerPrayerStripField
```

## Tier 2 — P2 proof

```text
[ ] HDA_P2_MoltLayerFamily
[ ] HDA_P2_MoltRavine
[ ] HDA_P2_EcologyOnMolt
```

## Tier 3 — P3 proof

```text
[ ] HDA_P3_HorizonMouthComposer
[ ] HDA_P3_WayfoldAuthoring
[ ] HDA_P3_FilterFlowField
```

## Tier 4 — only after region scale demands it

```text
[ ] PDG region tiler
[ ] World Partition terrain batch tools
[ ] automated HLOD-prep pipeline
[ ] Houdini-PCG graph integration for expensive specialized operations
```

---

# 12. First three work sessions

## Session A — Mara + plugin validation

**Target: one evening**

```text
[ ] verify Houdini Engine UE5.8 session
[ ] verify Node Sync / Session Sync
[ ] send one Unreal static mesh UE -> Houdini -> UE
[ ] send Melusina reference mesh/skeleton into Houdini
[ ] establish Mara proxy proportions beside Melusina
[ ] establish shoulder/perch sockets for Ebenezer
[ ] create HDA_CH_CurlCluster v0
[ ] export one curl test back to Unreal
```

Do not sculpt the full coat tonight.

## Session B — Faraway Mother procedural blockout

```text
[ ] create 1 km-ish prototype valley heightfield
[ ] place 5 tension anchors
[ ] draw one player route curve
[ ] generate 3 major cloth/geography folds
[ ] generate one seam graph
[ ] establish one local cloth target and one distant linked fold
[ ] bake proxies into Unreal
[ ] author one Blueprint interaction where local tug causes distant response
[ ] test reveal from final camera
```

Goal is a greybox interaction, not pretty cloth simulation.

## Session C — God That Molts material proof

```text
[ ] author/sculpt one base molt plate
[ ] create 4 related procedural states
[ ] preserve pivots/material slots
[ ] export CatalyzeMask
[ ] create hand specimen using same seam generator
[ ] create cliff-scale variant using same generator
[ ] import to UE
[ ] build one Catalyze state swap/blend
[ ] confirm specimen and cliff visibly share anatomy
```

Only after this works should the ravine biome expand.

---

# 13. Definition of done before P3 production starts

Do not move into full Horizon Eater production until:

### Character
- Mara LOD0 body/face silhouette is approved in UE.
- Existing locomotion/retarget works.
- Ebenezer perch sockets exist.

### P1
- one tension-valley route works;
- distant cloth response works;
- Faraway Mother reveal works from gameplay camera.

### P2
- one Catalyze interaction works;
- micro specimen and kilometer-scale layer share the same visual anatomy;
- current-body evidence is authored.

### Pipeline
- HDA outputs can be baked cleanly;
- generated assets have stable names/folders;
- no playable map relies on an HDA being live at runtime;
- PCG/Houdini responsibilities are clear.

---

# 14. Anti-scope rules

Do not build yet:
- generalized non-Euclidean geometry engine;
- runtime cloth simulation for kilometer-scale Faraway Mother;
- runtime chemistry simulator;
- giant skeletal rig for any P0–P3 Monolith;
- a universal procedural world generator;
- procedural hero-character face generator;
- full Houdini-Niagara dependency before UE5.8 verification;
- one HDA that tries to generate an entire chapter.

Prefer a family of small legible HDAs that each answer one production question.

---

# 15. Best immediate task

If opening Houdini right now, start here:

```text
1. Start Houdini Engine session from UE5.8.
2. Node Sync Melusina's skeletal/body reference into Houdini.
3. Build a Mara proportion cage/proxy around that scaffold.
4. Export the proxy back beside Melusina.
5. Create HDA_CH_CurlCluster with 5–10 guide curves.
6. Stop and test in Unreal before creating any more character detail.
```

Then begin `HDA_P1_TensionValley` with only five anchors and three giant folds.

That sequence proves the character pipeline and the most important procedural level-design idea without committing the project to a large procedural framework.
