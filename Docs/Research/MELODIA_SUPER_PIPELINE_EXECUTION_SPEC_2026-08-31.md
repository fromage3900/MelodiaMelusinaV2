# Melodia Super-Pipeline — Executable World Authoring Specification

**Date:** 2026-08-31  
**Project:** Melodia Melusina  
**Engine:** Unreal Engine 5.8  
**DCC/compiler:** Houdini 22  
**Status:** execution specification; replaces vague “tool stack” thinking with explicit ownership, contracts, benchmarks, and promotion rules.

---

# 1. Prime directive

> Every new tool must either make Melodia visibly better per artist-hour, make the existing pipeline safer/reproducible, or remove a manual boundary between systems we already own.

The target is **not** maximum software count.

The target is a small, powerful, replaceable compiler stack.

---

# 2. Production ownership model

## Layer A — authored source truth

### SpeedTree
Owns:
- botanical identity;
- branching/leaf/frond construction;
- plant-level wind authoring;
- species variants;
- authored plant source.

Does not own:
- world ecology rules;
- biome logic;
- gameplay state;
- runtime procedural world authority.

### Blender / ZBrush / Marvelous / other DCCs
Own:
- hero meshes;
- sculpt/detail source;
- authored geometry that is not best generated procedurally.

---

## Layer B — deep procedural compiler

### Houdini SOPs
Own:
- geometry transformation;
- semantic fields derived from geometry;
- impossible terrain/anatomy construction;
- curve/spline processing;
- offline simulation;
- deterministic batchable transformations.

### Houdini Copernicus
Owns:
- geometry-aware masks/textures;
- adjacency/distance/curvature-driven look data;
- shared geometry→texture state;
- HDA texture outputs to Unreal where advantageous.

### Houdini-PCG bridge
Owns:
- selected deep procedural stages inside UE PCG graphs;
- semantic data transformation;
- curve/point/attribute processing;
- authoring-time geometry generation where justified.

Does not own:
- shipping runtime state;
- every PCG operation;
- direct gameplay logic.

---

## Layer C — Unreal procedural orchestration

### UE PCG
Owns:
- world-context orchestration;
- distribution;
- point/attribute flow;
- editor-facing procedural graphs;
- data-driven authoring;
- integration with World Partition/runtime generation.

### PCG Editor Mode
Owns:
- artist gestures into procedural systems;
- spline/surface/paint/volume authoring;
- tool presets.

### PCG Manual Editing / Data Overrides
Owns:
- hero exceptions;
- non-destructive local corrections;
- artist override layer after systemic generation.

### PCG Biome Core
Candidate owner for:
- local/global biome composition;
- AssetID-based asset resolution;
- overlapping biome priorities/blending;
- runtime hierarchical detail generation.

SpeedTree assets flow through it; Biome Core does not replace SpeedTree authoring.

---

## Layer D — Unreal representation and streaming

### World Partition
Owns shipping world streaming.

### Nanite / conventional mesh representation
Owns static geometry representation.

### Nanite Foliage / Nanite Assemblies
Experimental candidate representation for selected ecology.

### Mesh Terrain
Experimental candidate for non-heightfield/folded/cavity-rich terrain.

These are representation systems, not semantic world authority.

---

## Layer E — runtime response and presentation

### Niagara
Owns runtime particles and field-driven presentation.

### Unreal materials / Substrate project materials
Own shipping material behavior and game-responsive shader logic.

### Runtime PCG / Biome Core runtime
May own local detailed generation only where profiled and explicitly approved.

### Gameplay systems
Remain project-native Unreal gameplay authority.

---

## Layer F — optional authoring accelerators

These are evaluated as replaceable accelerators:

- IlluGen;
- LiquiGen;
- EmberGen;
- Cascadeur;
- Dash;
- Toolbag;
- Gaea;
- World Creator;
- VectorayGen;
- FluidNinja where runtime value justifies it;
- other trench-sweep candidates.

They do not become pipeline pillars by default.

---

# 3. Canonical super-pipeline flow

```text
SOURCE ASSETS / ARTIST GESTURES

SpeedTree / hero meshes / UE spline / PCG paint / data tables
        |
        v
PCG AUTHORING INPUT
        |
        +--------------------------+
        |                          |
        v                          v
native PCG transforms        Houdini HDA stage
        |                          |
        |                          v
        |                 semantic transform
        |                          |
        +------------<-------------+
        |
        v
SEMANTIC WORLD DATA
        |
        +--> Biome Core / AssetID resolution --> SpeedTree / prop families
        |
        +--> Mesh Terrain material/weight/shape layers
        |
        +--> Niagara/material field consumers
        |
        +--> terminal GPU PCG for dense detail
        |
        v
MANUAL EDITING / HERO EXCEPTIONS
        |
        v
BAKE / VALIDATE / PACKAGE
        |
        v
WORLD PARTITION + SHIPPING UE RUNTIME
```

---

# 4. Semantic data contract — minimum production fields

Every cross-tool field needs:

```text
name
meaning
type
PCG domain
unit
coordinate space
normalization rule
valid range
source/generator
revision
consumer list
```

Minimum field family:

| Field | Type | Domain | Unit/range | Meaning |
| --- | --- | --- | --- | --- |
| `melodia_moisture` | float | @Points | 0..1 | local ecological wetness |
| `melodia_wind_exposure` | float | @Points | 0..1 | exposure to macro wind |
| `melodia_monolith_proximity` | float | @Points | meters or normalized; declared per graph | distance/influence to Monolith |
| `melodia_molt_age` | float | @Points | 0..1 | P2 biological state |
| `melodia_filter_flow_strength` | float | @Points | 0..1 | P3 field magnitude |
| `melodia_filter_flow_dir_ws` | vector3 | @Points | normalized world-space direction | P3 visible/ecological flow |
| `melodia_tension` | float | @Points | 0..1 | Faraway Mother / fabric / growth tension |
| `melodia_ecological_density` | float | @Points | 0..1 | spawn-density control |
| `melodia_asset_id` | int/string | @Points | stable ID | Unreal/Biome lookup key |
| `melodia_seed` | int | @Data | integer | deterministic graph seed |
| `melodia_schema_version` | string | @Data | semver-like | semantic contract version |
| `melodia_source_revision` | string | @Data | git/content revision | provenance |

## Vector rule

Generic vectors crossing Houdini-PCG must be explicitly converted and tested.

No semantic `_ws` vector is assumed correct merely because its name survived.

---

# 5. Artifact contract for every compiler stage

Every adopted HDA/graph/tool export must have a small manifest with:

```yaml
id:
version:
owner:
source_tool:
source_tool_build:
engine_build:
license_state:
inputs:
outputs:
semantic_schema:
seed:
coordinate_contract:
runtime_dependency:
authoring_dependency:
bake_mode:
cache_policy:
rollback:
notes:
```

Where possible, include a content/hash identifier for external source files.

---

# 6. Authoring dependency versus shipping dependency

Every tool receives two independent flags.

| Tool | Authoring dependency allowed? | Shipping dependency preferred? |
| --- | --- | --- |
| Houdini | yes | no |
| Copernicus | yes | no |
| SpeedTree | yes | no beyond exported/native UE assets |
| Cascadeur | yes | no |
| IlluGen | yes | no |
| Toolbag | yes | no |
| Dash | maybe | no |
| Gaea/World Creator | maybe | no |
| UE PCG | native | yes where graph/runtime use requires it |
| Niagara | native | yes |
| Unreal materials | native | yes |
| Mesh Terrain | experimental native | only after packaging/runtime gate |
| Nanite Foliage | experimental native | only after packaging/runtime gate |
| FluidNinja | optional external runtime | only with much higher bar |

---

# 7. Tier-0 validation sequence — do this before broad external-tool testing

## T0.1 — exact H22 + UE5.8 installation record

Record:
- Houdini production build;
- UE patch/build;
- Houdini Engine plug-in layout;
- whether PCG support is integrated or separate in that build;
- PCG plug-in enabled state;
- HDA node available in PCG graph;
- license checkout result.

**Stop condition:** build mismatch or unresolved plug-in ambiguity.

---

## T0.2 — scalar PCG→Houdini→PCG round-trip

**Map:** `LV_RND_HPCG_ScalarRoundTrip`

Input:
- 1024 deterministic points;
- moisture;
- monolith proximity;
- stable ID.

HDA:
- preserve ID;
- compute ecological density;
- return PCG-native data.

Pass:
- point count expected;
- IDs unchanged;
- scalar tolerance <= `1e-5` where the operation should be lossless;
- deterministic second cook;
- clean editor reopen reproduces result.

---

## T0.3 — vector-space canary

**Map:** `LV_RND_HPCG_VectorCanary`

Input known vectors:

```text
+X, +Y, +Z, -X, -Y, -Z
```

Record exact values:

```text
UE before
Houdini received
Houdini returned
UE after
```

Pass only after the project has one reusable conversion helper.

---

## T0.4 — metadata-domain canary

Prove:
- `@Data` provenance survives as expected;
- `@Points` semantic values survive;
- `@Elements` lookup-table usage stays on Unreal side unless explicitly supported/tested through HDA.

Do not use complex PCG types cross-DCC yet.

---

## T0.5 — cook/bake/cache/source-control canary

Measure:
- temporary output path;
- baked output path;
- PCG link behavior;
- reopen/regenerate behavior;
- Git diff;
- stale external-file behavior with cache on/off.

Pass only with documented cleanup and deterministic naming.

---

# 8. Tier-1 world-compiler benchmarks

## T1.1 — P3 Filter Flow authoring surface

```text
PCG Editor Mode spline
 -> Houdini HDA
 -> distance/curvature/flow fields
 -> PCG debug arrows
 -> ecology orientation/density
```

**Map:** `LV_RND_P3_FilterFlow_HPCG`

Green latency target for an interactive edit on the benchmark workstation:
- <= 2 sec: excellent;
- 2–5 sec: usable;
- 5–10 sec: batch/hero-tool only;
- >10 sec: not an interactive authoring node.

These thresholds are project adoption targets, not vendor guarantees.

---

## T1.2 — Biome Core + SpeedTree AssetID bridge

**Map:** `LV_RND_P3_BiomeCore_SpeedTree`

Use 3–5 existing SpeedTree species families.

Houdini emits semantic selection intent; Unreal resolves final assets.

Pass if:
- changing mesh/representation in Unreal does not require HDA edits;
- local/global biome overlap remains understandable;
- source-control output is predictable;
- semantic fields can be debugged visually.

---

## T1.3 — Manual Editing hero exception

After generation, make 10 artist corrections around one fixed camera.

Regenerate upstream system.

Pass if:
- intended overrides survive;
- excluded/moved hero instances remain understandable;
- no mysterious duplicate generation appears;
- reset/restore works.

---

## T1.4 — terminal GPU PCG density pass

Only after semantic transforms are finished:

```text
semantic data
 -> GPU PCG compute graph
 -> dense micro-detail spawn
```

Record:
- CPU→GPU uploads;
- GPU→CPU downloads;
- GPU node group count;
- point count;
- generation time;
- memory/GPU timing where available.

Reject graph designs that bounce repeatedly between CPU/HDA/GPU.

---

# 9. Tier-2 tool benchmarks — exact comparators

## Copernicus vs IlluGen

**Brief:** Sea Above / P3 animated caustic-flow-distortion family.

Comparator A:
- H22 Copernicus.

Comparator B:
- IlluGen.

Same outputs:
- flow;
- distortion;
- caustic/interference;
- packed mask;
- optional flipbook.

Win condition:
- visible result;
- authoring minutes;
- re-edit speed;
- export reproducibility;
- UE texture contract correctness.

---

## Dash vs native UE5.8

**Brief:** 20-minute P3 scene dressing pass.

Comparator A:
- PCG Editor Mode + Manual Editing + native placement.

Comparator B:
- Dash.

Dash only graduates if it produces a repeatable, visible advantage over the strongest native workflow.

---

## Cascadeur vs current animation blockout

**Brief:** 3–5 second Mara Anchor action.

Compare:
- skeleton setup;
- blocking time;
- contact cleanup;
- root motion;
- UE retarget/import;
- re-edit turnaround.

---

## Toolbag vs current hero bake/lookdev

**Brief:** one hero P2 fragment/prop.

Compare:
- bake setup;
- cage/debug workflow;
- map correctness;
- UDIM handling if relevant;
- turntable/QA time;
- UE parity.

---

# 10. Tier-3 experimental engine canaries

## Mesh Terrain

**Map:** `LV_RND_MeshTerrain_FoldedPatch`

Required:
- 20–40 m folded/cavity terrain;
- declared priority-layer contract;
- PCG read/write test;
- collision;
- material weights;
- package attempt;
- World Partition interaction.

**Hard rule:** no production terrain migration on first pass.

---

## Nanite Foliage / Assemblies

Use one selected SpeedTree-authored species.

Compare:
1. current representation;
2. conventional Nanite representation;
3. experimental Nanite Foliage/Assembly path where practical.

Record:
- asset size;
- streaming behavior;
- frame/GPU cost;
- wind/deformation quality;
- build time;
- packaging stability.

---

## PVE

Package-canary first.

Only proceed to artistic growth test if:
- plugin works on pinned UE5.8 build;
- test project packages;
- output can be migrated/isolated safely.

Its job is anomalous secondary Monolith growth, not replacing SpeedTree.

---

# 11. Material interchange benchmark

## OpenPBR / MaterialX canary

**Asset:** one petal/molt material.

Path:

```text
Houdini MaterialX/OpenPBR
 -> .mtlx or USD MaterialX
 -> UE5.8 Interchange
 -> native Substrate material
```

Score:
- texture references;
- BaseColor parity;
- roughness parity;
- normal parity;
- transmission/opacity if used;
- parameter naming;
- reimport;
- compile complexity.

Adopt only the subset that is stable.

Do not force runtime Melodia shader logic into MaterialX merely for theoretical portability.

---

# 12. Unreal MCP execution contract

Official Unreal MCP is Experimental, local, unauthenticated by default, and serializes tool execution on the game thread.

Melodia already has policy infrastructure.

## Required gateway

```text
request
 -> policy check
 -> explicit operation class
 -> approval level
 -> one selected editor transport
 -> transcript
 -> verification
```

## Phase 1 allowed official MCP operations

- inspect selected actor/asset;
- inspect a sandbox PCG graph;
- Data View point inspection;
- spawn one known R&D actor;
- create/configure one test MID;
- add one harmless PCG debug branch;
- run a known automation test.

## Phase 1 forbidden

- delete;
- bulk rename;
- production-map changes;
- plugin toggles;
- source-control operations;
- arbitrary shell execution;
- simultaneous writes with Monolith/T3D.

---

# 13. Benchmark scorecard

Every tool gets a 100-point score.

| Category | Weight |
| --- | ---: |
| Visible quality / Melodia fit | 25 |
| Artist-hour improvement | 25 |
| Reproducibility / determinism | 15 |
| UE integration / native output | 10 |
| Source-control friendliness | 10 |
| Runtime/performance impact | 5 |
| Maintainability / replaceability | 10 |

## Decision thresholds

### ADOPT
- >= 80 points;
- no red safety/license/package gate;
- at least one real Melodia win;
- second-run evidence where learning bias is high.

### PARK
- 60–79;
- useful but not currently decisive;
- or blocked by version/license/package maturity.

### REJECT
- < 60;
- or violates an explicit hard gate.

### WATCH
Use when the technology is too immature, inaccessible, or architecture-only to score fairly.

A WATCH is not a soft ADOPT.

---

# 14. Hard gates that override score

A tool cannot be ADOPT regardless of score if:

- commercial/export/license state is unclear;
- shipping dependency is unacceptable;
- source assets cannot be reproduced;
- it requires production-map migration during the spike;
- it creates a second gameplay/runtime authority;
- it cannot survive editor reopen/rebuild where expected;
- packaging fails for a feature intended to ship;
- data semantics silently change across boundaries;
- it introduces uncontrolled concurrent editor mutation.

---

# 15. Evidence bundle per spike

Preferred repo structure:

```text
Docs/Research/Evidence/Toolchain/<spike-id>/
  README.md
  result.json
  versions.md
  timings.csv
  import_export_contract.md
  screenshots/
```

If screenshots/binaries are too large or repo policy rejects them, store only small contact sheets and document the external/local evidence location.

`result.json` minimum:

```json
{
  "spike_id": "T1.1-p3-filter-flow-hpcg",
  "date": "2026-08-31",
  "tool_builds": {},
  "license_state": {},
  "inputs": [],
  "outputs": [],
  "setup_minutes": 0,
  "hands_on_minutes": 0,
  "repeat_run_minutes": 0,
  "cook_seconds": [],
  "cpu_gpu_transfers": {"uploads": 0, "downloads": 0},
  "runtime_dependency": false,
  "authoring_dependency": true,
  "package_result": "not_applicable",
  "score": 0,
  "decision": "WATCH",
  "notes": []
}
```

---

# 16. Naming rules

## R&D levels

```text
LV_RND_<System>_<Benchmark>
```

Examples:

- `LV_RND_HPCG_ScalarRoundTrip`
- `LV_RND_P3_FilterFlow_HPCG`
- `LV_RND_P3_BiomeCore_SpeedTree`
- `LV_RND_MeshTerrain_FoldedPatch`
- `LV_RND_MaraAnchor_Cascadeur`
- `LV_RND_SeaAbove_IlluGen`

## HDA families

```text
HDA_MEL_<Domain>_<Purpose>_v###
```

Examples:

- `HDA_MEL_PCG_SemanticRoundTrip_v001`
- `HDA_MEL_P3_FilterFlow_v001`
- `HDA_MEL_P2_MoltField_v001`

Internal parameter names are API and should be versioned carefully.

---

# 17. Commit policy after a spike

Commit:
- result Markdown/JSON;
- source scripts/configs owned by Melodia;
- HDA specification/source if repository/license policy permits;
- small debug graphs/config notes;
- version/license records;
- timing tables;
- small screenshots/contact sheets;
- exact decision.

Do not commit:
- installers;
- vendor binaries;
- trial/sample content without permission;
- huge generated caches;
- temporary Houdini/PCG output folders;
- opaque binaries that cannot be reproduced or are already generated.

---

# 18. Rollback doctrine

Every adopted tool needs a rollback statement.

Examples:

### Houdini-PCG
Fallback:
- bake native UE outputs;
- preserve semantic source manifest;
- downstream PCG can consume baked point/data assets or replacement native transforms.

### Dash
Fallback:
- keep normal UE actors/meshes;
- remove Dash as authoring dependency.

### IlluGen
Fallback:
- retain exported textures/flipbooks;
- source can be recreated through Copernicus if needed.

### Experimental UE feature
Fallback:
- maintain static mesh / conventional foliage / non-experimental representation baseline until feature is promoted.

---

# 19. Recommended execution order

1. Pin exact H22 + UE5.8 builds.
2. Resolve Houdini-PCG plug-in packaging on the actual machine.
3. Scalar round-trip.
4. Vector canary.
5. Metadata-domain/provenance canary.
6. Cook/bake/cache/source-control canary.
7. P3 spline/HDA authoring test.
8. Biome Core + SpeedTree AssetID test.
9. Manual Editing hero correction test.
10. GPU PCG terminal pass.
11. MaterialX/OpenPBR canary.
12. Unreal MCP vs Monolith constrained comparison.
13. Copernicus vs IlluGen.
14. Cascadeur Mara Anchor.
15. Dash vs native PCG authoring.
16. Toolbag hero QA.
17. Mesh Terrain folded patch.
18. Nanite Foliage representation canary.
19. PVE package canary.
20. LiquiGen/EmberGen shot workflows.
21. Gaea/World Creator only if a terrain problem remains unsolved.
22. RTX/neural/Procedura/Magpie remain WATCH unless a concrete bottleneck appears.

---

# 20. End-state definition

The super-pipeline is considered successful when a Melodia world change can be expressed as:

```text
artist edits one source gesture/asset
 -> semantic compiler updates deterministically
 -> Unreal distribution/runtime presentation responds
 -> hero exceptions survive
 -> evidence is reproducible
 -> shipping content does not depend on unnecessary external runtimes
```

That is the standard for calling this a pipeline rather than a collection of tools.
