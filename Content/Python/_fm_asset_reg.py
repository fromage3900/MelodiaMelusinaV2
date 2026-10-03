import unreal, json
EAL = unreal.EditorAssetLibrary
paths = [
    "/Game/Melodia/Levels/Opening/L_MelusinaMorning",
    "/Game/Melodia/Levels/Opening/L_MelusinaShowcase",
    "/Game/ZenForestTest",
    "/Game/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype",
]
out = {p: EAL.does_asset_exist(p) for p in paths}
# list a few assets under /Game/Melodia/Levels
try:
    out["list_opening"] = EAL.list_assets("/Game/Melodia/Levels/Opening", recursive=False, include_folder=False)[:20]
except Exception as e:
    out["list_err"] = str(e)
try:
    out["list_game"] = EAL.list_assets("/Game", recursive=False, include_folder=True)[:30]
except Exception as e:
    out["list_game_err"] = str(e)
# project dir
out["project"] = unreal.Paths.project_dir()
out["project_content"] = unreal.Paths.project_content_dir()
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
out["world"] = w.get_path_name() if w else None
print("REG " + json.dumps(out, default=str)[:6000])
