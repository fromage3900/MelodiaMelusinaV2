# -*- coding: utf-8 -*-
"""p21 — turntable: 8-frame 360° deploy-pose mini-animation, render loop PNGs.

Nikki doctrine / P6-prototype loop pattern: a hero should read as a sculpt
from ALL sides, not one poster frame.

RIG LESSON (verified by inspection): every violin part is a ROOT object with
no parent; ME_WaveViolin_Control is only a DRIVER SOURCE (parts read its
rotation_euler[0] to fold/deploy), and the light rig + presentation camera are
aimed at ONE composition side. => camera-orbit turntables render near-identical
frames (rotationally-dark rear views): in-blender census showed cross_frame_diff
0.0 while raw PNG md5s already diverged sub-pixel. The robust pattern is OBJECT
SPIN: a dedicated parent empty (ME_Violin_Turntable @ world origin, identity)
holds every instrument/socket object; the well-framed presentation camera and
lights stay put, and the empty is keyed through a full 360° turn on Z (the
instrument's vertical axis). As the lantern spins, the emissive/reflective
faces and asymmetric silhouettes (belly pattern, scroll spiral, strings,
ribbons) sweep the fixed lit composition -> genuine cross-frame variation.

This script ONLY renders frames + persists the spin animation. The numeric
evidence (trusted census + cross-frame diff on the FINAL PNGs) and the
contact-sheet plate are produced by a host-Python verifier that re-reads the
actual rendered files, because Blender's in-session image read is unreliable
here (returns stale buffers for fresh renders).

Hygiene: headless only, never connects to the owner's GUI session.
"""
import bpy, json, os, math

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
log = lambda m: print(f"[vr-p21] {m}", flush=True)
rep = {"phase": "p21", "ok": True}

scn = bpy.context.scene
mc = bpy.data.objects["ME_WaveViolin_Control"]
mc.rotation_euler.x = 0.0                              # DEPLOY pose locked
bpy.context.view_layer.update()

# ---- clean any leftover turntable camera from the abandoned camera-orbit ----
for nm in ("ME_Violin_Cam_Turntable",):
    old = bpy.data.objects.get(nm)
    if old:
        camdata = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if camdata and camdata.users == 0:
            bpy.data.cameras.remove(camdata)
            log(f"removed leftover {nm}")

# ---- turntable parent empty @ world origin, identity ----
tt = bpy.data.objects.get("ME_Violin_Turntable")
if tt is None:
    tt = bpy.data.objects.new("ME_Violin_Turntable", None)
    bpy.context.scene.collection.objects.link(tt)
tt.matrix_world = __import__("mathutils").Matrix.Identity(4)
if tt.animation_data:
    tt.animation_data_clear()
tt.rotation_euler = (0.0, 0.0, 0.0)

# ---- reparent every instrument/socket ROOT under the turntable (keep world) ----
EXCLUDE = {"ME_Violin_Cam_Macro", "ME_Violin_Cam_Macro.001", "ME_Violin_Cam_Macro2",
           "ME_WaveViolin_Cam_Presentation", "ME_WaveViolin_Light_Fill",
           "ME_WaveViolin_Light_Key", "ME_WaveViolin_Light_Rim",
           "ME_WaveViolin_Ground", "ME_WaveViolin_Control",
           "ME_Violin_WorldAnchor", "ME_Violin_Turntable"}
reparented = []
for ob in bpy.data.objects:
    if ob.parent is not None:                 # only roots
        continue
    if ob.name in EXCLUDE:
        continue
    ob.parent = tt                            # turntable at identity -> local==world
    reparented.append(ob.name)
rep["parented_under_turntable"] = len(reparented)
rep["turntable"] = {"object": tt.name, "mode": "object-spin about world Z",
                    "frames": 8, "frame_range": [1, 8],
                    "camera": "ME_WaveViolin_Cam_Presentation (fixed)"}
log(f"reparented {len(reparented)} roots under {tt.name}")

# ---- render 8 frames, keying the spin ----
scn.camera = bpy.data.objects["ME_WaveViolin_Cam_Presentation"]
scn.frame_start = 1
scn.frame_end = 8
N = 8
for i in range(N):
    f = i + 1
    sp = (i / N) * 2.0 * math.pi                 # full 360°
    tt.rotation_euler.z = sp
    scn.frame_set(f)
    tt.keyframe_insert(data_path="rotation_euler", frame=f)
    bpy.context.view_layer.update()              # eval deploy drivers under parent
    scn.render.filepath = os.path.join(OUT, f"p21_turn_{i:02d}.png")
    bpy.ops.render.render(write_still=True)
    log(f"frame {f}: spin_z={math.degrees(sp):.0f}deg")

bpy.ops.wm.save_mainfile()
json.dump(rep, open(os.path.join(OUT, "p21_report_partial.json"), "w"), indent=1)
log("p21 render DONE")