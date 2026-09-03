"""Inspect Grade V2 material code and structure."""
import unreal
MEL = unreal.MaterialEditingLibrary
mat = unreal.load_asset("/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade")
custom = [e for e in MEL.get_material_expressions(mat) if type(e).__name__ == "MaterialExpressionCustom"][0]
code = custom.get_editor_property("code")
print(f"CODE_LEN:{len(code)}")
print(f"HAS_RETURN:{'return' in code}")
print(f"HAS_GRADED:{'graded' in code}")
print(f"HAS_FINAL:{'finalColor' in code}")
# Print last 300 chars
print(f"CODE_END:{code[-300:]}")
# Print first 300 chars
print(f"CODE_START:{code[:300]}")
# Print pins
inputs = custom.get_editor_property("inputs")
pin_names = [str(i.get_editor_property("input_name")) for i in inputs]
print(f"PINS:{pin_names}")
