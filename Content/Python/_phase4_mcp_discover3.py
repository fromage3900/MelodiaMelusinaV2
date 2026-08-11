"""Discover all available MCP actions - iterate through approaches."""
import json, urllib.request

def mcp_call(method, params=None):
    req = urllib.request.Request(
        'http://127.0.0.1:9316/mcp',
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}).encode(),
        headers={"Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=15).read())

# Try monolith_discover with various namespaces
for ns in ["animation", "editor", "blueprint", "mesh", ""]:
    try:
        resp = mcp_call("monolith_discover", {"namespace": ns} if ns else {})
        r = resp.get("result", {})
        print(f"\n=== monolith_discover({ns!r}) ===")
        print(json.dumps(r, indent=2)[:2000])
    except Exception as e:
        print(f"\n=== monolith_discover({ns!r}) ERROR: {e}")

# Also try tools/call for describe_query
print("\n=== describe_query(all) ===")
try:
    resp = mcp_call("tools/call", {"name": "describe_query", "arguments": {"action": "list_all"}})
    print(json.dumps(resp, indent=2)[:2000])
except Exception as e:
    print(f"ERROR: {e}")
