"""
[DEPRECATED 2026-08-06] Surreal Arch MCP adapter - wraps surreal_arch genome tools via port 9877 execute_code.

Replaced by: deploy/blender_5.2_mcp.py (stdio MCP server, no TCP sockets, --factory-startup safe)
Migration: use blender-5.2 MCP server in .mcp.json instead of this TCP socket adapter.

Kept for reference only. Do not use in new automation.
"""
from __future__ import annotations

import json
import socket
import sys
import time

HOST = "127.0.0.1"
PORT = 9877
CMD_TIMEOUT = 15

TOOLS = [
    {
        "name": "surreal_list_genomes",
        "description": "List all 42 surreal_arch style genomes",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "surreal_status",
        "description": "Get active object's surreal_arch genome properties",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "surreal_apply_genome",
        "description": "Apply a style genome to the active object",
        "inputSchema": {
            "type": "object",
            "properties": {
                "genome_id": {"type": "string", "description": "Genome ID (e.g. ZEN_SHRINE_AXIS, GOTHIC_CATHEDRAL)"}
            },
            "required": ["genome_id"],
        },
    },
    {
        "name": "surreal_randomize_dna",
        "description": "Randomize genome DNA on active object with optional seed",
        "inputSchema": {
            "type": "object",
            "properties": {"seed": {"type": "integer", "description": "Random seed (optional)"}},
            "required": [],
        },
    },
    {
        "name": "surreal_spawn_graph",
        "description": "Spawn a greybox graph for a genome ID",
        "inputSchema": {
            "type": "object",
            "properties": {"genome_id": {"type": "string", "description": "Genome ID to spawn"}},
            "required": ["genome_id"],
        },
    },
    {
        "name": "surreal_smoke_test",
        "description": "Run the surreal_arch smoke test harness",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "surreal_execute",
        "description": "Execute arbitrary surreal_arch Blender Python code",
        "inputSchema": {
            "type": "object",
            "properties": {"code": {"type": "string", "description": "Python code using bpy and surreal_arch modules"}},
            "required": ["code"],
        },
    },
]


def _exec(code: str) -> dict:
    payload = json.dumps({"type": "execute_code", "params": {"code": code}})
    try:
        s = socket.create_connection((HOST, PORT), timeout=5)
        s.settimeout(CMD_TIMEOUT)
        s.sendall(payload.encode("utf-8"))
        time.sleep(2.5)
        resp = b""
        while True:
            try:
                chunk = s.recv(4096)
                if not chunk:
                    break
                resp += chunk
            except socket.timeout:
                break
        s.close()
        if not resp:
            return {"status": "error", "message": "empty response"}
        return json.loads(resp.decode("utf-8"))
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _handle_tool(name: str, args: dict) -> dict:
    if name == "surreal_list_genomes":
        code = """
import sys, json
mod = sys.modules.get('surreal_architecture_gen')
if mod:
    meta = getattr(mod, '_STYLE_GENOME_META', {})
    groups = getattr(mod, '_STYLE_GENOME_GROUPS', {})
    items = []
    for gid in getattr(mod, '_STYLE_GENOMES', []):
        m = meta.get(gid, {})
        items.append({'id': gid, 'family': m.get('family',''), 'graph': m.get('graph',''), 'transform': m.get('transform','none')})
    print(json.dumps({'total': len(items), 'genomes': items, 'groups': {k: list(v) for k, v in groups.items()}}))
else:
    print('{"error": "surreal_architecture_gen not loaded"}')
"""
        return _exec(code)
    if name == "surreal_status":
        code = """
import json
obj = bpy.context.active_object
if obj and hasattr(obj, 'surreal_arch_props'):
    p = obj.surreal_arch_props
    print(json.dumps({
        'name': obj.name, 'type': obj.type,
        'arch_type': p.arch_type, 'genome_id': getattr(p, 'style_genome_id', ''),
        'verticality': p.genome_verticality, 'symmetry': p.genome_symmetry,
        'ornament_density': p.genome_ornament_density,
        'structural_logic': p.genome_structural_logic,
        'organic_growth': p.genome_organic_growth,
        'cosmic_influence': p.genome_cosmic_influence,
    }))
else:
    print('{"active_object": null}')
"""
        return _exec(code)
    if name == "surreal_apply_genome":
        code = f"""
import sys, json
gid = '{args["genome_id"]}'
mod = sys.modules.get('surreal_architecture_gen')
if not mod:
    print('{{"error": "surreal_architecture_gen not loaded"}}')
else:
    try:
        from surreal_os import genome as os_genome
        obj = bpy.context.active_object
        if not obj or not hasattr(obj, 'surreal_arch_props'):
            print('{{"error": "No active mesh object"}}')
        else:
            os_genome.apply_genome(obj.surreal_arch_props, gid, monolith=mod)
            mod._active_style_genome = os_genome.load_genome(gid)
            bpy.context.view_layer.objects.active = obj
            print(f'{{"ok": true, "genome_id": "{gid}"}}')
    except Exception as e:
        print(f'{{"error": "{{e}}"}}')
"""
        return _exec(code)
    if name == "surreal_randomize_dna":
        seed = args.get("seed", "")
        code = f"""
import json, random
obj = bpy.context.active_object
if not obj or not hasattr(obj, 'surreal_arch_props'):
    print('{{"error": "No active mesh object"}}')
else:
    p = obj.surreal_arch_props
    axes = ['genome_verticality','genome_symmetry','genome_ornament_density','genome_structural_logic','genome_organic_growth','genome_cosmic_influence']
    rng = random.Random({seed} or random.randint(0,9999))
    for a in axes:
        setattr(p, a, rng.uniform(0.0, 1.0))
    print(json.dumps({{'ok': True, 'seed': {"seed"} or 'random', 'values': {{a: getattr(p, a) for a in axes}}}}))
"""
        return _exec(code)
    if name == "surreal_spawn_graph":
        code = f"""
import sys, json
gid = '{args["genome_id"]}'
mod = sys.modules.get('surreal_architecture_gen')
if not mod:
    print('{{"error": "surreal_architecture_gen not loaded"}}')
else:
    try:
        from surreal_os import genome as os_genome
        genome_data = os_genome.load_genome(gid)
        graph_id = genome_data.get('default_graph', 'ZEN_SHRINE_AXIS')
        from surreal_greybox.greybox_graph import GRAPH_REGISTRY, spawn_graph, resolve_graph_spacing
        meta = GRAPH_REGISTRY.get(graph_id)
        if not meta:
            print(f'{{"error": "Graph {{graph_id}} not found"}}')
        else:
            obj = bpy.context.active_object
            if obj and hasattr(obj, 'surreal_arch_props'):
                os_genome.apply_genome(obj.surreal_arch_props, gid, monolith=mod)
            spacing = resolve_graph_spacing(bpy.context)
            objs = spawn_graph(bpy.context, mod, meta['spec'], spacing=spacing, graph_id=graph_id)
            print(f'{{"ok": true, "graph_id": "{{graph_id}}", "spawned": {{len(objs)}}}}')
    except Exception as e:
        print(f'{{"error": "{{e}}"}}')
"""
        return _exec(code)
    if name == "surreal_smoke_test":
        code = """
import sys, json
mod = sys.modules.get('surreal_architecture_gen')
if not mod:
    print('{"error": "surreal_architecture_gen not loaded"}')
else:
    try:
        from surreal_arch.smoke_harness import run_smoke
        result = run_smoke()
        print(json.dumps({'ok': True, 'result': str(result)[:500]}))
    except Exception as e:
        print(f'{"error": "{e}"}')
"""
        return _exec(code)
    if name == "surreal_execute":
        return _exec(args["code"])
    return {"status": "error", "message": f"Unknown tool: {name}"}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        rid = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params", {})

        if method == "initialize":
            sys.stdout.write(json.dumps({
                "jsonrpc": "2.0", "id": rid,
            "result": {
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "surreal-arch-mcp-adapter", "version": "1.0.0"},
            }
            }) + "\n")
            sys.stdout.flush()
        elif method == "tools/list":
            sys.stdout.write(json.dumps({
                "jsonrpc": "2.0", "id": rid,
                "result": {"tools": TOOLS}
            }) + "\n")
            sys.stdout.flush()
        elif method == "tools/call":
            result = _handle_tool(params.get("name", ""), params.get("arguments", {}))
            sys.stdout.write(json.dumps({
                "jsonrpc": "2.0", "id": rid,
                "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
            }) + "\n")
            sys.stdout.flush()
        elif method == "notifications/initialized":
            pass
        else:
            sys.stdout.write(json.dumps({
                "jsonrpc": "2.0", "id": rid,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
