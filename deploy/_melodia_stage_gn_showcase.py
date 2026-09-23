"""Stage the GN showcase: every builder from the Paris + Brutalist lanes in one
.blend, organized into collections, each object carrying a LIVE geometry-nodes
modifier (so the dials stay editable in the file).

Usage:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
      --background --factory-startup --python deploy/_melodia_stage_gn_showcase.py

Outputs:
  Saved/Blend/MELODIA_GN_SHOWCASE_2026-09-23.blend   (the staged file)
  Saved/Audit/gn_showcase_manifest.json              (collection -> object -> builder)
  Saved/Audit/gn_showcase_overview.png               (verification render)

Collection tree:
  MELODIA_GN_SHOWCASE
    01_MAISON_IMPOSSIBLE
      MI_EscherLadder / MI_FountainLoop / MI_DayNightFacade /
      MI_Mansard / MI_PenroseArch / MI_MetamorphosisFrieze
    02_BRUTALIST
      BR_OfficeBlock / BR_CubicleFarm
"""
import json
import math
import os
import sys

DEPLOY = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(DEPLOY)
sys.path.insert(0, DEPLOY)
sys.path.append(os.path.join(os.environ["APPDATA"], "Blender Foundation",
                             "Blender", "5.2", "scripts", "addons"))

import bpy  # noqa: E402
from surreal_arch.melodia_gn import core  # noqa: E402
from surreal_arch.melodia_gn import (  # noqa: E402,F401
    paris_escher_ladder, paris_fountain_loop, paris_daynight_facade,
    paris_mansard, paris_penrose_arch, paris_metamorphosis_frieze,
    brutalist_office, brutalist_cubicles,
)
from surreal_arch.melodia_gn.presets import BUILDERS_PRESETS  # noqa: E402

STAMP = "2026-09-23"
BLEND_PATH = os.path.join(REPO, "Saved", "Blend",
                          f"MELODIA_GN_SHOWCASE_{STAMP}.blend")
MANIFEST_PATH = os.path.join(REPO, "Saved", "Audit",
                             "gn_showcase_manifest.json")
OVERVIEW_PATH = os.path.join(REPO, "Saved", "Audit",
                             "gn_showcase_overview.png")

# (builder id, collection, stage object name, preset, position)
LAYOUT = (
    ("GN_PARIS_EscherLadder", "MI_EscherLadder", "STAGE_EscherLadder",
     None, (-44.0, 0.0)),
    ("GN_PARIS_FountainLoop", "MI_FountainLoop", "STAGE_FountainLoop",
     None, (-26.0, 0.0)),
    ("GN_PARIS_DayNightFacade", "MI_DayNightFacade", "STAGE_DayNightFacade",
     "MI_CREPUSCULE", (-2.0, 0.0)),
    ("GN_PARIS_Mansard", "MI_Mansard", "STAGE_Mansard",
     None, (19.0, 0.0)),
    ("GN_PARIS_PenroseArch", "MI_PenroseArch", "STAGE_PenroseArch",
     "MI_ARCH_TRIBAR", (36.0, 0.0)),
    ("GN_PARIS_MetamorphosisFrieze", "MI_MetamorphosisFrieze",
     "STAGE_MetamorphosisFrieze", "MI_MORPH_SEAM", (50.0, 0.0)),
    ("GN_BRUTALIST_OfficeBlock", "BR_OfficeBlock", "STAGE_OfficeBlock",
     "BR_OFFICE_CIVIC", (-18.0, -30.0)),
    ("GN_BRUTALIST_CubicleFarm", "BR_CubicleFarm", "STAGE_CubicleFarm",
     "BR_CUBICLE_CANON", (12.0, -30.0)),
)


def set_param(tree, name, value):
    for item in tree.interface.items_tree:
        if (getattr(item, "name", "") == name
                and getattr(item, "in_out", "") == "INPUT"):
            try:
                item.default_value = value
                return True
            except Exception:
                return False
    return False


def eval_stats(ob):
    deps = bpy.context.evaluated_depsgraph_get()
    deps.update()
    ev = ob.evaluated_get(deps)
    m = ev.to_mesh()
    verts = len(m.vertices)
    lo = hi = None
    if verts:
        xs = [v.co for v in m.vertices]
        lo = tuple(min(c[i] for c in xs) for i in range(3))
        hi = tuple(max(c[i] for c in xs) for i in range(3))
    ev.to_mesh_clear()
    return verts, lo, hi


def ensure_collection(name, parent):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        parent.children.link(coll)
    return coll


# ---- scene reset ---------------------------------------------------------
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for coll in list(bpy.data.collections):
    bpy.data.collections.remove(coll)

root = ensure_collection("MELODIA_GN_SHOWCASE", bpy.context.scene.collection)
fam_maison = ensure_collection("01_MAISON_IMPOSSIBLE", root)
fam_brut = ensure_collection("02_BRUTALIST", root)

manifest = {"stamp": STAMP, "blend": BLEND_PATH, "collections": {}}
all_lo = [1e9, 1e9, 1e9]
all_hi = [-1e9, -1e9, -1e9]

for bid, coll_name, ob_name, preset, (px, py) in LAYOUT:
    if bid not in core.GROUP_BUILDERS:
        print(f"[stage] MISSING builder {bid} - skipped")
        continue
    res = core.GROUP_BUILDERS[bid]()
    tree = res[0] if isinstance(res, (tuple, list)) else res
    if preset:
        params = BUILDERS_PRESETS.get(bid, {}).get("presets", {}).get(preset)
        if params is None:
            print(f"[stage] WARNING: preset {preset} not found for {bid}")
        else:
            missing = [n for n, v in params.items() if not set_param(tree, n, v)]
            print(f"[stage] preset {bid}/{preset} applied"
                  + (f" MISSING={missing}" if missing else ""))
    parent = fam_maison if coll_name.startswith("MI_") else fam_brut
    coll = ensure_collection(coll_name, parent)
    me = bpy.data.meshes.new(ob_name + "_mesh")
    ob = bpy.data.objects.new(ob_name, me)
    coll.objects.link(ob)
    ob.location = (px, py, 0.0)
    mod = ob.modifiers.new("GN", "NODES")
    mod.node_group = tree
    verts, lo, hi = eval_stats(ob)
    n_params = sum(1 for it in tree.interface.items_tree
                   if getattr(it, "in_out", "") == "INPUT")
    manifest["collections"].setdefault(coll_name, []).append({
        "object": ob_name, "builder": bid, "preset": preset,
        "nodes": len(tree.nodes), "params": n_params, "verts": verts,
        "position": [px, py, 0.0],
    })
    print(f"[stage] {coll_name:26s} {ob_name:26s} {verts:6d}v "
          f"nodes={len(tree.nodes):4d} params={n_params}")
    for i in range(3):
        if lo is not None:
            all_lo[i] = min(all_lo[i], lo[i] + (px, py, 0)[i])
            all_hi[i] = max(all_hi[i], hi[i] + (px, py, 0)[i])

# ---- lights + camera for the verification render -------------------------
sun_data = bpy.data.lights.new("SUN", type='SUN')
sun_data.energy = 3.5
sun_data.angle = 0.35
sun = bpy.data.objects.new("SUN", sun_data)
bpy.context.scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(52.0), math.radians(-14.0),
                      math.radians(35.0))

world = bpy.data.worlds.new("StageWorld")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.045, 0.05, 0.06, 1.0)
    bg.inputs[1].default_value = 0.9
bpy.context.scene.world = world

cam_data = bpy.data.cameras.new("STAGE_CAM")
cam_data.lens = 42.0
cam = bpy.data.objects.new("STAGE_CAM", cam_data)
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam

from mathutils import Vector  # noqa: E402

center = Vector(((all_lo[0] + all_hi[0]) * 0.5,
                 (all_lo[1] + all_hi[1]) * 0.5,
                 (all_lo[2] + all_hi[2]) * 0.5))
radius = max((Vector(all_hi) - Vector(all_lo)).length * 0.5, 0.5)
elev = 0.36
azim = math.radians(265.0)
d = Vector((math.cos(elev) * math.cos(azim),
            math.cos(elev) * math.sin(azim),
            math.sin(elev)))
cam.location = center + d * radius * 0.92
look = (center - cam.location).normalized()
cam.rotation_euler = look.to_track_quat('-Z', 'Y').to_euler()

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
try:
    scene.eevee.taa_render_samples = 24
except Exception:
    pass
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.filepath = OVERVIEW_PATH
scene.render.image_settings.file_format = 'PNG'
scene.frame_set(scene.frame_current + 1)
bpy.ops.render.render(write_still=True)
print(f"[stage] overview rendered -> {OVERVIEW_PATH}")

# ---- save the blend ------------------------------------------------------
os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print(f"[stage] blend saved -> {BLEND_PATH}")

manifest["bounds"] = {"min": all_lo, "max": all_hi}
with open(MANIFEST_PATH, "w", encoding="utf-8") as fh:
    json.dump(manifest, fh, indent=2)
print(f"[stage] manifest -> {MANIFEST_PATH}")
print("[stage] DONE")
