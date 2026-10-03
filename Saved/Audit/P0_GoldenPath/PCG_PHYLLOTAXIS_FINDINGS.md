# PCG phyllotaxis piano path - findings (read-only, 2026-10-02)

## What exists
- PCGEx has NO planar spiral/phyllotaxis node. Only "Shape : φ Sphere" (Fibonacci-lattice SPHERE; PCGExShapeFiblat.h:17-45,125;
  EPCGExFibPhiConstant GoldenRatio|Custom; consumed by the "Create Shapes" node PCGExElementsShapes/Elements/PCGExCreateShapes.h).
  Other shapes: Circle, Grid, Polygon (PCGExElementsShapes/Public/Shapes).
- PCGEx path nodes (PCGExElementsPaths/Public/Elements): "Path : Resample" (PCGExPathResample.h:41, equal spacing), "Path : Subdivide"
  (PCGExSubdivide.h:30), "Path : Smooth" (PCGExSmooth.h:38), "Path : Write Tangents" (PCGExWriteTangents.h:26), "Path : Orient"
  (PCGExOrient.h:34, orientation sub-operation; output to transform or attribute), "Spline to Path" (PCGExSplineToPath.h:38),
  "Write Path Properties", "Path Spline Mesh Simple". Sampling: SampleNearestSpline / SampleNearestPath (PCGExElementsSampling).
- Blender GN: deploy/surreal_arch/melodia_gn/phyllotaxis.py - GOLDEN_ANGLE=137.5077 (:46), _build_spiral_points (:73),
  MEL_phyllotaxis_spiral (:187), MEL_phyllotaxis_pave (:228); registered via melodia_gn/__init__.py:131. (horn_dangl.py not grepped-hit; phyllotaxis.py is the shared source.)
- UE graphs: PCG_SeaAbove_East_PhyllotaxisBiome / _PhyllotaxisCourtyard (label PCG_East_PhyllotaxisCourtyard), builders
  Content/Python/add_sea_above_phyllotaxis_courtyard.py:13-16, expand_phyllotaxis_courtyard_graph.py:13-16 (script tags it
  "PCGEx_Fiblat_GoldenRatio", :70); Sakura PCG_Nikki_PhyllotaxisGarden(_Walkable) (phyllotaxis_swap_and_dress_2026-09-20.py:10).
  CURRENT_STATE.md:861 (140 instances, live proven 2026-09-12), :731, :465-466.
- Builder API: Content/Python/pcg_graph_builder.py - load_or_create_graph:51, clear_graph_nodes:15, add_node:30, find_pcgex_class:41
  (resolve PCGEx settings class by name fragment), wire_scatter_chain:295, fit_volume_to_ground:507.
- Piano precedent: Content/Python/build_pcg_piano.py - _make_point:49, PCGCreatePoints x2 (white/black) :215-216, coordinate_space
  LOCAL_COMPONENT :221, PCGSpawnActor NoMerging :226-235, edges :243-246. C++ APCGPianoKeyboard::AssignKeyIdentities
  (PCGPianoKeyboard.h:~277) re-derives MIDI by sorting white/black keys by LOCAL X - this WILL break on a spiral.

## Recommendation
Authored deterministic points from the golden-angle formula (PCGCreatePoints, LOCAL_COMPONENT, same as build_pcg_piano.py), then
optionally PCGEx Path:Resample/Smooth for a visual guide spline. A PCGEx chain cannot produce planar phyllotaxis natively
(Fiblat is spherical) and would re-seed/reorder points, losing note identity.

## Sketch (points in build_pcg_piano._make_point style)
```python
import math
GA = math.radians(137.50776405)
def phyllo_specs(n, c=90.0, turns_z=0.0, key_w=23.5, key_d=150.0):
    out = []
    for i in range(n):
        r, th = c*math.sqrt(i+1), i*GA        # Vogel; use th=i*GA*k for a longer winding arm
        out.append(dict(i=i, x=r*math.cos(th), y=r*math.sin(th), z=i*turns_z,
                        yaw=math.degrees(th)+90.0))   # key long axis tangent to the spiral
def make_point(unreal, s):
    p = unreal.PCGPoint()
    p.set_editor_property("transform", unreal.Transform(location=unreal.Vector(s["x"],s["y"],s["z"]),
        rotation=unreal.Rotator(0.0, s["yaw"], 0.0), scale=unreal.Vector(1,1,1)))
    p.set_editor_property("density", 1.0)
    return p
# note: a single Fermat arm spacing grows; for a LONG winding path prefer an Archimedean/log spiral (r=a+b*th) or
# ~sqrt-radius with step arc-length normalised so adjacent keys are ~key_w apart.
```
Rotator is (roll, pitch, yaw) in unreal.Rotator(roll,pitch,yaw) - verify arg order on the project's UE build.

## Risks
- Identity: key index/MIDI cannot ride the seed (re-seeded in local space). Sorting by local X in AssignKeyIdentities fails on a spiral;
  change it to sort by distance-along-path (polar angle or radius) - or emit an ordered attribute and read it. Needs C++ edit (owner-gated).
- Spawn order: PCGSpawnActor NoMerging order is not guaranteed; derive order from geometry (monotonic r/theta), not spawn index.
- Rotation per point: confirm PCGSpawnActor/InitializeFromPCGPoint applies point rotation, and the key-contact volume follows yaw.
- Terrain projection: authored z is flat; add a Projection/surface-sampler or line trace step (PCGEx SampleNearestSurface / native
  PCGSurfaceSampler/Projection) after create-points, then re-orient to normal; keep key pivots at top face.
- Local space: actor transform places the whole spiral; keyboard volume bounds must cover the spiral radius (PCGPianoKeyboard.h:220).
