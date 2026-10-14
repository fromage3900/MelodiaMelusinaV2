"""P4 wave 4 — string lane: cello, viola, double bass, banjo, mandolin, ukulele.

Gap audit first (repo-wide grep over `deploy/surreal_arch/` + the live registry,
2026-10-03): the string lane owns `MEL_music_baroque_violin`, `MEL_music_baroque_lute`,
`MEL_music_baroque_harpsichord`, `MEL_music_dulcimer`, `MEL_music_kalimba`,
`MEL_music_lissajous_harp`, the five `MEL_harp_*` ids and `MEL_violin_bow`. NONE of
the six ids below existed anywhere (grep count 0 each):

    cello, viola, double bass, banjo, mandolin, ukulele

Nothing here re-implements an existing id. The bowed family (cello/viola/double bass)
is a SIZING of the violin's own anatomy, not a second violin builder: one `_bowed_body`
law takes a body length and derives every proportion from it, exactly the way
`MEL_chime_tube`'s graduation law is reused rather than re-authored per chime.

Design rules (same as music_wind_percussion / music_percussion_kit):
  - ONE authored group may lead a builder. These six are native-only: the bowed and
    plucked bodies are lofted plates and swept ribs that 5.2 primitives express
    exactly, and a Higgsas subtree here would be decoration, not a lead. Every
    builder still stores `higgsas_lead` (1.0 = native) so the family gate and the
    instruments gate read them uniformly.
  - String ranks come from the shared `MEL_harp_string_unit` proto (music_harps_real)
    — never a private string cylinder, which is the duplication this lane avoids.
  - Line offsets are always CombineXYZ (a bare float broadcasts to (v, v, v)).
  - A field value never feeds a PRIMITIVE dimension (the collapse class): every
    primitive dimension here is a socket-driven CombineXYZ component with all three
    components written.

Builders:
    MEL_music_cello        body 0.76 m, 4 strings, endpin, C-bout ribs
    MEL_music_viola        body 0.42 m, 4 strings (the alto of the same law)
    MEL_music_double_bass  body 1.10 m, 4 strings, tall neck, endpin
    MEL_music_banjo        round drum head + tension hoop + 5 strings + resonator
    MEL_music_mandolin     8 strings in 4 courses + scroll + f-holes
    MEL_music_ukulele      4 strings, small body, pin bridge
"""

from __future__ import annotations

import math

from .core import (
    safe_node, link_sockets, label_tree, new_geometry_tree, add_float_param,
    add_int_param, add_bool_param, register_builder, sock, mesh_boolean_node,
)
from .music_harps_real import (
    _math, _combine, _export_tail, _ensure_string_proto,
)
from .music_higgsas_instruments import (
    _store_named, _cone, _cyl, _line, _xf, _set_fill,
)

# ---------------------------------------------------------------------------
# Shared laws — authored once, sized per instrument
# ---------------------------------------------------------------------------

# Fraction of the body length that each landmark sits at, measured along +X.
# These are the violin family's own proportions, expressed as ratios so the
# cello/viola/double-bass are SIZINGS, not three copies of the same numbers.
_BOUT_RATIOS = (0.16, 0.34, 0.50, 0.68, 0.86)   # lower / C / waist / upper / neck


def _string_rank(tree, loc, count_sock, span_sock, proto, spread_sock=None,
                 x_sock=None, length_sock=None, radius_sock=None):
    """A rank of strings from the shared `MEL_harp_string_unit` proto.

    Returns (instances_socket, points_socket). `span_sock` is the total fan
    width; `x_sock` shifts the whole rank along +X (the neck/bridge axis).

    `length_sock` / `radius_sock` are linked into the PROTO NODE's own group
    inputs, so each instrument gets its own string length. Without that the
    shared group keeps whatever length it was first created with (0.62 m, the
    concert harp's), and every instrument measures the same z extent.
    """
    bx, by = loc
    if proto is not None:
        if length_sock is not None and proto.inputs.get("Length M") is not None:
            link_sockets(tree, length_sock, proto.inputs["Length M"])
        if radius_sock is not None and proto.inputs.get("Radius M") is not None:
            link_sockets(tree, radius_sock, proto.inputs["Radius M"])
    n = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by))
    if n is None:
        return None, None
    link_sockets(tree, count_sock, sock(n, "Count"))
    if x_sock is not None:
        link_sockets(tree, x_sock, sock(n, "Start Location"))
    off = _combine(tree, (bx - 600, by - 140), 0.0, spread_sock, 0.0)
    link_sockets(tree, off.outputs["Vector"], sock(n, "Offset"))
    pts = safe_node(tree, "GeometryNodeMeshToPoints", (bx - 200, by))
    if pts is not None:
        link_sockets(tree, n.outputs["Mesh"], sock(pts, "Mesh") or pts.inputs[0])
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx, by))
    if inst is not None:
        link_sockets(tree, pts.outputs["Points"] if pts is not None else None,
                     sock(inst, "Points"))
        link_sockets(tree, proto.outputs["Geometry"] if proto is not None else None,
                     sock(inst, "Instance"))
    return (inst.outputs["Instances"] if inst is not None else None,
            pts.outputs["Points"] if pts is not None else None)


def _bowed_body(tree, gin, loc, length_sock, depth_sock, width_sock,
                rib_thick, vertices=48):
    """The violin-family body: a lofted plate pair with C-bout ribs.

    ONE law for the whole bowed family. The outline is a scaled cylinder whose
    X/Y radii are the body's half-length and half-width, and the C-bouts are a
    subtractive boolean of two side circles — the same waist the violin has,
    scaled by the caller's sockets. Returns (body_geometry, waist_centre_x).
    """
    bx, by = loc
    half_len = _math(tree, "MULTIPLY", (bx - 300, by + 200), length_sock, 0.5)
    half_w = _math(tree, "MULTIPLY", (bx - 300, by - 200), width_sock, 0.5)

    plate = _cyl(tree, (bx, by), 1.0, depth_sock, vertices=vertices, fill=2)
    # Cylinder radius is ONE socket: route the two axes through a Transform
    # scale so X/Y can differ (a vector input cannot be linked per component).
    plate_sc = _combine(tree, (bx - 100, by + 200), half_len.outputs[0],
                        half_w.outputs[0], 1.0)
    plate_xf = _xf(tree, (bx + 200, by), plate.outputs["Mesh"], scale=plate_sc)

    # C-bouts: two circles cut from each side at the waist
    waist_x = _math(tree, "MULTIPLY", (bx - 300, by - 600), length_sock, 0.06)
    cut = _cyl(tree, (bx, by - 600),
               _math(tree, "MULTIPLY", (bx - 300, by - 800), width_sock, 0.30).outputs[0],
               _math(tree, "MULTIPLY", (bx - 300, by - 1000), depth_sock, 3.0).outputs[0],
               vertices=32, fill=2)
    cut_r = _xf(tree, (bx + 200, by - 600), cut.outputs["Mesh"],
                translation=_combine(tree, (bx, by - 800),
                                    half_len.outputs[0], 0.0, 0.0))
    cut_l = _xf(tree, (bx + 200, by - 1000), cut.outputs["Mesh"],
                translation=_combine(tree, (bx, by - 1200),
                                    _math(tree, "MULTIPLY",
                                          (bx - 300, by - 1200),
                                          half_len.outputs[0], -1.0).outputs[0],
                                    0.0, 0.0))
    cut_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 400, by - 800))
    for s in (cut_r.outputs["Geometry"], cut_l.outputs["Geometry"]):
        link_sockets(tree, s, cut_join.inputs["Geometry"])
    waist_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 400, by - 400))
    link_sockets(tree, cut.outputs["Mesh"], waist_join.inputs["Geometry"])
    waist_geo = _xf(tree, (bx + 600, by - 400), cut_join.outputs["Geometry"],
                    translation=_combine(tree, (bx + 400, by - 600),
                                        waist_x.outputs[0], 0.0, 0.0)).outputs["Geometry"]

    body, _ = mesh_boolean_node(tree, (bx + 600, by), "DIFFERENCE",
                                plate_xf.outputs["Geometry"], waist_geo)
    return body, waist_x


def _neck(tree, gin, loc, length_sock, radius_sock, x_sock, z_sock):
    """A neck: a tapered bar from the body shoulder to the pegbox."""
    bx, by = loc
    n = _cyl(tree, (bx, by), radius_sock, length_sock, vertices=12)
    return _xf(tree, (bx + 200, by), n.outputs["Mesh"],
               rotation=(0.0, math.radians(90), 0.0),
               translation=_combine(tree, (bx, by - 140), x_sock, 0.0, z_sock)
               ).outputs["Geometry"]


def _finish(tree, gin, gout, geom, loc, bid, attrs, extra_labels=()):
    """Store the lane's attributes, apply the instrument Scale, export.

    The shared `_export_tail` in music_harps_real ignores the `Scale` group
    input entirely (it wires only Realize/Switch/Shade), so every builder in
    this module applies Scale itself with a Transform before the tail. A
    builder whose Scale dial does nothing is a dead parameter, and the gate
    asserts Scale reaches a Transform for exactly that reason.
    """
    bx, by = loc
    sc = _combine(tree, (bx - 200, by + 160), gin.outputs["Scale"],
                  gin.outputs["Scale"], gin.outputs["Scale"])
    xf = safe_node(tree, "GeometryNodeTransform", (bx, by))
    if xf is not None:
        link_sockets(tree, geom, sock(xf, "Geometry"))
        link_sockets(tree, sc.outputs["Vector"], sock(xf, "Scale"))
        geom = xf.outputs["Geometry"]
    stored = geom
    for i, (name, node) in enumerate(attrs):
        stored = _store_named(tree, (bx + 200 + i * 180, by), stored, name,
                              node if node is not None else 0.0)
    _export_tail(tree, gin, gout, stored, (bx + 200 + len(attrs) * 180 + 200, by))
    return stored


# ---------------------------------------------------------------------------
# MEL_music_cello
# ---------------------------------------------------------------------------

def build_music_cello(group_name="MEL_music_cello"):
    """Cello: 0.76 m body on the shared bowed-body law, 4 strings, endpin."""
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_cello"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 0.76, 0.4, 1.3)
    add_float_param(tree, "Body Width M", 0.44, 0.2, 0.8)
    add_float_param(tree, "Body Depth M", 0.115, 0.04, 0.3)
    add_float_param(tree, "Neck Length M", 0.58, 0.2, 1.2)
    add_int_param(tree, "String Count", 4, 2, 8)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    body, waist_x = _bowed_body(tree, gin, (bx - 1200, by), gin.outputs["Body Length M"],
                                gin.outputs["Body Depth M"], gin.outputs["Body Width M"],
                                gin.outputs["Body Depth M"])
    half_len = _math(tree, "MULTIPLY", (bx - 1500, by + 200),
                     gin.outputs["Body Length M"], 0.5)

    # f-holes: two tall thin cutters either side of the waist
    fh = safe_node(tree, "GeometryNodeMeshCube", (bx - 900, by + 400))
    fh.inputs["Size"].default_value = (0.03, 0.012, 1.0)
    fh_sc = _combine(tree, (bx - 1100, by + 400),
                     _math(tree, "MULTIPLY", (bx - 1300, by + 400),
                           gin.outputs["Body Length M"], 0.16).outputs[0],
                     gin.outputs["Body Depth M"],
                     _math(tree, "MULTIPLY", (bx - 1300, by + 260),
                           gin.outputs["Body Length M"], 0.19).outputs[0])
    fholes = []
    for sy in (-1.0, 1.0):
        holes = _xf(tree, (bx - 700, by + 400 + int(sy) * 200), fh.outputs["Mesh"],
                    scale=fh_sc,
                    translation=_combine(tree, (bx - 900, by + 260 + int(sy) * 200),
                                        _math(tree, "MULTIPLY",
                                              (bx - 1100, by + 260 + int(sy) * 200),
                                              gin.outputs["Body Length M"],
                                              0.05).outputs[0],
                                        _math(tree, "MULTIPLY",
                                              (bx - 1100, by + 120 + int(sy) * 200),
                                              gin.outputs["Body Width M"],
                                              0.17 * sy).outputs[0],
                                        0.0))
        fholes.append(holes.outputs["Geometry"])

    fjoin = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 300, by + 400))
    for f in fholes:
        link_sockets(tree, f, fjoin.inputs["Geometry"])
    cut, _ = mesh_boolean_node(tree, (bx, by), "DIFFERENCE", body,
                               fjoin.outputs["Geometry"])

    # neck + pegbox at the shoulder end
    neck_x = _math(tree, "ADD", (bx - 1300, by - 400), half_len.outputs[0],
                   _math(tree, "MULTIPLY", (bx - 1500, by - 400),
                         gin.outputs["Neck Length M"], 0.5).outputs[0])
    neck = _neck(tree, gin, (bx - 900, by - 400), gin.outputs["Neck Length M"],
                 _math(tree, "MULTIPLY", (bx - 1100, by - 400),
                       gin.outputs["Body Width M"], 0.055).outputs[0],
                 neck_x.outputs[0],
                 _math(tree, "MULTIPLY", (bx - 1100, by - 560),
                       gin.outputs["Body Depth M"], 0.5).outputs[0])
    box = safe_node(tree, "GeometryNodeMeshCube", (bx - 900, by - 700))
    box.inputs["Size"].default_value = (0.075, 0.05, 0.11)
    box_geo = _xf(tree, (bx - 700, by - 700), box.outputs["Mesh"],
                  translation=_combine(tree, (bx - 900, by - 840),
                                      _math(tree, "ADD", (bx - 1100, by - 840),
                                            neck_x.outputs[0],
                                            _math(tree, "MULTIPLY",
                                                  (bx - 1300, by - 840),
                                                  gin.outputs["Neck Length M"],
                                                  0.5).outputs[0]).outputs[0],
                                      0.0,
                                      _math(tree, "MULTIPLY",
                                            (bx - 1100, by - 1000),
                                            gin.outputs["Body Depth M"],
                                            0.5).outputs[0])).outputs["Geometry"]

    # endpin: a thin rod out of the lower bout
    pin = _cyl(tree, (bx - 900, by - 1200), 0.008,
               _math(tree, "MULTIPLY", (bx - 1100, by - 1200),
                     gin.outputs["Body Length M"], 0.22).outputs[0], vertices=8)
    pin_geo = _xf(tree, (bx - 700, by - 1200), pin.outputs["Mesh"],
                  rotation=(0.0, math.radians(90), 0.0),
                  translation=_combine(tree, (bx - 900, by - 1340),
                                      _math(tree, "MULTIPLY",
                                            (bx - 1100, by - 1340),
                                            half_len.outputs[0], -1.30).outputs[0],
                                      0.0, 0.0)).outputs["Geometry"]

    # 4 strings from the shared proto, fanned across the bridge
    proto = _ensure_string_proto(tree, "MEL_harp_string_unit", 0.62)
    spread = _math(tree, "MULTIPLY", (bx - 1100, by + 700),
                   gin.outputs["Body Width M"], 0.10)
    strings, _ = _string_rank(
        tree, (bx - 300, by + 700), gin.outputs["String Count"],
        gin.outputs["String Count"], proto,
        spread_sock=_math(tree, "DIVIDE", (bx - 500, by + 700),
                          spread.outputs[0],
                          _math(tree, "SUBTRACT", (bx - 700, by + 700),
                                gin.outputs["String Count"], 1.0).outputs[0]).outputs[0],
        x_sock=_combine(tree, (bx - 500, by + 560), neck_x.outputs[0], 0.0, 0.0),
        length_sock=_math(tree, "ADD", (bx - 500, by + 560), _math(tree, "MULTIPLY", (bx - 700, by + 560), gin.outputs["Body Length M"], 0.94).outputs[0], gin.outputs["Neck Length M"]).outputs[0])
    strings_lift = _xf(tree, (bx - 100, by + 700), strings,
                       translation=_combine(tree, (bx - 300, by + 560),
                                           0.0, 0.0,
                                           _math(tree, "MULTIPLY",
                                                 (bx - 500, by + 560),
                                                 gin.outputs["Body Depth M"],
                                                 0.62).outputs[0])
                       ).outputs["Geometry"] if strings else None

    geom = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 600, by))
    for s in (cut, neck, box_geo, pin_geo, strings_lift):
        if s is not None:
            link_sockets(tree, s, geom.inputs["Geometry"])

    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 600, by - 300))
    smod = _math(tree, "FLOORMOD", (bx + 600, by - 420), sidx.outputs["Index"], 12.0)
    _finish(tree, gin, gout, geom.outputs["Geometry"], (bx + 800, by), BID,
            [("string_semitone_mod12", smod.outputs[0]),
             ("higgsas_lead", 1.0)])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bowed Body", "nodes": ("Cylinder", "Mesh Boolean"), "role": "geometry"},
        {"title": "Neck + Pegbox", "nodes": ("Cube", "Transform"), "role": "geometry"},
        {"title": "Strings", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_viola
# ---------------------------------------------------------------------------

def build_music_viola(group_name="MEL_music_viola"):
    """Viola: the same bowed-body law at 0.42 m — the alto member of the family."""
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_viola"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 0.42, 0.25, 0.8)
    add_float_param(tree, "Body Width M", 0.25, 0.12, 0.5)
    add_float_param(tree, "Body Depth M", 0.068, 0.03, 0.2)
    add_float_param(tree, "Neck Length M", 0.34, 0.15, 0.8)
    add_int_param(tree, "String Count", 4, 2, 8)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    body, waist_x = _bowed_body(tree, gin, (bx - 1200, by),
                                gin.outputs["Body Length M"],
                                gin.outputs["Body Depth M"],
                                gin.outputs["Body Width M"],
                                gin.outputs["Body Depth M"])
    half_len = _math(tree, "MULTIPLY", (bx - 1500, by + 200),
                     gin.outputs["Body Length M"], 0.5)

    fh = safe_node(tree, "GeometryNodeMeshCube", (bx - 900, by + 400))
    fh.inputs["Size"].default_value = (0.03, 0.012, 1.0)
    fh_sc = _combine(tree, (bx - 1100, by + 400),
                     _math(tree, "MULTIPLY", (bx - 1300, by + 400),
                           gin.outputs["Body Length M"], 0.16).outputs[0],
                     gin.outputs["Body Depth M"],
                     _math(tree, "MULTIPLY", (bx - 1300, by + 260),
                           gin.outputs["Body Length M"], 0.19).outputs[0])
    fholes = []
    for sy in (-1.0, 1.0):
        holes = _xf(tree, (bx - 700, by + 400 + int(sy) * 200), fh.outputs["Mesh"],
                    scale=fh_sc,
                    translation=_combine(tree, (bx - 900, by + 260 + int(sy) * 200),
                                        _math(tree, "MULTIPLY",
                                              (bx - 1100, by + 260 + int(sy) * 200),
                                              gin.outputs["Body Length M"],
                                              0.05).outputs[0],
                                        _math(tree, "MULTIPLY",
                                              (bx - 1100, by + 120 + int(sy) * 200),
                                              gin.outputs["Body Width M"],
                                              0.17 * sy).outputs[0],
                                        0.0))
        fholes.append(holes.outputs["Geometry"])
    fjoin = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 300, by + 400))
    for f in fholes:
        link_sockets(tree, f, fjoin.inputs["Geometry"])
    cut, _ = mesh_boolean_node(tree, (bx, by), "DIFFERENCE", body,
                               fjoin.outputs["Geometry"])

    neck_x = _math(tree, "ADD", (bx - 1300, by - 400), half_len.outputs[0],
                   _math(tree, "MULTIPLY", (bx - 1500, by - 400),
                         gin.outputs["Neck Length M"], 0.5).outputs[0])
    neck = _neck(tree, gin, (bx - 900, by - 400), gin.outputs["Neck Length M"],
                 _math(tree, "MULTIPLY", (bx - 1100, by - 400),
                       gin.outputs["Body Width M"], 0.055).outputs[0],
                 neck_x.outputs[0],
                 _math(tree, "MULTIPLY", (bx - 1100, by - 560),
                       gin.outputs["Body Depth M"], 0.5).outputs[0])
    box = safe_node(tree, "GeometryNodeMeshCube", (bx - 900, by - 700))
    box.inputs["Size"].default_value = (0.055, 0.04, 0.08)
    box_geo = _xf(tree, (bx - 700, by - 700), box.outputs["Mesh"],
                  translation=_combine(tree, (bx - 900, by - 840),
                                      _math(tree, "ADD", (bx - 1100, by - 840),
                                            neck_x.outputs[0],
                                            _math(tree, "MULTIPLY",
                                                  (bx - 1300, by - 840),
                                                  gin.outputs["Neck Length M"],
                                                  0.5).outputs[0]).outputs[0],
                                      0.0,
                                      _math(tree, "MULTIPLY",
                                            (bx - 1100, by - 1000),
                                            gin.outputs["Body Depth M"],
                                            0.5).outputs[0])).outputs["Geometry"]

    proto = _ensure_string_proto(tree, "MEL_harp_string_unit", 0.34)
    spread = _math(tree, "MULTIPLY", (bx - 1100, by + 700),
                   gin.outputs["Body Width M"], 0.10)
    strings, _ = _string_rank(
        tree, (bx - 300, by + 700), gin.outputs["String Count"],
        gin.outputs["String Count"], proto,
        spread_sock=_math(tree, "DIVIDE", (bx - 500, by + 700),
                          spread.outputs[0],
                          _math(tree, "SUBTRACT", (bx - 700, by + 700),
                                gin.outputs["String Count"], 1.0).outputs[0]).outputs[0],
        x_sock=_combine(tree, (bx - 500, by + 560), neck_x.outputs[0], 0.0, 0.0),
        length_sock=_math(tree, "ADD", (bx - 500, by + 560), _math(tree, "MULTIPLY", (bx - 700, by + 560), gin.outputs["Body Length M"], 0.94).outputs[0], gin.outputs["Neck Length M"]).outputs[0])
    strings_lift = _xf(tree, (bx - 100, by + 700), strings,
                       translation=_combine(tree, (bx - 300, by + 560),
                                           0.0, 0.0,
                                           _math(tree, "MULTIPLY",
                                                 (bx - 500, by + 560),
                                                 gin.outputs["Body Depth M"],
                                                 0.62).outputs[0])
                       ).outputs["Geometry"] if strings else None

    geom = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 600, by))
    for s in (cut, neck, box_geo, strings_lift):
        if s is not None:
            link_sockets(tree, s, geom.inputs["Geometry"])

    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 600, by - 300))
    smod = _math(tree, "FLOORMOD", (bx + 600, by - 420), sidx.outputs["Index"], 12.0)
    _finish(tree, gin, gout, geom.outputs["Geometry"], (bx + 800, by), BID,
            [("string_semitone_mod12", smod.outputs[0]),
             ("higgsas_lead", 1.0)])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bowed Body", "nodes": ("Cylinder", "Mesh Boolean"), "role": "geometry"},
        {"title": "Neck + Pegbox", "nodes": ("Cube", "Transform"), "role": "geometry"},
        {"title": "Strings", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_double_bass
# ---------------------------------------------------------------------------

def build_music_double_bass(group_name="MEL_music_double_bass"):
    """Double bass: the bowed-body law at 1.10 m, sloped shoulders, tall neck."""
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_double_bass"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 1.10, 0.6, 1.8)
    add_float_param(tree, "Body Width M", 0.66, 0.3, 1.1)
    add_float_param(tree, "Body Depth M", 0.22, 0.08, 0.5)
    add_float_param(tree, "Neck Length M", 0.86, 0.4, 1.6)
    add_int_param(tree, "String Count", 4, 3, 6)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    body, waist_x = _bowed_body(tree, gin, (bx - 1200, by),
                                gin.outputs["Body Length M"],
                                gin.outputs["Body Depth M"],
                                gin.outputs["Body Width M"],
                                gin.outputs["Body Depth M"], vertices=64)
    half_len = _math(tree, "MULTIPLY", (bx - 1500, by + 200),
                     gin.outputs["Body Length M"], 0.5)

    # the bass's tall, narrow f-holes
    fh = safe_node(tree, "GeometryNodeMeshCube", (bx - 900, by + 400))
    fh.inputs["Size"].default_value = (0.03, 0.012, 1.0)
    fh_sc = _combine(tree, (bx - 1100, by + 400),
                     _math(tree, "MULTIPLY", (bx - 1300, by + 400),
                           gin.outputs["Body Length M"], 0.12).outputs[0],
                     gin.outputs["Body Depth M"],
                     _math(tree, "MULTIPLY", (bx - 1300, by + 260),
                           gin.outputs["Body Length M"], 0.22).outputs[0])
    fholes = []
    for sy in (-1.0, 1.0):
        holes = _xf(tree, (bx - 700, by + 400 + int(sy) * 200), fh.outputs["Mesh"],
                    scale=fh_sc,
                    translation=_combine(tree, (bx - 900, by + 260 + int(sy) * 200),
                                        _math(tree, "MULTIPLY",
                                              (bx - 1100, by + 260 + int(sy) * 200),
                                              gin.outputs["Body Length M"],
                                              0.04).outputs[0],
                                        _math(tree, "MULTIPLY",
                                              (bx - 1100, by + 120 + int(sy) * 200),
                                              gin.outputs["Body Width M"],
                                              0.18 * sy).outputs[0],
                                        0.0))
        fholes.append(holes.outputs["Geometry"])
    fjoin = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 300, by + 400))
    for f in fholes:
        link_sockets(tree, f, fjoin.inputs["Geometry"])
    cut, _ = mesh_boolean_node(tree, (bx, by), "DIFFERENCE", body,
                               fjoin.outputs["Geometry"])

    neck_x = _math(tree, "ADD", (bx - 1300, by - 400), half_len.outputs[0],
                   _math(tree, "MULTIPLY", (bx - 1500, by - 400),
                         gin.outputs["Neck Length M"], 0.5).outputs[0])
    neck = _neck(tree, gin, (bx - 900, by - 400), gin.outputs["Neck Length M"],
                 _math(tree, "MULTIPLY", (bx - 1100, by - 400),
                       gin.outputs["Body Width M"], 0.045).outputs[0],
                 neck_x.outputs[0],
                 _math(tree, "MULTIPLY", (bx - 1100, by - 560),
                       gin.outputs["Body Depth M"], 0.5).outputs[0])
    # scroll + pegbox: the bass's characteristic heavy head
    box = safe_node(tree, "GeometryNodeMeshCube", (bx - 900, by - 700))
    box.inputs["Size"].default_value = (0.16, 0.09, 0.24)
    box_geo = _xf(tree, (bx - 700, by - 700), box.outputs["Mesh"],
                  translation=_combine(tree, (bx - 900, by - 840),
                                      _math(tree, "ADD", (bx - 1100, by - 840),
                                            neck_x.outputs[0],
                                            _math(tree, "MULTIPLY",
                                                  (bx - 1300, by - 840),
                                                  gin.outputs["Neck Length M"],
                                                  0.5).outputs[0]).outputs[0],
                                      0.0,
                                      _math(tree, "MULTIPLY",
                                            (bx - 1100, by - 1000),
                                            gin.outputs["Body Depth M"],
                                            0.5).outputs[0])).outputs["Geometry"]
    scroll = _cyl(tree, (bx - 900, by - 1200), 0.045,
                  _math(tree, "MULTIPLY", (bx - 1100, by - 1200),
                        gin.outputs["Body Width M"], 0.12).outputs[0], vertices=16)
    scroll_geo = _xf(tree, (bx - 700, by - 1200), scroll.outputs["Mesh"],
                     rotation=(0.0, math.radians(90), 0.0),
                     translation=_combine(tree, (bx - 900, by - 1340),
                                         _math(tree, "ADD", (bx - 1100, by - 1340),
                                               neck_x.outputs[0],
                                               _math(tree, "MULTIPLY",
                                                     (bx - 1300, by - 1340),
                                                     gin.outputs["Neck Length M"],
                                                     0.5).outputs[0]).outputs[0],
                                         0.0, 0.0)).outputs["Geometry"]

    # endpin
    pin = _cyl(tree, (bx - 900, by - 1600), 0.011,
               _math(tree, "MULTIPLY", (bx - 1100, by - 1600),
                     gin.outputs["Body Length M"], 0.30).outputs[0], vertices=8)
    pin_geo = _xf(tree, (bx - 700, by - 1600), pin.outputs["Mesh"],
                  rotation=(0.0, math.radians(90), 0.0),
                  translation=_combine(tree, (bx - 900, by - 1740),
                                      _math(tree, "MULTIPLY",
                                            (bx - 1100, by - 1740),
                                            half_len.outputs[0], -1.28).outputs[0],
                                      0.0, 0.0)).outputs["Geometry"]

    proto = _ensure_string_proto(tree, "MEL_harp_string_unit", 0.90)
    spread = _math(tree, "MULTIPLY", (bx - 1100, by + 700),
                   gin.outputs["Body Width M"], 0.09)
    strings, _ = _string_rank(
        tree, (bx - 300, by + 700), gin.outputs["String Count"],
        gin.outputs["String Count"], proto,
        spread_sock=_math(tree, "DIVIDE", (bx - 500, by + 700),
                          spread.outputs[0],
                          _math(tree, "SUBTRACT", (bx - 700, by + 700),
                                gin.outputs["String Count"], 1.0).outputs[0]).outputs[0],
        x_sock=_combine(tree, (bx - 500, by + 560), neck_x.outputs[0], 0.0, 0.0),
        length_sock=_math(tree, "ADD", (bx - 500, by + 560), _math(tree, "MULTIPLY", (bx - 700, by + 560), gin.outputs["Body Length M"], 0.94).outputs[0], gin.outputs["Neck Length M"]).outputs[0])
    strings_lift = _xf(tree, (bx - 100, by + 700), strings,
                       translation=_combine(tree, (bx - 300, by + 560),
                                           0.0, 0.0,
                                           _math(tree, "MULTIPLY",
                                                 (bx - 500, by + 560),
                                                 gin.outputs["Body Depth M"],
                                                 0.62).outputs[0])
                       ).outputs["Geometry"] if strings else None

    geom = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 600, by))
    for s in (cut, neck, box_geo, scroll_geo, pin_geo, strings_lift):
        if s is not None:
            link_sockets(tree, s, geom.inputs["Geometry"])

    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 600, by - 300))
    smod = _math(tree, "FLOORMOD", (bx + 600, by - 420), sidx.outputs["Index"], 12.0)
    _finish(tree, gin, gout, geom.outputs["Geometry"], (bx + 800, by), BID,
            [("string_semitone_mod12", smod.outputs[0]),
             ("higgsas_lead", 1.0)])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bowed Body", "nodes": ("Cylinder", "Mesh Boolean"), "role": "geometry"},
        {"title": "Neck + Head", "nodes": ("Cube", "Transform"), "role": "geometry"},
        {"title": "Strings", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_banjo
# ---------------------------------------------------------------------------

def build_music_banjo(group_name="MEL_music_banjo"):
    """Banjo: round drum head, tension hoop, 5 strings, resonator bowl."""
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_banjo"
    bx, by = 0, 0

    add_float_param(tree, "Head Diameter M", 0.28, 0.15, 0.5)
    add_float_param(tree, "Rim Depth M", 0.09, 0.03, 0.2)
    add_float_param(tree, "Neck Length M", 0.52, 0.2, 1.0)
    add_int_param(tree, "String Count", 5, 4, 6)
    add_int_param(tree, "Bracket Count", 24, 8, 40)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    R = _math(tree, "MULTIPLY", (bx - 900, by + 200),
              gin.outputs["Head Diameter M"], 0.5)

    # rim: an open cylinder (the drum shell)
    rim = _cyl(tree, (bx - 700, by), R.outputs[0],
               gin.outputs["Rim Depth M"], vertices=64, fill=1)

    # head: a shallow disc across the top of the rim
    head = _cyl(tree, (bx - 700, by - 300), R.outputs[0],
                _math(tree, "MULTIPLY", (bx - 900, by - 300),
                      gin.outputs["Head Diameter M"], 0.012).outputs[0],
                vertices=64, fill=2)
    head_geo = _xf(tree, (bx - 500, by - 300), head.outputs["Mesh"],
                   translation=_combine(tree, (bx - 700, by - 440),
                                       0.0, 0.0,
                                       _math(tree, "MULTIPLY",
                                             (bx - 900, by - 440),
                                             gin.outputs["Rim Depth M"],
                                             0.5).outputs[0])).outputs["Geometry"]

    # tension hoop + a rank of brackets around the rim
    hoop = _cyl(tree, (bx - 700, by + 400),
                _math(tree, "MULTIPLY", (bx - 900, by + 400), R.outputs[0], 1.06).outputs[0],
                _math(tree, "MULTIPLY", (bx - 900, by + 260),
                      gin.outputs["Rim Depth M"], 0.16).outputs[0],
                vertices=64, fill=1)
    hoop_geo = _xf(tree, (bx - 500, by + 400), hoop.outputs["Mesh"],
                   translation=_combine(tree, (bx - 700, by + 260),
                                       0.0, 0.0,
                                       _math(tree, "MULTIPLY",
                                             (bx - 900, by + 260),
                                             gin.outputs["Rim Depth M"],
                                             0.56).outputs[0])).outputs["Geometry"]

    brk = _cyl(tree, (bx - 300, by - 700), 0.005,
               _math(tree, "MULTIPLY", (bx - 500, by - 700),
                     gin.outputs["Rim Depth M"], 0.85).outputs[0], vertices=6)
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 500, by - 700))
    link_sockets(tree, gin.outputs["Bracket Count"], sock(line, "Count"))
    spacing = _math(tree, "DIVIDE", (bx - 700, by - 700),
                    _math(tree, "MULTIPLY", (bx - 900, by - 700),
                          R.outputs[0], 6.2831853).outputs[0],
                    gin.outputs["Bracket Count"])
    link_sockets(tree, _combine(tree, (bx - 900, by - 840),
                                spacing.outputs[0], 0.0, 0.0).outputs["Vector"],
                 sock(line, "Offset"))
    bpts = safe_node(tree, "GeometryNodeMeshToPoints", (bx - 300, by - 700))
    if bpts is not None:
        link_sockets(tree, line.outputs["Mesh"], sock(bpts, "Mesh") or bpts.inputs[0])
    # place the rank points on the rim circle, not on a straight line
    bidx = safe_node(tree, "GeometryNodeInputIndex", (bx - 100, by - 1000))
    bang = _math(tree, "DIVIDE", (bx - 100, by - 1140),
                 _math(tree, "MULTIPLY", (bx - 300, by - 1140),
                       bidx.outputs["Index"], 6.2831853).outputs[0],
                 gin.outputs["Bracket Count"])
    bcirc = safe_node(tree, "GeometryNodeSetPosition", (bx + 100, by - 700))
    if bcirc is not None:
        link_sockets(tree, bpts.outputs["Points"] if bpts is not None else None,
                     sock(bcirc, "Geometry"))
        link_sockets(tree, _combine(tree, (bx - 100, by - 1140),
                                    _math(tree, "MULTIPLY",
                                          (bx - 300, by - 1000),
                                          R.outputs[0],
                                          _math(tree, "COSINE",
                                                (bx - 500, by - 1000),
                                                bang.outputs[0]).outputs[0]).outputs[0],
                                    _math(tree, "MULTIPLY",
                                          (bx - 300, by - 860),
                                          R.outputs[0],
                                          _math(tree, "SINE",
                                                (bx - 500, by - 860),
                                                bang.outputs[0]).outputs[0]).outputs[0],
                                    0.0).outputs["Vector"],
                     sock(bcirc, "Offset"))
    binst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 300, by - 700))
    if binst is not None:
        link_sockets(tree, bcirc.outputs["Geometry"] if bcirc is not None else None,
                     sock(binst, "Points"))
        link_sockets(tree, brk.outputs["Mesh"], sock(binst, "Instance"))

    # neck: a bar out of the rim, angled up to the peghead
    neck_x = _math(tree, "ADD", (bx - 900, by - 1400), R.outputs[0],
                   _math(tree, "MULTIPLY", (bx - 1100, by - 1400),
                         gin.outputs["Neck Length M"], 0.5).outputs[0])
    neck = _cyl(tree, (bx - 700, by - 1400), 0.014,
                gin.outputs["Neck Length M"], vertices=12)
    neck_geo = _xf(tree, (bx - 500, by - 1400), neck.outputs["Mesh"],
                   rotation=(0.0, math.radians(90), 0.0),
                   translation=_combine(tree, (bx - 700, by - 1540),
                                       neck_x.outputs[0], 0.0,
                                       _math(tree, "MULTIPLY",
                                             (bx - 900, by - 1540),
                                             gin.outputs["Rim Depth M"],
                                             0.55).outputs[0])).outputs["Geometry"]
    peghead = safe_node(tree, "GeometryNodeMeshCube", (bx - 700, by - 1700))
    peghead.inputs["Size"].default_value = (0.10, 0.035, 0.06)
    peg_geo = _xf(tree, (bx - 500, by - 1700), peghead.outputs["Mesh"],
                  translation=_combine(tree, (bx - 700, by - 1840),
                                      _math(tree, "ADD", (bx - 900, by - 1840),
                                            neck_x.outputs[0],
                                            _math(tree, "MULTIPLY",
                                                  (bx - 1100, by - 1840),
                                                  gin.outputs["Neck Length M"],
                                                  0.5).outputs[0]).outputs[0],
                                      0.0,
                                      _math(tree, "MULTIPLY",
                                            (bx - 900, by - 2000),
                                            gin.outputs["Rim Depth M"],
                                            0.55).outputs[0])).outputs["Geometry"]

    # resonator: a shallow bowl under the rim
    res = _cyl(tree, (bx - 700, by + 700), R.outputs[0],
               _math(tree, "MULTIPLY", (bx - 900, by + 700),
                     gin.outputs["Rim Depth M"], 0.75).outputs[0],
               vertices=48, fill=2)
    res_geo = _xf(tree, (bx - 500, by + 700), res.outputs["Mesh"],
                  translation=_combine(tree, (bx - 700, by + 560),
                                      0.0, 0.0,
                                      _math(tree, "MULTIPLY",
                                            (bx - 900, by + 560),
                                            gin.outputs["Rim Depth M"],
                                            -0.85).outputs[0])).outputs["Geometry"]

    proto = _ensure_string_proto(tree, "MEL_harp_string_unit", 0.55)
    spread = _math(tree, "MULTIPLY", (bx - 900, by + 900),
                   gin.outputs["Head Diameter M"], 0.16)
    strings, _ = _string_rank(
        tree, (bx - 100, by + 900), gin.outputs["String Count"],
        gin.outputs["String Count"], proto,
        spread_sock=_math(tree, "DIVIDE", (bx - 300, by + 900),
                          spread.outputs[0],
                          _math(tree, "SUBTRACT", (bx - 500, by + 900),
                                gin.outputs["String Count"], 1.0).outputs[0]).outputs[0],
        x_sock=_combine(tree, (bx - 300, by + 760), neck_x.outputs[0], 0.0, 0.0),
        length_sock=_math(tree, "ADD", (bx - 300, by + 760), _math(tree, "MULTIPLY", (bx - 500, by + 760), gin.outputs["Head Diameter M"], 0.5).outputs[0], gin.outputs["Neck Length M"]).outputs[0])
    strings_lift = _xf(tree, (bx + 100, by + 900), strings,
                       translation=_combine(tree, (bx - 100, by + 760),
                                           0.0, 0.0,
                                           _math(tree, "MULTIPLY",
                                                 (bx - 300, by + 760),
                                                 gin.outputs["Rim Depth M"],
                                                 0.85).outputs[0])
                       ).outputs["Geometry"] if strings else None

    geom = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 600, by))
    for s in (rim.outputs["Mesh"], head_geo, hoop_geo,
              binst.outputs["Instances"] if binst is not None else None,
              neck_geo, peg_geo, res_geo, strings_lift):
        if s is not None:
            link_sockets(tree, s, geom.inputs["Geometry"])

    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 600, by - 300))
    smod = _math(tree, "FLOORMOD", (bx + 600, by - 420), sidx.outputs["Index"], 12.0)
    _finish(tree, gin, gout, geom.outputs["Geometry"], (bx + 800, by), BID,
            [("string_semitone_mod12", smod.outputs[0]),
             ("higgsas_lead", 1.0)])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Drum + Head", "nodes": ("Cylinder", "Transform"), "role": "geometry"},
        {"title": "Hoop + Brackets", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Neck + Resonator", "nodes": ("Cube",), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_mandolin
# ---------------------------------------------------------------------------

def build_music_mandolin(group_name="MEL_music_mandolin"):
    """Mandolin: pear body, 8 strings in 4 courses, scroll head, f-holes."""
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_mandolin"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 0.33, 0.2, 0.55)
    add_float_param(tree, "Body Width M", 0.25, 0.15, 0.4)
    add_float_param(tree, "Body Depth M", 0.06, 0.025, 0.15)
    add_float_param(tree, "Neck Length M", 0.24, 0.1, 0.5)
    add_int_param(tree, "Course Count", 4, 2, 6)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    body, waist_x = _bowed_body(tree, gin, (bx - 1200, by),
                                gin.outputs["Body Length M"],
                                gin.outputs["Body Depth M"],
                                gin.outputs["Body Width M"],
                                gin.outputs["Body Depth M"])
    half_len = _math(tree, "MULTIPLY", (bx - 1500, by + 200),
                     gin.outputs["Body Length M"], 0.5)

    # f-holes
    fh = safe_node(tree, "GeometryNodeMeshCube", (bx - 900, by + 400))
    fh.inputs["Size"].default_value = (0.03, 0.012, 1.0)
    fh_sc = _combine(tree, (bx - 1100, by + 400),
                     _math(tree, "MULTIPLY", (bx - 1300, by + 400),
                           gin.outputs["Body Length M"], 0.13).outputs[0],
                     gin.outputs["Body Depth M"],
                     _math(tree, "MULTIPLY", (bx - 1300, by + 260),
                           gin.outputs["Body Length M"], 0.16).outputs[0])
    fholes = []
    for sy in (-1.0, 1.0):
        holes = _xf(tree, (bx - 700, by + 400 + int(sy) * 200), fh.outputs["Mesh"],
                    scale=fh_sc,
                    translation=_combine(tree, (bx - 900, by + 260 + int(sy) * 200),
                                        _math(tree, "MULTIPLY",
                                              (bx - 1100, by + 260 + int(sy) * 200),
                                              gin.outputs["Body Length M"],
                                              0.04).outputs[0],
                                        _math(tree, "MULTIPLY",
                                              (bx - 1100, by + 120 + int(sy) * 200),
                                              gin.outputs["Body Width M"],
                                              0.18 * sy).outputs[0],
                                        0.0))
        fholes.append(holes.outputs["Geometry"])
    fjoin = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 300, by + 400))
    for f in fholes:
        link_sockets(tree, f, fjoin.inputs["Geometry"])
    cut, _ = mesh_boolean_node(tree, (bx, by), "DIFFERENCE", body,
                               fjoin.outputs["Geometry"])

    neck_x = _math(tree, "ADD", (bx - 1300, by - 400), half_len.outputs[0],
                   _math(tree, "MULTIPLY", (bx - 1500, by - 400),
                         gin.outputs["Neck Length M"], 0.5).outputs[0])
    neck = _neck(tree, gin, (bx - 900, by - 400), gin.outputs["Neck Length M"],
                 _math(tree, "MULTIPLY", (bx - 1100, by - 400),
                       gin.outputs["Body Width M"], 0.05).outputs[0],
                 neck_x.outputs[0],
                 _math(tree, "MULTIPLY", (bx - 1100, by - 560),
                       gin.outputs["Body Depth M"], 0.5).outputs[0])
    # scroll head: the mandolin's signature curl
    scroll = _cyl(tree, (bx - 900, by - 700), 0.035,
                  _math(tree, "MULTIPLY", (bx - 1100, by - 700),
                        gin.outputs["Body Width M"], 0.10).outputs[0], vertices=16)
    scroll_geo = _xf(tree, (bx - 700, by - 700), scroll.outputs["Mesh"],
                     rotation=(0.0, math.radians(90), 0.0),
                     translation=_combine(tree, (bx - 900, by - 840),
                                         _math(tree, "ADD", (bx - 1100, by - 840),
                                               neck_x.outputs[0],
                                               _math(tree, "MULTIPLY",
                                                     (bx - 1300, by - 840),
                                                     gin.outputs["Neck Length M"],
                                                     0.5).outputs[0]).outputs[0],
                                         0.0, 0.0)).outputs["Geometry"]

    # 8 strings in 4 COURSES: two strings per course, courses fanned
    proto = _ensure_string_proto(tree, "MEL_harp_string_unit", 0.26)
    course_sock = _math(tree, "MULTIPLY", (bx - 1100, by + 900),
                        gin.outputs["Course Count"], 2.0)
    spread = _math(tree, "MULTIPLY", (bx - 1100, by + 1040),
                   gin.outputs["Body Width M"], 0.20)
    strings, _ = _string_rank(
        tree, (bx - 300, by + 900), course_sock, course_sock, proto,
        spread_sock=_math(tree, "DIVIDE", (bx - 500, by + 900),
                          spread.outputs[0],
                          _math(tree, "SUBTRACT", (bx - 700, by + 900),
                                course_sock, 1.0).outputs[0]).outputs[0],
        x_sock=_combine(tree, (bx - 500, by + 760), neck_x.outputs[0], 0.0, 0.0),
        length_sock=_math(tree, "ADD", (bx - 500, by + 760), _math(tree, "MULTIPLY", (bx - 700, by + 760), gin.outputs["Body Length M"], 0.94).outputs[0], gin.outputs["Neck Length M"]).outputs[0])
    strings_lift = _xf(tree, (bx - 100, by + 900), strings,
                       translation=_combine(tree, (bx - 300, by + 760),
                                           0.0, 0.0,
                                           _math(tree, "MULTIPLY",
                                                 (bx - 500, by + 760),
                                                 gin.outputs["Body Depth M"],
                                                 0.62).outputs[0])
                       ).outputs["Geometry"] if strings else None

    geom = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 600, by))
    for s in (cut, neck, scroll_geo, strings_lift):
        if s is not None:
            link_sockets(tree, s, geom.inputs["Geometry"])

    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 600, by - 300))
    smod = _math(tree, "FLOORMOD", (bx + 600, by - 420), sidx.outputs["Index"], 12.0)
    _finish(tree, gin, gout, geom.outputs["Geometry"], (bx + 800, by), BID,
            [("course_semitone_mod12", smod.outputs[0]),
             ("higgsas_lead", 1.0)])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Pear Body", "nodes": ("Cylinder", "Mesh Boolean"), "role": "geometry"},
        {"title": "Neck + Scroll", "nodes": ("Cube", "Transform"), "role": "geometry"},
        {"title": "Courses", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_ukulele
# ---------------------------------------------------------------------------

def build_music_ukulele(group_name="MEL_music_ukulele"):
    """Ukulele: small body on the bowed-body law, 4 strings, pin bridge."""
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_ukulele"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 0.24, 0.15, 0.4)
    add_float_param(tree, "Body Width M", 0.17, 0.1, 0.3)
    add_float_param(tree, "Body Depth M", 0.055, 0.02, 0.12)
    add_float_param(tree, "Neck Length M", 0.19, 0.08, 0.4)
    add_int_param(tree, "String Count", 4, 3, 6)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    body, waist_x = _bowed_body(tree, gin, (bx - 1200, by),
                                gin.outputs["Body Length M"],
                                gin.outputs["Body Depth M"],
                                gin.outputs["Body Width M"],
                                gin.outputs["Body Depth M"], vertices=40)
    half_len = _math(tree, "MULTIPLY", (bx - 1500, by + 200),
                     gin.outputs["Body Length M"], 0.5)

    # soundhole: one round hole under the strings
    hole = _cyl(tree, (bx - 900, by + 400),
                _math(tree, "MULTIPLY", (bx - 1100, by + 400),
                      gin.outputs["Body Width M"], 0.16).outputs[0],
                _math(tree, "MULTIPLY", (bx - 1100, by + 260),
                      gin.outputs["Body Depth M"], 3.0).outputs[0],
                vertices=32, fill=2)
    hole_geo = _xf(tree, (bx - 700, by + 400), hole.outputs["Mesh"],
                   translation=_combine(tree, (bx - 900, by + 260),
                                       _math(tree, "MULTIPLY",
                                             (bx - 1100, by + 260),
                                             gin.outputs["Body Length M"],
                                             0.06).outputs[0],
                                       0.0, 0.0)).outputs["Geometry"]
    cut, _ = mesh_boolean_node(tree, (bx, by), "DIFFERENCE", body, hole_geo)

    neck_x = _math(tree, "ADD", (bx - 1300, by - 400), half_len.outputs[0],
                   _math(tree, "MULTIPLY", (bx - 1500, by - 400),
                         gin.outputs["Neck Length M"], 0.5).outputs[0])
    neck = _neck(tree, gin, (bx - 900, by - 400), gin.outputs["Neck Length M"],
                 _math(tree, "MULTIPLY", (bx - 1100, by - 400),
                       gin.outputs["Body Width M"], 0.055).outputs[0],
                 neck_x.outputs[0],
                 _math(tree, "MULTIPLY", (bx - 1100, by - 560),
                       gin.outputs["Body Depth M"], 0.5).outputs[0])
    head = safe_node(tree, "GeometryNodeMeshCube", (bx - 900, by - 700))
    head.inputs["Size"].default_value = (0.055, 0.032, 0.05)
    head_geo = _xf(tree, (bx - 700, by - 700), head.outputs["Mesh"],
                   translation=_combine(tree, (bx - 900, by - 840),
                                       _math(tree, "ADD", (bx - 1100, by - 840),
                                             neck_x.outputs[0],
                                             _math(tree, "MULTIPLY",
                                                   (bx - 1300, by - 840),
                                                   gin.outputs["Neck Length M"],
                                                   0.5).outputs[0]).outputs[0],
                                       0.0,
                                       _math(tree, "MULTIPLY",
                                             (bx - 1100, by - 1000),
                                             gin.outputs["Body Depth M"],
                                             0.5).outputs[0])).outputs["Geometry"]

    # pin bridge: a small block with four pin bumps at the lower bout
    bridge = safe_node(tree, "GeometryNodeMeshCube", (bx - 900, by + 700))
    bridge.inputs["Size"].default_value = (0.018, 1.0, 0.012)
    bridge_sc = _combine(tree, (bx - 1100, by + 700),
                         gin.outputs["Body Depth M"],
                         _math(tree, "MULTIPLY", (bx - 1100, by + 560),
                               gin.outputs["Body Width M"], 0.55).outputs[0],
                         1.0)
    bridge_geo = _xf(tree, (bx - 700, by + 700), bridge.outputs["Mesh"],
                     scale=bridge_sc,
                     translation=_combine(tree, (bx - 900, by + 560),
                                         _math(tree, "MULTIPLY",
                                               (bx - 1100, by + 560),
                                               gin.outputs["Body Length M"],
                                               0.34).outputs[0],
                                         0.0,
                                         _math(tree, "MULTIPLY",
                                               (bx - 1100, by + 420),
                                               gin.outputs["Body Depth M"],
                                               0.62).outputs[0])).outputs["Geometry"]

    proto = _ensure_string_proto(tree, "MEL_harp_string_unit", 0.20)
    spread = _math(tree, "MULTIPLY", (bx - 1100, by + 900),
                   gin.outputs["Body Width M"], 0.16)
    strings, _ = _string_rank(
        tree, (bx - 300, by + 900), gin.outputs["String Count"],
        gin.outputs["String Count"], proto,
        spread_sock=_math(tree, "DIVIDE", (bx - 500, by + 900),
                          spread.outputs[0],
                          _math(tree, "SUBTRACT", (bx - 700, by + 900),
                                gin.outputs["String Count"], 1.0).outputs[0]).outputs[0],
        x_sock=_combine(tree, (bx - 500, by + 760), neck_x.outputs[0], 0.0, 0.0),
        length_sock=_math(tree, "ADD", (bx - 500, by + 760), _math(tree, "MULTIPLY", (bx - 700, by + 760), gin.outputs["Body Length M"], 0.94).outputs[0], gin.outputs["Neck Length M"]).outputs[0])
    strings_lift = _xf(tree, (bx - 100, by + 900), strings,
                       translation=_combine(tree, (bx - 300, by + 760),
                                           0.0, 0.0,
                                           _math(tree, "MULTIPLY",
                                                 (bx - 500, by + 760),
                                                 gin.outputs["Body Depth M"],
                                                 0.62).outputs[0])
                       ).outputs["Geometry"] if strings else None

    geom = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 600, by))
    for s in (cut, neck, head_geo, bridge_geo, strings_lift):
        if s is not None:
            link_sockets(tree, s, geom.inputs["Geometry"])

    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 600, by - 300))
    smod = _math(tree, "FLOORMOD", (bx + 600, by - 420), sidx.outputs["Index"], 12.0)
    _finish(tree, gin, gout, geom.outputs["Geometry"], (bx + 800, by), BID,
            [("string_semitone_mod12", smod.outputs[0]),
             ("higgsas_lead", 1.0)])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Body", "nodes": ("Cylinder", "Mesh Boolean"), "role": "geometry"},
        {"title": "Neck + Head", "nodes": ("Cube", "Transform"), "role": "geometry"},
        {"title": "Strings", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

register_builder(
    "MEL_music_cello", build_music_cello, "Cello",
    "Cello: 0.76 m body on the shared bowed-body law, f-holes, neck, pegbox, "
    "endpin, 4 strings from the shared harp string proto. Native-only.",
    "music",
)
register_builder(
    "MEL_music_viola", build_music_viola, "Viola",
    "Viola: the bowed-body law at 0.42 m — the alto member of the violin "
    "family. Native-only.",
    "music",
)
register_builder(
    "MEL_music_double_bass", build_music_double_bass, "Double Bass",
    "Double bass: the bowed-body law at 1.10 m with sloped shoulders, heavy "
    "scroll head, endpin and 4 strings. Native-only.",
    "music",
)
register_builder(
    "MEL_music_banjo", build_music_banjo, "Banjo",
    "Banjo: round drum head, tension hoop with a bracketed rank, resonator "
    "bowl, 5 strings. Native-only.",
    "music",
)
register_builder(
    "MEL_music_mandolin", build_music_mandolin, "Mandolin",
    "Mandolin: pear body, scroll head, f-holes, and 8 strings in 4 courses. "
    "Native-only.",
    "music",
)
register_builder(
    "MEL_music_ukulele", build_music_ukulele, "Ukulele",
    "Ukulele: small body on the bowed-body law, round soundhole, pin bridge, "
    "4 strings. Native-only.",
    "music",
)
