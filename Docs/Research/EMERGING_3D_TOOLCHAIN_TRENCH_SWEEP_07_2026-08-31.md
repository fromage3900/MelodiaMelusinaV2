# Emerging 3D Toolchain — Trench Sweep VII

**Date:** 2026-08-31  
**Project:** Melodia Melusina / UE5.8  
**Status:** external-accelerator evidence pass  
**Focus:** IlluGen, LiquiGen, EmberGen, Cascadeur 2026.1, Toolbag 5.03, Dash, Gaea2Unreal, World Creator bridges.

---

# 0. Why this pass exists

After Trench Sweep VI, the biggest architectural work moved to the Houdini ↔ PCG compiler contract. This pass returns to the external tools and asks a stricter question:

> What exact integration assumptions could make a promising tool fail after the first impressive demo?

The goal is to capture one-way links, version restrictions, unit conventions, reset behavior, incomplete documentation, and source-control hazards before those become pipeline folklore.

---

# 1. IlluGen — still high-value, but documentation maturity is itself an adoption risk

JangaFX's official product documentation describes IlluGen as a real-time VFX/tech-art asset generator for:

- tiling noise;
- normal maps;
- flowmaps;
- 3D FX meshes;
- caustics;
- masks;
- distortions;
- animation timelines;
- flipbook packing/unpacking.

Source:

- https://docs.jangafx.com/

However, the dedicated IlluGen documentation currently explicitly says the documentation is still a work in progress.

Source:

- https://docs.jangafx.com/illugen/index.html

## Melodia implication

IlluGen remains a good candidate for the Sea Above/P3 texture-motion benchmark, but **documentation maturity becomes part of the score**.

### New required evidence

For every IlluGen test commit:

- exact application build;
- exact source graph/project file;
- screenshot of export settings;
- output resolution/bit depth/format;
- channel packing;
- color-space assumptions;
- animation frame count/FPS;
- UE import settings;
- whether the graph can be recreated from committed/local source without relying on undocumented UI state.

### Decision gate

If IlluGen is 20–30% faster visually but too opaque to reproduce, it may remain a **specialist artist accelerator** instead of a canonical pipeline stage.

The percentage is a project threshold, not a vendor claim.

---

# 2. IlluGen benchmark is now a fair fight against H22 Copernicus

The benchmark must compare identical deliverables:

```text
Sea Above / P3 Animated Surface Pack
  flow
  distortion
  caustic/interference
  breakup/noise
  packed utility mask
  optional flipbook
```

## Run A — H22 Copernicus

Use geometry-aware/adjoining field inputs where useful.

## Run B — IlluGen

Use IlluGen's procedural/animated VFX workflow.

## Measure

- first useful result time;
- second-art-direction change time;
- export time;
- UE import/setup time;
- graph/source clarity;
- visual quality at fixed cameras;
- ability to reuse the source for a second scene.

The winner can differ by task family. Melodia does not need one universal texture tool.

---

# 3. LiquiGen — export convention is a first-class contract, not an afterthought

JangaFX documents LiquiGen as a real-time liquid simulator that can produce flipbooks, image sequences, and Alembic caches.

Sources:

- https://docs.jangafx.com/
- https://docs.jangafx.com/liquigen/index.html

LiquiGen's Alembic/OBJ export has explicit target conventions for:

- position units;
- velocity binding;
- velocity units;
- vector vs color interpretation;
- custom velocity attribute naming.

Source:

- https://docs.jangafx.com/liquigen/pages/references/How-To%20Guides/alembic_convention.html

## Important example

The documented Houdini convention uses:

- positions in meters;
- velocity as arbitrary data;
- Houdini-style `v` attribute;
- velocity in m/s.

## Melodia implication

Never say "export Alembic" without also recording:

```text
position unit
velocity unit
velocity binding
velocity attribute name
consumer convention
```

This is the liquid equivalent of the Houdini-PCG vector-space trap.

---

# 4. LiquiGen inputs have simulation-specific fragility

LiquiGen documents FBX/OBJ/Alembic input for emitters/colliders and notes:

- Alembic input uses OGAWA format;
- imported simulation geometry should be closed;
- geometry thinner than the voxel size may not process properly;
- loading imported meshes from a network drive can cause simulation/render instability.

Source:

- https://docs.jangafx.com/liquigen/pages/references/How-To%20Guides/import_animation.html

## Melodia rule

For LiquiGen tests:

- use a local working cache for source simulation inputs;
- record the canonical source path separately;
- record voxel size versus thinnest collider feature;
- make collider proxy geometry explicit;
- do not diagnose a failed thin cloth/branch collider as "LiquiGen is bad" before checking voxel scale.

### Benchmark update

Sea Above/P3 liquid tests should include two collider variants:

1. production-like thin/high-detail source;
2. simulation proxy designed for voxel scale.

If only the proxy works, record that as expected pipeline cost.

---

# 5. LiquiGen output families suggest two distinct Melodia roles

## Role A — baked real-time presentation

Use:
- flipbook;
- image sequence;
- normal/depth/thickness/render passes.

Best for:
- impossible droplets;
- hero splashes;
- surface events;
- stylized liquid presentation where full geometry is unnecessary.

## Role B — geometry/simulation source

Use:
- Alembic mesh/particle output;
- Houdini as optional cleanup/derivation stage.

Best for:
- hero liquid mesh reference;
- generating flow/velocity data;
- one-off cinematic/hero geometry that may later be simplified.

Do not make LiquiGen a runtime water authority.

---

# 6. EmberGen — keep frame-rate synchronization in the reproducibility record

JangaFX documents EmberGen export of:

- flipbooks;
- image sequences;
- VDB volumes.

Sources:

- https://docs.jangafx.com/
- https://docs.jangafx.com/embergen/pages/getting_started.html
- https://docs.jangafx.com/embergen/pages/FAQ.html

The documentation warns that imported animation, simulation timestep, playback FPS, and backplate frame rate need to be synchronized to align correctly.

## Melodia implication

Every EmberGen test result records:

```text
simulation timestep/fps
import playback fps
camera/backplate fps
export frame stride
first frame
frame count
```

A drifting atmospheric effect should not be debugged as a Niagara/UE problem if the source timing contract is wrong.

---

# 7. EmberGen benchmark should be judged on render-pass usefulness, not just beauty

For the large Monolith atmosphere test, export and evaluate separately:

- beauty/alpha;
- density-like pass if available/appropriate;
- emissive/fire-related pass if used;
- depth/other utility passes where available;
- VDB only if there is a concrete downstream need.

Adopt a pass only if a UE consumer is identified.

Do not export ten layers merely because the tool exposes ten layers.

---

# 8. Cascadeur 2026.1 — the Live Link is useful but it is not a round-trip link

Cascadeur 2026.1 rebuilt Live Link for Unreal and adds a root-motion tool, collision penetration cleaning, and other animation improvements.

Source:

- https://cascadeur.com/help/category/312

The current Live Link documentation states:

- it is a paid feature;
- available in Indie, Pro, and Teams subscriptions;
- Windows-only;
- the plug-in supports UE5.5–5.8 with Cascadeur 2026.1+;
- it streams bone transforms from Cascadeur to Unreal;
- joints are applied by name matching;
- animation can be written/recorded into an Unreal Animation Sequence;
- Live Link streams Cascadeur → Unreal, not Unreal → Cascadeur.

Source:

- https://cascadeur.com/help/category/268

## Critical correction to the mental model

Do not describe this as a bidirectional animation editor sync.

Correct model:

```text
UE-compatible skeleton/source
 -> Cascadeur authoring
 -> live preview/record into Unreal
```

not:

```text
UE edits <-> Cascadeur edits
```

---

# 9. Cascadeur Mara benchmark — revised gate

**Map:** `LV_RND_MaraAnchor_Cascadeur`

## Setup

Use a model/skeleton exported from Unreal or otherwise proven name-compatible.

## Measure

- skeleton prep minutes;
- Live Link setup minutes;
- first convincing brace/Anchor blockout;
- root-motion iteration;
- contact cleanup;
- penetration cleanup usefulness;
- Animation Sequence recording;
- UE retarget requirement;
- final re-edit turnaround.

## Pass

Cascadeur wins if it gives a materially faster physically believable body-mechanics pass and the one-way UE integration does not create unacceptable reimport friction.

## Park

If skeleton/name matching or subscription/platform requirements erase the time savings, keep Cascadeur as an occasional specialist tool.

---

# 10. Toolbag 5.03 — current release materially improves its hero-QA case

Marmoset Toolbag 5.03 build 5032 released August 12, 2026 and is documented as the latest release.

Source:

- https://docs.marmoset.co/docs/version-5-03/

Relevant changes include:

- improved layer caching for complex texture projects;
- fixes to height-map color space;
- UDIM tile detection fixes;
- curvature bake quality improvements;
- Max Ray Distance for bake rays;
- cage-generation robustness improvements;
- USD/UDIM export fixes.

Toolbag's current baking/texturing docs also support:

- Interactive Baking;
- UDIM baking;
- linked Bake Project → Texture Project workflows;
- per-tile resolution management.

Sources:

- https://docs.marmoset.co/docs/baking-attributes/
- https://docs.marmoset.co/docs/adding-a-texture-project/

## Melodia implication

The Toolbag benchmark should no longer be just "can it bake a normal map?"

Test the full **hero iteration loop**:

```text
high/low asset
 -> interactive bake
 -> cage/ray cleanup
 -> linked texture project
 -> fast lookdev/QA
 -> corrected export
 -> UE import
```

If Toolbag reduces the total hero feedback loop, it can justify a narrow role even when Substance remains the main material-authoring suite.

---

# 11. Toolbag benchmark — exact failure classes

Use one hero P2 fragment with:

- holes/close surfaces where ray distance matters;
- high curvature variation;
- at least two material IDs;
- one UDIM or multi-set case only if that reflects production reality.

Record:

- cage-fix count;
- ray-distance fixes;
- seam artifacts;
- curvature artifacts;
- height/normal color-space correctness;
- rebake time after source edit;
- reimport time into UE.

Toolbag's value is **feedback-loop compression**, not just rendering beauty.

---

# 12. Dash — keep it a last-mile human composition accelerator

Polygonflow documents Dash as an Unreal Engine 5 world-building ecosystem with:

- content browsing;
- surface/curve scatter;
- physics placement;
- vines;
- channel packing;
- blend materials;
- pivot tools;
- asset export and other artist utilities.

Sources:

- https://docs.polygonflow.io/
- https://docs.polygonflow.io/dash-tools/surfacescatter

This remains aligned with the current Melodia role:

```text
Houdini = systemic transformation
PCG/Biome = scalable distribution
Dash = optional last-mile authored composition
```

## New benchmark caution

Do not let Dash's scatter tools become a second ecology-definition system.

Allow Dash to place/finalize:
- hero debris;
- local rocks/logs;
- camera-critical props;
- physically-dropped set dressing.

Keep species selection, density logic, Monolith influence, and biome semantics in the canonical compiler stack.

---

# 13. Gaea2Unreal — strong natural Landscape handoff, weak direct answer to Mesh Terrain

Gaea's current Unreal bridge workflow prepares:

- heightfield;
- optional weight maps;
- JSON metadata;
- Unreal-friendly size/scale information;

and creates an Unreal **Landscape** through the Gaea Landscape Importer.

Source:

- https://docs.gaea.app/guides/use-in/bridges/gaea2unreal/index.html

## Melodia implication

Gaea remains valuable as:

- natural geology source;
- erosion baseline;
- mask/weight generator;
- believable terrain prior before Houdini deformation.

It is **not** currently the direct solution for the UE5.8 Mesh Terrain folded/cavity architecture.

Preferred role:

```text
Gaea natural macroform
 -> Houdini impossible/anatomical transform
 -> static mesh / Mesh Terrain R&D / Unreal representation
```

Do not evaluate Gaea by whether it independently makes impossible overhang anatomy.

---

# 14. World Creator — direct Unreal bridge has a destructive-looking reset option that must be tested carefully

World Creator documents bridge support for Unreal, Houdini, Blender, Cinema 4D, and Unity.

Source:

- https://docs.world-creator.com/reference/export/bridge-tools

The current Unreal Bridge includes options such as:

- World Partition settings;
- object import using PCG;
- `Reset PCG on Sync`;
- `Reset Detail Layers on Sync`;
- `Reimport Objects on Sync`.

Source:

- https://docs.world-creator.com/reference/export/bridge-tools/unreal-bridge

The documentation states that `Reset PCG on Sync` deletes existing PCG for the relevant Asset Name and creates a new one.

## Melodia risk

That behavior is exactly the kind of convenience feature that can destroy hand-authored downstream exceptions if enabled blindly.

### Required World Creator bridge canary

On a disposable map:

1. sync terrain;
2. inspect generated PCG/assets;
3. make one local downstream edit;
4. re-sync with reset options ON;
5. record what disappears;
6. repeat with reset options OFF;
7. inspect Git diff.

Never run first sync against a production map.

---

# 15. World Creator → Houdini may be the more Melodia-shaped route

World Creator's Houdini bridge can import terrain as:

- Houdini heightfield;
- displaced grid;
- splat/material layers as heightfield layers.

Source:

- https://docs.world-creator.com/reference/export/bridge-tools/houdini-bridge

## Why this is interesting

For Melodia, the strongest World Creator role may be:

```text
fast terrain composition
 -> Houdini heightfield + splat masks
 -> impossible topology/anatomy/semantic fields
 -> Unreal
```

rather than:

```text
World Creator owns final Unreal terrain
```

This preserves Houdini as the semantic/compiler boundary and makes World Creator replaceable.

---

# 16. World Creator / Gaea comparison — new test brief

Use one common brief:

> Horizon Eater highland/chalk steppe: geologically believable at macro scale, with clear erosion/drainage masks, before the terrain is violated anatomically in Houdini.

Each tool gets:

- 30 minutes first-pass authoring;
- identical target size;
- height output;
- 3–4 useful masks;
- one revision request after the first result.

Then Houdini gets the output and performs the same impossible transform.

Score terrain tools on:

- natural macroform quality;
- useful masks;
- iteration speed;
- bridge/export predictability;
- Houdini handoff;
- source-control footprint.

Not on final impossible anatomy.

---

# 17. New priority changes after this pass

| Tool | Updated status | Key reason |
| --- | --- | --- |
| IlluGen | TEST | excellent target fit, but docs/source reproducibility must be proven |
| LiquiGen | TEST | strong liquid output; unit/velocity conventions must be recorded |
| EmberGen | TEST | strong baked atmospheric role; timing/pass contract required |
| Cascadeur 2026.1 | TEST | UE5.8 Live Link is real, but paid/Windows/one-way |
| Toolbag 5.03 | TEST / likely narrow ADOPT candidate | current bake/texturing iteration loop is strong |
| Dash | OPTIONAL TEST | last-mile composition only; must beat native UE5.8 |
| Gaea | OPTIONAL NATURAL BASELINE | Landscape-oriented Unreal bridge; useful upstream geology |
| World Creator | OPTIONAL NATURAL BASELINE | fast bridges, but reset behavior requires canary |

---

# 18. Cross-tool hidden dependency checklist

Before a test begins, ask:

### Animation
- one-way or two-way integration?
- joint name matching?
- root motion preserved?
- paid feature?
- OS restriction?

### Simulation
- input unit?
- velocity unit?
- voxel size?
- closed collider requirement?
- source FPS?
- export frame stride?

### Terrain
- Landscape-only or mesh-capable?
- masks exported?
- bridge reset behavior?
- World Partition behavior?
- downstream edits preserved on re-sync?

### Texture/VFX generation
- exact source graph committed/preserved?
- docs mature enough to reproduce?
- channel packing?
- color-space contract?
- animation timing?

### Bake/lookdev
- rebake latency?
- cage/ray diagnostics?
- UDIM behavior?
- output color space?
- UE parity?

---

# 19. Immediate test sequence for these tools

After Tier-0/Tier-1 compiler gates:

1. Copernicus vs IlluGen — Sea Above/P3 animated texture pack.
2. Cascadeur 2026.1 — Mara Anchor one-way Live Link/Animation Sequence test.
3. Toolbag 5.03 — P2 hero feedback-loop bake test.
4. Dash — native PCG Editor Mode/Manual Editing comparison.
5. LiquiGen — hero impossible liquid with explicit Alembic convention manifest.
6. EmberGen — atmospheric event with FPS/pass manifest.
7. Gaea vs World Creator — shared natural geology brief feeding the same Houdini impossible transform.

---

# 20. Bottom line

The external tools remain valuable, but this deeper pass makes their roles narrower and safer:

- IlluGen = fast procedural VFX source, if reproducibility holds;
- LiquiGen = liquid simulation/bake source with explicit unit/velocity contract;
- EmberGen = volumetric bake source with explicit timing contract;
- Cascadeur = one-way physical animation accelerator into UE;
- Toolbag = hero bake/lookdev feedback-loop compressor;
- Dash = last-mile composition accelerator;
- Gaea/World Creator = natural geology front-ends before Houdini makes the world impossible.

That is a much healthier pipeline than allowing each application's bridge to quietly become its own world authority.
