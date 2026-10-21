"""Bake the Resonant Blooms into game-ready FBX stages (Bud / Half / Full x seeds, vines, petals).

  blender --background --python Tools/bake_bloom_kit.py -- [out_dir]

Writes <out_dir>/SM_*.fbx + bake_report.json. Meshes are true size (metres -> 1 uu = 1 cm on import), 3 material slots
named Petal / Accent / Stem, UV0 per petal (u across, v along), colour attribute GrowthCol (R open-time, G whorl,
B radius 0..1) - colour attributes and UV maps survive FBX, custom float attributes do not.
Staging only: nothing is written into Content/.
"""
import importlib.util
import json
import sys
import types
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
GN_DIR = ROOT / "deploy" / "surreal_arch" / "melodia_gn"
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = Path(args[0]).resolve() if args else ROOT / "Saved" / "Staging" / "MelusinaBlooms" / "bake"
OUT.mkdir(parents=True, exist_ok=True)

pkg = types.ModuleType("melodia_gn")
pkg.__path__ = [str(GN_DIR)]
sys.modules["melodia_gn"] = pkg
spec = importlib.util.spec_from_file_location("melodia_gn.blooms", GN_DIR / "blooms.py")
blooms = importlib.util.module_from_spec(spec)
sys.modules["melodia_gn.blooms"] = blooms
spec.loader.exec_module(blooms)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)

MATS = {n: bpy.data.materials.new(n) for n in ("Petal", "Accent", "Stem")}

STAGES = (("Bud", 0.0), ("Half", 0.55), ("Full", 1.0))
JOBS = []
for sp, fn in (("Rose", blooms.build_bloom_rose), ("Peony", blooms.build_bloom_peony)):
    for stage, g in STAGES:
        for seed in (1.0, 2.0, 3.0):
            JOBS.append((f"SM_Bloom_{sp}_{stage}_s{int(seed)}", fn, {"Growth": g, "Seed": seed}))
for stage, g in (("Half", 0.5), ("Full", 1.0)):
    JOBS.append((f"SM_Bloom_Vine_{stage}", blooms.build_vine_melody, {"Growth": g, "Seed": 2.0}))
for k, (ln, wd, rf) in enumerate(((0.075, 1.2, 0.02), (0.060, 1.45, 0.03), (0.090, 1.0, 0.015), (0.070, 0.9, 0.05))):
    JOBS.append((f"SM_Bloom_Petal_{'ABCD'[k]}", blooms.build_petal, {"Growth": 1.0, "Seed": float(k + 1), "Length": ln, "Width": wd, "Ruffle": rf}))

report = {"blender": bpy.app.version_string, "meshes": {}}
for name, fn, values in JOBS:
    tree = fn("tmp_" + name)
    for it in tree.interface.items_tree:
        if getattr(it, "in_out", "") != "INPUT":
            continue
        if it.name in values:
            it.default_value = values[it.name]
        elif it.name == "Petal Material":
            it.default_value = MATS["Petal"]
        elif it.name == "Accent Material":
            it.default_value = MATS["Accent"]
        elif it.name == "Stem Material":
            it.default_value = MATS["Stem"]
    src = bpy.data.objects.new("src", bpy.data.meshes.new("src"))
    bpy.context.scene.collection.objects.link(src)
    src.modifiers.new("GN", "NODES").node_group = tree
    ev = src.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = bpy.data.meshes.new_from_object(ev)
    me.name = name
    bpy.data.objects.remove(src)
    if not any(me.materials):                                  # petal-only group has no Set Material: give it the petal slot
        me.materials.clear()
        me.materials.append(MATS["Petal"])
    old_idx = [p.material_index for p in me.polygons]            # drop empty slots (GN leaves a null slot 0)
    used = sorted(set(old_idx))
    keep = [me.materials[i] for i in used]
    remap = {old: new for new, old in enumerate(used)}
    me.materials.clear()                                         # clear() zeroes every face index, so assign AFTER
    for m in keep:
        me.materials.append(m)
    for p, oi in zip(me.polygons, old_idx):
        p.material_index = remap[oi]
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    xs, ys, zs = [v.co.x for v in me.vertices], [v.co.y for v in me.vertices], [v.co.z for v in me.vertices]
    report["meshes"][name] = {
        "verts": len(me.vertices), "tris": sum(len(p.vertices) - 2 for p in me.polygons),
        "bounds_cm": {"x": [round(min(xs) * 100, 1), round(max(xs) * 100, 1)], "y": [round(min(ys) * 100, 1), round(max(ys) * 100, 1)],
                      "z": [round(min(zs) * 100, 1), round(max(zs) * 100, 1)]},
        "slots": [m.name if m else None for m in me.materials],
        "faces_per_slot": {str(k): sum(1 for p in me.polygons if p.material_index == k) for k in range(len(me.materials))},
        "colour_attrs": [a.name for a in me.color_attributes], "uv_layers": [u.name for u in me.uv_layers],
    }
    bpy.ops.export_scene.fbx(filepath=str(OUT / (name + ".fbx")), use_selection=True, object_types={"MESH"},
                             apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS", axis_forward="-Y", axis_up="Z",
                             mesh_smooth_type="FACE", add_leaf_bones=False)
    print("BAKED", name, report["meshes"][name]["tris"], report["meshes"][name]["slots"])
    bpy.data.objects.remove(ob)
(OUT / "bake_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("REPORT", OUT / "bake_report.json", len(JOBS), "meshes")
