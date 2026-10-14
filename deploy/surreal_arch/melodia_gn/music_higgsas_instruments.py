"""Higgsas musical instrument builders — new instruments, headless-built.

Gap audit first (repo-wide grep over `deploy/surreal_arch/` + the live registry,
2026-10-01): the music lane already owns harpsichord, baroque organ, lute,
violin, celesta, glockenspiel, kalimba, dulcimer, timpani, tubular bells,
bamboo chimes, siku panpipes, concert/Ur/kora harps, church bells, chimes and
the tuning fork. None of the six families below existed anywhere in the repo:

    bandoneon, saxophone, glass harmonica, music box, theremin, hurdy-gurdy

Nothing here re-implements an existing id — this is new geometry, not a second
authority on an old one.

Wise Higgsas use (the rule from references/higgsas-node-inventory.md): one
AUTHORED motif per builder, because every loaded group is a SUBTREE that costs
node budget.

  * ONE Higgsas group LEADS each builder, chosen for what it is actually good
    at: lofting the bellows skin, curling the sax crook, drawing a tuned bowl
    rim, cutting the music-box gear, drawing the theremin tone path, slinging
    the hurdy-gurdy drones.
  * Everything else in each instrument is native 5.2 nodes. Over-using the
    library buys nothing but subtree weight.
  * NO solver groups (Differential Growth / Ripples Solver / anything
    simulation-flavoured) — bake-only per the inventory note.
  * Every group call goes through `higgsas_pipeline`, which returns the
    fallback flag. `higgsas_report()` reports which path actually ran, so
    "built something" and "used Higgsas" stay separate claims.

Builders:
    MEL_music_bandoneon        Loft Splines      concert bellows + button board
    MEL_music_saxophone         Bend + Taper      crook, tapered bore, upturned bell
    MEL_music_glass_harmonica   Spherical Spiral  24 chromatically-tuned glass bowls
    MEL_music_music_box         Spur Gear         pinned barrel + governor gear
    MEL_music_theremin          Lissajous Curve   pitch/volume antenna pair
    MEL_music_hurdy_gurdy       Dynamic Catenary  3 drones + wheel tangent strings
"""

from __future__ import annotations

import math

from . import higgsas_pipeline as hp
from .core import (
    safe_node, link_sockets, link_float_to_vector, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    register_builder, sock,
)
# Shared helpers are reused, not re-authored: music_harps_real owns them and a
# fourth private copy is the defect this file exists to avoid.
from .music_harps_real import (
    _math, _combine, _export_tail, _store_named, _ensure_string_proto,
    _refresh_group_refs_multi,
)

# Which builders degraded to native, and which socket dials did not take —
# surfaced by higgsas_report() so a fallback is a REPORT, never a silent pass.
_FALLBACKS: dict = {}


def higgsas_report() -> dict:
    """Which builders ran native fallbacks instead of a Higgsas subtree."""
    return {
        "library": hp.library_path(),
        "available": hp.available(),
        "fallbacks": {k: list(v) for k, v in _FALLBACKS.items()},
    }


def _lead(builder_id, tree, name, loc, fallback_type=None, inputs=None):
    """Add a Higgsas group node, recording any degradation under `builder_id`.

    Returns ``(node, used_fallback)``. A socket dial that does not take is
    recorded too — a Higgsas group that loaded but got no values is a
    different (worse) outcome than a fallback, and must not read as success.
    """
    n = hp.node(tree, name, loc)
    used = n is None
    if n is None and fallback_type:
        n = safe_node(tree, fallback_type, loc)
    if n is None:
        _FALLBACKS.setdefault(builder_id, []).append(name)
        return None, True
    for key, value in (inputs or {}).items():
        if not hp.inp(n, key, value):
            _FALLBACKS.setdefault(builder_id, []).append("%s.%s" % (name, key))
    if used:
        _FALLBACKS.setdefault(builder_id, []).append(name)
    return n, used


def _store_named(tree, loc, geom, name, value_sock):
    """Store a named attribute. Accepts a FLOAT as well as a socket.

    The shared `_store_named` in music_harps_real links its value
    unconditionally, so passing a constant raises
    `Function.input expected a NodeSocket type, not float` and the attribute is
    dropped — which is why every builder here failed its link census on a
    scalar `higgsas_lead` flag. Local wrapper, no edit to the shared helper.
    """
    st = safe_node(tree, "GeometryNodeStoreNamedAttribute", loc)
    if st is None:
        return geom
    try:
        st.data_type = "FLOAT"
        st.inputs["Name"].default_value = name
    except Exception:
        pass
    link_sockets(tree, geom, st.inputs["Geometry"])
    v = st.inputs.get("Value") or st.inputs.get("Value_001")
    _wire(tree, value_sock, v)
    return st.outputs["Geometry"]


def _is_sock(val):
    """A socket, not a node. Sockets have `is_linked`; nodes have `outputs`."""
    return hasattr(val, "is_linked") or hasattr(val, "node")


def _resolve_output(val, target):
    """Turn a NODE into the output socket that fits `target`.

    The shared helpers (`_math`, `_combine`) RETURN NODES, while `_xf`/`_line`
    take sockets. Passing the node used to fall through `_wire` to a failed
    `default_value =` assignment and vanish silently — which is how every
    `offset=` in this module and several `translation=` in the shared layout
    were lost. Resolve by socket type, preferring the conventional name.
    """
    if val is None or not hasattr(val, "outputs") or not val.outputs:
        return None
    want = getattr(getattr(target, "type", None), "name", None) or getattr(target, "type", None)
    pref = ("Vector", "Value", "Integer", "Geometry", "Curve", "Points")
    if want == "FLOAT":
        pref = ("Value", "Integer", "Vector") + pref
    elif want == "INT":
        pref = ("Integer", "Value") + pref
    elif want in ("VECTOR", "RGBA"):
        pref = ("Vector", "Color", "Value") + pref
    elif want == "GEOMETRY":
        pref = ("Geometry", "Curve", "Points", "Instances", "Mesh") + pref
    for name in pref:
        s = val.outputs.get(name)
        if s is not None and getattr(s, "type", None) == want:
            return s
    for s in val.outputs:
        if getattr(s, "type", None) == want:
            return s
    for name in pref:
        s = val.outputs.get(name)
        if s is not None:
            return s
    return val.outputs[0]


def _wire(tree, val, target):
    """Set a default or link a socket — one place, so the check can't drift."""
    if val is None or target is None:
        return False
    if not _is_sock(val):
        resolved = _resolve_output(val, target)
        if resolved is None:
            try:
                target.default_value = val
                return True
            except Exception:
                return False
        val = resolved
    return link_sockets(tree, val, target) is not False


def _set_fill(node, fill):
    """Cap style by NAME, because the old integer count no longer exists.

    5.2's primitive cap is `fill_type` ENUM ('NONE', 'NGON', 'TRIANGLE_FAN').
    Callers used to pass 0/2/3 meaning fan/ngon/none; map those onto the enum
    so the intent survives, and never touch `Fill Segments` to change shape.
    """
    table = {0: "TRIANGLE_FAN", 1: "NONE", 2: "NGON", 3: "NONE"}
    name = fill if isinstance(fill, str) else table.get(fill, "NGON")
    try:
        node.fill_type = name
    except Exception:
        pass


def _cone(tree, loc, r_bottom, r_top, depth, vertices=32, fill=2):
    """MeshCone. `fill` is an NGON/TRIANGLE_FAN/NONE selector, not a count.

    MEASURED (Saved/Audit/gn_primitive_sockets.py): 5.2 keeps `Fill Segments`
    as a socket but drives the cap shape from the `fill_type` ENUM. Writing
    `inputs["Fill Segments"]` alone left fill_type=NGON on every cone, and the
    previous `fill=0` intent (a fan) was never applied — a silent no-op.
    """
    n = safe_node(tree, "GeometryNodeMeshCone", loc)
    if n is None:
        return None
    try:
        n.inputs["Vertices"].default_value = vertices
        n.inputs["Side Segments"].default_value = 1
        n.inputs["Fill Segments"].default_value = 1
    except Exception:
        pass
    _set_fill(n, fill)
    for key, val in (("Radius Bottom", r_bottom), ("Radius Top", r_top),
                     ("Depth", depth)):
        _wire(tree, val, sock(n, key))
    return n


def _cyl(tree, loc, radius, depth, vertices=24, fill=2):
    n = safe_node(tree, "GeometryNodeMeshCylinder", loc)
    if n is None:
        return None
    try:
        n.inputs["Vertices"].default_value = vertices
        n.inputs["Side Segments"].default_value = 1
        n.inputs["Fill Segments"].default_value = 1
    except Exception:
        pass
    _set_fill(n, fill)
    for key, val in (("Radius", radius), ("Depth", depth)):
        _wire(tree, val, sock(n, key))
    return n


def _line(tree, loc, count_sock=None, start=None, offset=None):
    """Mesh Line used as a rank: Count points, stepped by `offset`.

    MEASURED (Saved/Audit/gn_primitive_sockets.py): 5.2's MeshLine has NO
    `End Location` socket in either mode. Inputs are
    ['Count', 'Resolution', 'Start Location', 'Offset'], and `Offset` defaults
    to (0, 0, 1) — ONE METRE. Writing an end vector was therefore a silent
    no-op on every rank in this module, leaving each instance spaced 1 m apart
    (a 24-bowl rank measured 23.5 m and the gate failed on diagonal).

    The rank spacing this module wants is `span / (count - 1)`, i.e. the
    per-step offset — the caller passes a per-step vector, not an end point.
    """
    n = safe_node(tree, "GeometryNodeMeshLine", loc)
    if n is None:
        return None, None
    _wire(tree, count_sock, sock(n, "Count"))
    if sock(n, "Start Location") is not None:
        _wire(tree, start, sock(n, "Start Location"))
    _wire(tree, offset, sock(n, "Offset"))
    return n, n.outputs["Mesh"]


def _xf(tree, loc, geometry, rotation=None, translation=None, scale=None):
    n = safe_node(tree, "GeometryNodeTransform", loc)
    if n is None:
        return geometry
    link_sockets(tree, geometry, n.inputs["Geometry"])
    for key, val in (("Rotation", rotation), ("Translation", translation),
                     ("Scale", scale)):
        if val is not None:
            _wire(tree, val, n.inputs.get(key))
    return n


# ---------------------------------------------------------------------------
# MEL_music_bandoneon — concert accordion. Lead group: Loft Splines
# ---------------------------------------------------------------------------

def build_music_bandoneon(group_name="MEL_music_bandoneon"):
    """Concert bandoneon: lofted bellows skin pleated into a stack, two
    keyboard/grille boxes, a 6x12 button board, shoulder + hand strap rails.

    Lead: `Loft Splines` lofts the two bellows edge profiles into the pleat
    face, and rotated copies of that face ARE the bellows — the loft is the
    accordion fold, not a decoration on one.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_bandoneon"

    add_float_param(tree, "Box Width M", 0.46, 0.25, 0.9)
    add_float_param(tree, "Box Height M", 0.40, 0.2, 0.8)
    add_float_param(tree, "Box Depth M", 0.13, 0.06, 0.3)
    add_float_param(tree, "Bellows Pleats", 16, 4, 34)
    add_float_param(tree, "Bellows Depth M", 0.26, 0.08, 0.6)
    add_int_param(tree, "Button Rows", 6, 3, 8)
    add_int_param(tree, "Buttons Per Row", 12, 6, 18)
    add_float_param(tree, "Button Radius M", 0.0075, 0.003, 0.016)
    add_bool_param(tree, "Realize for export", False)

    bx, by = 0, 0
    half_h = _math(tree, "MULTIPLY", (bx - 1760, by + 140), gin.outputs["Box Height M"], 0.5)
    half_w = _math(tree, "MULTIPLY", (bx - 1760, by - 40), gin.outputs["Box Width M"], 0.5)
    # The bellows runs along X between the boxes, so its cross-section is
    # depth (Y) x height (Z). pleat face = a thin plate in that cross-section,
    # stacked along X.
    pleat_d = gin.outputs["Box Depth M"]
    pleat_h = _math(tree, "MULTIPLY", (bx - 1760, by - 340), half_h.outputs[0], 1.62)

    # --- bellows edge profiles: two lines along Y, top and bottom of the
    #     cross-section. Loft Splines lofts between them into the pleat face.
    prof_top, prof_top_sock = _line(tree, (bx - 1400, by + 320),
                                    offset=_combine(tree, (bx - 1580, by + 380),
                                                    0.0, pleat_d, pleat_h.outputs[0]))
    prof_bot, prof_bot_sock = _line(tree, (bx - 1400, by - 60),
                                    offset=_combine(tree, (bx - 1580, by - 20),
                                                    0.0, pleat_d,
                                                    _math(tree, "MULTIPLY", (bx - 1580, by - 180),
                                                          half_h.outputs[0], -1.62
                                                          ).outputs[0]))

    loft, used_loft = _lead(
        BID, tree, "Loft Splines", (bx - 1160, by + 160),
        fallback_type="GeometryNodeMeshCube",
        inputs={"Resample Splines": True, "Resolution/Resample Count": 16,
                "Loft Subdivide": 2, "Cyclic Splines": False, "Cyclic Loft": False},
    )
    if loft is None or used_loft:
        face = safe_node(tree, "GeometryNodeMeshCube", (bx - 1160, by + 160))
        fv = _combine(tree, (bx - 1340, by + 160), 0.004, pleat_d, pleat_h.outputs[0])
        link_sockets(tree, fv.outputs["Vector"], face.inputs["Size"])
        pleat_face = face.outputs["Mesh"]
    else:
        link_sockets(tree, prof_top_sock, loft.inputs["Curves"])
        link_sockets(tree, prof_bot_sock, loft.inputs["Curves"])
        pleat_face = loft.outputs["Mesh"]

    # --- pleat stack: the same face along X, each one tilted ---------------
    pcount = safe_node(tree, "FunctionNodeFloatToInt", (bx - 1400, by - 380))
    link_sockets(tree, gin.outputs["Bellows Pleats"], pcount.inputs[0])
    pleat_span = _math(tree, "MULTIPLY", (bx - 1580, by - 520),
                       gin.outputs["Bellows Depth M"], 1.0)
    pstep = _math(tree, "DIVIDE", (bx - 1560, by - 700), pleat_span.outputs[0],
                  _math(tree, "SUBTRACT", (bx - 1560, by - 780), pcount.outputs[0], 1.0).outputs[0])
    pline, pline_sock = _line(tree, (bx - 1160, by - 380),
                              count_sock=pcount.outputs[0],
                              start=_combine(tree, (bx - 1340, by - 520),
                                             _math(tree, "MULTIPLY", (bx - 1560, by - 620),
                                                   pleat_span.outputs[0], -0.5).outputs[0],
                                             0.0, 0.0),
                              offset=_combine(tree, (bx - 1340, by - 380),
                                              pstep.outputs[0], 0.0, 0.0))
    ppts = safe_node(tree, "GeometryNodeMeshToPoints", (bx - 980, by - 380))
    link_sockets(tree, pline_sock, sock(ppts, "Mesh") or ppts.inputs[0])

    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 800, by - 620))
    piv = _math(tree, "DIVIDE", (bx - 620, by - 620), idx.outputs["Index"], 34.0)
    srot = safe_node(tree, "FunctionNodeEulerToRotation", (bx - 460, by - 620))
    link_sockets(tree, piv.outputs[0], srot.inputs[0])

    pleats = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 140, by - 240))
    link_sockets(tree, ppts.outputs["Points"], sock(pleats, "Points"))
    link_sockets(tree, pleat_face, sock(pleats, "Instance"))
    rot_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 60, by - 240))
    link_sockets(tree, pleats.outputs["Instances"], sock(rot_inst, "Points"))
    link_sockets(tree, pleat_face, sock(rot_inst, "Instance"))
    if sock(rot_inst, "Rotation") is not None:
        link_sockets(tree, srot.outputs["Rotation"], sock(rot_inst, "Rotation"))

    # --- the two end boxes, seated at the bellows ends --------------------
    box_parts = []
    for i, sign in enumerate((-1.0, 1.0)):
        cube = safe_node(tree, "GeometryNodeMeshCube", (bx - 620, by - 860 - i * 200))
        sv = _combine(tree, (bx - 820, by - 860 - i * 200),
                      gin.outputs["Box Width M"], gin.outputs["Box Height M"],
                      gin.outputs["Box Depth M"])
        link_sockets(tree, sv.outputs["Vector"], cube.inputs["Size"])
        off = _math(tree, "ADD", (bx - 820, by - 1000 - i * 200),
                    _math(tree, "MULTIPLY", (bx - 1000, by - 1060 - i * 200),
                          half_w.outputs[0], sign).outputs[0],
                    _math(tree, "MULTIPLY", (bx - 1000, by - 1140 - i * 200),
                          pleat_span.outputs[0], 0.5).outputs[0])
        pos = _combine(tree, (bx - 500, by - 1000 - i * 200), off.outputs[0], 0.0, 0.0)
        box_parts.append(_xf(tree, (bx - 300, by - 860 - i * 200),
                             cube.outputs["Mesh"], translation=pos).outputs["Geometry"])

    # --- button board on the treble (right-hand) box -----------------------
    brow = safe_node(tree, "GeometryNodeMeshGrid", (bx - 620, by + 700))
    brow_off = _math(tree, "ADD", (bx - 1000, by + 620),
                     _math(tree, "MULTIPLY", (bx - 1180, by + 680),
                           half_w.outputs[0], 1.0).outputs[0],
                     _math(tree, "MULTIPLY", (bx - 1180, by + 560),
                           pleat_span.outputs[0], 0.5).outputs[0])
    for key, val in (
        ("Vertices X", gin.outputs["Buttons Per Row"]),
        ("Vertices Y", gin.outputs["Button Rows"]),
        ("Size X", _math(tree, "MULTIPLY", (bx - 1000, by + 860),
                         half_w.outputs[0], 1.6).outputs[0]),
        ("Size Y", _math(tree, "MULTIPLY", (bx - 1000, by + 740),
                         half_h.outputs[0], 1.4).outputs[0]),
    ):
        _wire(tree, val, sock(brow, key))
    bpos = _combine(tree, (bx - 800, by + 620), brow_off.outputs[0],
                    0.0, 0.0)
    bxf = _xf(tree, (bx - 420, by + 700), brow.outputs["Mesh"],
              translation=_combine(tree, (bx - 800, by + 620), brow_off.outputs[0],
                                   0.0,
                                   _math(tree, "MULTIPLY", (bx - 1000, by + 480),
                                         half_h.outputs[0], 1.02).outputs[0]))
    btn = _cyl(tree, (bx - 200, by + 900), gin.outputs["Button Radius M"],
               _math(tree, "MULTIPLY", (bx - 420, by + 1020),
                     gin.outputs["Button Radius M"], 1.3).outputs[0], vertices=12)
    btn_r = _xf(tree, (bx - 20, by + 900), btn.outputs["Mesh"],
                rotation=(math.radians(90), 0, 0))
    kinst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 200, by + 700))
    link_sockets(tree, bxf.outputs["Geometry"], sock(kinst, "Points"))
    link_sockets(tree, btn_r.outputs["Geometry"], sock(kinst, "Instance"))

    body = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 460, by))
    for s in (rot_inst.outputs["Instances"], kinst.outputs["Instances"], *box_parts):
        link_sockets(tree, s, body.inputs["Geometry"])

    bidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 460, by - 300))
    bmod = _math(tree, "FLOORMOD", (bx + 460, by - 400), bidx.outputs["Index"], 12.0)
    stored = _store_named(tree, (bx + 700, by - 200), body.outputs["Geometry"],
                          "button_semitone_mod12", bmod.outputs[0])
    stored = _store_named(tree, (bx + 880, by - 200), stored, "higgsas_lead",
                          0.0 if used_loft else 1.0)
    _export_tail(tree, gin, gout, stored, (bx + 1060, by))

    return label_tree(tree, group_name, [
        {"title": "Bellows Loft", "nodes": ("prof", "loft"), "role": "curve"},
        {"title": "Pleat Stack", "nodes": ("pline", "rot_inst"), "role": "instance"},
        {"title": "Boxes+Buttons", "nodes": ("cube", "brow", "btn"), "role": "geometry"},
        {"title": "Export", "nodes": ("realize", "switch", "shade"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_saxophone — lead group: Bend (+ Taper)
# ---------------------------------------------------------------------------

def build_music_saxophone(group_name="MEL_music_saxophone"):
    """Tenor saxophone: mouthpiece, bent crook, tapered conical bore, upturned
    bell, 6 key cups.

    Lead: `Taper` sets the conical bore (a Transform scale would also taper,
    but Taper is the authored cone law and keeps Limits explicit), then `Bend`
    curls the crook out of the body axis — a native Transform cannot bend a
    curve, so this is the one place the library is load-bearing.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_saxophone"

    add_float_param(tree, "Body Length M", 0.72, 0.35, 1.2)
    add_float_param(tree, "Body Radius M", 0.031, 0.012, 0.06)
    add_float_param(tree, "Bell Radius M", 0.115, 0.05, 0.2)
    add_float_param(tree, "Neck Bend Deg", 62.0, 20.0, 120.0)
    add_int_param(tree, "Key Count", 6, 3, 12)
    add_float_param(tree, "Key Cup Radius M", 0.026, 0.01, 0.05)
    add_bool_param(tree, "Realize for export", False)

    bx, by = 0, 0
    bend_rad = _math(tree, "MULTIPLY", (bx - 1180, by + 200),
                     gin.outputs["Neck Bend Deg"], 0.0174533)

    body = _cone(tree, (bx - 1000, by), gin.outputs["Body Radius M"],
                 _math(tree, "MULTIPLY", (bx - 1180, by - 120),
                       gin.outputs["Body Radius M"], 2.4).outputs[0],
                 gin.outputs["Body Length M"])

    taper, used_taper = _lead(
        BID, tree, "Taper", (bx - 740, by),
        fallback_type="GeometryNodeTransform",
        inputs={"Upper Factor": 1.0, "Lower Factor": 1.0, "Axis": (0.0, 0.0, 1.0),
                "Squish": 1.0, "Center": (0.0, 0.0, 0.36), "Smooth Limits": True},
    )
    if taper is not None and not used_taper:
        link_sockets(tree, body.outputs["Mesh"], taper.inputs["Geometry"])
        bore = taper.outputs["Geometry"]
    else:
        bore = _xf(tree, (bx - 740, by), body.outputs["Mesh"],
                   scale=(1.0, 1.0, 1.0)).outputs["Geometry"]

    bend, used_bend = _lead(
        BID, tree, "Bend", (bx - 500, by + 120),
        fallback_type="GeometryNodeTransform",
        inputs={"Angle": bend_rad.outputs[0], "Axis": (1.0, 0.0, 0.0),
                "Center": (0.0, 0.0, 0.0), "Limits Lower": 0.55,
                "Limits Upper": 1.0},
    )
    if bend is not None and not used_bend:
        link_sockets(tree, bore, bend.inputs["Geometry"])
        neck = bend.outputs["Geometry"]
    else:
        # Native fallback: no curve bend available, so the crook is a separate
        # rotated cylinder. Reported as a fallback, not dressed up as one.
        neck = bore

    crook = _cyl(tree, (bx - 260, by + 340),
                 _math(tree, "MULTIPLY", (bx - 500, by + 460),
                       gin.outputs["Body Radius M"], 1.15).outputs[0],
                 _math(tree, "MULTIPLY", (bx - 500, by + 340),
                       gin.outputs["Body Length M"], 0.30).outputs[0], vertices=20)
    crook_geo = _xf(tree, (bx - 80, by + 340), crook.outputs["Mesh"],
                    rotation=(math.radians(-64), 0, 0),
                    translation=(0.0, 0.0,
                                 _math(tree, "MULTIPLY", (bx - 500, by + 220),
                                       gin.outputs["Body Length M"], 1.02).outputs[0]
                                 )).outputs["Geometry"]

    # --- bell --------------------------------------------------------------
    bell = _cone(tree, (bx - 500, by - 700),
                 _math(tree, "MULTIPLY", (bx - 700, by - 620),
                       gin.outputs["Body Radius M"], 2.2).outputs[0],
                 gin.outputs["Bell Radius M"],
                 _math(tree, "MULTIPLY", (bx - 700, by - 800),
                       gin.outputs["Body Length M"], 0.20).outputs[0])
    bell_geo = _xf(tree, (bx - 260, by - 700), bell.outputs["Mesh"],
                   rotation=(math.radians(18), 0, 0),
                   translation=(0.0, 0.0,
                                _math(tree, "MULTIPLY", (bx - 700, by - 960),
                                      gin.outputs["Body Length M"], 0.94).outputs[0]
                                )).outputs["Geometry"]

    # --- key cups: a rake of points in front of the bell-side of the body --
    kcount = safe_node(tree, "FunctionNodeFloatToInt", (bx - 460, by + 980))
    link_sockets(tree, gin.outputs["Key Count"], kcount.inputs[0])
    kspan = _math(tree, "MULTIPLY", (bx - 460, by + 800), gin.outputs["Body Length M"], 0.72)
    kline, kline_sock = _line(tree, (bx - 260, by + 900),
                              count_sock=kcount.outputs[0],
                              offset=_combine(tree, (bx - 460, by + 800), 0.0, 0.0,
                                              _math(tree, "DIVIDE", (bx - 660, by + 620),
                                                    kspan.outputs[0],
                                                    _math(tree, "SUBTRACT", (bx - 660, by + 540),
                                                          kcount.outputs[0], 1.0).outputs[0]
                                                    ).outputs[0]))
    kpts = safe_node(tree, "GeometryNodeMeshToPoints", (bx - 80, by + 900))
    link_sockets(tree, kline_sock, sock(kpts, "Mesh") or kpts.inputs[0])
    krad = _math(tree, "MULTIPLY", (bx - 460, by + 700), gin.outputs["Body Radius M"], 1.9)
    kpts2 = _xf(tree, (bx + 100, by + 900), kpts.outputs["Points"],
                translation=_combine(tree, (bx - 240, by + 700),
                                     krad.outputs[0], 0.0, 0.0)).outputs["Geometry"]
    cup = _cyl(tree, (bx + 280, by + 1120), gin.outputs["Key Cup Radius M"],
               _math(tree, "MULTIPLY", (bx + 60, by + 1240),
                     gin.outputs["Key Cup Radius M"], 1.1).outputs[0], vertices=20)
    cup_geo = _xf(tree, (bx + 460, by + 1120), cup.outputs["Mesh"],
                  rotation=(0.0, math.radians(90), 0.0)).outputs["Geometry"]
    kinst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 660, by + 900))
    link_sockets(tree, kpts2, sock(kinst, "Points"))
    link_sockets(tree, cup_geo, sock(kinst, "Instance"))

    # --- mouthpiece --------------------------------------------------------
    mp = _cone(tree, (bx - 260, by - 1300),
               _math(tree, "MULTIPLY", (bx - 500, by - 1220),
                     gin.outputs["Body Radius M"], 0.55).outputs[0],
               _math(tree, "MULTIPLY", (bx - 500, by - 1400),
                     gin.outputs["Body Radius M"], 1.1).outputs[0],
               _math(tree, "MULTIPLY", (bx - 500, by - 1560),
                     gin.outputs["Body Length M"], 0.11).outputs[0], vertices=20)
    mp_geo = _xf(tree, (bx - 80, by - 1300), mp.outputs["Mesh"],
                 rotation=(math.radians(-64), 0, 0),
                 translation=(0.0, 0.0,
                              _math(tree, "MULTIPLY", (bx - 500, by - 1720),
                                    gin.outputs["Body Length M"], 1.24).outputs[0]
                              )).outputs["Geometry"]

    body_j = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 920, by - 200))
    for s in (bore, crook_geo, bell_geo, kinst.outputs["Instances"], mp_geo):
        link_sockets(tree, s, body_j.inputs["Geometry"])

    kidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 920, by - 440))
    kmod = _math(tree, "FLOORMOD", (bx + 920, by - 560), kidx.outputs["Index"], 12.0)
    stored = _store_named(tree, (bx + 1140, by - 340), body_j.outputs["Geometry"],
                          "key_semitone_mod12", kmod.outputs[0])
    stored = _store_named(tree, (bx + 1300, by - 340), stored, "higgsas_lead",
                          0.0 if (used_bend or used_taper) else 1.0)
    _export_tail(tree, gin, gout, stored, (bx + 1480, by - 200))

    return label_tree(tree, group_name, [
        {"title": "Bore", "nodes": ("cone", "taper"), "role": "geometry"},
        {"title": "Crook+Bell", "nodes": ("bend", "bell"), "role": "curve"},
        {"title": "Keys+Mouthpiece", "nodes": ("cup", "mp"), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "switch", "shade"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_glass_harmonica — lead group: Spherical Spiral
# ---------------------------------------------------------------------------

def build_music_glass_harmonica(group_name="MEL_music_glass_harmonica"):
    """Franklin's glass armonica: spindle, 24 chromatically-tuned bowls on a
    rake, sustain wheel, bow.

    Lead: `Spherical Spiral` draws the bowl's rim coil — a tuned glass bowl is
    defined by its RIM, and the rim is a swept spiral path. Then `Bezier
    Resample` evens the spiral's density before the tube sweep, which is
    exactly what that group is for.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_glass_harmonica"

    add_int_param(tree, "Bowl Count", 24, 8, 36)
    add_float_param(tree, "Bowl Radius M", 0.075, 0.03, 0.15)
    add_float_param(tree, "Bowl Depth M", 0.070, 0.02, 0.18)
    add_float_param(tree, "Spindle Length M", 0.92, 0.4, 1.6)
    add_float_param(tree, "Rim Tube M", 0.0035, 0.001, 0.008)
    add_bool_param(tree, "Realize for export", False)

    bx, by = 0, 0

    spiral, used_spiral = _lead(
        BID, tree, "Spherical Spiral", (bx - 1100, by + 260),
        fallback_type="GeometryNodeCurvePrimitiveCircle",
        inputs={"Resolution": 128, "Radius": gin.outputs["Bowl Radius M"],
                "Min Parameter": 0.0, "Max Parameter": 1.0},
    )
    if spiral is not None and not used_spiral and sock(spiral, "Rotations") is not None:
        link_sockets(tree, _math(tree, "MULTIPLY", (bx - 1280, by + 400),
                                 gin.outputs["Bowl Count"], 0.0).outputs[0],
                     sock(spiral, "Rotations"))
    rim_curve = spiral.outputs["Curve"] if (spiral is not None and not used_spiral) else None
    if rim_curve is None:
        cc = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 1100, by + 260))
        try:
            cc.inputs["Resolution"].default_value = 64
        except Exception:
            pass
        link_sockets(tree, gin.outputs["Bowl Radius M"], sock(cc, "Radius"))
        rim_curve = cc.outputs["Curve"]

    resample, used_resample = _lead(
        BID, tree, "Bezier Resample", (bx - 840, by + 260),
        fallback_type="GeometryNodeResampleCurve",
        inputs={"Length": _math(tree, "MULTIPLY", (bx - 1060, by + 440),
                                 gin.outputs["Rim Tube M"], 30.0).outputs[0]},
    )
    if resample is not None and not used_resample:
        link_sockets(tree, rim_curve, resample.inputs["Curve"])
        rim_curve = resample.outputs["Curve"]
    else:
        rs = safe_node(tree, "GeometryNodeResampleCurve", (bx - 840, by + 260))
        link_sockets(tree, rim_curve, sock(rs, "Curve") or rs.inputs[0])

    prof = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 640, by + 80))
    try:
        prof.inputs["Resolution"].default_value = 8
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Rim Tube M"], sock(prof, "Radius"))
    sweep = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 440, by + 260))
    link_sockets(tree, rim_curve, sock(sweep, "Curve") or sweep.inputs[0])
    link_sockets(tree, prof.outputs["Curve"], sock(sweep, "Profile Curve"))

    bowl = _cone(tree, (bx - 440, by - 60), gin.outputs["Bowl Radius M"],
                 _math(tree, "MULTIPLY", (bx - 640, by - 200),
                       gin.outputs["Bowl Radius M"], 0.52).outputs[0],
                 gin.outputs["Bowl Depth M"], fill=3)
    bowl_j = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 200, by + 120))
    link_sockets(tree, bowl.outputs["Mesh"], bowl_j.inputs["Geometry"])
    link_sockets(tree, sweep.outputs["Mesh"], bowl_j.inputs["Geometry"])

    # --- the rank of bowls on the spindle ---------------------------------
    acount = safe_node(tree, "FunctionNodeFloatToInt", (bx - 820, by - 620))
    link_sockets(tree, gin.outputs["Bowl Count"], acount.inputs[0])
    aspan = _math(tree, "MULTIPLY", (bx - 820, by - 780), gin.outputs["Spindle Length M"], 0.94)
    aline, aline_sock = _line(tree, (bx - 620, by - 620), count_sock=acount.outputs[0],
                              offset=_combine(tree, (bx - 820, by - 780), 0.0, 0.0,
                                              _math(tree, "DIVIDE", (bx - 1020, by - 900),
                                                    aspan.outputs[0],
                                                    _math(tree, "SUBTRACT", (bx - 1020, by - 980),
                                                          acount.outputs[0], 1.0).outputs[0]
                                                    ).outputs[0]))
    apts = safe_node(tree, "GeometryNodeMeshToPoints", (bx - 420, by - 620))
    link_sockets(tree, aline_sock, sock(apts, "Mesh") or apts.inputs[0])
    ainst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 40, by - 400))
    link_sockets(tree, apts.outputs["Points"], sock(ainst, "Points"))
    link_sockets(tree, bowl_j.outputs["Geometry"], sock(ainst, "Instance"))

    spindle = _cyl(tree, (bx - 620, by - 900), 0.010, gin.outputs["Spindle Length M"],
                   vertices=16)
    spindle_geo = spindle.outputs["Mesh"]
    wheel = _cyl(tree, (bx - 620, by - 1180), 0.16, 0.022, vertices=48)
    wheel_geo = _xf(tree, (bx - 380, by - 1180), wheel.outputs["Mesh"],
                    rotation=(0.0, math.radians(90), 0.0),
                    translation=(0.0, 0.0,
                                 _math(tree, "MULTIPLY", (bx - 820, by - 1340),
                                       gin.outputs["Spindle Length M"], 0.96).outputs[0]
                                 )).outputs["Geometry"]
    base = safe_node(tree, "GeometryNodeMeshCube", (bx - 620, by - 1420))
    bv = _combine(tree, (bx - 820, by - 1420), 0.42, 0.24,
                  _math(tree, "MULTIPLY", (bx - 820, by - 1560),
                        gin.outputs["Spindle Length M"], 0.08).outputs[0])
    link_sockets(tree, bv.outputs["Vector"], base.inputs["Size"])
    base_geo = base.outputs["Mesh"]

    body = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 320, by - 400))
    for s in (ainst.outputs["Instances"], spindle_geo, wheel_geo, base_geo):
        link_sockets(tree, s, body.inputs["Geometry"])

    bidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 320, by - 640))
    bmod = _math(tree, "FLOORMOD", (bx + 320, by - 760), bidx.outputs["Index"], 12.0)
    stored = _store_named(tree, (bx + 540, by - 560), body.outputs["Geometry"],
                          "bowl_semitone_mod12", bmod.outputs[0])
    stored = _store_named(tree, (bx + 720, by - 560), stored, "higgsas_lead",
                          0.0 if (used_spiral or used_resample) else 1.0)
    _export_tail(tree, gin, gout, stored, (bx + 900, by - 400))

    return label_tree(tree, group_name, [
        {"title": "Bowl Rim", "nodes": ("spiral", "resample"), "role": "curve"},
        {"title": "Rank", "nodes": ("aline", "ainst"), "role": "instance"},
        {"title": "Frame", "nodes": ("spindle", "wheel", "base"), "role": "geometry"},
        {"title": "Export", "nodes": ("realize", "switch", "shade"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_music_box — lead group: Spur Gear
# ---------------------------------------------------------------------------

def build_music_music_box(group_name="MEL_music_music_box"):
    """Cylinder music box: pinned barrel, governor gear train, steel comb,
    spring barrel and winding key.

    Lead: `Spur Gear` cuts the governor pinion and the barrel drive gear —
    real involute-ish teeth, which no native node produces. Native fallback is
    a plain cylinder, reported as a fallback.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_music_box"

    add_float_param(tree, "Barrel Length M", 0.26, 0.08, 0.6)
    add_float_param(tree, "Barrel Radius M", 0.052, 0.02, 0.12)
    add_int_param(tree, "Pin Rows", 6, 2, 14)
    add_int_param(tree, "Pins Per Row", 20, 6, 40)
    add_float_param(tree, "Pin Radius M", 0.0022, 0.0008, 0.006)
    add_int_param(tree, "Comb Teeth", 24, 8, 48)
    add_int_param(tree, "Governor Teeth", 14, 6, 40)
    add_bool_param(tree, "Realize for export", False)

    bx, by = 0, 0

    # --- governor + drive gears -------------------------------------------
    # Spur Gear diameter is Module x Teeth (measured: module 0.0065 x 14 teeth
    # -> 0.104 m across), so the governor pinion is sized from Barrel Radius,
    # not from a guess.
    gear_module = _math(tree, "DIVIDE", (bx - 1300, by + 420),
                        gin.outputs["Barrel Radius M"], 8.0)
    gear, used_gear = _lead(
        BID, tree, "Spur Gear", (bx - 1060, by + 420),
        fallback_type="GeometryNodeMeshCylinder",
        inputs={
            "Teeth": gin.outputs["Governor Teeth"],
            "Module": gear_module.outputs[0],
            "Pressure Angle": 0.3491,
            "Height": _math(tree, "MULTIPLY", (bx - 1300, by + 300),
                            gin.outputs["Barrel Radius M"], 0.22).outputs[0],
            "Side Segments": 1,
            "Fillet Resolution": 2,
        },
    )
    gear_at = _combine(tree, (bx - 860, by + 560),
                       _math(tree, "MULTIPLY", (bx - 1300, by + 620),
                             gin.outputs["Barrel Length M"], 0.34).outputs[0],
                       0.0, 0.0)
    if gear is not None and not used_gear:
        gear_geo = gear.outputs["Mesh Gear"]
        gear_xf = _xf(tree, (bx - 700, by + 420), gear_geo,
                      rotation=(0.0, math.radians(90), 0.0),
                      translation=gear_at).outputs["Geometry"]
    else:
        gcyl = _cyl(tree, (bx - 700, by + 420),
                    _math(tree, "MULTIPLY", (bx - 1060, by + 300),
                          gin.outputs["Barrel Radius M"], 0.22).outputs[0],
                    _math(tree, "MULTIPLY", (bx - 1060, by + 560),
                          gin.outputs["Barrel Radius M"], 0.10).outputs[0],
                    vertices=32)
        gear_xf = _xf(tree, (bx - 700, by + 420), gcyl.outputs["Mesh"],
                      rotation=(0.0, math.radians(90), 0.0),
                      translation=gear_at).outputs["Geometry"]

    # --- pinned barrel -----------------------------------------------------
    barrel = _cyl(tree, (bx - 900, by), gin.outputs["Barrel Radius M"],
                  gin.outputs["Barrel Length M"], vertices=48, fill=0)
    rows = []
    for i in range(1):
        pincount = safe_node(tree, "FunctionNodeFloatToInt", (bx - 1320, by - 420 - i * 200))
        link_sockets(tree, gin.outputs["Pins Per Row"], pincount.inputs[0])
        span = _math(tree, "MULTIPLY", (bx - 1320, by - 560 - i * 200),
                     gin.outputs["Barrel Length M"], 0.94)
        line, line_sock = _line(tree, (bx - 1120, by - 420 - i * 200),
                                count_sock=pincount.outputs[0],
                                offset=_combine(tree, (bx - 1320, by - 560 - i * 200),
                                                0.0, 0.0,
                                                _math(tree, "DIVIDE", (bx - 1520, by - 640 - i * 200),
                                                      span.outputs[0],
                                                      _math(tree, "SUBTRACT", (bx - 1520, by - 720 - i * 200),
                                                            pincount.outputs[0], 1.0).outputs[0]
                                                      ).outputs[0]))
        pts = safe_node(tree, "GeometryNodeMeshToPoints", (bx - 940, by - 420 - i * 200))
        link_sockets(tree, line_sock, sock(pts, "Mesh") or pts.inputs[0])
        # ride the barrel surface: pins point radially outward
        rad = _math(tree, "ADD", (bx - 1320, by - 700 - i * 200),
                    gin.outputs["Barrel Radius M"],
                    _math(tree, "MULTIPLY", (bx - 1500, by - 700 - i * 200),
                          gin.outputs["Barrel Radius M"], 0.06).outputs[0])
        placed = _xf(tree, (bx - 760, by - 420 - i * 200), pts.outputs["Points"],
                     translation=_combine(tree, (bx - 1000, by - 700 - i * 200),
                                          rad.outputs[0], 0.0, 0.0)).outputs["Geometry"]
        pin = _cyl(tree, (bx - 700, by - 260 - i * 200), gin.outputs["Pin Radius M"],
                   _math(tree, "MULTIPLY", (bx - 940, by - 260 - i * 200),
                         gin.outputs["Barrel Radius M"], 0.22).outputs[0], vertices=8)
        pin_geo = _xf(tree, (bx - 520, by - 260 - i * 200), pin.outputs["Mesh"],
                      rotation=(0.0, math.radians(90), 0.0)).outputs["Geometry"]
        inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 340, by - 420 - i * 200))
        link_sockets(tree, placed, sock(inst, "Points"))
        link_sockets(tree, pin_geo, sock(inst, "Instance"))
        rows.append(inst.outputs["Instances"])

    # --- steel comb --------------------------------------------------------
    # The comb runs along the barrel's axis (Z), not X. Teeth are placed at
    # Y = 3.6*R (above the barrel surface) and Z varies along the barrel length.
    toothcount = safe_node(tree, "FunctionNodeFloatToInt", (bx - 1100, by - 1100))
    link_sockets(tree, gin.outputs["Comb Teeth"], toothcount.inputs[0])
    tspan = _math(tree, "MULTIPLY", (bx - 1100, by - 1240), gin.outputs["Barrel Length M"], 1.06)
    # Step in Z (barrel axis), not X
    tline, tline_sock = _line(tree, (bx - 900, by - 1100), count_sock=toothcount.outputs[0],
                               offset=_combine(tree, (bx - 1100, by - 1240),
                                               0.0, 0.0,
                                               _math(tree, "DIVIDE", (bx - 1300, by - 1320),
                                                     tspan.outputs[0],
                                                     _math(tree, "SUBTRACT", (bx - 1300, by - 1400),
                                                           toothcount.outputs[0], 1.0).outputs[0]
                                                     ).outputs[0]))
    tpts = safe_node(tree, "GeometryNodeMeshToPoints", (bx - 720, by - 1100))
    link_sockets(tree, tline_sock, sock(tpts, "Mesh") or tpts.inputs[0])
    tooth = safe_node(tree, "GeometryNodeMeshCube", (bx - 520, by - 1240))
    tv = _combine(tree, (bx - 700, by - 1240),
                  _math(tree, "DIVIDE", (bx - 900, by - 1380),
                        gin.outputs["Barrel Length M"], 26.0).outputs[0],
                  _math(tree, "MULTIPLY", (bx - 900, by - 1520),
                        gin.outputs["Barrel Radius M"], 3.4).outputs[0],
                  _math(tree, "MULTIPLY", (bx - 900, by - 1660),
                        gin.outputs["Barrel Radius M"], 0.16).outputs[0])
    link_sockets(tree, tv.outputs["Vector"], tooth.inputs["Size"])
    # Place teeth at barrel center in X, above barrel in Y, Z varies along barrel
    tpos = _combine(tree, (bx - 700, by - 1100),
                    0.0,
                    _math(tree, "MULTIPLY", (bx - 1100, by - 1000),
                          gin.outputs["Barrel Radius M"], 3.6).outputs[0],
                    0.0)
    tooth_geo = _xf(tree, (bx - 340, by - 1240), tooth.outputs["Mesh"],
                    translation=tpos).outputs["Geometry"]
    tinst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 160, by - 1100))
    link_sockets(tree, tpts.outputs["Points"], sock(tinst, "Points"))
    link_sockets(tree, tooth_geo, sock(tinst, "Instance"))

    # --- case, spring barrel, winding key ---------------------------------
    # The case is sized off the barrel it encloses (1.25 x 8R x 7R covers the
    # barrel plus the comb teeth at 3.6R in Y), not off a fixed guess: at the
    # earlier 1.9/9.0/8.0 multipliers the box measured 0.49 x 0.47 x 0.42 m
    # for a 0.26 m barrel and the gate rejected the diagonal.
    case = safe_node(tree, "GeometryNodeMeshCube", (bx - 520, by - 1600))
    cv = _combine(tree, (bx - 720, by - 1600),
                  _math(tree, "MULTIPLY", (bx - 940, by - 1600),
                        gin.outputs["Barrel Length M"], 1.25).outputs[0],
                  _math(tree, "MULTIPLY", (bx - 940, by - 1740),
                        gin.outputs["Barrel Radius M"], 8.0).outputs[0],
                  _math(tree, "MULTIPLY", (bx - 940, by - 1880),
                        gin.outputs["Barrel Radius M"], 7.0).outputs[0])
    link_sockets(tree, cv.outputs["Vector"], case.inputs["Size"])
    case_geo = _xf(tree, (bx - 300, by - 1600), case.outputs["Mesh"],
                   translation=_combine(tree, (bx - 500, by - 1740), 0.0,
                                        _math(tree, "MULTIPLY", (bx - 720, by - 1600),
                                              gin.outputs["Barrel Radius M"], 1.4).outputs[0],
                                        0.0)).outputs["Geometry"]
    spring = _cyl(tree, (bx - 520, by + 700),
                  _math(tree, "MULTIPLY", (bx - 720, by + 700),
                        gin.outputs["Barrel Radius M"], 0.85).outputs[0],
                  _math(tree, "MULTIPLY", (bx - 720, by + 560),
                        gin.outputs["Barrel Length M"], 0.42).outputs[0], vertices=32)
    spring_x = _math(tree, "MULTIPLY", (bx - 720, by + 860),
                      gin.outputs["Barrel Length M"], -0.72)
    spring_geo = _xf(tree, (bx - 300, by + 700), spring.outputs["Mesh"],
                     rotation=(0.0, math.radians(90), 0.0),
                     translation=_combine(tree, (bx - 500, by + 860),
                                          spring_x.outputs[0], 0.0, 0.0)
                     ).outputs["Geometry"]
    keybar = _cyl(tree, (bx - 520, by + 980), 0.004, 0.11, vertices=10)
    key_x = _math(tree, "MULTIPLY", (bx - 720, by + 840),
                  gin.outputs["Barrel Length M"], -0.95)
    key_z = _math(tree, "MULTIPLY", (bx - 720, by + 1120),
                  gin.outputs["Barrel Radius M"], 0.2)
    key_geo = _xf(tree, (bx - 300, by + 980), keybar.outputs["Mesh"],
                  rotation=(0.0, math.radians(90), 0.0),
                  translation=_combine(tree, (bx - 500, by + 840),
                                       key_x.outputs[0], 0.0, key_z.outputs[0])
                  ).outputs["Geometry"]

    body = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 80, by - 600))
    for s in (barrel.outputs["Mesh"], gear_xf, *rows, tinst.outputs["Instances"],
              case_geo, spring_geo, key_geo):
        link_sockets(tree, s, body.inputs["Geometry"])

    midx = safe_node(tree, "GeometryNodeInputIndex", (bx + 80, by - 820))
    mmod = _math(tree, "FLOORMOD", (bx + 80, by - 940), midx.outputs["Index"], 12.0)
    stored = _store_named(tree, (bx + 300, by - 740), body.outputs["Geometry"],
                          "note_semitone_mod12", mmod.outputs[0])
    stored = _store_named(tree, (bx + 480, by - 740), stored, "higgsas_lead",
                          0.0 if used_gear else 1.0)
    _export_tail(tree, gin, gout, stored, (bx + 660, by - 600))

    return label_tree(tree, group_name, [
        {"title": "Governor Gear", "nodes": ("gear",), "role": "geometry"},
        {"title": "Pinned Barrel", "nodes": ("barrel", "inst"), "role": "instance"},
        {"title": "Comb+Case", "nodes": ("tinst", "case"), "role": "geometry"},
        {"title": "Export", "nodes": ("realize", "switch", "shade"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_theremin — lead group: Lissajous Curve
# ---------------------------------------------------------------------------

def build_music_theremin(group_name="MEL_music_theremin"):
    """Theremin: cabinet, pitch antenna + pitch-reference loop, volume
    antenna + volume loop, tone-field rail, audio out.

    Lead: `Lissajous Curve` draws the pitch-reference loop and the tone-field
    trace — two frequency ratios in one plane IS the Lissajous figure, and it
    is the one geometry in this instrument that has no native equivalent.
    Native fallback: a circle primitive.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_theremin"

    add_float_param(tree, "Cabinet Width M", 0.62, 0.3, 1.1)
    add_float_param(tree, "Cabinet Height M", 0.30, 0.12, 0.6)
    add_float_param(tree, "Cabinet Depth M", 0.42, 0.2, 0.8)
    add_float_param(tree, "Antenna Height M", 0.34, 0.12, 0.7)
    add_float_param(tree, "Loop Radius M", 0.10, 0.03, 0.24)
    add_int_param(tree, "Pitch Freq X", 3, 1, 9)
    add_int_param(tree, "Pitch Freq Y", 2, 1, 9)
    add_float_param(tree, "Trace Width M", 0.006, 0.002, 0.02)
    add_bool_param(tree, "Realize for export", False)

    bx, by = 0, 0

    def _lissajous(fx, fy, x_loc, y_loc):
        """Lissajous loop at the requested radius.

        MEASURED (Saved/Audit/higgsas_group_scale_probe.py): the group's span
        is ~2x Size per axis and Z tracks Size.Z independently, so Size is the
        radius control and NO post-transform scale is applied — scaling the
        swept mesh afterwards would shrink the tube radius with it (the
        0.006 m trace wire became 0.0006 m that way, first pass).
        """
        size = _combine(tree, (x_loc - 180, y_loc - 120),
                        gin.outputs["Loop Radius M"], gin.outputs["Loop Radius M"],
                        gin.outputs["Loop Radius M"])
        n, used = _lead(
            BID, tree, "Lissajous Curve", (x_loc, y_loc),
            fallback_type="GeometryNodeCurvePrimitiveCircle",
            inputs={"Resolution": 256, "X Frequency": fx, "Y Frequency": fy,
                    "Z Frequency": 1, "Y Phase Offset": 1.5708,
                    "Z Phase Offset": 0.0, "Size": size.outputs["Vector"]},
        )
        curve = n.outputs["Curve"] if (n is not None and not used) else None
        if curve is None:
            cc = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (x_loc, y_loc))
            try:
                cc.inputs["Resolution"].default_value = 64
            except Exception:
                pass
            link_sockets(tree, gin.outputs["Loop Radius M"], sock(cc, "Radius"))
            curve = cc.outputs["Curve"]
        return curve, used

    def _tube(curve, radius_sock, x_loc, y_loc):
        prof = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (x_loc - 180, y_loc - 140))
        try:
            prof.inputs["Resolution"].default_value = 8
        except Exception:
            pass
        _wire(tree, radius_sock, sock(prof, "Radius"))
        sweep = safe_node(tree, "GeometryNodeCurveToMesh", (x_loc, y_loc))
        link_sockets(tree, curve, sock(sweep, "Curve") or sweep.inputs[0])
        link_sockets(tree, prof.outputs["Curve"], sock(sweep, "Profile Curve"))
        return sweep.outputs["Mesh"]

    pitch_curve, used_pitch = _lissajous(gin.outputs["Pitch Freq X"],
                                        gin.outputs["Pitch Freq Y"], bx - 900, by + 520)
    vol_curve, used_vol = _lissajous(5, 4, bx - 900, by - 300)
    trace_curve, used_trace = _lissajous(gin.outputs["Pitch Freq Y"],
                                         gin.outputs["Pitch Freq X"], bx - 900, by - 1200)

    # --- antennas ----------------------------------------------------------
    ant = _cyl(tree, (bx - 620, by + 900),
               _math(tree, "MULTIPLY", (bx - 900, by + 1020),
                     gin.outputs["Trace Width M"], 0.6).outputs[0],
               gin.outputs["Antenna Height M"], vertices=10)
    ant_geo = _xf(tree, (bx - 420, by + 900), ant.outputs["Mesh"],
                  translation=(_math(tree, "MULTIPLY", (bx - 900, by + 1140),
                                     gin.outputs["Cabinet Width M"], 0.22).outputs[0],
                               0.0,
                               _math(tree, "MULTIPLY", (bx - 900, by + 1260),
                                     gin.outputs["Cabinet Height M"], 0.5).outputs[0])
                  ).outputs["Geometry"]
    ant2 = _cyl(tree, (bx - 620, by + 900),
                _math(tree, "MULTIPLY", (bx - 900, by + 1020),
                      gin.outputs["Trace Width M"], 0.6).outputs[0],
                _math(tree, "MULTIPLY", (bx - 900, by + 900),
                      gin.outputs["Antenna Height M"], 0.7).outputs[0], vertices=10)
    ant2_geo = _xf(tree, (bx - 420, by + 700), ant2.outputs["Mesh"],
                   translation=(_math(tree, "MULTIPLY", (bx - 900, by + 1140),
                                      gin.outputs["Cabinet Width M"], -0.22).outputs[0],
                                0.0,
                                _math(tree, "MULTIPLY", (bx - 900, by + 1260),
                                      gin.outputs["Cabinet Height M"], 0.5).outputs[0])
                   ).outputs["Geometry"]

    # Loops carry no post-scale: the Lissajous Size dials already set the
    # radius (measured), and scaling the swept tube would shrink the wire too.
    pitch_loop = _xf(tree, (bx - 300, by + 520),
                     _tube(pitch_curve, gin.outputs["Trace Width M"], bx - 120, by + 520),
                     translation=_combine(tree, (bx - 900, by + 640),
                                          _math(tree, "MULTIPLY", (bx - 1120, by + 700),
                                                gin.outputs["Cabinet Width M"], 0.34).outputs[0],
                                          0.0,
                                          _math(tree, "MULTIPLY", (bx - 1120, by + 820),
                                                gin.outputs["Cabinet Height M"], 0.62).outputs[0])
                     ).outputs["Geometry"]
    vol_loop = _xf(tree, (bx - 300, by - 300),
                   _tube(vol_curve, gin.outputs["Trace Width M"], bx - 120, by - 300),
                   translation=_combine(tree, (bx - 900, by - 180),
                                        _math(tree, "MULTIPLY", (bx - 1120, by - 120),
                                              gin.outputs["Cabinet Width M"], -0.34).outputs[0],
                                        0.0,
                                        _math(tree, "MULTIPLY", (bx - 1120, by + 20),
                                              gin.outputs["Cabinet Height M"], 0.62).outputs[0])
                   ).outputs["Geometry"]

    # --- tone-field trace rail across the cabinet front --------------------
    rail = _tube(trace_curve, _math(tree, "MULTIPLY", (bx - 120, by - 1340),
                                     gin.outputs["Trace Width M"], 1.4).outputs[0],
                 bx + 40, by - 1200)
    rail_geo = _xf(tree, (bx + 240, by - 1200), rail,
                   translation=_combine(tree, (bx - 40, by - 1040), 0.0,
                                        _math(tree, "MULTIPLY", (bx - 240, by - 980),
                                              gin.outputs["Cabinet Depth M"], 0.52).outputs[0],
                                        _math(tree, "MULTIPLY", (bx - 240, by - 860),
                                              gin.outputs["Cabinet Height M"], 0.04).outputs[0])
                   ).outputs["Geometry"]

    # --- cabinet + audio out ----------------------------------------------
    cab = safe_node(tree, "GeometryNodeMeshCube", (bx - 620, by - 1800))
    cabv = _combine(tree, (bx - 900, by - 1800), gin.outputs["Cabinet Width M"],
                    gin.outputs["Cabinet Height M"], gin.outputs["Cabinet Depth M"])
    link_sockets(tree, cabv.outputs["Vector"], cab.inputs["Size"])
    cab_geo = _xf(tree, (bx - 300, by - 1800), cab.outputs["Mesh"],
                  translation=(0.0, 0.0,
                               _math(tree, "MULTIPLY", (bx - 900, by - 1940),
                                     gin.outputs["Cabinet Height M"], 0.5).outputs[0])
                  ).outputs["Geometry"]
    horn = _cone(tree, (bx - 300, by - 2100), 0.012, 0.075, 0.13, vertices=24)
    horn_geo = _xf(tree, (bx - 120, by - 2100), horn.outputs["Mesh"],
                   rotation=(0.0, math.radians(90), 0.0),
                   translation=(_math(tree, "MULTIPLY", (bx - 900, by - 2260),
                                      gin.outputs["Cabinet Width M"], 0.30).outputs[0],
                                0.0,
                                _math(tree, "MULTIPLY", (bx - 900, by - 2380),
                                      gin.outputs["Cabinet Height M"], 1.10).outputs[0])
                   ).outputs["Geometry"]

    body = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 480, by - 800))
    for s in (cab_geo, ant_geo, ant2_geo, pitch_loop, vol_loop, rail_geo, horn_geo):
        link_sockets(tree, s, body.inputs["Geometry"])

    bidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 480, by - 1020))
    bmod = _math(tree, "FLOORMOD", (bx + 480, by - 1140), bidx.outputs["Index"], 12.0)
    stored = _store_named(tree, (bx + 700, by - 960), body.outputs["Geometry"],
                          "tone_semitone_mod12", bmod.outputs[0])
    stored = _store_named(tree, (bx + 880, by - 960), stored, "higgsas_lead",
                          0.0 if (used_pitch or used_vol or used_trace) else 1.0)
    _export_tail(tree, gin, gout, stored, (bx + 1060, by - 800))

    return label_tree(tree, group_name, [
        {"title": "Lissajous Loops", "nodes": ("pitch", "volume"), "role": "curve"},
        {"title": "Tone Field", "nodes": ("trace", "sweep"), "role": "curve"},
        {"title": "Cabinet", "nodes": ("cab", "ant", "horn"), "role": "geometry"},
        {"title": "Export", "nodes": ("realize", "switch", "shade"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_hurdy_gurdy — lead group: Dynamic Catenary Splines
# ---------------------------------------------------------------------------

def build_music_hurdy_gurdy(group_name="MEL_music_hurdy_gurdy"):
    """Hurdy-gurdy: waisted body, cranked wheel + keybox, 3 tangent strings,
    drone strings (catenary), pegbox with tuning pegs, crank handle.

    Lead: `Dynamic Catenary Splines` hangs the drone strings — they sag under
    their own tension and the sag IS the catenary. Native fallback: straight
    lines, which read as rigid rods.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_hurdy_gurdy"

    add_float_param(tree, "Body Length M", 0.68, 0.35, 1.2)
    add_float_param(tree, "Body Width M", 0.26, 0.12, 0.45)
    add_float_param(tree, "Body Depth M", 0.10, 0.04, 0.2)
    add_float_param(tree, "Wheel Radius M", 0.085, 0.03, 0.16)
    add_int_param(tree, "Drone Count", 3, 1, 6)
    add_int_param(tree, "Key Count", 12, 4, 24)
    add_float_param(tree, "String Radius M", 0.0014, 0.0004, 0.005)
    add_bool_param(tree, "Realize for export", False)

    bx, by = 0, 0
    half_len = _math(tree, "MULTIPLY", (bx - 1560, by + 140), gin.outputs["Body Length M"], 0.5)

    # --- waisted body: three blocks, the middle one narrower ---------------
    body_parts = []
    for i, (sc, zoff) in enumerate(((1.0, 0.42), (0.72, 0.0), (1.0, -0.42))):
        cube = safe_node(tree, "GeometryNodeMeshCube", (bx - 1240, by - 200 - i * 260))
        wv = _math(tree, "MULTIPLY", (bx - 1440, by - 200 - i * 260),
                   gin.outputs["Body Width M"], sc)
        hv = _math(tree, "MULTIPLY", (bx - 1440, by - 340 - i * 260),
                   gin.outputs["Body Length M"], 0.42)
        vv = _combine(tree, (bx - 1440, by - 200 - i * 260), wv.outputs[0],
                      hv.outputs[0], gin.outputs["Body Depth M"])
        link_sockets(tree, vv.outputs["Vector"], cube.inputs["Size"])
        zv = _math(tree, "MULTIPLY", (bx - 1440, by - 480 - i * 260), half_len.outputs[0], zoff)
        body_parts.append(_xf(tree, (bx - 1040, by - 200 - i * 260), cube.outputs["Mesh"],
                              translation=_combine(tree, (bx - 1200, by - 480 - i * 260),
                                                   0.0, 0.0, zv.outputs[0])
                              ).outputs["Geometry"])

    # --- drone strings: the catenary lead ----------------------------------
    dcount = safe_node(tree, "FunctionNodeFloatToInt", (bx - 1440, by + 420))
    link_sockets(tree, gin.outputs["Drone Count"], dcount.inputs[0])
    dspan = _math(tree, "MULTIPLY", (bx - 1440, by + 280), gin.outputs["Body Length M"], 0.92)
    dline, dline_sock = _line(tree, (bx - 1240, by + 420), count_sock=dcount.outputs[0],
                              offset=_combine(tree, (bx - 1440, by + 280), 0.0, 0.0,
                                              _math(tree, "DIVIDE", (bx - 1640, by + 200),
                                                    dspan.outputs[0],
                                                    _math(tree, "SUBTRACT", (bx - 1640, by + 120),
                                                          dcount.outputs[0], 1.0).outputs[0]
                                                    ).outputs[0]))
    dpts = safe_node(tree, "GeometryNodeMeshToPoints", (bx - 1040, by + 420))
    link_sockets(tree, dline_sock, sock(dpts, "Mesh") or dpts.inputs[0])
    dy = _math(tree, "DIVIDE", (bx - 1440, by + 560), gin.outputs["Body Width M"], 8.0)
    drake = _math(tree, "MULTIPLY", (bx - 1440, by + 700), dy.outputs[0], 2.0)
    draked = _xf(tree, (bx - 860, by + 420), dpts.outputs["Points"],
                 translation=_combine(tree, (bx - 1040, by + 560),
                                      0.0, drake.outputs[0],
                                      _math(tree, "MULTIPLY", (bx - 1440, by + 840),
                                            half_len.outputs[0], 0.55).outputs[0])
                 ).outputs["Geometry"]

    cat, used_cat = _lead(
        BID, tree, "Dynamic Catenary Splines", (bx - 660, by + 420),
        fallback_type="GeometryNodeMeshToCurve",
        inputs={"Spline Length": _math(tree, "MULTIPLY", (bx - 880, by + 620),
                                       gin.outputs["Body Length M"], 0.86).outputs[0],
                "Spline Resolution": 24, "Axis Rotation": 0.0},
    )
    drone_geo = None
    if cat is not None and not used_cat:
        link_sockets(tree, draked, cat.inputs["Splines"])
        dsweep = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 440, by + 420))
        link_sockets(tree, cat.outputs["Splines"], sock(dsweep, "Curve") or dsweep.inputs[0])
        dprof = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 620, by + 240))
        try:
            dprof.inputs["Resolution"].default_value = 8
        except Exception:
            pass
        link_sockets(tree, gin.outputs["String Radius M"], sock(dprof, "Radius"))
        link_sockets(tree, dprof.outputs["Curve"], sock(dsweep, "Profile Curve"))
        drone_geo = dsweep.outputs["Mesh"]
    else:
        tocurve = safe_node(tree, "GeometryNodeMeshToCurve", (bx - 660, by + 420))
        link_sockets(tree, draked, sock(tocurve, "Mesh") or tocurve.inputs[0])
        dsweep = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 440, by + 420))
        link_sockets(tree, tocurve.outputs["Curve"], sock(dsweep, "Curve") or dsweep.inputs[0])
        dprof = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 620, by + 240))
        try:
            dprof.inputs["Resolution"].default_value = 8
        except Exception:
            pass
        link_sockets(tree, gin.outputs["String Radius M"], sock(dprof, "Radius"))
        link_sockets(tree, dprof.outputs["Curve"], sock(dsweep, "Profile Curve"))
        drone_geo = dsweep.outputs["Mesh"]

    # --- tangent strings: reuse the harp string proto ----------------------
    proto = _ensure_string_proto(tree, "MEL_harp_string_unit", 0.62)
    if proto is not None:
        if proto.inputs.get("Radius M") is not None:
            link_sockets(tree, gin.outputs["String Radius M"], proto.inputs["Radius M"])
    kcount = safe_node(tree, "FunctionNodeFloatToInt", (bx - 1440, by - 900))
    link_sockets(tree, gin.outputs["Key Count"], kcount.inputs[0])
    kspan = _math(tree, "MULTIPLY", (bx - 1440, by - 1040), gin.outputs["Body Length M"], 0.74)
    kline, kline_sock = _line(tree, (bx - 1240, by - 900), count_sock=kcount.outputs[0],
                              offset=_combine(tree, (bx - 1440, by - 1040), 0.0, 0.0,
                                              _math(tree, "DIVIDE", (bx - 1640, by - 1120),
                                                    kspan.outputs[0],
                                                    _math(tree, "SUBTRACT", (bx - 1640, by - 1200),
                                                          kcount.outputs[0], 1.0).outputs[0]
                                                    ).outputs[0]))
    kpts = safe_node(tree, "GeometryNodeMeshToPoints", (bx - 1040, by - 900))
    link_sockets(tree, kline_sock, sock(kpts, "Mesh") or kpts.inputs[0])
    krake = _xf(tree, (bx - 860, by - 900), kpts.outputs["Points"],
                translation=_combine(tree, (bx - 1040, by - 760),
                                     0.0,
                                     _math(tree, "MULTIPLY", (bx - 1440, by - 620),
                                           gin.outputs["Body Width M"], 0.34).outputs[0],
                                     _math(tree, "MULTIPLY", (bx - 1440, by - 760),
                                           half_len.outputs[0], 0.30).outputs[0])
                ).outputs["Geometry"]
    kinst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 660, by - 900))
    link_sockets(tree, krake, sock(kinst, "Points"))
    if proto is not None:
        link_sockets(tree, proto.outputs["Geometry"], sock(kinst, "Instance"))

    # --- wheel, keybox, crank, pegbox --------------------------------------
    wheel = _cyl(tree, (bx - 1240, by - 1300), gin.outputs["Wheel Radius M"],
                 _math(tree, "MULTIPLY", (bx - 1440, by - 1300),
                       gin.outputs["Body Width M"], 0.42).outputs[0], vertices=48, fill=0)
    wheel_geo = _xf(tree, (bx - 1040, by - 1300), wheel.outputs["Mesh"],
                    rotation=(0.0, math.radians(90), 0.0),
                    translation=(0.0,
                                 _math(tree, "MULTIPLY", (bx - 1440, by - 1440),
                                       gin.outputs["Body Width M"], 0.40).outputs[0],
                                 _math(tree, "MULTIPLY", (bx - 1440, by - 1580),
                                       half_len.outputs[0], 0.22).outputs[0])
                    ).outputs["Geometry"]
    keybox = safe_node(tree, "GeometryNodeMeshCube", (bx - 1240, by - 1700))
    kvv = _combine(tree, (bx - 1440, by - 1700),
                   _math(tree, "MULTIPLY", (bx - 1640, by - 1700),
                         gin.outputs["Body Width M"], 0.30).outputs[0],
                   _math(tree, "MULTIPLY", (bx - 1640, by - 1840),
                         gin.outputs["Body Length M"], 0.30).outputs[0],
                   _math(tree, "MULTIPLY", (bx - 1640, by - 1980),
                         gin.outputs["Body Depth M"], 1.6).outputs[0])
    link_sockets(tree, kvv.outputs["Vector"], keybox.inputs["Size"])
    keybox_geo = _xf(tree, (bx - 1040, by - 1700), keybox.outputs["Mesh"],
                     translation=_combine(tree, (bx - 1240, by - 1840), 0.0,
                                          _math(tree, "MULTIPLY", (bx - 1440, by - 1980),
                                                gin.outputs["Body Width M"], 0.62).outputs[0],
                                          _math(tree, "MULTIPLY", (bx - 1440, by - 2120),
                                                half_len.outputs[0], 0.30).outputs[0])
                     ).outputs["Geometry"]
    crank = _cyl(tree, (bx - 1240, by - 2160), 0.008,
                 _math(tree, "MULTIPLY", (bx - 1440, by - 2160),
                       gin.outputs["Wheel Radius M"], 0.6).outputs[0], vertices=10)
    crank_geo = _xf(tree, (bx - 1040, by - 2160), crank.outputs["Mesh"],
                    rotation=(0.0, math.radians(90), 0.0),
                    translation=(0.0,
                                 _math(tree, "MULTIPLY", (bx - 1440, by - 2300),
                                       gin.outputs["Body Width M"], 0.62).outputs[0],
                                 _math(tree, "MULTIPLY", (bx - 1440, by - 2440),
                                       half_len.outputs[0], 0.58).outputs[0])
                    ).outputs["Geometry"]
    pegbox = safe_node(tree, "GeometryNodeMeshCube", (bx - 1240, by + 1000))
    pv = _combine(tree, (bx - 1440, by + 1000),
                  _math(tree, "MULTIPLY", (bx - 1640, by + 1000),
                        gin.outputs["Body Width M"], 0.34).outputs[0],
                  _math(tree, "MULTIPLY", (bx - 1640, by + 860),
                        gin.outputs["Body Length M"], 0.26).outputs[0],
                  gin.outputs["Body Depth M"])
    link_sockets(tree, pv.outputs["Vector"], pegbox.inputs["Size"])
    pegbox_geo = _xf(tree, (bx - 1040, by + 1000), pegbox.outputs["Mesh"],
                     translation=_combine(tree, (bx - 1240, by + 860), 0.0, 0.0,
                                          _math(tree, "MULTIPLY", (bx - 1440, by + 720),
                                                half_len.outputs[0], 1.28).outputs[0])
                     ).outputs["Geometry"]
    pegcount = safe_node(tree, "FunctionNodeFloatToInt", (bx - 1440, by + 1400))
    link_sockets(tree, gin.outputs["Key Count"], pegcount.inputs[0])
    pgspan = _math(tree, "MULTIPLY", (bx - 1440, by + 1540), gin.outputs["Body Length M"], 0.24)
    pegline, pegline_sock = _line(tree, (bx - 1240, by + 1400),
                                  count_sock=pegcount.outputs[0],
                                  offset=_combine(tree, (bx - 1440, by + 1540), 0.0, 0.0,
                                                  _math(tree, "DIVIDE", (bx - 1640, by + 1620),
                                                        pgspan.outputs[0],
                                                        _math(tree, "SUBTRACT", (bx - 1640, by + 1700),
                                                              pegcount.outputs[0], 1.0).outputs[0]
                                                        ).outputs[0]))
    pegpts = safe_node(tree, "GeometryNodeMeshToPoints", (bx - 1040, by + 1400))
    link_sockets(tree, pegline_sock, sock(pegpts, "Mesh") or pegpts.inputs[0])
    pegrake = _xf(tree, (bx - 860, by + 1400), pegpts.outputs["Points"],
                  translation=_combine(tree, (bx - 1040, by + 1400), 0.0,
                                       _math(tree, "MULTIPLY", (bx - 1440, by + 1260),
                                             gin.outputs["Body Width M"], 0.22).outputs[0],
                                       _math(tree, "MULTIPLY", (bx - 1440, by + 1120),
                                             half_len.outputs[0], 1.30).outputs[0])
                  ).outputs["Geometry"]
    peg = _cyl(tree, (bx - 660, by + 1620), 0.006, 0.05, vertices=10)
    peg_geo = _xf(tree, (bx - 480, by + 1620), peg.outputs["Mesh"],
                  rotation=(math.radians(90), 0, 0)).outputs["Geometry"]
    peginst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 300, by + 1400))
    link_sockets(tree, pegrake, sock(peginst, "Points"))
    link_sockets(tree, peg_geo, sock(peginst, "Instance"))

    body = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 100, by - 600))
    for s in (*body_parts, drone_geo, kinst.outputs["Instances"], wheel_geo,
              keybox_geo, crank_geo, pegbox_geo, peginst.outputs["Instances"]):
        link_sockets(tree, s, body.inputs["Geometry"])

    bidx = safe_node(tree, "GeometryNodeInputIndex", (bx + 100, by - 820))
    bmod = _math(tree, "FLOORMOD", (bx + 100, by - 940), bidx.outputs["Index"], 12.0)
    stored = _store_named(tree, (bx + 320, by - 760), body.outputs["Geometry"],
                          "key_semitone_mod12", bmod.outputs[0])
    stored = _store_named(tree, (bx + 500, by - 760), stored, "higgsas_lead",
                          0.0 if used_cat else 1.0)
    _export_tail(tree, gin, gout, stored, (bx + 680, by - 600))

    _refresh_group_refs_multi(tree, ("MEL_harp_string_unit",))
    return label_tree(tree, group_name, [
        {"title": "Drone Catenary", "nodes": ("dpts", "cat"), "role": "curve"},
        {"title": "Tangents", "nodes": ("kline", "kinst"), "role": "instance"},
        {"title": "Action", "nodes": ("wheel", "crank", "keybox"), "role": "geometry"},
        {"title": "Export", "nodes": ("realize", "switch", "shade"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

register_builder(
    "MEL_music_bandoneon", build_music_bandoneon, "Bandoneon",
    "Concert accordion: lofted bellows skin pleated into a stack, two boxes, "
    "6x12 chromatic button board. Lead group: Higgsas Loft Splines.",
    "music",
)
register_builder(
    "MEL_music_saxophone", build_music_saxophone, "Saxophone",
    "Tenor sax: tapered conical bore, bent crook, upturned bell, 6 key cups. "
    "Lead groups: Higgsas Taper + Bend.",
    "music",
)
register_builder(
    "MEL_music_glass_harmonica", build_music_glass_harmonica, "Glass Harmonica",
    "Franklin armonica: 24 chromatically-tuned glass bowls on a spindle with "
    "sustain wheel. Lead group: Higgsas Spherical Spiral + Bezier Resample.",
    "music",
)
register_builder(
    "MEL_music_music_box", build_music_music_box, "Music Box (Cylinder)",
    "Pinned cylinder music box: governor gear train, 6x20 pin field, steel "
    "comb, spring barrel. Lead group: Higgsas Spur Gear.",
    "music",
)
register_builder(
    "MEL_music_theremin", build_music_theremin, "Theremin",
    "Pitch + volume antennas with Lissajous reference loops and a tone-field "
    "trace rail. Lead group: Higgsas Lissajous Curve.",
    "music",
)
register_builder(
    "MEL_music_hurdy_gurdy", build_music_hurdy_gurdy, "Hurdy-Gurdy",
    "Waisted body, cranked wheel + keybox, 3 catenary drones, 12 tangent "
    "strings, pegbox. Lead group: Higgsas Dynamic Catenary Splines.",
    "music",
)