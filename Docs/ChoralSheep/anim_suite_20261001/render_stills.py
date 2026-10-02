"""Key-pose stills for the A2 suite: one 512x512 PNG per take at its peak frame.
Re-opens the SAVED A2 file, renders to stills/<Take>.png. Does not modify the blend.
EEVEE Next first; falls back to Workbench if the headless GL context fails.
"""
import json
import os

import bpy

LANE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(LANE, "choral_sheep_ANIMSUITE_A2_20261001.blend")
STILLS = os.path.join(LANE, "stills")
os.makedirs(STILLS, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=SRC, load_ui=False)
sc = bpy.context.scene
rig = bpy.data.objects["rig"]

# --- camera: reuse scene camera if present, else build a 3/4 view ---
cam = next((ob for ob in sc.objects if ob.type == "CAMERA"), None)
if cam is None:
    cam_data = bpy.data.cameras.new("StillCam")
    cam = bpy.data.objects.new("StillCam", cam_data)
    sc.collection.objects.link(cam)
    cam.location = (2.6, -2.6, 1.5)
    tgt = bpy.data.objects.new("StillCamTarget", None)
    sc.collection.objects.link(tgt)
    tgt.location = (0.0, 0.0, 0.7)
    con = cam.constraints.new("TRACK_TO")
    con.target = tgt
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
sc.camera = cam
sc.camera.data.lens = 35.0  # scene camera was clipping the head; widen for key-pose stills

# --- light: reuse if present, else add a sun ---
if not any(ob.type in {"SUN", "POINT", "AREA"} for ob in sc.objects):
    sun_data = bpy.data.lights.new("StillSun", "SUN")
    sun_data.energy = 3.0
    sun = bpy.data.objects.new("StillSun", sun_data)
    sc.collection.objects.link(sun)
    sun.rotation_euler = (0.9, 0.2, 0.6)

sc.render.resolution_x = 512
sc.render.resolution_y = 512
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"

# peak frames from A2_verify_20261001.json
TAKES = {"Graze": 20, "Bleat": 12, "EarFlick": 6, "TailWag": 26, "Harmonize": 24}


def render_take(name, frame, engine):
    act = bpy.data.actions["CHORAL_A2_%s_Rig" % name]
    rig.animation_data.action = act
    sc.frame_set(frame)
    bpy.context.view_layer.update()
    sc.render.engine = engine
    sc.render.filepath = os.path.join(STILLS, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("STILL", name, frame, engine, flush=True)


engine = "BLENDER_EEVEE"  # 5.2 enum (EEVEE Next was renamed back)
try:
    for name, fr in TAKES.items():
        render_take(name, fr, engine)
except Exception as ex:  # headless GL failure -> workbench
    print("EEVEE_FAILED", repr(ex), flush=True)
    engine = "BLENDER_WORKBENCH"
    for name, fr in TAKES.items():
        render_take(name, fr, engine)

print("STILLS_DONE", json.dumps({"engine": engine, "takes": list(TAKES)}), flush=True)
os._exit(0)
