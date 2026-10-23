"""Color-pipeline probe: pure RED world, no objects, no lamps.
256px render -> if the PNG is red, color management is fine.
Run:  blender -b --factory-startup -noaudio --python probe_color.py
"""
from pathlib import Path

import bpy

scene = bpy.context.scene
# background mode starts with the DEFAULT cube/camera/light - clear them or the
# probe camera renders the inside of the default cube (the invalid black result)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 8
scene.render.resolution_x = 256
scene.render.resolution_y = 256
try:
    scene.view_settings.view_transform = "Standard"
except Exception:
    pass
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (1.0, 0.0, 0.0, 1.0)
bg.inputs[1].default_value = 1.0
cam_data = bpy.data.cameras.new("C")
cam = bpy.data.objects.new("C", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (0, 0, 0)
cam.rotation_euler = (1.5707963, 0, 0)   # look along -Y into empty space
scene.camera = cam
out = Path(__file__).parent / "probe_color.png"
scene.render.filepath = str(out)
bpy.ops.render.render(write_still=True)

from PIL import Image
import numpy as np
img = np.asarray(Image.open(str(out)).convert("RGB"), dtype=np.float32)
print("[probe] mean RGB:", img.mean(axis=(0, 1)).round(1),
      "max:", img.max(axis=(0, 1)).round(1))
print("[probe] VERDICT:", "RED-OK" if img[..., 0].mean() > img[..., 1].mean() + 50
      else "BROKEN (not red)")
