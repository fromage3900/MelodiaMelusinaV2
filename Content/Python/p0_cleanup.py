"""Phase 0.3-0.7: Fix shadows, MIs, warmup, sorting, bounds"""
import json, urllib.request

MCP = "http://127.0.0.1:9316/mcp"
SAKURA = "/Game/EnvSandbox/VFX/Systems/Sakura"
MATS = "/Game/EnvSandbox/VFX/Materials"

def ct(n,a,timeout=15):
    p={"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}
    r=urllib.request.Request(MCP,data=json.dumps(p).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=timeout) as resp:
        return json.loads(resp.read().decode())
def gt(r):
    return r.get("result",{}).get("content",[{}])[0].get("text","")
def ok(r):
    return not r.get("result",{}).get("isError",False)

# ====================================================
# 0.3: Fix shadows on sprite renderers + add ViewDepth sort
# ====================================================
print("=== 0.3: Fix sprite renderer properties ===")
sprite_renderers = [
    ("NS_SakuraPetals_v2", "Petals", 0),
    ("NS_SakuraDreamSparkle", "DreamMotes", 0),
    ("NS_SakuraLanternMotes", "LanternMotes", 0),
    ("NS_SakuraPetalGust", "OmnidirectionalBurst", 0),
    ("NS_WindRibbonGust", "E_OmnidirectionalPetalBurst", 0),
    ("NS_ConstellationDraw", "Stars", 0),
]
for sys, em, ri in sprite_renderers:
    a = f"{SAKURA}/{sys}.{sys}"
    # bCastShadows=False
    r = ct("niagara_query", {"action":"set_renderer_property","params":{
        "asset_path": a, "emitter": em, "renderer_index": ri,
        "property": "bCastShadows", "value": False
    }})
    print(f"  {sys}/{em}[{ri}] bCastShadows=0: {'OK' if ok(r) else gt(r)[:60]}")
    # SortMode=ViewDepth (value 2)
    r = ct("niagara_query", {"action":"set_renderer_property","params":{
        "asset_path": a, "emitter": em, "renderer_index": ri,
        "property": "SortMode", "value": 2
    }})
    print(f"  {sys}/{em}[{ri}] SortMode=ViewDepth: {'OK' if ok(r) else gt(r)[:60]}")

# ====================================================
# 0.4: Assign remaining MIs
# ====================================================
print("\n=== 0.4: Assign remaining MIs ===")
remaining = [
    ("NS_SakuraPetals_v2", "EM_PondRipple", 0, f"{MATS}/MI_Niagara_Pond.MI_Niagara_Pond"),
    ("NS_SakuraPetals_v2", "EM_PetalPile", 0, f"{MATS}/MI_Niagara_Petal.MI_Niagara_Petal"),
    ("NS_WindRibbonGust", "E_OmnidirectionalPetalBurst", 0, f"{MATS}/MI_Niagara_Gust.MI_Niagara_Gust"),
]
for sys, em, ri, mat in remaining:
    a = f"{SAKURA}/{sys}.{sys}"
    r = ct("niagara_query", {"action":"set_renderer_material","params":{
        "asset_path": a, "emitter": em, "renderer_index": ri, "material": mat
    }})
    print(f"  {sys}/{em}[{ri}] -> {mat.split('/')[-1]}: {'OK' if ok(r) else gt(r)[:60]}")

# ====================================================
# 0.5: Fix warmup anomalies
# ====================================================
print("\n=== 0.5: Fix warmup ===")
warmup_fixes = [
    ("NS_SakuraDreamSparkle", 0.0),
    ("NS_SakuraWaterPetals", 2.0),
]
for sys, warmup in warmup_fixes:
    a = f"{SAKURA}/{sys}.{sys}"
    r = ct("niagara_query", {"action":"set_system_property","params":{
        "asset_path": a, "property": "WarmupTime", "value": warmup
    }})
    print(f"  {sys} warmup={warmup}s: {'OK' if ok(r) else gt(r)[:60]}")

# ====================================================
# 0.6: Add DreamVisibility to NS_SakuraPondShimmer
# ====================================================
print("\n=== 0.6: Add DreamVisibility to PondShimmer ===")
a = f"{SAKURA}/NS_SakuraPondShimmer.NS_SakuraPondShimmer"
r = ct("niagara_query", {"action":"add_user_parameter","params":{
    "asset_path": a, "name": "DreamVisibility",
    "type": "NiagaraFloat", "default": 1.0
}})
print(f"  add DreamVisibility: {'OK' if ok(r) else gt(r)[:60]}")

# ====================================================
# 0.7: Set FixedBounds on unbounded systems
# ====================================================
print("\n=== 0.7: Set FixedBounds ===")
unbounded = [
    "NS_SakuraDreamSparkle", "NS_SakuraLanternMotes",
    "NS_SakuraPondShimmer", "NS_SakuraWaterPetals",
    "NS_WindRibbonGust", "NS_ConstellationDraw",
]
for sys in unbounded:
    a = f"{SAKURA}/{sys}.{sys}"
    # Set fixed bounds - need to figure out appropriate bounds per system
    # Default generous bounds: XYZ (-500..500, -500..500, -500..500)
    r = ct("niagara_query", {"action":"set_fixed_bounds","params":{
        "asset_path": a, "bounds_min": [-500,-500,-500], "bounds_max": [500,500,500],
        "apply_to_emitters": True
    }})
    print(f"  {sys}: {'OK' if ok(r) else gt(r)[:60]}")

# ====================================================
# Save all modified systems
# ====================================================
print("\n=== Save all ===")
all_systems = [
    "NS_SakuraPetals", "NS_SakuraPetals_v2", "NS_SakuraGroundPetals",
    "NS_SakuraPetalGust", "NS_SakuraDreamSparkle", "NS_SakuraLanternMotes",
    "NS_SakuraPondShimmer", "NS_SakuraWaterPetals", "NS_WindRibbonGust",
    "NS_ConstellationDraw",
]
for sys in all_systems:
    a = f"{SAKURA}/{sys}.{sys}"
    r = ct("niagara_query", {"action":"save_system","params":{"asset_path": a}})
    print(f"  {sys}: {'OK' if ok(r) else 'FAIL'}")
