"""Why does the pulse move MEL_castle_gothic_window by 1.8 m?

The audit measured a 1836 mm displacement on a 2332 mm diagonal with Musical Amplitude
0.02 - which caps the offset vector at 40 mm. So something amplifies it downstream.
This measures the actual bounding box both ways and dumps the Set Position nodes.
"""
import sys

import bpy

sys.path.insert(0, r"P:/MelodiaMelusinaV2-Laptop/deploy")
from surreal_arch.melodia_gn.core import GROUP_BUILDERS  # noqa: E402

MM = 0.001
ID = "MEL_castle_gothic_window"


def run(sub, influence):
    h = bpy.data.node_groups.new("h", "GeometryNodeTree")
    h.is_modifier = True
    h.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    h.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = h.nodes.new("NodeGroupInput")
    go = h.nodes.new("NodeGroupOutput")
    g = h.nodes.new("GeometryNodeGroup")
    g.node_tree = sub
    h.links.new(gi.outputs[0], g.inputs["Geometry"])
    names = [it.identifier for it in sub.interface.items_tree
             if getattr(it, "in_out", None) == "INPUT" and getattr(it, "name", None) == "Music Influence"]
    for ident in names:
        s = g.inputs[ident]
        s.default_value = influence
        print("    influence socket set %r -> %r" % (influence, s.default_value))
    h.links.new(g.outputs["Geometry"], go.inputs[0])

    me = bpy.data.meshes.new("m")
    ob = bpy.data.objects.new("o", me)
    bpy.context.scene.collection.objects.link(ob)
    m = ob.modifiers.new("n", "NODES")
    m.node_group = h
    bpy.context.view_layer.update()
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mm = ev.to_mesh()
    co = [tuple(v.co) for v in mm.vertices]
    lo = [min(c[i] for c in co) for i in range(3)]
    hi = [max(c[i] for c in co) for i in range(3)]
    print("    influence %.1f  verts %d" % (influence, len(co)))
    for i, ax in enumerate("XYZ"):
        print("      %s  %9.2f .. %9.2f   span %9.2f mm" % (ax, lo[i] / MM, hi[i] / MM, (hi[i] - lo[i]) / MM))
    ev.to_mesh_clear()
    ob.modifiers.clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    bpy.data.node_groups.remove(h)
    return co


sub = GROUP_BUILDERS[ID]()
sub = sub[0] if isinstance(sub, (tuple, list)) else sub

print("  %s" % ID)
c0 = run(sub, 0.0)
c1 = run(sub, 1.0)
if len(c0) == len(c1):
    d = sorted(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5 for a, b in zip(c0, c1))
    print("    displacement mm: min %.3f  median %.3f  max %.3f" % (d[0] / MM, d[len(d) // 2] / MM, d[-1] / MM))

print()
print("  Set Position nodes and what feeds their Offset:")
for n in sub.nodes:
    if n.bl_idname == "GeometryNodeSetPosition":
        src = []
        for l in n.inputs["Offset"].links:
            src.append(l.from_node.bl_idname)
        print("    %-22s offset<-%s" % (n.name, ",".join(src) or "(none)"))
print("  scale-ish nodes:")
for n in sub.nodes:
    if n.bl_idname in ("GeometryNodeTransform", "GeometryNodeScaleInstances", "GeometryNodeScaleElements"):
        sc = n.inputs["Scale"]
        lk = [l.from_node.bl_idname for l in sc.links]
        print("    %-22s %-28s scale<-%s  default=%s" % (n.name, n.bl_idname, ",".join(lk) or "-", getattr(sc, "default_value", None)))
print("DONE")
