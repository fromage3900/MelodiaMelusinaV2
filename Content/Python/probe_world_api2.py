import unreal
for c in [unreal.EditorLevelLibrary,unreal.LevelEditorSubsystem]: print(c,[x for x in dir(c) if 'world' in x.lower() or 'play' in x.lower()])
