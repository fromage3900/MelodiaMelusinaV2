# 07 — Gate 7 (P1): `HDA_Foundry_FlowVolume`

| | |
|---|---|
| **Purpose** | A baked vector field of how air/water moves around terrain, architecture, ocean, splines and landmarks, for presentation consumers to sample. |
| **Authority** | Baked data. Niagara systems that already exist sample it. Runtime wind semantics stay on the existing source-authority → `UMelodiaCymaticsWriterSubsystem` chain. The flow volume never writes `Cymatic_Wind*`. |
| **Inputs** | FieldAtlas tile (height, `flowdir`), collision geometry (cathedral, landmarks), optional ocean surface, guide splines, prevailing wind (from recipe; matches the channel vocabulary `wind_x/wind_y/wind_strength`). |
| **Outputs** | (a) velocity VDB (low-res, e.g. 1 m voxels over a tile), (b) surface flow texture (`flowdir_x`, `flowdir_y`, `flow` in RG/B), (c) Niagara-sampling representation: a **Volume Texture** asset imported from a 2D-sliced atlas (flipbook) or a sparse point cloud CSV of velocity samples. Manifest records voxel size, bounds and vector units (cm/s). |
| **Evidence** | `Saved/Audit/houdini_foundry/<recipe_id>/` |
| **Status** | STAGED. No recipe yet. Write `recipes/houdini_foundry/flow_volume_<place>.v1.json` (product `flow_volume`, `params.channels: ["velocity","flowdir","flow"]`) when this gate starts. |

## Network outline

`collision SDF (VDB from polygons: terrain tile + architecture) → velocity source (prevailing wind + spline guides) → Gas/Smoke solver (or a cheap potential-flow approximation: divergence-free projection around the SDF) for N settle frames → average last K frames → VDB velocity → resample to export grid → (a) VDB, (b) surface projection to XY texture, (c) volume-texture slices + point samples`.

Pick the potential-flow path for the interactive test (seconds). Use the solver path only on the heavy lane.

## Consumers (existing systems only)

mist · pollen · petals · leaves · bubbles · glitter (Gate 6 active grains) · magical motes · floating debris. Each consumer is an existing Niagara system that gains a **Vector Field / Volume Texture sample** module or a curl-noise replacement. Use the existing FX packs (`specs/niagara/*.json`) and effect types. Add the sample module to the system that already owns that look; do not fork a new system.

## Done when

One tile's flow volume verifies deterministically. In UE, one existing Niagara system visibly follows it: particles route around the cathedral rather than through it. The system is saved and reloaded, with a before/after capture.
