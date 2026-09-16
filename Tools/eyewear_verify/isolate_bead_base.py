"""Clean 2x2 isolation: does the bead string need base Geometry, and does the
in-graph Guide Curve path actually work?

The earlier test set the base mesh AND the guide object at the same time, so a
green result was consistent with either route working. This varies one thing at
a time:

    base    guide-obj   guide-curve   use_curve
    ----    ---------   -----------   ---------
    none    none        none          True     -> expect empty
    none    none        curve         True     -> pure in-graph curve path
    none    curve       none          False    -> pure object path
    cube    none        curve         True     -> curve path with base geometry
"""
import sys

import bpy

sys.path.insert(0, r"P:/MelodiaMelusinaV2-Laptop/deploy")
from surreal_arch.melodia_gn.core import GROUP_BUILDERS  # noqa: E402

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
    i = names.index(name)
    coll = node.outputs if outputs else node.inputs
    return coll[i] if i < len(coll) else None


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


def run(base, obj, curve, use_curve, tag):
    h = bpy.data.node_groups.new("h", "GeometryNodeTree")
    h.is_modifier = True
    h.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    h.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = h.nodes.new("NodeGroupInput")
    go = h.nodes.new("NodeGroupOutput")
    grp = h.nodes.new("GeometryNodeGroup")
    grp.node_tree = sub

    if base == "cube":
        cube = h.nodes.new("GeometryNodeMeshCube")
        cube.inputs["Size"].default_value = (0.05, 0.02, 0.02)
        h.links.new(cube.outputs["Mesh"], gsock(grp, "Geometry"))
    else:
        h.links.new(gi.outputs[0], gsock(grp, "Geometry"))

    if obj is not None:
        try:
            gsock(grp, "Guide").default_value = obj
        except Exception as e:
            print("   (could not set Guide object: %s)" % e)
    if curve is not None:
        oi = h.nodes.new("GeometryNodeObjectInfo")
        oi.inputs["Object"].default_value = curve
        h.links.new(oi.outputs["Geometry"], gsock(grp, "Guide Curve"))
    b = gsock(grp, "Guide From Curve")
    if b is not None:
        b.default_value = use_curve

    h.links.new(gsock(grp, "Geometry", outputs=True), go.inputs[0])

    me = bpy.data.meshes.new("m")
    ob = bpy.data.objects.new("o", me)
    bpy.context.scene.collection.objects.link(ob)
    m = ob.modifiers.new("n", "NODES")
    m.node_group = h
    bpy.context.view_layer.update()
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mm = ev.to_mesh()
    n = len(mm.vertices) if mm else 0
    print("  %-38s verts=%d" % (tag, n))
    ev.to_mesh_clear()
    ob.modifiers.clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    return n


a = run("none", None, None, True, "base:none obj:none  curve:none")
b = run("none", None, gob, True, "base:none obj:none  curve:yes")
c = run("none", gob, None, False, "base:none obj:yes   curve:none")
d = run("cube", None, gob, True, "base:cube obj:none  curve:yes")

print()
results.append(("empty everything yields nothing", a == 0))
results.append(("in-graph curve path works without base geometry", b > 0))
results.append(("object path works without base geometry", c > 0))
for tag, ok in results:
    print("  %-52s %s" % (tag, "PASS" if ok else "FAIL"))
print("RESULT %s" % ("PASS" if all(o for _, o in results) else "FAIL"))
print("DONE")
