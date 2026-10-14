"""P4 wave 8 — keyboard lane: grand piano, upright piano, harmonium, clavinet,
mellotron, tonewheel organ.

Gap audit first (repo-wide grep over `deploy/surreal_arch/` + the live registry,
2026-10-04): the keyboard lane owns `MEL_music_baroque_harpsichord`,
`MEL_music_baroque_organ` (a walkable FACADE), `MEL_music_organ_pipes` (an ET
pipe rank, nested in the organ), `MEL_imm_piano_keys` (a WALKABLE key row),
`MEL_music_piano_roll` / `MEL_mh_piano_walk` (notation and a walkway), and
`MEL_music_celesta`. NONE of the six ids below existed anywhere (grep count 0
each, and 0 in `Tools/registry_baseline.json`):

    grand piano, upright piano, harmonium, clavinet, mellotron, tonewheel organ

`MEL_music_baroque_organ` is architecture (a facade you walk into) and
`MEL_music_organ_pipes` is its pipe rank — neither is a drawbar console, which
is why `MEL_music_tonewheel_organ` is a new id rather than a preset of them.

Design rules (same as music_wind_percussion / music_percussion_kit /
music_string_kit / music_wind_folk):
  - Native-only: these are cases, plates, ranks and drums that 5.2 primitives
    express exactly; a Higgsas subtree here would be decoration, not a lead.
    Every builder still stores `higgsas_lead` (1.0 = native) so the family gate
    and the instruments gate read the lane uniformly.
  - The keybed is authored ONCE (`_keyboard`) and sized per instrument. All six
    share it: white rank + the `{0,1,3,4,5}-mod-7` black subset (the octave law
    `MEL_imm_piano_keys` established), never six private copies.
  - Origin-explicit primitives only: `_cyl_x`/`_cyl_z` take the CENTRE,
    `_cone_x`/`_cone_z` take the BASE. This lane adds `_cyl_y` (the shared set
    has no Y-laid cylinder) under the same contract.
  - The shared `MEL_harp_string_unit` proto is REUSED for the upright's vertical
    string rank, with the caller's own length linked into the proto NODE's
    `Length M` at the call site (an unlinked proto keeps the first-created
    length and every instrument measures the same z extent).
  - Line offsets are always CombineXYZ (a bare float broadcasts to (v, v, v)).
  - A field value never feeds a PRIMITIVE dimension (the collapse class): every
    primitive dimension here is a socket-driven CombineXYZ component with all
    three components written.

Builders:
    MEL_music_grand_piano      case + curved bentside + tilted lid + music desk
                               + 3 legs + 52-key keybed + graduated string rank
                               + 3 pedals
    MEL_music_upright_piano    tall case + fallboard + music desk + 2 legs
                               + keybed + vertical string rank + 3 pedals
    MEL_music_harmonium        case on side panels + keybed + 8 drawstops
                               + 2 knee levers + treadle pair + pleated bellows
    MEL_music_clavinet         thin body on a stand + keybed + short string rank
                               + 2 pickup bars + cable rail
    MEL_music_mellotron        case on a stand + keybed + 2 tape reels + 2 tape
                               frame plates + a rank of tape heads
    MEL_music_tonewheel_organ  plinth + console + 2 manuals + 9 drawbars
                               + 13-note pedalboard + swell pedal + rotating
                               speaker drum in its own cabinet
"""

from __future__ import annotations

import math

from .core import (
    safe_node, link_sockets, label_tree, new_geometry_tree, add_float_param,
    add_int_param, add_bool_param, register_builder, sock,
)
from .music_harps_real import _math, _combine, _ensure_string_proto
from .music_higgsas_instruments import (
    _store_named, _cone, _cyl, _line, _xf, _set_fill,
)
from .music_string_kit import _finish
from .music_percussion_kit import _inst_rank
from .music_wind_reed_brass import (
    _vec, _sphere, _cone_x, _cyl_x, _cone_z, _cyl_z, _cone_proto_z,
    _cyl_proto_z, _join, _count_minus_one, _step, _rank, _rank_axis,
    _half_span, _stand, _box_pair, _rank_inst,
)

_FALLBACKS: dict = {}


# ---------------------------------------------------------------------------
# Lane-local maths wrappers (socket-returning, so no stray `.outputs[0]`)
# ---------------------------------------------------------------------------

def _m(tree, op, loc, a=None, b=None):
    """A Math node's Value output, or None. `a`/`b` may be sockets or floats."""
    n = _math(tree, op, loc, a, b)
    return n.outputs[0] if n is not None and n.outputs else None


def _boolop(tree, op, loc, a=None, b=None):
    """A FunctionNodeBooleanMath output. `FunctionNodeBooleanMath` is 5.2's
    spelling (probed 2026-10-04: inputs ['Boolean','Boolean'], ops AND/OR/NOT/
    XOR/...). A wrong bl_idname would be swallowed by `safe_node`'s None and the
    whole selection would silently fall through, so the caller asserts it."""
    n = safe_node(tree, "FunctionNodeBooleanMath", loc)
    if n is None:
        return None
    try:
        n.operation = op
    except Exception:
        pass
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        s = n.inputs[i]
        if isinstance(v, (int, float)):
            try:
                s.default_value = bool(v)
            except Exception:
                pass
        else:
            link_sockets(tree, v, s)
    return n.outputs["Boolean"] if n.outputs else None


def _cyl_y(tree, loc, r, length, cy, x=0.0, z=0.0, verts=24):
    """Cylinder laid along Y with its CENTRE at `cy`.

    The shared wave-6 helper set has X-laid and Z-laid forms only. This is the
    same contract as `_cyl_x`/`_cyl_z`: the argument is the CENTRE, never a base
    (`MeshCylinder`'s origin is its centre; `MeshCone`'s is its base).
    """
    prim = _cyl(tree, loc, r, length, vertices=verts)
    if prim is None:
        return None
    return _xf(tree, (loc[0] + 200, loc[1]), prim.outputs["Mesh"],
               rotation=(math.radians(90.0), 0.0, 0.0),
               translation=_vec(tree, (loc[0] + 200, loc[1] - 200),
                               x, cy, z)).outputs["Geometry"]


def _keys_attrs(tree, loc):
    """The keyboard lane's attribute pair: a key-semitone tag + the lead flag.

    `key_semitone_mod12` is the tag `music_higgsas_instruments` already uses for
    keyboard builders, so a convergence consumer reads every keyed instrument
    the same way.
    """
    bx, by = loc
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx, by))
    mod = _m(tree, "MODULO", (bx, by - 140), idx.outputs["Index"] if idx else None, 12.0)
    return [("key_semitone_mod12", mod), ("higgsas_lead", 1.0)]


# ---------------------------------------------------------------------------
# The keybed law — authored once, sized per instrument
# ---------------------------------------------------------------------------

def _keyboard(tree, loc, white_count, span, kw, kd, kh, base_z, y,
              black_frac=0.62):
    """A piano-style keybed: a white rank with the mod-7 black subset.

    `white_count` is an INT socket, `span` the total keybed width in X, `kw` the
    per-key pitch source (unused: the pitch is span/(count-1) so a rank of N
    keys always spans exactly `span` — the `MEL_music_sheng` double-count class
    cannot appear). `kd`/`kh` are the key depth (Y) and height (Z); `base_z` is
    the keybed's underside and `y` the white keys' centre line.

    Returns a geometry socket (whites + blacks). The blacks are the
    {0,1,3,4,5}-mod-7 subset of the SAME rank points, shifted +half a step in X,
    forward in -Y and raised so they stand proud of the whites — the octave law
    `MEL_imm_piano_keys` established, reused here rather than re-derived.
    """
    bx, by = loc
    half_span = _m(tree, "MULTIPLY", (bx - 900, by + 240), span, -0.5)
    step = _step(tree, (bx - 700, by + 120), span, white_count)
    half_kh = _m(tree, "MULTIPLY", (bx - 900, by - 100), kh, 0.5)
    pt_z = _m(tree, "ADD", (bx - 700, by - 100), base_z, half_kh)

    pts = _rank_axis(tree, (bx - 400, by), white_count, "x", half_span,
                     step.outputs[0], y=y, z=pt_z)

    w_kw = _m(tree, "MULTIPLY", (bx - 700, by - 320), step.outputs[0], 0.88)
    wkey = safe_node(tree, "GeometryNodeMeshCube", (bx - 500, by - 320))
    if wkey is not None:
        link_sockets(tree, _vec(tree, (bx - 700, by - 480), w_kw, kd, kh),
                     sock(wkey, "Size"))
    whites = _inst_rank(tree, (bx - 100, by), pts, wkey.outputs["Mesh"] if wkey else None)

    # black subset: mod 7 in {0,1,3,4,5}
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 400, by + 500))
    mod7 = _m(tree, "MODULO", (bx - 200, by + 500), idx.outputs["Index"] if idx else None, 7.0)
    lt2 = _m(tree, "LESS_THAN", (bx, by + 620), mod7, 2.0)
    gt2 = _m(tree, "GREATER_THAN", (bx, by + 500), mod7, 2.0)
    lt6 = _m(tree, "LESS_THAN", (bx, by + 380), mod7, 6.0)
    band = _boolop(tree, "AND", (bx + 200, by + 500), gt2, lt6)
    sel = _boolop(tree, "OR", (bx + 400, by + 620), lt2, band)

    bpts = None
    sep = safe_node(tree, "GeometryNodeSeparateGeometry", (bx + 600, by))
    if sep is not None and pts is not None and sel is not None:
        link_sockets(tree, pts, sock(sep, "Geometry"))
        link_sockets(tree, sel, sock(sep, "Selection"))
        bpts = sep.outputs["Selection"]

    b_kh = _m(tree, "MULTIPLY", (bx + 700, by - 320), kh, 1.55)
    b_kd = _m(tree, "MULTIPLY", (bx + 700, by - 480), kd, black_frac)
    # re-centre: the point came from the white rank at base_z + kh/2, the black
    # proto is taller, so lift the point by (b_kh - kh)/2 — a proto is scaled
    # about the instance origin, not about its own base.
    dz = _m(tree, "MULTIPLY", (bx + 700, by - 640),
            _m(tree, "SUBTRACT", (bx + 500, by - 640), b_kh, kh), 0.5)
    b_shift = _m(tree, "MULTIPLY", (bx + 700, by - 800), step.outputs[0], 0.5)
    b_y = _m(tree, "MULTIPLY", (bx + 700, by - 960), kd, -0.22)
    bpts2 = None
    if bpts is not None:
        bpts2 = _xf(tree, (bx + 900, by), bpts,
                    translation=_vec(tree, (bx + 900, by - 800),
                                     b_shift, b_y, dz)).outputs["Geometry"]

    bkey = safe_node(tree, "GeometryNodeMeshCube", (bx + 1100, by - 320))
    if bkey is not None:
        link_sockets(tree, _vec(tree, (bx + 900, by - 480), w_kw, b_kd, b_kh),
                     sock(bkey, "Size"))
    blacks = _inst_rank(tree, (bx + 1300, by), bpts2,
                        bkey.outputs["Mesh"] if bkey else None)

    return _join(tree, (bx + 1500, by), [whites, blacks])


def _string_rank_y(tree, loc, count_sock, span_sock, first_sock, y, z,
                   r_sock, len_sock, spread=0.55):
    """A rank of Y-laid strings with a Mersenne-style length graduation.

    The proto is centred on its own origin, so the instance point IS the string
    centre. `ScaleInstances` is fed (1, s, 1) from a Math chain over the index —
    a rank with no driver is N identical strings, and the gate asserts the
    driver exists. Scaling about the instance origin grows a bass string both
    ways, which is the real layout (bass strings run further front AND back).
    """
    bx, by = loc
    proto = _cyl_y(tree, (bx - 400, by), r_sock, len_sock, 0.0, verts=10)
    if proto is None:
        return None
    pts = _rank_axis(tree, (bx - 200, by), count_sock, "x", first_sock,
                     _step(tree, (bx - 400, by - 200), span_sock, count_sock).outputs[0],
                     y=y, z=z)
    inst = _inst_rank(tree, (bx, by), pts, proto)
    if inst is None:
        return None
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx, by - 400))
    t = _m(tree, "DIVIDE", (bx + 200, by - 400), idx.outputs["Index"] if idx else None,
           _count_minus_one(tree, (bx, by - 560), count_sock))
    s = _m(tree, "SUBTRACT", (bx + 400, by - 400), 1.0,
           _m(tree, "MULTIPLY", (bx + 200, by - 720), t, spread))
    sc = _vec(tree, (bx + 600, by - 400), 1.0, s, 1.0)
    si = safe_node(tree, "GeometryNodeScaleInstances", (bx + 800, by))
    if si is None:
        return inst
    link_sockets(tree, inst, sock(si, "Instances") or si.inputs[0])
    link_sockets(tree, sc, sock(si, "Scale") or si.inputs[1])
    return si.outputs["Instances"] if "Instances" in si.outputs else si.outputs[0]


def _disc_y(tree, loc, r_sock, depth_sock, cy, x=0.0, z=0.0, verts=32):
    """A disc standing in the XZ plane (axis along Y) — tape reels, drums."""
    return _cyl_y(tree, loc, r_sock, depth_sock, cy, x=x, z=z, verts=verts)


def _plate(tree, loc, sx, sy, sz, translation=None, rotation=None):
    """A thin box whose Size is a fully-linked CombineXYZ.

    A primitive `Size` with an UNLINKED component defaults that component to 0
    (the castle-merlon class: a zero-width slab whose degeneracy propagates into
    every parent), so every plate in this lane links all three components.
    """
    n = safe_node(tree, "GeometryNodeMeshCube", loc)
    if n is None:
        return None
    link_sockets(tree, _vec(tree, (loc[0] - 200, loc[1] - 200), sx, sy, sz),
                 sock(n, "Size"))
    if translation is None and rotation is None:
        return n.outputs["Mesh"]
    return _xf(tree, (loc[0] + 200, loc[1]), n.outputs["Mesh"],
               rotation=rotation, translation=translation).outputs["Geometry"]


# ---------------------------------------------------------------------------
# MEL_music_grand_piano
# ---------------------------------------------------------------------------

def build_music_grand_piano(group_name="MEL_music_grand_piano"):
    """Grand piano: case, curved bentside, tilted lid, music desk, 3 legs,
    52-key keybed, graduated string rank, 3 pedals.

    The case's long axis is Y (front-to-back) and the keyboard runs along X —
    the real instrument's layout, and the reason the keybed's `span` is a
    fraction of the case WIDTH while the strings run along Y.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_grand_piano"
    bx, by = 0, 0

    add_float_param(tree, "Body Width M", 1.48, 0.8, 2.2)
    add_float_param(tree, "Body Length M", 1.95, 1.0, 2.8)
    add_float_param(tree, "Body Depth M", 0.24, 0.10, 0.45)
    add_float_param(tree, "Lid Angle", 32.0, 0.0, 70.0)
    add_float_param(tree, "Leg Height M", 0.62, 0.3, 0.9)
    add_int_param(tree, "White Key Count", 52, 24, 88)
    add_float_param(tree, "Key Depth M", 0.14, 0.06, 0.24)
    add_float_param(tree, "Key Height M", 0.022, 0.010, 0.05)
    add_int_param(tree, "String Count", 30, 8, 60)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    W = gin.outputs["Body Width M"]
    L = gin.outputs["Body Length M"]
    D = gin.outputs["Body Depth M"]
    LH = gin.outputs["Leg Height M"]
    KD = gin.outputs["Key Depth M"]
    KH = gin.outputs["Key Height M"]

    half_w = _m(tree, "MULTIPLY", (bx - 2000, by - 200), W, 0.5)
    half_l = _m(tree, "MULTIPLY", (bx - 2000, by - 340), L, 0.5)
    case_top = _m(tree, "ADD", (bx - 2000, by - 480), LH, D)
    case_mid = _m(tree, "ADD", (bx - 2000, by - 620), LH,
                  _m(tree, "MULTIPLY", (bx - 2200, by - 620), D, 0.5))

    # --- case: a box whose long axis is Y -----------------------------------
    case = _plate(tree, (bx - 1500, by), W, L, D,
                  translation=_vec(tree, (bx - 1500, by - 200), 0.0, 0.0, case_mid))

    # --- bentside: the curved rim, a quadratic bezier swept with a tube ------
    bz = safe_node(tree, "GeometryNodeCurveQuadraticBezier", (bx - 1500, by - 900))
    if bz is not None:
        try:
            bz.inputs["Resolution"].default_value = 24
        except Exception:
            pass
        link_sockets(tree, _vec(tree, (bx - 1700, by - 1040),
                                _m(tree, "MULTIPLY", (bx - 1900, by - 1040), half_w, -1.0),
                                _m(tree, "MULTIPLY", (bx - 1900, by - 1180), half_l, 0.5),
                                case_top), bz.inputs["Start"])
        link_sockets(tree, _vec(tree, (bx - 1700, by - 1320), 0.0,
                                _m(tree, "MULTIPLY", (bx - 1900, by - 1320), half_l, 1.06),
                                case_top), bz.inputs["Middle"])
        link_sockets(tree, _vec(tree, (bx - 1700, by - 1460), half_w,
                                _m(tree, "MULTIPLY", (bx - 1900, by - 1460), half_l, 0.5),
                                case_top), bz.inputs["End"])
    prof = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 1500, by - 1700))
    if prof is not None:
        try:
            prof.inputs["Radius"].default_value = 0.035
            prof.inputs["Resolution"].default_value = 8
        except Exception:
            pass
    c2m = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 1200, by - 900))
    bentside = None
    if c2m is not None and bz is not None and prof is not None:
        link_sockets(tree, bz.outputs["Curve"], sock(c2m, "Curve"))
        link_sockets(tree, prof.outputs["Curve"], sock(c2m, "Profile Curve"))
        bentside = c2m.outputs["Mesh"]

    # --- lid: hinged on the -X edge, opened by Lid Angle ---------------------
    lid_plate = _plate(tree, (bx - 1500, by - 2000), W, L, 0.02,
                       translation=_vec(tree, (bx - 1700, by - 2140), half_w, 0.0, 0.0))
    ang = _m(tree, "MULTIPLY", (bx - 2000, by - 2280), gin.outputs["Lid Angle"],
             -0.0174533)
    lid = _xf(tree, (bx - 1200, by - 2000), lid_plate,
              rotation=_vec(tree, (bx - 1500, by - 2140), 0.0, ang, 0.0),
              translation=_vec(tree, (bx - 1400, by - 2140),
                               _m(tree, "MULTIPLY", (bx - 1600, by - 2140), half_w, -1.0),
                               0.0, case_top))
    lid_geo = lid.outputs["Geometry"] if lid is not None else None

    # --- music desk: a standing plate just behind the keys -------------------
    desk = _plate(tree, (bx - 1200, by - 2500),
                  _m(tree, "MULTIPLY", (bx - 1400, by - 2500), W, 0.36),
                  0.02,
                  _m(tree, "MULTIPLY", (bx - 1400, by - 2640), D, 0.95),
                  translation=_vec(tree, (bx - 1400, by - 2640), 0.0,
                                   _m(tree, "MULTIPLY", (bx - 1600, by - 2640), half_l, -0.62),
                                   _m(tree, "ADD", (bx - 1600, by - 2780), case_top,
                                      _m(tree, "MULTIPLY", (bx - 1800, by - 2780), D, 0.45))),
                  rotation=_vec(tree, (bx - 1400, by - 2920), math.radians(-18.0), 0.0, 0.0))

    # --- three legs (two front, one under the tail) -------------------------
    legs = []
    for i, (lx, ly) in enumerate(((-0.42, -0.34), (0.42, -0.34), (0.0, 0.34))):
        legs.append(_cyl_z(tree, (bx - 1000 - i * 200, by - 3200),
                           _m(tree, "MULTIPLY", (bx - 1200 - i * 200, by - 3200), W, 0.024),
                           LH,
                           _m(tree, "MULTIPLY", (bx - 1200 - i * 200, by - 3340), LH, 0.5),
                           x=_m(tree, "MULTIPLY", (bx - 1200 - i * 200, by - 3480), W, lx),
                           y=_m(tree, "MULTIPLY", (bx - 1200 - i * 200, by - 3620), L, ly),
                           verts=16))

    # --- keybed: 52 whites, on the case front -------------------------------
    kb = _keyboard(tree, (bx - 400, by - 4000), gin.outputs["White Key Count"],
                   _m(tree, "MULTIPLY", (bx - 800, by - 4000), W, 0.82),
                   None, KD, KH, case_top,
                   _m(tree, "ADD", (bx - 800, by - 4140),
                      _m(tree, "MULTIPLY", (bx - 1000, by - 4140), half_l, -1.0),
                      _m(tree, "MULTIPLY", (bx - 1000, by - 4280), KD, -0.44)))

    # --- strings: a graduated rank along X, lying along Y inside the case ----
    strings = _string_rank_y(
        tree, (bx - 400, by - 5200), gin.outputs["String Count"],
        _m(tree, "MULTIPLY", (bx - 800, by - 5200), W, 0.62),
        _m(tree, "MULTIPLY", (bx - 1000, by - 5200),
           _m(tree, "MULTIPLY", (bx - 1200, by - 5200), W, 0.62), -0.5),
        y=_m(tree, "MULTIPLY", (bx - 800, by - 5340), L, 0.06),
        z=_m(tree, "ADD", (bx - 800, by - 5480), LH,
             _m(tree, "MULTIPLY", (bx - 1000, by - 5480), D, 0.45)),
        r_sock=_m(tree, "MULTIPLY", (bx - 800, by - 5620), W, 0.0026),
        len_sock=_m(tree, "MULTIPLY", (bx - 800, by - 5760), L, 0.86))

    # --- three pedals on a lyre at the front --------------------------------
    pedal = _plate(tree, (bx - 800, by - 6000),
                   _m(tree, "MULTIPLY", (bx - 1000, by - 6000), W, 0.055),
                   0.10, 0.022,
                   translation=_vec(tree, (bx - 1000, by - 6140), 0.0,
                                    _m(tree, "MULTIPLY", (bx - 1200, by - 6140), half_l, -1.16),
                                    0.03))
    pedals = _rank_inst(tree, (bx - 400, by - 6000), 3, pedal,
                        _m(tree, "MULTIPLY", (bx - 600, by - 6000), W, 0.14),
                        _m(tree, "MULTIPLY", (bx - 600, by - 6140), W, -0.07))

    geom = _join(tree, (bx + 400, by),
                 [case, bentside, lid_geo, desk, kb, strings, pedals] + legs)

    _finish(tree, gin, gout, geom, (bx + 600, by), BID,
            _keys_attrs(tree, (bx + 400, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Case + Bentside", "nodes": ("Cube", "Quadratic Bezier", "Curve to Mesh"), "role": "geometry"},
        {"title": "Lid + Desk + Legs", "nodes": ("Cube", "Cylinder", "Transform"), "role": "geometry"},
        {"title": "Keybed + Strings", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_upright_piano
# ---------------------------------------------------------------------------

def build_music_upright_piano(group_name="MEL_music_upright_piano"):
    """Upright piano: tall case on two front legs, fallboard, music desk, keybed
    at 0.72 of the case height, vertical string rank (the shared
    `MEL_harp_string_unit` proto), three pedals.

    The case is TALL (height > depth) — that is what makes it an upright and not
    a grand, and the gate asserts `Case Height M` really reaches the case's
    primitive Size.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_upright_piano"
    bx, by = 0, 0

    add_float_param(tree, "Case Width M", 1.45, 0.8, 2.0)
    add_float_param(tree, "Case Depth M", 0.60, 0.3, 0.9)
    add_float_param(tree, "Case Height M", 1.22, 0.7, 1.6)
    add_float_param(tree, "Leg Height M", 0.10, 0.0, 0.3)
    add_int_param(tree, "White Key Count", 52, 24, 88)
    add_float_param(tree, "Key Depth M", 0.14, 0.06, 0.24)
    add_float_param(tree, "Key Height M", 0.022, 0.010, 0.05)
    add_int_param(tree, "String Count", 30, 8, 60)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    W = gin.outputs["Case Width M"]
    D = gin.outputs["Case Depth M"]
    H = gin.outputs["Case Height M"]
    LH = gin.outputs["Leg Height M"]
    KD = gin.outputs["Key Depth M"]
    KH = gin.outputs["Key Height M"]

    half_w = _m(tree, "MULTIPLY", (bx - 2000, by - 200), W, 0.5)
    half_d = _m(tree, "MULTIPLY", (bx - 2000, by - 340), D, 0.5)
    case_mid = _m(tree, "ADD", (bx - 2000, by - 480), LH,
                  _m(tree, "MULTIPLY", (bx - 2200, by - 480), H, 0.5))
    case_top = _m(tree, "ADD", (bx - 2000, by - 620), LH, H)
    key_z = _m(tree, "ADD", (bx - 2000, by - 760), LH,
               _m(tree, "MULTIPLY", (bx - 2200, by - 760), H, 0.72))

    case = _plate(tree, (bx - 1500, by), W, D, H,
                  translation=_vec(tree, (bx - 1500, by - 200), 0.0, 0.0, case_mid))

    # top lid
    top = _plate(tree, (bx - 1500, by - 900), W, D, 0.03,
                 translation=_vec(tree, (bx - 1500, by - 1100), 0.0, 0.0,
                                  _m(tree, "ADD", (bx - 1700, by - 1100), case_top, 0.015)))

    # fallboard above the keys, tilted forward
    fall = _plate(tree, (bx - 1500, by - 1600), W, 0.03,
                  _m(tree, "MULTIPLY", (bx - 1700, by - 1600), H, 0.14),
                  translation=_vec(tree, (bx - 1700, by - 1740), 0.0,
                                   _m(tree, "ADD", (bx - 1900, by - 1740),
                                      _m(tree, "MULTIPLY", (bx - 2100, by - 1740), half_d, -1.0),
                                      _m(tree, "MULTIPLY", (bx - 2100, by - 1880), KD, -0.30)),
                                   _m(tree, "ADD", (bx - 1900, by - 1880), key_z,
                                      _m(tree, "MULTIPLY", (bx - 2100, by - 1880), H, 0.075))),
                  rotation=_vec(tree, (bx - 1700, by - 2020), math.radians(26.0), 0.0, 0.0))

    # music desk
    desk = _plate(tree, (bx - 1200, by - 2400),
                  _m(tree, "MULTIPLY", (bx - 1400, by - 2400), W, 0.62), 0.02,
                  _m(tree, "MULTIPLY", (bx - 1400, by - 2540), H, 0.16),
                  translation=_vec(tree, (bx - 1400, by - 2540), 0.0,
                                   _m(tree, "ADD", (bx - 1600, by - 2540),
                                      _m(tree, "MULTIPLY", (bx - 1800, by - 2540), half_d, -1.0), -0.06),
                                   _m(tree, "ADD", (bx - 1600, by - 2680), key_z,
                                      _m(tree, "MULTIPLY", (bx - 1800, by - 2680), H, 0.16))))

    # two front legs
    legs = []
    for i, sx in enumerate((-1.0, 1.0)):
        legs.append(_cyl_z(tree, (bx - 1000 - i * 200, by - 3000),
                           _m(tree, "MULTIPLY", (bx - 1200 - i * 200, by - 3000), W, 0.018),
                           LH,
                           _m(tree, "MULTIPLY", (bx - 1200 - i * 200, by - 3140), LH, 0.5),
                           x=_m(tree, "MULTIPLY", (bx - 1200 - i * 200, by - 3280), half_w, sx),
                           y=_m(tree, "MULTIPLY", (bx - 1200 - i * 200, by - 3420), half_d, -0.72),
                           verts=14))

    # keybed on the front face
    kb = _keyboard(tree, (bx - 400, by - 3800), gin.outputs["White Key Count"],
                   _m(tree, "MULTIPLY", (bx - 800, by - 3800), W, 0.82),
                   None, KD, KH, key_z,
                   _m(tree, "ADD", (bx - 800, by - 3940),
                      _m(tree, "MULTIPLY", (bx - 1000, by - 3940), half_d, -1.0),
                      _m(tree, "MULTIPLY", (bx - 1000, by - 4080), KD, -0.42)))

    # vertical strings inside the case — the shared proto, length linked at the
    # call site (an unlinked proto keeps the length it was first created with).
    proto = _ensure_string_proto(tree, "MEL_harp_string_unit", length_default=1.0)
    str_len = _m(tree, "MULTIPLY", (bx - 800, by - 5000), H, 0.78)
    str_r = _m(tree, "MULTIPLY", (bx - 800, by - 5140), W, 0.0022)
    if proto is not None:
        if proto.inputs.get("Length M") is not None:
            link_sockets(tree, str_len, proto.inputs["Length M"])
        if proto.inputs.get("Radius M") is not None:
            link_sockets(tree, str_r, proto.inputs["Radius M"])
    str_pts = _rank_axis(tree, (bx - 400, by - 5000), gin.outputs["String Count"], "x",
                         _m(tree, "MULTIPLY", (bx - 600, by - 5000), half_w, -0.86),
                         _step(tree, (bx - 800, by - 5200),
                               _m(tree, "MULTIPLY", (bx - 1000, by - 5200), W, 0.86),
                               gin.outputs["String Count"]).outputs[0],
                         y=_m(tree, "MULTIPLY", (bx - 600, by - 5340), D, 0.10),
                         z=_m(tree, "ADD", (bx - 600, by - 5480), LH,
                              _m(tree, "MULTIPLY", (bx - 800, by - 5480), str_len, 0.5)))
    strings = None
    if proto is not None and str_pts is not None:
        strings = _inst_rank(tree, (bx, by - 5000), str_pts, proto)

    # three pedals
    pedal = _plate(tree, (bx - 800, by - 6200),
                   _m(tree, "MULTIPLY", (bx - 1000, by - 6200), W, 0.05),
                   0.10, 0.022,
                   translation=_vec(tree, (bx - 1000, by - 6340), 0.0,
                                    _m(tree, "MULTIPLY", (bx - 1200, by - 6340), half_d, -1.10),
                                    0.03))
    pedals = _rank_inst(tree, (bx - 400, by - 6200), 3, pedal,
                        _m(tree, "MULTIPLY", (bx - 600, by - 6200), W, 0.13),
                        _m(tree, "MULTIPLY", (bx - 600, by - 6340), W, -0.065))

    geom = _join(tree, (bx + 400, by),
                 [case, top, fall, desk, kb, strings, pedals] + legs)

    _finish(tree, gin, gout, geom, (bx + 600, by), BID,
            _keys_attrs(tree, (bx + 400, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Tall Case + Lid", "nodes": ("Cube", "Transform"), "role": "geometry"},
        {"title": "Fallboard + Desk + Legs", "nodes": ("Cube", "Cylinder"), "role": "geometry"},
        {"title": "Keybed + Strings", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_harmonium
# ---------------------------------------------------------------------------

def build_music_harmonium(group_name="MEL_music_harmonium"):
    """Harmonium (reed organ): case on two side panels, keybed, a rank of 8
    drawstops on the front, 2 knee levers, a treadle pair, and a pleated
    feeder bellows behind.

    The drawstop rank and the bellows pleat stack are the two features that make
    this a reed organ and not a piano; the bellows reuses the wave-6 `_stand`
    graduation law with `spread=0.0` (uniform pleats, like the accordion).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_harmonium"
    bx, by = 0, 0

    add_float_param(tree, "Case Width M", 1.05, 0.6, 1.6)
    add_float_param(tree, "Case Depth M", 0.55, 0.3, 0.85)
    add_float_param(tree, "Case Height M", 0.78, 0.4, 1.1)
    add_float_param(tree, "Stand Height M", 0.45, 0.2, 0.7)
    add_int_param(tree, "White Key Count", 49, 24, 73)
    add_float_param(tree, "Key Depth M", 0.13, 0.06, 0.22)
    add_float_param(tree, "Key Height M", 0.021, 0.010, 0.045)
    add_int_param(tree, "Drawstop Count", 8, 4, 16)
    add_float_param(tree, "Bellows Depth M", 0.24, 0.10, 0.45)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    W = gin.outputs["Case Width M"]
    D = gin.outputs["Case Depth M"]
    H = gin.outputs["Case Height M"]
    SH = gin.outputs["Stand Height M"]
    KD = gin.outputs["Key Depth M"]
    KH = gin.outputs["Key Height M"]
    BD = gin.outputs["Bellows Depth M"]

    half_w = _m(tree, "MULTIPLY", (bx - 2000, by - 200), W, 0.5)
    half_d = _m(tree, "MULTIPLY", (bx - 2000, by - 340), D, 0.5)
    case_mid = _m(tree, "ADD", (bx - 2000, by - 480), SH,
                  _m(tree, "MULTIPLY", (bx - 2200, by - 480), H, 0.5))
    case_top = _m(tree, "ADD", (bx - 2000, by - 620), SH, H)

    case = _plate(tree, (bx - 1500, by), W, D, H,
                  translation=_vec(tree, (bx - 1500, by - 200), 0.0, 0.0, case_mid))

    # two side panels carrying the case (the gap holds the treadles)
    panels = []
    for i, sx in enumerate((-1.0, 1.0)):
        panels.append(_plate(
            tree, (bx - 1400 - i * 200, by - 900),
            _m(tree, "MULTIPLY", (bx - 1600 - i * 200, by - 900), W, 0.06),
            _m(tree, "MULTIPLY", (bx - 1600 - i * 200, by - 1040), D, 0.92),
            SH,
            translation=_vec(tree, (bx - 1600 - i * 200, by - 1040),
                             _m(tree, "MULTIPLY", (bx - 1800 - i * 200, by - 1040), half_w, sx * 0.94),
                             0.0,
                             _m(tree, "MULTIPLY", (bx - 1800 - i * 200, by - 1180), SH, 0.5))))

    # keybed on the case front
    kb = _keyboard(tree, (bx - 400, by - 1800), gin.outputs["White Key Count"],
                   _m(tree, "MULTIPLY", (bx - 800, by - 1800), W, 0.84),
                   None, KD, KH, case_top,
                   _m(tree, "ADD", (bx - 800, by - 1940),
                      _m(tree, "MULTIPLY", (bx - 1000, by - 1940), half_d, -1.0),
                      _m(tree, "MULTIPLY", (bx - 1000, by - 2080), KD, -0.45)))

    # drawstop rank: knobs sticking out of the front panel, marching along X
    knob = _cyl_y(tree, (bx - 1000, by - 2800),
                  _m(tree, "MULTIPLY", (bx - 1200, by - 2800), H, 0.028),
                  _m(tree, "MULTIPLY", (bx - 1200, by - 2940), D, 0.20),
                  0.0, verts=12)
    knob_geo = _xf(tree, (bx - 700, by - 2800), knob,
                   translation=_vec(tree, (bx - 900, by - 2940), 0.0,
                                    _m(tree, "ADD", (bx - 1100, by - 2940),
                                       _m(tree, "MULTIPLY", (bx - 1300, by - 2940), half_d, -1.0),
                                       _m(tree, "MULTIPLY", (bx - 1300, by - 3080), D, -0.06)),
                                    _m(tree, "ADD", (bx - 1100, by - 3080), SH,
                                       _m(tree, "MULTIPLY", (bx - 1300, by - 3080), H, 0.86)))
                   ).outputs["Geometry"]
    stops = _rank_inst(
        tree, (bx - 300, by - 2800), gin.outputs["Drawstop Count"], knob_geo,
        _m(tree, "MULTIPLY", (bx - 500, by - 2800), W, 0.62),
        _m(tree, "MULTIPLY", (bx - 500, by - 2940), W, -0.31))

    # two knee levers under the keybed
    lever = _plate(tree, (bx - 1000, by - 3600),
                   _m(tree, "MULTIPLY", (bx - 1200, by - 3600), W, 0.06),
                   _m(tree, "MULTIPLY", (bx - 1200, by - 3740), D, 0.34),
                   0.02,
                   translation=_vec(tree, (bx - 1200, by - 3740), 0.0,
                                    _m(tree, "MULTIPLY", (bx - 1400, by - 3740), half_d, -0.72),
                                    _m(tree, "ADD", (bx - 1400, by - 3880), case_top,
                                       _m(tree, "MULTIPLY", (bx - 1600, by - 3880), KH, -3.0))),
                   rotation=_vec(tree, (bx - 1200, by - 4020), math.radians(-14.0), 0.0, 0.0))
    levers = _rank_inst(tree, (bx - 300, by - 3600), 2, lever,
                        _m(tree, "MULTIPLY", (bx - 500, by - 3600), W, 0.30),
                        _m(tree, "MULTIPLY", (bx - 500, by - 3740), W, -0.15))

    # treadle pair at the floor
    treadle = _plate(tree, (bx - 1000, by - 4600),
                     _m(tree, "MULTIPLY", (bx - 1200, by - 4600), W, 0.34),
                     _m(tree, "MULTIPLY", (bx - 1200, by - 4740), D, 0.86),
                     0.02,
                     translation=_vec(tree, (bx - 1200, by - 4740), 0.0, 0.0,
                                      _m(tree, "MULTIPLY", (bx - 1400, by - 4740), SH, 0.16)),
                     rotation=_vec(tree, (bx - 1200, by - 4880), math.radians(8.0), 0.0, 0.0))
    treadles = _rank_inst(tree, (bx - 300, by - 4600), 2, treadle,
                          _m(tree, "MULTIPLY", (bx - 500, by - 4600), W, 0.40),
                          _m(tree, "MULTIPLY", (bx - 500, by - 4740), W, -0.20))

    # pleated feeder bellows behind the case — the accordion pleat law.
    # The proto's ORIGIN must be its own BOTTOM (`_stand` places about the
    # instance origin), and the 16 deg fold tilt means the plate's Z extent is
    # NOT just `pleat_w`: rotating about X mixes Y into Z. Lift by half the
    # ROTATED extent (w*cos16 + h*sin16) and seat the rank on the floor, or the
    # pleats sink through it (measured: bottom at z = -0.258 before the fix).
    pleat_h = _m(tree, "MULTIPLY", (bx - 2000, by - 5600), BD, 0.86)
    pleat_w = _m(tree, "MULTIPLY", (bx - 2000, by - 5740), W, 0.72)
    pleat_t = _m(tree, "MULTIPLY", (bx - 2000, by - 5880),
                _m(tree, "MULTIPLY", (bx - 2200, by - 5880), W, 0.72), 0.06)
    plate_node = safe_node(tree, "GeometryNodeMeshCube", (bx - 1500, by - 5600))
    if plate_node is not None:
        link_sockets(tree, _vec(tree, (bx - 1700, by - 5740), pleat_t, pleat_h, pleat_w),
                     sock(plate_node, "Size"))
    lift = _m(tree, "MULTIPLY", (bx - 1600, by - 6020),
              _m(tree, "ADD", (bx - 1800, by - 6020),
                 _m(tree, "MULTIPLY", (bx - 2000, by - 6020), pleat_w, 0.9613),
                 _m(tree, "MULTIPLY", (bx - 2200, by - 6160), pleat_h, 0.2756)),
              0.5)
    pleat_proto = _xf(tree, (bx - 1200, by - 5600), plate_node.outputs["Mesh"],
                      rotation=(math.radians(16.0), 0.0, 0.0),
                      translation=_vec(tree, (bx - 1400, by - 6020), 0.0, 0.0, lift)
                      ).outputs["Geometry"]
    bellows = _stand(tree, (bx - 400, by - 5600), gin.outputs["Drawstop Count"],
                     pleat_proto, _m(tree, "MULTIPLY", (bx - 600, by - 5600), W, 0.72),
                     0.0, spread=0.0)

    geom = _join(tree, (bx + 400, by),
                 [case, kb, stops, levers, treadles, bellows] + panels)

    _finish(tree, gin, gout, geom, (bx + 600, by), BID,
            _keys_attrs(tree, (bx + 400, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Case + Panels", "nodes": ("Cube", "Transform"), "role": "geometry"},
        {"title": "Keybed", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Drawstops + Levers + Bellows", "nodes": ("Cylinder", "Mesh Line"), "role": "instance"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_clavinet
# ---------------------------------------------------------------------------

def build_music_clavinet(group_name="MEL_music_clavinet"):
    """Clavinet: a THIN body on a stand, keybed, a short string rank and TWO
    pickup bars.

    The body is thin (no soundboard volume) and the pickups are bars under the
    strings — that is what separates it from the grand piano, whose body is a
    deep case. The gate asserts two bars with fully-linked `Size`.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_clavinet"
    bx, by = 0, 0

    add_float_param(tree, "Body Width M", 0.90, 0.5, 1.3)
    add_float_param(tree, "Body Depth M", 0.42, 0.25, 0.7)
    add_float_param(tree, "Body Height M", 0.12, 0.06, 0.25)
    add_float_param(tree, "Stand Height M", 0.66, 0.4, 0.95)
    add_int_param(tree, "White Key Count", 60, 24, 88)
    add_float_param(tree, "Key Depth M", 0.12, 0.06, 0.20)
    add_float_param(tree, "Key Height M", 0.020, 0.010, 0.045)
    add_int_param(tree, "String Count", 40, 8, 60)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    W = gin.outputs["Body Width M"]
    D = gin.outputs["Body Depth M"]
    H = gin.outputs["Body Height M"]
    SH = gin.outputs["Stand Height M"]
    KD = gin.outputs["Key Depth M"]
    KH = gin.outputs["Key Height M"]

    half_w = _m(tree, "MULTIPLY", (bx - 2000, by - 200), W, 0.5)
    half_d = _m(tree, "MULTIPLY", (bx - 2000, by - 340), D, 0.5)
    body_mid = _m(tree, "ADD", (bx - 2000, by - 480), SH,
                  _m(tree, "MULTIPLY", (bx - 2200, by - 480), H, 0.5))
    body_top = _m(tree, "ADD", (bx - 2000, by - 620), SH, H)

    body = _plate(tree, (bx - 1500, by), W, D, H,
                  translation=_vec(tree, (bx - 1500, by - 200), 0.0, 0.0, body_mid))

    # stand: four legs + a cross bar
    legs = []
    for i, (sx, sy) in enumerate(((-1.0, -1.0), (1.0, -1.0), (-1.0, 1.0), (1.0, 1.0))):
        legs.append(_cyl_z(tree, (bx - 1400 - i * 160, by - 900),
                           _m(tree, "MULTIPLY", (bx - 1600 - i * 160, by - 900), W, 0.016),
                           SH,
                           _m(tree, "MULTIPLY", (bx - 1600 - i * 160, by - 1040), SH, 0.5),
                           x=_m(tree, "MULTIPLY", (bx - 1600 - i * 160, by - 1180), half_w, sx * 0.88),
                           y=_m(tree, "MULTIPLY", (bx - 1600 - i * 160, by - 1320), half_d, sy * 0.82),
                           verts=12))
    cross = _plate(tree, (bx - 1200, by - 1600),
                   _m(tree, "MULTIPLY", (bx - 1400, by - 1600), W, 1.72), 0.02, 0.02,
                   translation=_vec(tree, (bx - 1400, by - 1740), 0.0,
                                    _m(tree, "MULTIPLY", (bx - 1600, by - 1740), half_d, -0.82),
                                    _m(tree, "MULTIPLY", (bx - 1600, by - 1880), SH, 0.30)))

    # keybed on the body front
    kb = _keyboard(tree, (bx - 400, by - 2200), gin.outputs["White Key Count"],
                   _m(tree, "MULTIPLY", (bx - 800, by - 2200), W, 0.88),
                   None, KD, KH, body_top,
                   _m(tree, "ADD", (bx - 800, by - 2340),
                      _m(tree, "MULTIPLY", (bx - 1000, by - 2340), half_d, -1.0),
                      _m(tree, "MULTIPLY", (bx - 1000, by - 2480), KD, -0.45)))

    # short string rank inside the thin body
    strings = _string_rank_y(
        tree, (bx - 400, by - 3200), gin.outputs["String Count"],
        _m(tree, "MULTIPLY", (bx - 800, by - 3200), W, 0.66),
        _m(tree, "MULTIPLY", (bx - 1000, by - 3200),
           _m(tree, "MULTIPLY", (bx - 1200, by - 3200), W, 0.66), -0.5),
        y=_m(tree, "MULTIPLY", (bx - 800, by - 3340), D, 0.04),
        z=_m(tree, "MULTIPLY", (bx - 800, by - 3480), H, 0.30),
        r_sock=_m(tree, "MULTIPLY", (bx - 800, by - 3620), W, 0.0020),
        len_sock=_m(tree, "MULTIPLY", (bx - 800, by - 3760), D, 0.80),
        spread=0.30)

    # two pickup bars under the strings — fully-linked Size on both
    bars = []
    for i, yf in enumerate((-0.22, 0.20)):
        bars.append(_plate(
            tree, (bx - 1000 - i * 300, by - 4200),
            _m(tree, "MULTIPLY", (bx - 1200 - i * 300, by - 4200), W, 0.70),
            0.022, 0.028,
            translation=_vec(tree, (bx - 1200 - i * 300, by - 4340), 0.0,
                             _m(tree, "MULTIPLY", (bx - 1400 - i * 300, by - 4340), D, yf),
                             _m(tree, "MULTIPLY", (bx - 1400 - i * 300, by - 4480), H, 0.12))))

    geom = _join(tree, (bx + 400, by),
                 [body, cross, kb, strings] + legs + bars)

    _finish(tree, gin, gout, geom, (bx + 600, by), BID,
            _keys_attrs(tree, (bx + 400, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Thin Body + Stand", "nodes": ("Cube", "Cylinder"), "role": "geometry"},
        {"title": "Keybed", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Strings + Pickup Bars", "nodes": ("Cylinder", "Cube"), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_mellotron
# ---------------------------------------------------------------------------

def build_music_mellotron(group_name="MEL_music_mellotron"):
    """Mellotron: a case on a stand, keybed, TWO tape reels standing behind the
    keys, two tape frame plates, and a rank of tape heads between them.

    The tape frames and reels are the instrument's identity — the notes are
    tapes, not strings, so there is no string rank here at all (the gate asserts
    the reel and head ranks exist instead).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_mellotron"
    bx, by = 0, 0

    add_float_param(tree, "Case Width M", 1.05, 0.6, 1.5)
    add_float_param(tree, "Case Depth M", 0.55, 0.3, 0.8)
    add_float_param(tree, "Case Height M", 0.18, 0.08, 0.35)
    add_float_param(tree, "Stand Height M", 0.70, 0.45, 0.95)
    add_int_param(tree, "White Key Count", 35, 24, 61)
    add_float_param(tree, "Key Depth M", 0.12, 0.06, 0.20)
    add_float_param(tree, "Key Height M", 0.020, 0.010, 0.045)
    add_float_param(tree, "Reel Radius M", 0.085, 0.04, 0.16)
    add_int_param(tree, "Tape Head Count", 35, 8, 61)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    W = gin.outputs["Case Width M"]
    D = gin.outputs["Case Depth M"]
    H = gin.outputs["Case Height M"]
    SH = gin.outputs["Stand Height M"]
    KD = gin.outputs["Key Depth M"]
    KH = gin.outputs["Key Height M"]
    RR = gin.outputs["Reel Radius M"]

    half_w = _m(tree, "MULTIPLY", (bx - 2000, by - 200), W, 0.5)
    half_d = _m(tree, "MULTIPLY", (bx - 2000, by - 340), D, 0.5)
    case_mid = _m(tree, "ADD", (bx - 2000, by - 480), SH,
                  _m(tree, "MULTIPLY", (bx - 2200, by - 480), H, 0.5))
    case_top = _m(tree, "ADD", (bx - 2000, by - 620), SH, H)

    case = _plate(tree, (bx - 1500, by), W, D, H,
                  translation=_vec(tree, (bx - 1500, by - 200), 0.0, 0.0, case_mid))

    # stand: four legs + a stretcher
    legs = []
    for i, (sx, sy) in enumerate(((-1.0, -1.0), (1.0, -1.0), (-1.0, 1.0), (1.0, 1.0))):
        legs.append(_cyl_z(tree, (bx - 1400 - i * 160, by - 900),
                           _m(tree, "MULTIPLY", (bx - 1600 - i * 160, by - 900), W, 0.015),
                           SH,
                           _m(tree, "MULTIPLY", (bx - 1600 - i * 160, by - 1040), SH, 0.5),
                           x=_m(tree, "MULTIPLY", (bx - 1600 - i * 160, by - 1180), half_w, sx * 0.90),
                           y=_m(tree, "MULTIPLY", (bx - 1600 - i * 160, by - 1320), half_d, sy * 0.86),
                           verts=12))
    stretcher = _plate(tree, (bx - 1200, by - 1600), W, 0.02, 0.02,
                       translation=_vec(tree, (bx - 1200, by - 1740), 0.0,
                                        _m(tree, "MULTIPLY", (bx - 1400, by - 1740), half_d, -0.86),
                                        _m(tree, "MULTIPLY", (bx - 1400, by - 1880), SH, 0.26)))

    # keybed on the case front
    kb = _keyboard(tree, (bx - 400, by - 2200), gin.outputs["White Key Count"],
                   _m(tree, "MULTIPLY", (bx - 800, by - 2200), W, 0.88),
                   None, KD, KH, case_top,
                   _m(tree, "ADD", (bx - 800, by - 2340),
                      _m(tree, "MULTIPLY", (bx - 1000, by - 2340), half_d, -1.0),
                      _m(tree, "MULTIPLY", (bx - 1000, by - 2480), KD, -0.45)))

    # two tape reels standing behind the keys (discs in the XZ plane)
    reel_z = _m(tree, "ADD", (bx - 2000, by - 3200), case_top,
                _m(tree, "MULTIPLY", (bx - 2200, by - 3200), RR, 0.95))
    reels = []
    for i, sx in enumerate((-1.0, 1.0)):
        reels.append(_disc_y(tree, (bx - 1400 - i * 200, by - 3200), RR, 0.030,
                             _m(tree, "MULTIPLY", (bx - 1600 - i * 200, by - 3200), D, 0.22),
                             x=_m(tree, "MULTIPLY", (bx - 1600 - i * 200, by - 3200), half_w, sx * 0.70),
                             z=reel_z, verts=32))

    # two tape frame plates flanking the reels
    frames = []
    for i, sx in enumerate((-1.0, 1.0)):
        frames.append(_plate(
            tree, (bx - 1200 - i * 260, by - 4000),
            0.020,
            _m(tree, "MULTIPLY", (bx - 1400 - i * 260, by - 4000), D, 0.70),
            _m(tree, "MULTIPLY", (bx - 1400 - i * 260, by - 4140), RR, 2.60),
            translation=_vec(tree, (bx - 1400 - i * 260, by - 4140),
                            _m(tree, "MULTIPLY", (bx - 1600 - i * 260, by - 4140), half_w, sx * 0.92),
                            _m(tree, "MULTIPLY", (bx - 1600 - i * 260, by - 4280), D, 0.18),
                            reel_z)))

    # tape head rank between the reels, marching along X
    head = _plate(tree, (bx - 1000, by - 4800),
                  _m(tree, "MULTIPLY", (bx - 1200, by - 4800), W, 0.016),
                  _m(tree, "MULTIPLY", (bx - 1200, by - 4940), D, 0.10),
                  _m(tree, "MULTIPLY", (bx - 1200, by - 5080), RR, 0.30),
                  translation=_vec(tree, (bx - 1200, by - 4940), 0.0,
                                   _m(tree, "MULTIPLY", (bx - 1400, by - 4940), D, 0.20),
                                   _m(tree, "ADD", (bx - 1400, by - 5080), case_top,
                                      _m(tree, "MULTIPLY", (bx - 1600, by - 5080), RR, 0.30))))
    heads = _rank_inst(tree, (bx - 300, by - 4800), gin.outputs["Tape Head Count"], head,
                       _m(tree, "MULTIPLY", (bx - 500, by - 4800), W, 0.70),
                       _m(tree, "MULTIPLY", (bx - 500, by - 4940), W, -0.35))

    geom = _join(tree, (bx + 400, by),
                 [case, stretcher, kb, heads] + legs + reels + frames)

    _finish(tree, gin, gout, geom, (bx + 600, by), BID,
            _keys_attrs(tree, (bx + 400, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Case + Stand", "nodes": ("Cube", "Cylinder"), "role": "geometry"},
        {"title": "Keybed", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Tape Reels + Frames + Heads", "nodes": ("Cylinder", "Cube"), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_tonewheel_organ
# ---------------------------------------------------------------------------

def build_music_tonewheel_organ(group_name="MEL_music_tonewheel_organ"):
    """Tonewheel organ console: plinth, console, TWO manuals, a rank of 9
    drawbars, a 13-note pedalboard, a swell pedal, and a rotating speaker drum
    in its own cabinet.

    The two manuals + drawbar rank + pedalboard are what make it a drawbar
    console; `MEL_music_baroque_organ` is a walkable pipe FACADE and
    `MEL_music_organ_pipes` is its ET pipe rank, so neither is this id.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    BID = "MEL_music_tonewheel_organ"
    bx, by = 0, 0

    add_float_param(tree, "Case Width M", 1.15, 0.6, 1.7)
    add_float_param(tree, "Case Depth M", 0.65, 0.35, 1.0)
    add_float_param(tree, "Case Height M", 0.72, 0.4, 1.1)
    add_float_param(tree, "Plinth Height M", 0.10, 0.04, 0.25)
    add_int_param(tree, "White Key Count", 44, 24, 61)
    add_float_param(tree, "Key Depth M", 0.13, 0.06, 0.22)
    add_float_param(tree, "Key Height M", 0.021, 0.010, 0.045)
    add_int_param(tree, "Drawbar Count", 9, 4, 12)
    add_int_param(tree, "Pedal Count", 13, 8, 25)
    add_float_param(tree, "Drum Radius M", 0.16, 0.08, 0.3)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    W = gin.outputs["Case Width M"]
    D = gin.outputs["Case Depth M"]
    H = gin.outputs["Case Height M"]
    PH = gin.outputs["Plinth Height M"]
    KD = gin.outputs["Key Depth M"]
    KH = gin.outputs["Key Height M"]
    DR = gin.outputs["Drum Radius M"]

    half_w = _m(tree, "MULTIPLY", (bx - 2000, by - 200), W, 0.5)
    half_d = _m(tree, "MULTIPLY", (bx - 2000, by - 340), D, 0.5)
    case_mid = _m(tree, "ADD", (bx - 2000, by - 480), PH,
                  _m(tree, "MULTIPLY", (bx - 2200, by - 480), H, 0.5))
    case_top = _m(tree, "ADD", (bx - 2000, by - 620), PH, H)
    upper_z = _m(tree, "ADD", (bx - 2000, by - 760), case_top,
                 _m(tree, "MULTIPLY", (bx - 2200, by - 760), KH, 1.6))

    plinth = _plate(tree, (bx - 1500, by),
                    _m(tree, "MULTIPLY", (bx - 1700, by), W, 1.06),
                    _m(tree, "MULTIPLY", (bx - 1700, by - 140), D, 1.06),
                    PH,
                    translation=_vec(tree, (bx - 1500, by - 140), 0.0, 0.0,
                                     _m(tree, "MULTIPLY", (bx - 1700, by - 140), PH, 0.5)))
    console = _plate(tree, (bx - 1500, by - 800), W, D, H,
                     translation=_vec(tree, (bx - 1500, by - 1000), 0.0, 0.0, case_mid))

    # lower manual (front) and upper manual (set back and raised)
    kb_lower = _keyboard(
        tree, (bx - 400, by - 1600), gin.outputs["White Key Count"],
        _m(tree, "MULTIPLY", (bx - 800, by - 1600), W, 0.86),
        None, KD, KH, case_top,
        _m(tree, "ADD", (bx - 800, by - 1740),
           _m(tree, "MULTIPLY", (bx - 1000, by - 1740), half_d, -1.0),
           _m(tree, "MULTIPLY", (bx - 1000, by - 1880), KD, -0.48)))
    kb_upper = _keyboard(
        tree, (bx - 400, by - 2600), gin.outputs["White Key Count"],
        _m(tree, "MULTIPLY", (bx - 800, by - 2600), W, 0.86),
        None, KD, KH, upper_z,
        _m(tree, "ADD", (bx - 800, by - 2740),
           _m(tree, "MULTIPLY", (bx - 1000, by - 2740), half_d, -1.0),
           _m(tree, "MULTIPLY", (bx - 1000, by - 2880), KD, -0.06)))

    # drawbar rank on the upper panel, standing up in +Z
    bar = _cyl_z(tree, (bx - 1000, by - 3600),
                 _m(tree, "MULTIPLY", (bx - 1200, by - 3600), W, 0.010),
                 _m(tree, "MULTIPLY", (bx - 1200, by - 3740), KH, 2.4),
                 _m(tree, "MULTIPLY", (bx - 1200, by - 3880),
                    _m(tree, "MULTIPLY", (bx - 1400, by - 3880), KH, 2.4), 0.5),
                 y=_m(tree, "MULTIPLY", (bx - 1200, by - 4020), half_d, -1.0),
                 verts=10)
    bar_geo = _xf(tree, (bx - 700, by - 3600), bar,
                  translation=_vec(tree, (bx - 900, by - 3880), 0.0, 0.0,
                                   _m(tree, "ADD", (bx - 1100, by - 3880), case_top,
                                      _m(tree, "MULTIPLY", (bx - 1300, by - 3880), H, 0.14)))
                  ).outputs["Geometry"]
    drawbars = _rank_inst(
        tree, (bx - 300, by - 3600), gin.outputs["Drawbar Count"], bar_geo,
        _m(tree, "MULTIPLY", (bx - 500, by - 3600), W, 0.30),
        _m(tree, "MULTIPLY", (bx - 500, by - 3740), W, -0.15))

    # pedalboard: a rank of wide short keys at the floor, in front
    pedal = _plate(tree, (bx - 1000, by - 4800),
                   _m(tree, "MULTIPLY", (bx - 1200, by - 4800), W, 0.062),
                   _m(tree, "MULTIPLY", (bx - 1200, by - 4940), D, 0.52),
                   0.028,
                   translation=_vec(tree, (bx - 1200, by - 4940), 0.0,
                                    _m(tree, "MULTIPLY", (bx - 1400, by - 4940), half_d, -1.06),
                                    0.02))
    pedals = _rank_inst(tree, (bx - 300, by - 4800), gin.outputs["Pedal Count"], pedal,
                        _m(tree, "MULTIPLY", (bx - 500, by - 4800), W, 0.78),
                        _m(tree, "MULTIPLY", (bx - 500, by - 4940), W, -0.39))

    # swell pedal
    swell = _plate(tree, (bx - 1000, by - 5600),
                   _m(tree, "MULTIPLY", (bx - 1200, by - 5600), W, 0.12), 0.16, 0.024,
                   translation=_vec(tree, (bx - 1200, by - 5740), 0.0,
                                    _m(tree, "MULTIPLY", (bx - 1400, by - 5740), half_d, -1.20),
                                    0.03),
                   rotation=_vec(tree, (bx - 1200, by - 5880), math.radians(-12.0), 0.0, 0.0))

    # rotating speaker drum in its own cabinet beside the console
    cab_x = _m(tree, "MULTIPLY", (bx - 2000, by - 6400), W, 0.80)
    cabinet = _plate(tree, (bx - 1500, by - 6400),
                     _m(tree, "MULTIPLY", (bx - 1700, by - 6400), W, 0.34),
                     _m(tree, "MULTIPLY", (bx - 1700, by - 6540), W, 0.36),
                     _m(tree, "MULTIPLY", (bx - 1700, by - 6680), W, 0.86),
                     translation=_vec(tree, (bx - 1700, by - 6540), cab_x, 0.0,
                                      _m(tree, "MULTIPLY", (bx - 1900, by - 6680), W, 0.43)))
    drum = _cyl_z(tree, (bx - 1200, by - 7000),
                  DR, _m(tree, "MULTIPLY", (bx - 1400, by - 7000), W, 0.28),
                  _m(tree, "MULTIPLY", (bx - 1400, by - 7140), W, 0.62),
                  x=cab_x, verts=32)

    geom = _join(tree, (bx + 400, by),
                 [plinth, console, kb_lower, kb_upper, drawbars, pedals,
                  swell, cabinet, drum])

    _finish(tree, gin, gout, geom, (bx + 600, by), BID,
            _keys_attrs(tree, (bx + 400, by - 300)))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Plinth + Console", "nodes": ("Cube", "Transform"), "role": "geometry"},
        {"title": "Two Manuals", "nodes": ("Mesh Line", "Instance on Points"), "role": "instance"},
        {"title": "Drawbars + Pedalboard", "nodes": ("Cylinder", "Cube"), "role": "instance"},
        {"title": "Speaker Cabinet + Drum", "nodes": ("Cube", "Cylinder"), "role": "geometry"},
        {"title": "Export", "nodes": ("Realize Instances", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

register_builder(
    "MEL_music_grand_piano", build_music_grand_piano, "Grand Piano",
    "Case + curved bentside + tilted lid + 3 legs + 52-key keybed + graduated "
    "string rank + 3 pedals.", category="music")

register_builder(
    "MEL_music_upright_piano", build_music_upright_piano, "Upright Piano",
    "Tall case + fallboard + music desk + keybed + vertical string rank + "
    "3 pedals.", category="music")

register_builder(
    "MEL_music_harmonium", build_music_harmonium, "Harmonium",
    "Reed-organ case on side panels + keybed + 8 drawstops + knee levers + "
    "treadles + pleated feeder bellows.", category="music")

register_builder(
    "MEL_music_clavinet", build_music_clavinet, "Clavinet",
    "Thin body on a stand + keybed + short string rank + 2 pickup bars.",
    category="music")

register_builder(
    "MEL_music_mellotron", build_music_mellotron, "Mellotron",
    "Case on a stand + keybed + 2 tape reels + 2 tape frames + a rank of tape "
    "heads.", category="music")

register_builder(
    "MEL_music_tonewheel_organ", build_music_tonewheel_organ, "Tonewheel Organ",
    "Drawbar console: plinth + 2 manuals + 9 drawbars + 13-note pedalboard + "
    "swell pedal + rotating speaker drum.", category="music")
