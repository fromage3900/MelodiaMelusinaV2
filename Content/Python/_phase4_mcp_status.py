"""Check MCP server status and try various query methods."""
import json, urllib.request, sys

def mcp_call(method, params=None):
    req = urllib.request.Request(
        'http://127.0.0.1:9316/mcp',
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
        return resp
    except Exception as e:
        return {"error": str(e)}

# 1. Check status
print("=== monolith_status ===")
r = mcp_call("monolith_status")
print(json.dumps(r, indent=2)[:500])

# 2. Try to get the tools/call format working
print("\n=== tools/call describe_query ===")
r = mcp_call("tools/call", {"name": "describe_query", "arguments": {"action": "list_targets"}})
print(json.dumps(r, indent=2)[:500])

# 3. Try animation_query directly
print("\n=== animation_query(list_actions) ===")
r = mcp_call("tools/call", {"name": "animation_query", "arguments": {"action": "list_actions"}})
print(json.dumps(r, indent=2)[:1000])

# 4. Try editor_query list_actions
print("\n=== editor_query(list_actions) ===")
r = mcp_call("tools/call", {"name": "editor_query", "arguments": {"action": "list_actions"}})
print(json.dumps(r, indent=2)[:1000])

# 5. Try blueprint_query list_actions
print("\n=== blueprint_query(list_actions) ===")
r = mcp_call("tools/call", {"name": "blueprint_query", "arguments": {"action": "list_actions"}})
print(json.dumps(r, indent=2)[:1000])
