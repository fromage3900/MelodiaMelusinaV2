"""Definitive test: does the in-graph Guide Curve path produce BEADS?

My earlier tests resolved group-node sockets by mapping names through the
sub-tree interface. Group node inputs support direct name lookup, so that
indirection was unnecessary and is the prime suspect for the earlier result.
This test uses direct lookup and prints each socket it touches, so a wrong
socket shows up as a wrong name rather than as silent empty geometry.

The guide geometry is IDENTICAL in both cases (the same scene curve object),
so the only variable is which route the switch selects.
"""
import sys

import bpy

sys.path.insert(0, r"P:/MelodiaMelusinaV2-Laptop/deploy")
from surreal_arch.melodia_gn.core import GROUP_BUILDERS  # noqa: E402

MM = 0.001

cu = bpy.data.curves.new("gc", "CURVE")
cu.dimensions = "3D"
sp = cu.splines.new("POLY")
sp.points.add(1)
sp.points[0].co = (0.0, 0.0, 0.0, 1.0)
sp.points[1].co = (0.20, 0.0, 0.0, 1.0)
gob = bpy.data.objects.new("gc", cu)
bpy.context.scene.collection.objects.link(gob)

sub = GROUP_BUILDERS["MEL_nikki_bead_string"]()
sub = sub[0] if isinstance(sub, (tuple, list)) else sub


def run(use_curve, tag):
    h = bpy.data.node_groups.new("h", "GeometryNodeTree")
    h.is_modifier = True
    h.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    h.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = h.nodes.new("NodeGroupInput")
    go = h.nodes.new("NodeGroupOutput")
    grp = h.nodes.new("GeometryNodeGroup")
    grp.node_tree = sub

    names = [s.name for s in grp.inputs]
    if "Guide Curve" not in names or "Guide From Curve" not in names:
        print("  %-22s MISSING SOCKET; have=%s" % (tag, names))
        return None

    h.links.new(gi.outputs[0], grp.inputs["Geometry"])

    oi = h.nodes.new("GeometryNodeObjectInfo")
    oi.inputs["Object"].default_value = gob
    h.links.new(oi.outputs["Geometry"], grp.inputs["Guide Curve"])
    # the object route too, so BOTH routes point at the same curve
    grp.inputs["Guide"].default_value = gob

    sw = grp.inputs["Guide From Curve"]
    sw.default_value = use_curve

    h.links.new(grp.outputs["Geometry"], go.inputs[0])

    me = bpy.data.meshes.new("m")
    ob = bpy.data.objects.new("o", me)
    bpy.context.scene.collection.objects.link(ob)
    m = ob.modifiers.new("n", "NODES")
    m.node_group = h
    bpy.context.view_layer.update()
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mm = ev.to_mesh()
    n = len(mm.vertices) if mm else 0
    ys = [v.co.y for v in mm.vertices] if n else [0]
    print("  %-22s use_curve=%-5s verts=%-6d  beads~%d  y[%.2f %.2f]"
          % (tag, use_curve, n, max(0, (n - 16) // 222), min(ys) / MM, max(ys) / MM))
    ev.to_mesh_clear()
    ob.modifiers.clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    return n


print("  group node has %d inputs; Guide From Curve at index %d"
      % (len(sub.interface.items_tree), [s.name for s in sub.interface.items_tree
                                         if getattr(s, "in_out", None) == "INPUT"].index("Guide From Curve")
         if "Guide From Curve" in [getattr(s, "name", None) for s in sub.interface.items_tree] else -1))
a = run(False, "object route")
b = run(True, "curve route")
print()
print("  beads via object route: %s" % (a and a > 16))
print("  beads via curve route : %s" % (b and b > 16))
print("  RESULT %s" % ("PASS" if (a and b and a > 16 and b > 16) else "FAIL"))
print("DONE")
