"""Deep review: module configs, material parameters, data interfaces"""
import json
import urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"
MATS = "/Game/EnvSandbox/VFX/Materials"
SAKURA = "/Game/EnvSandbox/VFX/Systems/Sakura"

def call_tool(name, args, timeout=30):
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": name, "arguments": args}}
    req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())

def get_text(result):
    return result.get("result", {}).get("content", [{}])[0].get("text", "")

def niagara(action, params):
    r = call_tool("niagara_query", {"action": action, "params": params})
    return json.loads(get_text(r))

# 1. Check existing parent material parameters
print("=" * 60)
print("MATERIAL REVIEW")
print("=" * 60)

parent_mats = [
    ("M_SakuraPetal", "Petal"),
    ("M_Niagara_SakuraSprite", "SpriteBase"),
    ("M_Niagara_Ripple", "Ripple"),
    ("M_SakuraRibbon", "Ribbon"),
    ("M_StardustParticle_Glow", "Stardust"),
]

for mat_name, label in parent_mats:
    mat_path = f"{MATS}/{mat_name}.{mat_name}"
    r = call_tool("material_query", {"action": "get_material_properties", "params": {"material_path": mat_path}})
    props_text = get_text(r)
    r2 = call_tool("material_query", {"action": "get_material_parameters", "params": {"material_path": mat_path}})
    params_text = get_text(r2)
    print(f"\n  {mat_name} ({label}):")
    try:
        # Check properties
        props = json.loads(props_text)
        if isinstance(props, dict):
            print(f"    Blend: {props.get('blend_mode', '?')}, Shading: {props.get('shading_model', '?')}, Domain: {props.get('domain', '?')}")
    except:
        print(f"    Props: {props_text[:100]}")
    
    try:
        params = json.loads(params_text)
        if isinstance(params, list):
            for p in params[:8]:  # first 8 params
                print(f"    [{p.get('type','?')}] {p.get('name','?')} = {p.get('default','?')}")
        elif isinstance(params, dict) and params.get("parameters"):
            for p in params["parameters"][:8]:
                print(f"    [{p.get('type','?')}] {p.get('name','?')} = {p.get('default','?')}")
        else:
            print(f"    Params: {json.dumps(params)[:200]}")
    except:
        print(f"    Params err: {params_text[:200]}")

# 2. Check the SKIP emitter modules for each unused original mat
print()
print("=" * 60)
print("EMITTERS USING ORIGINAL MATS (not MIs)")
print("=" * 60)

# NS_SakuraPetals_v2 extra emitters
for emitter in ["EM_PondRipple", "EM_PetalPile"]:
    print(f"\n  NS_SakuraPetals_v2/{emitter}:")
    r = niagara("get_ordered_modules", {"asset_path": f"{SAKURA}/NS_SakuraPetals_v2", "emitter": emitter})
    for stage, mods in r.get("stages", {}).items():
        for m in mods:
            print(f"    {stage}: {m.get('name', m.get('script', '?'))}")

# NS_WindRibbonGust/E_OmnidirectionalPetalBurst
print(f"\n  NS_WindRibbonGust/E_OmnidirectionalPetalBurst:")
r = niagara("get_ordered_modules", {"asset_path": f"{SAKURA}/NS_WindRibbonGust", "emitter": "E_OmnidirectionalPetalBurst"})
for stage, mods in r.get("stages", {}).items():
    for m in mods:
        print(f"    {stage}: {m.get('name', m.get('script', '?'))}")

# NS_ConstellationDraw
print(f"\n  NS_ConstellationDraw/Stars:")
r = niagara("get_ordered_modules", {"asset_path": f"{SAKURA}/NS_ConstellationDraw", "emitter": "Stars"})
for stage, mods in r.get("stages", {}).items():
    for m in mods:
        print(f"    {stage}: {m.get('name', m.get('script', '?'))}")

# 3. Check WindRibbonGust sprite emitter too
print(f"\n  NS_WindRibbonGust/Gust:")
r = niagara("get_ordered_modules", {"asset_path": f"{SAKURA}/NS_WindRibbonGust", "emitter": "Gust"})
for stage, mods in r.get("stages", {}).items():
    for m in mods:
        print(f"    {stage}: {m.get('name', m.get('script', '?'))}")

# 4. Get data interfaces for the sprite renderers
print()
print("=" * 60)
print("RENDERER PROPERTIES (for sprite renderers)")
print("=" * 60)

sprite_systems = [
    ("NS_SakuraPetals_v2", "Petals"),
    ("NS_SakuraDreamSparkle", "DreamMotes"),
    ("NS_SakuraLanternMotes", "LanternMotes"),
    ("NS_SakuraPetalGust", "OmnidirectionalBurst"),
    ("NS_WindRibbonGust", "E_OmnidirectionalPetalBurst"),
    ("NS_ConstellationDraw", "Stars"),
]
for sys_name, emitter in sprite_systems:
    r = niagara("list_renderer_properties", {"asset_path": f"{SAKURA}/{sys_name}", "emitter": emitter})
    props = r.get("properties", [])
    print(f"\n  {sys_name}/{emitter}:")
    for p in props:
        print(f"    {p.get('name', '?')} = {p.get('value', '?')} ({p.get('type', '?')})")
