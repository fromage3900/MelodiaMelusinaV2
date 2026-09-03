import json, urllib.request
MCP = "http://127.0.0.1:9316/mcp"
def ct(n,a):
    p={"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}
    r=urllib.request.Request(MCP,data=json.dumps(p).encode(),headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(r,timeout=15).read().decode())
def gt(r):
    return r.get("result",{}).get("content",[{}])[0].get("text","")

# Verify material compilation
print("=== Material Compilation ===")
mats = [
    "Masters/M_SDF_ParallaxPulse_Niagara",
    "SDF/M_MusicalSDF_PulsingGeometry_Niagara",
    "Masters/M_Niagara_Foliage",
    "Masters/M_SDF_Foliage_Niagara",
]
for m in mats:
    a = f"/Game/EnvSandbox/Materials/{m}.{m.split('/')[-1]}"
    r = ct("material_query", {"action":"get_compilation_stats","params":{"asset_path":a}})
    text = gt(r)
    if "Failed" not in text:
        data = json.loads(text)
        errs = len(data.get("compile_errors",[]))
        compiled = data.get("is_compiled",False)
        print(f"  {m.split('/')[-1]}: compiled={compiled} errors={errs}")

# Verify systems
print("\n=== System Diagnostics ===")
systems = [
    "NS_SDF_ParallaxPulse", "NS_SDF_PulsingGeometry", "NS_SDF_ParallaxFish",
    "NS_SDF_Foliage_Grass", "NS_SDF_Foliage_Bush", "NS_SDF_Foliage_Vine"
]
for s in systems:
    a = f"/Game/EnvSandbox/VFX/Systems/Sakura/{s}.{s}"
    r = ct("niagara_query", {"action":"get_system_diagnostics","params":{"asset_path":a}})
    text = gt(r)
    try:
        data = json.loads(text)
        errs = data.get("error_count",-1)
        warns = data.get("warning_count",-1)
        print(f"  {s}: {errs} errors, {warns} warnings")
    except:
        print(f"  {s}: {text[:80]}")

# Check all MIs
print("\n=== Material Instance Verification ===")
mis = [
    "MI_Niagara_Foliage_Grass", "MI_Niagara_Foliage_Leaf1", "MI_Niagara_Foliage_Leaf2",
    "MI_Niagara_Foliage_Leaf3", "MI_Niagara_Foliage_Vine",
    "MI_Melusina_Cello", "MI_Melusina_Crystal", "MI_Melusina_Note", "MI_Melusina_Treble",
]
for mi in mis:
    for folder in ["Masters", "Instances/Melusina"]:
        a = f"/Game/EnvSandbox/Materials/{folder}/{mi}.{mi}"
        r = ct("material_query", {"action":"get_material_properties","params":{"asset_path":a}})
        if "Failed" not in gt(r):
            print(f"  {mi}: FOUND at {folder}")
            break
    else:
        print(f"  {mi}: NOT FOUND")

print("\n=== NPC ===")
r = ct("niagara_query", {"action":"get_npc","params":{"asset_path":"/Game/EnvSandbox/VFX/MPC/NPC_SakuraDream.NPC_SakuraDream"}})
print(gt(r)[:400])
