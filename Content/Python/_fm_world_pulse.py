import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
print("WORLD", w.get_path_name() if w else None)
print("EXISTS_MORNING", unreal.EditorAssetLibrary.does_asset_exist("/Game/Melodia/Levels/Opening/L_MelusinaMorning"))
