# Melodia Vector Field Laboratory — 2026-08-31

**Project:** Melodia Melusina / UE5.8  
**Status:** implementation-ready micro-benchmark  
**Decision:** BUILD  
**Tools:** Houdini, native UE/Niagara, VectorayGen where available

## Goal

Create one canonical vector-field contract and prove that the same directional intent can survive authoring, export/import, Unreal consumption, and visualization without silent axis/unit drift.

This is foundational for filter flow, wind, tension, pollen movement, liquid guidance, Monolith pull, and Cymatic propagation.

## Map and assets

```text
LV_RND_P3_VectorFieldLab
VF_P3_FilterFlow_Houdini
VF_P3_FilterFlow_Vectoray
VF_P3_FilterFlow_Native
NS_RND_VectorFieldVisualizer
BP_RND_VectorFieldProbe
```

## Canonical contract

Use `melodia_filter_flow_dir_ws`, `melodia_wind_dir_ws`, or `melodia_tension_dir_ws` only when the data is explicitly world-space.

For each field, record:

```text
coordinate system
handedness
up axis
forward axis
position unit
vector unit/meaning
normalization rule
sampling bounds
resolution
source build
export format
```

Generic vector attributes crossing Houdini-PCG do not get an automatic trust assumption. Conversion is explicit and centralized.

## Axis canary

Before any artistic field, round-trip these exact directions:

```text
(+1,0,0)
(-1,0,0)
(0,+1,0)
(0,-1,0)
(0,0,+1)
(0,0,-1)
```

Visualize each in UE with colored arrows and log numeric samples. Any mismatch blocks the artistic benchmark.

## Three authoring lanes

### A — Houdini

Create one obstacle-aware P3 flow field derived from simple geometry and export/bridge it using the intended production path.

### B — Native UE/Niagara

Create the closest practical field with native tools. The purpose is a baseline, not feature parity.

### C — VectorayGen

Timebox authoring after install/setup. Record exact export/import workflow and whether the semantic owner remains outside VectorayGen.

## Common brief

> P3 filter-flow current bends around three coral/monolith obstacles, accelerates through a narrow throat, then relaxes into a broad spiral basin.

Use identical bounds and probe positions.

## Probe harness

Place fixed probes at 25 known world positions. Each probe records:

- sampled direction;
- magnitude;
- expected qualitative behavior;
- angle difference against the chosen reference lane.

This turns a pretty vector visualization into measurable cross-tool evidence.

## Runtime consumers

Test the field against at least two consumers:

1. Niagara particles following the field;
2. PCG or material orientation/debug arrows.

Optional later consumers: foliage lean, Cymatic memory drift, liquid source guidance.

## Metrics

- minutes to first useful field;
- minutes for second art-direction change;
- angular error at probes;
- magnitude error where meaningful;
- export/import friction;
- data size;
- UE sampling cost;
- source reproducibility;
- coordinate-system failures;
- whether field can be regenerated after source geometry edit.

## Decision

**ADOPT a tool role** if it materially shortens field authoring while preserving the canonical contract and reproducible source.

**PARK** if visually strong but conversion/import is fragile or proprietary state becomes the only editable truth.

**REJECT** any pipeline that cannot deterministically explain world-space direction after round-trip.

## Evidence

```text
Docs/Research/Evidence/VectorFieldLab/
  README.md
  coordinate_contract.json
  axis_canary.md
  probe_samples.csv
  houdini_capture.png
  native_capture.png
  vectoray_capture.png
  runtime_perf.csv
  decision.md
```

## Architectural outcome

The expected winner may differ by task. The important deliverable is not a universal vector-field tool; it is a stable Melodia field contract that every authoring tool must obey.