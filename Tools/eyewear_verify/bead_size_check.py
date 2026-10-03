"""Does Bead Radius control bead size? Fresh tree per value, set asserted.

The previous version of this test reused ONE bead-string tree across four runs and
mutated its interface defaults in place. If a set silently failed, the previous
value persisted and the measurement described the wrong value. Same class of
mistake as the guide-switch test. This rebuilds the tree for every value and fails
loudly if the default did not take.

Beads are instanced along a straight guide on +X at y=0, so a bead's Y half-extent
IS its radius. Cord radius is 0.0032, well below any expected bead size.
"""
import os
import sys

import bpy

_WT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_WT, "deploy"))
from surreal_arch.melodia_gn.core import GROUP_BUILDERS  # noqa: E402

MM = 0.001


def measure(radius_m):
    """Build a FRESH bead string, set the radius, measure the bead."""
    sub = GROUP_BUILDERS["MEL_nikki_bead_string"]()
    sub = sub[0] if isinstance(sub, (tuple, list)) else sub

    # kill taper and jitter so only the radius can move the number
    want = {"Bead Radius": radius_m, "Taper": 0.0, "Jitter": 0.0,
            "Droop": 0.0, "Bead Count": 6}
    got = {}
    for it in sub.interface.items_tree:
        n = getattr(it, "name", None)
        if n in want:
            it.default_value = want[n]
            got[n] = it.default_value
    for n, v in want.items():
        assert n in got, "param %s missing from the interface" % n
        assert abs(got[n] - v) < 1e-9, "set failed for %s: %r != %r" % (n, got[n], v)

    h = bpy.data.node_groups.new("h", "GeometryNodeTree")
    h.is_modifier = True
    h.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    h.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = h.nodes.new("NodeGroupInput")
    go = h.nodes.new("NodeGroupOutput")
    ln = h.nodes.new("GeometryNodeCurvePrimitiveLine")
    ln.inputs["Start"].default_value = (-0.30, 0.0, 0.0)
    ln.inputs["End"].default_value = (0.30, 0.0, 0.0)
    g = h.nodes.new("GeometryNodeGroup")
    g.node_tree = sub
    h.links.new(gi.outputs[0], g.inputs["Geometry"])
    h.links.new(ln.outputs["Curve"], g.inputs["Guide Curve"])
    g.inputs["Guide From Curve"].default_value = True
    h.links.new(g.outputs["Geometry"], go.inputs[0])

    me = bpy.data.meshes.new("m")
    ob = bpy.data.objects.new("o", me)
    bpy.context.scene.collection.objects.link(ob)
    m = ob.modifiers.new("n", "NODES")
    m.node_group = h
    bpy.context.view_layer.update()
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mm = ev.to_mesh()
    if not mm or not mm.vertices:
        raise RuntimeError("EMPTY output for radius %r" % radius_m)
    ys = [v.co.y for v in mm.vertices]
    r = max(abs(min(ys)), abs(max(ys))) / MM
    ev.to_mesh_clear()
    ob.modifiers.clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    bpy.data.node_groups.remove(h)
    return r


print("  expected_mm   measured_mm   ratio")
rows = []
for param in (0.010, 0.022, 0.044):
    got = measure(param)
    exp = param / MM
    rows.append((exp, got, got / exp if exp else 0))
    print("  %10.2f   %10.2f   %5.2f" % (exp, got, got / exp if exp else 0))

linear = all(abs(r[2] - 1.0) < 0.05 for r in rows)
monotonic = rows[0][1] < rows[1][1] < rows[2][1]
print()
print("  radius == parameter at all three values : %s" % linear)
print("  monotonic in the parameter             : %s" % monotonic)
print("  RESULT %s" % ("PASS" if (linear and monotonic) else "FAIL"))
print("DONE")
