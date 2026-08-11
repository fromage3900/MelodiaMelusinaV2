"""Check FBX import properties that are setable."""
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

cmd = """
import unreal

# Check if skeleton is a property on FbxImportUI
ui = unreal.FbxImportUI()
print("skeleton on UI:", hasattr(ui, 'set_skeleton') or hasattr(ui, 'skeleton'))

# Check anim import data
anim = unreal.FbxAnimSequenceImportData()
print("Has remove_redundant_keys:", hasattr(anim, 'set_editor_property'))
try:
    anim.set_editor_property('remove_redundant_keys', True)
    print("Set remove_redundant_keys: OK")
except:
    print("Set remove_redundant_keys: FAILED")

# Check how to set skeleton on import
# Try setting on skeletal_mesh instead
print("Has skeletal_mesh on UI:", 'skeletal_mesh' in str([x for x in dir(ui) if 'skel' in x.lower()]))

# Use simpler import approach - just use import_asset_tasks with a basic setup
print("\\nTrying simpler approach...")
task = unreal.AssetImportTask()
task.set_editor_property('filename', r'G:\\EnvironmentPortfolio\\BS_GodFile\\Imports\\Mocap\\RunCycle.fbx')
task.set_editor_property('destination_path', '/Game/Melodia/Mocap/Source/Anims')
task.set_editor_property('destination_name', 'A_Src_RunCycle_TEST')
task.set_editor_property('replace_existing', True)
task.set_editor_property('save', True)
task.set_editor_property('automated', True)

# Minimal options
opts = unreal.FbxImportUI()
opts.set_editor_property('import_mesh', False)
opts.set_editor_property('import_animations', True)
skel = unreal.load_asset('/Game/Melodia/Mocap/Source/SK_MocapSource_Skeleton.SK_MocapSource_Skeleton')
print(f"Loaded skeleton: {skel}")

# Set skeleton on the UI directly
try:
    opts.set_editor_property('skeleton', skel)
    print("Set skeleton on UI: OK")
except Exception as e:
    print(f"Set skeleton on UI failed: {e}")

# Try on import data
anim_data = opts.get_editor_property('anim_sequence_import_data')
print(f"Got anim_sequence_import_data: {anim_data}")
if anim_data:
    try:
        anim_data.set_editor_property('skeleton', skel)
        print("Set skeleton on anim_data: OK")
    except Exception as e:
        print(f"Set skeleton on anim_data failed: {e}")

task.set_editor_property('options', opts)
print("Task ready")
"""
r = mcp_run(cmd)
for o in r.get("output", []):
    print(o.get("output",""))
if r.get("result"):
    print("Result:", r["result"][:500])
