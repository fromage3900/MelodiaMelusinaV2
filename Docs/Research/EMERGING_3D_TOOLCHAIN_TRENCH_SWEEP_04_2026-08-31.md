# Emerging 3D Toolchain — Trench Sweep 04

**Date:** 2026-08-31
**Project:** Melodia Melusina / UE5.8
**Status:** R&D findings + priority refinement
**Companion:** `TOOLCHAIN_KICKOFF_2026-08-30_CASCADEUR_ILLUGEN_BLENDER_RHYTHM.md`

## Executive result

The latest sweep does not justify adding more production dependencies. It does reveal a stronger architectural lane: **music as structured procedural world-authoring data**, interpreted across Blender, Houdini and Unreal.

The most project-specific opportunity is no longer simply “Blender MIDI geometry.” It is a small **Melodia Musical World Compiler** experiment:

```text
MIDI semantic events -----------+
                                |
rendered audio / stems ---------+--> musical authoring representation
                                |          |
                                |          +--> Blender: fast form + motion sketching
                                |          +--> Houdini: fields + topology + semantic processing
                                |          +--> Copernicus/IlluGen: visual evidence + residue
                                |          +--> Unreal: native baked assets + runtime convergence
                                |
Unreal rhythm subsystem --------+--> remains runtime/gameplay authority
```

This is an authoring compiler, **not another runtime rhythm system**.

---

# Findings worth retaining

## Blender 5.2 procedural architecture — PROMOTE

The useful story is the combination of newer Geometry Nodes primitives rather than one MIDI node:

- `Sample Sound Frequencies`: continuous spectral response from rendered audio;
- Lists: variable-length structured procedural data;
- Geometry Bundles: carry arbitrary structured data with geometry across graph/object boundaries;
- closures: reusable injected behavior rather than graph duplication;
- attribute-transfer/introspection improvements;
- experimental XPBD-backed Geometry Nodes physics.

There is no assumption of a native MIDI reader. MIDI remains a small parse/import bridge feeding structured event data.

### Melodia interpretation

Define a minimal event contract conceptually equivalent to:

```text
MusicalEvent
    note
    velocity
    channel
    start_time
    duration
    normalized_beat
    phrase_id
    optional semantic tag
```

Do not overengineer serialization during the first proof.

MIDI answers **what happened musically**. Audio spectrum answers **how the rendered music is energetically behaving**.

Example:

```text
MIDI chord -> grow a coral/flower cluster
Audio low band -> macro breathing
Audio mids -> branch/tension response
Audio highs -> shimmer/micro-motion
```

### XPBD experiment

Use musical structure to create geometry and spectral energy to force/deform it:

`note/chord -> ribbon/membrane/filament -> audio band forces -> XPBD motion -> bake`

Candidate outputs: prayer-strip forests, underwater membranes, coral filaments, Bell fabrics, music-grown cloth terrain.

Maturity: **EXPERIMENTAL but unusually project-specific**.

---

## Houdini 22 Walk on Surface — TEST SOON

Use vector fields/directions to trace curves over arbitrary surfaces.

Melodia candidates:
- P1 seam/tension paths;
- P2 veins/fungal succession;
- P3 filter-flow filaments;
- tide seams;
- Monolith anatomical traces;
- procedural prayer strips / growth paths.

High-value test: feed the same P3 directional field used by Niagara into a Houdini surface and derive physical filament/vein geometry from it.

This tests the core doctrine that **one field should leave evidence in multiple representations**.

---

## Houdini Curve Animate — TEST SOON

Potential bridge between procedural curves and direct art direction. Test on one tendril/ribbon/underwater filament rather than generic motion graphics.

Adopt only if it materially shortens the last 20% art-direction pass compared with procedural-only or Blender animation.

---

## Copernicus terrain — PROMOTE

Treat COP terrain as a fast GPU terrain/mask/look-development lane rather than only texture authoring.

Candidate ownership:

```text
Copernicus = fast erosion / strata / masks / terrain appearance
SOPs       = impossible topology / overhangs / anatomy / caves
UE5.8      = runtime assembly / PCG / interaction
```

Important experiment: arbitrary/SOP-authored geometry -> terrain projection/rasterization -> COP processing -> back to geometry/UE representation.

This may allow geological truth to be applied *after* impossible forms are authored.

---

## UE5.8 Mesh Terrain + PCG — CHANGE TEST QUESTION

Do not merely test whether UE can display a folded Houdini mesh.

Test whether procedural systems can **read and modify** the topology usefully:

```text
Houdini folded/overhung patch
 -> Mesh Terrain
 -> PCG reads partition
 -> PCG writes one material/weight/terrain effect
 -> boolean cavity/overhang test
 -> vegetation scatter responds to terrain channels
 -> collision/navigation/package check
```

The transformative criterion is procedural interaction, not rendering.

Status remains **R&D only**.

---

## UE5.8 Procedural Vegetation Editor — DEMOTE / PACKAGE GATE

Do not treat PVE as a SpeedTree replacement. Interesting features include growth, skeleton extraction, grafting, avoidance, carving and trimming, but current-version packaging reliability must be verified before visual-quality evaluation is worth much time.

Gate order:
1. tiny generated plant;
2. package test;
3. only if successful, evaluate bizarre secondary growth/mutation around SpeedTree ecology.

SpeedTree remains authoritative.

---

## Unreal MCP + PCG skills — PROMOTE, CONSTRAIN

The useful question is not whether an agent can spawn primitives. Test whether domain-specific PCG context can produce reliable bounded procedural operations.

Longer-term target is **agent as pipeline operator**, not autonomous editor improvisation.

Candidate deterministic workflow:

```text
P3BiomeValidation
  inspect target PCG graph
  verify expected inputs/attributes
  verify SpeedTree references
  validate density bounds
  validate P3 flow mask
  generate isolated test region
  run validation
  capture/report result
```

First-party Epic MCP remains baseline. Community MCP implementations are architectural/coverage benchmarks until reliability and source-control behavior are proven.

---

## IlluGen Accumulate — NEW MELodia-SPECIFIC TEST

Promote `Accumulate` from generic VFX feature to a **motion-memory authoring experiment**.

Potential outputs:
- Bellwake path residue;
- wetness persistence;
- pollen/filter-flow history;
- secretion trails;
- wave-energy exposure;
- persistent biological response masks.

Pipeline:

`animated motion/particles/distortion -> Accumulate -> residue/history map -> UE material/Niagara/world evidence`

This is more differentiated from Houdini/Copernicus than a generic flow-map benchmark.

---

## Cascadeur 2026.2 layers — REFINE TEST

Animation Layers are promising but should be evaluated as a cleanup/polish accelerator rather than justification for replacing the production animation stack.

Better benchmark:

```text
existing rough motion
 -> layer: weight/contact correction
 -> layer: staff/hand contact
 -> layer: silhouette exaggeration
 -> layer: secondary recovery
 -> UE round-trip
```

Measure cleanup minutes saved and residual UE work.

---

## Gaussian splats — PROCESSING LANE, NOT TRAINER ASSUMPTION

Houdini 22's splat tooling is valuable because splats can participate in procedural processing, USD and downstream reconstruction/interpretation. Do not assume Houdini is automatically the best training frontend.

Benchmark training/quality/friction against a dedicated splat tool when this lane becomes active.

Single-image splat generators are reference/ideation tools only until they prove geometric or material utility.

Interesting Melodia question: can concept/capture splats become **editable evidence** — normals, relighting, masks, spatial reference, proxy geometry — rather than final camera-dependent assets?

---

## Procedura — ARCHITECTURAL REFERENCE

The important principle is not text-to-3D itself. It is **AI generating editable procedural programs/assemblies instead of opaque mesh output**.

Use as reference when designing future Melodia agent/HDA/PCG systems:

`agent intent -> explicit procedural representation -> artist edits -> deterministic rebuild`

Status: **RESEARCH ONLY**.

---

## NVIDIA neural texture compression — WATCH / LATER BENCHMARK

Do not benchmark on toy textures. Wait until representative Melodia 4K/8K multi-channel material sets exist, then measure:
- VRAM;
- streaming/storage;
- decode cost;
- visual error;
- UE integration complexity.

Status: **WATCH**.

---

## Magpie — WATCH

Keep the architectural lesson:

`simulation truth != visual truth`

A conventional deterministic engine can own gameplay/world state while another representation/rendering layer owns appearance. This is strategically relevant but not a current shipping dependency or Unreal replacement plan.

---

# Revised trench priority

1. **Melodia Musical World Compiler proof** — Blender MIDI semantics + audio spectrum + procedural form.
2. **Houdini Walk on Surface** driven by a Melodia field.
3. **Copernicus terrain -> SOP impossible topology -> UE Mesh Terrain/PCG loop**.
4. **IlluGen motion-memory / residue maps**.
5. **Epic MCP skill-driven bounded PCG operation**.
6. **Blender XPBD music-grown cloth/filaments**.
7. **Houdini GSplat processing benchmark**.
8. Procedura architecture study.
9. RTX neural material compression when representative material sets exist.
10. Magpie watch only.

---

# The lane to hone in on: Melodia Musical World Compiler

This is the highest-love/highest-project-identity experiment because it connects an existing musical premise to visible authored world form instead of adding another disconnected content tool.

## First proof: Rhythm Garden / Tide Organism

Use a short Melodia MIDI phrase plus its rendered audio.

### Stage A — semantic ingest

Parse only:
- note;
- velocity;
- start beat/time;
- duration;
- channel/track.

Create one point/event per note. Avoid DAW features, notation, tempo editing, chord recognition and generalized interchange during v0.

### Stage B — procedural grammar

Map:
- time -> primary growth axis;
- pitch -> height/band/species family;
- velocity -> thickness/bloom;
- duration -> extension/curve length;
- channel -> organism/material family.

Chords naturally become clustered events because notes share time.

### Stage C — continuous audio response

Use `Sample Sound Frequencies` on the rendered phrase:
- low -> organism breathing / macro displacement;
- mids -> branch/tension motion;
- highs -> fine filaments/shimmer.

This makes the form semantically authored by MIDI but physically/visually animated by the actual sound.

### Stage D — optional physics

Feed ribbons/filaments/membranes into experimental XPBD only after the static/event-driven grammar works.

Do not let physics become the blocker for the first proof.

### Stage E — Houdini handoff

Export enough semantics to reconstruct/refine the form in Houdini. Test whether one field can then generate:
- Walk on Surface traces;
- ecology masks;
- Copernicus visual evidence;
- Niagara-compatible flow/reference data.

### Stage F — Unreal handoff

Bake ordinary assets/data. Unreal remains authoritative for:
- beat clock;
- gameplay state;
- convergence progression;
- player response;
- final runtime material/Niagara logic.

The offline compiler may generate **possibilities**; Unreal decides **when/why they happen**.

## Success condition

Within one focused session, one musical phrase should generate a result that:
1. visibly resembles authored Melodia worldbuilding rather than an equalizer;
2. changes meaningfully when the MIDI phrase changes;
3. reacts continuously to the rendered audio;
4. remains editable as procedural data;
5. can be baked/exported without a Blender runtime dependency.

If those five pass, promote this from niche experiment to a dedicated procedural-authoring lane.

## Failure condition

PARK if:
- it looks like generic music visualization;
- MIDI parsing dominates the session;
- musical semantics disappear after export;
- Houdini can accomplish the same work faster with clearer data ownership;
- it creates a second runtime rhythm authority.

---

# Immediate build order

```text
00 choose 8–16 bar MIDI + rendered audio
01 parse MIDI -> event points
02 GN event attributes -> simple coral/ribbon/flower grammar
03 add Sample Sound Frequencies modulation
04 make one compelling still + short motion proof
05 export event/form data
06 ingest/refine in Houdini
07 bake/import a UE proof
08 record ADOPT / PARK decision
```

Timebox the first Blender-only proof to roughly two hours. If a compelling form is not appearing by then, stop and diagnose the grammar rather than expanding infrastructure.

---

# Doctrine

> **Music should not merely synchronize Melodia's world. Music should be capable of authoring its anatomy.**

The useful pipeline is therefore not “MIDI visualizer -> Unreal.” It is:

> **musical intent -> structured events + spectral behavior -> procedural form/field/evidence -> authored native game assets -> runtime convergence.**
