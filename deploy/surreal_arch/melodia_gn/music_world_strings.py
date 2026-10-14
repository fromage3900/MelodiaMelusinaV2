"""P4 wave 5 — world/folk string lane: sitar, koto, balalaika, shamisen, erhu,
guzheng.

Gap audit first (repo-wide grep over `deploy/surreal_arch/` + the live registry,
2026-10-03): the string lane owns the five `MEL_harp_*` ids, the baroque
violin/lute/harpsichord trio, dulcimer, kalimba, lissajous harp, violin bow, and
the wave-4 bowed/plucked set (cello, viola, double bass, banjo, mandolin,
ukulele). NONE of the six ids below existed anywhere (grep count 0 each):

    sitar, koto, balalaika, shamisen, erhu, guzheng

Nothing here re-implements an existing id. The wave-4 `_string_rank` / `_neck` /
`_finish` helpers and the shared `MEL_harp_string_unit` proto are REUSED, not
re-authored — a second private rank helper is the defect wave 4 exists to avoid.

Design rules (same as music_string_kit / music_percussion_kit):
  - Native-only. These are box, drum, gourd and prism bodies that 5.2
    primitives express exactly; a Higgsas subtree here would be decoration, not
    a lead. Every builder still stores `higgsas_lead` (1.0 = native) so the
    family gate and the instruments gate read the lane uniformly.
  - ONE body law per family, SIZED per instrument, never copied numbers:
    `_zither_body` (long board + end rails) serves koto and guzheng;
    `_prism_body` (n-vertex cylinder = an n-sided body) serves shamisen (4),
    erhu (6) and the balalaika's triangular cone prism.
  - String ranks come from the shared `MEL_harp_string_unit` proto, each builder
    linking its OWN length into the proto node's group input.
  - Line offsets are always CombineXYZ (a bare float broadcasts to (v, v, v)).
  - A field value never feeds a PRIMITIVE dimension (the collapse class): every
    primitive dimension here is a socket-driven CombineXYZ component with all
    three components written.
  - Orientation convention of this lane: the soundboard lies in XY and the
    strings stand along +Z above it (the instrument "on the bench" pose, the
    same pose wave 4's bowed bodies use).

Builders:
    MEL_music_sitar        gourd resonator + tabli + long neck + frets + 7/12 strings
    MEL_music_koto         paulownia board + 2 end rails + 13 strings + 13 ji
    MEL_music_balalaika    triangular prism body + soundhole + fretted neck + 3 strings
    MEL_music_shamisen     square dou + skins + 3-section sao + 3 strings + bachi
    MEL_music_erhu         hexagonal soundbox + python skin + qin gan + 2 strings + bow
    MEL_music_guzheng      arched board + 21 strings + 21 zhen ma bridges + end pieces
"""

from __future__ import annotations

import math

from .core import (
    safe_node, link_sockets, label_tree, new_geometry_tree, add_float_param,
    add_int_param, add_bool_param, register_builder, sock, mesh_boolean_node,
)
from .music_harps_real import _math, _combine, _ensure_string_proto
from .music_higgsas_instruments import (
    _store_named, _cone, _cyl, _line, _xf, _set_fill,
)
from .music_string_kit import _string_rank, _neck, _finish
from .music_percussion_kit import _inst_rank


# ---------------------------------------------------------------------------
# Shared laws — authored once, sized per instrument
# ---------------------------------------------------------------------------


def _rank_points_x(tree, loc, count_sock, step_sock):
    """A rank of points stepped along +X. Offset is CombineXYZ by construction."""
    bx, by = loc
    line, line_sock = _line(
        tree, (bx, by), count_sock=count_sock,
        offset=_combine(tree, (bx - 200, by - 140), step_sock, 0.0, 0.0))
    if line is None:
        return None
    pts = safe_node(tree, "GeometryNodeMeshToPoints", (bx + 200, by))
    if pts is None:
        return None
    link_sockets(tree, line_sock, sock(pts, "Mesh") or pts.inputs[0])
    return pts.outputs["Points"]


def _rank_points_y(tree, loc, count_sock, step_sock):
    """A rank of points stepped along +Y (the across-the-board axis)."""
    bx, by = loc
    line, line_sock = _line(
        tree, (bx, by), count_sock=count_sock,
        offset=_combine(tree, (bx - 200, by - 140), 0.0, step_sock, 0.0))
    if line is None:
        return None
    pts = safe_node(tree, "GeometryNodeMeshToPoints", (bx + 200, by))
    if pts is None:
        return None
    link_sockets(tree, line_sock, sock(pts, "Mesh") or pts.inputs[0])
    return pts.outputs["Points"]


def _lay_strings(tree, loc, inst, length_sock, low_x_sock, z_sock):
    """Lay a rank of Z-standing string protos FLAT along +X over the board.

    The shared `MEL_harp_string_unit` proto is a cylinder along **+Z** centred at
    its own origin, so a rank left unrotated stands straight UP out of the
    soundboard (measured in the wave-5 first shots: the strings hung off the
    instrument's side). The rank is therefore rotated +90 deg about Y (Z -> X)
    and its origin placed at the string CENTRE, `low_x + length/2`.

    The rank must be built at **x = 0** (`x_sock=None`): the rotation is applied
    about the transform's own origin, so any non-zero `Start Location` on the
    MeshLine leaks straight into Z after the rotation. Measured on the first
    wave-5 pass: a rank with `Start Location = neck_x = 0.61` came out at
    z = -0.436 = -0.61 + z_sock exactly. `low_x_sock` does all the X placement.
    """
    bx, by = loc
    if inst is None:
        return None
    half = _math(tree, "MULTIPLY", (bx - 200, by + 140), length_sock, 0.5)
    cx = _math(tree, "ADD", (bx - 200, by - 140), low_x_sock, half.outputs[0])
    return _xf(tree, (bx, by), inst,
               rotation=(0.0, math.radians(90.0), 0.0),
               translation=_combine(tree, (bx - 200, by - 280),
                                   cx.outputs[0], 0.0, z_sock)
               ).outputs["Geometry"]


def _prism_body(tree, loc, sides, radius_sock, depth_sock, spin=0.0, fill=2):
    """An n-sided body: an n-vertex cylinder (4 = square dou, 6 = erhu box).

    `spin` rotates the cross-section so a 4-sided body lands axis-aligned.
    """
    bx, by = loc
    n = _cyl(tree, (bx, by), radius_sock, depth_sock, vertices=sides, fill=fill)
    if n is None:
        return None, None
    if not spin:
        return n.outputs["Mesh"], n
    return _xf(tree, (bx + 200, by), n.outputs["Mesh"],
               rotation=(0.0, 0.0, spin)).outputs["Geometry"], n


def _zither_body(tree, loc, length_sock, width_sock, depth_sock,
                 rail_frac=0.055, vertices=4):
    """A long flat soundboard with an end rail at each end. Koto + guzheng law.

    The board is a box (length x width x depth) laid along X. The rails are two
    shallow bars at the ends, sized from the same width socket, so a longer or
    wider board carries proportionally longer rails instead of fixed numbers.
    """
    bx, by = loc
    board = safe_node(tree, "GeometryNodeMeshCube", (bx, by))
    if board is None:
        return None
    link_sockets(tree, _combine(tree, (bx - 200, by - 140),
                                length_sock, width_sock, depth_sock).outputs["Vector"],
                 board.inputs["Size"])
    parts = [board.outputs["Mesh"]]
    rail_len = _math(tree, "MULTIPLY", (bx - 200, by - 400),
                     length_sock, rail_frac)
    rail = safe_node(tree, "GeometryNodeMeshCube", (bx - 100, by - 600))
    rail_h = _math(tree, "MULTIPLY", (bx - 300, by - 600), depth_sock, 2.4)
    link_sockets(tree, _combine(tree, (bx - 300, by - 740),
                                rail_len.outputs[0], width_sock, rail_h.outputs[0]
                                ).outputs["Vector"],
                 rail.inputs["Size"])
    for sx in (-1.0, 1.0):
        parts.append(_xf(
            tree, (bx + 200, by - 600 + int(sx) * 200), rail.outputs["Mesh"],
            translation=_combine(
                tree, (bx, by - 740 + int(sx) * 200),
                _math(tree, "MULTIPLY", (bx - 200, by - 740 + int(sx) * 200),
                      _math(tree, "MULTIPLY",
                            (bx - 400, by - 740 + int(sx) * 200),
                            _math(tree, "SUBTRACT",
                                  (bx - 600, by - 740 + int(sx) * 200),
                                  0.5, rail_frac).outputs[0],
                            sx).outputs[0],
                      length_sock).outputs[0],
                0.0, 0.0)).outputs["Geometry"])
    return parts


# ---------------------------------------------------------------------------
# MEL_music_sitar
# ---------------------------------------------------------------------------

def build_music_sitar(group_name="MEL_music_sitar"):
    """Sitar: gourd resonator, tabli soundboard, long neck, frets, 7 + taraf strings."""
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_sitar"
    bx, by = 0, 0

    add_float_param(tree, "Body Diameter M", 0.36, 0.18, 0.6)
    add_float_param(tree, "Body Depth M", 0.30, 0.12, 0.5)
    add_float_param(tree, "Neck Length M", 0.86, 0.4, 1.4)
    add_int_param(tree, "String Count", 7, 4, 9)
    add_int_param(tree, "Sympathetic Count", 12, 0, 22)
    add_int_param(tree, "Fret Count", 20, 8, 26)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    R = _math(tree, "MULTIPLY", (bx - 1700, by + 260),
              gin.outputs["Body Diameter M"], 0.5)

    # gourd resonator: a sphere squashed along Z into a pumpkin
    gourd = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 1500, by + 200))
    gourd.inputs["Segments"].default_value = 48
    gourd.inputs["Rings"].default_value = 24
    link_sockets(tree, R.outputs[0], sock(gourd, "Radius"))
    gsc = _combine(tree, (bx - 1700, by + 120), 1.0, 1.0,
                   _math(tree, "DIVIDE", (bx - 1900, by + 120),
                         gin.outputs["Body Depth M"],
                         gin.outputs["Body Diameter M"]).outputs[0])
    gourd_geo = _xf(tree, (bx - 1300, by + 200), gourd.outputs["Mesh"],
                    scale=gsc).outputs["Geometry"]

    # tabli: the soundboard disc on the gourd's top face
    tabli = _cyl(tree, (bx - 1300, by - 100),
                 _math(tree, "MULTIPLY", (bx - 1500, by - 100), R.outputs[0], 0.92).outputs[0],
                 _math(tree, "MULTIPLY", (bx - 1500, by - 240),
                       gin.outputs["Body Depth M"], 0.06).outputs[0], vertices=48)
    tabli_geo = _xf(tree, (bx - 1100, by - 100), tabli.outputs["Mesh"],
                    translation=_combine(tree, (bx - 1300, by - 240), 0.0, 0.0,
                                        _math(tree, "MULTIPLY",
                                              (bx - 1500, by - 240),
                                              gin.outputs["Body Depth M"],
                                              0.53).outputs[0])).outputs["Geometry"]

    # second (smaller) gourd behind the main one
    kaddu = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 1500, by - 400))
    kaddu.inputs["Segments"].default_value = 32
    kaddu.inputs["Rings"].default_value = 16
    link_sockets(tree, _math(tree, "MULTIPLY", (bx - 1700, by - 400),
                             R.outputs[0], 0.52).outputs[0],
                 sock(kaddu, "Radius"))
    kaddu_geo = _xf(tree, (bx - 1300, by - 400), kaddu.outputs["Mesh"],
                    translation=_combine(tree, (bx - 1500, by - 540),
                                        _math(tree, "MULTIPLY",
                                              (bx - 1700, by - 540),
                                              R.outputs[0], -0.92).outputs[0],
                                        0.0, 0.0)).outputs["Geometry"]

    # neck: a tapered bar out of the gourd, plus the pegbox at its end. Both sit
    # at the TOP of the gourd (z = the tabli plane), not on the ground: a neck at
    # z=0 with the body centred at z=0 reads as a bar through the middle of the
    # pumpkin (the wave-5 first shots).
    z_top = _math(tree, "MULTIPLY", (bx - 1700, by - 620),
                  gin.outputs["Body Depth M"], 0.42)
    neck_x = _math(tree, "ADD", (bx - 1700, by - 800), R.outputs[0],
                   _math(tree, "MULTIPLY", (bx - 1900, by - 800),
                         gin.outputs["Neck Length M"], 0.5).outputs[0])
    neck = _neck(tree, gin, (bx - 1300, by - 800), gin.outputs["Neck Length M"],
                 _math(tree, "MULTIPLY", (bx - 1500, by - 800),
                       gin.outputs["Body Diameter M"], 0.052).outputs[0],
                 neck_x.outputs[0], z_top.outputs[0])
    head = safe_node(tree, "GeometryNodeMeshCube", (bx - 1300, by - 1100))
    head.inputs["Size"].default_value = (0.09, 0.05, 0.055)
    head_geo = _xf(tree, (bx - 1100, by - 1100), head.outputs["Mesh"],
                   translation=_combine(tree, (bx - 1300, by - 1240),
                                       _math(tree, "ADD", (bx - 1500, by - 1240),
                                             neck_x.outputs[0],
                                             _math(tree, "MULTIPLY",
                                                   (bx - 1700, by - 1240),
                                                   gin.outputs["Neck Length M"],
                                                   0.5).outputs[0]).outputs[0],
                                       0.0, z_top.outputs[0])).outputs["Geometry"]

    # jawari bridge: a wide flat bar under the strings on the tabli
    jaw = safe_node(tree, "GeometryNodeMeshCube", (bx - 1300, by - 600))
    jaw.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    jaw_geo = _xf(tree, (bx - 1100, by - 600), jaw.outputs["Mesh"],
                  scale=_combine(tree, (bx - 1300, by - 740),
                                 _math(tree, "MULTIPLY",
                                       (bx - 1500, by - 740),
                                       gin.outputs["Body Diameter M"], 0.055).outputs[0],
                                 _math(tree, "MULTIPLY",
                                       (bx - 1500, by - 880),
                                       gin.outputs["Body Diameter M"], 0.72).outputs[0],
                                 _math(tree, "MULTIPLY",
                                       (bx - 1500, by - 1020),
                                       gin.outputs["Body Depth M"], 0.10).outputs[0]),
                  translation=_combine(tree, (bx - 1300, by - 1160),
                                      _math(tree, "MULTIPLY",
                                            (bx - 1500, by - 1160),
                                            R.outputs[0], 0.30).outputs[0],
                                      0.0,
                                      _math(tree, "MULTIPLY",
                                            (bx - 1500, by - 1300),
                                            gin.outputs["Body Depth M"],
                                            0.52).outputs[0])).outputs["Geometry"]

    # frets: a rank of thin arched bars along the neck, on top of it
    fret = safe_node(tree, "GeometryNodeMeshCube", (bx - 1300, by + 600))
    fret.inputs["Size"].default_value = (0.006, 1.0, 0.012)
    fret_sc = _combine(tree, (bx - 1500, by + 600),
                       1.0,
                       _math(tree, "MULTIPLY", (bx - 1700, by + 600),
                             gin.outputs["Body Diameter M"], 0.13).outputs[0],
                       1.0)
    fret_geo = _xf(tree, (bx - 1100, by + 600), fret.outputs["Mesh"],
                   scale=fret_sc).outputs["Geometry"]
    fret_pts = _rank_points_x(
        tree, (bx - 900, by + 600), gin.outputs["Fret Count"],
        _math(tree, "DIVIDE", (bx - 1100, by + 600),
              gin.outputs["Neck Length M"],
              gin.outputs["Fret Count"]).outputs[0])
    frets = _inst_rank(tree, (bx - 700, by + 600), fret_pts, fret_geo)
    frets_geo = _xf(tree, (bx - 500, by + 600), frets,
                    translation=_combine(tree, (bx - 700, by + 460),
                                        _math(tree, "MULTIPLY",
                                              (bx - 900, by + 460),
                                              R.outputs[0], 0.10).outputs[0],
                                        0.0,
                                        _math(tree, "MULTIPLY",
                                              (bx - 900, by + 320),
                                              gin.outputs["Body Depth M"],
                                              0.52).outputs[0])).outputs["Geometry"]

    # 7 main strings + the taraf sympathetic rank, both from the shared proto.
    # Laid flat along +X (see _lay_strings) from the tail over the neck.
    proto = _ensure_string_proto(tree, "MEL_harp_string_unit", 0.62)
    tail_x = _math(tree, "MULTIPLY", (bx - 1700, by + 700),
                   R.outputs[0], -1.15)
    main_len = _math(tree, "ADD", (bx - 1100, by + 900),
                     _math(tree, "MULTIPLY", (bx - 1300, by + 900),
                           gin.outputs["Neck Length M"], 0.96).outputs[0],
                     _math(tree, "MULTIPLY", (bx - 1300, by + 1040),
                           R.outputs[0], 1.20).outputs[0])
    spread = _math(tree, "MULTIPLY", (bx - 1100, by + 1040),
                   gin.outputs["Body Diameter M"], 0.085)
    strings, _ = _string_rank(
        tree, (bx - 300, by + 900), gin.outputs["String Count"],
        gin.outputs["String Count"], proto,
        spread_sock=_math(tree, "DIVIDE", (bx - 500, by + 900),
                          spread.outputs[0],
                          _math(tree, "SUBTRACT", (bx - 700, by + 900),
                                gin.outputs["String Count"], 1.0).outputs[0]).outputs[0],
        x_sock=_combine(tree, (bx - 500, by + 760), 0.0,
                        _math(tree, "MULTIPLY", (bx - 700, by + 760),
                              spread.outputs[0], -0.5).outputs[0], 0.0),
        length_sock=main_len.outputs[0])
    strings_lift = _lay_strings(
        tree, (bx - 100, by + 900), strings, main_len.outputs[0],
        tail_x.outputs[0],
        _math(tree, "MULTIPLY", (bx - 300, by + 760),
              gin.outputs["Body Depth M"], 0.58).outputs[0])

    sym_pts = _rank_points_x(
        tree, (bx - 900, by + 1300), gin.outputs["Sympathetic Count"],
        _math(tree, "DIVIDE", (bx - 1100, by + 1300),
              _math(tree, "MULTIPLY", (bx - 1300, by + 1300),
                    gin.outputs["Body Diameter M"], 0.13).outputs[0],
              _math(tree, "MAXIMUM", (bx - 1500, by + 1300),
                    gin.outputs["Sympathetic Count"], 1.0).outputs[0]).outputs[0])
    sym_inst = _inst_rank(tree, (bx - 700, by + 1300), sym_pts, proto,
                          scale_sock=_combine(
                              tree, (bx - 900, by + 1160), 1.0, 1.0,
                              _math(tree, "DIVIDE", (bx - 1100, by + 1160),
                                    main_len.outputs[0],
                                    _math(tree, "MAXIMUM", (bx - 1300, by + 1160),
                                          main_len.outputs[0], 1.0).outputs[0]
                                    ).outputs[0]).outputs["Vector"])
    sym_geo = _lay_strings(
        tree, (bx - 500, by + 1300), sym_inst, main_len.outputs[0],
        tail_x.outputs[0],
        _math(tree, "MULTIPLY", (bx - 700, by + 1160),
              gin.outputs["Body Depth M"], 0.46).outputs[0])

    geom = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 600, by))
    for s in (gourd_geo, tabli_geo, kaddu_geo, neck, head_geo, jaw_geo,
              frets_geo, strings_lift, sym_geo):
        if s is not None:
            link_sockets(tree, s, geom.inputs["Geometry"])

    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 600, by - 300))
    smod = _math(tree, "FLOORMOD", (bx + 600, by - 420), sidx.outputs["Index"], 12.0)
    _finish(tree, gin, gout, geom.outputs["Geometry"], (bx + 800, by), BID,
            [("string_semitone_mod12", smod.outputs[0]), ("higgsas_lead", 1.0)])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Gourd + Tabli", "nodes": ("UV Sphere", "Cylinder"), "role": "geometry"},
        {"title": "Neck + Frets", "nodes": ("Cube", "Instance on Points"), "role": "geometry"},
        {"title": "Strings + Taraf", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_koto
# ---------------------------------------------------------------------------

def build_music_koto(group_name="MEL_music_koto"):
    """Koto: paulownia board, two end rails, 13 strings, 13 movable ji bridges."""
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_koto"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 1.82, 0.9, 2.4)
    add_float_param(tree, "Body Width M", 0.24, 0.12, 0.5)
    add_float_param(tree, "Body Depth M", 0.07, 0.03, 0.2)
    add_int_param(tree, "String Count", 13, 7, 25)
    add_int_param(tree, "Bridge Count", 13, 7, 25)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    board_parts = _zither_body(tree, (bx - 1400, by),
                               gin.outputs["Body Length M"],
                               gin.outputs["Body Width M"],
                               gin.outputs["Body Depth M"])
    body_geo = board_parts[0] if board_parts else None
    rails = board_parts[1:] if board_parts else []

    # ji: a small angled bridge under each string, in one movable row
    ji = safe_node(tree, "GeometryNodeMeshCube", (bx - 1300, by + 700))
    ji.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    ji_geo = _xf(tree, (bx - 1100, by + 700), ji.outputs["Mesh"],
                 rotation=(0.0, math.radians(-28.0), 0.0),
                 scale=_combine(tree, (bx - 1300, by + 560),
                                _math(tree, "MULTIPLY", (bx - 1500, by + 560),
                                      gin.outputs["Body Width M"], 0.10).outputs[0],
                                _math(tree, "MULTIPLY", (bx - 1500, by + 420),
                                      gin.outputs["Body Width M"], 0.022).outputs[0],
                                _math(tree, "MULTIPLY", (bx - 1500, by + 280),
                                      gin.outputs["Body Depth M"], 0.62).outputs[0]
                                )).outputs["Geometry"]
    ji_spread = _math(tree, "DIVIDE", (bx - 1100, by + 700),
                      _math(tree, "MULTIPLY", (bx - 1300, by + 700),
                            gin.outputs["Body Width M"], 0.86).outputs[0],
                      _math(tree, "SUBTRACT", (bx - 1500, by + 700),
                            gin.outputs["Bridge Count"], 1.0).outputs[0])
    ji_pts = _rank_points_y(tree, (bx - 900, by + 700),
                            gin.outputs["Bridge Count"], ji_spread.outputs[0])
    ji_inst = _inst_rank(tree, (bx - 700, by + 700), ji_pts, ji_geo)
    ji_geo_final = _xf(tree, (bx - 500, by + 700), ji_inst,
                       translation=_combine(tree, (bx - 700, by + 560),
                                           _math(tree, "MULTIPLY",
                                                 (bx - 900, by + 560),
                                                 gin.outputs["Body Length M"],
                                                 0.18).outputs[0],
                                           0.0,
                                           _math(tree, "MULTIPLY",
                                                 (bx - 900, by + 420),
                                                 gin.outputs["Body Depth M"],
                                                 0.62).outputs[0])
                       ).outputs["Geometry"]

    proto = _ensure_string_proto(tree, "MEL_harp_string_unit", 1.20)
    spread = _math(tree, "MULTIPLY", (bx - 1100, by + 1000),
                   gin.outputs["Body Width M"], 0.82)
    koto_len = _math(tree, "MULTIPLY", (bx - 700, by + 860),
                     gin.outputs["Body Length M"], 0.90)
    strings, _ = _string_rank(
        tree, (bx - 300, by + 1000), gin.outputs["String Count"],
        gin.outputs["String Count"], proto,
        spread_sock=_math(tree, "DIVIDE", (bx - 500, by + 1000),
                          spread.outputs[0],
                          _math(tree, "SUBTRACT", (bx - 700, by + 1000),
                                gin.outputs["String Count"], 1.0).outputs[0]).outputs[0],
        x_sock=_combine(tree, (bx - 500, by + 860), 0.0,
                        _math(tree, "MULTIPLY", (bx - 700, by + 860),
                              spread.outputs[0], -0.5).outputs[0], 0.0),
        length_sock=koto_len.outputs[0])
    strings_geo = _lay_strings(
        tree, (bx - 100, by + 1000), strings, koto_len.outputs[0],
        _math(tree, "MULTIPLY", (bx - 300, by + 860),
              gin.outputs["Body Length M"], -0.47).outputs[0],
        _math(tree, "MULTIPLY", (bx - 500, by + 860),
              gin.outputs["Body Depth M"], 0.75).outputs[0])

    geom = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 600, by))
    for s in ([body_geo] + rails + [ji_geo_final, strings_geo]):
        if s is not None:
            link_sockets(tree, s, geom.inputs["Geometry"])

    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 600, by - 300))
    smod = _math(tree, "FLOORMOD", (bx + 600, by - 420), sidx.outputs["Index"], 12.0)
    _finish(tree, gin, gout, geom.outputs["Geometry"], (bx + 800, by), BID,
            [("string_semitone_mod12", smod.outputs[0]), ("higgsas_lead", 1.0)])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Paulownia Board", "nodes": ("Cube", "Transform"), "role": "geometry"},
        {"title": "Ji Bridges", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Strings", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_balalaika
# ---------------------------------------------------------------------------

def build_music_balalaika(group_name="MEL_music_balalaika"):
    """Balalaika: triangular prism body, round soundhole, fretted neck, 3 strings."""
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_balalaika"
    bx, by = 0, 0

    add_float_param(tree, "Body Width M", 0.33, 0.15, 0.6)
    add_float_param(tree, "Body Length M", 0.43, 0.2, 0.8)
    add_float_param(tree, "Body Depth M", 0.09, 0.03, 0.2)
    add_float_param(tree, "Neck Length M", 0.44, 0.2, 0.9)
    add_int_param(tree, "String Count", 3, 2, 6)
    add_int_param(tree, "Fret Count", 16, 6, 24)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    # triangular body: a THREE-vertex cone is a triangular prism (axis Z, so the
    # triangle lies in XY and the body depth is the prism's thickness).
    #
    # NO union with the lower bout and NO boolean here: measured 2026-10-03, a
    # MeshBoolean whose cutter touches the mesh's own boundary (the soundhole
    # disc at the triangle's wide edge) emits ZERO geometry, and the coplanar
    # union that fed it was empty for the same class of reason. The body is
    # therefore a plain triangle prism and the soundhole is a RIM RING laid on
    # the top face — the honest geometry for this primitive, no boolean at all.
    R = _math(tree, "MULTIPLY", (bx - 1700, by + 260),
              gin.outputs["Body Length M"], 0.62)
    tri = _cone(tree, (bx - 1500, by + 200), R.outputs[0], R.outputs[0],
                gin.outputs["Body Depth M"], vertices=3)
    body = tri.outputs["Mesh"] if tri is not None else None
    # lower bout: a short round rod lying along Y at the triangle's wide edge
    bout = _cyl(tree, (bx - 1500, by - 200),
                _math(tree, "MULTIPLY", (bx - 1700, by - 200),
                      gin.outputs["Body Depth M"], 0.62).outputs[0],
                _math(tree, "MULTIPLY", (bx - 1700, by - 340),
                      gin.outputs["Body Width M"], 0.72).outputs[0], vertices=32)
    bout_geo = _xf(tree, (bx - 1300, by - 200), bout.outputs["Mesh"],
                   rotation=(math.radians(90.0), 0.0, 0.0),
                   translation=_combine(tree, (bx - 1500, by - 340),
                                       _math(tree, "MULTIPLY",
                                             (bx - 1700, by - 340),
                                             R.outputs[0], -0.60).outputs[0],
                                       0.0, 0.0)).outputs["Geometry"]

    # soundhole: a rim ring on the top face near the wide end (no boolean)
    hole = _cyl(tree, (bx - 1500, by - 600),
                _math(tree, "MULTIPLY", (bx - 1700, by - 600),
                      gin.outputs["Body Length M"], 0.10).outputs[0],
                _math(tree, "MULTIPLY", (bx - 1700, by - 740),
                      gin.outputs["Body Depth M"], 0.04).outputs[0],
                vertices=24, fill=1)
    hole_geo = _xf(tree, (bx - 1300, by - 600), hole.outputs["Mesh"],
                   translation=_combine(tree, (bx - 1500, by - 740),
                                       _math(tree, "MULTIPLY",
                                             (bx - 1700, by - 740),
                                             R.outputs[0], -0.34).outputs[0],
                                       0.0,
                                       _math(tree, "MULTIPLY",
                                             (bx - 1700, by - 880),
                                             gin.outputs["Body Depth M"],
                                             0.53).outputs[0])).outputs["Geometry"]

    # neck + pegbox on the narrow vertex side
    neck_x = _math(tree, "ADD", (bx - 1700, by - 1000), R.outputs[0],
                   _math(tree, "MULTIPLY", (bx - 1900, by - 1000),
                         gin.outputs["Neck Length M"], 0.5).outputs[0])
    neck = _neck(tree, gin, (bx - 1300, by - 1000), gin.outputs["Neck Length M"],
                 _math(tree, "MULTIPLY", (bx - 1500, by - 1000),
                       gin.outputs["Body Width M"], 0.048).outputs[0],
                 neck_x.outputs[0], 0.0)
    head = safe_node(tree, "GeometryNodeMeshCube", (bx - 1300, by - 1300))
    head.inputs["Size"].default_value = (0.075, 0.042, 0.05)
    head_geo = _xf(tree, (bx - 1100, by - 1300), head.outputs["Mesh"],
                   translation=_combine(tree, (bx - 1300, by - 1440),
                                       _math(tree, "ADD", (bx - 1500, by - 1440),
                                             neck_x.outputs[0],
                                             _math(tree, "MULTIPLY",
                                                   (bx - 1700, by - 1440),
                                                   gin.outputs["Neck Length M"],
                                                   0.5).outputs[0]).outputs[0],
                                       0.0, 0.0)).outputs["Geometry"]

    # frets along the neck
    fret = safe_node(tree, "GeometryNodeMeshCube", (bx - 1300, by + 600))
    fret.inputs["Size"].default_value = (0.005, 1.0, 0.010)
    fret_geo = _xf(tree, (bx - 1100, by + 600), fret.outputs["Mesh"],
                   scale=_combine(tree, (bx - 1300, by + 600), 1.0,
                                  _math(tree, "MULTIPLY",
                                        (bx - 1500, by + 600),
                                        gin.outputs["Body Width M"], 0.11).outputs[0],
                                  1.0)).outputs["Geometry"]
    fret_pts = _rank_points_x(
        tree, (bx - 900, by + 600), gin.outputs["Fret Count"],
        _math(tree, "DIVIDE", (bx - 1100, by + 600),
              gin.outputs["Neck Length M"],
              gin.outputs["Fret Count"]).outputs[0])
    frets_geo = _inst_rank(tree, (bx - 700, by + 600), fret_pts, fret_geo)
    frets_final = _xf(tree, (bx - 500, by + 600), frets_geo,
                      translation=_combine(tree, (bx - 700, by + 460),
                                          _math(tree, "MULTIPLY",
                                                (bx - 900, by + 460),
                                                R.outputs[0], 0.14).outputs[0],
                                          0.0,
                                          _math(tree, "MULTIPLY",
                                                (bx - 900, by + 320),
                                                gin.outputs["Body Depth M"],
                                                0.60).outputs[0])).outputs["Geometry"]

    proto = _ensure_string_proto(tree, "MEL_harp_string_unit", 0.55)
    spread = _math(tree, "MULTIPLY", (bx - 1100, by + 900),
                   gin.outputs["Body Width M"], 0.075)
    bal_len = _math(tree, "ADD", (bx - 700, by + 760),
                    _math(tree, "MULTIPLY", (bx - 900, by + 760),
                          gin.outputs["Body Length M"], 0.86).outputs[0],
                    gin.outputs["Neck Length M"])
    strings, _ = _string_rank(
        tree, (bx - 300, by + 900), gin.outputs["String Count"],
        gin.outputs["String Count"], proto,
        spread_sock=_math(tree, "DIVIDE", (bx - 500, by + 900),
                          spread.outputs[0],
                          _math(tree, "SUBTRACT", (bx - 700, by + 900),
                                gin.outputs["String Count"], 1.0).outputs[0]).outputs[0],
        x_sock=_combine(tree, (bx - 500, by + 760), 0.0,
                        _math(tree, "MULTIPLY", (bx - 700, by + 760),
                              spread.outputs[0], -0.5).outputs[0], 0.0),
        length_sock=bal_len.outputs[0])
    strings_geo = _lay_strings(
        tree, (bx - 100, by + 900), strings, bal_len.outputs[0],
        _math(tree, "MULTIPLY", (bx - 300, by + 760),
              gin.outputs["Body Length M"], -0.42).outputs[0],
        _math(tree, "MULTIPLY", (bx - 500, by + 760),
              gin.outputs["Body Depth M"], 0.62).outputs[0])

    geom = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 600, by))
    for s in (body, bout_geo, hole_geo, neck, head_geo, frets_final, strings_geo):
        if s is not None:
            link_sockets(tree, s, geom.inputs["Geometry"])

    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 600, by - 300))
    smod = _math(tree, "FLOORMOD", (bx + 600, by - 420), sidx.outputs["Index"], 12.0)
    _finish(tree, gin, gout, geom.outputs["Geometry"], (bx + 800, by), BID,
            [("string_semitone_mod12", smod.outputs[0]), ("higgsas_lead", 1.0)])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Triangular Body", "nodes": ("Cone", "Mesh Boolean"), "role": "geometry"},
        {"title": "Neck + Frets", "nodes": ("Cube", "Instance on Points"), "role": "geometry"},
        {"title": "Strings", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_shamisen
# ---------------------------------------------------------------------------

def build_music_shamisen(group_name="MEL_music_shamisen"):
    """Shamisen: square dou with front/back skins, 3-section sao, 3 strings, bachi."""
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_shamisen"
    bx, by = 0, 0

    add_float_param(tree, "Body Width M", 0.20, 0.1, 0.4)
    add_float_param(tree, "Body Depth M", 0.075, 0.03, 0.2)
    add_float_param(tree, "Neck Length M", 0.80, 0.3, 1.3)
    add_int_param(tree, "String Count", 3, 2, 4)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    R = _math(tree, "MULTIPLY", (bx - 1700, by + 260),
              gin.outputs["Body Width M"], 0.5)
    # dou: a FOUR-vertex cylinder is a square body; spin 45 deg to sit axis-aligned
    dou_geo, _ = _prism_body(tree, (bx - 1500, by + 200), 4, R.outputs[0],
                             gin.outputs["Body Depth M"],
                             spin=math.radians(45.0))
    # skins: two plates clamped on the front and back faces. Radius is set so the
    # plate diameter matches the DOU's across-flats width (a 4-gon of radius R
    # spans 1.414*R), not the circumradius — otherwise the skins overhang.
    skin = _cyl(tree, (bx - 1500, by - 200),
                _math(tree, "MULTIPLY", (bx - 1700, by - 200), R.outputs[0], 0.72).outputs[0],
                _math(tree, "MULTIPLY", (bx - 1700, by - 340),
                      gin.outputs["Body Depth M"], 0.06).outputs[0], vertices=32)
    skin_geos = []
    for sz in (-1.0, 1.0):
        skin_geos.append(_xf(
            tree, (bx - 1300, by - 200 + int(sz) * 200), skin.outputs["Mesh"],
            rotation=(0.0, 0.0, math.radians(45.0)),
            translation=_combine(tree, (bx - 1500, by - 340 + int(sz) * 200),
                                0.0, 0.0,
                                _math(tree, "MULTIPLY",
                                      (bx - 1700, by - 340 + int(sz) * 200),
                                      gin.outputs["Body Depth M"],
                                      0.50 * sz).outputs[0])).outputs["Geometry"])

    # sao: three neck sections, the signature of the shamisen
    neck_x = _math(tree, "ADD", (bx - 1700, by - 900), R.outputs[0],
                   _math(tree, "MULTIPLY", (bx - 1900, by - 900),
                         gin.outputs["Neck Length M"], 0.5).outputs[0])
    sao = _neck(tree, gin, (bx - 1300, by - 900), gin.outputs["Neck Length M"],
                _math(tree, "MULTIPLY", (bx - 1500, by - 900),
                      gin.outputs["Body Width M"], 0.045).outputs[0],
                neck_x.outputs[0], 0.0)
    # section collars: three rings along the neck naming its three joints
    collar = _cyl(tree, (bx - 1300, by - 1200),
                  _math(tree, "MULTIPLY", (bx - 1500, by - 1200),
                        gin.outputs["Body Width M"], 0.062).outputs[0],
                  _math(tree, "MULTIPLY", (bx - 1500, by - 1340),
                        gin.outputs["Body Width M"], 0.045).outputs[0], vertices=12)
    collar_geo = _xf(tree, (bx - 1100, by - 1200), collar.outputs["Mesh"],
                     rotation=(0.0, math.radians(90.0), 0.0),
                     translation=_combine(tree, (bx - 1300, by - 1340),
                                         _math(tree, "MULTIPLY",
                                               (bx - 1500, by - 1340),
                                               R.outputs[0], -0.30).outputs[0],
                                         0.0, 0.0)).outputs["Geometry"]
    head = safe_node(tree, "GeometryNodeMeshCube", (bx - 1300, by - 1600))
    head.inputs["Size"].default_value = (0.085, 0.045, 0.05)
    head_geo = _xf(tree, (bx - 1100, by - 1600), head.outputs["Mesh"],
                   translation=_combine(tree, (bx - 1300, by - 1740),
                                       _math(tree, "ADD", (bx - 1500, by - 1740),
                                             neck_x.outputs[0],
                                             _math(tree, "MULTIPLY",
                                                   (bx - 1700, by - 1740),
                                                   gin.outputs["Neck Length M"],
                                                   0.5).outputs[0]).outputs[0],
                                       0.0, 0.0)).outputs["Geometry"]

    # bachi: the large angled plectrum, kept as a prop beside the body
    bachi = safe_node(tree, "GeometryNodeMeshCube", (bx - 1300, by + 700))
    bachi.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    bachi_geo = _xf(tree, (bx - 1100, by + 700), bachi.outputs["Mesh"],
                    rotation=(0.0, math.radians(-24.0), 0.0),
                    scale=_combine(tree, (bx - 1300, by + 560),
                                   _math(tree, "MULTIPLY", (bx - 1500, by + 560),
                                         gin.outputs["Body Width M"], 0.55).outputs[0],
                                   _math(tree, "MULTIPLY", (bx - 1500, by + 420),
                                         gin.outputs["Body Width M"], 0.32).outputs[0],
                                   _math(tree, "MULTIPLY", (bx - 1500, by + 280),
                                         gin.outputs["Body Depth M"], 0.09).outputs[0]
                                   ),
                    translation=_combine(tree, (bx - 1300, by + 420),
                                        _math(tree, "MULTIPLY",
                                              (bx - 1500, by + 420),
                                              R.outputs[0], 1.90).outputs[0],
                                        0.0, 0.0)).outputs["Geometry"]

    proto = _ensure_string_proto(tree, "MEL_harp_string_unit", 0.80)
    spread = _math(tree, "MULTIPLY", (bx - 1100, by + 900),
                   gin.outputs["Body Width M"], 0.10)
    sh_len = _math(tree, "ADD", (bx - 700, by + 760),
                   _math(tree, "MULTIPLY", (bx - 900, by + 760),
                         gin.outputs["Body Width M"], 1.10).outputs[0],
                   gin.outputs["Neck Length M"])
    strings, _ = _string_rank(
        tree, (bx - 300, by + 900), gin.outputs["String Count"],
        gin.outputs["String Count"], proto,
        spread_sock=_math(tree, "DIVIDE", (bx - 500, by + 900),
                          spread.outputs[0],
                          _math(tree, "SUBTRACT", (bx - 700, by + 900),
                                gin.outputs["String Count"], 1.0).outputs[0]).outputs[0],
        x_sock=_combine(tree, (bx - 500, by + 760), 0.0,
                        _math(tree, "MULTIPLY", (bx - 700, by + 760),
                              spread.outputs[0], -0.5).outputs[0], 0.0),
        length_sock=sh_len.outputs[0])
    strings_geo = _lay_strings(
        tree, (bx - 100, by + 900), strings, sh_len.outputs[0],
        _math(tree, "MULTIPLY", (bx - 300, by + 760),
              gin.outputs["Body Width M"], -0.70).outputs[0],
        _math(tree, "MULTIPLY", (bx - 500, by + 760),
              gin.outputs["Body Depth M"], 0.60).outputs[0])

    geom = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 600, by))
    for s in ([dou_geo] + skin_geos + [sao, collar_geo, head_geo, bachi_geo,
                                       strings_geo]):
        if s is not None:
            link_sockets(tree, s, geom.inputs["Geometry"])

    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 600, by - 300))
    smod = _math(tree, "FLOORMOD", (bx + 600, by - 420), sidx.outputs["Index"], 12.0)
    _finish(tree, gin, gout, geom.outputs["Geometry"], (bx + 800, by), BID,
            [("string_semitone_mod12", smod.outputs[0]), ("higgsas_lead", 1.0)])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Square Dou + Skins", "nodes": ("Cylinder", "Transform"), "role": "geometry"},
        {"title": "Sao Neck + Bachi", "nodes": ("Cube", "Transform"), "role": "geometry"},
        {"title": "Strings", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_erhu
# ---------------------------------------------------------------------------

def build_music_erhu(group_name="MEL_music_erhu"):
    """Erhu: hexagonal soundbox with python skin, qin gan, 2 strings, qianjin, bow."""
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_erhu"
    bx, by = 0, 0

    add_float_param(tree, "Body Diameter M", 0.10, 0.05, 0.25)
    add_float_param(tree, "Body Depth M", 0.085, 0.04, 0.2)
    add_float_param(tree, "Neck Length M", 0.78, 0.3, 1.3)
    add_int_param(tree, "String Count", 2, 2, 4)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    R = _math(tree, "MULTIPLY", (bx - 1700, by + 260),
              gin.outputs["Body Diameter M"], 0.5)
    # soundbox: a SIX-vertex cylinder — the erhu's hexagonal drum
    box_geo, _ = _prism_body(tree, (bx - 1500, by + 200), 6, R.outputs[0],
                             gin.outputs["Body Depth M"])
    # python skin: a taut membrane across the front face
    skin = _cyl(tree, (bx - 1500, by - 200),
                _math(tree, "MULTIPLY", (bx - 1700, by - 200), R.outputs[0], 1.04).outputs[0],
                _math(tree, "MULTIPLY", (bx - 1700, by - 340),
                      gin.outputs["Body Depth M"], 0.05).outputs[0], vertices=32)
    skin_geo = _xf(tree, (bx - 1300, by - 200), skin.outputs["Mesh"],
                   translation=_combine(tree, (bx - 1500, by - 340),
                                       0.0, 0.0,
                                       _math(tree, "MULTIPLY",
                                             (bx - 1700, by - 340),
                                             gin.outputs["Body Depth M"],
                                             0.52).outputs[0])).outputs["Geometry"]

    # qin gan: the long neck straight through the box, plus two tuning pegs
    neck_x = _math(tree, "ADD", (bx - 1700, by - 900), R.outputs[0],
                   _math(tree, "MULTIPLY", (bx - 1900, by - 900),
                         gin.outputs["Neck Length M"], 0.5).outputs[0])
    neck = _neck(tree, gin, (bx - 1300, by - 900), gin.outputs["Neck Length M"],
                 _math(tree, "MULTIPLY", (bx - 1500, by - 900),
                       gin.outputs["Body Diameter M"], 0.085).outputs[0],
                 neck_x.outputs[0], 0.0)
    peg = _cyl(tree, (bx - 1300, by - 1300), 0.009,
               _math(tree, "MULTIPLY", (bx - 1500, by - 1300),
                     gin.outputs["Body Diameter M"], 0.62).outputs[0], vertices=8)
    peg_geos = []
    for sy in (-1.0, 1.0):
        peg_geos.append(_xf(
            tree, (bx - 1100, by - 1300 + int(sy) * 200), peg.outputs["Mesh"],
            rotation=(math.radians(90.0), 0.0, 0.0),
            translation=_combine(tree, (bx - 1300, by - 1440 + int(sy) * 200),
                                _math(tree, "ADD", (bx - 1500, by - 1440 + int(sy) * 200),
                                      neck_x.outputs[0],
                                      _math(tree, "MULTIPLY",
                                            (bx - 1700, by - 1440 + int(sy) * 200),
                                            gin.outputs["Neck Length M"],
                                            0.40).outputs[0]).outputs[0],
                                0.0, 0.0)).outputs["Geometry"])

    # qianjin: the loop of cord that ties the two strings to the neck
    qianjin = _cyl(tree, (bx - 1300, by - 1700),
                   _math(tree, "MULTIPLY", (bx - 1500, by - 1700),
                         gin.outputs["Body Diameter M"], 0.20).outputs[0],
                   _math(tree, "MULTIPLY", (bx - 1500, by - 1840),
                         gin.outputs["Body Diameter M"], 0.055).outputs[0], vertices=16)
    qianjin_geo = _xf(tree, (bx - 1100, by - 1700), qianjin.outputs["Mesh"],
                      rotation=(0.0, math.radians(90.0), 0.0),
                      translation=_combine(tree, (bx - 1300, by - 1840),
                                          _math(tree, "ADD", (bx - 1500, by - 1840),
                                                neck_x.outputs[0],
                                                _math(tree, "MULTIPLY",
                                                      (bx - 1700, by - 1840),
                                                      gin.outputs["Neck Length M"],
                                                      0.24).outputs[0]).outputs[0],
                                          0.0, 0.0)).outputs["Geometry"]

    # bridge: a small wedge on the python skin
    bridge = safe_node(tree, "GeometryNodeMeshCube", (bx - 1300, by + 600))
    bridge.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    bridge_geo = _xf(tree, (bx - 1100, by + 600), bridge.outputs["Mesh"],
                     scale=_combine(tree, (bx - 1300, by + 460),
                                    _math(tree, "MULTIPLY", (bx - 1500, by + 460),
                                          gin.outputs["Body Diameter M"], 0.30).outputs[0],
                                    _math(tree, "MULTIPLY", (bx - 1500, by + 320),
                                          gin.outputs["Body Diameter M"], 0.10).outputs[0],
                                    _math(tree, "MULTIPLY", (bx - 1500, by + 180),
                                          gin.outputs["Body Depth M"], 0.10).outputs[0]
                                    ),
                     translation=_combine(tree, (bx - 1300, by + 320),
                                         0.0, 0.0,
                                         _math(tree, "MULTIPLY",
                                               (bx - 1500, by + 320),
                                               gin.outputs["Body Depth M"],
                                               0.56).outputs[0])).outputs["Geometry"]

    proto = _ensure_string_proto(tree, "MEL_harp_string_unit", 0.75)
    spread = _math(tree, "MULTIPLY", (bx - 1100, by + 900),
                   gin.outputs["Body Diameter M"], 0.16)
    er_len = _math(tree, "ADD", (bx - 700, by + 760),
                   _math(tree, "MULTIPLY", (bx - 900, by + 760),
                         gin.outputs["Body Diameter M"], 1.4).outputs[0],
                   gin.outputs["Neck Length M"])
    strings, _ = _string_rank(
        tree, (bx - 300, by + 900), gin.outputs["String Count"],
        gin.outputs["String Count"], proto,
        spread_sock=_math(tree, "DIVIDE", (bx - 500, by + 900),
                          spread.outputs[0],
                          _math(tree, "SUBTRACT", (bx - 700, by + 900),
                                gin.outputs["String Count"], 1.0).outputs[0]).outputs[0],
        x_sock=_combine(tree, (bx - 500, by + 760), 0.0,
                        _math(tree, "MULTIPLY", (bx - 700, by + 760),
                              spread.outputs[0], -0.5).outputs[0], 0.0),
        length_sock=er_len.outputs[0])
    strings_geo = _lay_strings(
        tree, (bx - 100, by + 900), strings, er_len.outputs[0],
        _math(tree, "MULTIPLY", (bx - 300, by + 760),
              gin.outputs["Body Diameter M"], -0.75).outputs[0],
        _math(tree, "MULTIPLY", (bx - 500, by + 760),
              gin.outputs["Body Depth M"], 0.62).outputs[0])

    # bow: a stick with horsehair, lying across the string band
    stick = _cyl(tree, (bx - 1300, by + 1300), 0.006,
                 _math(tree, "MULTIPLY", (bx - 1500, by + 1300),
                       gin.outputs["Neck Length M"], 0.86).outputs[0], vertices=8)
    bow_parts = []
    for dz, rr in ((0.0, 1.0), (0.012, 0.35)):
        bow_parts.append(_xf(
            tree, (bx - 1100, by + 1300 + int(rr * 100)), stick.outputs["Mesh"],
            rotation=(0.0, math.radians(90.0), 0.0),
            translation=_combine(tree, (bx - 1300, by + 1440 + int(rr * 100)),
                                0.0, 0.0,
                                _math(tree, "ADD", (bx - 1500, by + 1440),
                                      _math(tree, "MULTIPLY",
                                            (bx - 1700, by + 1440),
                                            gin.outputs["Body Depth M"],
                                            0.30).outputs[0],
                                      dz).outputs[0])).outputs["Geometry"])

    geom = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 600, by))
    for s in [box_geo, skin_geo, neck] + peg_geos + [qianjin_geo, bridge_geo,
                                                     strings_geo] + bow_parts:
        if s is not None:
            link_sockets(tree, s, geom.inputs["Geometry"])

    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 600, by - 300))
    smod = _math(tree, "FLOORMOD", (bx + 600, by - 420), sidx.outputs["Index"], 12.0)
    _finish(tree, gin, gout, geom.outputs["Geometry"], (bx + 800, by), BID,
            [("string_semitone_mod12", smod.outputs[0]), ("higgsas_lead", 1.0)])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Hex Soundbox + Skin", "nodes": ("Cylinder", "Transform"), "role": "geometry"},
        {"title": "Qin Gan + Pegs", "nodes": ("Cube", "Transform"), "role": "geometry"},
        {"title": "Strings + Bow", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_guzheng
# ---------------------------------------------------------------------------

def build_music_guzheng(group_name="MEL_music_guzheng"):
    """Guzheng: long board with an arched top, 21 strings, 21 zhen ma bridges."""
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_guzheng"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 1.63, 0.8, 2.2)
    add_float_param(tree, "Body Width M", 0.30, 0.15, 0.55)
    add_float_param(tree, "Body Depth M", 0.10, 0.04, 0.25)
    add_int_param(tree, "String Count", 21, 13, 30)
    add_int_param(tree, "Bridge Count", 21, 13, 30)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    board_parts = _zither_body(tree, (bx - 1400, by),
                               gin.outputs["Body Length M"],
                               gin.outputs["Body Width M"],
                               gin.outputs["Body Depth M"],
                               rail_frac=0.075, vertices=8)
    body_geo = board_parts[0] if board_parts else None
    rails = board_parts[1:] if board_parts else []

    # arched top: a second, shallower board whose width tapers — the guzheng's
    # characteristic convex soundboard, expressed as a scaled thin box
    arch = safe_node(tree, "GeometryNodeMeshCube", (bx - 1400, by - 500))
    arch_h = _math(tree, "MULTIPLY", (bx - 1600, by - 500),
                   gin.outputs["Body Depth M"], 0.30)
    link_sockets(tree, _combine(tree, (bx - 1600, by - 640),
                                _math(tree, "MULTIPLY", (bx - 1800, by - 640),
                                      gin.outputs["Body Length M"], 0.99).outputs[0],
                                _math(tree, "MULTIPLY", (bx - 1800, by - 780),
                                      gin.outputs["Body Width M"], 1.02).outputs[0],
                                arch_h.outputs[0]).outputs["Vector"],
                 arch.inputs["Size"])
    arch_geo = _xf(tree, (bx - 1200, by - 500), arch.outputs["Mesh"],
                   translation=_combine(tree, (bx - 1400, by - 640), 0.0, 0.0,
                                       _math(tree, "MULTIPLY",
                                             (bx - 1600, by - 640),
                                             gin.outputs["Body Depth M"],
                                             0.62).outputs[0])).outputs["Geometry"]

    # zhen ma: a movable bridge under each string, in one row
    ma = safe_node(tree, "GeometryNodeMeshCube", (bx - 1300, by + 700))
    ma.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    ma_geo = _xf(tree, (bx - 1100, by + 700), ma.outputs["Mesh"],
                 rotation=(0.0, math.radians(-30.0), 0.0),
                 scale=_combine(tree, (bx - 1300, by + 560),
                                _math(tree, "MULTIPLY", (bx - 1500, by + 560),
                                      gin.outputs["Body Width M"], 0.085).outputs[0],
                                _math(tree, "MULTIPLY", (bx - 1500, by + 420),
                                      gin.outputs["Body Width M"], 0.020).outputs[0],
                                _math(tree, "MULTIPLY", (bx - 1500, by + 280),
                                      gin.outputs["Body Depth M"], 0.72).outputs[0]
                                )).outputs["Geometry"]
    ma_spread = _math(tree, "DIVIDE", (bx - 1100, by + 700),
                      _math(tree, "MULTIPLY", (bx - 1300, by + 700),
                            gin.outputs["Body Width M"], 0.88).outputs[0],
                      _math(tree, "SUBTRACT", (bx - 1500, by + 700),
                            gin.outputs["Bridge Count"], 1.0).outputs[0])
    ma_pts = _rank_points_y(tree, (bx - 900, by + 700),
                            gin.outputs["Bridge Count"], ma_spread.outputs[0])
    ma_inst = _inst_rank(tree, (bx - 700, by + 700), ma_pts, ma_geo)
    ma_geo_final = _xf(tree, (bx - 500, by + 700), ma_inst,
                       translation=_combine(tree, (bx - 700, by + 560),
                                           _math(tree, "MULTIPLY",
                                                 (bx - 900, by + 560),
                                                 gin.outputs["Body Length M"],
                                                 0.13).outputs[0],
                                           0.0,
                                           _math(tree, "MULTIPLY",
                                                 (bx - 900, by + 420),
                                                 gin.outputs["Body Depth M"],
                                                 0.78).outputs[0])
                       ).outputs["Geometry"]

    proto = _ensure_string_proto(tree, "MEL_harp_string_unit", 1.30)
    spread = _math(tree, "MULTIPLY", (bx - 1100, by + 1000),
                   gin.outputs["Body Width M"], 0.86)
    gz_len = _math(tree, "MULTIPLY", (bx - 700, by + 860),
                   gin.outputs["Body Length M"], 0.90)
    strings, _ = _string_rank(
        tree, (bx - 300, by + 1000), gin.outputs["String Count"],
        gin.outputs["String Count"], proto,
        spread_sock=_math(tree, "DIVIDE", (bx - 500, by + 1000),
                          spread.outputs[0],
                          _math(tree, "SUBTRACT", (bx - 700, by + 1000),
                                gin.outputs["String Count"], 1.0).outputs[0]).outputs[0],
        x_sock=_combine(tree, (bx - 500, by + 860), 0.0,
                        _math(tree, "MULTIPLY", (bx - 700, by + 860),
                              spread.outputs[0], -0.5).outputs[0], 0.0),
        length_sock=gz_len.outputs[0])
    strings_geo = _lay_strings(
        tree, (bx - 100, by + 1000), strings, gz_len.outputs[0],
        _math(tree, "MULTIPLY", (bx - 300, by + 860),
              gin.outputs["Body Length M"], -0.46).outputs[0],
        _math(tree, "MULTIPLY", (bx - 500, by + 860),
              gin.outputs["Body Depth M"], 0.95).outputs[0])

    geom = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 600, by))
    for s in ([body_geo] + rails + [arch_geo, ma_geo_final, strings_geo]):
        if s is not None:
            link_sockets(tree, s, geom.inputs["Geometry"])

    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 600, by - 300))
    smod = _math(tree, "FLOORMOD", (bx + 600, by - 420), sidx.outputs["Index"], 12.0)
    _finish(tree, gin, gout, geom.outputs["Geometry"], (bx + 800, by), BID,
            [("string_semitone_mod12", smod.outputs[0]), ("higgsas_lead", 1.0)])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Board + Arch", "nodes": ("Cube", "Transform"), "role": "geometry"},
        {"title": "Zhen Ma Bridges", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Strings", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

register_builder(
    "MEL_music_sitar", build_music_sitar, "Sitar",
    "Sitar: gourd resonator, tabli soundboard, jawari bridge, long fretted neck, "
    "7 main strings and a taraf sympathetic rank. Native-only.",
    "music",
)
register_builder(
    "MEL_music_koto", build_music_koto, "Koto",
    "Koto: paulownia board with two end rails, 13 strings, 13 movable ji "
    "bridges. Native-only.",
    "music",
)
register_builder(
    "MEL_music_balalaika", build_music_balalaika, "Balalaika",
    "Balalaika: triangular prism body with a rounded lower bout, round "
    "soundhole, fretted neck, 3 strings. Native-only.",
    "music",
)
register_builder(
    "MEL_music_shamisen", build_music_shamisen, "Shamisen",
    "Shamisen: square dou with front/back skins, three-section sao neck, collar "
    "rings, bachi plectrum, 3 strings. Native-only.",
    "music",
)
register_builder(
    "MEL_music_erhu", build_music_erhu, "Erhu",
    "Erhu: hexagonal soundbox with a python-skin membrane, qin gan neck, tuning "
    "pegs, qianjin cord, bridge, 2 strings and a bow. Native-only.",
    "music",
)
register_builder(
    "MEL_music_guzheng", build_music_guzheng, "Guzheng",
    "Guzheng: long board with an arched soundboard and end rails, 21 strings, "
    "21 movable zhen ma bridges. Native-only.",
    "music",
)
