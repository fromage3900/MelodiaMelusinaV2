import unreal
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
print("W", w.get_path_name() if w else None)
print("ED", unreal.SystemLibrary.is_packaged_for_distribution() if False else "ok")
