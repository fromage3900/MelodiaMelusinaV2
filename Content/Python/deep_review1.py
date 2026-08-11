"""Deep review: full project inventory"""
import json
import urllib.request
from datetime import datetime

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

# 1. List ALL systems in the project
print("=" * 60)
print("PHASE 1: PROJECT INVENTORY")
print("=" * 60)

# Search with broad filter
r = call_tool("niagara_query", {"action": "list_systems", "params": {"search": "", "path": SAKURA}})
data = json.loads(get_text(r))
all_systems = []
for s in data.get("systems", []):
    name = s.get("name", s.get("path", "?"))
    p = s.get("path", "?")
    all_systems.append((name, p))
    print(f"  System: {name}")
    print(f"    Path: {p}")

print(f"\nTotal systems found: {len(all_systems)}")

# 2. For each system, get summary + emitter details
for sys_name, sys_path in all_systems:
    print("=" * 50)
    print(f"SYSTEM: {sys_name}")
    print("-" * 50)
    
    # Summary
    r = call_tool("niagara_query", {"action": "get_system_summary", "params": {"asset_path": sys_path}})
    summary = json.loads(get_text(r))
    
    props = summary.get("system_properties", {})
    print(f"  Effect Type: {props.get('effect_type', 'N/A')}")
    print(f"  Warmup: {props.get('warmup_time', 0)}s")
    print(f"  Deterministic: {props.get('determinism', False)}")
    print(f"  Fixed Bounds: {props.get('fixed_bounds', False)}")
    
    user_params = summary.get("user_parameters", [])
    if user_params:
        print(f"  User Params ({len(user_params)}):")
        for up in user_params:
            print(f"    {up.get('name', '?')} = {up.get('default', '?')} ({up.get('type', '?')})")
    
    # Emitters
    emitters = summary.get("emitters", [])
    for em in emitters:
        ename = em.get("name", "?")
        sim = em.get("sim_target", "?")
        ls = em.get("local_space", False)
        print(f"\n  Emitter: {ename}")
        print(f"      Sim: {sim}, LocalSpace: {ls}, Enabled: {em.get('enabled', True)}")
        print(f"      Sprite: {em.get('has_sprite_renderer')}, Ribbon: {em.get('has_ribbon_renderer')}, Mesh: {em.get('has_mesh_renderer')}")
        
        # Renderers
        r2 = call_tool("niagara_query", {"action": "list_renderers", "params": {"asset_path": sys_path, "emitter": ename}})
        rends = json.loads(get_text(r2))
        for rd in rends.get("renderers", []):
            print(f"        Renderer[{rd['index']}]({rd['type']}): {rd.get('material', 'NONE').split('/')[-1]}")
        
        # Modules per stage
        r3 = call_tool("niagara_query", {"action": "get_ordered_modules", "params": {"asset_path": sys_path, "emitter": ename}})
        modules = json.loads(get_text(r3))
        stages = modules.get("stages", modules.get("modules", []))
        if isinstance(stages, dict):
            for stage_name, mods in stages.items():
                mod_names = [m.get("name", m.get("script", "?")) for m in mods]
                print(f"        {stage_name}: {', '.join(mod_names)}")
        
        # Event handlers
        r4 = call_tool("niagara_query", {"action": "get_event_handlers", "params": {"asset_path": sys_path, "emitter": ename}})
        events = json.loads(get_text(r4))
        handlers = events.get("event_handlers", [])
        if handlers:
            for h in handlers:
                print(f"        Event: {h.get('source_event', '?')} -> {h.get('execution_mode', '?')}")
