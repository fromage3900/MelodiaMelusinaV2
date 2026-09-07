# Melodia / Monolith MCP Tool Reference

**Purpose:** how to drive the live editor from outside it. Written 2026-09-06
after using Monolith to resolve pin names that Unreal's Python API would not
expose. Companion doc: `Docs/MATERIAL_AUTHORING_GUIDE.md`.

---

## 1. Endpoints

From `BS_GodFile/.mcp.json`:

| server | transport | address |
|---|---|---|
| **Monolith** | HTTP | `http://127.0.0.1:9316/mcp` |
| claireon | HTTP | `http://127.0.0.1:60162/mcp` |
| melodia | stdio | `deploy/melodia_mcp_server.py` (`MONOLITH_URL` → 9316) |
| agent_bridge | stdio | `deploy/agent_bridge_mcp.py` — policy-gated, raw UE denied |

Monolith requires the editor to be **running**. It exposes 28 tools; the
material domain alone has 60+ actions.

Bind loopback only. Never `0.0.0.0`.

---

## 2. Calling it

Two helpers live in `Tools/` (gitignored — recreate from this doc if lost).

`Tools/mono.py` — thin JSON-RPC caller, importable:

```python
import sys; sys.path.insert(0, "Tools")
from mono import q
r = q("get_expression_pin_info", {"class_name": "Noise"})
```

CLI form:
```bash
python Tools/mono.py get_expression_pin_info "{\"class_name\":\"Noise\"}"
```

### Two practical warnings

**PowerShell mangles inline JSON.** Escaped quotes get eaten and you get
`JSONDecodeError`. For anything non-trivial, write a small `.py` file that
imports `q` rather than passing JSON on the command line.

**Responses may be SSE.** The endpoint answers either plain JSON or
`data: {...}` lines. Parse both. Payloads arrive wrapped in
`result.content[].text` as a JSON *string* — parse twice.

Minimal transport:

```python
req = urllib.request.Request(
    "http://127.0.0.1:9316/mcp",
    data=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call",
                     "params":{"name":"material_query",
                               "arguments":{"action":A,"params":P}}}).encode(),
    headers={"Content-Type":"application/json",
             "Accept":"application/json, text/event-stream"})
```

---

## 3. Discovery

```bash
python Tools/monolith_probe.py                 # list all 28 tools
python Tools/monolith_probe.py material_query  # one tool's schema
```

`monolith_discover("<namespace>")` enumerates a domain's actions. Pass
`detail=true` for full param schemas.

**There is no `describe_query` action** — that guess returns
`Unknown action: material.describe_query`. Use `monolith_discover`.

### Finding a param name the fast way

Call the action with `{}`. The error names what's missing:

```
Missing required param(s): [class_name]. Provided keys: []
```

That is faster than reading schemas. Note the convention is **`asset_path`** —
not `path`, not `function_path`. A wrong key fails *silently* as an empty
string: `Failed to load asset at ''`.

---

## 4. `material_query` — the actions that matter

### Introspection (read-only, safe)

| action | params | returns |
|---|---|---|
| `get_expression_pin_info` | `class_name` | exact input/output pin names + indices |
| `get_function_info` | `asset_path` | function inputs w/ types, outputs, categories |
| `get_all_expressions` | `asset_path` | every node in a material |
| `get_expression_details` | `asset_path`, expression | one node's properties |
| `get_full_connection_graph` | `asset_path` | every wire — source of `*_connections.json` |
| `get_expression_connections` | `asset_path`, expression | one node's wires |
| `get_material_parameters` | `asset_path` | params, groups, defaults |
| `get_material_properties` | `asset_path` | domain, blend mode, shading model |
| `get_compilation_stats` | `asset_path` | `is_compiled`, instruction counts, samplers |
| `list_expression_classes` | — | every placeable node class |
| `export_material_graph` | `asset_path` | full graph dump |
| `export_function_graph` | `asset_path` | function graph dump |

`get_expression_pin_info` is the single most valuable call here. It is the only
reliable way to learn pin names, and wrong pin names fail silently.

### Validation

| action | notes |
|---|---|
| `validate_material` | finds islands, unused params; reports `severity` / `type` / `expression` |
| `recompile_material` | after edits |
| `render_preview`, `get_thumbnail` | visual confirmation |
| `check_tiling_quality` | texture tiling |
| `audit_orphan_materials` | project-wide |

**Always `validate_material` after authoring.** An unwired input still compiles
clean — islands are the only signal.

### Authoring (mutating)

| action | notes |
|---|---|
| `create_material`, `create_material_instance`, `duplicate_material` | |
| `build_material_graph`, `build_function_graph` | bulk construction |
| `connect_expressions` | `asset_path`, `from_expression`, `from_output`, `to_expression`, `to_input` |
| `set_expression_property`, `move_expression`, `rename_expression` | |
| `disconnect_expression`, `delete_expression`, `delete_expressions`, `clear_graph` | destructive |
| `create_custom_hlsl_node`, `update_custom_hlsl_node` | |
| `set_material_property`, `batch_set_material_property` | |
| `auto_layout` | tidy node positions |
| `save_material`, `batch_recompile` | |
| `begin_transaction` / `end_transaction` | **wrap multi-step edits** |

### Instances

`get_instance_parameters`, `set_instance_parameter`, `set_instance_parameters`,
`clear_instance_parameter`, `set_instance_parent`, `list_material_instances`.

`set_instance_parent` is the scripted route for reparenting work.

### Functions & textures

`create_material_function`, `update_material_function`,
`set_function_metadata`, `delete_function_expression`,
`layout_function_expressions`, `rename_function_parameter_group`,
`create_function_instance`, `set_function_instance_parameter`,
`get_function_instance_info`.

`import_texture`, `get_texture_properties`, `preview_texture`,
`preview_textures`, `create_pbr_material_from_disk`.

---

## 5. Recipes

### Resolve pins before wiring

```python
for c in ["Noise", "Power", "Fresnel", "SubstrateToonBSDF"]:
    r = q("get_expression_pin_info", {"class_name": c})
    print(c, [i["name"] for i in r["inputs"]])
```
See `Tools/node_pins.py`.

### Read a function signature

```python
r = q("get_function_info",
      {"asset_path": "/Game/EnvSandbox/Materials/Functions/MF_NikkiRimGlow"})
for i in r["inputs"]:
    print(i["name"], i["type"])
```
See `Tools/sig_summary.py`. **This is the only way to read MaterialFunction
pins** — `MEL.get_material_expressions` rejects function assets outright.

### Repair island nodes

```python
q("connect_expressions", {
    "asset_path": P,
    "from_expression": "MaterialExpressionWorldPosition_0",
    "from_output": "XYZ",
    "to_expression": "MaterialExpressionMultiply_3",
    "to_input": "A"})
q("recompile_material", {"asset_path": P})
q("save_material", {"asset_path": P})
q("validate_material", {"asset_path": P})   # confirm issue_count == 0
```
See `Tools/fix_petalprism_sparkle.py` — this repaired 4 islands in PetalPrism
caused by two wrong pin names.

### Post-authoring gate

```python
v = q("validate_material", {"asset_path": P})
s = q("get_compilation_stats", {"asset_path": P})
assert v["issue_count"] == 0 and s["is_compiled"]
```
See `Tools/verify_family.py`.

---

## 6. Editor Python vs Monolith

| task | use |
|---|---|
| discover pin names | **Monolith** — only reliable source |
| read MaterialFunction pins | **Monolith** — Python API refuses |
| validate / compile stats | **Monolith** |
| visual preview | **Monolith** `render_preview` |
| build a large graph | either; editor Python is fine with verified pins |
| bulk repetitive edits | **Monolith** + transactions |

Editor Python runs via console (Alt+F11):
```python
exec(open("C:/EnvironmentPortfolio/BS_GodFile/Tools/<script>.py").read())
```
Relative paths do **not** resolve — always absolute.

---

## 7. Editor launch

`Launch_Editor.bat` gates on a git sync check. To bypass deliberately:

```powershell
$env:MELODIA_SKIP_SYNC_CHECK=1
& "C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe" `
    BS_GodFile.uproject -DDC-ForceMemoryCache
```

UE **5.8** is the installed engine. `-run=pythonscript` did not work here;
use the in-editor console instead.

One editor instance, one port 9316. Batch saves with `unattended:true`.
No writes to `Content/_PROJECT/`.

---

## 8. Gotcha ledger

- `asset_path` is the path key — wrong keys fail silently as `''`
- No `describe_query`; use `monolith_discover`
- Empty-params call is the fastest way to learn required params
- Responses may be SSE; payload is JSON-in-a-string inside `content[].text`
- PowerShell destroys inline JSON — use a `.py` wrapper
- Monolith needs the editor running; nothing works otherwise
- Wrap multi-step mutations in `begin_transaction` / `end_transaction`
- `Tools/*` is gitignored here, so these helpers are local-only
