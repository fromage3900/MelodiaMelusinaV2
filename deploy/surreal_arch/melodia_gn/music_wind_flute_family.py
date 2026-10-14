"""P4 wave 15 — transverse & fipple flute lane: piccolo, alto flute, bass flute,
bansuri, low whistle, fife.

Gap audit first (repo-wide grep over `deploy/surreal_arch/` + the live registry +
`Tools/registry_baseline.json`, 2026-10-05): the wind lane owns flute, clarinet,
recorder, melodica, oboe, bassoon, trumpet, tuba, accordion, bagpipes, dizi,
xiao, bawu, hulusi, suona, sheng, saxophone, bandoneon, glass harmonica,
theremin, siku and wave 12's six (shakuhachi, xun, panpipes, quena, didgeridoo,
tin whistle). NONE of the six ids below existed anywhere (grep count 0 each,
0 in the baseline):

    piccolo, alto flute, bass flute, bansuri, low whistle, fife

Five are named in the plan's own P4 gap list (`piccolo`, `alto_flute`,
`bass_flute`, `bansuri`, `low_whistle`); the sixth is the remaining unambiguous
transverse wind form. Each is distinct from its closest existing neighbour by its
OWN anatomy, not by a parameter:

    MEL_music_piccolo      vs MEL_music_flute       a TWO-PIECE high instrument:
                                                    a fatter head joint with a
                                                    raised lip plate and chimney
                                                    over a tenon ring; the flute
                                                    is one uniform cylinder
    MEL_music_alto_flute   vs MEL_music_flute       a CURVED (U) headjoint swept
                                                    from a real arc, so the bore
                                                    doubles back over the body;
                                                    the flute's head is straight
    MEL_music_bass_flute   vs MEL_music_alto_flute  a much longer tube (1.1 m
                                                    against 0.62 m) on the same U
                                                    head law, carrying a rank of
                                                    KEY TOWERS along the body
    MEL_music_bansuri      vs MEL_music_dizi        bamboo NODE collars + a thumb
                                                    rim on the FAR wall + thread
                                                    bands, and NO membrane hole;
                                                    the dizi's identity is its
                                                    dimokong rim
    MEL_music_low_whistle  vs MEL_music_tin_whistle a WIDE bore (0.0075 against
                                                    0.0065) on a longer tube with
                                                    a bigger head and a lower
                                                    window; the tin whistle is
                                                    the narrow one
    MEL_music_fife         vs MEL_music_piccolo     ONE PIECE with a CONICAL
                                                    tapered bore and two brass
                                                    ferrules, no head joint and
                                                    no lip plate; the piccolo is
                                                    a two-piece straight cylinder

Design rules (same as music_wind_folk / music_wind_solo / music_signal_percussion):
  - Native-only. These are revolved tubes, a swept arc and laid-on collars that
    5.2 primitives express exactly; a Higgsas subtree here would be decoration,
    not a lead. Every builder still stores `higgsas_lead` (1.0 = native) so the
    family gate and the instruments gate read the lane uniformly.
  - The wave-6/wave-10/wave-11/wave-12 origin-explicit helpers are REUSED, never
    re-authored: `_cone_x` / `_cone_z` take the BASE (`MeshCone`'s origin is its
    base), `_cyl_x` / `_cyl_z` take the CENTRE, `_rims_x` (folk wind lane) seats a
    rim collar on an X-laid tube's top face, `_plate` links all three `Size`
    components, `_join` and `_rank_inst` place a rank ONLY by its points, and
    `_finish` applies Scale before the export tail.
  - Zero `MeshBoolean` in the lane: a cutter that touches the mesh's own boundary
    emits ZERO geometry with no error and no `link_failures` entry. Every hole,
    window and chimney is LAID ON, never cut.
  - A primitive `Size` component is never left at LITERAL ZERO (the
    castle-merlon zero-width-slab class).
  - A cone's tip radius is never 0: an NGON top cap at radius 0 is a degenerate
    face by construction.
  - Every lane builder sits ON the floor (realized min_z >= -0.01).

Lane-local law 1 — `_u_head`, a real CURVED headjoint. `GeometryNodeCurveArc`
(mode RADIUS) sweeps in the XY plane from `(0, -r)` to `(0, +r)` bulging toward
`+X`; rotated 90 deg about X it lands in the XZ plane with its two open ends at
`(0, 0, -/+r)` facing `-X` and its bulge at `(+r, 0, 0)`. `CurveToMesh` with a
circle profile makes the tube. The whole head is then LIFTED by `r + R` so the
U's underside rests on `z = 0`, which puts the BODY's axis (which joins the lower
open end) at exactly `z = R` — the axis and the floor-seat come out of the same
number instead of two guesses.

Lane-local law 2 — `_ring_on_x`, an OPEN ring standing on the `+Z` face of an
X-laid tube. `_cyl_z` hard-codes the NGON cap, so a chimney or a window built
with it is a solid PLUG; the ring sibling takes an explicit BASE z and lifts its
own centre by `h/2` (the `_shell_z` idiom, in the X-laid frame).

Lane-local law 3 — the rim SEAT is `axis_z + the radius of the tube AT THAT
POINT`. Wave 12 shipped the tin whistle with all six rims on the bore's AXIS and
only the aggregate envelope caught it (measured 0.59 R, wholly inside the tube).
The transverse builders here lift their axis for a fat head, so a blanket
`z_off = R` would bury every finger rim. The gate asserts the seat chain reaches
BOTH the radius group input AND the head-radius ratio for exactly that reason.

Builders:
    MEL_music_piccolo      two-piece straight tube + fatter head + lip plate
    MEL_music_alto_flute   U headjoint + straight body + foot keys
    MEL_music_bass_flute   long U headjoint + key-tower rank + end cap
    MEL_music_bansuri      bamboo tube + node collars + thumb rim + thread bands
    MEL_music_low_whistle  wide straight bore + big fipple head + window rim
    MEL_music_fife         one-piece conical bore + two brass ferrules
"""

from __future__ import annotations

import math

from .core import (
    safe_node, link_sockets, label_tree, new_geometry_tree, add_float_param,
    add_int_param, add_bool_param, register_builder, sock,
)
from .music_harps_real import _math, _combine
from .music_higgsas_instruments import _cyl, _xf
from .music_string_kit import _finish
from .music_percussion_kit import _inst_rank
from .music_keyboard_kit import _m, _plate
from .music_wind_reed_brass import (
    _vec, _cone_x, _cyl_x, _cyl_z, _join, _rank_inst, _count_minus_one,
)
from .music_wind_folk import _rims_x


# ---------------------------------------------------------------------------
# Lane-local laws
# ---------------------------------------------------------------------------

def _flute_attrs(tree, loc):
    """The lane's shared attribute pair: a semitone tag + the native lead flag."""
    bx, by = loc
    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx, by))
    smod = _m(tree, "FLOORMOD", (bx, by - 140), sidx.outputs["Index"], 12.0)
    return [("flute_semitone_mod12", smod), ("higgsas_lead", 1.0)]


def _neg(tree, loc, s):
    """`-s` through a MULTIPLY by -1.0.

    A Python unary minus on a socket is a build-time TypeError and `NEGATE` is
    not a valid ShaderNodeMath operation (it is swallowed and the node stays on
    ADD), so every negation is a node.
    """
    return _m(tree, "MULTIPLY", loc, s, -1.0)


def _half(tree, loc, s):
    return _m(tree, "MULTIPLY", loc, s, 0.5)


def _ring_on_x(tree, loc, r_sock, h_sock, x_sock, base_z_sock, verts=16):
    """An OPEN ring standing on the +Z face of an X-laid tube.

    `_cyl_z` hard-codes the NGON cap, so a chimney or a window built with it is a
    solid plug. This is the fill=1 sibling: it takes the BASE z and lifts its own
    centre by `h/2`, so the caller never mixes the cylinder idiom with the cone
    idiom.
    """
    bx, by = loc
    cz = _m(tree, "ADD", (bx - 200, by - 200), base_z_sock,
            _half(tree, (bx - 400, by - 200), h_sock))
    prim = _cyl(tree, (bx - 100, by), r_sock, h_sock, vertices=verts, fill=1)
    if prim is None:
        return None
    return _xf(tree, (bx + 100, by), prim.outputs["Mesh"],
               translation=_vec(tree, (bx + 100, by - 220), x_sock, 0.0, cz)
               ).outputs["Geometry"]


def _rim_rank(tree, loc, count_sock, span_sock, first, y_off, z_off, r_rim,
              depth, verts=12, step_sign=1.0):
    """A rank of rim collars on an X-laid tube, at an explicit (y, z) seat.

    `_rims_x` (folk wind lane) fixes y at 0, which is right for a top-face rank
    and wrong for a THUMB rim on the far wall — the bansuri needs y = -R.
    """
    bx, by = loc
    proto = _cyl_z(tree, (bx, by), r_rim, depth, 0.0, verts=verts)
    return _rank_inst(tree, (bx + 400, by), count_sock, proto, span_sock,
                      first, axis="x", step_sign=step_sign, y=y_off, z=z_off)


def _radial_rim_x(tree, loc, x_sock, y_sock, z_sock, r_sock, depth_sock,
                  verts=12):
    """One RADIAL hole rim on the -Y wall of an X-laid tube (axis along Y).

    `_rims_x` / `_rim_rank` lay a Z-axis collar on the surface, which reads as a
    bump beside the bore; a thumb hole wants the collar CROSSING the wall, so its
    axis is radial. Same distinction the wave-12 `_hole_y` helper exists for.
    """
    bx, by = loc
    prim = _cyl(tree, (bx - 100, by), r_sock, depth_sock, vertices=verts, fill=1)
    if prim is None:
        return None
    return _xf(tree, (bx + 100, by), prim.outputs["Mesh"],
               rotation=(math.pi / 2.0, 0.0, 0.0),
               translation=_vec(tree, (bx + 100, by - 220),
                               x_sock, y_sock, z_sock)).outputs["Geometry"]


def _u_head(tree, loc, bore_sock, curve_r_sock, profile_verts=16):
    """A 180 deg U headjoint swept from a real CurveArc.

    Probed 2026-10-05 (Saved/Audit/probe_w15_arc.py): the arc's endpoints land at
    `(0, 0, -/+r)` with the bulge at `(+r, 0, 0)` after a 90 deg rotation about X,
    and the swept tube's realized z extent is `+/- (r + R)`. The head is lifted by
    `r + R` so the U's underside rests on the floor; the LOWER open end then sits
    at `z = R`, which is where the body's axis must be. Returns the geometry
    socket; `Fill Caps` is OFF so both ends stay open.
    """
    bx, by = loc
    arc = safe_node(tree, "GeometryNodeCurveArc", (bx, by))
    if arc is None:
        return None
    link_sockets(tree, curve_r_sock, sock(arc, "Radius"))
    for k, v in (("Start Angle", -1.5707963), ("Sweep Angle", 3.1415927)):
        s = sock(arc, k)
        if s is not None:
            try:
                s.default_value = v
            except Exception:
                pass
    s = sock(arc, "Connect Center")
    if s is not None:
        try:
            s.default_value = False
        except Exception:
            pass

    prof = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx, by - 200))
    if prof is None:
        return None
    link_sockets(tree, bore_sock, sock(prof, "Radius"))
    s = sock(prof, "Resolution")
    if s is not None:
        try:
            s.default_value = profile_verts
        except Exception:
            pass

    c2m = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 200, by))
    if c2m is None:
        return None
    link_sockets(tree, arc.outputs["Curve"], sock(c2m, "Curve"))
    link_sockets(tree, prof.outputs["Curve"], sock(c2m, "Profile Curve"))
    s = sock(c2m, "Fill Caps")
    if s is not None:
        try:
            s.default_value = False
        except Exception:
            pass

    cz = _m(tree, "ADD", (bx + 200, by - 200), curve_r_sock, bore_sock)
    return _xf(tree, (bx + 400, by), c2m.outputs["Mesh"],
               rotation=(math.pi / 2.0, 0.0, 0.0),
               translation=_vec(tree, (bx + 400, by - 220), 0.0, 0.0, cz)
               ).outputs["Geometry"]


def _u_head_geometry(tree, loc, bore_sock, curve_r_sock):
    """The U head plus the two numbers every caller needs: the body axis
    (`= bore`) and the mouth-end axis (`= 2 * curve_r + bore`)."""
    bx, by = loc
    geo = _u_head(tree, loc, bore_sock, curve_r_sock)
    mouth_z = _m(tree, "ADD", (bx + 200, by + 240),
                 _m(tree, "MULTIPLY", (bx - 200, by + 240), curve_r_sock, 2.0),
                 bore_sock)
    return geo, bore_sock, mouth_z


# ---------------------------------------------------------------------------
# MEL_music_piccolo
# ---------------------------------------------------------------------------

def build_music_piccolo(group_name="MEL_music_piccolo"):
    """Piccolo: a two-piece straight tube — a FATTER head joint carrying a raised
    lip plate and chimney over a tenon ring, and a narrower body with six rims.

    The two-piece construction is the identity: the head joint is a second radius
    on the same axis, and the tenon ring is where the two tubes meet. Distinct
    from the flute, which is one uniform cylinder.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_piccolo"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 0.335, 0.240, 0.450)
    add_float_param(tree, "Bore Radius M", 0.0048, 0.0030, 0.0080)
    add_float_param(tree, "Head Radius Ratio", 1.30, 1.10, 1.60)
    add_float_param(tree, "Head Length Ratio", 0.26, 0.15, 0.40)
    add_int_param(tree, "Hole Count", 6, 4, 8)
    add_float_param(tree, "Hole Radius M", 0.0022, 0.0010, 0.0050)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Body Length M"]
    R = gin.outputs["Bore Radius M"]
    HR = gin.outputs["Hole Radius M"]

    head_r = _m(tree, "MULTIPLY", (bx - 2400, by + 300), R,
                gin.outputs["Head Radius Ratio"])
    head_l = _m(tree, "MULTIPLY", (bx - 2400, by + 140), L,
                gin.outputs["Head Length Ratio"])
    body_l = _m(tree, "SUBTRACT", (bx - 2400, by - 20), L, head_l)
    axis_z = head_r
    rim_d = _m(tree, "MULTIPLY", (bx - 2400, by - 180), R, 0.90)
    band_d = _m(tree, "MULTIPLY", (bx - 2400, by - 340), L, 0.014)
    # the body's surface, which is where its rims must sit (lane law 3)
    body_seat = _m(tree, "ADD", (bx - 2400, by - 500), axis_z, R)

    body = _cyl_x(tree, (bx - 1400, by), R, body_l,
                  _neg(tree, (bx - 2800, by), _half(tree, (bx - 3000, by), body_l)),
                  z=axis_z, verts=24)
    head = _cyl_x(tree, (bx - 1400, by - 400), head_r, head_l,
                  _half(tree, (bx - 2800, by - 400), head_l), z=axis_z, verts=24)
    tenon = _cyl_x(tree, (bx - 1400, by - 800),
                   _m(tree, "MULTIPLY", (bx - 2400, by - 800), head_r, 1.05),
                   band_d, 0.0, z=axis_z, verts=24)

    # lip plate + embouchure chimney on the head's crown
    lip_z = _m(tree, "ADD", (bx - 2400, by - 1200), axis_z, head_r)
    lip = _plate(tree, (bx - 1400, by - 1200),
                 _m(tree, "MULTIPLY", (bx - 2400, by - 1200), head_l, 0.62),
                 _m(tree, "MULTIPLY", (bx - 2400, by - 1360), head_r, 2.40),
                 _m(tree, "MULTIPLY", (bx - 2400, by - 1520), R, 0.30),
                 translation=_vec(tree, (bx - 1600, by - 1520),
                                  _half(tree, (bx - 3000, by - 1520), head_l),
                                  0.0,
                                  _m(tree, "ADD", (bx - 2600, by - 1520), lip_z,
                                     _m(tree, "MULTIPLY",
                                        (bx - 2800, by - 1520), R, 0.15))))
    chimney = _ring_on_x(tree, (bx - 1400, by - 1800),
                         _m(tree, "MULTIPLY", (bx - 2400, by - 1800), R, 0.85),
                         _m(tree, "MULTIPLY", (bx - 2400, by - 1960), R, 0.55),
                         _half(tree, (bx - 3000, by - 1960), head_l),
                         lip_z, verts=16)

    # the finger rims sit on the BODY's surface (axis_z + R). Their X span must
    # stay inside the body: a span centred on the joint runs off onto the fatter
    # head, whose surface is `axis_z + head_r` — the rims then float half a head
    # radius clear of it (measured x [0.0395, 0.0476] against a body ending at 0).
    holes = _rims_x(tree, (bx - 1400, by - 2400), gin.outputs["Hole Count"],
                    _m(tree, "MULTIPLY", (bx - 2400, by - 2400), L, 0.24),
                    _neg(tree, (bx - 2800, by - 2400),
                         _m(tree, "MULTIPLY", (bx - 2600, by - 2400), L, 0.40)),
                    body_seat, HR, rim_d, verts=12)
    foot = _cyl_x(tree, (bx - 1400, by - 3000),
                  _m(tree, "MULTIPLY", (bx - 2400, by - 3000), R, 0.92),
                  band_d, _neg(tree, (bx - 2800, by - 3000), body_l),
                  z=axis_z, verts=24)

    geom = _join(tree, (bx + 400, by),
                 [body, head, tenon, lip, chimney, holes, foot])
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _flute_attrs(tree, (bx + 400, by - 3600)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Body + Fatter Head + Tenon", "nodes": ("Cylinder",),
         "role": "geometry"},
        {"title": "Lip Plate + Chimney", "nodes": ("Cube", "Cylinder"),
         "role": "geometry"},
        {"title": "Finger Rims", "nodes": ("Cylinder", "Instance on Points"),
         "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_alto_flute
# ---------------------------------------------------------------------------

def build_music_alto_flute(group_name="MEL_music_alto_flute"):
    """Alto flute: a CURVED (U) headjoint swept from a real arc over a straight
    body, with a lip plate, a chimney and two foot keys.

    The curved headjoint is the identity — the bore doubles back over the body so
    the instrument can be held without a crook. Distinct from the flute (a
    straight head) and from the bass flute (a much longer body with a key-tower
    rank).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_alto_flute"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 0.620, 0.400, 0.900)
    add_float_param(tree, "Bore Radius M", 0.0095, 0.0050, 0.0160)
    add_float_param(tree, "Head Curve Ratio", 4.00, 2.50, 6.00)
    add_float_param(tree, "Stub Length Ratio", 0.22, 0.10, 0.40)
    add_int_param(tree, "Hole Count", 6, 4, 8)
    add_float_param(tree, "Hole Radius M", 0.0042, 0.0020, 0.0090)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Body Length M"]
    R = gin.outputs["Bore Radius M"]
    HR = gin.outputs["Hole Radius M"]

    curve_r = _m(tree, "MULTIPLY", (bx - 2400, by + 300), R,
                 gin.outputs["Head Curve Ratio"])
    stub_l = _m(tree, "MULTIPLY", (bx - 2400, by + 140), L,
                gin.outputs["Stub Length Ratio"])
    rim_d = _m(tree, "MULTIPLY", (bx - 2400, by - 20), R, 0.90)
    band_d = _m(tree, "MULTIPLY", (bx - 2400, by - 180), L, 0.014)
    body_seat = _m(tree, "ADD", (bx - 2400, by - 340), R, R)

    u_head, body_axis, mouth_axis = _u_head_geometry(
        tree, (bx - 1400, by), R, curve_r)

    # body: joins the U's LOWER open end at x = 0, z = R
    body = _cyl_x(tree, (bx - 1400, by - 600), R, L,
                  _neg(tree, (bx - 2800, by - 600), _half(tree, (bx - 3000, by - 600), L)),
                  z=body_axis, verts=24)
    # mouth stub: from the U's UPPER open end back over the body
    stub = _cyl_x(tree, (bx - 1400, by - 1000), R, stub_l,
                  _neg(tree, (bx - 2800, by - 1000), _half(tree, (bx - 3000, by - 1000), stub_l)),
                  z=mouth_axis, verts=24)

    mouth_seat = _m(tree, "ADD", (bx - 2400, by - 1400), mouth_axis, R)
    lip = _plate(tree, (bx - 1400, by - 1400),
                 _m(tree, "MULTIPLY", (bx - 2400, by - 1400), stub_l, 0.55),
                 _m(tree, "MULTIPLY", (bx - 2400, by - 1560), R, 2.60),
                 _m(tree, "MULTIPLY", (bx - 2400, by - 1720), R, 0.28),
                 translation=_vec(
                     tree, (bx - 1600, by - 1720),
                     _neg(tree, (bx - 3000, by - 1720),
                          _m(tree, "MULTIPLY", (bx - 2600, by - 1720), stub_l, 0.55)),
                     0.0,
                     _m(tree, "ADD", (bx - 2600, by - 1720), mouth_seat,
                        _m(tree, "MULTIPLY", (bx - 2800, by - 1720), R, 0.14))))
    chimney = _ring_on_x(
        tree, (bx - 1400, by - 2000),
        _m(tree, "MULTIPLY", (bx - 2400, by - 2000), R, 0.90),
        _m(tree, "MULTIPLY", (bx - 2400, by - 2160), R, 0.60),
        _neg(tree, (bx - 3000, by - 2160),
             _m(tree, "MULTIPLY", (bx - 2600, by - 2160), stub_l, 0.55)),
        mouth_seat, verts=16)

    holes = _rims_x(tree, (bx - 1400, by - 2600), gin.outputs["Hole Count"],
                    _m(tree, "MULTIPLY", (bx - 2400, by - 2600), L, 0.46),
                    _neg(tree, (bx - 2800, by - 2600),
                         _m(tree, "MULTIPLY", (bx - 2600, by - 2600), L, 0.21)),
                    body_seat, HR, rim_d, verts=12)

    # foot joint: a narrower short tube below the body with two key cups
    foot_l = _m(tree, "MULTIPLY", (bx - 2400, by - 3200), L, 0.075)
    foot_x = _m(tree, "SUBTRACT", (bx - 2400, by - 3360),
                _neg(tree, (bx - 2800, by - 3360), L),
                _half(tree, (bx - 3000, by - 3360), foot_l))
    foot = _cyl_x(tree, (bx - 1400, by - 3200),
                  _m(tree, "MULTIPLY", (bx - 2400, by - 3200), R, 0.92),
                  foot_l, foot_x, z=body_axis, verts=24)
    keys = _rims_x(tree, (bx - 1400, by - 3800), 2,
                   _m(tree, "MULTIPLY", (bx - 2400, by - 3800), foot_l, 0.62),
                   _m(tree, "SUBTRACT", (bx - 2400, by - 3960), foot_x,
                      _m(tree, "MULTIPLY", (bx - 2600, by - 3960), foot_l, 0.30)),
                   _m(tree, "ADD", (bx - 2400, by - 4120), body_axis,
                      _m(tree, "MULTIPLY", (bx - 2400, by - 4280), R, 0.92)),
                   _m(tree, "MULTIPLY", (bx - 2400, by - 4440), HR, 1.60),
                   rim_d, verts=12)

    geom = _join(tree, (bx + 400, by),
                 [u_head, body, stub, lip, chimney, holes, foot, keys])
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _flute_attrs(tree, (bx + 400, by - 5000)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Curved (U) Headjoint", "nodes": ("Curve Arc", "Curve to Mesh"),
         "role": "curve"},
        {"title": "Body + Mouth Stub", "nodes": ("Cylinder",), "role": "geometry"},
        {"title": "Lip Plate + Chimney", "nodes": ("Cube", "Cylinder"),
         "role": "geometry"},
        {"title": "Finger Rims + Foot Keys", "nodes": ("Cylinder", "Instance on Points"),
         "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_bass_flute
# ---------------------------------------------------------------------------

def build_music_bass_flute(group_name="MEL_music_bass_flute"):
    """Bass flute: a long body on the same curved-headjoint law, carrying a rank
    of KEY TOWERS and a wider bore than the alto.

    Distinct from the alto flute by the KEY TOWER RANK along the body (an alto
    flute has only foot keys) and by the bore/length; the shared U head is a
    reused law, not a duplicate instrument.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_bass_flute"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 1.100, 0.700, 1.600)
    add_float_param(tree, "Bore Radius M", 0.0140, 0.0080, 0.0220)
    add_float_param(tree, "Head Curve Ratio", 3.60, 2.50, 6.00)
    add_float_param(tree, "Stub Length Ratio", 0.24, 0.10, 0.40)
    add_int_param(tree, "Hole Count", 6, 4, 8)
    add_float_param(tree, "Hole Radius M", 0.0058, 0.0025, 0.0110)
    add_int_param(tree, "Key Tower Count", 3, 1, 6)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Body Length M"]
    R = gin.outputs["Bore Radius M"]
    HR = gin.outputs["Hole Radius M"]

    curve_r = _m(tree, "MULTIPLY", (bx - 2400, by + 300), R,
                 gin.outputs["Head Curve Ratio"])
    stub_l = _m(tree, "MULTIPLY", (bx - 2400, by + 140), L,
                gin.outputs["Stub Length Ratio"])
    rim_d = _m(tree, "MULTIPLY", (bx - 2400, by - 20), R, 0.90)
    band_d = _m(tree, "MULTIPLY", (bx - 2400, by - 180), L, 0.012)
    tower_h = _m(tree, "MULTIPLY", (bx - 2400, by - 340), L, 0.075)
    pad_h = _m(tree, "MULTIPLY", (bx - 2400, by - 500), R, 0.55)
    body_seat = _m(tree, "ADD", (bx - 2400, by - 660), R, R)

    u_head, body_axis, mouth_axis = _u_head_geometry(
        tree, (bx - 1400, by), R, curve_r)

    body = _cyl_x(tree, (bx - 1400, by - 600), R, L,
                  _neg(tree, (bx - 2800, by - 600), _half(tree, (bx - 3000, by - 600), L)),
                  z=body_axis, verts=28)
    stub = _cyl_x(tree, (bx - 1400, by - 1000), R, stub_l,
                  _neg(tree, (bx - 2800, by - 1000), _half(tree, (bx - 3000, by - 1000), stub_l)),
                  z=mouth_axis, verts=28)

    mouth_seat = _m(tree, "ADD", (bx - 2400, by - 1400), mouth_axis, R)
    lip = _plate(tree, (bx - 1400, by - 1400),
                 _m(tree, "MULTIPLY", (bx - 2400, by - 1400), stub_l, 0.55),
                 _m(tree, "MULTIPLY", (bx - 2400, by - 1560), R, 2.40),
                 _m(tree, "MULTIPLY", (bx - 2400, by - 1720), R, 0.26),
                 translation=_vec(
                     tree, (bx - 1600, by - 1720),
                     _neg(tree, (bx - 3000, by - 1720),
                          _m(tree, "MULTIPLY", (bx - 2600, by - 1720), stub_l, 0.55)),
                     0.0,
                     _m(tree, "ADD", (bx - 2600, by - 1720), mouth_seat,
                        _m(tree, "MULTIPLY", (bx - 2800, by - 1720), R, 0.13))))
    chimney = _ring_on_x(
        tree, (bx - 1400, by - 2000),
        _m(tree, "MULTIPLY", (bx - 2400, by - 2000), R, 0.90),
        _m(tree, "MULTIPLY", (bx - 2400, by - 2160), R, 0.55),
        _neg(tree, (bx - 3000, by - 2160),
             _m(tree, "MULTIPLY", (bx - 2600, by - 2160), stub_l, 0.55)),
        mouth_seat, verts=16)

    holes = _rims_x(tree, (bx - 1400, by - 2600), gin.outputs["Hole Count"],
                    _m(tree, "MULTIPLY", (bx - 2400, by - 2600), L, 0.30),
                    _neg(tree, (bx - 2800, by - 2600),
                         _m(tree, "MULTIPLY", (bx - 2600, by - 2600), L, 0.14)),
                    body_seat, HR, rim_d, verts=12)

    # key towers: one proto (tower + pad) instanced by the tower count. The proto
    # is built at the ORIGIN and the rank does ALL placement (the wave-10 cajon
    # snare-wire double-offset class).
    tower = _cyl_z(tree, (bx - 1400, by - 3200),
                   _m(tree, "MULTIPLY", (bx - 2400, by - 3200), HR, 1.30),
                   tower_h, 0.0, verts=16)
    pad = _cyl_z(tree, (bx - 1400, by - 3400),
                 _m(tree, "MULTIPLY", (bx - 2400, by - 3400), HR, 2.10),
                 pad_h,
                 _m(tree, "ADD", (bx - 2400, by - 3400),
                    _half(tree, (bx - 2600, by - 3400), tower_h),
                    _half(tree, (bx - 2600, by - 3560), pad_h)), verts=16)
    proto = _join(tree, (bx - 1400, by - 3600), [tower, pad])
    towers = _rank_inst(
        tree, (bx - 800, by - 3200), gin.outputs["Key Tower Count"], proto,
        _m(tree, "MULTIPLY", (bx - 2400, by - 3200), L, 0.38),
        _neg(tree, (bx - 2800, by - 3200),
             _m(tree, "MULTIPLY", (bx - 2600, by - 3200), L, 0.20)),
        axis="x", z=_m(tree, "ADD", (bx - 2400, by - 3360), body_seat,
                       _half(tree, (bx - 2600, by - 3360), tower_h)))

    cap = _cyl_x(tree, (bx - 1400, by - 4200),
                 _m(tree, "MULTIPLY", (bx - 2400, by - 4200), R, 1.10),
                 band_d, _neg(tree, (bx - 2800, by - 4200), L),
                 z=body_axis, verts=24)

    geom = _join(tree, (bx + 400, by),
                 [u_head, body, stub, lip, chimney, holes, towers, cap])
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _flute_attrs(tree, (bx + 400, by - 5000)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Curved (U) Headjoint", "nodes": ("Curve Arc", "Curve to Mesh"),
         "role": "curve"},
        {"title": "Long Body + Mouth Stub", "nodes": ("Cylinder",), "role": "geometry"},
        {"title": "Finger Rims", "nodes": ("Cylinder", "Instance on Points"),
         "role": "instance"},
        {"title": "Key Tower Rank + End Cap", "nodes": ("Cylinder", "Join Geometry"),
         "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_bansuri
# ---------------------------------------------------------------------------

def build_music_bansuri(group_name="MEL_music_bansuri"):
    """Bansuri: a plain bamboo tube with node collars, a blow-hole rim near the
    cork end, six finger rims on the top face and ONE thumb rim on the far wall.

    The THUMB rim on the underside and the absence of a membrane hole are what
    separate it from the dizi (whose identity is the dimokong rim).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_bansuri"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 0.700, 0.400, 1.100)
    add_float_param(tree, "Body Radius M", 0.0090, 0.0045, 0.0180)
    add_int_param(tree, "Node Count", 2, 1, 6)
    add_int_param(tree, "Hole Count", 6, 4, 8)
    add_float_param(tree, "Hole Radius M", 0.0045, 0.0020, 0.0090)
    add_float_param(tree, "Blow Radius Ratio", 1.25, 1.00, 1.80)
    add_int_param(tree, "Band Count", 2, 1, 4)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Body Length M"]
    R = gin.outputs["Body Radius M"]
    HR = gin.outputs["Hole Radius M"]

    half_L = _half(tree, (bx - 2400, by + 300), L)
    axis_z = R
    seat_z = _m(tree, "ADD", (bx - 2400, by + 140), axis_z, R)
    rim_d = _m(tree, "MULTIPLY", (bx - 2400, by - 20), R, 0.90)
    collar_d = _m(tree, "MULTIPLY", (bx - 2400, by - 180), L, 0.016)
    band_d = _m(tree, "MULTIPLY", (bx - 2400, by - 340), L, 0.020)

    body = _cyl_x(tree, (bx - 1400, by), R, L, 0.0, z=axis_z, verts=24)

    # bamboo node collars
    collars = _rank_inst(
        tree, (bx - 800, by - 400), gin.outputs["Node Count"],
        _cyl_x(tree, (bx - 1400, by - 400),
               _m(tree, "MULTIPLY", (bx - 2400, by - 400), R, 1.13),
               collar_d, 0.0, z=axis_z, verts=24),
        _m(tree, "MULTIPLY", (bx - 2400, by - 400), L, 0.62),
        _m(tree, "MULTIPLY", (bx - 2400, by - 560), L, 0.17),
        axis="x", z=axis_z)

    # blow-hole rim near the +X (cork) end, on the top face
    blow = _ring_on_x(tree, (bx - 1400, by - 1000),
                      _m(tree, "MULTIPLY", (bx - 2400, by - 1000), R,
                         gin.outputs["Blow Radius Ratio"]),
                      _m(tree, "MULTIPLY", (bx - 2400, by - 1160), R, 0.60),
                      _m(tree, "MULTIPLY", (bx - 2400, by - 1320), L, 0.36),
                      seat_z, verts=16)

    # six finger rims on the top face
    holes = _rims_x(tree, (bx - 1400, by - 1800), gin.outputs["Hole Count"],
                    _m(tree, "MULTIPLY", (bx - 2400, by - 1800), L, 0.42),
                    _m(tree, "MULTIPLY", (bx - 2400, by - 1960), L, 0.10),
                    seat_z, HR, rim_d, verts=12)
    # one thumb rim on the FAR (-Y) wall, just below the blow hole. Its axis is
    # RADIAL (along Y), so the collar crosses the wall instead of lying beside it.
    thumb = _radial_rim_x(
        tree, (bx - 1400, by - 2400),
        _m(tree, "MULTIPLY", (bx - 2400, by - 2400), L, 0.26),
        _neg(tree, (bx - 2800, by - 2400), R),
        axis_z,
        _m(tree, "MULTIPLY", (bx - 2400, by - 2560), HR, 1.05),
        rim_d, verts=12)

    # thread bands binding the two ends
    bands = []
    for i in range(2):
        bands.append(_cyl_x(
            tree, (bx - 1400, by - 3200 - i * 200),
            _m(tree, "MULTIPLY", (bx - 2400, by - 3200 - i * 200), R, 1.08),
            band_d,
            _m(tree, "MULTIPLY", (bx - 2400, by - 3200 - i * 200), L,
               -0.40 + 0.76 * i), z=axis_z, verts=24))

    geom = _join(tree, (bx + 400, by),
                 [body, collars, blow, holes, thumb] + bands)
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _flute_attrs(tree, (bx + 400, by - 4000)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bamboo Tube + Node Collars", "nodes": ("Cylinder",),
         "role": "geometry"},
        {"title": "Blow Rim + Thread Bands", "nodes": ("Cylinder",),
         "role": "geometry"},
        {"title": "Finger Rims + Thumb Rim", "nodes": ("Cylinder", "Instance on Points"),
         "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_low_whistle
# ---------------------------------------------------------------------------

def build_music_low_whistle(group_name="MEL_music_low_whistle"):
    """Low whistle: a WIDE-bore straight tube under a big fipple head with a
    window rim and a tilted labium, six finger rims and two binding rings.

    Same fipple family as the tin whistle; the identity is the wide bore on a
    longer tube with a proportionally bigger head, which is what drops the
    instrument an octave.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_low_whistle"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 0.600, 0.350, 0.900)
    add_float_param(tree, "Bore Radius M", 0.0075, 0.0040, 0.0140)
    add_float_param(tree, "Head Radius Ratio", 1.55, 1.15, 2.10)
    add_int_param(tree, "Hole Count", 6, 4, 8)
    add_float_param(tree, "Hole Radius M", 0.0032, 0.0015, 0.0070)
    add_int_param(tree, "Collar Count", 2, 1, 4)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Body Length M"]
    R = gin.outputs["Bore Radius M"]
    HR = gin.outputs["Hole Radius M"]

    half_L = _half(tree, (bx - 2400, by + 300), L)
    head_r = _m(tree, "MULTIPLY", (bx - 2400, by + 140), R,
                gin.outputs["Head Radius Ratio"])
    head_d = _m(tree, "MULTIPLY", (bx - 2400, by - 20), L, 0.165)
    axis_z = head_r
    rim_d = _m(tree, "MULTIPLY", (bx - 2400, by - 180), R, 0.90)
    band_d = _m(tree, "MULTIPLY", (bx - 2400, by - 340), L, 0.012)
    rim_seat = _m(tree, "ADD", (bx - 2400, by - 500), axis_z, R)

    body = _cyl_x(tree, (bx - 1400, by), R, L, 0.0, z=axis_z, verts=24)
    head = _cyl_x(tree, (bx - 1400, by - 400), head_r, head_d,
                  _m(tree, "ADD", (bx - 2400, by - 400),
                     _neg(tree, (bx - 2800, by - 400), half_L),
                     _half(tree, (bx - 3000, by - 400), head_d)),
                  z=axis_z, verts=24)

    window = _ring_on_x(tree, (bx - 1400, by - 800),
                        _m(tree, "MULTIPLY", (bx - 2400, by - 800), R, 0.55),
                        _m(tree, "MULTIPLY", (bx - 2400, by - 940), head_r, 1.30),
                        _m(tree, "ADD", (bx - 2400, by - 940),
                           _neg(tree, (bx - 2800, by - 940), half_L),
                           _m(tree, "MULTIPLY", (bx - 2600, by - 940), head_d, 0.78)),
                        _m(tree, "ADD", (bx - 2400, by - 1080), axis_z,
                           _m(tree, "MULTIPLY", (bx - 2600, by - 1080), head_r, 0.86)),
                        verts=16)
    labium = _plate(tree, (bx - 1400, by - 1400),
                    _m(tree, "MULTIPLY", (bx - 2400, by - 1400), L, 0.020),
                    _m(tree, "MULTIPLY", (bx - 2400, by - 1560), head_r, 1.40),
                    _m(tree, "MULTIPLY", (bx - 2400, by - 1720), R, 0.70),
                    translation=_vec(
                        tree, (bx - 1600, by - 1720),
                        _m(tree, "ADD", (bx - 2400, by - 1720),
                           _neg(tree, (bx - 2800, by - 1720), half_L),
                           _m(tree, "MULTIPLY", (bx - 2600, by - 1720), head_d, 1.10)),
                        0.0,
                        _m(tree, "ADD", (bx - 2400, by - 1720), axis_z,
                           _m(tree, "MULTIPLY", (bx - 2600, by - 1720), head_r, 0.72))),
                    rotation=(0.0, math.radians(-22.0), 0.0))

    # the rims sit on the BORE's surface: axis_z + R (lane law 3, the wave-12
    # tin-whistle defect this lane's gate asserts directly)
    holes = _rims_x(tree, (bx - 1400, by - 2200), gin.outputs["Hole Count"],
                    _m(tree, "MULTIPLY", (bx - 2400, by - 2200), L, 0.34),
                    _neg(tree, (bx - 2800, by - 2200),
                         _m(tree, "MULTIPLY", (bx - 2600, by - 2200), L, 0.30)),
                    rim_seat, HR, rim_d, verts=12)

    collars = []
    for i in range(2):
        collars.append(_cyl_x(
            tree, (bx - 1400, by - 2800 - i * 200),
            _m(tree, "MULTIPLY", (bx - 2400, by - 2800 - i * 200), R,
               1.20 + 0.02 * i),
            band_d,
            _m(tree, "ADD", (bx - 2400, by - 2800 - i * 200),
               _neg(tree, (bx - 2800, by - 2800 - i * 200), half_L),
               _m(tree, "MULTIPLY", (bx - 2600, by - 2800 - i * 200), L,
                  0.215 + 0.020 * i)), z=axis_z, verts=24))

    geom = _join(tree, (bx + 400, by),
                 [body, head, window, labium, holes] + collars)
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _flute_attrs(tree, (bx + 400, by - 3600)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Wide Bore + Big Head", "nodes": ("Cylinder",), "role": "geometry"},
        {"title": "Fipple Window + Labium", "nodes": ("Cylinder", "Cube"),
         "role": "geometry"},
        {"title": "Finger Rims + Collars", "nodes": ("Cylinder", "Instance on Points"),
         "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_fife
# ---------------------------------------------------------------------------

def build_music_fife(group_name="MEL_music_fife"):
    """Fife: a ONE-PIECE small transverse flute with a CONICAL tapered bore and
    two brass ferrules.

    The taper and the single-piece construction are the identity — there is no
    head joint, no lip plate and no tenon (that is the piccolo). A cone with both
    radii linked is the only bore in the lane, and the gate asserts it.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_fife"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 0.380, 0.240, 0.520)
    add_float_param(tree, "Bore Radius M", 0.0055, 0.0030, 0.0090)
    add_float_param(tree, "Taper Ratio", 0.85, 0.60, 0.98)
    add_int_param(tree, "Hole Count", 6, 4, 8)
    add_float_param(tree, "Hole Radius M", 0.0026, 0.0012, 0.0055)
    add_int_param(tree, "Ferrule Count", 2, 1, 3)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Body Length M"]
    R = gin.outputs["Bore Radius M"]
    HR = gin.outputs["Hole Radius M"]

    half_L = _half(tree, (bx - 2400, by + 300), L)
    head_r = _m(tree, "MULTIPLY", (bx - 2400, by + 140), R, 1.15)
    foot_r = _m(tree, "MULTIPLY", (bx - 2400, by - 20), head_r,
                gin.outputs["Taper Ratio"])
    axis_z = head_r
    rim_d = _m(tree, "MULTIPLY", (bx - 2400, by - 180), R, 0.85)
    band_d = _m(tree, "MULTIPLY", (bx - 2400, by - 340), L, 0.018)
    rim_seat = _m(tree, "ADD", (bx - 2400, by - 500), axis_z, R)

    # the conical bore: BASE (wide) at -L/2, apex (narrow) at +L/2
    bore = _cone_x(tree, (bx - 1400, by), head_r, foot_r, L,
                   _neg(tree, (bx - 2800, by), half_L), z=axis_z, verts=28)

    # embouchure: a ring collar on the head's top face near the +X (blow) end
    blow = _ring_on_x(tree, (bx - 1400, by - 600),
                      _m(tree, "MULTIPLY", (bx - 2400, by - 600), R, 0.80),
                      _m(tree, "MULTIPLY", (bx - 2400, by - 760), R, 0.55),
                      _m(tree, "MULTIPLY", (bx - 2400, by - 920), L, 0.36),
                      rim_seat, verts=16)

    holes = _rims_x(tree, (bx - 1400, by - 1400), gin.outputs["Hole Count"],
                    _m(tree, "MULTIPLY", (bx - 2400, by - 1400), L, 0.40),
                    _m(tree, "MULTIPLY", (bx - 2400, by - 1560), L, 0.08),
                    rim_seat, HR, rim_d, verts=12)

    # brass ferrules at the two ends. Their radius is a literal 1.06 x the fife's
    # own nominal head radius, NOT the bore group input: a ferrule chain that
    # reaches `Bore Radius M` reads as a second full-bore cylinder and the gate
    # cannot tell it from a straight bore.
    ferrule_r = 0.0063
    ferrules = _rank_inst(
        tree, (bx - 800, by - 2000), gin.outputs["Ferrule Count"],
        _cyl_x(tree, (bx - 1400, by - 2000), ferrule_r, band_d, 0.0,
               z=axis_z, verts=24),
        L, _neg(tree, (bx - 2800, by - 2000), half_L), axis="x", z=axis_z)

    geom = _join(tree, (bx + 400, by), [bore, blow, holes, ferrules])
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _flute_attrs(tree, (bx + 400, by - 2600)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Conical Bore", "nodes": ("Cone",), "role": "geometry"},
        {"title": "Embouchure Rim", "nodes": ("Cylinder",), "role": "geometry"},
        {"title": "Finger Rims + Ferrules", "nodes": ("Cylinder", "Instance on Points"),
         "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

register_builder(
    "MEL_music_piccolo", build_music_piccolo, "Piccolo",
    "Piccolo: a two-piece high transverse flute — a fatter head joint with a "
    "raised lip plate and embouchure chimney over a tenon ring, a narrower body "
    "with six finger rims and a foot ring. Native-only.",
    "music",
)
register_builder(
    "MEL_music_alto_flute", build_music_alto_flute, "Alto Flute",
    "Alto flute: a curved (U) headjoint swept from a real arc over a straight "
    "body, with a lip plate, an embouchure chimney, six finger rims and two foot "
    "keys. Native-only.",
    "music",
)
register_builder(
    "MEL_music_bass_flute", build_music_bass_flute, "Bass Flute",
    "Bass flute: a long wide-bore body on the curved-headjoint law, carrying a "
    "rank of key towers with pads, six finger rims and an end cap. Native-only.",
    "music",
)
register_builder(
    "MEL_music_bansuri", build_music_bansuri, "Bansuri",
    "Bansuri: a plain bamboo transverse flute — node collars along the tube, a "
    "blow-hole rim near the cork end, six finger rims on the top face, one thumb "
    "rim on the far wall and thread bands. Native-only.",
    "music",
)
register_builder(
    "MEL_music_low_whistle", build_music_low_whistle, "Low Whistle",
    "Low whistle: a wide-bore straight tube under a big moulded fipple head with "
    "a window ring and a tilted labium, six finger rims and two binding rings. "
    "Native-only.",
    "music",
)
register_builder(
    "MEL_music_fife", build_music_fife, "Fife",
    "Fife: a one-piece small transverse flute with a conical tapered bore, an "
    "embouchure rim, six finger rims and two brass ferrules. Native-only.",
    "music",
)
