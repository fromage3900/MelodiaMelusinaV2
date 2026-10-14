"""P5 wave 16 - notation glyph lane: C clefs, accidentals, quarter rest.

Gap audit first (repo-wide grep over `deploy/surreal_arch/` + the live registry +
`Tools/registry_baseline.json`, 2026-10-05): the notation family owns the treble
and bass clefs, the note head, staff, beam cluster, triplet, chord stack,
fermata, repeat bar, meter sign, key unit, phrase and the sheet rails. NONE of
the six ids below existed anywhere (grep count 0 each):

    alto clef, tenor clef, sharp, flat, natural, quarter rest

Nothing here re-implements an existing glyph. The two C clefs are ONE law
(`_c_clef`) sized by a `Staff Line` seat, not two copies of the same numbers -
exactly the way the bowed family sizes one `_bowed_body`. The three accidentals
share the stroke laws of the lane (a stem is `Thickness` wide and carries no
rotation) and differ in anatomy, which is what makes them three glyphs and not
one.

Design rules (same as music_wind_flute_family / music_aux_percussion2):
  - Native-only. A glyph is swept strokes, plates and revolved tubes that 5.2
    primitives express exactly; a Higgsas subtree here would be decoration, not
    a lead. Every builder still stores `higgsas_lead` (1.0 = native) so the
    family gate reads the lane uniformly.
  - The shared helpers are REUSED, never re-authored: `_sweep` /
    `_profile_circle` / `_profile_out` (notation_extras, the proven XY-glyph
    tube idiom - no profile rotation, because a glyph lives in the XY plane),
    `_plate` (music_keyboard_kit - links all three `Size` components),
    `_cyl` / `_xf` / `_store_named` (music_higgsas_instruments), `_join` /
    `_vec` (music_wind_reed_brass), `_m` / `_math` / `_combine`, and `_finish`
    (music_string_kit - applies Scale BEFORE the export tail, which the shared
    `_export_tail` does not).
  - Zero `MeshBoolean` in the lane: a cutter that touches the mesh's own
    boundary emits ZERO geometry with no error and no `link_failures` entry.
    Every stroke here is laid on, not cut.
  - A literal rotation tuple lands in a socket's `default_value`, never in a
    link, so every tilt in this lane is a linked CombineXYZ fed by a group
    input - a gate can then prove the tilt is real rather than reading an
    absent link as "no tilt".

Builders:
    MEL_music_alto_clef     C clef seated on staff line 3
    MEL_music_tenor_clef    C clef seated on staff line 4 (same body, one line down)
    MEL_music_sharp         two verticals + two parallel slanted cross bars
    MEL_music_flat          vertical stem + elliptical belly on the right
    MEL_music_natural       two STAGGERED verticals + two slanted connectors
    MEL_music_rest_quarter  five-segment swept zigzag stroke
"""

from __future__ import annotations

import math

from .core import (
    safe_node, link_sockets, label_tree, new_geometry_tree, add_float_param,
    add_int_param, add_bool_param, register_builder, sock,
)
from .music_harps_real import _math, _combine
from .music_higgsas_instruments import _store_named, _cyl, _xf
from .music_keyboard_kit import _m, _plate
from .music_string_kit import _finish
from .music_wind_reed_brass import _vec, _join
from .notation_extras import _profile_circle, _profile_out, _sweep


# ---------------------------------------------------------------------------
# Lane-local laws
# ---------------------------------------------------------------------------

def _neg(tree, loc, s):
    """`-s` through a MULTIPLY by -1.0.

    A Python unary minus on a socket is a build-time TypeError and `NEGATE` is
    not a valid ShaderNodeMath operation (it is swallowed and the node stays on
    ADD), so every negation is a node.
    """
    return _m(tree, "MULTIPLY", loc, s, -1.0)


def _half(tree, loc, s):
    return _m(tree, "MULTIPLY", loc, s, 0.5)


def _radians(tree, loc, deg_sock):
    return _m(tree, "MULTIPLY", loc, deg_sock, math.pi / 180.0)


def _tube(tree, loc, curve_sock, radius_sock, profile_res=10):
    """A swept tube stroke for an XY glyph.

    Uses the notation_extras idiom verbatim: the profile circle is NOT rotated
    about X. `core.sweep_profile` rotates it 90 deg (correct for the AAA railing
    family, where the curve is not a glyph), and the notation module's own
    builders have always swept unrotated - measured on this lane: an unrotated
    profile gives a round tube lying in the glyph plane with z extent
    `+/- radius` (Saved/Audit/probe_w16_api2.py).
    """
    bx, by = loc
    prof = _profile_circle(tree, bx, by - 200, radius_sock,
                           vertices=profile_res)
    return _sweep(tree, bx, by, curve_sock, _profile_out(prof))


def _arc_xy(tree, loc, r_sock, start_deg, sweep_deg, res=24):
    """A `CurveArc` in the glyph's own XY plane.

    Probed 2026-10-05 (Saved/Audit/probe_w15_arc.py + probe_w16_api.py): mode
    RADIUS is the default, the arc lies in XY with angle 0 at +X and a CCW
    sweep, and `Connect Center` OFF leaves the chord open. No rotation is
    applied - the glyph plane IS XY.
    """
    n = safe_node(tree, "GeometryNodeCurveArc", loc)
    if n is None:
        return None
    link_sockets(tree, r_sock, sock(n, "Radius"))
    for key, val in (("Start Angle", math.radians(start_deg)),
                     ("Sweep Angle", math.radians(sweep_deg))):
        s = sock(n, key)
        if s is not None:
            try:
                s.default_value = val
            except Exception:
                pass
    s = sock(n, "Connect Center")
    if s is not None:
        try:
            s.default_value = False
        except Exception:
            pass
    s = sock(n, "Resolution")
    if s is not None:
        try:
            s.default_value = res
        except Exception:
            pass
    return n


def _glyph_attrs(tree, loc, family_value):
    """The lane's shared attribute triple.

    `glyph_semitone_mod12` is the house index->element-palette key every other
    lane stores (bowl_/key_/flute_/drum_ ...), `glyph_family` carries the real
    semantic class (1 clef / 2 accidental / 3 rest), and `higgsas_lead` = 1.0
    records that this lane's lead is native.
    """
    bx, by = loc
    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx, by))
    smod = _m(tree, "FLOORMOD", (bx, by - 140), sidx.outputs["Index"], 12.0)
    return [("glyph_semitone_mod12", smod),
            ("glyph_family", float(family_value)),
            ("higgsas_lead", 1.0)]


def _glyph_common(tree, gin, bx, by):
    """Params every glyph in the lane exposes, plus the shared size sockets."""
    add_float_param(tree, "Glyph Height", 0.60, 0.20, 1.60)
    add_float_param(tree, "Thickness", 0.055, 0.015, 0.180)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)
    return gin.outputs["Glyph Height"], gin.outputs["Thickness"]


# ---------------------------------------------------------------------------
# MEL_music_alto_clef / MEL_music_tenor_clef - one C-clef law, two seats
# ---------------------------------------------------------------------------

def _c_clef(group_name, default_line):
    """A C clef: a thick vertical spine on the LEFT, and two thick arms that
    sweep off it and meet at a POINT on the right at mid-height.

    Arc geometry, measured not recalled: `CurveArc` in RADIUS mode lies in XY
    with angle 0 at +X and a CCW sweep. The upper arm covers 0..170 deg and the
    lower 190..360, so the two arms MEET at 0 deg (the right point) and leave a
    20 deg notch at 180 deg — which is where the spine sits, so the glyph closes
    there. Sweeps are positive-only, so no negative-sweep behaviour is assumed.

    The `Staff Line` seat is the whole difference between the alto and tenor
    clefs, so it is a single linked chain — `(Staff Line - 3) * Line Spacing` —
    applied as ONE Transform on the joined glyph. A gate can therefore prove the
    seat is real (it reaches BOTH group inputs) and measure that the two clefs
    land exactly one line apart.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_int_param(tree, "Staff Line", default_line, 1, 5)
    add_float_param(tree, "Line Spacing", 0.13, 0.040, 0.400)
    add_float_param(tree, "Arc Radius Ratio", 0.40, 0.25, 0.50)
    add_float_param(tree, "Spine Width Ratio", 1.60, 0.80, 3.00)

    r = _m(tree, "MULTIPLY", (bx - 2600, by + 300), H,
           gin.outputs["Arc Radius Ratio"])
    seat = _m(tree, "MULTIPLY", (bx - 2600, by + 160),
              _m(tree, "SUBTRACT", (bx - 2800, by + 160),
                 gin.outputs["Staff Line"], 3.0),
              gin.outputs["Line Spacing"])
    left_x = _neg(tree, (bx - 2600, by), r)

    # the spine: thicker than a stroke (it is the clef's body) and exactly as
    # tall as the arms reach, so the three parts form one closed silhouette
    spine_w = _m(tree, "MULTIPLY", (bx - 2600, by - 160), T,
                 gin.outputs["Spine Width Ratio"])
    arm_r = _m(tree, "MULTIPLY", (bx - 2600, by - 320), T, 0.90)
    spine_h = _m(tree, "MULTIPLY", (bx - 2600, by - 480),
                 _m(tree, "ADD", (bx - 2800, by - 480), r, arm_r), 2.0)
    spine = _plate(tree, (bx - 1400, by), spine_w, spine_h, T,
                   translation=_vec(tree, (bx - 1600, by), left_x, 0.0, 0.0))

    # two thick arms meeting at the right point
    upper_arc = _arc_xy(tree, (bx - 1400, by - 800), r, 0.0, 170.0)
    lower_arc = _arc_xy(tree, (bx - 1400, by - 1200), r, 190.0, 170.0)
    upper = _tube(tree, (bx - 1000, by - 800),
                  upper_arc.outputs["Curve"], arm_r) if upper_arc else None
    lower = _tube(tree, (bx - 1000, by - 1200),
                  lower_arc.outputs["Curve"], arm_r) if lower_arc else None

    geom = _join(tree, (bx + 400, by), [spine, upper, lower])
    seated = _xf(tree, (bx + 600, by), geom,
                 translation=_vec(tree, (bx + 600, by - 220), 0.0, seat, 0.0)
                 ).outputs["Geometry"]
    _finish(tree, gin, gout, seated, (bx + 900, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 1.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Spine", "nodes": ("Cube",), "role": "geometry"},
        {"title": "C Arms", "nodes": ("Arc", "Curve to Mesh"), "role": "curve"},
        {"title": "Staff Seat", "nodes": ("Transform",), "role": "math"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


def build_music_alto_clef(group_name="MEL_music_alto_clef"):
    """Alto (C) clef - the C body seated on staff line 3, the viola's clef."""
    return _c_clef(group_name, 3)


def build_music_tenor_clef(group_name="MEL_music_tenor_clef"):
    """Tenor (C) clef - the SAME C body seated one staff line lower (line 4)."""
    return _c_clef(group_name, 4)


# ---------------------------------------------------------------------------
# MEL_music_sharp
# ---------------------------------------------------------------------------

def build_music_sharp(group_name="MEL_music_sharp"):
    """Sharp - two strictly VERTICAL strokes crossed by two parallel slanted
    bars. The verticals share a Y centre and the bars share one tilt; that
    pairing is the identity (the natural staggers its verticals instead).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Bar Gap", 0.115, 0.040, 0.300)
    add_float_param(tree, "Cross Span Ratio", 2.30, 1.30, 4.00)
    add_float_param(tree, "Slant", 22.0, 0.0, 45.0)

    gap = gin.outputs["Bar Gap"]
    half_gap = _half(tree, (bx - 2600, by + 160), gap)
    slant = _radians(tree, (bx - 2600, by), gin.outputs["Slant"])
    rot = _vec(tree, (bx - 2600, by - 160), 0.0, 0.0, slant)

    vert_a = _plate(tree, (bx - 1400, by), T, H, T,
                    translation=_vec(tree, (bx - 1600, by),
                                     _neg(tree, (bx - 2800, by), half_gap),
                                     0.0, 0.0))
    vert_b = _plate(tree, (bx - 1400, by - 400), T, H, T,
                    translation=_vec(tree, (bx - 1600, by - 400),
                                     half_gap, 0.0, 0.0))

    cross_w = _m(tree, "MULTIPLY", (bx - 2600, by - 800), gap,
                 gin.outputs["Cross Span Ratio"])
    cross_h = _m(tree, "MULTIPLY", (bx - 2600, by - 960), T, 0.85)
    cross_off = _m(tree, "MULTIPLY", (bx - 2600, by - 1120), H, 0.16)
    cross_t = _plate(tree, (bx - 1400, by - 1200), cross_w, cross_h, T,
                     rotation=rot,
                     translation=_vec(tree, (bx - 1600, by - 1200),
                                      0.0, cross_off, 0.0))
    cross_b = _plate(tree, (bx - 1400, by - 1600), cross_w, cross_h, T,
                     rotation=rot,
                     translation=_vec(tree, (bx - 1600, by - 1600),
                                      0.0, _neg(tree, (bx - 2800, by - 1600),
                                                cross_off), 0.0))

    geom = _join(tree, (bx + 400, by), [vert_a, vert_b, cross_t, cross_b])
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 2000), 2.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Vertical Strokes", "nodes": ("Cube",), "role": "geometry"},
        {"title": "Slanted Cross Bars", "nodes": ("Transform",),
         "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_flat
# ---------------------------------------------------------------------------

def build_music_flat(group_name="MEL_music_flat"):
    """Flat - a vertical stem with an ELLIPTICAL belly bulging to its right.

    The belly is a 24-sided cylinder (a solid disc with a cap, so the glyph is
    not a one-sided plane) scaled non-uniformly to 0.72 in Y: the non-uniform
    scale IS the glyph's identity and the gate asserts it, because a uniform
    disc would be the wrong shape while still measuring non-zero.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Belly Ratio", 0.19, 0.10, 0.32)
    add_float_param(tree, "Belly Flatten", 0.72, 0.40, 1.00)
    add_float_param(tree, "Belly Drop", 0.06, 0.00, 0.30)

    belly_r = _m(tree, "MULTIPLY", (bx - 2600, by + 160), H,
                 gin.outputs["Belly Ratio"])
    stem = _plate(tree, (bx - 1400, by), T, H, T,
                  translation=_vec(tree, (bx - 1600, by), 0.0, 0.0, 0.0))

    # the belly's left edge must sit INSIDE the stem, so its centre is a
    # fraction of its own radius rather than a multiple of the stroke width
    belly_x = _m(tree, "MULTIPLY", (bx - 2600, by - 400), belly_r, 0.85)
    belly_y = _neg(tree, (bx - 2600, by - 560),
                   _m(tree, "MULTIPLY", (bx - 2800, by - 560), H,
                      gin.outputs["Belly Drop"]))
    prim = _cyl(tree, (bx - 1400, by - 800), belly_r, T, vertices=24, fill=2)
    belly = None
    if prim is not None:
        belly = _xf(tree, (bx - 1200, by - 800), prim.outputs["Mesh"],
                    scale=_vec(tree, (bx - 1400, by - 1000), 1.0,
                               gin.outputs["Belly Flatten"], 1.0),
                    translation=_vec(tree, (bx - 1200, by - 1200),
                                     belly_x, belly_y, 0.0)).outputs["Geometry"]

    geom = _join(tree, (bx + 400, by), [stem, belly])
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1600), 2.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Stem", "nodes": ("Cube",), "role": "geometry"},
        {"title": "Elliptical Belly", "nodes": ("Cylinder",), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_natural
# ---------------------------------------------------------------------------

def build_music_natural(group_name="MEL_music_natural"):
    """Natural - two STAGGERED vertical strokes joined by two slanted bars.

    The stagger is the identity: the left stroke owns the lower half and the
    right stroke the upper half, so the two verticals' Y centres are separated
    by `Stagger`. The sharp's verticals share one centre; the gate asserts both
    relationships, which is what stops the two glyphs collapsing into each
    other.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Stroke Gap", 0.115, 0.040, 0.300)
    add_float_param(tree, "Stroke Ratio", 0.68, 0.35, 0.85)
    add_float_param(tree, "Stagger", 0.16, 0.06, 0.35)
    add_float_param(tree, "Slant", 24.0, 0.0, 45.0)
    add_float_param(tree, "Connector Drop", 0.15, 0.05, 0.28)

    gap = gin.outputs["Stroke Gap"]
    stroke_h = _m(tree, "MULTIPLY", (bx - 2600, by + 160), H,
                  gin.outputs["Stroke Ratio"])
    stag = _m(tree, "MULTIPLY", (bx - 2600, by), H,
              gin.outputs["Stagger"])
    slant = _radians(tree, (bx - 2600, by - 160), gin.outputs["Slant"])
    rot = _vec(tree, (bx - 2600, by - 320), 0.0, 0.0, slant)

    left = _plate(tree, (bx - 1400, by), T, stroke_h, T,
                  translation=_vec(tree, (bx - 1600, by), 0.0,
                                   _neg(tree, (bx - 2800, by), stag), 0.0))
    right = _plate(tree, (bx - 1400, by - 400), T, stroke_h, T,
                   translation=_vec(tree, (bx - 1600, by - 400), gap,
                                    stag, 0.0))

    # The connectors run from the LEFT stroke's top/bottom corner to the RIGHT
    # stroke's bottom/top corner, so their width is the FULL gap plus both
    # stroke half-widths. A shorter connector leaves the glyph open at the
    # corner (measured: a `gap + 2T` plate left a 2 mm bite out of both joins
    # on the first build), and the Y separation between the two connectors is
    # the stagger, not a fraction of the glyph height.
    conn_w = _m(tree, "ADD", (bx - 2600, by - 800), gap, T)
    conn_h = _m(tree, "MULTIPLY", (bx - 2600, by - 960), T, 0.70)
    conn_x = _half(tree, (bx - 2600, by - 1120), gap)
    conn_drop = _m(tree, "MULTIPLY", (bx - 2600, by - 1280), H,
                   gin.outputs["Connector Drop"])
    conn_t = _plate(tree, (bx - 1400, by - 1200), conn_w, conn_h, T,
                    rotation=rot,
                    translation=_vec(tree, (bx - 1600, by - 1200),
                                     conn_x, conn_drop, 0.0))
    conn_b = _plate(tree, (bx - 1400, by - 1600), conn_w, conn_h, T,
                    rotation=rot,
                    translation=_vec(tree, (bx - 1600, by - 1600),
                                     conn_x,
                                     _neg(tree, (bx - 2800, by - 1600),
                                          conn_drop), 0.0))

    geom = _join(tree, (bx + 400, by), [left, right, conn_t, conn_b])
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 2000), 2.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Staggered Strokes", "nodes": ("Cube",), "role": "geometry"},
        {"title": "Slanted Connectors", "nodes": ("Transform",),
         "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_rest_quarter
# ---------------------------------------------------------------------------

# The quarter rest's own calligraphic zigzag, as fractions of Glyph Height.
# Six points -> five strokes, so the gate can assert the cardinality literally.
_REST_PTS = (
    (0.08, 0.50),
    (-0.12, 0.22),
    (0.13, 0.06),
    (-0.14, -0.16),
    (0.10, -0.34),
    (-0.02, -0.50),
)


def build_music_rest_quarter(group_name="MEL_music_rest_quarter"):
    """Quarter rest - a five-stroke swept zigzag, taller than it is wide.

    Every point is a live multiple of `Glyph Height` (never a baked constant),
    so the glyph resizes with the dial. The strokes are joined and swept with a
    circle profile at half the glyph `Thickness` - the rest is a calligraphic
    stroke, not a stack of plates.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Stroke Radius Ratio", 0.55, 0.25, 0.90)
    add_float_param(tree, "Sweep Resolution", 8.0, 4.0, 20.0)
    add_float_param(tree, "Zigzag Width", 1.00, 0.50, 2.00)

    # point sockets: X = Zigzag Width * fraction * Glyph Height, Y = Glyph
    # Height * fraction. The X factor carries the height because the rest's
    # width is a fraction of its HEIGHT (a music glyph's proportions are
    # height-relative); scaling only by Zigzag Width made the glyph 2.1x wider
    # than it is tall at the default - the wrong shape for a quarter rest.
    pts = []
    for i, (px, py) in enumerate(_REST_PTS):
        y = _m(tree, "MULTIPLY", (bx - 3000, by + 400 - i * 180), H, py)
        x = _m(tree, "MULTIPLY", (bx - 2800, by + 400 - i * 180),
               _m(tree, "MULTIPLY", (bx - 3000, by + 400 - i * 180), H,
                  gin.outputs["Zigzag Width"]), px)
        pts.append(_vec(tree, (bx - 2600, by + 400 - i * 180), x, y, 0.0))

    stroke_r = _m(tree, "MULTIPLY", (bx - 2600, by - 1600), T,
                  gin.outputs["Stroke Radius Ratio"])

    segs = []
    for i in range(len(pts) - 1):
        p0, p1 = pts[i], pts[i + 1]
        b = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment",
                      (bx - 1400, by + 400 - i * 260))
        if b is None:
            continue
        link_sockets(tree, p0, sock(b, "Start"))
        link_sockets(tree, p1, sock(b, "End"))
        # straight handles: lerp at 1/3 and 2/3 through VectorMath, so the
        # segment really passes through both authored points.
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
            b.inputs["Resolution"].default_value = 6
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

    stroke = _tube(tree, (bx + 400, by + 200), path, stroke_r, profile_res=10)
    geom = stroke
    if stroke is None:
        geom = path
    _finish(tree, gin, gout, geom, (bx + 900, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 3.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Zigzag Path", "nodes": ("Bezier", "Join", "Merge"),
         "role": "curve"},
        {"title": "Swept Stroke", "nodes": ("Curve to Mesh",), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# -- Registry ---------------------------------------------------------------

register_builder("MEL_music_alto_clef", build_music_alto_clef, "Music Alto Clef",
                 "C clef on staff line 3 - full-height spine, two end serifs, "
                 "two thick arcs bracketing the seat line",
                 "music")
register_builder("MEL_music_tenor_clef", build_music_tenor_clef, "Music Tenor Clef",
                 "C clef on staff line 4 - the alto clef's own body, seated one "
                 "staff line lower",
                 "music")
register_builder("MEL_music_sharp", build_music_sharp, "Music Sharp",
                 "Sharp accidental - two vertical strokes crossed by two "
                 "parallel slanted bars",
                 "music")
register_builder("MEL_music_flat", build_music_flat, "Music Flat",
                 "Flat accidental - vertical stem with an elliptical belly "
                 "bulging to the right",
                 "music")
register_builder("MEL_music_natural", build_music_natural, "Music Natural",
                 "Natural accidental - two staggered vertical strokes joined by "
                 "two slanted connectors",
                 "music")
register_builder("MEL_music_rest_quarter", build_music_rest_quarter,
                 "Music Quarter Rest",
                 "Quarter rest - five-stroke swept calligraphic zigzag",
                 "music")
