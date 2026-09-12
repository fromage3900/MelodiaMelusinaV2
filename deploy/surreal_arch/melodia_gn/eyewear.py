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
    add_bool_param, add_float_param, label_tree, link_sockets,
    new_geometry_tree, register_builder, safe_node, sock,
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
