"""Discover animation + editor + blueprint actions available."""
import json, urllib.request

def mcp_call(method, params=None):
    req = urllib.request.Request(
        'http://127.0.0.1:9316/mcp',
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}).encode(),
        headers={"Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=15).read())

for ns in ["animation", "editor", "blueprint", "mesh"]:
    resp = mcp_call("monolith_discover", {"namespace": ns, "detail": True})
    actions = resp.get("result", {}).get("actions", resp.get("result", {}))
    if isinstance(actions, list):
        print(f"\n=== {ns} ({len(actions)} actions) ===")
        for a in actions:
            name = a.get("name", a.get("action", "?"))
            desc = (a.get("description") or "")[:100]
            print(f"  {name}: {desc}")
    else:
        print(f"\n=== {ns} ===\n{json.dumps(actions, indent=2)[:1000]}")
