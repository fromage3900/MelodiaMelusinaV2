"""Test run_python via MCP, then check what source anims exist for retargeting."""
import json, urllib.request

def mcp_tool(name, args):
    req = urllib.request.Request(
        'http://127.0.0.1:9316/mcp',
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                         "params": {"name": name, "arguments": args}}).encode(),
        headers={"Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

# Discover available editor actions
print("=== editor_query(discover) ===")
r = mcp_tool("editor_query", {"action": "discover"})
print(json.dumps(r, indent=2)[:1000])

# Try run_python
print("\n=== editor_query(run_python) checking python exec ===")
r = mcp_tool("editor_query", {"action": "run_python", "params": {"command": "import unreal; print('MCP Python OK: v' + unreal.get_version())", "mode": "execute_statement"}})
print(json.dumps(r, indent=2)[:1000])

# Check what source animations exist
print("\n=== check source anims ===")
r = mcp_tool("editor_query", {"action": "run_python", "params": {"command": "import unreal; assets = unreal.EditorAssetLibrary.list_assets('/Game/Melodia/Mocap/Source/Anims', False, False); print('Source anims:', len(assets)); [print(a) for a in assets]", "mode": "execute_statement"}})
print(json.dumps(r, indent=2)[:2000])
