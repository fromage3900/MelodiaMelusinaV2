"""P4 wave 12 — solo & folk wind lane: shakuhachi, xun, panpipes, quena,
didgeridoo, tin whistle.

Gap audit first (repo-wide grep over `deploy/surreal_arch/` + the live registry +
`Tools/registry_baseline.json`, 2026-10-04): the wind lane already owns
saxophone, bandoneon, glass harmonica, theremin, siku, flute, clarinet, recorder,
melodica, oboe, bassoon, trumpet, tuba, accordion, bagpipes, dizi, xiao, bawu,
hulusi, suona and sheng. NONE of the six ids below existed anywhere (grep count 0
each, 0 in the baseline):

    shakuhachi, xun, panpipes, quena, didgeridoo, tin whistle

Each of the six is distinct from its closest existing neighbour by its OWN
anatomy, not by a parameter:

    MEL_music_shakuhachi vs MEL_music_xiao   a WIDE-BORE tapered tube with a
                                             SLANTED utaguchi blowing edge and a
                                             flared ROOT end; the xiao is a
                                             narrow even tube with a notched top
                                             and no flare
    MEL_music_xun        vs MEL_music_ocarina a TOP-BLOWN egg-shaped clay vessel
                                             with no windway at all; the ocarina
                                             is a super-ellipsoid with a windway
                                             tube on its side
    MEL_music_panpipes   vs MEL_music_sheng  a BUNDLE of closed graduated tubes
                                             bound in two rows hanging from one
                                             aligned mouthpiece plane; the sheng
                                             is a bowl of reed-window pipes
    MEL_music_quena      vs MEL_music_xiao   a U-NOTCH cut into the rim (two proud
                                             walls + a notch floor) on a wide
                                             banded bone/wood body; the xiao's
                                             top is a plain inward chamfer
    MEL_music_didgeridoo vs MEL_music_tubular_bells  a long plain TAPERED trunk
                                             with NO holes and a beeswax
                                             mouthpiece collar; chimes are a
                                             rank of hanging tubes
    MEL_music_tin_whistle vs MEL_music_recorder  a STRAIGHT narrow metal tube
                                             under a moulded head with a fipple
                                             window and a labium; the recorder
                                             is a tapered wooden body with a
                                             separate block and 7 holes

Design rules (same as music_wind_folk / music_keyboard_kit /
music_world_percussion / music_aux_percussion):
  - Native-only. These are revolved tubes, vessel forms, plates and bound
    bundles that 5.2 primitives express exactly; a Higgsas subtree here would be
    decoration, not a lead. Every builder still stores `higgsas_lead` (1.0 =
    native) so the family gate and the instruments gate read the lane uniformly.
  - The wave-6/wave-10/wave-11 origin-explicit helpers are REUSED, never
    re-authored: `_cone_x` / `_cone_z` take the BASE (`MeshCone`'s origin is its
    base), `_cyl_x` / `_cyl_z` take the CENTRE, `_cone_proto_z` / `_cyl_proto_z`
    return base-origin protos, `_shell_z` / `_disc_z` / `_ring_rank` / `_mean_r`
    come from the world-percussion lane, `_rims_x` from the folk wind lane,
    `_cyl_y` / `_graded_rank` from the auxiliary-percussion lane, `_plate` links
    all three `Size` components.
  - Zero `MeshBoolean` in the lane: a cutter that touches the mesh's own boundary
    emits ZERO geometry with no error and no `link_failures` entry. Every hole,
    notch and window is LAID ON, never cut.
  - A primitive `Size` component is never left at LITERAL ZERO (the
    castle-merlon zero-width-slab class).
  - A cone's tip radius is never 0: an NGON top cap at radius 0 is a degenerate
    face by construction.
  - Every lane builder sits ON the floor (realized min_z >= -0.01). A horizontal
    tube's AXIS therefore sits at the radius of its WIDEST coaxial part, not at
    its own radius — a 1.45R head on an axis at R hangs 0.45R through the floor.

Lane-local law 1 — `_taper_rank`, a length-graduated rank whose SPREAD is a
socket. Wave 11's `_graded_rank` hardcodes `spread` as a literal, so a panpipe
driven by it would have a Shortest Ratio dial that does nothing (the wave-4 dead
Scale class). The graduation stays in ONE axis: the tubes shorten with pitch while
their bore stays constant.

Lane-local law 2 — a rank on a VESSEL (the xun's ellipsoid) is seated at the
vessel's radius AT ITS OWN HEIGHT, never at a blanket mean or at the widest
point. The xun's two hole ranks sit in the middle band where the ellipsoid's
radius factor is within 2% of R, so a constant-Y seat straddles the surface
there; a rank placed near either pole would float off it.

Builders:
    MEL_music_shakuhachi  flared root + tapered bore + utaguchi edge + 4+1 rims
    MEL_music_xun         top-blown clay egg + foot ring + 2 x 3 finger rims
    MEL_music_panpipes    two bound rows of closed graduated tubes
    MEL_music_quena       U-notched rim + banded body + 6+1 radial rims
    MEL_music_didgeridoo  long tapered trunk + beeswax collars + bell rim
    MEL_music_tin_whistle straight tube + fipple head + window ring + labium
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
    _vec, _sphere, _cone_x, _cyl_x, _cone_z, _cyl_z, _cone_proto_z,
    _cyl_proto_z, _join, _rank_inst, _rank_axis, _half_span, _count_minus_one,
    _attrs,
)
from .music_world_percussion import _shell_z, _disc_z
from .music_wind_folk import _rims_x
from .music_aux_percussion import _cyl_y


# ---------------------------------------------------------------------------
# Lane-local laws
# ---------------------------------------------------------------------------

def _ring_x(tree, loc, r_sock, depth_sock, cx, z, verts=24):
    """An OPEN ring (fill NONE) whose axis is along X, centred at (cx, 0, z).

    `_cyl_x` hard-codes the NGON cap, so a rim or a window built with it is a
    solid plug. This is the ring sibling: `_cyl(fill=1)` rotated onto X.
    """
    prim = _cyl(tree, loc, r_sock, depth_sock, vertices=verts, fill=1)
    if prim is None:
        return None
    return _xf(tree, (loc[0] + 200, loc[1]), prim.outputs["Mesh"],
               rotation=(0.0, 1.5707963, 0.0),
               translation=_vec(tree, (loc[0] + 200, loc[1] - 200),
                               cx, 0.0, z)).outputs["Geometry"]


def _ring_z(tree, loc, r_sock, depth_sock, cz, x=0.0, y=0.0, verts=16):
    """An OPEN ring (fill NONE) along Z, centred at (x, y, cz)."""
    prim = _cyl(tree, loc, r_sock, depth_sock, vertices=verts, fill=1)
    if prim is None:
        return None
    return _xf(tree, (loc[0] + 200, loc[1]), prim.outputs["Mesh"],
               translation=_vec(tree, (loc[0] + 200, loc[1] - 200),
                               x, y, cz)).outputs["Geometry"]


def _hole_y(tree, loc, r_sock, depth_sock, y_sock, z_sock, verts=12):
    """One RADIAL hole rim on a Z-laid tube: axis along Y, centred at (0, y, z).

    `_rims_z` (folk wind lane) seats a Z-laid collar PARALLEL to the tube, which
    reads as a bump beside the bore rather than a hole through its wall. A radial
    rim crosses the surface, so it reads as a bored hole without a boolean.
    """
    prim = _cyl_y(tree, loc, r_sock, depth_sock, verts=verts)
    if prim is None:
        return None
    return _xf(tree, (loc[0] + 400, loc[1]), prim,
               translation=_vec(tree, (loc[0] + 400, loc[1] - 200),
                               0.0, y_sock, z_sock)).outputs["Geometry"]


def _rims_y(tree, loc, count_sock, span_sock, first_sock, y_sock, r_sock,
           depth_sock, verts=12, step_sign=1.0):
    """A rank of radial hole rims on the +/-Y wall of a Z-laid tube."""
    proto = _cyl_y(tree, loc, r_sock, depth_sock, verts=verts)
    return _rank_inst(tree, (loc[0] + 400, loc[1]), count_sock, proto,
                      span_sock, first_sock, axis="z", step_sign=step_sign,
                      y=y_sock)


def _top_proto_z(tree, loc, geo_sock, length_sock):
    """Shift a BASE-origin proto DOWN by its own length, so its origin is its TOP.

    A panpipe bundle hangs from one aligned mouthpiece plane, so the instance
    origin must be the tube's TOP; scaling about the instance origin then shortens
    the tube downward and every top stays on the plane.
    """
    neg = _m(tree, "MULTIPLY", (loc[0] - 200, loc[1] - 200), length_sock, -1.0)
    return _xf(tree, loc, geo_sock,
               translation=_vec(tree, (loc[0], loc[1] - 300),
                               0.0, 0.0, neg)).outputs["Geometry"]


def _taper_rank(tree, loc, count_sock, proto_geo, span_sock, top_z,
                spread_sock, grad_axis="z"):
    """A rank stepped along X, graduated in ONE axis by a SOCKET spread.

    Sibling of wave-11's `_graded_rank`, which hardcodes `spread` as a literal —
    a panpipe whose Shortest Ratio dial did nothing would be a dead parameter.
    The scale vector is `ratio` on `grad_axis` and a literal 1.0 on the other two,
    so the members shorten with pitch while their width and bore stay constant
    (`_stand`'s uniform per-index scale is the wrong idiom). The proto's ORIGIN
    must be the member's own TOP.
    """
    bx, by = loc
    denom = _m(tree, "MAXIMUM", (bx - 1200, by - 200),
               _m(tree, "SUBTRACT", (bx - 1400, by - 200), count_sock, 1.0), 1.0)
    step = _m(tree, "DIVIDE", (bx - 1000, by - 200), span_sock, denom)
    pts = _rank_axis(tree, (bx - 800, by), count_sock, "x",
                     _half_span(tree, (bx - 1000, by + 200), span_sock),
                     step, z=top_z)
    if pts is None:
        return None
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 800, by - 300))
    t = _m(tree, "DIVIDE", (bx - 600, by - 300), idx.outputs["Index"], denom)
    ratio = _m(tree, "SUBTRACT", (bx - 400, by - 300), 1.0,
               _m(tree, "MULTIPLY", (bx - 600, by - 440), t, spread_sock))
    one = 1.0
    vec = {"x": (ratio, one, one), "y": (one, ratio, one),
           "z": (one, one, ratio)}[grad_axis]
    sc = _vec(tree, (bx - 200, by - 300), *vec)
    return _inst_rank(tree, (bx + 200, by), pts, proto_geo, scale_sock=sc)


def _row_counts(tree, loc, count_sock):
    """`front = floor(n/2 + 0.5)`, `back = n - front` — the split law.

    A count that drives TWO rows must be SPLIT, not applied twice (the
    `MEL_music_sheng` defect: 17 pipes produced 34). The FLOOR + SUBTRACT pair is
    what the family gate asserts.
    """
    bx, by = loc
    front = _m(tree, "FLOOR", (bx, by),
               _m(tree, "ADD", (bx - 200, by - 140),
                  _m(tree, "MULTIPLY", (bx - 400, by - 140), count_sock, 0.5),
                  0.5))
    back = _m(tree, "SUBTRACT", (bx + 200, by), count_sock, front)
    return front, back


def _neg_seat(tree, loc, r_sock, ratio):
    """`-ratio * r` — the seat of a rank on the FAR wall of a tube."""
    return _m(tree, "MULTIPLY", loc, r_sock, -abs(ratio))


def _neg(tree, loc, sock):
    """`-sock` through a MULTIPLY by -1.0.

    A Python unary minus on a socket raises `TypeError: bad operand type for
    unary -: 'NodeSocketFloat'` at BUILD time — the whole builder dies, which is
    loud, but it means the negation must be a node. (`NEGATE` is NOT a valid
    ShaderNodeMath operation: it is silently swallowed and the node stays on ADD.)
    """
    return _m(tree, "MULTIPLY", loc, sock, -1.0)


# ---------------------------------------------------------------------------
# MEL_music_shakuhachi
# ---------------------------------------------------------------------------

def build_music_shakuhachi(group_name="MEL_music_shakuhachi"):
    """Shakuhachi: flared root, wide tapered bore, slanted utaguchi, 4+1 rims.

    Vertical (+Z, base on the floor). The WIDE BORE and the flared root are the
    two features that separate it from the xiao (a narrow even tube); the
    utaguchi is a tilted blowing-edge plate standing proud of the top band.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_shakuhachi"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 0.545, 0.30, 1.00)
    add_float_param(tree, "Bore Radius M", 0.019, 0.010, 0.030)
    add_float_param(tree, "Root Flare Ratio", 1.30, 1.00, 1.80)
    add_int_param(tree, "Node Count", 3, 2, 6)
    add_int_param(tree, "Hole Count", 4, 3, 6)
    add_float_param(tree, "Hole Radius M", 0.0055, 0.0020, 0.0120)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Body Length M"]
    R = gin.outputs["Bore Radius M"]
    HR = gin.outputs["Hole Radius M"]

    flare_h = _m(tree, "MULTIPLY", (bx - 2200, by + 300), L, 0.075)
    body_h = _m(tree, "SUBTRACT", (bx - 2400, by + 300), L, flare_h)
    r_lo = _m(tree, "MULTIPLY", (bx - 2200, by + 140), R,
              gin.outputs["Root Flare Ratio"])
    r_hi = _m(tree, "MULTIPLY", (bx - 2200, by - 20), R, 0.86)
    band_h = _m(tree, "MULTIPLY", (bx - 2200, by - 180), L, 0.025)
    collar_d = _m(tree, "MULTIPLY", (bx - 2200, by - 340), L, 0.016)
    rim_d = _m(tree, "MULTIPLY", (bx - 2200, by - 500), R, 0.90)

    # root flare: widest at z = 0 so the instrument stands on its bell
    flare = _cone_z(tree, (bx - 1400, by), r_lo,
                    _m(tree, "MULTIPLY", (bx - 2400, by), R, 1.02),
                    flare_h, 0.0, verts=32)
    # bore: a wide taper narrowing toward the mouthpiece
    body = _cone_z(tree, (bx - 1400, by - 400),
                   _m(tree, "MULTIPLY", (bx - 2400, by - 400), R, 1.02),
                   r_hi, body_h, flare_h, verts=32)
    # top band + the utaguchi blowing-edge plate, tilted
    band = _cyl_z(tree, (bx - 1400, by - 800),
                  _m(tree, "MULTIPLY", (bx - 2400, by - 800), R, 1.10),
                  band_h, _m(tree, "SUBTRACT", (bx - 2600, by - 800), L,
                             _m(tree, "MULTIPLY", (bx - 2800, by - 800),
                                band_h, 0.5)), verts=24)
    edge = _plate(tree, (bx - 1400, by - 1200),
                  _m(tree, "MULTIPLY", (bx - 2400, by - 1200), R, 2.10),
                  _m(tree, "MULTIPLY", (bx - 2400, by - 1360), R, 1.30),
                  _m(tree, "MULTIPLY", (bx - 2400, by - 1520), L, 0.028),
                  translation=_vec(tree, (bx - 1600, by - 1520), 0.0,
                                   _m(tree, "MULTIPLY",
                                      (bx - 2400, by - 1520), R, -0.34),
                                   _m(tree, "MULTIPLY",
                                      (bx - 2400, by - 1680), L, 1.012)),
                  rotation=(math.radians(18.0), 0.0, 0.0))

    # bamboo node collars along the upper body
    collar = _cyl_z(tree, (bx - 1400, by - 2000),
                    _m(tree, "MULTIPLY", (bx - 2400, by - 2000), R, 1.14),
                    collar_d, 0.0, verts=24)
    collars = _rank_inst(
        tree, (bx - 900, by - 2000), gin.outputs["Node Count"], collar,
        _m(tree, "MULTIPLY", (bx - 2400, by - 2000), L, 0.60),
        _m(tree, "MULTIPLY", (bx - 2400, by - 2140), L, 0.20), axis="z")

    # four finger rims on the +Y wall, one thumb rim on the -Y wall
    holes = _rims_y(
        tree, (bx - 1400, by - 2600), gin.outputs["Hole Count"],
        _m(tree, "MULTIPLY", (bx - 2400, by - 2600), L, 0.36),
        _m(tree, "MULTIPLY", (bx - 2400, by - 2740), L, 0.22),
        _m(tree, "MULTIPLY", (bx - 2400, by - 2880), R, 0.98),
        HR, rim_d, verts=12)
    thumb = _hole_y(
        tree, (bx - 1400, by - 3200), HR, rim_d,
        _neg_seat(tree, (bx - 2400, by - 3200), R, 0.98),
        _m(tree, "MULTIPLY", (bx - 2400, by - 3340), L, 0.44), verts=12)

    geom = _join(tree, (bx + 400, by),
                 [flare, body, band, edge, collars, holes, thumb])
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _attrs(tree, (bx + 400, by - 3800)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Flared Root + Tapered Bore", "nodes": ("Cone",),
         "role": "geometry"},
        {"title": "Utaguchi + Node Collars", "nodes": ("Cylinder", "Cube"),
         "role": "geometry"},
        {"title": "Finger + Thumb Rims", "nodes": ("Cylinder", "Instance on Points"),
         "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_xun
# ---------------------------------------------------------------------------

def build_music_xun(group_name="MEL_music_xun"):
    """Xun: a top-blown egg-shaped clay vessel with a foot ring and 6 rims.

    A VESSEL, not a tube: the body is a UV sphere scaled into an egg, the blow
    rim sits on the crown, and there is NO windway (that is the ocarina). The six
    finger rims are split 3 + 3 across the two walls of the middle band, where the
    ellipsoid's radius factor is within 2% of R, so a constant-Y seat straddles
    the surface (lane law 2).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_xun"
    bx, by = 0, 0

    add_float_param(tree, "Body Height M", 0.105, 0.050, 0.200)
    add_float_param(tree, "Body Radius M", 0.045, 0.020, 0.090)
    add_float_param(tree, "Blow Radius M", 0.011, 0.005, 0.025)
    add_int_param(tree, "Hole Count", 6, 4, 10)
    add_float_param(tree, "Hole Radius M", 0.0048, 0.0020, 0.0100)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    H = gin.outputs["Body Height M"]
    R = gin.outputs["Body Radius M"]
    BR = gin.outputs["Blow Radius M"]
    HR = gin.outputs["Hole Radius M"]

    half_h = _m(tree, "MULTIPLY", (bx - 2200, by + 300), H, 0.5)
    foot_h = _m(tree, "MULTIPLY", (bx - 2200, by + 140), H, 0.10)
    band_first = _m(tree, "MULTIPLY", (bx - 2200, by - 20), H, 0.40)
    band_span = _m(tree, "MULTIPLY", (bx - 2200, by - 180), H, 0.18)
    seat_y = _m(tree, "MULTIPLY", (bx - 2200, by - 340), R, 0.96)
    rim_d = _m(tree, "MULTIPLY", (bx - 2200, by - 500), R, 0.30)

    # the egg: a UV sphere scaled on all three axes (origin at its own centre),
    # then lifted so its underside rests on z = 0
    egg = _sphere(tree, (bx - 1400, by), 1.0, segments=48, rings=24)
    body = _xf(tree, (bx - 1200, by), egg.outputs["Mesh"],
               scale=_vec(tree, (bx - 1600, by - 200), R, R, half_h),
               translation=_vec(tree, (bx - 1600, by - 400), 0.0, 0.0, half_h)
               ).outputs["Geometry"]

    # foot ring: a short open band standing on the floor, hugging the egg where
    # the ellipsoid's radius factor reaches 0.60 R (z = 0.10 H)
    foot = _shell_z(tree, (bx - 1400, by - 800),
                    _m(tree, "MULTIPLY", (bx - 2200, by - 800), R, 0.62),
                    foot_h, 0.0, verts=32)

    # blow rim on the crown (the xun is TOP-blown; no windway tube exists)
    blow = _cyl_z(tree, (bx - 1400, by - 1200),
                  _m(tree, "MULTIPLY", (bx - 2200, by - 1200), BR, 1.70),
                  _m(tree, "MULTIPLY", (bx - 2200, by - 1340), H, 0.10),
                  _m(tree, "MULTIPLY", (bx - 2200, by - 1480), H, 0.99),
                  verts=20)

    # six finger rims: 3 on the +Y wall and 3 on the -Y wall of the middle band
    front_n, back_n = _row_counts(tree, (bx - 3400, by - 1600),
                                  gin.outputs["Hole Count"])
    front = _rims_y(tree, (bx - 1400, by - 1800), front_n, band_span,
                    band_first, seat_y, HR, rim_d, verts=12)
    back = _rims_y(tree, (bx - 1400, by - 2200), back_n, band_span,
                   band_first, _neg_seat(tree, (bx - 2400, by - 2200), R, 0.96),
                   HR, rim_d, verts=12)

    geom = _join(tree, (bx + 400, by), [body, foot, blow, front, back])
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _attrs(tree, (bx + 400, by - 2600)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Clay Egg + Foot Ring", "nodes": ("UV Sphere", "Cylinder"),
         "role": "geometry"},
        {"title": "Blow Rim", "nodes": ("Cylinder",), "role": "geometry"},
        {"title": "Finger Rims (two walls)", "nodes": ("Cylinder", "Instance on Points"),
         "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_panpipes
# ---------------------------------------------------------------------------

def build_music_panpipes(group_name="MEL_music_panpipes"):
    """Panpipes (zampona): two bound rows of closed tubes, lengths graduated.

    The BUNDLE is the identity: the tubes are closed at their lower end, all
    mouthpiece ends share one aligned plane, and they are bound with cords. The
    front row is offset half a pitch from the back row, as a real zampona's two
    rows interleave. `Pipe Count` is SPLIT across the two rows (floor/rest), never
    applied to both.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_panpipes"
    bx, by = 0, 0

    add_int_param(tree, "Pipe Count", 13, 6, 24)
    add_float_param(tree, "Pipe Diameter M", 0.017, 0.008, 0.035)
    add_float_param(tree, "Longest Pipe M", 0.340, 0.150, 0.700)
    add_float_param(tree, "Shortest Ratio", 0.45, 0.25, 0.80)
    add_float_param(tree, "Row Gap Ratio", 0.30, 0.05, 0.80)
    add_int_param(tree, "Binding Count", 2, 1, 4)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    N = gin.outputs["Pipe Count"]
    D = gin.outputs["Pipe Diameter M"]
    LP = gin.outputs["Longest Pipe M"]
    r_pipe = _m(tree, "MULTIPLY", (bx - 2200, by + 300), D, 0.5)
    spread = _m(tree, "SUBTRACT", (bx - 2200, by + 140), 1.0,
                gin.outputs["Shortest Ratio"])
    row_dy = _m(tree, "MULTIPLY", (bx - 2200, by - 20), D,
                _m(tree, "ADD", (bx - 2400, by - 20),
                   gin.outputs["Row Gap Ratio"], 1.0))

    front_n, back_n = _row_counts(tree, (bx - 3600, by - 300), N)
    span_front = _m(tree, "MULTIPLY", (bx - 3200, by - 300), D,
                    _count_minus_one(tree, (bx - 3400, by - 300), front_n).outputs[0])
    span_back = _m(tree, "MULTIPLY", (bx - 3200, by - 500), D,
                   _count_minus_one(tree, (bx - 3400, by - 500), back_n).outputs[0])
    dx_half = _m(tree, "MULTIPLY", (bx - 3200, by - 700), D, 0.5)

    # proto: a CLOSED tube (NGON cap at the node end), origin shifted to its TOP
    tube = _cyl_proto_z(tree, (bx - 1400, by), r_pipe, LP, verts=16)
    proto = _top_proto_z(tree, (bx - 1200, by), tube, LP)

    front = _taper_rank(tree, (bx - 800, by), front_n, proto,
                        span_front, LP, spread, grad_axis="z")
    front = _xf(tree, (bx - 600, by), front,
                translation=_vec(tree, (bx - 600, by - 200), 0.0,
                                 _m(tree, "MULTIPLY", (bx - 2200, by - 200),
                                    row_dy, -0.5), 0.0)).outputs["Geometry"]
    back = _taper_rank(tree, (bx - 800, by - 600), back_n, proto,
                       span_back, LP, spread, grad_axis="z")
    back = _xf(tree, (bx - 600, by - 600), back,
               translation=_vec(tree, (bx - 600, by - 800), dx_half,
                                _m(tree, "MULTIPLY", (bx - 2200, by - 800),
                                   row_dy, 0.5), 0.0)).outputs["Geometry"]

    # bindings: open cords around the bundle, sized on the bundle's ACTUAL
    # half-extents. The X half-extent is half the WIDER ROW's span (plus the
    # row offset) — deriving it from N*D instead measured 1.9x too wide (a
    # 0.2276 ring on a 0.119 bundle, from the per-part probe). The Y half-extent
    # is the outer row's offset plus the tube radius.
    wx_half = _m(tree, "ADD", (bx - 2600, by - 1000),
                 _m(tree, "MULTIPLY", (bx - 2800, by - 1000),
                    _m(tree, "MAXIMUM", (bx - 3000, by - 1000),
                       span_front, span_back), 0.5),
                 _m(tree, "MULTIPLY", (bx - 2800, by - 1000), D, 0.5))
    wy_half = _m(tree, "ADD", (bx - 2600, by - 1200),
                 _m(tree, "MULTIPLY", (bx - 2800, by - 1200), row_dy, 0.5),
                 r_pipe)
    r_bind = _m(tree, "MULTIPLY", (bx - 2600, by - 1400),
                _m(tree, "MAXIMUM", (bx - 2800, by - 1400), wx_half, wy_half),
                1.03)
    cord_h = _m(tree, "MULTIPLY", (bx - 2600, by - 1600), D, 0.55)
    bindings = []
    for i in range(2):
        base = _m(tree, "MULTIPLY", (bx - 2600 - i * 200, by - 1800 - i * 200),
                  LP, 0.56 + 0.28 * i)
        bindings.append(_shell_z(tree, (bx - 1400, by - 1800 - i * 200),
                                 r_bind, cord_h, base, verts=32))

    geom = _join(tree, (bx + 400, by), [front, back] + bindings)
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _attrs(tree, (bx + 400, by - 2800)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Closed Tube Proto", "nodes": ("Cylinder", "Transform"),
         "role": "geometry"},
        {"title": "Two Pipe Rows", "nodes": ("Mesh Line", "Instance on Points"),
         "role": "instance"},
        {"title": "Bindings", "nodes": ("Cylinder",), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_quena
# ---------------------------------------------------------------------------

def build_music_quena(group_name="MEL_music_quena"):
    """Quena: a U-notched rim, a wide banded body, 6 finger rims + a thumb rim.

    The U-NOTCH is the identity: two proud walls and a notch floor standing above
    the top rim, so the player's airstream splits on the far edge. Distinct from
    the xiao's plain inward chamfer. Vertical, base on the floor.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_quena"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 0.390, 0.200, 0.700)
    add_float_param(tree, "Bore Radius M", 0.0085, 0.0040, 0.0180)
    add_float_param(tree, "Notch Depth Ratio", 0.30, 0.10, 0.60)
    add_int_param(tree, "Hole Count", 6, 4, 8)
    add_float_param(tree, "Hole Radius M", 0.0034, 0.0015, 0.0080)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Body Length M"]
    R = gin.outputs["Bore Radius M"]
    HR = gin.outputs["Hole Radius M"]

    half_L = _m(tree, "MULTIPLY", (bx - 2200, by + 300), L, 0.5)
    notch_h = _m(tree, "MULTIPLY", (bx - 2200, by + 140), L,
                 _m(tree, "MULTIPLY", (bx - 2400, by + 140),
                    gin.outputs["Notch Depth Ratio"], 0.10))
    rim_d = _m(tree, "MULTIPLY", (bx - 2200, by - 20), R, 0.90)
    band_d = _m(tree, "MULTIPLY", (bx - 2200, by - 180), L, 0.020)

    body = _cyl_z(tree, (bx - 1400, by), R, L, half_L, verts=32)
    top_ring = _shell_z(tree, (bx - 1400, by - 400),
                        _m(tree, "MULTIPLY", (bx - 2200, by - 400), R, 1.12),
                        _m(tree, "MULTIPLY", (bx - 2200, by - 540), L, 0.020),
                        _m(tree, "SUBTRACT", (bx - 2400, by - 540), L,
                           _m(tree, "MULTIPLY", (bx - 2600, by - 540), L, 0.020)),
                        verts=32)

    # the U-notch: two proud walls + a notch floor above the rim
    walls = []
    for i, sx in enumerate((-1.0, 1.0)):
        walls.append(_plate(
            tree, (bx - 1400, by - 800 - i * 200),
            _m(tree, "MULTIPLY", (bx - 2200, by - 800 - i * 200), R, 0.30),
            _m(tree, "MULTIPLY", (bx - 2200, by - 800 - i * 200), R, 1.90),
            notch_h,
            translation=_vec(
                tree, (bx - 1600, by - 960 - i * 200),
                _m(tree, "MULTIPLY", (bx - 2200, by - 960 - i * 200), R,
                   0.62 * sx),
                0.0,
                _m(tree, "ADD", (bx - 2400, by - 960 - i * 200), L,
                   _m(tree, "MULTIPLY", (bx - 2600, by - 960 - i * 200),
                      notch_h, 0.5)))))
    floor = _plate(tree, (bx - 1400, by - 1200),
                   _m(tree, "MULTIPLY", (bx - 2200, by - 1200), R, 1.24),
                   _m(tree, "MULTIPLY", (bx - 2200, by - 1360), R, 1.90),
                   _m(tree, "MULTIPLY", (bx - 2200, by - 1520), notch_h, 0.30),
                   translation=_vec(tree, (bx - 1600, by - 1520), 0.0, 0.0,
                                    _m(tree, "ADD", (bx - 2400, by - 1520), L,
                                       _m(tree, "MULTIPLY",
                                          (bx - 2600, by - 1520), notch_h, 0.15))))

    # banded foot: two thread bands
    bands = []
    for i in range(2):
        bands.append(_cyl_z(tree, (bx - 1400, by - 2000 - i * 200),
                            _m(tree, "MULTIPLY", (bx - 2200, by - 2000 - i * 200),
                               R, 1.16),
                            band_d,
                            _m(tree, "MULTIPLY",
                               (bx - 2200, by - 2000 - i * 200), L,
                               0.018 + 0.030 * i), verts=24))

    holes = _rims_y(
        tree, (bx - 1400, by - 2600), gin.outputs["Hole Count"],
        _m(tree, "MULTIPLY", (bx - 2200, by - 2600), L, 0.40),
        _m(tree, "MULTIPLY", (bx - 2200, by - 2740), L, 0.24),
        _m(tree, "MULTIPLY", (bx - 2200, by - 2880), R, 0.98),
        HR, rim_d, verts=12)
    thumb = _hole_y(
        tree, (bx - 1400, by - 3200), HR, rim_d,
        _neg_seat(tree, (bx - 2200, by - 3200), R, 0.98),
        _m(tree, "MULTIPLY", (bx - 2200, by - 3340), L, 0.42), verts=12)

    geom = _join(tree, (bx + 400, by),
                 [body, top_ring, floor, holes, thumb] + walls + bands)
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _attrs(tree, (bx + 400, by - 3800)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Body + Foot Bands", "nodes": ("Cylinder",), "role": "geometry"},
        {"title": "U-Notch", "nodes": ("Cube", "Cylinder"), "role": "geometry"},
        {"title": "Finger + Thumb Rims", "nodes": ("Cylinder", "Instance on Points"),
         "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_didgeridoo
# ---------------------------------------------------------------------------

def build_music_didgeridoo(group_name="MEL_music_didgeridoo"):
    """Didgeridoo: a long plain TAPERED trunk, beeswax collars, a bell rim.

    The defining feature is what is ABSENT: a didgeridoo has NO finger holes and
    NO keys, just a tapering bore. The family gate asserts the tree carries zero
    MeshLine ranks for exactly that reason. Laid along +X with its axis at the
    BELL radius, so the wide end rests on the floor and the mouth end lifts.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_didgeridoo"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 1.500, 0.800, 2.500)
    add_float_param(tree, "Mouth Radius M", 0.016, 0.008, 0.030)
    add_float_param(tree, "Bell Radius M", 0.038, 0.018, 0.080)
    add_float_param(tree, "Collar Radius Ratio", 1.55, 1.10, 2.20)
    add_int_param(tree, "Collar Count", 2, 1, 4)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Body Length M"]
    RM = gin.outputs["Mouth Radius M"]
    RB = gin.outputs["Bell Radius M"]

    half_L = _m(tree, "MULTIPLY", (bx - 2200, by + 300), L, 0.5)
    collar_d = _m(tree, "MULTIPLY", (bx - 2200, by + 140), L, 0.050)
    bell_d = _m(tree, "MULTIPLY", (bx - 2200, by - 20), L, 0.012)

    # the trunk: base (wide) at -L/2, apex (mouth) at +L/2, axis at z = RB
    trunk = _cone_x(tree, (bx - 1400, by), RB, RM, L,
                    _m(tree, "MULTIPLY", (bx - 2400, by), L, -0.5),
                    z=RB, sign=1.0, verts=32)

    # beeswax collars near the mouth end
    collars = []
    for i in range(2):
        collars.append(_cyl_x(
            tree, (bx - 1400, by - 400 - i * 200),
            _m(tree, "MULTIPLY", (bx - 2200, by - 400 - i * 200), RM,
               gin.outputs["Collar Radius Ratio"]),
            collar_d,
            _m(tree, "SUBTRACT", (bx - 2400, by - 400 - i * 200), half_L,
               _m(tree, "MULTIPLY", (bx - 2600, by - 400 - i * 200),
                  collar_d, 0.60 + 0.70 * i)),
            z=RB, verts=24))

    # bell rim: an open ring at the wide end. Its radius is 1.04 x RB, so it must
    # be seated at 1.04 x RB too — a proud rim on an axis at RB dips 0.04 RB
    # (1.5 mm) through the floor otherwise.
    bell_r = _m(tree, "MULTIPLY", (bx - 2200, by - 900), RB, 1.04)
    bell = _ring_x(tree, (bx - 1400, by - 900), bell_r, bell_d,
                   _m(tree, "ADD", (bx - 2400, by - 900),
                      _neg(tree, (bx - 2800, by - 900), half_L),
                      _m(tree, "MULTIPLY", (bx - 2600, by - 900), bell_d, 0.5)),
                   bell_r, verts=32)

    geom = _join(tree, (bx + 400, by), [trunk, bell] + collars)
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _attrs(tree, (bx + 400, by - 1800)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Tapered Trunk", "nodes": ("Cone",), "role": "geometry"},
        {"title": "Mouth Collars + Bell Rim", "nodes": ("Cylinder",),
         "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_tin_whistle
# ---------------------------------------------------------------------------

def build_music_tin_whistle(group_name="MEL_music_tin_whistle"):
    """Tin whistle: a STRAIGHT narrow metal tube under a moulded fipple head.

    The straight untapered bore is what separates it from the recorder (a tapered
    wooden body with a separate block); the fipple window is an open ring laid on
    the head's crown with a tilted labium plate just downstream. Laid along +X
    with its axis at the HEAD radius, so the fat head rests on the floor.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_tin_whistle"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 0.300, 0.150, 0.500)
    add_float_param(tree, "Bore Radius M", 0.0065, 0.0030, 0.0120)
    add_float_param(tree, "Head Radius Ratio", 1.45, 1.15, 2.00)
    add_int_param(tree, "Hole Count", 6, 4, 8)
    add_float_param(tree, "Hole Radius M", 0.0025, 0.0010, 0.0060)
    add_int_param(tree, "Collar Count", 2, 1, 4)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Body Length M"]
    R = gin.outputs["Bore Radius M"]
    HR = gin.outputs["Hole Radius M"]

    half_L = _m(tree, "MULTIPLY", (bx - 2200, by + 300), L, 0.5)
    head_r = _m(tree, "MULTIPLY", (bx - 2200, by + 140), R,
                gin.outputs["Head Radius Ratio"])
    head_d = _m(tree, "MULTIPLY", (bx - 2200, by - 20), L, 0.170)
    axis_z = head_r
    rim_d = _m(tree, "MULTIPLY", (bx - 2200, by - 180), R, 0.90)
    band_d = _m(tree, "MULTIPLY", (bx - 2200, by - 340), L, 0.012)

    body = _cyl_x(tree, (bx - 1400, by), R, L, 0.0, z=axis_z, verts=24)
    head = _cyl_x(tree, (bx - 1400, by - 400), head_r, head_d,
                  _m(tree, "ADD", (bx - 2400, by - 400),
                     _neg(tree, (bx - 2800, by - 400), half_L),
                     _m(tree, "MULTIPLY", (bx - 2600, by - 400), head_d, 0.5)),
                  z=axis_z, verts=24)

    # fipple window: an OPEN ring on the head's crown + a tilted labium plate
    window = _ring_z(tree, (bx - 1400, by - 800),
                     _m(tree, "MULTIPLY", (bx - 2200, by - 800), R, 0.55),
                     _m(tree, "MULTIPLY", (bx - 2200, by - 940), head_r, 1.30),
                     _m(tree, "ADD", (bx - 2400, by - 940), axis_z,
                        _m(tree, "MULTIPLY", (bx - 2600, by - 940),
                           head_r, 0.86)),
                     x=_m(tree, "ADD", (bx - 2400, by - 940),
                        _neg(tree, (bx - 2800, by - 940), half_L),
                          _m(tree, "MULTIPLY", (bx - 2600, by - 940),
                             head_d, 0.78)), verts=16)
    labium = _plate(tree, (bx - 1400, by - 1400),
                    _m(tree, "MULTIPLY", (bx - 2200, by - 1400), L, 0.020),
                    _m(tree, "MULTIPLY", (bx - 2200, by - 1560), head_r, 1.40),
                    _m(tree, "MULTIPLY", (bx - 2200, by - 1720), R, 0.70),
                    translation=_vec(
                        tree, (bx - 1600, by - 1720),
                        _m(tree, "ADD", (bx - 2400, by - 1720),
                           _neg(tree, (bx - 2800, by - 1720), half_L),
                           _m(tree, "MULTIPLY", (bx - 2600, by - 1720),
                              head_d, 1.10)),
                        0.0,
                        _m(tree, "ADD", (bx - 2400, by - 1720), axis_z,
                           _m(tree, "MULTIPLY", (bx - 2600, by - 1720),
                              head_r, 0.72))),
                    rotation=(0.0, math.radians(-22.0), 0.0))

    # binding ring just downstream of the head
    collars = []
    for i in range(2):
        collars.append(_cyl_x(
            tree, (bx - 1400, by - 2200 - i * 200),
            _m(tree, "MULTIPLY", (bx - 2200, by - 2200 - i * 200), R,
               1.20 + 0.02 * i),
            band_d,
            _m(tree, "ADD", (bx - 2400, by - 2200 - i * 200),
               _neg(tree, (bx - 2800, by - 2200 - i * 200), half_L),
               _m(tree, "MULTIPLY", (bx - 2600, by - 2200 - i * 200), L,
                  0.215 + 0.020 * i)),
            z=axis_z, verts=24))

    # The finger rims sit on the TOP of the bore, not on the AXIS: the bore's
    # surface is `axis_z + R`, and a rank seated at `axis_z` puts every rim
    # wholly INSIDE the tube (measured 0.00385 max radius against a 0.0065 bore,
    # 0.59 R — all six invisible). Every other X-laid instrument in the family has
    # its axis at z = 0, where `z_off = R` IS the surface; this is the one that
    # lifts its axis for a fat head, so the seat has to be lifted with it.
    rim_seat = _m(tree, "ADD", (bx - 2200, by - 3000), axis_z, R)
    holes = _rims_x(
        tree, (bx - 1400, by - 2800), gin.outputs["Hole Count"],
        _m(tree, "MULTIPLY", (bx - 2200, by - 2800), L, 0.420),
        _m(tree, "MULTIPLY", (bx - 2200, by - 2940), L, 0.030),
        rim_seat, HR, rim_d, verts=12)

    geom = _join(tree, (bx + 400, by),
                 [body, head, window, labium, holes] + collars)
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _attrs(tree, (bx + 400, by - 3400)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Straight Bore + Head", "nodes": ("Cylinder",), "role": "geometry"},
        {"title": "Fipple Window + Labium", "nodes": ("Cylinder", "Cube"),
         "role": "geometry"},
        {"title": "Finger Rims + Collars", "nodes": ("Cylinder", "Instance on Points"),
         "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

register_builder(
    "MEL_music_shakuhachi", build_music_shakuhachi, "Shakuhachi",
    "Shakuhachi: a wide-bore tapered bamboo flute with a flared root end, a "
    "slanted utaguchi blowing edge, bamboo node collars and four finger rims "
    "plus a thumb rim. Native-only.",
    "music",
)
register_builder(
    "MEL_music_xun", build_music_xun, "Xun",
    "Xun: a top-blown egg-shaped clay vessel with a foot ring, a crown blow rim "
    "and six finger rims split across the two walls of the middle band. "
    "Native-only.",
    "music",
)
register_builder(
    "MEL_music_panpipes", build_music_panpipes, "Panpipes",
    "Panpipes (zampona): two bound rows of closed tubes hanging from one aligned "
    "mouthpiece plane, lengths graduated and interleaved. Native-only.",
    "music",
)
register_builder(
    "MEL_music_quena", build_music_quena, "Quena",
    "Quena: an Andean end-blown flute with a U-notched rim (two proud walls and a "
    "notch floor), a banded body and six finger rims plus a thumb rim. "
    "Native-only.",
    "music",
)
register_builder(
    "MEL_music_didgeridoo", build_music_didgeridoo, "Didgeridoo",
    "Didgeridoo: a long plain tapered trunk with no finger holes, a beeswax "
    "mouthpiece collar pair and a bell rim. Native-only.",
    "music",
)
register_builder(
    "MEL_music_tin_whistle", build_music_tin_whistle, "Tin Whistle",
    "Tin whistle: a straight narrow metal tube under a moulded fipple head with a "
    "window ring and a tilted labium, six finger rims and binding rings. "
    "Native-only.",
    "music",
)
