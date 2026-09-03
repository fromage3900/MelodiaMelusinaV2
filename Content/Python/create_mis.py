"""Create material instances and assign to renderers"""
import json
import urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"
MATS = "/Game/EnvSandbox/VFX/Materials"

def call_tool(name, args, timeout=15):
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": name, "arguments": args}}
    req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())

def get_text(result):
    return result.get("result", {}).get("content", [{}])[0].get("text", "")

# First verify the parent materials exist
parents = ["M_SakuraPetal", "M_Niagara_SakuraSprite", "M_Niagara_Ripple"]
for p in parents:
    r = call_tool("material_query", {"action": "discover", "params": {}})
    # Just check via set_renderer_material on a known-good system
    r = call_tool("niagara_query", {"action": "set_renderer_material", "params": {
        "asset_path": "/Game/EnvSandbox/VFX/Systems/Sakura/NS_SakuraDreamSparkle",
        "emitter": "DreamMotes",
        "renderer_index": 0,
        "material": f"{MATS}/{p}.{p}",
    }})
    text = get_text(r)
    ok = "Failed to load" not in text
    print(f"  {p}: {'EXISTS' if ok else 'MISSING'}")

print()

# Create MI instances using create_material_instance
# Check the create_material_instance action params first
r = call_tool("material_query", {"action": "create_material_instance", "params": {
    "destination_path": f"{MATS}/MI_Niagara_Sparkle",
    "parent_material": f"{MATS}/M_Niagara_SakuraSprite",
}})
print(f"create MI_Niagara_Sparkle: {get_text(r)[:300]}")

r = call_tool("material_query", {"action": "create_material_instance", "params": {
    "destination_path": f"{MATS}/MI_Niagara_Petal",
    "parent_material": f"{MATS}/M_SakuraPetal",
}})
print(f"create MI_Niagara_Petal: {get_text(r)[:300]}")

r = call_tool("material_query", {"action": "create_material_instance", "params": {
    "destination_path": f"{MATS}/MI_Niagara_Mote",
    "parent_material": f"{MATS}/M_Niagara_SakuraSprite",
}})
print(f"create MI_Niagara_Mote: {get_text(r)[:300]}")

r = call_tool("material_query", {"action": "create_material_instance", "params": {
    "destination_path": f"{MATS}/MI_Niagara_Pond",
    "parent_material": f"{MATS}/M_Niagara_Ripple",
}})
print(f"create MI_Niagara_Pond: {get_text(r)[:300]}")

r = call_tool("material_query", {"action": "create_material_instance", "params": {
    "destination_path": f"{MATS}/MI_Niagara_Gust",
    "parent_material": f"{MATS}/M_Niagara_SakuraSprite",
}})
print(f"create MI_Niagara_Gust: {get_text(r)[:300]}")
