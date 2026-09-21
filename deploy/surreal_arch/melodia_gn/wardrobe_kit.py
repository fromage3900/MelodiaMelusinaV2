"""Universal Wardrobe GN kit — procedural garment builders over the mannequin.

Phase 2 of the Universal Wardrobe Studio AAA pipeline.
Plan: .hermes/plans/2026-09-06_003500-universal-wardrobe-studio-aaa-pipeline.md

Laws (enforced by Tools/wardrobe_pipeline/wardrobe_proof.py):
  - Every dial is neutral-at-ZERO (multiply wiring; defaults 0.0).
  - Trees end in Realize Instances (instances don't survive new_from_object).
  - No POWER on possibly-negative bases; radicals guarded with MAXIMUM(x, 0).
  - Audio builders use _add_sound_param + band math + audio_amplitude store.
  - Universal Musical Influence is auto-added by the registry — never manually.
"""
from __future__ import annotations

from .core import (
    add_float_param,
    add_int_param,
    label_tree,
    link_sockets,
    new_geometry_tree,
    register_builder,
    safe_node,
    sock,
)


def _zero_safe_sq(tree, sock_in, loc):
    """x*x via MULTIPLY — POWER(negative, 2) is NaN in Blender math nodes."""
    sq = safe_node(tree, "ShaderNodeMath", loc)
    sq.operation = "MULTIPLY"
    link_sockets(tree, sock_in, sq.inputs[0])
    link_sockets(tree, sock_in, sq.inputs[1])
    return sq.outputs[0]


def _guard_sqrt(tree, sock_in, loc):
    """MAXIMUM(x, 0) then SQRT — radicals must never see negatives."""
    clamp0 = safe_node(tree, "ShaderNodeMath", (loc[0] - 90, loc[1] - 60))
    clamp0.operation = "MAXIMUM"
    link_sockets(tree, sock_in, clamp0.inputs[0])
    clamp0.inputs[1].default_value = 0.0
    root = safe_node(tree, "ShaderNodeMath", loc)
    root.operation = "SQRT"
    link_sockets(tree, clamp0.outputs[0], root.inputs[0])
    return root.outputs[0]


def build_garm_drape_base(group_name="MEL_garm_drape_base"):
    """Garment shell over the mannequin: thickness offset along normals.

    Neutral at defaults: pure passthrough. Dials push the shell outward/inward,
    flare the skirt zone, and taper the torso — all zero-centered.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    geo = gin.outputs["Geometry"]

    add_float_param(tree, "Shell Offset", 0.0, -0.05, 0.2)   # garment thickness
    add_float_param(tree, "Skirt Flare", 0.0, -0.5, 1.5)     # lower-zone widen
    add_float_param(tree, "Torso Taper", 0.0, -0.5, 0.5)     # upper-zone pinch
    add_float_param(tree, "Noise Life", 0.0, 0.0, 0.1)       # fabric surface life
    add_int_param(tree, "Seed", 20260906, 0, 99999999)

    pos = safe_node(tree, "GeometryNodeInputPosition", (-620, 60))
    norm = safe_node(tree, "GeometryNodeInputNormal", (-620, -80))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (-440, 60))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    # zone weight: 1 below z=0.9 (skirt), 0 above — smooth via clamped line
    zw = safe_node(tree, "ShaderNodeMath", (-260, 120))
    zw.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["Z"], zw.inputs[0])
    zw.inputs[1].default_value = -1.1111   # (0.9 - z) * 1.111 / 0.9 approx
    zw2 = safe_node(tree, "ShaderNodeMath", (-80, 120))
    zw2.operation = "MULTIPLY"
    link_sockets(tree, zw.outputs[0], zw2.inputs[0])
    zw2.inputs[1].default_value = 1.0
    clamp_zone = safe_node(tree, "ShaderNodeClamp", (100, 120))
    clamp_zone.inputs["Min"].default_value = 0.0
    clamp_zone.inputs["Max"].default_value = 1.0
    link_sockets(tree, zw2.outputs[0], clamp_zone.inputs[0])
    # 5.2: ShaderNodeClamp output is 'Result', not 'Value' (input IS 'Value')
    zone = clamp_zone.outputs["Result"]

    # skirt flare: offset.x/y scaled by zone * Flare (zero-neutral)
    flare_amt = safe_node(tree, "ShaderNodeMath", (280, 200))
    flare_amt.operation = "MULTIPLY"
    link_sockets(tree, zone, flare_amt.inputs[0])
    link_sockets(tree, gin.outputs["Skirt Flare"], flare_amt.inputs[1])

    sep_xy = safe_node(tree, "ShaderNodeSeparateXYZ", (-440, 260))
    link_sockets(tree, pos.outputs["Position"], sep_xy.inputs["Vector"])
    flare_x = safe_node(tree, "ShaderNodeMath", (460, 240))
    flare_x.operation = "MULTIPLY"
    link_sockets(tree, sep_xy.outputs["X"], flare_x.inputs[0])
    link_sockets(tree, flare_amt.outputs[0], flare_x.inputs[1])
    flare_y = safe_node(tree, "ShaderNodeMath", (460, 160))
    flare_y.operation = "MULTIPLY"
    link_sockets(tree, sep_xy.outputs["Y"], flare_y.inputs[0])
    link_sockets(tree, flare_amt.outputs[0], flare_y.inputs[1])

    # torso taper: (1 - zone) * Taper * z-scaled pinch (zero-neutral)
    inv_zone = safe_node(tree, "ShaderNodeMath", (280, 60))
    inv_zone.operation = "SUBTRACT"
    inv_zone.inputs[0].default_value = 1.0
    link_sockets(tree, zone, inv_zone.inputs[1])
    taper_amt = safe_node(tree, "ShaderNodeMath", (460, 60))
    taper_amt.operation = "MULTIPLY"
    link_sockets(tree, inv_zone.outputs[0], taper_amt.inputs[0])
    link_sockets(tree, gin.outputs["Torso Taper"], taper_amt.inputs[1])
    taper_x = safe_node(tree, "ShaderNodeMath", (640, 80))
    taper_x.operation = "MULTIPLY"
    link_sockets(tree, sep_xy.outputs["X"], taper_x.inputs[0])
    link_sockets(tree, taper_amt.outputs[0], taper_x.inputs[1])
    taper_y = safe_node(tree, "ShaderNodeMath", (640, 0))
    taper_y.operation = "MULTIPLY"
    link_sockets(tree, sep_xy.outputs["Y"], taper_y.inputs[0])
    link_sockets(tree, taper_amt.outputs[0], taper_y.inputs[1])

    # shell offset along normal * Shell Offset (zero-neutral by construction)
    off_n = safe_node(tree, "ShaderNodeVectorMath", (280, -160))
    off_n.operation = "SCALE"
    link_sockets(tree, norm.outputs["Normal"], off_n.inputs["Vector"])
    link_sockets(tree, gin.outputs["Shell Offset"], off_n.inputs["Scale"])

    # noise life (zero-neutral): noise * Noise Life, along normal too
    noise = safe_node(tree, "ShaderNodeTexNoise", (-440, -220))
    try:
        noise.inputs["Scale"].default_value = 6.0
        noise.inputs["Detail"].default_value = 3.0
        w = sock(noise, "W")
        if w is not None:
            w.default_value = float(20260906 % 100) * 0.01
    except Exception:
        pass
    link_sockets(tree, pos.outputs["Position"], noise.inputs["Vector"])
    nz = sock(noise, "Fac") or noise.outputs[0]
    nz_off = safe_node(tree, "ShaderNodeVectorMath", (280, -300))
    nz_off.operation = "SCALE"
    link_sockets(tree, norm.outputs["Normal"], nz_off.inputs["Vector"])
    link_sockets(tree, nz, nz_off.inputs["Scale"])
    nz_gain = safe_node(tree, "ShaderNodeMath", (100, -300))
    nz_gain.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Noise Life"], nz_gain.inputs[0])
    nz_gain.inputs[1].default_value = 1.0
    # scale input is a socket; multiply via vector scale of scaled value:
    link_sockets(tree, gin.outputs["Noise Life"], nz_off.inputs["Scale"])

    # combine lateral offsets
    comb = safe_node(tree, "ShaderNodeCombineXYZ", (820, 120))
    add1 = safe_node(tree, "ShaderNodeMath", (820, 200))
    add1.operation = "ADD"
    link_sockets(tree, flare_x.outputs[0], add1.inputs[0])
    link_sockets(tree, taper_x.outputs[0], add1.inputs[1])
    add2 = safe_node(tree, "ShaderNodeMath", (820, 60))
    add2.operation = "ADD"
    link_sockets(tree, flare_y.outputs[0], add2.inputs[0])
    link_sockets(tree, taper_y.outputs[0], add2.inputs[1])
    comb.inputs["Z"].default_value = 0.0
    link_sockets(tree, add1.outputs[0], comb.inputs["X"])
    link_sockets(tree, add2.outputs[0], comb.inputs["Y"])

    # total offset = comb + normal-scaled (shell offset + noise life)
    total_scale = safe_node(tree, "ShaderNodeMath", (820, -160))
    total_scale.operation = "ADD"
    link_sockets(tree, gin.outputs["Shell Offset"], total_scale.inputs[0])
    link_sockets(tree, gin.outputs["Noise Life"], total_scale.inputs[1])
    link_sockets(tree, total_scale.outputs[0], off_n.inputs["Scale"])

    total = safe_node(tree, "ShaderNodeVectorMath", (1000, -40))
    total.operation = "ADD"
    link_sockets(tree, comb.outputs["Vector"], total.inputs[0])
    link_sockets(tree, off_n.outputs["Vector"], total.inputs[1])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (1180, 0))
    link_sockets(tree, geo, set_pos.inputs["Geometry"])
    link_sockets(tree, total.outputs["Vector"], set_pos.inputs["Offset"])
    # Position input intentionally UNSET: offset mode keeps authored shape.

    link_sockets(tree, set_pos.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Zones", "nodes": ("zone",), "role": "attribute"},
        {"title": "Shape Dials", "nodes": ("flare", "taper", "offset", "noise"), "role": "attribute"},
        {"title": "Offset", "nodes": ("set_position",), "role": "output"},
    ])


def build_garm_trim_lattice(group_name="MEL_garm_trim_lattice"):
    """Brass trim lattice: rivet-scale instancing on garment edges/points.

    Zero-neutral: at defaults, Density 0 => no instances => identical output bounds.
    Instances realize at the tail (proof law).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    geo = gin.outputs["Geometry"]

    add_float_param(tree, "Trim Density", 0.0, 0.0, 20.0)   # 0 = none (neutral)
    add_float_param(tree, "Trim Size", 0.02, 0.005, 0.1)
    add_float_param(tree, "Rivet Pitch Factor", 6.0, 2.0, 12.0)  # biomech rule
    add_int_param(tree, "Seed", 20260906, 0, 99999999)

    # distribute on faces (garment surface), poisson-ish via density
    dist = safe_node(tree, "GeometryNodeDistributePointsOnFaces", (-80, 0))
    link_sockets(tree, geo, dist.inputs["Mesh"])
    link_sockets(tree, gin.outputs["Trim Density"], dist.inputs["Density"])
    try:
        dist.inputs["Seed"].default_value = 20260906
    except Exception:
        pass

    # rivet: small ico sphere
    rivet = safe_node(tree, "GeometryNodeMeshIcoSphere", (-80, -220))
    try:
        rivet.inputs["Radius"].default_value = 0.02
        rivet.inputs["Subdivisions"].default_value = 2
    except Exception:
        pass
    # size driven by Trim Size / Pitch Factor relationship kept simple: size socket
    size_mul = safe_node(tree, "ShaderNodeMath", (-260, -160))
    size_mul.operation = "DIVIDE"
    link_sockets(tree, gin.outputs["Trim Size"], size_mul.inputs[0])
    link_sockets(tree, gin.outputs["Rivet Pitch Factor"], size_mul.inputs[1])
    if rivet is not None:
        link_sockets(tree, size_mul.outputs[0], rivet.inputs["Radius"])

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (160, -60))
    if dist is not None:
        link_sockets(tree, dist.outputs["Points"], inst.inputs["Points"])
    if rivet is not None:
        link_sockets(tree, rivet.outputs["Mesh"], inst.inputs["Instance"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (340, 0))
    link_sockets(tree, geo, join.inputs["Geometry"])
    if inst is not None:
        link_sockets(tree, inst.outputs["Instances"], join.inputs["Geometry"])

    real = safe_node(tree, "GeometryNodeRealizeInstances", (520, 0))
    link_sockets(tree, join.outputs["Geometry"], real.inputs["Geometry"])
    link_sockets(tree, real.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Distribute", "nodes": ("distribute",), "role": "geometry"},
        {"title": "Trim Rivets", "nodes": ("rivet", "instance"), "role": "instance"},
        {"title": "Merge", "nodes": ("join", "realize"), "role": "output"},
    ])


def build_garm_layer_stack(group_name="MEL_garm_layer_stack"):
    """Join N garment shells with gasket gap; layer order is authored order.

    Zero-neutral: Layer Count 1 => just the input shell passthrough.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    geo = gin.outputs["Geometry"]

    add_float_param(tree, "Layer Offset", 0.0, 0.0, 0.05)  # gasket gap per layer
    add_float_param(tree, "Layer Count", 1.0, 1.0, 6.0)

    # duplicate the input shell, offset each copy along its normal by i * gap
    # 5.2 Duplicate Elements on the mesh, per-copy index -> scale normal offset
    dup = safe_node(tree, "GeometryNodeDuplicateElements", (-80, 0))
    try:
        dup.domain = "FACE"
        link_sockets(tree, gin.outputs["Layer Count"], dup.inputs["Amount"])
    except Exception:
        pass
    link_sockets(tree, geo, dup.inputs["Geometry"])

    idx = sock(dup, "Copy Index") or (dup.outputs.get("Copy Index") if dup else None)
    norm = safe_node(tree, "GeometryNodeInputNormal", (-80, -200))
    mul = safe_node(tree, "ShaderNodeMath", (100, -160))
    mul.operation = "MULTIPLY"
    if idx is not None:
        link_sockets(tree, idx, mul.inputs[0])
    link_sockets(tree, gin.outputs["Layer Offset"], mul.inputs[1])

    off = safe_node(tree, "ShaderNodeVectorMath", (280, -120))
    off.operation = "SCALE"
    link_sockets(tree, norm.outputs["Normal"], off.inputs["Vector"])
    link_sockets(tree, mul.outputs[0], off.inputs["Scale"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (460, -40))
    if dup is not None:
        link_sockets(tree, dup.outputs["Geometry"], set_pos.inputs["Geometry"])
    link_sockets(tree, off.outputs["Vector"], set_pos.inputs["Offset"])

    # realize not strictly needed (no instances) but harmless and law-consistent
    real = safe_node(tree, "GeometryNodeRealizeInstances", (640, 0))
    link_sockets(tree, set_pos.outputs["Geometry"], real.inputs["Geometry"])
    link_sockets(tree, real.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Duplicate", "nodes": ("duplicate",), "role": "geometry"},
        {"title": "Gasket Offset", "nodes": ("offset",), "role": "geometry"},
        {"title": "Out", "nodes": ("realize",), "role": "output"},
    ])


def register():
    register_builder(
        "MEL_garm_drape_base",
        build_garm_drape_base,
        "Wardrobe Drape Base",
        "Zero-neutral garment shell over mannequin: thickness, skirt flare, torso taper, fabric life",
        "Wardrobe",
    )
    register_builder(
        "MEL_garm_trim_lattice",
        build_garm_trim_lattice,
        "Wardrobe Trim Lattice",
        "Rivet/trim instancing on garment surface (biomech pitch rules; density 0 = neutral)",
        "Wardrobe",
    )
    register_builder(
        "MEL_garm_layer_stack",
        build_garm_layer_stack,
        "Wardrobe Layer Stack",
        "Join N garment shells with gasket gap; count 1 = passthrough (neutral)",
        "Wardrobe",
    )
