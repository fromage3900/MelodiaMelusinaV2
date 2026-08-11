"""Discover all animation actions available via MCP."""
import json, urllib.request

def mcp_call(action, params):
    body = {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "animation_query", "arguments": {"action": action, "params": params}}
    }
    req = urllib.request.Request(
        'http://127.0.0.1:9316/mcp',
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

# Get all animation actions via monolith_discover
body = {
    "jsonrpc": "2.0", "id": 1, "method": "tools/call",
    "params": {"name": "monolith_discover", "arguments": {"namespace": "animation", "detail": True}}
}
req = urllib.request.Request(
    'http://127.0.0.1:9316/mcp',
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
print(json.dumps(resp, indent=2)[:4000])
