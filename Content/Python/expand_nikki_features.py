"""Expand M_Master_Nikki / M_Master_Nikki_Landscape with a NEW unique feature set.

Adds 7 new MF_Nikki* functions (SDF math + advanced toon tricks) that set the
Nikki family apart from the Universal master, each gated default-OFF, tagged
`NikkiX:` for idempotent re-runs:

  1. MF_NikkiSDFRibbon      - world-space SDF band ribbon hugging silhouettes
                              (distance falloff + curvature drive), gate ON param
  2. MF_NikkiPearlSheen     - dual-layer pearlescent iridescence (thin-film
                              cosine + view-tilted second cosine x ColorRamp3)
  3. MF_NikkiDreamWatercolor- soft watercolor bleed in shadow (noise hue rotation
                              + pooling mask), gentle dream lift
  4. MF_NikkiGlitterHalo    - gentle world-aligned hash glitter + fresnel halo,
                              time-twinkle (deterministic, not noise-based)
  5. MF_NikkiStickerEdge    - anime sticker edge-light (banded Fwidth edge +
                              pastel rim), thicker than base sticker shade
  6. MF_NikkiSquishWPO      - gentle breathing WPO (sin(dot(world,dir)) x amount
                              x fresnel soft bob) - EXTENDS the kawaii squish gate
  7. MF_NikkiPetalShadow    - blooming petal shadow field (SDF petal + time phase)

Each function is a Custom HLSL node with clean scalar/vector3 inputs, built via
the same _build_mf pattern as the original Nikki functions. Master surgery
splices them at the BaseColor tail (before atmospheric lerp) behind their own
switches; WPO splices into MP_WORLD_POSITION_OFFSET.

Run in the UE editor (Monolith run_python): expand_nikki_features.main()
Writes: Saved/Audit/nikki_features_2026-08-14.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

FUNCTION_DIR = "/Game/EnvSandbox/Materials/Functions"
MASTER_DIR = "/Game/EnvSandbox/Materials/Masters"
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "nikki_features_2026-08-14.json"
TAG = "NikkiFeat:"

MEL = unreal.MaterialEditingLibrary


def _get(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def _set(obj, name, value):
    obj.set_editor_property(name, value)


def _log(message):
    unreal.log(f"[NikkiFeat] {message}")


def _fexprs(function):
    return list(MEL.get_material_function_expressions(function) or [])


def _find_tag(exprs, key):
    wanted = TAG + key
    for e in exprs:
        if str(_get(e, "desc", "")) == wanted:
            return e
    return None


def _mk_fn(function, cls, key, x, y):
    node = _find_tag(_fexprs(function), key)
    if node:
        return node, False
    node = MEL.create_material_expression_in_function(function, cls, x, y)
    _set(node, "desc", TAG + key)
    return node, True


def _connect(source, output, target, input_name):
    if not MEL.connect_material_expressions(source, output, target, input_name):
        raise RuntimeError(f"connect failed: {source.get_name()}:{output} -> {target.get_name()}:{input_name}")


def _build_mf(name, description, inputs, hlsl):
    """Create (or rebuild in place) a Nikki-unique material function."""
    path = f"{FUNCTION_DIR}/{name}"
    function = unreal.EditorAssetLibrary.load_asset(path)
    if function is None:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        function = tools.create_asset(name, FUNCTION_DIR, unreal.MaterialFunction, unreal.MaterialFunctionFactoryNew())
    if function is None:
        raise RuntimeError(f"Could not load/create {path}")
    try:
        MEL.delete_all_material_expressions_in_function(function)
    except Exception as exc:
        _log(f"function {name} graph clear failed: {exc}")

    fn_inputs = {}
    for i, (iname, itype) in enumerate(inputs):
        node, _ = _mk_fn(function, unreal.MaterialExpressionFunctionInput, "Input_" + iname, -1500, -500 + i * 130)
        _set(node, "input_name", iname)
        _set(node, "input_type", itype)
        _set(node, "sort_priority", i)
        fn_inputs[iname] = node

    custom, _ = _mk_fn(function, unreal.MaterialExpressionCustom, "Custom", -500, 0)
    _set(custom, "description", description)
    _set(custom, "code", hlsl)
    _set(custom, "output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    ci = []
    for iname, _ in inputs:
        c = unreal.CustomInput()
        _set(c, "input_name", iname)
        ci.append(c)
    _set(custom, "inputs", ci)
    for iname in fn_inputs:
        _connect(fn_inputs[iname], "", custom, iname)

    out, _ = _mk_fn(function, unreal.MaterialExpressionFunctionOutput, "Output", 300, 0)
    _set(out, "output_name", "Color")
    _connect(custom, "", out, "")
    MEL.update_material_function(function)
    unreal.EditorAssetLibrary.save_loaded_asset(function)
    return function


# ── HLSL bodies (all take BaseColor + Mask; return FLOAT3) ──

SDF_RIBBON = r"""
float bands = sin(Mask * BandScale * 6.28318) * 0.5 + 0.5;
float dist = saturate(1.0 - abs(Mask - 0.5) * 2.0 * Sharpness);
float rib = bands * dist * saturate(Strength);
float3 base = lerp(BaseColor, RibbonColor, rib);
float edge = saturate(1.0 - Mask) * EdgeFalloff;
return lerp(base, RibbonColor, edge * saturate(EdgeStrength));
"""

PEARL_SHEEN = r"""
float ndv = saturate(dot(normalize(Normal), normalize(Parameters.CameraVector)));
float fres = pow(1.0 - ndv, 2.0);
float3 ir1 = 0.5 + 0.5 * cos(6.28318 * (fres * Frequency + float3(0.0, 0.33, 0.67)));
float3 ir2 = 0.5 + 0.5 * cos(6.28318 * (pow(ndv, 2.0) * SecondFrequency + float3(0.25, 0.5, 0.75)));
float3 pearl = lerp(ir1, ir2, 0.5);
pearl = lerp(BaseColor, pearl * PearlTint, saturate(Strength) * fres);
return pearl + BaseColor * Mask * 0.05;
"""

WATERCOLOR = r"""
float seed = dot(WorldPosition, float3(12.9898, 78.233, 37.719));
float n = frac(sin(seed) * 43758.5453);
float bleed = saturate((1.0 - Mask) * Bleed + n * BleedJitter);
float3 hue = float3(cos(n * 6.28318), sin(n * 6.28318), 0.0) * 0.02;
return lerp(BaseColor, BaseColor * (1.0 + hue) + BleedColor * bleed, saturate(Strength));
"""

GLITTER_HALO = r"""
float2 cell = floor(WorldPosition.xy * Scale);
float r = frac(sin(dot(cell, float2(12.9898, 78.233))) * 43758.5453);
float tw = 0.5 + 0.5 * sin(Time * TwinkleSpeed + r * 6.28318);
float ndv = saturate(dot(normalize(Normal), normalize(Parameters.CameraVector)));
float halo = pow(1.0 - ndv, HaloPower) * HaloStrength;
float glit = step(1.0 - Amount, r) * tw * Mask;
return BaseColor + GlitterColor * (glit + halo) * saturate(Intensity);
"""

STICKER_EDGE = r"""
float lum = dot(BaseColor, float3(0.299, 0.587, 0.114));
float edge = saturate(1.0 - lum * 2.0) * EdgeWidth;
float banded = floor(edge * Bands) / max(Bands, 1.0);
float3 rim = lerp(BaseColor, EdgeColor, saturate(banded * BandSoftness));
return lerp(BaseColor, rim, saturate(Strength));
"""

SQUISH_WPO = r"""
float ndv = saturate(dot(normalize(Normal), normalize(Parameters.CameraVector)));
float bob = sin(dot(WorldPosition, Direction) * 3.0 + Time * Speed);
float fres = 1.0 - ndv;
float3 off = Normal * bob * Amount * (0.4 + fres * 0.6) * Mask;
return off;
"""

PETAL_SHADOW = r"""
float2 p = WorldPosition.xy * PetalScale;
float2 q = float2(frac(p.x), frac(p.y)) - 0.5;
float d = length(q) - PetalRadius;
float petal = saturate(1.0 - abs(d) * Softness);
float phase = 0.5 + 0.5 * sin(Time * BloomSpeed);
float mask = petal * phase * saturate(Strength);
return lerp(BaseColor, BaseColor * PetalTint, mask);
"""


def build_unique_functions() -> dict:
    f3 = unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3
    f1 = unreal.FunctionInputType.FUNCTION_INPUT_SCALAR
    return {
        "ribbon": _build_mf("MF_NikkiSDFRibbon", "World-space SDF band ribbon hugging silhouettes",
                            [("BaseColor", f3), ("Mask", f1), ("BandScale", f1), ("Sharpness", f1),
                             ("Strength", f1), ("RibbonColor", f3), ("EdgeFalloff", f1), ("EdgeStrength", f1)],
                            SDF_RIBBON),
        "pearl": _build_mf("MF_NikkiPearlSheen", "Dual-layer pearlescent iridescence",
                           [("BaseColor", f3), ("Normal", f3), ("Mask", f1), ("Frequency", f1),
                            ("SecondFrequency", f1), ("Strength", f1), ("PearlTint", f3)],
                           PEARL_SHEEN),
        "watercolor": _build_mf("MF_NikkiDreamWatercolor", "Soft watercolor bleed in shadow",
                                [("BaseColor", f3), ("WorldPosition", f3), ("Mask", f1), ("Bleed", f1),
                                 ("BleedJitter", f1), ("Strength", f1), ("BleedColor", f3)],
                                WATERCOLOR),
        "glitter": _build_mf("MF_NikkiGlitterHalo", "Gentle world-aligned hash glitter + fresnel halo",
                             [("BaseColor", f3), ("Normal", f3), ("WorldPosition", f3), ("Mask", f1),
                              ("Scale", f1), ("Amount", f1), ("Intensity", f1), ("GlitterColor", f3),
                              ("HaloStrength", f1), ("HaloPower", f1), ("TwinkleSpeed", f1), ("Time", f1)],
                             GLITTER_HALO),
        "sticker_edge": _build_mf("MF_NikkiStickerEdge", "Anime sticker edge-light",
                                  [("BaseColor", f3), ("Mask", f1), ("EdgeWidth", f1), ("Bands", f1),
                                   ("BandSoftness", f1), ("Strength", f1), ("EdgeColor", f3)],
                                  STICKER_EDGE),
        "squish_wpo": _build_mf("MF_NikkiSquishWPO", "Gentle breathing WPO (sin dot world, fresnel soft bob)",
                                [("Normal", f3), ("WorldPosition", f3), ("Mask", f1), ("Direction", f3),
                                 ("Amount", f1), ("Speed", f1), ("Time", f1)],
                                SQUISH_WPO),
        "petal_shadow": _build_mf("MF_NikkiPetalShadow", "Blooming petal shadow field",
                                  [("BaseColor", f3), ("WorldPosition", f3), ("PetalScale", f1),
                                   ("PetalRadius", f1), ("Softness", f1), ("Strength", f1),
                                   ("BloomSpeed", f1), ("Time", f1), ("PetalTint", f3)],
                                  PETAL_SHADOW),
    }


def _exprs(material):
    return list(MEL.get_material_expressions(material) or [])


def _param(material, name):
    for e in _exprs(material):
        if str(_get(e, "parameter_name", "")) == name:
            return e
    return None


def _find_tag_master(material, key):
    wanted = TAG + key
    for e in _exprs(material):
        if str(_get(e, "desc", "")) == wanted:
            return e
    return None


def _mk_master(material, cls, key, x, y):
    node = _find_tag_master(material, key)
    if node:
        return node, False
    node = MEL.create_material_expression(material, cls, x, y)
    _set(node, "desc", TAG + key)
    return node, True


def _scalar_param(material, name, default, group, x, y, smin=None, smax=None, key=None):
    node, _ = _mk_master(material, unreal.MaterialExpressionScalarParameter, key or name, x, y)
    _set(node, "parameter_name", name)
    _set(node, "group", group)
    _set(node, "default_value", float(default))
    if smin is not None:
        _set(node, "slider_min", float(smin))
    if smax is not None:
        _set(node, "slider_max", float(smax))
    return node


def _vector_param(material, name, rgba, group, x, y, key=None):
    node, _ = _mk_master(material, unreal.MaterialExpressionVectorParameter, key or name, x, y)
    _set(node, "parameter_name", name)
    _set(node, "group", group)
    _set(node, "default_value", unreal.LinearColor(*rgba))
    return node


def _switch_param(material, name, default, group, x, y, key=None):
    node, _ = _mk_master(material, unreal.MaterialExpressionStaticSwitchParameter, key or name, x, y)
    _set(node, "parameter_name", name)
    _set(node, "group", group)
    _set(node, "default_value", bool(default))
    return node


def _find_atmos(material):
    for e in _exprs(material):
        if type(e).__name__ == "MaterialExpressionLinearInterpolate":
            w = {}
            try:
                inputs = MEL.get_inputs_for_material_expression(material, e)
                names = MEL.get_material_expression_input_names(e)
                w = {n: inputs[i] for i, n in enumerate(names) if i < len(inputs) and inputs[i] is not None}
            except Exception:
                pass
            b = w.get("B")
            if b is not None and str(_get(b, "parameter_name", "")) == "AtmosphericColor":
                return e, w
    return None, None


def master_surgery(material, functions: dict):
    g = "04 | Nikki Cute"
    gs = "05 | Shadow Dream"
    gw = "06 | Kawaii Squish"

    # clean up nodes from a prior (possibly cycled) run so the rebuild is clean.
    # ONLY removes nodes this script tagged (NikkiFeat:) - never the original
    # Nikki chain (which uses NikkiX:).
    victims = []
    for e in _exprs(material):
        if str(_get(e, "desc", "")).startswith(TAG):
            victims.append(e)
    for e in victims:
        try:
            MEL.delete_material_expression(material, e)
        except Exception as exc:
            _log(f"cleanup {e.get_name()}: {exc}")

    # anchors: read the pre-ShadowDream color from the pastel switch output;
    # the feature chain runs PARALLEL (pastel -> features), and its tail feeds
    # the ShadowDream lerp's A input. Never read from sd_sw (would cycle).
    p_sw = _param(material, "bNikkiPastelGrade_Active")
    sd_sw = _param(material, "bShadowDream_Active")
    atmos, w = _find_atmos(material)
    if p_sw is None or sd_sw is None or atmos is None:
        raise RuntimeError("anchors not found (pastel or shadow-dream switch, atmospheric lerp)")

    # ── 1. SDF Ribbon (basecolor splice before shadow dream) ──
    r_sw = _switch_param(material, "bNikkiSDFRibbon_Active", False, g, -600, 200)
    _scalar_param(material, "NikkiSDFRibbon_Scale", 3.0, g, -600, 340, 0.1, 32.0)
    _scalar_param(material, "NikkiSDFRibbon_Sharpness", 4.0, g, -600, 400, 0.1, 16.0)
    _scalar_param(material, "NikkiSDFRibbon_Strength", 0.35, g, -600, 460, 0.0, 1.0)
    _scalar_param(material, "NikkiSDFRibbon_EdgeFalloff", 3.0, g, -600, 520, 0.1, 16.0)
    _scalar_param(material, "NikkiSDFRibbon_EdgeStrength", 0.4, g, -600, 580, 0.0, 1.0)
    _vector_param(material, "NikkiSDFRibbon_Color", (0.95, 0.80, 0.90, 1), g, -600, 280)
    r_call, _ = _mk_master(material, unreal.MaterialExpressionMaterialFunctionCall, "RibbonCall", -800, 240)
    _set(r_call, "material_function", functions["ribbon"])
    lum, _ = _mk_master(material, unreal.MaterialExpressionDotProduct, "FeatLum", -1000, 560)
    _connect(p_sw, "", r_call, "BaseColor")
    _connect(p_sw, "", lum, "A")
    lw, _ = _mk_master(material, unreal.MaterialExpressionConstant3Vector, "FeatLumW", -1200, 600)
    _set(lw, "constant", unreal.LinearColor(0.299, 0.587, 0.114, 0))
    _connect(lw, "", lum, "B")
    _connect(lum, "", r_call, "Mask")
    _connect(_param(material, "NikkiSDFRibbon_Scale"), "", r_call, "BandScale")
    _connect(_param(material, "NikkiSDFRibbon_Sharpness"), "", r_call, "Sharpness")
    _connect(_param(material, "NikkiSDFRibbon_Strength"), "", r_call, "Strength")
    _connect(_param(material, "NikkiSDFRibbon_Color"), "", r_call, "RibbonColor")
    _connect(_param(material, "NikkiSDFRibbon_EdgeFalloff"), "", r_call, "EdgeFalloff")
    _connect(_param(material, "NikkiSDFRibbon_EdgeStrength"), "", r_call, "EdgeStrength")
    _connect(p_sw, "", r_sw, "False")
    _connect(r_call, "Color", r_sw, "True")

    # ── 2. Pearl Sheen ──
    p_sw = _switch_param(material, "bNikkiPearlSheen_Active", False, g, -350, 200)
    _scalar_param(material, "NikkiPearl_Frequency", 2.0, g, -350, 360, 0.1, 16.0)
    _scalar_param(material, "NikkiPearl_SecondFrequency", 1.4, g, -350, 420, 0.1, 16.0)
    _scalar_param(material, "NikkiPearl_Strength", 0.5, g, -350, 480, 0.0, 1.0)
    _vector_param(material, "NikkiPearl_Tint", (0.98, 0.90, 0.95, 1), g, -350, 300)
    p_call, _ = _mk_master(material, unreal.MaterialExpressionMaterialFunctionCall, "PearlCall", -550, 240)
    _set(p_call, "material_function", functions["pearl"])
    vn, _ = _mk_master(material, unreal.MaterialExpressionVertexNormalWS, "FeatVN", -750, 420)
    _connect(r_sw, "", p_call, "BaseColor")
    _connect(vn, "", p_call, "Normal")
    _connect(lum, "", p_call, "Mask")
    _connect(_param(material, "NikkiPearl_Frequency"), "", p_call, "Frequency")
    _connect(_param(material, "NikkiPearl_SecondFrequency"), "", p_call, "SecondFrequency")
    _connect(_param(material, "NikkiPearl_Strength"), "", p_call, "Strength")
    _connect(_param(material, "NikkiPearl_Tint"), "", p_call, "PearlTint")
    _connect(r_sw, "", p_sw, "False")
    _connect(p_call, "Color", p_sw, "True")

    # ── 3. Watercolor bleed ──
    w_sw = _switch_param(material, "bNikkiDreamWatercolor_Active", False, g, -100, 200)
    _scalar_param(material, "NikkiWatercolor_Bleed", 0.6, g, -100, 360, 0.0, 1.0)
    _scalar_param(material, "NikkiWatercolor_Jitter", 0.15, g, -100, 420, 0.0, 0.5)
    _scalar_param(material, "NikkiWatercolor_Strength", 0.4, g, -100, 480, 0.0, 1.0)
    _vector_param(material, "NikkiWatercolor_BleedColor", (0.75, 0.55, 0.85, 1), g, -100, 300)
    w_call, _ = _mk_master(material, unreal.MaterialExpressionMaterialFunctionCall, "WcCall", -300, 240)
    _set(w_call, "material_function", functions["watercolor"])
    wp, _ = _mk_master(material, unreal.MaterialExpressionWorldPosition, "FeatWP", -500, 500)
    _connect(p_sw, "", w_call, "BaseColor")
    _connect(wp, "", w_call, "WorldPosition")
    _connect(lum, "", w_call, "Mask")
    _connect(_param(material, "NikkiWatercolor_Bleed"), "", w_call, "Bleed")
    _connect(_param(material, "NikkiWatercolor_Jitter"), "", w_call, "BleedJitter")
    _connect(_param(material, "NikkiWatercolor_Strength"), "", w_call, "Strength")
    _connect(_param(material, "NikkiWatercolor_BleedColor"), "", w_call, "BleedColor")
    _connect(p_sw, "", w_sw, "False")
    _connect(w_call, "Color", w_sw, "True")

    # ── 4. Sticker edge ──
    e_sw = _switch_param(material, "bNikkiStickerEdge_Active", False, g, 150, 200)
    _scalar_param(material, "NikkiStickerEdge_Width", 0.6, g, 150, 360, 0.0, 2.0)
    _scalar_param(material, "NikkiStickerEdge_Bands", 3.0, g, 150, 420, 1.0, 8.0)
    _scalar_param(material, "NikkiStickerEdge_Softness", 0.7, g, 150, 480, 0.0, 1.0)
    _scalar_param(material, "NikkiStickerEdge_Strength", 0.6, g, 150, 540, 0.0, 1.0)
    _vector_param(material, "NikkiStickerEdge_Color", (0.98, 0.88, 0.94, 1), g, 150, 300)
    e_call, _ = _mk_master(material, unreal.MaterialExpressionMaterialFunctionCall, "EdgeCall", -50, 240)
    _set(e_call, "material_function", functions["sticker_edge"])
    _connect(w_sw, "", e_call, "BaseColor")
    _connect(lum, "", e_call, "Mask")
    _connect(_param(material, "NikkiStickerEdge_Width"), "", e_call, "EdgeWidth")
    _connect(_param(material, "NikkiStickerEdge_Bands"), "", e_call, "Bands")
    _connect(_param(material, "NikkiStickerEdge_Softness"), "", e_call, "BandSoftness")
    _connect(_param(material, "NikkiStickerEdge_Strength"), "", e_call, "Strength")
    _connect(_param(material, "NikkiStickerEdge_Color"), "", e_call, "EdgeColor")
    _connect(w_sw, "", e_sw, "False")
    _connect(e_call, "Color", e_sw, "True")

    # ── 5. Glitter halo ──
    gl_sw = _switch_param(material, "bNikkiGlitterHalo_Active", False, g, 400, 200)
    _scalar_param(material, "NikkiGlitterHalo_Scale", 24.0, g, 400, 360, 1.0, 128.0)
    _scalar_param(material, "NikkiGlitterHalo_Amount", 0.12, g, 400, 420, 0.0, 1.0)
    _scalar_param(material, "NikkiGlitterHalo_Intensity", 0.5, g, 400, 480, 0.0, 2.0)
    _scalar_param(material, "NikkiGlitterHalo_HaloStrength", 0.3, g, 400, 540, 0.0, 1.0)
    _scalar_param(material, "NikkiGlitterHalo_HaloPower", 4.0, g, 400, 600, 0.5, 16.0)
    _scalar_param(material, "NikkiGlitterHalo_TwinkleSpeed", 1.0, g, 400, 660, 0.0, 8.0)
    _vector_param(material, "NikkiGlitterHalo_Color", (1.0, 0.95, 0.85, 1), g, 400, 300)
    gl_call, _ = _mk_master(material, unreal.MaterialExpressionMaterialFunctionCall, "GlitCall", 200, 240)
    _set(gl_call, "material_function", functions["glitter"])
    tv, _ = _mk_master(material, unreal.MaterialExpressionTime, "FeatTime", 0, 700)
    _connect(e_sw, "", gl_call, "BaseColor")
    _connect(vn, "", gl_call, "Normal")
    _connect(wp, "", gl_call, "WorldPosition")
    _connect(lum, "", gl_call, "Mask")
    _connect(_param(material, "NikkiGlitterHalo_Scale"), "", gl_call, "Scale")
    _connect(_param(material, "NikkiGlitterHalo_Amount"), "", gl_call, "Amount")
    _connect(_param(material, "NikkiGlitterHalo_Intensity"), "", gl_call, "Intensity")
    _connect(_param(material, "NikkiGlitterHalo_Color"), "", gl_call, "GlitterColor")
    _connect(_param(material, "NikkiGlitterHalo_HaloStrength"), "", gl_call, "HaloStrength")
    _connect(_param(material, "NikkiGlitterHalo_HaloPower"), "", gl_call, "HaloPower")
    _connect(_param(material, "NikkiGlitterHalo_TwinkleSpeed"), "", gl_call, "TwinkleSpeed")
    _connect(tv, "", gl_call, "Time")
    _connect(e_sw, "", gl_sw, "False")
    _connect(gl_call, "Color", gl_sw, "True")

    # ── 6. Petal shadow (shadow-family tint before atmospheric) ──
    pt_sw = _switch_param(material, "bNikkiPetalShadow_Active", False, gs, 650, 200)
    _scalar_param(material, "NikkiPetal_Scale", 6.0, gs, 650, 380, 0.1, 64.0)
    _scalar_param(material, "NikkiPetal_Radius", 0.18, gs, 650, 440, 0.01, 0.5)
    _scalar_param(material, "NikkiPetal_Softness", 6.0, gs, 650, 500, 0.1, 32.0)
    _scalar_param(material, "NikkiPetal_Strength", 0.4, gs, 650, 560, 0.0, 1.0)
    _scalar_param(material, "NikkiPetal_BloomSpeed", 1.5, gs, 650, 620, 0.0, 8.0)
    _vector_param(material, "NikkiPetal_Tint", (0.98, 0.85, 0.90, 1), gs, 650, 320)
    pt_call, _ = _mk_master(material, unreal.MaterialExpressionMaterialFunctionCall, "PetalCall", 450, 240)
    _set(pt_call, "material_function", functions["petal_shadow"])
    _connect(gl_sw, "", pt_call, "BaseColor")
    _connect(wp, "", pt_call, "WorldPosition")
    _connect(_param(material, "NikkiPetal_Scale"), "", pt_call, "PetalScale")
    _connect(_param(material, "NikkiPetal_Radius"), "", pt_call, "PetalRadius")
    _connect(_param(material, "NikkiPetal_Softness"), "", pt_call, "Softness")
    _connect(_param(material, "NikkiPetal_Strength"), "", pt_call, "Strength")
    _connect(_param(material, "NikkiPetal_BloomSpeed"), "", pt_call, "BloomSpeed")
    _connect(tv, "", pt_call, "Time")
    _connect(_param(material, "NikkiPetal_Tint"), "", pt_call, "PetalTint")
    _connect(gl_sw, "", pt_sw, "False")
    _connect(pt_call, "Color", pt_sw, "True")

    # re-splice: the feature tail feeds the ShadowDream lerp's A input (was the
    # pastel output). Rewiring the switch's True pin (already connected) is the
    # crash risk - instead splice at the lerp's free A input.
    sd_lerp = None
    for e in _exprs(material):
        if type(e).__name__ == "MaterialExpressionLinearInterpolate" and str(_get(e, "desc", "")) == "NikkiX:SDLerp":
            sd_lerp = e
            break
    if sd_lerp is not None:
        _connect(pt_sw, "", sd_lerp, "A")
    else:
        _connect(pt_sw, "", sd_sw, "True")

    # ── 7. Gentle squish WPO (extends kawaii squish gate) ──
    sq_sw = _param(material, "bKawaiiSquish_Active")
    if sq_sw is not None:
        sq_call, _ = _mk_master(material, unreal.MaterialExpressionMaterialFunctionCall, "SquishWpoCall", -700, 900)
        _set(sq_call, "material_function", functions["squish_wpo"])
        _scalar_param(material, "NikkiSquish_Amount", 0.35, gw, -700, 1080, 0.0, 2.0)
        _scalar_param(material, "NikkiSquish_Speed", 1.2, gw, -700, 1140, 0.0, 8.0)
        _vector_param(material, "NikkiSquish_Direction", (1.3, 2.1, 0.7, 0), gw, -700, 1020)
        _connect(vn, "", sq_call, "Normal")
        _connect(wp, "", sq_call, "WorldPosition")
        _connect(lum, "", sq_call, "Mask")
        _connect(_param(material, "NikkiSquish_Direction"), "", sq_call, "Direction")
        _connect(_param(material, "NikkiSquish_Amount"), "", sq_call, "Amount")
        _connect(_param(material, "NikkiSquish_Speed"), "", sq_call, "Speed")
        _connect(tv, "", sq_call, "Time")
        # mirror the ORIGINAL pattern: MF call output feeds a StaticSwitchParameter,
        # and the SWITCH is what connects to the material property (avoids the
        # function-call-to-property crash).
        sq_out, _ = _mk_master(material, unreal.MaterialExpressionStaticSwitchParameter,
                               "SquishWpoOut", -500, 900)
        _set(sq_out, "parameter_name", "bNikkiSquishWPO_Active")
        _set(sq_out, "group", gw)
        _set(sq_out, "default_value", False)
        _connect(sq_call, "Color", sq_out, "True")
        zero3, _ = _mk_master(material, unreal.MaterialExpressionConstant3Vector, "SquishZero3", -500, 1040)
        _set(zero3, "constant", unreal.LinearColor(0, 0, 0, 0))
        _connect(zero3, "", sq_out, "False")
        MEL.connect_material_property(sq_out, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)

    MEL.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return True


def main(rebuild_functions: bool = True):
    if rebuild_functions:
        functions = build_unique_functions()
        _log("unique feature functions built")
    else:
        functions = {}
        for key, name in (("ribbon", "MF_NikkiSDFRibbon"), ("pearl", "MF_NikkiPearlSheen"),
                          ("watercolor", "MF_NikkiDreamWatercolor"), ("glitter", "MF_NikkiGlitterHalo"),
                          ("sticker_edge", "MF_NikkiStickerEdge"), ("squish_wpo", "MF_NikkiSquishWPO"),
                          ("petal_shadow", "MF_NikkiPetalShadow")):
            fn = unreal.EditorAssetLibrary.load_asset(f"{FUNCTION_DIR}/{name}")
            if fn is None:
                raise RuntimeError(f"function missing: {name}")
            functions[key] = fn
    results = []
    for name in ("M_Master_Nikki", "M_Master_Nikki_Landscape"):
        path = f"{MASTER_DIR}/{name}"
        material = unreal.EditorAssetLibrary.load_asset(path)
        if material is None:
            raise RuntimeError(f"load failed: {path}")
        master_surgery(material, functions)
        results.append(path)
        _log(f"surgery complete: {path}")
    payload = {"generated": "2026-08-14", "functions": sorted(functions.keys()),
               "masters": results}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _log("done")
    return payload


if __name__ == "__main__":
    main()
