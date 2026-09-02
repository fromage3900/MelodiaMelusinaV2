# Procedural Vegetation Editor — Anomalous Growth Canary — 2026-08-31

**Project:** Melodia Melusina / UE5.8  
**Status:** WATCH / package-canary-first  
**Decision:** TEST ONLY AS ANOMALOUS SECONDARY GROWTH

## Role

Do not evaluate PVE as a SpeedTree replacement.

Use it only for growth that is intentionally biologically wrong and difficult to author as ordinary botanical assets:

- tendrils invading architecture;
- root lattices seeking cymatic nodes;
- Monolith-corrupted branch structures;
- secondary growth wrapping hero props;
- short local transitions from natural to impossible vegetation.

SpeedTree remains botanical authoring truth for normal flora.

## First question: does it package?

Before art evaluation, create a minimal shipping canary.

**Map:** `LV_RND_PVE_PackageCanary`

Contains:

- one simple generated growth asset;
- one material;
- one collision/no-collision variant;
- no production dependencies.

Run editor, standalone, cook, packaged launch, reopen, and second-machine reproduction if available.

If the tested UE5.8.x build still reproduces known packaged-project failures, stop. Record WATCH and do not build production content around it.

## Artistic canary after package pass

**Map:** `LV_RND_PVE_AnomalousGrowth`

Brief:

> A normal SpeedTree-authored coral/tree stands beside a Monolith fragment. Secondary tendrils emerge from the environment, bend toward a harmonic/cymatic node, cross architecture, and visibly violate the source plant's normal growth logic.

The PVE result must look like a new layer, not a replacement tree.

## Integration boundary

```text
SpeedTree / authored mesh = normal botanical identity
Houdini / semantic fields = why abnormal growth happens
PVE = optional local anomalous-growth representation
UE = shipping/runtime authority
```

PVE must consume a clear source cue (volume/spline/points/field approximation). It should not invent ecology rules independently.

## Tests

1. package canary;
2. create one abnormal vine/root structure;
3. edit source cue and regenerate;
4. reopen editor;
5. duplicate map and migrate asset;
6. inspect Git/source-control churn;
7. package again;
8. compare authoring time against Houdini-generated vine + spline mesh/native PCG alternative.

## Metrics

```text
package success
crashes/asserts
first useful growth minutes
revision minutes
source cue clarity
regeneration stability
generated asset count
source-control churn
runtime GPU/CPU cost
collision/interaction practicality
visual uniqueness versus Houdini/native alternative
```

## Decision gates

**ADOPT narrow anomalous-growth role** only if packaging is stable, authoring is materially faster than existing tools, and PVE stays downstream of canonical ecology semantics.

**PARK** if visually excellent but UE5.8 packaging/build stability remains uncertain.

**REJECT replacement role** if it duplicates SpeedTree, creates opaque ecology logic, or cannot survive packaged builds.

## Evidence

```text
Docs/Research/Evidence/PVEAnomalousGrowth/
  README.md
  engine_plugin_manifest.json
  package_canary.md
  regeneration_test.md
  source_control_summary.txt
  houdini_native_comparison.md
  decision.md
```

## Rule

No chapter-scale PVE work before the package canary passes on the exact project engine build.