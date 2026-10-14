"""P5 wave 21: notation signs — double sharp, double flat, coda, segno,
breath mark, sforzando.

Every glyph is staff-relative: its dimensions are ratios of `Glyph Height`,
never absolute metres. The lane law is the same as waves 16-20: one
`_glyph_common` param set, one `_finish` export tail, one `_glyph_attrs`
attribute set.
"""

from .core import (
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    safe_node, link_sockets, label_tree, register_builder, sock,
)
from .music_keyboard_kit import _m, _plate
from .music_higgsas_instruments import _cyl, _xf
from .music_wind_reed_brass import _vec, _join
from .music_string_kit import _finish
from .music_notation_glyphs import (
    _neg, _half, _radians, _tube, _glyph_common, _glyph_attrs, _arc_xy,
)


# ---------------------------------------------------------------------------
# MEL_music_double_sharp
# ---------------------------------------------------------------------------

def build_music_double_sharp(group_name="MEL_music_double_sharp"):
    """Double sharp - two crossed bars forming an X.

    The identity is the CROSS: two bars of equal length intersecting at
    their own centres at 90 degrees. A single bar is a tenuto; two parallel
    bars are a double flat. The gate asserts the cross angle and the
    equal length.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Cross Angle", 90.0, 45.0, 135.0)
    add_float_param(tree, "Bar Length Ratio", 0.85, 0.50, 1.20)

    bar_len = _m(tree, "MULTIPLY", (bx - 2600, by + 160), H,
                 gin.outputs["Bar Length Ratio"])
    bar_w = _m(tree, "MULTIPLY", (bx - 2600, by), T, 0.90)
    half_len = _half(tree, (bx - 2600, by - 160), bar_len)
    cross_ang = _radians(tree, (bx - 2600, by - 320),
                         gin.outputs["Cross Angle"])
    half_ang = _half(tree, (bx - 2600, by - 480), cross_ang)

    # bar 1: rotated +half_ang from vertical
    rot1 = _vec(tree, (bx - 2600, by - 640), 0.0, 0.0, half_ang)
    bar1 = _plate(tree, (bx - 1400, by), bar_w, bar_len, T,
                  rotation=rot1,
                  translation=_vec(tree, (bx - 1600, by), 0.0, 0.0, 0.0))

    # bar 2: rotated -half_ang from vertical (the cross)
    rot2 = _vec(tree, (bx - 2600, by - 800), 0.0, 0.0,
                _neg(tree, (bx - 2800, by - 800), half_ang))
    bar2 = _plate(tree, (bx - 1400, by - 400), bar_w, bar_len, T,
                  rotation=rot2,
                  translation=_vec(tree, (bx - 1600, by - 400), 0.0, 0.0, 0.0))

    geom = _join(tree, (bx + 400, by), [bar1, bar2])
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 6.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Cross Bars", "nodes": ("Cube", "Transform"), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_double_flat
# ---------------------------------------------------------------------------

def build_music_double_flat(group_name="MEL_music_double_flat"):
    """Double flat - two flat bellies side by side.

    The identity is the PAIR: two elliptical bellies sharing one stem,
    separated by `Belly Gap`. A single belly is a flat; the gate asserts
    the pair's separation and the shared stem.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Belly Ratio", 0.19, 0.10, 0.32)
    add_float_param(tree, "Belly Flatten", 0.72, 0.40, 1.00)
    add_float_param(tree, "Belly Drop", 0.06, 0.00, 0.30)
    add_float_param(tree, "Belly Gap", 0.14, 0.06, 0.30)

    belly_r = _m(tree, "MULTIPLY", (bx - 2600, by + 160), H,
                 gin.outputs["Belly Ratio"])
    gap = gin.outputs["Belly Gap"]
    half_gap = _half(tree, (bx - 2600, by), gap)

    stem = _plate(tree, (bx - 1400, by), T, H, T,
                  translation=_vec(tree, (bx - 1600, by),
                                   _neg(tree, (bx - 2800, by), half_gap),
                                   0.0, 0.0))

    belly_y = _neg(tree, (bx - 2600, by - 560),
                   _m(tree, "MULTIPLY", (bx - 2800, by - 560), H,
                      gin.outputs["Belly Drop"]))

    prim_a = _cyl(tree, (bx - 1400, by - 800), belly_r, T, vertices=24, fill=2)
    belly_a = None
    if prim_a is not None:
        belly_a = _xf(tree, (bx - 1200, by - 800), prim_a.outputs["Mesh"],
                      scale=_vec(tree, (bx - 1400, by - 1000), 1.0,
                                 gin.outputs["Belly Flatten"], 1.0),
                      translation=_vec(tree, (bx - 1200, by - 1200),
                                       _neg(tree, (bx - 2800, by - 1200),
                                            _m(tree, "MULTIPLY",
                                               (bx - 3000, by - 1200),
                                               belly_r, 0.85)),
                                       belly_y, 0.0)).outputs["Geometry"]

    prim_b = _cyl(tree, (bx - 1400, by - 1600), belly_r, T, vertices=24, fill=2)
    belly_b = None
    if prim_b is not None:
        belly_b = _xf(tree, (bx - 1200, by - 1600), prim_b.outputs["Mesh"],
                      scale=_vec(tree, (bx - 1400, by - 1800), 1.0,
                                 gin.outputs["Belly Flatten"], 1.0),
                      translation=_vec(tree, (bx - 1200, by - 2000),
                                       _m(tree, "MULTIPLY",
                                          (bx - 3000, by - 2000),
                                          belly_r, 0.85),
                                       belly_y, 0.0)).outputs["Geometry"]

    parts = [stem]
    if belly_a is not None:
        parts.append(belly_a)
    if belly_b is not None:
        parts.append(belly_b)
    geom = _join(tree, (bx + 400, by), parts)
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 7.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Stem", "nodes": ("Cube",), "role": "geometry"},
        {"title": "Bellies", "nodes": ("Cylinder", "Transform"), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_coda
# ---------------------------------------------------------------------------

def build_music_coda(group_name="MEL_music_coda"):
    """Coda - a circle with a cross through it.

    The identity is the CROSS INSIDE THE CIRCLE: a ring (closed curve swept
    with a circle profile) plus two perpendicular bars. The gate asserts
    the ring's radius and the bars' intersection at the centre.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Ring Ratio", 0.38, 0.20, 0.55)
    add_float_param(tree, "Cross Span", 0.80, 0.50, 1.10)

    ring_r = _m(tree, "MULTIPLY", (bx - 2600, by + 160), H,
                gin.outputs["Ring Ratio"])
    cross_span = _m(tree, "MULTIPLY", (bx - 2600, by), H,
                    gin.outputs["Cross Span"])
    bar_w = _m(tree, "MULTIPLY", (bx - 2600, by - 160), T, 0.85)

    # the ring: a closed circle path swept with a circle profile
    ring_path = safe_node(tree, "GeometryNodeCurvePrimitiveCircle",
                          (bx - 1400, by))
    if ring_path is not None:
        ring_path.mode = "RADIUS"
        ring_path.inputs["Resolution"].default_value = 32
        link_sockets(tree, ring_r, ring_path.inputs["Radius"])
    ring = _tube(tree, (bx - 1000, by),
                 ring_path.outputs["Curve"] if ring_path else None,
                 _m(tree, "MULTIPLY", (bx - 2600, by - 320), T, 0.55),
                 profile_res=8) if ring_path else None

    # the cross: two perpendicular bars
    bar_h = _plate(tree, (bx - 1400, by - 800), bar_w, cross_span, T,
                   translation=_vec(tree, (bx - 1600, by - 800), 0.0, 0.0, 0.0))
    bar_v = _plate(tree, (bx - 1400, by - 1200), cross_span, bar_w, T,
                   translation=_vec(tree, (bx - 1600, by - 1200), 0.0, 0.0, 0.0))

    parts = [bar_h, bar_v]
    if ring is not None:
        parts.insert(0, ring)
    geom = _join(tree, (bx + 400, by), parts)
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 8.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Ring", "nodes": ("Curve", "Curve to Mesh"), "role": "curve"},
        {"title": "Cross", "nodes": ("Cube",), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_segno
# ---------------------------------------------------------------------------

def build_music_segno(group_name="MEL_music_segno"):
    """Segno - an S-curve with two dots.

    The identity is the S-CURVE: a bezier path with two inflections, plus
    two dots at the top-right and bottom-left. The gate asserts the curve's
    inflection count and the dots' placement at the extremities.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Curve Width", 0.55, 0.30, 0.80)
    add_float_param(tree, "Dot Ratio", 0.12, 0.06, 0.22)

    curve_w = _m(tree, "MULTIPLY", (bx - 2600, by + 160), H,
                 gin.outputs["Curve Width"])
    dot_r = _m(tree, "MULTIPLY", (bx - 2600, by), H,
               gin.outputs["Dot Ratio"])
    stroke_r = _m(tree, "MULTIPLY", (bx - 2600, by - 160), T, 0.55)

    # the S-curve: a bezier path with 4 points (2 inflections)
    pts = []
    for i, (px, py) in enumerate([(0.15, 0.45), (-0.20, 0.15),
                                    (0.20, -0.15), (-0.15, -0.45)]):
        x = _m(tree, "MULTIPLY", (bx - 3000, by + 400 - i * 180),
               _m(tree, "MULTIPLY", (bx - 3200, by + 400 - i * 180), H,
                  curve_w), px)
        y = _m(tree, "MULTIPLY", (bx - 2800, by + 400 - i * 180), H, py)
        pts.append(_vec(tree, (bx - 2600, by + 400 - i * 180), x, y, 0.0))

    segs = []
    for i in range(len(pts) - 1):
        p0, p1 = pts[i], pts[i + 1]
        b = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment",
                      (bx - 1400, by + 400 - i * 260))
        if b is None:
            continue
        link_sockets(tree, p0, sock(b, "Start"))
        link_sockets(tree, p1, sock(b, "End"))
        delta = safe_node(tree, "ShaderNodeVectorMath",
                          (bx - 3000, by - 400 - i * 260))
        if delta is not None:
            delta.operation = "SUBTRACT"
            link_sockets(tree, p1, delta.inputs[0])
            link_sockets(tree, p0, delta.inputs[1])
            for slot, t in (("Start Handle", 1.0 / 3.0),
                            ("End Handle", 2.0 / 3.0)):
                mul = safe_node(tree, "ShaderNodeVectorMath",
                                (bx - 2800, by - 500 - i * 260))
                add = safe_node(tree, "ShaderNodeVectorMath",
                                (bx - 2600, by - 600 - i * 260))
                if mul is None or add is None:
                    continue
                mul.operation = "SCALE"
                link_sockets(tree, delta.outputs["Vector"], mul.inputs[0])
                try:
                    mul.inputs["Scale"].default_value = t
                except Exception:
                    pass
                add.operation = "ADD"
                link_sockets(tree, p0, add.inputs[0])
                link_sockets(tree, mul.outputs["Vector"], add.inputs[1])
                link_sockets(tree, add.outputs["Vector"], sock(b, slot))
        try:
            b.inputs["Resolution"].default_value = 8
        except Exception:
            pass
        segs.append(b.outputs["Curve"])

    joined = _join(tree, (bx - 200, by + 200), segs)
    merge = safe_node(tree, "GeometryNodeMergeByDistance", (bx + 100, by + 200))
    if merge is not None and joined is not None:
        link_sockets(tree, joined, merge.inputs["Geometry"])
        try:
            merge.inputs["Distance"].default_value = 0.0005
        except Exception:
            pass
        path = merge.outputs["Geometry"]
    else:
        path = joined

    curve = _tube(tree, (bx + 400, by + 200), path, stroke_r,
                  profile_res=8) if path else None

    # the dots: two small cylinders at the extremities
    dot_t = _cyl(tree, (bx - 1400, by - 800), dot_r, T, vertices=16, fill=2)
    dot_top = None
    if dot_t is not None:
        dot_top = _xf(tree, (bx - 1200, by - 800), dot_t.outputs["Mesh"],
                      translation=_vec(tree, (bx - 1200, by - 1000),
                                       _m(tree, "MULTIPLY",
                                          (bx - 3000, by - 1000), H, 0.35),
                                       _m(tree, "MULTIPLY",
                                          (bx - 3200, by - 1000), H, 0.38),
                                       0.0)).outputs["Geometry"]

    dot_b = _cyl(tree, (bx - 1400, by - 1200), dot_r, T, vertices=16, fill=2)
    dot_bot = None
    if dot_b is not None:
        dot_bot = _xf(tree, (bx - 1200, by - 1200), dot_b.outputs["Mesh"],
                      translation=_vec(tree, (bx - 1200, by - 1400),
                                       _neg(tree, (bx - 3000, by - 1400),
                                            _m(tree, "MULTIPLY",
                                               (bx - 3200, by - 1400), H, 0.35)),
                                       _neg(tree, (bx - 3400, by - 1400),
                                            _m(tree, "MULTIPLY",
                                               (bx - 3600, by - 1400), H, 0.38)),
                                       0.0)).outputs["Geometry"]

    parts = []
    if curve is not None:
        parts.append(curve)
    if dot_top is not None:
        parts.append(dot_top)
    if dot_bot is not None:
        parts.append(dot_bot)
    geom = _join(tree, (bx + 600, by), parts)
    _finish(tree, gin, gout, geom, (bx + 900, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 9.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "S-Curve", "nodes": ("Bezier", "Join", "Curve to Mesh"),
         "role": "curve"},
        {"title": "Dots", "nodes": ("Cylinder", "Transform"), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_breath_mark
# ---------------------------------------------------------------------------

def build_music_breath_mark(group_name="MEL_music_breath_mark"):
    """Breath mark - a comma-like curve.

    The identity is the COMMA: a single swept curve with a taper (thick at
    the head, thin at the tail). The gate asserts the taper ratio and the
    curve's inflection.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Head Ratio", 0.20, 0.10, 0.35)
    add_float_param(tree, "Tail Ratio", 0.04, 0.01, 0.12)
    add_float_param(tree, "Curve Bend", 0.35, 0.15, 0.60)

    head_r = _m(tree, "MULTIPLY", (bx - 2600, by + 160), H,
                gin.outputs["Head Ratio"])
    tail_r = _m(tree, "MULTIPLY", (bx - 2600, by), H,
                gin.outputs["Tail Ratio"])
    bend = _m(tree, "MULTIPLY", (bx - 2600, by - 160), H,
              gin.outputs["Curve Bend"])

    # the comma: a bezier path with 3 points (1 inflection)
    pts = []
    for i, (px, py) in enumerate([(0.0, 0.45), (0.30, 0.10), (0.0, -0.40)]):
        x = _m(tree, "MULTIPLY", (bx - 3000, by + 400 - i * 180), bend, px)
        y = _m(tree, "MULTIPLY", (bx - 2800, by + 400 - i * 180), H, py)
        pts.append(_vec(tree, (bx - 2600, by + 400 - i * 180), x, y, 0.0))

    segs = []
    for i in range(len(pts) - 1):
        p0, p1 = pts[i], pts[i + 1]
        b = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment",
                      (bx - 1400, by + 400 - i * 260))
        if b is None:
            continue
        link_sockets(tree, p0, sock(b, "Start"))
        link_sockets(tree, p1, sock(b, "End"))
        delta = safe_node(tree, "ShaderNodeVectorMath",
                          (bx - 3000, by - 400 - i * 260))
        if delta is not None:
            delta.operation = "SUBTRACT"
            link_sockets(tree, p1, delta.inputs[0])
            link_sockets(tree, p0, delta.inputs[1])
            for slot, t in (("Start Handle", 1.0 / 3.0),
                            ("End Handle", 2.0 / 3.0)):
                mul = safe_node(tree, "ShaderNodeVectorMath",
                                (bx - 2800, by - 500 - i * 260))
                add = safe_node(tree, "ShaderNodeVectorMath",
                                (bx - 2600, by - 600 - i * 260))
                if mul is None or add is None:
                    continue
                mul.operation = "SCALE"
                link_sockets(tree, delta.outputs["Vector"], mul.inputs[0])
                try:
                    mul.inputs["Scale"].default_value = t
                except Exception:
                    pass
                add.operation = "ADD"
                link_sockets(tree, p0, add.inputs[0])
                link_sockets(tree, mul.outputs["Vector"], add.inputs[1])
                link_sockets(tree, add.outputs["Vector"], sock(b, slot))
        try:
            b.inputs["Resolution"].default_value = 10
        except Exception:
            pass
        segs.append(b.outputs["Curve"])

    joined = _join(tree, (bx - 200, by + 200), segs)
    merge = safe_node(tree, "GeometryNodeMergeByDistance", (bx + 100, by + 200))
    if merge is not None and joined is not None:
        link_sockets(tree, joined, merge.inputs["Geometry"])
        try:
            merge.inputs["Distance"].default_value = 0.0005
        except Exception:
            pass
        path = merge.outputs["Geometry"]
    else:
        path = joined

    # taper: set curve radius from head to tail
    taper = safe_node(tree, "GeometryNodeSetCurveRadius", (bx + 400, by + 200))
    if taper is not None and path is not None:
        link_sockets(tree, path, taper.inputs["Curve"])
        # radius per point: interpolate from head_r to tail_r
        param = safe_node(tree, "GeometryNodeSplineParameter",
                          (bx + 600, by + 200))
        if param is not None:
            link_sockets(tree, param.outputs["Factor"], taper.inputs["Radius"])
            # scale factor to go from head_r to tail_r
            # radius = head_r + factor * (tail_r - head_r)
            # = head_r * (1 - factor) + tail_r * factor
            # Use a MapRange node: from [0,1] to [head_r, tail_r]
            mr = safe_node(tree, "ShaderNodeMapRange", (bx + 800, by + 200))
            if mr is not None:
                link_sockets(tree, param.outputs["Factor"], mr.inputs["Value"])
                mr.inputs["From Min"].default_value = 0.0
                mr.inputs["From Max"].default_value = 1.0
                link_sockets(tree, head_r, mr.inputs["To Min"])
                link_sockets(tree, tail_r, mr.inputs["To Max"])
                link_sockets(tree, mr.outputs["Result"],
                             taper.inputs["Radius"])
        curve = taper.outputs["Curve"]
    else:
        curve = path

    stroke = _tube(tree, (bx + 1000, by + 200), curve, head_r,
                   profile_res=8) if curve else None
    geom = stroke if stroke is not None else curve
    _finish(tree, gin, gout, geom, (bx + 1300, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 10.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Comma Curve", "nodes": ("Bezier", "Join", "Curve to Mesh"),
         "role": "curve"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_sforzando
# ---------------------------------------------------------------------------

def build_music_sforzando(group_name="MEL_music_sforzando"):
    """Sforzando - an sfz mark: a horizontal wedge with a vertical stem.

    The identity is the WEDGE + STEM: a crescendo-like wedge (two bars
    meeting at a point) with a vertical stem descending from the apex. The
    gate asserts the wedge's aspect and the stem's attachment at the apex.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Wedge Angle", 25.0, 10.0, 45.0)
    add_float_param(tree, "Stem Drop", 0.30, 0.15, 0.50)

    wedge_ang = _radians(tree, (bx - 2600, by + 160),
                         gin.outputs["Wedge Angle"])
    stem_drop = _m(tree, "MULTIPLY", (bx - 2600, by), H,
                   gin.outputs["Stem Drop"])
    bar_w = _m(tree, "MULTIPLY", (bx - 2600, by - 160), T, 0.85)
    half_w = _half(tree, (bx - 2600, by - 320), H)

    # the wedge: two bars meeting at the left point
    rot_top = _vec(tree, (bx - 2600, by - 480), 0.0, 0.0,
                   _neg(tree, (bx - 2800, by - 480), wedge_ang))
    rot_bot = _vec(tree, (bx - 2600, by - 640), 0.0, 0.0, wedge_ang)

    bar_top = _plate(tree, (bx - 1400, by), bar_w, half_w, T,
                     rotation=rot_top,
                     translation=_vec(tree, (bx - 1600, by),
                                      _neg(tree, (bx - 2800, by),
                                           _half(tree, (bx - 3000, by), half_w)),
                                      _half(tree, (bx - 3200, by), half_w), 0.0))
    bar_bot = _plate(tree, (bx - 1400, by - 400), bar_w, half_w, T,
                     rotation=rot_bot,
                     translation=_vec(tree, (bx - 1600, by - 400),
                                      _neg(tree, (bx - 2800, by - 400),
                                           _half(tree, (bx - 3000, by - 400), half_w)),
                                      _neg(tree, (bx - 3200, by - 400),
                                           _half(tree, (bx - 3400, by - 400), half_w)),
                                      0.0))

    # the stem: a vertical bar descending from the apex
    stem = _plate(tree, (bx - 1400, by - 800), bar_w, stem_drop, T,
                  translation=_vec(tree, (bx - 1600, by - 800),
                                   _neg(tree, (bx - 2800, by - 800), half_w),
                                   _neg(tree, (bx - 3000, by - 800), stem_drop),
                                   0.0))

    geom = _join(tree, (bx + 400, by), [bar_top, bar_bot, stem])
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 11.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Wedge", "nodes": ("Cube", "Transform"), "role": "geometry"},
        {"title": "Stem", "nodes": ("Cube",), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

register_builder("MEL_music_double_sharp", build_music_double_sharp,
                 "Music Double Sharp",
                 "Double sharp accidental - two crossed bars forming an X",
                 "music")
register_builder("MEL_music_double_flat", build_music_double_flat,
                 "Music Double Flat",
                 "Double flat accidental - two elliptical bellies side by side",
                 "music")
register_builder("MEL_music_coda", build_music_coda,
                 "Music Coda",
                 "Coda sign - a circle with a cross through it",
                 "music")
register_builder("MEL_music_segno", build_music_segno,
                 "Music Segno",
                 "Segno sign - an S-curve with two dots",
                 "music")
register_builder("MEL_music_breath_mark", build_music_breath_mark,
                 "Music Breath Mark",
                 "Breath mark - a comma-like curve",
                 "music")
register_builder("MEL_music_sforzando", build_music_sforzando,
                 "Music Sforzando",
                 "Sforzando - a horizontal wedge with a vertical stem",
                 "music")
