"""Import staged audio sources into the project via editor import tasks.

Phase B-1: Zundamon kitchen UI blips -> /Game/Melodia/Audio/SFX/UI/
Phase B-2: Sewaa Zundamon song (full + inst) -> /Game/Melodia/Audio/BGM/
"""
import unreal

SRC_UI = r"C:\Users\froma\AppData\Local\Temp\opencode\audio_sources\ui_blips_zundamon"
SRC_SEWAA = r"C:\Users\froma\AppData\Local\Temp\opencode\audio_sources\sewaa_zundamon"
DEST_UI = "/Game/Melodia/Audio/SFX/UI"
DEST_BGM = "/Game/Melodia/Audio/BGM"

tools = unreal.AssetToolsHelpers.get_asset_tools()


def import_wavs(src_dir, dest_path, prefix=None):
    import os
    files = sorted(os.listdir(src_dir))
    tasks = []
    for f in files:
        if not f.lower().endswith(".wav"):
            continue
        name = os.path.splitext(f)[0]
        if prefix:
            name = f"{prefix}_{name}"
        task = unreal.AssetImportTask()
        task.filename = os.path.join(src_dir, f)
        task.destination_path = dest_path
        task.destination_name = name
        task.automated = True
        task.save = True
        task.replace_existing = False
        tasks.append(task)
    if not tasks:
        print(f"NO_WAVS in {src_dir}")
        return []
    tools.import_asset_tasks(tasks)
    imported = []
    for t in tasks:
        for p in (t.imported_object_paths or []):
            if p:
                imported.append(p)
    return imported


# Ensure destination folders exist
for folder in (DEST_UI, DEST_BGM):
    if not unreal.EditorAssetLibrary.does_directory_exist(folder):
        unreal.EditorAssetLibrary.make_directory(folder)

ui_imported = import_wavs(SRC_UI, DEST_UI, prefix="UI_Blip")
print(f"UI_IMPORTED: {len(ui_imported)}")
for p in ui_imported:
    unreal.log(f"[AudioImport] {p}")

sewaa_imported = import_wavs(SRC_SEWAA, DEST_BGM, prefix="SW_BGM_Zundamon")
print(f"SEWAA_IMPORTED: {len(sewaa_imported)}")
for p in sewaa_imported:
    unreal.log(f"[AudioImport] {p}")

try:
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    print("SAVED")
except Exception as e:
    print(f"SAVE_WARN: {e}")
