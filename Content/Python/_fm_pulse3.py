import unreal, json
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
print("WORLD", w.get_path_name() if w else None)
print("PROJECT", unreal.Paths.project_dir())
# asset registry sample
eal = unreal.EditorAssetLibrary
print("ZEN", eal.does_asset_exist("/Game/ZenForestTest"))
print("MORNING", eal.does_asset_exist("/Game/Melodia/Levels/Opening/L_MelusinaMorning"))
try:
    assets = eal.list_assets("/Game", recursive=False, include_folder=True)
    print("GAME_ROOT", list(assets)[:15] if assets else [])
except Exception as e:
    print("LIST_ERR", e)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
print("ACTORS", len(list(eas.get_all_level_actors())))
