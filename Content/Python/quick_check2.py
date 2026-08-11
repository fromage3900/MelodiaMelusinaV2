"""Quick renderer check for mesh and ribbon renderers"""
import json, urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"
SAKURA = "/Game/EnvSandbox/VFX/Systems/Sakura"

def niagara(action, params):
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": "niagara_query", "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        r = json.loads(resp.read().decode())
        return r.get("result", {}).get("content", [{}])[0].get("text", "")

# Check key properties for each renderer type
checks = [
    ("NS_SakuraPetals", "CanopyDrift", 0, "mesh"),
    ("NS_SakuraDreamSparkle", "DreamMotes", 0, "sprite"),
    ("NS_SakuraPetalGust", "RibbonTrailFollower", 0, "ribbon"),
    ("NS_SakuraPetals_v2", "EM_PondRipple", 0, "mesh"),
    ("NS_SakuraPetals_v2", "EM_PetalPile", 0, "mesh"),
    ("NS_WindRibbonGust", "E_OmnidirectionalPetalBurst", 0, "sprite"),
]

for sys_name, emitter, ri, rtype in checks:
    text = niagara("list_renderer_properties", {"asset_path": f"{SAKURA}/{sys_name}", "emitter": emitter, "renderer_index": ri})
    try:
        data = json.loads(text)
        print(f"\n{sys_name}/{emitter}[{ri}]({rtype}):")
        for p in data.get("properties", []):
            name = p.get("name", "")
            if name in ("Material", "Alignment", "FacingMode", "SortMode", "bCastShadows", "SourceMode", "SubImageSize"):
                print(f"  {name}: {p.get('value', '?')}")
    except json.JSONDecodeError:
        print(f"\n{sys_name}/{emitter}[{ri}]({rtype}): {text[:100]}")

# Also check modules for EM_PondRipple and EM_PetalPile to understand their event-driven setup
for emitter in ["EM_PondRipple", "EM_PetalPile"]:
    text = niagara("get_emitter_summary", {"asset_path": f"{SAKURA}/NS_SakuraPetals_v2", "emitter": emitter})
    try:
        data = json.loads(text)
        print(f"\n\nNS_SakuraPetals_v2/{emitter} summary:")
        print(json.dumps(data, indent=2)[:2000])
    except:
        print(f"\n\nNS_SakuraPetals_v2/{emitter}: {text[:200]}")
