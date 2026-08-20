#!/usr/bin/env python3
"""Final TP_Melusina fix using struct import_text."""
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

script = """
import unreal

tp = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina")
if not tp:
    print("ERROR: TP_Melusina not found")

s = tp.get_editor_property("Settings")
print("Before: " + s.export_text()[:300])

# Build import text with all values
# DiffuseRamp: ColorCurves[0]=R, [1]=G, [2]=B, [3]=A
# Keys: shadow=violet(0.034,0.022,0.047,1), mid=white(1,1,1,1), lit=warm(1.08,1.04,0.98,1)
import_text = (
    "(DiffuseRamp=("
    "ColorCurves[0]=(Keys=((Time=0.0,Value=0.034),(Time=0.3,Value=1.0),(Time=1.0,Value=1.08)),DefaultValue=0.0,PreInfinityExtrap=RCCE_Constant,PostInfinityExtrap=RCCE_Constant),"
    "ColorCurves[1]=(Keys=((Time=0.0,Value=0.022),(Time=0.3,Value=1.0),(Time=1.0,Value=1.04)),DefaultValue=0.0,PreInfinityExtrap=RCCE_Constant,PostInfinityExtrap=RCCE_Constant),"
    "ColorCurves[2]=(Keys=((Time=0.0,Value=0.047),(Time=0.3,Value=1.0),(Time=1.0,Value=0.98)),DefaultValue=0.0,PreInfinityExtrap=RCCE_Constant,PostInfinityExtrap=RCCE_Constant),"
    "ColorCurves[3]=(Keys=((Time=0.0,Value=1.0),(Time=0.3,Value=1.0),(Time=1.0,Value=1.0)),DefaultValue=1.0,PreInfinityExtrap=RCCE_Constant,PostInfinityExtrap=RCCE_Constant)"
    "),"
    "SpecularRamp=("
    "ColorCurves[0]=(Keys=((Time=0.9,Value=1.0)),DefaultValue=0.0,PreInfinityExtrap=RCCE_Constant,PostInfinityExtrap=RCCE_Constant),"
    "ColorCurves[1]=(Keys=((Time=0.9,Value=1.0)),DefaultValue=0.0,PreInfinityExtrap=RCCE_Constant,PostInfinityExtrap=RCCE_Constant),"
    "ColorCurves[2]=(Keys=((Time=0.9,Value=1.0)),DefaultValue=0.0,PreInfinityExtrap=RCCE_Constant,PostInfinityExtrap=RCCE_Constant),"
    "ColorCurves[3]=(Keys=((Time=0.9,Value=1.0)),DefaultValue=1.0,PreInfinityExtrap=RCCE_Constant,PostInfinityExtrap=RCCE_Constant)"
    "),"
    "ShadowExtinctionCoefficient=0.300000,"
    "DiffuseIndirectScale=0.300000,"
    "SpecularIndirectScale=0.300000"
    ")"
)

result = s.import_text(import_text)
print("import_text result: " + str(result))
print("After: " + s.export_text()[:500])

if result:
    tp.set_editor_property("Settings", s)
    unreal.EditorAssetLibrary.save_asset("/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina")
    print("SAVED")
    
    # Verify
    tp2 = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina")
    s2 = tp2.get_editor_property("Settings")
    print("Verify: " + s2.export_text()[:500])
else:
    print("import_text FAILED")
"""
result = monolith("editor_query", {"action":"run_python","command":script})
print(result)
