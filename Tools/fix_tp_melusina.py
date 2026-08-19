#!/usr/bin/env python3
"""Diagnose TP_Melusina asset properties and fix the spec."""
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

# Step 1: Full export text
print("="*60)
print("FULL TP_Melusina EXPORT")
print("="*60)
text = monolith("project_query", {"action":"export_asset_text","asset_path":"/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina"})
print(text)

# Step 2: Read properties via Python API
print("\n"+"="*60)
print("TP_Melusina SETTINGS PROPERTIES")
print("="*60)
script = """
import unreal
tp = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina")
if tp:
    s = tp.get_editor_property("Settings")
    props = [p for p in dir(s) if not p.startswith("_")]
    for p in sorted(props):
        try:
            v = s.get_editor_property(p)
            print("{}: {} = {}".format(p, type(v).__name__, str(v)[:120]))
        except Exception as e:
            print("{}: ERROR = {}".format(p, str(e)[:80]))
else:
    print("TP_Melusina not found")
"""
result = monolith("editor_query", {"action":"run_python","command":script})
print(result[:3000])

# Step 3: Write corrected spec
print("\n"+"="*60)
print("APPLYING CORRECTED VALUES")
print("="*60)

# Based on export, the actual property names are:
# DiffuseRamp (curve), SpecularRamp (curve), ShadowExtinctionCoefficient (scalar 0.3)
# DiffuseIndirectScale (scalar 0.3), SpecularIndirectScale (scalar 0.3)
# ShadowHatchingPatternDistributionRamp (curve, not a texture path!)
# SpecularIndirectRamp (curve, not in our spec)

# Fix: set scalars that failed
script2 = """
import unreal
tp = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina")
if tp:
    s = tp.get_editor_property("Settings")
    
    # Set ShadowExtinctionCoefficient (was ShadowingExtinction in old spec)
    s.set_editor_property("ShadowExtinctionCoefficient", 0.3)
    
    # Set curves - DiffuseRamp: shadow=violet, mid=white, lit=warm
    c = unreal.RuntimeCurveLinearColor()
    c.add_key(0.0, unreal.LinearColor(0.034, 0.022, 0.047, 1.0))
    c.add_key(0.3, unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
    c.add_key(1.0, unreal.LinearColor(1.08, 1.04, 0.98, 1.0))
    s.set_editor_property("DiffuseRamp", c)
    
    # Set SpecularRamp
    c2 = unreal.RuntimeCurveLinearColor()
    c2.add_key(0.9, unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
    s.set_editor_property("SpecularRamp", c2)
    
    # Set ShadowHatchingPatternDistributionRamp (curve, not texture)
    hat = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/Materials/ToonProfiles/T_HatchPattern")
    if hat:
        s.set_editor_property("ShadowHatchingPattern", hat)
        print("ShadowHatchingPattern set to T_HatchPattern")
    
    tp.set_editor_property("Settings", s)
    unreal.EditorAssetLibrary.save_asset("/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina")
    print("ALL VALUES APPLIED SUCCESSFULLY")
else:
    print("ERROR: Could not load TP_Melusina")
"""
result2 = monolith("editor_query", {"action":"run_python","command":script2})
print(result2[:2000])

# Step 4: Verify
print("\n"+"="*60)
print("VERIFICATION - Re-export")
print("="*60)
text2 = monolith("project_query", {"action":"export_asset_text","asset_path":"/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina","grep_pattern":"Settings"})
print(text2[:2000])
