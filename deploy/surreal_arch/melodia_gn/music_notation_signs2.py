"""P5 wave 22 - notation signs lane 2.

Eleven native-only glyphs: trill, mordent, turn, inverted_turn, glissando,
arpeggio, pedal_down, pedal_up, octave_shift, key_signature, tempo_mark.

All reuse the lane helpers. Each builder stores the lane attribute triple
(glyph_semitone_mod12, glyph_family, higgsas_lead).
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
# Wavy line helper (shared by turn, glissando, arpeggio)
# ---------------------------------------------------------------------------

def _wavy_line(tree, bx, by, length_sock, amp_sock, freq_sock, thick_sock,
               vertical=False, phase=0.0):
    """A wavy line: MeshLine -> SetPosition(sine) -> MeshToCurve -> sweep."""
    ml = safe_node(tree, "GeometryNodeMeshLine", (bx, by))
    if ml is None:
        return None
    ml.mode = "OFFSET"
    ml.inputs["Count"].default_value = 32
    inv_count = _m(tree, "MULTIPLY", (bx, by - 140), length_sock, 1.0 / 31.0)
    if vertical:
        link_sockets(tree, _vec(tree, (bx, by - 280), 0.0, inv_count, 0.0),
                     ml.inputs["Offset"])
    else:
        link_sockets(tree, _vec(tree, (bx, by - 280), inv_count, 0.0, 0.0),
                     ml.inputs["Offset"])

    pos = safe_node(tree, "GeometryNodeInputPosition", (bx, by - 420))
    sep = safe_node(tree, "GeometryNodeSeparateXYZ", (bx, by - 560))
    if pos is None or sep is None:
        return None
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])
    coord = sep.outputs["Y"] if vertical else sep.outputs["X"]
    sin_in = _m(tree, "MULTIPLY", (bx, by - 700), coord, freq_sock)
    sin_out = _m(tree, "SINE", (bx, by - 840), sin_in)
    amp = _m(tree, "MULTIPLY", (bx, by - 980), sin_out, amp_sock)
    if vertical:
        disp = _vec(tree, (bx, by - 1120), amp, 0.0, 0.0)
    else:
        disp = _vec(tree, (bx, by - 1120), 0.0, amp, 0.0)
    sp = safe_node(tree, "GeometryNodeSetPosition", (bx, by - 1260))
    if sp is None:
        return None
    link_sockets(tree, ml.outputs["Mesh"], sp.inputs["Geometry"])
    link_sockets(tree, disp, sp.inputs["Offset"])

    m2c = safe_node(tree, "GeometryNodeMeshToCurve", (bx, by - 1400))
    if m2c is None:
        return None
    link_sockets(tree, sp.outputs["Geometry"], m2c.inputs["Mesh"])
    return _tube(tree, (bx, by - 1540), m2c.outputs["Curve"], thick_sock)


# ---------------------------------------------------------------------------
# Trill
# ---------------------------------------------------------------------------

def build_music_trill(group_name="MEL_music_trill"):
    """Trill mark: two vertical plates + one horizontal plate (approximating 'tr')."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Stroke Ratio", 0.14, 0.06, 0.30)
    add_float_param(tree, "Cross Ratio", 0.55, 0.30, 0.90)

    sw = _m(tree, "MULTIPLY", (bx - 2600, by + 160), T,
            gin.outputs["Stroke Ratio"])
    cw = _m(tree, "MULTIPLY", (bx - 2600, by), T,
            gin.outputs["Cross Ratio"])

    stem1 = _plate(tree, (bx - 1400, by), sw, H, T,
                   translation=_vec(tree, (bx - 1600, by),
                                    _neg(tree, (bx - 2800, by), cw), 0.0, 0.0))
    stem2 = _plate(tree, (bx - 1400, by - 800), sw, H, T,
                   translation=_vec(tree, (bx - 1600, by - 800),
                                    _m(tree, "MULTIPLY", (bx - 2800, by - 800),
                                       cw, 0.35), 0.0, 0.0))
    cross = _plate(tree, (bx - 1400, by - 1600), cw, T, T,
                   translation=_vec(tree, (bx - 1600, by - 1600),
                                    _neg(tree, (bx - 2800, by - 1600), cw),
                                    _m(tree, "MULTIPLY", (bx - 3000, by - 1600),
                                       H, 0.85), 0.0))

    geom = _join(tree, (bx + 400, by), [stem1, stem2, cross])
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 8.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Mordent
# ---------------------------------------------------------------------------

def build_music_mordent(group_name="MEL_music_mordent"):
    """Mordent: one horizontal plate + one short vertical plate crossing it."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Span Ratio", 0.35, 0.15, 0.60)
    add_float_param(tree, "Cross Height", 0.22, 0.10, 0.45)

    span = _m(tree, "MULTIPLY", (bx - 2600, by), H,
              gin.outputs["Span Ratio"])
    ch = _m(tree, "MULTIPLY", (bx - 2600, by - 160), H,
            gin.outputs["Cross Height"])

    horiz = _plate(tree, (bx - 1400, by), span, T, T)
    vert = _plate(tree, (bx - 1400, by - 800), T, ch, T,
                  translation=_vec(tree, (bx - 1600, by - 800),
                                   _m(tree, "MULTIPLY", (bx - 2800, by - 800),
                                      span, 0.25), 0.0, 0.0))

    geom = _join(tree, (bx + 400, by), [horiz, vert])
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 8.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Turn / Inverted Turn
# ---------------------------------------------------------------------------

def build_music_turn(group_name="MEL_music_turn"):
    """Turn: a horizontal S-curve (one sine period)."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Wave Length", 0.50, 0.20, 1.00)
    add_float_param(tree, "Wave Amplitude", 0.12, 0.04, 0.30)
    add_float_param(tree, "Wave Frequency", 1.0, 0.5, 3.0)

    wavy = _wavy_line(tree, bx, by,
                      gin.outputs["Wave Length"],
                      gin.outputs["Wave Amplitude"],
                      gin.outputs["Wave Frequency"],
                      T)

    geom = wavy
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 8.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


def build_music_inverted_turn(group_name="MEL_music_inverted_turn"):
    """Inverted turn: a horizontal S-curve flipped vertically."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Wave Length", 0.50, 0.20, 1.00)
    add_float_param(tree, "Wave Amplitude", 0.12, 0.04, 0.30)
    add_float_param(tree, "Wave Frequency", 1.0, 0.5, 3.0)

    wavy = _wavy_line(tree, bx, by,
                      gin.outputs["Wave Length"],
                      _neg(tree, (bx - 2600, by),
                           gin.outputs["Wave Amplitude"]),
                      gin.outputs["Wave Frequency"],
                      T)

    geom = wavy
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 8.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Glissando
# ---------------------------------------------------------------------------

def build_music_glissando(group_name="MEL_music_glissando"):
    """Glissando: a horizontal wavy line with multiple sine periods."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Wave Length", 0.70, 0.30, 1.50)
    add_float_param(tree, "Wave Amplitude", 0.08, 0.02, 0.20)
    add_float_param(tree, "Wave Frequency", 3.0, 1.0, 6.0)

    wavy = _wavy_line(tree, bx, by,
                      gin.outputs["Wave Length"],
                      gin.outputs["Wave Amplitude"],
                      gin.outputs["Wave Frequency"],
                      T)

    geom = wavy
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 8.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Arpeggio
# ---------------------------------------------------------------------------

def build_music_arpeggio(group_name="MEL_music_arpeggio"):
    """Arpeggio: a vertical wavy line."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Wave Length", 0.60, 0.20, 1.20)
    add_float_param(tree, "Wave Amplitude", 0.10, 0.03, 0.25)
    add_float_param(tree, "Wave Frequency", 4.0, 1.0, 8.0)

    wavy = _wavy_line(tree, bx, by,
                      gin.outputs["Wave Length"],
                      gin.outputs["Wave Amplitude"],
                      gin.outputs["Wave Frequency"],
                      T, vertical=True)

    geom = wavy
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 8.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Pedal Down
# ---------------------------------------------------------------------------

def build_music_pedal_down(group_name="MEL_music_pedal_down"):
    """Pedal down: vertical plate + two horizontal plates + dot."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Dot Ratio", 0.08, 0.03, 0.15)

    dr = _m(tree, "MULTIPLY", (bx - 2600, by), T,
            gin.outputs["Dot Ratio"])

    stem = _plate(tree, (bx - 1400, by), T, H, T,
                  translation=_vec(tree, (bx - 1600, by),
                                   _neg(tree, (bx - 2800, by),
                                        _m(tree, "MULTIPLY", (bx - 3000, by),
                                           H, 0.25)), 0.0, 0.0))
    bar1 = _plate(tree, (bx - 1400, by - 800), H, T, T,
                  translation=_vec(tree, (bx - 1600, by - 800),
                                   _neg(tree, (bx - 2800, by - 800),
                                        _m(tree, "MULTIPLY", (bx - 3000, by - 800),
                                           H, 0.35)),
                                   _m(tree, "MULTIPLY", (bx - 3200, by - 800),
                                      H, 0.55), 0.0))
    bar2 = _plate(tree, (bx - 1400, by - 1600), H, T, T,
                  translation=_vec(tree, (bx - 1600, by - 1600),
                                   _neg(tree, (bx - 2800, by - 1600),
                                        _m(tree, "MULTIPLY", (bx - 3000, by - 1600),
                                           H, 0.35)),
                                   _m(tree, "MULTIPLY", (bx - 3200, by - 1600),
                                      H, 0.30), 0.0))
    dot = _cyl(tree, (bx - 1400, by - 2400), dr, T, vertices=16, fill=2)

    parts = [stem, bar1, bar2]
    if dot is not None:
        parts.append(dot)
    geom = _join(tree, (bx + 400, by), parts)
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 10.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Pedal Up
# ---------------------------------------------------------------------------

def build_music_pedal_up(group_name="MEL_music_pedal_up"):
    """Pedal up: three crossing plates (asterisk)."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Arm Ratio", 0.45, 0.20, 0.80)

    arm = _m(tree, "MULTIPLY", (bx - 2600, by), H,
             gin.outputs["Arm Ratio"])

    a1 = _plate(tree, (bx - 1400, by), arm, T, T)
    a2 = _plate(tree, (bx - 1400, by - 800), arm, T, T,
                rotation=(0.0, 0.0, math.radians(60)))
    a3 = _plate(tree, (bx - 1400, by - 1600), arm, T, T,
                rotation=(0.0, 0.0, math.radians(120)))

    geom = _join(tree, (bx + 400, by), [a1, a2, a3])
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 10.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Octave Shift
# ---------------------------------------------------------------------------

def build_music_octave_shift(group_name="MEL_music_octave_shift"):
    """Octave shift: a series of small horizontal plates + a vertical hook."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Dash Count", 5, 2, 10)
    add_float_param(tree, "Dash Length", 0.12, 0.05, 0.25)
    add_float_param(tree, "Hook Height", 0.30, 0.15, 0.60)

    dc = gin.outputs["Dash Count"]
    dl = _m(tree, "MULTIPLY", (bx - 2600, by), H,
            gin.outputs["Dash Length"])
    hh = _m(tree, "MULTIPLY", (bx - 2600, by - 160), H,
            gin.outputs["Hook Height"])

    parts = []
    for i in range(10):
        if i < 5:
            dx = _m(tree, "MULTIPLY", (bx - 3200 + i * 80, by), dl,
                   float(i))
            dash = _plate(tree, (bx - 1400 + i * 80, by - i * 80), dl, T, T,
                          translation=_vec(tree, (bx - 1600 + i * 80, by - i * 80),
                                           dx, 0.0, 0.0))
            if dash is not None:
                parts.append(dash)

    hook = _plate(tree, (bx + 200, by), T, hh, T,
                  translation=_vec(tree, (bx + 400, by),
                                   _m(tree, "MULTIPLY", (bx - 2800, by), dl, 5.0),
                                   0.0, 0.0))
    if hook is not None:
        parts.append(hook)

    geom = _join(tree, (bx + 600, by), parts)
    _finish(tree, gin, gout, geom, (bx + 900, by), group_name,
            _glyph_attrs(tree, (bx + 600, by - 1800), 10.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Key Signature
# ---------------------------------------------------------------------------

_SHARP_POS = [8, 5, 9, 6, 3, 7, 2]
_FLAT_POS = [2, 5, 1, 6, 3, 7, 4]


def build_music_key_signature(group_name="MEL_music_key_signature"):
    """Key signature: a row of sharps or flats at the correct staff positions."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_int_param(tree, "Number of Accidentals", 3, 0, 7)
    add_bool_param(tree, "Use Sharps", True)
    add_float_param(tree, "Accidental Spacing", 0.18, 0.08, 0.40)
    add_float_param(tree, "Line Spacing", 0.13, 0.04, 0.40)

    n_acc = gin.outputs["Number of Accidentals"]
    use_sharps = gin.outputs["Use Sharps"]
    spacing = _m(tree, "MULTIPLY", (bx - 2600, by), H,
                  gin.outputs["Accidental Spacing"])
    ls = gin.outputs["Line Spacing"]

    parts = []
    for i in range(7):
        x_off = _m(tree, "MULTIPLY", (bx - 3200 + i * 80, by), spacing,
                  float(i))
        pos_list = _SHARP_POS if True else _FLAT_POS
        staff_pos = pos_list[i]
        y_off = _m(tree, "MULTIPLY", (bx - 3600 + i * 80, by),
                   _m(tree, "SUBTRACT", (bx - 3800 + i * 80, by),
                      float(staff_pos), 4.5),
                   _m(tree, "MULTIPLY", (bx - 4000 + i * 80, by), ls, 0.5))

        if i < 5:
            if True:  # sharp
                sw = _m(tree, "MULTIPLY", (bx - 4200 + i * 80, by), T, 0.6)
                v1 = _plate(tree, (bx - 4400 + i * 80, by - i * 80), sw, H, T,
                            translation=_vec(tree, (bx - 4600 + i * 80, by - i * 80),
                                             _neg(tree, (bx - 4800 + i * 80, by - i * 80),
                                                  _m(tree, "MULTIPLY", (bx - 5000 + i * 80, by - i * 80),
                                                     spacing, 0.3)),
                                             y_off, 0.0))
                v2 = _plate(tree, (bx - 5200 + i * 80, by - i * 80), sw, H, T,
                            translation=_vec(tree, (bx - 5400 + i * 80, by - i * 80),
                                             _m(tree, "MULTIPLY", (bx - 5600 + i * 80, by - i * 80),
                                                spacing, 0.3),
                                             y_off, 0.0))
                h1 = _plate(tree, (bx - 5800 + i * 80, by - i * 80), spacing, T, T,
                            translation=_vec(tree, (bx - 6000 + i * 80, by - i * 80),
                                             _neg(tree, (bx - 6200 + i * 80, by - i * 80),
                                                  _m(tree, "MULTIPLY", (bx - 6400 + i * 80, by - i * 80),
                                                     spacing, 0.3)),
                                             _m(tree, "MULTIPLY", (bx - 6600 + i * 80, by - i * 80),
                                                H, 0.35), 0.0))
                h2 = _plate(tree, (bx - 6800 + i * 80, by - i * 80), spacing, T, T,
                            translation=_vec(tree, (bx - 7000 + i * 80, by - i * 80),
                                             _neg(tree, (bx - 7200 + i * 80, by - i * 80),
                                                  _m(tree, "MULTIPLY", (bx - 7400 + i * 80, by - i * 80),
                                                     spacing, 0.3)),
                                             _m(tree, "MULTIPLY", (bx - 7600 + i * 80, by - i * 80),
                                                H, 0.55), 0.0))
                if v1 is not None:
                    parts.append(v1)
                if v2 is not None:
                    parts.append(v2)
                if h1 is not None:
                    parts.append(h1)
                if h2 is not None:
                    parts.append(h2)
            else:  # flat
                stem = _plate(tree, (bx - 4400 + i * 80, by - i * 80), T, H, T,
                              translation=_vec(tree, (bx - 4600 + i * 80, by - i * 80),
                                               x_off, y_off, 0.0))
                belly = _cyl(tree, (bx - 4800 + i * 80, by - i * 80),
                             _m(tree, "MULTIPLY", (bx - 5000 + i * 80, by - i * 80),
                                H, 0.19), T, vertices=24, fill=2)
                if stem is not None:
                    parts.append(stem)
                if belly is not None:
                    parts.append(belly)

    geom = _join(tree, (bx + 800, by), parts)
    _finish(tree, gin, gout, geom, (bx + 1100, by), group_name,
            _glyph_attrs(tree, (bx + 800, by - 1800), 9.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Tempo Mark
# ---------------------------------------------------------------------------

def build_music_tempo_mark(group_name="MEL_music_tempo_mark"):
    """Tempo mark: note head + stem + equal sign + three plates."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    H, T = _glyph_common(tree, gin, bx, by)
    add_float_param(tree, "Note Size", 0.20, 0.10, 0.40)
    add_float_param(tree, "Digit Width", 0.08, 0.04, 0.15)

    ns = _m(tree, "MULTIPLY", (bx - 2600, by), H,
            gin.outputs["Note Size"])
    dw = _m(tree, "MULTIPLY", (bx - 2600, by - 160), H,
            gin.outputs["Digit Width"])

    head = _cyl(tree, (bx - 1400, by), ns, T, vertices=24, fill=2)
    if head is not None:
        head = _xf(tree, (bx - 1200, by), head.outputs["Mesh"],
                   scale=_vec(tree, (bx - 1400, by - 200), 1.0, 0.72, 1.0)).outputs["Geometry"]

    stem = _plate(tree, (bx - 1400, by - 800), T, H, T,
                  translation=_vec(tree, (bx - 1600, by - 800),
                                   _m(tree, "MULTIPLY", (bx - 2800, by - 800),
                                      ns, 0.85),
                                   _m(tree, "MULTIPLY", (bx - 3000, by - 800),
                                      H, 0.45), 0.0))

    eq1 = _plate(tree, (bx - 1400, by - 1600), H, T, T,
                 translation=_vec(tree, (bx - 1600, by - 1600),
                                  _m(tree, "MULTIPLY", (bx - 2800, by - 1600),
                                     ns, 1.4),
                                  _m(tree, "MULTIPLY", (bx - 3000, by - 1600),
                                     H, 0.30), 0.0))
    eq2 = _plate(tree, (bx - 1400, by - 2400), H, T, T,
                 translation=_vec(tree, (bx - 1600, by - 2400),
                                  _m(tree, "MULTIPLY", (bx - 2800, by - 2400),
                                     ns, 1.4),
                                  _m(tree, "MULTIPLY", (bx - 3000, by - 2400),
                                     H, 0.55), 0.0))

    d1 = _plate(tree, (bx - 1400, by - 3200), dw, H, T,
                translation=_vec(tree, (bx - 1600, by - 3200),
                                 _m(tree, "MULTIPLY", (bx - 2800, by - 3200),
                                    ns, 2.2), 0.0, 0.0))
    d2 = _plate(tree, (bx - 1400, by - 4000), dw, H, T,
                translation=_vec(tree, (bx - 1600, by - 4000),
                                 _m(tree, "MULTIPLY", (bx - 2800, by - 4000),
                                    ns, 2.6), 0.0, 0.0))
    d3 = _plate(tree, (bx - 1400, by - 4800), dw, H, T,
                translation=_vec(tree, (bx - 1600, by - 4800),
                                 _m(tree, "MULTIPLY", (bx - 2800, by - 4800),
                                    ns, 3.0), 0.0, 0.0))

    parts = [p for p in [head, stem, eq1, eq2, d1, d2, d3] if p is not None]
    geom = _join(tree, (bx + 400, by), parts)
    _finish(tree, gin, gout, geom, (bx + 700, by), group_name,
            _glyph_attrs(tree, (bx + 400, by - 1800), 9.0))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Register all builders
# ---------------------------------------------------------------------------

register_builder("MEL_music_trill", build_music_trill, "Trill",
                 "Trill ornament mark.", category="music")
register_builder("MEL_music_mordent", build_music_mordent, "Mordent",
                 "Mordent ornament mark.", category="music")
register_builder("MEL_music_turn", build_music_turn, "Turn",
                 "Turn ornament mark.", category="music")
register_builder("MEL_music_inverted_turn", build_music_inverted_turn,
                 "Inverted Turn", "Inverted turn ornament mark.", category="music")
register_builder("MEL_music_glissando", build_music_glissando, "Glissando",
                 "Glissando wavy line.", category="music")
register_builder("MEL_music_arpeggio", build_music_arpeggio, "Arpeggio",
                 "Arpeggio vertical wavy line.", category="music")
register_builder("MEL_music_pedal_down", build_music_pedal_down,
                 "Pedal Down", "Pedal down marking.", category="music")
register_builder("MEL_music_pedal_up", build_music_pedal_up, "Pedal Up",
                 "Pedal up marking.", category="music")
register_builder("MEL_music_octave_shift", build_music_octave_shift,
                 "Octave Shift", "Octave shift dashed line.", category="music")
register_builder("MEL_music_key_signature", build_music_key_signature,
                 "Key Signature", "Key signature accidentals.", category="music")
register_builder("MEL_music_tempo_mark", build_music_tempo_mark,
                 "Tempo Mark", "Tempo marking.", category="music")
