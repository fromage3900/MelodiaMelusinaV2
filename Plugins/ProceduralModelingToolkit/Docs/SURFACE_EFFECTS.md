# Surface Effects

Phase 12 adds reusable surface-effect modifiers for the existing Dynamic Mesh modifier stack.

## Implemented Effects

| Effect | Geometry Script node usage | Notes |
|---|---|---|
| Cracks | `Apply Perlin Noise to Mesh`, `Set Mesh Constant Vertex Color` | Adds fine negative displacement and a dark crack mask. |
| Damage | `Apply Perlin Noise to Mesh`, `Set Mesh Constant Vertex Color`, `Blur Mesh Vertex Colors` | Adds broader chipped displacement and damage color. |
| Edge Wear | `Set Mesh Constant Vertex Color`, `Blur Mesh Vertex Colors` | Writes a pale wear mask for material interpretation. |
| Dirt | `Set Mesh Constant Vertex Color`, `Blur Mesh Vertex Colors` | Writes a dark earth mask. |
| Moss | `Set Mesh Constant Vertex Color`, `Blur Mesh Vertex Colors` | Writes a green growth mask. |
| Rust | `Set Mesh Constant Vertex Color`, `Blur Mesh Vertex Colors` | Writes an orange oxidation mask. |
| Snow | `Set Mesh Constant Vertex Color`, `Blur Mesh Vertex Colors` | Writes a cool white accumulation mask. |
| Vertex Paint | `Set Mesh Constant Vertex Color`, `Blur Mesh Vertex Colors` | Generic vertex color fill. |

## Parameter Names

- `Intensity`
- `Magnitude`
- `Frequency`
- `Seed`
- `Color`
- `Alpha`
- `BlurIterations`
- `ApplyDisplacement`

`Color` is stored as an RGB vector. `Alpha` is stored separately.

## Current Contract

These effects write vertex colors as reusable masks. Cracks and damage can also displace the mesh. Final material interpretation should be handled by project materials that read vertex color channels.

## Tests

`ProceduralModelingToolkit.SurfaceEffects.ExecuteIndependently` executes each surface effect against a transient cube Dynamic Mesh and validates non-empty output.
