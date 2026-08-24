# Melodia Mesh Terrain P0

## Constraint

Melodia's natural-world substrate uses **UE 5.8 Mesh Terrain only**. The P0
does not create or import a classic Landscape actor. Musical PCG dressing may
be layered on top after the Mesh Terrain base is created and built.

## Source chain

1. Author the terrain recipe in Gaea (or use the recorded public DEM route
   below for a repeatable real-world anchor).
2. Export a metric mesh from Gaea's Mesher. Gaea's metric mesh mode is
   `1 unit = 1 meter`; the Unreal handoff therefore applies `100 cm per meter`.
3. Stage the mesh as a UE 5.8 Mesh Terrain partition in the isolated
   `/Game/_PROJECT/ResonantWorld/Offline/` namespace.
4. Attach the Mesh Terrain definition/material and build the partition.
5. Run the musical PCG graphs only after the terrain partition has generated;
   PCG points must read Mesh Terrain data, never a placeholder plane.

Gaea's current Unreal bridge is intentionally not the target here: its own
   product page describes direct Unreal export for standard and World
   Partition Landscapes and says Mesh actor support is forthcoming. Gaea is
   the authoring/export source; Mesh Terrain is the UE runtime substrate.

## Repeatable DEM route

`Content/Python/melodia_mesh_terrain_source.py` can query Open Topo Data's
ASTER 30 m dataset in batches, convert WGS-84 samples to a local metric ENU
grid, export an OBJ, and write a provenance manifest. The current Petal
Cantata source is a 12 km × 12 km Yoshino-region sample at 129 × 129 points
(~93.75 m sample spacing over the real ASTER 30 m dataset). A recorded response can be passed with
`--elevation-json` so the mesh build remains deterministic and auditable.

The script's output manifest records the source URL, geographic anchor,
metric extents, vertex/triangle counts, SHA-256, UE import scale, required
plugins, and the explicit `classic_landscape_used: false` guard.

## UE 5.8 plugin gate

The project must explicitly enable these engine plugins before the editor is
restarted for the Mesh Terrain pass:

- `MeshPartition`
- `MeshTerrainMode`
- `MeshPartitionWater`
- `PCGMeshPartitionInterop`

Mesh Terrain is an experimental UE 5.8 feature. Keep this proof isolated and
do not promote it to the webfront until the built partition has a clean PIE
runtime gate and a visually accepted standalone capture.

## Definition of done

- The source mesh is derived from Gaea or a named public DEM, not a generated
  greybox plane.
- The manifest's metric width/depth matches the requested real-world extent.
- Mesh Terrain partition build completes in UE 5.8.
- PCG generation reads the partition and produces tagged musical outputs.
- PIE has zero Blueprint Runtime Error, Accessed None, Fatal, Ensure, and
  cached-lighting matches.
- The beauty capture is clean and separately reviewed by lookdev.
