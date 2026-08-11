"""Try AutomatedAssetImportData approach."""
import json, urllib.request

script = r"""import unreal

result = {"ok": False}

# Check AutomatedAssetImportData
try:
    data = unreal.AutomatedAssetImportData()
    # Check settable properties
    for prop in ["group", "filenames", "destination_path", "destination_name", 
                 "replace_existing", "skip_read_only", "factory", "level_to_load"]:
        try:
            data.set_editor_property(prop, None if prop == "factory" else [] if prop in ["filenames"] else 
                                     "/Game/Temp" if prop == "destination_path" else "Test" if prop == "destination_name" else True)
            result[prop] = "settable"
        except Exception as e:
            result[prop] = str(e)[:60]
except Exception as e:
    result["error"] = str(e)[:200]

print(json.dumps(result))
"""

with open(r'G:\EnvironmentPortfolio\BS_GodFile\Content\Python\_phase4_check_autoimport.py', 'w') as f:
    f.write(script)

req = urllib.request.Request(
    'http://127.0.0.1:9316/mcp',
    data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": "editor_query",
                                "arguments": {"action": "run_python",
                                              "params": {"command": "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/_phase4_check_autoimport.py",
                                                         "mode": "execute_file"}}}}).encode(),
    headers={"Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
print(text[:2000])
