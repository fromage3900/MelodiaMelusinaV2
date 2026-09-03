# -*- coding: utf-8 -*-
"""
Melusina Animation Stage — Template Generator

Creates a pre-lit, pre-rigged Blender template for character animation.
Run from Blender's Text Editor or command line:

    blender --python Tools/create_animation_template.py

Output: Templates/Melusina_Animation_Stage.blend
"""
import bpy
import os
from mathutils import Vector

TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Templates", "Melusina_Animation_Stage.blend"
)

def clear_scene():
    """Remove all objects from the scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Clean up orphaned data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)
    for block in bpy.data.cameras:
        if block.users == 0:
            bpy.data.cameras.remove(block)
    for block in bpy.data.lights:
        if block.users == 0:
            bpy.data.lights.remove(block)

def create_collection(name):
    """Create a collection if it doesn't exist."""
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    return coll

def setup_render_settings():
    """Configure render settings for animation."""
    scene = bpy.context.scene
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 2000
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'

    # Use EEVEE Next if available
    engines = {e.identifier for e in scene.bl_rna.properties["render"].fixed_type.properties["engine"].enum_items}
    if "BLENDER_EEVEE_NEXT" in engines:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    else:
        scene.render.engine = "BLENDER_EEVEE"

def create_light(name, light_type, location, energy, color, size=1.0, collection=None):
    """Create a light with standard settings."""
    light_data = bpy.data.lights.new(name=name, type=light_type)
    light_data.energy = energy
    light_data.color = color
    if light_type == 'AREA':
        light_data.size = size

    light_obj = bpy.data.objects.new(name=name, object_data=light_data)
    light_obj.location = Vector(location)

    if collection:
        collection.objects.link(light_obj)
    else:
        bpy.context.collection.objects.link(light_obj)

    return light_obj

def create_camera(name, location, lens, fstop, aim_target, collection=None):
    """Create a camera with DOF aimed at target."""
    cam_data = bpy.data.cameras.new(name=name)
    cam_data.lens = lens
    cam_data.clip_start = 0.1
    cam_data.clip_end = 100.0
    cam_data.sensor_width = 36.0

    cam_obj = bpy.data.objects.new(name=name, object_data=cam_data)
    cam_obj.location = Vector(location)

    # Aim at target
    direction = Vector(aim_target) - cam_obj.location
    cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    # DOF
    cam_data.dof.use_dof = True
    cam_data.dof.focus_distance = direction.length
    cam_data.dof.aperture_fstop = fstop

    if collection:
        collection.objects.link(cam_obj)
    else:
        bpy.context.collection.objects.link(cam_obj)

    return cam_obj

def create_ground(collection):
    """Create a shadow-catcher ground plane."""
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"

    # Shadow catcher material
    mat = bpy.data.materials.new(name="M_ShadowCatcher")
    mat.use_nodes = True
    mat.blend_method = 'BLEND'
    ground.data.materials.append(mat)

    if collection:
        # Move to collection
        for c in ground.users_collection:
            c.objects.unlink(ground)
        collection.objects.link(ground)

    return ground

def create_stage():
    """Create the full animation stage."""
    clear_scene()

    # Create collections
    char_coll = create_collection("Character")
    light_coll = create_collection("Lighting")
    cam_coll = create_collection("Cameras")
    stage_coll = create_collection("Stage")

    # Render settings
    setup_render_settings()

    # === LIGHTING (3-point) ===
    # Key light - warm, bright, 45° up-right-front
    key = create_light(
        "L_Key", 'AREA',
        location=(2.6, -2.4, 3.4),
        energy=800,
        color=(1.0, 0.93, 0.84),
        size=1.8,
        collection=light_coll
    )

    # Fill light - cool, softer, opposite side
    fill = create_light(
        "L_Fill", 'AREA',
        location=(-2.4, 1.6, 2.2),
        energy=300,
        color=(0.45, 0.82, 1.0),
        size=1.2,
        collection=light_coll
    )

    # Rim light - behind, for silhouette edge
    rim = create_light(
        "L_Rim", 'SPOT',
        location=(0, 3.2, 2.8),
        energy=500,
        color=(1.0, 0.88, 0.45),
        collection=light_coll
    )
    rim.data.spot_size = 0.785  # 45 degrees

    # === CAMERAS ===
    # Beauty camera - portrait, aimed at chest
    beauty = create_camera(
        "Cam_Beauty",
        location=(3.05, -4.45, 1.55),
        lens=50.0,
        fstop=2.8,
        aim_target=(0, -0.18, 1.10),
        collection=cam_coll
    )

    # Macro camera - close-up, aimed at head
    macro = create_camera(
        "Cam_Macro",
        location=(0.85, -1.70, 1.46),
        lens=90.0,
        fstop=2.8,
        aim_target=(0, -0.16, 1.44),
        collection=cam_coll
    )

    # Set beauty as active camera
    bpy.context.scene.camera = beauty

    # === STAGE ===
    ground = create_ground(stage_coll)

    # === SAVE ===
    os.makedirs(os.path.dirname(TEMPLATE_PATH), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=TEMPLATE_PATH)
    print(f"Template saved: {TEMPLATE_PATH}")

if __name__ == "__main__":
    create_stage()
