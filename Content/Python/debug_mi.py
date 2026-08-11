"""Debug create_material_instance parameters"""
import json
import urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"
MATS = "/Game/EnvSandbox/VFX/Materials"

def get_text(r):
    return r.get("result", {}).get("content", [{}])[0].get("text", "")

# Try different parameter formats
for params in [
    {"destination_path": f"{MATS}/MI_Niagara_Sparkle.MI_Niagara_Sparkle", "parent_material": f"{MATS}/M_Niagara_SakuraSprite.M_Niagara_SakuraSprite"},
    {"destination_path": f"{MATS}/MI_Niagara_Sparkle.MI_Niagara_Sparkle", "parent": f"{MATS}/M_Niagara_SakuraSprite"},
    {"path": f"{MATS}/MI_Niagara_Sparkle", "parent": f"{MATS}/M_Niagara_SakuraSprite"},
]:
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": "material_query", "arguments": {
                   "action": "create_material_instance",
                   "params": params
               }}}
    req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = json.loads(resp.read().decode())
    text = get_text(raw)
    print(f"Params {params}: {text[:300]}")
    print()

# Also check the set_instance_parameter action
payload = {"jsonrpc": "2.0", "id": 10, "method": "tools/call",
           "params": {"name": "material_query", "arguments": {
               "action": "set_instance_parameter",
               "params": {
                   "material_path": f"{MATS}/M_Niagara_SakuraSprite.M_Niagara_SakuraSprite",
                   "parameter_name": "TestParam",
                   "value": 0.5,
               }
           }}}
req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=15) as resp:
    raw = json.loads(resp.read().decode())
print(f"set_instance_parameter: {get_text(raw)[:300]}")
