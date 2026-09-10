# -*- coding: utf-8 -*-
"""p21 keyfix: rebuild the turntable spin keyframes in the CURRENT blend.
Lesson: set the transform AFTER scn.frame_set(f), then keyframe_insert — doing
it the other way around lets frame_set re-evaluate the (empty) fcurve and
clobber the assigned Z to 0 (that's why the saved action rot all-zero).
Fixed for a seamless 8-frame 360 loop with linear interpolation.
"""
import bpy, os, math

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
scn = bpy.context.scene
tt = bpy.data.objects["ME_Violin_Turntable"]

if tt.animation_data:
    tt.animation_data_clear()
N = 8
scn.frame_start = 1
scn.frame_end = N
for i in range(N):
    f = i + 1
    sp = (i / N) * 2.0 * math.pi
    scn.frame_set(f)                 # land on the frame FIRST
    tt.rotation_euler.z = sp         # then assign
    tt.keyframe_insert(data_path="rotation_euler", index=2, frame=f)

# linear interpolation for a clean loop (API tolerant — 5.2 may rename fcurves)
try:
    for fc in tt.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
except AttributeError:
    print("note: fcurves attr unavailable; keeping default interp", flush=True)

# verify evaluation
probe = []
for f in range(1, N + 1):
    scn.frame_set(f); bpy.context.view_layer.update()
    probe.append(round(math.degrees(tt.rotation_euler.z), 1))
print("tt z-rot eval per frame (deg):", probe, flush=True)
assert any(abs(p) > 30 for p in probe), "keyframes not applied!"
scn.frame_set(1)
bpy.ops.wm.save_mainfile()
print("p21 keys fixed + saved", flush=True)