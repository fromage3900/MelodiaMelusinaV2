# Phase 6 Boolean Modifier

Phase 6 adds a live mesh-boolean modifier to the Procedural Modeling Toolkit. It is the Unreal counterpart to the Blender `GeometryNodeMeshBoolean` DIFFERENCE workflow used in `deploy/surreal_greybox/primitives.py`.

## Implemented modifier

| Modifier | Geometry Script node | Notes |
|---|---|---|
| Boolean | `Apply Mesh Boolean` | Cuts, joins, or intersects the target mesh with a cutter Static Mesh. |

## Supported operations

The modifier stores the operation as an integer that maps directly to `EGeometryScriptBooleanOperation`:

| Stored value | Geometry Script enum | Behaviour |
|---|---|---|
| 0 | `Union` | Merge the cutter into the target. |
| 1 | `Intersection` | Keep only the overlapping volume. |
| 2 | `Subtract` | Cut the cutter out of the target (default). |
| 3 | `TrimInside` | Trim the target inside the cutter. |
| 4 | `TrimOutside` | Trim the target outside the cutter. |
| 5 | `NewPolyGroupInside` | Assign a new poly group to the inside. |
| 6 | `NewPolyGroupOutside` | Assign a new poly group to the outside. |

The first implementation is fully wired for `Subtract` (procedural windows/doors). The other enum values are accepted by the parameter system and passed through to Geometry Script.

## Parameter names

Stable names for Phase 6 preset serialization:

- `Operation` (`int32`) — maps to `EGeometryScriptBooleanOperation`.
- `CutterMeshPath` (`FString`) — Unreal asset path, e.g. `/Game/EnvSandbox/Meshes/Primitives/SM_WindowCutter`.
- `CutterLocation` (`FVector`) — translation of the cutter in target space.
- `CutterRotation` (`FRotator`) — rotation of the cutter in target space.
- `CutterScale` (`FVector`) — scale of the cutter in target space.
- `bShowPreview` (`bool`) — hint for future preview systems; currently stored and logged.
- `bPreserveCutter` (`bool`) — when false, the transient cutter Dynamic Mesh is reset after the boolean to release memory.

## Execution flow

1. Validate that the target `UDynamicMesh` exists and is non-empty.
2. Load the cutter `UStaticMesh` from `CutterMeshPath` via `LoadObject`.
3. Convert the cutter to a transient `UDynamicMesh` using `UGeometryScriptLibrary_StaticMeshFunctions::CopyMeshFromStaticMeshV2`.
4. Apply `UGeometryScriptLibrary_MeshBooleanFunctions::ApplyMeshBoolean` with:
   - `TargetTransform` = identity
   - `ToolTransform` = `FTransform(CutterRotation, CutterLocation, CutterScale)`
   - `Operation` = clamped `Operation` value
   - default `FGeometryScriptMeshBooleanOptions` (`bFillHoles=true`, `bSimplifyOutput=true`)
5. Optionally reset the transient cutter mesh.
6. Return success/failure with a descriptive message.

## Registration

`UProceduralModelingToolkitBooleanModifier` derives from `UProceduralModelingToolkitModifier` and can be added to any `UProceduralModelingToolkitModifierStack` via `AddModifier(UProceduralModelingToolkitBooleanModifier::StaticClass())`. The stack uses Unreal reflection and does not require an explicit registration table.

## GMM geometry contract

Python-side support lives in `Content/Python/gmm/geometry/`:

- `modifiers.py` — `boolean_difference`, `boolean_union`, and `boolean_intersect` are accepted `GeometryModifier` types.
- `schemas.py` — `validate_boolean_parameters()` enforces the parameter contract.
- `ue_adapter.py` — `preview_boolean()` and `apply_boolean()` are fail-closed outside Unreal.
- `procedural_window.py` — `WindowSpec` + `build_window_stack()` produce a ready-to-intake `ModifierStack` of boolean-difference window cutters.

## Procedural window example

```python
from gmm.geometry.procedural_window import WindowSpec, build_window_stack

spec = WindowSpec(
    wall_width=8.0,
    wall_height=3.5,
    wall_thickness=0.3,
    window_width=1.2,
    window_height=1.4,
    window_sill_height=1.0,
    count=3,
)
stack = build_window_stack("/Game/EnvSandbox/Meshes/Walls/SM_Wall", spec)
print(stack.to_dict())
```

## Tests

- C++: `ProceduralModelingToolkit.Modifiers.Boolean.DifferenceSubtractsVolume` creates a cube Dynamic Mesh, builds a smaller box cutter Static Mesh, applies a boolean difference, and asserts that the mesh was modified and remains valid.
- Python: `Content/Python/gmm/tests/test_geometry_modifiers.py` verifies modifier-type acceptance, parameter validation, and cutter count from `procedural_window.py`.

## Known limitations / next steps

- A full closed-editor C++ build is required before the new class is available in the editor.
- Live editor verification of the boolean workflow against real wall assets is pending.
- PCG node integration (a `Boolean` modifier stack node) is a future Phase 10 item.
- `Union` and `Intersect` are enum-stubbed at the C++ level; the parameter contract supports them, but dedicated asset/UI presets have not been authored yet.
