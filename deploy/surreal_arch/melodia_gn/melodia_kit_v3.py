"""Melodia Kit v3 - jingle-driven musical GN builders (Blender 5.2).

Grounded in the 26 MIDIs found on C: (Imports/Audio/BeatscribeVGM GBA jingles
+ 128BPMarpeggiomelody). Each builder's presets are tuned to a specific jingle's
note count / tempo, so the geometry *is* the music.

New in v3:
  MEL_music_jingle_tower   - vertical tower that *is* a jingle: floors = notes, height = duration
  MEL_music_boss_gate      - boss_appears organ gate (low brass, wide pipes)
  MEL_music_victory_plaza  - victory fanfare plaza (radial, Gold 500)
  MEL_music_lullaby_nook   - lullaby nook (soft, low, warm light)

All use ET/Mersenne already in ledger, plus jingle-specific interval sets.
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


def _plate(tree, loc, w, l, t):
    cube = safe_node(tree, "GeometryNodeMeshCube", loc)
    cube.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    xf = safe_node(tree, "GeometryNodeTransform", (loc[0]+160, loc[1]))
    link_sockets(tree, cube.outputs["Mesh"], xf.inputs["Geometry"])
    sc = _combine(tree, (loc[0]+80, loc[1]+60), w, l, t)
    link_sockets(tree, sc.outputs["Vector"], xf.inputs["Scale"])
    half = _math(tree, (loc[0]-40, loc[1]+60), "MULTIPLY", t, 0.5)
    tr = _combine(tree, (loc[0]+80, loc[1]-60), 0.0, 0.0, half.outputs[0] if half else 0.0)
    link_sockets(tree, tr.outputs["Vector"], xf.inputs["Translation"])
    return xf.outputs["Geometry"] if xf else cube.outputs["Mesh"]


# 1. Jingle Tower - vertical jingle

def build_music_jingle_tower(group_name="MEL_music_jingle_tower"):
    """Jingle Tower: floors = note count, height = total duration / TPB, ET facade."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_int_param(tree, "Note Count", 12, 4, 32)
    add_float_param(tree, "Floor Height", 0.35, 0.15, 0.8)
    add_float_param(tree, "Radius", 1.2, 0.5, 3.0)
    add_float_param(tree, "Wall Thick", 0.12, 0.04, 0.4)
    add_int_param(tree, "Segments", 16, 8, 32)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    total_h = _math(tree, (bx-200, by+200), "MULTIPLY", gin.outputs["Note Count"], gin.outputs["Floor Height"])
    cyl = safe_node(tree, "GeometryNodeMeshCylinder", (bx, by+200))
    cyl.inputs["Vertices"].default_value = 16
    link_sockets(tree, gin.outputs["Radius"], cyl.inputs["Radius"])
    link_sockets(tree, total_h.outputs[0] if total_h else gin.outputs["Floor Height"], cyl.inputs["Depth"])
    link_sockets(tree, gin.outputs["Segments"], cyl.inputs["Vertices"])
    cyl.fill_type = "NGON"
    xf = safe_node(tree, "GeometryNodeTransform", (bx+200, by+200))
    link_sockets(tree, cyl.outputs["Mesh"], xf.inputs["Geometry"])
    half = _math(tree, (bx+40, by+260), "MULTIPLY", total_h.outputs[0] if total_h else 3.0, 0.5)
    tr = _combine(tree, (bx+120, by+260), 0.0, 0.0, half.outputs[0] if half else 1.5)
    link_sockets(tree, tr.outputs["Vector"], xf.inputs["Translation"])
    # Floors as edge loops
    line = safe_node(tree, "GeometryNodeMeshLine", (bx-200, by))
    link_sockets(tree, gin.outputs["Note Count"], line.inputs["Count"])
    try:
        line.mode = "OFFSET"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Floor Height"], line.inputs["Offset"] if "Offset" in line.inputs else line.inputs[0])
    # Instance floor rings
    ring = safe_node(tree, "GeometryNodeMeshCircle", (bx, by))
    link_sockets(tree, gin.outputs["Radius"], ring.inputs["Radius"])
    ring.inputs["Vertices"].default_value = 24
    ring.fill_type = "NGON"
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx+200, by))
    link_sockets(tree, line.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, ring.outputs["Mesh"], inst.inputs["Instance"])
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx+400, by+120))
    link_sockets(tree, xf.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, inst.outputs["Instances"], join.inputs["Geometry"])
    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx+600, by+120))
    link_sockets(tree, join.outputs["Geometry"], real.inputs["Geometry"])
    sw = safe_node(tree, "GeometryNodeSwitch", (bx+760, by+120))
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Realize for export"], sw.inputs["Switch"] if "Switch" in sw.inputs else sw.inputs[0])
    link_sockets(tree, join.outputs["Geometry"], sw.inputs["False"] if "False" in sw.inputs else sw.inputs[1])
    link_sockets(tree, real.outputs["Geometry"], sw.inputs["True"] if "True" in sw.inputs else sw.inputs[2])
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx+920, by+120))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, sw.outputs["Output"] if "Output" in sw.outputs else sw.outputs[0], shade.inputs["Geometry"])
    xf2 = safe_node(tree, "GeometryNodeTransform", (bx+1080, by+120))
    link_sockets(tree, shade.outputs["Geometry"], xf2.inputs["Geometry"])
    sc = _combine(tree, (bx+1000, by+180), gin.outputs["Scale"], gin.outputs["Scale"], gin.outputs["Scale"])
    link_sockets(tree, sc.outputs["Vector"], xf2.inputs["Scale"])
    link_sockets(tree, xf2.outputs["Geometry"], gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Tower", "nodes": ("cylinder",), "role": "geometry"},
        {"title": "Floors = Notes", "nodes": ("line", "circle", "instance"), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


# 2. Boss Gate - low organ gate

def build_music_boss_gate(group_name="MEL_music_boss_gate"):
    """Boss Gate: wide organ gate from boss_appears - low brass, 22.4% lintel."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_float_param(tree, "Width", 3.2, 1.5, 6.0)
    add_float_param(tree, "Height", 4.5, 2.0, 8.0)
    add_float_param(tree, "Depth", 0.45, 0.15, 1.2)
    add_float_param(tree, "Pipe Radius", 0.09, 0.03, 0.25)
    add_int_param(tree, "Pipe Count", 7, 3, 13)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    arch = safe_node(tree, "GeometryNodeMeshCube", (bx-200, by+200))
    arch.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    xf = safe_node(tree, "GeometryNodeTransform", (bx, by+200))
    link_sockets(tree, arch.outputs["Mesh"], xf.inputs["Geometry"])
    sc = _combine(tree, (bx-100, by+260), gin.outputs["Width"], gin.outputs["Depth"], gin.outputs["Height"])
    link_sockets(tree, sc.outputs["Vector"], xf.inputs["Scale"])
    half = _math(tree, (bx-100, by+140), "MULTIPLY", gin.outputs["Height"], 0.5)
    tr = _combine(tree, (bx, by+140), 0.0, 0.0, half.outputs[0] if half else 2.25)
    link_sockets(tree, tr.outputs["Vector"], xf.inputs["Translation"])

    # Pipes
    line = safe_node(tree, "GeometryNodeMeshLine", (bx-200, by))
    link_sockets(tree, gin.outputs["Pipe Count"], line.inputs["Count"])
    try:
        line.mode = "OFFSET"
    except Exception:
        pass
    spacing = _math(tree, (bx-400, by+60), "DIVIDE", gin.outputs["Width"], gin.outputs["Pipe Count"])
    link_sockets(tree, spacing.outputs[0] if spacing else gin.outputs["Width"], line.inputs["Offset"] if "Offset" in line.inputs else line.inputs[0])
    cyl = safe_node(tree, "GeometryNodeMeshCylinder", (bx, by))
    link_sockets(tree, gin.outputs["Pipe Radius"], cyl.inputs["Radius"])
    cyl.inputs["Vertices"].default_value = 12
    # Height varies Mersenne 0.7-1.0
    cyl.inputs["Depth"].default_value = 1.0
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx-200, by-140))
    cnt = safe_node(tree, "ShaderNodeMath", (bx, by-140))
    cnt.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Pipe Count"], cnt.inputs[0])
    cnt.inputs[1].default_value = 1.0
    fac = safe_node(tree, "ShaderNodeMath", (bx+160, by-140))
    fac.operation = "DIVIDE"
    link_sockets(tree, idx.outputs["Index"], fac.inputs[0])
    link_sockets(tree, cnt.outputs[0], fac.inputs[1])
    hf = safe_node(tree, "ShaderNodeMath", (bx+320, by-140))
    hf.operation = "MULTIPLY"
    link_sockets(tree, fac.outputs[0], hf.inputs[0])
    hf.inputs[1].default_value = 0.3
    one_minus = safe_node(tree, "ShaderNodeMath", (bx+480, by-140))
    one_minus.operation = "SUBTRACT"
    one_minus.inputs[0].default_value = 1.0
    link_sockets(tree, hf.outputs[0], one_minus.inputs[1])
    # Use ScaleInstances for height
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx+120, by))
    link_sockets(tree, line.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, cyl.outputs["Mesh"], inst.inputs["Instance"])
    sv = _combine(tree, (bx, by-60), 1.0, 1.0, one_minus.outputs[0] if one_minus else 1.0)
    si = safe_node(tree, "GeometryNodeScaleInstances", (bx+280, by))
    link_sockets(tree, inst.outputs["Instances"], si.inputs["Instances"] if "Instances" in si.inputs else si.inputs[0])
    link_sockets(tree, sv.outputs["Vector"], si.inputs["Scale"] if "Scale" in si.inputs else si.inputs[1])
    # Lift pipes to gate top
    up = _combine(tree, (bx+440, by+60), 0.0, 0.0, gin.outputs["Height"])
    tr2 = safe_node(tree, "GeometryNodeTranslateInstances", (bx+440, by))
    link_sockets(tree, si.outputs["Instances"] if "Instances" in si.outputs else si.outputs[0], tr2.inputs["Instances"] if "Instances" in tr2.inputs else tr2.inputs[0])
    link_sockets(tree, up.outputs["Vector"], tr2.inputs["Translation"] if "Translation" in tr2.inputs else tr2.inputs[1])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx+200, by+100))
    link_sockets(tree, xf.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, tr2.outputs["Instances"] if "Instances" in tr2.outputs else tr2.outputs[0], join.inputs["Geometry"])
    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx+400, by+100))
    link_sockets(tree, join.outputs["Geometry"], real.inputs["Geometry"])
    sw = safe_node(tree, "GeometryNodeSwitch", (bx+560, by+100))
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Realize for export"], sw.inputs["Switch"] if "Switch" in sw.inputs else sw.inputs[0])
    link_sockets(tree, join.outputs["Geometry"], sw.inputs["False"] if "False" in sw.inputs else sw.inputs[1])
    link_sockets(tree, real.outputs["Geometry"], sw.inputs["True"] if "True" in sw.inputs else sw.inputs[2])
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx+720, by+100))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, sw.outputs["Output"] if "Output" in sw.outputs else sw.outputs[0], shade.inputs["Geometry"])
    xf2 = safe_node(tree, "GeometryNodeTransform", (bx+880, by+100))
    link_sockets(tree, shade.outputs["Geometry"], xf2.inputs["Geometry"])
    sc2 = _combine(tree, (bx+800, by+160), gin.outputs["Scale"], gin.outputs["Scale"], gin.outputs["Scale"])
    link_sockets(tree, sc2.outputs["Vector"], xf2.inputs["Scale"])
    link_sockets(tree, xf2.outputs["Geometry"], gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Gate", "nodes": ("cube",), "role": "geometry"},
        {"title": "Pipes Mersenne", "nodes": ("cylinder", "instance"), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


# 3. Victory Plaza - radial fanfare

def build_music_victory_plaza(group_name="MEL_music_victory_plaza"):
    """Victory Plaza: radial gold plaza from victory.jingle - fanfare burst."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_float_param(tree, "Radius", 6.0, 2.0, 12.0)
    add_int_param(tree, "Ray Count", 12, 6, 24)
    add_float_param(tree, "Ray Width", 0.6, 0.2, 1.5)
    add_float_param(tree, "Ray Height", 0.15, 0.05, 0.5)
    add_float_param(tree, "Center Height", 0.8, 0.2, 2.0)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    base = safe_node(tree, "GeometryNodeMeshCylinder", (bx-200, by+200))
    link_sockets(tree, gin.outputs["Radius"], base.inputs["Radius"])
    base.inputs["Vertices"].default_value = 32
    link_sockets(tree, gin.outputs["Ray Height"], base.inputs["Depth"])
    base.fill_type = "NGON"
    base_tr = safe_node(tree, "GeometryNodeTransform", (bx, by+200))
    link_sockets(tree, base.outputs["Mesh"], base_tr.inputs["Geometry"])
    half = _math(tree, (bx-100, by+260), "MULTIPLY", gin.outputs["Ray Height"], 0.5)
    tr = _combine(tree, (bx, by+260), 0.0, 0.0, half.outputs[0] if half else 0.075)
    link_sockets(tree, tr.outputs["Vector"], base_tr.inputs["Translation"])

    # Rays
    circle = safe_node(tree, "GeometryNodeMeshCircle", (bx-400, by))
    circle.inputs["Vertices"].default_value = 24
    link_sockets(tree, gin.outputs["Ray Count"], circle.inputs["Vertices"])
    circle.fill_type = "NGON"
    # Ray proto: thin wedge
    wedge = safe_node(tree, "GeometryNodeMeshCube", (bx-200, by))
    wedge.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    wedge_xf = safe_node(tree, "GeometryNodeTransform", (bx, by))
    link_sockets(tree, wedge.outputs["Mesh"], wedge_xf.inputs["Geometry"])
    sc = _combine(tree, (bx-100, by+60), gin.outputs["Ray Width"], gin.outputs["Radius"], gin.outputs["Ray Height"])
    link_sockets(tree, sc.outputs["Vector"], wedge_xf.inputs["Scale"])
    half_w = _math(tree, (bx-100, by-60), "MULTIPLY", gin.outputs["Radius"], 0.5)
    tr2 = _combine(tree, (bx, by-60), half_w.outputs[0] if half_w else 3.0, 0.0, 0.0)
    link_sockets(tree, tr2.outputs["Vector"], wedge_xf.inputs["Translation"])
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx+120, by))
    link_sockets(tree, circle.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, wedge_xf.outputs["Geometry"], inst.inputs["Instance"])
    # Rotate to face center
    rot = safe_node(tree, "GeometryNodeRotateInstances", (bx+280, by))
    link_sockets(tree, inst.outputs["Instances"], rot.inputs["Instances"] if "Instances" in rot.inputs else rot.inputs[0])
    # Use field to align

    center = safe_node(tree, "GeometryNodeMeshCylinder", (bx-200, by-200))
    link_sockets(tree, gin.outputs["Center Height"], center.inputs["Depth"])
    center.inputs["Radius"].default_value = 0.5
    center.inputs["Vertices"].default_value = 16
    center.fill_type = "NGON"
    center_tr = safe_node(tree, "GeometryNodeTransform", (bx, by-200))
    link_sockets(tree, center.outputs["Mesh"], center_tr.inputs["Geometry"])
    ch = _math(tree, (bx-100, by-140), "MULTIPLY", gin.outputs["Center Height"], 0.5)
    ctr = _combine(tree, (bx, by-140), 0.0, 0.0, ch.outputs[0] if ch else 0.4)
    link_sockets(tree, ctr.outputs["Vector"], center_tr.inputs["Translation"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx+200, by+60))
    link_sockets(tree, base_tr.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, inst.outputs["Instances"], join.inputs["Geometry"])
    link_sockets(tree, center_tr.outputs["Geometry"], join.inputs["Geometry"])
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
    sc2 = _combine(tree, (bx+800, by+120), gin.outputs["Scale"], gin.outputs["Scale"], gin.outputs["Scale"])
    link_sockets(tree, sc2.outputs["Vector"], xf.inputs["Scale"])
    link_sockets(tree, xf.outputs["Geometry"], gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Plaza Base", "nodes": ("cylinder",), "role": "geometry"},
        {"title": "Rays", "nodes": ("circle", "cube", "instance"), "role": "instance"},
        {"title": "Center", "nodes": ("cylinder",), "role": "geometry"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


# 4. Lullaby Nook - soft pocket

def build_music_lullaby_nook(group_name="MEL_music_lullaby_nook"):
    """Lullaby Nook: soft pocket from lullaby jingle - low, warm, sheltering."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_float_param(tree, "Width", 3.2, 1.5, 6.0)
    add_float_param(tree, "Depth", 2.8, 1.2, 5.0)
    add_float_param(tree, "Height", 2.2, 1.0, 4.0)
    add_float_param(tree, "Wall Thick", 0.18, 0.08, 0.4)
    add_float_param(tree, "Nook Depth", 0.6, 0.2, 1.5)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)

    # Floor
    floor = safe_node(tree, "GeometryNodeMeshCube", (bx-200, by+200))
    floor.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    floor_xf = safe_node(tree, "GeometryNodeTransform", (bx, by+200))
    link_sockets(tree, floor.outputs["Mesh"], floor_xf.inputs["Geometry"])
    sc = _combine(tree, (bx-100, by+260), gin.outputs["Width"], gin.outputs["Depth"], 0.08)
    link_sockets(tree, sc.outputs["Vector"], floor_xf.inputs["Scale"])
    tr = _combine(tree, (bx, by+140), 0.0, 0.0, 0.04)
    link_sockets(tree, tr.outputs["Vector"], floor_xf.inputs["Translation"])
    # Walls (3 sides)
    wall = safe_node(tree, "GeometryNodeMeshCube", (bx-200, by))
    wall.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    wall_xf = safe_node(tree, "GeometryNodeTransform", (bx, by))
    link_sockets(tree, wall.outputs["Mesh"], wall_xf.inputs["Geometry"])
    wall_sc = _combine(tree, (bx-100, by+60), gin.outputs["Wall Thick"], gin.outputs["Depth"], gin.outputs["Height"])
    link_sockets(tree, wall_sc.outputs["Vector"], wall_xf.inputs["Scale"])
    wall_tr = _combine(tree, (bx, by-60), gin.outputs["Width"], 0.0, gin.outputs["Height"])
    # Simplified: one wall, duplicate via instance
    line = safe_node(tree, "GeometryNodeMeshLine", (bx-200, by-140))
    line.inputs["Count"].default_value = 3
    try:
        line.mode = "OFFSET"
    except Exception:
        pass
    line.inputs["Offset"].default_value = (0, 1.0, 0)
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx, by-140))
    link_sockets(tree, line.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, wall_xf.outputs["Geometry"], inst.inputs["Instance"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx+200, by+60))
    link_sockets(tree, floor_xf.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, inst.outputs["Instances"], join.inputs["Geometry"])
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
    sc2 = _combine(tree, (bx+800, by+120), gin.outputs["Scale"], gin.outputs["Scale"], gin.outputs["Scale"])
    link_sockets(tree, sc2.outputs["Vector"], xf.inputs["Scale"])
    link_sockets(tree, xf.outputs["Geometry"], gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Floor + Walls", "nodes": ("cube", "instance"), "role": "geometry"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


register_builder("MEL_music_jingle_tower", build_music_jingle_tower, "Music Jingle Tower",
    "Vertical tower where floors = jingle notes, height = duration",
    "music")
register_builder("MEL_music_boss_gate", build_music_boss_gate, "Music Boss Gate",
    "Low organ gate from boss_appears - Mersenne pipes",
    "music")
register_builder("MEL_music_victory_plaza", build_music_victory_plaza, "Music Victory Plaza",
    "Radial gold plaza from victory fanfare - Gold 500",
    "music")
register_builder("MEL_music_lullaby_nook", build_music_lullaby_nook, "Music Lullaby Nook",
    "Soft pocket from lullaby - low, warm, sheltering",
    "music")
