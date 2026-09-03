"""Import the Sewaa full mix + instrumental (ASCII names) as battle BGM candidates."""
import unreal

SRC = r"C:\Users\froma\AppData\Local\Temp\opencode\audio_sources\sewaa_zundamon"
DEST = "/Game/Melodia/Audio/BGM"

if not unreal.EditorAssetLibrary.does_directory_exist(DEST):
    unreal.EditorAssetLibrary.make_directory(DEST)

tools = unreal.AssetToolsHelpers.get_asset_tools()
import os
tasks = []
for name, fname in [("SW_BGM_Zundamon_Sewaa_Full", "SW_Zundamon_Sewaa_Full.wav"),
                    ("SW_BGM_Zundamon_Sewaa_Inst", "SW_Zundamon_Sewaa_Inst.wav")]:
    task = unreal.AssetImportTask()
    task.filename = os.path.join(SRC, fname)
    task.destination_path = DEST
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = False
    tasks.append(task)

tools.import_asset_tasks(tasks)
for t in tasks:
    for p in (t.imported_object_paths or []):
        if p:
            unreal.log(f"[AudioImport] {p}")
            print(f"IMPORTED: {p}")
