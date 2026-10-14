"""P4 wave 14 — frame & signal percussion lane: temple block, ratchet, bodhran,
slapstick, slit drum, handpan.

Gap audit first (repo-wide grep over `deploy/surreal_arch/` + the live registry +
`Tools/registry_baseline.json`, 2026-10-05): the percussion lane owns timpani,
snare drum, bass drum, cymbals, tambourine, carillon, steelpan, gong, ocarina,
glockenspiel, celesta, marimba, vibraphone, tubular bells, wave 10's six hand
drums (djembe, congas, bongos, cajon, frame drum, tabla), wave 11's six
auxiliary pieces (tom-tom, xylophone, washboard, claves, cabasa, guiro) and
wave 13's six small hand pieces (maracas, wood block, cowbell, castanets,
shaker, vibraslap). NONE of the six ids below existed anywhere (grep count 0
each, 0 in the baseline):

    temple block, ratchet, bodhran, slapstick, slit drum, handpan

Four are named in the plan's own P4 gap list (`temple_block`, `ratchet`,
`bodhran`, `slapstick`); the other two are the remaining unambiguous percussion
forms. Each is distinct from its closest existing neighbour by its OWN anatomy,
not by a parameter:

    MEL_music_temple_block vs MEL_music_wood_block  a FISH-shaped hollow block
                                                    with a rounded belly, a
                                                    slotted mouth on the crown
                                                    and a stand rail; the wood
                                                    block is a plain slotted box
    MEL_music_ratchet      vs MEL_music_vibraslap   a TOOTHED WHEEL on an axle
                                                    inside a frame, driven by a
                                                    crank and stopped by a
                                                    sprung tongue; the vibraslap
                                                    is a toothed box on a BENT rod
    MEL_music_bodhran      vs MEL_music_frame_drum  a DEEP shell with TWO crossed
                                                    internal bars, tuning lugs
                                                    and a tipper resting on the
                                                    head; the frame drum is a
                                                    shallow braced ring
    MEL_music_slapstick    vs MEL_music_claves      two boards HINGED at one end
                                                    about a real pin, with a
                                                    handle; the claves are two
                                                    loose solid rods
    MEL_music_slit_drum    vs MEL_music_cajon       a hollow LOG with a
                                                    longitudinal SLIT between two
                                                    UNEQUAL lips; the cajon is a
                                                    closed box with a tapa plate
    MEL_music_handpan      vs MEL_music_steelpan    a convex hammered DOME with a
                                                    central ding and a radial rank
                                                    of dimpled tone fields; the
                                                    steelpan is a concave open pan

Design rules (same as music_world_percussion / music_aux_percussion /
music_aux_percussion2 / music_wind_solo):
  - Native-only. These are revolved shells, plates, wheels and bars that 5.2
    primitives express exactly; a Higgsas subtree here would be decoration, not a
    lead. Every builder still stores `higgsas_lead` (1.0 = native) so the family
    gate and the instruments gate read the lane uniformly.
  - The wave-6/wave-10/wave-11 origin-explicit helpers are REUSED, never
    re-authored: `_cone_x` / `_cone_z` take the BASE (`MeshCone`'s origin is its
    base), `_cyl_x` / `_cyl_z` take the CENTRE, `_sphere` takes its centre,
    `_shell_z` / `_disc_z` / `_ring_rank` / `_tube_y` / `_mean_r` come from the
    world-percussion lane, `_plate` links all three `Size` components, `_join`
    and `_rank_inst` place a rank ONLY by its points, `_finish` applies Scale.
  - Zero `MeshBoolean` in the lane: a cutter that touches the mesh's own boundary
    emits ZERO geometry with no error and no `link_failures` entry. Every slit,
    mouth, port and dimple is LAID ON, never cut.
  - A primitive `Size` component is never left at LITERAL ZERO (the
    castle-merlon zero-width-slab class).
  - A cone's tip radius is never 0: an NGON top cap at radius 0 is a degenerate
    face by construction.
  - Every lane builder sits ON the floor (realized min_z >= -0.01).

Lane-local law 1 — `_hinge_pair`, two boards joined at one end about a REAL pin.
A slapstick's identity is that one board swings; the moving board's Transform
rotation traces to the `Hinge Angle` group input (a literal rotation tuple lands
in `default_value`, not in a link, so the gate reads the link FIRST and falls
back to the default — the wave-6/wave-10 lesson).

Lane-local law 2 — `_cross_bars`, a bodhran's internal bars. Two bars at 90 deg
spanning the shell's INNER diameter, seated at the mean of the shell's two rim
depths (a bar seated at one rim's depth hangs off the other). The bar length is
derived from the shell's ACTUAL inner radius, never from the count x a constant
(the wave-12 panpipes binding-cord defect).

Lane-local law 3 — `_unequal_lips`, a slit drum's two lips. A real slit drum's
lips are deliberately UNEQUAL (the wider lip sounds the lower pitch), so the two
plates' widths trace to `Lip Ratio` through opposite factors and the gate asserts
BOTH the ratio link AND that the two widths differ.

Lane-local law 4 — `_tone_field_ring`, the handpan's dimpled tone fields. The
dome is a scaled UV sphere, so the surface height at radial distance d is
`Rz * sqrt(1 - (d/Rx)^2)`, NOT the crown height: a constant-z seat floats the
fields off the shell (the wave-12 vessel law, same class as the xun's band). The
seat is a real SQRT chain and the gate asserts the SQRT operation took (an
unswallowed bad op name is how NEGATE silently stayed on ADD).

Builders:
    MEL_music_temple_block fish-shaped hollow block + slotted mouth + stand rail
    MEL_music_ratchet      toothed wheel + axle + frame + crank + sprung tongue
    MEL_music_bodhran      deep shell + head + two crossed bars + lugs + tipper
    MEL_music_slapstick    two hinged boards + pin + handle
    MEL_music_slit_drum    hollow log + unequal slit lips + end caps
    MEL_music_handpan      convex dome + central ding + radial tone fields + port
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
    _vec, _sphere, _cone_x, _cyl_x, _cone_z, _cyl_z, _join, _rank_inst,
    _rank_axis, _half_span, _count_minus_one,
)
from .music_world_percussion import _shell_z, _disc_z, _ring_rank, _tube_y


# ---------------------------------------------------------------------------
# Lane-local laws
# ---------------------------------------------------------------------------

def _perc_attrs(tree, loc):
    """The lane's shared attribute pair: a semitone tag + the native lead flag."""
    bx, by = loc
    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx, by))
    smod = _m(tree, "MODULO", (bx, by - 140), sidx.outputs["Index"], 12.0)
    return [("drum_semitone_mod12", smod), ("higgsas_lead", 1.0)]


def _disc_y(tree, loc, r_sock, t_sock, cy, x=0.0, z=0.0, verts=32):
    """A solid disc (NGON cap) lying in the XZ plane, centred at `cy`.

    `_tube_y` is the OPEN sibling; a ratchet WHEEL must be solid, so this is the
    NGON-capped one. `MeshCylinder`'s origin is its centre, so the disc is built
    at the origin, laid onto Y and translated once.
    """
    prim = _cyl(tree, (loc[0] - 100, loc[1]), r_sock, t_sock,
                vertices=verts, fill=2)
    if prim is None:
        return None
    return _xf(tree, (loc[0] + 100, loc[1]), prim.outputs["Mesh"],
               rotation=(1.5707963, 0.0, 0.0),
               translation=_vec(tree, (loc[0] + 100, loc[1] - 220),
                               x, cy, z)).outputs["Geometry"]


def _neg(tree, loc, s):
    """`-s` through a MULTIPLY by -1.0.

    A Python unary minus on a socket is a build-time TypeError, and `NEGATE` is
    not a valid ShaderNodeMath operation (it is swallowed and the node stays on
    ADD), so negation is always a node.
    """
    return _m(tree, "MULTIPLY", loc, s, -1.0)


def _radial_ring_xz(tree, loc, count_sock, proto_geo, radius_sock,
                    cx=0.0, cz=0.0):
    """A radial rank in the XZ plane — a VERTICAL ring, for a wheel's rim.

    `_ring_rank` (world-percussion lane) builds its `MeshCircle` in the XY plane,
    which is right for a handpan's horizontal tone fields or a bodhran's lug band
    and WRONG for a wheel: the ratchet's teeth came out as a flat horizontal
    crown at the axle height (measured Y band 0.068 against a Z extent of 0.0147,
    i.e. every tooth at the same z) instead of a ring around the disc's rim.
    Rotating the circle 90 deg about X puts it in the XZ plane, matching the
    disc's own axis (a `MeshCylinder` rotated onto Y).
    """
    bx, by = loc
    circ = safe_node(tree, "GeometryNodeMeshCircle", (bx, by))
    if circ is None:
        return None
    try:
        circ.fill_type = "NONE"
    except Exception:
        pass
    link_sockets(tree, count_sock, sock(circ, "Vertices"))
    link_sockets(tree, radius_sock, sock(circ, "Radius"))
    pts = safe_node(tree, "GeometryNodeMeshToPoints", (bx + 200, by))
    if pts is None:
        return None
    link_sockets(tree, circ.outputs["Mesh"], sock(pts, "Mesh"))
    place = _xf(tree, (bx + 400, by), pts.outputs["Points"],
                rotation=_vec(tree, (bx + 400, by - 140), math.pi / 2.0, 0.0,
                              0.0),
                translation=_vec(tree, (bx + 400, by - 220), cx, 0.0, cz))
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 600, by))
    if inst is None:
        return None
    link_sockets(tree, place.outputs["Geometry"], sock(inst, "Points"))
    link_sockets(tree, proto_geo, sock(inst, "Instance"))
    return inst.outputs["Instances"]


def _hinge_pair(tree, loc, half_w_sock, board_l_sock, board_t_sock, gap_sock,
                angle_sock, base_z, pin_r=0.006):
    """Two boards joined at one end about a REAL pin — the slapstick law.

    The hinge line is the pair's common end at `-half_w`; the FIXED board runs
    from the hinge toward +X, and the MOVING board is authored at the hinge and
    rotated about Y so its free end LIFTS. Returns `(fixed, moving, pin, mid_z)`.

    TWO things this helper must get right, both measured:

    (a) the swing must lift, not dip. A rotation about +Y by a POSITIVE angle
        takes +X toward -Z, so the free end goes DOWN through the floor; the
        angle is therefore negated (`-angle_sock`) and the free end rises.
    (b) `base_z` is the axis height the whole assembly shares. A board seated at
        `T/2 + pin_r` above z = 0 still puts the PIN, the HANDLE and the GRIP on
        the axis z = 0, so each of them hangs its own radius below the floor
        (measured -0.0326 on the first pass). `base_z` is the largest of those
        radii, so the round parts rest ON the floor.

    The rotation is a LINK (from the `Hinge Angle` group input), not a literal
    tuple, so the gate can assert the swing is dial-driven.
    """
    bx, by = loc
    hinge_x = _neg(tree, (bx - 1400, by - 200), half_w_sock)
    mid_z = _m(tree, "ADD", (bx - 1400, by - 340),
               _m(tree, "MULTIPLY", (bx - 1600, by - 340), board_t_sock, 0.5),
               _m(tree, "ADD", (bx - 1800, by - 340), pin_r, base_z))
    # the moving board's own seat is lifted by the hinge gap, so the pair does not
    # share a face at the pin (a gap of 0 is a valid flush hinge)
    mov_mid = _m(tree, "ADD", (bx - 1400, by - 520), mid_z, gap_sock)

    fixed = _plate(
        tree, (bx - 1000, by), board_l_sock, _m(
            tree, "MULTIPLY", (bx - 1600, by), half_w_sock, 0.80), board_t_sock,
        translation=_vec(tree, (bx - 1200, by - 200),
                         _m(tree, "ADD", (bx - 1600, by - 200), hinge_x,
                            _m(tree, "MULTIPLY", (bx - 1800, by - 200),
                               board_l_sock, 0.5)),
                         0.0, mid_z))

    # The moving board is authored CENTRED ON THE ORIGIN, rotated, then placed.
    # `GeometryNodeTransform` rotates about the tree origin, NOT about the
    # geometry's own centre, so authoring the board at `hinge + L/2` and rotating
    # would swing it around the world origin instead of the pin (measured: the
    # first pass put the free end 21 mm through the floor). The rotated centre is
    # exactly `hinge + (L/2 cos a, 0, L/2 sin a)` for a -a rotation about Y.
    mov_half = _m(tree, "MULTIPLY", (bx - 1600, by - 460), board_l_sock, 0.5)
    cos_a = _m(tree, "COSINE", (bx - 1600, by - 1000), angle_sock)
    sin_a = _m(tree, "SINE", (bx - 1600, by - 1140), angle_sock)
    mov_cx = _m(tree, "ADD", (bx - 1400, by - 800), hinge_x,
                _m(tree, "MULTIPLY", (bx - 1600, by - 800), mov_half, cos_a))
    mov_cz = _m(tree, "ADD", (bx - 1400, by - 940), mov_mid,
                _m(tree, "MULTIPLY", (bx - 1600, by - 940), mov_half, sin_a))
    moving = _plate(
        tree, (bx - 1000, by - 600), board_l_sock,
        _m(tree, "MULTIPLY", (bx - 1600, by - 600), half_w_sock, 0.80),
        board_t_sock,
        translation=_vec(tree, (bx - 1200, by - 800), mov_cx, 0.0, mov_cz),
        rotation=_vec(tree, (bx - 1200, by - 1000), 0.0,
                      _neg(tree, (bx - 1400, by - 1000), angle_sock), 0.0))

    pin = _cyl_x(tree, (bx - 1000, by - 1200), pin_r,
                 _m(tree, "MULTIPLY", (bx - 1600, by - 1200), half_w_sock,
                    1.90), hinge_x, z=mid_z, verts=12)
    return fixed, moving, pin, mid_z


def _gate_geo(tree, loc, cond_sock, geo_sock):
    """`geo_sock` when `cond_sock` is true, EMPTY geometry otherwise.

    A real dial for a 0-or-more count. A MeshLine with `Count` 0 is genuine
    empty geometry, so the part disappears rather than collapsing to a degenerate
    shell (a zero-radius ring is a degenerate face, not an absent part).
    """
    bx, by = loc
    empty = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by))
    if empty is not None:
        try:
            empty.inputs["Count"].default_value = 0
        except Exception:
            pass
    sw = safe_node(tree, "GeometryNodeSwitch", (bx, by))
    if sw is None:
        return geo_sock
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, cond_sock, sw.inputs.get("Switch") or sw.inputs[0])
    link_sockets(tree, empty.outputs["Mesh"] if empty else None,
                 sw.inputs.get("False") or sw.inputs[1])
    link_sockets(tree, geo_sock, sw.inputs.get("True") or sw.inputs[2])
    return sw.outputs.get("Output") or sw.outputs[0]


def _cross_bars(tree, loc, inner_r_sock, bar_r, seat_z, count_sock):
    """Bars crossing the shell's inner diameter at 90 deg, gated by `count_sock`.

    `seat_z` must be the MEAN of the shell's two rim depths. A bar's length is
    derived from the shell's ACTUAL inner radius (`2 x inner_r`), never from a
    count x a constant — the wave-12 panpipes binding-cord defect. `Bar Count`
    is a REAL dial: the second bar is wrapped in a geometry Switch, so 1 gives one
    bar and 2 gives the crossed pair.
    """
    bx, by = loc
    span = _m(tree, "MULTIPLY", (bx - 400, by), inner_r_sock, 2.0)
    first = _cyl_x(tree, (bx, by - 300), bar_r, span, 0.0, y=0.0, z=seat_z,
                   verts=8)
    second = _cyl_x(tree, (bx, by - 500), bar_r, span, 0.0, y=0.0, z=seat_z,
                    verts=8)
    second = _xf(tree, (bx + 200, by - 500), second,
                 rotation=_vec(tree, (bx + 200, by - 700), 0.0, 0.0,
                               math.radians(90.0)))
    cond = _m(tree, "GREATER_THAN", (bx + 200, by - 900), count_sock, 1.0)
    return [first, _gate_geo(tree, (bx + 400, by - 500), cond, second)]


def _unequal_lips(tree, loc, lip_w_sock, ratio_sock, lip_t_sock, slit_w_sock,
                  half_len_sock, top_z):
    """Two lips of UNEQUAL width straddling a slit on a log's crown.

    The wider lip sounds the lower pitch, so BOTH widths trace to `Lip Ratio`:
    the narrow lip is `w x 0.72` and the wide one is that x `ratio`. Driving only
    one lip from the ratio would leave the other blind to the dial, and the gate
    asserts both. Each lip's inner face sits at `+/-slit_w/2` from the axis, so
    the slit's own width is exact. Returns `(lip_a, lip_b)`.
    """
    bx, by = loc
    w_a = _m(tree, "MULTIPLY", (bx - 400, by), lip_w_sock, 0.72)
    w_b = _m(tree, "MULTIPLY", (bx - 400, by - 140), w_a, ratio_sock)
    half_slit = _m(tree, "MULTIPLY", (bx - 400, by - 280), slit_w_sock, 0.5)
    off_a = _m(tree, "ADD", (bx - 200, by - 420), half_slit,
               _m(tree, "MULTIPLY", (bx - 400, by - 420), w_a, 0.5))
    off_b = _m(tree, "ADD", (bx - 200, by - 560), half_slit,
               _m(tree, "MULTIPLY", (bx - 400, by - 560), w_b, 0.5))
    a = _plate(tree, (bx, by), half_len_sock, w_a, lip_t_sock,
               translation=_vec(tree, (bx - 200, by - 700), 0.0, off_a, top_z))
    b = _plate(tree, (bx, by - 840), half_len_sock, w_b, lip_t_sock,
               translation=_vec(tree, (bx - 200, by - 1040), 0.0,
                                _neg(tree, (bx - 400, by - 1040), off_b),
                                top_z))
    return a, b


def _tone_field_ring(tree, loc, count_sock, proto_geo, dome_r_sock,
                     dome_h_sock, ring_fac):
    """A radial rank of tone fields seated ON a scaled dome's surface.

    The dome is a UV sphere scaled to `(r, r, h)`, so the surface height at
    radial distance `d` is `h * sqrt(1 - (d/r)^2)` — NOT `h`. A constant-z seat
    floats the fields off the shell (the wave-12 vessel law). `ring_fac` is the
    radial fraction of `r` the ring sits at, so the SQRT argument is a pure
    function of the fraction and cannot be poisoned by a dial.
    """
    bx, by = loc
    d = _m(tree, "MULTIPLY", (bx - 400, by), dome_r_sock, ring_fac)
    t = _m(tree, "DIVIDE", (bx - 300, by - 140), d, dome_r_sock)
    t2 = _m(tree, "MULTIPLY", (bx - 200, by - 280), t, t)
    z = _m(tree, "MULTIPLY", (bx - 100, by - 420), dome_h_sock,
           _m(tree, "SQRT", (bx - 200, by - 420),
              _m(tree, "SUBTRACT", (bx - 300, by - 420), 1.0, t2)))
    return _ring_rank(tree, (bx + 200, by), count_sock, proto_geo, d,
                      cz=z)


# ---------------------------------------------------------------------------
# MEL_music_temple_block
# ---------------------------------------------------------------------------

def build_music_temple_block(group_name="MEL_music_temple_block"):
    """Temple block: a fish-shaped hollow block on a stand rail.

    The FISH BODY is the identity: two spheres (a rounded belly and a tapered
    tail end) joined into one elongated form, with a slotted mouth on the crown
    and a stand rail beneath. Distinct from the wood block, which is a plain box.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_temple_block"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 0.170, 0.080, 0.320)
    add_float_param(tree, "Body Radius M", 0.052, 0.025, 0.100)
    add_float_param(tree, "Mouth Width M", 0.020, 0.008, 0.045)
    add_float_param(tree, "Wall Depth M", 0.006, 0.002, 0.014)
    add_int_param(tree, "Ridge Count", 3, 1, 6)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Body Length M"]
    R = gin.outputs["Body Radius M"]
    MW = gin.outputs["Mouth Width M"]
    WD = gin.outputs["Wall Depth M"]

    belly_h = _m(tree, "MULTIPLY", (bx - 2200, by + 300), R, 0.92)
    tail_h = _m(tree, "MULTIPLY", (bx - 2200, by + 140), R, 0.68)
    seat_z = _m(tree, "MULTIPLY", (bx - 2200, by - 20), R, 0.30)
    rail_r = _m(tree, "MULTIPLY", (bx - 2200, by - 180), R, 0.075)

    # belly: a sphere scaled to an ellipsoid, centred at its own height
    belly = _sphere(tree, (bx - 1400, by), 1.0, segments=40, rings=20)
    belly = _xf(tree, (bx - 1200, by), belly.outputs["Mesh"],
                scale=_vec(tree, (bx - 1600, by - 200),
                           _m(tree, "MULTIPLY", (bx - 2400, by - 200), L, 0.30),
                           belly_h, belly_h),
                translation=_vec(tree, (bx - 1600, by - 400), 0.0, 0.0,
                                 belly_h)).outputs["Geometry"]
    # tail: a narrower ellipsoid at the +X end, also resting on the floor
    tail = _sphere(tree, (bx - 1400, by - 600), 1.0, segments=32, rings=16)
    tail = _xf(tree, (bx - 1200, by - 600), tail.outputs["Mesh"],
               scale=_vec(tree, (bx - 1600, by - 800),
                          _m(tree, "MULTIPLY", (bx - 2400, by - 800), L, 0.20),
                          tail_h, tail_h),
               translation=_vec(tree, (bx - 1600, by - 1000),
                                _m(tree, "MULTIPLY", (bx - 2400, by - 1000),
                                   L, 0.26),
                                0.0, tail_h)).outputs["Geometry"]

    # slotted mouth: two rails on the crown straddling `Mouth Width M`, their
    # inner faces exactly half a mouth apart (the wood-block `_slot_rails` idiom,
    # re-derived here because the host is a dome, not a flat box).
    # the belly is a sphere scaled to `belly_h` and lifted by `belly_h`, so its
    # CROWN is `2 x belly_h` — not `R` (measured: rails at 0.0488 against a crown
    # at 0.0956, i.e. the whole mouth buried inside the body)
    crown_z = _m(tree, "ADD", (bx - 2200, by - 1400),
                 _m(tree, "MULTIPLY", (bx - 2400, by - 1400), belly_h, 2.0),
                 _m(tree, "MULTIPLY", (bx - 2400, by - 1560), WD, 0.5))
    # the rails' INNER faces are `Mouth Width M` apart, so each is offset by
    # half the mouth PLUS half its own thickness (offsetting by half the mouth
    # alone leaves a slot narrower than the dial says)
    rail_half = _m(tree, "MULTIPLY", (bx - 2200, by - 1600), WD, 0.30)
    half_mw = _m(tree, "ADD", (bx - 2200, by - 1700),
                 _m(tree, "MULTIPLY", (bx - 2400, by - 1700), MW, 0.5),
                 rail_half)
    rails = []
    for i, sx in enumerate((1.0, -1.0)):
        # the second rail's offset is an explicit NEGATION node, not a Python
        # `-0.5` literal: `0.5 * sx` folds to a plain -0.5 at build time and the
        # tree then carries no opposed pair for any probe to find.
        off = half_mw if sx > 0 else _neg(
            tree, (bx - 2200, by - 1800 - i * 200), half_mw)
        rails.append(_plate(
            tree, (bx - 1400, by - 1800 - i * 200),
            _m(tree, "MULTIPLY", (bx - 2200, by - 1800 - i * 200), L, 0.34),
            _m(tree, "MULTIPLY", (bx - 2200, by - 1800 - i * 200), WD, 0.60),
            _m(tree, "MULTIPLY", (bx - 2200, by - 1800 - i * 200), R, 0.16),
            translation=_vec(
                tree, (bx - 1600, by - 2000 - i * 200),
                _m(tree, "MULTIPLY", (bx - 2200, by - 2000 - i * 200), L, 0.06),
                off, crown_z)))

    # three ridge bands across the belly
    ridge = _cyl_x(tree, (bx - 1400, by - 2600),
                   _m(tree, "MULTIPLY", (bx - 2200, by - 2600), R, 1.02),
                   _m(tree, "MULTIPLY", (bx - 2200, by - 2740), L, 0.030),
                   0.0, z=belly_h, verts=24)
    ridges = _rank_inst(
        tree, (bx - 900, by - 2600), gin.outputs["Ridge Count"], ridge,
        _m(tree, "MULTIPLY", (bx - 2200, by - 2600), L, 0.42),
        _m(tree, "MULTIPLY", (bx - 2200, by - 2740), L, -0.21), axis="x")

    # stand rail: a bar under the belly on two feet
    rail = _cyl_x(tree, (bx - 1400, by - 3200), rail_r,
                  _m(tree, "MULTIPLY", (bx - 2200, by - 3200), L, 0.66),
                  0.0, z=rail_r, verts=10)
    feet = []
    for i, sx in enumerate((-1.0, 1.0)):
        feet.append(_cyl_z(
            tree, (bx - 1400, by - 3400 - i * 200), rail_r,
            _m(tree, "MULTIPLY", (bx - 2200, by - 3400 - i * 200), R, 0.16),
            _m(tree, "MULTIPLY", (bx - 2200, by - 3400 - i * 200), R, 0.08),
            x=_m(tree, "MULTIPLY", (bx - 2200, by - 3400 - i * 200), L,
                 0.26 * sx), verts=10))

    geom = _join(tree, (bx + 400, by),
                 [belly, tail, ridges, rail] + rails + feet)
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _perc_attrs(tree, (bx + 400, by - 3800)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Fish Body + Tail", "nodes": ("UV Sphere",), "role": "geometry"},
        {"title": "Slotted Mouth + Ridges", "nodes": ("Cube", "Cylinder"),
         "role": "geometry"},
        {"title": "Stand Rail", "nodes": ("Cylinder", "Instance on Points"),
         "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_ratchet
# ---------------------------------------------------------------------------

def build_music_ratchet(group_name="MEL_music_ratchet"):
    """Ratchet: a toothed WHEEL on an axle inside a frame, a crank, a tongue.

    The TOOTHED WHEEL is the identity (a slotted box or a bent rod is a
    different machine). The wheel is a disc with a radial rank of teeth around
    its rim; the tongue is a sprung plate riding the teeth; the frame is two
    side plates carrying the axle; the crank is an arm + a knob on the -Y face.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_ratchet"
    bx, by = 0, 0

    add_float_param(tree, "Wheel Radius M", 0.058, 0.025, 0.120)
    add_float_param(tree, "Wheel Width M", 0.020, 0.008, 0.045)
    add_int_param(tree, "Tooth Count", 12, 6, 24)
    add_float_param(tree, "Frame Height M", 0.150, 0.070, 0.300)
    add_float_param(tree, "Tongue Length M", 0.075, 0.030, 0.160)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    WR = gin.outputs["Wheel Radius M"]
    WW = gin.outputs["Wheel Width M"]
    FH = gin.outputs["Frame Height M"]
    TL = gin.outputs["Tongue Length M"]

    axle_z = _m(tree, "ADD", (bx - 2200, by + 300),
                _m(tree, "MULTIPLY", (bx - 2400, by + 300), WR, 1.00),
                _m(tree, "MULTIPLY", (bx - 2400, by + 140), WW, 0.70))
    tooth_r = _m(tree, "MULTIPLY", (bx - 2200, by + 140), WR, 0.11)
    hub_r = _m(tree, "MULTIPLY", (bx - 2200, by - 20), WR, 0.22)
    plate_t = _m(tree, "MULTIPLY", (bx - 2200, by - 180), WW, 0.16)
    frame_x = _m(tree, "MULTIPLY", (bx - 2200, by - 260), WR, 1.20)

    # the wheel: a SOLID disc along Y (axis across the frame) at the axle height
    wheel = _disc_y(tree, (bx - 1400, by), WR, WW, 0.0, z=axle_z, verts=40)
    # teeth: a radial rank of cubes around the rim, each centred on its own point
    tooth = _plate(tree, (bx - 1400, by - 400),
                   _m(tree, "MULTIPLY", (bx - 2200, by - 400), tooth_r, 1.90),
                   WW,
                   _m(tree, "MULTIPLY", (bx - 2200, by - 560), tooth_r, 2.30),
                   translation=_vec(tree, (bx - 1600, by - 560), 0.0, 0.0, 0.0))
    teeth = _radial_ring_xz(tree, (bx - 900, by - 400),
                            gin.outputs["Tooth Count"], tooth, WR, cz=axle_z)
    # axle
    axle = _tube_y(tree, (bx - 1400, by - 900), hub_r,
                   _m(tree, "MULTIPLY", (bx - 2200, by - 900), WW, 3.40),
                   0.0, z=axle_z, verts=16)
    # frame: two side plates, standing on the floor, each pierced by the axle
    # each plate sits just OUTSIDE the wheel's own width, so the wheel turns
    # BETWEEN them; at +/-0.80 x WW the plates were inside the wheel's span and
    # its rim passed through both
    plate_y = _m(tree, "ADD", (bx - 2200, by - 1200),
                 _m(tree, "MULTIPLY", (bx - 2400, by - 1200), WW, 0.5),
                 _m(tree, "MULTIPLY", (bx - 2400, by - 1320), plate_t, 0.5))
    frame = []
    for i, sy in enumerate((-1.0, 1.0)):
        frame.append(_plate(
            tree, (bx - 1400, by - 1200 - i * 200),
            frame_x, plate_t, FH,
            translation=_vec(
                tree, (bx - 1600, by - 1400 - i * 200), 0.0,
                _m(tree, "MULTIPLY", (bx - 2200, by - 1400 - i * 200), plate_y,
                   sy),
                _m(tree, "MULTIPLY", (bx - 2200, by - 1400 - i * 200), FH,
                   0.5))))
    # tongue: a sprung plate whose TIP rides the wheel's teeth. Its centre sits
    # `TL/2` inboard of the teeth band along the tilt, so the free end lands ON
    # the rim instead of reaching the wheel's top and intersecting it (measured:
    # a rigid plate spanning the wheel's full diameter).
    # tip target: `1.05 x WR`, i.e. ON the tooth band (rim 1.0 WR, tooth tips
    # 1.11 WR). A -24 deg rotation about Y sends the +X end DOWN, so the centre
    # must sit `(TL/2) sin(24)` ABOVE the axle for the tip to land at axle
    # height. Getting the sign wrong put the tip at radius 0.78 WR — inside the
    # wheel disc, so the tongue speared the wheel instead of riding its teeth.
    tilt = math.radians(-24.0)
    tip_r = _m(tree, "MULTIPLY", (bx - 2400, by - 2160), WR, 1.05)
    tongue_cx = _m(tree, "SUBTRACT", (bx - 2400, by - 2260), tip_r,
                   _m(tree, "MULTIPLY", (bx - 2800, by - 2160), TL,
                      0.5 * math.cos(tilt)))
    tongue_cz = _m(tree, "ADD", (bx - 2400, by - 2360), axle_z,
                   _m(tree, "MULTIPLY", (bx - 2600, by - 2160), TL,
                      0.5 * abs(math.sin(tilt))))
    tongue_w = _m(tree, "MULTIPLY", (bx - 2200, by - 2000), WW, 0.80)
    tongue_y = _m(tree, "ADD", (bx - 2200, by - 1900), plate_y,
                  _m(tree, "MULTIPLY", (bx - 2400, by - 1900), tongue_w, 0.5))
    tongue = _plate(
        tree, (bx - 1400, by - 2000), TL, tongue_w,
        _m(tree, "MULTIPLY", (bx - 2200, by - 2160), WR, 0.10),
        translation=_vec(tree, (bx - 1600, by - 2160), tongue_cx, tongue_y,
                         tongue_cz),
        rotation=(0.0, tilt, 0.0))
    # crank: an arm on the -Y face + a knob
    arm = _plate(tree, (bx - 1400, by - 2600),
                 _m(tree, "MULTIPLY", (bx - 2200, by - 2600), WR, 0.86),
                 plate_t,
                 _m(tree, "MULTIPLY", (bx - 2200, by - 2760), WR, 0.24),
                 translation=_vec(
                     tree, (bx - 1600, by - 2760),
                     _m(tree, "MULTIPLY", (bx - 2200, by - 2760), WR, 0.43),
                     _m(tree, "MULTIPLY", (bx - 2200, by - 2760), WW, -1.50),
                     axle_z))
    knob = _tube_y(tree, (bx - 1400, by - 3000),
                   _m(tree, "MULTIPLY", (bx - 2200, by - 3000), WR, 0.14),
                   _m(tree, "MULTIPLY", (bx - 2200, by - 3160), WW, 0.60),
                   _m(tree, "MULTIPLY", (bx - 2200, by - 3160), WW, -1.50),
                   x=_m(tree, "MULTIPLY", (bx - 2200, by - 3160), WR, 0.86),
                   z=axle_z, verts=12)

    geom = _join(tree, (bx + 400, by),
                 [wheel, teeth, axle, tongue, arm, knob] + frame)
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _perc_attrs(tree, (bx + 400, by - 3600)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Toothed Wheel + Axle", "nodes": ("Cylinder",), "role": "geometry"},
        {"title": "Frame + Tongue", "nodes": ("Cube",), "role": "geometry"},
        {"title": "Teeth + Crank", "nodes": ("Cube", "Instance on Points"),
         "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_bodhran
# ---------------------------------------------------------------------------

def build_music_bodhran(group_name="MEL_music_bodhran"):
    """Bodhran: a deep shell, a head, TWO crossed internal bars, lugs, a tipper.

    The CROSSED BARS are the identity (the frame drum is a shallow braced ring
    with none). The shell is a deep open band, the head a disc on its rim, the
    bars two cylinders at 90 deg spanning the inner diameter at the shell's mean
    depth, the lugs a radial rank, and the tipper a beater resting on the head.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_bodhran"
    bx, by = 0, 0

    add_float_param(tree, "Shell Diameter M", 0.450, 0.200, 0.700)
    add_float_param(tree, "Shell Depth M", 0.110, 0.040, 0.240)
    add_float_param(tree, "Head Thickness M", 0.004, 0.001, 0.012)
    add_int_param(tree, "Lug Count", 8, 4, 16)
    add_int_param(tree, "Bar Count", 2, 1, 3)
    add_float_param(tree, "Tipper Length M", 0.230, 0.100, 0.400)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    D = gin.outputs["Shell Diameter M"]
    H = gin.outputs["Shell Depth M"]
    HT = gin.outputs["Head Thickness M"]
    TL = gin.outputs["Tipper Length M"]

    r_out = _m(tree, "MULTIPLY", (bx - 2200, by + 300), D, 0.5)
    r_in = _m(tree, "MULTIPLY", (bx - 2200, by + 140), r_out, 0.94)
    bar_r = _m(tree, "MULTIPLY", (bx - 2200, by - 20), H, 0.030)
    lug_r = _m(tree, "MULTIPLY", (bx - 2200, by - 180), H, 0.045)
    tipper_r = _m(tree, "MULTIPLY", (bx - 2200, by - 340), TL, 0.030)
    mid_z = _m(tree, "MULTIPLY", (bx - 2200, by - 500), H, 0.50)

    # shell: a deep open band standing on the floor
    shell = _shell_z(tree, (bx - 1400, by), r_out, H, 0.0, verts=48)
    # head: a disc centred on the shell's top rim
    head = _disc_z(tree, (bx - 1400, by - 400),
                   _m(tree, "MULTIPLY", (bx - 2200, by - 400), r_out, 1.02),
                   HT, H, verts=48)
    # rim ring: a proud band around the head's edge
    rim = _shell_z(tree, (bx - 1400, by - 800),
                   _m(tree, "MULTIPLY", (bx - 2200, by - 800), r_out, 1.04),
                   _m(tree, "MULTIPLY", (bx - 2200, by - 940), H, 0.075),
                   _m(tree, "SUBTRACT", (bx - 2400, by - 940), H,
                      _m(tree, "MULTIPLY", (bx - 2600, by - 940), H, 0.075)),
                   verts=48)
    # lugs: a radial rank of blocks around the shell's outer wall
    # the lug block's own depth is small relative to the shell, so seating the
    # ring at `r_out` leaves it straddling the wall. Measured per-part: the lug
    # band spans the full shell diameter at z in [0.0385, 0.0715] on a shell of
    # height 0.11 — a band around the shell's middle, which is where lugs sit.
    lug_depth = _m(tree, "MULTIPLY", (bx - 2200, by - 1560), H, 0.26)
    lug = _plate(tree, (bx - 1400, by - 1400),
                 _m(tree, "MULTIPLY", (bx - 2200, by - 1400), r_out, 0.10),
                 lug_depth,
                 _m(tree, "MULTIPLY", (bx - 2200, by - 1720), H, 0.30),
                 translation=_vec(tree, (bx - 1600, by - 1720), 0.0, 0.0, 0.0))
    lugs = _ring_rank(tree, (bx - 900, by - 1400), gin.outputs["Lug Count"],
                      lug, r_out, cz=mid_z)

    # crossed bars: two cylinders spanning the inner diameter at the mean depth.
    # `Bar Count` selects 1 or 2 bars; the second is at 90 deg to the first.
    bars = _cross_bars(tree, (bx - 1400, by - 2400), r_in, bar_r, mid_z,
                       gin.outputs["Bar Count"])

    # tipper: a beater resting across the head, its own ends proud of the rim
    tipper = _cyl_x(tree, (bx - 1400, by - 3000), tipper_r, TL, 0.0,
                    y=_m(tree, "MULTIPLY", (bx - 2200, by - 3000), r_out, 0.12),
                    z=_m(tree, "ADD", (bx - 2400, by - 3000), H,
                          _m(tree, "MULTIPLY", (bx - 2600, by - 3000),
                             tipper_r, 1.10)),
                    verts=16)

    geom = _join(tree, (bx + 400, by),
                 [shell, head, rim, lugs, tipper] + bars)
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _perc_attrs(tree, (bx + 400, by - 3600)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Shell + Head + Rim", "nodes": ("Cylinder",), "role": "geometry"},
        {"title": "Crossed Bars", "nodes": ("Cylinder",), "role": "geometry"},
        {"title": "Lugs", "nodes": ("Cube", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_slapstick
# ---------------------------------------------------------------------------

def build_music_slapstick(group_name="MEL_music_slapstick"):
    """Slapstick: two boards HINGED at one end about a real pin, plus a handle.

    The HINGE is the identity (two loose rods are the claves). The moving board's
    Transform rotation is LINKED from `Hinge Angle`, so the swing is dial-driven
    and the gate can see it.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_slapstick"
    bx, by = 0, 0

    add_float_param(tree, "Board Length M", 0.300, 0.120, 0.600)
    add_float_param(tree, "Board Width M", 0.075, 0.030, 0.160)
    add_float_param(tree, "Board Thickness M", 0.010, 0.004, 0.025)
    add_float_param(tree, "Hinge Gap M", 0.006, 0.001, 0.020)
    add_float_param(tree, "Hinge Angle", 0.35, 0.0, 1.20)
    add_float_param(tree, "Handle Length M", 0.110, 0.040, 0.240)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Board Length M"]
    W = gin.outputs["Board Width M"]
    T = gin.outputs["Board Thickness M"]
    HL = gin.outputs["Handle Length M"]

    half_w = _m(tree, "MULTIPLY", (bx - 2200, by + 300), W, 0.5)
    board_l = _m(tree, "SUBTRACT", (bx - 2200, by + 140), L,
                 _m(tree, "MULTIPLY", (bx - 2400, by + 140), W, 0.55))
    handle_r = _m(tree, "MULTIPLY", (bx - 2200, by - 20), W, 0.11)
    grip_r = _m(tree, "MULTIPLY", (bx - 2200, by - 100), handle_r, 1.30)
    pin_r = _m(tree, "MULTIPLY", (bx - 2200, by - 180), T, 0.55)
    # the assembly's shared axis: the largest radius any coaxial round part has,
    # so nothing hangs below z = 0 (the didgeridoo axis-height law)
    base_z = _m(tree, "MAXIMUM", (bx - 2200, by - 260), grip_r,
                _m(tree, "MAXIMUM", (bx - 2400, by - 260), pin_r, handle_r))

    fixed, moving, pin, mid_z = _hinge_pair(
        tree, (bx - 1600, by - 600), half_w, board_l, T,
        gin.outputs["Hinge Gap M"], gin.outputs["Hinge Angle"],
        base_z=base_z, pin_r=pin_r)

    # handle: a shaft off the hinge end on the -X side, plus a grip band, both on
    # the assembly's shared axis
    handle = _cyl_x(tree, (bx - 1400, by - 2200), handle_r, HL,
                    _neg(tree, (bx - 2400, by - 2200),
                         _m(tree, "ADD", (bx - 2600, by - 2200), half_w,
                            _m(tree, "MULTIPLY", (bx - 2800, by - 2200), HL,
                               0.5))),
                    z=mid_z, verts=16)
    grip = _cyl_x(tree, (bx - 1400, by - 2600), grip_r,
                  _m(tree, "MULTIPLY", (bx - 2200, by - 2760), HL, 0.28),
                  _neg(tree, (bx - 2400, by - 2760),
                       _m(tree, "ADD", (bx - 2600, by - 2760), half_w,
                          _m(tree, "MULTIPLY", (bx - 2800, by - 2760), HL,
                             0.62))),
                  z=mid_z, verts=16)

    geom = _join(tree, (bx + 400, by),
                 [fixed, moving, pin, handle, grip])
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _perc_attrs(tree, (bx + 400, by - 3200)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Hinged Boards", "nodes": ("Cube",), "role": "geometry"},
        {"title": "Hinge Pin", "nodes": ("Cylinder",), "role": "geometry"},
        {"title": "Handle + Grip", "nodes": ("Cylinder",), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_slit_drum
# ---------------------------------------------------------------------------

def build_music_slit_drum(group_name="MEL_music_slit_drum"):
    """Slit drum: a hollow LOG with a longitudinal SLIT between UNEQUAL lips.

    The SLIT and its asymmetric lips are the identity (the cajon is a closed box
    with a tapa). The log is a scaled sphere, the lips two plates of different
    widths straddling the slit, the ends two caps, and the resonator mouths two
    laid-on rings on the log's flanks.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_slit_drum"
    bx, by = 0, 0

    add_float_param(tree, "Log Length M", 0.620, 0.250, 1.100)
    add_float_param(tree, "Log Radius M", 0.130, 0.060, 0.260)
    add_float_param(tree, "Slit Width M", 0.026, 0.008, 0.060)
    add_float_param(tree, "Lip Ratio", 1.55, 1.15, 2.40)
    add_float_param(tree, "Lip Thickness M", 0.012, 0.004, 0.030)
    add_int_param(tree, "Mouth Count", 2, 0, 4)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Log Length M"]
    R = gin.outputs["Log Radius M"]
    SW = gin.outputs["Slit Width M"]
    LT = gin.outputs["Lip Thickness M"]

    # the log is a sphere scaled z by R and lifted by R, so its CROWN is `2 x R`
    # — a slit at `R` is cut at the log's equator and never shows (measured)
    top_z = _m(tree, "MULTIPLY", (bx - 2200, by + 300), R, 2.00)
    lip_w = _m(tree, "MULTIPLY", (bx - 2200, by + 140), SW, 1.60)
    half_len = _m(tree, "MULTIPLY", (bx - 2200, by - 20), L, 0.34)
    cap_r = _m(tree, "MULTIPLY", (bx - 2200, by - 180), R, 0.90)

    # the log: a UV sphere scaled into a lying barrel, resting on the floor
    log = _sphere(tree, (bx - 1400, by), 1.0, segments=48, rings=24)
    log = _xf(tree, (bx - 1200, by), log.outputs["Mesh"],
              scale=_vec(tree, (bx - 1600, by - 200),
                         _m(tree, "MULTIPLY", (bx - 2400, by - 200), L, 0.5),
                         R, R),
              translation=_vec(tree, (bx - 1600, by - 400), 0.0, 0.0,
                               R)).outputs["Geometry"]

    # the slit: two UNEQUAL lips straddling it on the crown
    lip_a, lip_b = _unequal_lips(
        tree, (bx - 1400, by - 700), lip_w, gin.outputs["Lip Ratio"], LT, SW,
        half_len,
        _m(tree, "ADD", (bx - 2400, by - 900), top_z,
           _m(tree, "MULTIPLY", (bx - 2600, by - 900), LT, 0.5)))

    # end caps: two discs standing at the log's ends
    caps = []
    for i, sx in enumerate((-1.0, 1.0)):
        caps.append(_disc_z(
            tree, (bx - 1400, by - 1400 - i * 200),
            _m(tree, "MULTIPLY", (bx - 2200, by - 1400 - i * 200), R, 0.86),
            _m(tree, "MULTIPLY", (bx - 2200, by - 1400 - i * 200), L, 0.020),
            R,
            x=_m(tree, "MULTIPLY", (bx - 2200, by - 1400 - i * 200), L,
                 0.47 * sx), verts=32))

    # resonator mouths: rings laid on the log's flanks, along Y, gated by
    # `Mouth Count` (0 = a plain log, which is a legitimate setting). The two
    # rings sit on OPPOSITE flanks — the side is a SIGNED centre, never a 180 deg
    # rotation (a Transform rotates about the tree origin, so a pi-about-Z flip
    # would move the ring in X as well as Y).
    mouths = []
    for i in range(2):
        side = 1.0 if i == 0 else -1.0
        m_geo = _tube_y(
            tree, (bx - 1400, by - 2000 - i * 200),
            _m(tree, "MULTIPLY", (bx - 2200, by - 2000 - i * 200), cap_r, 0.34),
            _m(tree, "MULTIPLY", (bx - 2200, by - 2000 - i * 200), R, 0.16),
            _m(tree, "MULTIPLY", (bx - 2200, by - 2000 - i * 200), R,
               0.94 * side),
            x=_m(tree, "MULTIPLY", (bx - 2200, by - 2000 - i * 200), L, 0.22),
            z=_m(tree, "MULTIPLY", (bx - 2200, by - 2000 - i * 200), R, 0.55),
            verts=20)
        cond = _m(tree, "GREATER_THAN", (bx - 600, by - 2400 - i * 200),
                  gin.outputs["Mouth Count"], float(i))
        mouths.append(_gate_geo(tree, (bx - 400, by - 2000 - i * 200), cond,
                                m_geo))

    geom = _join(tree, (bx + 400, by),
                 [log, lip_a, lip_b] + caps + mouths)
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _perc_attrs(tree, (bx + 400, by - 3000)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Hollow Log + End Caps", "nodes": ("UV Sphere", "Cylinder"),
         "role": "geometry"},
        {"title": "Slit Lips (unequal)", "nodes": ("Cube",), "role": "geometry"},
        {"title": "Resonator Mouths", "nodes": ("Cylinder",), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_handpan
# ---------------------------------------------------------------------------

def build_music_handpan(group_name="MEL_music_handpan"):
    """Handpan: a convex hammered DOME with a central ding and tone fields.

    The DOME plus its radial tone fields are the identity (the steelpan is a
    concave open pan). The shell is a scaled UV sphere, the ding a flattened
    sphere on the crown, the tone fields a radial rank seated ON the dome's
    surface at their own radius, the bottom port a ring, and three feet.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_handpan"
    bx, by = 0, 0

    add_float_param(tree, "Dome Diameter M", 0.520, 0.250, 0.800)
    add_float_param(tree, "Dome Height M", 0.150, 0.060, 0.300)
    add_int_param(tree, "Tone Count", 8, 4, 12)
    add_float_param(tree, "Field Diameter M", 0.070, 0.030, 0.140)
    add_float_param(tree, "Ding Diameter M", 0.105, 0.045, 0.180)
    add_int_param(tree, "Foot Count", 3, 3, 5)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    D = gin.outputs["Dome Diameter M"]
    H = gin.outputs["Dome Height M"]
    FD = gin.outputs["Field Diameter M"]
    DD = gin.outputs["Ding Diameter M"]

    r_dome = _m(tree, "MULTIPLY", (bx - 2200, by + 300), D, 0.5)
    field_r = _m(tree, "MULTIPLY", (bx - 2200, by + 140), FD, 0.5)
    field_z = _m(tree, "MULTIPLY", (bx - 2200, by - 20), FD, 0.16)
    ring_r = _m(tree, "MULTIPLY", (bx - 2200, by - 180), r_dome, 0.58)
    foot_h = _m(tree, "MULTIPLY", (bx - 2200, by - 340), H, 0.16)
    port_r = _m(tree, "MULTIPLY", (bx - 2200, by - 500), r_dome, 0.30)

    # the shell: a sphere scaled to a shallow convex dome, resting on the floor
    dome = _sphere(tree, (bx - 1400, by), 1.0, segments=56, rings=28)
    dome = _xf(tree, (bx - 1200, by), dome.outputs["Mesh"],
               scale=_vec(tree, (bx - 1600, by - 200), r_dome, r_dome, H),
               translation=_vec(tree, (bx - 1600, by - 400), 0.0, 0.0,
                                H)).outputs["Geometry"]

    # central ding: a flattened sphere on the crown
    ding = _sphere(tree, (bx - 1400, by - 700), 1.0, segments=32, rings=16)
    ding = _xf(tree, (bx - 1200, by - 700), ding.outputs["Mesh"],
               scale=_vec(tree, (bx - 1600, by - 900),
                          _m(tree, "MULTIPLY", (bx - 2400, by - 900), DD, 0.5),
                          _m(tree, "MULTIPLY", (bx - 2400, by - 1100), DD, 0.5),
                          _m(tree, "MULTIPLY", (bx - 2400, by - 1300), DD,
                             0.10)),
               translation=_vec(tree, (bx - 1600, by - 1500), 0.0, 0.0,
                                H)).outputs["Geometry"]

    # tone fields: a radial rank of flattened dimples seated ON the dome surface
    field = _sphere(tree, (bx - 1400, by - 1800), 1.0, segments=20, rings=12)
    field = _xf(tree, (bx - 1200, by - 1800), field.outputs["Mesh"],
                scale=_vec(tree, (bx - 1600, by - 2000), field_r, field_r,
                           field_z),
                translation=_vec(tree, (bx - 1600, by - 2200), 0.0, 0.0,
                                 0.0)).outputs["Geometry"]
    fields = _tone_field_ring(tree, (bx - 900, by - 1800),
                              gin.outputs["Tone Count"], field, r_dome, H,
                              0.58)

    # bottom port ring + feet, both under the shell
    port = _shell_z(tree, (bx - 1400, by - 2600), port_r,
                    _m(tree, "MULTIPLY", (bx - 2200, by - 2600), H, 0.10),
                    _m(tree, "MULTIPLY", (bx - 2200, by - 2740), H, 0.10),
                    verts=32)
    # the proto is centred on its OWN origin (cz = 0) and the ring does ALL the
    # placement: baking `cz = foot_h/2` here and passing it to the rank again
    # floats every foot `foot_h/2` above the floor (measured min_z 0.0120)
    foot = _cyl_z(tree, (bx - 1400, by - 3000),
                  _m(tree, "MULTIPLY", (bx - 2200, by - 3000), r_dome, 0.045),
                  foot_h, 0.0, verts=10)
    feet = _ring_rank(tree, (bx - 900, by - 3000), gin.outputs["Foot Count"],
                      foot, _m(tree, "MULTIPLY", (bx - 2200, by - 3000),
                               r_dome, 0.34),
                      cz=_m(tree, "MULTIPLY", (bx - 2200, by - 3200), foot_h,
                            0.5))

    geom = _join(tree, (bx + 400, by),
                 [dome, ding, fields, port, feet])
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _perc_attrs(tree, (bx + 400, by - 3400)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Convex Dome + Ding", "nodes": ("UV Sphere",), "role": "geometry"},
        {"title": "Tone Fields", "nodes": ("UV Sphere", "Instance on Points"),
         "role": "instance"},
        {"title": "Port + Feet", "nodes": ("Cylinder", "Instance on Points"),
         "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

register_builder(
    "MEL_music_temple_block", build_music_temple_block, "Temple Block",
    "Temple block: a fish-shaped hollow block (rounded belly + tapered tail) "
    "with a slotted mouth on the crown, ridge bands and a stand rail. "
    "Native-only.",
    "music",
)
register_builder(
    "MEL_music_ratchet", build_music_ratchet, "Ratchet",
    "Ratchet: a toothed wheel on an axle inside a two-plate frame, with a crank "
    "and a sprung tongue riding the teeth. Native-only.",
    "music",
)
register_builder(
    "MEL_music_bodhran", build_music_bodhran, "Bodhran",
    "Bodhran: a deep shell with a head, a proud rim, a radial lug rank, two "
    "crossed internal bars and a tipper resting on the head. Native-only.",
    "music",
)
register_builder(
    "MEL_music_slapstick", build_music_slapstick, "Slapstick",
    "Slapstick: two boards hinged at one end about a real pin, the moving board "
    "swung by a Hinge Angle dial, on a gripped handle. Native-only.",
    "music",
)
register_builder(
    "MEL_music_slit_drum", build_music_slit_drum, "Slit Drum",
    "Slit drum: a hollow log with a longitudinal slit between two UNEQUAL lips, "
    "end caps and laid-on resonator mouths. Native-only.",
    "music",
)
register_builder(
    "MEL_music_handpan", build_music_handpan, "Handpan",
    "Handpan: a convex hammered dome with a central ding and a radial rank of "
    "dimpled tone fields seated on the shell surface, a bottom port and three "
    "feet. Native-only.",
    "music",
)
