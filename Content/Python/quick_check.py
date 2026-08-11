"""Quick renderer property check"""
import json, urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"
SAKURA = "/Game/EnvSandbox/VFX/Systems/Sakura"

payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
           "params": {"name": "niagara_query", "arguments": {
               "action": "list_renderer_properties",
               "params": {
                   "asset_path": f"{SAKURA}/NS_SakuraDreamSparkle",
                   "emitter": "DreamMotes",
                   "renderer_index": 0,
               }
           }}}
req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=15) as resp:
    r = json.loads(resp.read().decode())
text = r.get("result", {}).get("content", [{}])[0].get("text", "")
print(text[:2000])
