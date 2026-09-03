import unreal
try: unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_end_play()
except Exception: pass
try: unreal.EditorLevelLibrary.editor_end_play()
except Exception: pass
