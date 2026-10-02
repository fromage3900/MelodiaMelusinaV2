"""MEL_phyllotaxis — shared phyllotaxis spiral point generator.

The golden angle (137.5077 deg) was already authored as a design constant in all
seven brooch genomes behind `brooch_genome.py`'s portable genome pattern. That
pattern's rule is that builders MUST NOT hardcode design constants of their own,
so this module is the single GN-side authority both brooches and the Choral Sheep
consume. Authoring a second copy of the math inside sheep code would be the exact
defect the GN builder workflow warns about.

Two builders:
  MEL_phyllotaxis_spiral — an open spiral of points (diverge or converge)
  MEL_phyllotaxis_pave   — the same distribution as a FILL for gem/bead fields

Composition contract (per melodia-gn-builder-workflow):
  - sub-builders take (tree, props, ...) and return a GEOMETRY SOCKET
  - the _group wrapper owns the interface and links it
  - return `tree`, NEVER a (tree, gin, gout) triple - a triple opts the tree
    into the auto-applied Universal Music pass and grows music sockets it does
    not use.

5.2 traps this module is written against:
  - GN MODULO is float, so `Index % step < 0.5` does NOT mean "every Nth point"
    and the FRACT(Factor/step) replacement is worse (Factor/step < 1 makes FRACT
    the identity, so EVERY point passes). We never select by modulo: we resample
    to an exact Count and instance once per point.
  - ShaderNodeMath inputs[0] AND inputs[1] both default to 0.5, so a bare
    constant in a Math node silently computes 0.5 * K. Every binary op below
    writes both operands from a Value node.
  - There is no Math CLAMP in 5.x; use ShaderNodeClamp, whose input is `Value`
    and whose OUTPUT is `Result` (outputs["Value"] raises KeyError).
  - ResampleCurve's mode is a NodeSocketMenu with TITLE-CASE items
    ('Evaluated', 'Count', 'Length'); it is not a node property.
"""
from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, sock, link_sockets, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    register_builder,
)

GOLDEN_ANGLE = 137.5077


def _const(tree, loc, value, label=""):
    """A Value node. NEVER a bare-constant ShaderNodeMath (see module docstring)."""
    n = safe_node(tree, "ShaderNodeValue", loc)
    color_node(n, "value")
    n.outputs[0].default_value = float(value)
    if label:
        n.label = label
    return n.outputs[0]


def _math(tree, op, loc, in0=None, in1=None, label=""):
    """ShaderNodeMath with BOTH operands written explicitly for binary ops."""
    n = safe_node(tree, "ShaderNodeMath", loc)
    n.operation = op
    color_node(n, "math")
    if in0 is not None:
        link_sockets(tree, in0, n.inputs[0])
    if in1 is not None:
        link_sockets(tree, in1, n.inputs[1])
    if label:
        n.label = label
    return n.outputs[0]


def _build_spiral_points(tree, loc, dials, even=False):
    """Materialise the spiral as a point cloud, then to a curve.

    Uses a Distribute-on-points-free approach: Mesh Line -> Set Position with an
    Index-driven position, which keeps the count EXACT and needs no modulo.
    """
    count = dials["count"]
    line = safe_node(tree, "GeometryNodeMeshLine", loc)
    color_node(line, "spiral")
    for spelling in ("Count", "count"):
        if spelling in line.inputs:
            link_sockets(tree, dials["count"], line.inputs[spelling])
            break
    # MeshLine's default Offset is (0,0,1), so point k sits at z=k. Left alone
    # the "spiral" is a 170-unit corkscrew: the geometry measures correct in X/Y
    # and every gate passes, but the points are stacked in Z and read as one dot
    # from above. A flat spiral needs NO line offset at all.
    if "Offset" in line.inputs:
        line.inputs["Offset"].default_value = (0.0, 0.0, 0.0)

    # Per-point index -> spiral position, via Spline/Index field maths.
    idx = safe_node(tree, "GeometryNodeInputIndex", (loc[0] - 900, loc[1] + 200))
    color_node(idx, "field")

    a = dials["angle"]
    if even:
        # theta = index * (2pi / count)  ->  index * 2pi / count
        two_pi = _const(tree, (loc[0] - 1100, loc[1] + 40), 2.0 * math.pi)
        cnt = _math(tree, "DIVIDE", (loc[0] - 900, loc[1] + 40), two_pi, dials["count"])
        step = _math(tree, "MULTIPLY", (loc[0] - 700, loc[1] + 40), idx.outputs[0], cnt)
    else:
        rad = _math(tree, "MULTIPLY", (loc[0] - 900, loc[1] + 40),
                    _const(tree, (loc[0] - 1100, loc[1] + 160), math.pi / 180.0),
                    a)
        step = _math(tree, "MULTIPLY", (loc[0] - 700, loc[1] + 40), idx.outputs[0], rad)

    # radius along the spiral, honouring Inward
    r = _math(tree, "MULTIPLY", (loc[0] - 700, loc[1] - 60), idx.outputs[0], dials["radius_step"])
    # Inward negates the STEP, giving start - k*step. With start 0.0 that is
    # negative, and |negative| still grows with k - so the sign must be applied
    # to the radius itself, not to an offset. Switch the subtraction ORDER:
    #   outward: start + k*step   (grows)
    #   inward : k*step - start   (shrinks when start > 0, 0 at k=0)
    # start is the OUTER radius for an inward spiral, so the default of 0.0
    # makes an inward spiral degenerate - that is the caller's dial to set.
    r_out = _math(tree, "ADD", (loc[0] - 300, loc[1] - 300),
                  dials["radius_start"], r)
    r_in = _math(tree, "SUBTRACT", (loc[0] - 300, loc[1] - 420), r, dials["radius_start"])
    r_sw = safe_node(tree, "GeometryNodeSwitch", (loc[0] - 140, loc[1] - 340))
    r_sw.input_type = "FLOAT"
    link_sockets(tree, r_out, r_sw.inputs["False"])
    link_sockets(tree, r_in, r_sw.inputs["True"])
    link_sockets(tree, dials["inward"], r_sw.inputs["Switch"])
    radius = r_sw.outputs[0]

    # x = r cos(theta), y = r sin(theta)
    cos_t = _math(tree, "COSINE", (loc[0] - 320, loc[1] + 140), step)
    sin_t = _math(tree, "SINE", (loc[0] - 320, loc[1] - 140), step)
    x = _math(tree, "MULTIPLY", (loc[0] - 140, loc[1] + 140), radius, cos_t)
    y = _math(tree, "MULTIPLY", (loc[0] - 140, loc[1] - 140), radius, sin_t)

    pos = safe_node(tree, "ShaderNodeCombineXYZ", (loc[0] + 60, loc[1]))
    color_node(pos, "vector")
    link_sockets(tree, x, pos.inputs["X"])
    link_sockets(tree, y, pos.inputs["Y"])
    link_sockets(tree, _const(tree, (loc[0] - 140, loc[1] - 260), 0.0), pos.inputs["Z"])

    setp = safe_node(tree, "GeometryNodeSetPosition", (loc[0] + 240, loc[1]))
    color_node(setp, "geometry")
    link_sockets(tree, line.outputs[0], setp.inputs["Geometry"])
    link_sockets(tree, pos.outputs[0], setp.inputs["Offset"])

    to_pts = safe_node(tree, "GeometryNodeMeshToPoints", (loc[0] + 420, loc[1]))
    color_node(to_pts, "geometry")
    link_sockets(tree, setp.outputs["Geometry"], to_pts.inputs["Mesh"])
    return to_pts.outputs[0]


def _dials(tree, count_default=144, angle=GOLDEN_ANGLE, **over):
    d = {
        "count": add_int_param(tree, "Count", count_default, 1, 99999999),
        "angle": add_float_param(tree, "Angle", angle, 1.0, 180.0),
        "divergence": add_float_param(tree, "Divergence", 22.5, 0.0, 180.0),
        "radius_start": add_float_param(tree, "Radius Start", 0.0, 0.0, 5.0),
        "radius_step": add_float_param(tree, "Radius Step", 0.002, -0.05, 0.05),
        "inward": add_bool_param(tree, "Inward", False),
        "size_ramp": add_float_param(tree, "Size Ramp", 0.0, 0.0, 1.0),
        "size_base": add_float_param(tree, "Size Base", 0.002, 0.0001, 0.5),
        "even": add_bool_param(tree, "Even", False),
    }
    # Caller overrides must be applied to the INTERFACE DEFAULT, not the dict key
    # name - renaming a key would break every _build_spiral_points lookup.
    # NOTE: d[k] is the SOCKET returned by add_*_param, and the interface item
    # is a DIFFERENT object - look the item up by the dial's DISPLAY name.
    for k, v in over.items():
        if k not in d:
            raise KeyError(f"unknown dial override {k!r}; have {sorted(d)}")
        display = {"radius_start": "Radius Start", "radius_step": "Radius Step",
                   "count": "Count", "angle": "Angle", "inward": "Inward",
                   "even": "Even", "size_base": "Size Base"}[k]
        item = next((it for it in tree.interface.items_tree
                     if getattr(it, "item_type", "") == "SOCKET"
                     and getattr(it, "in_out", "") == "INPUT" and it.name == display), None)
        if item is None:
            raise KeyError(f"no interface socket named {display!r} for override {k!r}")
        try:
            item.default_value = v
        except Exception:
            pass
    return d


# ── Builder 1: the spiral ──────────────────────────────────────────────────

def build_phyllotaxis_spiral(group_name="MEL_phyllotaxis_spiral"):
    """Open phyllotaxis spiral as a point cloud.

    Even=false -> golden angle (organic, the sunflower register)
    Even=true  -> theta = i * 2pi/n (even pave, the brooch register)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    d = _dials(tree)
    pts = _build_spiral_points(tree, (0, 0), d, even=False)
    # Even switch: build both, pick per-evaluation (Switch picks ONE geometry for
    # the whole evaluation, which is correct here because it is a global dial,
    # not a per-point variant mix).
    even_pts = _build_spiral_points(tree, (0, -900), d, even=True)
    # MeshToPoints outputs "Points", NOT "Geometry" - feeding a GEOMETRY-typed
    # Switch yields empty with no error, which is how this tree built clean,
    # linked clean, reported 0 link failures, and still evaluated 0 verts.
    # Realise each branch to mesh FIRST so both switch inputs are the same type.
    def _as_mesh(points_sock, y):
        # Points -> vertices -> mesh. RealizeInstances does NOT convert a Points
        # cloud (it expects an Instances domain), so it passed the data through
        # and the GEOMETRY switch still saw nothing.
        p2v = safe_node(tree, "GeometryNodePointsToVertices", (700, y))
        color_node(p2v, "geometry")
        link_sockets(tree, points_sock, p2v.inputs["Points"])
        return p2v.outputs[0]

    sw = safe_node(tree, "GeometryNodeSwitch", (900, 0))
    sw.input_type = "GEOMETRY"
    link_sockets(tree, _as_mesh(pts, -160), sw.inputs["False"])
    link_sockets(tree, _as_mesh(even_pts, -1060), sw.inputs["True"])
    link_sockets(tree, d["even"], sw.inputs["Switch"])
    link_sockets(tree, sw.outputs[0], gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Spiral", "nodes": ("line", "setp", "to_pts"), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# ── Builder 2: pave ───────────────────────────────────────────────────────

def build_phyllotaxis_pave(group_name="MEL_phyllotaxis_pave"):
    """Phyllotaxis spiral pre-populated with gem instances.

    Same distribution as the spiral; adds a sized instance per point so a brooch
    pave or a horn's studded field can both read from it.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    d = _dials(tree, count_default=80, radius_start=0.255, radius_step=0.0012)

    gem = safe_node(tree, "GeometryNodeMeshIcoSphere", (-600, -300))
    color_node(gem, "instance")
    for sp, dv in (("Radius", 1.0), ("Subdivisions", 1), ("Subdivision", 1)):
        if sp in gem.inputs:
            gem.inputs[sp].default_value = dv
            break
    link_sockets(tree, d["size_base"], gem.inputs["Radius"])

    # Both distributions, then a real Even switch. Hardcoding even=False here made
    # the Even dial a silent lie: the tree carried the socket but ignored it, and
    # both renders came out identical.
    def _points_for(even, y):
        pts = _build_spiral_points(tree, (-400, y), d, even=even)
        p2v = safe_node(tree, "GeometryNodePointsToVertices", (100, y))
        color_node(p2v, "geometry")
        link_sockets(tree, pts, p2v.inputs["Points"])
        return p2v.outputs[0]

    ev_sw = safe_node(tree, "GeometryNodeSwitch", (300, 0))
    ev_sw.input_type = "GEOMETRY"
    link_sockets(tree, _points_for(False, 300), ev_sw.inputs["False"])
    link_sockets(tree, _points_for(True, -900), ev_sw.inputs["True"])
    link_sockets(tree, d["even"], ev_sw.inputs["Switch"])

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (500, 0))
    color_node(inst, "instance")
    link_sockets(tree, ev_sw.outputs[0], inst.inputs["Points"])
    link_sockets(tree, gem.outputs[0], inst.inputs["Instance"])
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (700, 0))
    color_node(realize, "geometry")
    link_sockets(tree, inst.outputs[0], realize.inputs["Geometry"])
    link_sockets(tree, realize.outputs[0], gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Pave", "nodes": ("gem", "inst", "realize"), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


register_builder(
    "MEL_phyllotaxis_spiral", build_phyllotaxis_spiral,
    "Phyllotaxis Spiral",
    "Golden-angle (or even) spiral point cloud. 137.5077 deg default.",
    category="ornament",
)
register_builder(
    "MEL_phyllotaxis_pave", build_phyllotaxis_pave,
    "Phyllotaxis Pave",
    "Phyllotaxis distribution pre-populated with gem instances for pave fields.",
    category="ornament",
)
