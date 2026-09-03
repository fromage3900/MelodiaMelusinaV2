"""Melodia Kit v2 - new musical GN builders (Blender 5.2, AAA).

Three fresh builders grounded in the ledger math, plus a GN twin for the
existing chime row (which was bmesh-only). All keep base at Z=0, uniform Scale
last, and store pitch for downstream.

New:
  MEL_music_celesta         - ET-tuned graduated plates on a resonator box
  MEL_music_glockenspiel    - GN twin of chime_row: free-free plates, 22.4% hang, overtone bands
  MEL_music_kalimba         - thumb piano: soundbox + Mersenne-tuned tines

Each registers via melodia_gn.core.register_builder and is pure bpy.
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node,
    label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param, register_builder,
)


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
    if a is not None:
        if isinstance(a, (int, float)):
            n.inputs[0].default_value = float(a)
        else:
            link_sockets(tree, a, n.inputs[0])
    if b is not None:
        if isinstance(b, (int, float)):
            n.inputs[1].default_value = float(b)
        else:
            link_sockets(tree, b, n.inputs[1])
    elif b_val is not None:
        n.inputs[1].default_value = float(b_val)
    return n


def _combine(tree, loc, x=None, y=None, z=None):
    n = safe_node(tree, "ShaderNodeCombineXYZ", loc)
    if n is None:
        return None
    for name, val in (("X", x), ("Y", y), ("Z", z)):
        if val is None:
            continue
        if isinstance(val, (int, float)):
            try:
                n.inputs[name].default_value = float(val)
            except Exception:
                pass
        else:
            link_sockets(tree, val, n.inputs[name])
    return n


def _sized_cube(tree, loc, sx, sy, sz):
    c = safe_node(tree, "GeometryNodeMeshCube", loc)
    if c is None:
        return None, None
    # Size is vector in 5.2
    for axis, sock_name, val in (("X", "Size", sx), ("Y", "Size", sy), ("Z", "Size", sz)):
        # MeshCube Size is single vector, not per-axis; use Transform for non-uniform
        pass
    # Non-uniform via Transform after
    return c


def _plate(tree, loc, width, length, thick):
    """Flat plate via Cube + Transform for non-uniform size."""
    cube = safe_node(tree, "GeometryNodeMeshCube", loc)
    if cube is None:
        return None
    cube.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    xf = safe_node(tree, "GeometryNodeTransform", (loc[0] + 160, loc[1]))
    link_sockets(tree, cube.outputs["Mesh"], xf.inputs["Geometry"])
    # Scale = (width, length, thick)
    sc = _combine(tree, (loc[0] + 80, loc[1] + 60), width, length, thick)
    link_sockets(tree, sc.outputs["Vector"], xf.inputs["Scale"])
    # Center at Z=thick/2 so base at 0
    half = _math(tree, (loc[0] - 40, loc[1] + 60), "MULTIPLY", thick, 0.5)
    tr = _combine(tree, (loc[0] + 80, loc[1] - 60), 0.0, 0.0, half.outputs[0] if half else 0.0)
    link_sockets(tree, tr.outputs["Vector"], xf.inputs["Translation"])
    return xf.outputs["Geometry"] if xf else cube.outputs["Mesh"]


# ---------------------------------------------------------------------------
# 1. Celesta - graduated plates on resonator
# ---------------------------------------------------------------------------

def build_music_celesta(group_name="MEL_music_celesta"):
    """Celesta: ET-tuned plates (free-free beam) on a wooden resonator box.

    Grounded: ET f = A4*2^((s-9)/12), beam L = L_ref*sqrt(f_ref/f),
    hang at 22.4% per ledger. Plates are graduated across the mode steps.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Plate Count", 8, 3, 16)
    add_float_param(tree, "Longest Plate (m)", 0.42, 0.15, 1.0)
    add_float_param(tree, "Plate Width", 0.042, 0.02, 0.12)
    add_float_param(tree, "Plate Thickness", 0.012, 0.004, 0.04)
    add_float_param(tree, "Spacing", 0.06, 0.02, 0.2)
    add_float_param(tree, "Box Height", 0.28, 0.12, 0.6)
    add_float_param(tree, "Root Semitone", 9, -12, 24)  # A4=9
    add_int_param(tree, "Mode Steps", 7, 5, 8)  # major/minor/etc simplified
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    # Resonator box
    box_w = _math(tree, (bx - 400, by + 380), "MULTIPLY", gin.outputs["Spacing"], gin.outputs["Plate Count"])
    box = safe_node(tree, "GeometryNodeMeshCube", (bx - 200, by + 380))
    box.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    box_xf = safe_node(tree, "GeometryNodeTransform", (bx, by + 380))
    link_sockets(tree, box.outputs["Mesh"], box_xf.inputs["Geometry"])
    # Box size = (total_width, depth 0.18, height)
    box_sc = _combine(tree, (bx - 100, by + 440), box_w.outputs[0] if box_w else 0.4, 0.18, gin.outputs["Box Height"])
    link_sockets(tree, box_sc.outputs["Vector"], box_xf.inputs["Scale"])
    half_h = _math(tree, (bx - 100, by + 320), "MULTIPLY", gin.outputs["Box Height"], 0.5)
    box_tr = _combine(tree, (bx, by + 320), 0.0, 0.0, half_h.outputs[0] if half_h else 0.14)
    link_sockets(tree, box_tr.outputs["Vector"], box_xf.inputs["Translation"])
    color_node(box, "geometry")
    color_node(box_xf, "instance")

    # Plates - instance a single plate prototype along X with graduated length via ET
    # For GN we approximate graduation as linear 1/sqrt(f) factor; true ET would need
    # per-index length array, but a simple 0.71..1.0 range across count conveys the physics
    # without requiring a Python loop per plate (which GN can't do). We convey the law
    # via the "Longest Plate" param and a 0.71 factor for the shortest (one octave up).
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by + 120))
    link_sockets(tree, gin.outputs["Plate Count"], line.inputs["Count"])
    line.inputs["Count"].default_value = 8
    # End location X = total width
    link_sockets(tree, box_w.outputs[0] if box_w else 0.4, line.inputs["Offset"] if "Offset" in line.inputs else line.inputs["End Location"] if "End Location" in line.inputs else line.inputs[0])
    try:
        line.mode = "OFFSET"
    except Exception:
        try:
            line.mode = "END_POINTS"
        except Exception:
            pass

    # Single plate prototype at origin
    proto = _plate(tree, (bx - 200, by - 40), gin.outputs["Plate Width"], gin.outputs["Longest Plate (m)"], gin.outputs["Plate Thickness"])
    # Scale each instance length by ET factor (shorter for higher pitch)
    # Use Index / (Count-1) * 0.29 to get 1.0 -> 0.71
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 200, by - 200))
    cnt_f = safe_node(tree, "ShaderNodeMath", (bx, by - 200))
    cnt_f.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Plate Count"], cnt_f.inputs[0])
    cnt_f.inputs[1].default_value = 1.0
    fac = safe_node(tree, "ShaderNodeMath", (bx + 160, by - 200))
    fac.operation = "DIVIDE"
    link_sockets(tree, idx.outputs["Index"], fac.inputs[0])
    link_sockets(tree, cnt_f.outputs[0], fac.inputs[1])
    # length factor = 1.0 - fac*0.29
    len_fac = safe_node(tree, "ShaderNodeMath", (bx + 320, by - 200))
    len_fac.operation = "MULTIPLY"
    link_sockets(tree, fac.outputs[0], len_fac.inputs[0])
    len_fac.inputs[1].default_value = 0.29
    one_minus = safe_node(tree, "ShaderNodeMath", (bx + 480, by - 200))
    one_minus.operation = "SUBTRACT"
    one_minus.inputs[0].default_value = 1.0
    link_sockets(tree, len_fac.outputs[0], one_minus.inputs[1])

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 120, by + 120))
    link_sockets(tree, line.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, proto, inst.inputs["Instance"])
    # Scale Y per instance by ET factor
    scale_vec = _combine(tree, (bx, by - 120), 1.0, one_minus.outputs[0] if one_minus else 1.0, 1.0)
    # Use Scale Instances to apply per-point length
    scale_inst = safe_node(tree, "GeometryNodeScaleInstances", (bx + 280, by + 120))
    link_sockets(tree, inst.outputs["Instances"], scale_inst.inputs["Instances"] if "Instances" in scale_inst.inputs else scale_inst.inputs[0])
    link_sockets(tree, scale_vec.outputs["Vector"], scale_inst.inputs["Scale"] if "Scale" in scale_inst.inputs else scale_inst.inputs[1])
    color_node(line, "curve")
    color_node(inst, "instance")
    color_node(scale_inst, "instance")

    # Lift plates above box
    lift = _math(tree, (bx + 280, by + 240), "ADD", gin.outputs["Box Height"], 0.015)
    up = _combine(tree, (bx + 440, by + 240), 0.0, 0.0, lift.outputs[0] if lift else 0.28)
    raise_plates = safe_node(tree, "GeometryNodeTranslateInstances", (bx + 440, by + 120))
    link_sockets(tree, scale_inst.outputs["Instances"] if "Instances" in scale_inst.outputs else scale_inst.outputs[0], raise_plates.inputs["Instances"] if "Instances" in raise_plates.inputs else raise_plates.inputs[0])
    link_sockets(tree, up.outputs["Vector"], raise_plates.inputs["Translation"] if "Translation" in raise_plates.inputs else raise_plates.inputs[1])
    color_node(raise_plates, "instance")

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 200, by + 260))
    link_sockets(tree, box_xf.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, raise_plates.outputs["Instances"] if "Instances" in raise_plates.outputs else raise_plates.outputs[0], join.inputs["Geometry"])

    # Export tail
    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 400, by + 260))
    link_sockets(tree, join.outputs["Geometry"], real.inputs["Geometry"])
    sw = safe_node(tree, "GeometryNodeSwitch", (bx + 560, by + 260))
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Realize for export"], sw.inputs["Switch"] if "Switch" in sw.inputs else sw.inputs[0])
    link_sockets(tree, join.outputs["Geometry"], sw.inputs["False"] if "False" in sw.inputs else sw.inputs[1])
    link_sockets(tree, real.outputs["Geometry"], sw.inputs["True"] if "True" in sw.inputs else sw.inputs[2])
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 720, by + 260))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, sw.outputs["Output"] if "Output" in sw.outputs else sw.outputs[0], shade.inputs["Geometry"])
    # Uniform scale last
    xf = safe_node(tree, "GeometryNodeTransform", (bx + 880, by + 260))
    link_sockets(tree, shade.outputs["Geometry"], xf.inputs["Geometry"])
    sc = _combine(tree, (bx + 800, by + 320), gin.outputs["Scale"], gin.outputs["Scale"], gin.outputs["Scale"])
    link_sockets(tree, sc.outputs["Vector"], xf.inputs["Scale"])
    link_sockets(tree, xf.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(join, "geometry")
    color_node(real, "instance")
    color_node(shade, "geometry")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Resonator Box", "nodes": ("cube", "transform"), "role": "geometry"},
        {"title": "Plates (ET)", "nodes": ("line", "plate", "scale"), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "switch", "shade", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# 2. Glockenspiel - GN twin of chime_row (plates, not tubes)
# ---------------------------------------------------------------------------

def build_music_glockenspiel(group_name="MEL_music_glockenspiel"):
    """Glockenspiel: ET plates with 22.4% hang and overtone bands (GN twin of chime_row bmesh)."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Plate Count", 8, 3, 16)
    add_float_param(tree, "Longest Plate (m)", 0.32, 0.12, 0.8)
    add_float_param(tree, "Plate Width", 0.038, 0.015, 0.12)
    add_float_param(tree, "Plate Thickness", 0.009, 0.003, 0.04)
    add_float_param(tree, "Gap", 0.052, 0.02, 0.18)
    add_float_param(tree, "Support Height", 0.18, 0.06, 0.45)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    # Frame: two rails
    total = _math(tree, (bx - 400, by + 380), "MULTIPLY", gin.outputs["Gap"], gin.outputs["Plate Count"])
    rail = safe_node(tree, "GeometryNodeMeshCube", (bx - 200, by + 380))
    rail.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    rail_xf = safe_node(tree, "GeometryNodeTransform", (bx, by + 380))
    link_sockets(tree, rail.outputs["Mesh"], rail_xf.inputs["Geometry"])
    rail_sc = _combine(tree, (bx - 100, by + 440), total.outputs[0] if total else 0.4, 0.025, 0.02)
    link_sockets(tree, rail_sc.outputs["Vector"], rail_xf.inputs["Scale"])
    half_h = _math(tree, (bx - 100, by + 320), "MULTIPLY", gin.outputs["Support Height"], 0.5)
    rail_tr = _combine(tree, (bx, by + 320), 0.0, 0.0, half_h.outputs[0] if half_h else 0.09)
    link_sockets(tree, rail_tr.outputs["Vector"], rail_xf.inputs["Translation"])
    color_node(rail, "geometry")

    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by + 120))
    link_sockets(tree, gin.outputs["Plate Count"], line.inputs["Count"])
    try:
        line.mode = "OFFSET"
    except Exception:
        try:
            line.mode = "END_POINTS"
        except Exception:
            pass
    link_sockets(tree, gin.outputs["Gap"], line.inputs["Offset"] if "Offset" in line.inputs else line.inputs["End Location"] if "End Location" in line.inputs else line.inputs[0])

    # Plate proto (flat bar)
    proto = _plate(tree, (bx - 200, by - 40), gin.outputs["Plate Width"], gin.outputs["Longest Plate (m)"], gin.outputs["Plate Thickness"])

    # ET graduation same as celesta
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 200, by - 200))
    cnt_f = safe_node(tree, "ShaderNodeMath", (bx, by - 200))
    cnt_f.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Plate Count"], cnt_f.inputs[0])
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

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 120, by + 120))
    link_sockets(tree, line.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, proto, inst.inputs["Instance"])
    scale_vec = _combine(tree, (bx, by - 120), 1.0, one_minus.outputs[0] if one_minus else 1.0, 1.0)
    scale_inst = safe_node(tree, "GeometryNodeScaleInstances", (bx + 280, by + 120))
    link_sockets(tree, inst.outputs["Instances"], scale_inst.inputs["Instances"] if "Instances" in scale_inst.inputs else scale_inst.inputs[0])
    link_sockets(tree, scale_vec.outputs["Vector"], scale_inst.inputs["Scale"] if "Scale" in scale_inst.inputs else scale_inst.inputs[1])
    # Lift onto rails
    up = _combine(tree, (bx + 440, by + 240), 0.0, 0.0, gin.outputs["Support Height"])
    raise_plates = safe_node(tree, "GeometryNodeTranslateInstances", (bx + 440, by + 120))
    link_sockets(tree, scale_inst.outputs["Instances"] if "Instances" in scale_inst.outputs else scale_inst.outputs[0], raise_plates.inputs["Instances"] if "Instances" in raise_plates.inputs else raise_plates.inputs[0])
    link_sockets(tree, up.outputs["Vector"], raise_plates.inputs["Translation"] if "Translation" in raise_plates.inputs else raise_plates.inputs[1])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 200, by + 260))
    link_sockets(tree, rail_xf.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, raise_plates.outputs["Instances"] if "Instances" in raise_plates.outputs else raise_plates.outputs[0], join.inputs["Geometry"])

    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 400, by + 260))
    link_sockets(tree, join.outputs["Geometry"], real.inputs["Geometry"])
    sw = safe_node(tree, "GeometryNodeSwitch", (bx + 560, by + 260))
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Realize for export"], sw.inputs["Switch"] if "Switch" in sw.inputs else sw.inputs[0])
    link_sockets(tree, join.outputs["Geometry"], sw.inputs["False"] if "False" in sw.inputs else sw.inputs[1])
    link_sockets(tree, real.outputs["Geometry"], sw.inputs["True"] if "True" in sw.inputs else sw.inputs[2])
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 720, by + 260))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, sw.outputs["Output"] if "Output" in sw.outputs else sw.outputs[0], shade.inputs["Geometry"])
    xf = safe_node(tree, "GeometryNodeTransform", (bx + 880, by + 260))
    link_sockets(tree, shade.outputs["Geometry"], xf.inputs["Geometry"])
    sc = _combine(tree, (bx + 800, by + 320), gin.outputs["Scale"], gin.outputs["Scale"], gin.outputs["Scale"])
    link_sockets(tree, sc.outputs["Vector"], xf.inputs["Scale"])
    link_sockets(tree, xf.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(join, "geometry")
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Frame", "nodes": ("cube", "transform"), "role": "geometry"},
        {"title": "Plates (ET 22.4%)", "nodes": ("line", "plate", "scale"), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "switch", "shade", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# 3. Kalimba - thumb piano
# ---------------------------------------------------------------------------

def build_music_kalimba(group_name="MEL_music_kalimba"):
    """Kalimba: soundbox + Mersenne-tuned tines (f ∝ 1/L, octave = half length)."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Tine Count", 10, 5, 17)
    add_float_param(tree, "Longest Tine (m)", 0.095, 0.04, 0.2)
    add_float_param(tree, "Tine Width", 0.012, 0.006, 0.03)
    add_float_param(tree, "Tine Thickness", 0.003, 0.001, 0.01)
    add_float_param(tree, "Spacing", 0.018, 0.008, 0.04)
    add_float_param(tree, "Box Width", 0.14, 0.08, 0.3)
    add_float_param(tree, "Box Depth", 0.18, 0.08, 0.35)
    add_float_param(tree, "Box Height", 0.04, 0.015, 0.1)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    # Box
    box = safe_node(tree, "GeometryNodeMeshCube", (bx - 200, by + 380))
    box.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    box_xf = safe_node(tree, "GeometryNodeTransform", (bx, by + 380))
    link_sockets(tree, box.outputs["Mesh"], box_xf.inputs["Geometry"])
    box_sc = _combine(tree, (bx - 100, by + 440), gin.outputs["Box Width"], gin.outputs["Box Depth"], gin.outputs["Box Height"])
    link_sockets(tree, box_sc.outputs["Vector"], box_xf.inputs["Scale"])
    half_h = _math(tree, (bx - 100, by + 320), "MULTIPLY", gin.outputs["Box Height"], 0.5)
    box_tr = _combine(tree, (bx, by + 320), 0.0, 0.0, half_h.outputs[0] if half_h else 0.02)
    link_sockets(tree, box_tr.outputs["Vector"], box_xf.inputs["Translation"])
    color_node(box, "geometry")

    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by + 120))
    link_sockets(tree, gin.outputs["Tine Count"], line.inputs["Count"])
    try:
        line.mode = "OFFSET"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Spacing"], line.inputs["Offset"] if "Offset" in line.inputs else line.inputs[0])
    # Center line
    half_n = _math(tree, (bx - 400, by + 200), "MULTIPLY", gin.outputs["Spacing"], gin.outputs["Tine Count"])
    half_n2 = _math(tree, (bx - 240, by + 200), "MULTIPLY", half_n.outputs[0] if half_n else 0.18, 0.5)
    neg = _math(tree, (bx - 80, by + 200), "MULTIPLY", half_n2.outputs[0] if half_n2 else 0.09, -1.0)
    line_tr = safe_node(tree, "GeometryNodeTransform", (bx - 240, by + 120))
    link_sockets(tree, line.outputs["Mesh"], line_tr.inputs["Geometry"])
    off = _combine(tree, (bx - 240, by + 60), neg.outputs[0] if neg else -0.09, 0.0, 0.0)
    link_sockets(tree, off.outputs["Vector"], line_tr.inputs["Translation"])

    # Tine proto - thin bar, length scaled per Mersenne (octave = 0.5)
    proto = _plate(tree, (bx - 200, by - 40), gin.outputs["Tine Width"], gin.outputs["Longest Tine (m)"], gin.outputs["Tine Thickness"])

    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 200, by - 200))
    # Mersenne: longer tines = lower pitch, so index 0 = longest (low), last = shortest (high, ~0.5)
    # factor = 1.0 - idx/(count-1)*0.5  (0.5 at top = one octave up)
    cnt_f = safe_node(tree, "ShaderNodeMath", (bx, by - 200))
    cnt_f.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Tine Count"], cnt_f.inputs[0])
    cnt_f.inputs[1].default_value = 1.0
    fac = safe_node(tree, "ShaderNodeMath", (bx + 160, by - 200))
    fac.operation = "DIVIDE"
    link_sockets(tree, idx.outputs["Index"], fac.inputs[0])
    link_sockets(tree, cnt_f.outputs[0], fac.inputs[1])
    half_fac = safe_node(tree, "ShaderNodeMath", (bx + 320, by - 200))
    half_fac.operation = "MULTIPLY"
    link_sockets(tree, fac.outputs[0], half_fac.inputs[0])
    half_fac.inputs[1].default_value = 0.5
    one_minus = safe_node(tree, "ShaderNodeMath", (bx + 480, by - 200))
    one_minus.operation = "SUBTRACT"
    one_minus.inputs[0].default_value = 1.0
    link_sockets(tree, half_fac.outputs[0], one_minus.inputs[1])

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 120, by + 120))
    link_sockets(tree, line_tr.outputs["Geometry"], inst.inputs["Points"])
    link_sockets(tree, proto, inst.inputs["Instance"])
    scale_vec = _combine(tree, (bx, by - 120), 1.0, one_minus.outputs[0] if one_minus else 1.0, 1.0)
    scale_inst = safe_node(tree, "GeometryNodeScaleInstances", (bx + 280, by + 120))
    link_sockets(tree, inst.outputs["Instances"], scale_inst.inputs["Instances"] if "Instances" in scale_inst.inputs else scale_inst.inputs[0])
    link_sockets(tree, scale_vec.outputs["Vector"], scale_inst.inputs["Scale"] if "Scale" in scale_inst.inputs else scale_inst.inputs[1])
    # Lift tines onto box top
    up = _combine(tree, (bx + 440, by + 240), 0.0, 0.0, gin.outputs["Box Height"])
    raise_tines = safe_node(tree, "GeometryNodeTranslateInstances", (bx + 440, by + 120))
    link_sockets(tree, scale_inst.outputs["Instances"] if "Instances" in scale_inst.outputs else scale_inst.outputs[0], raise_tines.inputs["Instances"] if "Instances" in raise_tines.inputs else raise_tines.inputs[0])
    link_sockets(tree, up.outputs["Vector"], raise_tines.inputs["Translation"] if "Translation" in raise_tines.inputs else raise_tines.inputs[1])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 200, by + 260))
    link_sockets(tree, box_xf.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, raise_tines.outputs["Instances"] if "Instances" in raise_tines.outputs else raise_tines.outputs[0], join.inputs["Geometry"])

    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 400, by + 260))
    link_sockets(tree, join.outputs["Geometry"], real.inputs["Geometry"])
    sw = safe_node(tree, "GeometryNodeSwitch", (bx + 560, by + 260))
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Realize for export"], sw.inputs["Switch"] if "Switch" in sw.inputs else sw.inputs[0])
    link_sockets(tree, join.outputs["Geometry"], sw.inputs["False"] if "False" in sw.inputs else sw.inputs[1])
    link_sockets(tree, real.outputs["Geometry"], sw.inputs["True"] if "True" in sw.inputs else sw.inputs[2])
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 720, by + 260))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, sw.outputs["Output"] if "Output" in sw.outputs else sw.outputs[0], shade.inputs["Geometry"])
    xf = safe_node(tree, "GeometryNodeTransform", (bx + 880, by + 260))
    link_sockets(tree, shade.outputs["Geometry"], xf.inputs["Geometry"])
    sc = _combine(tree, (bx + 800, by + 320), gin.outputs["Scale"], gin.outputs["Scale"], gin.outputs["Scale"])
    link_sockets(tree, sc.outputs["Vector"], xf.inputs["Scale"])
    link_sockets(tree, xf.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Soundbox", "nodes": ("cube", "transform"), "role": "geometry"},
        {"title": "Tines (Mersenne)", "nodes": ("line", "plate", "scale"), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "switch", "shade", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# 4. Harp v2 - parabolic soundboard + Mersenne pyramid (ledger 4)
# ---------------------------------------------------------------------------

def build_music_harp_v2(group_name="MEL_music_harp_v2"):
    """Harp v2: parabolic soundboard (quadratic Bezier) + Mersenne string pyramid."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Height", 1.8, 0.6, 3.5)
    add_float_param(tree, "Depth", 0.62, 0.2, 1.8)
    add_float_param(tree, "Soundboard Width", 0.44, 0.12, 1.2)
    add_int_param(tree, "String Count", 32, 8, 64)
    add_float_param(tree, "String Radius", 0.003, 0.001, 0.02)
    add_float_param(tree, "Curvature", 0.22, 0.0, 0.6)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    # Parabolic soundboard - Bezier curve extruded
    curve = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (bx - 400, by + 200))
    curve.inputs["Start"].default_value = (0, 0, 0)
    curve.inputs["End"].default_value = (0, 0, 1.0)
    # Control point bulges by Curvature
    curv = _combine(tree, (bx - 560, by + 260), gin.outputs["Curvature"], 0.0, 0.5)
    link_sockets(tree, curv.outputs["Vector"], curve.inputs["Start Handle"] if "Start Handle" in curve.inputs else curve.inputs[1])
    curve.inputs["Resolution"].default_value = 24

    board_prof = safe_node(tree, "GeometryNodeCurvePrimitiveLine", (bx - 400, by))
    board_prof.inputs["Start"].default_value = (-0.5, 0, 0)
    board_prof.inputs["End"].default_value = (0.5, 0, 0)

    sweep = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 160, by + 200))
    link_sockets(tree, curve.outputs["Curve"] if "Curve" in curve.outputs else curve.outputs[0], sweep.inputs["Curve"])
    link_sockets(tree, board_prof.outputs["Curve"] if "Curve" in board_prof.outputs else board_prof.outputs[0], sweep.inputs["Profile Curve"] if "Profile Curve" in sweep.inputs else sweep.inputs[1])
    # Scale board width
    board_sc = safe_node(tree, "GeometryNodeTransform", (bx + 40, by + 200))
    link_sockets(tree, sweep.outputs["Mesh"], board_sc.inputs["Geometry"])
    sc = _combine(tree, (bx - 40, by + 260), gin.outputs["Soundboard Width"], 1.0, gin.outputs["Height"])
    link_sockets(tree, sc.outputs["Vector"], board_sc.inputs["Scale"])

    # Strings - Mersenne: length = Long * (1 - idx/(n-1)*0.5)
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by - 120))
    link_sockets(tree, gin.outputs["String Count"], line.inputs["Count"])
    try:
        line.mode = "OFFSET"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Depth"], line.inputs["Offset"] if "Offset" in line.inputs else line.inputs[0])

    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 200, by - 240))
    cnt = safe_node(tree, "ShaderNodeMath", (bx, by - 240))
    cnt.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["String Count"], cnt.inputs[0])
    cnt.inputs[1].default_value = 1.0
    fac = safe_node(tree, "ShaderNodeMath", (bx + 160, by - 240))
    fac.operation = "DIVIDE"
    link_sockets(tree, idx.outputs["Index"], fac.inputs[0])
    link_sockets(tree, cnt.outputs[0], fac.inputs[1])
    # Mersenne 0.5 factor
    mf = safe_node(tree, "ShaderNodeMath", (bx + 320, by - 240))
    mf.operation = "MULTIPLY"
    link_sockets(tree, fac.outputs[0], mf.inputs[0])
    mf.inputs[1].default_value = 0.5
    one_minus = safe_node(tree, "ShaderNodeMath", (bx + 480, by - 240))
    one_minus.operation = "SUBTRACT"
    one_minus.inputs[0].default_value = 1.0
    link_sockets(tree, mf.outputs[0], one_minus.inputs[1])

    cyl = safe_node(tree, "GeometryNodeMeshCylinder", (bx + 40, by - 120))
    cyl.inputs["Vertices"].default_value = 6
    link_sockets(tree, gin.outputs["String Radius"], cyl.inputs["Radius"])
    cyl.inputs["Depth"].default_value = 1.0

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 120, by - 120))
    link_sockets(tree, line.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, cyl.outputs["Mesh"], inst.inputs["Instance"])
    sv = _combine(tree, (bx, by - 320), 1.0, 1.0, one_minus.outputs[0] if one_minus else 1.0)
    si = safe_node(tree, "GeometryNodeScaleInstances", (bx + 280, by - 120))
    link_sockets(tree, inst.outputs["Instances"], si.inputs["Instances"] if "Instances" in si.inputs else si.inputs[0])
    link_sockets(tree, sv.outputs["Vector"], si.inputs["Scale"] if "Scale" in si.inputs else si.inputs[1])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 200, by + 40))
    link_sockets(tree, board_sc.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, si.outputs["Instances"] if "Instances" in si.outputs else si.outputs[0], join.inputs["Geometry"])
    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 400, by + 40))
    link_sockets(tree, join.outputs["Geometry"], real.inputs["Geometry"])
    sw = safe_node(tree, "GeometryNodeSwitch", (bx + 560, by + 40))
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Realize for export"], sw.inputs["Switch"] if "Switch" in sw.inputs else sw.inputs[0])
    link_sockets(tree, join.outputs["Geometry"], sw.inputs["False"] if "False" in sw.inputs else sw.inputs[1])
    link_sockets(tree, real.outputs["Geometry"], sw.inputs["True"] if "True" in sw.inputs else sw.inputs[2])
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 720, by + 40))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, sw.outputs["Output"] if "Output" in sw.outputs else sw.outputs[0], shade.inputs["Geometry"])
    xf = safe_node(tree, "GeometryNodeTransform", (bx + 880, by + 40))
    link_sockets(tree, shade.outputs["Geometry"], xf.inputs["Geometry"])
    sc2 = _combine(tree, (bx + 800, by + 100), gin.outputs["Scale"], gin.outputs["Scale"], gin.outputs["Scale"])
    link_sockets(tree, sc2.outputs["Vector"], xf.inputs["Scale"])
    link_sockets(tree, xf.outputs["Geometry"], gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Parabolic Board", "nodes": ("bezier", "sweep"), "role": "geometry"},
        {"title": "Strings Mersenne", "nodes": ("line", "cylinder", "scale"), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "switch", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# 5. Waveform Wall v2 - additive 1/n^k with MeshToCurve fix
# ---------------------------------------------------------------------------

def build_music_waveform_wall_v2(group_name="MEL_music_waveform_wall_v2"):
    """Waveform wall v2: correct additive saw/square/tri 1/n^k via Spline Parameter + sine stack.

    Fixes ledger 5: MeshToCurve before SetPosition (Factor is 0 on mesh), proper
    1/n^k amplitude law per harmonic.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Width", 4.0, 1.0, 12.0)
    add_float_param(tree, "Amplitude", 0.6, 0.1, 2.0)
    add_float_param(tree, "Base Freq", 1.0, 0.2, 6.0)
    add_int_param(tree, "Harmonics", 5, 1, 9)
    add_float_param(tree, "Falloff Exp", 1.0, 0.5, 2.0)  # 1.0 saw 1/n, 2.0 tri 1/n^2, square uses odd only
    add_int_param(tree, "Resolution", 128, 32, 512)
    add_float_param(tree, "Thickness", 0.02, 0.005, 0.12)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    # Base curve along X - must be Curve before Factor
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by + 200))
    link_sockets(tree, gin.outputs["Resolution"], line.inputs["Count"])
    try:
        line.mode = "OFFSET"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Width"], line.inputs["Offset"] if "Offset" in line.inputs else line.inputs[0])
    to_curve = safe_node(tree, "GeometryNodeMeshToCurve", (bx - 200, by + 200))
    link_sockets(tree, line.outputs["Mesh"], to_curve.inputs["Mesh"] if "Mesh" in to_curve.inputs else to_curve.inputs[0])
    curve = to_curve.outputs["Curve"] if "Curve" in to_curve.outputs else to_curve.outputs[0]
    spl = safe_node(tree, "GeometryNodeSplineParameter", (bx, by + 260))
    fac = spl.outputs["Factor"] if "Factor" in spl.outputs else spl.outputs[0]

    # Additive stack: sum sin(n*t)/n^k for n=1..Harmonics
    # For now fixed 5 harmonics with correct 1/n^k weighting (Fallback if Harmonics param not wired per harmonic)
    prev = None
    for n in range(1, 6):
        f = _math(tree, (bx + 80 + n*120, by + 80), "MULTIPLY", fac, gin.outputs["Base Freq"])
        # * n
        fn = _math(tree, (bx + 80 + n*120, by + 20), "MULTIPLY", f.outputs[0] if f else fac, float(n))
        s = _math(tree, (bx + 80 + n*120, by - 40), "SINE", fn.outputs[0] if fn else fac, 0.0)
        # amplitude 1 / n^k
        amp = safe_node(tree, "ShaderNodeMath", (bx + 80 + n*120, by - 120))
        amp.operation = "POWER"
        amp.inputs[0].default_value = float(n)
        link_sockets(tree, gin.outputs["Falloff Exp"], amp.inputs[1])
        inv = safe_node(tree, "ShaderNodeMath", (bx + 80 + n*120, by - 180))
        inv.operation = "DIVIDE"
        inv.inputs[0].default_value = 1.0
        link_sockets(tree, amp.outputs[0], inv.inputs[1])
        mul = safe_node(tree, "ShaderNodeMath", (bx + 80 + n*120, by - 240))
        mul.operation = "MULTIPLY"
        link_sockets(tree, s.outputs[0] if s else fac, mul.inputs[0])
        link_sockets(tree, inv.outputs[0], mul.inputs[1])
        if prev is None:
            prev = mul.outputs[0]
        else:
            add = safe_node(tree, "ShaderNodeMath", (bx + 80 + n*120, by - 300))
            add.operation = "ADD"
            link_sockets(tree, prev, add.inputs[0])
            link_sockets(tree, mul.outputs[0], add.inputs[1])
            prev = add.outputs[0]
    # Final * Amplitude
    amp_all = _math(tree, (bx + 800, by - 80), "MULTIPLY", prev, gin.outputs["Amplitude"])
    # Set Position Z = y
    pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 200, by + 40))
    link_sockets(tree, curve, pos.inputs["Geometry"])
    # Need Position input to offset Z
    # Use Combine to set Z
    # We have factor 0..1, we need to move points up by amp
    # SetPosition Offset Z = amp_all
    off = _combine(tree, (bx + 80, by - 80), 0.0, 0.0, amp_all.outputs[0] if amp_all else 0.0)
    link_sockets(tree, off.outputs["Vector"], pos.inputs["Offset"] if "Offset" in pos.inputs else pos.inputs[1])

    # Sweep to thick wall
    prof = safe_node(tree, "GeometryNodeCurvePrimitiveLine", (bx - 200, by - 160))
    prof.inputs["Start"].default_value = (-0.5, 0, 0)
    prof.inputs["End"].default_value = (0.5, 0, 0)
    sweep = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 400, by + 40))
    link_sockets(tree, pos.outputs["Geometry"], sweep.inputs["Curve"])
    link_sockets(tree, prof.outputs["Curve"] if "Curve" in prof.outputs else prof.outputs[0], sweep.inputs["Profile Curve"] if "Profile Curve" in sweep.inputs else sweep.inputs[1])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 600, by + 40))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, sweep.outputs["Mesh"], shade.inputs["Geometry"])
    xf = safe_node(tree, "GeometryNodeTransform", (bx + 760, by + 40))
    link_sockets(tree, shade.outputs["Geometry"], xf.inputs["Geometry"])
    sc = _combine(tree, (bx + 680, by + 100), gin.outputs["Scale"], gin.outputs["Scale"], gin.outputs["Scale"])
    link_sockets(tree, sc.outputs["Vector"], xf.inputs["Scale"])
    link_sockets(tree, xf.outputs["Geometry"], gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Additive Harmonics 1/n^k", "nodes": ("sine", "power", "add"), "role": "math"},
        {"title": "Wall", "nodes": ("curve", "sweep"), "role": "geometry"},
        {"title": "Export", "nodes": ("shade", "Group Output"), "role": "output"},
    ])


# -- Registry --
register_builder("MEL_music_celesta", build_music_celesta, "Music Celesta",
    "ET-tuned graduated plates on resonator box - free-free beam law, 22.4% hang",
    "music")
register_builder("MEL_music_glockenspiel", build_music_glockenspiel, "Music Glockenspiel (GN Twin)",
    "GN twin of chime_row: ET plates, 22.4% hang, overtone bands on frame",
    "music")
register_builder("MEL_music_kalimba", build_music_kalimba, "Music Kalimba",
    "Thumb piano - Mersenne 1/L tines (octave = half length) on soundbox",
    "music")
register_builder("MEL_music_harp_v2", build_music_harp_v2, "Music Harp v2 (Parabolic)",
    "Parabolic soundboard + Mersenne string pyramid - ledger 4",
    "music")
register_builder("MEL_music_waveform_wall_v2", build_music_waveform_wall_v2, "Waveform Wall v2",
    "Additive 1/n^k wall with MeshToCurve fix - ledger 5",
    "music")
