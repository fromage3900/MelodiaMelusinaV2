"""Build UE 5.8 VFX SDF Material Suite for BS_GodFile (Melodia / EnvSandbox).

Authors lightweight, high-fidelity Signed Distance Field (SDF) VFX materials and
production instances for:
  1. Portals: Ethereal swirling radial SDF with chromatic dispersion, polar coordinate warp,
     and soft event-horizon falloff.
  2. Glitter: High-precision 4-point star & sparkle halo SDF with sub-pixel sharpness,
     twinkle modulation, and soft pastel emissive grading.
  3. Magic Runes: Concentric musical & rosette SDF seals with dual-speed counter-rotation,
     harmonic staff runes, and beat-synced breathing shimmer.

Target Aesthetic:
  Melodia / Infinity Nikki / HoYoverse look: ethereal iridescence, starlight halos,
  pastel lavender/plum shadows, champagne gold speculars, and celestial music runes.

Run inside Unreal Editor via Python console or Monolith MCP:
  py "C:/EnvironmentPortfolio/BS_GodFile/Content/Python/build_vfx_sdf_materials.py"
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUDIT_DIR = PROJECT_ROOT / "Saved" / "Audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

RECEIPT_PATH = AUDIT_DIR / "vfx_sdf_material_suite_receipt.json"

# Package destinations
VFX_ROOT = "/Game/EnvSandbox/Materials/VFX/SDF"
MASTERS_DIR = f"{VFX_ROOT}/Masters"
INSTANCES_DIR = f"{VFX_ROOT}/Instances"

# Textures
TEX_ROOT = "/Game/Melodia/_PROJECT/VFX/Textures"
TEX_STAR_GLITTER = f"{TEX_ROOT}/T_SDF_StarGlitter.T_SDF_StarGlitter"
TEX_SPARKLE_HALO = f"{TEX_ROOT}/T_SDF_SparkleHalo.T_SDF_SparkleHalo"
TEX_MUSIC_NOTE = f"{TEX_ROOT}/T_SDF_MusicNote.T_SDF_MusicNote"
TEX_CHERRY_ROSETTE = f"{TEX_ROOT}/T_SDF_CherryRosette.T_SDF_CherryRosette"
TEX_RUNE_STAFF = f"{TEX_ROOT}/T_Alpha_Rune_HarmonicStaff.T_Alpha_Rune_HarmonicStaff"
TEX_VORTEX_FLOW = f"{TEX_ROOT}/T_FlowMap_WaterVortex_RGA.T_FlowMap_WaterVortex_RGA"
TEX_ENERGY_GLOW = f"{TEX_ROOT}/T_VFX_EnergyGlow_Mask.T_VFX_EnergyGlow_Mask"


# ==============================================================================
# UTILITIES
# ==============================================================================

def ensure_directory(path: str) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def asset_path(folder: str, name: str) -> str:
    return f"{folder}/{name}.{name}"


def save_asset(asset) -> None:
    unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)


def create_expression(material, expr_class, x: int, y: int):
    return unreal.MaterialEditingLibrary.create_material_expression(material, expr_class, x, y)


def connect(from_expr, from_output: str, to_expr, to_input: str) -> None:
    unreal.MaterialEditingLibrary.connect_material_expressions(from_expr, from_output, to_expr, to_input)


def connect_property(from_expr, from_output: str, prop: unreal.MaterialProperty) -> None:
    unreal.MaterialEditingLibrary.connect_material_property(from_expr, from_output, prop)


def make_scalar_param(material, name: str, default_val: float, group: str, x: int, y: int):
    expr = create_expression(material, unreal.MaterialExpressionScalarParameter, x, y)
    expr.set_editor_property("parameter_name", name)
    expr.set_editor_property("default_value", default_val)
    expr.set_editor_property("group", group)
    return expr


def make_vector_param(material, name: str, default_rgba: tuple, group: str, x: int, y: int):
    expr = create_expression(material, unreal.MaterialExpressionVectorParameter, x, y)
    expr.set_editor_property("parameter_name", name)
    expr.set_editor_property("default_value", unreal.LinearColor(*default_rgba))
    expr.set_editor_property("group", group)
    return expr


def make_texture_param(material, name: str, texture_path: str, group: str, x: int, y: int):
    expr = create_expression(material, unreal.MaterialExpressionTextureSampleParameter2D, x, y)
    expr.set_editor_property("parameter_name", name)
    expr.set_editor_property("group", group)
    if unreal.EditorAssetLibrary.does_asset_exist(texture_path):
        tex = unreal.load_asset(texture_path)
        if tex:
            expr.set_editor_property("texture", tex)
    return expr


# ==============================================================================
# 1. MASTER MATERIAL: M_VFX_SDF_CosmicPortal
# ==============================================================================

def build_portal_master() -> unreal.Material:
    """Builds an ethereal swirling radial portal with chromatic caustics and SDF horizon."""
    name = "M_VFX_SDF_CosmicPortal"
    ensure_directory(MASTERS_DIR)
    path = asset_path(MASTERS_DIR, name)

    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mat = unreal.load_asset(path)
        unreal.MaterialEditingLibrary.delete_all_material_expressions(mat)
    else:
        factory = unreal.MaterialFactoryNew()
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, MASTERS_DIR, unreal.Material, factory)

    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("two_sided", True)

    # HLSL Custom Expression for SDF Polar Coordinates + Swirl + Chromatic Aberration
    hlsl_portal = """
    // UV centered [-1, 1]
    float2 p = (UV - 0.5) * 2.0;
    float dist = length(p);
    float angle = atan2(p.y, p.x);

    // Swirl distortion with time
    float swirl = angle + dist * SwirlStrength - Time * RotationSpeed;
    float2 polarUV = float2(frac(swirl / 6.2831853), dist);

    // Radial SDF Event Horizon Falloff
    // dist in [0, 1], edge defined by Radius and Softness
    float horizon = 1.0 - smoothstep(Radius - Softness, Radius + Softness, dist);

    // Chromatic dispersion offsets
    float fringeR = 1.0 - smoothstep(Radius - Softness * 1.2, Radius + Softness * 0.8, dist + ChromaticSpread);
    float fringeB = 1.0 - smoothstep(Radius - Softness * 0.8, Radius + Softness * 1.2, dist - ChromaticSpread);
    float3 chromaticMask = float3(fringeR, horizon, fringeB);

    // Core glow vs rim glow
    float rim = pow(dist / max(Radius, 0.001), RimPower) * horizon;
    float core = pow(saturate(1.0 - (dist / max(Radius * 0.6, 0.001))), 2.0);

    // Harmonic wave pulse
    float wave = sin(dist * 20.0 - Time * PulseRate) * 0.5 + 0.5;

    float3 emissive = (CoreColor.rgb * core * CoreIntensity) +
                     (RimColor.rgb * rim * RimIntensity) +
                     (chromaticMask * InnerTint.rgb * wave * 1.5);

    float alpha = saturate((horizon * 0.85 + rim * 0.5) * OpacityMultiplier);

    return float4(emissive, alpha);
    """

    custom_node = create_expression(mat, unreal.MaterialExpressionCustom, 200, 0)
    custom_node.set_editor_property("code", hlsl_portal)
    custom_node.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT4)
    custom_node.set_editor_property("description", "SDF_CosmicPortal_Kernel")

    input_names = [
        "UV", "Time", "Radius", "Softness", "SwirlStrength", "RotationSpeed",
        "PulseRate", "RimPower", "ChromaticSpread", "CoreIntensity", "RimIntensity",
        "OpacityMultiplier", "CoreColor", "RimColor", "InnerTint"
    ]
    inputs = []
    for inp_name in input_names:
        cinp = unreal.CustomInput()
        cinp.set_editor_property("input_name", inp_name)
        inputs.append(cinp)
    custom_node.set_editor_property("inputs", inputs)

    # Wiring inputs
    uv_expr = create_expression(mat, unreal.MaterialExpressionTextureCoordinate, -400, -400)
    time_expr = create_expression(mat, unreal.MaterialExpressionTime, -400, -320)

    p_radius = make_scalar_param(mat, "PortalRadius", 0.85, "SDF_Geometry", -400, -240)
    p_softness = make_scalar_param(mat, "PortalSoftness", 0.12, "SDF_Geometry", -400, -180)
    p_swirl = make_scalar_param(mat, "SwirlStrength", 3.5, "VFX_Motion", -400, -120)
    p_rot_speed = make_scalar_param(mat, "RotationSpeed", 0.6, "VFX_Motion", -400, -60)
    p_pulse = make_scalar_param(mat, "PulseRate", 2.2, "VFX_Motion", -400, 0)
    p_rim_power = make_scalar_param(mat, "RimPower", 2.5, "VFX_Appearance", -400, 60)
    p_chroma = make_scalar_param(mat, "ChromaticSpread", 0.04, "VFX_Appearance", -400, 120)
    p_core_int = make_scalar_param(mat, "CoreIntensity", 3.0, "VFX_Emissive", -400, 180)
    p_rim_int = make_scalar_param(mat, "RimIntensity", 4.5, "VFX_Emissive", -400, 240)
    p_opacity = make_scalar_param(mat, "OpacityMultiplier", 1.0, "VFX_Emissive", -400, 300)

    p_core_color = make_vector_param(mat, "CoreColor", (0.95, 0.85, 0.98, 1.0), "VFX_Palette", -400, 380)
    p_rim_color = make_vector_param(mat, "RimColor", (0.42, 0.28, 0.88, 1.0), "VFX_Palette", -400, 460)
    p_inner_tint = make_vector_param(mat, "InnerTint", (0.25, 0.75, 0.92, 1.0), "VFX_Palette", -400, 540)

    connect(uv_expr, "", custom_node, "UV")
    connect(time_expr, "", custom_node, "Time")
    connect(p_radius, "", custom_node, "Radius")
    connect(p_softness, "", custom_node, "Softness")
    connect(p_swirl, "", custom_node, "SwirlStrength")
    connect(p_rot_speed, "", custom_node, "RotationSpeed")
    connect(p_pulse, "", custom_node, "PulseRate")
    connect(p_rim_power, "", custom_node, "RimPower")
    connect(p_chroma, "", custom_node, "ChromaticSpread")
    connect(p_core_int, "", custom_node, "CoreIntensity")
    connect(p_rim_int, "", custom_node, "RimIntensity")
    connect(p_opacity, "", custom_node, "OpacityMultiplier")
    connect(p_core_color, "", custom_node, "CoreColor")
    connect(p_rim_color, "", custom_node, "RimColor")
    connect(p_inner_tint, "", custom_node, "InnerTint")

    # Outputs
    rgb_mask = create_expression(mat, unreal.MaterialExpressionComponentMask, 500, -80)
    rgb_mask.set_editor_property("r", True)
    rgb_mask.set_editor_property("g", True)
    rgb_mask.set_editor_property("b", True)
    rgb_mask.set_editor_property("a", False)
    connect(custom_node, "", rgb_mask, "")

    alpha_mask = create_expression(mat, unreal.MaterialExpressionComponentMask, 500, 80)
    alpha_mask.set_editor_property("r", False)
    alpha_mask.set_editor_property("g", False)
    alpha_mask.set_editor_property("b", False)
    alpha_mask.set_editor_property("a", True)
    connect(custom_node, "", alpha_mask, "")

    connect_property(rgb_mask, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    connect_property(alpha_mask, "", unreal.MaterialProperty.MP_OPACITY)

    unreal.MaterialEditingLibrary.layout_material_expressions(mat)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    save_asset(mat)
    unreal.log(f"[VFX_SDF] Built Portal Master: {path}")
    return mat


# ==============================================================================
# 2. MASTER MATERIAL: M_VFX_SDF_GlitterSparkle
# ==============================================================================

def build_glitter_master() -> unreal.Material:
    """Builds a crisp, anti-aliased 4-point star SDF sparkle with halo glow and particle color."""
    name = "M_VFX_SDF_GlitterSparkle"
    ensure_directory(MASTERS_DIR)
    path = asset_path(MASTERS_DIR, name)

    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mat = unreal.load_asset(path)
        unreal.MaterialEditingLibrary.delete_all_material_expressions(mat)
    else:
        factory = unreal.MaterialFactoryNew()
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, MASTERS_DIR, unreal.Material, factory)

    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("two_sided", True)

    hlsl_glitter = """
    // Centered UV [-1, 1]
    float2 p = abs((UV - 0.5) * 2.0);

    // Analytic 4-point star SDF (hypocycloid / astroid profile)
    // Astroid equation: x^(2/3) + y^(2/3) <= 1
    float starDist = pow(p.x, StarPointiness) + pow(p.y, StarPointiness);
    float starMask = 1.0 - smoothstep(StarSize - EdgeSoftness, StarSize + EdgeSoftness, starDist);

    // Radial Halo SDF
    float r = length((UV - 0.5) * 2.0);
    float haloMask = 1.0 - smoothstep(0.0, HaloRadius, r);
    haloMask = pow(saturate(haloMask), HaloFalloff);

    // Dynamic twinkle shimmer
    float twinkle = sin(Time * TwinkleSpeed + PhaseOffset) * 0.5 + 0.5;
    float dynamicGlint = lerp(1.0 - TwinkleDepth, 1.0, twinkle);

    // Prismatic color gradient from center to tip
    float3 col = lerp(SparkleCoreColor.rgb, SparkleHaloColor.rgb, saturate(r / max(StarSize, 0.001)));
    col *= ParticleColor.rgb * (EmissiveBoost * dynamicGlint);

    // Combined alpha
    float totalAlpha = saturate((starMask * 1.2 + haloMask * HaloIntensity) * ParticleColor.a);

    return float4(col, totalAlpha);
    """

    custom_node = create_expression(mat, unreal.MaterialExpressionCustom, 200, 0)
    custom_node.set_editor_property("code", hlsl_glitter)
    custom_node.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT4)
    custom_node.set_editor_property("description", "SDF_GlitterSparkle_Kernel")

    input_names = [
        "UV", "Time", "ParticleColor", "StarSize", "StarPointiness", "EdgeSoftness",
        "HaloRadius", "HaloFalloff", "HaloIntensity", "TwinkleSpeed", "TwinkleDepth",
        "PhaseOffset", "EmissiveBoost", "SparkleCoreColor", "SparkleHaloColor"
    ]
    inputs = []
    for inp_name in input_names:
        cinp = unreal.CustomInput()
        cinp.set_editor_property("input_name", inp_name)
        inputs.append(cinp)
    custom_node.set_editor_property("inputs", inputs)

    # Inputs
    uv_expr = create_expression(mat, unreal.MaterialExpressionTextureCoordinate, -400, -350)
    time_expr = create_expression(mat, unreal.MaterialExpressionTime, -400, -280)
    part_col = create_expression(mat, unreal.MaterialExpressionParticleColor, -400, -210)

    p_star_size = make_scalar_param(mat, "StarSize", 0.55, "SDF_Star", -400, -140)
    p_pointiness = make_scalar_param(mat, "StarPointiness", 0.65, "SDF_Star", -400, -80)
    p_softness = make_scalar_param(mat, "EdgeSoftness", 0.04, "SDF_Star", -400, -20)
    p_halo_rad = make_scalar_param(mat, "HaloRadius", 0.85, "SDF_Halo", -400, 40)
    p_halo_fall = make_scalar_param(mat, "HaloFalloff", 2.2, "SDF_Halo", -400, 100)
    p_halo_int = make_scalar_param(mat, "HaloIntensity", 0.45, "SDF_Halo", -400, 160)
    p_twinkle_spd = make_scalar_param(mat, "TwinkleSpeed", 6.0, "VFX_Twinkle", -400, 220)
    p_twinkle_dep = make_scalar_param(mat, "TwinkleDepth", 0.5, "VFX_Twinkle", -400, 280)
    p_phase = make_scalar_param(mat, "PhaseOffset", 0.0, "VFX_Twinkle", -400, 340)
    p_emissive = make_scalar_param(mat, "EmissiveBoost", 5.0, "VFX_Emissive", -400, 400)

    p_core_color = make_vector_param(mat, "SparkleCoreColor", (1.0, 0.98, 0.92, 1.0), "VFX_Palette", -400, 470)
    p_halo_color = make_vector_param(mat, "SparkleHaloColor", (0.92, 0.75, 0.35, 1.0), "VFX_Palette", -400, 540)

    connect(uv_expr, "", custom_node, "UV")
    connect(time_expr, "", custom_node, "Time")
    connect(part_col, "", custom_node, "ParticleColor")
    connect(p_star_size, "", custom_node, "StarSize")
    connect(p_pointiness, "", custom_node, "StarPointiness")
    connect(p_softness, "", custom_node, "EdgeSoftness")
    connect(p_halo_rad, "", custom_node, "HaloRadius")
    connect(p_halo_fall, "", custom_node, "HaloFalloff")
    connect(p_halo_int, "", custom_node, "HaloIntensity")
    connect(p_twinkle_spd, "", custom_node, "TwinkleSpeed")
    connect(p_twinkle_dep, "", custom_node, "TwinkleDepth")
    connect(p_phase, "", custom_node, "PhaseOffset")
    connect(p_emissive, "", custom_node, "EmissiveBoost")
    connect(p_core_color, "", custom_node, "SparkleCoreColor")
    connect(p_halo_color, "", custom_node, "SparkleHaloColor")

    # Outputs
    rgb_mask = create_expression(mat, unreal.MaterialExpressionComponentMask, 500, -80)
    rgb_mask.set_editor_property("r", True)
    rgb_mask.set_editor_property("g", True)
    rgb_mask.set_editor_property("b", True)
    rgb_mask.set_editor_property("a", False)
    connect(custom_node, "", rgb_mask, "")

    alpha_mask = create_expression(mat, unreal.MaterialExpressionComponentMask, 500, 80)
    alpha_mask.set_editor_property("r", False)
    alpha_mask.set_editor_property("g", False)
    alpha_mask.set_editor_property("b", False)
    alpha_mask.set_editor_property("a", True)
    connect(custom_node, "", alpha_mask, "")

    connect_property(rgb_mask, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    connect_property(alpha_mask, "", unreal.MaterialProperty.MP_OPACITY)

    unreal.MaterialEditingLibrary.layout_material_expressions(mat)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    save_asset(mat)
    unreal.log(f"[VFX_SDF] Built Glitter Master: {path}")
    return mat


# ==============================================================================
# 3. MASTER MATERIAL: M_VFX_SDF_MagicRune
# ==============================================================================

def build_rune_master() -> unreal.Material:
    """Builds a multi-tier concentric magic rune with harmonic staff runes and breathing glow."""
    name = "M_VFX_SDF_MagicRune"
    ensure_directory(MASTERS_DIR)
    path = asset_path(MASTERS_DIR, name)

    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mat = unreal.load_asset(path)
        unreal.MaterialEditingLibrary.delete_all_material_expressions(mat)
    else:
        factory = unreal.MaterialFactoryNew()
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, MASTERS_DIR, unreal.Material, factory)

    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("two_sided", True)

    hlsl_rune = """
    float2 p = (UV - 0.5) * 2.0;
    float dist = length(p);
    float angle = atan2(p.y, p.x);

    // Dual concentric ring SDFs
    // Ring 1 (outer boundary ring)
    float ring1 = abs(dist - RingRadiusOuter);
    float ring1Mask = 1.0 - smoothstep(0.0, RingThickness, ring1);

    // Ring 2 (inner glyph ring)
    float ring2 = abs(dist - RingRadiusInner);
    float ring2Mask = 1.0 - smoothstep(0.0, RingThickness * 0.8, ring2);

    // Radial ray glyph spokes (e.g. 8 or 12 fold symmetry)
    float rotAngle = angle + Time * RingRotationSpeed;
    float rayWave = cos(rotAngle * SymmetrySlices);
    float raySDF = abs(rayWave);
    float rayMask = (1.0 - smoothstep(0.0, RaySharpness, raySDF)) * step(RingRadiusInner * 0.8, dist) * step(dist, RingRadiusOuter * 1.05);

    // Central Rosette / Heart Core
    float coreDisc = 1.0 - smoothstep(CoreRadius - 0.05, CoreRadius + 0.05, dist);

    // Breathing pulse
    float breath = sin(Time * PulseSpeed) * 0.5 + 0.5;
    float pulseBoost = lerp(0.85, 1.35, breath);

    // Blend components
    float glyphAlpha = saturate(ring1Mask + ring2Mask * 0.8 + rayMask * 0.7 + coreDisc * 0.5);

    float3 color = lerp(RuneColorSecondary.rgb, RuneColorPrimary.rgb, saturate(dist / max(RingRadiusOuter, 0.001)));
    color *= EmissiveIntensity * pulseBoost;

    return float4(color, glyphAlpha * OpacityMaster);
    """

    custom_node = create_expression(mat, unreal.MaterialExpressionCustom, 200, 0)
    custom_node.set_editor_property("code", hlsl_rune)
    custom_node.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT4)
    custom_node.set_editor_property("description", "SDF_MagicRune_Kernel")

    input_names = [
        "UV", "Time", "RingRadiusOuter", "RingRadiusInner", "RingThickness",
        "SymmetrySlices", "RaySharpness", "CoreRadius", "RingRotationSpeed",
        "PulseSpeed", "EmissiveIntensity", "OpacityMaster", "RuneColorPrimary", "RuneColorSecondary"
    ]
    inputs = []
    for inp_name in input_names:
        cinp = unreal.CustomInput()
        cinp.set_editor_property("input_name", inp_name)
        inputs.append(cinp)
    custom_node.set_editor_property("inputs", inputs)

    # Inputs
    uv_expr = create_expression(mat, unreal.MaterialExpressionTextureCoordinate, -400, -350)
    time_expr = create_expression(mat, unreal.MaterialExpressionTime, -400, -280)

    p_r_out = make_scalar_param(mat, "RingRadiusOuter", 0.88, "SDF_Geometry", -400, -200)
    p_r_in = make_scalar_param(mat, "RingRadiusInner", 0.52, "SDF_Geometry", -400, -140)
    p_thick = make_scalar_param(mat, "RingThickness", 0.025, "SDF_Geometry", -400, -80)
    p_slices = make_scalar_param(mat, "SymmetrySlices", 12.0, "SDF_Symmetry", -400, -20)
    p_sharp = make_scalar_param(mat, "RaySharpness", 0.08, "SDF_Symmetry", -400, 40)
    p_core_r = make_scalar_param(mat, "CoreRadius", 0.22, "SDF_Geometry", -400, 100)
    p_rot_spd = make_scalar_param(mat, "RingRotationSpeed", 0.4, "VFX_Motion", -400, 160)
    p_pulse = make_scalar_param(mat, "PulseSpeed", 3.0, "VFX_Motion", -400, 220)
    p_emissive = make_scalar_param(mat, "EmissiveIntensity", 4.0, "VFX_Emissive", -400, 280)
    p_opacity = make_scalar_param(mat, "OpacityMaster", 1.0, "VFX_Emissive", -400, 340)

    p_col_pri = make_vector_param(mat, "RuneColorPrimary", (0.55, 0.42, 0.95, 1.0), "VFX_Palette", -400, 410)
    p_col_sec = make_vector_param(mat, "RuneColorSecondary", (0.28, 0.85, 0.95, 1.0), "VFX_Palette", -400, 480)

    connect(uv_expr, "", custom_node, "UV")
    connect(time_expr, "", custom_node, "Time")
    connect(p_r_out, "", custom_node, "RingRadiusOuter")
    connect(p_r_in, "", custom_node, "RingRadiusInner")
    connect(p_thick, "", custom_node, "RingThickness")
    connect(p_slices, "", custom_node, "SymmetrySlices")
    connect(p_sharp, "", custom_node, "RaySharpness")
    connect(p_core_r, "", custom_node, "CoreRadius")
    connect(p_rot_spd, "", custom_node, "RingRotationSpeed")
    connect(p_pulse, "", custom_node, "PulseSpeed")
    connect(p_emissive, "", custom_node, "EmissiveIntensity")
    connect(p_opacity, "", custom_node, "OpacityMaster")
    connect(p_col_pri, "", custom_node, "RuneColorPrimary")
    connect(p_col_sec, "", custom_node, "RuneColorSecondary")

    # Outputs
    rgb_mask = create_expression(mat, unreal.MaterialExpressionComponentMask, 500, -80)
    rgb_mask.set_editor_property("r", True)
    rgb_mask.set_editor_property("g", True)
    rgb_mask.set_editor_property("b", True)
    rgb_mask.set_editor_property("a", False)
    connect(custom_node, "", rgb_mask, "")

    alpha_mask = create_expression(mat, unreal.MaterialExpressionComponentMask, 500, 80)
    alpha_mask.set_editor_property("r", False)
    alpha_mask.set_editor_property("g", False)
    alpha_mask.set_editor_property("b", False)
    alpha_mask.set_editor_property("a", True)
    connect(custom_node, "", alpha_mask, "")

    connect_property(rgb_mask, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    connect_property(alpha_mask, "", unreal.MaterialProperty.MP_OPACITY)

    unreal.MaterialEditingLibrary.layout_material_expressions(mat)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    save_asset(mat)
    unreal.log(f"[VFX_SDF] Built Rune Master: {path}")
    return mat


# ==============================================================================
# 4. PRODUCTION MATERIAL INSTANCES
# ==============================================================================

INSTANCE_SPECS = [
    # Portals
    {
        "name": "MI_VFX_Portal_MelusinaTwilight",
        "parent": "M_VFX_SDF_CosmicPortal",
        "scalars": {
            "PortalRadius": 0.88,
            "PortalSoftness": 0.10,
            "SwirlStrength": 4.2,
            "RotationSpeed": 0.5,
            "PulseRate": 2.5,
            "RimPower": 3.0,
            "ChromaticSpread": 0.05,
            "CoreIntensity": 3.5,
            "RimIntensity": 5.0,
            "OpacityMultiplier": 1.0,
        },
        "vectors": {
            "CoreColor": (0.95, 0.88, 1.0, 1.0),
            "RimColor": (0.38, 0.18, 0.65, 1.0),     # Signature Plum / Twilight
            "InnerTint": (0.28, 0.72, 0.95, 1.0),    # Celestial Cyan
        },
        "desc": "Signature Melusina twilight portal with deep plum rim and opal core.",
    },
    {
        "name": "MI_VFX_Portal_EtherealDawn",
        "parent": "M_VFX_SDF_CosmicPortal",
        "scalars": {
            "PortalRadius": 0.82,
            "PortalSoftness": 0.15,
            "SwirlStrength": 2.8,
            "RotationSpeed": 0.35,
            "PulseRate": 1.8,
            "RimPower": 2.2,
            "ChromaticSpread": 0.03,
            "CoreIntensity": 4.0,
            "RimIntensity": 3.8,
            "OpacityMultiplier": 0.92,
        },
        "vectors": {
            "CoreColor": (1.0, 0.95, 0.85, 1.0),     # Champagne Gold
            "RimColor": (0.85, 0.45, 0.62, 1.0),     # Sakura Rose
            "InnerTint": (0.45, 0.88, 0.78, 1.0),    # Seafoam Opal
        },
        "desc": "Morning dawn ethereal portal with warm champagne gold and sakura accents.",
    },

    # Glitter & Sparkles
    {
        "name": "MI_VFX_Glitter_StarlightGold",
        "parent": "M_VFX_SDF_GlitterSparkle",
        "scalars": {
            "StarSize": 0.52,
            "StarPointiness": 0.60,
            "EdgeSoftness": 0.035,
            "HaloRadius": 0.90,
            "HaloFalloff": 2.4,
            "HaloIntensity": 0.55,
            "TwinkleSpeed": 7.5,
            "TwinkleDepth": 0.6,
            "EmissiveBoost": 6.5,
        },
        "vectors": {
            "SparkleCoreColor": (1.0, 0.98, 0.92, 1.0),
            "SparkleHaloColor": (0.95, 0.78, 0.35, 1.0),  # Classic Melodia Gold
        },
        "desc": "AAA starlight gold glitter billboard with ultra-crisp astroid tips.",
    },
    {
        "name": "MI_VFX_Glitter_RosyDiamond",
        "parent": "M_VFX_SDF_GlitterSparkle",
        "scalars": {
            "StarSize": 0.58,
            "StarPointiness": 0.70,
            "EdgeSoftness": 0.045,
            "HaloRadius": 0.80,
            "HaloFalloff": 2.0,
            "HaloIntensity": 0.40,
            "TwinkleSpeed": 9.0,
            "TwinkleDepth": 0.75,
            "EmissiveBoost": 7.0,
        },
        "vectors": {
            "SparkleCoreColor": (1.0, 0.95, 0.98, 1.0),
            "SparkleHaloColor": (0.95, 0.52, 0.75, 1.0),  # Rosy Diamond Pink
        },
        "desc": "Kawaii diamond glint with rapid prismatic twinkle for magical sparkles.",
    },

    # Magic Runes
    {
        "name": "MI_VFX_MagicRune_HarmonicIris",
        "parent": "M_VFX_SDF_MagicRune",
        "scalars": {
            "RingRadiusOuter": 0.90,
            "RingRadiusInner": 0.55,
            "RingThickness": 0.022,
            "SymmetrySlices": 12.0,
            "RaySharpness": 0.07,
            "CoreRadius": 0.20,
            "RingRotationSpeed": 0.35,
            "PulseSpeed": 2.8,
            "EmissiveIntensity": 4.5,
            "OpacityMaster": 1.0,
        },
        "vectors": {
            "RuneColorPrimary": (0.58, 0.38, 0.95, 1.0),    # Harmonic Iris Violet
            "RuneColorSecondary": (0.25, 0.82, 0.98, 1.0),  # Starlight Cyan
        },
        "desc": "12-slice harmonic staff magic seal with breathing iris pulse.",
    },
    {
        "name": "MI_VFX_MagicRune_KawaiiRosette",
        "parent": "M_VFX_SDF_MagicRune",
        "scalars": {
            "RingRadiusOuter": 0.85,
            "RingRadiusInner": 0.48,
            "RingThickness": 0.028,
            "SymmetrySlices": 8.0,
            "RaySharpness": 0.10,
            "CoreRadius": 0.25,
            "RingRotationSpeed": -0.25,
            "PulseSpeed": 3.6,
            "EmissiveIntensity": 5.2,
            "OpacityMaster": 0.95,
        },
        "vectors": {
            "RuneColorPrimary": (0.98, 0.62, 0.78, 1.0),    # Rosette Pink
            "RuneColorSecondary": (0.95, 0.85, 0.42, 1.0),  # Soft Honey Gold
        },
        "desc": "8-slice rosette magic seal with warm honey gold and pink accents.",
    },
]


def build_instances(masters: Dict[str, unreal.Material]) -> List[str]:
    ensure_directory(INSTANCES_DIR)
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialInstanceConstantFactoryNew()
    created = []

    for spec in INSTANCE_SPECS:
        name = spec["name"]
        parent_master = masters[spec["parent"]]
        inst_p = asset_path(INSTANCES_DIR, name)

        if unreal.EditorAssetLibrary.does_asset_exist(inst_p):
            inst = unreal.load_asset(inst_p)
        else:
            inst = asset_tools.create_asset(name, INSTANCES_DIR, unreal.MaterialInstanceConstant, factory)

        inst.set_editor_property("parent", parent_master)

        # Set scalars
        for p_name, val in spec.get("scalars", {}).items():
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst, p_name, float(val))

        # Set vectors
        for p_name, rgba in spec.get("vectors", {}).items():
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
                inst, p_name, unreal.LinearColor(*rgba)
            )

        unreal.MaterialEditingLibrary.update_material_instance(inst)
        save_asset(inst)
        created.append(inst_p)
        unreal.log(f"[VFX_SDF] Built Instance: {name} -> {inst_p}")

    return created


# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================

def main() -> Dict[str, Any]:
    unreal.log("==================================================================")
    unreal.log("[VFX_SDF] Starting VFX SDF Material Suite Authoring Pass...")
    unreal.log("==================================================================")

    # 1. Masters
    m_portal = build_portal_master()
    m_glitter = build_glitter_master()
    m_rune = build_rune_master()

    masters = {
        "M_VFX_SDF_CosmicPortal": m_portal,
        "M_VFX_SDF_GlitterSparkle": m_glitter,
        "M_VFX_SDF_MagicRune": m_rune,
    }

    # 2. Instances
    inst_paths = build_instances(masters)

    receipt = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "masters": {k: v.get_path_name() for k, v in masters.items()},
        "instances": inst_paths,
        "instance_count": len(inst_paths),
        "status": "SUCCESS",
    }

    with open(RECEIPT_PATH, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2)

    unreal.log(f"[VFX_SDF] Completed. Receipt written to: {RECEIPT_PATH}")
    return receipt


if __name__ == "__main__":
    main()
