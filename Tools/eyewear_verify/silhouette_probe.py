"""5.2 capability probe for the 8.1/8.2 work: which silhouette/select nodes exist and
what their sockets are called on THIS build. Assumed names are how a plan fails."""
import bpy

WANT = ["GeometryNodeIndexSwitch", "GeometryNodeMenuSwitch", "GeometryNodeSwitch",
        "GeometryNodeCurveArc", "GeometryNodeCurvePrimitiveBezierSegment",
        "GeometryNodeCurvePrimitiveQuadrilateral", "GeometryNodeResampleCurve",
        "GeometryNodeFilletCurve", "GeometryNodeCurveToMesh"]

print("  blender %s" % bpy.app.version_string)
g = bpy.data.node_groups.new("probe", "GeometryNodeTree")
for name in WANT:
    try:
        n = g.nodes.new(name)
    except Exception as exc:
        print("  %-44s ABSENT (%s)" % (name, exc))
        continue
    ins = []
    for s in n.inputs:
        ins.append("%s:%s" % (s.name, getattr(s, "default_value", "")))
    props = [p for p in ("data_type", "mode", "fill_type", "operation") if hasattr(n, p)]
    print("  %-44s OK" % name)
    print("      inputs : %s" % " | ".join(ins)[:300])
    for p in props:
        try:
            print("      prop   : %s = %r" % (p, getattr(n, p)))
        except Exception:
            pass
    if name == "GeometryNodeIndexSwitch":
        try:
            n.index_switch_items.new()
            n.index_switch_items.new()
            print("      after 2x new: %d inputs, names %s"
                  % (len(n.inputs), [s.name for s in n.inputs]))
        except Exception as exc:
            print("      index_switch_items.new failed: %s" % exc)
bpy.data.node_groups.remove(g)
print("DONE")
