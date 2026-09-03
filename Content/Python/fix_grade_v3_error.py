"""Emergency fix: revert Grade V3 code block causing compile failure."""
import unreal
MAT = "/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade"
MEL = unreal.MaterialEditingLibrary
m = unreal.load_asset(MAT)
if not m:
    raise RuntimeError("Missing grade material")

custom = [e for e in MEL.get_material_expressions(m) if type(e).__name__ == "MaterialExpressionCustom"][0]
code = custom.get_editor_property("code")

v3_marker = "// ---- V3 ART OF SHADER INTEGRATION -----------------------------------"
v3_end = "// -------------------------------------------------------------------------"

if v3_marker in code:
    start = code.find(v3_marker)
    end = code.find(v3_end, start) + len(v3_end)
    code = code[:start] + code[end:]
    custom.set_editor_property("code", code)
    MEL.recompile_material(m)
    unreal.EditorAssetLibrary.save_asset(MAT)
    print("OK: V3 block removed, length=" + str(len(code)))
else:
    print("SKIP: V3 block not found")

# Verify compilation
rb = [e for e in MEL.get_material_expressions(m) if type(e).__name__ == "MaterialExpressionCustom"][0]
rc = rb.get_editor_property("code")
print("V3_in_code=" + str("V3 ART" in rc))
