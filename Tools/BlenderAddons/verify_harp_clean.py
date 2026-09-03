import bpy
import bmesh

bpy.ops.import_scene.fbx(filepath="C:/EnvironmentPortfolio/BS_GodFile/Exports/MelusinaInstruments/SM_Mus_Harp_Concert_Real.fbx")

for o in bpy.context.selected_objects:
    if o.type != "MESH":
        continue
    mesh = o.data
    verts = len(mesh.vertices)
    polys = len(mesh.polygons)
    ngons = sum(1 for p in mesh.polygons if len(p.vertices) > 4)
    degen = sum(1 for p in mesh.polygons if p.area < 1e-8)
    
    bm = bmesh.new()
    bm.from_mesh(mesh)
    non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
    bm.free()
    
    status = "✓ CLEAN" if (ngons == 0 and degen == 0 and non_manifold == 0) else f"ngons={ngons} degen={degen} nm={non_manifold}"
    print(f"{o.name}: v={verts} p={polys} {status}")
