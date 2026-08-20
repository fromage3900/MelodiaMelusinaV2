#!/usr/bin/env python3
"""Fix SK_Melusina material slot assignments using materials array API."""
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

script = """
import unreal

mesh = unreal.EditorAssetLibrary.load_asset("/Game/Melodia/Characters/Melusina/SK_Melusina")
if not mesh:
    print("ERROR: SK_Melusina not found")

# Read current material slots
materials = mesh.get_editor_property("materials")
print("=== Current slots (before fix) ===")
for i, m in enumerate(materials):
    mi = m.get_editor_property("material_interface")
    if mi:
        slot_name = str(m.get_editor_property("material_slot_name") or "")
    print("  Slot {}: {} ({}) slot='{}'".format(i, mi.get_name(), mi.get_path_name()[:90], slot_name))
    else:
        print("  Slot {}: NONE".format(i))

# Define slot fixes: slot_index -> MI asset path
slot_fixes = {
    5: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Metal_2__Matcap__002",
    6: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Outline_005",
    7: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Material_021",
    8: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Outline_004",
    10: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Halftone_Circles___Circles__3_Inputs__001",
    11: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Material_022",
    14: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Outline_Shader_star_034",
    15: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Material_024",
}

# Fix slot 0 too - it uses master directly instead of an MI
# slot_fixes[0] = "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Gradient__Radial__002"

fixed = 0
errors = 0
for slot_idx, mi_path in slot_fixes.items():
    mi = unreal.EditorAssetLibrary.load_asset(mi_path)
    if mi:
        if slot_idx < len(materials):
            mat_slot = materials[slot_idx]
            mat_slot.set_editor_property("material_interface", mi)
            print("  Slot {}: set to {}".format(slot_idx, mi_path))
            fixed += 1
        else:
            print("  ERROR Slot {}: index out of range (len={})".format(slot_idx, len(materials)))
            errors += 1
    else:
        print("  ERROR Slot {}: MI not found at {}".format(slot_idx, mi_path))
        errors += 1

# Write materials array back
if fixed > 0:
    mesh.set_editor_property("materials", materials)
    unreal.EditorAssetLibrary.save_asset("/Game/Melodia/Characters/Melusina/SK_Melusina")
    print("\\nSaved SK_Melusina with {} fixes".format(fixed))

# Verify
mesh2 = unreal.EditorAssetLibrary.load_asset("/Game/Melodia/Characters/Melusina/SK_Melusina")
mats2 = mesh2.get_editor_property("materials")
print("\\n=== After fix ===")
for i, m in enumerate(mats2):
    mi = m.get_editor_property("material_interface")
    if mi:
        print("  Slot {}: {} ({})".format(i, mi.get_name(), mi.get_path_name()[:90]))
    else:
        print("  Slot {}: NONE".format(i))

print("\\nFixed: {}, Errors: {}".format(fixed, errors))
"""
result = monolith("editor_query", {"action":"run_python","command":script})
print(result)
