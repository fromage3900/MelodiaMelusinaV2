"""Build shared MF_* material function library for full-stack toon materials.

Run headless:
  UnrealEditor-Cmd.exe BS_GodFile.uproject ^
    -ExecutePythonScript="G:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_material_functions.py"
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

import material_lib as lib

REPORT_PATH = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "material_functions_build.json"

# (name, description) — each MF exposes Result output for master MaterialFunctionCall wiring
MF_SPECS: list[tuple[str, str]] = [
    ("MF_UVTransform", "UV scale + rotation transform"),
    ("MF_RealParallax", "Height-based parallax UV offset"),
    ("MF_CurvatureOrnament", "Curvature-driven ornament mask"),
    ("MF_Impressionist_BrushStroke", "Directional oil paint stroke mask"),
    ("MF_Impressionist_Impasto", "Impasto height from stroke mask"),
    ("MF_Impressionist_Temporal", "Temporal FBm noise modulation"),
    ("MF_Impressionist_InkPool", "Valley ink pooling mask"),
    ("MF_AudioReactiveBlend", "Audio MPC-driven blend factor"),
    ("MF_GildingOverlay", "Gold tint overlay blend"),
    ("MF_MapComposite", "Normal/roughness map composite factor"),
    ("MF_SDF_BandRelief", "World SDF band relief mask"),
    ("MF_AnimeSkinWrap", "Wrap lighting + soft skin shadow mask"),
    ("MF_ParallaxCore", "Height parallax UV offset — modes 0/1/2"),
    ("MF_NormalAdjust", "Normal strength + power + per-layer scale"),
    ("MF_Madoka", "Witch-barrier voronoi veins + cute/corrupt tint (Phase 1, no Blur)"),
    ("MF_Itto", "Truchet crack + wear roughness add (Phase 1, no height/ink)"),
]


def _clear_function_graph(mf: unreal.MaterialFunction) -> None:
    try:
        if not hasattr(unreal.MaterialEditingLibrary, "get_material_function_expressions"):
            return
        exprs = unreal.MaterialEditingLibrary.get_material_function_expressions(mf)
        for expr in list(exprs or []):
            unreal.MaterialEditingLibrary.delete_material_expression_in_function(mf, expr)
    except Exception as exc:
        unreal.log_warning(f"[MF] clear graph {mf.get_name()}: {exc}")


def _create_or_rebuild_mf(name: str, *, force: bool = False) -> unreal.MaterialFunction:
    lib.ensure_directory(lib.FUNCTION_DIR)
    path = lib.asset_path(lib.FUNCTION_DIR, name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        mf = unreal.load_asset(path)
        if mf and not force:
            unreal.log(f"[MF] skip existing {path}")
            return mf
        if mf and force:
            _clear_function_graph(mf)
            return mf

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialFunctionFactoryNew()
    mf = asset_tools.create_asset(name, lib.FUNCTION_DIR, unreal.MaterialFunction, factory)
    if mf:
        return mf

    # Fallback: duplicate a sibling MF when create_asset returns None (ghost delete / registry lag).
    for template in ("MF_MapComposite", "MF_RealParallax", "MF_GildingOverlay"):
        src = lib.asset_path(lib.FUNCTION_DIR, template)
        if not unreal.EditorAssetLibrary.does_asset_exist(src):
            continue
        dest = f"{lib.FUNCTION_DIR}/{name}"
        dup = unreal.EditorAssetLibrary.duplicate_asset(src, dest)
        if dup and unreal.EditorAssetLibrary.does_asset_exist(path):
            mf = unreal.load_asset(path)
            if mf:
                if force:
                    _clear_function_graph(mf)
                unreal.log(f"[MF] duplicated {template} -> {name}")
                return mf

    raise RuntimeError(f"Failed to create {name} at {lib.FUNCTION_DIR}")


def _add_function_output(mf, from_expr, output_name: str, x: int, y: int) -> None:
    out = lib.create_expression(mf, unreal.MaterialExpressionFunctionOutput, x, y)
    out.set_editor_property("output_name", output_name)
    lib.connect(from_expr, "", out, "")


def _fn_input(mf, name: str, x: int, y: int, *, sort: int = 0):
    """Material function input exposed on MaterialFunctionCall pins."""
    inp = lib.create_expression(mf, unreal.MaterialExpressionFunctionInput, x, y)
    inp.set_editor_property("input_name", name)
    try:
        inp.set_editor_property("sort_priority", sort)
    except Exception:
        pass
    if name in ("UV",):
        try:
            inp.set_editor_property("input_type", unreal.FunctionInputType.FIT_FLOAT2)
        except Exception:
            pass
    if name == "HeightTexture":
        try:
            inp.set_editor_property("input_type", unreal.FunctionInputType.FIT_TEXTURE2D)
        except Exception:
            pass
    return inp


def _view_xy(mf, x: int, y: int):
    """Camera vector XY as float2 for parallax offset."""
    view = lib.create_expression(mf, unreal.MaterialExpressionCameraVectorWS, x, y)
    view_r = lib.create_expression(mf, unreal.MaterialExpressionComponentMask, x + 160, y - 40)
    view_r.set_editor_property("r", True)
    view_r.set_editor_property("g", False)
    view_r.set_editor_property("b", False)
    view_r.set_editor_property("a", False)
    lib.connect_unary(view, view_r)
    view_g = lib.create_expression(mf, unreal.MaterialExpressionComponentMask, x + 160, y + 40)
    view_g.set_editor_property("r", False)
    view_g.set_editor_property("g", True)
    view_g.set_editor_property("b", False)
    view_g.set_editor_property("a", False)
    lib.connect_unary(view, view_g)
    xy = lib.create_expression(mf, unreal.MaterialExpressionAppendVector, x + 320, y)
    lib.connect_append2(view_r, view_g, xy)
    return xy


def _build_uv_transform(mf: unreal.MaterialFunction) -> None:
    uv = lib.create_expression(mf, unreal.MaterialExpressionTextureCoordinate, -800, 0)
    uv.set_editor_property("coordinate_index", 0)
    scale = lib.scalar_param(mf, "UVScale", "UV", 1.0, -800, 120)
    rot = lib.scalar_param(mf, "UVRotation", "UV", 0.0, -800, 220)
    mul = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -560, 40)
    lib.connect(uv, "", mul, "A")
    lib.connect(scale, "", mul, "B")
    rot_rad = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -560, 180)
    const_pi = lib.create_expression(mf, unreal.MaterialExpressionConstant, -720, 260)
    const_pi.set_editor_property("r", 0.0174533)
    lib.connect(rot, "", rot_rad, "A")
    lib.connect(const_pi, "", rot_rad, "B")
    cos_n = lib.create_expression(mf, unreal.MaterialExpressionCosine, -360, 120)
    sin_n = lib.create_expression(mf, unreal.MaterialExpressionSine, -360, 220)
    lib.connect_unary(rot_rad, cos_n)
    lib.connect_unary(rot_rad, sin_n)
    _add_function_output(mf, mul, "Result", -120, 40)


def _build_real_parallax(mf: unreal.MaterialFunction) -> None:
    height = lib.scalar_param(mf, "Height", "Parallax", 0.5, -800, 0)
    scale = lib.scalar_param(mf, "ParallaxScale", "Parallax", 0.05, -800, 100)
    view = lib.create_expression(mf, unreal.MaterialExpressionCameraVectorWS, -800, 220)
    offset = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -480, 80)
    lib.connect(height, "", offset, "A")
    lib.connect(scale, "", offset, "B")
    parallax = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -240, 80)
    lib.connect(offset, "", parallax, "A")
    lib.connect(view, "", parallax, "B")
    _add_function_output(mf, parallax, "Result", -40, 80)


def _build_curvature_ornament(mf: unreal.MaterialFunction) -> None:
    normal = lib.create_expression(mf, unreal.MaterialExpressionPixelNormalWS, -800, 0)
    ddx = lib.create_expression(mf, unreal.MaterialExpressionDDX, -600, -80)
    ddy = lib.create_expression(mf, unreal.MaterialExpressionDDY, -600, 80)
    lib.connect_unary(normal, ddx)
    lib.connect_unary(normal, ddy)
    curve = lib.create_expression(mf, unreal.MaterialExpressionAdd, -400, 0)
    lib.connect(ddx, "", curve, "A")
    lib.connect(ddy, "", curve, "B")
    sens = lib.scalar_param(mf, "CurvatureSensitivity", "Ornament", 2.0, -800, 180)
    style = lib.scalar_param(mf, "OrnamentStyle", "Ornament", 0.0, -800, 280)
    mod = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -200, 40)
    lib.connect(curve, "", mod, "A")
    lib.connect(sens, "", mod, "B")
    styled = lib.create_expression(mf, unreal.MaterialExpressionAdd, 0, 40)
    lib.connect(mod, "", styled, "A")
    lib.connect(style, "", styled, "B")
    mask = lib.create_expression(mf, unreal.MaterialExpressionAbs, 160, 40)
    lib.connect_unary(styled, mask)
    _add_function_output(mf, mask, "Result", 320, 40)


def _build_brush_stroke(mf: unreal.MaterialFunction) -> None:
    world = lib.create_expression(mf, unreal.MaterialExpressionWorldPosition, -900, 0)
    mask_xy = lib.create_expression(mf, unreal.MaterialExpressionComponentMask, -720, 0)
    mask_xy.set_editor_property("r", True)
    mask_xy.set_editor_property("g", True)
    mask_xy.set_editor_property("b", False)
    mask_xy.set_editor_property("a", False)
    lib.connect(world, "", mask_xy, "")
    brush_scale = lib.scalar_param(mf, "BrushScale", "OilPaint", 0.045, -900, 120)
    stroke = lib.scalar_param(mf, "StrokeStrength", "OilPaint", 0.55, -900, 220)
    scale_mul = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -540, 40)
    lib.connect(mask_xy, "", scale_mul, "A")
    lib.connect(brush_scale, "", scale_mul, "B")
    sin_n = lib.create_expression(mf, unreal.MaterialExpressionSine, -360, 40)
    sin_n.set_editor_property("period", 1.0)
    lib.connect_unary(scale_mul, sin_n)
    abs_n = lib.create_expression(mf, unreal.MaterialExpressionAbs, -180, 40)
    lib.connect_unary(sin_n, abs_n)
    out = lib.create_expression(mf, unreal.MaterialExpressionMultiply, 0, 40)
    lib.connect(abs_n, "", out, "A")
    lib.connect(stroke, "", out, "B")
    _add_function_output(mf, out, "Result", 180, 40)


def _build_impasto(mf: unreal.MaterialFunction) -> None:
    stroke = lib.scalar_param(mf, "StrokeMask", "Impasto", 0.5, -600, 0)
    strength = lib.scalar_param(mf, "ImpastoStrength", "Impasto", 0.35, -600, 100)
    height = lib.scalar_param(mf, "ImpastoHeight", "Impasto", 0.025, -600, 200)
    h1 = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -320, 40)
    lib.connect(stroke, "", h1, "A")
    lib.connect(strength, "", h1, "B")
    h2 = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -120, 40)
    lib.connect(h1, "", h2, "A")
    lib.connect(height, "", h2, "B")
    _add_function_output(mf, h2, "Result", 80, 40)


def _build_temporal(mf: unreal.MaterialFunction) -> None:
    world = lib.create_expression(mf, unreal.MaterialExpressionWorldPosition, -900, 0)
    mask_xy = lib.create_expression(mf, unreal.MaterialExpressionComponentMask, -720, 0)
    mask_xy.set_editor_property("r", True)
    mask_xy.set_editor_property("g", True)
    mask_xy.set_editor_property("b", False)
    mask_xy.set_editor_property("a", False)
    lib.connect(world, "", mask_xy, "")
    time = lib.create_expression(mf, unreal.MaterialExpressionTime, -900, 140)
    noise_scale = lib.scalar_param(mf, "NoiseScale", "Temporal", 1.5, -900, 260)
    temporal = lib.scalar_param(mf, "TemporalStrength", "Temporal", 0.12, -900, 360)
    wind = lib.scalar_param(mf, "WindSpeed", "Temporal", 0.15, -900, 460)
    wind_mul = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -720, 160)
    lib.connect(time, "", wind_mul, "A")
    lib.connect(wind, "", wind_mul, "B")
    scaled = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -540, 40)
    lib.connect(mask_xy, "", scaled, "A")
    lib.connect(noise_scale, "", scaled, "B")
    phase = lib.create_expression(mf, unreal.MaterialExpressionAdd, -360, 60)
    lib.connect(scaled, "", phase, "A")
    lib.connect(wind_mul, "", phase, "B")
    sine = lib.create_expression(mf, unreal.MaterialExpressionSine, -180, 60)
    sine.set_editor_property("period", 1.0)
    lib.connect_unary(phase, sine)
    out = lib.create_expression(mf, unreal.MaterialExpressionMultiply, 0, 60)
    lib.connect(sine, "", out, "A")
    lib.connect(temporal, "", out, "B")
    _add_function_output(mf, out, "Result", 180, 60)


def _build_ink_pool(mf: unreal.MaterialFunction) -> None:
    stroke = lib.scalar_param(mf, "StrokeMask", "Ink", 0.5, -600, 0)
    wetness = lib.scalar_param(mf, "Wetness", "Ink", 0.0, -600, 100)
    ink = lib.scalar_param(mf, "InkIntensity", "Ink", 0.0, -600, 200)
    pooling = lib.scalar_param(mf, "PoolingStrength", "Ink", 0.5, -600, 300)
    inv = lib.create_expression(mf, unreal.MaterialExpressionOneMinus, -360, 0)
    lib.connect_unary(stroke, inv)
    wet = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -180, 40)
    lib.connect(inv, "", wet, "A")
    lib.connect(wetness, "", wet, "B")
    ink_w = lib.create_expression(mf, unreal.MaterialExpressionMultiply, 0, 40)
    lib.connect(wet, "", ink_w, "A")
    lib.connect(ink, "", ink_w, "B")
    pool = lib.create_expression(mf, unreal.MaterialExpressionMultiply, 180, 40)
    lib.connect(ink_w, "", pool, "A")
    lib.connect(pooling, "", pool, "B")
    _add_function_output(mf, pool, "Result", 360, 40)


def _build_audio_blend(mf: unreal.MaterialFunction) -> None:
    reactivity = lib.scalar_param(mf, "AudioReactivity", "Audio", 0.0, -600, 0)
    bass_w = lib.scalar_param(mf, "BassWeight", "Audio", 1.0, -600, 100)
    mid_w = lib.scalar_param(mf, "MidWeight", "Audio", 0.5, -600, 200)
    treble_w = lib.scalar_param(mf, "TrebleWeight", "Audio", 0.25, -600, 300)
    blend = lib.create_expression(mf, unreal.MaterialExpressionAdd, -240, 120)
    lib.connect(bass_w, "", blend, "A")
    mid_add = lib.create_expression(mf, unreal.MaterialExpressionAdd, -400, 160)
    lib.connect(mid_w, "", mid_add, "A")
    lib.connect(treble_w, "", mid_add, "B")
    lib.connect(mid_add, "", blend, "B")
    out = lib.create_expression(mf, unreal.MaterialExpressionMultiply, 0, 80)
    lib.connect(reactivity, "", out, "A")
    lib.connect(blend, "", out, "B")
    _add_function_output(mf, out, "Result", 180, 80)


def _build_gilding(mf: unreal.MaterialFunction) -> None:
    strength = lib.scalar_param(mf, "GildingStrength", "Gilding", 0.0, -600, 0)
    gold = lib.vector_param(mf, "GoldTint", "Gilding", (0.85, 0.65, 0.25, 1.0), -600, 120)
    emissive = lib.scalar_param(mf, "GoldEmissive", "Gilding", 0.0, -600, 260)
    out = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -240, 80)
    lib.connect(strength, "", out, "A")
    lib.connect(gold, "", out, "B")
    _add_function_output(mf, out, "Color", 0, 80)
    _add_function_output(mf, emissive, "Emissive", 0, 260)


def _build_map_composite(mf: unreal.MaterialFunction) -> None:
    rough_map = lib.texture_param(mf, "RoughnessMap", "Maps", -600, 0)
    normal_map = lib.texture_param(mf, "NormalMap", "Maps", -600, 160)
    rough_const = lib.scalar_param(mf, "RoughnessScalar", "Maps", 0.75, -600, 320)
    rough_mul = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -240, 40)
    lib.connect(rough_map, "", rough_mul, "A")
    lib.connect(rough_const, "", rough_mul, "B")
    _add_function_output(mf, rough_mul, "Roughness", 0, 40)
    _add_function_output(mf, normal_map, "Normal", 0, 160)


def _build_anime_skin_wrap(mf: unreal.MaterialFunction) -> None:
    """Wrapped N·L proxy for anime skin — strength 0 = neutral lit factor (~1)."""
    normal = lib.create_expression(mf, unreal.MaterialExpressionPixelNormalWS, -900, 0)
    light_dir = lib.create_expression(mf, unreal.MaterialExpressionConstant3Vector, -900, 140)
    light_dir.set_editor_property("constant", unreal.LinearColor(0.35, 0.55, 0.85, 1.0))
    ndotl = lib.create_expression(mf, unreal.MaterialExpressionDotProduct, -680, 40)
    lib.connect(normal, "", ndotl, "A")
    lib.connect(light_dir, "", ndotl, "B")
    wrap_str = lib.scalar_param(mf, "WrapStrength", "Skin", 0.0, -900, 280)
    wrap_rad = lib.scalar_param(mf, "WrapRadius", "Skin", 0.55, -900, 380)
    wrap_mul = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -520, 120)
    lib.connect(wrap_rad, "", wrap_mul, "A")
    lib.connect(wrap_str, "", wrap_mul, "B")
    wrap_add = lib.create_expression(mf, unreal.MaterialExpressionAdd, -360, 40)
    lib.connect(ndotl, "", wrap_add, "A")
    lib.connect(wrap_mul, "", wrap_add, "B")
    one = lib.create_expression(mf, unreal.MaterialExpressionConstant, -520, 260)
    one.set_editor_property("r", 1.0)
    wrap_den = lib.create_expression(mf, unreal.MaterialExpressionAdd, -360, 200)
    lib.connect(one, "", wrap_den, "A")
    lib.connect(wrap_rad, "", wrap_den, "B")
    wrap_div = lib.create_expression(mf, unreal.MaterialExpressionDivide, -200, 80)
    lib.connect(wrap_add, "", wrap_div, "A")
    lib.connect(wrap_den, "", wrap_div, "B")
    wrap_sat = lib.create_expression(mf, unreal.MaterialExpressionSaturate, -40, 80)
    lib.connect_unary(wrap_div, wrap_sat)
    std_sat = lib.create_expression(mf, unreal.MaterialExpressionSaturate, -200, 220)
    lib.connect_unary(ndotl, std_sat)
    lit = lib.create_expression(mf, unreal.MaterialExpressionLinearInterpolate, 120, 120)
    lib.connect(std_sat, "", lit, "A")
    lib.connect(wrap_sat, "", lit, "B")
    lib.connect(wrap_str, "", lit, "Alpha")
    _add_function_output(mf, lit, "Result", 300, 120)


def _build_parallax_core(mf: unreal.MaterialFunction) -> None:
    """Parallax UV offset: mode 0 simple, 1 steep, 2 stepped POM proxy."""
    uv_in = _fn_input(mf, "UV", -1400, 0, sort=0)
    ht_in = _fn_input(mf, "HeightTexture", -1400, 120, sort=1)
    scale_in = _fn_input(mf, "ParallaxScale", -1400, 240, sort=2)
    layer_in = _fn_input(mf, "LayerParallaxScale", -1400, 360, sort=3)
    str_in = _fn_input(mf, "ParallaxStrength", -1400, 480, sort=4)
    height_in = _fn_input(mf, "ParallaxHeight", -1400, 600, sort=5)
    steps_in = _fn_input(mf, "ParallaxSteps", -1400, 720, sort=6)
    mode_in = _fn_input(mf, "ParallaxMode", -1400, 840, sort=7)

    h_s = lib.create_expression(mf, unreal.MaterialExpressionTextureSample, -1120, 40)
    lib.connect_any(ht_in, h_s, ("Tex", "TextureObject"))
    lib.connect_any(uv_in, h_s, ("UVs", "Coordinates"))
    h_r = lib.create_expression(mf, unreal.MaterialExpressionComponentMask, -960, 40)
    h_r.set_editor_property("r", True)
    h_r.set_editor_property("g", False)
    h_r.set_editor_property("b", False)
    h_r.set_editor_property("a", False)
    lib.connect_unary(h_s, h_r)

    eff_scale = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -800, 200)
    lib.connect(scale_in, "", eff_scale, "A")
    lib.connect(layer_in, "", eff_scale, "B")
    eff_scale2 = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -640, 200)
    lib.connect(eff_scale, "", eff_scale2, "A")
    lib.connect(height_in, "", eff_scale2, "B")
    pom_s = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -800, 40)
    lib.connect(h_r, "", pom_s, "A")
    lib.connect(eff_scale2, "", pom_s, "B")
    pom_s2 = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -640, 40)
    lib.connect(pom_s, "", pom_s2, "A")
    lib.connect(str_in, "", pom_s2, "B")

    view_xy = _view_xy(mf, -1120, 320)
    off_simple = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -480, 120)
    lib.connect(pom_s2, "", off_simple, "A")
    lib.connect(view_xy, "", off_simple, "B")

    steep_mul = lib.create_expression(mf, unreal.MaterialExpressionConstant, -640, 280)
    steep_mul.set_editor_property("r", 1.75)
    off_steep = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -480, 280)
    lib.connect(off_simple, "", off_steep, "A")
    lib.connect(steep_mul, "", off_steep, "B")

    uv_pre = lib.create_expression(mf, unreal.MaterialExpressionAdd, -320, 120)
    lib.connect(uv_in, "", uv_pre, "A")
    lib.connect(off_simple, "", uv_pre, "B")
    h_s2 = lib.create_expression(mf, unreal.MaterialExpressionTextureSample, -1120, 520)
    lib.connect_any(ht_in, h_s2, ("Tex", "TextureObject"))
    lib.connect_any(uv_pre, h_s2, ("UVs", "Coordinates"))
    h_r2 = lib.create_expression(mf, unreal.MaterialExpressionComponentMask, -960, 520)
    h_r2.set_editor_property("r", True)
    h_r2.set_editor_property("g", False)
    h_r2.set_editor_property("b", False)
    h_r2.set_editor_property("a", False)
    lib.connect_unary(h_s2, h_r2)
    h_blend = lib.create_expression(mf, unreal.MaterialExpressionAdd, -800, 480)
    lib.connect(h_r, "", h_blend, "A")
    lib.connect(h_r2, "", h_blend, "B")
    half = lib.create_expression(mf, unreal.MaterialExpressionConstant, -960, 620)
    half.set_editor_property("r", 0.5)
    h_avg = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -640, 500)
    lib.connect(h_blend, "", h_avg, "A")
    lib.connect(half, "", h_avg, "B")
    steps_norm = lib.create_expression(mf, unreal.MaterialExpressionConstant, -800, 640)
    steps_norm.set_editor_property("r", 0.125)
    steps_mul = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -640, 640)
    lib.connect(steps_in, "", steps_mul, "A")
    lib.connect(steps_norm, "", steps_mul, "B")
    pom_pom = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -480, 500)
    lib.connect(h_avg, "", pom_pom, "A")
    lib.connect(eff_scale2, "", pom_pom, "B")
    pom_pom2 = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -320, 500)
    lib.connect(pom_pom, "", pom_pom2, "A")
    lib.connect(str_in, "", pom_pom2, "B")
    pom_pom3 = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -160, 500)
    lib.connect(pom_pom2, "", pom_pom3, "A")
    lib.connect(steps_mul, "", pom_pom3, "B")
    off_pom = lib.create_expression(mf, unreal.MaterialExpressionMultiply, 0, 500)
    lib.connect(pom_pom3, "", off_pom, "A")
    lib.connect(view_xy, "", off_pom, "B")

    blend_01 = lib.create_expression(mf, unreal.MaterialExpressionSaturate, -320, 840)
    lib.connect_unary(mode_in, blend_01)
    mode_12 = lib.create_expression(mf, unreal.MaterialExpressionSubtract, -480, 920)
    one = lib.create_expression(mf, unreal.MaterialExpressionConstant, -640, 920)
    one.set_editor_property("r", 1.0)
    lib.connect(mode_in, "", mode_12, "A")
    lib.connect(one, "", mode_12, "B")
    blend_12 = lib.create_expression(mf, unreal.MaterialExpressionSaturate, -320, 920)
    lib.connect_unary(mode_12, blend_12)
    off_01 = lib.create_expression(mf, unreal.MaterialExpressionLinearInterpolate, 160, 200)
    lib.connect(off_simple, "", off_01, "A")
    lib.connect(off_steep, "", off_01, "B")
    lib.connect(blend_01, "", off_01, "Alpha")
    off_final = lib.create_expression(mf, unreal.MaterialExpressionLinearInterpolate, 320, 360)
    lib.connect(off_01, "", off_final, "A")
    lib.connect(off_pom, "", off_final, "B")
    lib.connect(blend_12, "", off_final, "Alpha")
    uv_out = lib.create_expression(mf, unreal.MaterialExpressionAdd, 480, 360)
    lib.connect(uv_in, "", uv_out, "A")
    lib.connect(off_final, "", uv_out, "B")
    _add_function_output(mf, uv_out, "UV", 640, 360)


def _build_normal_adjust(mf: unreal.MaterialFunction) -> None:
    """Unpack normal map, scale XY, power Z, per-layer strength."""
    n_in = _fn_input(mf, "Normal", -1000, 0, sort=0)
    str_in = _fn_input(mf, "NormalStrength", -1000, 120, sort=1)
    pow_in = _fn_input(mf, "NormalPower", -1000, 240, sort=2)
    layer_in = _fn_input(mf, "LayerNormalStrength", -1000, 360, sort=3)

    two = lib.create_expression(mf, unreal.MaterialExpressionConstant, -800, 80)
    two.set_editor_property("r", 2.0)
    n_unpk = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -640, 40)
    lib.connect(n_in, "", n_unpk, "A")
    lib.connect(two, "", n_unpk, "B")
    one = lib.create_expression(mf, unreal.MaterialExpressionConstant, -800, 160)
    one.set_editor_property("r", 1.0)
    n_off = lib.create_expression(mf, unreal.MaterialExpressionSubtract, -480, 40)
    lib.connect(n_unpk, "", n_off, "A")
    lib.connect(one, "", n_off, "B")

    eff_str = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -640, 280)
    lib.connect(str_in, "", eff_str, "A")
    lib.connect(layer_in, "", eff_str, "B")
    n_xy = lib.create_expression(mf, unreal.MaterialExpressionComponentMask, -320, 0)
    n_xy.set_editor_property("r", True)
    n_xy.set_editor_property("g", True)
    n_xy.set_editor_property("b", False)
    n_xy.set_editor_property("a", False)
    lib.connect_unary(n_off, n_xy)
    n_z = lib.create_expression(mf, unreal.MaterialExpressionComponentMask, -320, 120)
    n_z.set_editor_property("r", False)
    n_z.set_editor_property("g", False)
    n_z.set_editor_property("b", True)
    n_z.set_editor_property("a", False)
    lib.connect_unary(n_off, n_z)
    xy_s = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -160, 0)
    lib.connect(n_xy, "", xy_s, "A")
    lib.connect(eff_str, "", xy_s, "B")
    half = lib.create_expression(mf, unreal.MaterialExpressionConstant, -480, 200)
    half.set_editor_property("r", 0.5)
    z_pos = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -320, 200)
    lib.connect(n_z, "", z_pos, "A")
    lib.connect(half, "", z_pos, "B")
    z_pos2 = lib.create_expression(mf, unreal.MaterialExpressionAdd, -160, 200)
    lib.connect(z_pos, "", z_pos2, "A")
    lib.connect(half, "", z_pos2, "B")
    z_sat = lib.create_expression(mf, unreal.MaterialExpressionSaturate, 0, 200)
    lib.connect_unary(z_pos2, z_sat)
    z_pow = lib.create_expression(mf, unreal.MaterialExpressionPower, 160, 200)
    lib.connect(z_sat, "", z_pow, "Base")
    lib.connect(pow_in, "", z_pow, "Exp")
    z_back = lib.create_expression(mf, unreal.MaterialExpressionMultiply, 320, 200)
    lib.connect(z_pow, "", z_back, "A")
    lib.connect(two, "", z_back, "B")
    z_final = lib.create_expression(mf, unreal.MaterialExpressionSubtract, 480, 200)
    lib.connect(z_back, "", z_final, "A")
    lib.connect(one, "", z_final, "B")
    n_ts = lib.create_expression(mf, unreal.MaterialExpressionAppendVector, 320, 40)
    lib.connect_append2(xy_s, z_final, n_ts)
    len_n = lib.create_expression(mf, unreal.MaterialExpressionSquareRoot, 640, 80)
    dot = lib.create_expression(mf, unreal.MaterialExpressionDotProduct, 480, 80)
    lib.connect(n_ts, "", dot, "A")
    lib.connect(n_ts, "", dot, "B")
    lib.connect_unary(dot, len_n)
    eps = lib.create_expression(mf, unreal.MaterialExpressionConstant, 480, 180)
    eps.set_editor_property("r", 0.001)
    len_safe = lib.create_expression(mf, unreal.MaterialExpressionAdd, 640, 180)
    lib.connect(len_n, "", len_safe, "A")
    lib.connect(eps, "", len_safe, "B")
    n_norm = lib.create_expression(mf, unreal.MaterialExpressionDivide, 800, 80)
    lib.connect(n_ts, "", n_norm, "A")
    lib.connect(len_safe, "", n_norm, "B")
    half_v = lib.create_expression(mf, unreal.MaterialExpressionConstant, 800, 200)
    half_v.set_editor_property("r", 0.5)
    n_pack = lib.create_expression(mf, unreal.MaterialExpressionMultiply, 960, 80)
    lib.connect(n_norm, "", n_pack, "A")
    lib.connect(half_v, "", n_pack, "B")
    n_pack2 = lib.create_expression(mf, unreal.MaterialExpressionAdd, 1120, 80)
    lib.connect(n_pack, "", n_pack2, "A")
    lib.connect(half_v, "", n_pack2, "B")
    _add_function_output(mf, n_pack2, "Normal", 1280, 80)


def _build_sdf_band(mf: unreal.MaterialFunction) -> None:
    world = lib.create_expression(mf, unreal.MaterialExpressionWorldPosition, -900, 0)
    mask_xy = lib.create_expression(mf, unreal.MaterialExpressionComponentMask, -720, 0)
    mask_xy.set_editor_property("r", True)
    mask_xy.set_editor_property("g", True)
    mask_xy.set_editor_property("b", False)
    mask_xy.set_editor_property("a", False)
    lib.connect(world, "", mask_xy, "")
    band_scale = lib.scalar_param(mf, "BandScale", "SDF", 0.035, -900, 120)
    band_strength = lib.scalar_param(mf, "BandStrength", "SDF", 0.22, -900, 220)
    scale_mul = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -540, 40)
    lib.connect(mask_xy, "", scale_mul, "A")
    lib.connect(band_scale, "", scale_mul, "B")
    sin_n = lib.create_expression(mf, unreal.MaterialExpressionSine, -360, 40)
    sin_n.set_editor_property("period", 1.0)
    lib.connect_unary(scale_mul, sin_n)
    abs_n = lib.create_expression(mf, unreal.MaterialExpressionAbs, -180, 40)
    lib.connect_unary(sin_n, abs_n)
    out = lib.create_expression(mf, unreal.MaterialExpressionMultiply, 0, 40)
    lib.connect(abs_n, "", out, "A")
    lib.connect(band_strength, "", out, "B")
    _add_function_output(mf, out, "Result", 180, 40)


def _build_madoka(mf: unreal.MaterialFunction) -> None:
    """Witch-barrier voronoi veins + cute/corrupt tint. Phase 1: no Blur node
    (the sigma-8 full-screen Blur on a 600+ node master was the likely cause
    of the prior catastrophic rebuild failure) — cheap DDX/DDY edge approx instead.
    """
    world = lib.create_expression(mf, unreal.MaterialExpressionWorldPosition, -900, 0)
    mask_xy = lib.create_expression(mf, unreal.MaterialExpressionComponentMask, -720, 0)
    mask_xy.set_editor_property("r", True)
    mask_xy.set_editor_property("g", True)
    mask_xy.set_editor_property("b", False)
    mask_xy.set_editor_property("a", False)
    lib.connect(world, "", mask_xy, "")

    wallpaper_scale = lib.scalar_param(mf, "WitchBarrierWallpaperScale", "Madoka", 4.0, -900, 140)
    glow_amount = lib.scalar_param(mf, "MadokaGlowAmount", "Madoka", 0.0, -900, 240)
    vein_emissive = lib.scalar_param(mf, "MadokaVeinEmissive", "Madoka", 0.0, -900, 340)
    cute_bias = lib.scalar_param(mf, "MadokaCuteBias", "Madoka", 0.5, -900, 440)
    emissive_bright = lib.scalar_param(mf, "MadokaEmissiveBrightness", "Madoka", 0.0, -900, 540)

    scaled = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -540, 0)
    lib.connect(mask_xy, "", scaled, "A")
    lib.connect(wallpaper_scale, "", scaled, "B")
    voronoi = lib.create_expression(mf, unreal.MaterialExpressionNoise, -380, 0)
    lib.connect(scaled, "", voronoi, "Position")
    voronoi_sat = lib.create_expression(mf, unreal.MaterialExpressionSaturate, -220, 0)
    lib.connect_unary(voronoi, voronoi_sat)

    ddx = lib.create_expression(mf, unreal.MaterialExpressionDDX, -220, 140)
    ddy = lib.create_expression(mf, unreal.MaterialExpressionDDY, -220, 240)
    lib.connect_unary(voronoi_sat, ddx)
    lib.connect_unary(voronoi_sat, ddy)
    ddx_abs = lib.create_expression(mf, unreal.MaterialExpressionAbs, -60, 140)
    ddy_abs = lib.create_expression(mf, unreal.MaterialExpressionAbs, -60, 240)
    lib.connect_unary(ddx, ddx_abs)
    lib.connect_unary(ddy, ddy_abs)
    veins = lib.create_expression(mf, unreal.MaterialExpressionAdd, 100, 190)
    lib.connect(ddx_abs, "", veins, "A")
    lib.connect(ddy_abs, "", veins, "B")

    vein_glow = lib.create_expression(mf, unreal.MaterialExpressionMultiply, 260, 190)
    lib.connect(veins, "", vein_glow, "A")
    lib.connect(vein_emissive, "", vein_glow, "B")

    cute_color = lib.create_expression(mf, unreal.MaterialExpressionConstant3Vector, -540, 420)
    cute_color.set_editor_property("constant", unreal.LinearColor(0.92, 0.55, 0.88, 1.0))
    corrupt_color = lib.create_expression(mf, unreal.MaterialExpressionConstant3Vector, -540, 540)
    corrupt_color.set_editor_property("constant", unreal.LinearColor(0.55, 0.12, 0.18, 1.0))
    tint_mix = lib.create_expression(mf, unreal.MaterialExpressionLinearInterpolate, -340, 480)
    lib.connect(corrupt_color, "", tint_mix, "A")
    lib.connect(cute_color, "", tint_mix, "B")
    lib.connect(cute_bias, "", tint_mix, "Alpha")

    color_out = lib.create_expression(mf, unreal.MaterialExpressionMultiply, 100, 420)
    lib.connect(tint_mix, "", color_out, "A")
    lib.connect(voronoi_sat, "", color_out, "B")

    glow_base = lib.create_expression(mf, unreal.MaterialExpressionMultiply, 100, 560)
    lib.connect(tint_mix, "", glow_base, "A")
    lib.connect(glow_amount, "", glow_base, "B")
    emissive_scaled = lib.create_expression(mf, unreal.MaterialExpressionMultiply, 420, 280)
    lib.connect(vein_glow, "", emissive_scaled, "A")
    lib.connect(emissive_bright, "", emissive_scaled, "B")
    emissive_out = lib.create_expression(mf, unreal.MaterialExpressionAdd, 580, 380)
    lib.connect(emissive_scaled, "", emissive_out, "A")
    lib.connect(glow_base, "", emissive_out, "B")

    _add_function_output(mf, color_out, "Color", 280, 420)
    _add_function_output(mf, emissive_out, "Emissive", 740, 380)


def _build_itto(mf: unreal.MaterialFunction) -> None:
    """Truchet-style crack + wear roughness add. Phase 1 only — IttoInkStrength/
    IttoErosionStrength/IttoWearDepth deliberately deferred (height+ink pass),
    same as the project's existing Impressionist-ink deferral pattern.
    """
    world = lib.create_expression(mf, unreal.MaterialExpressionWorldPosition, -700, 0)
    mask_xy = lib.create_expression(mf, unreal.MaterialExpressionComponentMask, -540, 0)
    mask_xy.set_editor_property("r", True)
    mask_xy.set_editor_property("g", True)
    mask_xy.set_editor_property("b", False)
    mask_xy.set_editor_property("a", False)
    lib.connect(world, "", mask_xy, "")

    pattern_scale = lib.scalar_param(mf, "IttoPatternScale", "Itto", 3.0, -700, 140)
    crack_depth = lib.scalar_param(mf, "IttoCrackDepth", "Itto", 0.0, -700, 240)
    wear_amount = lib.scalar_param(mf, "IttoWearAmount", "Itto", 0.0, -700, 340)

    scaled = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -360, 0)
    lib.connect(mask_xy, "", scaled, "A")
    lib.connect(pattern_scale, "", scaled, "B")
    truchet = lib.create_expression(mf, unreal.MaterialExpressionNoise, -200, 0)
    lib.connect(scaled, "", truchet, "Position")
    truchet_sat = lib.create_expression(mf, unreal.MaterialExpressionSaturate, -40, 0)
    lib.connect_unary(truchet, truchet_sat)

    ddx = lib.create_expression(mf, unreal.MaterialExpressionDDX, -40, 140)
    ddy = lib.create_expression(mf, unreal.MaterialExpressionDDY, -40, 240)
    lib.connect_unary(truchet_sat, ddx)
    lib.connect_unary(truchet_sat, ddy)
    ddx_abs = lib.create_expression(mf, unreal.MaterialExpressionAbs, 120, 140)
    ddy_abs = lib.create_expression(mf, unreal.MaterialExpressionAbs, 120, 240)
    lib.connect_unary(ddx, ddx_abs)
    lib.connect_unary(ddy, ddy_abs)
    cracks = lib.create_expression(mf, unreal.MaterialExpressionAdd, 280, 190)
    lib.connect(ddx_abs, "", cracks, "A")
    lib.connect(ddy_abs, "", cracks, "B")
    crack_mask = lib.create_expression(mf, unreal.MaterialExpressionMultiply, 440, 190)
    lib.connect(cracks, "", crack_mask, "A")
    lib.connect(crack_depth, "", crack_mask, "B")

    wear = lib.create_expression(mf, unreal.MaterialExpressionMultiply, 120, 380)
    lib.connect(truchet_sat, "", wear, "A")
    lib.connect(wear_amount, "", wear, "B")

    roughness_add = lib.create_expression(mf, unreal.MaterialExpressionAdd, 600, 290)
    lib.connect(crack_mask, "", roughness_add, "A")
    lib.connect(wear, "", roughness_add, "B")
    _add_function_output(mf, roughness_add, "RoughnessAdd", 760, 290)


BUILDERS = {
    "MF_UVTransform": _build_uv_transform,
    "MF_RealParallax": _build_real_parallax,
    "MF_CurvatureOrnament": _build_curvature_ornament,
    "MF_Impressionist_BrushStroke": _build_brush_stroke,
    "MF_Impressionist_Impasto": _build_impasto,
    "MF_Impressionist_Temporal": _build_temporal,
    "MF_Impressionist_InkPool": _build_ink_pool,
    "MF_AudioReactiveBlend": _build_audio_blend,
    "MF_GildingOverlay": _build_gilding,
    "MF_MapComposite": _build_map_composite,
    "MF_SDF_BandRelief": _build_sdf_band,
    "MF_AnimeSkinWrap": _build_anime_skin_wrap,
    "MF_ParallaxCore": _build_parallax_core,
    "MF_NormalAdjust": _build_normal_adjust,
    "MF_Madoka": _build_madoka,
    "MF_Itto": _build_itto,
}


def build_all(*, force: bool = False) -> list[str]:
    unreal.log("=== Building material function library ===")
    created: list[str] = []
    for name, _desc in MF_SPECS:
        try:
            builder = BUILDERS[name]
            mf = _create_or_rebuild_mf(name, force=force)
            exprs = []
            try:
                exprs = list(unreal.MaterialEditingLibrary.get_function_expressions(mf) or [])
            except Exception:
                pass
            if force or not exprs:
                builder(mf)
                try:
                    unreal.MaterialEditingLibrary.recompile_material_function(mf)
                except Exception:
                    pass
                lib.save_package(mf)
            path = lib.asset_path(lib.FUNCTION_DIR, name)
            created.append(path)
            unreal.log(f"[MF] built {path}")
        except Exception as exc:
            unreal.log_warning(f"[MF] skip {name}: {exc}")
    return created


def main() -> int:
    force = "--force" in sys.argv
    paths = build_all(force=force)
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "functions": paths,
        "count": len(paths),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"[MF] complete: {len(paths)} functions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
