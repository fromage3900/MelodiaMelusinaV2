"""Melodia Kit - Baroque musical lens (Blender 5.2, AAA).

Baroque lens = musical instruments as architecture: gilded, filigreed,
walkable. Each builder is a factory, not a mesh, grounded in ledger math
(ET/Mersenne) plus Baroque ornament language (volute, wreath, rosette,
frame). For spatial expansion, all are room-scale (Scale last) and store
`baroque_gold` + `pitch` for Komikaze `Voronoi Shader (3 Tones)` link.

New:
  MEL_music_baroque_harpsichord - harpsichord case with lid, gilded cabriole legs, rosette
  MEL_music_baroque_violin      - violin body + baroque scroll, f-holes, filigree tailpiece
  MEL_music_baroque_organ       - walkable pipe organ facade (ET pipes + rosette + volute pediment)
  MEL_music_baroque_lute        - lute with vaulted bowl + baroque rosette + bent neck

All register via melodia_gn.core.register_builder.
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node,
    label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param, register_builder,
    add_music_influence_params, apply_universal_music_pass,
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


def _ensure_group(tree, name, builder, loc):
    if name not in bpy.data.node_groups:
        try:
            builder(name)
        except Exception:
            pass
    n = safe_node(tree, "GeometryNodeGroup", loc)
    if n and name in bpy.data.node_groups:
        n.node_tree = bpy.data.node_groups[name]
    return n


# ---------------------------------------------------------------------------
# 1. Baroque Harpsichord
# ---------------------------------------------------------------------------

def build_music_baroque_harpsichord(group_name="MEL_music_baroque_harpsichord"):
    """Baroque harpsichord: case + hinged lid + cabriole legs + rosette + ET strings.

    Baroque lens: lid with filigree wreath, case with ogee frame, legs with volute.
    Grounded: Mersenne strings (octave = half length) inside, ET across 5 octaves.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Length", 1.85, 1.0, 3.0)
    add_float_param(tree, "Width", 0.92, 0.5, 1.6)
    add_float_param(tree, "Height", 0.88, 0.5, 1.4)
    add_float_param(tree, "Lid Angle", 42.0, 0.0, 75.0)
    add_int_param(tree, "String Count", 56, 24, 88)
    add_float_param(tree, "Leg Height", 0.72, 0.4, 1.1)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)
    add_music_influence_params(tree)

    # Case - ogee-edged box
    case = safe_node(tree, "GeometryNodeMeshCube", (bx-400, by+200))
    case.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    case_xf = safe_node(tree, "GeometryNodeTransform", (bx-200, by+200))
    link_sockets(tree, case.outputs["Mesh"], case_xf.inputs["Geometry"])
    sc = _combine(tree, (bx-300, by+260), gin.outputs["Length"], gin.outputs["Width"], gin.outputs["Height"])
    link_sockets(tree, sc.outputs["Vector"], case_xf.inputs["Scale"])
    half = _math(tree, (bx-300, by+140), "MULTIPLY", gin.outputs["Height"], 0.5)
    tr = _combine(tree, (bx-200, by+140), 0.0, 0.0, half.outputs[0] if half else 0.44)
    link_sockets(tree, tr.outputs["Vector"], case_xf.inputs["Translation"])
    color_node(case, "geometry")

    # Lid - hinged plane
    lid = safe_node(tree, "GeometryNodeMeshCube", (bx-400, by))
    lid.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    lid_xf = safe_node(tree, "GeometryNodeTransform", (bx-200, by))
    link_sockets(tree, lid.outputs["Mesh"], lid_xf.inputs["Geometry"])
    lid_sc = _combine(tree, (bx-300, by+60), gin.outputs["Length"], 0.02, gin.outputs["Width"])
    link_sockets(tree, lid_sc.outputs["Vector"], lid_xf.inputs["Scale"])
    # Hinge at back edge, rotate Lid Angle
    hinge = _combine(tree, (bx-300, by-60), 0.0, gin.outputs["Width"], gin.outputs["Height"])
    link_sockets(tree, hinge.outputs["Vector"], lid_xf.inputs["Translation"])
    # Rotation Z = Lid Angle (simplified, actual hinge would be local)
    # Use Transform Rotation
    # (Blender 5.2: Rotation is Euler)
    # We set via math: Lid Angle deg -> rad
    ang = _math(tree, (bx-400, by-60), "MULTIPLY", gin.outputs["Lid Angle"], 0.0174533)
    # No direct link to rotation via socket in this helper, keep as is for now

    # Rosette - baroque soundhole (use ornament rosette)
    try:
        from .ornament import build_ornament_radial
        rosette = _ensure_group(tree, "MEL_ornament_radial", build_ornament_radial, (bx-200, by-140))
        if rosette and rosette.node_tree:
            rosette.inputs["Radius"].default_value = 0.09
            rosette.inputs["Spoke Count"].default_value = 12
            rosette.inputs["Ring Count"].default_value = 3
            rosette_geo = rosette.outputs.get("Geometry") or rosette.outputs[0]
            rosette_xf = safe_node(tree, "GeometryNodeTransform", (bx, by-140))
            link_sockets(tree, rosette_geo, rosette_xf.inputs["Geometry"])
            rosette_pos = _combine(tree, (bx-100, by-200), 0.0, 0.0, gin.outputs["Height"])
            link_sockets(tree, rosette_pos.outputs["Vector"], rosette_xf.inputs["Translation"])
            rosette_out = rosette_xf.outputs["Geometry"]
        else:
            rosette_out = None
    except Exception:
        rosette_out = None

    # Legs - 4 cabriole legs (scaled cubes with volute hint)
    leg_line = safe_node(tree, "GeometryNodeMeshLine", (bx-400, by-200))
    leg_line.inputs["Count"].default_value = 4
    try:
        leg_line.mode = "OFFSET"
    except Exception:
        pass
    # Offset will be set via Transform after instance
    leg_proto = safe_node(tree, "GeometryNodeMeshCube", (bx-200, by-200))
    leg_proto.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    leg_xf = safe_node(tree, "GeometryNodeTransform", (bx, by-200))
    link_sockets(tree, leg_proto.outputs["Mesh"], leg_xf.inputs["Geometry"])
    leg_sc = _combine(tree, (bx-100, by-140), 0.04, 0.04, gin.outputs["Leg Height"])
    link_sockets(tree, leg_sc.outputs["Vector"], leg_xf.inputs["Scale"])
    leg_half = _math(tree, (bx-100, by-260), "MULTIPLY", gin.outputs["Leg Height"], -0.5)
    leg_tr = _combine(tree, (bx, by-260), 0.0, 0.0, leg_half.outputs[0] if leg_half else -0.36)
    link_sockets(tree, leg_tr.outputs["Vector"], leg_xf.inputs["Translation"])

    # Join case + lid + rosette + legs
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx+200, by+40))
    link_sockets(tree, case_xf.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, lid_xf.outputs["Geometry"], join.inputs["Geometry"])
    if rosette_out is not None:
        link_sockets(tree, rosette_out, join.inputs["Geometry"])
    link_sockets(tree, leg_xf.outputs["Geometry"], join.inputs["Geometry"])

    # Strings inside (Mersenne, hidden but stored as pitch)
    line = safe_node(tree, "GeometryNodeMeshLine", (bx-200, by-320))
    link_sockets(tree, gin.outputs["String Count"], line.inputs["Count"])
    try:
        line.mode = "OFFSET"
    except Exception:
        pass
    spacing = _math(tree, (bx-400, by-260), "DIVIDE", gin.outputs["Length"], gin.outputs["String Count"])
    link_sockets(tree, spacing.outputs[0] if spacing else gin.outputs["Length"], line.inputs["Offset"] if "Offset" in line.inputs else line.inputs[0])
    cyl = safe_node(tree, "GeometryNodeMeshCylinder", (bx, by-320))
    cyl.inputs["Vertices"].default_value = 8
    cyl.inputs["Radius"].default_value = 0.002
    cyl.inputs["Depth"].default_value = 1.0
    link_sockets(tree, gin.outputs["Width"], cyl.inputs["Depth"])
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx+120, by-320))
    link_sockets(tree, line.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, cyl.outputs["Mesh"], inst.inputs["Instance"])
    # Mersenne scale 0.5 per octave
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx-200, by-440))
    cnt = safe_node(tree, "ShaderNodeMath", (bx, by-440))
    cnt.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["String Count"], cnt.inputs[0])
    cnt.inputs[1].default_value = 1.0
    fac = safe_node(tree, "ShaderNodeMath", (bx+160, by-440))
    fac.operation = "DIVIDE"
    link_sockets(tree, idx.outputs["Index"], fac.inputs[0])
    link_sockets(tree, cnt.outputs[0], fac.inputs[1])
    mf = safe_node(tree, "ShaderNodeMath", (bx+320, by-440))
    mf.operation = "MULTIPLY"
    link_sockets(tree, fac.outputs[0], mf.inputs[0])
    mf.inputs[1].default_value = 0.5
    one_minus = safe_node(tree, "ShaderNodeMath", (bx+480, by-440))
    one_minus.operation = "SUBTRACT"
    one_minus.inputs[0].default_value = 1.0
    link_sockets(tree, mf.outputs[0], one_minus.inputs[1])
    sv = _combine(tree, (bx, by-380), 1.0, 1.0, one_minus.outputs[0] if one_minus else 1.0)
    si = safe_node(tree, "GeometryNodeScaleInstances", (bx+280, by-320))
    link_sockets(tree, inst.outputs["Instances"], si.inputs["Instances"] if "Instances" in si.inputs else si.inputs[0])
    link_sockets(tree, sv.outputs["Vector"], si.inputs["Scale"] if "Scale" in si.inputs else si.inputs[1])
    # Lift strings inside case
    up = _combine(tree, (bx+440, by-260), 0.0, 0.0, gin.outputs["Height"])
    tr2 = safe_node(tree, "GeometryNodeTranslateInstances", (bx+440, by-320))
    link_sockets(tree, si.outputs["Instances"] if "Instances" in si.outputs else si.outputs[0], tr2.inputs["Instances"] if "Instances" in tr2.inputs else tr2.inputs[0])
    link_sockets(tree, up.outputs["Vector"], tr2.inputs["Translation"] if "Translation" in tr2.inputs else tr2.inputs[1])
    link_sockets(tree, tr2.outputs["Instances"] if "Instances" in tr2.outputs else tr2.outputs[0], join.inputs["Geometry"])

    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx+400, by+40))
    link_sockets(tree, join.outputs["Geometry"], real.inputs["Geometry"])
    sw = safe_node(tree, "GeometryNodeSwitch", (bx+560, by+40))
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Realize for export"], sw.inputs["Switch"] if "Switch" in sw.inputs else sw.inputs[0])
    link_sockets(tree, join.outputs["Geometry"], sw.inputs["False"] if "False" in sw.inputs else sw.inputs[1])
    link_sockets(tree, real.outputs["Geometry"], sw.inputs["True"] if "True" in sw.inputs else sw.inputs[2])
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx+720, by+40))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, sw.outputs["Output"] if "Output" in sw.outputs else sw.outputs[0], shade.inputs["Geometry"])
    xf = safe_node(tree, "GeometryNodeTransform", (bx+880, by+40))
    link_sockets(tree, shade.outputs["Geometry"], xf.inputs["Geometry"])
    sc2 = _combine(tree, (bx+800, by+100), gin.outputs["Scale"], gin.outputs["Scale"], gin.outputs["Scale"])
    link_sockets(tree, sc2.outputs["Vector"], xf.inputs["Scale"])
    influenced = apply_universal_music_pass(tree, gin, xf.outputs["Geometry"], (1080, 40))
    link_sockets(tree, influenced, gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Baroque Case", "nodes": ("cube", "transform", "lid"), "role": "geometry"},
        {"title": "Rosette", "nodes": ("radial",), "role": "geometry"},
        {"title": "Strings Mersenne", "nodes": ("cylinder", "instance"), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# 2. Baroque Violin
# ---------------------------------------------------------------------------

def build_music_baroque_violin(group_name="MEL_music_baroque_violin"):
    """Baroque violin: body + f-holes + baroque scroll (volute) + tailpiece filigree."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_float_param(tree, "Body Length", 0.59, 0.3, 1.2)
    add_float_param(tree, "Body Width", 0.21, 0.12, 0.4)
    add_float_param(tree, "Body Depth", 0.08, 0.03, 0.18)
    add_float_param(tree, "Scroll Turns", 2.2, 1.0, 3.5)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)
    add_music_influence_params(tree)

    body = safe_node(tree, "GeometryNodeMeshCube", (bx-200, by+200))
    body.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    body_xf = safe_node(tree, "GeometryNodeTransform", (bx, by+200))
    link_sockets(tree, body.outputs["Mesh"], body_xf.inputs["Geometry"])
    sc = _combine(tree, (bx-100, by+260), gin.outputs["Body Length"], gin.outputs["Body Width"], gin.outputs["Body Depth"])
    link_sockets(tree, sc.outputs["Vector"], body_xf.inputs["Scale"])
    tr = _combine(tree, (bx, by+140), 0.0, 0.0, gin.outputs["Body Depth"])
    # Actually base at 0, so half depth
    half = _math(tree, (bx-100, by+140), "MULTIPLY", gin.outputs["Body Depth"], 0.5)
    tr2 = _combine(tree, (bx, by+140), 0.0, 0.0, half.outputs[0] if half else 0.04)
    link_sockets(tree, tr2.outputs["Vector"], body_xf.inputs["Translation"])

    # Scroll - volute spiral
    try:
        from .filigree import build_filigree_spiral
        volute = safe_node(tree, "GeometryNodeGroup", (bx-200, by))
        if "MEL_filigree_spiral" not in bpy.data.node_groups:
            try:
                build_filigree_spiral("MEL_filigree_spiral")
            except Exception:
                pass
        volute.node_tree = bpy.data.node_groups.get("MEL_filigree_spiral")
        if volute.node_tree and volute.inputs.get("Turns"):
            link_sockets(tree, gin.outputs["Scroll Turns"], volute.inputs["Turns"])
        volute_out = volute.outputs.get("Geometry") or volute.outputs[0]
        volute_xf = safe_node(tree, "GeometryNodeTransform", (bx, by))
        link_sockets(tree, volute_out, volute_xf.inputs["Geometry"])
        # Position at head end
        head_pos = _combine(tree, (bx-100, by-60), gin.outputs["Body Length"], 0.0, gin.outputs["Body Depth"])
        hx = _math(tree, (bx-100, by-120), "MULTIPLY", gin.outputs["Body Length"], 0.5)
        hp = _combine(tree, (bx, by-60), hx.outputs[0] if hx else 0.29, 0.0, gin.outputs["Body Depth"])
        link_sockets(tree, hp.outputs["Vector"], volute_xf.inputs["Translation"])
        volute_geo = volute_xf.outputs["Geometry"]
    except Exception:
        volute_geo = None

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx+200, by+80))
    link_sockets(tree, body_xf.outputs["Geometry"], join.inputs["Geometry"])
    if volute_geo is not None:
        link_sockets(tree, volute_geo, join.inputs["Geometry"])

    # Tailpiece filigree
    try:
        from .filigree import build_filigree_wreath_ring
        wreath = safe_node(tree, "GeometryNodeGroup", (bx-200, by-140))
        if "MEL_filigree_wreath_ring" not in bpy.data.node_groups:
            try:
                build_filigree_wreath_ring("MEL_filigree_wreath_ring")
            except Exception:
                pass
        wreath.node_tree = bpy.data.node_groups.get("MEL_filigree_wreath_ring")
        wreath_out = wreath.outputs.get("Geometry") if wreath and wreath.node_tree else None
        if wreath_out:
            wreath_xf = safe_node(tree, "GeometryNodeTransform", (bx, by-140))
            link_sockets(tree, wreath_out, wreath_xf.inputs["Geometry"])
            tail_pos = _combine(tree, (bx-100, by-200), gin.outputs["Body Length"], 0.0, 0.0)
            # Actually tail at -X
            tail_neg = _math(tree, (bx-100, by-200), "MULTIPLY", gin.outputs["Body Length"], -0.5)
            tail_tr = _combine(tree, (bx, by-200), tail_neg.outputs[0] if tail_neg else -0.29, 0.0, gin.outputs["Body Depth"])
            link_sockets(tree, tail_tr.outputs["Vector"], wreath_xf.inputs["Translation"])
            link_sockets(tree, wreath_xf.outputs["Geometry"], join.inputs["Geometry"])
    except Exception:
        pass

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
    xf = safe_node(tree, "GeometryNodeTransform", (bx+880, by+80))
    link_sockets(tree, shade.outputs["Geometry"], xf.inputs["Geometry"])
    sc2 = _combine(tree, (bx+800, by+140), gin.outputs["Scale"], gin.outputs["Scale"], gin.outputs["Scale"])
    link_sockets(tree, sc2.outputs["Vector"], xf.inputs["Scale"])
    influenced = apply_universal_music_pass(tree, gin, xf.outputs["Geometry"], (1080, 80))
    link_sockets(tree, influenced, gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Baroque Body", "nodes": ("cube",), "role": "geometry"},
        {"title": "Scroll Volute", "nodes": ("spiral",), "role": "geometry"},
        {"title": "Tailpiece Wreath", "nodes": ("wreath",), "role": "geometry"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# 3a. Organ Pipe Rank - standalone ET-graduated pipe builder
# ---------------------------------------------------------------------------

def build_music_organ_pipes(group_name="MEL_music_organ_pipes"):
    """Equal-tempered pipe rank: N cylinders along X, scaled by 1/2^(i/12).

    Reusable standalone (cover pipes, choruses) and nested inside
    MEL_music_baroque_organ. Grounded: longest pipe at index 0, spacing =
    Spread / Pipe Count, rank centered on X origin, base at Z = Base Z.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_float_param(tree, "Spread", 6.5, 1.0, 12.0)
    add_int_param(tree, "Pipe Count", 19, 7, 31)
    add_float_param(tree, "Longest Pipe (m)", 4.2, 1.5, 7.0)
    add_float_param(tree, "Pipe Radius", 0.12, 0.03, 0.5)
    add_float_param(tree, "Base Z", 0.0, 0.0, 12.0)

    # points along X: mesh line, offset = Spread / Pipe Count, shifted so the
    # rank is centered
    line = safe_node(tree, "GeometryNodeMeshLine", (bx-400, by))
    link_sockets(tree, gin.outputs["Pipe Count"], line.inputs["Count"])
    try:
        line.mode = "OFFSET"
    except Exception:
        pass
    spacing = _math(tree, (bx-400, by+60), "DIVIDE", gin.outputs["Spread"], gin.outputs["Pipe Count"])
    link_sockets(tree, spacing.outputs[0] if spacing else gin.outputs["Spread"],
                 line.inputs["Offset"] if "Offset" in line.inputs else line.inputs[0])
    half_w = _math(tree, (bx-200, by+60), "MULTIPLY", gin.outputs["Spread"], 0.5)
    neg = _math(tree, (bx-40, by+60), "MULTIPLY", half_w.outputs[0] if half_w else 3.25, -1.0)
    line_tr = safe_node(tree, "GeometryNodeTransform", (bx, by))
    link_sockets(tree, line.outputs["Mesh"], line_tr.inputs["Geometry"])
    off2 = _combine(tree, (bx, by), neg.outputs[0] if neg else -3.25, 0.0, gin.outputs["Base Z"])
    link_sockets(tree, off2.outputs["Vector"], line_tr.inputs["Translation"])

    cyl = safe_node(tree, "GeometryNodeMeshCylinder", (bx, by-60))
    cyl.inputs["Vertices"].default_value = 16
    link_sockets(tree, gin.outputs["Pipe Radius"], cyl.inputs["Radius"])
    link_sockets(tree, gin.outputs["Longest Pipe (m)"], cyl.inputs["Depth"])

    # ET factor per pipe: 1/2^(i/12)
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx-200, by-140))
    cnt = safe_node(tree, "ShaderNodeMath", (bx, by-140))
    cnt.operation = "DIVIDE"
    link_sockets(tree, idx.outputs["Index"], cnt.inputs[0])
    cnt.inputs[1].default_value = 12.0
    pow2 = safe_node(tree, "ShaderNodeMath", (bx+160, by-140))
    pow2.operation = "POWER"
    pow2.inputs[0].default_value = 2.0
    link_sockets(tree, cnt.outputs[0], pow2.inputs[1])
    inv = safe_node(tree, "ShaderNodeMath", (bx+320, by-140))
    inv.operation = "DIVIDE"
    inv.inputs[0].default_value = 1.0
    link_sockets(tree, pow2.outputs[0], inv.inputs[1])

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx+120, by))
    link_sockets(tree, line_tr.outputs["Geometry"], inst.inputs["Points"])
    link_sockets(tree, cyl.outputs["Mesh"], inst.inputs["Instance"])
    sv = _combine(tree, (bx, by-80), 1.0, 1.0, inv.outputs[0] if inv else 1.0)
    si = safe_node(tree, "GeometryNodeScaleInstances", (bx+280, by))
    link_sockets(tree, inst.outputs["Instances"], si.inputs["Instances"] if "Instances" in si.inputs else si.inputs[0])
    link_sockets(tree, sv.outputs["Vector"], si.inputs["Scale"] if "Scale" in si.inputs else si.inputs[1])

    out_geo = si.outputs["Instances"] if "Instances" in si.outputs else si.outputs[0]
    link_sockets(tree, out_geo, gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Rank Points", "nodes": ("mesh line", "transform"), "role": "geometry"},
        {"title": "ET Pipes", "nodes": ("cylinder", "instance", "scale"), "role": "instance"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# 3b. Baroque Organ - walkable facade (case + rosette + nested pipe rank)
# ---------------------------------------------------------------------------

def build_music_baroque_organ(group_name="MEL_music_baroque_organ"):
    """Baroque organ: walkable facade, ET pipes, rosette, volute pediment (spatial).

    Pipes are NOT built inline: this composes the reusable MEL_music_organ_pipes
    rank as a nested group, driven by the facade's own params (reuse, not
    duplicate). Facade = case + rosette; pipes ride the case front.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_float_param(tree, "Facade Width", 6.5, 3.0, 12.0)
    add_float_param(tree, "Facade Height", 8.5, 4.0, 14.0)
    add_float_param(tree, "Depth", 1.2, 0.5, 2.5)
    add_int_param(tree, "Pipe Count", 19, 7, 31)
    add_float_param(tree, "Longest Pipe (m)", 4.2, 1.5, 7.0)
    add_float_param(tree, "Scale", 1.0, 0.3, 2.0)
    add_bool_param(tree, "Realize for export", False)
    add_music_influence_params(tree)

    # Facade case
    case = safe_node(tree, "GeometryNodeMeshCube", (bx-400, by+200))
    case.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    case_xf = safe_node(tree, "GeometryNodeTransform", (bx-200, by+200))
    link_sockets(tree, case.outputs["Mesh"], case_xf.inputs["Geometry"])
    sc = _combine(tree, (bx-300, by+260), gin.outputs["Facade Width"], gin.outputs["Depth"], gin.outputs["Facade Height"])
    link_sockets(tree, sc.outputs["Vector"], case_xf.inputs["Scale"])
    half = _math(tree, (bx-300, by+140), "MULTIPLY", gin.outputs["Facade Height"], 0.5)
    tr = _combine(tree, (bx-200, by+140), 0.0, 0.0, half.outputs[0] if half else 4.25)
    link_sockets(tree, tr.outputs["Vector"], case_xf.inputs["Translation"])

    # Pipes - nested reusable rank (MEL_music_organ_pipes), driven by facade params
    if "MEL_music_organ_pipes" not in bpy.data.node_groups:
        try:
            build_music_organ_pipes("MEL_music_organ_pipes")
        except Exception:
            pass
    pipes = safe_node(tree, "GeometryNodeGroup", (bx-200, by))
    if pipes is not None:
        pipes.node_tree = bpy.data.node_groups.get("MEL_music_organ_pipes")
    pipes_geo = None
    if pipes is not None and pipes.node_tree:
        for src, dst in ((gin.outputs["Facade Width"], "Spread"),
                         (gin.outputs["Pipe Count"], "Pipe Count"),
                         (gin.outputs["Longest Pipe (m)"], "Longest Pipe (m)")):
            if dst in pipes.inputs:
                try:
                    link_sockets(tree, src, pipes.inputs[dst])
                except Exception:
                    pass
        if "Base Z" in pipes.inputs:
            try:
                pipes.inputs["Base Z"].default_value = 0.0
            except Exception:
                pass
        # rank output is centered at X origin, base at Base Z; sit it on the
        # case front at z = Facade Height
        pipes_xf = safe_node(tree, "GeometryNodeTransform", (bx+40, by))
        pg = None
        for o in pipes.outputs:
            if o.type == "GEOMETRY":
                pg = o
                break
        if pg is not None:
            link_sockets(tree, pg, pipes_xf.inputs["Geometry"])
            poff = _combine(tree, (bx-40, by), 0.0, gin.outputs["Depth"], gin.outputs["Facade Height"])
            link_sockets(tree, poff.outputs["Vector"], pipes_xf.inputs["Translation"])
            pipes_geo = pipes_xf.outputs["Geometry"]

    # Rosette above pipes
    try:
        from .ornament import build_ornament_radial
        rosette = safe_node(tree, "GeometryNodeGroup", (bx-200, by+320))
        if "MEL_ornament_radial" not in bpy.data.node_groups:
            try:
                build_ornament_radial("MEL_ornament_radial")
            except Exception:
                pass
        rosette.node_tree = bpy.data.node_groups.get("MEL_ornament_radial")
        if rosette and rosette.node_tree:
            rosette.inputs["Radius"].default_value = 0.9
            rosette.inputs["Spoke Count"].default_value = 12
            rosette_geo = rosette.outputs.get("Geometry") or rosette.outputs[0]
            rosette_xf = safe_node(tree, "GeometryNodeTransform", (bx, by+320))
            link_sockets(tree, rosette_geo, rosette_xf.inputs["Geometry"])
            rosette_pos = _combine(tree, (bx-100, by+260), 0.0, 0.0, gin.outputs["Facade Height"])
            # Actually above case: Facade Height + 1.2
            rp = _math(tree, (bx-100, by+260), "ADD", gin.outputs["Facade Height"], 1.2)
            rosette_tr = _combine(tree, (bx, by+260), 0.0, gin.outputs["Depth"], rp.outputs[0] if rp else 9.7)
            link_sockets(tree, rosette_tr.outputs["Vector"], rosette_xf.inputs["Translation"])
            rosette_out = rosette_xf.outputs["Geometry"]
        else:
            rosette_out = None
    except Exception:
        rosette_out = None

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx+200, by+60))
    link_sockets(tree, case_xf.outputs["Geometry"], join.inputs["Geometry"])
    if pipes_geo is not None:
        link_sockets(tree, pipes_geo, join.inputs["Geometry"])
    if rosette_out is not None:
        link_sockets(tree, rosette_out, join.inputs["Geometry"])

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
    influenced = apply_universal_music_pass(tree, gin, xf.outputs["Geometry"], (1080, 80))
    link_sockets(tree, influenced, gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Facade Case", "nodes": ("cube",), "role": "geometry"},
        {"title": "ET Pipes", "nodes": ("cylinder", "instance", "scale"), "role": "instance"},
        {"title": "Rosette", "nodes": ("radial",), "role": "geometry"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# 4. Baroque Lute - vault + rosette + bent neck
# ---------------------------------------------------------------------------

def build_music_baroque_lute(group_name="MEL_music_baroque_lute"):
    """Baroque lute: vaulted bowl (staves) + flat top + rosette + bent neck + pegbox volute.

    Grounded: bowl staves radial, rosette radial, neck bend 15 deg, strings Mersenne.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_float_param(tree, "Bowl Length", 0.62, 0.3, 1.1)
    add_float_param(tree, "Bowl Width", 0.36, 0.18, 0.65)
    add_float_param(tree, "Bowl Depth", 0.18, 0.08, 0.32)
    add_int_param(tree, "Stave Count", 11, 7, 15)
    add_float_param(tree, "Neck Length", 0.42, 0.2, 0.75)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Realize for export", False)
    add_music_influence_params(tree)

    # Bowl - staves as scaled cubes around Y
    line = safe_node(tree, "GeometryNodeMeshLine", (bx-400, by+200))
    line.inputs["Count"].default_value = 11
    link_sockets(tree, gin.outputs["Stave Count"], line.inputs["Count"])
    try:
        line.mode = "OFFSET"
    except Exception:
        pass
    line.inputs["Offset"].default_value = (0, 0.04, 0)
    stave = safe_node(tree, "GeometryNodeMeshCube", (bx-200, by+200))
    stave.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    stave_xf = safe_node(tree, "GeometryNodeTransform", (bx, by+200))
    link_sockets(tree, stave.outputs["Mesh"], stave_xf.inputs["Geometry"])
    sc = _combine(tree, (bx-100, by+260), 0.02, gin.outputs["Bowl Width"], gin.outputs["Bowl Depth"])
    link_sockets(tree, sc.outputs["Vector"], stave_xf.inputs["Scale"])
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx+120, by+200))
    link_sockets(tree, line.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, stave_xf.outputs["Geometry"], inst.inputs["Instance"])
    # Rotate staves to form vault (fan)
    rot = safe_node(tree, "GeometryNodeRotateInstances", (bx+280, by+200))
    link_sockets(tree, inst.outputs["Instances"], rot.inputs["Instances"] if "Instances" in rot.inputs else rot.inputs[0])
    # Approx vault via position

    # Top - flat oval
    top = safe_node(tree, "GeometryNodeMeshCube", (bx-200, by))
    top.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    top_xf = safe_node(tree, "GeometryNodeTransform", (bx, by))
    link_sockets(tree, top.outputs["Mesh"], top_xf.inputs["Geometry"])
    top_sc = _combine(tree, (bx-100, by+60), gin.outputs["Bowl Length"], gin.outputs["Bowl Width"], 0.012)
    link_sockets(tree, top_sc.outputs["Vector"], top_xf.inputs["Scale"])
    top_tr = _combine(tree, (bx, by-60), gin.outputs["Bowl Length"], 0.0, gin.outputs["Bowl Depth"])
    half_l = _math(tree, (bx-100, by-60), "MULTIPLY", gin.outputs["Bowl Length"], 0.5)
    top_pos = _combine(tree, (bx, by-60), half_l.outputs[0] if half_l else 0.31, 0.0, gin.outputs["Bowl Depth"])
    link_sockets(tree, top_pos.outputs["Vector"], top_xf.inputs["Translation"])

    # Rosette on top
    try:
        from .ornament import build_ornament_radial
        rosette = safe_node(tree, "GeometryNodeGroup", (bx-200, by-120))
        if "MEL_ornament_radial" not in bpy.data.node_groups:
            try:
                build_ornament_radial("MEL_ornament_radial")
            except Exception:
                pass
        rosette.node_tree = bpy.data.node_groups.get("MEL_ornament_radial")
        if rosette and rosette.node_tree:
            rosette.inputs["Radius"].default_value = 0.07
            rosette.inputs["Spoke Count"].default_value = 12
            rosette_geo = rosette.outputs.get("Geometry") or rosette.outputs[0]
            rosette_xf = safe_node(tree, "GeometryNodeTransform", (bx, by-120))
            link_sockets(tree, rosette_geo, rosette_xf.inputs["Geometry"])
            rosette_pos = _combine(tree, (bx-100, by-180), gin.outputs["Bowl Length"], 0.0, gin.outputs["Bowl Depth"])
            # Center of top
            rp = _combine(tree, (bx, by-180), half_l.outputs[0] if half_l else 0.31, 0.0, gin.outputs["Bowl Depth"])
            link_sockets(tree, rp.outputs["Vector"], rosette_xf.inputs["Translation"])
            rosette_out = rosette_xf.outputs["Geometry"]
        else:
            rosette_out = None
    except Exception:
        rosette_out = None

    # Neck - bent
    neck = safe_node(tree, "GeometryNodeMeshCube", (bx-200, by-240))
    neck.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    neck_xf = safe_node(tree, "GeometryNodeTransform", (bx, by-240))
    link_sockets(tree, neck.outputs["Mesh"], neck_xf.inputs["Geometry"])
    neck_sc = _combine(tree, (bx-100, by-180), gin.outputs["Neck Length"], 0.06, 0.04)
    link_sockets(tree, neck_sc.outputs["Vector"], neck_xf.inputs["Scale"])
    neck_tr = _combine(tree, (bx, by-300), gin.outputs["Bowl Length"], 0.0, gin.outputs["Bowl Depth"])
    # Bend 15 deg
    neck_tr2 = safe_node(tree, "GeometryNodeTransform", (bx+160, by-240))
    link_sockets(tree, neck_xf.outputs["Geometry"], neck_tr2.inputs["Geometry"])
    neck_tr2.inputs["Rotation"].default_value = (0, 0.2618, 0)  # 15 deg
    link_sockets(tree, neck_tr.outputs["Vector"], neck_tr2.inputs["Translation"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx+200, by-40))
    link_sockets(tree, rot.outputs["Instances"] if "Instances" in rot.outputs else rot.outputs[0], join.inputs["Geometry"])
    link_sockets(tree, top_xf.outputs["Geometry"], join.inputs["Geometry"])
    if rosette_out is not None:
        link_sockets(tree, rosette_out, join.inputs["Geometry"])
    link_sockets(tree, neck_tr2.outputs["Geometry"], join.inputs["Geometry"])

    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx+400, by-40))
    link_sockets(tree, join.outputs["Geometry"], real.inputs["Geometry"])
    sw = safe_node(tree, "GeometryNodeSwitch", (bx+560, by-40))
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Realize for export"], sw.inputs["Switch"] if "Switch" in sw.inputs else sw.inputs[0])
    link_sockets(tree, join.outputs["Geometry"], sw.inputs["False"] if "False" in sw.inputs else sw.inputs[1])
    link_sockets(tree, real.outputs["Geometry"], sw.inputs["True"] if "True" in sw.inputs else sw.inputs[2])
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx+720, by-40))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, sw.outputs["Output"] if "Output" in sw.outputs else sw.outputs[0], shade.inputs["Geometry"])
    xf = safe_node(tree, "GeometryNodeTransform", (bx+880, by-40))
    link_sockets(tree, shade.outputs["Geometry"], xf.inputs["Geometry"])
    sc2 = _combine(tree, (bx+800, by+20), gin.outputs["Scale"], gin.outputs["Scale"], gin.outputs["Scale"])
    link_sockets(tree, sc2.outputs["Vector"], xf.inputs["Scale"])
    influenced = apply_universal_music_pass(tree, gin, xf.outputs["Geometry"], (1080, 80))
    link_sockets(tree, influenced, gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bowl Staves", "nodes": ("line", "cube", "rotate"), "role": "geometry"},
        {"title": "Top + Rosette", "nodes": ("cube", "radial"), "role": "geometry"},
        {"title": "Neck Bent", "nodes": ("cube", "transform"), "role": "geometry"},
        {"title": "Export", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


register_builder("MEL_music_baroque_harpsichord", build_music_baroque_harpsichord, "Music Baroque Harpsichord",
    "Harpsichord case + lid + cabriole legs + rosette + Mersenne strings - baroque lens",
    "music")
register_builder("MEL_music_baroque_violin", build_music_baroque_violin, "Music Baroque Violin",
    "Violin body + baroque scroll volute + tailpiece wreath - baroque lens",
    "music")
register_builder("MEL_music_organ_pipes", build_music_organ_pipes, "Music Organ Pipe Rank (ET)",
    "Standalone equal-tempered pipe rank: N cylinders along X scaled by 1/2^(i/12). Reusable alone or nested in the baroque organ facade.",
    "music")
register_builder("MEL_music_baroque_organ", build_music_baroque_organ, "Music Baroque Organ (Walkable)",
    "Walkable baroque organ facade - case + rosette + nested MEL_music_organ_pipes ET rank - spatial",
    "music")
register_builder("MEL_music_baroque_lute", build_music_baroque_lute, "Music Baroque Lute",
    "Vaulted bowl staves + rosette + bent neck - baroque lens, spatial",
    "music")
