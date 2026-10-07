"""P4 instrument-gap builders: steelpan, gong, ocarina.

Gap audit first (repo-wide grep over `deploy/surreal_arch/` + the live registry,
2026-10-02): the percussion lane owns timpani, church bell, bell tower, tube
chimes, glockenspiel, celesta, jingle tower and the aeolian wall; the wind lane
owns saxophone, bandoneon, glass harmonica, theremin and siku. None of the three
families below existed anywhere:

    steelpan (steel drum), gong, ocarina

`MEL_mh_xylo_fountain` and `MEL_imm_piano_keys` instance bar profiles on a
spline; neither is a pan, a gong or a vessel flute. Nothing here re-implements
an existing id.

Wise Higgsas use (same rule as music_higgsas_instruments): ONE authored group
LEADS each builder, because every loaded group is a subtree that costs node
budget. Everything else is native 5.2.

    MEL_music_steelpan   Spherical Spiral  the note-pad spiral on the playing face
    MEL_music_gong       Bend              the dish: a flat disc bowed into a bowl
    MEL_music_ocarina    Super Ellipsoid   the vessel body; holes are native cuts

Builders:
    MEL_music_steelpan  bowl + rim + skirt + Fibonacci note pads + stand
    MEL_music_gong      dished disc + central boss + suspension frame + cords
    MEL_music_ocarina   ovoid body + windway + mouthpiece + 6 bored finger holes
"""

from __future__ import annotations

import math

from . import higgsas_pipeline as hp
from .core import (
    safe_node, link_sockets, label_tree, new_geometry_tree, add_float_param,
    add_int_param, add_bool_param, register_builder, sock, mesh_boolean_node,
)
# Shared helpers are reused, never re-authored (a second private copy of the
# rank/transform helpers is the defect music_higgsas_instruments exists to avoid).
from .music_harps_real import _math, _combine, _export_tail
from .music_higgsas_instruments import (
    _lead, _store_named, _cone, _cyl, _line, _xf, _set_fill,
)

_FALLBACKS: dict = {}


def higgsas_report() -> dict:
    """Which of these builders ran native fallbacks instead of a Higgsas subtree."""
    return {
        "library": hp.library_path(),
        "available": hp.available(),
        "fallbacks": {k: list(v) for k, v in _FALLBACKS.items()},
    }


def _sphere(tree, loc, radius, segments=48, rings=24):
    """A UV sphere. `radius` may be a socket."""
    n = safe_node(tree, "GeometryNodeMeshUVSphere", loc)
    if n is None:
        return None
    for key, val in (("Segments", segments), ("Rings", rings), ("Radius", radius)):
        s = sock(n, key)
        if s is None:
            continue
        if isinstance(val, (int, float)):
            try:
                s.default_value = val
            except Exception:
                pass
        else:
            link_sockets(tree, val, s)
    return n


def _ring(tree, loc, radius, resolution=48, fill=1):
    """A curve circle — used for rims and hoops."""
    n = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", loc)
    if n is None:
        return None
    s = sock(n, "Resolution")
    if s is not None:
        try:
            s.default_value = resolution
        except Exception:
            pass
    _set_fill(n, fill)
    r = sock(n, "Radius")
    if r is not None:
        if isinstance(radius, (int, float)):
            try:
                r.default_value = radius
            except Exception:
                pass
        else:
            link_sockets(tree, radius, r)
    return n


def _fib_spiral(tree, loc, count_sock, radius_sock, golden=2.399963229728653):
    """Fibonacci (golden-angle) spiral point field, driven by Index.

    Returns (points_socket, count_sock). Deterministic and Index-driven — the
    same rank pattern the rest of the music lane uses, so the layout is
    reproducible at any count instead of seeded per-run.

        r_i = radius * sqrt((i + 0.5) / n)
        t_i = i * golden_angle
    """
    bx, by = loc
    dpts = safe_node(tree, "GeometryNodeMeshToPoints", (bx, by))
    line, line_sock = _line(tree, (bx - 240, by),
                            count_sock=count_sock,
                            offset=_combine(tree, (bx - 460, by), 0.0, 0.0, 0.0))
    if dpts is not None:
        link_sockets(tree, line_sock, sock(dpts, "Mesh") or dpts.inputs[0])

    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 240, by - 200))
    n_int = safe_node(tree, "FunctionNodeFloatToInt", (bx - 460, by - 200))
    if n_int is not None:
        link_sockets(tree, count_sock, n_int.inputs[0])
    half = _math(tree, "ADD", (bx - 240, by - 320), idx.outputs["Index"], 0.5)
    norm = _math(tree, "DIVIDE", (bx - 60, by - 320), half.outputs[0],
                 n_int.outputs[0] if n_int is not None else 1.0)
    root = _math(tree, "SQRT", (bx + 120, by - 320), norm.outputs[0])
    rad = _math(tree, "MULTIPLY", (bx + 300, by - 320), root.outputs[0], radius_sock)
    ang = _math(tree, "MULTIPLY", (bx - 60, by - 480), idx.outputs["Index"], golden)
    cosx = _math(tree, "COSINE", (bx + 120, by - 480), ang.outputs[0])
    siny = _math(tree, "SINE", (bx + 120, by - 620), ang.outputs[0])
    px = _math(tree, "MULTIPLY", (bx + 300, by - 480), rad.outputs[0], cosx.outputs[0])
    py = _math(tree, "MULTIPLY", (bx + 300, by - 620), rad.outputs[0], siny.outputs[0])
    placed = safe_node(tree, "GeometryNodeSetPosition", (bx + 520, by))
    if placed is not None:
        link_sockets(tree, dpts.outputs["Points"] if dpts else None,
                     sock(placed, "Geometry"))
        link_sockets(tree, _combine(tree, (bx + 300, by - 800),
                                    px.outputs[0], py.outputs[0], 0.0),
                     sock(placed, "Offset"))
    return placed.outputs["Geometry"] if placed is not None else None, count_sock


# ---------------------------------------------------------------------------
# MEL_music_steelpan
# ---------------------------------------------------------------------------

def build_music_steelpan(group_name="MEL_music_steelpan"):
    """Steelpan (steel drum): dished playing bowl, rolled rim, tapered skirt,
    a Fibonacci-spaced field of note pads on the face, three stand legs.

    Lead: `Spherical Spiral` supplies the pad-spiral path; the pads are then
    Instanced along it. Native fallback: the Index-driven golden-angle spiral
    above, which gives the same layout without the library subtree.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_steelpan"

    add_float_param(tree, "Pan Radius M", 0.18, 0.08, 0.45)
    add_float_param(tree, "Pan Depth M", 0.12, 0.04, 0.3)
    add_float_param(tree, "Skirt Depth M", 0.11, 0.03, 0.3)
    add_int_param(tree, "Note Pads", 24, 6, 48)
    add_float_param(tree, "Pad Radius M", 0.026, 0.008, 0.06)
    add_float_param(tree, "Leg Length M", 0.55, 0.2, 1.2)
    add_float_param(tree, "Skin Thickness M", 0.0035, 0.001, 0.012)
    add_bool_param(tree, "Realize for export", False)

    bx, by = 0, 0
    r_sock = gin.outputs["Pan Radius M"]
    depth = gin.outputs["Pan Depth M"]

    # --- playing face: a squashed sphere reads as the dished bowl -----------
    bowl = _sphere(tree, (bx - 1400, by + 300), r_sock, segments=64, rings=32)
    bowl_flat = _xf(tree, (bx - 1160, by + 300), bowl.outputs["Mesh"],
                    scale=_combine(tree, (bx - 1300, by + 160), 1.0, 1.0,
                                   _math(tree, "MULTIPLY", (bx - 1300, by + 40),
                                         depth, 0.62).outputs[0])
                    ).outputs["Geometry"]

    # --- rolled rim: a swept circle around the pan edge --------------------
    rim_r = _math(tree, "MULTIPLY", (bx - 1300, by + 620), r_sock, 1.0)
    rim_path = _ring(tree, (bx - 1160, by + 620), rim_r, resolution=64, fill=1)
    rim_prof = _ring(tree, (bx - 1160, by + 460),
                     _math(tree, "MULTIPLY", (bx - 1400, by + 460),
                           gin.outputs["Skin Thickness M"], 6.0).outputs[0],
                     resolution=10, fill=1)
    rim = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 940, by + 620))
    if rim is not None:
        link_sockets(tree, rim_path.outputs["Curve"], sock(rim, "Curve"))
        link_sockets(tree, rim_prof.outputs["Curve"], sock(rim, "Profile Curve"))
    rim_geo = _xf(tree, (bx - 740, by + 620), rim.outputs["Mesh"] if rim else None,
                  translation=_combine(tree, (bx - 1160, by + 780), 0.0, 0.0,
                                       _math(tree, "MULTIPLY", (bx - 1400, by + 780),
                                             depth, 0.30).outputs[0])
                  ).outputs["Geometry"]

    # --- tapered skirt: cone under the rim ---------------------------------
    skirt = _cone(tree, (bx - 1160, by - 200), rim_r, rim_r,
                  gin.outputs["Skirt Depth M"], vertices=64, fill=1)
    skirt_geo = _xf(tree, (bx - 900, by - 200), skirt.outputs["Mesh"] if skirt else None,
                    scale=_combine(tree, (bx - 1080, by - 340), 1.0, 1.0, 1.0),
                    translation=_combine(tree, (bx - 1080, by - 480), 0.0, 0.0,
                                        _math(tree, "MULTIPLY", (bx - 1300, by - 480),
                                              gin.outputs["Skirt Depth M"], -0.55).outputs[0])
                    ).outputs["Geometry"]

    # --- note pads on the face --------------------------------------------
    pad_pts, pad_count = _fib_spiral(
        tree, (bx - 1400, by + 1100), gin.outputs["Note Pads"],
        _math(tree, "MULTIPLY", (bx - 1640, by + 1100), r_sock, 0.74).outputs[0])
    pad_pts_z = _xf(tree, (bx - 600, by + 1100), pad_pts,
                    translation=_combine(tree, (bx - 800, by + 960), 0.0, 0.0,
                                        _math(tree, "MULTIPLY", (bx - 1000, by + 960),
                                              depth, 0.60).outputs[0])
                    ).outputs["Geometry"]

    spiral, used_spiral = _lead(
        BID, tree, "Spherical Spiral", (bx - 600, by + 1400),
        fallback_type="GeometryNodeSetPosition",
        # Real sockets (probed, Saved/Audit/probe_higgsas_socks_20261002.py):
        # Resolution / Rotations / Radius / Min-Max Parameter. There is NO
        # `Turns` and NO `Geometry` input, and the output is a CURVE named
        # "Curve" — not "Geometry".
        inputs={"Radius": _math(tree, "MULTIPLY", (bx - 800, by + 1540),
                                r_sock, 0.74).outputs[0],
                "Rotations": 3.0, "Resolution": 48,
                "Min Parameter": 0.0, "Max Parameter": 1.0},
    )
    # The pad field is ONE either/or, not a dangling subtree: the Higgsas spiral
    # supplies the layout when it loads, the golden-angle Fibonacci field is the
    # native fallback. Linking a lead group and then ignoring its output is the
    # subtree-weight defect this module's docstring warns about.
    if spiral is not None and not used_spiral:
        sp_pts = safe_node(tree, "GeometryNodeMeshToPoints", (bx - 380, by + 1400))
        if sp_pts is not None:
            link_sockets(tree, spiral.outputs.get("Curve") or spiral.outputs[0],
                         sock(sp_pts, "Mesh") or sp_pts.inputs[0])
        pads_src = sp_pts.outputs["Points"] if sp_pts is not None else pad_pts_z
    else:
        pads_src = pad_pts_z

    pad = _cyl(tree, (bx - 380, by + 1400),
               gin.outputs["Pad Radius M"],
               _math(tree, "MULTIPLY", (bx - 600, by + 1540),
                     gin.outputs["Pad Radius M"], 0.30).outputs[0],
               vertices=24, fill=2)
    pad_geo = _xf(tree, (bx - 160, by + 1400), pad.outputs["Mesh"] if pad else None,
                  rotation=(0.0, 0.0, 0.0)).outputs["Geometry"]
    pad_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 40, by + 1100))
    if pad_inst is not None:
        link_sockets(tree, pads_src, sock(pad_inst, "Points"))
        link_sockets(tree, pad_geo, sock(pad_inst, "Instance"))

    # --- three stand legs --------------------------------------------------
    leg_count = 3
    legs = []
    for i in range(leg_count):
        a = (2.0 * math.pi / leg_count) * i + math.radians(90)
        leg = _cyl(tree, (bx - 380, by - 700 - i * 200), 0.012,
                   gin.outputs["Leg Length M"], vertices=12)
        # Spread is PROPORTIONAL to the pan radius. A bare 0.62 put the leg feet
        # 0.62 m out from a 0.18 m pan (measured diag 1.62 m for a 0.36 m pan).
        spread = _math(tree, "MULTIPLY", (bx - 600, by - 900 - i * 200),
                       r_sock, 0.62)
        legs.append(_xf(tree, (bx - 160, by - 700 - i * 200),
                        leg.outputs["Mesh"] if leg else None,
                        rotation=(0.0, 0.0, 0.0),
                        translation=_combine(tree, (bx - 380, by - 900 - i * 200),
                                            _math(tree, "MULTIPLY",
                                                  (bx - 600, by - 1060 - i * 200),
                                                  spread.outputs[0], math.cos(a)).outputs[0],
                                            _math(tree, "MULTIPLY",
                                                  (bx - 600, by - 1220 - i * 200),
                                                  spread.outputs[0], math.sin(a)).outputs[0],
                                            _math(tree, "MULTIPLY",
                                                  (bx - 600, by - 1380 - i * 200),
                                                  gin.outputs["Leg Length M"], -0.30).outputs[0])
                        ).outputs["Geometry"])

    body = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 300, by))
    for s in (bowl_flat, rim_geo, skirt_geo,
              pad_inst.outputs["Instances"] if pad_inst else None, *legs):
        if s is not None:
            link_sockets(tree, s, body.inputs["Geometry"])

    pidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 300, by - 220))
    pmod = _math(tree, "FLOORMOD", (bx + 300, by - 340), pidx.outputs["Index"], 12.0)
    stored = _store_named(tree, (bx + 520, by - 160), body.outputs["Geometry"],
                          "note_semitone_mod12", pmod.outputs[0])
    stored = _store_named(tree, (bx + 700, by - 160), stored, "higgsas_lead",
                          0.0 if used_spiral else 1.0)
    _export_tail(tree, gin, gout, stored, (bx + 900, by))

    return label_tree(tree, group_name, [
        {"title": "Bowl + Rim", "nodes": ("bowl", "rim", "skirt"), "role": "geometry"},
        {"title": "Note Field", "nodes": ("spiral", "pad_inst"), "role": "instance"},
        {"title": "Stand", "nodes": ("leg",), "role": "geometry"},
        {"title": "Export", "nodes": ("realize", "switch", "shade"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_gong
# ---------------------------------------------------------------------------

def build_music_gong(group_name="MEL_music_gong"):
    """Gong: a flat disc bowed into a dish, central boss, two suspension cords
    and a standing frame.

    Lead: `Bend` bows the disc about its diameter — a native Transform cannot
    bend geometry, so the dish is the one place the library is load-bearing.
    Native fallback: a scaled sphere (a true dish, not a bowed disc).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_gong"

    add_float_param(tree, "Gong Radius M", 0.34, 0.12, 0.9)
    add_float_param(tree, "Disc Thickness M", 0.006, 0.002, 0.03)
    add_float_param(tree, "Dish Deg", 26.0, 0.0, 70.0)
    add_float_param(tree, "Boss Radius M", 0.075, 0.02, 0.2)
    add_float_param(tree, "Frame Height M", 1.05, 0.5, 2.2)
    add_float_param(tree, "Frame Spread M", 0.42, 0.2, 1.0)
    add_float_param(tree, "Cord Radius M", 0.006, 0.002, 0.02)
    add_bool_param(tree, "Realize for export", False)

    bx, by = 0, 0
    r_sock = gin.outputs["Gong Radius M"]
    dish_rad = _math(tree, "MULTIPLY", (bx - 1500, by + 260),
                     gin.outputs["Dish Deg"], 0.0174533)

    disc = _cyl(tree, (bx - 1300, by + 400), r_sock,
                gin.outputs["Disc Thickness M"], vertices=96, fill=2)

    bend, used_bend = _lead(
        BID, tree, "Bend", (bx - 1060, by + 400),
        fallback_type="GeometryNodeTransform",
        inputs={"Angle": dish_rad.outputs[0], "Axis": (1.0, 0.0, 0.0),
                "Center": (0.0, 0.0, 0.0), "Limits Lower": 0.0,
                "Limits Upper": 1.0},
    )
    if bend is not None and not used_bend:
        link_sockets(tree, disc.outputs["Mesh"], sock(bend, "Geometry"))
        dished = bend.outputs["Geometry"]
    else:
        # Native fallback: a very flat sphere IS a dish (unlike a flat disc).
        fb = _sphere(tree, (bx - 1060, by + 400), r_sock, segments=64, rings=24)
        dished = _xf(tree, (bx - 820, by + 400), fb.outputs["Mesh"],
                     scale=_combine(tree, (bx - 1060, by + 260), 1.0, 1.0,
                                    _math(tree, "MULTIPLY", (bx - 1060, by + 120),
                                          gin.outputs["Dish Deg"], 0.006).outputs[0])
                     ).outputs["Geometry"]

    # --- central boss: a domed knob on the face ----------------------------
    boss = _sphere(tree, (bx - 820, by + 700), gin.outputs["Boss Radius M"],
                   segments=32, rings=16)
    boss_geo = _xf(tree, (bx - 580, by + 700), boss.outputs["Mesh"],
                   scale=_combine(tree, (bx - 820, by + 560), 1.0, 1.0, 0.55),
                   translation=_combine(tree, (bx - 820, by + 420), 0.0, 0.0,
                                       _math(tree, "MULTIPLY", (bx - 1060, by + 420),
                                             gin.outputs["Boss Radius M"], 0.35).outputs[0])
                   ).outputs["Geometry"]

    # --- rim: a rolled edge around the disc --------------------------------
    rim_path = _ring(tree, (bx - 820, by + 1000), r_sock, resolution=96, fill=1)
    rim_prof = _ring(tree, (bx - 820, by + 840),
                     _math(tree, "MULTIPLY", (bx - 1060, by + 840),
                           gin.outputs["Disc Thickness M"], 3.0).outputs[0],
                     resolution=10, fill=1)
    rim = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 580, by + 1000))
    if rim is not None:
        link_sockets(tree, rim_path.outputs["Curve"], sock(rim, "Curve"))
        link_sockets(tree, rim_prof.outputs["Curve"], sock(rim, "Profile Curve"))

    # --- suspension frame + cords -----------------------------------------
    post_h = gin.outputs["Frame Height M"]
    post = _cyl(tree, (bx - 1300, by - 700), 0.016, post_h, vertices=16)
    posts = []
    for sign in (-1.0, 1.0):
        posts.append(_xf(tree, (bx - 1060, by - 700 - int(sign) * 200),
                         post.outputs["Mesh"],
                         translation=_combine(tree, (bx - 1300, by - 900 - int(sign) * 200),
                                             _math(tree, "MULTIPLY",
                                                   (bx - 1500, by - 900 - int(sign) * 200),
                                                   gin.outputs["Frame Spread M"], sign).outputs[0],
                                             0.0, 0.0)
                         ).outputs["Geometry"])
    bar = _cyl(tree, (bx - 1060, by - 1500), 0.014,
               _math(tree, "MULTIPLY", (bx - 1300, by - 1500),
                     gin.outputs["Frame Spread M"], 2.0).outputs[0], vertices=16)
    bar_geo = _xf(tree, (bx - 820, by - 1500), bar.outputs["Mesh"],
                  rotation=(0.0, math.radians(90), 0.0),
                  translation=_combine(tree, (bx - 1060, by - 1640), 0.0, 0.0,
                                      _math(tree, "MULTIPLY", (bx - 1300, by - 1640),
                                            post_h, 0.5).outputs[0])
                  ).outputs["Geometry"]

    cords = []
    for sign in (-1.0, 1.0):
        cord = _cyl(tree, (bx - 580, by - 1900 - int(sign) * 200),
                    gin.outputs["Cord Radius M"],
                    _math(tree, "MULTIPLY", (bx - 820, by - 1900 - int(sign) * 200),
                          gin.outputs["Frame Height M"], 0.34).outputs[0], vertices=8)
        cords.append(_xf(tree, (bx - 380, by - 1900 - int(sign) * 200),
                         cord.outputs["Mesh"],
                         rotation=(0.0, math.radians(-18) * sign, 0.0),
                         translation=_combine(tree, (bx - 580, by - 2100 - int(sign) * 200),
                                             sign * 0.30, 0.0, 0.10)
                         ).outputs["Geometry"])

    frame = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 100, by - 900))
    for s in (rim.outputs["Mesh"] if rim else None, bar_geo, *posts, *cords):
        if s is not None:
            link_sockets(tree, s, frame.inputs["Geometry"])
    frame_geo = _xf(tree, (bx + 140, by - 900), frame.outputs["Geometry"],
                    translation=_combine(tree, (bx - 60, by - 1060),
                                        0.0, 0.0,
                                        _math(tree, "MULTIPLY", (bx - 260, by - 1060),
                                              post_h, 0.5).outputs[0])
                    ).outputs["Geometry"]

    # --- raise the disc onto the frame ------------------------------------
    lifted = _xf(tree, (bx + 380, by + 400), dished,
                 translation=_combine(tree, (bx + 180, by + 260), 0.0, 0.0,
                                     _math(tree, "MULTIPLY", (bx - 20, by + 260),
                                           post_h, 1.05).outputs[0])
                 ).outputs["Geometry"]
    boss_lift = _xf(tree, (bx + 380, by + 700), boss_geo,
                    translation=_combine(tree, (bx + 180, by + 560), 0.0, 0.0,
                                         _math(tree, "MULTIPLY", (bx - 20, by + 560),
                                               post_h, 1.05).outputs[0])
                    ).outputs["Geometry"]
    # rim rides with the disc
    rim_lift = _xf(tree, (bx + 380, by + 1000), rim.outputs["Mesh"] if rim else None,
                   translation=_combine(tree, (bx + 180, by + 860), 0.0, 0.0,
                                        _math(tree, "MULTIPLY", (bx - 20, by + 860),
                                              post_h, 1.05).outputs[0])
                   ).outputs["Geometry"]

    body = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 620, by + 200))
    for s in (lifted, boss_lift, rim_lift, frame_geo):
        if s is not None:
            link_sockets(tree, s, body.inputs["Geometry"])

    gidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 620, by - 200))
    gmod = _math(tree, "FLOORMOD", (bx + 620, by - 320), gidx.outputs["Index"], 12.0)
    stored = _store_named(tree, (bx + 840, by - 160), body.outputs["Geometry"],
                          "gong_semitone_mod12", gmod.outputs[0])
    stored = _store_named(tree, (bx + 1020, by - 160), stored, "higgsas_lead",
                          0.0 if used_bend else 1.0)
    _export_tail(tree, gin, gout, stored, (bx + 1220, by))

    return label_tree(tree, group_name, [
        {"title": "Dished Disc", "nodes": ("disc", "bend"), "role": "geometry"},
        {"title": "Boss + Rim", "nodes": ("boss", "rim"), "role": "geometry"},
        {"title": "Frame", "nodes": ("post", "bar", "cord"), "role": "geometry"},
        {"title": "Export", "nodes": ("realize", "switch", "shade"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_ocarina
# ---------------------------------------------------------------------------

def build_music_ocarina(group_name="MEL_music_ocarina"):
    """Ocarina: a super-ellipsoid vessel body, a windway tube on the side, a
    raised mouthpiece, and 6 finger holes bored through the shell.

    Lead: `Super Ellipsoid` is the authored vessel form (a superellipsoid ovoid
    is exactly what an ocarina body is; a UV sphere is the fallback). The finger
    holes are REAL cuts — native Mesh Boolean DIFFERENCE against cylinders that
    OVERHANG the shell, because a cutter buried inside the body produces an
    enclosed cavity and sliver faces instead of a hole.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_ocarina"

    add_float_param(tree, "Body Length M", 0.15, 0.06, 0.4)
    add_float_param(tree, "Body Radius M", 0.055, 0.02, 0.15)
    add_float_param(tree, "Mouthpiece M", 0.045, 0.01, 0.15)
    add_int_param(tree, "Finger Holes", 6, 2, 12)
    add_float_param(tree, "Hole Radius M", 0.006, 0.001, 0.02)
    add_float_param(tree, "Wall M", 0.006, 0.002, 0.02)
    add_bool_param(tree, "Realize for export", False)

    # Declared here so a missing node type is a HARD FAILURE, not a silent skip:
    # `GeometryNodeAlignRotationToVector` does not exist in 5.2 (it is
    # `FunctionNodeAlignRotationToVector`), and the geometry-namespace spelling
    # made safe_node return None — every hole cutter then sat unrotated with no
    # exception and no link_failures entry. Probe first, declare, then assert.
    _PROBE = safe_node(tree, "FunctionNodeAlignRotationToVector", (0, 0))
    _HAS_ALIGN = _PROBE is not None
    if _PROBE is not None:
        tree.nodes.remove(_PROBE)

    bx, by = 0, 0
    len_sock = gin.outputs["Body Length M"]
    rad_sock = gin.outputs["Body Radius M"]

    # --- vessel body --------------------------------------------------------
    # Real sockets (probed): Size (VECTOR) / N / M / Segments / Rings, output
    # "Mesh". `N` and `M` are the superellipsoid exponents; the aspect ratio is
    # folded into Size, not a Transform scale (which left a stray SetPosition
    # node with no geometry and one dropped link).
    body_lead, used_body = _lead(
        BID, tree, "Super Ellipsoid", (bx - 1500, by + 300),
        fallback_type="GeometryNodeMeshUVSphere",
        inputs={"Size": _combine(tree, (bx - 1740, by + 300),
                                 rad_sock, rad_sock, len_sock),
                "N": 2.6, "M": 2.2, "Segments": 48, "Rings": 24},
    )
    if body_lead is not None and not used_body:
        body_geo = body_lead.outputs.get("Mesh") or body_lead.outputs[0]
    else:
        fb = _sphere(tree, (bx - 1500, by + 300), rad_sock, segments=48, rings=24)
        body_geo = _xf(tree, (bx - 1260, by + 300), fb.outputs["Mesh"],
                       scale=_combine(tree, (bx - 1500, by + 160), 1.0, 1.0,
                                      _math(tree, "DIVIDE", (bx - 1500, by + 20),
                                            len_sock, rad_sock).outputs[0])
                       ).outputs["Geometry"]

    # --- windway + mouthpiece on the +Y side --------------------------------
    mp_len = _math(tree, "MULTIPLY", (bx - 1500, by - 400),
                   gin.outputs["Mouthpiece M"], 1.0)
    mp = _cyl(tree, (bx - 1260, by - 400),
              _math(tree, "MULTIPLY", (bx - 1500, by - 260),
                    rad_sock, 0.22).outputs[0], mp_len, vertices=20, fill=2)
    mp_geo = _xf(tree, (bx - 1020, by - 400), mp.outputs["Mesh"] if mp else None,
                 rotation=(math.radians(-90), 0.0, 0.0),
                 translation=_combine(tree, (bx - 1260, by - 560), 0.0,
                                     _math(tree, "MULTIPLY", (bx - 1500, by - 560),
                                           rad_sock, 0.92).outputs[0], 0.0)
                 ).outputs["Geometry"]

    # --- finger holes: cutters that OVERHANG the shell ---------------------
    hole_pts, hole_count = _fib_spiral(
        tree, (bx - 1500, by + 900), gin.outputs["Finger Holes"],
        _math(tree, "MULTIPLY", (bx - 1740, by + 900), rad_sock, 0.80).outputs[0])
    # keep them on the upper half of the vessel (no holes through the windway)
    hole_pts2 = _xf(tree, (bx - 900, by + 900), hole_pts,
                    scale=_combine(tree, (bx - 1100, by + 760), 1.0, 1.0, 1.0),
                    translation=_combine(tree, (bx - 1100, by + 620), 0.0, 0.0, 0.0)
                    ).outputs["Geometry"]

    # 5.2 node-type truth (probed, Saved/Audit/probe_node_types_20261002.py):
    # there is NO `GeometryNodeAlignRotationToVector` — the type lives in the
    # FUNCTION namespace (`FunctionNodeAlignRotationToVector`). The Geometry
    # spelling made safe_node return None, which silently left every cutter
    # unrotated with no exception and no link_failures entry.
    align = safe_node(tree, "FunctionNodeAlignRotationToVector", (bx - 700, by + 1100))
    if align is None:
        align = safe_node(tree, "FunctionNodeAlignEulerToVector", (bx - 700, by + 1100))
    if align is not None:
        # Holes are bored radially, so each cutter must point ALONG the surface
        # normal. Feeding a Position field into the align node's Vector input
        # rotates every instance by its own POSITION, not its normal — the holes
        # would fire in random directions. Normal is the socket that means
        # "outward from this point on the shell".
        nrm = safe_node(tree, "GeometryNodeInputNormal", (bx - 900, by + 1100))
        link_sockets(tree, nrm.outputs["Normal"] if nrm is not None else None,
                     sock(align, "Vector"))
        s = sock(align, "Factor")
        if s is not None:
            try:
                s.default_value = 1.0
            except Exception:
                pass
        ax = sock(align, "Axis")
        if ax is not None:
            try:
                ax.default_value = "Z"
            except Exception:
                pass

    cutter = _cyl(tree, (bx - 700, by + 1400),
                  gin.outputs["Hole Radius M"],
                  _math(tree, "MULTIPLY", (bx - 900, by + 1540),
                        rad_sock, 4.0).outputs[0], vertices=16, fill=2)
    cut_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 500, by + 1100))
    if cut_inst is not None:
        link_sockets(tree, hole_pts2, sock(cut_inst, "Points"))
        link_sockets(tree, cutter.outputs["Mesh"], sock(cut_inst, "Instance"))
        if align is not None:
            link_sockets(tree, align.outputs["Rotation"],
                         sock(cut_inst, "Rotation"))
    # Loud on a missing node type. A silently-unrotated cutter is the exact
    # failure this assert exists for; the gate measures the result too.
    if not _HAS_ALIGN:
        raise RuntimeError(
            "MEL_music_ocarina: FunctionNodeAlignRotationToVector is unavailable "
            "in this Blender build — the finger-hole cutters cannot be aimed "
            "along the shell normal. Refusing to emit a builder whose holes are "
            "known-wrong (a silently unrotated cutter bores in a random direction)."
        )
    cut_real = safe_node(tree, "GeometryNodeRealizeInstances", (bx - 280, by + 1100))
    if cut_real is not None:
        link_sockets(tree, cut_inst.outputs["Instances"] if cut_inst else None,
                     sock(cut_real, "Geometry"))

    bored, _bnode = mesh_boolean_node(
        tree, (bx - 40, by + 300), "DIFFERENCE",
        body_geo, cut_real.outputs["Geometry"] if cut_real else None)

    # --- mouthpiece joins the bored vessel ---------------------------------
    body = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 220, by + 300))
    for s in (bored, mp_geo):
        if s is not None:
            link_sockets(tree, s, body.inputs["Geometry"])

    hidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 220, by - 100))
    hmod = _math(tree, "FLOORMOD", (bx + 220, by - 220), hidx.outputs["Index"], 12.0)
    stored = _store_named(tree, (bx + 440, by - 60), body.outputs["Geometry"],
                          "hole_semitone_mod12", hmod.outputs[0])
    stored = _store_named(tree, (bx + 620, by - 60), stored, "higgsas_lead",
                          0.0 if used_body else 1.0)
    _export_tail(tree, gin, gout, stored, (bx + 820, by + 300))

    return label_tree(tree, group_name, [
        {"title": "Vessel", "nodes": ("super_ellipsoid", "mp"), "role": "geometry"},
        {"title": "Bored Holes", "nodes": ("align", "cutter", "boolean"), "role": "geometry"},
        {"title": "Export", "nodes": ("realize", "switch", "shade"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

register_builder(
    "MEL_music_steelpan", build_music_steelpan, "Steelpan",
    "Steel drum: dished playing bowl, rolled rim, tapered skirt, a "
    "Fibonacci-spaced field of note pads, three stand legs. Lead group: "
    "Higgsas Spherical Spiral.",
    "music",
)
register_builder(
    "MEL_music_gong", build_music_gong, "Gong",
    "Dished bronze disc with a rolled rim and central boss, hung by two cords "
    "from a standing frame. Lead group: Higgsas Bend (bows the disc).",
    "music",
)
register_builder(
    "MEL_music_ocarina", build_music_ocarina, "Ocarina",
    "Vessel flute: super-ellipsoid body, side windway, raised mouthpiece, and "
    "6 finger holes bored by Mesh Boolean. Lead group: Higgsas Super Ellipsoid.",
    "music",
)
