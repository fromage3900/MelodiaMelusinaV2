"""build_ui_material_suite.py - Canonical UI Material Suite Builder for Melodia.

Authors and wires:
1. M_UI_UniversalToon_Master: Cel stepped gradients, SDF box border, Ben-Day halftone, paper grain, drop shadow, sheen sweep, progress meter.
2. M_UI_Mstone_Master: Gemstone facet refraction, Chladni cymatics, spectral dispersion, Beer-Lambert absorption, glint sparkles, gilded bezel.
3. M_UI_Nikki_Master: Pastel watercolor grade, iridescent shimmer loop, white die-cut sticker edge, stardust sparkles, idle breathe.
4. M_UI_Storybook_RadialRing: Polar SDF ring arcs, dashed orbital rails, celestial pips.
5. M_UI_Storybook_OrreryDisc: Concentric astronomical disc frames, stardust backdrop.
6. Overhauls existing stubs: M_UI_Nikki_StorybookCard, M_UI_Nikki_VitalsMeter, M_UI_AudioGlow_Border.
7. Creates 16 canonical Material Instances (MIs) adhering to Figma design tokens and storybook specs.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal
import material_lib as lib

ROOT_FOLDER = "/Game/Melodia/UI/Materials"
AUDIT_REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "ui_material_suite_build.json"
AUDIT_REPORT.parent.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# HLSL SHADER SOURCES
# ==============================================================================

HLSL_UNIVERSAL_TOON = r"""
float2 dims = max(Dimensions, float2(16.0, 16.0));
float radius = clamp(CornerRadius, 0.0, min(dims.x, dims.y) * 0.5);

// 1. SDF Box Distance
float2 p = (UV - 0.5) * dims;
float2 b = (dims * 0.5) - radius;
float2 q = abs(p) - b;
float dist = length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - radius;
float aa = max(fwidth(dist), 0.75);

// Card body & border masks
float cardMask = 1.0 - smoothstep(-aa, aa, dist);
float bThick = max(BorderThickness, 0.5);
float borderDist = abs(dist + bThick * 0.5) - bThick * 0.5;
float borderMask = (1.0 - smoothstep(-aa, aa, borderDist)) * cardMask;
float innerMask = (1.0 - smoothstep(-aa, aa, dist + bThick)) * cardMask;

// 2. Drop Shadow (Figma spec: offset, blur, opacity)
float2 pShadow = (UV - 0.5) * dims - ShadowOffset;
float2 qShadow = abs(pShadow) - b;
float distShadow = length(max(qShadow, 0.0)) + min(max(qShadow.x, qShadow.y), 0.0) - radius;
float sBlur = max(ShadowBlur, 0.1);
float shadowMask = (1.0 - smoothstep(-sBlur, sBlur + aa, distShadow)) * (1.0 - cardMask);

// 3. Ben-Day Halftone (Toon Print)
float2 rUV = float2(UV.x * 0.7071 - UV.y * 0.7071, UV.x * 0.7071 + UV.y * 0.7071);
float2 dotCell = frac(rUV * max(HalftoneScale, 2.0)) - 0.5;
float dotDist = length(dotCell);
float dotRadius = 0.28 * (1.0 + BeatPulse * 0.25);
float dotMask = 1.0 - smoothstep(dotRadius - 0.05, dotRadius + 0.05, dotDist);

// 4. Paper Grain (Organic Tactile Feel)
float grain = frac(sin(dot(UV * dims * 0.25, float2(12.9898, 78.233))) * 43758.5453);
float grainMod = (grain - 0.5) * PaperGrainIntensity * 0.12;

// 5. Sheen Sweep (BraceVoluteSheen)
float sheenPos = UV.x * 0.7 + UV.y * 0.3;
float sheenDist = abs(sheenPos - frac(SheenSweep));
float sheenGlow = exp(-sheenDist * sheenDist * 90.0) * cardMask;

// 6. Progress Bar Mode
float isBar = step(0.5, IsProgressBar);
float fillMask = step(UV.x, FillProgress);
float tick = 1.0 - step(0.04, frac(UV.x * 10.0));
fillMask = lerp(fillMask, fillMask * (1.0 - tick * 0.25), 0.7);
float barLead = exp(-abs(UV.x - FillProgress) * 50.0) * isBar;

// 7. Shading Composite
float3 baseCol = FillColor.rgb * (1.0 + grainMod);
float3 withHalftone = lerp(baseCol, AccentColor.rgb, dotMask * HalftoneIntensity * 0.6);
float3 fillOrBar = lerp(withHalftone, withHalftone * fillMask + AccentColor.rgb * barLead * 0.5, isBar);
float3 contentCol = lerp(BorderColor.rgb, fillOrBar, innerMask);
contentCol += AccentColor.rgb * sheenGlow * 0.7;

// Combine with Shadow
float3 finalRGB = lerp(ShadowColor.rgb, contentCol, cardMask);
float finalAlpha = saturate(cardMask * FillColor.a + shadowMask * ShadowOpacity * ShadowColor.a);

return float4(finalRGB, finalAlpha);
"""

HLSL_MSTONE = r"""
float2 dims = max(Dimensions, float2(16.0, 16.0));
float radius = clamp(CornerRadius, 0.0, min(dims.x, dims.y) * 0.5);

// SDF Shape
float2 p = (UV - 0.5) * dims;
float2 b = (dims * 0.5) - radius;
float2 q = abs(p) - b;
float dist = length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - radius;
float aa = max(fwidth(dist), 0.75);
float gemMask = 1.0 - smoothstep(-aa, aa, dist);

// Polar Facet Space
float2 cUV = UV - 0.5;
float angle = atan2(cUV.y, cUV.x);
float r = length(cUV) * 2.0;

// Chladni Cymatics & Geometric Facets
float fDens = max(FacetDensity, 4.0);
float facet = cos(angle * fDens) * sin(r * fDens * 1.5 + Time * 0.4);
float chladni = abs(sin(angle * 4.0) * cos(r * 8.0) - cos(angle * 4.0) * sin(r * 8.0));
float cymatics = smoothstep(0.04, 0.22, chladni);

// Prismatic Dispersion (Chromatic Aberration along facets)
float disp = clamp(DispersionSpread, 0.0, 0.2);
float rF = cos(angle * fDens - disp * 4.0);
float gF = cos(angle * fDens);
float bF = cos(angle * fDens + disp * 4.0);
float3 spectralDisp = float3(rF, gF, bF) * 0.5 + 0.5;

// Beer-Lambert Volumetric Absorption Gradient
float depth = 1.0 - saturate(r);
float3 absorption = exp(-depth * 2.2 * (1.0 - DeepJewelColor.rgb));
float3 jewelBody = lerp(DeepJewelColor.rgb * absorption, HighlightJewelColor.rgb, pow(saturate(r), 1.6));
jewelBody = lerp(jewelBody, jewelBody * spectralDisp, 0.45);
jewelBody += HighlightJewelColor.rgb * cymatics * 0.25 * (1.0 + ResonancePulse * 0.5);

// Specular Twinkle Glints
float gScale = max(GlintScale, 4.0);
float2 gUV = frac((UV + float2(sin(Time * 0.9), cos(Time * 0.7)) * 0.04) * gScale) - 0.5;
float glintStar = max(exp(-abs(gUV.x) * 35.0) * exp(-abs(gUV.y) * 4.0), exp(-abs(gUV.y) * 35.0) * exp(-abs(gUV.x) * 4.0));
float twinkle = saturate(sin(Time * 3.5 + UV.x * 24.0 + UV.y * 32.0));
float3 glintRGB = float3(1.0, 1.0, 1.0) * glintStar * twinkle * GlintIntensity;

// Metallic Gilded Bezel Frame
float bWidth = max(BezelWidth, 1.0);
float bezelDist = abs(dist + bWidth * 0.5) - bWidth * 0.5;
float bezelMask = (1.0 - smoothstep(-aa, aa, bezelDist)) * gemMask;
float innerGemMask = (1.0 - smoothstep(-aa, aa, dist + bWidth)) * gemMask;
float bezelSheen = saturate(cos(angle * 2.0 + Time * 0.8) * 0.5 + 0.5);
float3 bezelRGB = BezelColor.rgb * (0.8 + bezelSheen * 0.4);

// Final Composite
float3 finalRGB = lerp(bezelRGB, jewelBody + glintRGB, innerGemMask);
float finalAlpha = gemMask * DeepJewelColor.a;

return float4(finalRGB, finalAlpha);
"""

HLSL_NIKKI = r"""
float2 dims = max(Dimensions, float2(16.0, 16.0));
float radius = clamp(CornerRadius, 0.0, min(dims.x, dims.y) * 0.5);

// SDF Card & Sticker
float2 p = (UV - 0.5) * dims;
float2 b = (dims * 0.5) - radius;
float2 q = abs(p) - b;
float dist = length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - radius;
float aa = max(fwidth(dist), 0.75);

// Sticker Outer Edge & Card Inner
float sWidth = max(StickerEdgeWidth, 1.0);
float cardMask = 1.0 - smoothstep(-aa, aa, dist);
float stickerMask = 1.0 - smoothstep(-aa, aa, dist - sWidth);
float whiteStickerEdge = saturate(stickerMask - cardMask);

// Dual-tone Pastel Watercolor Gradient
float gradT = UV.x * 0.6 + UV.y * 0.4;
float bleed = (sin(UV.x * 25.0) * cos(UV.y * 20.0)) * 0.03 * WatercolorBleed;
float3 pastelWash = lerp(PastelColorA.rgb, PastelColorB.rgb, smoothstep(0.1, 0.9, gradT + bleed));

// Iridescent Shimmer Loop & Mother-of-Pearl Sheen
float iriAngle = dot(UV - 0.5, float2(cos(Time * 0.6 + IridescentPhase * 6.28), sin(Time * 0.6 + IridescentPhase * 6.28)));
float3 iriSpectrum = 0.5 + 0.5 * cos(iriAngle * 7.0 + float3(0.0, 2.094, 4.188));
float3 cardSurface = lerp(IvoryBaseColor.rgb, pastelWash, 0.45);
cardSurface = lerp(cardSurface, iriSpectrum, PearlSheenIntensity * 0.32);

// 4-Point & 8-Point Stardust Sparkles
float sDens = max(SparkleDensity, 2.0);
float2 sGrid = frac(UV * sDens) - 0.5;
float spStar = max(exp(-abs(sGrid.x) * 30.0) * exp(-abs(sGrid.y) * 4.0), exp(-abs(sGrid.y) * 30.0) * exp(-abs(sGrid.x) * 4.0));
float spTwinkle = saturate(sin(Time * SparkleTwinkleSpeed + UV.x * 35.0 + UV.y * 45.0));
float3 sparkleRGB = float3(1.0, 0.95, 0.85) * spStar * spTwinkle * 1.5;

// Gold Trim Filigree Rim
float trimDist = abs(dist + 1.0) - 1.0;
float trimMask = (1.0 - smoothstep(-aa, aa, trimDist)) * cardMask;
cardSurface = lerp(cardSurface, GoldTrimColor.rgb, trimMask * 0.85);

// Add Sparkle & Breathe Modulation
cardSurface += sparkleRGB;
float breathe = 1.0 + IdleBreathe * sin(Time * 2.094) * 0.05; // 3.0s loop
cardSurface *= breathe;

// Final Color & Alpha (White sticker border + Card surface)
float3 finalRGB = lerp(float3(1.0, 1.0, 1.0), cardSurface, cardMask);
float finalAlpha = stickerMask * IvoryBaseColor.a;

return float4(finalRGB, finalAlpha);
"""

HLSL_RADIAL_RING = r"""
float2 cUV = UV - 0.5;
float r = length(cUV) * 2.0;
float angle = atan2(cUV.y, cUV.x);

float innerR = clamp(InnerRadiusNormalized, 0.01, 0.98);
float outerR = clamp(OuterRadiusNormalized, innerR + 0.01, 1.0);
float feather = max(Feather, 0.005);

// Ring Band Mask
float ringMask = smoothstep(innerR - feather, innerR, r) * (1.0 - smoothstep(outerR, outerR + feather, r));

// Dash Pattern
float dCount = max(DashCount, 0.0);
float isDashed = step(0.5, dCount);
float normAngle = frac((angle / 6.2831853) + Time * OrbitSpeed);
float dashCell = frac(normAngle * max(dCount, 1.0));
float dashMask = 1.0 - step(clamp(DashRatio, 0.1, 0.9), dashCell);
float finalPattern = lerp(ringMask, ringMask * dashMask, isDashed);

float3 col = lerp(RingColor.rgb, DashGlowColor.rgb, isDashed * 0.3);
float alpha = finalPattern * RingColor.a;

return float4(col, alpha);
"""

HLSL_ORRERY_DISC = r"""
float2 cUV = UV - 0.5;
float r = length(cUV) * 2.0;
float angle = atan2(cUV.y, cUV.x);

float aa = max(fwidth(r), 0.005);

// Core Disc
float coreMask = 1.0 - smoothstep(CoreRadius - aa, CoreRadius + aa, r);

// Inner Dashed Ring
float innerBand = smoothstep(InnerRadius - 0.03, InnerRadius, r) * (1.0 - smoothstep(InnerRadius, InnerRadius + 0.03, r));
float normAngle = frac((angle / 6.2831853) + OrbitRotation + Time * 0.02);
float dashCell = frac(normAngle * max(InnerDashCount, 1.0));
float innerDash = step(0.5, dashCell);
float innerRingMask = innerBand * innerDash;

// Outer Solid Ring
float outerBand = smoothstep(OuterRadius - 0.04, OuterRadius, r) * (1.0 - smoothstep(OuterRadius, OuterRadius + 0.04, r));

// Disc Stardust background
float stardust = frac(sin(dot(UV * 40.0, float2(12.9898, 78.233))) * 43758.5453);
float3 coreRGB = CoreDiscColor.rgb + GlowColor.rgb * (stardust * 0.15);

// Composite
float3 finalRGB = coreRGB * coreMask + InnerRingColor.rgb * innerRingMask + OuterRingColor.rgb * outerBand;
float finalAlpha = saturate(coreMask * CoreDiscColor.a + innerRingMask * InnerRingColor.a + outerBand * OuterRingColor.a);

return float4(finalRGB, finalAlpha);
"""

# ==============================================================================
# MASTER MATERIAL BUILDER HELPERS
# ==============================================================================

def _get_or_create_material(name: str) -> unreal.Material:
    lib.ensure_directory(ROOT_FOLDER)
    path = f"{ROOT_FOLDER}/{name}"
    mat = unreal.EditorAssetLibrary.load_asset(path)
    if not mat:
        factory = unreal.MaterialFactoryNew()
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, ROOT_FOLDER, unreal.Material, factory)
    
    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_UI)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    return mat

def _setup_custom_node(mat: unreal.Material, hlsl_code: str, desc: str, input_names: list[str]) -> unreal.MaterialExpressionCustom:
    mel = unreal.MaterialEditingLibrary
    custom = lib.create_expression(mat, unreal.MaterialExpressionCustom, 200, 0)
    custom.set_editor_property("code", hlsl_code)
    custom.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT4)
    custom.set_editor_property("description", desc)
    
    inputs = []
    for name in input_names:
        inp = unreal.CustomInput()
        inp.set_editor_property("input_name", name)
        inputs.append(inp)
    custom.set_editor_property("inputs", inputs)
    return custom

def _mask_component(mat: unreal.Material, from_expr, r: bool, g: bool, b: bool, a: bool, x: int, y: int):
    mask = lib.create_expression(mat, unreal.MaterialExpressionComponentMask, x, y)
    mask.set_editor_property("r", r)
    mask.set_editor_property("g", g)
    mask.set_editor_property("b", b)
    mask.set_editor_property("a", a)
    lib.connect(from_expr, "", mask, "")
    return mask

def _wire_outputs(mat: unreal.Material, custom_node: unreal.MaterialExpressionCustom):
    mel = unreal.MaterialEditingLibrary
    rgb_mask = _mask_component(mat, custom_node, True, True, True, False, 500, -100)
    alpha_mask = _mask_component(mat, custom_node, False, False, False, True, 500, 100)
    mel.connect_material_property(rgb_mask, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.connect_material_property(alpha_mask, "", unreal.MaterialProperty.MP_OPACITY)

# ==============================================================================
# SPECIFIC MASTER BUILDERS
# ==============================================================================

def build_universal_toon_master() -> unreal.Material:
    name = "M_UI_UniversalToon_Master"
    mat = _get_or_create_material(name)
    lib.clear_material_graph(mat)
    
    input_names = [
        "UV", "Dimensions", "FillColor", "BorderColor", "ShadowColor", "AccentColor",
        "CornerRadius", "BorderThickness", "HalftoneScale", "HalftoneIntensity",
        "PaperGrainIntensity", "BeatPulse", "SheenSweep", "FillProgress",
        "IsProgressBar", "ShadowOpacity", "ShadowBlur", "ShadowOffset", "Time"
    ]
    custom = _setup_custom_node(mat, HLSL_UNIVERSAL_TOON, "UniversalToon_SDF_Core", input_names)
    
    # UV and Time
    uv_node = lib.create_expression(mat, unreal.MaterialExpressionTextureCoordinate, -400, -400)
    time_node = lib.create_expression(mat, unreal.MaterialExpressionTime, -400, 600)
    lib.connect(uv_node, "", custom, "UV")
    lib.connect(time_node, "", custom, "Time")
    
    # Vector parameters
    dims = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, -300)
    dims.set_editor_property("parameter_name", "Dimensions")
    dims.set_editor_property("default_value", unreal.LinearColor(300.0, 200.0, 0.0, 0.0))
    dims.set_editor_property("group", "Metrics")
    lib.connect(dims, "", custom, "Dimensions")
    
    fill = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, -200)
    fill.set_editor_property("parameter_name", "FillColor")
    fill.set_editor_property("default_value", unreal.LinearColor(0.988, 0.984, 0.973, 1.0)) # #FCFBF8 Ivory
    fill.set_editor_property("group", "Colors")
    lib.connect(fill, "", custom, "FillColor")
    
    border = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, -100)
    border.set_editor_property("parameter_name", "BorderColor")
    border.set_editor_property("default_value", unreal.LinearColor(0.867, 0.780, 0.608, 1.0)) # #DDC79B Gold 300
    border.set_editor_property("group", "Colors")
    lib.connect(border, "", custom, "BorderColor")
    
    shadow = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, 0)
    shadow.set_editor_property("parameter_name", "ShadowColor")
    shadow.set_editor_property("default_value", unreal.LinearColor(0.141, 0.106, 0.180, 0.25)) # #241B2E Shadow
    shadow.set_editor_property("group", "Colors")
    lib.connect(shadow, "", custom, "ShadowColor")
    
    accent = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, 100)
    accent.set_editor_property("parameter_name", "AccentColor")
    accent.set_editor_property("default_value", unreal.LinearColor(0.949, 0.816, 0.545, 1.0)) # #F2D08B Gold Accent
    accent.set_editor_property("group", "Colors")
    lib.connect(accent, "", custom, "AccentColor")
    
    # Scalar parameters
    scalars = [
        ("CornerRadius", 14.0, "Metrics"),
        ("BorderThickness", 1.0, "Metrics"),
        ("HalftoneScale", 8.0, "Stylization"),
        ("HalftoneIntensity", 0.0, "Stylization"),
        ("PaperGrainIntensity", 0.35, "Stylization"),
        ("BeatPulse", 0.0, "Animation"),
        ("SheenSweep", 0.0, "Animation"),
        ("FillProgress", 1.0, "Progress"),
        ("IsProgressBar", 0.0, "Progress"),
        ("ShadowOpacity", 1.0, "Shadow"),
        ("ShadowBlur", 2.0, "Shadow"),
    ]
    y_offset = -300
    for pname, pval, pgrp in scalars:
        sp = lib.scalar_param(mat, pname, pgrp, pval, -200, y_offset)
        lib.connect(sp, "", custom, pname)
        y_offset += 80
        
    sh_offset = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -200, y_offset)
    sh_offset.set_editor_property("parameter_name", "ShadowOffset")
    sh_offset.set_editor_property("default_value", unreal.LinearColor(7.0, 8.0, 0.0, 0.0))
    sh_offset.set_editor_property("group", "Shadow")
    lib.connect(sh_offset, "", custom, "ShadowOffset")
    
    _wire_outputs(mat, custom)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    unreal.log(f"[UI Master] Created and saved {name}")
    return mat

def build_mstone_master() -> unreal.Material:
    name = "M_UI_Mstone_Master"
    mat = _get_or_create_material(name)
    lib.clear_material_graph(mat)
    
    input_names = [
        "UV", "Dimensions", "DeepJewelColor", "HighlightJewelColor", "BezelColor",
        "FacetDensity", "DispersionSpread", "GlintScale", "GlintIntensity",
        "ResonancePulse", "BezelWidth", "CornerRadius", "Time"
    ]
    custom = _setup_custom_node(mat, HLSL_MSTONE, "Mstone_Facet_Cymatics_Core", input_names)
    
    uv_node = lib.create_expression(mat, unreal.MaterialExpressionTextureCoordinate, -400, -300)
    time_node = lib.create_expression(mat, unreal.MaterialExpressionTime, -400, 400)
    lib.connect(uv_node, "", custom, "UV")
    lib.connect(time_node, "", custom, "Time")
    
    dims = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, -200)
    dims.set_editor_property("parameter_name", "Dimensions")
    dims.set_editor_property("default_value", unreal.LinearColor(128.0, 128.0, 0.0, 0.0))
    dims.set_editor_property("group", "Metrics")
    lib.connect(dims, "", custom, "Dimensions")
    
    deep = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, -100)
    deep.set_editor_property("parameter_name", "DeepJewelColor")
    deep.set_editor_property("default_value", unreal.LinearColor(0.08, 0.52, 0.78, 1.0)) # Aquamarine deep
    deep.set_editor_property("group", "Gemstone")
    lib.connect(deep, "", custom, "DeepJewelColor")
    
    high = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, 0)
    high.set_editor_property("parameter_name", "HighlightJewelColor")
    high.set_editor_property("default_value", unreal.LinearColor(0.525, 0.894, 1.0, 1.0)) # Pearl Aqua
    high.set_editor_property("group", "Gemstone")
    lib.connect(high, "", custom, "HighlightJewelColor")
    
    bezel = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, 100)
    bezel.set_editor_property("parameter_name", "BezelColor")
    bezel.set_editor_property("default_value", unreal.LinearColor(0.949, 0.816, 0.545, 1.0)) # Gold foil
    bezel.set_editor_property("group", "Gemstone")
    lib.connect(bezel, "", custom, "BezelColor")
    
    scalars = [
        ("FacetDensity", 8.0, "Gemstone"),
        ("DispersionSpread", 0.05, "Optics"),
        ("GlintScale", 16.0, "Optics"),
        ("GlintIntensity", 1.2, "Optics"),
        ("ResonancePulse", 0.0, "Harmonics"),
        ("BezelWidth", 3.0, "Metrics"),
        ("CornerRadius", 64.0, "Metrics"),
    ]
    y_offset = -200
    for pname, pval, pgrp in scalars:
        sp = lib.scalar_param(mat, pname, pgrp, pval, -200, y_offset)
        lib.connect(sp, "", custom, pname)
        y_offset += 80
        
    _wire_outputs(mat, custom)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    unreal.log(f"[UI Master] Created and saved {name}")
    return mat

def build_nikki_master() -> unreal.Material:
    name = "M_UI_Nikki_Master"
    mat = _get_or_create_material(name)
    lib.clear_material_graph(mat)
    
    input_names = [
        "UV", "Dimensions", "PastelColorA", "PastelColorB", "IvoryBaseColor",
        "GoldTrimColor", "CornerRadius", "StickerEdgeWidth", "IridescentPhase",
        "PearlSheenIntensity", "SparkleDensity", "SparkleTwinkleSpeed",
        "WatercolorBleed", "IdleBreathe", "Time"
    ]
    custom = _setup_custom_node(mat, HLSL_NIKKI, "Nikki_MagicalGirl_Core", input_names)
    
    uv_node = lib.create_expression(mat, unreal.MaterialExpressionTextureCoordinate, -400, -300)
    time_node = lib.create_expression(mat, unreal.MaterialExpressionTime, -400, 500)
    lib.connect(uv_node, "", custom, "UV")
    lib.connect(time_node, "", custom, "Time")
    
    dims = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, -200)
    dims.set_editor_property("parameter_name", "Dimensions")
    dims.set_editor_property("default_value", unreal.LinearColor(320.0, 180.0, 0.0, 0.0))
    dims.set_editor_property("group", "Metrics")
    lib.connect(dims, "", custom, "Dimensions")
    
    pastA = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, -100)
    pastA.set_editor_property("parameter_name", "PastelColorA")
    pastA.set_editor_property("default_value", unreal.LinearColor(1.0, 0.576, 0.71, 1.0)) # Rose #FF93B5
    pastA.set_editor_property("group", "Palette")
    lib.connect(pastA, "", custom, "PastelColorA")
    
    pastB = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, 0)
    pastB.set_editor_property("parameter_name", "PastelColorB")
    pastB.set_editor_property("default_value", unreal.LinearColor(0.525, 0.894, 1.0, 1.0)) # Pearl Aqua #86E4FF
    pastB.set_editor_property("group", "Palette")
    lib.connect(pastB, "", custom, "PastelColorB")
    
    ivory = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, 100)
    ivory.set_editor_property("parameter_name", "IvoryBaseColor")
    ivory.set_editor_property("default_value", unreal.LinearColor(0.988, 0.984, 0.973, 1.0)) # Ivory
    ivory.set_editor_property("group", "Palette")
    lib.connect(ivory, "", custom, "IvoryBaseColor")
    
    gold = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, 200)
    gold.set_editor_property("parameter_name", "GoldTrimColor")
    gold.set_editor_property("default_value", unreal.LinearColor(0.867, 0.780, 0.608, 1.0)) # Gold 300
    gold.set_editor_property("group", "Palette")
    lib.connect(gold, "", custom, "GoldTrimColor")
    
    scalars = [
        ("CornerRadius", 16.0, "Metrics"),
        ("StickerEdgeWidth", 2.0, "Metrics"),
        ("IridescentPhase", 0.0, "Stylization"),
        ("PearlSheenIntensity", 0.65, "Stylization"),
        ("SparkleDensity", 6.0, "Sparkles"),
        ("SparkleTwinkleSpeed", 2.5, "Sparkles"),
        ("WatercolorBleed", 0.4, "Stylization"),
        ("IdleBreathe", 0.5, "Animation"),
    ]
    y_offset = -200
    for pname, pval, pgrp in scalars:
        sp = lib.scalar_param(mat, pname, pgrp, pval, -200, y_offset)
        lib.connect(sp, "", custom, pname)
        y_offset += 80
        
    _wire_outputs(mat, custom)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    unreal.log(f"[UI Master] Created and saved {name}")
    return mat

def build_radial_ring_master() -> unreal.Material:
    name = "M_UI_Storybook_RadialRing"
    mat = _get_or_create_material(name)
    lib.clear_material_graph(mat)
    
    input_names = [
        "UV", "Dimensions", "RingColor", "DashGlowColor",
        "InnerRadiusNormalized", "OuterRadiusNormalized", "DashCount",
        "DashRatio", "OrbitSpeed", "Feather", "Time"
    ]
    custom = _setup_custom_node(mat, HLSL_RADIAL_RING, "RadialRing_Polar_Core", input_names)
    
    uv_node = lib.create_expression(mat, unreal.MaterialExpressionTextureCoordinate, -400, -300)
    time_node = lib.create_expression(mat, unreal.MaterialExpressionTime, -400, 300)
    lib.connect(uv_node, "", custom, "UV")
    lib.connect(time_node, "", custom, "Time")
    
    dims = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, -200)
    dims.set_editor_property("parameter_name", "Dimensions")
    dims.set_editor_property("default_value", unreal.LinearColor(512.0, 512.0, 0.0, 0.0))
    dims.set_editor_property("group", "Metrics")
    lib.connect(dims, "", custom, "Dimensions")
    
    ringCol = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, -100)
    ringCol.set_editor_property("parameter_name", "RingColor")
    ringCol.set_editor_property("default_value", unreal.LinearColor(0.953, 0.902, 0.784, 1.0)) # #F3E6C8 Gold 200
    ringCol.set_editor_property("group", "Colors")
    lib.connect(ringCol, "", custom, "RingColor")
    
    glowCol = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, 0)
    glowCol.set_editor_property("parameter_name", "DashGlowColor")
    glowCol.set_editor_property("default_value", unreal.LinearColor(0.867, 0.780, 0.608, 1.0)) # Gold 300
    glowCol.set_editor_property("group", "Colors")
    lib.connect(glowCol, "", custom, "DashGlowColor")
    
    scalars = [
        ("InnerRadiusNormalized", 0.75, "Geometry"),
        ("OuterRadiusNormalized", 0.85, "Geometry"),
        ("DashCount", 0.0, "Dashes"),
        ("DashRatio", 0.5, "Dashes"),
        ("OrbitSpeed", 0.0, "Animation"),
        ("Feather", 0.01, "Geometry"),
    ]
    y_offset = -150
    for pname, pval, pgrp in scalars:
        sp = lib.scalar_param(mat, pname, pgrp, pval, -200, y_offset)
        lib.connect(sp, "", custom, pname)
        y_offset += 80
        
    _wire_outputs(mat, custom)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    unreal.log(f"[UI Master] Created and saved {name}")
    return mat

def build_orrery_disc_master() -> unreal.Material:
    name = "M_UI_Storybook_OrreryDisc"
    mat = _get_or_create_material(name)
    lib.clear_material_graph(mat)
    
    input_names = [
        "UV", "Dimensions", "OuterRingColor", "InnerRingColor", "CoreDiscColor",
        "GlowColor", "OuterRadius", "InnerRadius", "CoreRadius",
        "InnerDashCount", "OrbitRotation", "Time"
    ]
    custom = _setup_custom_node(mat, HLSL_ORRERY_DISC, "OrreryDisc_Frame_Core", input_names)
    
    uv_node = lib.create_expression(mat, unreal.MaterialExpressionTextureCoordinate, -400, -300)
    time_node = lib.create_expression(mat, unreal.MaterialExpressionTime, -400, 400)
    lib.connect(uv_node, "", custom, "UV")
    lib.connect(time_node, "", custom, "Time")
    
    dims = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, -200)
    dims.set_editor_property("parameter_name", "Dimensions")
    dims.set_editor_property("default_value", unreal.LinearColor(256.0, 256.0, 0.0, 0.0))
    dims.set_editor_property("group", "Metrics")
    lib.connect(dims, "", custom, "Dimensions")
    
    outerCol = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, -100)
    outerCol.set_editor_property("parameter_name", "OuterRingColor")
    outerCol.set_editor_property("default_value", unreal.LinearColor(0.953, 0.902, 0.784, 1.0))
    outerCol.set_editor_property("group", "Colors")
    lib.connect(outerCol, "", custom, "OuterRingColor")
    
    innerCol = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, 0)
    innerCol.set_editor_property("parameter_name", "InnerRingColor")
    innerCol.set_editor_property("default_value", unreal.LinearColor(0.867, 0.780, 0.608, 1.0))
    innerCol.set_editor_property("group", "Colors")
    lib.connect(innerCol, "", custom, "InnerRingColor")
    
    coreCol = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, 100)
    coreCol.set_editor_property("parameter_name", "CoreDiscColor")
    coreCol.set_editor_property("default_value", unreal.LinearColor(0.165, 0.086, 0.275, 0.95)) # Plum #2A1646
    coreCol.set_editor_property("group", "Colors")
    lib.connect(coreCol, "", custom, "CoreDiscColor")
    
    glowCol = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, 200)
    glowCol.set_editor_property("parameter_name", "GlowColor")
    glowCol.set_editor_property("default_value", unreal.LinearColor(0.949, 0.816, 0.545, 1.0))
    glowCol.set_editor_property("group", "Colors")
    lib.connect(glowCol, "", custom, "GlowColor")
    
    scalars = [
        ("OuterRadius", 0.92, "Geometry"),
        ("InnerRadius", 0.72, "Geometry"),
        ("CoreRadius", 0.65, "Geometry"),
        ("InnerDashCount", 24.0, "Dashes"),
        ("OrbitRotation", 0.0, "Animation"),
    ]
    y_offset = -150
    for pname, pval, pgrp in scalars:
        sp = lib.scalar_param(mat, pname, pgrp, pval, -200, y_offset)
        lib.connect(sp, "", custom, pname)
        y_offset += 80
        
    _wire_outputs(mat, custom)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    unreal.log(f"[UI Master] Created and saved {name}")
    return mat

# ==============================================================================
# STUB OVERHAULS
# ==============================================================================

def overhaul_nikki_storybook_card():
    """Upgrade M_UI_Nikki_StorybookCard into full Nikki Master graph with complete styling."""
    name = "M_UI_Nikki_StorybookCard"
    mat = _get_or_create_material(name)
    lib.clear_material_graph(mat)
    
    input_names = [
        "UV", "Dimensions", "PastelColorA", "PastelColorB", "IvoryBaseColor",
        "GoldTrimColor", "CornerRadius", "StickerEdgeWidth", "IridescentPhase",
        "PearlSheenIntensity", "SparkleDensity", "SparkleTwinkleSpeed",
        "WatercolorBleed", "IdleBreathe", "Time"
    ]
    custom = _setup_custom_node(mat, HLSL_NIKKI, "Nikki_Card_Overhauled_Core", input_names)
    
    uv_node = lib.create_expression(mat, unreal.MaterialExpressionTextureCoordinate, -400, -300)
    time_node = lib.create_expression(mat, unreal.MaterialExpressionTime, -400, 500)
    lib.connect(uv_node, "", custom, "UV")
    lib.connect(time_node, "", custom, "Time")
    
    dims = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, -200)
    dims.set_editor_property("parameter_name", "Dimensions")
    dims.set_editor_property("default_value", unreal.LinearColor(340.0, 160.0, 0.0, 0.0))
    dims.set_editor_property("group", "Metrics")
    lib.connect(dims, "", custom, "Dimensions")
    
    pastA = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, -100)
    pastA.set_editor_property("parameter_name", "PastelColorA")
    pastA.set_editor_property("default_value", unreal.LinearColor(1.0, 0.576, 0.71, 1.0))
    pastA.set_editor_property("group", "Palette")
    lib.connect(pastA, "", custom, "PastelColorA")
    
    pastB = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, 0)
    pastB.set_editor_property("parameter_name", "PastelColorB")
    pastB.set_editor_property("default_value", unreal.LinearColor(0.525, 0.894, 1.0, 1.0))
    pastB.set_editor_property("group", "Palette")
    lib.connect(pastB, "", custom, "PastelColorB")
    
    ivory = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, 100)
    ivory.set_editor_property("parameter_name", "IvoryBaseColor")
    ivory.set_editor_property("default_value", unreal.LinearColor(0.988, 0.984, 0.973, 1.0))
    ivory.set_editor_property("group", "Palette")
    lib.connect(ivory, "", custom, "IvoryBaseColor")
    
    gold = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, 200)
    gold.set_editor_property("parameter_name", "GoldTrimColor")
    gold.set_editor_property("default_value", unreal.LinearColor(0.867, 0.780, 0.608, 1.0))
    gold.set_editor_property("group", "Palette")
    lib.connect(gold, "", custom, "GoldTrimColor")
    
    scalars = [
        ("CornerRadius", 14.0, "Metrics"),
        ("StickerEdgeWidth", 2.0, "Metrics"),
        ("IridescentPhase", 0.0, "Stylization"),
        ("PearlSheenIntensity", 0.5, "Stylization"),
        ("SparkleDensity", 5.0, "Sparkles"),
        ("SparkleTwinkleSpeed", 2.0, "Sparkles"),
        ("WatercolorBleed", 0.3, "Stylization"),
        ("IdleBreathe", 0.4, "Animation"),
    ]
    y_offset = -200
    for pname, pval, pgrp in scalars:
        sp = lib.scalar_param(mat, pname, pgrp, pval, -200, y_offset)
        lib.connect(sp, "", custom, pname)
        y_offset += 80
        
    _wire_outputs(mat, custom)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    unreal.log(f"[UI Stub Overhaul] Overhauled and saved {name}")
    return mat

def overhaul_nikki_vitals_meter():
    """Upgrade M_UI_Nikki_VitalsMeter into full Toon/Nikki progress bar meter graph."""
    name = "M_UI_Nikki_VitalsMeter"
    mat = _get_or_create_material(name)
    lib.clear_material_graph(mat)
    
    input_names = [
        "UV", "Dimensions", "FillColor", "BorderColor", "ShadowColor", "AccentColor",
        "CornerRadius", "BorderThickness", "HalftoneScale", "HalftoneIntensity",
        "PaperGrainIntensity", "BeatPulse", "SheenSweep", "FillProgress",
        "IsProgressBar", "ShadowOpacity", "ShadowBlur", "ShadowOffset", "Time"
    ]
    custom = _setup_custom_node(mat, HLSL_UNIVERSAL_TOON, "Nikki_Vitals_Meter_Core", input_names)
    
    uv_node = lib.create_expression(mat, unreal.MaterialExpressionTextureCoordinate, -400, -400)
    time_node = lib.create_expression(mat, unreal.MaterialExpressionTime, -400, 600)
    lib.connect(uv_node, "", custom, "UV")
    lib.connect(time_node, "", custom, "Time")
    
    dims = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, -300)
    dims.set_editor_property("parameter_name", "Dimensions")
    dims.set_editor_property("default_value", unreal.LinearColor(240.0, 18.0, 0.0, 0.0))
    dims.set_editor_property("group", "Metrics")
    lib.connect(dims, "", custom, "Dimensions")
    
    fill = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, -200)
    fill.set_editor_property("parameter_name", "FillColor")
    fill.set_editor_property("default_value", unreal.LinearColor(1.0, 0.576, 0.71, 1.0)) # Rose #FF93B5
    fill.set_editor_property("group", "Colors")
    lib.connect(fill, "", custom, "FillColor")
    
    border = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, -100)
    border.set_editor_property("parameter_name", "BorderColor")
    border.set_editor_property("default_value", unreal.LinearColor(0.867, 0.780, 0.608, 1.0))
    border.set_editor_property("group", "Colors")
    lib.connect(border, "", custom, "BorderColor")
    
    shadow = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, 0)
    shadow.set_editor_property("parameter_name", "ShadowColor")
    shadow.set_editor_property("default_value", unreal.LinearColor(0.141, 0.106, 0.180, 0.3))
    shadow.set_editor_property("group", "Colors")
    lib.connect(shadow, "", custom, "ShadowColor")
    
    accent = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, 100)
    accent.set_editor_property("parameter_name", "AccentColor")
    accent.set_editor_property("default_value", unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
    accent.set_editor_property("group", "Colors")
    lib.connect(accent, "", custom, "AccentColor")
    
    scalars = [
        ("CornerRadius", 3.0, "Metrics"),
        ("BorderThickness", 1.0, "Metrics"),
        ("HalftoneScale", 12.0, "Stylization"),
        ("HalftoneIntensity", 0.2, "Stylization"),
        ("PaperGrainIntensity", 0.1, "Stylization"),
        ("BeatPulse", 0.0, "Animation"),
        ("SheenSweep", 0.0, "Animation"),
        ("FillProgress", 1.0, "Progress"),
        ("IsProgressBar", 1.0, "Progress"),
        ("ShadowOpacity", 0.5, "Shadow"),
        ("ShadowBlur", 1.0, "Shadow"),
    ]
    y_offset = -300
    for pname, pval, pgrp in scalars:
        sp = lib.scalar_param(mat, pname, pgrp, pval, -200, y_offset)
        lib.connect(sp, "", custom, pname)
        y_offset += 80
        
    sh_offset = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -200, y_offset)
    sh_offset.set_editor_property("parameter_name", "ShadowOffset")
    sh_offset.set_editor_property("default_value", unreal.LinearColor(0.0, 2.0, 0.0, 0.0))
    sh_offset.set_editor_property("group", "Shadow")
    lib.connect(sh_offset, "", custom, "ShadowOffset")
    
    _wire_outputs(mat, custom)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    unreal.log(f"[UI Stub Overhaul] Overhauled and saved {name}")
    return mat

def overhaul_audio_glow_border():
    """Upgrade M_UI_AudioGlow_Border into audio-reactive border glow graph."""
    name = "M_UI_AudioGlow_Border"
    mat = _get_or_create_material(name)
    lib.clear_material_graph(mat)
    
    input_names = [
        "UV", "Dimensions", "FillColor", "BorderColor", "ShadowColor", "AccentColor",
        "CornerRadius", "BorderThickness", "HalftoneScale", "HalftoneIntensity",
        "PaperGrainIntensity", "BeatPulse", "SheenSweep", "FillProgress",
        "IsProgressBar", "ShadowOpacity", "ShadowBlur", "ShadowOffset", "Time"
    ]
    custom = _setup_custom_node(mat, HLSL_UNIVERSAL_TOON, "AudioGlow_Border_Core", input_names)
    
    uv_node = lib.create_expression(mat, unreal.MaterialExpressionTextureCoordinate, -400, -400)
    time_node = lib.create_expression(mat, unreal.MaterialExpressionTime, -400, 600)
    lib.connect(uv_node, "", custom, "UV")
    lib.connect(time_node, "", custom, "Time")
    
    dims = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, -300)
    dims.set_editor_property("parameter_name", "Dimensions")
    dims.set_editor_property("default_value", unreal.LinearColor(256.0, 256.0, 0.0, 0.0))
    dims.set_editor_property("group", "Metrics")
    lib.connect(dims, "", custom, "Dimensions")
    
    fill = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, -200)
    fill.set_editor_property("parameter_name", "FillColor")
    fill.set_editor_property("default_value", unreal.LinearColor(0.165, 0.086, 0.275, 0.0)) # Clear/transparent center
    fill.set_editor_property("group", "Colors")
    lib.connect(fill, "", custom, "FillColor")
    
    border = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, -100)
    border.set_editor_property("parameter_name", "BorderColor")
    border.set_editor_property("default_value", unreal.LinearColor(0.949, 0.816, 0.545, 1.0)) # Gold glow
    border.set_editor_property("group", "Colors")
    lib.connect(border, "", custom, "BorderColor")
    
    shadow = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, 0)
    shadow.set_editor_property("parameter_name", "ShadowColor")
    shadow.set_editor_property("default_value", unreal.LinearColor(0.949, 0.816, 0.545, 0.5))
    shadow.set_editor_property("group", "Colors")
    lib.connect(shadow, "", custom, "ShadowColor")
    
    accent = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -400, 100)
    accent.set_editor_property("parameter_name", "AccentColor")
    accent.set_editor_property("default_value", unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
    accent.set_editor_property("group", "Colors")
    lib.connect(accent, "", custom, "AccentColor")
    
    scalars = [
        ("CornerRadius", 16.0, "Metrics"),
        ("BorderThickness", 2.0, "Metrics"),
        ("HalftoneScale", 8.0, "Stylization"),
        ("HalftoneIntensity", 0.0, "Stylization"),
        ("PaperGrainIntensity", 0.0, "Stylization"),
        ("BeatPulse", 0.5, "Animation"),
        ("SheenSweep", 0.0, "Animation"),
        ("FillProgress", 1.0, "Progress"),
        ("IsProgressBar", 0.0, "Progress"),
        ("ShadowOpacity", 0.8, "Shadow"),
        ("ShadowBlur", 8.0, "Shadow"),
    ]
    y_offset = -300
    for pname, pval, pgrp in scalars:
        sp = lib.scalar_param(mat, pname, pgrp, pval, -200, y_offset)
        lib.connect(sp, "", custom, pname)
        y_offset += 80
        
    sh_offset = lib.create_expression(mat, unreal.MaterialExpressionVectorParameter, -200, y_offset)
    sh_offset.set_editor_property("parameter_name", "ShadowOffset")
    sh_offset.set_editor_property("default_value", unreal.LinearColor(0.0, 0.0, 0.0, 0.0))
    sh_offset.set_editor_property("group", "Shadow")
    lib.connect(sh_offset, "", custom, "ShadowOffset")
    
    _wire_outputs(mat, custom)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    unreal.log(f"[UI Stub Overhaul] Overhauled and saved {name}")
    return mat

# ==============================================================================
# MATERIAL INSTANCE BUILDER
# ==============================================================================

def create_instance(name: str, parent_material: unreal.Material, scalar_overrides: dict[str, float] = None, vector_overrides: dict[str, unreal.LinearColor] = None) -> unreal.MaterialInstanceConstant:
    path = f"{ROOT_FOLDER}/{name}"
    mi = unreal.EditorAssetLibrary.load_asset(path)
    if not mi:
        factory = unreal.MaterialInstanceConstantFactoryNew()
        mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, ROOT_FOLDER, unreal.MaterialInstanceConstant, factory)
        
    unreal.MaterialEditingLibrary.set_material_instance_parent(mi, parent_material)
    
    if scalar_overrides:
        for k, v in scalar_overrides.items():
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, k, float(v))
            
    if vector_overrides:
        for k, v in vector_overrides.items():
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, k, v)
            
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    unreal.log(f"[UI Instance] Created/Updated {name}")
    return mi

def build_all_instances(masters: dict[str, unreal.Material]):
    toon = masters["M_UI_UniversalToon_Master"]
    mstone = masters["M_UI_Mstone_Master"]
    nikki = masters["M_UI_Nikki_Master"]
    ring = masters["M_UI_Storybook_RadialRing"]
    disc = masters["M_UI_Storybook_OrreryDisc"]
    
    instances = []
    
    # 1. Toon Instances
    instances.append(create_instance(
        "MI_UI_Toon_Card_Parchment", toon,
        scalar_overrides={"CornerRadius": 14.0, "BorderThickness": 1.0, "HalftoneIntensity": 0.0, "PaperGrainIntensity": 0.4},
        vector_overrides={
            "FillColor": unreal.LinearColor(0.988, 0.984, 0.973, 1.0), # #FCFBF8
            "BorderColor": unreal.LinearColor(0.867, 0.780, 0.608, 1.0), # #DDC79B
            "ShadowColor": unreal.LinearColor(0.141, 0.106, 0.180, 0.25) # #241B2E
        }
    ))
    
    instances.append(create_instance(
        "MI_UI_Toon_Card_Plum", toon,
        scalar_overrides={"CornerRadius": 10.0, "BorderThickness": 2.0, "HalftoneIntensity": 0.15, "PaperGrainIntensity": 0.2},
        vector_overrides={
            "FillColor": unreal.LinearColor(0.165, 0.086, 0.275, 1.0), # #2A1646
            "BorderColor": unreal.LinearColor(0.949, 0.816, 0.545, 1.0), # #F2D08B
            "ShadowColor": unreal.LinearColor(0.141, 0.106, 0.180, 0.35)
        }
    ))
    
    instances.append(create_instance(
        "MI_UI_Toon_Button_Primary", toon,
        scalar_overrides={"CornerRadius": 10.0, "BorderThickness": 1.0, "SheenSweep": 0.0, "PaperGrainIntensity": 0.2},
        vector_overrides={
            "FillColor": unreal.LinearColor(0.988, 0.984, 0.973, 1.0),
            "BorderColor": unreal.LinearColor(0.867, 0.780, 0.608, 1.0),
            "AccentColor": unreal.LinearColor(0.949, 0.816, 0.545, 1.0)
        }
    ))
    
    instances.append(create_instance(
        "MI_UI_Toon_Progress_Gold", toon,
        scalar_overrides={"CornerRadius": 4.0, "BorderThickness": 1.0, "IsProgressBar": 1.0, "FillProgress": 0.75},
        vector_overrides={
            "FillColor": unreal.LinearColor(0.949, 0.816, 0.545, 1.0),
            "BorderColor": unreal.LinearColor(0.867, 0.780, 0.608, 1.0)
        }
    ))
    
    # 2. Mstone Instances
    instances.append(create_instance(
        "MI_UI_Mstone_Diamond_Reticle", mstone,
        scalar_overrides={"FacetDensity": 8.0, "DispersionSpread": 0.06, "GlintIntensity": 1.5, "BezelWidth": 2.5, "CornerRadius": 64.0},
        vector_overrides={
            "DeepJewelColor": unreal.LinearColor(0.85, 0.92, 1.0, 1.0),
            "HighlightJewelColor": unreal.LinearColor(1.0, 1.0, 1.0, 1.0),
            "BezelColor": unreal.LinearColor(0.95, 0.95, 1.0, 1.0)
        }
    ))
    
    instances.append(create_instance(
        "MI_UI_Mstone_Aquamarine_Crest", mstone,
        scalar_overrides={"FacetDensity": 6.0, "DispersionSpread": 0.04, "GlintIntensity": 1.2, "BezelWidth": 3.0, "CornerRadius": 64.0},
        vector_overrides={
            "DeepJewelColor": unreal.LinearColor(0.08, 0.52, 0.78, 1.0),
            "HighlightJewelColor": unreal.LinearColor(0.525, 0.894, 1.0, 1.0),
            "BezelColor": unreal.LinearColor(0.949, 0.816, 0.545, 1.0)
        }
    ))
    
    instances.append(create_instance(
        "MI_UI_Mstone_RosyQuartz_Vitals", mstone,
        scalar_overrides={"FacetDensity": 10.0, "DispersionSpread": 0.03, "GlintIntensity": 1.0, "BezelWidth": 2.0, "CornerRadius": 64.0},
        vector_overrides={
            "DeepJewelColor": unreal.LinearColor(0.88, 0.35, 0.52, 1.0),
            "HighlightJewelColor": unreal.LinearColor(1.0, 0.576, 0.71, 1.0), # Rose #FF93B5
            "BezelColor": unreal.LinearColor(0.949, 0.816, 0.545, 1.0)
        }
    ))
    
    instances.append(create_instance(
        "MI_UI_Mstone_VoidOrchid_Accent", mstone,
        scalar_overrides={"FacetDensity": 12.0, "DispersionSpread": 0.08, "GlintIntensity": 1.8, "BezelWidth": 3.5, "CornerRadius": 64.0},
        vector_overrides={
            "DeepJewelColor": unreal.LinearColor(0.18, 0.05, 0.32, 1.0),
            "HighlightJewelColor": unreal.LinearColor(0.75, 0.35, 0.95, 1.0),
            "BezelColor": unreal.LinearColor(0.949, 0.816, 0.545, 1.0)
        }
    ))
    
    # 3. Nikki Instances
    instances.append(create_instance(
        "MI_UI_Nikki_Card_Ivory", nikki,
        scalar_overrides={"CornerRadius": 14.0, "StickerEdgeWidth": 2.0, "PearlSheenIntensity": 0.6},
        vector_overrides={
            "PastelColorA": unreal.LinearColor(1.0, 0.576, 0.71, 1.0),
            "PastelColorB": unreal.LinearColor(0.525, 0.894, 1.0, 1.0),
            "IvoryBaseColor": unreal.LinearColor(0.988, 0.984, 0.973, 1.0)
        }
    ))
    
    instances.append(create_instance(
        "MI_UI_Nikki_Card_Sakura", nikki,
        scalar_overrides={"CornerRadius": 14.0, "StickerEdgeWidth": 2.0, "PearlSheenIntensity": 0.5},
        vector_overrides={
            "PastelColorA": unreal.LinearColor(0.906, 0.788, 0.808, 1.0), # #E7C9CE
            "PastelColorB": unreal.LinearColor(1.0, 0.576, 0.71, 1.0),
            "IvoryBaseColor": unreal.LinearColor(0.906, 0.788, 0.808, 1.0)
        }
    ))
    
    instances.append(create_instance(
        "MI_UI_Nikki_Card_Lavender", nikki,
        scalar_overrides={"CornerRadius": 14.0, "StickerEdgeWidth": 2.0, "PearlSheenIntensity": 0.55},
        vector_overrides={
            "PastelColorA": unreal.LinearColor(0.941, 0.863, 0.941, 1.0), # #F0DCF0
            "PastelColorB": unreal.LinearColor(0.525, 0.894, 1.0, 1.0),
            "IvoryBaseColor": unreal.LinearColor(0.941, 0.863, 0.941, 1.0)
        }
    ))
    
    instances.append(create_instance(
        "MI_UI_Nikki_Card_Plum", nikki,
        scalar_overrides={"CornerRadius": 10.0, "StickerEdgeWidth": 2.0, "PearlSheenIntensity": 0.4},
        vector_overrides={
            "PastelColorA": unreal.LinearColor(0.165, 0.086, 0.275, 1.0), # #2A1646
            "PastelColorB": unreal.LinearColor(0.396, 0.275, 0.494, 1.0), # #65467E
            "IvoryBaseColor": unreal.LinearColor(0.165, 0.086, 0.275, 1.0)
        }
    ))
    
    instances.append(create_instance(
        "MI_UI_Nikki_VitalityBar", toon,
        scalar_overrides={"CornerRadius": 3.0, "BorderThickness": 1.0, "IsProgressBar": 1.0, "FillProgress": 1.0},
        vector_overrides={
            "FillColor": unreal.LinearColor(1.0, 0.576, 0.71, 1.0), # Rose #FF93B5
            "BorderColor": unreal.LinearColor(0.867, 0.780, 0.608, 1.0)
        }
    ))
    
    instances.append(create_instance(
        "MI_UI_Nikki_ResonanceBar", toon,
        scalar_overrides={"CornerRadius": 3.0, "BorderThickness": 1.0, "IsProgressBar": 1.0, "FillProgress": 1.0},
        vector_overrides={
            "FillColor": unreal.LinearColor(0.525, 0.894, 1.0, 1.0), # Pearl Aqua #86E4FF
            "BorderColor": unreal.LinearColor(0.867, 0.780, 0.608, 1.0)
        }
    ))
    
    instances.append(create_instance(
        "MI_UI_Nikki_QuestMeter", toon,
        scalar_overrides={"CornerRadius": 4.0, "BorderThickness": 1.0, "IsProgressBar": 1.0, "FillProgress": 0.65},
        vector_overrides={
            "FillColor": unreal.LinearColor(0.949, 0.816, 0.545, 1.0), # Gold #F2D08B
            "BorderColor": unreal.LinearColor(0.867, 0.780, 0.608, 1.0)
        }
    ))
    
    # 4. Radial / Orrery Instances
    instances.append(create_instance(
        "MI_UI_Orrery_RingOuter", ring,
        scalar_overrides={"InnerRadiusNormalized": 0.85, "OuterRadiusNormalized": 0.90, "DashCount": 0.0},
        vector_overrides={"RingColor": unreal.LinearColor(0.953, 0.902, 0.784, 1.0)} # #F3E6C8
    ))
    
    instances.append(create_instance(
        "MI_UI_Orrery_RingMidDashed", ring,
        scalar_overrides={"InnerRadiusNormalized": 0.64, "OuterRadiusNormalized": 0.68, "DashCount": 36.0, "DashRatio": 0.55, "OrbitSpeed": 0.01},
        vector_overrides={
            "RingColor": unreal.LinearColor(0.867, 0.780, 0.608, 1.0), # #DDC79B
            "DashGlowColor": unreal.LinearColor(0.949, 0.816, 0.545, 1.0)
        }
    ))
    
    instances.append(create_instance(
        "MI_UI_Orrery_RingInner", ring,
        scalar_overrides={"InnerRadiusNormalized": 0.42, "OuterRadiusNormalized": 0.46, "DashCount": 0.0},
        vector_overrides={"RingColor": unreal.LinearColor(0.953, 0.902, 0.784, 1.0)} # #F3E6C8
    ))
    
    instances.append(create_instance(
        "MI_UI_Orrery_DiscFrame", disc,
        scalar_overrides={"OuterRadius": 0.92, "InnerRadius": 0.72, "CoreRadius": 0.65, "InnerDashCount": 24.0},
        vector_overrides={
            "OuterRingColor": unreal.LinearColor(0.953, 0.902, 0.784, 1.0),
            "InnerRingColor": unreal.LinearColor(0.867, 0.780, 0.608, 1.0),
            "CoreDiscColor": unreal.LinearColor(0.165, 0.086, 0.275, 0.95),
            "GlowColor": unreal.LinearColor(0.949, 0.816, 0.545, 1.0)
        }
    ))
    
    return instances

# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

def main():
    start_time = datetime.now(timezone.utc)
    unreal.log("=== BEGIN UI MATERIAL SUITE AUTHORING PASS ===")
    
    # Step 1: Build Master Materials
    m_toon = build_universal_toon_master()
    m_mstone = build_mstone_master()
    m_nikki = build_nikki_master()
    m_ring = build_radial_ring_master()
    m_disc = build_orrery_disc_master()
    
    masters = {
        "M_UI_UniversalToon_Master": m_toon,
        "M_UI_Mstone_Master": m_mstone,
        "M_UI_Nikki_Master": m_nikki,
        "M_UI_Storybook_RadialRing": m_ring,
        "M_UI_Storybook_OrreryDisc": m_disc,
    }
    
    # Step 2: Overhaul Stubs
    m_stub_card = overhaul_nikki_storybook_card()
    m_stub_vitals = overhaul_nikki_vitals_meter()
    m_stub_glow = overhaul_audio_glow_border()
    
    stubs = {
        "M_UI_Nikki_StorybookCard": m_stub_card,
        "M_UI_Nikki_VitalsMeter": m_stub_vitals,
        "M_UI_AudioGlow_Border": m_stub_glow,
    }
    
    # Step 3: Build All Material Instances
    instances = build_all_instances(masters)
    
    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()
    
    receipt = {
        "timestamp": end_time.isoformat(),
        "duration_seconds": duration,
        "masters_authored": [k for k in masters.keys()],
        "stubs_overhauled": [k for k in stubs.keys()],
        "instances_created": [inst.get_name() for inst in instances if inst],
        "total_assets": len(masters) + len(stubs) + len(instances),
        "status": "PASS"
    }
    
    AUDIT_REPORT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    unreal.log(f"=== UI MATERIAL SUITE COMPLETE: {receipt['total_assets']} assets generated in {duration:.2f}s ===")
    print(f"__UI_MATERIAL_PASS_COMPLETE__:{json.dumps(receipt)}")

if __name__ == "__main__":
    main()
