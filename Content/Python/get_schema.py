"""Get action schema for set_renderer_material"""
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

# Try describe_query action_schema
print("=== describe_query('action_schema') for set_renderer_material ===")
r = call_tool("niagara_query", {"action": "describe_query", "params": {"action": "action_schema", "schema_action": "set_renderer_material"}})
print(get_text(r)[:2000])

print()
print("=== describe_query('action_schema') raw ===")
print(json.dumps(r, indent=2)[:3000])
