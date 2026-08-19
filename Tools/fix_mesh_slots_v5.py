#!/usr/bin/env python3
"""Fix SK_Melusina material slots using correct SkeletalMaterial struct."""
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
'    old_mats = mesh.get_editor_property("materials")\n',
'    fix_map = {\n',
'        0: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Gradient__Radial__002",\n',
'        5: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Metal_2__Matcap__002",\n',
'        6: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Outline_005",\n',
'        7: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Material_021",\n',
'        8: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Outline_004",\n',
'        10: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Halftone_Circles___Circles__3_Inputs__001",\n',
'        11: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Material_022",\n',
'        14: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Outline_Shader_star_034",\n',
'        15: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Material_024",\n',
'    }\n',
'    new_mats = []\n',
'    for i, old in enumerate(old_mats):\n',
'        if i in fix_map:\n',
'            mi = unreal.EditorAssetLibrary.load_asset(fix_map[i])\n',
'            if mi:\n',
'                slot = unreal.SkeletalMaterial()\n',
'                slot.set_editor_property("material_interface", mi)\n',
'                slot.set_editor_property("material_slot_name", old.get_editor_property("material_slot_name"))\n',
'                # uv_channel_data is read-only, skip it\n',
'                new_mats.append(slot)\n',
'                print("  Slot %d: MI_Melusina_%s -> %s" % (i, fix_map[i].split("_")[-1].split(".")[0], mi.get_name()))\n',
'            else:\n',
'                print("  Slot %d: FAILED to load %s" % (i, fix_map[i]))\n',
'                new_mats.append(old)\n',
'        else:\n',
'            new_mats.append(old)\n',
'    mesh.set_editor_property("materials", new_mats)\n',
'    unreal.EditorAssetLibrary.save_asset("/Game/Melodia/Characters/Melusina/SK_Melusina")\n',
'    print("\\nSaved with %d fixes" % len(fix_map))\n',
'    mesh2 = unreal.EditorAssetLibrary.load_asset("/Game/Melodia/Characters/Melusina/SK_Melusina")\n',
'    print("\\nAfter:")\n',
'    for i, m in enumerate(mesh2.get_editor_property("materials")):\n',
'        mi = m.get_editor_property("material_interface")\n',
'        if mi:\n',
'            print("  Slot %d: %s" % (i, mi.get_name()[:70]))\n',
'        else:\n',
'            print("  Slot %d: NONE" % i)\n',
])

result = monolith("editor_query", {"action":"run_python","command":script})
print(result)
