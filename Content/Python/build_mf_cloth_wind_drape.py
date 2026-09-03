#!/usr/bin/env python3
"""
Build MF_ClothWindDrape — cloth wind/drape material function.
Run INSIDE the UE editor (editor_query:run_python -> exec this file).
Outputs: WPO (float3), NormalOffset (float3).
"""
import unreal  # noqa

MF_PATH = "/Game/EnvSandbox/Materials/Functions/MF_ClothWindDrape"


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
        print("MF not found:", MF_PATH); return 1
    mel = unreal.MaterialEditingLibrary
    mel.delete_all_material_expressions_in_function(mf)

    i_uv   = fn_input(mf, "UV",            -1600, 0,   unreal.FunctionInputType.FUNCTION_INPUT_VECTOR2, 0)
    i_time = fn_input(mf, "Time",          -1600, 140, unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 1)
    i_ws   = fn_input(mf, "WindStrength",  -1600, 260, unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 2)
    i_wspd = fn_input(mf, "WindSpeed",     -1600, 380, unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 3)
    i_wdir = fn_input(mf, "WindDirection", -1600, 500, unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3, 4)
    i_fold = fn_input(mf, "FoldingAmount", -1600, 620, unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 5)
    i_mask = fn_input(mf, "DrapeMask",     -1600, 740, unreal.FunctionInputType.FUNCTION_INPUT_SCALAR, 6)

    code = """float sweep = WindStrength * sin(Time * WindSpeed * 3.14159 * 2.0);
float phaseU = UV.x * 6.28318;
float fold = FoldingAmount * sin(phaseU * 2.0 + Time * WindSpeed * 6.28318 * 0.75);
float flap = FoldingAmount * 0.35 * sin(phaseU + Time * WindSpeed * 6.28318 * 1.25 + 1.7);
float amp = DrapeMask * saturate(WindStrength * 3.0 + FoldingAmount * 1.5);
float3 offset = WindDirection * (sweep + fold + flap) * amp;
offset.z += amp * 0.25 * (1.0 + sin(Time * WindSpeed * 3.14159 * 1.6 + phaseU * 0.5));
return offset;"""
    custom = create_expression(mf, unreal.MaterialExpressionCustom, -1000, 100)
    custom.set_editor_property("code", code)
    custom.set_editor_property("description", "MF_ClothWindDrape wind sweep/fold/flap")

    names = ["UV","Time","WindStrength","WindSpeed","WindDirection","FoldingAmount","DrapeMask"]
    ins = list(custom.get_editor_property("inputs"))
    while len(ins) < len(names):
        ins.append(unreal.CustomInput())
    for idx, nm in enumerate(names):
        try:
            ins[idx].set_editor_property("input_name", nm)
        except Exception as e:
            print("  input set err", idx, nm, e)
    custom.set_editor_property("inputs", ins)

    mel.connect_material_expressions(i_uv,   "", custom, "UV")
    mel.connect_material_expressions(i_time, "", custom, "Time")
    mel.connect_material_expressions(i_ws,   "", custom, "WindStrength")
    mel.connect_material_expressions(i_wspd, "", custom, "WindSpeed")
    mel.connect_material_expressions(i_wdir, "", custom, "WindDirection")
    mel.connect_material_expressions(i_fold, "", custom, "FoldingAmount")
    mel.connect_material_expressions(i_mask, "", custom, "DrapeMask")

    o_wpo = fn_output(mf, "WPO", -200, 120)
    mel.connect_material_expressions(custom, "", o_wpo, "")

    o_norm = fn_output(mf, "NormalOffset", -200, 320)
    const0 = create_expression(mf, unreal.MaterialExpressionConstant3Vector, -400, 320)
    try:
        const0.set_editor_property("constant", unreal.LinearColor(0, 0, 0, 1))
    except Exception:
        try:
            const0.set_editor_property("default_value", (0, 0, 0))
        except Exception as e2:
            print("const set err", e2)
    mel.connect_material_expressions(const0, "", o_norm, "")

    try:
        unreal.MaterialEditingLibrary.update_material_function(mf)
    except Exception as e:
        print("update_material_function err:", e)
    unreal.EditorAssetLibrary.save_asset(MF_PATH)
    print("MF_ClothWindDrape built + saved:", MF_PATH)
    return 0


if __name__ == "__main__":
    main()
