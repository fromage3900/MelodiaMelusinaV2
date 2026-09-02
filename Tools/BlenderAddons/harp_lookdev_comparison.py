"""Lookdev comparison sheet: Concert Harp vs references.

Renders:
1. Beauty pass (full color, studio lighting)
2. Clay/ambient occlusion pass
3. Wireframe overlay
4. Side-by-side with reference images

Run: blender --factory-startup -b -P Tools/BlenderAddons/harp_lookdev_comparison.py
"""
import bpy
import os
import math

repo = "C:/EnvironmentPortfolio/BS_GodFile"
out_dir = os.path.join(repo, "Exports", "MelusinaInstruments", "Lookdev")
os.makedirs(out_dir, exist_ok=True)

print("=== Concert Harp — Lookdev Comparison ===")

# Load the harp FBX
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

fbx_path = os.path.join(out_dir, "SM_Mus_Harp_Concert_Real.fbx")
bpy.ops.import_scene.fbx(filepath=fbx_path)
harp = bpy.context.selected_objects[0]
harp.name = "Harp_Concert"

# Center the harp at origin for better framing
bpy.ops.object.select_all(action="DESELECT")
harp.select_set(True)
bpy.context.view_layer.objects.active = harp
bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')
bpy.ops.object.location_clear()

print(f"[harp] loaded: {len(harp.data.vertices)} verts, {len(harp.data.polygons)} polys")

# ============================================================
# BEAUTY RENDER
# ============================================================

# Lighting
bpy.ops.object.light_add(type="AREA", location=(2, -2, 3))
key = bpy.context.active_object
key.data.energy = 500
key.data.size = 3
key.data.color = (1.0, 0.95, 0.9)

bpy.ops.object.light_add(type="AREA", location=(-2, -1, 2))
fill = bpy.context.active_object
fill.data.energy = 200
fill.data.size = 2
fill.data.color = (0.9, 0.95, 1.0)

bpy.ops.object.light_add(type="AREA", location=(0, 3, 2))
rim = bpy.context.active_object
rim.data.energy = 400
rim.data.size = 1.5

# Camera
bpy.ops.object.camera_add(location=(0, -2.5, 1.2))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(75), 0, 0)
bpy.context.scene.camera = cam
cam.data.lens = 35

# Background
scene = bpy.context.scene
scene.world.node_tree.nodes[1].inputs[0].default_value = (0.88, 0.85, 0.78, 1.0)

# Render settings
scene.render.engine = "CYCLES"
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.cycles.samples = 512
scene.cycles.use_denoising = True

# Beauty pass
scene.render.filepath = os.path.join(out_dir, "harp_beauty_")
scene.render.image_settings.file_format = "PNG"
bpy.ops.render.render(write_still=True)
print(f"[render] beauty -> {scene.render.filepath}0001.png")

# ============================================================
# WIREFRAME OVERLAY
# ============================================================

# Enable wireframe overlay
harp.show_wire = True
harp.show_all_edges = True

# Render wireframe
scene.render.filepath = os.path.join(out_dir, "harp_wire_")
bpy.ops.render.render(write_still=True)
print(f"[render] wireframe -> {scene.render.filepath}0001.png")

# Disable wireframe
harp.show_wire = False
harp.show_all_edges = False

# ============================================================
# CLAY RENDER (AO-like)
# ============================================================

# Override material to clay
clay_mat = bpy.data.materials.new(name="Clay")
clay_mat.use_nodes = True
clay_nodes = clay_mat.node_tree.nodes
clay_bsdf = clay_nodes.get("Principled BSDF")
if clay_bsdf:
    clay_bsdf.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1.0)
    clay_bsdf.inputs["Roughness"].default_value = 0.9

# Store original materials
orig_mats = [slot.material for slot in harp.material_slots]

# Assign clay
for slot in harp.material_slots:
    slot.material = clay_mat

# Render clay
scene.render.filepath = os.path.join(out_dir, "harp_clay_")
bpy.ops.render.render(write_still=True)
print(f"[render] clay -> {scene.render.filepath}0001.png")

# Restore materials
for i, slot in enumerate(harp.material_slots):
    if i < len(orig_mats):
        slot.material = orig_mats[i]

# ============================================================
# TURNAROUND (360° rotation, 8 frames)
# ============================================================

scene.render.filepath = os.path.join(out_dir, "harp_turnaround_")
for i in range(8):
    angle = i * 45
    harp.rotation_euler = (0, 0, math.radians(angle))
    scene.render.filepath = os.path.join(out_dir, f"harp_turn_{i:02d}_")
    bpy.ops.render.render(write_still=True)
    print(f"[render] turnaround {angle}°")

# Reset rotation
harp.rotation_euler = (0, 0, 0)

print("=== Lookdev Comparison Complete ===")
