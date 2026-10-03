"""Beauty render scene for the eyewear editorial — studio lighting + camera rig.

Rebuilds the demo scene from the realized hero meshes (source of truth stays
in the GN builders) and renders beauty passes: HERO_3Q 3/4, FRONT_ORTHO
technical view, PROFILE, and TURNTABLE frames. Lighting follows the plan's
photography research (Appendix B): one very large diffuser sized to cover the
whole family of angles, plus small area sources for the acetate edges and
temples. Proportionally scaled to a 134 mm subject.

Outputs to Exports/EyewearEditorial/Beauty/<hero>/<shot>.png
"""
import json
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
BEAUTY = os.path.join(ROOT, "Beauty")
os.makedirs(BEAUTY, exist_ok=True)

MM = 0.001
# subject is 0.134 BU wide; photography research: diffuser ~15-20x subject width
# at ~6-7x subject width of distance. Scale proportionally.
SUBJECT_W = 0.134
DIFFUSER_SCALE = 18.0 * SUBJECT_W   # ~2.4 m
DIFFUSER_DIST = 7.0 * SUBJECT_W     # ~0.94 m


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


def build_studio_world(sc):
    """Studio world: neutral mid-grey, no sky. Beauty wants a controlled
    environment, not a sky gradient."""
    world = bpy.data.worlds.new("Studio_Beauty")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.05, 0.05, 0.05, 1.0)
    bg.inputs["Strength"].default_value = 0.0   # lights only, no ambient
    sc.world = world
    return world


def build_studio_lights(sc):
    """Three-point studio: large diffuser key + two small edge sources.

    Key: very large area light above-front, the dominant source. Sized to
    cover the family of angles (the whole 134 mm subject + lens reflection).
    Fill: smaller area light opposite side, lower ratio.
    Rim: small area light behind for the acetate edge glow."""
    lights = []

    # KEY — large diffuser, the dominant source
    key = bpy.data.lights.new("Key_Diffuser", "AREA")
    key.shape = "RECTANGLE"
    key.size = DIFFUSER_SCALE
    key.size_y = DIFFUSER_SCALE * 0.6
    key.energy = 400.0
    key.color = (1.0, 0.98, 0.95)   # slightly warm
    key_obj = bpy.data.objects.new("Key_Diffuser", key)
    sc.collection.objects.link(key_obj)
    key_obj.location = (0.2, -DIFFUSER_DIST, DIFFUSER_DIST * 0.8)
    look_at(key_obj, (0, 0, 0))
    lights.append(key_obj)

    # FILL — smaller, opposite side, cooler, lower ratio
    fill = bpy.data.lights.new("Fill_Area", "AREA")
    fill.shape = "RECTANGLE"
    fill.size = DIFFUSER_SCALE * 0.4
    fill.size_y = DIFFUSER_SCALE * 0.3
    fill.energy = 100.0
    fill.color = (0.95, 0.97, 1.0)   # slightly cool
    fill_obj = bpy.data.objects.new("Fill_Area", fill)
    sc.collection.objects.link(fill_obj)
    fill_obj.location = (-0.6, -0.4, 0.3)
    look_at(fill_obj, (0, 0, 0))
    lights.append(fill_obj)

    # RIM — small, behind, for acetate edge glow
    rim = bpy.data.lights.new("Rim_Spot", "AREA")
    rim.shape = "RECTANGLE"
    rim.size = 0.15
    rim.size_y = 0.4
    rim.energy = 400.0
    rim_obj = bpy.data.objects.new("Rim_Spot", rim)
    sc.collection.objects.link(rim_obj)
    rim_obj.location = (-0.3, 0.5, 0.2)
    look_at(rim_obj, (0, 0, 0))
    lights.append(rim_obj)

    return lights


def build_camera_rig(sc):
    """Camera rig: HERO_3Q (85-100mm equiv), FRONT_ORTHO (technical), PROFILE.
    Returns dict of name -> (camera_obj, camera_data)."""
    rig = {}

    # HERO_3Q — 90mm equiv, the beauty 3/4
    cam3q = bpy.data.cameras.new("HERO_3Q")
    cam3q.lens = 90.0
    cam3q.clip_start = 0.0005
    cam3q.clip_end = 10.0
    cam3q_obj = bpy.data.objects.new("HERO_3Q", cam3q)
    sc.collection.objects.link(cam3q_obj)
    rig["HERO_3Q"] = (cam3q_obj, cam3q)

    # FRONT_ORTHO — orthographic, the technical/product view
    cam_front = bpy.data.cameras.new("FRONT_ORTHO")
    cam_front.type = "ORTHO"
    cam_front.ortho_scale = SUBJECT_W * 1.6   # frame the 134mm subject with margin
    cam_front.clip_start = 0.0005
    cam_front.clip_end = 10.0
    cam_front_obj = bpy.data.objects.new("FRONT_ORTHO", cam_front)
    sc.collection.objects.link(cam_front_obj)
    rig["FRONT_ORTHO"] = (cam_front_obj, cam_front)

    # PROFILE — same lens as 3Q, rotated 90
    cam_prof = bpy.data.cameras.new("PROFILE")
    cam_prof.lens = 90.0
    cam_prof.clip_start = 0.0005
    cam_prof.clip_end = 10.0
    cam_prof_obj = bpy.data.objects.new("PROFILE", cam_prof)
    sc.collection.objects.link(cam_prof_obj)
    rig["PROFILE"] = (cam_prof_obj, cam_prof)

    return rig


def realize_hero(tag, params):
    """Build the GN tree, realize to mesh, return (frame_obj, lens_obj)."""
    r = GROUP_BUILDERS["MEL_eyewear_pair"]()
    tree = r[0] if isinstance(r, (tuple, list)) else r
    for k, v in params.items():
        setp(tree, k, v)

    sc = bpy.context.scene

    # frame
    me = bpy.data.meshes.new("M_" + tag)
    ob = bpy.data.objects.new("HERO_" + tag, me)
    sc.collection.objects.link(ob)
    mod = ob.modifiers.new("m", "NODES")
    mod.node_group = tree
    bpy.context.view_layer.update()
    real = bpy.data.meshes.new_from_object(ob.evaluated_get(
        bpy.context.evaluated_depsgraph_get()))
    ob.modifiers.clear()
    ob.data = real

    # lens (join both halves)
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
    lreal = bpy.data.meshes.new_from_object(lob.evaluated_get(
        bpy.context.evaluated_depsgraph_get()))
    lob.modifiers.clear()
    lob.data = lreal
    bpy.data.node_groups.remove(lw)

    # standup: family Y-up -> world Z-up
    ob.rotation_euler = (math.radians(-90.0), 0.0, 0.0)
    lob.rotation_euler = (math.radians(-90.0), 0.0, 0.0)
    bpy.context.view_layer.update()

    return ob, lob


def place_for_shot(cam_obj, cam_data, shot_name):
    """Position the camera for a given shot. Subject at origin, optical centre
    ~ (0, 0, -0.01)."""
    target = Vector((0.0, 0.0, -0.01))
    if shot_name == "HERO_3Q":
        cam_obj.location = Vector((0.20, -0.34, 0.13))
    elif shot_name == "FRONT_ORTHO":
        cam_obj.location = Vector((0.0, -0.5, 0.0))
    elif shot_name == "PROFILE":
        cam_obj.location = Vector((0.5, 0.0, 0.0))
    elif shot_name == "TURNTABLE":
        cam_obj.location = Vector((0.20, -0.34, 0.13))
    look_at(cam_obj, target)


def render_hero(tag, ob, lob, cam_rig, sc, shot_name):
    """Render one hero from one camera angle."""
    out_dir = os.path.join(BEAUTY, tag)
    os.makedirs(out_dir, exist_ok=True)

    # hide all other heroes
    for o in sc.objects:
        if o.type == "MESH" and o is not ob and o is not lob:
            o.hide_render = True

    cam_obj, cam_data = cam_rig[shot_name]
    sc.camera = cam_obj
    place_for_shot(cam_obj, cam_data, shot_name)

    # DOF on the hero cam for beauty
    if shot_name in ("HERO_3Q", "PROFILE", "TURNTABLE"):
        cam_data.dof.use_dof = True
        cam_data.dof.focus_distance = 0.45
        cam_data.dof.aperture_fstop = 2.8
    else:
        cam_data.dof.use_dof = False

    sc.render.filepath = os.path.join(out_dir, shot_name + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDER %s %s" % (tag, shot_name))

    # unhide
    for o in sc.objects:
        if o.type == "MESH":
            o.hide_render = False


def main():
    sc = bpy.context.scene

    # clean scene
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # render settings — beauty
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x = 2048
    sc.render.resolution_y = 2048
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.eevee.taa_render_samples = 256
    try:
        sc.eevee.bloom_threshold = 0.8
        sc.eevee.bloom_intensity = 0.05
        sc.eevee.use_bloom = True
    except Exception:
        pass   # bloom API changed across EEVEE versions
    try:
        sc.eevee.use_ssr = True
        sc.eevee.use_ssr_refraction = True
    except Exception:
        pass
    sc.display_settings.display_device = "sRGB"
    sc.view_settings.exposure = -0.7

    build_studio_world(sc)
    build_studio_lights(sc)
    cam_rig = build_camera_rig(sc)

    # hide all cameras' meshes from each other
    for name, (cam_obj, cam_data) in cam_rig.items():
        if name != "HERO_3Q":
            cam_obj.hide_render = True

    shots = ["HERO_3Q", "FRONT_ORTHO", "PROFILE"]

    for tag, params in HEROES:
        ob, lob = realize_hero(tag, params)
        print("HERO %s verts=%d/%d" % (tag, len(ob.data.vertices), len(lob.data.vertices)))
        for shot in shots:
            render_hero(tag, ob, lob, cam_rig, sc, shot)

    # save the beauty scene
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "eyewear_beauty.blend"))
    print("SAVED", os.path.join(ROOT, "eyewear_beauty.blend"))
    print("DONE")


if __name__ == "__main__":
    main()
