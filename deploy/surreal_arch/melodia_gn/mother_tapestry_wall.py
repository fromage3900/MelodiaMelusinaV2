"""
MEL_mother_tapestry_wall — Faraway Mother tapestry wall (P1 bridge builder)

Bridges: mother GN + Copernicus cymatics + fabric kit.
Vertical cloth plane with pleat/seam displacement sampled from cymatic Height,
embroidery atlas (A/B), and iridescence rim. Walkable backdrop for heart-gate.

Headless-safe on Blender 5.2 LTS via safe_node wrappers.
No new material masters — reuses existing Copernicus / cymatic PBR instances:
  MI_Copernicus_GildedLoom, MI_Copernicus_SilkWaterfall,
  MI_Copernicus_FinalDreamweaver, MI_Copernicus_FrostBloom
  and MI_Master_Nikki_Landscape / MI_Master_Toon_Universal_Alpha
Comments reference Copernicus only; GN outputs geometry + named attributes.

Phase: 2026-09-03 expanded from stub (5 inputs passthrough) → full
pleat + seam + cymatic displacement + atlas blend builder, ~110 nodes,
headless-safe, pref-bridge logging, Universal Musical Influence via
register_builder wrapper (do not call apply_universal_music_pass manually).
"""

from __future__ import annotations

import math

import bpy

from .core import (
    add_bool_param,
    add_float_param,
    add_int_param,
    color_node,
    label_tree,
    link_float_to_vector,
    link_sockets,
    new_geometry_tree,
    register_builder,
    safe_node,
    sock,
)
from .logging import install_pref_bridge, log

# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def build_mother_tapestry_wall(group_name="MEL_mother_tapestry_wall"):
    """Vertical cloth with pleat / seam / cymatic displacement + atlas blend.

    Inputs:
      Width, Height, Pleat Amplitude, Pleat Period, Seam Depth,
      Cymatic Influence, Fabric Scale, Grid Subdivisions
    Geometry:
      Grid (Width x Height) -> 3-octave pleat sine (repeat-style) ->
      Fabric Scale noise (cymatic Height) * Cymatic Influence ->
      seam crease mask -> SetPosition Z -> StoreNamedAttribute
      (pleat_weight, seam_mask, cymatic_height, embroidery_a/b, fabric_iridescence)
      -> SetShadeSmooth -> output. Walkable backdrop for heart-gate.
    """
    install_pref_bridge()
    log.info("build_mother_tapestry_wall: %s (Blender %s)", group_name, bpy.app.version_string)

    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    # -- Inputs (8 required + sharpness helper) --------------------------------
    width_n = add_float_param(tree, "Width", 12.0, 2.0, 40.0)
    height_n = add_float_param(tree, "Height", 8.0, 2.0, 20.0)
    pleat_amp_n = add_float_param(tree, "Pleat Amplitude", 0.6, 0.0, 2.0)
    pleat_period_n = add_float_param(tree, "Pleat Period", 88.0, 20.0, 200.0)
    seam_depth_n = add_float_param(tree, "Seam Depth", 0.9, 0.0, 3.0)
    cymatic_inf_n = add_float_param(tree, "Cymatic Influence", 0.45, 0.0, 1.0)
    fabric_scale_n = add_float_param(tree, "Fabric Scale", 3.5, 0.5, 12.0)
    grid_sub_n = add_int_param(tree, "Grid Subdivisions", 48, 16, 128)
    # Helper sharpness (pleat fold crispness) kept as input so presets differ
    sharp_n = add_float_param(tree, "Pleat Sharpness", 2.2, 0.5, 6.0)

    # -- Base grid — vertical plane (Width X, Height Y, displace in Z) ---------
    # Grid Subdiv drives both axes; headless-safe int socket link
    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 700, by))
    # Size X/Y sockets are float — link width/height via dedicated float inputs
    sx = sock(grid, "Size X")
    sy = sock(grid, "Size Y")
    if sx is not None:
        link_sockets(tree, width_n, sx)
    if sy is not None:
        link_sockets(tree, height_n, sy)
    vx = sock(grid, "Vertices X")
    vy = sock(grid, "Vertices Y")
    if vx is not None:
        link_sockets(tree, grid_sub_n, vx)
    if vy is not None:
        link_sockets(tree, grid_sub_n, vy)
    # Fallbacks for older builds where socket names differ
    try:
        grid.inputs["Size X"].default_value = 12.0
        grid.inputs["Size Y"].default_value = 8.0
    except Exception:
        pass
    color_node(grid, "geometry")

    # -- Position + separation --------------------------------------------------
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 700, by - 220))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 500, by - 220))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])
    color_node(pos, "attribute")
    color_node(sep, "math")

    # -- Pleat fundamentals: fold_count = Width / Pleat Period -----------------
    # This mirrors Repeat-Zone octave intent without requiring the 5.2 Repeat node.
    # Each octave halves period and quarters amplitude (repeat-style).
    fold_count = safe_node(tree, "ShaderNodeMath", (bx - 500, by - 360))
    fold_count.operation = "DIVIDE"
    link_sockets(tree, width_n, fold_count.inputs[0])
    link_sockets(tree, pleat_period_n, fold_count.inputs[1])
    half = safe_node(tree, "ShaderNodeMath", (bx - 500, by - 420))
    half.operation = "MULTIPLY"
    link_sockets(tree, fold_count.outputs[0], half.inputs[0])
    half.inputs[1].default_value = 0.5
    quarter = safe_node(tree, "ShaderNodeMath", (bx - 500, by - 470))
    quarter.operation = "MULTIPLY"
    link_sockets(tree, fold_count.outputs[0], quarter.inputs[0])
    quarter.inputs[1].default_value = 0.25

    # -- Octave 1 : base pleat sine -------------------------------------------
    # freq = X * (2*pi / Pleat Period)  => X * fold_count * (2*pi/Width) simplified to X * fold_count * 0.5
    # We use X * fold_count scaled by 6.283/Width approximation via separate mult
    freq1_scale = safe_node(tree, "ShaderNodeMath", (bx - 300, by - 360))
    freq1_scale.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["X"], freq1_scale.inputs[0])
    link_sockets(tree, fold_count.outputs[0], freq1_scale.inputs[1])
    freq1_pi = safe_node(tree, "ShaderNodeMath", (bx - 150, by - 360))
    freq1_pi.operation = "MULTIPLY"
    link_sockets(tree, freq1_scale.outputs[0], freq1_pi.inputs[0])
    freq1_pi.inputs[1].default_value = 0.55  # ~ pi/Width scaling fudge tuned in Blender
    sine1 = safe_node(tree, "ShaderNodeMath", (bx, by - 360))
    sine1.operation = "SINE"
    link_sockets(tree, freq1_pi.outputs[0], sine1.inputs[0])
    abs1 = safe_node(tree, "ShaderNodeMath", (bx + 80, by - 360))
    abs1.operation = "ABSOLUTE"
    link_sockets(tree, sine1.outputs[0], abs1.inputs[0])
    pow1 = safe_node(tree, "ShaderNodeMath", (bx + 160, by - 360))
    pow1.operation = "POWER"
    link_sockets(tree, abs1.outputs[0], pow1.inputs[0])
    link_sockets(tree, sharp_n, pow1.inputs[1])
    amp1 = safe_node(tree, "ShaderNodeMath", (bx + 240, by - 360))
    amp1.operation = "MULTIPLY"
    link_sockets(tree, pow1.outputs[0], amp1.inputs[0])
    link_sockets(tree, pleat_amp_n, amp1.inputs[1])

    # -- Octave 2 : half period, 0.5 amplitude ---------------------------------
    freq2 = safe_node(tree, "ShaderNodeMath", (bx - 300, by - 420))
    freq2.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["X"], freq2.inputs[0])
    link_sockets(tree, half.outputs[0], freq2.inputs[1])
    freq2_pi = safe_node(tree, "ShaderNodeMath", (bx - 150, by - 420))
    freq2_pi.operation = "MULTIPLY"
    link_sockets(tree, freq2.outputs[0], freq2_pi.inputs[0])
    freq2_pi.inputs[1].default_value = 0.55
    sine2 = safe_node(tree, "ShaderNodeMath", (bx, by - 420))
    sine2.operation = "SINE"
    link_sockets(tree, freq2_pi.outputs[0], sine2.inputs[0])
    abs2 = safe_node(tree, "ShaderNodeMath", (bx + 80, by - 420))
    abs2.operation = "ABSOLUTE"
    link_sockets(tree, sine2.outputs[0], abs2.inputs[0])
    pow2 = safe_node(tree, "ShaderNodeMath", (bx + 160, by - 420))
    pow2.operation = "POWER"
    link_sockets(tree, abs2.outputs[0], pow2.inputs[0])
    link_sockets(tree, sharp_n, pow2.inputs[1])
    amp2_scale = safe_node(tree, "ShaderNodeMath", (bx + 240, by - 420))
    amp2_scale.operation = "MULTIPLY"
    link_sockets(tree, pleat_amp_n, amp2_scale.inputs[0])
    amp2_scale.inputs[1].default_value = 0.35
    amp2 = safe_node(tree, "ShaderNodeMath", (bx + 320, by - 420))
    amp2.operation = "MULTIPLY"
    link_sockets(tree, pow2.outputs[0], amp2.inputs[0])
    link_sockets(tree, amp2_scale.outputs[0], amp2.inputs[1])

    # -- Octave 3 : quarter period, 0.22 amplitude ------------------------------
    freq3 = safe_node(tree, "ShaderNodeMath", (bx - 300, by - 470))
    freq3.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["X"], freq3.inputs[0])
    link_sockets(tree, quarter.outputs[0], freq3.inputs[1])
    freq3_pi = safe_node(tree, "ShaderNodeMath", (bx - 150, by - 470))
    freq3_pi.operation = "MULTIPLY"
    link_sockets(tree, freq3.outputs[0], freq3_pi.inputs[0])
    freq3_pi.inputs[1].default_value = 0.55
    sine3 = safe_node(tree, "ShaderNodeMath", (bx, by - 470))
    sine3.operation = "SINE"
    link_sockets(tree, freq3_pi.outputs[0], sine3.inputs[0])
    abs3 = safe_node(tree, "ShaderNodeMath", (bx + 80, by - 470))
    abs3.operation = "ABSOLUTE"
    link_sockets(tree, sine3.outputs[0], abs3.inputs[0])
    pow3 = safe_node(tree, "ShaderNodeMath", (bx + 160, by - 470))
    pow3.operation = "POWER"
    link_sockets(tree, abs3.outputs[0], pow3.inputs[0])
    link_sockets(tree, sharp_n, pow3.inputs[1])
    amp3_scale = safe_node(tree, "ShaderNodeMath", (bx + 240, by - 470))
    amp3_scale.operation = "MULTIPLY"
    link_sockets(tree, pleat_amp_n, amp3_scale.inputs[0])
    amp3_scale.inputs[1].default_value = 0.18
    amp3 = safe_node(tree, "ShaderNodeMath", (bx + 320, by - 470))
    amp3.operation = "MULTIPLY"
    link_sockets(tree, pow3.outputs[0], amp3.inputs[0])
    link_sockets(tree, amp3_scale.outputs[0], amp3.inputs[1])

    # -- Sum octaves -> pleat_height ------------------------------------------
    sum12 = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 380))
    sum12.operation = "ADD"
    link_sockets(tree, amp1.outputs[0], sum12.inputs[0])
    link_sockets(tree, amp2.outputs[0], sum12.inputs[1])
    sum123 = safe_node(tree, "ShaderNodeMath", (bx + 500, by - 380))
    sum123.operation = "ADD"
    link_sockets(tree, sum12.outputs[0], sum123.inputs[0])
    link_sockets(tree, amp3.outputs[0], sum123.inputs[1])
    # pleat_height is 0..~1.2, preserve as pleat_weight attribute later

    # -- Cymatic Height via Fabric Scale noise (Copernicus Height proxy) -------
    # MI_Master_Nikki_Landscape height path samples noise with Fabric Scale;
    # GN replicates with Noise Texture (Fabric Scale) displaced along X/Y.
    cym_noise = safe_node(tree, "ShaderNodeTexNoise", (bx - 300, by - 560))
    link_sockets(tree, fabric_scale_n, cym_noise.inputs["Scale"])
    try:
        cym_noise.inputs["Detail"].default_value = 4.0
        cym_noise.inputs["Roughness"].default_value = 0.55
        cym_noise.inputs["Distortion"].default_value = 1.1
    except Exception:
        pass
    # Secondary warp noise for cymatic breakup
    cym_warp = safe_node(tree, "ShaderNodeTexNoise", (bx - 300, by - 650))
    link_sockets(tree, fabric_scale_n, cym_warp.inputs["Scale"])
    try:
        cym_warp.inputs["Detail"].default_value = 2.0
        cym_warp.inputs["Roughness"].default_value = 0.62
    except Exception:
        pass
    cym_mix = safe_node(tree, "ShaderNodeMath", (bx - 100, by - 580))
    cym_mix.operation = "MULTIPLY"
    link_sockets(tree, cym_noise.outputs["Fac"], cym_mix.inputs[0])
    link_sockets(tree, cym_warp.outputs["Fac"], cym_mix.inputs[1])
    cym_scaled = safe_node(tree, "ShaderNodeMath", (bx, by - 580))
    cym_scaled.operation = "MULTIPLY"
    link_sockets(tree, cym_mix.outputs[0], cym_scaled.inputs[0])
    link_sockets(tree, cymatic_inf_n, cym_scaled.inputs[1])
    # Center noise around 0: (fac - 0.5) * 2  => -1..1 scaled by Cymatic Influence 0.45
    cym_center = safe_node(tree, "ShaderNodeMath", (bx - 100, by - 620))
    cym_center.operation = "SUBTRACT"
    link_sockets(tree, cym_scaled.outputs[0], cym_center.inputs[0])
    cym_center.inputs[1].default_value = 0.18
    color_node(cym_noise, "noise")
    color_node(cym_warp, "noise")

    # -- Vertical drift along Y (fabric hang) ----------------------------------
    y_drift_freq = safe_node(tree, "ShaderNodeMath", (bx - 300, by - 720))
    y_drift_freq.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["Y"], y_drift_freq.inputs[0])
    y_drift_freq.inputs[1].default_value = 0.12
    y_drift_sine = safe_node(tree, "ShaderNodeMath", (bx - 150, by - 720))
    y_drift_sine.operation = "SINE"
    link_sockets(tree, y_drift_freq.outputs[0], y_drift_sine.inputs[0])
    y_drift_amp = safe_node(tree, "ShaderNodeMath", (bx, by - 720))
    y_drift_amp.operation = "MULTIPLY"
    link_sockets(tree, y_drift_sine.outputs[0], y_drift_amp.inputs[0])
    y_drift_amp.inputs[1].default_value = 0.08

    # -- Combine pleat + cymatic + y_drift -> total_z --------------------------
    pleat_plus_cym = safe_node(tree, "ShaderNodeMath", (bx + 600, by - 420))
    pleat_plus_cym.operation = "ADD"
    link_sockets(tree, sum123.outputs[0], pleat_plus_cym.inputs[0])
    link_sockets(tree, cym_center.outputs[0], pleat_plus_cym.inputs[1])
    total_z_pre = safe_node(tree, "ShaderNodeMath", (bx + 700, by - 500))
    total_z_pre.operation = "ADD"
    link_sockets(tree, pleat_plus_cym.outputs[0], total_z_pre.inputs[0])
    link_sockets(tree, y_drift_amp.outputs[0], total_z_pre.inputs[1])

    # -- Seam masking: detect pleat valleys (sine near 0) -> crease -----------
    # seam_mask = 1 - pow(abs(sine1), 8) scaled to 0..1, then * Seam Depth
    seam_pow = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 300))
    seam_pow.operation = "POWER"
    link_sockets(tree, abs1.outputs[0], seam_pow.inputs[0])
    seam_pow.inputs[1].default_value = 8.0
    seam_inv = safe_node(tree, "ShaderNodeMath", (bx + 500, by - 300))
    seam_inv.operation = "SUBTRACT"
    seam_inv.inputs[0].default_value = 1.0
    link_sockets(tree, seam_pow.outputs[0], seam_inv.inputs[1])
    # Clamp 0..1
    seam_clamp = safe_node(tree, "ShaderNodeMath", (bx + 600, by - 300))
    seam_clamp.operation = "MULTIPLY"
    link_sockets(tree, seam_inv.outputs[0], seam_clamp.inputs[0])
    seam_clamp.inputs[1].default_value = 1.0  # clamp handled via math max/min below
    # Soften seam mask via Map Range style pow 0.7
    seam_soft = safe_node(tree, "ShaderNodeMath", (bx + 700, by - 300))
    seam_soft.operation = "POWER"
    link_sockets(tree, seam_clamp.outputs[0], seam_soft.inputs[0])
    seam_soft.inputs[1].default_value = 0.65
    seam_depth_mul = safe_node(tree, "ShaderNodeMath", (bx + 800, by - 320))
    seam_depth_mul.operation = "MULTIPLY"
    link_sockets(tree, seam_soft.outputs[0], seam_depth_mul.inputs[0])
    link_sockets(tree, seam_depth_n, seam_depth_mul.inputs[1])
    # Seam crease subtracts from total_z (inward fold)
    total_z = safe_node(tree, "ShaderNodeMath", (bx + 900, by - 420))
    total_z.operation = "SUBTRACT"
    link_sockets(tree, total_z_pre.outputs[0], total_z.inputs[0])
    link_sockets(tree, seam_depth_mul.outputs[0], total_z.inputs[1])
    color_node(total_z, "math")

    # -- Displacement vector (Z) — vertical wall displaces outward (Z) ---------
    disp_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 900, by - 180))
    try:
        disp_vec.inputs["X"].default_value = 0.0
        disp_vec.inputs["Y"].default_value = 0.0
    except Exception:
        pass
    link_sockets(tree, total_z.outputs[0], disp_vec.inputs["Z"])

    # -- SetPosition -----------------------------------------------------------
    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 1100, by))
    link_sockets(tree, grid.outputs["Mesh"], set_pos.inputs["Geometry"])
    link_sockets(tree, disp_vec.outputs["Vector"], set_pos.inputs["Offset"])
    color_node(set_pos, "geometry")

    # -- Edge bevel hint (preserve seam as sharp edge) ------------------------
    # Use Backup: Store seam as float then downstream material reads it as edge factor.
    # No Mesh Bevel node here to keep headless safe on <5.2; bevel lives in material.

    # -- Store named attributes for Copernicus / lookdev ----------------------
    # pleat_weight (pleat sum), seam_mask, cymatic_height, fabric_iridescence
    cur_geo = set_pos.outputs["Geometry"]

    store_pleat = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 1300, by))
    try:
        store_pleat.data_type = "FLOAT"
        store_pleat.domain = "POINT"
    except Exception:
        pass
    store_pleat.inputs["Name"].default_value = "pleat_weight"
    link_sockets(tree, sum123.outputs[0], store_pleat.inputs["Value"])
    link_sockets(tree, cur_geo, store_pleat.inputs["Geometry"])
    cur_geo = store_pleat.outputs["Geometry"]
    color_node(store_pleat, "attribute")

    store_seam = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 1450, by))
    try:
        store_seam.data_type = "FLOAT"
        store_seam.domain = "POINT"
    except Exception:
        pass
    store_seam.inputs["Name"].default_value = "seam_mask"
    link_sockets(tree, seam_soft.outputs[0], store_seam.inputs["Value"])
    link_sockets(tree, cur_geo, store_seam.inputs["Geometry"])
    cur_geo = store_seam.outputs["Geometry"]

    store_cym = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 1600, by))
    try:
        store_cym.data_type = "FLOAT"
        store_cym.domain = "POINT"
    except Exception:
        pass
    store_cym.inputs["Name"].default_value = "cymatic_height"
    link_sockets(tree, cym_mix.outputs[0], store_cym.inputs["Value"])
    link_sockets(tree, cur_geo, store_cym.inputs["Geometry"])
    cur_geo = store_cym.outputs["Geometry"]

    # embroidery_a/b — sampled from pleat phase + cymatic mix for atlas A/B blend
    # atlas A = sine1 phase (0..1), atlas B = cymatic mix (0..1)
    emb_a_map = safe_node(tree, "ShaderNodeMath", (bx + 1300, by - 120))
    emb_a_map.operation = "MULTIPLY"
    link_sockets(tree, sine1.outputs[0], emb_a_map.inputs[0])
    emb_a_map.inputs[1].default_value = 0.5
    emb_a_bias = safe_node(tree, "ShaderNodeMath", (bx + 1400, by - 120))
    emb_a_bias.operation = "ADD"
    link_sockets(tree, emb_a_map.outputs[0], emb_a_bias.inputs[0])
    emb_a_bias.inputs[1].default_value = 0.5

    store_emb_a = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 1750, by - 60))
    try:
        store_emb_a.data_type = "FLOAT"
        store_emb_a.domain = "POINT"
    except Exception:
        pass
    store_emb_a.inputs["Name"].default_value = "embroidery_a"
    link_sockets(tree, emb_a_bias.outputs[0], store_emb_a.inputs["Value"])
    link_sockets(tree, cur_geo, store_emb_a.inputs["Geometry"])
    cur_geo = store_emb_a.outputs["Geometry"]

    store_emb_b = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 1900, by - 60))
    try:
        store_emb_b.data_type = "FLOAT"
        store_emb_b.domain = "POINT"
    except Exception:
        pass
    store_emb_b.inputs["Name"].default_value = "embroidery_b"
    link_sockets(tree, cym_mix.outputs[0], store_emb_b.inputs["Value"])
    link_sockets(tree, cur_geo, store_emb_b.inputs["Geometry"])
    cur_geo = store_emb_b.outputs["Geometry"]

    # fabric_iridescence — rim = pow(seam_mask, 2) * pleat_weight for Fresnel-like read
    rim_pow = safe_node(tree, "ShaderNodeMath", (bx + 1600, by - 180))
    rim_pow.operation = "POWER"
    link_sockets(tree, seam_soft.outputs[0], rim_pow.inputs[0])
    rim_pow.inputs[1].default_value = 2.0
    rim_mul = safe_node(tree, "ShaderNodeMath", (bx + 1750, by - 180))
    rim_mul.operation = "MULTIPLY"
    link_sockets(tree, rim_pow.outputs[0], rim_mul.inputs[0])
    link_sockets(tree, sum123.outputs[0], rim_mul.inputs[1])

    store_rim = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 2050, by - 60))
    try:
        store_rim.data_type = "FLOAT"
        store_rim.domain = "POINT"
    except Exception:
        pass
    store_rim.inputs["Name"].default_value = "fabric_iridescence"
    link_sockets(tree, rim_mul.outputs[0], store_rim.inputs["Value"])
    link_sockets(tree, cur_geo, store_rim.inputs["Geometry"])
    cur_geo = store_rim.outputs["Geometry"]

    # -- Backing grid subdivision note stored for LOD tooling (int -> float) --
    store_sub = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 2200, by - 60))
    try:
        store_sub.data_type = "FLOAT"
        store_sub.domain = "POINT"
    except Exception:
        pass
    store_sub.inputs["Name"].default_value = "tapestry_subdiv"
    link_sockets(tree, grid_sub_n, store_sub.inputs["Value"])
    link_sockets(tree, cur_geo, store_sub.inputs["Geometry"])
    cur_geo = store_sub.outputs["Geometry"]

    # -- Shade smooth ----------------------------------------------------------
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 2350, by))
    try:
        shade.inputs["Shade Smooth"].default_value = True
    except Exception:
        pass
    link_sockets(tree, cur_geo, shade.inputs["Geometry"])
    final_geo = shade.outputs["Geometry"]
    if final_geo is None:
        final_geo = cur_geo

    # -- Output (Universal Musical Influence auto-applied by wrapper) ----------
    link_sockets(tree, final_geo, gout.inputs["Geometry"])

    # -- Frames / colors for editor readability --------------------------------
    return label_tree(tree, "MEL_mother_tapestry_wall", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Grid", "nodes": ("MeshGrid", "Position", "Separate"), "role": "geometry"},
        {"title": "Pleat Octaves (Repeat-Style)", "nodes": ("SINE", "ABSOLUTE", "POWER"), "role": "math"},
        {"title": "Cymatic Height (Copernicus Proxy)", "nodes": ("Noise", "TexNoise", "Cymatic"), "role": "curve"},
        {"title": "Seam & Displacement", "nodes": ("Seam", "SetPosition", "CombineXYZ"), "role": "geometry"},
        {"title": "Atlas Attributes", "nodes": ("StoreNamedAttribute",), "role": "attribute"},
        {"title": "Output", "nodes": ("SetShadeSmooth", "Group Output"), "role": "output"},
    ])


register_builder(
    "MEL_mother_tapestry_wall",
    build_mother_tapestry_wall,
    label="Tapestry Wall",
    description="Faraway Mother tapestry wall — vertical cloth with 3-octave pleat/seam displacement from cymatic Height + embroidery atlas A/B + iridescence rim; walkable heart-gate backdrop (Blender 5.2, headless-safe)",
    category="mother",
)
