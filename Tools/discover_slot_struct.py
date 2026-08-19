#!/usr/bin/env python3
"""Discover SkeletalMesh material slot struct class."""
import json, sys, urllib.request

MCP = "http://127.0.0.1:9316/mcp"

def monolith(tool, args, timeout=30):
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
'if mesh:\n',
'    mats = mesh.get_editor_property("materials")\n',
'    if len(mats) > 0:\n',
'        first = mats[0]\n',
'        print("Type: %s" % type(first).__name__)\n',
'        print("Module: %s" % type(first).__module__)\n',
'        print("Dir: %s" % [p for p in dir(first) if not p.startswith("_")])\n',
'        print("Repr: %s" % repr(first)[:300])\n',
'        try:\n',
'            d = first.to_dict()\n',
'            print("to_dict: %s" % d)\n',
'        except:\n',
'            pass\n',
'        try:\n',
'            t = first.to_tuple()\n',
'            print("to_tuple: %s" % t)\n',
'        except:\n',
'            pass\n',
'        try:\n',
'            et = first.export_text()\n',
'            print("export_text: %s" % et[:500])\n',
'        except:\n',
'            pass\n',
'    # Search unreal for all classes with "Mesh" or "Material" and "Slot"\n',
'    matches = []\n',
'    for name in dir(unreal):\n',
'        if "aterial" in name and "lot" in name:\n',
'            matches.append(name)\n',
'        if "esh" in name and "lot" in name:\n',
'            matches.append(name)\n',
'    if matches:\n',
'        print("\\nCandidates: %s" % matches)\n',
])
result = monolith("editor_query", {"action":"run_python","command":script})
print(result)
