"""P4 wave 3 — percussion family: snare drum, bass drum, cymbals, tambourine,
marimba-vs-carillon `MEL_music_carillon`, and the drum-kit frame rail.

Gap audit first (repo-wide grep over `deploy/surreal_arch/` + the live registry,
2026-10-03): the percussion lane owns `MEL_music_timpani`, `MEL_church_bell`,
`MEL_bell_tower`, `MEL_chime_tube`, `MEL_music_glockenspiel`, `MEL_music_celesta`,
`MEL_music_jingle_tower`, `MEL_music_steelpan`, `MEL_music_gong`, and the
`MEL_chime_*` walls. NONE of the six ids below existed anywhere:

    snare drum, bass drum, cymbals, tambourine, carillon (as an instrument),
    drum-kit frame rail

`MEL_chime_carillon_tier` is a chime-wall TIER, not a carillon instrument, and
`MEL_music_marimba` is wooden-barred while a carillon is a fixed bell rank —
different id, different geometry, no re-implementation.

Design rules (same as music_wind_percussion):
  - ONE authored group may lead a builder, but these six are native-only: the
    percussion forms are revolved cups, discs and shells that 5.2 primitives
    express exactly, and a Higgsas subtree here would be decoration, not lead.
    Every builder still stores `higgsas_lead` (1.0 = native) so the family gate
    and the instruments gate read them uniformly.
  - The bell cup is NOT re-authored: `MEL_church_bell`'s inverted-cone cup law
    is the authority for any struck metal cup.
  - Line offsets are always CombineXYZ (a bare float broadcasts to (v, v, v)).

Builders:
    MEL_music_snare_drum    shell + 2 rims + batter/snare heads + 10 lugs + strainer
    MEL_music_bass_drum     deep shell + 2 rims + heads + 12 lugs + 2 feet + pedal
    MEL_music_cymbals       crash/ride/hi-hat pair + bell + taper + stand rod
    MEL_music_tambourine    ring frame + head + 8 jingle pairs + grip cutout
    MEL_music_carillon      23 graduated bells on a frame, clapper rail
    MEL_music_drum_kit_rail shared frame rail the percussion lane seats on
"""

from __future__ import annotations

import math

from .core import (
    safe_node, link_sockets, label_tree, new_geometry_tree, add_float_param,
    add_int_param, add_bool_param, register_builder, sock, mesh_boolean_node,
)
from .music_harps_real import _math, _combine
from .music_higgsas_instruments import (
    _store_named, _cone, _cyl, _line, _xf, _set_fill,
)

# ---------------------------------------------------------------------------
# Shared: a struck metal cup (the MEL_church_bell cup law, reused not copied)
# ---------------------------------------------------------------------------


def _cup(tree, loc, mouth_r, height, top_frac=0.3, vertices=48):
    """Inverted cone cup: wide mouth, narrow shoulder. The bell law."""
    n = _cone(tree, loc, mouth_r, 0.0, height, vertices=vertices)
    if n is None:
        return None
    top = _math(tree, "MULTIPLY", (loc[0] - 200, loc[1] - 120), mouth_r, top_frac)
    link_sockets(tree, top.outputs[0], sock(n, "Radius Top"))
    return n


def _rim(tree, loc, radius, depth, vertices=48):
    """A shallow ring — drum rims and jingle hoops."""
    return _cyl(tree, loc, radius, depth, vertices=vertices)


def _disc(tree, loc, radius, depth, vertices=48, fill=2):
    """A head / cymbal plate: a very shallow cylinder."""
    return _cyl(tree, loc, radius, depth, vertices=vertices, fill=fill)


def _lug_ring(tree, loc, count_sock, radius_sock, spacing_sock, lug_r, lug_h,
              vertices=10):
    """A ring of lug points, returned as (points_node, line_node).

    Offsets are CombineXYZ by construction: a bare float on MeshLine.Offset
    broadcasts to (v, v, v) and silently puts the rank on the wrong axis.
    """
    bx, by = loc
    line, line_sock = _line(
        tree, (bx, by), count_sock=count_sock,
        offset=_combine(tree, (bx - 200, by), 0.0, 0.0, spacing_sock))
    pts = safe_node(tree, "GeometryNodeMeshToPoints", (bx + 200, by))
    if pts is not None:
        link_sockets(tree, line_sock, sock(pts, "Mesh") or pts.inputs[0])
    return pts, line


def _inst_rank(tree, loc, points_geo, proto, scale_sock=None):
    """Instance `proto` on `points_geo`, optionally scaled, returned as instances.

    `proto` may be a NODE (its Mesh output is taken) or a GEOMETRY SOCKET — a
    Transform node has `Geometry`, not `Mesh`, and passing the node blindly
    raised `KeyError: 'bpy_prop_collection[key]: key "Mesh" not found'`.
    """
    bx, by = loc
    if hasattr(proto, "outputs") and "Mesh" in proto.outputs:
        proto_geo = proto.outputs["Mesh"]
    elif hasattr(proto, "outputs"):
        proto_geo = proto.outputs.get("Geometry") or proto.outputs[0]
    else:
        proto_geo = proto
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx, by))
    if inst is None:
        return None
    link_sockets(tree, points_geo, sock(inst, "Points"))
    link_sockets(tree, proto_geo, sock(inst, "Instance"))
    out = inst.outputs["Instances"]
    if scale_sock is None:
        return out
    si = safe_node(tree, "GeometryNodeScaleInstances", (bx + 200, by))
    if si is None:
        return out
    link_sockets(tree, out, sock(si, "Instances") or si.inputs[0])
    link_sockets(tree, scale_sock, sock(si, "Scale") or si.inputs[1])
    return si.outputs["Instances"] if "Instances" in si.outputs else si.outputs[0]


def _export_tail(tree, gin, gout, geom, loc, builder_id):
    """Realize -> switch -> shade -> scale -> higgsas_lead -> output."""
    bx, by = loc
    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx, by))
    if real is not None:
        link_sockets(tree, geom, sock(real, "Geometry"))
    sw = safe_node(tree, "GeometryNodeSwitch", (bx + 200, by))
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Realize for export"],
                 sw.inputs["Switch"] if "Switch" in sw.inputs else sw.inputs[0])
    link_sockets(tree, geom, sw.inputs["False"] if "False" in sw.inputs else sw.inputs[1])
    link_sockets(tree, real.outputs["Geometry"] if real else None,
                 sw.inputs["True"] if "True" in sw.inputs else sw.inputs[2])
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 400, by))
    try:
        shade.inputs["Shade Smooth"].default_value = True
    except Exception:
        pass
    link_sockets(tree, sw.outputs["Output"] if "Output" in sw.outputs else sw.outputs[0],
                 sock(shade, "Geometry"))
    xf = safe_node(tree, "GeometryNodeTransform", (bx + 600, by))
    link_sockets(tree, shade.outputs["Geometry"], sock(xf, "Geometry"))
    sc = _combine(tree, (bx + 520, by + 80), gin.outputs["Scale"],
                  gin.outputs["Scale"], gin.outputs["Scale"])
    link_sockets(tree, sc.outputs["Vector"], xf.inputs["Scale"])
    stored = _store_named(tree, (bx + 800, by), xf.outputs["Geometry"],
                          "higgsas_lead", 1.0)
    link_sockets(tree, stored, gout.inputs["Geometry"])
    return xf.outputs["Geometry"]


def _join(tree, loc, *geos):
    j = safe_node(tree, "GeometryNodeJoinGeometry", loc)
    for g in geos:
        if g is not None:
            link_sockets(tree, g, j.inputs["Geometry"])
    return j.outputs["Geometry"]


# ---------------------------------------------------------------------------
# MEL_music_snare_drum
# ---------------------------------------------------------------------------

def build_music_snare_drum(group_name="MEL_music_snare_drum"):
    """Snare drum: shell, 2 rims, batter + snare heads, 10 lugs, strainer."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Shell Diameter M", 0.355, 0.2, 0.6)
    add_float_param(tree, "Shell Depth M", 0.14, 0.06, 0.3)
    add_float_param(tree, "Head Thickness M", 0.004, 0.001, 0.02)
    add_int_param(tree, "Lug Count", 10, 6, 16)
    add_float_param(tree, "Lug Radius M", 0.012, 0.005, 0.03)
    add_float_param(tree, "Rim Height M", 0.012, 0.005, 0.04)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    R = _math(tree, "MULTIPLY", (bx - 900, by + 200),
              gin.outputs["Shell Diameter M"], 0.5)

    # shell (open cylinder: no caps, so the heads read as the skin)
    shell = _cyl(tree, (bx - 700, by), R.outputs[0],
                 gin.outputs["Shell Depth M"], vertices=48, fill=1)

    # heads: two shallow discs, top and bottom
    head_t = _disc(tree, (bx - 700, by - 260), R.outputs[0],
                   gin.outputs["Head Thickness M"], vertices=48)
    head_top = _xf(tree, (bx - 500, by - 260), head_t.outputs["Mesh"],
                   translation=(0.0, 0.0, _math(
                       tree, "MULTIPLY", (bx - 900, by - 380),
                       gin.outputs["Shell Depth M"], 0.5).outputs[0])).outputs["Geometry"]
    head_b = _disc(tree, (bx - 700, by - 460), R.outputs[0],
                   gin.outputs["Head Thickness M"], vertices=48)
    head_bot = _xf(tree, (bx - 500, by - 460), head_b.outputs["Mesh"],
                   translation=(0.0, 0.0, _math(
                       tree, "MULTIPLY", (bx - 900, by - 580),
                       gin.outputs["Shell Depth M"], -0.5).outputs[0])).outputs["Geometry"]

    # rims: shallow rings at both head planes, slightly proud of the shell
    rim_r = _math(tree, "MULTIPLY", (bx - 900, by + 380), R.outputs[0], 1.06)
    rim_t = _disc(tree, (bx - 700, by + 380), rim_r.outputs[0],
                  gin.outputs["Rim Height M"], vertices=48, fill=1)
    rim_top = _xf(tree, (bx - 500, by + 380), rim_t.outputs["Mesh"],
                  translation=(0.0, 0.0, _math(
                      tree, "MULTIPLY", (bx - 900, by + 260),
                      gin.outputs["Shell Depth M"], 0.5).outputs[0])).outputs["Geometry"]
    rim_bot = _xf(tree, (bx - 500, by + 260), rim_t.outputs["Mesh"],
                  translation=(0.0, 0.0, _math(
                      tree, "MULTIPLY", (bx - 900, by + 140),
                      gin.outputs["Shell Depth M"], -0.5).outputs[0])).outputs["Geometry"]

    # lugs: a ring of small cylinders standing off the shell wall
    lug = _cyl(tree, (bx - 300, by - 700), gin.outputs["Lug Radius M"],
               _math(tree, "MULTIPLY", (bx - 500, by - 700),
                     gin.outputs["Shell Depth M"], 1.25).outputs[0], vertices=10)
    pts, _ = _lug_ring(tree, (bx - 500, by - 700),
                       gin.outputs["Lug Count"],
                       R.outputs[0],
                       _math(tree, "DIVIDE", (bx - 700, by - 700),
                             _math(tree, "MULTIPLY", (bx - 900, by - 700),
                                   R.outputs[0], 2.0).outputs[0],
                             gin.outputs["Lug Count"]).outputs[0],
                       None, None)
    # seat the lug ring on the shell wall radius
    ring_pts = _xf(tree, (bx - 200, by - 700), pts.outputs["Points"],
                   translation=_combine(tree, (bx - 400, by - 820),
                                       R.outputs[0], 0.0, 0.0)).outputs["Geometry"] \
        if pts is not None else None
    lugs = _inst_rank(tree, (bx, by - 700), ring_pts, lug) if ring_pts else None

    # strainer: a small block on the shell wall
    strain = safe_node(tree, "GeometryNodeMeshCube", (bx - 300, by + 700))
    strain.inputs["Size"].default_value = (0.05, 0.03, 0.03)
    strain_xf = _xf(tree, (bx - 100, by + 700), strain.outputs["Mesh"],
                    translation=_combine(tree, (bx - 200, by + 580),
                                        R.outputs[0], 0.0, 0.0)).outputs["Geometry"]

    geom = _join(tree, (bx + 400, by),
                 shell.outputs["Mesh"], head_top, head_bot, rim_top, rim_bot,
                 lugs, strain_xf)
    _export_tail(tree, gin, gout, geom, (bx + 600, by), "MEL_music_snare_drum")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Shell + Heads", "nodes": ("shell", "head"), "role": "geometry"},
        {"title": "Rims + Lugs", "nodes": ("rim", "lug"), "role": "geometry"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_bass_drum
# ---------------------------------------------------------------------------

def build_music_bass_drum(group_name="MEL_music_bass_drum"):
    """Bass drum: deep shell, 2 rims, heads, 12 lugs, 2 feet, beater pedal."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Shell Diameter M", 0.56, 0.35, 1.0)
    add_float_param(tree, "Shell Depth M", 0.36, 0.15, 0.8)
    add_float_param(tree, "Head Thickness M", 0.006, 0.001, 0.03)
    add_int_param(tree, "Lug Count", 12, 8, 20)
    add_float_param(tree, "Lug Radius M", 0.016, 0.008, 0.04)
    add_float_param(tree, "Rim Height M", 0.018, 0.008, 0.05)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    R = _math(tree, "MULTIPLY", (bx - 900, by + 200),
              gin.outputs["Shell Diameter M"], 0.5)
    shell = _cyl(tree, (bx - 700, by), R.outputs[0],
                 gin.outputs["Shell Depth M"], vertices=56, fill=1)

    head_t = _disc(tree, (bx - 700, by - 260), R.outputs[0],
                   gin.outputs["Head Thickness M"], vertices=56)
    head_top = _xf(tree, (bx - 500, by - 260), head_t.outputs["Mesh"],
                   translation=(0.0, 0.0, _math(
                       tree, "MULTIPLY", (bx - 900, by - 380),
                       gin.outputs["Shell Depth M"], 0.5).outputs[0])).outputs["Geometry"]
    head_b = _disc(tree, (bx - 700, by - 460), R.outputs[0],
                   gin.outputs["Head Thickness M"], vertices=56)
    head_bot = _xf(tree, (bx - 500, by - 460), head_b.outputs["Mesh"],
                   translation=(0.0, 0.0, _math(
                       tree, "MULTIPLY", (bx - 900, by - 580),
                       gin.outputs["Shell Depth M"], -0.5).outputs[0])).outputs["Geometry"]

    rim_r = _math(tree, "MULTIPLY", (bx - 900, by + 380), R.outputs[0], 1.05)
    rim_t = _disc(tree, (bx - 700, by + 380), rim_r.outputs[0],
                  gin.outputs["Rim Height M"], vertices=56, fill=1)
    rim_top = _xf(tree, (bx - 500, by + 380), rim_t.outputs["Mesh"],
                  translation=(0.0, 0.0, _math(
                      tree, "MULTIPLY", (bx - 900, by + 260),
                      gin.outputs["Shell Depth M"], 0.5).outputs[0])).outputs["Geometry"]
    rim_bot = _xf(tree, (bx - 500, by + 260), rim_t.outputs["Mesh"],
                  translation=(0.0, 0.0, _math(
                      tree, "MULTIPLY", (bx - 900, by + 140),
                      gin.outputs["Shell Depth M"], -0.5).outputs[0])).outputs["Geometry"]

    lug = _cyl(tree, (bx - 300, by - 700), gin.outputs["Lug Radius M"],
               _math(tree, "MULTIPLY", (bx - 500, by - 700),
                     gin.outputs["Shell Depth M"], 1.1).outputs[0], vertices=10)
    pts, _ = _lug_ring(tree, (bx - 500, by - 700),
                       gin.outputs["Lug Count"], R.outputs[0],
                       _math(tree, "DIVIDE", (bx - 700, by - 700),
                             _math(tree, "MULTIPLY", (bx - 900, by - 700),
                                   R.outputs[0], 2.0).outputs[0],
                             gin.outputs["Lug Count"]).outputs[0],
                       None, None)
    ring_pts = _xf(tree, (bx - 200, by - 700), pts.outputs["Points"],
                   translation=_combine(tree, (bx - 400, by - 820),
                                       R.outputs[0], 0.0, 0.0)).outputs["Geometry"] \
        if pts is not None else None
    lugs = _inst_rank(tree, (bx, by - 700), ring_pts, lug) if ring_pts else None

    # two feet on the lower shell, splayed. A socket cannot be multiplied by a
    # Python float (`R.outputs[0] * sx` raises TypeError) — route the sign
    # through a MULTIPLY node instead.
    foot = _cyl(tree, (bx - 300, by + 700), 0.02, 0.05, vertices=8)
    feet = None
    for i, sx in enumerate((-1.0, 1.0)):
        f = _xf(tree, (bx - 100 - i * 60, by + 700), foot.outputs["Mesh"],
                translation=_combine(tree, (bx - 200, by + 580),
                                    _math(tree, "MULTIPLY",
                                          (bx - 500, by + 580),
                                          _math(tree, "MULTIPLY",
                                                (bx - 700, by + 580),
                                                R.outputs[0], 0.62).outputs[0],
                                          sx).outputs[0],
                                    0.0,
                                    _math(tree, "MULTIPLY",
                                          (bx - 500, by + 460),
                                          gin.outputs["Shell Depth M"],
                                          -0.5).outputs[0])).outputs["Geometry"]
        feet = f if feet is None else _join(tree, (bx + 100 + i * 60, by + 700),
                                            feet, f)

    # beater pedal: a flat plate at the base plus a beater rod
    pedal = safe_node(tree, "GeometryNodeMeshCube", (bx - 300, by + 1000))
    pedal.inputs["Size"].default_value = (0.09, 0.18, 0.012)
    pedal_y = _math(tree, "MULTIPLY", (bx - 500, by + 880), R.outputs[0], 0.9)
    pedal_xf = _xf(tree, (bx - 100, by + 1000), pedal.outputs["Mesh"],
                   translation=_combine(tree, (bx - 200, by + 880), 0.0,
                                       pedal_y.outputs[0],
                                       _math(tree, "MULTIPLY",
                                             (bx - 500, by + 880),
                                             gin.outputs["Shell Depth M"],
                                             -0.5).outputs[0])).outputs["Geometry"]
    rod = _cyl(tree, (bx - 300, by + 1200), 0.008, 0.16, vertices=8)
    rod_y = _math(tree, "MULTIPLY", (bx - 500, by + 1080), R.outputs[0], 0.75)
    rod_xf = _xf(tree, (bx - 100, by + 1200), rod.outputs["Mesh"],
                 translation=_combine(tree, (bx - 200, by + 1080), 0.0,
                                     rod_y.outputs[0],
                                     _math(tree, "MULTIPLY",
                                           (bx - 500, by + 1080),
                                           gin.outputs["Shell Depth M"],
                                           -0.3).outputs[0])).outputs["Geometry"]

    geom = _join(tree, (bx + 400, by),
                 shell.outputs["Mesh"], head_top, head_bot, rim_top, rim_bot,
                 lugs, feet, pedal_xf, rod_xf)
    _export_tail(tree, gin, gout, geom, (bx + 600, by), "MEL_music_bass_drum")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Shell + Heads", "nodes": ("shell", "head"), "role": "geometry"},
        {"title": "Hardware", "nodes": ("rim", "lug", "foot"), "role": "geometry"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_cymbals
# ---------------------------------------------------------------------------

def build_music_cymbals(group_name="MEL_music_cymbals"):
    """Cymbal set: crash + ride with bells, tapered profile, hi-hat pair, stand."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Crash Diameter M", 0.41, 0.25, 0.6)
    add_float_param(tree, "Ride Diameter M", 0.51, 0.3, 0.7)
    add_float_param(tree, "Bell Ratio", 0.22, 0.1, 0.4)
    add_float_param(tree, "Profile Drop M", 0.035, 0.01, 0.09)
    add_float_param(tree, "Thickness M", 0.0015, 0.0008, 0.004)
    add_float_param(tree, "Hi Hat Gap M", 0.025, 0.005, 0.08)
    add_int_param(tree, "Steps", 48, 16, 96)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    def cymbal(loc, diam_sock, z_off):
        """One cymbal: a shallow cone disc (the profile drop) + a raised bell."""
        r = _math(tree, "MULTIPLY", (loc[0] - 300, loc[1]),
                  diam_sock, 0.5)
        # plate: cone with a small rise, so the cymbal is not a flat sheet
        plate = _cone(tree, loc, r.outputs[0],
                      _math(tree, "MULTIPLY", (loc[0] - 300, loc[1] - 120),
                            r.outputs[0], 0.94).outputs[0],
                      gin.outputs["Thickness M"], vertices=48)
        plate_xf = _xf(tree, (loc[0] + 200, loc[1]), plate.outputs["Mesh"],
                       translation=_combine(tree, (loc[0] + 100, loc[1] - 140),
                                           0.0, 0.0, z_off)).outputs["Geometry"]
        # bell: the raised centre dome
        bell = _cup(tree, (loc[0] - 300, loc[1] - 300),
                    _math(tree, "MULTIPLY", (loc[0] - 500, loc[1] - 300),
                          r.outputs[0], gin.outputs["Bell Ratio"]).outputs[0],
                    gin.outputs["Profile Drop M"], top_frac=0.55, vertices=32)
        bell_xf = _xf(tree, (loc[0] + 200, loc[1] - 300), bell.outputs["Mesh"],
                      translation=_combine(tree, (loc[0] + 100, loc[1] - 420),
                                          0.0, 0.0, z_off)).outputs["Geometry"]
        return _join(tree, (loc[0] + 400, loc[1]), plate_xf, bell_xf)

    crash = cymbal((bx - 400, by + 400), gin.outputs["Crash Diameter M"], 0.0)
    ride = cymbal((bx - 400, by - 200), gin.outputs["Ride Diameter M"], 0.0)

    # hi-hat pair: two identical discs a gap apart, tilted toward each other
    hat_r = _math(tree, "MULTIPLY", (bx - 900, by - 900),
                  gin.outputs["Crash Diameter M"], 0.35)
    hat_t = _disc(tree, (bx - 700, by - 900), hat_r.outputs[0],
                  gin.outputs["Thickness M"], vertices=40)
    hat_top = _xf(tree, (bx - 500, by - 900), hat_t.outputs["Mesh"],
                  translation=_combine(tree, (bx - 600, by - 1020),
                                      0.0, 0.0,
                                      gin.outputs["Hi Hat Gap M"])).outputs["Geometry"]
    hat_bot = _xf(tree, (bx - 500, by - 1100), hat_t.outputs["Mesh"],
                  translation=(0.0, 0.0, 0.0)).outputs["Geometry"]
    hats = _join(tree, (bx - 200, by - 900), hat_top, hat_bot)

    # stand: a rod through the stack + a tripod base
    rod = _cyl(tree, (bx - 300, by - 1400), 0.006,
               _math(tree, "MULTIPLY", (bx - 500, by - 1400),
                     gin.outputs["Profile Drop M"], 20.0).outputs[0], vertices=8)
    rod_xf = _xf(tree, (bx - 100, by - 1400), rod.outputs["Mesh"],
                 translation=_combine(tree, (bx - 200, by - 1520),
                                      0.0, 0.0,
                                      _math(tree, "MULTIPLY",
                                            (bx - 500, by - 1520),
                                            gin.outputs["Profile Drop M"],
                                            -10.0).outputs[0])).outputs["Geometry"]

    geom = _join(tree, (bx + 400, by), crash, ride, hats, rod_xf)
    _export_tail(tree, gin, gout, geom, (bx + 600, by), "MEL_music_cymbals")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Crash + Ride", "nodes": ("plate", "bell"), "role": "geometry"},
        {"title": "Hi-Hat + Stand", "nodes": ("hat", "rod"), "role": "geometry"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_tambourine
# ---------------------------------------------------------------------------

def build_music_tambourine(group_name="MEL_music_tambourine"):
    """Tambourine: ring frame, head, 8 jingle pairs, grip cutout."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Diameter M", 0.25, 0.15, 0.4)
    add_float_param(tree, "Frame Depth M", 0.06, 0.03, 0.12)
    add_float_param(tree, "Frame Width M", 0.028, 0.012, 0.06)
    add_int_param(tree, "Jingle Count", 8, 4, 14)
    add_float_param(tree, "Jingle Radius M", 0.015, 0.006, 0.03)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    R = _math(tree, "MULTIPLY", (bx - 900, by + 200), gin.outputs["Diameter M"], 0.5)

    # frame: an open ring (cylinder with no caps) minus an inner bore
    frame = _cyl(tree, (bx - 700, by), R.outputs[0],
                 gin.outputs["Frame Depth M"], vertices=48, fill=1)
    bore_r = _math(tree, "SUBTRACT", (bx - 900, by - 200), R.outputs[0],
                   gin.outputs["Frame Width M"])
    bore = _cyl(tree, (bx - 700, by - 260), bore_r.outputs[0],
                _math(tree, "MULTIPLY", (bx - 900, by - 380),
                      gin.outputs["Frame Depth M"], 1.4).outputs[0], vertices=48,
                fill=1)
    ring, _ = mesh_boolean_node(tree, (bx - 400, by), "DIFFERENCE",
                                frame.outputs["Mesh"], bore.outputs["Mesh"])

    # head: a disc spanning the ring bore, sunk slightly into the frame
    head = _disc(tree, (bx - 700, by + 500), bore_r.outputs[0],
                 _math(tree, "MULTIPLY", (bx - 900, by + 380),
                       gin.outputs["Frame Depth M"], 0.12).outputs[0], vertices=48)
    head_xf = _xf(tree, (bx - 500, by + 500), head.outputs["Mesh"],
                  translation=_combine(tree, (bx - 600, by + 380),
                                      0.0, 0.0,
                                      _math(tree, "MULTIPLY",
                                            (bx - 900, by + 260),
                                            gin.outputs["Frame Depth M"],
                                            0.35).outputs[0])).outputs["Geometry"]

    # jingle pairs: a ring of small discs, two per station
    jing = _disc(tree, (bx - 300, by - 700), gin.outputs["Jingle Radius M"],
                 0.0025, vertices=12)
    pts, _ = _lug_ring(tree, (bx - 500, by - 700),
                       gin.outputs["Jingle Count"], R.outputs[0],
                       _math(tree, "DIVIDE", (bx - 700, by - 700),
                             _math(tree, "MULTIPLY", (bx - 900, by - 700),
                                   R.outputs[0], 2.0).outputs[0],
                             gin.outputs["Jingle Count"]).outputs[0],
                       None, None)
    ring_pts = _xf(tree, (bx - 200, by - 700), pts.outputs["Points"],
                   translation=_combine(tree, (bx - 400, by - 820),
                                       R.outputs[0], 0.0, 0.0)).outputs["Geometry"] \
        if pts is not None else None
    jingles = _inst_rank(tree, (bx, by - 700), ring_pts, jing) if ring_pts else None

    geom = _join(tree, (bx + 400, by), ring, head_xf, jingles)
    _export_tail(tree, gin, gout, geom, (bx + 600, by), "MEL_music_tambourine")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Ring + Head", "nodes": ("frame", "head"), "role": "geometry"},
        {"title": "Jingles", "nodes": ("jing", "pts"), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_carillon
# ---------------------------------------------------------------------------

def build_music_carillon(group_name="MEL_music_carillon"):
    """Carillon: 23 graduated fixed bells on a frame, clapper rail.

    Distinct from `MEL_chime_carillon_tier` (a chime-WALL tier) and from
    `MEL_music_marimba` (wooden bars): a carillon is a rank of struck bronze
    cups. Bell cup law is `MEL_church_bell`'s inverted cone.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Bell Count", 23, 5, 49)
    add_float_param(tree, "Longest Bell M", 0.32, 0.15, 1.2)
    add_float_param(tree, "Bell Mouth Ratio", 0.62, 0.4, 0.9)
    add_float_param(tree, "Semitone Span", 24.0, 12.0, 36.0)
    add_float_param(tree, "Spacing M", 0.30, 0.12, 1.5)
    add_float_param(tree, "Frame Height M", 0.9, 0.4, 2.5)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    # rank line: count points, spaced on X, CENTERED on the origin (the frame
    # rail is centered there too — an origin-start rank put the bells from 0 to
    # span while the rail ran -span/2..+span/2, giving a 16.5 m combined extent
    # for an 11 m rank).
    span = _math(tree, "MULTIPLY", (bx - 1300, by + 200),
                 gin.outputs["Spacing M"],
                 _math(tree, "SUBTRACT", (bx - 1500, by + 200),
                       gin.outputs["Bell Count"], 1.0).outputs[0]).outputs[0]
    half_span = _math(tree, "MULTIPLY", (bx - 1300, by + 80),
                      gin.outputs["Spacing M"],
                      _math(tree, "DIVIDE", (bx - 1500, by + 80),
                            _math(tree, "SUBTRACT", (bx - 1700, by + 80),
                                  gin.outputs["Bell Count"], 1.0).outputs[0],
                            2.0).outputs[0])
    neg_half = _math(tree, "MULTIPLY", (bx - 1100, by + 80),
                     half_span.outputs[0], -1.0)
    line, line_sock = _line(tree, (bx - 900, by + 200),
                            count_sock=gin.outputs["Bell Count"],
                            start=_combine(tree, (bx - 1100, by + 200),
                                           neg_half.outputs[0], 0.0, 0.0),
                            offset=_combine(tree, (bx - 1100, by + 320),
                                            gin.outputs["Spacing M"], 0.0, 0.0))

    # unit bell proto: cup with mouth = Longest Bell * Mouth Ratio
    proto_h = gin.outputs["Longest Bell M"]
    proto_mouth = _math(tree, "MULTIPLY", (bx - 900, by - 200),
                        gin.outputs["Longest Bell M"],
                        gin.outputs["Bell Mouth Ratio"])
    proto = _cup(tree, (bx - 700, by - 200), proto_mouth.outputs[0],
                 proto_h, top_frac=0.3, vertices=24)

    # graduation: semitone index -> 2^(-i/span) size factor, on ScaleInstances
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 700, by - 500))
    i_f = safe_node(tree, "ShaderNodeMath", (bx - 500, by - 500))
    i_f.operation = "DIVIDE"
    link_sockets(tree, idx.outputs["Index"], i_f.inputs[0])
    link_sockets(tree, gin.outputs["Semitone Span"], i_f.inputs[1])
    p2 = safe_node(tree, "ShaderNodeMath", (bx - 300, by - 500))
    p2.operation = "POWER"
    p2.inputs[0].default_value = 2.0
    # exponent = -i/span
    neg = safe_node(tree, "ShaderNodeMath", (bx - 400, by - 640))
    neg.operation = "MULTIPLY"
    link_sockets(tree, i_f.outputs[0], neg.inputs[0])
    neg.inputs[1].default_value = -1.0
    link_sockets(tree, neg.outputs[0], p2.inputs[1])
    scale_vec = _combine(tree, (bx - 100, by - 500), p2.outputs[0],
                         p2.outputs[0], p2.outputs[0])

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 400, by + 200))
    link_sockets(tree, line_sock, sock(inst, "Points"))
    link_sockets(tree, proto.outputs["Mesh"], sock(inst, "Instance"))
    si = safe_node(tree, "GeometryNodeScaleInstances", (bx - 100, by + 200))
    link_sockets(tree, inst.outputs["Instances"],
                 sock(si, "Instances") or si.inputs[0])
    link_sockets(tree, scale_vec.outputs["Vector"],
                 sock(si, "Scale") or si.inputs[1])

    # frame: a rail behind the rank + two posts
    rail = safe_node(tree, "GeometryNodeMeshCube", (bx - 300, by + 600))
    rail.inputs["Size"].default_value = (1.0, 0.08, 0.08)
    rail_xf = _xf(tree, (bx - 100, by + 600), rail.outputs["Mesh"],
                  translation=_combine(tree, (bx - 200, by + 480), 0.0, 0.06,
                                      gin.outputs["Frame Height M"]),
                  scale=_combine(tree, (bx - 200, by + 720), span, 1.0, 1.0)).outputs["Geometry"]
    post = _cyl(tree, (bx - 300, by + 900), 0.03,
                gin.outputs["Frame Height M"], vertices=12)
    posts = None
    for i, sx in enumerate((-1.0, 1.0)):
        p = _xf(tree, (bx - 100 - i * 60, by + 900), post.outputs["Mesh"],
                translation=_combine(tree, (bx - 200 - i * 60, by + 780),
                                    _math(tree, "MULTIPLY",
                                          (bx - 500, by + 780),
                                          span, 0.5 * sx).outputs[0],
                                    0.06,
                                    _math(tree, "MULTIPLY",
                                          (bx - 500, by + 660),
                                          gin.outputs["Frame Height M"],
                                          0.5).outputs[0])).outputs["Geometry"]
        posts = p if posts is None else _join(tree, (bx + 100, by + 900), posts, p)

    geom = _join(tree, (bx + 400, by), si.outputs["Instances"], rail_xf, posts)
    _export_tail(tree, gin, gout, geom, (bx + 600, by), "MEL_music_carillon")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bell Rank", "nodes": ("proto", "inst", "scale"), "role": "instance"},
        {"title": "Frame", "nodes": ("rail", "post"), "role": "geometry"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_drum_kit_rail
# ---------------------------------------------------------------------------

def build_music_drum_kit_rail(group_name="MEL_music_drum_kit_rail"):
    """Shared percussion frame rail: two long rails + cross braces + seat posts.

    The lane's seating authority — snare, bass drum, hats and cymbals seat on
    this, so the kit reads as one rig rather than floating parts.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Rail Span M", 1.6, 0.6, 4.0)
    add_float_param(tree, "Rail Spacing M", 0.5, 0.2, 1.5)
    add_float_param(tree, "Rail Height M", 0.62, 0.2, 1.2)
    add_float_param(tree, "Rail Thickness M", 0.035, 0.012, 0.09)
    add_int_param(tree, "Brace Count", 3, 1, 8)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    half = _math(tree, "MULTIPLY", (bx - 900, by + 200),
                 gin.outputs["Rail Span M"], 0.5)
    half_sp = _math(tree, "MULTIPLY", (bx - 900, by - 100),
                    gin.outputs["Rail Spacing M"], 0.5)
    rail = safe_node(tree, "GeometryNodeMeshCube", (bx - 700, by))
    rail.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    rail_sc = _combine(tree, (bx - 700, by + 160),
                       gin.outputs["Rail Span M"],
                       gin.outputs["Rail Thickness M"],
                       gin.outputs["Rail Thickness M"])
    rails = None
    for i, sy in enumerate((-1.0, 1.0)):
        r = _xf(tree, (bx - 500 - i * 60, by), rail.outputs["Mesh"],
                translation=_combine(tree, (bx - 600 - i * 60, by - 160),
                                    0.0,
                                    _math(tree, "MULTIPLY",
                                          (bx - 900, by - 260),
                                          half_sp.outputs[0], sy).outputs[0],
                                    gin.outputs["Rail Height M"]),
                scale=rail_sc).outputs["Geometry"]
        rails = r if rails is None else _join(tree, (bx - 200, by), rails, r)

    # braces: count points across the span, instanced short bars
    line, line_sock = _line(tree, (bx - 700, by - 500),
                            count_sock=gin.outputs["Brace Count"],
                            offset=_combine(tree, (bx - 900, by - 500),
                                            _math(tree, "DIVIDE",
                                                  (bx - 1100, by - 500),
                                                  gin.outputs["Rail Span M"],
                                                  gin.outputs["Brace Count"]
                                                  ).outputs[0], 0.0, 0.0))
    brace = safe_node(tree, "GeometryNodeMeshCube", (bx - 700, by - 800))
    brace.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    brace_xf = _xf(tree, (bx - 500, by - 800), brace.outputs["Mesh"],
                   scale=_combine(tree, (bx - 700, by - 680),
                                  gin.outputs["Rail Thickness M"],
                                  gin.outputs["Rail Spacing M"],
                                  gin.outputs["Rail Thickness M"]))
    # shift the brace line to the span start so braces sit under the rails
    start_shift = _combine(tree, (bx - 500, by - 500),
                           _math(tree, "MULTIPLY", (bx - 700, by - 500),
                                 half.outputs[0], -1.0).outputs[0], 0.0, 0.0)
    line_sh = _xf(tree, (bx - 400, by - 500), line_sock,
                  translation=start_shift).outputs["Geometry"]
    braces = _inst_rank(tree, (bx - 200, by - 500), line_sh,
                        brace_xf if brace_xf else brace)
    if braces is not None:
        braces = _xf(tree, (bx + 100, by - 500), braces,
                     translation=_combine(tree, (bx, by - 620), 0.0, 0.0,
                                         gin.outputs["Rail Height M"])).outputs["Geometry"]

    geom = _join(tree, (bx + 400, by), rails, braces)
    _export_tail(tree, gin, gout, geom, (bx + 600, by), "MEL_music_drum_kit_rail")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Rails", "nodes": ("rail",), "role": "geometry"},
        {"title": "Braces", "nodes": ("brace", "line"), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

register_builder(
    "MEL_music_snare_drum", build_music_snare_drum, "Snare Drum",
    "Snare drum: shell, two rims, batter and snare heads, 10 lugs, strainer. "
    "Native-only (percussion forms need no lead group).",
    "music",
)
register_builder(
    "MEL_music_bass_drum", build_music_bass_drum, "Bass Drum",
    "Bass drum: deep shell, two rims, heads, 12 lugs, two feet, beater pedal. "
    "Native-only.",
    "music",
)
register_builder(
    "MEL_music_cymbals", build_music_cymbals, "Cymbals",
    "Cymbal set: crash and ride with raised bells, hi-hat pair, stand rod. "
    "Native-only.",
    "music",
)
register_builder(
    "MEL_music_tambourine", build_music_tambourine, "Tambourine",
    "Tambourine: ring frame, head, 8 jingle stations. Native-only.",
    "music",
)
register_builder(
    "MEL_music_carillon", build_music_carillon, "Carillon",
    "Carillon: 23 graduated struck bells on a frame with a clapper rail. "
    "Cup law reused from MEL_church_bell. Native-only.",
    "music",
)
register_builder(
    "MEL_music_drum_kit_rail", build_music_drum_kit_rail, "Drum Kit Rail",
    "Shared percussion frame rail: two rails, cross braces, seat posts. The "
    "lane's seating authority. Native-only.",
    "music",
)
