import unreal
import json

# ============================================================
# Set materials on cathedral houdini meshes
# ============================================================

def set_material_on_mesh(mesh_path, material_path):
    """Set the first material slot on a StaticMesh."""
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if mesh is None:
        print(f"[FAIL] Could not load mesh: {mesh_path}")
        return False
    
    mat = unreal.EditorAssetLibrary.load_asset(material_path)
    if mat is None:
        print(f"[FAIL] Could not load material: {material_path}")
        return False
    
    # StaticMesh has StaticMaterials array
    static_materials = mesh.get_editor_property("static_materials")
    if static_materials and len(static_materials) > 0:
        static_materials[0].set_editor_property("material_interface", mat)
        print(f"[OK] Set material on {mesh_path.split('/')[-1]}")
        return True
    else:
        print(f"[SKIP] No material slots on {mesh_path.split('/')[-1]}")
        return False

meshes_mats = [
    ("/Game/EnvSandbox/Meshes/Cathedral_Houdini/SM_P4_Cathedral_Crystal_6Bays_Harmony.SM_P4_Cathedral_Crystal_6Bays_Harmony", 
     "/Game/EnvSandbox/Materials/Masters/M_Crystal_Clear_Toon.M_Crystal_Clear_Toon"),
    ("/Game/EnvSandbox/Meshes/Cathedral_Houdini/SM_P4_Cathedral_Crystal_8Bays_Grand.SM_P4_Cathedral_Crystal_8Bays_Grand",
     "/Game/EnvSandbox/Materials/Masters/M_Crystal_Clear_Toon.M_Crystal_Clear_Toon"),
    ("/Game/EnvSandbox/Meshes/Cathedral_Houdini/SM_P4_Cathedral_Crystal_Rose_6Bays.SM_P4_Cathedral_Crystal_Rose_6Bays",
     "/Game/EnvSandbox/Materials/Masters/M_Crystal_Clear_Toon.M_Crystal_Clear_Toon"),
    ("/Game/EnvSandbox/Meshes/Cathedral_Houdini/SM_P4_Cathedral_Fractal_6Bays_Harmony.SM_P4_Cathedral_Fractal_6Bays_Harmony",
     "/Game/EnvSandbox/Materials/Masters/M_IridescentMystical.M_IridescentMystical"),
    ("/Game/EnvSandbox/Meshes/Cathedral_Houdini/SM_P4_Cathedral_Fractal_8Bays_Grand.SM_P4_Cathedral_Fractal_8Bays_Grand",
     "/Game/EnvSandbox/Materials/Masters/M_IridescentMystical.M_IridescentMystical"),
    ("/Game/EnvSandbox/Meshes/Cathedral_Houdini/SM_P4_Cathedral_RoseWindow_6Bays.SM_P4_Cathedral_RoseWindow_6Bays",
     "/Game/EnvSandbox/Materials/Masters/M_Crystal_Clear_Toon.M_Crystal_Clear_Toon"),
]

print("=== Setting materials on cathedral houdini meshes ===")
for mesh_path, mat_path in meshes_mats:
    set_material_on_mesh(mesh_path, mat_path)

print("\n=== DONE ===")
