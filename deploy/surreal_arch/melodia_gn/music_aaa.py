"""AAA musical geometry GN builders - ZBrush IMM-ready kit (Blender 5.2 APIs).

Eight production builders pushing the music category into AAA territory:
waveform wall, vinyl disc, lissajous harp, piano key row, frequency ribcage,
tuning fork column, metronome pillar, soundhole rosette.

Conventions: base at Z=0, uniform Scale applied last, named attributes stored,
every builder links its result into Group Output. IMM-friendly: tubes swept via
CurveToMesh with Fill Caps=True (closed ends).
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node,
    label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param,
)


# ── Local helpers (Blender 5.2-safe) ────────────────────────────────────

def _out(node, name=None):
    if node is None:
        return None
    if name:
        s = node.outputs.get(name)
        if s:
            return s
    return node.outputs[0] if node.outputs else None


def _in(node, name):
    if node is None:
        return None
    return node.inputs.get(name)


def _math(tree, loc, op, a=None, b=None, b_val=None):
    n = safe_node(tree, "ShaderNodeMath", loc)
    if n is None:
        return None
    try:
        n.operation = op
    except Exception:
        return None
    if _is_sock(a):
        link_sockets(tree, a, n.inputs[0])
    elif isinstance(a, (int, float)) and not isinstance(a, bool):
        n.inputs[0].default_value = a
    if _is_sock(b):
        link_sockets(tree, b, n.inputs[1])
    elif b_val is not None:
        n.inputs[1].default_value = b_val
    return n


def _bool(tree, loc, op, a=None, b=None):
    n = safe_node(tree, "FunctionNodeBooleanMath", loc)
    if n is None:
        return None
    try:
        n.operation = op
    except Exception:
        return None
    if _is_sock(a):
        link_sockets(tree, a, n.inputs[0])
    if _is_sock(b):
        link_sockets(tree, b, n.inputs[1])
    return n


def _is_sock(v):
    return v is not None and hasattr(v, "is_output")


def _vec(tree, loc, x=None, y=None, z=None):
    n = safe_node(tree, "ShaderNodeCombineXYZ", loc)
    if n is None:
        return None
    for comp, sock in (("X", x), ("Y", y), ("Z", z)):
        if _is_sock(sock):
            link_sockets(tree, sock, n.inputs[comp])
    return n


def _xf(tree, loc, geo, loc_v=None, rot=None, scale=None):
    n = safe_node(tree, "GeometryNodeTransform", loc)
    if n is None:
        return None
    if geo is not None:
        link_sockets(tree, geo, n.inputs["Geometry"])
    if _is_sock(loc_v):
        link_sockets(tree, loc_v, n.inputs["Translation"])
    elif isinstance(loc_v, (tuple, list)):
        try:
            n.inputs["Translation"].default_value = loc_v
        except Exception:
            pass
    if rot is not None:
        try:
            n.inputs["Rotation"].default_value = rot
        except Exception:
            pass
    if _is_sock(scale):
        link_sockets(tree, scale, n.inputs["Scale"])
    elif isinstance(scale, (tuple, list)):
        try:
            n.inputs["Scale"].default_value = scale
        except Exception:
            pass
    return n


def _sock(v):
    """Normalize node -> its first output socket; pass sockets through."""
    if v is None:
        return None
    if hasattr(v, "outputs") and not hasattr(v, "is_output"):
        return v.outputs[0] if v.outputs else None
    return v


def _point_line(tree, loc, count_sock, start=(0, 0, 0), step=None, step_sock=None):
    """Line of points via OFFSET mode (Blender 5.2 MeshLine: Count/Start/Offset)."""
    line = safe_node(tree, "GeometryNodeMeshLine", loc)
    if line is None:
        return None
    try:
        line.mode = "OFFSET"
    except Exception:
        pass
    cs = _sock(count_sock)
    if cs is not None:
        link_sockets(tree, cs, _in(line, "Count"))
    sv = _in(line, "Start Location")
    if sv is not None:
        sv.default_value = start
    off = _in(line, "Offset")
    if off is not None:
        ss = _sock(step_sock)
        if ss is not None:
            link_sockets(tree, ss, off)
        elif step is not None:
            off.default_value = step
    return line


def _tube(tree, loc, curve_sock, radius_sock, radius_val=0.02, verts=8, fill_caps=True,
          mesh_source=False):
    """Sweep a curve into a capped tube (IMM-safe closed ends).

    mesh_source=True inserts MeshToCurve first (for MeshLine/SetPosition sources).
    """
    if curve_sock is None:
        return None
    src = curve_sock
    if mesh_source:
        m2c = safe_node(tree, "GeometryNodeMeshToCurve", (loc[0] - 120, loc[1] + 90))
        if m2c is None:
            return None
        mesh_in = _in(m2c, "Mesh") or _in(m2c, "Geometry")
        link_sockets(tree, curve_sock, mesh_in)
        src = m2c.outputs["Curve"]
    prof = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (loc[0] - 200, loc[1] - 80))
    c2m = safe_node(tree, "GeometryNodeCurveToMesh", loc)
    if prof is None or c2m is None:
        return None
    prof.inputs["Resolution"].default_value = verts
    rad_in = _in(prof, "Radius")
    if rad_in is not None:
        if radius_sock is not None:
            link_sockets(tree, radius_sock, rad_in)
        else:
            rad_in.default_value = radius_val
    # profile circle lies in XY by default; rotate to stand across the curve
    prof_xf = _xf(tree, (loc[0] - 100, loc[1] - 160), prof.outputs["Curve"],
                  rot=(math.radians(90), 0, 0))
    prof_geo = prof_xf.outputs["Geometry"] if prof_xf else prof.outputs["Curve"]
    link_sockets(tree, src, _in(c2m, "Curve"))
    link_sockets(tree, prof_geo, _in(c2m, "Profile Curve"))
    try:
        c2m.inputs["Fill Caps"].default_value = fill_caps
    except Exception:
        pass
    return c2m.outputs["Mesh"]


def _torus(tree, loc, major_sock, major_mult, minor_sock, minor_mult, major_seg=64, minor_seg=12):
    """Torus without a native node: big circle swept by small circle."""
    outer = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (loc[0] - 300, loc[1]))
    inner = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (loc[0] - 300, loc[1] - 120))
    if outer is None or inner is None:
        return None
    outer.inputs["Resolution"].default_value = major_seg
    inner.inputs["Resolution"].default_value = minor_seg
    mo = _math(tree, (loc[0] - 480, loc[1]), "MULTIPLY", a=major_sock, b_val=major_mult)
    mi = _math(tree, (loc[0] - 480, loc[1] - 140), "MULTIPLY", a=minor_sock, b_val=minor_mult)
    if mo:
        link_sockets(tree, mo.outputs[0], _in(outer, "Radius"))
    if mi:
        link_sockets(tree, mi.outputs[0], _in(inner, "Radius"))
    # minor circle must stand perpendicular: rotate 90deg Y
    inner_xf = _xf(tree, (loc[0] - 120, loc[1] - 60), inner.outputs["Curve"],
                   rot=(0, math.radians(90), 0))
    prof_curve = inner_xf.outputs["Geometry"] if inner_xf else inner.outputs["Curve"]
    c2m = safe_node(tree, "GeometryNodeCurveToMesh", (loc[0] + 100, loc[1]))
    if c2m is None:
        return None
    link_sockets(tree, outer.outputs["Curve"], _in(c2m, "Curve"))
    link_sockets(tree, prof_curve, _in(c2m, "Profile Curve"))
    try:
        c2m.inputs["Fill Caps"].default_value = False
    except Exception:
        pass
    return c2m.outputs["Mesh"]


def _realize(tree, loc, geo):
    """Realize instances - sets 'Realize All' (Blender 5.2+ input, default False)."""
    rl = safe_node(tree, "GeometryNodeRealizeInstances", loc)
    if rl is None:
        return geo
    link_sockets(tree, geo, rl.inputs["Geometry"])
    ra = _in(rl, "Realize All")
    if ra is not None:
        try:
            ra.default_value = True
        except Exception:
            pass
    return rl.outputs["Geometry"]


def _finish(tree, gin, gout, geo, loc, smooth=True):
    """Shade + uniform scale + MANDATORY link into Group Output."""
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", loc)
    src = geo
    if shade is not None and geo is not None:
        link_sockets(tree, geo, shade.inputs["Geometry"])
        try:
            shade.inputs["Shade Smooth"].default_value = smooth
        except Exception:
            pass
        src = shade.outputs["Geometry"]
    vec = safe_node(tree, "ShaderNodeCombineXYZ", (loc[0], loc[1] - 90))
    xf = safe_node(tree, "GeometryNodeTransform", (loc[0] + 180, loc[1]))
    if xf is not None and src is not None:
        link_sockets(tree, src, xf.inputs["Geometry"])
        if vec is not None:
            for comp in ("X", "Y", "Z"):
                link_sockets(tree, gin.outputs["Scale"], vec.inputs[comp])
            link_sockets(tree, vec.outputs["Vector"], xf.inputs["Scale"])
        src = xf.outputs["Geometry"]
    if src is not None and gout is not None:
        link_sockets(tree, src, _in(gout, "Geometry"))


def _lift_to_floor(tree, geo, height_sock, height_mult, loc):
    """Translate geometry up so its base sits at Z=0 (for centered primitives)."""
    half = _math(tree, (loc[0] - 150, loc[1] - 70), "MULTIPLY", a=height_sock, b_val=height_mult * 0.5)
    v = _vec(tree, (loc[0], loc[1] - 130), z=half.outputs[0] if half else None)
    xf = safe_node(tree, "GeometryNodeTransform", (loc[0] + 150, loc[1]))
    if xf and v:
        link_sockets(tree, geo, xf.inputs["Geometry"])
        link_sockets(tree, v.outputs["Vector"], xf.inputs["Translation"])
        return xf.outputs["Geometry"]
    return geo


# ────────────────────────────────────────────────────────────────────────
# 1. Waveform Wall
# ────────────────────────────────────────────────────────────────────────

def build_music_waveform_wall(group_name="MEL_music_waveform_wall"):
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Width", 4.0, 0.5, 20.0)
    add_float_param(tree, "Amplitude", 0.5, 0.05, 3.0)
    add_float_param(tree, "Base Freq", 6.0, 1.0, 40.0)
    add_float_param(tree, "Harmonic Blend", 0.5, 0.0, 1.0)
    add_int_param(tree, "Resolution", 128, 16, 512)
    add_float_param(tree, "Thickness", 0.04, 0.01, 0.3)
    add_float_param(tree, "Scale", 1.0, 0.1, 5.0)

    # Straight line along X centred on origin: start=-W/2, offset=+W
    neg_half = _math(tree, (-700, 260), "MULTIPLY", a=gin.outputs["Width"], b_val=-0.5)
    start_v = _vec(tree, (-560, 320), x=neg_half.outputs[0] if neg_half else None)
    off_v = _vec(tree, (-560, 200), x=gin.outputs["Width"])
    line = _point_line(tree, (-380, 300), gin.outputs["Resolution"],
                       start=(0, 0, 0), step=None, step_sock=off_v)
    if line and start_v:
        link_sockets(tree, start_v.outputs["Vector"], _in(line, "Start Location"))

    spl = safe_node(tree, "GeometryNodeSplineParameter", (-380, 480))
    factor = _out(spl, "Factor")

    def layer(loc_y, mult, blend_param, blend_default):
        tm = _math(tree, (-180, loc_y), "MULTIPLY", a=factor, b_val=mult * math.tau)
        sn = _math(tree, (-20, loc_y), "SINE")
        if tm and sn:
            link_sockets(tree, tm.outputs[0], sn.inputs[0])
            amp = _math(tree, (150, loc_y), "MULTIPLY",
                        a=sn.outputs[0],
                        b=gin.outputs[blend_param] if blend_param else None,
                        b_val=blend_default)
            return _math(tree, (320, loc_y), "MULTIPLY",
                         a=amp.outputs[0] if amp else None, b=gin.outputs["Amplitude"])
        return None

    l1 = layer(560, 1.0, None, 1.0)
    l2 = layer(430, 2.0, "Harmonic Blend", 0.5)
    l3 = layer(300, 4.0, "Harmonic Blend", 0.25)

    sum_a = _math(tree, (520, 520), "ADD", a=l1, b=l2)
    total = _math(tree, (660, 480), "ADD",
                  a=sum_a.outputs[0] if sum_a else l1, b=l3)

    disp = _vec(tree, (820, 460), z=total.outputs[0] if total else None)
    set_pos = safe_node(tree, "GeometryNodeSetPosition", (980, 400))
    if set_pos and line:
        link_sockets(tree, line.outputs["Mesh"], set_pos.inputs["Geometry"])
        if disp:
            link_sockets(tree, disp.outputs["Vector"], set_pos.inputs["Offset"])

    body = _tube(tree, (1180, 380), set_pos.outputs["Geometry"] if set_pos else None,
                 gin.outputs["Thickness"], verts=6, fill_caps=True, mesh_source=True)
    _finish(tree, gin, gout, body, (1450, 380))

    color_node(line, "curve")
    color_node(set_pos, "geometry")
    return label_tree(tree, "MEL_music_waveform_wall", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Additive Harmonics", "nodes": ("math", "sine"), "role": "math"},
        {"title": "Displaced Ribbon", "nodes": ("set position", "tube"), "role": "geometry"},
        {"title": "Output", "nodes": ("shade", "transform", "Group Output"), "role": "output"},
    ])


# ────────────────────────────────────────────────────────────────────────
# 2. Vinyl Disc
# ────────────────────────────────────────────────────────────────────────

def build_music_vinyl_disc(group_name="MEL_music_vinyl_disc"):
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Radius", 1.0, 0.3, 4.0)
    add_float_param(tree, "Thickness", 0.03, 0.005, 0.2)
    add_int_param(tree, "Grooves", 48, 8, 200)
    add_bool_param(tree, "Has Label", True)
    add_bool_param(tree, "Spindle Hole", True)
    add_float_param(tree, "Scale", 1.0, 0.1, 5.0)

    parts = []
    disc = safe_node(tree, "GeometryNodeMeshCylinder", (-600, 420))
    if disc:
        disc.inputs["Vertices"].default_value = 96
        disc.fill_type = "NGON"
        link_sockets(tree, gin.outputs["Radius"], _in(disc, "Radius"))
        link_sockets(tree, gin.outputs["Thickness"], _in(disc, "Depth"))
        parts.append(_lift_to_floor(tree, disc.outputs["Mesh"], gin.outputs["Thickness"], 1.0, (-350, 420)))

    # Groove spiral standing on top face
    spiral = safe_node(tree, "GeometryNodeCurveSpiral", (-600, 180))
    inner_r = _math(tree, (-790, 240), "MULTIPLY", a=gin.outputs["Radius"], b_val=0.38)
    outer_r = _math(tree, (-790, 140), "MULTIPLY", a=gin.outputs["Radius"], b_val=0.96)
    if spiral:
        spiral.inputs["Height"].default_value = 0.0
        spiral.inputs["Resolution"].default_value = 256
        link_sockets(tree, gin.outputs["Grooves"], _in(spiral, "Rotations"))
        if inner_r:
            link_sockets(tree, inner_r.outputs[0], _in(spiral, "Start Radius"))
        if outer_r:
            link_sockets(tree, outer_r.outputs[0], _in(spiral, "End Radius"))
        flat = _xf(tree, (-380, 200), spiral.outputs["Curve"], rot=(math.radians(90), 0, 0))
        top_z = _math(tree, (-380, 110), "MULTIPLY", a=gin.outputs["Thickness"], b_val=1.05)
        zv = _vec(tree, (-210, 120), z=top_z.outputs[0] if top_z else None)
        sp_pos = safe_node(tree, "GeometryNodeSetPosition", (-60, 180))
        if flat and sp_pos:
            link_sockets(tree, flat.outputs["Geometry"], sp_pos.inputs["Geometry"])
            if zv:
                link_sockets(tree, zv.outputs["Vector"], sp_pos.inputs["Offset"])
        groove = _tube(tree, (160, 180), sp_pos.outputs["Geometry"] if sp_pos else None,
                       None, radius_val=0.0025, verts=5, fill_caps=False)
        if groove:
            parts.append(groove)

    join1 = safe_node(tree, "GeometryNodeJoinGeometry", (450, 300))
    if join1:
        for p in [p for p in parts if p]:
            link_sockets(tree, p, join1.inputs["Geometry"])

    result = join1.outputs["Geometry"] if join1 else None

    # Label
    lbl_switch = safe_node(tree, "GeometryNodeSwitch", (650, 300))
    if lbl_switch and result:
        try:
            lbl_switch.input_type = "GEOMETRY"
        except Exception:
            pass
        link_sockets(tree, gin.outputs["Has Label"], _in(lbl_switch, "Switch"))
        lbl = safe_node(tree, "GeometryNodeMeshCylinder", (-600, -40))
        if lbl:
            lbl.inputs["Vertices"].default_value = 64
            lbl.fill_type = "NGON"
            lr = _math(tree, (-790, 0), "MULTIPLY", a=gin.outputs["Radius"], b_val=0.34)
            lt = _math(tree, (-790, -90), "MULTIPLY", a=gin.outputs["Thickness"], b_val=2.2)
            if lr:
                link_sockets(tree, lr.outputs[0], _in(lbl, "Radius"))
            if lt:
                link_sockets(tree, lt.outputs[0], _in(lbl, "Depth"))
            lifted = _lift_to_floor(tree, lbl.outputs["Mesh"], lt.outputs[0] if lt else None, 1.0, (-350, -40))
            link_sockets(tree, lifted, _true_socket(lbl_switch) if hasattr(lbl_switch, "inputs") else None)
        t_out = _out(lbl_switch, "Output") or (lbl_switch.outputs[0] if lbl_switch.outputs else None)
        j2 = safe_node(tree, "GeometryNodeJoinGeometry", (850, 300))
        if j2:
            link_sockets(tree, result, j2.inputs["Geometry"])
            if t_out:
                link_sockets(tree, t_out, j2.inputs["Geometry"])
            result = j2.outputs["Geometry"]

    # Spindle hole
    hole_switch = safe_node(tree, "GeometryNodeSwitch", (1050, 300))
    if hole_switch and result:
        try:
            hole_switch.input_type = "GEOMETRY"
        except Exception:
            pass
        link_sockets(tree, gin.outputs["Spindle Hole"], _in(hole_switch, "Switch"))
        hole = safe_node(tree, "GeometryNodeMeshCylinder", (-600, -280))
        cut = None
        if hole:
            hole.inputs["Vertices"].default_value = 20
            hole.fill_type = "NGON"
            hr = _math(tree, (-790, -240), "MULTIPLY", a=gin.outputs["Radius"], b_val=0.007)
            if hr:
                link_sockets(tree, hr.outputs[0], _in(hole, "Radius"))
            hole.inputs["Depth"].default_value = 4.0
            bl = safe_node(tree, "GeometryNodeMeshBoolean", (500, -280))
            if bl:
                bl.operation = "DIFFERENCE"
                link_sockets(tree, result, bl.inputs[0])
                link_sockets(tree, hole.outputs["Mesh"], bl.inputs[1])
                cut = bl.outputs[0]
        if hasattr(hole_switch, "inputs"):
            ts = _true_socket(hole_switch)
            if ts:
                link_sockets(tree, cut or result, ts)
        fs = _false_socket(hole_switch)
        if fs:
            link_sockets(tree, result, fs)
        result = _out(hole_switch, "Output") or (hole_switch.outputs[0] if hole_switch.outputs else None)

    _finish(tree, gin, gout, result, (1300, 300))

    color_node(disc, "geometry")
    color_node(spiral, "curve")
    return label_tree(tree, "MEL_music_vinyl_disc", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Disc And Grooves", "nodes": ("disc", "spiral"), "role": "geometry"},
        {"title": "Label And Hole", "nodes": ("switch", "boolean"), "role": "instance"},
        {"title": "Output", "nodes": ("shade", "transform", "Group Output"), "role": "output"},
    ])


def _true_socket(node):
    return node.inputs.get("True") or node.inputs.get("TRUE") or (
        node.inputs[1] if len(node.inputs) > 1 else None)


def _false_socket(node):
    return node.inputs.get("False") or node.inputs.get("FALSE") or (
        node.inputs[0] if node.inputs else None)


# ────────────────────────────────────────────────────────────────────────
# 3. Lissajous Harp
# ────────────────────────────────────────────────────────────────────────

def build_music_lissajous_harp(group_name="MEL_music_lissajous_harp"):
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Height", 3.0, 1.0, 10.0)
    add_float_param(tree, "Width", 1.6, 0.5, 6.0)
    add_float_param(tree, "Thickness", 0.06, 0.01, 0.3)
    add_float_param(tree, "String Gauge", 0.012, 0.002, 0.06)
    add_float_param(tree, "Scale", 1.0, 0.1, 5.0)

    parts = []

    # Soundbox plinth
    bw = _math(tree, (-800, 120), "MULTIPLY", a=gin.outputs["Width"], b_val=1.35)
    bh = _math(tree, (-800, 30), "MULTIPLY", a=gin.outputs["Height"], b_val=0.22)
    box = safe_node(tree, "GeometryNodeMeshCube", (-560, 100))
    if box:
        sz = _vec(tree, (-700, 60), x=bw.outputs[0] if bw else None,
                  y=gin.outputs["Thickness"], z=bh.outputs[0] if bh else None)
        if sz:
            link_sockets(tree, sz.outputs["Vector"], _in(box, "Size"))
        lifted = _lift_to_floor(tree, box.outputs["Mesh"], bh.outputs[0] if bh else None, 1.0, (-330, 100))
        if lifted:
            parts.append(lifted)

    # Arc frame pillar
    hw45 = _math(tree, (-800, 420), "MULTIPLY", a=gin.outputs["Width"], b_val=-0.55)
    hh24 = _math(tree, (-800, 340), "MULTIPLY", a=gin.outputs["Height"], b_val=0.24)
    hx12 = _math(tree, (-800, 260), "MULTIPLY", a=gin.outputs["Width"], b_val=-0.18)
    eh98 = _math(tree, (-800, 180), "MULTIPLY", a=gin.outputs["Height"], b_val=0.98)
    start_v = _vec(tree, (-620, 470), x=hw45.outputs[0] if hw45 else None,
                   y=hh24.outputs[0] if hh24 else None, z=0)
    ctrl_v = _vec(tree, (-620, 400), x=hx12.outputs[0] if hx12 else None,
                  y=hh24.outputs[0] if hh24 else None, z=eh98.outputs[0] if eh98 else None)
    end_v = _vec(tree, (-620, 330), x=hw45.outputs[0] if hw45 else None,
                 y=hh24.outputs[0] if hh24 else None, z=eh98.outputs[0] if eh98 else None)
    frame_bez = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (-400, 420))
    if frame_bez and all((start_v, ctrl_v, end_v)):
        link_sockets(tree, start_v.outputs["Vector"], _in(frame_bez, "Start"))
        link_sockets(tree, start_v.outputs["Vector"], _in(frame_bez, "Start Handle"))
        link_sockets(tree, ctrl_v.outputs["Vector"], _in(frame_bez, "End Handle"))
        link_sockets(tree, end_v.outputs["Vector"], _in(frame_bez, "End"))
        frame = _tube(tree, (-100, 420), frame_bez.outputs["Curve"],
                      gin.outputs["Thickness"], verts=8, fill_caps=True)
        if frame:
            parts.append(frame)

    # Lissajous string web standing upright
    try:
        from .profiles import build_lissajous_curve
        web_name = "MEL_lissajous"
        if web_name not in bpy.data.node_groups:
            try:
                build_lissajous_curve(web_name)
            except Exception:
                pass
        web_grp = safe_node(tree, "GeometryNodeGroup", (-560, 640))
        if web_grp and web_name in bpy.data.node_groups:
            web_grp.node_tree = bpy.data.node_groups[web_name]
            for nm, val in (("A", 0.95), ("B", 1.35), ("Steps", 96)):
                sock = web_grp.inputs.get(nm)
                if sock is not None:
                    sock.default_value = val
            web_tube = _tube(tree, (-260, 640), _out(web_grp, "Geometry"),
                             gin.outputs["String Gauge"], verts=4, fill_caps=False)
            if web_tube:
                stood = _xf(tree, (-40, 640), web_tube, rot=(math.radians(90), 0, 0))
                mh = _math(tree, (-260, 520), "MULTIPLY", a=gin.outputs["Height"], b_val=0.62)
                mv = _vec(tree, (-90, 500), z=mh.outputs[0] if mh else None)
                placed = safe_node(tree, "GeometryNodeSetPosition", (140, 640))
                if stood and placed:
                    link_sockets(tree, stood.outputs["Geometry"], placed.inputs["Geometry"])
                    if mv:
                        link_sockets(tree, mv.outputs["Vector"], placed.inputs["Position"])
                    parts.append(placed.outputs["Geometry"])
    except Exception:
        pass

    join = safe_node(tree, "GeometryNodeJoinGeometry", (420, 350))
    if join:
        for p in [p for p in parts if p]:
            link_sockets(tree, p, join.inputs["Geometry"])
        _finish(tree, gin, gout, join.outputs["Geometry"], (680, 350))

    color_node(box, "geometry")
    color_node(frame_bez, "curve")
    return label_tree(tree, "MEL_music_lissajous_harp", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Soundbox And Frame", "nodes": ("box", "bezier"), "role": "geometry"},
        {"title": "String Web", "nodes": ("lissajous", "web"), "role": "curve"},
        {"title": "Output", "nodes": ("join", "shade", "Group Output"), "role": "output"},
    ])


# ────────────────────────────────────────────────────────────────────────
# 4. Piano Key Row (IMM)
# ────────────────────────────────────────────────────────────────────────

def build_imm_piano_keys(group_name="MEL_imm_piano_keys"):
    tree, gin, gout = new_geometry_tree(group_name)

    add_int_param(tree, "Octaves", 2, 1, 8)
    add_float_param(tree, "Key Width", 0.22, 0.08, 0.6)
    add_float_param(tree, "Key Depth", 0.9, 0.3, 2.5)
    add_float_param(tree, "Key Height", 0.09, 0.02, 0.4)
    add_float_param(tree, "Black Length Ratio", 0.62, 0.3, 0.9)
    add_float_param(tree, "Scale", 1.0, 0.1, 5.0)

    # 7 whites per octave - literal A × Octaves (avoid b_val/link slot collision)
    total_whites = _math(tree, (-750, 430), "MULTIPLY",
                         a=7.0, b=gin.outputs["Octaves"] if gin.outputs.get("Octaves") else None,
                         b_val=2 if not gin.outputs.get("Octaves") else None)

    # White key centres march -X from origin
    kw_step = _math(tree, (-750, 330), "MULTIPLY", a=gin.outputs["Key Width"], b_val=-1.0)
    step_v = _vec(tree, (-600, 360), x=kw_step.outputs[0] if kw_step else None)
    wline = _point_line(tree, (-430, 430), total_whites.outputs[0] if total_whites else None,
                        start=(0, 0, 0), step=None, step_sock=step_v)

    idx = safe_node(tree, "GeometryNodeInputIndex", (-430, 600))
    mod7 = _math(tree, (-270, 600), "MODULO", a=idx.outputs["Index"] if idx else None, b_val=7.0)
    lt2 = _math(tree, (-100, 660), "LESS_THAN", a=mod7.outputs[0] if mod7 else None, b_val=2.0)
    gt2 = _math(tree, (-100, 560), "GREATER_THAN", a=mod7.outputs[0] if mod7 else None, b_val=2.0)
    lt6 = _math(tree, (-100, 470), "LESS_THAN", a=mod7.outputs[0] if mod7 else None, b_val=6.0)
    band = _bool(tree, (80, 520), "AND", a=gt2.outputs[0] if gt2 else None,
                 b=lt6.outputs[0] if lt6 else None)
    is_black = _bool(tree, (250, 600), "OR", a=lt2.outputs[0] if lt2 else None,
                     b=band.outputs[0] if band else None)

    sep = safe_node(tree, "GeometryNodeSeparateGeometry", (430, 550))
    black_pts = None
    if sep and wline and is_black:
        link_sockets(tree, wline.outputs["Mesh"], sep.inputs["Geometry"])
        link_sockets(tree, is_black.outputs[0], sep.inputs["Selection"])
        black_pts = sep.outputs.get("Selection") or sep.outputs[0]

    def keys(pts_sock, black, lx):
        if pts_sock is None:
            return None
        inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (lx + 220, 550))
        cube = safe_node(tree, "GeometryNodeMeshCube", (lx, 550))
        if inst is None or cube is None:
            return None
        depth_ratio = gin.outputs["Black Length Ratio"] if black else None
        dz = _math(tree, (lx - 170, 430), "MULTIPLY",
                   a=gin.outputs["Key Depth"], b=depth_ratio) if black else None
        size = _vec(tree, (lx - 60, 500),
                    x=gin.outputs["Key Width"],
                    y=dz.outputs[0] if dz else gin.outputs["Key Depth"],
                    z=gin.outputs["Key Height"])
        if size:
            link_sockets(tree, size.outputs["Vector"], _in(cube, "Size"))
        lifted = _lift_to_floor(tree, cube.outputs["Mesh"], gin.outputs["Key Height"], 1.0, (lx + 60, 550))
        if lifted:
            # Blacks sit on the boundary after their white: nudge -X by half a key
            src = lifted
            if black:
                bx = _math(tree, (lx + 130, 470), "MULTIPLY", a=gin.outputs["Key Width"], b_val=-0.5)
                bv = _vec(tree, (lx + 260, 470), x=bx.outputs[0] if bx else None)
                shifted = safe_node(tree, "GeometryNodeTransform", (lx + 380, 550))
                if shifted and bv:
                    link_sockets(tree, src, shifted.inputs["Geometry"])
                    link_sockets(tree, bv.outputs["Vector"], shifted.inputs["Translation"])
                    src = shifted.outputs["Geometry"]
            link_sockets(tree, src, inst.inputs["Instance"])
            link_sockets(tree, pts_sock, inst.inputs["Points"])
            return _realize(tree, (lx + 420, 550), inst.outputs["Instances"])
        return None

    # Whites use every key position; blacks are the {0,1,3,4,5}-mod-7 subset
    w_geo = keys(wline.outputs["Mesh"] if wline else None, False, 640)
    b_geo = keys(black_pts, True, 900)

    join = safe_node(tree, "GeometryNodeJoinGeometry", (1420, 550))
    if join:
        for p in (w_geo, b_geo):
            if p:
                link_sockets(tree, p, join.inputs["Geometry"])
        _finish(tree, gin, gout, join.outputs["Geometry"], (1620, 550), smooth=False)

    color_node(wline, "curve")
    color_node(sep, "attribute")
    color_node(join, "geometry")
    return label_tree(tree, "MEL_imm_piano_keys", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Black Key Pattern", "nodes": ("index", "modulo", "separate"), "role": "math"},
        {"title": "Keys", "nodes": ("cube", "instance", "realize"), "role": "instance"},
        {"title": "Output", "nodes": ("join", "shade", "Group Output"), "role": "output"},
    ])


# ────────────────────────────────────────────────────────────────────────
# 5. Frequency Ribcage
# ────────────────────────────────────────────────────────────────────────

def build_music_frequency_ribcage(group_name="MEL_music_frequency_ribcage"):
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Span", 4.0, 1.0, 16.0)
    add_float_param(tree, "Max Height", 2.0, 0.5, 10.0)
    add_int_param(tree, "Rib Count", 7, 3, 31)
    add_float_param(tree, "Spacing", 1.2, 0.4, 6.0)
    add_float_param(tree, "Thickness", 0.07, 0.01, 0.3)
    add_float_param(tree, "Scale", 1.0, 0.1, 5.0)

    def arch(y_loc, h_div):
        bez = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (-600, y_loc))
        if not bez:
            return None
        half_neg = _math(tree, (-820, y_loc + 120), "MULTIPLY", a=gin.outputs["Span"], b_val=-0.5)
        half_pos = _math(tree, (-820, y_loc + 40), "MULTIPLY", a=gin.outputs["Span"], b_val=0.5)
        apex = _math(tree, (-820, y_loc - 40), "MULTIPLY", a=gin.outputs["Max Height"], b_val=h_div)
        shoulder = _math(tree, (-820, y_loc - 120), "MULTIPLY", a=gin.outputs["Max Height"], b_val=h_div * 0.28)
        s = _vec(tree, (-640, y_loc + 90), x=half_neg.outputs[0] if half_neg else None, z=0)
        e = _vec(tree, (-640, y_loc + 20), x=half_pos.outputs[0] if half_pos else None, z=0)
        c = _vec(tree, (-640, y_loc - 50), z=apex.outputs[0] if apex else None)
        cs = _vec(tree, (-640, y_loc - 120), z=shoulder.outputs[0] if shoulder else None)
        if all((s, e, c, cs)):
            link_sockets(tree, s.outputs["Vector"], _in(bez, "Start"))
            link_sockets(tree, s.outputs["Vector"], _in(bez, "Start Handle"))
            link_sockets(tree, cs.outputs["Vector"], _in(bez, "End Handle"))
            link_sockets(tree, e.outputs["Vector"], _in(bez, "End"))
        return _tube(tree, (-330, y_loc), bez.outputs["Curve"],
                     gin.outputs["Thickness"], verts=6, fill_caps=True)

    tiers = [t for t in (arch(520, 1.0), arch(240, 0.66), arch(-40, 0.4)) if t]
    join_tiers = safe_node(tree, "GeometryNodeJoinGeometry", (-60, 250))
    if join_tiers:
        for t in tiers:
            link_sockets(tree, t, join_tiers.inputs["Geometry"])

    spacing_total = None
    if gin.outputs.get("Spacing") and gin.outputs.get("Rib Count"):
        m1 = _math(tree, (-420, -170), "MULTIPLY", a=gin.outputs["Spacing"], b=gin.outputs["Rib Count"])
        spacing_total = m1.outputs[0] if m1 else None
    step_v = _vec(tree, (-100, -190), y=spacing_total)
    rline = _point_line(tree, (100, -170),
                        gin.outputs["Rib Count"] if gin.outputs.get("Rib Count") else None,
                        start=(0, 0, 0), step=None, step_sock=step_v)

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (330, 60))
    realized_geo = None
    if inst and join_tiers and rline:
        link_sockets(tree, join_tiers.outputs["Geometry"], inst.inputs["Instance"])
        link_sockets(tree, rline.outputs["Mesh"], inst.inputs["Points"])
        realized_geo = _realize(tree, (540, 60), inst.outputs["Instances"])

    _finish(tree, gin, gout, realized_geo, (760, 60))

    color_node(join_tiers, "geometry")
    color_node(inst, "instance")
    return label_tree(tree, "MEL_music_frequency_ribcage", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Harmonic Arch Tiers", "nodes": ("bezier", "join"), "role": "curve"},
        {"title": "Rib Array", "nodes": ("line", "instance", "realize"), "role": "instance"},
        {"title": "Output", "nodes": ("shade", "Group Output"), "role": "output"},
    ])


# ────────────────────────────────────────────────────────────────────────
# 6. Tuning Fork Column
# ────────────────────────────────────────────────────────────────────────

def build_music_tuning_fork(group_name="MEL_music_tuning_fork"):
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Total Height", 2.4, 0.6, 8.0)
    add_float_param(tree, "Fork Width", 0.42, 0.12, 1.6)
    add_float_param(tree, "Thickness", 0.09, 0.02, 0.4)
    add_float_param(tree, "Prong Split", 0.14, 0.02, 0.5)
    add_float_param(tree, "Scale", 1.0, 0.1, 5.0)

    parts = []
    shaft_h = _math(tree, (-800, 300), "MULTIPLY", a=gin.outputs["Total Height"], b_val=0.55)
    shaft = safe_node(tree, "GeometryNodeMeshCube", (-580, 300))
    if shaft and shaft_h:
        sz = _vec(tree, (-720, 240), x=gin.outputs["Thickness"],
                  y=gin.outputs["Thickness"], z=shaft_h.outputs[0])
        if sz:
            link_sockets(tree, sz.outputs["Vector"], _in(shaft, "Size"))
        lifted = _lift_to_floor(tree, shaft.outputs["Mesh"], shaft_h.outputs[0], 1.0, (-340, 300))
        if lifted:
            parts.append(lifted)

    # Plinth
    plinth = safe_node(tree, "GeometryNodeMeshCube", (-580, 120))
    if plinth:
        psz = _vec(tree, (-720, 60),
                   x=gin.outputs["Fork Width"], y=gin.outputs["Fork Width"],
                   z=gin.outputs["Thickness"])
        if psz:
            link_sockets(tree, psz.outputs["Vector"], _in(plinth, "Size"))
        lifted = _lift_to_floor(tree, plinth.outputs["Mesh"], gin.outputs["Thickness"], 1.0, (-340, 120))
        if lifted:
            parts.append(lifted)

    # Yoke sphere at junction
    yoke = safe_node(tree, "GeometryNodeMeshUVSphere", (-580, -60))
    if yoke:
        yoke.inputs["Segments"].default_value = 16
        yoke.inputs["Rings"].default_value = 10
        yr = _math(tree, (-760, -100), "MULTIPLY", a=gin.outputs["Thickness"], b_val=1.6)
        yh = _math(tree, (-760, -180), "MULTIPLY", a=gin.outputs["Total Height"], b_val=0.55)
        ys = safe_node(tree, "GeometryNodeTransform", (-380, -60))
        yp = safe_node(tree, "GeometryNodeSetPosition", (-180, -60))
        if ys and yr:
            sv = _vec(tree, (-540, -140),
                      x=yr.outputs[0], y=yr.outputs[0], z=yr.outputs[0])
            if sv:
                link_sockets(tree, yoke.outputs["Mesh"], ys.inputs["Geometry"])
                link_sockets(tree, sv.outputs["Vector"], ys.inputs["Scale"])
        if yp and yh:
            link_sockets(tree, ys.outputs["Geometry"] if ys else yoke.outputs["Mesh"],
                         yp.inputs["Position"] if False else yp.inputs["Geometry"])
            pv = _vec(tree, (-350, -230), z=yh.outputs[0])
            if pv:
                link_sockets(tree, pv.outputs["Vector"], yp.inputs["Position"])
            parts.append(yp.outputs["Geometry"])

    def prong(side_sign, y_loc):
        cyl = safe_node(tree, "GeometryNodeMeshCylinder", (-580, y_loc))
        if not cyl:
            return None
        cyl.inputs["Vertices"].default_value = 16
        cyl.fill_type = "NGON"
        link_sockets(tree, gin.outputs["Thickness"], _in(cyl, "Radius"))
        ph = _math(tree, (-760, y_loc - 80), "MULTIPLY", a=gin.outputs["Total Height"], b_val=0.42)
        if ph:
            link_sockets(tree, ph.outputs[0], _in(cyl, "Depth"))
        dx = _math(tree, (-760, y_loc - 160), "MULTIPLY", a=gin.outputs["Prong Split"], b_val=side_sign)
        pz = _math(tree, (-760, y_loc - 240), "MULTIPLY", a=gin.outputs["Total Height"], b_val=0.76)
        tv = _vec(tree, (-420, y_loc - 200), x=dx.outputs[0] if dx else None,
                  z=pz.outputs[0] if pz else None)
        xf = safe_node(tree, "GeometryNodeTransform", (-260, y_loc))
        if xf and tv:
            link_sockets(tree, cyl.outputs["Mesh"], xf.inputs["Geometry"])
            link_sockets(tree, tv.outputs["Vector"], xf.inputs["Translation"])
            xf.inputs["Rotation"].default_value = (side_sign * 0.06, 0, 0)
            return xf.outputs["Geometry"]
        return None

    for s in (-1, 1):
        p = prong(s, -320 if s < 0 else -460)
        if p:
            parts.append(p)

    join = safe_node(tree, "GeometryNodeJoinGeometry", (420, 100))
    if join:
        for p in [p for p in parts if p]:
            link_sockets(tree, p, join.inputs["Geometry"])
        _finish(tree, gin, gout, join.outputs["Geometry"], (660, 100))

    return label_tree(tree, "MEL_music_tuning_fork", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Shaft Plinth Yoke", "nodes": ("shaft", "plinth", "yoke"), "role": "geometry"},
        {"title": "Prongs", "nodes": ("prong",), "role": "instance"},
        {"title": "Output", "nodes": ("join", "shade", "Group Output"), "role": "output"},
    ])


# ────────────────────────────────────────────────────────────────────────
# 7. Metronome Pillar
# ────────────────────────────────────────────────────────────────────────

def build_music_metronome_pillar(group_name="MEL_music_metronome_pillar"):
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Body Height", 3.2, 1.0, 10.0)
    add_float_param(tree, "Base Width", 1.1, 0.3, 4.0)
    add_float_param(tree, "Pendulum Angle", 12.0, -40.0, 40.0)
    add_bool_param(tree, "Show Pendulum", True)
    add_float_param(tree, "Scale", 1.0, 0.1, 5.0)

    parts = []
    body = safe_node(tree, "GeometryNodeMeshCone", (-580, 320))
    if body:
        body.inputs["Vertices"].default_value = 4
        body.fill_type = "NGON"
        link_sockets(tree, gin.outputs["Body Height"], _in(body, "Depth"))
        link_sockets(tree, gin.outputs["Base Width"], _in(body, "Radius Bottom"))
        tw = _math(tree, (-760, 240), "MULTIPLY", a=gin.outputs["Base Width"], b_val=0.16)
        if tw:
            link_sockets(tree, tw.outputs[0], _in(body, "Radius Top"))
        rotated = _xf(tree, (-360, 320), body.outputs["Mesh"], rot=(0, 0, math.radians(45)))
        lifted = None
        if rotated:
            lifted = _lift_to_floor(tree, rotated.outputs["Geometry"],
                                    gin.outputs["Body Height"], 1.0, (-140, 320))
        parts.append((lifted or (rotated.outputs["Geometry"] if rotated else body.outputs["Mesh"])))

    pend_switch = safe_node(tree, "GeometryNodeSwitch", (520, 60))
    pend_geo = None
    rod_len = _math(tree, (-580, -60), "MULTIPLY", a=gin.outputs["Body Height"], b_val=0.72)
    rod = safe_node(tree, "GeometryNodeMeshCube", (-580, -140))
    if rod and rod_len:
        rs = _vec(tree, (-720, -200), x=0.03, y=0.03, z=rod_len.outputs[0])
        if rs:
            link_sockets(tree, rs.outputs["Vector"], _in(rod, "Size"))
        # pivot at top: drop rod by its length below pivot point (pivot near top of body)
        pivot_z = _math(tree, (-760, -280), "MULTIPLY", a=gin.outputs["Body Height"], b_val=0.82)
        drop = _math(tree, (-760, -360), "SUBTRACT",
                     a=pivot_z.outputs[0] if pivot_z else None,
                     b=rod_len.outputs[0])
        dv = _vec(tree, (-420, -320), z=drop.outputs[0] if drop else None)
        rod_xf = safe_node(tree, "GeometryNodeTransform", (-240, -140))
        if rod_xf and dv:
            link_sockets(tree, rod.outputs["Mesh"], rod_xf.inputs["Geometry"])
            link_sockets(tree, dv.outputs["Vector"], rod_xf.inputs["Translation"])
        deg2rad = _math(tree, (-580, -460), "MULTIPLY", a=gin.outputs["Pendulum Angle"], b_val=0.0174533)
        swing = safe_node(tree, "GeometryNodeTransform", (-40, -140))
        if swing and deg2rad:
            link_sockets(tree, rod_xf.outputs["Geometry"] if rod_xf else rod.outputs["Mesh"],
                         swing.inputs["Geometry"])
            rv = _vec(tree, (-210, -520), y=deg2rad.outputs[0])
            if rv:
                link_sockets(tree, rv.outputs["Vector"], swing.inputs["Rotation"])
            bob = safe_node(tree, "GeometryNodeMeshUVSphere", (-580, -620))
            bob_pos = safe_node(tree, "GeometryNodeSetPosition", (-40, -620))
            if bob and bob_pos:
                bob.inputs["Segments"].default_value = 16
                bob.inputs["Rings"].default_value = 10
                br = _math(tree, (-760, -660), "MULTIPLY", a=gin.outputs["Base Width"], b_val=0.13)
                bs = safe_node(tree, "GeometryNodeTransform", (-400, -620))
                if bs and br:
                    bvv = _vec(tree, (-560, -720), x=br.outputs[0], y=br.outputs[0], z=br.outputs[0])
                    if bvv:
                        link_sockets(tree, bob.outputs["Mesh"], bs.inputs["Geometry"])
                        link_sockets(tree, bvv.outputs["Vector"], bs.inputs["Scale"])
                tip_z = _math(tree, (-400, -800), "MULTIPLY", a=rod_len.outputs[0], b_val=-0.94)
                tip_base = _math(tree, (-560, -880), "ADD",
                                 a=pivot_z.outputs[0] if pivot_z else None,
                                 b=tip_z.outputs[0] if tip_z else None)
                tvp = _vec(tree, (-240, -840), z=tip_base.outputs[0] if tip_base else None)
                if tvp:
                    link_sockets(tree, bs.outputs["Geometry"] if bs else bob.outputs["Mesh"],
                                 bob_pos.inputs["Geometry"])
                    link_sockets(tree, tvp.outputs["Vector"], bob_pos.inputs["Position"])
            j = safe_node(tree, "GeometryNodeJoinGeometry", (180, -300))
            if j and swing:
                link_sockets(tree, swing.outputs["Geometry"], j.inputs["Geometry"])
                if bob_pos:
                    link_sockets(tree, bob_pos.outputs["Geometry"], j.inputs["Geometry"])
                pend_geo = j.outputs["Geometry"]

    if pend_switch:
        try:
            pend_switch.input_type = "GEOMETRY"
        except Exception:
            pass
        link_sockets(tree, gin.outputs["Show Pendulum"], _in(pend_switch, "Switch"))
        if pend_geo and _true_socket(pend_switch):
            link_sockets(tree, pend_geo, _true_socket(pend_switch))
        if parts and _false_socket(pend_switch):
            link_sockets(tree, parts[0], _false_socket(pend_switch))

    joined = _out(pend_switch, "Output") or (pend_switch.outputs[0] if pend_switch and pend_switch.outputs else None)
    join = safe_node(tree, "GeometryNodeJoinGeometry", (760, 200))
    if join:
        for p in [p for p in parts if p]:
            link_sockets(tree, p, join.inputs["Geometry"])
        if pend_geo and joined:
            link_sockets(tree, joined, join.inputs["Geometry"])
        _finish(tree, gin, gout, join.outputs["Geometry"], (960, 200))

    return label_tree(tree, "MEL_music_metronome_pillar", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Obelisk Body", "nodes": ("cone",), "role": "geometry"},
        {"title": "Pendulum", "nodes": ("rod", "bob", "switch"), "role": "instance"},
        {"title": "Output", "nodes": ("join", "shade", "Group Output"), "role": "output"},
    ])


# ────────────────────────────────────────────────────────────────────────
# 8. Soundhole Rosette
# ────────────────────────────────────────────────────────────────────────

def build_music_soundhole_rosette(group_name="MEL_music_soundhole_rosette"):
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Outer Radius", 1.2, 0.3, 5.0)
    add_float_param(tree, "Ring Thickness", 0.045, 0.01, 0.2)
    add_int_param(tree, "Marker Count", 12, 0, 48)
    add_float_param(tree, "Depth", 0.12, 0.02, 0.8)
    add_float_param(tree, "Scale", 1.0, 0.1, 5.0)

    parts = []
    for i, (rr, rt) in enumerate(((0.92, 0.9), (0.74, 1.2), (0.56, 0.85))):
        ring = _torus(tree, (-500, 420 - i * 200),
                      gin.outputs["Outer Radius"], rr,
                      gin.outputs["Ring Thickness"], rt,
                      major_seg=64, minor_seg=10)
        if ring:
            # flatten: squash Z to Depth
            flat = safe_node(tree, "GeometryNodeTransform", (-220, 420 - i * 200))
            if flat:
                fv = _vec(tree, (-380, 340 - i * 200),
                          x=1.0, y=1.0, z=gin.outputs["Depth"])
                if fv:
                    link_sockets(tree, ring, flat.inputs["Geometry"])
                    link_sockets(tree, fv.outputs["Vector"], flat.inputs["Scale"])
                    parts.append(flat.outputs["Geometry"])
                else:
                    parts.append(ring)

    # Radial marker studs on outer vertex-ring
    circ = safe_node(tree, "GeometryNodeMeshCircle", (-500, -140))
    marker_geo = None
    stud_inst = None
    if circ:
        circ.fill_type = "NONE"
        link_sockets(tree, gin.outputs["Marker Count"], _in(circ, "Vertices"))
        link_sockets(tree, gin.outputs["Outer Radius"], _in(circ, "Radius"))
        stud = safe_node(tree, "GeometryNodeMeshCube", (-500, -300))
        if stud:
            sw = _math(tree, (-680, -340), "MULTIPLY", a=gin.outputs["Ring Thickness"], b_val=1.6)
            sd = _math(tree, (-680, -420), "MULTIPLY", a=gin.outputs["Depth"], b_val=1.1)
            ss = _vec(tree, (-540, -380),
                      x=sw.outputs[0] if sw else None,
                      y=sw.outputs[0] if sw else None,
                      z=sd.outputs[0] if sd else None)
            if ss:
                link_sockets(tree, ss.outputs["Vector"], _in(stud, "Size"))
            inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (-220, -140))
            if inst:
                link_sockets(tree, circ.outputs["Mesh"], inst.inputs["Points"])
                link_sockets(tree, stud.outputs["Mesh"], inst.inputs["Instance"])
                marker_geo = _realize(tree, (20, -140), inst.outputs["Instances"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (450, 150))
    if join:
        for p in [p for p in parts if p]:
            link_sockets(tree, p, join.inputs["Geometry"])
        if marker_geo:
            link_sockets(tree, marker_geo, join.inputs["Geometry"])
        _finish(tree, gin, gout, join.outputs["Geometry"], (680, 150))

    color_node(circ, "curve")
    return label_tree(tree, "MEL_music_soundhole_rosette", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Concentric Rings", "nodes": ("torus", "flatten"), "role": "geometry"},
        {"title": "Radial Markers", "nodes": ("circle", "stud", "realize"), "role": "instance"},
        {"title": "Output", "nodes": ("join", "shade", "Group Output"), "role": "output"},
    ])


# ────────────────────────────────────────────────────────────────────────
# 9. Harmonograph - damped Lissajous tracery, Score-interval ratios
# ────────────────────────────────────────────────────────────────────────

def build_music_harmonograph(group_name="MEL_music_harmonograph"):
    """Damped harmonograph: x=A1 sin(f1 t+p1) e^(-d t), y=A2 sin(f2 t+p2) e^(-d t).

    f1:f2 ratios map to musical intervals - octave 2:1, fifth 3:2, fourth 4:3,
    major third 5:4 (set via Frequency A/B). Damping gives the classic decay
    spiral-in of pendulum harmonographs.
    """
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Turns", 3.0, 0.5, 12.0)
    add_float_param(tree, "Frequency A", 3.0, 1.0, 9.0)
    add_float_param(tree, "Frequency B", 2.0, 1.0, 9.0)
    add_float_param(tree, "Phase", 0.0, -3.14159, 3.14159)
    add_float_param(tree, "Damping", 0.35, 0.0, 1.5)
    add_float_param(tree, "Amplitude", 1.2, 0.2, 4.0)
    add_int_param(tree, "Resolution", 400, 64, 1600)
    add_float_param(tree, "Thickness", 0.02, 0.004, 0.12)
    add_float_param(tree, "Scale", 1.0, 0.1, 5.0)

    # Parameter line: t along X - MUST become a CURVE before SetPosition,
    # because Spline Parameter Factor is undefined (=0) on mesh geometry.
    line = _point_line(tree, (-520, 300), gin.outputs["Resolution"],
                       start=(-1.6, 0, 0), step=(0.008, 0, 0))
    line_c2c = safe_node(tree, "GeometryNodeMeshToCurve", (-360, 300))
    if line_c2c and line:
        link_sockets(tree, line.outputs["Mesh"], _in(line_c2c, "Mesh"))
    curve_sock = line_c2c.outputs["Curve"] if line_c2c else None

    spl = safe_node(tree, "GeometryNodeSplineParameter", (-300, 470))
    factor = _out(spl, "Factor")

    # T = factor * Turns * 2π
    tau_t = _math(tree, (-120, 500), "MULTIPLY", a=factor)
    turns_tau = _math(tree, (-280, 560), "MULTIPLY", a=gin.outputs["Turns"], b_val=math.tau)
    if tau_t and turns_tau:
        link_sockets(tree, turns_tau.outputs[0], tau_t.inputs[1])

    # envelope e^(-d-T): EXPONENT node computes e^x
    env_in = None
    if gin.outputs.get("Damping"):
        dt = _math(tree, (-40, 380), "MULTIPLY",
                   a=gin.outputs["Damping"], b=tau_t.outputs[0] if tau_t else None)
        if dt:
            neg_dt2 = _math(tree, (120, 380), "MULTIPLY", a=dt.outputs[0], b_val=-1.0)
            expn = _math(tree, (280, 400), "EXPONENT")
            if expn and neg_dt2:
                link_sockets(tree, neg_dt2.outputs[0], expn.inputs[0])
                env_in = expn.outputs[0]

    def axis(loc_y, freq_param, phase_val):
        ft = _math(tree, (140, loc_y), "MULTIPLY",
                   a=tau_t.outputs[0] if tau_t else None,
                   b=gin.outputs[freq_param])
        sn = _math(tree, (320, loc_y), "SINE")
        if ft and sn:
            ph_add = _math(tree, (240, loc_y - 90), "ADD", a=ft.outputs[0], b_val=phase_val)
            link_sockets(tree, ph_add.outputs[0], sn.inputs[0]) if ph_add else None
            amp = _math(tree, (480, loc_y), "MULTIPLY",
                        a=sn.outputs[0], b=env_in or gin.outputs["Amplitude"])
            out = _math(tree, (620, loc_y), "MULTIPLY",
                        a=amp.outputs[0] if amp else None, b=gin.outputs["Amplitude"])
            return out.outputs[0] if out else None
        return None

    xv = axis(560, "Frequency A", 0.0)
    yv = axis(420, "Frequency B", math.pi / 2)

    disp = _vec(tree, (800, 480), x=xv, y=yv)
    set_pos = safe_node(tree, "GeometryNodeSetPosition", (950, 350))
    if set_pos and curve_sock:
        link_sockets(tree, curve_sock, set_pos.inputs["Geometry"])
        if disp:
            link_sockets(tree, disp.outputs["Vector"], set_pos.inputs["Offset"])

    body = _tube(tree, (1150, 350), set_pos.outputs["Geometry"] if set_pos else None,
                 gin.outputs["Thickness"], verts=6, fill_caps=True)

    # Center the drawing at its bounding-box middle via a rough recenter: shift X by -1.6+? keep simple.
    _finish(tree, gin, gout, body, (1420, 350))

    color_node(line, "curve")
    color_node(set_pos, "geometry")
    return label_tree(tree, "MEL_music_harmonograph", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Damped Oscillators", "nodes": ("sine", "exponent"), "role": "math"},
        {"title": "Tracery Curve", "nodes": ("set position", "tube"), "role": "geometry"},
        {"title": "Output", "nodes": ("shade", "transform", "Group Output"), "role": "output"},
    ])


# ── Registry ────────────────────────────────────────────────────────────
from .core import register_builder

register_builder("MEL_music_waveform_wall", build_music_waveform_wall, "Waveform Wall",
                 "Oscilloscope ribbon displaced by 3 additive harmonic layers (capped tube)",
                 "music")
register_builder("MEL_music_vinyl_disc", build_music_vinyl_disc, "Vinyl Disc",
                 "Record disc with groove spiral, label, spindle-hole boolean",
                 "music")
register_builder("MEL_music_lissajous_harp", build_music_lissajous_harp, "Lissajous Harp",
                 "Harp frame, soundbox plinth and upright lissajous string web",
                 "music")
register_builder("MEL_imm_piano_keys", build_imm_piano_keys, "Piano Key Row (IMM)",
                 "Octave strip with 2+3 black-key grouping, floor-pivoted for IMM",
                 "music")
register_builder("MEL_music_frequency_ribcage", build_music_frequency_ribcage, "Frequency Ribcage",
                 "Vault ribs in 1/k harmonic decay tiers arrayed along Y",
                 "music")
register_builder("MEL_music_tuning_fork", build_music_tuning_fork, "Tuning Fork Column",
                 "Plinth, shaft, yoke sphere and split prongs",
                 "music")
register_builder("MEL_music_metronome_pillar", build_music_metronome_pillar, "Metronome Pillar",
                 "Obelisk metronome with angle-driven pendulum and bob",
                 "music")
register_builder("MEL_music_soundhole_rosette", build_music_soundhole_rosette, "Soundhole Rosette",
                 "Guitar soundhole medallion: flattened concentric rings + radial studs",
                 "music")
register_builder("MEL_music_harmonograph", build_music_harmonograph, "Harmonograph Tracery",
                 "Damped Lissajous pendulum drawing - f1:f2 = Score interval (2:1 oct, 3:2 fifth)",
                 "music")
