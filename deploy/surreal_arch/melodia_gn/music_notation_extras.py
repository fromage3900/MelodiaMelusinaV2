"""P5 wave 18 - notation extras: sixteenth note, eighth/sixteenth rests,
dynamics (f/p/mf/mp/ff/pp), hairpins, percussion clef.

Gap audit first (repo-wide grep over `deploy/surreal_arch/` + the live registry +
`Tools/registry_baseline.json`, 2026-10-05): the notation family owns the treble,
bass, alto and tenor clefs, the note head, staff, beam cluster, triplet, chord
stack, fermata, repeat bar, meter sign, key unit, phrase, the sheet rails, the
sharp/flat/natural accidentals, the quarter rest, the whole/half/quarter/eighth
notes and the whole/half rests. NONE of the twelve ids below existed anywhere
(grep count 0 each):

    sixteenth note, eighth rest, sixteenth rest,
    dynamic f, dynamic p, dynamic mf, dynamic mp, dynamic ff, dynamic pp,
    hairpin crescendo, hairpin decrescendo, percussion clef

The sixteenth note is the eighth note's law (filled head + stem) plus a SECOND
flag -- the duration table's next row. The two rests are ONE slash law at two
dot counts. The six dynamics are ONE letter law at six anatomies (f and p are
the atoms; m is two stems + two arches; mp/mf are m+p / m+f; ff/pp are f+f /
p+p). The two hairpins are ONE wedge law at two seats. The percussion clef is
two thick vertical bars.

Design rules (same as music_notation_glyphs / music_note_durations):
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
    MEL_music_note_sixteenth    filled head + stem + TWO flags
    MEL_music_rest_eighth       slash + one dot
    MEL_music_rest_sixteenth    slash + two dots
    MEL_music_dynamic_f         forte: f
    MEL_music_dynamic_p         piano: p
    MEL_music_dynamic_mf        mezzo-forte: mf
    MEL_music_dynamic_mp        mezzo-piano: mp
    MEL_music_dynamic_ff        fortissimo: ff
    MEL_music_dynamic_pp        pianissimo: pp
    MEL_music_hairpin_cresc     crescendo: two lines meeting at the left
    MEL_music_hairpin_decresc   decrescendo: two lines meeting at the right
    MEL_music_percussion_clef   two thick vertical bars
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
# Wave 17's duration-note laws are REUSED, never re-authored a second time: the
# head (one ellipse law, two anatomies), the stem and the flag live in
# music_note_durations, and this lane's own byte-identical copies are gone.
from .music_note_durations import _common_params, _head, _stem, _flag


# ---------------------------------------------------------------------------
# Lane-local laws
# ---------------------------------------------------------------------------

def _neg(tree, loc, s):
    """`-s` through a MULTIPLY by -1.0."""
    return _m(tree, "MULTIPLY", loc, s, -1.0)


def _half(tree, loc, s):
    return _m(tree, "MULTIPLY", loc, s, 0.5)


def _radians(tree, loc, deg_sock):
    return _m(tree, "MULTIPLY", loc, deg_sock, math.pi / 180.0)


def _tube(tree, loc, curve_sock, radius_sock, profile_res=10):
    """A swept tube stroke for an XY glyph (no profile rotation)."""
    bx, by = loc
    prof = _profile_circle(tree, bx, by - 200, radius_sock,
                           vertices=profile_res)
    return _sweep(tree, bx, by, curve_sock, _profile_out(prof))


def _glyph_attrs(tree, loc, family_value):
    """The notation family's shared attribute triple (wave-16/17 convention)."""
    bx, by = loc
    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx, by))
    smod = _m(tree, "FLOORMOD", (bx, by - 140), sidx.outputs["Index"], 12.0)
    return [("glyph_semitone_mod12", smod),
            ("glyph_family", float(family_value)),
            ("higgsas_lead", 1.0)]


def _glyph_common(tree, gin, bx, by):
    """Params every glyph in the lane exposes, plus the shared Scale sockets."""
    add_float_param(tree, "Glyph Height", 0.60, 0.20, 1.60)
    add_float_param(tree, "Thickness", 0.055, 0.015, 0.180)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)
    return gin.outputs["Glyph Height"], gin.outputs["Thickness"]


# ---------------------------------------------------------------------------
# MEL_music_note_sixteenth - filled head + stem + TWO flags
# (the head / stem / flag laws are imported from music_note_durations above)
# ---------------------------------------------------------------------------


def build_music_note_sixteenth(group_name="MEL_music_note_sixteenth"):
    """Sixteenth note - filled head, stem, and TWO flags (the eighth's law
    plus a second flag -- the duration table's next row)."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Line Spacing", 0.13, 0.040, 0.400)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)
    add_float_param(tree, "Head Width", 0.115, 0.040, 0.300)
    add_float_param(tree, "Head Height", 0.082, 0.030, 0.220)
    add_float_param(tree, "Head Stroke", 0.013, 0.004, 0.040)
    add_float_param(tree, "Head Tilt", 20.0, 0.0, 45.0)
    add_float_param(tree, "Stem Length", 0.44, 0.15, 0.90)
    add_float_param(tree, "Stem Thickness", 0.022, 0.008, 0.060)
    add_float_param(tree, "Flag Reach", 0.16, 0.05, 0.40)
    add_float_param(tree, "Flag Drop", 0.22, 0.06, 0.50)
    add_float_param(tree, "Flag Thickness", 0.017, 0.005, 0.045)

    hw = gin.outputs["Head Width"]
    hh = gin.outputs["Head Height"]
    stroke = gin.outputs["Head Stroke"]
    tilt = _vec(tree, (bx - 1800, by + 200), 0.0, 0.0,
                _radians(tree, (bx - 2000, by + 200),
                         gin.outputs["Head Tilt"]))

    head = _head(tree, (bx - 1400, by), False, hw, hh, tilt, stroke)

    tilt_rad = _radians(tree, (bx - 2000, by - 200),
                        gin.outputs["Head Tilt"])
    stem_x = _m(tree, "MULTIPLY", (bx - 1800, by - 200), hw,
                _m(tree, "COSINE", (bx - 2000, by - 400), tilt_rad))
    stem = _stem(tree, (bx - 1000, by - 200), hw, tilt_rad,
                 gin.outputs["Stem Length"],
                 gin.outputs["Stem Thickness"])

    # TWO flags: the first at the stem top, the second offset down by 0.6 x
    # Stem Length (the sixteenth note's second flag)
    flag1 = _flag(tree, (bx - 200, by - 400), stem_x,
                  gin.outputs["Stem Length"],
                  gin.outputs["Flag Reach"],
                  gin.outputs["Flag Drop"],
                  gin.outputs["Flag Thickness"])
    flag2_y = _m(tree, "MULTIPLY", (bx - 600, by - 600),
                 gin.outputs["Stem Length"], 0.60)
    flag2 = _flag(tree, (bx - 200, by - 800), stem_x, flag2_y,
                  gin.outputs["Flag Reach"],
                  gin.outputs["Flag Drop"],
                  gin.outputs["Flag Thickness"])

    parts = [head, stem, flag1, flag2]
    geom = _join(tree, (bx + 900, by), parts)
    _finish(tree, gin, gout, geom, (bx + 1200, by), group_name,
            _glyph_attrs(tree, (bx + 900, by - 2400), 4.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Head", "nodes": ("Cylinder", "Transform"), "role": "geometry"},
        {"title": "Stem And Flags", "nodes": ("Cube", "Bezier", "Transform"),
         "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_rest_eighth / MEL_music_rest_sixteenth - one slash law, two dot counts
# ---------------------------------------------------------------------------

def _rest_slash(group_name, num_dots):
    """A rest: a diagonal slash with `num_dots` dots.

    The slash is a swept tube from upper-left to lower-right. The dots are
    small filled circles (capped cylinders) placed to the right of the slash.
    The eighth rest has ONE dot; the sixteenth rest has TWO.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Slash Length Ratio", 0.72, 0.40, 1.00)
    add_float_param(tree, "Slash Angle", 60.0, 30.0, 80.0)
    add_float_param(tree, "Dot Radius Ratio", 0.16, 0.08, 0.30)
    add_float_param(tree, "Dot Spacing Ratio", 0.36, 0.20, 0.60)
    add_float_param(tree, "Stroke Radius Ratio", 0.55, 0.25, 0.90)

    slash_len = _m(tree, "MULTIPLY", (bx - 2600, by + 300), H,
                   gin.outputs["Slash Length Ratio"])
    slash_ang = _radians(tree, (bx - 2600, by + 160),
                         gin.outputs["Slash Angle"])
    stroke_r = _m(tree, "MULTIPLY", (bx - 2600, by), T,
                  gin.outputs["Stroke Radius Ratio"])
    dot_r = _m(tree, "MULTIPLY", (bx - 2600, by - 160), H,
               gin.outputs["Dot Radius Ratio"])
    dot_sp = _m(tree, "MULTIPLY", (bx - 2600, by - 320), H,
                gin.outputs["Dot Spacing Ratio"])

    # The slash: a line from (0, +slash_len/2) to (0, -slash_len/2) rotated
    # by `Slash Angle` about Z, then swept with a circle profile.
    half_sl = _m(tree, "MULTIPLY", (bx - 2800, by + 300), slash_len, 0.5)
    dx = _m(tree, "MULTIPLY", (bx - 2800, by + 160), half_sl,
            _m(tree, "SINE", (bx - 3000, by + 160), slash_ang))
    dy = _m(tree, "MULTIPLY", (bx - 2800, by), half_sl,
            _m(tree, "COSINE", (bx - 3000, by), slash_ang))

    seg = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment",
                    (bx - 1400, by))
    if seg is None:
        return None
    link_sockets(tree, _vec(tree, (bx - 1600, by + 300),
                            _neg(tree, (bx - 3200, by + 300), dx),
                            half_sl, 0.0),
                 sock(seg, "Start"))
    link_sockets(tree, _vec(tree, (bx - 1600, by + 100), dx,
                            _neg(tree, (bx - 3200, by + 100), half_sl), 0.0),
                 sock(seg, "End"))
    rs = sock(seg, "Resolution")
    if rs is not None:
        try:
            rs.default_value = 4
        except Exception:
            pass
    slash = _tube(tree, (bx - 1000, by), seg.outputs["Curve"], stroke_r,
                  profile_res=8)

    # The dots: small filled circles to the right of the slash
    parts = [slash] if slash else []
    for i in range(num_dots):
        dot_x = _m(tree, "MULTIPLY", (bx - 2600, by - 480 - i * 200),
                   dot_sp, 0.8 + i * 0.0)
        dot_y = _m(tree, "MULTIPLY", (bx - 2600, by - 640 - i * 200),
                   H, 0.18 - i * 0.22)
        prim = _cyl(tree, (bx - 1400, by - 480 - i * 200), dot_r, T,
                    vertices=16, fill=2)
        if prim is not None:
            dot = _xf(tree, (bx - 1200, by - 480 - i * 200),
                      prim.outputs["Mesh"],
                      translation=_vec(tree, (bx - 1200, by - 640 - i * 200),
                                       dot_x, dot_y, 0.0)).outputs["Geometry"]
            parts.append(dot)

    geom = _join(tree, (bx + 400, by), parts)
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 3.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Slash", "nodes": ("Bezier", "Curve to Mesh"),
         "role": "geometry"},
        {"title": "Dots", "nodes": ("Cylinder", "Transform"),
         "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


def build_music_rest_eighth(group_name="MEL_music_rest_eighth"):
    """Eighth rest - a diagonal slash with ONE dot."""
    return _rest_slash(group_name, 1)


def build_music_rest_sixteenth(group_name="MEL_music_rest_sixteenth"):
    """Sixteenth rest - the SAME slash with TWO dots."""
    return _rest_slash(group_name, 2)


# ---------------------------------------------------------------------------
# Dynamics: f, p, mf, mp, ff, pp
# ---------------------------------------------------------------------------

def _x_off(tree, loc, base, x_off):
    """`base + x_off` when x_off is a socket, else just `base`."""
    if x_off is None:
        return base
    return _m(tree, "ADD", loc, base, x_off)


def _dynamic_f(tree, gin, bx, by, H, T, x_off=None):
    """The letter 'f': a vertical stem, a cross bar, and a top hook."""
    stem = _plate(tree, (bx - 1400, by), T, H, T,
                  translation=_vec(tree, (bx - 1600, by),
                                   0.0 if x_off is None else
                                   _x_off(tree, (bx - 2800, by), 0.0, x_off),
                                   0.0, 0.0))
    cross_w = _m(tree, "MULTIPLY", (bx - 2600, by + 160), H, 0.32)
    cross = _plate(tree, (bx - 1400, by - 400), cross_w, T, T,
                    translation=_vec(tree, (bx - 1600, by - 400),
                                     _x_off(tree, (bx - 2800, by - 400),
                                            _m(tree, "MULTIPLY",
                                               (bx - 3000, by - 400),
                                               H, 0.10), x_off),
                                     _m(tree, "MULTIPLY",
                                        (bx - 2800, by - 560),
                                        H, 0.22),
                                     0.0))
    hook_w = _m(tree, "MULTIPLY", (bx - 2600, by - 720), H, 0.22)
    hook = _plate(tree, (bx - 1400, by - 800), hook_w, T, T,
                   translation=_vec(tree, (bx - 1600, by - 800),
                                    _x_off(tree, (bx - 2800, by - 800),
                                           _m(tree, "MULTIPLY",
                                              (bx - 3000, by - 800),
                                              H, 0.06), x_off),
                                    _m(tree, "MULTIPLY",
                                       (bx - 2800, by - 960),
                                       H, 0.42),
                                    0.0))
    return [stem, cross, hook]


def _dynamic_p(tree, gin, bx, by, H, T, x_off=None):
    """The letter 'p': a vertical stem with a bowl (ellipse) on the right."""
    stem = _plate(tree, (bx - 1400, by), T, H, T,
                  translation=_vec(tree, (bx - 1600, by),
                                   0.0 if x_off is None else
                                   _x_off(tree, (bx - 2800, by), 0.0, x_off),
                                   0.0, 0.0))
    bowl_r = _m(tree, "MULTIPLY", (bx - 2600, by + 160), H, 0.20)
    bowl_x = _m(tree, "MULTIPLY", (bx - 2600, by), bowl_r, 1.1)
    bowl_y = _m(tree, "MULTIPLY", (bx - 2600, by - 160), H, 0.18)
    prim = _cyl(tree, (bx - 1400, by - 400), bowl_r, T, vertices=20, fill=2)
    bowl = None
    if prim is not None:
        bowl = _xf(tree, (bx - 1200, by - 400),
                   prim.outputs["Mesh"],
                   scale=_vec(tree, (bx - 1400, by - 560), 1.0, 0.72, 1.0),
                   translation=_vec(tree, (bx - 1200, by - 560),
                                    _x_off(tree, (bx - 2800, by - 560),
                                           bowl_x, x_off),
                                    bowl_y, 0.0)).outputs["Geometry"]
    return [stem, bowl]


def _dynamic_m(tree, gin, bx, by, H, T, x_off=None):
    """The letter 'm': two vertical stems with two arches."""
    stem1 = _plate(tree, (bx - 1400, by), T, H, T,
                   translation=_vec(tree, (bx - 1600, by),
                                    0.0 if x_off is None else
                                    _x_off(tree, (bx - 2800, by), 0.0, x_off),
                                    0.0, 0.0))
    stem2 = _plate(tree, (bx - 1400, by - 400), T, H, T,
                   translation=_vec(tree, (bx - 1600, by - 400),
                                    _x_off(tree, (bx - 2800, by - 400),
                                           _m(tree, "MULTIPLY",
                                              (bx - 3000, by - 400),
                                              H, 0.28), x_off),
                                    0.0, 0.0))
    arch1_w = _m(tree, "MULTIPLY", (bx - 2600, by - 560), H, 0.28)
    arch1 = _plate(tree, (bx - 1400, by - 720), arch1_w, T, T,
                    translation=_vec(tree, (bx - 1600, by - 720),
                                     _x_off(tree, (bx - 2800, by - 720),
                                            _m(tree, "MULTIPLY",
                                               (bx - 3000, by - 720),
                                               H, 0.14), x_off),
                                     _m(tree, "MULTIPLY",
                                        (bx - 2800, by - 880),
                                        H, 0.30),
                                     0.0))
    arch2_w = _m(tree, "MULTIPLY", (bx - 2600, by - 880), H, 0.28)
    arch2 = _plate(tree, (bx - 1400, by - 1040), arch2_w, T, T,
                    translation=_vec(tree, (bx - 1600, by - 1040),
                                     _x_off(tree, (bx - 2800, by - 1040),
                                            _m(tree, "MULTIPLY",
                                               (bx - 3000, by - 1040),
                                               H, 0.42), x_off),
                                     _m(tree, "MULTIPLY",
                                        (bx - 2800, by - 1200),
                                        H, 0.30),
                                     0.0))
    return [stem1, stem2, arch1, arch2]


def _dynamic_glyph(group_name, parts_fn):
    """A dynamic letter glyph: build the parts, join, finish."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    H, T = _glyph_common(tree, gin, bx, by)
    parts = parts_fn(tree, gin, bx, by, H, T)
    parts = [p for p in parts if p is not None]
    geom = _join(tree, (bx + 400, by), parts)
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 5.0))
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Letter", "nodes": ("Cube", "Cylinder", "Transform"),
         "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


def build_music_dynamic_f(group_name="MEL_music_dynamic_f"):
    """Forte - the letter 'f'."""
    return _dynamic_glyph(group_name, _dynamic_f)


def build_music_dynamic_p(group_name="MEL_music_dynamic_p"):
    """Piano - the letter 'p'."""
    return _dynamic_glyph(group_name, _dynamic_p)


def build_music_dynamic_mf(group_name="MEL_music_dynamic_mf"):
    """Mezzo-forte - 'mf' (m at x=0, f at x=0.55H)."""
    def parts_fn(tree, gin, bx, by, H, T):
        m = _dynamic_m(tree, gin, bx, by, H, T, x_off=0.0)
        xo = _m(tree, "MULTIPLY", (bx - 3400, by), H, 0.55)
        f = _dynamic_f(tree, gin, bx, by, H, T, x_off=xo)
        return m + f
    return _dynamic_glyph(group_name, parts_fn)


def build_music_dynamic_mp(group_name="MEL_music_dynamic_mp"):
    """Mezzo-piano - 'mp' (m at x=0, p at x=0.55H)."""
    def parts_fn(tree, gin, bx, by, H, T):
        m = _dynamic_m(tree, gin, bx, by, H, T, x_off=0.0)
        xo = _m(tree, "MULTIPLY", (bx - 3400, by), H, 0.55)
        p = _dynamic_p(tree, gin, bx, by, H, T, x_off=xo)
        return m + p
    return _dynamic_glyph(group_name, parts_fn)


def build_music_dynamic_ff(group_name="MEL_music_dynamic_ff"):
    """Fortissimo - 'ff' (two f's side by side)."""
    def parts_fn(tree, gin, bx, by, H, T):
        f1 = _dynamic_f(tree, gin, bx, by, H, T, x_off=0.0)
        xo = _m(tree, "MULTIPLY", (bx - 3400, by), H, 0.45)
        f2 = _dynamic_f(tree, gin, bx, by, H, T, x_off=xo)
        return f1 + f2
    return _dynamic_glyph(group_name, parts_fn)


def build_music_dynamic_pp(group_name="MEL_music_dynamic_pp"):
    """Pianissimo - 'pp' (two p's side by side)."""
    def parts_fn(tree, gin, bx, by, H, T):
        p1 = _dynamic_p(tree, gin, bx, by, H, T, x_off=0.0)
        xo = _m(tree, "MULTIPLY", (bx - 3400, by), H, 0.45)
        p2 = _dynamic_p(tree, gin, bx, by, H, T, x_off=xo)
        return p1 + p2
    return _dynamic_glyph(group_name, parts_fn)


# ---------------------------------------------------------------------------
# Hairpins: crescendo, decrescendo
# ---------------------------------------------------------------------------

def _wedge(tree, loc, length, ang, thick, base, sgn):
    """Two bars that SHARE one endpoint (the apex) and open at the other.

    The lane's ONE wedge law, used by the hairpins and by the accent mark
    (which is the same mark at a compact scale). A bar of `length` rotated by
    `ang` has half-extents `(dx, dy) = half_l x (cos ang, sin ang)`; the two
    bars are rotated `+ang` and `-ang` and seated at `Y = +/- dy/2`, which makes
    them share the endpoint `(-dx, 0)` and open at `(+dx, +/-dy)` - a wedge
    spanning `2 x dx` in X with a `2 x dy` mouth. Measured at the defaults:
    X extent 0.4735, Y extent 0.2748 = `3 x half_l x sin(ang) + thick x cos(ang)`
    (`Saved/Audit/probe_w19_hairpin2.py`).

    `base` sets the direction and is the ONLY thing that mirrors the wedge: a
    box rotated by `ang` and by `ang + 180` is the same box, so a bare sign flip
    cannot mirror it. `base` 0.0 puts the apex on the LEFT (a `<`), `pi` on the
    RIGHT (a `>`). `sgn` = +/-1.0 swaps which bar sits above.

    Returns `(upper, lower)` geometry sockets.
    """
    bx, by = loc
    half_l = _m(tree, "MULTIPLY", (bx - 400, by + 160), length, 0.5)
    dy = _m(tree, "MULTIPLY", (bx - 400, by - 160), half_l,
            _m(tree, "SINE", (bx - 600, by - 160), ang))
    half_dy = _m(tree, "MULTIPLY", (bx - 400, by - 320), dy, 0.5)
    neg_half_dy = _m(tree, "MULTIPLY", (bx - 400, by - 480), half_dy, -1.0)

    def _rot(loc2, sign):
        return _vec(tree, loc2, 0.0, 0.0,
                    _m(tree, "ADD", (loc2[0] - 200, loc2[1] - 140), base,
                       _m(tree, "MULTIPLY", (loc2[0] - 400, loc2[1] - 280),
                          ang, sign)))

    upper = _plate(tree, (bx, by), length, thick, thick,
                   rotation=_rot((bx - 200, by + 160), sgn),
                   translation=_vec(tree, (bx - 200, by), 0.0, half_dy, 0.0))
    lower = _plate(tree, (bx, by - 400), length, thick, thick,
                   rotation=_rot((bx - 200, by - 240), -sgn),
                   translation=_vec(tree, (bx - 200, by - 400), 0.0,
                                   neg_half_dy, 0.0))
    return upper, lower


def _hairpin(group_name, flip):
    """A hairpin: the lane's wedge law at full length, apex left or right.

    `flip` = +1.0 puts the apex on the LEFT so the wedge opens to the RIGHT
    (crescendo, `<`); -1.0 puts it on the RIGHT (decrescendo, `>`).

    MEASURED DEFECT, wave 19 (`Saved/Audit/probe_w19_parts.py`): the wave-18
    draft computed `dy` and then used it NOWHERE. Both bars were seated at
    Y = 0 with equal and opposite rotations, i.e. two equal bars crossed at
    their own centres - an X mark, not a wedge. Neither the aggregate
    vert/face/degen/diag envelope nor this lane's own G assertion saw it,
    because the two arrangements have IDENTICAL X extents and differ in Y by
    exactly `dy` (0.2006 crossed vs 0.2748 wedge) - only a closed-form shape
    check separates them.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Hairpin Angle", 18.0, 5.0, 40.0)
    add_float_param(tree, "Hairpin Length Ratio", 0.80, 0.40, 1.20)

    length = _m(tree, "MULTIPLY", (bx - 2600, by + 160), H,
                gin.outputs["Hairpin Length Ratio"])
    ang = _radians(tree, (bx - 2600, by), gin.outputs["Hairpin Angle"])
    base = 0.0 if flip > 0 else math.pi
    sgn = 1.0 if flip > 0 else -1.0

    upper, lower = _wedge(tree, (bx - 1600, by), length, ang, T, base, sgn)
    geom = _join(tree, (bx + 400, by), [upper, lower])
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 6.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Wedge", "nodes": ("Cube", "Transform"), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


def build_music_hairpin_cresc(group_name="MEL_music_hairpin_cresc"):
    """Crescendo - two lines meeting at the LEFT (opens to the right, <)."""
    return _hairpin(group_name, 1.0)


def build_music_hairpin_decresc(group_name="MEL_music_hairpin_decresc"):
    """Decrescendo - two lines meeting at the RIGHT (opens to the left, >)."""
    return _hairpin(group_name, -1.0)


# ---------------------------------------------------------------------------
# MEL_music_percussion_clef - two thick vertical bars
# ---------------------------------------------------------------------------

def build_music_percussion_clef(group_name="MEL_music_percussion_clef"):
    """Percussion clef - two thick vertical bars side by side.

    The two bars are identical plates separated by `Bar Gap`. The glyph is
    centred on the staff (Y centre = 0).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Bar Gap", 0.18, 0.08, 0.40)
    add_float_param(tree, "Bar Width Ratio", 0.32, 0.15, 0.60)

    gap = gin.outputs["Bar Gap"]
    bar_w = _m(tree, "MULTIPLY", (bx - 2600, by + 160), H,
               gin.outputs["Bar Width Ratio"])
    half_gap = _half(tree, (bx - 2600, by), gap)

    bar1 = _plate(tree, (bx - 1400, by), bar_w, H, T,
                  translation=_vec(tree, (bx - 1600, by),
                                   _neg(tree, (bx - 2800, by), half_gap),
                                   0.0, 0.0))
    bar2 = _plate(tree, (bx - 1400, by - 400), bar_w, H, T,
                  translation=_vec(tree, (bx - 1600, by - 400),
                                   half_gap, 0.0, 0.0))

    geom = _join(tree, (bx + 400, by), [bar1, bar2])
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 7.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bars", "nodes": ("Cube",), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Articulation accents: staccato, accent, marcato - ONE mark law, three seats
# ---------------------------------------------------------------------------

def _mark_common(tree, gin, bx, by):
    """The articulation marks' shared size params (staff-relative, like a rest).

    The Scale param MUST be named `Scale`: `_finish` (music_string_kit) reads
    `gin.outputs["Scale"]` to apply the lane Scale before the export tail, so a
    differently-named dial raises `KeyError: 'Scale'` at build time.
    """
    add_float_param(tree, "Line Spacing", 0.13, 0.040, 0.400)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)
    return gin.outputs["Line Spacing"]


def build_music_staccato(group_name="MEL_music_staccato"):
    """Staccato - a small solid DOT placed on the note's own Y.

    Real notation puts the staccato dot on the OPPOSITE side of the note head
    from the stem, so the mark sits at Y = 0 on the staff line - which is why
    this builder carries no seat parameter at all while its two siblings do.
    The dot is a capped cylinder (a solid disc), never a ring: a staccato is a
    filled mark.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    LS = _mark_common(tree, gin, bx, by)
    add_float_param(tree, "Dot Radius Ratio", 0.20, 0.08, 0.40)

    r = _m(tree, "MULTIPLY", (bx - 2600, by + 160), LS,
           gin.outputs["Dot Radius Ratio"])
    depth = _m(tree, "MULTIPLY", (bx - 2600, by), LS, 0.10)
    prim = _cyl(tree, (bx - 1400, by), r, depth, vertices=20, fill=2)

    geom = prim.outputs["Mesh"] if prim is not None else None
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1600), 8.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Dot", "nodes": ("Cylinder",), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


def build_music_accent(group_name="MEL_music_accent"):
    """Accent - a compact `>`: the lane's WEDGE law at accent scale.

    Probed rather than assumed (`Saved/Audit/probe_w19_shape.py`): at
    `Mark Length Ratio` 0.55, `Mark Angle` 45 and `Mark Thickness Ratio` 0.12
    the mark measures X 0.0616 against Y 0.0869, i.e. a Y/X aspect of 1.41 with
    a mouth (`2 x half_l x sin ang` = 0.0506) more than 3x its own bar
    thickness (0.0156). BOTH halves of that matter: the aspect is what makes it
    an accent rather than a hairpin, and the mouth-vs-thickness ratio is what
    makes it a `>` rather than a solid blob - a first pass at a thicker stroke
    put the mouth at 0.023 against a 0.029 thickness, so the bars overlapped
    and the mark had no opening at all.

    The apex points RIGHT (`base` = pi), which is what makes this a `>`: with
    the default `base` 0 the same law renders `<`, i.e. a miniature crescendo,
    and the first render of this builder did exactly that. The apex direction
    is asserted structurally (D2), because it is the one property the aspect
    and the extent both preserve under a mirror.

    Reusing `_wedge` rather than re-deriving the two seats is the whole point:
    a second hand-rolled wedge is how the wave-18 crossed-bar defect happened.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    LS = _mark_common(tree, gin, bx, by)
    add_float_param(tree, "Mark Length Ratio", 0.55, 0.10, 0.80)
    add_float_param(tree, "Mark Angle", 45.0, 10.0, 60.0)
    add_float_param(tree, "Mark Thickness Ratio", 0.12, 0.04, 0.30)

    length = _m(tree, "MULTIPLY", (bx - 2600, by + 160), LS,
                gin.outputs["Mark Length Ratio"])
    ang = _radians(tree, (bx - 2600, by), gin.outputs["Mark Angle"])
    thick = _m(tree, "MULTIPLY", (bx - 2600, by - 160), LS,
               gin.outputs["Mark Thickness Ratio"])

    upper, lower = _wedge(tree, (bx - 1600, by), length, ang, thick,
                          math.pi, -1.0)
    geom = _join(tree, (bx + 400, by), [upper, lower])
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 8.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Wedge", "nodes": ("Cube", "Transform"), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


def build_music_marcato(group_name="MEL_music_marcato"):
    """Marcato - a STEEP narrow wedge (`^`), the accent's own law at a second seat.

    The separating law is arithmetic, not a parameter: the SAME `_wedge` law
    with `Mark Angle` 75 and `Mark Length Ratio` 0.45 measures X 0.0354 against
    Y 0.1193, a Y/X aspect of 3.37 - well over twice the accent's 1.41, and its
    mouth (0.0566) still clears its own thickness (0.0156). The gate asserts the
    ASPECT RATIO between the two marks rather than either number, so a dial
    change cannot silently collapse them into one glyph.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    LS = _mark_common(tree, gin, bx, by)
    add_float_param(tree, "Mark Length Ratio", 0.45, 0.10, 0.90)
    add_float_param(tree, "Mark Angle", 75.0, 40.0, 85.0)
    add_float_param(tree, "Mark Thickness Ratio", 0.12, 0.04, 0.30)

    length = _m(tree, "MULTIPLY", (bx - 2600, by + 160), LS,
                gin.outputs["Mark Length Ratio"])
    ang = _radians(tree, (bx - 2600, by), gin.outputs["Mark Angle"])
    thick = _m(tree, "MULTIPLY", (bx - 2600, by - 160), LS,
               gin.outputs["Mark Thickness Ratio"])

    upper, lower = _wedge(tree, (bx - 1600, by), length, ang, thick,
                          math.pi, -1.0)
    geom = _join(tree, (bx + 400, by), [upper, lower])
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 8.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Steep Wedge", "nodes": ("Cube", "Transform"),
         "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Dotted notes - ONE augmentation-dot law at three durations
# ---------------------------------------------------------------------------

def build_music_note_dotted(group_name, hollow, has_flag):
    """A dotted note: the wave-17 duration note plus ONE augmentation dot.

    The dot is a strict function of the note's own head, not a free-floating
    mark: its radius is `Dot Radius Ratio x Head Height` and its seat is
    `Head Width + Head Height x Dot Offset Ratio` along X, so it scales with the
    head it augments. That is the law the gate asserts (the dot's Radius and
    Translation BOTH trace to head-sized inputs) - a dot sized from `Line
    Spacing` would be a second, independent glyph.

    The three durations reuse the wave-17 table exactly (hollow head at the
    half, filled at the quarter, plus the eighth's flag), so a dotted note
    differs from its undotted sibling by the DOT and nothing else.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    _common_params(tree, gin, bx, by)
    add_float_param(tree, "Head Width", 0.115, 0.040, 0.300)
    add_float_param(tree, "Head Height", 0.082, 0.030, 0.220)
    add_float_param(tree, "Head Stroke", 0.013, 0.004, 0.040)
    add_float_param(tree, "Head Tilt", 20.0, 0.0, 45.0)
    add_float_param(tree, "Stem Length", 0.44, 0.15, 0.90)
    add_float_param(tree, "Stem Thickness", 0.022, 0.008, 0.060)
    add_float_param(tree, "Dot Radius Ratio", 0.17, 0.05, 0.40)
    add_float_param(tree, "Dot Offset Ratio", 0.55, 0.10, 1.20)
    if has_flag:
        add_float_param(tree, "Flag Reach", 0.16, 0.05, 0.40)
        add_float_param(tree, "Flag Drop", 0.22, 0.06, 0.50)
        add_float_param(tree, "Flag Thickness", 0.017, 0.005, 0.045)

    hw = gin.outputs["Head Width"]
    hh = gin.outputs["Head Height"]
    stroke = gin.outputs["Head Stroke"]
    tilt = _vec(tree, (bx - 1800, by + 200), 0.0, 0.0,
                _radians(tree, (bx - 2000, by + 200),
                         gin.outputs["Head Tilt"]))

    head = _head(tree, (bx - 1400, by), hollow, hw, hh, tilt, stroke)

    parts = [head]
    tilt_rad = _radians(tree, (bx - 2000, by - 200),
                        gin.outputs["Head Tilt"])
    stem_x = _m(tree, "MULTIPLY", (bx - 1800, by - 200), hw,
                _m(tree, "COSINE", (bx - 2000, by - 400), tilt_rad))
    parts.append(_stem(tree, (bx - 1000, by - 200), hw, tilt_rad,
                       gin.outputs["Stem Length"],
                       gin.outputs["Stem Thickness"]))
    if has_flag:
        parts.append(_flag(tree, (bx - 200, by - 400), stem_x,
                           gin.outputs["Stem Length"],
                           gin.outputs["Flag Reach"],
                           gin.outputs["Flag Drop"],
                           gin.outputs["Flag Thickness"]))

    # the augmentation dot: sized by the HEAD and seated clear of its right edge
    dot_r = _m(tree, "MULTIPLY", (bx - 2200, by - 900), hh,
               gin.outputs["Dot Radius Ratio"])
    dot_off = _m(tree, "MULTIPLY", (bx - 2200, by - 1060), hh,
                 gin.outputs["Dot Offset Ratio"])
    dot_x = _m(tree, "ADD", (bx - 2200, by - 1220), hw, dot_off)
    dot_depth = _m(tree, "MULTIPLY", (bx - 2200, by - 1380), hh, 0.25)
    prim = _cyl(tree, (bx - 1000, by - 1000), dot_r, dot_depth,
                vertices=20, fill=2)
    if prim is not None:
        parts.append(_xf(tree, (bx - 800, by - 1000), prim.outputs["Mesh"],
                         translation=_vec(tree, (bx - 800, by - 1200),
                                          dot_x, 0.0, 0.0)).outputs["Geometry"])

    geom = _join(tree, (bx + 900, by), parts)
    _finish(tree, gin, gout, geom, (bx + 1200, by), group_name,
            _glyph_attrs(tree, (bx + 900, by - 2600), 9.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Head", "nodes": ("Circle", "Cylinder", "Curve to Mesh"),
         "role": "geometry"},
        {"title": "Stem And Flag", "nodes": ("Cube", "Bezier", "Transform"),
         "role": "geometry"},
        {"title": "Augmentation Dot", "nodes": ("Cylinder",),
         "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


def build_music_note_dotted_half(group_name="MEL_music_note_dotted_half"):
    """Dotted half note - the half note's HOLLOW head + stem + one dot."""
    return build_music_note_dotted(group_name, hollow=True, has_flag=False)


def build_music_note_dotted_quarter(group_name="MEL_music_note_dotted_quarter"):
    """Dotted quarter note - the quarter note's FILLED head + stem + one dot."""
    return build_music_note_dotted(group_name, hollow=False, has_flag=False)


def build_music_note_dotted_eighth(group_name="MEL_music_note_dotted_eighth"):
    """Dotted eighth note - the eighth note's FILLED head + stem + flag + dot."""
    return build_music_note_dotted(group_name, hollow=False, has_flag=True)


# -- Registry ---------------------------------------------------------------

register_builder("MEL_music_staccato", build_music_staccato,
                 "Music Staccato",
                 "Staccato - a small solid dot on the note's own Y",
                 "music")
register_builder("MEL_music_accent", build_music_accent,
                 "Music Accent",
                 "Accent - a compact >, the wedge law at accent scale",
                 "music")
register_builder("MEL_music_marcato", build_music_marcato,
                 "Music Marcato",
                 "Marcato - a steep narrow wedge, the accent's law at a "
                 "second seat",
                 "music")
register_builder("MEL_music_note_dotted_half", build_music_note_dotted_half,
                 "Music Dotted Half Note",
                 "Dotted half note - hollow head, stem, one augmentation dot",
                 "music")
register_builder("MEL_music_note_dotted_quarter",
                 build_music_note_dotted_quarter,
                 "Music Dotted Quarter Note",
                 "Dotted quarter note - filled head, stem, one augmentation dot",
                 "music")
register_builder("MEL_music_note_dotted_eighth",
                 build_music_note_dotted_eighth,
                 "Music Dotted Eighth Note",
                 "Dotted eighth note - filled head, stem, flag, one "
                 "augmentation dot",
                 "music")
register_builder("MEL_music_note_sixteenth", build_music_note_sixteenth,
                 "Music Sixteenth Note",
                 "Sixteenth note - filled head, stem, and two flags",
                 "music")
register_builder("MEL_music_rest_eighth", build_music_rest_eighth,
                 "Music Eighth Rest",
                 "Eighth rest - diagonal slash with one dot",
                 "music")
register_builder("MEL_music_rest_sixteenth", build_music_rest_sixteenth,
                 "Music Sixteenth Rest",
                 "Sixteenth rest - diagonal slash with two dots",
                 "music")
register_builder("MEL_music_dynamic_f", build_music_dynamic_f,
                 "Music Dynamic Forte",
                 "Forte - the letter f",
                 "music")
register_builder("MEL_music_dynamic_p", build_music_dynamic_p,
                 "Music Dynamic Piano",
                 "Piano - the letter p",
                 "music")
register_builder("MEL_music_dynamic_mf", build_music_dynamic_mf,
                 "Music Dynamic Mezzo-Forte",
                 "Mezzo-forte - mf",
                 "music")
register_builder("MEL_music_dynamic_mp", build_music_dynamic_mp,
                 "Music Dynamic Mezzo-Piano",
                 "Mezzo-piano - mp",
                 "music")
register_builder("MEL_music_dynamic_ff", build_music_dynamic_ff,
                 "Music Dynamic Fortissimo",
                 "Fortissimo - ff",
                 "music")
register_builder("MEL_music_dynamic_pp", build_music_dynamic_pp,
                 "Music Dynamic Pianissimo",
                 "Pianissimo - pp",
                 "music")
register_builder("MEL_music_hairpin_cresc", build_music_hairpin_cresc,
                 "Music Hairpin Crescendo",
                 "Crescendo - two lines meeting at the left",
                 "music")
register_builder("MEL_music_hairpin_decresc", build_music_hairpin_decresc,
                 "Music Hairpin Decrescendo",
                 "Decrescendo - two lines meeting at the right",
                 "music")
register_builder("MEL_music_percussion_clef", build_music_percussion_clef,
                 "Music Percussion Clef",
                 "Percussion clef - two thick vertical bars",
                 "music")
