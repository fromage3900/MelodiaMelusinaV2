# Toolbag 5.03 Hero Asset Feedback Loop — 2026-08-31

**Project:** Melodia Melusina / UE5.8  
**Status:** narrow production-acceleration benchmark  
**Decision:** TEST / likely specialist role

## Goal

Measure whether Toolbag shortens the complete hero-asset correction loop, not whether it can produce a pretty bake.

```text
high/low source
 -> interactive bake
 -> cage/ray correction
 -> texture/lookdev check
 -> export
 -> Unreal import
 -> fixed-camera QA
 -> source correction
 -> rebake/reimport
```

## Benchmark asset

Use one real P2 hero fragment or ornate environment prop containing:

- close surfaces/holes that can expose ray-distance problems;
- strong curvature variation;
- at least two material IDs;
- normal + curvature + AO needs;
- one representative multi-set/UDIM case only if production actually requires it.

**Map:** `LV_RND_ToolbagHeroFeedback`

## Comparators

### A — current production workflow

Existing bake/lookdev route used by the project.

### B — Toolbag 5.03 workflow

Use Interactive Baking, explicit cage/ray controls, linked texture/lookdev project where useful, then Unreal import.

Do not replace Substance merely because Toolbag wins the bake phase.

## Test sequence

1. initial bake from identical source;
2. log cage/ray/seam failures;
3. fix until acceptable;
4. import to Unreal and capture fixed cameras;
5. make one real high-poly change;
6. rebake/reimport;
7. make one material/texture correction;
8. capture total elapsed artist minutes.

## Metrics

```text
initial setup minutes
first acceptable bake minutes
cage-fix count
ray-distance fix count
seam/curvature artifact count
rebake time after source edit
lookdev correction time
UE import/reimport time
total loop minutes
manual file-management steps
source reproducibility
final fixed-camera quality
```

## Source-control rule

Commit only reusable source/settings/manifests and lightweight evidence. Do not commit redundant large bake intermediates unless they are already part of the project asset policy.

## Decision gates

**ADOPT narrow role** if Toolbag materially reduces the total feedback loop and outputs remain straightforward for existing Unreal/Substance workflows.

**PARK** if it only wins isolated baking but creates extra file/tool state that erases the gain.

**REJECT replacement framing** if the current pipeline reaches equivalent result with less context switching or if Toolbag becomes a second material-authoring authority.

## Evidence

```text
Docs/Research/Evidence/ToolbagHeroLoop/
  README.md
  source_manifest.json
  bake_settings.md
  artifact_log.csv
  fixed_camera_comparison.md
  iteration_timing.csv
  decision.md
```

## Desired role

Toolbag earns a place only as a feedback-loop compressor for hero assets. Substance/project Unreal materials remain their existing authorities unless separately re-evaluated.