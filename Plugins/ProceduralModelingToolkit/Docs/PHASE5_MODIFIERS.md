# Phase 5 Modifiers

Phase 5 adds the higher-impact modeling modifiers used for repeated environment-art workflows. Each modifier derives from `UProceduralModelingToolkitModifier` and executes independently against a `UDynamicMesh`.

## Implemented Modifiers

| Modifier | Geometry Script node | Notes |
|---|---|---|
| Extrude | `Apply Mesh Linear Extrude Faces` | Extrudes the full mesh selection by distance and direction. |
| Inset | `Apply Mesh Inset Outset Faces` | Insets or outsets the full mesh selection using Geometry Script's face inset operation. |
| Remesh | `Apply Uniform Remesh` | Rebuilds mesh tessellation by target triangle count or target edge length. |
| Simplify | `Apply Simplify To Triangle Count` | Reduces topology to a target triangle budget. |
| Twist | `Apply Twist Warp To Mesh` | Twists around a configurable transform, angle, and extent. |
| Bend | `Apply Bend Warp To Mesh` | Bends around a configurable transform, angle, and extent. |
| Inflate | `Apply Mesh Offset` | Offsets vertices along averaged normals for inflate/deflate behavior. |

## Parameter Names

These names are stable for Phase 6 preset serialization.

- `Distance`
- `Direction`
- `UseAverageNormal`
- `UVScale`
- `SolidsToShells`
- `Reproject`
- `BoundaryOnly`
- `Softness`
- `AreaScale`
- `TargetTriangleCount`
- `TargetEdgeLength`
- `UseTargetEdgeLength`
- `RemeshIterations`
- `SmoothingRate`
- `ReprojectToInputMesh`
- `DiscardAttributes`
- `Angle`
- `Extent`
- `Origin`
- `Orientation`
- `SymmetricExtents`
- `LowerExtent`
- `Bidirectional`
- `FixedBoundary`
- `SolveSteps`
- `SmoothAlpha`

## Tests

`ProceduralModelingToolkit.Modifiers.Phase5.ExecuteIndependently` creates a transient cube Dynamic Mesh and executes each Phase 5 modifier independently.

The test verifies:

- modifier object creation
- successful execution
- non-empty output mesh
- valid post-execution triangle count

## Notes

Several Phase 5 modifiers alter topology and may be expensive on high-resolution assets. Batch processing should use progress reporting and cancellation before these are exposed to folder-level processing.
