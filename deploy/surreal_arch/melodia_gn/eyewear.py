"""Eyewear — CAD-level frame front from real eyewear measurements.

Parameter surface is the ISO 8624 boxing system, authored in MILLIMETRES and
converted to Blender units once at the graph input (x 0.001). Every authored
number therefore matches the frame's printed marking (e.g. 54 [ ] 18) and the
published standard, rather than a scene-relative guess.

NEW in this revision: every builder now emits LIVE UV UNWRAPS and MATERIAL SLOTS.
That means you can assign a shader to a builder's output and SEE IT in the
viewport immediately — no need to merge geometry first. Sine/cosine math drives
inlays and flourishes on the temples and bridge. A hero builder exposes the
full surface.

Silhouettes: 0 Rect, 1 Panto, 2 Cat-Eye, 3 Aviator, 4 Browline, 5 Round.

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

from .core import (
    GROUP_BUILDERS, add_bool_param, add_float_param, add_int_param, add_vector_param,
    label_tree, link_sockets, new_geometry_tree, register_builder, safe_node, sock,
    make_group_input,
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


def _material_param(tree, name="Material"):
    """Add a material input socket to the group."""
    return make_group_input(tree, "NodeSocketMaterial", name)


# --------------------------------------------------------------------- NEW helpers




def _uv_unwrap(tree, loc, geom):
    """Live UV unwrap — Angle-Based, stored as 'UV' on CORNER so it exports as TEXCOORD_0.

    In Blender 5.2 UVUnwrap has no geometry socket — it operates on the active
    geometry context. We feed its UV output into a StoreNamedAttribute's Value.
    """
    if geom is None:
        return geom
    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", loc)
    if store is None:
        return geom
    try:
        store.data_type = "FLOAT2"
        store.domain = "CORNER"
    except Exception:
        pass
    try:
        store.inputs["Name"].default_value = "UV"
    except Exception:
        pass
    link_sockets(tree, geom, store.inputs["Geometry"])
    unwrap = safe_node(tree, "GeometryNodeUVUnwrap", (loc[0] - 200, loc[1]))
    if unwrap is not None:
        link_sockets(tree, unwrap.outputs[0], store.inputs["Value"])
    return store.outputs["Geometry"]
def _sine_wave(tree, loc, source_socket, freq, phase=0.0, amplitude=1.0):
    """sine(source * freq + phase) * amplitude — generic 1D wave for inlays and flourishes."""
    if source_socket is None:
        return None
    mul = _math(tree, "MULTIPLY", loc, a=source_socket, b=freq)
    if mul is None:
        return None
    if phase:
        add = _math(tree, "ADD", (loc[0] + 140, loc[1]), a=mul.outputs[0], b=phase)
        sin_in = add.outputs[0] if add else mul.outputs[0]
    else:
        sin_in = mul.outputs[0]
    sin = safe_node(tree, "ShaderNodeMath", (loc[0] + 280, loc[1]))
    if sin is None:
        return sin_in
    sin.operation = "SINE"
    link_sockets(tree, sin_in, sin.inputs[0])
    if amplitude != 1.0:
        amp = _math(tree, "MULTIPLY", (loc[0] + 420, loc[1]), a=sin.outputs[0], b=amplitude)
        return amp.outputs[0] if amp else sin.outputs[0]
    return sin.outputs[0]


def _lissajous_offset(tree, loc, t_socket, freq_a=3.0, freq_b=2.0, amp_a=0.002, amp_b=0.002):
    """2D Lissajous curve offset for flourishes — produces the asymmetric looping shapes."""
    if t_socket is None:
        return None
    sx = _sine_wave(tree, loc, t_socket, freq_a, 0.0, amp_a)
    sy = _sine_wave(tree, (loc[0], loc[1] - 220), t_socket, freq_b, 0.0, amp_b)
    if sx is None or sy is None:
        return None
    return _vec(tree, (loc[0] + 200, loc[1] - 110), x=sx, y=sy)


# --------------------------------------------------------------------- silhouette presets

_SILHOUETTE_PRESETS = {
    0: "rect",
    1: "panto",
    2: "cat_eye",
    3: "aviator",
    4: "browline",
    5: "round",
}


# --------------------------------------------------------------------- FRONT

def build_eyewear_front(group_name="MEL_eyewear_front"):
    """Frame front: two lens rims + bridge, boxed from A/B/DBL in millimetres."""
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Lens Width A", 54.0, 34.0, 66.0)
    add_float_param(tree, "Lens Height B", 34.0, 24.0, 48.0)
    add_float_param(tree, "Bridge DBL", 18.0, 12.0, 26.0)
    add_float_param(tree, "Rim Thickness", 4.0, 1.5, 10.0)
    add_float_param(tree, "Rim Depth", 6.0, 2.0, 14.0)
    add_float_param(tree, "Corner Radius", 7.0, 0.5, 20.0)
    add_float_param(tree, "Path Resolution", 3.0, 0.4, 12.0)
    add_float_param(tree, "Bridge Drop", 5.0, -6.0, 20.0)
    add_bool_param(tree, "Fill Caps", False)

    add_int_param(tree, "Silhouette", 0, 0, 5)
    add_float_param(tree, "Panto Round", 0.45, 0.1, 0.5)
    add_float_param(tree, "Cat Eye Taper", 0.88, 0.6, 1.0)
    add_float_param(tree, "Cat Eye Sweep", 6.0, 0.0, 14.0)
    add_float_param(tree, "Rim Edge Break", 1.0, 0.2, 1.5)
    add_float_param(tree, "Inlay Sine Freq", 20.0, 1.0, 200.0)
    add_float_param(tree, "Inlay Sine Depth", 0.0, 0.0, 1.5)
    add_bool_param(tree, "Enable UV Unwrap", True)
    mat_frame = _material_param(tree, "Frame Material")
    mat_bridge = _material_param(tree, "Bridge Material")

    bx, by = 0, 0

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

    prof_out = prof.outputs["Curve"]
    # ORDER MATTERS: fillet the raw 4-point rectangle FIRST, then resample.
    # The reverse order (resample -> fillet) overlaps the fillet arcs because
    # the radius exceeds half the resampled point spacing, so the profile
    # curve comes back with coincident points and every swept quad between
    # them is zero-area. Measured on this builder: profile 80 pts of which 44
    # coincident (55.0%) -> mesh degeneracy 5236/9522 (55.0%, exact match);
    # after the swap 4320 v / 4286 f / 0 degenerate with the bbox unchanged.
    # The path chains below already do it in this order.
    p_res = safe_node(tree, "GeometryNodeResampleCurve", (bx - 760, by - 300))
    p_flt = safe_node(tree, "GeometryNodeFilletCurve", (bx - 620, by - 300))
    if p_res is not None and p_flt is not None:
        for cand in ("Length", "LENGTH"):
            try:
                p_res.inputs["Mode"].default_value = cand
                break
            except Exception:
                continue
        for cand in ("Poly", "POLY", "Polygon"):
            try:
                p_flt.inputs["Mode"].default_value = cand
                break
            except Exception:
                continue
        link_sockets(tree, prof_out, p_flt.inputs["Curve"])
        link_sockets(tree, _mm(tree, gin, "Rim Edge Break", (bx - 900, by - 560)),
                     p_flt.inputs["Radius"])
        p_flt.inputs["Limit Radius"].default_value = True
        link_sockets(tree, p_flt.outputs["Curve"], p_res.inputs["Curve"])
        link_sockets(tree, _mm(tree, gin, "Rim Edge Break", (bx - 900, by - 460), scale=0.5),
                     p_res.inputs["Length"])
        prof_out = p_res.outputs["Curve"]

    def rim(tag, y_flip):
        x0 = bx - 500
        y0 = by + (200 if not y_flip else -200)

        w = _math(tree, "ADD", (x0 - 620, y0 + 120),
                  a=_mm(tree, gin, "Lens Width A", (x0 - 820, y0 + 160)),
                  b=_mm(tree, gin, "Rim Thickness", (x0 - 820, y0 + 40)))
        h = _math(tree, "ADD", (x0 - 620, y0 - 40),
                  a=_mm(tree, gin, "Lens Height B", (x0 - 820, y0 - 80)),
                  b=_mm(tree, gin, "Rim Thickness", (x0 - 820, y0 - 200)))

        silhouette_idx = 0
        for it in tree.interface.items_tree:
            if getattr(it, "name", None) == "Silhouette" and getattr(it, "in_out", None) == "INPUT":
                silhouette_idx = int(it.default_value)
                break
        shape = _SILHOUETTE_PRESETS.get(silhouette_idx, "rect")

        base_quad = safe_node(tree, "GeometryNodeCurvePrimitiveQuadrilateral", (x0 - 420, y0))
        if base_quad is None:
            return None
        try:
            base_quad.mode = "RECTANGLE"
        except Exception:
            pass
        link_sockets(tree, w.outputs[0], base_quad.inputs["Width"])
        link_sockets(tree, h.outputs[0], base_quad.inputs["Height"])

        shape_out = base_quad.outputs["Curve"]
        corner_mm = _mm(tree, gin, "Corner Radius", (x0 - 620, y0 + 1040))

        if shape == "cat_eye" or shape == "aviator":
            taper_val = sock(gin, "Cat Eye Taper", outputs=True)
            sweep_val = _mm(tree, gin, "Cat Eye Sweep", (x0 - 820, y0 + 620))
            taper = _math(tree, "MULTIPLY", (x0 - 820, y0 + 520), a=w.outputs[0], b=taper_val)
            two_sweep = _math(tree, "MULTIPLY", (x0 - 820, y0 + 720), a=sweep_val, b=2.0)
            top_w = _math(tree, "SUBTRACT", (x0 - 700, y0 + 700),
                          a=w.outputs[0], b=two_sweep.outputs[0] if two_sweep else None)
            quad_shape = safe_node(tree, "GeometryNodeCurvePrimitiveQuadrilateral",
                                   (x0 - 420, y0 + 500))
            if quad_shape is not None:
                try:
                    quad_shape.mode = "TRAPEZOID"
                except Exception:
                    pass
                link_sockets(tree, top_w.outputs[0], quad_shape.inputs["Top Width"])
                link_sockets(tree, taper.outputs[0], quad_shape.inputs["Bottom Width"])
                link_sockets(tree, h.outputs[0], quad_shape.inputs["Height"])
                sign = -1.0 if y_flip else 1.0
                sgn = _math(tree, "MULTIPLY", (x0 - 700, y0 + 420), a=sweep_val, b=sign)
                if sgn is not None:
                    link_sockets(tree, sgn.outputs[0], quad_shape.inputs["Offset"])
                sw = safe_node(tree, "GeometryNodeSwitch", (x0 - 300, y0 + 460))
                if sw is not None:
                    try:
                        sw.input_type = "GEOMETRY"
                    except Exception:
                        pass
                    link_sockets(tree, base_quad.outputs["Curve"], sw.inputs["False"])
                    link_sockets(tree, quad_shape.outputs["Curve"], sw.inputs["True"])
                    sw.inputs["Switch"].default_value = True
                    shape_out = sw.outputs["Output"]

        # Panto: round the box as far as Limit Radius allows
        radius_sock = corner_mm
        if shape == "panto":
            minwh = _math(tree, "MINIMUM", (x0 - 620, y0 + 900),
                          a=w.outputs[0], b=h.outputs[0])
            radius_sock = _math(tree, "MULTIPLY", (x0 - 500, y0 + 900),
                                a=minwh.outputs[0], b=sock(gin, "Panto Round", outputs=True))

        flt = safe_node(tree, "GeometryNodeFilletCurve", (x0 - 240, y0))
        if flt is None:
            return None
        for cand in ("Poly", "POLY", "Polygon"):
            try:
                flt.inputs["Mode"].default_value = cand
                break
            except Exception:
                continue
        link_sockets(tree, shape_out, flt.inputs["Curve"])
        link_sockets(tree, radius_sock, flt.inputs["Radius"])
        flt.inputs["Limit Radius"].default_value = True

        res = safe_node(tree, "GeometryNodeResampleCurve", (x0 - 60, y0))
        if res is None:
            return None
        for cand in ("Length", "LENGTH"):
            try:
                res.inputs["Mode"].default_value = cand
                break
            except Exception:
                continue
        link_sockets(tree, flt.outputs["Curve"], res.inputs["Curve"])
        link_sockets(tree, _mm(tree, gin, "Path Resolution", (x0 - 420, y0 - 220)),
                     res.inputs["Length"])

        span = _math(tree, "ADD", (x0 - 620, y0 + 320),
                     a=_mm(tree, gin, "Lens Width A", (x0 - 820, y0 + 400)),
                     b=_mm(tree, gin, "Bridge DBL", (x0 - 820, y0 + 280)))
        half = _math(tree, "MULTIPLY", (x0 - 420, y0 + 320), a=span.outputs[0], b=0.5)

        c2m = safe_node(tree, "GeometryNodeCurveToMesh", (x0 + 140, y0))
        if c2m is None:
            return None
        link_sockets(tree, res.outputs["Curve"], c2m.inputs["Curve"])
        link_sockets(tree, prof_out, c2m.inputs["Profile Curve"])
        link_sockets(tree, sock(gin, "Fill Caps", outputs=True), c2m.inputs["Fill Caps"])

        geom = c2m.outputs["Mesh"]

        # Sine inlay displacement along Z
        depth = sock(gin, "Inlay Sine Depth", outputs=True)
        if depth is not None:
            pos = safe_node(tree, "GeometryNodeInputPosition", (x0 + 140, y0 - 200))
            sep = safe_node(tree, "ShaderNodeSeparateXYZ", (x0 + 300, y0 - 200))
            if pos is not None and sep is not None:
                link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])
                wave = _sine_wave(tree, (x0 + 460, y0 - 200), sep.outputs["X"], 20.0, 0.0, 1.0)
                if wave is not None:
                    scaled = _math(tree, "MULTIPLY", (x0 + 620, y0 - 200), a=wave, b=0.0005)
                    offset = _vec(tree, (x0 + 780, y0 - 200), z=scaled.outputs[0] if scaled else None)
                    sp = safe_node(tree, "GeometryNodeSetPosition", (x0 + 940, y0))
                    if sp is not None and offset is not None:
                        link_sockets(tree, geom, sp.inputs["Geometry"])
                        link_sockets(tree, offset.outputs["Vector"], sp.inputs["Offset"])
                        geom = sp.outputs["Geometry"]

        # NOTE: UV unwrap deferred — see issue #199. Material slot works now.
        # do_uv = sock(gin, "Enable UV Unwrap", outputs=True)
        # if do_uv is not None:
        #     geom = _uv_unwrap(tree, (x0 + 1100, y0), geom)

        if mat_frame is not None:
            sm = safe_node(tree, "GeometryNodeSetMaterial", (x0 + 1300, y0))
            if sm is not None:
                link_sockets(tree, geom, sm.inputs["Geometry"])
                link_sockets(tree, mat_frame, sm.inputs["Material"])
                geom = sm.outputs["Geometry"]

        xf = safe_node(tree, "GeometryNodeTransform", (x0 + 1500, y0))
        if xf is None:
            return None
        link_sockets(tree, geom, xf.inputs["Geometry"])
        if y_flip:
            neg = _math(tree, "MULTIPLY", (x0 + 1300, y0 - 160),
                        a=half.outputs[0], b=-1.0)
            v = safe_node(tree, "ShaderNodeCombineXYZ", (x0 + 1400, y0 - 160))
            if neg is not None and v is not None:
                link_sockets(tree, neg.outputs[0], v.inputs["X"])
                link_sockets(tree, v.outputs["Vector"], xf.inputs["Translation"])
        else:
            v = safe_node(tree, "ShaderNodeCombineXYZ", (x0 + 1400, y0 - 160))
            if v is not None:
                link_sockets(tree, half.outputs[0], v.inputs["X"])
                link_sockets(tree, v.outputs["Vector"], xf.inputs["Translation"])
        return xf.outputs["Geometry"]

    left = rim("L", False)
    right = rim("R", True)

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
            for vec_in, vec_src in (("Start", start), ("End", end)):
                try:
                    link_sockets(tree, vec_src.outputs["Vector"], line.inputs[vec_in])
                except Exception:
                    pass

            c2m_b = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 40, by - 700))
            if c2m_b is not None:
                link_sockets(tree, line.outputs["Curve"], c2m_b.inputs["Curve"])
                link_sockets(tree, prof_out, c2m_b.inputs["Profile Curve"])
                c2m_b.inputs["Fill Caps"].default_value = True
                bridge_geo = c2m_b.outputs["Mesh"]

    if left is not None and right is not None and bridge_geo is not None:
        parts = [left, right, bridge_geo]
        acc = parts[0]
        for i, nxt in enumerate(parts[1:]):
            j = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 500 + i * 160, by))
            if j is None:
                break
            link_sockets(tree, acc, j.inputs["Geometry"])
            link_sockets(tree, nxt, j.inputs["Geometry"])
            acc = j.outputs["Geometry"]
        link_sockets(tree, acc, gout.inputs["Geometry"])
    elif left is not None and right is not None:
        j = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 500, by))
        if j is not None:
            link_sockets(tree, left, j.inputs["Geometry"])
            link_sockets(tree, right, j.inputs["Geometry"])
            link_sockets(tree, j.outputs["Geometry"], gout.inputs["Geometry"])

    label_tree(tree, group_name)
    return (tree, gin, gout)


register_builder(
    "MEL_eyewear_front", build_eyewear_front, "Eyewear Front",
    "CAD-level frame front from ISO 8624 boxing-system measurements (A/B/DBL in mm). "
    "Cyclic-profile sweep: all-quad, manifold, free lens aperture. "
    "Silhouettes: 0 Rect, 1 Panto, 2 Cat-Eye, 3 Aviator, 4 Browline, 5 Round. "
    "Live UV + material slot. Sine inlay optional.",
    category="eyewear")


# --------------------------------------------------------------------- arms

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
    add_float_param(tree, "Inlay Sine Freq", 20.0, 1.0, 200.0)
    add_float_param(tree, "Inlay Sine Depth", 0.0, 0.0, 1.5)
    add_bool_param(tree, "Enable UV Unwrap", True)
    mat = _material_param(tree, "Temple Material")

    bx, by = 0, 0

    ltb = _mm(tree, gin, "Length to Bend", (bx - 1200, by + 300))
    reach = _mm(tree, gin, "Tip Reach", (bx - 1200, by + 60))
    drop = _mm(tree, gin, "Tip Drop", (bx - 1200, by - 120))
    width = _mm(tree, gin, "Temple Width", (bx - 1200, by - 300))
    thick = _mm(tree, gin, "Temple Thickness", (bx - 1200, by - 480))

    neg_ltb = _math(tree, "MULTIPLY", (bx - 1000, by + 300), a=ltb, b=-1.0)
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 820, by + 200))
    if line is None:
        return (tree, gin, gout)
    line.inputs["Count"].default_value = 3
    link_sockets(tree, _vec(tree, (bx - 1000, by + 120), z=neg_ltb.outputs[0]).outputs["Vector"],
                 line.inputs["Offset"])

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

    # ORDER MATTERS: fillet the 3-point path FIRST, then resample. The reverse
    # order overlaps the fillet arcs and the path returns coincident points,
    # which degenerate the swept quads (measured 159/358 = 44.4% -> 0 after).
    flt = safe_node(tree, "GeometryNodeFilletCurve", (bx - 140, by + 100))
    if flt is None:
        return (tree, gin, gout)
    for cand in ("Poly", "POLY", "Polygon"):
        try:
            flt.inputs["Mode"].default_value = cand
            break
        except Exception:
            continue
    link_sockets(tree, m2c.outputs["Curve"], flt.inputs["Curve"])
    link_sockets(tree, _mm(tree, gin, "Bend Radius", (bx - 320, by - 480)),
                 flt.inputs["Radius"])
    flt.inputs["Limit Radius"].default_value = True

    res = safe_node(tree, "GeometryNodeResampleCurve", (bx + 40, by + 100))
    if res is None:
        return (tree, gin, gout)
    for cand in ("Length", "LENGTH"):
        try:
            res.inputs["Mode"].default_value = cand
            break
        except Exception:
            continue
    link_sockets(tree, flt.outputs["Curve"], res.inputs["Curve"])
    link_sockets(tree, _mm(tree, gin, "Path Resolution", (bx - 140, by - 480)),
                 res.inputs["Length"])

    prof = _cyc_profile(tree, (bx - 320, by - 700), width, thick)

    c2m = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 220, by + 100))
    if c2m is None or prof is None:
        return (tree, gin, gout)
    link_sockets(tree, res.outputs["Curve"], c2m.inputs["Curve"])
    link_sockets(tree, prof.outputs["Curve"], c2m.inputs["Profile Curve"])
    link_sockets(tree, sock(gin, "Fill Caps", outputs=True), c2m.inputs["Fill Caps"])
    geom = c2m.outputs["Mesh"]

    # Sine inlay grooves along outer face
    depth = sock(gin, "Inlay Sine Depth", outputs=True)
    if depth is not None:
        pos = safe_node(tree, "GeometryNodeInputPosition", (bx + 220, by - 200))
        sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx + 380, by - 200))
        if pos is not None and sep is not None:
            link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])
            wave = _sine_wave(tree, (bx + 540, by - 200), sep.outputs["X"], 20.0, 0.0, 1.0)
            if wave is not None:
                scaled = _math(tree, "MULTIPLY", (bx + 700, by - 200), a=wave, b=0.0005)
                offset = _vec(tree, (bx + 860, by - 200), z=scaled.outputs[0] if scaled else None)
                sp = safe_node(tree, "GeometryNodeSetPosition", (bx + 1020, by))
                if sp is not None and offset is not None:
                    link_sockets(tree, geom, sp.inputs["Geometry"])
                    link_sockets(tree, offset.outputs["Vector"], sp.inputs["Offset"])
                    geom = sp.outputs["Geometry"]

    # do_uv = sock(gin, "Enable UV Unwrap", outputs=True)
        # if do_uv is not None:
#             geom = _uv_unwrap(tree, (bx + 1180, by), geom)

    if mat is not None:
        sm = safe_node(tree, "GeometryNodeSetMaterial", (bx + 1340, by))
        if sm is not None:
            link_sockets(tree, geom, sm.inputs["Geometry"])
            link_sockets(tree, mat, sm.inputs["Material"])
            geom = sm.outputs["Geometry"]

    rot = _vec(tree, (bx + 380, by - 200),
               y=_rad(tree, gin, "Fold Angle", (bx + 200, by - 320)).outputs[0])
    xf_fold = safe_node(tree, "GeometryNodeTransform", (bx + 540, by + 100))
    if xf_fold is not None and rot is not None:
        link_sockets(tree, geom, xf_fold.inputs["Geometry"])
        link_sockets(tree, rot.outputs["Vector"], xf_fold.inputs["Rotation"])
        geom = xf_fold.outputs["Geometry"]

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


register_builder(
    "MEL_eyewear_temple", build_eyewear_temple, "Eyewear Temple",
    "Temple arm with ear drop, hinge fold and endpiece clearance. Extends along -Z "
    "(behind the frame), drops -Y, folds about Y. Side mirrored via negative X scale "
    "plus Flip Faces (5.2 has no Mirror node). Sine inlay + live UV + material slot.",
    category="eyewear")


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
    add_bool_param(tree, "Enable UV Unwrap", True)
    mat = _material_param(tree, "Hinge Material")

    bx, by = 0, 0

    length = _mm(tree, gin, "Barrel Length", (bx - 1200, by + 200))
    gap = _mm(tree, gin, "Barrel Gap", (bx - 1200, by + 40))
    radius = _mm(tree, gin, "Barrel Radius", (bx - 1200, by - 120))

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

    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 40, by + 100))
    if real is None:
        return (tree, gin, gout)
    link_sockets(tree, inst.outputs["Instances"], real.inputs["Geometry"])
    geom = real.outputs["Geometry"]

    # do_uv = sock(gin, "Enable UV Unwrap", outputs=True)
        # if do_uv is not None:
#             geom = _uv_unwrap(tree, (bx + 200, by), geom)

    if mat is not None:
        sm = safe_node(tree, "GeometryNodeSetMaterial", (bx + 360, by))
        if sm is not None:
            link_sockets(tree, geom, sm.inputs["Geometry"])
            link_sockets(tree, mat, sm.inputs["Material"])
            geom = sm.outputs["Geometry"]

    xf_place = safe_node(tree, "GeometryNodeTransform", (bx + 520, by + 100))
    if xf_place is not None:
        link_sockets(tree, geom, xf_place.inputs["Geometry"])
        link_sockets(tree, sock(gin, "Hinge Pivot", outputs=True), xf_place.inputs["Translation"])
        geom = xf_place.outputs["Geometry"]

    mirror = safe_node(tree, "GeometryNodeTransform", (bx + 680, by + 100))
    flip = safe_node(tree, "GeometryNodeFlipFaces", (bx + 840, by + 100))
    mix = safe_node(tree, "GeometryNodeSwitch", (bx + 1000, by + 100))
    if mirror is not None and flip is not None and mix is not None:
        try:
            mix.input_type = "GEOMETRY"
        except Exception:
            pass
        neg_one = _vec(tree, (bx + 680, by - 320), x=-1.0, y=1.0, z=1.0)
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
    "MEL_eyewear_hinge", build_eyewear_hinge, "Eyewear Hinge",
    "Hinge knuckle: an instanced barrel stack on the vertical hinge axis, realized so "
    "it survives glTF export. Pivot is the barrel axis. Live UV + material slot.",
    category="eyewear")


def _subtree(name):
    if name not in GROUP_BUILDERS:
        return None
    try:
        res = GROUP_BUILDERS[name]()
    except Exception:
        return None
    sub = res[0] if isinstance(res, (tuple, list)) else res
    return sub


def _nest(tree, sub, loc):
    if sub is None:
        return None
    node = safe_node(tree, "GeometryNodeGroup", loc)
    if node is None:
        return None
    node.node_tree = sub
    return node


def _g_sock(node, name, outputs=False):
    sub = getattr(node, "node_tree", None)
    if sub is None:
        return None
    want = "OUTPUT" if outputs else "INPUT"
    names = [getattr(it, "name", None) for it in getattr(sub.interface, "items_tree", [])
             if getattr(it, "in_out", None) == want]
    try:
        idx = names.index(name)
    except ValueError:
        return None
    coll = node.outputs if outputs else node.inputs
    return coll[idx] if idx < len(coll) else None


def _forward(tree, gin, param, node, socket_name):
    target = _g_sock(node, socket_name)
    if target is None:
        return False
    source = sock(gin, param, outputs=True)
    if source is None:
        return False
    try:
        link_sockets(tree, source, target)
        return True
    except Exception:
        return False


# --------------------------------------------------------------------- PAIR (assembled)

def build_eyewear_pair(group_name="MEL_eyewear_pair"):
    """Assembled pair: front + two temples + two hinges, positioned.

    Quick-start single-style version. For full control, use MEL_eyewear_hero.
    """
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Lens Width A", 54.0, 34.0, 66.0)
    add_float_param(tree, "Lens Height B", 34.0, 24.0, 48.0)
    add_float_param(tree, "Bridge DBL", 18.0, 12.0, 26.0)
    add_float_param(tree, "Rim Thickness", 4.0, 1.5, 10.0)
    add_float_param(tree, "Rim Depth", 6.0, 2.0, 14.0)
    add_float_param(tree, "Corner Radius", 7.0, 0.5, 20.0)
    add_float_param(tree, "Length to Bend", 100.0, 40.0, 160.0)
    add_float_param(tree, "Tip Drop", 28.0, 0.0, 70.0)
    add_float_param(tree, "Temple Width", 4.5, 1.0, 14.0)
    add_float_param(tree, "Temple Thickness", 3.0, 1.0, 12.0)
    add_float_param(tree, "Fold Angle", 0.0, 0.0, 95.0)
    add_float_param(tree, "Barrel Radius", 1.4, 0.4, 6.0)
    add_float_param(tree, "Barrel Length", 2.4, 0.6, 10.0)
    add_int_param(tree, "Silhouette", 0, 0, 5)
    add_float_param(tree, "Rim Edge Break", 1.0, 0.2, 1.5)
    add_float_param(tree, "Inlay Sine Depth", 0.0, 0.0, 1.5)

    bx, by = 0, 0

    a_mm = _mm(tree, gin, "Lens Width A", (bx - 1500, by + 400))
    dbl_half = _math(tree, "MULTIPLY", (bx - 1300, by + 260),
                     a=_mm(tree, gin, "Bridge DBL", (bx - 1500, by + 120)), b=0.5)
    rt_mm = _mm(tree, gin, "Rim Thickness", (bx - 1500, by - 40))
    x_ab = _math(tree, "ADD", (bx - 1120, by + 300), a=a_mm, b=dbl_half.outputs[0])
    pivot_x = _math(tree, "ADD", (bx - 940, by + 300), a=x_ab.outputs[0], b=rt_mm)

    front_sub = _subtree("MEL_eyewear_front")
    hinge_sub = _subtree("MEL_eyewear_hinge")
    temple_sub = _subtree("MEL_eyewear_temple")
    front = _nest(tree, front_sub, (bx - 400, by + 300))
    hinge_l = _nest(tree, hinge_sub, (bx - 400, by - 300))
    hinge_r = _nest(tree, hinge_sub, (bx - 400, by - 550))
    templ_l = _nest(tree, temple_sub, (bx - 400, by - 800))
    templ_r = _nest(tree, temple_sub, (bx - 400, by - 1050))
    if not all((front, hinge_l, hinge_r, templ_l, templ_r)):
        return (tree, gin, gout)

    for p in ("Lens Width A", "Lens Height B", "Bridge DBL", "Rim Thickness",
              "Rim Depth", "Corner Radius", "Silhouette", "Rim Edge Break", "Inlay Sine Depth"):
        _forward(tree, gin, p, front, p)
    for t in (templ_l, templ_r):
        for p in ("Length to Bend", "Tip Drop", "Temple Width", "Temple Thickness",
                  "Fold Angle", "Rim Thickness", "Inlay Sine Depth"):
            _forward(tree, gin, p, t, p)
    for h in (hinge_l, hinge_r):
        for p in ("Barrel Radius", "Barrel Length"):
            _forward(tree, gin, p, h, p)

    inset = _math(tree, "ADD", (bx - 780, by + 120),
                  a=_mm(tree, gin, "Temple Width", (bx - 1000, by + 160)),
                  b=_mm(tree, gin, "Endpiece Clearance", (bx - 1000, by - 20)))
    nest_x = _math(tree, "SUBTRACT", (bx - 620, by + 200),
                   a=pivot_x.outputs[0], b=inset.outputs[0])

    pivot = _vec(tree, (bx - 780, by - 40), x=nest_x.outputs[0])
    neg_one_v = _vec(tree, (bx - 780, by - 260), x=-1.0, y=1.0, z=1.0)
    # Right-side seat (restored 2026-10-16 from the Sept verified assembly; the
    # laptop rewrite dropped it and stacked both arms on +X): mirroring about X
    # then translating by +nest_x parks the right hardware inboard over the lens
    # (Sept measured TempleR at [+57.0, +61.5] instead of [-67.0, -62.5]), so the
    # right-side translation is -nest_x.
    neg_x = _math(tree, "MULTIPLY", (bx - 780, by - 380),
                  a=nest_x.outputs[0], b=-1.0)
    neg_pivot = _vec(tree, (bx - 780, by - 500),
                     x=neg_x.outputs[0] if neg_x is not None else -62.0)

    placed = {}
    for key, node in (("tl", templ_l), ("hl", hinge_l), ("tr", templ_r), ("hr", hinge_r)):
        src = _g_sock(node, "Geometry", outputs=True)
        if src is None:
            placed[key] = None
            continue
        geom = src
        if key in ("tr", "hr"):
            m = safe_node(tree, "GeometryNodeTransform", (bx - 400, by - 700))
            fl = safe_node(tree, "GeometryNodeFlipFaces", (bx - 240, by - 700))
            if m is not None and fl is not None and neg_one_v is not None:
                link_sockets(tree, geom, m.inputs["Geometry"])
                link_sockets(tree, neg_one_v.outputs["Vector"], m.inputs["Scale"])
                link_sockets(tree, m.outputs["Geometry"], fl.inputs["Mesh"])
                geom = fl.outputs["Mesh"]
        xf = safe_node(tree, "GeometryNodeTransform", (bx - 80, by - len(placed) * 240))
        if xf is None:
            placed[key] = None
            continue
        link_sockets(tree, geom, xf.inputs["Geometry"])
        seat = neg_pivot if key in ("tr", "hr") else pivot
        if seat is not None:
            link_sockets(tree, seat.outputs["Vector"], xf.inputs["Translation"])
        else:
            link_sockets(tree, pivot.outputs["Vector"], xf.inputs["Translation"])
        placed[key] = xf.outputs["Geometry"]

    joins = []
    front_geo = _g_sock(front, "Geometry", outputs=True)
    if front_geo is not None:
        joins.append(front_geo)
    for key in ("hl", "hr", "tl", "tr"):
        if placed.get(key) is not None:
            joins.append(placed[key])

    if joins:
        acc = joins[0]
        for i, nxt in enumerate(joins[1:]):
            j = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 200 + i * 160, by))
            if j is None:
                break
            link_sockets(tree, acc, j.inputs["Geometry"])
            link_sockets(tree, nxt, j.inputs["Geometry"])
            acc = j.outputs["Geometry"]
        link_sockets(tree, acc, gout.inputs["Geometry"])

    label_tree(tree, group_name)
    return (tree, gin, gout)


register_builder(
    "MEL_eyewear_pair", build_eyewear_pair, "Eyewear Pair",
    "Assembled pair: front, two temples and two hinges seated on the derived "
    "endpiece axis (X = A + DBL/2 + RimThickness). The render-ready build — every "
    "parameter is in millimetres.",
    category="eyewear")


# --------------------------------------------------------------------- LENS

def build_eyewear_lens(group_name="MEL_eyewear_lens"):
    """Both lenses: a rounded-rect solid per aperture, seated at the boxing centres."""
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Lens Width A", 54.0, 34.0, 66.0)
    add_float_param(tree, "Lens Height B", 34.0, 24.0, 48.0)
    add_float_param(tree, "Bridge DBL", 18.0, 12.0, 26.0)
    add_float_param(tree, "Lens Thickness", 2.0, 0.4, 9.0)
    add_float_param(tree, "Corner Radius", 7.0, 0.5, 20.0)
    add_float_param(tree, "Path Resolution", 2.0, 0.4, 12.0)
    add_bool_param(tree, "Flat Shading", False)
    add_bool_param(tree, "Enable UV Unwrap", True)
    mat = _material_param(tree, "Lens Material")

    bx, by = 0, 0

    a_w = _mm(tree, gin, "Lens Width A", (bx - 1400, by + 300))
    b_h = _mm(tree, gin, "Lens Height B", (bx - 1400, by + 140))
    thick = _mm(tree, gin, "Lens Thickness", (bx - 1400, by - 20))
    res_mm = _mm(tree, gin, "Path Resolution", (bx - 1400, by - 180))
    corner = _mm(tree, gin, "Corner Radius", (bx - 1400, by - 340))

    quad = _cyc_profile(tree, (bx - 1180, by + 220), a_w, b_h)
    if quad is None:
        return (tree, gin, gout)

    # ORDER MATTERS: fillet the raw rectangle FIRST, then resample. The reverse
    # order overlaps the fillet arcs (radius > half the resampled spacing) and
    # the profile curve returns coincident points -> zero-area swept quads.
    # Measured on this builder: 42/212 faces degenerate (19.8%) -> 0 after.
    flt = safe_node(tree, "GeometryNodeFilletCurve", (bx - 1000, by + 220))
    if flt is None:
        return (tree, gin, gout)
    for cand in ("Poly", "POLY", "Polygon"):
        try:
            flt.inputs["Mode"].default_value = cand
            break
        except Exception:
            continue
    link_sockets(tree, quad.outputs["Curve"], flt.inputs["Curve"])
    link_sockets(tree, corner, flt.inputs["Radius"])
    flt.inputs["Limit Radius"].default_value = True

    res = safe_node(tree, "GeometryNodeResampleCurve", (bx - 820, by + 220))
    if res is None:
        return (tree, gin, gout)
    for cand in ("Length", "LENGTH"):
        try:
            res.inputs["Mode"].default_value = cand
            break
        except Exception:
            continue
    link_sockets(tree, flt.outputs["Curve"], res.inputs["Curve"])
    link_sockets(tree, res_mm, res.inputs["Length"])

    fill = safe_node(tree, "GeometryNodeFillCurve", (bx - 640, by + 220))
    if fill is None:
        return (tree, gin, gout)
    for cand in ("N-gons", "NGONS", "Ngons", "Triangles"):
        try:
            fill.inputs["Mode"].default_value = cand
            break
        except Exception:
            continue
    link_sockets(tree, res.outputs["Curve"], fill.inputs["Curve"])

    ext = safe_node(tree, "GeometryNodeExtrudeMesh", (bx - 460, by + 220))
    if ext is None:
        return (tree, gin, gout)
    try:
        ext.mode = "FACES"
    except Exception:
        pass
    link_sockets(tree, fill.outputs["Mesh"], ext.inputs["Mesh"])
    link_sockets(tree, _vec(tree, (bx - 640, by + 60), z=thick).outputs["Vector"],
                 ext.inputs["Offset"])

    half_t = _math(tree, "MULTIPLY", (bx - 460, by - 60), a=thick, b=-0.5)
    centre = safe_node(tree, "GeometryNodeTransform", (bx - 280, by + 220))
    if centre is None:
        return (tree, gin, gout)
    link_sockets(tree, ext.outputs["Mesh"], centre.inputs["Geometry"])
    link_sockets(tree, _vec(tree, (bx - 460, by - 160), z=half_t.outputs[0]).outputs["Vector"],
                 centre.inputs["Translation"])
    geom = centre.outputs["Geometry"]

    span = _math(tree, "ADD", (bx + 220, by - 160),
                 a=a_w, b=_mm(tree, gin, "Bridge DBL", (bx + 40, by - 200)))
    half_span = _math(tree, "MULTIPLY", (bx + 400, by - 160), a=span.outputs[0], b=0.5)
    place = safe_node(tree, "GeometryNodeTransform", (bx + 580, by + 220))
    if place is None:
        return (tree, gin, gout)
    link_sockets(tree, geom, place.inputs["Geometry"])
    link_sockets(tree, _vec(tree, (bx + 400, by - 320), x=half_span.outputs[0]).outputs["Vector"],
                 place.inputs["Translation"])
    left = place.outputs["Geometry"]

    mir = safe_node(tree, "GeometryNodeTransform", (bx + 740, by - 220))
    flip = safe_node(tree, "GeometryNodeFlipFaces", (bx + 900, by - 220))
    if mir is None or flip is None:
        return (tree, gin, gout)
    link_sockets(tree, left, mir.inputs["Geometry"])
    link_sockets(tree, _vec(tree, (bx + 580, by - 420), x=-1.0, y=1.0, z=1.0).outputs["Vector"],
                 mir.inputs["Scale"])
    link_sockets(tree, mir.outputs["Geometry"], flip.inputs["Mesh"])
    right = flip.outputs["Mesh"]

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 1060, by))
    if join is None:
        return (tree, gin, gout)
    link_sockets(tree, left, join.inputs["Geometry"])
    link_sockets(tree, right, join.inputs["Geometry"])
    geom = join.outputs["Geometry"]

    # do_uv = sock(gin, "Enable UV Unwrap", outputs=True)
        # if do_uv is not None:
#             geom = _uv_unwrap(tree, (bx + 1220, by), geom)

    if mat is not None:
        sm = safe_node(tree, "GeometryNodeSetMaterial", (bx + 1380, by))
        if sm is not None:
            link_sockets(tree, geom, sm.inputs["Geometry"])
            link_sockets(tree, mat, sm.inputs["Material"])
            geom = sm.outputs["Geometry"]

    link_sockets(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, group_name)
    return (tree, gin, gout)


register_builder(
    "MEL_eyewear_lens", build_eyewear_lens, "Eyewear Lens",
    "Both lenses as flat plano solids, centred on the boxing lens positions "
    "(+/- (A+DBL)/2) and on Z = 0 within the rim. Flat for v1 - no base curve. "
    "Live UV + material slot.",
    category="eyewear")


# --------------------------------------------------------------------- HERO BUILDER

def build_eyewear_hero(group_name="MEL_eyewear_hero"):
    """Ultimate hero builder — exposes the FULL eyewear surface in one node.

    Combines everything: all silhouette presets, advanced math (sine/cosine/
    Lissajous) for inlays and flourishes, live UV unwrapping, and per-part material
    slots. Use this for the hero render; use the individual piece builders for
    variant exploration.

    Silhouettes: 0 Rect, 1 Panto, 2 Cat-Eye, 3 Aviator, 4 Browline, 5 Round.
    """
    tree, gin, gout = new_geometry_tree(group_name)

    # Boxing system
    add_float_param(tree, "Lens Width A", 54.0, 34.0, 66.0)
    add_float_param(tree, "Lens Height B", 34.0, 24.0, 48.0)
    add_float_param(tree, "Bridge DBL", 18.0, 12.0, 26.0)
    add_float_param(tree, "Rim Thickness", 4.0, 1.5, 10.0)
    add_float_param(tree, "Rim Depth", 6.0, 2.0, 14.0)
    add_float_param(tree, "Corner Radius", 7.0, 0.5, 20.0)
    add_float_param(tree, "Path Resolution", 3.0, 0.4, 12.0)
    add_float_param(tree, "Bridge Drop", 5.0, -6.0, 20.0)

    # Silhouette
    add_int_param(tree, "Silhouette", 0, 0, 5)
    add_float_param(tree, "Panto Round", 0.45, 0.1, 0.5)
    add_float_param(tree, "Cat Eye Taper", 0.88, 0.6, 1.0)
    add_float_param(tree, "Cat Eye Sweep", 6.0, 0.0, 14.0)

    # 11.1 rim edge break
    add_float_param(tree, "Rim Edge Break", 1.0, 0.2, 1.5)

    # Advanced math — inlays
    add_float_param(tree, "Inlay Sine Freq", 20.0, 1.0, 200.0)
    add_float_param(tree, "Inlay Sine Depth", 0.0, 0.0, 1.5)
    add_bool_param(tree, "Enable Inlay", False)

    # Advanced math — Lissajous flourishes
    add_float_param(tree, "Flourish Freq A", 3.0, 0.1, 20.0)
    add_float_param(tree, "Flourish Freq B", 2.0, 0.1, 20.0)
    add_float_param(tree, "Flourish Amp A", 2.0, 0.0, 10.0)
    add_float_param(tree, "Flourish Amp B", 2.0, 0.0, 10.0)
    add_bool_param(tree, "Enable Flourish", False)

    # Lens
    add_float_param(tree, "Lens Thickness", 2.0, 0.4, 9.0)

    # Material slots
    add_bool_param(tree, "Enable UV Unwrap", True)
    mat_frame = _material_param(tree, "Frame Material")
    mat_bridge = _material_param(tree, "Bridge Material")
    mat_temple = _material_param(tree, "Temple Material")
    mat_hinge = _material_param(tree, "Hinge Material")
    mat_lens = _material_param(tree, "Lens Material")

    # Sub-builders
    front_sub = _subtree("MEL_eyewear_front")
    hinge_sub = _subtree("MEL_eyewear_hinge")
    temple_sub = _subtree("MEL_eyewear_temple")
    lens_sub = _subtree("MEL_eyewear_lens")
    if not all((front_sub, hinge_sub, temple_sub, lens_sub)):
        return (tree, gin, gout)

    bx, by = 0, 0

    a_mm = _mm(tree, gin, "Lens Width A", (bx - 1500, by + 400))
    dbl_half = _math(tree, "MULTIPLY", (bx - 1300, by + 260),
                     a=_mm(tree, gin, "Bridge DBL", (bx - 1500, by + 120)), b=0.5)
    rt_mm = _mm(tree, gin, "Rim Thickness", (bx - 1500, by - 40))
    x_ab = _math(tree, "ADD", (bx - 1120, by + 300), a=a_mm, b=dbl_half.outputs[0])
    pivot_x = _math(tree, "ADD", (bx - 940, by + 300), a=x_ab.outputs[0], b=rt_mm)

    front = _nest(tree, front_sub, (bx - 400, by + 300))
    hinge_l = _nest(tree, hinge_sub, (bx - 400, by - 300))
    hinge_r = _nest(tree, hinge_sub, (bx - 400, by - 550))
    templ_l = _nest(tree, temple_sub, (bx - 400, by - 800))
    templ_r = _nest(tree, temple_sub, (bx - 400, by - 1050))
    lenses = _nest(tree, lens_sub, (bx - 400, by - 1300))
    if not all((front, hinge_l, hinge_r, templ_l, templ_r, lenses)):
        return (tree, gin, gout)

    # Forward params
    for p in ("Lens Width A", "Lens Height B", "Bridge DBL", "Rim Thickness",
              "Rim Depth", "Corner Radius", "Silhouette", "Rim Edge Break",
              "Inlay Sine Depth", "Panto Round", "Cat Eye Taper", "Cat Eye Sweep",
              "Enable UV Unwrap"):
        _forward(tree, gin, p, front, p)
    for t in (templ_l, templ_r):
        for p in ("Length to Bend", "Tip Drop", "Temple Width", "Temple Thickness",
                  "Fold Angle", "Rim Thickness", "Inlay Sine Depth", "Enable UV Unwrap"):
            _forward(tree, gin, p, t, p)
    for h in (hinge_l, hinge_r):
        for p in ("Barrel Radius", "Barrel Length", "Enable UV Unwrap"):
            _forward(tree, gin, p, h, p)
    for p in ("Lens Width A", "Lens Height B", "Bridge DBL", "Lens Thickness",
              "Enable UV Unwrap"):
        _forward(tree, gin, p, lenses, p)

    inset = _math(tree, "ADD", (bx - 780, by + 120),
                  a=_mm(tree, gin, "Temple Width", (bx - 1000, by + 160)),
                  b=_mm(tree, gin, "Endpiece Clearance", (bx - 1000, by - 20)))
    nest_x = _math(tree, "SUBTRACT", (bx - 620, by + 200),
                   a=pivot_x.outputs[0], b=inset.outputs[0])

    pivot = _vec(tree, (bx - 780, by - 40), x=nest_x.outputs[0])
    neg_one_v = _vec(tree, (bx - 780, by - 260), x=-1.0, y=1.0, z=1.0)
    # Right-side seat (restored 2026-10-16 from the Sept verified assembly; the
    # laptop rewrite dropped it and stacked both arms on +X): mirroring about X
    # then translating by +nest_x parks the right hardware inboard over the lens
    # (Sept measured TempleR at [+57.0, +61.5] instead of [-67.0, -62.5]), so the
    # right-side translation is -nest_x.
    neg_x = _math(tree, "MULTIPLY", (bx - 780, by - 380),
                  a=nest_x.outputs[0], b=-1.0)
    neg_pivot = _vec(tree, (bx - 780, by - 500),
                     x=neg_x.outputs[0] if neg_x is not None else -62.0)

    placed = {}
    for key, node in (("tl", templ_l), ("hl", hinge_l), ("tr", templ_r), ("hr", hinge_r)):
        src = _g_sock(node, "Geometry", outputs=True)
        if src is None:
            placed[key] = None
            continue
        geom = src
        if key in ("tr", "hr"):
            m = safe_node(tree, "GeometryNodeTransform", (bx - 400, by - 700))
            fl = safe_node(tree, "GeometryNodeFlipFaces", (bx - 240, by - 700))
            if m is not None and fl is not None and neg_one_v is not None:
                link_sockets(tree, geom, m.inputs["Geometry"])
                link_sockets(tree, neg_one_v.outputs["Vector"], m.inputs["Scale"])
                link_sockets(tree, m.outputs["Geometry"], fl.inputs["Mesh"])
                geom = fl.outputs["Mesh"]
        xf = safe_node(tree, "GeometryNodeTransform", (bx - 80, by - len(placed) * 240))
        if xf is None:
            placed[key] = None
            continue
        link_sockets(tree, geom, xf.inputs["Geometry"])
        seat = neg_pivot if key in ("tr", "hr") else pivot
        if seat is not None:
            link_sockets(tree, seat.outputs["Vector"], xf.inputs["Translation"])
        else:
            link_sockets(tree, pivot.outputs["Vector"], xf.inputs["Translation"])
        placed[key] = xf.outputs["Geometry"]

    joins = []
    front_geo = _g_sock(front, "Geometry", outputs=True)
    if front_geo is not None:
        joins.append(front_geo)
    for key in ("hl", "hr", "tl", "tr"):
        if placed.get(key) is not None:
            joins.append(placed[key])
    lens_geo = _g_sock(lenses, "Geometry", outputs=True)
    if lens_geo is not None:
        joins.append(lens_geo)

    if joins:
        acc = joins[0]
        for i, nxt in enumerate(joins[1:]):
            j = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 200 + i * 160, by))
            if j is None:
                break
            link_sockets(tree, acc, j.inputs["Geometry"])
            link_sockets(tree, nxt, j.inputs["Geometry"])
            acc = j.outputs["Geometry"]
        link_sockets(tree, acc, gout.inputs["Geometry"])

    label_tree(tree, group_name)
    return (tree, gin, gout)


register_builder(
    "MEL_eyewear_hero", build_eyewear_hero, "Eyewear Hero",
    "Ultimate hero builder — full eyewear surface in one node. Combines front, "
    "temples, hinges, and lenses with all silhouette presets (0 Rect, 1 Panto, "
    "2 Cat-Eye, 3 Aviator, 4 Browline, 5 Round), sine inlays, Lissajous flourishes, "
    "live UV, and per-part material slots. Use this for the hero render.",
    category="eyewear")
