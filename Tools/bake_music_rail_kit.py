"""Bake the sheet-music railing kit from the Melodia Studio GN group MEL_music_sheet_rail.

Run headless (Blender 5.2):
  blender --background --python Tools/bake_music_rail_kit.py -- [out_dir]

Produces modular straight segments (and a clef end cap) as FBX plus bake_report.json. The kit is placed along a walkway
spline by PCGEx (Path Spline Mesh / instancing); no live Houdini needed. Staging only: nothing is written into Content/.
"""
import importlib.util
import json
import os
import sys
import types
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
GN_DIR = ROOT / "deploy" / "surreal_arch" / "melodia_gn"
OUT = Path(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv and len(sys.argv) > sys.argv.index("--") + 1 else ROOT / "Saved" / "Audit" / "PianoRails_20261004"
OUT.mkdir(parents=True, exist_ok=True)

pkg = types.ModuleType("melodia_gn")
pkg.__path__ = [str(GN_DIR)]
sys.modules["melodia_gn"] = pkg
sa = types.ModuleType("surreal_arch")
sa.__path__ = [str(GN_DIR.parent)]
sys.modules["surreal_arch"] = sa


def _load(name):
    spec = importlib.util.spec_from_file_location("melodia_gn." + name, GN_DIR / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["melodia_gn." + name] = mod
    spec.loader.exec_module(mod)
    return mod


# Order matters: music_heroes imports from .core / .profiles / .music
for n in ("core", "math_ops", "primitives", "profiles", "music", "music_heroes"):
    if (GN_DIR / (n + ".py")).exists():
        try:
            _load(n)
        except Exception as exc:  # report, keep going: a missing optional module must not hide the real failure
            print("LOAD-WARN", n, repr(exc))

heroes = sys.modules["melodia_gn.music_heroes"]
group_name = "MEL_music_sheet_rail"
if group_name not in bpy.data.node_groups:
    heroes.build_music_sheet_rail(group_name)
group = bpy.data.node_groups[group_name]
sock = {i.name: i.identifier for i in group.interface.items_tree if getattr(i, "in_out", "") == "INPUT"}
print("INPUTS", sock)

VARIANTS = {
    "RAIL_Straight_2m": dict(Length=2.0, **{"Post Count": 2, "Note Count": 3, "Show Clef": False}),
    "RAIL_Straight_4m": dict(Length=4.0, **{"Post Count": 3, "Note Count": 6, "Show Clef": False}),
    "RAIL_Straight_8m": dict(Length=8.0, **{"Post Count": 5, "Note Count": 12, "Show Clef": False}),
    "RAIL_ClefCap_2m": dict(Length=2.0, **{"Post Count": 2, "Note Count": 3, "Show Clef": True}),
}

report = {"blender": bpy.app.version_string, "source_group": group_name, "variants": {}}
for name, params in VARIANTS.items():
    # Blender 5.x NodesModifier rejects id-property writes from Python; drive the group's interface defaults, and only
    # THEN create the modifier so it picks the defaults up (a modifier made earlier keeps the previous variant's values).
    items = {i.name: i for i in group.interface.items_tree if getattr(i, "in_out", "") == "INPUT"}
    for key, value in list(params.items()) + [("Realize for export", True)]:
        item = items.get(key)
        if item is None:
            print("MISSING INPUT", key)
            continue
        try:
            item.default_value = value
        except Exception as exc:
            print("SET-FAIL", key, repr(value), exc)
    bpy.ops.object.select_all(action="DESELECT")
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    mod = obj.modifiers.new("MEL_music_sheet_rail", "NODES")
    mod.node_group = group
    bpy.context.view_layer.update()
    obj.update_tag()
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    em = ev.to_mesh()
    verts, polys = len(em.vertices), len(em.polygons)
    xs = [v.co.x for v in em.vertices]
    ys = [v.co.y for v in em.vertices]
    zs = [v.co.z for v in em.vertices]
    bounds = [round(min(xs), 3), round(max(xs), 3), round(min(ys), 3), round(max(ys), 3), round(min(zs), 3), round(max(zs), 3)] if xs else None
    ev.to_mesh_clear()
    report["variants"][name] = {"params": params, "verts": verts, "polys": polys, "bounds_m": bounds}
    print("BAKED", name, verts, polys, bounds)
    if verts == 0:
        continue
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.export_scene.fbx(
        filepath=str(OUT / (name + ".fbx")), use_selection=True, object_types={"MESH"},
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS", axis_forward="-Y", axis_up="Z",
        mesh_smooth_type="FACE", add_leaf_bones=False,
    )
    report["variants"][name]["fbx"] = str(OUT / (name + ".fbx"))

(OUT / "bake_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("REPORT", OUT / "bake_report.json")
