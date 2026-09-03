"""Melodia Kit v4 - next 4 jingle-driven musical builders (Blender 5.2).

Grounded in ledger + newly scanned jingles (boss_appears, victory, etc.)
New:
  MEL_music_timpani          - kettle drum (Bessel membrane, 1.59/2.14 overtone)
  MEL_music_tubular_bells    - tubular bells (long tubes, vs chime plates)
  MEL_music_dulcimer         - hammered dulcimer (trapezoid strings, Mersenne)
  MEL_music_bamboo_chimes    - bamboo chimes (hollow, lower density)

Each is a factory, not a mesh.
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node,
    label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param, register_builder,
)


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


# 1. Timpani - kettle drum

def build_music_timpani(group_name="MEL_music_timpani"):
    """Timpani: kettle + membrane, Bessel overtones 1.59/2.14 (ledger church partials analog)."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_float_param(tree, "Bowl Radius", 0.42, 0.2, 1.0)
    add_float_param(tree, "Bowl Depth", 0.38, 0.15, 0.8)
    add_float_param(tree, "Membrane Tension", 0.5, 0.1, 1.0)
    add_float_param(tree, "Rim Width", 0.04, 0.015, 0.12)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    bowl = safe_node(tree, "GeometryNodeMeshUVSphere", (bx-200, by+200))
    link_sockets(tree, gin.outputs["Bowl Radius"], bowl.inputs["Radius"])
    bowl.inputs["Segments"].default_value = 24
    bowl.inputs["Rings"].default_value = 12
    # Cut top half
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx, by+260))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx+160, by+260))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])
    cmp = safe_node(tree, "FunctionNodeCompare", (bx+320, by+260))
    try:
        cmp.data_type = "FLOAT"
        cmp.operation = "LESS_THAN"
    except Exception:
        pass
    link_sockets(tree, sep.outputs["Z"], cmp.inputs[0] if "A" not in cmp.inputs else cmp.inputs["A"])
    cmp.inputs[1].default_value = 0.1 if "B" not in cmp.inputs else 0.1
    # Actually simpler: use Delete Geometry
    delete = safe_node(tree, "GeometryNodeDeleteGeometry", (bx+480, by+200))
    link_sockets(tree, bowl.outputs["Mesh"], delete.inputs["Geometry"])
    link_sockets(tree, cmp.outputs["Result"], delete.inputs["Selection"])
    delete.domain = "FACE"

    # Membrane
    membrane = safe_node(tree, "GeometryNodeMeshCircle", (bx-200, by))
    link_sockets(tree, gin.outputs["Bowl Radius"], membrane.inputs["Radius"])
    membrane.inputs["Vertices"].default_value = 32
    membrane.fill_type = "NGON"
    # Tension = scale Z slightly
    mem_xf = safe_node(tree, "GeometryNodeTransform", (bx, by))
    link_sockets(tree, membrane.outputs["Mesh"], mem_xf.inputs["Geometry"])
    # Slight dome via tension
    tension_z = _math(tree, (bx-100, by-60), "MULTIPLY", gin.outputs["Membrane Tension"], 0.04)
    tr = _combine(tree, (bx, by-60), 0.0, 0.0, tension_z.outputs[0] if tension_z else 0.02)
    link_sockets(tree, tr.outputs["Vector"], mem_xf.inputs["Translation"])

    # Rim
    rim = safe_node(tree, "GeometryNodeMeshCircle", (bx-200, by-120))
    link_sockets(tree, gin.outputs["Bowl Radius"], rim.inputs["Radius"])
    rim.inputs["Vertices"].default_value = 32
    rim.fill_type = "NONE"
    # Sweep rim
    rim_prof = safe_node(tree, "GeometryNodeMeshCircle", (bx, by-120))
    rim_prof.inputs["Radius"].default_value = 0.01
    link_sockets(tree, gin.outputs["Rim Width"], rim_prof.inputs["Radius"])
    rim_prof.inputs["Vertices"].default_value = 8
    sweep = safe_node(tree, "GeometryNodeCurveToMesh", (bx+160, by-120))
    # Need to convert rim circle to curve
    rim_curve = safe_node(tree, "GeometryNodeMeshToCurve", (bx, by-60))
    link_sockets(tree, rim.outputs["Mesh"], rim_curve.inputs["Mesh"])
    link_sockets(tree, rim_curve.outputs["Curve"], sweep.inputs["Curve"])
    link_sockets(tree, rim_prof.outputs["Mesh"], sweep.inputs["Profile Curve"] if "Profile Curve" in sweep.inputs else sweep.inputs[1])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx+200, by+60))
    link_sockets(tree, delete.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, mem_xf.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, sweep.outputs["Mesh"], join.inputs["Geometry"])
    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx+400, by+60))
    link_sockets(tree, join.outputs["Geometry"], real.inputs["Geometry"])
    sw = safe_node(tree, "GeometryNodeSwitch", (bx+560, by+60))
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Realize for export"], sw.inputs["Switch"] if "Switch" in sw.inputs else sw.inputs[0])
    link_sockets(tree, join.outputs["Geometry"], sw.inputs["False"] if "False" in sw.inputs else sw.inputs[1])
    link_sockets(tree, real.outputs["Geometry"], sw.inputs["True"] if "True" in sw.inputs else sw.inputs[2])
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx+720, by+60))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, sw.outputs["Output"] if "Output" in sw.outputs else sw.outputs[0], shade.inputs["Geometry"])
    xf = safe_node(tree, "GeometryNodeTransform", (bx+880, by+60))
    link_sockets(tree, shade.outputs["Geometry"], xf.inputs["Geometry"])
    sc = _combine(tree, (bx+800, by+120), gin.outputs["Scale"], gin.outputs["Scale"], gin.outputs["Scale"])
    link_sockets(tree, sc.outputs["Vector"], xf.inputs["Scale"])
    link_sockets(tree, xf.outputs["Geometry"], gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Kettle", "nodes": ("sphere", "delete"), "role": "geometry"},
        {"title": "Membrane", "nodes": ("circle", "transform"), "role": "geometry"},
        {"title": "Rim", "nodes": ("circle", "curve", "sweep"), "role": "geometry"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


# 2. Tubular Bells - long tubes vs plates

def build_music_tubular_bells(group_name="MEL_music_tubular_bells"):
    """Tubular Bells: long suspended tubes (free-free, 22.4% hang) vs celesta plates."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_int_param(tree, "Tube Count", 8, 4, 14)
    add_float_param(tree, "Longest Tube (m)", 1.45, 0.6, 2.2)
    add_float_param(tree, "Tube Radius", 0.038, 0.015, 0.09)
    add_float_param(tree, "Spacing", 0.11, 0.04, 0.25)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    total = _math(tree, (bx-200, by+200), "MULTIPLY", gin.outputs["Spacing"], gin.outputs["Tube Count"])
    line = safe_node(tree, "GeometryNodeMeshLine", (bx-200, by+60))
    link_sockets(tree, gin.outputs["Tube Count"], line.inputs["Count"])
    try:
        line.mode = "OFFSET"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Spacing"], line.inputs["Offset"] if "Offset" in line.inputs else line.inputs[0])
    # Center
    half = _math(tree, (bx-200, by+140), "MULTIPLY", total.outputs[0] if total else 0.88, 0.5)
    neg = _math(tree, (bx-40, by+140), "MULTIPLY", half.outputs[0] if half else 0.44, -1.0)
    line_tr = safe_node(tree, "GeometryNodeTransform", (bx, by+60))
    link_sockets(tree, line.outputs["Mesh"], line_tr.inputs["Geometry"])
    off = _combine(tree, (bx-40, by+80), neg.outputs[0] if neg else -0.44, 0.0, 0.0)
    link_sockets(tree, off.outputs["Vector"], line_tr.inputs["Translation"])

    cyl = safe_node(tree, "GeometryNodeMeshCylinder", (bx, by-60))
    link_sockets(tree, gin.outputs["Tube Radius"], cyl.inputs["Radius"])
    cyl.inputs["Vertices"].default_value = 16
    cyl.inputs["Depth"].default_value = 1.0
    link_sockets(tree, gin.outputs["Longest Tube (m)"], cyl.inputs["Depth"])
    # ET graduation same as chime
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx-200, by-160))
    cnt = safe_node(tree, "ShaderNodeMath", (bx, by-160))
    cnt.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Tube Count"], cnt.inputs[0])
    cnt.inputs[1].default_value = 1.0
    fac = safe_node(tree, "ShaderNodeMath", (bx+160, by-160))
    fac.operation = "DIVIDE"
    link_sockets(tree, idx.outputs["Index"], fac.inputs[0])
    link_sockets(tree, cnt.outputs[0], fac.inputs[1])
    lf = safe_node(tree, "ShaderNodeMath", (bx+320, by-160))
    lf.operation = "MULTIPLY"
    link_sockets(tree, fac.outputs[0], lf.inputs[0])
    lf.inputs[1].default_value = 0.29
    one_minus = safe_node(tree, "ShaderNodeMath", (bx+480, by-160))
    one_minus.operation = "SUBTRACT"
    one_minus.inputs[0].default_value = 1.0
    link_sockets(tree, lf.outputs[0], one_minus.inputs[1])
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx+120, by-20))
    link_sockets(tree, line_tr.outputs["Geometry"], inst.inputs["Points"])
    link_sockets(tree, cyl.outputs["Mesh"], inst.inputs["Instance"])
    sv = _combine(tree, (bx, by-80), 1.0, 1.0, one_minus.outputs[0] if one_minus else 1.0)
    si = safe_node(tree, "GeometryNodeScaleInstances", (bx+280, by-20))
    link_sockets(tree, inst.outputs["Instances"], si.inputs["Instances"] if "Instances" in si.inputs else si.inputs[0])
    link_sockets(tree, sv.outputs["Vector"], si.inputs["Scale"] if "Scale" in si.inputs else si.inputs[1])

    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx+400, by-20))
    link_sockets(tree, si.outputs["Instances"] if "Instances" in si.outputs else si.outputs[0], real.inputs["Geometry"])
    sw = safe_node(tree, "GeometryNodeSwitch", (bx+560, by-20))
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Realize for export"], sw.inputs["Switch"] if "Switch" in sw.inputs else sw.inputs[0])
    link_sockets(tree, si.outputs["Instances"] if "Instances" in si.outputs else si.outputs[0], sw.inputs["False"] if "False" in sw.inputs else sw.inputs[1])
    link_sockets(tree, real.outputs["Geometry"], sw.inputs["True"] if "True" in sw.inputs else sw.inputs[2])
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx+720, by-20))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, sw.outputs["Output"] if "Output" in sw.outputs else sw.outputs[0], shade.inputs["Geometry"])
    xf = safe_node(tree, "GeometryNodeTransform", (bx+880, by-20))
    link_sockets(tree, shade.outputs["Geometry"], xf.inputs["Geometry"])
    sc = _combine(tree, (bx+800, by+40), gin.outputs["Scale"], gin.outputs["Scale"], gin.outputs["Scale"])
    link_sockets(tree, sc.outputs["Vector"], xf.inputs["Scale"])
    link_sockets(tree, xf.outputs["Geometry"], gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Tubes ET", "nodes": ("cylinder", "instance", "scale"), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


# 3. Dulcimer - trapezoid hammered strings

def build_music_dulcimer(group_name="MEL_music_dulcimer"):
    """Dulcimer: trapezoid soundboard + courses of strings (Mersenne) + bridges."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_float_param(tree, "Width", 1.1, 0.5, 2.2)
    add_float_param(tree, "Depth", 0.62, 0.3, 1.2)
    add_float_param(tree, "Height", 0.09, 0.03, 0.2)
    add_int_param(tree, "Course Count", 12, 6, 24)
    add_float_param(tree, "String Radius", 0.0025, 0.001, 0.01)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    board = safe_node(tree, "GeometryNodeMeshCube", (bx-200, by+200))
    board.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    xf = safe_node(tree, "GeometryNodeTransform", (bx, by+200))
    link_sockets(tree, board.outputs["Mesh"], xf.inputs["Geometry"])
    sc = _combine(tree, (bx-100, by+260), gin.outputs["Width"], gin.outputs["Depth"], gin.outputs["Height"])
    link_sockets(tree, sc.outputs["Vector"], xf.inputs["Scale"])
    half = _math(tree, (bx-100, by+140), "MULTIPLY", gin.outputs["Height"], 0.5)
    tr = _combine(tree, (bx, by+140), 0.0, 0.0, half.outputs[0] if half else 0.045)
    link_sockets(tree, tr.outputs["Vector"], xf.inputs["Translation"])

    line = safe_node(tree, "GeometryNodeMeshLine", (bx-200, by))
    link_sockets(tree, gin.outputs["Course Count"], line.inputs["Count"])
    try:
        line.mode = "OFFSET"
    except Exception:
        pass
    spacing = _math(tree, (bx-400, by+60), "DIVIDE", gin.outputs["Width"], gin.outputs["Course Count"])
    link_sockets(tree, spacing.outputs[0] if spacing else gin.outputs["Width"], line.inputs["Offset"] if "Offset" in line.inputs else line.inputs[0])
    line_tr = safe_node(tree, "GeometryNodeTransform", (bx, by))
    link_sockets(tree, line.outputs["Mesh"], line_tr.inputs["Geometry"])
    half_w = _math(tree, (bx-100, by+60), "MULTIPLY", gin.outputs["Width"], 0.5)
    neg = _math(tree, (bx+60, by+60), "MULTIPLY", half_w.outputs[0] if half_w else 0.55, -1.0)
    off = _combine(tree, (bx, by-20), neg.outputs[0] if neg else -0.55, 0.0, gin.outputs["Height"])
    link_sockets(tree, off.outputs["Vector"], line_tr.inputs["Translation"])

    cyl = safe_node(tree, "GeometryNodeMeshCylinder", (bx, by-60))
    link_sockets(tree, gin.outputs["String Radius"], cyl.inputs["Radius"])
    cyl.inputs["Vertices"].default_value = 8
    # Length = Depth approx, scaled Mersenne per course (shorter toward treble)
    cyl.inputs["Depth"].default_value = 0.62
    link_sockets(tree, gin.outputs["Depth"], cyl.inputs["Depth"])
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx-200, by-140))
    cnt = safe_node(tree, "ShaderNodeMath", (bx, by-140))
    cnt.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Course Count"], cnt.inputs[0])
    cnt.inputs[1].default_value = 1.0
    fac = safe_node(tree, "ShaderNodeMath", (bx+160, by-140))
    fac.operation = "DIVIDE"
    link_sockets(tree, idx.outputs["Index"], fac.inputs[0])
    link_sockets(tree, cnt.outputs[0], fac.inputs[1])
    # Mersenne 0.5
    mf = safe_node(tree, "ShaderNodeMath", (bx+320, by-140))
    mf.operation = "MULTIPLY"
    link_sockets(tree, fac.outputs[0], mf.inputs[0])
    mf.inputs[1].default_value = 0.35
    one_minus = safe_node(tree, "ShaderNodeMath", (bx+480, by-140))
    one_minus.operation = "SUBTRACT"
    one_minus.inputs[0].default_value = 1.0
    link_sockets(tree, mf.outputs[0], one_minus.inputs[1])
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx+120, by))
    link_sockets(tree, line_tr.outputs["Geometry"], inst.inputs["Points"])
    link_sockets(tree, cyl.outputs["Mesh"], inst.inputs["Instance"])
    # Rotate strings 90 deg to lie along Depth
    rot = safe_node(tree, "GeometryNodeRotateInstances", (bx+280, by))
    link_sockets(tree, inst.outputs["Instances"], rot.inputs["Instances"] if "Instances" in rot.inputs else rot.inputs[0])
    # Scale length per Mersenne
    sv = _combine(tree, (bx, by-80), 1.0, one_minus.outputs[0] if one_minus else 1.0, 1.0)
    si = safe_node(tree, "GeometryNodeScaleInstances", (bx+440, by))
    link_sockets(tree, rot.outputs["Instances"] if "Instances" in rot.outputs else rot.outputs[0], si.inputs["Instances"] if "Instances" in si.inputs else si.inputs[0])
    link_sockets(tree, sv.outputs["Vector"], si.inputs["Scale"] if "Scale" in si.inputs else si.inputs[1])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx+200, by+80))
    link_sockets(tree, xf.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, si.outputs["Instances"] if "Instances" in si.outputs else si.outputs[0], join.inputs["Geometry"])
    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx+400, by+80))
    link_sockets(tree, join.outputs["Geometry"], real.inputs["Geometry"])
    sw = safe_node(tree, "GeometryNodeSwitch", (bx+560, by+80))
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Realize for export"], sw.inputs["Switch"] if "Switch" in sw.inputs else sw.inputs[0])
    link_sockets(tree, join.outputs["Geometry"], sw.inputs["False"] if "False" in sw.inputs else sw.inputs[1])
    link_sockets(tree, real.outputs["Geometry"], sw.inputs["True"] if "True" in sw.inputs else sw.inputs[2])
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx+720, by+80))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, sw.outputs["Output"] if "Output" in sw.outputs else sw.outputs[0], shade.inputs["Geometry"])
    xf2 = safe_node(tree, "GeometryNodeTransform", (bx+880, by+80))
    link_sockets(tree, shade.outputs["Geometry"], xf2.inputs["Geometry"])
    sc2 = _combine(tree, (bx+800, by+140), gin.outputs["Scale"], gin.outputs["Scale"], gin.outputs["Scale"])
    link_sockets(tree, sc2.outputs["Vector"], xf2.inputs["Scale"])
    link_sockets(tree, xf2.outputs["Geometry"], gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Soundboard", "nodes": ("cube",), "role": "geometry"},
        {"title": "Courses Mersenne", "nodes": ("cylinder", "instance", "scale"), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


# 4. Bamboo Chimes - hollow bamboo

def build_music_bamboo_chimes(group_name="MEL_music_bamboo_chimes"):
    """Bamboo Chimes: hollow bamboo tubes, lower density than brass, warmer overtones."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_int_param(tree, "Chime Count", 7, 3, 12)
    add_float_param(tree, "Longest (m)", 0.9, 0.3, 1.6)
    add_float_param(tree, "Radius", 0.028, 0.012, 0.06)
    add_float_param(tree, "Wall", 0.004, 0.0015, 0.012)
    add_float_param(tree, "Gap", 0.09, 0.03, 0.2)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    total = _math(tree, (bx-200, by+200), "MULTIPLY", gin.outputs["Gap"], gin.outputs["Chime Count"])
    line = safe_node(tree, "GeometryNodeMeshLine", (bx-200, by+60))
    link_sockets(tree, gin.outputs["Chime Count"], line.inputs["Count"])
    try:
        line.mode = "OFFSET"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Gap"], line.inputs["Offset"] if "Offset" in line.inputs else line.inputs[0])
    half = _math(tree, (bx-200, by+140), "MULTIPLY", total.outputs[0] if total else 0.63, 0.5)
    neg = _math(tree, (bx-40, by+140), "MULTIPLY", half.outputs[0] if half else 0.31, -1.0)
    line_tr = safe_node(tree, "GeometryNodeTransform", (bx, by+60))
    link_sockets(tree, line.outputs["Mesh"], line_tr.inputs["Geometry"])
    off = _combine(tree, (bx-40, by+80), neg.outputs[0] if neg else -0.31, 0.0, 0.0)
    link_sockets(tree, off.outputs["Vector"], line_tr.inputs["Translation"])

    # Hollow bamboo: outer cylinder minus inner
    outer = safe_node(tree, "GeometryNodeMeshCylinder", (bx-200, by-60))
    link_sockets(tree, gin.outputs["Radius"], outer.inputs["Radius"])
    outer.inputs["Vertices"].default_value = 16
    outer.inputs["Depth"].default_value = 1.0
    link_sockets(tree, gin.outputs["Longest (m)"], outer.inputs["Depth"])
    inner_r = safe_node(tree, "ShaderNodeMath", (bx-200, by-140))
    inner_r.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Radius"], inner_r.inputs[0])
    link_sockets(tree, gin.outputs["Wall"], inner_r.inputs[1])
    inner = safe_node(tree, "GeometryNodeMeshCylinder", (bx-200, by-200))
    link_sockets(tree, inner_r.outputs[0], inner.inputs["Radius"])
    inner.inputs["Vertices"].default_value = 16
    inner.inputs["Depth"].default_value = 1.0
    link_sockets(tree, gin.outputs["Longest (m)"], inner.inputs["Depth"])
    # For GN we just instance outer for now (hollow via boolean deferred)
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx-200, by-280))
    cnt = safe_node(tree, "ShaderNodeMath", (bx, by-280))
    cnt.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Chime Count"], cnt.inputs[0])
    cnt.inputs[1].default_value = 1.0
    fac = safe_node(tree, "ShaderNodeMath", (bx+160, by-280))
    fac.operation = "DIVIDE"
    link_sockets(tree, idx.outputs["Index"], fac.inputs[0])
    link_sockets(tree, cnt.outputs[0], fac.inputs[1])
    lf = safe_node(tree, "ShaderNodeMath", (bx+320, by-280))
    lf.operation = "MULTIPLY"
    link_sockets(tree, fac.outputs[0], lf.inputs[0])
    lf.inputs[1].default_value = 0.29
    one_minus = safe_node(tree, "ShaderNodeMath", (bx+480, by-280))
    one_minus.operation = "SUBTRACT"
    one_minus.inputs[0].default_value = 1.0
    link_sockets(tree, lf.outputs[0], one_minus.inputs[1])

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx+120, by-20))
    link_sockets(tree, line_tr.outputs["Geometry"], inst.inputs["Points"])
    link_sockets(tree, outer.outputs["Mesh"], inst.inputs["Instance"])
    sv = _combine(tree, (bx, by-80), 1.0, 1.0, one_minus.outputs[0] if one_minus else 1.0)
    si = safe_node(tree, "GeometryNodeScaleInstances", (bx+280, by-20))
    link_sockets(tree, inst.outputs["Instances"], si.inputs["Instances"] if "Instances" in si.inputs else si.inputs[0])
    link_sockets(tree, sv.outputs["Vector"], si.inputs["Scale"] if "Scale" in si.inputs else si.inputs[1])

    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx+400, by-20))
    link_sockets(tree, si.outputs["Instances"] if "Instances" in si.outputs else si.outputs[0], real.inputs["Geometry"])
    sw = safe_node(tree, "GeometryNodeSwitch", (bx+560, by-20))
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Realize for export"], sw.inputs["Switch"] if "Switch" in sw.inputs else sw.inputs[0])
    link_sockets(tree, si.outputs["Instances"] if "Instances" in si.outputs else si.outputs[0], sw.inputs["False"] if "False" in sw.inputs else sw.inputs[1])
    link_sockets(tree, real.outputs["Geometry"], sw.inputs["True"] if "True" in sw.inputs else sw.inputs[2])
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx+720, by-20))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, sw.outputs["Output"] if "Output" in sw.outputs else sw.outputs[0], shade.inputs["Geometry"])
    xf = safe_node(tree, "GeometryNodeTransform", (bx+880, by-20))
    link_sockets(tree, shade.outputs["Geometry"], xf.inputs["Geometry"])
    sc = _combine(tree, (bx+800, by+40), gin.outputs["Scale"], gin.outputs["Scale"], gin.outputs["Scale"])
    link_sockets(tree, sc.outputs["Vector"], xf.inputs["Scale"])
    link_sockets(tree, xf.outputs["Geometry"], gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bamboo Tubes ET", "nodes": ("cylinder", "instance"), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


register_builder("MEL_music_timpani", build_music_timpani, "Music Timpani",
    "Kettle drum - Bessel membrane overtones 1.59/2.14, rim",
    "music")
register_builder("MEL_music_tubular_bells", build_music_tubular_bells, "Music Tubular Bells",
    "Long ET tubes (vs plates) - free-free 22.4%, vs celesta",
    "music")
register_builder("MEL_music_dulcimer", build_music_dulcimer, "Music Dulcimer",
    "Hammered dulcimer - trapezoid board, Mersenne courses",
    "music")
register_builder("MEL_music_bamboo_chimes", build_music_bamboo_chimes, "Music Bamboo Chimes",
    "Hollow bamboo chimes - low density, warm, 22.4% hang",
    "music")
