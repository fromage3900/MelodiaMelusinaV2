"""Verify Phase 0 changes"""
import json, urllib.request

MCP = "http://127.0.0.1:9316/mcp"
SAKURA = "/Game/EnvSandbox/VFX/Systems/Sakura"

def ct(n,a):
    p={"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}
    r=urllib.request.Request(MCP,data=json.dumps(p).encode(),headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(r,timeout=15).read().decode())
def gt(r):
    return r.get("result",{}).get("content",[{}])[0].get("text","")

sprite_checks = [
    ("NS_SakuraPetals_v2", "Petals", 0),
    ("NS_SakuraDreamSparkle", "DreamMotes", 0),
    ("NS_SakuraLanternMotes", "LanternMotes", 0),
    ("NS_SakuraPetalGust", "OmnidirectionalBurst", 0),
    ("NS_WindRibbonGust", "E_OmnidirectionalPetalBurst", 0),
    ("NS_ConstellationDraw", "Stars", 0),
]

print("=== Verify sprites: bCastShadows + SortMode ===")
for sys, em, ri in sprite_checks:
    a = f"{SAKURA}/{sys}.{sys}"
    r = ct("niagara_query", {"action":"list_renderer_properties","params":{"asset_path":a, "emitter":em, "renderer_index":ri}})
    text = gt(r)
    if "bCastShadows" in text:
        # Extract bCastShadows value
        for line in text.split(","):
            if "bCastShadows" in line:
                print(f"  {sys}/{em}: {line.strip()}")
            if "SortMode" in line:
                print(f"  {sys}/{em}: {line.strip()}")

print("\n=== Verify remaining MIs ===")
remaining = [
    ("NS_SakuraPetals_v2", "EM_PondRipple", 0, "MI_Niagara_Pond"),
    ("NS_SakuraPetals_v2", "EM_PetalPile", 0, "MI_Niagara_Petal"),
    ("NS_WindRibbonGust", "E_OmnidirectionalPetalBurst", 0, "MI_Niagara_Gust"),
]
for sys, em, ri, expected in remaining:
    a = f"{SAKURA}/{sys}.{sys}"
    r = ct("niagara_query", {"action":"list_renderers","params":{"asset_path":a, "emitter":em}})
    text = gt(r)
    for rend in json.loads(text).get("renderers",[]):
        if rend.get("index") == ri:
            rm = rend.get("material","?")
            ok = expected in rm
            print(f"  {'OK' if ok else 'MISMATCH'}: {sys}/{em}[{ri}] -> {rm.split('/')[-1]}")

print("\n=== Verify warmup ===")
for sys in ["NS_SakuraDreamSparkle", "NS_SakuraWaterPetals"]:
    a = f"{SAKURA}/{sys}.{sys}"
    r = ct("niagara_query", {"action":"get_system_summary","params":{"asset_path":a}})
    text = gt(r)
    data = json.loads(text)
    warmup = data.get("system_properties",{}).get("warmup_time","?")
    print(f"  {sys} warmup={warmup}s")

print("\n=== Verify EffectType on all systems ===")
for sys in ["NS_SakuraPetals","NS_SakuraPetals_v2","NS_SakuraGroundPetals","NS_SakuraPetalGust",
            "NS_SakuraDreamSparkle","NS_SakuraLanternMotes","NS_SakuraPondShimmer",
            "NS_SakuraWaterPetals","NS_WindRibbonGust","NS_ConstellationDraw"]:
    a = f"{SAKURA}/{sys}.{sys}"
    r = ct("niagara_query", {"action":"get_system_summary","params":{"asset_path":a}})
    text = gt(r)
    data = json.loads(text)
    etype = data.get("system_properties",{}).get("effect_type","?")
    print(f"  {sys}: effect_type={etype}")
