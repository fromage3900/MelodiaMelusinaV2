# -*- coding: utf-8 -*-
"""p21 onepass: render ONE keyed turntable frame in a fresh process.
Each frame gets its own blender -b process (frames past 0 are otherwise
cached identically by EEVEE 5.2 in a single headless run). Usage:
  blender -b ME_WaveViolin.blend -P p21_onepass.py -- <idx 0..7>
The blend already carries ME_Violin_Turntable + parented parts + spin keyframes.
"""
import bpy, os, sys

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
idx = int(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else 0

bpy.ops.wm.open_mainfile(filepath=BLEND)
scn = bpy.context.scene
scn.camera = bpy.data.objects["ME_WaveViolin_Cam_Presentation"]
scn.frame_set(idx + 1)                      # evaluate the keyed spin for this frame
bpy.context.view_layer.update()
scn.render.filepath = os.path.join(OUT, f"p21_turn_{idx:02d}.png")
bpy.ops.render.render(write_still=True)
print(f"[onepass] frame {idx} -> p21_turn_{idx:02d}.png", flush=True)