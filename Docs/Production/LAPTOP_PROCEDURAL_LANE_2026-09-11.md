# ASUS Laptop Procedural Lane — Blender 5.2 / Geometry Nodes / ArmorPaint

**Date:** 2026-09-11  
**Status:** ACTIVE WORKSTATION LANE CONTRACT  
**Workstation branch:** `collab/laptop/longterm`  
**Canonical runtime authority:** `main`  
**Related research:** `Docs/Research/UE58_PROCEDURAL_WORLDBUILDING_TEST_NOW_2026-09-11.md`  
**Related policy:** `Docs/Production/BRANCH_WORKSTATION_POLICY.md`

This document defines what the ASUS Nitro laptop is for during current capstone production. It is intentionally narrow: Blender / Geometry Nodes / lightweight procedural authoring / experimental texture tooling. It must not become a second game/runtime authority.

> Laptop work is a production source lane. `main` remains the canonical UE/runtime/capstone truth. Promote useful DCC work deliberately; do not wholesale-merge laptop branch history over `main`.

---

## 1. Current role of the laptop

Use the laptop for:

- Blender 5.2 LTS Geometry Nodes authoring;
- procedural asset and ecology prototypes;
- Blender Python automation for GN builders;
- audio-reactive geometry experiments;
- lightweight asset/texture experimentation;
- ArmorPaint build/evaluation work;
- on-the-go DCC iteration while the primary PC/lab lane handles Unreal, heavy baking, builds, and runtime validation.

Do **not** move core UE gameplay, save, combat, quest, or runtime-authority work into this lane.

---

## 2. Blender baseline — target Blender 5.2 LTS

Use **Blender 5.2 LTS** as the preferred procedural-authoring baseline for new laptop GN work unless an existing production `.blend` requires an older version.

Why this version matters to Melodia:

- native sound-frequency sampling is available inside Geometry Nodes;
- Geometry Bundles make reusable procedural context easier to pass through GN systems;
- Python control of Geometry Nodes modifier inputs is cleaner through current RNA properties;
- LTS stability is preferable to daily-build churn during capstone production.

Before upgrading an established `.blend`, preserve a known-good copy and verify custom scripts/add-ons.

---

## 3. P0 laptop experiment — `GN_Melodia_AudioResonance`

### Goal

Prove that a Melodia music source can drive an art-directed procedural geometry system directly in Blender without creating a second gameplay/audio authority.

Conceptual chain:

```text
Melodia audio / stem
  -> Sample Sound Frequencies
  -> 3 authored frequency bands
  -> GN fields
  -> geometry / instances / motion
  -> baked or exported DCC result
```

### First version

Create one reusable Geometry Nodes modifier/group with three deliberately readable responses, for example:

- low band -> large-form displacement / breathing;
- mid band -> scatter density / growth;
- high band -> instance scale / sparkle / micro-motion.

The visual language should remain Melodia/cymatics-adjacent rather than generic music-visualizer equalizer art.

### Required proof

Keep the proof small:

1. one `.blend` source;
2. one short capture showing three bands producing distinct readable behavior;
3. one screenshot of the GN graph;
4. note audio source / band ranges / useful exposed controls;
5. one exported static or baked result if promotion to UE is useful.

**Pass:** the system produces art-directable geometry fast enough to reuse.  
**Park:** it is visually interesting but adds no production advantage over Houdini / UE PCG / authored animation.  
**Reject:** it becomes fragile, opaque, or generic audio-reactive decoration.

---

## 4. P1 — reusable `MelodiaEcologyBundle`

Use Blender 5.2 Geometry Bundles to prototype a compact reusable procedural context for ecology/worldbuilding tools.

Candidate context:

```text
Resonance
Density
Scale
Seed
AssetFamily
CymaticStrength
MaterialVariant
```

The bundle is **Blender authoring state only**. Before export/promotion, convert every downstream-relevant value into explicit geometry, attributes, named data, textures, or documented export metadata.

Do not assume Blender Bundle semantics survive into Unreal.

Desired outcome:

```text
GN authoring context
  -> explicit exportable attributes
  -> UE 5.8 PCG / material consumers
```

This should complement the `Resonance Ecology v0` proof documented in `Docs/Research/UE58_PROCEDURAL_WORLDBUILDING_TEST_NOW_2026-09-11.md`.

---

## 5. P1 — Blender Python automation

Use Blender 5.2 Python for **authoring automation**, especially:

- set exposed GN modifier inputs;
- set seeds / resonance / asset family parameters;
- generate variants;
- run validation checks;
- batch naming / export preparation;
- capture small evidence sets.

Preferred model:

```text
Python
  -> configure GN modifier
  -> generate one controlled variant
  -> validate
  -> export / capture
```

Avoid building a giant automation framework before one actual Melodia asset benefits from it.

Python in this lane does not own gameplay truth. Export explicit results/contracts to Unreal.

---

## 6. ArmorPaint — active local evaluation

**Current user-reported status (2026-09-11): ArmorPaint is being compiled locally.**

Treat ArmorPaint as an evaluation, **not** as a replacement for Substance Painter/Sampler yet.

### Smallest useful benchmark

Use one real Melodia asset and compare the full loop:

```text
open/import
-> bake
-> paint
-> masks/layers
-> export PBR maps
-> import into UE 5.8
-> inspect material result
```

Evaluate:

- stability on the laptop;
- bake quality;
- layer/mask ergonomics;
- speed for quick asset lookdev;
- export consistency;
- packed-map flexibility;
- UE round-trip friction;
- whether it offers any meaningful advantage over the existing Substance workflow.

End with exactly one decision:

- **ADOPT AUXILIARY** — genuinely useful for quick/lightweight laptop painting;
- **PARK** — works but does not beat current Substance workflow;
- **REJECT** — instability or workflow friction makes it not worth maintaining.

Do not migrate existing Substance assets solely because ArmorPaint is open-source/lightweight.

---

## 7. Other tools — bounded watch/test list

### Gaea 2.3 — USE WHERE IT ALREADY HELPS

Macros / region workflows may be useful for reusable Melodia terrain recipes, but this is not required laptop work unless a concrete terrain task benefits.

Candidate reusable recipes:

- `Melodia_FloatingIsland`
- `Melodia_SeaAbove_Cliff`
- `Melodia_MonolithErosion`
- `Melodia_ResonanceValley`

Export useful masks/height data to the normal UE/Houdini/PCG pipeline.

### World Creator 2026 — WATCH / EVALUATE, DO NOT MIGRATE

Potential future value: fast terrain composition with Blender/UE bridge workflows.

Do not buy or migrate the terrain pipeline based on integration claims alone. Evaluate a Community Edition or equivalent low-risk test when practical and compare against Gaea + Houdini on one real Melodia task.

### Geo-Scatter — OPTIONAL

May be useful for fast Blender portfolio/layout/scatter composition. It does **not** replace UE PCG as the canonical runtime/world-population lane.

If tested, keep it to one scene and export only the result needed downstream.

---

## 8. Promotion contract — laptop -> Unreal

```text
visual / procedural idea
  -> `collab/laptop/longterm`
  -> Blender / GN / texture source
  -> validate locally
  -> identify exact promotable artifact
  -> scoped promotion branch / PR
  -> UE import
  -> PCG / material / runtime validation
  -> evidence
  -> `main`
```

Promotable artifacts may include:

- `.blend` source intentionally selected for shared provenance;
- FBX / glTF / Alembic / textures where appropriate;
- explicit point/mesh attributes;
- masks / heightfields / cymatic textures;
- Python utilities with a proven production use;
- screenshots/captures needed to show evidence.

Never promote unrelated laptop branch history just to move one useful DCC artifact.

---

## 9. Authority boundaries

The laptop lane must not create replacements for established authorities:

- UE gameplay/runtime truth remains on `main`;
- UE PCG remains the final Unreal procedural assembly/environment population lane;
- Houdini remains the stronger topology/spatial/variant procedural lane where appropriate;
- Nikki Cymatics remains the approved Sheep material path;
- Substance remains the core texture-authoring stack until an explicit benchmark changes that decision;
- TouchDesigner remains a visual/performance instrument, not gameplay truth;
- Blender audio sampling is a procedural authoring input, not a new beat clock or rhythm grader.

---

## 10. Immediate execution order

Do not open five simultaneous tool experiments.

1. **Finish/preserve the GN work already in progress.**
2. Build the smallest `GN_Melodia_AudioResonance` proof.
3. Package useful recurring GN values into a small `MelodiaEcologyBundle` only if the first proof benefits.
4. Finish compiling ArmorPaint and run **one** real-asset benchmark.
5. Promote only proven useful artifacts/attributes into the UE `Resonance Ecology v0` experiment.
6. Leave World Creator / Geo-Scatter / broader terrain-tool evaluation parked unless a current task specifically needs them.

The goal of this lane is **more finished Melodia art per hour**, not accumulating procedural software.
