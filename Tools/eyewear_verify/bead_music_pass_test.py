"""8.0 causality test: is the bead inflation the universal music pass?

The control proved the bare sphere is exact and the bead is not. The chain dump showed
an undeclared post-pass: Set Position.001 fed by a radial XY offset built from
sin(Z*FreqA) + sin(atan2(Y,X)*FreqB) * Amplitude * Influence - the Universal Musical
Influence pass. This varies THAT and nothing else.

    Music Influence 0.0  -> bead must measure its own Radius exactly
    Music Influence 1.0  -> bead must reproduce the reported overscale

If those both hold, the fault is the pass's absolute amplitude (0.02 BU = 20 mm)
against a 22 mm bead, not MEL_nikki_bead's radius.
"""
import sys

import bpy

sys.path.insert(0, r"P:/MelodiaMelusinaV2-Laptop/deploy")
from surreal_arch.melodia_gn.core import GROUP_BUILDERS  # noqa: E402

MM = 0.001
CASES = ((0.010, 0.0), (0.022, 0.0), (0.044, 0.0),
         (0.022, 1.0))


def run(builder, radius, influence, tag):
    """Fresh tree per case. Bead Radius + the pass state set, both asserted."""
    sub = GROUP_BUILDERS[builder]()
    sub = sub[0] if isinstance(sub, (tuple, list)) else sub

    want = {"Bead Radius": radius, "Taper": 0.0, "Jitter": 0.0, "Droop": 0.0,
            "Bead Count": 6, "Music Influence": influence}
    got = {}
    for it in sub.interface.items_tree:
        if getattr(it, "in_out", None) != "INPUT":
            continue
        if getattr(it, "name", None) in want:
            it.default_value = want[it.name]
            got[it.name] = it.default_value
    for n, v in want.items():
        assert n in got, "param %s missing (builder %s)" % (n, builder)
        assert abs(got[n] - v) < 1e-6, "set failed for %s: %r != %r" % (n, got[n], v)

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
        raise RuntimeError("EMPTY output for %s" % tag)
    # Cord runs along X; the drop is along Y, so a bead's Y half-extent is its radius.
    ys = [v.co.y for v in mm.vertices]
    yh = max(abs(min(ys)), abs(max(ys))) / MM
    ev.to_mesh_clear()
    ob.modifiers.clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    bpy.data.node_groups.remove(h)
    exp = radius / MM
    print("  %-34s influence %.1f   expected %8.2f   measured %8.2f   ratio %5.3f"
          % (tag, influence, exp, yh, yh / exp))
    return yh, exp


print()
off = [run("MEL_nikki_bead_string", r, i, "bead_string") for r, i in CASES if i == 0.0]
on = run("MEL_nikki_bead_string", 0.022, 1.0, "bead_string (pass ON)")

exact_off = all(abs(m - e) < 0.02 * e for m, e in off)
overscale_on = abs(on[0] - on[1]) > 0.10 * on[1]
print()
print("  pass OFF -> bead radius == parameter (2%%)  : %s" % exact_off)
print("  pass ON  -> overscale reproduced           : %s" % overscale_on)
print()
if exact_off and overscale_on:
    print("  VERDICT: the universal music pass IS the 25%% - MEL_nikki_bead's radius is exact")
elif not exact_off and overscale_on:
    print("  VERDICT: the pass explains part of it; the bead radius is still off on its own")
else:
    print("  VERDICT: inconclusive - the pass does not explain the measurement")
print("DONE")
