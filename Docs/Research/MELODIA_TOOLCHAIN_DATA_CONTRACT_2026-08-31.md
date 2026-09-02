# Melodia Toolchain Data Contract — Semantic Fields / Interchange / Evidence

**Date:** 2026-08-31  
**Status:** proposed R&D contract for Houdini / Copernicus / SpeedTree / PCG / Niagara / Mesh Terrain / Substance / MaterialX / external authoring tools  
**Purpose:** stop world meaning from being lost when data crosses tools.

> Tool ownership can differ. Semantic meaning may not.

---

## 1. Why this exists

Melodia now has enough procedural and authoring surfaces that a new failure mode is becoming more dangerous than any one bad graph:

> the same concept exists in five tools under five names, units, coordinate systems and channel packings.

Examples:

- `filter flow` as a Houdini vector field;
- a grayscale COP texture;
- a PCG point attribute;
- a Mesh Terrain weight channel;
- a Niagara force;
- a material UV distortion direction.

Those are allowed to be different **representations** of one concept. They are not allowed to silently become different meanings.

This document defines the first shared schema.

---

# 2. Canonical schema name

```text
melodia.semantic-fields.v1
```

Any exported manifest using these names must include:

```json
{
  "schema": "melodia.semantic-fields.v1",
  "producer": "<tool/pipeline>",
  "producer_version": "<exact build>",
  "bridge_version": "<plugin build or null>",
  "engine_version": "5.8.x or null",
  "coordinate_system": "RH_YUP_ZFWD | RH_ZUP | UE_LH_ZUP | explicit",
  "linear_unit": "m | cm",
  "color_space": "linear | sRGB | ACEScg | n/a",
  "seed": 0,
  "input_hashes": {},
  "outputs": []
}
```

No procedural export is considered reproducible without explicit units and coordinate system.

---

# 3. Canonical semantic fields

## 3.1 Scalar fields

| Canonical name | Type | Domain | Meaning | Notes |
| --- | --- | --- | --- | --- |
| `melodia_moisture` | float | 0..1 | available surface/ecological moisture | 0 dry, 1 saturated; not water depth |
| `melodia_slope` | float | 0..1 | normalized surface slope | `0 = horizontal`, `1 = vertical`; do not store degrees under this name |
| `melodia_wind_exposure` | float | 0..1 | exposure to prevailing environmental flow | magnitude only; direction lives in a vector field |
| `melodia_soil_depth_m` | float | meters | estimated usable substrate depth | may exceed 1; never normalize silently |
| `melodia_monolith_distance_m` | float | meters | distance to canonical Monolith influence source | raw physical distance |
| `melodia_monolith_proximity` | float | 0..1 | artist/game normalized proximity response | must document remap curve/range in manifest |
| `melodia_molt_age` | float | 0..1 | normalized P2 biological molt age/state progression | canonical cross-tool P2 scalar |
| `melodia_filter_flow_strength` | float | 0..1 | magnitude/readability of P3 filter-flow effect | direction stored separately |
| `melodia_tension_strength` | float | 0..1 | local structural/fabric/biological tension magnitude | direction stored separately |
| `melodia_ecological_density` | float | 0..1 | intended local ecology density multiplier | does not equal literal instance count |
| `melodia_reactivity` | float | 0..1 | material/ecology readiness to react to current state | visual/game bridge field; owner must be documented |
| `melodia_wetness` | float | 0..1 | surface wetness presentation field | distinct from environmental moisture |

## 3.2 Vector fields

| Canonical name | Type | Domain | Meaning |
| --- | --- | --- | --- |
| `melodia_filter_flow_dir_ws` | float3 | normalized world-space vector | P3 horizon/filter flow direction |
| `melodia_wind_dir_ws` | float3 | normalized world-space vector | prevailing environmental wind/current direction |
| `melodia_tension_dir_ws` | float3 | normalized world-space vector | primary local tension/fiber direction |
| `melodia_surface_normal_ws` | float3 | normalized world-space vector | explicit world-space normal when needed for offline exchange |

**Rule:** vector field names ending `_ws` always mean world space after conversion to the consumer's coordinate system.

Never store a tangent-space vector under a `_ws` field name.

## 3.3 Discrete identifiers

| Canonical name | Type | Meaning |
| --- | --- | --- |
| `melodia_biome_id` | int32 | project-defined biome identifier |
| `melodia_region_id` | int32 | authored procedural region/zone |
| `melodia_material_state_id` | int32 | discrete material state when a scalar is insufficient |
| `melodia_source_id` | int64/string | stable producer element/source identifier |

Discrete IDs must never be encoded only as display colors without the original integer mapping in the manifest.

---

# 4. Representation mapping by tool

## Houdini SOPs

Preferred representation:

```text
point/vertex/primitive/detail attributes
```

Examples:

```text
f@melodia_moisture
v@melodia_filter_flow_dir_ws
f@melodia_filter_flow_strength
i@melodia_biome_id
```

Use primitive/detail attributes when a field is constant over a whole authored element rather than duplicating values at every point.

## Copernicus

Preferred representation:

- named layers;
- detached attributes where appropriate;
- EXR or ordinary texture outputs for bake handoff;
- explicit metadata/manifest mapping when packed.

Never assume `R=moisture`, `G=molt`, etc. without a manifest.

## Unreal PCG

Preferred representation:

- typed PCG metadata attributes using the canonical names;
- project Data Tables/Data Assets for remap curves and categorical mappings;
- Gameplay Tags only for discrete semantic classifications where hierarchical meaning is useful.

Do not convert continuous floats into tags.

## UE5.8 Mesh Terrain

Preferred representation:

- weight channels named from the canonical field, subject to engine naming constraints;
- Priority Layers define ownership/order, not meaning.

Recommended first channels:

```text
Moisture          <- melodia_moisture
MoltAge           <- melodia_molt_age
FilterFlow        <- melodia_filter_flow_strength
EcologyDensity    <- melodia_ecological_density
```

Vector directions cannot be reduced to a single scalar weight channel without losing information. Store direction separately through texture/vector data or derive from an agreed source.

## Niagara

Preferred representation hierarchy:

1. native project runtime/game parameters when the field is gameplay-owned;
2. PCG/material texture/data asset handoff;
3. Houdini Point Cache only after UE5.8 compatibility canary passes.

Recommended names in Niagara user parameters:

```text
User.Melodia.FilterFlowDirection
User.Melodia.FilterFlowStrength
User.Melodia.WindDirection
User.Melodia.WindExposure
```

Niagara names may be Unreal-style for ergonomics, but the manifest must map them to the canonical schema.

## SpeedTree

SpeedTree remains botanical authoring authority, not world-field authority.

Do not force raw semantic-field ingestion into SpeedTree unless a real workflow requires it.

Preferred use:

```text
canonical world fields
 -> UE PCG / material / placement logic
 -> choose SpeedTree species/variant/transform/presentation
```

A SpeedTree asset is normally a consumer-selected variant, not the source of `melodia_moisture` or `melodia_filter_flow`.

---

# 5. Coordinate-system contract

This is mandatory because the stack mixes DCC and engine conventions.

## Canonical semantic vector convention

For manifests and offline interchange, record vectors in the producer's native convention **and** include the conversion applied at each bridge.

Recommended manifest block:

```json
{
  "vectors": {
    "source_space": "Houdini_RH_YUP_or_project_actual",
    "target_space": "UE_LH_ZUP",
    "conversion": "<explicit matrix or named bridge preset>",
    "normalized_after_conversion": true
  }
}
```

Never rely on “the importer handles it” without recording which importer/version did so.

### JangaFX

LiquiGen/EmberGen export UIs expose target-package coordinate/unit conventions. Record the chosen preset in the manifest.

### World Creator / Gaea

Even if the official bridge carries scale metadata, record resulting UE dimensions from a known calibration distance.

### Calibration object

Every new bridge should support a standard test:

```text
10.0 m cube or ruler
+ one +X/+Y/+Z direction marker
```

The imported result must be measured in UE before the bridge is considered validated.

---

# 6. Texture and channel-packing contract

## Never pack first and document later

Before packing channels, define:

```text
channel
canonical semantic
value range
color space
compression target
filtering mode
mip behavior
```

Example:

```yaml
asset: T_P3_FilterFlow_Masks
color_space: linear
channels:
  R: melodia_filter_flow_strength
  G: melodia_ecological_density
  B: melodia_wind_exposure
  A: reserved_1
```

### Rules

- semantic masks are linear unless there is a deliberate exception;
- normal maps use the project's normal-map import contract, not generic color compression;
- flow vectors must document encoding convention (`RG signed 0..1`, angle+magnitude, etc.);
- roughness/metalness/AO are material data, not semantic world fields unless explicitly bridged;
- do not mark arbitrary packed masks as sRGB for convenience.

---

# 7. Material interoperability contract — MaterialX / OpenPBR

MaterialX/OpenPBR is an **interchange/reference** layer, not a replacement for Melodia's shipping master materials.

## Candidate canonical authoring parameters

For compatible assets, preserve these when possible:

```text
base_color
base_metalness
specular_roughness
specular_ior
specular_anisotropy / anisotropy direction where available
coat_weight
coat_roughness
fuzz/sheen
transmission_weight
subsurface-related parameters where supported
normal
height/displacement
```

### Version note

Current tool versions do not necessarily ship the exact same MaterialX library revision. Record MaterialX/OpenPBR version with every interchange test.

### Unreal warning

UE's current MaterialX/OpenPBR import path has shading-model limitations, including transmission/subsurface constraints. Imported material parity is evidence, not assumed correctness.

---

# 8. USD contract

Use USD for:

- asset assembly;
- lookdev/reference exchange;
- MaterialX/OpenPBR carriage;
- procedural set/variant review;
- DCC-to-DCC composition.

Do not declare USD the shipping world authority.

UE5.8 asset import can be used in production evaluation. Level import and asset pre-generation remain experimental and require separate gates.

## USD package manifest minimum

```text
root_layer
referenced_layers
meters_per_unit
up_axis
material_render_context
materialx_version
texture_search_roots
asset_hashes
```

---

# 9. Determinism contract

Every procedural artifact that is expected to recook reproducibly must record:

```text
seed
producer build
plugin/bridge build
input hashes
relevant parameter block
output hashes
```

A graph is not considered deterministic just because it has a seed parameter.

### Recook test

1. cook/export;
2. hash outputs;
3. close/reopen tool where feasible;
4. recook unchanged;
5. hash outputs again;
6. record whether hashes are identical or semantically equivalent.

For GPU/ML tools where byte identity may be unrealistic, define a tolerance metric instead of pretending exact determinism exists.

---

# 10. Ownership contract

The semantic contract does not erase system ownership.

```text
Unreal runtime/game systems = gameplay truth
Houdini = procedural authored world evidence
Copernicus = procedural image/texture evidence
SpeedTree = botanical asset truth
PCG = Unreal-side distribution/assembly
Niagara = transient VFX/readability
Substance/Toolbag = material/asset finishing and QA
JangaFX = authoring/simulation acceleration
Dash = local final dressing acceleration
```

If the same field can be authored in multiple tools, its manifest must declare the current owner.

Example:

```json
{
  "field": "melodia_filter_flow_strength",
  "owner": "Houdini:P3_FieldAuthoring_v2",
  "consumers": ["UE_PCG", "Niagara", "Material"]
}
```

A consumer must not silently become a second author.

---

# 11. Priority-layer contract for Mesh Terrain

Recommended first R&D layout:

```text
0 Base
10 HoudiniAnatomy
20 PCGEcology
30 MaterialEvidence
40 ArtistOverride
```

Rules:

- PCG reads from a defined earlier layer and writes to a later layer;
- avoid inclusive reads that include the output layer;
- `ArtistOverride` is final and should not be procedurally rewritten;
- package tests must use the compiled/build transformer pipeline, not only preview data.

---

# 12. Evidence folder pattern

Recommended lightweight pattern:

```text
Docs/Research/Evidence/Toolchain/<YYYY-MM-DD>/<tool_or_bridge>/
    result.md
    manifest.json
    metrics.json
    screenshots/
    hashes.txt
```

Large generated binaries stay outside Git unless project policy explicitly promotes them.

If generated evidence lives under `Saved/`, the committed doc must include the exact path and enough metadata to regenerate it.

---

# 13. Machine-readable result schema

Recommended v1 result:

```json
{
  "schema": "melodia.toolchain-spike-result.v1",
  "tool": "Houdini Copernicus",
  "tool_version": "22.0.xxx",
  "bridge_version": "HoudiniEngine 22.0.xxx",
  "engine_version": "5.8.x",
  "benchmark": "P2_Molt_Material_Family",
  "setup_minutes": 0,
  "hands_on_minutes": 0,
  "runtime_dependency": false,
  "packaging_test": "not_applicable",
  "determinism": {
    "seed": 20260828,
    "status": "pass|fail|tolerance"
  },
  "metrics": {},
  "decision": "ADOPT|PARK|REJECT|WATCH",
  "evidence": []
}
```

This can later feed an automated research dashboard instead of relying on prose-only decisions.

---

# 14. First implementation tasks

- [ ] Create a JSON Schema for `melodia.toolchain-spike-result.v1` if multiple spikes begin producing machine-readable results.
- [ ] Add canonical semantic field names to the P3 filter-flow benchmark.
- [ ] Add canonical field names to the P2 molt benchmark.
- [ ] Add a coordinate/unit calibration object to every new DCC bridge test.
- [ ] Add texture packing manifests to IlluGen/Copernicus comparative tests.
- [ ] Add `MPD_RND_MelodiaFoldedTerrain` weight-channel mapping for Mesh Terrain spike.
- [ ] Run Houdini-Niagara UE5.8 canary before relying on point-cache attributes.
- [ ] Run OpenPBR/MaterialX round-trip and record version mismatch/parameter loss.

---

# 15. Non-negotiable anti-drift rules

- A canonical field name has one meaning.
- Units are part of the type.
- Coordinate space is part of the type.
- Packed channels require a manifest.
- A consumer does not become an author by accident.
- A pretty editor preview is not packaging evidence.
- A bridge is not trusted until scale + axis + attribute preservation are measured.
- An import succeeding is not material parity.
- A seed alone is not deterministic proof.

The goal is not maximal standardization. The goal is to make every tool disposable enough that Melodia can swap an authoring layer without losing the world's meaning.