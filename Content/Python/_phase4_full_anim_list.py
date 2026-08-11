"""Get full animation action list + check for montage/ABP actions."""
import json, urllib.request

def mcp_call(method, params):
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": method, "arguments": params}}
    req = urllib.request.Request(
        'http://127.0.0.1:9316/mcp',
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
    return json.loads(text)

# Get ALL animation action names
r = mcp_call("monolith_discover", {"namespace": "animation", "detail": False})
actions = r.get("actions", [])
print("=== All animation actions ===")
for a in actions:
    print(f"  {a.get('action', '?')}: {a.get('description', '')[:80]}")

# Check for montage create
r2 = mcp_call("describe_query", {"action": "action_schema", "params": {"target_namespace": "animation", "target_action": "add_anim_graph_node"}})
if r2.get("isError"):
    print("\nNo 'add_anim_graph_node' action found")
else:
    print("\nadd_anim_graph_node:", json.dumps(r2)[:500])

# Check what editor actions we have
r3 = mcp_call("monolith_discover", {"namespace": "editor", "detail": False})
editor_actions = r3.get("actions", [])
print("\n=== Editor actions ===")
for a in editor_actions:
    print(f"  {a.get('action', '?')}: {a.get('description', '')[:80]}")
