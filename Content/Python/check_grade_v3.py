"""Verify Grade V3 compilation."""
import unreal
MAT = "/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade"
m = unreal.load_asset(MAT)
if not m:
    print("FAIL: material not found")
else:
    # Check the code
    custom = [e for e in unreal.MaterialEditingLibrary.get_material_expressions(m) if type(e).__name__ == "MaterialExpressionCustom"][0]
    code = custom.get_editor_property("code")
    print(f"CODE_LEN: {len(code)}")
    print(f"CEL_STEPS: {'CelSteps' in code}")
    print(f"DYNAMIC_CONTRAST: {'DynamicContrast' in code}")
    print(f"SELECTIVE: {'KeepColorHue' in code}")
    # Check new params exist
    exprs = unreal.MaterialEditingLibrary.get_material_expressions(m) or []
    params = set()
    for e in exprs:
        try: params.add(str(e.get_editor_property("parameter_name")))
        except: pass
    for p in ["CelSteps", "DynamicContrast", "SelectiveStrength", "KeepColorHue"]:
        print(f"PARAM_{p}: {p in params}")
    # Compile
    unreal.MaterialEditingLibrary.recompile_material(m)
    print("RECOMPILED")
