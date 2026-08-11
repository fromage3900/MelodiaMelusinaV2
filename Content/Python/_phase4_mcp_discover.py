"""Discover MCP tools available for Phase 4 execution."""
import json, urllib.request

def mcp_call(method, params=None):
    req = urllib.request.Request(
        'http://127.0.0.1:9316/mcp',
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}).encode(),
        headers={"Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=15).read())

resp = mcp_call("tools/list")
tools = resp.get("result", {}).get("tools", [])
print(f"Found {len(tools)} tools:\n")
for t in tools:
    desc = (t.get("description") or "")[:150]
    print(f"  {t['name']}")
    print(f"    {desc}")
    inp = t.get("inputSchema", {}).get("properties", {})
    if inp:
        print(f"    params: {', '.join(inp.keys())}")
    print()
