# UE 5.8 Procedural Worldbuilding — TEST NOW Addendum

**Date:** 2026-09-11  
**Status:** RESEARCH / IMPLEMENTATION CANDIDATES — only items worth practical testing now  
**Authority boundary:** This document does **not** replace [`Docs/WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md`](../WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md). Runtime truth remains C++-owned; PCG/Houdini/Python/material systems are authoring and presentation consumers unless an existing runtime contract explicitly says otherwise.  
**Related:** [`EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH_2026-08-30.md`](EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH_2026-08-30.md), [`NMS_SCALE_PROCEDURAL_AUDIO_REACTIVE_PIPELINES_2026-09-02.md`](NMS_SCALE_PROCEDURAL_AUDIO_REACTIVE_PIPELINES_2026-09-02.md), [`../Pipelines/MELODIA_CYMATICS_MONOLITH_HOUDINI_EMERGING3D_PIPELINE.md`](../Pipelines/MELODIA_CYMATICS_MONOLITH_HOUDINI_EMERGING3D_PIPELINE.md)

---

## Executive decision

Do **not** open another generalized procedural framework. The highest-value near-term proof is one small **Resonance Ecology** chain that exercises the current Melodia stack end to end:

```text
Houdini 21
  cymatic / terrain field
  -> attributed points

UE 5.8 PCG Python Data Processor
  -> derive Resonance
  -> EcologyClass
  -> MaterialVariant
  -> ScaleBias

UE PCG
  -> spawn 3-5 existing Melodia meshes

Material instance / per-instance custom data
  -> same resonance value drives roughness / iridescence / emissive response
```

This is a production experiment, not a new runtime authority.

### Priority order

1. **UE 5.8 PCG Python Data Processor / Python interop — TEST NOW**
2. **Houdini 21 -> Unreal PCG semantic point attributes — TEST NOW**
3. **GPU PCG + Custom HLSL for dense magical ecology — SANDBOX TEST**
4. **WorldClaw coarse-to-fine region hierarchy — STEAL THE DESIGN PATTERN ONLY**

Defer broad generative-world / diffusion research unless it can beat the above on a real Melodia task.

---

## 1. UE 5.8 PCG Python Data Processor — first test

### Why it matters

UE 5.8 adds a PCG Python Data Processor path that makes Python useful directly in PCG authoring instead of only as external editor automation. The useful Melodia pattern is to treat incoming PCG points as procedural data, derive semantic attributes in Python, and hand those attributes back to downstream PCG nodes.

### Practical role in Melodia

Use Python to classify and enrich points, not to own gameplay state.

Candidate attributes:

```text
Resonance
EcologyClass
MaterialVariant
ScaleBias
PitchClass
DistanceToWater
SlopeClass
CymaticBand
```

Example conceptual classifier:

```text
Resonance = f(height, slope, distance_to_water, cymatic_value, seed)
```

Downstream PCG then chooses meshes, density, orientation, material variants, decals, or VFX from those attributes.

### Smallest decisive experiment

Create a tiny test graph:

```text
Houdini points
-> PCG input
-> Python Data Processor
-> semantic classification
-> mesh/material selection
```

**Pass condition:** Python-derived attributes visibly change at least two downstream decisions in-engine without introducing a second runtime truth system.

**Evidence:**
- screenshot of graph;
- before/after point attribute dump;
- viewport showing at least two semantic classes;
- short note on execution limitations and whether the path is editor-only/baked for this use.

**Decision:** 🔥 TEST NOW.

---

## 2. Houdini 21 -> Unreal PCG — semantic point handoff

### Why it matters

The useful boundary is now clearer:

> **Houdini solves topology, spatial relationships, fields, and reusable procedural construction. Unreal PCG owns assembly, density, art direction, and placement of Unreal-native content.**

Do not build another monolithic HDA that tries to own the finished scene.

### Melodia use

Houdini outputs transforms plus a deliberately small semantic schema. Suggested first-pass fields:

```text
P / transform
resonance
family
scale_bias
material_variant
mask_or_band
```

UE PCG consumes them to place existing art-directed assets.

### Best first production proof

Use either:

- **Resonance Astrolabe:** modular instrument parts / silhouette families / cymatic motifs; or
- **Sea Above Resonance Ecology:** terrain/cymatic samples -> ecology points.

Prefer the ecology proof if the goal is to validate the entire procedural-worldbuilding chain in one shot.

### Stop rule

If the HDA starts accumulating Unreal-specific art direction that is easier to tune in PCG, stop and move that decision downstream.

**Decision:** 🔥 TEST NOW.

---

## 3. GPU PCG + Custom HLSL — dense magical ecology sandbox

### Why it matters

GPU PCG can make very dense procedural responses plausible without turning every small decorative element into CPU-side authored logic. The most interesting Melodia application is to let a **shared musical/cymatic field drive both geometry placement and shading**.

### Prototype

```text
Chladni / cymatic texture or field
-> GPU PCG field sampling
-> threshold / ridge / band classification
-> points
-> flowers / crystals / motes / reeds / decals
-> per-instance custom data
-> material response
```

The key idea is not "more particles." It is one authored musical field producing coherent geometry and material behavior.

### Good test scene

A single Sea Above or Monolithic Ecology patch with:

- 3-5 existing meshes;
- one Chladni/cymatic source;
- one material family;
- density high enough to expose whether GPU execution is materially useful.

### Safety boundary

Treat GPU PCG as an experimental authoring/performance lane until it has survived the project’s actual packaging and performance evidence gates. Do not make capstone-critical content depend on an unproven GPU-only path.

**Decision:** 🧪 SANDBOX TEST.

---

## 4. WorldClaw-style coarse-to-fine world specification — pattern only

### Useful idea

The valuable part is the hierarchy, not the AI generator. Formalize worldbuilding as an art-directable specification:

```text
Chapter
-> Region
-> Ecology
-> Landform
-> Asset Families
-> Material Family
-> Resonance Rules
-> PCG Recipe
```

This gives Python/Houdini/PCG a common vocabulary without creating a new gameplay subsystem.

### Tiny Melodia experiment

Write **one** machine-readable region specification for a Sea Above test region. Keep it intentionally small, for example:

```text
region_id
seed
landform_profile
ecology_family
asset_families
material_family
resonance_profile
pcg_recipe
```

Then test whether current tooling can consume it to configure the Houdini -> PCG -> material path.

Do not build a general world compiler until this proves useful on one authored region.

**Decision:** 🟡 STEAL THE DESIGN PATTERN; NO FRAMEWORK BUILD YET.

---

## Recommended implementation: Resonance Ecology v0

### Goal

Prove that one musical/cymatic source can drive **spatial generation + semantic classification + visual material response** while preserving existing ownership boundaries.

### Inputs

- one Chladni/cymatic texture or sampled Houdini field;
- one small terrain/plane patch;
- 3-5 existing Melodia meshes;
- existing material instances where possible;
- deterministic seed.

### Authoring chain

1. **Houdini** samples terrain/cymatic information and emits points.
2. **PCG Python** derives semantic attributes.
3. **UE PCG** maps semantic classes to existing meshes and density rules.
4. **Per-instance/custom material data** reuses `Resonance` or an equivalent scalar to control roughness / iridescence / emissive response.
5. Capture editor evidence and, if appropriate, a packaged-build proof before promotion.

### Minimum schema

| Attribute | Owner | Meaning |
|---|---|---|
| `Resonance` | Houdini or PCG Python | normalized shared world/material driver |
| `EcologyClass` | PCG Python | discrete spawn family |
| `MaterialVariant` | PCG Python | approved material-instance variation |
| `ScaleBias` | PCG Python | controlled size variation |
| `Seed` | source graph | deterministic regeneration |

### Pass criteria

- deterministic regeneration with the same seed;
- at least two ecology classes;
- at least two visible material responses from the same resonance field;
- no new SaveGame / gameplay / rhythm / quest authority;
- output is editable/art-directable in Unreal;
- the experiment is small enough to delete if it does not improve the authored result.

### Evidence bundle

```text
Docs/Evidence/ProceduralWorldbuilding/ResonanceEcology_v0/
  graph_overview.png
  houdini_point_attributes.png
  ue_pcg_classes.png
  material_response.png
  README.md
```

The evidence folder is a target convention only; do not commit generated evidence until the actual test exists.

---

## What not to do this week

- no generalized procedural-world framework;
- no second runtime ecology manager;
- no AI world generator dependency;
- no diffusion terrain pipeline unless it beats current terrain/Houdini work on a specific shot;
- no duplicated master material — reuse the current approved material families and the Nikki Cymatics path where Sheep are involved;
- no procedural system that hides artist control behind opaque random generation.

---

## Promotion rule

A technique moves from this research addendum into canonical production guidance only after a real Melodia test produces evidence.

Every spike ends with exactly one outcome:

- **ADOPT** — demonstrated production win; document the contract and reuse it.
- **PARK** — interesting, but no current production advantage.
- **REJECT** — adds complexity or reduces art direction without compensating value.

For the current cycle, the only required experiment is **Resonance Ecology v0**. Everything else should support that proof rather than expand scope.
