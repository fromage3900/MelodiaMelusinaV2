# PCG Integration

Phase 10 adds custom PCG settings/elements that invoke the Procedural Modeling Toolkit from PCG graphs.

## Nodes

| Node | Purpose |
|---|---|
| `PMT Generate Ornaments` | Generates deterministic ornament or filigree spline paths. |
| `PMT Modify Meshes` | Applies a modifier stack to an assigned Static Mesh through the Dynamic Mesh pipeline. |
| `PMT Process Splines` | Generates and prepares toolkit spline path data for downstream PCG use. |
| `PMT Generate Dynamic Mesh` | Creates a transient Dynamic Mesh and optionally applies a modifier stack. |
| `PMT Output Static Mesh` | Runs the Dynamic Mesh pipeline and saves a new Static Mesh asset. |

## Current Contract

The first integration pass registers native PCG nodes and invokes toolkit systems. Nodes pass PCG data through so they can be inserted into existing graphs without breaking downstream wiring.

Asset-writing nodes run on the main thread and are marked non-cacheable because they can create editor assets.

## Future Work

The next PCG iteration should add typed PCG data outputs for:

- spline path collections
- Dynamic Mesh resources
- generated Static Mesh asset references
- modifier stack diagnostics

That typed data layer can be added behind these stable node names.
