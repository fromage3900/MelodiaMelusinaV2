"""Eyewear — CAD-level frame front from real eyewear measurements.

Parameter surface is the ISO 8624 boxing system, authored in MILLIMETRES and
converted to Blender units once at the graph input (x 0.001). Every authored
number therefore matches the frame's printed marking (e.g. 54 [ ] 18) and the
published standard, rather than a scene-relative guess.

Construction (see Docs/Production/EYEWEAR_GN_BUILDER_PLAN_2026-09-12.md):
  cyclic profile swept along a cyclic silhouette -> all-quad, manifold, closed,
  with the lens aperture free (no boolean, no cut).

Verified on Blender 5.2.1: the sweep yields 0 n-gons, 0 triangles, 0 non-manifold
edges. Two engine facts drive the shape of this module:
  * Object Info defaults to transform_space='ORIGINAL'; referenced geometry needs
    'RELATIVE' or it is displaced by the host object's world transform.
  * Curve to Mesh has no even-thickness / miter option, so corners must be
    pre-rounded (Fillet Curve, Limit Radius on) or the profile self-intersects
    on the inside of the turn.

CAD detail: the boxing-system A/B dimensions describe the LENS APERTURE, not the
outer rim. The silhouette path is therefore the aperture box grown by one rim
thickness per side, so the swept band's inner edge lands exactly on A x B.
"""

from __future__ import annotations

import bpy

from .core import (
    add_bool_param, add_float_param, add_int_param, add_vector_param,
    label_tree, link_sockets, new_geometry_tree, register_builder, safe_node, sock,
)

MM = 0.001          # millimetres -> Blender units (1 BU = 1 m)


# --------------------------------------------------------------------- helpers

def _math(tree, op, loc, a=None, b=None):
    n = safe_node(tree, "ShaderNodeMath", loc)
    if n is None:
        return None
    n.operation = op
    if a is not None:
        link_sockets(tree, a, n.inputs[0])
    if b is not None:
        if hasattr(b, "is_output") or hasattr(b, "node"):
            link_sockets(tree, b, n.inputs[1])
        else:
            n.inputs[1].default_value = b
    return n


def _mm(tree, gin, param, loc, scale=1.0):
    """Group param in millimetres -> a socket in Blender units."""
    m = _math(tree, "MULTIPLY", loc, a=sock(gin, param, outputs=True), b=MM * scale)
    return m.outputs[0] if m else None


def _constant(tree, loc, value):
    v = safe_node(tree, "ShaderNodeValue", loc)
    if v is not None:
        v.outputs[0].default_value = value
    return v


def _offset(tree, loc, source, dx):
    """source + dx, where dx is a socket or a float."""
    return _math(tree, "ADD", loc, a=source, b=dx)


def build_eyewear_front(group_name="MEL_eyewear_front"):
    """Frame front: two lens rims + bridge, boxed from A/B/DBL in millimetres."""
    tree, gin, gout = new_geometry_tree(group_name)

    # --- boxing system (millimetres) -----------------------------------------
    add_float_param(tree, "Lens Width A", 54.0, 34.0, 66.0)
    add_float_param(tree, "Lens Height B", 34.0, 24.0, 48.0)
    add_float_param(tree, "Bridge DBL", 18.0, 12.0, 26.0)
    add_float_param(tree, "Rim Thickness", 4.0, 1.5, 10.0)
    add_float_param(tree, "Rim Depth", 6.0, 2.0, 14.0)
    add_float_param(tree, "Corner Radius", 7.0, 0.5, 20.0)
    add_float_param(tree, "Path Resolution", 3.0, 0.4, 12.0)
    add_float_param(tree, "Bridge Drop", 5.0, -6.0, 20.0)
    add_bool_param(tree, "Fill Caps", False)

    bx, by = 0, 0

    # --- profile: the rim cross-section, cyclic ------------------------------
    prof = safe_node(tree, "GeometryNodeCurvePrimitiveQuadrilateral", (bx - 900, by - 300))
    if prof is None:
        return (tree, gin, gout)
    try:
        prof.mode = "RECTANGLE"
    except Exception:
        pass
    link_sockets(tree, _mm(tree, gin, "Rim Thickness", (bx - 1080, by - 260)),
                 prof.inputs["Width"])
    link_sockets(tree, _mm(tree, gin, "Rim Depth", (bx - 1080, by - 360)),
                 prof.inputs["Height"])

    def rim(tag, y_flip):
        """One eyewire: aperture box grown by a rim, resampled, filleted, swept."""
        x0 = bx - 500
        y0 = by + (200 if not y_flip else -200)

        # aperture A x B, grown one rim thickness per side so the swept band's
        # inner edge lands exactly on A x B
        w = _math(tree, "ADD", (x0 - 620, y0 + 120),
                  a=_mm(tree, gin, "Lens Width A", (x0 - 820, y0 + 160)),
                  b=_mm(tree, gin, "Rim Thickness", (x0 - 820, y0 + 40)))
        h = _math(tree, "ADD", (x0 - 620, y0 - 40),
                  a=_mm(tree, gin, "Lens Height B", (x0 - 820, y0 - 80)),
                  b=_mm(tree, gin, "Rim Thickness", (x0 - 820, y0 - 200)))

        quad = safe_node(tree, "GeometryNodeCurvePrimitiveQuadrilateral", (x0 - 420, y0))
        if quad is None:
            return None
        try:
            quad.mode = "RECTANGLE"
        except Exception:
            pass
        link_sockets(tree, w.outputs[0], quad.inputs["Width"])
        link_sockets(tree, h.outputs[0], quad.inputs["Height"])

        # uniform path spacing, then pre-round the corners (Limit Radius on) so
        # the profile cannot self-intersect inside a turn
        res = safe_node(tree, "GeometryNodeResampleCurve", (x0 - 240, y0))
        if res is None:
            return None
        for cand in ("Length", "LENGTH"):
            try:
                res.inputs["Mode"].default_value = cand
                break
            except Exception:
                continue
        link_sockets(tree, quad.outputs["Curve"], res.inputs["Curve"])
        link_sockets(tree, _mm(tree, gin, "Path Resolution", (x0 - 420, y0 - 220)),
                     res.inputs["Length"])

        flt = safe_node(tree, "GeometryNodeFilletCurve", (x0 - 60, y0))
        if flt is None:
            return None
        for cand in ("Poly", "POLY", "Polygon"):
            try:
                flt.inputs["Mode"].default_value = cand
                break
            except Exception:
                continue
        link_sockets(tree, res.outputs["Curve"], flt.inputs["Curve"])
        link_sockets(tree, _mm(tree, gin, "Corner Radius", (x0 - 240, y0 - 320)),
                     flt.inputs["Radius"])
        flt.inputs["Limit Radius"].default_value = True

        # place the lens centre at +/-(A + DBL)/2 so the aperture gap is exactly DBL
        span = _math(tree, "ADD", (x0 - 620, y0 + 320),
                     a=_mm(tree, gin, "Lens Width A", (x0 - 820, y0 + 400)),
                     b=_mm(tree, gin, "Bridge DBL", (x0 - 820, y0 + 280)))
        half = _math(tree, "MULTIPLY", (x0 - 420, y0 + 320), a=span.outputs[0], b=0.5)

        c2m = safe_node(tree, "GeometryNodeCurveToMesh", (x0 + 140, y0))
        if c2m is None:
            return None
        link_sockets(tree, flt.outputs["Curve"], c2m.inputs["Curve"])
        link_sockets(tree, prof.outputs["Curve"], c2m.inputs["Profile Curve"])
        link_sockets(tree, sock(gin, "Fill Caps", outputs=True), c2m.inputs["Fill Caps"])

        xf = safe_node(tree, "GeometryNodeTransform", (x0 + 300, y0))
        if xf is None:
            return None
        link_sockets(tree, c2m.outputs["Mesh"], xf.inputs["Geometry"])
        if y_flip:
            neg = _math(tree, "MULTIPLY", (x0 + 100, y0 - 160),
                        a=half.outputs[0], b=-1.0)
            vec = safe_node(tree, "ShaderNodeCombineXYZ", (x0 + 200, y0 - 160))
            if neg is not None and vec is not None:
                link_sockets(tree, neg.outputs[0], vec.inputs["X"])
                link_sockets(tree, vec.outputs["Vector"], xf.inputs["Translation"])
        else:
            vec = safe_node(tree, "ShaderNodeCombineXYZ", (x0 + 200, y0 - 160))
            if vec is not None:
                link_sockets(tree, half.outputs[0], vec.inputs["X"])
                link_sockets(tree, vec.outputs["Vector"], xf.inputs["Translation"])
        return xf.outputs["Geometry"]

    left = rim("L", False)
    right = rim("R", True)

    # --- bridge: nasal span swept with the same profile ----------------------
    bridge_geo = None
    line = safe_node(tree, "GeometryNodeCurvePrimitiveLine", (bx - 120, by - 700))
    if line is not None:
        half_dbl = _math(tree, "MULTIPLY", (bx - 380, by - 660),
                         a=_mm(tree, gin, "Bridge DBL", (bx - 560, by - 640)), b=0.5)
        start = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 220, by - 620))
        end = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 220, by - 780))
        top = _math(tree, "MULTIPLY", (bx - 560, by - 820),
                    a=_mm(tree, gin, "Lens Height B", (bx - 740, by - 800)), b=0.5)
        drop = _mm(tree, gin, "Bridge Drop", (bx - 740, by - 940))
        by_sock = _math(tree, "SUBTRACT", (bx - 380, by - 860),
                        a=top.outputs[0], b=drop)
        if all(x is not None for x in (start, end, by_sock)):
            neg_half = _math(tree, "MULTIPLY", (bx - 380, by - 600),
                             a=half_dbl.outputs[0], b=-1.0)
            if neg_half is not None:
                link_sockets(tree, neg_half.outputs[0], start.inputs["X"])
            link_sockets(tree, half_dbl.outputs[0], end.inputs["X"])
            link_sockets(tree, by_sock.outputs[0], start.inputs["Y"])
            link_sockets(tree, by_sock.outputs[0], end.inputs["Y"])
            # the vectors must actually be linked into the line, or it keeps its
            # default (0,0,0)->(0,0,1) span and the bridge is 1 BU tall
            for vec_in, vec_src in (("Start", start), ("End", end)):
                try:
                    link_sockets(tree, vec_src.outputs["Vector"], line.inputs[vec_in])
                except Exception:
                    pass

            c2m_b = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 40, by - 700))
            if c2m_b is not None:
                link_sockets(tree, line.outputs["Curve"], c2m_b.inputs["Curve"])
                link_sockets(tree, prof.outputs["Curve"], c2m_b.inputs["Profile Curve"])
                # the rims are cyclic so caps are meaningless there; the bridge is an
                # open span and must be capped to stay manifold. Its two caps are the
                # only n-gons in the result.
                c2m_b.inputs["Fill Caps"].default_value = True
                bridge_geo = c2m_b.outputs["Mesh"]

    # --- combine -------------------------------------------------------------
    if left is not None and right is not None and bridge_geo is not None:
        j1 = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 500, by))
        if j1 is not None:
            link_sockets(tree, left, j1.inputs["Geometry"])
            link_sockets(tree, right, j1.inputs["Geometry"])
            j2 = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 660, by))
            if j2 is not None:
                link_sockets(tree, j1.outputs["Geometry"], j2.inputs["Geometry"])
                link_sockets(tree, bridge_geo, j2.inputs["Geometry"])
                link_sockets(tree, j2.outputs["Geometry"], gout.inputs["Geometry"])
    elif left is not None and right is not None:
        j1 = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 500, by))
        if j1 is not None:
            link_sockets(tree, left, j1.inputs["Geometry"])
            link_sockets(tree, right, j1.inputs["Geometry"])
            link_sockets(tree, j1.outputs["Geometry"], gout.inputs["Geometry"])

    label_tree(tree, group_name)
    return (tree, gin, gout)


register_builder(
    "MEL_eyewear_front", build_eyewear_front, "Eyewear Front",
    "CAD-level frame front from ISO 8624 boxing-system measurements (A/B/DBL in mm). "
    "Cyclic-profile sweep: all-quad, manifold, free lens aperture.",
    category="eyewear")


# --------------------------------------------------------------------- arms
#
# Axis convention for the whole eyewear family, and it is load-bearing:
#
#     X  across the face (frame width, 2A + DBL + 2xRimThickness)
#     Y  vertical (lens height B); the ear drop is -Y
#     Z  the viewing axis; behind the frame is -Z
#
# A frame front lies in XY and the temples run backward along -Z. Folding rotates
# about Y. The hinge barrel axis is therefore Y as well, which is why the cylinder
# is rotated 90 degrees about X before being instanced.


def _vec(tree, loc, x=None, y=None, z=None, const=0.0):
    """CombineXYZ with each component either a socket or a float."""
    n = safe_node(tree, "ShaderNodeCombineXYZ", loc)
    if n is None:
        return None
    for name, val in (("X", x), ("Y", y), ("Z", z)):
        if val is None:
            n.inputs[name].default_value = const
        elif hasattr(val, "node"):
            link_sockets(tree, val, n.inputs[name])
        else:
            n.inputs[name].default_value = val
    return n


def _rad(tree, gin, param, loc):
    """Group param in degrees -> radians."""
    return _math(tree, "MULTIPLY", loc, a=sock(gin, param, outputs=True),
                 b=0.017453292519943295)


def _cyc_profile(tree, loc, w_sock, h_sock):
    """A cyclic rectangular cross-section (the swept profile)."""
    q = safe_node(tree, "GeometryNodeCurvePrimitiveQuadrilateral", loc)
    if q is None:
        return None
    try:
        q.mode = "RECTANGLE"
    except Exception:
        pass
    link_sockets(tree, w_sock, q.inputs["Width"])
    link_sockets(tree, h_sock, q.inputs["Height"])
    return q


def build_eyewear_temple(group_name="MEL_eyewear_temple"):
    """Temple arm: straight run to the bend, then the ear drop, with a hinge fold."""
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Length to Bend", 100.0, 40.0, 160.0)
    add_float_param(tree, "Tip Reach", 22.0, 0.0, 80.0)
    add_float_param(tree, "Tip Drop", 28.0, 0.0, 70.0)
    add_float_param(tree, "Temple Width", 4.5, 1.0, 14.0)
    add_float_param(tree, "Temple Thickness", 3.0, 1.0, 12.0)
    add_float_param(tree, "Bend Radius", 8.0, 1.0, 40.0)
    add_float_param(tree, "Path Resolution", 3.0, 0.4, 12.0)
    add_float_param(tree, "Fold Angle", 0.0, 0.0, 95.0)
    add_float_param(tree, "Endpiece Clearance", 0.5, 0.0, 10.0)
    add_vector_param(tree, "Hinge Pivot", (0.0, 0.0, 0.0))
    add_bool_param(tree, "Right Side", False)
    add_bool_param(tree, "Fill Caps", True)

    bx, by = 0, 0

    ltb = _mm(tree, gin, "Length to Bend", (bx - 1200, by + 300))
    reach = _mm(tree, gin, "Tip Reach", (bx - 1200, by + 60))
    drop = _mm(tree, gin, "Tip Drop", (bx - 1200, by - 120))
    width = _mm(tree, gin, "Temple Width", (bx - 1200, by - 300))
    thick = _mm(tree, gin, "Temple Thickness", (bx - 1200, by - 480))

    # --- path: three points along -Z, the last moved to the tip ---------------
    neg_ltb = _math(tree, "MULTIPLY", (bx - 1000, by + 300), a=ltb, b=-1.0)
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 820, by + 200))
    if line is None:
        return (tree, gin, gout)
    line.inputs["Count"].default_value = 3
    link_sockets(tree, _vec(tree, (bx - 1000, by + 120), z=neg_ltb.outputs[0]).outputs["Vector"],
                 line.inputs["Offset"])

    # last point -> (0, -TipDrop, -(LTB + TipReach))
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 820, by - 900))
    cmp2 = safe_node(tree, "FunctionNodeCompare", (bx - 660, by - 900))
    sel_last = None
    if idx is not None and cmp2 is not None:
        cmp2.data_type = "INT"
        cmp2.operation = "EQUAL"
        link_sockets(tree, idx.outputs["Index"], cmp2.inputs["A"])
        cmp2.inputs["B"].default_value = 2
        sel_last = cmp2.outputs["Result"]

    back = _math(tree, "ADD", (bx - 1000, by - 120), a=ltb, b=reach)
    neg_back = _math(tree, "MULTIPLY", (bx - 820, by - 120), a=back.outputs[0], b=-1.0)
    neg_drop = _math(tree, "MULTIPLY", (bx - 1000, by - 300), a=drop, b=-1.0)
    tip_pos = _vec(tree, (bx - 660, by - 200), y=neg_drop.outputs[0], z=neg_back.outputs[0])

    setp = safe_node(tree, "GeometryNodeSetPosition", (bx - 500, by + 100))
    if setp is None:
        return (tree, gin, gout)
    link_sockets(tree, line.outputs["Mesh"], setp.inputs["Geometry"])
    if sel_last is not None:
        link_sockets(tree, sel_last, setp.inputs["Selection"])
    if tip_pos is not None:
        link_sockets(tree, tip_pos.outputs["Vector"], setp.inputs["Position"])

    m2c = safe_node(tree, "GeometryNodeMeshToCurve", (bx - 320, by + 100))
    if m2c is None:
        return (tree, gin, gout)
    link_sockets(tree, setp.outputs["Geometry"], m2c.inputs["Mesh"])

    # --- uniform spacing, then round the bend ---------------------------------
    res = safe_node(tree, "GeometryNodeResampleCurve", (bx - 140, by + 100))
    if res is None:
        return (tree, gin, gout)
    for cand in ("Length", "LENGTH"):
        try:
            res.inputs["Mode"].default_value = cand
            break
        except Exception:
            continue
    link_sockets(tree, m2c.outputs["Curve"], res.inputs["Curve"])
    link_sockets(tree, _mm(tree, gin, "Path Resolution", (bx - 320, by - 480)),
                 res.inputs["Length"])

    flt = safe_node(tree, "GeometryNodeFilletCurve", (bx + 40, by + 100))
    if flt is None:
        return (tree, gin, gout)
    for cand in ("Poly", "POLY", "Polygon"):
        try:
            flt.inputs["Mode"].default_value = cand
            break
        except Exception:
            continue
    link_sockets(tree, res.outputs["Curve"], flt.inputs["Curve"])
    link_sockets(tree, _mm(tree, gin, "Bend Radius", (bx - 140, by - 480)),
                 flt.inputs["Radius"])
    flt.inputs["Limit Radius"].default_value = True

    prof = _cyc_profile(tree, (bx - 320, by - 700), width, thick)

    c2m = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 220, by + 100))
    if c2m is None or prof is None:
        return (tree, gin, gout)
    link_sockets(tree, flt.outputs["Curve"], c2m.inputs["Curve"])
    link_sockets(tree, prof.outputs["Curve"], c2m.inputs["Profile Curve"])
    link_sockets(tree, sock(gin, "Fill Caps", outputs=True), c2m.inputs["Fill Caps"])
    geom = c2m.outputs["Mesh"]

    # --- fold about Y, then place, then mirror --------------------------------
    rot = _vec(tree, (bx + 380, by - 200), y=_rad(tree, gin, "Fold Angle", (bx + 200, by - 320)).outputs[0])
    xf_fold = safe_node(tree, "GeometryNodeTransform", (bx + 540, by + 100))
    if xf_fold is not None and rot is not None:
        link_sockets(tree, geom, xf_fold.inputs["Geometry"])
        link_sockets(tree, rot.outputs["Vector"], xf_fold.inputs["Rotation"])
        geom = xf_fold.outputs["Geometry"]

    # clearance: half the temple width plus the endpiece gap, along +X
    half_w = _math(tree, "MULTIPLY", (bx + 380, by - 560), a=width, b=0.5)
    clr = _math(tree, "ADD", (bx + 540, by - 560), a=half_w.outputs[0],
                b=_mm(tree, gin, "Endpiece Clearance", (bx + 380, by - 720)))
    piv = _vec(tree, (bx + 540, by - 400),
               x=clr.outputs[0] if clr is not None else None)
    xf_place = safe_node(tree, "GeometryNodeTransform", (bx + 700, by + 100))
    if xf_place is not None and piv is not None:
        link_sockets(tree, geom, xf_place.inputs["Geometry"])
        link_sockets(tree, piv.outputs["Vector"], xf_place.inputs["Translation"])
        geom = xf_place.outputs["Geometry"]

    mirror = safe_node(tree, "GeometryNodeTransform", (bx + 860, by + 100))
    flip = safe_node(tree, "GeometryNodeFlipFaces", (bx + 1020, by + 100))
    mix = safe_node(tree, "GeometryNodeSwitch", (bx + 1180, by + 100))
    if mirror is not None and flip is not None and mix is not None:
        try:
            mix.input_type = "GEOMETRY"
        except Exception:
            pass
        neg_one = _vec(tree, (bx + 700, by - 700), x=-1.0, y=1.0, z=1.0)
        link_sockets(tree, geom, mirror.inputs["Geometry"])
        if neg_one is not None:
            link_sockets(tree, neg_one.outputs["Vector"], mirror.inputs["Scale"])
        link_sockets(tree, mirror.outputs["Geometry"], flip.inputs["Mesh"])
        link_sockets(tree, sock(gin, "Right Side", outputs=True), mix.inputs["Switch"])
        link_sockets(tree, geom, mix.inputs["False"])
        link_sockets(tree, flip.outputs["Mesh"], mix.inputs["True"])
        geom = mix.outputs["Output"]

    link_sockets(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, group_name)
    return (tree, gin, gout)


def build_eyewear_hinge(group_name="MEL_eyewear_hinge"):
    """Hinge knuckle: an instanced barrel stack on the vertical (Y) hinge axis."""
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Barrel Radius", 1.4, 0.4, 6.0)
    add_float_param(tree, "Barrel Length", 2.4, 0.6, 10.0)
    add_float_param(tree, "Barrel Gap", 0.15, 0.0, 2.0)
    add_int_param(tree, "Front Barrels", 1, 1, 3)
    add_int_param(tree, "Temple Barrels", 2, 1, 3)
    add_int_param(tree, "Side Vertices", 12, 6, 32)
    add_vector_param(tree, "Hinge Pivot", (0.0, 0.0, 0.0))
    add_bool_param(tree, "Right Side", False)

    bx, by = 0, 0

    length = _mm(tree, gin, "Barrel Length", (bx - 1200, by + 200))
    gap = _mm(tree, gin, "Barrel Gap", (bx - 1200, by + 40))
    radius = _mm(tree, gin, "Barrel Radius", (bx - 1200, by - 120))

    # step = length + gap ; count = front + temple ; startY = -(count-1)*step/2
    step = _math(tree, "ADD", (bx - 1000, by + 140), a=length, b=gap)
    count = _math(tree, "ADD", (bx - 1000, by - 40),
                  a=sock(gin, "Front Barrels", outputs=True),
                  b=sock(gin, "Temple Barrels", outputs=True))
    span = _math(tree, "MULTIPLY", (bx - 820, by + 140),
                 a=_math(tree, "SUBTRACT", (bx - 1000, by + 300),
                         a=count.outputs[0], b=1.0).outputs[0],
                 b=step.outputs[0])
    start_y = _math(tree, "MULTIPLY", (bx - 640, by + 140), a=span.outputs[0], b=-0.5)

    points = safe_node(tree, "GeometryNodeMeshLine", (bx - 460, by + 200))
    if points is None:
        return (tree, gin, gout)
    link_sockets(tree, count.outputs[0], points.inputs["Count"])
    link_sockets(tree, _vec(tree, (bx - 640, by + 40), y=start_y.outputs[0]).outputs["Vector"],
                 points.inputs["Start Location"])
    link_sockets(tree, _vec(tree, (bx - 640, by - 80), y=step.outputs[0]).outputs["Vector"],
                 points.inputs["Offset"])

    # the barrel: a cylinder along Z rotated 90 deg about X so its axis is Y
    cyl = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 460, by - 200))
    if cyl is None:
        return (tree, gin, gout)
    link_sockets(tree, radius, cyl.inputs["Radius"])
    link_sockets(tree, length, cyl.inputs["Depth"])
    link_sockets(tree, sock(gin, "Side Vertices", outputs=True), cyl.inputs["Vertices"])

    xf_axis = safe_node(tree, "GeometryNodeTransform", (bx - 300, by - 200))
    if xf_axis is None:
        return (tree, gin, gout)
    link_sockets(tree, cyl.outputs["Mesh"], xf_axis.inputs["Geometry"])
    link_sockets(tree, _vec(tree, (bx - 460, by - 360), x=1.5707963267948966).outputs["Vector"],
                 xf_axis.inputs["Rotation"])

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 120, by + 100))
    if inst is None:
        return (tree, gin, gout)
    link_sockets(tree, points.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, xf_axis.outputs["Geometry"], inst.inputs["Instance"])

    # realize: an unrealized instance cloud exports as an EMPTY glb
    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 40, by + 100))
    if real is None:
        return (tree, gin, gout)
    link_sockets(tree, inst.outputs["Instances"], real.inputs["Geometry"])
    geom = real.outputs["Geometry"]

    xf_place = safe_node(tree, "GeometryNodeTransform", (bx + 200, by + 100))
    if xf_place is not None:
        link_sockets(tree, geom, xf_place.inputs["Geometry"])
        link_sockets(tree, sock(gin, "Hinge Pivot", outputs=True), xf_place.inputs["Translation"])
        geom = xf_place.outputs["Geometry"]

    mirror = safe_node(tree, "GeometryNodeTransform", (bx + 360, by + 100))
    flip = safe_node(tree, "GeometryNodeFlipFaces", (bx + 520, by + 100))
    mix = safe_node(tree, "GeometryNodeSwitch", (bx + 680, by + 100))
    if mirror is not None and flip is not None and mix is not None:
        try:
            mix.input_type = "GEOMETRY"
        except Exception:
            pass
        neg_one = _vec(tree, (bx + 360, by - 320), x=-1.0, y=1.0, z=1.0)
        link_sockets(tree, geom, mirror.inputs["Geometry"])
        if neg_one is not None:
            link_sockets(tree, neg_one.outputs["Vector"], mirror.inputs["Scale"])
        link_sockets(tree, mirror.outputs["Geometry"], flip.inputs["Mesh"])
        link_sockets(tree, sock(gin, "Right Side", outputs=True), mix.inputs["Switch"])
        link_sockets(tree, geom, mix.inputs["False"])
        link_sockets(tree, flip.outputs["Mesh"], mix.inputs["True"])
        geom = mix.outputs["Output"]

    link_sockets(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, group_name)
    return (tree, gin, gout)


register_builder(
    "MEL_eyewear_temple", build_eyewear_temple, "Eyewear Temple",
    "Temple arm with ear drop, hinge fold and endpiece clearance. Extends along -Z "
    "(behind the frame), drops -Y, folds about Y. Side mirrored via negative X scale "
    "plus Flip Faces (5.2 has no Mirror node).",
    category="eyewear")

register_builder(
    "MEL_eyewear_hinge", build_eyewear_hinge, "Eyewear Hinge",
    "Hinge knuckle: an instanced barrel stack on the vertical hinge axis, realized so "
    "it survives glTF export. Pivot is the barrel axis.",
    category="eyewear")
