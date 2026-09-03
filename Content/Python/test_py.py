"""Test Python API output"""
import json
import urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"

payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
           "params": {"name": "python", "arguments": {"script": [
               "import unreal",
               "print('hello from UE Python')",
               "print('type:', type(unreal))",
           ]}}}
req = urllib.request.Request(
    MCP_URL, data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req, timeout=15) as resp:
    r = json.loads(resp.read().decode())

print("Full response:")
print(json.dumps(r, indent=2)[:2000])
