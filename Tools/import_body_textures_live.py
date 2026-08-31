import unreal, os
src = "C:/EnvironmentPortfolio/BS_GodFile/Content/Melodia/Characters/Melusina/Textures"
dest = "/Game/Melodia/Characters/Melusina/Textures"
files = {
    "T_Melusina_Body_BC.png": ("T_Melusina_Body_BC", False, unreal.TextureCompressionSettings.TC_DEFAULT, True),
    "T_Melusina_Body_N.png": ("T_Melusina_Body_N", True, unreal.TextureCompressionSettings.TC_NORMALMAP, False),
    "T_Melusina_Body_ORM.png": ("T_Melusina_Body_ORM", True, unreal.TextureCompressionSettings.TC_MASKS, False),
    "T_Melusina_Body_H.png": ("T_Melusina_Body_H", True, unreal.TextureCompressionSettings.TC_MASKS, False),
    "T_Melusina_Body_Mask.png": ("T_Melusina_Body_Mask", True, unreal.TextureCompressionSettings.TC_MASKS, False),
    "T_Melusina_Body_Emission.png": ("T_Melusina_Body_Emission", True, unreal.TextureCompressionSettings.TC_DEFAULT, True),
}
for fname, (dest_name, is_linear, comp, srgb) in files.items():
    fpath = os.path.join(src, fname)
    if not os.path.exists(fpath):
        print(f"Missing {fpath}")
        continue
    existing = unreal.EditorAssetLibrary.does_asset_exist(f"{dest}/{dest_name}")
    if existing:
        print(f"Exists {dest}/{dest_name}, skipping import")
        continue
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", fpath)
    task.set_editor_property("destination_path", dest)
    task.set_editor_property("destination_name", dest_name)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    if task.get_editor_property("imported_object_paths"):
        tex = unreal.load_asset(task.get_editor_property("imported_object_paths")[0])
        if tex:
            tex.set_editor_property("compression_settings", comp)
            tex.set_editor_property("srgb", srgb)
            unreal.EditorAssetLibrary.save_loaded_asset(tex)
            print(f"Imported {dest_name} {comp} srgb={srgb}")
        else:
            print(f"Failed load {dest_name}")
    else:
        print(f"Failed import {fname}")

# Now repoint MIs
import unreal as u
lib = u.MaterialEditingLibrary
for mi_path in ["/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_SBW_MELUSINA_006", "/Game/Melodia/Characters/Melusina/Materials/MI_Melusina_SBW_MELUSINA_007"]:
    mi = u.load_asset(mi_path)
    bc = u.load_asset(f"{dest}/T_Melusina_Body_BC")
    n = u.load_asset(f"{dest}/T_Melusina_Body_N")
    orm = u.load_asset(f"{dest}/T_Melusina_Body_ORM")
    h = u.load_asset(f"{dest}/T_Melusina_Body_H")
    if bc:
        lib.set_material_instance_texture_parameter_value(mi, "Albedo", bc)
        print(f"Set Albedo {mi_path}")
    if n:
        lib.set_material_instance_texture_parameter_value(mi, "NormalMap", n)
        print(f"Set Normal {mi_path}")
    # For ORM, we need to handle packed: set Roughness and Metallic to ORM with appropriate logic
    # Since master uses separate RoughnessMap/MetallicMap when bUseSeparate true, we can set both to ORM
    if orm:
        lib.set_material_instance_texture_parameter_value(mi, "RoughnessMap", orm)
        lib.set_material_instance_texture_parameter_value(mi, "MetallicMap", orm)
        print(f"Set ORM as Roughness+Metallic {mi_path}")
    if h:
        lib.set_material_instance_texture_parameter_value(mi, "HeightMap", h)
        print(f"Set Height {mi_path}")
    lib.set_material_instance_static_switch_parameter_value(mi, "bUseSeparateRoughnessMap", True)
    lib.set_material_instance_static_switch_parameter_value(mi, "bUseSeparateMetallicMap", True)
    u.EditorAssetLibrary.save_loaded_asset(mi)
    print(f"Saved {mi_path}")

print("DONE")
