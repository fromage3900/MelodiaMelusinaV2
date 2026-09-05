import unreal
import os
import json

BASE = "C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/SurrealFabric_Flipbooks"
DEST = "/Game/EnvSandbox/Textures/SurrealFabric_Flipbooks"

# Texture settings by map type
MAP_SETTINGS = {
    "BaseColor": (True, unreal.TextureCompressionSettings.TC_DEFAULT),
    "Normal": (False, unreal.TextureCompressionSettings.TC_NORMALMAP),
    "Roughness": (False, unreal.TextureCompressionSettings.TC_GRAYSCALE),
    "Iridescence": (False, unreal.TextureCompressionSettings.TC_GRAYSCALE),
    "Height": (False, unreal.TextureCompressionSettings.TC_GRAYSCALE),
}

def import_png(png_path, dest_path, dest_name, srgb, compression):
    task = unreal.AssetImportTask()
    task.filename = png_path
    task.destination_path = dest_path
    task.destination_name = dest_name
    task.replace_existing = False
    task.automated = True
    task.save = True
    task.srgb = srgb
    task.compression_settings = compression
    task.lod_group = unreal.TextureGroup.WORLD
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return unreal.EditorAssetLibrary.does_asset_exist(f"{dest_path}/{dest_name}")

# Collect all PNGs
pngs = []
for root, dirs, files in os.walk(BASE):
    for fn in files:
        if fn.endswith(".png"):
            pngs.append(os.path.join(root, fn))

print(f"Found {len(pngs)} PNGs to import")

# Import with correct settings
imported = 0
skipped = 0
failed = []
for png in pngs:
    rel = os.path.relpath(png, BASE)
    parts = rel.split(os.path.sep)
    # Path: SetName/FileName.png
    set_name = parts[0]
    file_name = parts[1]
    
    # Determine map type from filename
    map_type = None
    for mt in MAP_SETTINGS:
        if f"_{mt}" in file_name:
            map_type = mt
            break
    if not map_type:
        # Try without case
        for mt in MAP_SETTINGS:
            if f"_{mt.lower()}" in file_name.lower():
                map_type = mt
                break
    if not map_type:
        failed.append(f"Unknown map type: {file_name}")
        continue
    
    srgb, compression = MAP_SETTINGS[map_type]
    
    # Destination: /Game/EnvSandbox/Textures/SurrealFabric_Flipbooks/SetName/FileName (no .png)
    dest_name = file_name[:-4]
    dest_path = f"{DEST}/{set_name}"
    
    if unreal.EditorAssetLibrary.does_asset_exist(f"{dest_path}/{dest_name}"):
        skipped += 1
        continue
    
    ok = import_png(png, dest_path, dest_name, srgb, compression)
    if ok:
        imported += 1
    else:
        failed.append(file_name)
    
    if (imported + skipped) % 50 == 0:
        print(f"  progress: {imported} imported, {skipped} skipped")

print(f"\nDONE: {imported} imported, {skipped} skipped, {len(failed)} failed")
if failed:
    print("FAILED:", failed[:10])
