import unreal
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
LVL = "/Game/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype"
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
wp = w.get_path_name() if w else None
print("BEFORE", wp)
if "MelusinaMorning" in (wp or ""):
    raise SystemExit("refused morning")
if "LV_FarawayMother_Prototype" not in (wp or ""):
    print("LOAD", LES.load_level(LVL))
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
print("AFTER", w.get_path_name() if w else None)
