"""Probe 11.4: quantifies the assembled pair's unwelded seam verts and sizes
the Merge-by-Distance threshold.

Method: evaluate MEL_eyewear_pair realized, count boundary / wire /
non-manifold edges plus doubled verts via bmesh, then wrap the pair in a
Merge-by-Distance stage at candidate thresholds and re-measure, checking the
boxing contract (134.000) does not move.

Finding (Blender 5.2.1, 2026-09-12): the base pair is edge-manifold but
carries 5688 doubled seam verts (10464 -> 4776 at 0.02 mm); 0.05 mm already
creates wire edges. WELD_DISTANCE_MM = 0.02 in eyewear.py is this probe's
value, not a guess.
"""
import sys

import bpy

sys.path.insert(0, "P:/MelodiaMelusinaV2-Laptop/deploy")
from surreal_arch.melodia_gn.core import GROUP_BUILDERS  # noqa: E402

MM = 0.001


def build_eval(tree):
    me = bpy.data.meshes.new("__b__")
    ob = bpy.data.objects.new("__o__", me)
    bpy.context.scene.collection.objects.link(ob)
    mod = ob.modifiers.new("m", "NODES")
    mod.node_group = tree
    bpy.context.view_layer.update()
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    m = ev.to_mesh()
    return ev, m, ob, me


def release(ev, m, ob, me):
    ev.to_mesh_clear()
    ob.modifiers.clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)


def manifold_stats(m):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(m)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    boundary = sum(1 for e in bm.edges if e.is_boundary)
    nonman = sum(1 for e in bm.edges if not e.is_manifold)
    wire = nonman - boundary
    nverts = len(bm.verts)
    xs = [v.co.x for v in bm.verts]
    w = (max(xs) - min(xs)) / MM if xs else -1.0
    bm.free()
    return {"verts": nverts,
            "edges": len(m.edges) if hasattr(m, "edges") else -1,
            "boundary": boundary, "wire": wire, "nonmanifold": nonman,
            "width_mm": round(w, 3)}


def get(name):
    r = GROUP_BUILDERS[name]()
    return r[0] if isinstance(r, (tuple, list)) else r


pair_t = get("MEL_eyewear_pair")
ev, m, ob, me = build_eval(pair_t)
base = manifold_stats(m)
release(ev, m, ob, me)
print("BASE pair: verts=%d edges=%d boundary=%d wire=%d nonmanifold=%d width=%s"
      % (base["verts"], base["edges"], base["boundary"], base["wire"],
         base["nonmanifold"], base["width_mm"]))

# weld candidates, in mm
for t_mm in (0.02, 0.05, 0.1, 0.2):
    tree = bpy.data.node_groups.new("__weld__", "GeometryNodeTree")
    gi = tree.nodes.new("NodeGroupInput")
    go = tree.nodes.new("NodeGroupOutput")
    tree.interface.new_socket(name="Geometry", in_out="INPUT",
                              socket_type="NodeSocketGeometry")
    tree.interface.new_socket(name="Geometry", in_out="OUTPUT",
                              socket_type="NodeSocketGeometry")
    mg = tree.nodes.new("GeometryNodeMergeByDistance")
    mg.inputs["Distance"].default_value = t_mm * MM
    tree.links.new(gi.outputs["Geometry"], mg.inputs["Geometry"])
    tree.links.new(mg.outputs["Geometry"], go.inputs["Geometry"])
    # chain pair -> weld: build a wrapper tree
    wrap = bpy.data.node_groups.new("__wrap__", "GeometryNodeTree")
    wgi = wrap.nodes.new("NodeGroupInput")
    wgo = wrap.nodes.new("NodeGroupOutput")
    wrap.interface.new_socket(name="Geometry", in_out="INPUT",
                              socket_type="NodeSocketGeometry")
    wrap.interface.new_socket(name="Geometry", in_out="OUTPUT",
                              socket_type="NodeSocketGeometry")
    gn = wrap.nodes.new("GeometryNodeGroup")
    gn.node_tree = pair_t
    wm = wrap.nodes.new("GeometryNodeGroup")
    wm.node_tree = tree
    wrap.links.new(wgi.outputs["Geometry"], gn.inputs["Geometry"])
    wrap.links.new(gn.outputs["Geometry"], wm.inputs["Geometry"])
    wrap.links.new(wm.outputs["Geometry"], wgo.inputs["Geometry"])
    ev2, m2, ob2, me2 = build_eval(wrap)
    st = manifold_stats(m2)
    release(ev2, m2, ob2, me2)
    bpy.data.node_groups.remove(wrap)
    bpy.data.node_groups.remove(tree)
    print("WELD t=%.2fmm: verts=%d boundary=%d wire=%d nonmanifold=%d width=%s"
          % (t_mm, st["verts"], st["boundary"], st["wire"], st["nonmanifold"],
             st["width_mm"]))

print("DONE")
