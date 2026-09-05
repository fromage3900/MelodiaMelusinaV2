import unreal
import os

BASE = "C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/SurrealFabric_Flipbooks"
DEST = "/Game/EnvSandbox/Textures/SurrealFabric_Flipbooks"

MAP_SETTINGS = {
    "BaseColor": (True, unreal.TextureCompressionSettings.TC_DEFAULT),
    "Normal": (False, unreal.TextureCompressionSettings.TC_NORMALMAP),
    "Roughness": (False, unreal.TextureCompressionSettings.TC_GRAYSCALE),
    "Iridescence": (False, unreal.TextureCompressionSettings.TC_GRAYSCALE),
    "Height": (False, unreal.TextureCompressionSettings.TC_GRAYSCALE),
}

# Collect all PNGs
pngs = []
for root, dirs, files in os.walk(BASE):
    for fn in files:
        if fn.endswith(".png"):
            pngs.append(os.path.join(root, fn))

print(f"Found {len(pngs)} PNGs")

imported = 0
skipped = 0
failed = []

for png in pngs:
    rel = os.path.relpath(png, BASE)
    parts = rel.split(os.path.sep)
    set_name = parts[0]
    file_name = parts[1]
    
    map_type = None
    for mt in ["BaseColor", "Normal", "Roughness", "Iridescence", "Height"]:
        if f"_{mt}" in file_name or f"_{mt.lower()}" in file_name.lower():
            map_type = mt
            break
    if not map_type:
        failed.append(f"Unknown: {file_name}")
        continue
    
    srgb, compression = MAP_SETTINGS[map_type]
    dest_name = file_name[:-4]
    dest_path = f"{DEST}/{set_name}"
    
    if unreal.EditorAssetLibrary.does_asset_exist(f"{dest_path}/{dest_name}"):
        skipped += 1
        continue
    
    task = unreal.AssetImportTask()
    task.filename = png
    task.destination_path = dest_path
    task.destination_name = dest_name
    task.replace_existing = False
    task.automated = True
    task.save = True
    task.srgb = srgb
    task.compression_settings = compression
    task.lod_group = unreal.TextureGroup.WORLD
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    
    if unreal.EditorAssetLibrary.does_asset_exist(f"{dest_path}/{dest_name}"):
        imported += 1
    else:
        failed.append(file_name)
    
    if (imported + skipped) % 50 == 0:
        print(f"  {imported} imported, {skipped} skipped")

print(f"DONE: {imported} imported, {skipped} skipped, {len(failed)} failed")
if failed:
    print("FAILED samples:", failed[:5])
