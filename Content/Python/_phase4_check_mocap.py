"""Check Mocap source dir and import pipeline."""
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

# Check Mocap source directory structure
cmds = [
    "import unreal; asst = unreal.EditorAssetLibrary; print('Mocap source dir:', asst.does_directory_exist('/Game/Melodia/Mocap/Source'))",
    "import unreal; assets = unreal.EditorAssetLibrary.list_assets('/Game/Melodia/Mocap/Source', True, False); print('Source assets:', len(assets)); [print(f'  {a}') for a in assets]",
    "import unreal; asst = unreal.EditorAssetLibrary; print('Mocap dir:', asst.does_directory_exist('/Game/Melodia/Mocap'))",
    "import unreal; assets = unreal.EditorAssetLibrary.list_assets('/Game/Melodia/Mocap', True, False); print('Mocap assets:', len(assets)); [print(f'  {a}') for a in assets]",
]
for c in cmds:
    r = mcp_run(c)
    ok = r.get("ok")
    out = "\n".join(o.get("output","") for o in r.get("output",[]))
    print(out)
    print("---")
