"""11.4 manifold check on the assembled pair.

Join Geometry does NOT weld. final_verify.py measures extents and pin-points but never
asks "is the mesh watertight", so the assembled pair has passed every check while being
non-manifold at four seams (front-bridge, front-hinge x2, hinge-temple x2). That is a
real defect for any delivery path that cares about a closed mesh (3D print, web viewers
that assert manifoldness, UE import).

This builds the pair, runs BKE_mesh_validate, and reports every non-manifold edge and
every loose edge. It is the check that was missing.
"""
import sys

import bpy

sys.path.insert(0, r"P:/MelodiaMelusinaV2-Laptop/deploy")
from surreal_arch.melodia_gn.core import GROUP_BUILDERS  # noqa: E402

r = GROUP_BUILDERS["MEL_eyewear_pair"]()
tree = r[0] if isinstance(r, (tuple, list)) else r

me = bpy.data.meshes.new("m")
ob = bpy.data.objects.new("o", me)
bpy.context.scene.collection.objects.link(ob)
mod = ob.modifiers.new("n", "NODES")
mod.node_group = tree
bpy.context.view_layer.update()
ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
mm = ev.to_mesh()

if not mm:
    print("  EMPTY")
else:
    # BKE_mesh_validate is what the exporter's "Validate Mesh" option calls; it
    # populates mm.validate() warnings. We re-run it to be explicit about what fails.
    mm.validate(verbose=True)
    nonmanifold = 0
    loose = 0
    # In 5.2 the validation result is exposed through the mesh's attributes; the
    # simplest portable signal is the edge flag layer written by validate().
    try:
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(mm)
        bm.edges.ensure_lookup_table()
        nonmanifold = sum(1 for e in bm.edges if not e.is_contiguous)
        loose = sum(1 for e in bm.edges if e.is_wire or len(e.link_faces) == 0)
        # boundary edges (1 face) are also non-manifold for a closed mesh
        boundary = sum(1 for e in bm.edges if len(e.link_faces) == 1)
        bm.free()
    except Exception as exc:
        print("  bmesh inspect failed: %s" % exc)

    print("  verts %d  edges %d  faces %d" % (len(mm.vertices), len(mm.edges), len(mm.polygons)))
    print("  non-manifold edges : %d" % nonmanifold)
    print("  loose edges       : %d" % loose)
    print("  boundary edges    : %d" % boundary)

ev.to_mesh_clear()
ob.modifiers.clear()
bpy.data.objects.remove(ob, do_unlink=True)
bpy.data.meshes.remove(me)
print()
print("  RESULT %s" % ("PASS" if nonmanifold == 0 else "FAIL"))
print("DONE")
