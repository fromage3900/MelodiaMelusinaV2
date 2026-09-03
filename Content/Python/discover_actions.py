"""List MCP tools - find monolith tools"""
import json
import urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"

def call_tool(name, args, timeout=15):
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": name, "arguments": args}}
    req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())

def get_text(result):
    return result.get("result", {}).get("content", [{}])[0].get("text", "")

# Try monolith discover for niagara
print("=== monolith_discover('niagara') ===")
r = call_tool("monolith_discover", {"namespace": "niagara"})
print(get_text(r)[:3000])

print()
print("=== monolith_discover('material') ===")
r = call_tool("monolith_discover", {"namespace": "material"})
print(get_text(r)[:2000])

# Check if there's a monolith_python tool
print()
print("=== tools/list filtered ===")
payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=15) as resp:
    r = json.loads(resp.read().decode())
    for t in r.get("result", {}).get("tools", []):
        name = t.get("name", "")
        if "python" in name.lower() or "script" in name.lower() or "monolith" in name.lower():
            print(f"  {name}: {t.get('description', '')[:100]}")
