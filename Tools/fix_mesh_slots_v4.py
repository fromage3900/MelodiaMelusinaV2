#!/usr/bin/env python3
"""Fix SK_Melusina material slots by rebuilding the materials array."""
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
'    mats = mesh.get_editor_property("materials")\n',
'    print("Before: %d slots" % len(mats))\n',
'    fix_map = {\n',
'        5: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Metal_2__Matcap__002",\n',
'        6: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Outline_005",\n',
'        7: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Material_021",\n',
'        8: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Outline_004",\n',
'        10: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Halftone_Circles___Circles__3_Inputs__001",\n',
'        11: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Material_022",\n',
'        14: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Outline_Shader_star_034",\n',
'        15: "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Material_024",\n',
'    }\n',
'    fix_map[0] = "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_Gradient__Radial__002"\n',
'    new_mats = []\n',
'    for i, old_mat in enumerate(mats):\n',
'        try:\n',
'            if i in fix_map:\n',
'                mi_path = fix_map[i]\n',
'                mi = unreal.EditorAssetLibrary.load_asset(mi_path)\n',
'                if mi:\n',
'                    old_slot_name = old_mat.get_editor_property("material_slot_name") or ""\n',
'                    new_struct = unreal.SkeletalMeshMaterialSlot()\n',
'                    new_struct.set_editor_property("material_interface", mi)\n',
'                    new_struct.set_editor_property("material_slot_name", old_slot_name)\n',
'                    new_mats.append(new_struct)\n',
'                    print("  Slot %d -> %s" % (i, mi.get_name()))\n',
'                else:\n',
'                    print("  ERROR: Could not load %s" % mi_path)\n',
'                    new_mats.append(old_mat)\n',
'            else:\n',
'                new_mats.append(old_mat)\n',
'        except Exception as e:\n',
'            print("  ERROR Slot %d: %s" % (i, str(e)[:100]))\n',
'            new_mats.append(old_mat)\n',
'    try:\n',
'        mesh.set_editor_property("materials", new_mats)\n',
'        unreal.EditorAssetLibrary.save_asset("/Game/Melodia/Characters/Melusina/SK_Melusina")\n',
'        print("Saved with %d fixes" % len(fix_map))\n',
'    except Exception as e:\n',
'        print("set_editor_property error: %s" % str(e)[:200])\n',
'    mesh2 = unreal.EditorAssetLibrary.load_asset("/Game/Melodia/Characters/Melusina/SK_Melusina")\n',
'    mats2 = mesh2.get_editor_property("materials")\n',
'    print("After:")\n',
'    for i, m in enumerate(mats2):\n',
'        mi = m.get_editor_property("material_interface")\n',
'        if mi:\n',
'            print("  Slot %d: %s" % (i, mi.get_name()[:60]))\n',
'        else:\n',
'            print("  Slot %d: NONE" % i)\n',
])

result = monolith("editor_query", {"action":"run_python","command":script})
print(result)
