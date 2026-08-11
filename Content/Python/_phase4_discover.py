"""Discover animation actions and check editor actions for ABP skeleton setup."""
import json, urllib.request

def raw_rpc(method, params):
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": method, "arguments": params}}
    req = urllib.request.Request("http://127.0.0.1:9316/mcp", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    return resp

# Discover animation namespace actions
r = raw_rpc("discover_query", {"action": "discover", "params": {"namespace": "animation"}})
print("=== Animation actions ===")
print(json.dumps(r, indent=2)[:5000])

# Also check editor namespace for skeleton-related actions
r2 = raw_rpc("discover_query", {"action": "discover", "params": {"namespace": "editor"}})
print("\n=== Editor actions (filtered skeleton/abp) ===")
text = r2.get("result", {}).get("content", [{}])[0].get("text", "")
# Look for skeleton/ABP related actions
for line in text.split("\n"):
    if any(kw in line.lower() for kw in ["skeleton", "abp", "skel", "anim_blueprint", "animinstance"]):
        print(line[:200])
