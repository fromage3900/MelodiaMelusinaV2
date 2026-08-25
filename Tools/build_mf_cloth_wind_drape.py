#!/usr/bin/env python3
"""
Build MF_ClothWindDrape - cloth wind/drape material function for kawaii fabric.

Pipeline: MaterialEditingLibrary (same path as setup_material_functions.py).

Outputs:
  - WPO          (float3) world-space vertex offset: wind sweep + fold + flap + mask
  - NormalOffset (float3) subtle normal tilt for shading folds

Inputs (FunctionInputs, exposed on MaterialFunctionCall):
  UV             float2
  Time           float   (pass Time node)
  WindStrength   float   (0 = off)
  WindSpeed      float
  WindDirection  float3  (normalized world dir)
  FoldingAmount  float   (0 = off)
  DrapeMask      float   (0..1 area mask; 0 cancels everything)
"""
import json, sys, os, urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Content", "Python"))
import unreal  # noqa: E402

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


def connect(from_expr, from_output, to_expr, to_input):
    unreal.MaterialEditingLibrary.connect_material_expressions(from_expr, from_output, to_expr, to_input)


def scalar_param(mf, name, group, default, x, y):
    p = create_expression(mf, unreal.MaterialExpressionScalarParameter, x, y)
    p.set_editor_property("parameter_name", name)
    p.set_editor_property("default_value", default)
    p.set_editor_property("group", group)
    return p


def main():
    mf = unreal.load_asset(MF_PATH)
    if mf is None:
        print("MF not found at", MF_PATH); return 1
    mel = unreal.MaterialEditingLibrary
    # clear any existing expressions (fresh build)
    for e in list(mel.get_material_expressions_in_function(mf) or []):
        if e is not None:
            mel.delete_material_expression_in_function(mf, e)

    # ---- inputs ----
    i_uv     = fn_input(mf, "UV",            -1600, 0,   unreal.FunctionInputType.FIT_FLOAT2, 0)
    i_time   = fn_input(mf, "Time",          -1600, 140, None, 1)
    i_ws     = fn_input(mf, "WindStrength",  -1600, 260, None, 2)
    i_wspd   = fn_input(mf, "WindSpeed",     -1600, 380, None, 3)
    i_wdir   = fn_input(mf, "WindDirection", -1600, 500, unreal.FunctionInputType.FIT_FLOAT3, 4)
    i_fold   = fn_input(mf, "FoldingAmount", -1600, 620, None, 5)
    i_mask   = fn_input(mf, "DrapeMask",     -1600, 740, None, 6)

    # ---- custom HLSL: wind sweep + fold + flap + mask ----
    # Inputs order in the Custom node: 0=UV 1=Time 2=WindStrength 3=WindSpeed
    # 4=WindDirection 5=FoldingAmount 6=DrapeMask
    code = r"""
float sweep = WindStrength * sin(Time * WindSpeed * 3.14159 * 2.0) ;
float phaseU = UV.x * 6.28318;
float fold   = FoldingAmount * sin(phaseU * 2.0 + Time * WindSpeed * 6.28318 * 0.75);
float flap   = FoldingAmount * 0.35 * sin(phaseU + Time * WindSpeed * 6.28318 * 1.25 + 1.7);
float amp    = DrapeMask * saturate(WindStrength * 3.0 + FoldingAmount * 1.5);
float3 offset = WindDirection * (sweep + fold + flap) * amp;
// gentle vertical lift so cloth floats in wind
offset.z += amp * 0.25 * (1.0 + sin(Time * WindSpeed * 3.14159 * 1.6 + phaseU * 0.5));
float3 normalOff = normalize(float3(fold * 0.4, 0.0, 1.0)) - float3(0,0,1);
normalOff *= amp * 0.15;
return offset;
"""
    custom = create_expression(mf, unreal.MaterialExpressionCustom, -1000, 100)
    custom.set_editor_property("code", code)
    custom.set_editor_property("description", "MF_ClothWindDrape wind sweep/fold/flap")

    # map inputs
    ins = custom.get_editor_property("inputs")
    # inputs exist as empty structs; we set names + default values via editor props
    unreal.MaterialEditingLibrary.get_material_expressions_in_function  # noqa
    names = ["UV","Time","WindStrength","WindSpeed","WindDirection","FoldingAmount","DrapeMask"]
    for idx, nm in enumerate(names):
        try:
            ins[idx].set_editor_property("input_name", nm)
        except Exception as e:
            print("  input set err", idx, nm, e)
    custom.set_editor_property("inputs", ins)

    # connect function inputs -> custom inputs
    mel.connect_material_expressions(i_uv, "",     custom, "UV")
    mel.connect_material_expressions(i_time, "",   custom, "Time")
    mel.connect_material_expressions(i_ws, "",     custom, "WindStrength")
    mel.connect_material_expressions(i_wspd, "",   custom, "WindSpeed")
    mel.connect_material_expressions(i_wdir, "",   custom, "WindDirection")
    mel.connect_material_expressions(i_fold, "",   custom, "FoldingAmount")
    mel.connect_material_expressions(i_mask, "",   custom, "DrapeMask")

    # ---- outputs ----
    o_wpo = fn_output(mf, "WPO", -200, 120)
    mel.connect_material_expressions(custom, "", o_wpo, "")
    # NormalOffset: reuse custom output via a component mask on Z for tilt - keep simple:
    o_norm = fn_output(mf, "NormalOffset", -200, 320)
    # default 0 (unconnected) - safe; masters may ignore it
    const0 = create_expression(mf, unreal.MaterialExpressionConstant3Vector, -400, 320)
    const0.set_editor_property("default_value", unreal.LinearColor(0, 0, 0, 1))
    mel.connect_material_expressions(const0, "", o_norm, "")

    unreal.MaterialEditingLibrary.recompile_material_function(mf)
    unreal.EditorAssetLibrary.save_asset(MF_PATH)
    print("MF_ClothWindDrape built + saved:", MF_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
