# Phase 4 Modifiers

Phase 4 adds the first concrete modifiers. Each modifier derives from `UProceduralModelingToolkitModifier` and can execute independently against a `UDynamicMesh`.

## Implemented Modifiers

| Modifier | Geometry Script node | Notes |
|---|---|---|
| Translate | `Translate Mesh` | Applies a vector offset to all vertices. |
| Rotate | `Rotate Mesh` | Rotates around a configurable origin. |
| Scale | `Scale Mesh` | Scales around a configurable origin. |
| Mirror | `Apply Mesh Mirror` | Mirrors across a configurable frame with cut/weld options. |
| Noise | `Apply Perlin Noise to Mesh` | Applies 3D Perlin displacement, defaulting to normal-based displacement. |
| Smooth | `Apply Iterative Smoothing to Mesh` | Applies full-mesh iterative smoothing. |
| Recompute Normals | `Recompute Normals` | Recomputes mesh normals with angle/area weighting options. |

## Parameter Names

Stable parameter names are intentionally simple so Phase 6 preset JSON can serialize them directly.

- `Translation`
- `Rotation`
- `Origin`
- `Scale`
- `PlaneOrigin`
- `PlaneRotation`
- `ApplyPlaneCut`
- `FlipCutSide`
- `WeldAlongPlane`
- `Magnitude`
- `Frequency`
- `FrequencyShift`
- `Seed`
- `ApplyAlongNormal`
- `Iterations`
- `Alpha`
- `AngleWeighted`
- `AreaWeighted`

## Tests

`ProceduralModelingToolkit.Modifiers.Phase4.ExecuteIndependently` creates a transient cube Dynamic Mesh and executes each Phase 4 modifier independently.

The test verifies:

- modifier object creation
- successful execution
- non-empty output mesh
- valid post-execution triangle count
- stable triangle count for non-topology modifiers
