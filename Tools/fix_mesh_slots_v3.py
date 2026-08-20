#!/usr/bin/env python3
"""Fix SK_Melusina material slot assignments - clean version."""
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

script = "".join([
'import unreal\n',
'mesh = unreal.EditorAssetLibrary.load_asset("/Game/Melodia/Characters/Melusina/SK_Melusina")\n',
'if not mesh:\n',
'    print("ERROR: SK_Melusina not found")\n',
'else:\n',
'    materials = mesh.get_editor_property("materials")\n',
'    print("=== Current slots (before fix) ===")\n',
'    for i, m in enumerate(materials):\n',
'        mi = m.get_editor_property("material_interface")\n',
'        if mi:\n',
'            sn = str(m.get_editor_property("material_slot_name") or "")\n',
'            print("  Slot %d: %s (%s) slot=%s" % (i, mi.get_name(), mi.get_path_name()[:90], sn))\n',
'        else:\n',
'            print("  Slot %d: NONE" % i)\n',
'\n',
'    slot_fixes = {\n',
'        5: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Metal_2__Matcap__002",\n',
'        6: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Outline_005",\n',
'        7: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Material_021",\n',
'        8: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Outline_004",\n',
'        10: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Halftone_Circles___Circles__3_Inputs__001",\n',
'        11: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Material_022",\n',
'        14: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Outline_Shader_star_034",\n',
'        15: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Material_024",\n',
'    }\n',
'    fixed = 0\n',
'    errors = 0\n',
'    for slot_idx, mi_path in slot_fixes.items():\n',
'        mi = unreal.EditorAssetLibrary.load_asset(mi_path)\n',
'        if mi:\n',
'            if slot_idx < len(materials):\n',
'                materials[slot_idx].set_editor_property("material_interface", mi)\n',
'                print("  Slot %d: set to %s" % (slot_idx, mi_path))\n',
'                fixed += 1\n',
'            else:\n',
'                print("  ERROR Slot %d: index out of range" % slot_idx)\n',
'                errors += 1\n',
'        else:\n',
'            print("  ERROR Slot %d: MI not found at %s" % (slot_idx, mi_path))\n',
'            errors += 1\n',
'    if fixed > 0:\n',
'        mesh.set_editor_property("materials", materials)\n',
'        unreal.EditorAssetLibrary.save_asset("/Game/Melodia/Characters/Melusina/SK_Melusina")\n',
'        print("Saved SK_Melusina with %d fixes" % fixed)\n',
'    mesh2 = unreal.EditorAssetLibrary.load_asset("/Game/Melodia/Characters/Melusina/SK_Melusina")\n',
'    mats2 = mesh2.get_editor_property("materials")\n',
'    print("=== After fix ===")\n',
'    for i, m in enumerate(mats2):\n',
'        mi = m.get_editor_property("material_interface")\n',
'        if mi:\n',
'            print("  Slot %d: %s (%s)" % (i, mi.get_name(), mi.get_path_name()[:90]))\n',
'        else:\n',
'            print("  Slot %d: NONE" % i)\n',
'    print("Fixed: %d, Errors: %d" % (fixed, errors))\n',
])

result = monolith("editor_query", {"action":"run_python","command":script})
print(result)
