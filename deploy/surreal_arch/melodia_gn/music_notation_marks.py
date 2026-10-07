"""P5 wave 20 - notation marks: thirty-second note, bar lines, tenuto, caesura.

Gap audit (repo-wide grep over `deploy/surreal_arch/` + the live registry +
`Tools/registry_baseline.json`, 2026-10-07): the notation family owns the
treble/bass/alto/tenor/percussion clefs, sharp/flat/natural, whole/half/
quarter/eighth/sixteenth notes, the dotted half/quarter/eighth, the whole/
half/quarter/eighth/sixteenth rests, f/p/mf/mp/ff/pp, both hairpins,
staccato/accent/marcato, the staff, beam cluster, triplet, chord stack,
fermata, repeat bar, meter sign, key unit and phrase. NONE of the six ids below
existed anywhere (grep count 0 each):

    thirty-second note, bar line, double bar line, final bar line,
    tenuto, caesura

Lane laws (one law, several seats - the shape every wave-16..19 lane follows):

  * The THIRTY-SECOND NOTE is the duration table's next row: the sixteenth
    note's law (filled head + stem + two flags) plus a THIRD flag. The three
    flags' seats are `fraction x Stem Length` down the stem, so the flag
    fractions ARE the row and the gate reads them back off the Start-Y math
    nodes rather than trusting a snapshot.
  * The THREE BAR LINES are ONE stroke law at three seats: a plain bar line is
    ONE thin stroke, a double bar line is TWO thin strokes separated by
    `Bar Gap`, and a final bar line is the SAME pair with the right-hand stroke
    thickened by `Thick Ratio`. A bar line's proportions are ratios of
    `Staff Height` (it spans the staff), not of a glyph height.
  * TENUTO is the articulation family's next member and its identity is its
    ORIENTATION: a short thick HORIZONTAL stroke, where staccato is a disc and
    accent/marcato are vertical wedges. The gate asserts the aspect, because a
    tenuto built vertical would be a second marcato.
  * CAESURA is two slanted thick strokes (`//`), the one law at two seats.

Design rules (same as music_notation_glyphs / music_note_durations /
music_notation_extras):
  - Native-only. Every builder stores `higgsas_lead` (1.0 = native) plus
    `glyph_semitone_mod12` and `glyph_family`, so the family gate reads the
    lane uniformly.
  - The shared helpers are REUSED, never re-authored: `_head` / `_stem` /
    `_flag` / `_common_params` (music_note_durations - the duration laws),
    `_neg` / `_half` / `_radians` (music_notation_extras), `_glyph_attrs`
    (music_notation_glyphs), `_plate` / `_m` (music_keyboard_kit - links all
    three `Size` components), `_xf` (music_higgsas_instruments), `_join` /
    `_vec` (music_wind_reed_brass), and `_finish` (music_string_kit - applies
    Scale BEFORE the export tail, which the shared `_export_tail` does not).
  - Zero `MeshBoolean` in the lane: a cutter that touches the mesh's own
    boundary emits ZERO geometry with no error and no `link_failures` entry.
    Every stroke here is laid on, not cut.
  - A literal rotation tuple lands in a socket's `default_value`, never in a
    link, so every tilt here is a linked CombineXYZ fed by a group input - a
    gate can then prove the tilt is real rather than reading an absent link as
    "no tilt".

Builders:
    MEL_music_note_thirty_second   filled head + stem + THREE flags
    MEL_music_bar_line             one thin stroke
    MEL_music_bar_double           two thin strokes
    MEL_music_bar_final            thin + thick stroke
    MEL_music_tenuto               one short thick horizontal stroke
    MEL_music_caesura              two slanted thick strokes
"""

from __future__ import annotations

from .core import (
    label_tree, new_geometry_tree, add_float_param, add_bool_param,
    register_builder,
)
from .music_higgsas_instruments import _xf
from .music_keyboard_kit import _m, _plate
from .music_string_kit import _finish
from .music_wind_reed_brass import _vec, _join
# The duration-note laws are REUSED, never re-authored: the head (one ellipse
# law, two anatomies), the stem and the flag live in music_note_durations, and
# the sign/angle helpers live in music_notation_extras.
from .music_note_durations import _common_params, _head, _stem, _flag
from .music_notation_extras import _neg, _half, _radians
from .music_notation_glyphs import _glyph_attrs


# ---------------------------------------------------------------------------
# MEL_music_note_thirty_second - the duration table's next row (THREE flags)
# ---------------------------------------------------------------------------

# The three flag seats, as fractions of `Stem Length` measured DOWN the stem.
# These fractions ARE the thirty-second row, so the gate reads them back off the
# Start-Y math nodes instead of trusting a parameter snapshot.
_FLAG_FRACTIONS = (1.00, 0.68, 0.36)


def build_music_note_thirty_second(group_name="MEL_music_note_thirty_second"):
    """Thirty-second note - filled head, stem, and THREE flags.

    The sixteenth note's law (`MEL_music_note_sixteenth`, wave 18) plus a third
    flag: the head is the same FILLED ellipse, the stem the same stroke off the
    head's tilted right edge, and the flags the same bezier hook at three
    descending seats.
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
    add_float_param(tree, "Flag Reach", 0.16, 0.05, 0.40)
    add_float_param(tree, "Flag Drop", 0.22, 0.06, 0.50)
    add_float_param(tree, "Flag Thickness", 0.017, 0.005, 0.045)

    hw = gin.outputs["Head Width"]
    hh = gin.outputs["Head Height"]
    stroke = gin.outputs["Head Stroke"]
    stem_len = gin.outputs["Stem Length"]
    tilt_rad = _radians(tree, (bx - 2000, by - 200),
                        gin.outputs["Head Tilt"])
    tilt = _vec(tree, (bx - 1800, by + 200), 0.0, 0.0, tilt_rad)

    head = _head(tree, (bx - 1400, by), False, hw, hh, tilt, stroke)

    stem_x = _m(tree, "MULTIPLY", (bx - 1800, by - 200), hw,
                _m(tree, "COSINE", (bx - 2000, by - 400), tilt_rad))
    stem = _stem(tree, (bx - 1000, by - 200), hw, tilt_rad, stem_len,
                 gin.outputs["Stem Thickness"])

    parts = [head, stem]
    for i, frac in enumerate(_FLAG_FRACTIONS):
        # Each flag's seat is its OWN `fraction x Stem Length` chain, so the
        # gate can walk Start -> CombineXYZ.Y -> MULTIPLY and read the fraction
        # back, proving the three seats are distinct and ordered.
        fy = _m(tree, "MULTIPLY", (bx - 600, by - 600 - i * 200),
                stem_len, frac)
        parts.append(_flag(tree, (bx - 200, by - 900 - i * 200), stem_x, fy,
                           gin.outputs["Flag Reach"],
                           gin.outputs["Flag Drop"],
                           gin.outputs["Flag Thickness"]))

    geom = _join(tree, (bx + 900, by), parts)
    _finish(tree, gin, gout, geom, (bx + 1200, by), group_name,
            _glyph_attrs(tree, (bx + 900, by - 2600), 4.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Head", "nodes": ("Cylinder", "Transform"),
         "role": "geometry"},
        {"title": "Stem And Three Flags",
         "nodes": ("Cube", "Bezier", "Transform"), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Bar lines: one stroke law, three seats
# ---------------------------------------------------------------------------

def _bar_stroke(tree, loc, height, thick, x_off, depth):
    """ONE bar stroke: `thick` along X, `height` along Y, `depth` along Z.

    A bar line is a vertical stroke, so its proportions are ratios of
    `Staff Height` (it spans the staff). `_plate` links all three `Size`
    components - an UNLINKED component defaults to 0 and produces the
    castle-merlon zero-width slab.

    The Z seat is written as a LITERAL 0.0 inside the CombineXYZ (a stroke lies
    in the glyph plane, it is not raised), so a gate reading the seat sees a
    literal rather than a missing link and can still walk X/Y to the stroke law.
    """
    return _plate(tree, loc, thick, height, depth,
                  translation=_vec(tree, (loc[0] - 400, loc[1] - 400),
                                   x_off, 0.0, 0.0))


def _bar_family(group_name, mode):
    """The bar-line law: `single` (one thin), `double` (two thin), `final`
    (thin + thick). The three seats share the stroke law, the staff height, the
    gap and the thickness dial, so a gate can prove they are one law.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Staff Height", 0.60, 0.20, 1.60)
    add_float_param(tree, "Bar Thickness", 0.030, 0.008, 0.090)
    add_float_param(tree, "Bar Gap", 0.075, 0.020, 0.200)
    add_float_param(tree, "Thick Ratio", 3.00, 1.50, 6.00)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    hgt = gin.outputs["Staff Height"]
    th = gin.outputs["Bar Thickness"]
    gap = gin.outputs["Bar Gap"]
    half_gap = _half(tree, (bx - 2600, by + 160), gap)
    neg_half_gap = _neg(tree, (bx - 2600, by + 320), half_gap)
    # the stroke's Z depth is its own thickness: the lane's glyph plane is XY,
    # so the extrusion depth is the same dial, never a second parameter
    depth = th

    parts = []
    if mode == "single":
        parts.append(_bar_stroke(tree, (bx - 1400, by), hgt, th, 0.0, depth))
    elif mode == "double":
        parts.append(_bar_stroke(tree, (bx - 1400, by), hgt, th,
                                 neg_half_gap, depth))
        parts.append(_bar_stroke(tree, (bx - 1400, by - 400), hgt, th,
                                 half_gap, depth))
    else:
        # final: the thin stroke on the left, the THICK one on the right
        thick = _m(tree, "MULTIPLY", (bx - 2600, by - 480), th,
                   gin.outputs["Thick Ratio"])
        parts.append(_bar_stroke(tree, (bx - 1400, by), hgt, th,
                                 neg_half_gap, depth))
        parts.append(_bar_stroke(tree, (bx - 1400, by - 400), hgt, thick,
                                 half_gap, depth))

    geom = _join(tree, (bx + 400, by), parts)
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 10.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bar Strokes", "nodes": ("Cube", "Transform"),
         "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


def build_music_bar_line(group_name="MEL_music_bar_line"):
    """Bar line - ONE thin stroke spanning the staff."""
    return _bar_family(group_name, "single")


def build_music_bar_double(group_name="MEL_music_bar_double"):
    """Double bar line - TWO thin strokes separated by `Bar Gap`."""
    return _bar_family(group_name, "double")


def build_music_bar_final(group_name="MEL_music_bar_final"):
    """Final bar line - the double pair with the right stroke thickened."""
    return _bar_family(group_name, "final")


# ---------------------------------------------------------------------------
# MEL_music_tenuto / MEL_music_caesura - the mark family's next two members
# ---------------------------------------------------------------------------

def _mark_common(tree, gin, bx, by):
    """The marks' shared size params (staff-relative, like a rest).

    The Scale param MUST be named `Scale`: `_finish` (music_string_kit) reads
    `gin.outputs["Scale"]` to apply the lane Scale before the export tail, so a
    differently-named dial raises `KeyError: 'Scale'` at build time.
    """
    add_float_param(tree, "Line Spacing", 0.13, 0.040, 0.400)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)
    return gin.outputs["Line Spacing"]


def build_music_tenuto(group_name="MEL_music_tenuto"):
    """Tenuto - ONE short thick HORIZONTAL stroke.

    The identity of a tenuto is its orientation: staccato is a disc, accent and
    marcato are vertical wedges, and the tenuto is the one articulation mark
    that is wider than it is tall. A tenuto built vertical would be a second
    marcato, so the gate asserts the aspect (Y/X well under 1) rather than the
    extents alone.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    LS = _mark_common(tree, gin, bx, by)
    add_float_param(tree, "Tenuto Length Ratio", 0.85, 0.30, 1.50)
    add_float_param(tree, "Tenuto Thickness Ratio", 0.14, 0.05, 0.30)

    length = _m(tree, "MULTIPLY", (bx - 2600, by + 160), LS,
                gin.outputs["Tenuto Length Ratio"])
    thick = _m(tree, "MULTIPLY", (bx - 2600, by), LS,
               gin.outputs["Tenuto Thickness Ratio"])

    geom = _plate(tree, (bx - 1400, by), length, thick, thick)
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1600), 11.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Horizontal Stroke", "nodes": ("Cube",), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


def build_music_caesura(group_name="MEL_music_caesura"):
    """Caesura - TWO slanted thick strokes (the `//` pause mark).

    One law at two seats: the same plate at `+/- Caesura Gap / 2`, both rotated
    by `Caesura Slant`, so the pair's closed form is
    `X = gap + thick*cos + length*sin` and `Y = thick*sin + length*cos`.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    LS = _mark_common(tree, gin, bx, by)
    add_float_param(tree, "Caesura Length Ratio", 1.15, 0.40, 2.00)
    add_float_param(tree, "Caesura Thickness Ratio", 0.16, 0.05, 0.35)
    add_float_param(tree, "Caesura Gap Ratio", 0.34, 0.10, 0.80)
    add_float_param(tree, "Caesura Slant", 28.0, 5.0, 50.0)

    length = _m(tree, "MULTIPLY", (bx - 2600, by + 160), LS,
                gin.outputs["Caesura Length Ratio"])
    thick = _m(tree, "MULTIPLY", (bx - 2600, by), LS,
               gin.outputs["Caesura Thickness Ratio"])
    gap = _m(tree, "MULTIPLY", (bx - 2600, by - 160), LS,
             gin.outputs["Caesura Gap Ratio"])
    slant = _radians(tree, (bx - 2600, by - 320),
                     gin.outputs["Caesura Slant"])
    rot = _vec(tree, (bx - 2600, by - 480), 0.0, 0.0, slant)
    half_gap = _half(tree, (bx - 2600, by - 640), gap)

    left = _plate(tree, (bx - 1400, by), thick, length, thick,
                  rotation=rot,
                  translation=_vec(tree, (bx - 1600, by),
                                   _neg(tree, (bx - 2800, by), half_gap),
                                   0.0, 0.0))
    right = _plate(tree, (bx - 1400, by - 400), thick, length, thick,
                   rotation=rot,
                   translation=_vec(tree, (bx - 1600, by - 400),
                                    half_gap, 0.0, 0.0))

    geom = _join(tree, (bx + 400, by), [left, right])
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 12.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Slanted Strokes", "nodes": ("Cube", "Transform"),
         "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# -- Registry ---------------------------------------------------------------

register_builder("MEL_music_note_thirty_second", build_music_note_thirty_second,
                 "Music Thirty-Second Note",
                 "Thirty-second note - filled head, stem and THREE flags.",
                 category="music")
register_builder("MEL_music_bar_line", build_music_bar_line,
                 "Music Bar Line",
                 "Bar line - one thin stroke spanning the staff.",
                 category="music")
register_builder("MEL_music_bar_double", build_music_bar_double,
                 "Music Double Bar Line",
                 "Double bar line - two thin strokes separated by a gap.",
                 category="music")
register_builder("MEL_music_bar_final", build_music_bar_final,
                 "Music Final Bar Line",
                 "Final bar line - a thin stroke and a thick stroke.",
                 category="music")
register_builder("MEL_music_tenuto", build_music_tenuto,
                 "Music Tenuto",
                 "Tenuto - one short thick horizontal stroke.",
                 category="music")
register_builder("MEL_music_caesura", build_music_caesura,
                 "Music Caesura",
                 "Caesura - two slanted thick strokes (//).",
                 category="music")
