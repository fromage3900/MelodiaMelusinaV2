"""A2 event takes for the Choral Sheep - BONE-DRIVEN (exports to UE with no morph targets).

Measured basis (2026-10-01, probe_mesh_truth): c_ear_*, c_tail_*, c_jawbone, c_spine_*, c_neck, c_head
all deform the mesh. (The older "ears/tail dead" receipts measured the non-deform *_ref marker bones.)
Rotation law (head-tip mm/deg): c_spine_01 X ~12.9 Z-drop, c_spine_02 ~9.1, c_spine_03 ~5.1,
c_neck ~2.1, c_head ~2.8 (-Y). Positive X pitches the head DOWN.

Reads  : WORK_BASE (pristine copy)       Writes: OUT (new file each run; base is never modified)
Env    : GRAZE_SCALE (float, default 1.0) - bounded-retry knob for head-down depth
Run    : blender --background --factory-startup --python author_a2.py
"""
import json
import math
import os
from pathlib import Path

import bpy

LANE = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\choral_sheep\anim_suite_20261001")
BASE = LANE / "choral_sheep_ANIMSUITE_WORK_20261001.blend"
OUT = LANE / "choral_sheep_ANIMSUITE_A2_20261001.blend"
S = float(os.environ.get("GRAZE_SCALE", "1.0"))

bpy.ops.wm.open_mainfile(filepath=str(BASE), load_ui=False)
sc = bpy.context.scene
rig = bpy.data.objects["rig"]
sc.render.fps = 24
sc.render.fps_base = 1.0


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def two_pi(x):
    return 2 * math.pi * x


# --- take definitions: name -> (frames, loop, fn(p) -> {(bone, axis_index): degrees}) ------------
def graze(p):
    d = ease(p / 0.20) * ease((1.0 - p) / 0.28)            # 0 -> 1 plateau -> 0, closes at both ends
    chew = d * (0.5 - 0.5 * math.cos(two_pi(6 * p)))
    return {("c_spine_01.x", 0): 7.0 * S * d, ("c_spine_02.x", 0): 8.0 * S * d,
            ("c_spine_03.x", 0): 9.0 * S * d, ("c_neck.x", 0): 24.0 * S * d,
            ("c_head.x", 0): 14.0 * S * d + 1.5 * d * math.sin(two_pi(3 * p)),
            ("c_jawbone.x", 0): 6.0 * chew}


def bleat(p):
    j = ease(p / 0.15) * ease((0.95 - p) / 0.25) * (1.0 + 0.12 * math.sin(two_pi(5 * p)) * ease(p / 0.2) * ease((1 - p) / 0.3))
    return {("c_jawbone.x", 0): 20.0 * j, ("c_head.x", 0): -5.0 * j,
            ("c_neck.x", 0): -7.0 * j, ("c_spine_03.x", 0): -2.0 * j}


def _flick(p):
    return math.sin(two_pi(p)) * (1.0 - p)


def earflick(p):
    p2 = max(0.0, p - 0.08) / 0.92
    return {("c_ear_01.l", 0): 18.0 * _flick(p), ("c_ear_02.l", 0): 24.0 * _flick(p2),
            ("c_head.x", 2): 1.2 * _flick(p)}


def tailwag(p):
    w = two_pi(3 * p)
    return {("c_tail_master.x", 2): 9.0 * math.sin(w), ("c_tail_00.x", 2): 6.0 * math.sin(w - 0.6),
            ("c_tail_01.x", 2): 6.0 * math.sin(w - 1.2), ("c_tail_02.x", 2): 5.0 * math.sin(w - 1.8),
            ("c_tail_master.x", 0): 3.0 * (0.5 - 0.5 * math.cos(two_pi(p)))}


def harmonize(p):
    r = ease(p / 0.20) * ease((1.0 - p) / 0.20)
    return {("c_spine_03.x", 0): -4.0 * r, ("c_spine_02.x", 0): -2.0 * r, ("c_neck.x", 0): -14.0 * r,
            ("c_head.x", 0): -9.0 * r, ("c_head.x", 2): 2.2 * r * math.sin(two_pi(p)),
            ("c_jawbone.x", 0): 4.0 * r}


TAKES = {"Graze": (96, True, graze, 4), "Bleat": (48, False, bleat, 2), "EarFlick": (24, False, earflick, 1),
         "TailWag": (60, True, tailwag, 2), "Harmonize": (120, False, harmonize, 4)}

# every bone any take touches -> reset to rest between takes
ALL_BONES = sorted({b for _, (_, _, fn, _) in TAKES.items() for (b, _) in fn(0.37).keys()})
for bn in ALL_BONES:
    pb = rig.pose.bones[bn]
    pb.rotation_mode = "XYZ"


def reset_rest():
    for bn in ALL_BONES:
        rig.pose.bones[bn].rotation_euler = (0.0, 0.0, 0.0)
        rig.pose.bones[bn].location = (0.0, 0.0, 0.0)


# keep A1 alive through the save (zero-user actions are dropped on save)
for a in bpy.data.actions:
    a.use_fake_user = True
if rig.animation_data is None:
    rig.animation_data_create()
a1_rig = bpy.data.actions.get("CHORAL_A1_Idle_Rig")

receipt = {"base": str(BASE), "out": str(OUT), "graze_scale": S, "fps": 24, "takes": {}}
for name, (frames, loop, fn, step) in TAKES.items():
    reset_rest()
    act = bpy.data.actions.new("CHORAL_A2_%s_Rig" % name)
    act.use_fake_user = True
    rig.animation_data.action = act
    channels = set()
    for f in sorted(set(list(range(0, frames, step)) + [frames])):
        vals = fn(f / frames)
        reset_rest()
        for (bn, ai), deg in vals.items():
            e = list(rig.pose.bones[bn].rotation_euler)
            e[ai] = math.radians(deg)
            rig.pose.bones[bn].rotation_euler = e
            channels.add((bn, ai))
        for bn in {b for (b, _) in vals.keys()}:
            rig.pose.bones[bn].keyframe_insert("rotation_euler", frame=f)
    receipt["takes"][name] = {"action": act.name, "frames": frames, "loop": loop, "key_step": step,
                              "channels": sorted("%s[%d]" % c for c in channels)}
    print("AUTHORED", name, frames, "keys step", step, "channels", len(channels), flush=True)

reset_rest()
if a1_rig:
    rig.animation_data.action = a1_rig
sc.frame_start, sc.frame_end = 0, 96
sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
receipt["bytes"] = OUT.stat().st_size
(LANE / "A2_authoring_20261001.json").write_text(json.dumps(receipt, indent=1))
print("A2_AUTHOR_DONE", json.dumps({"out": str(OUT), "bytes": receipt["bytes"], "scale": S}), flush=True)
os._exit(0)
