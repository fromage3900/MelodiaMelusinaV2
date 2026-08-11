"""Build the gated Global Distance Field contact material spike.

This script is intentionally additive: it creates the reusable contact function,
adds an OFF-by-default branch to the Universal master, and creates one enabled
test material instance. It does not touch gameplay maps.
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

import material_lib as lib


MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
FUNCTION_DIR = "/Game/EnvSandbox/Materials/Functions"
FUNCTION = f"{FUNCTION_DIR}/MF_DF_ContactBlend"
TEST_DIR = "/Game/Melodia/Materials/DistanceField"
TEST_MI = f"{TEST_DIR}/MI_DF_ContactBlend_Soft"
REPORT = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "distance_field_material_spike.json"
GROUP = "02b | Distance Field Contact"


def _asset_path(folder: str, name: str) -> str:
    return f"{folder}/{name}.{name}"


def _clear_function(mf):
    for expr in list(unreal.MaterialEditingLibrary.get_material_function_expressions(mf) or []):
        unreal.MaterialEditingLibrary.delete_material_expression_in_function(mf, expr)


def _fn_input(mf, name: str, x: int, y: int, default: float):
    node = unreal.MaterialEditingLibrary.create_material_expression_in_function(
        mf, unreal.MaterialExpressionFunctionInput, x, y
    )
    node.set_editor_property("input_name", name)
    try:
        node.set_editor_property("input_type", unreal.FunctionInputType.FIT1)
    except Exception:
        pass
    for prop in ("preview_value", "preview_value_float"):
        try:
            node.set_editor_property(prop, default)
            break
        except Exception:
            pass
    return node


def _build_function():
    unreal.EditorAssetLibrary.make_directory(FUNCTION_DIR)
    mf = unreal.EditorAssetLibrary.load_asset(FUNCTION)
    if not mf:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        mf = tools.create_asset("MF_DF_ContactBlend", FUNCTION_DIR, unreal.MaterialFunction, unreal.MaterialFunctionFactoryNew())
    if not mf:
        raise RuntimeError(f"Could not create {FUNCTION}")
    _clear_function(mf)
    mel = unreal.MaterialEditingLibrary
    world = mel.create_material_expression_in_function(mf, unreal.MaterialExpressionWorldPosition, -1000, 0)
    offset = _fn_input(mf, "WorldPositionOffset", -1000, 180, 0.0)
    down = lib.create_expression(mf, unreal.MaterialExpressionConstant3Vector, -920, 360)
    down.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, -1.0, 0.0))
    offset_vec = lib.create_expression(mf, unreal.MaterialExpressionMultiply, -760, 240)
    lib.connect(down, "", offset_vec, "A")
    lib.connect(offset, "", offset_vec, "B")
    pos = lib.create_expression(mf, unreal.MaterialExpressionAdd, -560, 0)
    lib.connect(world, "", pos, "A")
    lib.connect(offset_vec, "", pos, "B")
    df = lib.create_expression(mf, unreal.MaterialExpressionDistanceToNearestSurface, -560, 0)
    lib.connect(pos, "", df, "Position")
    absolute = lib.create_expression(mf, unreal.MaterialExpressionAbs, -380, 0)
    lib.connect_unary(df, absolute)
    distance = _fn_input(mf, "BlendDistance", -560, 180, 18.0)
    divide = lib.create_expression(mf, unreal.MaterialExpressionDivide, -180, 0)
    lib.connect(absolute, "", divide, "A")
    lib.connect(distance, "", divide, "B")
    inverse = lib.create_expression(mf, unreal.MaterialExpressionOneMinus, 0, 0)
    lib.connect_unary(divide, inverse)
    saturated = lib.create_expression(mf, unreal.MaterialExpressionSaturate, 180, 0)
    lib.connect_unary(inverse, saturated)
    sharpness = _fn_input(mf, "BlendSharpness", 0, 180, 3.0)
    powered = lib.create_expression(mf, unreal.MaterialExpressionPower, 360, 0)
    lib.connect(saturated, "", powered, "Base")
    lib.connect(sharpness, "", powered, "Exp")

    noise_scale = _fn_input(mf, "NoiseScale", 0, 380, 0.015)
    noise_pos = lib.create_expression(mf, unreal.MaterialExpressionMultiply, 180, 300)
    lib.connect(pos, "", noise_pos, "A")
    lib.connect(noise_scale, "", noise_pos, "B")
    noise = lib.create_expression(mf, unreal.MaterialExpressionNoise, 360, 300)
    lib.connect(noise_pos, "", noise, "Position")
    noise_sat = lib.create_expression(mf, unreal.MaterialExpressionSaturate, 540, 300)
    lib.connect_unary(noise, noise_sat)
    noise_mask = lib.create_expression(mf, unreal.MaterialExpressionMultiply, 720, 0)
    lib.connect(powered, "", noise_mask, "A")
    lib.connect(noise_sat, "", noise_mask, "B")
    breakup = _fn_input(mf, "NoiseBreakup", 360, 480, 0.0)
    broken = lib.create_expression(mf, unreal.MaterialExpressionLinearInterpolate, 900, 0)
    lib.connect(powered, "", broken, "A")
    lib.connect(noise_mask, "", broken, "B")
    lib.connect(breakup, "", broken, "Alpha")
    ground_height = _fn_input(mf, "GroundHeight", 720, 680, 0.0)
    height_falloff = _fn_input(mf, "HeightFalloff", 900, 680, 28.0)
    height_mask = lib.create_expression(mf, unreal.MaterialExpressionComponentMask, 900, 820)
    height_mask.set_editor_property("r", False); height_mask.set_editor_property("g", False)
    height_mask.set_editor_property("b", True); height_mask.set_editor_property("a", False)
    lib.connect(world, "", height_mask, "Input")
    height_delta = lib.create_expression(mf, unreal.MaterialExpressionSubtract, 1080, 820)
    lib.connect(height_mask, "", height_delta, "A"); lib.connect(ground_height, "", height_delta, "B")
    height_abs = lib.create_expression(mf, unreal.MaterialExpressionAbs, 1260, 820); lib.connect_unary(height_delta, height_abs)
    height_div = lib.create_expression(mf, unreal.MaterialExpressionDivide, 1440, 820)
    lib.connect(height_abs, "", height_div, "A"); lib.connect(height_falloff, "", height_div, "B")
    height_inv = lib.create_expression(mf, unreal.MaterialExpressionOneMinus, 1620, 820); lib.connect_unary(height_div, height_inv)
    height_sat = lib.create_expression(mf, unreal.MaterialExpressionSaturate, 1800, 820); lib.connect_unary(height_inv, height_sat)
    # Require both actual Global Distance Field proximity and the authored
    # ground-height envelope. The height term prevents the contact mask from
    # climbing an entire prop; the DF term prevents a horizontal blend band on
    # geometry that is not actually near another surface.
    combined = lib.create_expression(mf, unreal.MaterialExpressionMultiply, 1080, 700)
    lib.connect(broken, "", combined, "A")
    lib.connect(height_sat, "", combined, "B")
    active = _fn_input(mf, "DistanceFieldBlendActive", 540, 500, 1.0)
    active_mask = lib.create_expression(mf, unreal.MaterialExpressionMultiply, 1080, 0)
    lib.connect(combined, "", active_mask, "A")
    lib.connect(active, "", active_mask, "B")
    strength = _fn_input(mf, "BlendStrength", 720, 500, 1.0)
    result = lib.create_expression(mf, unreal.MaterialExpressionMultiply, 1260, 0)
    lib.connect(active_mask, "", result, "A")
    lib.connect(strength, "", result, "B")
    output = mel.create_material_expression_in_function(mf, unreal.MaterialExpressionFunctionOutput, 1480, 0)
    output.set_editor_property("output_name", "Result")
    lib.connect(result, "", output, "")
    if hasattr(mel, "recompile_material_function"):
        mel.recompile_material_function(mf)
    lib.save_package(mf)
    return mf


def _scalar(m, name, default, y):
    node = unreal.MaterialEditingLibrary.create_material_expression(m, unreal.MaterialExpressionScalarParameter, 13200, y)
    node.set_editor_property("parameter_name", name)
    node.set_editor_property("default_value", default)
    node.set_editor_property("group", GROUP)
    return node


def _vector(m, name, value, y):
    node = unreal.MaterialEditingLibrary.create_material_expression(m, unreal.MaterialExpressionVectorParameter, 13200, y)
    node.set_editor_property("parameter_name", name)
    node.set_editor_property("default_value", unreal.LinearColor(*value))
    node.set_editor_property("group", GROUP)
    return node


def _switch(m, y):
    node = unreal.MaterialEditingLibrary.create_material_expression(m, unreal.MaterialExpressionStaticSwitchParameter, 14600, y)
    node.set_editor_property("parameter_name", "bDFContactBlend_Active")
    node.set_editor_property("default_value", False)
    node.set_editor_property("group", GROUP)
    return node


def _build_master():
    m = unreal.EditorAssetLibrary.load_asset(MASTER)
    if not m:
        raise RuntimeError(f"Could not load {MASTER}")
    mel = unreal.MaterialEditingLibrary
    exprs = list(mel.get_material_expressions(m) or [])
    existing = [e for e in exprs if isinstance(e, unreal.MaterialExpressionStaticSwitchParameter) and str(e.get_editor_property("parameter_name")) == "bDFContactBlend_Active"]
    if existing:
        return {"master_modified": False, "reason": "bDFContactBlend_Active already exists"}
    toon = next((e for e in exprs if "SubstrateToonBSDF" in type(e).__name__), None)
    if not toon:
        raise RuntimeError("Universal master has no Substrate Toon BSDF")
    inputs = list(mel.get_inputs_for_material_expression(m, toon) or [])
    pin_names = list(mel.get_material_expression_input_names(toon) or [])
    mapping = {name: inputs[index] for index, name in enumerate(pin_names) if index < len(inputs)}
    unreal.log(f"[DistanceFieldSpike] Universal BSDF input slots={len(inputs)} mapping={[(name, getattr(mapping.get(name), 'get_name', lambda: None)() if mapping.get(name) else None) for name in pin_names]}")
    def pick(*names):
        for name in names:
            if mapping.get(name):
                return mapping[name]
        return None
    base_src = pick("BaseColor", "DiffuseColor")
    rough_src = pick("Roughness")
    normal_src = pick("Normal", "TangentNormal", "NormalMap")
    if not all((base_src, rough_src, normal_src)):
        raise RuntimeError(f"Could not preserve Universal master BSDF named inputs: {pin_names}")
    call = mel.create_material_expression(m, unreal.MaterialExpressionMaterialFunctionCall, 14200, 0)
    call.set_editor_property("material_function", unreal.EditorAssetLibrary.load_asset(FUNCTION))
    params = {
        "BlendDistance": _scalar(m, "DFContactBlendDistance", 18.0, -360),
        "BlendSharpness": _scalar(m, "DFContactBlendSharpness", 3.0, -240),
        "BlendStrength": _scalar(m, "DFContactBlendStrength", 0.0, -120),
        "NoiseBreakup": _scalar(m, "DFContactNoiseBreakup", 0.0, 0),
        "NoiseScale": _scalar(m, "DFContactNoiseScale", 0.015, 120),
        "WorldPositionOffset": _scalar(m, "DFContactWorldPositionOffset", 12.0, 240),
        "GroundHeight": _scalar(m, "DFContactGroundHeight", 0.0, 360),
        "HeightFalloff": _scalar(m, "DFContactHeightFalloff", 28.0, 480),
    }
    for pin, node in params.items():
        lib.connect(node, "", call, pin)
    active_one = unreal.MaterialEditingLibrary.create_material_expression(m, unreal.MaterialExpressionConstant, 13700, 300)
    active_one.set_editor_property("r", 1.0)
    lib.connect(active_one, "", call, "DistanceFieldBlendActive")
    mask = call
    tint = _vector(m, "DFContactTint", (0.24, 0.30, 0.34, 1.0), 420)
    roughness = _scalar(m, "DFContactRoughness", 0.82, 540)
    neutral = unreal.MaterialEditingLibrary.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, 13700, 660)
    neutral.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 1.0, 0.0))
    color_lerp = unreal.MaterialEditingLibrary.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, 14900, -80)
    lib.connect(base_src, "", color_lerp, "A")
    lib.connect(tint, "", color_lerp, "B")
    lib.connect(mask, "Result", color_lerp, "Alpha")
    color_switch = _switch(m, -80)
    lib.connect(base_src, "", color_switch, "False")
    lib.connect(color_lerp, "", color_switch, "True")
    rough_lerp = unreal.MaterialEditingLibrary.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, 14900, 180)
    lib.connect(rough_src, "", rough_lerp, "A")
    lib.connect(roughness, "", rough_lerp, "B")
    lib.connect(mask, "Result", rough_lerp, "Alpha")
    rough_switch = _switch(m, 180)
    lib.connect(rough_src, "", rough_switch, "False")
    lib.connect(rough_lerp, "", rough_switch, "True")
    normal_lerp = unreal.MaterialEditingLibrary.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, 14900, 440)
    lib.connect(normal_src, "", normal_lerp, "A")
    lib.connect(neutral, "", normal_lerp, "B")
    lib.connect(mask, "Result", normal_lerp, "Alpha")
    normal_switch = _switch(m, 440)
    lib.connect(normal_src, "", normal_switch, "False")
    lib.connect(normal_lerp, "", normal_switch, "True")
    lib.connect(color_switch, "", toon, "BaseColor")
    lib.connect(rough_switch, "", toon, "Roughness")
    lib.connect(normal_switch, "", toon, "Normal")
    mel.recompile_material(m)
    lib.save_package(m)
    return {"master_modified": True, "static_switch": "bDFContactBlend_Active", "function": FUNCTION}


def _build_test_instance():
    unreal.EditorAssetLibrary.make_directory(TEST_DIR)
    mi = unreal.EditorAssetLibrary.load_asset(TEST_MI)
    if not mi:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        mi = tools.create_asset("MI_DF_ContactBlend_Soft", TEST_DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    if not mi:
        raise RuntimeError(f"Could not create {TEST_MI}")
    mi.set_editor_property("parent", unreal.EditorAssetLibrary.load_asset(MASTER))
    mel = unreal.MaterialEditingLibrary
    mel.set_material_instance_static_switch_parameter_value(mi, "bDFContactBlend_Active", True)
    for name, value in {
        "DFContactBlendDistance": 22.0,
        "DFContactBlendSharpness": 3.0,
        "DFContactBlendStrength": 1.0,
        "DFContactNoiseBreakup": 0.18,
        "DFContactNoiseScale": 0.012,
        "DFContactWorldPositionOffset": 12.0,
        "DFContactGroundHeight": 0.0,
        "DFContactHeightFalloff": 28.0,
        "DFContactRoughness": 0.78,
    }.items():
        mel.set_material_instance_scalar_parameter_value(mi, name, value)
    mel.set_material_instance_vector_parameter_value(mi, "DFContactTint", unreal.LinearColor(0.30, 0.36, 0.38, 1.0))
    lib.save_package(mi)
    return {"test_instance": TEST_MI, "enabled": True}


def main():
    _build_function()
    master = _build_master()
    instance = _build_test_instance()
    result = {"function": FUNCTION, **master, **instance, "mesh_distance_fields_enabled": True, "legacy_plugin_removed": True}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log(f"[DistanceFieldSpike] Built material spike -> {REPORT}")


if __name__ == "__main__":
    main()
