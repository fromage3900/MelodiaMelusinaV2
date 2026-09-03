"""Phase 0.7b: Set FixedBounds with correct params"""
import json, urllib.request

MCP = "http://127.0.0.1:9316/mcp"
SAKURA = "/Game/EnvSandbox/VFX/Systems/Sakura"

def ct(n,a):
    p={"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":n,"arguments":a}}
    r=urllib.request.Request(MCP,data=json.dumps(p).encode(),headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(r,timeout=15).read().decode())
def gt(r):
    return r.get("result",{}).get("content",[{}])[0].get("text","")
def ok(r):
    return not r.get("result",{}).get("isError",False)

unbounded = [
    "NS_SakuraDreamSparkle", "NS_SakuraLanternMotes",
    "NS_SakuraPondShimmer", "NS_SakuraWaterPetals",
    "NS_WindRibbonGust", "NS_ConstellationDraw",
]
for sys in unbounded:
    a = f"{SAKURA}/{sys}.{sys}"
    r = ct("niagara_query", {"action":"set_fixed_bounds","params":{
        "asset_path": a, "min": [-500,-500,-500], "max": [500,500,500]
    }})
    print(f"  {sys}: {'OK' if ok(r) else gt(r)[:80]}")
    # Save
    ct("niagara_query", {"action":"save_system","params":{"asset_path": a}})
