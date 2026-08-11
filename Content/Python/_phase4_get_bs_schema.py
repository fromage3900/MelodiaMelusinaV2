"""Get action schema for create_blend_space_1d."""
import json, urllib.request

# Try describe_query to get the schema
body = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "describe_query",
        "arguments": {
            "action": "action_schema",
            "params": {
                "target_namespace": "animation",
                "target_action": "create_blend_space_1d"
            }
        }
    }
}

req = urllib.request.Request(
    'http://127.0.0.1:9316/mcp',
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json"},
)
try:
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    print(json.dumps(resp, indent=2)[:3000])
except Exception as e:
    print(f"Error: {e}")
