"""Debug MCP discover response."""
import json, urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"

def mcp_raw(namespace, action, params=None):
    body = {"namespace": namespace, "action": action}
    if params:
        body["params"] = params
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(MCP_URL, data=data,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
    return raw

# Full raw response
raw = mcp_raw("monolith", "discover", {"namespace": "animation"})
print("=== Raw discover response ===")
print(raw[:5000])

print("\n\n=== Trying discover with no namespace ===")
raw2 = mcp_raw("monolith", "discover")
print(raw2[:5000])

print("\n\n=== Trying monolith status ===")
raw3 = mcp_raw("monolith", "status")
print(raw3[:2000])
