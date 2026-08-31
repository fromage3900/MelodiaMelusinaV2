#!/usr/bin/env python3
"""
Build MF_FabricMountainWPO — audio-reactive multi-frequency WPO for fabric mountains.

Reads Cymatics values from MPC and combines 4 WPO layers:
  - Macro swell: Chladni standing-wave * BassIntensity
  - Medium folds: sin/cos noise * MidIntensity
  - Micro detail: Copernicus height map * BeatPulse
  - Wind response: MF_ClothWindDrape * RhythmPulse

Run via Monolith run_python action:
  monolith run_python Content/Python/build_mf_fabric_mountain_wpo.py
"""
import unreal

MF_PATH = "/Game/EnvSandbox/Materials/Functions/MF_FabricMountainWPO"


def create_expression(mf, cls, x, y):
    return unreal.MaterialEditingLibrary.create_material_expression_in_function(mf, cls, x, y)


def fn_input(mf, name, x, y, input_type=None, sort=0):
    inp = create_expression(mf, unreal.MaterialExpressionFunctionInput, x, y)
    inp.set_editor_property("input_name", name)
    try:
        inp.set_editor_property("sort_priority", sort)
    except Exception:
        pass
    if input_type is not None:
        try:
            inp.set_editor_property("input_type", input_type)
        except Exception:
            pass
    return inp


def fn_output(mf, name, x, y):
    out = create_expression(mf, unreal.MaterialExpressionFunctionOutput, x, y)
    out.set_editor_property("output_name", name)
    return out


def main():
    mf = unreal.load_asset(MF_PATH)
    if mf is None:
        # Create new MF
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        mf = tools.create_asset("MF_FabricMountainWPO", "/Game/EnvSandbox/Materials/Functions", unreal.MaterialFunction, unreal.MaterialFunctionFactoryNew())
        if not mf:
            print("ERROR: Failed to create MF")
            return 1
        print("Created MF:", MF_PATH)
    else:
        print("MF exists, updating...")

    mel = unreal.MaterialEditingLibrary
    mel.delete_all_material_expressions_in_function(mf)

    # Inputs
    i_uv = fn_input(mf, "UV", -1600, 0, unreal.FunctionInputType.FUNCTION_INPUT_VECTOR2, 0)
    i_time = fn_input(mf, "Time", -1600, 100, unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 1)
    i_cymatic = fn_input(mf, "CymaticAmplitude", -1600, 200, unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 2)
    i_bass = fn_input(mf, "BassIntensity", -1600, 300, unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 3)
    i_mid = fn_input(mf, "MidIntensity", -1600, 400, unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 4)
    i_beat = fn_input(mf, "BeatPulse", -1600, 500, unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 5)
    i_rhythm = fn_input(mf, "RhythmPulse", -1600, 600, unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 6)
    i_wind_str = fn_input(mf, "WindStrength", -1600, 700, unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 7)
    i_wind_spd = fn_input(mf, "WindSpeed", -1600, 800, unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 8)
    i_wind_dir = fn_input(mf, "WindDirection", -1600, 900, unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3, 9)
    i_fold_amt = fn_input(mf, "FoldingAmount", -1600, 1000, unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 10)
    i_height_map = fn_input(mf, "HeightMap", -1600, 1100, unreal.FunctionInputType.FUNCTION_INPUT_TEXTURE2D, 11)
    i_mountain_scale = fn_input(mf, "MountainScale", -1600, 1200, unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 12)

    # Macro swell: CymaticAmplitude * BassIntensity * sin(UV.x * 3.14159 * 2.0 * MountainScale * 0.001 + Time)
    macro_code = """float macroFreq = 3.14159 * 2.0 * MountainScale * 0.001;
float macroPhase = UV.x * macroFreq + Time * 0.5;
float macroSwell = CymaticAmplitude * BassIntensity * sin(macroPhase) * 50.0;
return macroSwell;"""

    macro_custom = create_expression(mf, unreal.MaterialExpressionCustom, -800, 200)
    macro_custom.set_editor_property("code", macro_code)
    macro_custom.set_editor_property("description", "Macro swell: Chladni * BassIntensity")
    macro_inputs = list(macro_custom.get_editor_property("inputs"))
    while len(macro_inputs) < 5:
        macro_inputs.append(unreal.CustomInput())
    macro_inputs[0].set_editor_property("input_name", "UV")
    macro_inputs[1].set_editor_property("input_name", "Time")
    macro_inputs[2].set_editor_property("input_name", "CymaticAmplitude")
    macro_inputs[3].set_editor_property("input_name", "BassIntensity")
    macro_inputs[4].set_editor_property("input_name", "MountainScale")
    macro_custom.set_editor_property("inputs", macro_inputs)

    mel.connect_material_expressions(i_uv, "", macro_custom, "UV")
    mel.connect_material_expressions(i_time, "", macro_custom, "Time")
    mel.connect_material_expressions(i_cymatic, "", macro_custom, "CymaticAmplitude")
    mel.connect_material_expressions(i_bass, "", macro_custom, "BassIntensity")
    mel.connect_material_expressions(i_mountain_scale, "", macro_custom, "MountainScale")

    # Medium folds: sin(UV.x * 0.01 * MountainScale) * cos(UV.y * 0.008 * MountainScale) * MidIntensity * 10.0
    medium_code = """float medX = UV.x * 0.01 * MountainScale;
float medY = UV.y * 0.008 * MountainScale;
float mediumFolds = sin(medX + Time * 0.3) * cos(medY + Time * 0.2) * MidIntensity * 10.0;
return mediumFolds;"""

    medium_custom = create_expression(mf, unreal.MaterialExpressionCustom, -800, 400)
    medium_custom.set_editor_property("code", medium_code)
    medium_custom.set_editor_property("description", "Medium folds: sin/cos * MidIntensity")
    medium_inputs = list(medium_custom.get_editor_property("inputs"))
    while len(medium_inputs) < 4:
        medium_inputs.append(unreal.CustomInput())
    medium_inputs[0].set_editor_property("input_name", "UV")
    medium_inputs[1].set_editor_property("input_name", "Time")
    medium_inputs[2].set_editor_property("input_name", "MidIntensity")
    medium_inputs[3].set_editor_property("input_name", "MountainScale")
    medium_custom.set_editor_property("inputs", medium_inputs)

    mel.connect_material_expressions(i_uv, "", medium_custom, "UV")
    mel.connect_material_expressions(i_time, "", medium_custom, "Time")
    mel.connect_material_expressions(i_mid, "", medium_custom, "MidIntensity")
    mel.connect_material_expressions(i_mountain_scale, "", medium_custom, "MountainScale")

    # Micro detail: HeightMap sample * BeatPulse
    micro_code = """float microDetail = HeightMap * BeatPulse * 2.0;
return microDetail;"""

    micro_custom = create_expression(mf, unreal.MaterialExpressionCustom, -800, 600)
    micro_custom.set_editor_property("code", micro_code)
    micro_custom.set_editor_property("description", "Micro detail: HeightMap * BeatPulse")
    micro_inputs = list(micro_custom.get_editor_property("inputs"))
    while len(micro_inputs) < 2:
        micro_inputs.append(unreal.CustomInput())
    micro_inputs[0].set_editor_property("input_name", "HeightMap")
    micro_inputs[1].set_editor_property("input_name", "BeatPulse")
    micro_custom.set_editor_property("inputs", micro_inputs)

    mel.connect_material_expressions(i_height_map, "", micro_custom, "HeightMap")
    mel.connect_material_expressions(i_beat, "", micro_custom, "BeatPulse")

    # Wind response: MF_ClothWindDrape with RhythmPulse modulation
    wind_code = """float windSweep = WindStrength * sin(Time * WindSpeed * 3.14159 * 2.0) * RhythmPulse;
float windFold = FoldingAmount * sin(UV.x * 6.28318 * 2.0 + Time * WindSpeed * 6.28318 * 0.75) * RhythmPulse;
float3 windOffset = WindDirection * (windSweep + windFold) * 5.0;
return windOffset;"""

    wind_custom = create_expression(mf, unreal.MaterialExpressionCustom, -800, 800)
    wind_custom.set_editor_property("code", wind_code)
    wind_custom.set_editor_property("description", "Wind response: cloth drape * RhythmPulse")
    wind_inputs = list(wind_custom.get_editor_property("inputs"))
    while len(wind_inputs) < 6:
        wind_inputs.append(unreal.CustomInput())
    wind_inputs[0].set_editor_property("input_name", "UV")
    wind_inputs[1].set_editor_property("input_name", "Time")
    wind_inputs[2].set_editor_property("input_name", "WindStrength")
    wind_inputs[3].set_editor_property("input_name", "WindSpeed")
    wind_inputs[4].set_editor_property("input_name", "WindDirection")
    wind_inputs[5].set_editor_property("input_name", "FoldingAmount")
    wind_custom.set_editor_property("inputs", wind_inputs)

    mel.connect_material_expressions(i_uv, "", wind_custom, "UV")
    mel.connect_material_expressions(i_time, "", wind_custom, "Time")
    mel.connect_material_expressions(i_wind_str, "", wind_custom, "WindStrength")
    mel.connect_material_expressions(i_wind_spd, "", wind_custom, "WindSpeed")
    mel.connect_material_expressions(i_wind_dir, "", wind_custom, "WindDirection")
    mel.connect_material_expressions(i_fold_amt, "", wind_custom, "FoldingAmount")

    # Combine all layers
    combine_code = """float totalZ = macroSwell + mediumFolds + microDetail + windOffset.z;
float3 finalWPO = float3(windOffset.x, windOffset.y, totalZ);
return finalWPO;"""

    combine_custom = create_expression(mf, unreal.MaterialExpressionCustom, -200, 500)
    combine_custom.set_editor_property("code", combine_code)
    combine_custom.set_editor_property("description", "Combine all WPO layers")
    combine_inputs = list(combine_custom.get_editor_property("inputs"))
    while len(combine_inputs) < 4:
        combine_inputs.append(unreal.CustomInput())
    combine_inputs[0].set_editor_property("input_name", "macroSwell")
    combine_inputs[1].set_editor_property("input_name", "mediumFolds")
    combine_inputs[2].set_editor_property("input_name", "microDetail")
    combine_inputs[3].set_editor_property("input_name", "windOffset")
    combine_custom.set_editor_property("inputs", combine_inputs)

    mel.connect_material_expressions(macro_custom, "", combine_custom, "macroSwell")
    mel.connect_material_expressions(medium_custom, "", combine_custom, "mediumFolds")
    mel.connect_material_expressions(micro_custom, "", combine_custom, "microDetail")
    mel.connect_material_expressions(wind_custom, "", combine_custom, "windOffset")

    # Output
    o_wpo = fn_output(mf, "WPO", 200, 500)
    mel.connect_material_expressions(combine_custom, "", o_wpo, "")

    # Normal offset (simplified)
    o_norm = fn_output(mf, "NormalOffset", 200, 700)
    const0 = create_expression(mf, unreal.MaterialExpressionConstant3Vector, -200, 700)
    try:
        const0.set_editor_property("constant", unreal.LinearColor(0, 0, 0, 1))
    except Exception:
        try:
            const0.set_editor_property("default_value", (0, 0, 0))
        except Exception as e2:
            print("const set err", e2)
    mel.connect_material_expressions(const0, "", o_norm, "")

    try:
        mel.update_material_function(mf)
    except Exception as e:
        print("update_material_function err:", e)

    unreal.EditorAssetLibrary.save_asset(MF_PATH)
    print("MF_FabricMountainWPO built + saved:", MF_PATH)
    return 0


if __name__ == "__main__":
    main()
