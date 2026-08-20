#!/usr/bin/env python3
"""Discover UE5.8 Python API for ToonProfile and curves."""
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

# Discover the TP settings API
script = """
import unreal

tp = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina")
if tp:
    print("=== TP_Melusina dir ===")
    for p in dir(tp):
        print("  {}".format(p))
    
    s = tp.get_editor_property("Settings")
    print("\\n=== Settings type: {} ===".format(type(s).__name__))
    
    # Try accessing as dict/struct
    for method_name in ["to_dict", "to_tuple", "keys", "values", "items", "property_names"]:
        try:
            method = getattr(s, method_name, None)
            if method:
                result = method()
                print("{}(): {} = {}".format(method_name, type(result).__name__, str(result)[:200]))
        except Exception as e:
            print("{}: ERROR {}".format(method_name, str(e)[:80]))
    
    # Try direct attribute access
    for field in ["DiffuseRamp", "SpecularRamp", "DiffuseIndirectScale", "SpecularIndirectScale", "ShadowExtinctionCoefficient", "ShadowHatchingPattern", "ShadowHatchingPatternDistributionRamp"]:
        try:
            val = getattr(s, field, "NOT_FOUND")
            print("  s.{} = {} ({})".format(field, str(val)[:100], type(val).__name__))
        except Exception as e:
            print("  s.{}: ERROR {}".format(field, str(e)[:80]))

    # Understand curve type
    try:
        ramp = getattr(s, "DiffuseRamp", None)
        if ramp:
            print("\\n=== DiffuseRamp dir ===")
            for p in dir(ramp):
                print("  {}".format(p))
            # Try to understand curve API
            for method_name in ["keys", "add_key", "add", "ExternalCurve", "get_editor_property", "set_editor_property", "Curves", "KeyHandles", "DrawInfo"]:
                try:
                    val = getattr(ramp, method_name, "NOT_FOUND")
                    if val != "NOT_FOUND":
                        print("  ramp.{}: {} ({})".format(method_name, str(val)[:150], type(val).__name__))
                except Exception as e:
                    pass
    except Exception as e:
        print("DiffuseRamp access error: {}".format(str(e)[:100]))
else:
    print("TP_Melusina not found")
"""
result = monolith("editor_query", {"action":"run_python","command":script})
print(result)
