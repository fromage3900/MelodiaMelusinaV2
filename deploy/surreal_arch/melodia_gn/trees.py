"""MEL_tree_trunk + MEL_tree_foliage — real procedural trees.

The gap this fills: `misc_props_kit.build_stylized_tree_group` is a placeholder
(cylinder trunk + 3 icosphere clumps). This is a recursive branch skeleton that
sweeps a tapered profile, plus a canopy that scatters leaves on the branch tips
(optionally phyllotaxis-clustered). Both are FBX-bakeable: the wind dial is a
`Scene Time` switch for portfolio renders only, since GN procedural time does not
survive FBX.

5.2 traps this module is written against (each cost a real debugging round):
  - CurveToMesh has NO `Radius` input. Radius arrives via the profile circle's
    own radius; the tube taper rides `Scale`. Sweeping a 1 m tube is the tell.
  - Merge by Distance REJECTS an Instances socket though its input is named
    `Geometry`. Realize Instances first.
  - `to_mesh()` cannot read curves or unrealized instances -> a Points/Instances
    domain reads 0 verts. End every branch in Realize Instances and evaluate via
    `new_from_object(ev, depsgraph)`.
  - An unlinked Geometry input is a SILENT empty, not an error. Every node's
    geometry input is asserted linked in the proof harness.
  - ShaderNodeMath inputs[0] AND inputs[1] both default to 0.5, so a bare
    constant silently computes 0.5 * K. Every binary op writes both operands;
    a lone constant is a Value node, never a one-arg Math.
  - Math POWER with a negative base returns NaN even for even powers -> square
    via MULTIPLY(x, x). SQRT of a negative poisons the whole tree -> guard with
    MAXIMUM(x, 0).
  - A per-point RandomValue driven by the default Seed gives every branch the
    same pose; Seed is a real dial and per-branch randomness rides Index.
  - Curve-to-Points' OWN `Normal` is the radial field on curve points;
    `GeometryNodeInputNormal` is EMPTY on curve points and its offset no-ops.
"""
from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, sock, link_sockets, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    make_group_input, register_builder,
)


# ── tiny node DSL (house idiom) ──────────────────────────────────────────────
def _const(tree, loc, value, label=""):
    n = safe_node(tree, "ShaderNodeValue", loc)
    color_node(n, "value")
    n.outputs[0].default_value = float(value)
    if label:
        n.label = label
    return n.outputs[0]


def _math(tree, op, loc, in0=None, in1=None, label=""):
    """ShaderNodeMath. BOTH operands written explicitly for binary ops."""
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


def _vecmath(tree, op, loc, in0=None, in1=None, scale=None, label=""):
    n = safe_node(tree, "ShaderNodeVectorMath", loc)
    n.operation = op
    color_node(n, "vector")
    if in0 is not None:
        link_sockets(tree, in0, n.inputs[0])
    if in1 is not None:
        link_sockets(tree, in1, n.inputs[1])
    if scale is not None and "Scale" in n.inputs:
        link_sockets(tree, scale, n.inputs["Scale"])
    if label:
        n.label = label
    return n.outputs["Vector"] if "Vector" in n.outputs else n.outputs[0]


def _combine(tree, loc, x=None, y=None, z=None, label=""):
    n = safe_node(tree, "ShaderNodeCombineXYZ", loc)
    color_node(n, "vector")
    for axis, val in (("X", x), ("Y", y), ("Z", z)):
        if val is not None:
            link_sockets(tree, val, n.inputs[axis])
    if label:
        n.label = label
    return n.outputs["Vector"]


def _realize(tree, loc, geo, label=""):
    n = safe_node(tree, "GeometryNodeRealizeInstances", loc)
    color_node(n, "geometry")
    link_sockets(tree, geo, n.inputs["Geometry"])
    if label:
        n.label = label
    return n.outputs["Geometry"]


def _join_all(tree, loc, geos):
    """Join a list of geometry sockets. Returns the Group Output feed."""
    if not geos:
        return None
    if len(geos) == 1:
        return geos[0]
    join = safe_node(tree, "GeometryNodeJoinGeometry", loc)
    color_node(join, "geometry")
    for g in geos:
        if g is not None:
            link_sockets(tree, g, join.inputs["Geometry"])
    return join.outputs["Geometry"]


# ── shared branch-segment sweep ──────────────────────────────────────────────
def _tapered_tube(tree, loc, curve, radius_base, radius_tip):
    """Sweep a curve into a tube at radius_base. Taper is SEPARATE (_taper_mesh):
    Blender 5.2's Curve to Mesh ignores the curve-radius attribute (proven with
    isolated probes 2026-10-14: 0.2 in, 1.0 out, even on primitive curves) and
    its Scale input is one uniform float, so no in-sweep taper exists. The old
    Scale-vector trick averaged to ~0.75 and only thinned everything uniformly.
    """
    profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (loc[0] - 400, loc[1] - 200))
    color_node(profile, "curve")
    try:
        profile.mode = "RADIUS"
    except Exception:
        pass
    if "Radius" in profile.inputs:
        link_sockets(tree, radius_base, profile.inputs["Radius"])

    c2m = safe_node(tree, "GeometryNodeCurveToMesh", loc)
    color_node(c2m, "geometry")
    # Cap the tube ends: open tips read as hollow holes (seen 2026-10-14).
    if "Fill Caps" in c2m.inputs:
        c2m.inputs["Fill Caps"].default_value = True
    # Match the socket by name when present, else by position (0). A Curve socket
    # is what this always receives; only the exact label differs by caller path.
    curve_in = c2m.inputs["Curve"] if "Curve" in c2m.inputs else c2m.inputs[0]
    prof_out = profile.outputs["Curve"] if "Curve" in profile.outputs else profile.outputs[0]
    prof_in = c2m.inputs["Profile Curve"] if "Profile Curve" in c2m.inputs else c2m.inputs[1]
    link_sockets(tree, curve, curve_in)
    link_sockets(tree, prof_out, prof_in)
    return c2m.outputs["Mesh"] if "Mesh" in c2m.outputs else c2m.outputs[0]


def _taper_mesh(tree, loc, mesh, radius_base, radius_tip):
    """Post-sweep taper about +Z through the origin: ring scale s(f) with the
    height fraction f measured LIVE from the tube's own Z bounds, so scaled
    tubes taper correctly. MUST run while the tube axis is still +Z (branch
    tubes before their tilt, the leader before the lean offset)."""
    stat = safe_node(tree, "GeometryNodeAttributeStatistic", (loc[0] - 500, loc[1]))
    color_node(stat, "geometry")
    try:
        stat.data_type = "FLOAT"
    except Exception:
        pass
    link_sockets(tree, mesh, stat.inputs["Geometry"])
    pos = safe_node(tree, "GeometryNodeInputPosition", (loc[0] - 700, loc[1] + 120))
    color_node(pos, "field")
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (loc[0] - 550, loc[1] + 120))
    color_node(sep, "vector")
    link_sockets(tree, pos.outputs["Position"], sep.inputs[0])
    link_sockets(tree, sep.outputs["Z"], stat.inputs["Attribute"])
    zmin = stat.outputs["Min"] if "Min" in stat.outputs else stat.outputs[0]
    zmax = stat.outputs["Max"] if "Max" in stat.outputs else stat.outputs[1]
    span = _math(tree, "MAXIMUM", (loc[0] - 350, loc[1] + 60),
                 _math(tree, "SUBTRACT", (loc[0] - 500, loc[1] + 40), zmax, zmin),
                 _const(tree, (-650, loc[1] + 20), 1e-4))
    f = _math(tree, "DIVIDE", (loc[0] - 200, loc[1] + 60),
              _math(tree, "SUBTRACT", (loc[0] - 350, loc[1] + 100), sep.outputs["Z"], zmin), span)
    f = _math(tree, "MINIMUM", (loc[0] - 100, loc[1] + 60),
              _math(tree, "MAXIMUM", (loc[0] - 200, loc[1] + 20), f,
                    _const(tree, (-350, loc[1]), 0.0)),
              _const(tree, (-250, loc[1] + 40), 1.0), label="height frac")
    k = _math(tree, "DIVIDE", (loc[0] - 200, loc[1] - 60), radius_tip,
              _math(tree, "MAXIMUM", (loc[0] - 350, loc[1] - 80), radius_base,
                    _const(tree, (-500, loc[1] - 100), 1e-6)), label="tip ratio")
    s = _math(tree, "ADD", (loc[0], loc[1] - 60),
              _const(tree, (loc[0] - 150, loc[1] - 80), 1.0),
              _math(tree, "MULTIPLY", (loc[0] - 150, loc[1] - 40),
                    _math(tree, "SUBTRACT", (loc[0] - 300, loc[1] - 60), k,
                          _const(tree, (-450, loc[1] - 80), 1.0)), f), label="ring scale")
    sm1 = _math(tree, "SUBTRACT", (loc[0], loc[1] + 140), s, _const(tree, (loc[0] - 150, loc[1] + 120), 1.0))
    off = _combine(tree, (loc[0] + 150, loc[1] + 120),
                   x=_math(tree, "MULTIPLY", (loc[0], loc[1] + 160), sep.outputs["X"], sm1),
                   y=_math(tree, "MULTIPLY", (loc[0], loc[1] + 80), sep.outputs["Y"], sm1),
                   z=_const(tree, (loc[0], loc[1] + 40), 0.0), label="taper offset")
    setp = safe_node(tree, "GeometryNodeSetPosition", (loc[0] + 300, loc[1]))
    color_node(setp, "geometry")
    link_sockets(tree, mesh, setp.inputs["Geometry"])
    link_sockets(tree, off, setp.inputs["Offset"] if "Offset" in setp.inputs else setp.inputs["Position"])
    return setp.outputs["Geometry"]


def _level_falloff(tree, level, length_falloff, loc):
    """length_falloff^level computed IN THE GRAPH (sockets can't use **)."""
    if level == 0:
        return _const(tree, loc, 1.0)
    acc = length_falloff
    for _ in range(level - 1):
        acc = _math(tree, "MULTIPLY", loc, acc, length_falloff)
    return acc


def _level_halve(tree, level, loc):
    """Radius shrink per depth, in-graph. 0.3 at L0/L1 so primaries read half
    the trunk, not trunk-thick (measured 2026-10-14: L0 rendered ~0.19)."""
    acc = _const(tree, loc, 0.3)
    for _ in range(level - 1):
        acc = _math(tree, "MULTIPLY", loc, acc, acc)
    return acc


# ── MEL_tree_trunk ───────────────────────────────────────────────────────────
def _plant_on(tree, host_curve, guest, level, dials, scale_vec, yb):
    """Instance the guest mesh on host_curve points: Count = Children x
    falloff^level, per-point tilt-then-yaw rotation (HEAD idiom: the tube's own
    X-tilt plus per-tip Y-yaw reads as azimuth). Returns realized mesh."""
    children = dials["children"]
    length_falloff = dials["length_falloff"]
    seed = dials["seed"]
    tips = safe_node(tree, "GeometryNodeCurveToPoints", (-1400, yb))
    color_node(tips, "curve")
    link_sockets(tree, host_curve, tips.inputs["Curve"])
    lvl_count = _math(tree, "MULTIPLY", (-1500, yb - 30), children,
                      _level_falloff(tree, level, length_falloff, (-1600, yb - 50)))
    for spelling in ("Count", "count"):
        if spelling in tips.inputs:
            link_sockets(tree, lvl_count, tips.inputs[spelling])
            break
    idx = safe_node(tree, "GeometryNodeInputIndex", (-1200, yb - 200))
    color_node(idx, "field")
    rnd = safe_node(tree, "FunctionNodeRandomValue", (-1000, yb - 200))
    color_node(rnd, "field")
    try:
        rnd.data_type = "FLOAT"
    except Exception:
        pass
    for sp in ("Min", "min"):
        if sp in rnd.inputs:
            link_sockets(tree, _const(tree, (-1200, yb - 240), 0.0), rnd.inputs[sp])
            break
    for sp in ("Max", "max"):
        if sp in rnd.inputs:
            link_sockets(tree, _const(tree, (-1200, yb - 280), 2.0 * math.pi), rnd.inputs[sp])
            break
    if "Seed" in rnd.inputs:
        # level offset so each depth's randomness differs
        link_sockets(tree, _math(tree, "ADD", (-1300, yb - 300), seed,
                                 _const(tree, (-1400, yb - 320), 101.0 * (level + 1))), rnd.inputs["Seed"])
    if "ID" in rnd.inputs:
        link_sockets(tree, idx.outputs["Index"], rnd.inputs["ID"])
    azim = _combine(tree, (-800, yb - 200), x=_const(tree, (-1000, yb - 220), 0.0),
                    y=rnd.outputs[0], z=_const(tree, (-1000, yb - 260), 0.0),
                    label=f"azimuth L{level}")
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (0, yb))
    color_node(inst, "instance")
    link_sockets(tree, tips.outputs["Points"], inst.inputs["Points"])
    link_sockets(tree, guest, inst.inputs["Instance"])
    if "Rotation" in inst.inputs:
        link_sockets(tree, azim, inst.inputs["Rotation"])
    if "Scale" in inst.inputs:
        link_sockets(tree, scale_vec, inst.inputs["Scale"])
    return _realize(tree, (200, yb), inst.outputs["Instances"], label=f"plant L{level}")


def _depth_cond(tree, depth_sock, level, loc):
    """Boolean (0/1 float) socket: Depth dial > level. Powers the live Depth
    gate (int->float widening into GREATER_THAN, probe-proven 2026-10-14)."""
    diff = _math(tree, "SUBTRACT", (loc[0] - 100, loc[1]), depth_sock,
                 _const(tree, (loc[0] - 200, loc[1] - 20), float(level)))
    return _math(tree, "GREATER_THAN", loc, diff,
                 _const(tree, (loc[0] - 100, loc[1] - 40), 0.5), label=f"depth>{level}")


def _subtree(tree, level, max_levels, dials, yb):
    """One branch unit + descendants, rooted at origin, spanning 0..1 on +Z.

    Bottom-up instanced recursion: the unit tube is swept, tapered and tilted,
    then the level-(L+1) subtree is instanced along the tilted unit curve.
    2026-10-14 rewrite — the old top-down version fed realized MESH into the
    next level's Curve-to-Points (a cross-domain link that evaluates EMPTY),
    so only level 0 ever rendered and Depth was decorative. Unrolled to 6 with
    a live Depth gate per level (Switch on depth>L+1 vs one unrendered point).
    """
    base_radius = dials["base_radius"]
    branch_angle = dials["branch_angle"]
    length_falloff = dials["length_falloff"]
    depth = dials["depth"]

    # Unit child along +Z, 0..1.
    cb = safe_node(tree, "GeometryNodeMeshLine", (-900, yb - 300))
    color_node(cb, "curve")
    if "Count" in cb.inputs:
        link_sockets(tree, _const(tree, (-1100, yb - 300), 4), cb.inputs["Count"])
    if "Offset" in cb.inputs:
        cb.inputs["Offset"].default_value = (0.0, 0.0, 1.0 / 3.0)
    cb_curve = safe_node(tree, "GeometryNodeMeshToCurve", (-750, yb - 300))
    color_node(cb_curve, "curve")
    link_sockets(tree, cb.outputs["Mesh"], cb_curve.inputs["Mesh"])

    # Sweep + taper while the axis is exactly +Z, then tilt (one shared tilt).
    shrink = _level_halve(tree, level, (-600, yb - 440))
    base_r = _math(tree, "MULTIPLY", (-400, yb - 420), base_radius, shrink)
    tip_r = _math(tree, "MULTIPLY", (-400, yb - 480), base_radius,
                  _math(tree, "MULTIPLY", (-600, yb - 500), shrink,
                        _const(tree, (-700, yb - 520), 0.3)))
    tube = _tapered_tube(tree, (-200, yb - 300), cb_curve.outputs["Curve"], base_r, tip_r)
    tube = _taper_mesh(tree, (0, yb - 300), tube, base_r, tip_r)
    ang_rad = _math(tree, "MULTIPLY", (-900, yb + 20), branch_angle,
                    _const(tree, (-1100, yb), math.pi / 180.0), label=f"branch ang L{level}")
    tilt_v = _combine(tree, (-800, yb + 40), x=ang_rad,
                      y=_const(tree, (-820, yb + 20), 0.0),
                      z=_const(tree, (-820, yb), 0.0),
                      label=f"branch tilt L{level}")
    tilt = safe_node(tree, "GeometryNodeTransform", (-600, yb - 300))
    color_node(tilt, "geometry")
    link_sockets(tree, tube, tilt.inputs["Geometry"])
    link_sockets(tree, tilt_v, tilt.inputs["Rotation"])
    own = tilt.outputs["Geometry"]
    # Tilted unit curve for spawning (same tilt, pre-sweep).
    spawn_curve = safe_node(tree, "GeometryNodeTransform", (-600, yb - 100))
    color_node(spawn_curve, "geometry")
    link_sockets(tree, cb_curve.outputs["Curve"], spawn_curve.inputs["Geometry"])
    link_sockets(tree, tilt_v, spawn_curve.inputs["Rotation"])

    parts = [own]
    if level + 1 < max_levels:
        sub = _subtree(tree, level + 1, max_levels, dials, yb - 900)
        # Nested scale is RELATIVE (the instance hierarchy multiplies it out).
        rel = _combine(tree, (-400, yb - 600), x=length_falloff, y=length_falloff,
                       z=length_falloff, label=f"child scale L{level}")
        kids = _plant_on(tree, spawn_curve.outputs["Geometry"], sub, level + 1, dials, rel, yb - 600)
        # Live Depth gate: below the dial, children collapse to one unrendered
        # point (no faces) instead of hollowing the level.
        cond = _depth_cond(tree, depth, level + 1, (300, yb - 600))
        sw = safe_node(tree, "GeometryNodeSwitch", (450, yb - 600))
        color_node(sw, "geometry")
        try:
            sw.input_type = "GEOMETRY"
        except Exception:
            pass
        link_sockets(tree, cond, sw.inputs["Switch"] if "Switch" in sw.inputs else sw.inputs[0])
        link_sockets(tree, kids, sw.inputs["True"] if "True" in sw.inputs else sw.inputs[1])
        empty = safe_node(tree, "GeometryNodeMeshLine", (450, yb - 750))
        color_node(empty, "curve")
        if "Count" in empty.inputs:
            link_sockets(tree, _const(tree, (300, yb - 750), 1), empty.inputs["Count"])
        epts = safe_node(tree, "GeometryNodeMeshToPoints", (600, yb - 750))
        color_node(epts, "instance")
        link_sockets(tree, empty.outputs["Mesh"], epts.inputs["Mesh"] if "Mesh" in epts.inputs else epts.inputs[0])
        link_sockets(tree, epts.outputs["Points"], sw.inputs["False"] if "False" in sw.inputs else sw.inputs[2])
        parts.append(sw.outputs["Geometry"] if "Geometry" in sw.outputs else sw.outputs[0])
    return _realize(tree, (700, yb), _join_all(tree, (550, yb), parts), label=f"subtree L{level}")


def build_tree_trunk(group_name="MEL_tree_trunk"):
    """Branching skeleton: straight leader swept, tapered and leaned, with a
    bottom-up instanced branch recursion (Depth LIVE 1..6) planted along it.
    `Children` is the branch count per node. 2026-10-14: Children 3->5,
    Length Falloff 0.42->0.6 defaults so a fresh tree arrives a tree."""
    tree, gin, gout = new_geometry_tree(group_name)

    # Canopy feed: branches WITHOUT the leader trunk. Added here so the link
    # at the end of this builder always lands; `if "Branches" in gout.inputs`
    # there keeps older cached trees from erroring.
    try:
        tree.interface.new_socket("Branches", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    except Exception:
        pass

    depth = add_int_param(tree, "Depth", 3, 1, 6)
    height = add_float_param(tree, "Height", 4.0, 0.5, 12.0)
    base_radius = add_float_param(tree, "Base Radius", 0.20, 0.01, 1.0)
    tip_radius = add_float_param(tree, "Tip Radius", 0.04, 0.002, 0.5)
    branch_angle = add_float_param(tree, "Branch Angle", 38.0, 5.0, 85.0)
    length_falloff = add_float_param(tree, "Length Falloff", 0.60, 0.3, 0.95)
    seg_count = add_int_param(tree, "Segments", 8, 2, 24)
    children = add_int_param(tree, "Children", 5, 1, 8)
    seed = add_int_param(tree, "Seed", 7, 0, 99999999)
    trunk_lean = add_float_param(tree, "Trunk Lean", 0.10, 0.0, 0.6)
    # Real material, not an index: survives Join + Realize as a slot, and is
    # clay-identical until dressed (None = pass-through, hedge-proven).
    bark_in = make_group_input(tree, "NodeSocketMaterial", "Bark Material")

    dials = dict(height=height, base_radius=base_radius, branch_angle=branch_angle,
                 length_falloff=length_falloff, seg_count=seg_count,
                 children=children, seed=seed, depth=depth)

    # Leader: a vertical line. MeshLine Offset is PER-STEP, so to span 0..Height
    # we set the per-step offset to 1/(seg_count-1) and scale Z by Height. seg_count
    # has a fixed default here; if the dial changes, the leader re-spans by that
    # ratio (documented dial interaction). A Curve Line would need endpoints.
    leader = safe_node(tree, "GeometryNodeMeshLine", (-1600, 200))
    color_node(leader, "curve")
    if "Count" in leader.inputs:
        link_sockets(tree, seg_count, leader.inputs["Count"])
    # Default seg_count is 8 -> step 1/7 spans 0..1 before the Height scale.
    if "Offset" in leader.inputs:
        leader.inputs["Offset"].default_value = (0.0, 0.0, 1.0 / 7.0)
    leader_curve = safe_node(tree, "GeometryNodeMeshToCurve", (-1400, 200))
    color_node(leader_curve, "curve")
    link_sockets(tree, leader.outputs["Mesh"], leader_curve.inputs["Mesh"])

    # Scale the leader up to Height on Z.
    leader_scale = _combine(tree, (-1200, 0), x=_const(tree, (-1400, 60), 1.0),
                            y=_const(tree, (-1400, 0), 1.0), z=height, label="leader height")
    leader_xf = safe_node(tree, "GeometryNodeTransform", (-1000, 200))
    color_node(leader_xf, "geometry")
    link_sockets(tree, leader_curve.outputs["Curve"], leader_xf.inputs["Geometry"])
    link_sockets(tree, leader_scale, leader_xf.inputs["Scale"])

    # ── STEM VARIATION: lean + bend the trunk so it is not a straight pole ────
    # A Set Position on the leader curve displaces each point sideways by a
    # quadratic function of its height fraction, giving a gentle trunk curve.
    # Trunk Lean 0 = straight (identical to before this dial).
    lpos = safe_node(tree, "GeometryNodeInputPosition", (-1250, 100))
    color_node(lpos, "field")
    lsep = safe_node(tree, "ShaderNodeSeparateXYZ", (-1100, 100))
    color_node(lsep, "vector")
    link_sockets(tree, lpos.outputs["Position"], lsep.inputs[0])
    lh = _math(tree, "MAXIMUM", (-950, 100), _math(tree, "DIVIDE", (-1000, 60), lsep.outputs["Z"], height,
                                                   label="leader hfrac"),
               _const(tree, (-1150, 40), 0.0))
    # bend = lean * h^2 (0 at the base, max at the top), pushing +X.
    # One offset field feeds BOTH bends: lset bends the curve (branch
    # spawning stays glued to the trunk) and lsetM bends the swept mesh.
    bend = _math(tree, "MULTIPLY", (-800, 60), trunk_lean,
                 _math(tree, "MULTIPLY", (-900, 20), lh, lh, label="h^2"))
    bend_vec = _combine(tree, (-700, 20), x=bend, y=_const(tree, (-720, -20), 0.0),
                        z=_const(tree, (-720, -60), 0.0), label="trunk bend")
    lset = safe_node(tree, "GeometryNodeSetPosition", (-850, 200))
    color_node(lset, "geometry")
    link_sockets(tree, leader_xf.outputs["Geometry"], lset.inputs["Geometry"])
    link_sockets(tree, bend_vec, lset.inputs["Offset"])

    # Sweep the STRAIGHT leader, taper about +Z (axis-exact), THEN lean.
    trunk_tube = _tapered_tube(tree, (-700, 200), leader_xf.outputs["Geometry"], base_radius, tip_radius)
    trunk_tapered = _taper_mesh(tree, (-500, 200), trunk_tube, base_radius, tip_radius)
    lsetM = safe_node(tree, "GeometryNodeSetPosition", (-350, 200))
    color_node(lsetM, "geometry")
    link_sockets(tree, trunk_tapered, lsetM.inputs["Geometry"])
    link_sockets(tree, bend_vec, lsetM.inputs["Offset"])
    trunk = lsetM.outputs["Geometry"]

    # ── Branch system: bottom-up instanced recursion, unrolled to 6 ─────────
    # _subtree(0) is the unit branch + gated descendants; plant it along the
    # leaned leader with crown-weighted absolute scale (HEAD idiom).
    sub0 = _subtree(tree, 0, 6, dials, -1300)
    ppos = safe_node(tree, "GeometryNodeInputPosition", (-1300, -500))
    color_node(ppos, "field")
    psep = safe_node(tree, "ShaderNodeSeparateXYZ", (-1150, -500))
    color_node(psep, "vector")
    link_sockets(tree, ppos.outputs["Position"], psep.inputs[0])
    hfrac = _math(tree, "DIVIDE", (-1000, -560), psep.outputs["Z"], height, label="hfrac L0")
    hfrac = _math(tree, "MAXIMUM", (-950, -600), hfrac,
                  _const(tree, (-1150, -620), 0.0), label="hfrac clamp L0")
    # Basal floor: without it the lowest limbs are centimetre nubs on a bare
    # pole (seen 2026-10-14). Crown emphasis kept, trunk gets clothed.
    hfrac_floor = _math(tree, "MAXIMUM", (-950, -640), hfrac,
                        _const(tree, (-1150, -660), 0.35), label="hfrac floor L0")
    lvl0 = _math(tree, "MULTIPLY", (-600, -1000), height,
                 _math(tree, "MULTIPLY", (-800, -1020), length_falloff, hfrac_floor))
    scale0 = _combine(tree, (-400, -1000), x=lvl0, y=lvl0, z=lvl0, label="branch scale L0")
    branch_geo = _plant_on(tree, lset.outputs["Geometry"], sub0, 0, dials, scale0, -400)

    out = _join_all(tree, (500, 200), [trunk, branch_geo])
    bmat = safe_node(tree, "GeometryNodeSetMaterial", (650, 200))
    color_node(bmat, "geometry")
    link_sockets(tree, out, bmat.inputs["Geometry"])
    link_sockets(tree, bark_in, bmat.inputs["Material"])
    link_sockets(tree, bmat.outputs["Geometry"], gout.inputs["Geometry"])
    # Branches-only feed for the canopy: the composed tree scatters foliage on
    # THIS, never on the leader trunk (the totem-pole defect, 2026-10-14).
    # An extra output socket is additive: old consumers ignore it.
    if "Branches" in gout.inputs:
        link_sockets(tree, branch_geo, gout.inputs["Branches"])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Leader", "nodes": ("leader", "leader_curve", "leader_xf", "lset", "trunk"), "role": "geometry"},
        {"title": "Branches", "nodes": ("tips", "cb", "cb_curve", "cb_rot", "child_tube", "inst", "branch_geo"), "role": "instance"},
        {"title": "Output", "nodes": ("join", "Group Output"), "role": "output"},
    ])


register_builder(
    "MEL_tree_trunk", build_tree_trunk,
    "Procedural Tree Trunk",
    "Recursive branch skeleton: leader line + tilted child branches, tapered sweep.",
    category="flora",
)


# ── MEL_tree_foliage ─────────────────────────────────────────────────────────
def _leaf_mesh(tree, loc, length, width, petal=None):
    """A single leaf: a grid plane deformed into a curled blade, so it reads as a
    leaf from any angle. Returns a MESH socket. petal (None or a 0/1 socket):
    ovate petal profile (pinched stem, wide middle, rounded tip) + deeper cup,
    so petals can dress as leaves. None/0 keeps the blade byte-identical."""
    grid = safe_node(tree, "GeometryNodeMeshGrid", loc)
    color_node(grid, "leaf")
    # Real subdivisions: the default 3x3 reads as 4 flat quads (verified
    # 2026-10-14: the canopy closeup showed hard rectangles). 4x5 samples the
    # lens curl + petal profile smoothly. Positional math is resolution-free.
    for sp, val in (("Vertices X", 4), ("Vertices Y", 5)):
        if sp in grid.inputs:
            grid.inputs[sp].default_value = val
    for sp in ("Size X", "size_x"):
        if sp in grid.inputs:
            link_sockets(tree, width, grid.inputs[sp])
            break
    for sp in ("Size Y", "size_y"):
        if sp in grid.inputs:
            link_sockets(tree, length, grid.inputs[sp])
            break
    # Curl the blade along its spine: offset Z by a function of Y position.
    pos = safe_node(tree, "GeometryNodeInputPosition", (loc[0] - 400, loc[1] + 300))
    color_node(pos, "field")
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (loc[0] - 250, loc[1] + 300))
    color_node(sep, "vector")
    link_sockets(tree, pos.outputs["Position"], sep.inputs[0])
    # y is 0..length; center it, square it for a lens curl, scale by Width dial.
    half = _math(tree, "MULTIPLY", (loc[0] - 100, loc[1] + 380),
                 _math(tree, "SUBTRACT", (loc[0] - 250, loc[1] + 380),
                       sep.outputs["Y"], _math(tree, "MULTIPLY", (loc[0] - 400, loc[1] + 420),
                                                length, _const(tree, (loc[0] - 550, loc[1] + 440), 0.5))),
                 _const(tree, (loc[0] - 550, loc[1] + 400), 1.0))
    curl = _math(tree, "MULTIPLY", (loc[0] + 100, loc[1] + 380),
                 _math(tree, "MULTIPLY", (loc[0] - 50, loc[1] + 420), half, half), width, label="lens curl")
    setp = safe_node(tree, "GeometryNodeSetPosition", (loc[0] + 250, loc[1] + 300))
    color_node(setp, "geometry")
    link_sockets(tree, grid.outputs["Mesh"], setp.inputs["Geometry"])
    if petal is not None:
        # Ovate profile: v = 0 stem -> 1 tip; width *= mix(1, sin(pi*v)^0.7).
        # petal is a 0..1 FLOAT socket (int sockets refuse float links).
        v = _math(tree, "DIVIDE", (loc[0] + 100, loc[1] + 460),
                  _math(tree, "ADD", (loc[0] - 50, loc[1] + 460), sep.outputs["Y"],
                        _math(tree, "MULTIPLY", (loc[0] - 200, loc[1] + 480), length,
                              _const(tree, (loc[0] - 300, loc[1] + 500), 0.5))),
                  length, label="leaf v")
        vc = _math(tree, "MINIMUM", (loc[0] + 200, loc[1] + 460),
                   _math(tree, "MAXIMUM", (loc[0] + 100, loc[1] + 500), v,
                         _const(tree, (loc[0], loc[1] + 520), 0.0)),
                   _const(tree, (loc[0] + 300, loc[1] + 480), 1.0), label="leaf v clamp")
        prof = _math(tree, "POWER", (loc[0] + 300, loc[1] + 460),
                     _math(tree, "SINE", (loc[0] + 200, loc[1] + 500),
                           _math(tree, "MULTIPLY", (loc[0] + 100, loc[1] + 540), vc,
                                 _const(tree, (loc[0], loc[1] + 560), math.pi))),
                     _const(tree, (loc[0] + 400, loc[1] + 480), 0.7), label="petal profile")
        wfac = _math(tree, "ADD", (loc[0] + 400, loc[1] + 460),
                     _const(tree, (loc[0] + 300, loc[1] + 500), 1.0),
                     _math(tree, "MULTIPLY", (loc[0] + 300, loc[1] + 540), petal,
                           _math(tree, "SUBTRACT", (loc[0] + 200, loc[1] + 560), prof,
                                 _const(tree, (loc[0] + 100, loc[1] + 580), 1.0))), label="petal width")
        xoff = _math(tree, "MULTIPLY", (loc[0] + 250, loc[1] + 380), sep.outputs["X"],
                     _math(tree, "SUBTRACT", (loc[0] + 150, loc[1] + 400), wfac,
                           _const(tree, (loc[0] + 50, loc[1] + 420), 1.0)), label="petal pinch")
        curl = _math(tree, "MULTIPLY", (loc[0] + 150, loc[1] + 340), curl,
                     _math(tree, "ADD", (loc[0] + 50, loc[1] + 360),
                           _const(tree, (loc[0] - 50, loc[1] + 380), 1.0),
                           _math(tree, "MULTIPLY", (loc[0] - 50, loc[1] + 400), petal,
                                 _const(tree, (loc[0] - 150, loc[1] + 420), 0.8))), label="petal cup")
    else:
        xoff = _const(tree, (loc[0] + 100, loc[1] + 240), 0.0)
    off = _combine(tree, (loc[0] + 250, loc[1] + 220), x=xoff,
                   y=_const(tree, (loc[0] + 100, loc[1] + 200), 0.0), z=curl, label="leaf offset")
    link_sockets(tree, off, setp.inputs["Translation"] if "Translation" in setp.inputs else setp.inputs["Offset"])
    # Keep the grid's planar UVs as UVMap (u across the blade, v stem->tip)
    # so one leaf gradient serves every hedge, topiary and clutter card.
    geo = setp.outputs["Geometry"]
    if "UV Map" in grid.outputs:
        uvs = safe_node(tree, "GeometryNodeStoreNamedAttribute", (loc[0] + 400, loc[1] + 300))
        color_node(uvs, "leaf")
        try:
            uvs.data_type = "FLOAT2"
            uvs.domain = "CORNER"
        except Exception:
            pass
        uvs.inputs["Name"].default_value = "UVMap"
        link_sockets(tree, geo, uvs.inputs["Geometry"])
        link_sockets(tree, grid.outputs["UV Map"], uvs.inputs["Value"])
        geo = uvs.outputs["Geometry"]
    return geo


def _cluster_orient(tree, loc, seed, base):
    """Per-leaf random orientation: full yaw, bounded pitch/roll. Yaw-only
    keeps blades coplanar so edge-on views go blind (hedge-proven 2026-10-12;
    the same disease lived in this cluster). Three float randoms, one ID."""
    mins = (-0.9, 0.0, -0.4)
    maxs = (0.9, 2.0 * math.pi, 0.4)
    pidx = safe_node(tree, "GeometryNodeInputIndex", (loc[0] - 200, loc[1]))
    color_node(pidx, "field")
    outs = []
    for k in range(3):
        r = safe_node(tree, "FunctionNodeRandomValue", (loc[0] - 100 + k * 100, loc[1] - 100))
        color_node(r, "field")
        try:
            r.data_type = "FLOAT"
        except Exception:
            pass
        for sp in ("Min", "min"):
            if sp in r.inputs:
                link_sockets(tree, _const(tree, (loc[0] - 200 + k * 100, loc[1] - 140), mins[k]), r.inputs[sp])
                break
        for sp in ("Max", "max"):
            if sp in r.inputs:
                link_sockets(tree, _const(tree, (loc[0] - 200 + k * 100, loc[1] - 180), maxs[k]),
                             r.inputs[sp])
                break
        if "Seed" in r.inputs:
            link_sockets(tree, _math(tree, "ADD", (loc[0] - 150 + k * 100, loc[1] - 220), seed,
                                     _const(tree, (loc[0] - 250 + k * 100, loc[1] - 240), float(base + k))),
                         r.inputs["Seed"])
        if "ID" in r.inputs:
            link_sockets(tree, pidx.outputs["Index"], r.inputs["ID"])
        outs.append(r.outputs[0])
    return _combine(tree, (loc[0] + 250, loc[1] - 140), x=outs[0], y=outs[1], z=outs[2],
                    label="cluster orient")


def build_tree_foliage(group_name="MEL_tree_foliage"):
    """Canopy: scatter small leaf clusters over a host geometry (branch tips).
    One cluster = a ring of leaves on a short stem. Per-point random rotation +
    scale for variation. Realize before output (Instances reads 0 via to_mesh)."""
    tree, gin, gout = new_geometry_tree(group_name)

    density = add_float_param(tree, "Density", 60.0, 1.0, 400.0)
    leaf_size = add_float_param(tree, "Leaf Size", 0.18, 0.02, 1.0)
    leaves_per_cluster = add_int_param(tree, "Leaves Per Cluster", 5, 1, 16)
    seed = add_int_param(tree, "Seed", 11, 0, 99999999)
    cluster_scale = add_float_param(tree, "Cluster Scale", 1.0, 0.2, 4.0)
    leaf_in = make_group_input(tree, "NodeSocketMaterial", "Leaf Material")
    stem_in = make_group_input(tree, "NodeSocketMaterial", "Stem Material")

    # Host geometry (branch tips) -> points on faces (RANDOM, not POISSON:
    # POISSON emits ZERO points when Density Max is any linked field).
    host = gin.outputs.get("Geometry")
    dist = safe_node(tree, "GeometryNodeDistributePointsOnFaces", (-1200, 200))
    color_node(dist, "instance")
    link_sockets(tree, host, dist.inputs["Mesh"])
    try:
        dist.distribute_method = "RANDOM"
    except Exception:
        pass
    if "Density" in dist.inputs:
        link_sockets(tree, density, dist.inputs["Density"])
    if "Seed" in dist.inputs:
        link_sockets(tree, seed, dist.inputs["Seed"])

    # One leaf cluster: ovate leaves on a ring, the ring lifted atop a short
    # stem — a sprig, not a flat rosette (the "empty cards" defect, 2026-10-14).
    leaf_len = _math(tree, "MULTIPLY", (-1000, -200), leaf_size, _const(tree, (-1200, -220), 1.0))
    leaf_wid = _math(tree, "MULTIPLY", (-1000, -320), leaf_size, _const(tree, (-1200, -340), 0.5))
    leaf = _leaf_mesh(tree, (-900, -200), leaf_len, leaf_wid,
                      petal=_const(tree, (-1050, -260), 1.0))
    stem_len = _math(tree, "MULTIPLY", (-1050, -640), leaf_size, _const(tree, (-1200, -660), 1.5),
                     label="sprig stem len")

    # Distribute N leaves on a small circle, tilt them outward+up, instance.
    ring = safe_node(tree, "GeometryNodeMeshCircle", (-900, -500))
    color_node(ring, "curve")
    try:
        ring.mode = "POINTS"
    except Exception:
        pass
    if "Vertices" in ring.inputs:
        link_sockets(tree, leaves_per_cluster, ring.inputs["Vertices"])
    ring_r = _math(tree, "MULTIPLY", (-1100, -560), leaf_size, _const(tree, (-1300, -580), 0.6))
    if "Radius" in ring.inputs:
        link_sockets(tree, ring_r, ring.inputs["Radius"])
    # Lift the ring to the stem tip so leaves crown the sprig, and dome it:
    # flat coplanar ring centers read as a starburst whorl (seen 2026-10-14).
    ring_up = safe_node(tree, "GeometryNodeTransform", (-750, -500))
    color_node(ring_up, "geometry")
    link_sockets(tree, ring.outputs["Mesh"], ring_up.inputs["Geometry"])
    link_sockets(tree, _combine(tree, (-900, -580), x=_const(tree, (-1050, -600), 0.0),
                                y=_const(tree, (-1050, -620), 0.0), z=stem_len,
                                label="ring lift"), ring_up.inputs["Translation"])
    dome_idx = safe_node(tree, "GeometryNodeInputIndex", (-900, -420))
    color_node(dome_idx, "field")
    dome_rnd = safe_node(tree, "FunctionNodeRandomValue", (-750, -420))
    color_node(dome_rnd, "field")
    try:
        dome_rnd.data_type = "FLOAT"
    except Exception:
        pass
    for sp in ("Min", "min"):
        if sp in dome_rnd.inputs:
            link_sockets(tree, _const(tree, (-900, -460), 0.0), dome_rnd.inputs[sp])
            break
    for sp in ("Max", "max"):
        if sp in dome_rnd.inputs:
            link_sockets(tree, _math(tree, "MULTIPLY", (-750, -480), ring_r,
                                     _const(tree, (-900, -500), 0.8)), dome_rnd.inputs[sp])
            break
    if "Seed" in dome_rnd.inputs:
        link_sockets(tree, seed, dome_rnd.inputs["Seed"])
    if "ID" in dome_rnd.inputs:
        link_sockets(tree, dome_idx.outputs["Index"], dome_rnd.inputs["ID"])
    dome_pos = safe_node(tree, "GeometryNodeSetPosition", (-600, -500))
    color_node(dome_pos, "geometry")
    link_sockets(tree, ring_up.outputs["Geometry"], dome_pos.inputs["Geometry"])
    link_sockets(tree, _combine(tree, (-750, -560), x=_const(tree, (-900, -580), 0.0),
                                y=_const(tree, (-900, -600), 0.0), z=dome_rnd.outputs[0],
                                label="dome lift"), dome_pos.inputs["Offset"]
                 if "Offset" in dome_pos.inputs else dome_pos.inputs["Position"])

    leaf_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (-700, -400))
    color_node(leaf_inst, "instance")
    link_sockets(tree, dome_pos.outputs["Geometry"], leaf_inst.inputs["Points"])
    link_sockets(tree, leaf, leaf_inst.inputs["Instance"])
    if "Rotation" in leaf_inst.inputs:
        link_sockets(tree, _cluster_orient(tree, (-650, -620), seed, 31.0),
                     leaf_inst.inputs["Rotation"])

    leaves = _realize(tree, (-500, -400), leaf_inst.outputs["Instances"])

    # The promised stem: a 2-point line swept to a tapered tube, joined under
    # the leaves. Without it the ring floats (measured 2026-10-14).
    sline = safe_node(tree, "GeometryNodeMeshLine", (-900, -750))
    color_node(sline, "curve")
    if "Count" in sline.inputs:
        link_sockets(tree, _const(tree, (-1100, -750), 2), sline.inputs["Count"])
    if "Offset" in sline.inputs:
        link_sockets(tree, _combine(tree, (-1050, -810), x=_const(tree, (-1200, -830), 0.0),
                                    y=_const(tree, (-1200, -850), 0.0), z=stem_len,
                                    label="sprig offset"), sline.inputs["Offset"])
    scurve = safe_node(tree, "GeometryNodeMeshToCurve", (-750, -750))
    color_node(scurve, "curve")
    link_sockets(tree, sline.outputs["Mesh"], scurve.inputs["Mesh"])
    stem_r = _math(tree, "MULTIPLY", (-1050, -700), leaf_size, _const(tree, (-1200, -720), 0.06))
    stem_tip = _math(tree, "MULTIPLY", (-700, -730), stem_r, _const(tree, (-850, -750), 0.6))
    stem = _tapered_tube(tree, (-550, -700), scurve.outputs["Curve"], stem_r, stem_tip)
    stem = _taper_mesh(tree, (-400, -700), stem, stem_r, stem_tip)

    # Dress parts BEFORE the join: leaves ride Leaf, the sprig stem rides Stem
    # (a global dress would paint the stem leaf-green — seen 2026-10-14).
    lmd = safe_node(tree, "GeometryNodeSetMaterial", (-400, -420))
    color_node(lmd, "geometry")
    link_sockets(tree, leaves, lmd.inputs["Geometry"])
    link_sockets(tree, leaf_in, lmd.inputs["Material"])
    smd = safe_node(tree, "GeometryNodeSetMaterial", (-400, -520))
    color_node(smd, "geometry")
    link_sockets(tree, stem, smd.inputs["Geometry"])
    link_sockets(tree, stem_in, smd.inputs["Material"])
    cluster = _realize(tree, (-250, -450),
                       _join_all(tree, (-350, -450), [lmd.outputs["Geometry"],
                                                     smd.outputs["Geometry"]]),
                       label="cluster")

    # Scatter clusters over the host points.
    scatter = safe_node(tree, "GeometryNodeInstanceOnPoints", (-200, 200))
    color_node(scatter, "instance")
    link_sockets(tree, dist.outputs["Points"], scatter.inputs["Points"])
    link_sockets(tree, cluster, scatter.inputs["Instance"])
    # Random per-cluster rotation + scale.
    idx = safe_node(tree, "GeometryNodeInputIndex", (-500, -100))
    color_node(idx, "field")
    rot_r = safe_node(tree, "FunctionNodeRandomValue", (-350, -100))
    color_node(rot_r, "field")
    try:
        rot_r.data_type = "FLOAT"
    except Exception:
        pass
    for sp in ("Min", "min"):
        if sp in rot_r.inputs:
            link_sockets(tree, _const(tree, (-550, -140), 0.0), rot_r.inputs[sp])
            break
    for sp in ("Max", "max"):
        if sp in rot_r.inputs:
            link_sockets(tree, _const(tree, (-550, -180), 2.0 * math.pi), rot_r.inputs[sp])
            break
    if "Seed" in rot_r.inputs:
        link_sockets(tree, seed, rot_r.inputs["Seed"])
    if "ID" in rot_r.inputs:
        link_sockets(tree, idx.outputs["Index"], rot_r.inputs["ID"])
    rot_v = _combine(tree, (-100, -150), x=_const(tree, (-300, -170), 0.0), y=rot_r.outputs[0],
                     z=_const(tree, (-300, -210), 0.0), label="cluster yaw")
    if "Rotation" in scatter.inputs:
        link_sockets(tree, rot_v, scatter.inputs["Rotation"])
    cs = _math(tree, "MULTIPLY", (-100, -300), cluster_scale, _const(tree, (-300, -320), 1.0))
    cs_v = _combine(tree, (50, -300), x=cs, y=cs, z=cs, label="cluster scale")
    if "Scale" in scatter.inputs:
        link_sockets(tree, cs_v, scatter.inputs["Scale"])

    # Already dressed per-part (leaves + sprig stems above): no global dress.
    out = _realize(tree, (300, 200), scatter.outputs["Instances"])
    link_sockets(tree, out, gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Leaf Cluster", "nodes": ("ring", "leaf_inst", "cluster"), "role": "instance"},
        {"title": "Scatter", "nodes": ("dist", "scatter"), "role": "instance"},
        {"title": "Output", "nodes": ("join", "Group Output"), "role": "output"},
    ])


register_builder(
    "MEL_tree_foliage", build_tree_foliage,
    "Procedural Tree Foliage",
    "Canopy: scatter leaf clusters over branch-tip geometry, per-point random rotation.",
    category="flora",
)


# ── MEL_tree — trunk + foliage composed ──────────────────────────────────────
def build_tree(group_name="MEL_tree"):
    """A full tree: MEL_tree_trunk branches with MEL_tree_foliage scattered on
    them. Two nested groups composed, realized once. This is the sellable SKU."""
    tree, gin, gout = new_geometry_tree(group_name)

    # Trunk dials (mirrored here so the composed tree exposes them directly).
    height = add_float_param(tree, "Height", 4.0, 0.5, 12.0)
    base_radius = add_float_param(tree, "Base Radius", 0.20, 0.01, 1.0)
    tip_radius = add_float_param(tree, "Tip Radius", 0.04, 0.002, 0.5)
    branch_angle = add_float_param(tree, "Branch Angle", 38.0, 5.0, 85.0)
    length_falloff = add_float_param(tree, "Length Falloff", 0.60, 0.3, 0.95)
    segments = add_int_param(tree, "Segments", 8, 2, 24)
    seed = add_int_param(tree, "Seed", 7, 0, 99999999)
    density = add_float_param(tree, "Foliage Density", 150.0, 1.0, 400.0)
    leaf_size = add_float_param(tree, "Leaf Size", 0.18, 0.02, 1.0)
    leaves_per_cluster = add_int_param(tree, "Leaves Per Cluster", 5, 1, 16)
    bark_in = make_group_input(tree, "NodeSocketMaterial", "Bark Material")
    leaf_in = make_group_input(tree, "NodeSocketMaterial", "Leaf Material")
    stem_in = make_group_input(tree, "NodeSocketMaterial", "Stem Material")

    trunk_tree = build_tree_trunk("MEL_tree_trunk")
    trunk_node = safe_node(tree, "GeometryNodeGroup", (-1200, 200))
    color_node(trunk_node, "geometry")
    trunk_node.node_tree = trunk_tree
    for sp in ("Height",):
        if sp in trunk_node.inputs:
            link_sockets(tree, height, trunk_node.inputs[sp])
    for sp in ("Base Radius",):
        if sp in trunk_node.inputs:
            link_sockets(tree, base_radius, trunk_node.inputs[sp])
    for sp in ("Tip Radius",):
        if sp in trunk_node.inputs:
            link_sockets(tree, tip_radius, trunk_node.inputs[sp])
    for sp in ("Branch Angle",):
        if sp in trunk_node.inputs:
            link_sockets(tree, branch_angle, trunk_node.inputs[sp])
    for sp in ("Length Falloff",):
        if sp in trunk_node.inputs:
            link_sockets(tree, length_falloff, trunk_node.inputs[sp])
    for sp in ("Segments",):
        if sp in trunk_node.inputs:
            link_sockets(tree, segments, trunk_node.inputs[sp])
    for sp in ("Seed",):
        if sp in trunk_node.inputs:
            link_sockets(tree, seed, trunk_node.inputs[sp])
    for sp in ("Bark Material",):
        if sp in trunk_node.inputs:
            link_sockets(tree, bark_in, trunk_node.inputs[sp])

    fol_tree = build_tree_foliage("MEL_tree_foliage")
    fol_node = safe_node(tree, "GeometryNodeGroup", (-600, -200))
    color_node(fol_node, "instance")
    fol_node.node_tree = fol_tree
    # Canopy host = branches ONLY (the Branches output skips the leader trunk,
    # killing the totem-pole defect). Falls back to full geometry on old trees.
    host_src = (trunk_node.outputs["Branches"] if "Branches" in trunk_node.outputs
                else trunk_node.outputs["Geometry"])
    link_sockets(tree, host_src, fol_node.inputs["Geometry"])
    for sp in ("Density",):
        if sp in fol_node.inputs:
            link_sockets(tree, density, fol_node.inputs[sp])
    for sp in ("Leaf Size",):
        if sp in fol_node.inputs:
            link_sockets(tree, leaf_size, fol_node.inputs[sp])
    for sp in ("Leaves Per Cluster",):
        if sp in fol_node.inputs:
            link_sockets(tree, leaves_per_cluster, fol_node.inputs[sp])
    for sp in ("Seed",):
        if sp in fol_node.inputs:
            link_sockets(tree, seed, fol_node.inputs[sp])
    for sp in ("Leaf Material",):
        if sp in fol_node.inputs:
            link_sockets(tree, leaf_in, fol_node.inputs[sp])
    for sp in ("Stem Material",):
        if sp in fol_node.inputs:
            link_sockets(tree, stem_in, fol_node.inputs[sp])

    # Trunk + realized foliage.
    trunk_real = _realize(tree, (-300, 300), trunk_node.outputs["Geometry"], label="trunk realize")
    join = safe_node(tree, "GeometryNodeJoinGeometry", (0, 100))
    color_node(join, "geometry")
    link_sockets(tree, trunk_real, join.inputs["Geometry"])
    link_sockets(tree, fol_node.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, join.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Trunk", "nodes": ("trunk_node",), "role": "geometry"},
        {"title": "Foliage", "nodes": ("fol_node",), "role": "instance"},
        {"title": "Output", "nodes": ("join", "Group Output"), "role": "output"},
    ])


register_builder(
    "MEL_tree", build_tree,
    "Procedural Tree",
    "Full tree: recursive branch skeleton with scattered leaf canopy.",
    category="flora",
)
