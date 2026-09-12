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
import json
import os
import struct

from .core import (
    GROUP_BUILDERS, add_bool_param, add_float_param, add_int_param, add_vector_param,
    label_tree, link_sockets, make_group_input, make_group_output, new_geometry_tree,
    register_builder, safe_node, sock,
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


def build_eyewear_tortoise(group_name="MEL_eyewear_tortoise"):
    """Chainable COLOR_0 writer (11.6): tortoise marbling over a solid base.

    out = mix(Solid, marble(Position * Scale), Amount). Amount 0 writes the
    solid alone (today's look, and the ensure step that guarantees every part
    carries Col so joined meshes never inherit a black default).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    make_group_input(tree, "NodeSocketColor", "Solid", default=TORTOISE_SOLID)
    add_float_param(tree, "Amount", 0.0, 0.0, 1.0)
    add_float_param(tree, "Scale", 250.0, 10.0, 2000.0)

    bx, by = 0, 0
    done = False
    try:
        pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 600, by))
        noise = safe_node(tree, "ShaderNodeTexNoise", (bx - 420, by))
        link_sockets(tree, sock(pos, "Position", outputs=True),
                     sock(noise, "Vector"))
        link_sockets(tree, sock(gin, "Scale", outputs=True),
                     sock(noise, "Scale"))
        try:
            sock(noise, "Detail").default_value = 3.0
        except Exception:
            pass
        marble = None
        try:
            # Noise Fac concentrates mid-range, which would leave the ramp's
            # dark/honey ends unsampled (measured marble stuck in [0.22, 0.6]).
            # Remap 0.2..0.8 -> 0..1 (clamped) so the full stop range expresses.
            fac = sock(noise, "Fac", outputs=True)
            mr = safe_node(tree, "ShaderNodeMapRange", (bx - 330, by))
            _typed(mr, "From Min", "VALUE").default_value = 0.2
            _typed(mr, "From Max", "VALUE").default_value = 0.8
            link_sockets(tree, fac, _typed(mr, "Value", "VALUE"))
            marble = _ramp(tree, _typed(mr, "Result", "VALUE", outputs=True),
                           TORTOISE_STOPS, (bx - 240, by))
        except Exception:
            marble = _ramp(tree, sock(noise, "Fac", outputs=True),
                           TORTOISE_STOPS, (bx - 240, by))
        mixed = _mix_rgba(tree, sock(gin, "Amount", outputs=True),
                          sock(gin, "Solid", outputs=True), marble,
                          (bx - 60, by))
        out = _store_col(tree, sock(gin, "Geometry", outputs=True), mixed,
                         (bx + 140, by))
        link_sockets(tree, out, gout.inputs["Geometry"])
        done = out is not None
    except Exception:
        done = False
    if not done:
        link_sockets(tree, sock(gin, "Geometry", outputs=True),
                     gout.inputs["Geometry"])
    label_tree(tree, group_name)
    return (tree, gin, gout)


register_builder(
    "MEL_eyewear_tortoise", build_eyewear_tortoise, "Eyewear Tortoise",
    "Chainable COLOR_0 writer: tortoise marbling over Solid "
    "(Amount 0 = solid).",
    category="eyewear")


def build_eyewear_lens_gradient(group_name="MEL_eyewear_lens_gradient"):
    """Chainable COLOR_0 writer (11.6): vertical lens tint, Top at +Y.

    t = MapRange(Y, -HalfHeight, +HalfHeight -> 0, 1); out = mix(Bottom, Top, t).
    Equal tints = uniform (today's look).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    make_group_input(tree, "NodeSocketColor", "Top Tint", default=LENS_TINT_DEFAULT)
    make_group_input(tree, "NodeSocketColor", "Bottom Tint", default=LENS_TINT_DEFAULT)
    add_float_param(tree, "Half Height", 17.0, 1.0, 100.0)

    bx, by = 0, 0
    try:
        pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 600, by))
        sepx = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 420, by))
        link_sockets(tree, sock(pos, "Position", outputs=True), sock(sepx, "Vector"))
        half = sock(gin, "Half Height", outputs=True)
        negh = _math(tree, "MULTIPLY", (bx - 420, by - 200), a=half, b=-1.0)
        mr = safe_node(tree, "ShaderNodeMapRange", (bx - 240, by))
        link_sockets(tree, sock(sepx, "Y", outputs=True), _typed(mr, "Value", "VALUE"))
        link_sockets(tree, negh.outputs[0], _typed(mr, "From Min", "VALUE"))
        link_sockets(tree, half, _typed(mr, "From Max", "VALUE"))
        mixed = _mix_rgba(tree, _typed(mr, "Result", "VALUE", outputs=True),
                          sock(gin, "Bottom Tint", outputs=True),
                          sock(gin, "Top Tint", outputs=True), (bx - 60, by))
        out = _store_col(tree, sock(gin, "Geometry", outputs=True), mixed,
                         (bx + 140, by))
        if out is not None:
            link_sockets(tree, out, gout.inputs["Geometry"])
    except Exception:
        link_sockets(tree, sock(gin, "Geometry", outputs=True), gout.inputs["Geometry"])
    label_tree(tree, group_name)
    return (tree, gin, gout)


register_builder(
    "MEL_eyewear_lens_gradient", build_eyewear_lens_gradient, "Eyewear Lens Gradient",
    "Chainable COLOR_0 writer: vertical lens tint (Top at +Y).",
    category="eyewear")


def build_eyewear_uv(group_name="MEL_eyewear_uv"):
    """Chainable UV writer (8.5): dominant-axis box projection -> UVMap.

    Weights w_i = |n_i|^8 / sum (smooth triplanar: no switches, no seams);
    each axis pair bbox-normalized to 0..1, times UV Scale. Stored CORNER
    FLOAT2 'UVMap', which exports as TEXCOORD_0 (measured, uv_api_probe —
    custom names export too, as TEXCOORD_1+, but the canonical first UV
    keeps the Amazon node vocabulary clean).
    NOTE: no Mix node — Mix has no FLOAT2 mode on 5.2 (silently stays FLOAT).
    All blends here are scalar Math or VectorMath SCALE/ADD.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "UV Scale", 1.0, 0.01, 100.0)

    bx, by = 0, 0
    try:
        pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 900, by + 200))
        sepp = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 720, by + 200))
        link_sockets(tree, sock(pos, "Position", outputs=True), sock(sepp, "Vector"))
        xs = sock(sepp, "X", outputs=True)
        ys = sock(sepp, "Y", outputs=True)
        zs = sock(sepp, "Z", outputs=True)

        bb = safe_node(tree, "GeometryNodeBoundBox", (bx - 900, by - 200))
        sepmn = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 720, by - 160))
        sepmx = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 720, by - 320))
        # BoundBox needs its Geometry input: unlinked Min/Max collapse the
        # span guard to 1e-6 and UVs explode to ~1e4 (measured).
        link_sockets(tree, sock(gin, "Geometry", outputs=True), sock(bb, "Geometry"))
        link_sockets(tree, sock(bb, "Min", outputs=True), sock(sepmn, "Vector"))
        link_sockets(tree, sock(bb, "Max", outputs=True), sock(sepmx, "Vector"))

        nrm = safe_node(tree, "GeometryNodeInputNormal", (bx - 900, by + 480))
        absn = safe_node(tree, "ShaderNodeVectorMath", (bx - 720, by + 480))
        try:
            absn.operation = "ABSOLUTE"
        except Exception:
            pass
        link_sockets(tree, sock(nrm, "Normal", outputs=True), sock(absn, "Vector"))
        sepn = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 540, by + 480))
        link_sockets(tree, sock(absn, "Vector", outputs=True), sock(sepn, "Vector"))

        def _vmath(op, a, b, loc):
            vm = safe_node(tree, "ShaderNodeVectorMath", loc)
            if vm is None:
                return None
            try:
                vm.operation = op
            except Exception:
                pass
            try:
                link_sockets(tree, a, vm.inputs[0])
                if b is not None:
                    try:
                        vm.inputs[1]
                    except Exception:
                        return vm
                    link_sockets(tree, b, vm.inputs[1])
            except Exception:
                pass
            return vm

        def _norm1d(sel, mn, mx, loc):
            d = _math(tree, "SUBTRACT", (loc[0], loc[1] + 40), a=sel, b=mn)
            span = _math(tree, "MAXIMUM", (loc[0] + 180, loc[1] + 40),
                         a=_math(tree, "SUBTRACT", (loc[0], loc[1] - 60),
                                 a=mx, b=mn).outputs[0], b=1e-6)
            return _math(tree, "DIVIDE", (loc[0] + 360, loc[1] + 40),
                         a=(d.outputs[0] if d else None),
                         b=(span.outputs[0] if span else None))

        # three planar projections, bbox-normalized
        pxx = _norm1d(ys, sock(sepmn, "Y", outputs=True), sock(sepmx, "Y", outputs=True),
                      (bx - 360, by + 320))
        pxz = _norm1d(zs, sock(sepmn, "Z", outputs=True), sock(sepmx, "Z", outputs=True),
                      (bx - 360, by + 120))
        pyx = _norm1d(xs, sock(sepmn, "X", outputs=True), sock(sepmx, "X", outputs=True),
                      (bx - 360, by - 80))
        pyz = _norm1d(zs, sock(sepmn, "Z", outputs=True), sock(sepmx, "Z", outputs=True),
                      (bx - 360, by - 280))
        pzx = _norm1d(xs, sock(sepmn, "X", outputs=True), sock(sepmx, "X", outputs=True),
                      (bx - 360, by - 480))
        pzy = _norm1d(ys, sock(sepmn, "Y", outputs=True), sock(sepmx, "Y", outputs=True),
                      (bx - 360, by - 680))

        cX = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 180, by + 220))
        link_sockets(tree, pxx.outputs[0], sock(cX, "X"))
        link_sockets(tree, pxz.outputs[0], sock(cX, "Y"))
        cY = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 180, by - 80))
        link_sockets(tree, pyx.outputs[0], sock(cY, "X"))
        link_sockets(tree, pyz.outputs[0], sock(cY, "Y"))
        cZ = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 180, by - 380))
        link_sockets(tree, pzx.outputs[0], sock(cZ, "X"))
        link_sockets(tree, pzy.outputs[0], sock(cZ, "Y"))

        # smooth triplanar weights, guarded divide
        p8 = 8.0
        wx = _math(tree, "POWER", (bx - 360, by + 560),
                   a=sock(sepn, "X", outputs=True), b=p8)
        wy = _math(tree, "POWER", (bx - 180, by + 560),
                   a=sock(sepn, "Y", outputs=True), b=p8)
        wz = _math(tree, "POWER", (bx, by + 560),
                   a=sock(sepn, "Z", outputs=True), b=p8)
        tot = _math(tree, "ADD", (bx + 180, by + 560),
                    a=_math(tree, "ADD", (bx, by + 640),
                            a=wx.outputs[0], b=wy.outputs[0]).outputs[0],
                    b=wz.outputs[0])
        den = _math(tree, "ADD", (bx + 360, by + 560), a=tot.outputs[0], b=1e-6)
        fx = _math(tree, "DIVIDE", (bx + 540, by + 560), a=wx.outputs[0], b=den.outputs[0])
        fy = _math(tree, "DIVIDE", (bx + 540, by + 440), a=wy.outputs[0], b=den.outputs[0])
        fz = _math(tree, "DIVIDE", (bx + 540, by + 320), a=wz.outputs[0], b=den.outputs[0])

        def _wscale(vec_out, w, loc):
            vm = safe_node(tree, "ShaderNodeVectorMath", loc)
            if vm is None:
                return None
            try:
                vm.operation = "SCALE"
            except Exception:
                pass
            try:
                link_sockets(tree, vec_out, vm.inputs[0])
                link_sockets(tree, w.outputs[0], sock(vm, "Scale"))
                return vm.outputs["Vector"]
            except Exception:
                return None

        tX = _wscale(sock(cX, "Vector", outputs=True), fx, (bx + 720, by + 220))
        tY = _wscale(sock(cY, "Vector", outputs=True), fy, (bx + 720, by - 80))
        tZ = _wscale(sock(cZ, "Vector", outputs=True), fz, (bx + 720, by - 380))
        tXY = _vmath("ADD", tX, tY, (bx + 900, by))
        tXYZ = _vmath("ADD", (tXY.outputs["Vector"] if tXY else None), tZ,
                      (bx + 1080, by))
        uv = safe_node(tree, "ShaderNodeVectorMath", (bx + 1260, by))
        try:
            uv.operation = "SCALE"
        except Exception:
            pass
        link_sockets(tree, (tXYZ.outputs["Vector"] if tXYZ else None), uv.inputs[0])
        link_sockets(tree, sock(gin, "UV Scale", outputs=True), sock(uv, "Scale"))

        st = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 1440, by))
        try:
            st.data_type = "FLOAT2"
        except Exception:
            pass
        try:
            st.domain = "CORNER"
        except Exception:
            pass
        try:
            sock(st, "Name").default_value = "UVMap"
        except Exception:
            pass
        link_sockets(tree, sock(gin, "Geometry", outputs=True), sock(st, "Geometry"))
        link_sockets(tree, uv.outputs["Vector"], sock(st, "Value"))
        link_sockets(tree, st.outputs["Geometry"], gout.inputs["Geometry"])
    except Exception:
        link_sockets(tree, sock(gin, "Geometry", outputs=True), gout.inputs["Geometry"])
    label_tree(tree, group_name)
    return (tree, gin, gout)


register_builder(
    "MEL_eyewear_uv", build_eyewear_uv, "Eyewear UV",
    "Chainable UV writer (8.5): dominant-axis box projection -> UVMap "
    "(TEXCOORD_0).",
    category="eyewear")


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

    # 8.1 silhouettes. Every shape stays INSCRIBED in the same w x h box, so the boxing
    # contract (outer width 2A + DBL + 2 Rim Thickness) is invariant across them and the
    # existing 134.000 measurement still pins the aperture. 0 Rect, 1 Round/Panto,
    # 2 Cat-Eye.
    add_int_param(tree, "Silhouette", 0, 0, 2)
    add_float_param(tree, "Panto Round", 0.45, 0.1, 0.5)
    add_float_param(tree, "Cat Eye Taper", 0.88, 0.6, 1.0)
    add_float_param(tree, "Cat Eye Sweep", 6.0, 0.0, 14.0)
    # 11.1 rim edge break. Every real frame is tumbled, not modelled with a rounded edge;
    # 0.5-1.0 mm acetate and 0.2-0.5 mm metal are inference from the tumbling process, not
    # a published radius. Constructed into the profile - GeometryNodeMeshBevel is measured
    # unusable on this build (0.3 mm took a 54 mm lens to 322 mm).
    add_float_param(tree, "Rim Edge Break", 1.0, 0.2, 1.5)
    # 11.2 base curve + frame form. Defaults 0/0 keep today's verified flat
    # look bit-exact (pure-Z fields; X/Y untouched); the editorial set passes
    # explicit values (Base Curve 4-6, Form Angle ~4.4).
    add_float_param(tree, "Base Curve", 0.0, 0.0, 8.0)
    add_float_param(tree, "Form Angle", 0.0, 0.0, 25.0)

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

    # rounded rim cross-section: resample so the fillet has a vertex to work with, then
    # fillet with Limit Radius on so the break cannot consume a whole face (clamp is
    # half the shortest edge - 2.0 mm for the 4.0 x 6.0 default profile)
    prof_out = prof.outputs["Curve"]
    p_res = safe_node(tree, "GeometryNodeResampleCurve", (bx - 760, by - 300))
    p_flt = safe_node(tree, "GeometryNodeFilletCurve", (bx - 620, by - 300))
    if p_res is not None and p_flt is not None:
        for cand in ("Length", "LENGTH"):
            try:
                p_res.inputs["Mode"].default_value = cand
                break
            except Exception:
                continue
        link_sockets(tree, prof_out, p_res.inputs["Curve"])
        link_sockets(tree, _mm(tree, gin, "Rim Edge Break", (bx - 900, by - 460), scale=0.5),
                     p_res.inputs["Length"])
        for cand in ("Poly", "POLY", "Polygon"):
            try:
                p_flt.inputs["Mode"].default_value = cand
                break
            except Exception:
                continue
        link_sockets(tree, p_res.outputs["Curve"], p_flt.inputs["Curve"])
        link_sockets(tree, _mm(tree, gin, "Rim Edge Break", (bx - 900, by - 560)),
                     p_flt.inputs["Radius"])
        p_flt.inputs["Limit Radius"].default_value = True
        prof_out = p_flt.outputs["Curve"]

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

        # --- 8.1 silhouette branch -------------------------------------------
        # Cat-eye as a TRAPEZOID (measured on 5.2: Width not used, Bottom Width / Top
        # Width / Offset are - Top Width is centred on Offset). Top Width = w - 2*Sweep
        # and Offset = Sweep put the swept top edge exactly on +w/2, so the box is
        # unchanged and the 134.000 assertion still pins the aperture.
        sweep_mm = _mm(tree, gin, "Cat Eye Sweep", (x0 - 820, y0 + 620))
        taper = _math(tree, "MULTIPLY", (x0 - 820, y0 + 520),
                      a=w.outputs[0], b=sock(gin, "Cat Eye Taper", outputs=True))
        two_sweep = _math(tree, "MULTIPLY", (x0 - 820, y0 + 720), a=sweep_mm, b=2.0)
        top_w = _math(tree, "SUBTRACT", (x0 - 700, y0 + 700),
                      a=w.outputs[0], b=two_sweep.outputs[0] if two_sweep else None)
        quad_ce = safe_node(tree, "GeometryNodeCurvePrimitiveQuadrilateral", (x0 - 420, y0 + 500))
        if quad_ce is not None:
            try:
                quad_ce.mode = "TRAPEZOID"
            except Exception:
                pass
            link_sockets(tree, top_w.outputs[0], quad_ce.inputs["Top Width"])
            link_sockets(tree, taper.outputs[0], quad_ce.inputs["Bottom Width"])
            link_sockets(tree, h.outputs[0], quad_ce.inputs["Height"])
            sign = -1.0 if y_flip else 1.0
            sgn = _math(tree, "MULTIPLY", (x0 - 700, y0 + 420), a=sweep_mm, b=sign)
            if sgn is not None:
                link_sockets(tree, sgn.outputs[0], quad_ce.inputs["Offset"])

        sw_geo = safe_node(tree, "GeometryNodeIndexSwitch", (x0 - 300, y0 + 460))
        shape_out = quad.outputs["Curve"]
        if sw_geo is not None:
            try:
                sw_geo.data_type = "GEOMETRY"
            except Exception:
                pass
            while len(sw_geo.index_switch_items) < 3:
                sw_geo.index_switch_items.new()
            link_sockets(tree, sock(gin, "Silhouette", outputs=True), sw_geo.inputs["Index"])
            link_sockets(tree, quad.outputs["Curve"], sw_geo.inputs["0"])
            link_sockets(tree, quad.outputs["Curve"], sw_geo.inputs["1"])
            if quad_ce is not None:
                link_sockets(tree, quad_ce.outputs["Curve"], sw_geo.inputs["2"])
            shape_out = sw_geo.outputs[0]

        # corner radius per shape: 0/2 use the Corner Radius param, 1 (panto) rounds the
        # box as far as Limit Radius allows
        minwh = _math(tree, "MINIMUM", (x0 - 620, y0 + 900),
                      a=w.outputs[0], b=h.outputs[0])
        panto_r = _math(tree, "MULTIPLY", (x0 - 500, y0 + 900),
                        a=minwh.outputs[0], b=sock(gin, "Panto Round", outputs=True))
        corner = _mm(tree, gin, "Corner Radius", (x0 - 620, y0 + 1040))
        sw_rad = safe_node(tree, "GeometryNodeIndexSwitch", (x0 - 340, y0 + 980))
        radius_out = corner
        if sw_rad is not None and corner is not None:
            try:
                sw_rad.data_type = "FLOAT"
            except Exception:
                pass
            while len(sw_rad.index_switch_items) < 3:
                sw_rad.index_switch_items.new()
            link_sockets(tree, sock(gin, "Silhouette", outputs=True), sw_rad.inputs["Index"])
            link_sockets(tree, corner, sw_rad.inputs["0"])
            link_sockets(tree, panto_r.outputs[0], sw_rad.inputs["1"])
            link_sockets(tree, corner, sw_rad.inputs["2"])
            radius_out = sw_rad.outputs[0]

        # Fillet BEFORE resample. Measured: with Resample first, every silhouette edge is
        # diced to Path Resolution (~3 mm), and Fillet's Limit Radius clamps to half the
        # shortest edge - 1.5 mm - so Corner Radius (7 mm) and the panto radius (18.9 mm)
        # both collapsed to the same value and the shape branch measured dead (rect and
        # panto row width identical at 128.257). Filleting the undiced quad lets
        # Limit Radius clamp against the real 42 mm edge (21 mm) instead.
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
        link_sockets(tree, radius_out, flt.inputs["Radius"])
        flt.inputs["Limit Radius"].default_value = True

        # uniform path spacing over the already-rounded corners, so the profile cannot
        # self-intersect inside a turn
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

        # place the lens centre at +/-(A + DBL)/2 so the aperture gap is exactly DBL
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
                link_sockets(tree, prof_out, c2m_b.inputs["Profile Curve"])
                # the rims are cyclic so caps are meaningless there; the bridge is an
                # open span and must be capped to stay manifold. Its two caps are the
                # only n-gons in the result.
                c2m_b.inputs["Fill Caps"].default_value = True
                bridge_geo = c2m_b.outputs["Mesh"]

    # --- combine -------------------------------------------------------------
    # 11.2 post-pass: wrap + base curve as one pure-Z field over the joined
    # front (rims + bridge together, so no seam can open between them).
    _fspan = _math(tree, "ADD", (bx + 140, by + 240),
                     a=_mm(tree, gin, "Lens Width A", (bx - 60, by + 280)),
                     b=_mm(tree, gin, "Bridge DBL", (bx - 60, by + 160)))
    half_span = _math(tree, "MULTIPLY", (bx + 320, by + 240),
                      a=(_fspan.outputs[0] if _fspan is not None else None), b=0.5)
    front_joined = None
    if left is not None and right is not None and bridge_geo is not None:
        j1 = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 500, by))
        if j1 is not None:
            link_sockets(tree, left, j1.inputs["Geometry"])
            link_sockets(tree, right, j1.inputs["Geometry"])
            j2 = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 660, by))
            if j2 is not None:
                link_sockets(tree, j1.outputs["Geometry"], j2.inputs["Geometry"])
                link_sockets(tree, bridge_geo, j2.inputs["Geometry"])
                front_joined = j2.outputs["Geometry"]
    elif left is not None and right is not None:
        j1 = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 500, by))
        if j1 is not None:
            link_sockets(tree, left, j1.inputs["Geometry"])
            link_sockets(tree, right, j1.inputs["Geometry"])
            front_joined = j1.outputs["Geometry"]
    if front_joined is not None and half_span is not None:
        front_joined = _base_curve_field(tree, front_joined, gin,
                                         half_span.outputs[0], (bx + 840, by))
    # NOTE: no finish writer here. _subtree() rebuilds by name, so a writer
    # nested in this intermediate builder would be destroyed when the pair
    # builds its own copy for the shared finish pass. The pair owns ALL
    # tortoise application (see _paint); this builder stays paint-free.
    if front_joined is not None:
        link_sockets(tree, front_joined, gout.inputs["Geometry"])

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


def _subtree(name):
    """Build a registered builder ONCE and return its tree.

    CRITICAL: new_geometry_tree REMOVES and recreates a tree by name. Building the
    same sub-builder twice therefore destroys the tree the first group node was
    pointing at - node_tree goes to None, the output socket disappears, and the
    instance is silently dropped from the join. Build each sub-tree once, then
    share it across as many group nodes as needed.
    """
    if name not in GROUP_BUILDERS:
        print("[eyewear] _subtree: '%s' is not registered" % name)
        return None
    try:
        res = GROUP_BUILDERS[name]()
    except Exception as exc:
        print("[eyewear] _subtree: building '%s' raised %s: %s"
              % (name, type(exc).__name__, exc))
        return None
    sub = res[0] if isinstance(res, (tuple, list)) else res
    if sub is None:
        print("[eyewear] _subtree: '%s' returned no tree" % name)
    return sub


def _nest(tree, sub, loc):
    """One group node pointing at an ALREADY-BUILT sub-tree."""
    if sub is None:
        return None
    node = safe_node(tree, "GeometryNodeGroup", loc)
    if node is None:
        print("[eyewear] _nest: could not create a Group node")
        return None
    node.node_tree = sub
    return node


def _g_sock(node, name, outputs=False):
    """Resolve a nested group node's socket by NAME.

    A Group node's sockets are identified as Socket_0, Socket_1 ... not by the
    parameter name, so they must be mapped through the nested tree's interface.
    Order matches the interface declaration order.
    """
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
    """Drive a nested builder's input from a pair-level parameter."""
    target = _g_sock(node, socket_name)
    if target is None:
        return False
    try:
        link_sockets(tree, sock(gin, param, outputs=True), target)
        return True
    except Exception:
        return False


# ------------------------------------------- 11.4/11.5 pair integrity -----
# 11.4: Join Geometry does not weld, so the assembled pair carried 5688 doubled
# seam verts (measured: 10464 verts collapse to 4776 at a 0.02 mm weld, with
# zero wire edges introduced; 0.05 mm already creates wire — probe
# Tools/eyewear_verify/pair_manifold_probe.py). The weld below is that measured
# value, not a guess.
WELD_DISTANCE_MM = 0.02


def _weld(tree, geom, loc, dist_mm=WELD_DISTANCE_MM):
    """Merge by Distance at a measured threshold (11.4)."""
    if geom is None:
        return None
    mg = safe_node(tree, "GeometryNodeMergeByDistance", loc)
    if mg is None:
        return geom
    try:
        mg.inputs["Distance"].default_value = dist_mm * MM
    except Exception:
        pass
    try:
        link_sockets(tree, geom, sock(mg, "Geometry"))
        return mg.outputs["Geometry"]
    except Exception:
        return geom


def _principled_material(name, base_color, metallic=0.0, roughness=0.5,
                         alpha=None, blend=None):
    """Get-or-create an eyewear material, rebuilt deterministically (11.5/11.6).

    Same convention as materials_kit builders: clear and rebuild so repeated
    builder evaluation cannot stack stale nodes.
    """
    try:
        mat = bpy.data.materials.get(name)
        if mat is None:
            mat = bpy.data.materials.new(name)
    except Exception:
        return None
    try:
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        out.location = (400, 0)
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (100, 0)
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = base_color
        for key, val in (("Metallic", metallic), ("Roughness", roughness)):
            if key in bsdf.inputs:
                try:
                    bsdf.inputs[key].default_value = val
                except Exception:
                    pass
        if alpha is not None and "Alpha" in bsdf.inputs:
            try:
                bsdf.inputs["Alpha"].default_value = alpha
            except Exception:
                pass
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        if blend is not None:
            try:
                mat.blend_method = blend
            except Exception:
                pass
    except Exception:
        pass
    return mat


def _drive_base_from_col(mat):
    """Point a Principled Base Color at the Col attribute (11.6).

    Col IS the display color (solid / marble / gradient per part); the
    authored Base Color stays as the no-attribute fallback. Every part leaves
    the pair builders carrying Col, so the fallback never shows — and the
    export gate asserts it.
    """
    try:
        nt = mat.node_tree
        bsdf = next(n for n in nt.nodes
                    if getattr(n, "bl_idname", "") == "ShaderNodeBsdfPrincipled")
        attr = nt.nodes.new("ShaderNodeAttribute")
        attr.location = (-200, 100)
        try:
            attr.attribute_name = COL_ATTR
        except Exception:
            pass
        nt.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
    except Exception:
        pass


def ensure_eyewear_materials():
    """The four M1 delivery materials (11.6).

    Display color comes from the CORNER COLOR_0 attribute the builders write
    (solid / tortoise marble / lens gradient); the authored Base Color stays
    as the no-attribute fallback. Lens stays clear of
    KHR_materials_transmission: alpha blend only, so three.js pays no extra
    scene render per lens.
    """
    mats = {
        "acetate": _principled_material(
            "MEL_mat_eyewear_acetate", (0.09, 0.055, 0.045, 1.0),
            metallic=0.0, roughness=0.45),
        "metal": _principled_material(
            "MEL_mat_eyewear_metal", (0.95, 0.80, 0.60, 1.0),
            metallic=1.0, roughness=0.28),
        "lens": _principled_material(
            "MEL_mat_eyewear_lens", (0.90, 0.95, 1.0, 1.0),
            metallic=0.0, roughness=0.05, alpha=0.30, blend="BLEND"),
        "silicone": _principled_material(
            "MEL_mat_eyewear_silicone", (0.75, 0.72, 0.70, 1.0),
            metallic=0.0, roughness=0.90),
    }
    for mat in mats.values():
        if mat is not None:
            _drive_base_from_col(mat)
    return mats


def decode_glb_summary(path):
    """Minimal GLB reader for the export gate: per-primitive attributes,
    COLOR_0 stats and triangle counts. Raises on anything unparseable —
    including the classic 176-byte empty file (no JSON chunk survives)."""
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 20:
        raise AssertionError("gate: %s is %d bytes, not a GLB" % (path, len(data)))
    magic, _ver, _ln = struct.unpack("<III", data[:12])
    if magic != 0x46546C67:
        raise AssertionError("gate: %s bad magic %s" % (path, hex(magic)))
    off, js, bn = 12, None, None
    while off < len(data):
        clen, ctype = struct.unpack("<II", data[off:off + 8])
        chunk = data[off + 8:off + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(chunk.decode("utf-8"))
        elif ctype == 0x004E4942:
            bn = chunk
        off += 8 + clen
    if js is None or bn is None:
        raise AssertionError("gate: %s missing JSON/BIN chunks" % path)
    prims = []
    for prim in js["meshes"][0]["primitives"]:
        attrs = list(prim.get("attributes", {}).keys())
        info = {"attrs": attrs, "color0": None, "tris": 0, "verts": 0}
        for key, want in (("COLOR_0", "color0"), ("POSITION", "verts")):
            ai = prim["attributes"].get(key)
            if ai is None:
                continue
            acc = js["accessors"][ai]
            bv = js["bufferViews"][acc["bufferView"]]
            start = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
            n = acc["count"]
            comp = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[acc["type"]]
            vals = struct.unpack("<%df" % (n * comp), bn[start:start + 4 * n * comp])
            if want == "color0":
                r0 = [vals[i * comp] for i in range(n)]
                mean = tuple(sum(vals[i * comp + c] for i in range(n)) / n
                             for c in range(min(comp, 3)))
                info["color0"] = {"mean": mean, "min": min(r0), "max": max(r0),
                                  "count": n}
            else:
                info["verts"] = n
        ii = prim.get("indices")
        if ii is not None:
            info["tris"] = js["accessors"][ii]["count"] // 3
        prims.append(info)
    return {"prims": prims, "bytes": len(data),
            "tris": sum(p["tris"] for p in prims)}


def _set_params(tree, params):
    for name, val in (params or {}).items():
        for it in getattr(tree.interface, "items_tree", []):
            if getattr(it, "name", None) == name:
                try:
                    it.default_value = val
                except Exception:
                    pass
                break


def melodia_eyewear_export_gate(outdir, parts=("Frame", "TempleL", "TempleR",
                                              "LensL", "LensR"),
                                params=None, tri_budget=150000,
                                byte_budget=3 * 1024 * 1024):
    """8.5 export gate: realize + export each part, assert delivery-ready.

    A GN group cannot touch the filesystem, so the gate is a Python-side
    builder over the same bpy export path: fresh pair build with `params`
    applied, one selected-object GLB per part with export_apply=True (the
    export_apply=False empty-file trap fails here by construction), then:
    file non-empty AND TEXCOORD_0 present AND COLOR_0 present with >100
    corners AND tri/byte budgets (Khronos single-item: 150k tris, 3 MB).
    Returns {part: report}; raises AssertionError listing every failure.
    """
    res = GROUP_BUILDERS["MEL_eyewear_pair"]()
    pair_tree = res[0] if isinstance(res, (tuple, list)) else res
    _set_params(pair_tree, params)
    try:
        os.makedirs(outdir, exist_ok=True)
    except Exception as exc:
        raise AssertionError("gate: cannot create %s (%s)" % (outdir, exc))
    report, problems = {}, []
    for part in parts:
        wrap = bpy.data.node_groups.new("__gate__", "GeometryNodeTree")
        try:
            wgi = wrap.nodes.new("NodeGroupInput")
            wgo = wrap.nodes.new("NodeGroupOutput")
            wrap.interface.new_socket(name="Geometry", in_out="INPUT",
                                      socket_type="NodeSocketGeometry")
            wrap.interface.new_socket(name="Geometry", in_out="OUTPUT",
                                      socket_type="NodeSocketGeometry")
            gn = wrap.nodes.new("GeometryNodeGroup")
            gn.node_tree = pair_tree
            wrap.links.new(wgi.outputs["Geometry"], gn.inputs["Geometry"])
            wrap.links.new(gn.outputs[part], wgo.inputs["Geometry"])
            me = bpy.data.meshes.new("__gate__")
            ob = bpy.data.objects.new("__gateo__", me)
            bpy.context.scene.collection.objects.link(ob)
            ob.modifiers.new("m", "NODES").node_group = wrap
            bpy.context.view_layer.update()
            bpy.ops.object.select_all(action="DESELECT")
            ob.select_set(True)
            bpy.context.view_layer.objects.active = ob
            path = os.path.join(outdir, "MEL_eyewear_%s.glb" % part)
            bpy.ops.export_scene.gltf(
                filepath=path, use_selection=True, export_format="GLB",
                export_apply=True, export_texcoords=True, export_normals=True)
            try:
                bpy.data.objects.remove(ob, do_unlink=True)
            except Exception:
                pass
            summary = decode_glb_summary(path)
            row = {"file": path, "bytes": summary["bytes"], "tris": summary["tris"],
                   "prims": len(summary["prims"])}
            report[part] = row
            if summary["bytes"] < 1024:
                problems.append("%s: %d bytes (empty-export trap)" % (part, summary["bytes"]))
            if summary["bytes"] > byte_budget:
                problems.append("%s: %d bytes over budget" % (part, summary["bytes"]))
            if summary["tris"] > tri_budget:
                problems.append("%s: %d tris over budget" % (part, summary["tris"]))
            for pi, prim in enumerate(summary["prims"]):
                if "TEXCOORD_0" not in prim["attrs"]:
                    problems.append("%s prim %d: no TEXCOORD_0 (%s)"
                                    % (part, pi, prim["attrs"]))
                col = prim["color0"]
                if col is None or col["count"] < 100:
                    problems.append("%s prim %d: no usable COLOR_0" % (part, pi))
        except AssertionError:
            raise
        except Exception as exc:
            problems.append("%s: harness error %s: %s" % (part, type(exc).__name__, exc))
        finally:
            try:
                bpy.data.node_groups.remove(wrap)
            except Exception:
                pass
    if problems:
        raise AssertionError("gate FAIL:\n  - " + "\n  - ".join(problems))
    return report


def _apply_material(tree, geom, material, loc):
    """Assign a material to one part's geometry (11.5). Pure pass-through on failure."""
    if geom is None or material is None:
        return geom
    sm = safe_node(tree, "GeometryNodeSetMaterial", loc)
    if sm is None:
        return geom
    try:
        link_sockets(tree, geom, sock(sm, "Geometry"))
        sock(sm, "Material").default_value = material
    except Exception:
        return geom
    try:
        return sm.outputs["Geometry"]
    except Exception:
        return geom


def _split_x_sign(tree, geom, loc):
    """Split one geometry into (x >= 0, x < 0) halves (lens L/R, 11.5).

    Selection is Position.X GREATER_THAN 0 via ShaderNode nodes, the same
    construction family the rest of this module already uses.
    """
    if geom is None:
        return None, None
    x0, y0 = loc
    pos = safe_node(tree, "GeometryNodeInputPosition", (x0, y0))
    sepx = safe_node(tree, "ShaderNodeSeparateXYZ", (x0 + 180, y0))
    if pos is None or sepx is None:
        return None, None
    try:
        link_sockets(tree, sock(pos, "Position", outputs=True),
                     sock(sepx, "Vector"))
        x_sock = sock(sepx, "X", outputs=True)
    except Exception:
        return None, None
    gt = _math(tree, "GREATER_THAN", (x0 + 360, y0), a=x_sock, b=0.0)
    sep = safe_node(tree, "GeometryNodeSeparateGeometry", (x0 + 540, y0))
    if gt is None or sep is None:
        return None, None
    try:
        link_sockets(tree, geom, sock(sep, "Geometry"))
        link_sockets(tree, gt.outputs[0], sock(sep, "Selection"))
        return sep.outputs["Selection"], sep.outputs["Inverted"]
    except Exception:
        return None, None


_SMOOTH_ABS_K = 0.002  # BU (2 mm): smooth-abs knee for the 11.2 fields

# 11.6 sRGB working values. The exporter converts vertex colours on the way
# out (see tortoise_gradient_check.py round-trip pin), so these are authored
# as sRGB and verified against the decoded GLB, never assumed.
TORTOISE_SOLID = (0.09, 0.055, 0.045, 1.0)   # neutral espresso acetate
TORTOISE_STOPS = (  # (position, rgba) marbling across Noise Fac
    (0.00, (0.05, 0.020, 0.010, 1.0)),
    (0.35, (0.28, 0.090, 0.020, 1.0)),
    (0.55, (0.75, 0.420, 0.120, 1.0)),
    (0.72, (0.50, 0.200, 0.050, 1.0)),
    (1.00, (0.04, 0.015, 0.008, 1.0)),
)
LENS_TINT_DEFAULT = (0.90, 0.95, 1.0, 1.0)
CHAMPAGNE = (0.95, 0.80, 0.60, 1.0)
COL_ATTR = "Col"  # Blender default colour-attribute name: exports as COLOR_0


def _typed(node, name, stype, outputs=False):
    """Socket by (name, type). REQUIRED on 5.2 multi-type nodes (Mix exposes
    Factor/A/B/Result in FLOAT, VECTOR, RGBA and ROTATION side by side, all
    sharing names) — name-only lookup silently lands on FLOAT."""
    if node is None:
        return None
    coll = node.outputs if outputs else node.inputs
    try:
        for s in coll:
            if getattr(s, "name", None) == name and getattr(s, "type", None) == stype:
                return s
    except Exception:
        pass
    return None


def _mix_rgba(tree, factor, col_a, col_b, loc):
    """Color mix node (Factor, A, B). Returns the RGBA Result or None."""
    mx = safe_node(tree, "ShaderNodeMix", loc)
    if mx is None:
        return None
    try:
        mx.data_type = "RGBA"
    except Exception:
        pass
    try:
        mx.blend_type = "MIX"
    except Exception:
        pass
    try:
        if factor is not None:
            link_sockets(tree, factor, _typed(mx, "Factor", "VALUE"))
        if col_a is not None:
            link_sockets(tree, col_a, _typed(mx, "A", "RGBA"))
        if col_b is not None:
            link_sockets(tree, col_b, _typed(mx, "B", "RGBA"))
        return _typed(mx, "Result", "RGBA", outputs=True)
    except Exception:
        return None


def _store_col(tree, geom, color_sock, loc, name=COL_ATTR):
    """Write a colour field to a CORNER FLOAT_COLOR attribute (11.6)."""
    if geom is None or color_sock is None:
        return geom
    st = safe_node(tree, "GeometryNodeStoreNamedAttribute", loc)
    if st is None:
        return geom
    try:
        st.data_type = "FLOAT_COLOR"
    except Exception:
        pass
    try:
        st.domain = "CORNER"
    except Exception:
        pass
    try:
        sock(st, "Name").default_value = name
    except Exception:
        pass
    try:
        link_sockets(tree, geom, sock(st, "Geometry"))
        link_sockets(tree, color_sock, sock(st, "Value"))
        return st.outputs["Geometry"]
    except Exception:
        return geom


def _ramp(tree, fac_sock, stops, loc):
    """ValToRGB with explicit stops. Returns outputs['Color'] or None."""
    rp = safe_node(tree, "ShaderNodeValToRGB", loc)
    if rp is None or fac_sock is None:
        return None
    try:
        link_sockets(tree, fac_sock, sock(rp, "Fac"))
        els = rp.color_ramp.elements
        while len(els) < len(stops):
            els.new(0.5)
        for el, (pos, col) in zip(els, stops):
            el.position = pos
            el.color = col
        return rp.outputs["Color"]
    except Exception:
        return None


def _base_curve_field(tree, geom, gin, half_sock, loc,
                      bc_param="Base Curve", form_param="Form Angle"):
    """11.2 base curve + frame form as pure Z fields (no splits, no topology change).

    sag = R - sqrt(max(R^2 - r^2, 0)) with R = 523 / max(BaseCurve, 1e-3) mm
    (plan table: 2 base -> 261.5 mm | 4 -> 130.75 | 6 -> 87.17 | 8 -> 65.38)
    and r^2 = (smooth|x| - half)^2 + y^2 about each eye's boxing centre;
    wrap pushes z -= smooth|x| * sin(Form). smooth|x| = sqrt(x^2 + k^2) - k.

    Why fields, not the plan's per-side rotation: splitting the front at x = 0
    DROPS the ~80 bridge faces straddling the plane (measured,
    split_behavior_probe) — Separate never resurrects them on rejoin. The sag
    needs no sign anyway (distance is even: both sides agree at x = 0), and the
    smoothed abs keeps the wrap continuous and crease-free across the bridge.
    Pure Z by construction, so every X/Y boxing assertion survives untouched.
    At Base Curve 0 the residual sag is ~1e-6 BU; at Form Angle 0 the wrap is
    exactly 0. Defaults are 0/0 (today's verified look); the editorial set
    passes explicit values. Any wiring failure degrades to passthrough and the
    z-assertions in base_curve_check.py catch it.
    """
    if geom is None or half_sock is None:
        return geom
    x0, y0 = loc
    try:
        bc = sock(gin, bc_param, outputs=True)
        form = sock(gin, form_param, outputs=True)
        pos = safe_node(tree, "GeometryNodeInputPosition", (x0, y0 - 260))
        sepx = safe_node(tree, "ShaderNodeSeparateXYZ", (x0 + 180, y0 - 260))
        link_sockets(tree, sock(pos, "Position", outputs=True), sock(sepx, "Vector"))
        xs = sock(sepx, "X", outputs=True)
        ys = sock(sepx, "Y", outputs=True)
        # smooth |x|
        x2 = _math(tree, "MULTIPLY", (x0 + 360, y0 - 200), a=xs, b=xs)
        kk = _constant(tree, (x0 + 360, y0 - 320), _SMOOTH_ABS_K ** 2)
        ssum = _math(tree, "ADD", (x0 + 540, y0 - 260),
                     a=x2.outputs[0], b=kk.outputs[0])
        srt = _math(tree, "SQRT", (x0 + 720, y0 - 260), a=ssum.outputs[0])
        kval = _constant(tree, (x0 + 720, y0 - 380), _SMOOTH_ABS_K)
        ax = _math(tree, "SUBTRACT", (x0 + 900, y0 - 260),
                   a=srt.outputs[0], b=kval.outputs[0])
        axs = ax.outputs[0]
        # sag about the eye boxing centre
        dx = _math(tree, "SUBTRACT", (x0 + 1080, y0 - 260), a=axs, b=half_sock)
        dx2 = _math(tree, "MULTIPLY", (x0 + 1260, y0 - 200),
                    a=dx.outputs[0], b=dx.outputs[0])
        dy2 = _math(tree, "MULTIPLY", (x0 + 1260, y0 - 320), a=ys, b=ys)
        r2 = _math(tree, "ADD", (x0 + 1440, y0 - 260),
                   a=dx2.outputs[0], b=dy2.outputs[0])
        bcmax = _math(tree, "MAXIMUM", (x0 + 1080, y0 + 100), a=bc, b=0.001)
        c523 = _constant(tree, (x0 + 1080, y0 - 20), 523.0)
        rmm = _math(tree, "DIVIDE", (x0 + 1260, y0 + 40),
                    a=c523.outputs[0], b=bcmax.outputs[0])
        rr = _math(tree, "MULTIPLY", (x0 + 1440, y0 + 40),
                   a=rmm.outputs[0], b=MM)
        rrs = rr.outputs[0]
        r2s = r2.outputs[0]
        rr2 = _math(tree, "MULTIPLY", (x0 + 1620, y0 + 100), a=rrs, b=rrs)
        sub = _math(tree, "SUBTRACT", (x0 + 1800, y0 + 40),
                    a=rr2.outputs[0], b=r2s)
        diff = _math(tree, "MAXIMUM", (x0 + 1980, y0 + 40),
                     a=sub.outputs[0], b=0.0)
        root = _math(tree, "SQRT", (x0 + 2160, y0 + 40), a=diff.outputs[0])
        sag = _math(tree, "SUBTRACT", (x0 + 2340, y0 + 40),
                    a=rrs, b=root.outputs[0])
        # wrap: z -= smooth|x| * sin(form)
        rad = _math(tree, "MULTIPLY", (x0 + 1620, y0 - 200), a=form, b=0.0174532925)
        s = _math(tree, "SINE", (x0 + 1800, y0 - 200), a=rad.outputs[0])
        wrap = _math(tree, "MULTIPLY", (x0 + 1980, y0 - 200),
                     a=axs, b=s.outputs[0])
        negw = _math(tree, "MULTIPLY", (x0 + 2160, y0 - 200),
                     a=wrap.outputs[0], b=-1.0)
        offz = _math(tree, "SUBTRACT", (x0 + 2340, y0 - 200),
                     a=negw.outputs[0], b=sag.outputs[0])
        comb = safe_node(tree, "ShaderNodeCombineXYZ", (x0 + 2520, y0 - 200))
        link_sockets(tree, offz.outputs[0], sock(comb, "Z"))
        sp = safe_node(tree, "GeometryNodeSetPosition", (x0 + 2700, y0))
        link_sockets(tree, geom, sock(sp, "Geometry"))
        link_sockets(tree, comb.outputs["Vector"], sock(sp, "Offset"))
        return sp.outputs["Geometry"]
    except Exception:
        return geom


def build_eyewear_pair(group_name="MEL_eyewear_pair"):
    """A complete, assembled pair: front + two temples + two hinges, positioned.

    The endpiece X is derived, not guessed. From the boxing arithmetic the outer
    width is 2A + DBL + 2*RimThickness, so the hinge sits at
        X = A + DBL/2 + RimThickness
    and both the temple and the hinge take that as their Hinge Pivot. The right
    side is produced by the nested builders' own mirroring, so both sides use the
    same positive pivot.
    """
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Lens Width A", 54.0, 34.0, 66.0)
    add_float_param(tree, "Lens Height B", 34.0, 24.0, 48.0)
    add_float_param(tree, "Bridge DBL", 18.0, 12.0, 26.0)
    add_float_param(tree, "Rim Thickness", 4.0, 1.5, 10.0)
    add_float_param(tree, "Rim Depth", 6.0, 2.0, 14.0)
    add_float_param(tree, "Corner Radius", 7.0, 0.5, 20.0)
    add_int_param(tree, "Silhouette", 0, 0, 2)
    add_float_param(tree, "Length to Bend", 100.0, 40.0, 160.0)
    add_float_param(tree, "Tip Drop", 28.0, 0.0, 70.0)
    add_float_param(tree, "Temple Width", 4.5, 1.0, 14.0)
    add_float_param(tree, "Temple Thickness", 3.0, 1.0, 12.0)
    add_float_param(tree, "Fold Angle", 0.0, 0.0, 95.0)
    add_float_param(tree, "Barrel Radius", 1.4, 0.4, 6.0)
    add_float_param(tree, "Barrel Length", 2.4, 0.6, 10.0)
    # 11.2 defaults flat (today's verified look); forwarded to front + lens,
    # and applied as rigid seat rotations below so hinges/temples track the wrap.
    add_float_param(tree, "Base Curve", 0.0, 0.0, 8.0)
    add_float_param(tree, "Form Angle", 0.0, 0.0, 25.0)
    # 11.6 editorial finish controls.
    add_float_param(tree, "Tortoise", 0.0, 0.0, 1.0)
    make_group_input(tree, "NodeSocketColor", "Top Tint", default=LENS_TINT_DEFAULT)
    make_group_input(tree, "NodeSocketColor", "Bottom Tint", default=LENS_TINT_DEFAULT)
    # 11.7 hero variants: metal frame swaps front + temples to the metal
    # material (hinges are always metal); Frame Solid tints the writer base.
    add_bool_param(tree, "Metal Frame", False)
    make_group_input(tree, "NodeSocketColor", "Frame Solid", default=TORTOISE_SOLID)

    bx, by = 0, 0

    # endpiece X in BU: A + DBL/2 + RimThickness, all in mm
    a_mm = _mm(tree, gin, "Lens Width A", (bx - 1500, by + 400))
    dbl_half = _math(tree, "MULTIPLY", (bx - 1300, by + 260),
                     a=_mm(tree, gin, "Bridge DBL", (bx - 1500, by + 120)), b=0.5)
    rt_mm = _mm(tree, gin, "Rim Thickness", (bx - 1500, by - 40))
    x_ab = _math(tree, "ADD", (bx - 1120, by + 300), a=a_mm, b=dbl_half.outputs[0])
    pivot_x = _math(tree, "ADD", (bx - 940, by + 300), a=x_ab.outputs[0], b=rt_mm)

    # each sub-tree is built exactly once, then shared by the group nodes
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

    # forward the frame parameters to the front (finish params live here in
    # the pair: the shared tortoise pass below, driven by Tortoise)
    for p in ("Lens Width A", "Lens Height B", "Bridge DBL", "Rim Thickness",
              "Rim Depth", "Corner Radius", "Silhouette",
              "Base Curve", "Form Angle"):
        _forward(tree, gin, p, front, p)

    # arms and knuckles
    for t in (templ_l, templ_r):
        for p in ("Length to Bend", "Tip Drop", "Temple Width", "Temple Thickness",
                  "Fold Angle", "Rim Thickness"):
            _forward(tree, gin, p, t, p)
    for h in (hinge_l, hinge_r):
        for p in ("Barrel Radius", "Barrel Length"):
            _forward(tree, gin, p, h, p)

    # seat both arms and both knuckles on the derived endpiece axis
    # Placement is done by a Transform AFTER each nested node, not by driving the
    # nested "Hinge Pivot" input. Setting that input through the group node did not
    # take reliably (the right knuckle landed correctly while the left stayed at the
    # origin, leaving 1.4 mm - one barrel radius - of asymmetry), so the pair owns
    # placement itself and the nested builders keep their own defaults.
    # Seat the nest so the temple's OUTER face is flush with the frame's outer edge.
    # The arm builder offsets itself by (half width + clearance) internally, so its
    # outer face sits at (width + clearance) from the nest origin.
    inset = _math(tree, "ADD", (bx - 780, by + 120),
                  a=_mm(tree, gin, "Temple Width", (bx - 1000, by + 160)),
                  b=_mm(tree, gin, "Endpiece Clearance", (bx - 1000, by - 20)))
    nest_x = _math(tree, "SUBTRACT", (bx - 620, by + 200),
                   a=pivot_x.outputs[0], b=inset.outputs[0])

    pivot = _vec(tree, (bx - 780, by - 40), x=nest_x.outputs[0])
    neg_one_v = _vec(tree, (bx - 780, by - 260), x=-1.0, y=1.0, z=1.0)
    # the right side mirrors the SEAT as well as the geometry: mirroring about
    # X then translating by +nest_x parks the right arm inboard over the lens
    # (measured: TempleR at [+57.0, +61.5] instead of [-67.0, -62.5]). The
    # right-side translation is therefore -nest_x.
    neg_x = _math(tree, "MULTIPLY", (bx - 780, by - 380),
                  a=nest_x.outputs[0], b=-1.0)
    neg_pivot = _vec(tree, (bx - 780, by - 500),
                     x=neg_x.outputs[0] if neg_x is not None else -62.0)

    # 11.2 seat tracking: rigid wrap rotation about the frame origin, +form on
    # the left, -form on the right (mirrored, so coincident joints stay
    # coincident exactly, like the seat mirror above). At Form Angle 0 this is
    # identity. Front/lens halves use the equivalent Z field in-builder.
    form_rad = _math(tree, "MULTIPLY", (bx - 780, by - 620),
                     a=sock(gin, "Form Angle", outputs=True), b=0.0174532925)

    # 11.5 materials: acetate front + temples, metal hinges, blend lens.
    # Assigned BEFORE placement transforms; transforms never touch materials.
    mats = ensure_eyewear_materials()
    acetate = mats.get("acetate")
    metal = mats.get("metal")
    lens_mat = mats.get("lens")

    def _join2(a, b, loc):
        j = safe_node(tree, "GeometryNodeJoinGeometry", loc)
        if j is None or a is None or b is None:
            return a if b is None else b
        link_sockets(tree, a, j.inputs["Geometry"])
        link_sockets(tree, b, j.inputs["Geometry"])
        return j.outputs["Geometry"]

    dressed = {}
    dressed["front"] = _g_sock(front, "Geometry", outputs=True)
    dressed["hl"] = _apply_material(
        tree, _g_sock(hinge_l, "Geometry", outputs=True), metal, (bx - 240, by - 300))
    dressed["hr"] = _apply_material(
        tree, _g_sock(hinge_r, "Geometry", outputs=True), metal, (bx - 240, by - 550))
    dressed["tl"] = _g_sock(templ_l, "Geometry", outputs=True)
    dressed["tr"] = _g_sock(templ_r, "Geometry", outputs=True)

    # 11.7 Metal Frame switch: front + temples select acetate vs metal without
    # rebuilding (Switch input_type GEOMETRY, measured on 5.2). Hinges stay metal.
    def _finish(geom, loc):
        a = _apply_material(tree, geom, acetate, (loc[0], loc[1]))
        m = _apply_material(tree, geom, metal, (loc[0] + 140, loc[1] - 120))
        sw = safe_node(tree, "GeometryNodeSwitch", (loc[0] + 280, loc[1] - 60))
        if sw is None or a is None or m is None:
            return a if m is None else m
        try:
            sw.input_type = "GEOMETRY"
        except Exception:
            pass
        try:
            link_sockets(tree, sock(gin, "Metal Frame", outputs=True),
                         sock(sw, "Switch"))
            link_sockets(tree, a, sock(sw, "False"))
            link_sockets(tree, m, sock(sw, "True"))
            return sw.outputs["Output"]
        except Exception:
            return a

    dressed["front"] = _finish(
        _g_sock(front, "Geometry", outputs=True), (bx - 240, by + 430))
    dressed["tl"] = _finish(
        _g_sock(templ_l, "Geometry", outputs=True), (bx - 240, by - 930))
    dressed["tr"] = _finish(
        _g_sock(templ_r, "Geometry", outputs=True), (bx - 240, by - 1180))

    # 11.6 COLOR_0 ensure: solid Col on arms + knuckles (temples espresso via
    # the writer default, hinges champagne) so the join never inherits a
    # black default attribute.
    tor_sub = _subtree("MEL_eyewear_tortoise")
    # Champagne constant: FunctionNodeCombineColor (ShaderNodeRGB and
    # ShaderNodeCombineColor cannot join a geometry tree on this build).
    champ = safe_node(tree, "FunctionNodeCombineColor", (bx - 60, by - 1250))
    champ_col = None
    if champ is not None:
        try:
            sock(champ, "Red").default_value = CHAMPAGNE[0]
            sock(champ, "Green").default_value = CHAMPAGNE[1]
            sock(champ, "Blue").default_value = CHAMPAGNE[2]
            sock(champ, "Alpha").default_value = CHAMPAGNE[3]
            champ_col = sock(champ, "Color", outputs=True)
        except Exception:
            champ_col = None

    def _paint(geom, loc, solid_from=None, amount_from=None):
        n = _nest(tree, tor_sub, loc)
        if n is None:
            return geom
        try:
            link_sockets(tree, geom, _g_sock(n, "Geometry"))
            if solid_from is not None:
                link_sockets(tree, solid_from, _g_sock(n, "Solid"))
            if amount_from is not None:
                link_sockets(tree, amount_from, _g_sock(n, "Amount"))
            return _g_sock(n, "Geometry", outputs=True)
        except Exception:
            return geom

    if tor_sub is not None:
        dressed["front"] = _paint(dressed.get("front"), (bx - 60, by - 1170),
                                  amount_from=sock(gin, "Tortoise", outputs=True),
                                  solid_from=sock(gin, "Frame Solid", outputs=True))
        dressed["tl"] = _paint(dressed.get("tl"), (bx - 60, by - 1300))
        dressed["tr"] = _paint(dressed.get("tr"), (bx - 60, by - 1430))
        dressed["hl"] = _paint(dressed.get("hl"), (bx - 60, by - 1560), champ_col)
        dressed["hr"] = _paint(dressed.get("hr"), (bx - 60, by - 1690), champ_col)

    # 8.5 UV finish: one shared writer (same once-per-build rule as paint),
    # applied post-paint pre-placement in local coords. Store adds no topology,
    # so the downstream welds are unaffected by construction.
    uv_sub = _subtree("MEL_eyewear_uv")

    def _uv(geom, loc):
        n = _nest(tree, uv_sub, loc)
        if n is None:
            return geom
        try:
            link_sockets(tree, geom, _g_sock(n, "Geometry"))
            return _g_sock(n, "Geometry", outputs=True)
        except Exception:
            return geom

    if uv_sub is not None:
        for _k, _y in (("front", by - 1820), ("tl", by - 1950), ("tr", by - 2080),
                       ("hl", by - 2210), ("hr", by - 2340)):
            dressed[_k] = _uv(dressed.get(_k), (bx - 60, _y))

    placed = {}
    for key, node in (("tl", templ_l), ("hl", hinge_l), ("tr", templ_r), ("hr", hinge_r)):
        src = dressed.get(key)
        if src is None:
            placed[key] = None
            continue
        geom = src
        # the right side must be MIRRORED, not merely translated to the other side,
        # or the arm reaches inward instead of outward
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
        seated = xf.outputs["Geometry"]
        if form_rad is not None:
            side_sign = -1.0 if key in ("tr", "hr") else 1.0
            ly = by - len(placed) * 240
            sgn = _math(tree, "MULTIPLY", (bx + 240, ly),
                        a=form_rad.outputs[0], b=side_sign)
            rvec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 420, ly))
            rt = safe_node(tree, "GeometryNodeTransform", (bx + 600, ly))
            if sgn is not None and rvec is not None and rt is not None:
                link_sockets(tree, sgn.outputs[0], rvec.inputs["Y"])
                link_sockets(tree, seated, rt.inputs["Geometry"])
                link_sockets(tree, rvec.outputs["Vector"], sock(rt, "Rotation"))
                seated = rt.outputs["Geometry"]
        placed[key] = seated

    # 11.5 Frame output: front + both hinges, welded (11.4). Hinges keep their
    # metal slot through the join; Join Geometry preserves per-face materials.
    frame_geo = dressed.get("front")
    frame_geo = _join2(frame_geo, placed.get("hl"), (bx + 200, by + 200))
    frame_geo = _join2(frame_geo, placed.get("hr"), (bx + 360, by + 200))
    frame_geo = _weld(tree, frame_geo, (bx + 520, by + 200))

    # lenses: nest once, drive from the same boxing params, split L/R by X sign.
    lens_r_geo = lens_l_geo = None
    lens_sub = _subtree("MEL_eyewear_lens")
    lens_n = _nest(tree, lens_sub, (bx - 400, by - 1300))
    if lens_n is not None:
        for p in ("Lens Width A", "Lens Height B", "Bridge DBL",
                  "Base Curve", "Form Angle", "Top Tint", "Bottom Tint"):
            _forward(tree, gin, p, lens_n, p)
        lens_geo = _g_sock(lens_n, "Geometry", outputs=True)
        lens_r_geo, lens_l_geo = _split_x_sign(tree, lens_geo, (bx - 200, by - 1300))
        lens_r_geo = _apply_material(tree, lens_r_geo, lens_mat, (bx + 360, by - 1300))
        lens_l_geo = _apply_material(tree, lens_l_geo, lens_mat, (bx + 360, by - 1500))
        if uv_sub is not None:
            lens_r_geo = _uv(lens_r_geo, (bx + 180, by - 1300))
            lens_l_geo = _uv(lens_l_geo, (bx + 180, by - 1500))

    # 11.5 five named part outputs (Amazon node vocabulary). The original
    # assembled Geometry output stays the modifier path (active output).
    for _part in ("Frame", "TempleL", "TempleR", "LensL", "LensR"):
        make_group_output(tree, "NodeSocketGeometry", _part)
    try:
        if frame_geo is not None:
            link_sockets(tree, frame_geo, gout.inputs["Frame"])
        if placed.get("tl") is not None:
            link_sockets(tree, placed["tl"], gout.inputs["TempleL"])
        if placed.get("tr") is not None:
            link_sockets(tree, placed["tr"], gout.inputs["TempleR"])
        if lens_l_geo is not None:
            link_sockets(tree, lens_l_geo, gout.inputs["LensL"])
        if lens_r_geo is not None:
            link_sockets(tree, lens_r_geo, gout.inputs["LensR"])
    except Exception:
        pass
    try:
        gout.is_active_output = True
    except Exception:
        pass

    joins = [g for g in (frame_geo, placed.get("tl"), placed.get("tr"))
             if g is not None]

    if joins:
        acc = joins[0]
        for i, nxt in enumerate(joins[1:]):
            j = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 700 + i * 160, by))
            if j is None:
                break
            link_sockets(tree, acc, j.inputs["Geometry"])
            link_sockets(tree, nxt, j.inputs["Geometry"])
            acc = j.outputs["Geometry"]
        # 11.4: weld the assembled pair — kills the doubled seam verts.
        acc = _weld(tree, acc, (bx + 700 + len(joins) * 160, by))
        link_sockets(tree, acc, gout.inputs["Geometry"])

    label_tree(tree, group_name)
    return (tree, gin, gout)


register_builder(
    "MEL_eyewear_pair", build_eyewear_pair, "Eyewear Pair",
    "Assembled pair: front, two temples and two hinges seated on the derived "
    "endpiece axis (X = A + DBL/2 + RimThickness, mirrored per side), welded "
    "0.02 mm (11.4), with five named part outputs Frame/TempleL/TempleR/LensL/"
    "LensR carrying the acetate/metal/lens delivery materials (11.5). The "
    "render-ready build — every parameter is in millimetres.",
    category="eyewear")


def build_eyewear_lens(group_name="MEL_eyewear_lens"):
    """Both lenses: a rounded-rect solid per aperture, seated at the boxing centres.

    Base Curve + Form Angle drive the same pure-Z field as the front (11.2),
    so rim and lens stay in agreement. Default flat (today's look).

    Flow is silhouette -> Fill Curve -> Extrude Mesh. Note Fill Curve takes
    (Curve, Group ID, Mode, Fill Rule) and Extrude Mesh takes
    (Mesh, Selection, Offset, Offset Scale, Individual) with mode on the PROPERTY.
    """
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Lens Width A", 54.0, 34.0, 66.0)
    add_float_param(tree, "Lens Height B", 34.0, 24.0, 48.0)
    add_float_param(tree, "Bridge DBL", 18.0, 12.0, 26.0)
    add_float_param(tree, "Lens Thickness", 2.0, 0.4, 9.0)
    add_float_param(tree, "Corner Radius", 7.0, 0.5, 20.0)
    add_float_param(tree, "Path Resolution", 2.0, 0.4, 12.0)
    add_bool_param(tree, "Flat Shading", False)
    # 11.2: same base-curve/form field as the front, driven from the same
    # values so rim and lens agree. Default flat (today's look).
    add_float_param(tree, "Base Curve", 0.0, 0.0, 8.0)
    add_float_param(tree, "Form Angle", 0.0, 0.0, 25.0)
    # 11.6 lens gradient endpoints (Top at +Y). Equal = uniform (today's look).
    make_group_input(tree, "NodeSocketColor", "Top Tint", default=LENS_TINT_DEFAULT)
    make_group_input(tree, "NodeSocketColor", "Bottom Tint", default=LENS_TINT_DEFAULT)

    bx, by = 0, 0

    a_w = _mm(tree, gin, "Lens Width A", (bx - 1400, by + 300))
    b_h = _mm(tree, gin, "Lens Height B", (bx - 1400, by + 140))
    thick = _mm(tree, gin, "Lens Thickness", (bx - 1400, by - 20))
    res_mm = _mm(tree, gin, "Path Resolution", (bx - 1400, by - 180))
    corner = _mm(tree, gin, "Corner Radius", (bx - 1400, by - 340))

    quad = _cyc_profile(tree, (bx - 1180, by + 220), a_w, b_h)
    if quad is None:
        return (tree, gin, gout)

    res = safe_node(tree, "GeometryNodeResampleCurve", (bx - 1000, by + 220))
    if res is None:
        return (tree, gin, gout)
    for cand in ("Length", "LENGTH"):
        try:
            res.inputs["Mode"].default_value = cand
            break
        except Exception:
            continue
    link_sockets(tree, quad.outputs["Curve"], res.inputs["Curve"])
    link_sockets(tree, res_mm, res.inputs["Length"])

    flt = safe_node(tree, "GeometryNodeFilletCurve", (bx - 820, by + 220))
    if flt is None:
        return (tree, gin, gout)
    for cand in ("Poly", "POLY", "Polygon"):
        try:
            flt.inputs["Mode"].default_value = cand
            break
        except Exception:
            continue
    link_sockets(tree, res.outputs["Curve"], flt.inputs["Curve"])
    link_sockets(tree, corner, flt.inputs["Radius"])
    flt.inputs["Limit Radius"].default_value = True

    fill = safe_node(tree, "GeometryNodeFillCurve", (bx - 640, by + 220))
    if fill is None:
        return (tree, gin, gout)
    for cand in ("N-gons", "NGONS", "Ngons", "Triangles"):
        try:
            fill.inputs["Mode"].default_value = cand
            break
        except Exception:
            continue
    link_sockets(tree, flt.outputs["Curve"], fill.inputs["Curve"])

    ext = safe_node(tree, "GeometryNodeExtrudeMesh", (bx - 460, by + 220))
    if ext is None:
        return (tree, gin, gout)
    try:
        ext.mode = "FACES"
    except Exception:
        pass
    link_sockets(tree, fill.outputs["Mesh"], ext.inputs["Mesh"])
    # extrude along +Z by the thickness, then centre the prism on Z = 0
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

    # Edge break: deliberately NOT applied. GeometryNodeMeshBevel is unusable
    # on this mesh in 5.2 - a 0.3 mm offset took the 54 mm lens to 322 mm,
    # both unrestricted and restricted to the extrude Side selection. The
    # same defect was already measured on this project for the decor star and
    # heart builders and the node was removed there too. A lens edge break
    # belongs in the profile geometry, not in a bevel pass.
    # seat at the boxing lens centre and mirror for the right eye
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

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 1220, by))
    lens_joined = None
    if shade is not None:
        link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
        smooth = safe_node(tree, "GeometryNodeSwitch", (bx + 1380, by))
        if smooth is not None:
            try:
                smooth.input_type = "BOOLEAN"
            except Exception:
                pass
            inv = safe_node(tree, "FunctionNodeBooleanMath", (bx + 1220, by - 200))
            if inv is not None:
                inv.operation = "NOT"
                link_sockets(tree, sock(gin, "Flat Shading", outputs=True), inv.inputs[0])
                link_sockets(tree, inv.outputs[0], smooth.inputs["False"])
            smooth.inputs["True"].default_value = False
            smooth.inputs["Switch"].default_value = True
            link_sockets(tree, smooth.outputs["Output"], shade.inputs["Shade Smooth"])
        lens_joined = shade.outputs["Geometry"]
    else:
        lens_joined = join.outputs["Geometry"]
    # 11.2 post-pass over both lenses together (same field as the front, same
    # centres, so rim and lens stay in agreement).
    if lens_joined is not None and half_span is not None:
        lens_joined = _base_curve_field(tree, lens_joined, gin,
                                        half_span.outputs[0], (bx + 1400, by))
    # 11.6 COLOR_0: vertical gradient tint (defaults uniform = today's look).
    if lens_joined is not None:
        grad_sub = _subtree("MEL_eyewear_lens_gradient")
        grad_n = _nest(tree, grad_sub, (bx + 1580, by))
        if grad_n is not None:
            _forward(tree, gin, "Top Tint", grad_n, "Top Tint")
            _forward(tree, gin, "Bottom Tint", grad_n, "Bottom Tint")
            try:
                half_b = _math(tree, "MULTIPLY", (bx + 1400, by - 200),
                               a=b_h, b=0.5)
                if half_b is not None:
                    link_sockets(tree, half_b.outputs[0],
                                 _g_sock(grad_n, "Half Height"))
                link_sockets(tree, lens_joined, _g_sock(grad_n, "Geometry"))
                lens_joined = _g_sock(grad_n, "Geometry", outputs=True)
            except Exception:
                pass
    if lens_joined is not None:
        link_sockets(tree, lens_joined, gout.inputs["Geometry"])

    label_tree(tree, group_name)
    return (tree, gin, gout)


register_builder(
    "MEL_eyewear_lens", build_eyewear_lens, "Eyewear Lens",
    "Both lenses as plano solids, centred on the boxing lens positions "
    "(+/- (A+DBL)/2) and on Z = 0 within the rim. Base Curve + Form Angle "
    "drive the same pure-Z field as the front (default flat).",
    category="eyewear")
