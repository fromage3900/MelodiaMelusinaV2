"""Check monolith_discover for editor/animation actions."""
import json, urllib.request

def mcp_call(method, params=None):
    req = urllib.request.Request(
        'http://127.0.0.1:9316/mcp',
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}).encode(),
        headers={"Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=15).read())

# Try discover with various approaches
for ns in ["editor", "animation", "blueprint"]:
    for verbose in [False, True]:
        try:
            resp = mcp_call("monolith_discover", {"namespace": ns, "verbose": verbose})
            content = resp.get("result", {})
            if isinstance(content, list):
                print(f"\n=== {ns} (verbose={verbose}) [{len(content)} actions] ===")
                for a in content[:10]:
                    print(f"  {a.get('name', a.get('action', '?'))}: {str(a.get('description',''))[:80]}"  )
            elif isinstance(content, dict) and content.get("actions"):
                acts = content["actions"]
                print(f"\n=== {ns} (verbose={verbose}) [{len(acts)} actions] ===")
                for a in acts[:10]:
                    print(f"  {a.get('name', a.get('action', '?'))}: {str(a.get('description',''))[:80]}")
            elif content:
                print(f"\n=== {ns} (verbose={verbose}) ===\n{json.dumps(content, indent=2)[:500]}")
        except Exception as e:
            print(f"\n=== {ns} (verbose={verbose}) ERROR: {e}")
