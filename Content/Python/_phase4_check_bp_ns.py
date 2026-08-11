"""Check blueprint namespace for variable-related actions."""
import json, urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"

body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "monolith_discover", "arguments": {"namespace": "blueprint"}}}
data = json.dumps(body).encode("utf-8")
req = urllib.request.Request(MCP_URL, data=data, headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=60) as resp:
    r = json.loads(resp.read().decode("utf-8"))

text = r.get("result", {}).get("content", [{}])[0].get("text", "")
try:
    actions = json.loads(text) if text.startswith("{") else text
except:
    actions = text

if isinstance(actions, dict):
    for a in actions.get("actions", []):
        if any(kw in a.get("action","").lower() for kw in ["variable", "float", "speed", "member", "property"]):
            print(f"{a['action']}: {a.get('description','')[:120]}")
    print(f"\nTotal: {actions.get('total', 0)} actions")
else:
    print(str(actions)[:3000])
