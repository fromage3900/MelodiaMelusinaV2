import unreal
import os

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
DEST = "/Game/Melodia/Characters/Melusina/Textures/Clothes"

for name, srgb, comp, group in TEXTURES:
    png = f"{BASE}/{name}.png"
    dest_path = f"{DEST}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(dest_path):
        print(f"SKIP (exists): {name}")
        continue
    task = unreal.AssetImportTask()
    task.filename = png
    task.destination_path = DEST
    task.destination_name = name
    task.replace_existing = False
    task.automated = True
    task.save = True
    task.srgb = srgb
    comp_map = {"TC_Default": unreal.TextureCompressionSettings.TC_DEFAULT,
                "TC_Normalmap": unreal.TextureCompressionSettings.TC_NORMALMAP,
                "TC_Masks": unreal.TextureCompressionSettings.TC_MASKS}
    task.compression_settings = comp_map[comp]
    group_map = {"World": unreal.TextureGroup.WORLD,
                 "Effects": unreal.TextureGroup.EFFECTS}
    task.lod_group = group_map[group]
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    # Verify
    if unreal.EditorAssetLibrary.does_asset_exist(dest_path):
        print(f"OK: {name}")
    else:
        print(f"FAIL: {name}")
