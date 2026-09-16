# CLO → Blender → GLB → Three.js Commercial Pipeline

**Status:** PRODUCTION CHECKLIST / EXECUTION EVIDENCE REQUIRED  
**Date:** 2026-09-10

This pipeline exists to turn one original garment into reusable proof for fabric consulting, realtime-material work, and browser configurator jobs.

It is intentionally small and evidence-driven. One clean garment is enough.

## 0. Scope

Target asset for the first proof:

- one original simple knit sweater / top;
- neutral commercial silhouette;
- front chest region suitable for a patch/decal;
- no Melodia character/IP dependency;
- no client branding;
- no copyrighted garment replication.

The goal is not fashion collection production. The goal is a reproducible web-ready garment pipeline.

---

# 1. CLO authoring

## Garment construction

Keep the pattern/silhouette simple enough that downstream optimization remains predictable.

Record:

- CLO project/source file;
- garment dimensions / scale convention;
- fabric/preset used as simulation reference;
- particle distance used for the saved proof state;
- any thickness / subdivision settings that materially affect export;
- front/back/sleeve/collar pattern organization;
- final simulated pose used for web proof.

## Before export

Verify:

- no accidental intersections that dominate the browser silhouette;
- front chest area is sufficiently clean for decal testing;
- UV layout exists and is usable;
- garment scale is known;
- hidden/internal geometry is not being exported unnecessarily;
- design symmetry/asymmetry is intentional.

## Export evidence

Capture one clean CLO screenshot showing:

- whole garment;
- pattern/garment relationship where useful;
- enough UI context to establish genuine CLO usage without exposing unrelated personal/project content.

Do not claim the CLO asset is optimized for realtime until downstream cleanup is complete.

---

# 2. Blender cleanup / web preparation

Import the CLO export into Blender and preserve a clean editable source before destructive optimization.

Suggested source stages:

```text
sweater_CLO_source.*
sweater_blender_cleanup.blend
sweater_web_final.blend
sweater_web.glb
```

## Geometry checks

Record before/after:

- vertex count;
- triangle count;
- object count;
- material slots;
- UV sets;
- loose / duplicate geometry;
- normals/tangents;
- scale/transforms;
- bounding dimensions.

Clean only what produces measurable web value.

Potential operations:

- remove hidden/internal geometry if safe;
- merge unnecessary objects/material slots;
- fix normals;
- apply/normalize transforms where export requires it;
- retopologize or decimate only when silhouette/deformation requirements permit;
- preserve a higher-quality source separately;
- simplify excessively dense CLO geometry;
- ensure UVs remain valid after optimization.

## Suggested first-proof budget

Treat these as working targets, not universal rules:

- hero garment: aim for a visually justified web triangle count rather than arbitrary extreme reduction;
- material slots: preferably 1–3;
- base texture target: 2K maximum for first hero proof unless close-up evidence requires more;
- mobile proof should be tested at realistic DPR and viewport width;
- use compression only after verifying the quality tradeoff.

Record actual numbers instead of claiming the target was reached.

---

# 3. Material / texture preparation

For the commercial clean-room proof, use only owner-authored or clearly commercial-reuse-safe texture resources.

Minimum useful state set:

1. knit-like;
2. smoother/satin-like comparison if appropriate;
3. coarse/woven or alternate stitch-scale response.

The configurator proof may use one garment and three independently authored material/stitch states rather than three garments.

## Minimum texture documentation

For each state, record:

- base-color source and color space;
- normal source / orientation;
- roughness source;
- AO only if it materially improves the result;
- any packed-channel convention;
- dimensions;
- file format;
- whether tiling is used;
- provenance/license.

## Physical versus artistic data

Clearly separate:

**Observed / measured:**
- pattern dimensions;
- garment geometry;
- photographed/reference weave scale if controlled;
- actual texture dimensions;
- actual browser diagnostics.

**Artist-authored / approximated:**
- roughness tuning;
- normal strength;
- sheen-like response;
- stylized color adjustments;
- procedural weave generation when not scan-derived.

Do not describe an artistic material as a measured physical fabric model.

---

# 4. GLB export

## Naming convention

Use predictable generic names, for example:

```text
GARMENT_Sweater
MAT_Knit_Base
LOC_ChestPatch
```

If separate submeshes are actually needed, name them by functional region rather than DCC-generated defaults.

## Export checklist

- correct scene scale;
- intended normals/tangents present;
- only required objects exported;
- textures resolved;
- no accidental cameras/lights unless intentionally part of the deliverable;
- materials render acceptably after GLB round-trip;
- hierarchy documented;
- file byte size recorded;
- export settings captured in Markdown or screenshot.

Do not claim Draco, Meshopt, KTX2/Basis or another compression path unless it was actually executed and browser-tested.

---

# 5. Three.js validation

The proof should validate the final GLB independently of the DCC viewport.

Minimum browser test:

- GLB loads without uncaught errors;
- orbit/zoom works;
- garment remains readable under neutral light;
- close-up camera reveals textile response;
- grazing-angle view makes roughness/normal differences visible;
- material/stitch state can switch without renderer rebuild;
- base color can change;
- chest patch/decal state can change if implemented;
- current configuration can be represented as JSON;
- reset restores defaults;
- mobile-width layout remains usable;
- diagnostics capture approximate FPS, DPR, draw calls and triangles.

Example state contract:

```json
{
  "surface": "knit_fine",
  "color": "neutral_cream",
  "decal": "patch_none"
}
```

This is a local presentation/configuration state, not an ecommerce order contract.

---

# 6. Evidence package

The first complete proof should contain:

```text
01_CLO_whole_garment.png
02_Blender_cleanup.png
03_GLTF_GLBBudget.md
04_ThreeJS_whole_garment.png
05_ThreeJS_grazing_closeup.png
06_material_comparison.png
07_mobile_width.png
08_config_state.json
09_runtime_diagnostics.md
10_provenance_manifest.md
```

File names may differ; the evidence categories should not.

## Proposal-safe claims after evidence exists

Potential claims:

- CLO garment authoring / preparation experience;
- garment cleanup and optimization in Blender;
- GLB delivery for realtime web presentation;
- Three.js PBR material validation;
- material/stitch/color variant state handling;
- browser diagnostics / mobile QA;
- clear distinction between physical input data and artist-authored material approximation.

Each claim must point to an actual artifact.

---

# 7. Reusable automation opportunities

Only automate steps that are deterministic and inspectable.

Good candidates:

- Blender scene validation script;
- triangle/material/object budget report;
- transform/naming audit;
- batch GLB export preset;
- texture-dimension/provenance manifest generator;
- browser asset-stat readout;
- JSON configurator-state schema.

Keep subjective garment fit, silhouette, textile lookdev and final artistic judgment human-reviewed.

---

# Next single action

Create/select the original CLO sweater source, capture its baseline evidence, and export it to Blender. Do not begin a second garment until the first one reaches browser validation.
