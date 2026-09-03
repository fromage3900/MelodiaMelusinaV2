# Modifier Framework

Phase 3 adds the generic modifier framework. It intentionally does not implement concrete modifiers.

## Goals

- provide a Blender-like modifier stack shape
- keep modifiers independent and reorderable
- allow individual enable/disable state
- support generic parameter storage
- define an execution boundary for future mesh tools
- preserve a future path for preset serialization and version migration

## Core Types

| Type | Purpose |
|---|---|
| `UProceduralModelingToolkitModifier` | Abstract base class for all future modifiers. |
| `FProceduralModelingToolkitModifierParameters` | Versioned generic parameter set. |
| `FProceduralModelingToolkitModifierParameter` | Single typed parameter value. |
| `UProceduralModelingToolkitModifierStack` | Ordered stack of instanced modifiers. |
| `FProceduralModelingToolkitModifierExecutionContext` | Source/output metadata passed into modifier execution. |
| `FProceduralModelingToolkitModifierResult` | Per-modifier success/message result. |
| `FProceduralModelingToolkitModifierStackResult` | Aggregate stack execution result. |

## Base Modifier Contract

Every future modifier derives from `UProceduralModelingToolkitModifier` and overrides:

```cpp
FProceduralModelingToolkitModifierResult Execute(
    UDynamicMesh* TargetMesh,
    const FProceduralModelingToolkitModifierExecutionContext& Context
);
```

The base implementation is a pass-through. It validates that the target Dynamic Mesh exists and returns success without changing geometry.

## Serialization

Both modifier and stack classes override `Serialize(FArchive& Ar)`.

Current serialization relies on Unreal property serialization for:

- enabled state
- modifier id
- display name
- parameter values
- stack order
- stack version
- future preset source path

Phase 6 should add JSON import/export on top of this object model, using `Version` fields for compatibility.

## Enable / Disable

Each modifier has:

```cpp
bool bEnabled;
void SetEnabled(bool bInEnabled);
bool IsEnabled() const;
```

Disabled modifiers remain in the stack but are skipped during execution.

## Parameter Struct

The generic parameter model supports:

- boolean
- integer
- float
- vector
- rotator
- string

Concrete modifiers in Phase 4 should define stable parameter names and populate defaults in their constructors.

## Modifier Stack

The stack supports:

- `AddModifier`
- `RemoveModifierAt`
- `MoveModifier`
- `SetModifierEnabled`
- `Execute`

Execution is ordered from first modifier to last modifier. The first failed enabled modifier stops the stack.

## Dynamic Mesh Pipeline Integration

The Dynamic Mesh pipeline now creates and executes an empty modifier stack between:

1. `Copy Mesh From Static Mesh`
2. `Copy Mesh To Static Mesh`

This is the official insertion point for Phase 4 and beyond.

## Future Phases

- Phase 4: Translate, Rotate, Scale, Mirror, Noise, Smooth, Recompute Normals.
- Phase 5: Extrude, Inset, Remesh, Simplify, Twist, Bend, Inflate.
- Phase 6: JSON preset save/load/duplicate/delete with versioning.
- Phase 7: batch processing for folders, selected assets, and filtered collections.
- Phase 8-9: spline ornament and filigree generators.
- Phase 10: PCG integration nodes that invoke toolkit stacks.
