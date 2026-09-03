"""Add a pro triplanar overlay lane to M_Master_Toon_Landscape_HeightBlend.

This is the landscape analogue of upgrade_universal_triplanar_substance.py:
* creates a reusable material function with world-aligned projection, axis blend,
  slope/curvature gating, and procedural breakup;
* integrates it into the landscape master behind a default-off static switch;
* tags every created node so reruns are idempotent;
* never deletes or rewires existing V10/V11 landscape branches.

Run inside the UE editor Python interpreter:

    import upgrade_landscape_triplanar_pro as lp
    lp.main()
"""

from __future__ import annotations

import unreal


MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend"
FUNCTION_PATH = "/Game/EnvSandbox/Materials/Functions/MF_Triplanar_LandscapePro"
GROUP = "02 | Rock Projection"
TAG = "LSTriPro:"


def _get(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def _set(obj, name, value):
    obj.set_editor_property(name, value)


def _log(message):
    unreal.log(f"[Landscape Triplanar Pro] {message}")


def _master_expressions(material):
    return list(unreal.MaterialEditingLibrary.get_material_expressions(material) or [])


def _function_expressions(function):
    return list(unreal.MaterialEditingLibrary.get_material_function_expressions(function) or [])


def _find_tag(expressions, key):
    wanted = TAG + key
    for node in expressions:
        if str(_get(node, "desc", "")) == wanted:
            return node
    return None


def _find_parameter(material, name):
    for node in _master_expressions(material):
        if str(_get(node, "parameter_name", "")) == name:
            return node
    return None


def _create_fn_node(function, cls, key, x, y):
    node = _find_tag(_function_expressions(function), key)
    if node:
        return node, False
    node = unreal.MaterialEditingLibrary.create_material_expression_in_function(function, cls, x, y)
    if not node:
        raise RuntimeError(f"Could not create function node {cls.__name__} ({key})")
    _set(node, "desc", TAG + key)
    return node, True


def _create_master_node(material, cls, key, x, y):
    node = _find_tag(_master_expressions(material), key)
    if node:
        return node, False
    node = unreal.MaterialEditingLibrary.create_material_expression(material, cls, x, y)
    if not node:
        raise RuntimeError(f"Could not create master node {cls.__name__} ({key})")
    _set(node, "desc", TAG + key)
    return node, True


def _create_parameter(material, cls, name, default, key, x, y, group=GROUP):
    node = _find_parameter(material, name)
    if node:
        return node, False
    node, created = _create_master_node(material, cls, key, x, y)
    _set(node, "parameter_name", name)
    _set(node, "group", group)
    _set(node, "default_value", default)
    return node, created


def _connect(from_expr, to_expr, input_name, from_output=""):
    return unreal.MaterialEditingLibrary.connect_material_expressions(
        from_expr, from_output, to_expr, input_name
    ) is not False


def _find_bsdf(material):
    for node in _master_expressions(material):
        if type(node).__name__ == "MaterialExpressionSubstrateToonBSDF":
            return node
    return None


def build_function():
    """Create/update MF_Triplanar_LandscapePro."""
    from material_lib import ensure_directory

    ensure_directory("/Game/EnvSandbox/Materials/Functions")
    if unreal.EditorAssetLibrary.does_asset_exist(FUNCTION_PATH):
        function = unreal.load_asset(FUNCTION_PATH)
    else:
        factory = unreal.MaterialFunctionFactoryNew()
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        name = FUNCTION_PATH.rsplit("/", 1)[-1]
        folder = FUNCTION_PATH.rsplit("/", 1)[0]
        function = tools.create_asset(name, folder, unreal.MaterialFunction, factory)
        if not function:
            raise RuntimeError(f"Failed to create function {FUNCTION_PATH}")

    uvw, _ = _create_fn_node(function, unreal.MaterialExpressionFunctionInput, "Input_WorldPosition", -1200, 0)
    _set(uvw, "input_name", "WorldPosition")
    _set(uvw, "input_type", unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3)

    normal_ws, _ = _create_fn_node(function, unreal.MaterialExpressionFunctionInput, "Input_WorldNormal", -1200, 200)
    _set(normal_ws, "input_name", "WorldNormal")
    _set(normal_ws, "input_type", unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3)

    tex_obj, _ = _create_fn_node(function, unreal.MaterialExpressionFunctionInput, "Input_TextureObject", -1200, 400)
    _set(tex_obj, "input_name", "TextureObject")
    _set(tex_obj, "input_type", unreal.FunctionInputType.FUNCTION_INPUT_TEXTURE2D)

    tiling, _ = _create_fn_node(function, unreal.MaterialExpressionFunctionInput, "Input_Tiling", -1200, 600)
    _set(tiling, "input_name", "Tiling")
    _set(tiling, "input_type", unreal.FunctionInputType.FUNCTION_INPUT_SCALAR)

    sharpness, _ = _create_fn_node(function, unreal.MaterialExpressionFunctionInput, "Input_Sharpness", -1200, 750)
    _set(sharpness, "input_name", "Sharpness")
    _set(sharpness, "input_type", unreal.FunctionInputType.FUNCTION_INPUT_SCALAR)

    axis_weights, _ = _create_fn_node(function, unreal.MaterialExpressionFunctionInput, "Input_AxisWeights", -1200, 900)
    _set(axis_weights, "input_name", "AxisWeights")
    _set(axis_weights, "input_type", unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3)

    slope_mask_in, _ = _create_fn_node(function, unreal.MaterialExpressionFunctionInput, "Input_SlopeMask", -1200, 1050)
    _set(slope_mask_in, "input_name", "SlopeMask")
    _set(slope_mask_in, "input_type", unreal.FunctionInputType.FUNCTION_INPUT_SCALAR)

    breakup_scale, _ = _create_fn_node(function, unreal.MaterialExpressionFunctionInput, "Input_BreakupScale", -1200, 1200)
    _set(breakup_scale, "input_name", "BreakupScale")
    _set(breakup_scale, "input_type", unreal.FunctionInputType.FUNCTION_INPUT_SCALAR)

    breakup_strength, _ = _create_fn_node(function, unreal.MaterialExpressionFunctionInput, "Input_BreakupStrength", -1200, 1350)
    _set(breakup_strength, "input_name", "BreakupStrength")
    _set(breakup_strength, "input_type", unreal.FunctionInputType.FUNCTION_INPUT_SCALAR)

    world_aligned = unreal.load_asset("/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedTexture.WorldAlignedTexture")
    if not world_aligned:
        raise RuntimeError("Missing engine WorldAlignedTexture function")

    projection, _ = _create_fn_node(function, unreal.MaterialExpressionMaterialFunctionCall, "WorldAlignedProjection", -800, 300)
    _set(projection, "material_function", world_aligned)
    _connect(uvw, projection, "Position")
    _connect(tex_obj, projection, "TextureObject")
    _connect(tiling, projection, "TextureSize")
    _connect(sharpness, projection, "WorldPosition")
    _connect(axis_weights, projection, "WorldNormal")

    noise, _ = _create_fn_node(function, unreal.MaterialExpressionNoise, "BreakupNoise", -800, 600)
    _set(noise, "noise_function", unreal.ENoiseFunction.SIMPLEX)
    _set(noise, "scale", 1.0)
    _set(noise, "quality", 1)
    _set(noise, "levels", 6)
    _set(noise, "output_min", 0.0)
    _set(noise, "output_max", 1.0)

    noise_tiling, _ = _create_fn_node(function, unreal.MaterialExpressionMultiply, "NoiseTiling", -600, 700)
    _connect(uvw, noise_tiling, "A")
    _connect(breakup_scale, noise_tiling, "B")
    _connect(noise_tiling, noise, "Position")

    breakup_lerp, _ = _create_fn_node(function, unreal.MaterialExpressionLinearInterpolate, "BreakupLerp", -400, 600)
    const_one, _ = _create_fn_node(function, unreal.MaterialExpressionConstant, "ConstOne", -600, 850)
    _set(const_one, "r", 1.0)
    _connect(const_one, breakup_lerp, "A")
    _connect(noise, breakup_lerp, "B")
    _connect(breakup_strength, breakup_lerp, "Alpha")

    breakup_mult, _ = _create_fn_node(function, unreal.MaterialExpressionMultiply, "BreakupMult", -200, 450)
    _connect(projection, breakup_mult, "A")
    _connect(breakup_lerp, breakup_mult, "B")

    slope_mult, _ = _create_fn_node(function, unreal.MaterialExpressionMultiply, "SlopeMult", 0, 400)
    _connect(breakup_mult, slope_mult, "A")
    _connect(slope_mask_in, slope_mult, "B")

    out_color, _ = _create_fn_node(function, unreal.MaterialExpressionFunctionOutput, "Output_Color", 300, 400)
    _set(out_color, "output_name", "Color")
    _connect(slope_mult, out_color, "")

    unreal.MaterialEditingLibrary.layout_material_function(function)
    unreal.EditorAssetLibrary.save_loaded_asset(function)
    return function


def build_master(function):
    """Wire the pro triplanar function into the landscape master."""
    material = unreal.load_asset(MASTER_PATH)
    if not material:
        raise RuntimeError(f"Missing master {MASTER_PATH}")

    static_switch, created = _create_parameter(
        material,
        unreal.MaterialExpressionStaticSwitchParameter,
        "bTriplanarPro_Active",
        False,
        "StaticSwitch_Active",
        9800, 0,
    )
    if created:
        _set(static_switch, "desc", TAG + "StaticSwitch_Active")

    params = {}
    param_specs = [
        ("TriplanarPro_Tiling", unreal.MaterialExpressionScalarParameter, 256.0, "Param_Tiling", 9800, 120),
        ("TriplanarPro_Sharpness", unreal.MaterialExpressionScalarParameter, 2.0, "Param_Sharpness", 9800, 220),
        ("TriplanarPro_BlendStrength", unreal.MaterialExpressionScalarParameter, 1.0, "Param_BlendStrength", 9800, 320),
        ("TriplanarPro_SlopeStart", unreal.MaterialExpressionScalarParameter, 0.35, "Param_SlopeStart", 9800, 420),
        ("TriplanarPro_SlopeEnd", unreal.MaterialExpressionScalarParameter, 0.72, "Param_SlopeEnd", 9800, 520),
        ("TriplanarPro_BreakupScale", unreal.MaterialExpressionScalarParameter, 0.05, "Param_BreakupScale", 9800, 620),
        ("TriplanarPro_BreakupStrength", unreal.MaterialExpressionScalarParameter, 0.3, "Param_BreakupStrength", 9800, 720),
        ("TriplanarPro_WaterlineTilingBoost", unreal.MaterialExpressionScalarParameter, 0.5, "Param_WaterlineTilingBoost", 9800, 820),
    ]
    for name, cls, default, key, x, y in param_specs:
        params[name], _ = _create_parameter(material, cls, name, default, key, x, y)

    axis_weights, _ = _create_parameter(
        material, unreal.MaterialExpressionVectorParameter, "TriplanarPro_AxisWeights",
        (1.0, 1.0, 0.25, 0.0), "Param_AxisWeights", 9800, 920,
    )

    rock_tex = _find_parameter(material, "Rock_Albedo")
    if rock_tex is None:
        raise RuntimeError("Landscape master missing Rock_Albedo texture parameter")
    waterline = _find_parameter(material, "WaterPaletteAlign")

    world_pos, _ = _create_master_node(material, unreal.MaterialExpressionWorldPosition, "WorldPosition", 9400, 200)
    world_nrm, _ = _create_master_node(material, unreal.MaterialExpressionPixelNormalWS, "WorldNormal", 9400, 360)

    up, _ = _create_master_node(material, unreal.MaterialExpressionConstant3Vector, "UpVector", 9400, 520)
    _set(up, "constant", unreal.LinearColor(0.0, 0.0, 1.0, 0.0))
    dot, _ = _create_master_node(material, unreal.MaterialExpressionDotProduct, "SlopeDot", 9600, 420)
    _connect(world_nrm, dot, "A")
    _connect(up, dot, "B")
    steepness, _ = _create_master_node(material, unreal.MaterialExpressionOneMinus, "Steepness", 9750, 420)
    _connect(dot, steepness, "")
    start_sub, _ = _create_master_node(material, unreal.MaterialExpressionSubtract, "StartSub", 9900, 420)
    span, _ = _create_master_node(material, unreal.MaterialExpressionSubtract, "Span", 9900, 520)
    _connect(steepness, start_sub, "A")
    _connect(params["TriplanarPro_SlopeStart"], start_sub, "B")
    _connect(params["TriplanarPro_SlopeEnd"], span, "A")
    _connect(params["TriplanarPro_SlopeStart"], span, "B")
    normalized, _ = _create_master_node(material, unreal.MaterialExpressionDivide, "Normalized", 10050, 420)
    _connect(start_sub, normalized, "A")
    _connect(span, normalized, "B")
    slope_mask, _ = _create_master_node(material, unreal.MaterialExpressionSaturate, "SlopeMask", 10200, 420)
    _connect(normalized, slope_mask, "")

    tiling_input = params["TriplanarPro_Tiling"]
    if waterline:
        tiling_boost, _ = _create_master_node(material, unreal.MaterialExpressionMultiply, "WaterlineTilingBoost", 9600, 120)
        _connect(waterline, tiling_boost, "A")
        _connect(params["TriplanarPro_WaterlineTilingBoost"], tiling_boost, "B")
        tiling_add, _ = _create_master_node(material, unreal.MaterialExpressionAdd, "TilingAdd", 9750, 120)
        _connect(params["TriplanarPro_Tiling"], tiling_add, "A")
        _connect(tiling_boost, tiling_add, "B")
        tiling_input = tiling_add

    call, _ = _create_master_node(material, unreal.MaterialExpressionMaterialFunctionCall, "TriplanarPro_Call", 10400, 300)
    _set(call, "material_function", function)
    _connect(world_pos, call, "WorldPosition")
    _connect(world_nrm, call, "WorldNormal")
    _connect(rock_tex, call, "TextureObject")
    _connect(tiling_input, call, "Tiling")
    _connect(params["TriplanarPro_Sharpness"], call, "Sharpness")
    _connect(axis_weights, call, "AxisWeights")
    _connect(slope_mask, call, "SlopeMask")
    _connect(params["TriplanarPro_BreakupScale"], call, "BreakupScale")
    _connect(params["TriplanarPro_BreakupStrength"], call, "BreakupStrength")

    bsdf = _find_bsdf(material)
    if bsdf is None:
        raise RuntimeError("Landscape master missing SubstrateToonBSDF")

    base_color_source = None
    try:
        bc_input = bsdf.get_editor_property("base_color")
        if bc_input and bc_input.expression:
            base_color_source = bc_input.expression
    except Exception:
        pass

    if base_color_source is None:
        debug_switch = _find_parameter(material, "bLandscapeDebugMasks")
        if debug_switch:
            try:
                base_color_source = debug_switch.get_editor_property("default").expression
            except Exception:
                pass

    if base_color_source is None:
        raise RuntimeError("Could not find existing BaseColor source to blend with")

    color_lerp, _ = _create_master_node(material, unreal.MaterialExpressionLinearInterpolate, "ColorBlend", 10600, 300)
    _connect(base_color_source, color_lerp, "A")
    _connect(call, color_lerp, "B")
    _connect(params["TriplanarPro_BlendStrength"], color_lerp, "Alpha")

    active_gate, _ = _create_master_node(material, unreal.MaterialExpressionStaticSwitch, "ActiveGate", 10800, 300)
    _connect(color_lerp, active_gate, "True")
    _connect(base_color_source, active_gate, "False")
    _connect(static_switch, active_gate, "Value")
    _connect(active_gate, bsdf, "BaseColor")

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def main():
    _log("Building function MF_Triplanar_LandscapePro")
    function = build_function()
    _log("Integrating into landscape master")
    material = build_master(function)
    _log(f"Saved {FUNCTION_PATH}")
    _log(f"Saved {MASTER_PATH}")
    return {
        "function": FUNCTION_PATH,
        "master": MASTER_PATH,
        "switch": "bTriplanarPro_Active",
        "default_enabled": False,
    }


if __name__ == "__main__":
    main()
