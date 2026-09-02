# Mara Elletra Vell / Melusina — AAA Houdini Hero Asset Production Blueprint

**Date:** 2026-08-31  
**Project:** Melodia Melusina / UE5.8 / Houdini 22  
**Status:** production-grade R&D blueprint; execute on a separate implementation branch  
**Build target:** one finished hero instrument family + one new garment family + shared cymatic authoring/runtime language  
**Supersedes:** this document deepens, but does not delete, `MARA_ELLETRA_HOUDINI_HERO_ASSET_CYMATICS_EXECUTION_PLAN_2026-08-31.md`.

---

# 0. Executive production decision

The target is **not** a collection of pretty procedural props. The target is a reusable character-asset production system capable of producing the kind of visual density, material coherence, animation readability, and authored variation expected from a high-end stylized RPG hero character.

The system should make the following sentence true:

> Mara/Elletra's instruments, garments, animation accents, materials, and runtime cymatic effects are all manifestations of one controlled design language rather than separate assets that happen to share motifs.

The AAA production stack is therefore:

```text
USER ART / CURRENT CHARACTER / CONCEPT TARGETS
        |
        +--> design authority + silhouette grammar
        |
        v
HOUDINI CHARACTER-ASSET COMPILER
        |
        +--> instrument frame grammar
        +--> cymatic pattern grammar
        +--> ornament grammar
        +--> garment panel grammar
        +--> Vellum offline drape
        +--> KineFX / deformation preparation
        +--> hero / gameplay / proxy representations
        +--> Copernicus bake + masks
        |
        v
UNREAL 5.8 ASSET ASSEMBLY
        |
        +--> Static / Skeletal / Chaos Cloth assets
        +--> toon / pearl / glass / fabric materials
        +--> Niagara Data Channel presentation
        +--> authored transform states
        +--> animation sockets / secondary motion
        |
        v
RUNTIME PERFORMANCE + ART QA
```

Houdini remains an **authoring/compiler dependency only**. Unreal remains gameplay, animation, rendering, cloth-runtime, and shipping authority.

---

# 1. Visual authority and reference hierarchy

Character identity must be protected from procedural drift.

Reference priority:

1. **User-authored character artwork** — face, proportions, line economy, attitude, silhouette language.
2. **Current in-engine Melusina/Mara assets** — actual proportions, costume scale, hand scale, gameplay-camera readability.
3. **Existing character/companion concept sheets** — ornament, palette, instrument relationship, narrative role.
4. **Generated weapon/instrument sheets** — breadth of prop silhouettes and construction ideas only.
5. **External technical references** — construction/material/engineering inspiration, never direct art-direction authority.

The generated concept sheets are intentionally treated as **design-space exploration**, not canonical character art.

Tracked visual board:

```text
Docs/Plans/Images/mara_elletra_aaa_asset_reference_board_16x9_2026-08-31.svg
```

Art rule:

> If a procedural result is technically impressive but makes Mara/Elletra look like a different game's character, it fails.

---

# 2. AAA quality pillars

Every hero asset is reviewed against six pillars.

## P1 — silhouette hierarchy

At gameplay distance the player should identify:

1. overall instrument family;
2. major resonator/ring/harp mass;
3. grip and hand relationship;
4. one signature asymmetry;
5. only then small ornament.

No amount of filigree can compensate for a weak 3–5 meter silhouette.

## P2 — material storytelling

Material families must be physically and narratively distinct:

- abyssal/brushed brass = structural calibration hardware;
- pearl/shell = resonant organic memory;
- crystal/glass = field conduction / spectral response;
- enamel/lacquer = designed human intervention;
- fabric/lace = soft carrier of pattern memory;
- emissive inlay = active cymatic state, not generic neon trim.

## P3 — mechanical believability

Even magical instruments need understandable construction.

Every moving component should answer:

- what supports it?
- what rotates/slides/flexes?
- where does force travel?
- what is rigid vs compliant?
- where would a performer grip it?
- how does it rest when not active?

## P4 — procedural authorship without procedural sameness

The compiler must produce families, not clones.

Variation should happen at multiple scales:

```text
macro: silhouette / frame topology
meso: ring count / resonator form / string layout / shell arrangement
micro: engraving / pearl spacing / fasteners / surface breakup
state: idle / measuring / harmonizing / burst / damaged or disrupted
```

## P5 — animation readability

A hero prop must offer usable animation channels.

At minimum:

- one major mechanical motion;
- one secondary delayed motion;
- one small rhythmic response;
- one material/emissive response;
- one surrounding VFX response.

This layered response is what makes an object feel expensive.

## P6 — runtime discipline

The hero asset must survive:

- gameplay camera;
- close dialogue/cutscene framing;
- TSR/DLAA/DLSS temporal reconstruction;
- lower scalability tiers;
- packaged build;
- source-control reopen;
- deterministic rebuild from source manifest.

---

# 3. Character-specific design language

## 3.1 Mara / Elletra

Her instruments should read as **measurement devices that happen to be musical**.

Primary motifs:

- astrolabe / survey geometry;
- concentric calibration rings;
- suspended weights;
- tuned strings and chimes;
- field lenses;
- compass/eye/rose-window constructions;
- controlled asymmetry;
- scholarly mechanical density rather than brute weapon mass.

Recommended silhouette ratio:

```text
60% elegant vertical / circular survey geometry
25% instrument language
15% weapon-danger implication
```

Avoid turning every instrument into a spear or fantasy scythe.

## 3.2 Melusina

Her family should read as **sea-grown instruments disciplined into playable artifacts**.

Primary motifs:

- shell chambers;
- pearl nodal points;
- water-current curves;
- coral branching;
- translucent membranes;
- tide pendulums;
- softer curvature than Mara/Elletra's measured structures.

Recommended ratio:

```text
55% living/marine form
30% musical mechanism
15% human-made structural restraint
```

The two families should share cymatic mathematics but differ in how that mathematics is embodied.

---

# 4. Asset family architecture

Build four reusable instrument chassis.

## A — Survey Chassis

Targets:

- Resonance Astrolabe
- Sonic Scepter
- Cartographer's Rod
- Lattice Rod
- Monolith Tuner
- Field Compass

Core modules:

```text
shaft
survey_head
ring_stack
resonator_disc
pendulum
calibration_weights
lens
ornament_rail
hand_grip
```

## B — Tension Chassis

Targets:

- Ripple Lyre
- Wave Harp
- Pearl Harp
- Choral Cage
- Measureless Lute

Core modules:

```text
outer_frame
bridge_A
bridge_B
string_array
resonator_body
tuning_nodes
hanging_chimes
shoulder_or_hip_rest
```

## C — Chamber Chassis

Targets:

- Phase Bell
- Veil Drum
- Tidal Disc
- Echo Orb
- Shell Drum
- Coral Conch

Core modules:

```text
shell_body
membrane
radial_frame
suspension
impact_or_activation_zone
resonator_surface
apertures
secondary_chimes
```

## D — Transform Chassis

Targets:

- Crescendo Fan
- Harmonic Seeder
- Current Flute
- anomalous Monolith variants

These explicitly support state-changing geometry.

---

# 5. Houdini package architecture

Implementation branch target:

```text
Tools/Houdini/mara_elletra/
  README.md
  config/
    mara_elletra_asset_manifest.v2.json
    instrument_family_contract.v1.json
    garment_panel_contract.v1.json
    cymatic_pattern_presets.v1.json
    ornament_grammar.v1.json
    material_family_contract.v1.json
    runtime_budget_contract.v1.json

  hda/
    HDA_MEL_Instrument_Frame_v001.hda
    HDA_MEL_Instrument_RingStack_v001.hda
    HDA_MEL_Instrument_StringArray_v001.hda
    HDA_MEL_Instrument_ChimeArray_v001.hda
    HDA_MEL_Instrument_Resonator_v001.hda
    HDA_MEL_Instrument_OrnamentGrammar_v001.hda
    HDA_MEL_Instrument_VariantCompiler_v001.hda
    HDA_MEL_Garment_PanelPrep_v001.hda
    HDA_MEL_Garment_ResonanceDetail_v001.hda
    HDA_MEL_CymaticPattern_v001.hda

  instrument/
    build_instrument_family.py
    build_game_representation.py
    build_animation_parts.py

  garment/
    import_garment_contract.py
    build_vellum_proxy.py
    build_resonance_details.py
    build_garment_states.py
    export_cloth_sources.py

  cymatics/
    build_scalar_field.py
    build_vector_field.py
    extract_nodal_curves.py
    project_pattern_to_surface.py

  copernicus/
    bake_instrument_maps.py
    bake_garment_maps.py
    build_iridescent_masks.py
    build_cymatic_emission.py

  export/
    export_unreal_static.py
    export_unreal_skeletal.py
    export_chaos_cloth_sources.py

  qa/
    validate_manifest.py
    validate_scale_axis.py
    validate_material_slots.py
    validate_animation_parts.py
    validate_uv_texel.py
    validate_runtime_budget.py
    validate_deterministic_rebuild.py
```

---

# 6. Geometry generation: hero-prop standard

## 6.1 Guide-curve first

Every instrument begins as a deliberately tiny semantic blockout:

```text
CENTERLINE
SILHOUETTE_L
SILHOUETTE_R
GRIP_XFORM
RESONATOR_XFORM
PRIMARY_MOTION_AXIS
SECONDARY_MOTION_AXIS
ORNAMENT_ZONES
```

These guides should be editable quickly in Houdini or imported from Blender.

Do not let early procedural networks bury the artistic decisions inside hundreds of nodes.

## 6.2 Frame construction

Recommended SOP flow:

```text
curve input
 -> resample
 -> orient along curve
 -> width/taper ramp
 -> Sweep SOP
 -> local profile deformation
 -> junction preparation
 -> selective Boolean/VDB join
 -> Quad Remesh where needed
 -> PolyBevel
 -> Normal / weighted normal preparation
 -> semantic groups
```

Avoid VDB-unioning the entire object. Use it only for difficult organic junctions; preserve crisp manufactured rails as clean polygonal construction.

## 6.3 Structural detail frequency bands

Think in three bands.

### Macro detail

Must survive gameplay distance:

- outer silhouette;
- ring stack;
- large blades/petals;
- resonator chamber;
- big asymmetry.

### Meso detail

Readable in inventory/dialogue:

- ribs;
- bridge mechanisms;
- clamps;
- pearl settings;
- large engravings;
- knobs/dials;
- shell layering.

### Micro detail

Close-up only:

- tiny engraving;
- fasteners;
- etched numerals;
- hairline seams;
- micro filigree;
- material roughness breakup.

Micro detail defaults to **baked/masked**, not geometry.

## 6.4 Part semantics

Every generated part carries:

```text
mel_asset_id
mel_variant_id
mel_part_id
mel_part_class
mel_material_family
mel_motion_channel
mel_socket_id
mel_cymatic_receiver
mel_lod_class
mel_bake_only
mel_runtime_keep
```

This makes downstream export deterministic and lets the game representation diverge from the authoring mesh without losing meaning.

---

# 7. Cymatic design system — from decorative motif to asset DNA

The first plan defined `melodia.cymatic-pattern.v1`. The AAA version expands the concept into a library.

## 7.1 Pattern families

```text
MEL_CYM_ROSE_*       radial / rose-window resonance
MEL_CYM_TIDE_*       flowing offset interference
MEL_CYM_LATTICE_*    repeating calibration lattice
MEL_CYM_CHLADNI_*    plate-like nodal forms
MEL_CYM_MONOLITH_*   intentionally broken/asymmetric modes
MEL_CYM_MEMORY_*     softened residual/echo forms
```

## 7.2 Pattern outputs

One pattern preset should be able to output:

1. scalar field;
2. nodal curves;
3. crest curves;
4. gradient/vector field;
5. signed/normalized mask;
6. geometry displacement guide;
7. embroidery guide;
8. Niagara/runtime parameter preset.

## 7.3 Surface adaptation

A flat cymatic pattern should not simply be UV-stamped onto every asset.

Support three projection modes:

```text
UV_DOMAIN       predictable material-space motif
GEODESIC-ish    surface-following engraving/embroidery
FRAME_FIELD     pattern bent by surface principal direction / authored vector field
```

For hero props, use the pattern to affect **construction**, not just decoration:

- apertures happen at node intersections;
- pearl settings occupy high-coherence points;
- ring braces align to dominant radial bands;
- fabric stitch density follows field amplitude;
- scale orientation follows the gradient.

That is how the cymatic language becomes believable world design.

---

# 8. Copernicus material/bake pipeline

The repo already has a true Copernicus direction replacing ad-hoc PIL rasterization. Preserve that trajectory.

Official SideFX reference:

- https://www.sidefx.com/docs/houdini/nodes/cop/bakegeometrytextures.html

Use Copernicus for:

```text
high -> game bake
curvature
AO
thickness
position / normal
cymatic mask
ornament ID mask
material family ID mask
fabric weave mask
pearl/shell response masks
emission mask
micro-height
```

## 8.1 Hero instrument texture strategy

Do not create a unique 4K texture set for every small variant by default.

Prefer:

```text
shared tiling metal / shell / crystal detail
+ trim / ornament atlas
+ per-asset cymatic mask
+ per-asset packed ID/roughness mask
+ optional hero normal/height sheet where truly needed
```

This supports visual richness without texture-memory explosion.

## 8.2 Geometry vs normal decision

Keep geometry when it affects:

- silhouette;
- shadow shape;
- parallax at expected camera distance;
- actual moving mechanism.

Bake when it only affects:

- shallow engraving;
- micro trim;
- surface scratches;
- tiny filigree;
- weave.

---

# 9. Unreal representation strategy

## 9.1 Rigid hero body

Use normal static meshes, with Nanite evaluated where useful.

UE5.8 Nanite supports static and skeletal meshes but does not support Morph Targets, and opaque/masked materials are the safe baseline. Translucent resonator/glass surfaces should therefore remain separate non-Nanite components.

Official references:

- https://dev.epicgames.com/documentation/unreal-engine/nanite-virtualized-geometry-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/nanite-technical-details

Recommended split:

```text
SM_Mara_Astrolabe_Body       opaque / optional Nanite
SK_Mara_Astrolabe_Rings      animated rigid parts
SM_Mara_Astrolabe_Strings    conventional low-cost geometry
SM_Mara_Astrolabe_Glass      translucent, non-Nanite
```

## 9.2 Moving mechanisms

For ring stacks and large moving parts, choose among:

1. skeletal mesh rigid skinning;
2. separate static-mesh components;
3. vertex animation/material motion for tiny repeated elements.

Default to the simplest system that preserves animation direction and authoring clarity.

## 9.3 Runtime response layers

A high-end response stack should be staggered:

```text
T+0 ms      material flash / field response
T+20-80 ms  primary ring/dial movement begins
T+60-180 ms secondary chimes/pendants follow
T+80-250 ms Niagara field expands
T+150ms+    ecological memory/pollen settles
```

Do not trigger every layer at exactly the same frame.

---

# 10. Garment pipeline — AAA hybrid, not one-solver dogma

The offline and runtime cloth systems should have different jobs.

## 10.1 Houdini / Vellum job

Houdini owns:

- panel preparation;
- exploratory drape;
- silhouette solving;
- wrinkle/pleat design studies;
- authored rest states;
- resonance-state target shapes;
- garment detail distribution;
- simulation caches for reference or bake.

It does **not** need to be the shipping cloth solver.

## 10.2 UE5.8 Chaos Panel Cloth job

UE5.8's Panel Cloth workflow is a non-destructive Dataflow-based runtime cloth pipeline that supports external panel-based DCC inputs, simulation/render mesh separation, skin-weight transfer, XPBD constraints, weight maps and physics-asset collision.

Official reference:

- https://dev.epicgames.com/documentation/unreal-engine/panel-cloth-editor-overview
- https://dev.epicgames.com/documentation/unreal-engine/dataflow-overview

Therefore the production model should be:

```text
Houdini/Vellum = design + authored cloth source
UE Chaos Cloth = runtime simulation authority where cloth is needed
```

## 10.3 Garment layer architecture

Mara/Elletra Surveyor Mantle:

```text
L0 body fit / underlayer
L1 inner silk
L2 main coat
L3 structured mantle panels
L4 sleeves
L5 collar / shoulder structure
L6 cymatic embroidery and piping
L7 rigid shell / brass / pearl trim
L8 tassels / chains / pendants
L9 optional translucent veil pieces
```

Each layer carries explicit collision and simulation rules.

## 10.4 Render mesh vs simulation mesh

Never simulate the full decorated hero render mesh directly if a lighter proxy can drive it.

Use:

```text
SIM mesh   -> clean, low-density, stable triangles
RENDER mesh-> final folds, trim, embroidery, shell detail
```

Transfer/deform detail from the simulation result.

## 10.5 Shorewake repair as mandatory precursor

Before calling the garment stack production-ready:

- move canonical source out of Downloads/Desktop;
- hash-pin source;
- repair panel indexing;
- standardize numeric panel order;
- resolve the dead Houdini-weight handoff;
- generate per-stage manifests;
- create render/sim mesh distinction;
- reduce brute-force plate geometry;
- prove one packaged runtime cloth test.

---

# 11. Character attachment and interaction design

Hero props need authored relationships to body and costume.

Create sockets/contracts for:

```text
hand_R_primary
hand_L_support
back_holster
hip_holster
mantle_mount
instrument_rest
companion_perch
```

For Ebenezer-compatible designs, add dedicated perch/interaction transforms rather than letting animation solve arbitrary positions every time.

Potential companion behaviors:

- lands on tuning ring;
- taps calibration weight;
- reacts to unstable resonance;
- steals/relocates a tuning token;
- acts as visual scale cue on oversized instruments.

These should be treated as animation opportunities, not baked into the procedural geometry network.

---

# 12. Animation-state package

Each hero instrument should ship with a small state library.

Minimum:

```text
REST
DRAW / EQUIP
MEASURE
TUNE
HARMONIZE
PERFECT_BURST
MISS_DISRUPT
SHEATHE
```

Mechanism channels:

```text
RingA_Rotation
RingB_Rotation
Resonator_Pulse
Pendulum_Swing
String_Response
Chime_Response
Glass_Iridescence
Cymatic_Emission
```

The Houdini manifest should export these part identities so Unreal animation setup is stable across variants.

---

# 13. Runtime cymatic bridge

The authoritative source remains:

```cpp
UMelodiaRhythmCombatSubsystem::OnLaneHitJudged
```

Existing code documents it as presentation-only and fires it once per judged press, including misses.

Do not add:

- a second timer;
- duplicate grading;
- VFX feedback into combat authority;
- runtime Houdini cooking.

Presentation architecture:

```text
OnLaneHitJudged
  -> BP_MelodiaCymaticHeroInstrument
       -> local instrument state
       -> MID / material parameters
       -> ring/chime animation request
       -> NDC_MelodiaRhythmPulse
  -> NS_Melodia_CymaticField / Memory
```

Grade art language:

```text
Perfect = phase lock, clean symmetry, crisp resonance
Great   = near-lock, slight drift
Good    = unstable wide bands, softer coordination
Miss    = destructive phase, interruption, brief collapse
```

---

# 14. Art-budget model

Do not use one global triangle limit. Budget by representation and importance.

For each prop record:

```text
hero_authoring_triangles
hero_runtime_triangles_or_nanite_input
animated_non_nanite_triangles
translucent_triangles
material_slots
unique_texture_memory
shared_texture_memory
skeletal_bones_or_rigid_parts
Niagara GPU cost
draw calls / passes
```

Recommended constraints are evidence-based, not arbitrary:

- one hero prop may be expensive in a close shot;
- the same asset must have a cheaper gameplay state;
- translucent area must be aggressively controlled;
- material-slot count should be minimized after authoring;
- tiny repeated geometry must justify itself against normal/mask alternatives.

---

# 15. LOD / representation tiers

Even with Nanite, define art tiers.

## HERO

Inventory/cinematic:

- full silhouette geometry;
- hero engravings where justified;
- best glass/shell treatment;
- all primary moving parts;
- dense ornament.

## GAMEPLAY

- same silhouette;
- reduced tiny filigree;
- simplified chimes/strings;
- baked micro engraving;
- bounded translucency;
- full rhythm response.

## DISTANT / HOLSTERED

- simplified mechanisms;
- emission as primary read;
- no invisible internal geometry;
- minimal secondary animation.

---

# 16. Technical QA gates

Every accepted variant must pass:

## Geometry

- clean transforms/pivots;
- no degenerate/non-manifold surprises on game representation;
- deliberate hard/soft normals;
- no floating micro parts without purpose;
- correct hand scale.

## UV/material

- texel density logged;
- trim/shared material opportunities used;
- packed masks validated;
- transparent areas isolated;
- cymatic mask ID matches manifest.

## Animation

- motion axes exported correctly;
- no part-name drift;
- one draw/equip motion;
- one judged-hit response;
- no skinning explosions after reopen.

## Runtime

- fixed camera baseline;
- `stat gpu` capture;
- TSR/DLAA/DLSS observation;
- packaged build;
- repeated PIE/reopen;
- no duplicate event binding;
- low-setting readability.

## Determinism

- source hashes;
- HDA version;
- seed;
- output hashes where practical;
- same source + settings reconstructs semantically equivalent output.

---

# 17. Review gates inspired by AAA character production

Use explicit art reviews instead of waiting until the end.

## Gate R0 — concept translation

Deliver:

- 6–12 black silhouettes;
- hand/character scale;
- mechanism sketch;
- one material key.

No detail modeling yet.

## Gate R1 — blockout

Deliver:

- UE-imported greybox;
- hand placement;
- gameplay camera;
- inventory camera;
- major motion test.

## Gate R2 — high-detail structural pass

Deliver:

- final primary/secondary geometry;
- ornament zones;
- cymatic construction integrated;
- no final micro polish yet.

## Gate R3 — game representation

Deliver:

- static/skeletal split;
- UVs;
- material IDs;
- game topology/representation;
- animation part naming.

## Gate R4 — materials

Deliver:

- Copernicus bake;
- toon/material integration;
- glass/pearl solution;
- emissive cymatic masks;
- reference lighting shots.

## Gate R5 — runtime character integration

Deliver:

- equip/draw;
- judged-hit response;
- Niagara field;
- garment interaction;
- temporal reconstruction test.

## Gate R6 — final QA

Deliver:

- deterministic rebuild notes;
- packaged build;
- source-control reopen;
- performance table;
- hero/gameplay comparison;
- ADOPT/PARK/REJECT decision.

---

# 18. First flagship asset: Resonance Astrolabe

This should be the first asset taken through the entire stack.

## Required visual features

- unmistakable circular survey silhouette;
- 2–4 nested rings;
- central cymatic resonator;
- one glass/pearl lens;
- one pendulum/calibration weight;
- asymmetric ornament cluster;
- functional grip;
- one visible physical hinge or gimbal.

## Required procedural features

- editable ring count/radii;
- replaceable cymatic pattern;
- ornament grammar controls;
- hero/game representation switch;
- deterministic material IDs;
- stable animation part names.

## Required runtime features

- Perfect locks rings into coherent alignment;
- Great nearly aligns with residual drift;
- Good creates looser phase;
- Miss interrupts alignment;
- resonator emission uses the same `MEL_CYM_001` family;
- Niagara pulse expands into world field.

This is the **golden asset**. Every later instrument pipeline decision is judged against it.

---

# 19. Second flagship asset: Ripple Lyre

The Lyre proves that the system generalizes beyond circular survey props.

Goals:

- procedural curved outer frame;
- deterministic string array;
- per-string semantic frequency ratio;
- visible bridge mechanics;
- wave-like cymatic pattern traveling across resonator/body;
- delayed string/chime response.

If the Astrolabe and Lyre both succeed using shared modules, the family architecture is credible.

---

# 20. First flagship garment: Surveyor Mantle

Goals:

- preserve the broad, layered silhouette from the concept direction;
- fit current character proportions;
- distinguish soft inner layers from structured outer pieces;
- create visible instrument harnessing;
- use one cymatic pattern as actual embroidery construction;
- support at least one `HARMONIZE` authored state;
- prove Chaos Cloth runtime on selected layers rather than simulating everything.

Signature feature:

> During high coherence, cymatic embroidery should visually organize along the garment before the surrounding world responds.

This makes the character the first readable scale of the larger ecological system.

---

# 21. PC execution order

## Tonight / first sitting

1. create implementation branch;
2. create stable `ArtSource/MaraElletra` root;
3. hash-pin current character and garment sources;
4. make 6 Astrolabe silhouettes;
5. choose one and build centerline + ring guides;
6. build `HDA_MEL_Instrument_RingStack_v001`;
7. build `MEL_CYM_001` field + nodal curves;
8. engrave one resonator;
9. export greybox into UE;
10. verify character hand scale and gameplay silhouette.

**Do not spend the first sitting polishing filigree.**

## Second sitting

1. split moving rings from rigid body;
2. create basic material families;
3. Copernicus cymatic/emission mask;
4. wire `BP_MelodiaCymaticHeroInstrument`;
5. bind `OnLaneHitJudged`;
6. create Perfect/Great/Good/Miss motion/material language;
7. capture fixed-camera evidence.

## Third sitting

1. Shorewake v2 contract repair;
2. simulation/render proxy separation;
3. project `MEL_CYM_001` to selected garment panel;
4. one Vellum-authored resonance state;
5. Chaos Cloth canary in UE.

## Fourth sitting

1. Ripple Lyre;
2. test reuse of frame/resonator/cymatic modules;
3. compare time-to-first-useful result against Astrolabe;
4. only then start broad instrument family expansion.

---

# 22. Evidence bundle

Each flagship asset stores:

```text
Docs/Research/Evidence/MaraElletraHeroAssets/<AssetId>/
  README.md
  source_manifest.json
  hda_manifest.json
  cymatic_pattern.json
  silhouette_review.md
  material_review.md
  runtime_review.md
  perf.csv
  package_test.md
  deterministic_rebuild.md
  decision.md
```

Screenshots should include:

- flat concept comparison;
- greybox in hand;
- gameplay camera;
- close material shot;
- Perfect response;
- Miss response;
- low scalability state.

---

# 23. Promotion rubric

## ADOPT

The pipeline produces at least two visually different hero instruments and one garment using shared modules; character identity is preserved; rebuilds are predictable; runtime reactions are cheap and readable.

## PARK

The procedural authoring is useful but creates excessive cleanup, or the result only looks strong in static renders.

## REJECT specific modules

Reject any module that:

- adds procedural complexity without reducing iteration time;
- destroys silhouette control;
- produces fragile game topology;
- needs runtime Houdini cooks;
- requires giant unique texture sets for every variant;
- creates microgeometry with no visible payoff;
- forces garment simulation onto decorative rigid details;
- duplicates rhythm authority.

---

# 24. Final production thesis

The grand version of this pipeline is not "procedural weapons."

It is a **character-scale semantic compiler**:

```text
music / measurement / tide / memory
        ↓
cymatic field definition
        ↓
prop construction
+ garment construction
+ material organization
+ animation channels
+ world VFX response
        ↓
one recognizable Melodia language
```

If executed correctly, the player should be able to look at Mara/Elletra's instrument, her embroidery, a nearby cymatic field in the water, and the arrangement of particles around her and intuit that all four phenomena belong to the same underlying rules.

That is the AAA target: not maximum complexity, but **coherent complexity whose logic survives from concept art to runtime**.
