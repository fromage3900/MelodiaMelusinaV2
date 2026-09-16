# Figma Minimal Polish Brief — Afternoon Submission Pack

**Date:** 2026-09-10  
**Purpose:** use available Figma capacity for a very small visual-polish layer over three already-active WebGL proof lanes.  
**Rule:** Figma is for presentation/packaging, not inventing new product scope.

## Shared visual system

Build **one reusable evidence-card / case-study frame** and create three variants from it.

### Visual language

- clean technical editorial layout;
- restrained off-white / charcoal foundation;
- one subtle lane accent only where it clarifies hierarchy;
- no Melodia branding, fantasy ornament, or decorative UI that distracts from proof;
- prioritize screenshots, measured values, and pipeline diagrams over marketing copy;
- 8px spacing grid;
- modest corner radius;
- thin neutral dividers;
- strong typographic hierarchy;
- screenshots stay uncropped where evidence matters;
- all performance numbers must come from runtime measurement, never placeholders in final exports.

### Core components

Create one component set with:

1. **Case-study cover**
   - title;
   - one-sentence capability claim;
   - hero screenshot / render;
   - compact status badge (`RUNTIME VERIFIED`, `CAPTURED`, etc.);
   - no fake client logo.

2. **Evidence card**
   - screenshot;
   - measured value block;
   - short `What this proves` text;
   - optional source/DCC path label.

3. **Pipeline strip**
   - 4–6 simple steps;
   - compact arrows;
   - tool labels only where they matter.

4. **Requirements matrix**
   - buyer requirement;
   - proof artifact;
   - status.

5. **Footer / contact strip**
   - portfolio URL;
   - GitHub/demo link if appropriate;
   - concise role descriptor: `Realtime 3D / Technical Art / WebGL`.

## Required frames

Create only these:

- **1600×900 cover** — one per lane (3 total).
- **1440px desktop evidence sheet** — one reusable component with 3 variants.
- **390px mobile evidence sheet** — verify hierarchy and screenshot readability.

Do not create a full brand system, pitch deck, website redesign, social campaign, logo exploration, or speculative mock client UI.

---

# Lane A — Product Motion / Web-ready GLB

**Tone:** clinical premium product visualization.

Use:
- neutral light/dark studio background;
- crisp hierarchy;
- subtle cool accent;
- product silhouette as dominant image;
- callout anchors and diagnostics as evidence, not decoration.

Cover copy direction:

**Web-ready product animation / Three.js proof**  
Deterministic scrub-safe motion, named hierarchy, anchored callouts, realtime diagnostics, and GLB-oriented asset preparation.

Evidence cards should prioritize:
- final product render / viewport;
- hierarchy / locator proof;
- timeline scrub proof;
- triangle / material / texture / byte stats;
- desktop + mobile runtime.

---

# Lane B — CLO → Blender → GLB → Three.js Fabric Pipeline

**Tone:** textile material study / technical-fashion lab.

Use:
- warm neutral / ecru foundation;
- material close-ups;
- subtle muted textile accent;
- avoid fashion-magazine styling that hides technical evidence.

Cover copy direction:

**Realtime garment & fabric material pipeline**  
CLO garment workflow, Blender realtime preparation, PBR texture/material organization, Three.js inspection, and web validation.

Evidence cards should prioritize:
- CLO source screenshot;
- Blender cleanup / topology view;
- GLB / Three.js garment view;
- grazing-light material close-up;
- material preset / channel inspection;
- known-approximation note where relevant.

---

# Lane C — Procedural Industrial System Loop

**Tone:** monochrome technical / machined / systems visualization.

Use:
- light-grey monochrome base;
- charcoal typography;
- color only for STRUCTURAL / FLOW / THERMAL evidence;
- fixed-camera full assembly image;
- avoid cinematic gradients, bloom, or decorative sci-fi UI.

Cover copy direction:

**Procedural mechanical motion system**  
Absolute-time deterministic choreography, constant-speed hard-stop motion, seeded assemblies, and solver-inspired visualization states.

Evidence cards should prioritize:
- BASE monochrome capture;
- motion-law timeline;
- LOOP Δ = 0 proof;
- three visualization modes;
- seeded variation;
- runtime diagnostics.

---

# Export package

For each lane export:

```text
cover-1600x900.png
proof-desktop.png
proof-mobile.png
requirements-matrix.png   # only if useful
```

Keep editable Figma source organized as:

```text
00_SHARED_COMPONENTS
01_PRODUCT_MOTION
02_FABRIC_CLO
03_INDUSTRIAL_LOOP
99_EXPORTS
```

## Token-spend priority

If Figma/AI credits are limited, spend them in this order:

1. establish shared evidence-card component;
2. polish Lane A cover + evidence sheet;
3. polish Lane C cover + evidence sheet;
4. polish Lane B cover + evidence sheet;
5. stop.

Do not burn credits generating decorative variants once the hierarchy is clean.

## Final rule

Figma polish may improve composition, spacing, hierarchy, cropping, annotation styling, and presentation consistency. It must **never** invent performance values, runtime states, client results, or capabilities that are not already evidenced elsewhere in the repo.
