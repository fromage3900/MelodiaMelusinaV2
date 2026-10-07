"""P4 instrument-gap builders: flute, clarinet, recorder, marimba, vibraphone, melodica.

Gap audit first (repo-wide grep over `deploy/surreal_arch/` + the live registry,
2026-10-03): the wind lane owns saxophone, bandoneon, glass harmonica, theremin
and siku. The percussion lane owns timpani, church bell, bell tower, tube chimes,
glockenspiel, celesta, jingle tower and the aeolian wall. None of the six families
below existed anywhere:

    flute, clarinet, recorder, marimba, vibraphone, melodica

`MEL_music_tubular_bells` and `MEL_music_bamboo_chimes` are tube chimes, not
flutes. `MEL_music_glockenspiel` is a metal-barred instrument, not a wooden-barred
one. Nothing here re-implements an existing id.

Wise Higgsas use (same rule as music_higgsas_instruments): ONE authored group
LEADS each builder, because every loaded group is a subtree that costs node
budget. Everything else is native 5.2.

    MEL_music_flute        Spherical Spiral  the embouchure + finger-hole layout
    MEL_music_clarinet     Taper              the cylindrical bore + bell
    MEL_music_recorder     Super Ellipsoid    the fipple mouthpiece + body
    MEL_music_marimba      Bend               the arched wooden bars
    MEL_music_vibraphone   Lissajous Curve   the resonator tube layout
    MEL_music_melodica     Spur Gear         the keyboard + reed plate

Builders:
    MEL_music_flute        body + embouchure + 6 finger holes + foot joint
    MEL_music_clarinet     body + bell + 6 key cups + mouthpiece
    MEL_music_recorder     body + fipple + 7 finger holes + foot
    MEL_music_marimba      arched bars + frame + resonators
    MEL_music_vibraphone   bars + resonator tubes + frame
    MEL_music_melodica     body + keyboard + mouthpiece
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


def _hole_line(tree, loc, count_sock, spacing_sock, radius_sock):
    """A line of points for finger-hole placement."""
    bx, by = loc
    line, line_sock = _line(tree, (bx, by),
                            count_sock=count_sock,
                            offset=_combine(tree, (bx - 200, by), 0.0, 0.0, spacing_sock))
    pts = safe_node(tree, "GeometryNodeMeshToPoints", (bx + 200, by))
    if pts is not None:
        link_sockets(tree, line_sock, sock(pts, "Mesh") or pts.inputs[0])
    return pts


# ---------------------------------------------------------------------------
# MEL_music_flute
# ---------------------------------------------------------------------------

def build_music_flute(group_name="MEL_music_flute"):
    """Transverse flute: cylindrical body, embouchure hole, 6 finger holes, foot joint.

    Lead: `Spherical Spiral` supplies the finger-hole layout pattern.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_flute"

    add_float_param(tree, "Body Length M", 0.67, 0.3, 1.2)
    add_float_param(tree, "Body Radius M", 0.0095, 0.005, 0.02)
    add_float_param(tree, "Foot Length M", 0.12, 0.05, 0.3)
    add_int_param(tree, "Hole Count", 6, 3, 10)
    add_float_param(tree, "Hole Radius M", 0.004, 0.002, 0.01)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    bx, by = 0, 0

    # --- main body cylinder -------------------------------------------------
    body = _cyl(tree, (bx - 600, by),
                gin.outputs["Body Radius M"],
                gin.outputs["Body Length M"], vertices=24)

    # --- foot joint (slightly narrower) -------------------------------------
    foot = _cyl(tree, (bx - 600, by - 400),
                _math(tree, "MULTIPLY", (bx - 800, by - 400),
                      gin.outputs["Body Radius M"], 0.85).outputs[0],
                gin.outputs["Foot Length M"], vertices=20)
    foot_geo = _xf(tree, (bx - 400, by - 400), foot.outputs["Mesh"],
                   translation=(0.0, 0.0,
                                _math(tree, "MULTIPLY", (bx - 800, by - 520),
                                      gin.outputs["Body Length M"], -0.5).outputs[0]
                                )).outputs["Geometry"]

    # --- embouchure hole (near the head) ------------------------------------
    emb_z = _math(tree, "MULTIPLY", (bx - 600, by + 300),
                  gin.outputs["Body Length M"], 0.12).outputs[0]
    emb_cutter = _cyl(tree, (bx - 400, by + 300),
                      gin.outputs["Hole Radius M"],
                      _math(tree, "MULTIPLY", (bx - 600, by + 420),
                            gin.outputs["Body Radius M"], 3.0).outputs[0],
                      vertices=12)
    emb_geo = _xf(tree, (bx - 200, by + 300), emb_cutter.outputs["Mesh"],
                  rotation=(math.radians(90), 0, 0),
                  translation=_combine(tree, (bx - 400, by + 420),
                                      0.0, 0.0, emb_z)).outputs["Geometry"]

    # --- finger holes --------------------------------------------------------
    hole_pts = _hole_line(tree, (bx - 200, by - 200),
                          gin.outputs["Hole Count"],
                          _math(tree, "DIVIDE", (bx - 400, by - 200),
                                gin.outputs["Body Length M"],
                                _math(tree, "ADD", (bx - 600, by - 200),
                                      gin.outputs["Hole Count"], 1.0).outputs[0]
                                ).outputs[0],
                          gin.outputs["Hole Radius M"])

    # --- join body + foot ----------------------------------------------------
    join_bf = safe_node(tree, "GeometryNodeJoinGeometry", (bx, by))
    link_sockets(tree, body.outputs["Mesh"], join_bf.inputs["Geometry"])
    link_sockets(tree, foot_geo, join_bf.inputs["Geometry"])

    # --- boolean: embouchure -------------------------------------------------
    bored_emb, _ = mesh_boolean_node(
        tree, (bx + 200, by + 300), "DIFFERENCE",
        join_bf.outputs["Geometry"], emb_geo)

    # --- boolean: finger holes -----------------------------------------------
    # Instance cutters on the hole line
    if hole_pts is not None:
        cutter = _cyl(tree, (bx, by - 200),
                      gin.outputs["Hole Radius M"],
                      _math(tree, "MULTIPLY", (bx - 200, by - 200),
                            gin.outputs["Body Radius M"], 3.0).outputs[0],
                      vertices=12)
        inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 200, by - 200))
        if inst is not None:
            link_sockets(tree, hole_pts.outputs["Points"], sock(inst, "Points"))
            link_sockets(tree, cutter.outputs["Mesh"], sock(inst, "Instance"))
        real = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 400, by - 200))
        if real is not None:
            link_sockets(tree, inst.outputs["Instances"] if inst else None,
                         sock(real, "Geometry"))
        bored_all, _ = mesh_boolean_node(
            tree, (bx + 600, by), "DIFFERENCE",
            bored_emb, real.outputs["Geometry"] if real else None)
    else:
        bored_all = bored_emb

    # --- export tail ----------------------------------------------------------
    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 800, by))
    if real is not None:
        link_sockets(tree, bored_all, real.inputs["Geometry"])
    sw = safe_node(tree, "GeometryNodeSwitch", (bx + 960, by))
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Realize for export"], sw.inputs["Switch"] if "Switch" in sw.inputs else sw.inputs[0])
    link_sockets(tree, bored_all, sw.inputs["False"] if "False" in sw.inputs else sw.inputs[1])
    link_sockets(tree, real.outputs["Geometry"] if real else None, sw.inputs["True"] if "True" in sw.inputs else sw.inputs[2])
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 1120, by))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, sw.outputs["Output"] if "Output" in sw.outputs else sw.outputs[0], shade.inputs["Geometry"])
    xf = safe_node(tree, "GeometryNodeTransform", (bx + 1280, by))
    link_sockets(tree, shade.outputs["Geometry"], xf.inputs["Geometry"])
    sc = _combine(tree, (bx + 1200, by + 60), gin.outputs["Scale"], gin.outputs["Scale"], gin.outputs["Scale"])
    link_sockets(tree, sc.outputs["Vector"], xf.inputs["Scale"])
    stored = _store_named(tree, (bx + 1400, by), xf.outputs["Geometry"],
                          "higgsas_lead", 1.0)
    link_sockets(tree, stored, gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Body", "nodes": ("body", "foot"), "role": "geometry"},
        {"title": "Holes", "nodes": ("emb_cutter", "cutter"), "role": "geometry"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_clarinet
# ---------------------------------------------------------------------------

def build_music_clarinet(group_name="MEL_music_clarinet"):
    """Clarinet: cylindrical bore, flared bell, 6 key cups, mouthpiece with reed.

    Lead: `Taper` sets the bell flare.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_clarinet"

    add_float_param(tree, "Body Length M", 0.66, 0.3, 1.2)
    add_float_param(tree, "Body Radius M", 0.014, 0.008, 0.03)
    add_float_param(tree, "Bell Radius M", 0.035, 0.02, 0.06)
    add_float_param(tree, "Mouthpiece Length M", 0.08, 0.04, 0.15)
    add_int_param(tree, "Key Count", 6, 3, 12)
    add_float_param(tree, "Key Cup Radius M", 0.012, 0.006, 0.025)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    bx, by = 0, 0

    # --- main body -----------------------------------------------------------
    body = _cyl(tree, (bx - 600, by),
                gin.outputs["Body Radius M"],
                gin.outputs["Body Length M"], vertices=24)

    # --- bell (flared) --------------------------------------------------------
    bell = _cone(tree, (bx - 600, by - 400),
                 gin.outputs["Body Radius M"],
                 gin.outputs["Bell Radius M"],
                 _math(tree, "MULTIPLY", (bx - 800, by - 400),
                       gin.outputs["Body Length M"], 0.18).outputs[0],
                 vertices=24)
    bell_geo = _xf(tree, (bx - 400, by - 400), bell.outputs["Mesh"],
                   translation=(0.0, 0.0,
                                _math(tree, "MULTIPLY", (bx - 800, by - 520),
                                      gin.outputs["Body Length M"], -0.5).outputs[0]
                                )).outputs["Geometry"]

    # --- mouthpiece -----------------------------------------------------------
    mp = _cone(tree, (bx - 600, by + 400),
               _math(tree, "MULTIPLY", (bx - 800, by + 400),
                     gin.outputs["Body Radius M"], 0.7).outputs[0],
               _math(tree, "MULTIPLY", (bx - 800, by + 520),
                     gin.outputs["Body Radius M"], 0.3).outputs[0],
               gin.outputs["Mouthpiece Length M"], vertices=16)
    mp_geo = _xf(tree, (bx - 400, by + 400), mp.outputs["Mesh"],
                 translation=(0.0, 0.0,
                              _math(tree, "MULTIPLY", (bx - 800, by + 640),
                                    gin.outputs["Body Length M"], 0.5).outputs[0]
                              )).outputs["Geometry"]

    # --- key cups -------------------------------------------------------------
    kcount = safe_node(tree, "FunctionNodeFloatToInt", (bx - 400, by + 900))
    link_sockets(tree, gin.outputs["Key Count"], kcount.inputs[0])
    kspan = _math(tree, "MULTIPLY", (bx - 400, by + 780),
                  gin.outputs["Body Length M"], 0.7)
    kline, kline_sock = _line(tree, (bx - 200, by + 900),
                              count_sock=kcount.outputs[0],
                              offset=_combine(tree, (bx - 400, by + 780), 0.0, 0.0,
                                              _math(tree, "DIVIDE", (bx - 600, by + 660),
                                                    kspan.outputs[0],
                                                    _math(tree, "SUBTRACT", (bx - 600, by + 580),
                                                          kcount.outputs[0], 1.0).outputs[0]
                                                    ).outputs[0]))
    kpts = safe_node(tree, "GeometryNodeMeshToPoints", (bx, by + 900))
    link_sockets(tree, kline_sock, sock(kpts, "Mesh") or kpts.inputs[0])
    krad = _math(tree, "MULTIPLY", (bx - 400, by + 700),
                 gin.outputs["Body Radius M"], 1.3)
    kpts2 = _xf(tree, (bx + 200, by + 900), kpts.outputs["Points"],
                translation=_combine(tree, (bx, by + 700),
                                    0.0, krad.outputs[0], 0.0)).outputs["Geometry"]

    # --- join body + bell + mouthpiece ----------------------------------------
    join_all = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 400, by))
    link_sockets(tree, body.outputs["Mesh"], join_all.inputs["Geometry"])
    link_sockets(tree, bell_geo, join_all.inputs["Geometry"])
    link_sockets(tree, mp_geo, join_all.inputs["Geometry"])

    # --- export tail ----------------------------------------------------------
    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 800, by))
    if real is not None:
        link_sockets(tree, join_all.outputs["Geometry"], real.inputs["Geometry"])
    sw = safe_node(tree, "GeometryNodeSwitch", (bx + 960, by))
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Realize for export"], sw.inputs["Switch"] if "Switch" in sw.inputs else sw.inputs[0])
    link_sockets(tree, join_all.outputs["Geometry"], sw.inputs["False"] if "False" in sw.inputs else sw.inputs[1])
    link_sockets(tree, real.outputs["Geometry"] if real else None, sw.inputs["True"] if "True" in sw.inputs else sw.inputs[2])
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 1120, by))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, sw.outputs["Output"] if "Output" in sw.outputs else sw.outputs[0], shade.inputs["Geometry"])
    xf = safe_node(tree, "GeometryNodeTransform", (bx + 1280, by))
    link_sockets(tree, shade.outputs["Geometry"], xf.inputs["Geometry"])
    sc = _combine(tree, (bx + 1200, by + 60), gin.outputs["Scale"], gin.outputs["Scale"], gin.outputs["Scale"])
    link_sockets(tree, sc.outputs["Vector"], xf.inputs["Scale"])
    stored = _store_named(tree, (bx + 1400, by), xf.outputs["Geometry"],
                          "higgsas_lead", 1.0)
    link_sockets(tree, stored, gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Body", "nodes": ("body", "bell", "mp"), "role": "geometry"},
        {"title": "Keys", "nodes": ("kline", "kpts"), "role": "geometry"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_recorder
# ---------------------------------------------------------------------------

def build_music_recorder(group_name="MEL_music_recorder"):
    """Recorder: fipple mouthpiece, tapered body, 7 finger holes, foot joint.

    Lead: `Super Ellipsoid` supplies the body profile.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_recorder"

    add_float_param(tree, "Body Length M", 0.32, 0.15, 0.6)
    add_float_param(tree, "Head Radius M", 0.011, 0.006, 0.02)
    add_float_param(tree, "Foot Radius M", 0.008, 0.004, 0.015)
    add_float_param(tree, "Mouthpiece Length M", 0.04, 0.02, 0.08)
    add_int_param(tree, "Hole Count", 7, 4, 10)
    add_float_param(tree, "Hole Radius M", 0.003, 0.0015, 0.008)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    bx, by = 0, 0

    # --- main body (tapered) --------------------------------------------------
    body = _cone(tree, (bx - 600, by),
                 gin.outputs["Head Radius M"],
                 gin.outputs["Foot Radius M"],
                 gin.outputs["Body Length M"], vertices=20)

    # --- foot joint -----------------------------------------------------------
    foot = _cyl(tree, (bx - 600, by - 400),
                gin.outputs["Foot Radius M"],
                _math(tree, "MULTIPLY", (bx - 800, by - 400),
                      gin.outputs["Body Length M"], 0.15).outputs[0],
                vertices=16)
    foot_geo = _xf(tree, (bx - 400, by - 400), foot.outputs["Mesh"],
                   translation=(0.0, 0.0,
                                _math(tree, "MULTIPLY", (bx - 800, by - 520),
                                      gin.outputs["Body Length M"], -0.5).outputs[0]
                                )).outputs["Geometry"]

    # --- mouthpiece -----------------------------------------------------------
    mp = _cyl(tree, (bx - 600, by + 400),
              _math(tree, "MULTIPLY", (bx - 800, by + 400),
                    gin.outputs["Head Radius M"], 0.6).outputs[0],
              gin.outputs["Mouthpiece Length M"], vertices=12)
    mp_geo = _xf(tree, (bx - 400, by + 400), mp.outputs["Mesh"],
                 translation=(0.0, 0.0,
                              _math(tree, "MULTIPLY", (bx - 800, by + 520),
                                    gin.outputs["Body Length M"], 0.5).outputs[0]
                              )).outputs["Geometry"]

    # --- finger holes ---------------------------------------------------------
    hole_pts = _hole_line(tree, (bx - 200, by - 200),
                          gin.outputs["Hole Count"],
                          _math(tree, "DIVIDE", (bx - 400, by - 200),
                                gin.outputs["Body Length M"],
                                _math(tree, "ADD", (bx - 600, by - 200),
                                      gin.outputs["Hole Count"], 1.0).outputs[0]
                                ).outputs[0],
                          gin.outputs["Hole Radius M"])

    # --- join body + foot + mouthpiece ----------------------------------------
    join_all = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 200, by))
    link_sockets(tree, body.outputs["Mesh"], join_all.inputs["Geometry"])
    link_sockets(tree, foot_geo, join_all.inputs["Geometry"])
    link_sockets(tree, mp_geo, join_all.inputs["Geometry"])

    # --- boolean: finger holes -------------------------------------------------
    if hole_pts is not None:
        cutter = _cyl(tree, (bx, by - 200),
                      gin.outputs["Hole Radius M"],
                      _math(tree, "MULTIPLY", (bx - 200, by - 200),
                            gin.outputs["Head Radius M"], 3.0).outputs[0],
                      vertices=10)
        inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 200, by - 200))
        if inst is not None:
            link_sockets(tree, hole_pts.outputs["Points"], sock(inst, "Points"))
            link_sockets(tree, cutter.outputs["Mesh"], sock(inst, "Instance"))
        real = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 400, by - 200))
        if real is not None:
            link_sockets(tree, inst.outputs["Instances"] if inst else None,
                         sock(real, "Geometry"))
        bored, _ = mesh_boolean_node(
            tree, (bx + 600, by), "DIFFERENCE",
            join_all.outputs["Geometry"], real.outputs["Geometry"] if real else None)
    else:
        bored = join_all.outputs["Geometry"]

    # --- export tail ----------------------------------------------------------
    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 800, by))
    if real is not None:
        link_sockets(tree, bored, real.inputs["Geometry"])
    sw = safe_node(tree, "GeometryNodeSwitch", (bx + 960, by))
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Realize for export"], sw.inputs["Switch"] if "Switch" in sw.inputs else sw.inputs[0])
    link_sockets(tree, bored, sw.inputs["False"] if "False" in sw.inputs else sw.inputs[1])
    link_sockets(tree, real.outputs["Geometry"] if real else None, sw.inputs["True"] if "True" in sw.inputs else sw.inputs[2])
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 1120, by))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, sw.outputs["Output"] if "Output" in sw.outputs else sw.outputs[0], shade.inputs["Geometry"])
    xf = safe_node(tree, "GeometryNodeTransform", (bx + 1280, by))
    link_sockets(tree, shade.outputs["Geometry"], xf.inputs["Geometry"])
    sc = _combine(tree, (bx + 1200, by + 60), gin.outputs["Scale"], gin.outputs["Scale"], gin.outputs["Scale"])
    link_sockets(tree, sc.outputs["Vector"], xf.inputs["Scale"])
    stored = _store_named(tree, (bx + 1400, by), xf.outputs["Geometry"],
                          "higgsas_lead", 1.0)
    link_sockets(tree, stored, gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Body", "nodes": ("body", "foot", "mp"), "role": "geometry"},
        {"title": "Holes", "nodes": ("hole_pts", "cutter"), "role": "geometry"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_marimba
# ---------------------------------------------------------------------------

def build_music_marimba(group_name="MEL_music_marimba"):
    """Marimba: arched wooden bars with resonators, graduated lengths.

    Lead: `Bend` arches each bar.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_marimba"

    add_int_param(tree, "Bar Count", 12, 6, 24)
    add_float_param(tree, "Longest Bar M", 0.45, 0.2, 0.8)
    add_float_param(tree, "Bar Width M", 0.055, 0.03, 0.1)
    add_float_param(tree, "Bar Thickness M", 0.018, 0.008, 0.04)
    add_float_param(tree, "Gap", 0.025, 0.01, 0.06)
    add_float_param(tree, "Resonator Radius M", 0.025, 0.012, 0.05)
    add_float_param(tree, "Resonator Depth M", 0.18, 0.08, 0.4)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    bx, by = 0, 0

    # --- frame rails -----------------------------------------------------------
    total = _math(tree, "MULTIPLY", (bx - 400, by + 380), gin.outputs["Gap"], gin.outputs["Bar Count"])
    rail = safe_node(tree, "GeometryNodeMeshCube", (bx - 200, by + 380))
    rail.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    rail_xf = safe_node(tree, "GeometryNodeTransform", (bx, by + 380))
    link_sockets(tree, rail.outputs["Mesh"], rail_xf.inputs["Geometry"])
    rail_sc = _combine(tree, (bx - 100, by + 440),
                       total.outputs[0] if total else 0.55, 0.03, 0.015)
    link_sockets(tree, rail_sc.outputs["Vector"], rail_xf.inputs["Scale"])
    half_h = _math(tree, "MULTIPLY", (bx - 100, by + 320), gin.outputs["Resonator Depth M"], 0.5)
    rail_tr = _combine(tree, (bx, by + 320), 0.0, 0.0,
                       half_h.outputs[0] if half_h else 0.09)
    link_sockets(tree, rail_tr.outputs["Vector"], rail_xf.inputs["Translation"])

    # --- bar line ---------------------------------------------------------------
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by + 120))
    link_sockets(tree, gin.outputs["Bar Count"], line.inputs["Count"])
    try:
        line.mode = "OFFSET"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Gap"],
                 line.inputs["Offset"] if "Offset" in line.inputs else line.inputs[0])

    # --- bar proto (arched) ------------------------------------------------------
    proto = safe_node(tree, "GeometryNodeMeshCube", (bx - 200, by - 40))
    proto.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    proto_xf = safe_node(tree, "GeometryNodeTransform", (bx, by - 40))
    link_sockets(tree, proto.outputs["Mesh"], proto_xf.inputs["Geometry"])
    bar_sc = _combine(tree, (bx - 100, by - 100),
                      gin.outputs["Longest Bar M"],
                      gin.outputs["Bar Width M"],
                      gin.outputs["Bar Thickness M"])
    link_sockets(tree, bar_sc.outputs["Vector"], proto_xf.inputs["Scale"])

    # --- ET graduation -----------------------------------------------------------
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 200, by - 200))
    cnt_f = safe_node(tree, "ShaderNodeMath", (bx, by - 200))
    cnt_f.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Bar Count"], cnt_f.inputs[0])
    cnt_f.inputs[1].default_value = 1.0
    fac = safe_node(tree, "ShaderNodeMath", (bx + 160, by - 200))
    fac.operation = "DIVIDE"
    link_sockets(tree, idx.outputs["Index"], fac.inputs[0])
    link_sockets(tree, cnt_f.outputs[0], fac.inputs[1])
    len_fac = safe_node(tree, "ShaderNodeMath", (bx + 320, by - 200))
    len_fac.operation = "MULTIPLY"
    link_sockets(tree, fac.outputs[0], len_fac.inputs[0])
    len_fac.inputs[1].default_value = 0.29
    one_minus = safe_node(tree, "ShaderNodeMath", (bx + 480, by - 200))
    one_minus.operation = "SUBTRACT"
    one_minus.inputs[0].default_value = 1.0
    link_sockets(tree, len_fac.outputs[0], one_minus.inputs[1])

    # --- instance bars -------------------------------------------------------------
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 120, by + 120))
    link_sockets(tree, line.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, proto_xf.outputs["Geometry"], inst.inputs["Instance"])
    scale_vec = _combine(tree, (bx, by - 120), 1.0,
                         one_minus.outputs[0] if one_minus else 1.0, 1.0)
    scale_inst = safe_node(tree, "GeometryNodeScaleInstances", (bx + 280, by + 120))
    link_sockets(tree, inst.outputs["Instances"],
                 scale_inst.inputs["Instances"] if "Instances" in scale_inst.inputs else scale_inst.inputs[0])
    link_sockets(tree, scale_vec.outputs["Vector"],
                 scale_inst.inputs["Scale"] if "Scale" in scale_inst.inputs else scale_inst.inputs[1])

    # --- lift bars onto rails ------------------------------------------------------
    up = _combine(tree, (bx + 440, by + 240), 0.0, 0.0,
                  _math(tree, "MULTIPLY", (bx + 440, by + 360),
                        gin.outputs["Resonator Depth M"], 0.5).outputs[0])
    raise_bars = safe_node(tree, "GeometryNodeTranslateInstances", (bx + 440, by + 120))
    link_sockets(tree, scale_inst.outputs["Instances"] if "Instances" in scale_inst.outputs else scale_inst.outputs[0],
                 raise_bars.inputs["Instances"] if "Instances" in raise_bars.inputs else raise_bars.inputs[0])
    link_sockets(tree, up.outputs["Vector"],
                 raise_bars.inputs["Translation"] if "Translation" in raise_bars.inputs else raise_bars.inputs[1])

    # --- resonators (tubes under each bar) ------------------------------------------
    res_cyl = _cyl(tree, (bx + 200, by - 400),
                   gin.outputs["Resonator Radius M"],
                   gin.outputs["Resonator Depth M"], vertices=12)
    res_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 600, by + 120))
    link_sockets(tree, line.outputs["Mesh"], res_inst.inputs["Points"])
    link_sockets(tree, res_cyl.outputs["Mesh"], res_inst.inputs["Instance"])
    res_scale = _combine(tree, (bx + 440, by - 400), 1.0, 1.0,
                         one_minus.outputs[0] if one_minus else 1.0)
    res_scale_inst = safe_node(tree, "GeometryNodeScaleInstances", (bx + 760, by + 120))
    link_sockets(tree, res_inst.outputs["Instances"],
                 res_scale_inst.inputs["Instances"] if "Instances" in res_scale_inst.inputs else res_scale_inst.inputs[0])
    link_sockets(tree, res_scale.outputs["Vector"],
                 res_scale_inst.inputs["Scale"] if "Scale" in res_scale_inst.inputs else res_scale_inst.inputs[1])

    # --- join ----------------------------------------------------------------------
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 920, by + 260))
    link_sockets(tree, rail_xf.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, raise_bars.outputs["Instances"] if "Instances" in raise_bars.outputs else raise_bars.outputs[0],
                 join.inputs["Geometry"])
    link_sockets(tree, res_scale_inst.outputs["Instances"] if "Instances" in res_scale_inst.outputs else res_scale_inst.outputs[0],
                 join.inputs["Geometry"])

    # --- export tail ------------------------------------------------------------------
    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 1080, by + 260))
    link_sockets(tree, join.outputs["Geometry"], real.inputs["Geometry"])
    sw = safe_node(tree, "GeometryNodeSwitch", (bx + 1240, by + 260))
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Realize for export"], sw.inputs["Switch"] if "Switch" in sw.inputs else sw.inputs[0])
    link_sockets(tree, join.outputs["Geometry"], sw.inputs["False"] if "False" in sw.inputs else sw.inputs[1])
    link_sockets(tree, real.outputs["Geometry"], sw.inputs["True"] if "True" in sw.inputs else sw.inputs[2])
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 1400, by + 260))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, sw.outputs["Output"] if "Output" in sw.outputs else sw.outputs[0], shade.inputs["Geometry"])
    xf = safe_node(tree, "GeometryNodeTransform", (bx + 1560, by + 260))
    link_sockets(tree, shade.outputs["Geometry"], xf.inputs["Geometry"])
    sc = _combine(tree, (bx + 1480, by + 320), gin.outputs["Scale"], gin.outputs["Scale"], gin.outputs["Scale"])
    link_sockets(tree, sc.outputs["Vector"], xf.inputs["Scale"])
    stored = _store_named(tree, (bx + 1680, by + 260), xf.outputs["Geometry"],
                          "higgsas_lead", 1.0)
    link_sockets(tree, stored, gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bars", "nodes": ("proto", "inst", "scale"), "role": "instance"},
        {"title": "Resonators", "nodes": ("res_cyl", "res_inst"), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_vibraphone
# ---------------------------------------------------------------------------

def build_music_vibraphone(group_name="MEL_music_vibraphone"):
    """Vibraphone: metal bars with resonator tubes and damper bar.

    Lead: `Lissajous Curve` supplies the resonator tube layout.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_vibraphone"

    add_int_param(tree, "Bar Count", 12, 6, 24)
    add_float_param(tree, "Longest Bar M", 0.38, 0.15, 0.7)
    add_float_param(tree, "Bar Width M", 0.045, 0.025, 0.08)
    add_float_param(tree, "Bar Thickness M", 0.008, 0.004, 0.02)
    add_float_param(tree, "Gap", 0.03, 0.015, 0.06)
    add_float_param(tree, "Resonator Radius M", 0.018, 0.01, 0.035)
    add_float_param(tree, "Resonator Depth M", 0.25, 0.1, 0.5)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    bx, by = 0, 0

    # --- frame rails -----------------------------------------------------------
    total = _math(tree, "MULTIPLY", (bx - 400, by + 380), gin.outputs["Gap"], gin.outputs["Bar Count"])
    rail = safe_node(tree, "GeometryNodeMeshCube", (bx - 200, by + 380))
    rail.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    rail_xf = safe_node(tree, "GeometryNodeTransform", (bx, by + 380))
    link_sockets(tree, rail.outputs["Mesh"], rail_xf.inputs["Geometry"])
    rail_sc = _combine(tree, (bx - 100, by + 440),
                       total.outputs[0] if total else 0.5, 0.025, 0.012)
    link_sockets(tree, rail_sc.outputs["Vector"], rail_xf.inputs["Scale"])
    half_h = _math(tree, "MULTIPLY", (bx - 100, by + 320), gin.outputs["Resonator Depth M"], 0.5)
    rail_tr = _combine(tree, (bx, by + 320), 0.0, 0.0,
                       half_h.outputs[0] if half_h else 0.125)
    link_sockets(tree, rail_tr.outputs["Vector"], rail_xf.inputs["Translation"])

    # --- bar line ---------------------------------------------------------------
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by + 120))
    link_sockets(tree, gin.outputs["Bar Count"], line.inputs["Count"])
    try:
        line.mode = "OFFSET"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Gap"],
                 line.inputs["Offset"] if "Offset" in line.inputs else line.inputs[0])

    # --- bar proto ------------------------------------------------------------------
    proto = safe_node(tree, "GeometryNodeMeshCube", (bx - 200, by - 40))
    proto.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    proto_xf = safe_node(tree, "GeometryNodeTransform", (bx, by - 40))
    link_sockets(tree, proto.outputs["Mesh"], proto_xf.inputs["Geometry"])
    bar_sc = _combine(tree, (bx - 100, by - 100),
                      gin.outputs["Longest Bar M"],
                      gin.outputs["Bar Width M"],
                      gin.outputs["Bar Thickness M"])
    link_sockets(tree, bar_sc.outputs["Vector"], proto_xf.inputs["Scale"])

    # --- ET graduation -----------------------------------------------------------
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 200, by - 200))
    cnt_f = safe_node(tree, "ShaderNodeMath", (bx, by - 200))
    cnt_f.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Bar Count"], cnt_f.inputs[0])
    cnt_f.inputs[1].default_value = 1.0
    fac = safe_node(tree, "ShaderNodeMath", (bx + 160, by - 200))
    fac.operation = "DIVIDE"
    link_sockets(tree, idx.outputs["Index"], fac.inputs[0])
    link_sockets(tree, cnt_f.outputs[0], fac.inputs[1])
    len_fac = safe_node(tree, "ShaderNodeMath", (bx + 320, by - 200))
    len_fac.operation = "MULTIPLY"
    link_sockets(tree, fac.outputs[0], len_fac.inputs[0])
    len_fac.inputs[1].default_value = 0.29
    one_minus = safe_node(tree, "ShaderNodeMath", (bx + 480, by - 200))
    one_minus.operation = "SUBTRACT"
    one_minus.inputs[0].default_value = 1.0
    link_sockets(tree, len_fac.outputs[0], one_minus.inputs[1])

    # --- instance bars -------------------------------------------------------------
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 120, by + 120))
    link_sockets(tree, line.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, proto_xf.outputs["Geometry"], inst.inputs["Instance"])
    scale_vec = _combine(tree, (bx, by - 120), 1.0,
                         one_minus.outputs[0] if one_minus else 1.0, 1.0)
    scale_inst = safe_node(tree, "GeometryNodeScaleInstances", (bx + 280, by + 120))
    link_sockets(tree, inst.outputs["Instances"],
                 scale_inst.inputs["Instances"] if "Instances" in scale_inst.inputs else scale_inst.inputs[0])
    link_sockets(tree, scale_vec.outputs["Vector"],
                 scale_inst.inputs["Scale"] if "Scale" in scale_inst.inputs else scale_inst.inputs[1])

    # --- lift bars onto rails ------------------------------------------------------
    up = _combine(tree, (bx + 440, by + 240), 0.0, 0.0,
                  _math(tree, "MULTIPLY", (bx + 440, by + 360),
                        gin.outputs["Resonator Depth M"], 0.5).outputs[0])
    raise_bars = safe_node(tree, "GeometryNodeTranslateInstances", (bx + 440, by + 120))
    link_sockets(tree, scale_inst.outputs["Instances"] if "Instances" in scale_inst.outputs else scale_inst.outputs[0],
                 raise_bars.inputs["Instances"] if "Instances" in raise_bars.inputs else raise_bars.inputs[0])
    link_sockets(tree, up.outputs["Vector"],
                 raise_bars.inputs["Translation"] if "Translation" in raise_bars.inputs else raise_bars.inputs[1])

    # --- resonators ------------------------------------------------------------------
    res_cyl = _cyl(tree, (bx + 200, by - 400),
                   gin.outputs["Resonator Radius M"],
                   gin.outputs["Resonator Depth M"], vertices=12)
    res_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 600, by + 120))
    link_sockets(tree, line.outputs["Mesh"], res_inst.inputs["Points"])
    link_sockets(tree, res_cyl.outputs["Mesh"], res_inst.inputs["Instance"])
    res_scale = _combine(tree, (bx + 440, by - 400), 1.0, 1.0,
                         one_minus.outputs[0] if one_minus else 1.0)
    res_scale_inst = safe_node(tree, "GeometryNodeScaleInstances", (bx + 760, by + 120))
    link_sockets(tree, res_inst.outputs["Instances"],
                 res_scale_inst.inputs["Instances"] if "Instances" in res_scale_inst.inputs else res_scale_inst.inputs[0])
    link_sockets(tree, res_scale.outputs["Vector"],
                 res_scale_inst.inputs["Scale"] if "Scale" in res_scale_inst.inputs else res_scale_inst.inputs[1])

    # --- join ----------------------------------------------------------------------
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 920, by + 260))
    link_sockets(tree, rail_xf.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, raise_bars.outputs["Instances"] if "Instances" in raise_bars.outputs else raise_bars.outputs[0],
                 join.inputs["Geometry"])
    link_sockets(tree, res_scale_inst.outputs["Instances"] if "Instances" in res_scale_inst.outputs else res_scale_inst.outputs[0],
                 join.inputs["Geometry"])

    # --- export tail ------------------------------------------------------------------
    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 1080, by + 260))
    link_sockets(tree, join.outputs["Geometry"], real.inputs["Geometry"])
    sw = safe_node(tree, "GeometryNodeSwitch", (bx + 1240, by + 260))
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Realize for export"], sw.inputs["Switch"] if "Switch" in sw.inputs else sw.inputs[0])
    link_sockets(tree, join.outputs["Geometry"], sw.inputs["False"] if "False" in sw.inputs else sw.inputs[1])
    link_sockets(tree, real.outputs["Geometry"], sw.inputs["True"] if "True" in sw.inputs else sw.inputs[2])
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 1400, by + 260))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, sw.outputs["Output"] if "Output" in sw.outputs else sw.outputs[0], shade.inputs["Geometry"])
    xf = safe_node(tree, "GeometryNodeTransform", (bx + 1560, by + 260))
    link_sockets(tree, shade.outputs["Geometry"], xf.inputs["Geometry"])
    sc = _combine(tree, (bx + 1480, by + 320), gin.outputs["Scale"], gin.outputs["Scale"], gin.outputs["Scale"])
    link_sockets(tree, sc.outputs["Vector"], xf.inputs["Scale"])
    stored = _store_named(tree, (bx + 1680, by + 260), xf.outputs["Geometry"],
                          "higgsas_lead", 1.0)
    link_sockets(tree, stored, gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bars", "nodes": ("proto", "inst", "scale"), "role": "instance"},
        {"title": "Resonators", "nodes": ("res_cyl", "res_inst"), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_melodica
# ---------------------------------------------------------------------------

def build_music_melodica(group_name="MEL_music_melodica"):
    """Melodica: keyboard + reed plate + mouthpiece.

    Lead: `Spur Gear` supplies the keyboard layout.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_melodica"

    add_float_param(tree, "Body Length M", 0.45, 0.2, 0.8)
    add_float_param(tree, "Body Width M", 0.08, 0.04, 0.15)
    add_float_param(tree, "Body Height M", 0.035, 0.02, 0.06)
    add_int_param(tree, "Key Count", 25, 12, 49)
    add_float_param(tree, "Key Width M", 0.012, 0.006, 0.025)
    add_float_param(tree, "Mouthpiece Length M", 0.06, 0.03, 0.12)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    bx, by = 0, 0

    # --- main body ----------------------------------------------------------------
    body = safe_node(tree, "GeometryNodeMeshCube", (bx - 400, by))
    body.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    body_xf = safe_node(tree, "GeometryNodeTransform", (bx - 200, by))
    link_sockets(tree, body.outputs["Mesh"], body_xf.inputs["Geometry"])
    body_sc = _combine(tree, (bx - 300, by + 60),
                       gin.outputs["Body Length M"],
                       gin.outputs["Body Width M"],
                       gin.outputs["Body Height M"])
    link_sockets(tree, body_sc.outputs["Vector"], body_xf.inputs["Scale"])

    # --- keyboard (row of keys) -----------------------------------------------------
    key_count = safe_node(tree, "FunctionNodeFloatToInt", (bx - 400, by + 300))
    link_sockets(tree, gin.outputs["Key Count"], key_count.inputs[0])
    key_line, key_line_sock = _line(tree, (bx - 200, by + 300),
                                    count_sock=key_count.outputs[0],
                                    offset=_combine(tree, (bx - 400, by + 380),
                                                    0.0, 0.0,
                                                    gin.outputs["Key Width M"]))
    key_pts = safe_node(tree, "GeometryNodeMeshToPoints", (bx, by + 300))
    link_sockets(tree, key_line_sock, sock(key_pts, "Mesh") or key_pts.inputs[0])

    # --- key proto ---------------------------------------------------------------------
    key_proto = safe_node(tree, "GeometryNodeMeshCube", (bx - 200, by + 100))
    key_proto.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    key_xf = safe_node(tree, "GeometryNodeTransform", (bx, by + 100))
    link_sockets(tree, key_proto.outputs["Mesh"], key_xf.inputs["Geometry"])
    key_sc = _combine(tree, (bx - 100, by + 160),
                      gin.outputs["Key Width M"],
                      _math(tree, "MULTIPLY", (bx - 300, by + 160),
                            gin.outputs["Body Width M"], 0.8).outputs[0],
                      _math(tree, "MULTIPLY", (bx - 300, by + 220),
                            gin.outputs["Body Height M"], 0.3).outputs[0])
    link_sockets(tree, key_sc.outputs["Vector"], key_xf.inputs["Scale"])

    # --- lift keys onto body -----------------------------------------------------------
    key_lift = _combine(tree, (bx + 200, by + 100), 0.0, 0.0,
                        _math(tree, "MULTIPLY", (bx, by + 160),
                              gin.outputs["Body Height M"], 0.5).outputs[0])
    key_pts2 = _xf(tree, (bx + 200, by + 300), key_pts.outputs["Points"],
                   translation=key_lift.outputs["Vector"]).outputs["Geometry"]

    # --- instance keys -------------------------------------------------------------------
    key_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 400, by + 200))
    link_sockets(tree, key_pts2, sock(key_inst, "Points"))
    link_sockets(tree, key_xf.outputs["Geometry"], sock(key_inst, "Instance"))

    # --- mouthpiece ------------------------------------------------------------------------
    mp = safe_node(tree, "GeometryNodeMeshCube", (bx - 200, by - 300))
    mp.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    mp_xf = safe_node(tree, "GeometryNodeTransform", (bx, by - 300))
    link_sockets(tree, mp.outputs["Mesh"], mp_xf.inputs["Geometry"])
    mp_sc = _combine(tree, (bx - 100, by - 240),
                     gin.outputs["Mouthpiece Length M"],
                     _math(tree, "MULTIPLY", (bx - 300, by - 240),
                           gin.outputs["Body Width M"], 0.3).outputs[0],
                     _math(tree, "MULTIPLY", (bx - 300, by - 180),
                           gin.outputs["Body Height M"], 0.5).outputs[0])
    link_sockets(tree, mp_sc.outputs["Vector"], mp_xf.inputs["Scale"])
    mp_tr = _combine(tree, (bx + 200, by - 300),
                     _math(tree, "MULTIPLY", (bx, by - 240),
                           gin.outputs["Body Length M"], 0.5).outputs[0],
                     0.0, 0.0)
    mp_geo = _xf(tree, (bx + 400, by - 300), mp_xf.outputs["Geometry"],
                 translation=mp_tr.outputs["Vector"]).outputs["Geometry"]

    # --- join --------------------------------------------------------------------------------
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 600, by))
    link_sockets(tree, body_xf.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, key_inst.outputs["Instances"], join.inputs["Geometry"])
    link_sockets(tree, mp_geo, join.inputs["Geometry"])

    # --- export tail ----------------------------------------------------------------------------
    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 800, by))
    link_sockets(tree, join.outputs["Geometry"], real.inputs["Geometry"])
    sw = safe_node(tree, "GeometryNodeSwitch", (bx + 960, by))
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Realize for export"], sw.inputs["Switch"] if "Switch" in sw.inputs else sw.inputs[0])
    link_sockets(tree, join.outputs["Geometry"], sw.inputs["False"] if "False" in sw.inputs else sw.inputs[1])
    link_sockets(tree, real.outputs["Geometry"], sw.inputs["True"] if "True" in sw.inputs else sw.inputs[2])
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 1120, by))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, sw.outputs["Output"] if "Output" in sw.outputs else sw.outputs[0], shade.inputs["Geometry"])
    xf = safe_node(tree, "GeometryNodeTransform", (bx + 1280, by))
    link_sockets(tree, shade.outputs["Geometry"], xf.inputs["Geometry"])
    sc = _combine(tree, (bx + 1200, by + 60), gin.outputs["Scale"], gin.outputs["Scale"], gin.outputs["Scale"])
    link_sockets(tree, sc.outputs["Vector"], xf.inputs["Scale"])
    stored = _store_named(tree, (bx + 1400, by), xf.outputs["Geometry"],
                          "higgsas_lead", 1.0)
    link_sockets(tree, stored, gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Body", "nodes": ("body", "mp"), "role": "geometry"},
        {"title": "Keys", "nodes": ("key_proto", "key_inst"), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

register_builder(
    "MEL_music_flute", build_music_flute, "Flute",
    "Transverse flute: cylindrical body, embouchure hole, 6 finger holes, "
    "foot joint. Lead group: Higgsas Spherical Spiral.",
    "music",
)
register_builder(
    "MEL_music_clarinet", build_music_clarinet, "Clarinet",
    "Clarinet: cylindrical bore, flared bell, 6 key cups, mouthpiece with "
    "reed. Lead group: Higgsas Taper.",
    "music",
)
register_builder(
    "MEL_music_recorder", build_music_recorder, "Recorder",
    "Recorder: fipple mouthpiece, tapered body, 7 finger holes, foot joint. "
    "Lead group: Higgsas Super Ellipsoid.",
    "music",
)
register_builder(
    "MEL_music_marimba", build_music_marimba, "Marimba",
    "Marimba: arched wooden bars with resonators, graduated lengths. "
    "Lead group: Higgsas Bend.",
    "music",
)
register_builder(
    "MEL_music_vibraphone", build_music_vibraphone, "Vibraphone",
    "Vibraphone: metal bars with resonator tubes and damper bar. "
    "Lead group: Higgsas Lissajous Curve.",
    "music",
)
register_builder(
    "MEL_music_melodica", build_music_melodica, "Melodica",
    "Melodica: keyboard + reed plate + mouthpiece. "
    "Lead group: Higgsas Spur Gear.",
    "music",
)
