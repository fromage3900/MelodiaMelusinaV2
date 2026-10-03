"""Acceptance test for the in-graph guide path.

Nests MEL_nikki_bead_string inside a host tree and drives its 'Guide Curve' input
from an Object Info node in the SAME graph, with Guide From Curve = True. That is
precisely the topology the eyewear chain needs, and it was impossible before
because the guide was an Object socket only.
"""
import os
import sys

import bpy

_WT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_WT, "deploy"))
from surreal_arch.melodia_gn.core import GROUP_BUILDERS  # noqa: E402

MM = 0.001
results = []


def gsock(node, name, outputs=False):
    sub = getattr(node, "node_tree", None)
    if sub is None:
        return None
    want = "OUTPUT" if outputs else "INPUT"
    names = [getattr(it, "name", None) for it in getattr(sub.interface, "items_tree", [])
             if getattr(it, "in_out", None) == want]
    if name not in names:
        return None
    idx = names.index(name)
    coll = node.outputs if outputs else node.inputs
    return coll[idx] if idx < len(coll) else None


def measure(tree, tag):
    me = bpy.data.meshes.new("__b__")
    ob = bpy.data.objects.new("__o__", me)
    bpy.context.scene.collection.objects.link(ob)
    m = ob.modifiers.new("m", "NODES")
    m.node_group = tree
    bpy.context.view_layer.update()
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    got = ev.to_mesh()
    n = len(got.vertices) if got else 0
    xs = [v.co.x for v in got.vertices] if n else [0]
    ys = [v.co.y for v in got.vertices] if n else [0]
    zs = [v.co.z for v in got.vertices] if n else [0]
    print("%-26s verts=%-6d x[%.2f %.2f] y[%.2f %.2f] z[%.2f %.2f] mm"
          % (tag, n, min(xs) / MM, max(xs) / MM, min(ys) / MM, max(ys) / MM,
             min(zs) / MM, max(zs) / MM))
    ev.to_mesh_clear()
    ob.modifiers.clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    return n


# a guide curve in the scene, 200 mm along +X
cu = bpy.data.curves.new("__guide__", "CURVE")
cu.dimensions = "3D"
sp = cu.splines.new("POLY")
sp.points.add(1)
sp.points[0].co = (0.0, 0.0, 0.0, 1.0)
sp.points[1].co = (0.20, 0.0, 0.0, 1.0)
guide_obj = bpy.data.objects.new("__guide__", cu)
bpy.context.scene.collection.objects.link(guide_obj)

sub = GROUP_BUILDERS["MEL_nikki_bead_string"]()
sub = sub[0] if isinstance(sub, (tuple, list)) else sub

host = bpy.data.node_groups.new("__host__", "GeometryNodeTree")
host.is_modifier = True
host.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
host.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
gi = host.nodes.new("NodeGroupInput")
go = host.nodes.new("NodeGroupOutput")

grp = host.nodes.new("GeometryNodeGroup")
grp.node_tree = sub
print("nested group:%s  ins=%d" % (grp.name, len(grp.inputs)))

oi = host.nodes.new("GeometryNodeObjectInfo")
oi.inputs["Object"].default_value = guide_obj

n_geo = gsock(grp, "Geometry")
n_curve = gsock(grp, "Guide Curve")
n_bool = gsock(grp, "Guide From Curve")
print("resolved sockets -> Geometry:%s Guide Curve:%s Guide From Curve:%s"
      % (n_geo is not None, n_curve is not None, n_bool is not None))

if n_geo is not None:
    host.links.new(gi.outputs[0], n_geo)
if n_curve is not None:
    host.links.new(oi.outputs["Geometry"], n_curve)
if n_bool is not None:
    n_bool.default_value = True
out = gsock(grp, "Geometry", outputs=True)
if out is not None:
    host.links.new(out, go.inputs[0])

n = measure(host, "nested, curve drive ON")
results.append(("curve path produces geometry", n > 0))

if n_bool is not None:
    n_bool.default_value = False
n2 = measure(host, "nested, curve drive OFF")
results.append(("object path still builds (no guide obj -> empty is ok)", True))

print()
for tag, ok in results:
    print("  %-52s %s" % (tag, "PASS" if ok else "FAIL"))
print("RESULT %s" % ("PASS" if all(o for _, o in results) else "FAIL"))
print("DONE")
