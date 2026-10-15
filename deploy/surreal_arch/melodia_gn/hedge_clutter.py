"""MEL_hedge + MEL_foliage_clutter — real procedural hedge and ground clutter.

The gap this fills: `env_extras.build_env_hedgerow` is a cube body + UV-sphere
blobs with no stem variation — it reads as a box. A hedge reads as a hedge because
of DENSITY and the trimmed outer shell: many short twigs packed along a spine,
leaf clusters on those twigs, and a flat top. Both builders reuse the tree's
primitives (twig line -> tapered tube, leaf-cluster ring) so the flora pack stays
in one visual family.

Same 5.2 traps as trees.py are respected (RANDOM not POISSON scatter, realize
before output, both Math operands explicit, tapered tube rides Scale, Delete
Geometry Selection linked explicitly).
"""
from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, sock, link_sockets, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    make_group_input, register_builder,
)
from .trees import _const, _math, _combine, _realize, _join_all, _tapered_tube, _leaf_mesh


# ── MEL_hedge ────────────────────────────────────────────────────────────────
def build_hedge(group_name="MEL_hedge", spine_k=0.5, base_k=1.0, wob_k=0.0, undergrowth=None, spine_curve_fn=None):
    """Procedural hedge: a trimmed spine with dense short twigs and leaf clusters.

    Row Length runs along X. Twig Count / Twig Length / Twig Angle drive the stem
    variation; Leaf Size / Leaves Per Cluster drive the foliage mass. Trim Height
    clips everything above it (the 'clipped hedge' silhouette) via Delete Geometry.
    spine_k sets the spine height as a fraction of Trim Height (0.5 = mid-mass,
    lower for tall wild forms so foliage reaches the ground). base_k scales the
    spine core tube (thin it for wild forms so no straight pipe shows). wob_k
    bends the spine with a gentle sine (wild only) so the core highlight is not
    ruler-straight — 0 keeps formal hedges exactly as before. spine_curve_fn
    (used by the spline topiary) builds the spine curve inside the tree from
    the tree's own dials — no scene-object references: object-fed modifier
    inputs deadlock 5.2 evaluation (proven headless+live 2026-10-12, ~0 CPU
    idle hang), so drawn-curve-follows-object is out; native curve primitives
    (arch/ring/spiral) are the working road. undergrowth clothes the core
    with leaf clusters (defaults on for wild/spline, off for formal)."""
    tree, gin, gout = new_geometry_tree(group_name)

    row_length = add_float_param(tree, "Row Length", 4.0, 0.5, 30.0)
    row_width = add_float_param(tree, "Row Width", 0.7, 0.2, 3.0)
    trim_height = add_float_param(tree, "Trim Height", 1.1, 0.3, 4.0)
    twig_count = add_int_param(tree, "Twig Count", 14, 3, 60)
    twig_length = add_float_param(tree, "Twig Length", 0.55, 0.05, 1.5)
    twig_angle = add_float_param(tree, "Twig Angle", 42.0, 10.0, 80.0)
    leaf_size = add_float_param(tree, "Leaf Size", 0.075, 0.01, 0.3)
    leaves_per_cluster = add_int_param(tree, "Leaves Per Cluster", 4, 1, 12)
    density = add_float_param(tree, "Foliage Density", 200.0, 10.0, 900.0)
    seed = add_int_param(tree, "Seed", 5, 0, 99999999)
    leaf_shape = add_float_param(tree, "Leaf Shape", 0.0, 0.0, 1.0)
    blossom_amt = add_float_param(tree, "Blossom Amount", 0.0, 0.0, 1.0)
    # Real materials (not indices): indices die in Join+Trim, materials ride
    # the join as slots. Defaults None = clay until dressed (blooms par).
    leaf_mat_in = make_group_input(tree, "NodeSocketMaterial", "Leaf Material")
    stem_mat_in = make_group_input(tree, "NodeSocketMaterial", "Stem Material")
    blossom_mat_in = make_group_input(tree, "NodeSocketMaterial", "Blossom Material")

    # ── Spine: built-in primitive curve (spline topiary) or straight row ──
    # NOTE: no scene-object references anywhere on this road (see docstring).
    if spine_curve_fn is not None:
        spine_geo = spine_curve_fn(tree, gin)
    else:
        spine = safe_node(tree, "GeometryNodeMeshLine", (-1500, 0))
        color_node(spine, "curve")
        if "Count" in spine.inputs:
            link_sockets(tree, twig_count, spine.inputs["Count"])
        if "Offset" in spine.inputs:
            spine.inputs["Offset"].default_value = (1.0, 0.0, 0.0)
        spine_curve = safe_node(tree, "GeometryNodeMeshToCurve", (-1350, 0))
        color_node(spine_curve, "curve")
        link_sockets(tree, spine.outputs["Mesh"], spine_curve.inputs["Mesh"])

        # MeshLine spans 0..(count-1) in X; scale so the last point lands on Row Length.
        scale_x = _math(tree, "DIVIDE", (-1300, -120), row_length,
                        _math(tree, "SUBTRACT", (-1450, -120), twig_count, _const(tree, (-1550, -140), 1.0)),
                        label="spine length")
        spine_xf = safe_node(tree, "GeometryNodeTransform", (-1150, 0))
        color_node(spine_xf, "geometry")
        link_sockets(tree, spine_curve.outputs["Curve"], spine_xf.inputs["Geometry"])
        link_sockets(tree, _combine(tree, (-1250, -180), x=scale_x, y=_const(tree, (-1400, -200), 1.0),
                                    z=_const(tree, (-1400, -220), 1.0), label="spine scale"),
                     spine_xf.inputs["Scale"])
        spine_geo = spine_xf.outputs["Geometry"]
        # Lift the spine to mid-height so twigs fan UPWARD from the middle of the hedge
        # instead of from the ground (a hedge's mass sits high, not along the floor).
        spine_lift = safe_node(tree, "GeometryNodeTransform", (-1000, 0))
        color_node(spine_lift, "geometry")
        link_sockets(tree, spine_geo, spine_lift.inputs["Geometry"])
        link_sockets(tree, _combine(tree, (-1150, -260), x=_const(tree, (-1300, -280), 0.0),
                                    y=_const(tree, (-1300, -300), 0.0),
                                    z=_math(tree, "MULTIPLY", (-1250, -320), trim_height,
                                            _const(tree, (-1350, -340), spine_k), label="spine lift"),
                                    label="lift offset"),
                     spine_lift.inputs["Translation"])
        spine_geo = spine_lift.outputs["Geometry"]

    # Wild-only spine wobble: gentle sine offsets in Y/Z ride the spine curve
    # BEFORE the sweep and the twig spawn, so core, twigs and foliage all
    # follow one organic line instead of a ruler.
    if wob_k > 0.0:
        pos = safe_node(tree, "GeometryNodeInputPosition", (-1350, -100))
        color_node(pos, "field")
        sep = safe_node(tree, "ShaderNodeSeparateXYZ", (-1200, -100))
        color_node(sep, "field")
        link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])
        ph1 = _math(tree, "MULTIPLY", (-1050, -60), sep.outputs["X"],
                    _const(tree, (-1150, -80), 1.3), label="wob phase")
        s1 = _math(tree, "SINE", (-950, -60), ph1, label="wob sine")
        yoff = _math(tree, "MULTIPLY", (-850, -60), s1,
                     _const(tree, (-950, -80), wob_k), label="wob y")
        ph2 = _math(tree, "MULTIPLY", (-1050, -160), sep.outputs["X"],
                    _const(tree, (-1150, -180), 0.9), label="wob phase z")
        s2 = _math(tree, "COSINE", (-950, -160), ph2, label="wob cosine")
        zoff = _math(tree, "MULTIPLY", (-850, -160), s2,
                     _const(tree, (-950, -180), wob_k * 0.4), label="wob z")
        wob = safe_node(tree, "GeometryNodeSetPosition", (-750, -100))
        color_node(wob, "geometry")
        wob.label = "spine wobble"
        link_sockets(tree, spine_geo, wob.inputs["Geometry"])
        link_sockets(tree, _combine(tree, (-800, -240), x=_const(tree, (-900, -260), 0.0),
                                    y=yoff, z=zoff, label="wob offset"),
                     wob.inputs["Offset"])
        spine_geo = wob.outputs["Geometry"]

    # Hedge body: a short tapered tube along the spine (base_k thins the core
    # for wild forms so no straight pipe shows through the foliage).
    base = _tapered_tube(tree, (-950, 0), spine_geo,
                         _math(tree, "MULTIPLY", (-1100, -120), row_width, _const(tree, (-1200, -140), 0.07 * base_k)),
                         _math(tree, "MULTIPLY", (-1100, -180), row_width, _const(tree, (-1200, -200), 0.055 * base_k)))

    # ── One unit twig (a 3-point line along +Z), tilted by Twig Angle ──────
    twig = safe_node(tree, "GeometryNodeMeshLine", (-900, -400))
    color_node(twig, "curve")
    if "Count" in twig.inputs:
        link_sockets(tree, _const(tree, (-1050, -400), 3), twig.inputs["Count"])
    if "Offset" in twig.inputs:
        twig.inputs["Offset"].default_value = (0.0, 0.0, 0.5)
    twig_curve = safe_node(tree, "GeometryNodeMeshToCurve", (-750, -400))
    color_node(twig_curve, "curve")
    link_sockets(tree, twig.outputs["Mesh"], twig_curve.inputs["Mesh"])

    ang = _math(tree, "MULTIPLY", (-800, -180), twig_angle, _const(tree, (-950, -200), math.pi / 180.0))
    twig_rot = safe_node(tree, "GeometryNodeTransform", (-600, -400))
    color_node(twig_rot, "geometry")
    link_sockets(tree, twig_curve.outputs["Curve"], twig_rot.inputs["Geometry"])
    link_sockets(tree, _combine(tree, (-700, -160), x=ang, y=_const(tree, (-720, -180), 0.0),
                                z=_const(tree, (-720, -200), 0.0), label="twig tilt"),
                 twig_rot.inputs["Rotation"])
    # Transform's geometry output is "Geometry", not "Curve"; feed that into the sweep.
    twig_tube = _tapered_tube(tree, (-400, -400), twig_rot.outputs["Geometry"],
                              _math(tree, "MULTIPLY", (-600, -520), row_width, _const(tree, (-700, -540), 0.018)),
                              _math(tree, "MULTIPLY", (-600, -580), row_width, _const(tree, (-700, -600), 0.007)))

    # ── Spawn points along the spine + instance twigs with random yaw ──────
    pts = safe_node(tree, "GeometryNodeCurveToPoints", (-1150, -300))
    color_node(pts, "curve")
    link_sockets(tree, spine_geo, pts.inputs["Curve"])
    for sp in ("Count", "count"):
        if sp in pts.inputs:
            link_sockets(tree, twig_count, pts.inputs[sp])
            break

    idx = safe_node(tree, "GeometryNodeInputIndex", (-1200, -700))
    color_node(idx, "field")
    rnd = safe_node(tree, "FunctionNodeRandomValue", (-1000, -700))
    color_node(rnd, "field")
    try:
        rnd.data_type = "FLOAT"
    except Exception:
        pass
    for sp in ("Min", "min"):
        if sp in rnd.inputs:
            link_sockets(tree, _const(tree, (-1200, -740), 0.0), rnd.inputs[sp])
            break
    for sp in ("Max", "max"):
        if sp in rnd.inputs:
            link_sockets(tree, _const(tree, (-1200, -780), 2.0 * math.pi), rnd.inputs[sp])
            break
    if "Seed" in rnd.inputs:
        link_sockets(tree, seed, rnd.inputs["Seed"])
    if "ID" in rnd.inputs:
        link_sockets(tree, idx.outputs["Index"], rnd.inputs["ID"])

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (-150, -300))
    color_node(inst, "instance")
    link_sockets(tree, pts.outputs["Points"], inst.inputs["Points"])
    link_sockets(tree, twig_tube, inst.inputs["Instance"])
    if "Rotation" in inst.inputs:
        # yaw about Z fans the X-tilted twigs upward-outward all around.
        # (Yaw about Y tumbles them into a ground skirt — verified 2026-10-12.)
        link_sockets(tree, _combine(tree, (-300, -680), x=_const(tree, (-400, -700), 0.0),
                                    y=_const(tree, (-400, -720), 0.0), z=rnd.outputs[0],
                                    label="twig yaw"), inst.inputs["Rotation"])
    rndL = safe_node(tree, "FunctionNodeRandomValue", (-200, -760))
    color_node(rndL, "field")
    try:
        rndL.data_type = "FLOAT"
    except Exception:
        pass
    for sp in ("Min", "min"):
        if sp in rndL.inputs:
            link_sockets(tree, _const(tree, (-350, -780), 0.7), rndL.inputs[sp])
            break
    for sp in ("Max", "max"):
        if sp in rndL.inputs:
            link_sockets(tree, _const(tree, (-350, -820), 1.3), rndL.inputs[sp])
            break
    if "Seed" in rndL.inputs:
        link_sockets(tree, _math(tree, "ADD", (-300, -860), seed, _const(tree, (-400, -880), 11.0)), rndL.inputs["Seed"])
    if "ID" in rndL.inputs:
        link_sockets(tree, idx.outputs["Index"], rndL.inputs["ID"])
    tllen = _math(tree, "MULTIPLY", (-150, -720), twig_length, rndL.outputs[0])
    tl = _combine(tree, (-100, -700), x=tllen, y=tllen, z=tllen, label="twig len")
    if "Scale" in inst.inputs:
        link_sockets(tree, tl, inst.inputs["Scale"])

    twigs = _realize(tree, (50, -300), inst.outputs["Instances"], label="twigs")

    # ── Leaf clusters scattered on the realized twigs (RANDOM, not POISSON) ─
    leaf_len = _math(tree, "MULTIPLY", (-900, -850), leaf_size, _const(tree, (-1000, -870), 1.0))
    leaf_wid = _math(tree, "MULTIPLY", (-900, -900), leaf_size, _const(tree, (-1000, -920), 0.55))
    leaf = _leaf_mesh(tree, (-700, -850), leaf_len, leaf_wid, petal=leaf_shape)

    ring = safe_node(tree, "GeometryNodeMeshCircle", (-700, -1000))
    color_node(ring, "curve")
    try:
        ring.mode = "POINTS"
    except Exception:
        pass
    if "Vertices" in ring.inputs:
        link_sockets(tree, leaves_per_cluster, ring.inputs["Vertices"])
    ring_r = _math(tree, "MULTIPLY", (-850, -1040), leaf_size, _const(tree, (-950, -1060), 0.5))
    if "Radius" in ring.inputs:
        link_sockets(tree, ring_r, ring.inputs["Radius"])

    leaf_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (-500, -900))
    color_node(leaf_inst, "instance")
    link_sockets(tree, ring.outputs["Mesh"], leaf_inst.inputs["Points"])
    link_sockets(tree, leaf, leaf_inst.inputs["Instance"])
    cluster = _realize(tree, (-300, -900), leaf_inst.outputs["Instances"], label="cluster")

    dist = safe_node(tree, "GeometryNodeDistributePointsOnFaces", (-100, -500))
    color_node(dist, "instance")
    link_sockets(tree, twigs, dist.inputs["Mesh"])
    try:
        dist.distribute_method = "RANDOM"
    except Exception:
        pass
    if "Density" in dist.inputs:
        link_sockets(tree, density, dist.inputs["Density"])
    if "Seed" in dist.inputs:
        link_sockets(tree, _math(tree, "ADD", (-150, -540), seed, _const(tree, (-250, -560), 2.0)), dist.inputs["Seed"])

    scatter = safe_node(tree, "GeometryNodeInstanceOnPoints", (100, -500))
    color_node(scatter, "instance")
    link_sockets(tree, dist.outputs["Points"], scatter.inputs["Points"])
    link_sockets(tree, cluster, scatter.inputs["Instance"])
    if "Rotation" in scatter.inputs:
        link_sockets(tree, _scatter_orient(tree, (-50, -650), seed, 15.0), scatter.inputs["Rotation"])
    foliage = _realize(tree, (300, -500), scatter.outputs["Instances"], label="foliage")

    # ── Blossoms: petal-shaped cards in accent (mat 1) on the twigs ──────
    # Blossom Amount 0 yields no instances, so default hedges are untouched;
    # raise it for spring. Petal profile reuses _leaf_mesh(petal=1), UVs ride
    # along for the blush gradients.
    b_len = _math(tree, "MULTIPLY", (-900, -1150), leaf_size, _const(tree, (-1000, -1170), 0.7))
    b_wid = _math(tree, "MULTIPLY", (-900, -1200), leaf_size, _const(tree, (-1000, -1220), 0.35))
    b_leaf = _leaf_mesh(tree, (-700, -1150), b_len, b_wid,
                        petal=_const(tree, (-800, -1150), 1.0))
    b_ring = safe_node(tree, "GeometryNodeMeshCircle", (-700, -1300))
    color_node(b_ring, "curve")
    try:
        b_ring.mode = "POINTS"
    except Exception:
        pass
    if "Vertices" in b_ring.inputs:
        b_ring.inputs["Vertices"].default_value = 3
    b_ring_r = _math(tree, "MULTIPLY", (-850, -1340), leaf_size, _const(tree, (-950, -1360), 0.5))
    if "Radius" in b_ring.inputs:
        link_sockets(tree, b_ring_r, b_ring.inputs["Radius"])
    b_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (-500, -1200))
    color_node(b_inst, "instance")
    link_sockets(tree, b_ring.outputs["Mesh"], b_inst.inputs["Points"])
    link_sockets(tree, b_leaf, b_inst.inputs["Instance"])
    b_cluster = _realize(tree, (-300, -1200), b_inst.outputs["Instances"], label="blossom cluster")
    b_dist = safe_node(tree, "GeometryNodeDistributePointsOnFaces", (-100, -900))
    color_node(b_dist, "instance")
    link_sockets(tree, twigs, b_dist.inputs["Mesh"])
    try:
        b_dist.distribute_method = "RANDOM"
    except Exception:
        pass
    if "Density" in b_dist.inputs:
        link_sockets(tree, _math(tree, "MULTIPLY", (-150, -940), density, blossom_amt,
                                 label="blossom density"), b_dist.inputs["Density"])
    if "Seed" in b_dist.inputs:
        link_sockets(tree, _math(tree, "ADD", (-150, -1000), seed, _const(tree, (-250, -1020), 71.0)),
                     b_dist.inputs["Seed"])
    b_scat = safe_node(tree, "GeometryNodeInstanceOnPoints", (100, -900))
    color_node(b_scat, "instance")
    link_sockets(tree, b_dist.outputs["Points"], b_scat.inputs["Points"])
    link_sockets(tree, b_cluster, b_scat.inputs["Instance"])
    if "Rotation" in b_scat.inputs:
        link_sockets(tree, _scatter_orient(tree, (-50, -1050), seed, 77.0), b_scat.inputs["Rotation"])
    blossoms = _realize(tree, (300, -900), b_scat.outputs["Instances"], label="blossoms")
    b_mat = safe_node(tree, "GeometryNodeSetMaterial", (450, -900))
    color_node(b_mat, "geometry")
    link_sockets(tree, blossoms, b_mat.inputs["Geometry"])
    link_sockets(tree, blossom_mat_in, b_mat.inputs["Material"])
    blossoms = b_mat.outputs["Geometry"]

    # ── Undergrowth (wild only): leaf clusters hugging the core tube ──
    # clothes the spine so no bare highlight shows through gaps, and breaks
    # the flat-cut bottom edge with low foliage. Formal hedges skip it so
    # their approved geometry does not change. (curve_input spline topiaries
    # opt in explicitly.)
    if undergrowth is None:
        undergrowth = (wob_k > 0.0)
    extra = []
    if undergrowth:
        dist2 = safe_node(tree, "GeometryNodeDistributePointsOnFaces", (-100, -700))
        color_node(dist2, "instance")
        link_sockets(tree, base, dist2.inputs["Mesh"])
        try:
            dist2.distribute_method = "RANDOM"
        except Exception:
            pass
        if "Density" in dist2.inputs:
            link_sockets(tree, _math(tree, "MULTIPLY", (-150, -740), density,
                                     _const(tree, (-250, -760), 0.5), label="under density"),
                         dist2.inputs["Density"])
        if "Seed" in dist2.inputs:
            link_sockets(tree, _math(tree, "ADD", (-150, -800), seed, _const(tree, (-250, -820), 23.0)),
                         dist2.inputs["Seed"])
        scatter2 = safe_node(tree, "GeometryNodeInstanceOnPoints", (100, -700))
        color_node(scatter2, "instance")
        link_sockets(tree, dist2.outputs["Points"], scatter2.inputs["Points"])
        link_sockets(tree, cluster, scatter2.inputs["Instance"])
        if "Rotation" in scatter2.inputs:
            link_sockets(tree, _scatter_orient(tree, (-50, -850), seed, 45.0), scatter2.inputs["Rotation"])
        extra = [_realize(tree, (300, -700), scatter2.outputs["Instances"], label="undergrowth")]

    # Material family: stem parts ride Stem, leaves ride Leaf, blossoms ride
    # Blossom (real materials survive Join+Trim as slots; indices do not).
    # Formal hedges gain the material path here — clay-identical until
    # dressed, and the v02 material row can finally dress them.
    def _dress(geo, mat_sock, lx, ly):
        _m = safe_node(tree, "GeometryNodeSetMaterial", (lx, ly))
        color_node(_m, "geometry")
        link_sockets(tree, geo, _m.inputs["Geometry"])
        link_sockets(tree, mat_sock, _m.inputs["Material"])
        return _m.outputs["Geometry"]

    dressed = [_dress(base, stem_mat_in, 380, -100),
               _dress(twigs, stem_mat_in, 400, -150),
               _dress(foliage, leaf_mat_in, 420, -200)]
    dressed_extra = []
    for _g in extra:
        dressed_extra.append(_dress(_g, leaf_mat_in, 440, -250))

    hedge = _join_all(tree, (500, 0), dressed + [blossoms] + dressed_extra)

    # ── Trim: delete everything above Trim Height (the clipped top) ────────
    tpos = safe_node(tree, "GeometryNodeInputPosition", (600, 200))
    color_node(tpos, "field")
    tsep = safe_node(tree, "ShaderNodeSeparateXYZ", (700, 200))
    color_node(tsep, "vector")
    link_sockets(tree, tpos.outputs["Position"], tsep.inputs[0])
    above = _math(tree, "GREATER_THAN", (800, 200), tsep.outputs["Z"], trim_height)
    trim = safe_node(tree, "GeometryNodeDeleteGeometry", (900, 200))
    color_node(trim, "geometry")
    link_sockets(tree, hedge, trim.inputs["Geometry"])
    link_sockets(tree, above, trim.inputs["Selection"])   # explicit; unlinked deletes ALL

    link_sockets(tree, trim.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Spine", "nodes": ("spine", "spine_curve", "spine_xf", "base"), "role": "geometry"},
        {"title": "Twigs", "nodes": ("pts", "twig", "twig_curve", "twig_rot", "twig_tube", "inst", "twigs"), "role": "instance"},
        {"title": "Foliage", "nodes": ("ring", "leaf_inst", "cluster", "dist", "scatter", "foliage"), "role": "instance"},
        {"title": "Trim", "nodes": ("above", "trim"), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# ── MEL_hedge_wild ─────────────────────────────────────────────────────────
def build_hedge_wild(group_name="MEL_hedge_wild"):
    """Tall unclipped hedge: the same trimmed-hedge graph as MEL_hedge, grown
    out — low spine so the up-fan starts near the ground, long twigs for
    stature. No graph fork, the dials stay live."""
    tree = build_hedge(group_name, spine_k=0.3, base_k=0.45, wob_k=0.12)
    wild = {"Row Length": 6.0, "Row Width": 1.2, "Trim Height": 2.6,
            "Twig Count": 26, "Twig Length": 1.5, "Twig Angle": 50.0,
            "Leaf Size": 0.11, "Leaves Per Cluster": 5,
            "Foliage Density": 300.0, "Seed": 11}
    try:
        for it in tree.interface.items_tree:
            if getattr(it, "item_type", "") == "SOCKET" and getattr(it, "in_out", "") == "INPUT":
                if it.name in wild:
                    it.default_value = wild[it.name]
    except Exception:
        pass
    # (No trailing SetMaterialIndex: parts carry native 2/1 indices now, so a
    # post-join index would clobber the blossom accent.)
    return tree


def _topiary_cluster(tree, loc, leaf_size, leaves_per_cluster, seed, petal=None):
    """One leaf cluster + ring (shared by ball and cone). Returns geometry."""
    leaf_len = _math(tree, "MULTIPLY", (loc[0] - 200, loc[1] - 50), leaf_size,
                     _const(tree, (loc[0] - 300, loc[1] - 70), 1.0))
    leaf_wid = _math(tree, "MULTIPLY", (loc[0] - 200, loc[1] - 100), leaf_size,
                     _const(tree, (loc[0] - 300, loc[1] - 120), 0.55))
    leaf = _leaf_mesh(tree, (loc[0], loc[1] - 50), leaf_len, leaf_wid, petal=petal)
    ring = safe_node(tree, "GeometryNodeMeshCircle", (loc[0], loc[1] - 200))
    color_node(ring, "curve")
    try:
        ring.mode = "POINTS"
    except Exception:
        pass
    if "Vertices" in ring.inputs:
        link_sockets(tree, leaves_per_cluster, ring.inputs["Vertices"])
    if "Radius" in ring.inputs:
        link_sockets(tree, _math(tree, "MULTIPLY", (loc[0] - 150, loc[1] - 240), leaf_size,
                                 _const(tree, (loc[0] - 250, loc[1] - 260), 0.5)),
                     ring.inputs["Radius"])
    leaf_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (loc[0] + 200, loc[1] - 100))
    color_node(leaf_inst, "instance")
    link_sockets(tree, ring.outputs["Mesh"], leaf_inst.inputs["Points"])
    link_sockets(tree, leaf, leaf_inst.inputs["Instance"])
    return _realize(tree, (loc[0] + 400, loc[1] - 100), leaf_inst.outputs["Instances"], label="cluster")


def _scatter_orient(tree, loc, seed, base):
    """Full 3D random orientation per scatter point. Yaw-only keeps blades
    coplanar, so edge-on views go blind (verified 2026-10-12: the wild hedge
    read as bare sticks from the side). Three float randoms, one shared ID."""
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
                link_sockets(tree, _const(tree, (loc[0] - 200 + k * 100, loc[1] - 140), 0.0), r.inputs[sp])
                break
        for sp in ("Max", "max"):
            if sp in r.inputs:
                link_sockets(tree, _const(tree, (loc[0] - 200 + k * 100, loc[1] - 180), 2.0 * math.pi),
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
                    label="scatter orient")


def _topiary_trunk(tree, loc, trunk_r, top_z):
    """Open-tube trunk buried at the base (bottom rim sits below ground)."""
    trunk = safe_node(tree, "GeometryNodeMeshCylinder", loc)
    color_node(trunk, "curve")
    if "Vertices" in trunk.inputs:
        trunk.inputs["Vertices"].default_value = 10
    if "Radius" in trunk.inputs:
        link_sockets(tree, trunk_r, trunk.inputs["Radius"])
    if "Depth" in trunk.inputs:
        link_sockets(tree, top_z, trunk.inputs["Depth"])
    tr = safe_node(tree, "GeometryNodeTransform", (loc[0] + 200, loc[1]))
    color_node(tr, "geometry")
    link_sockets(tree, trunk.outputs["Mesh"], tr.inputs["Geometry"])
    half = _math(tree, "MULTIPLY", (loc[0] + 100, loc[1] - 120), top_z,
                 _const(tree, (loc[0], loc[1] - 140), 0.5))
    link_sockets(tree, _combine(tree, (loc[0] + 100, loc[1] - 180),
                                x=_const(tree, (loc[0], loc[1] - 200), 0.0),
                                y=_const(tree, (loc[0], loc[1] - 220), 0.0),
                                z=_math(tree, "SUBTRACT", (loc[0] + 100, loc[1] - 240), half,
                                        _const(tree, (loc[0], loc[1] - 260), 0.05)),
                                label="trunk lift"),
                 tr.inputs["Translation"])
    return tr.outputs["Geometry"]


def _topiary_finish(tree, loc, group_name, trunk_geo, foliage_geo, frame_title):
    """Join trunk + foliage first, then ONE material index 2 (stem/leaf
    family). A two-input Join placed AFTER SetMaterialIndex resets indices
    to 0 when the object carries no material slots — verified headless."""
    out = _join_all(tree, (loc[0], loc[1] - 150), [trunk_geo, foliage_geo])
    mat = safe_node(tree, "GeometryNodeSetMaterialIndex", (loc[0] + 200, loc[1] - 150))
    color_node(mat, "geometry")
    link_sockets(tree, out, mat.inputs["Geometry"])
    mat.inputs["Material Index"].default_value = 2
    gout = None
    for n in tree.nodes:
        if n.type == "GROUP_OUTPUT":
            gout = n
            break
    link_sockets(tree, mat.outputs["Geometry"], gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": frame_title, "nodes": ("dist", "scatter", "foliage"), "role": "instance"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# ── MEL_topiary_ball ─────────────────────────────────────────────────────
def build_topiary_ball(group_name="MEL_topiary_ball"):
    """Clipped ball topiary: short trunk with a dense leaf-sphere crown. The
    shell is a closed UV sphere, so it stays joined under the foliage."""
    tree, gin, gout = new_geometry_tree(group_name)
    ball_r = add_float_param(tree, "Ball Radius", 0.55, 0.15, 2.0)
    crown_h = add_float_param(tree, "Crown Height", 1.15, 0.4, 4.0)
    trunk_r = add_float_param(tree, "Trunk Radius", 0.05, 0.01, 0.3)
    leaf_size = add_float_param(tree, "Leaf Size", 0.09, 0.01, 0.3)
    leaves_per_cluster = add_int_param(tree, "Leaves Per Cluster", 5, 1, 12)
    density = add_float_param(tree, "Foliage Density", 260.0, 10.0, 900.0)
    seed = add_int_param(tree, "Seed", 21, 0, 99999999)
    leaf_shape = add_float_param(tree, "Leaf Shape", 0.0, 0.0, 1.0)

    trunk_geo = _topiary_trunk(tree, (-1200, 300), trunk_r, crown_h)

    shell = safe_node(tree, "GeometryNodeMeshUVSphere", (-1100, -200))
    color_node(shell, "curve")
    if "Segments" in shell.inputs:
        shell.inputs["Segments"].default_value = 20
    if "Rings" in shell.inputs:
        shell.inputs["Rings"].default_value = 12
    if "Radius" in shell.inputs:
        shell.inputs["Radius"].default_value = 1.0
    shell_xf = safe_node(tree, "GeometryNodeTransform", (-900, -200))
    color_node(shell_xf, "geometry")
    link_sockets(tree, shell.outputs["Mesh"], shell_xf.inputs["Geometry"])
    link_sockets(tree, _combine(tree, (-1000, -260), x=ball_r, y=ball_r,
                                z=_math(tree, "MULTIPLY", (-1100, -280), ball_r,
                                        _const(tree, (-1200, -300), 0.9)), label="ball scale"),
                 shell_xf.inputs["Scale"])
    link_sockets(tree, _combine(tree, (-1000, -360), x=_const(tree, (-1100, -380), 0.0),
                                y=_const(tree, (-1100, -400), 0.0), z=crown_h, label="ball lift"),
                 shell_xf.inputs["Translation"])

    dist = safe_node(tree, "GeometryNodeDistributePointsOnFaces", (-700, -200))
    color_node(dist, "instance")
    link_sockets(tree, shell_xf.outputs["Geometry"], dist.inputs["Mesh"])
    try:
        dist.distribute_method = "RANDOM"
    except Exception:
        pass
    if "Density" in dist.inputs:
        link_sockets(tree, density, dist.inputs["Density"])
    if "Seed" in dist.inputs:
        link_sockets(tree, seed, dist.inputs["Seed"])

    cluster = _topiary_cluster(tree, (-500, -500), leaf_size, leaves_per_cluster, seed, petal=leaf_shape)
    scatter = safe_node(tree, "GeometryNodeInstanceOnPoints", (-100, -200))
    color_node(scatter, "instance")
    link_sockets(tree, dist.outputs["Points"], scatter.inputs["Points"])
    link_sockets(tree, cluster, scatter.inputs["Instance"])
    if "Rotation" in scatter.inputs:
        link_sockets(tree, _scatter_orient(tree, (-250, -350), seed, 25.0), scatter.inputs["Rotation"])
    foliage = _realize(tree, (100, -200), scatter.outputs["Instances"], label="foliage")

    body = _join_all(tree, (250, -200), [shell_xf.outputs["Geometry"], foliage])
    return _topiary_finish(tree, (450, -200), group_name, trunk_geo, body, "Ball Crown")


# ── MEL_topiary_cone ─────────────────────────────────────────────────────
def build_topiary_cone(group_name="MEL_topiary_cone"):
    """Clipped cone topiary. The cone shell is an open tube, so it feeds the
    distributor only and never joins the output (an open shell would render
    hollow); density carries the silhouette."""
    tree, gin, gout = new_geometry_tree(group_name)
    base_r = add_float_param(tree, "Base Radius", 0.5, 0.15, 2.0)
    cone_h = add_float_param(tree, "Cone Height", 1.4, 0.4, 4.0)
    crown_base = add_float_param(tree, "Crown Base", 0.6, 0.1, 3.0)
    trunk_r = add_float_param(tree, "Trunk Radius", 0.05, 0.01, 0.3)
    leaf_size = add_float_param(tree, "Leaf Size", 0.09, 0.01, 0.3)
    leaves_per_cluster = add_int_param(tree, "Leaves Per Cluster", 5, 1, 12)
    density = add_float_param(tree, "Foliage Density", 260.0, 10.0, 900.0)
    seed = add_int_param(tree, "Seed", 33, 0, 99999999)
    leaf_shape = add_float_param(tree, "Leaf Shape", 0.0, 0.0, 1.0)

    trunk_top = _math(tree, "ADD", (-1250, 340), crown_base,
                      _const(tree, (-1350, 360), 0.3))
    trunk_geo = _topiary_trunk(tree, (-1200, 300), trunk_r, trunk_top)

    shell = safe_node(tree, "GeometryNodeMeshCone", (-1100, -200))
    color_node(shell, "curve")
    if "Vertices" in shell.inputs:
        shell.inputs["Vertices"].default_value = 24
    if "Radius Bottom" in shell.inputs:
        link_sockets(tree, base_r, shell.inputs["Radius Bottom"])
    if "Depth" in shell.inputs:
        link_sockets(tree, cone_h, shell.inputs["Depth"])
    shell_xf = safe_node(tree, "GeometryNodeTransform", (-900, -200))
    color_node(shell_xf, "geometry")
    link_sockets(tree, shell.outputs["Mesh"], shell_xf.inputs["Geometry"])
    # the cone primitive grows +Z from its base (not centered): seat the base
    # at Crown Base directly — no half-height lift (verified headless).
    link_sockets(tree, _combine(tree, (-1000, -360), x=_const(tree, (-1100, -380), 0.0),
                                y=_const(tree, (-1100, -400), 0.0), z=crown_base,
                                label="cone seat"),
                 shell_xf.inputs["Translation"])

    dist = safe_node(tree, "GeometryNodeDistributePointsOnFaces", (-700, -200))
    color_node(dist, "instance")
    link_sockets(tree, shell_xf.outputs["Geometry"], dist.inputs["Mesh"])
    try:
        dist.distribute_method = "RANDOM"
    except Exception:
        pass
    if "Density" in dist.inputs:
        link_sockets(tree, density, dist.inputs["Density"])
    if "Seed" in dist.inputs:
        link_sockets(tree, _math(tree, "ADD", (-750, -240), seed,
                                 _const(tree, (-850, -260), 1.0)), dist.inputs["Seed"])

    cluster = _topiary_cluster(tree, (-500, -500), leaf_size, leaves_per_cluster, seed, petal=leaf_shape)
    scatter = safe_node(tree, "GeometryNodeInstanceOnPoints", (-100, -200))
    color_node(scatter, "instance")
    link_sockets(tree, dist.outputs["Points"], scatter.inputs["Points"])
    link_sockets(tree, cluster, scatter.inputs["Instance"])
    if "Rotation" in scatter.inputs:
        link_sockets(tree, _scatter_orient(tree, (-250, -350), seed, 35.0), scatter.inputs["Rotation"])
    foliage = _realize(tree, (100, -200), scatter.outputs["Instances"], label="foliage")
    return _topiary_finish(tree, (450, -200), group_name, trunk_geo, foliage, "Cone Crown")


register_builder(
    "MEL_hedge_wild", build_hedge_wild,
    "Wild Hedge",
    "Tall unclipped hedge: same graph as the trimmed hedge with grown-out dials.",
    category="flora",
)
register_builder(
    "MEL_topiary_ball", build_topiary_ball,
    "Topiary Ball",
    "Clipped ball topiary: trunk with a dense leaf-sphere crown.",
    category="flora",
)
register_builder(
    "MEL_topiary_cone", build_topiary_cone,
    "Topiary Cone",
    "Clipped cone topiary: trunk with a dense foliage cone.",
    category="flora",
)
register_builder(
    "MEL_hedge", build_hedge,
    "Procedural Hedge",
    "Trimmed hedge: dense spine with twigs and leaf clusters, flat top via Trim Height.",
    category="flora",
)


# ── MEL_topiary_spline ─────────────────────────────────────────────────────
def _spline_curve(tree, gin_unused=None):
    """In-tree spine curves (no scene objects): arch bezier / ring / coil,
    switched live by the Spline Shape dial. Own dials, created here."""
    shape = add_int_param(tree, "Spline Shape", 0, 0, 2)
    width = add_float_param(tree, "Arch Width", 4.0, 0.5, 12.0)
    height = add_float_param(tree, "Arch Height", 2.2, 0.5, 6.0)

    def _in(node, name):
        # 5.2 input lookup is by IDENTIFIER ("Point_1"), not display name
        # ("Point 1") — resolve by .name explicitly.
        return next(i for i in node.inputs if i.name == name)

    hw = _math(tree, "MULTIPLY", (-1900, 100), width, _const(tree, (-2000, 120), 0.5))
    nhw = _math(tree, "MULTIPLY", (-1900, 60), width, _const(tree, (-2000, 80), -0.5))
    # arch: symmetric bezier, handles at full height (peak ~= 0.75 x Height)
    bez = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (-1700, 100))
    color_node(bez, "curve")
    if "Resolution" in bez.inputs:
        bez.inputs["Resolution"].default_value = 32
    link_sockets(tree, _combine(tree, (-1850, -40), x=nhw, y=_const(tree, (-1950, -60), 0.0),
                                z=_const(tree, (-1950, -80), 0.0)), _in(bez, "Start"))
    link_sockets(tree, _combine(tree, (-1850, -140), x=nhw, y=_const(tree, (-1950, -160), 0.0),
                                z=height), _in(bez, "Start Handle"))
    link_sockets(tree, _combine(tree, (-1850, -240), x=hw, y=_const(tree, (-1950, -260), 0.0),
                                z=height), _in(bez, "End Handle"))
    link_sockets(tree, _combine(tree, (-1850, -340), x=hw, y=_const(tree, (-1950, -360), 0.0),
                                z=_const(tree, (-1950, -380), 0.0)), _in(bez, "End"))
    # ring: 3-point circle standing in XZ, centre at half height
    ring = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (-1700, -500))
    color_node(ring, "curve")
    if "Resolution" in ring.inputs:
        ring.inputs["Resolution"].default_value = 64
    rr = _math(tree, "MULTIPLY", (-1900, -560), width, _const(tree, (-2000, -580), 0.25))
    ch = _math(tree, "MULTIPLY", (-1900, -600), height, _const(tree, (-2000, -620), 0.5))
    link_sockets(tree, rr, _in(ring, "Radius"))
    link_sockets(tree, _combine(tree, (-1850, -660), x=rr, y=_const(tree, (-1950, -680), 0.0),
                                z=ch), _in(ring, "Point 1"))
    link_sockets(tree, _combine(tree, (-1850, -760), x=_math(tree, "MULTIPLY", (-1950, -780), rr,
                                                             _const(tree, (-2050, -800), -1.0)),
                                y=_const(tree, (-1950, -820), 0.0), z=ch), _in(ring, "Point 2"))
    link_sockets(tree, _combine(tree, (-1850, -860), x=_const(tree, (-1950, -880), 0.0),
                                y=_const(tree, (-1950, -900), 0.0),
                                z=_math(tree, "ADD", (-1950, -940), ch, rr)), _in(ring, "Point 3"))
    # coil: spiral up (topiary corkscrew)
    spi = safe_node(tree, "GeometryNodeCurveSpiral", (-1700, -1000))
    color_node(spi, "curve")
    if "Resolution" in spi.inputs:
        spi.inputs["Resolution"].default_value = 96
    for sp, dv in (("Rotations", 3.0), ("Start Radius", "hw"), ("End Radius", 0.05), ("Height", "height")):
        try:
            tgt = _in(spi, sp)
        except StopIteration:
            continue
        if dv == "hw":
            link_sockets(tree, hw, tgt)
        elif dv == "height":
            link_sockets(tree, height, tgt)
        else:
            tgt.default_value = dv
    # live switch: 0 arch, 1 ring, 2 coil
    eq1 = _math(tree, "COMPARE", (-1500, -500), shape, _const(tree, (-1600, -520), 1.0))
    inner = safe_node(tree, "GeometryNodeSwitch", (-1400, -500))
    color_node(inner, "geometry")
    try:
        inner.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, eq1, _in(inner, "Switch"))
    link_sockets(tree, ring.outputs["Curve"], _in(inner, "False"))
    link_sockets(tree, spi.outputs["Curve"], _in(inner, "True"))
    eq0 = _math(tree, "COMPARE", (-1500, 100), shape, _const(tree, (-1600, 120), 0.0))
    outer = safe_node(tree, "GeometryNodeSwitch", (-1300, 100))
    color_node(outer, "geometry")
    try:
        outer.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, eq0, _in(outer, "Switch"))
    link_sockets(tree, bez.outputs["Curve"], _in(outer, "False"))
    link_sockets(tree, inner.outputs["Geometry"] if "Geometry" in inner.outputs else inner.outputs[0],
                 _in(outer, "True"))
    return outer.outputs["Geometry"] if "Geometry" in outer.outputs else outer.outputs[0]


def build_topiary_spline(group_name="MEL_topiary_spline"):
    """Topiary grown along a BUILT-IN curve: archway, ring, or coil (Spline
    Shape dial), sized by Arch Width/Height. Same hedge graph — twigs, petal
    leaves, blossoms, undergrowth — on a curve that needs no scene object."""
    tree = build_hedge(group_name, spine_k=0.0, base_k=0.6, wob_k=0.0,
                       undergrowth=True, spine_curve_fn=_spline_curve)
    arch = {"Row Width": 0.5, "Trim Height": 3.5,
            "Twig Count": 40, "Twig Length": 0.6, "Twig Angle": 45.0,
            "Leaf Size": 0.09, "Leaves Per Cluster": 5,
            "Foliage Density": 500.0, "Leaf Shape": 1, "Blossom Amount": 0.6,
            "Seed": 21}
    try:
        for it in tree.interface.items_tree:
            if getattr(it, "item_type", "") == "SOCKET" and getattr(it, "in_out", "") == "INPUT":
                if it.name in arch:
                    it.default_value = arch[it.name]
    except Exception:
        pass
    # (No trailing SetMaterialIndex: parts carry native 2/1 indices now.)
    return tree


register_builder(
    "MEL_topiary_spline", build_topiary_spline,
    "Spline Topiary",
    "Topiary along a drawn curve: archways, spirals, rings from one graph.",
    category="flora",
)


# ── MEL_foliage_clutter ──────────────────────────────────────────────────────
def build_foliage_clutter(group_name="MEL_foliage_clutter"):
    """Scatter leaf clusters + optional twiglets across a host surface (Geometry input).

    Fills loose ends: tufts and small green clutter. Per-point random rotation and
    scale for variation; Height Mask thins the clutter toward the top of the host
    so it reads as ground cover rather than a uniform shell (0 = no masking).
    """
    tree, gin, gout = new_geometry_tree(group_name)

    density = add_float_param(tree, "Density", 90.0, 1.0, 800.0)
    leaf_size = add_float_param(tree, "Leaf Size", 0.14, 0.01, 0.6)
    leaves_per_cluster = add_int_param(tree, "Leaves Per Cluster", 5, 1, 16)
    twiglets = add_int_param(tree, "Twiglets", 0, 0, 1)
    scale_var = add_float_param(tree, "Scale Variation", 0.6, 0.0, 1.0)
    height_mask = add_float_param(tree, "Height Mask", 0.0, 0.0, 1.0)
    seed = add_int_param(tree, "Seed", 17, 0, 99999999)
    leaf_shape = add_float_param(tree, "Leaf Shape", 0.0, 0.0, 1.0)

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

    # Optional height mask: keep points near the base, thin them near the top.
    if "Selection" in dist.inputs and height_mask is not None:
        hpos = safe_node(tree, "GeometryNodeInputPosition", (-1250, -100))
        color_node(hpos, "field")
        hsep = safe_node(tree, "ShaderNodeSeparateXYZ", (-1100, -100))
        color_node(hsep, "vector")
        link_sockets(tree, hpos.outputs["Position"], hsep.inputs[0])
        # keep = 1 - height_mask * z/(z+1)  -> 1 at ground, decays upward
        zn = _math(tree, "DIVIDE", (-950, -100), hsep.outputs["Z"],
                   _math(tree, "ADD", (-1050, -160), hsep.outputs["Z"], _const(tree, (-1150, -180), 1.0)))
        keep = _math(tree, "SUBTRACT", (-800, -140), _const(tree, (-900, -160), 1.0),
                     _math(tree, "MULTIPLY", (-850, -200), height_mask, zn))
        link_sockets(tree, _math(tree, "GREATER_THAN", (-650, -140), keep,
                                 _const(tree, (-750, -160), 0.15)), dist.inputs["Selection"])

    # Leaf cluster ring (same family as tree canopy).
    leaf_len = _math(tree, "MULTIPLY", (-1000, -300), leaf_size, _const(tree, (-1100, -320), 1.0))
    leaf_wid = _math(tree, "MULTIPLY", (-1000, -400), leaf_size, _const(tree, (-1100, -420), 0.55))
    leaf = _leaf_mesh(tree, (-800, -300), leaf_len, leaf_wid, petal=leaf_shape)

    ring = safe_node(tree, "GeometryNodeMeshCircle", (-800, -500))
    color_node(ring, "curve")
    try:
        ring.mode = "POINTS"
    except Exception:
        pass
    if "Vertices" in ring.inputs:
        link_sockets(tree, leaves_per_cluster, ring.inputs["Vertices"])
    ring_r = _math(tree, "MULTIPLY", (-950, -520), leaf_size, _const(tree, (-1050, -540), 0.5))
    if "Radius" in ring.inputs:
        link_sockets(tree, ring_r, ring.inputs["Radius"])

    leaf_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (-600, -400))
    color_node(leaf_inst, "instance")
    link_sockets(tree, ring.outputs["Mesh"], leaf_inst.inputs["Points"])
    link_sockets(tree, leaf, leaf_inst.inputs["Instance"])
    cluster = _realize(tree, (-400, -400), leaf_inst.outputs["Instances"], label="cluster")

    # Per-point random rotation + scale.
    pidx = safe_node(tree, "GeometryNodeInputIndex", (-500, 0))
    color_node(pidx, "field")
    rrot = safe_node(tree, "FunctionNodeRandomValue", (-350, 0))
    color_node(rrot, "field")
    try:
        rrot.data_type = "FLOAT"
    except Exception:
        pass
    for sp in ("Min", "min"):
        if sp in rrot.inputs:
            link_sockets(tree, _const(tree, (-500, -40), 0.0), rrot.inputs[sp])
            break
    for sp in ("Max", "max"):
        if sp in rrot.inputs:
            link_sockets(tree, _const(tree, (-500, -80), 2.0 * math.pi), rrot.inputs[sp])
            break
    if "Seed" in rrot.inputs:
        link_sockets(tree, _math(tree, "ADD", (-600, -120), seed, _const(tree, (-700, -140), 3.0)), rrot.inputs["Seed"])
    if "ID" in rrot.inputs:
        link_sockets(tree, pidx.outputs["Index"], rrot.inputs["ID"])

    rscale = safe_node(tree, "FunctionNodeRandomValue", (-350, -200))
    color_node(rscale, "field")
    try:
        rscale.data_type = "FLOAT"
    except Exception:
        pass
    for sp in ("Min", "min"):
        if sp in rscale.inputs:
            link_sockets(tree, _math(tree, "SUBTRACT", (-500, -240), _const(tree, (-600, -260), 1.0), scale_var), rscale.inputs[sp])
            break
    for sp in ("Max", "max"):
        if sp in rscale.inputs:
            link_sockets(tree, _math(tree, "ADD", (-500, -280), _const(tree, (-600, -300), 1.0), scale_var), rscale.inputs[sp])
            break
    if "Seed" in rscale.inputs:
        link_sockets(tree, _math(tree, "ADD", (-600, -320), seed, _const(tree, (-700, -340), 9.0)), rscale.inputs["Seed"])
    if "ID" in rscale.inputs:
        link_sockets(tree, pidx.outputs["Index"], rscale.inputs["ID"])

    scatter = safe_node(tree, "GeometryNodeInstanceOnPoints", (-100, 200))
    color_node(scatter, "instance")
    link_sockets(tree, dist.outputs["Points"], scatter.inputs["Points"])
    link_sockets(tree, cluster, scatter.inputs["Instance"])
    if "Rotation" in scatter.inputs:
        link_sockets(tree, _combine(tree, (-150, -40), x=_const(tree, (-250, -60), 0.0),
                                    y=rrot.outputs[0], z=_const(tree, (-250, -100), 0.0),
                                    label="clutter yaw"), scatter.inputs["Rotation"])
    if "Scale" in scatter.inputs:
        sv = _combine(tree, (-150, -240), x=rscale.outputs[0], y=rscale.outputs[0],
                      z=rscale.outputs[0], label="clutter scale")
        link_sockets(tree, sv, scatter.inputs["Scale"])

    out = _realize(tree, (150, 200), scatter.outputs["Instances"], label="leaves realized")
    link_sockets(tree, out, gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Distribute", "nodes": ("dist",), "role": "instance"},
        {"title": "Leaf Cluster", "nodes": ("ring", "leaf_inst", "cluster"), "role": "instance"},
        {"title": "Scatter", "nodes": ("scatter",), "role": "instance"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


register_builder(
    "MEL_foliage_clutter", build_foliage_clutter,
    "Foliage Clutter",
    "Scatter leaf clusters over a host surface to fill loose ends.",
    category="flora",
)
