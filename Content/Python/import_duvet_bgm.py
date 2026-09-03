"""Import duvet melusina cover as battle BGM SoundWave (looping)."""
import unreal

SRC = r"C:\Users\froma\AppData\Local\Temp\opencode\duvet_melusina_cover.wav"
DEST_PATH = "/Game/Melodia/Audio/BGM"
DEST_NAME = "SW_BGM_Battle_Duvet_Cover"

existing = f"{DEST_PATH}/{DEST_NAME}.{DEST_NAME}"
if unreal.EditorAssetLibrary.does_asset_exist(existing):
    unreal.log(f"[Duvet] asset already exists: {existing}")
    sw = unreal.EditorAssetLibrary.load_asset(existing)
    sw.set_editor_property("looping", True)
    unreal.EditorAssetLibrary.save_loaded_asset(sw, only_if_is_dirty=False)
    print("ALREADY_EXISTS")
else:
    task = unreal.AssetImportTask()
    task.filename = SRC
    task.destination_path = DEST_PATH
    task.destination_name = DEST_NAME
    task.automated = True
    task.save = True
    task.replace_existing = False
    task.replace_existing_settings = False

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    tools.import_asset_tasks([task])

    imported = [a for a in task.imported_object_paths if a]
    print(f"IMPORTED: {imported}")

    # Load and set looping
    sw = unreal.EditorAssetLibrary.load_asset(existing)
    if sw:
        sw.set_editor_property("looping", True)
        unreal.EditorAssetLibrary.save_loaded_asset(sw, only_if_is_dirty=False)
        print(f"LOOPING_SET: {existing}")
    else:
        print("LOAD_FAILED_AFTER_IMPORT")
