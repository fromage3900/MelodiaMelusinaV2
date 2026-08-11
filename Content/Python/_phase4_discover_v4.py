"""Try different MCP method name patterns."""
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

# Try monolith_discover as method name
print("=== monolith_discover tool ===")
r = mcp_rpc("monolith_discover", {"namespace": "animation"})
print(r.get("result", {}).get("content", [{}])[0].get("text", json.dumps(r)[:500]))

# Also try describe list_targets properly
print("\n=== describe list_targets ===")
r2 = mcp_rpc("describe_query", {"action": "list_targets", "params": {"target_namespace": "animation"}})
text = r2.get("result", {}).get("content", [{}])[0].get("text", "")
print(text[:3000])

# Try describe action_schema with target
print("\n=== describe action_schema ===")
r3 = mcp_rpc("describe_query", {"action": "action_schema", "params": {"target": "animation"}})
text = r3.get("result", {}).get("content", [{}])[0].get("text", "")
print(text[:3000])
