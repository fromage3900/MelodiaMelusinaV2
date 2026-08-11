"""Verify MIs exist and assign to renderers"""
import json
import urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"
MATS = "/Game/EnvSandbox/VFX/Materials"
SAKURA = "/Game/EnvSandbox/VFX/Systems/Sakura"

def call_tool(name, args, timeout=15):
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": name, "arguments": args}}
    req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())

def get_text(result):
    return result.get("result", {}).get("content", [{}])[0].get("text", "")

# New MIs + their system assignments
mier = [
    ("MI_Niagara_Sparkle", "M_Niagara_SakuraSprite"),
    ("MI_Niagara_Petal", "M_SakuraPetal"),
    ("MI_Niagara_Mote", "M_Niagara_SakuraSprite"),
    ("MI_Niagara_Pond", "M_Niagara_Ripple"),
    ("MI_Niagara_Gust", "M_Niagara_SakuraSprite"),
]

# Verify each MI exists by trying to assign it to a renderer (will fail if not found)
print("=== Verify MIs exist ===")
for mi_name, parent_name in mier:
    path = f"{MATS}/{mi_name}.{mi_name}"
    r = call_tool("material_query", {"action": "get_material_parameters", "params": {
        "material_path": path,
    }})
    is_err = r.get("result", {}).get("isError", False)
    print(f"  {mi_name}: {'EXISTS' if not is_err else 'MISSING / ' + get_text(r)[:60]}")

print()

# Now assign to systems
# NS_SakuraPondShimmer uses mesh renderer, so skip that one for now
assignments = [
    ("NS_SakuraPetals", "CanopyDrift", 0, "MI_Niagara_Petal"),
    ("NS_SakuraPetals_v2", "Petals", 0, "MI_Niagara_Petal"),
    ("NS_SakuraPetals_v2", "Petals", 1, "MI_Niagara_Petal"),
    ("NS_SakuraGroundPetals", "GroundPetals", 0, "MI_Niagara_Petal"),
    ("NS_SakuraDreamSparkle", "DreamMotes", 0, "MI_Niagara_Sparkle"),
    ("NS_SakuraLanternMotes", "LanternMotes", 0, "MI_Niagara_Mote"),
    ("NS_SakuraPondShimmer", "Ripples", 0, "MI_Niagara_Pond"),
    ("NS_SakuraWaterPetals", "GroundPetals", 0, "MI_Niagara_Petal"),
]

print("=== Assign MIs to renderers ===")
for sys_name, emitter, ri, mi_name in assignments:
    asset = f"{SAKURA}/{sys_name}"
    mat_path = f"{MATS}/{mi_name}.{mi_name}"
    r = call_tool("niagara_query", {"action": "set_renderer_material", "params": {
        "asset_path": asset,
        "emitter": emitter,
        "renderer_index": ri,
        "material": mat_path,
    }})
    is_err = r.get("result", {}).get("isError", False)
    status = "OK" if not is_err else f"FAIL: {get_text(r)[:80]}"
    print(f"  {sys_name}/{emitter}[{ri}] <- {mi_name}: {status}")

print()

# Save all modified systems
print("=== Save systems ===")
for sys_name, _, _, _ in assignments:
    asset = f"{SAKURA}/{sys_name}"
    r = call_tool("niagara_query", {"action": "save_system", "params": {"asset_path": asset}})
    is_err = r.get("result", {}).get("isError", False)
    status = "OK" if not is_err else f"FAIL: {get_text(r)[:80]}"
    print(f"  {sys_name}: {status}")

print()

# Verify final state
print("=== Verify renderers ===")
for sys_name, emitter, ri, mi_name in assignments:
    asset = f"{SAKURA}/{sys_name}"
    r = call_tool("niagara_query", {"action": "list_renderers", "params": {"asset_path": asset, "emitter": emitter}})
    text = get_text(r)
    try:
        data = json.loads(text)
        for rend in data.get("renderers", []):
            if rend.get("index") == ri:
                rm = rend.get("material", "?")
                ok = mi_name in rm
                print(f"  {'OK' if ok else 'MISMATCH'}: {sys_name}/{emitter}[{ri}] -> {rm}")
    except:
        print(f"  FAIL parse: {text[:100]}")
