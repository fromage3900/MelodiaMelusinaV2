"""P5 wave 17 - duration note lane: whole / half / quarter / eighth + the two
block rests.

Gap audit first (repo-wide grep over `deploy/surreal_arch/` + the live registry +
`Tools/registry_baseline.json`, 2026-10-05): the notation family owns the treble,
bass, alto and tenor clefs, the note head, staff, beam cluster, triplet, chord
stack, fermata, repeat bar, meter sign, key unit, phrase, the sheet rails, the
sharp/flat/natural accidentals and the quarter rest. NONE of the six ids below
existed anywhere (grep count 0 each, and 0 in the baseline):

    whole note, half note, quarter note, eighth note, whole rest, half rest

`MEL_music_note_head` is a single ANATOMY-AGNOSTIC head (an ellipsoid with a
stem and a flag switched on by `Has Stem`/`Has Flag` booleans) - it is one
glyph, not the duration family, and it carries no hollow/filled distinction.
`MEL_music_rest_quarter` (wave 16) is a five-stroke calligraphic zigzag; the
whole and half rests are SOLID BLOCKS, a different anatomy entirely.

The four notes are ONE head law at two anatomies and three stem/flag seats, the
way the two C clefs are one body at two seats:

    duration   head      stem   flags
    whole      HOLLOW    no     0
    half       HOLLOW    yes    0
    quarter    FILLED    yes    0
    eighth     FILLED    yes    1

That table IS real notation (hollow = whole and half), so the gate can assert it
causally: the hollow head is a closed circle PATH swept with a circle profile
(a ring with a real hole, no boolean), the filled head is a capped cylinder -
both scaled by the SAME `Head Width` / `Head Height` chain, so the two
anatomies differ by construction, not by a parameter.

The two rests are likewise ONE block law at two seats, and this is the lane's
sharpest law: a half rest SITS ON staff line 3 (block bottom on the line) and a
whole rest HANGS FROM staff line 4 (block top on the line), so the two blocks
occupy the SAME staff space and touch edge-to-edge. `Staff Line` is the only
difference between them - the same `(Staff Line - 3) * Line Spacing` seat chain
the C clefs use, so both lanes agree on the staff coordinate system.

Design rules (same as music_notation_glyphs / music_wind_flute_family):
  - Native-only. A glyph is swept strokes, plates and a swept ring that 5.2
    primitives express exactly; a Higgsas subtree here would be decoration, not
    a lead. Every builder still stores `higgsas_lead` (1.0 = native) so the
    family gate reads the lane uniformly.
  - The shared helpers are REUSED, never re-authored: `_sweep` /
    `_profile_circle` / `_profile_out` (notation_extras, the proven XY-glyph
    tube idiom - no profile rotation, because a glyph lives in the XY plane),
    `_plate` (music_keyboard_kit - links all three `Size` components), `_cyl` /
    `_xf` / `_store_named` (music_higgsas_instruments), `_join` / `_vec`
    (music_wind_reed_brass), `_m` / `_math` / `_combine`, and `_finish`
    (music_string_kit - applies Scale BEFORE the export tail, which the shared
    `_export_tail` does not).
  - Zero `MeshBoolean` in the lane: a cutter that touches the mesh's own
    boundary emits ZERO geometry with no error and no `link_failures` entry.
    The hollow head's hole is a swept RING, not a cut.
  - A literal rotation tuple lands in a socket's `default_value`, never in a
    link, so the head TILT is a linked CombineXYZ fed by `Head Tilt` - a gate
    can then prove the tilt is real rather than reading an absent link as
    "no tilt".
  - The stem's X seat is `Head Width * cos(Head Tilt)`, not `Head Width`: the
    head is a TILTED ellipse, so its right extremity is inside the un-tilted
    semi-axis and a stem placed at `Head Width` would float clear of the head
    it is supposed to be attached to (the wave-16 floating-connector class).

Builders:
    MEL_music_note_whole    hollow head, no stem
    MEL_music_note_half     hollow head + stem
    MEL_music_note_quarter  filled head + stem
    MEL_music_note_eighth   filled head + stem + one flag
    MEL_music_rest_whole    solid block hanging from staff line 4
    MEL_music_rest_half     solid block seated on staff line 3
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

def _radians(tree, loc, deg_sock):
    return _m(tree, "MULTIPLY", loc, deg_sock, math.pi / 180.0)


def _head(tree, loc, hollow, hw, hh, tilt, stroke, verts=24):
    """A note head: one ellipse law, two anatomies.

    HOLLOW (whole / half) is a closed `CurvePrimitiveCircle` PATH scaled into the
    ellipse and swept with a circle profile - a ring with a real hole and NO
    boolean. FILLED (quarter / eighth) is a capped cylinder scaled by the SAME
    vector. Both are scaled by `(hw, hh, 1)` and rotated by `tilt`, so the two
    anatomies differ by construction while sharing the size chain - and both
    measure the same Z extent (`2 x Head Stroke`), which the gate asserts.

    Probed 2026-10-05 (`Saved/Audit/probe_w17_api.py`): a default
    `CurvePrimitiveCircle` (radius 1, CLOSED) swept with a radius-0.22 circle
    profile is a clean torus - 256 verts, 0 degenerate faces, extents
    x/y +/-1.22 and z +/-0.22 exactly.
    """
    bx, by = loc
    if hollow:
        path = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx, by))
        if path is None:
            return None
        rs = sock(path, "Resolution")
        if rs is not None:
            try:
                rs.default_value = 24
            except Exception:
                pass
        scaled = _xf(tree, (bx + 300, by), path.outputs["Curve"],
                     rotation=tilt,
                     scale=_vec(tree, (bx + 300, by - 220), hw, hh, 1.0))
        prof = _profile_circle(tree, bx + 600, by - 460, stroke, vertices=8)
        sweep = _sweep(tree, bx + 900, by, scaled.outputs["Geometry"],
                       _profile_out(prof))
        if sweep is None:
            return None
        fs = sock(sweep, "Fill Caps")
        if fs is not None:
            try:
                fs.default_value = False
            except Exception:
                pass
        return sweep.outputs["Mesh"]
    depth = _m(tree, "MULTIPLY", (bx - 300, by - 320), stroke, 2.0)
    prim = _cyl(tree, (bx, by), 1.0, depth, vertices=verts, fill=2)
    if prim is None:
        return None
    return _xf(tree, (bx + 300, by), prim.outputs["Mesh"],
               rotation=tilt,
               scale=_vec(tree, (bx + 300, by - 220), hw, hh, 1.0)
               ).outputs["Geometry"]


def _stem(tree, loc, head_w, tilt_rad, length, thick):
    """A stem rising from the head's RIGHT edge to `length`.

    Its X seat is `Head Width * cos(Head Tilt)`: the head is a TILTED ellipse,
    so its right extremity sits INSIDE the un-tilted semi-axis and a stem at
    `Head Width` would hang clear of the head. The chain is linked (never a
    baked constant), so the gate can prove the stem reads BOTH `Head Width` and
    `Head Tilt` through a COSINE.
    """
    bx, by = loc
    cos_t = _m(tree, "COSINE", (bx - 400, by + 200), tilt_rad)
    seat_x = _m(tree, "MULTIPLY", (bx - 200, by + 200), head_w, cos_t)
    half_len = _m(tree, "MULTIPLY", (bx - 200, by), length, 0.5)
    return _plate(tree, (bx, by), thick, length, thick,
                  translation=_vec(tree, (bx - 200, by - 200),
                                  seat_x, half_len, 0.0))


def _flag(tree, loc, x0, y0, reach, drop, thick):
    """One eighth-note flag: a bezier hook off the stem's TOP, tube-swept.

    Start is the stem's top `(x0, y0) = (stem_x, Stem Length)`; the curve leaves
    it heading +X and arrives at `(x0 + reach, y0 - drop)`. Every point is a
    live socket, so the gate can prove the flag is anchored to the stem's own
    top and sized by `Flag Reach` / `Flag Drop`.
    """
    bx, by = loc
    seg = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (bx, by))
    if seg is None:
        return None
    h1x = _m(tree, "MULTIPLY", (bx - 1400, by - 400), reach, 0.55)
    h1y = _m(tree, "MULTIPLY", (bx - 1400, by - 560), drop, 0.05)
    h2x = _m(tree, "MULTIPLY", (bx - 1200, by - 720), reach, 0.95)
    h2y = _m(tree, "MULTIPLY", (bx - 1200, by - 880), drop, 0.45)
    link_sockets(tree, _vec(tree, (bx - 800, by + 300), x0, y0, 0.0),
                 sock(seg, "Start"))
    link_sockets(tree, _vec(tree, (bx - 800, by + 100),
                            _m(tree, "ADD", (bx - 1000, by + 100), x0, h1x),
                            _m(tree, "SUBTRACT", (bx - 1000, by - 60), y0, h1y),
                            0.0),
                 sock(seg, "Start Handle"))
    link_sockets(tree, _vec(tree, (bx - 800, by - 100),
                            _m(tree, "ADD", (bx - 1000, by - 100), x0, h2x),
                            _m(tree, "SUBTRACT", (bx - 1000, by - 260), y0, h2y),
                            0.0),
                 sock(seg, "End Handle"))
    link_sockets(tree, _vec(tree, (bx - 800, by - 300),
                            _m(tree, "ADD", (bx - 1000, by - 300), x0, reach),
                            _m(tree, "SUBTRACT", (bx - 1000, by - 460), y0, drop),
                            0.0),
                 sock(seg, "End"))
    rs = sock(seg, "Resolution")
    if rs is not None:
        try:
            rs.default_value = 8
        except Exception:
            pass
    prof = _profile_circle(tree, bx + 200, by - 700, thick, vertices=8)
    sweep = _sweep(tree, bx + 500, by, seg.outputs["Curve"],
                   _profile_out(prof))
    if sweep is None:
        return None
    fs = sock(sweep, "Fill Caps")
    if fs is not None:
        try:
            fs.default_value = False
        except Exception:
            pass
    return sweep.outputs["Mesh"]


def _glyph_attrs(tree, loc, family_value):
    """The notation family's shared attribute triple (wave-16 convention).

    `glyph_semitone_mod12` is the house index->element-palette key every lane
    stores, `glyph_family` carries the real semantic class (3 rest / 4 duration
    note - the wave-16 clef=1 / accidental=2 numbering continues), and
    `higgsas_lead` = 1.0 records that this lane's lead is native.
    """
    bx, by = loc
    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx, by))
    smod = _m(tree, "FLOORMOD", (bx, by - 140), sidx.outputs["Index"], 12.0)
    return [("glyph_semitone_mod12", smod),
            ("glyph_family", float(family_value)),
            ("higgsas_lead", 1.0)]


def _common_params(tree, gin, bx, by):
    """Params every glyph in the lane exposes, plus the shared Scale sockets."""
    add_float_param(tree, "Line Spacing", 0.13, 0.040, 0.400)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)
    return gin.outputs["Line Spacing"]


# ---------------------------------------------------------------------------
# MEL_music_note_whole / _half / _quarter / _eighth - one head law, four seats
# ---------------------------------------------------------------------------

def _duration_note(group_name, hollow, has_stem, has_flag):
    """A duration note: ONE head law, an optional stem, an optional flag.

    `hollow` picks the head anatomy (swept ring vs capped cylinder) and
    `has_stem` / `has_flag` add the stroke and the hook. The three booleans ARE
    the duration table, so the gate can assert the anatomy of each id rather
    than a parameter snapshot.
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
    stem_x = None
    if has_stem:
        tilt_rad = _radians(tree, (bx - 2000, by - 200),
                            gin.outputs["Head Tilt"])
        stem_x = _m(tree, "MULTIPLY", (bx - 1800, by - 200), hw,
                    _m(tree, "COSINE", (bx - 2000, by - 400), tilt_rad))
        stem = _stem(tree, (bx - 1000, by - 200), hw, tilt_rad,
                     gin.outputs["Stem Length"],
                     gin.outputs["Stem Thickness"])
        parts.append(stem)
        if has_flag:
            parts.append(_flag(tree, (bx - 200, by - 400), stem_x,
                               gin.outputs["Stem Length"],
                               gin.outputs["Flag Reach"],
                               gin.outputs["Flag Drop"],
                               gin.outputs["Flag Thickness"]))

    geom = _join(tree, (bx + 900, by), parts)
    _finish(tree, gin, gout, geom, (bx + 1200, by), group_name,
            _glyph_attrs(tree, (bx + 900, by - 2400), 4.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Head", "nodes": ("Circle", "Cylinder", "Curve to Mesh"),
         "role": "geometry"},
        {"title": "Stem And Flag", "nodes": ("Cube", "Bezier", "Transform"),
         "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


def build_music_note_whole(group_name="MEL_music_note_whole"):
    """Whole note - a HOLLOW head and nothing else: no stem, no flag."""
    return _duration_note(group_name, hollow=True, has_stem=False,
                          has_flag=False)


def build_music_note_half(group_name="MEL_music_note_half"):
    """Half note - the whole note's HOLLOW head plus a stem."""
    return _duration_note(group_name, hollow=True, has_stem=True,
                          has_flag=False)


def build_music_note_quarter(group_name="MEL_music_note_quarter"):
    """Quarter note - a FILLED head plus a stem (hollow stops at the half)."""
    return _duration_note(group_name, hollow=False, has_stem=True,
                          has_flag=False)


def build_music_note_eighth(group_name="MEL_music_note_eighth"):
    """Eighth note - filled head, stem, and ONE flag hooking off the stem top."""
    return _duration_note(group_name, hollow=False, has_stem=True,
                          has_flag=True)


# ---------------------------------------------------------------------------
# MEL_music_rest_whole / MEL_music_rest_half - one block law, two seats
# ---------------------------------------------------------------------------

def _rest_block(group_name, default_line, side):
    """A block rest: a solid rectangle seated on / hanging from a staff line.

    `side` = +1.0 seats the block ON its line (bottom edge on the line, the HALF
    rest); -1.0 hangs it BELOW its line (top edge on the line, the WHOLE rest).
    Real notation puts the half rest on line 3 and the whole rest on line 4, so
    with one `Line Spacing` the two blocks occupy the SAME staff space and touch
    edge-to-edge - the gate measures both edges against the line each one owns.

    The seat is the SAME `(Staff Line - 3) * Line Spacing` chain the wave-16 C
    clefs use, so both notation lanes agree on the staff coordinate system.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    _common_params(tree, gin, bx, by)
    add_int_param(tree, "Staff Line", default_line, 1, 5)
    add_float_param(tree, "Rest Width Ratio", 1.30, 0.50, 2.50)
    add_float_param(tree, "Rest Height Ratio", 0.50, 0.20, 1.00)
    add_float_param(tree, "Rest Thickness", 0.050, 0.015, 0.160)

    # A block rest spans ONE staff space, so both of its plan dimensions are
    # ratios of `Line Spacing` - a rest is a staff-relative glyph, not a
    # free-floating one. `Rest Height Ratio` 0.5 is the notation law that makes
    # the whole rest's underside and the half rest's top edge the SAME line:
    # the two blocks fill one staff space and touch edge-to-edge, which is what
    # the gate measures (G).
    rest_w = _m(tree, "MULTIPLY", (bx - 2200, by + 460),
                gin.outputs["Rest Width Ratio"], gin.outputs["Line Spacing"])
    rest_h = _m(tree, "MULTIPLY", (bx - 2200, by + 290),
                gin.outputs["Rest Height Ratio"], gin.outputs["Line Spacing"])
    line_y = _m(tree, "MULTIPLY", (bx - 2200, by + 300),
                _m(tree, "SUBTRACT", (bx - 2400, by + 300),
                   gin.outputs["Staff Line"], 3.0),
                gin.outputs["Line Spacing"])
    half_h = _m(tree, "MULTIPLY", (bx - 2200, by + 120), rest_h, 0.5)
    seat = _m(tree, "ADD", (bx - 2200, by - 60), line_y,
              _m(tree, "MULTIPLY", (bx - 2400, by - 60), half_h, side))

    block = _plate(tree, (bx - 1400, by), rest_w, rest_h,
                   gin.outputs["Rest Thickness"],
                   translation=_vec(tree, (bx - 1600, by), 0.0, seat, 0.0))

    _finish(tree, gin, gout, block, (bx + 400, by), group_name,
            _glyph_attrs(tree, (bx + 100, by - 1600), 3.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Block", "nodes": ("Cube",), "role": "geometry"},
        {"title": "Staff Seat", "nodes": ("Transform", "Math"), "role": "math"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


def build_music_rest_whole(group_name="MEL_music_rest_whole"):
    """Whole rest - a solid block HANGING from staff line 4."""
    return _rest_block(group_name, 4, -1.0)


def build_music_rest_half(group_name="MEL_music_rest_half"):
    """Half rest - the SAME block SEATED ON staff line 3 (the whole rest's
    mirror; together the two fill one staff space)."""
    return _rest_block(group_name, 3, 1.0)


# -- Registry ---------------------------------------------------------------

register_builder("MEL_music_note_whole", build_music_note_whole,
                 "Music Whole Note",
                 "Whole note - hollow swept-ring head, no stem",
                 "music")
register_builder("MEL_music_note_half", build_music_note_half,
                 "Music Half Note",
                 "Half note - the whole note's hollow head plus a stem",
                 "music")
register_builder("MEL_music_note_quarter", build_music_note_quarter,
                 "Music Quarter Note",
                 "Quarter note - filled head plus stem",
                 "music")
register_builder("MEL_music_note_eighth", build_music_note_eighth,
                 "Music Eighth Note",
                 "Eighth note - filled head, stem, and one flag hooking off "
                 "the stem top",
                 "music")
register_builder("MEL_music_rest_whole", build_music_rest_whole,
                 "Music Whole Rest",
                 "Whole rest - solid block hanging from staff line 4",
                 "music")
register_builder("MEL_music_rest_half", build_music_rest_half,
                 "Music Half Rest",
                 "Half rest - the same block seated on staff line 3; the two "
                 "rests fill one staff space",
                 "music")
