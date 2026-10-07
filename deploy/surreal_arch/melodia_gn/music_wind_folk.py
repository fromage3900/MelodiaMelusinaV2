"""P4 wave 7 — Chinese & Andean folk wind lane: dizi, xiao, bawu, hulusi,
suona, sheng.

Gap audit first (repo-wide grep over `deploy/surreal_arch/` + the live registry +
`Tools/registry_baseline.json`, 2026-10-03): the wind lane owns saxophone,
bandoneon, glass harmonica, theremin, siku, flute, clarinet, recorder, melodica,
oboe, bassoon, trumpet, tuba, accordion, bagpipes. NONE of the six ids below
existed anywhere (grep count 0 each):

    dizi, xiao, bawu, hulusi, suona, sheng

Nothing here re-implements an existing id. Each of the six is distinct from the
closest existing neighbour by its OWN anatomy, not by a parameter:

    MEL_music_dizi    vs MEL_music_flute    bamboo NODE collars along the tube +
                                            a membrane hole (dimokong) rim; the
                                            western flute is smooth metal with
                                            a lip plate and a foot joint
    MEL_music_xiao    vs MEL_music_recorder END-blown and VERTICAL (Z-laid) with
                                            a notched top; the recorder is
                                            horizontal with a fipple block
    MEL_music_bawu    vs MEL_music_clarinet a free REED WINDOW near the blow end
                                            (rails + tongue), not a mouthpiece
                                            with a cane reed
    MEL_music_hulusi  vs MEL_music_bagpipes a GOURD wind chest + 3 drones + 1
                                            melody pipe with finger holes; the
                                            bagpipes are a leather bag with a
                                            chanter and a blowpipe
    MEL_music_suona   vs MEL_music_trumpet  a CONICAL wooden body under a flared
                                            METAL bell + a small double reed on
                                            a staple; the trumpet is cylindrical
                                            brass with piston valves
    MEL_music_sheng   vs MEL_music_baroque_organ  a BOWL of 17 graduated bamboo
                                            pipes with reed windows; the organ
                                            is a rank of pipes on a chest

Design rules (same as music_string_kit / music_percussion_kit /
music_world_strings / music_wind_reed_brass):
  - Native-only. These are bamboo tubes, gourd chests, cones and reed plates that
    5.2 primitives express exactly; a Higgsas subtree here would be decoration,
    not a lead. Every builder still stores `higgsas_lead` (1.0 = native) so the
    family gate and the instruments gate read the lane uniformly.
  - The wave-6 origin-explicit helpers are REUSED, never re-authored: `_cone_x` /
    `_cone_z` take the BASE (`MeshCone`'s origin is its base, spans z [0, depth]),
    `_cyl_x` / `_cyl_z` take the CENTRE (`MeshCylinder` spans z [-d/2, d/2]),
    `_cone_proto_z` / `_cyl_proto_z` return protos whose origin is their own
    bottom so `_stand`'s per-instance graduation happens about the base.
  - Placement is applied ONCE, in the rank's own points. `_rank_inst` places a
    rank ONLY by its points; there is no second translate to double with.
  - A rank's Start/Offset are always CombineXYZ (a bare float on MeshLine.Offset
    broadcasts to (v, v, v) and silently puts the rank on the wrong axis).
  - Hole detail is a RIM RING laid on the body, never a boolean: measured
    2026-10-03 on the balalaika, a MeshBoolean whose cutter touches the mesh's
    own boundary emits ZERO geometry with no error and no link_failures entry.
    The gate asserts zero MeshBoolean in the lane.
  - A rank is CENTRED (`-span/2` start) so it sits over its host instead of
    running off the +X half.

Builders:
    MEL_music_dizi    bamboo tube + node collars + membrane rim + 6 finger rims
    MEL_music_xiao    vertical bamboo tube + notched top + 5 finger rims
    MEL_music_bawu    tube + free-reed window (rails + tongue) + 6 finger rims
    MEL_music_hulusi  gourd chest + 3 graduated drones + melody pipe + blow pipe
    MEL_music_suona   conical body + metal bell + staple reed + 8 finger rims
    MEL_music_sheng   wind chest bowl + two rows of graduated reed-window pipes
"""

from __future__ import annotations

import math

from .core import (
    safe_node, link_sockets, label_tree, new_geometry_tree, add_float_param,
    add_int_param, add_bool_param, register_builder, sock,
)
from .music_harps_real import _math, _combine
from .music_higgsas_instruments import (
    _store_named, _cone, _cyl, _line, _xf, _set_fill,
)
from .music_string_kit import _finish
from .music_wind_reed_brass import (
    _vec, _sphere, _cone_x, _cyl_x, _cone_z, _cyl_z, _cone_proto_z,
    _cyl_proto_z, _join, _rank_inst, _stand, _half_span, _attrs,
)


# ---------------------------------------------------------------------------
# Lane-local rim law — a hole is a collar laid ON the body, never a cut
# ---------------------------------------------------------------------------

def _rims_x(tree, loc, count_sock, span_sock, first, z_off, r_rim, depth,
            verts=12, step_sign=1.0):
    """A rank of rim collars standing on the +Z face of an X-laid tube.

    The proto is a Z-laid collar centred on its own origin, so the rank places
    each instance at (x_i, 0, z_off) and it straddles the tube surface — the
    same idiom as wave 6's oboe key cups, and the reason no boolean is needed.
    `step_sign` is -1 when the rank must run toward -X from `first` (the dizi's
    finger holes sit BELOW its membrane, not above it).
    """
    bx, by = loc
    proto = _cyl_z(tree, (bx, by), r_rim, depth, 0.0, verts=verts)
    return _rank_inst(tree, (bx + 400, by), count_sock, proto, span_sock,
                      first, axis="x", step_sign=step_sign, z=z_off)


def _rims_z(tree, loc, count_sock, span_sock, first, y_off, r_rim, depth,
            verts=12, step_sign=1.0):
    """A rank of rim collars on the -Y face of a Z-laid tube."""
    bx, by = loc
    proto = _cyl_z(tree, (bx, by), r_rim, depth, 0.0, verts=verts)
    return _rank_inst(tree, (bx + 400, by), count_sock, proto, span_sock,
                      first, axis="z", step_sign=step_sign, y=y_off)


# ---------------------------------------------------------------------------
# MEL_music_dizi
# ---------------------------------------------------------------------------

def build_music_dizi(group_name="MEL_music_dizi"):
    """Dizi: bamboo tube, node collars, membrane hole (dimokong), 6 finger rims.

    Horizontal (+X). The bamboo NODE collars and the membrane hole are the two
    features that make this a dizi and not a flute; the finger holes are rim
    rings laid on the top face.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_dizi"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 0.65, 0.30, 1.10)
    add_float_param(tree, "Body Radius M", 0.008, 0.004, 0.020)
    add_int_param(tree, "Node Count", 5, 2, 12)
    add_int_param(tree, "Hole Count", 6, 3, 10)
    add_float_param(tree, "Hole Radius M", 0.0035, 0.0015, 0.008)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Body Length M"]
    R = gin.outputs["Body Radius M"]
    HR = gin.outputs["Hole Radius M"]

    ring_len = _math(tree, "MULTIPLY", (bx - 2000, by - 200), L, 0.012)
    node_span = _math(tree, "MULTIPLY", (bx - 2000, by - 340), L, 0.86)
    hole_span = _math(tree, "MULTIPLY", (bx - 2000, by - 480), L, 0.42)
    cap_len = _math(tree, "MULTIPLY", (bx - 2000, by - 620), L, 0.022)

    # bore: a cylinder along X with its CENTRE at the origin
    bore = _cyl_x(tree, (bx - 1500, by), R, L, 0.0, verts=24)

    # bamboo node collars — the dizi's signature. The proto is centred at x = 0
    # so the rank's own points do all the placement (never a second translate).
    node_ring = _cyl_x(tree, (bx - 1500, by - 700),
                       _math(tree, "MULTIPLY", (bx - 1700, by - 700), R, 1.16
                             ).outputs[0],
                       ring_len.outputs[0], 0.0, verts=20)
    nodes = _rank_inst(
        tree, (bx - 900, by - 700), gin.outputs["Node Count"], node_ring,
        node_span.outputs[0],
        _half_span(tree, (bx - 1100, by - 700), node_span.outputs[0]),
        axis="x")

    # membrane hole (dimokong) rim at +0.20 L on the top face, just below the
    # blow hole — the real dizi order from the head end is blow, membrane, then
    # the six finger holes down the lower half.
    memb = _cyl_z(tree, (bx - 1500, by - 1100),
                  _math(tree, "MULTIPLY", (bx - 1700, by - 1100), R, 0.95
                        ).outputs[0],
                  _math(tree, "MULTIPLY", (bx - 1700, by - 1240), R, 0.40
                        ).outputs[0],
                  R,
                  x=_math(tree, "MULTIPLY", (bx - 1700, by - 1380), L, 0.20
                          ).outputs[0], verts=16)

    # six finger-hole rims, all BELOW the membrane: first at 0.10 L stepping
    # -0.10 L each, i.e. the rank spans [0.10 L, -0.32 L]. The step sign is
    # NEGATIVE because `_rank_inst` steps from `first` in the +axis direction by
    # default — without it the rank runs UP into the membrane and the blow hole.
    holes = _rims_x(
        tree, (bx - 1500, by - 1600), gin.outputs["Hole Count"],
        hole_span.outputs[0],
        _math(tree, "MULTIPLY", (bx - 1700, by - 1600), L, 0.10).outputs[0],
        R, HR,
        _math(tree, "MULTIPLY", (bx - 1700, by - 1740), R, 0.34).outputs[0],
        step_sign=-1.0)

    # blow-hole rim near the head end
    blow = _cyl_z(tree, (bx - 1500, by - 2000),
                  _math(tree, "MULTIPLY", (bx - 1700, by - 2000), R, 1.10
                        ).outputs[0],
                  _math(tree, "MULTIPLY", (bx - 1700, by - 2140), R, 0.40
                        ).outputs[0],
                  R,
                  x=_math(tree, "MULTIPLY", (bx - 1700, by - 2280), L, 0.30
                          ).outputs[0], verts=16)

    # bound end caps
    caps = []
    for i, sx in enumerate((-0.5, 0.5)):
        caps.append(_cyl_x(
            tree, (bx - 1300, by - 2400 - i * 200),
            _math(tree, "MULTIPLY", (bx - 1500, by - 2400 - i * 200), R, 1.20
                  ).outputs[0],
            cap_len.outputs[0],
            _math(tree, "MULTIPLY", (bx - 1500, by - 2680 - i * 200), L, sx
                  ).outputs[0], verts=20))

    geom = _join(tree, (bx + 800, by),
                 [bore, nodes, memb, holes, blow] + caps)

    _finish(tree, gin, gout, geom, (bx + 1000, by), BID,
            _attrs(tree, (bx + 800, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bamboo Bore + Nodes", "nodes": ("Cylinder", "Instance on Points"), "role": "geometry"},
        {"title": "Membrane + Finger Rims", "nodes": ("Cylinder", "Instance on Points"), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_xiao
# ---------------------------------------------------------------------------

def build_music_xiao(group_name="MEL_music_xiao"):
    """Xiao: end-blown VERTICAL bamboo tube, notched top, 5 finger rims.

    Laid along +Z from a base at the origin — the whole point of the
    instrument, and the gate asserts the z extent dominates (a xiao built
    horizontally would be a recorder with the wrong name).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_xiao"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 0.75, 0.35, 1.20)
    add_float_param(tree, "Body Radius M", 0.009, 0.004, 0.020)
    add_int_param(tree, "Node Count", 5, 2, 12)
    add_int_param(tree, "Hole Count", 5, 3, 8)
    add_float_param(tree, "Hole Radius M", 0.0035, 0.0015, 0.008)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Body Length M"]
    R = gin.outputs["Body Radius M"]
    HR = gin.outputs["Hole Radius M"]

    half_L = _math(tree, "MULTIPLY", (bx - 2000, by - 200), L, 0.5)
    ring_len = _math(tree, "MULTIPLY", (bx - 2000, by - 340), L, 0.012)
    node_span = _math(tree, "MULTIPLY", (bx - 2000, by - 480), L, 0.84)
    hole_span = _math(tree, "MULTIPLY", (bx - 2000, by - 620), L, 0.50)

    # tube: Z-laid, BASE at z = 0 (so the top is exactly at z = L)
    tube = _cyl_z(tree, (bx - 1500, by), R, L, half_L.outputs[0], verts=24)

    # notched top: a short inward chamfer where the V-notch sits
    notch = _cone_z(tree, (bx - 1500, by - 500),
                    _math(tree, "MULTIPLY", (bx - 1700, by - 500), R, 1.06
                          ).outputs[0],
                    _math(tree, "MULTIPLY", (bx - 1700, by - 640), R, 0.42
                          ).outputs[0],
                    _math(tree, "MULTIPLY", (bx - 1700, by - 780), L, 0.030
                          ).outputs[0],
                    L, verts=20)

    # bamboo node collars along the tube
    node_ring = _cyl_z(tree, (bx - 1500, by - 1100),
                       _math(tree, "MULTIPLY", (bx - 1700, by - 1100), R, 1.14
                             ).outputs[0],
                       ring_len.outputs[0], 0.0, verts=20)
    nodes = _rank_inst(
        tree, (bx - 900, by - 1100), gin.outputs["Node Count"], node_ring,
        node_span.outputs[0],
        _math(tree, "MULTIPLY", (bx - 1100, by - 1100), L, 0.06).outputs[0],
        axis="z")

    # five finger rims down the -Y face, on the LOWER half of the tube (the
    # xiao is fingered from the bottom; holes at 0.20..0.50 of the length)
    holes = _rims_z(
        tree, (bx - 1500, by - 1500), gin.outputs["Hole Count"],
        hole_span.outputs[0],
        _math(tree, "MULTIPLY", (bx - 1700, by - 1500), L, 0.20).outputs[0],
        _math(tree, "MULTIPLY", (bx - 1700, by - 1640), R, -0.92).outputs[0],
        HR, _math(tree, "MULTIPLY", (bx - 1700, by - 1780), R, 0.34
                  ).outputs[0])

    # bound foot ring
    foot = _cyl_z(tree, (bx - 1500, by - 2100),
                  _math(tree, "MULTIPLY", (bx - 1700, by - 2100), R, 1.16
                        ).outputs[0],
                  _math(tree, "MULTIPLY", (bx - 1700, by - 2240), L, 0.020
                        ).outputs[0],
                  _math(tree, "MULTIPLY", (bx - 1700, by - 2380), L, 0.014
                        ).outputs[0], verts=20)

    geom = _join(tree, (bx + 800, by), [tube, notch, nodes, holes, foot])

    _finish(tree, gin, gout, geom, (bx + 1000, by), BID,
            _attrs(tree, (bx + 800, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bamboo Tube + Notch", "nodes": ("Cylinder", "Cone"), "role": "geometry"},
        {"title": "Nodes + Finger Rims", "nodes": ("Cylinder", "Instance on Points"), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_bawu
# ---------------------------------------------------------------------------

def build_music_bawu(group_name="MEL_music_bawu"):
    """Bawu: bamboo tube with a rectangular FREE-REED window near the blow end.

    The reed window (two rails + a tongue plate) is the signature — a bawu is a
    free-reed instrument, not a mouthpiece-and-cane-reed one, so the reed is
    geometry in the tube wall rather than a cone on the end.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_bawu"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 0.45, 0.20, 0.80)
    add_float_param(tree, "Body Radius M", 0.008, 0.004, 0.018)
    add_int_param(tree, "Node Count", 4, 2, 10)
    add_int_param(tree, "Hole Count", 6, 3, 10)
    add_float_param(tree, "Hole Radius M", 0.0032, 0.0015, 0.008)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Body Length M"]
    R = gin.outputs["Body Radius M"]
    HR = gin.outputs["Hole Radius M"]

    ring_len = _math(tree, "MULTIPLY", (bx - 2000, by - 200), L, 0.013)
    node_span = _math(tree, "MULTIPLY", (bx - 2000, by - 340), L, 0.84)
    hole_span = _math(tree, "MULTIPLY", (bx - 2000, by - 480), L, 0.40)

    bore = _cyl_x(tree, (bx - 1500, by), R, L, 0.0, verts=24)

    node_ring = _cyl_x(tree, (bx - 1500, by - 700),
                       _math(tree, "MULTIPLY", (bx - 1700, by - 700), R, 1.15
                             ).outputs[0],
                       ring_len.outputs[0], 0.0, verts=20)
    nodes = _rank_inst(
        tree, (bx - 900, by - 700), gin.outputs["Node Count"], node_ring,
        node_span.outputs[0],
        _half_span(tree, (bx - 1100, by - 700), node_span.outputs[0]),
        axis="x")

    # free-reed window: a seat plate + a tongue plate on the top face, at +0.34 L
    seat_len = _math(tree, "MULTIPLY", (bx - 2000, by - 1100), L, 0.11)
    seat_w = _math(tree, "MULTIPLY", (bx - 2000, by - 1240), R, 1.10)
    seat_h = _math(tree, "MULTIPLY", (bx - 2000, by - 1380), R, 0.30)
    seat_x = _math(tree, "MULTIPLY", (bx - 2000, by - 1520), L, 0.34)
    seat = safe_node(tree, "GeometryNodeMeshCube", (bx - 1500, by - 1100))
    link_sockets(tree, _vec(tree, (bx - 1700, by - 1240),
                            seat_len.outputs[0], seat_w.outputs[0],
                            seat_h.outputs[0]), seat.inputs["Size"])
    seat_geo = _xf(tree, (bx - 1300, by - 1100), seat.outputs["Mesh"],
                   translation=_vec(tree, (bx - 1300, by - 1240),
                                    seat_x.outputs[0], 0.0,
                                    _math(tree, "MULTIPLY",
                                          (bx - 1500, by - 1240), R, 0.92
                                          ).outputs[0])
                   ).outputs["Geometry"]

    tongue_len = _math(tree, "MULTIPLY", (bx - 2000, by - 1600), L, 0.085)
    tongue_w = _math(tree, "MULTIPLY", (bx - 2000, by - 1740), R, 0.50)
    tongue_h = _math(tree, "MULTIPLY", (bx - 2000, by - 1880), R, 0.10)
    tongue = safe_node(tree, "GeometryNodeMeshCube", (bx - 1500, by - 1600))
    link_sockets(tree, _vec(tree, (bx - 1700, by - 1740),
                            tongue_len.outputs[0], tongue_w.outputs[0],
                            tongue_h.outputs[0]), tongue.inputs["Size"])
    tongue_geo = _xf(tree, (bx - 1300, by - 1600), tongue.outputs["Mesh"],
                     translation=_vec(tree, (bx - 1300, by - 1740),
                                      seat_x.outputs[0], 0.0,
                                      _math(tree, "MULTIPLY",
                                            (bx - 1500, by - 1740), R, 1.16
                                            ).outputs[0])
                     ).outputs["Geometry"]
    window = _join(tree, (bx - 1000, by - 1300), [seat_geo, tongue_geo])

    # blow collar at the +X end
    blow = _cyl_x(tree, (bx - 1500, by - 2100),
                  _math(tree, "MULTIPLY", (bx - 1700, by - 2100), R, 1.06
                        ).outputs[0],
                  _math(tree, "MULTIPLY", (bx - 1700, by - 2240), L, 0.055
                        ).outputs[0],
                  _math(tree, "MULTIPLY", (bx - 1700, by - 2380), L, 0.47
                        ).outputs[0], verts=20)

    # six finger rims on the top face, between the window and the -X end
    holes = _rims_x(
        tree, (bx - 1500, by - 2600), gin.outputs["Hole Count"],
        hole_span.outputs[0],
        _math(tree, "MULTIPLY", (bx - 1700, by - 2600), L, -0.34).outputs[0],
        R, HR,
        _math(tree, "MULTIPLY", (bx - 1700, by - 2740), R, 0.34).outputs[0])

    # bound end cap
    cap = _cyl_x(tree, (bx - 1500, by - 3000),
                 _math(tree, "MULTIPLY", (bx - 1700, by - 3000), R, 1.18
                       ).outputs[0],
                 _math(tree, "MULTIPLY", (bx - 1700, by - 3140), L, 0.024
                       ).outputs[0],
                 _math(tree, "MULTIPLY", (bx - 1700, by - 3280), L, -0.5
                       ).outputs[0], verts=20)

    geom = _join(tree, (bx + 800, by),
                 [bore, nodes, window, blow, holes, cap])

    _finish(tree, gin, gout, geom, (bx + 1000, by), BID,
            _attrs(tree, (bx + 800, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bamboo Bore + Nodes", "nodes": ("Cylinder", "Instance on Points"), "role": "geometry"},
        {"title": "Free-Reed Window", "nodes": ("Cube", "Join Geometry"), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_hulusi
# ---------------------------------------------------------------------------

def build_music_hulusi(group_name="MEL_music_hulusi"):
    """Hulusi: gourd wind chest, 3 graduated drones, melody pipe, blow pipe.

    The gourd (a squashed sphere) plus a melody pipe that carries FINGER HOLES
    is what separates this from the bagpipes, whose chanter has no keys and
    whose bag is leather. The drones reuse wave 6's `_stand` graduation law
    rather than three copied tubes.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_hulusi"
    bx, by = 0, 0

    add_float_param(tree, "Gourd Radius M", 0.065, 0.03, 0.14)
    add_float_param(tree, "Melody Length M", 0.34, 0.15, 0.60)
    add_float_param(tree, "Drone Length M", 0.30, 0.12, 0.55)
    add_int_param(tree, "Drone Count", 3, 1, 5)
    add_int_param(tree, "Hole Count", 7, 4, 10)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    BR = gin.outputs["Gourd Radius M"]
    ML = gin.outputs["Melody Length M"]
    DL = gin.outputs["Drone Length M"]

    # gourd: a squashed sphere, centre one radius-and-a-bit up
    gourd_z = _math(tree, "MULTIPLY", (bx - 2000, by - 200), BR, 1.10)
    gourd = _xf(tree, (bx - 1500, by),
                _sphere(tree, (bx - 1700, by), BR).outputs["Mesh"],
                scale=_vec(tree, (bx - 1700, by - 200), 1.30, 1.00, 0.86),
                translation=_vec(tree, (bx - 1700, by - 340), 0.0, 0.0,
                                 gourd_z.outputs[0])).outputs["Geometry"]
    gourd_top = _math(tree, "ADD", (bx - 2000, by - 480), gourd_z.outputs[0],
                      _math(tree, "MULTIPLY", (bx - 2200, by - 480), BR, 0.82
                            ).outputs[0])

    # mouthpiece: a short neck cone on the gourd's top, slightly +X of centre —
    # this IS the blow point on a hulusi (there is no separate blow pipe).
    neck = _cone_z(tree, (bx - 1500, by - 700),
                   _math(tree, "MULTIPLY", (bx - 1700, by - 700), BR, 0.26
                         ).outputs[0],
                   _math(tree, "MULTIPLY", (bx - 1700, by - 840), BR, 0.18
                         ).outputs[0],
                   _math(tree, "MULTIPLY", (bx - 1700, by - 980), BR, 0.42
                         ).outputs[0],
                   gourd_top.outputs[0],
                   x=_math(tree, "MULTIPLY", (bx - 1700, by - 1120), BR, 0.34
                           ).outputs[0], verts=16)

    # melody pipe: Z-laid, BASE on the gourd top, at -X
    melody = _cyl_z(tree, (bx - 1500, by - 1400),
                    _math(tree, "MULTIPLY", (bx - 1700, by - 1400), BR, 0.075
                          ).outputs[0],
                    ML,
                    _math(tree, "ADD", (bx - 1700, by - 1540),
                          gourd_top.outputs[0],
                          _math(tree, "MULTIPLY", (bx - 1900, by - 1540),
                                ML, 0.5).outputs[0]).outputs[0],
                    x=_math(tree, "MULTIPLY", (bx - 1700, by - 1680), BR, -1.05
                            ).outputs[0], verts=20)

    # finger rims down the melody pipe's -Y face
    holes = _rims_z(
        tree, (bx - 900, by - 1900), gin.outputs["Hole Count"],
        _math(tree, "MULTIPLY", (bx - 1100, by - 1900), ML, 0.62).outputs[0],
        _math(tree, "ADD", (bx - 1100, by - 2040), gourd_top.outputs[0],
              _math(tree, "MULTIPLY", (bx - 1300, by - 2040), ML, 0.24
                    ).outputs[0]).outputs[0],
        _math(tree, "MULTIPLY", (bx - 1100, by - 2180), BR, -0.075).outputs[0],
        _math(tree, "MULTIPLY", (bx - 1100, by - 2320), BR, 0.030).outputs[0],
        _math(tree, "MULTIPLY", (bx - 1100, by - 2460), BR, 0.034).outputs[0])

    # three graduated drones: the wave-6 `_stand` law, protos bottom-origin so
    # the per-instance scale graduates about the base, not the mid-point.
    drone_proto = _cyl_proto_z(tree, (bx - 1500, by - 2800),
                               _math(tree, "MULTIPLY", (bx - 1700, by - 2800),
                                     BR, 0.052).outputs[0], DL, verts=16)
    drone_cap = _cone_proto_z(tree, (bx - 1500, by - 3200),
                              _math(tree, "MULTIPLY", (bx - 1700, by - 3200),
                                    BR, 0.086).outputs[0],
                              _math(tree, "MULTIPLY", (bx - 1700, by - 3340),
                                    BR, 0.062).outputs[0],
                              _math(tree, "MULTIPLY", (bx - 1700, by - 3480),
                                    BR, 0.13).outputs[0], verts=16)
    cap_seated = _xf(tree, (bx - 1300, by - 3200), drone_cap,
                     translation=_vec(tree, (bx - 1300, by - 3340), 0.0, 0.0,
                                      DL)).outputs["Geometry"]
    drone_all = _join(tree, (bx - 1000, by - 2800), [drone_proto, cap_seated])
    drone_span = _math(tree, "MULTIPLY", (bx - 2000, by - 3800), BR, 1.05)
    drones = _stand(tree, (bx - 400, by - 2800), gin.outputs["Drone Count"],
                    drone_all, drone_span.outputs[0], gourd_top.outputs[0],
                    spread=0.24)
    drones = _xf(tree, (bx - 200, by - 2800), drones,
                 translation=_vec(tree, (bx - 200, by - 2940), 0.0,
                                  _math(tree, "MULTIPLY",
                                        (bx - 400, by - 2940), BR, -0.22
                                        ).outputs[0], 0.0)).outputs["Geometry"]

    # blow pipe: a short cone on the gourd's top at -X, tilted out. On a hulusi
    # the blow pipe and the melody-pipe seat are the two fittings on the gourd
    # top; the neck cone above IS the mouthpiece, so this stem is the blow point
    # at -1.05 BR — distinct from it, not a duplicate of it.
    blow_len = _math(tree, "MULTIPLY", (bx - 2000, by - 4200), BR, 0.80)
    blow_proto = _cyl_proto_z(tree, (bx - 1500, by - 4200),
                              _math(tree, "MULTIPLY", (bx - 1700, by - 4200),
                                    BR, 0.048).outputs[0], blow_len.outputs[0],
                              verts=12)
    blow = _xf(tree, (bx - 1300, by - 4200), blow_proto,
               rotation=(0.0, math.radians(-42.0), 0.0),
               translation=_vec(tree, (bx - 1300, by - 4340),
                                _math(tree, "MULTIPLY", (bx - 1500, by - 4340),
                                      BR, 1.05).outputs[0], 0.0,
                                gourd_top.outputs[0])).outputs["Geometry"]

    geom = _join(tree, (bx + 800, by),
                 [gourd, neck, melody, holes, drones, blow])

    _finish(tree, gin, gout, geom, (bx + 1000, by), BID,
            _attrs(tree, (bx + 800, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Gourd Chest", "nodes": ("UV Sphere", "Cone"), "role": "geometry"},
        {"title": "Melody Pipe + Holes", "nodes": ("Cylinder", "Instance on Points"), "role": "geometry"},
        {"title": "Drones + Blow Pipe", "nodes": ("Cylinder", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_suona
# ---------------------------------------------------------------------------

def build_music_suona(group_name="MEL_music_suona"):
    """Suona: conical wooden body, flared metal bell, staple reed, 8 finger rims.

    The BORE TAPERS (narrow at the reed, wide at the bell) — a straight
    cylinder is a trumpet, not a suona — and the bell is a second cone whose
    base sits exactly on the body's wide end. The gate asserts both.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_suona"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 0.30, 0.15, 0.55)
    add_float_param(tree, "Bore Radius M", 0.011, 0.005, 0.025)
    add_float_param(tree, "Bell Radius M", 0.055, 0.025, 0.11)
    add_float_param(tree, "Reed Length M", 0.045, 0.02, 0.09)
    add_int_param(tree, "Hole Count", 8, 4, 12)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Body Length M"]
    R = gin.outputs["Bore Radius M"]
    RL = gin.outputs["Reed Length M"]

    half_L = _math(tree, "MULTIPLY", (bx - 2000, by - 200), L, 0.5)
    neg_half_L = _math(tree, "MULTIPLY", (bx - 2200, by - 200), half_L.outputs[0],
                       -1.0)
    bell_len = _math(tree, "MULTIPLY", (bx - 2000, by - 340), L, 0.34)
    bell_end = _math(tree, "ADD", (bx - 2000, by - 480), half_L.outputs[0],
                     bell_len.outputs[0])
    r_wide = _math(tree, "MULTIPLY", (bx - 2000, by - 620), R, 1.55)
    hole_span = _math(tree, "MULTIPLY", (bx - 2000, by - 760), L, 0.55)

    # body: BASE (narrow, R) at -L/2, apex (wide) at +L/2 — the taper
    body = _cone_x(tree, (bx - 1500, by), R, r_wide.outputs[0], L,
                   neg_half_L.outputs[0], verts=28)

    # bell: base (wide) sits exactly on the body's apex, apex at the mouth
    bell = _cone_x(tree, (bx - 1500, by - 800), r_wide.outputs[0],
                   gin.outputs["Bell Radius M"], bell_len.outputs[0],
                   half_L.outputs[0], verts=40)

    # bell mouth rim
    rim = _cyl_x(tree, (bx - 1500, by - 1400),
                 _math(tree, "MULTIPLY", (bx - 1700, by - 1400),
                       gin.outputs["Bell Radius M"], 1.05).outputs[0],
                 _math(tree, "MULTIPLY", (bx - 1700, by - 1540), bell_len.outputs[0],
                       0.07).outputs[0],
                 bell_end.outputs[0], verts=40)

    # staple reed: a small cone leaving the narrow end outward (-X)
    reed = _cone_x(tree, (bx - 1500, by - 2000),
                   _math(tree, "MULTIPLY", (bx - 1700, by - 2000), R, 0.45
                         ).outputs[0],
                   _math(tree, "MULTIPLY", (bx - 1700, by - 2140), R, 0.22
                         ).outputs[0],
                   RL, neg_half_L.outputs[0], sign=-1.0, verts=14)

    # joint collar at the body/bell seam
    collar = _cyl_x(tree, (bx - 1500, by - 2600),
                    _math(tree, "MULTIPLY", (bx - 1700, by - 2600),
                          r_wide.outputs[0], 1.06).outputs[0],
                    _math(tree, "MULTIPLY", (bx - 1700, by - 2740), L, 0.035
                          ).outputs[0],
                    half_L.outputs[0], verts=28)

    # eight finger rims on the body's +Z face. The suona's bore is CONICAL, so
    # the tube's top surface climbs from R at the reed end to 1.55R at the bell
    # end; a rim seated at a constant radius would sink at the wide end. The
    # collars are therefore seated at the cone's MEAN radius (1.28 R) and made
    # deep enough (1.5 R) to straddle the taper across the whole rank.
    holes = _rims_x(
        tree, (bx - 1500, by - 3000), gin.outputs["Hole Count"],
        hole_span.outputs[0],
        _math(tree, "MULTIPLY", (bx - 1700, by - 3000), L, -0.28).outputs[0],
        _math(tree, "MULTIPLY", (bx - 1700, by - 3140), R, 1.28).outputs[0],
        _math(tree, "MULTIPLY", (bx - 1700, by - 3280), R, 0.42).outputs[0],
        _math(tree, "MULTIPLY", (bx - 1700, by - 3420), R, 1.50).outputs[0])

    geom = _join(tree, (bx + 800, by), [body, bell, rim, reed, collar, holes])

    _finish(tree, gin, gout, geom, (bx + 1000, by), BID,
            _attrs(tree, (bx + 800, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Conical Body", "nodes": ("Cone", "Transform"), "role": "geometry"},
        {"title": "Metal Bell + Reed", "nodes": ("Cone", "Transform"), "role": "geometry"},
        {"title": "Finger Rims", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_sheng
# ---------------------------------------------------------------------------

def build_music_sheng(group_name="MEL_music_sheng"):
    """Sheng: wind-chest bowl, two rows of graduated reed-window bamboo pipes.

    The pipe CLUSTER in a bowl is the instrument. One pipe law (`_cyl_proto_z`
    tube + a reed-window collar baked into the proto) is sized by `_stand`'s
    graduation, and the two rows are the same rank translated once in Y — no
    second placement of the rank itself.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_sheng"
    bx, by = 0, 0

    add_float_param(tree, "Chest Radius M", 0.075, 0.035, 0.16)
    add_float_param(tree, "Chest Height M", 0.070, 0.03, 0.15)
    add_float_param(tree, "Pipe Length M", 0.40, 0.18, 0.70)
    add_int_param(tree, "Pipe Count", 17, 8, 30)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    CR = gin.outputs["Chest Radius M"]
    CH = gin.outputs["Chest Height M"]
    PL = gin.outputs["Pipe Length M"]

    half_CH = _math(tree, "MULTIPLY", (bx - 2000, by - 200), CH, 0.5)
    bowl_top = _math(tree, "ADD", (bx - 2000, by - 340), CH,
                     _math(tree, "MULTIPLY", (bx - 2200, by - 340), CH, 0.45
                           ).outputs[0])
    pipe_base = _math(tree, "ADD", (bx - 2000, by - 480), bowl_top.outputs[0],
                      _math(tree, "MULTIPLY", (bx - 2200, by - 480), CH, 0.55
                            ).outputs[0])

    # wind chest: a cylinder (base at 0) with a tapering bowl on top
    chest = _cyl_z(tree, (bx - 1500, by), CR, CH, half_CH.outputs[0], verts=28)
    bowl = _cone_z(tree, (bx - 1500, by - 700),
                   CR,
                   _math(tree, "MULTIPLY", (bx - 1700, by - 700), CR, 0.52
                         ).outputs[0],
                   _math(tree, "MULTIPLY", (bx - 1700, by - 840), CH, 0.45
                         ).outputs[0],
                   CH, verts=28)

    # pipe proto: a tube whose BASE is its own origin, with a reed-window collar
    # baked in at 0.12 of its length so the graduation carries both.
    pipe_r = _math(tree, "MULTIPLY", (bx - 2000, by - 1100), CR, 0.045)
    tube = _cyl_proto_z(tree, (bx - 1500, by - 1100), pipe_r.outputs[0], PL,
                        verts=14)
    win = _cyl_z(tree, (bx - 1500, by - 1500),
                 _math(tree, "MULTIPLY", (bx - 1700, by - 1500), pipe_r.outputs[0],
                       1.45).outputs[0],
                 _math(tree, "MULTIPLY", (bx - 1700, by - 1640), PL, 0.035
                       ).outputs[0],
                 _math(tree, "MULTIPLY", (bx - 1700, by - 1780), PL, 0.12
                       ).outputs[0], verts=14)
    pipe_proto = _join(tree, (bx - 1000, by - 1100), [tube, win])

    # front row: 1.45 CR span; back row: 1.10 CR span, translated once in Y.
    # The Pipe Count is the TOTAL, split across the two rows — a real sheng's 17
    # pipes are 9 + 8, not 17 + 17. front = floor(n/2 + 0.5), back = n - front.
    front_span = _math(tree, "MULTIPLY", (bx - 2000, by - 2000), CR, 1.45)
    back_span = _math(tree, "MULTIPLY", (bx - 2000, by - 2140), CR, 1.10)
    row_y = _math(tree, "MULTIPLY", (bx - 2000, by - 2280), CR, 0.32)
    front_n = _math(tree, "FLOOR", (bx - 2000, by - 2400),
                    _math(tree, "ADD", (bx - 2200, by - 2400),
                          _math(tree, "DIVIDE", (bx - 2400, by - 2400),
                                gin.outputs["Pipe Count"], 2.0).outputs[0],
                          0.5).outputs[0])
    back_n = _math(tree, "SUBTRACT", (bx - 2000, by - 2560),
                   gin.outputs["Pipe Count"], front_n.outputs[0])

    front = _stand(tree, (bx - 400, by - 2000), front_n.outputs[0],
                   pipe_proto, front_span.outputs[0], pipe_base.outputs[0],
                   spread=0.34)
    front = _xf(tree, (bx - 200, by - 2000), front,
                translation=_vec(tree, (bx - 200, by - 2140), 0.0,
                                 row_y.outputs[0], 0.0)).outputs["Geometry"]
    back = _stand(tree, (bx - 400, by - 2600), back_n.outputs[0],
                  pipe_proto, back_span.outputs[0], pipe_base.outputs[0],
                  spread=0.30)
    back = _xf(tree, (bx - 200, by - 2600), back,
               translation=_vec(tree, (bx - 200, by - 2740), 0.0,
                                _math(tree, "MULTIPLY",
                                      (bx - 400, by - 2740), row_y.outputs[0],
                                      -1.0).outputs[0], 0.0)).outputs["Geometry"]

    # mouthpiece: a cone leaving the chest's -X side, pointing outward
    mp_len = _math(tree, "MULTIPLY", (bx - 2000, by - 3200), CR, 1.20)
    mp = _cone_x(tree, (bx - 1500, by - 3200),
                 _math(tree, "MULTIPLY", (bx - 1700, by - 3200), CR, 0.30
                       ).outputs[0],
                 _math(tree, "MULTIPLY", (bx - 1700, by - 3340), CR, 0.17
                       ).outputs[0],
                 mp_len.outputs[0],
                 _math(tree, "MULTIPLY", (bx - 1700, by - 3480), CR, -0.55
                       ).outputs[0],
                 z=half_CH.outputs[0], sign=-1.0, verts=16)

    geom = _join(tree, (bx + 800, by), [chest, bowl, front, back, mp])

    _finish(tree, gin, gout, geom, (bx + 1000, by), BID,
            _attrs(tree, (bx + 800, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Wind Chest", "nodes": ("Cylinder", "Cone"), "role": "geometry"},
        {"title": "Pipe Cluster (two rows)", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Mouthpiece", "nodes": ("Cone", "Transform"), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

register_builder(
    "MEL_music_dizi", build_music_dizi, "Dizi",
    "Dizi: Chinese transverse bamboo flute — bamboo node collars along the tube, "
    "a membrane hole (dimokong) rim, six finger rims, a blow-hole rim and bound "
    "end caps. Native-only.",
    "music",
)
register_builder(
    "MEL_music_xiao", build_music_xiao, "Xiao",
    "Xiao: end-blown vertical bamboo flute — notched top, bamboo node collars, "
    "five finger rims on the front face and a bound foot ring. Native-only.",
    "music",
)
register_builder(
    "MEL_music_bawu", build_music_bawu, "Bawu",
    "Bawu: bamboo free-reed pipe — a rectangular reed window (seat plate + "
    "tongue) in the tube wall near the blow end, bamboo node collars and six "
    "finger rims. Native-only.",
    "music",
)
register_builder(
    "MEL_music_hulusi", build_music_hulusi, "Hulusi",
    "Hulusi: gourd wind chest with a neck, a melody pipe carrying seven finger "
    "rims, three graduated drone pipes with top cups and a tilted blow pipe. "
    "Native-only.",
    "music",
)
register_builder(
    "MEL_music_suona", build_music_suona, "Suona",
    "Suona: conical wooden body under a flared metal bell, a staple-mounted "
    "double reed, a joint collar and eight finger rims. Native-only.",
    "music",
)
register_builder(
    "MEL_music_sheng", build_music_sheng, "Sheng",
    "Sheng: wind-chest bowl carrying two rows of graduated bamboo pipes, each "
    "with a reed-window collar, plus an outward mouthpiece cone. Native-only.",
    "music",
)
