"""Is the bead actually the size its parameter says?

Bead Radius defaults to 0.022 m. With the default Taper (up to 1.275x) and Jitter
(up to 1.12x) a bead could legitimately reach ~31 mm, which is close to the
+/-29.5 mm spread measured earlier. So the earlier "order of magnitude too large"
claim may be wrong. Isolate: taper and jitter off should leave exactly the
parameter value.
"""
import sys

import bpy

sys.path.insert(0, r"P:/MelodiaMelusinaV2-Laptop/deploy")
from surreal_arch.melodia_gn.core import GROUP_BUILDERS  # noqa: E402

MM = 0.001
sub = GROUP_BUILDERS["MEL_nikki_bead_string"]()
sub = sub[0] if isinstance(sub, (tuple, list)) else sub


def setp(tree, name, val):
    for it in tree.interface.items_tree:
        if getattr(it, "name", None) == name:
            it.default_value = val
            return True
    return False


def run(tag, taper, jitter, radius, droop=0.0):
    h = bpy.data.node_groups.new("h", "GeometryNodeTree")
    h.is_modifier = True
    h.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    h.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = h.nodes.new("NodeGroupInput")
    go = h.nodes.new("NodeGroupOutput")
    ln = h.nodes.new("GeometryNodeCurvePrimitiveLine")
    ln.inputs["Start"].default_value = (-0.05, 0.0, 0.0)
    ln.inputs["End"].default_value = (0.05, 0.0, 0.0)
    g = h.nodes.new("GeometryNodeGroup")
    g.node_tree = sub
    h.links.new(gi.outputs[0], g.inputs["Geometry"])
    h.links.new(ln.outputs["Curve"], g.inputs["Guide Curve"])
    g.inputs["Guide From Curve"].default_value = True
    for n, v in (("Taper", taper), ("Jitter", jitter), ("Bead Radius", radius),
                 ("Droop", droop), ("Bead Count", 14)):
        if not setp(sub, n, v):
            print("   (no param %s)" % n)
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
        print("  %-44s EMPTY" % tag)
        return
    xs = [v.co.x for v in mm.vertices]
    ys = [v.co.y for v in mm.vertices]
    # beads sit on a line along X at y=0, so the Y half-extent IS the bead radius
    print("  %-44s verts=%-5d  bead radius ~= %.2f mm   x[%.1f %.1f]"
          % (tag, len(mm.vertices), max(abs(min(ys)), abs(max(ys))) / MM,
             min(xs) / MM, max(xs) / MM))
    ev.to_mesh_clear()
    ob.modifiers.clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    for l in list(h.links):
        h.links.remove(l)
    bpy.data.node_groups.remove(h)


print("  Bead Radius parameter is 0.022 m = 22.00 mm")
run("taper=0 jitter=0  (pure parameter)", 0.0, 0.0, 0.022)
run("taper=0 jitter=0  radius=0.010", 0.0, 0.0, 0.010)
run("defaults (taper .55 jitter .12)", 0.55, 0.12, 0.022)
run("taper=0 jitter=0  radius=0.044", 0.0, 0.0, 0.044)
print("DONE")
