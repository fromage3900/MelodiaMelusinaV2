"""Blender 5.2 MCP stdio adapter — launches blender.exe --background for each tool call.

No persistent daemon, no TCP sockets. Each tool spins up a headless Blender,
executes the Python code, and returns JSON. Safe, auditable, no corruption vector.

Uses --factory-startup to avoid broken third-party addons, then imports
surreal_architecture_gen (the Melodia Studio monolith) for genome tools.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import traceback as tb_mod
from typing import Any

BLENDER_EXE = os.environ.get(
    "BLENDER_EXE",
    r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe",
)
MONOLITH_PATH = os.environ.get(
    "MONOLITH_PATH",
    r"C:\Users\froma\AppData\Roaming\Blender Foundation\Blender\5.2\scripts\addons\surreal_architecture_gen.py",
)


def _run_blender(code: str, timeout: int = 90) -> dict[str, Any]:
    """Execute Python code in a headless Blender 5.2 instance."""
    preamble = "import bpy, json, sys, traceback\n"
    wrapped = (
        preamble
        + "try:\n"
        + "    " + code.replace("\n", "\n    ") + "\n"
        + "except Exception as e:\n"
        + "    print(json.dumps({'status': 'error', 'message': str(e), 'traceback': traceback.format_exc()}))\n"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(wrapped)
        script_path = f.name
    try:
        proc = subprocess.run(
            [BLENDER_EXE, "--background", "--factory-startup", "--python", script_path],
            capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        stdout = proc.stdout or ""
        for line in reversed(stdout.strip().split("\n")):
            line = line.strip()
            if line.startswith("{"):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
        stderr = (proc.stderr or "")[:500]
        return {"status": "error", "message": f"No JSON result", "stderr": stderr, "stdout": stdout[:500]}
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": f"Blender timed out after {timeout}s"}
    except FileNotFoundError:
        return {"status": "error", "message": f"Blender not found at {BLENDER_EXE}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        try:
            os.unlink(script_path)
        except OSError:
            pass


def _import_and_register() -> str:
    """Return Python code to import and register the surreal_architecture_gen monolith."""
    return (
        f"import sys, os\n"
        f"addon_dir = os.path.dirname({json.dumps(MONOLITH_PATH)})\n"
        f"if addon_dir not in sys.path:\n"
        f"    sys.path.insert(0, addon_dir)\n"
        f"import surreal_architecture_gen\n"
        f"surreal_architecture_gen.register()\n"
    )


TOOLS: dict[str, dict] = {}
RESOURCES: dict[str, dict] = {}


def tool(name: str, description: str, input_schema: dict | None = None):
    """Decorator to register an MCP tool."""
    def wrapper(fn):
        TOOLS[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema or {"type": "object", "properties": {}, "required": []},
            "fn": fn,
        }
        return fn
    return wrapper


def resource(uri: str, name: str, description: str, mime_type: str = "text/plain"):
    """Decorator to register an MCP resource (expert prompt template)."""
    def wrapper(fn):
        RESOURCES[uri] = {
            "uri": uri, "name": name, "description": description,
            "mimeType": mime_type, "fn": fn,
        }
        return fn
    return wrapper


# ── Expert prompt resources (guide AI assistants toward professional results) ──

@resource("melodia://studio/overview", "Melodia Studio Overview",
          "Complete overview of Melodia Studio capabilities, genome system, and GN builders.")
def _res_overview() -> str:
    return """# Melodia Studio — Surreal Architecture Generator (v2.131.0)

A Blender 5.2 addon for procedural surreal architecture with style genomes,
Greybox kits, 59 Geometry Node builders, and Unreal Engine game pipeline.

## Architecture
- **Monolith**: `surreal_architecture_gen` (~1.9MB, 38K lines) — main addon entry point
- **59 GN builders**: castle kit, music notation, ornaments, filigree, structures, effects, math ops
- **56 styles** across 8 groups: asian, zen, baroque, gothic, civic, castle, woods, greybox
- **18 Escher presets**: Penrose stairs, Mobius cathedral, fractal towers, etc.
- **31 Surreal OS genomes**: style genome definitions with DNA parameters
- **41 UI panels** in Properties editor + 3 panels in View3D sidebar (Melodia Studio tab)

## Key MCP Tools
- `list_genomes` — browse all 56 styles
- `apply_style` — apply a style group+id to active object
- `run_gn_builder` — build and apply a GN tree to an object
- `generate_rhythm_dungeon` — BPM-driven dungeon layout generation
- `validate_mesh` — check mesh health (non-manifold, UV, naming)

## Workflow: Natural Language → Architecture
1. Create/select a mesh object
2. Call `list_genomes` to see available styles
3. Call `apply_style` with group and style_id
4. Call `run_gn_builder` with a builder name like MEL_castle_tower
5. Call `generate` or tweak DNA sliders via `execute_blender_code`
"""

@resource("melodia://genome/workflow", "Genome Workflow Guide",
          "Step-by-step guide for using the Surreal OS genome system.")
def _res_genome_workflow() -> str:
    return """# Surreal OS Genome Workflow Guide

The genome system maps architectural DNA parameters to Geometry Node inputs.
It's a shape grammar system — define a genome once, generate infinite variations.

## DNA Parameters (per object)
- `genome_verticality` (0-1): tall/spires vs low/spread
- `genome_symmetry` (0-1): mirrored/axial vs asymmetric
- `genome_ornament_density` (0-1): bare vs richly decorated
- `genome_structural_logic` (0-1): rational/structural vs organic/fluid
- `genome_organic_growth` (0-1): rigid/geometric vs biological/vine-like
- `genome_cosmic_influence` (0-1): realistic vs surreal/otherworldly

## Style Groups
| Group | Best for | Typical Use |
|-------|----------|-------------|
| gothic | Cathedrals, churches, sacred | Verticality 0.8+, ornament 0.6+ |
| zen | Shrines, gardens, peaceful | Symmetry 0.7+, organic 0.3- |
| baroque | Palaces, classical, ornate | Ornament 0.8+, structural 0.7+ |
| castle | Fortifications, military | Verticality 0.6, symmetry 0.5 |
| asian | Pagodas, temples, bridges | Organic 0.4+, cosmic 0.3 |
| civic | Town halls, public buildings | Structural 0.7, symmetry 0.6 |
| woods | Experimental, deconstructivist | Cosmic 0.6+, organic 0.7+ |
| greybox | Level design, prototyping | All params moderate |

## Rhythm Game Integration (Cadence Strike)
Map BPM to DNA:
- BPM 80-100 → zen/asian (low ornament, wide spacing)
- BPM 120-140 → gothic/civic (medium density, mixed symmetry)
- BPM 160-180 → baroque/castle (dense, high verticality)
- BPM 200+ → woods/experimental (chaotic, cosmic high)
"""

@resource("melodia://pipeline/game-asset", "Game Asset Pipeline",
          "End-to-end pipeline: Blender procedural architecture → Unreal Engine game asset.")
def _res_pipeline() -> str:
    return """# Game Asset Pipeline: Blender → Unreal Engine

## Overview
Chain MCP servers for a single-prompt asset pipeline:
Blender MCP → surreal_arch → Monolith → Unreal Engine

## Pipeline Steps
1. **Model in Blender**: Create mesh + `apply_style` + `run_gn_builder`
2. **Generate**: `execute_blender_code` to call `bpy.ops.surreal_arch.generate`
3. **Validate**: `validate_mesh` for non-manifold, UV overlap, naming conventions
4. **Export**: `export_fbx` with Unreal-compatible settings
5. **Import in UE**: Use Monolith MCP (`blueprint_query`) or UEBlueprintMCP
6. **Configure materials**: Set up material instances in Unreal
7. **Place in level**: Position asset using Monolith MCP `editor_query`

## Best Practices
- Keep geometry manifold (procedural gen can create non-manifold edges)
- Name objects with SM_ prefix before export
- Use real-world scale (1 Blender unit = 1 meter)
- Bake trim sheets before export for game-ready materials
"""

@resource("melodia://pipeline/rhythm-dungeon", "Rhythm Dungeon Generator",
          "Generate Persona-style rhythm dungeons from BPM analysis.")
def _res_rhythm() -> str:
    return """# Rhythm Dungeon Generator (Cadence Strike)

Generate dungeon layouts where architecture responds to music BPM.
Inspired by Persona 5's procedurally-generated Palaces.

## BPM-to-Architecture Mapping
| BPM Range | Style | Spacing | Verticality | Mood |
|-----------|-------|---------|-------------|------|
| 80-100 (Ballad) | Zen/Asian | Wide (0.7) | Low (0.3) | Calm, exploratory |
| 100-120 (Downtempo) | Civic | Moderate (0.5) | Medium (0.4) | Structured |
| 120-140 (Pop/Rock) | Gothic | Medium (0.5) | High (0.7) | Dramatic, intense |
| 140-160 (House) | Baroque/Castle | Dense (0.3) | High (0.8) | Grand, imposing |
| 160-180 (DnB) | Woods/Greybox | Tight (0.2) | Very High (0.9) | Chaotic, urgent |
| 200+ (Speedcore) | Escher/custom | Variable | Extreme | Surreal, psychedelic |

## Workflow
1. Extract BPM from song (use `quantum_rank` service if available)
2. Call `generate_rhythm_dungeon` with BPM and room count
3. The system maps BPM to genome DNA parameters
4. Each room is generated with the appropriate style and DNA
5. Corridors between rooms use beat-synced spacing

## Output
- Individual room meshes with `Room_` prefix
- Collision-ready geometry
- Trim-baked materials for UE import
- Snap points for procedural assembly in Unreal
"""


@tool("get_scene_info", "Get info about the current Blender scene (objects, materials, version).")
def _get_scene_info(args: dict) -> dict:
    code = (
        "info = {\n"
        "    'version': list(bpy.app.version),\n"
        "    'scene': bpy.context.scene.name,\n"
        "    'object_count': len(bpy.context.scene.objects),\n"
        "    'objects': [{'name': o.name, 'type': o.type} for o in bpy.context.scene.objects[:50]],\n"
        "    'materials_count': len(bpy.data.materials),\n"
        "}\n"
        "print(json.dumps({'status': 'ok', 'result': info}))\n"
    )
    return _run_blender(code)


@tool("get_active_object", "Get details about the active object in the scene.")
def _get_active_object(args: dict) -> dict:
    code = (
        "obj = bpy.context.view_layer.objects.active\n"
        "if obj:\n"
        "    info = {'name': obj.name, 'type': obj.type, 'location': list(obj.location),\n"
        "        'rotation': list(obj.rotation_euler), 'scale': list(obj.scale), 'visible': obj.visible_get()}\n"
        "    if obj.type == 'MESH':\n"
        "        info['vertices'] = len(obj.data.vertices)\n"
        "        info['faces'] = len(obj.data.polygons)\n"
        "    print(json.dumps({'status': 'ok', 'result': info}))\n"
        "else:\n"
        "    print(json.dumps({'status': 'ok', 'result': None}))\n"
    )
    return _run_blender(code)


@tool("execute_blender_code", "Execute arbitrary Python code in Blender with bpy available.",
      {"type": "object", "properties": {"code_string": {"type": "string", "description": "Python code to execute"}},
       "required": ["code_string"]})
def _execute_blender_code(args: dict) -> dict:
    code = (
        f"exec({json.dumps(args['code_string'])}, {{'bpy': bpy, 'json': json}})\n"
        "print(json.dumps({'status': 'ok', 'result': 'executed'}))\n"
    )
    return _run_blender(code)


@tool("list_genomes", "List all available surreal_arch style genomes (56 styles across 8 groups).")
def _list_genomes(args: dict) -> dict:
    code = (
        _import_and_register() +
        "mod = sys.modules.get('surreal_architecture_gen')\n"
        "if mod and hasattr(mod, 'STYLE_REGISTRY'):\n"
        "    items = []\n"
        "    for group, styles in mod.STYLE_REGISTRY.items():\n"
        "        for sid in styles:\n"
        "            items.append({'group': group, 'id': sid})\n"
        "    presets = getattr(mod, 'ESCHER_PRESETS', {})\n"
        "    print(json.dumps({'status': 'ok', 'result': {\n"
        "        'total': len(items), 'styles': items, 'groups': list(mod.STYLE_REGISTRY.keys()),\n"
        "        'escher_presets': list(presets.keys()) if presets else []\n"
        "    }}))\n"
        "else:\n"
        "    print(json.dumps({'status': 'ok', 'result': {'total': 0, 'styles': [],\n"
        "        'note': 'surreal_architecture_gen not loaded'}}))\n"
    )
    return _run_blender(code, timeout=120)


@tool("apply_style", "Apply a style from STYLE_REGISTRY to the active object.",
      {"type": "object",
       "properties": {
           "style_group": {"type": "string", "description": "Style group (gothic, zen, baroque, castle, civic, asian, woods, greybox)"},
           "style_id": {"type": "string", "description": "Style ID within the group"}},
       "required": ["style_group", "style_id"]})
def _apply_style(args: dict) -> dict:
    code = (
        _import_and_register() +
        f"sg = {json.dumps(args['style_group'])}\n"
        f"si = {json.dumps(args['style_id'])}\n"
        "mod = sys.modules.get('surreal_architecture_gen')\n"
        "if not mod or not hasattr(mod, 'STYLE_REGISTRY'):\n"
        "    print(json.dumps({'status': 'error', 'message': 'monolith not loaded'}))\n"
        "elif sg not in mod.STYLE_REGISTRY:\n"
        "    print(json.dumps({'status': 'error', 'message': f'Unknown group {sg}'}))\n"
        "elif si not in mod.STYLE_REGISTRY[sg]:\n"
        "    print(json.dumps({'status': 'error', 'message': f'Unknown style {si}'}))\n"
        "else:\n"
        "    obj = bpy.context.view_layer.objects.active\n"
        "    if not obj:\n"
        "        print(json.dumps({'status': 'error', 'message': 'No active object'}))\n"
        "    else:\n"
        "        if hasattr(obj, 'surreal_arch_props'):\n"
        "            p = obj.surreal_arch_props\n"
        "            p.arch_type = si\n"
        "        print(json.dumps({'status': 'ok', 'result': {'group': sg, 'style': si, 'object': obj.name}}))\n"
    )
    return _run_blender(code, timeout=120)


@tool("create_mesh", "Create a mesh primitive in Blender.",
      {"type": "object",
       "properties": {
           "name": {"type": "string", "description": "Name for the new object"},
           "mesh_type": {"type": "string", "description": "CUBE, SPHERE, CYLINDER, PLANE, CONE, or TORUS"}},
       "required": ["name", "mesh_type"]})
def _create_mesh(args: dict) -> dict:
    name = args.get("name", "NewMesh")
    mt = args.get("mesh_type", "CUBE").upper()
    valid = {"CUBE": "cube_add", "SPHERE": "uv_sphere_add", "CYLINDER": "cylinder_add",
             "PLANE": "plane_add", "CONE": "cone_add", "TORUS": "torus_add"}
    if mt not in valid:
        return {"status": "error", "message": f"Invalid mesh_type {mt}"}
    code = (
        f"bpy.ops.mesh.primitive_{valid[mt]}()\n"
        f"obj = bpy.context.active_object\n"
        f"obj.name = {json.dumps(name)}\n"
        "print(json.dumps({'status': 'ok', 'result': {'name': obj.name, 'type': obj.type}}))\n"
    )
    return _run_blender(code)


@tool("list_materials", "List all materials in the current Blender scene.")
def _list_materials(args: dict) -> dict:
    code = (
        "mats = [{'name': m.name, 'users': m.users} for m in bpy.data.materials]\n"
        "print(json.dumps({'status': 'ok', 'result': {'materials': mats, 'count': len(mats)}}))\n"
    )
    return _run_blender(code)


@tool("export_fbx", "Export selected objects to FBX.",
      {"type": "object", "properties": {
          "file_path": {"type": "string", "description": "Full path for the FBX file (default: temp file)"}},
       "required": []})
def _export_fbx(args: dict) -> dict:
    path = args.get("file_path", "")
    code = (
        f"import os, tempfile\n"
        f"path = {json.dumps(path)} or os.path.join(tempfile.gettempdir(), 'blender_export.fbx')\n"
        "bpy.ops.export_scene.fbx(filepath=path, use_selection=True)\n"
        "print(json.dumps({'status': 'ok', 'result': {'path': path}}))\n"
    )
    return _run_blender(code)


@tool("list_gn_builders", "List all 59 registered Geometry Node builders by category.")
def _list_gn_builders(args: dict) -> dict:
    code = (
        _import_and_register() +
        "from surreal_arch.melodia_gn.core import GROUP_METADATA, CATEGORY_META\n"
        "cats = {}\n"
        "for name, meta in GROUP_METADATA.items():\n"
        "    cid = meta.get('category', 'Other')\n"
        "    cats.setdefault(cid, []).append({'name': name, 'label': meta.get('label', name)})\n"
        "cats_sorted = {k: sorted(v, key=lambda x: x['label']) for k, v in sorted(cats.items())}\n"
        "print(json.dumps({'status': 'ok', 'result': {'categories': {k: [x['name'] for x in v] for k, v in cats_sorted.items()}, 'total': len(GROUP_METADATA)}}))\n"
    )
    return _run_blender(code, timeout=120)


@tool("run_gn_builder", "Build and apply a Geometry Node tree to an object.",
      {"type": "object",
       "properties": {
           "builder_name": {"type": "string", "description": "Builder name (e.g. MEL_castle_tower, MEL_music_note_head, MEL_ornament_vine)"},
           "object_name": {"type": "string", "description": "Target object name (empty = active object)"}},
       "required": ["builder_name"]})
def _run_gn_builder(args: dict) -> dict:
    bname = args.get("builder_name", "")
    oname = args.get("object_name", "")
    code = (
        _import_and_register() +
        f"bname = {json.dumps(bname)}\n"
        f"oname = {json.dumps(oname)}\n"
        "from surreal_arch.melodia_gn.core import GROUP_BUILDERS, GROUP_METADATA\n"
        "if bname not in GROUP_BUILDERS:\n"
        "    print(json.dumps({'status': 'error', 'message': f'Builder {bname} not found'}))\n"
        "else:\n"
        "    obj = bpy.data.objects.get(oname) or bpy.context.active_object\n"
        "    if not obj:\n"
        "        print(json.dumps({'status': 'error', 'message': 'No target object'}))\n"
        "    else:\n"
        "        result = GROUP_BUILDERS[bname]()\n"
        "        tree = result[0] if isinstance(result, (tuple, list)) else result\n"
        "        mod = obj.modifiers.new(name=bname, type='NODES')\n"
        "        mod.node_group = tree\n"
        "        meta = GROUP_METADATA.get(bname, {})\n"
        "        print(json.dumps({'status': 'ok', 'result': {'builder': bname, 'object': obj.name, 'category': meta.get('category', ''), 'label': meta.get('label', bname)}}))\n"
    )
    return _run_blender(code, timeout=120)


@tool("validate_mesh", "Validate a mesh for game-readiness (non-manifold, UV, naming).",
      {"type": "object", "properties": {
          "object_name": {"type": "string", "description": "Object name (empty = active object)"}},
       "required": []})
def _validate_mesh(args: dict) -> dict:
    oname = args.get("object_name", "")
    code = (
        f"oname = {json.dumps(oname)}\n"
        "obj = bpy.data.objects.get(oname) or bpy.context.active_object\n"
        "if not obj or obj.type != 'MESH':\n"
        "    print(json.dumps({'status': 'error', 'message': 'No mesh object'}))\n"
        "else:\n"
        "    import bmesh\n"
        "    mesh = obj.data\n"
        "    info = {'name': obj.name, 'vertices': len(mesh.vertices), 'faces': len(mesh.polygons)}\n"
        "    # Non-manifold edges\n"
        "    bm = bmesh.new()\n"
        "    bm.from_mesh(mesh)\n"
        "    bm.edges.ensure_lookup_table()\n"
        "    non_manifold = sum(1 for e in bm.edges if not e.is_manifold)\n"
        "    bm.free()\n"
        "    info['non_manifold_edges'] = non_manifold\n"
        "    # UV check\n"
        "    uv_layers = len(mesh.uv_layers)\n"
        "    info['uv_layers'] = uv_layers\n"
        "    has_uv = uv_layers > 0 and any(l.data for l in mesh.uv_layers if l.data)\n"
        "    info['has_valid_uv'] = has_uv\n"
        "    # Naming convention\n"
        "    name_ok = obj.name.startswith(('SM_', 'UBX_', 'UCX_', 'Room_'))\n"
        "    info['name_convention_ok'] = name_ok\n"
        "    info['health'] = 'pass' if (non_manifold == 0 and has_uv) else 'warn'\n"
        "    print(json.dumps({'status': 'ok', 'result': info}))\n"
    )
    return _run_blender(code, timeout=60)


@tool("generate_rhythm_dungeon", "Generate a BPM-driven rhythm dungeon layout.",
      {"type": "object",
       "properties": {
           "bpm": {"type": "number", "description": "Song BPM (80-200+)"},
           "room_count": {"type": "integer", "description": "Number of rooms (3-12)"},
           "base_name": {"type": "string", "description": "Root collection name"}},
       "required": ["bpm", "room_count"]})
def _generate_rhythm_dungeon(args: dict) -> dict:
    bpm = args.get("bpm", 120)
    rooms = args.get("room_count", 5)
    bname = args.get("base_name", "RhythmDungeon")
    # Map BPM to style and DNA
    if bpm < 100:
        sg, sv, sd = "zen", 0.3, 0.7
    elif bpm < 120:
        sg, sv, sd = "civic", 0.4, 0.5
    elif bpm < 140:
        sg, sv, sd = "gothic", 0.7, 0.5
    elif bpm < 160:
        sg, sv, sd = "baroque", 0.8, 0.3
    elif bpm < 180:
        sg, sv, sd = "castle", 0.9, 0.2
    else:
        sg, sv, sd = "greybox", 0.9, 0.1
    # Pick a random style from the group
    code = (
        _import_and_register() +
        f"sg = {json.dumps(sg)}\n"
        f"sv_val = {sv}\n"
        f"sd_val = {sd}\n"
        f"rooms = {rooms}\n"
        f"bname = {json.dumps(bname)}\n"
        "mod = sys.modules.get('surreal_architecture_gen')\n"
        "style_ids = [sid for sid in mod.STYLE_REGISTRY.get(sg, {}) if sid not in ('panel_label', 'bl_idname', 'class_name', 'match', 'picker_hint', 'glossary', 'hints_by_type')]\n"
        "import random; random.seed()\n"
        "if not style_ids:\n"
        "    style_ids = list(mod.STYLE_REGISTRY.get(sg, {}).keys())\n"
        "results = []\n"
        "for i in range(rooms):\n"
        "    sid = random.choice(style_ids) if style_ids else list(mod.STYLE_REGISTRY.get(sg, {}).keys())[0]\n"
        "    bpy.ops.mesh.primitive_cube_add(size=2, location=(i * 5, 0, 0))\n"
        "    obj = bpy.context.active_object\n"
        "    obj.name = f'{bname}_Room_{i:02d}'\n"
        "    if hasattr(obj, 'surreal_arch_props'):\n"
        "        p = obj.surreal_arch_props\n"
        "        p.arch_type = sid\n"
        "        p.genome_verticality = sv_val + random.uniform(-0.1, 0.1)\n"
        "        p.genome_ornament_density = sd_val + random.uniform(-0.1, 0.1)\n"
        "    results.append({'room': obj.name, 'style': sg, 'style_id': sid, 'position': [i * 5, 0, 0]})\n"
        "print(json.dumps({'status': 'ok', 'result': {'rooms': results, 'bpm': bpm, 'style_group': sg, 'total': rooms}}))\n"
    )
    return _run_blender(code, timeout=300)


# ── MCP stdio server (raw JSON-RPC, compatible with older mcp package) ──

def _send(msg: dict):
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def main():
    # Read JSON-RPC requests line by line from stdin
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params", {})

        if method == "initialize":
            _send({
                "jsonrpc": "2.0", "id": req_id,
                "result": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {"tools": {}, "resources": {}},
                    "serverInfo": {"name": "Blender 5.2 MCP", "version": "2.0.0"},
                }
            })
        elif method == "notifications/initialized":
            pass  # no response expected
        elif method == "tools/list":
            tool_list = [
                {"name": t["name"], "description": t["description"], "inputSchema": t["inputSchema"]}
                for t in TOOLS.values()
            ]
            _send({"jsonrpc": "2.0", "id": req_id, "result": {"tools": tool_list}})
        elif method == "resources/list":
            res_list = [
                {"uri": r["uri"], "name": r["name"], "description": r["description"], "mimeType": r["mimeType"]}
                for r in RESOURCES.values()
            ]
            _send({"jsonrpc": "2.0", "id": req_id, "result": {"resources": res_list}})
        elif method == "resources/read":
            uri = params.get("uri", "")
            if uri in RESOURCES:
                text = RESOURCES[uri]["fn"]()
                _send({"jsonrpc": "2.0", "id": req_id,
                       "result": {"contents": [{"uri": uri, "mimeType": RESOURCES[uri]["mimeType"], "text": text}]}})
            else:
                _send({"jsonrpc": "2.0", "id": req_id,
                       "error": {"code": -32602, "message": f"Resource not found: {uri}"}})
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            if tool_name not in TOOLS:
                _send({"jsonrpc": "2.0", "id": req_id,
                       "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}})
            else:
                try:
                    result = TOOLS[tool_name]["fn"](tool_args)
                    _send({"jsonrpc": "2.0", "id": req_id,
                           "result": {"content": [{"type": "text", "text": json.dumps(result)}]}})
                except Exception as e:
                    _send({"jsonrpc": "2.0", "id": req_id,
                           "error": {"code": -32000, "message": str(e)}})
        elif method == "shutdown":
            _send({"jsonrpc": "2.0", "id": req_id, "result": None})
        elif method == "exit":
            break
        else:
            _send({"jsonrpc": "2.0", "id": req_id,
                   "error": {"code": -32601, "message": f"Method not found: {method}"}})


if __name__ == "__main__":
    main()
