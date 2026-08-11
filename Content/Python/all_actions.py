"""Get all niagara actions and test set_renderer_material more carefully"""
import json
import urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"

def call_tool(name, args, timeout=15):
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": name, "arguments": args}}
    req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())

def get_text(result):
    return result.get("result", {}).get("content", [{}])[0].get("text", "")

# Get all niagara actions
r = call_tool("monolith_discover", {"namespace": "niagara"})
text = get_text(r)
actions = json.loads(text)
print("All niagara actions:")
for a in actions.get("actions", []):
    print(f"  {a['action']}: {a['description'][:100]}")
