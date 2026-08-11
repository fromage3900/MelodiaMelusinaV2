"""Check for remaining jitterPx references in V6 code."""
import unreal

MEL = unreal.MaterialEditingLibrary
mat = unreal.load_asset("/Game/EnvSandbox/Materials/PostProcess/Candidates/M_PP_StorybookOutline_Premium_Candidate")
custom = [e for e in MEL.get_material_expressions(mat) if type(e).__name__ == "MaterialExpressionCustom"][0]
code = custom.get_editor_property("code")
lines = code.split("\\n")
print("=== Jitter references ===")
for i, l in enumerate(lines):
    if "jitter" in l.lower():
        print(f"L{i}: {l}")
print("=== First 25 lines ===")
for i in range(min(25, len(lines))):
    print(f"L{i}: {lines[i]}")
print(f"\\nTotal lines: {len(lines)}")
print(f"Code length: {len(code)}")
