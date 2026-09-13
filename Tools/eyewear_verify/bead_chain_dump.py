"""8.0 step 2 — read the wiring, and measure the extent asymmetrically.

The control proved the inflation is inside MEL_nikki_bead's own chain (bare sphere
tracks its Radius exactly; the bead does not: X 1.65x, Y 1.91x at Radius 0.022, Z
exact). So this dumps the actual node graph rather than guessing at it, and reports
min/max separately per axis, because max(|min|, |max|) cannot tell a scale from a
translation from a shear.
"""
import os
import sys

import bpy

_WT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_WT, "deploy"))
from surreal_arch.melodia_gn.core import GROUP_BUILDERS  # noqa: E402

MM = 0.001


def describe(tree):
    print("  nodes in %s:" % tree.name)
    for n in tree.nodes:
        ins = []
        for s in n.inputs:
            links = [l.from_node.bl_idname + "." + l.from_socket.name for l in s.links]
            if links:
                ins.append("%s<-%s" % (s.name, ",".join(links)))
            elif hasattr(s, "default_value"):
                try:
                    ins.append("%s=%s" % (s.name, repr(s.default_value)[:24]))
                except Exception:
                    pass
        print("    %-34s %-34s %s" % (n.name, n.bl_idname, "  ".join(ins)))
    print("  default interface values:")
    for it in tree.interface.items_tree:
        if getattr(it, "in_out", None) == "INPUT" and hasattr(it, "default_value"):
            print("    %-22s %r" % (it.name, it.default_value))


def measure_asym(tree, radius):
    h = bpy.data.node_groups.new("h", "GeometryNodeTree")
    h.is_modifier = True
    h.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    h.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = h.nodes.new("NodeGroupInput")
    go = h.nodes.new("NodeGroupOutput")
    g = h.nodes.new("GeometryNodeGroup")
    g.node_tree = tree
    h.links.new(gi.outputs[0], g.inputs["Geometry"])
    for k in ("Segments", "Rings"):
        if k in [s.name for s in g.inputs]:
            pass
    for it in tree.interface.items_tree:
        if getattr(it, "name", None) == "Radius" and getattr(it, "in_out", None) == "INPUT":
            s = g.inputs[it.identifier]
            s.default_value = radius
            print("    set Radius %r -> %r" % (radius, s.default_value))
    h.links.new(g.outputs["Geometry"], go.inputs[0])

    me = bpy.data.meshes.new("m")
    ob = bpy.data.objects.new("o", me)
    bpy.context.scene.collection.objects.link(ob)
    m = ob.modifiers.new("n", "NODES")
    m.node_group = h
    bpy.context.view_layer.update()
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mm = ev.to_mesh()
    out = {}
    for i, ax in enumerate("XYZ"):
        vals = [v.co[i] for v in mm.vertices]
        out[ax] = (min(vals) / MM, max(vals) / MM)
    nv = len(mm.vertices)
    ev.to_mesh_clear()
    ob.modifiers.clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    bpy.data.node_groups.remove(h)
    return out, nv


for radius in (0.022, 0.044):
    tree = GROUP_BUILDERS["MEL_nikki_bead"]()
    tree = tree[0] if isinstance(tree, (tuple, list)) else tree
    print()
    print("=== MEL_nikki_bead  Radius %r  expected %.2f mm ===" % (radius, radius / MM))
    out, nv = measure_asym(tree, radius)
    for ax, (lo, hi) in out.items():
        print("    %s  min %9.2f   max %9.2f   span %9.2f" % (ax, lo, hi, hi - lo))
    print("    verts %d" % nv)
    if radius == 0.022:
        print()
        describe(tree)

print()
print("DONE")
