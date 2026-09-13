"""11.7 editorial scene: realize all 6 heroes to mesh, stage, stills, save.

Realized (not live GN): six live pair variants cannot coexist (each build
invalidates the shared subtrees the earlier ones nest). Realized meshes are
also export-safe and version-proof. Source of truth stays in the builders.
Standup: -90 deg about X (family Y-up loads lying down), origin = optical
centre already. Camera clip_start 0.0005 (the 11.7 trap: default 0.1 clips
the whole 0.134 m asset). Square transparent PNGs for web/Upwork cards.
"""
import math
import os
import sys

import bpy
from mathutils import Quaternion, Vector

_WT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WT = _WT
sys.path.insert(0, WT + "/deploy")
from surreal_arch.melodia_gn.core import GROUP_BUILDERS  # noqa: E402

ESP = (0.09, 0.055, 0.045, 1.0)
CHAMP = (0.95, 0.80, 0.60, 1.0)
BASE = {"Base Curve": 6.0, "Form Angle": 4.4,
        "Top Tint": (0.15, 0.15, 0.18, 1.0),
        "Bottom Tint": (0.90, 0.95, 1.00, 1.0)}
HEROES = [
    ("rect-tortoise", dict(BASE, **{"Silhouette": 0, "Tortoise": 1.0,
                                    "Metal Frame": False, "Frame Solid": ESP})),
    ("rect-metal", dict(BASE, **{"Silhouette": 0, "Tortoise": 0.0, "Base Curve": 4.0,
                                 "Metal Frame": True, "Frame Solid": CHAMP})),
    ("panto-tortoise", dict(BASE, **{"Silhouette": 1, "Tortoise": 1.0,
                                     "Metal Frame": False, "Frame Solid": ESP})),
    ("panto-metal", dict(BASE, **{"Silhouette": 1, "Tortoise": 0.0, "Base Curve": 4.0,
                                  "Metal Frame": True, "Frame Solid": CHAMP})),
    ("cateye-tortoise", dict(BASE, **{"Silhouette": 2, "Tortoise": 1.0,
                                      "Metal Frame": False, "Frame Solid": ESP})),
    ("cateye-metal", dict(BASE, **{"Silhouette": 2, "Tortoise": 0.0, "Base Curve": 4.0,
                                   "Metal Frame": True, "Frame Solid": CHAMP})),
    ("aviator-tortoise", dict(BASE, **{"Silhouette": 3, "Tortoise": 1.0,
                                       "Metal Frame": False, "Frame Solid": ESP})),
    ("aviator-metal", dict(BASE, **{"Silhouette": 3, "Tortoise": 0.0, "Base Curve": 4.0,
                                    "Metal Frame": True, "Frame Solid": CHAMP})),
]
ROOT = os.path.join(WT, "Exports", "EyewearEditorial")
os.makedirs(os.path.join(ROOT, "Stills"), exist_ok=True)

# clean scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = 1080
sc.render.resolution_y = 1080
sc.render.resolution_percentage = 100
sc.render.film_transparent = True
sc.eevee.taa_render_samples = 64
sc.display_settings.display_device = "sRGB"
try:
    sc.view_settings.view_transform = "Standard"
except Exception:
    pass

# lights + world
sun = bpy.data.lights.new("Key", "SUN")
sun.energy = 3.0
sun_obj = bpy.data.objects.new("Key", sun)
sc.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(50), 0, math.radians(35))
fill = bpy.data.lights.new("Fill", "AREA")
fill.energy = 60.0
fill.size = 0.5
fill_obj = bpy.data.objects.new("Fill", fill)
sc.collection.objects.link(fill_obj)
fill_obj.location = (-0.4, -0.3, 0.3)
world = bpy.data.worlds.new("Studio")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.75, 0.75, 0.78, 1.0)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
sc.world = world

# camera (clip trap fixed)
cam = bpy.data.cameras.new("HERO_3Q")
cam.lens = 90.0
cam.clip_start = 0.0005
cam.clip_end = 10.0
cam_obj = bpy.data.objects.new("HERO_3Q", cam)
sc.collection.objects.link(cam_obj)
sc.camera = cam_obj


def look_at(obj, target):
    d = Vector(target) - obj.location
    q = d.to_track_quat("-Z", "Y")
    obj.rotation_euler = q.to_euler()


def setp(tree, name, val):
    for it in getattr(tree.interface, "items_tree", []):
        if getattr(it, "name", None) == name:
            try:
                it.default_value = val
                return True
            except Exception:
                pass
    return False


heroes = []
for tag, params in HEROES:
    r = GROUP_BUILDERS["MEL_eyewear_pair"]()
    tree = r[0] if isinstance(r, (tuple, list)) else r
    for k, v in params.items():
        setp(tree, k, v)
    me = bpy.data.meshes.new("M_" + tag)
    ob = bpy.data.objects.new("HERO_" + tag, me)
    sc.collection.objects.link(ob)
    mod = ob.modifiers.new("m", "NODES")
    mod.node_group = tree
    bpy.context.view_layer.update()
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    m = ev.to_mesh()
    if m is None or not len(m.vertices):
        print("HERO %s EMPTY" % tag)
        ev.to_mesh_clear()
        continue
    real = bpy.data.meshes.new_from_object(ob.evaluated_get(
        bpy.context.evaluated_depsgraph_get()))
    ev.to_mesh_clear()
    ob.modifiers.clear()
    ob.data = real
    ob.name = "HERO_" + tag
    # lenses: join both halves in pair space, realize as a sibling object
    lw = bpy.data.node_groups.new("__lensw__", "GeometryNodeTree")
    lgi = lw.nodes.new("NodeGroupInput")
    lgo = lw.nodes.new("NodeGroupOutput")
    lw.interface.new_socket(name="Geometry", in_out="INPUT",
                            socket_type="NodeSocketGeometry")
    lw.interface.new_socket(name="Geometry", in_out="OUTPUT",
                            socket_type="NodeSocketGeometry")
    lgn = lw.nodes.new("GeometryNodeGroup")
    lgn.node_tree = tree
    lj = lw.nodes.new("GeometryNodeJoinGeometry")
    lw.links.new(lgi.outputs["Geometry"], lgn.inputs["Geometry"])
    lw.links.new(lgn.outputs["LensL"], lj.inputs["Geometry"])
    lw.links.new(lgn.outputs["LensR"], lj.inputs["Geometry"])
    lw.links.new(lj.outputs["Geometry"], lgo.inputs["Geometry"])
    lme = bpy.data.meshes.new("ML_" + tag)
    lob = bpy.data.objects.new("HERO_" + tag + "_lens", lme)
    sc.collection.objects.link(lob)
    lmod = lob.modifiers.new("m", "NODES")
    lmod.node_group = lw
    bpy.context.view_layer.update()
    lev = lob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    lm = lev.to_mesh()
    if lm is not None and len(lm.vertices):
        lreal = bpy.data.meshes.new_from_object(lob.evaluated_get(
            bpy.context.evaluated_depsgraph_get()))
        lev.to_mesh_clear()
        lob.modifiers.clear()
        lob.data = lreal
    else:
        print("HERO %s LENS EMPTY" % tag)
        lev.to_mesh_clear()
    bpy.data.node_groups.remove(lw)
    # standup: family Y-up -> world Z-up
    ob.rotation_euler = (math.radians(-90.0), 0.0, 0.0)
    lob.rotation_euler = (math.radians(-90.0), 0.0, 0.0)
    bpy.context.view_layer.update()
    print("HERO %s verts=%d/%d mats=%s" % (
        tag, len(real.vertices), len(lob.data.vertices),
        sorted({mt.name for mt in real.materials if mt})))
    heroes.append((tag, ob, lob))

# lineup for the live session + individual stills at origin
for i, (tag, ob, lob) in enumerate(heroes):
    ob.location = (i * 0.30 - 0.75, 0.0, 0.0)
    lob.location = ob.location

blend = os.path.join(ROOT, "eyewear_editorial.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend)
print("saved", blend)

for tag, ob, lob in heroes:
    home = ob.location.copy()
    ob.location = (0.0, 0.0, -0.01)
    lob.location = (0.0, 0.0, -0.01)
    for t2, o2, l2 in heroes:
        o2.hide_render = (o2 is not ob)
        l2.hide_render = (l2 is not lob)
    cam_obj.location = (0.20, -0.34, 0.13)
    look_at(cam_obj, (0.0, 0.0, -0.02))
    sc.render.filepath = os.path.join(ROOT, "Stills", tag + ".png")
    bpy.ops.render.render(write_still=True)
    print("still", tag)
    ob.location = home
    lob.location = home
    for t2, o2, l2 in heroes:
        o2.hide_render = False
        l2.hide_render = False

bpy.ops.wm.save_as_mainfile()
print("DONE")

