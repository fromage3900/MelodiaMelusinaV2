import json, urllib.request
MCP = "http://127.0.0.1:9316/mcp"
def ct(n,a):
    p={"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}
    r=urllib.request.Request(MCP,data=json.dumps(p).encode(),headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(r,timeout=15).read().decode())
def gt(r):
    return r.get("result",{}).get("content",[{}])[0].get("text","")

# Create M_Niagara_Foliage clean master
r = ct("material_query", {"action":"create_material","params":{"save_path":"/Game/EnvSandbox/Materials/Masters/M_Niagara_Foliage"}})
print("create:", gt(r)[:200])

a = "/Game/EnvSandbox/Materials/Masters/M_Niagara_Foliage.M_Niagara_Foliage"
r = ct("material_query", {"action":"set_material_property","params":{
    "asset_path":a, "blend_mode":"BLEND_Translucent", "shading_model":"MSM_Unlit",
    "two_sided":True, "used_with_niagara_sprites":True, "used_with_niagara_ribbons":True
}})
print("props:", gt(r)[:200])

r = ct("material_query", {"action":"get_compilation_stats","params":{"asset_path":a}})
text = gt(r)
data = json.loads(text) if text and "Failed" not in text else {}
errs = len(data.get("compile_errors",[]))
compiled = data.get("is_compiled","?")
print("compiled:", compiled, "errors:", errs)

# Create foliage MIs
tx_root = "/Game/EnvSandbox/Textures/Melusina/FoliageCards"
foliage = [
    ("MI_Niagara_Foliage_Grass", "T_FoliageCards_grass1"),
    ("MI_Niagara_Foliage_Leaf1", "T_FoliageCards_leaf1"),
    ("MI_Niagara_Foliage_Leaf2", "T_FoliageCards_leaf2"),
    ("MI_Niagara_Foliage_Leaf3", "T_FoliageCards_leaf3"),
    ("MI_Niagara_Foliage_Vine", "T_FoliageCards_sheetmusicvine"),
]
for mi_name, tx_name in foliage:
    mi_path = f"/Game/EnvSandbox/Materials/Masters/{mi_name}"
    r = ct("material_query", {"action":"create_material_instance","params":{"asset_path":mi_path, "parent_material": a}})
    ok = not r.get("result",{}).get("isError",False)
    if ok:
        tx_full = f"{tx_root}/{tx_name}.{tx_name}"
        mi_full = f"{mi_path}.{mi_name}"
        ct("material_query", {"action":"set_instance_parameter","params":{"asset_path":mi_full, "parameter_name":"Param", "texture_value": tx_full}})
        ct("material_query", {"action":"save_material","params":{"asset_path":mi_full}})
    status = "OK" if ok else "FAIL"
    print(f"  {mi_name}: {status}")

ct("material_query", {"action":"save_material","params":{"asset_path":a}})
print("Master saved.")

# Update systems
print("\nUpdating foliage systems...")
mapping = {"Grass":"MI_Niagara_Foliage_Grass","Bush":"MI_Niagara_Foliage_Leaf1","Vine":"MI_Niagara_Foliage_Vine"}
for tag, mi_name in mapping.items():
    sys_name = f"NS_SDF_Foliage_{tag}"
    emitter = "GrassBlades" if tag == "Grass" else ("BushCluster" if tag == "Bush" else "VineStrands")
    mat = f"/Game/EnvSandbox/Materials/Masters/{mi_name}.{mi_name}"
    sys_path = f"/Game/EnvSandbox/VFX/Systems/Sakura/{sys_name}.{sys_name}"
    r = ct("niagara_query", {"action":"set_renderer_material","params":{"asset_path":sys_path, "emitter":emitter, "renderer_index":0, "material":mat}})
    print(f"  {sys_name} -> {mi_name}: mat set")
    ct("niagara_query", {"action":"save_system","params":{"asset_path":sys_path}})

print("\nAll done.")
