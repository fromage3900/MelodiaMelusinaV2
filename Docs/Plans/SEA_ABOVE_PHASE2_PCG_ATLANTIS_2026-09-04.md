# SeaAbove Phase 2: terrain grounded dressing and Atlantis kit

Date: 2026-09-04
Level: `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype`

## Scale decision

The landscape remains at its authored extent of approximately 249,752 cm per axis (about 5 km square). The playable map should gain scale through districts, sightline rhythm, and streaming, not by shrinking the terrain or raycasting a collapsed copy of the world. Existing hero volumes remain human-readable local set pieces; the eastern third is the first controlled expansion district.

## PCG cells

All new scatter graphs use a downward landscape-only World Raycast after their point-producing branches. A miss keeps the original point, while non-landscape hits are rejected. This makes the graphs safe to reuse on later terraces and keeps props on the terrain instead of at the volume's source Z.

| Cell | Graph | Anchor | Volume scale | Result |
| --- | --- | --- | --- | --- |
| East ridge | `PCG_SeaAbove_East_Scree` | `(170000,-70000,43368)` | `(30,20,3)` | 1,020 rock instances in 51 ISMs |
| East terrace | `PCG_SeaAbove_East_TerraceGarden` | `(190000,-90000,38981)` | `(24,16,2.5)` | 215 instances in 11 ISMs |
| Atlantis grove | `PCG_SeaAbove_East_AtlantisGrove` | `(210000,-90000,42733)` | `(12,10,2)` | 191 instances in 11 ISMs |
| East phyllotaxis ridge | `PCG_SeaAbove_East_PhyllotaxisBiome` | `(220000,50000,67007)` | `(8,8,2)` | 140 rock instances in 3 ISMs |

The Atlantis grove is a derivative of the terrace graph. Its branch roles now use corrected Atlantis arch, column, tree, and shrub meshes, with the largest branch biased to shrubs so the area reads as a garden around a few architectural beats rather than a repeated building field.

The authored architecture point transforms in both the TerraceGarden and Atlantis derivatives were normalized to a unit-scale band. The source graph contained non-uniform values as high as `262.9` on a column axis, which made a dressing actor's editor bounds balloon across the map. After normalization the TerraceGarden remains 215 instances with a maximum generated scale of 1.29, while the Atlantis grove remains 191 instances inside an approximately 34 m by 33 m cell with a maximum generated scale of 1.24.

The conservative LOD0 budget for that grove is about 0.66M triangles; the rock cell is about 0.47M triangles. Both use instanced static mesh components, so the raw per-instance draw estimate is intentionally higher than the runtime cost.

The phyllotaxis ridge is the reusable curated-biome recipe. It derives from `PCG_Nikki_PhyllotaxisGarden`, keeps `PCGExCreateShapeFiblat` on its `GoldenRatio` phi constant, and uses a fixed resolution of 140 over an approximately 18 m local shape. The golden-angle distribution supplies the macro spacing while the Fiblat shape supplies the nested radial rhythm; this produces a garden-like cadence without a square grid. A landscape-only downward World Raycast is inserted before the transform/spawn branch, with `select_landscape_hits=Require`, `ignore_pcg_hits=true`, and original points retained only on a miss. At the authored actor scale the generated footprint is about 40 m square, the Z span is about 57 cm on the selected ridge, and generated instance scales stay below 1.40. The same graph can be reused for a second biome by changing the anchor and actor scale while leaving the golden-ratio construction intact.

## Navigation and pacing

The east district has local bounds around the hero cells plus a fourth bounds volume centered near `(190000,-70000,45000)` with extent `(28000,26000,14000)` for the expanded dressing district. Navigation built cleanly at 12,576 tiles across four bounds; the expanded eastern bound persisted through an editor reload. Current measured routes are:

- BellTree to east terrace: 8,045 cm
- BellTree to Xylophone: 22,642 cm
- Xylophone to Cathedral: 30,101 cm
- Cathedral to Colonnade: 22,891 cm

The minimum measured route width at the BellTree entry is 724 cm, above the 300 cm traversal contract. These routes provide the initial Nikki-style promenade: intimate hero cells connected by longer landscape views and deliberate breathing space.

## Atlantis asset utility set

Vendor meshes remain untouched. The following derived assets live under `/Game/EnvSandbox/Meshes/Atlantis_PivotFixed/`:

`ArchA`, `ArchB`, `ColumnsA`, `ColumnsB`, `TreeA`, `TreeD`, `ShrubsA`, and `ShrubsC`.

Each derived mesh has a bottom-center pivot, complex collision as simple, preserved source material slots, and Nanite enabled. LOD chains were generated for the six higher-cost assets; the source geometry is retained at LOD0 for hero framing. All eight pivots pass the bottom-center check and all eight have collision.

The 54 architecture-prefixed Atlantis material instances now inherit from their canonical, texture-authored counterparts under `/Game/EnvSandbox/Materials/Instances/Atlantis/MI_*`. This preserves the existing local scalar accents while restoring the canonical Albedo, Height, Normal, Metallic, Roughness, and opacity wiring. The remap was saved as 54 exact packages after clearing the read-only file attribute that caused the editor save crash.

The converged `M_Master_Nikki_Landscape` recompiles successfully (353 pixel and 153 vertex instructions). Its validator still reports duplicate and unused parameter warnings from the intentionally layered legacy branches; the active Gaea path is compiled and the Glacier instance carries whole-landscape remap vectors (`Min=(-249752,-249752)`, `Size=(499504,499504)`) with `bGaeaWholeLandscapeColor` and `bUseGaeaMasks` enabled.

## Next pass

Extend the same cell contract west-to-east in additional bounded zones, then add sightline/choke-point exclusions to keep landmarks legible. Houdini Engine and VDMs remain a later authored-landform lane; they should feed masks and proxy geometry into these cells rather than replace the landscape scale or the terrain-grounding contract.
