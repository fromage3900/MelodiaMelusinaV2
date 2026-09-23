"""Headless preview renders for the Track A PARIS builders (2026-09-22).

Renders each builder (defaults + one Maison preset) from a framed 3/4 camera
into Saved/Audit/paris_trackA_previews/.  Evidence only: the committed script
produced them, the scene is generated fresh, nothing is saved back.

Run:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
      --background --factory-startup --python deploy/_melodia_render_paris_previews.py
"""
import math
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO, "deploy"))
sys.path.append(os.path.join(os.environ["APPDATA"], "Blender Foundation",
                             "Blender", "5.2", "scripts", "addons"))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from surreal_arch.melodia_gn import core  # noqa: E402
from surreal_arch.melodia_gn import paris_fountain_loop  # noqa: E402,F401
from surreal_arch.melodia_gn import paris_daynight_facade  # noqa: E402,F401
from surreal_arch.melodia_gn import paris_mansard  # noqa: E402,F401
from surreal_arch.melodia_gn import paris_penrose_arch  # noqa: E402,F401
from surreal_arch.melodia_gn import paris_metamorphosis_frieze  # noqa: E402,F401
from surreal_arch.melodia_gn import brutalist_office  # noqa: E402,F401
from surreal_arch.melodia_gn import brutalist_cubicles  # noqa: E402,F401

OUT = os.path.join(REPO, "Saved", "Audit", "paris_trackA_previews")
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.resolution_x = 720
scene.render.resolution_y = 540
scene.render.image_settings.file_format = 'PNG'
try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except Exception:
    scene.render.engine = 'BLENDER_WORKBENCH'
try:
    scene.eevee.taa_render_samples = 48
except Exception:
    pass

world = bpy.data.worlds.new("PreviewWorld")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.27, 0.29, 0.33, 1.0)
    bg.inputs[1].default_value = 1.0

# ground plane so composition is grounded
gm = bpy.data.meshes.new("ground")
gob = bpy.data.objects.new("ground", gm)
scene.collection.objects.link(gob)
gm.from_pydata([(-40, -40, 0), (40, -40, 0), (40, 40, 0), (-40, 40, 0)],
               [], [(0, 1, 2, 3)])
gm.update()

cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 50
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

sun_data = bpy.data.lights.new("sun", 'SUN')
sun_data.energy = 4.0
sun = bpy.data.objects.new("sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(52.0), 0.0, math.radians(35.0))

fill_data = bpy.data.lights.new("fill", 'SUN')
fill_data.energy = 1.2
fill = bpy.data.objects.new("fill", fill_data)
scene.collection.objects.link(fill)
fill.rotation_euler = (math.radians(65.0), 0.0, math.radians(-140.0))


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


def apply_preset(tree, builder, preset):
    from surreal_arch.melodia_gn.presets import BUILDERS_PRESETS
    params = BUILDERS_PRESETS[builder]["presets"][preset]
    missing = []
    for name, value in params.items():
        if not set_param(tree, name, value):
            missing.append(name)
    print(f"[previews] applied preset {builder}/{preset}; missing={missing}")


def build(builder):
    core.reset_link_failures()
    res = core.GROUP_BUILDERS[builder]()
    tree = res[0] if isinstance(res, (tuple, list)) else res
    me = bpy.data.meshes.new(builder + "_m")
    ob = bpy.data.objects.new(builder, me)
    scene.collection.objects.link(ob)
    refresh_mod(ob, tree)
    return ob, tree


def refresh_mod(ob, tree):
    """Re-create the NODES modifier.

    A modifier FREEZES the tree's interface values when node_group is
    assigned - changing interface defaults afterwards never reaches an
    existing modifier (the classic "audio-reactive reads as silence forever"
    trap).  After applying a preset, the modifier must be re-created.
    """
    mod = ob.modifiers.get("gn")
    if mod is not None:
        ob.modifiers.remove(mod)
    mod = ob.modifiers.new("gn", "NODES")
    mod.node_group = tree


def frame_camera(ob, azimuth=math.radians(35.0), elev=0.62, dist_k=2.9):
    deps = bpy.context.evaluated_depsgraph_get()
    deps.update()
    ev = ob.evaluated_get(deps)
    m = ev.to_mesh()
    xs = [v.co for v in m.vertices]
    lo = Vector((min(c[0] for c in xs), min(c[1] for c in xs), min(c[2] for c in xs)))
    hi = Vector((max(c[0] for c in xs), max(c[1] for c in xs), max(c[2] for c in xs)))
    ev.to_mesh_clear()
    center = (lo + hi) * 0.5
    radius = max((hi - lo).length * 0.5, 0.5)
    d = Vector((math.cos(elev) * math.cos(azimuth),
                math.cos(elev) * math.sin(azimuth),
                math.sin(elev)))
    cam.location = center + d * radius * dist_k
    look = (center - cam.location).normalized()
    cam.rotation_euler = look.to_track_quat('-Z', 'Y').to_euler()


CURRENT = {"ob": None}


def image_stats(path):
    img = bpy.data.images.load(path)
    px = img.pixels[:]
    n = len(px) // 4
    lum = [0.2126 * px[i * 4] + 0.7152 * px[i * 4 + 1] + 0.0722 * px[i * 4 + 2]
           for i in range(n)]
    mean = sum(lum) / max(n, 1)
    bright = sum(1 for v in lum if v > 0.60) / max(n, 1)
    bpy.data.images.remove(img)
    return mean, bright


def shoot(tag):
    ob = CURRENT.get("ob")
    if ob is not None:
        deps = bpy.context.evaluated_depsgraph_get()
        deps.update()
        ev = ob.evaluated_get(deps)
        m = ev.to_mesh()
        print(f"[previews] {tag}: verts={len(m.vertices)}")
        ev.to_mesh_clear()
    # Background-mode EEVEE reuses cached results when nothing dirties the
    # render depsgraph between calls - bump the frame to force a full re-eval
    # (a stale shot rendered the previous state otherwise).
    scene.frame_set(scene.frame_current + 1)
    path = os.path.join(OUT, tag + ".png")
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    mean, bright = image_stats(path)
    print(f"[previews] wrote {path} mean={mean:.4f} bright={bright:.4f}")


# ---- fountain: defaults + the self-feed read -----------------------------
ob, tree = build("GN_PARIS_FountainLoop")
CURRENT["ob"] = ob
frame_camera(ob, azimuth=math.radians(40.0), elev=0.55, dist_k=2.6)
shoot("fountain_defaults")
apply_preset(tree, "GN_PARIS_FountainLoop", "MI_SELF_FEED")
refresh_mod(ob, tree)
shoot("fountain_self_feed")
bpy.data.objects.remove(ob, do_unlink=True)

# ---- facade: night preset + dusk preset ----------------------------------
ob, tree = build("GN_PARIS_DayNightFacade")
CURRENT["ob"] = ob
# +55deg: the facade's dressed side faces +Y, so the camera must sit on +Y too
# (the -55deg first pass framed the blank back of the wall).
frame_camera(ob, azimuth=math.radians(55.0), elev=0.30, dist_k=2.1)
apply_preset(tree, "GN_PARIS_DayNightFacade", "MI_NUIT")
refresh_mod(ob, tree)
shoot("facade_nuit")
apply_preset(tree, "GN_PARIS_DayNightFacade", "MI_CREPUSCULE")
refresh_mod(ob, tree)
shoot("facade_crepuscule")
set_param(tree, "Night Mix", 0.0)
set_param(tree, "Shutter Open", 0.85)
refresh_mod(ob, tree)
shoot("facade_jour")
bpy.data.objects.remove(ob, do_unlink=True)

# ---- mansard roof band ---------------------------------------------------
ob, tree = build("GN_PARIS_Mansard")
CURRENT["ob"] = ob
frame_camera(ob, azimuth=math.radians(50.0), elev=0.42, dist_k=2.0)
shoot("mansard_canon")
bpy.data.objects.remove(ob, do_unlink=True)

# ---- penrose arch (the impossible read) ----------------------------------
ob, tree = build("GN_PARIS_PenroseArch")
CURRENT["ob"] = ob
apply_preset(tree, "GN_PARIS_PenroseArch", "MI_ARCH_TRIBAR")
refresh_mod(ob, tree)
frame_camera(ob, azimuth=math.radians(65.0), elev=0.18, dist_k=2.2)
shoot("arch_tribar")
bpy.data.objects.remove(ob, do_unlink=True)

# ---- metamorphosis frieze (the seam) -------------------------------------
ob, tree = build("GN_PARIS_MetamorphosisFrieze")
CURRENT["ob"] = ob
apply_preset(tree, "GN_PARIS_MetamorphosisFrieze", "MI_MORPH_SEAM")
refresh_mod(ob, tree)
frame_camera(ob, azimuth=math.radians(35.0), elev=0.35, dist_k=1.9)
shoot("frieze_seam")
bpy.data.objects.remove(ob, do_unlink=True)

def set_param(tree, name, value):
    for item in tree.interface.items_tree:
        if (getattr(item, "name", "") == name
                and getattr(item, "in_out", "") == "INPUT"):
            item.default_value = value
            return True
    return False


# ---- brutalist office block ----------------------------------------------
ob, tree = build("GN_BRUTALIST_OfficeBlock")
CURRENT["ob"] = ob
frame_camera(ob, azimuth=math.radians(140.0), elev=0.30, dist_k=2.6)
shoot("office_civic")
bpy.data.objects.remove(ob, do_unlink=True)

ob, tree = build("GN_BRUTALIST_OfficeBlock")
CURRENT["ob"] = ob
frame_camera(ob, azimuth=math.radians(180.0), elev=0.10, dist_k=2.4)
shoot("office_front")
bpy.data.objects.remove(ob, do_unlink=True)

ob, tree = build("GN_BRUTALIST_OfficeBlock")
CURRENT["ob"] = ob
apply_preset(tree, "GN_BRUTALIST_OfficeBlock", "BR_OFFICE_BUNKER")
refresh_mod(ob, tree)
frame_camera(ob, azimuth=math.radians(140.0), elev=0.28, dist_k=2.0)
shoot("office_bunker")
bpy.data.objects.remove(ob, do_unlink=True)

# ---- brutalist cubicle farm ----------------------------------------------
# low corner angle: the ceiling grid is a solid slab, a top-down shot shows
# only the slab - come in under it
ob, tree = build("GN_BRUTALIST_CubicleFarm")
CURRENT["ob"] = ob
frame_camera(ob, azimuth=math.radians(215.0), elev=0.24, dist_k=2.0)
shoot("cubicle_canon")
bpy.data.objects.remove(ob, do_unlink=True)

# plan read: ceiling off so the whole grid is visible from above
ob, tree = build("GN_BRUTALIST_CubicleFarm")
CURRENT["ob"] = ob
set_param(tree, "Ceiling Grid", False)
refresh_mod(ob, tree)
frame_camera(ob, azimuth=math.radians(215.0), elev=0.72, dist_k=1.9)
shoot("cubicle_plan")
bpy.data.objects.remove(ob, do_unlink=True)

ob, tree = build("GN_BRUTALIST_CubicleFarm")
CURRENT["ob"] = ob
apply_preset(tree, "GN_BRUTALIST_CubicleFarm", "BR_CUBICLE_SWARM")
refresh_mod(ob, tree)
frame_camera(ob, azimuth=math.radians(215.0), elev=0.24, dist_k=2.0)
shoot("cubicle_swarm")
bpy.data.objects.remove(ob, do_unlink=True)

print("[previews] done")
