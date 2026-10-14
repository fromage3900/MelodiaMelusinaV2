"""Preview the MEL_bloom_* builders: three growth stages per species, Workbench render to PNG.

  blender --background --python Tools/bloom_preview.py -- [out_dir] [species ...]

Staging only. Used to LOOK at the geometry before baking (Tools/bake_bloom_kit.py).
"""
import importlib.util
import math
import sys
import types
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
GN_DIR = ROOT / "deploy" / "surreal_arch" / "melodia_gn"
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = (Path(args[0]).resolve() if args else ROOT / "Saved" / "Staging" / "MelusinaBlooms" / "preview")
SPECIES = args[1:] or ["rose", "peony"]
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


for n in ("core", "blooms"):
    _load(n)
blooms = sys.modules["melodia_gn.blooms"]

COLORS = {"vine": [(0.3,0.6,0.3,1)]*3, "petal": [(0.95,0.5,0.6,1)]*3, "rose": [(0.93, 0.36, 0.52, 1), (1.0, 0.82, 0.35, 1), (0.25, 0.55, 0.30, 1)],
          "peony": [(0.98, 0.70, 0.80, 1), (1.0, 0.82, 0.35, 1), (0.25, 0.55, 0.30, 1)]}


def make_mats(sp):
    mats = []
    for i, c in enumerate(COLORS[sp]):
        m = bpy.data.materials.new(f"{sp}_{i}")
        m.diffuse_color = c
        mats.append(m)
    return mats


def build_object(sp, growth, x, seed=1.0):
    tree = (getattr(blooms, "build_bloom_" + sp, None) or getattr(blooms, "build_" + ("vine_melody" if sp == "vine" else sp)))("MEL_" + sp)
    me = bpy.data.meshes.new(f"{sp}_{growth}")
    ob = bpy.data.objects.new(f"{sp}_{growth}", me)
    bpy.context.scene.collection.objects.link(ob)
    for m in make_mats(sp):
        me.materials.append(m)
    tree = tree.copy()   # Blender 5.x: set per-object values on the interface defaults, not modifier id-props
    for it in tree.interface.items_tree:
        if getattr(it, "in_out", "") == "INPUT":
            if it.name == "Growth":
                it.default_value = growth
            elif it.name == "Seed":
                it.default_value = seed
    mod = ob.modifiers.new("GN", "NODES")
    mod.node_group = tree
    ob.location = (x, 0, 0)
    return ob


scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "SINGLE"
scene.display.shading.single_color = (0.95, 0.45, 0.58)
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 1800, 700
scene.render.film_transparent = False
scene.world = bpy.data.worlds.new("w")
scene.world.color = (0.92, 0.90, 0.95)

for sp in SPECIES:
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    span = 0.7 if sp == "vine" else 0.34
    objs = [build_object(sp, g, i * span - span) for i, g in enumerate((0.0, 0.55, 1.0))]
    dg = bpy.context.evaluated_depsgraph_get()
    report = []
    for ob in objs:
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        zs = [v.co.z for v in me.vertices]
        report.append((ob.name, len(me.vertices), sum(len(p.vertices) - 2 for p in me.polygons),
                       round(min(zs), 3) if zs else None, round(max(zs), 3) if zs else None,
                       [a.name for a in me.color_attributes], [u.name for u in me.uv_layers],
                       {k: sum(1 for p in me.polygons if p.material_index == k) for k in range(3)}))
        ev.to_mesh_clear()
    for r in report:
        print("STAGE", sp, r)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 2.6 if sp == "vine" else 0.9
    cam.location = (0, -2.0, 0.9 if sp == "vine" else 0.25)
    cam.rotation_euler = (math.radians(86), 0, 0)
    scene.render.filepath = str(OUT / f"{sp}_side.png")
    bpy.ops.render.render(write_still=True)
    cam.data.ortho_scale = 0.8
    cam.location = (0, -0.55, 0.9)
    cam.rotation_euler = (math.radians(30), 0, 0)
    scene.render.filepath = str(OUT / f"{sp}_top.png")
    bpy.ops.render.render(write_still=True)
print("PREVIEW_DONE", OUT)
