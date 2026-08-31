# Environmental VFX Ownership Stack — 2026-08-31

**Project:** Melodia Melusina / UE5.8  
**Status:** implementation-ready comparative plan  
**Goal:** stop evaluating Niagara, FluidNinja, LiquiGen, EmberGen, Houdini and IlluGen as interchangeable tools.

## Ownership doctrine

```text
Niagara          = runtime local response / interactive fields / particles
Houdini          = offline semantic simulation and reusable authored fields
LiquiGen         = liquid simulation source / bake / hero cache
EmberGen         = volumetric source / bake / hero atmosphere
FluidNinja       = optional runtime environmental-interaction accelerator only if it beats native Niagara
IlluGen          = procedural VFX texture/flow/flipbook authoring accelerator
Copernicus       = geometry-aware masks/textures/fields where H22 wins the task
```

No third-party VFX tool becomes gameplay authority.

## Common benchmark

**Map:** `LV_RND_P3_EnvironmentalReactionStack`

Brief: player-local harmonic caustic-flow event around shallow water/coral, followed by one hero splash and one Monolith atmospheric pulse.

## Test matrix

### Runtime field lane

Compare:
- native Niagara Grid2D/Grid3D/NDC baseline;
- FluidNinja only if installed and compatible.

Measure latency, GPU ms, cross-surface coherence, authoring time, deterministic reset, package result.

### Liquid source lane

LiquiGen creates one hero liquid event. Record:
- position units;
- velocity unit;
- velocity binding;
- velocity attribute name;
- voxel size versus thinnest collider;
- export type: flipbook/image/Alembic;
- downstream UE consumer.

Do not use LiquiGen as runtime water authority.

### Volumetric source lane

EmberGen creates one Monolith atmospheric pulse. Record:
- simulation timestep/FPS;
- imported animation FPS;
- camera/backplate FPS;
- export first frame/count/stride;
- exact useful passes;
- whether VDB has a concrete consumer.

### Texture/flow lane

Run the same caustic/distortion/flow deliverable through:
- H22 Copernicus;
- IlluGen;
- native material/Niagara approximation.

Judge first useful result, revision time, source reproducibility, UE import friction, and final stability.

## Hard boundaries

- Niagara owns runtime gameplay-adjacent presentation because it lives inside Unreal.
- external tools may create sources/caches/textures but should not require runtime editor/service dependencies;
- every baked source needs a manifest with units, FPS, color space, packing, seed, and source build;
- a beautiful vendor sample does not count as evidence;
- export ten passes only when ten consumers exist.

## Metrics

```text
artist minutes to first usable result
artist minutes to second revision
runtime GPU/CPU ms
memory footprint
package/cook result
source reproducibility
unit/FPS mistakes discovered
source-control footprint
visual quality at fixed cameras
runtime dependency count
```

## Decision gates

**ADOPT narrow role** when a tool clearly wins a specific family of tasks and leaves deterministic, documented Unreal-consumable outputs.

**PARK** when quality is excellent but the handoff/reproduction burden is too high for common production.

**REJECT duplicate role** when native Niagara/Copernicus reaches the same result in comparable time with less pipeline risk.

## Evidence

```text
Docs/Research/Evidence/EnvironmentalVFX/
  README.md
  benchmark_manifest.json
  niagara_result.md
  fluidninja_result.md
  liquigen_manifest.json
  embergen_manifest.json
  copernicus_vs_illugen.md
  perf_summary.csv
  decision_matrix.md
```

## Recommended execution order

```text
1. native Niagara baseline
2. Copernicus baseline
3. IlluGen texture/flow test
4. LiquiGen hero liquid
5. EmberGen hero atmosphere
6. FluidNinja only if native runtime-field limitations remain
```

The point is a clean ownership stack, not collecting every VFX package.