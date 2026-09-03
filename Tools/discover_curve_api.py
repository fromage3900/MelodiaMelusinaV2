#!/usr/bin/env python3
"""Discover RuntimeCurveLinearColor API and apply TP_Melusina."""
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

# Discover RuntimeCurveLinearColor API
print("=== RuntimeCurveLinearColor API ===")
rc = unreal.RuntimeCurveLinearColor()
for p in dir(rc):
    if not p.startswith("_"):
        print("  {}".format(p))

# The keys/curves might be accessed differently in 5.8
# Try ExternalCurve or Curves
try:
    ec = rc.get_editor_property("ExternalCurve")
    print("ExternalCurve: {}".format(ec))
except:
    print("No ExternalCurve")

try:
    c = rc.get_editor_property("Curves")
    print("Curves: {} type={}".format(c, type(c).__name__ if c else "None"))
    if c:
        print("  dir: {}".format([x for x in dir(c) if not x.startswith("_")]))
except Exception as e:
    print("Curves error: {}".format(str(e)[:80]))

# Try assigning directly via copy
print("\\n=== Try constructing struct ===")
# Create a new curve with keys by constructing the InternalCurveInfo/Keys
try:
    # In some UE versions, you assign keys via curve editor data
    # Let's check if we can modify in-place
    tp = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina")
    s = tp.get_editor_property("Settings")
    
    # Try directly setting via export_text on the settings struct
    print("Settings export_text: {}".format(s.export_text()[:500]))
    
    # Try importing text
    new_text = "(DiffuseRamp=(ColorCurves[0]=(Keys=((Time=0.0,Value=0.034),(Time=0.3,Value=1.0),(Time=1.0,Value=1.08))),ColorCurves[1]=(Keys=((Time=0.0,Value=0.022),(Time=0.3,Value=1.0),(Time=1.0,Value=1.04))),ColorCurves[2]=(Keys=((Time=0.0,Value=0.047),(Time=0.3,Value=1.0),(Time=1.0,Value=0.98))),ColorCurves[3]=(Keys=((Time=0.0,Value=1.0),(Time=0.3,Value=1.0),(Time=1.0,Value=1.0)))),SpecularRamp=(ColorCurves[0]=(Keys=((Time=0.9,Value=1.0))),ColorCurves[1]=(Keys=((Time=0.9,Value=1.0))),ColorCurves[2]=(Keys=((Time=0.9,Value=1.0))),ColorCurves[3]=(Keys=((Time=0.9,Value=1.0)))),ShadowExtinctionCoefficient=0.300000,DiffuseIndirectScale=0.300000,SpecularIndirectScale=0.300000)"
    print("\\nTrying import_text on Settings...")
    new_s = s.import_text(new_text)
    print("import_text result: {} type={}".format(new_s, type(new_s).__name__ if new_s else "None"))
    
    if new_s:
        # Set it back
        tp.set_editor_property("Settings", new_s)
        unreal.EditorAssetLibrary.save_asset("/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina")
        print("SAVED")
        
        # Verify
        tp2 = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina")
        s2 = tp2.get_editor_property("Settings")
        print("Verify export_text: {}".format(s2.export_text()[:500]))
    else:
        print("import_text returned None")
except Exception as e:
    print("Error: {}".format(str(e)[:300]))
    import traceback
    traceback.print_exc()
"""
result = monolith("editor_query", {"action":"run_python","command":script})
print(result)
