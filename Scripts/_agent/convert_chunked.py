import json, sys, urllib.request, time

MCP = "http://127.0.0.1:9316/mcp"

def call(script, timeout=300):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": "editor_query",
                                  "arguments": {"action": "run_python", "command": script}}}).encode()
    r = json.loads(urllib.request.urlopen(urllib.request.Request(
        MCP, data=body, headers={"Content-Type": "application/json"}), timeout=timeout).read())
    res = r.get("result", {})
    return not res.get("isError")

def healthy():
    try:
        urllib.request.urlopen("http://localhost:9316/health", timeout=3)
        return True
    except Exception:
        return False

CHUNK_SCRIPT = '''
import unreal
mic_list = %s
MASTER = unreal.load_asset("/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal")
done = 0
for p in mic_list:
    mi = unreal.load_asset(p)
    if not mi:
        continue
    try:
        parent = mi.get_editor_property("parent")
        if parent and str(parent.get_name()) == "M_Master_Toon_Universal":
            continue
        unreal.MaterialEditingLibrary.set_material_instance_parent(mi, MASTER)
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, "PaletteRampLow", unreal.LinearColor(0.42, 0.36, 0.48, 1.0))
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, "PaletteRampMid", unreal.LinearColor(0.93, 0.85, 0.72, 1.0))
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, "PaletteRampHigh", unreal.LinearColor(1.0, 0.97, 0.90, 1.0))
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "RampSharpness", 0.65)
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "RampContrast", 0.55)
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "RampStrength", 0.9)
        done += 1
    except Exception:
        pass
unreal.EditorAssetLibrary.save_directory("/Game/EnvSandbox/Meshes", only_if_is_dirty=True, recursive=True)
import json
open(r"C:/Users/froma/AppData/Local/Temp/opencode/convert_chunk_progress.json","w").write(json.dumps({"done": done}))
'''

# collect all MICs under Environment
collect = '''
import unreal, json
reg = unreal.AssetRegistryHelpers.get_asset_registry()
mics = []
for a in reg.get_assets_by_path("/Game/EnvSandbox/Meshes/Environment", recursive=True):
    if str(a.asset_class_path.asset_name) == "MaterialInstanceConstant":
        mics.append(str(a.package_name) + "." + str(a.asset_name))
open(r"C:/Users/froma/AppData/Local/Temp/opencode/mic_list.json","w").write(json.dumps(mics))
'''
call(collect)
mics = json.load(open(r"C:\Users\froma\AppData\Local\Temp\opencode\mic_list.json"))
print("total MICs:", len(mics))

BATCH = 100
total = 0
for i in range(0, len(mics), BATCH):
    if not healthy():
        print("editor down at chunk", i // BATCH, "- waiting")
        for _ in range(90):
            time.sleep(10)
            if healthy():
                break
        if not healthy():
            print("editor never recovered; stopping")
            break
    chunk = mics[i:i + BATCH]
    ok = call(CHUNK_SCRIPT % json.dumps(chunk), timeout=500)
    if ok:
        total += BATCH
        print("chunk", i // BATCH, "ok (", total, "/", len(mics), ")")
    else:
        print("chunk", i // BATCH, "failed/connection issue - retry once")
        time.sleep(10)
        ok = call(CHUNK_SCRIPT % json.dumps(chunk), timeout=500)
        if not ok:
            print("stopping at chunk", i // BATCH)
            break

print("DONE converted:", total)
