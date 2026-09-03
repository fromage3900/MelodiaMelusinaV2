# GN Builder Development Guide

> **Audience:** Technical artists and pipeline engineers extending Melodia Studio's Geometry Nodes stack.
> **Scope:** How to create, register, test, and document GN builders across the three frameworks in this repo.
> **Verified against:** `deploy/surreal_arch/melodia_gn/core.py` (L1–1288), `music.py`, `melodia_gn_route.py`, `Tools/BlenderAddons/blender_kawaii_gn/core/gn_framework.py`, `Tools/BlenderAddons/blender_brutalist_gn/core/gn_framework.py`.

---

## 1. The Three GN Frameworks

This repo ships **three independent Geometry Nodes frameworks**. They do not share a base class or registry. Pick the one that matches the job.

| Framework | Location | Pattern | Registry | Count | Use when |
|-----------|----------|---------|----------|-------|----------|
| **Melodia GN** | `deploy/surreal_arch/melodia_gn/` | Flat `build_*()` functions | `GROUP_BUILDERS` dict via `register_builder()` | 165+ | Musical notation, castle kit, ornament, structures, greybox, effects — anything that ships through `melodia_gn_route.py` into the UE pipeline |
| **Kawaii GN** | `Tools/BlenderAddons/blender_kawaii_gn/` | `KawaiiGNBase` subclass | `KAWAII_GN_REGISTRY` via `@register_generator` | ~25 | Cute/pastel procedural assets (food, plushies, characters, nature) — needs Kindchenschema cuteness driving |
| **Brutalist GN** | `Tools/BlenderAddons/blender_brutalist_gn/` | `BrutalistGNBase` subclass | `BRUTALIST_GN_REGISTRY` via `@register_generator` | ~10 | Raw concrete, monolithic architecture, pilotis, panel walls |

### Key differences

| Concern | Melodia GN | Kawaii GN | Brutalist GN |
|---------|------------|-----------|--------------|
| **Builder shape** | `def build_foo(group_name="MEL_foo"):` | `class FooGN(KawaiiGNBase):` | `class FooGN(BrutalistGNBase):` |
| **Tree creation** | `new_geometry_tree(name)` → `(tree, gin, gout)` | `bpy.data.node_groups.new()` inside `get_node_tree()` | Same as Kawaii |
| **Blender 5.x Geometry OUTPUT** | Handled by `new_geometry_tree()` → `make_group_output()` | `ensure_geometry_interface(tree, with_input=...)` | Relies on Blender default (NodeGroupOutput auto-creates Geometry socket) |
| **Parameter helpers** | `add_float_param()`, `add_int_param()`, `add_bool_param()`, `add_vector_param()` | Manual `tree.interface.new_socket()` | Manual `tree.interface.new_socket()` |
| **Cuteness / Roundness** | ❌ | `ensure_roundness_parameter(tree)` + `apply_scene_cuteness_to_object()` | ❌ |
| **Music influence** | `add_music_influence_params()` + `apply_universal_music_pass()` auto-wired | ❌ | ❌ |
| **Labeling** | `label_tree(tree, title, frames=[...])` + `STUDIO_LABELS` entry | Tree name only | Tree name only |
| **Routing** | `ARCH_TO_GN` map in `melodia_gn_route.py` | UI panel via `list_generators_by_category()` | UI panel via `list_generators_by_category()` |

> **Rule:** Do NOT mix frameworks. A Melodia GN builder is a function; a Kawaii/Brutalist builder is a class. They have different registries, different tree-creation paths, and different Blender 5.x compatibility shims.

---

## 2. Creating a New Melodia GN Builder

### 2.1 File structure

```
deploy/surreal_arch/melodia_gn/
├── core.py              # safe_node, link_sockets, new_geometry_tree, register_builder, STUDIO_LABELS
├── music.py             # build_music_note_head, build_music_treble_clef, ...
├── castle.py            # build_castle_tower, build_castle_keep, ...
├── ornament.py          # build_ornament_vine, ...
├── <your_module>.py     # ← create this
```

One module per domain. Each module imports helpers from `core.py` and calls `register_builder()` at module scope.

### 2.2 The `build_*()` function

Every builder follows this skeleton:

```python
# deploy/surreal_arch/melodia_gn/my_domain.py
from __future__ import annotations
import math
import bpy
from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    label_tree, sweep_profile,
)


def build_my_new_thing(group_name="MEL_my_new_thing"):
    """One-line summary.

    Longer description: what geometry it produces, what attributes it stores,
    and which helper patterns it uses (sweep_profile, store_named_attr, etc.).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    # ── Parameters ─────────────────────────────────────────────
    add_float_param(tree, "Width", 4.0, 0.5, 30.0)
    add_int_param(tree, "Segments", 8, 2, 64)
    add_bool_param(tree, "Realize", False)

    # ── Geometry ────────────────────────────────────────────────
    cube = safe_node(tree, "GeometryNodeMeshCube", (bx - 400, by))
    link_float_to_vector(tree, gin.outputs["Width"], cube, "Size", component=0)

    # ... more nodes ...

    # ── Output (REQUIRED) ───────────────────────────────────────
    # ALWAYS link final geometry to the Group Output Geometry socket.
    link_sockets(tree, final_geom.outputs["Geometry"], gout.inputs["Geometry"])

    # ── Labeling ────────────────────────────────────────────────
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Main", "nodes": ("cube", "transform"), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
```

### 2.3 Registering the builder

At module scope (bottom of file), register into the global catalog:

```python
from .core import register_builder

register_builder(
    "MEL_my_new_thing",          # tree_name — must match group_name default
    build_my_new_thing,          # builder_fn
    "My New Thing",              # label — human-readable
    "Description for tooltip.",  # description
    "structures",                # category — must be in CATEGORY_META or will be uncategorized
    hidden=False,                # True = live but hidden from GN Stack
    role="sku",                  # sku | modifier | tool | factory | pcg_alias | pcg_keep
)
```

> **Important:** `register_builder()` wraps your function in `_labeled_builder` which auto-applies `ensure_labeled_tree()` and `apply_universal_music_pass()`. You do NOT need to call these yourself.

### 2.4 Node tree conventions

| Convention | Rule |
|------------|------|
| **Group naming** | `MEL_<snake_case>` — e.g. `MEL_music_note_head`, `MEL_castle_tower` |
| **Node coordinates** | Use `bx, by` origin + offsets. X increases left→right (input→output). Y separates parallel chains. |
| **Socket access** | Use `sock(node, "Name", "Alt Name", outputs=True)` — never hardcode socket indices. |
| **Float→Vector** | Use `link_float_to_vector(tree, src, target_node, "Scale", component=0)` — handles Blender 5.1 CombineXYZ bridging automatically. |
| **Mesh Boolean** | Use `mesh_boolean_node(tree, loc, "DIFFERENCE", mesh_a, mesh_b)` — handles 5.2 socket renames. |
| **Sweep / rail** | Use `sweep_profile(tree, loc, curve_sock, radius_sock)` — the AAA railing pattern. |
| **Coloring** | Call `color_node(node, "geometry"|"instance"|"math"|"curve"|"attribute"|"input"|"output")` for studio palette. |
| **Frames** | Pass `frames=[...]` to `label_tree()` — groups nodes visually in the editor. |

### 2.5 Blender 5.x compatibility

`core.py` already handles most renames. Rules for builders:

1. **Never hardcode `bl_idname`** — always go through `safe_node()`. It remaps via `NODE_REMAP_52`:
   - `GeometryNodeCube` → `GeometryNodeMeshCube`
   - `GeometryNodeUVSphere` → `GeometryNodeMeshUVSphere`
   - `GeometryNodeSeparateXYZ` → `ShaderNodeSeparateXYZ`
   - `ShaderNodeTime` → `GeometryNodeInputSceneTime`
   - etc.

2. **Never access `vector_socket.inputs[i]`** — Blender 5.1 removed sub-sockets. Use `link_float_to_vector()`.

3. **Never assume `tree.inputs` / `tree.outputs`** — Blender 4.0 removed them. Use `make_group_input()` / `make_group_output()`.

4. **Never assume Geometry OUTPUT exists** — `new_geometry_tree()` calls `make_group_output()` which uses `tree.interface.new_socket()`. Safe.

5. **Torus is gone** — use `add_mesh_torus()` / `add_mesh_torus_linked()` which build it from two curve circles.

6. **Resample Curve COUNT** — use `set_resample_count()` which handles the 5.x mode/offset socket rename.

7. **Version checks** — if you must branch on version, use `bpy.app.version >= (5, 0, 0)`. Prefer `safe_node()` remapping over explicit version checks.

---

## 3. Creating a New Kawaii GN Generator

### 3.1 File structure

```
Tools/BlenderAddons/blender_kawaii_gn/
├── core/
│   ├── gn_framework.py    # KawaiiGNBase, register_generator, KAWAII_GN_REGISTRY
│   └── node_builder.py    # link_from_input, kindchenschema_from_input, link_cube_size
├── generators/
│   ├── kawaii_architecture.py
│   ├── kawaii_characters.py
│   └── <your_generator>.py   # ← create this
```

### 3.2 The `KawaiiGNBase` subclass

```python
# Tools/BlenderAddons/blender_kawaii_gn/generators/my_kawaii.py
import bpy
from ..core.gn_framework import KawaiiGNBase, register_generator, get_input_socket
from ..core.node_builder import link_from_input, kindchenschema_from_input


@register_generator
class KawaiiMyAssetGN(KawaiiGNBase):
    """Docstring — appears in UI tooltip."""
    
    category = "architecture"           # groups in panel
    generator_id = "kawaii_my_asset_gn" # unique key in KAWAII_GN_REGISTRY
    generator_name = "My Kawaii Asset"  # human name + tree name prefix
    description = "Cute pastel thing"   # tooltip
    uses_input_geometry = False          # True = expose Geometry input socket
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        """Add custom input sockets."""
        tree.interface.new_socket('Width', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Height', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Roundness', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Width': socket.default_value = 2.0
            elif socket.name == 'Height': socket.default_value = 1.0
            elif socket.name == 'Roundness': socket.default_value = 0.7
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        """Build the actual geometry."""
        nodes = tree.nodes
        links = tree.links
        
        # Access input sockets via get_input_socket (Blender 4.2-5.1 safe)
        width_sock = get_input_socket(input_node, 'Width')
        
        cube = nodes.new('GeometryNodeMeshCube')
        cube.location = (-200, 0)
        links.new(width_sock, cube.inputs['Size'].sockets[0])
        
        # Link to output
        links.new(cube.outputs['Mesh'], output_node.inputs['Geometry'])
```

### 3.3 How it works

- `@register_generator` adds the class to `KAWAII_GN_REGISTRY[cls.generator_id]`.
- `get_node_tree()` creates `Kawaii GN - {generator_name}` tree, calls `build_node_tree()` which calls `ensure_geometry_interface()` (Blender 5.x safe), then `add_parameters()` + `build_geometry()`.
- `ensure_roundness_parameter(tree)` is auto-called — every Kawaii tree exposes `Roundness` for scene cuteness driving.
- `create_object()` / `apply_to_object()` attach the tree as a `NODES` modifier.

### 3.4 Parameters

- Use `tree.interface.new_socket(name, in_out='INPUT', socket_type=...)` — Blender 4+ interface API.
- Set `socket.default_value` after creation.
- Common types: `NodeSocketFloat`, `NodeSocketInt`, `NodeSocketBool`, `NodeSocketVector`, `NodeSocketGeometry`.

---

## 4. Creating a New Brutalist GN Generator

### 4.1 File structure

```
Tools/BlenderAddons/blender_brutalist_gn/
├── core/
│   ├── gn_framework.py    # BrutalistGNBase, register_generator, BRUTALIST_GN_REGISTRY
│   └── operators.py
├── generators/
│   ├── walls.py
│   ├── structures.py
│   ├── details.py
│   ├── complexes.py
│   └── <your_generator>.py   # ← create this
```

### 4.2 The `BrutalistGNBase` subclass

```python
# Tools/BlenderAddons/blender_brutalist_gn/generators/my_brutalist.py
import bpy
from ..core.gn_framework import BrutalistGNBase, register_generator


@register_generator
class BrutalistMyStructureGN(BrutalistGNBase):
    """Docstring."""
    
    category = "structures"
    generator_id = "brutalist_my_structure_gn"
    generator_name = "My Brutalist Structure"
    description = "Raw concrete thing"
    
    @classmethod
    def add_parameters(cls, tree, input_node, output_node):
        tree.interface.new_socket('Width', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Height', in_out='INPUT', socket_type='NodeSocketFloat')
        tree.interface.new_socket('Thickness', in_out='INPUT', socket_type='NodeSocketFloat')
        
        for socket in tree.interface.items_tree:
            if socket.name == 'Width': socket.default_value = 6.0
            elif socket.name == 'Height': socket.default_value = 4.0
            elif socket.name == 'Thickness': socket.default_value = 0.3
    
    @classmethod
    def build_geometry(cls, tree, input_node, output_node):
        nodes = tree.nodes
        links = tree.links
        
        wall = nodes.new('GeometryNodeMeshCube')
        wall.location = (-400, 0)
        wall.inputs['Size'].default_value = (6.0, 0.3, 4.0)
        links.new(input_node.outputs['Width'], wall.inputs['Size'].sockets[0])
        links.new(input_node.outputs['Thickness'], wall.inputs['Size'].sockets[1])
        links.new(input_node.outputs['Height'], wall.inputs['Size'].sockets[2])
        
        links.new(wall.outputs['Mesh'], output_node.inputs['Geometry'])
```

### 4.3 Brutalist vs Kawaii differences

- No `ensure_geometry_interface()` call — relies on Blender's default NodeGroupOutput having a Geometry socket.
- No `ensure_roundness_parameter()` — no cuteness driving.
- No `uses_input_geometry` flag — simpler pattern.
- Tree name: `Brutalist GN - {generator_name}`.

---

## 5. Registering a Builder in `melodia_gn_route.py`

This section applies **only to Melodia GN builders** that need to be reachable from the UE pipeline via `try_apply_melodia_gn()`.

### 5.1 The `ARCH_TO_GN` map

```python
# deploy/surreal_arch/melodia_gn_route.py
ARCH_TO_GN = {
    "GAZEBO": ("structures.build_gazebo", "MEL_gazebo"),
    "ARCH": ("structures.build_arch", "MEL_arch"),
    "MELODIA_NOTE_HEAD": ("music.build_music_note_head", "MEL_music_note_head"),
    # ← add your entry:
    "MY_NEW_THING": ("my_domain.build_my_new_thing", "MEL_my_new_thing"),
}
```

Format: `"ARCH_TYPE": ("dotted.module.path.build_fn", "MEL_group_name")`

The dotted path is resolved by `_resolve_builder()`:
```python
mod_name, fn_name = dotted.rsplit(".", 1)
mod = __import__(f"surreal_arch.melodia_gn.{mod_name}", fromlist=[fn_name])
return getattr(mod, fn_name)
```

### 5.2 The `STUDIO_LABELS` entry

Add to `STUDIO_LABELS` in `core.py` for UI display:

```python
"MY_NEW_THING": {
    "ui_label": "My New Thing",
    "mel_tree": "MEL_my_new_thing",
    "category": "Structures",
    "panel_hint": "Short description for tooltip.",
},
```

### 5.3 Collection routing

`_collection_for_arch_type()` auto-assigns objects to collections based on `arch_type` prefix:

| Prefix | Collection |
|--------|------------|
| `MELODIA_`, `MUSIC_`, `NOTE_HEAD`, `TREBLE_CLEF`, `SHEET_MUSIC_RAIL` | `MusicalGN_Editable` |
| `NIKKI_`, `SKY_` | `NikkiGN_Editable` |
| `ESCHER_` | `EscherGN_Editable` |
| `ORN_`, `CASTLE_`, `ARCH`, `GAZEBO`, `PORTICO` | `OrnamentGN_Editable` |

If your arch_type doesn't match a prefix, returns `None` (no collection assignment). Add a new prefix branch if needed.

### 5.4 Routing decision

`should_use_melodia_gn(arch_type, prefer=True)` returns `True` when:
- `arch_type in ARCH_TO_GN`, OR
- `arch_type.startswith(("MELODIA_", "ORN_", "MUSIC_", "CASTLE_", "NIKKI_", "ESCHER_"))`

`try_apply_melodia_gn(obj, props, monolith)` is the entry point — it resolves the builder, creates the tree, attaches a `MelodiaGN` modifier, binds music props, and assigns the object to the right collection.

---

## 6. Testing a Builder

### 6.1 Offline import check

```bash
python Tools/gn_health_check.py
```

What it does:
- Scans all GN paths (`Melodia GN`, `Kawaii GN`, `Brutalist GN`, etc.)
- Counts `.py` modules
- Tries to import each package `__init__.py`
- Detects `KAWAII_GN_REGISTRY`, `BRUTALIST_GN_REGISTRY`, `MELODIA_GN_REGISTRY`
- Writes `Saved/Audit/gn_health_report_YYYY-MM-DD.json`

**No Blender required.** Catches syntax errors, missing imports, broken registrations.

### 6.2 In-Blender test

```bash
# Run inside Blender's Python (or via blender --python):
python Tools/gn_health_check.py --live
```

What it adds:
- Actually creates each node tree via `bpy.data.node_groups.new()`
- Verifies Geometry OUTPUT socket exists
- Catches runtime errors in `build_*()` / `build_geometry()`

### 6.3 GN health check (manual in Blender)

```python
# In Blender Python console:
import surreal_arch.melodia_gn as mg
mg.build_music_note_head()  # replace with your builder
# Check the node tree appears in bpy.data.node_groups
```

### 6.4 Per-framework verification

| Framework | Import test | Tree test | Registry test |
|-----------|-------------|-----------|---------------|
| Melodia GN | `from surreal_arch.melodia_gn.music import build_music_note_head` | `build_music_note_head()` → tree in `bpy.data.node_groups` | `"MEL_music_note_head" in GROUP_BUILDERS` |
| Kawaii GN | `from blender_kawaii_gn.generators.kawaii_architecture import KawaiiBricksGN` | `KawaiiBricksGN.get_node_tree()` | `"kawaii_bricks_gn" in KAWAII_GN_REGISTRY` |
| Brutalist GN | `from blender_brutalist_gn.generators.walls import BrutalistConcreteWallGN` | `BrutalistConcreteWallGN.get_node_tree()` | `"brutalist_concrete_wall_gn" in BRUTALIST_GN_REGISTRY` |

### 6.5 Regression testing

```bash
# Fingerprint comparison (after bake):
python Tools/bp_regression_checker.py
```

---

## 7. Common Pitfalls

### 7.1 Missing Geometry OUTPUT socket

**Symptom:** Tree builds but produces no geometry / modifier shows empty output.

**Cause:** Blender 5.x does NOT auto-create Geometry OUTPUT on `bpy.data.node_groups.new()`.

**Fix:**
- Melodia GN: use `new_geometry_tree()` — it calls `make_group_output()`.
- Kawaii GN: `build_node_tree()` calls `ensure_geometry_interface()`.
- Brutalist GN: relies on default — if broken, add `ensure_geometry_interface(tree)` call.

**Verify:**
```python
def tree_has_geometry_output(tree):
    for item in tree.interface.items_tree:
        if item.in_out == 'OUTPUT' and item.name == 'Geometry':
            return True
    return False
```

### 7.2 Blender 5.x node name changes

**Symptom:** `safe_node()` logs `WARNING: 'GeometryNodeCube' not available`.

**Cause:** Node was renamed in 5.x.

**Fix:** Always use `safe_node()` — it remaps via `NODE_REMAP_52`. If a node is missing from the map, add it to `NODE_REMAP_52` in `core.py`:

```python
NODE_REMAP_52 = {
    "GeometryNodeCube": "GeometryNodeMeshCube",
    # ... add new remaps here
}
```

### 7.3 `bpy.app.version` checks

**Symptom:** Builder works in 4.x but breaks in 5.x (or vice versa).

**Anti-pattern:**
```python
if bpy.app.version >= (5, 0, 0):
    # do 5.x thing
else:
    # do 4.x thing
```

**Prefer:** Use the compat helpers that already handle the branch:
- `safe_node()` — remaps bl_idname
- `link_float_to_vector()` — bridges CombineXYZ for removed vector sub-sockets
- `make_group_input()` / `make_group_output()` — uses `tree.interface` with legacy fallback
- `set_resample_count()` — handles ResampleCurve socket renames

Only use explicit `bpy.app.version` checks when no helper exists.

### 7.4 Forgetting to link to Group Output

**Symptom:** Tree builds, all nodes present, but output is empty.

**Fix:** Every builder MUST end with:
```python
link_sockets(tree, final_geometry, gout.inputs["Geometry"])
```

For class-based frameworks (Kawaii/Brutalist):
```python
links.new(final_geometry, output_node.inputs['Geometry'])
```

### 7.5 Vector socket sub-sockets removed in 5.1

**Symptom:** `cube.inputs['Size'].sockets[0]` throws `AttributeError`.

**Cause:** Blender 5.1 removed `.sockets` / sub-sockets from vector inputs.

**Fix:** Use `link_float_to_vector(tree, src, target_node, "Size", component=0)` — it creates a CombineXYZ bridge automatically.

### 7.6 NodeFrame parenting errors

**Symptom:** `label_tree()` throws when assigning `node.parent = frame`.

**Fix:** `label_tree()` already wraps this in try/except. If you manually parent nodes, do the same.

### 7.7 Stale registry entries after rename

**Symptom:** `GROUP_METADATA` has entries for builders that no longer exist.

**Fix:** Call `purge_stale_builders()` before `_rebuild_derived_data()`. Already handled in `__init__.py`.

### 7.8 Melodia GN: forgetting `register_builder()`

**Symptom:** Builder function exists but doesn't appear in GN Stack panel.

**Fix:** You must call `register_builder()` at module scope. Importing the module (via `__init__.py`) triggers it.

---

## 8. How to Document a Builder

### 8.1 Docstring

Every `build_*()` function and every generator class gets a docstring:

```python
def build_music_note_head(group_name="MEL_music_note_head"):
    """Elliptical note head with optional stem and flag.

    Stores 'pitch', 'duration', 'velocity' attributes for downstream reads.
    Uses: power_scale (flag curvature), store_attribute (pitch/duration/velocity),
          bounding_box (auto-scale to staff lines)
    """
```

Format:
- **Line 1:** One-line summary.
- **Line 2:** Blank.
- **Body:** What it produces, what attributes it stores, which helper patterns it uses.

### 8.2 Parameters

Document parameters in the docstring or as comments:

```python
add_float_param(tree, "Width", 4.0, 0.5, 30.0)   # wall length in meters
add_int_param(tree, "Segments", 8, 2, 64)         # radial resolution
add_bool_param(tree, "Realize", False)            # realize instances for export
```

### 8.3 `STUDIO_LABELS` entry

```python
"MELODIA_NOTE_HEAD": {
    "ui_label": "Note Head",
    "mel_tree": "MEL_music_note_head",
    "category": "Musical Notation",
    "panel_hint": "GN Stack note-head primitive.",
},
```

- `ui_label`: Short name for panel buttons.
- `mel_tree`: Must match the `MEL_` group name.
- `category`: GN Stack section.
- `panel_hint`: Tooltip text (1-2 lines max).

### 8.4 Frame labels

Use `label_tree()` frames to create visual sections in the node editor:

```python
return label_tree(tree, "MEL_music_note_head", [
    {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
    {"title": "Note Head", "nodes": ("sphere", "transform", "scale"), "role": "geometry"},
    {"title": "Stem And Flag", "nodes": ("stem", "flag", "switch"), "role": "instance"},
    {"title": "Attributes", "nodes": ("store", "pitch", "duration", "velocity"), "role": "attribute"},
    {"title": "Output", "nodes": ("shade", "Group Output"), "role": "output"},
])
```

`role` controls color: `input` (blue), `output` (red), `geometry` (green), `instance` (yellow), `math` (purple), `curve` (teal), `attribute` (sage).

### 8.5 Examples

For complex builders, add a usage example in the module docstring or a `README.md`:

```python
"""
Example:
    >>> from surreal_arch.melodia_gn.music import build_music_note_head
    >>> tree = build_music_note_head()
    >>> tree.name
    'MEL_music_note_head'
"""
```

### 8.6 Changelog entry

When adding a new builder, add a line to `deploy/SURREAL_ARCH_CHANGELOG.md`:

```
## v2.XXX.0 — <feature description>
- **`MEL_my_new_thing`** builder — one-line description.
```

---

## Quick Reference: Which Framework Do I Use?

```
Is it shipping to UE via melodia_gn_route.py?
├── YES → Melodia GN (flat build_*() function)
└── NO → Is it cute/pastel/kawaii?
    ├── YES → Kawaii GN (KawaiiGNBase subclass)
    └── NO → Is it raw concrete/monolithic?
        ├── YES → Brutalist GN (BrutalistGNBase subclass)
        └── NO → Melodia GN (default for studio work)
```

---

## File Map

| File | Purpose |
|------|---------|
| `deploy/surreal_arch/melodia_gn/core.py` | Core helpers: `safe_node`, `link_sockets`, `new_geometry_tree`, `register_builder`, `STUDIO_LABELS`, `NODE_REMAP_52` |
| `deploy/surreal_arch/melodia_gn/music.py` | Musical notation builders (note head, treble clef, staff, harmonic, phrase) |
| `deploy/surreal_arch/melodia_gn/castle.py` | Castle kit builders (tower, keep, gatehouse, crenellation, etc.) |
| `deploy/surreal_arch/melodia_gn/__init__.py` | Imports all builder modules, calls `_rebuild_derived_data()` |
| `deploy/surreal_arch/melodia_gn_route.py` | `ARCH_TO_GN` map, `try_apply_melodia_gn()`, collection routing |
| `Tools/BlenderAddons/blender_kawaii_gn/core/gn_framework.py` | `KawaiiGNBase`, `register_generator`, `KAWAII_GN_REGISTRY`, `ensure_geometry_interface` |
| `Tools/BlenderAddons/blender_brutalist_gn/core/gn_framework.py` | `BrutalistGNBase`, `register_generator`, `BRUTALIST_GN_REGISTRY` |
| `Tools/gn_health_check.py` | Offline + live GN health verification |
