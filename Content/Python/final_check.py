"""Final: handle NS_SakuraPetalGust and verify everything"""
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

# Check NS_SakuraPetalGust
print("=== NS_SakuraPetalGust ===")
r = call_tool("niagara_query", {"action": "get_system_summary", "params": {
    "asset_path": f"{SAKURA}/NS_SakuraPetalGust",
}})
summary = json.loads(get_text(r))
for e in summary.get("emitters", []):
    print(f"  Emitter: {e['name']} (has_sprite={e.get('has_sprite_renderer')}, has_ribbon={e.get('has_ribbon_renderer')}, has_mesh={e.get('has_mesh_renderer')})")

# List renderers for each emitter
r = call_tool("niagara_query", {"action": "list_emitters", "params": {
    "asset_path": f"{SAKURA}/NS_SakuraPetalGust",
}})
emitters = json.loads(get_text(r))
for e in emitters.get("emitters", []):
    ename = e.get("name", "?")
    r2 = call_tool("niagara_query", {"action": "list_renderers", "params": {
        "asset_path": f"{SAKURA}/NS_SakuraPetalGust",
        "emitter": ename,
    }})
    renderers = json.loads(get_text(r2))
    for rend in renderers.get("renderers", []):
        print(f"  {ename}[{rend['index']}]({rend['type']}): {rend.get('material', 'NONE')}")

print()
print("=== Full verification of all 8 assigned systems ===")
checks = [
    ("NS_SakuraPetals", "CanopyDrift", 0, "MI_Niagara_Petal"),
    ("NS_SakuraPetals_v2", "Petals", 0, "MI_Niagara_Petal"),
    ("NS_SakuraPetals_v2", "Petals", 1, "MI_Niagara_Petal"),
    ("NS_SakuraGroundPetals", "GroundPetals", 0, "MI_Niagara_Petal"),
    ("NS_SakuraDreamSparkle", "DreamMotes", 0, "MI_Niagara_Sparkle"),
    ("NS_SakuraLanternMotes", "LanternMotes", 0, "MI_Niagara_Mote"),
    ("NS_SakuraPondShimmer", "Ripples", 0, "MI_Niagara_Pond"),
    ("NS_SakuraWaterPetals", "GroundPetals", 0, "MI_Niagara_Petal"),
]
all_ok = True
for sys_name, emitter, ri, expected in checks:
    asset = f"{SAKURA}/{sys_name}"
    r = call_tool("niagara_query", {"action": "list_renderers", "params": {"asset_path": asset, "emitter": emitter}})
    try:
        data = json.loads(get_text(r))
        for rend in data.get("renderers", []):
            if rend.get("index") == ri:
                rm = rend.get("material", "?")
                ok = expected in rm
                print(f"  {'OK' if ok else 'MISMATCH'}: {sys_name}/{emitter}[{ri}] -> {rm.split('/')[-1]}")
                if not ok:
                    all_ok = False
    except:
        print(f"  FAIL parse: {sys_name}")

print()
if all_ok:
    print("All 8 renderers verified OK")
else:
    print("Some mismatches found!")
