"""Execute Phase 4.0 import+retarget via MCP run_python."""
import json, urllib.request

def mcp_tool(name, args):
    req = urllib.request.Request(
        'http://127.0.0.1:9316/mcp',
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                         "params": {"name": name, "arguments": args}}).encode(),
        headers={"Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=300).read())

script_path = "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/_phase4_import_missing_mocap.py"

r = mcp_tool("editor_query", {
    "action": "run_python",
    "params": {
        "command": script_path,
        "mode": "execute_file"
    }
})

text = r.get("result", {}).get("content", [{}])[0].get("text", "{}")
print(text[:3000])
