"""What do the quadrilateral modes actually produce? Measured, because the plan's cat-eye
route depends on mode semantics that are easy to assume and wrong.

For each mode: set Width=54, Height=34, Bottom Width=40, Top Width=54, Offset=6 and report
the resulting point extents - that tells us which knob moves which edge.
"""
import bpy

print("  blender %s" % bpy.app.version_string)

for mode in ("RECTANGLE", "PARALLELOGRAM", "TRAPEZOID", "KITE"):
    h = bpy.data.node_groups.new("h_" + mode, "GeometryNodeTree")
    h.is_modifier = True
    h.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    h.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    h.nodes.new("NodeGroupInput")
    go = h.nodes.new("NodeGroupOutput")
    q = h.nodes.new("GeometryNodeCurvePrimitiveQuadrilateral")
    try:
        q.mode = mode
    except Exception as exc:
        print("  %-14s mode rejected: %s" % (mode, exc))
        bpy.data.node_groups.remove(h)
        continue
    for name, val in (("Width", 0.054), ("Height", 0.034), ("Bottom Width", 0.040),
                      ("Top Width", 0.054), ("Offset", 0.006)):
        try:
            q.inputs[name].default_value = val
        except Exception:
            pass
    h.links.new(q.outputs["Curve"], go.inputs[0])

    # A curve output evaluates to an empty mesh; sweep it with a hair-thin profile so the
    # extents are the quadrilateral's own points (+-0.1 mm).
    prof = h.nodes.new("GeometryNodeCurvePrimitiveCircle")
    prof.inputs["Radius"].default_value = 0.0001
    if "Resolution" in [s.name for s in prof.inputs]:
        prof.inputs["Resolution"].default_value = 3
    sweep = h.nodes.new("GeometryNodeCurveToMesh")
    h.links.new(q.outputs["Curve"], sweep.inputs["Curve"])
    h.links.new(prof.outputs["Curve"], sweep.inputs["Profile Curve"])
    h.links.new(sweep.outputs["Mesh"], go.inputs[0])

    me = bpy.data.meshes.new("m")
    ob = bpy.data.objects.new("o", me)
    bpy.context.scene.collection.objects.link(ob)
    m = ob.modifiers.new("n", "NODES")
    m.node_group = h
    bpy.context.view_layer.update()
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mm = ev.to_mesh()
    co = [tuple(v.co) for v in mm.vertices] if mm else []
    if co:
        lo = [min(c[i] for c in co) for i in range(3)]
        hi = [max(c[i] for c in co) for i in range(3)]
        print("  %-14s %3d pts  X %7.2f..%7.2f  Y %7.2f..%7.2f"
              % (mode, len(co), lo[0] * 1000, hi[0] * 1000, lo[1] * 1000, hi[1] * 1000))
    else:
        print("  %-14s empty" % mode)
    ev.to_mesh_clear()
    ob.modifiers.clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    bpy.data.node_groups.remove(h)
print("DONE")
