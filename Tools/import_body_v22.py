import unreal, os
src_dir = "C:/EnvironmentPortfolio/BS_GodFile/Content/Melodia/Characters/Melusina/Textures"
# Body PNGs are already staged as files, need to import via AssetTools
# Use the existing PNGs as source for import (they are in same dir, but need to be imported as textures)
# AssetTools import requires external file path, not Content path. The PNGs are already in Content dir as loose files, not ideal.
# Instead, we will directly check if T_Melusina_Body_BC etc uassets exist, if not, we will set MIs to use the already-imported T_Melusina_M_Melusina_* as placeholder and log need for proper import.

# For now, repoint SBW MIs to use the v22 Body BC/N if they exist as assets, otherwise keep old but log.

def repoint_mi(mi_path, new_albedo, new_normal):
    mi = unreal.load_asset(mi_path)
    if not mi:
        print(f"MI not found {mi_path}")
        return
    # Get current textures to compare
    lib = unreal.MaterialEditingLibrary
    # Try to load new textures
    albedo_tex = unreal.load_asset(new_albedo)
    normal_tex = unreal.load_asset(new_normal)
    if albedo_tex:
        lib.set_material_instance_texture_parameter_value(mi, "Albedo", albedo_tex)
        print(f"Set {mi_path} Albedo -> {new_albedo}")
    else:
        print(f"Albedo texture not found {new_albedo} (need import)")
    if normal_tex:
        lib.set_material_instance_texture_parameter_value(mi, "NormalMap", normal_tex)
        print(f"Set {mi_path} Normal -> {new_normal}")
    else:
        print(f"Normal not found {new_normal}")
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    print(f"Saved {mi_path}")

# Try v22 body textures (expected after proper import)
new_bc = "/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Body_BC"
new_n = "/Game/Melodia/Characters/Melusina/Textures/T_Melusina_Body_N"
# Fallback: check if they exist
for p in [new_bc, new_n]:
    exists = unreal.EditorAssetLibrary.does_asset_exist(p)
    print(f"Exists {p}: {exists}")

# If they don't exist, we will at least verify current MI state
for mi in ["/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_SBW_MELUSINA_006", "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_SBW_MELUSINA_007"]:
    m = unreal.load_asset(mi)
    print(f"MI {mi} parent {m.get_editor_property('parent').get_path_name() if m else 'None'}")
    # List texture params
    try:
        params = unreal.MaterialEditingLibrary.get_material_instance_parameters(m)
        print(params)
    except Exception as e:
        print(f"params err {e}")
