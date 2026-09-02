# Melodia PCG Semantic Field Domain Mapping

**Date:** 2026-08-31  
**Project:** Melodia Melusina / UE5.8 / Houdini 22  
**Status:** companion contract for `melodia.semantic-fields.v1`  
**Purpose:** make semantic meaning survive UE PCG ↔ Houdini ↔ Biome Core ↔ Niagara/material boundaries.

---

# 1. Why this exists

UE5.8 PCG distinguishes metadata domains. Houdini also has attribute ownership/classes. A field name can survive a pipeline while its actual scope or meaning changes.

This document adds a concrete mapping layer so the project can test that semantic fields are not silently promoted/demoted between:

- whole-data metadata;
- point metadata;
- lookup-table/attribute-set metadata;
- Houdini detail/point/primitive attributes;
- downstream runtime consumers.

Primary Epic references:

- https://dev.epicgames.com/documentation/unreal-engine/procedural-content-generation-overview
- https://dev.epicgames.com/documentation/unreal-engine/procedural-content-generation-framework-data-types-reference-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes

Primary SideFX reference:

- https://www.sidefx.com/docs/houdini/unreal/pcg/overview.html

---

# 2. PCG domains used by this contract

## `@Data`

One value describing the data object as a whole.

Use for:
- schema version;
- generator identity;
- source revision;
- seed;
- coordinate/space declaration;
- provenance;
- benchmark trace ID.

Do not use for per-point ecology values.

---

## `@Points`

Per-point metadata.

Use for:
- moisture;
- Monolith proximity;
- filter-flow strength/direction;
- local ecological density;
- asset selection intent;
- local molt/tension state.

This is the main semantic world domain.

---

## `@Elements`

Attribute-set/table element metadata.

Use for:
- Biome Core root asset rows;
- lookup tables;
- reusable material/profile definitions;
- asset-family metadata that should not be duplicated per point.

Do not push whole lookup tables through Houdini merely because UE can represent them.

---

# 3. Houdini attribute ownership used by this contract

Recommended mapping:

| UE PCG domain | Houdini ownership | Notes |
| --- | --- | --- |
| `@Data` | detail | one value for incoming point cloud/data set |
| `@Points` | point | direct semantic per-point mapping |
| `@Elements` | detail arrays/table geometry/separate input | test explicitly; do not assume automatic transparent mapping |

The exact Houdini-PCG plug-in representation must be confirmed with the Tier-0 canary. This table is the desired contract, not an assertion that every type is currently preserved by the plug-in.

---

# 4. Production v1 fields

## Provenance / data-level

| Name | UE domain | Houdini owner | Type | Required |
| --- | --- | --- | --- | --- |
| `melodia_schema_version` | `@Data` | detail | string | yes |
| `melodia_generator_id` | `@Data` | detail | string | yes |
| `melodia_source_revision` | `@Data` | detail | string | yes |
| `melodia_seed` | `@Data` | detail | int | yes |
| `melodia_space_contract` | `@Data` | detail | string | yes when vectors exist |
| `melodia_trace_id` | `@Data` | detail | string | R&D recommended |

---

## Ecology / world semantics

| Name | UE domain | Houdini owner | Type | Unit/range | Vector conversion? |
| --- | --- | --- | --- | --- | --- |
| `melodia_moisture` | `@Points` | point | float | 0..1 | no |
| `melodia_wind_exposure` | `@Points` | point | float | 0..1 | no |
| `melodia_monolith_proximity_m` | `@Points` | point | float | meters | no |
| `melodia_monolith_influence` | `@Points` | point | float | 0..1 | no |
| `melodia_molt_age` | `@Points` | point | float | 0..1 | no |
| `melodia_filter_flow_strength` | `@Points` | point | float | 0..1 | no |
| `melodia_filter_flow_dir_ws` | `@Points` | point | vector3 | normalized | **yes** |
| `melodia_tension` | `@Points` | point | float | 0..1 | no |
| `melodia_tension_dir_ws` | `@Points` | point | vector3 | normalized | **yes** |
| `melodia_ecological_density` | `@Points` | point | float | 0..1 | no |
| `melodia_asset_family_id` | `@Points` | point | string/int | stable ID | no |
| `melodia_source_point_id` | `@Points` | point | int/string | stable ID | no |

---

# 5. Naming rule: encode unit or normalization when ambiguity would be dangerous

Bad:

```text
melodia_monolith_proximity
```

because a downstream user cannot know whether it means meters or normalized influence.

Preferred:

```text
melodia_monolith_proximity_m
melodia_monolith_influence
```

Bad:

```text
melodia_flow
```

Preferred:

```text
melodia_filter_flow_strength
melodia_filter_flow_dir_ws
```

A semantic name should answer what the field means without opening the generating HDA.

---

# 6. Vector-space contract

SideFX documents that generic vector attributes are not automatically coordinate-converted in the same way point positions can be, because the bridge cannot infer semantic meaning.

Therefore every vector field needs:

```text
semantic type: direction | position | normal | arbitrary vector
space: world | local | tangent
normalized: true/false
unit: if not normalized
conversion helper version
```

## Required helper names

Conceptually:

```text
MEL_UE_TO_HOU_DIRECTION
MEL_HOU_TO_UE_DIRECTION
MEL_UE_TO_HOU_POSITION
MEL_HOU_TO_UE_POSITION
```

Do not reuse a position transform on normals/directions without proving it is correct.

---

# 7. Scalar tolerance contract

For identity/pass-through tests:

- float absolute error target: `<= 1e-5`;
- integer/string IDs: exact;
- bool: exact;
- normalized direction length after round-trip: `1.0 ± 1e-4` unless zero-vector is explicitly valid.

These are project validation thresholds, not vendor guarantees.

For intentionally remapped/generated fields, record the formula/version rather than expecting pass-through equality.

---

# 8. Stable ID contract

Every point participating in a cross-DCC round-trip should carry a stable source ID.

Purpose:
- detect reordering;
- compare before/after values;
- diagnose lost/duplicated points;
- make deterministic diff reports.

Preferred field:

```text
melodia_source_point_id
```

Do not use point array order as identity.

---

# 9. Biome Core AssetID boundary

Biome Core's root asset table architecture should remain Unreal-owned.

Preferred path:

```text
semantic point
 -> melodia_asset_family_id
 -> Unreal mapping/transform graph
 -> Biome Core AssetID
 -> root asset table
 -> final SpeedTree/mesh/actor representation
```

Avoid embedding Unreal object paths throughout Houdini semantic logic.

This keeps Houdini reusable and lets Unreal retarget representation independently.

---

# 10. Complex UE5.8 attribute types — deliberately deferred

UE5.8 supports arrays, structures, sets, and maps as metadata values.

For Melodia:

```text
v1 = primitive cross-DCC types only
v2 candidate = complex types after explicit Houdini-PCG preservation test
```

Reasons:
- fewer bridge ambiguities;
- easier JSON evidence;
- easier debug visualization;
- easier HLSL/Niagara consumption;
- less risk of vendor-specific serialization assumptions.

Complex types can still be used inside Unreal-only graphs where valuable.

---

# 11. GPU PCG compatibility rule

Before a semantic field enters a GPU compute graph:

- type must be GPU-supported for the target node/HLSL path;
- domain must be appropriate;
- all Houdini transforms should normally be complete;
- CPU→GPU upload count is recorded;
- if field returns to CPU, download count is recorded.

Prefer:

```text
semantic authoring on CPU/Houdini
 -> terminal GPU detail work
```

not repeated alternation.

---

# 12. Niagara/material consumer rule

A runtime consumer must not reinterpret a field name casually.

For each consumer, document:

```yaml
consumer:
field:
expected_range:
expected_space:
clamp_behavior:
missing_field_behavior:
visual_debug_method:
```

Example:

```yaml
consumer: Niagara/P3_FilterPollen
field: melodia_filter_flow_dir_ws
expected_range: normalized
expected_space: Unreal world
missing_field_behavior: use authored fallback vector
visual_debug_method: spawn direction arrows in R&D mode
```

---

# 13. Missing-field behavior

Production consumers need explicit behavior if a field is missing.

Allowed strategies:

- fail validation and block bake;
- use deterministic default;
- use explicitly documented fallback field.

Forbidden:

- silently generate random values;
- silently reinterpret another field;
- silently treat missing normalized data as zero without documenting the visual consequence.

---

# 14. Field lifecycle

Every field has one of:

```text
SOURCE
DERIVED
TRANSIENT
BAKED
RUNTIME
DEPRECATED
```

Examples:

- `melodia_monolith_proximity_m`: DERIVED/BAKED;
- `melodia_filter_flow_dir_ws`: DERIVED/BAKED/RUNTIME consumer;
- debug curvature helper: TRANSIENT;
- obsolete experimental field: DEPRECATED.

Transient fields should be stripped before final bake unless required for debugging/reproducibility.

---

# 15. Schema versioning

Use:

```text
melodia.semantic-fields.v1
```

Breaking changes require a new version when they change:
- field meaning;
- unit;
- coordinate-space interpretation;
- ID semantics;
- required domain.

Adding an optional field can remain within the same version if old consumers remain correct.

---

# 16. Validation report format

For each HDA round-trip test, produce a table:

```text
id | field | before | received_houdini | returned_houdini | after_ue | error | pass
```

For vectors, include:

```text
length_before
length_after
angle_error_degrees
```

For datasets:

```text
point_count_before
point_count_after
missing_ids
duplicate_ids
schema_version_before
schema_version_after
```

---

# 17. First executable test matrix

## Scalar matrix

- [ ] moisture 0.0
- [ ] moisture 0.5
- [ ] moisture 1.0
- [ ] proximity 0 m
- [ ] proximity 25 m
- [ ] proximity 1000 m
- [ ] negative sentinel only if field explicitly permits it

## ID matrix

- [ ] 0
- [ ] 1
- [ ] max typical project ID
- [ ] stable string family ID

## Vector matrix

- [ ] +X
- [ ] +Y
- [ ] +Z
- [ ] -X
- [ ] -Y
- [ ] -Z
- [ ] normalized diagonal
- [ ] zero vector only as error/fallback canary

## Provenance matrix

- [ ] schema version
- [ ] generator ID
- [ ] seed
- [ ] source revision

---

# 18. Adoption gate

The semantic-field bridge is CORE-ready only when:

- domain mapping is understood;
- stable IDs survive;
- vector conversion is centralized;
- scalar tolerances pass;
- cache behavior is documented;
- Unreal asset resolution remains downstream of semantic logic;
- debug visualization exists;
- second cook is deterministic;
- clean editor reopen reproduces output.

Until then, fields are R&D data, not production contracts.

---

# 19. Bottom line

The super-pipeline becomes durable when `melodia_filter_flow_dir_ws` means exactly the same thing whether it is being computed in Houdini, filtered in PCG, used to resolve an ecology rule, or consumed by Niagara.

The semantic contract is therefore more important than any individual plug-in.
