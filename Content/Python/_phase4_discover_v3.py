"""Discover actions using proper JSON-RPC format."""
import json, urllib.request

def mcp_rpc(method, arguments):
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": method, "arguments": arguments}}
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request("http://127.0.0.1:9316/mcp", data=data,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))

# Try discover via monolith namespace
print("=== monolith discover ===")
r = mcp_rpc("monolith_query", {"action": "discover", "params": {"namespace": "animation"}})
print(r.get("result", {}).get("content", [{}])[0].get("text", "no text")[:5000])

print("\n=== describe list_targets ===")
r2 = mcp_rpc("describe_query", {"action": "list_targets", "params": {}})
print(json.dumps(r2, indent=2)[:2000])

print("\n=== describe schema (list describe actions) ===")
r3 = mcp_rpc("describe_query", {"action": "schema", "params": {"target_namespace": "describe"}})
text = r3.get("result", {}).get("content", [{}])[0].get("text", "")
print(text[:3000])
