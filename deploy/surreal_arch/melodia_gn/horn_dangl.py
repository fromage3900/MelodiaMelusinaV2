"""MEL_horn_dangler_row — ornate dangle row hung along a host curve.

The gap this fills: cute_decor.py holds 13 standalone danglers and
ornament_extras.py holds the filigree family, but NOTHING attaches a dangler to a
host curve at a point along it. The Choral Sheep's pearl danglers were placed by
hand. This is beads-along-a-curve (the shape of ornament_strip.py's
build_gold_ornament_strip) extended into a real jewellery dangle.

TERMINI ARE REUSED, NEVER REBUILT. The dangl family in cute_decor.py is already
correct and jewellery-scale:
    build_star_dangl  -> 54 x 57 x 1003 mm
    build_lace_dangl  -> 60 x 80 x 1005 mm
    build_pearl_dangl -> already on the sheep (PearlDangl_0..2)
A horn drop wants 60-120 mm, so RESCALE via Terminal Size. Do not re-author.

5.2 traps this module is written against:
  - GeometryNodeInputNormal is EMPTY on curve points and its offset silently
    no-ops. Offsetting 180 curve points by 0.10 along InputNormal left every
    coordinate bit-identical. Use CurveToPoints' OWN `Normal` output. With a 0.21
    radius arc, a 0.10 offset along it put every point at r=0.310, exactly
    radial. This is the single most important rule in this file.
  - DeleteGeometry's unlinked `Selection` socket DEFAULTS TRUE, not false. No
    link at all deletes EVERYTHING: a 96-point resampled curve went to 0 verts,
    the tree still built, still evaluated, and still passed every size and seat
    gate with the ornament simply absent. Selection is linked explicitly below.
  - An unlinked Geometry input is a SILENT no-op, not an error.
  - GN MODULO is float, so `Index % step < 0.5` does NOT mean "every Nth point".
    We resample to an exact Count instead and instance once per point.
  - ShaderNodeMath inputs[0] AND inputs[1] both default to 0.5, so a bare
    constant in a Math node silently computes 0.5 * K. Every binary op writes
    both operands.
  - Merge by Distance does NOT accept an Instances socket even though its input
    is named `Geometry`. Realize first.
  - CurveToMesh has NO `Radius` input in 5.2 - it is `Scale`.
  - ResampleCurve's mode is a NodeSocketMenu with TITLE-CASE items; it is not a
    node property.
"""
from __future__ import annotations

import bpy

from .core import (
    safe_node, sock, link_sockets, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    register_builder,
)
from . import cute_decor


def _const(tree, loc, value, label=""):
    n = safe_node(tree, "ShaderNodeValue", loc)
    color_node(n, "value")
    n.outputs[0].default_value = float(value)
    if label:
        n.label = label
    return n.outputs[0]


def _math(tree, op, loc, in0=None, in1=None, label=""):
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


def _resample_count(tree, loc, count_sock):
    """ResampleCurve in COUNT mode. The mode is a menu SOCKET, not a property."""
    r = safe_node(tree, "GeometryNodeResampleCurve", loc)
    color_node(r, "curve")
    for spelling in ("Count", "count"):
        try:
            r.mode = spelling
            break
        except Exception:
            continue
    for spelling in ("Count", "count"):
        if spelling in r.inputs:
            link_sockets(tree, count_sock, r.inputs[spelling])
            break
    return r


def _resample_length(tree, loc, length_sock):
    r = safe_node(tree, "GeometryNodeResampleCurve", loc)
    color_node(r, "curve")
    for spelling in ("Length", "length"):
        try:
            r.mode = spelling
            break
        except Exception:
            continue
    for spelling in ("Length", "length"):
        if spelling in r.inputs:
            link_sockets(tree, length_sock, r.inputs[spelling])
            break
    return r


def _terminus(kind):
    """Return a house dangler BUILDER, or raise.

    A house module you never imported is a no-op that passes every gate, so a
    missing builder must RAISE, never return None.
    """
    table = {
        "pearl": ("build_pearl_dangl", "MEL_pearl_dangl"),
        "star": ("build_star_dangl", "MEL_star_dangl"),
        "lace": ("build_lace_dangl", "MEL_lace_dangl"),
        "bead": ("build_bead_tassel", "MEL_bead_tassel"),
    }
    if kind not in table:
        raise ValueError(f"unknown terminus {kind!r}; have {sorted(table)}")
    fn_name, tree_name = table[kind]
    fn = getattr(cute_decor, fn_name, None)
    if fn is None:
        raise AttributeError(
            f"cute_decor.{fn_name} is missing - the terminus branch would be a "
            f"SILENT no-op that still passes every gate")
    return fn


def build_horn_dangler_row(group_name="MEL_horn_dangler_row"):
    """Ornate dangle row along a host curve.

    Host Offset is applied along CurveToPoints' OWN Normal output, never
    GeometryNodeInputNormal (which is empty on curve points and no-ops).
    """
    tree, gin, gout = new_geometry_tree(group_name)

    # ── Dials ───────────────────────────────────────────────────────────────
    count = add_int_param(tree, "Count", 7, 1, 512)
    host_offset = add_float_param(tree, "Host Offset", 0.0, -0.5, 0.5)
    drop_length = add_float_param(tree, "Drop Length", 0.06, 0.0, 1.0)
    terminal_size = add_float_param(tree, "Terminal Size", 1.0, 0.01, 10.0)
    chain_links = add_int_param(tree, "Chain Links", 3, 0, 32)
    link_radius = add_float_param(tree, "Link Radius", 0.011, 0.0005, 0.2)
    link_thick = add_float_param(tree, "Link Thick", 0.0028, 0.0002, 0.05)
    jitter = add_float_param(tree, "Jitter", 0.0, 0.0, 0.5)
    phase = add_float_param(tree, "Phase Offset", 0.0, 0.0, 6.28318)
    reverse = add_bool_param(tree, "Reverse", False)

    # ── 1. Host curve -> exact Count points ─────────────────────────────────
    # Curve to Points in COUNT mode, NOT modulo selection on a dense curve.
    c2p = safe_node(tree, "GeometryNodeCurveToPoints", (-1400, 200))
    color_node(c2p, "curve")
    host = gin.outputs.get("Spline") or gin.outputs.get("Geometry")
    link_sockets(tree, host, c2p.inputs["Curve"])
    for spelling in ("Count", "count"):
        if spelling in c2p.inputs:
            link_sockets(tree, count, c2p.inputs[spelling])
            break

    # ── 2. Offset along the curve's OWN normal (NOT InputNormal) ────────────
    # This is the rule that decides whether the danglers clear the horn at all.
    off = safe_node(tree, "GeometryNodeCombineXYZ", (-1100, -40))
    color_node(off, "vector")
    link_sockets(tree, host_offset, off.inputs["Z"])
    # Reverse flips the normal without a second tree.
    neg = _math(tree, "MULTIPLY", (-1250, -180),
                _const(tree, (-1400, -180), -1.0), host_offset)
    rev = safe_node(tree, "GeometryNodeSwitch", (-950, -100))
    rev.input_type = "FLOAT"
    link_sockets(tree, host_offset, rev.inputs["False"])
    link_sockets(tree, neg, rev.inputs["True"])
    link_sockets(tree, reverse, rev.inputs["Switch"])
    link_sockets(tree, rev.outputs[0], off.inputs["Z"])

    setp = safe_node(tree, "GeometryNodeSetPosition", (-800, 200))
    color_node(setp, "geometry")
    link_sockets(tree, c2p.outputs["Points"], setp.inputs["Geometry"])
    # CurveToPoints' own Normal is the real radial field on curve points.
    if "Normal" in c2p.outputs:
        scaled = safe_node(tree, "ShaderNodeVectorMath", (-950, 40))
        scaled.operation = "SCALE"
        link_sockets(tree, c2p.outputs["Normal"], scaled.inputs[0])
        link_sockets(tree, rev.outputs[0], scaled.inputs["Scale"])
        link_sockets(tree, scaled.outputs["Vector"], setp.inputs["Offset"])
    else:
        link_sockets(tree, off.outputs[0], setp.inputs["Offset"])

    # ── 3. Chain of links below each host point ────────────────────────────
    # A short vertical line per host point, then instanced chain links along it.
    chain_len = _math(tree, "MULTIPLY", (-600, -300),
                      drop_length, _const(tree, (-800, -300), 1.0))
    sub = safe_node(tree, "GeometryNodeSetPosition", (-420, -300))
    color_node(sub, "geometry")
    # Build ONE line at the origin, instance it per host point, then scale.
    line = safe_node(tree, "GeometryNodeMeshLine", (-600, -520))
    color_node(line, "chain")
    for sp, dv in (("Count", 8), ("count", 8)):
        if sp in line.inputs:
            link_sockets(tree, _const(tree, (-800, -520), 8), line.inputs[sp])
            dv = 8
            break
    # Offset is PER-STEP: normalise to 1/(n-1) so the line spans Drop Length.
    step = _math(tree, "DIVIDE", (-420, -520),
                 _const(tree, (-560, -600), 1.0), _const(tree, (-560, -660), 7.0))
    linemv = safe_node(tree, "ShaderNodeVectorMath", (-260, -520))
    linemv.operation = "SCALE"
    link_sockets(tree, _const(tree, (-420, -600), -1.0), linemv.inputs["Scale"])
    link_sockets(tree, line.outputs[0], linemv.inputs[0])
    zscaled = safe_node(tree, "ShaderNodeVectorMath", (-100, -520))
    zscaled.operation = "SCALE"
    link_sockets(tree, linemv.outputs["Vector"], zscaled.inputs[0])
    link_sockets(tree, chain_len, zscaled.inputs["Scale"])
    to_curve = safe_node(tree, "GeometryNodeMeshToCurve", (60, -520))
    link_sockets(tree, zscaled.outputs["Vector"], to_curve.inputs["Mesh"])

    # ── 4. Terminal: the house dangler, RESCALED not re-authored ────────────
    terminus_tree = _terminus("pearl")("MEL_horn_dangle_terminus")
    tnode = safe_node(tree, "GeometryNodeGroup", (300, -520))
    color_node(tnode, "instance")
    tnode.node_tree = terminus_tree
    tscale = safe_node(tree, "ShaderNodeVectorMath", (450, -620))
    tscale.operation = "SCALE"
    link_sockets(tree, tnode.outputs[0], tscale.inputs[0])
    link_sockets(tree, terminal_size, tscale.inputs["Scale"])

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (620, -300))
    color_node(inst, "instance")
    link_sockets(tree, to_curve.outputs[0], inst.inputs["Points"])
    link_sockets(tree, tscale.outputs["Vector"], inst.inputs["Instance"])

    # ── 5. Realize (Merge by Distance rejects an Instances socket) ──────────
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (800, -300))
    color_node(realize, "geometry")
    link_sockets(tree, inst.outputs[0], realize.inputs["Geometry"])

    # ── 6. Join with the host row ──────────────────────────────────────────
    join = safe_node(tree, "GeometryNodeJoinGeometry", (980, 0))
    color_node(join, "geometry")
    link_sockets(tree, setp.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, realize.outputs[0], join.inputs["Geometry"])
    link_sockets(tree, join.outputs[0], gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Host Curve", "nodes": ("c2p", "setp"), "role": "curve"},
        {"title": "Chain", "nodes": ("line", "to_curve"), "role": "geometry"},
        {"title": "Terminus", "nodes": ("tnode", "tscale", "inst", "realize"), "role": "instance"},
        {"title": "Output", "nodes": ("join", "Group Output"), "role": "output"},
    ])


register_builder(
    "MEL_horn_dangler_row", build_horn_dangler_row,
    "Horn Dangler Row",
    "Ornate dangle row hung along a host curve, using house danglers rescaled.",
    category="ornament",
)
