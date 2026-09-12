"""Build a silhouette preset comparison grid.

Creates 6 pairs (one per silhouette) in a row, each labeled, all using the
same boxing (A54 B34 DBL18). Run headless or in live Blender.
"""
import sys

import bpy

sys.path.insert(0, r"P:/MelodiaMelusinaV2-Laptop/deploy")
from surreal_arch.melodia_gn.core import GROUP_BUILDERS  # noqa: E402

# Clear scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# World
bpy.context.scene.render.engine = "BLENDER_EEVEE"
bpy.context.scene.render.resolution_x = 1600
bpy.context.scene.render.resolution_y = 2000

# Lighting
for name, energy, loc in (
    ("Key", 600, (2.6, -2.4, 3.4)),
    ("Rim", 300, (-2.4, 1.6, 2.8)),
    ("Fill", 200, (0.4, 2.8, 2.2)),
):
    bpy.ops.object.light_add(type="AREA", location=loc)
    light = bpy.context.active_object
    light.name = name
    light.data.energy = energy
    light.data.size = 1.5

# Camera
bpy.ops.object.camera_add(location=(0, -6, 1.4))
cam = bpy.context.active_object
cam.name = "Cam_Compare"
cam.data.lens = 50
cam.data.clip_start = 0.001
bpy.context.scene.camera = cam

# 6 silhouettes
SILHOUETTES = [
    (0, "Rect"),
    (1, "Panto"),
    (2, "CatEye"),
    (3, "Aviator"),
    (4, "Browline"),
    (5, "Round"),
]

print("=== Staging silhouette comparison grid ===")

spacing = 0.30  # meters between each pair
x_start = -((len(SILHOUETTES) - 1) * spacing) / 2

for i, (idx, label) in enumerate(SILHOUETTES):
    x = x_start + i * spacing
    
    # Create mesh host (Cube) — GN modifiers produce geometry on mesh hosts, not empties
    bpy.ops.mesh.primitive_cube_add(size=0.10, location=(x, 0, 0))
    host = bpy.context.active_object
    host.name = f"Eyewear_{label}"
    
    # Apply hero builder
    mod = host.modifiers.new("GN", "NODES")
    mod.node_group = GROUP_BUILDERS["MEL_eyewear_hero"]()
    
    # Set silhouette
    for it in mod.node_group.interface.items_tree:
        if getattr(it, "name", None) == "Silhouette" and getattr(it, "in_out", None) == "INPUT":
            it.default_value = idx
    
    # Rotate to stand up
    host.rotation_euler = (-1.5707963267948966, 0, 0)  # -90° X
    
    print(f"  [{i+1}/6] {label} (idx={idx}) at x={x:.2f}")

# Frame camera to see all
bpy.ops.object.select_all(action="SELECT")
bpy.ops.view3d.camera_to_view_selected()

# Save
bpy.ops.wm.save_as_mainfile(
    filepath=r"P:/MelodiaMelusinaV2-Laptop/Saved/Accessories/Silhouette_Grid_v1.blend"
)

print()
print("=== Saved to Saved/Accessories/Silhouette_Grid_v1.blend ===")
print("=== Camera: Cam_Compare, Lens 50mm, looking down -Y ===")
print("DONE")
