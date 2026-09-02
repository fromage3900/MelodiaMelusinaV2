"""The God That Molts GN builders — 8 builders for the molting arthropod Monolith.

Aquatic arthropod aesthetic: trilobite body plan (cephalon/thorax/pygidium),
translucent chitin, cathedral interiors, bioluminescent veins, breathing pulse.

Builders:
  MEL_shell_cephalon       — trilobite head shell
  MEL_shell_thorax         — segmented thorax arches (cathedral)
  MEL_shell_pygidium       — tail fan shell with biolum
  MEL_shell_interior       — walkable hollow shell interior
  MEL_fracture_seam        — crack lines breaking open
  MEL_biolum_vein          — glowing bioluminescent veins
  MEL_gravity_well         — spacetime distortion volume
  MEL_aftermath_fragment   — scattered old molt fragments
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    add_vector_param, make_group_input, make_group_output, tree_input_names,
    register_builder,
)


# -----------------------------------------------------------------------------
# 1. MEL_shell_cephalon — trilobite head shell
# -----------------------------------------------------------------------------

def build_shell_cephalon(group_name="MEL_shell_cephalon"):
    """Trilobite head shell — the cephalon with segmented lobes.

    Inputs:
      Scale, Segment Count, Lobe Depth, Chitin Opacity, Vein Glow, Breathing Speed
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    scale_n = add_float_param(tree, "Scale", 1.0, 0.01, 100.0)
    seg_n = add_int_param(tree, "Segment Count", 5, 1, 16)
    lobe_n = add_float_param(tree, "Lobe Depth", 0.3, 0.0, 2.0)
    opacity_n = add_float_param(tree, "Chitin Opacity", 0.8, 0.0, 1.0)
    glow_n = add_float_param(tree, "Vein Glow", 1.5, 0.0, 5.0)
    breath_n = add_float_param(tree, "Breathing Speed", 1.0, 0.0, 5.0)

    # Base shape: flattened sphere (cephalon)
    sphere = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 400, by))
    sphere.inputs["Rings"].default_value = 16
    sphere.inputs["Segments"].default_value = 24

    # Flatten to cephalon shape
    flatten = safe_node(tree, "GeometryNodeTransform", (bx - 200, by))
    link_sockets(tree, sphere.outputs["Mesh"], flatten.inputs["Geometry"])
    flatten.inputs["Scale"].default_value = (1.0, 0.6, 0.4)

    # Segment lines: displace along X
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 200, by - 200))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx, by - 200))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    seg_freq = safe_node(tree, "ShaderNodeMath", (bx + 200, by - 200))
    seg_freq.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["X"], seg_freq.inputs[0])
    link_sockets(tree, seg_n, seg_freq.inputs[1])

    seg_sin = safe_node(tree, "ShaderNodeMath", (bx + 300, by - 200))
    seg_sin.operation = "SINE"
    link_sockets(tree, seg_freq.outputs["Value"], seg_sin.inputs[0])

    lobe_mul = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 200))
    lobe_mul.operation = "MULTIPLY"
    link_sockets(tree, seg_sin.outputs["Value"], lobe_mul.inputs[0])
    link_sockets(tree, lobe_n, lobe_mul.inputs[1])

    # Breathing pulse
    breath = safe_node(tree, "ShaderNodeTexNoise", (bx + 200, by - 350))
    breath.inputs["Scale"].default_value = 0.5
    link_sockets(tree, breath_n, breath.inputs["Detail"])

    breath_mul = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 350))
    breath_mul.operation = "MULTIPLY"
    link_sockets(tree, breath.outputs["Fac"], breath_mul.inputs[0])
    breath_mul.inputs[1].default_value = 0.05

    # Combine lobe + breathing
    combined = safe_node(tree, "ShaderNodeMath", (bx + 500, by - 200))
    combined.operation = "ADD"
    link_sockets(tree, lobe_mul.outputs["Value"], combined.inputs[0])
    link_sockets(tree, breath_mul.outputs["Value"], combined.inputs[1])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 600, by))
    link_sockets(tree, flatten.outputs["Geometry"], set_pos.inputs["Geometry"])
    z_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 400, by - 100))
    z_vec.inputs["X"].default_value = 0.0
    z_vec.inputs["Y"].default_value = 0.0
    link_sockets(tree, combined.outputs["Value"], z_vec.inputs["Z"])
    link_sockets(tree, z_vec.outputs["Vector"], set_pos.inputs["Offset"])

    # Store attributes
    store_opacity = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 800, by))
    store_opacity.data_type = "FLOAT"
    store_opacity.inputs["Name"].default_value = "chitin_opacity"
    link_sockets(tree, opacity_n, store_opacity.inputs["Value"])
    link_sockets(tree, set_pos.outputs["Geometry"], store_opacity.inputs["Geometry"])

    store_glow = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 1000, by))
    store_glow.data_type = "FLOAT"
    store_glow.inputs["Name"].default_value = "vein_glow"
    link_sockets(tree, glow_n, store_glow.inputs["Value"])
    link_sockets(tree, store_opacity.outputs["Geometry"], store_glow.inputs["Geometry"])

    link_sockets(tree, store_glow.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(sphere, "geometry")
    color_node(breath, "noise")
    color_node(set_pos, "geometry")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Cephalon", "nodes": ("sphere", "flatten"), "role": "geometry"},
        {"title": "Segments", "nodes": ("seg_sin", "breath", "set_pos"), "role": "geometry"},
        {"title": "Output", "nodes": ("store_opacity", "store_glow", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 2. MEL_shell_thorax — segmented thorax arches (cathedral)
# -----------------------------------------------------------------------------

def build_shell_thorax(group_name="MEL_shell_thorax"):
    """Segmented thorax arches — the cathedral ribbed interior.

    Inputs:
      Segment Count, Arch Height, Rib Spacing, Breathing Speed, Chitin Thickness
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    seg_n = add_int_param(tree, "Segment Count", 8, 1, 32)
    arch_n = add_float_param(tree, "Arch Height", 3.0, 0.1, 20.0)
    rib_n = add_float_param(tree, "Rib Spacing", 0.5, 0.01, 5.0)
    breath_n = add_float_param(tree, "Breathing Speed", 1.0, 0.0, 5.0)
    thick_n = add_float_param(tree, "Chitin Thickness", 0.2, 0.01, 2.0)

    # Base arch: curved line
    arch_curve = safe_node(tree, "GeometryNodeCurvePrimitiveBezierArc", (bx - 400, by))
    arch_curve.inputs["Resolution"].default_value = 16
    arch_curve.inputs["Radius"].default_value = 2.0
    arch_curve.inputs["Start Angle"].default_value = 0.0
    arch_curve.inputs["Sweep Angle"].default_value = math.pi

    # Instance arches along X (segments)
    arch_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by - 200))
    link_sockets(tree, seg_n, arch_line.inputs["Count"])
    arch_line.inputs["Offset"].default_value = (1.0, 0.0, 0.0)

    arch_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 200, by))
    link_sockets(tree, arch_line.outputs["Mesh"], arch_inst.inputs["Points"])
    link_sockets(tree, arch_curve.outputs["Curve"], arch_inst.inputs["Instance"])

    # Scale arches by arch height
    arch_scale = safe_node(tree, "GeometryNodeScaleInstances", (bx, by))
    link_sockets(tree, arch_inst.outputs["Instances"], arch_scale.inputs["Instances"])
    link_sockets(tree, arch_n, arch_scale.inputs["Scale"])

    # Realize
    arch_real = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 200, by))
    link_sockets(tree, arch_scale.outputs["Instances"], arch_real.inputs["Geometry"])

    # Breathing pulse
    breath = safe_node(tree, "ShaderNodeTexNoise", (bx + 200, by - 200))
    breath.inputs["Scale"].default_value = 0.3
    link_sockets(tree, breath_n, breath.inputs["Detail"])

    breath_mul = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 200))
    breath_mul.operation = "MULTIPLY"
    link_sockets(tree, breath.outputs["Fac"], breath_mul.inputs[0])
    breath_mul.inputs[1].default_value = 0.1

    # Displace for breathing
    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 400, by))
    link_sockets(tree, arch_real.outputs["Geometry"], set_pos.inputs["Geometry"])
    z_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 200, by - 300))
    z_vec.inputs["X"].default_value = 0.0
    z_vec.inputs["Y"].default_value = 0.0
    link_sockets(tree, breath_mul.outputs["Value"], z_vec.inputs["Z"])
    link_sockets(tree, z_vec.outputs["Vector"], set_pos.inputs["Offset"])

    # Store attributes
    store_thick = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 600, by))
    store_thick.data_type = "FLOAT"
    store_thick.inputs["Name"].default_value = "chitin_thickness"
    link_sockets(tree, thick_n, store_thick.inputs["Value"])
    link_sockets(tree, set_pos.outputs["Geometry"], store_thick.inputs["Geometry"])

    link_sockets(tree, store_thick.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(arch_curve, "curve")
    color_node(arch_inst, "instance")
    color_node(breath, "noise")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Arches", "nodes": ("arch_curve", "arch_inst", "arch_scale"), "role": "curve"},
        {"title": "Breathing", "nodes": ("breath", "set_pos"), "role": "geometry"},
        {"title": "Output", "nodes": ("store_thick", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 3. MEL_shell_pygidium — tail fan shell with biolum
# -----------------------------------------------------------------------------

def build_shell_pygidium(group_name="MEL_shell_pygidium"):
    """Tail fan shell — the pygidium with bioluminescent veins.

    Inputs:
      Fan Angle, Vein Density, Biolum Intensity, Pulse Phase, Scale
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    angle_n = add_float_param(tree, "Fan Angle", 120.0, 10.0, 360.0)
    vein_n = add_int_param(tree, "Vein Count", 12, 1, 48)
    biolum_n = add_float_param(tree, "Biolum Intensity", 2.0, 0.0, 10.0)
    phase_n = add_float_param(tree, "Pulse Phase", 0.0, 0.0, 6.28)
    scale_n = add_float_param(tree, "Scale", 1.0, 0.01, 100.0)

    # Base fan: cone with wide angle
    fan = safe_node(tree, "GeometryNodeMeshCone", (bx - 400, by))
    fan.inputs["Vertices"].default_value = 24
    fan.inputs["Radius Bottom"].default_value = 2.0
    fan.inputs["Radius Top"].default_value = 0.0
    fan.inputs["Depth"].default_value = 1.0

    # Scale
    fan_scale = safe_node(tree, "GeometryNodeTransform", (bx - 200, by))
    link_sockets(tree, fan.outputs["Mesh"], fan_scale.inputs["Geometry"])
    link_sockets(tree, scale_n, fan_scale.inputs["Scale"])

    # Veins: instanced lines radiating from center
    vein_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by - 200))
    link_sockets(tree, vein_n, vein_line.inputs["Count"])
    vein_line.inputs["Offset"].default_value = (0.0, 1.0, 0.0)

    vein_pts = safe_node(tree, "GeometryNodeDistributePointsOnFaces", (bx - 400, by - 260))
    link_sockets(tree, fan_scale.outputs["Geometry"], vein_pts.inputs["Mesh"])
    vein_pts.distribute_method = "RANDOM"

    vein_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 200, by - 200))
    link_sockets(tree, vein_pts.outputs["Points"], vein_inst.inputs["Points"])
    link_sockets(tree, vein_line.outputs["Mesh"], vein_inst.inputs["Instance"])
    vein_real = safe_node(tree, "GeometryNodeRealizeInstances", (bx, by - 200))
    link_sockets(tree, vein_inst.outputs["Instances"], vein_real.inputs["Geometry"])

    # Join fan + veins
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 200, by))
    link_sockets(tree, fan_scale.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, vein_real.outputs["Geometry"], join.inputs["Geometry"])

    # Pulse phase
    pulse = safe_node(tree, "ShaderNodeMath", (bx + 200, by - 350))
    pulse.operation = "SINE"
    link_sockets(tree, phase_n, pulse.inputs[0])

    pulse_mul = safe_node(tree, "ShaderNodeMath", (bx + 300, by - 350))
    pulse_mul.operation = "MULTIPLY"
    link_sockets(tree, pulse.outputs["Value"], pulse_mul.inputs[0])
    link_sockets(tree, biolum_n, pulse_mul.inputs[1])

    # Store attributes
    store_biolum = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 400, by))
    store_biolum.data_type = "FLOAT"
    store_biolum.inputs["Name"].default_value = "biolum_intensity"
    link_sockets(tree, pulse_mul.outputs["Value"], store_biolum.inputs["Value"])
    link_sockets(tree, join.outputs["Geometry"], store_biolum.inputs["Geometry"])

    link_sockets(tree, store_biolum.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(fan, "geometry")
    color_node(vein_inst, "instance")
    color_node(pulse, "noise")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Fan", "nodes": ("fan", "fan_scale"), "role": "geometry"},
        {"title": "Veins", "nodes": ("vein_line", "vein_inst", "vein_real"), "role": "geometry"},
        {"title": "Output", "nodes": ("store_biolum", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 4. MEL_shell_interior — walkable hollow shell interior
# -----------------------------------------------------------------------------

def build_shell_interior(group_name="MEL_shell_interior"):
    """Walkable hollow shell interior — the cathedral sacred space.

    Inputs:
      Wall Thickness, Arch Count, Vein Spacing, Cathedral Height, Breathing Depth
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    wt_n = add_float_param(tree, "Wall Thickness", 0.3, 0.01, 3.0)
    arch_n = add_int_param(tree, "Arch Count", 12, 1, 48)
    vein_n = add_float_param(tree, "Vein Spacing", 1.0, 0.1, 10.0)
    height_n = add_float_param(tree, "Cathedral Height", 8.0, 0.5, 50.0)
    breath_n = add_float_param(tree, "Breathing Depth", 0.1, 0.0, 2.0)

    # Outer shell: large dome
    outer = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 400, by))
    outer.inputs["Rings"].default_value = 24
    outer.inputs["Segments"].default_value = 32

    # Scale to cathedral shape (taller than wide)
    outer_scale = safe_node(tree, "GeometryNodeTransform", (bx - 200, by))
    link_sockets(tree, outer.outputs["Mesh"], outer_scale.inputs["Geometry"])
    outer_scale.inputs["Scale"].default_value = (1.0, 1.0, 1.5)

    # Inner shell: smaller sphere for hollowing
    inner = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 400, by - 200))
    inner.inputs["Rings"].default_value = 24
    inner.inputs["Segments"].default_value = 32

    inner_scale = safe_node(tree, "GeometryNodeTransform", (bx - 200, by - 200))
    link_sockets(tree, inner.outputs["Mesh"], inner_scale.inputs["Geometry"])
    inner_scale.inputs["Scale"].default_value = (1.0, 1.0, 1.5)

    # Boolean difference for hollow interior
    boolean = safe_node(tree, "GeometryNodeMeshBoolean", (bx, by))
    boolean.operation = "DIFFERENCE"
    link_sockets(tree, outer_scale.outputs["Geometry"], boolean.inputs["Mesh 1"])
    link_sockets(tree, inner_scale.outputs["Geometry"], boolean.inputs["Mesh 2"])

    # Breathing displacement
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx, by - 300))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx + 200, by - 300))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    noise = safe_node(tree, "ShaderNodeTexNoise", (bx + 200, by - 400))
    noise.inputs["Scale"].default_value = 0.5
    link_sockets(tree, breath_n, noise.inputs["Detail"])

    noise_mul = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 400))
    noise_mul.operation = "MULTIPLY"
    link_sockets(tree, noise.outputs["Fac"], noise_mul.inputs[0])
    noise_mul.inputs[1].default_value = 0.05

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 400, by))
    link_sockets(tree, boolean.outputs["Mesh"], set_pos.inputs["Geometry"])
    z_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 200, by - 500))
    z_vec.inputs["X"].default_value = 0.0
    z_vec.inputs["Y"].default_value = 0.0
    link_sockets(tree, noise_mul.outputs["Value"], z_vec.inputs["Z"])
    link_sockets(tree, z_vec.outputs["Vector"], set_pos.inputs["Offset"])

    # Store attributes
    store_height = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 600, by))
    store_height.data_type = "FLOAT"
    store_height.inputs["Name"].default_value = "cathedral_height"
    link_sockets(tree, height_n, store_height.inputs["Value"])
    link_sockets(tree, set_pos.outputs["Geometry"], store_height.inputs["Geometry"])

    link_sockets(tree, store_height.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(outer, "geometry")
    color_node(boolean, "geometry")
    color_node(noise, "noise")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Shell", "nodes": ("outer", "inner", "boolean"), "role": "geometry"},
        {"title": "Breathing", "nodes": ("noise", "set_pos"), "role": "geometry"},
        {"title": "Output", "nodes": ("store_height", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 5. MEL_fracture_seam — crack lines breaking open
# -----------------------------------------------------------------------------

def build_fracture_seam(group_name="MEL_fracture_seam"):
    """Crack lines where the shell breaks open — fracture seams.

    Inputs:
      Crack Count, Crack Depth, Glow Leak, Decay Age, Scale
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    count_n = add_int_param(tree, "Crack Count", 8, 1, 32)
    depth_n = add_float_param(tree, "Crack Depth", 0.5, 0.01, 5.0)
    glow_n = add_float_param(tree, "Glow Leak", 1.5, 0.0, 5.0)
    decay_n = add_float_param(tree, "Decay Age", 0.5, 0.0, 1.0)
    scale_n = add_float_param(tree, "Scale", 1.0, 0.01, 100.0)

    # Crack paths: random walk lines
    crack_base = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by))
    link_sockets(tree, count_n, crack_base.inputs["Count"])
    crack_base.inputs["Offset"].default_value = (0.0, 1.0, 0.0)

    # Randomize crack paths
    crack_noise = safe_node(tree, "ShaderNodeTexNoise", (bx - 200, by - 100))
    crack_noise.inputs["Scale"].default_value = 3.0
    crack_noise.inputs["Detail"].default_value = 6.0

    crack_set = safe_node(tree, "GeometryNodeSetPosition", (bx, by))
    link_sockets(tree, crack_base.outputs["Mesh"], crack_set.inputs["Geometry"])
    crack_disp = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 200, by - 200))
    link_float_to_vector(tree, crack_noise.outputs["Fac"], crack_disp, "X", defaults=(0.0, 0.0, 0.0))
    link_sockets(tree, crack_disp.outputs["Vector"], crack_set.inputs["Offset"])

    # Convert to curve
    crack_curve = safe_node(tree, "GeometryNodeMeshToCurve", (bx + 200, by))
    link_sockets(tree, crack_set.outputs["Mesh"], crack_curve.inputs["Mesh"])

    # Set radius for crack width
    crack_radius = safe_node(tree, "GeometryNodeSetCurveRadius", (bx + 400, by))
    link_sockets(tree, crack_curve.outputs["Curve"], crack_radius.inputs["Curve"])
    crack_radius.inputs["Radius"].default_value = 0.02

    # Store attributes
    store_depth = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 600, by))
    store_depth.data_type = "FLOAT"
    store_depth.inputs["Name"].default_value = "crack_depth"
    link_sockets(tree, depth_n, store_depth.inputs["Value"])
    link_sockets(tree, crack_radius.outputs["Curve"], store_depth.inputs["Geometry"])

    store_glow = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 800, by))
    store_glow.data_type = "FLOAT"
    store_glow.inputs["Name"].default_value = "glow_leak"
    link_sockets(tree, glow_n, store_glow.inputs["Value"])
    link_sockets(tree, store_depth.outputs["Geometry"], store_glow.inputs["Geometry"])

    store_decay = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 1000, by))
    store_decay.data_type = "FLOAT"
    store_decay.inputs["Name"].default_value = "decay_age"
    link_sockets(tree, decay_n, store_decay.inputs["Value"])
    link_sockets(tree, store_glow.outputs["Geometry"], store_decay.inputs["Geometry"])

    link_sockets(tree, store_decay.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(crack_base, "curve")
    color_node(crack_noise, "noise")
    color_node(crack_set, "geometry")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Cracks", "nodes": ("crack_base", "crack_noise", "crack_set"), "role": "curve"},
        {"title": "Output", "nodes": ("store_depth", "store_glow", "store_decay", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 6. MEL_biolum_vein — glowing bioluminescent veins
# -----------------------------------------------------------------------------

def build_biolum_vein(group_name="MEL_biolum_vein"):
    """Glowing bioluminescent veins — living light that breathes.

    Inputs:
      Vein Count, Pulse Speed, Color Shift, Breathing Depth, Scale
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    count_n = add_int_param(tree, "Vein Count", 16, 1, 64)
    pulse_n = add_float_param(tree, "Pulse Speed", 1.0, 0.0, 5.0)
    shift_n = add_float_param(tree, "Color Shift", 0.5, 0.0, 1.0)
    breath_n = add_float_param(tree, "Breathing Depth", 0.3, 0.0, 2.0)
    scale_n = add_float_param(tree, "Scale", 1.0, 0.01, 100.0)

    # Vein paths: branching lines
    vein_base = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by))
    link_sockets(tree, count_n, vein_base.inputs["Count"])
    vein_base.inputs["Offset"].default_value = (0.0, 1.0, 0.0)

    # Randomize vein paths
    vein_noise = safe_node(tree, "ShaderNodeTexNoise", (bx - 200, by - 100))
    vein_noise.inputs["Scale"].default_value = 2.0
    vein_noise.inputs["Detail"].default_value = 4.0

    vein_set = safe_node(tree, "GeometryNodeSetPosition", (bx, by))
    link_sockets(tree, vein_base.outputs["Mesh"], vein_set.inputs["Geometry"])
    vein_disp = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 200, by - 200))
    link_float_to_vector(tree, vein_noise.outputs["Fac"], vein_disp, "X", defaults=(0.0, 0.0, 0.0))
    link_sockets(tree, vein_disp.outputs["Vector"], vein_set.inputs["Offset"])

    # Convert to curve
    vein_curve = safe_node(tree, "GeometryNodeMeshToCurve", (bx + 200, by))
    link_sockets(tree, vein_set.outputs["Mesh"], vein_curve.inputs["Mesh"])

    # Set radius
    vein_radius = safe_node(tree, "GeometryNodeSetCurveRadius", (bx + 400, by))
    link_sockets(tree, vein_curve.outputs["Curve"], vein_radius.inputs["Curve"])
    vein_radius.inputs["Radius"].default_value = 0.01

    # Pulse animation
    pulse = safe_node(tree, "ShaderNodeMath", (bx + 200, by - 350))
    pulse.operation = "SINE"
    link_sockets(tree, pulse_n, pulse.inputs[0])

    pulse_mul = safe_node(tree, "ShaderNodeMath", (bx + 300, by - 350))
    pulse_mul.operation = "MULTIPLY"
    link_sockets(tree, pulse.outputs["Value"], pulse_mul.inputs[0])
    link_sockets(tree, breath_n, pulse_mul.inputs[1])

    # Store attributes
    store_pulse = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 600, by))
    store_pulse.data_type = "FLOAT"
    store_pulse.inputs["Name"].default_value = "pulse_intensity"
    link_sockets(tree, pulse_mul.outputs["Value"], store_pulse.inputs["Value"])
    link_sockets(tree, vein_radius.outputs["Curve"], store_pulse.inputs["Geometry"])

    store_shift = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 800, by))
    store_shift.data_type = "FLOAT"
    store_shift.inputs["Name"].default_value = "color_shift"
    link_sockets(tree, shift_n, store_shift.inputs["Value"])
    link_sockets(tree, store_pulse.outputs["Geometry"], store_shift.inputs["Geometry"])

    link_sockets(tree, store_shift.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(vein_base, "curve")
    color_node(vein_noise, "noise")
    color_node(pulse, "noise")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Veins", "nodes": ("vein_base", "vein_noise", "vein_set"), "role": "curve"},
        {"title": "Pulse", "nodes": ("pulse", "store_pulse"), "role": "noise"},
        {"title": "Output", "nodes": ("store_shift", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 7. MEL_gravity_well — spacetime distortion volume
# -----------------------------------------------------------------------------

def build_gravity_well(group_name="MEL_gravity_well"):
    """Spacetime distortion volume — mass warps space around the shell.

    Inputs:
      Distortion Strength, Lens Radius, Chromatic Aberration, Breathing Pulse, Scale
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    distort_n = add_float_param(tree, "Distortion Strength", 0.5, 0.0, 5.0)
    lens_n = add_float_param(tree, "Lens Radius", 5.0, 0.1, 50.0)
    chroma_n = add_float_param(tree, "Chromatic Aberration", 0.3, 0.0, 2.0)
    pulse_n = add_float_param(tree, "Breathing Pulse", 1.0, 0.0, 5.0)
    scale_n = add_float_param(tree, "Scale", 1.0, 0.01, 100.0)

    # Base volume: sphere
    sphere = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 400, by))
    sphere.inputs["Rings"].default_value = 16
    sphere.inputs["Segments"].default_value = 24

    # Scale
    sphere_scale = safe_node(tree, "GeometryNodeTransform", (bx - 200, by))
    link_sockets(tree, sphere.outputs["Mesh"], sphere_scale.inputs["Geometry"])
    link_sockets(tree, scale_n, sphere_scale.inputs["Scale"])

    # Distortion: displace vertices based on distance from center
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx, by - 200))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx + 200, by - 200))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    # Distance from center
    dist_sq = safe_node(tree, "ShaderNodeMath", (bx + 200, by - 300))
    dist_sq.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["X"], dist_sq.inputs[0])
    link_sockets(tree, sep.outputs["X"], dist_sq.inputs[1])

    dist_sq_y = safe_node(tree, "ShaderNodeMath", (bx + 200, by - 360))
    dist_sq_y.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["Y"], dist_sq_y.inputs[0])
    link_sockets(tree, sep.outputs["Y"], dist_sq_y.inputs[1])

    dist_sum = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 360))
    dist_sum.operation = "ADD"
    link_sockets(tree, dist_sq.outputs["Value"], dist_sum.inputs[0])
    link_sockets(tree, dist_sq_y.outputs["Value"], dist_sum.inputs[1])

    dist = safe_node(tree, "ShaderNodeMath", (bx + 500, by - 360))
    dist.operation = "SQRT"
    link_sockets(tree, dist_sum.outputs["Value"], dist.inputs[0])

    # Inverse distance for gravity falloff
    inv_dist = safe_node(tree, "ShaderNodeMath", (bx + 600, by - 360))
    inv_dist.operation = "DIVIDE"
    inv_dist.inputs[0].default_value = 1.0
    link_sockets(tree, dist.outputs["Value"], inv_dist.inputs[1])

    # Distortion strength
    distort_mul = safe_node(tree, "ShaderNodeMath", (bx + 700, by - 360))
    distort_mul.operation = "MULTIPLY"
    link_sockets(tree, inv_dist.outputs["Value"], distort_mul.inputs[0])
    link_sockets(tree, distort_n, distort_mul.inputs[1])

    # Breathing pulse
    pulse = safe_node(tree, "ShaderNodeMath", (bx + 200, by - 500))
    pulse.operation = "SINE"
    link_sockets(tree, pulse_n, pulse.inputs[0])

    pulse_mul = safe_node(tree, "ShaderNodeMath", (bx + 300, by - 500))
    pulse_mul.operation = "MULTIPLY"
    link_sockets(tree, pulse.outputs["Value"], pulse_mul.inputs[0])
    pulse_mul.inputs[1].default_value = 0.1

    # Combine distortion + pulse
    combined = safe_node(tree, "ShaderNodeMath", (bx + 800, by - 360))
    combined.operation = "ADD"
    link_sockets(tree, distort_mul.outputs["Value"], combined.inputs[0])
    link_sockets(tree, pulse_mul.outputs["Value"], combined.inputs[1])

    # Displace
    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 1000, by))
    link_sockets(tree, sphere_scale.outputs["Geometry"], set_pos.inputs["Geometry"])
    disp_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 800, by - 200))
    link_float_to_vector(tree, combined.outputs["Value"], disp_vec, "X", defaults=(0.0, 0.0, 0.0))
    link_sockets(tree, disp_vec.outputs["Vector"], set_pos.inputs["Offset"])

    # Store attributes
    store_lens = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 1200, by))
    store_lens.data_type = "FLOAT"
    store_lens.inputs["Name"].default_value = "lens_radius"
    link_sockets(tree, lens_n, store_lens.inputs["Value"])
    link_sockets(tree, set_pos.outputs["Geometry"], store_lens.inputs["Geometry"])

    store_chroma = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 1400, by))
    store_chroma.data_type = "FLOAT"
    store_chroma.inputs["Name"].default_value = "chromatic_aberration"
    link_sockets(tree, chroma_n, store_chroma.inputs["Value"])
    link_sockets(tree, store_lens.outputs["Geometry"], store_chroma.inputs["Geometry"])

    link_sockets(tree, store_chroma.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(sphere, "volume")
    color_node(dist, "math")
    color_node(set_pos, "volume")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Volume", "nodes": ("sphere", "sphere_scale"), "role": "volume"},
        {"title": "Distortion", "nodes": ("dist", "inv_dist", "set_pos"), "role": "volume"},
        {"title": "Output", "nodes": ("store_lens", "store_chroma", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 8. MEL_aftermath_fragment — scattered old molt fragments
# -----------------------------------------------------------------------------

def build_aftermath_fragment(group_name="MEL_aftermath_fragment"):
    """Scattered old molt fragments — aftermath of the god's molting.

    Inputs:
      Fragment Count, Scatter Range, Decay Age, Chitin Remnant, Scale
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    count_n = add_int_param(tree, "Fragment Count", 24, 1, 128)
    scatter_n = add_float_param(tree, "Scatter Range", 10.0, 0.1, 100.0)
    decay_n = add_float_param(tree, "Decay Age", 0.5, 0.0, 1.0)
    remnant_n = add_float_param(tree, "Chitin Remnant", 0.3, 0.0, 1.0)
    scale_n = add_float_param(tree, "Scale", 1.0, 0.01, 100.0)

    # Fragment base: small irregular shapes
    frag_base = safe_node(tree, "GeometryNodeMeshCube", (bx - 400, by))
    frag_base.inputs["Size"].default_value = (0.3, 0.1, 0.05)

    # Scatter points
    scatter_grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 600, by - 200))
    link_sockets(tree, scatter_n, scatter_grid.inputs["Size X"])
    link_sockets(tree, scatter_n, scatter_grid.inputs["Size Y"])
    scatter_grid.inputs["Vertices X"].default_value = 8
    scatter_grid.inputs["Vertices Y"].default_value = 8

    scatter_pts = safe_node(tree, "GeometryNodeDistributePointsOnFaces", (bx - 400, by - 200))
    link_sockets(tree, scatter_grid.outputs["Mesh"], scatter_pts.inputs["Mesh"])
    scatter_pts.distribute_method = "RANDOM"
    link_sockets(tree, count_n, scatter_pts.inputs["Seed"])

    # Randomize fragment positions
    scatter_noise = safe_node(tree, "ShaderNodeTexNoise", (bx - 200, by - 300))
    scatter_noise.inputs["Scale"].default_value = 2.0

    scatter_set = safe_node(tree, "GeometryNodeSetPosition", (bx - 200, by - 200))
    link_sockets(tree, scatter_pts.outputs["Points"], scatter_set.inputs["Geometry"])
    scatter_disp = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 400, by - 400))
    link_float_to_vector(tree, scatter_noise.outputs["Fac"], scatter_disp, "X", defaults=(0.0, 0.0, 0.0))
    link_sockets(tree, scatter_disp.outputs["Vector"], scatter_set.inputs["Offset"])

    # Instance fragments
    frag_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx, by))
    link_sockets(tree, scatter_set.outputs["Geometry"], frag_inst.inputs["Points"])
    link_sockets(tree, frag_base.outputs["Mesh"], frag_inst.inputs["Instance"])

    # Random scale per fragment
    frag_scale = safe_node(tree, "GeometryNodeScaleInstances", (bx + 200, by))
    link_sockets(tree, frag_inst.outputs["Instances"], frag_scale.inputs["Instances"])
    frag_scale.inputs["Scale"].default_value = (1.0, 1.0, 1.0)

    # Realize
    frag_real = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 400, by))
    link_sockets(tree, frag_scale.outputs["Instances"], frag_real.inputs["Geometry"])

    # Store attributes
    store_decay = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 600, by))
    store_decay.data_type = "FLOAT"
    store_decay.inputs["Name"].default_value = "decay_age"
    link_sockets(tree, decay_n, store_decay.inputs["Value"])
    link_sockets(tree, frag_real.outputs["Geometry"], store_decay.inputs["Geometry"])

    store_remnant = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 800, by))
    store_remnant.data_type = "FLOAT"
    store_remnant.inputs["Name"].default_value = "chitin_remnant"
    link_sockets(tree, remnant_n, store_remnant.inputs["Value"])
    link_sockets(tree, store_decay.outputs["Geometry"], store_remnant.inputs["Geometry"])

    link_sockets(tree, store_remnant.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(frag_base, "geometry")
    color_node(scatter_pts, "points")
    color_node(frag_inst, "instance")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Scatter", "nodes": ("scatter_grid", "scatter_pts", "scatter_set"), "role": "points"},
        {"title": "Fragments", "nodes": ("frag_base", "frag_inst", "frag_scale"), "role": "geometry"},
        {"title": "Output", "nodes": ("store_decay", "store_remnant", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# Registry
# -----------------------------------------------------------------------------

from .core import register_builder

register_builder("MEL_shell_cephalon", build_shell_cephalon,
    "Shell Cephalon",
    "Trilobite head shell — the cephalon with segmented lobes",
    "god_molts")

register_builder("MEL_shell_thorax", build_shell_thorax,
    "Shell Thorax",
    "Segmented thorax arches — the cathedral ribbed interior",
    "god_molts")

register_builder("MEL_shell_pygidium", build_shell_pygidium,
    "Shell Pygidium",
    "Tail fan shell — the pygidium with bioluminescent veins",
    "god_molts")

register_builder("MEL_shell_interior", build_shell_interior,
    "Shell Interior",
    "Walkable hollow shell interior — the cathedral sacred space",
    "god_molts")

register_builder("MEL_fracture_seam", build_fracture_seam,
    "Fracture Seam",
    "Crack lines where the shell breaks open — fracture seams",
    "god_molts")

register_builder("MEL_biolum_vein", build_biolum_vein,
    "Biolum Vein",
    "Glowing bioluminescent veins — living light that breathes",
    "god_molts")

register_builder("MEL_gravity_well", build_gravity_well,
    "Gravity Well",
    "Spacetime distortion volume — mass warps space around the shell",
    "god_molts")

register_builder("MEL_aftermath_fragment", build_aftermath_fragment,
    "Aftermath Fragment",
    "Scattered old molt fragments — aftermath of the god's molting",
    "god_molts")
