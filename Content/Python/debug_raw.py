"""Debug: check raw return from set_renderer_material with renderer_index"""
import json
import urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"
SAKURA = "/Game/EnvSandbox/VFX/Systems/Sakura"
MATS = "/Game/EnvSandbox/VFX/Materials"

path = f"{SAKURA}/NS_SakuraDreamSparkle"
emitter = "DreamMotes"

# Use direct MCP call to see raw response
payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
           "params": {"name": "niagara_query", "arguments": {
               "action": "set_renderer_material",
               "params": {
                   "asset_path": path,
                   "emitter": emitter,
                   "renderer_index": 0,
                   "material": f"{MATS}/MI_Niagara_Sparkle.MI_Niagara_Sparkle",
               }}}}
req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=15) as resp:
    raw = json.loads(resp.read().decode())

print("Raw set_renderer_material response:")
print(json.dumps(raw, indent=2)[:2000])

print()

# Check - did the material change?
payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
           "params": {"name": "niagara_query", "arguments": {
               "action": "list_renderers",
               "params": {"asset_path": path, "emitter": emitter}
           }}}
req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=15) as resp:
    raw2 = json.loads(resp.read().decode())

text2 = raw2.get("result", {}).get("content", [{}])[0].get("text", "{}")
print("Verify after set:")
print(text2[:500])
