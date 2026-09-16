# Custom Asset Strike Pack — 2026-09-10

**Goal:** create a tiny set of original 3D assets that directly increase proposal credibility for today's strongest WebGL listings.

These are not portfolio vanity assets. Each asset must prove a buyer-requested pipeline and leave behind a reusable source/export recipe.

## Asset 1 — Modular Handheld Product

**Targets:** $3,000 web-ready product-animation listing; generic product-viewer/configurator work.

Create one original neutral handheld device with:
- hard-surface primary shell;
- one hinged/sliding/rotating subassembly;
- 3 named anchor/locator points for callouts;
- 2–4 compact PBR material slots;
- clean object hierarchy and naming;
- web-target triangle budget approximately 30k–80k after final optimization, with lower LOD if useful;
- 2K-or-lower texture target for web proof;
- editable Blender source;
- GLB export target;
- named deterministic animation clips or a hierarchy suitable for browser-side scrub animation.

Do not copy the client's medical/diagnostic products. Design it as a fictional compact creative/measurement device: scanner, field recorder, light meter, compact synth controller, environmental sensor, etc.

### Fast owner/Kimi split

Kimi can generate Blender Python scaffolding for blockout, naming, locators, hierarchy, animation actions, and export checks. Brennan owns the final silhouette/material/art-direction pass.

**Finish evidence:** Blender source + exported GLB + screenshot + triangle/material/texture stats + successful load in Product Motion Lab.

---

## Asset 2 — CLO Knit Garment Hero

**Targets:** Three.js fabric technical-art consultancy; $2,000–$5,000 knitwear configurator.

Create one original simple knit top/sweater in CLO 3D. Keep the design generic and commercial-proof oriented rather than character-specific.

Required:
- clean simple silhouette readable on web;
- front chest area suitable for decal/embroidery placement;
- sensible UV layout;
- garment topology/export suitable for downstream cleanup/retopo if needed;
- at least 3 original stitch/material states after web conversion;
- base color variation support;
- one generic original patch/decal placement region;
- CLO source retained;
- clean Blender/web-prep version retained;
- GLB export retained.

Pipeline proof:

```text
CLO garment
→ export geometry / UVs
→ Blender cleanup + web optimization
→ texture/material preparation
→ GLB
→ Three.js material/configurator validation
```

The evidence is more important than complexity. One clean garment that proves the whole pipeline beats a fashion collection.

**Finish evidence:** CLO screenshot/source, Blender cleanup screenshot, GLB, Three.js screenshot, triangle count, texture set description, and exported configurator JSON state.

---

## Asset 3 — Procedural Mechanical Module

**Targets:** $10,000 industrial homepage loop; procedural WebGL environment/hero work.

Create one original mechanical/architectural module that can be procedurally repeated and animated. Examples: heat exchanger module, modular pump housing, energy manifold, abstract filtration tower, robotic gantry cell, architectural ventilation unit.

Required:
- completely original/non-client-specific design;
- modular subcomponents;
- deterministic seedable arrangement;
- one-axis mechanical motions with hard stops;
- clear hierarchy;
- neutral base materials;
- optional state visualization masks/attributes for STRUCTURAL / FLOW / THERMAL illustration modes;
- web-friendly instancing/repetition path;
- stable hero composition from at least 3 seeds.

Kimi should prefer procedural Three.js/Blender-Python/Houdini-generated geometry over a time-consuming manual hero model. Brennan can art-direct silhouette, scale and surface language.

**Finish evidence:** 3 seeded variations + one 10–16 second deterministic loop + diagnostics + source generator or generation recipe.

---

# Priority today

1. **Handheld Product** — directly improves the strongest $3,000 listing and Product Motion Lab.
2. **CLO Knit Garment** — directly strengthens two strong listings and proves a genuine CLO→web pipeline.
3. **Mechanical Module** — only after 1 and 2 have runtime evidence.

Do not build all three to AAA final-art quality before applying. The first pass should be clean enough to prove topology, hierarchy, materials, animation and web delivery. Buyer proof comes first; extra lookdev comes after the underlying pipeline works.

# Reuse rule

Every custom asset must leave behind at least one reusable generic artifact:
- Blender generation/validation script;
- CLO export checklist;
- GLB optimization preset;
- texture-budget checklist;
- naming/hierarchy convention;
- browser loader/configurator primitive;
- deterministic animation helper.

That reusable artifact belongs to `tools/fromage-webgl-kit/` and should be independent of Melodia IP.