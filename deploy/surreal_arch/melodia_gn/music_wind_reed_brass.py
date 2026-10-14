"""P4 wave 6 — reed & brass wind lane: oboe, bassoon, trumpet, tuba, accordion,
bagpipes.

Gap audit first (repo-wide grep over `deploy/surreal_arch/` + `Tools/registry_baseline.json`
+ the live registry, 2026-10-03): the wind lane owns saxophone, bandoneon, glass
harmonica, theremin, siku, flute, clarinet, recorder, melodica. NONE of the six
ids below existed anywhere (grep count 0 each):

    oboe, bassoon, trumpet, tuba, accordion, bagpipes

Nothing here re-implements an existing id. `MEL_music_accordion` is distinct from
`MEL_music_bandoneon`: the bandoneon's signature is a 6x12 BUTTON BOARD lofted
onto pleated bellows (its `Loft Splines` lead), the accordion's is a PIANO
keyboard on the treble box and a bass-button rank on the bass box. The shared
idea (two end boxes + a bellows between them) is a LAW here — `_box_pair` — sized
per caller, not a copy of the bandoneon's node graph.

Design rules (same as music_string_kit / music_percussion_kit / music_world_strings):
  - Native-only. These are tubes, bells, boxes and bags that 5.2 primitives
    express exactly; a Higgsas subtree here would be decoration, not a lead.
    Every builder still stores `higgsas_lead` (1.0 = native) so the family gate
    and the instruments gate read the lane uniformly.
  - ONE law per family, SIZED per instrument, never copied numbers: `_cone_x` /
    `_cyl_x` / `_cone_z` / `_cyl_z` (origin-explicit placement), `_box_pair`
    (accordion end boxes), `_stand` (a Z-standing rank graduated by
    ScaleInstances).
  - PRIMITIVE ORIGINS ARE NOT UNIFORM, and this module encodes the truth rather
    than the intuition. Probed 2026-10-03 with a bare depth-2 primitive:
    `MeshCone` spans z [0, 2] — its origin is the BASE, not the centre — while
    `MeshCylinder` spans z [-1, 1] — origin the CENTRE. Every bell, bocal and
    chanter here is a cone, so the `base + length/2` idiom (correct for a
    cylinder) put each of them half a length past its seat. The `_cone_*` helpers
    below take the BASE; the `_cyl_*` helpers take the CENTRE.
  - Placement is applied ONCE, in the Transform's Translation. A position written
    into BOTH a MeshLine `Start Location` and a later translate step doubles
    (measured: this lane's first pass put the oboe's key rank at x = -0.006 while
    the bore spanned [0, 0.50] — the rank was built at the -X end and never
    moved, and the aggregate gate still scored it 6/6).
  - A rank's Start/Offset are always CombineXYZ. A bare float on MeshLine.Offset
    broadcasts to (v, v, v) and silently puts the rank on the wrong axis.
  - A field value never feeds a PRIMITIVE dimension (the collapse class): every
    primitive dimension here is a socket-driven Math chain or a fully-linked
    CombineXYZ component.
  - Hole detail is a RIM RING laid on the body, never a boolean: measured
    2026-10-03 on the balalaika, a MeshBoolean whose cutter touches the mesh's
    own boundary emits ZERO geometry with no error and no link_failures entry.

Builders:
    MEL_music_oboe       conical bore + flared bell + double reed + 8 key cups
    MEL_music_bassoon    folded (U) bore + bocal crook + bell + reed + keys
    MEL_music_trumpet    leadpipe + tuning slide + 3 piston valves + flared bell
    MEL_music_tuba       bell-up cone + bottom bow + side pipe + 4 valves
    MEL_music_accordion  two boxes + pleated bellows + piano keys + bass buttons
    MEL_music_bagpipes   bag + chanter with hole rings + 3 graduated drones
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
from .music_percussion_kit import _inst_rank


# ---------------------------------------------------------------------------
# Origin-explicit placement — the primitive origin is NOT the centre
# ---------------------------------------------------------------------------


def _vec(tree, loc, x, y, z):
    return _combine(tree, loc, x, y, z).outputs["Vector"]


def _sphere(tree, loc, radius, segments=48, rings=24):
    """A UV sphere. `radius` may be a socket."""
    n = safe_node(tree, "GeometryNodeMeshUVSphere", loc)
    if n is None:
        return None
    for key, val in (("Segments", segments), ("Rings", rings)):
        s = sock(n, key)
        if s is not None:
            try:
                s.default_value = val
            except Exception:
                pass
    link_sockets(tree, radius, sock(n, "Radius"))
    return n


def _cone_x(tree, loc, r_base, r_tip, length, base_x, y=0.0, z=0.0,
            sign=1.0, verts=24):
    """Cone laid along X with its BASE at `base_x`, apex at base_x + sign*length."""
    prim = _cone(tree, loc, r_base, r_tip, length, vertices=verts)
    if prim is None:
        return None
    return _xf(tree, (loc[0] + 200, loc[1]), prim.outputs["Mesh"],
               rotation=(0.0, math.radians(90.0 * sign), 0.0),
               translation=_vec(tree, (loc[0] + 200, loc[1] - 200),
                               base_x, y, z)).outputs["Geometry"]


def _cyl_x(tree, loc, r, length, cx, y=0.0, z=0.0, verts=24):
    """Cylinder laid along X with its CENTRE at `cx`."""
    prim = _cyl(tree, loc, r, length, vertices=verts)
    if prim is None:
        return None
    return _xf(tree, (loc[0] + 200, loc[1]), prim.outputs["Mesh"],
               rotation=(0.0, math.radians(90.0), 0.0),
               translation=_vec(tree, (loc[0] + 200, loc[1] - 200),
                               cx, y, z)).outputs["Geometry"]


def _cone_z(tree, loc, r_base, r_tip, length, base_z, x=0.0, y=0.0,
            sign=1.0, verts=24):
    """Cone laid along Z with its BASE at `base_z`, apex at base_z + sign*length."""
    prim = _cone(tree, loc, r_base, r_tip, length, vertices=verts)
    if prim is None:
        return None
    rot = (math.radians(180.0), 0.0, 0.0) if sign < 0 else None
    return _xf(tree, (loc[0] + 200, loc[1]), prim.outputs["Mesh"],
               rotation=rot,
               translation=_vec(tree, (loc[0] + 200, loc[1] - 200),
                               x, y, base_z)).outputs["Geometry"]


def _cyl_z(tree, loc, r, length, cz, x=0.0, y=0.0, verts=24):
    """Cylinder laid along Z with its CENTRE at `cz`."""
    prim = _cyl(tree, loc, r, length, vertices=verts)
    if prim is None:
        return None
    return _xf(tree, (loc[0] + 200, loc[1]), prim.outputs["Mesh"],
               translation=_vec(tree, (loc[0] + 200, loc[1] - 200),
                               x, y, cz)).outputs["Geometry"]


def _cone_proto_z(tree, loc, r_base, r_tip, length, verts=24):
    """A cone whose BASE sits at its own origin (so an instance can stand on it)."""
    prim = _cone(tree, loc, r_base, r_tip, length, vertices=verts)
    if prim is None:
        return None
    return _xf(tree, (loc[0] + 200, loc[1]), prim.outputs["Mesh"],
               translation=_vec(tree, (loc[0] + 200, loc[1] - 200),
                               0.0, 0.0, 0.0)).outputs["Geometry"]


def _cyl_proto_z(tree, loc, r, length, verts=24):
    """A cylinder whose BASE (not centre) sits at its own origin."""
    prim = _cyl(tree, loc, r, length, vertices=verts)
    if prim is None:
        return None
    half = _math(tree, "MULTIPLY", (loc[0] + 100, loc[1] - 300), length, 0.5)
    return _xf(tree, (loc[0] + 200, loc[1]), prim.outputs["Mesh"],
               translation=_vec(tree, (loc[0] + 200, loc[1] - 200),
                               0.0, 0.0, half.outputs[0])).outputs["Geometry"]


# ---------------------------------------------------------------------------
# Shared rank / join laws
# ---------------------------------------------------------------------------


def _join(tree, loc, parts):
    """Join a list of geometry sockets, skipping Nones. Returns a socket."""
    bx, by = loc
    j = safe_node(tree, "GeometryNodeJoinGeometry", (bx, by))
    if j is None:
        return None
    for s in parts:
        if s is not None:
            link_sockets(tree, s, j.inputs["Geometry"])
    return j.outputs["Geometry"]


def _count_minus_one(tree, loc, count_sock):
    """count - 1, floored at 1 so a divide-by-zero can never poison a step."""
    return _math(tree, "MAXIMUM", loc,
                 _math(tree, "SUBTRACT", (loc[0] - 200, loc[1] - 140),
                       count_sock, 1.0).outputs[0], 1.0)


def _step(tree, loc, span_sock, count_sock):
    """span / max(count - 1, 1) — the per-instance pitch of a rank."""
    return _math(tree, "DIVIDE", loc, span_sock,
                 _count_minus_one(tree, (loc[0] - 200, loc[1] - 200),
                                  count_sock).outputs[0])


def _rank(tree, loc, count_sock, start_vec, offset_vec):
    """A rank of points from a MeshLine. Start/Offset are CombineXYZ by
    construction (a bare float on Offset broadcasts to (v, v, v))."""
    bx, by = loc
    line, line_sock = _line(tree, (bx, by), count_sock=count_sock,
                            start=start_vec, offset=offset_vec)
    if line is None:
        return None
    pts = safe_node(tree, "GeometryNodeMeshToPoints", (bx + 200, by))
    if pts is None:
        return None
    link_sockets(tree, line_sock, sock(pts, "Mesh") or pts.inputs[0])
    return pts.outputs["Points"]


def _rank_axis(tree, loc, count_sock, axis, first, step, y=0.0, z=0.0, x=0.0):
    """A rank stepped along one axis. `axis` is 'x', 'y' or 'z'."""
    bx, by = loc
    if axis == "x":
        a, b = (first, y, z), (step, 0.0, 0.0)
    elif axis == "y":
        a, b = (x, first, z), (0.0, step, 0.0)
    else:
        a, b = (x, y, first), (0.0, 0.0, step)
    return _rank(tree, loc, count_sock,
                 _vec(tree, (bx - 400, by - 280), *a),
                 _vec(tree, (bx - 400, by - 140), *b))


def _half_span(tree, loc, span_sock):
    """-span/2 — the start that centres a `count`-wide rank of `step` pitch."""
    return _math(tree, "MULTIPLY", loc, span_sock, -0.5).outputs[0]


def _stand(tree, loc, count_sock, proto_geo, span_sock, base_z, spread=0.62):
    """A rank of Z-standing protos centred on the origin, graduated by scale.

    The proto's ORIGIN must be its own bottom: the per-instance scale is applied
    about the instance origin, so a proto centred on its own mid-point would
    leave every graduated member floating at a different height. The rank is
    centred (`-span/2` start) so it sits over its host instead of running off +X.
    """
    bx, by = loc
    step = _step(tree, (bx - 600, by - 200), span_sock, count_sock)
    pts = _rank_axis(tree, (bx - 400, by), count_sock, "x",
                     _half_span(tree, (bx - 600, by + 200), span_sock),
                     step.outputs[0], z=base_z)
    if pts is None:
        return None
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 400, by - 300))
    t = _math(tree, "DIVIDE", (bx - 200, by - 300), idx.outputs["Index"],
              _count_minus_one(tree, (bx - 400, by - 440),
                               count_sock).outputs[0])
    s = _math(tree, "SUBTRACT", (bx, by - 300), 1.0,
              _math(tree, "MULTIPLY", (bx - 200, by - 440),
                    t.outputs[0], spread).outputs[0])
    sc = _vec(tree, (bx + 200, by - 300), s.outputs[0], s.outputs[0],
              s.outputs[0])
    return _inst_rank(tree, (bx + 400, by), pts, proto_geo, scale_sock=sc)


def _box_pair(tree, loc, span_sock, box_w_sock, box_h_sock, box_d_sock):
    """Two end boxes flanking a bellows gap along X. Accordion/bandoneon law.

    Returns `(geo, gap_half_socket, box_centre_socket)` so the caller can seat a
    bellows stack in the real gap instead of at copied coordinates.
    """
    bx, by = loc
    gap_half = _math(tree, "MULTIPLY", (bx - 200, by - 200), span_sock, 0.5)
    box_cx = _math(tree, "ADD", (bx - 200, by - 340), gap_half.outputs[0],
                   _math(tree, "MULTIPLY", (bx - 400, by - 340),
                         box_w_sock, 0.5).outputs[0])
    box = safe_node(tree, "GeometryNodeMeshCube", (bx, by))
    link_sockets(tree, _vec(tree, (bx - 200, by - 480),
                            box_w_sock, box_d_sock, box_h_sock),
                 box.inputs["Size"])
    parts = []
    for i, sx in enumerate((-1.0, 1.0)):
        s = _math(tree, "MULTIPLY", (bx - 400, by - 620 + i * 160),
                  box_cx.outputs[0], sx)
        parts.append(_xf(tree, (bx + 200, by - 620 + i * 160),
                         box.outputs["Mesh"],
                         translation=_vec(tree, (bx + 200, by - 760 + i * 160),
                                          s.outputs[0], 0.0, 0.0)
                         ).outputs["Geometry"])
    return _join(tree, (bx + 400, by), parts), gap_half, box_cx


def _rank_inst(tree, loc, count_sock, proto_geo, span_sock, first_sock,
               axis="x", step_sign=1.0, y=0.0, z=0.0, x=0.0):
    """A rank of `proto_geo` along one axis, starting at `first_sock`.

    `first_sock` is the FIRST instance's coordinate; the pitch is
    `span / (count-1)`. The proto is placed ONLY by the rank point — no extra
    translate — so a placement can never be applied twice.
    """
    bx, by = loc
    step = _step(tree, (bx - 600, by - 200), span_sock, count_sock)
    signed = _math(tree, "MULTIPLY", (bx - 400, by - 200), step.outputs[0],
                   step_sign)
    pts = _rank_axis(tree, (bx - 200, by), count_sock, axis, first_sock,
                     signed.outputs[0], y=y, z=z, x=x)
    if pts is None:
        return proto_geo
    inst = _inst_rank(tree, (bx + 200, by), pts, proto_geo)
    return _xf(tree, (bx + 400, by), inst).outputs["Geometry"]


def _attrs(tree, loc):
    """The lane's shared attribute pair: a semitone tag + the native lead flag."""
    bx, by = loc
    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx, by))
    smod = _math(tree, "FLOORMOD", (bx, by - 140), sidx.outputs["Index"], 12.0)
    return [("wind_semitone_mod12", smod.outputs[0]), ("higgsas_lead", 1.0)]


# ---------------------------------------------------------------------------
# MEL_music_oboe
# ---------------------------------------------------------------------------

def build_music_oboe(group_name="MEL_music_oboe"):
    """Oboe: conical bore, flared bell, double reed, 8 key cups, tenon rings."""
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_oboe"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 0.60, 0.3, 1.1)
    add_float_param(tree, "Body Radius M", 0.0085, 0.004, 0.02)
    add_float_param(tree, "Bell Radius M", 0.024, 0.012, 0.05)
    add_float_param(tree, "Reed Length M", 0.07, 0.03, 0.13)
    add_int_param(tree, "Key Count", 8, 4, 14)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Body Length M"]
    R = gin.outputs["Body Radius M"]
    RL = gin.outputs["Reed Length M"]

    bell_len = _math(tree, "MULTIPLY", (bx - 1800, by - 200), L, 0.17)
    bore_len = _math(tree, "SUBTRACT", (bx - 1800, by - 340), L,
                     bell_len.outputs[0])
    r_top = _math(tree, "MULTIPLY", (bx - 1800, by - 480), R, 1.25)

    # bore: base (R) at x = 0, apex (R*taper) at x = bore_len. The bell's base
    # sits exactly on the bore's apex — one law, two cones, no gap, no overlap.
    bore = _cone_x(tree, (bx - 1400, by), R, r_top.outputs[0],
                   bore_len.outputs[0], 0.0)
    bell = _cone_x(tree, (bx - 1400, by - 700), r_top.outputs[0],
                   gin.outputs["Bell Radius M"], bell_len.outputs[0],
                   bore_len.outputs[0])

    # double reed: two thin blades at the -X end (base of the bore), offset in Z
    reed_len = _math(tree, "MULTIPLY", (bx - 1800, by - 900), RL, 0.95)
    reed_w = _math(tree, "MULTIPLY", (bx - 1800, by - 1040), R, 1.7)
    reed_t = _math(tree, "MULTIPLY", (bx - 1800, by - 1180), R, 0.28)
    reed_z = _math(tree, "MULTIPLY", (bx - 1800, by - 1320), R, 0.34)
    reed_cx = _math(tree, "MULTIPLY", (bx - 1800, by - 1460),
                    reed_len.outputs[0], -0.5)
    blade = safe_node(tree, "GeometryNodeMeshCube", (bx - 1400, by - 900))
    link_sockets(tree, _vec(tree, (bx - 1600, by - 1040),
                            reed_len.outputs[0], reed_w.outputs[0],
                            reed_t.outputs[0]), blade.inputs["Size"])
    reeds = _join(tree, (bx - 1000, by - 900), [
        _xf(tree, (bx - 1200, by - 900), blade.outputs["Mesh"],
            translation=_vec(tree, (bx - 1200, by - 1040),
                             reed_cx.outputs[0], 0.0, reed_z.outputs[0])
            ).outputs["Geometry"],
        _xf(tree, (bx - 1200, by - 1200), blade.outputs["Mesh"],
            translation=_vec(tree, (bx - 1200, by - 1340),
                             reed_cx.outputs[0], 0.0,
                             _math(tree, "MULTIPLY", (bx - 1400, by - 1340),
                                   reed_z.outputs[0], -1.0).outputs[0])
            ).outputs["Geometry"],
    ])

    # key cups on top of the bore: first at 0.15L, pitch over 0.65L
    cup = _cyl_z(tree, (bx - 1400, by - 1800),
                 _math(tree, "MULTIPLY", (bx - 1600, by - 1800), R, 1.5
                       ).outputs[0],
                 _math(tree, "MULTIPLY", (bx - 1600, by - 1940), R, 0.7
                       ).outputs[0],
                 _math(tree, "MULTIPLY", (bx - 1600, by - 2080), R, 0.35
                       ).outputs[0], verts=12)
    keys = _rank_inst(
        tree, (bx - 600, by - 1800), gin.outputs["Key Count"], cup,
        _math(tree, "MULTIPLY", (bx - 800, by - 1800), L, 0.65).outputs[0],
        _math(tree, "MULTIPLY", (bx - 800, by - 1940), L, 0.15).outputs[0],
        axis="x", z=_math(tree, "MULTIPLY", (bx - 800, by - 2080),
                          R, 1.35).outputs[0])

    # tenon rings: two shallow collars naming the joint breaks
    rings = []
    for i, frac in enumerate((0.30, 0.62)):
        rings.append(_cyl_x(tree, (bx - 1200, by + 700 + i * 200),
                            _math(tree, "MULTIPLY",
                                  (bx - 1400, by + 700 + i * 200), R, 1.5
                                  ).outputs[0],
                            _math(tree, "MULTIPLY",
                                  (bx - 1400, by + 560 + i * 200), R, 0.5
                                  ).outputs[0],
                            _math(tree, "MULTIPLY",
                                  (bx - 1400, by + 700 + i * 200), L, frac
                                  ).outputs[0], verts=16))

    geom = _join(tree, (bx + 800, by), [bore, bell, reeds, keys] + rings)

    _finish(tree, gin, gout, geom, (bx + 1000, by), BID,
            _attrs(tree, (bx + 800, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Conical Bore + Bell", "nodes": ("Cone", "Transform"), "role": "geometry"},
        {"title": "Double Reed", "nodes": ("Cube", "Join Geometry"), "role": "geometry"},
        {"title": "Keys + Tenons", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_bassoon
# ---------------------------------------------------------------------------

def build_music_bassoon(group_name="MEL_music_bassoon"):
    """Bassoon: folded (U) bore, bocal crook, flared bell, double reed, 6 keys."""
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_bassoon"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 1.05, 0.6, 1.5)
    add_float_param(tree, "Body Radius M", 0.019, 0.01, 0.04)
    add_float_param(tree, "Bell Radius M", 0.034, 0.02, 0.07)
    add_float_param(tree, "Reed Length M", 0.075, 0.03, 0.14)
    add_int_param(tree, "Key Count", 6, 3, 12)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Body Length M"]
    R = gin.outputs["Body Radius M"]
    RL = gin.outputs["Reed Length M"]

    base_z = _math(tree, "MULTIPLY", (bx - 1800, by - 700), R, 1.15)
    tube_x = _math(tree, "MULTIPLY", (bx - 1800, by - 840), R, 1.5)
    neg_tube_x = _math(tree, "MULTIPLY", (bx - 2000, by - 840),
                       tube_x.outputs[0], -1.0)
    tube_cz = _math(tree, "ADD", (bx - 1600, by - 980), base_z.outputs[0],
                    _math(tree, "MULTIPLY", (bx - 1800, by - 1120),
                          L, 0.5).outputs[0])
    tube_top = _math(tree, "ADD", (bx - 1600, by - 1260), base_z.outputs[0], L)

    # the fold: two parallel tubes at +/-x, joined by a bottom bow along X
    tubes = [
        _cyl_z(tree, (bx - 1400, by + 200), R, L, tube_cz.outputs[0],
               x=tube_x.outputs[0], verts=20),
        _cyl_z(tree, (bx - 1400, by - 200), R, L, tube_cz.outputs[0],
               x=neg_tube_x.outputs[0], verts=20),
    ]
    bow = _cyl_x(tree, (bx - 1400, by - 1400), R,
                 _math(tree, "MULTIPLY", (bx - 1600, by - 1400),
                       tube_x.outputs[0], 2.4).outputs[0],
                 0.0, z=base_z.outputs[0], verts=20)

    # bell: a flared cone standing on the TOP of the front tube
    bell = _cone_z(tree, (bx - 1400, by + 700), R,
                   gin.outputs["Bell Radius M"],
                   _math(tree, "MULTIPLY", (bx - 1600, by + 700),
                         L, 0.20).outputs[0],
                   tube_top.outputs[0], x=tube_x.outputs[0], verts=24)

    # bocal crook: a cone leaving the top of the BACK tube toward -X
    crook_len = _math(tree, "MULTIPLY", (bx - 1800, by - 1800), L, 0.16)
    crook = _cone_x(tree, (bx - 1400, by - 1800),
                    _math(tree, "MULTIPLY", (bx - 1600, by - 1800), R, 0.45
                          ).outputs[0],
                    _math(tree, "MULTIPLY", (bx - 1600, by - 1940), R, 0.70
                          ).outputs[0],
                    crook_len.outputs[0], neg_tube_x.outputs[0],
                    z=tube_top.outputs[0], sign=-1.0, verts=16)

    # double reed at the crook's far end
    reed_cx = _math(tree, "SUBTRACT", (bx - 1600, by - 2400),
                    neg_tube_x.outputs[0],
                    _math(tree, "ADD", (bx - 1800, by - 2400),
                          crook_len.outputs[0],
                          _math(tree, "MULTIPLY", (bx - 2000, by - 2400),
                                RL, 0.5).outputs[0]).outputs[0])
    reed_z = _math(tree, "MULTIPLY", (bx - 1800, by - 2400), R, 0.16)
    blade = safe_node(tree, "GeometryNodeMeshCube", (bx - 1400, by - 2400))
    link_sockets(tree, _vec(tree, (bx - 1600, by - 2540),
                            _math(tree, "MULTIPLY", (bx - 1800, by - 2540),
                                  RL, 0.95).outputs[0],
                            _math(tree, "MULTIPLY", (bx - 1800, by - 2680),
                                  R, 0.85).outputs[0],
                            _math(tree, "MULTIPLY", (bx - 1800, by - 2820),
                                  R, 0.14).outputs[0]), blade.inputs["Size"])
    reeds = _join(tree, (bx - 1000, by - 2400), [
        _xf(tree, (bx - 1200, by - 2400), blade.outputs["Mesh"],
            translation=_vec(tree, (bx - 1200, by - 2540),
                             reed_cx.outputs[0], 0.0,
                             _math(tree, "ADD", (bx - 1400, by - 2540),
                                   tube_top.outputs[0],
                                   reed_z.outputs[0]).outputs[0])
            ).outputs["Geometry"],
        _xf(tree, (bx - 1200, by - 2700), blade.outputs["Mesh"],
            translation=_vec(tree, (bx - 1200, by - 2840),
                             reed_cx.outputs[0], 0.0,
                             _math(tree, "SUBTRACT", (bx - 1400, by - 2840),
                                   tube_top.outputs[0],
                                   reed_z.outputs[0]).outputs[0])
            ).outputs["Geometry"],
    ])

    # keys: a rank along Z on the front tube's +Y face
    cup = _cyl_x(tree, (bx - 1400, by - 3400),
                 _math(tree, "MULTIPLY", (bx - 1600, by - 3400), R, 0.5
                       ).outputs[0],
                 _math(tree, "MULTIPLY", (bx - 1600, by - 3540), R, 0.9
                       ).outputs[0],
                 0.0, verts=10)
    keys = _rank_inst(
        tree, (bx - 600, by - 3400), gin.outputs["Key Count"], cup,
        _math(tree, "MULTIPLY", (bx - 800, by - 3400), L, 0.52).outputs[0],
        _math(tree, "ADD", (bx - 800, by - 3540), base_z.outputs[0],
              _math(tree, "MULTIPLY", (bx - 1000, by - 3540),
                    L, 0.20).outputs[0]).outputs[0],
        axis="z",
        y=_math(tree, "MULTIPLY", (bx - 800, by - 3680), R, 1.35).outputs[0],
        x=tube_x.outputs[0])

    geom = _join(tree, (bx + 800, by),
                 tubes + [bow, bell, crook, reeds, keys])

    _finish(tree, gin, gout, geom, (bx + 1000, by), BID,
            _attrs(tree, (bx + 800, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Folded Bore + Bow", "nodes": ("Cylinder", "Transform"), "role": "geometry"},
        {"title": "Bell + Bocal + Reed", "nodes": ("Cone", "Join Geometry"), "role": "geometry"},
        {"title": "Keys", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_trumpet
# ---------------------------------------------------------------------------

def build_music_trumpet(group_name="MEL_music_trumpet"):
    """Trumpet: leadpipe, tuning slide, 3 piston valves, flared bell, mouthpiece."""
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_trumpet"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 0.44, 0.25, 0.8)
    add_float_param(tree, "Bore Radius M", 0.0105, 0.005, 0.022)
    add_float_param(tree, "Bell Radius M", 0.062, 0.03, 0.12)
    add_int_param(tree, "Valve Count", 3, 2, 5)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Body Length M"]
    R = gin.outputs["Bore Radius M"]

    lead_len = _math(tree, "MULTIPLY", (bx - 1800, by - 700), L, 0.68)
    half_lead = _math(tree, "MULTIPLY", (bx - 1800, by - 840),
                      lead_len.outputs[0], 0.5)
    neg_half = _math(tree, "MULTIPLY", (bx - 2000, by - 840),
                     half_lead.outputs[0], -1.0)
    bell_len = _math(tree, "MULTIPLY", (bx - 1800, by - 980), L, 0.32)

    lead = _cyl_x(tree, (bx - 1400, by), R, lead_len.outputs[0], 0.0)
    # bell base sits on the leadpipe's +X end
    bell = _cone_x(tree, (bx - 1400, by - 980), R,
                   gin.outputs["Bell Radius M"], bell_len.outputs[0],
                   half_lead.outputs[0], verts=32)
    # mouthpiece cone leaves the -X end pointing outward
    mp_len = _math(tree, "MULTIPLY", (bx - 1800, by - 1400), L, 0.13)
    mp = _cone_x(tree, (bx - 1400, by - 1400),
                 R, _math(tree, "MULTIPLY", (bx - 1600, by - 1400),
                          R, 0.80).outputs[0],
                 mp_len.outputs[0], neg_half.outputs[0], sign=-1.0, verts=16)

    # tuning slide: two parallel legs in Z near the bell end + a U elbow
    slide_len = _math(tree, "MULTIPLY", (bx - 1800, by + 700), L, 0.22)
    slide_z = _math(tree, "MULTIPLY", (bx - 1800, by + 560), R, 3.0)
    slide_cx = _math(tree, "MULTIPLY", (bx - 1800, by + 420), L, 0.10)
    slide_end = _math(tree, "SUBTRACT", (bx - 1600, by + 420),
                      slide_cx.outputs[0],
                      _math(tree, "MULTIPLY", (bx - 1800, by + 420),
                            slide_len.outputs[0], 0.5).outputs[0])
    legs = []
    for i, sz in enumerate((1.0, -1.0)):
        legs.append(_cyl_x(tree, (bx - 1200, by + 700 + i * 200), R,
                           slide_len.outputs[0], slide_cx.outputs[0],
                           z=_math(tree, "MULTIPLY",
                                   (bx - 1400, by + 700 + i * 200),
                                   slide_z.outputs[0], sz).outputs[0],
                           verts=16))
    elbow = _cyl_z(tree, (bx - 1400, by + 1100), R,
                   _math(tree, "MULTIPLY", (bx - 1600, by + 1100),
                         slide_z.outputs[0], 2.0).outputs[0],
                   0.0, x=slide_end.outputs[0], verts=16)

    # valves: a rank along X of Z-standing pistons on top of the leadpipe
    valve_len = _math(tree, "MULTIPLY", (bx - 1800, by - 2000), R, 8.0)
    valve_base = _math(tree, "MULTIPLY", (bx - 1800, by - 2000), R, 1.2)
    valve_proto = _cyl_proto_z(tree, (bx - 1400, by - 2000),
                               _math(tree, "MULTIPLY", (bx - 1600, by - 2000),
                                     R, 1.55).outputs[0],
                               valve_len.outputs[0], verts=16)
    vspan = _math(tree, "MULTIPLY", (bx - 1800, by - 2200), L, 0.30)
    valves = _stand(tree, (bx - 800, by - 2000), gin.outputs["Valve Count"],
                    valve_proto, vspan.outputs[0], valve_base.outputs[0],
                    spread=0.0)

    # finger buttons: spheres seated on each valve top
    btn = _sphere(tree, (bx - 1400, by - 2600),
                  _math(tree, "MULTIPLY", (bx - 1600, by - 2600), R, 0.80
                        ).outputs[0], segments=16, rings=8)
    btn_proto = _xf(tree, (bx - 1200, by - 2600), btn.outputs["Mesh"],
                    translation=_vec(tree, (bx - 1200, by - 2740), 0.0, 0.0,
                                     _math(tree, "ADD", (bx - 1400, by - 2740),
                                           valve_len.outputs[0],
                                           _math(tree, "MULTIPLY",
                                                 (bx - 1600, by - 2740),
                                                 R, 0.80).outputs[0]
                                           ).outputs[0])
                    ).outputs["Geometry"]
    buttons = _stand(tree, (bx - 400, by - 2600), gin.outputs["Valve Count"],
                     btn_proto, vspan.outputs[0], valve_base.outputs[0],
                     spread=0.0)

    geom = _join(tree, (bx + 800, by),
                 [lead, bell, mp, elbow] + legs + [valves, buttons])

    _finish(tree, gin, gout, geom, (bx + 1000, by), BID,
            _attrs(tree, (bx + 800, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Leadpipe + Bell + Mouthpiece", "nodes": ("Cone", "Cylinder"), "role": "geometry"},
        {"title": "Tuning Slide", "nodes": ("Cylinder", "Transform"), "role": "geometry"},
        {"title": "Valves + Buttons", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_tuba
# ---------------------------------------------------------------------------

def build_music_tuba(group_name="MEL_music_tuba"):
    """Tuba: bell-up cone, main body, bottom bow, side pipe, 4 valves, mouthpipe."""
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_tuba"
    bx, by = 0, 0

    add_float_param(tree, "Body Height M", 1.02, 0.6, 1.5)
    add_float_param(tree, "Bore Radius M", 0.052, 0.03, 0.09)
    add_float_param(tree, "Bell Radius M", 0.19, 0.10, 0.30)
    add_int_param(tree, "Valve Count", 4, 3, 6)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    H = gin.outputs["Body Height M"]
    R = gin.outputs["Bore Radius M"]

    bow_z = _math(tree, "MULTIPLY", (bx - 1800, by - 700), R, 1.15)
    body_len = _math(tree, "MULTIPLY", (bx - 1800, by - 840), H, 0.54)
    body_x = _math(tree, "MULTIPLY", (bx - 1800, by - 980), R, 2.9)
    neg_body_x = _math(tree, "MULTIPLY", (bx - 2000, by - 980),
                       body_x.outputs[0], -1.0)
    body_cz = _math(tree, "ADD", (bx - 1600, by - 1120), bow_z.outputs[0],
                    _math(tree, "MULTIPLY", (bx - 1800, by - 1260),
                          body_len.outputs[0], 0.5).outputs[0])
    body_top = _math(tree, "ADD", (bx - 1600, by - 1400), bow_z.outputs[0],
                     body_len.outputs[0])

    body = _cyl_z(tree, (bx - 1400, by), R, body_len.outputs[0],
                  body_cz.outputs[0], x=body_x.outputs[0], verts=32)
    bow = _cyl_x(tree, (bx - 1400, by - 1400), R,
                 _math(tree, "MULTIPLY", (bx - 1600, by - 1400),
                       body_x.outputs[0], 2.4).outputs[0],
                 0.0, z=bow_z.outputs[0], verts=32)

    side_len = _math(tree, "MULTIPLY", (bx - 1800, by - 1700), H, 0.44)
    side_cz = _math(tree, "ADD", (bx - 1600, by - 1840), bow_z.outputs[0],
                    _math(tree, "MULTIPLY", (bx - 1800, by - 1980),
                          side_len.outputs[0], 0.5).outputs[0])
    side = _cyl_z(tree, (bx - 1400, by - 1700),
                  _math(tree, "MULTIPLY", (bx - 1600, by - 1700), R, 0.68
                        ).outputs[0],
                  side_len.outputs[0], side_cz.outputs[0],
                  x=neg_body_x.outputs[0], verts=24)

    # bell: a big flare standing on the main body's top
    bell_len = _math(tree, "MULTIPLY", (bx - 1800, by - 2100), H, 0.42)
    bell = _cone_z(tree, (bx - 1400, by - 2100), R,
                   gin.outputs["Bell Radius M"], bell_len.outputs[0],
                   body_top.outputs[0], x=body_x.outputs[0], verts=48)

    # valves: a vertical bank of pistons on the side pipe
    valve_len = _math(tree, "MULTIPLY", (bx - 1800, by - 2500), R, 2.6)
    valve_proto = _cyl_proto_z(tree, (bx - 1400, by - 2500),
                               _math(tree, "MULTIPLY", (bx - 1600, by - 2500),
                                     R, 0.58).outputs[0],
                               valve_len.outputs[0], verts=16)
    vspan = _math(tree, "MULTIPLY", (bx - 1800, by - 2700), side_len.outputs[0],
                  0.55)
    valves = _stand(tree, (bx - 800, by - 2500), gin.outputs["Valve Count"],
                    valve_proto, vspan.outputs[0],
                    _math(tree, "ADD", (bx - 1600, by - 2700),
                          bow_z.outputs[0],
                          _math(tree, "MULTIPLY", (bx - 1800, by - 2840),
                                side_len.outputs[0], 0.12).outputs[0]).outputs[0],
                    spread=0.0)

    # mouthpipe: a cone leaving the side pipe toward -X near its top
    mp_len = _math(tree, "MULTIPLY", (bx - 1800, by - 3100), H, 0.24)
    mp = _cone_x(tree, (bx - 1400, by - 3100),
                 _math(tree, "MULTIPLY", (bx - 1600, by - 3100), R, 0.52
                       ).outputs[0],
                 _math(tree, "MULTIPLY", (bx - 1600, by - 3240), R, 0.34
                       ).outputs[0],
                 mp_len.outputs[0], neg_body_x.outputs[0], sign=-1.0,
                 z=_math(tree, "ADD", (bx - 1600, by - 3380),
                         bow_z.outputs[0],
                         _math(tree, "MULTIPLY", (bx - 1800, by - 3380),
                               side_len.outputs[0], 0.84).outputs[0]).outputs[0],
                 verts=16)

    geom = _join(tree, (bx + 800, by),
                 [body, bow, side, bell, mp, valves])

    _finish(tree, gin, gout, geom, (bx + 1000, by), BID,
            _attrs(tree, (bx + 800, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Body + Bow + Side Pipe", "nodes": ("Cylinder", "Transform"), "role": "geometry"},
        {"title": "Bell + Mouthpipe", "nodes": ("Cone", "Transform"), "role": "geometry"},
        {"title": "Valves", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_accordion
# ---------------------------------------------------------------------------

def build_music_accordion(group_name="MEL_music_accordion"):
    """Accordion: two end boxes, pleated bellows, piano keys, bass buttons, straps."""
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_accordion"
    bx, by = 0, 0

    add_float_param(tree, "Body Height M", 0.32, 0.16, 0.6)
    add_float_param(tree, "Body Depth M", 0.20, 0.10, 0.4)
    add_float_param(tree, "Box Width M", 0.10, 0.05, 0.2)
    add_float_param(tree, "Bellows Span M", 0.22, 0.10, 0.4)
    add_int_param(tree, "Pleat Count", 14, 6, 30)
    add_int_param(tree, "Key Count", 14, 6, 30)
    add_int_param(tree, "Bass Button Count", 8, 4, 20)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    H = gin.outputs["Body Height M"]
    D = gin.outputs["Body Depth M"]
    BW = gin.outputs["Box Width M"]
    SPAN = gin.outputs["Bellows Span M"]

    boxes, gap_half, box_cx = _box_pair(tree, (bx - 1600, by), SPAN, BW, H, D)

    # bellows: a rank of thin plates across the gap, each tilted about X so the
    # fold reads as a fold. The tilt is baked into the PROTO (a rank of
    # instances cannot carry a per-instance rotation through _inst_rank), the
    # same choice wave 5's ji / zhen-ma bridges make. The rank is centred on the
    # origin, which is the middle of the gap, so the pleats fill the bellows.
    plate = safe_node(tree, "GeometryNodeMeshCube", (bx - 1600, by + 700))
    plate_t = _step(tree, (bx - 1800, by + 700),
                    _math(tree, "MULTIPLY", (bx - 2000, by + 700),
                          SPAN, 0.90).outputs[0],
                    gin.outputs["Pleat Count"])
    link_sockets(tree, _vec(tree, (bx - 1800, by + 560),
                            _math(tree, "MULTIPLY", (bx - 2000, by + 560),
                                  plate_t.outputs[0], 0.35).outputs[0],
                            _math(tree, "MULTIPLY", (bx - 2000, by + 420),
                                  D, 1.02).outputs[0],
                            _math(tree, "MULTIPLY", (bx - 2000, by + 280),
                                  H, 1.02).outputs[0]), plate.inputs["Size"])
    plate_proto = _xf(tree, (bx - 1400, by + 700), plate.outputs["Mesh"],
                      rotation=(math.radians(14.0), 0.0, 0.0)
                      ).outputs["Geometry"]
    pleats = _stand(tree, (bx - 600, by + 700), gin.outputs["Pleat Count"],
                    plate_proto, SPAN, 0.0, spread=0.0)

    # piano keys: a rank along Z on the treble box, projecting out of its -Y face
    key_w = _math(tree, "MULTIPLY", (bx - 1800, by + 1100), H, 0.035)
    key_d = _math(tree, "MULTIPLY", (bx - 1800, by + 1240), D, 0.38)
    key_h = _math(tree, "MULTIPLY", (bx - 1800, by + 1380), H, 0.055)
    key = safe_node(tree, "GeometryNodeMeshCube", (bx - 1600, by + 1100))
    link_sockets(tree, _vec(tree, (bx - 1800, by + 1240),
                            key_w.outputs[0], key_d.outputs[0],
                            key_h.outputs[0]), key.inputs["Size"])
    keys = _rank_inst(
        tree, (bx - 600, by + 1100), gin.outputs["Key Count"],
        key.outputs["Mesh"],
        _math(tree, "MULTIPLY", (bx - 800, by + 1100), H, 0.72).outputs[0],
        _math(tree, "MULTIPLY", (bx - 800, by + 1240), H, -0.36).outputs[0],
        axis="z",
        y=_math(tree, "MULTIPLY", (bx - 800, by + 1380), D, -0.62).outputs[0],
        x=box_cx.outputs[0])

    # bass buttons: a rank along Z of short cylinders on the bass box's -Y face
    btn = _cyl_proto_z(tree, (bx - 1400, by + 1900),
                       _math(tree, "MULTIPLY", (bx - 1600, by + 1900),
                             H, 0.012).outputs[0],
                       _math(tree, "MULTIPLY", (bx - 1600, by + 2040),
                             D, 0.06).outputs[0], verts=12)
    buttons = _rank_inst(
        tree, (bx - 600, by + 1900), gin.outputs["Bass Button Count"], btn,
        _math(tree, "MULTIPLY", (bx - 800, by + 1900), H, 0.50).outputs[0],
        _math(tree, "MULTIPLY", (bx - 800, by + 2040), H, -0.25).outputs[0],
        axis="z",
        y=_math(tree, "MULTIPLY", (bx - 800, by + 2320), D, -0.58).outputs[0],
        x=_math(tree, "MULTIPLY", (bx - 800, by + 2180),
                box_cx.outputs[0], -1.0).outputs[0])

    # straps: two thin bars across the treble box
    strap = safe_node(tree, "GeometryNodeMeshCube", (bx - 1600, by + 2800))
    link_sockets(tree, _vec(tree, (bx - 1800, by + 2660),
                            _math(tree, "MULTIPLY", (bx - 2000, by + 2660),
                                  BW, 1.1).outputs[0],
                            _math(tree, "MULTIPLY", (bx - 2000, by + 2520),
                                  D, 0.08).outputs[0],
                            _math(tree, "MULTIPLY", (bx - 2000, by + 2380),
                                  H, 0.055).outputs[0]), strap.inputs["Size"])
    straps = []
    for i, sz in enumerate((0.34, -0.30)):
        straps.append(_xf(
            tree, (bx - 1400, by + 2800 + i * 200), strap.outputs["Mesh"],
            translation=_vec(tree, (bx - 1400, by + 2940 + i * 200),
                             box_cx.outputs[0],
                             _math(tree, "MULTIPLY",
                                   (bx - 1600, by + 2940 + i * 200),
                                   D, -0.54).outputs[0],
                             _math(tree, "MULTIPLY",
                                   (bx - 1600, by + 2940 + i * 200),
                                   H, sz).outputs[0])).outputs["Geometry"])

    geom = _join(tree, (bx + 800, by),
                 [boxes, pleats, keys, buttons] + straps)

    _finish(tree, gin, gout, geom, (bx + 1000, by), BID,
            _attrs(tree, (bx + 800, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "End Boxes", "nodes": ("Cube", "Transform"), "role": "geometry"},
        {"title": "Bellows Pleats", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Keys + Bass Buttons", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_bagpipes
# ---------------------------------------------------------------------------

def build_music_bagpipes(group_name="MEL_music_bagpipes"):
    """Bagpipes: bag, chanter with hole rings, 3 graduated drones, blowpipe."""
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_bagpipes"
    bx, by = 0, 0

    add_float_param(tree, "Bag Radius M", 0.17, 0.09, 0.32)
    add_float_param(tree, "Chanter Length M", 0.33, 0.18, 0.55)
    add_float_param(tree, "Drone Length M", 0.70, 0.4, 1.1)
    add_int_param(tree, "Drone Count", 3, 1, 5)
    add_int_param(tree, "Hole Count", 8, 4, 12)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    BR = gin.outputs["Bag Radius M"]
    CL = gin.outputs["Chanter Length M"]
    DL = gin.outputs["Drone Length M"]

    # bag: a squashed sphere whose centre sits one radius-and-a-bit up
    bag_z = _math(tree, "MULTIPLY", (bx - 1800, by - 200), BR, 2.6)
    bag_geo = _xf(tree, (bx - 1200, by),
                  _sphere(tree, (bx - 1400, by), BR).outputs["Mesh"],
                  scale=_vec(tree, (bx - 1600, by - 200), 1.30, 1.00, 0.85),
                  translation=_vec(tree, (bx - 1400, by - 340), 0.0, 0.0,
                                   bag_z.outputs[0])).outputs["Geometry"]
    bag_bottom = _math(tree, "SUBTRACT", (bx - 1800, by - 480), bag_z.outputs[0],
                       _math(tree, "MULTIPLY", (bx - 2000, by - 480),
                             BR, 0.72).outputs[0])
    bag_top = _math(tree, "ADD", (bx - 1800, by - 620), bag_z.outputs[0],
                    _math(tree, "MULTIPLY", (bx - 2000, by - 620),
                          BR, 0.72).outputs[0])

    # chanter: a tapered cone HANGING from the bag's underside, apex downward
    chanter_x = _math(tree, "MULTIPLY", (bx - 1800, by - 700), BR, 0.60)
    chanter_r = _math(tree, "MULTIPLY", (bx - 1800, by - 840), BR, 0.065)
    chanter = _cone_z(tree, (bx - 1400, by - 700),
                      chanter_r.outputs[0],
                      _math(tree, "MULTIPLY", (bx - 1600, by - 700),
                            chanter_r.outputs[0], 0.62).outputs[0],
                      CL, bag_bottom.outputs[0], x=chanter_x.outputs[0],
                      sign=-1.0, verts=16)

    # hole rings: shallow collars down the chanter (a RIM RING, never a boolean)
    hole = _cyl_z(tree, (bx - 1400, by - 1200),
                  _math(tree, "MULTIPLY", (bx - 1600, by - 1200),
                        chanter_r.outputs[0], 1.6).outputs[0],
                  _math(tree, "MULTIPLY", (bx - 1600, by - 1340),
                        chanter_r.outputs[0], 0.45).outputs[0],
                  0.0, verts=16)
    holes = _rank_inst(
        tree, (bx - 600, by - 1200), gin.outputs["Hole Count"], hole,
        _math(tree, "MULTIPLY", (bx - 800, by - 1200), CL, 0.62).outputs[0],
        _math(tree, "SUBTRACT", (bx - 800, by - 1340), bag_bottom.outputs[0],
              _math(tree, "MULTIPLY", (bx - 1000, by - 1340),
                    CL, 0.18).outputs[0]).outputs[0],
        axis="z", step_sign=-1.0, x=chanter_x.outputs[0])

    # drones: a graduated rank standing on the bag, each with a top cup BAKED
    # INTO the proto so the per-instance scale graduates both.
    drone_r = _math(tree, "MULTIPLY", (bx - 1800, by + 700), BR, 0.060)
    drone_tube = _cyl_proto_z(tree, (bx - 1400, by + 700), drone_r.outputs[0],
                              DL, verts=16)
    cup = _cone_proto_z(tree, (bx - 1400, by + 1100),
                        _math(tree, "MULTIPLY", (bx - 1600, by + 1100),
                              drone_r.outputs[0], 1.7).outputs[0],
                        _math(tree, "MULTIPLY", (bx - 1600, by + 1240),
                              drone_r.outputs[0], 1.2).outputs[0],
                        _math(tree, "MULTIPLY", (bx - 1600, by + 1380),
                              drone_r.outputs[0], 3.0).outputs[0], verts=16)
    cup_seated = _xf(tree, (bx - 1200, by + 1100), cup,
                     translation=_vec(tree, (bx - 1200, by + 1240), 0.0, 0.0,
                                      DL)).outputs["Geometry"]
    drone_proto = _join(tree, (bx - 1000, by + 700), [drone_tube, cup_seated])
    drone_span = _math(tree, "MULTIPLY", (bx - 1800, by + 1700), BR, 0.68)
    drones = _stand(tree, (bx - 400, by + 700), gin.outputs["Drone Count"],
                    drone_proto, drone_span.outputs[0], bag_top.outputs[0])

    # blowpipe: a tube leaving the bag's upper -X side, tilted up and out
    blow_len = _math(tree, "MULTIPLY", (bx - 1800, by + 2100), BR, 1.05)
    blow_proto = _cyl_proto_z(tree, (bx - 1400, by + 2100),
                              _math(tree, "MULTIPLY", (bx - 1600, by + 2100),
                                    BR, 0.075).outputs[0],
                              blow_len.outputs[0], verts=12)
    blow = _xf(tree, (bx - 1200, by + 2100), blow_proto,
               rotation=(0.0, math.radians(-50.0), 0.0),
               translation=_vec(tree, (bx - 1200, by + 2240),
                               _math(tree, "MULTIPLY", (bx - 1400, by + 2240),
                                     BR, -0.86).outputs[0], 0.0,
                               bag_z.outputs[0])).outputs["Geometry"]

    geom = _join(tree, (bx + 800, by),
                 [bag_geo, chanter, holes, drones, blow])

    _finish(tree, gin, gout, geom, (bx + 1000, by), BID,
            _attrs(tree, (bx + 800, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bag", "nodes": ("UV Sphere", "Transform"), "role": "geometry"},
        {"title": "Chanter + Hole Rings", "nodes": ("Cone", "Instance on Points"), "role": "geometry"},
        {"title": "Drones + Blowpipe", "nodes": ("Cylinder", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

register_builder(
    "MEL_music_oboe", build_music_oboe, "Oboe",
    "Oboe: conical bore with a flared bell, double reed, eight key cups and two "
    "tenon rings. Native-only.",
    "music",
)
register_builder(
    "MEL_music_bassoon", build_music_bassoon, "Bassoon",
    "Bassoon: folded (U) bore with a bottom bow, flared bell, bocal crook, "
    "double reed and a key rank. Native-only.",
    "music",
)
register_builder(
    "MEL_music_trumpet", build_music_trumpet, "Trumpet",
    "Trumpet: leadpipe, tuning slide with U elbow, a rank of piston valves with "
    "finger buttons, flared bell and mouthpiece. Native-only.",
    "music",
)
register_builder(
    "MEL_music_tuba", build_music_tuba, "Tuba",
    "Tuba: bell-up flare on a main body, bottom bow, side pipe, a rank of four "
    "valves and a mouthpipe. Native-only.",
    "music",
)
register_builder(
    "MEL_music_accordion", build_music_accordion, "Accordion",
    "Accordion: two end boxes with a tilted pleated bellows, a piano-key rank on "
    "the treble box, bass buttons and shoulder straps. Native-only.",
    "music",
)
register_builder(
    "MEL_music_bagpipes", build_music_bagpipes, "Bagpipes",
    "Bagpipes: bag, tapered chanter with hole rings, three graduated drones each "
    "with a top cup, and a blowpipe. Native-only.",
    "music",
)
