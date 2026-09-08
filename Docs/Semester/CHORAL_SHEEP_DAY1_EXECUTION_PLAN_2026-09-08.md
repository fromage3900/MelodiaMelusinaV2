# Choral Sheep Capstone — Day 1 Execution Plan

**Date:** 2026-09-08  
**Status:** ACTIVE  
**Capstone:** Choral Sheep — Harmonic Ecology  
**Presentation spine:** **Creature → Motif → Harmony → World**

## Session objective

Today is not an infrastructure day.

The goal is to turn the existing, fully rigged Choral Sheep into the first visible capstone proof while Gemini develops the TouchDesigner / After Effects presentation lane in parallel.

The first successful artifact is:

> **one lovable sheep → Harmonize → pitch C becomes visible in the fleece → clean return to rest**

If that works, the capstone has moved from planning into authored proof.

---

## Current owner-confirmed asset truth

As of 2026-09-08, the project owner confirms:

- the Choral Sheep source is **fully rigged**;
- the old August note that the body had zero vertex groups is stale for the current source;
- the current source may still require an **Auto-Rig Pro (ARP) re-export** before Unreal import/reimport;
- the current Unreal skeletal-mesh/export state must still be verified before calling the asset runtime-proven;
- Groom remains optional for the first base-creature proof.

Important evidence distinction:

```text
owner-confirmed fully rigged source
    ≠
fresh FBX export verified
    ≠
UE skeletal import/reimport verified
    ≠
animation / Harmonize runtime proven
```

Do not re-rig the sheep unless a fresh export/deformation check proves the current rig is unusable.

---

## Lane A — Owner / Blender + Unreal

### A0 — Open the authoritative sheep source

First action:
1. open the current Choral Sheep .blend;
2. confirm the visible mesh, armature, material slots, and current animation/deformation state;
3. make one obvious pose/deformation test;
4. identify whether this file is currently using an ARP export workflow or the older generic deform-only export route.

**Pass:** the current source deforms correctly in Blender.

If it deforms correctly, do not revisit weight painting or rig architecture.

### A1 — Resolve export path

Because the current rig may need ARP re-exporting, choose the export path from evidence rather than assumption.

#### Preferred if current source is ARP-authored / ARP-managed
Use the current Auto-Rig Pro export workflow and produce a fresh Unreal-target FBX.

Verify:
- only required deform/export bones are shipped;
- mesh remains skinned;
- scale/orientation are correct for UE;
- material slots survive;
- no helper/control-only structures pollute the UE skeleton;
- animation compatibility is not broken by the export.

#### Fallback / comparison route
The repository already contains:
`Tools/BlenderAddons/melodia_studio/export_choral_sheep.py`

That exporter uses the older deform-only FBX route. It is useful as:
- a fallback;
- a comparison export;
- a diagnostic if ARP export produces an unexpected skeleton.

Do **not** blindly replace a working ARP export with the old generic exporter.

### A2 — UE import / reimport proof

Target remains:

`/Game/Melodia/Companions/ChoralSheep/SK_ChoralSheep`

Verify:
- mesh renders;
- skin deformation survives;
- skeleton hierarchy is sane;
- no catastrophic scale/orientation error;
- material slots are intact;
- existing companion definition can resolve the mesh;
- no missing-asset / Blueprint runtime errors are introduced.

Do not redesign maps or gameplay architecture during this step.

### A3 — M0 beauty-ready creature

Before Chladni Fleece, make one sheep visually convincing.

Priorities:
- silhouette;
- face / ears;
- bell / trim;
- clean coat values;
- readable wool volume;
- no broken deformation;
- one appealing idle / pose.

Current wool direction:
- preserve the dusty / soft coat language;
- let normal, sheen, groom, lighting, and authored fleece form create wool volume;
- do not add heavy albedo noise merely to make the surface look more complicated.

Groom is optional for M0. A clean base sheep is better than a broken hero Groom.

### A4 — M1: one sheep / one note

Build the smallest readable Harmonize proof:

```text
rest
→ Harmonize begins
→ pitch C field appears
→ amplitude controls intensity
→ beat phase adds restrained pulse
→ Harmonize ends
→ fleece returns cleanly to baseline
```

Use the existing Melodia music-reactivity / cymatics architecture.

Do not create:
- a second music clock;
- another global OSC bridge;
- another cymatics subsystem;
- a new generic visual-instrument framework.

**Pass condition:** without debug labels, a viewer can understand that the sheep sang and its wool organized into a musical pattern.

### A5 — Capture two pieces of evidence

Before expanding to E/G, capture:

1. **Creature beauty**
   - one clean hero frame / short take;
   - character first, technical explanation absent.

2. **Pitch-C proof**
   - same creature in readable Harmonize / Chladni state;
   - enough framing to compare rest vs resonant fleece.

These become real inputs for the TD/AE lane.

---

## Lane B — Gemini / TouchDesigner + After Effects

Gemini already owns:

- deterministic capstone replay schema;
- Chladni Fleece TD network spec;
- C/E/G field representation;
- transparent fleece/world/constellation passes;
- AE project organization;
- 60–90 second editorial structure;
- shot/pass manifest;
- capstone README.

Canonical handoff:

`Docs/Handoffs/GEMINI_TD_AE_CAPSTONE_HANDOFF_2026-09-08.md`

Gemini must design around the existing implementation spine:

```text
UniversalMusicalInfluence
→ existing beat/audio/cymatics presentation data
→ Choral Sheep-specific consumer/profile
→ TD visualization / deterministic replay
→ UE final authored result
→ AE assembly
```

Gemini should not block waiting for a perfect final sheep. It can use the C presentation fixture to build/replay the data path, but final claims must wait for real UE proof.

---

## Lane C — Repo / QA support

During the art session:

- keep `main` as authority;
- do not create new branches for ordinary capstone work;
- review Gemini outputs as they land;
- reject duplicate OSC / beat / cymatics infrastructure;
- keep the capstone deliverable ledger synchronized with actual evidence;
- preserve honest status language: owner-confirmed, source-present, export-verified, runtime-proven, capture-approved;
- avoid website churn while the deployed professor-facing site is green.

The website is supporting presentation infrastructure today, not the production target.

---

## Decision tree for the first hour

```text
Open sheep source
    ↓
Does current rig deform correctly?
    ├─ NO → diagnose current rig/export relationship only
    │       do not begin shader/capstone expansion
    │
    └─ YES
        ↓
Does current ARP/FBX export import cleanly to UE?
        ├─ NO → compare ARP export against repository deform-only exporter
        │
        └─ YES
            ↓
        M0 creature beauty
            ↓
        M1 one-note C Harmonize proof
```

The export problem is allowed to consume time only until the sheep is reliably in UE. It is not permission to rebuild the character pipeline.

---

## Today’s priority order

1. Verify current fully rigged source.
2. ARP re-export if needed.
3. Verify UE skeletal mesh / deformation.
4. Produce one beauty-ready sheep.
5. Produce one Harmonize / pitch-C Chladni proof.
6. Capture beauty + proof.
7. Review Gemini TD/AE outputs.
8. If energy remains: begin E/G, not the full chromatic flock.

---

## Explicitly out of scope today

- full twelve-note flock;
- new game-wide music infrastructure;
- re-rigging a source that already deforms;
- final Groom perfection before M0;
- another website redesign;
- new public Three.js architecture;
- full 60–90 second final film before the first real sheep proof;
- broad repository cleanup.

---

## End-of-day success levels

### Minimum win
- current rig/export truth verified;
- one clean sheep in UE.

### Good day
- M0 creature beauty;
- M1 pitch-C Harmonize proof;
- two useful captures.

### Excellent day
- all above;
- Gemini replay/TD/AE documents land;
- first C/E/G staging begins.

Do not judge the day by number of systems touched.

Judge it by whether **the sheep became real on screen**.
