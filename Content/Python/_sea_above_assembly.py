import unreal
import json

# ============================================================
# SEA ABOVE P0 ASSEMBLY
# Place cathedral meshes, apply materials, configure PCG
# ============================================================

def set_material_on_mesh(mesh_path, material_path):
    """Set the material on a static mesh asset."""
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if mesh is None:
        print(f"[FAIL] Could not load mesh: {mesh_path}")
        return False
    mat = unreal.EditorAssetLibrary.load_asset(material_path)
    if mat is None:
        print(f"[FAIL] Could not load material: {material_path}")
        return False
    # Get material slots
    mat_inter = mesh.get_editor_property("static_materials")
    if mat_inter and len(mat_inter) > 0:
        mat_inter[0].set_editor_property("material_interface", mesh, mat)
        print(f"[OK] Set material on {mesh_path}")
        return True
    else:
        print(f"[SKIP] No material slots on {mesh_path}")
        return False

def place_actor_in_level(mesh_path, location, rotation=None, scale=None):
    """Spawn a static mesh actor in the level."""
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if mesh is None:
        print(f"[FAIL] Could not load mesh: {mesh_path}")
        return None
    # Get the world
    world = unreal.EditorLevelLibrary.get_editor_world()
    # Create the actor
    actor_location = unreal.Vector(location[0], location[1], location[2])
    actor_rotation = unreal.Rotator(0, 0, 0) if rotation is None else unreal.Rotator(rotation[0], rotation[1], rotation[2])
    actor_scale = unreal.Vector(1, 1, 1) if scale is None else unreal.Vector(scale[0], scale[1], scale[2])
    
    actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
        mesh,
        actor_location,
        actor_rotation
    )
    if actor:
        actor.set_actor_scale3d(actor_scale)
        print(f"[OK] Placed {mesh_path.split('/')[-1]} at {location}")
    else:
        print(f"[FAIL] Could not spawn {mesh_path}")
    return actor

# Materials
M_CRYSTAL_CLEAR = "/Game/EnvSandbox/Materials/Masters/M_Crystal_Clear_Toon.M_Crystal_Clear_Toon"
M_CATHEDRAL_FLOOR = "/Game/EnvSandbox/Materials/Masters/M_CathedralFloor_Textured.M_CathedralFloor_Textured"
M_IRIDESCENT = "/Game/EnvSandbox/Materials/Masters/M_IridescentMystical.M_IridescentMystical"
M_AUDIO_REACTIVE = "/Game/EnvSandbox/Materials/Masters/M_AudioReactive_BaseMaster.M_AudioReactive_BaseMaster"

# ============================================================
# PHASE 1: Apply materials to cathedral houdini meshes
# ============================================================
print("\n=== PHASE 1: Apply materials to cathedral meshes ===\n")

cathedral_meshes = {
    "SM_P4_Cathedral_Crystal_6Bays_Harmony": M_CRYSTAL_CLEAR,
    "SM_P4_Cathedral_Crystal_8Bays_Grand": M_CRYSTAL_CLEAR,
    "SM_P4_Cathedral_Crystal_Rose_6Bays": M_CRYSTAL_CLEAR,
    "SM_P4_Cathedral_Fractal_6Bays_Harmony": M_IRIDESCENT,
    "SM_P4_Cathedral_Fractal_8Bays_Grand": M_IRIDESCENT,
    "SM_P4_Cathedral_RoseWindow_6Bays": M_CRYSTAL_CLEAR,
}

base_path = "/Game/EnvSandbox/Meshes/Cathedral_Houdini/"
for mesh_name, mat_path in cathedral_meshes.items():
    mesh_path = f"{base_path}{mesh_name}.{mesh_name}"
    set_material_on_mesh(mesh_path, mat_path)

print("\n=== PHASE 1 complete ===\n")
