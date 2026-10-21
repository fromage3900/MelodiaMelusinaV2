"""P4 wave 11 — auxiliary percussion lane: tom-tom, xylophone, washboard,
claves, cabasa, guiro.

Gap audit first (repo-wide grep over `deploy/surreal_arch/` + the live registry +
`Tools/registry_baseline.json`, 2026-10-04): the percussion lane owns timpani,
snare drum, bass drum, cymbals, tambourine, carillon, steelpan, gong, ocarina,
glockenspiel, celesta, marimba, vibraphone, tubular bells, and wave 10's six hand
drums (djembe, congas, bongos, cajon, frame drum, tabla). NONE of the six ids
below existed anywhere (grep count 0 each, 0 in the baseline):

    tom-tom, xylophone, washboard, claves, cabasa, guiro

`MEL_music_snare_drum` is a shallow shell with a strainer; the tom-tom is a deep
two-headed shell with a tension-rod basket. `MEL_music_marimba` is arched bars
over resonator tubes and `MEL_music_glockenspiel` is metal; the xylophone is
flat graduated WOOD bars on a bare rail frame with no resonators.
`MEL_music_frame_drum` is a wide shallow ring; the washboard is a corrugated
board. Claves, cabasa and guiro have no relative in the registry at all.

Design rules (same as music_world_percussion / music_keyboard_kit /
music_wind_folk):
  - Native-only. These are revolved shells, rods, boards and bead rings that 5.2
    primitives express exactly; a Higgsas subtree here would be decoration, not a
    lead. Every builder still stores `higgsas_lead` (1.0 = native) so the family
    gate and the instruments gate read the lane uniformly.
  - The wave-6/wave-10 origin-explicit helpers are REUSED, never re-authored:
    `_cone_z` takes the BASE (`MeshCone`'s origin is its base), `_cyl_z` /
    `_cyl_x` take the CENTRE, `_disc_z` / `_shell_z` / `_ring_rank` / `_mean_r` /
    `_tube_y` come from the wave-10 world-percussion lane, `_plate` links all
    three `Size` components, `_rank_inst` places a rank ONLY by its points.
  - Zero `MeshBoolean` in the lane: a cutter that touches the mesh's own boundary
    emits ZERO geometry with no error and no `link_failures` entry. Every rim,
    ring, port and notch is LAID ON, never cut.
  - A primitive `Size` component is never left at LITERAL ZERO (the
    castle-merlon zero-width-slab class).
  - A cone's tip radius is never 0: an NGON top cap at radius 0 is a degenerate
    face by construction.
  - Every lane builder sits ON the floor (realized min_z >= -0.01).

Lane-local law 1 — `_graded_rank`, a rank graduated in ONE axis. `_stand`
(wind_reed_brass) scales all three axes by index, which is right for organ pipes
and wrong for xylophone bars: a real bar shortens with pitch while its width and
height stay constant. `_graded_rank` applies `ScaleInstances` with a CombineXYZ
whose graduated component is the ratio and whose other two are literal 1.0, so
the bars read as a graduated keyboard rather than a shrinking stack.

Lane-local law 2 — a rank laid on a CONICAL host must FOLLOW the taper. The
guiro's notch rank crosses a straight cone, so its `MeshLine` offset carries a Z
component equal to the radius change over the span; a constant-Z rank (the naive
`_rank_inst(axis="x", z=r)`) floats off the surface at one end and buries itself
at the other. Same family as the wave-10 "seat a rank on a conical host" law,
except here the fix is the rank's own slope rather than a mean radius. Where the
rank is short relative to the taper (the tom-tom's two lug rings), the mean
radius is the right seat instead.

Builders:
    MEL_music_tom_tom      deep two-headed shell + 2 lug rings + rod basket + stand
    MEL_music_xylophone    13 flat graduated wood bars on a bare rail frame
    MEL_music_washboard    corrugated board + frame rails + laid-on thumb ring
    MEL_music_claves       exactly TWO hardwood rods with rounded ends
    MEL_music_cabasa       handle + bead-wrapped cylinder (5 bead rings)
    MEL_music_guiro        tapered gourd + a sloped rank of notches + scraper
"""

from __future__ import annotations

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
    _rank_axis, _rank, _half_span,
)
from .music_world_percussion import (
    _disc_z, _shell_z, _ring_rank, _mean_r, _tube_y,
)


# ---------------------------------------------------------------------------
# Lane-local laws
# ---------------------------------------------------------------------------

def _cyl_y(tree, loc, r, length, verts=10):
    """A cylinder laid along Y, CENTRED at its own origin.

    A guiro notch crosses the gourd's width, so the proto must lie along Y while
    the rank steps along X. `_cyl_x` / `_cyl_z` cannot express that; this is the
    third axis of the same idiom.
    """
    prim = _cyl(tree, loc, r, length, vertices=verts)
    if prim is None:
        return None
    return _xf(tree, (loc[0] + 200, loc[1]), prim.outputs["Mesh"],
               rotation=(1.5707963, 0.0, 0.0),
               translation=_vec(tree, (loc[0] + 200, loc[1] - 200),
                               0.0, 0.0, 0.0)).outputs["Geometry"]


def _graded_rank(tree, loc, count_sock, proto_geo, span_sock, base_z,
                 grad_axis="y", spread=0.62):
    """A rank stepped along X, graduated in ONE axis only, at `base_z`.

    `_stand`'s per-index scale is uniform in all three axes; a xylophone bar
    shortens with pitch while its width and height stay constant, so the scale
    vector here is `ratio` on `grad_axis` and a literal 1.0 on the other two.
    The proto's ORIGIN must be its own bottom (the scale is applied about the
    instance origin).
    """
    bx, by = loc
    denom = _m(tree, "MAXIMUM", (bx - 1200, by - 200),
               _m(tree, "SUBTRACT", (bx - 1400, by - 200), count_sock, 1.0), 1.0)
    step = _m(tree, "DIVIDE", (bx - 1000, by - 200), span_sock, denom)
    pts = _rank_axis(tree, (bx - 800, by), count_sock, "x",
                     _half_span(tree, (bx - 1000, by + 200), span_sock),
                     step, z=base_z)
    if pts is None:
        return None
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 800, by - 300))
    t = _m(tree, "DIVIDE", (bx - 600, by - 300), idx.outputs["Index"], denom)
    ratio = _m(tree, "SUBTRACT", (bx - 400, by - 300), 1.0,
               _m(tree, "MULTIPLY", (bx - 600, by - 440), t, spread))
    one = 1.0
    vec = {"x": (ratio, one, one), "y": (one, ratio, one),
           "z": (one, one, ratio)}[grad_axis]
    sc = _vec(tree, (bx - 200, by - 300), *vec)
    return _inst_rank(tree, (bx + 200, by), pts, proto_geo, scale_sock=sc)


def _perc_attrs(tree, loc):
    """The lane's shared attribute pair: a semitone tag + the native lead flag."""
    bx, by = loc
    sidx = safe_node(tree, "GeometryNodeInputIndex", (bx, by))
    smod = _m(tree, "MODULO", (bx, by - 140), sidx.outputs["Index"], 12.0)
    return [("drum_semitone_mod12", smod), ("higgsas_lead", 1.0)]


# ---------------------------------------------------------------------------
# MEL_music_tom_tom
# ---------------------------------------------------------------------------

def build_music_tom_tom(group_name="MEL_music_tom_tom"):
    """Tom-tom: a deep two-headed shell, two lug rings, a rod basket, a stand.

    TWO heads is the identity — `MEL_music_snare_drum` is a shallow shell with a
    strainer and `MEL_music_congas` is a pair of barrels with one head each. The
    shell is a slight taper (narrower at the bottom), the lugs are radial rings
    at both rims, and the tension rods are a radial rank connecting them.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_tom_tom"
    bx, by = 0, 0

    add_float_param(tree, "Shell Diameter M", 0.33, 0.20, 0.50)
    add_float_param(tree, "Shell Depth M", 0.30, 0.15, 0.55)
    add_float_param(tree, "Head Thickness M", 0.004, 0.001, 0.02)
    add_float_param(tree, "Lug Radius M", 0.010, 0.004, 0.03)
    add_int_param(tree, "Lug Count", 6, 4, 12)
    add_float_param(tree, "Stand Lift M", 0.26, 0.08, 0.5)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    R = _m(tree, "MULTIPLY", (bx - 1800, by + 300),
           gin.outputs["Shell Diameter M"], 0.5)
    D = gin.outputs["Shell Depth M"]
    t_head = gin.outputs["Head Thickness M"]
    lug_r = gin.outputs["Lug Radius M"]
    lift = gin.outputs["Stand Lift M"]
    foot_r = _m(tree, "MULTIPLY", (bx - 1800, by + 140), R, 0.86)
    # A rank on a CONICAL host is seated at the shell's radius AT ITS OWN
    # HEIGHT, never at the widest end and never at a blanket mean. The shell
    # runs foot_r -> R over D, so radius(z) = foot_r + (R - foot_r) * z/D; the
    # two lug rings sit at 0.10 D and 0.90 D and the rod rank spans the two, so
    # its own seat is the 0.50 D radius. (A single mean for both rings left each
    # one ~9 mm off its own rim: 0.874 R and 0.986 R against a 0.930 R seat.)
    d_r = _m(tree, "SUBTRACT", (bx - 2000, by + 140), R, foot_r)
    seat_lo = _m(tree, "ADD", (bx - 2000, by - 20), foot_r,
                 _m(tree, "MULTIPLY", (bx - 2200, by - 20), d_r, 0.10))
    seat_hi = _m(tree, "ADD", (bx - 2000, by - 180), foot_r,
                 _m(tree, "MULTIPLY", (bx - 2200, by - 180), d_r, 0.90))
    seat_mid = _m(tree, "ADD", (bx - 2000, by - 340), foot_r,
                  _m(tree, "MULTIPLY", (bx - 2200, by - 340), d_r, 0.50))
    top_z = _m(tree, "ADD", (bx - 2000, by - 500), lift, D)
    mid_z = _m(tree, "ADD", (bx - 2000, by - 660), lift,
               _m(tree, "MULTIPLY", (bx - 2200, by - 660), D, 0.5))
    lug_lo = _m(tree, "ADD", (bx - 2000, by - 820), lift,
                _m(tree, "MULTIPLY", (bx - 2200, by - 820), D, 0.10))
    lug_hi = _m(tree, "ADD", (bx - 2000, by - 980), lift,
                _m(tree, "MULTIPLY", (bx - 2200, by - 980), D, 0.90))

    # shell: a taper, closed (the heads sit on it, so no hollow interior)
    shell = _cone_z(tree, (bx - 1200, by), foot_r, R, D, lift, verts=32)
    # the two heads — the tom-tom's identity
    head_lo = _disc_z(tree, (bx - 1000, by - 200), foot_r, t_head, lift, verts=32)
    head_hi = _disc_z(tree, (bx - 1000, by - 400), R, t_head, top_z, verts=32)
    # lug rings at both rims + a rod rank connecting them, each seated at the
    # shell's radius AT ITS OWN HEIGHT (see seat_lo / seat_hi / seat_mid above)
    lug = _cyl_z(tree, (bx - 800, by - 660),
                 _m(tree, "MULTIPLY", (bx - 1000, by - 660), lug_r, 1.2),
                 _m(tree, "MULTIPLY", (bx - 1000, by - 660), lug_r, 1.6),
                 0.0, verts=8)
    lugs_lo = _ring_rank(tree, (bx - 600, by - 660), gin.outputs["Lug Count"],
                         lug, seat_lo, cz=lug_lo)
    lugs_hi = _ring_rank(tree, (bx - 600, by - 900), gin.outputs["Lug Count"],
                         lug, seat_hi, cz=lug_hi)
    rod = _cyl_z(tree, (bx - 800, by - 1100),
                 _m(tree, "MULTIPLY", (bx - 1000, by - 1100), lug_r, 0.42),
                 _m(tree, "SUBTRACT", (bx - 1200, by - 1100), lug_hi, lug_lo),
                 0.0, verts=8)
    rods = _ring_rank(tree, (bx - 600, by - 1100), gin.outputs["Lug Count"],
                      rod, seat_mid, cz=mid_z)
    # stand: a post from the floor + three splayed feet
    post = _cyl_z(tree, (bx - 1000, by + 700), 0.016, lift,
                  _m(tree, "MULTIPLY", (bx - 1200, by + 700), lift, 0.5),
                  verts=12)
    feet = []
    for i, (sx, sy) in enumerate(((-1.0, 0.0), (0.5, 0.866), (0.5, -0.866))):
        feet.append(_plate(tree, (bx - 800, by + 900 + i * 200),
                           0.11, 0.05, 0.022,
                           rotation=(0.0, 0.0, i * 2.0944),
                           translation=_vec(tree, (bx - 1000, by + 760 + i * 200),
                                           _m(tree, "MULTIPLY",
                                              (bx - 1400, by + 760 + i * 200),
                                              R, 0.62 * sx),
                                           _m(tree, "MULTIPLY",
                                              (bx - 1400, by + 600 + i * 200),
                                              R, 0.62 * sy),
                                           0.011)))

    geom = _join(tree, (bx + 400, by),
                 [shell, head_lo, head_hi, lugs_lo, lugs_hi, rods, post] + feet)
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _perc_attrs(tree, (bx + 400, by - 1500)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Two-Headed Shell", "nodes": ("Cone", "head_lo", "head_hi"),
         "role": "geometry"},
        {"title": "Lugs + Rod Basket", "nodes": ("Circle", "Instance on Points"),
         "role": "instance"},
        {"title": "Stand", "nodes": ("Cylinder", "Cube"), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_xylophone
# ---------------------------------------------------------------------------

def build_music_xylophone(group_name="MEL_music_xylophone"):
    """Xylophone: flat graduated WOOD bars on a bare rail frame, no resonators.

    The bare frame is the identity — `MEL_music_marimba` hangs arched bars over
    resonator tubes and `MEL_music_glockenspiel` is metal. Each bar here
    shortens with pitch while its width and height stay constant (lane law),
    which is why the rank is `_graded_rank` and not `_stand`.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_xylophone"
    bx, by = 0, 0

    add_int_param(tree, "Bar Count", 13, 6, 24)
    add_float_param(tree, "Longest Bar M", 0.38, 0.18, 0.7)
    add_float_param(tree, "Bar Width M", 0.026, 0.010, 0.06)
    add_float_param(tree, "Bar Height M", 0.022, 0.008, 0.05)
    add_float_param(tree, "Rail Spread M", 0.30, 0.12, 0.6)
    add_float_param(tree, "Frame Height M", 0.62, 0.3, 1.0)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    N = gin.outputs["Bar Count"]
    bar_l = gin.outputs["Longest Bar M"]
    bar_w = gin.outputs["Bar Width M"]
    bar_h = gin.outputs["Bar Height M"]
    spread = gin.outputs["Rail Spread M"]
    fh = gin.outputs["Frame Height M"]
    rail_t = _m(tree, "MULTIPLY", (bx - 2000, by + 300), bar_h, 0.9)
    half_bar = _m(tree, "MULTIPLY", (bx - 2000, by + 140), bar_h, 0.5)
    # the rank is WIDER than the longest bar: at 13 bars the pitch must clear the
    # bar width or the whole keyboard interpenetrates itself. Everything below
    # (rails, legs, end frames) is sized off `rank_span`, never off `bar_l`.
    rank_span = _m(tree, "MULTIPLY", (bx - 2000, by - 20), bar_l, 1.45)

    # bars: proto's ORIGIN is its own bottom, so `_graded_rank` scales about it.
    # A bar runs along Y (its length) and the rank steps along X, so each bar
    # rests across both rails.
    bar = _plate(tree, (bx - 1200, by), bar_w, bar_l, bar_h,
                 translation=_vec(tree, (bx - 1400, by - 200), 0.0, 0.0,
                                  half_bar))
    bars = _graded_rank(tree, (bx - 600, by), N, bar, rank_span, fh,
                        grad_axis="y")

    # rails: two long members running along X under the rank, tops flush with
    # Frame Height. They run PAST the end frames so the joints are real.
    rails = []
    for i, sy in enumerate((-1.0, 1.0)):
        rails.append(_plate(tree, (bx - 800, by - 700 - i * 200),
                            _m(tree, "MULTIPLY", (bx - 1600, by - 700 - i * 200),
                               rank_span, 1.12),
                            0.032, rail_t,
                            translation=_vec(tree,
                                             (bx - 1000, by - 860 - i * 200),
                                             0.0,
                                             _m(tree, "MULTIPLY",
                                                (bx - 1600, by - 860 - i * 200),
                                                spread, 0.5 * sy),
                                             _m(tree, "SUBTRACT",
                                                (bx - 1800, by - 860 - i * 200),
                                                fh, _m(tree, "MULTIPLY",
                                                       (bx - 2000,
                                                        by - 860 - i * 200),
                                                       rail_t, 0.5)))))
    # legs: four posts from the floor to the rails, INSIDE the end frames
    legs = []
    for i, (sx, sy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1))):
        legs.append(_plate(tree, (bx - 800, by - 1400 - i * 200),
                           0.034, 0.034, fh,
                           translation=_vec(tree,
                                            (bx - 1000, by - 1560 - i * 200),
                                            _m(tree, "MULTIPLY",
                                               (bx - 1600, by - 1560 - i * 200),
                                               rank_span, 0.46 * sx),
                                            _m(tree, "MULTIPLY",
                                               (bx - 1600, by - 1700 - i * 200),
                                               spread, 0.58 * sy),
                                            _m(tree, "MULTIPLY",
                                               (bx - 1600, by - 1700 - i * 200),
                                               fh, 0.5))))
    # end frames: cross-members tying the two rails together at both ends
    frames = []
    for i, sx in enumerate((-1.0, 1.0)):
        frames.append(_plate(tree, (bx - 800, by - 2300 - i * 200),
                             0.030,
                             _m(tree, "MULTIPLY", (bx - 1600, by - 2300 - i * 200),
                                spread, 1.16),
                             0.030,
                             translation=_vec(tree,
                                              (bx - 1000, by - 2460 - i * 200),
                                              _m(tree, "MULTIPLY",
                                                 (bx - 1600, by - 2460 - i * 200),
                                                 rank_span, 0.56 * sx),
                                              0.0,
                                              _m(tree, "SUBTRACT",
                                                 (bx - 1800, by - 2460 - i * 200),
                                                 fh, 0.015))))

    geom = _join(tree, (bx + 400, by), [bars] + rails + legs + frames)
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _perc_attrs(tree, (bx + 400, by - 2800)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Graduated Bars", "nodes": ("Cube", "Instance on Points"),
         "role": "instance"},
        {"title": "Bare Rail Frame", "nodes": ("Cube",), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_washboard
# ---------------------------------------------------------------------------

def build_music_washboard(group_name="MEL_music_washboard"):
    """Washboard: a corrugated board, a frame of rails, a laid-on thumb ring.

    The corrugation is a Z rank of thin X-laid ridges standing proud of the
    board's front face — laid on, never cut (the boolean class). The frame rails
    stand further proud so the board reads as a framed panel.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_washboard"
    bx, by = 0, 0

    add_float_param(tree, "Board Width M", 0.30, 0.15, 0.5)
    add_float_param(tree, "Board Height M", 0.42, 0.2, 0.7)
    add_float_param(tree, "Board Thickness M", 0.012, 0.004, 0.03)
    add_int_param(tree, "Rib Count", 14, 6, 30)
    add_float_param(tree, "Rib Radius M", 0.005, 0.002, 0.012)
    add_float_param(tree, "Frame Thickness M", 0.014, 0.005, 0.04)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    W = gin.outputs["Board Width M"]
    H = gin.outputs["Board Height M"]
    T = gin.outputs["Board Thickness M"]
    rib_r = gin.outputs["Rib Radius M"]
    ft = gin.outputs["Frame Thickness M"]
    # the frame's BOTTOM rail sits on the floor and the board's underside rests
    # on it: rail height is 0.10 H and its centre is 0.05 H, so the board centre
    # is 0.60 H. With board_cz = ft + H/2 the bottom rail hung to z = -0.028
    # (measured) — a part below the floor, which only a min_z check sees.
    board_cz = _m(tree, "MULTIPLY", (bx - 2000, by - 200), H, 0.60)
    # the frame plane sits exactly on the board's FRONT face: centre at
    # -(T/2 + ft/2), so the rail's back face is flush with the board and its
    # front face clears the rib band. Combined with the rails sitting outside
    # the rib band in BOTH X and Z, no two parts interpenetrate (the wave-9
    # placement-factor law).
    frame_y = _m(tree, "MULTIPLY", (bx - 2000, by - 360),
                 _m(tree, "ADD", (bx - 2200, by - 360),
                    _m(tree, "MULTIPLY", (bx - 2400, by - 360), T, 0.5), ft),
                 -1.0)

    board = _plate(tree, (bx - 1200, by), W, T, H,
                   translation=_vec(tree, (bx - 1400, by - 200), 0.0, 0.0,
                                    board_cz))
    # ribs: X-laid ridges, ranked in Z, standing proud of the -Y face
    rib = _cyl_x(tree, (bx - 1200, by - 700),
                 rib_r,
                 _m(tree, "MULTIPLY", (bx - 1400, by - 700), W, 0.94),
                 0.0, y=0.0, z=0.0, verts=10)
    rib_span = _m(tree, "MULTIPLY", (bx - 2000, by - 700), H, 0.78)
    ribs = _rank_inst(tree, (bx - 700, by - 700), gin.outputs["Rib Count"],
                      rib, rib_span,
                      _m(tree, "ADD", (bx - 2200, by - 700), ft,
                         _m(tree, "MULTIPLY", (bx - 2400, by - 700), H, 0.11)),
                      axis="z",
                      y=_m(tree, "MULTIPLY", (bx - 2200, by - 860), T, -0.5),
                      x=0.0)
    # frame: top + bottom rails (wide in X, thin in Z) and left + right stiles
    # (thin in X, tall in Z). Every rail sits OUTSIDE the rib band in both axes.
    frames = []
    for i, (sx, sz) in enumerate(((0.0, 1.0), (0.0, -1.0), (-1.0, 0.0),
                                  (1.0, 0.0))):
        across = sz != 0.0
        frames.append(_plate(
            tree, (bx - 800, by - 1200 - i * 200),
            _m(tree, "MULTIPLY", (bx - 1600, by - 1200 - i * 200), W,
               (1.06 if across else 0.10)),
            _m(tree, "MULTIPLY", (bx - 1600, by - 1200 - i * 200), ft, 1.4),
            _m(tree, "MULTIPLY", (bx - 1600, by - 1200 - i * 200), H,
               (0.10 if across else 1.0)),
            translation=_vec(
                tree, (bx - 1000, by - 1360 - i * 200),
                _m(tree, "MULTIPLY", (bx - 1600, by - 1360 - i * 200), W,
                   0.53 * sx),
                frame_y,
                _m(tree, "ADD", (bx - 1800, by - 1360 - i * 200),
                   _m(tree, "MULTIPLY", (bx - 2000, by - 1360 - i * 200), H,
                      0.55 * sz),
                   board_cz))))
    # thumb ring: an open ring mounted on the front of the top rail
    thumb = _tube_y(tree, (bx - 1000, by - 2200),
                    _m(tree, "MULTIPLY", (bx - 1600, by - 2200), ft, 1.1),
                    _m(tree, "MULTIPLY", (bx - 1600, by - 2360), T, 1.4),
                    frame_y,
                    z=_m(tree, "ADD", (bx - 1800, by - 2360),
                         _m(tree, "MULTIPLY", (bx - 2000, by - 2360), H, 0.60),
                         board_cz), verts=20)

    geom = _join(tree, (bx + 400, by), [board, ribs, thumb] + frames)
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _perc_attrs(tree, (bx + 400, by - 2600)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Board + Ribs", "nodes": ("Cube", "Instance on Points"),
         "role": "instance"},
        {"title": "Frame + Thumb Ring", "nodes": ("Cube", "Cylinder"),
         "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_claves
# ---------------------------------------------------------------------------

def build_music_claves(group_name="MEL_music_claves"):
    """Claves: exactly TWO hardwood rods with rounded ends, side by side.

    The PAIR is the identity and the count is a LITERAL 2 (a rank driven by a
    group input would let the user make four claves). Each rod is a cylinder
    with a sphere at either end, so the striking faces are domed.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_claves"
    bx, by = 0, 0

    add_float_param(tree, "Length M", 0.20, 0.10, 0.35)
    add_float_param(tree, "Diameter M", 0.025, 0.010, 0.05)
    add_float_param(tree, "Pair Gap M", 0.045, 0.010, 0.15)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Length M"]
    D = gin.outputs["Diameter M"]
    gap = gin.outputs["Pair Gap M"]
    r_rod = _m(tree, "MULTIPLY", (bx - 2000, by + 300), D, 0.5)
    cz = r_rod

    # the rod proto: a cylinder CENTRED at the origin, domed at both ends
    shaft = _cyl_x(tree, (bx - 1200, by), r_rod, L, 0.0, z=cz, verts=16)
    caps = []
    for i, sx in enumerate((-1.0, 1.0)):
        s = _sphere(tree, (bx - 1200, by - 400 - i * 200), r_rod,
                    segments=16, rings=10)
        caps.append(_xf(tree, (bx - 1000, by - 400 - i * 200),
                        s.outputs["Mesh"],
                        translation=_vec(tree, (bx - 1000, by - 600 - i * 200),
                                         _m(tree, "MULTIPLY",
                                            (bx - 1600, by - 600 - i * 200),
                                            L, 0.5 * sx),
                                         0.0, cz)).outputs["Geometry"])
    rod = _join(tree, (bx - 700, by), [shaft] + caps)

    # TWO rods, ranked along Y about the origin. The count is a LITERAL INT — a
    # rank driven by a group input would let the user make four claves, and a
    # FLOAT literal into MeshLine's INT `Count` socket is dropped SILENTLY by
    # `_wire` (its `default_value =` assignment raises), leaving the node on its
    # default of 10. Measured before the fix: 3240 verts (10 rods) and a y
    # extent of 0.43 against 648 verts and 0.045 with `2`.
    claves = _rank_inst(tree, (bx - 400, by), 2, rod, gap,
                        _half_span(tree, (bx - 600, by), gap), axis="y")

    geom = _join(tree, (bx + 400, by), [claves])
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _perc_attrs(tree, (bx + 400, by - 900)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Two Rods", "nodes": ("Cylinder", "Sphere"), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_cabasa
# ---------------------------------------------------------------------------

def build_music_cabasa(group_name="MEL_music_cabasa"):
    """Cabasa: a handle under a cylinder wrapped in five rings of beads.

    The bead COIL is the identity — five radial rings of small spheres up the
    body, each a `MeshCircle`(NONE) -> `MeshToPoints` -> `InstanceOnPoints`
    (lane law 1), which is what makes it a chain of beads rather than a painted
    band. Standing on its handle, so min_z = 0.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_cabasa"
    bx, by = 0, 0

    add_float_param(tree, "Body Diameter M", 0.10, 0.04, 0.20)
    add_float_param(tree, "Body Length M", 0.14, 0.06, 0.28)
    add_float_param(tree, "Handle Length M", 0.12, 0.04, 0.30)
    add_float_param(tree, "Handle Radius M", 0.013, 0.005, 0.03)
    add_int_param(tree, "Bead Count", 16, 6, 40)
    add_float_param(tree, "Bead Radius M", 0.0045, 0.002, 0.012)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    Rb = _m(tree, "MULTIPLY", (bx - 2000, by + 300),
            gin.outputs["Body Diameter M"], 0.5)
    Lb = gin.outputs["Body Length M"]
    Lh = gin.outputs["Handle Length M"]
    Rh = gin.outputs["Handle Radius M"]
    bead_r = gin.outputs["Bead Radius M"]
    body_base = Lh
    body_cz = _m(tree, "ADD", (bx - 2000, by - 200), Lh,
                 _m(tree, "MULTIPLY", (bx - 2200, by - 200), Lb, 0.5))

    handle = _cyl_z(tree, (bx - 1200, by), Rh,
                    Lh, _m(tree, "MULTIPLY", (bx - 1400, by), Lh, 0.5),
                    verts=16)
    body = _cyl_z(tree, (bx - 1200, by - 300), Rb, Lb, body_cz, verts=24)
    bead = _sphere(tree, (bx - 1200, by - 700), bead_r, segments=12, rings=8)
    bead_r_ring = _m(tree, "ADD", (bx - 2000, by - 700), Rb, bead_r)

    # five bead rings up the body (a coil). Each ring's own cz is a math chain
    # off Body Length, so the coil follows the body's real span.
    rings = []
    for i in range(5):
        frac = 0.12 + 0.19 * i
        cz = _m(tree, "ADD", (bx - 2400 - i * 200, by - 900),
                body_base,
                _m(tree, "MULTIPLY", (bx - 2600 - i * 200, by - 900), Lb,
                   frac))
        rings.append(_ring_rank(tree, (bx - 800, by - 900 - i * 200),
                                gin.outputs["Bead Count"], bead.outputs["Mesh"],
                                bead_r_ring, cz=cz))

    geom = _join(tree, (bx + 400, by), [handle, body] + rings)
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _perc_attrs(tree, (bx + 400, by - 2200)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Handle + Body", "nodes": ("Cylinder",), "role": "geometry"},
        {"title": "Bead Coil", "nodes": ("Circle", "Instance on Points"),
         "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_guiro
# ---------------------------------------------------------------------------

def build_music_guiro(group_name="MEL_music_guiro"):
    """Guiro: a tapered gourd with a rank of cross notches and a scraper.

    The notch rank is the identity — thin Y-laid ridges stepped along the
    gourd's own length (the rank's proto lies across the body, not along it).
    The gourd rests on its widest section, so min_z = 0.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_guiro"
    bx, by = 0, 0

    add_float_param(tree, "Body Length M", 0.32, 0.15, 0.6)
    add_float_param(tree, "Body Diameter M", 0.075, 0.03, 0.16)
    add_int_param(tree, "Notch Count", 12, 6, 28)
    add_float_param(tree, "Notch Radius M", 0.0032, 0.001, 0.008)
    add_float_param(tree, "Scraper Length M", 0.22, 0.08, 0.4)
    add_float_param(tree, "Scraper Radius M", 0.005, 0.002, 0.012)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    L = gin.outputs["Body Length M"]
    R = _m(tree, "MULTIPLY", (bx - 2000, by + 300),
           gin.outputs["Body Diameter M"], 0.5)
    notch_r = gin.outputs["Notch Radius M"]
    head_r = _m(tree, "MULTIPLY", (bx - 2000, by + 140), R, 0.72)
    tail_r = _m(tree, "MULTIPLY", (bx - 2000, by - 20), R, 0.42)
    # length fractions along X: head at -0.5 L, belly at +0.08 L, tail at +0.5 L.
    # The head-side cone therefore runs 0.58 L and the tail-side cone 0.42 L, so
    # each cone's APEX lands exactly on the belly (a length of 0.5 L would put
    # the apex 0.08 L short of it and leave a gap at the widest point).
    head_frac, mid_frac, tail_frac = -0.5, 0.08, 0.5
    head_len = _m(tree, "MULTIPLY", (bx - 2000, by - 180), L,
                  mid_frac - head_frac)
    tail_len = _m(tree, "MULTIPLY", (bx - 2000, by - 340), L,
                  tail_frac - mid_frac)
    head_x = _m(tree, "MULTIPLY", (bx - 2000, by - 500), L, head_frac)
    mid_x = _m(tree, "MULTIPLY", (bx - 2000, by - 660), L, mid_frac)
    tail_x = _m(tree, "MULTIPLY", (bx - 2000, by - 820), L, tail_frac)

    # the gourd: a long taper from the belly down to the head, then a short cone
    # back down to the tail. Both axes sit at z = R, so the belly rests at z = 0.
    gourd_a = _cone_x(tree, (bx - 1200, by), R, head_r, head_len, mid_x,
                      z=R, sign=-1.0, verts=24)
    gourd_b = _cone_x(tree, (bx - 1200, by - 400), tail_r, R, tail_len,
                      tail_x, z=R, sign=-1.0, verts=24)
    cap = _sphere(tree, (bx - 1200, by - 800), head_r, segments=16, rings=10)
    cap_geo = _xf(tree, (bx - 1000, by - 800), cap.outputs["Mesh"],
                  translation=_vec(tree, (bx - 1000, by - 1000), head_x,
                                   0.0, R)).outputs["Geometry"]

    # notches: Y-laid ridges ranked along the HEAD-side cone, whose surface
    # radius runs linearly from head_r at -0.5 L to R at +0.08 L. The rank's
    # first point AND its per-step Z offset are read off that taper, so every
    # notch straddles the real surface (lane law 2). A constant-Z rank floats
    # off the narrow end and buries itself at the wide end.
    band_a, band_b = -0.38, 0.02
    u_a = (band_a - head_frac) / (mid_frac - head_frac)
    u_b = (band_b - head_frac) / (mid_frac - head_frac)
    n_start_x = _m(tree, "MULTIPLY", (bx - 2400, by - 1200), L, band_a)
    n_end_x = _m(tree, "MULTIPLY", (bx - 2400, by - 1360), L, band_b)
    n_dr = _m(tree, "SUBTRACT", (bx - 2600, by - 1520), R, head_r)
    n_start_r = _m(tree, "ADD", (bx - 2600, by - 1680), head_r,
                   _m(tree, "MULTIPLY", (bx - 2800, by - 1680), n_dr, u_a))
    n_end_r = _m(tree, "ADD", (bx - 2600, by - 1840), head_r,
                 _m(tree, "MULTIPLY", (bx - 2800, by - 1840), n_dr, u_b))
    n_denom = _m(tree, "MAXIMUM", (bx - 3000, by - 2000),
                 _m(tree, "SUBTRACT", (bx - 3200, by - 2000),
                    gin.outputs["Notch Count"], 1.0), 1.0)
    n_dx = _m(tree, "DIVIDE", (bx - 3400, by - 2000),
              _m(tree, "SUBTRACT", (bx - 3600, by - 2000), n_end_x, n_start_x),
              n_denom)
    n_dz = _m(tree, "DIVIDE", (bx - 3400, by - 2160),
              _m(tree, "SUBTRACT", (bx - 3600, by - 2160), n_end_r, n_start_r),
              n_denom)
    notch = _cyl_y(tree, (bx - 1200, by - 1200), notch_r,
                   _m(tree, "MULTIPLY", (bx - 2000, by - 1200), R, 1.5),
                   verts=8)
    notch_pts = _rank(tree, (bx - 600, by - 1200), gin.outputs["Notch Count"],
                      _vec(tree, (bx - 900, by - 1400), n_start_x, 0.0,
                           n_start_r),
                      _vec(tree, (bx - 900, by - 1540), n_dx, 0.0, n_dz))
    notches = _inst_rank(tree, (bx - 400, by - 1200), notch_pts, notch)

    # scraper: a thin rod laid beside the gourd
    scraper = _cyl_x(tree, (bx - 1200, by - 1800),
                     gin.outputs["Scraper Radius M"],
                     gin.outputs["Scraper Length M"], 0.0,
                     y=_m(tree, "MULTIPLY", (bx - 2000, by - 1800), R, 1.7),
                     z=gin.outputs["Scraper Radius M"], verts=10)

    geom = _join(tree, (bx + 400, by),
                 [gourd_a, gourd_b, cap_geo, notches, scraper])
    _finish(tree, gin, gout, geom, (bx + 700, by), BID,
            _perc_attrs(tree, (bx + 400, by - 2400)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Tapered Gourd", "nodes": ("Cone", "Sphere"), "role": "geometry"},
        {"title": "Notch Rank", "nodes": ("Cylinder", "Instance on Points"),
         "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"),
         "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

register_builder(
    "MEL_music_tom_tom", build_music_tom_tom, "Tom-Tom",
    "Tom-tom: a deep two-headed tapered shell with lug rings at both rims, a "
    "radial tension-rod basket and a floor stand. Native-only.",
    "music",
)
register_builder(
    "MEL_music_xylophone", build_music_xylophone, "Xylophone",
    "Xylophone: flat graduated wood bars (length-only graduation) on a bare "
    "rail frame with no resonators. Native-only.",
    "music",
)
register_builder(
    "MEL_music_washboard", build_music_washboard, "Washboard",
    "Washboard: a corrugated board with a rank of laid-on ridges, a proud frame "
    "of rails and a thumb ring. Native-only.",
    "music",
)
register_builder(
    "MEL_music_claves", build_music_claves, "Claves",
    "Claves: exactly two hardwood rods with domed ends, side by side. "
    "Native-only.",
    "music",
)
register_builder(
    "MEL_music_cabasa", build_music_cabasa, "Cabasa",
    "Cabasa: a handle under a cylinder wrapped in five radial rings of beads. "
    "Native-only.",
    "music",
)
register_builder(
    "MEL_music_guiro", build_music_guiro, "Guiro",
    "Guiro: a tapered gourd with a rank of cross notches and a scraper rod. "
    "Native-only.",
    "music",
)
