"""Assign MI_Niagara_Gust to NS_SakuraPetalGust/OmnidirectionalBurst and do final save"""
import json
import urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"
MATS = "/Game/EnvSandbox/VFX/Materials"
SAKURA = "/Game/EnvSandbox/VFX/Systems/Sakura"

def call_tool(name, args, timeout=15):
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": name, "arguments": args}}
    req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())

def get_text(result):
    return result.get("result", {}).get("content", [{}])[0].get("text", "")

# Assign MI_Niagara_Gust
sys_name = "NS_SakuraPetalGust"
asset = f"{SAKURA}/{sys_name}"
mat_path = f"{MATS}/MI_Niagara_Gust.MI_Niagara_Gust"

print("=== Assign MI_Niagara_Gust ===")
r = call_tool("niagara_query", {"action": "set_renderer_material", "params": {
    "asset_path": asset,
    "emitter": "OmnidirectionalBurst",
    "renderer_index": 0,
    "material": mat_path,
}})
is_err = r.get("result", {}).get("isError", False)
print(f"  Set: {'OK' if not is_err else 'FAIL: ' + get_text(r)[:80]}")

# Save
r = call_tool("niagara_query", {"action": "save_system", "params": {"asset_path": asset}})
print(f"  Save: {get_text(r)[:80]}")

# Verify
r = call_tool("niagara_query", {"action": "list_renderers", "params": {"asset_path": asset, "emitter": "OmnidirectionalBurst"}})
data = json.loads(get_text(r))
for rend in data.get("renderers", []):
    rm = rend.get("material", "?")
    ok = "MI_Niagara_Gust" in rm
    print(f"  Verify: {'OK' if ok else 'MISMATCH'} -> {rm.split('/')[-1]}")

print()
print("=== Full final summary ===")
systems = [
    "NS_SakuraPetals", "NS_SakuraPetals_v2", "NS_SakuraGroundPetals",
    "NS_SakuraDreamSparkle", "NS_SakuraLanternMotes",
    "NS_SakuraPondShimmer", "NS_SakuraWaterPetals", "NS_SakuraPetalGust",
]
for s in systems:
    asset = f"{SAKURA}/{s}"
    r = call_tool("niagara_query", {"action": "list_emitters", "params": {"asset_path": asset}})
    emitters = json.loads(get_text(r))
    em_names = [e.get("name", "?") for e in emitters.get("emitters", [])]
    renderers_info = []
    for ename in em_names:
        r2 = call_tool("niagara_query", {"action": "list_renderers", "params": {"asset_path": asset, "emitter": ename}})
        rends = json.loads(get_text(r2))
        for rd in rends.get("renderers", []):
            rm = rd.get("material", "NONE").split("/")[-1]
            renderers_info.append(f"{ename}[{rd['index']}]={rm}")
    print(f"  {s}: {', '.join(renderers_info)}")
