#!/usr/bin/env python3
"""Fix TP_Melusina using proper UE5.8 ToonProfileStruct API."""
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

print("="*60)
print("TP_Melusina Fix v2 - Using Struct Construction")
print("="*60)

script = """
import unreal

tp = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina")
if not tp:
    print("ERROR: TP_Melusina not found")

# First try: see if Settings can be set via set_editor_property with a dict
print("=== Method 1: Try getting current Settings ===")
s = tp.get_editor_property("Settings")
print("Settings type: " + type(s).__name__)
print("Settings repr: " + repr(s)[:500])

# Try to access struct fields via _post_init
if hasattr(s, "_post_init"):
    print("Has _post_init")
    try:
        pi = s._post_init()
        print("_post_init: " + str(pi)[:300])
    except Exception as e:
        print("_post_init error: " + str(e)[:100])

# Try constructing a new struct
print("\\n=== Method 2: Try constructing ToonProfileStruct ===")
try:
    # Try to find the struct in unreal module
    struct_class = getattr(unreal, "ToonProfileStruct", None)
    if struct_class:
        print("Found ToonProfileStruct class: " + str(struct_class))
        # Try creating with kwargs
        new_settings = struct_class()
        print("Created new ToonProfileStruct")
        # Try setting fields
        for f in dir(new_settings):
            if not f.startswith("_"):
                print("  field: " + f)
    else:
        print("ToonProfileStruct not in unreal module")
        # Try finding it
        for name in sorted(dir(unreal)):
            if "oon" in name.lower() or "rofile" in name.lower() or "profile" in name.lower():
                print("Found candidate: " + name)
except Exception as e:
    print("Struct construction error: " + str(e)[:200])

# Method 3: Use call_method to set each property
print("\\n=== Method 3: Direct field access on Settings ===")
try:
    settings_fields = ["DiffuseRamp", "SpecularRamp", "DiffuseIndirectScale", 
                       "SpecularIndirectScale", "ShadowExtinctionCoefficient",
                       "ShadowHatchingPattern", "ShadowHatchingPatternDistributionRamp",
                       "SpecularIndirectRamp"]
    for field in settings_fields:
        try:
            val = s.get_editor_property(field)
            print("s.{} = {} ({})".format(field, str(val)[:100], type(val).__name__ if val else "None"))
        except Exception as e:
            print("s.{}: get_editor_property error: {}".format(field, str(e)[:80]))
except Exception as e:
    print("Settings access error: {}".format(str(e)[:100]))

# Method 4: Try importing text
print("\\n=== Method 4: Try import_asset_text ===")
try:
    t3d = \"\"\"Begin Object Class=/Script/Engine.ToonProfile Name="TP_Melusina" ExportPath="/Script/Engine.ToonProfile'/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina.TP_Melusina'"
   Settings=(DiffuseRamp=(ColorCurves[0]=(Keys=((Time=0.0,Value=0.034),(Time=0.3,Value=1.0),(Time=1.0,Value=1.08))),ColorCurves[1]=(Keys=((Time=0.0,Value=0.022),(Time=0.3,Value=1.0),(Time=1.0,Value=1.04))),ColorCurves[2]=(Keys=((Time=0.0,Value=0.047),(Time=0.3,Value=1.0),(Time=1.0,Value=0.98))),ColorCurves[3]=(Keys=((Time=0.0,Value=1.0),(Time=0.3,Value=1.0),(Time=1.0,Value=1.0)))),SpecularRamp=(ColorCurves[0]=(Keys=((Time=0.9,Value=1.0))),ColorCurves[1]=(Keys=((Time=0.9,Value=1.0))),ColorCurves[2]=(Keys=((Time=0.9,Value=1.0))),ColorCurves[3]=(Keys=((Time=0.9,Value=1.0)))),ShadowExtinctionCoefficient=0.300000,ShadowHatchingPattern=/Game/EnvSandbox/Materials/ToonProfiles/T_HatchPattern.T_HatchPattern,DiffuseIndirectScale=0.300000,SpecularIndirectScale=0.300000)
End Object
\"\"\"
    imported = unreal.EditorAssetLibrary.import_asset_text(
        "/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina",
        "/Script/Engine.ToonProfile",
        t3d
    )
    print("import_asset_text result: " + str(imported)[:200])
except Exception as e:
    print("import_asset_text error: " + str(e)[:200])
    print("Import text might not exist in 5.8 API")

print("\\n=== Done ===")
"""
result = monolith("editor_query", {"action":"run_python","command":script})
print(result)
