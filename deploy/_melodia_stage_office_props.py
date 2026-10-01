"""Stage + shoot GN_OFFICE_DeskCluster - the first film prop, on camera.

Read-only against the builder; writes only into Saved/. Produces:

  1. Saved/Blend/OFFICE_DESK_REVIEW_<date>.blend - labelled collection, live
     geometry-nodes modifier so the dials stay playable in the file, one node
     group per object so two presets never fight over socket defaults.
  2. Saved/Audit/office_desk_shots_*.png - three framings of the same prop:
     three-quarter, front elevation (the dimension shot), and a low macro on
     the monitor/desk junction.
  3. Saved/Audit/office_desk_stage.json - the numbers behind the pictures.

The asset is ISOLATED in every shot (only lights, camera and _LAB helpers are
left visible), per the pipeline rule that a render is evidence only when the
subject is unambiguous in it.

Usage:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
      --background --factory-startup \
      --python deploy/_melodia_stage_office_props.py -- --date 2026-10-01

    -- --date YYYY-MM-DD   stamp on outputs (default today)
    -- --skip-render       stage + save the .blend only
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
from mathutils import Vector  # noqa: E402
from surreal_arch.melodia_gn import office_props  # noqa: E402
from surreal_arch.melodia_gn.paris_common import out_name  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


STAMP = arg("--date", "2026-10-01")
SKIP_RENDER = "--skip-render" in argv
BUILDER_ID = "GN_OFFICE_DeskCluster"

AUDIT = os.path.join(REPO, "Saved", "Audit")
BLEND_PATH = os.path.join(REPO, "Saved", "Blend",
                         "OFFICE_DESK_REVIEW_%s.blend" % STAMP)
os.makedirs(AUDIT, exist_ok=True)
os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)


# ---- clear the scene (a fresh factory-startup file is already empty, but a
# ---- re-run against a saved file must not inherit the previous stage).
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.1   # 1 unit = 100 mm, house convention

report = {"builder": BUILDER_ID, "date": STAMP, "objects": [], "shots": []}


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


def eval_stats(ob, world=False):
    """Measured vert/poly count and bbox.

    world=True adds the object's LOCATION to the bbox. The evaluated mesh is in
    LOCAL space, so a staged object at x=-1.6 still measures around 0 - and a
    camera framed on that number aims at empty space beside the prop. That is
    why every shot came back as background with the desk cropped at the edge.
    """
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    nv, npoly = len(me.vertices), len(me.polygons)
    bb = None
    if nv:
        ox, oy, oz = (ob.location if world else (0.0, 0.0, 0.0))
        xs = [v.co.x + ox for v in me.vertices]
        ys = [v.co.y + oy for v in me.vertices]
        zs = [v.co.z + oz for v in me.vertices]
        bb = {"x": [round(min(xs), 4), round(max(xs), 4)],
              "y": [round(min(ys), 4), round(max(ys), 4)],
              "z": [round(min(zs), 4), round(max(zs), 4)]}
    ev.to_mesh_clear()
    return nv, npoly, bb


# ---- the prop, in three dressed variants ----------------------------------
VARIANTS = [
    # (object name, preset dict, x offset)
    ("DESK_Standard", {}, -1.6),
    ("DESK_MonitorOff", {"Monitor": False}, 0.4),
    ("DESK_Bare", {"Pedestal": False, "Keyboard": False, "Mouse": False,
                   "Mouse Pad": False, "Chair": False}, 2.4),
]

col = bpy.data.collections.new("OFFICE_PROPS")
scene.collection.children.link(col)

# Give the props a readable material too: the `surface` Group Input has no
# default, so an unset material renders as the flat default grey and the shot
# reads as a silhouette study rather than a dressed prop.
desk_mat = bpy.data.materials.new("LAB_Worktop")
desk_mat.use_nodes = True
_dbsdf = desk_mat.node_tree.nodes.get("Principled BSDF")
if _dbsdf is not None:
    _dbsdf.inputs["Base Color"].default_value = (0.72, 0.66, 0.56, 1.0)
    _dbsdf.inputs["Roughness"].default_value = 0.55


for name, overrides, xoff in VARIANTS:
    # A UNIQUE tree per staged object. build_office_desk_cluster() reuses and
    # purges any existing tree of the same name (new_geometry_tree), so three
    # variants sharing one name left all three modifiers pointing at whichever
    # tree was built last - the saved .blend then showed flat slabs instead of
    # desks, and the camera framed empty space.
    tree = office_props.build_office_desk_cluster("GN_OFFICE_DeskCluster_" + name)
    mesh = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, mesh)
    col.objects.link(ob)
    for k, v in overrides.items():
        set_param(tree, k, v)
    # the `surface` material socket: without a default the whole cluster renders
    # as flat default grey
    for it in tree.interface.items_tree:
        if (getattr(it, "name", "") == "surface"
                and getattr(it, "in_out", "") == "INPUT"):
            try:
                it.default_value = desk_mat
            except Exception as exc:
                print("[office-stage] WARN surface default %s: %s" % (name, exc))
    ob.location = (xoff, 0.0, 0.0)
    mod = ob.modifiers.new("gn", 'NODES')
    # Measure on a THROWAWAY object bound to the same tree. A modifier that has
    # already evaluated keeps its own cached result: writing the interface
    # default afterwards changes nothing measurable, which is why all three
    # variants first reported an identical 294 verts. A fresh modifier resolves
    # against the interface at construction time. The staged object still gets
    # a real modifier below so the dials stay playable in the .blend.
    probe = bpy.data.objects.new("_probe_" + name, bpy.data.meshes.new("_pm"))
    scene.collection.objects.link(probe)
    pm = probe.modifiers.new("gn", 'NODES')
    pm.node_group = tree
    nv, npoly, bb = eval_stats(probe, world=False)
    bpy.data.objects.remove(probe, do_unlink=True)
    # the real object, same tree, same dials
    mod.node_group = tree
    wnv, wnp, wbb = eval_stats(ob, world=True)
    if overrides:
        print("[office-stage] %-16s overrides=%s verts=%d"
              % (name, sorted(overrides), nv))
    report["objects"].append({"object": name, "overrides": overrides,
                              "verts": nv, "polys": npoly, "bbox": bb,
                              "world_bbox": wbb, "location": list(ob.location)})
    print("[office-stage] %-16s verts=%-5d polys=%-5d %s"
          % (name, nv, npoly, json.dumps(bb)))

# ---- lighting: a three-point studio rig, soft key + fill + rim ------------
def add_light(name, ltype, loc, energy, size=1.0, rot=(0, 0, 0)):
    d = bpy.data.lights.new(name, ltype)
    d.energy = energy
    if ltype == 'AREA':
        d.size = size
    ob = bpy.data.objects.new(name, d)
    ob.location = loc
    ob.rotation_euler = rot
    scene.collection.objects.link(ob)
    return ob


add_light("LAB_Key", 'AREA', (-2.2, -3.0, 3.2), 1400, 3.0,
          (math.radians(50), 0, math.radians(-35)))
add_light("LAB_Fill", 'AREA', (3.0, -2.0, 1.6), 220, 4.0,
          (math.radians(72), 0, math.radians(55)))
add_light("LAB_Rim", 'AREA', (0.5, 3.2, 2.4), 420, 2.0,
          (math.radians(115), 0, math.radians(10)))

# A SUN as the render key. Three area lights plus a 16 m floor produced a flat
# wash at these distances; one directional source with real falloff is what
# actually reads on a grey prop. The area rig stays for interactive use.
sun_data = bpy.data.lights.new("LAB_Sun", 'SUN')
sun_data.energy = 3.2
sun_data.angle = math.radians(3.0)
sun = bpy.data.objects.new("LAB_Sun", sun_data)
sun.rotation_euler = (math.radians(52), 0.0, math.radians(-38))
scene.collection.objects.link(sun)

# A matte floor so contact shadows read and the prop is not floating in void.
# Built from an explicit mesh, NOT bpy.ops - the operator version added the
# plane into whatever collection was active and the material then landed on
# bpy.data.objects[0], which is the first DESK, not the floor.
floor_mesh = bpy.data.meshes.new("LAB_FloorMesh")
floor_mesh.from_pydata([(-5, -5, 0), (5, -5, 0), (5, 5, 0), (-5, 5, 0)],
                       [], [(0, 1, 2, 3)])
floor_mesh.update()
floor = bpy.data.objects.new("LAB_Floor", floor_mesh)
scene.collection.objects.link(floor)

fm = bpy.data.materials.new("LAB_FloorMat")
fm.use_nodes = True
_fbsdf = fm.node_tree.nodes.get("Principled BSDF")
if _fbsdf is not None:
    _fbsdf.inputs["Base Color"].default_value = (0.055, 0.056, 0.060, 1.0)
    _fbsdf.inputs["Roughness"].default_value = 0.92
floor.data.materials.append(fm)

# ---- world: soft grey, no HDRI needed for a dimension check ---------------
world = bpy.data.worlds.new("LAB_World")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (
    0.16, 0.17, 0.19, 1.0)
world.node_tree.nodes["Background"].inputs[1].default_value = 1.0

# ---- render engine --------------------------------------------------------
for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE', 'CYCLES'):
    try:
        scene.render.engine = engine
        print("[office-stage] engine = %s" % engine)
        break
    except Exception:
        continue
scene.render.resolution_x = 1280
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
try:
    scene.eevee.taa_render_samples = 48
except Exception:
    pass


# ---- camera ---------------------------------------------------------------
cam_data = bpy.data.cameras.new("LAB_Cam")
cam_data.lens = 50.0
cam = bpy.data.objects.new("LAB_Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam


def frame(ob, azimuth_deg, elevation_deg, margin=1.15):
    """Aim the camera at the object's WORLD bbox from a spherical offset."""
    nv, npoly, bb = eval_stats(ob, world=True)
    if not bb:
        return
    lo = Vector((bb["x"][0], bb["y"][0], bb["z"][0]))
    hi = Vector((bb["x"][1], bb["y"][1], bb["z"][1]))
    ctr = (lo + hi) * 0.5
    radius = max((hi - lo).length * 0.5, 0.05) * margin
    az, el = math.radians(azimuth_deg), math.radians(elevation_deg)
    direction = Vector((math.sin(az) * math.cos(el),
                        -math.cos(az) * math.cos(el),
                        math.sin(el)))
    # cam_data.angle is ALREADY in radians - wrapping it in math.radians()
    # squared the value, which collapsed the distance and put the camera
    # inside the desk. Frame on the horizontal half-FOV with a margin.
    # Fit the SPHERE of radius `radius` in the SMALLER of the two half-angles.
    # sensor_width 36mm at 50mm lens gives angle=0.628 rad (36 deg) on the long
    # axis; the SHORT axis is narrower by the aspect ratio. Using the long-axis
    # half-angle for both put the camera 0.5 m from a 1.5 m desk, which framed
    # two surfaces as abstract bars.
    aspect = scene.render.resolution_x / float(scene.render.resolution_y)
    half_h = cam_data.angle * 0.5
    half_w = math.atan(math.tan(half_h) * aspect)
    half_fov = min(half_h, half_w)
    cam.location = ctr + direction * (radius / math.tan(half_fov))
    # point at the centre
    d = (ctr - cam.location)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def isolate(target):
    hidden = []
    for ob in scene.objects:
        if ob is target or ob.name.startswith("LAB_"):
            continue
        if ob.type == 'MESH' and not ob.hide_render:
            ob.hide_render = True
            hidden.append(ob)
    target.hide_render = False
    return hidden


def unisolate(hidden):
    for ob in hidden:
        ob.hide_render = False


SHOTS = [
    ("three_quarter", "DESK_Standard", 42.0, 26.0, 1.15),
    ("front_elevation", "DESK_Standard", 0.0, 8.0, 1.10),
    ("low_macro", "DESK_Standard", 28.0, 4.0, 0.55),
    ("variant_monitor_off", "DESK_MonitorOff", 38.0, 22.0, 1.15),
    ("variant_bare", "DESK_Bare", 34.0, 20.0, 1.15),
]

if not SKIP_RENDER:
    for tag, obj_name, az, el, margin in SHOTS:
        ob = bpy.data.objects.get(obj_name)
        if ob is None:
            continue
        hidden = isolate(ob)
        # area lights are visible geometry in frame; the sun is not. Hide the
        # three area lights for the shot and keep the sun as the key.
        area_hidden = [o for o in scene.objects
                       if o.type == 'LIGHT' and o.data.type == 'AREA']
        for o in area_hidden:
            o.hide_render = True
        frame(ob, az, el, margin)
        path = os.path.join(AUDIT, "office_desk_shot_%s.png" % tag)
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        unisolate(hidden)
        for o in area_hidden:
            o.hide_render = False
        nv, npoly, bb = eval_stats(ob)
        report["shots"].append({"tag": tag, "object": obj_name,
                                "azimuth": az, "elevation": el,
                                "margin": margin, "file": path,
                                "verts": nv,
                                "camera": [round(v, 4) for v in cam.location],
                                "cam_rot": [round(v, 4) for v in
                                             cam.rotation_euler]})
        print("[office-stage] shot %-22s -> %s" % (tag, os.path.basename(path)))

# ---- save the .blend ------------------------------------------------------
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("[office-stage] blend: %s" % BLEND_PATH)

with open(os.path.join(AUDIT, "office_desk_stage.json"), "w") as fh:
    json.dump(report, fh, indent=2)
print("[office-stage] manifest: %s" % os.path.join(AUDIT,
                                                   "office_desk_stage.json"))