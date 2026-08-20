#!/usr/bin/env python3
"""Discover correct API to set materials on SkeletalMesh in UE5.8."""
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

mesh = unreal.EditorAssetLibrary.load_asset("/Game/Melodia/Characters/Melusina/SK_Melusina")
if not mesh:
    print("ERROR: SK_Melusina not found")

# Discover mesh API
print("=== SK_Melusina mesh methods ===")
for p in dir(mesh):
    if not p.startswith("_") and (p.startswith("get") or p.startswith("set") or p.startswith("add") or "material" in p.lower() or "slot" in p.lower()):
        print("  {}".format(p))

# Check for material slots
print("\\n=== Materials ===")
try:
    mats = mesh.get_materials()
    print("get_materials() type={} count={}".format(type(mats).__name__, len(mats)))
    for i, m in enumerate(mats):
        if m:
            print("  Slot {}: {} ({})".format(i, m.get_name(), m.get_path_name()[:80]))
        else:
            print("  Slot {}: NONE".format(i))
except Exception as e:
    print("get_materials error: {}".format(str(e)[:100]))

# Check for set_material or assign
for method_name in ["set_material", "set_material_by_name", "set_material_index"]:
    try:
        fn = getattr(mesh, method_name, None)
        if fn:
            print("\\n{} exists: {}".format(method_name, fn))
    except:
        pass

# Try using the editor subsystem
print("\\n=== SkeletalMeshEditorSubsystem ===")
subsys = unreal.SkeletalMeshEditorSubsystem()
if subsys:
    print("SkeletalMeshEditorSubsystem loaded")
    for p in dir(subsys):
        if not p.startswith("_") and ("material" in p.lower() or "slot" in p.lower()):
            print("  {}".format(p))
    
    # Try to assign materials
    try:
        result = subsys.get_number_of_material_slots(mesh)
        print("get_number_of_material_slots: {}".format(result))
    except Exception as e:
        print("get_number_of_material_slots error: {}".format(str(e)[:100]))

# Try direct materials array access
print("\\n=== Direct materials array ===")
try:
    # Materials might be accessible through the static mesh's material array
    materials_prop = mesh.get_editor_property("materials") 
    print("materials prop: {} type={}".format(str(materials_prop)[:200], type(materials_prop).__name__))
    if isinstance(materials_prop, list):
        for i, m in enumerate(materials_prop):
            print("  [{}]: {}".format(i, str(m)[:100]))
except Exception as e:
    print("materials prop error: {}".format(str(e)[:100]))

# Try mesh_utilities
print("\\n=== MeshUtilities ===")
try:
    mu = unreal.MeshUtilities()
    if mu:
        for p in dir(mu):
            if not p.startswith("_") and ("material" in p.lower() or "slot" in p.lower()):
                print("  {}".format(p))
except Exception as e:
    print("MeshUtilities error: {}".format(str(e)[:100]))

# Try StaticMeshEditorSubsystem (maybe it works for skeletal too)
print("\\n=== StaticMeshEditorSubsystem ===")
try:
    sme = unreal.StaticMeshEditorSubsystem()
    if sme:
        for p in dir(sme):
            if not p.startswith("_") and ("material" in p.lower() or "slot" in p.lower()):
                print("  {}".format(p))
except Exception as e:
    print("StaticMeshEditorSubsystem error: {}".format(str(e)[:100]))
"""
result = monolith("editor_query", {"action":"run_python","command":script})
print(result)
