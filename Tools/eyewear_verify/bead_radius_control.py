"""CONTROL for 8.0 — is the bead inflation in MEL_nikki_bead, or in the measurement?

The item has been reported wrong three times, twice because a test fault was read as a
builder defect. This runs the baseline the previous session never ran:

    A  bare GeometryNodeMeshUVSphere at the same radii, measured the same way
    B  MEL_nikki_bead itself, fresh tree per value, set asserted
    C  the socket's hard range, to test whether the interface clamps the set

Reading:
    A correct + B inflated  ->  the defect is inside the bead's own chain
    A also inflated         ->  the measurement or the host is wrong, not the builder

Every case builds a FRESH tree (new_geometry_tree removes and re-creates by name, so a
reused one can silently null a tree a group node still points at).
"""
import sys

import bpy

sys.path.insert(0, r"P:/MelodiaMelusinaV2-Laptop/deploy")
from surreal_arch.melodia_gn.core import GROUP_BUILDERS  # noqa: E402

MM = 0.001
RADII = (0.010, 0.022, 0.044)


def host(node_tree=None, radius=None, tag=""):
    """Host tree holding either a group node (node_tree) or a bare sphere."""
    h = bpy.data.node_groups.new("h_" + tag, "GeometryNodeTree")
    h.is_modifier = True
    h.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    h.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    h.nodes.new("NodeGroupInput")
    go = h.nodes.new("NodeGroupOutput")

    if node_tree is None:
        n = h.nodes.new("GeometryNodeMeshUVSphere")
        out = n.outputs["Mesh"]
        sock = n.inputs["Radius"]
        sock.default_value = radius
        # RNA socket defaults are float32; 1e-12 is tighter than the storage.
        assert abs(sock.default_value - radius) < 1e-6, "bare sphere set failed"
    else:
        n = h.nodes.new("GeometryNodeGroup")
        n.node_tree = node_tree
        sock = None
        for it in node_tree.interface.items_tree:
            if getattr(it, "name", None) == "Radius" and getattr(it, "in_out", None) == "INPUT":
                sock = n.inputs[it.identifier]
        assert sock is not None, "no Radius input on " + tag
        sock.default_value = radius
        assert abs(sock.default_value - radius) < 1e-9, (
            "set did not take for %s: %r != %r" % (tag, sock.default_value, radius))
        out = n.outputs["Geometry"]

    h.links.new(out, go.inputs[0])
    return h


def measure(node_tree=None, tag="", segs=None, rings=None):
    rows = []
    for radius in RADII:
        h = host(node_tree=node_tree, radius=radius, tag=tag)
        if node_tree is None and segs is not None:
            for n in h.nodes:
                if n.bl_idname == "GeometryNodeMeshUVSphere":
                    n.inputs["Segments"].default_value = segs
                    n.inputs["Rings"].default_value = rings

        me = bpy.data.meshes.new("m")
        ob = bpy.data.objects.new("o", me)
        bpy.context.scene.collection.objects.link(ob)
        m = ob.modifiers.new("n", "NODES")
        m.node_group = h
        bpy.context.view_layer.update()
        ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mm = ev.to_mesh()
        if not mm or not mm.vertices:
            raise RuntimeError("EMPTY output for %s radius %r" % (tag, radius))
        xs = [v.co.x for v in mm.vertices]
        ys = [v.co.y for v in mm.vertices]
        zs = [v.co.z for v in mm.vertices]
        xh = max(abs(min(xs)), abs(max(xs))) / MM
        yh = max(abs(min(ys)), abs(max(ys))) / MM
        zh = max(abs(min(zs)), abs(max(zs))) / MM
        nv = len(mm.vertices)
        ev.to_mesh_clear()
        ob.modifiers.clear()
        bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.meshes.remove(me)
        bpy.data.node_groups.remove(h)
        exp = radius / MM
        rows.append((exp, xh, yh, zh, nv))
        print("  %-26s exp %8.2f   X %8.2f  Y %8.2f  Z %8.2f  verts %5d  Xratio %5.3f"
              % (tag, exp, xh, yh, zh, nv, xh / exp))
    return rows


print("  Blender %s" % bpy.app.version_string)

print()
print("A. bare GeometryNodeMeshUVSphere (control)")
bare = measure(None, "bare_sphere")

print()
print("B. MEL_nikki_bead template (fresh tree per value)")
bead = measure(GROUP_BUILDERS["MEL_nikki_bead"](), "MEL_nikki_bead")

print()
print("C. socket range on the bead's Radius param")
sub = GROUP_BUILDERS["MEL_nikki_bead"]()
sub = sub[0] if isinstance(sub, (tuple, list)) else sub
for it in sub.interface.items_tree:
    if getattr(it, "name", None) == "Radius" and getattr(it, "in_out", None) == "INPUT":
        print("  interface  default=%r  min=%r  max=%r  subtype=%r"
              % (it.default_value, getattr(it, "min_value", None),
                 getattr(it, "max_value", None), getattr(it, "subtype", None)))

h = host(node_tree=sub, radius=1.0, tag="range_probe")
for n in h.nodes:
    if n.bl_idname == "GeometryNodeGroup":
        for it in sub.interface.items_tree:
            if getattr(it, "name", None) == "Radius" and getattr(it, "in_out", None) == "INPUT":
                s = n.inputs[it.identifier]
                print("  group node  after set 1.0 -> %r  min=%r max=%r"
                      % (s.default_value, getattr(s, "min_value", None),
                         getattr(s, "max_value", None)))
bpy.data.node_groups.remove(h)

print()
bare_ok = all(abs(r[1] - r[0]) < 0.05 * r[0] for r in bare)
bead_ok = all(abs(r[1] - r[0]) < 0.05 * r[0] for r in bead)
print("  bare sphere tracks its Radius        : %s" % bare_ok)
print("  MEL_nikki_bead tracks its Radius     : %s" % bead_ok)
print()
if bare_ok and not bead_ok:
    print("  VERDICT: defect is INSIDE MEL_nikki_bead's own chain")
elif not bare_ok:
    print("  VERDICT: the bare control is ALSO wrong - suspect the measurement, not the builder")
else:
    print("  VERDICT: both correct - the fault is downstream, in the consumer/instance path")
print("DONE")
