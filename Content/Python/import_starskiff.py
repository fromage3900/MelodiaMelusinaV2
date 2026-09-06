import unreal

TEXTURES = [
    ("T_Starskiff_BrassFiligree_Normal", False, "TC_Normalmap", "World"),
    ("T_Starskiff_Hull_Height", False, "TC_Default", "World"),
    ("T_Starskiff_Jewel_BaseColor", True, "TC_Default", "World"),
    ("T_Starskiff_Jewel_Normal", False, "TC_Normalmap", "World"),
    ("T_Starskiff_PlankSeam_Mask", False, "TC_Masks", "World"),
    ("T_Starskiff_RegalEdgeWear_Mask", False, "TC_Masks", "World"),
    ("T_Starskiff_SternCrest_BaseColor", True, "TC_Default", "World"),
]

BASE = "C:/EnvironmentPortfolio/BS_GodFile/Content/Melodia/Characters/Melusina/Textures/Clothes"

for name, srgb, comp, group in TEXTURES:
    png = f"{BASE}/{name}.png"
    uasset = f"{BASE}/{name}.uasset"
    if unreal.EditorAssetLibrary.does_asset_exist(f"/Game/Melodia/Characters/Melusina/Textures/Clothes/{name}"):
        print(f"SKIP (exists): {name}")
        continue
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", png)
    task.set_editor_property("destination_path", "/Game/Melodia/Characters/Melusina/Textures/Clothes")
    task.set_editor_property("destination_name", name)
    task.set_editor_property("replace_existing", False)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    # sRGB
    task.set_editor_property("srgb", srgb)
    # Compression
    comp_map = {"TC_Default": unreal.TextureCompressionSettings.TC_DEFAULT,
                "TC_Normalmap": unreal.TextureCompressionSettings.TC_NORMALMAP,
                "TC_Masks": unreal.TextureCompressionSettings.TC_MASKS}
    task.set_editor_property("compression_settings", comp_map.get(comp, unreal.TextureCompressionSettings.TC_DEFAULT))
    # LOD group
    group_map = {"World": unreal.TextureGroup.WORLD,
                 "Effects": unreal.TextureGroup.EFFECTS}
    task.set_editor_property("lod_group", group_map.get(group, unreal.TextureGroup.WORLD))
    # Import
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    print(f"IMPORTED: {name} (srgb={srgb}, comp={comp}, group={group})")
