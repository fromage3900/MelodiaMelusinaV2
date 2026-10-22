import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
print("WORLD", w.get_path_name() if w else None)
print("ZEN", unreal.EditorAssetLibrary.does_asset_exist("/Game/ZenForestTest"))
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
print("ACTORS", len(list(eas.get_all_level_actors())) if eas else -1)
