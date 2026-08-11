"""Check AssetTools import methods."""
script = """import unreal, json
tools = unreal.AssetToolsHelpers.get_asset_tools()
methods = [m for m in dir(tools) if 'import' in m.lower() or 'asset' in m.lower()]
print(json.dumps({"import_methods": methods}))
"""

with open(r'G:\EnvironmentPortfolio\BS_GodFile\Content\Python\_phase4_check_import_methods.py', 'w') as f:
    f.write(script)

import json, urllib.request

req = urllib.request.Request(
    'http://127.0.0.1:9316/mcp',
    data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": "editor_query",
                                "arguments": {"action": "run_python",
                                              "params": {"command": "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/_phase4_check_import_methods.py",
                                                         "mode": "execute_file"}}}}).encode(),
    headers={"Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
print(text[:2000])
