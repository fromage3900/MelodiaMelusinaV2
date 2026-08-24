"""Generate collision for terrain meshes and export UE5-ready FBX.

For each terrain mesh:
1. Create convex hull collision proxy (simplified mesh)
2. Assign as UCX_ collision prefix (UE5 convention)
3. Export FBX with collision embedded

UE5 import settings:
- Units: centimeters (scale 100)
- Collision: use UCX_ prefixed meshes
- Generate lightmap UVs: yes

Run inside Blender:
  blender --background --factory-startup --python generate_collision.py
"""

import bpy
import os
import sys
import math

REPO = r"C:\EnvironmentPortfolio\BS_GodFile"
ADDON = os.path.join(REPO, "Tools", "BlenderAddons", "melodia_studio")
if ADDON not in sys.path:
    sys.path.insert(0, ADDON)

import walkable_world as ww
import smooth_terrain as st


def generate_field(midi_path, preset_id="walkable_highlands"):
    """Generate smooth terrain mesh."""
    mesh = st.generate_smooth_terrain(midi_path, preset_id)
    if mesh is None:
        return None

    obj = bpy.data.objects.new("Terrain", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def add_collision(obj, method="CONVEX_HULL"):
    """Add collision proxy to terrain object.

    Methods:
    - CONVEX_HULL: simplified convex mesh (best for UE5)
    - BOX: simple box bounds
    - MESH: use terrain mesh itself (expensive)
    """
    if obj is None:
        return None

    if method == "CONVEX_HULL":
        # Duplicate and decimate for convex hull
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.ops.object.duplicate()
        collision_obj = bpy.context.active_object
        collision_obj.name = "UCX_%s" % obj.name

        # Add Decimate modifier for simplification
        mod = collision_obj.modifiers.new(name="CollisionDecimate", type='DECIMATE')
        mod.decimate_type = "DISSOLVE"
        mod.angle_limit = math.radians(15)

        # Apply modifier
        bpy.ops.object.modifier_apply(modifier=mod.name)

        # Parent to terrain
        collision_obj.parent = obj
        collision_obj.matrix_parent_inverse = obj.matrix_world.inverted()

        return collision_obj

    elif method == "BOX":
        # Simple box bounds
        bbox = obj.bound_box
        xs = [v[0] for v in bbox]
        ys = [v[1] for v in bbox]
        zs = [v[2] for v in bbox]

        mx = (min(xs) + max(xs)) / 2
        my = (min(ys) + max(ys)) / 2
        mz = (min(zs) + max(zs)) / 2
        sx = (max(xs) - min(xs)) / 2
        sy = (max(ys) - min(ys)) / 2
        sz = (max(zs) - min(zs)) / 2

        bpy.ops.mesh.primitive_cube_add(size=1, location=(mx, my, mz))
        collision_obj = bpy.context.active_object
        collision_obj.name = "UCX_%s" % obj.name
        collision_obj.scale = (sx, sy, sz)
        collision_obj.parent = obj
        collision_obj.matrix_parent_inverse = obj.matrix_world.inverted()

        return collision_obj

    return None


def export_with_collision(obj, output_path, collision_obj=None):
    """Export FBX with collision for UE5."""
    if obj is None:
        return None

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Select objects to export
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    if collision_obj:
        collision_obj.select_set(True)

    # UE5 export settings
    bpy.ops.export_scene.fbx(
        filepath=output_path,
        use_selection=True,
        global_scale=100.0,  # meters to centimeters
        apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL',
        axis_forward='-Z',
        axis_up='Y',
        use_custom_props=True,
        mesh_smooth_type='FACE',
        use_mesh_modifiers=True,
        path_mode='AUTO',
        embed_textures=False,
        batch_mode='OFF'
    )

    return output_path


def main():
    midi = os.path.join(REPO, "Content", "MelodiaIntegration", "MIDI",
                        "128BPMarpeggiomelody.mid")
    preset_id = "walkable_highlands"

    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Generate terrain
    terrain = generate_field(midi, preset_id)
    if terrain is None:
        print("[collision] Failed to generate terrain", flush=True)
        return

    # Add collision
    collision = add_collision(terrain, method="CONVEX_HULL")

    # Export
    out = os.path.join(REPO, "Saved", "Audit", "ue5_export",
                       "terrain_%s.fbx" % preset_id)
    result = export_with_collision(terrain, out, collision)

    if result:
        print("[collision] SUCCESS: %s" % result, flush=True)
        print("[collision] File size: %d bytes" % os.path.getsize(result), flush=True)
    else:
        print("[collision] FAILED", flush=True)


if __name__ == "__main__":
    main()
