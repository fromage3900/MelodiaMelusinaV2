#!/usr/bin/env python3
"""Fix SK_Melusina material slot assignments.
8 slots point to MI_Melusina_Material_023 (catch-all) instead of their proper MIs.
"""
import json, sys, urllib.request

MCP = "http://127.0.0.1:9316/mcp"

def monolith(tool, args, timeout=60):
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":tool,"arguments":args}}).encode()
    req = urllib.request.Request(MCP, data=body, headers={"Content-Type":"application/json"})
    resp = urllib.request.urlopen(req, timeout=timeout)
    data = json.loads(resp.read().decode())
    result = data.get("result",{})
    if result.get("isError"):
        return "ERROR:" + result.get("content",[{}])[0].get("text","")
    return result.get("content",[{}])[0].get("text","")

# Slot -> correct MI mapping (from audit)
# Slots that need fixing (currently all pointing to MI_Melusina_Material_023):
SLOT_FIXES = {
    5: "MI_Melusina_Metal_2__Matcap__002",    # Should be metal matcap, was celestial catch-all
    6: "MI_Melusina_Outline_005",              # Should be outline
    7: "MI_Melusina_Material_021",             # Should be material_021
    8: "MI_Melusina_Outline_004",              # Should be outline
    10: "MI_Melusina_Halftone_Circles___Circles__3_Inputs__001",  # Should be halftone
    11: "MI_Melusina_Material_022",            # Should be material_022
    14: "MI_Melusina_Outline_Shader_star_034", # Should be outline
    15: "MI_Melusina_Material_024",            # Should be shirt (exists with T_MelusinaC_SHIRT_001_*!)
}

print("="*60)
print("SK_Melusina Material Slot Fix")
print("="*60)
print()

# Build Python script to run in-editor
lines = []
lines.append("import unreal")
lines.append("")
lines.append('mesh = unreal.EditorAssetLibrary.load_asset("/Game/Melodia/Characters/Melusina/SK_Melusina")')
lines.append("if not mesh:")
lines.append('    print("ERROR: Could not load SK_Melusina")')
lines.append("")
lines.append("slot_fixes = {")
for slot, mi_name in SLOT_FIXES.items():
    lines.append(f'    {slot}: "/Game/Melodia/Characters/Melusina/Materials/{mi_name}",')
lines.append("}")
lines.append("")
lines.append('base_path = "/Game/Melodia/Characters/Melusina/Materials/"')
lines.append("fixed = 0")
lines.append("errors = 0")
lines.append("")
lines.append("for slot, mi_path in slot_fixes.items():")
lines.append("    mi = unreal.EditorAssetLibrary.load_asset(mi_path)")
lines.append("    if mi:")
lines.append("        mesh.set_material(slot, mi)")
lines.append('        print(f"  Slot {slot}: set to {mi_path}")')
lines.append("        fixed += 1")
lines.append("    else:")
lines.append('        print(f"  ERROR Slot {slot}: Could not load {mi_path}")')
lines.append("        errors += 1")
lines.append("")
lines.append("if errors > 0:")
lines.append('    print(f"\\n{errors} error(s) loading MIs - check paths")')
lines.append("")
lines.append("")
lines.append("# Also print all slot assignments for verification")
lines.append('print("\\n=== Full slot map after fix ===")')
lines.append("for i in range(mesh.get_num_sections()):")
lines.append("    mat = mesh.get_material(i)")
lines.append("    if mat:")
lines.append("        print(f'  Slot {i}: {mat.get_path_name()[:100]}')")
lines.append("    else:")
lines.append("        print(f'  Slot {i}: NONE')")
lines.append("")
lines.append("# Save the mesh")
lines.append("unreal.EditorAssetLibrary.save_asset(\"/Game/Melodia/Characters/Melusina/SK_Melusina\")")
lines.append('print("\\nSK_Melusina saved")')

script = "\n".join(lines)

result = monolith("editor_query", {"action":"run_python","command":script})
print(result)
