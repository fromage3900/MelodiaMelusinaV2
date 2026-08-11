# Dynamic Mesh Pipeline

The Dynamic Mesh pipeline is the first reusable mesh-processing lane in the Procedural Modeling Toolkit.

It performs a conservative round trip:

1. Read selected `UStaticMesh` assets from the Content Browser selection.
2. Validate that each source mesh is readable and has SourceModel LOD0 geometry.
3. Duplicate the source mesh to `/Game/EnvSandbox/Procedural/Meshes/Processed`.
4. Convert the original Static Mesh into a transient `UDynamicMesh`.
5. Convert the transient Dynamic Mesh back into the duplicated Static Mesh asset.
6. Save the duplicated Static Mesh.
7. Validate that the output asset exists, is separate from the source, and has non-empty geometry.

The original mesh is never written to. The duplicate is the write target.

## Documentation Reviewed

This implementation follows the project direction from:

- `Docs/SANDBOX_LONGTERM_PLAN.md`: keep generated outputs under EnvSandbox, preserve stock-engine durability, and avoid brittle custom graph ports.
- `Docs/PCG_PORTFOLIO_PLAN.md`: build reusable pipelines under EnvSandbox rather than migrating old fragile systems directly.
- `Docs/PCG_MELODIA_SALVAGE_MAP.md`: use rebuild/thin-wrapper patterns and keep legacy content as reference.
- `RoofGeneratorPro/README.md` and `RoofGeneratorPro/CHANGELOG.md`: prefer stable modifier anchors and non-destructive processing over broken procedural-node ambition.

## Geometry Script Nodes Used

These are C++ calls to Geometry Script Blueprint nodes. Their Blueprint display names are listed because future artist-facing tools may expose the same operations.

| Blueprint node | C++ API | Purpose |
|---|---|---|
| `Check Static Mesh Has Available LOD` | `UGeometryScriptLibrary_StaticMeshFunctions::CheckStaticMeshHasAvailableLOD` | Validates that SourceModel LOD0 can be read before conversion. |
| `Copy Mesh From Static Mesh` | `UGeometryScriptLibrary_StaticMeshFunctions::CopyMeshFromStaticMeshV2` | Copies the selected source `UStaticMesh` into a transient `UDynamicMesh`. |
| `Copy Mesh To Static Mesh` | `UGeometryScriptLibrary_StaticMeshFunctions::CopyMeshToStaticMesh` | Writes the transient `UDynamicMesh` into the duplicated `UStaticMesh` asset. |

No deformation, boolean, remesh, bevel, UV generation, or cleanup modifiers are applied in this phase.

## Validation Checks

Source validation:

- selected object must be a `UStaticMesh`
- source must not be null
- source must not be a compiled-in engine asset
- source must have at least one source model
- source LOD0 triangle count must be greater than zero
- Geometry Script must report SourceModel LOD0 as available

Round-trip validation:

- output mesh must exist
- output mesh must not be the same UObject as the source
- output path must not match source path
- saved output asset must exist in the asset registry path
- Dynamic Mesh triangle count must be greater than zero
- output Static Mesh LOD0 triangle count must be greater than zero
- output triangle count must match the transient Dynamic Mesh triangle count

## Future Modifier Insertion Point

Future modifiers should operate after `CopyMeshFromStaticMeshV2` and before `CopyMeshToStaticMesh`.

Example future stages:

- bevel/chamfer
- architectural panel slicing
- procedural cornice extrusion
- UV projection
- material ID remapping
- collision generation
- PCG-driven batch processing

Each modifier should add its own validation before writing the duplicate asset.
