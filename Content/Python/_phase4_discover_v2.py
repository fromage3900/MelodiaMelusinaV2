"""Discover animation namespace using correct MCP API path."""
import json, urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"

def mcp_call(namespace, action, params=None):
    body = {"namespace": namespace, "action": action}
    if params:
        body["params"] = params
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(MCP_URL, data=data,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)

# 1. Discover animation namespace
print("=== Discover animation namespace ===")
r = mcp_call("monolith", "discover", {"namespace": "animation"})
# Print all action names
actions = r.get("result", {}).get("content", [{}])[0].get("text", "")
if isinstance(actions, str):
    print(actions[:5000])
else:
    print(json.dumps(actions, indent=2)[:5000])

# 2. Also discover editor namespace to find ABP skeleton actions
print("\n=== Discover editor namespace (filtered) ===")
r2 = mcp_call("monolith", "discover", {"namespace": "editor"})
text = r2.get("result", {}).get("content", [{}])[0].get("text", "")
if isinstance(text, str):
    for line in text.split("\n"):
        if any(kw in line.lower() for kw in ["skeleton", "abp", "skel", "blueprint", "anim"]):
            print(line[:200])
else:
    print(json.dumps(text, indent=2)[:2000])
