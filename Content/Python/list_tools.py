"""List MCP tools"""
import json
import urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"

# Direct tools/list
payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        r = json.loads(resp.read().decode())
        print("Direct tools/list:")
        print(json.dumps(r, indent=2)[:3000])
except Exception as e:
    print(f"Error: {e}")

print()

# Also discover niagara actions
payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
           "params": {"name": "niagara_query", "arguments": {"action": "discover", "params": {}}}}
req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        r = json.loads(resp.read().decode())
        print("niagara_query discover:")
        text = r.get("result", {}).get("content", [{}])[0].get("text", "")
        print(text[:3000])
except Exception as e:
    print(f"Error: {e}")
