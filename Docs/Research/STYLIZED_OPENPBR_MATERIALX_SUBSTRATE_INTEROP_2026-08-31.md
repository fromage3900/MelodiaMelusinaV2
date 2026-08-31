# Stylized OpenPBR / MaterialX / Substrate Interoperability Canary — 2026-08-31

**Project:** Melodia Melusina / UE5.8  
**Status:** constrained interchange benchmark  
**Decision:** TEST, NOT MIGRATE

## Goal

Identify the portable material subset that can move between Houdini, Substance/Sampler, Toolbag and Unreal without replacing Melodia's existing Unreal toon/material authority.

The question is not whether OpenPBR is more modern. The question is whether it reduces handoff friction while preserving the stylized result.

## Benchmark asset

Use one real hero material family with difficult properties:

- pearl / nacre iridescence;
- fabric or petal roughness variation;
- normal + height detail;
- metallic/gilded accent;
- packed masks;
- optional translucency/subsurface only if already required by production.

**Map:** `LV_RND_MaterialInterop_PearlFabric`

## Lanes

### A — project authority

Existing Unreal material/master workflow and current exported texture set.

### B — OpenPBR authoring interchange

Author/represent the same source using OpenPBR-compatible channels in Houdini/Substance where supported, export MaterialX/USD where useful, then import/translate into UE5.8.

### C — Substrate experiment

Rebuild only the portable subset in a dedicated experimental Substrate material. Do not modify frozen production master materials.

## Portable subset to prove first

```text
base color
roughness
metalness
normal
height/displacement source
emission
opacity where simple
```

Treat iridescence, stylized ramping, toon hatching, transmission and complex subsurface as feature-specific tests rather than assumptions.

## Required comparison

At fixed cameras and lighting, capture:

- source authoring view;
- Toolbag/reference view if used;
- Unreal production material;
- Unreal imported/interchanged material;
- Substrate experimental material.

Judge visual delta, not only channel completeness.

## Contract rules

- Unreal shipping material remains authority until an explicit migration project says otherwise;
- MaterialX/OpenPBR is an interchange/reference contract, not permission to let each DCC reinterpret the look independently;
- channel color space and range must be recorded;
- packed masks must be explicitly unpacked/repacked rather than silently guessed;
- every conversion records tool/build/version and import settings;
- no automatic conversion is accepted without a fixed-scene comparison.

## Metrics

```text
authoring minutes
export/import minutes
number of manual fixes
visual delta in base/roughness/specular response
normal/height fidelity
iridescence/toon mismatch
shader compile cost
runtime GPU cost
source-file clarity
round-trip reproducibility
```

## Pass / park / reject

**ADOPT as interchange subset** if base material properties round-trip predictably and reduce repeated remapping work while preserving stylized output.

**PARK advanced lobes** if iridescence/transmission/subsurface/toon behavior diverges or requires UE-specific reconstruction.

**REJECT migration** if the portable format becomes a weaker lowest-common-denominator that harms the final look or creates duplicate authorities.

## Evidence

```text
Docs/Research/Evidence/MaterialInterop/
  README.md
  channel_contract.json
  export_import_settings.md
  fixed_camera_comparison.md
  shader_cost.csv
  manual_fix_log.md
  decision.md
```

## Desired outcome

A small, boring, reliable interchange contract for common PBR data, while Melodia-specific stylization remains deliberately Unreal-owned.