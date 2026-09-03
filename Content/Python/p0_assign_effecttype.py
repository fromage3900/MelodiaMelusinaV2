"""Phase 0.2: Configure EffectType and assign to all systems"""
import json, urllib.request

MCP = "http://127.0.0.1:9316/mcp"
EFT = "/Game/EnvSandbox/VFX/EffectTypes/ENV_SakuraVFX.ENV_SakuraVFX"
SAKURA = "/Game/EnvSandbox/VFX/Systems/Sakura"

def ct(n,a,timeout=15):
    p={"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}
    r=urllib.request.Request(MCP,data=json.dumps(p).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=timeout) as resp:
        return json.loads(resp.read().decode())
def gt(r):
    return r.get("result",{}).get("content",[{}])[0].get("text","")

# Set scalability settings - try set_scalability_settings
r = ct("niagara_query", {"action":"set_scalability_settings","params":{
    "asset_path": EFT,
}})
print(f"set_scalability_settings: {gt(r)[:200]}")

# Try set_effect_type_property
for prop_name, val in [("bCullByDistance", True), ("CullDistanceMax", 10000.0), ("CullDistanceMin", 2000.0)]:
    r = ct("niagara_query", {"action":"set_effect_type_property","params":{
        "asset_path": EFT,
        "property": prop_name,
        "value": val,
    }})
    print(f"set_effect_type_property({prop_name}={val}): {gt(r)[:100]}")

# Save
r = ct("niagara_query", {"action":"save_system","params":{"asset_path": EFT}})
print(f"save: {gt(r)[:100]}")

# Now assign to all 10 systems
sakura_systems = [
    "NS_SakuraPetals", "NS_SakuraPetals_v2", "NS_SakuraGroundPetals",
    "NS_SakuraPetalGust", "NS_SakuraDreamSparkle", "NS_SakuraLanternMotes",
    "NS_SakuraPondShimmer", "NS_SakuraWaterPetals", "NS_WindRibbonGust",
    "NS_ConstellationDraw",
]
print()
for sys in sakura_systems:
    a = f"{SAKURA}/{sys}.{sys}"
    r = ct("niagara_query", {"action":"set_effect_type","params":{"asset_path": a, "effect_type": EFT}})
    ok = not r.get("result",{}).get("isError",False)
    print(f"  assign {sys}: {'OK' if ok else 'FAIL: ' + gt(r)[:80]}")
    
    # Save
    r = ct("niagara_query", {"action":"save_system","params":{"asset_path": a}})
    ok = not r.get("result",{}).get("isError",False)
    print(f"    save {sys}: {'OK' if ok else 'FAIL'}")
