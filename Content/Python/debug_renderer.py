"""Test set_renderer_material with various approaches"""
import json
import urllib.request
import time

MCP_URL = "http://127.0.0.1:9316/mcp"
SAKURA = "/Game/EnvSandbox/VFX/Systems/Sakura"
MATS = "/Game/EnvSandbox/VFX/Materials"


def call_tool(name, args, timeout=15):
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": name, "arguments": args}}
    req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def get_text(result):
    return result.get("result", {}).get("content", [{}])[0].get("text", "")


def niagara(action, params, timeout=15):
    r = call_tool("niagara_query", {"action": action, "params": params}, timeout=timeout)
    text = get_text(r)
    try:
        return json.loads(text)
    except:
        return {"error": text}


# 1. Check renderer properties
sys_ns = "NS_SakuraDreamSparkle"
emitter = "DreamMotes"
path = f"{SAKURA}/{sys_ns}"

print("=== list_renderer_properties ===")
r = niagara("list_renderer_properties", {"asset_path": path, "emitter": emitter})
for p in r.get("properties", []):
    print(f"  {p.get('name')}: {p.get('value')} (type={p.get('type')})")

print()
print("=== list_renderers (detailed) ===")
r = niagara("list_renderers", {"asset_path": path, "emitter": emitter})
print(json.dumps(r, indent=2)[:500])

print()
# 2. Try set_renderer_material with class name instead of index
print("=== Try set_renderer_material with class name ===")
r = niagara("set_renderer_material", {
    "asset_path": path,
    "emitter": emitter,
    "renderer": "NiagaraSpriteRendererProperties",
    "material": f"{MATS}/MI_Niagara_Sparkle.MI_Niagara_Sparkle",
})
print(f"Result: {json.dumps(r)[:300]}")

print()
# 3. Verify
r = niagara("list_renderers", {"asset_path": path, "emitter": emitter})
for rend in r.get("renderers", []):
    print(f"  Renderer[{rend['index']}]: {rend['type']} -> {rend.get('material', 'NONE')}")
