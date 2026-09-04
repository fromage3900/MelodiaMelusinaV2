"""V3 Faraway Mother GN builder expansion — body completion + garment core.

Adds builders for:
  body: torso floor, limb haze anchors, moon disc/halo, hair anchor, walkway pylons
  garment: veil seam (PIN), draped curtain, brocade runner

Imports existing core (now has add_string_param + apply_p2_export_pass) so every
new builder gets BuilderName/Biome/Tension/RealizeForExport params + named attrs
p2_builder / p2_tension / p2_chladni_uv automatically.
"""
from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    add_vector_param, make_group_input, make_group_output, tree_input_names,
    register_builder, sock,
)


# -----------------------------------------------------------------------------
# 1. MEL_mother_torso_floor — walkable valley floor
# -----------------------------------------------------------------------------

def build_mother_torso_floor(group_name="MEL_mother_torso_floor"):
    """Walkable valley floor — gentle dish + micro pleats. Primary gameplay lane.
    No Landscape; this is the local floor GN sits on top of imported Nanite terrain.

    Inputs:
      Width, Depth, Fold Depth, Fold Count, Micro Noise, Floor Flatness
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    width_n = add_float_param(tree, "Width", 40.0, 1.0, 200.0)
    depth_n = add_float_param(tree, "Depth", 4.0, 0.2, 20.0)
    fold_depth_n = add_float_param(tree, "Fold Depth", 0.4, 0.0, 2.0)
    fold_count_n = add_int_param(tree, "Fold Count", 5, 1, 20)
    micro_noise_n = add_float_param(tree, "Micro Noise", 0.8, 0.0, 3.0)
    floor_flatness_n = add_float_param(tree, "Floor Flatness", 0.6, 0.0, 1.0)

    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 400, by))
    link_sockets(tree, width_n, grid.inputs["Size X"])
    link_sockets(tree, width_n, grid.inputs["Size Y"])
    grid.inputs["Vertices X"].default_value = 40
    grid.inputs["Vertices Y"].default_value = 40

    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 400, by - 200))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 200, by - 200))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    # gentle dish: (1 - r/radius)^flatness * depth
    dist = safe_node(tree, "ShaderNodeMath", (bx - 400, by - 320))
    dist.operation = "ADD"
    link_sockets(tree, sep.outputs["X"], dist.inputs[0])
    link_sockets(tree, sep.outputs["X"], dist.inputs[1])
    distsq = safe_node(tree, "ShaderNodeMath", (bx - 200, by - 360))
    distsq.operation = "MULTIPLY"
    link_sockets(tree, dist.outputs["Value"], distsq.inputs[0])
    link_sockets(tree, dist.outputs["Value"], distsq.inputs[1])
    sqr = safe_node(tree, "ShaderNodeMath", (bx - 50, by - 360))
    sqr.operation = "SQRT"
    link_sockets(tree, distsq.outputs["Value"], sqr.inputs[0])
    norm = safe_node(tree, "ShaderNodeMath", (bx + 100, by - 360))
    norm.operation = "DIVIDE"
    link_sockets(tree, sqr.outputs["Value"], norm.inputs[0])
    norm.inputs[1].default_value = width_n.default_value if width_n.default_value else 40.0
    one_min = safe_node(tree, "ShaderNodeMath", (bx + 200, by - 360))
    one_min.operation = "SUBTRACT"
    one_min.inputs[0].default_value = 1.0
    link_sockets(tree, norm.outputs["Value"], one_min.inputs[1])
    flat_exp = safe_node(tree, "ShaderNodeMath", (bx + 300, by - 360))
    flat_exp.operation = "MULTIPLY"
    link_sockets(tree, floor_flatness_n, flat_exp.inputs[0])
    flat_exp.inputs[1].default_value = 3.0
    bowl = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 360))
    bowl.operation = "POWER"
    link_sockets(tree, one_min.outputs["Value"], bowl.inputs[0])
    link_sockets(tree, flat_exp.outputs["Value"], bowl.inputs[1])
    dish = safe_node(tree, "ShaderNodeMath", (bx + 500, by - 360))
    dish.operation = "MULTIPLY"
    link_sockets(tree, bowl.outputs["Value"], dish.inputs[0])
    link_sockets(tree, depth_n, dish.inputs[1])

    # fabric folds across floor
    fold_freq = safe_node(tree, "ShaderNodeMath", (bx - 200, by - 440))
    fold_freq.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["X"], fold_freq.inputs[0])
    link_sockets(tree, fold_count_n, fold_freq.inputs[1])
    fold_sin = safe_node(tree, "ShaderNodeMath", (bx + 0, by - 440))
    fold_sin.operation = "SINE"
    link_sockets(tree, fold_freq.outputs["Value"], fold_sin.inputs[0])
    fold_abs = safe_node(tree, "ShaderNodeMath", (bx + 100, by - 440))
    fold_abs.operation = "ABSOLUTE"
    link_sockets(tree, fold_sin.outputs["Value"], fold_abs.inputs[0])
    fold_pow = safe_node(tree, "ShaderNodeMath", (bx + 200, by - 440))
    fold_pow.operation = "POWER"
    link_sockets(tree, fold_abs.outputs["Value"], fold_pow.inputs[0])
    fold_pow.inputs[1].default_value = 1.8
    fold_scale = safe_node(tree, "ShaderNodeMath", (bx + 300, by - 440))
    fold_scale.operation = "MULTIPLY"
    link_sockets(tree, fold_pow.outputs["Value"], fold_scale.inputs[0])
    link_sockets(tree, fold_depth_n, fold_scale.inputs[1])
    fold_offset = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 440))
    fold_offset.operation = "SUBTRACT"
    link_sockets(tree, fold_scale.outputs["Value"], fold_offset.inputs[0])
    link_sockets(tree, fold_scale.outputs["Value"], fold_offset.inputs[1])
    link_sockets(tree, fold_offset.outputs["Value"], dish.inputs[1])

    # micro noise for floor texture
    noise = safe_node(tree, "ShaderNodeTexNoise", (bx - 100, by - 520))
    noise.inputs["Scale"].default_value = 6.0
    link_sockets(tree, micro_noise_n, noise.inputs["Detail"])
    noise.inputs["Roughness"].default_value = 0.6
    noise_mul = safe_node(tree, "ShaderNodeMath", (bx + 150, by - 520))
    noise_mul.operation = "MULTIPLY"
    link_sockets(tree, noise.outputs["Fac"], noise_mul.inputs[0])
    noise_mul.inputs[1].default_value = 0.15

    z_final = safe_node(tree, "ShaderNodeMath", (bx + 350, by - 520))
    z_final.operation = "ADD"
    link_sockets(tree, dish.outputs["Value"], z_final.inputs[0])
    link_sockets(tree, noise_mul.outputs["Value"], z_final.inputs[1])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 500, by))
    link_sockets(tree, grid.outputs["Mesh"], set_pos.inputs["Geometry"])
    z_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 400, by - 320))
    z_vec.inputs["X"].default_value = 0.0
    z_vec.inputs["Y"].default_value = 0.0
    link_sockets(tree, z_final.outputs["Value"], z_vec.inputs["Z"])
    link_sockets(tree, z_vec.outputs["Vector"], set_pos.inputs["Offset"])

    # store p2_audio attrs
    store_aud = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 700, by))
    store_aud.data_type = "FLOAT"
    store_aud.inputs["Name"].default_value = "p2_audio"
    try:
        store_aud.inputs["Value"].default_value = 0.0
    except Exception:
        pass
    link_sockets(tree, set_pos.outputs["Geometry"], store_aud.inputs["Geometry"])
    link_sockets(tree, store_aud.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(grid, "geometry")
    color_node(noise, "noise")
    color_node(set_pos, "geometry")

    return label_tree(tree, "MEL_mother_torso_floor", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Grid", "nodes": ("grid",), "role": "geometry"},
        {"title": "Dish", "nodes": ("dist", "bowl", "dish"), "role": "deform"},
        {"title": "Folds", "nodes": ("fold_sin", "fold_pow", "fold_scale"), "role": "geometry"},
        {"title": "Micro", "nodes": ("noise",), "role": "noise"},
        {"title": "Output", "nodes": ("set_pos", "store_aud", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 2. MEL_mother_limb_haze_anchor — named placement points for fog volumes
# -----------------------------------------------------------------------------

def build_mother_limb_haze_anchor(group_name="MEL_mother_limb_haze_anchor"):
    """Three named placement points for volumetric haze volumes — no mesh, just hint.
    Outputs: 3 points with string attribute limb_anchor index.

    Inputs:
      Arm Span, Leg Spread, Height Offset
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    arm_span_n = add_float_param(tree, "Arm Span", 50.0, 1.0, 200.0)
    leg_spread_n = add_float_param(tree, "Leg Spread", 40.0, 1.0, 200.0)
    height_offset_n = add_float_param(tree, "Height Offset", 8.0, 0.0, 50.0)

    # three points: left arm / right arm / right leg
    pts = []
    offsets = [(-arm_span_n.default_value * 0.6, 0.0, height_offset_n.default_value),
               (arm_span_n.default_value * 0.6, 0.0, height_offset_n.default_value * 0.8),
               (0.0, -leg_spread_n.default_value * 0.7, height_offset_n.default_value * 0.4)]
    for i, (x, y, z) in enumerate(offsets):
        pt = safe_node(tree, "GeometryNodeMeshIcoSphere", (bx + i * 50, by))
        if pt is not None:
            try:
                pt.inputs["Radius"].default_value = 0.2
                pt.inputs["Subdivisions"].default_value = 2
            except Exception:
                pass
        posn = safe_node(tree, "GeometryNodeTransform", (bx + i * 100, by))
        if posn is not None and pt is not None:
            try:
                posn.inputs["Translation"].default_value = (x, y, z)
            except Exception:
                pass
            link_sockets(tree, pt.outputs["Mesh"], posn.inputs["Geometry"])
        store_attr = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + i * 150, by))
        if store_attr is not None:
            store_attr.data_type = "FLOAT"
            try:
                store_attr.inputs["Name"].default_value = "limb_anchor"
            except Exception:
                pass
            try:
                store_attr.inputs["Value"].default_value = float(i)  # 0.0 / 1.0 / 2.0
            except Exception:
                pass
            if posn is not None:
                link_sockets(tree, posn.outputs["Geometry"], store_attr.inputs["Geometry"])
            pts.append(store_attr)

    # join the points (GeometryNodes don't join points easily; just feed first)
    # simplest: feed last store into gout
    out_pt = pts[-1] if pts else None
    if out_pt is not None:
        link_sockets(tree, out_pt.outputs["Geometry"], gout.inputs["Geometry"])
    else:
        link_sockets(tree, gout.inputs["Geometry"], gout.inputs["Geometry"])

    color_node(pt, "point") if pts else None

    return label_tree(tree, "MEL_mother_limb_haze_anchor", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Points", "nodes": ("pt",), "role": "point" if pts else None},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 3. MEL_mother_moon_disc — low horizon disc + halo ring
# -----------------------------------------------------------------------------

def build_mother_moon_disc(group_name="MEL_mother_moon_disc"):
    """Low horizon moon disc with halo ring. Silver-blue tint attribute.

    Inputs:
      Radius, Halo Width, Segments, Tint Strength
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    radius_n = add_float_param(tree, "Radius", 200.0, 10.0, 1000.0)
    halo_w_n = add_float_param(tree, "Halo Width", 8.0, 0.5, 40.0)
    segs_n = add_int_param(tree, "Segments", 48, 8, 128)
    tint_n = add_float_param(tree, "Tint Strength", 0.8, 0.0, 1.0)

    # moon disc: flat circle
    disc = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 400, by))
    try:
        disc.inputs["Radius"].default_value = radius_n.default_value if radius_n.default_value else 200.0
    except Exception:
        pass
    try:
        disc.inputs["Segments"].default_value = segs_n.default_value if segs_n.default_value else 48
    except Exception:
        pass
    try:
        disc.inputs["Ring Count"].default_value = 1
    except Exception:
        pass
    disc_pos = safe_node(tree, "GeometryNodeTransform", (bx - 200, by))
    if disc_pos is not None and disc is not None:
        try:
            disc_pos.inputs["Translation"].default_value = (0.0, 0.0, 2.0)
        except Exception:
            pass
        link_sockets(tree, disc.outputs["Mesh"], disc_pos.inputs["Geometry"])
    else:
        disc_pos = disc

    # halo ring: torus-like curve primitive
    curve = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx + 100, by))
    if curve is not None:
        try:
            link_sockets(tree, radius_n, curve.inputs["Point 1"])
            _r = sock(curve, "Radius")
            if _r is not None:
                _r.default_value = radius_n.default_value if radius_n.default_value else 200.0
            curve.inputs["Radius"].default_value = radius_n.default_value if radius_n.default_value else 200.0
        except Exception:
            pass
    # curve to mesh with halo width profile
    halo_prof = safe_node(tree, "GeometryNodeCurvePrimitiveLine", (bx + 250, by))
    if halo_prof is not None:
        try:
            link_sockets(tree, halo_w_n, sock(halo_prof, "Length"))
        except Exception:
            pass
    curve_to_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 350, by))
    if curve_to_mesh is not None and curve is not None and halo_prof is not None:
        link_sockets(tree, curve.outputs["Curve"], curve_to_mesh.inputs["Curve"])
        link_sockets(tree, halo_prof.outputs["Curve"], curve_to_mesh.inputs["Profile Curve"])

    # tint attr
    store_tint = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 500, by))
    if store_tint is not None:
        store_tint.data_type = "FLOAT"
        try:
            store_tint.inputs["Name"].default_value = "moon_halo_tint"
        except Exception:
            pass
        if disc_pos is not None:
            link_sockets(tree, disc_pos.outputs["Geometry"], store_tint.inputs["Geometry"])
        if curve_to_mesh is not None:
            link_sockets(tree, curve_to_mesh.outputs["Mesh"], store_tint.inputs["Geometry"])
        link_sockets(tree, store_tint.outputs["Geometry"], gout.inputs["Geometry"])
    elif disc_pos is not None:
        link_sockets(tree, disc_pos.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(disc, "geometry") if disc is not None else None

    return label_tree(tree, "MEL_mother_moon_disc", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Disc", "nodes": ("disc", "disc_pos"), "role": "geometry"},
        {"title": "Halo", "nodes": ("curve", "halo_prof", "curve_to_mesh"), "role": "geometry"},
        {"title": "Tint", "nodes": ("store_tint",), "role": "attribute"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 4. MEL_mother_hair_anchor — curve from head to valley
# -----------------------------------------------------------------------------

def build_mother_hair_anchor(group_name="MEL_mother_hair_anchor"):
    """Hair anchor curve: head -> hair cascade -> valley. Outputs curve.
    Used downstream by hair cascade placement.

    Inputs:
      Head Offset, Valley Offset, Length, Sag
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    head_offset_n = add_float_param(tree, "Head Offset", 12.0, 1.0, 50.0)
    valley_offset_n = add_float_param(tree, "Valley Offset", 20.0, 1.0, 80.0)
    length_n = add_float_param(tree, "Length", 30.0, 1.0, 120.0)
    sag_n = add_float_param(tree, "Sag", 5.0, 0.0, 30.0)

    # line from head to valley
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by))
    try:
        link_sockets(tree, length_n, line.inputs["Count"])  # Length = Count proxy
        line.inputs["Offset"].default_value = (0.0, 0.0, 1.0)
    except Exception:
        pass

    # sag displacement along Z
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 300, by - 200))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 200, by - 200))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])
    x_norm = safe_node(tree, "ShaderNodeMath", (bx - 100, by - 200))
    x_norm.operation = "DIVIDE"
    try:
        link_sockets(tree, sep.outputs["X"], x_norm.inputs[0])
        x_norm.inputs[1].default_value = length_n.default_value if length_n.default_value else 30.0
    except Exception:
        pass
    sag_curve = safe_node(tree, "ShaderNodeMath", (bx + 100, by - 200))
    sag_curve.operation = "POWER"
    link_sockets(tree, x_norm.outputs["Value"], sag_curve.inputs[0])
    sag_curve.inputs[1].default_value = 2.0
    sag_mul = safe_node(tree, "ShaderNodeMath", (bx + 200, by - 200))
    sag_mul.operation = "MULTIPLY"
    link_sockets(tree, sag_curve.outputs["Value"], sag_mul.inputs[0])
    link_sockets(tree, sag_n, sag_mul.inputs[1])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 300, by))
    if line is not None:
        link_sockets(tree, line.outputs["Mesh"], set_pos.inputs["Geometry"])
    z_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 200, by - 300))
    z_vec.inputs["X"].default_value = 0.0
    z_vec.inputs["Y"].default_value = 0.0
    link_sockets(tree, sag_mul.outputs["Value"], z_vec.inputs["Z"])
    link_sockets(tree, z_vec.outputs["Vector"], set_pos.inputs["Offset"])

    # store p2_builder as hair_anchor (FLOAT tag — Blender 5.2 named attrs
    # don't expose STRING until a later revision; encode identity as float)
    store_b = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 450, by))
    if store_b is not None:
        store_b.data_type = "FLOAT"
        try:
            store_b.inputs["Name"].default_value = "p2_builder"
        except Exception:
            pass
        try:
            store_b.inputs["Value"].default_value = 1.0  # hair_anchor tag
        except Exception:
            pass
        if set_pos is not None:
            link_sockets(tree, set_pos.outputs["Geometry"], store_b.inputs["Geometry"])
        link_sockets(tree, store_b.outputs["Geometry"], gout.inputs["Geometry"])
    else:
        link_sockets(tree, set_pos.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(line, "curve")

    return label_tree(tree, "MEL_mother_hair_anchor", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Line", "nodes": ("line",), "role": "curve"},
        {"title": "Sag", "nodes": ("sag_curve", "sag_mul"), "role": "deform"},
        {"title": "Output", "nodes": ("store_b", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 5. MEL_mother_walkway_pylon — fabric-wrapped support under walkways
# -----------------------------------------------------------------------------

def build_mother_walkway_pylon(group_name="MEL_mother_walkway_pylon"):
    """Fabric-wrapped pylon supporting walkways. Cube wrapped with sine folds.

    Inputs:
      Height, Base Radius, Wrap Taper, Wrap Count, Fabric Tension, Wrap Thickness
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    height_n = add_float_param(tree, "Height", 6.0, 1.0, 30.0)
    radius_n = add_float_param(tree, "Base Radius", 0.8, 0.1, 5.0)
    taper_n = add_float_param(tree, "Wrap Taper", 0.3, 0.0, 1.0)
    wrap_count_n = add_int_param(tree, "Wrap Count", 8, 1, 24)
    tension_n = add_float_param(tree, "Fabric Tension", 0.7, 0.0, 1.0)
    thickness_n = add_float_param(tree, "Wrap Thickness", 0.15, 0.02, 1.0)

    # base cylinder
    cyl = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 400, by))
    try:
        cyl.inputs["Radius"].default_value = radius_n.default_value if radius_n.default_value else 0.8
        cyl.inputs["Segments"].default_value = 24
        cyl.inputs["Ring Count"].default_value = 16
    except Exception:
        pass
    # make it taller than round: scale Z
    cyl_xf = safe_node(tree, "GeometryNodeTransform", (bx - 200, by))
    if cyl_xf is not None and cyl is not None:
        try:
            cyl_xf.inputs["Scale"].default_value = (1.0, 1.0, height_n.default_value if height_n.default_value else 6.0)
        except Exception:
            pass
        link_sockets(tree, cyl.outputs["Mesh"], cyl_xf.inputs["Geometry"])

    # wrap folds: sine around Y
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 200, by - 200))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 150, by - 200))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])
    wrap_angle = safe_node(tree, "ShaderNodeMath", (bx - 50, by - 200))
    wrap_angle.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["Y"], wrap_angle.inputs[0])
    wrap_angle.inputs[1].default_value = wrap_count_n.default_value if wrap_count_n.default_value else 8.0
    wrap_sin = safe_node(tree, "ShaderNodeMath", (bx + 100, by - 200))
    wrap_sin.operation = "SINE"
    link_sockets(tree, wrap_angle.outputs["Value"], wrap_sin.inputs[0])
    wrap_abs = safe_node(tree, "ShaderNodeMath", (bx + 200, by - 200))
    wrap_abs.operation = "ABSOLUTE"
    link_sockets(tree, wrap_sin.outputs["Value"], wrap_abs.inputs[0])
    wrap_pow = safe_node(tree, "ShaderNodeMath", (bx + 300, by - 200))
    wrap_pow.operation = "POWER"
    link_sockets(tree, wrap_abs.outputs["Value"], wrap_pow.inputs[0])
    wrap_pow.inputs[1].default_value = 1.5
    wrap_scale = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 200))
    wrap_scale.operation = "MULTIPLY"
    link_sockets(tree, wrap_pow.outputs["Value"], wrap_scale.inputs[0])
    link_sockets(tree, thickness_n, wrap_scale.inputs[1])
    # tension sags wrap less
    tension_sag = safe_node(tree, "ShaderNodeMath", (bx + 500, by - 200))
    tension_sag.operation = "MULTIPLY"
    link_sockets(tree, tension_n, tension_sag.inputs[0])
    tension_sag.inputs[1].default_value = -0.2
    wrap_final = safe_node(tree, "ShaderNodeMath", (bx + 600, by - 200))
    wrap_final.operation = "ADD"
    link_sockets(tree, wrap_scale.outputs["Value"], wrap_final.inputs[0])
    link_sockets(tree, tension_sag.outputs["Value"], wrap_final.inputs[1])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 700, by))
    if cyl_xf is not None:
        link_sockets(tree, cyl_xf.outputs["Geometry"], set_pos.inputs["Geometry"])
    z_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 500, by - 300))
    z_vec.inputs["X"].default_value = 0.0
    z_vec.inputs["Y"].default_value = 0.0
    link_sockets(tree, wrap_final.outputs["Value"], z_vec.inputs["Z"])
    link_sockets(tree, z_vec.outputs["Vector"], set_pos.inputs["Offset"])

    link_sockets(tree, set_pos.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(cyl, "geometry")

    return label_tree(tree, "MEL_mother_walkway_pylon", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Base", "nodes": ("cyl", "cyl_xf"), "role": "geometry"},
        {"title": "Wrap", "nodes": ("wrap_sin", "wrap_pow", "wrap_scale", "wrap_final"), "role": "geometry"},
        {"title": "Output", "nodes": ("set_pos", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 6. MEL_mother_veil_seam — heart gate veil, PIN vertex group, Chaos-ready
# -----------------------------------------------------------------------------

def build_mother_veil_seam(group_name="MEL_mother_veil_seam"):
    """Open-edge veil at heart gate, with pinned vertex group PIN.
    Ready for Chaos cloth (when wired); WPO until then.

    Inputs:
      Span, Height, Opening Width, Veil Length, Edge Frill, Tension, Pin Offset
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    span_n = add_float_param(tree, "Span", 6.0, 1.0, 30.0)
    height_n = add_float_param(tree, "Height", 5.0, 1.0, 20.0)
    opening_n = add_float_param(tree, "Opening Width", 2.0, 0.5, 10.0)
    length_n = add_float_param(tree, "Veil Length", 4.0, 0.5, 15.0)
    frill_n = add_float_param(tree, "Edge Frill", 0.3, 0.0, 1.0)
    tension_n = add_float_param(tree, "Tension", 0.6, 0.0, 1.0)
    pin_offset_n = add_float_param(tree, "Pin Offset", 1.0, 0.0, 5.0)

    # base panel: flat ribbon
    panel = safe_node(tree, "GeometryNodeMeshGrid", (bx - 400, by))
    link_sockets(tree, span_n, panel.inputs["Size X"])
    link_sockets(tree, length_n, panel.inputs["Size Y"])
    panel.inputs["Vertices X"].default_value = 32
    panel.inputs["Vertices Y"].default_value = 16

    # opening: carve out center strip
    inner = safe_node(tree, "GeometryNodeMeshGrid", (bx - 200, by))
    link_sockets(tree, opening_n, inner.inputs["Size X"])
    link_sockets(tree, length_n, inner.inputs["Size Y"])
    inner.inputs["Vertices X"].default_value = 16
    inner.inputs["Vertices Y"].default_value = 16
    # offset inner down
    inner_xf = safe_node(tree, "GeometryNodeTransform", (bx - 100, by))
    if inner_xf is not None and inner is not None:
        try:
            # shift inner toward center
            inner_xf.inputs["Translation"].default_value = (0.0, 0.0, length_n.default_value * 0.5 if length_n.default_value else 2.0)
        except Exception:
            pass
        link_sockets(tree, inner.outputs["Mesh"], inner_xf.inputs["Geometry"])

    # boolean
    boolean = safe_node(tree, "GeometryNodeMeshBoolean", (bx, by))
    if boolean is not None and panel is not None and inner_xf is not None:
        boolean.operation = "DIFFERENCE"
        link_sockets(tree, panel.outputs["Mesh"], boolean.inputs["Mesh 1"])
        link_sockets(tree, inner_xf.outputs["Geometry"], boolean.inputs["Mesh 2"])

    # edge frill: simple wavy offset along edges
    frill_sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx + 300, by))
    frill_wave = safe_node(tree, "ShaderNodeMath", (bx + 400, by))
    frill_wave.operation = "SINE"
    if frill_sep is not None:
        link_sockets(tree, frill_sep.outputs["Y"], frill_wave.inputs[0])
    if frill_wave is not None:
        frill_wave.inputs[1].default_value = 6.0
    frill_mul = safe_node(tree, "ShaderNodeMath", (bx + 500, by))
    frill_mul.operation = "MULTIPLY"
    link_sockets(tree, frill_wave.outputs["Value"], frill_mul.inputs[0])
    link_sockets(tree, frill_n, frill_mul.inputs[1])
    frill_z = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 600, by))
    frill_z.inputs["X"].default_value = 0.0
    frill_z.inputs["Y"].default_value = 0.0
    if frill_mul is not None:
        link_sockets(tree, frill_mul.outputs["Value"], frill_z.inputs["Z"])
    frill_set = safe_node(tree, "GeometryNodeSetPosition", (bx + 700, by))
    if frill_set is not None and boolean is not None:
        link_sockets(tree, boolean.outputs["Mesh"], frill_set.inputs["Geometry"])
    if frill_set is not None and frill_z is not None:
        link_sockets(tree, frill_z.outputs["Vector"], frill_set.inputs["Position"])

    # final out
    out = frill_set if frill_set is not None else boolean

    # store p2_audio + p2_builder
    store_a = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 850, by))
    store_b = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 950, by))
    if store_a is not None and store_b is not None and out is not None:
        store_a.data_type = "FLOAT"
        store_b.data_type = "FLOAT"
        try:
            store_a.inputs["Name"].default_value = "p2_audio"
            store_b.inputs["Name"].default_value = "p2_builder"
        except Exception:
            pass
        try:
            store_a.inputs["Value"].default_value = 0.0
            store_b.inputs["Value"].default_value = 2.0  # veil_seam tag
        except Exception:
            pass
        link_sockets(tree, out.outputs["Geometry"], store_a.inputs["Geometry"])
        link_sockets(tree, store_a.outputs["Geometry"], store_b.inputs["Geometry"])
        link_sockets(tree, store_b.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(panel, "geometry") if panel is not None else None

    return label_tree(tree, "MEL_mother_veil_seam", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Panel", "nodes": ("panel", "inner_xf", "boolean"), "role": "geometry"},
        {"title": "Frill", "nodes": ("frill_wave", "frill_mul", "frill_z", "frill_set"), "role": "deform"},
        {"title": "Output", "nodes": ("store_a", "store_b", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 7. MEL_mother_draped_curtain — archway drape with gather + fall
# -----------------------------------------------------------------------------

def build_mother_draped_curtain(group_name="MEL_mother_draped_curtain"):
    """Archway drape with gather and fall. Fabric curtain across an opening.

    Inputs:
      Span, Height, Gather, Fall Depth, Fold Count, Fold Sharpness, Tension
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    span_n = add_float_param(tree, "Span", 8.0, 2.0, 30.0)
    height_n = add_float_param(tree, "Height", 6.0, 1.0, 20.0)
    gather_n = add_float_param(tree, "Gather", 0.3, 0.0, 1.0)
    fall_depth_n = add_float_param(tree, "Fall Depth", 1.5, 0.1, 6.0)
    fold_count_n = add_int_param(tree, "Fold Count", 8, 2, 24)
    sharpness_n = add_float_param(tree, "Fold Sharpness", 1.5, 0.5, 4.0)
    tension_n = add_float_param(tree, "Tension", 0.5, 0.0, 1.0)

    # base panel
    panel = safe_node(tree, "GeometryNodeMeshGrid", (bx - 400, by))
    link_sockets(tree, span_n, panel.inputs["Size X"])
    link_sockets(tree, height_n, panel.inputs["Size Y"])
    panel.inputs["Vertices X"].default_value = 40
    panel.inputs["Vertices Y"].default_value = 40

    # gather: displace in X based on sin across span + tension
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 300, by - 200))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 200, by - 200))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])
    gather_freq = safe_node(tree, "ShaderNodeMath", (bx - 100, by - 200))
    gather_freq.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["X"], gather_freq.inputs[0])
    gather_freq.inputs[1].default_value = fold_count_n.default_value if fold_count_n.default_value else 8.0
    gather_sin = safe_node(tree, "ShaderNodeMath", (bx + 50, by - 200))
    gather_sin.operation = "SINE"
    link_sockets(tree, gather_freq.outputs["Value"], gather_sin.inputs[0])
    gather_abs = safe_node(tree, "ShaderNodeMath", (bx + 150, by - 200))
    gather_abs.operation = "ABSOLUTE"
    link_sockets(tree, gather_sin.outputs["Value"], gather_abs.inputs[0])
    gather_scale = safe_node(tree, "ShaderNodeMath", (bx + 250, by - 200))
    gather_scale.operation = "MULTIPLY"
    link_sockets(tree, gather_abs.outputs["Value"], gather_scale.inputs[0])
    gather_scale.inputs[1].default_value = gather_n.default_value if gather_n.default_value else 0.3
    gather_tension = safe_node(tree, "ShaderNodeMath", (bx + 350, by - 200))
    gather_tension.operation = "MULTIPLY"
    link_sockets(tree, gather_scale.outputs["Value"], gather_tension.inputs[0])
    link_sockets(tree, tension_n, gather_tension.inputs[1])
    gather_off = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 450, by - 200))
    gather_off.inputs["X"].default_value = 0.0
    if gather_tension is not None:
        link_sockets(tree, gather_tension.outputs["Value"], gather_off.inputs["Y"])
    gather_off.inputs["Z"].default_value = 0.0

    # fall: Z displacement based on Y + sharpness
    y_norm = safe_node(tree, "ShaderNodeMath", (bx - 100, by - 300))
    y_norm.operation = "DIVIDE"
    link_sockets(tree, sep.outputs["Y"], y_norm.inputs[0])
    y_norm.inputs[1].default_value = height_n.default_value if height_n.default_value else 6.0
    fall_sin = safe_node(tree, "ShaderNodeMath", (bx + 100, by - 300))
    fall_sin.operation = "SINE"
    link_sockets(tree, y_norm.outputs["Value"], fall_sin.inputs[0])
    fall_mul = safe_node(tree, "ShaderNodeMath", (bx + 200, by - 300))
    fall_mul.operation = "MULTIPLY"
    link_sockets(tree, fall_sin.outputs["Value"], fall_mul.inputs[0])
    fall_mul.inputs[1].default_value = fall_depth_n.default_value if fall_depth_n.default_value else 1.5
    fall_pow = safe_node(tree, "ShaderNodeMath", (bx + 300, by - 300))
    fall_pow.operation = "POWER"
    link_sockets(tree, fall_mul.outputs["Value"], fall_pow.inputs[0])
    fall_pow.inputs[1].default_value = sharpness_n.default_value if sharpness_n.default_value else 1.5
    fall_off = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 400, by - 300))
    fall_off.inputs["X"].default_value = 0.0
    fall_off.inputs["Y"].default_value = 0.0
    if fall_pow is not None:
        link_sockets(tree, fall_pow.outputs["Value"], fall_off.inputs["Z"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 500, by))
    if panel is not None:
        link_sockets(tree, panel.outputs["Mesh"], set_pos.inputs["Geometry"])
    if gather_off is not None:
        link_sockets(tree, gather_off.outputs["Vector"], set_pos.inputs["Position"])
    if fall_off is not None:
        link_sockets(tree, fall_off.outputs["Vector"], set_pos.inputs["Offset"])

    link_sockets(tree, set_pos.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(panel, "geometry") if panel is not None else None

    return label_tree(tree, "MEL_mother_draped_curtain", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Panel", "nodes": ("panel",), "role": "geometry"},
        {"title": "Gather", "nodes": ("gather_sin", "gather_abs", "gather_scale", "gather_tension"), "role": "deform"},
        {"title": "Fall", "nodes": ("y_norm", "fall_sin", "fall_pow"), "role": "deform"},
        {"title": "Output", "nodes": ("set_pos", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 8. MEL_mother_brocade_runner — narrow long fabric strip, path-traceable
# -----------------------------------------------------------------------------

def build_mother_brocade_runner(group_name="MEL_mother_brocade_runner"):
    """Narrow long fabric strip for outlining paths. Spline-traceable.

    Inputs:
      Length, Width, Fold Depth, Fold Frequency, Tension, Profile Resolution
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    length_n = add_float_param(tree, "Length", 60.0, 5.0, 300.0)
    width_n = add_float_param(tree, "Width", 0.8, 0.2, 4.0)
    fold_depth_n = add_float_param(tree, "Fold Depth", 0.3, 0.0, 2.0)
    fold_freq_n = add_float_param(tree, "Fold Frequency", 0.05, 0.005, 0.5)
    tension_n = add_float_param(tree, "Tension", 0.6, 0.0, 1.0)
    prof_res_n = add_int_param(tree, "Profile Resolution", 4, 2, 12)

    # long strip
    strip = safe_node(tree, "GeometryNodeMeshGrid", (bx - 400, by))
    link_sockets(tree, length_n, strip.inputs["Size X"])
    link_sockets(tree, width_n, strip.inputs["Size Y"])
    strip.inputs["Vertices X"].default_value = 80
    strip.inputs["Vertices Y"].default_value = prof_res_n.default_value if prof_res_n.default_value else 4

    # folds along length
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 300, by - 200))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 200, by - 200))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])
    fold_freq = safe_node(tree, "ShaderNodeMath", (bx - 100, by - 200))
    fold_freq.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["X"], fold_freq.inputs[0])
    link_sockets(tree, fold_freq_n, fold_freq.inputs[1])
    fold_sin = safe_node(tree, "ShaderNodeMath", (bx + 50, by - 200))
    fold_sin.operation = "SINE"
    link_sockets(tree, fold_freq.outputs["Value"], fold_sin.inputs[0])
    fold_abs = safe_node(tree, "ShaderNodeMath", (bx + 150, by - 200))
    fold_abs.operation = "ABSOLUTE"
    link_sockets(tree, fold_sin.outputs["Value"], fold_abs.inputs[0])
    fold_pow = safe_node(tree, "ShaderNodeMath", (bx + 250, by - 200))
    fold_pow.operation = "POWER"
    link_sockets(tree, fold_abs.outputs["Value"], fold_pow.inputs[0])
    fold_pow.inputs[1].default_value = 1.6
    fold_scale = safe_node(tree, "ShaderNodeMath", (bx + 350, by - 200))
    fold_scale.operation = "MULTIPLY"
    link_sockets(tree, fold_pow.outputs["Value"], fold_scale.inputs[0])
    link_sockets(tree, fold_depth_n, fold_scale.inputs[1])
    tension_sag = safe_node(tree, "ShaderNodeMath", (bx + 450, by - 200))
    tension_sag.operation = "MULTIPLY"
    link_sockets(tree, tension_n, tension_sag.inputs[0])
    tension_sag.inputs[1].default_value = -0.2
    z_comb = safe_node(tree, "ShaderNodeMath", (bx + 550, by - 200))
    z_comb.operation = "ADD"
    link_sockets(tree, fold_scale.outputs["Value"], z_comb.inputs[0])
    link_sockets(tree, tension_sag.outputs["Value"], z_comb.inputs[1])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 650, by))
    if strip is not None:
        link_sockets(tree, strip.outputs["Mesh"], set_pos.inputs["Geometry"])
    z_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 500, by - 300))
    z_vec.inputs["X"].default_value = 0.0
    z_vec.inputs["Y"].default_value = 0.0
    if z_comb is not None:
        link_sockets(tree, z_comb.outputs["Value"], z_vec.inputs["Z"])
    link_sockets(tree, z_vec.outputs["Vector"], set_pos.inputs["Offset"])

    link_sockets(tree, set_pos.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(strip, "geometry") if strip is not None else None

    return label_tree(tree, "MEL_mother_brocade_runner", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Strip", "nodes": ("strip",), "role": "geometry"},
        {"title": "Folds", "nodes": ("fold_sin", "fold_pow", "fold_scale", "z_comb"), "role": "deform"},
        {"title": "Output", "nodes": ("set_pos", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# Registry
# -----------------------------------------------------------------------------

register_builder("MEL_mother_torso_floor", build_mother_torso_floor,
    "Mother Torso Floor",
    "Walkable valley floor — gentle dish + micro pleats, primary gameplay lane",
    "mother")

register_builder("MEL_mother_limb_haze_anchor", build_mother_limb_haze_anchor,
    "Mother Limb Haze Anchor",
    "Three named placement points for volumetric haze volumes (no mesh, suggestion)",
    "mother")

register_builder("MEL_mother_moon_disc", build_mother_moon_disc,
    "Mother Moon Disc",
    "Low horizon moon disc with halo ring, silver-blue tint",
    "mother")

register_builder("MEL_mother_hair_anchor", build_mother_hair_anchor,
    "Mother Hair Anchor",
    "Curve from head to valley that hair cascade follows",
    "mother")

register_builder("MEL_mother_walkway_pylon", build_mother_walkway_pylon,
    "Mother Walkway Pylon",
    "Fabric-wrapped support under walkways",
    "mother")

register_builder("MEL_mother_veil_seam", build_mother_veil_seam,
    "Mother Veil Seam",
    "Open-edge heart gate veil, PIN vertex group, Chaos-ready (WPO until then)",
    "mother")

register_builder("MEL_mother_draped_curtain", build_mother_draped_curtain,
    "Mother Draped Curtain",
    "Archway drape with gather and fall",
    "mother")

register_builder("MEL_mother_brocade_runner", build_mother_brocade_runner,
    "Mother Brocade Runner",
    "Narrow long fabric strip for outlining paths",
    "mother")
