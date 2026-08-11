"""Query FbxImportUI and FbxAnimSequenceImportData properties via MCP."""
import json, urllib.request

def mcp_run(cmd):
    req = urllib.request.Request(
        'http://127.0.0.1:9316/mcp',
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                         "params": {"name": "editor_query",
                                    "arguments": {"action": "run_python",
                                                  "params": {"command": cmd, "mode": "execute_statement"}}}}).encode(),
        headers={"Content-Type": "application/json"},
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
    return json.loads(text)

# Query available props
cmd = """
import unreal
# Check FbxImportUI props
ui = unreal.FbxImportUI()
ui_props = [p for p in dir(ui) if not p.startswith('_')]
print("FbxImportUI:", ui_props)

# Check FbxAnimSequenceImportData props
anim = unreal.FbxAnimSequenceImportData()
anim_props = [p for p in dir(anim) if not p.startswith('_')]
print("FbxAnimSeq:", anim_props)

# Check how to import anim onto an existing skeleton
print("AssetTools methods:", [m for m in dir(unreal.AssetToolsHelpers.get_asset_tools()) if 'import' in m.lower()])
"""
r = mcp_run(cmd)
for o in r.get("output", []):
    print(o.get("output",""))
