"""Debug create_material_instance with various paths"""
import json
import urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"
MATS = "/Game/EnvSandbox/VFX/Materials"

def get_text(r):
    return r.get("result", {}).get("content", [{}])[0].get("text", "")

# Try many path formats
paths = [
    f"{MATS}/MI_Niagara_Sparkle",
    f"{MATS}/MI_Niagara_Sparkle.MI_Niagara_Sparkle",
    f"/Game/EnvSandbox/VFX/Materials/MI_Niagara_Sparkle",
    f"/Game/EnvSandbox/VFX/Materials/MI_Niagara_Sparkle.MI_Niagara_Sparkle",
    f"MI_Niagara_Sparkle",  # might be relative
]

for dest in paths:
    for parent in [
        f"{MATS}/M_Niagara_SakuraSprite.M_Niagara_SakuraSprite",
        f"{MATS}/M_Niagara_SakuraSprite",
    ]:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                   "params": {"name": "material_query", "arguments": {
                       "action": "create_material_instance",
                       "params": {"destination_path": dest, "parent_material": parent}
                   }}}
        req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = json.loads(resp.read().decode())
        text = get_text(raw)
        is_err = raw.get("result", {}).get("isError", False)
        if not is_err:
            print(f"SUCCESS: dest={dest}, parent={parent} -> {text[:200]}")
        else:
            err = text[:100] if text else "?"
            if "schema" not in err:  # skip schema errors we already know about
                print(f"FAIL: dest={dest}, parent={parent} -> {err}")
