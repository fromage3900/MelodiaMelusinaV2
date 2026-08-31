# Next Highest-Value R&D Tests — 2026-08-30

**Project:** Melodia Melusina / UE5.8  
**Context:** Dash is already in active use, so it is no longer treated as a generic adoption candidate.  
**Goal:** prioritize tests that either create a visibly unique Melodia interaction or prove a durable architecture boundary.

---

## Priority order

### 1. Cymatic Ecology -> ecological memory

**Why first:** highest visible uniqueness per hour and already aligned with existing rhythm, Niagara, PCG, PCG Biome Core, and PCG-Niagara infrastructure.

Build the current Cymatic Ecology MVP, then make its standing-wave field alter the local environment for a short persistence window.

Target reactions:
- pearl/pollen accumulation on nodal lines;
- coral/grass orientation toward harmonic bands;
- local density bias from coherence;
- a short-lived spatial afterimage after a phrase ends;
- Misses introduce visible destructive interference rather than generic VFX noise.

**Win condition:** a player can infer rhythm quality from environmental organization without reading UI.

**Hard rule:** presentation/environment response does not become rhythm authority.

---

### 2. Dash -> procedural regeneration survivability

Dash is already useful. The unanswered question is whether it fits the super-pipeline safely.

**Map:** `LV_RND_P3_DashRegeneration`

Procedure:
1. create a deterministic PCG/Houdini/SpeedTree baseline;
2. perform a deliberate Dash hero pass;
3. record what Dash leaves behind: native Actors, plugin-owned state, transforms, materials, metadata;
4. regenerate the underlying procedural layer;
5. compare scene state and Git diff;
6. recreate the same hero exceptions with UE5.8 PCG Manual Editing where practical.

Measure:
- hero edits preserved/lost;
- duplicate actors;
- source-control churn;
- regeneration safety;
- migration behavior with Dash unavailable;
- time versus PCG Manual Editing + native placement.

**Desired role:**

```text
Houdini / PCG = repeatable systemic layout
Dash          = fast final human composition pass
Manual Editing = durable procedural exceptions where needed
```

**Win condition:** Dash accelerates hero composition without becoming the only place those decisions can exist.

---

### 3. Houdini-PCG semantic round-trip — Tier 0 compiler proof

This remains the highest architectural-value test.

**Map:** `LV_RND_HPCG_ScalarRoundTrip`

Prove:
- stable point IDs;
- `melodia_moisture`;
- `melodia_monolith_proximity_m`;
- `melodia_ecological_density`;
- one explicit world-space direction field;
- clean second cook and editor reopen;
- predictable cache/bake/source-control behavior.

Then progress immediately to:

```text
PCG Editor Mode spline
 -> Houdini HDA
 -> melodia_filter_flow_*
 -> PCG/Biome Core
 -> SpeedTree ecology
 -> Niagara/material response
```

**Win condition:** one authored gesture propagates through the compiler without semantic drift.

---

### 4. DLSS 4.5 / DLAA temporal torture test on Cymatic Ecology

Cymatic Ecology deliberately creates difficult reconstruction content:
- subpixel standing-wave lines;
- translucent water;
- iridescent pearl materials;
- Niagara particles;
- emissive harmonic geometry;
- fast phase changes on rhythm events.

Fixed sequence:
- 8 deterministic beats;
- fixed camera path;
- identical effect seed.

Compare:
- TSR;
- DLAA;
- DLSS Quality;
- DLSS Balanced only if Quality is stable.

Record:
- GPU ms;
- internal/output resolution;
- line breakup;
- ghosting;
- water shimmer;
- toon-edge stability;
- particle persistence artifacts.

**Win condition:** visual stability improves enough to justify the integration without masking rhythm timing or thin-line detail.

---

### 5. RTX Neural Texture Compression — one real Copernicus family

Do not benchmark vendor samples.

Use one real 4K Melodia family, preferably:
- P2 molt state family; or
- pearl/iridescent Sea Above family.

Compare:
- project BCn baseline;
- source/uncompressed reference;
- NTC experiment.

Record:
- disk footprint;
- resident memory where measurable;
- encode/setup cost;
- reconstruction artifacts in roughness/normal/masks;
- stability under toon/Substrate lighting;
- exact SDK/build provenance.

**Decision:** keep runtime integration WATCH unless a reproducible UE5.8 path is proven.

---

### 6. Magpie architecture proxy — white-box visual-truth renderer

Magpie is now backed by a real Aug 2026 paper and deserves a deeper architecture experiment, but not a shipping runtime integration.

The useful test is to build the **boundary**, not reproduce a 5B H100 renderer.

Create a deterministic Unreal capture lane that emits:
- white-box RGB;
- camera pose;
- frame/time ID;
- optional depth;
- optional normals;
- optional semantic/object ID;
- full-fidelity reference render.

Then evaluate an external/offline generative renderer against that paired capture.

This becomes `Magpie-Lite`: an interchangeable render-server interface for lookdev/previs/Monolith perception research.

See:
`Docs/Research/MAGPIE_REALTIME_WORLD_RENDERER_DEEP_DIVE_2026-08-30.md`

---

### 7. NvRTX 5.8 Preview / Mega Geometry — isolated renderer branch

Only after stock UE/DLSS evidence exists.

Use a dense Melodia-specific scene:
- cathedral ornament;
- coral;
- Nanite terrain detail;
- optional selected foliage;
- wet/reflective surfaces.

Compare stock HWRT/path-traced reference versus NvRTX features.

Record separately:
- **shipping value**;
- **portfolio/reference-renderer value**.

Do not let a source-engine compile block the game-visible experiments above.

---

### 8. External VFX authoring shootout

Run one identical brief through:
- H22 Copernicus;
- IlluGen;
- LiquiGen or EmberGen where the medium applies;
- native Niagara/material graph baseline.

Candidate brief:
`Sea Above / P3 harmonic caustic-flow response`.

Judge:
- artist minutes;
- graph reproducibility;
- export friction;
- native UE output;
- visual quality;
- runtime dependency.

Do not adopt multiple tools for the same job unless their roles remain genuinely distinct.

---

## Tonight / next-session split

### Tonight

```text
1. Cymatic static field
2. Rhythm -> field bridge
3. Ecological memory / pearl dust
4. Dash regeneration canary if the baseline map is ready
5. TSR vs DLAA / DLSS Quality
```

### Next session

```text
1. Houdini-PCG semantic Tier 0
2. Magpie-Lite white-box capture interface
3. NTC material-memory canary
4. NvRTX 5.8 Preview isolated branch
```

---

## Promotion rule

A test only becomes workflow infrastructure if it produces at least one of:

1. a visibly unique Melodia result unavailable from the current pipeline in comparable time;
2. a measurable artist-hour reduction while leaving understandable native outputs;
3. a durable data/automation boundary that simplifies multiple later systems.

Novelty without one of those outcomes remains R&D.