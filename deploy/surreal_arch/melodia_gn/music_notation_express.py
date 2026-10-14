"""P5 wave 23 - notation expression & bowing marks lane.

Six native-only glyphs:

    MEL_music_tie         shallow arc, the tie between two like notes
    MEL_music_slur        the SAME arc law, deeper - a slur over unlike notes
    MEL_music_grace_note  small filled head + stem + slash (acciaccatura)
    MEL_music_tremolo     stem crossed by three diagonal slashes
    MEL_music_up_bow      U mark: two verticals + a bar at the BOTTOM
    MEL_music_down_bow    the SAME parts mirrored: bar at the TOP

Design rules (same as music_notation_glyphs / music_note_durations /
music_notation_extras / music_notation_marks / music_notation_signs2):

  - Native-only. Every builder stores `higgsas_lead` (1.0 = native) plus
    `glyph_semitone_mod12` and `glyph_family`, so the family gate reads the
    lane uniformly.
  - The shared helpers are REUSED, never re-authored: `_neg` / `_half` /
    `_radians` / `_tube` / `_arc_xy` / `_glyph_attrs` / `_glyph_common`
    (music_notation_glyphs), `_m` / `_plate` (music_keyboard_kit - `_plate`
    links all three `Size` components), `_xf` (music_higgsas_instruments),
    `_join` / `_vec` (music_wind_reed_brass), and `_finish` (music_string_kit -
    applies Scale BEFORE the export tail, which the shared `_export_tail` does
    not, so the Scale dial is live rather than dead).
  - Zero `MeshBoolean` in the lane: a cutter that touches the mesh's own
    boundary emits ZERO geometry with no error and no `link_failures` entry.
    Every stroke here is laid on, not cut.
  - A literal rotation tuple lands in a socket's `default_value`, never in a
    link, so every tilt here is a linked CombineXYZ fed by a group input - a
    gate can then prove the tilt is real rather than reading an absent link as
    "no tilt".
  - **A Python operator on a NodeSocket is a build-time TypeError** (`T * 1.5`,
    `sep + T`), so every dimension in this lane goes through `_scaled` / `_m`.
  - **The bow pair is a MIRROR, and a mirror is the one property extents
    cannot see.** A box rotated by `ang` and by `ang + 180` is the SAME box, so
    the two marks are built as one law at two seats: the SAME three parts, with
    the cross bar's Y seat flipped. The gate therefore asserts the MOUTH SIDE
    (which end is open), not the bbox.
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
from .music_notation_glyphs import (
    _neg, _half, _radians, _tube, _arc_xy, _glyph_attrs, _glyph_common,
)


# ---------------------------------------------------------------------------
# Lane-local laws
# ---------------------------------------------------------------------------

def _scaled(tree, loc, base_sock, factor):
    """`base_sock * factor` through a MULTIPLY node.

    A Python `*` on a NodeSocket is a build-time TypeError and kills the whole
    builder, so every dimension in this lane is a node.
    """
    return _m(tree, "MULTIPLY", loc, base_sock, float(factor))


def _arc_glyph(group_name, start_deg, sweep_deg, depth_default, family_value):
    """One arc law at two depths - the tie and the slur.

    `Depth Ratio` scales the arc radius off `Glyph Height`; the tie is the
    shallow reading and the slur the deep one, and the two differ ONLY in that
    ratio and the sweep, so the gate can assert the relationship rather than a
    snapshot. The arc lies in the glyph's own XY plane (probed 2026-10-05:
    `CurveArc` RADIUS mode, angle 0 at +X, CCW sweep), so the swept stroke
    straddles z = 0 and the lane's symmetry law is `|min_z| == |max_z|`.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Depth Ratio", depth_default, 0.20, 1.60)

    r = _m(tree, "MULTIPLY", (bx - 2600, by), H,
           gin.outputs["Depth Ratio"])
    stroke = _scaled(tree, (bx - 2600, by - 160), T, 0.80)

    arc = _arc_xy(tree, (bx - 1400, by), r, start_deg, sweep_deg)
    geom = None
    if arc is not None:
        geom = _tube(tree, (bx - 1000, by), arc.outputs["Curve"], stroke)

    if geom is not None:
        _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
                _glyph_attrs(tree, (bx + 400, by - 1800), family_value))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Arc", "nodes": ("Arc", "Curve to Mesh"), "role": "curve"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


def build_music_tie(group_name="MEL_music_tie"):
    """Tie - a SHALLOW arc joining two notes of the same pitch."""
    return _arc_glyph(group_name, 200.0, 140.0, 0.42, 13.0)


def build_music_slur(group_name="MEL_music_slur"):
    """Slur - the SAME arc law, deeper: a semicircle over unlike notes."""
    return _arc_glyph(group_name, 180.0, 180.0, 0.62, 13.0)


# ---------------------------------------------------------------------------
# MEL_music_grace_note
# ---------------------------------------------------------------------------

def build_music_grace_note(group_name="MEL_music_grace_note"):
    """Grace note (acciaccatura) - a small filled head, a stem, and a slash.

    Three parts, and the slash is the identifying one: it is a plate TILTED
    about Z by `Slash Angle`, wired from a group input so the tilt is a real
    link a gate can walk (a literal tuple would hide in `default_value`).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Note Size", 0.20, 0.10, 0.40)
    add_float_param(tree, "Stem Length", 0.42, 0.20, 0.80)
    add_float_param(tree, "Slash Angle", 30.0, 10.0, 60.0)

    ns = _m(tree, "MULTIPLY", (bx - 2600, by), H, gin.outputs["Note Size"])
    sl = _m(tree, "MULTIPLY", (bx - 2600, by - 160), H,
            gin.outputs["Stem Length"])
    ang = _radians(tree, (bx - 2600, by - 320), gin.outputs["Slash Angle"])

    # head: a filled cylinder scaled to an ellipse
    head = _cyl(tree, (bx - 1400, by), ns, T, vertices=24, fill=2)
    if head is not None:
        head = _xf(tree, (bx - 1200, by), head.outputs["Mesh"],
                   scale=_vec(tree, (bx - 1400, by - 200), 1.0, 0.72, 1.0)
                   ).outputs["Geometry"]

    # stem: vertical plate, its X seat at the tilted head's right extremity
    stem_x = _scaled(tree, (bx - 2800, by - 800), ns, 0.86)
    stem_y = _scaled(tree, (bx - 3000, by - 800), sl, 0.50)
    stem = _plate(tree, (bx - 1400, by - 800), T, sl, T,
                  translation=_vec(tree, (bx - 1600, by - 800),
                                   stem_x, stem_y, 0.0))

    # slash: a thin plate crossing the stem, tilted about Z
    slash = _plate(tree, (bx - 1400, by - 1600), T, sl, T,
                   translation=_vec(tree, (bx - 1600, by - 1600),
                                    stem_x, stem_y, 0.0),
                   rotation=_vec(tree, (bx - 1600, by - 1800), 0.0, 0.0, ang))

    parts = [p for p in (head, stem, slash) if p is not None]
    geom = _join(tree, (bx + 400, by), parts)
    if geom is not None:
        _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
                _glyph_attrs(tree, (bx + 400, by - 1800), 14.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Head + Stem + Slash",
         "nodes": ("Cylinder", "Cube", "Join Geometry"), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_tremolo
# ---------------------------------------------------------------------------

def build_music_tremolo(group_name="MEL_music_tremolo"):
    """Tremolo - a stem crossed by THREE diagonal slashes (the standard count).

    Four parts in all: one stem plus three slashes at 25 / 50 / 75 per cent of
    the stem, each tilted about Z by `Slash Angle`. The count is fixed at the
    notational standard of three rather than exposed as a dial, so no parameter
    in this builder is dead.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Stem Length", 0.60, 0.30, 1.00)
    add_float_param(tree, "Slash Angle", 30.0, 10.0, 60.0)

    sl = _m(tree, "MULTIPLY", (bx - 2600, by), H,
            gin.outputs["Stem Length"])
    ang = _radians(tree, (bx - 2600, by - 160), gin.outputs["Slash Angle"])

    # the stem: a vertical plate centred on the origin
    stem = _plate(tree, (bx - 1400, by), T, sl, T)

    # three slashes at 25 / 50 / 75 per cent up the stem
    parts = [stem]
    for i, frac in enumerate((0.25, 0.50, 0.75)):
        seat = _scaled(tree, (bx - 2800, by - 800 - i * 800), sl, frac)
        slash = _plate(tree, (bx - 1400, by - 800 - i * 800), T, sl, T,
                       translation=_vec(tree, (bx - 1600, by - 800 - i * 800),
                                        0.0, seat, 0.0),
                       rotation=_vec(tree, (bx - 1600, by - 1000 - i * 800),
                                     0.0, 0.0, ang))
        parts.append(slash)

    geom = _join(tree, (bx + 400, by), parts)
    if geom is not None:
        _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
                _glyph_attrs(tree, (bx + 400, by - 1800), 14.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Stem + 3 Slashes",
         "nodes": ("Cube", "Join Geometry"), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_up_bow / MEL_music_down_bow - one law, two seats (a MIRROR)
# ---------------------------------------------------------------------------

def _bow_mark(group_name, mouth_up, family_value):
    """One bow-mark law at two seats: two verticals plus one cross bar.

    `mouth_up` True puts the bar at the BOTTOM (an up-bow: the mark's opening
    faces up) and False at the TOP (a down-bow: the opening faces down). The
    parts are identical and the extents are identical - a mirror is the one
    property a bbox cannot see - so the seat is the whole difference and it is
    a single linked chain off `Arm Length`, which is what the gate walks.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Arm Length", 0.34, 0.15, 0.70)
    add_float_param(tree, "Arm Separation", 0.26, 0.10, 0.55)

    al = _m(tree, "MULTIPLY", (bx - 2600, by), H,
            gin.outputs["Arm Length"])
    sep = _m(tree, "MULTIPLY", (bx - 2600, by - 160), H,
             gin.outputs["Arm Separation"])
    half_sep = _half(tree, (bx - 2600, by - 320), sep)
    half_al = _half(tree, (bx - 2600, by - 480), al)

    # the two verticals: centred on the origin, separated along X
    left = _plate(tree, (bx - 1400, by), T, al, T,
                  translation=_vec(tree, (bx - 1600, by),
                                   _neg(tree, (bx - 2800, by), half_sep),
                                   0.0, 0.0))
    right = _plate(tree, (bx - 1400, by - 800), T, al, T,
                   translation=_vec(tree, (bx - 1600, by - 800),
                                    half_sep, 0.0, 0.0))

    # the cross bar: at the BOTTOM for an up-bow, at the TOP for a down-bow
    if mouth_up:
        bar_y = _neg(tree, (bx - 2800, by - 1600), half_al)
    else:
        bar_y = half_al
    bar_w = _m(tree, "ADD", (bx - 2800, by - 1760), sep, T)
    bar = _plate(tree, (bx - 1400, by - 1600), bar_w, T, T,
                 translation=_vec(tree, (bx - 1600, by - 1600), 0.0, bar_y, 0.0))

    parts = [p for p in (left, right, bar) if p is not None]
    geom = _join(tree, (bx + 400, by), parts)
    if geom is not None:
        _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
                _glyph_attrs(tree, (bx + 400, by - 1800), family_value))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Two Arms + Bar",
         "nodes": ("Cube", "Join Geometry"), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


def build_music_up_bow(group_name="MEL_music_up_bow"):
    """Up-bow - two verticals joined by a bar at the BOTTOM (opening faces up)."""
    return _bow_mark(group_name, True, 15.0)


def build_music_down_bow(group_name="MEL_music_down_bow"):
    """Down-bow - the SAME parts mirrored: the bar sits at the TOP."""
    return _bow_mark(group_name, False, 15.0)


# ---------------------------------------------------------------------------
# Register all builders
# ---------------------------------------------------------------------------

register_builder("MEL_music_tie", build_music_tie, "Tie",
                 "Tie expression mark.", category="music")
register_builder("MEL_music_slur", build_music_slur, "Slur",
                 "Slur expression mark.", category="music")
register_builder("MEL_music_grace_note", build_music_grace_note, "Grace Note",
                 "Grace note (acciaccatura).", category="music")
register_builder("MEL_music_tremolo", build_music_tremolo, "Tremolo",
                 "Tremolo marking.", category="music")
register_builder("MEL_music_up_bow", build_music_up_bow, "Up Bow",
                 "Up-bow marking.", category="music")
register_builder("MEL_music_down_bow", build_music_down_bow, "Down Bow",
                 "Down-bow marking.", category="music")
